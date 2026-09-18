# -*- coding: utf-8 -*-
"""
GAMEHUB — уникальный игровой Telegram-бот.
Файл 1/2: bot.py   Файл 2/2: requirements.txt

20 игр   : dice slot roulette bj coin guess rps ttt mines hangman
           anagram quiz highlow bs memory bulls duel race lotto range
15 систем: экономика, профиль+уровни, daily, work, bank, shop+inv, pet,
           clan, quests, ach, ref, top, market, rob, boss+tourney
Админка  : /admin /give /take /ban /unban /broadcast /logs /export /tick /lottodraw
Работает в ЛС и в группах, баланс общий, антифлуд, бан-фильтр.

Запуск:
    pip install -r requirements.txt
    BOT_TOKEN=123:ABC ADMIN_IDS=123456789 python bot.py
В @BotFather ВЫКЛЮЧИ Group Privacy — иначе бот не читает обычный текст в чатах.
"""
import asyncio
import csv
import io
import os
import random
import sqlite3
import time
from datetime import date
from threading import RLock

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatType, ParseMode
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (BufferedInputFile, CallbackQuery,
                           InlineKeyboardButton as B, InlineKeyboardMarkup as K,
                           Message)
from aiogram.dispatcher.middlewares.base import BaseMiddleware

# ══════════════════ КОНФИГ ══════════════════
TOKEN = "8996813076:AAGq74gyRRW5fMxvHaIE190_B-tmzXk8aNA"
ADMINS = "5356400377"
DB = os.getenv("DB_PATH", "gamehub.db")

CUR = "🪙"
START_BAL = 1000
MIN_BET = 10
REF_BONUS = 500
DAILY_BASE, DAILY_STREAK = 700, 150
WORK_MIN, WORK_MAX = 150, 450
BANK_RATE, BANK_DAYS = 0.05, 7
CLAN_COST = 10000
TICKET_PRICE = 100
LOTTO_TICKET = 100
ROB_FINE = 300
BOSS_HP = 10000
FLOOD_N, FLOOD_T = 6, 5
GAME_CMDS = {"dice", "slot", "slots", "roulette", "rul", "bj", "blackjack", "coin", "guess",
             "rps", "ttt", "mines", "hangman", "anagram", "quiz", "highlow", "bs", "seabattle",
             "memory", "bulls", "duel", "race", "lotto", "range", "tir"}
WORDS = ["телеграм", "монета", "питомец", "турнир", "рулетка", "алмаз", "кристалл", "крепость",
         "фонарь", "дракон", "магнит", "пещера", "капитан", "знамя", "веретено", "кладовая"]
QUIZ = [("Сколько планет в Солнечной системе?", ["7", "8", "9", "10"], 1),
        ("Сколько сторон у шестиугольника?", ["5", "6", "7", "8"], 1),
        ("Кто написал «Война и мир»?", ["Пушкин", "Толстой", "Достоевский", "Чехов"], 1),
        ("Столица Японии?", ["Осака", "Киото", "Токио", "Нагоя"], 2),
        ("Сколько клеток на шахматной доске?", ["64", "81", "49", "100"], 0),
        ("Что тяжелее: 1 кг ваты или 1 кг железа?", ["Вата", "Железо", "Одинаково", "Зависит"], 2),
        ("Самая длинная река мира?", ["Амазонка", "Нил", "Янцзы", "Амур"], 0),
        ("Сколько бит в байте?", ["4", "8", "16", "32"], 1),
        ("Год первого полёта человека в космос?", ["1957", "1961", "1965", "1969"], 1),
        ("Планета ближе всего к Солнцу?", ["Венера", "Марс", "Меркурий", "Земля"], 2),
        ("Какой газ нужен нам для жизни?", ["Азот", "Кислород", "Гелий", "Аргон"], 1),
        ("Сколько цветов в радуге?", ["5", "6", "7", "8"], 2)]
STOCKS = {"GHB": 120, "MIN": 260, "PET": 430, "CLN": 850, "BT": 1600, "LOT": 3200}
SHOP = {"boost": ("🚀 Бустер +50 XP", 700), "shield": ("🛡 Щит от кражи", 900),
        "clover": ("🍀 Клевер удачи", 1400), "ticket": ("🎟 Билет удачи", 2500)}

# ══════════════════ БАЗА ══════════════════
_c = sqlite3.connect(DB, check_same_thread=False)
_c.row_factory = sqlite3.Row
_lk = RLock()


def ex(s, a=()):
    with _lk:
        cur = _c.execute(s, a)
        _c.commit()
        return cur.rowcount


def q1(s, a=()):
    with _lk:
        return _c.execute(s, a).fetchone()


def qa(s, a=()):
    with _lk:
        return _c.execute(s, a).fetchall()


def sc(s, a=()):
    row = q1(s, a)
    return None if row is None else row[0]


TABLES = [
    """CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, username TEXT DEFAULT '',
    balance INTEGER DEFAULT 1000, bank INTEGER DEFAULT 0, bank_ts INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0, daily_ts INTEGER DEFAULT 0, streak INTEGER DEFAULT 0,
    work_ts INTEGER DEFAULT 0, pet TEXT DEFAULT '', pet_lvl INTEGER DEFAULT 1,
    pet_ts INTEGER DEFAULT 0, clan INTEGER DEFAULT 0, ref_by INTEGER DEFAULT 0,
    banned INTEGER DEFAULT 0, games INTEGER DEFAULT 0, wins INTEGER DEFAULT 0,
    bet_sum INTEGER DEFAULT 0, win_sum INTEGER DEFAULT 0, created INTEGER DEFAULT 0)""",
    "CREATE TABLE IF NOT EXISTS inv(user_id INTEGER, item TEXT, qty INTEGER DEFAULT 0,"
    " PRIMARY KEY(user_id,item))",
    "CREATE TABLE IF NOT EXISTS chats(chat_id INTEGER PRIMARY KEY, games_on INTEGER DEFAULT 1)",
    """CREATE TABLE IF NOT EXISTS clans(clan_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
    owner INTEGER, treasury INTEGER DEFAULT 0)""",
    """CREATE TABLE IF NOT EXISTS quests(user_id INTEGER, day TEXT, qkey TEXT, need INTEGER,
    prog INTEGER DEFAULT 0, done INTEGER DEFAULT 0, reward INTEGER DEFAULT 0,
    PRIMARY KEY(user_id,day,qkey))""",
    "CREATE TABLE IF NOT EXISTS ach(user_id INTEGER, aid TEXT, PRIMARY KEY(user_id,aid))",
    "CREATE TABLE IF NOT EXISTS stocks(sym TEXT PRIMARY KEY, price INTEGER, prev INTEGER)",
    "CREATE TABLE IF NOT EXISTS holdings(user_id INTEGER, sym TEXT, qty INTEGER DEFAULT 0,"
    " PRIMARY KEY(user_id,sym))",
    "CREATE TABLE IF NOT EXISTS bosses(chat_id INTEGER PRIMARY KEY, hp INTEGER, max_hp INTEGER)",
    "CREATE TABLE IF NOT EXISTS tickets(user_id INTEGER PRIMARY KEY, qty INTEGER DEFAULT 0)",
    """CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER,
    user_id INTEGER, action TEXT, amount INTEGER DEFAULT 0)""",
]


def init_db():
    for t in TABLES:
        ex(t)
    for sym, price in STOCKS.items():
        if not sc("SELECT 1 FROM stocks WHERE sym=?", (sym,)):
            ex("INSERT INTO stocks(sym,price,prev) VALUES(?,?,?)", (sym, price, price))


# ══════════════════ УТИЛИТЫ ══════════════════
def ts():
    return int(time.time())


def day():
    return date.today().isoformat()


def fmt(n):
    return f"{int(n):,}".replace(",", " ")


def u(uid):
    return q1("SELECT * FROM users WHERE user_id=?", (uid,))


def bal(uid):
    r = u(uid)
    return r["balance"] if r else 0


