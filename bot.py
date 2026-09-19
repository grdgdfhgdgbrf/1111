# ============================================================
#  GameHub v2 — Telegram-бот: 9 игр + админка
#  Python 3.11+ | aiogram 3.x | SQLite
# ============================================================

import asyncio
import logging
import random
import string
import sqlite3
from datetime import datetime, timedelta, date
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, DiceEmoji, ChatType
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

# ============================================================
#  КОНФИГ
# ============================================================
BOT_TOKEN = "8996813076:AAGq74gyRRW5fMxvHaIE190_B-tmzXk8aNA"
ADMIN_IDS = [5356400377]
DB_PATH = "bot.db"

DAILY_BONUS = 500           # ежедневный бонус
FIRST_GAME_BONUS = 100      # бонус за первую игру дня

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.FileHandler("bot.log", encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger("GameHub")

# ============================================================
#  БАЗА ДАННЫХ
# ============================================================
def db_init():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 1000,
        last_bonus TEXT,
        last_game_bonus TEXT,
        pvp_wins INTEGER DEFAULT 0,
        pvp_losses INTEGER DEFAULT 0,
        pvp_draws INTEGER DEFAULT 0,
        bot_wins INTEGER DEFAULT 0,
        bot_losses INTEGER DEFAULT 0,
        dice_wins INTEGER DEFAULT 0,
        dice_losses INTEGER DEFAULT 0,
        guess_wins INTEGER DEFAULT 0,
        guess_losses INTEGER DEFAULT 0,
        coin_wins INTEGER DEFAULT 0,
        coin_losses INTEGER DEFAULT 0,
        slots_wins INTEGER DEFAULT 0,
        slots_losses INTEGER DEFAULT 0,
        emoji_wins INTEGER DEFAULT 0,
        emoji_losses INTEGER DEFAULT 0,
        bj_wins INTEGER DEFAULT 0,
        bj_losses INTEGER DEFAULT 0,
        roulette_wins INTEGER DEFAULT 0,
        roulette_losses INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        ban_reason TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_seen TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS games_pvp (
        code TEXT PRIMARY KEY,
        chat_id INTEGER,
        player1_id INTEGER,
        player2_id INTEGER,
        board TEXT,
        turn INTEGER,
        symbol1 TEXT,
        symbol2 TEXT,
        status TEXT,
        winner_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS admin_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT,
        target_id INTEGER,
        details TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    con.commit()
    con.close()


def db(sql: str, params: tuple = (), fetch: str = "none"):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sql, params)
    result = None
    if fetch == "one":
        row = cur.fetchone()
        result = dict(row) if row else None
    elif fetch == "all":
        result = [dict(r) for r in cur.fetchall()]
    con.commit()
    con.close()
    return result


def get_user(uid: int) -> Optional[dict]:
    return db("SELECT * FROM users WHERE user_id=?", (uid,), "one")


def ensure_user(uid: int, username: str = None):
    if not get_user(uid):
        db("INSERT INTO users (user_id, username) VALUES (?, ?)", (uid, username or ""))
    else:
        db("UPDATE users SET username=?, last_seen=CURRENT_TIMESTAMP WHERE user_id=?",
           (username or "", uid))


def add_balance(uid: int, amount: int):
    db("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))


def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


def gen_code(n: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


def check_daily_bonus(uid: int) -> Optional[int]:
    """Возвращает сумму бонуса, если доступен, иначе None."""
    u = get_user(uid)
    today = date.today().isoformat()
    if u["last_bonus"] != today:
        db("UPDATE users SET last_bonus=?, balance=balance+? WHERE user_id=?",
           (today, DAILY_BONUS, uid))
        return DAILY_BONUS
    return None


def check_first_game_bonus(uid: int) -> Optional[int]:
    """Бонус за первую игру дня."""
    u = get_user(uid)
    today = date.today().isoformat()
    if u["last_game_bonus"] != today:
        db("UPDATE users SET last_game_bonus=?, balance=balance+? WHERE user_id=?",
           (today, FIRST_GAME_BONUS, uid))
        return FIRST_GAME_BONUS
    return None


# ============================================================
#  КЛАВИАТУРЫ
# ============================================================
def kb_main(uid: int) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🎮 Игры"),          KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="🎁 Бонус"),         KeyboardButton(text="🏆 Топ-10")],
        [KeyboardButton(text="📖 Помощь")],
    ]
    if is_admin(uid):
        rows.append([KeyboardButton(text="⚙️ Админка")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def kb_games() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌⭕ Крестики PvP (в чате)", callback_data="menu:pvp"),
         InlineKeyboardButton(text="🤖 Крестики с ботом", callback_data="menu:bot")],
        [InlineKeyboardButton(text="🎲 Кубик-дуэль", callback_data="menu:dice"),
         InlineKeyboardButton(text="🔢 Угадай число", callback_data="menu:guess")],
        [InlineKeyboardButton(text="🪙 Монетка", callback_data="menu:coin"),
         InlineKeyboardButton(text="🎰 Слоты", callback_data="menu:slots")],
        [InlineKeyboardButton(text="🎭 Угадай эмодзи", callback_data="menu:emoji"),
         InlineKeyboardButton(text="🃏 Блэкджек", callback_data="menu:bj")],
        [InlineKeyboardButton(text="🎡 Мини-рулетка", callback_data="menu:roulette")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
    ])


def kb_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 К играм", callback_data="menu:games")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
    ])


def kb_pvp_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать игру в этом чате", callback_data="pvp:create")],
        [InlineKeyboardButton(text="🎮 К играм", callback_data="menu:games")],
    ])


def kb_bot_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать игру", callback_data="bot:new")],
        [InlineKeyboardButton(text="🎮 К играм", callback_data="menu:games")],
    ])


def kb_dice_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать ставку", callback_data="dice:create")],
        [InlineKeyboardButton(text="🎮 К играм", callback_data="menu:games")],
    ])


def kb_guess_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Лёгкий 1-50 (ставка 50)",   callback_data="guess:new:easy")],
        [InlineKeyboardButton(text="🟡 Средний 1-100 (ставка 100)", callback_data="guess:new:medium")],
        [InlineKeyboardButton(text="🔴 Сложный 1-1000 (ставка 250)",callback_data="guess:new:hard")],
        [InlineKeyboardButton(text="🎮 К играм", callback_data="menu:games")],
    ])


