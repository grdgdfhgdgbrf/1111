#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚔️ Арена Дуэлянтов — PvP-онли
Только PvP. Если соперник не найден — подставляется замаскированный бот,
неотличимый от обычного игрока (человеческий ник, обычный профиль, ответные бои).
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

START_CHIPS = 150
START_POINTS = 5
POINTS_PER_LEVEL = 2
BASE_STATS = {"hp": 100, "atk": 12, "defense": 4, "spd": 10, "crit": 5}
LEVEL_BONUS = {"hp": 10, "atk": 2, "defense": 1}
POINT_VALUE = {"hp": 10, "atk": 2, "defense": 2, "spd": 1, "crit": 1}

CRIT_CAP = 60
DEF_FACTOR = 0.7
BASE_SPEC_CD = 3
MAX_ROUNDS = 40
PVP_COOLDOWN = 8
PVP_FARM_LIMIT = 3

BODY_ZONES = {
    "head":  dict(name="Голова",  emoji="🧠", dmg=1.6, crit=2.2, miss=0.30, hp=0.20),
    "torso": dict(name="Торс",    emoji="🫀", dmg=1.0, crit=1.0, miss=0.08, hp=0.45),
    "arms":  dict(name="Руки",    emoji="💪", dmg=0.8, crit=0.8, miss=0.12, hp=0.20),
    "legs":  dict(name="Ноги",    emoji="🦵", dmg=0.9, crit=0.9, miss=0.15, hp=0.15),
}


def xp_need(level: int) -> int:
    return 40 + 20 * level


WEAPONS = {
    "dagger": dict(emoji="🗡", name="Кинжал", spec="Тысяча порезов",
                   desc="3 удара по 40% урона", price=0, chance=25),
    "sword": dict(emoji="⚔️", name="Меч", spec="Казнь",
                  desc="добивает цель с HP < 30% (урон ×3)", price=300, chance=25),
    "axe": dict(emoji="🪓", name="Топор", spec="Кровопускание",
                desc="кровотечение: 5% макс. HP цели, 3 раунда", price=600, chance=20),
    "bow": dict(emoji="🏹", name="Лук", spec="Снайперский выстрел",
                desc="100% крит, игнорирует защиту", price=800, chance=20),
    "staff": dict(emoji="🔥", name="Посох", spec="Огненный шторм",
                  desc="горение: 30% урона удара, 3 раунда", price=1200, chance=20),
    "hammer": dict(emoji="🔨", name="Молот", spec="Землетрясение",
                   desc="150% урона + оглушение", price=1500, chance=15),
}

ARMORS = {
    "none":   dict(emoji="👕", name="Без брони",   df=0,  hp=0,  price=0,    chance=0,  cd=0, dmg=0,  desc="—"),
    "light":  dict(emoji="🥋", name="Лёгкая",      df=3,  hp=10, price=200,  chance=10, cd=0, dmg=0,  desc="+10% шанс спец-атаки"),
    "medium": dict(emoji="🛡", name="Средняя",     df=6,  hp=25, price=500,  chance=0,  cd=1, dmg=0,  desc="−1 к откату спец-атаки"),
    "heavy":  dict(emoji="🏋️", name="Тяжёлая",     df=10, hp=50, price=1000, chance=0,  cd=0, dmg=20, desc="+20% урон спец-атаки"),
    "legend": dict(emoji="✨", name="Легендарная", df=15, hp=80, price=3000, chance=15, cd=0, dmg=30, desc="+15% шанс, +30% урон спец-атаки"),
}

# ── Человеческие ники для замаскированных соперников ────────────────
HUMAN_NAMES = [
    "Максим", "Артём", "Данил", "Кирилл", "Егор", "Иван", "Никита", "Рома",
    "Саня", "Дима", "Влад", "Серёга", "Паша", "Толя", "Женя", "Костя",
    "Лёха", "Миша", "Гриша", "Стас", "Олег", "Ден", "Марк", "Тимур",
    "Алина", "Катя", "Настя", "Даша", "Лера", "Соня", "Вика", "Полина",
    "Крис", "Милана", "Аня", "Юля", "Оля", "Маша", "Ксюша", "Ника",
]

HUMAN_TITLES = ["", "", "", "xd", "pro", "god", "tvoy", "real", "top", "_", "1", "007"]

# ── Меню ────────────────────────────────────────────────────────────
BTN_PVP = "🤺 PvP (игроки)"
BTN_CHAR = "🎒 Персонаж"
BTN_SHOP = "🏪 Магазин"
BTN_TOP = "🏆 Топ"
MENU_TEXTS = {BTN_PVP, BTN_CHAR, BTN_SHOP, BTN_TOP}