def pay(uid, amount):
    ex("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, uid))
    ex("INSERT INTO logs(ts,user_id,action,amount) VALUES(?,?,?,?)",
       (ts(), uid, "pay" if amount >= 0 else "take", amount))


def lvl(xp):
    return xp // 150 + 1


def bet_of(raw, uid, lo=MIN_BET):
    """Возвращает (ставка, ошибка)."""
    b = bal(uid)
    if raw in ("all", "все", "вабанк"):
        amount = b
    elif raw in ("half", "половина"):
        amount = b // 2
    elif raw.isdigit():
        amount = int(raw)
    else:
        return None, f"Ставка — число: <code>/slot 100</code>, либо <code>all</code> / <code>half</code>. Минимум {lo}{CUR}."
    if amount < lo:
        return None, f"Минимальная ставка — {lo}{CUR}."
    if amount > b:
        return None, f"Не хватает монет: у тебя {fmt(b)}{CUR}, нужно {fmt(amount)}{CUR}."
    return amount, None


def carg(cmd):
    return ((cmd.args or "").strip().split() or [""])[0]


def cargs(cmd):
    return (cmd.args or "").strip().split()


async def ensure(tg, ref=0):
    uid = tg.id
    if not u(uid):
        ex("INSERT INTO users(user_id,username,balance,created,ref_by) VALUES(?,?,?,?,?)",
           (uid, tg.username or "", START_BAL, ts(), ref))
        if ref and ref != uid and u(ref):
            pay(ref, REF_BONUS)
            pay(uid, REF_BONUS)
        return True
    ex("UPDATE users SET username=? WHERE user_id=?", (tg.username or "", uid))
    return False


def iadd(uid, item, n=1):
    ex("INSERT INTO inv(user_id,item,qty) VALUES(?,?,?) "
       "ON CONFLICT(user_id,item) DO UPDATE SET qty=qty+?", (uid, item, n, n))


def iget(uid, item):
    v = sc("SELECT qty FROM inv WHERE user_id=? AND item=?", (uid, item))
    return v or 0


def itake(uid, item, n=1):
    if iget(uid, item) < n:
        return False
    ex("UPDATE inv SET qty=qty-? WHERE user_id=? AND item=?", (n, uid, item))
    return True


QPOOL = {"games": ("Сыграть {n} игр", (5, 15)), "wins": ("Выиграть {n} раз", (2, 6)),
         "bet": ("Сделать ставок на {n}", (2000, 10000)), "work": ("Поработать {n} раза", (1, 3)),
         "feed": ("Покормить питомца {n} раза", (1, 2))}


def qensure(uid):
    if sc("SELECT 1 FROM quests WHERE user_id=? AND day=? LIMIT 1", (uid, day())):
        return
    for k in random.sample(list(QPOOL), 3):
        lo, hi = QPOOL[k][1]
        need = random.randint(lo, hi)
        ex("INSERT OR REPLACE INTO quests(user_id,day,qkey,need,prog,done,reward)"
           " VALUES(?,?,?,?,0,0,?)", (uid, day(), k, need, need * (60 if k == "bet" else 120)))


def qbump(uid, key, n=1):
    ex("UPDATE quests SET prog=prog+? WHERE user_id=? AND day=? AND qkey=? AND done=0",
       (n, uid, day(), key))


ACH = [("w1", "Первая победа", lambda r: r["wins"] >= 1, 0),
       ("w25", "25 побед", lambda r: r["wins"] >= 25, 500),
       ("w200", "200 побед", lambda r: r["wins"] >= 200, 3000),
       ("g50", "50 игр", lambda r: r["games"] >= 50, 500),
       ("g500", "500 игр", lambda r: r["games"] >= 500, 4000),
       ("b50k", "Капитал 50 000", lambda r: r["balance"] >= 50000, 2000),
       ("b500k", "Капитал 500 000", lambda r: r["balance"] >= 500000, 15000),
       ("l10", "10 уровень", lambda r: lvl(r["xp"]) >= 10, 1500),
       ("l25", "25 уровень", lambda r: lvl(r["xp"]) >= 25, 6000),
       ("pet5", "Питомец 5 уровня", lambda r: r["pet_lvl"] >= 5 and r["pet"] != "", 2000),
       ("clan", "Состою в клане", lambda r: r["clan"] > 0, 1000),
       ("st7", "Стрик 7 дней", lambda r: r["streak"] >= 7, 2500)]


def check_ach(uid):
    row = u(uid)
    have = {x["aid"] for x in qa("SELECT aid FROM ach WHERE user_id=?", (uid,))}
    got = []
    for aid, title, cond, rew in ACH:
        if aid in have or not cond(row):
            continue
        ex("INSERT OR IGNORE INTO ach(user_id,aid) VALUES(?,?)", (uid, aid))
        if rew:
            pay(uid, rew)
        got.append(title)
    return got


def R(bet, payout, win):
    net = payout - bet
    head = "🎉 Победа!" if net > 0 else ("🤝 Возврат" if net == 0 else "💀 Проигрыш")
    return f"{head} {'+' if net >= 0 else ''}{fmt(net)}{CUR}"


def finish(uid, bet, payout, win, game):
    xp = max(2, min(60, bet // 120 + (20 if win else 2)))
    ex("""UPDATE users SET balance=balance+?, games=games+1, wins=wins+?,
          bet_sum=bet_sum+?, win_sum=win_sum+?, xp=xp+? WHERE user_id=?""",
       (payout, 1 if win else 0, bet, payout, xp, uid))
    ex("INSERT INTO logs(ts,user_id,action,amount) VALUES(?,?,?,?)",
       (ts(), uid, f"game:{game}", payout - bet))
    qbump(uid, "games")
    qbump(uid, "bet", bet)
    if win:
        qbump(uid, "wins")
    check_ach(uid)


def end(uid, bet, payout, win, game, extra=""):
    finish(uid, bet, payout, win, game)
    tail = f"\n{extra}" if extra else ""
    return f"{R(bet, payout, win)} | Баланс: {fmt(bal(uid))}{CUR}{tail}"


# ══════════════════ МИДЛВАРЬ ══════════════════
class Guard(BaseMiddleware):
    def __init__(self):
        self.f = {}

    async def __call__(self, handler, event: Message, data):
        fu = event.from_user
        if not fu or fu.is_bot:
            return await handler(event, data)
        row = u(fu.id)
        if row and row["banned"] and fu.id not in ADMINS:
            return
        t = ts()
        seq = [x for x in self.f.get(fu.id, []) if t - x < FLOOD_T]
        seq.append(t)
        self.f[fu.id] = seq
        if len(seq) > FLOOD_N and fu.id not in ADMINS:
            return
        if event.chat.type != ChatType.PRIVATE and event.text and event.text.startswith("/"):
            cmd = event.text[1:].split()[0].split("@")[0].lower()
            if cmd in GAME_CMDS and not games_on(event.chat.id):
                return
        return await handler(event, data)


def games_on(chat_id):
    r = q1("SELECT games_on FROM chats WHERE chat_id=?", (chat_id,))
    if not r:
        ex("INSERT OR IGNORE INTO chats(chat_id) VALUES(?)", (chat_id,))
        return True
    return bool(r["games_on"])


# ══════════════════ ИГРЫ ══════════════════
rt = Router()


class F_ (StatesGroup):
    guess = State()
    hang = State()
    ana = State()
    bulls = State()
    bc = State()


# 1 ── кости
@rt.message(Command("dice"))
async def g_dice(m: Message, command: CommandObject):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    a, b = random.randint(1, 6), random.randint(1, 6)
    win = a > b
    payout = bet * 2 if win else (bet if a == b else 0)
    await m.reply(f"🎲 Ты: <b>{a}</b> — Бот: <b>{b}</b>\n" + end(m.from_user.id, bet, payout, win, "dice"))


# 2 ── слоты
@rt.message(Command("slot", "slots"))
async def g_slot(m: Message, command: CommandObject):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    reel = ["🍒", "🍋", "🍇", "💎", "7️⃣", "🔔"]
    s = [random.choice(reel) for _ in range(3)]
    if s[0] == s[1] == s[2]:
        mult = {"💎": 20, "7️⃣": 12}.get(s[0], 6)
    elif len(set(s)) == 2:
        mult = 1.5
    else:
        mult = 0
    payout = int(bet * mult)
    await m.reply(f"🎰 | {s[0]} | {s[1]} | {s[2]} |\nМножитель ×{mult}\n"
                  + end(m.from_user.id, bet, payout, mult > 1, "slot"))


# 3 ── рулетка
@rt.message(Command("roulette", "rul"))
async def g_roulette(m: Message, command: CommandObject):
    await ensure(m.from_user)
    p = cargs(command)
    if len(p) < 2:
        return await m.reply("Формат: <code>/roulette 100 red</code>\n"
                             "Ставки: red · black · even · odd · число 0–36 (×36)")
    bet, err = bet_of(p[0], m.from_user.id)
    if err:
        return await m.reply(err)
    pick = p[1].lower()
    pay(m.from_user.id, -bet)
    n = random.randint(0, 36)
    red = n in (1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36)
    mult = 0
    if pick.isdigit() and int(pick) == n:
        mult = 36
    elif pick == "red" and red:
        mult = 2
    elif pick == "black" and n and not red:
        mult = 2
    elif pick == "even" and n and n % 2 == 0:
        mult = 2
    elif pick == "odd" and n % 2 == 1:
        mult = 2
    payout = bet * mult
    color = "🟢 зеро" if n == 0 else ("🔴 красное" if red else "⚫ чёрное")
    await m.reply(f"🎡 Выпало <b>{n}</b> ({color}), ты ставил {pick}\n"
                  + end(m.from_user.id, bet, payout, mult > 1, "roulette"))


# 4 ── быстрый блэкджек
def hand():
    cards = [random.randint(2, 11) for _ in range(2)]
    while sum(cards) < 17:
        cards.append(random.randint(2, 11))
    return sum(cards)


@rt.message(Command("bj", "blackjack"))
async def g_bj(m: Message, command: CommandObject):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    p, d = hand(), hand()
    mult = 2.5 if p == 21 else (2 if (p <= 21 and (d > 21 or p > d)) else (1 if p == d else 0))
    payout = int(bet * mult)
    await m.reply(f"🃏 Ты: <b>{p}</b> — Дилер: <b>{d}</b>\n"
                  + end(m.from_user.id, bet, payout, mult > 1, "bj"))


# 5 ── монетка
@rt.message(Command("coin"))
async def g_coin(m: Message, command: CommandObject):
    await ensure(m.from_user)
    p = cargs(command)
    if len(p) < 2:
        return await m.reply("Формат: <code>/coin 100 орел</code> или <code>/coin 100 решка</code>")
    bet, err = bet_of(p[0], m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    out = random.choice(["орёл", "решка"])
    win = out.startswith(p[1].lower()[:4])
    payout = bet * 2 if win else 0
    await m.reply(f"🪙 Выпал <b>{out}</b>\n" + end(m.from_user.id, bet, payout, win, "coin"))


# 6 ── угадай число
@rt.message(Command("guess"))
async def g_guess(m: Message, command: CommandObject, state: FSMContext):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    await state.set_state(F_.guess)
    await state.update_data(bet=bet, num=random.randint(1, 100), tries=7)
    await m.reply(f"🔢 Загадал число 1–100. 7 попыток, ставка {fmt(bet)}{CUR}. Пиши число!")


@rt.message(F_.guess, F.text)
async def s_guess(m: Message, state: FSMContext):
    d = await state.get_data()
    t = m.text.strip()
    if not t.isdigit():
        return await m.reply("Нужно число от 1 до 100.")
    n = int(t)
    if n == d["num"]:
        await state.clear()
        payout = int(d["bet"] * (2 + (7 - d["tries"]) * 0.15))
        return await m.reply(f"🎯 Точно, {n}!\n" + end(m.from_user.id, d["bet"], payout, True, "guess"))
    d["tries"] -= 1
    if d["tries"] <= 0:
        await state.clear()
        return await m.reply(f"💀 Попытки кончились, было {d['num']}.\n"
                             + end(m.from_user.id, d["bet"], 0, False, "guess"))
    await state.update_data(tries=d["tries"])
    await m.reply(f"{'📈 больше' if n < d['num'] else '📉 меньше'}! Осталось: {d['tries']}")


# 7 ── КНБ
@rt.message(Command("rps"))
async def g_rps(m: Message, command: CommandObject):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    kb = K(inline_keyboard=[[B(text="✊", callback_data=f"rps:rock:{bet}"),
                             B(text="✋", callback_data=f"rps:paper:{bet}"),
                             B(text="✌️", callback_data=f"rps:scissors:{bet}")]])
    await m.reply(f"✂️ КНБ, ставка {fmt(bet)}{CUR}. Твой ход:", reply_markup=kb)


@rt.callback_query(F.data.startswith("rps:"))
async def cb_rps(cb: CallbackQuery):
    _, pick, bet = cb.data.split(":")
    bet = int(bet)
    beat = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
    em = {"rock": "✊", "paper": "✋", "scissors": "✌️"}
    bp = random.choice(list(em))
    win, draw = beat[pick] == bp, pick == bp
    payout = bet * 2 if win else (bet if draw else 0)
    await cb.message.edit_text(f"Ты {em[pick]} — бот {em[bp]}\n"
                               + end(cb.from_user.id, bet, payout, win, "rps"))
    await cb.answer("Победа!" if win else ("Ничья" if draw else "Проигрыш"))


# 8 ── крестики-нолики
LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def who(b):
    for a, c, d in LINES:
        if b[a] == b[c] == b[d] != "·":
            return b[a]
    return None


def nice(b):
    return "\n".join(" ".join(b[i:i + 3]) for i in (0, 3, 6))


def botmove(b):
    for mk in ("O", "X"):
        for a, c, d in LINES:
            ln = [b[a], b[c], b[d]]
            if ln.count(mk) == 2 and "·" in ln:
                return [a, c, d][ln.index("·")]
    return next((i for i in (4, 0, 2, 6, 8, 1, 3, 5, 7) if b[i] == "·"), None)


def ttt_kb(b, bet):
    return K(inline_keyboard=[[B(text=b[i], callback_data=f"ttt:{i}:{bet}") for i in range(x, x + 3)]
                              for x in (0, 3, 6)])


@rt.message(Command("ttt"))
async def g_ttt(m: Message, command: CommandObject):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    b = ["·"] * 9
    await m.reply(f"⭕ Ты <b>X</b>, бот <b>O</b>. Ставка {fmt(bet)}{CUR}.", reply_markup=ttt_kb(b, bet))


@rt.callback_query(F.data.startswith("ttt:"))
async def cb_ttt(cb: CallbackQuery):
    _, i, bet = cb.data.split(":")
    i, bet = int(i), int(bet)
    b = [x.text if x.text in ("X", "O") else "·" for row in cb.message.reply_markup.inline_keyboard for x in row]
    if b[i] != "·":
        return await cb.answer("Клетка занята")
    b[i] = "X"
    w = who(b)
    if not w and "·" in b:
        j = botmove(b)
        if j is not None:
            b[j] = "O"
        w = who(b)
    if w == "X":
        txt = "🎉 Ты выиграл!\n" + end(cb.from_user.id, bet, bet * 2, True, "ttt")
    elif w == "O":
        txt = "💀 Бот выиграл.\n" + end(cb.from_user.id, bet, 0, False, "ttt")
    elif "·" not in b:
        txt = "🤝 Ничья.\n" + end(cb.from_user.id, bet, bet, False, "ttt")
    else:
        txt = "Твой ход..."
    over = bool(w) or "·" not in b
    await cb.message.edit_text(nice(b) + "\n\n" + txt, reply_markup=None if over else ttt_kb(b, bet))
    await cb.answer()


# 9 ── сапёр
MINE = {}


@rt.message(Command("mines"))
async def g_mines(m: Message, command: CommandObject):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    MINE[m.from_user.id] = {"b": set(random.sample(range(25), 5)), "o": set(), "bet": bet}
    kb = K(inline_keyboard=[[B(text="❔", callback_data=f"mn:{i}") for i in range(x, x + 5)]
                            for x in (0, 5, 10, 15, 20)] + [[B(text="💰 Забрать", callback_data="mn:cash")]])
    await m.reply(f"💣 5×5, 5 мин, ставка {fmt(bet)}{CUR}. Каждая чистая клетка ×1.35.", reply_markup=kb)


@rt.callback_query(F.data.startswith("mn:"))
async def cb_mines(cb: CallbackQuery):
    g = MINE.get(cb.from_user.id)
    if not g:
        return await cb.answer("Партия не найдена")
    act = cb.data.split(":")[1]
    bet = g["bet"]
    if act == "cash":
        mult = 1.35 ** len(g["o"]) if g["o"] else 1
        payout = int(bet * mult)
        del MINE[cb.from_user.id]
        return await cb.message.edit_text(f"💰 Забрал на ×{mult:.2f}\n"
                                          + end(cb.from_user.id, bet, payout, payout > bet, "mines"))
    i = int(act)
    if i in g["o"]:
        return await cb.answer("Уже открыто")
    g["o"].add(i)
    if i in g["b"]:
        del MINE[cb.from_user.id]
        return await cb.message.edit_text("💥 Мина!\n" + end(cb.from_user.id, bet, 0, False, "mines"))
    kb = K(inline_keyboard=[[B(text=("💚" if j in g["o"] else "❔"), callback_data=f"mn:{j}")
                             for j in range(x, x + 5)] for x in (0, 5, 10, 15, 20)]
           + [[B(text=f"💰 Забрать ×{1.35 ** len(g['o']):.2f}", callback_data="mn:cash")]])
    await cb.message.edit_reply_markup(reply_markup=kb)
    await cb.answer("Чисто!")


# 10 ── виселица
@rt.message(Command("hangman"))
async def g_hang(m: Message, command: CommandObject, state: FSMContext):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    w = random.choice(WORDS)
    await state.set_state(F_.hang)
    await state.update_data(bet=bet, w=w, used=[], life=6)
    await m.reply(f"🔤 <code>{'_ ' * len(w)}</code> — {len(w)} букв, 6 ошибок, ставка {fmt(bet)}{CUR}.\n"
                  "Пиши по одной букве.")


@rt.message(F_.hang, F.text)
async def s_hang(m: Message, state: FSMContext):
    d = await state.get_data()
    ch = m.text.strip().lower()[:1]
    if not ch.isalpha():
        return await m.reply("Нужна одна буква.")
    if ch in d["used"]:
        return await m.reply("Эта буква уже была.")
    d["used"].append(ch)
    if ch not in d["w"]:
        d["life"] -= 1
    if all(c in d["used"] for c in d["w"]):
        await state.clear()
        payout = int(d["bet"] * (1 + d["life"] * 0.4))
        return await m.reply(f"🎉 Слово: <b>{d['w']}</b>\n"
                             + end(m.from_user.id, d["bet"], payout, True, "hangman"))
    if d["life"] <= 0:
        await state.clear()
        return await m.reply(f"💀 Было <b>{d['w']}</b>.\n" + end(m.from_user.id, d["bet"], 0, False, "hangman"))
    await state.update_data(used=d["used"], life=d["life"])
    await m.reply(" ".join(c if c in d["used"] else "_" for c in d["w"]) + f"\nОшибок осталось: {d['life']}")


# 11 ── анаграмма
@rt.message(Command("anagram"))
async def g_ana(m: Message, command: CommandObject, state: FSMContext):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    w = random.choice(WORDS)
    await state.set_state(F_.ana)
    await state.update_data(bet=bet, w=w, tries=3)
    await m.reply(f"🧩 Собери слово: <b>{''.join(random.sample(w, len(w))).upper()}</b>\n"
                  f"3 попытки, ставка {fmt(bet)}{CUR}.")


@rt.message(F_.ana, F.text)
async def s_ana(m: Message, state: FSMContext):
    d = await state.get_data()
    if m.text.strip().lower() == d["w"]:
        await state.clear()
        return await m.reply(f"🎉 Верно: <b>{d['w']}</b>\n"
                             + end(m.from_user.id, d["bet"], d["bet"] * 3, True, "anagram"))
    d["tries"] -= 1
    if d["tries"] <= 0:
        await state.clear()
        return await m.reply(f"💀 Было <b>{d['w']}</b>.\n" + end(m.from_user.id, d["bet"], 0, False, "anagram"))
    await state.update_data(tries=d["tries"])
    await m.reply(f"Не то. Попыток: {d['tries']}")


# 12 ── викторина
@rt.message(Command("quiz"))
async def g_quiz(m: Message, command: CommandObject):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    qi = random.randrange(len(QUIZ))
    q, opts, _ = QUIZ[qi]
    kb = K(inline_keyboard=[[B(text=o, callback_data=f"qz:{qi}:{i}:{bet}")] for i, o in enumerate(opts)])
    await m.reply(f"❓ {q}\nСтавка {fmt(bet)}{CUR}.", reply_markup=kb)


@rt.callback_query(F.data.startswith("qz:"))
async def cb_quiz(cb: CallbackQuery):
    _, qi, i, bet = cb.data.split(":")
    qi, i, bet = int(qi), int(i), int(bet)
    win = i == QUIZ[qi][2]
    payout = bet * 2 if win else 0
    await cb.message.edit_text(("✅ Верно! " if win else "❌ Неверно. ") +
                               f"Правильно: <b>{QUIZ[qi][1][QUIZ[qi][2]]}</b>\n"
                               + end(cb.from_user.id, bet, payout, win, "quiz"))
    await cb.answer()


# 13 ── больше/меньше
HL = {}


@rt.message(Command("highlow"))
async def g_hl(m: Message, command: CommandObject):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    HL[m.from_user.id] = {"bet": bet, "n": random.randint(2, 98), "s": 0}
    kb = K(inline_keyboard=[[B(text="⬆️ Больше", callback_data="hl:hi"), B(text="⬇️ Меньше", callback_data="hl:lo"),
                             B(text="💰 Забрать", callback_data="hl:cash")]])
    await m.reply(f"🎲 Число: <b>{HL[m.from_user.id]['n']}</b>. Дальше больше или меньше? (×1.8/шаг)",
                  reply_markup=kb)


@rt.callback_query(F.data.startswith("hl:"))
async def cb_hl(cb: CallbackQuery):
    g = HL.get(cb.from_user.id)
    if not g:
        return await cb.answer("Партия не найдена")
    act, bet = cb.data.split(":")[1], g["bet"]
    if act == "cash":
        payout = int(bet * 1.8 ** g["s"])
        del HL[cb.from_user.id]
        return await cb.message.edit_text(f"💰 Забрал ×{1.8 ** g['s']:.2f}\n"
                                          + end(cb.from_user.id, bet, payout, g["s"] > 0, "highlow"))
    old, new = g["n"], random.randint(1, 100)
    right = new > old if act == "hi" else new < old
    if not right:
        del HL[cb.from_user.id]
        return await cb.message.edit_text(f"Было {old}, выпало {new} 💀\n"
                                          + end(cb.from_user.id, bet, 0, False, "highlow"))
    g["n"], g["s"] = new, g["s"] + 1
    if g["s"] >= 6:
        payout = int(bet * 1.8 ** g["s"])
        del HL[cb.from_user.id]
        return await cb.message.edit_text("🔥 6 шагов подряд!\n"
                                          + end(cb.from_user.id, bet, payout, True, "highlow"))
    await cb.message.edit_text(f"✅ Было {old} → выпало <b>{new}</b> (×{1.8 ** g['s']:.2f})",
                               reply_markup=cb.message.reply_markup)
    await cb.answer("Есть!")


# 14 ── морской бой
BS = {}


@rt.message(Command("bs", "seabattle"))
async def g_bs(m: Message, command: CommandObject):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    ships = set()
    while len(ships) < 9:
        row, col = divmod(random.randint(0, 24), 5)
        if random.random() < 0.5 and col <= 2:
            ships.update(row * 5 + col + k for k in range(3))
        elif row <= 2:
            ships.update((row + k) * 5 + col for k in range(3))
    BS[m.from_user.id] = {"s": ships, "fired": set(), "bet": bet}
    kb = K(inline_keyboard=[[B(text="🌊", callback_data=f"bs:{i}") for i in range(x, x + 5)]
                            for x in (0, 5, 10, 15, 20)])
    await m.reply(f"🚢 Флот спрятан (3 корабля), 5 выстрелов, ставка {fmt(bet)}{CUR}.", reply_markup=kb)


@rt.callback_query(F.data.startswith("bs:"))
async def cb_bs(cb: CallbackQuery):
    g = BS.get(cb.from_user.id)
    if not g:
        return await cb.answer("Партия не найдена")
    i = int(cb.data.split(":")[1])
    if i not in g["fired"]:
        g["fired"].add(i)
    hits = len(g["fired"] & g["s"])
    bet = g["bet"]
    if len(g["fired"]) >= 5 or hits == 9:
        payout = int(bet * (0.6 * hits + (3 if hits >= 9 else 0)))
        del BS[cb.from_user.id]
        return await cb.message.edit_text(f"🎯 Попаданий: {hits}\n"
                                          + end(cb.from_user.id, bet, payout, payout > bet, "bs"))
    kb = K(inline_keyboard=[[B(text=("💥" if j in g["fired"] and j in g["s"] else
                                    ("💨" if j in g["fired"] else "🌊")), callback_data=f"bs:{j}")
                             for j in range(x, x + 5)] for x in (0, 5, 10, 15, 20)])
    await cb.message.edit_reply_markup(reply_markup=kb)
    await cb.answer("🔥 Попал!" if i in g["s"] else "Мимо")


# 15 ── мемори
MEM = {}


@rt.message(Command("memory"))
async def g_mem(m: Message, command: CommandObject):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    deck = ["🍒", "🍋", "🍇", "💎", "🔔", "⚽️", "🎈", "🧊"] * 2
    random.shuffle(deck)
    MEM[m.from_user.id] = {"d": deck, "op": [], "ok": set(), "f": 0, "bet": bet}
    kb = K(inline_keyboard=[[B(text="❔", callback_data=f"mem:{i}") for i in range(x, x + 4)]
                            for x in (0, 4, 8, 12)])
    await m.reply(f"🧠 Мемори 4×4: 8 пар за 16 ходов. Ставка {fmt(bet)}{CUR}.", reply_markup=kb)


@rt.callback_query(F.data.startswith("mem:"))
async def cb_mem(cb: CallbackQuery):
    g = MEM.get(cb.from_user.id)
    if not g:
        return await cb.answer("Партия не найдена")
    i = int(cb.data.split(":")[1])
    bet = g["bet"]
    if i in g["ok"] or i in g["op"]:
        return await cb.answer("Открыто")
    g["op"].append(i)
    if len(g["op"]) == 2:
        g["f"] += 1
        a, b = g["op"]
        if g["d"][a] == g["d"][b]:
            g["ok"].update((a, b))
        g["op"] = []
    if len(g["ok"]) == 16:
        payout = int(bet * (3 if g["f"] <= 14 else 1.2))
        del MEM[cb.from_user.id]
        return await cb.message.edit_text(f"🎉 Все пары за {g['f']} ходов!\n"
                                          + end(cb.from_user.id, bet, payout, True, "memory"))
    if g["f"] >= 16:
        del MEM[cb.from_user.id]
        return await cb.message.edit_text("💀 Ходы кончились.\n" + end(cb.from_user.id, bet, 0, False, "memory"))
    kb = K(inline_keyboard=[[B(text=(g["d"][j] if (j in g["ok"] or j in g["op"]) else "❔"),
                               callback_data=f"mem:{j}") for j in range(x, x + 4)] for x in (0, 4, 8, 12)])
    await cb.message.edit_reply_markup(reply_markup=kb)
    await cb.answer()


# 16 ── быки и коровы
@rt.message(Command("bulls"))
async def g_bulls(m: Message, command: CommandObject, state: FSMContext):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    sec = "".join(random.sample("123456789", 4))
    await state.set_state(F_.bulls)
    await state.update_data(bet=bet, sec=sec, tries=8)
    await m.reply("🐄 Загадано 4 цифры без повторов. 8 попыток, ставка "
                  f"{fmt(bet)}{CUR}.\nБык — цифра на месте, корова — угадана цифра.\nПиши 4 цифры.")


@rt.message(F_.bulls, F.text)
async def s_bulls(m: Message, state: FSMContext):
    d = await state.get_data()
    g = m.text.strip()
    if not (g.isdigit() and len(g) == 4):
        return await m.reply("Ровно 4 цифры, например <code>1234</code>.")
    bull = sum(1 for i in range(4) if g[i] == d["sec"][i])
    cow = sum(1 for x in set(g) if x in d["sec"]) - bull
    if bull == 4:
        await state.clear()
        return await m.reply(f"🎉 Точно: {d['sec']}\n"
                             + end(m.from_user.id, d["bet"], d["bet"] * 5, True, "bulls"))
    d["tries"] -= 1
    if d["tries"] <= 0:
        await state.clear()
        return await m.reply(f"💀 Было {d['sec']}.\n" + end(m.from_user.id, d["bet"], 0, False, "bulls"))
    await state.update_data(tries=d["tries"])
    await m.reply(f"🐄 Быки: {bull}, коровы: {cow}. Попыток: {d['tries']}")


# 17 ── дуэль
@rt.message(Command("duel"))
async def g_duel(m: Message, command: CommandObject):
    await ensure(m.from_user)
    if not m.reply_to_message or m.reply_to_message.from_user.is_bot:
        return await m.reply("Ответь на сообщение игрока: <code>/duel 100</code>")
    foe = m.reply_to_message.from_user
    if foe.id == m.from_user.id:
        return await m.reply("С собой не выйдет 🙂")
    await ensure(foe)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    if bal(foe.id) < bet:
        return await m.reply(f"У {foe.full_name} только {fmt(bal(foe.id))}{CUR}.")
    kb = K(inline_keyboard=[[B(text=f"⚔️ Принять ({fmt(bet)}{CUR})", callback_data=f"dl:ok:{m.from_user.id}:{bet}"),
                             B(text="🙅 Отказ", callback_data="dl:no")]])
    await m.reply(f"⚔️ <b>{m.from_user.full_name}</b> вызывает <b>{foe.full_name}</b>!\n"
                  f"Ставка {fmt(bet)}{CUR}, победитель забирает {fmt(bet * 2)}{CUR}.", reply_markup=kb)


@rt.callback_query(F.data.startswith("dl:"))
async def cb_duel(cb: CallbackQuery):
    p = cb.data.split(":")
    if p[1] == "no":
        return await cb.message.edit_text("🙅 Дуэль отменена.")
    host, bet = int(p[2]), int(p[3])
    if cb.from_user.id == host:
        return await cb.answer("Это твой вызов — ждём соперника.")
    if bal(cb.from_user.id) < bet or bal(host) < bet:
        return await cb.answer("У кого-то не хватает монет")
    pay(host, -bet)
    pay(cb.from_user.id, -bet)
    win_host = random.random() < 0.5
    finish(host, bet, bet * 2 if win_host else 0, win_host, "duel")
    finish(cb.from_user.id, bet, 0 if win_host else bet * 2, not win_host, "duel")
    name = cb.message.reply_to_message.from_user.full_name if cb.message.reply_to_message else "вызывающий"
    if not win_host:
        name = cb.from_user.full_name
    await cb.message.edit_text(f"⚔️ Победил <b>{name}</b> и забрал {fmt(bet * 2)}{CUR}.")
    await cb.answer("Ты победил!" if not win_host else "Ты проиграл")


# 18 ── гонки
@rt.message(Command("race"))
async def g_race(m: Message, command: CommandObject):
    await ensure(m.from_user)
    p = cargs(command)
    if len(p) < 2 or p[1] not in "1234":
        return await m.reply("Формат: <code>/race 100 2</code> — ставка и лошадь 1–4.\n"
                             "Коэффициенты: 1 — ×5, 2 — ×3, 3 — ×2.5, 4 — ×2")
    bet, err = bet_of(p[0], m.from_user.id)
    if err:
        return await m.reply(err)
    pick = int(p[1])
    pay(m.from_user.id, -bet)
    weights = [1, 2, 3, 5]
    roll, acc, winner = random.uniform(0, sum(weights)), 0, 4
    for i, w in enumerate(weights, 1):
        acc += w
        if roll <= acc:
            winner = i
            break
    odds = {1: 5, 2: 3, 3: 2.5, 4: 2}[pick]
    payout = int(bet * odds) if pick == winner else 0
    track = "".join("🏇" if i == winner else "・" for i in range(1, 5))
    await m.reply(f"🏁 {track}\nПобедила лошадь №{winner}, у тебя №{pick}\n"
                  + end(m.from_user.id, bet, payout, payout > 0, "race"))


# 19 ── лотерея
@rt.message(Command("lotto"))
async def g_lotto(m: Message, command: CommandObject):
    await ensure(m.from_user)
    if carg(command) == "draw":
        if m.from_user.id not in ADMINS:
            return await m.reply("Розыгрыш запускает админ.")
        rows = qa("SELECT user_id, qty FROM tickets WHERE qty>0")
        if not rows:
            return await m.reply("Билетов нет.")
        pool = [x["user_id"] for x in rows for _ in range(x["qty"])]
        winner = random.choice(pool)
        pot = int(sum(x["qty"] for x in rows) * LOTTO_TICKET * 0.8)
        pay(winner, pot)
        ex("DELETE FROM tickets")
        try:
            await m.bot.send_message(winner, f"🎉 Ты выиграл лотерею! Приз {fmt(pot)}{CUR}")
        except Exception:
            pass
        return await m.reply(f"🎟 Победитель: <a href='tg://user?id={winner}'>игрок</a>, приз {fmt(pot)}{CUR}.")
    if bal(m.from_user.id) < LOTTO_TICKET:
        return await m.reply(f"Билет стоит {LOTTO_TICKET}{CUR}, у тебя {fmt(bal(m.from_user.id))}{CUR}.")
    pay(m.from_user.id, -LOTTO_TICKET)
    ex("INSERT INTO tickets(user_id,qty) VALUES(?,1) ON CONFLICT(user_id) DO UPDATE SET qty=qty+1",
       (m.from_user.id,))
    total = sc("SELECT COALESCE(SUM(qty),0) FROM tickets") or 0
    await m.reply(f"🎟 Билет куплен! Билетов в банке: {total}\n"
                  f"Приз: {fmt(int(total * LOTTO_TICKET * 0.8))}{CUR}\nРозыгрыш: <code>/lotto draw</code> (админ)")


# 20 ── тир
@rt.message(Command("range", "tir"))
async def g_range(m: Message, command: CommandObject):
    await ensure(m.from_user)
    bet, err = bet_of(carg(command), m.from_user.id)
    if err:
        return await m.reply(err)
    pay(m.from_user.id, -bet)
    luck = 0.12 if iget(m.from_user.id, "clover") else 0.0
    shots = ["🎯" if random.random() < 0.55 + luck else "💨" for _ in range(5)]
    hits = shots.count("🎯")
    mult = {5: 6, 4: 2.5, 3: 1.3}.get(hits, 0)
    payout = int(bet * mult)
    await m.reply("🔫 " + " ".join(shots) + f"\nПопаданий {hits}/5 (×{mult})\n"
                  + end(m.from_user.id, bet, payout, mult > 1, "range"))


# ══════════════════ СИСТЕМЫ ══════════════════
HELP = ("🎮 <b>GAMEHUB</b> — 20 игр и 15 систем.\n\n"
        "🎲 Игры: /dice /slot /roulette /bj /coin /guess /rps /ttt /mines /hangman\n"
        "/anagram /quiz /highlow /bs /memory /bulls /duel /race /lotto /range\n\n"
        "📊 Системы:\n"
        "👤 /profile · 🎁 /daily · 💼 /work · 🏦 /bank · 🛒 /shop · 🎒 /inv\n"
        "🐾 /pet · 🛡 /clan · 📜 /quests · 🏅 /ach · 🤝 /ref · 🏆 /top\n"
        "📈 /market · 🥷 /rob · 👹 /boss (в чате) · 🏟 /tourney (в чате)\n\n"
        "Ставка указывается сразу: <code>/slot 100</code>, можно <code>all</code> или <code>half</code>.\n"
        "Работаю и в ЛС, и в группах — баланс общий.")


@rt.message(CommandStart())
async def cmd_start(m: Message, command: CommandObject):
    ref = 0
    if command.args and command.args.startswith("ref_"):
        ref = int(command.args[4:]) if command.args[4:].isdigit() else 0
    new = await ensure(m.from_user, ref)
    await m.reply(HELP + (f"\n\n🎉 Ты новичок — на счету <b>{fmt(START_BAL)}{CUR}</b>." if new else
                          f"\n\nБаланс: <b>{fmt(bal(m.from_user.id))}{CUR}</b>."), disable_web_page_preview=True)


@rt.message(Command("help", "menu"))
async def cmd_help(m: Message):
    await ensure(m.from_user)
    await m.reply(HELP, disable_web_page_preview=True)


# 1-2 ── профиль и уровни
@rt.message(Command("profile", "me"))
async def cmd_profile(m: Message):
    await ensure(m.from_user)
    t = m.reply_to_message.from_user if m.reply_to_message else m.from_user
    row = u(t.id)
    if not row:
        return await m.reply("Игрок ещё не начинал — пусть напишет /start.")
    lv = lvl(row["xp"])
    pr = row["xp"] - (lv - 1) * 150
    bar = "█" * int(pr / 15) + "░" * (10 - int(pr / 15))
    clan = sc("SELECT name FROM clans WHERE clan_id=?", (row["clan"],))
    await m.reply f"👤 <b>{t.full_name}</b>\nУровень <b>{lv}</b> [{bar}] {pr}/150 XP\n"
                  f"Баланс: <b>{fmt(row['balance'])}{CUR}</b> · Банк: {fmt(row['bank'])}{CUR}\n"
                  f"Игры: {row['games']} · Победы: {row['wins']} · Оборот: {fmt(row['bet_sum'])}{CUR}\n"
                  f"🐾 Питомец: {(row['pet'] + f' (ур. {row[\"pet_lvl\"]})') if row['pet'] else '—'}\n"
                  f"🛡 Клан: {clan or '—'} · 🔥 Стрик: {row['streak']} дн."


# 3 ── daily
@rt.message(Command("daily", "bonus"))
async def cmd_daily(m: Message):
    await ensure(m.from_user)
    row = u(m.from_user.id)
    delta = ts() - row["daily_ts"]
    if delta < 20 * 3600:
        left = 20 * 3600 - delta
        return await m.reply(f"⏳ Бонус уже взят. Через {left // 3600} ч {left % 3600 // 60} мин.")
    streak = row["streak"] + 1 if delta < 48 * 3600 else 1
    amount = DAILY_BASE + (streak - 1) * DAILY_STREAK
    ex("UPDATE users SET balance=balance+?, daily_ts=?, streak=? WHERE user_id=?",
       (amount, ts(), streak, m.from_user.id))
    check_ach(m.from_user.id)
    await m.reply(f"🎁 +<b>{fmt(amount)}{CUR}</b>\n🔥 Стрик: {streak} дн. "
                  f"(следующий ≈ {fmt(amount + DAILY_STREAK)}{CUR})")


# 4 ── work
@rt.message(Command("work"))
async def cmd_work(m: Message):
    await ensure(m.from_user)
    row = u(m.from_user.id)
    if ts() - row["work_ts"] < 3600:
        left = 3600 - (ts() - row["work_ts"])
        return await m.reply(f"😮‍💨 Отдохни {left // 60} мин {left % 60} сек.")
    jobs = ["разгружал вагоны", "чинил бота", "ловил рыбу", "писал код", "водил такси",
            "тестировал игры", "копа́л алмазы", "стримил"]
    earned = random.randint(WORK_MIN, WORK_MAX)
    ex("UPDATE users SET balance=balance+?, work_ts=?, xp=xp+5 WHERE user_id=?",
       (earned, ts(), m.from_user.id))
    qbump(m.from_user.id, "work")
    check_ach(m.from_user.id)
    await m.reply(f"💼 Ты {random.choice(jobs)} и заработал <b>+{fmt(earned)}{CUR}</b> (+5 XP)")


# 5 ── bank
@rt.message(Command("bank"))
async def cmd_bank(m: Message, command: CommandObject):
    await ensure(m.from_user)
    uid = m.from_user.id
    p = cargs(command)
    row = u(uid)
    if p and p[0] in ("dep", "взнос") and len(p) > 1:
        amount, err = bet_of(p[1], uid, 100)
        if err:
            return await m.reply(err)
        pay(uid, -amount)
        ex("UPDATE users SET bank=bank+?, bank_ts=? WHERE user_id=?", (amount, ts(), uid))
        return await m.reply(f"🏦 Вклад: {fmt(amount)}{CUR} под {int(BANK_RATE * 100)}% в сутки.")
    if p and p[0] in ("get", "снять"):
        if ts() - row["bank_ts"] < 3600:
            return await m.reply("Минимальный срок вклада — 1 час.")
        days = min(BANK_DAYS, max(1, (ts() - row["bank_ts"]) // 86400))
        total = int(row["bank"] * (1 + BANK_RATE * days))
        ex("UPDATE users SET bank=0, bank_ts=0, balance=balance+? WHERE user_id=?", (total, uid))
        return await m.reply(f"🏦 Снял {fmt(total)}{CUR} (вклад {fmt(row['bank'])} + проценты за {days} дн.)")
    d = min(BANK_DAYS, max(0, (ts() - row["bank_ts"]) // 86400)) if row["bank"] else 0
    await m.reply(f"🏦 <b>Банк</b>\nВклад: {fmt(row['bank'])}{CUR} (+{fmt(int(row['bank'] * BANK_RATE * d))}{CUR})\n"
                  f"Ставка: {int(BANK_RATE * 100)}% в сутки, максимум {BANK_DAYS} дн.\n\n"
                  "<code>/bank dep 10000</code> — положить\n<code>/bank get</code> — снять")


# 6 ── shop + inv
@rt.message(Command("shop"))
async def cmd_shop(m: Message):
    await ensure(m.from_user)
    kb = K(inline_keyboard=[[B(text=f"{v[0]} — {fmt(v[1])}{CUR}", callback_data=f"shop:{k}")]
                            for k, v in SHOP.items()])
    await m.reply("🛒 <b>Магазин</b>\n" + "\n".join(f"{v[0]} — <b>{fmt(v[1])}{CUR}</b>"
                                                    for v in SHOP.values()), reply_markup=kb)


@rt.callback_query(F.data.startswith("shop:"))
async def cb_shop(cb: CallbackQuery):
    key = cb.data.split(":")[1]
    name, price = SHOP[key]
    if bal(cb.from_user.id) < price:
        return await cb.answer("Не хватает монет", show_alert=True)
    pay(cb.from_user.id, -price)
    iadd(cb.from_user.id, key)
    await cb.answer(f"Куплено: {name}", show_alert=True)


@rt.message(Command("inv"))
async def cmd_inv(m: Message):
    await ensure(m.from_user)
    rows = qa("SELECT item, qty FROM inv WHERE user_id=? AND qty>0", (m.from_user.id,))
    if not rows:
        return await m.reply("🎒 Инвентарь пуст, загляни в /shop")
    await m.reply("🎒 <b>Инвентарь</b>\n" + "\n".join(
        f"{SHOP.get(x['item'], (x['item'], 0))[0]} ×{x['qty']}" for x in rows),
        reply_markup=K(inline_keyboard=[[B(text="🚀 Использовать бустер", callback_data="use:boost")]]))


@rt.callback_query(F.data == "use:boost")
async def cb_boost(cb: CallbackQuery):
    if not itake(cb.from_user.id, "boost"):
        return await cb.answer("Бустера нет", show_alert=True)
    ex("UPDATE users SET xp=xp+50 WHERE user_id=?", (cb.from_user.id,))
    await cb.answer("Бустер применён: +50 XP", show_alert=True)


# 7 ── питомец
@rt.message(Command("pet"))
async def cmd_pet(m: Message, command: CommandObject):
    await ensure(m.from_user)
    uid, row, p = m.from_user.id, u(m.from_user.id), cargs(command)
    if not row["pet"]:
        if not p:
            return await m.reply("🐾 Питомца нет. Придумай имя: <code>/pet Барсик</code>")
        ex("UPDATE users SET pet=?, pet_lvl=1, pet_ts=? WHERE user_id=?", (p[0][:16], ts(), uid))
        return await m.reply(f"🐾 Питомец <b>{p[0][:16]}</b> завёлся! Корми (/pet feed) — растёт и приносит монеты.")
    if p and p[0] == "feed":
        if bal(uid) < 100:
            return await m.reply("Корм стоит 100" + CUR + ", монет не хватает.")
        pay(uid, -100)
        lv = row["pet_lvl"] + 1 if random.random() < 0.6 else row["pet_lvl"]
        ex("UPDATE users SET pet_lvl=?, pet_ts=? WHERE user_id=?", (lv, ts(), uid))
        qbump(uid, "feed")
        check_ach(uid)
        return await m.reply(f"🍖 {row['pet']} покормлен, уровень <b>{lv}</b>")
    if p and p[0] == "claim":
        if ts() - row["pet_ts"] < 4 * 3600:
            left = 4 * 3600 - (ts() - row["pet_ts"])
            return await m.reply(f"⏳ Питомец устал, через {left // 3600} ч {left % 3600 // 60} мин.")
        income = row["pet_lvl"] * 120
        pay(uid, income)
        ex("UPDATE users SET pet_ts=? WHERE user_id=?", (ts(), uid))
        return await m.reply(f"💰 {row['pet']} принёс <b>+{fmt(income)}{CUR}</b> (ур. {row['pet_lvl']})")
    await m.reply(f"🐾 <b>{row['pet']}</b> · уровень <b>{row['pet_lvl']}</b>\n"
                  f"Доход: {fmt(row['pet_lvl'] * 120)}{CUR} каждые 4 часа\n\n"
                  f"<code>/pet feed</code> — покормить (100{CUR})\n<code>/pet claim</code> — собрать доход")


# 8 ── клан
@rt.message(Command("clan"))
async def cmd_clan(m: Message, command: CommandObject):
    await ensure(m.from_user)
    uid, row, p = m.from_user.id, u(m.from_user.id), cargs(command)
    sub = p[0].lower() if p else "info"
    if sub == "create" and len(p) > 1:
        if row["clan"]:
            return await m.reply("Ты уже в клане.")
        if bal(uid) < CLAN_COST:
            return await m.reply(f"Создание клана — {fmt(CLAN_COST)}{CUR}.")
        pay(uid, -CLAN_COST)
        ex("INSERT INTO clans(name,owner) VALUES(?,?)", (p[1][:20], uid))
        cid = sc("SELECT clan_id FROM clans WHERE owner=? ORDER BY clan_id DESC LIMIT 1", (uid,))
        ex("UPDATE users SET clan=? WHERE user_id=?", (cid, uid))
        return await m.reply(f"🛡 Клан <b>{p[1][:20]}</b> создан! Вступают: <code>/clan join {cid}</code>")
    if sub == "join" and len(p) > 1 and p[1].isdigit():
        cid = int(p[1])
        if not sc("SELECT 1 FROM clans WHERE clan_id=?", (cid,)):
            return await m.reply("Такого клана нет.")
        ex("UPDATE users SET clan=? WHERE user_id=?", (cid, uid))
        check_ach(uid)
        return await m.reply(f"🛡 Ты в клане <b>{sc('SELECT name FROM clans WHERE clan_id=?', (cid,))}</b>")
    if sub in ("dep", "взнос") and len(p) > 1:
        if not row["clan"]:
            return await m.reply("Сначала вступи в клан.")
        amount, err = bet_of(p[1], uid, 100)
        if err:
            return await m.reply(err)
        pay(uid, -amount)
        ex("UPDATE clans SET treasury=treasury+? WHERE clan_id=?", (amount, row["clan"]))
        return await m.reply(f"💰 В казну внесено {fmt(amount)}{CUR}.")
    if sub == "leave":
        ex("UPDATE users SET clan=0 WHERE user_id=?", (uid,))
        return await m.reply("Ты покинул клан.")
    if sub == "top":
        rows = qa("SELECT c.name, c.treasury, COUNT(u.user_id) n FROM clans c "
                  "LEFT JOIN users u ON u.clan=c.clan_id GROUP BY c.clan_id ORDER BY c.treasury DESC LIMIT 10")
        if not rows:
            return await m.reply("Кланов пока нет.")
        return await m.reply("🛡 <b>Топ кланов</b>\n" + "\n".join(
            f"{i}. {x['name']} — казна {fmt(x['treasury'])}{CUR}, игроков {x['n']}"
            for i, x in enumerate(rows, 1)))
    if not row["clan"]:
        return await m.reply(f"🛡 Ты без клана.\nСоздать: <code>/clan create Название</code> "
                             f"({fmt(CLAN_COST)}{CUR})\nВступить: <code>/clan join ID</code>\n"
                             "Список: <code>/clan top</code>")
    c = q1("SELECT * FROM clans WHERE clan_id=?", (row["clan"],))
    members = qa("SELECT username, balance FROM users WHERE clan=? ORDER BY balance DESC LIMIT 10",
                 (row["clan"],))
    await m.reply(f"🛡 <b>{c['name']}</b> (id {c['clan_id']})\nКазна: {fmt(c['treasury'])}{CUR}\n"
                  + "\n".join(f"• {x['username'] or 'игрок'} — {fmt(x['balance'])}{CUR}" for x in members)
                  + "\n\n<code>/clan dep 5000</code> · <code>/clan leave</code>")


# 9 ── квесты
@rt.message(Command("quests"))
async def cmd_quests(m: Message, command: CommandObject):
    await ensure(m.from_user)
    uid = m.from_user.id
    qensure(uid)
    rows = qa("SELECT * FROM quests WHERE user_id=? AND day=?", (uid, day()))
    if carg(command) == "claim":
        got = 0
        for x in rows:
            if x["prog"] >= x["need"] and not x["done"]:
                ex("UPDATE quests SET done=1 WHERE user_id=? AND day=? AND qkey=?", (uid, day(), x["qkey"]))
                pay(uid, x["reward"])
                got += x["reward"]
        return await m.reply(f"✅ Получено <b>+{fmt(got)}{CUR}</b>" if got else "Пока нечего забирать.")
    lines = []
    for x in rows:
        state = "✅" if x["done"] else ("🎁 готово" if x["prog"] >= x["need"] else
                                        f"{min(x['prog'], x['need'])}/{x['need']}")
        lines.append(f"• {QPOOL[x['qkey']][0].format(n=x['need'])} — {state} (+{fmt(x['reward'])}{CUR})")
    await m.reply("📜 <b>Квесты дня</b>\n" + "\n".join(lines) + "\n\nЗабрать: <code>/quests claim</code>")


# 10 ── достижения
@rt.message(Command("ach"))
async def cmd_ach(m: Message):
    await ensure(m.from_user)
    have = {x["aid"] for x in qa("SELECT aid FROM ach WHERE user_id=?", (m.from_user.id,))}
    row = u(m.from_user.id)
    lines = [f"{'✅' if a in have else '🔒'} {t}" + (f" — {fmt(rew)}{CUR}" if rew and a not in have else "")
             for a, t, _, rew in ACH]
    await m.reply(f"🏅 <b>Достижения {len(have)}/{len(ACH)}</b>\n" + "\n".join(lines) +
                  f"\n\nПобеды: {row['wins']} · Игры: {row['games']} · Уровень: {lvl(row['xp'])}")


# 11 ── рефералы
@rt.message(Command("ref"))
async def cmd_ref(m: Message):
    await ensure(m.from_user)
    me = await m.bot.get_me()
    cnt = sc("SELECT COUNT(*) FROM users WHERE ref_by=?", (m.from_user.id,))
    await m.reply(f"🤝 Приглашено игроков: <b>{cnt}</b> (по {fmt(REF_BONUS)}{CUR} за каждого)\n\n"
                  f"Твоя ссылка:\nt.me/{me.username}?start=ref_{m.from_user.id}")


# 12 ── топ
@rt.message(Command("top"))
async def cmd_top(m: Message, command: CommandObject):
    await ensure(m.from_user)
    mode = carg(command) or "bal"
    if mode in ("win", "wins"):
        rows = qa("SELECT username, user_id, wins v FROM users ORDER BY wins DESC LIMIT 10")
        title = "🏆 Топ по победам"
    elif mode == "clan":
        return await cmd_clan(m, CommandObject(prefix="/", command="clan", args="top"))
    else:
        rows = qa("SELECT username, user_id, balance v FROM users ORDER BY balance DESC LIMIT 10")
        title = "🏆 Топ по капиталу"
    if not rows:
        return await m.reply("Пока пусто.")
    await m.reply(f"{title} (сезон)\n" + "\n".join(
        f"{i}. {('@' + x['username']) if x['username'] else 'игрок ' + str(x['user_id'])} — {fmt(x['v'])}"
        + (CUR if mode not in ("win", "wins") else " побед") for i, x in enumerate(rows, 1))
        + "\n\n<code>/top win</code> · <code>/top clan</code>")


# 13 ── биржа
@rt.message(Command("market"))
async def cmd_market(m: Message, command: CommandObject):
    await ensure(m.from_user)
    p = cargs(command)
    uid = m.from_user.id
    if len(p) > 2 and p[0] in ("buy", "sell"):
        sym = p[1].upper()
        price = sc("SELECT price FROM stocks WHERE sym=?", (sym,))
        if not price:
            return await m.reply("Нет такого тикера, смотри /market")
        if not p[2].isdigit():
            return await m.reply("Количество — целое число.")
        qty = int(p[2])
        if p[0] == "buy":
            cost = price * qty
            if bal(uid) < cost:
                return await m.reply(f"Нужно {fmt(cost)}{CUR}, у тебя {fmt(bal(uid))}{CUR}.")
            pay(uid, -cost)
            ex("INSERT INTO holdings(user_id,sym,qty) VALUES(?,?,?) "
               "ON CONFLICT(user_id,sym) DO UPDATE SET qty=qty+?", (uid, sym, qty, qty))
            return await m.reply(f"📈 Куплено {qty} {sym} по {fmt(price)}{CUR} = {fmt(cost)}{CUR}")
        have = sc("SELECT qty FROM holdings WHERE user_id=? AND sym=?", (uid, sym)) or 0
        if have < qty:
            return await m.reply(f"У тебя только {have} {sym}.")
        ex("UPDATE holdings SET qty=qty-? WHERE user_id=? AND sym=?", (qty, uid, sym))
        pay(uid, price * qty)
        return await m.reply(f"📉 Продано {qty} {sym} за {fmt(price * qty)}{CUR}")
    for sym in STOCKS:
        old = sc("SELECT price FROM stocks WHERE sym=?", (sym,))
        new = max(20, int(old * (1 + random.uniform(-0.06, 0.07))))
        ex("UPDATE stocks SET prev=?, price=? WHERE sym=?", (old, new, sym))
    hold = {x["sym"]: x["qty"] for x in qa("SELECT sym,qty FROM holdings WHERE user_id=? AND qty>0", (uid,))}
    lines = []
    for x in qa("SELECT * FROM stocks ORDER BY price DESC"):
        d = x["price"] - x["prev"]
        lines.append(f"{'📈' if d > 0 else ('📉' if d < 0 else '➖')} <b>{x['sym']}</b> — {fmt(x['price'])}{CUR}"
                     f" ({'+' if d >= 0 else ''}{fmt(d)})" + (f" · у тебя {hold[x['sym']]}" if hold.get(x["sym"]) else ""))
    await m.reply("📊 <b>Биржа</b>\n" + "\n".join(lines) +
                  "\n\n<code>/market buy GHB 5</code> · <code>/market sell GHB 5</code>")


# 14 ── кража
@rt.message(Command("rob"))
async def cmd_rob(m: Message):
    await ensure(m.from_user)
    if not m.reply_to_message or m.reply_to_message.from_user.is_bot:
        return await m.reply("Ответь на сообщение игрока: <code>/rob</code>")
    foe = m.reply_to_message.from_user
    if foe.id == m.from_user.id:
        return await m.reply("Себя обокрасть не выйдет 🙂")
    await ensure(foe)
    if iget(foe.id, "shield"):
        itake(foe.id, "shield")
        return await m.reply(f"🛡 У {foe.full_name} был щит — кража сорвалась, щит сгорел.")
    victim = bal(foe.id)
    if victim < 200:
        return await m.reply(f"У {foe.full_name} брать нечего ({fmt(victim)}{CUR}).")
    if random.random() < 0.4:
        amount = max(100, min(5000, int(victim * random.uniform(0.08, 0.18))))
        ex("UPDATE users SET balance=balance-? WHERE user_id=?", (amount, foe.id))
        pay(m.from_user.id, amount)
        return await m.reply(f"🥷 Кража удалась: +{fmt(amount)}{CUR} из кармана {foe.full_name}.")
    fine = min(ROB_FINE, bal(m.from_user.id))
    pay(m.from_user.id, -fine)
    pay(foe.id, fine)
    return await m.reply(f"🚨 Поймали! Штраф {fmt(fine)}{CUR} ушёл {foe.full_name}.")


# 15 ── босс + турнир
HIT_CD, TOURN = {}, {}


@rt.message(Command("boss"))
async def cmd_boss(m: Message):
    await ensure(m.from_user)
    if m.chat.type == ChatType.PRIVATE:
        return await m.reply("👹 Боссы — для групп: добавь меня в чат и вызови там.")
    row = q1("SELECT * FROM bosses WHERE chat_id=?", (m.chat.id,))
    if not row or row["hp"] <= 0:
        ex("INSERT INTO bosses(chat_id,hp,max_hp) VALUES(?,?,?) ON CONFLICT(chat_id) "
           "DO UPDATE SET hp=excluded.hp, max_hp=excluded.max_hp", (m.chat.id, BOSS_HP, BOSS_HP))
        return await m.reply(f"👹 <b>Босс появился!</b> HP {fmt(BOSS_HP)}\nБей командой /hit — за удары платят.")
    await m.reply(f"👹 Босс жив: <b>{fmt(row['hp'])}</b>/{fmt(row['max_hp'])} HP\nБей: /hit")


@rt.message(Command("hit"))
async def cmd_hit(m: Message):
    await ensure(m.from_user)
    if m.chat.type == ChatType.PRIVATE:
        return await m.reply("Удары по боссу — в группе.")
    row = q1("SELECT * FROM bosses WHERE chat_id=?", (m.chat.id,))
    if not row or row["hp"] <= 0:
        return await m.reply("Босса нет. Вызови /boss")
    if ts() - HIT_CD.get((m.chat.id, m.from_user.id), 0) < 300:
        return await m.reply(f"⏳ Перезарядка {300 - (ts() - HIT_CD[(m.chat.id, m.from_user.id)])} сек.")
    HIT_CD[(m.chat.id, m.from_user.id)] = ts()
    dmg = random.randint(600, 1500)
    left = max(0, row["hp"] - dmg)
    ex("UPDATE bosses SET hp=? WHERE chat_id=?", (left, m.chat.id))
    pay(m.from_user.id, dmg // 10)
    if left == 0:
        pay(m.from_user.id, 8000)
        return await m.reply(f"💥 Удар на {fmt(dmg)} — босс повержен! Убийце +{fmt(8000)}{CUR} 🏆")
    await m.reply(f"⚔️ Удар на <b>{fmt(dmg)}</b>, осталось {fmt(left)} HP (+{fmt(dmg // 10)}{CUR})")


async def tourney_end(bot, chat_id):
    await asyncio.sleep(120)
    t = TOURN.pop(chat_id, None)
    if not t or not t["players"]:
        return
    winner = random.choice(t["players"])
    prize = int(t["pot"] * 0.9)
    pay(winner, prize)
    try:
        await bot.send_message(chat_id, f"🏟 Турнир завершён! Победитель получает <b>{fmt(prize)}{CUR}</b> 🏆")
    except Exception:
        pass


@rt.message(Command("tourney"))
async def cmd_tourney(m: Message, command: CommandObject):
    await ensure(m.from_user)
    if m.chat.type == ChatType.PRIVATE:
        return await m.reply("🏟 Турниры — в группах.")
    cid = m.chat.id
    t = TOURN.get(cid)
    if not t:
        bet, err = bet_of(carg(command), m.from_user.id, 100)
        if err:
            return await m.reply("Формат: <code>/tourney 500</code> — взнос и участие.")
        pay(m.from_user.id, -bet)
        TOURN[cid] = {"bet": bet, "pot": bet, "players": [m.from_user.id]}
        asyncio.create_task(tourney_end(m.bot, cid))
        return await m.reply(f"🏟 Турнир открыт! Взнос {fmt(bet)}{CUR}, приём 2 минуты.\n"
                             "Присоединиться: /tourney")
    if m.from_user.id in t["players"]:
        return await m.reply(f"Ты уже в турнире. Банк: {fmt(t['pot'])}{CUR}, участников {len(t['players'])}")
    bet = t["bet"]
    if bal(m.from_user.id) < bet:
        return await m.reply(f"Нужен взнос {fmt(bet)}{CUR}.")
    pay(m.from_user.id, -bet)
    t["pot"] += bet
    t["players"].append(m.from_user.id)
    await m.reply(f"🏟 Ты в турнире! Банк {fmt(t['pot'])}{CUR}, участников {len(t['players'])}")


# ══════════════════ АДМИНКА ══════════════════
def is_admin(uid):
    return uid in ADMINS


@rt.message(Command("admin"))
async def cmd_admin(m: Message):
    if not is_admin(m.from_user.id):
        return
    users = sc("SELECT COUNT(*) FROM users") or 0
    total = sc("SELECT COALESCE(SUM(balance),0) FROM users") or 0
    games = sc("SELECT COALESCE(SUM(games),0) FROM users") or 0
    await m.reply(
        f"🛠 <b>Админ-панель</b>\nИгроков: {users}\nМонет в обороте: {fmt(total)}{CUR}\nПартий: {fmt(games)}\n\n"
        "/give ID СУММА — выдать\n/take ID СУММА — списать\n/ban ID — бан\n/unban ID — разбан\n"
        "/broadcast ТЕКСТ — рассылка\n/logs 30 — последние операции\n/export — CSV по игрокам\n"
        "/tick — толчок биржи (курс вверх/вниз)\n/chatstat — статистика этого чата",
        reply_markup=K(inline_keyboard=[[B(text="📊 Статистика", callback_data="adm:stat"),
                                         B(text="📜 Логи", callback_data="adm:logs")],
                                        [B(text="🎮 Игры в чате: вкл/выкл", callback_data="adm:toggle")],
                                        [B(text="📈 Толчок биржи", callback_data="adm:tick")]]))


@rt.callback_query(F.data.startswith("adm:"))
async def cb_admin(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await cb.answer("Нет доступа", show_alert=True)
    act = cb.data.split(":")[1]
    if act == "stat":
        return await cb.answer(f"Игроков: {sc('SELECT COUNT(*) FROM users')}, "
                               f"бан {fmt(sc('SELECT COALESCE(SUM(balance),0) FROM users'))}", show_alert=True)
    if act == "logs":
        rows = qa("SELECT * FROM logs ORDER BY id DESC LIMIT 10")
        return await cb.answer("\n".join(f"{x['user_id']} {x['action']} {x['amount']}" for x in rows)[:200],
                               show_alert=True)
    if act == "toggle":
        cur = games_on(cb.message.chat.id)
        ex("UPDATE chats SET games_on=? WHERE chat_id=?", (0 if cur else 1, cb.message.chat.id))
        return await cb.answer(f"Игры в чате: {'выкл' if cur else 'вкл'}", show_alert=True)
    if act == "tick":
        for sym in STOCKS:
            old = sc("SELECT price FROM stocks WHERE sym=?", (sym,))
            ex("UPDATE stocks SET prev=?, price=? WHERE sym=?",
               (old, max(20, int(old * random.uniform(0.9, 1.15))), sym))
        return await cb.answer("Биржа дёрнулась 📈", show_alert=True)


def find_user(token):
    if token.isdigit():
        return u(int(token))
    row = q1("SELECT * FROM users WHERE username=?", (token.lstrip("@"),))
    return row


@rt.message(Command("give"))
async def cmd_give(m: Message, command: CommandObject):
    if not is_admin(m.from_user.id):
        return
    p = cargs(command)
    if len(p) < 2 or not p[1].isdigit():
        return await m.reply("Формат: <code>/give ID_или_@username СУММА</code>")
    row = find_user(p[0])
    if not row:
        return await m.reply("Игрок не найден.")
    try:
        amount = int(p[1])
    except ValueError:
        return await m.reply("Сумма — число.")
    pay(row["user_id"], amount)
    await m.reply(f"✅ Выдано {fmt(amount)}{CUR} игроку {row['user_id']}. Баланс: {fmt(bal(row['user_id']))}{CUR}")
    try:
        await m.bot.send_message(row["user_id"], f"🎁 Админ выдал тебе {fmt(amount)}{CUR}")
    except Exception:
        pass


@rt.message(Command("take"))
async def cmd_take(m: Message, command: CommandObject):
    if not is_admin(m.from_user.id):
        return
    p = cargs(command)
    if len(p) < 2 or not p[1].isdigit():
        return await m.reply("Формат: <code>/take ID СУММА</code>")
    row = find_user(p[0])
    if not row:
        return await m.reply("Игрок не найден.")
    amount = min(int(p[1]), row["balance"])
    pay(row["user_id"], -amount)
    await m.reply(f"✅ Списано {fmt(amount)}{CUR} у {row['user_id']}.")


@rt.message(Command("ban", "unban"))
async def cmd_ban(m: Message, command: CommandObject):
    if not is_admin(m.from_user.id):
        return
    flag = 1 if command.command == "ban" else 0
    row = find_user(carg(command))
    if not row:
        return await m.reply("Формат: <code>/ban ID</code>")
    ex("UPDATE users SET banned=? WHERE user_id=?", (flag, row["user_id"]))
    await m.reply(("🚫 Забанен " if flag else "✅ Разбанен ") + str(row["user_id"]))


@rt.message(Command("broadcast"))
async def cmd_broadcast(m: Message, command: CommandObject):
    if not is_admin(m.from_user.id):
        return
    text = (command.args or "").strip()
    if not text:
        return await m.reply("Формат: <code>/broadcast Текст сообщения</code>")
    ok = 0
    for row in qa("SELECT user_id FROM users"):
        try:
            await m.bot.send_message(row["user_id"], f"📢 {text}")
            ok += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)
    await m.reply(f"📢 Доставлено: {ok}")


@rt.message(Command("logs"))
async def cmd_logs(m: Message, command: CommandObject):
    if not is_admin(m.from_user.id):
        return
    n = int(carg(command)) if carg(command).isdigit() else 20
    rows = qa("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (min(n, 100),))
    if not rows:
        return await m.reply("Логов нет.")
    await m.reply("\n".join(f"• {x['user_id']} · {x['action']} · {x['amount']:+}" for x in rows))


@rt.message(Command("export"))
async def cmd_export(m: Message):
    if not is_admin(m.from_user.id):
        return
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["user_id", "username", "balance", "bank", "xp", "level", "games", "wins",
                "bet_sum", "win_sum", "clan", "pet", "banned"])
    for x in qa("SELECT * FROM users ORDER BY balance DESC"):
        w.writerow([x["user_id"], x["username"], x["balance"], x["bank"], x["xp"], lvl(x["xp"]),
                    x["games"], x["wins"], x["bet_sum"], x["win_sum"], x["clan"], x["pet"], x["banned"]])
    data = buf.getvalue().encode("utf-8")
    await m.reply_document(BufferedInputFile(data, filename="gamehub_players.csv"), caption="📤 Экспорт игроков")


@rt.message(Command("tick"))
async def cmd_tick(m: Message):
    if not is_admin(m.from_user.id):
        return
    for sym in STOCKS:
        old = sc("SELECT price FROM stocks WHERE sym=?", (sym,))
        ex("UPDATE stocks SET prev=?, price=? WHERE sym=?",
           (old, max(20, int(old * random.uniform(0.9, 1.15))), sym))
    await m.reply("📈 Курс обновлён.")


@rt.message(Command("chatstat"))
async def cmd_chatstat(m: Message):
    if not is_admin(m.from_user.id):
        return
    if m.chat.type == ChatType.PRIVATE:
        return await m.reply("Команда для групп.")
    games = bool(games_on(m.chat.id))
    boss = q1("SELECT * FROM bosses WHERE chat_id=?", (m.chat.id,))
    t = TOURN.get(m.chat.id)
    await m.reply(f"📊 <b>Чат {m.chat.id}</b>\nИгры: {'вкл' if games else 'выкл'}\n"
                  f"Босс: {fmt(boss['hp']) if boss else 'нет'}\n"
                  f"Турнир: {fmt(t['pot']) + CUR if t else 'нет'}")


# ══════════════════ ЗАПУСК ══════════════════
async def main():
    if not TOKEN:
        raise SystemExit("Не задан BOT_TOKEN. Запуск: BOT_TOKEN=... ADMIN_IDS=... python bot.py")
    init_db()
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(Guard())
    dp.include_router(rt)
    await bot.set_my_commands([
        ("start", "Меню и все команды"), ("daily", "Бонус дня"), ("work", "Заработок"),
        ("profile", "Профиль"), ("top", "Топ игроков"), ("quests", "Квесты дня"),
        ("shop", "Магазин"), ("pet", "Питомец"), ("clan", "Клан"), ("market", "Биржа"),
        ("mines", "Сапёр"), ("slot", "Слоты"), ("ttt", "Крестики-нолики")])
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