def kb_bet_menu(game: str, presets: list = None) -> InlineKeyboardMarkup:
    presets = presets or [50, 100, 250, 500]
    rows = [[InlineKeyboardButton(text=f"💰 {p}", callback_data=f"{game}:bet:{p}") for p in presets[:2]],
            [InlineKeyboardButton(text=f"💰 {p}", callback_data=f"{game}:bet:{p}") for p in presets[2:]]]
    rows.append([InlineKeyboardButton(text="✏️ Своя ставка", callback_data=f"{game}:bet:custom")])
    rows.append([InlineKeyboardButton(text="🎮 К играм", callback_data="menu:games")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_board(board: list, prefix: str = "pvp") -> InlineKeyboardMarkup:
    rows = []
    for r in range(3):
        row = []
        for c in range(3):
            i = r * 3 + c
            cell = board[i]
            label = cell if cell in ("❌", "⭕") else "⬜"
            row.append(InlineKeyboardButton(text=label, callback_data=f"{prefix}:move:{i}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="🏳️ Сдаться", callback_data=f"{prefix}:surrender")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def render_board(board: list) -> str:
    return "\n".join(" ".join(board[r*3:r*3+3]) for r in range(3))


def kb_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
        [InlineKeyboardButton(text="👥 Топ-20 юзеров", callback_data="admin:users")],
        [InlineKeyboardButton(text="💰 Выдать монеты", callback_data="admin:give")],
        [InlineKeyboardButton(text="🚫 Забанить", callback_data="admin:ban")],
        [InlineKeyboardButton(text="✅ Разбанить", callback_data="admin:unban")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin:broadcast")],
        [InlineKeyboardButton(text="📜 Список банов", callback_data="admin:banlist")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
    ])


# ============================================================
#  FSM
# ============================================================
class S(StatesGroup):
    dice_bet = State()
    guess_play = State()
    bet_custom = State()
    bj_play = State()
    admin_give_uid = State()
    admin_give_amount = State()
    admin_ban_uid = State()
    admin_ban_reason = State()
    admin_unban_uid = State()
    admin_broadcast = State()


# ============================================================
#  ЛОГИКА КРЕСТИКОВ
# ============================================================
WIN_LINES = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]

def check_winner(board: list) -> Optional[str]:
    for a,b,c in WIN_LINES:
        if board[a] == board[b] == board[c] and board[a] in ("❌","⭕"):
            return board[a]
    if all(x in ("❌","⭕") for x in board):
        return "draw"
    return None


def minimax(board: list, is_bot: bool, alpha=-10, beta=10) -> int:
    res = check_winner(board)
    if res == "⭕": return 10
    if res == "❌": return -10
    if res == "draw": return 0

    if is_bot:
        best = -10
        for i in range(9):
            if board[i] == "⬜":
                board[i] = "⭕"
                score = minimax(board, False, alpha, beta)
                board[i] = "⬜"
                best = max(best, score)
                alpha = max(alpha, score)
                if beta <= alpha: break
        return best
    else:
        best = 10
        for i in range(9):
            if board[i] == "⬜":
                board[i] = "❌"
                score = minimax(board, True, alpha, beta)
                board[i] = "⬜"
                best = min(best, score)
                beta = min(beta, score)
                if beta <= alpha: break
        return best


def bot_smart(board: list) -> int:
    """Всегда оптимальный ход (непобедимый)."""
    best_score = -99
    best_move = None
    for i in range(9):
        if board[i] == "⬜":
            board[i] = "⭕"
            score = minimax(board, False)
            board[i] = "⬜"
            if score > best_score:
                best_score = score
                best_move = i
    return best_move


# ============================================================
#  РОУТЕР + BOT
# ============================================================
router = Router()
bot: Bot = None


# ---------- СТАРТ ----------
@router.message(CommandStart())
async def cmd_start(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    u = get_user(msg.from_user.id)
    if u["is_banned"]:
        await msg.answer(f"🚫 Вы забанены.\nПричина: {u['ban_reason'] or 'не указана'}")
        return

    bonus = check_daily_bonus(msg.from_user.id)
    bonus_text = f"\n\n🎁 <b>Ежедневный бонус: +{bonus} монет!</b>" if bonus else ""

    await msg.answer(
        f"👋 Привет, <b>{msg.from_user.first_name}</b>!\n\n"
        f"🎮 <b>GameHub</b> — 9 игр на монеты:\n"
        f"❌⭕ Крестики PvP · 🤖 Крестики с ботом\n"
        f"🎲 Кубик · 🔢 Угадай число\n"
        f"🪙 Монетка · 🎰 Слоты · 🎭 Эмодзи\n"
        f"🃏 Блэкджек · 🎡 Рулетка\n\n"
        f"💰 Баланс: <b>{get_user(msg.from_user.id)['balance']}</b>"
        f"{bonus_text}",
        reply_markup=kb_main(msg.from_user.id),
    )


@router.message(Command("help"))
@router.message(F.text == "📖 Помощь")
async def cmd_help(msg: Message):
    await msg.answer(
        "📖 <b>Помощь</b>\n\n"
        "<b>Игры:</b>\n"
        "❌⭕ Крестики PvP — только в группах\n"
        "🤖 Крестики с ботом — умный бот\n"
        "🎲 Кубик-дуэль · 🔢 Угадай число\n"
        "🪙 Монетка · 🎰 Слоты · 🎭 Эмодзи\n"
        "🃏 Блэкджек · 🎡 Рулетка\n\n"
        "<b>Бонусы:</b>\n"
        f"🎁 Ежедневный: +{DAILY_BONUS}\n"
        f"🎮 Первая игра дня: +{FIRST_GAME_BONUS}\n\n"
        "<b>Команды:</b>\n"
        "/start /profile /top /bonus /cancel\n"
        "/join КОД — присоединиться к крестикам в группе"
    )


@router.message(Command("cancel"))
async def cmd_cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("❌ Действие отменено.", reply_markup=kb_main(msg.from_user.id))


@router.message(Command("bonus"))
@router.message(F.text == "🎁 Бонус")
async def cmd_bonus(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    b = check_daily_bonus(msg.from_user.id)
    if b:
        await msg.answer(f"🎁 Ежедневный бонус получен: <b>+{b}</b> монет!")
    else:
        await msg.answer("⏳ Бонус уже получен. Приходи завтра!")


@router.callback_query(F.data == "menu:main")
async def cb_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await cb.message.edit_text("🏠 <b>Главное меню</b>", reply_markup=kb_back())
    except TelegramBadRequest:
        pass
    await cb.answer()


@router.callback_query(F.data == "menu:games")
async def cb_games(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await cb.message.edit_text("🎮 <b>Выбери игру:</b>", reply_markup=kb_games())
    except TelegramBadRequest:
        await cb.message.answer("🎮 <b>Выбери игру:</b>", reply_markup=kb_games())
    await cb.answer()


@router.message(F.text == "🎮 Игры")
async def msg_games(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    await msg.answer("🎮 <b>Выбери игру:</b>", reply_markup=kb_games())


# ---------- ПРОФИЛЬ / ТОП ----------
@router.message(F.text == "👤 Профиль")
@router.message(Command("profile"))
async def cmd_profile(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    u = get_user(msg.from_user.id)
    total_pvp = u["pvp_wins"] + u["pvp_losses"] + u["pvp_draws"]
    wr = round(u["pvp_wins"] / total_pvp * 100) if total_pvp else 0
    total_games = (
        u["pvp_wins"]+u["pvp_losses"]+u["pvp_draws"]+
        u["bot_wins"]+u["bot_losses"]+
        u["dice_wins"]+u["dice_losses"]+
        u["guess_wins"]+u["guess_losses"]+
        u["coin_wins"]+u["coin_losses"]+
        u["slots_wins"]+u["slots_losses"]+
        u["emoji_wins"]+u["emoji_losses"]+
        u["bj_wins"]+u["bj_losses"]+
        u["roulette_wins"]+u["roulette_losses"]
    )
    text = (
        f"👤 <b>Профиль</b>\n"
        f"🆔 <code>{u['user_id']}</code>\n"
        f"📅 {u['created_at'][:10]}\n\n"
        f"💰 Баланс: <b>{u['balance']}</b>\n"
        f"🎮 Всего игр: {total_games}\n\n"
        f"❌⭕ PvP: {u['pvp_wins']}П/{u['pvp_losses']}Пр/{u['pvp_draws']}Н ({wr}%)\n"
        f"🤖 Бот: {u['bot_wins']}П/{u['bot_losses']}Пр\n"
        f"🎲 Кубик: {u['dice_wins']}П/{u['dice_losses']}Пр\n"
        f"🔢 Число: {u['guess_wins']}П/{u['guess_losses']}Пр\n"
        f"🪙 Монетка: {u['coin_wins']}П/{u['coin_losses']}Пр\n"
        f"🎰 Слоты: {u['slots_wins']}П/{u['slots_losses']}Пр\n"
        f"🎭 Эмодзи: {u['emoji_wins']}П/{u['emoji_losses']}Пр\n"
        f"🃏 Блэкджек: {u['bj_wins']}П/{u['bj_losses']}Пр\n"
        f"🎡 Рулетка: {u['roulette_wins']}П/{u['roulette_losses']}Пр"
    )
    await msg.answer(text)


@router.message(F.text == "🏆 Топ-10")
@router.message(Command("top"))
async def cmd_top(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 По монетам", callback_data="top:balance"),
         InlineKeyboardButton(text="❌⭕ По PvP", callback_data="top:pvp")],
    ])
    await msg.answer("🏆 <b>Топ-10</b>", reply_markup=kb)


@router.callback_query(F.data.startswith("top:"))
async def cb_top(cb: CallbackQuery):
    mode = cb.data.split(":")[1]
    if mode == "balance":
        rows = db("SELECT user_id, username, balance FROM users WHERE is_banned=0 ORDER BY balance DESC LIMIT 10", fetch="all")
        title = "💰 <b>Топ по монетам</b>\n\n"
        val = lambda r: f"{r['balance']} 💰"
    else:
        rows = db("SELECT user_id, username, pvp_wins FROM users WHERE is_banned=0 ORDER BY pvp_wins DESC LIMIT 10", fetch="all")
        title = "❌⭕ <b>Топ по PvP</b>\n\n"
        val = lambda r: f"{r['pvp_wins']} 🏆"
    medals = ["🥇","🥈","🥉"] + ["▫️"]*7
    text = title + "\n".join(
        f"{medals[i]} {r['username'] or r['user_id']} — {val(r)}"
        for i, r in enumerate(rows)
    )
    try:
        await cb.message.edit_text(text, reply_markup=kb_back())
    except TelegramBadRequest:
        await cb.message.answer(text, reply_markup=kb_back())
    await cb.answer()


# ============================================================
#  ИГРА 1: PvP КРЕСТИКИ — ТОЛЬКО В ЧАТЕ
# ============================================================
@router.callback_query(F.data == "menu:pvp")
async def cb_pvp_menu(cb: CallbackQuery):
    if cb.message.chat.type == ChatType.PRIVATE:
        await cb.answer("❌ Крестики PvP доступны только в групповых чатах! Добавь бота в чат.",
                        show_alert=True)
        return
    await cb.message.edit_text(
        "❌⭕ <b>Крестики-нолики PvP</b>\n\n"
        "Нажми «Создать игру», затем второй игрок вводит /join КОД.",
        reply_markup=kb_pvp_menu(),
    )
    await cb.answer()


@router.message(F.text == "❌⭕ Крестики PvP")
async def msg_pvp(msg: Message):
    if msg.chat.type == ChatType.PRIVATE:
        await msg.answer("❌ Крестики PvP — только в группах. Добавь бота в чат и вызови /pvp.")
        return
    await msg.answer("❌⭕ <b>Крестики PvP</b>\n\nНажми кнопку ниже.", reply_markup=kb_pvp_menu())


@router.message(Command("pvp"))
async def cmd_pvp(msg: Message):
    if msg.chat.type == ChatType.PRIVATE:
        await msg.answer("❌ Только в группах.")
        return
    await msg.answer("❌⭕ <b>Крестики PvP</b>", reply_markup=kb_pvp_menu())


@router.callback_query(F.data == "pvp:create")
async def pvp_create(cb: CallbackQuery):
    if cb.message.chat.type == ChatType.PRIVATE:
        await cb.answer("❌ Только в группах.", show_alert=True); return

    code = gen_code()
    board = "⬜"*9
    symbol1 = random.choice(["❌","⭕"])
    symbol2 = "⭕" if symbol1 == "❌" else "❌"
    db("INSERT INTO games_pvp (code, chat_id, player1_id, board, turn, symbol1, symbol2, status) VALUES (?,?,?,?,?,?,?,?)",
       (code, cb.message.chat.id, cb.from_user.id, board, 1, symbol1, symbol2, "waiting"))
    await cb.message.edit_text(
        f"✅ Игра создана!\n\n"
        f"🔑 Код: <code>{code}</code>\n"
        f"<a href='tg://user?id={cb.from_user.id}'>{cb.from_user.first_name}</a> играет за {symbol1}\n\n"
        f"Второй игрок: <code>/join {code}</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data=f"pvp:cancel:{code}")],
        ]),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("pvp:cancel:"))
async def pvp_cancel(cb: CallbackQuery):
    code = cb.data.split(":")[2]
    db("DELETE FROM games_pvp WHERE code=?", (code,))
    await cb.message.edit_text("❌ Игра отменена.")
    await cb.answer()


@router.message(Command("join"))
async def pvp_join(msg: Message):
    if msg.chat.type == ChatType.PRIVATE:
        await msg.answer("❌ Только в группах."); return
    parts = msg.text.split()
    if len(parts) != 2:
        await msg.answer("Использование: <code>/join КОД</code>"); return
    code = parts[1].upper()
    game = db("SELECT * FROM games_pvp WHERE code=?", (code,), "one")
    if not game:
        await msg.answer("❌ Игра не найдена."); return
    if game["chat_id"] != msg.chat.id:
        await msg.answer("❌ Эта игра в другом чате."); return
    if game["player1_id"] == msg.from_user.id:
        await msg.answer("❌ Ты уже создал эту игру."); return
    if game["status"] != "waiting":
        await msg.answer("❌ Игра уже начата."); return

    ensure_user(msg.from_user.id, msg.from_user.username)
    db("UPDATE games_pvp SET player2_id=?, status='playing' WHERE code=?", (msg.from_user.id, code))
    game = db("SELECT * FROM games_pvp WHERE code=?", (code,), "one")
    board = list(game["board"])

    bonus = check_first_game_bonus(msg.from_user.id)
    bonus_text = f"\n🎮 Бонус за первую игру дня: +{bonus}!" if bonus else ""

    await msg.answer(
        f"🎮 <b>Игра началась!</b>\n\n"
        f"<a href='tg://user?id={game['player1_id']}'>Игрок 1</a> {game['symbol1']} vs "
        f"<a href='tg://user?id={game['player2_id']}'>Игрок 2</a> {game['symbol2']}\n"
        f"Ход: {game['symbol1']}{bonus_text}\n\n{render_board(board)}",
        reply_markup=kb_board(board, prefix=f"pvp:{code}"),
    )


@router.callback_query(F.data.startswith("pvp:") & F.data.contains(":move:"))
async def pvp_move(cb: CallbackQuery):
    parts = cb.data.split(":")
    if len(parts) != 4: await cb.answer("Ошибка."); return
    _, code, _, idx = parts
    idx = int(idx)
    game = db("SELECT * FROM games_pvp WHERE code=?", (code,), "one")
    if not game or game["status"] != "playing":
        await cb.answer("Игра недоступна.", show_alert=True); return
    if cb.message.chat.id != game["chat_id"]:
        await cb.answer("Не тот чат.", show_alert=True); return

    uid = cb.from_user.id
    if uid not in (game["player1_id"], game["player2_id"]):
        await cb.answer("Ты не участник.", show_alert=True); return
    current_uid = game["player1_id"] if game["turn"] == 1 else game["player2_id"]
    if uid != current_uid:
        await cb.answer("Не твой ход!", show_alert=True); return

    board = list(game["board"])
    if board[idx] != "⬜":
        await cb.answer("Клетка занята!", show_alert=True); return

    symbol = game["symbol1"] if game["turn"] == 1 else game["symbol2"]
    board[idx] = symbol
    winner = check_winner(board)

    if winner == "draw":
        db("UPDATE games_pvp SET board=?, status='finished' WHERE code=?", ("".join(board), code))
        db("UPDATE users SET pvp_draws=pvp_draws+1 WHERE user_id IN (?,?)", (game["player1_id"], game["player2_id"]))
        db("UPDATE users SET balance=balance+50 WHERE user_id IN (?,?)", (game["player1_id"], game["player2_id"]))
        try:
            await cb.message.edit_text(
                f"🤝 <b>Ничья!</b> Оба +50 монет.\n\n{render_board(board)}",
                reply_markup=kb_back(),
            )
        except TelegramBadRequest: pass
    elif winner:
        loser_id = game["player2_id"] if game["turn"] == 1 else game["player1_id"]
        db("UPDATE games_pvp SET board=?, status='finished', winner_id=? WHERE code=?", ("".join(board), uid, code))
        db("UPDATE users SET pvp_wins=pvp_wins+1, balance=balance+200 WHERE user_id=?", (uid,))
        db("UPDATE users SET pvp_losses=pvp_losses+1 WHERE user_id=?", (loser_id,))
        try:
            await cb.message.edit_text(
                f"🏆 <b>{symbol} победил!</b> +200 монет\n\n{render_board(board)}",
                reply_markup=kb_back(),
            )
        except TelegramBadRequest: pass
    else:
        db("UPDATE games_pvp SET board=?, turn=? WHERE code=?", ("".join(board), 2 if game["turn"]==1 else 1, code))
        next_sym = game["symbol2"] if game["turn"] == 1 else game["symbol1"]
        next_uid = game["player2_id"] if game["turn"] == 1 else game["player1_id"]
        try:
            await cb.message.edit_text(
                f"Ход: {next_sym} — <a href='tg://user?id={next_uid}'>{'Игрок 1' if game['turn']==1 else 'Игрок 2'}</a>\n\n{render_board(board)}",
                reply_markup=kb_board(board, prefix=f"pvp:{code}"),
            )
        except TelegramBadRequest: pass
    await cb.answer()


@router.callback_query(F.data.startswith("pvp:") & F.data.contains(":surrender"))
async def pvp_surrender(cb: CallbackQuery):
    code = cb.data.split(":")[1]
    game = db("SELECT * FROM games_pvp WHERE code=?", (code,), "one")
    if not game or game["status"] != "playing":
        await cb.answer("Игра недоступна.", show_alert=True); return
    uid = cb.from_user.id
    if uid not in (game["player1_id"], game["player2_id"]):
        await cb.answer("Не участник.", show_alert=True); return
    winner_id = game["player2_id"] if uid == game["player1_id"] else game["player1_id"]
    db("UPDATE games_pvp SET status='finished', winner_id=? WHERE code=?", (winner_id, code))
    db("UPDATE users SET pvp_wins=pvp_wins+1, balance=balance+200 WHERE user_id=?", (winner_id,))
    db("UPDATE users SET pvp_losses=pvp_losses+1 WHERE user_id=?", (uid,))
    try:
        await cb.message.edit_text("🏳️ Сдался! 🏆 Соперник +200 монет.", reply_markup=kb_back())
    except TelegramBadRequest: pass
    await cb.answer()


# ============================================================
#  ИГРА 2: КРЕСТИКИ С БОТОМ (одна сложность — умный)
# ============================================================
@router.callback_query(F.data == "menu:bot")
async def cb_bot_menu(cb: CallbackQuery):
    await cb.message.edit_text(
        "🤖 <b>Крестики с ботом</b>\n\n"
        "Бот играет оптимально — победить можно только вничью 😉\n"
        "Ты — ❌, ходишь первым.",
        reply_markup=kb_bot_menu(),
    )
    await cb.answer()


@router.message(F.text == "🤖 Крестики с ботом")
async def msg_bot(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    await msg.answer("🤖 <b>Крестики с ботом</b>\n\nБот играет оптимально.", reply_markup=kb_bot_menu())


@router.callback_query(F.data == "bot:new")
async def bot_new(cb: CallbackQuery, state: FSMContext):
    board = ["⬜"]*9
    await state.update_data(board=board)
    await cb.message.edit_text(
        f"🤖 Ты — ❌, ходишь первым.\n\n{render_board(board)}",
        reply_markup=kb_board(board, prefix="bot"),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("bot:") & F.data.contains(":move:"))
async def bot_move(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split(":")
    idx = int(parts[2])
    data = await state.get_data()
    board = data.get("board")
    if not board:
        await cb.answer("Игра устарела.", show_alert=True); return
    if board[idx] != "⬜":
        await cb.answer("Клетка занята!", show_alert=True); return

    board[idx] = "❌"
    res = check_winner(board)

    if res is None:
        bot_i = bot_smart(board)
        board[bot_i] = "⭕"
        res = check_winner(board)

    await state.update_data(board=board)
    kb_end = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Ещё раз", callback_data="bot:new")],
        [InlineKeyboardButton(text="🎮 К играм", callback_data="menu:games")],
    ])

    if res == "❌":
        db("UPDATE users SET bot_wins=bot_wins+1, balance=balance+150 WHERE user_id=?", (cb.from_user.id,))
        bonus = check_first_game_bonus(cb.from_user.id)
        bt = f"\n🎮 Бонус дня: +{bonus}" if bonus else ""
        txt = f"🏆 <b>Ты победил!</b> +150 монет{bt}\n\n{render_board(board)}"
        kb = kb_end
    elif res == "⭕":
        db("UPDATE users SET bot_losses=bot_losses+1 WHERE user_id=?", (cb.from_user.id,))
        txt = f"😔 <b>Бот победил.</b>\n\n{render_board(board)}"
        kb = kb_end
    elif res == "draw":
        db("UPDATE users SET balance=balance+25 WHERE user_id=?", (cb.from_user.id,))
        txt = f"🤝 <b>Ничья!</b> +25 монет\n\n{render_board(board)}"
        kb = kb_end
    else:
        txt = f"Ход: ❌\n\n{render_board(board)}"
        kb = kb_board(board, prefix="bot")

    try:
        await cb.message.edit_text(txt, reply_markup=kb)
    except TelegramBadRequest:
        await cb.message.answer(txt, reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data == "bot:surrender")
async def bot_surrender(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("🏳️ Ты сдался.", reply_markup=kb_back())
    await cb.answer()


# ============================================================
#  ИГРА 3: КУБИК-ДУЭЛЬ (PvP, в чате)
# ============================================================
@router.callback_query(F.data == "menu:dice")
async def cb_dice_menu(cb: CallbackQuery):
    u = get_user(cb.from_user.id)
    await cb.message.edit_text(
        f"🎲 <b>Кубик-дуэль</b>\n💰 Баланс: {u['balance']}\n\nСоздай ставку и передай код другу.",
        reply_markup=kb_dice_menu(),
    )
    await cb.answer()


@router.message(F.text == "🎲 Кубик-дуэль")
async def msg_dice(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    u = get_user(msg.from_user.id)
    await msg.answer(f"🎲 <b>Кубик-дуэль</b>\n💰 Баланс: {u['balance']}", reply_markup=kb_dice_menu())


@router.callback_query(F.data == "dice:create")
async def dice_create(cb: CallbackQuery, state: FSMContext):
    await state.set_state(S.dice_bet)
    await cb.message.edit_text("💰 Введи сумму ставки (мин. 10):")
    await cb.answer()


@router.message(S.dice_bet)
async def dice_bet_input(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        await msg.answer("❌ Введи число."); return
    bet = int(msg.text)
    u = get_user(msg.from_user.id)
    if bet < 10:
        await msg.answer("❌ Минимум 10."); return
    if bet > u["balance"]:
        await msg.answer(f"❌ Мало монет. Баланс: {u['balance']}"); return

    code = gen_code()
    db("INSERT INTO games_pvp (code, chat_id, player1_id, board, status, symbol1) VALUES (?,?,?,?,?,?)",
       (code, msg.chat.id, msg.from_user.id, "dice", "waiting", str(bet)))
    await state.clear()
    await msg.answer(
        f"✅ Ставка {bet}!\n🔑 Код: <code>{code}</code>\n\nСоперник: <code>/dice_join {code}</code>",
        reply_markup=kb_back(),
    )


@router.message(Command("dice_join"))
async def dice_join(msg: Message):
    parts = msg.text.split()
    if len(parts) != 2:
        await msg.answer("Использование: /dice_join КОД"); return
    code = parts[1].upper()
    game = db("SELECT * FROM games_pvp WHERE code=? AND board='dice'", (code,), "one")
    if not game or game["status"] != "waiting":
        await msg.answer("❌ Игра недоступна."); return
    if game["player1_id"] == msg.from_user.id:
        await msg.answer("❌ Ты создатель."); return

    ensure_user(msg.from_user.id, msg.from_user.username)
    bet = int(game["symbol1"])
    u = get_user(msg.from_user.id)
    if u["balance"] < bet:
        await msg.answer(f"❌ Нужно {bet} монет."); return

    db("UPDATE games_pvp SET player2_id=?, status='playing' WHERE code=?", (msg.from_user.id, code))

    await msg.answer("🎲 Бросаем...")
    d1 = await bot.send_dice(msg.chat.id, emoji=DiceEmoji.DICE)
    await asyncio.sleep(4)
    d2 = await bot.send_dice(msg.chat.id, emoji=DiceEmoji.DICE)
    await asyncio.sleep(4)

    v1, v2 = d1.dice.value, d2.dice.value
    # Игрок 1 — первый кубик, игрок 2 — второй (по очерёдности создания)
    if v1 > v2:
        winner, loser = game["player1_id"], msg.from_user.id
        txt = f"🏆 <a href='tg://user?id={winner}'>Игрок 1</a> победил! ({v1} vs {v2}) +{bet}💰"
    elif v2 > v1:
        winner, loser = msg.from_user.id, game["player1_id"]
        txt = f"🏆 <a href='tg://user?id={winner}'>Игрок 2</a> победил! ({v2} vs {v1}) +{bet}💰"
    else:
        txt = f"🤝 Ничья ({v1} vs {v2}) — ставки возвращены."
        winner = None

    if winner:
        add_balance(winner, bet)
        add_balance(loser, -bet)
        db("UPDATE users SET dice_wins=dice_wins+1 WHERE user_id=?", (winner,))
        db("UPDATE users SET dice_losses=dice_losses+1 WHERE user_id=?", (loser,))
    db("UPDATE games_pvp SET status='finished', winner_id=? WHERE code=?", (winner, code))
    await msg.answer(txt, reply_markup=kb_back())


# ============================================================
#  ИГРА 4: УГАДАЙ ЧИСЛО (со ставкой)
# ============================================================
GUESS_CFG = {
    "easy":   {"max": 50,   "tries": 7,  "bet": 50},
    "medium": {"max": 100,  "tries": 10, "bet": 100},
    "hard":   {"max": 1000, "tries": 15, "bet": 250},
}


@router.callback_query(F.data == "menu:guess")
async def cb_guess_menu(cb: CallbackQuery):
    await cb.message.edit_text("🔢 <b>Угадай число</b>\n\nСтавка списывается сразу. Победа = ×2.", reply_markup=kb_guess_menu())
    await cb.answer()


@router.message(F.text == "🔢 Угадай число")
async def msg_guess(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    await msg.answer("🔢 <b>Угадай число</b>", reply_markup=kb_guess_menu())


@router.callback_query(F.data.startswith("guess:new:"))
async def guess_new(cb: CallbackQuery, state: FSMContext):
    diff = cb.data.split(":")[2]
    cfg = GUESS_CFG[diff]
    u = get_user(cb.from_user.id)
    if u["balance"] < cfg["bet"]:
        await cb.answer(f"❌ Нужно {cfg['bet']} монет.", show_alert=True); return

    add_balance(cb.from_user.id, -cfg["bet"])
    num = random.randint(1, cfg["max"])
    await state.update_data(diff=diff, num=num, tries=0, bet=cfg["bet"])
    await state.set_state(S.guess_play)
    await cb.message.edit_text(
        f"🔢 Сложность: <b>{diff}</b>\n"
        f"Диапазон: 1–{cfg['max']}\n"
        f"Попыток: {cfg['tries']}\n"
        f"Ставка: {cfg['bet']} (победа = +{cfg['bet']*2})\n\n"
        f"Введи число:"
    )
    await cb.answer()


@router.message(S.guess_play)
async def guess_input(msg: Message, state: FSMContext):
    if not msg.text or not msg.text.lstrip("-").isdigit():
        await msg.answer("❌ Введи число."); return
    guess = int(msg.text)
    data = await state.get_data()
    num = data["num"]; tries = data["tries"] + 1
    cfg = GUESS_CFG[data["diff"]]
    bet = data["bet"]

    if guess == num:
        add_balance(msg.from_user.id, bet * 2)
        db("UPDATE users SET guess_wins=guess_wins+1 WHERE user_id=?", (msg.from_user.id,))
        bonus = check_first_game_bonus(msg.from_user.id)
        bt = f"\n🎮 Бонус дня: +{bonus}" if bonus else ""
        await state.clear()
        await msg.answer(
            f"🎉 <b>Угадал!</b>\nЧисло: {num}\nПопыток: {tries}\n💰 +{bet*2} монет{bt}",
            reply_markup=kb_back(),
        )
        return

    if tries >= cfg["tries"]:
        db("UPDATE users SET guess_losses=guess_losses+1 WHERE user_id=?", (msg.from_user.id,))
        await state.clear()
        await msg.answer(f"😔 <b>Провал.</b> Число: {num}\n💸 -{bet} монет", reply_markup=kb_back())
        return

    await state.update_data(tries=tries)
    hint = "📈 Больше" if guess < num else "📉 Меньше"
    await msg.answer(f"{hint}\nПопытка {tries}/{cfg['tries']}")


# ============================================================
#  ИГРА 5: МОНЕТКА (50/50, ×2)
# ============================================================
@router.callback_query(F.data == "menu:coin")
async def cb_coin(cb: CallbackQuery):
    await cb.message.edit_text("🪙 <b>Монетка</b>\n\nУгадай сторону — выигрыш ×2.", reply_markup=kb_bet_menu("coin", [50, 100, 250, 500]))
    await cb.answer()


@router.message(F.text == "🪙 Монетка")
async def msg_coin(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    await msg.answer("🪙 <b>Монетка</b>", reply_markup=kb_bet_menu("coin", [50, 100, 250, 500]))


@router.callback_query(F.data.startswith("coin:bet:"))
async def coin_bet(cb: CallbackQuery, state: FSMContext):
    val = cb.data.split(":")[2]
    if val == "custom":
        await state.set_state(S.bet_custom)
        await state.update_data(game="coin")
        await cb.message.edit_text("✏️ Введи сумму ставки:")
        await cb.answer(); return

    bet = int(val)
    u = get_user(cb.from_user.id)
    if u["balance"] < bet:
        await cb.answer("❌ Мало монет.", show_alert=True); return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🦅 Орёл", callback_data=f"coin:play:{bet}:o"),
         InlineKeyboardButton(text="🪙 Решка", callback_data=f"coin:play:{bet}:r")],
        [InlineKeyboardButton(text="🎮 К играм", callback_data="menu:games")],
    ])
    await cb.message.edit_text(f"🪙 Ставка {bet}. Выбирай сторону:", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("coin:play:"))
async def coin_play(cb: CallbackQuery):
    _, _, bet_s, choice = cb.data.split(":")
    bet = int(bet_s)
    u = get_user(cb.from_user.id)
    if u["balance"] < bet:
        await cb.answer("❌ Мало монет.", show_alert=True); return

    result = random.choice(["o", "r"])
    if result == choice:
        add_balance(cb.from_user.id, bet)
        db("UPDATE users SET coin_wins=coin_wins+1 WHERE user_id=?", (cb.from_user.id,))
        txt = f"🪙 Выпало: {'🦅 Орёл' if result=='o' else '🪙 Решка'}\n🏆 Победа! +{bet}💰"
    else:
        add_balance(cb.from_user.id, -bet)
        db("UPDATE users SET coin_losses=coin_losses+1 WHERE user_id=?", (cb.from_user.id,))
        txt = f"🪙 Выпало: {'🦅 Орёл' if result=='o' else '🪙 Решка'}\n😔 Проигрыш. -{bet}💰"

    await cb.message.edit_text(txt, reply_markup=kb_back())
    await cb.answer()


# ============================================================
#  ИГРА 6: СЛОТЫ (×0 / ×2 / ×5)
# ============================================================
SLOT_EMOJI = ["🍒","🍋","🍇","💎","7️⃣"]

@router.callback_query(F.data == "menu:slots")
async def cb_slots(cb: CallbackQuery):
    await cb.message.edit_text("🎰 <b>Слоты</b>\n\n3 в ряд: ×5 · 2 в ряд: ×2 · иначе 0", reply_markup=kb_bet_menu("slots", [50, 100, 250, 500]))
    await cb.answer()


@router.message(F.text == "🎰 Слоты")
async def msg_slots(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    await msg.answer("🎰 <b>Слоты</b>", reply_markup=kb_bet_menu("slots", [50, 100, 250, 500]))


@router.callback_query(F.data.startswith("slots:bet:"))
async def slots_bet(cb: CallbackQuery, state: FSMContext):
    val = cb.data.split(":")[2]
    if val == "custom":
        await state.set_state(S.bet_custom)
        await state.update_data(game="slots")
        await cb.message.edit_text("✏️ Введи сумму:")
        await cb.answer(); return

    bet = int(val)
    u = get_user(cb.from_user.id)
    if u["balance"] < bet:
        await cb.answer("❌ Мало монет.", show_alert=True); return

    reel = [random.choice(SLOT_EMOJI) for _ in range(3)]
    # подсчёт: три одинаковых — ×5, два одинаковых — ×2
    if reel[0] == reel[1] == reel[2]:
        win = bet * 5
        add_balance(cb.from_user.id, win - bet)
        db("UPDATE users SET slots_wins=slots_wins+1 WHERE user_id=?", (cb.from_user.id,))
        res = f"🎉 <b>ДЖЕКПОТ!</b> ×5 = +{win-bet}💰"
    elif reel[0] == reel[1] or reel[1] == reel[2] or reel[0] == reel[2]:
        win = bet * 2
        add_balance(cb.from_user.id, win - bet)
        db("UPDATE users SET slots_wins=slots_wins+1 WHERE user_id=?", (cb.from_user.id,))
        res = f"🏆 Два в ряд! ×2 = +{win-bet}💰"
    else:
        add_balance(cb.from_user.id, -bet)
        db("UPDATE users SET slots_losses=slots_losses+1 WHERE user_id=?", (cb.from_user.id,))
        res = f"😔 Мимо. -{bet}💰"

    await cb.message.edit_text(
        f"🎰 | {reel[0]} | {reel[1]} | {reel[2]} |\n\n{res}",
        reply_markup=kb_back(),
    )
    await cb.answer()


# ============================================================
#  ИГРА 7: УГАДАЙ ЭМОДЗИ
# ============================================================
EMOJI_PAIRS = [
    ("🍕", ["Пицца","Бургер","Суши"]),
    ("🚗", ["Машина","Самолёт","Поезд"]),
    ("🐶", ["Собака","Кошка","Лиса"]),
    ("🌈", ["Радуга","Молния","Снег"]),
    ("🍎", ["Яблоко","Груша","Персик"]),
    ("🎸", ["Гитара","Пианино","Скрипка"]),
    ("⚽", ["Футбол","Баскетбол","Теннис"]),
    ("🌙", ["Луна","Солнце","Звезда"]),
    ("🐟", ["Рыба","Кит","Акула"]),
    ("🎂", ["Торт","Пирог","Мороженое"]),
]

@router.callback_query(F.data == "menu:emoji")
async def cb_emoji(cb: CallbackQuery):
    await cb.message.edit_text("🎭 <b>Угадай эмодзи</b>\n\nУгадай, что означает эмодзи. Ставка ×2 при победе.",
                               reply_markup=kb_bet_menu("emoji", [50, 100, 250, 500]))
    await cb.answer()


@router.message(F.text == "🎭 Угадай эмодзи")
async def msg_emoji(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    await msg.answer("🎭 <b>Угадай эмодзи</b>", reply_markup=kb_bet_menu("emoji", [50, 100, 250, 500]))


@router.callback_query(F.data.startswith("emoji:bet:"))
async def emoji_bet(cb: CallbackQuery, state: FSMContext):
    val = cb.data.split(":")[2]
    if val == "custom":
        await state.set_state(S.bet_custom)
        await state.update_data(game="emoji")
        await cb.message.edit_text("✏️ Введи сумму:")
        await cb.answer(); return

    bet = int(val)
    u = get_user(cb.from_user.id)
    if u["balance"] < bet:
        await cb.answer("❌ Мало монет.", show_alert=True); return

    emoji, options = random.choice(EMOJI_PAIRS)
    await state.update_data(bet=bet, answer=options[0])
    opts = options[:]
    random.shuffle(opts)
    rows = [[InlineKeyboardButton(text=o, callback_data=f"emoji:ans:{o}")] for o in opts]
    rows.append([InlineKeyboardButton(text="🎮 К играм", callback_data="menu:games")])
    await cb.message.edit_text(f"🎭 Что означает {emoji}?\n\nСтавка: {bet}",
                               reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await cb.answer()


@router.callback_query(F.data.startswith("emoji:ans:"))
async def emoji_ans(cb: CallbackQuery, state: FSMContext):
    ans = cb.data.split(":", 2)[2]
    data = await state.get_data()
    correct = data.get("answer")
    bet = data.get("bet", 0)

    if ans == correct:
        add_balance(cb.from_user.id, bet)
        db("UPDATE users SET emoji_wins=emoji_wins+1 WHERE user_id=?", (cb.from_user.id,))
        txt = f"🏆 Правильно! +{bet}💰"
    else:
        add_balance(cb.from_user.id, -bet)
        db("UPDATE users SET emoji_losses=emoji_losses+1 WHERE user_id=?", (cb.from_user.id,))
        txt = f"😔 Неверно. Правильно: {correct}. -{bet}💰"

    await state.clear()
    await cb.message.edit_text(txt, reply_markup=kb_back())
    await cb.answer()


# ============================================================
#  ИГРА 8: БЛЭКДЖЕК (упрощённый, 21)
# ============================================================
def bj_draw() -> int:
    return random.choice([2,3,4,5,6,7,8,9,10,10,10,10,11])  # 11 = туз

def bj_sum(hand: list) -> int:
    s = sum(hand)
    while s > 21 and 11 in hand:
        hand[hand.index(11)] = 1
        s = sum(hand)
    return s


@router.callback_query(F.data == "menu:bj")
async def cb_bj(cb: CallbackQuery):
    await cb.message.edit_text("🃏 <b>Блэкджек</b>\n\nНабери 21 или ближе к 21, чем бот. ×2 при победе.",
                               reply_markup=kb_bet_menu("bj", [50, 100, 250, 500]))
    await cb.answer()


@router.message(F.text == "🃏 Блэкджек")
async def msg_bj(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    await msg.answer("🃏 <b>Блэкджек</b>", reply_markup=kb_bet_menu("bj", [50, 100, 250, 500]))


@router.callback_query(F.data.startswith("bj:bet:"))
async def bj_bet(cb: CallbackQuery, state: FSMContext):
    val = cb.data.split(":")[2]
    if val == "custom":
        await state.set_state(S.bet_custom)
        await state.update_data(game="bj")
        await cb.message.edit_text("✏️ Введи сумму:")
        await cb.answer(); return

    bet = int(val)
    u = get_user(cb.from_user.id)
    if u["balance"] < bet:
        await cb.answer("❌ Мало монет.", show_alert=True); return

    player = [bj_draw(), bj_draw()]
    dealer = [bj_draw(), bj_draw()]
    await state.update_data(player=player, dealer=dealer, bet=bet)
    await state.set_state(S.bj_play)

    await show_bj(cb, player, dealer, bet, hide_dealer=True)


async def show_bj(cb: CallbackQuery, player, dealer, bet, hide_dealer=True, extra=""):
    dealer_txt = f"{dealer[0]} + 🂠" if hide_dealer else f"{dealer} = {bj_sum(dealer)}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🃏 Ещё", callback_data="bj:hit"),
         InlineKeyboardButton(text="✋ Хватит", callback_data="bj:stand")],
    ])
    await cb.message.edit_text(
        f"🃏 <b>Блэкджек</b> (ставка {bet})\n\n"
        f"👤 Ты: {player} = <b>{bj_sum(player)}</b>\n"
        f"🤖 Дилер: {dealer_txt}\n{extra}",
        reply_markup=kb,
    )


@router.callback_query(F.data == "bj:hit", S.bj_play)
async def bj_hit(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    player = data["player"]; dealer = data["dealer"]; bet = data["bet"]
    player.append(bj_draw())
    await state.update_data(player=player)

    s = bj_sum(player)
    if s > 21:
        add_balance(cb.from_user.id, -bet)
        db("UPDATE users SET bj_losses=bj_losses+1 WHERE user_id=?", (cb.from_user.id,))
        await state.clear()
        await cb.message.edit_text(f"💥 Перебор! {player} = {s}\n-{bet}💰", reply_markup=kb_back())
        await cb.answer(); return
    await show_bj(cb, player, dealer, bet, hide_dealer=True)
    await cb.answer()


@router.callback_query(F.data == "bj:stand", S.bj_play)
async def bj_stand(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    player = data["player"]; dealer = data["dealer"]; bet = data["bet"]

    while bj_sum(dealer) < 17:
        dealer.append(bj_draw())

    ps, ds = bj_sum(player), bj_sum(dealer)
    if ds > 21 or ps > ds:
        add_balance(cb.from_user.id, bet)
        db("UPDATE users SET bj_wins=bj_wins+1 WHERE user_id=?", (cb.from_user.id,))
        res = f"🏆 Победа! +{bet}💰"
    elif ps == ds:
        res = "🤝 Ничья. Ставка возвращена."
    else:
        add_balance(cb.from_user.id, -bet)
        db("UPDATE users SET bj_losses=bj_losses+1 WHERE user_id=?", (cb.from_user.id,))
        res = f"😔 Проигрыш. -{bet}💰"

    await state.clear()
    await cb.message.edit_text(
        f"🃏 <b>Финал</b>\n\n"
        f"👤 Ты: {player} = {ps}\n"
        f"🤖 Дилер: {dealer} = {ds}\n\n{res}",
        reply_markup=kb_back(),
    )
    await cb.answer()


# ============================================================
#  ИГРА 9: МИНИ-РУЛЕТКА
# ============================================================
@router.callback_query(F.data == "menu:roulette")
async def cb_roulette(cb: CallbackQuery):
    await cb.message.edit_text(
        "🎡 <b>Мини-рулетка</b>\n\n"
        "🔴 Красное ×2 · ⚫ Чёрное ×2 · 🟢 Зеро ×14",
        reply_markup=kb_bet_menu("roulette", [50, 100, 250, 500]),
    )
    await cb.answer()


@router.message(F.text == "🎡 Мини-рулетка")
async def msg_roulette(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    await msg.answer("🎡 <b>Мини-рулетка</b>", reply_markup=kb_bet_menu("roulette", [50, 100, 250, 500]))


@router.callback_query(F.data.startswith("roulette:bet:"))
async def roulette_bet(cb: CallbackQuery, state: FSMContext):
    val = cb.data.split(":")[2]
    if val == "custom":
        await state.set_state(S.bet_custom)
        await state.update_data(game="roulette")
        await cb.message.edit_text("✏️ Введи сумму:")
        await cb.answer(); return

    bet = int(val)
    u = get_user(cb.from_user.id)
    if u["balance"] < bet:
        await cb.answer("❌ Мало монет.", show_alert=True); return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Красное", callback_data=f"roulette:play:{bet}:r"),
         InlineKeyboardButton(text="⚫ Чёрное", callback_data=f"roulette:play:{bet}:b")],
        [InlineKeyboardButton(text="🟢 Зеро", callback_data=f"roulette:play:{bet}:z")],
        [InlineKeyboardButton(text="🎮 К играм", callback_data="menu:games")],
    ])
    await cb.message.edit_text(f"🎡 Ставка {bet}. Выбирай:", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("roulette:play:"))
async def roulette_play(cb: CallbackQuery):
    _, _, bet_s, choice = cb.data.split(":")
    bet = int(bet_s)
    u = get_user(cb.from_user.id)
    if u["balance"] < bet:
        await cb.answer("❌ Мало монет.", show_alert=True); return

    spin = random.choices(["r","b","z"], weights=[48, 48, 4])[0]
    labels = {"r":"🔴 Красное","b":"⚫ Чёрное","z":"🟢 Зеро"}

    if choice == spin:
        mult = 14 if spin == "z" else 2
        add_balance(cb.from_user.id, bet * (mult - 1))
        db("UPDATE users SET roulette_wins=roulette_wins+1 WHERE user_id=?", (cb.from_user.id,))
        txt = f"🎡 Выпало: {labels[spin]}\n🏆 Победа! ×{mult} = +{bet*(mult-1)}💰"
    else:
        add_balance(cb.from_user.id, -bet)
        db("UPDATE users SET roulette_losses=roulette_losses+1 WHERE user_id=?", (cb.from_user.id,))
        txt = f"🎡 Выпало: {labels[spin]}\n😔 Проигрыш. -{bet}💰"

    await cb.message.edit_text(txt, reply_markup=kb_back())
    await cb.answer()


# ============================================================
#  УНИВЕРСАЛЬНЫЙ ВВОД СТАВКИ (custom)
# ============================================================
@router.message(S.bet_custom)
async def bet_custom_input(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        await msg.answer("❌ Число."); return
    bet = int(msg.text)
    if bet < 10:
        await msg.answer("❌ Минимум 10."); return
    data = await state.get_data()
    game = data["game"]
    u = get_user(msg.from_user.id)
    if u["balance"] < bet:
        await msg.answer(f"❌ Мало монет. Баланс: {u['balance']}"); return

    await state.clear()
    # Имитируем callback для соответствующей игры
    if game == "coin":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🦅 Орёл", callback_data=f"coin:play:{bet}:o"),
             InlineKeyboardButton(text="🪙 Решка", callback_data=f"coin:play:{bet}:r")],
        ])
        await msg.answer(f"🪙 Ставка {bet}. Выбирай:", reply_markup=kb)
    elif game == "slots":
        # сразу крутим
        reel = [random.choice(SLOT_EMOJI) for _ in range(3)]
        if reel[0] == reel[1] == reel[2]:
            win = bet * 5; add_balance(msg.from_user.id, win - bet)
            db("UPDATE users SET slots_wins=slots_wins+1 WHERE user_id=?", (msg.from_user.id,))
            res = f"🎉 ДЖЕКПОТ! ×5 = +{win-bet}💰"
        elif reel[0]==reel[1] or reel[1]==reel[2] or reel[0]==reel[2]:
            win = bet * 2; add_balance(msg.from_user.id, win - bet)
            db("UPDATE users SET slots_wins=slots_wins+1 WHERE user_id=?", (msg.from_user.id,))
            res = f"🏆 ×2 = +{win-bet}💰"
        else:
            add_balance(msg.from_user.id, -bet)
            db("UPDATE users SET slots_losses=slots_losses+1 WHERE user_id=?", (msg.from_user.id,))
            res = f"😔 -{bet}💰"
        await msg.answer(f"🎰 | {reel[0]} | {reel[1]} | {reel[2]} |\n\n{res}", reply_markup=kb_back())
    elif game == "emoji":
        emoji, options = random.choice(EMOJI_PAIRS)
        await state.update_data(bet=bet, answer=options[0])
        opts = options[:]; random.shuffle(opts)
        rows = [[InlineKeyboardButton(text=o, callback_data=f"emoji:ans:{o}")] for o in opts]
        await msg.answer(f"🎭 Что означает {emoji}?", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    elif game == "bj":
        player = [bj_draw(), bj_draw()]; dealer = [bj_draw(), bj_draw()]
        await state.update_data(player=player, dealer=dealer, bet=bet)
        await state.set_state(S.bj_play)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🃏 Ещё", callback_data="bj:hit"),
             InlineKeyboardButton(text="✋ Хватит", callback_data="bj:stand")],
        ])
        await msg.answer(
            f"🃏 Блэкджек (ставка {bet})\n👤 Ты: {player} = {bj_sum(player)}\n🤖 Дилер: {dealer[0]} + 🂠",
            reply_markup=kb,
        )
    elif game == "roulette":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔴 Красное", callback_data=f"roulette:play:{bet}:r"),
             InlineKeyboardButton(text="⚫ Чёрное", callback_data=f"roulette:play:{bet}:b")],
            [InlineKeyboardButton(text="🟢 Зеро", callback_data=f"roulette:play:{bet}:z")],
        ])
        await msg.answer(f"🎡 Ставка {bet}.", reply_markup=kb)


