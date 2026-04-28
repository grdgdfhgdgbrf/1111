import asyncio
import random
import hashlib
import hmac
import json
import time
from datetime import datetime, date
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler
from telegram.constants import ParseMode

# ================= КОНФИГУРАЦИЯ =================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Замените на токен вашего бота
ADMIN_IDS = [123456789]  # Список ID администраторов (замените)
STARS_PRICE = 1  # 1 звезда = 1 рубль (или любая валюта)
MIN_WITHDRAW = 100
WITHDRAW_COOLDOWN_HOURS = 24
MAX_WITHDRAWS_PER_DAY = 3
DAILY_LOSS_LIMIT = 50000
DAILY_WIN_LIMIT = 100000
CONSECUTIVE_LOSS_LIMIT = 10
MIN_BALANCE_TO_PLAY = 10
REFERRAL_BONUS = 50
REFERRAL_PERCENT = 5
CHECKSYSTEM_PRICE = 500

# ================= ХРАНИЛИЩЕ В ПАМЯТИ =================
users: Dict[int, dict] = {}  # user_id -> данные
referrals: Dict[int, List[int]] = defaultdict(list)  # реферер -> список рефералов
withdraw_requests: Dict[int, dict] = {}  # user_id -> последний запрос
tickets: Dict[int, dict] = {}  # ticket_id -> данные
promocodes: Dict[str, dict] = {}  # код -> данные
cheques: Dict[str, dict] = {}  # код чека -> данные
tasks: Dict[int, dict] = {}  # task_id -> данные
admin_logs: List[dict] = []
banned_withdraw: set = set()
check_system_unlocked: Dict[int, bool] = defaultdict(bool)

# Вспомогательные структуры для игр
user_games: Dict[int, dict] = defaultdict(lambda: {"loss_streak": 0, "daily_win": 0, "daily_loss": 0})
crash_games: Dict[int, float] = {}  # user_id -> текущая игра
mines_games: Dict[int, dict] = {}  # user_id -> состояние игры

# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================
def get_user(user_id: int) -> dict:
    if user_id not in users:
        users[user_id] = {
            "balance": 100,  # стартовый бонус
            "total_won": 0,
            "total_lost": 0,
            "total_games": 0,
            "wins": 0,
            "referrer_id": None,
            "ref_earnings": 0,
            "last_withdraw_time": 0,
            "withdraws_today": 0,
            "last_withdraw_date": None,
        }
    return users[user_id]

def save_stats():
    # В RAM не нужно сохранять, но можно при желании добавить файл
    pass

def update_daily_limits(user_id: int, amount: int, is_win: bool):
    today = str(date.today())
    g = user_games[user_id]
    if g.get("last_date") != today:
        g["daily_win"] = 0
        g["daily_loss"] = 0
        g["last_date"] = today
    if is_win:
        g["daily_win"] += amount
    else:
        g["daily_loss"] += amount

def check_limits(user_id: int, bet: int, potential_win: int) -> Tuple[bool, str]:
    g = user_games[user_id]
    if g.get("loss_streak", 0) >= CONSECUTIVE_LOSS_LIMIT:
        return False, "⚠️ У вас слишком много проигрышей подряд. Сделайте паузу."
    if g["daily_loss"] + bet > DAILY_LOSS_LIMIT:
        return False, f"⚠️ Дневной лимит проигрыша ({DAILY_LOSS_LIMIT}⭐)."
    if g["daily_win"] + potential_win > DAILY_WIN_LIMIT:
        return False, f"⚠️ Дневной лимит выигрыша ({DAILY_WIN_LIMIT}⭐) будет превышен."
    return True, ""

def add_money(user_id: int, amount: int, reason=""):
    user = get_user(user_id)
    user["balance"] += amount
    if reason:
        log_action(user_id, f"Начислено {amount}⭐. {reason}")

def subtract_money(user_id: int, amount: int, reason=""):
    user = get_user(user_id)
    if user["balance"] >= amount:
        user["balance"] -= amount
        if reason:
            log_action(user_id, f"Списано {amount}⭐. {reason}")
        return True
    return False

def log_action(user_id: int, action: str):
    admin_logs.append({"user_id": user_id, "action": action, "time": time.time()})

def generate_hash(seed: str, salt: str) -> str:
    return hashlib.sha256(f"{seed}{salt}".encode()).hexdigest()

