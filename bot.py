#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚔️ Арена Дуэлянтов — PvP + Казино + РП + Боссы (исправленная версия)
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

START_CHIPS = 400
MAX_ROUNDS = 80
TURN_TIMEOUT = 45
RP_COOLDOWN = 5

# ── PREMIUM EMOJI ID ───────────────────────────────────────────────
PE = {
    "fire":   "5368324170671202286",
    "sword":  "5368324170671202286",
    "coin":   "5368324170671202286",
    "chips":  "5368324170671202286",
    "trophy": "5368324170671202286",
    "skull":  "5368324170671202286",
    "shield": "5368324170671202286",
    "heart":  "5368324170671202286",
    "slot":   "5368324170671202286",
    "dice":   "5368324170671202286",
    "boss":   "5368324170671202286",
    "glove":  "5368324170671202286",
}


def pe(key: str, fallback: str) -> str:
    eid = PE.get(key)
    if not eid:
        return fallback
    return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'


E_FIRE   = pe("fire", "🔥")
E_SWORD  = pe("sword", "⚔️")
E_COIN   = pe("coin", "🪙")
E_CHIPS  = pe("chips", "💰")
E_TROPHY = pe("trophy", "🏆")
E_SKULL  = pe("skull", "💀")
E_SHIELD = pe("shield", "🛡")
E_HEART  = pe("heart", "❤️")
E_SLOT   = pe("slot", "🎰")
E_DICE   = pe("dice", "🎲")
E_BOSS   = pe("boss", "👹")
E_GLOVE  = pe("glove", "🧤")

# ── Зоны тела ───────────────────────────────────────────────────────
ZONES = ["head", "torso", "arms", "legs"]
ZONE_INFO = {
    "head":  dict(name="Голова", emoji="🧠", mult=1.5),
    "torso": dict(name="Торс",   emoji="🫀", mult=1.0),
    "arms":  dict(name="Руки",   emoji="💪", mult=0.8),
    "legs":  dict(name="Ноги",   emoji="🦵", mult=0.9),
}

# ── Оружие ──────────────────────────────────────────────────────────
WEAPONS = {
    "fists":  dict(emoji="👊", name="Кулаки",  dmg=10, spec="Серия ударов",
                   desc="3 быстрых удара по 50% урона", price=0, chance=25),
    "dagger": dict(emoji="🗡", name="Кинжал",  dmg=14, spec="Тысяча порезов",
                   desc="3 удара по 50% урона", price=200, chance=30),
    "sword":  dict(emoji="⚔️", name="Меч",     dmg=20, spec="Казнь",
                   desc="двойной урон по зоне", price=450, chance=28),
    "axe":    dict(emoji="🪓", name="Топор",   dmg=26, spec="Кровопускание",
                   desc="+5 урона в следующие 3 раунда", price=700, chance=24),
    "bow":    dict(emoji="🏹", name="Лук",     dmg=32, spec="Снайперский выстрел",
                   desc="игнорирует защиту брони", price=1000, chance=22),
    "staff":  dict(emoji="🔥", name="Посох",   dmg=38, spec="Огненный шторм",
                   desc="+6 урона в следующие 3 раунда", price=1400, chance=22),
    "hammer": dict(emoji="🔨", name="Молот",   dmg=46, spec="Землетрясение",
                   desc="×2 урона и оглушение", price=2000, chance=18),
}

# ── Броня: 4 слота ──────────────────────────────────────────────────
ARMOR_LEVELS = ["none", "light", "medium", "heavy", "legend"]

ARMOR_TEMPLATE = {
    "none":   dict(name="Без",         emoji="👕", df=0,  price=0,    chance=0,  dmg_bonus=0,  desc="—"),
    "light":  dict(name="Лёгкая",      emoji="🥋", df=2,  price=100,  chance=5,  dmg_bonus=0,  desc="+5% шанс спец-атаки"),
    "medium": dict(name="Средняя",     emoji="🛡", df=5,  price=280,  chance=0,  dmg_bonus=0,  desc="ровная защита"),
    "heavy":  dict(name="Тяжёлая",     emoji="🏋️", df=9,  price=550,  chance=0,  dmg_bonus=15, desc="+15% урон спец-атаки"),
    "legend": dict(name="Легендарная", emoji="✨", df=14, price=1100, chance=10, dmg_bonus=25, desc="+10% шанс, +25% урон спец-атаки"),
}

ARMOR_ZONE_MULT = {
    "head":  0.8,
    "torso": 1.3,
    "arms":  0.9,
    "legs":  1.0,
}


def armor_item_key(slot: str, level: str) -> str:
    return f"{slot}_{level}"


def armor_item_info(slot: str, level: str) -> dict:
    base = ARMOR_TEMPLATE[level]
    zmult = ARMOR_ZONE_MULT[slot]
    df = round(base["df"] * zmult)
    price = round(base["price"] * zmult)
    return dict(
        slot=slot,
        level=level,
        name=f"{base['name']} ({ZONE_INFO[slot]['name'].lower()})",
        emoji=base["emoji"],
        df=df,
        price=price,
        chance=base["chance"],
        dmg_bonus=base["dmg_bonus"],
        desc=base["desc"],
    )


def build_all_armor_items() -> dict:
    items = {}
    for slot in ZONES:
        for level in ARMOR_LEVELS:
            key = armor_item_key(slot, level)
            items[key] = armor_item_info(slot, level)
    return items


ARMOR_ITEMS = build_all_armor_items()
START_ARMOR = ",".join(armor_item_key(s, "none") for s in ZONES)

BASE_STATS = dict(hp=150)

# ── Арены ───────────────────────────────────────────────────────────
ARENAS = {
    "bronze": dict(name="Бронзовая арена", emoji="🥉", min_wins=0,  max_wins=9,   prize=30),
    "silver": dict(name="Серебряная арена", emoji="🥈", min_wins=10, max_wins=29,  prize=60),
    "gold":   dict(name="Золотая арена",   emoji="🥇", min_wins=30, max_wins=10**9, prize=120),
}
ARENA_ORDER = ["bronze", "silver", "gold"]


def arena_of(wins: int) -> str:
    for k in ARENA_ORDER:
        a = ARENAS[k]
        if a["min_wins"] <= wins <= a["max_wins"]:
            return k
    return "gold"


# ── БОССЫ ───────────────────────────────────────────────────────────
BOSSES = {
    "goblin": dict(
        key="goblin",
        name="👺 Гоблин-Вождь",
        desc="Хитрый и злой. Бьёт по слабой броне.",
        hp=160, weapon="sword",
        armor_slot_levels={"head": "light", "torso": "light", "arms": "none", "legs": "none"},
        reward_mult=3, min_wins=0,
    ),
    "dragon": dict(
        key="dragon",
        name="🐉 Древний Дракон",
        desc="Огнедышащий. Оружие — посох.",
        hp=260, weapon="staff",
        armor_slot_levels={"head": "medium", "torso": "heavy", "arms": "medium", "legs": "medium"},
        reward_mult=5, min_wins=5,
    ),
    "lord": dict(
        key="lord",
        name="👹 Древний Лорд",
        desc="Владыка арены. Молот и легендарная броня.",
        hp=380, weapon="hammer",
        armor_slot_levels={"head": "legend", "torso": "legend", "arms": "legend", "legs": "legend"},
        reward_mult=10, min_wins=15,
    ),
}

# ── Ники для скрытых ботов ──────────────────────────────────────────
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
BTN_CASINO = "🎰 Казино"
BTN_GEAR = "🎒 Снаряжение"
BTN_TOP = "🏆 Топ"
BTN_RP = "🎭 РП"
MENU_TEXTS = {BTN_ARENA, BTN_CASINO, BTN_GEAR, BTN_TOP, BTN_RP}

MENU_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_ARENA)],
        [KeyboardButton(text=BTN_CASINO), KeyboardButton(text=BTN_RP)],
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
    armor_slots: dict = field(default_factory=dict)
    dots: list = field(default_factory=list)
    stun: bool = False

    def __post_init__(self):
        w = WEAPONS.get(self.weapon) or WEAPONS["fists"]
        self.weapon = self.weapon if self.weapon in WEAPONS else "fists"
        self.weapon_dmg = w["dmg"]

        slots = self.armor_slots or {}
        fixed = {}
        for s in ZONES:
            key = slots.get(s) or armor_item_key(s, "none")
            if key not in ARMOR_ITEMS:
                key = armor_item_key(s, "none")
            fixed[s] = key
        self.armor_slots = fixed

        self.armor_def = {}
        total_chance = 0
        total_bonus = 0
        for slot in ZONES:
            key = self.armor_slots[slot]
            item = ARMOR_ITEMS[key]
            self.armor_def[slot] = item["df"]
            total_chance += item["chance"]
            total_bonus += item["dmg_bonus"]

        # Суммарный шанс (максимум 70), бонус — средний
        self.spec_chance = min(w["chance"] + total_chance, 70)
        self.spec_dmg_bonus = total_bonus / 100.0

    def alive(self) -> bool:
        return self.hp > 0

    def armor_of(self, zone: str) -> int:
        return self.armor_def.get(zone, 0)

    def weapon_of_zone(self, zone: str) -> int:
        return max(1, round(self.weapon_dmg * ZONE_INFO[zone]["mult"]))


def hp_bar(f: Fighter, width: int = 12) -> str:
    if f.max_hp <= 0:
        return "⬛" * width
    filled = int(round(width * f.hp / f.max_hp))
    filled = max(0, min(width, filled))
    ratio = f.hp / f.max_hp
    if ratio > 0.6:
        return "🟩" * filled + "⬛" * (width - filled)
    elif ratio > 0.3:
        return "🟨" * filled + "⬛" * (width - filled)
    else:
        return "🟥" * filled + "⬛" * (width - filled)


def fighter_card(f: Fighter) -> str:
    w = WEAPONS[f.weapon]
    ad = f.armor_def
    return (
        f"│ <b>{f.name}</b>\n"
        f"│ {E_HEART} <b>{f.hp}</b>/{f.max_hp}  {hp_bar(f)}\n"
        f"│ {w['emoji']} {w['name']} · урон {f.weapon_dmg}\n"
        f"│ {E_SHIELD} 🧠{ad['head']} 🫀{ad['torso']} 💪{ad['arms']} 🦵{ad['legs']}"
    )


# ════════════════════════════════════════════════════════════════════
#  УРОН
# ════════════════════════════════════════════════════════════════════

