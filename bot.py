#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚔️ Арена Дуэлянтов — PvP-онли, последовательные бои, 3 арены по победам.
Прогресс = только победы. Поражение отнимает 1 победу.
Боты маскируются под игроков и не показываются в топе.
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

START_CHIPS = 100          # оставлено как счётчик монет, если захочешь вернуть магазин
CRIT_CAP = 60
DEF_FACTOR = 0.7
BASE_SPEC_CD = 3
MAX_ROUNDS = 60
TURN_TIMEOUT = 90          # секунд на ход (антифлуд)

# Зоны тела — общие и для атаки, и для защиты
BODY_ZONES = {
    "head":  dict(name="Голова",  emoji="🧠", dmg=1.6, crit=2.2, hit=0.70, hp=0.20),
    "torso": dict(name="Торс",    emoji="🫀", dmg=1.0, crit=1.0, hit=0.92, hp=0.45),
    "arms":  dict(name="Руки",    emoji="💪", dmg=0.8, crit=0.8, hit=0.88, hp=0.20),
    "legs":  dict(name="Ноги",    emoji="🦵", dmg=0.9, crit=0.9, hit=0.85, hp=0.15),
}

# ── Арены ───────────────────────────────────────────────────────────
ARENAS = {
    "bronze":   dict(name="Бронзовая арена", emoji="🥉", min_wins=0,  max_wins=9),
    "silver":   dict(name="Серебряная арена", emoji="🥈", min_wins=10, max_wins=29),
    "gold":     dict(name="Золотая арена",   emoji="🥇", min_wins=30, max_wins=10**9),
}
ARENA_ORDER = ["bronze", "silver", "gold"]


def arena_of(wins: int) -> str:
    for key in ARENA_ORDER:
        a = ARENAS[key]
        if a["min_wins"] <= wins <= a["max_wins"]:
            return key
    return "gold"


# ── Оружие и броня (без прокачки, только экипировка) ───────────────
WEAPONS = {
    "fists":  dict(emoji="👊", name="Кулаки", spec="Серия ударов",
                   desc="3 удара по 40% урона", price=0, chance=25),
    "dagger": dict(emoji="🗡", name="Кинжал", spec="Тысяча порезов",
                   desc="3 удара по 40% урона", price=100, chance=30),
    "sword":  dict(emoji="⚔️", name="Меч", spec="Казнь",
                   desc="добивает цель с HP < 30% (урон ×3)", price=250, chance=28),
    "axe":    dict(emoji="🪓", name="Топор", spec="Кровопускание",
                   desc="кровотечение: 5% макс. HP, 3 раунда", price=400, chance=24),
    "bow":    dict(emoji="🏹", name="Лук", spec="Снайперский выстрел",
                   desc="100% крит, игнорирует защиту", price=550, chance=22),
    "staff":  dict(emoji="🔥", name="Посох", spec="Огненный шторм",
                   desc="горение: 30% урона, 3 раунда", price=700, chance=22),
    "hammer": dict(emoji="🔨", name="Молот", spec="Землетрясение",
                   desc="150% урона + оглушение", price=900, chance=18),
}

ARMORS = {
    "none":   dict(emoji="👕", name="Без брони",   df=0,  hp=0,  price=0,   chance=0,  cd=0, dmg=0,  desc="—"),
    "light":  dict(emoji="🥋", name="Лёгкая",      df=3,  hp=10, price=80,  chance=10, cd=0, dmg=0,  desc="+10% шанс спец-атаки"),
    "medium": dict(emoji="🛡", name="Средняя",     df=6,  hp=25, price=200, chance=0,  cd=1, dmg=0,  desc="−1 к откату спец-атаки"),
    "heavy":  dict(emoji="🏋️", name="Тяжёлая",     df=10, hp=50, price=400, chance=0,  cd=0, dmg=20, desc="+20% урон спец-атаки"),
    "legend": dict(emoji="✨", name="Легендарная", df=15, hp=80, price=800, chance=15, cd=0, dmg=30, desc="+15% шанс, +30% урон спец-атаки"),
}

# Базовые статы — фиксированные, никакой прокачки
BASE_STATS = dict(hp=120, atk=14, defense=5, spd=10, crit=8)

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
#  БОЕВОЙ ДВИЖОК — ПОШАГОВЫЙ
# ════════════════════════════════════════════════════════════════════

