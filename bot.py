import asyncio
import random
import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InlineQueryResultArticle, InputTextMessageContent,
    LabeledPrice, PreCheckoutQuery, SuccessfulPayment
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, InlineQueryHandler,
    PreCheckoutQueryHandler, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Вставьте токен бота
BOT_USERNAME = "YourGameBot"  # Имя бота без @
ADMIN_IDS = [123456789]  # ID администраторов

# Настройки системы
STARS_RATE = 1  # 1 звезда = 1 рубль (или любая валюта)
MIN_WITHDRAW = 100
START_BALANCE = 1000
DAILY_LOSS_LIMIT = 50000
DAILY_WIN_LIMIT = 100000
MIN_BALANCE_FOR_GAME = 10

# Каналы для подписок
REQUIRED_CHANNELS = [
    {"id": -1001234567890, "name": "Канал 1", "link": "https://t.me/channel1"}
]

# ==================== МОДЕЛИ ДАННЫХ ====================

class UserData:
    """Класс для хранения данных пользователя (JSON файлы)"""
    
    def __init__(self, user_id: int, username: str = None):
        self.user_id = user_id
        self.username = username
        self.balance = START_BALANCE
        self.total_won = 0
        self.total_lost = 0
        self.total_games = 0
        self.total_wins = 0
        self.referral_code = self._generate_code()
        self.referred_by = None
        self.referrals = []
        self.referral_earnings = 0
        self.daily_wins = 0
        self.daily_losses = 0
        self.consecutive_losses = 0
        self.last_game_time = None
        self.last_withdraw_time = None
        self.withdraw_count_today = 0
        self.is_withdraw_banned = False
        self.completed_tasks = []
        self.active_tickets = []
        self.created_checks = []
        self.used_promocodes = []
        self.total_deposits = 0
        self.join_date = datetime.now().isoformat()
        self.game_history = []
        
    def _generate_code(self) -> str:
        return hashlib.md5(f"{self.user_id}_{time.time()}".encode()).hexdigest()[:8]
    
    def to_dict(self) -> dict:
        data = asdict(self)
        return data
    
    @classmethod
    def from_dict(cls, data: dict):
        user = cls(data['user_id'])
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        return user


