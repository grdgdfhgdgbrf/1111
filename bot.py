#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚔️ Арена Дуэлянтов — Telegram-бот (PvE / PvP / данжи / магазин / топ)

Стек: Python 3.10+, aiogram 3.7+, SQLite (стандартная библиотека).

Запуск:
    pip install "aiogram>=3.7"
    export BOT_TOKEN="123456:ABC..."      # токен от @BotFather
    python bot.py

Необязательные переменные окружения:
    DB_PATH   — путь к файлу базы (по умолчанию arena.db)

Весь баланс (цены, шансы, награды, формулы) вынесен в константы в начале файла.
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
#  КОНФИГ И БАЛАНС
# ════════════════════════════════════════════════════════════════════

DB_PATH = os.getenv("DB_PATH", "arena.db")

START_CHIPS = 100            # стартовые фишки
START_POINTS = 5             # стартовые очки прокачки
POINTS_PER_LEVEL = 2         # очков прокачки за уровень
BASE_STATS = {"hp": 100, "atk": 12, "defense": 4, "spd": 10, "crit": 5}
LEVEL_BONUS = {"hp": 10, "atk": 2, "defense": 1}          # за уровень
POINT_VALUE = {"hp": 10, "atk": 2, "defense": 2, "spd": 1, "crit": 1}  # за 1 очко

CRIT_CAP = 60                # максимум шанса крита, %
DEF_FACTOR = 0.7             # сколько урона гасит 1 единица защиты
BASE_SPEC_CD = 3             # откат спец-атаки (в ходах владельца)
MAX_ROUNDS = 40              # лимит раундов в бою
PVP_COOLDOWN = 15            # секунд между PvP-боями одного игрока
PVP_FARM_LIMIT = 3           # боёв с одним соперником в час без штрафа к награде


def xp_need(level: int) -> int:
    """Опыта до следующего уровня."""
    return 40 + 20 * level


# ── Оружие ──────────────────────────────────────────────────────────
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

# ── Броня ───────────────────────────────────────────────────────────
ARMORS = {
    "none": dict(emoji="👕", name="Без брони", df=0, hp=0, price=0,
                 chance=0, cd=0, dmg=0, desc="—"),
    "light": dict(emoji="🥋", name="Лёгкая", df=3, hp=10, price=200,
                  chance=10, cd=0, dmg=0, desc="+10% шанс спец-атаки"),
    "medium": dict(emoji="🛡", name="Средняя", df=6, hp=25, price=500,
                   chance=0, cd=1, dmg=0, desc="−1 к откату спец-атаки"),
    "heavy": dict(emoji="🏋️", name="Тяжёлая", df=10, hp=50, price=1000,
                  chance=0, cd=0, dmg=20, desc="+20% урон спец-атаки"),
    "legend": dict(emoji="✨", name="Легендарная", df=15, hp=80, price=3000,
                   chance=15, cd=0, dmg=30, desc="+15% шанс, +30% урон спец-атаки"),
}

# ── PvE-боты ────────────────────────────────────────────────────────
BOTS = [
    dict(name="🐀 Крысолов", hp=80, atk=10, df=3, spd=8, crit=3,
         weapon="dagger", armor="none", chips=30, xp=20),
    dict(name="🗡 Разбойник", hp=120, atk=14, df=5, spd=11, crit=6,
         weapon="dagger", armor="light", chips=60, xp=40),
    dict(name="🪖 Наёмник", hp=180, atk=19, df=8, spd=12, crit=8,
         weapon="axe", armor="medium", chips=110, xp=70),
    dict(name="🏹 Чемпион арены", hp=260, atk=25, df=12, spd=14, crit=10,
         weapon="bow", armor="heavy", chips=200, xp=120),
    dict(name="😈 Тёмный лорд", hp=380, atk=33, df=16, spd=16, crit=12,
         weapon="staff", armor="legend", chips=400, xp=220),
]

# ── Данжи ───────────────────────────────────────────────────────────
DUNGEONS = {
    "crypt": dict(emoji="🏚", name="Склеп", rooms=3, fee=50, prize=200, mult=1.0,
                  mobs=["💀 Скелет", "🧟 Зомби", "👻 Хранитель склепа"]),
    "cave": dict(emoji="🕳", name="Пещера", rooms=5, fee=150, prize=600, mult=1.3,
                 mobs=["🦇 Гигантская летучая мышь", "🕷 Паук-охотник", "🐺 Пещерный волк",
                       "🪨 Каменный голем", "🐉 Пещерный дракон"]),
    "fort": dict(emoji="🏰", name="Крепость", rooms=7, fee=400, prize=1500, mult=1.6,
                 mobs=["🛡 Страж ворот", "🏹 Лучник", "🐎 Рыцарь", "🧙 Боевой маг",
                       "⚔️ Капитан стражи", "😈 Палач", "👑 Король-лич"]),
}
DUNGEON_WEAPON_CYCLE = ["dagger", "sword", "axe", "bow", "staff"]
DUNGEON_ROOM_SCALE = 0.3     # рост силы монстров от комнаты к комнате
DUNGEON_BOSS_SCALE = 1.25    # усиление босса в последней комнате

# ── Меню ────────────────────────────────────────────────────────────
BTN_PVE = "⚔️ PvE (боты)"
BTN_PVP = "🤺 PvP (игроки)"
BTN_DG = "🏚 Данжи"
BTN_CHAR = "🎒 Персонаж"
BTN_SHOP = "🏪 Магазин"
BTN_TOP = "🏆 Топ"
MENU_TEXTS = {BTN_PVE, BTN_PVP, BTN_DG, BTN_CHAR, BTN_SHOP, BTN_TOP}