def compute_damage(att: Fighter, dfn: Fighter, atk_zone: str, def_zone: Optional[str],
                   ignore_armor: bool = False, extra_mult: float = 1.0) -> tuple[int, str]:
    if def_zone == atk_zone:
        return 0, f"{E_SHIELD} <b>Блок!</b>"
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
    w = WEAPONS[att.weapon]
    spec_name = w["spec"]

    if def_zone == atk_zone:
        log.append(f"{E_SHIELD} {dfn.name} заблокировал <b>{spec_name}</b>")
        return True

    if att.weapon in ("fists", "dagger"):
        hits = []
        total = 0
        for _ in range(3):
            d, _ = compute_damage(att, dfn, atk_zone, def_zone)
            d = max(1, round(d * 0.5))
            hits.append(d)
            total += d
        dfn.hp = max(0, dfn.hp - total)
        log.append(f"{w['emoji']} <b>{spec_name}</b>: {' + '.join(map(str, hits))} = <b>−{total}</b>")
        return True

    if att.weapon == "sword":
        d, _ = compute_damage(att, dfn, atk_zone, def_zone, extra_mult=2.0)
        dfn.hp = max(0, dfn.hp - d)
        log.append(f"{E_SWORD} <b>{spec_name}</b>: {att.name} → {dfn.name} "
                   f"[{ZONE_INFO[atk_zone]['emoji']} {ZONE_INFO[atk_zone]['name']}] <b>−{d}</b>")
        return True

    if att.weapon == "axe":
        d, _ = compute_damage(att, dfn, atk_zone, def_zone)
        dfn.hp = max(0, dfn.hp - d)
        bleed = max(1, round(dfn.max_hp * 0.04))
        _add_dot(dfn, "🩸 Кровотечение", bleed, 3)
        log.append(f"🪓 <b>{spec_name}</b>: {att.name} → {dfn.name} <b>−{d}</b>, "
                   f"кровь по <b>{bleed}</b> ×3")
        return True

    if att.weapon == "bow":
        d, _ = compute_damage(att, dfn, atk_zone, def_zone, ignore_armor=True, extra_mult=1.5)
        dfn.hp = max(0, dfn.hp - d)
        log.append(f"🏹 <b>{spec_name}</b>: {att.name} → {dfn.name} сквозь броню <b>−{d}</b>")
        return True

    if att.weapon == "staff":
        d, _ = compute_damage(att, dfn, atk_zone, def_zone)
        dfn.hp = max(0, dfn.hp - d)
        burn = max(1, round(d * 0.4))
        _add_dot(dfn, f"{E_FIRE} Горение", burn, 3)
        log.append(f"{E_FIRE} <b>{spec_name}</b>: {att.name} → {dfn.name} <b>−{d}</b>, "
                   f"огонь по <b>{burn}</b> ×3")
        return True

    if att.weapon == "hammer":
        d, _ = compute_damage(att, dfn, atk_zone, def_zone, extra_mult=2.0)
        dfn.hp = max(0, dfn.hp - d)
        dfn.stun = True
        log.append(f"🔨 <b>{spec_name}</b>: {att.name} → {dfn.name} <b>−{d}</b>, оглушён")
        return True

    return False


def resolve_attack(att: Fighter, dfn: Fighter, atk_zone: str, def_zone: Optional[str],
                   log: list) -> None:
    if att.stun:
        att.stun = False
        log.append(f"💫 {att.name} оглушён — пропуск хода")
        return

    if random.random() * 100 < att.spec_chance:
        if apply_special(att, dfn, atk_zone, def_zone, log):
            return

    dmg, note = compute_damage(att, dfn, atk_zone, def_zone)
    if note:
        log.append(f"{ZONE_INFO[atk_zone]['emoji']} {att.name} бьёт в «{ZONE_INFO[atk_zone]['name']}» — {note}")
        return

    dfn.hp = max(0, dfn.hp - dmg)
    log.append(
        f"👊 {att.name} → {dfn.name} "
        f"[{ZONE_INFO[atk_zone]['emoji']} {ZONE_INFO[atk_zone]['name']}] <b>−{dmg}</b>"
    )


# ════════════════════════════════════════════════════════════════════
#  ДУЭЛЬ
# ════════════════════════════════════════════════════════════════════

@dataclass
class Duel:
    a_id: int
    b_id: int
    a: Fighter
    b: Fighter
    attacker_is_a: bool = True
    round_no: int = 1
    atk_zone: Optional[str] = None
    log: list = field(default_factory=list)
    started: float = field(default_factory=time.time)
    is_boss: bool = False
    boss_key: Optional[str] = None
    reward_mult: int = 1

    bot_last_block_round: int = -10
    bot_block_streak: int = 0

    timer_task: Optional[asyncio.Task] = None
    timer_deadline: float = 0.0
    timer_for: Optional[int] = None
    timer_role: Optional[str] = None

    def state_for(self, uid: int) -> str:
        if uid == self.a_id:
            return "attacker" if self.attacker_is_a else "defender"
        if uid == self.b_id:
            return "defender" if self.attacker_is_a else "attacker"
        return "none"

    def attacker(self) -> Fighter:
        return self.a if self.attacker_is_a else self.b

    def defender(self) -> Fighter:
        return self.b if self.attacker_is_a else self.a

    def attacker_id(self) -> int:
        return self.a_id if self.attacker_is_a else self.b_id

    def defender_id(self) -> int:
        return self.b_id if self.attacker_is_a else self.a_id

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


DUELS: dict[int, Duel] = {}


def stop_timer(duel: Duel):
    if duel.timer_task and not duel.timer_task.done():
        duel.timer_task.cancel()
    duel.timer_task = None
    duel.timer_deadline = 0.0
    duel.timer_for = None
    duel.timer_role = None


def end_duel(duel: Duel):
    stop_timer(duel)
    DUELS.pop(duel.a_id, None)
    if duel.b_id > 0:
        DUELS.pop(duel.b_id, None)


def start_timer(duel: Duel, uid: int, role: str, bot: Bot):
    if uid < 0:
        return
    stop_timer(duel)
    duel.timer_for = uid
    duel.timer_role = role
    duel.timer_deadline = time.time() + TURN_TIMEOUT
    duel.timer_task = asyncio.create_task(_timer_runner(duel, uid, role, bot))


async def _timer_runner(duel: Duel, uid: int, role: str, bot: Bot):
    try:
        while True:
            left = int(round(duel.timer_deadline - time.time()))
            if left <= 0:
                break
            await asyncio.sleep(1)
        if duel.timer_for != uid:
            return
        if duel.state_for(uid) != role:
            return
        if duel not in DUELS.values():
            return
        await _auto_lose(duel, uid, bot)
    except asyncio.CancelledError:
        return
    except Exception as e:
        logging.warning(f"timer error: {e}")


async def _auto_lose(duel: Duel, loser_uid: int, bot: Bot):
    loser = duel.me(loser_uid)
    duel.log.append(f"⏱ <b>{loser.name if loser else '?'} не успел за {TURN_TIMEOUT} сек — авто-поражение!</b>")
    winner_is_a = not (loser_uid == duel.a_id)
    await _finish_duel(duel, winner_is_a=winner_is_a, bot=bot, reason="timeout")


# ════════════════════════════════════════════════════════════════════
#  БАЗА
# ════════════════════════════════════════════════════════════════════

_db = sqlite3.connect(DB_PATH, check_same_thread=False)
_db.row_factory = sqlite3.Row
_db_lock = asyncio.Lock()


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
            armor_head TEXT NOT NULL DEFAULT 'head_none',
            armor_torso TEXT NOT NULL DEFAULT 'torso_none',
            armor_arms TEXT NOT NULL DEFAULT 'arms_none',
            armor_legs TEXT NOT NULL DEFAULT 'legs_none',
            weapons_owned TEXT NOT NULL DEFAULT 'fists',
            armors_owned TEXT NOT NULL DEFAULT 'head_none,torso_none,arms_none,legs_none',
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
    try:
        return _db.execute(sql, args).fetchone()
    except Exception as e:
        logging.warning(f"q1 error: {e}")
        return None


def qa(sql, args=()):
    try:
        return _db.execute(sql, args).fetchall()
    except Exception as e:
        logging.warning(f"qa error: {e}")
        return []


def ex(sql, args=()):
    try:
        cur = _db.execute(sql, args)
        _db.commit()
        return cur
    except Exception as e:
        logging.warning(f"ex error: {e}")
        return None


def get_player(uid):
    return q1("SELECT * FROM players WHERE user_id=?", (uid,))


def create_player(uid, username, name):
    ex(
        "INSERT OR IGNORE INTO players (user_id, username, name, chips, wins, losses, "
        "weapon, armor_head, armor_torso, armor_arms, armor_legs, "
        "weapons_owned, armors_owned, created) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (uid, username, name, START_CHIPS, 0, 0,
         "fists", "head_none", "torso_none", "arms_none", "legs_none",
         "fists", START_ARMOR, time.time()),
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


def add_chips(uid, amount: int):
    ex("UPDATE players SET chips=chips+? WHERE user_id=?", (amount, uid))


def player_armor_slots(p) -> dict:
    if not p:
        return {s: armor_item_key(s, "none") for s in ZONES}
    return {
        "head":  p["armor_head"]  or "head_none",
        "torso": p["armor_torso"] or "torso_none",
        "arms":  p["armor_arms"]  or "arms_none",
        "legs":  p["armor_legs"]  or "legs_none",
    }


def fighter_from_row(p) -> Fighter:
    slots = player_armor_slots(p)
    total_hp = BASE_STATS["hp"]
    for key in slots.values():
        lvl = key.split("_", 1)[1] if "_" in key else "none"
        if lvl == "light":    total_hp += 5
        elif lvl == "medium": total_hp += 12
        elif lvl == "heavy":  total_hp += 20
        elif lvl == "legend": total_hp += 30
    return Fighter(
        name=esc(p["name"]),
        max_hp=total_hp,
        hp=total_hp,
        weapon=p["weapon"] if p["weapon"] in WEAPONS else "fists",
        armor_slots=slots,
    )


def boss_to_fighter(boss: dict) -> Fighter:
    slots = {s: armor_item_key(s, boss["armor_slot_levels"][s]) for s in ZONES}
    return Fighter(
        name=boss["name"],
        max_hp=boss["hp"],
        hp=boss["hp"],
        weapon=boss["weapon"],
        armor_slots=slots,
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
        key = arena_of(wins)
        if key == "bronze":
            weapon = random.choice(["fists", "dagger", "sword"])
            lvl_range = ["none", "light"]
        elif key == "silver":
            weapon = random.choice(["sword", "axe", "bow"])
            lvl_range = ["light", "medium"]
        else:
            weapon = random.choice(["bow", "staff", "hammer"])
            lvl_range = ["medium", "heavy", "legend"]

        slots = {s: armor_item_key(s, random.choice(lvl_range)) for s in ZONES}
        armors_owned = ",".join(set(list(slots.values()) + [armor_item_key(s, "none") for s in ZONES]))

        ex(
            "INSERT INTO players (user_id, username, name, chips, wins, losses, "
            "weapon, armor_head, armor_torso, armor_arms, armor_legs, "
            "weapons_owned, armors_owned, is_bot, created) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (uid, None, name, random.randint(0, 400), wins, losses,
             weapon, slots["head"], slots["torso"], slots["arms"], slots["legs"],
             weapon, armors_owned, 1, time.time()),
        )


# ════════════════════════════════════════════════════════════════════
#  ЭКРАНЫ
# ════════════════════════════════════════════════════════════════════

async def safe_edit(cb: CallbackQuery, text: str, markup=None):
    try:
        await cb.message.edit_text(text[:4090], reply_markup=markup)
    except TelegramBadRequest as e:
        if "not modified" not in str(e):
            try:
                await cb.message.answer(text[:4090], reply_markup=markup)
            except Exception:
                pass