MENU_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_PVP)],
        [KeyboardButton(text=BTN_CHAR), KeyboardButton(text=BTN_SHOP)],
        [KeyboardButton(text=BTN_TOP)],
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
#  БОЕВОЙ ДВИЖОК
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
    weapon: str = "dagger"
    armor: str = "none"
    cd: int = 0
    stun: bool = False
    dots: list = field(default_factory=list)
    zone_hp: dict = field(default_factory=dict)

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


def zones_status(f: Fighter) -> str:
    parts = []
    for k in ("head", "torso", "arms", "legs"):
        cur = max(0, f.zone_hp[k])
        bar = "🟩" if cur > f.max_zone[k] * 0.5 else ("🟨" if cur > 0 else "🟥")
        parts.append(f"{bar}{BODY_ZONES[k]['emoji']}{cur}")
    return " ".join(parts)


def hit_damage(att, dfn, zone, mult=1.0, ignore_def=False):
    z = BODY_ZONES[zone]
    base = att.atk * random.uniform(0.85, 1.15) * z["dmg"]
    reduction = 0 if ignore_def else dfn.df * DEF_FACTOR
    return max(1, round((base - reduction) * mult))


def apply_damage(f, zone, dmg):
    f.zone_hp[zone] = max(0, f.zone_hp[zone] - dmg)
    f.hp = max(0, f.hp - dmg)
    if f.zone_hp[zone] == 0:
        return f" 💥 {BODY_ZONES[zone]['name']} выведена из строя!"
    return ""


def _add_dot(target, name, dmg, rounds):
    target.dots = [d for d in target.dots if d["name"] != name]
    target.dots.append({"name": name, "dmg": dmg, "left": rounds})


def use_special(att, dfn, zone):
    w = att.weapon
    m = att.spec_mult
    info = WEAPONS[w]
    head = f"{info['emoji']} <b>{info['spec']}!</b> "

    if w == "dagger":
        hits = [hit_damage(att, dfn, zone, 0.4 * m) for _ in range(3)]
        total = sum(hits)
        note = apply_damage(dfn, zone, total)
        return head + f"{att.name}: {' + '.join(map(str, hits))} = <b>−{total}</b>{note}"
    if w == "sword":
        dmg = hit_damage(att, dfn, zone, 3 * m)
        note = apply_damage(dfn, zone, dmg)
        return head + f"{att.name} добивает {dfn.name} в {BODY_ZONES[zone]['name']}: <b>−{dmg}</b>{note}"
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


def take_turn(att, dfn, out, zone=None):
    for d in list(att.dots):
        att.hp = max(0, att.hp - d["dmg"])
        out.append(f"{d['name']}: {att.name} −{d['dmg']}")
        d["left"] -= 1
        if d["left"] <= 0:
            att.dots.remove(d)
        if att.hp == 0:
            out.append(f"☠️ {att.name} гибнет от эффектов")
            return

    if att.stun:
        att.stun = False
        if att.cd > 0:
            att.cd -= 1
        out.append(f"💫 {att.name} оглушён и пропускает ход")
        return

    ready = att.cd == 0
    if att.cd > 0:
        att.cd -= 1

    target_zone = zone if zone in dfn.alive_zones() else random.choice(dfn.alive_zones() or ["torso"])
    z = BODY_ZONES[target_zone]

    can_special = ready and not (att.weapon == "sword" and dfn.hp > dfn.max_hp * 0.3)
    if can_special and random.random() * 100 < att.spec_chance:
        out.append(use_special(att, dfn, target_zone))
        att.cd = att.spec_cd
        return

    if random.random() < z["miss"]:
        out.append(f"🌀 {att.name} промахнулся по «{z['name']}»")
        return

    dmg = hit_damage(att, dfn, target_zone)
    is_crit = random.random() * 100 < att.crit * z["crit"]
    if is_crit:
        dmg *= 2
    note = apply_damage(dfn, target_zone, dmg)
    out.append(
        f"{'💥 Крит!' if is_crit else '👊'} {att.name} → {dfn.name} [{z['emoji']} {z['name']}]: <b>−{dmg}</b>{note}"
    )


def choose_ai_zone(dfn):
    alive = dfn.alive_zones()
    if not alive:
        return "torso"
    if random.random() < 0.4:
        return random.choice(alive)
    return min(alive, key=lambda k: dfn.zone_hp[k])


