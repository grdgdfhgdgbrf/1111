# -*- coding: utf-8 -*-
"""
🌾 Telegram-бот «Игра Ферма»
Стек: Python 3.10+, aiogram 3.x, SQLite (из стандартной библиотеки).

Запуск:
    pip install -r requirements.txt
    Linux/macOS:  export BOT_TOKEN="123456:ABC..."
    Windows:      set BOT_TOKEN=123456:ABC...
    python farm_bot.py

Токен берётся у @BotFather в Telegram (/newbot).
"""

import asyncio
import html
import os
import random
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# ─────────────────────────── НАСТРОЙКИ ───────────────────────────
BOT_TOKEN = os.getenv("8996813076:AAGq74gyRRW5fMxvHaIE190_B-tmzXk8aNA")
DB_PATH = os.getenv("DB_PATH", "farm.db")

START_COINS = 100          # стартовый капитал
START_SLOTS = 3            # грядок на 1 уровне
MAX_SLOTS = 9              # максимум грядок
HARVEST_MIN, HARVEST_MAX = 2, 3   # сколько плодов даёт одна грядка


@dataclass(frozen=True)
class Crop:
    key: str
    name: str
    emoji: str
    seed_price: int
    grow_sec: int
    sell_price: int
    xp: int
    level: int          # с какого уровня доступна


CROPS = {c.key: c for c in [
    Crop("wheat",      "Пшеница",     "🌾", 10,    60,   25,   5, 1),
    Crop("carrot",     "Морковь",     "🥕", 25,   180,   60,  12, 1),
    Crop("corn",       "Кукуруза",    "🌽", 60,   600,  150,  30, 2),
    Crop("pumpkin",    "Тыква",       "🎃", 150, 1800,  400,  80, 3),
    Crop("strawberry", "Клубника",    "🍓", 300, 3600,  850, 150, 4),
    Crop("sunflower",  "Подсолнух",   "🌻", 700, 7200, 2100, 300, 5),
]}