def gear_screen(uid):
    p = get_player(uid)
    if not p:
        return "Профиль не найден.", None
    w = WEAPONS[p["weapon"]]
    f = fighter_from_row(p)
    slots = player_armor_slots(p)
    lines = [
        f"🎒 <b>{esc(p['name'])}</b>",
        "",
        f"{E_TROPHY} Победы: <b>{p['wins']}</b>  ·  {E_SKULL} Поражения: {p['losses']}",
        f"{E_CHIPS} Фишки: <b>{p['chips']}</b>",
        f"📍 {ARENAS[arena_of(p['wins'])]['emoji']} {ARENAS[arena_of(p['wins'])]['name']}",
        "",
        f"❤️ HP: <b>{f.max_hp}</b>   ⚔️ Атака: <b>{f.weapon_dmg}</b>",
        "",
        "<b>⚔️ Оружие:</b>",
        f"  {w['emoji']} {w['name']} — <i>{w['spec']}</i>",
        f"     урон <b>{w['dmg']}</b>, шанс {w['chance']}%",
        "",
        "<b>🛡 Броня по слотам:</b>",
    ]
    for slot in ZONES:
        key = slots[slot]
        item = ARMOR_ITEMS.get(key) or armor_item_info(slot, "none")
        lines.append(
            f"  {ZONE_INFO[slot]['emoji']} {ZONE_INFO[slot]['name']}: "
            f"{item['emoji']} <b>{item['name']}</b>  (защита {item['df']})"
        )
    kb = ikb(
        [("⚔️ Оружие", "gear:w", "primary"), ("🛡 Броня", "gear:armor_menu", "primary")],
        [("👤 Мой профиль", "duel:myprofile", "success")],
    )
    return "\n".join(lines), kb


def armor_slot_menu(uid):
    p = get_player(uid)
    if not p:
        return "Профиль не найден.", None
    slots = player_armor_slots(p)
    lines = ["🛡 <b>Броня — выбери часть тела</b>", f"{E_CHIPS} Фишки: <b>{p['chips']}</b>", ""]
    for slot in ZONES:
        item = ARMOR_ITEMS.get(slots[slot]) or armor_item_info(slot, "none")
        lines.append(
            f"{ZONE_INFO[slot]['emoji']} <b>{ZONE_INFO[slot]['name']}</b> — "
            f"{item['emoji']} {item['name']} (защита {item['df']})"
        )
    kb = ikb(
        [("🧠 Голова", "gear:head", "primary")],
        [("🫀 Торс", "gear:torso", "primary")],
        [("💪 Руки", "gear:arms", "primary")],
        [("🦵 Ноги", "gear:legs", "primary")],
        [("⬅️ Назад", "gear:menu", "success")],
    )
    return "\n".join(lines), kb


def armor_slot_list(uid, slot: str):
    p = get_player(uid)
    if not p or slot not in ZONES:
        return "Ошибка.", None
    slots = player_armor_slots(p)
    equipped = slots.get(slot, armor_item_key(slot, "none"))
    owned = set(p["armors_owned"].split(","))

    lines = [
        f"🛡 <b>Броня на {ZONE_INFO[slot]['name'].lower()}</b>",
        f"{E_CHIPS} Фишки: <b>{p['chips']}</b>", "",
    ]
    rows = []
    for level in ARMOR_LEVELS:
        key = armor_item_key(slot, level)
        item = ARMOR_ITEMS[key]
        lines.append(
            f"{item['emoji']} <b>{item['name']}</b> — защита <b>{item['df']}</b>\n"
            f"    {item['desc']}"
        )
        if key == equipped:
            label, style = "✅ надето", "success"
        elif key in owned:
            label, style = "🎒 надеть", "primary"
        else:
            label, style = f"{item['price']}💰", "danger"
        rows.append([(f"{item['emoji']} {item['name']} · {label}", f"buy_armor:{slot}:{level}", style)])
    rows.append([("⬅️ К слотам", "gear:armor_menu", "success")])
    return "\n".join(lines), ikb(*rows)


def weapon_list(uid):
    p = get_player(uid)
    if not p:
        return "Профиль не найден.", None
    equipped = p["weapon"]
    owned = set(p["weapons_owned"].split(","))
    lines = ["⚔️ <b>Оружие</b>", f"{E_CHIPS} Фишки: <b>{p['chips']}</b>", ""]
    rows = []
    for key, it in WEAPONS.items():
        lines.append(f"{it['emoji']} <b>{it['name']}</b> — <i>{it['spec']}</i>\n"
                     f"    урон {it['dmg']} · шанс {it['chance']}% · {it['desc']}")
        if key == equipped:
            label, style = "✅ надето", "success"
        elif key in owned:
            label, style = "🎒 надеть", "primary"
        else:
            label, style = f"{it['price']}💰", "danger"
        rows.append([(f"{it['emoji']} {it['name']} · {label}", f"buy_weapon:{key}", style)])
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
        lines.append(f"{mark} <b>{esc(r['name'])}</b> — {r['wins']} {E_TROPHY} / {r['losses']} {E_SKULL}{you}")
    me = get_player(uid)
    if me and all(r["user_id"] != uid for r in rows) and a["min_wins"] <= me["wins"] <= a["max_wins"]:
        rank = q1(
            "SELECT COUNT(*) c FROM players WHERE is_bot=0 AND banned=0 AND wins BETWEEN ? AND ? AND wins > ?",
            (a["min_wins"], a["max_wins"], me["wins"]),
        )
        rank = (rank["c"] if rank else 0) + 1
        lines += ["…", f"{rank}. <b>{esc(me['name'])}</b> — {me['wins']} {E_TROPHY} / {me['losses']} {E_SKULL} ← ты"]
    lines += ["", f"{E_TROPHY} Победа: +1 и деньги. {E_SKULL} Поражение: −1."]
    kb = ikb(
        [("🥉 Бронза", "top:bronze", "danger"),
         ("🥈 Серебро", "top:silver", "primary"),
         ("🥇 Золото", "top:gold", "success")],
        [("⬅️ Назад", "arena:menu", "success")],
    )
    return "\n".join(lines), kb


def arena_menu_screen(uid):
    p = get_player(uid)
    if not p:
        return "Профиль не найден.", None
    key = arena_of(p["wins"])
    a = ARENAS[key]
    text = (
        f"╔══════════════════════════╗\n"
        f"      ⚔️ <b>АРЕНА ДУЭЛЯНТОВ</b>\n"
        f"╚══════════════════════════╝\n\n"
        f"{E_TROPHY} Победы: <b>{p['wins']}</b>  ·  {E_SKULL} Поражения: {p['losses']}\n"
        f"{E_CHIPS} Фишки: <b>{p['chips']}</b>\n"
        f"📍 {a['emoji']} <b>{a['name']}</b>\n\n"
        f"🥉 Бронза — 0–9 побед  ·  <b>{ARENAS['bronze']['prize']}💰</b>\n"
        f"🥈 Серебро — 10–29 побед  ·  <b>{ARENAS['silver']['prize']}💰</b>\n"
        f"🥇 Золото — 30+ побед  ·  <b>{ARENAS['gold']['prize']}💰</b>\n\n"
        f"<b>📜 Правила боя:</b>\n"
        f"• Атакующий выбирает зону удара — <b>{TURN_TIMEOUT} сек</b>\n"
        f"• Защищающийся — зону защиты — <b>{TURN_TIMEOUT} сек</b>\n"
        f"• Совпало → блок. Иначе урон = оружие − броня зоны\n"
        f"• Роли меняются каждый раунд\n"
        f"• Побеждает тот, у кого HP &gt; 0"
    )
    kb = ikb(
        [("🎲 Найти соперника", "arena:find", "success")],
        [("👹 Боссы", "arena:bosses", "danger")],
        [("📋 Список соперников", "arena:list", "primary")],
        [("🔎 Вызвать по нику", "arena:find_name", "primary")],
        [("🏆 Топ арен", "top:cur", "primary")],
        [("👤 Мой профиль", "duel:myprofile", "success")],
    )
    return text, kb


def bosses_menu_screen(uid):
    p = get_player(uid)
    if not p:
        return "Профиль не найден.", None
    lines = [
        f"╔══════════════════════════╗\n"
        f"      {E_BOSS} <b>БОССЫ АРЕНЫ</b>\n"
        f"╚══════════════════════════╝\n",
    ]
    rows = []
    for bkey, b in BOSSES.items():
        locked = p["wins"] < b["min_wins"]
        lock = f"🔒 нужен {b['min_wins']} {E_TROPHY}" if locked else f"награда ×{b['reward_mult']}"
        lines.append(
            f"{b['name']}\n"
            f"  ❤️ HP {b['hp']} · ⚔️ {WEAPONS[b['weapon']]['name']}\n"
            f"  {b['desc']}\n"
            f"  → {lock}\n"
        )
        style = "danger" if not locked else "primary"
        label = b["name"] if not locked else f"{b['name']} 🔒"
        rows.append([(label, f"arena:boss:{bkey}", style)])
    rows.append([("⬅️ Назад", "arena:menu", "success")])
    return "\n".join(lines), ikb(*rows)


def arena_list_screen(uid):
    p = get_player(uid)
    if not p:
        return "Профиль не найден.", None
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
    kb_rows = []
    for r in rows:
        kb_rows.append([
            (f"{r['name'][:16]} · {r['wins']}{E_TROPHY}/{r['losses']}{E_SKULL}",
             f"duel:pick:{r['user_id']}", "primary"),
            ("👁", f"duel:profile:{r['user_id']}", "success"),
        ])
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
#  БОТ-ЛОГИКА
# ════════════════════════════════════════════════════════════════════

def bot_pick_attack_zone(attacker: Fighter, defender: Fighter) -> str:
    if random.random() < 0.10:
        return random.choice(ZONES)
    if defender.hp <= defender.max_hp * 0.30:
        return max(ZONES, key=lambda z: attacker.weapon_of_zone(z))

    def score(z: str) -> tuple:
        dmg = attacker.weapon_of_zone(z) - defender.armor_of(z)
        return (dmg, ZONE_INFO[z]["mult"])
    return max(ZONES, key=score)


def bot_wants_to_defend(duel: Duel, bot_is_a: bool) -> bool:
    if duel.bot_block_streak >= 2:
        return False
    if duel.round_no - duel.bot_last_block_round < 3:
        return False
    bot = duel.a if bot_is_a else duel.b
    base = 0.25
    ratio = bot.hp / bot.max_hp
    if ratio < 0.30:
        base = 0.65
    elif ratio < 0.60:
        base = 0.40
    return random.random() < base


def bot_pick_defend_zone(attacker: Fighter, defender: Fighter) -> str:
    def danger(z: str) -> int:
        return attacker.weapon_of_zone(z) - defender.armor_of(z)
    sorted_zones = sorted(ZONES, key=danger, reverse=True)
    if random.random() < 0.25 and len(sorted_zones) > 1:
        return sorted_zones[1]
    return sorted_zones[0]


# ════════════════════════════════════════════════════════════════════
#  КАЗИНО
# ════════════════════════════════════════════════════════════════════

CASINO_BETS = [10, 25, 50, 100, 250, 500, 1000]


def casino_menu(uid):
    p = get_player(uid)
    if not p:
        return "Профиль не найден.", None
    text = (
        f"╔══════════════════════════╗\n"
        f"   {E_SLOT} <b>КАЗИНО</b>\n"
        f"╚══════════════════════════╝\n\n"
        f"{E_CHIPS} Баланс: <b>{p['chips']}</b>\n\n"
        f"Выбери игру:"
    )
    kb = ikb(
        [("🎰 Слоты (×2…×10)", "cas:slots", "success")],
        [("🎲 Кости (×2)", "cas:dice", "primary"),
         ("🪙 Монетка (×2)", "cas:coin", "primary")],
        [("🎡 Рулетка (×2 / ×14)", "cas:roulette", "danger")],
        [("⬅️ В меню", "arena:menu", "success")],
    )
    return text, kb


