#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚔️ Арена Дуэлянтов — PvP-онли, пошаговый бой по зонам.
Атакующий выбирает зону удара → Защищающийся выбирает зону защиты.
Совпало → блок. Не совпало → урон = оружие - защита_зоны.
Прогресс = победы. Поражение −1 победа. 3 арены. Боты скрыты, в топ не входят.
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
MAX_ROUNDS = 80

# ── Зоны тела ───────────────────────────────────────────────────────
ZONES = ["head", "torso", "arms", "legs"]
ZONE_INFO = {
    "head":  dict(name="Голова", emoji="🧠", mult=1.5),
    "torso": dict(name="Торс",   emoji="🫀", mult=1.0),
    "arms":  dict(name="Руки",   emoji="💪", mult=0.8),
    "legs":  dict(name="Ноги",   emoji="🦵", mult=0.9),
}

# ── Оружие: урон, спец-атака ────────────────────────────────────────
WEAPONS = {
    "fists":  dict(emoji="👊", name="Кулаки",  dmg=10, spec="Серия ударов",
                   desc="3 быстрых удара по 50% урона", price=0, chance=25),
    "dagger": dict(emoji="🗡", name="Кинжал",  dmg=14, spec="Тысяча порезов",
                   desc="3 удара по 50% урона", price=150, chance=30),
    "sword":  dict(emoji="⚔️", name="Меч",     dmg=20, spec="Казнь",
                   desc="двойной урон по зоне", price=350, chance=28),
    "axe":    dict(emoji="🪓", name="Топор",   dmg=26, spec="Кровопускание",
                   desc="+5 урона в следующие 3 раунда", price=550, chance=24),
    "bow":    dict(emoji="🏹", name="Лук",     dmg=32, spec="Снайперский выстрел",
                   desc="игнорирует защиту брони", price=800, chance=22),
    "staff":  dict(emoji="🔥", name="Посох",   dmg=38, spec="Огненный шторм",
                   desc="+6 урона в следующие 3 раунда", price=1100, chance=22),
    "hammer": dict(emoji="🔨", name="Молот",   dmg=46, spec="Землетрясение",
                   desc="×2 урона и оглушение", price=1600, chance=18),
}

# ── Броня: защита по каждой зоне ────────────────────────────────────
# armor_def = {head, torso, arms, legs}
ARMORS = {
    "none": dict(
        emoji="👕", name="Без брони", hp=0, price=0, chance=0, dmg_bonus=0,
        desc="—",
        armor_def=dict(head=0, torso=0, arms=0, legs=0),
    ),
    "light": dict(
        emoji="🥋", name="Лёгкая", hp=10, price=120, chance=10, dmg_bonus=0,
        desc="+10% шанс спец-атаки",
        armor_def=dict(head=1, torso=3, arms=2, legs=2),
    ),
    "medium": dict(
        emoji="🛡", name="Средняя", hp=25, price=320, chance=0, dmg_bonus=0,
        desc="ровная защита всех зон",
        armor_def=dict(head=3, torso=6, arms=4, legs=4),
    ),
    "heavy": dict(
        emoji="🏋️", name="Тяжёлая", hp=50, price=650, chance=0, dmg_bonus=20,
        desc="+20% урона спец-атаки",
        armor_def=dict(head=5, torso=10, arms=7, legs=7),
    ),
    "legend": dict(
        emoji="✨", name="Легендарная", hp=80, price=1200, chance=15, dmg_bonus=30,
        desc="+15% шанс, +30% урон спец-атаки",
        armor_def=dict(head=8, torso=14, arms=10, legs=10),
    ),
}

BASE_STATS = dict(hp=140)

# ── Арены ───────────────────────────────────────────────────────────
ARENAS = {
    "bronze": dict(name="Бронзовая арена", emoji="🥉", min_wins=0,  max_wins=9),
    "silver": dict(name="Серебряная арена", emoji="🥈", min_wins=10, max_wins=29),
    "gold":   dict(name="Золотая арена",   emoji="🥇", min_wins=30, max_wins=10**9),
}
ARENA_ORDER = ["bronze", "silver", "gold"]


def arena_of(wins: int) -> str:
    for k in ARENA_ORDER:
        a = ARENAS[k]
        if a["min_wins"] <= wins <= a["max_wins"]:
            return k
    return "gold"


# ── Человеческие ники для скрытых соперников ────────────────────────
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
    kb = []
    for row in rows:
        line = []
        for item in row:
            if len(item) == 3:
                line.append(btn(item[0], item[1], item[2]))
            else:
                line.append(btn(item[0], item[1]))
        kb.append(line)
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ════════════════════════════════════════════════════════════════════
#  БОЕЦ
# ════════════════════════════════════════════════════════════════════