def simulate(a, b, player_zone=None, player_is_a=True):
    blocks = []
    timed_out = False
    for rnd in range(1, MAX_ROUNDS + 1):
        if a.spd > b.spd or (a.spd == b.spd and random.random() < 0.5):
            order = [a, b]
        else:
            order = [b, a]
        lines = [f"<b>Раунд {rnd}</b>"]
        for att in order:
            dfn = b if att is a else a
            if att.is_dead() or dfn.is_dead():
                break
            zone = None
            if att is a and player_is_a:
                zone = player_zone if rnd == 1 else None
            else:
                zone = choose_ai_zone(dfn)
            take_turn(att, dfn, lines, zone)
            if att.is_dead() or dfn.is_dead():
                break
        lines.append(
            f"❤️ {a.name} {a.hp}/{a.max_hp} · {b.name} {b.hp}/{b.max_hp}\n"
            f"   {a.name}: {zones_status(a)}\n   {b.name}: {zones_status(b)}"
        )
        blocks.append("\n".join(lines))
        if a.is_dead() or b.is_dead():
            break
    else:
        timed_out = True

    if a.is_dead() and b.is_dead():
        winner = a if a.hp >= b.hp else b
    elif a.is_dead():
        winner = b
    elif b.is_dead():
        winner = a
    else:
        ra = a.hp / a.max_hp + 0.5 * (len(a.alive_zones()) / 4)
        rb = b.hp / b.max_hp + 0.5 * (len(b.alive_zones()) / 4)
        winner = a if ra > rb else b if rb > ra else random.choice([a, b])
    if timed_out:
        blocks.append("⏱ Бой затянулся — победа по остатку HP.")
    return winner, blocks


def render_battle(blocks, head, foot, limit=3900):
    budget = limit - len(head) - len(foot) - 80
    picked, total = [], 0
    for blk in reversed(blocks):
        if total + len(blk) + 2 > budget:
            break
        picked.append(blk)
        total += len(blk) + 2
    picked.reverse()
    skipped = len(blocks) - len(picked)
    body = "\n\n".join(picked)
    if skipped:
        body = f"<i>… скрыто раундов: {skipped}</i>\n\n{body}"
    return f"{head}\n\n{body}\n\n{foot}"


def zone_keyboard(prefix, back_data=None):
    rows = []
    for key, z in BODY_ZONES.items():
        rows.append([(f"{z['emoji']} {z['name']} (×{z['dmg']:.1f})", f"{prefix}:{key}", "primary")])
    if back_data:
        rows.append([("⬅️ Назад", back_data, "success")])
    return ikb(*rows)


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
            level INTEGER NOT NULL DEFAULT 1,
            xp INTEGER NOT NULL DEFAULT 0,
            chips INTEGER NOT NULL DEFAULT 0,
            points INTEGER NOT NULL DEFAULT 0,
            hp INTEGER NOT NULL,
            atk INTEGER NOT NULL,
            defense INTEGER NOT NULL,
            spd INTEGER NOT NULL,
            crit INTEGER NOT NULL,
            weapon TEXT NOT NULL DEFAULT 'dagger',
            armor TEXT NOT NULL DEFAULT 'none',
            weapons_owned TEXT NOT NULL DEFAULT 'dagger',
            armors_owned TEXT NOT NULL DEFAULT 'none',
            wins INTEGER NOT NULL DEFAULT 0,
            losses INTEGER NOT NULL DEFAULT 0,
            pvp_wins INTEGER NOT NULL DEFAULT 0,
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
        "INSERT OR IGNORE INTO players (user_id, username, name, chips, points, hp, atk, defense, spd, crit, created) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (uid, username, name, START_CHIPS, START_POINTS,
         s["hp"], s["atk"], s["defense"], s["spd"], s["crit"], time.time()),
    )


def notify(uid, text):
    ex("INSERT INTO notifications (user_id, text, ts) VALUES (?,?,?)", (uid, text, time.time()))


def apply_result(uid, *, chips=0, xp=0, win=None, pvp=False):
    p = get_player(uid)
    if not p:
        return 1, 0
    lvl, cur = p["level"], p["xp"] + xp
    hp, atk, df, pts = p["hp"], p["atk"], p["defense"], p["points"]
    ups = 0
    while cur >= xp_need(lvl):
        cur -= xp_need(lvl)
        lvl += 1
        ups += 1
        hp += LEVEL_BONUS["hp"]
        atk += LEVEL_BONUS["atk"]
        df += LEVEL_BONUS["defense"]
        pts += POINTS_PER_LEVEL
    ex(
        "UPDATE players SET level=?, xp=?, chips=chips+?, points=?, hp=?, atk=?, defense=?, "
        "wins=wins+?, losses=losses+?, pvp_wins=pvp_wins+? WHERE user_id=?",
        (lvl, cur, chips, pts, hp, atk, df,
         int(win is True), int(win is False), int(win is True and pvp), uid),
    )
    return lvl, ups


def lvl_text(lvl, ups):
    if not ups:
        return ""
    return (
        f"\n🎉 <b>Новый уровень: {lvl}!</b> "
        f"+{ups * LEVEL_BONUS['hp']} HP, +{ups * LEVEL_BONUS['atk']} ATK, "
        f"+{ups * LEVEL_BONUS['defense']} DEF, +{ups * POINTS_PER_LEVEL} очк. прокачки"
    )


# ── Замаскированные боты ────────────────────────────────────────────