def bet_keyboard(game: str):
    rows = []
    line = []
    for b in CASINO_BETS:
        line.append((f"{b}💰", f"cas:{game}:bet:{b}", "primary"))
        if len(line) == 4:
            rows.append(line)
            line = []
    if line:
        rows.append(line)
    rows.append([("💥 Всё (all-in)", f"cas:{game}:allin", "danger")])
    rows.append([("⬅️ В казино", "cas:menu", "success")])
    return ikb(*rows)


def play_slots(uid: int, bet: int):
    p = get_player(uid)
    if not p or p["chips"] < bet:
        return None, "Недостаточно фишек."
    symbols = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣"]
    weights = [25, 22, 20, 15, 12, 6]
    spin = random.choices(symbols, weights=weights, k=3)
    add_chips(uid, -bet)
    if spin[0] == spin[1] == spin[2]:
        mult = {"7️⃣": 10, "💎": 8}.get(spin[0], 5)
        win = bet * mult
        add_chips(uid, win)
        return f"{' | '.join(spin)}\n\n{E_TROPHY} <b>Джекпот ×{mult}!</b> +{win}💰", None
    if spin[0] == spin[1] or spin[1] == spin[2] or spin[0] == spin[2]:
        win = int(bet * 2)
        add_chips(uid, win)
        return f"{' | '.join(spin)}\n\n✅ Пара! +{win}💰", None
    return f"{' | '.join(spin)}\n\n{E_SKULL} Мимо. −{bet}💰", None


def play_dice(uid: int, bet: int):
    p = get_player(uid)
    if not p or p["chips"] < bet:
        return None, "Недостаточно фишек."
    player = random.randint(1, 6)
    dealer = random.randint(1, 6)
    add_chips(uid, -bet)
    if player > dealer:
        win = bet * 2
        add_chips(uid, win)
        return f"{E_DICE} Ты: {player} · Дилер: {dealer}\n\n{E_TROPHY} Победа! +{win}💰", None
    if player == dealer:
        add_chips(uid, bet)
        return f"{E_DICE} Ты: {player} · Дилер: {dealer}\n\n🤝 Ничья. Ставка возвращена.", None
    return f"{E_DICE} Ты: {player} · Дилер: {dealer}\n\n{E_SKULL} Поражение. −{bet}💰", None


def play_coin(uid: int, bet: int, choice: str = "heads"):
    p = get_player(uid)
    if not p or p["chips"] < bet:
        return None, "Недостаточно фишек."
    result = random.choice(["heads", "tails"])
    add_chips(uid, -bet)
    if result == choice:
        win = bet * 2
        add_chips(uid, win)
        return f"{E_COIN} Выпало: <b>{'Орёл' if result == 'heads' else 'Решка'}</b>\n\n{E_TROPHY} Победа! +{win}💰", None
    return f"{E_COIN} Выпало: <b>{'Орёл' if result == 'heads' else 'Решка'}</b>\n\n{E_SKULL} Поражение. −{bet}💰", None


def play_roulette(uid: int, bet: int, color: str = "red"):
    p = get_player(uid)
    if not p or p["chips"] < bet:
        return None, "Недостаточно фишек."
    reds = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    num = random.randint(0, 36)
    if num == 0:
        res_color = "green"
    elif num in reds:
        res_color = "red"
    else:
        res_color = "black"
    add_chips(uid, -bet)
    if color == res_color:
        mult = 14 if color == "green" else 2
        win = bet * mult
        add_chips(uid, win)
        return f"🎡 Выпало: <b>{num} {res_color}</b>\n\n{E_TROPHY} Победа ×{mult}! +{win}💰", None
    return f"🎡 Выпало: <b>{num} {res_color}</b>\n\n{E_SKULL} Поражение. −{bet}💰", None


# ════════════════════════════════════════════════════════════════════
#  РП
# ════════════════════════════════════════════════════════════════════

RP_ACTIONS = {
    "ударить":    ("👊", "ударил(а)"),
    "обнять":     ("🤗", "обнял(а)"),
    "поцеловать": ("😘", "поцеловал(а)"),
    "пнуть":      ("🦵", "пнул(а)"),
    "погладить":  ("🤚", "погладил(а)"),
    "укусить":    ("😬", "укусил(а)"),
    "пожать":     ("🤝", "пожал(а) руку"),
    "толкнуть":   ("💥", "толкнул(а)"),
    "кинуть":     ("🥊", "кинул(а) в"),
    "лечить":     ("💊", "подлечил(а)"),
}

RP_COOLDOWNS: dict[tuple, float] = {}


def rp_text(actor_name: str, target_name: str, action: str) -> str:
    emoji, verb = RP_ACTIONS.get(action, ("✨", action))
    return f"{emoji} <b>{esc(actor_name)}</b> {verb} <b>{esc(target_name)}</b>!"


# ════════════════════════════════════════════════════════════════════
#  ХЕНДЛЕРЫ
# ════════════════════════════════════════════════════════════════════

router = Router()


class Reg(StatesGroup):
    name = State()


class DuelFind(StatesGroup):
    target = State()


HELP_TEXT = (
    "╔══════════════════════════╗\n"
    "   ⚔️ <b>АРЕНА ДУЭЛЯНТОВ</b>\n"
    "╚══════════════════════════╝\n\n"
    "PvP + казино + РП + боссы.\n\n"
    "<b>Как писать команды:</b>\n"
    "• В <b>группе</b> — только ответом на сообщение игрока.\n"
    "• В <b>ЛС</b> — ответом или по <code>@username</code> / ID.\n\n"
    "<b>Игрокам:</b>\n"
    "• <code>перчатка</code> — вызвать на бой\n"
    "• <code>перевод 100</code> — перевести фишки\n"
    "• <code>ударить</code>, <code>обнять</code>, <code>поцеловать</code>, <code>пнуть</code>,\n"
    "  <code>погладить</code>, <code>укусить</code>, <code>пожать</code>, <code>толкнуть</code>,\n"
    "  <code>кинуть</code>, <code>лечить</code>\n"
    "• <code>фото</code>, <code>топ</code>, <code>босс</code>, <code>help</code>\n\n"
    "<b>Админу:</b>\n"
    "• <code>бан</code> / <code>разбан</code>\n"
    "• <code>выдать 1000</code>, <code>очки 5</code>, <code>винрейт 50</code>\n"
    "• <code>стоп</code>, <code>рассылка текст</code>, <code>ботов 10</code>\n\n"
    "<b>Бой:</b> атакующий выбирает зону удара, защищающийся — зону защиты. "
    "Совпало → блок. Иначе урон = оружие − броня зоны.\n"
    f"⏱ У игроков {TURN_TIMEOUT} сек на ход, бот отвечает мгновенно."
)


async def flush_notifications(m: Message):
    rows = qa("SELECT id, text FROM notifications WHERE user_id=? AND seen=0 ORDER BY id LIMIT 15",
              (m.from_user.id,))
    if not rows:
        return
    ids = [r["id"] for r in rows]
    if ids:
        placeholders = ",".join("?" * len(ids))
        ex(f"UPDATE notifications SET seen=1 WHERE id IN ({placeholders})", tuple(ids))
    await m.answer("📬 <b>Пока тебя не было:</b>\n\n" + "\n\n".join(r["text"] for r in rows))


def touch_username(m: Message):
    if m.from_user:
        ex("UPDATE players SET username=? WHERE user_id=?", (m.from_user.username, m.from_user.id))


def is_banned(uid) -> bool:
    p = get_player(uid)
    return bool(p and p["banned"])


# ── Резолвер цели ─────────────────────────────────────────────────

def is_private(m: Message) -> bool:
    return m.chat.type == "private"


def resolve_target_by_text(text: str) -> Optional[int]:
    if not text:
        return None
    parts = text.split()
    for token in parts:
        key = token.strip().lstrip("@").strip(",.:;!?")
        if not key:
            continue
        if key.lstrip("-").isdigit():
            row = q1("SELECT user_id FROM players WHERE user_id=?", (int(key),))
            if row:
                return row["user_id"]
        row = q1(
            "SELECT user_id FROM players WHERE LOWER(username)=LOWER(?) OR LOWER(name)=LOWER(?) LIMIT 1",
            (key, key),
        )
        if row:
            return row["user_id"]
    return None


def resolve_target(m: Message, command_word: str) -> tuple[Optional[int], Optional[str]]:
    # Reply — если цель не бот
    if m.reply_to_message and m.reply_to_message.from_user:
        target_user = m.reply_to_message.from_user
        if not target_user.is_bot:
            return target_user.id, None

    if is_private(m):
        text = m.text or ""
        rest = text[len(command_word):].strip() if text.lower().startswith(command_word.lower()) else text
        tid = resolve_target_by_text(rest)
        if tid:
            return tid, None
        return None, f"Укажи цель: <code>{command_word} @user</code> или ответь на сообщение."
    return None, (
        f"⚠️ В группе команда работает <b>только ответом</b> на сообщение игрока.\n"
        f"Ответь на его сообщение и напиши <code>{command_word}</code>."
    )


# ════════════════════════════════════════════════════════════════════
#  /start и т.д.
# ════════════════════════════════════════════════════════════════════

@router.message(CommandStart())
async def cmd_start(m: Message, state: FSMContext):
    await state.clear()
    ensure_masked_bots(24)
    p = get_player(m.from_user.id)
    if p:
        touch_username(m)
        if is_private(m):
            await m.answer(f"С возвращением, <b>{esc(p['name'])}</b>! Арена ждёт 👇", reply_markup=MENU_KB)
            await flush_notifications(m)
        else:
            await m.answer(f"С возвращением, <b>{esc(p['name'])}</b>! Команды — ответом на сообщение.")
        return
    await state.set_state(Reg.name)
    await m.answer(
        "⚔️ <b>Добро пожаловать на Арену Дуэлянтов!</b>\n\n"
        "PvP + казино + РП + боссы.\n"
        "Броня на 4 части тела.\n\n"
        "Как зовут твоего бойца? (2–16 символов)",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Command("help"))
async def cmd_help(m: Message):
    await m.answer(HELP_TEXT, reply_markup=MENU_KB if (is_private(m) and get_player(m.from_user.id)) else None)


@router.message(Command("menu"))
async def cmd_menu(m: Message, state: FSMContext):
    await state.clear()
    if not get_player(m.from_user.id):
        return await m.answer("Сначала отправь /start.")
    if is_private(m):
        await m.answer("Главное меню 👇", reply_markup=MENU_KB)
        await flush_notifications(m)
    else:
        await m.answer("Меню доступно в ЛС с ботом.")


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
        f"{E_CHIPS} Стартовый баланс: {START_CHIPS}",
        reply_markup=MENU_KB if is_private(m) else None,
    )


# ════════════════════════════════════════════════════════════════════
#  МЕНЮ
# ════════════════════════════════════════════════════════════════════

async def show_arena(m):
    t, k = arena_menu_screen(m.from_user.id)
    await m.answer(t, reply_markup=k)


async def show_casino(m):
    t, k = casino_menu(m.from_user.id)
    await m.answer(t, reply_markup=k)