MENU_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_PVE), KeyboardButton(text=BTN_PVP)],
        [KeyboardButton(text=BTN_DG), KeyboardButton(text=BTN_CHAR)],
        [KeyboardButton(text=BTN_SHOP), KeyboardButton(text=BTN_TOP)],
    ],
    resize_keyboard=True,
)

esc = html.escape


# ════════════════════════════════════════════════════════════════════
#  БОЕВОЙ ДВИЖОК
# ════════════════════════════════════════════════════════════════════

@dataclass
class Fighter:
    name: str                # уже экранированное для HTML имя
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

    def __post_init__(self):
        w, a = WEAPONS[self.weapon], ARMORS[self.armor]
        self.spec_chance = min(w["chance"] + a["chance"], 70)
        self.spec_mult = 1 + a["dmg"] / 100
        self.spec_cd = max(0, BASE_SPEC_CD - a["cd"])


def hit_damage(att: Fighter, dfn: Fighter, mult: float = 1.0, ignore_def: bool = False) -> int:
    base = att.atk * random.uniform(0.85, 1.15)
    reduction = 0 if ignore_def else dfn.df * DEF_FACTOR
    return max(1, round((base - reduction) * mult))


def use_special(att: Fighter, dfn: Fighter) -> str:
    """Применяет спец-атаку оружия, возвращает строку для лога."""
    w = att.weapon
    m = att.spec_mult
    info = WEAPONS[w]
    head = f"{info['emoji']} <b>{info['spec']}!</b> "

    if w == "dagger":
        hits = [hit_damage(att, dfn, 0.4 * m) for _ in range(3)]
        total = sum(hits)
        dfn.hp = max(0, dfn.hp - total)
        return head + f"{att.name}: {' + '.join(map(str, hits))} = <b>−{total}</b>"

    if w == "sword":
        dmg = hit_damage(att, dfn, 3 * m)
        dfn.hp = max(0, dfn.hp - dmg)
        return head + f"{att.name} добивает {dfn.name}: <b>−{dmg}</b>"

    if w == "axe":
        dmg = hit_damage(att, dfn, m)
        dfn.hp = max(0, dfn.hp - dmg)
        bleed = max(1, round(dfn.max_hp * 0.05 * m))
        _add_dot(dfn, "🩸 Кровотечение", bleed, 3)
        return head + f"{att.name} → {dfn.name}: <b>−{dmg}</b>, кровь по <b>{bleed}</b> ×3"

    if w == "bow":
        dmg = hit_damage(att, dfn, 2 * m, ignore_def=True)
        dfn.hp = max(0, dfn.hp - dmg)
        return head + f"{att.name} → {dfn.name}: крит сквозь броню <b>−{dmg}</b>"

    if w == "staff":
        dmg = hit_damage(att, dfn, m)
        dfn.hp = max(0, dfn.hp - dmg)
        burn = max(1, round(dmg * 0.3))
        _add_dot(dfn, "🔥 Горение", burn, 3)
        return head + f"{att.name} → {dfn.name}: <b>−{dmg}</b>, огонь по <b>{burn}</b> ×3"

    if w == "hammer":
        dmg = hit_damage(att, dfn, 1.5 * m)
        dfn.hp = max(0, dfn.hp - dmg)
        dfn.stun = True
        return head + f"{att.name} → {dfn.name}: <b>−{dmg}</b>, цель оглушена"

    raise ValueError(w)


def _add_dot(target: Fighter, name: str, dmg: int, rounds: int) -> None:
    target.dots = [d for d in target.dots if d["name"] != name]  # не стакается
    target.dots.append({"name": name, "dmg": dmg, "left": rounds})


def take_turn(att: Fighter, dfn: Fighter, out: list) -> None:
    # 1) DOT-эффекты на самом ходящем
    for d in list(att.dots):
        att.hp = max(0, att.hp - d["dmg"])
        out.append(f"{d['name']}: {att.name} −{d['dmg']}")
        d["left"] -= 1
        if d["left"] <= 0:
            att.dots.remove(d)
        if att.hp == 0:
            out.append(f"☠️ {att.name} гибнет от эффектов")
            return

    # 2) оглушение
    if att.stun:
        att.stun = False
        if att.cd > 0:
            att.cd -= 1
        out.append(f"💫 {att.name} оглушён и пропускает ход")
        return

    # 3) откат спец-атаки
    ready = att.cd == 0
    if att.cd > 0:
        att.cd -= 1

    # 4) спец-атака или обычный удар
    can_special = ready and not (att.weapon == "sword" and dfn.hp > dfn.max_hp * 0.3)
    if can_special and random.random() * 100 < att.spec_chance:
        out.append(use_special(att, dfn))
        att.cd = att.spec_cd
    else:
        dmg = hit_damage(att, dfn)
        is_crit = random.random() * 100 < att.crit
        if is_crit:
            dmg *= 2
        dfn.hp = max(0, dfn.hp - dmg)
        out.append(f"{'💥 Крит!' if is_crit else '👊'} {att.name} → {dfn.name}: <b>−{dmg}</b>")


def simulate(a: Fighter, b: Fighter):
    """Авто-бой. Возвращает (победитель: Fighter, список текстовых блоков-раундов)."""
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
            if att.hp <= 0 or dfn.hp <= 0:
                break
            take_turn(att, dfn, lines)
            if att.hp <= 0 or dfn.hp <= 0:
                break
        lines.append(f"❤️ {a.name} {a.hp}/{a.max_hp} · {b.name} {b.hp}/{b.max_hp}")
        blocks.append("\n".join(lines))
        if a.hp <= 0 or b.hp <= 0:
            break
    else:
        timed_out = True

    if a.hp <= 0:
        winner = b
    elif b.hp <= 0:
        winner = a
    else:  # лимит раундов — побеждает тот, у кого больше доля HP
        ra, rb = a.hp / a.max_hp, b.hp / b.max_hp
        winner = a if ra > rb else b if rb > ra else random.choice([a, b])
    if timed_out:
        blocks.append("⏱ Время боя вышло — победа по остатку HP.")
    return winner, blocks