@dataclass
class Fighter:
    name: str
    max_hp: int
    hp: int
    atk: int
    df: int
    spd: int
    crit: int
    weapon: str = "fists"
    armor: str = "none"
    cd: int = 0
    stun: bool = False
    dots: list = field(default_factory=list)
    zone_hp: dict = field(default_factory=dict)
    defending: Optional[str] = None

    def __post_init__(self):
        w, a = WEAPONS[self.weapon], ARMORS[self.armor]
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


def zones_status(f: Fighter) -> str:
    parts = []
    for k in ("head", "torso", "arms", "legs"):
        cur = max(0, f.zone_hp[k])
        bar = "🟩" if cur > f.max_zone[k] * 0.5 else ("🟨" if cur > 0 else "🟥")
        parts.append(f"{bar}{BODY_ZONES[k]['emoji']}{cur}")
    return " ".join(parts)


def hp_bar(f: Fighter) -> str:
    if f.max_hp <= 0:
        return ""
    filled = int(round(10 * f.hp / f.max_hp))
    return "█" * filled + "░" * (10 - filled)


def hit_damage(att: Fighter, dfn: Fighter, zone: str, mult: float = 1.0, ignore_def: bool = False) -> int:
    z = BODY_ZONES[zone]
    base = att.atk * random.uniform(0.85, 1.15) * z["dmg"]
    reduction = 0 if ignore_def else dfn.df * DEF_FACTOR
    # если цель защищает эту зону — режем урон
    if dfn.defending == zone:
        mult *= 0.45
    return max(1, round((base - reduction) * mult))


def apply_damage(f: Fighter, zone: str, dmg: int) -> str:
    f.zone_hp[zone] = max(0, f.zone_hp[zone] - dmg)
    f.hp = max(0, f.hp - dmg)
    if f.zone_hp[zone] == 0:
        return f" 💥 {BODY_ZONES[zone]['name']} выведена из строя!"
    return ""


def _add_dot(target: Fighter, name: str, dmg: int, rounds: int):
    target.dots = [d for d in target.dots if d["name"] != name]
    target.dots.append({"name": name, "dmg": dmg, "left": rounds})


def use_special(att: Fighter, dfn: Fighter, zone: str) -> str:
    w = att.weapon
    m = att.spec_mult
    info = WEAPONS[w]
    head = f"{info['emoji']} <b>{info['spec']}!</b> "

    if w in ("fists", "dagger"):
        hits = [hit_damage(att, dfn, zone, 0.4 * m) for _ in range(3)]
        total = sum(hits)
        note = apply_damage(dfn, zone, total)
        return head + f"{att.name}: {' + '.join(map(str, hits))} = <b>−{total}</b>{note}"
    if w == "sword":
        dmg = hit_damage(att, dfn, zone, 3 * m)
        note = apply_damage(dfn, zone, dmg)
        return head + f"{att.name} → {dfn.name} [{BODY_ZONES[zone]['name']}]: <b>−{dmg}</b>{note}"
    if w == "axe":
        dmg = hit_damage(att, dfn, zone, m)
        note = apply_damage(dfn, zone, dmg)
        bleed = max(1, round(dfn.max_hp * 0.05 * m))
        _add_dot(dfn, "🩸 Кровотечение", bleed, 3)
        return head + f"{att.name} → {dfn.name}: <b>−{dmg}</b>{note}, кровь по <b>{bleed}</b> ×3"
    if w == "bow":
        dmg = hit_damage(att, dfn, zone, 2 * m, ignore_def=True)
        note = apply_damage(dfn, zone, dmg)
        return head + f"{att.name} → {dfn.name}: крит сквозь броню <b>−{dmg}</b>{note}"
    if w == "staff":
        dmg = hit_damage(att, dfn, zone, m)
        note = apply_damage(dfn, zone, dmg)
        burn = max(1, round(dmg * 0.3))
        _add_dot(dfn, "🔥 Горение", burn, 3)
        return head + f"{att.name} → {dfn.name}: <b>−{dmg}</b>{note}, огонь по <b>{burn}</b> ×3"
    if w == "hammer":
        dmg = hit_damage(att, dfn, zone, 1.5 * m)
        note = apply_damage(dfn, zone, dmg)
        dfn.stun = True
        return head + f"{att.name} → {dfn.name}: <b>−{dmg}</b>{note}, цель оглушена"
    raise ValueError(w)


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