async def show_gear(m):
    t, k = gear_screen(m.from_user.id)
    await m.answer(t, reply_markup=k)


async def show_top(m):
    p = get_player(m.from_user.id)
    if not p:
        return
    t, k = top_screen(m.from_user.id, arena_of(p["wins"]))
    await m.answer(t, reply_markup=k)


async def show_rp(m):
    text = (
        "🎭 <b>РП-команды</b>\n\n"
        "В группе — ответом на сообщение игрока, одним словом:\n"
        "<code>ударить</code>, <code>обнять</code>, <code>поцеловать</code>, <code>пнуть</code>,\n"
        "<code>погладить</code>, <code>укусить</code>, <code>пожать</code>, <code>толкнуть</code>,\n"
        "<code>кинуть</code>, <code>лечить</code>.\n\n"
        "В ЛС — так же, или через <code>ударить @user</code>.\n\n"
        f"Откат: {RP_COOLDOWN} сек."
    )
    await m.answer(text)


MENU_HANDLERS = {
    BTN_ARENA: show_arena,
    BTN_CASINO: show_casino,
    BTN_GEAR: show_gear,
    BTN_TOP: show_top,
    BTN_RP: show_rp,
}


async def menu_dispatch(m, state):
    await state.clear()
    if is_banned(m.from_user.id):
        return await m.answer("🚫 Доступ закрыт.")
    if not get_player(m.from_user.id):
        return await m.answer("Сначала отправь /start.")
    touch_username(m)
    await flush_notifications(m)
    handler = MENU_HANDLERS.get(m.text)
    if handler:
        await handler(m)


@router.message(F.text.in_(MENU_TEXTS))
async def on_menu(m: Message, state: FSMContext):
    if not is_private(m):
        return
    await menu_dispatch(m, state)


# ════════════════════════════════════════════════════════════════════
#  БОЙ: НАЧАЛО
# ════════════════════════════════════════════════════════════════════

def start_duel(aid: int, bid: int, is_boss: bool = False,
               boss_key: Optional[str] = None, reward_mult: int = 1) -> Optional[Duel]:
    a_row = get_player(aid)
    if not a_row:
        return None
    fa = fighter_from_row(a_row)
    if is_boss and boss_key and boss_key in BOSSES:
        fb = boss_to_fighter(BOSSES[boss_key])
    else:
        b_row = get_player(bid)
        if not b_row:
            return None
        fb = fighter_from_row(b_row)
    attacker_is_a = random.random() < 0.5
    duel = Duel(a_id=aid, b_id=bid, a=fa, b=fb,
                attacker_is_a=attacker_is_a, is_boss=is_boss,
                boss_key=boss_key, reward_mult=reward_mult)
    first_name = fa.name if attacker_is_a else fb.name
    prefix = f"{E_BOSS} <b>БОСС</b> " if is_boss else ""
    duel.log.append(f"{prefix}Бой начался! Первым атакует <b>{first_name}</b>.")
    DUELS[aid] = duel
    if bid > 0:
        DUELS[bid] = duel
    return duel


async def begin_duel_msg(aid: int, bid: int, m: Message, bot: Bot,
                         is_boss: bool = False, boss_key: Optional[str] = None,
                         reward_mult: int = 1):
    if bid == aid:
        return await m.answer("🤨 Нельзя драться с самим собой.")
    if aid in DUELS:
        return await m.answer("У тебя уже идёт бой.")
    duel = start_duel(aid, bid, is_boss=is_boss, boss_key=boss_key, reward_mult=reward_mult)
    if not duel:
        return await m.answer("Не удалось начать бой.")
    role = duel.state_for(aid)
    if role == "attacker":
        text = duel_status_text(duel, aid, timer_left=TURN_TIMEOUT)
        await m.answer(text, reply_markup=attack_zone_kb())
        start_timer(duel, aid, "attacker", bot)
    else:
        atk_id = duel.attacker_id()
        if atk_id < 0:
            duel.atk_zone = bot_pick_attack_zone(duel.attacker(), duel.defender())
            text = duel_status_text(duel, aid, extra="⚔️ Соперник уже выбрал удар.",
                                    timer_left=TURN_TIMEOUT)
            await m.answer(text, reply_markup=defend_zone_kb())
            start_timer(duel, aid, "defender", bot)
        else:
            text = duel_status_text(duel, aid, extra="⏳ Соперник выбирает удар…")
            await m.answer(text, reply_markup=ikb([("🔄 Обновить", "duel:refresh", "primary")]))
    if bid > 0 and not is_boss:
        notify(bid, f"{E_GLOVE} <b>{esc(get_player(aid)['name'])}</b> кинул тебе перчатку! "
                    f"Открой «⚔️ Арена» в ЛС бота.")


# ════════════════════════════════════════════════════════════════════
#  КЛАВИАТУРЫ БОЯ
# ════════════════════════════════════════════════════════════════════

def attack_zone_kb() -> InlineKeyboardMarkup:
    return ikb(
        [("🧠 Голова ×1.5", "duel:atk:head", "danger"),
         ("🫀 Торс ×1.0", "duel:atk:torso", "danger")],
        [("💪 Руки ×0.8", "duel:atk:arms", "danger"),
         ("🦵 Ноги ×0.9", "duel:atk:legs", "danger")],
    )


def defend_zone_kb() -> InlineKeyboardMarkup:
    return ikb(
        [("🧠 Голова", "duel:def:head", "success"),
         ("🫀 Торс", "duel:def:torso", "success")],
        [("💪 Руки", "duel:def:arms", "success"),
         ("🦵 Ноги", "duel:def:legs", "success")],
    )


def duel_status_text(duel: Duel, for_uid: int, extra: str = "",
                     timer_left: Optional[int] = None) -> str:
    role = duel.state_for(for_uid)
    atk_name = duel.attacker().name
    me = duel.me(for_uid) or duel.a
    opp = duel.opponent(for_uid) or duel.b

    if role == "attacker":
        prompt = "🎯 <b>Твой ход</b> — выбери, куда бить"
    elif role == "defender":
        prompt = f"{E_SHIELD} <b>{atk_name}</b> атакует — выбери, что защищать"
    else:
        prompt = "⏳ Бой идёт…"

    if timer_left is not None and role in ("attacker", "defender"):
        prompt += f"\n⏱ Осталось: <b>{timer_left} сек</b>"

    if not duel.log:
        body = "  <i>Бой начинается…</i>"
    else:
        body = "\n".join(f"  {ln}" for ln in duel.log[-5:])

    boss_line = ""
    if duel.is_boss:
        boss_line = f"{E_BOSS} <b>БОЙ С БОССОМ</b>  ·  награда ×{duel.reward_mult}\n\n"

    return (
        f"╔══════════════════════════╗\n"
        f"      ⚔️ <b>РАУНД {duel.round_no}</b>\n"
        f"╚══════════════════════════╝\n\n"
        f"{boss_line}"
        f"┌─ 🔵 <b>ТЫ</b>\n"
        f"{fighter_card(me)}\n"
        f"└────────────\n\n"
        f"┌─ 🔴 <b>СОПЕРНИК</b>\n"
        f"{fighter_card(opp)}\n"
        f"└────────────\n\n"
        f"📜 <b>Последние действия:</b>\n{body}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{prompt}"
        + (f"\n\n{extra}" if extra else "")
    )


# ════════════════════════════════════════════════════════════════════
#  CALLBACKS
# ════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "arena:menu")
async def cb_arena_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = arena_menu_screen(cb.from_user.id)
    if t:
        await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data == "arena:bosses")
async def cb_arena_bosses(cb: CallbackQuery):
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = bosses_menu_screen(cb.from_user.id)
    if t:
        await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^arena:boss:\w+$"))
async def cb_arena_boss_fight(cb: CallbackQuery, bot: Bot):
    p = get_player(cb.from_user.id)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    if cb.from_user.id in DUELS:
        return await cb.answer("У тебя уже идёт бой.", show_alert=True)
    bkey = cb.data.split(":")[2]
    if bkey not in BOSSES:
        return await cb.answer("Босс не найден.", show_alert=True)
    b = BOSSES[bkey]
    if p["wins"] < b["min_wins"]:
        return await cb.answer(f"Нужно {b['min_wins']} 🏆 для этого босса.", show_alert=True)
    duel = start_duel(cb.from_user.id, -1, is_boss=True, boss_key=bkey, reward_mult=b["reward_mult"])
    if not duel:
        return await cb.answer("Ошибка запуска боя.", show_alert=True)
    role = duel.state_for(cb.from_user.id)
    if role == "attacker":
        text = duel_status_text(duel, cb.from_user.id, timer_left=TURN_TIMEOUT)
        await safe_edit(cb, text, attack_zone_kb())
        start_timer(duel, cb.from_user.id, "attacker", bot)
    else:
        duel.atk_zone = bot_pick_attack_zone(duel.attacker(), duel.defender())
        text = duel_status_text(duel, cb.from_user.id,
                                extra="⚔️ Босс уже выбрал удар.", timer_left=TURN_TIMEOUT)
        await safe_edit(cb, text, defend_zone_kb())
        start_timer(duel, cb.from_user.id, "defender", bot)
    await cb.answer(f"Бой с {b['name']} начался!")


@router.callback_query(F.data == "arena:find")
async def cb_arena_find(cb: CallbackQuery, bot: Bot):
    p = get_player(cb.from_user.id)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    if cb.from_user.id in DUELS:
        return await cb.answer("У тебя уже идёт бой.", show_alert=True)
    oid = pick_opponent(cb.from_user.id, p["wins"])
    if not oid:
        return await cb.answer("Не удалось подобрать соперника.", show_alert=True)
    duel = start_duel(cb.from_user.id, oid)
    if not duel:
        return await cb.answer("Не удалось начать бой.", show_alert=True)
    role = duel.state_for(cb.from_user.id)
    if role == "attacker":
        text = duel_status_text(duel, cb.from_user.id, timer_left=TURN_TIMEOUT)
        await safe_edit(cb, text, attack_zone_kb())
        start_timer(duel, cb.from_user.id, "attacker", bot)
    else:
        atk_id = duel.attacker_id()
        if atk_id < 0:
            duel.atk_zone = bot_pick_attack_zone(duel.attacker(), duel.defender())
            text = duel_status_text(duel, cb.from_user.id,
                                    extra="⚔️ Соперник уже выбрал удар.", timer_left=TURN_TIMEOUT)
            await safe_edit(cb, text, defend_zone_kb())
            start_timer(duel, cb.from_user.id, "defender", bot)
        else:
            text = duel_status_text(duel, cb.from_user.id, extra="⏳ Соперник выбирает удар…")
            await safe_edit(cb, text, ikb([("🔄 Обновить", "duel:refresh", "primary")]))
    await cb.answer()