def _random_bot_name(existing: set) -> str:
    for _ in range(200):
        base = random.choice(HUMAN_NAMES)
        title = random.choice(HUMAN_TITLES)
        suffix = str(random.randint(1, 99)) if random.random() < 0.35 else ""
        name = f"{base}{title}{suffix}"
        if name.lower() not in existing and len(name) <= 16:
            existing.add(name.lower())
            return name
    return f"Игрок{random.randint(1000, 9999)}"


def ensure_masked_bots(count: int = 12):
    """Создаёт пул замаскированных ботов с человеческими никами."""
    existing = {r["name"].lower() for r in qa("SELECT name FROM players")}
    bots = qa("SELECT user_id FROM players WHERE is_bot=1")
    need = max(0, count - len(bots))
    for _ in range(need):
        name = _random_bot_name(existing)
        uid = -random.randint(10_000_000, 99_999_999)   # отрицательные id — не пересекаются с людьми
        lvl = random.randint(1, 12)
        s = BASE_STATS
        hp = s["hp"] + LEVEL_BONUS["hp"] * (lvl - 1) + random.randint(-10, 30)
        atk = s["atk"] + LEVEL_BONUS["atk"] * (lvl - 1) + random.randint(-2, 4)
        df = s["defense"] + LEVEL_BONUS["defense"] * (lvl - 1) + random.randint(-1, 3)
        spd = s["spd"] + random.randint(-2, 6)
        crit = min(CRIT_CAP, s["crit"] + random.randint(0, 15))
        weapon = random.choice(list(WEAPONS.keys()))
        armor = random.choice(list(ARMORS.keys()))
        wins = random.randint(lvl * 2, lvl * 9)
        losses = random.randint(lvl, lvl * 5)
        pvp_wins = random.randint(lvl, wins)
        ex(
            "INSERT INTO players (user_id, username, name, level, xp, chips, points, hp, atk, defense, spd, crit, "
            "weapon, armor, weapons_owned, armors_owned, wins, losses, pvp_wins, is_bot, created) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (uid, None, name, lvl, random.randint(0, xp_need(lvl) - 1),
             random.randint(50, 800), 0, hp, atk, df, spd, crit,
             weapon, armor, weapon, armor, wins, losses, pvp_wins, 1, time.time()),
        )


# ════════════════════════════════════════════════════════════════════
#  ФАБРИКИ
# ════════════════════════════════════════════════════════════════════

def player_fighter(p, hp=None):
    arm = ARMORS[p["armor"]]
    max_hp = p["hp"] + arm["hp"]
    return Fighter(
        name=esc(p["name"]),
        max_hp=max_hp,
        hp=max_hp if hp is None else max(1, min(hp, max_hp)),
        atk=p["atk"],
        df=p["defense"] + arm["df"],
        spd=p["spd"],
        crit=min(p["crit"], CRIT_CAP),
        weapon=p["weapon"],
        armor=p["armor"],
    )


def stats_line(f):
    return f"❤️{f.max_hp} ⚔️{f.atk} 🛡{f.df} 💨{f.spd} 🎯{f.crit}%"


# ════════════════════════════════════════════════════════════════════
#  ЭКРАНЫ
# ════════════════════════════════════════════════════════════════════

async def safe_edit(cb, text, markup=None):
    try:
        await cb.message.edit_text(text[:4090], reply_markup=markup)
    except TelegramBadRequest as e:
        if "not modified" not in str(e):
            await cb.message.answer(text[:4090], reply_markup=markup)


def char_screen(uid):
    p = get_player(uid)
    w, a = WEAPONS[p["weapon"]], ARMORS[p["armor"]]
    f = player_fighter(p)
    lines = [
        f"🎒 <b>{esc(p['name'])}</b> · ур. {p['level']}",
        f"✨ Опыт: {p['xp']}/{xp_need(p['level'])}   💰 Фишки: <b>{p['chips']}</b>",
        f"🏆 Победы: {p['wins']} (PvP: {p['pvp_wins']}) · 💀 Поражения: {p['losses']}",
        "",
        f"❤️ HP: <b>{f.max_hp}</b>" + (f" (броня +{a['hp']})" if a["hp"] else ""),
        f"⚔️ Атака: <b>{f.atk}</b>",
        f"🛡 Защита: <b>{f.df}</b>" + (f" (броня +{a['df']})" if a["df"] else ""),
        f"💨 Скорость: <b>{f.spd}</b>",
        f"🎯 Крит: <b>{f.crit}%</b>",
        "",
        f"{w['emoji']} Оружие: <b>{w['name']}</b> — {w['spec']}",
        f"    {w['desc']}",
        f"    шанс {f.spec_chance}% · урон ×{f.spec_mult:.1f} · откат {f.spec_cd}",
        f"{a['emoji']} Броня: <b>{a['name']}</b> — {a['desc']}",
        "",
        f"<b>Зоны тела:</b>",
        zones_status(f),
    ]
    rows = []
    if p["points"] > 0:
        lines.append(f"\n🎯 Свободных очков: <b>{p['points']}</b>")
        rows = [
            [(f"❤️ HP +{POINT_VALUE['hp']}", "up:hp", "success"),
             (f"⚔️ ATK +{POINT_VALUE['atk']}", "up:atk", "success")],
            [(f"🛡 DEF +{POINT_VALUE['defense']}", "up:defense", "success"),
             (f"💨 SPD +{POINT_VALUE['spd']}", "up:spd", "success")],
            [(f"🎯 Крит +{POINT_VALUE['crit']}%", "up:crit", "success")],
        ]
    return "\n".join(lines), (ikb(*rows) if rows else None)