def do_attack(att: Fighter, dfn: Fighter, zone: str, log: list):
    """Один удар по зоне. Возвращает True, если цель жива."""
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

    can_special = ready and not (att.weapon == "sword" and dfn.hp > dfn.max_hp * 0.3)
    if can_special and random.random() * 100 < att.spec_chance:
        log.append(use_special(att, dfn, zone))
        att.cd = att.spec_cd
        return dfn.alive()

    # промах зависит от того, защищает ли цель эту зону
    hit_chance = z["hit"]
    if dfn.defending == zone:
        hit_chance -= 0.25
    if random.random() > hit_chance:
        log.append(f"🌀 {att.name} промахнулся по «{z['name']}»")
        return dfn.alive()

    dmg = hit_damage(att, dfn, zone)
    is_crit = random.random() * 100 < att.crit * z["crit"]
    if is_crit:
        dmg *= 2
    note = apply_damage(dfn, zone, dmg)
    log.append(
        f"{'💥 Крит!' if is_crit else '👊'} {att.name} → {dfn.name} "
        f"[{z['emoji']} {z['name']}]: <b>−{dmg}</b>{note}"
    )
    return dfn.alive()


def ai_pick_attack_zone(dfn: Fighter) -> str:
    """Бот бьёт по слабой живой зоне игрока."""
    alive = dfn.alive_zones()
    if not alive:
        return "torso"
    if random.random() < 0.4:
        return random.choice(alive)
    return min(alive, key=lambda k: dfn.zone_hp[k])


def ai_pick_defend_zone() -> str:
    # бот чаще защищает торс, иногда голову
    return random.choices(
        ["torso", "head", "arms", "legs"],
        weights=[45, 30, 15, 10],
    )[0]


# ── Состояние боя (в памяти) ────────────────────────────────────────
# key = (attacker_id, opponent_id) — активный бой.
# Бой идёт в памяти, т.к. пошаговый. При рестарте — сбрасывается.

@dataclass
class Duel:
    aid: int
    did: int
    a: Fighter
    b: Fighter
    turn: str              # "a" — ходит игрок, "b" — ходит соперник
    round_no: int = 1
    log: list = field(default_factory=list)
    first_zone: Optional[str] = None
    started: float = field(default_factory=time.time)

    def current(self) -> Fighter:
        return self.a if self.turn == "a" else self.b

    def opponent_of(self, f: Fighter) -> Fighter:
        return self.b if f is self.a else self.a


DUELS: dict[int, Duel] = {}          # aid -> Duel (одновременно не больше одного на игрока)


def duel_end_text(duel: Duel, winner_is_a: bool) -> tuple[str, InlineKeyboardMarkup]:
    kb = ikb([("⚔️ На арену", "arena:menu", "success")])
    if winner_is_a:
        return "🏆 <b>Победа!</b>", kb
    return "💀 <b>Поражение.</b>", kb


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
    s = BASE_STATS
    ex(
        "INSERT OR IGNORE INTO players (user_id, username, name, chips, wins, losses, "
        "weapon, armor, weapons_owned, armors_owned, created) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (uid, username, name, START_CHIPS, 0, 0, "fists", "none", "fists", "none", time.time()),
    )


def notify(uid, text):
    ex("INSERT INTO notifications (user_id, text, ts) VALUES (?,?,?)", (uid, text, time.time()))


def add_win(uid: int):
    ex("UPDATE players SET wins=wins+1 WHERE user_id=?", (uid,))


def add_loss(uid: int):
    # при поражении вычитаем 1 победу, но не ниже нуля
    ex("UPDATE players SET losses=losses+1, wins=CASE WHEN wins>0 THEN wins-1 ELSE 0 END WHERE user_id=?",
       (uid,))


def stats_line(f: Fighter) -> str:
    return f"❤️{f.max_hp} ⚔️{f.atk} 🛡{f.df} 💨{f.spd} 🎯{f.crit}%"


