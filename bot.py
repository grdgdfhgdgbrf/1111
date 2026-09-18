# ============================================================
#  GameHub — Telegram-бот: 4 игры + админка
#  Python 3.11+ | aiogram 3.x | SQLite
#  Один файл. Запуск: python main.py
# ============================================================

import asyncio
import logging
import os
import random
import string
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, DiceEmoji
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
ADMIN_IDS = "5356400377"

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
        pvp_wins INTEGER DEFAULT 0,
        pvp_losses INTEGER DEFAULT 0,
        pvp_draws INTEGER DEFAULT 0,
        bot_easy_wins INTEGER DEFAULT 0,
        bot_medium_wins INTEGER DEFAULT 0,
        bot_hard_wins INTEGER DEFAULT 0,
        dice_wins INTEGER DEFAULT 0,
        dice_losses INTEGER DEFAULT 0,
        guess_wins INTEGER DEFAULT 0,
        guess_losses INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        ban_reason TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_seen TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS games_pvp (
        code TEXT PRIMARY KEY,
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
    CREATE TABLE IF NOT EXISTS games_dice (
        code TEXT PRIMARY KEY,
        player1_id INTEGER,
        player2_id INTEGER,
        bet INTEGER,
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


# ============================================================
#  КЛАВИАТУРЫ
# ============================================================
def kb_main(uid: int) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🎮 Крестики-нолики"), KeyboardButton(text="🤖 Крестики с ботом")],
        [KeyboardButton(text="🎲 Кубик-дуэль"),     KeyboardButton(text="🔢 Угадай число")],
        [KeyboardButton(text="👤 Профиль"),         KeyboardButton(text="🏆 Топ-10")],
    ]
    if is_admin(uid):
        rows.append([KeyboardButton(text="⚙️ Админка")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def kb_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")]])


def kb_pvp_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать игру", callback_data="pvp:create")],
        [InlineKeyboardButton(text="🔗 Присоединиться", callback_data="pvp:join_info")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
    ])


def kb_bot_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Легко",  callback_data="bot:new:easy")],
        [InlineKeyboardButton(text="🟡 Средне", callback_data="bot:new:medium")],
        [InlineKeyboardButton(text="🔴 Сложно", callback_data="bot:new:hard")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
    ])


def kb_dice_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать ставку", callback_data="dice:create")],
        [InlineKeyboardButton(text="🔗 Присоединиться", callback_data="dice:join_info")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
    ])


def kb_guess_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Лёгкий 1-50",   callback_data="guess:new:easy")],
        [InlineKeyboardButton(text="🟡 Средний 1-100", callback_data="guess:new:medium")],
        [InlineKeyboardButton(text="🔴 Сложный 1-1000",callback_data="guess:new:hard")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
    ])


def kb_board(board: list, prefix: str = "pvp", disabled: bool = False) -> InlineKeyboardMarkup:
    rows = []
    for r in range(3):
        row = []
        for c in range(3):
            i = r * 3 + c
            cell = board[i]
            label = cell if cell in ("❌", "⭕") else "⬜"
            row.append(InlineKeyboardButton(text=label, callback_data=f"{prefix}:move:{i}"))
        rows.append(row)
    if not disabled:
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
    pvp_join = State()
    dice_bet = State()
    dice_join = State()
    guess_play = State()
    admin_give_uid = State()
    admin_give_amount = State()
    admin_ban_uid = State()
    admin_ban_reason = State()
    admin_unban_uid = State()
    admin_broadcast = State()


# ============================================================
#  ЛОГИКА ИГР
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


def bot_easy(board: list) -> int:
    return random.choice([i for i,x in enumerate(board) if x == "⬜"])


def bot_medium(board: list) -> int:
    empties = [i for i,x in enumerate(board) if x == "⬜"]
    for i in empties:
        board[i] = "⭕"
        if check_winner(board) == "⭕":
            board[i] = "⬜"; return i
        board[i] = "⬜"
    for i in empties:
        board[i] = "❌"
        if check_winner(board) == "❌":
            board[i] = "⬜"; return i
        board[i] = "⬜"
    return random.choice(empties)


def bot_hard(board: list) -> int:
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
#  РОУТЕР
# ============================================================
router = Router()


