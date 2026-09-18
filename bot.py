# -*- coding: utf-8 -*-
"""
ГлифБот — простой игровой бот для Telegram (работает и в группах, и в ЛС).

Стек: Python 3.10+ | aiogram 3 | SQLite (aiosqlite)
Файл 1 из 2: bot.py           Файл 2 из 2: requirements.txt

Запуск:
    pip install -r requirements.txt
    Linux/macOS:  BOT_TOKEN="123:AA..." ADMIN_IDS="12345" python bot.py
    Windows:      set BOT_TOKEN=123:AA... && set ADMIN_IDS=12345 && python bot.py

Важно: в @BotFather выключи Group Privacy (/setprivacy -> Disable),
иначе в группах не будет работать игра на вводе текста (/guess).
"""

import asyncio
import html
import logging
import os
import random
import time

import aiosqlite
from aiogram import BaseMiddleware, Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("glyphbot")

# ============================== КОНФИГ ==============================
BOT_TOKEN = "8996813076:AAGq74gyRRW5fMxvHaIE190_B-tmzXk8aNA"
ADMIN_IDS = "5356400377"

START_BALANCE = 1000      # стартовый баланс
MIN_BET = 10              # минимальная ставка
MAX_BET = 50_000          # максимальная ставка
DAILY_BASE = 500          # база ежедневного бонуса
DAILY_STREAK_BONUS = 100  # прибавка за каждый день серии
WORK_MIN, WORK_MAX = 150, 400
WORK_CD = 3600            # кулдаун работы, сек
ROB_CD = 600              # кулдаун ограбления, сек
BANK_PERCENT = 3          # % в час на вклад
PET_CD = 4 * 3600         # доход питомца раз в 4 часа
PET_INCOME = 120          # монет с уровня питомца
PET_FEED_COST = 150       # цена корма
THROTTLE = 0.6            # антифлуд, сек
JACKPOT_CUT = 2           # % со ставки в банк чата
JACKPOT_MIN = 5000        # минимальный банк для розыгрыша

SHOP = {
    "shield": ("🛡 Щит от ограбления", 400),
    "clover": ("🍀 Клевер (+10% к выигрышу, одна игра)", 600),
    "food": ("🍖 Корм для питомца", PET_FEED_COST),
}