@dataclass
class Fighter:
    name: str
    max_hp: int
    hp: int
    weapon: str
    armor: str
    dots: list = field(default_factory=list)
    stun: bool = False

    def __post_init__(self):
        w = WEAPONS[self.weapon]
        a = ARMORS[self.armor]
        self.weapon_dmg = w["dmg"]
        self.armor_def = dict(a["armor_def"])
        self.spec_chance = min(w["chance"] + a["chance"], 70)
        self.spec_dmg_bonus = a["dmg_bonus"] / 100.0

    def alive(self) -> bool:
        return self.hp > 0

    def armor_of(self, zone: str) -> int:
        return self.armor_def.get(zone, 0)

    def weapon_of_zone(self, zone: str) -> int:
        return max(1, round(self.weapon_dmg * ZONE_INFO[zone]["mult"]))


def hp_bar(f: Fighter) -> str:
    if f.max_hp <= 0:
        return ""
    filled = int(round(10 * f.hp / f.max_hp))
    return "█" * filled + "░" * (10 - filled)


def fighter_card(f: Fighter) -> str:
    w = WEAPONS[f.weapon]
    a = ARMORS[f.armor]
    ad = f.armor_def
    return (
        f"<b>{f.name}</b>  ❤️{f.hp}/{f.max_hp}\n"
        f"{hp_bar(f)}\n"
        f"{w['emoji']} {w['name']} (урон {f.weapon_dmg})  ·  {a['emoji']} {a['name']}\n"
        f"🛡 Защита: 🧠{ad['head']} 🫀{ad['torso']} 💪{ad['arms']} 🦵{ad['legs']}"
    )


# ════════════════════════════════════════════════════════════════════
#  РАСЧЁТ УРОНА
# ════════════════════════════════════════════════════════════════════

def compute_damage(att: Fighter, dfn: Fighter, atk_zone: str, def_zone: Optional[str],
                   ignore_armor: bool = False, extra_mult: float = 1.0) -> tuple[int, str]:
    """
    Возвращает (урон, описание).
    Если atk_zone == def_zone → полный блок, урон 0.
    Иначе урон = оружие_зоны - защита_зоны. Минимум 1.
    """
    if def_zone == atk_zone:
        return 0, "🛡 <b>Заблокировано!</b>"
    weapon_dmg = att.weapon_of_zone(atk_zone)
    armor = 0 if ignore_armor else dfn.armor_of(atk_zone)
    dmg = weapon_dmg - armor
    if extra_mult != 1.0:
        dmg = round(dmg * extra_mult)
    dmg = max(1, dmg)
    return dmg, ""


def tick_dots(f: Fighter, log: list):
    for d in list(f.dots):
        f.hp = max(0, f.hp - d["dmg"])
        log.append(f"{d['name']}: {f.name} −{d['dmg']}")
        d["left"] -= 1
        if d["left"] <= 0:
            f.dots.remove(d)
        if f.hp <= 0:
            log.append(f"☠️ {f.name} гибнет от эффектов")
            return


def _add_dot(target: Fighter, name: str, dmg: int, rounds: int):
    target.dots = [d for d in target.dots if d["name"] != name]
    target.dots.append({"name": name, "dmg": dmg, "left": rounds})