# ---------- СТАРТ / МЕНЮ ----------
@router.message(CommandStart())
async def cmd_start(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    u = get_user(msg.from_user.id)
    if u["is_banned"]:
        await msg.answer(f"🚫 Вы забанены.\nПричина: {u['ban_reason'] or 'не указана'}")
        return
    await msg.answer(
        f"👋 Привет, <b>{msg.from_user.first_name}</b>!\n\n"
        f"🎮 <b>GameHub</b> — 4 игры в одном боте:\n"
        f"❌⭕ Крестики (PvP) · 🤖 Крестики с ботом\n"
        f"🎲 Кубик-дуэль · 🔢 Угадай число\n\n"
        f"Выбирай игру 👇",
        reply_markup=kb_main(msg.from_user.id),
    )


@router.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "📖 <b>Помощь</b>\n\n"
        "/start — меню\n/profile — профиль\n/top — топ-10\n"
        "/cancel — отмена действия\n"
        + ("/admin — админка\n" if is_admin(msg.from_user.id) else "")
    )


@router.message(Command("cancel"))
async def cmd_cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("❌ Действие отменено.", reply_markup=kb_main(msg.from_user.id))


@router.callback_query(F.data == "menu:main")
async def cb_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await cb.message.edit_text("🏠 <b>Главное меню</b>\nВыбирай игру 👇", reply_markup=kb_back())
    except TelegramBadRequest:
        pass
    await cb.answer()


# ---------- ПРОФИЛЬ ----------
@router.message(F.text == "👤 Профиль")
@router.message(Command("profile"))
async def cmd_profile(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    u = get_user(msg.from_user.id)
    total_pvp = u["pvp_wins"] + u["pvp_losses"] + u["pvp_draws"]
    wr = round(u["pvp_wins"] / total_pvp * 100) if total_pvp else 0
    text = (
        f"👤 <b>Профиль</b>\n"
        f"🆔 <code>{u['user_id']}</code>\n"
        f"📅 Регистрация: {u['created_at'][:10]}\n\n"
        f"💰 Баланс: <b>{u['balance']}</b> монет\n\n"
        f"❌⭕ <b>Крестики PvP</b>: {u['pvp_wins']}П / {u['pvp_losses']}Пр / {u['pvp_draws']}Н (винрейт {wr}%)\n"
        f"🤖 <b>Крестики с ботом</b>:\n"
        f"   🟢 {u['bot_easy_wins']} · 🟡 {u['bot_medium_wins']} · 🔴 {u['bot_hard_wins']}\n"
        f"🎲 <b>Кубик</b>: {u['dice_wins']}П / {u['dice_losses']}Пр\n"
        f"🔢 <b>Угадай число</b>: {u['guess_wins']}П / {u['guess_losses']}Пр"
    )
    await msg.answer(text)


@router.message(F.text == "🏆 Топ-10")
@router.message(Command("top"))
async def cmd_top(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 По монетам", callback_data="top:balance"),
         InlineKeyboardButton(text="❌⭕ По PvP", callback_data="top:pvp")],
    ])
    await msg.answer("🏆 <b>Топ-10</b>\nВыбери категорию:", reply_markup=kb)


@router.callback_query(F.data.startswith("top:"))
async def cb_top(cb: CallbackQuery):
    mode = cb.data.split(":")[1]
    if mode == "balance":
        rows = db("SELECT user_id, username, balance FROM users WHERE is_banned=0 ORDER BY balance DESC LIMIT 10", fetch="all")
        title = "💰 <b>Топ-10 по монетам</b>\n\n"
        val = lambda r: f"{r['balance']} 💰"
    else:
        rows = db("SELECT user_id, username, pvp_wins FROM users WHERE is_banned=0 ORDER BY pvp_wins DESC LIMIT 10", fetch="all")
        title = "❌⭕ <b>Топ-10 по победам в PvP</b>\n\n"
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
#  ИГРА 1: PvP КРЕСТИКИ
# ============================================================
@router.message(F.text == "🎮 Крестики-нолики")
async def pvp_menu(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    await msg.answer("🎮 <b>Крестики-нолики PvP</b>\n\nСоздай игру и передай код другу.", reply_markup=kb_pvp_menu())


@router.callback_query(F.data == "pvp:create")
async def pvp_create(cb: CallbackQuery):
    code = gen_code()
    board = "⬜"*9
    symbol1 = random.choice(["❌","⭕"])
    symbol2 = "⭕" if symbol1 == "❌" else "❌"
    db("INSERT INTO games_pvp (code, player1_id, board, turn, symbol1, symbol2, status) VALUES (?,?,?,?,?,?,?)",
       (code, cb.from_user.id, board, 1, symbol1, symbol2, "waiting"))
    await cb.message.edit_text(
        f"✅ Игра создана!\n\n"
        f"🔑 Код: <code>{code}</code>\n"
        f"Ты играешь за {symbol1}\n\n"
        f"Отправь другу: <code>/join {code}</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data=f"pvp:cancel:{code}")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
        ]),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("pvp:cancel:"))