def shop_screen(uid, page="w"):
    p = get_player(uid)
    is_w = page == "w"
    table = WEAPONS if is_w else ARMORS
    owned = set(p["weapons_owned" if is_w else "armors_owned"].split(","))
    equipped = p["weapon" if is_w else "armor"]

    lines = [f"🏪 <b>Магазин — {'оружие' if is_w else 'броня'}</b>",
             f"💰 Фишки: <b>{p['chips']}</b>", ""]
    rows = [[("⚔️ Оружие" + (" •" if is_w else ""), "shop:w", "primary"),
             ("🛡 Броня" + ("" if is_w else " •"), "shop:a", "primary")]]
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
    return "\n".join(lines), ikb(*rows)


def top_screen(uid):
    rows = qa("SELECT user_id, name, level, wins, pvp_wins FROM players "
              "ORDER BY wins DESC, level DESC, user_id LIMIT 10")
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Топ бойцов</b>", ""]
    for i, r in enumerate(rows):
        mark = medals[i] if i < 3 else f"{i + 1}."
        you = " ← ты" if r["user_id"] == uid else ""
        lines.append(f"{mark} <b>{esc(r['name'])}</b> — {r['wins']} поб. (PvP: {r['pvp_wins']}) · ур. {r['level']}{you}")
    me = get_player(uid)
    if me and all(r["user_id"] != uid for r in rows):
        rank = q1("SELECT COUNT(*) AS c FROM players WHERE wins > ?", (me["wins"],))["c"] + 1
        lines += ["…", f"{rank}. <b>{esc(me['name'])}</b> — {me['wins']} поб. · ур. {me['level']} ← ты"]
    return "\n".join(lines)


def pvp_screen():
    text = ("🤺 <b>PvP — арена игроков</b>\n\n"
            "Бой считается сразу по текущим билдам обоих.\n"
            "Соперник узнает результат, когда зайдёт в бота.\n\n"
            "🏆 Победа: фишки и опыт\n💀 Поражение: небольшой опыт")
    kb = ikb(
        [("🎲 Случайный соперник", "pvp:rand", "success")],
        [("📋 Список соперников", "pvp:list", "primary")],
        [("🔎 Вызвать по нику / ID", "pvp:find", "primary")],
    )
    return text, kb


def pvp_list_screen(uid):
    me = get_player(uid)
    rows = qa("SELECT user_id, name, level, wins FROM players WHERE user_id != ? AND banned=0 "
              "ORDER BY ABS(level - ?), RANDOM() LIMIT 8", (uid, me["level"]))
    if not rows:
        return "Сейчас никого нет в сети.", ikb([("⬅️ Назад", "pvp:menu", "primary")])
    kb_rows = [[(f"{r['name'][:18]} · ур.{r['level']} · 🏆{r['wins']}",
                 f"pvp:f:{r['user_id']}", "primary")] for r in rows]
    kb_rows.append([("⬅️ Назад", "pvp:menu", "primary")])
    return "📋 <b>Соперники:</b>", ikb(*kb_rows)


def pick_opponent(uid, level):
    """Возвращает user_id соперника. Если людей рядом нет — гарантированно даёт бота."""
    rows = qa("SELECT user_id FROM players WHERE user_id != ? AND banned=0 AND is_bot=0 "
              "ORDER BY ABS(level - ?), RANDOM() LIMIT 6", (uid, level))
    pool = [r["user_id"] for r in rows]
    bots = qa("SELECT user_id FROM players WHERE is_bot=1 AND banned=0 "
              "ORDER BY ABS(level - ?), RANDOM() LIMIT 6", (level,))
    bot_pool = [r["user_id"] for r in bots]
    # 55% шанс подсунуть бота, если рядом есть живые — чтобы соперники всегда находились
    if pool and bot_pool:
        return random.choice(bot_pool if random.random() < 0.55 else pool)
    if pool:
        return random.choice(pool)
    if bot_pool:
        return random.choice(bot_pool)
    ensure_masked_bots(6)
    rows = qa("SELECT user_id FROM players WHERE is_bot=1 ORDER BY RANDOM() LIMIT 1")
    return rows[0]["user_id"] if rows else None