# ════════════════════════════════════════════════════════════════════
#  СКРЫТЫЕ СОПЕРНИКИ (маскированные боты)
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
        # бот распределяется по арене случайно, но с уклоном в слабые
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
            (uid, None, name, random.randint(0, 300), wins, losses,
             weapon, armor, weapon, armor, 1, time.time()),
        )


# ════════════════════════════════════════════════════════════════════
#  ФАБРИКИ
# ════════════════════════════════════════════════════════════════════

def player_fighter(p) -> Fighter:
    arm = ARMORS[p["armor"]]
    max_hp = BASE_STATS["hp"] + arm["hp"]
    return Fighter(
        name=esc(p["name"]),
        max_hp=max_hp,
        hp=max_hp,
        atk=BASE_STATS["atk"],
        df=BASE_STATS["defense"] + arm["df"],
        spd=BASE_STATS["spd"],
        crit=min(BASE_STATS["crit"], CRIT_CAP),
        weapon=p["weapon"],
        armor=p["armor"],
    )


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
    lines = [
        f"🎒 <b>{esc(p['name'])}</b>",
        f"🏆 Победы: <b>{p['wins']}</b>  ·  💀 Поражения: {p['losses']}",
        f"💰 Фишки: <b>{p['chips']}</b>",
        f"📍 Арена: {ARENAS[arena_of(p['wins'])]['emoji']} {ARENAS[arena_of(p['wins'])]['name']}",
        "",
        f"❤️ HP: <b>{f.max_hp}</b>",
        f"⚔️ Атака: <b>{f.atk}</b>",
        f"🛡 Защита: <b>{f.df}</b>",
        f"💨 Скорость: <b>{f.spd}</b>",
        f"🎯 Крит: <b>{f.crit}%</b>",
        "",
        f"{w['emoji']} Оружие: <b>{w['name']}</b> — {w['spec']}",
        f"    {w['desc']}",
        f"{a['emoji']} Броня: <b>{a['name']}</b> — {a['desc']}",
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
            lines.append(f"{it['emoji']} <b>{it['name']}</b> — {it['spec']} (шанс {it['chance']}%)\n    {it['desc']}")
        else:
            lines.append(f"{it['emoji']} <b>{it['name']}</b> — DEF +{it['df']}, HP +{it['hp']}\n    {it['desc']}")
        if key == equipped:
            label, style = "✅ надето", "success"
        elif key in owned:
            label, style = "🎒 надеть", "primary"
        else:
            label, style = f"{it['price']}💰", "danger"
        rows.append([(f"{it['emoji']} {it['name']} · {label}", f"buy:{page}:{key}", style)])
    rows.append([("⬅️ Назад", "gear:menu", "success")])
    return "\n".join(lines), ikb(*rows)


def top_screen(uid, arena_key: str):
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
            "SELECT COUNT(*) c FROM players WHERE is_bot=0 AND banned=0 AND wins BETWEEN ? AND ? AND wins > ?",
            (a["min_wins"], a["max_wins"], me["wins"]),
        )["c"] + 1
        lines += ["…", f"{rank}. <b>{esc(me['name'])}</b> — {me['wins']} 🏆 / {me['losses']} 💀 ← ты"]
    lines += ["", f"🏆 Победы дают переход на арену выше. 💀 Поражение забирает 1 победу."]
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
        f"🥉 Бронза — 0–9 побед\n"
        f"🥈 Серебро — 10–29 побед\n"
        f"🥇 Золото — 30+ побед\n\n"
        f"<b>Победа +1 🏆. Поражение −1 🏆.</b> Выпасть с арены можно."
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
                ikb([("🎲 Найти", "arena:find", "success")], [("⬅️ Назад", "arena:menu", "success")]))
    kb_rows = [
        [(f"{r['name'][:16]} · 🏆{r['wins']} / 💀{r['losses']}", f"duel:pick:{r['user_id']}", "primary")]
        for r in rows
    ]
    kb_rows.append([("⬅️ Назад", "arena:menu", "success")])
    return f"{a['emoji']} <b>{a['name']}</b> — соперники:", ikb(*kb_rows)