async def pvp_cancel(cb: CallbackQuery):
    code = cb.data.split(":")[2]
    db("DELETE FROM games_pvp WHERE code=?", (code,))
    await cb.message.edit_text("❌ Игра отменена.", reply_markup=kb_back())
    await cb.answer()


@router.message(Command("join"))
async def pvp_join(msg: Message):
    parts = msg.text.split()
    if len(parts) != 2:
        await msg.answer("Использование: <code>/join КОД</code>")
        return
    code = parts[1].upper()
    game = db("SELECT * FROM games_pvp WHERE code=?", (code,), "one")
    if not game:
        await msg.answer("❌ Игра не найдена.")
        return
    if game["player1_id"] == msg.from_user.id:
        await msg.answer("❌ Ты уже создал эту игру.")
        return
    if game["status"] != "waiting":
        await msg.answer("❌ Игра уже начата или завершена.")
        return

    ensure_user(msg.from_user.id, msg.from_user.username)
    db("UPDATE games_pvp SET player2_id=?, status='playing' WHERE code=?", (msg.from_user.id, code))
    game = db("SELECT * FROM games_pvp WHERE code=?", (code,), "one")

    board = list(game["board"])
    text = f"🎮 <b>Игра началась!</b>\n\nТвой ход: {game['symbol1']}\n\n{render_board(board)}"

    try:
        await bot.send_message(game["player1_id"], text, reply_markup=kb_board(board, prefix=f"pvp:{code}"))
    except TelegramForbiddenError:
        pass
    await msg.answer(text, reply_markup=kb_board(board, prefix=f"pvp:{code}"))


@router.callback_query(F.data.startswith("pvp:") & F.data.contains(":move:"))
async def pvp_move(cb: CallbackQuery):
    parts = cb.data.split(":")
    if len(parts) != 4:
        await cb.answer("Ошибка."); return
    _, code, _, idx = parts
    idx = int(idx)
    game = db("SELECT * FROM games_pvp WHERE code=?", (code,), "one")
    if not game or game["status"] != "playing":
        await cb.answer("Игра недоступна.", show_alert=True); return

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
        txt = f"🤝 <b>Ничья!</b>\n\n{render_board(board)}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Реванш", callback_data=f"pvp:rematch:{code}")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
        ])
    elif winner:
        loser_id = game["player2_id"] if game["turn"] == 1 else game["player1_id"]
        db("UPDATE games_pvp SET board=?, status='finished', winner_id=? WHERE code=?", ("".join(board), uid, code))
        db("UPDATE users SET pvp_wins=pvp_wins+1 WHERE user_id=?", (uid,))
        db("UPDATE users SET pvp_losses=pvp_losses+1 WHERE user_id=?", (loser_id,))
        txt = f"🏆 <b>{symbol} победил!</b>\n\n{render_board(board)}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Реванш", callback_data=f"pvp:rematch:{code}")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
        ])
    else:
        db("UPDATE games_pvp SET board=?, turn=? WHERE code=?", ("".join(board), 2 if game["turn"]==1 else 1, code))
        next_uid = game["player2_id"] if game["turn"] == 1 else game["player1_id"]
        next_sym = game["symbol2"] if game["turn"] == 1 else game["symbol1"]
        txt = f"Ход: {next_sym}\n\n{render_board(board)}"
        kb = kb_board(board, prefix=f"pvp:{code}")

    for pid in (game["player1_id"], game["player2_id"]):
        try:
            await bot.send_message(pid, txt, reply_markup=kb)
        except TelegramForbiddenError:
            pass
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    await cb.answer()