# ============================== БАЗА ==============================
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    balance     INTEGER NOT NULL DEFAULT 0,
    bank        INTEGER NOT NULL DEFAULT 0,
    bank_time   INTEGER NOT NULL DEFAULT 0,
    xp          INTEGER NOT NULL DEFAULT 0,
    level       INTEGER NOT NULL DEFAULT 1,
    streak      INTEGER NOT NULL DEFAULT 0,
    last_daily  INTEGER NOT NULL DEFAULT 0,
    last_work   INTEGER NOT NULL DEFAULT 0,
    last_rob    INTEGER NOT NULL DEFAULT 0,
    last_pet    INTEGER NOT NULL DEFAULT 0,
    pet_name    TEXT,
    pet_level   INTEGER NOT NULL DEFAULT 0,
    wins        INTEGER NOT NULL DEFAULT 0,
    losses      INTEGER NOT NULL DEFAULT 0,
    banned      INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS items (
    user_id INTEGER NOT NULL,
    item    TEXT NOT NULL,
    qty     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, item)
);
CREATE TABLE IF NOT EXISTS chats (
    chat_id  INTEGER PRIMARY KEY,
    games_on INTEGER NOT NULL DEFAULT 1,
    jackpot  INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS chat_players (
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (chat_id, user_id)
);
CREATE TABLE IF NOT EXISTS logs (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action  TEXT NOT NULL,
    amount  INTEGER NOT NULL,
    ts      INTEGER NOT NULL
);
"""

db = None


async def q(sql: str, params: tuple = ()):
    cur = await db.execute(sql, params)
    rows = await cur.fetchall()
    await cur.close()
    return rows


async def x(sql: str, params: tuple = ()):
    await db.execute(sql, params)
    await db.commit()


async def init_db():
    global db
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.executescript(SCHEMA)
    await db.commit()


# ============================ ХЕЛПЕРЫ ============================
def money(n) -> str:
    return f"{int(n):,}".replace(",", " ")


def uname(user) -> str:
    return html.escape(user.full_name or "игрок")


def fmt_time(seconds) -> str:
    seconds = max(0, int(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours} ч {minutes} мин"
    if minutes:
        return f"{minutes} мин {secs} с"
    return f"{secs} с"


async def get_user(user_id: int, username: str | None = None):
    rows = await q("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not rows:
        await x(
            "INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)",
            (user_id, username, START_BALANCE),
        )
        rows = await q("SELECT * FROM users WHERE user_id = ?", (user_id,))
    elif username and rows[0]["username"] != username:
        await x("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        rows = await q("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return rows[0]


async def get_balance(user_id: int) -> int:
    rows = await q("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    return rows[0]["balance"] if rows else 0


async def add_log(user_id: int, action: str, amount: int):
    await x(
        "INSERT INTO logs (user_id, action, amount, ts) VALUES (?, ?, ?, ?)",
        (user_id, action, amount, int(time.time())),
    )


async def get_chat(chat_id: int):
    rows = await q("SELECT * FROM chats WHERE chat_id = ?", (chat_id,))
    if not rows:
        await x("INSERT OR IGNORE INTO chats (chat_id) VALUES (?)", (chat_id,))
        rows = await q("SELECT * FROM chats WHERE chat_id = ?", (chat_id,))
    return rows[0]


async def add_xp(user_id: int, amount: int) -> int:
    """Начисляет опыт. Возвращает бонус монет, если поднялся уровень."""
    await x("UPDATE users SET xp = xp + ? WHERE user_id = ?", (amount, user_id))
    row = (await q("SELECT xp, level FROM users WHERE user_id = ?", (user_id,)))[0]
    new_level = 1 + row["xp"] // 100
    if new_level > row["level"]:
        bonus = (new_level - row["level"]) * 200
        await x(
            "UPDATE users SET level = ?, balance = balance + ? WHERE user_id = ?",
            (new_level, bonus, user_id),
        )
        return bonus
    return 0


def parse_bet(raw: str | None, balance: int):
    """Ставка: число, all или half."""
    if not raw:
        return None
    word = raw.strip().lower()
    if word in ("all", "все", "всё", "вабанк"):
        return balance
    if word in ("half", "половина"):
        return balance // 2
    if word.isdigit():
        return int(word)
    return None


async def take_bet(message: Message, raw_args: str | None):
    """Проверяет игрока/ставку/настройки чата. Возвращает ставку или None."""
    user = await get_user(message.from_user.id, message.from_user.username)
    bet = parse_bet((raw_args or "").split()[0] if raw_args else None, user["balance"])
    if bet is None:
        await message.reply(
            "💰 Укажи ставку: <code>/dice 100</code>, <code>all</code> или <code>half</code>."
        )
        return None
    if bet < MIN_BET:
        await message.reply(f"Минимальная ставка — {money(MIN_BET)} 🪙")
        return None
    if bet > user["balance"]:
        await message.reply(
            f"Недостаточно монет: у тебя {money(user['balance'])} 🪙, "
            f"а ставка {money(bet)} 🪙"
        )
        return None
    if bet > MAX_BET:
        bet = MAX_BET
    if message.chat.type in ("group", "supergroup"):
        chat = await get_chat(message.chat.id)
        if not chat["games_on"] and message.from_user.id not in ADMIN_IDS:
            await message.reply("🚫 Игры в этом чате выключены админом.")
            return None
        await x(
            "INSERT OR IGNORE INTO chat_players (chat_id, user_id) VALUES (?, ?)",
            (message.chat.id, message.from_user.id),
        )
        cut = max(1, bet * JACKPOT_CUT // 100)
        await x(
            "UPDATE chats SET jackpot = jackpot + ? WHERE chat_id = ?",
            (cut, message.chat.id),
        )
    return bet


async def apply_result(user_id: int, bet: int, payout: int) -> dict:
    """
    Считает итог игры. payout — сколько монет возвращается игроку (0 при проигрыше,
    bet при ничьей, bet*множитель при выигрыше).
    """
    data = {"payout": payout, "clover": False, "level_bonus": 0}
    if payout > bet:
        rows = await q(
            "SELECT qty FROM items WHERE user_id = ? AND item = 'clover'", (user_id,)
        )
        if rows and rows[0]["qty"] > 0:
            payout = int(payout * 1.1)
            data["payout"] = payout
            data["clover"] = True
            await x(
                "UPDATE items SET qty = qty - 1 WHERE user_id = ? AND item = 'clover'",
                (user_id,),
            )
    net = payout - bet
    await x("UPDATE users SET balance = balance + ? WHERE user_id = ?", (net, user_id))
    if payout > bet:
        await x("UPDATE users SET wins = wins + 1 WHERE user_id = ?", (user_id,))
        data["level_bonus"] = await add_xp(user_id, 7)
    elif payout == 0:
        await x("UPDATE users SET losses = losses + 1 WHERE user_id = ?", (user_id,))
        data["level_bonus"] = await add_xp(user_id, 2)
    else:
        data["level_bonus"] = await add_xp(user_id, 3)
    await add_log(user_id, "game", net)
    return data


def result_line(bet: int, res: dict) -> str:
    payout = res["payout"]
    if payout > bet:
        line = f"🎉 <b>Выигрыш {money(payout)}</b> 🪙 (чистыми +{money(payout - bet)})"
    elif payout == bet:
        line = "🤝 <b>Возврат ставки</b>"
    else:
        line = f"😔 <b>Проигрыш {money(bet)}</b> 🪙"
    if res["clover"]:
        line += "\n🍀 Клевер добавил +10%"
    if res["level_bonus"]:
        line += f"\n⭐ Новый уровень! +{money(res['level_bonus'])} 🪙"
    return line


# ============================ МИДЛВАРИ ============================
class Throttle(BaseMiddleware):
    """Простой антифлуд по пользователю."""

    def __init__(self, rate: float = THROTTLE):
        self.rate = rate
        self.last: dict[int, float] = {}

    async def __call__(self, handler, event: Message, data):
        uid = event.from_user.id if event.from_user else 0
        now = time.time()
        if uid and now - self.last.get(uid, 0) < self.rate:
            return
        self.last[uid] = now
        return await handler(event, data)


class BanCheck(BaseMiddleware):
    """Блокирует забаненным доступ к боту."""

    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user is not None and user.id not in ADMIN_IDS:
            rows = await q("SELECT banned FROM users WHERE user_id = ?", (user.id,))
            if rows and rows[0]["banned"]:
                if isinstance(event, Message):
                    try:
                        await event.reply("🚫 Доступ к боту заблокирован.")
                    except Exception:
                        pass
                elif isinstance(event, CallbackQuery):
                    await event.answer("🚫 Доступ заблокирован.", show_alert=True)
                return
        return await handler(event, data)


router = Router()


# ========================= ТЕКСТЫ И ДЕЙСТВИЯ =========================
def games_text() -> str:
    return (
        "🎮 <b>Игры</b> (ставка вторым словом: <code>100</code>, <code>all</code>, <code>half</code>)\n\n"
        "<b>Кубики и мячи</b> — /dice /darts /basket /foot /bowl\n"
        "<b>Слоты</b> — /slot (до x20)\n"
        "<b>Рулетка</b> — /roulette 100 red (red x2, black x2, green x14)\n"
        "<b>Монетка</b> — /coin 100 orel (orel/reshka)\n"
        "<b>Угадай число</b> — /guess 100 (6 попыток, x5)\n"
        "<b>КНБ</b> — /rps 100\n"
        "<b>Блэкджек</b> — /bj 100\n"
        "<b>Викторина</b> — /quiz 100 (x2.5)\n"
        "<b>Мины 3×3</b> — /mines 100 (кэшаут, до x7)\n"
        "<b>Дуэль с игроком</b> — /duel 100 ответом на сообщение\n"
    )


def help_text() -> str:
    return (
        "🕹 <b>ГлифБот</b> — игровой бот для чатов и лички.\n"
        "Баланс и питомец общие: играешь в группе — растёт и в ЛС.\n\n"
        + games_text()
        + "\n💼 <b>Системы</b>\n"
        "/balance — кошелёк и банк\n"
        "/profile — профиль, уровень, статистика\n"
        "/daily — ежедневный бонус (серия до 10 дней)\n"
        "/work — подработка раз в час\n"
        "/bank — вклад под 3% в час (<code>/bank put 1000</code>, <code>/bank take</code>)\n"
        "/shop, /buy, /inv — магазин и инвентарь\n"
        "/pet — питомец: кормить и забирать доход\n"
        "/top — топ-10 игроков\n"
        "/pay 100 — перевод ответом на сообщение\n"
        "/rob — ограбление ответом на сообщение\n"
        "/jackpot — банк чата, /drawjackpot — розыгрыш\n\n"
        "⚙️ /admin — админ-панель (для админов)\n"
    )


async def act_balance(user_id: int) -> str:
    u = await get_user(user_id)
    return (
        f"💰 <b>Баланс</b>\n"
        f"Кошелёк: <b>{money(u['balance'])}</b> 🪙\n"
        f"Банк: <b>{money(u['bank'])}</b> 🏦"
    )


async def act_profile(user_id: int, username: str | None = None) -> str:
    u = await get_user(user_id, username)
    games = u["wins"] + u["losses"]
    wr = int(u["wins"] / games * 100) if games else 0
    pet = (
        f"{html.escape(u['pet_name'])} (ур. {u['pet_level']})"
        if u["pet_name"]
        else "нет — заведи: /pet"
    )
    inv_rows = await q(
        "SELECT item, qty FROM items WHERE user_id = ? AND qty > 0", (user_id,)
    )
    inv = (
        ", ".join(
            f"{SHOP[r['item']][0]} x{r['qty']}"
            for r in inv_rows
            if r["item"] in SHOP
        )
        or "пусто"
    )
    return (
        f"👤 <b>Профиль</b>\n"
        f"Игрок: {html.escape(uname_username(u))}\n"
        f"⭐ Уровень <b>{u['level']}</b> (опыт {u['xp'] % 100}/100)\n"
        f"💰 Кошелёк: <b>{money(u['balance'])}</b> 🪙\n"
        f"🏦 Банк: <b>{money(u['bank'])}</b> 🪙\n"
        f"💎 Всего: <b>{money(u['balance'] + u['bank'])}</b> 🪙\n"
        f"🎮 Игр: {games} (побед {u['wins']}, поражений {u['losses']}, винрейт {wr}%)\n"
        f"🐾 Питомец: {pet}\n"
        f"🎒 Инвентарь: {inv}"
    )


def uname_username(u) -> str:
    return f"@{u['username']}" if u["username"] else f"id{u['user_id']}"


async def act_daily(user_id: int) -> str:
    u = await get_user(user_id)
    now = int(time.time())
    if u["last_daily"] and now - u["last_daily"] < 86400:
        return f"⏰ Бонус уже получен. Следующий через {fmt_time(86400 - (now - u['last_daily']))}."
    streak = u["streak"] + 1 if now - u["last_daily"] < 2 * 86400 else 1
    streak = min(streak, 10)
    amount = DAILY_BASE + DAILY_STREAK_BONUS * (streak - 1)
    await x(
        "UPDATE users SET balance = balance + ?, last_daily = ?, streak = ? WHERE user_id = ?",
        (amount, now, streak, user_id),
    )
    await add_log(user_id, "daily", amount)
    return (
        f"🎁 <b>Ежедневный бонус</b>\n+<b>{money(amount)}</b> 🪙 (серия: {streak} дн.)\n"
        f"💰 Баланс: <b>{money(await get_balance(user_id))}</b>"
    )


WORK_JOBS = [
    "разгрузил вагоны",
    "починил бота",
    "написал код",
    "помог соседу с ремонтом",
    "поймал рыбу",
    "развёз заказы",
    "собрал сервер",
]


async def act_work(user_id: int) -> str:
    u = await get_user(user_id)
    now = int(time.time())
    if u["last_work"] and now - u["last_work"] < WORK_CD:
        return f"⏰ Ты уже работал. Отдохни {fmt_time(WORK_CD - (now - u['last_work']))}."
    reward = random.randint(WORK_MIN, WORK_MAX) + u["level"] * 20
    await x(
        "UPDATE users SET balance = balance + ?, last_work = ? WHERE user_id = ?",
        (reward, now, user_id),
    )
    await add_xp(user_id, 5)
    await add_log(user_id, "work", reward)
    return (
        f"💼 Ты {random.choice(WORK_JOBS)} и заработал <b>{money(reward)}</b> 🪙\n"
        f"💰 Баланс: <b>{money(await get_balance(user_id))}</b>"
    )


def shop_text() -> str:
    lines = ["🛒 <b>Магазин</b>"]
    for key, (title, price) in SHOP.items():
        lines.append(f"{title} — <b>{money(price)}</b> 🪙 (<code>/buy {key}</code>)")
    lines.append("\n🍀 Клевер срабатывает сам в следующей выигрышной игре.")
    return "\n".join(lines)


def shop_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{title} · {money(price)}", callback_data=f"buy:{key}"
                )
            ]
            for key, (title, price) in SHOP.items()
        ]
    )


async def buy_item(user_id: int, key: str) -> str:
    if key not in SHOP:
        return "Такого товара нет."
    title, price = SHOP[key]
    u = await get_user(user_id)
    if u["balance"] < price:
        return f"Не хватает монет: нужно {money(price)} 🪙, у тебя {money(u['balance'])} 🪙"
    await x("UPDATE users SET balance = balance - ? WHERE user_id = ?", (price, user_id))
    rows = await q("SELECT qty FROM items WHERE user_id = ? AND item = ?", (user_id, key))
    if rows:
        await x(
            "UPDATE items SET qty = qty + 1 WHERE user_id = ? AND item = ?", (user_id, key)
        )
    else:
        await x(
            "INSERT INTO items (user_id, item, qty) VALUES (?, ?, 1)", (user_id, key)
        )
    await add_log(user_id, "buy", -price)
    return (
        f"✅ Куплено: {title}\n"
        f"💰 Остаток: <b>{money(await get_balance(user_id))}</b> 🪙 (/inv — инвентарь)"
    )


async def act_pet(user_id: int) -> str:
    u = await get_user(user_id)
    if not u["pet_name"]:
        await x(
            "UPDATE users SET pet_name = 'Глифик', pet_level = 1 WHERE user_id = ?",
            (user_id,),
        )
        u = await get_user(user_id)
    income = PET_INCOME * u["pet_level"]
    left = PET_CD - (int(time.time()) - u["last_pet"]) if u["last_pet"] else 0
    status = f"доход через {fmt_time(left)}" if left > 0 else "доход готов 🎉"
    return (
        f"🐾 <b>{html.escape(u['pet_name'])}</b> — уровень <b>{u['pet_level']}</b>\n"
        f"Приносит <b>{money(income)}</b> 🪙 раз в 4 часа ({status})\n"
        f"Корм: {money(PET_FEED_COST)} 🪙 → +1 уровень\n"
        f"Переименовать: <code>/pet name Барсик</code>"
    )


def pet_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍖 Покормить", callback_data="pet:feed"),
                InlineKeyboardButton(text="💰 Забрать доход", callback_data="pet:collect"),
            ]
        ]
    )


async def act_pet_feed(user_id: int) -> str:
    u = await get_user(user_id)
    if not u["pet_name"]:
        return "Сначала заведи питомца: /pet"
    if u["pet_level"] >= 30:
        return "🐾 Питомец уже максимального уровня (30)."
    food = await q("SELECT qty FROM items WHERE user_id = ? AND item = 'food'", (user_id,))
    if food and food[0]["qty"] > 0:
        await x(
            "UPDATE items SET qty = qty - 1 WHERE user_id = ? AND item = 'food'", (user_id,)
        )
        paid = "🍖 корм из инвентаря"
    else:
        if u["balance"] < PET_FEED_COST:
            return (
                f"Не хватает монет: корм стоит {money(PET_FEED_COST)} 🪙 "
                f"(или купи 🍖 в /shop)"
            )
        await x(
            "UPDATE users SET balance = balance - ? WHERE user_id = ?",
            (PET_FEED_COST, user_id),
        )
        paid = f"{money(PET_FEED_COST)} 🪙"
    await x("UPDATE users SET pet_level = pet_level + 1 WHERE user_id = ?", (user_id,))
    u = await get_user(user_id)
    return (
        f"🍖 {html.escape(u['pet_name'])} покормлен ({paid}) — "
        f"уровень <b>{u['pet_level']}</b> 💪"
    )


async def act_pet_collect(user_id: int) -> str:
    u = await get_user(user_id)
    if not u["pet_name"]:
        return "Сначала заведи питомца: /pet"
    now = int(time.time())
    if u["last_pet"] and now - u["last_pet"] < PET_CD:
        return f"⏰ Питомец ещё отдыхает: {fmt_time(PET_CD - (now - u['last_pet']))}"
    income = PET_INCOME * u["pet_level"]
    await x(
        "UPDATE users SET balance = balance + ?, last_pet = ? WHERE user_id = ?",
        (income, now, user_id),
    )
    await add_log(user_id, "pet", income)
    return (
        f"💰 {html.escape(u['pet_name'])} принёс <b>{money(income)}</b> 🪙\n"
        f"Баланс: <b>{money(await get_balance(user_id))}</b>"
    )


async def act_top() -> str:
    rows = await q(
        "SELECT user_id, username, balance, bank FROM users "
        "ORDER BY (balance + bank) DESC LIMIT 10"
    )
    if not rows:
        return "🏆 Пока пусто."
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Топ-10 игроков</b>"]
    for i, r in enumerate(rows, 1):
        icon = medals[i - 1] if i <= 3 else f"{i}."
        name = f"@{html.escape(r['username'])}" if r["username"] else f"id{r['user_id']}"
        lines.append(f"{icon} {name} — <b>{money(r['balance'] + r['bank'])}</b> 🪙")
    return "\n".join(lines)


def bank_profit(u) -> int:
    if u["bank"] <= 0:
        return 0
    hours = max(0.0, (time.time() - u["bank_time"]) / 3600)
    return int(u["bank"] * BANK_PERCENT / 100 * hours)


async def bank_text(user_id: int) -> str:
    u = await get_user(user_id)
    if u["bank"] > 0:
        return (
            f"🏦 <b>Банк</b>\n"
            f"Вклад: <b>{money(u['bank'])}</b> 🪙\n"
            f"Проценты: <b>+{money(bank_profit(u))}</b> ({BANK_PERCENT}% в час)\n"
            f"Кошелёк: <b>{money(u['balance'])}</b> 🪙\n\n"
            f"Снять всё: <code>/bank take</code>"
        )
    return (
        f"🏦 <b>Банк</b>\n"
        f"Вклада нет. Кошелёк: <b>{money(u['balance'])}</b> 🪙\n\n"
        f"Положить: <code>/bank put 1000</code> ({BANK_PERCENT}% в час)"
    )


# ============================== ИГРЫ ==============================
DICE_GAMES = {
    "dice": ("🎲", 4, 2),
    "darts": ("🎯", 5, 3),
    "basket": ("🏀", 4, 3),
    "foot": ("⚽", 4, 3),
    "bowl": ("🎳", 5, 3),
}


@router.message(Command("dice", "darts", "basket", "foot", "bowl"))
async def cmd_dice(message: Message, command: CommandObject, bot: Bot):
    emoji, need, mult = DICE_GAMES[command.command]
    bet = await take_bet(message, command.args)
    if bet is None:
        return
    sent = await bot.send_dice(message.chat.id, emoji=emoji)
    value = sent.dice.value
    win = value >= need
    res = await apply_result(message.from_user.id, bet, int(bet * mult) if win else 0)
    head = (
        f"{emoji} выпало <b>{value}</b> (нужно ≥ {need}) — "
        f"{'победа!' if win else 'не угадал'}"
    )
    await message.reply(
        f"{head}\n{result_line(bet, res)}\n"
        f"💰 Баланс: <b>{money(await get_balance(message.from_user.id))}</b>"
    )


REELS = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣"]


@router.message(Command("slot", "slots"))
async def cmd_slot(message: Message, command: CommandObject):
    bet = await take_bet(message, command.args)
    if bet is None:
        return
    r = [random.choice(REELS) for _ in range(3)]
    if r[0] == r[1] == r[2]:
        mult = {"💎": 15, "7️⃣": 20}.get(r[0], 7)
    elif r[0] == r[1] or r[1] == r[2] or r[0] == r[2]:
        mult = 1.5
    else:
        mult = 0
    res = await apply_result(message.from_user.id, bet, int(bet * mult))
    await message.reply(
        f"🎰 | {' | '.join(r)} |\n{result_line(bet, res)}\n"
        f"💰 Баланс: <b>{money(await get_balance(message.from_user.id))}</b>"
    )


RED_NUMS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
ROULETTE_ALIAS = {
    "red": "red", "r": "red", "красное": "red", "красный": "red",
    "black": "black", "b": "black", "черное": "black", "чёрное": "black",
    "черный": "black", "чёрный": "black",
    "green": "green", "g": "green", "зеро": "green", "зеленое": "green",
}
ROULETTE_PAY = {"red": 2, "black": 2, "green": 14}
ROULETTE_TITLE = {"red": "🔴 красное", "black": "⚫ чёрное", "green": "🟢 зеро"}


@router.message(Command("roulette"))
async def cmd_roulette(message: Message, command: CommandObject):
    parts = (command.args or "").split()
    bet = await take_bet(message, parts[0] if parts else None)
    if bet is None:
        return
    choice = ROULETTE_ALIAS.get(parts[1].lower()) if len(parts) > 1 else None
    if not choice:
        res = await apply_result(message.from_user.id, bet, bet)
        await message.reply(
            "Укажи цвет: <code>/roulette 100 red</code> (red, black, green)\n"
            f"{result_line(bet, res)}"
        )
        return
    number = random.randint(0, 36)
    color = "green" if number == 0 else ("red" if number in RED_NUMS else "black")
    win = color == choice
    res = await apply_result(
        message.from_user.id, bet, int(bet * ROULETTE_PAY[choice]) if win else 0
    )
    await message.reply(
        f"🎡 Выпало <b>{number}</b> {ROULETTE_TITLE[color]}\n"
        f"Твоя ставка: {ROULETTE_TITLE[choice]} (x{ROULETTE_PAY[choice]}–"
        f"{'✅' if win else '❌'})\n{result_line(bet, res)}\n"
        f"💰 Баланс: <b>{money(await get_balance(message.from_user.id))}</b>"
    )


COIN_ALIAS = {
    "orel": "o", "орёл": "o", "орел": "o", "heads": "o", "o": "o",
    "reshka": "r", "решка": "r", "tails": "r", "r": "r",
}
COIN_TITLE = {"o": "🦅 орёл", "r": "🪙 решка"}


@router.message(Command("coin"))
async def cmd_coin(message: Message, command: CommandObject):
    parts = (command.args or "").split()
    bet = await take_bet(message, parts[0] if parts else None)
    if bet is None:
        return
    choice = COIN_ALIAS.get(parts[1].lower()) if len(parts) > 1 else None
    if not choice:
        res = await apply_result(message.from_user.id, bet, bet)
        await message.reply(
            "Укажи сторону: <code>/coin 100 orel</code> (orel или reshka)\n"
            f"{result_line(bet, res)}"
        )
        return
    side = random.choice(["o", "r"])
    win = side == choice
    res = await apply_result(message.from_user.id, bet, bet * 2 if win else 0)
    await message.reply(
        f"Монетка: {COIN_TITLE[side]} — {'угадал ✅' if win else 'не угадал ❌'}\n"
        f"{result_line(bet, res)}\n"
        f"💰 Баланс: <b>{money(await get_balance(message.from_user.id))}</b>"
    )


RPS_TITLE = {"rock": "🪨 камень", "scissors": "✂️ ножницы", "paper": "📄 бумага"}
RPS_BEATS = {"rock": "scissors", "scissors": "paper", "paper": "rock"}


@router.message(Command("rps"))
async def cmd_rps(message: Message, command: CommandObject):
    bet = await take_bet(message, command.args)
    if bet is None:
        return
    uid = message.from_user.id
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🪨", callback_data=f"rps:{uid}:{bet}:rock"),
                InlineKeyboardButton(text="✂️", callback_data=f"rps:{uid}:{bet}:scissors"),
                InlineKeyboardButton(text="📄", callback_data=f"rps:{uid}:{bet}:paper"),
            ]
        ]
    )
    await message.reply(f"✊ КНБ на <b>{money(bet)}</b> 🪙 — выбирай:", reply_markup=kb)


@router.callback_query(F.data.startswith("rps:"))
async def cq_rps(call: CallbackQuery):
    _, uid, bet, choice = call.data.split(":")
    uid, bet = int(uid), int(bet)
    if call.from_user.id != uid:
        await call.answer("Это не твоя игра 🙂", show_alert=True)
        return
    bot_choice = random.choice(["rock", "scissors", "paper"])
    if choice == bot_choice:
        payout = bet
        verdict = "Ничья 🤝"
    elif RPS_BEATS[choice] == bot_choice:
        payout = bet * 2
        verdict = "Ты выиграл 🎉"
    else:
        payout = 0
        verdict = "Ты проиграл 😔"
    res = await apply_result(uid, bet, payout)
    await call.message.edit_text(
        f"Ты: {RPS_TITLE[choice]}\nБот: {RPS_TITLE[bot_choice]}\n<b>{verdict}</b>\n"
        f"{result_line(bet, res)}\n💰 Баланс: <b>{money(await get_balance(uid))}</b>"
    )
    await call.answer()


QUIZ_BANK = [
    ("Сколько планет в Солнечной системе?", ["7", "8", "9", "10"], 1),
    ("Кто написал «Евгения Онегина»?", ["Лермонтов", "Пушкин", "Гоголь", "Толстой"], 1),
    ("Столица Японии?", ["Осака", "Киото", "Токио", "Сеул"], 2),
    ("Сколько букв в русском алфавите?", ["32", "33", "34", "36"], 1),
    ("Какой газ нужен человеку для дыхания?", ["Азот", "Кислород", "Водород", "Гелий"], 1),
    ("Сколько сторон у шестиугольника?", ["5", "6", "7", "8"], 1),
    ("Самый большой океан?", ["Атлантический", "Индийский", "Тихий", "Северный"], 2),
    ("Сколько минут в двух часах?", ["100", "110", "120", "140"], 2),
]


class QuizGame(StatesGroup):
    play = State()


@router.message(Command("quiz"))
async def cmd_quiz(message: Message, command: CommandObject, state: FSMContext):
    bet = await take_bet(message, command.args)
    if bet is None:
        return
    question, options, correct = random.choice(QUIZ_BANK)
    await state.set_state(QuizGame.play)
    await state.update_data(bet=bet, correct=correct, uid=message.from_user.id)
    rows = [
        [InlineKeyboardButton(text=f"{chr(65 + i)}. {opt}", callback_data=f"qz:{i}")]
        for i, opt in enumerate(options)
    ]
    await message.reply(
        f"❓ <b>Викторина</b>\n{question}\n\nСтавка <b>{money(bet)}</b> 🪙, верный ответ ×2.5",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.callback_query(F.data.startswith("qz:"))
async def cq_quiz(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data or data.get("correct") is None:
        await call.answer("Вопрос уже закрыт.", show_alert=True)
        return
    if call.from_user.id != data["uid"]:
        await call.answer("Это не твоя игра 🙂", show_alert=True)
        return
    pick = int(call.data.split(":")[1])
    bet = data["bet"]
    win = pick == data["correct"]
    await state.clear()
    res = await apply_result(call.from_user.id, bet, int(bet * 2.5) if win else 0)
    await call.message.edit_text(
        f"{'✅ Верно!' if win else '❌ Мимо.'}\n{result_line(bet, res)}\n"
        f"💰 Баланс: <b>{money(await get_balance(call.from_user.id))}</b>"
    )
    await call.answer()


class GuessGame(StatesGroup):
    play = State()


@router.message(Command("guess"))
async def cmd_guess(message: Message, command: CommandObject, state: FSMContext):
    bet = await take_bet(message, command.args)
    if bet is None:
        return
    await state.set_state(GuessGame.play)
    await state.update_data(
        bet=bet, target=random.randint(1, 100), tries=0, uid=message.from_user.id
    )
    await message.reply(
        f"🔢 Я загадал число от <b>1</b> до <b>100</b>.\n"
        f"Просто пришли число в чат. Попыток: 6, выигрыш ×5.\n"
        f"Ставка: <b>{money(bet)}</b> 🪙 (выход — /cancel)"
    )


@router.message(GuessGame.play, Command("cancel"))
async def cmd_guess_cancel(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    if data.get("bet"):
        res = await apply_result(message.from_user.id, data["bet"], data["bet"])
        await message.reply(f"Игра прервана.\n{result_line(data['bet'], res)}")
    else:
        await message.reply("Игра прервана.")


@router.message(GuessGame.play, F.text)
async def guess_step(message: Message, state: FSMContext):
    data = await state.get_data()
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.reply("Нужно число от 1 до 100 (выход — /cancel).")
        return
    num = int(text)
    uid = data["uid"]
    bet = data["bet"]
    tries = data["tries"] + 1
    target = data["target"]
    if num == target:
        await state.clear()
        res = await apply_result(uid, bet, bet * 5)
        await message.reply(
            f"🎯 Точно! Это было число <b>{target}</b> (попыток: {tries}).\n"
            f"{result_line(bet, res)}\n"
            f"💰 Баланс: <b>{money(await get_balance(uid))}</b>"
        )
        return
    if tries >= 6:
        await state.clear()
        res = await apply_result(uid, bet, 0)
        await message.reply(
            f"😔 Попытки кончились. Я загадывал <b>{target}</b>.\n"
            f"{result_line(bet, res)}\n"
            f"💰 Баланс: <b>{money(await get_balance(uid))}</b>"
        )
        return
    await state.update_data(tries=tries)
    hint = "больше ⬆️" if target > num else "меньше ⬇️"
    await message.reply(f"Не угадал. Моё число <b>{hint}</b>. Осталось попыток: {6 - tries}")


class BJGame(StatesGroup):
    play = State()


def new_deck() -> list[int]:
    deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
    random.shuffle(deck)
    return deck


def hand_score(hand: list[int]) -> int:
    score = sum(hand)
    aces = hand.count(11)
    while score > 21 and aces:
        score -= 10
        aces -= 1
    return score


def show_hand(hand: list[int]) -> str:
    return " ".join(str(c) for c in hand)


def bj_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🃏 Ещё карту", callback_data="bj:hit"),
                InlineKeyboardButton(text="✋ Хватит", callback_data="bj:stand"),
            ]
        ]
    )


def bj_table(bet: int, player: list[int], dealer: list[int], hidden: bool) -> str:
    dealer_text = f"{dealer[0]} + ?" if hidden else show_hand(dealer)
    dealer_score = f" = <b>{hand_score(dealer)}</b>" if not hidden else ""
    return (
        f"🃏 <b>Блэкджек</b> (ставка {money(bet)} 🪙)\n"
        f"Ты: {show_hand(player)} = <b>{hand_score(player)}</b>\n"
        f"Дилер: {dealer_text}{dealer_score}"
    )


@router.message(Command("bj", "blackjack"))
async def cmd_bj(message: Message, command: CommandObject, state: FSMContext):
    bet = await take_bet(message, command.args)
    if bet is None:
        return
    deck = new_deck()
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]
    uid = message.from_user.id
    if hand_score(player) == 21:
        res = await apply_result(uid, bet, int(bet * 2.5))
        await message.reply(
            f"🃏 <b>Блэкджек с раздачи!</b> Карты: {show_hand(player)}\n"
            f"{result_line(bet, res)}\n"
            f"💰 Баланс: <b>{money(await get_balance(uid))}</b>"
        )
        return
    await state.set_state(BJGame.play)
    await state.update_data(bet=bet, deck=deck, player=player, dealer=dealer, uid=uid)
    await message.reply(
        bj_table(bet, player, dealer, hidden=True), reply_markup=bj_kb()
    )


@router.callback_query(F.data.startswith("bj:"))
async def cq_bj(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if "deck" not in data:
        await call.answer("Партия не найдена — начни заново: /bj 100", show_alert=True)
        return
    if call.from_user.id != data["uid"]:
        await call.answer("Это партия другого игрока.", show_alert=True)
        return
    action = call.data.split(":")[1]
    bet, deck = data["bet"], data["deck"]
    player, dealer, uid = data["player"], data["dealer"], data["uid"]

    if action == "hit":
        player.append(deck.pop())
        if hand_score(player) > 21:
            await state.clear()
            res = await apply_result(uid, bet, 0)
            await call.message.edit_text(
                f"🃏 Перебор: {show_hand(player)} = <b>{hand_score(player)}</b>\n"
                f"{result_line(bet, res)}\n"
                f"💰 Баланс: <b>{money(await get_balance(uid))}</b>"
            )
            await call.answer()
            return
        await state.update_data(player=player, deck=deck)
        await call.message.edit_text(
            bj_table(bet, player, dealer, hidden=True), reply_markup=bj_kb()
        )
        await call.answer()
        return

    while hand_score(dealer) < 17:
        dealer.append(deck.pop())
    p, d = hand_score(player), hand_score(dealer)
    if p > d:
        payout, verdict = bet * 2, "🏆 Ты победил!"
    elif p == d:
        payout, verdict = bet, "🤝 Ничья"
    else:
        payout, verdict = 0, "🎩 Дилер выиграл"
    await state.clear()
    res = await apply_result(uid, bet, payout)
    await call.message.edit_text(
        f"🃏 Ты: {show_hand(player)} = <b>{p}</b>\n"
        f"🎩 Дилер: {show_hand(dealer)} = <b>{d}</b>\n"
        f"<b>{verdict}</b>\n{result_line(bet, res)}\n"
        f"💰 Баланс: <b>{money(await get_balance(uid))}</b>"
    )
    await call.answer()


MINE_MULT = {1: 1.4, 2: 1.9, 3: 2.6, 4: 3.6, 5: 5.0, 6: 7.0}


class MinesGame(StatesGroup):
    play = State()


def mines_kb(opened: list[int]) -> InlineKeyboardMarkup:
    rows = []
    for r in range(3):
        row = []
        for c in range(3):
            i = r * 3 + c
            row.append(
                InlineKeyboardButton(
                    text="✅" if i in opened else "⬜", callback_data=f"mn:{i}"
                )
            )
        rows.append(row)
    rows.append([InlineKeyboardButton(text="💸 Забрать", callback_data="mn:cash")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("mines"))
async def cmd_mines(message: Message, command: CommandObject, state: FSMContext):
    bet = await take_bet(message, command.args)
    if bet is None:
        return
    bombs = random.sample(range(9), 3)
    await state.set_state(MinesGame.play)
    await state.update_data(
        bet=bet, bombs=bombs, opened=[], uid=message.from_user.id, chat=message.chat.id
    )
    await message.reply(
        f"⛏ <b>Мины</b> (ставка {money(bet)} 🪙)\n"
        f"На поле 3 мины из 9. Открывай клетки и забирай выигрыш в любой момент.\n"
        f"Множители: x1.4 → x1.9 → x2.6 → x3.6 → x5 → x7",
        reply_markup=mines_kb([]),
    )


@router.callback_query(F.data.startswith("mn:"))
async def cq_mines(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if "bombs" not in data:
        await call.answer("Игра не найдена — начни заново: /mines 100", show_alert=True)
        return
    if call.from_user.id != data["uid"]:
        await call.answer("Это чужая игра 🙂", show_alert=True)
        return
    uid, bet = data["uid"], data["bet"]
    bombs, opened = data["bombs"], data["opened"]

    if call.data == "mn:cash":
        if not opened:
            await call.answer("Открой хотя бы одну клетку.", show_alert=True)
            return
        payout = int(bet * MINE_MULT.get(len(opened), 7.0))
        await state.clear()
        res = await apply_result(uid, bet, payout)
        await call.message.edit_text(
            f"💸 Забрал на {len(opened)} клетках\n{result_line(bet, res)}\n"
            f"💰 Баланс: <b>{money(await get_balance(uid))}</b>"
        )
        await call.answer()
        return

    cell = int(call.data.split(":")[1])
    if cell in opened:
        await call.answer("Эта клетка уже открыта.")
        return
    if cell in bombs:
        await state.clear()
        res = await apply_result(uid, bet, 0)
        field = "".join(
            "💥" if i == cell else ("✅" if i in opened else "⬜") for i in range(9)
        )
        await call.message.edit_text(
            f"💥 Мина на клетке {cell + 1}!\n{field}\n{result_line(bet, res)}\n"
            f"💰 Баланс: <b>{money(await get_balance(uid))}</b>"
        )
        await call.answer()
        return

    opened.append(cell)
    if len(opened) == 6:
        payout = int(bet * 7.0)
        await state.clear()
        res = await apply_result(uid, bet, payout)
        await call.message.edit_text(
            f"🏆 Все безопасные клетки открыты!\n{result_line(bet, res)}\n"
            f"💰 Баланс: <b>{money(await get_balance(uid))}</b>"
        )
        await call.answer()
        return
    await state.update_data(opened=opened)
    mult = MINE_MULT.get(len(opened) + 1, 7.0)
    await call.message.edit_text(
        f"⛏ <b>Мины</b> (ставка {money(bet)} 🪙)\n"
        f"Открыто: {len(opened)} · следующий шаг даст ×{mult}\n"
        f"Забрать сейчас: <b>{money(int(bet * MINE_MULT.get(len(opened), 1.0)))}</b>",
        reply_markup=mines_kb(opened),
    )
    await call.answer()


@router.message(Command("duel"))
async def cmd_duel(message: Message, command: CommandObject):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("Ответь командой на сообщение игрока: <code>/duel 100</code>")
        return
    rival = message.reply_to_message.from_user
    if rival.is_bot or rival.id == message.from_user.id:
        await message.reply("Нужен живой соперник и не ты сам 🙂")
        return
    bet = await take_bet(message, command.args)
    if bet is None:
        return
    rival_u = await get_user(rival.id, rival.username)
    if rival_u["balance"] < bet:
        await message.reply(f"У соперника нет {money(bet)} 🪙 на ставку.")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"⚔️ Принять ({money(bet)} 🪙)",
                    callback_data=f"duel:{message.from_user.id}:{rival.id}:{bet}",
                )
            ]
        ]
    )
    await message.reply(
        f"⚔️ {uname(message.from_user)} вызывает {uname(rival)} на дуэль!\n"
        f"Ставка: <b>{money(bet)}</b> 🪙 — победитель забирает всё.\n"
        f"Ждём подтверждения {uname(rival)}.",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("duel:"))
async def cq_duel(call: CallbackQuery):
    _, chall, rival, bet = call.data.split(":")
    chall, rival, bet = int(chall), int(rival), int(bet)
    if call.from_user.id != rival:
        await call.answer("Это не твой вызов 🙂", show_alert=True)
        return
    a = await get_user(chall)
    b = await get_user(rival)
    if a["balance"] < bet or b["balance"] < bet:
        await call.answer("У кого-то уже не хватает монет — дуэль отменена.", show_alert=True)
        await call.message.edit_text("⚔️ Дуэль отменена: не хватает монет у одного из игроков.")
        return
    winner, loser = random.choice([(chall, rival), (rival, chall)])
    res_w = await apply_result(winner, bet, bet * 2)
    res_l = await apply_result(loser, bet, 0)
    await call.message.edit_text(
        f"⚔️ <b>Дуэль завершена!</b>\n"
        f"🏆 Победил <a href=\"tg://user?id={winner}\">игрок</a> (+{money(bet)} 🪙)\n"
        f"{result_line(bet, res_w)}\n"
        f"Проигравший: {result_line(bet, res_l)}\n"
        f"💰 Баланс победителя: <b>{money(await get_balance(winner))}</b>"
    )
    await call.answer("Дуэль окончена")


# ============================ СИСТЕМЫ ============================
def menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎮 Игры", callback_data="menu:games"),
                InlineKeyboardButton(text="👤 Профиль", callback_data="menu:profile"),
            ],
            [
                InlineKeyboardButton(text="🎁 Дейли", callback_data="menu:daily"),
                InlineKeyboardButton(text="💼 Работа", callback_data="menu:work"),
            ],
            [
                InlineKeyboardButton(text="🐾 Питомец", callback_data="menu:pet"),
                InlineKeyboardButton(text="🏆 Топ", callback_data="menu:top"),
            ],
            [
                InlineKeyboardButton(text="🛒 Магазин", callback_data="menu:shop"),
                InlineKeyboardButton(text="💰 Баланс", callback_data="menu:balance"),
            ],
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    await get_user(message.from_user.id, message.from_user.username)
    if message.chat.type == "private":
        await message.answer(
            f"Привет, {uname(message.from_user)}! 🕹\n\n{help_text()}",
            reply_markup=menu_kb(),
        )
    else:
        chat = await get_chat(message.chat.id)
        state = "включены 🎮" if chat["games_on"] else "выключены 🚫"
        await message.reply(
            f"Привет! Я игровой бот. Игры в этом чате {state}.\n"
            f"Список игр — /games, полная справка — /help, банк чата — /jackpot"
        )


@router.message(Command("help", "menu"))
async def cmd_help(message: Message):
    await message.answer(help_text(), reply_markup=menu_kb())


@router.message(Command("games"))
async def cmd_games(message: Message):
    await message.reply(games_text())


@router.message(Command("balance", "bal"))
async def cmd_balance(message: Message):
    await message.reply(await act_balance(message.from_user.id))


@router.message(Command("profile", "me"))
async def cmd_profile(message: Message):
    await message.reply(
        await act_profile(message.from_user.id, message.from_user.username)
    )


@router.message(Command("daily", "bonus"))
async def cmd_daily(message: Message):
    await get_user(message.from_user.id, message.from_user.username)
    await message.reply(await act_daily(message.from_user.id))


@router.message(Command("work"))
async def cmd_work(message: Message):
    await get_user(message.from_user.id, message.from_user.username)
    await message.reply(await act_work(message.from_user.id))


@router.message(Command("top"))
async def cmd_top(message: Message):
    await message.reply(await act_top())


@router.message(Command("shop"))
async def cmd_shop(message: Message):
    await message.reply(shop_text(), reply_markup=shop_kb())


@router.message(Command("buy"))
async def cmd_buy(message: Message, command: CommandObject):
    key = (command.args or "").split()
    if not key:
        await message.reply("Что купить? <code>/buy shield</code>")
        return
    await message.reply(await buy_item(message.from_user.id, key[0].lower()))


@router.message(Command("inv"))
async def cmd_inv(message: Message):
    rows = await q(
        "SELECT item, qty FROM items WHERE user_id = ? AND qty > 0",
        (message.from_user.id,),
    )
    if not rows:
        await message.reply("🎒 Инвентарь пуст. Загляни в /shop")
        return
    lines = ["🎒 <b>Инвентарь</b>"]
    for r in rows:
        title = SHOP.get(r["item"], (r["item"], 0))[0]
        lines.append(f"{title} — x{r['qty']}")
    await message.reply("\n".join(lines))


@router.message(Command("pet"))
async def cmd_pet(message: Message, command: CommandObject):
    await get_user(message.from_user.id, message.from_user.username)
    args = (command.args or "").split()
    uid = message.from_user.id
    if not args:
        await message.reply(await act_pet(uid), reply_markup=pet_kb())
        return
    action = args[0].lower()
    if action in ("feed", "корм", "покормить"):
        await message.reply(await act_pet_feed(uid))
    elif action in ("collect", "доход", "забрать"):
        await message.reply(await act_pet_collect(uid))
    elif action in ("name", "имя") and len(args) > 1:
        name = html.escape(" ".join(args[1:])[:20])
        await x("UPDATE users SET pet_name = ? WHERE user_id = ?", (name, uid))
        await message.reply(f"✅ Теперь питомца зовут <b>{name}</b>.")
    else:
        await message.reply(
            "🐾 Команды: <code>/pet</code>, <code>/pet feed</code>, "
            "<code>/pet collect</code>, <code>/pet name Барсик</code>"
        )


@router.callback_query(F.data.startswith("pet:"))
async def cq_pet(call: CallbackQuery):
    action = call.data.split(":")[1]
    if action == "feed":
        text = await act_pet_feed(call.from_user.id)
    else:
        text = await act_pet_collect(call.from_user.id)
    await call.message.reply(text)
    await call.answer()


@router.message(Command("bank"))
async def cmd_bank(message: Message, command: CommandObject):
    await get_user(message.from_user.id, message.from_user.username)
    uid = message.from_user.id
    args = (command.args or "").split()
    if not args:
        await message.reply(await bank_text(uid))
        return
    action = args[0].lower()
    if action in ("put", "вложить", "положить"):
        if len(args) < 2:
            await message.reply("Сколько вложить? <code>/bank put 1000</code>")
            return
        u = await get_user(uid)
        amount = parse_bet(args[1], u["balance"])
        if not amount or amount < 1:
            await message.reply("Нужна сумма, например <code>/bank put 1000</code>")
            return
        if amount > u["balance"]:
            await message.reply(f"У тебя только {money(u['balance'])} 🪙")
            return
        now = int(time.time())
        profit = bank_profit(u)
        new_bank = u["bank"] + profit + amount if u["bank"] > 0 else amount
        await x(
            "UPDATE users SET bank = ?, bank_time = ?, balance = balance - ? WHERE user_id = ?",
            (new_bank, now, amount, uid),
        )
        await message.reply(
            f"🏦 Вклад пополнен на <b>{money(amount)}</b> 🪙\n"
            f"Всего в банке: <b>{money(new_bank)}</b> 🪙 (+{BANK_PERCENT}% в час)"
        )
    elif action in ("take", "снять", "забрать"):
        u = await get_user(uid)
        if u["bank"] <= 0:
            await message.reply("Вклада нет.")
            return
        total = u["bank"] + bank_profit(u)
        await x(
            "UPDATE users SET balance = balance + ?, bank = 0, bank_time = 0 WHERE user_id = ?",
            (total, uid),
        )
        await add_log(uid, "bank_take", total)
        await message.reply(
            f"🏦 Снято <b>{money(total)}</b> 🪙\n"
            f"💰 Баланс: <b>{money(await get_balance(uid))}</b>"
        )
    else:
        await message.reply(
            "🏦 <code>/bank</code> — состояние\n"
            "<code>/bank put 1000</code> — вложить\n"
            "<code>/bank take</code> — снять всё"
        )


@router.message(Command("pay"))
async def cmd_pay(message: Message, command: CommandObject):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("Ответь командой на сообщение игрока: <code>/pay 100</code>")
        return
    target = message.reply_to_message.from_user
    if target.is_bot or target.id == message.from_user.id:
        await message.reply("Так не получится 🙂")
        return
    sender = await get_user(message.from_user.id, message.from_user.username)
    amount = parse_bet((command.args or "").split()[0] if command.args else None, sender["balance"])
    if not amount or amount < 1:
        await message.reply("Укажи сумму: <code>/pay 100</code>")
        return
    if amount > sender["balance"]:
        await message.reply(f"У тебя только {money(sender['balance'])} 🪙")
        return
    await get_user(target.id, target.username)
    await x(
        "UPDATE users SET balance = balance - ? WHERE user_id = ?",
        (amount, message.from_user.id),
    )
    await x("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target.id))
    await add_log(message.from_user.id, "pay_out", -amount)
    await add_log(target.id, "pay_in", amount)
    await message.reply(
        f"💸 {uname(message.from_user)} перевёл {uname(target)} "
        f"<b>{money(amount)}</b> 🪙"
    )


@router.message(Command("rob"))
async def cmd_rob(message: Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("Ответь командой на сообщение игрока: <code>/rob</code>")
        return
    victim = message.reply_to_message.from_user
    if victim.is_bot or victim.id == message.from_user.id:
        await message.reply("Нужна живая жертва 🙂")
        return
    robber = await get_user(message.from_user.id, message.from_user.username)
    target = await get_user(victim.id, victim.username)
    now = int(time.time())
    if robber["last_rob"] and now - robber["last_rob"] < ROB_CD:
        left = ROB_CD - (now - robber["last_rob"])
        await message.reply(f"⏰ Слишком рискованно. Попробуй через {fmt_time(left)}.")
        return
    if target["balance"] < 200:
        await message.reply("У жертвы меньше 200 🪙 — овчинка не стоит выделки.")
        return
    await x("UPDATE users SET last_rob = ? WHERE user_id = ?", (now, robber["user_id"]))
    shields = await q(
        "SELECT qty FROM items WHERE user_id = ? AND item = 'shield'", (target["user_id"],)
    )
    if shields and shields[0]["qty"] > 0:
        await x(
            "UPDATE items SET qty = qty - 1 WHERE user_id = ? AND item = 'shield'",
            (target["user_id"],),
        )
        await message.reply(f"🛡 У {uname(victim)} сработал щит — ограбление провалилось!")
        return
    if random.random() < 0.45:
        stolen = max(1, target["balance"] * random.randint(10, 20) // 100)
        await x(
            "UPDATE users SET balance = balance - ? WHERE user_id = ?",
            (stolen, target["user_id"]),
        )
        await x(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (stolen, robber["user_id"]),
        )
        await add_log(robber["user_id"], "rob_win", stolen)
        await add_log(target["user_id"], "rob_lose", -stolen)
        await message.reply(
            f"🥷 {uname(message.from_user)} обчистил {uname(victim)} на "
            f"<b>{money(stolen)}</b> 🪙!"
        )
    else:
        fine = min(robber["balance"], max(50, robber["balance"] // 10))
        await x(
            "UPDATE users SET balance = balance - ? WHERE user_id = ?",
            (fine, robber["user_id"]),
        )
        await add_log(robber["user_id"], "rob_fail", -fine)
        await message.reply(f"🚨 Ограбление провалилось! Штраф: <b>{money(fine)}</b> 🪙")


@router.message(Command("jackpot"))
async def cmd_jackpot(message: Message):
    if message.chat.type == "private":
        await message.reply("🎰 Джекпот копится в групповых чатах.")
        return
    chat = await get_chat(message.chat.id)
    await message.reply(
        f"🎰 <b>Джекпот чата</b>: {money(chat['jackpot'])} 🪙\n"
        f"С каждой ставки сюда уходит {JACKPOT_CUT}%.\n"
        f"Розыгрыш доступен, когда банк ≥ {money(JACKPOT_MIN)}: /drawjackpot"
    )


@router.message(Command("drawjackpot"))
async def cmd_draw_jackpot(message: Message):
    if message.chat.type == "private":
        await message.reply("🎰 Розыгрыш работает в группах.")
        return
    chat = await get_chat(message.chat.id)
    if chat["jackpot"] < JACKPOT_MIN:
        await message.reply(
            f"🎰 В банке всего {money(chat['jackpot'])} 🪙 — нужно {money(JACKPOT_MIN)}."
        )
        return
    players = await q(
        "SELECT user_id FROM chat_players WHERE chat_id = ?", (message.chat.id,)
    )
    if not players:
        await message.reply("В этом чате ещё никто не играл.")
        return
    prize = chat["jackpot"]
    winner = random.choice(players)["user_id"]
    await get_user(winner)
    await x("UPDATE chats SET jackpot = 0 WHERE chat_id = ?", (message.chat.id,))
    await x("UPDATE users SET balance = balance + ? WHERE user_id = ?", (prize, winner))
    await add_log(winner, "jackpot", prize)
    await message.reply(
        f"🎉 <b>Джекпот {money(prize)} 🪙</b> забирает "
        f"<a href=\"tg://user?id={winner}\">игрок</a>!"
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.reply("Ок, отменил.")


@router.callback_query(F.data.startswith("menu:"))
async def cq_menu(call: CallbackQuery):
    key = call.data.split(":")[1]
    uid = call.from_user.id
    if key == "games":
        await call.message.reply(games_text())
    elif key == "profile":
        await call.message.reply(await act_profile(uid, call.from_user.username))
    elif key == "daily":
        await get_user(uid, call.from_user.username)
        await call.message.reply(await act_daily(uid))
    elif key == "work":
        await get_user(uid, call.from_user.username)
        await call.message.reply(await act_work(uid))
    elif key == "pet":
        await get_user(uid, call.from_user.username)
        await call.message.reply(await act_pet(uid), reply_markup=pet_kb())
    elif key == "top":
        await call.message.reply(await act_top())
    elif key == "shop":
        await call.message.reply(shop_text(), reply_markup=shop_kb())
    elif key == "balance":
        await call.message.reply(await act_balance(uid))
    await call.answer()


@router.callback_query(F.data.startswith("buy:"))
async def cq_buy(call: CallbackQuery):
    await call.message.reply(await buy_item(call.from_user.id, call.data.split(":")[1]))
    await call.answer()


# ============================ АДМИНКА ============================
class AdminAct(StatesGroup):
    input = State()


def admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="adm:stats"),
                InlineKeyboardButton(text="👤 Юзер", callback_data="adm:user"),
            ],
            [
                InlineKeyboardButton(text="💰 Выдать", callback_data="adm:give"),
                InlineKeyboardButton(text="💸 Снять", callback_data="adm:take"),
            ],
            [
                InlineKeyboardButton(text="🚫 Бан", callback_data="adm:ban"),
                InlineKeyboardButton(text="✅ Разбан", callback_data="adm:unban"),
            ],
            [
                InlineKeyboardButton(text="📢 Рассылка", callback_data="adm:cast"),
                InlineKeyboardButton(text="🎮 Игры чата", callback_data="adm:toggle"),
            ],
            [InlineKeyboardButton(text="📜 Логи", callback_data="adm:logs")],
        ]
    )


async def admin_stats() -> str:
    users = (await q("SELECT COUNT(*) c FROM users"))[0]["c"]
    total = (await q("SELECT COALESCE(SUM(balance + bank), 0) s FROM users"))[0]["s"]
    bets = (await q("SELECT COUNT(*) c FROM logs WHERE action = 'game'"))[0]["c"]
    banned = (await q("SELECT COUNT(*) c FROM users WHERE banned = 1"))[0]["c"]
    chats = (await q("SELECT COUNT(*) c FROM chats"))[0]["c"]
    return (
        f"📊 <b>Статистика</b>\n"
        f"Игроков: <b>{users}</b> (забанено: {banned})\n"
        f"Монет в экономике: <b>{money(total)}</b> 🪙\n"
        f"Ставок сделано: <b>{bets}</b>\n"
        f"Чатов в базе: <b>{chats}</b>"
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Команда только для админов.")
        return
    await message.reply("⚙️ <b>Админ-панель</b>\nВыбери действие:", reply_markup=admin_kb())


ROB_CD = 600  # (оверрайд выше, оставлен для наглядности порядка настроек)


@router.callback_query(F.data.startswith("adm:"))
async def cq_admin(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("⛔ Только для админов", show_alert=True)
        return
    key = call.data.split(":")[1]

    if key == "stats":
        await call.message.reply(await admin_stats())

    elif key in ("give", "take"):
        await state.set_state(AdminAct.input)
        await state.update_data(op="give" if key == "give" else "take")
        word = "выдать" if key == "give" else "снять"
        await call.message.reply(
            f"Пришли <code>ID сумма</code>, чтобы {word} монеты.\nНапример: <code>123456789 5000</code>"
        )

    elif key in ("ban", "unban"):
        await state.set_state(AdminAct.input)
        await state.update_data(op=key)
        await call.message.reply(
            "Пришли ID игрока." if key == "ban" else "Пришли ID для разбана."
        )

    elif key == "cast":
        await state.set_state(AdminAct.input)
        await state.update_data(op="cast")
        await call.message.reply("Пришли текст рассылки (можно HTML).")

    elif key == "user":
        await state.set_state(AdminAct.input)
        await state.update_data(op="user")
        await call.message.reply("Пришли ID игрока.")

    elif key == "logs":
        rows = await q(
            "SELECT user_id, action, amount, ts FROM logs ORDER BY id DESC LIMIT 10"
        )
        if not rows:
            await call.message.reply("Логов пока нет.")
        else:
            lines = ["📜 <b>Последние операции</b>"]
            for r in rows:
                when = time.strftime("%d.%m %H:%M", time.localtime(r["ts"]))
                lines.append(
                    f"{when} · <code>{r['user_id']}</code> · {r['action']} · "
                    f"{money(r['amount'])}"
                )
            await call.message.reply("\n".join(lines))

    elif key == "toggle":
        if call.message.chat.type == "private":
            await call.message.reply("Переключать игры можно только в группе.")
        else:
            chat = await get_chat(call.message.chat.id)
            new_value = 0 if chat["games_on"] else 1
            await x(
                "UPDATE chats SET games_on = ? WHERE chat_id = ?",
                (new_value, call.message.chat.id),
            )
            await call.message.reply(
                "🎮 Игры включены." if new_value else "🚫 Игры выключены."
            )
    await call.answer()


@router.message(AdminAct.input)
async def admin_input(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await state.clear()
        return
    data = await state.get_data()
    op = data.get("op", "")
    text = (message.text or "").strip()
    await state.clear()

    if op in ("give", "take"):
        parts = text.split()
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            await message.reply("Формат: <code>ID сумма</code>")
            return
        uid, amount = int(parts[0]), int(parts[1])
        if op == "take":
            amount = -amount
        await get_user(uid)
        await x("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
        await add_log(uid, f"admin_{op}", amount)
        await message.reply(
            f"✅ <code>{uid}</code>: {money(amount)} 🪙\n"
            f"Новый баланс: <b>{money(await get_balance(uid))}</b>"
        )
        try:
            await message.bot.send_message(uid, f"💰 Баланс изменён админом: {money(amount)} 🪙")
        except Exception:
            pass

    elif op in ("ban", "unban"):
        if not text.isdigit():
            await message.reply("Нужен числовой ID.")
            return
        uid = int(text)
        await get_user(uid)
        value = 1 if op == "ban" else 0
        await x("UPDATE users SET banned = ? WHERE user_id = ?", (value, uid))
        await add_log(uid, f"admin_{op}", 0)
        await message.reply("🚫 Забанен." if value else "✅ Разбанен.")

    elif op == "cast":
        if not text:
            await message.reply("Пустой текст — рассылка отменена.")
            return
        ids = [r["user_id"] for r in await q("SELECT user_id FROM users WHERE banned = 0")]
        sent = 0
        for uid in ids:
            try:
                await message.bot.send_message(uid, f"📢 {text}")
                sent += 1
            except Exception:
                pass
            await asyncio.sleep(0.05)
        await message.reply(f"📢 Отправлено {sent} из {len(ids)}.")

    elif op == "user":
        if not text.isdigit():
            await message.reply("Нужен числовой ID.")
            return
        uid = int(text)
        u = await get_user(uid)
        await message.reply(
            f"👤 <code>{uid}</code>\n"
            f"Баланс: <b>{money(u['balance'])}</b> 🪙 · банк {money(u['bank'])} 🪙\n"
            f"Уровень {u['level']}, опыта {u['xp']}\n"
            f"Игр: побед {u['wins']}, поражений {u['losses']}\n"
            f"Питомец: {u['pet_name'] or '—'} (ур. {u['pet_level']})\n"
            f"Бан: {'да' if u['banned'] else 'нет'}"
        )


@router.message(Command("casino_on", "casino_off", "games_on", "games_off"))
async def cmd_casino(message: Message, command: CommandObject):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Только админ может включать и выключать игры.")
        return
    if message.chat.type == "private":
        await message.reply("Команда работает в групповом чате.")
        return
    value = 1 if command.command in ("casino_on", "games_on") else 0
    await get_chat(message.chat.id)
    await x("UPDATE chats SET games_on = ? WHERE chat_id = ?", (value, message.chat.id))
    await message.reply("🎮 Игры включены." if value else "🚫 Игры выключены.")


@router.message(Command("give"))
async def cmd_give(message: Message, command: CommandObject):
    await admin_input(message, state=None) if False else None  # (заглушка, не используется)
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Только для админов.")
        return
    parts = (command.args or "").split()
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].lstrip("-").isdigit():
        await message.reply("Формат: <code>/give ID сумма</code> (можно отрицательную)")
        return
    uid, amount = int(parts[0]), int(parts[1])
    await get_user(uid)
    await x("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
    await add_log(uid, "admin_give", amount)
    await message.reply(
        f"✅ <code>{uid}</code>: {money(amount)} 🪙 · баланс "
        f"<b>{money(await get_balance(uid))}</b>"
    )


# ============================== СТАРТ ==============================
async def set_commands(bot: Bot):
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Начало и меню"),
            BotCommand(command="games", description="Список игр"),
            BotCommand(command="balance", description="Баланс"),
            BotCommand(command="profile", description="Профиль"),
            BotCommand(command="daily", description="Ежедневный бонус"),
            BotCommand(command="work", description="Подработка"),
            BotCommand(command="bank", description="Банк под проценты"),
            BotCommand(command="shop", description="Магазин"),
            BotCommand(command="pet", description="Питомец"),
            BotCommand(command="top", description="Топ игроков"),
            BotCommand(command="help", description="Справка"),
        ]
    )


async def main():
    if not BOT_TOKEN:
        raise SystemExit(
            "Не задан BOT_TOKEN. Пример: BOT_TOKEN=\"123:AA...\" python bot.py"
        )
    await init_db()
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    router.message.middleware(BanCheck())
    router.message.middleware(Throttle())
    dp.include_router(router)
    await set_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    log.info("ГлифБот запущен. Админов: %s", len(ADMIN_IDS))
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as exc:
        log.info("Остановлено: %s", exc)