# ============================================================
#  АДМИНКА
# ============================================================
@router.message(F.text == "⚙️ Админка")
@router.message(Command("admin"))
async def admin_menu(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Нет доступа."); return
    await msg.answer("⚙️ <b>Админ-панель</b>", reply_markup=kb_admin())


@router.callback_query(F.data == "admin:stats")
async def admin_stats(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔", show_alert=True); return
    total = db("SELECT COUNT(*) c FROM users", fetch="one")["c"]
    day_ago = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    active = db("SELECT COUNT(*) c FROM users WHERE last_seen > ?", (day_ago,), "one")["c"]
    pvp = db("SELECT COUNT(*) c FROM games_pvp WHERE board!='dice'", fetch="one")["c"]
    total_bal = db("SELECT COALESCE(SUM(balance),0) c FROM users", fetch="one")["c"]
    await cb.message.edit_text(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Юзеров: {total}\n"
        f"🔥 Активных 24ч: {active}\n"
        f"❌⭕ PvP игр: {pvp}\n"
        f"💰 Сумма балансов: {total_bal}",
        reply_markup=kb_admin(),
    )
    await cb.answer()


@router.callback_query(F.data == "admin:users")
async def admin_users(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔", show_alert=True); return
    rows = db("SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT 20", fetch="all")
    text = "👥 <b>Топ-20</b>\n\n" + "\n".join(
        f"{i+1}. {r['username'] or '—'} | <code>{r['user_id']}</code> | {r['balance']}💰"
        for i, r in enumerate(rows)
    )
    await cb.message.edit_text(text, reply_markup=kb_admin())
    await cb.answer()


@router.callback_query(F.data == "admin:give")
async def admin_give(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔", show_alert=True); return
    await state.set_state(S.admin_give_uid)
    await cb.message.edit_text("💰 Введи user_id:"); await cb.answer()


@router.message(S.admin_give_uid)
async def admin_give_uid(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    if not msg.text.isdigit(): await msg.answer("❌ Число."); return
    uid = int(msg.text)
    if not get_user(uid): await msg.answer("❌ Не найден."); return
    await state.update_data(target=uid)
    await state.set_state(S.admin_give_amount)
    await msg.answer("💰 Введи сумму:")


@router.message(S.admin_give_amount)
async def admin_give_amt(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    try: amount = int(msg.text)
    except ValueError: await msg.answer("❌ Число."); return
    data = await state.get_data(); target = data["target"]
    add_balance(target, amount)
    db("INSERT INTO admin_log (admin_id, action, target_id, details) VALUES (?,?,?,?)",
       (msg.from_user.id, "give_coins", target, str(amount)))
    await state.clear()
    await msg.answer(f"✅ {amount} монет → <code>{target}</code>", reply_markup=kb_admin())


@router.callback_query(F.data == "admin:ban")
async def admin_ban(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔", show_alert=True); return
    await state.set_state(S.admin_ban_uid)
    await cb.message.edit_text("🚫 user_id для бана:"); await cb.answer()


@router.message(S.admin_ban_uid)
async def admin_ban_uid(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    if not msg.text.isdigit(): await msg.answer("❌ Число."); return
    uid = int(msg.text)
    if not get_user(uid): await msg.answer("❌ Не найден."); return
    await state.update_data(target=uid)
    await state.set_state(S.admin_ban_reason)
    await msg.answer("🚫 Причина:")


@router.message(S.admin_ban_reason)
async def admin_ban_reason(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    data = await state.get_data(); target = data["target"]
    db("UPDATE users SET is_banned=1, ban_reason=? WHERE user_id=?", (msg.text, target))
    db("INSERT INTO admin_log (admin_id, action, target_id, details) VALUES (?,?,?,?)",
       (msg.from_user.id, "ban", target, msg.text))
    await state.clear()
    await msg.answer(f"🚫 <code>{target}</code> забанен.", reply_markup=kb_admin())


@router.callback_query(F.data == "admin:unban")
async def admin_unban(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔", show_alert=True); return
    await state.set_state(S.admin_unban_uid)
    await cb.message.edit_text("✅ user_id для разбана:"); await cb.answer()


@router.message(S.admin_unban_uid)
async def admin_unban_uid(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    if not msg.text.isdigit(): await msg.answer("❌ Число."); return
    uid = int(msg.text)
    db("UPDATE users SET is_banned=0, ban_reason=NULL WHERE user_id=?", (uid,))
    db("INSERT INTO admin_log (admin_id, action, target_id) VALUES (?,?,?)",
       (msg.from_user.id, "unban", uid))
    await state.clear()
    await msg.answer(f"✅ <code>{uid}</code> разбанен.", reply_markup=kb_admin())


@router.callback_query(F.data == "admin:banlist")
async def admin_banlist(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔", show_alert=True); return
    rows = db("SELECT user_id, username, ban_reason FROM users WHERE is_banned=1", fetch="all")
    text = "📜 Пусто." if not rows else "📜 <b>Баны</b>\n\n" + "\n".join(
        f"🚫 <code>{r['user_id']}</code> — {r['ban_reason'] or '—'}" for r in rows
    )
    await cb.message.edit_text(text, reply_markup=kb_admin())
    await cb.answer()


@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔", show_alert=True); return
    await state.set_state(S.admin_broadcast)
    await cb.message.edit_text("📢 Текст рассылки:"); await cb.answer()


@router.message(S.admin_broadcast)
async def admin_broadcast_send(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    text = msg.text
    await state.clear()
    users = db("SELECT user_id FROM users WHERE is_banned=0", fetch="all")
    progress = await msg.answer(f"📢 0/{len(users)}")
    sent = 0
    for u in users:
        try:
            await bot.send_message(u["user_id"], f"📢 <b>Рассылка</b>\n\n{text}")
            sent += 1
        except TelegramForbiddenError:
            pass
        except Exception as e:
            log.warning(f"BC {u['user_id']}: {e}")
        if sent % 20 == 0:
            try: await progress.edit_text(f"📢 {sent}/{len(users)}")
            except TelegramBadRequest: pass
        await asyncio.sleep(0.05)
    await progress.edit_text(f"✅ {sent}/{len(users)}", reply_markup=kb_admin())


# ============================================================
#  ЗАПУСК
# ============================================================
async def main():
    global bot
    db_init()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    log.info("🚀 GameHub v2 запущен")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("🛑 Остановлен")