# ================= ИГРЫ =================
async def play_coin(update: Update, ctx: ContextTypes.DEFAULT_TYPE, user_id: int, bet: int, choice: str):
    if bet < MIN_BALANCE_TO_PLAY:
        await update.message.reply_text(f"❌ Минимальная ставка {MIN_BALANCE_TO_PLAY}⭐")
        return
    user = get_user(user_id)
    if user["balance"] < bet:
        await update.message.reply_text("❌ Недостаточно средств")
        return
    result = random.choice(["орел", "решка"])
    win = (result == choice)
    potential_win = int(bet * 1.95)
    ok, msg = check_limits(user_id, bet, potential_win if win else 0)
    if not ok:
        await update.message.reply_text(msg)
        return
    user["balance"] -= bet
    user["total_games"] += 1
    if win:
        user["balance"] += potential_win
        user["total_won"] += potential_win
        user["wins"] += 1
        user_games[user_id]["loss_streak"] = 0
        update_daily_limits(user_id, potential_win, True)
        await update.message.reply_text(f"🪙 Монета выпала: {result}\n✅ Вы выиграли {potential_win}⭐!")
    else:
        user["total_lost"] += bet
        user_games[user_id]["loss_streak"] += 1
        update_daily_limits(user_id, bet, False)
        await update.message.reply_text(f"🪙 Монета выпала: {result}\n❌ Вы проиграли {bet}⭐")

async def play_roulette(update: Update, ctx: ContextTypes.DEFAULT_TYPE, user_id: int, bet: int, bet_type: str):
    if bet < MIN_BALANCE_TO_PLAY:
        await update.message.reply_text(f"❌ Минимальная ставка {MIN_BALANCE_TO_PLAY}⭐")
        return
    user = get_user(user_id)
    if user["balance"] < bet:
        await update.message.reply_text("❌ Недостаточно средств")
        return
    num = random.randint(0, 36)
    color = "красное" if num % 2 == 1 else "черное" if num != 0 else "zero"
    parity = "четное" if num % 2 == 0 and num != 0 else "нечетное" if num != 0 else "zero"
    win = False
    if bet_type == "красное" and color == "красное": win = True
    elif bet_type == "черное" and color == "черное": win = True
    elif bet_type == "четное" and parity == "четное": win = True
    elif bet_type == "нечетное" and parity == "нечетное": win = True
    potential_win = int(bet * 1.95)
    ok, msg = check_limits(user_id, bet, potential_win if win else 0)
    if not ok:
        await update.message.reply_text(msg)
        return
    user["balance"] -= bet
    user["total_games"] += 1
    if win:
        user["balance"] += potential_win
        user["total_won"] += potential_win
        user["wins"] += 1
        user_games[user_id]["loss_streak"] = 0
        update_daily_limits(user_id, potential_win, True)
        await update.message.reply_text(f"🎱 Выпало число {num} ({color})\n✅ Вы выиграли {potential_win}⭐!")
    else:
        user["total_lost"] += bet
        user_games[user_id]["loss_streak"] += 1
        update_daily_limits(user_id, bet, False)
        await update.message.reply_text(f"🎱 Выпало число {num} ({color})\n❌ Вы проиграли {bet}⭐")

# Здесь аналогично реализуются остальные игры: cubes, crash, mines, diamond, blackjack, fortune, knb, poker, keno, wheel
# Из-за ограничения длины кода — сокращённые версии, в полной версии все 12 игр.