@router.callback_query(F.data == "arena:list")
async def cb_arena_list(cb: CallbackQuery):
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = arena_list_screen(cb.from_user.id)
    if t:
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
async def cb_duel_pick(cb: CallbackQuery, bot: Bot):
    p = get_player(cb.from_user.id)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    if cb.from_user.id in DUELS:
        return await cb.answer("У тебя уже идёт бой.", show_alert=True)
    tid = int(cb.data.split(":")[2])
    if tid == cb.from_user.id:
        return await cb.answer("Нельзя драться с собой.", show_alert=True)
    duel = start_duel(cb.from_user.id, tid)
    if not duel:
        return await cb.answer("Соперник недоступен.", show_alert=True)
    role = duel.state_for(cb.from_user.id)
    if role == "attacker":
        text = duel_status_text(duel, cb.from_user.id, timer_left=TURN_TIMEOUT)
        await safe_edit(cb, text, attack_zone_kb())
        start_timer(duel, cb.from_user.id, "attacker", bot)
    else:
        atk_id = duel.attacker_id()
        if atk_id < 0:
            duel.atk_zone = bot_pick_attack_zone(duel.attacker(), duel.defender())
            text = duel_status_text(duel, cb.from_user.id,
                                    extra="⚔️ Соперник уже выбрал удар.", timer_left=TURN_TIMEOUT)
            await safe_edit(cb, text, defend_zone_kb())
            start_timer(duel, cb.from_user.id, "defender", bot)
        else:
            text = duel_status_text(duel, cb.from_user.id, extra="⏳ Соперник выбирает удар…")
            await safe_edit(cb, text, ikb([("🔄 Обновить", "duel:refresh", "primary")]))
    await cb.answer()


def profile_text(row) -> str:
    if not row:
        return "Профиль не найден."
    w = WEAPONS[row["weapon"]] if row["weapon"] in WEAPONS else WEAPONS["fists"]
    f = fighter_from_row(row)
    slots = player_armor_slots(row)
    arena = ARENAS[arena_of(row["wins"])]
    lines = [
        f"👤 <b>{esc(row['name'])}</b>",
        "",
        f"{E_TROPHY} {row['wins']}  ·  {E_SKULL} {row['losses']}  ·  {E_CHIPS} {row['chips']}",
        f"📍 {arena['emoji']} {arena['name']}",
        "",
        f"❤️ HP: <b>{f.max_hp}</b>",
        f"{w['emoji']} {w['name']} — урон <b>{w['dmg']}</b>",
        "",
        "<b>🛡 Броня:</b>",
    ]
    for slot in ZONES:
        item = ARMOR_ITEMS.get(slots[slot]) or armor_item_info(slot, "none")
        lines.append(f"  {ZONE_INFO[slot]['emoji']} {ZONE_INFO[slot]['name']}: "
                     f"{item['emoji']} {item['name']} ({item['df']})")
    return "\n".join(lines)


@router.callback_query(F.data.regexp(r"^duel:profile:-?\d+$"))
async def cb_duel_profile(cb: CallbackQuery):
    tid = int(cb.data.split(":")[2])
    row = get_player(tid)
    if not row:
        return await cb.answer("Игрок не найден.", show_alert=True)
    text = profile_text(row)
    kb = ikb([("⬅️ Назад", "arena:list", "success")],
             [("⚔️ Вызвать на бой", f"duel:pick:{tid}", "danger")])
    await safe_edit(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "duel:myprofile")
async def cb_my_profile(cb: CallbackQuery):
    row = get_player(cb.from_user.id)
    if not row:
        return await cb.answer("Сначала /start", show_alert=True)
    text = profile_text(row)
    kb = ikb([("⬅️ Назад", "arena:menu", "success")],
             [("🎒 Снаряжение", "gear:menu", "primary")])
    await safe_edit(cb, text, kb)
    await cb.answer()


# ════════════════════════════════════════════════════════════════════
#  БОЙ: атака/защита
# ════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.regexp(r"^duel:atk:(head|torso|arms|legs)$"))
async def cb_duel_attack(cb: CallbackQuery, bot: Bot):
    duel = DUELS.get(cb.from_user.id)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    if duel.state_for(cb.from_user.id) != "attacker":
        return await cb.answer("Сейчас не твой ход атаковать.", show_alert=True)
    if duel.timer_for != cb.from_user.id:
        return await cb.answer("Время вышло или ход уже сделан.", show_alert=True)
    stop_timer(duel)
    atk_zone = cb.data.split(":")[2]
    if atk_zone not in ZONES:
        return await cb.answer()
    duel.atk_zone = atk_zone
    def_id = duel.defender_id()

    if def_id < 0:
        bot_is_a = (def_id == duel.a_id)
        bot_f = duel.a if bot_is_a else duel.b
        attacker = duel.b if bot_is_a else duel.a
        if bot_wants_to_defend(duel, bot_is_a):
            def_zone = bot_pick_defend_zone(attacker, bot_f)
            duel.bot_last_block_round = duel.round_no
            duel.bot_block_streak += 1
            duel.log.append(f"🛡 {bot_f.name} встаёт в защиту")
        else:
            def_zone = None
            duel.bot_block_streak = 0
        await _resolve_round(duel, bot, cb=cb, atk_zone=atk_zone, def_zone=def_zone)
    else:
        attacker_name = duel.attacker().name
        text_b = duel_status_text(duel, def_id,
                                  extra=f"⚔️ {attacker_name} выбрал зону удара!",
                                  timer_left=TURN_TIMEOUT)
        try:
            await bot.send_message(def_id, text_b, reply_markup=defend_zone_kb())
        except Exception:
            pass
        start_timer(duel, def_id, "defender", bot)
        text_a = duel_status_text(duel, cb.from_user.id, extra="⏳ Ждём защиту соперника…")
        await safe_edit(cb, text_a, ikb([("🔄 Обновить", "duel:refresh", "primary")]))
    await cb.answer("Удар выбран.")


@router.callback_query(F.data.regexp(r"^duel:def:(head|torso|arms|legs)$"))
async def cb_duel_defend(cb: CallbackQuery, bot: Bot):
    duel = DUELS.get(cb.from_user.id)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    if duel.state_for(cb.from_user.id) != "defender":
        return await cb.answer("Сейчас ты не защищаешься.", show_alert=True)
    if duel.atk_zone is None:
        return await cb.answer("Атакующий ещё не выбрал зону.", show_alert=True)
    if duel.timer_for != cb.from_user.id:
        return await cb.answer("Время вышло или ход уже сделан.", show_alert=True)
    stop_timer(duel)
    def_zone = cb.data.split(":")[2]
    if def_zone not in ZONES:
        return await cb.answer()
    await _resolve_round(duel, bot, cb=cb, atk_zone=duel.atk_zone, def_zone=def_zone)


@router.callback_query(F.data == "duel:ready_def")
async def cb_duel_ready_def(cb: CallbackQuery):
    duel = DUELS.get(cb.from_user.id)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    if duel.state_for(cb.from_user.id) != "defender":
        return await cb.answer("Сейчас не твоя защита.", show_alert=True)
    if duel.atk_zone is None:
        return await cb.answer("Атакующий ещё выбирает зону.", show_alert=True)
    left = max(0, int(round(duel.timer_deadline - time.time()))) if duel.timer_for == cb.from_user.id else TURN_TIMEOUT
    text = duel_status_text(duel, cb.from_user.id,
                            extra=f"{E_SHIELD} Выбери зону защиты.", timer_left=left)
    await safe_edit(cb, text, defend_zone_kb())
    await cb.answer()


@router.callback_query(F.data == "duel:refresh")
async def cb_duel_refresh(cb: CallbackQuery):
    duel = DUELS.get(cb.from_user.id)
    if not duel:
        return await cb.answer("Бой не найден.", show_alert=True)
    role = duel.state_for(cb.from_user.id)
    if role == "attacker":
        if duel.timer_for == cb.from_user.id:
            left = max(0, int(round(duel.timer_deadline - time.time())))
            text = duel_status_text(duel, cb.from_user.id,
                                    extra="🎯 Выбери зону удара.", timer_left=left)
            await safe_edit(cb, text, attack_zone_kb())
        else:
            text = duel_status_text(duel, cb.from_user.id, extra="⏳ Ждём защиту соперника…")
            await safe_edit(cb, text, ikb([("🔄 Обновить", "duel:refresh", "primary")]))
    else:
        if duel.atk_zone is None:
            text = duel_status_text(duel, cb.from_user.id, extra="⏳ Соперник ещё выбирает удар…")
            await safe_edit(cb, text, ikb([("🔄 Обновить", "duel:refresh", "primary")]))
        else:
            left = max(0, int(round(duel.timer_deadline - time.time()))) if duel.timer_for == cb.from_user.id else TURN_TIMEOUT
            text = duel_status_text(duel, cb.from_user.id,
                                    extra=f"{E_SHIELD} Выбери зону защиты.", timer_left=left)
            await safe_edit(cb, text, defend_zone_kb())
    await cb.answer("Обновлено")


# ════════════════════════════════════════════════════════════════════
#  РАЗРЕШЕНИЕ РАУНДА
# ════════════════════════════════════════════════════════════════════

async def _resolve_round(duel: Duel, bot: Bot, cb: Optional[CallbackQuery],
                         atk_zone: str, def_zone: Optional[str]):
    stop_timer(duel)
    attacker = duel.attacker()
    defender = duel.defender()

    duel.log.append(f"── Раунд {duel.round_no} ──")
    duel.log.append(
        f"⚔️ {attacker.name} → {ZONE_INFO[atk_zone]['emoji']} {ZONE_INFO[atk_zone]['name']}"
    )
    if def_zone:
        duel.log.append(
            f"🛡 {defender.name} → {ZONE_INFO[def_zone]['emoji']} {ZONE_INFO[def_zone]['name']}"
        )

    tick_dots(attacker, duel.log)
    if not attacker.alive():
        return await _finish_duel(duel, winner_is_a=(attacker is duel.b), bot=bot)

    resolve_attack(attacker, defender, atk_zone, def_zone, duel.log)
    if not defender.alive():
        return await _finish_duel(duel, winner_is_a=(defender is duel.a), bot=bot)

    duel.atk_zone = None
    duel.attacker_is_a = not duel.attacker_is_a
    duel.round_no += 1

    if duel.round_no - duel.bot_last_block_round > 4:
        duel.bot_block_streak = 0

    if duel.round_no > MAX_ROUNDS:
        winner_is_a = duel.a.hp >= duel.b.hp
        return await _finish_duel(duel, winner_is_a=winner_is_a, bot=bot, reason="max_rounds")

    await _start_next_round(duel, bot)


async def _start_next_round(duel: Duel, bot: Bot):
    atk_id = duel.attacker_id()
    def_id = duel.defender_id()

    if atk_id > 0:
        text = duel_status_text(duel, atk_id,
                                extra="🎯 Твой ход — выбери зону удара.", timer_left=TURN_TIMEOUT)
        try:
            await bot.send_message(atk_id, text, reply_markup=attack_zone_kb())
        except Exception:
            pass
        start_timer(duel, atk_id, "attacker", bot)
    else:
        duel.atk_zone = bot_pick_attack_zone(duel.attacker(), duel.defender())
        duel.log.append(f"⚔️ {duel.attacker().name} выбрал удар")
        if def_id > 0:
            text = duel_status_text(duel, def_id,
                                    extra=f"{E_SHIELD} Соперник атакует — выбери зону защиты.",
                                    timer_left=TURN_TIMEOUT)
            try:
                await bot.send_message(def_id, text, reply_markup=defend_zone_kb())
            except Exception:
                pass
            start_timer(duel, def_id, "defender", bot)