def apply_special(att: Fighter, dfn: Fighter, atk_zone: str, def_zone: Optional[str],
                  log: list) -> bool:
    """Возвращает True, если спец-атака сработала (и урон уже нанесён)."""
    w = WEAPONS[att.weapon]
    spec_name = w["spec"]

    if def_zone == atk_zone:
        log.append(f"🛡 {dfn.name} заблокировал <b>{spec_name}</b>!")
        return True  # спец-атака «состоялась», но была заблокирована

    if att.weapon == "fists" or att.weapon == "dagger":
        hits = []
        total = 0
        for _ in range(3):
            d, _ = compute_damage(att, dfn, atk_zone, def_zone)
            d = max(1, round(d * 0.5))
            hits.append(d)
            total += d
        dfn.hp = max(0, dfn.hp - total)
        log.append(f"{w['emoji']} <b>{spec_name}!</b> {' + '.join(map(str, hits))} = <b>−{total}</b>")
        return True

    if att.weapon == "sword":
        d, _ = compute_damage(att, dfn, atk_zone, def_zone, extra_mult=2.0)
        dfn.hp = max(0, dfn.hp - d)
        log.append(f"{w['emoji']} <b>{spec_name}!</b> {att.name} → {dfn.name} "
                   f"[{ZONE_INFO[atk_zone]['emoji']} {ZONE_INFO[atk_zone]['name']}]: <b>−{d}</b>")
        return True

    if att.weapon == "axe":
        d, _ = compute_damage(att, dfn, atk_zone, def_zone)
        dfn.hp = max(0, dfn.hp - d)
        bleed = max(1, round(dfn.max_hp * 0.04))
        _add_dot(dfn, "🩸 Кровотечение", bleed, 3)
        log.append(f"{w['emoji']} <b>{spec_name}!</b> {att.name} → {dfn.name}: <b>−{d}</b>, "
                   f"кровь по <b>{bleed}</b> ×3")
        return True

    if att.weapon == "bow":
        d, _ = compute_damage(att, dfn, atk_zone, def_zone, ignore_armor=True, extra_mult=1.5)
        dfn.hp = max(0, dfn.hp - d)
        log.append(f"{w['emoji']} <b>{spec_name}!</b> {att.name} → {dfn.name} сквозь броню: <b>−{d}</b>")
        return True

    if att.weapon == "staff":
        d, _ = compute_damage(att, dfn, atk_zone, def_zone)
        dfn.hp = max(0, dfn.hp - d)
        burn = max(1, round(d * 0.4))
        _add_dot(dfn, "🔥 Горение", burn, 3)
        log.append(f"{w['emoji']} <b>{spec_name}!</b> {att.name} → {dfn.name}: <b>−{d}</b>, "
                   f"огонь по <b>{burn}</b> ×3")
        return True

    if att.weapon == "hammer":
        d, _ = compute_damage(att, dfn, atk_zone, def_zone, extra_mult=2.0)
        dfn.hp = max(0, dfn.hp - d)
        dfn.stun = True
        log.append(f"{w['emoji']} <b>{spec_name}!</b> {att.name} → {dfn.name}: <b>−{d}</b>, оглушён")
        return True

    return False


def resolve_attack(att: Fighter, dfn: Fighter, atk_zone: str, def_zone: Optional[str],
                   log: list) -> None:
    """
    Один ход атакующего. Учитывает оглушение, спец-атаку, блок, обычный удар.
    """
    if att.stun:
        att.stun = False
        log.append(f"💫 {att.name} оглушён и пропускает ход")
        return

    # спец-атака
    if random.random() * 100 < att.spec_chance:
        if apply_special(att, dfn, atk_zone, def_zone, log):
            return

    # обычный удар
    dmg, note = compute_damage(att, dfn, atk_zone, def_zone)
    if note:
        log.append(f"{ZONE_INFO[atk_zone]['emoji']} {att.name} бьёт в «{ZONE_INFO[atk_zone]['name']}» — {note}")
        return

    dfn.hp = max(0, dfn.hp - dmg)
    log.append(
        f"👊 {att.name} → {dfn.name} "
        f"[{ZONE_INFO[atk_zone]['emoji']} {ZONE_INFO[atk_zone]['name']}]: <b>−{dmg}</b>"
    )


# ════════════════════════════════════════════════════════════════════
#  ДУЭЛЬ (пошаговая, через память)
# ════════════════════════════════════════════════════════════════════

@dataclass
class Duel:
    a_id: int
    b_id: int
    a: Fighter
    b: Fighter
    phase: str               # "a_attack" | "b_defend" | "b_attack" | "a_defend" | "done"
    round_no: int = 1
    atk_zone: Optional[str] = None       # выбранная атакующим зона (ждёт защиту)
    attacker_is_a: bool = True
    log: list = field(default_factory=list)
    started: float = field(default_factory=time.time)

    def me(self, uid: int) -> Optional[Fighter]:
        if uid == self.a_id:
            return self.a
        if uid == self.b_id:
            return self.b
        return None

    def opponent(self, uid: int) -> Optional[Fighter]:
        if uid == self.a_id:
            return self.b
        if uid == self.b_id:
            return self.a
        return None

    def state_for(self, uid: int) -> str:
        """Кто этот игрок сейчас: 'attacker' | 'defender' | 'none'."""
        if uid == self.a_id:
            return "attacker" if self.attacker_is_a else "defender"
        if uid == self.b_id:
            return "defender" if self.attacker_is_a else "attacker"
        return "none"


DUELS: dict[int, Duel] = {}