def _bot_auto_weapon(p):
    """Замаскированный бот «экипируется» под уровень соперника — незаметно."""
    return p


def run_pvp(aid, did, first_zone: Optional[str] = None):
    back = ikb([("🎲 Ещё раз", "pvp:rand", "success"), ("🤺 В меню PvP", "pvp:menu", "primary")])
    a, d = get_player(aid), get_player(did)
    if not a:
        return "Профиль не найден.", back
    if not d:
        return "Соперник уже недоступен.", back
    if aid == did:
        return "🤨 Нельзя драться с самим собой.", back

    now = time.time()
    wait = PVP_COOLDOWN - (now - a["last_pvp"])
    if wait > 0:
        return f"⏳ Отдышись: следующий бой через {int(wait) + 1} с.", back
    ex("UPDATE players SET last_pvp=? WHERE user_id=?", (now, aid))

    fa, fd = player_fighter(a), player_fighter(d)
    winner, blocks = simulate(fa, fd, player_zone=first_zone, player_is_a=True)

    recent = q1("SELECT COUNT(*) AS c FROM pvp_log WHERE attacker=? AND defender=? AND ts>?",
                (aid, did, now - 3600))["c"]
    ex("INSERT INTO pvp_log (attacker, defender, ts) VALUES (?,?,?)", (aid, did, now))
    scale = 1.0 if recent < PVP_FARM_LIMIT else 0.25
    if d["level"] <= a["level"] - 5:
        scale *= 0.5

    head = f"🤺 <b>{fa.name}</b> (ур. {a['level']}) vs <b>{fd.name}</b> (ур. {d['level']})"
    an = esc(a["name"])

    if winner is fa:
        chips = int((30 + 8 * d["level"]) * scale)
        xp = int((30 + 5 * d["level"]) * scale)
        lvl, ups = apply_result(aid, chips=chips, xp=xp, win=True, pvp=True)
        foot = f"🏆 <b>Победа!</b> +{chips}💰 +{xp} XP" + lvl_text(lvl, ups)
        if scale < 1:
            foot += "\n<i>Награда снижена: фарм или слишком слабый соперник.</i>"
        # ответная реакция соперника — как будто он «получил уведомление»
        dl, du = apply_result(did, xp=5, win=False)
        notify(did, f"🤺 <b>{an}</b> (ур. {a['level']}) напал на тебя — ты проиграл 💀 (+5 XP)"
               + lvl_text(dl, du))
    else:
        lvl, ups = apply_result(aid, xp=10, win=False)
        foot = f"💀 <b>Поражение.</b> +10 XP" + lvl_text(lvl, ups)
        dl, du = apply_result(did, chips=15, xp=15, win=True, pvp=True)
        notify(did, f"🤺 <b>{an}</b> (ур. {a['level']}) напал на тебя — ты отбился! 🏆 +15💰 +15 XP"
               + lvl_text(dl, du))
    return render_battle(blocks, head, foot), back


# ════════════════════════════════════════════════════════════════════
#  ХЕНДЛЕРЫ
# ════════════════════════════════════════════════════════════════════

router = Router()
router.message.filter(F.chat.type == "private")


class Reg(StatesGroup):
    name = State()


class PvpFind(StatesGroup):
    target = State()


class AdminBroadcast(StatesGroup):
    text = State()