async def _finish_duel(duel: Duel, winner_is_a: bool, bot: Bot, reason: str = "ko"):
    aid, bid = duel.a_id, duel.b_id
    a_row = get_player(aid)
    if not a_row:
        end_duel(duel)
        return
    b_row = get_player(bid) if bid and bid > 0 else None
    mult = duel.reward_mult if duel.is_boss else 1

    if winner_is_a:
        add_win(aid)
        arena_key = arena_of(get_player(aid)["wins"])
        prize = ARENAS[arena_key]["prize"] * mult
        add_chips(aid, prize)
        if bid and bid > 0:
            add_loss(bid)
            notify(bid, f"{E_SKULL} <b>{esc(a_row['name'])}</b> одолел тебя. −1 {E_TROPHY}")
        result_for_a = f"{E_TROPHY} <b>ПОБЕДА!</b> +1 {E_TROPHY}  ·  +{prize}{E_CHIPS}"
        result_for_b = f"{E_SKULL} <b>Поражение.</b> −1 {E_TROPHY}"
    else:
        if bid and bid > 0:
            add_win(bid)
            arena_key = arena_of(get_player(bid)["wins"])
            prize_b = ARENAS[arena_key]["prize"] * mult
            add_chips(bid, prize_b)
            notify(bid, f"{E_TROPHY} <b>{esc(a_row['name'])}</b> проиграл тебе! +1 {E_TROPHY}, +{prize_b}{E_CHIPS}")
        add_loss(aid)
        result_for_a = f"{E_SKULL} <b>ПОРАЖЕНИЕ.</b> −1 {E_TROPHY}"
        result_for_b = f"{E_TROPHY} <b>Победа!</b> +1 {E_TROPHY} и деньги"

    end_duel(duel)

    reason_line = ""
    if reason == "timeout":
        reason_line = f"\n⏱ Соперник не успел за {TURN_TIMEOUT} сек."
    elif reason == "max_rounds":
        reason_line = "\n⏱ Лимит раундов — победа по HP."

    new_a = get_player(aid)
    a_arena = ARENAS[arena_of(new_a["wins"])]
    footer_a = (
        f"\n╔══════════════════════════╗\n"
        f"  {result_for_a}\n"
        f"  {E_TROPHY} {new_a['wins']}  ·  {E_SKULL} {new_a['losses']}  ·  {E_CHIPS} {new_a['chips']}\n"
        f"  📍 {a_arena['emoji']} {a_arena['name']}"
        f"{reason_line}\n"
        f"╚══════════════════════════╝"
    )
    text_a = duel_status_text(duel, aid, extra=footer_a)
    kb_a = ikb([("⚔️ На арену", "arena:menu", "success")],
               [("🎲 Ещё бой", "arena:find", "danger")])
    try:
        await bot.send_message(aid, text_a, reply_markup=kb_a)
    except Exception:
        pass

    if bid and bid > 0:
        new_b = get_player(bid)
        if new_b:
            b_arena = ARENAS[arena_of(new_b["wins"])]
            footer_b = (
                f"\n╔══════════════════════════╗\n"
                f"  {result_for_b}\n"
                f"  {E_TROPHY} {new_b['wins']}  ·  {E_SKULL} {new_b['losses']}  ·  {E_CHIPS} {new_b['chips']}\n"
                f"  📍 {b_arena['emoji']} {b_arena['name']}"
                f"{reason_line}\n"
                f"╚══════════════════════════╝"
            )
            text_b = duel_status_text(duel, bid, extra=footer_b)
            kb_b = ikb([("⚔️ На арену", "arena:menu", "success")],
                       [("🎲 Ещё бой", "arena:find", "danger")])
            try:
                await bot.send_message(bid, text_b, reply_markup=kb_b)
            except Exception:
                pass


# ════════════════════════════════════════════════════════════════════
#  ТОП / СНАРЯЖЕНИЕ / КАЗИНО callbacks
# ════════════════════════════════════════════════════════════════════

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


@router.callback_query(F.data == "gear:menu")
async def cb_gear_menu(cb: CallbackQuery):
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = gear_screen(cb.from_user.id)
    if t:
        await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data == "gear:w")
async def cb_gear_weapon(cb: CallbackQuery):
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = weapon_list(cb.from_user.id)
    if t:
        await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data == "gear:armor_menu")
async def cb_gear_armor_menu(cb: CallbackQuery):
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = armor_slot_menu(cb.from_user.id)
    if t:
        await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^gear:(head|torso|arms|legs)$"))
async def cb_gear_armor_slot(cb: CallbackQuery):
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    slot = cb.data.split(":")[1]
    t, k = armor_slot_list(cb.from_user.id, slot)
    if t:
        await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^buy_weapon:(\w+)$"))
async def cb_buy_weapon(cb: CallbackQuery):
    p = get_player(cb.from_user.id)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    key = cb.data.split(":")[1]
    if key not in WEAPONS:
        return await cb.answer()
    item = WEAPONS[key]
    owned = set(p["weapons_owned"].split(","))
    if key in owned:
        ex("UPDATE players SET weapon=? WHERE user_id=?", (key, cb.from_user.id))
        toast = f"Надето: {item['name']}"
    elif p["chips"] >= item["price"]:
        ex("UPDATE players SET chips=chips-?, weapons_owned=?, weapon=? WHERE user_id=?",
           (item["price"], ",".join(owned | {key}), key, cb.from_user.id))
        toast = f"Куплено: {item['name']}"
    else:
        return await cb.answer(f"Нужно {item['price']}💰", show_alert=True)
    t, k = weapon_list(cb.from_user.id)
    if t:
        await safe_edit(cb, t, k)
    await cb.answer(toast)


@router.callback_query(F.data.regexp(r"^buy_armor:(head|torso|arms|legs):(none|light|medium|heavy|legend)$"))
async def cb_buy_armor(cb: CallbackQuery):
    p = get_player(cb.from_user.id)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    _, slot, level = cb.data.split(":")
    key = armor_item_key(slot, level)
    item = ARMOR_ITEMS.get(key)
    if not item:
        return await cb.answer("Предмет не найден.", show_alert=True)
    owned = set(p["armors_owned"].split(","))
    col = f"armor_{slot}"
    if key in owned:
        ex(f"UPDATE players SET {col}=? WHERE user_id=?", (key, cb.from_user.id))
        toast = f"Надето: {item['name']}"
    elif p["chips"] >= item["price"]:
        ex(f"UPDATE players SET chips=chips-?, armors_owned=?, {col}=? WHERE user_id=?",
           (item["price"], ",".join(owned | {key}), key, cb.from_user.id))
        toast = f"Куплено: {item['name']}"
    else:
        return await cb.answer(f"Нужно {item['price']}💰", show_alert=True)
    t, k = armor_slot_list(cb.from_user.id, slot)
    if t:
        await safe_edit(cb, t, k)
    await cb.answer(toast)


@router.callback_query(F.data == "cas:menu")
async def cb_cas_menu(cb: CallbackQuery):
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = casino_menu(cb.from_user.id)
    if t:
        await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^cas:(slots|dice|coin|roulette)$"))
async def cb_cas_game(cb: CallbackQuery):
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    game = cb.data.split(":")[1]
    titles = {
        "slots": f"{E_SLOT} Слоты",
        "dice": f"{E_DICE} Кости",
        "coin": f"{E_COIN} Монетка",
        "roulette": "🎡 Рулетка",
    }
    p = get_player(cb.from_user.id)
    text = (f"<b>{titles[game]}</b>\n\n"
            f"{E_CHIPS} Баланс: <b>{p['chips']}</b>\n\n"
            f"Выбери ставку:")
    await safe_edit(cb, text, bet_keyboard(game))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^cas:(slots|dice|coin|roulette):bet:\d+$"))
async def cb_cas_bet(cb: CallbackQuery):
    if not get_player(cb.from_user.id):
        return await cb.answer("Сначала /start", show_alert=True)
    _, game, _, bet_s = cb.data.split(":")
    bet = int(bet_s)
    await _process_bet(cb, game, bet)


@router.callback_query(F.data.regexp(r"^cas:(slots|dice|coin|roulette):allin$"))
async def cb_cas_allin(cb: CallbackQuery):
    p = get_player(cb.from_user.id)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    game = cb.data.split(":")[1]
    if p["chips"] <= 0:
        return await cb.answer("У тебя нет фишек.", show_alert=True)
    await _process_bet(cb, game, p["chips"])


async def _process_bet(cb: CallbackQuery, game: str, bet: int):
    p = get_player(cb.from_user.id)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    if bet <= 0:
        return await cb.answer("Неверная ставка.", show_alert=True)
    if p["chips"] < bet:
        return await cb.answer(f"Недостаточно фишек: нужно {bet}💰", show_alert=True)
    if game == "slots":
        result, err = play_slots(cb.from_user.id, bet)
    elif game == "dice":
        result, err = play_dice(cb.from_user.id, bet)
    elif game == "coin":
        result, err = play_coin(cb.from_user.id, bet)
    elif game == "roulette":
        result, err = play_roulette(cb.from_user.id, bet)
    else:
        return await cb.answer("Неизвестная игра.", show_alert=True)
    if err:
        return await cb.answer(err, show_alert=True)
    p2 = get_player(cb.from_user.id)
    kb = ikb(
        [("🔁 Ещё", f"cas:{game}", "success")],
        [("⬅️ В казино", "cas:menu", "primary")],
    )
    await safe_edit(cb, f"{result}\n\n{E_CHIPS} Баланс: <b>{p2['chips']}</b>", kb)
    await cb.answer()


# ════════════════════════════════════════════════════════════════════
#  ТЕКСТОВЫЕ КОМАНДЫ
# ════════════════════════════════════════════════════════════════════

def is_admin(uid: int) -> bool:
    return uid == ADMIN_ID


@router.message(F.text.regexp(r"(?i)^help$"))
async def txt_help(m: Message):
    if not get_player(m.from_user.id):
        return await m.answer("Сначала отправь /start в ЛС бота.")
    await m.answer(HELP_TEXT, reply_markup=MENU_KB if is_private(m) else None)


@router.message(F.text.regexp(r"(?i)^топ$"))
async def txt_top(m: Message):
    p = get_player(m.from_user.id)
    if not p:
        return await m.answer("Сначала /start в ЛС бота.")
    t, k = top_screen(m.from_user.id, arena_of(p["wins"]))
    await m.answer(t, reply_markup=k if is_private(m) else None)


@router.message(F.text.regexp(r"(?i)^фото$"))
async def txt_photo(m: Message):
    row = get_player(m.from_user.id)
    if not row:
        return await m.answer("Сначала /start в ЛС бота.")
    await m.answer(profile_text(row))


@router.message(F.text.regexp(r"(?i)^босс$"))
async def txt_boss(m: Message):
    if not get_player(m.from_user.id):
        return await m.answer("Сначала /start в ЛС бота.")
    if is_private(m):
        t, k = bosses_menu_screen(m.from_user.id)
        await m.answer(f"{E_BOSS} Выбери босса:", reply_markup=k if k else MENU_KB)
        if t:
            await m.answer(t)
    else:
        await m.answer(f"{E_BOSS} Меню боссов доступно в ЛС бота.")