def start_duel(aid: int, bid: int) -> Duel:
    a_row = get_player(aid)
    b_row = get_player(bid)
    fa = fighter_from_row(a_row)
    fb = fighter_from_row(b_row)
    attacker_is_a = random.random() < 0.5
    duel = Duel(
        a_id=aid, b_id=bid, a=fa, b=fb,
        phase="a_attack" if attacker_is_a else "b_attack",
        attacker_is_a=attacker_is_a,
    )
    first = duel.a.name if attacker_is_a else duel.b.name
    duel.log.append(f"🤺 Бой начался! Первым атакует <b>{first}</b>.")
    DUELS[aid] = duel
    if bid > 0:
        DUELS[bid] = duel
    return duel


def end_duel(duel: Duel):
    DUELS.pop(duel.a_id, None)
    if duel.b_id > 0:
        DUELS.pop(duel.b_id, None)


# ════════════════════════════════════════════════════════════════════
#  КЛАВИАТУРЫ БОЯ
# ════════════════════════════════════════════════════════════════════

def attack_zone_kb() -> InlineKeyboardMarkup:
    rows = []
    line = []
    for k in ZONES:
        z = ZONE_INFO[k]
        line.append((f"{z['emoji']} {z['name']}", f"duel:atk:{k}", "danger"))
        if len(line) == 2:
            rows.append(line)
            line = []
    if line:
        rows.append(line)
    return ikb(*rows)


def defend_zone_kb() -> InlineKeyboardMarkup:
    rows = []
    line = []
    for k in ZONES:
        z = ZONE_INFO[k]
        line.append((f"{z['emoji']} {z['name']}", f"duel:def:{k}", "success"))
        if len(line) == 2:
            rows.append(line)
            line = []
    if line:
        rows.append(line)
    return ikb(*rows)


def duel_status_text(duel: Duel, for_uid: int, extra: str = "") -> str:
    role = duel.state_for(for_uid)
    a, b = duel.a, duel.b
    atk_name = a.name if duel.attacker_is_a else b.name
    def_name = b.name if duel.attacker_is_a else a.name

    if role == "attacker":
        prompt = "🎯 <b>Твой ход — выбирай, куда бить</b>"
    elif role == "defender":
        prompt = f"🛡 <b>{atk_name} атакует — выбирай, что защищать</b>"
    else:
        prompt = "⏳ Бой идёт…"

    body = "\n".join(duel.log[-14:]) if duel.log else "<i>Бой начинается…</i>"
    return (
        f"<b>Раунд {duel.round_no}</b>\n\n"
        f"{fighter_card(a)}\n\n"
        f"{fighter_card(b)}\n\n"
        f"<b>Лог:</b>\n{body}\n\n"
        f"{prompt}"
        + (f"\n\n{extra}" if extra else "")
    )


def duel_status_short(duel: Duel, for_uid: int) -> str:
    return duel_status_text(duel, for_uid)


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
    if uid <= 0:
        return
    ex("INSERT INTO notifications (user_id, text, ts) VALUES (?,?,?)", (uid, text, time.time()))


def add_win(uid):
    ex("UPDATE players SET wins=wins+1 WHERE user_id=?", (uid,))


def add_loss(uid):
    ex("UPDATE players SET losses=losses+1, "
       "wins=CASE WHEN wins>0 THEN wins-1 ELSE 0 END WHERE user_id=?", (uid,))


def fighter_from_row(p) -> Fighter:
    arm = ARMORS[p["armor"]]
    max_hp = BASE_STATS["hp"] + arm["hp"]
    return Fighter(
        name=esc(p["name"]),
        max_hp=max_hp,
        hp=max_hp,
        weapon=p["weapon"],
        armor=p["armor"],
    )


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