def pick_opponent(uid, wins):
    """Находит соперника на той же арене. Если живых нет — подсовывает бота."""
    key = arena_of(wins)
    a = ARENAS[key]
    # сначала живые игроки на этой же арене
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
#  ПОШАГОВЫЙ БОЙ
# ════════════════════════════════════════════════════════════════════

def start_duel(aid: int, did: int) -> Duel:
    a = get_player(aid)
    d = get_player(did)
    fa = player_fighter(a)
    fd = player_fighter(d)
    # кто первый — по скорости; у обоих spd 10, бросаем монетку
    turn = "a" if random.random() < 0.5 else "b"
    duel = Duel(aid=aid, did=did, a=fa, b=fd, turn=turn, round_no=1)
    duel.log.append(f"🤺 Бой начался! Первым ходит <b>{duel.current().name}</b>.")
    DUELS[aid] = duel
    return duel


def duel_player_turn_keyboard(duel: Duel) -> InlineKeyboardMarkup:
    rows = [
        [("🛡 Защититься", "duel:defend_menu", "primary")],
    ]
    return ikb(*rows)


def duel_attack_keyboard() -> InlineKeyboardMarkup:
    rows = []
    line = []
    for k, z in BODY_ZONES.items():
        line.append((f"{z['emoji']} {z['name']} ×{z['dmg']:.1f}", f"duel:atk:{k}", "danger"))
        if len(line) == 2:
            rows.append(line)
            line = []
    if line:
        rows.append(line)
    rows.append([("⬅️ Назад", "duel:turn", "primary")])
    return ikb(*rows)


def duel_defend_keyboard() -> InlineKeyboardMarkup:
    rows = []
    line = []
    for k, z in BODY_ZONES.items():
        line.append((f"{z['emoji']} {z['name']}", f"duel:def:{k}", "success"))
        if len(line) == 2:
            rows.append(line)
            line = []
    if line:
        rows.append(line)
    rows.append([("⬅️ Назад", "duel:turn", "primary")])
    return ikb(*rows)


async def render_player_turn(cb: CallbackQuery, duel: Duel, note: str = ""):
    player_is_a = duel.turn == "a"
    prefix = f"<b>Твой ход</b>" if player_is_a else f"<b>Ход соперника</b>"
    text = render_duel(duel, head_extra=f"\n\n{prefix}. {note}" if note else f"\n\n{prefix}.")
    if player_is_a:
        kb = ikb(
            [("⚔️ Атаковать", "duel:attack_menu", "danger")],
            [("🛡 Защититься", "duel:defend_menu", "primary")],
        )
    else:
        kb = ikb([("▶️ Продолжить", "duel:continue", "success")])
    await safe_edit(cb, text, kb)


async def finish_duel(cb: CallbackQuery, duel: Duel, winner_is_a: bool):
    aid, did = duel.aid, duel.did
    DUELS.pop(aid, None)
    a_row = get_player(aid)
    d_row = get_player(did)

    if winner_is_a:
        add_win(aid)
        add_loss(did)
        notify(did, f"💀 <b>{esc(a_row['name'])}</b> одолел тебя на арене. −1 🏆")
        result_line = "🏆 <b>Победа!</b> +1 🏆"
    else:
        add_win(did)
        add_loss(aid)
        notify(did, f"🏆 <b>{esc(a_row['name'])}</b> проиграл тебе на арене. +1 🏆")
        result_line = "💀 <b>Поражение.</b> −1 🏆"

    new_a = get_player(aid)
    new_d = get_player(did)
    new_arena = ARENAS[arena_of(new_a["wins"])]
    foot = (
        f"{result_line}\n"
        f"🏆 Победы: {new_a['wins']}  ·  💀 Поражения: {new_a['losses']}\n"
        f"📍 Ты на {new_arena['emoji']} <b>{new_arena['name']}</b>\n"
        f"Соперник: {esc(new_d['name'])} — {new_d['wins']} 🏆"
    )
    text = render_duel(duel, head_extra="\n\n" + foot)
    kb = ikb([("⚔️ На арену", "arena:menu", "success")],
             [("🎲 Ещё раз", "arena:find", "danger")])
    await safe_edit(cb, text, kb)


async def advance_after_player(duel: Duel):
    """Если игрок походил — ход переходит к сопернику. Возвращает True, если бой продолжается."""
    if duel.a.is_dead() or duel.b.is_dead():
        return False
    duel.turn = "b"
    duel.round_no += 1
    return True