@router.callback_query(F.data.startswith("pvp:") & F.data.contains(":surrender"))
async def pvp_surrender(cb: CallbackQuery):
    parts = cb.data.split(":")
    code = parts[1]
    game = db("SELECT * FROM games_pvp WHERE code=?", (code,), "one")
    if not game or game["status"] != "playing":
        await cb.answer("Игра недоступна.", show_alert=True); return
    uid = cb.from_user.id
    if uid not in (game["player1_id"], game["player2_id"]):
        await cb.answer("Не участник.", show_alert=True); return
    winner_id = game["player2_id"] if uid == game["player1_id"] else game["player1_id"]
    db("UPDATE games_pvp SET status='finished', winner_id=? WHERE code=?", (winner_id, code))
    db("UPDATE users SET pvp_wins=pvp_wins+1 WHERE user_id=?", (winner_id,))
    db("UPDATE users SET pvp_losses=pvp_losses+1 WHERE user_id=?", (uid,))
    txt = "🏳️ Соперник сдался! 🏆 Победа!"
    for pid in (game["player1_id"], game["player2_id"]):
        try:
            await bot.send_message(pid, txt, reply_markup=kb_back())
        except TelegramForbiddenError:
            pass
    await cb.answer("Ты сдался.")


@router.callback_query(F.data.startswith("pvp:rematch:"))
async def pvp_rematch(cb: CallbackQuery):
    code = cb.data.split(":")[2]
    game = db("SELECT * FROM games_pvp WHERE code=?", (code,), "one")
    if not game:
        await cb.answer("Игра не найдена.", show_alert=True); return
    new_code = gen_code()
    s1, s2 = game["symbol2"], game["symbol1"]
    db("INSERT INTO games_pvp (code, player1_id, player2_id, board, turn, symbol1, symbol2, status) VALUES (?,?,?,?,?,?,?,?)",
       (new_code, game["player1_id"], game["player2_id"], "⬜"*9, 1, s1, s2, "playing"))
    board = ["⬜"]*9
    text = f"🔄 <b>Реванш!</b>\nТвой ход: {s1}\n\n{render_board(board)}"
    for pid in (game["player1_id"], game["player2_id"]):
        try:
            await bot.send_message(pid, text, reply_markup=kb_board(board, prefix=f"pvp:{new_code}"))
        except TelegramForbiddenError:
            pass
    await cb.answer()


# ============================================================
#  ИГРА 2: КРЕСТИКИ С БОТОМ
# ============================================================
@router.message(F.text == "🤖 Крестики с ботом")
async def bot_menu(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    await msg.answer("🤖 <b>Крестики с ботом</b>\n\nВыбери сложность:", reply_markup=kb_bot_menu())


@router.callback_query(F.data.startswith("bot:new:"))
async def bot_new(cb: CallbackQuery, state: FSMContext):
    diff = cb.data.split(":")[2]
    board = ["⬜"]*9
    await state.update_data(diff=diff, board=board)
    await cb.message.edit_text(
        f"🤖 Сложность: <b>{ {'easy':'🟢 Легко','medium':'🟡 Средне','hard':'🔴 Сложно'}[diff] }</b>\n"
        f"Ты — ❌, ходишь первым.\n\n{render_board(board)}",
        reply_markup=kb_board(board, prefix=f"bot:{diff}"),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("bot:") & F.data.contains(":move:"))
async def bot_move(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split(":")
    diff, _, idx = parts[1], parts[2], int(parts[3])
    data = await state.get_data()
    board = data.get("board")
    if not board:
        await cb.answer("Игра устарела. Начни заново.", show_alert=True); return
    if board[idx] != "⬜":
        await cb.answer("Клетка занята!", show_alert=True); return

    board[idx] = "❌"
    res = check_winner(board)

    if res is None:
        if diff == "easy":   bot_i = bot_easy(board)
        elif diff == "medium": bot_i = bot_medium(board)
        else: bot_i = bot_hard(board)
        board[bot_i] = "⭕"
        res = check_winner(board)

    await state.update_data(board=board)

    if res == "❌":
        db(f"UPDATE users SET bot_{diff}_wins = bot_{diff}_wins + 1 WHERE user_id=?", (cb.from_user.id,))
        txt = f"🏆 <b>Ты победил!</b>\n\n{render_board(board)}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Ещё раз", callback_data=f"bot:new:{diff}")],
            [InlineKeyboardButton(text="🎚 Сменить сложность", callback_data="bot:menu")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
        ])
    elif res == "⭕":
        txt = f"😔 <b>Бот победил.</b>\n\n{render_board(board)}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Ещё раз", callback_data=f"bot:new:{diff}")],
            [InlineKeyboardButton(text="🎚 Сменить сложность", callback_data="bot:menu")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
        ])
    elif res == "draw":
        txt = f"🤝 <b>Ничья!</b>\n\n{render_board(board)}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Ещё раз", callback_data=f"bot:new:{diff}")],
            [InlineKeyboardButton(text="🎚 Сменить сложность", callback_data="bot:menu")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
        ])
    else:
        txt = f"Ход: ❌\n\n{render_board(board)}"
        kb = kb_board(board, prefix=f"bot:{diff}")

    try:
        await cb.message.edit_text(txt, reply_markup=kb)
    except TelegramBadRequest:
        await cb.message.answer(txt, reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data == "bot:menu")
