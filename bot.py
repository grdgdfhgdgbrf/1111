#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚔️ Арена Дуэлянтов — PvP-онли, пошаговые бои.
Раунд: атакующий выбирает зону удара, защищающийся — зону защиты.
Если защита совпала с атакой — урон не проходит.
Урон = урон оружия − защита зоны бронёй.
"""

import asyncio
import html
import logging
import os
import random
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

# ════════════════════════════════════════════════════════════════════
#  КОНФИГ
# ════════════════════════════════════════════════════════════════════

BOT_TOKEN = os.getenv("BOT_TOKEN", "8996813076:AAGcvKnpHgpDAYcHw7NUWGtqI31pxllzWp4")
DB_PATH = os.getenv("DB_PATH", "arena.db")
ADMIN_ID = 5356400377

START_CHIPS = 200

# ── Зоны тела ───────────────────────────────────────────────────────
# dmg   — множитель урона при ударе по зоне
# armor — множитель брони для этой зоны (сколько % брони идёт в защиту)
# crit  — множитель шанса крита
BODY_ZONES = {
    "head":  dict(name="Голова",  emoji="🧠", dmg=1.6, armor=0.6, crit=2.2, hp=0.22),
    "torso": dict(name="Торс",    emoji="🫀", dmg=1.0, armor=1.0, crit=1.0, hp=0.40),
    "arms":  dict(name="Руки",    emoji="💪", dmg=0.8, armor=0.8, crit=0.8, hp=0.20),
    "legs":  dict(name="Ноги",    emoji="🦵", dmg=0.9, armor=0.7, crit=0.9, hp=0.18),
}

# ── Оружие ──────────────────────────────────────────────────────────
WEAPONS = {
    "fists":  dict(emoji="👊", name="Кулаки",  dmg=8,  spec="Серия ударов",
                   desc="3 удара по 40% урона", price=0,   chance=25),
    "dagger": dict(emoji="🗡", name="Кинжал",  dmg=11, spec="Тысяча порезов",
                   desc="3 удара по 40% урона", price=150, chance=30),
    "sword":  dict(emoji="⚔️", name="Меч",     dmg=14, spec="Казнь",
                   desc="добивает цель с HP < 30% (урон ×3)", price=350, chance=28),
    "axe":    dict(emoji="🪓", name="Топор",   dmg=17, spec="Кровопускание",
                   desc="кровотечение: 5% макс. HP, 3 раунда", price=550, chance=24),
    "bow":    dict(emoji="🏹", name="Лук",     dmg=15, spec="Снайперский выстрел",
                   desc="100% крит, игнорирует защиту", price=750, chance=22),
    "staff":  dict(emoji="🔥", name="Посох",   dmg=19, spec="Огненный шторм",
                   desc="горение: 30% урона, 3 раунда", price=950, chance=22),
    "hammer": dict(emoji="🔨", name="Молот",   dmg=22, spec="Землетрясение",
                   desc="150% урона + оглушение", price=1200, chance=18),
}

# ── Броня ───────────────────────────────────────────────────────────
# df — общая защита; распределяется по зонам через BODY_ZONES[zone]["armor"]
ARMORS = {
    "none":   dict(emoji="👕", name="Без брони",   df=0,  hp=0,  price=0,    chance=0,  cd=0, dmg=0,  desc="—"),
    "light":  dict(emoji="🥋", name="Лёгкая",      df=4,  hp=10, price=120,  chance=10, cd=0, dmg=0,  desc="+10% шанс спец-атаки"),
    "medium": dict(emoji="🛡", name="Средняя",     df=8,  hp=25, price=300,  chance=0,  cd=1, dmg=0,  desc="−1 к откату спец-атаки"),
    "heavy":  dict(emoji="🏋️", name="Тяжёлая",     df=13, hp=45, price=600,  chance=0,  cd=0, dmg=20, desc="+20% урон спец-атаки"),
    "legend": dict(emoji="✨", name="Легендарная", df=18, hp=70, price=1200, chance=15, cd=0, dmg=30, desc="+15% шанс, +30% урон спец-атаки"),
}

BASE_HP = 120
BASE_CRIT = 10
BASE_SPEC_CD = 3
CRIT_CAP = 60
MAX_ROUNDS = 60

# ── Арены по победам ────────────────────────────────────────────────
ARENAS = {
    "bronze": dict(name="Бронзовая арена",  emoji="🥉", min_wins=0,  max_wins=9),
    "silver": dict(name="Серебряная арена", emoji="🥈", min_wins=10, max_wins=29),
    "gold":   dict(name="Золотая арена",    emoji="🥇", min_wins=30, max_wins=10**9),
}
ARENA_ORDER = ["bronze", "silver", "gold"]


def arena_of(wins: int) -> str:
    for key in ARENA_ORDER:
        a = ARENAS[key]
        if a["min_wins"] <= wins <= a["max_wins"]:
            return key
    return "gold"


# ── Человеческие ники для скрытых соперников ───────────────────────
HUMAN_NAMES = [
    "Максим", "Артём", "Данил", "Кирилл", "Егор", "Иван", "Никита", "Рома",
    "Саня", "Дима", "Влад", "Серёга", "Паша", "Толя", "Женя", "Костя",
    "Лёха", "Миша", "Гриша", "Стас", "Олег", "Ден", "Марк", "Тимур",
    "Алина", "Катя", "Настя", "Даша", "Лера", "Соня", "Вика", "Полина",
    "Крис", "Милана", "Аня", "Юля", "Оля", "Маша", "Ксюша", "Ника",
]
HUMAN_TITLES = ["", "", "", "xd", "pro", "god", "real", "top", "_", "007", "tvoy"]

# ── Меню ────────────────────────────────────────────────────────────
BTN_ARENA = "⚔️ Арена"
BTN_GEAR = "🎒 Снаряжение"
BTN_TOP = "🏆 Топ"
MENU_TEXTS = {BTN_ARENA, BTN_GEAR, BTN_TOP}

MENU_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_ARENA)],
        [KeyboardButton(text=BTN_GEAR), KeyboardButton(text=BTN_TOP)],
    ],
    resize_keyboard=True,
)

esc = html.escape


# ════════════════════════════════════════════════════════════════════
#  UI
# ════════════════════════════════════════════════════════════════════

def btn(text: str, data: str, style: Optional[str] = None) -> InlineKeyboardButton:
    try:
        return InlineKeyboardButton(text=text, callback_data=data, style=style)
    except TypeError:
        return InlineKeyboardButton(text=text, callback_data=data)


def ikb(*rows) -> InlineKeyboardMarkup:
    keyboard = []
    for row in rows:
        line = []
        for item in row:
            if len(item) == 3:
                line.append(btn(item[0], item[1], item[2]))
            else:
                line.append(btn(item[0], item[1]))
        keyboard.append(line)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ════════════════════════════════════════════════════════════════════
#  БОЙЦЫ
# ════════════════════════════════════════════════════════════════════

@dataclass
class Fighter:
    name: str
    max_hp: int
    hp: int
    weapon: str = "fists"
    armor: str = "none"
    crit: int = BASE_CRIT
    cd: int = 0
    stun: bool = False
    dots: list = field(default_factory=list)
    zone_hp: dict = field(default_factory=dict)
    # защита, выбранная на текущий раунд (None — не защищается)
    defend_zone: Optional[str] = None

    def __post_init__(self):
        w, a = WEAPONS[self.weapon], ARMORS[self.armor]
        self.w_dmg = w["dmg"]                                     # урон оружия
        self.armor_df = a["df"]                                   # защита брони (общая)
        self.spec_chance = min(w["chance"] + a["chance"], 70)
        self.spec_mult = 1 + a["dmg"] / 100
        self.spec_cd = max(0, BASE_SPEC_CD - a["cd"])
        if not self.zone_hp:
            self.zone_hp = {k: max(1, round(self.max_hp * z["hp"])) for k, z in BODY_ZONES.items()}
        self.max_zone = dict(self.zone_hp)

    def alive_zones(self):
        return [k for k, v in self.zone_hp.items() if v > 0]

    def is_dead(self) -> bool:
        return self.hp <= 0 or not self.alive_zones()

    def alive(self) -> bool:
        return not self.is_dead()

    def zone_armor(self, zone: str) -> int:
        """Защита зоны = общая защита брони × коэффициент зоны."""
        z = BODY_ZONES[zone]
        return round(self.armor_df * z["armor"])


def zones_status(f: Fighter) -> str:
    parts = []
    for k in ("head", "torso", "arms", "legs"):
        cur = max(0, f.zone_hp[k])
        maxz = f.max_zone[k]
        bar = "🟩" if cur > maxz * 0.5 else ("🟨" if cur > 0 else "🟥")
        armor = f.zone_armor(k)
        parts.append(f"{bar}{BODY_ZONES[k]['emoji']}{cur}(🛡{armor})")
    return " ".join(parts)


def hp_bar(f: Fighter) -> str:
    if f.max_hp <= 0:
        return ""
    filled = int(round(10 * f.hp / f.max_hp))
    return "█" * filled + "░" * (10 - filled)


def _add_dot(target: Fighter, name: str, dmg: int, rounds: int):
    target.dots = [d for d in target.dots if d["name"] != name]
    target.dots.append({"name": name, "dmg": dmg, "left": rounds})


def apply_damage(f: Fighter, zone: str, dmg: int) -> str:
    f.zone_hp[zone] = max(0, f.zone_hp[zone] - dmg)
    f.hp = max(0, f.hp - dmg)
    if f.zone_hp[zone] == 0:
        return f" 💥 {BODY_ZONES[zone]['name']} выведена из строя!"
    return ""


# ── Основной расчёт удара ───────────────────────────────────────────
# Правило: если атакуемая зона == защищаемая зона → урон 0 (полный блок).
# Иначе урон = (урон оружия × множитель зоны + разброс) − защита зоны бронёй.

def compute_hit(att: Fighter, dfn: Fighter, zone: str,
                mult: float = 1.0, ignore_def: bool = False) -> tuple[bool, int, str]:
    """
    Возвращает (попал_ли, урон, пометка).
    Если защита совпала с атакой — урон 0, пометка "заблокировано".
    """
    if dfn.defend_zone == zone:
        return False, 0, "блок"

    z = BODY_ZONES[zone]
    raw = att.w_dmg * z["dmg"] * random.uniform(0.9, 1.1) * mult
    armor = 0 if ignore_def else dfn.zone_armor(zone)
    dmg = max(1, round(raw - armor))
    return True, dmg, "hit"


def do_attack(att: Fighter, dfn: Fighter, zone: str, log: list):
    """Один удар атакующего по зоне. Возвращает True, если цель жива."""
    if att.stun:
        att.stun = False
        if att.cd > 0:
            att.cd -= 1
        log.append(f"💫 {att.name} оглушён и пропускает ход")
        return dfn.alive()

    ready = att.cd == 0
    if att.cd > 0:
        att.cd -= 1

    if zone not in dfn.alive_zones():
        zone = random.choice(dfn.alive_zones() or ["torso"])
    z = BODY_ZONES[zone]
    zname = f"{z['emoji']} {z['name']}"

    # Полный блок
    if dfn.defend_zone == zone:
        log.append(f"🛡 <b>Блок!</b> {dfn.name} закрыл {zname} — урон не прошёл")
        # откат спец-атаки всё равно тикает
        return dfn.alive()

    # Спец-атака
    can_special = ready and not (att.weapon == "sword" and dfn.hp > dfn.max_hp * 0.3)
    if can_special and random.random() * 100 < att.spec_chance:
        log.append(use_special(att, dfn, zone))
        att.cd = att.spec_cd
        return dfn.alive()

    hit, dmg, note = compute_hit(att, dfn, zone)
    if not hit:
        log.append(f"🛡 {dfn.name} заблокировал удар по {zname}")
        return dfn.alive()

    # крит
    is_crit = random.random() * 100 < min(att.crit * z["crit"], 95)
    if is_crit:
        dmg *= 2
    mark = apply_damage(dfn, zone, dmg)
    log.append(
        f"{'💥 Крит!' if is_crit else '👊'} {att.name} → {dfn.name} [{zname}]: "
        f"<b>−{dmg}</b> (🛡{dfn.zone_armor(zone)}){mark}"
    )
    return dfn.alive()


def use_special(att: Fighter, dfn: Fighter, zone: str) -> str:
    w = att.weapon
    m = att.spec_mult
    info = WEAPONS[w]
    z = BODY_ZONES[zone]
    zname = f"{z['emoji']} {z['name']}"
    head = f"{info['emoji']} <b>{info['spec']}!</b> "

    def raw(mult=1.0, ignore=False):
        return compute_hit(att, dfn, zone, mult, ignore)

    if w in ("fists", "dagger"):
        total = 0
        parts = []
        for _ in range(3):
            ok, dmg, _ = raw(0.4 * m)
            if ok:
                total += dmg
                parts.append(str(dmg))
        mark = apply_damage(dfn, zone, total) if total else ""
        return head + f"{att.name} [{zname}]: {' + '.join(parts) or '0'} = <b>−{total}</b>{mark}"

    if w == "sword":
        ok, dmg, _ = raw(3 * m)
        if not ok:
            return head + f"{dfn.name} заблокировал казнь по {zname}"
        mark = apply_damage(dfn, zone, dmg)
        return head + f"{att.name} [{zname}] → {dfn.name}: <b>−{dmg}</b>{mark}"

    if w == "axe":
        ok, dmg, _ = raw(m)
        if not ok:
            return head + f"{dfn.name} заблокировал кровопускание"
        mark = apply_damage(dfn, zone, dmg)
        bleed = max(1, round(dfn.max_hp * 0.05 * m))
        _add_dot(dfn, "🩸 Кровотечение", bleed, 3)
        return head + f"{att.name} [{zname}] → {dfn.name}: <b>−{dmg}</b>{mark}, кровь <b>{bleed}</b> ×3"

    if w == "bow":
        ok, dmg, _ = raw(2 * m, ignore_def=True)
        if not ok:
            return head + f"{dfn.name} заблокировал выстрел"
        mark = apply_damage(dfn, zone, dmg)
        return head + f"{att.name} [{zname}] → {dfn.name}: сквозь броню <b>−{dmg}</b>{mark}"

    if w == "staff":
        ok, dmg, _ = raw(m)
        if not ok:
            return head + f"{dfn.name} заблокировал огонь"
        mark = apply_damage(dfn, zone, dmg)
        burn = max(1, round(dmg * 0.3))
        _add_dot(dfn, "🔥 Горение", burn, 3)
        return head + f"{att.name} [{zname}] → {dfn.name}: <b>−{dmg}</b>{mark}, огонь <b>{burn}</b> ×3"

    if w == "hammer":
        ok, dmg, _ = raw(1.5 * m)
        if not ok:
            return head + f"{dfn.name} заблокировал удар молота"
        mark = apply_damage(dfn, zone, dmg)
        dfn.stun = True
        return head + f"{att.name} [{zname}] → {dfn.name}: <b>−{dmg}</b>{mark}, оглушён"

    return head + "что-то пошло не так"


def tick_dots(f: Fighter, log: list):
    for d in list(f.dots):
        f.hp = max(0, f.hp - d["dmg"])
        log.append(f"{d['name']}: {f.name} −{d['dmg']}")
        d["left"] -= 1
        if d["left"] <= 0:
            f.dots.remove(d)
        if f.hp == 0:
            log.append(f"☠️ {f.name} гибнет от эффектов")
            return


# ════════════════════════════════════════════════════════════════════
#  ПОШАГОВЫЙ ДУЭЛЬ
# ════════════════════════════════════════════════════════════════════
#
#  Раунд состоит из двух фаз:
#    Фаза 1: игрок ВЫБИРАЕТ что делать — атаковать или защищаться.
#    Фаза 2: если игрок атакует — соперник защищается; если игрок
#            защищается — соперник атакует.
#    Ходы чередуются: чётный раунд — игрок атакует, нечётный — защищается.
#
#  Полное состояние хранится в памяти, т.к. бой пошаговый.

@dataclass
class Duel:
    aid: int
    did: int
    a: Fighter
    b: Fighter
    player_attacks: bool          # True — игрок атакует в этом раунде
    round_no: int = 1
    log: list = field(default_factory=list)
    player_choice: Optional[str] = None    # выбранная зона (атака/защита)
    started: float = field(default_factory=time.time)

    def player(self) -> Fighter:
        return self.a

    def opponent(self) -> Fighter:
        return self.b


DUELS: dict[int, Duel] = {}


def start_duel(aid: int, did: int) -> Duel:
    a_row = get_player(aid)
    d_row = get_player(did)
    fa = player_fighter(a_row)
    fd = player_fighter(d_row)
    # случайно, кто атакует в первом раунде
    player_attacks = random.random() < 0.5
    duel = Duel(aid=aid, did=did, a=fa, b=fd, player_attacks=player_attacks)
    first = "Ты" if player_attacks else esc(d_row["name"])
    duel.log.append(f"🤺 Бой начался! В первом раунде атакует <b>{first}</b>.")
    DUELS[aid] = duel
    return duel


def render_duel(duel: Duel, head_extra: str = "") -> str:
    a, b = duel.a, duel.b
    body = "\n".join(duel.log[-14:]) if duel.log else "<i>Бой начинается…</i>"
    head = f"<b>Раунд {duel.round_no}</b>  ·  🤺 <b>{a.name}</b> vs <b>{b.name}</b>"
    status = (
        f"❤️ {a.name}: {a.hp}/{a.max_hp}  {hp_bar(a)}\n"
        f"   {zones_status(a)}\n"
        f"❤️ {b.name}: {b.hp}/{b.max_hp}  {hp_bar(b)}\n"
        f"   {zones_status(b)}"
    )
    return f"{head}\n\n{body}\n\n{status}{head_extra}"


def attack_keyboard() -> InlineKeyboardMarkup:
    rows = []
    line = []
    for k, z in BODY_ZONES.items():
        line.append((f"{z['emoji']} {z['name']} ×{z['dmg']:.1f}", f"duel:zone:{k}", "danger"))
        if len(line) == 2:
            rows.append(line)
            line = []
    if line:
        rows.append(line)
    rows.append([("⬅️ Отмена", "duel:cancel", "primary")])
    return ikb(*rows)


def defend_keyboard() -> InlineKeyboardMarkup:
    rows = []
    line = []
    for k, z in BODY_ZONES.items():
        line.append((f"{z['emoji']} {z['name']}", f"duel:zone:{k}", "success"))
        if len(line) == 2:
            rows.append(line)
            line = []
    if line:
        rows.append(line)
    rows.append([("⬅️ Отмена", "duel:cancel", "primary")])
    return ikb(*rows)


def zone_choice_keyboard(is_attack: bool) -> InlineKeyboardMarkup:
    return attack_keyboard() if is_attack else defend_keyboard()


def main_turn_keyboard(duel: Duel) -> InlineKeyboardMarkup:
    if duel.player_attacks:
        return ikb(
            [("⚔️ Выбрать зону удара", "duel:choose_attack", "danger")],
            [("🏃 Пропустить ход", "duel:skip", "primary")],
        )
    else:
        return ikb(
            [("🛡 Выбрать зону защиты", "duel:choose_defend", "success")],
            [("🏃 Пропустить ход", "duel:skip", "primary")],
        )


def resolve_round(duel: Duel, player_zone: Optional[str], log: list):
    """Разрешает раунд: атакующий бьёт, защищающийся защищает."""
    a, b = duel.a, duel.b
    if duel.player_attacks:
        attacker, defender = a, b
        attacker_name = "Ты"
    else:
        attacker, defender = b, a
        attacker_name = esc(duel.b.name)

    # защищающийся выбирает зону защиты: игрок — свою, бот — рандом/умно
    if duel.player_attacks:
        # игрок атакует, бот защищается — случайная зона
        defender.defend_zone = random.choice(list(BODY_ZONES.keys()))
        log.append(f"🛡 {defender.name} защищает {BODY_ZONES[defender.defend_zone]['emoji']} {BODY_ZONES[defender.defend_zone]['name']}")
    else:
        # соперник атакует, игрок защищается — зона игрока уже в player_zone
        defender.defend_zone = player_zone
        log.append(f"🛡 Ты защищаешь {BODY_ZONES[player_zone]['emoji']} {BODY_ZONES[player_zone]['name']}")

    # тик DOT-ов на атакующем до удара
    tick_dots(attacker, log)
    if attacker.is_dead():
        return

    # удар
    if duel.player_attacks:
        do_attack(attacker, defender, player_zone, log)
    else:
        ai_zone = ai_pick_attack_zone(defender)
        log.append(f"⚔️ {attacker.name} атакует {BODY_ZONES[ai_zone]['emoji']} {BODY_ZONES[ai_zone]['name']}")
        do_attack(attacker, defender, ai_zone, log)


def ai_pick_attack_zone(dfn: Fighter) -> str:
    """Соперник целится в слабую живую зону игрока."""
    alive = dfn.alive_zones()
    if not alive:
        return "torso"
    if random.random() < 0.35:
        return random.choice(alive)
    # если игрок часто защищает торс — бить в другие зоны
    weights = {}
    for k in alive:
        base = 1.0
        if dfn.defend_zone == k:
            base = 0.2
        # целься в слабую зону
        base *= 1.0 + (1 - dfn.zone_hp[k] / dfn.max_zone[k])
        weights[k] = base
    keys = list(weights.keys())
    vals = [weights[k] for k in keys]
    return random.choices(keys, weights=vals)[0]


# ════════════════════════════════════════════════════════════════════
#  БАЗА
# ════════════════════════════════════════════════════════════════════

_db = sqlite3.connect(DB_PATH, check_same_thread=False)
_db.row_factory = sqlite3.Row


def init_db():
    _db.executescript(
        """
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            name TEXT NOT NULL,
            chips INTEGER NOT NULL DEFAULT 0,
            wins INTEGER NOT NULL DEFAULT 0,
            losses INTEGER NOT NULL DEFAULT 0,
            weapon TEXT NOT NULL DEFAULT 'fists',
            armor TEXT NOT NULL DEFAULT 'none',
            weapons_owned TEXT NOT NULL DEFAULT 'fists',
            armors_owned TEXT NOT NULL DEFAULT 'none',
            last_pvp REAL NOT NULL DEFAULT 0,
            banned INTEGER NOT NULL DEFAULT 0,
            is_bot INTEGER NOT NULL DEFAULT 0,
            created REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            ts REAL NOT NULL,
            seen INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS ix_notif ON notifications(user_id, seen);
        CREATE TABLE IF NOT EXISTS pvp_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attacker INTEGER NOT NULL,
            defender INTEGER NOT NULL,
            ts REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_pvp ON pvp_log(attacker, defender, ts);
        """
    )
    _db.commit()


def q1(sql, args=()):
    return _db.execute(sql, args).fetchone()


def qa(sql, args=()):
    return _db.execute(sql, args).fetchall()


def ex(sql, args=()):
    cur = _db.execute(sql, args)
    _db.commit()
    return cur


def get_player(uid):
    return q1("SELECT * FROM players WHERE user_id=?", (uid,))


def create_player(uid, username, name):
    ex(
        "INSERT OR IGNORE INTO players (user_id, username, name, chips, wins, losses, "
        "weapon, armor, weapons_owned, armors_owned, created) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (uid, username, name, START_CHIPS, 0, 0, "fists", "none", "fists", "none", time.time()),
    )


def notify(uid, text):
    ex("INSERT INTO notifications (user_id, text, ts) VALUES (?,?,?)", (uid, text, time.time()))


def add_win(uid):
    ex("UPDATE players SET wins=wins+1 WHERE user_id=?", (uid,))


def add_loss(uid):
    # Поражение = −1 победа (не ниже 0) + +1 к счётчику поражений
    ex("UPDATE players SET losses=losses+1, wins=CASE WHEN wins>0 THEN wins-1 ELSE 0 END WHERE user_id=?",
       (uid,))


# ════════════════════════════════════════════════════════════════════
#  СКРЫТЫЕ СОПЕРНИКИ
# ════════════════════════════════════════════════════════════════════

def _random_bot_name(existing: set) -> str:
    for _ in range(300):
        base = random.choice(HUMAN_NAMES)
        title = random.choice(HUMAN_TITLES)
        suffix = str(random.randint(1, 99)) if random.random() < 0.35 else ""
        name = f"{base}{title}{suffix}"
        if name.lower() not in existing and 2 <= len(name) <= 16:
            existing.add(name.lower())
            return name
    return f"Игрок{random.randint(1000, 9999)}"


def ensure_masked_bots(count: int = 18):
    existing = {r["name"].lower() for r in qa("SELECT name FROM players")}
    bots = qa("SELECT user_id FROM players WHERE is_bot=1")
    need = max(0, count - len(bots))
    for _ in range(need):
        name = _random_bot_name(existing)
        uid = -random.randint(10_000_000, 99_999_999)
        wins = random.choices(
            [random.randint(0, 9), random.randint(10, 29), random.randint(30, 70)],
            weights=[5, 4, 2],
        )[0]
        losses = random.randint(wins // 2, wins * 2 + 3)
        weapon = random.choice(list(WEAPONS.keys()))
        armor = random.choice(list(ARMORS.keys()))
        ex(
            "INSERT INTO players (user_id, username, name, chips, wins, losses, "
            "weapon, armor, weapons_owned, armors_owned, is_bot, created) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (uid, None, name, random.randint(0, 500), wins, losses,
             weapon, armor, weapon, armor, 1, time.time()),
        )


# ════════════════════════════════════════════════════════════════════
#  ФАБРИКИ
# ════════════════════════════════════════════════════════════════════

def player_fighter(p) -> Fighter:
    arm = ARMORS[p["armor"]]
    max_hp = BASE_HP + arm["hp"]
    return Fighter(
        name=esc(p["name"]),
        max_hp=max_hp,
        hp=max_hp,
        weapon=p["weapon"],
        armor=p["armor"],
        crit=min(BASE_CRIT, CRIT_CAP),
    )


def stats_line(f: Fighter) -> str:
    return f"❤️{f.max_hp} ⚔️{f.w_dmg} 🛡{f.armor_df} 🎯{f.crit}%"


# ════════════════════════════════════════════════════════════════════
#  ЭКРАНЫ
# ════════════════════════════════════════════════════════════════════

async def safe_edit(cb: CallbackQuery, text: str, markup=None):
    try:
        await cb.message.edit_text(text[:4090], reply_markup=markup)
    except TelegramBadRequest as e:
        if "not modified" not in str(e):
            await cb.message.answer(text[:4090], reply_markup=markup)


def gear_screen(uid):
    p = get_player(uid)
    w, a = WEAPONS[p["weapon"]], ARMORS[p["armor"]]
    f = player_fighter(p)
    arena = ARENAS[arena_of(p["wins"])]
    lines = [
        f"🎒 <b>{esc(p['name'])}</b>",
        f"🏆 Победы: <b>{p['wins']}</b>  ·  💀 Поражения: {p['losses']}",
        f"💰 Фишки: <b>{p['chips']}</b>",
        f"📍 {arena['emoji']} <b>{arena['name']}</b>",
        "",
        f"❤️ HP: <b>{f.max_hp}</b>",
        f"⚔️ Урон оружия: <b>{f.w_dmg}</b>",
        f"🛡 Защита брони: <b>{f.armor_df}</b>",
        f"🎯 Крит: <b>{f.crit}%</b>",
        "",
        f"{w['emoji']} Оружие: <b>{w['name']}</b> — {w['spec']}",
        f"    {w['desc']}",
        f"{a['emoji']} Броня: <b>{a['name']}</b> — {a['desc']}",
        "",
        f"<b>Защита по зонам:</b>",
        zones_status(f),
    ]
    rows = [
        [("⚔️ Оружие", "gear:w", "primary"), ("🛡 Броня", "gear:a", "primary")],
    ]
    return "\n".join(lines), ikb(*rows)


def gear_list_screen(uid, page="w"):
    p = get_player(uid)
    is_w = page == "w"
    table = WEAPONS if is_w else ARMORS
    owned = set(p["weapons_owned" if is_w else "armors_owned"].split(","))
    equipped = p["weapon" if is_w else "armor"]

    lines = [f"🏪 <b>{'Оружие' if is_w else 'Броня'}</b>",
             f"💰 Фишки: <b>{p['chips']}</b>", ""]
    rows = [[("⚔️ Оружие" + (" •" if is_w else ""), "gear:w", "primary"),
             ("🛡 Броня" + ("" if is_w else " •"), "gear:a", "primary")]]
    for key, it in table.items():
        if is_w:
            lines.append(f"{it['emoji']} <b>{it['name']}</b> — урон {it['dmg']}, {it['spec']} (шанс {it['chance']}%)\n    {it['desc']}")
        else:
            lines.append(f"{it['emoji']} <b>{it['name']}</b> — защита {it['df']}, HP +{it['hp']}\n    {it['desc']}")
        if key == equipped:
            label, style = "✅ надето", "success"
        elif key in owned:
            label, style = "🎒 надеть", "primary"
        else:
            label, style = f"{it['price']}💰", "danger"
        rows.append([(f"{it['emoji']} {it['name']} · {label}", f"buy:{page}:{key}", style)])
    rows.append([("⬅️ Назад", "gear:menu", "success")])
    return "\n".join(lines), ikb(*rows)


def top_screen(uid, arena_key):
    a = ARENAS[arena_key]
    rows = qa(
        "SELECT user_id, name, wins, losses FROM players "
        "WHERE is_bot=0 AND banned=0 AND wins BETWEEN ? AND ? "
        "ORDER BY wins DESC, losses ASC LIMIT 20",
        (a["min_wins"], a["max_wins"]),
    )
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"{a['emoji']} <b>{a['name']}</b> — топ по победам", ""]
    if not rows:
        lines.append("<i>Пока никого нет на этой арене.</i>")
    for i, r in enumerate(rows):
        mark = medals[i] if i < 3 else f"{i + 1}."
        you = " ← ты" if r["user_id"] == uid else ""
        lines.append(f"{mark} <b>{esc(r['name'])}</b> — {r['wins']} 🏆 / {r['losses']} 💀{you}")
    me = get_player(uid)
    if me and all(r["user_id"] != uid for r in rows) and a["min_wins"] <= me["wins"] <= a["max_wins"]:
        rank = q1(
            "SELECT COUNT(*) c FROM players WHERE is_bot=0 AND banned=0 "
            "AND wins BETWEEN ? AND ? AND wins > ?",
            (a["min_wins"], a["max_wins"], me["wins"]),
        )["c"] + 1
        lines += ["…", f"{rank}. <b>{esc(me['name'])}</b> — {me['wins']} 🏆 / {me['losses']} 💀 ← ты"]
    lines += ["", "🏆 Победа: +1 🏆.  💀 Поражение: −1 🏆."]
    kb = ikb(
        [("🥉 Бронза", "top:bronze", "danger"),
         ("🥈 Серебро", "top:silver", "primary"),
         ("🥇 Золото", "top:gold", "success")],
        [("⬅️ Назад", "arena:menu", "success")],
    )
    return "\n".join(lines), kb


def arena_menu_screen(uid):
    p = get_player(uid)
    key = arena_of(p["wins"])
    a = ARENAS[key]
    text = (
        f"⚔️ <b>Арена Дуэлянтов</b>\n\n"
        f"🏆 Твои победы: <b>{p['wins']}</b>  ·  💀 Поражения: {p['losses']}\n"
        f"📍 Ты на {a['emoji']} <b>{a['name']}</b>\n\n"
        f"🥉 Бронза — 0–9 🏆\n"
        f"🥈 Серебро — 10–29 🏆\n"
        f"🥇 Золото — 30+ 🏆\n\n"
        f"<b>Правила боя:</b>\n"
        f"• Раунд: один атакует, другой защищается.\n"
        f"• Если защита совпала с атакой — урон не проходит.\n"
        f"• Урон = урон оружия − защита зоны бронёй.\n"
        f"• Победа: +1 🏆. Поражение: −1 🏆."
    )
    kb = ikb(
        [("🎲 Найти соперника", "arena:find", "success")],
        [("📋 Список соперников", "arena:list", "primary")],
        [("🔎 Вызвать по нику / ID", "arena:find_name", "primary")],
        [("🏆 Топ арен", "top:cur", "primary")],
    )
    return text, kb


def arena_list_screen(uid):
    p = get_player(uid)
    key = arena_of(p["wins"])
    a = ARENAS[key]
    rows = qa(
        "SELECT user_id, name, wins, losses FROM players "
        "WHERE user_id != ? AND banned=0 AND wins BETWEEN ? AND ? "
        "ORDER BY RANDOM() LIMIT 8",
        (uid, a["min_wins"], a["max_wins"]),
    )
    if not rows:
        return ("Сейчас на твоей арене никого нет — жми «Найти соперника».",
                ikb([("🎲 Найти", "arena:find", "success")],
                    [("⬅️ Назад", "arena:menu", "success")]))
    kb_rows = [
        [(f"{r['name'][:16]} · 🏆{r['wins']} / 💀{r['losses']}", f"duel:pick:{r['user_id']}", "primary")]
        for r in rows
    ]
    kb_rows.append([("⬅️ Назад", "arena:menu", "success")])
    return f"{a['emoji']} <b>{a['name']}</b> — соперники:", ikb(*kb_rows)


def pick_opponent(uid, wins):
    key = arena_of(wins)
    a = ARENAS[key]
    humans = qa(
        "SELECT user_id FROM players WHERE user_id != ? AND banned=0 AND is_bot=0 "
        "AND wins BETWEEN ? AND ? ORDER BY RANDOM() LIMIT 6",
        (uid, a["min_wins"], a["max_wins"]),
    )
    bots = qa(
        "SELECT user_id FROM players WHERE is_bot=1 AND banned=0 "
        "AND wins BETWEEN ? AND ? ORDER BY RANDOM() LIMIT 6",
        (a["min_wins"], a["max_wins"]),
    )
    hp = [r["user_id"] for r in humans]
    bp = [r["user_id"] for r in bots]
    if hp and bp:
        return random.choice(bp if random.random() < 0.6 else hp)
    if hp:
        return random.choice(hp)
    if bp:
        return random.choice(bp)
    ensure_masked_bots(24)
    rows = qa("SELECT user_id FROM players WHERE is_bot=1 ORDER BY RANDOM() LIMIT 1")
    return rows[0]["user_id"] if rows else None


# ════════════════════════════════════════════════════════════════════
#  ХЕНДЛЕРЫ
# ════════════════════════════════════════════════════════════════════

router = Router()
router.message.filter(F.chat.type == "private")


class Reg(StatesGroup):
    name = State()


class DuelFind(StatesGroup):
    target = State()


class AdminBroadcast(StatesGroup):
    text = State()


HELP_TEXT = (
    "⚔️ <b>Арена Дуэлянтов</b>\n\n"
    "Пошаговые PvP-бои.\n\n"
    "<b>Как проходит раунд:</b>\n"
    "1. Один боец атакует, другой защищается.\n"
    "2. Атакующий выбирает зону удара.\n"
    "3. Защищающийся выбирает зону защиты.\n"
    "4. Если зоны совпали — урон 0 (полный блок).\n"
    "5. Иначе урон = урон оружия − защита зоны бронёй.\n\n"
    "🏆 Победа: +1 🏆.  💀 Поражение: −1 🏆.\n\n"
    "Арены: 🥉 0–9, 🥈 10–29, 🥇 30+.\n"
    "Команды: /start, /menu, /help"
)


async def flush_notifications(m: Message):
    rows = qa("SELECT id, text FROM notifications WHERE user_id=? AND seen=0 ORDER BY id LIMIT 15",
              (m.from_user.id,))
    if not rows:
        return
    ids = [r["id"] for r in rows]
    ex(f"UPDATE notifications SET seen=1 WHERE id IN ({','.join('?' * len(ids))})", tuple(ids))
    await m.answer("📬 <b>Пока тебя не было:</b>\n\n" + "\n\n".join(r["text"] for r in rows))


def touch_username(m):
    ex("UPDATE players SET username=? WHERE user_id=?", (m.from_user.username, m.from_user.id))


def is_banned(uid):
    p = get_player(uid)
    return bool(p and p["banned"])


# ── /start, /help, /menu ───────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(m: Message, state: FSMContext):
    await state.clear()
    if is_banned(m.from_user.id):
        return await m.answer("🚫 Доступ закрыт.")
    ensure_masked_bots(18)
    p = get_player(m.from_user.id)
    if p:
        touch_username(m)
        await m.answer(f"С возвращением, <b>{esc(p['name'])}</b>! Арена ждёт 👇", reply_markup=MENU_KB)
        await flush_notifications(m)
        return
    await state.set_state(Reg.name)
    await m.answer(
        "⚔️ <b>Добро пожаловать на Арену Дуэлянтов!</b>\n\n"
        "Пошаговые PvP-бои: атака против защиты.\n\n"
        "Как зовут твоего бойца? (2–16 символов)",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Command("help"))
async def cmd_help(m: Message):
    await m.answer(HELP_TEXT, reply_markup=MENU_KB if get_player(m.from_user.id) else None)


@router.message(Command("menu"))
async def cmd_menu(m: Message, state: FSMContext):
    await state.clear()
    if is_banned(m.from_user.id):
        return await m.answer("🚫 Доступ закрыт.")
    if not get_player(m.from_user.id):
        return await m.answer("Сначала отправь /start.")
    await m.answer("Главное меню 👇", reply_markup=MENU_KB)
    await flush_notifications(m)


@router.message(Reg.name, F.text)
async def reg_name(m: Message, state: FSMContext):
    name = " ".join(m.text.split())
    if not 2 <= len(name) <= 16 or name.startswith("/"):
        return await m.answer("Имя должно быть от 2 до 16 символов. Попробуй ещё раз:")
    if q1("SELECT 1 FROM players WHERE LOWER(name)=LOWER(?)", (name,)):
        name = f"{name}{random.randint(1, 99)}"
    create_player(m.from_user.id, m.from_user.username, name)
    ensure_masked_bots(18)
    await state.clear()
    await m.answer(
        f"Боец <b>{esc(name)}</b> создан! 🎉\n\n"
        f"Стартовое снаряжение: 👊 Кулаки, 👕 без брони.\n"
        f"Начни с «⚔️ Арена».",
        reply_markup=MENU_KB,
    )


# ── Ввод имени ────────────────────────────────────────────────────

@router.message(DuelFind.target, F.text)
async def duel_find_target(m: Message, state: FSMContext):
    if m.text in MENU_TEXTS:
        return await menu_dispatch(m, state)
    await state.clear()
    key = m.text.strip().lstrip("@")
    p = get_player(m.from_user.id)
    row = None
    if key.isdigit():
        row = q1("SELECT user_id FROM players WHERE user_id=? AND banned=0", (int(key),))
    if not row:
        row = q1(
            "SELECT user_id FROM players WHERE (LOWER(username)=LOWER(?) OR LOWER(name)=LOWER(?)) "
            "AND banned=0 LIMIT 1",
            (key, key),
        )
    if not row:
        target = pick_opponent(m.from_user.id, p["wins"])
        if not target:
            return await m.answer("Не удалось подобрать соперника.")
        return await begin_duel_msg(m, target)
    await begin_duel_msg(m, row["user_id"])


# ── Меню ───────────────────────────────────────────────────────────

async def show_arena(m):
    t, k = arena_menu_screen(m.from_user.id)
    await m.answer(t, reply_markup=k)


async def show_gear(m):
    t, k = gear_screen(m.from_user.id)
    await m.answer(t, reply_markup=k)


async def show_top(m):
    p = get_player(m.from_user.id)
    t, k = top_screen(m.from_user.id, arena_of(p["wins"]))
    await m.answer(t, reply_markup=k)


MENU_HANDLERS = {
    BTN_ARENA: show_arena,
    BTN_GEAR: show_gear,
    BTN_TOP: show_top,
}


async def menu_dispatch(m, state):
    await state.clear()
    if is_banned(m.from_user.id):
        return await m.answer("🚫 Доступ закрыт.")
    if not get_player(m.from_user.id):
        return await m.answer("Сначала отправь /start.")
    touch_username(m)
    await flush_notifications(m)
    await MENU_HANDLERS[m.text](m)


@router.message(F.text.in_(MENU_TEXTS))
async def on_menu(m: Message, state: FSMContext):
    await menu_dispatch(m, state)


# ── Запуск боя ────────────────────────────────────────────────────

async def begin_duel_msg(m: Message, did: int):
    aid = m.from_user.id
    if did == aid:
        return await m.answer("🤨 Нельзя драться с самим собой.")
    if aid in DUELS:
        return await m.answer("У тебя уже идёт бой — заверши его.")
    d = get_player(did)
    if not d:
        return await m.answer("Соперник недоступен.")
    duel = start_duel(aid, did)
    text = render_duel(duel)
    if duel.player_attacks:
        head = "\n\n<b>Раунд 1: ты атакуешь.</b> Выбери действие."
    else:
        head = f"\n\n<b>Раунд 1: {duel.b.name} атакует.</b> Ты защищаешься."
    await m.answer(text + head, reply_markup=main_turn_keyboard(duel))


async def begin_duel_cb(cb: CallbackQuery, did: int):
    aid = cb.from_user.id
    if did == aid:
        return await cb.answer("Нельзя драться с собой.", show_alert=True)
    if aid in DUELS:
        return await cb.answer("У тебя уже идёт бой.", show_alert=True)
    d = get_player(did)
    if not d:
        return await cb.answer("Соперник недоступен.", show_alert=True)
    duel = start_duel(aid, did)
    text = render_duel(duel)
    if duel.player_attacks:
        head = "\n\n<b>Раунд 1: ты атакуешь.</b> Выбери действие."
    else:
        head = f"\n\n<b>Раунд 1: {duel.b.name} атакует.</b> Ты защищаешься."
    await safe_edit(cb, text + head, main_turn_keyboard(duel))
    await cb.answer()


# ── Колбэки боя ───────────────────────────────────────────────────

def get_duel(cb: CallbackQuery) -> Optional[Duel]:
    return DUELS.get(cb.from_user.id)


@router.callback_query(F.data == "duel:choose_attack")
async def cb_choose_attack(cb: CallbackQuery):
    duel = get_duel(cb)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    if not duel.player_attacks:
        return await cb.answer("Сейчас ты защищаешься.", show_alert=True)
    text = render_duel(duel, head_extra="\n\n⚔️ <b>Куда бьём?</b>")
    await safe_edit(cb, text, attack_keyboard())
    await cb.answer()


@router.callback_query(F.data == "duel:choose_defend")
async def cb_choose_defend(cb: CallbackQuery):
    duel = get_duel(cb)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    if duel.player_attacks:
        return await cb.answer("Сейчас ты атакуешь.", show_alert=True)
    text = render_duel(duel, head_extra="\n\n🛡 <b>Какую зону защищаем?</b>")
    await safe_edit(cb, text, defend_keyboard())
    await cb.answer()


@router.callback_query(F.data == "duel:cancel")
async def cb_cancel(cb: CallbackQuery):
    duel = get_duel(cb)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    text = render_duel(duel)
    if duel.player_attacks:
        head = "\n\n<b>Твой ход.</b> Ты атакуешь."
    else:
        head = f"\n\n<b>Твой ход.</b> {duel.b.name} атакует, ты защищаешься."
    await safe_edit(cb, text + head, main_turn_keyboard(duel))
    await cb.answer()


@router.callback_query(F.data == "duel:skip")
async def cb_skip(cb: CallbackQuery):
    duel = get_duel(cb)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    # пропуск: игрок не защищается / не атакует — эквивалент «пропустить»
    player_zone = None
    await resolve_and_advance(cb, duel, player_zone)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^duel:zone:(head|torso|arms|legs)$"))
async def cb_zone(cb: CallbackQuery):
    duel = get_duel(cb)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    zone = cb.data.split(":")[2]
    await resolve_and_advance(cb, duel, zone)
    await cb.answer()


async def resolve_and_advance(cb: CallbackQuery, duel: Duel, zone: Optional[str]):
    """Разрешает раунд с выбранной зоной, проверяет конец боя и переключает фазу."""
    log = duel.log
    log.append(f"<b>— Раунд {duel.round_no} —</b>")

    # Защищающийся сбрасывает старую защиту
    duel.a.defend_zone = None
    duel.b.defend_zone = None

    if duel.player_attacks:
        # игрок атакует, бот защищается. zone = куда бьёт игрок (None = пропуск)
        if zone:
            bot_zone = random.choice(list(BODY_ZONES.keys()))
            duel.b.defend_zone = bot_zone
            log.append(f"🛡 {duel.b.name} защищает {BODY_ZONES[bot_zone]['emoji']} {BODY_ZONES[bot_zone]['name']}")
            tick_dots(duel.a, log)
            if duel.a.is_dead():
                return await finish_duel(cb, duel, winner_is_a=False)
            do_attack(duel.a, duel.b, zone, log)
            if duel.b.is_dead():
                return await finish_duel(cb, duel, winner_is_a=True)
        else:
            log.append("🏃 Ты пропустил атаку.")
    else:
        # бот атакует, игрок защищается. zone = куда защищается игрок (None = не защищается)
        if zone:
            duel.a.defend_zone = zone
            log.append(f"🛡 Ты защищаешь {BODY_ZONES[zone]['emoji']} {BODY_ZONES[zone]['name']}")
        else:
            log.append("🏃 Ты не защищаешься.")
        tick_dots(duel.b, log)
        if duel.b.is_dead():
            return await finish_duel(cb, duel, winner_is_a=True)
        ai_zone = ai_pick_attack_zone(duel.a)
        log.append(f"⚔️ {duel.b.name} атакует {BODY_ZONES[ai_zone]['emoji']} {BODY_ZONES[ai_zone]['name']}")
        do_attack(duel.b, duel.a, ai_zone, log)
        if duel.a.is_dead():
            return await finish_duel(cb, duel, winner_is_a=False)

    # переход к следующему раунду: смена ролей
    duel.round_no += 1
    duel.player_attacks = not duel.player_attacks

    text = render_duel(duel)
    if duel.player_attacks:
        head = "\n\n<b>Твой ход.</b> Ты атакуешь."
    else:
        head = f"\n\n<b>Твой ход.</b> {duel.b.name} атакует, ты защищаешься."
    await safe_edit(cb, text + head, main_turn_keyboard(duel))


async def finish_duel(cb: CallbackQuery, duel: Duel, winner_is_a: bool):
    aid, did = duel.aid, duel.did
    DUELS.pop(aid, None)
    a_row = get_player(aid)
    d_row = get_player(did)
    if not a_row or not d_row:
        return await safe_edit(cb, "Бой прерван.", ikb([("⚔️ На арену", "arena:menu", "success")]))

    if winner_is_a:
        add_win(aid)
        add_loss(did)
        if did > 0:
            notify(did, f"💀 <b>{esc(a_row['name'])}</b> одолел тебя на арене. −1 🏆")
        result_line = "🏆 <b>Победа!</b> +1 🏆"
    else:
        add_win(did)
        add_loss(aid)
        if did > 0:
            notify(did, f"🏆 <b>{esc(a_row['name'])}</b> проиграл тебе на арене. +1 🏆")
        result_line = "💀 <b>Поражение.</b> −1 🏆"

    new_a = get_player(aid)
    new_arena = ARENAS[arena_of(new_a["wins"])]
    foot = (
        f"{result_line}\n"
        f"🏆 Победы: {new_a['wins']}  ·  💀 Поражения: {new_a['losses']}\n"
        f"📍 Ты на {new_arena['emoji']} <b>{new_arena['name']}</b>"
    )
    text = render_duel(duel, head_extra="\n\n" + foot)
    kb = ikb(
        [("⚔️ На арену", "arena:menu", "success")],
        [("🎲 Ещё раз", "arena:find", "danger")],
    )
    await safe_edit(cb, text, kb)


# ── Арена: поиск/список ───────────────────────────────────────────

@router.callback_query(F.data == "arena:menu")
async def cb_arena_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = arena_menu_screen(cb.from_user.id)
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data == "arena:find")
async def cb_arena_find(cb: CallbackQuery):
    p = get_player(cb.from_user.id)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    if cb.from_user.id in DUELS:
        return await cb.answer("У тебя уже идёт бой.", show_alert=True)
    oid = pick_opponent(cb.from_user.id, p["wins"])
    if not oid:
        return await cb.answer("Не удалось подобрать соперника.", show_alert=True)
    await begin_duel_cb(cb, oid)


@router.callback_query(F.data == "arena:list")
async def cb_arena_list(cb: CallbackQuery):
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = arena_list_screen(cb.from_user.id)
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data == "arena:find_name")
async def cb_arena_find_name(cb: CallbackQuery, state: FSMContext):
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    await state.set_state(DuelFind.target)
    await cb.message.answer("🔎 Отправь @username, ID или имя бойца.")
    await cb.answer()


@router.callback_query(F.data.regexp(r"^duel:pick:-?\d+$"))
async def cb_duel_pick(cb: CallbackQuery):
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    tid = int(cb.data.split(":")[2])
    await begin_duel_cb(cb, tid)


# ── Топ ────────────────────────────────────────────────────────────

@router.callback_query(F.data.regexp(r"^top:(cur|bronze|silver|gold)$"))
async def cb_top(cb: CallbackQuery):
    p = get_player(cb.from_user.id)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    key = cb.data.split(":")[1]
    if key == "cur":
        key = arena_of(p["wins"])
    t, k = top_screen(cb.from_user.id, key)
    await safe_edit(cb, t, k)
    await cb.answer()


# ── Снаряжение ────────────────────────────────────────────────────

@router.callback_query(F.data == "gear:menu")
async def cb_gear_menu(cb: CallbackQuery):
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = gear_screen(cb.from_user.id)
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^gear:[wa]$"))
async def cb_gear_page(cb: CallbackQuery):
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = gear_list_screen(cb.from_user.id, cb.data.split(":")[1])
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^buy:[wa]:\w+$"))
async def cb_buy(cb: CallbackQuery):
    p = get_player(cb.from_user.id)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    _, kind, key = cb.data.split(":")
    table = WEAPONS if kind == "w" else ARMORS
    if key not in table:
        return await cb.answer()
    owned_col = "weapons_owned" if kind == "w" else "armors_owned"
    eq_col = "weapon" if kind == "w" else "armor"
    owned = p[owned_col].split(",")
    item = table[key]
    if key in owned:
        ex(f"UPDATE players SET {eq_col}=? WHERE user_id=?", (key, cb.from_user.id))
        toast = f"Надето: {item['name']}"
    elif p["chips"] >= item["price"]:
        ex(f"UPDATE players SET chips=chips-?, {owned_col}=?, {eq_col}=? WHERE user_id=?",
           (item["price"], ",".join(owned + [key]), key, cb.from_user.id))
        toast = f"Куплено: {item['name']}"
    else:
        return await cb.answer(f"Не хватает: нужно {item['price']}💰", show_alert=True)
    t, k = gear_list_screen(cb.from_user.id, kind)
    await safe_edit(cb, t, k)
    await cb.answer(toast)


# ── Админка ───────────────────────────────────────────────────────

def admin_only(uid):
    return uid == ADMIN_ID


@router.message(Command("admin"))
async def cmd_admin(m: Message):
    if not admin_only(m.from_user.id):
        return
    await m.answer(
        "🛠 <b>Админ-панель</b>\n\n"
        "/give &lt;user_id&gt; &lt;chips&gt;\n"
        "/setwins &lt;user_id&gt; &lt;n&gt;\n"
        "/ban &lt;user_id&gt;\n"
        "/unban &lt;user_id&gt;\n"
        "/broadcast — рассылка\n"
        "/stats — статистика\n"
        "/addbots &lt;n&gt; — добавить скрытых соперников\n"
        "/endduel &lt;user_id&gt; — принудительно завершить бой"
    )


@router.message(Command("stats"))
async def cmd_stats(m: Message):
    if not admin_only(m.from_user.id):
        return
    total = q1("SELECT COUNT(*) c FROM players WHERE is_bot=0")["c"]
    bots = q1("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    banned = q1("SELECT COUNT(*) c FROM players WHERE banned=1")["c"]
    duels = len(DUELS)
    await m.answer(
        f"📊 Игроков: {total}\n🤖 Скрытых соперников: {bots}\n🚫 Забанено: {banned}\n⚔️ Активных боёв: {duels}"
    )


@router.message(Command("addbots"))
async def cmd_addbots(m: Message):
    if not admin_only(m.from_user.id):
        return
    parts = m.text.split()
    n = int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 6
    before = q1("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    ensure_masked_bots(before + n)
    after = q1("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    await m.answer(f"✅ Добавлено: {after - before}")


@router.message(Command("give"))
async def cmd_give(m: Message):
    if not admin_only(m.from_user.id):
        return
    parts = m.text.split()
    if len(parts) != 3 or not parts[1].lstrip("-").isdigit() or not parts[2].lstrip("-").isdigit():
        return await m.answer("Использование: /give <user_id> <chips>")
    uid, amount = int(parts[1]), int(parts[2])
    if not get_player(uid):
        return await m.answer("Игрок не найден.")
    ex("UPDATE players SET chips=chips+? WHERE user_id=?", (amount, uid))
    await m.answer(f"✅ Выдано {amount}💰 игроку {uid}")
    if uid > 0:
        notify(uid, f"🎁 Тебе начислено {amount}💰")


@router.message(Command("setwins"))
async def cmd_setwins(m: Message):
    if not admin_only(m.from_user.id):
        return
    parts = m.text.split()
    if len(parts) != 3 or not parts[1].lstrip("-").isdigit() or not parts[2].isdigit():
        return await m.answer("Использование: /setwins <user_id> <n>")
    uid, n = int(parts[1]), int(parts[2])
    if not get_player(uid):
        return await m.answer("Игрок не найден.")
    ex("UPDATE players SET wins=? WHERE user_id=?", (n, uid))
    await m.answer(f"✅ Установлено {n} 🏆 игроку {uid}")
    if uid > 0:
        notify(uid, f"🎁 Тебе установлено {n} 🏆")


@router.message(Command("ban"))
async def cmd_ban(m: Message):
    if not admin_only(m.from_user.id):
        return
    parts = m.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await m.answer("Использование: /ban <user_id>")
    uid = int(parts[1])
    ex("UPDATE players SET banned=1 WHERE user_id=?", (uid,))
    DUELS.pop(uid, None)
    await m.answer(f"🚫 Игрок {uid} забанен.")


@router.message(Command("unban"))
async def cmd_unban(m: state Message):
    if not.clear admin_only(m.from_user.id()
):
        return
    parts    = m.text.split()
    rows if len(parts) !=  =2 or not parts[1].isdigit():
        return await m.answer("Использование: /unban <user_id>")
    uid = int(parts[1])
    ex("UPDATE players SET banned=0 WHERE user_id=?", (uid,))
    await m.answer(f"✅ Игрок {uid} разбанен.")


@router.message(Command("endduel"))
async def cmd_endduel(m: Message):
    if not admin_only(m.from_user.id):
        return
    parts = m.text.split()
    if len(parts) != 2 or not parts[1].lstrip("-").isdigit():
        return await m.answer("Использование: /endduel <user_id>")
    uid = int(parts[1])
    if uid in DUELS:
        DUELS.pop(uid, None)
        await m.answer(f"✅ Бой игрока {uid} сброшен.")
    else:
        await m.answer("У игрока нет активного боя.")


@router.message(Command("broadcast"))
async def cmd_broadcast(m: Message, state: FSMContext):
    if not admin_only(m.from_user.id):
        return
    await state.set_state(AdminBroadcast.text)
    await m.answer("📢 Отправь текст рассылки. /cancel — отмена.")


@router.message(AdminBroadcast.text, F.text)
async def broadcast_send(m: Message, state: FSMContext, bot: Bot):
    if m.text == "/cancel":
        await state.clear()
        return await m.answer("Отменено.")
    await qa("SELECT user_id FROM players WHERE banned=0 AND is_bot=0")
    ok = 0
    for r in rows:
        try:
            await bot.send_message(r["user_id"], f"📢 <b>Сообщение:</b>\n\n{m.text}")
            ok += 1
        except Exception:
            pass
    await m.answer(f"✅ Отправлено {ok} игрокам.")


# ── Fallback ──────────────────────────────────────────────────────

@router.message()
async def fallback(m: Message):
    if not get_player(m.from_user.id):
        return await m.answer("Отправь /start, чтобы создать бойца ⚔️")
    if is_banned(m.from_user.id):
        return await m.answer("🚫 Доступ закрыт.")
    await m.answer("Пользуйся меню внизу 👇", reply_markup=MENU_KB)


# ════════════════════════════════════════════════════════════════════
#  ЗАПУСК
# ════════════════════════════════════════════════════════════════════

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not BOT_TOKEN:
        raise SystemExit("Задай BOT_TOKEN.")
    init_db()
    ensure_masked_bots(18)
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать / вернуться"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="help", description="Правила"),
    ])
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())