async def advance_after_opponent(duel: Duel):
    if duel.a.is_dead() or duel.b.is_dead():
        return False
    duel.turn = "a"
    return True


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
    "Только PvP. Прокачки нет — только победы и снаряжение.\n\n"
    "🥉 Бронза — 0–9 🏆\n"
    "🥈 Серебро — 10–29 🏆\n"
    "🥇 Золото — 30+ 🏆\n\n"
    "В бою ты сам выбираешь, <b>куда бить</b> и <b>что защищать</b>.\n"
    "Победа: +1 🏆. Поражение: −1 🏆.\n\n"
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


def touch_username(m: Message):
    ex("UPDATE players SET username=? WHERE user_id=?", (m.from_user.username, m.from_user.id))


def is_banned(uid) -> bool:
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
        "Только PvP, никакой прокачки — только победы и снаряжение.\n\n"
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
        f"Стартовое снаряжение: 👊 Кулаки и 👕 без брони.\n"
        f"Начни с «⚔️ Арена» — найдёшь соперника по силе.",
        reply_markup=MENU_KB,
    )


# ── Ввод имени для поиска ─────────────────────────────────────────

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
        return await begin_duel(m.from_user.id, target, m)
    await begin_duel(m.from_user.id, row["user_id"], m)


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


# ── Запуск боя из сообщения ───────────────────────────────────────

async def begin_duel(aid: int, did: int, m: Message):
    if did == aid:
        return await m.answer("🤨 Нельзя драться с самим собой.")
    if aid in DUELS:
        return await m.answer("У тебя уже идёт бой — заверши его.")
    d = get_player(did)
    if not d:
        return await m.answer("Соперник недоступен.")
    if d["is_bot"]:
        # маскировка: не показываем, что это бот
        pass
    duel = start_duel(aid, did)
    text = render_duel(duel)
    kb = ikb(
        [("⚔️ Атаковать", "duel:attack_menu", "danger")],
        [("🛡 Защититься", "duel:defend_menu", "primary")],
    )
    await m.answer(text, reply_markup=kb)


# ── Колбэки боя ────────────────────────────────────────────────────

def get_duel(cb: CallbackQuery) -> Optional[Duel]:
    return DUELS.get(cb.from_user.id)


@router.callback_query(F.data == "duel:turn")
async def cb_duel_turn(cb: CallbackQuery):
    duel = get_duel(cb)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    if duel.turn != "a":
        return await cb.answer("Сейчас не твой ход.", show_alert=True)
    await render_player_turn(cb, duel)
    await cb.answer()


@router.callback_query(F.data == "duel:attack_menu")
async def cb_duel_attack_menu(cb: CallbackQuery):
    duel = get_duel(cb)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    if duel.turn != "a":
        return await cb.answer("Сейчас не твой ход.", show_alert=True)
    text = render_duel(duel, head_extra="\n\n<b>Куда бьём?</b>")
    await safe_edit(cb, text, duel_attack_keyboard())
    await cb.answer()


@router.callback_query(F.data == "duel:defend_menu")
async def cb_duel_defend_menu(cb: CallbackQuery):
    duel = get_duel(cb)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    if duel.turn != "a":
        return await cb.answer("Сейчас не твой ход.", show_alert=True)
    text = render_duel(duel, head_extra="\n\n<b>Какую зону защищаем в этот раунд?</b>")
    await safe_edit(cb, text, duel_defend_keyboard())
    await cb.answer()


@router.callback_query(F.data.regexp(r"^duel:atk:(head|torso|arms|legs)$"))
async def cb_duel_attack(cb: CallbackQuery):
    duel = get_duel(cb)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    if duel.turn != "a":
        return await cb.answer("Сейчас не твой ход.", show_alert=True)
    zone = cb.data.split(":")[2]

    duel.a.defending = None
    duel.log.append(f"<b>Раунд {duel.round_no}</b>")
    tick_dots(duel.a, duel.log)
    if duel.a.is_dead():
        return await finish_duel(cb, duel, winner_is_a=False)

    do_attack(duel.a, duel.b, zone, duel.log)

    if duel.b.is_dead():
        return await finish_duel(cb, duel, winner_is_a=True)

    # переход хода к сопернику — игрок увидит кнопку "Продолжить"
    duel.turn = "b"
    duel.round_no += 1
    await render_player_turn(cb, duel, note=f"Ты атаковал: {BODY_ZONES[zone]['emoji']} {BODY_ZONES[zone]['name']}.")
    await cb.answer()