# ─────────────────────────── БАЗА ДАННЫХ ───────────────────────────
@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id   INTEGER PRIMARY KEY,
            name      TEXT,
            coins     INTEGER NOT NULL DEFAULT 0,
            xp        INTEGER NOT NULL DEFAULT 0,
            level     INTEGER NOT NULL DEFAULT 1,
            harvested INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS plots (
            user_id    INTEGER NOT NULL,
            slot       INTEGER NOT NULL,
            crop       TEXT,
            planted_at INTEGER,
            PRIMARY KEY (user_id, slot)
        );
        CREATE TABLE IF NOT EXISTS inventory (
            user_id INTEGER NOT NULL,
            item    TEXT    NOT NULL,
            kind    TEXT    NOT NULL,      -- 'seed' | 'crop'
            amount  INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, item, kind)
        );
        """)


def ensure_user(user_id: int, name: str) -> bool:
    """Регистрирует игрока. Возвращает True, если он новый."""
    with db() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO users (user_id, name, coins) VALUES (?, ?, ?)",
            (user_id, name, START_COINS),
        )
        is_new = cur.rowcount == 1
        if is_new:
            conn.execute(
                "INSERT INTO inventory (user_id, item, kind, amount) VALUES (?, 'wheat', 'seed', 3)",
                (user_id,),
            )
        else:
            conn.execute("UPDATE users SET name = ? WHERE user_id = ?", (name, user_id))
    return is_new


def get_user(user_id: int):
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:                      # игрок нажал кнопку до /start
        ensure_user(user_id, "Фермер")
        with db() as conn:
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return row


def add_coins(user_id: int, delta: int) -> None:
    with db() as conn:
        conn.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (delta, user_id))


def xp_needed(level: int) -> int:
    return level * 100


def add_xp(user_id: int, amount: int) -> int:
    """Начисляет опыт, поднимает уровень. Возвращает новый уровень."""
    u = get_user(user_id)
    xp, level = u["xp"] + amount, u["level"]
    while xp >= xp_needed(level):
        xp -= xp_needed(level)
        level += 1
    with db() as conn:
        conn.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ?", (xp, level, user_id))
    return level


def slots_count(level: int) -> int:
    return min(MAX_SLOTS, START_SLOTS + level - 1)


def inv_change(conn, user_id: int, item: str, kind: str, delta: int) -> None:
    conn.execute(
        "INSERT INTO inventory (user_id, item, kind, amount) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(user_id, item, kind) DO UPDATE SET amount = amount + excluded.amount",
        (user_id, item, kind, delta),
    )


def inv_get(user_id: int, item: str, kind: str) -> int:
    with db() as conn:
        row = conn.execute(
            "SELECT amount FROM inventory WHERE user_id = ? AND item = ? AND kind = ?",
            (user_id, item, kind),
        ).fetchone()
    return row["amount"] if row else 0


def inv_all(user_id: int):
    with db() as conn:
        return conn.execute(
            "SELECT item, kind, amount FROM inventory WHERE user_id = ? AND amount > 0",
            (user_id,),
        ).fetchall()


def get_plots(user_id: int) -> dict:
    with db() as conn:
        rows = conn.execute(
            "SELECT slot, crop, planted_at FROM plots WHERE user_id = ?", (user_id,)
        ).fetchall()
    return {r["slot"]: r for r in rows}


# ─────────────────────────── ИГРОВЫЕ ДЕЙСТВИЯ ───────────────────────────
def fmt_time(sec: int) -> str:
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}ч {m}м"
    if m:
        return f"{m}м {s}с"
    return f"{s}с"


def do_plant(user_id: int, slot: int, crop_key: str):
    u = get_user(user_id)
    if slot >= slots_count(u["level"]):
        return False, f"🔒 Грядка откроется на {max(1, slot - 1)} уровне."
    plots = get_plots(user_id)
    if plots.get(slot) and plots[slot]["crop"]:
        return False, "🟫 Эта грядка уже занята."
    c = CROPS.get(crop_key)
    if c is None:
        return False, "Неизвестная культура."
    if inv_get(user_id, crop_key, "seed") <= 0:
        return False, "Нет таких семян — загляни в магазин 🛒"
    with db() as conn:
        inv_change(conn, user_id, crop_key, "seed", -1)
        conn.execute(
            "INSERT INTO plots (user_id, slot, crop, planted_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id, slot) DO UPDATE SET crop = excluded.crop, "
            "planted_at = excluded.planted_at",
            (user_id, slot, crop_key, int(time.time())),
        )
    return True, f"{c.emoji} Посажено: {c.name}. Созреет через {fmt_time(c.grow_sec)}."


def do_harvest(user_id: int, slot: int):
    now = int(time.time())
    plots = get_plots(user_id)
    p = plots.get(slot)
    if not p or not p["crop"]:
        return False, "Эта грядка пуста."
    c = CROPS[p["crop"]]
    left = c.grow_sec - (now - p["planted_at"])
    if left > 0:
        return False, f"{c.emoji} {c.name} ещё растёт: осталось {fmt_time(left)}."

    amount = random.randint(HARVEST_MIN, HARVEST_MAX)
    with db() as conn:
        conn.execute(
            "UPDATE plots SET crop = NULL, planted_at = NULL WHERE user_id = ? AND slot = ?",
            (user_id, slot),
        )
        inv_change(conn, user_id, c.key, "crop", amount)
        conn.execute("UPDATE users SET harvested = harvested + 1 WHERE user_id = ?", (user_id,))

    old_level = get_user(user_id)["level"]
    new_level = add_xp(user_id, c.xp)
    msg = f"✅ Собрано: {c.emoji} {c.name} ×{amount} (+{c.xp} XP)"
    if new_level > old_level:
        msg += f"\n🎉 Новый уровень — {new_level}!"
        if slots_count(new_level) > slots_count(old_level):
            msg += "\n🟫 Открыта новая грядка!"
    return True, msg


def do_buy(user_id: int, crop_key: str, n: int):
    u = get_user(user_id)
    c = CROPS.get(crop_key)
    if c is None:
        return False, "Неизвестная культура."
    if u["level"] < c.level:
        return False, f"🔒 {c.name} откроется на {c.level} уровне."
    cost = c.seed_price * n
    if u["coins"] < cost:
        return False, f"Не хватает монет: нужно {cost}🪙, а у тебя {u['coins']}🪙."
    with db() as conn:
        conn.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (cost, user_id))
        inv_change(conn, user_id, crop_key, "seed", n)
    return True, f"🛒 Куплено: {c.emoji} {c.name} ×{n} за {cost}🪙"


def do_sell(user_id: int, crop_key: str):
    c = CROPS.get(crop_key)
    if c is None:
        return False, "Неизвестная культура."
    amount = inv_get(user_id, crop_key, "crop")
    if amount <= 0:
        return False, "Нечего продавать."
    total = amount * c.sell_price
    with db() as conn:
        conn.execute(
            "UPDATE inventory SET amount = 0 WHERE user_id = ? AND item = ? AND kind = 'crop'",
            (user_id, crop_key),
        )
    add_coins(user_id, total)
    return True, f"💰 Продано: {c.emoji} {c.name} ×{amount} → +{total}🪙"


# ─────────────────────────── ЭКРАНЫ ───────────────────────────
def kb_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌱 Ферма", callback_data="farm"),
         InlineKeyboardButton(text="🛒 Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inv"),
         InlineKeyboardButton(text="👤 Профиль", callback_data="me")],
        [InlineKeyboardButton(text="🏆 Топ фермеров", callback_data="top")],
    ])


def screen_menu(user_id: int):
    u = get_user(user_id)
    text = (
        f"🌾 <b>Игра Ферма</b>\n\n"
        f"Кошелёк: <b>{u['coins']}🪙</b> · уровень <b>{u['level']}</b>\n\n"
        f"Покупай семена, сажай, собирай урожай и продавай его дороже. "
        f"Опыт даёт новые грядки.\n\nВыбирай раздел:"
    )
    return text, kb_menu()


def screen_farm(user_id: int):
    u = get_user(user_id)
    plots = get_plots(user_id)
    now = int(time.time())
    total = slots_count(u["level"])

    lines = [f"🌾 <b>Ферма</b> · уровень {u['level']} · {u['coins']}🪙 · грядок {total}/{MAX_SLOTS}", ""]
    rows, ready_any = [], False

    for slot in range(MAX_SLOTS):
        if slot >= total:
            lines.append(f"🔒 Грядка {slot + 1} — откроется на {slot - 1} уровне")
            continue
        p = plots.get(slot)
        if not p or not p["crop"]:
            lines.append(f"🟫 Грядка {slot + 1}: пусто")
            rows.append([InlineKeyboardButton(
                text=f"🌱 Грядка {slot + 1}: посадить", callback_data=f"plant:{slot}")])
            continue
        c = CROPS[p["crop"]]
        left = c.grow_sec - (now - p["planted_at"])
        if left > 0:
            lines.append(f"{c.emoji} Грядка {slot + 1}: {c.name} — ⏳ {fmt_time(left)}")
            rows.append([InlineKeyboardButton(
                text=f"⏳ Грядка {slot + 1}: {fmt_time(left)}", callback_data="noop")])
        else:
            ready_any = True
            lines.append(f"{c.emoji} Грядка {slot + 1}: {c.name} — ✅ готово!")
            rows.append([InlineKeyboardButton(
                text=f"✅ Собрать грядку {slot + 1}", callback_data=f"harvest:{slot}")])

    if ready_any:
        rows.append([InlineKeyboardButton(text="🧺 Собрать всё", callback_data="harvest_all")])
    rows.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="farm"),
                 InlineKeyboardButton(text="🛒 Магазин", callback_data="shop")])
    rows.append([InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inv"),
                 InlineKeyboardButton(text="◀️ Меню", callback_data="menu")])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


def screen_shop(user_id: int):
    u = get_user(user_id)
    lines = [f"🛒 <b>Магазин семян</b> · у тебя {u['coins']}🪙", ""]
    rows = []
    for c in CROPS.values():
        if u["level"] < c.level:
            lines.append(f"🔒 {c.emoji} {c.name} — с {c.level} уровня")
            continue
        lines.append(
            f"{c.emoji} <b>{c.name}</b> — семя {c.seed_price}🪙 · растёт {fmt_time(c.grow_sec)} · "
            f"продажа {c.sell_price}🪙 · +{c.xp} XP"
        )
        rows.append([
            InlineKeyboardButton(text=f"{c.emoji} ×1 — {c.seed_price}🪙", callback_data=f"buy:{c.key}:1"),
            InlineKeyboardButton(text=f"×5 — {c.seed_price * 5}🪙", callback_data=f"buy:{c.key}:5"),
            InlineKeyboardButton(text=f"×10 — {c.seed_price * 10}🪙", callback_data=f"buy:{c.key}:10"),
        ])
    rows.append([InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inv"),
                 InlineKeyboardButton(text="◀️ Меню", callback_data="menu")])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


def screen_inv(user_id: int):
    items = inv_all(user_id)
    seeds = [r for r in items if r["kind"] == "seed"]
    crops = [r for r in items if r["kind"] == "crop"]

    def fmt(rows_):
        return ", ".join(
            f"{CROPS[r['item']].emoji} {CROPS[r['item']].name} ×{r['amount']}" for r in rows_
        ) or "пусто"

    lines = ["🎒 <b>Инвентарь</b>", "", f"🌱 Семена: {fmt(seeds)}", "", f"🧺 Урожай: {fmt(crops)}"]
    rows = [[InlineKeyboardButton(
        text=f"💰 Продать {CROPS[r['item']].emoji} {CROPS[r['item']].name} ×{r['amount']} "
             f"→ {r['amount'] * CROPS[r['item']].sell_price}🪙",
        callback_data=f"sell:{r['item']}")] for r in crops]
    rows.append([InlineKeyboardButton(text="🛒 Магазин", callback_data="shop"),
                 InlineKeyboardButton(text="◀️ Меню", callback_data="menu")])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


def screen_me(user_id: int):
    u = get_user(user_id)
    need = xp_needed(u["level"])
    filled = min(10, int(10 * u["xp"] / need))
    bar = "▰" * filled + "▱" * (10 - filled)
    growing = sum(1 for p in get_plots(user_id).values() if p["crop"])
    text = (
        f"👤 <b>{html.escape(str(u['name'] or 'Фермер'))}</b>\n\n"
        f"Уровень: <b>{u['level']}</b>  {bar}  {u['xp']}/{need} XP\n"
        f"Монеты: <b>{u['coins']}🪙</b>\n"
        f"Грядки: {slots_count(u['level'])}/{MAX_SLOTS} · засажено сейчас: {growing}\n"
        f"Урожаев собрано: {u['harvested']}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌱 На ферму", callback_data="farm"),
         InlineKeyboardButton(text="◀️ Меню", callback_data="menu")],
    ])
    return text, kb


def screen_top(user_id: int):
    with db() as conn:
        rows_ = conn.execute(
            "SELECT name, level, xp, harvested FROM users ORDER BY level DESC, xp DESC LIMIT 10"
        ).fetchall()
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Топ фермеров</b>", ""]
    if not rows_:
        lines.append("Пока никого нет — стань первым!")
    for i, r in enumerate(rows_, 1):
        prefix = medals[i - 1] if i <= 3 else f"{i}."
        mark = " ← ты" if i == 1 and False else ""
        lines.append(
            f"{prefix} {html.escape(str(r['name'] or 'Фермер'))} — ур. {r['level']} "
            f"({r['xp']} XP, собрано {r['harvested']}){mark}"
        )
    lines.append("")
    lines.append("Свою статистику смотри в профиле 👤")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="me"),
         InlineKeyboardButton(text="◀️ Меню", callback_data="menu")],
    ])
    return "\n".join(lines), kb


# ─────────────────────────── ХЕНДЛЕРЫ ───────────────────────────
router = Router()


async def show(call: CallbackQuery, text: str, kb: InlineKeyboardMarkup) -> None:
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)


@router.message(CommandStart())
async def cmd_start(message: Message):
    is_new = ensure_user(message.from_user.id, message.from_user.full_name)
    name = html.escape(message.from_user.full_name)
    text = (
        (f"🌾 Привет, <b>{name}</b>!\n\n" if is_new else f"🌾 С возвращением, <b>{name}</b>!\n\n")
        + "Это игра-ферма: покупай семена, сажай их на грядки, собирай урожай и продавай дороже. "
        "За урожай капает опыт — он открывает новые грядки и культуры.\n\n"
        + f"Стартовый капитал: <b>{START_COINS}🪙</b>"
        + (" и 3 семечка пшеницы 🌾" if is_new else "")
        + "\n\nВыбирай раздел:"
    )
    await message.answer(text, reply_markup=kb_menu())


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "🌾 <b>Как играть</b>\n\n"
        "1. Загляни в 🛒 <b>магазин</b> и купи семена.\n"
        "2. На 🌱 <b>ферме</b> посади их на свободную грядку.\n"
        "3. Дождись созревания (кнопка «🔄 Обновить» покажет таймер).\n"
        "4. Собери урожай — он попадёт в 🎒 <b>инвентарь</b>.\n"
        "5. Продай урожай и купи семена подороже.\n\n"
        "Опыт за сбор поднимает уровень: +1 грядка за уровень (до 9) и новые культуры.\n\n"
        "Команды: /start — меню, /help — эта справка, /top — таблица лидеров."
    )
    await message.answer(text, reply_markup=kb_menu())


@router.message(Command("top"))
async def cmd_top(message: Message):
    get_user(message.from_user.id)
    text, kb = screen_top(message.from_user.id)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery):
    text, kb = screen_menu(call.from_user.id)
    await show(call, text, kb)
    await call.answer()


@router.callback_query(F.data == "farm")
async def cb_farm(call: CallbackQuery):
    text, kb = screen_farm(call.from_user.id)
    await show(call, text, kb)
    await call.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer("⏳ Урожай ещё растёт, заходи позже 😊", show_alert=False)


@router.callback_query(F.data.startswith("plant:"))
async def cb_plant(call: CallbackQuery):
    slot = int(call.data.split(":")[1])
    uid = call.from_user.id
    u = get_user(uid)

    rows = []
    for r in [i for i in inv_all(uid) if i["kind"] == "seed"]:
        c = CROPS[r["item"]]
        rows.append([InlineKeyboardButton(
            text=f"{c.emoji} {c.name} ×{r['amount']} · созреет за {fmt_time(c.grow_sec)}",
            callback_data=f"sow:{slot}:{c.key}")])
    if not rows:
        rows.append([InlineKeyboardButton(text="🛒 Купить семена", callback_data="shop")])
    rows.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="farm"),
                 InlineKeyboardButton(text="◀️ Меню", callback_data="menu")])

    text = (f"🟫 <b>Грядка {slot + 1}</b>: какие семена посадить?\n"
            f"Монет в кошельке: {u['coins']}🪙")
    await show(call, text, InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()


@router.callback_query(F.data.startswith("sow:"))
async def cb_sow(call: CallbackQuery):
    _, slot, key = call.data.split(":")
    ok, msg = do_plant(call.from_user.id, int(slot), key)
    if ok:
        text, kb = screen_farm(call.from_user.id)
        await show(call, text, kb)
        await call.answer(msg)
    else:
        await call.answer(msg, show_alert=True)


@router.callback_query(F.data.startswith("harvest:"))
async def cb_harvest(call: CallbackQuery):
    slot = int(call.data.split(":")[1])
    ok, msg = do_harvest(call.from_user.id, slot)
    if ok:
        text, kb = screen_farm(call.from_user.id)
        await show(call, text, kb)
        await call.answer(msg)
    else:
        await call.answer(msg, show_alert=True)


@router.callback_query(F.data == "harvest_all")
async def cb_harvest_all(call: CallbackQuery):
    uid = call.from_user.id
    u = get_user(uid)
    done, coins = [], 0
    for slot in range(slots_count(u["level"])):
        ok, msg = do_harvest(uid, slot)
        if ok:
            done.append(msg.splitlines()[0])
            coins += 1
    if not done:
        await call.answer("Пока нечего собирать 🌱", show_alert=True)
        return
    text, kb = screen_farm(uid)
    await show(call, f"🧺 Собрано грядок: {coins}\n\n" + text, kb)
    await call.answer("Урожай собран!")


@router.callback_query(F.data == "shop")
async def cb_shop(call: CallbackQuery):
    text, kb = screen_shop(call.from_user.id)
    await show(call, text, kb)
    await call.answer()


@router.callback_query(F.data.startswith("buy:"))
async def cb_buy(call: CallbackQuery):
    _, key, n = call.data.split(":")
    ok, msg = do_buy(call.from_user.id, key, int(n))
    if ok:
        text, kb = screen_shop(call.from_user.id)
        await show(call, text, kb)
        await call.answer(msg)
    else:
        await call.answer(msg, show_alert=True)


@router.callback_query(F.data == "inv")
async def cb_inv(call: CallbackQuery):
    text, kb = screen_inv(call.from_user.id)
    await show(call, text, kb)
    await call.answer()


@router.callback_query(F.data.startswith("sell:"))
async def cb_sell(call: CallbackQuery):
    key = call.data.split(":")[1]
    ok, msg = do_sell(call.from_user.id, key)
    if ok:
        text, kb = screen_inv(call.from_user.id)
        await show(call, text, kb)
        await call.answer(msg)
    else:
        await call.answer(msg, show_alert=True)


@router.callback_query(F.data == "me")
async def cb_me(call: CallbackQuery):
    text, kb = screen_me(call.from_user.id)
    await show(call, text, kb)
    await call.answer()


@router.callback_query(F.data == "top")
async def cb_top(call: CallbackQuery):
    text, kb = screen_top(call.from_user.id)
    await show(call, text, kb)
    await call.answer()


@router.message()
async def fallback(message: Message):
    await message.answer("🌾 Нажми /start — и вперёд на ферму!", reply_markup=kb_menu())


# ─────────────────────────── ЗАПУСК ───────────────────────────
async def main():
    if BOT_TOKEN.startswith("ВСТАВЬ"):
        print("⚠️  Сначала впиши токен: export BOT_TOKEN=... (или в переменную BOT_TOKEN)")
        return
    init_db()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    print("🌾 Бот-ферма запущен. Ctrl+C — остановить.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nОстановлено.")