def ensure_masked_bots(count: int = 24):
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
        losses = random.randint(max(0, wins // 2), wins * 2 + 3)
        # экипировка по «уровню» арены
        key = arena_of(wins)
        if key == "bronze":
            weapon = random.choice(["fists", "dagger", "sword"])
            armor = random.choice(["none", "light"])
        elif key == "silver":
            weapon = random.choice(["sword", "axe", "bow"])
            armor = random.choice(["light", "medium"])
        else:
            weapon = random.choice(["bow", "staff", "hammer"])
            armor = random.choice(["medium", "heavy", "legend"])
        ex(
            "INSERT INTO players (user_id, username, name, chips, wins, losses, "
            "weapon, armor, weapons_owned, armors_owned, is_bot, created) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (uid, None, name, random.randint(0, 400), wins, losses,
             weapon, armor, weapon, armor, 1, time.time()),
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
    w = WEAPONS[p["weapon"]]
    a = ARMORS[p["armor"]]
    f = fighter_from_row(p)
    lines = [
        f"🎒 <b>{esc(p['name'])}</b>",
        f"🏆 Победы: <b>{p['wins']}</b>  ·  💀 Поражения: {p['losses']}",
        f"💰 Фишки: <b>{p['chips']}</b>",
        f"📍 Арена: {ARENAS[arena_of(p['wins'])]['emoji']} {ARENAS[arena_of(p['wins'])]['name']}",
        "",
        fighter_card(f),
        "",
        f"{w['emoji']} Оружие: <b>{w['name']}</b> — {w['spec']}",
        f"    {w['desc']}  ·  базовый урон {w['dmg']}",
        f"{a['emoji']} Броня: <b>{a['name']}</b> — {a['desc']}",
    ]
    kb = ikb(
        [("⚔️ Оружие", "gear:w", "primary"), ("🛡 Броня", "gear:a", "primary")],
    )
    return "\n".join(lines), kb


def gear_list_screen(uid, page="w"):
    p = get_player(uid)
    is_w = page == "w"
    table = WEAPONS if is_w else ARMORS
    owned = set(p["weapons_owned" if is_w else "armors_owned"].split(","))
    equipped = p["weapon" if is_w else "armor"]

    title = "Оружие" if is_w else "Броня"
    lines = [f"🏪 <b>{title}</b>", f"💰 Фишки: <b>{p['chips']}</b>", ""]
    rows = [[("⚔️ Оружие" + (" •" if is_w else ""), "gear:w", "primary"),
             ("🛡 Броня" + ("" if is_w else " •"), "gear:a", "primary")]]
    for key, it in table.items():
        if is_w:
            lines.append(f"{it['emoji']} <b>{it['name']}</b> — {it['spec']}\n"
                         f"    урон {it['dmg']} · шанс {it['chance']}% · {it['desc']}")
        else:
            ad = it["armor_def"]
            lines.append(f"{it['emoji']} <b>{it['name']}</b> — {it['desc']}\n"
                         f"    ❤️+{it['hp']} · 🛡 🧠{ad['head']} 🫀{ad['torso']} 💪{ad['arms']} 🦵{ad['legs']}")
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
    lines += ["", "🏆 Победа: +1. 💀 Поражение: −1."]
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
        f"<b>Правила боя:</b>\n"
        f"• Атакующий выбирает зону удара\n"
        f"• Защищающийся выбирает зону защиты\n"
        f"• Совпало → урон не проходит\n"
        f"• Не совпало → урон = оружие − броня\n"
        f"• На следующем раунде роли меняются"
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
    ensure_masked_bots(30)
    rows = qa("SELECT user_id FROM players WHERE is_bot=1 ORDER BY RANDOM() LIMIT 1")
    return rows[0]["user_id"] if rows else None


# ════════════════════════════════════════════════════════════════════
#  БОТ-ЛОГИКА (выбор зон)
# ════════════════════════════════════════════════════════════════════

def bot_pick_attack_zone(opponent: Fighter) -> str:
    # бот бьёт туда, где у соперника слабее броня
    scored = sorted(ZONES, key=lambda z: opponent.armor_of(z))
    if random.random() < 0.5:
        return scored[0]
    return random.choice(ZONES)


def bot_pick_defend_zone(attacker: Fighter) -> str:
    # бот защищает самую «сильную» зону оружия атакующего
    scored = sorted(ZONES, key=lambda z: attacker.weapon_of_zone(z), reverse=True)
    if random.random() < 0.5:
        return scored[0]
    return random.choice(ZONES)


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
    "<b>Как идёт бой:</b>\n"
    "1. Один игрок выбирает, <b>куда бить</b>.\n"
    "2. Второй выбирает, <b>что защищать</b>.\n"
    "3. Совпало — урон не проходит. Не совпало — урон = оружие − броня зоны.\n"
    "4. На следующем раунде роли меняются.\n\n"
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
    ensure_masked_bots(24)
    p = get_player(m.from_user.id)
    if p:
        touch_username(m)
        await m.answer(f"С возвращением, <b>{esc(p['name'])}</b>! Арена ждёт 👇", reply_markup=MENU_KB)
        await flush_notifications(m)
        return
    await state.set_state(Reg.name)
    await m.answer(
        "⚔️ <b>Добро пожаловать на Арену Дуэлянтов!</b>\n\n"
        "Только PvP, без прокачки — только победы и снаряжение.\n\n"
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
    ensure_masked_bots(24)
    await state.clear()
    await m.answer(
        f"Боец <b>{esc(name)}</b> создан! 🎉\n\n"
        f"Стартовое снаряжение: 👊 Кулаки и 👕 без брони.\n"
        f"Открой «⚔️ Арена» и найди соперника.",
        reply_markup=MENU_KB,
    )


# ── Поиск по нику/ID ──────────────────────────────────────────────

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
        return await begin_duel_msg(m.from_user.id, target, m)
    await begin_duel_msg(m.from_user.id, row["user_id"], m)


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


# ── Начало боя ─────────────────────────────────────────────────────

async def begin_duel_msg(aid: int, bid: int, m: Message):
    if bid == aid:
        return await m.answer("🤨 Нельзя драться с самим собой.")
    if aid in DUELS:
        return await m.answer("У тебя уже идёт бой.")
    duel = start_duel(aid, bid)
    # кому первому атаковать — тому и приходит приглашение
    text = duel_status_text(duel, aid)
    role = duel.state_for(aid)
    if role == "attacker":
        kb = attack_zone_kb()
    else:
        kb = ikb([("▶️ Готов защищаться", "duel:ready_def", "primary")])
    await m.answer(text, reply_markup=kb)
    # уведомим реального соперника, если он существует
    if bid > 0:
        notify(bid, f"⚔️ <b>{esc(get_player(aid)['name'])}</b> вызвал тебя на арену. "
                    f"Зайди в «⚔️ Арена», чтобы принять бой.")


# ── Callback: старт боя ───────────────────────────────────────────

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
    text = duel_status_text(duel, cb.from_user.id)
    role = duel.state_for(cb.from_user.id)
    kb = attack_zone_kb() if role == "attacker" else ikb([("▶️ Готов защищаться", "duel:ready_def", "primary")])
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
    text = duel_status_text(duel, cb.from_user.id)
    role = duel.state_for(cb.from_user.id)
    kb = attack_zone_kb() if role == "attacker" else ikb([("▶️ Готов защищаться", "duel:ready_def", "primary")])
    await safe_edit(cb, text, kb)
    await cb.answer()


# ── ДУЭЛЬ: АТАКА ───────────────────────────────────────────────────

@router.callback_query(F.data.regexp(r"^duel:atk:(head|torso|arms|legs)$"))
async def cb_duel_attack(cb: CallbackQuery):
    duel = DUELS.get(cb.from_user.id)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    if duel.state_for(cb.from_user.id) != "attacker":
        return await cb.answer("Сейчас не твой ход атаковать.", show_alert=True)
    atk_zone = cb.data.split(":")[2]
    duel.atk_zone = atk_zone

    if cb.from_user.id == duel.a_id:
        # атакует A → ход защиты переходит к B (если он человек), иначе бот сам защищается
        if duel.b_id > 0:
            # человек-B — ждём его выбора
            text_b = duel_status_text(duel, duel.b_id,
                                      extra=f"⚔️ {duel.a.name} выбрал зону удара и ждёт твою защиту!")
            kb_b = defend_zone_kb()
            try:
                await cb.bot.send_message(duel.b_id, text_b, reply_markup=kb_b)
            except Exception:
                pass
            # игрок A видит «ожидание»
            text_a = duel_status_text(duel, duel.a_id, extra="⏳ Ждём защиту соперника…")
            kb_a = ikb([("🔄 Обновить", "duel:refresh", "primary")])
            await safe_edit(cb, text_a, kb_a)
            return await cb.answer("Удар выбран. Ждём защиту.")
        else:
            # соперник — бот, он сам выбирает защиту
            def_zone = bot_pick_defend_zone(duel.a)
            return await _resolve_and_advance(cb, duel, atk_zone, def_zone)
    else:
        # атакует B → ход защиты к A (человек)
        text_a = duel_status_text(duel, duel.a_id,
                                  extra=f"⚔️ {duel.b.name} выбрал зону удара и ждёт твою защиту!")
        kb_a = defend_zone_kb()
        await safe_edit(cb, text_a, kb_a)
        return await cb.answer("Удар выбран. Теперь защищается соперник.")


# ── ДУЭЛЬ: ЗАЩИТА ──────────────────────────────────────────────────

@router.callback_query(F.data.regexp(r"^duel:def:(head|torso|arms|legs)$"))
async def cb_duel_defend(cb: CallbackQuery):
    duel = DUELS.get(cb.from_user.id)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    if duel.state_for(cb.from_user.id) != "defender":
        return await cb.answer("Сейчас ты не защищаешься.", show_alert=True)
    if duel.atk_zone is None:
        return await cb.answer("Атакующий ещё не выбрал зону.", show_alert=True)
    def_zone = cb.data.split(":")[2]
    return await _resolve_and_advance(cb, duel, duel.atk_zone, def_zone)


@router.callback_query(F.data == "duel:ready_def")
async def cb_duel_ready_def(cb: CallbackQuery):
    """Игрок-защитник открывает экран с выбором зоны защиты (если атака уже выбрана)."""
    duel = DUELS.get(cb.from_user.id)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    if duel.state_for(cb.from_user.id) != "defender":
        return await cb.answer("Сейчас не твоя защита.", show_alert=True)
    if duel.atk_zone is None:
        return await cb.answer("Атакующий ещё выбирает зону.", show_alert=True)
    text = duel_status_text(duel, cb.from_user.id, extra="🛡 Выбери зону защиты.")
    await safe_edit(cb, text, defend_zone_kb())
    await cb.answer()


@router.callback_query(F.data == "duel:refresh")
async def cb_duel_refresh(cb: CallbackQuery):
    duel = DUELS.get(cb.from_user.id)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    role = duel.state_for(cb.from_user.id)
    if role == "attacker":
        if duel.atk_zone is None:
            text = duel_status_text(duel, cb.from_user.id, extra="🎯 Выбери зону удара.")
            await safe_edit(cb, text, attack_zone_kb())
        else:
            text = duel_status_text(duel, cb.from_user.id, extra="⏳ Ждём защиту соперника…")
            await safe_edit(cb, text, ikb([("🔄 Обновить", "duel:refresh", "primary")]))
    else:
        if duel.atk_zone is None:
            text = duel_status_text(duel, cb.from_user.id, extra="⏳ Соперник ещё выбирает удар…")
            await safe_edit(cb, text, ikb([("🔄 Обновить", "duel:refresh", "primary")]))
        else:
            text = duel_status_text(duel, cb.from_user.id, extra="🛡 Выбери зону защиты.")
            await safe_edit(cb, text, defend_zone_kb())
    await cb.answer("Обновлено")


# ── РАЗРЕШЕНИЕ РАУНДА И ПЕРЕДАЧА ХОДА ─────────────────────────────

async def _resolve_and_advance(cb: CallbackQuery, duel: Duel, atk_zone: str, def_zone: str):
    """
    Считает раунд: атака vs защита, добавляет лог, проверяет смерть,
    затем меняет роли атакующий↔защитник и переходит к следующему раунду.
    """
    attacker = duel.a if duel.attacker_is_a else duel.b
    defender = duel.b if duel.attacker_is_a else duel.a

    duel.log.append(f"<b>── Раунд {duel.round_no} ──</b>")
    duel.log.append(
        f"⚔️ {attacker.name} бьёт в {ZONE_INFO[atk_zone]['emoji']} {ZONE_INFO[atk_zone]['name']}  ·  "
        f"🛡 {defender.name} защищает {ZONE_INFO[def_zone]['emoji']} {ZONE_INFO[def_zone]['name']}"
    )

    # DOT-эффекты на атакующем — тикают в начале его хода
    tick_dots(attacker, duel.log)
    if not attacker.alive():
        return await _finish(cb, duel, winner_is_a=(attacker is duel.b))

    resolve_attack(attacker, defender, atk_zone, def_zone, duel.log)

    if not defender.alive():
        return await _finish(cb, duel, winner_is_a=(defender is duel.b) is False)

    # готовим следующий раунд: меняем роли
    duel.atk_zone = None
    duel.attacker_is_a = not duel.attacker_is_a
    duel.round_no += 1

    # Проверка лимита раундов
    if duel.round_no > MAX_ROUNDS:
        # победитель — у кого больше HP
        winner_is_a = duel.a.hp >= duel.b.hp
        return await _finish(cb, duel, winner_is_a=winner_is_a)

    # теперь надо показать состояние текущему игроку
    await _show_turn_to_current(cb, duel)


async def _show_turn_to_current(cb: CallbackQuery, duel: Duel):
    """
    После раунда роли поменялись. Показываем cb.from_user.id его текущую роль.
    Если роль 'attacker' — даём выбор удара. Если 'defender' — говорим ждать
    выбор атакующего (или даём готовиться).
    """
    uid = cb.from_user.id
    role = duel.state_for(uid)

    if role == "attacker":
        text = duel_status_text(duel, uid, extra="🎯 Твой ход — выбери зону удара.")
        await safe_edit(cb, text, attack_zone_kb())
    elif role == "defender":
        # Если соперник — бот, то бот уже "выбрал" атаку, и надо дать
        # защитнику сразу выбрать защиту (через кнопку).
        other_uid = duel.b_id if uid == duel.a_id else duel.a_id
        if other_uid < 0:
            # соперник — бот: он сделает свой ход автоматически, когда защитник нажмёт защиту
            duel.atk_zone = bot_pick_attack_zone(duel.opponent(uid))
            text = duel_status_text(duel, uid, extra="🛡 Соперник атакует — выбери зону защиты.")
            await safe_edit(cb, text, defend_zone_kb())
        else:
            text = duel_status_text(duel, uid,
                                    extra="⏳ Соперник выбирает зону удара. Нажми «Готов защищаться», "
                                          "когда атака придёт.")
            await safe_edit(cb, text, ikb([("▶️ Готов защищаться", "duel:ready_def", "primary")]))
    else:
        text = duel_status_text(duel, uid)
        await safe_edit(cb, text, ikb([("🔄 Обновить", "duel:refresh", "primary")]))


async def _finish(cb: CallbackQuery, duel: Duel, winner_is_a: bool):
    """
    Завершает бой, обновляет БД и рассылает финальные экраны обоим.
    winner_is_a=True — победа игрока duel.a_id.
    """
    aid, bid = duel.a_id, duel.b_id
    a_row = get_player(aid)
    b_row = get_player(bid) if bid else None

    if winner_is_a:
        add_win(aid)
        if bid:
            add_loss(bid)
            notify(bid, f"💀 <b>{esc(a_row['name'])}</b> одолел тебя на арене. −1 🏆")
        result_for_a = "🏆 <b>Победа!</b> +1 🏆"
        result_for_b = "💀 <b>Поражение.</b> −1 🏆"
    else:
        if bid:
            add_win(bid)
        add_loss(aid)
        if bid:
            notify(bid, f"🏆 <b>{esc(a_row['name'])}</b> проиграл тебе на арене. +1 🏆")
        result_for_a = "💀 <b>Поражение.</b> −1 🏆"
        result_for_b = "🏆 <b>Победа!</b> +1 🏆"

    end_duel(duel)

    new_a = get_player(aid)
    a_arena = ARENAS[arena_of(new_a["wins"])]

    # финальный экран для A
    footer_a = (
        f"{result_for_a}\n"
        f"🏆 {new_a['wins']}  ·  💀 {new_a['losses']}\n"
        f"📍 {a_arena['emoji']} {a_arena['name']}"
    )
    text_a = duel_status_text(duel, aid, extra=footer_a)
    kb_a = ikb([("⚔️ На арену", "arena:menu", "success")],
               [("🎲 Ещё бой", "arena:find", "danger")])

    # если финал пришёл тому, чей это cb — редактируем его сообщение
    if cb.from_user.id == aid:
        await safe_edit(cb, text_a, kb_a)
    else:
        await safe_edit(cb, text_a, kb_a)

    # отправим финальный экран второму игроку, если это человек
    if bid and bid > 0:
        new_b = get_player(bid)
        b_arena = ARENAS[arena_of(new_b["wins"])]
        footer_b = (
            f"{result_for_b}\n"
            f"🏆 {new_b['wins']}  ·  💀 {new_b['losses']}\n"
            f"📍 {b_arena['emoji']} {b_arena['name']}"
        )
        text_b = duel_status_text(duel, bid, extra=footer_b)
        kb_b = ikb([("⚔️ На арену", "arena:menu", "success")],
                   [("🎲 Ещё бой", "arena:find", "danger")])
        try:
            await cb.bot.send_message(bid, text_b, reply_markup=kb_b)
        except Exception:
            pass


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
        "/endduel &lt;user_id&gt; — сбросить бой"
    )


@router.message(Command("stats"))
async def cmd_stats(m: Message):
    if not admin_only(m.from_user.id):
        return
    total = q1("SELECT COUNT(*) c FROM players WHERE is_bot=0")["c"]
    bots = q1("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    banned = q1("SELECT COUNT(*) c FROM players WHERE banned=1")["c"]
    await m.answer(f"📊 Игроков: {total}\n🤖 Скрытых: {bots}\n🚫 Бан: {banned}\n⚔️ Активных боёв: {len({id(d) for d in DUELS.values()})}")


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
        duel = DUELS[uid]
        end_duel(duel)
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
    ensure_masked_bots(24)
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать / вернуться"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="help", description="Правила боя"),
    ])
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())