@router.callback_query(F.data.regexp(r"^duel:def:(head|torso|arms|legs)$"))
async def cb_duel_defend(cb: CallbackQuery):
    duel = get_duel(cb)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    if duel.turn != "a":
        return await cb.answer("Сейчас не твой ход.", show_alert=True)
    zone = cb.data.split(":")[2]
    duel.a.defending = zone
    duel.log.append(f"<b>Раунд {duel.round_no}</b>")
    duel.log.append(f"🛡 {duel.a.name} защищает: {BODY_ZONES[zone]['emoji']} {BODY_ZONES[zone]['name']}")

    tick_dots(duel.a, duel.log)
    if duel.a.is_dead():
        return await finish_duel(cb, duel, winner_is_a=False)

    duel.turn = "b"
    duel.round_no += 1
    await render_player_turn(cb, duel, note=f"Ты защищаешь: {BODY_ZONES[zone]['emoji']} {BODY_ZONES[zone]['name']}.")
    await cb.answer()


@router.callback_query(F.data == "duel:continue")
async def cb_duel_continue(cb: CallbackQuery):
    """Ход соперника — считаем его атаку/защиту и возвращаем ход игроку."""
    duel = get_duel(cb)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    if duel.turn != "b":
        return await cb.answer("Сейчас не ход соперника.", show_alert=True)

    # сброс прошлой защиты игрока
    duel.a.defending = None
    # соперник выбирает зону атаки и (иногда) защиту
    atk_zone = ai_pick_attack_zone(duel.a)
    duel.b.defending = ai_pick_defend_zone() if random.random() < 0.5 else None

    if duel.b.defending:
        duel.log.append(f"🛡 {duel.b.name} защищает: {BODY_ZONES[duel.b.defending]['emoji']} {BODY_ZONES[duel.b.defending]['name']}")

    tick_dots(duel.b, duel.log)
    if duel.b.is_dead():
        return await finish_duel(cb, duel, winner_is_a=True)

    do_attack(duel.b, duel.a, atk_zone, duel.log)

    if duel.a.is_dead():
        return await finish_duel(cb, duel, winner_is_a=False)

    duel.turn = "a"
    await render_player_turn(cb, duel, note=f"{duel.b.name} атакует {BODY_ZONES[atk_zone]['emoji']} {BODY_ZONES[atk_zone]['name']}.")
    await cb.answer()


# ── Арена: поиск и список ─────────────────────────────────────────

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
    duel = start_duel(cb.from_user.id, oid)
    text = render_duel(duel)
    kb = ikb(
        [("⚔️ Атаковать", "duel:attack_menu", "danger")],
        [("🛡 Защититься", "duel:defend_menu", "primary")],
    )
    await safe_edit(cb, text, kb)
    await cb.answer()


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
    p = get_player(cb.from_user.id)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    if cb.from_user.id in DUELS:
        return await cb.answer("У тебя уже идёт бой.", show_alert=True)
    tid = int(cb.data.split(":")[2])
    if tid == cb.from_user.id:
        return await cb.answer("Нельзя драться с собой.", show_alert=True)
    duel = start_duel(cb.from_user.id, tid)
    text = render_duel(duel)
    kb = ikb(
        [("⚔️ Атаковать", "duel:attack_menu", "danger")],
        [("🛡 Защититься", "duel:defend_menu", "primary")],
    )
    await safe_edit(cb, text, kb)
    await cb.answer()


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

def admin_only(uid: int) -> bool:
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
    await m.answer(f"📊 Игроков: {total}\n🤖 Скрытых соперников: {bots}\n🚫 Забанено: {banned}\n⚔️ Активных боёв: {duels}")


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
async def cmd_unban(m: Message):
    if not admin_only(m.from_user.id):
        return
    parts = m.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
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
    await state.clear()
    rows = qa("SELECT user_id FROM players WHERE banned=0 AND is_bot=0")
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