def render_battle(blocks: list, head: str, foot: str, limit: int = 3900) -> str:
    """Собирает лог боя так, чтобы влезть в сообщение Telegram (берём последние раунды)."""
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


# ════════════════════════════════════════════════════════════════════
#  БАЗА ДАННЫХ
# ════════════════════════════════════════════════════════════════════

_db = sqlite3.connect(DB_PATH, check_same_thread=False)
_db.row_factory = sqlite3.Row


def init_db() -> None:
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
        CREATE TABLE IF NOT EXISTS dungeon_runs (
            user_id INTEGER PRIMARY KEY,
            dkey TEXT NOT NULL,
            room INTEGER NOT NULL,
            hp INTEGER NOT NULL
        );
        """
    )
    _db.commit()


def q1(sql: str, args: tuple = ()):
    return _db.execute(sql, args).fetchone()


def qa(sql: str, args: tuple = ()):
    return _db.execute(sql, args).fetchall()


def ex(sql: str, args: tuple = ()):
    cur = _db.execute(sql, args)
    _db.commit()
    return cur


def get_player(uid: int):
    return q1("SELECT * FROM players WHERE user_id=?", (uid,))


def create_player(uid: int, username: Optional[str], name: str) -> None:
    s = BASE_STATS
    ex(
        "INSERT OR IGNORE INTO players (user_id, username, name, chips, points, hp, atk, defense, spd, crit, created) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (uid, username, name, START_CHIPS, START_POINTS,
         s["hp"], s["atk"], s["defense"], s["spd"], s["crit"], time.time()),
    )


def get_run(uid: int):
    return q1("SELECT * FROM dungeon_runs WHERE user_id=?", (uid,))


def in_run(uid: int) -> bool:
    return get_run(uid) is not None


def notify(uid: int, text: str) -> None:
    ex("INSERT INTO notifications (user_id, text, ts) VALUES (?,?,?)", (uid, text, time.time()))


def apply_result(uid: int, *, chips: int = 0, xp: int = 0, win: Optional[bool] = None, pvp: bool = False):
    """Начисляет награду и обрабатывает уровни. Возвращает (уровень, сколько уровней взято)."""
    p = get_player(uid)
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


def lvl_text(lvl: int, ups: int) -> str:
    if not ups:
        return ""
    return (
        f"\n🎉 <b>Новый уровень: {lvl}!</b> "
        f"+{ups * LEVEL_BONUS['hp']} HP, +{ups * LEVEL_BONUS['atk']} ATK, "
        f"+{ups * LEVEL_BONUS['defense']} DEF, +{ups * POINTS_PER_LEVEL} очк. прокачки"
    )


# ════════════════════════════════════════════════════════════════════
#  ФАБРИКИ БОЙЦОВ
# ════════════════════════════════════════════════════════════════════

def player_fighter(p, hp: Optional[int] = None) -> Fighter:
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


def bot_fighter(b: dict) -> Fighter:
    return Fighter(name=b["name"], max_hp=b["hp"], hp=b["hp"], atk=b["atk"], df=b["df"],
                   spd=b["spd"], crit=b["crit"], weapon=b["weapon"], armor=b["armor"])


def dungeon_enemy(dkey: str, room: int) -> Fighter:
    d = DUNGEONS[dkey]
    scale = d["mult"] * (1 + DUNGEON_ROOM_SCALE * (room - 1))
    boss = room == d["rooms"]
    if boss:
        scale *= DUNGEON_BOSS_SCALE
    hp = round(90 * scale)
    return Fighter(
        name=d["mobs"][room - 1],
        max_hp=hp,
        hp=hp,
        atk=round(11 * scale),
        df=round(4 * scale),
        spd=round(9 + room * d["mult"]),
        crit=min(5 + room, 25),
        weapon="hammer" if boss else DUNGEON_WEAPON_CYCLE[(room - 1) % len(DUNGEON_WEAPON_CYCLE)],
        armor="medium" if boss else "none",
    )


def stats_line(f: Fighter) -> str:
    return f"❤️{f.max_hp} ⚔️{f.atk} 🛡{f.df} 💨{f.spd} 🎯{f.crit}%"


# ════════════════════════════════════════════════════════════════════
#  UI-ХЕЛПЕРЫ И ЭКРАНЫ
# ════════════════════════════════════════════════════════════════════

def ikb(*rows) -> InlineKeyboardMarkup:
    """ikb([("текст", "data"), ...], [...])"""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=d) for t, d in row] for row in rows]
    )


async def safe_edit(cb: CallbackQuery, text: str, markup: Optional[InlineKeyboardMarkup] = None) -> None:
    try:
        await cb.message.edit_text(text[:4090], reply_markup=markup)
    except TelegramBadRequest as e:
        if "not modified" not in str(e):
            await cb.message.answer(text[:4090], reply_markup=markup)


# ── PvE ─────────────────────────────────────────────────────────────

def pve_screen():
    lines = ["⚔️ <b>PvE — арена ботов</b>",
             "Победа даёт фишки и опыт. Риска нет: HP восстанавливается после боя.", ""]
    rows = []
    for i, b in enumerate(BOTS):
        f = bot_fighter(b)
        w = WEAPONS[b["weapon"]]
        lines.append(f"<b>{i + 1}. {b['name']}</b> {w['emoji']}\n"
                     f"    {stats_line(f)}\n    награда: {b['chips']}💰 + {b['xp']} XP")
        rows.append([(f"{i + 1}. {b['name']} · {b['chips']}💰", f"pve:{i}")])
    return "\n".join(lines), ikb(*rows)


# ── Персонаж ────────────────────────────────────────────────────────

def char_screen(uid: int):
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
        f"🎯 Крит: <b>{f.crit}%</b> (×2 урона)",
        "",
        f"{w['emoji']} Оружие: <b>{w['name']}</b> — {w['spec']}",
        f"    {w['desc']}",
        f"    шанс {f.spec_chance}% · урон спец-атаки ×{f.spec_mult:.1f} · откат {f.spec_cd} хода",
        f"{a['emoji']} Броня: <b>{a['name']}</b> — {a['desc']}",
    ]
    rows = []
    if p["points"] > 0:
        lines.append(f"\n🎯 Свободных очков прокачки: <b>{p['points']}</b>")
        rows = [
            [(f"❤️ HP +{POINT_VALUE['hp']}", "up:hp"), (f"⚔️ ATK +{POINT_VALUE['atk']}", "up:atk")],
            [(f"🛡 DEF +{POINT_VALUE['defense']}", "up:defense"), (f"💨 SPD +{POINT_VALUE['spd']}", "up:spd")],
            [(f"🎯 Крит +{POINT_VALUE['crit']}%", "up:crit")],
        ]
    return "\n".join(lines), (ikb(*rows) if rows else None)


# ── Магазин ─────────────────────────────────────────────────────────

def shop_screen(uid: int, page: str = "w"):
    p = get_player(uid)
    is_w = page == "w"
    table = WEAPONS if is_w else ARMORS
    owned = set(p["weapons_owned" if is_w else "armors_owned"].split(","))
    equipped = p["weapon" if is_w else "armor"]

    lines = [f"🏪 <b>Магазин — {'оружие' if is_w else 'броня'}</b>",
             f"💰 Фишки: <b>{p['chips']}</b>", ""]
    rows = [[("⚔️ Оружие" + (" •" if is_w else ""), "shop:w"),
             ("🛡 Броня" + ("" if is_w else " •"), "shop:a")]]
    for key, it in table.items():
        if is_w:
            lines.append(f"{it['emoji']} <b>{it['name']}</b> — {it['spec']} (шанс {it['chance']}%)\n    {it['desc']}")
        else:
            lines.append(f"{it['emoji']} <b>{it['name']}</b> — DEF +{it['df']}, HP +{it['hp']}\n    {it['desc']}")
        if key == equipped:
            label = "✅ надето"
        elif key in owned:
            label = "🎒 надеть"
        else:
            label = f"{it['price']}💰"
        rows.append([(f"{it['emoji']} {it['name']} · {label}", f"buy:{page}:{key}")])
    if in_run(uid):
        lines.append("\n🔒 Пока ты в подземелье, экипировку менять нельзя.")
    return "\n".join(lines), ikb(*rows)


# ── Топ ─────────────────────────────────────────────────────────────

def top_screen(uid: int) -> str:
    rows = qa("SELECT user_id, name, level, wins, pvp_wins FROM players "
              "ORDER BY wins DESC, level DESC, user_id LIMIT 10")
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Топ бойцов по победам</b>", ""]
    for i, r in enumerate(rows):
        mark = medals[i] if i < 3 else f"{i + 1}."
        you = " ← ты" if r["user_id"] == uid else ""
        lines.append(f"{mark} <b>{esc(r['name'])}</b> — {r['wins']} поб. (PvP: {r['pvp_wins']}) · ур. {r['level']}{you}")
    me = get_player(uid)
    if me and all(r["user_id"] != uid for r in rows):
        rank = q1("SELECT COUNT(*) AS c FROM players WHERE wins > ?", (me["wins"],))["c"] + 1
        lines += ["…", f"{rank}. <b>{esc(me['name'])}</b> — {me['wins']} поб. · ур. {me['level']} ← ты"]
    return "\n".join(lines)


# ── PvP ─────────────────────────────────────────────────────────────

def pvp_screen():
    text = ("🤺 <b>PvP — арена игроков</b>\n\n"
            "Бой считается сразу, по текущим билдам обоих. Соперник узнает результат, "
            "когда зайдёт в бота.\n\n"
            "🏆 Победа: фишки и опыт (зависят от уровня соперника)\n"
            "💀 Поражение: небольшой опыт\n"
            "🛡 Защитился — тоже награда!")
    kb = ikb(
        [("🎲 Случайный соперник", "pvp:rand")],
        [("📋 Список соперников", "pvp:list")],
        [("🔎 Вызвать по нику / ID", "pvp:find")],
    )
    return text, kb


def pvp_list_screen(uid: int):
    me = get_player(uid)
    rows = qa("SELECT user_id, name, level, wins FROM players WHERE user_id != ? "
              "ORDER BY ABS(level - ?), wins DESC LIMIT 8", (uid, me["level"]))
    if not rows:
        return "Пока других бойцов нет. Позови друзей или потренируйся в PvE!", ikb([("⬅️ Назад", "pvp:menu")])
    kb_rows = [[(f"{r['name'][:16]} · ур.{r['level']} · 🏆{r['wins']}", f"pvp:f:{r['user_id']}")] for r in rows]
    kb_rows.append([("⬅️ Назад", "pvp:menu")])
    return "📋 <b>Соперники рядом с твоим уровнем:</b>", ikb(*kb_rows)


def pick_random_opponent(uid: int, level: int) -> Optional[int]:
    rows = qa("SELECT user_id FROM players WHERE user_id != ? ORDER BY ABS(level - ?), RANDOM() LIMIT 6",
              (uid, level))
    return random.choice(rows)["user_id"] if rows else None


def run_pvp(aid: int, did: int):
    """Проводит PvP-бой. Возвращает (текст, клавиатура)."""
    back = ikb([("🎲 Ещё раз", "pvp:rand"), ("🤺 В меню PvP", "pvp:menu")])
    a, d = get_player(aid), get_player(did)
    if not a or not d:
        return "Боец не найден.", back
    if aid == did:
        return "🤨 Нельзя драться с самим собой.", back
    now = time.time()
    wait = PVP_COOLDOWN - (now - a["last_pvp"])
    if wait > 0:
        return f"⏳ Отдышись: следующий бой через {int(wait) + 1} с.", back
    ex("UPDATE players SET last_pvp=? WHERE user_id=?", (now, aid))

    fa, fd = player_fighter(a), player_fighter(d)
    winner, blocks = simulate(fa, fd)

    recent = q1("SELECT COUNT(*) AS c FROM pvp_log WHERE attacker=? AND defender=? AND ts>?",
                (aid, did, now - 3600))["c"]
    ex("INSERT INTO pvp_log (attacker, defender, ts) VALUES (?,?,?)", (aid, did, now))
    scale = 1.0 if recent < PVP_FARM_LIMIT else 0.25
    if d["level"] <= a["level"] - 5:
        scale *= 0.5

    head = f"🤺 <b>{fa.name}</b> (ур. {a['level']}) vs <b>{fd.name}</b> (ур. {d['level']})"
    an, dn = esc(a["name"]), esc(d["name"])

    if winner is fa:
        chips = int((30 + 8 * d["level"]) * scale)
        xp = int((30 + 5 * d["level"]) * scale)
        lvl, ups = apply_result(aid, chips=chips, xp=xp, win=True, pvp=True)
        foot = f"🏆 <b>Победа!</b> +{chips}💰 +{xp} XP" + lvl_text(lvl, ups)
        if scale < 1:
            foot += "\n<i>Награда снижена: слишком слабый или слишком часто битый соперник.</i>"
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


# ── Данжи ───────────────────────────────────────────────────────────

def dg_list_screen(uid: int):
    if in_run(uid):
        return dg_run_screen(uid)
    lines = ["🏚 <b>Подземелья</b>",
             "Платишь вход и идёшь по комнатам подряд. <b>HP между боями не восстанавливается.</b> "
             "Погиб или сбежал — вход и всё потеряно. Прошёл — крупный куш.", ""]
    rows = []
    for key, d in DUNGEONS.items():
        lines.append(f"{d['emoji']} <b>{d['name']}</b> — {d['rooms']} комн. · вход {d['fee']}💰 · "
                     f"приз +{d['prize']}💰 · монстры ×{d['mult']}")
        rows.append([(f"{d['emoji']} {d['name']} · {d['fee']}💰", f"dg:i:{key}")])
    return "\n".join(lines), ikb(*rows)


def dg_info_screen(key: str):
    d = DUNGEONS[key]
    text = (f"{d['emoji']} <b>{d['name']}</b>\n\n"
            f"Комнат: {d['rooms']} (в последней — босс)\n"
            f"Вход: {d['fee']}💰\n"
            f"Награда за прохождение: +{d['prize']}💰 и +{d['prize'] // 4} XP\n"
            f"Сила монстров: ×{d['mult']}\n\n"
            "Восстановления HP между комнатами нет. Смерть или побег = потеря входа и награды.")
    return text, ikb([("🚪 Войти", f"dg:enter:{key}")], [("⬅️ Назад", "dg:list")])


def dg_run_screen(uid: int, prefix: str = ""):
    run, p = get_run(uid), get_player(uid)
    d = DUNGEONS[run["dkey"]]
    me = player_fighter(p, hp=run["hp"])
    e = dungeon_enemy(run["dkey"], run["room"])
    boss = " 👹 <b>БОСС</b>" if run["room"] == d["rooms"] else ""
    w = WEAPONS[e.weapon]
    text = (f"{prefix}{d['emoji']} <b>{d['name']}</b> — комната {run['room']}/{d['rooms']}\n"
            f"❤️ Твоё HP: <b>{me.hp}/{me.max_hp}</b> (не восстанавливается)\n\n"
            f"Впереди{boss}: <b>{e.name}</b> {w['emoji']}\n{stats_line(e)}")
    return text, ikb([("⚔️ В бой!", "dg:fight")], [("🏃 Сбежать", "dg:flee")])


# ════════════════════════════════════════════════════════════════════
#  ХЕНДЛЕРЫ
# ════════════════════════════════════════════════════════════════════

router = Router()
router.message.filter(F.chat.type == "private")


class Reg(StatesGroup):
    name = State()


class PvpFind(StatesGroup):
    target = State()


HELP_TEXT = (
    "⚔️ <b>Арена Дуэлянтов</b>\n\n"
    "• <b>PvE</b> — 5 ботов нарастающей сложности\n"
    "• <b>PvP</b> — бои с другими игроками (результат приходит, когда соперник заходит)\n"
    "• <b>Данжи</b> — 3 подземелья без восстановления HP\n"
    "• <b>Магазин</b> — оружие со спец-атаками и броня\n"
    "• <b>Персонаж</b> — распредели очки прокачки\n\n"
    "Бой идёт автоматически: побеждает лучший билд. Команды: /start, /menu, /help"
)


async def flush_notifications(m: Message) -> None:
    rows = qa("SELECT id, text FROM notifications WHERE user_id=? AND seen=0 ORDER BY id LIMIT 15",
              (m.from_user.id,))
    if not rows:
        return
    ids = [r["id"] for r in rows]
    ex(f"UPDATE notifications SET seen=1 WHERE id IN ({','.join('?' * len(ids))})", tuple(ids))
    await m.answer("📬 <b>Пока тебя не было:</b>\n\n" + "\n\n".join(r["text"] for r in rows))


def touch_username(m: Message) -> None:
    ex("UPDATE players SET username=? WHERE user_id=?", (m.from_user.username, m.from_user.id))


# ── /start, /help, /menu, регистрация ──────────────────────────────

@router.message(CommandStart())
async def cmd_start(m: Message, state: FSMContext):
    await state.clear()
    p = get_player(m.from_user.id)
    if p:
        touch_username(m)
        await m.answer(f"С возвращением, <b>{esc(p['name'])}</b>! Арена ждёт 👇", reply_markup=MENU_KB)
        await flush_notifications(m)
        return
    await state.set_state(Reg.name)
    await m.answer(
        "⚔️ <b>Добро пожаловать на Арену Дуэлянтов!</b>\n\n"
        "Здесь ты создашь бойца, прокачаешь его, купишь оружие и броню, "
        "победишь ботов, других игроков и пройдёшь подземелья.\n\n"
        "Как зовут твоего бойца? (2–16 символов)",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Command("help"))
async def cmd_help(m: Message):
    await m.answer(HELP_TEXT, reply_markup=MENU_KB if get_player(m.from_user.id) else None)


@router.message(Command("menu"))
async def cmd_menu(m: Message, state: FSMContext):
    await state.clear()
    if not get_player(m.from_user.id):
        return await m.answer("Сначала отправь /start и создай бойца.")
    await m.answer("Главное меню 👇", reply_markup=MENU_KB)
    await flush_notifications(m)


@router.message(Reg.name, F.text)
async def reg_name(m: Message, state: FSMContext):
    name = " ".join(m.text.split())
    if not 2 <= len(name) <= 16 or name.startswith("/"):
        return await m.answer("Имя должно быть от 2 до 16 символов. Попробуй ещё раз:")
    create_player(m.from_user.id, m.from_user.username, name)
    await state.clear()
    await m.answer(
        f"Боец <b>{esc(name)}</b> создан! 🎉\n\n"
        f"Тебе выдано {START_CHIPS}💰 и {START_POINTS} очков прокачки — "
        f"распредели их в разделе «{BTN_CHAR}», а потом отправляйся в PvE.",
        reply_markup=MENU_KB,
    )


# ── Ввод цели для PvP ──────────────────────────────────────────────

@router.message(PvpFind.target, F.text)
async def pvp_target(m: Message, state: FSMContext):
    if m.text in MENU_TEXTS:
        return await menu_dispatch(m, state)
    await state.clear()
    key = m.text.strip().lstrip("@")
    row = None
    if key.isdigit():
        row = q1("SELECT user_id FROM players WHERE user_id=?", (int(key),))
    if not row:
        row = q1("SELECT user_id FROM players WHERE LOWER(username)=LOWER(?) OR LOWER(name)=LOWER(?) LIMIT 1",
                 (key, key))
    if not row:
        return await m.answer("Боец не найден. Проверь ник/ID (игрок должен быть зарегистрирован в боте).")
    text, kb = run_pvp(m.from_user.id, row["user_id"])
    await m.answer(text, reply_markup=kb)


# ── Главное меню (reply-кнопки) ────────────────────────────────────

async def show_pve(m: Message):
    t, k = pve_screen()
    await m.answer(t, reply_markup=k)


async def show_pvp(m: Message):
    t, k = pvp_screen()
    await m.answer(t, reply_markup=k)


async def show_dungeons(m: Message):
    t, k = dg_list_screen(m.from_user.id)
    await m.answer(t, reply_markup=k)


async def show_char(m: Message):
    t, k = char_screen(m.from_user.id)
    await m.answer(t, reply_markup=k)


async def show_shop(m: Message):
    t, k = shop_screen(m.from_user.id, "w")
    await m.answer(t, reply_markup=k)


async def show_top(m: Message):
    await m.answer(top_screen(m.from_user.id))


MENU_HANDLERS = {
    BTN_PVE: show_pve,
    BTN_PVP: show_pvp,
    BTN_DG: show_dungeons,
    BTN_CHAR: show_char,
    BTN_SHOP: show_shop,
    BTN_TOP: show_top,
}


async def menu_dispatch(m: Message, state: FSMContext):
    await state.clear()
    if not get_player(m.from_user.id):
        return await m.answer("Сначала отправь /start и создай бойца.")
    touch_username(m)
    await flush_notifications(m)
    await MENU_HANDLERS[m.text](m)


@router.message(F.text.in_(MENU_TEXTS))
async def on_menu(m: Message, state: FSMContext):
    await menu_dispatch(m, state)


# ── Инлайн-колбэки ─────────────────────────────────────────────────

def cb_player(cb: CallbackQuery):
    return get_player(cb.from_user.id)


@router.callback_query(F.data == "pve:list")
async def cb_pve_list(cb: CallbackQuery):
    if not cb_player(cb):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = pve_screen()
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^pve:\d+$"))
async def cb_pve_fight(cb: CallbackQuery):
    uid = cb.from_user.id
    p = get_player(uid)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    idx = int(cb.data.split(":")[1])
    if not 0 <= idx < len(BOTS):
        return await cb.answer()
    bd = BOTS[idx]
    a, b = player_fighter(p), bot_fighter(bd)
    winner, blocks = simulate(a, b)
    head = f"⚔️ <b>{a.name}</b> vs <b>{b.name}</b>"
    if winner is a:
        lvl, ups = apply_result(uid, chips=bd["chips"], xp=bd["xp"], win=True)
        foot = f"🏆 <b>Победа!</b> +{bd['chips']}💰 +{bd['xp']} XP" + lvl_text(lvl, ups)
    else:
        lvl, ups = apply_result(uid, xp=5, win=False)
        foot = "💀 <b>Поражение.</b> +5 XP за храбрость. Прокачайся, купи снарягу и возвращайся!" + lvl_text(lvl, ups)
    kb = ikb([("🔁 Ещё раз", f"pve:{idx}")], [("📋 К списку ботов", "pve:list")])
    await safe_edit(cb, render_battle(blocks, head, foot), kb)
    await cb.answer()


# ── Персонаж: прокачка ─────────────────────────────────────────────

@router.callback_query(F.data.regexp(r"^up:(hp|atk|defense|spd|crit)$"))
async def cb_upgrade(cb: CallbackQuery):
    uid = cb.from_user.id
    p = get_player(uid)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    stat = cb.data.split(":")[1]           # только значения из regexp — безопасно для SQL
    if p["points"] <= 0:
        return await cb.answer("Нет свободных очков", show_alert=True)
    if stat == "crit" and p["crit"] >= CRIT_CAP:
        return await cb.answer(f"Крит уже на максимуме ({CRIT_CAP}%)", show_alert=True)
    ex(f"UPDATE players SET {stat}={stat}+?, points=points-1 WHERE user_id=?", (POINT_VALUE[stat], uid))
    t, k = char_screen(uid)
    await safe_edit(cb, t, k)
    await cb.answer("Прокачано!")


# ── Магазин ────────────────────────────────────────────────────────

@router.callback_query(F.data.regexp(r"^shop:[wa]$"))
async def cb_shop_page(cb: CallbackQuery):
    if not cb_player(cb):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = shop_screen(cb.from_user.id, cb.data.split(":")[1])
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^buy:[wa]:\w+$"))
async def cb_buy(cb: CallbackQuery):
    uid = cb.from_user.id
    p = get_player(uid)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    _, kind, key = cb.data.split(":")
    table = WEAPONS if kind == "w" else ARMORS
    if key not in table:
        return await cb.answer()
    if in_run(uid):
        return await cb.answer("Пока ты в подземелье, экипировку менять нельзя!", show_alert=True)
    owned_col = "weapons_owned" if kind == "w" else "armors_owned"
    eq_col = "weapon" if kind == "w" else "armor"
    owned = p[owned_col].split(",")
    item = table[key]

    if key in owned:
        ex(f"UPDATE players SET {eq_col}=? WHERE user_id=?", (key, uid))
        toast = f"Надето: {item['name']}"
    elif p["chips"] >= item["price"]:
        ex(f"UPDATE players SET chips=chips-?, {owned_col}=?, {eq_col}=? WHERE user_id=?",
           (item["price"], ",".join(owned + [key]), key, uid))
        toast = f"Куплено и надето: {item['name']}"
    else:
        return await cb.answer(f"Не хватает фишек: нужно {item['price']}💰", show_alert=True)

    t, k = shop_screen(uid, kind)
    await safe_edit(cb, t, k)
    await cb.answer(toast)


# ── Топ / PvP ──────────────────────────────────────────────────────

@router.callback_query(F.data == "pvp:menu")
async def cb_pvp_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    if not cb_player(cb):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = pvp_screen()
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data == "pvp:list")
async def cb_pvp_list(cb: CallbackQuery):
    if not cb_player(cb):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = pvp_list_screen(cb.from_user.id)
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data == "pvp:find")
async def cb_pvp_find(cb: CallbackQuery, state: FSMContext):
    if not cb_player(cb):
        return await cb.answer("Сначала /start", show_alert=True)
    await state.set_state(PvpFind.target)
    await cb.message.answer("🔎 Отправь @username, Telegram-ID или имя бойца, которого хочешь вызвать.\n"
                            "(Или нажми любую кнопку меню для отмены.)")
    await cb.answer()


@router.callback_query(F.data == "pvp:rand")
async def cb_pvp_rand(cb: CallbackQuery):
    uid = cb.from_user.id
    p = get_player(uid)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    oid = pick_random_opponent(uid, p["level"])
    if oid is None:
        await safe_edit(cb, "Пока других бойцов нет. Позови друзей или потренируйся в PvE!",
                        ikb([("⬅️ Назад", "pvp:menu")]))
        return await cb.answer()
    text, kb = run_pvp(uid, oid)
    await safe_edit(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^pvp:f:\d+$"))
async def cb_pvp_fight(cb: CallbackQuery):
    if not cb_player(cb):
        return await cb.answer("Сначала /start", show_alert=True)
    text, kb = run_pvp(cb.from_user.id, int(cb.data.split(":")[2]))
    await safe_edit(cb, text, kb)
    await cb.answer()


# ── Данжи ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "dg:list")
async def cb_dg_list(cb: CallbackQuery):
    if not cb_player(cb):
        return await cb.answer("Сначала /start", show_alert=True)
    t, k = dg_list_screen(cb.from_user.id)
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^dg:i:\w+$"))
async def cb_dg_info(cb: CallbackQuery):
    if not cb_player(cb):
        return await cb.answer("Сначала /start", show_alert=True)
    key = cb.data.split(":")[2]
    if key not in DUNGEONS:
        return await cb.answer()
    if in_run(cb.from_user.id):
        t, k = dg_run_screen(cb.from_user.id)
    else:
        t, k = dg_info_screen(key)
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^dg:enter:\w+$"))
async def cb_dg_enter(cb: CallbackQuery):
    uid = cb.from_user.id
    p = get_player(uid)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    key = cb.data.split(":")[2]
    if key not in DUNGEONS:
        return await cb.answer()
    if in_run(uid):
        t, k = dg_run_screen(uid)
        await safe_edit(cb, t, k)
        return await cb.answer("Ты уже в подземелье!")
    d = DUNGEONS[key]
    if p["chips"] < d["fee"]:
        return await cb.answer(f"Не хватает фишек: вход {d['fee']}💰", show_alert=True)
    max_hp = player_fighter(p).max_hp
    ex("UPDATE players SET chips=chips-? WHERE user_id=?", (d["fee"], uid))
    ex("INSERT INTO dungeon_runs (user_id, dkey, room, hp) VALUES (?,?,?,?)", (uid, key, 1, max_hp))
    t, k = dg_run_screen(uid, prefix=f"🚪 Ты заплатил {d['fee']}💰 и вошёл внутрь…\n\n")
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data == "dg:fight")
async def cb_dg_fight(cb: CallbackQuery):
    uid = cb.from_user.id
    p, run = get_player(uid), get_run(uid)
    if not p:
        return await cb.answer("Сначала /start", show_alert=True)
    if not run:
        t, k = dg_list_screen(uid)
        await safe_edit(cb, t, k)
        return await cb.answer("Ты сейчас не в подземелье.")

    d = DUNGEONS[run["dkey"]]
    room = run["room"]
    a = player_fighter(p, hp=run["hp"])
    b = dungeon_enemy(run["dkey"], room)
    winner, blocks = simulate(a, b)
    head = f"{d['emoji']} <b>{d['name']}</b> · комната {room}/{d['rooms']}\n<b>{a.name}</b> vs <b>{b.name}</b>"

    if winner is a:
        if room >= d["rooms"]:
            xp = d["prize"] // 4
            ex("DELETE FROM dungeon_runs WHERE user_id=?", (uid,))
            lvl, ups = apply_result(uid, chips=d["prize"], xp=xp, win=True)
            foot = (f"🎉 <b>{d['name']} пройден!</b> +{d['prize']}💰 +{xp} XP" + lvl_text(lvl, ups))
            kb = ikb([("🏚 К подземельям", "dg:list")])
        else:
            ex("UPDATE dungeon_runs SET room=room+1, hp=? WHERE user_id=?", (max(1, a.hp), uid))
            nxt = dungeon_enemy(run["dkey"], room + 1)
            boss = " 👹 БОСС" if room + 1 == d["rooms"] else ""
            foot = (f"✅ Комната зачищена! ❤️ {a.hp}/{a.max_hp}\n\n"
                    f"Дальше{boss}: <b>{nxt.name}</b>\n{stats_line(nxt)}")
            kb = ikb([("⚔️ Дальше", "dg:fight")], [("🏃 Сбежать", "dg:flee")])
    else:
        ex("DELETE FROM dungeon_runs WHERE user_id=?", (uid,))
        apply_result(uid, win=False)
        foot = (f"☠️ <b>Ты пал в комнате {room}.</b> Вход и награда потеряны.\n"
                "Прокачайся, экипируйся получше — и попробуй снова.")
        kb = ikb([("🏚 К подземельям", "dg:list")])

    await safe_edit(cb, render_battle(blocks, head, foot), kb)
    await cb.answer()


@router.callback_query(F.data == "dg:flee")
async def cb_dg_flee(cb: CallbackQuery):
    if not get_run(cb.from_user.id):
        t, k = dg_list_screen(cb.from_user.id)
        await safe_edit(cb, t, k)
        return await cb.answer()
    await safe_edit(
        cb,
        "🏃 Сбежать из подземелья?\n<b>Вход и весь прогресс забега будут потеряны.</b>",
        ikb([("Да, сбежать", "dg:flee2")], [("Остаться и драться", "dg:run")]),
    )
    await cb.answer()


@router.callback_query(F.data == "dg:run")
async def cb_dg_run(cb: CallbackQuery):
    if not get_run(cb.from_user.id):
        t, k = dg_list_screen(cb.from_user.id)
    else:
        t, k = dg_run_screen(cb.from_user.id)
    await safe_edit(cb, t, k)
    await cb.answer()


@router.callback_query(F.data == "dg:flee2")
async def cb_dg_flee2(cb: CallbackQuery):
    uid = cb.from_user.id
    if get_run(uid):
        ex("DELETE FROM dungeon_runs WHERE user_id=?", (uid,))
        await safe_edit(cb, "🏃 Ты сбежал из подземелья, потеряв вход. В другой раз повезёт больше!",
                        ikb([("🏚 К подземельям", "dg:list")]))
    else:
        t, k = dg_list_screen(uid)
        await safe_edit(cb, t, k)
    await cb.answer()


# ── Всё остальное ──────────────────────────────────────────────────

@router.message()
async def fallback(m: Message):
    if not get_player(m.from_user.id):
        return await m.answer("Отправь /start, чтобы создать бойца ⚔️")
    await m.answer("Пользуйся меню внизу 👇", reply_markup=MENU_KB)


# ════════════════════════════════════════════════════════════════════
#  ЗАПУСК
# ════════════════════════════════════════════════════════════════════

async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    token = "8996813076:AAGq74gyRRW5fMxvHaIE190_B-tmzXk8aNA"
    if not token:
        raise SystemExit("Задай переменную окружения BOT_TOKEN (токен от @BotFather).")
    init_db()
    bot = Bot(token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать / вернуться на арену"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="help", description="Правила и подсказки"),
    ])
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