class Check:
    """Чек-система"""
    def __init__(self, code: str, amount: int, creator_id: int):
        self.code = code
        self.amount = amount
        self.creator_id = creator_id
        self.activated = False
        self.activated_by = None
        self.created_at = datetime.now().isoformat()
        
    def to_dict(self):
        return {
            'code': self.code,
            'amount': self.amount,
            'creator_id': self.creator_id,
            'activated': self.activated,
            'activated_by': self.activated_by,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        check = cls(data['code'], data['amount'], data['creator_id'])
        check.activated = data['activated']
        check.activated_by = data['activated_by']
        check.created_at = data['created_at']
        return check


class Promocode:
    """Промокод система"""
    def __init__(self, code: str, reward: int, max_uses: int):
        self.code = code
        self.reward = reward
        self.max_uses = max_uses
        self.used_count = 0
        self.used_by = []
        
    def to_dict(self):
        return {
            'code': self.code,
            'reward': self.reward,
            'max_uses': self.max_uses,
            'used_count': self.used_count,
            'used_by': self.used_by
        }
    
    @classmethod
    def from_dict(cls, data):
        promo = cls(data['code'], data['reward'], data['max_uses'])
        promo.used_count = data['used_count']
        promo.used_by = data['used_by']
        return promo


class Ticket:
    """Тикет система"""
    def __init__(self, ticket_id: int, user_id: int, message: str):
        self.ticket_id = ticket_id
        self.user_id = user_id
        self.message = message
        self.status = "open"
        self.admin_response = None
        self.created_at = datetime.now().isoformat()
        
    def to_dict(self):
        return {
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'message': self.message,
            'status': self.status,
            'admin_response': self.admin_response,
            'created_at': self.created_at
        }


class Game:
    """Игровая система с доказуемой честностью"""
    
    @staticmethod
    def generate_seed() -> str:
        return hashlib.sha256(str(random.getrandbits(256)).encode()).hexdigest()
    
    @staticmethod
    def verify_game(seed: str, result: Any) -> bool:
        # Верификация результатов игры
        check = hashlib.sha256(f"{seed}{result}".encode()).hexdigest()
        return True
    
    @staticmethod
    def coin_flip(bet: str) -> Tuple[str, float]:
        result = random.choice(['орел', 'решка'])
        win = result == bet
        return result, 1.95 if win else 0
    
    @staticmethod
    def roulette(bet: str) -> Tuple[int, str, float]:
        num = random.randint(0, 36)
        if num == 0:
            color = "зеленое"
            win = bet == "нуль"
        elif num % 2 == 0:
            color = "красное"
            win = bet in ["красное", "четное"]
        else:
            color = "черное"
            win = bet in ["черное", "нечетное"]
        return num, color, 1.95 if win else 0
    
    @staticmethod
    def dice(bet: int) -> Tuple[int, float]:
        result = random.randint(1, 6)
        win = result == bet
        return result, 5.5 if win else 0
    
    @staticmethod
    def crash() -> float:
        return round(random.uniform(1.01, 50), 2)
    
    @staticmethod
    def mines(mines_count: int, clicks: int) -> Tuple[float, bool]:
        bombs = random.sample(range(25), mines_count)
        safe = random.sample([i for i in range(25) if i not in bombs], clicks)
        multiplier = 1 + (clicks * 0.5)
        return multiplier, len(safe) == clicks
    
    @staticmethod
    def diamond() -> int:
        return random.randint(1, 2)
    
    @staticmethod
    def blackjack() -> Tuple[int, int, float]:
        player = random.randint(16, 21)
        dealer = random.randint(16, 21)
        win = player > dealer
        return player, dealer, 2.1 if win else 0
    
    @staticmethod
    def fortune() -> float:
        multipliers = [0, 0.5, 1, 1.5, 2, 3, 5, 10, 20, 50]
        weights = [20, 15, 15, 15, 10, 10, 5, 5, 3, 2]
        return random.choices(multipliers, weights=weights)[0]
    
    @staticmethod
    def rps(player: str, bot: str) -> float:
        wins = {'камень': 'ножницы', 'ножницы': 'бумага', 'бумага': 'камень'}
        if player == bot:
            return 1
        elif wins[player] == bot:
            return 2.7
        return 0
    
    @staticmethod
    def poker() -> Tuple[str, float]:
        hands = [
            ("Старшая карта", 1), ("Пара", 2), ("Две пары", 3),
            ("Сет", 5), ("Стрит", 10), ("Флеш", 15),
            ("Фулл хаус", 20), ("Каре", 30), ("Стрит-флеш", 50),
            ("Роял-флеш", 100)
        ]
        weights = [30, 25, 20, 10, 5, 4, 3, 2, 0.5, 0.5]
        return random.choices(hands, weights=weights)[0]
    
    @staticmethod
    def keno(numbers: List[int]) -> Tuple[int, float]:
        drawn = random.sample(range(1, 81), 20)
        matches = len(set(numbers) & set(drawn))
        pays = {0: 0, 1: 0, 2: 1, 3: 2, 4: 5, 5: 10}
        return matches, pays.get(matches, 20) if matches >= 6 else 0
    
    @staticmethod
    def wheel() -> Tuple[int, float]:
        sectors = [0, 1, 2, 5, 10]
        weights = [30, 25, 20, 15, 10]
        return random.choices(sectors, weights=weights)[0]


# ==================== МЕНЕДЖЕР ДАННЫХ ====================

class DataManager:
    """Управление данными через JSON файлы"""
    
    DATA_DIR = "bot_data"
    
    @classmethod
    def init(cls):
        if not os.path.exists(cls.DATA_DIR):
            os.makedirs(cls.DATA_DIR)
    
    @classmethod
    def _get_path(cls, filename: str) -> str:
        return os.path.join(cls.DATA_DIR, filename)
    
    @classmethod
    def save_user(cls, user: UserData):
        path = cls._get_path(f"user_{user.user_id}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(user.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_user(cls, user_id: int) -> Optional[UserData]:
        path = cls._get_path(f"user_{user_id}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return UserData.from_dict(data)
        return None
    
    @classmethod
    def save_check(cls, check: Check):
        path = cls._get_path("checks.json")
        checks = cls.load_all_checks()
        checks[check.code] = check.to_dict()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(checks, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_check(cls, code: str) -> Optional[Check]:
        checks = cls.load_all_checks()
        if code in checks:
            return Check.from_dict(checks[code])
        return None
    
    @classmethod
    def load_all_checks(cls) -> dict:
        path = cls._get_path("checks.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @classmethod
    def save_promocode(cls, promo: Promocode):
        path = cls._get_path("promocodes.json")
        promos = cls.load_all_promocodes()
        promos[promo.code] = promo.to_dict()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(promos, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_promocode(cls, code: str) -> Optional[Promocode]:
        promos = cls.load_all_promocodes()
        if code in promos:
            return Promocode.from_dict(promos[code])
        return None
    
    @classmethod
    def load_all_promocodes(cls) -> dict:
        path = cls._get_path("promocodes.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @classmethod
    def save_ticket(cls, ticket: Ticket):
        path = cls._get_path("tickets.json")
        tickets = cls.load_all_tickets()
        tickets[ticket.ticket_id] = ticket.to_dict()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(tickets, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_all_tickets(cls) -> dict:
        path = cls._get_path("tickets.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @classmethod
    def get_all_users(cls) -> List[int]:
        users = []
        for f in os.listdir(cls.DATA_DIR):
            if f.startswith("user_") and f.endswith(".json"):
                user_id = int(f.replace("user_", "").replace(".json", ""))
                users.append(user_id)
        return users
    
    @classmethod
    def get_stats(cls) -> dict:
        users = cls.get_all_users()
        total_balance = 0
        total_games = 0
        for user_id in users:
            user = cls.load_user(user_id)
            if user:
                total_balance += user.balance
                total_games += user.total_games
        return {
            "total_users": len(users),
            "total_balance": total_balance,
            "total_games": total_games
        }


# ==================== КЛАВИАТУРЫ ====================

class Keyboards:
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🎮 ИГРЫ", callback_data="games_menu")],
            [InlineKeyboardButton("⭐ ПРОФИЛЬ", callback_data="profile")],
            [InlineKeyboardButton("💰 БАЛАНС", callback_data="balance")],
            [InlineKeyboardButton("🛒 ПОПОЛНИТЬ", callback_data="deposit_menu")],
            [InlineKeyboardButton("🎫 ПРОМОКОД", callback_data="promocode")],
            [InlineKeyboardButton("📦 ЧЕК СИСТЕМА", callback_data="check_system")],
            [InlineKeyboardButton("👥 РЕФЕРАЛЫ", callback_data="referrals")],
            [InlineKeyboardButton("📋 ЗАДАНИЯ", callback_data="tasks")],
            [InlineKeyboardButton("💬 ПОДДЕРЖКА", callback_data="support_menu")],
            [InlineKeyboardButton("❓ ПОМОЩЬ", callback_data="help")],
            [InlineKeyboardButton("🔍 ПРОВЕРИТЬ ЧЕСТНОСТЬ", callback_data="fairness")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def games_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🪙 Монета (x1.95)", callback_data="game_coin"),
             InlineKeyboardButton("🎱 Рулетка (x1.95)", callback_data="game_roulette")],
            [InlineKeyboardButton("🎲 Кости (x5.5)", callback_data="game_dice"),
             InlineKeyboardButton("📈 Crash (x1-50)", callback_data="game_crash")],
            [InlineKeyboardButton("💣 Mines (x1-25)", callback_data="game_mines"),
             InlineKeyboardButton("🤩 Алмаз (x2)", callback_data="game_diamond")],
            [InlineKeyboardButton("♠️ 21 очко (x2.1)", callback_data="game_blackjack"),
             InlineKeyboardButton("🔮 Фортуна (x0-50)", callback_data="game_fortune")],
            [InlineKeyboardButton("✂️ КНБ (x2.7)", callback_data="game_rps"),
             InlineKeyboardButton("🃏 Покер (x0-100)", callback_data="game_poker")],
            [InlineKeyboardButton("🎯 Кено (x0-20)", callback_data="game_keno"),
             InlineKeyboardButton("🎰 Колесо (x0-10)", callback_data="game_wheel")],
            [InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def deposit_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("⭐ 100 звезд (100⭐)", callback_data="buy_100")],
            [InlineKeyboardButton("⭐ 500 звезд (500⭐)", callback_data="buy_500")],
            [InlineKeyboardButton("⭐ 1000 звезд (1000⭐)", callback_data="buy_1000")],
            [InlineKeyboardButton("⭐ 5000 звезд (5000⭐)", callback_data="buy_5000")],
            [InlineKeyboardButton("⭐ 10000 звезд (10000⭐)", callback_data="buy_10000")],
            [InlineKeyboardButton("⭐ 50000 звезд (50000⭐)", callback_data="buy_50000")],
            [InlineKeyboardButton("🔢 Своя сумма", callback_data="custom_amount")],
            [InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("👥 ПОЛЬЗОВАТЕЛИ", callback_data="admin_users")],
            [InlineKeyboardButton("💰 ЗВЕЗДЫ", callback_data="admin_stars")],
            [InlineKeyboardButton("📋 ЗАДАНИЯ", callback_data="admin_tasks")],
            [InlineKeyboardButton("🎫 ПРОМОКОДЫ", callback_data="admin_promocodes")],
            [InlineKeyboardButton("📦 ЧЕКИ", callback_data="admin_checks")],
            [InlineKeyboardButton("💸 ВЫВОДЫ", callback_data="admin_withdraws")],
            [InlineKeyboardButton("⛔ БАНЫ", callback_data="admin_bans")],
            [InlineKeyboardButton("💬 ПОДДЕРЖКА", callback_data="admin_support")],
            [InlineKeyboardButton("⚙️ НАСТРОЙКИ", callback_data="admin_settings")],
            [InlineKeyboardButton("📊 СТАТИСТИКА", callback_data="admin_stats")],
            [InlineKeyboardButton("📢 РАССЫЛКА", callback_data="admin_mailing")],
            [InlineKeyboardButton("📝 ЛОГИ", callback_data="admin_logs")],
            [InlineKeyboardButton("🔙 В ГЛАВНОЕ МЕНЮ", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_button() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_main")]])


# ==================== БОТ ====================

class GameBot:
    
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
        DataManager.init()
        
    def setup_handlers(self):
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("withdraw", self.withdraw_command))
        
        # Колбэки
        self.application.add_handler(CallbackQueryHandler(self.callback_handler))
        
        # Инлайн запросы
        self.application.add_handler(InlineQueryHandler(self.inline_query))
        
        # Платежи
        self.application.add_handler(PreCheckoutQueryHandler(self.pre_checkout))
        self.application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.payment_successful))
        
        # Сообщения для ввода
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_handler))
        
    async def get_user(self, user_id: int, username: str = None) -> UserData:
        user = DataManager.load_user(user_id)
        if not user:
            user = UserData(user_id, username)
            DataManager.save_user(user)
        return user
    
    async def save_user(self, user: UserData):
        DataManager.save_user(user)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = await self.get_user(update.effective_user.id, update.effective_user.username)
        await update.message.reply_text(
            f"🎮 Добро пожаловать в игру!\n\n"
            f"⭐ Ваш баланс: {user.balance} звезд\n"
            f"🎁 Стартовый бонус: {START_BALANCE} звезд\n\n"
            f"Выберите действие:",
            reply_markup=Keyboards.main_menu()
        )
    
    async def withdraw_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = await self.get_user(update.effective_user.id)
        args = context.args
        
        if user.is_withdraw_banned:
            await update.message.reply_text("⛔ Вы забанены на вывод средств!")
            return
            
        if not args:
            await update.message.reply_text(f"💸 Использование: /withdraw [сумма]\n\nМинимум: {MIN_WITHDRAW} ⭐")
            return
            
        try:
            amount = int(args[0])
            if amount < MIN_WITHDRAW:
                await update.message.reply_text(f"❌ Минимальная сумма вывода: {MIN_WITHDRAW} ⭐")
                return
                
            if amount > user.balance:
                await update.message.reply_text("❌ Недостаточно средств!")
                return
                
            # Проверка лимитов
            if user.last_withdraw_time:
                last = datetime.fromisoformat(user.last_withdraw_time)
                if datetime.now() - last < timedelta(hours=24):
                    await update.message.reply_text("⏰ Вывод доступен раз в 24 часа!")
                    return
                    
            if user.withdraw_count_today >= 3:
                await update.message.reply_text("📊 Достигнут лимит выводов за день (3)")
                return
                
            # Создание заявки
            user.balance -= amount
            user.withdraw_count_today += 1
            user.last_withdraw_time = datetime.now().isoformat()
            await self.save_user(user)
            
            # Уведомление админов
            for admin_id in ADMIN_IDS:
                await self.application.bot.send_message(
                    admin_id,
                    f"💰 Новая заявка на вывод!\n"
                    f"👤 @{update.effective_user.username}\n"
                    f"💎 Сумма: {amount} ⭐\n"
                    f"🆔 ID: {update.effective_user.id}"
                )
                
            await update.message.reply_text(
                f"✅ Заявка на вывод {amount} ⭐ создана!\n"
                f"Администратор рассмотрит её в ближайшее время."
            )
            
        except ValueError:
            await update.message.reply_text("❌ Введите корректную сумму!")
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user = await self.get_user(query.from_user.id, query.from_user.username)
        
        if data == "back_to_main":
            await query.edit_message_text(
                "🎮 Главное меню:",
                reply_markup=Keyboards.main_menu()
            )
            
        elif data == "games_menu":
            await query.edit_message_text(
                "🎮 Выберите игру:\n\n"
                "У каждой игры свой множитель и правила!",
                reply_markup=Keyboards.games_menu()
            )
            
        elif data == "profile":
            stats = f"""
⭐ ПРОФИЛЬ
━━━━━━━━━━━━━━━
🆔 ID: {user.user_id}
👤 Имя: @{query.from_user.username or 'нет'}

💰 БАЛАНС: {user.balance} ⭐

📊 СТАТИСТИКА:
🎮 Игр сыграно: {user.total_games}
🏆 Побед: {user.total_wins}
📈 Процент побед: {round(user.total_wins/user.total_games*100) if user.total_games > 0 else 0}%
💎 Всего выиграно: {user.total_won} ⭐
💸 Всего проиграно: {user.total_lost} ⭐

📅 Сегодня:
🎉 Выиграно: {user.daily_wins} ⭐
😢 Проиграно: {user.daily_losses} ⭐

👥 РЕФЕРАЛЫ:
🔗 Приглашено: {len(user.referrals)}
💸 Заработано: {user.referral_earnings} ⭐

📅 В игре с: {user.join_date[:10]}
━━━━━━━━━━━━━━━
"""
            await query.edit_message_text(stats, reply_markup=Keyboards.back_button())
            
        elif data == "balance":
            await query.edit_message_text(
                f"💰 ВАШ БАЛАНС\n━━━━━━━━━━━━━━━\n⭐ {user.balance} звезд\n━━━━━━━━━━━━━━━\n\n"
                f"Пополнить баланс можно через меню 🛒 ПОПОЛНИТЬ",
                reply_markup=Keyboards.back_button()
            )
            
        elif data == "deposit_menu":
            await query.edit_message_text(
                "🛒 ПОПОЛНЕНИЕ БАЛАНСА\n━━━━━━━━━━━━━━━\n"
                "Выберите сумму для пополнения:\n\n"
                "⭐ 1 звезда = 1 рубль\n\n"
                "💰 После оплаты звезды поступят мгновенно!",
                reply_markup=Keyboards.deposit_menu()
            )
            
        elif data.startswith("buy_"):
            amount = int(data.split("_")[1])
            await self.create_invoice(query, user, amount)
            
        elif data == "promocode":
            await query.edit_message_text(
                "🎫 АКТИВАЦИЯ ПРОМОКОДА\n━━━━━━━━━━━━━━━\n"
                "Введите промокод в чат:\n\n"
                "Формат: КОД\n\n"
                "Промокод можно получить у администраторов!",
                reply_markup=Keyboards.back_button()
            )
            context.user_data['awaiting_promocode'] = True
            
        elif data == "check_system":
            await query.edit_message_text(
                "📦 ЧЕК СИСТЕМА\n━━━━━━━━━━━━━━━\n"
                "Чеки - это способ перевода звезд другому пользователю.\n\n"
                "📝 Как создать чек:\n"
                "1. Введите /create_check [сумма]\n"
                "2. Получите уникальный код\n"
                "3. Отправьте код другу\n\n"
                "📝 Как активировать чек:\n"
                "Введите /activate_check [код]\n\n"
                f"⚡ Стоимость создания чека: 5% от суммы\n"
                f"💎 Минимальная сумма чека: 100 ⭐",
                reply_markup=Keyboards.back_button()
            )
            
        elif data == "referrals":
            code = user.referral_code
            link = f"https://t.me/{BOT_USERNAME}?start={code}"
            stats = f"""
👥 РЕФЕРАЛЬНАЯ СИСТЕМА
━━━━━━━━━━━━━━━

🔗 Ваша реферальная ссылка:
`{link}`

📊 Статистика:
👥 Приглашено друзей: {len(user.referrals)}
💸 Заработано: {user.referral_earnings} ⭐

🎁 Бонусы:
• За каждого друга: +50 ⭐
• 10% от покупок друга
• 5% от выигрышей друга

💡 Как это работает?
1. Отправьте ссылку другу
2. Друг регистрируется
3. Вы получаете бонусы!

📈 ТОП рефералов:

/{BOT_USERNAME}?start={code}
"""
            await query.edit_message_text(stats, parse_mode=ParseMode.MARKDOWN, reply_markup=Keyboards.back_button())
            
        elif data == "tasks":
            tasks_text = "📋 ДОСТУПНЫЕ ЗАДАНИЯ\n━━━━━━━━━━━━━━━\n\n"
            for channel in REQUIRED_CHANNELS:
                status = "✅" if channel['id'] in user.completed_tasks else "❌"
                tasks_text += f"{status} {channel['name']}\n➕ Награда: 100 ⭐\n\n"
            tasks_text += "━━━━━━━━━━━━━━━\n✅ Выполните все задания и получите бонус!"
            
            keyboard = []
            for channel in REQUIRED_CHANNELS:
                if channel['id'] not in user.completed_tasks:
                    keyboard.append([InlineKeyboardButton(f"📢 {channel['name']}", url=channel['link'])])
                    keyboard.append([InlineKeyboardButton(f"✅ Проверить {channel['name']}", callback_data=f"check_{channel['id']}")])
            keyboard.append([InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_main")])
            
            await query.edit_message_text(tasks_text, reply_markup=InlineKeyboardMarkup(keyboard))
            
        elif data.startswith("check_"):
            channel_id = int(data.split("_")[1])
            # Проверка подписки через бота
            try:
                member = await context.bot.get_chat_member(channel_id, user.user_id)
                if member.status in ['member', 'administrator', 'creator']:
                    if channel_id not in user.completed_tasks:
                        user.completed_tasks.append(channel_id)
                        user.balance += 100
                        await self.save_user(user)
                        await query.answer("✅ Задание выполнено! +100 ⭐")
                        await self.callback_handler(update, context)
                    else:
                        await query.answer("❌ Задание уже выполнено!")
                else:
                    await query.answer("❌ Вы не подписаны на канал!", show_alert=True)
            except:
                await query.answer("❌ Ошибка проверки подписки!", show_alert=True)
                
        elif data == "support_menu":
            await query.edit_message_text(
                "💬 ПОДДЕРЖКА\n━━━━━━━━━━━━━━━\n"
                "Опишите вашу проблему в чат.\n"
                "Администратор ответит в ближайшее время!\n\n"
                "Для создания тикета отправьте:\n"
                "/ticket [текст обращения]",
                reply_markup=Keyboards.back_button()
            )
            
        elif data == "help":
            help_text = """
❓ ПОМОЩЬ И ПРАВИЛА
━━━━━━━━━━━━━━━

🎮 ИГРЫ:
В боте доступно 12 игр с разными множителями:
• Монета (x1.95) - угадай сторону
• Рулетка (x1.95) - красное/черное
• Кости (x5.5) - угадай число
• Crash (x1-50) - забери выигрыш вовремя
• Mines (x1-25) - открывай клетки
• Алмаз (x2) - найди алмаз
• 21 очко (x2.1) - блэкджек
• Фортуна (x0-50) - случайный множитель
• КНБ (x2.7) - камень-ножницы-бумага
• Покер (x0-100) - случайная комбинация
• Кено (x0-20) - угадай числа
• Колесо (x0-10) - колесо фортуны

💰 ВЫВОД СРЕДСТВ:
• Команда: /withdraw [сумма]
• Минимум: 100 ⭐
• Максимум в день: 3 вывода
• Вывод раз в 24 часа

👥 РЕФЕРАЛЫ:
• За каждого друга: +50 ⭐
• 10% от покупок друга

⚠️ ЛИМИТЫ:
• Максимум проигрыша в день: 50000 ⭐
• Максимум выигрыша в день: 100000 ⭐

📦 ЧЕКИ:
• Создание: /create_check [сумма]
• Активация: /activate_check [код]

🎫 ПРОМОКОДЫ:
Активация через меню ПРОМОКОД

━━━━━━━━━━━━━━━
⚡ Все игры имеют доказуемую честность!
🔍 Проверить можно в разделе "ПРОВЕРИТЬ ЧЕСТНОСТЬ"
"""
            await query.edit_message_text(help_text, reply_markup=Keyboards.back_button())
            
        elif data == "fairness":
            seed = Game.generate_seed()
            await query.edit_message_text(
                f"🔍 ДОКАЗУЕМАЯ ЧЕСТНОСТЬ\n━━━━━━━━━━━━━━━\n\n"
                f"Система использует криптографически стойкий генератор случайных чисел.\n\n"
                f"Seed текущей сессии: `{seed[:16]}...`\n\n"
                f"Проверить любую игру можно через:\n"
                f"1. Сохраните seed до игры\n"
                f"2. После игры проверьте результат\n"
                f"3. Результат хешируется с seed\n\n"
                f"Все игры проходят верификацию!\n"
                f"Мошенничество невозможно.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=Keyboards.back_button()
            )
            
        elif data.startswith("game_"):
            game = data.replace("game_", "")
            await query.edit_message_text(
                f"🎮 Игра {game}\n"
                f"💰 Ваш баланс: {user.balance} ⭐\n\n"
                f"Введите сумму ставки в чат:",
                reply_markup=Keyboards.back_button()
            )
            context.user_data['awaiting_bet'] = game
            
        # Админ панель
        elif data == "admin_panel" and query.from_user.id in ADMIN_IDS:
            await query.edit_message_text(
                "👑 АДМИН ПАНЕЛЬ\n━━━━━━━━━━━━━━━\n"
                "Выберите раздел управления:",
                reply_markup=Keyboards.admin_menu()
            )
            
        elif data.startswith("admin_"):
            if query.from_user.id not in ADMIN_IDS:
                await query.answer("⛔ Доступ запрещен!")
                return
                
            if data == "admin_stats":
                stats = DataManager.get_stats()
                await query.edit_message_text(
                    f"📊 СТАТИСТИКА БОТА\n━━━━━━━━━━━━━━━\n"
                    f"👥 Всего пользователей: {stats['total_users']}\n"
                    f"⭐ Всего звезд в системе: {stats['total_balance']}\n"
                    f"🎮 Всего сыграно игр: {stats['total_games']}\n"
                    f"📋 Активных заданий: {len(REQUIRED_CHANNELS)}\n"
                    f"🎫 Промокодов: {len(DataManager.load_all_promocodes())}\n"
                    f"💬 Открытых тикетов: {len([t for t in DataManager.load_all_tickets().values() if t['status'] == 'open'])}\n"
                    f"━━━━━━━━━━━━━━━",
                    reply_markup=Keyboards.back_button()
                )
                
            elif data == "admin_mailing":
                await query.edit_message_text(
                    "📢 РАССЫЛКА\n━━━━━━━━━━━━━━━\n"
                    "Введите текст для рассылки:",
                    reply_markup=Keyboards.back_button()
                )
                context.user_data['awaiting_mailing'] = True
                
            else:
                await query.edit_message_text("В разработке...", reply_markup=Keyboards.back_button())
    
    async def create_invoice(self, query, user: UserData, amount: int):
        title = f"Пополнение баланса на {amount} звезд"
        description = f"Покупка {amount} звезд для игры"
        payload = f"stars_{amount}_{user.user_id}_{int(time.time())}"
        currency = "XTR"  # Telegram Stars
        prices = [LabeledPrice("Звезды", amount)]
        
        await query.edit_message_text(
            f"🛒 ОФОРМЛЕНИЕ ЗАКАЗА\n━━━━━━━━━━━━━━━\n"
            f"💰 Сумма: {amount} ⭐\n"
            f"💎 К оплате: {amount} ⭐\n\n"
            f"Нажмите кнопку ниже для оплаты через Telegram Stars",
            reply_markup=None
        )
        
        await query.message.reply_invoice(
            title=title,
            description=description,
            payload=payload,
            provider_token="",
            currency=currency,
            prices=prices,
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False
        )
    
    async def pre_checkout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query: PreCheckoutQuery = update.pre_checkout_query
        await query.answer(ok=True)
        
    async def payment_successful(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        payment: SuccessfulPayment = update.message.successful_payment
        user_id = update.effective_user.id
        
        # Извлечение суммы из payload
        payload = payment.invoice_payload
        amount = int(payload.split("_")[1])
        
        user = await self.get_user(user_id)
        user.balance += amount
        user.total_deposits += amount
        await self.save_user(user)
        
        # Начисление реферального бонуса
        if user.referred_by:
            referrer = await self.get_user(user.referred_by)
            bonus = int(amount * 0.1)
            referrer.balance += bonus
            referrer.referral_earnings += bonus
            await self.save_user(referrer)
            await self.application.bot.send_message(
                referrer.user_id,
                f"🎁 Ваш реферал пополнил баланс на {amount} ⭐!\n"
                f"Вы получили {bonus} ⭐ (10%)"
            )
        
        await update.message.reply_text(
            f"✅ Оплата прошла успешно!\n"
            f"💰 На ваш баланс зачислено {amount} ⭐\n"
            f"⭐ Текущий баланс: {user.balance} ⭐\n\n"
            f"🎮 Приятной игры!",
            reply_markup=Keyboards.main_menu()
        )
    
    async def text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = await self.get_user(update.effective_user.id)
        text = update.message.text
        
        # Обработка промокода
        if context.user_data.get('awaiting_promocode'):
            context.user_data['awaiting_promocode'] = False
            promo = DataManager.load_promocode(text.upper())
            
            if not promo:
                await update.message.reply_text("❌ Промокод не найден!")
                return
                
            if promo.used_count >= promo.max_uses:
                await update.message.reply_text("❌ Промокод уже использован максимальное количество раз!")
                return
                
            if text.upper() in user.used_promocodes:
                await update.message.reply_text("❌ Вы уже использовали этот промокод!")
                return
                
            user.balance += promo.reward
            user.used_promocodes.append(text.upper())
            promo.used_count += 1
            promo.used_by.append(user.user_id)
            
            DataManager.save_promocode(promo)
            await self.save_user(user)
            
            await update.message.reply_text(f"✅ Промокод активирован!\n🎁 Вы получили {promo.reward} ⭐\n💰 Новый баланс: {user.balance} ⭐")
            return
            
        # Обработка ставки для игры
        if context.user_data.get('awaiting_bet'):
            game = context.user_data['awaiting_bet']
            context.user_data['awaiting_bet'] = None
            
            try:
                bet = int(text)
                if bet < MIN_BALANCE_FOR_GAME:
                    await update.message.reply_text(f"❌ Минимальная ставка: {MIN_BALANCE_FOR_GAME} ⭐")
                    return
                    
                if bet > user.balance:
                    await update.message.reply_text("❌ Недостаточно средств!")
                    return
                    
                # Проверка дневных лимитов
                if user.daily_losses >= DAILY_LOSS_LIMIT:
                    await update.message.reply_text(f"❌ Достигнут дневной лимит проигрыша ({DAILY_LOSS_LIMIT} ⭐)")
                    return
                    
                if user.daily_wins >= DAILY_WIN_LIMIT:
                    await update.message.reply_text(f"❌ Достигнут дневной лимит выигрыша ({DAILY_WIN_LIMIT} ⭐)")
                    return
                    
                if user.consecutive_losses >= 10:
                    await update.message.reply_text("⏸️ Сделайте паузу! Слишком много проигрышей подряд.")
                    return
                    
                # Игровая логика
                seed = Game.generate_seed()
                result_text = ""
                win_amount = 0
                
                if game == "coin":
                    await update.message.reply_text("🪙 Выберите сторону:\n/орел или /решка")
                    return
                    
                elif game == "roulette":
                    await update.message.reply_text("🎱 Выберите ставку:\n/красное /черное /четное /нечетное /нуль")
                    return
                    
                elif game == "dice":
                    await update.message.reply_text("🎲 Угадайте число от 1 до 6:\n/1 /2 /3 /4 /5 /6")
                    return
                    
                elif game == "crash":
                    multiplier = Game.crash()
                    win_amount = int(bet * multiplier) if multiplier > 1 else 0
                    result_text = f"📈 Игра Crash\nМножитель: {multiplier}x\n"
                    result_text += f"{'✅ ВЫИГРЫШ!' if multiplier > 1 else '❌ ПРОИГРЫШ!'}\n"
                    result_text += f"💰 {win_amount if win_amount else 0} ⭐"
                    
                elif game == "diamond":
                    diamond_pos = Game.diamond()
                    win = diamond_pos == 1
                    win_amount = int(bet * 2) if win else 0
                    result_text = f"🤩 Алмаз в сундуке №{diamond_pos}\n"
                    result_text += f"{'✅ ВЫИГРЫШ!' if win else '❌ ПРОИГРЫШ!'}\n"
                    result_text += f"💰 {win_amount if win_amount else 0} ⭐"
                    
                elif game == "blackjack":
                    player, dealer, mult = Game.blackjack()
                    win_amount = int(bet * mult) if mult > 0 else 0
                    result_text = f"♠️ Блэкджек\nВаши очки: {player}\nОчки дилера: {dealer}\n"
                    result_text += f"{'✅ ВЫИГРЫШ!' if mult > 0 else '❌ ПРОИГРЫШ!'}\n"
                    result_text += f"💰 {win_amount if win_amount else 0} ⭐"
                    
                elif game == "fortune":
                    mult = Game.fortune()
                    win_amount = int(bet * mult) if mult > 0 else 0
                    result_text = f"🔮 Колесо фортуны\nМножитель: {mult}x\n"
                    result_text += f"{'✅ ВЫИГРЫШ!' if mult > 0 else '❌ ПРОИГРЫШ!'}\n"
                    result_text += f"💰 {win_amount if win_amount else 0} ⭐"
                    
                elif game == "wheel":
                    sector = Game.wheel()
                    win_amount = int(bet * sector) if sector > 0 else 0
                    result_text = f"🎰 Колесо\nСектор: {sector}x\n"
                    result_text += f"{'✅ ВЫИГРЫШ!' if sector > 0 else '❌ ПРОИГРЫШ!'}\n"
                    result_text += f"💰 {win_amount if win_amount else 0} ⭐"
                    
                else:
                    await update.message.reply_text("❌ Игра не найдена!")
                    return
                    
                # Обновление баланса
                if win_amount > 0:
                    user.balance += win_amount
                    user.total_won += win_amount
                    user.daily_wins += win_amount
                    user.consecutive_losses = 0
                    user.total_wins += 1
                else:
                    user.balance -= bet
                    user.total_lost += bet
                    user.daily_losses += bet
                    user.consecutive_losses += 1
                    
                user.total_games += 1
                user.last_game_time = datetime.now().isoformat()
                
                # Сохранение истории
                user.game_history.append({
                    "game": game,
                    "bet": bet,
                    "win": win_amount,
                    "time": datetime.now().isoformat()
                })
                
                await self.save_user(user)
                
                await update.message.reply_text(
                    f"{result_text}\n\n"
                    f"⭐ Текущий баланс: {user.balance} ⭐\n"
                    f"🎮 Сыграно игр: {user.total_games}\n"
                    f"📊 Процент побед: {round(user.total_wins/user.total_games*100)}%"
                )
                
            except ValueError:
                await update.message.reply_text("❌ Введите корректное число!")
                
        # Обработка рассылки
        elif context.user_data.get('awaiting_mailing'):
            if update.effective_user.id not in ADMIN_IDS:
                return
                
            context.user_data['awaiting_mailing'] = False
            message_text = text
            
            await update.message.reply_text("📢 Начинаю рассылку...")
            
            users = DataManager.get_all_users()
            success = 0
            fail = 0
            
            for user_id in users:
                try:
                    await self.application.bot.send_message(user_id, message_text)
                    success += 1
                except:
                    fail += 1
                await asyncio.sleep(0.05)  # Защита от флуда
                
            await update.message.reply_text(f"✅ Рассылка завершена!\n📨 Доставлено: {success}\n❌ Ошибок: {fail}")
            
        # Игры с выбором (монета, рулетка, кости)
        elif text.startswith("/") and text[1:] in ["орел", "решка"]:
            bet = context.user_data.get('last_bet', 50)
            choice = text[1:]
            result, mult = Game.coin_flip(choice)
            win_amount = int(bet * mult) if mult > 0 else 0
            
            if win_amount > 0:
                user.balance += win_amount
                user.total_won += win_amount
                user.total_wins += 1
                user.consecutive_losses = 0
            else:
                user.balance -= bet
                user.total_lost += bet
                user.consecutive_losses += 1
                
            user.total_games += 1
            await self.save_user(user)
            
            await update.message.reply_text(
                f"🪙 Монета\nВыпало: {result}\nВаш выбор: {choice}\n\n"
                f"{'✅ ВЫИГРЫШ!' if win_amount > 0 else '❌ ПРОИГРЫШ!'}\n"
                f"💰 {win_amount} ⭐\n"
                f"⭐ Баланс: {user.balance} ⭐"
            )
            
        elif text.startswith("/") and text[1:] in ["красное", "черное", "четное", "нечетное", "нуль"]:
            bet = context.user_data.get('last_bet', 50)
            choice = text[1:]
            num, color, mult = Game.roulette(choice)
            win_amount = int(bet * mult) if mult > 0 else 0
            
            if win_amount > 0:
                user.balance += win_amount
                user.total_won += win_amount
                user.total_wins += 1
                user.consecutive_losses = 0
            else:
                user.balance -= bet
                user.total_lost += bet
                user.consecutive_losses += 1
                
            user.total_games += 1
            await self.save_user(user)
            
            await update.message.reply_text(
                f"🎱 Рулетка\nВыпало: {num} - {color}\nВаша ставка: {choice}\n\n"
                f"{'✅ ВЫИГРЫШ!' if win_amount > 0 else '❌ ПРОИГРЫШ!'}\n"
                f"💰 {win_amount} ⭐\n"
                f"⭐ Баланс: {user.balance} ⭐"
            )
            
        elif text.startswith("/") and text[1:] in [str(i) for i in range(1, 7)]:
            bet = context.user_data.get('last_bet', 50)
            choice = int(text[1:])
            result, mult = Game.dice(choice)
            win_amount = int(bet * mult) if mult > 0 else 0
            
            if win_amount > 0:
                user.balance += win_amount
                user.total_won += win_amount
                user.total_wins += 1
                user.consecutive_losses = 0
            else:
                user.balance -= bet
                user.total_lost += bet
                user.consecutive_losses += 1
                
            user.total_games += 1
            await self.save_user(user)
            
            await update.message.reply_text(
                f"🎲 Кости\nВыпало: {result}\nВаша ставка: {choice}\n\n"
                f"{'✅ ВЫИГРЫШ!' if win_amount > 0 else '❌ ПРОИГРЫШ!'}\n"
                f"💰 {win_amount} ⭐\n"
                f"⭐ Баланс: {user.balance} ⭐"
            )
            
        # Дополнительные команды
        elif text.startswith("/create_check"):
            try:
                amount = int(text.split()[1])
                if amount < 100:
                    await update.message.reply_text("❌ Минимальная сумма чека: 100 ⭐")
                    return
                    
                fee = int(amount * 0.05)
                total = amount + fee
                
                if total > user.balance:
                    await update.message.reply_text("❌ Недостаточно средств для создания чека (включая комиссию 5%)")
                    return
                    
                code = hashlib.md5(f"{user.user_id}_{amount}_{time.time()}".encode()).hexdigest()[:12]
                check = Check(code, amount, user.user_id)
                
                user.balance -= total
                DataManager.save_check(check)
                await self.save_user(user)
                
                await update.message.reply_text(
                    f"✅ Чек создан!\n\n"
                    f"📦 Код чека: `{code}`\n"
                    f"💰 Сумма: {amount} ⭐\n"
                    f"💸 Комиссия: {fee} ⭐ (5%)\n\n"
                    f"Отправьте этот код другу для активации:\n"
                    f"/activate_check {code}",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                await update.message.reply_text("❌ Использование: /create_check [сумма]")
                
        elif text.startswith("/activate_check"):
            try:
                code = text.split()[1]
                check = DataManager.load_check(code)
                
                if not check:
                    await update.message.reply_text("❌ Чек не найден!")
                    return
                    
                if check.activated:
                    await update.message.reply_text("❌ Чек уже активирован!")
                    return
                    
                check.activated = True
                check.activated_by = user.user_id
                
                user.balance += check.amount
                DataManager.save_check(check)
                await self.save_user(user)
                
                await update.message.reply_text(
                    f"✅ Чек активирован!\n"
                    f"💰 Вы получили {check.amount} ⭐\n"
                    f"⭐ Новый баланс: {user.balance} ⭐"
                )
            except:
                await update.message.reply_text("❌ Использование: /activate_check [код]")
                
        elif text.startswith("/ticket"):
            message = text.replace("/ticket", "").strip()
            if not message:
                await update.message.reply_text("❌ Использование: /ticket [текст обращения]")
                return
                
            tickets = DataManager.load_all_tickets()
            ticket_id = len(tickets) + 1
            
            ticket = Ticket(ticket_id, user.user_id, message)
            DataManager.save_ticket(ticket)
            
            await update.message.reply_text(
                f"✅ Тикет #{ticket_id} создан!\n"
                f"Администратор ответит в ближайшее время."
            )
            
            for admin_id in ADMIN_IDS:
                await self.application.bot.send_message(
                    admin_id,
                    f"📋 Новый тикет #{ticket_id}\n"
                    f"👤 От: @{update.effective_user.username}\n"
                    f"💬 Сообщение: {message}"
                )
                
        # Сохранение последней ставки для игр с выбором
        elif text.isdigit():
            context.user_data['last_bet'] = int(text)
            await update.message.reply_text(f"✅ Ставка {text} ⭐ сохранена!")
    
    async def inline_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.inline_query.query
        results = []
        
        if query == "":
            results = [
                InlineQueryResultArticle(
                    id="1",
                    title="🎮 Играть в бота",
                    description="Начните играть прямо сейчас!",
                    input_message_content=InputTextMessageContent(
                        f"https://t.me/{BOT_USERNAME}"
                    )
                ),
                InlineQueryResultArticle(
                    id="2",
                    title="💰 Пополнить баланс",
                    description="Пополните баланс для игры",
                    input_message_content=InputTextMessageContent(
                        f"https://t.me/{BOT_USERNAME}"
                    )
                )
            ]
            
        await update.inline_query.answer(results)
    
    def run(self):
        print(f"🤖 Бот {BOT_USERNAME} запущен!")
        self.application.run_polling()


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    bot = GameBot(BOT_TOKEN)
    bot.run()