HELP_TEXT = (
    "⚔️ <b>Арена Дуэлянтов</b>\n\n"
    "• <b>PvP</b> — бои с игроками\n"
    "• <b>Магазин</b> — оружие и броня\n"
    "• <b>Персонаж</b> — прокачка\n"
    "• <b>Топ</b> — рейтинг\n\n"
    "Перед боем выбираешь <b>зону удара</b>: голова — больно, но легко промахнуться.\n"
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
    ensure_masked_bots(12)
    p = get_player(m.from_user.id)
    if p:
        touch_username(m)
        await m.answer(f"С возвращением, <b>{esc(p['name'])}</b>! Арена ждёт 👇", reply_markup=MENU_KB)
        await flush_notifications(m)
        return
    await state.set_state(Reg.name)
    await m.answer(
        "⚔️ <b>Добро пожаловать на Арену Дуэлянтов!</b>\n\n"
        "Создай бойца, прокачай его, купи снарягу и побеждай на арене.\n\n"
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
    existing = q1("SELECT 1 FROM players WHERE LOWER(name)=LOWER(?)", (name,))
    if existing:
        name = f"{name}{random.randint(1, 99)}"
    create_player(m.from_user.id, m.from_user.username, name)
    ensure_masked_bots(12)
    await state.clear()
    await m.answer(
        f"Боец <b>{esc(name)}</b> создан! 🎉\n\n"
        f"Тебе выдано {START_CHIPS}💰 и {START_POINTS} очков прокачки.",
        reply_markup=MENU_KB,
    )


# ── PvP find ───────────────────────────────────────────────────────

@router.message(PvpFind.target, F.text)
async def pvp_target(m: Message, state: FSMContext):
    if m.text in MENU_TEXTS:
        return await menu_dispatch(m, state)
    await state.clear()
    key = m.text.strip().lstrip("@")
    row = None
    if key.isdigit():
        row = q1("SELECT user_id FROM players WHERE user_id=? AND banned=0", (int(key),))
    if not row:
        row = q1("SELECT user_id FROM players WHERE (LOWER(username)=LOWER(?) OR LOWER(name)=LOWER(?)) "
                 "AND banned=0 LIMIT 1", (key, key))
    if not row:
        # соперник «не найден» — подставляем замаскированного бота с похожим ником
        target = pick_opponent(m.from_user.id, get_player(m.from_user.id)["level"])
        if not target:
            return await m.answer("Не удалось подобрать соперника, попробуй ещё раз.")
        text, kb = run_pvp(m.from_user.id, target)
        return await m.answer(text, reply_markup=kb)
    text, kb = run_pvp(m.from_user.id, row["user_id"])
    await m.answer(text, reply_markup=kb)


# ── Меню ───────────────────────────────────────────────────────────

async def show_pvp(m):
    t, k = pvp_screen()
    await m.answer(t, reply_markup=k)


async def show_char(m):
    t, k = char_screen(m.from_user.id)
    await m.answer(t, reply_markup=k)


async def show_shop(m):
    t, k = shop_screen(m.from_user.id, "w")
    await m.answer(t, reply_markup=k)


async def show_top(m):
    await m.answer(top_screen(m.from_user.id))


MENU_HANDLERS = {
    BTN_PVP: show_pvp,
    BTN_CHAR: show_char,
    BTN_SHOP: show_shop,
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


# ── Callback helpers ───────────────────────────────────────────────

async def require_player(cb: CallbackQuery):
    if is_banned(cb.from_user.id):
        await cb.answer("🚫 Доступ закрыт.", show_alert=True)
        return None
    p = get_player(cb.from_user.id)
    if not p:
        await cb.answer("Сначала /start", show_alert=True)
        return None
    return p


# ── Прокачка ──────────────────────────────────────────────────────

@router.callback_query(F.data.regexp(r"^up:(hp|atk|defense|spd|crit)$"))
async def cb_upgrade(cb: CallbackQuery):
    p = await require_player(cb)
    if not p:
        return
    stat = cb.data.split(":")[1]
    if p["points"] <= 0:
        return await cb.answer("Нет свободных очков", show_alert=True)
    if stat == "crit" and p["crit"] >= CRIT_CAP:
        return await cb.answer(f"Крит уже на максимуме ({CRIT_CAP}%)", show_alert=True)
    ex(f"UPDATE players SET {stat}={stat}+?, points=points-1 WHERE user_id=?",
       (POINT_VALUE[stat], cb.from_user.id))
    t, k = char_screen(cb.from_user.id)
    await safe_edit(cb, t, k)
    await cb.answer("Прокачано!")


# ── Магазин ───────────────────────────────────────────────────────

@router.callback_query(F.data.regexp(r"^shop:[wa]$"))
async def cb_shop_page(cb: CallbackQuery):
    if not await require_player(cb):
        return
    t, k = shop_screen(cb.from_user.id, cb.data.split(":")[1])
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^buy:[wa]:\w+$"))
async def cb_buy(cb: CallbackQuery):
    p = await require_player(cb)
    if not p:
        return
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
    t, k = shop_screen(cb.from_user.id, kind)
    await safe_edit(cb, t, k)
    await cb.answer(toast)


# ── PvP ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "pvp:menu")
async def cb_pvp_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    if not await require_player(cb):
        return
    t, k = pvp_screen()
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data == "pvp:list")
async def cb_pvp_list(cb: CallbackQuery):
    if not await require_player(cb):
        return
    t, k = pvp_list_screen(cb.from_user.id)
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data == "pvp:find")
async def cb_pvp_find(cb: CallbackQuery, state: FSMContext):
    if not await require_player(cb):
        return
    await state.set_state(PvpFind.target)
    await cb.message.answer("🔎 Отправь @username, ID или имя бойца.")
    await cb.answer()


@router.callback_query(F.data == "pvp:rand")
async def cb_pvp_rand(cb: CallbackQuery):
    p = await require_player(cb)
    if not p:
        return
    oid = pick_opponent(cb.from_user.id, p["level"])
    if oid is None:
        return await cb.answer("Не удалось подобрать соперника.", show_alert=True)
    d = get_player(oid)
    text = (f"⚔️ <b>Соперник найден</b>\n\n"
            f"<b>{esc(d['name'])}</b> · ур. {d['level']} · 🏆 {d['wins']}\n"
            f"{stats_line(player_fighter(d))}\n\n"
            f"Выбери, куда бить первым:")
    await safe_edit(cb, text, zone_keyboard(f"pvprand:{oid}", back_data="pvp:menu"))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^pvprand:-?\d+:(head|torso|arms|legs)$"))
async def cb_pvp_rand_fight(cb: CallbackQuery):
    if not await require_player(cb):
        return
    _, oid_s, zone = cb.data.split(":")
    oid = int(oid_s)
    text, kb = run_pvp(cb.from_user.id, oid, first_zone=zone)
    await safe_edit(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^pvp:f:-?\d+$"))
async def cb_pvp_fight(cb: CallbackQuery):
    p = await require_player(cb)
    if not p:
        return
    target = int(cb.data.split(":")[2])
    d = get_player(target)
    if not d:
        return await cb.answer("Соперник недоступен.", show_alert=True)
    text = (f"⚔️ <b>Вызов</b>\n\n"
            f"<b>{esc(d['name'])}</b> · ур. {d['level']} · 🏆 {d['wins']}\n"
            f"{stats_line(player_fighter(d))}\n\n"
            f"Выбери зону удара:")
    await safe_edit(cb, text, zone_keyboard(f"pvpfight:{target}", back_data="pvp:list"))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^pvpfight:-?\d+:(head|torso|arms|legs)$"))
async def cb_pvp_fight_zone(cb: CallbackQuery):
    if not await require_player(cb):
        return
    _, tid_s, zone = cb.data.split(":")
    tid = int(tid_s)
    text, kb = run_pvp(cb.from_user.id, tid, first_zone=zone)
    await safe_edit(cb, text, kb)
    await cb.answer()


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
        "/givepoints &lt;user_id&gt; &lt;n&gt;\n"
        "/setlevel &lt;user_id&gt; &lt;lvl&gt;\n"
        "/ban &lt;user_id&gt;\n"
        "/unban &lt;user_id&gt;\n"
        "/broadcast — рассылка\n"
        "/stats — статистика\n"
        "/addbots &lt;n&gt; — добавить замаскированных соперников"
    )


@router.message(Command("stats"))
async def cmd_stats(m: Message):
    if not admin_only(m.from_user.id):
        return
    total = q1("SELECT COUNT(*) c FROM players WHERE is_bot=0")["c"]
    bots = q1("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    banned = q1("SELECT COUNT(*) c FROM players WHERE banned=1")["c"]
    await m.answer(f"📊 Игроков: {total}\n🤖 Соперников (скрытых): {bots}\n🚫 Забанено: {banned}")


@router.message(Command("addbots"))
async def cmd_addbots(m: Message):
    if not admin_only(m.from_user.id):
        return
    parts = m.text.split()
    n = int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 6
    before = q1("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    ensure_masked_bots(before + n)
    after = q1("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    await m.answer(f"✅ Добавлено соперников: {after - before}")


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


@router.message(Command("givepoints"))
async def cmd_givepoints(m: Message):
    if not admin_only(m.from_user.id):
        return
    parts = m.text.split()
    if len(parts) != 3 or not parts[1].lstrip("-").isdigit() or not parts[2].isdigit():
        return await m.answer("Использование: /givepoints <user_id> <n>")
    uid, n = int(parts[1]), int(parts[2])
    if not get_player(uid):
        return await m.answer("Игрок не найден.")
    ex("UPDATE players SET points=points+? WHERE user_id=?", (n, uid))
    await m.answer(f"✅ Выдано {n} очков игроку {uid}")
    if uid > 0:
        notify(uid, f"🎁 Тебе начислено {n} очков прокачки")


@router.message(Command("setlevel"))
async def cmd_setlevel(m: Message):
    if not admin_only(m.from_user.id):
        return
    parts = m.text.split()
    if len(parts) != 3 or not parts[1].lstrip("-").isdigit() or not parts[2].isdigit():
        return await m.answer("Использование: /setlevel <user_id> <lvl>")
    uid, lvl = int(parts[1]), int(parts[2])
    if not get_player(uid):
        return await m.answer("Игрок не найден.")
    ex("UPDATE players SET level=?, xp=0 WHERE user_id=?", (lvl, uid))
    await m.answer(f"✅ Уровень {lvl} установлен игроку {uid}")


@router.message(Command("ban"))
async def cmd_ban(m: Message):
    if not admin_only(m.from_user.id):
        return
    parts = m.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await m.answer("Использование: /ban <user_id>")
    uid = int(parts[1])
    ex("UPDATE players SET banned=1 WHERE user_id=?", (uid,))
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
    ensure_masked_bots(12)
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