@router.message(F.text.regexp(r"(?i)^перчатка(\s|$)"))
async def txt_glove(m: Message, bot: Bot):
    if not get_player(m.from_user.id):
        return await m.answer("Сначала /start в ЛС бота.")
    tid, err = resolve_target(m, "перчатка")
    if err:
        return await m.answer(err)
    if tid == m.from_user.id:
        return await m.answer("🤨 Нельзя вызвать себя.")
    target = get_player(tid)
    if not target:
        return await m.answer("Игрок не найден в боте.")
    if target["banned"]:
        return await m.answer("Этот игрок забанен.")
    if tid < 0:
        await begin_duel_msg(m.from_user.id, tid, m, bot)
        return
    notify(tid, f"{E_GLOVE} <b>{esc(get_player(m.from_user.id)['name'])}</b> кинул тебе перчатку!")
    await m.answer(f"{E_GLOVE} Ты кинул перчатку <b>{esc(target['name'])}</b>.")


@router.message(F.text.regexp(r"(?i)^перевод(\s|$)"))
async def txt_transfer(m: Message):
    row = get_player(m.from_user.id)
    if not row:
        return await m.answer("Сначала /start в ЛС бота.")
    tid, err = resolve_target(m, "перевод")
    if err:
        return await m.answer(err)
    if tid == m.from_user.id:
        return await m.answer("🤨 Себе переводить нельзя.")
    target = get_player(tid)
    if not target:
        return await m.answer("Игрок не найден.")
    if target["banned"]:
        return await m.answer("Этот игрок забанен.")
    amount = None
    for p in (m.text or "").split():
        if p.lstrip("-").isdigit():
            amount = int(p)
            break
    if not amount or amount <= 0:
        return await m.answer("Укажи сумму: <code>перевод 100</code>")
    if row["chips"] < amount:
        return await m.answer(f"Недостаточно фишек: у тебя {row['chips']}💰")
    add_chips(m.from_user.id, -amount)
    add_chips(tid, amount)
    await m.answer(f"{E_CHIPS} Переведено <b>{amount}</b> игроку <b>{esc(target['name'])}</b>.")
    notify(tid, f"{E_CHIPS} <b>{esc(row['name'])}</b> перевёл тебе <b>{amount}</b> фишек!")


async def _handle_rp(m: Message, action: str):
    if not get_player(m.from_user.id):
        return await m.answer("Сначала /start в ЛС бота.")
    tid, err = resolve_target(m, action)
    if err:
        return await m.answer(err)
    if tid == m.from_user.id:
        return await m.answer("🤨 Себе — нельзя.")
    target = get_player(tid)
    if not target:
        return await m.answer("Игрок не найден.")
    if target["banned"]:
        return await m.answer("Этот игрок забанен.")
    key = (m.from_user.id, action)
    now = time.time()
    last = RP_COOLDOWNS.get(key, 0)
    if now - last < RP_COOLDOWN:
        left = int(RP_COOLDOWN - (now - last)) + 1
        return await m.answer(f"⏱ Подожди ещё {left} сек.")
    RP_COOLDOWNS[key] = now
    actor = get_player(m.from_user.id)
    await m.answer(rp_text(actor["name"], target["name"], action))


@router.message(F.text.regexp(r"(?i)^ударить(\s|$)"))
async def rp_hit(m: Message):
    await _handle_rp(m, "ударить")


@router.message(F.text.regexp(r"(?i)^обнять(\s|$)"))
async def rp_hug(m: Message):
    await _handle_rp(m, "обнять")


@router.message(F.text.regexp(r"(?i)^поцеловать(\s|$)"))
async def rp_kiss(m: Message):
    await _handle_rp(m, "поцеловать")


@router.message(F.text.regexp(r"(?i)^пнуть(\s|$)"))
async def rp_kick(m: Message):
    await _handle_rp(m, "пнуть")


@router.message(F.text.regexp(r"(?i)^погладить(\s|$)"))
async def rp_pet(m: Message):
    await _handle_rp(m, "погладить")


@router.message(F.text.regexp(r"(?i)^укусить(\s|$)"))
async def rp_bite(m: Message):
    await _handle_rp(m, "укусить")


@router.message(F.text.regexp(r"(?i)^пожать(\s|$)"))
async def rp_handshake(m: Message):
    await _handle_rp(m, "пожать")


@router.message(F.text.regexp(r"(?i)^толкнуть(\s|$)"))
async def rp_push(m: Message):
    await _handle_rp(m, "толкнуть")


@router.message(F.text.regexp(r"(?i)^кинуть(\s|$)"))
async def rp_throw(m: Message):
    await _handle_rp(m, "кинуть")


@router.message(F.text.regexp(r"(?i)^лечить(\s|$)"))
async def rp_heal(m: Message):
    await _handle_rp(m, "лечить")


# ── Админ ─────────────────────────────────────────────────────────

@router.message(F.text.regexp(r"(?i)^бан(\s|$)"))
async def adm_ban(m: Message):
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_target(m, "бан")
    if err or not tid:
        return await m.answer(err or "Не найдено.")
    ex("UPDATE players SET banned=1 WHERE user_id=?", (tid,))
    DUELS.pop(tid, None)
    await m.answer(f"🚫 Игрок <code>{tid}</code> забанен.")


@router.message(F.text.regexp(r"(?i)^разбан(\s|$)"))
async def adm_unban(m: Message):
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_target(m, "разбан")
    if err or not tid:
        return await m.answer(err or "Не найдено.")
    ex("UPDATE players SET banned=0 WHERE user_id=?", (tid,))
    await m.answer(f"✅ Игрок <code>{tid}</code> разбанен.")


@router.message(F.text.regexp(r"(?i)^выдать(\s|$)"))
async def adm_give(m: Message):
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_target(m, "выдать")
    if err or not tid:
        return await m.answer(err or "Не найдено.")
    amount = None
    for p in (m.text or "").split():
        if p.lstrip("-").isdigit():
            amount = int(p)
            break
    if not amount:
        return await m.answer("Укажи сумму: <code>выдать 1000</code>")
    add_chips(tid, amount)
    await m.answer(f"✅ Выдано {amount}💰 игроку <code>{tid}</code>.")
    notify(tid, f"🎁 Админ выдал тебе {amount}💰")


@router.message(F.text.regexp(r"(?i)^очки(\s|$)"))
async def adm_points(m: Message):
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_target(m, "очки")
    if err or not tid:
        return await m.answer(err or "Не найдено.")
    amount = None
    for p in (m.text or "").split():
        if p.lstrip("-").isdigit():
            amount = int(p)
            break
    if not amount:
        return await m.answer("Укажи число: <code>очки 5</code>")
    ex("UPDATE players SET wins=wins+? WHERE user_id=?", (amount, tid))
    await m.answer(f"✅ Игроку <code>{tid}</code> начислено {amount} 🏆.")
    notify(tid, f"🎁 Админ начислил тебе {amount} {E_TROPHY}")


@router.message(F.text.regexp(r"(?i)^винрейт(\s|$)"))
async def adm_setwins(m: Message):
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_target(m, "винрейт")
    if err or not tid:
        return await m.answer(err or "Не найдено.")
    amount = None
    for p in (m.text or "").split():
        if p.isdigit():
            amount = int(p)
            break
    if amount is None:
        return await m.answer("Укажи число: <code>винрейт 50</code>")
    ex("UPDATE players SET wins=? WHERE user_id=?", (amount, tid))
    await m.answer(f"✅ Игроку <code>{tid}</code> установлено {amount} 🏆.")
    notify(tid, f"🎁 Админ установил тебе {amount} {E_TROPHY}")


@router.message(F.text.regexp(r"(?i)^стоп(\s|$)"))
async def adm_endduel(m: Message):
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_target(m, "стоп")
    if err or not tid:
        return await m.answer(err or "Не найдено.")
    if tid in DUELS:
        end_duel(DUELS[tid])
        await m.answer(f"✅ Бой игрока <code>{tid}</code> сброшен.")
    else:
        await m.answer("У игрока нет боя.")


@router.message(F.text.regexp(r"(?i)^рассылка\s+"))
async def adm_broadcast(m: Message, bot: Bot):
    if not is_admin(m.from_user.id):
        return
    text = (m.text or "").split(" ", 1)[1].strip()
    if not text:
        return await m.answer("Использование: <code>рассылка текст</code>")
    rows = qa("SELECT user_id FROM players WHERE banned=0 AND is_bot=0")
    ok = 0
    for r in rows:
        try:
            await bot.send_message(r["user_id"], f"📢 <b>Сообщение:</b>\n\n{text}")
            ok += 1
        except Exception:
            pass
    await m.answer(f"✅ Отправлено {ok} игрокам.")


@router.message(F.text.regexp(r"(?i)^ботов(\s|$)"))
async def adm_addbots(m: Message):
    if not is_admin(m.from_user.id):
        return
    n = 6
    for p in (m.text or "").split():
        if p.isdigit():
            n = int(p)
            break
    before = q1("SELECT COUNT(*) c FROM players WHERE is_bot=1")
    before = before["c"] if before else 0
    ensure_masked_bots(before + n)
    after = q1("SELECT COUNT(*) c FROM players WHERE is_bot=1")
    after = after["c"] if after else 0
    await m.answer(f"✅ Добавлено: {after - before}")


@router.message(Command("admin"))
async def cmd_admin(m: Message):
    if not is_admin(m.from_user.id):
        return
    await m.answer(
        "🛠 <b>Админ-команды</b>\n\n"
        "• <code>бан</code> / <code>разбан</code>\n"
        "• <code>выдать 1000</code>\n"
        "• <code>очки 5</code>\n"
        "• <code>винрейт 50</code>\n"
        "• <code>стоп</code>\n"
        "• <code>рассылка текст</code>\n"
        "• <code>ботов 10</code>"
    )


@router.message(Command("stats"))
async def cmd_stats(m: Message):
    if not is_admin(m.from_user.id):
        return
    total = q1("SELECT COUNT(*) c FROM players WHERE is_bot=0")
    bots = q1("SELECT COUNT(*) c FROM players WHERE is_bot=1")
    banned = q1("SELECT COUNT(*) c FROM players WHERE banned=1")
    total = total["c"] if total else 0
    bots = bots["c"] if bots else 0
    banned = banned["c"] if banned else 0
    unique_duels = len({id(d) for d in DUELS.values()})
    await m.answer(f"📊 Игроков: {total}\n🤖 Скрытых: {bots}\n🚫 Бан: {banned}\n⚔️ Активных боёв: {unique_duels}")


@router.message(DuelFind.target, F.text)
async def duel_find_target(m: Message, state: FSMContext, bot: Bot):
    if not is_private(m):
        return await state.clear()
    if m.text in MENU_TEXTS:
        return await menu_dispatch(m, state)
    await state.clear()
    key = m.text.strip().lstrip("@")
    p = get_player(m.from_user.id)
    if not p:
        return await m.answer("Сначала /start.")
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
        return await begin_duel_msg(m.from_user.id, target, m, bot)
    await begin_duel_msg(m.from_user.id, row["user_id"], m, bot)


@router.message()
async def fallback(m: Message):
    if not m.from_user:
        return
    if not get_player(m.from_user.id):
        if is_private(m):
            return await m.answer("Отправь /start, чтобы создать бойца ⚔️")
        return
    if is_banned(m.from_user.id):
        return await m.answer("🚫 Доступ закрыт.")
    if is_private(m):
        await m.answer("Пиши <code>help</code> или пользуйся меню внизу 👇", reply_markup=MENU_KB)
    else:
        await m.answer("В группе команды работают <b>ответом</b> на сообщение игрока.")


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
        BotCommand(command="help", description="Правила и команды"),
    ])
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