async def bot_menu_cb(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("🤖 <b>Крестики с ботом</b>\n\nВыбери сложность:", reply_markup=kb_bot_menu())
    await cb.answer()


@router.callback_query(F.data.startswith("bot:") & F.data.contains(":surrender"))
async def bot_surrender(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("🏳️ Ты сдался. Бот победил.", reply_markup=kb_back())
    await cb.answer()


# ============================================================
#  ИГРА 3: КУБИК-ДУЭЛЬ
# ============================================================
@router.message(F.text == "🎲 Кубик-дуэль")
async def dice_menu(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    u = get_user(msg.from_user.id)
    await msg.answer(f"🎲 <b>Кубик-дуэль</b>\n\n💰 Баланс: <b>{u['balance']}</b>", reply_markup=kb_dice_menu())


@router.callback_query(F.data == "dice:create")
async def dice_create(cb: CallbackQuery, state: FSMContext):
    await state.set_state(S.dice_bet)
    await cb.message.edit_text("💰 Введи сумму ставки (целое число, минимум 10):")
    await cb.answer()


@router.message(S.dice_bet)
async def dice_bet_input(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        await msg.answer("❌ Введи целое число."); return
    bet = int(msg.text)
    u = get_user(msg.from_user.id)
    if bet < 10:
        await msg.answer("❌ Минимум 10 монет."); return
    if bet > u["balance"]:
        await msg.answer(f"❌ Недостаточно монет. Баланс: {u['balance']}"); return

    code = gen_code()
    db("INSERT INTO games_dice (code, player1_id, bet, status) VALUES (?,?,?,?)",
       (code, msg.from_user.id, bet, "waiting"))
    await state.clear()
    await msg.answer(
        f"✅ Ставка создана!\n\n🔑 Код: <code>{code}</code>\n💰 Ставка: {bet}\n\n"
        f"Отправь другу: <code>/dice_join {code}</code>",
        reply_markup=kb_back(),
    )


@router.message(Command("dice_join"))
async def dice_join(msg: Message):
    parts = msg.text.split()
    if len(parts) != 2:
        await msg.answer("Использование: <code>/dice_join КОД</code>"); return
    code = parts[1].upper()
    game = db("SELECT * FROM games_dice WHERE code=?", (code,), "one")
    if not game or game["status"] != "waiting":
        await msg.answer("❌ Игра недоступна."); return
    if game["player1_id"] == msg.from_user.id:
        await msg.answer("❌ Ты создатель этой ставки."); return

    ensure_user(msg.from_user.id, msg.from_user.username)
    u = get_user(msg.from_user.id)
    if u["balance"] < game["bet"]:
        await msg.answer(f"❌ Недостаточно монет. Нужно: {game['bet']}"); return

    db("UPDATE games_dice SET player2_id=?, status='playing' WHERE code=?", (msg.from_user.id, code))

    await msg.answer(f"🎲 Бросаем кубики...")
    try:
        await bot.send_message(game["player1_id"], "🎲 Бросаем кубики...")
    except TelegramForbiddenError:
        pass

    await asyncio.sleep(1)
    d1 = await bot.send_dice(game["player1_id"], emoji=DiceEmoji.DICE)
    d2 = await bot.send_dice(msg.from_user.id, emoji=DiceEmoji.DICE)
    await asyncio.sleep(4)

    v1, v2 = d1.dice.value, d2.dice.value
    if v1 > v2:
        winner, loser = game["player1_id"], msg.from_user.id
        txt = f"🏆 Игрок 1 победил! ({v1} vs {v2})"
    elif v2 > v1:
        winner, loser = msg.from_user.id, game["player1_id"]
        txt = f"🏆 Игрок 2 победил! ({v2} vs {v1})"
    else:
        txt = f"🤝 Ничья! ({v1} vs {v2}) — ставки возвращены."
        winner = None

    if winner:
        add_balance(winner, game["bet"])
        add_balance(loser, -game["bet"])
        db("UPDATE users SET dice_wins=dice_wins+1 WHERE user_id=?", (winner,))
        db("UPDATE users SET dice_losses=dice_losses+1 WHERE user_id=?", (loser,))
    db("UPDATE games_dice SET status='finished', winner_id=? WHERE code=?", (winner, code))

    for pid in (game["player1_id"], msg.from_user.id):
        try:
            await bot.send_message(pid, txt, reply_markup=kb_back())
        except TelegramForbiddenError:
            pass


@router.callback_query(F.data == "dice:join_info")
async def dice_join_info(cb: CallbackQuery):
    await cb.message.edit_text("🔗 Отправь команду <code>/dice_join КОД</code> в этот чат.", reply_markup=kb_back())
    await cb.answer()


# ============================================================
#  ИГРА 4: УГАДАЙ ЧИСЛО
# ============================================================
@router.message(F.text == "🔢 Угадай число")
async def guess_menu(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    await msg.answer("🔢 <b>Угадай число</b>\n\nВыбери сложность:", reply_markup=kb_guess_menu())


GUESS_CFG = {
    "easy":   {"max": 50,   "tries": 7,  "reward": 50},
    "medium": {"max": 100,  "tries": 10, "reward": 100},
    "hard":   {"max": 1000, "tries": 15, "reward": 250},
}


@router.callback_query(F.data.startswith("guess:new:"))
async def guess_new(cb: CallbackQuery, state: FSMContext):
    diff = cb.data.split(":")[2]
    cfg = GUESS_CFG[diff]
    num = random.randint(1, cfg["max"])
    await state.update_data(diff=diff, num=num, tries=0)
    await state.set_state(S.guess_play)
    await cb.message.edit_text(
        f"🔢 Сложность: <b>{diff}</b>\n"
        f"Диапазон: 1–{cfg['max']}\n"
        f"Попыток: {cfg['tries']}\n\n"
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

    if guess == num:
        add_balance(msg.from_user.id, cfg["reward"])
        db("UPDATE users SET guess_wins=guess_wins+1 WHERE user_id=?", (msg.from_user.id,))
        await state.clear()
        await msg.answer(
            f"🎉 <b>Угадал!</b>\nЧисло: {num}\nПопыток: {tries}\n💰 +{cfg['reward']} монет",
            reply_markup=kb_back(),
        )
        return

    if tries >= cfg["tries"]:
        db("UPDATE users SET guess_losses=guess_losses+1 WHERE user_id=?", (msg.from_user.id,))
        await state.clear()
        await msg.answer(
            f"😔 <b>Попытки кончились.</b>\nЧисло было: {num}",
            reply_markup=kb_back(),
        )
        return

    await state.update_data(tries=tries)
    hint = "📈 Больше" if guess < num else "📉 Меньше"
    await msg.answer(f"{hint}\nПопытка {tries}/{cfg['tries']}")


# ============================================================
#  АДМИНКА
# ============================================================
def admin_only(uid: int) -> bool:
    return is_admin(uid)


@router.message(F.text == "⚙️ Админка")
@router.message(Command("admin"))
async def admin_menu(msg: Message):
    if not admin_only(msg.from_user.id):
        await msg.answer("⛔ Доступ запрещён."); return
    await msg.answer("⚙️ <b>Админ-панель</b>", reply_markup=kb_admin())


@router.callback_query(F.data == "admin:stats")
async def admin_stats(cb: CallbackQuery):
    if not admin_only(cb.from_user.id):
        await cb.answer("⛔", show_alert=True); return
    total = db("SELECT COUNT(*) c FROM users", fetch="one")["c"]
    day_ago = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    active = db("SELECT COUNT(*) c FROM users WHERE last_seen > ?", (day_ago,), "one")["c"]
    pvp_games = db("SELECT COUNT(*) c FROM games_pvp", fetch="one")["c"]
    dice_games = db("SELECT COUNT(*) c FROM games_dice", fetch="one")["c"]
    total_balance = db("SELECT COALESCE(SUM(balance),0) c FROM users", fetch="one")["c"]
    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Всего юзеров: {total}\n"
        f"🔥 Активных за 24ч: {active}\n"
        f"❌⭕ PvP игр: {pvp_games}\n"
        f"🎲 Кубик-игр: {dice_games}\n"
        f"💰 Суммарный баланс: {total_balance}"
    )
    await cb.message.edit_text(text, reply_markup=kb_admin())
    await cb.answer()


@router.callback_query(F.data == "admin:users")
async def admin_users(cb: CallbackQuery):
    if not admin_only(cb.from_user.id):
        await cb.answer("⛔", show_alert=True); return
    rows = db("SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT 20", fetch="all")
    text = "👥 <b>Топ-20 по балансу</b>\n\n" + "\n".join(
        f"{i+1}. {r['username'] or '—'} | <code>{r['user_id']}</code> | {r['balance']}💰"
        for i, r in enumerate(rows)
    )
    await cb.message.edit_text(text, reply_markup=kb_admin())
    await cb.answer()


@router.callback_query(F.data == "admin:give")
async def admin_give(cb: CallbackQuery, state: FSMContext):
    if not admin_only(cb.from_user.id):
        await cb.answer("⛔", show_alert=True); return
    await state.set_state(S.admin_give_uid)
    await cb.message.edit_text("💰 Введи <b>user_id</b> получателя:")
    await cb.answer()


@router.message(S.admin_give_uid)
async def admin_give_uid(msg: Message, state: FSMContext):
    if not admin_only(msg.from_user.id):
        return
    if not msg.text.isdigit():
        await msg.answer("❌ user_id — число."); return
    uid = int(msg.text)
    if not get_user(uid):
        await msg.answer("❌ Юзер не найден."); return
    await state.update_data(target=uid)
    await state.set_state(S.admin_give_amount)
    await msg.answer("💰 Введи сумму (можно отрицательную):")


@router.message(S.admin_give_amount)
async def admin_give_amount(msg: Message, state: FSMContext):
    if not admin_only(msg.from_user.id):
        return
    try:
        amount = int(msg.text)
    except ValueError:
        await msg.answer("❌ Введи число."); return
    data = await state.get_data()
    target = data["target"]
    add_balance(target, amount)
    db("INSERT INTO admin_log (admin_id, action, target_id, details) VALUES (?,?,?,?)",
       (msg.from_user.id, "give_coins", target, str(amount)))
    await state.clear()
    await msg.answer(f"✅ Выдано {amount} монет юзеру <code>{target}</code>", reply_markup=kb_admin())


@router.callback_query(F.data == "admin:ban")
async def admin_ban(cb: CallbackQuery, state: FSMContext):
    if not admin_only(cb.from_user.id):
        await cb.answer("⛔", show_alert=True); return
    await state.set_state(S.admin_ban_uid)
    await cb.message.edit_text("🚫 Введи <b>user_id</b> для бана:")
    await cb.answer()


@router.message(S.admin_ban_uid)
async def admin_ban_uid(msg: Message, state: FSMContext):
    if not admin_only(msg.from_user.id):
        return
    if not msg.text.isdigit():
        await msg.answer("❌ Число."); return
    uid = int(msg.text)
    if not get_user(uid):
        await msg.answer("❌ Юзер не найден."); return
    await state.update_data(target=uid)
    await state.set_state(S.admin_ban_reason)
    await msg.answer("🚫 Введи причину бана:")


@router.message(S.admin_ban_reason)
async def admin_ban_reason(msg: Message, state: FSMContext):
    if not admin_only(msg.from_user.id):
        return
    data = await state.get_data()
    target = data["target"]
    db("UPDATE users SET is_banned=1, ban_reason=? WHERE user_id=?", (msg.text, target))
    db("INSERT INTO admin_log (admin_id, action, target_id, details) VALUES (?,?,?,?)",
       (msg.from_user.id, "ban", target, msg.text))
    await state.clear()
    await msg.answer(f"🚫 Юзер <code>{target}</code> забанен.", reply_markup=kb_admin())


@router.callback_query(F.data == "admin:unban")
async def admin_unban(cb: CallbackQuery, state: FSMContext):
    if not admin_only(cb.from_user.id):
        await cb.answer("⛔", show_alert=True); return
    await state.set_state(S.admin_unban_uid)
    await cb.message.edit_text("✅ Введи <b>user_id</b> для разбана:")
    await cb.answer()


@router.message(S.admin_unban_uid)
async def admin_unban_uid(msg: Message, state: FSMContext):
    if not admin_only(msg.from_user.id):
        return
    if not msg.text.isdigit():
        await msg.answer("❌ Число."); return
    uid = int(msg.text)
    db("UPDATE users SET is_banned=0, ban_reason=NULL WHERE user_id=?", (uid,))
    db("INSERT INTO admin_log (admin_id, action, target_id) VALUES (?,?,?)",
       (msg.from_user.id, "unban", uid))
    await state.clear()
    await msg.answer(f"✅ Юзер <code>{uid}</code> разбанен.", reply_markup=kb_admin())


@router.callback_query(F.data == "admin:banlist")
async def admin_banlist(cb: CallbackQuery):
    if not admin_only(cb.from_user.id):
        await cb.answer("⛔", show_alert=True); return
    rows = db("SELECT user_id, username, ban_reason FROM users WHERE is_banned=1", fetch="all")
    if not rows:
        text = "📜 Список банов пуст."
    else:
        text = "📜 <b>Забаненные</b>\n\n" + "\n".join(
            f"🚫 <code>{r['user_id']}</code> {r['username'] or ''} — {r['ban_reason'] or 'без причины'}"
            for r in rows
        )
    await cb.message.edit_text(text, reply_markup=kb_admin())
    await cb.answer()


@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast(cb: CallbackQuery, state: FSMContext):
    if not admin_only(cb.from_user.id):
        await cb.answer("⛔", show_alert=True); return
    await state.set_state(S.admin_broadcast)
    await cb.message.edit_text("📢 Введи текст рассылки:")
    await cb.answer()


@router.message(S.admin_broadcast)
async def admin_broadcast_send(msg: Message, state: FSMContext):
    if not admin_only(msg.from_user.id):
        return
    text = msg.text
    await state.clear()
    users = db("SELECT user_id FROM users WHERE is_banned=0", fetch="all")
    progress = await msg.answer(f"📢 Отправка... 0/{len(users)}")
    sent = 0
    for u in users:
        try:
            await bot.send_message(u["user_id"], f"📢 <b>Рассылка</b>\n\n{text}")
            sent += 1
        except TelegramForbiddenError:
            pass
        except Exception as e:
            log.warning(f"Broadcast error {u['user_id']}: {e}")
        if sent % 20 == 0:
            try:
                await progress.edit_text(f"📢 Отправка... {sent}/{len(users)}")
            except TelegramBadRequest:
                pass
        await asyncio.sleep(0.05)
    await progress.edit_text(f"✅ Рассылка завершена: {sent}/{len(users)}", reply_markup=kb_admin())


# ============================================================
#  ЗАПУСК
# ============================================================
async def main():
    global bot
    db_init()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    log.info("🚀 GameHub запущен")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("🛑 Остановлен")