# ================= ПОЛЬЗОВАТЕЛЬСКИЕ СИСТЕМЫ =================
async def profile(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    u = get_user(user_id)
    g = user_games[user_id]
    winrate = 0
    if u["total_games"] > 0:
        winrate = u["wins"] / u["total_games"] * 100
    text = (
        f"⭐ ПРОФИЛЬ ⭐\n\n"
        f"💰 Баланс: {u['balance']}⭐\n"
        f"🎮 Игр сыграно: {u['total_games']}\n"
        f"🏆 Побед: {u['wins']}\n"
        f"📈 Процент побед: {winrate:.1f}%\n"
        f"💸 Всего выиграно: {u['total_won']}⭐\n"
        f"💀 Всего проиграно: {u['total_lost']}⭐\n"
        f"📅 Серия проигрышей: {g.get('loss_streak',0)}\n"
        f"📊 Дневной выигрыш: {g.get('daily_win',0)}⭐\n"
        f"📉 Дневной проигрыш: {g.get('daily_loss',0)}⭐"
    )
    keyboard = [[InlineKeyboardButton("🎁 Реферальная ссылка", callback_data="ref_link")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    await update.message.reply_text(f"💰 Ваш баланс: {u['balance']}⭐")

async def deposit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for amount in [100, 500, 1000, 5000, 10000, 50000]:
        keyboard.append([InlineKeyboardButton(f"{amount}⭐", callback_data=f"deposit_{amount}")])
    keyboard.append([InlineKeyboardButton("🔢 Своя сумма", callback_data="deposit_custom")])
    await update.message.reply_text("💎 Пополнение через Telegram Stars\nВыберите сумму:", reply_markup=InlineKeyboardMarkup(keyboard))

async def deposit_custom(update: Update, ctx: ContextTypes.DEFAULT_TYPE, amount: int):
    user_id = update.effective_user.id
    if amount < 50 or amount > 100000:
        await update.message.reply_text("Сумма от 50 до 100000⭐")
        return
    prices = [LabeledPrice(label="X Stars", amount=amount * STARS_PRICE)]
    await ctx.bot.send_invoice(
        chat_id=user_id,
        title="Пополнение баланса",
        description=f"Начисление {amount}⭐",
        payload=f"stars_{amount}",
        provider_token="",  # для Stars не нужен
        currency="XTR",
        prices=prices,
        need_name=False,
        need_email=False,
        is_flexible=False,
    )

async def pre_checkout(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    payload = update.message.successful_payment.invoice_payload
    amount = int(payload.split("_")[1])
    add_money(user_id, amount, "Пополнение через Stars")
    if get_user(user_id).get("referrer_id"):
        ref_id = get_user(user_id)["referrer_id"]
        ref_bonus = int(amount * REFERRAL_PERCENT / 100)
        add_money(ref_id, ref_bonus, f"Реферальный бонус от {user_id}")
        get_user(ref_id)["ref_earnings"] += ref_bonus
    await update.message.reply_text(f"✅ Пополнение на {amount}⭐ выполнено!")

# ================= АДМИН ПАНЕЛЬ (упрощённо) =================
async def admin_add_stars(update: Update, ctx: ContextTypes.DEFAULT_TYPE, user_id: int, amount: int):
    if update.effective_user.id not in ADMIN_IDS:
        return
    add_money(user_id, amount, "Админское начисление")
    await update.message.reply_text(f"✅ Добавлено {amount}⭐ пользователю {user_id}")

# ================= ОСНОВНОЙ ХЕНДЛЕР =================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ref_code = ctx.args[0] if ctx.args else None
    if ref_code and ref_code.isdigit() and int(ref_code) != user_id:
        ref_id = int(ref_code)
        if ref_id in users or get_user(ref_id):
            if not get_user(user_id).get("referrer_id"):
                get_user(user_id)["referrer_id"] = ref_id
                referrals[ref_id].append(user_id)
                add_money(ref_id, REFERRAL_BONUS, f"Реферальный бонус за {user_id}")
                add_money(user_id, REFERRAL_BONUS, "Бонус за регистрацию по ссылке")
    keyboard = [
        ["🎮 ИГРЫ", "⭐ ПРОФИЛЬ"],
        ["💰 БАЛАНС", "🛒 ПОПОЛНИТЬ"],
        ["🎫 ПРОМОКОД", "📦 ЧЕК СИСТЕМА"],
        ["👥 РЕФЕРАЛЫ", "📋 ЗАДАНИЯ"],
        ["💬 ПОДДЕРЖКА", "❓ ПОМОЩЬ"]
    ]
    await update.message.reply_text(
        "✨ Добро пожаловать в игровой бот!\nЗарабатывай и выводи Telegram Stars! ✨",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=text)] for row in keyboard for text in row])
    )

async def games_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🪙 Монета (x1.95)", "🎱 Рулетка (x1.95)"],
        ["🎲 Кости (x5.5)", "📈 Crash (x1-50)"],
        ["💣 Mines (x1-25)", "🤩 Алмаз (x2)"],
        ["♠️ 21 очко (x2.1)", "🔮 Фортуна (x0-50)"],
        ["✂️ КНБ (x2.7)", "🃏 Покер (x0-100)"],
        ["🎯 Кено (x0-20)", "🎰 Колесо (x0-10)"],
        ["◀️ НАЗАД"]
    ]
    kb = [[InlineKeyboardButton(text, callback_data=text)] for text in keyboard[0]] + [[InlineKeyboardButton(text, callback_data=text)] for text in keyboard[1]] + [[InlineKeyboardButton("◀️ НАЗАД", callback_data="main_menu")]]
    await update.message.reply_text("🎮 Выбери игру:", reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("deposit_"):
        amount = int(data.split("_")[1])
        await deposit_custom(update, ctx, amount)
    elif data == "main_menu":
        await start(update, ctx)
    elif data in ["🎮 ИГРЫ", "Игры"]:
        await games_menu(update, ctx)
    else:
        await query.edit_message_text("🚧 В разработке. Используйте команды.")

# ================= ЗАПУСК =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("add_stars", admin_add_stars))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(CallbackQueryHandler(callback_handler))
    # Здесь добавить обработчики для всех игр, рефералов, чеков, заданий, поддержки
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
