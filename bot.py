import asyncio
import json
import os
import random
import logging
import secrets
import string
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import aiofiles

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery, ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Конфигурация
BOT_TOKEN = "8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE"
ADMIN_IDS = [5356400377]
BOT_ID = 8670879387

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Файлы для хранения данных
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
WITHDRAWALS_FILE = os.path.join(DATA_DIR, "withdrawals.json")
CHECKS_FILE = os.path.join(DATA_DIR, "checks.json")
PROMO_FILE = os.path.join(DATA_DIR, "promo.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
ADMIN_LOGS_FILE = os.path.join(DATA_DIR, "admin_logs.json")
SUPPORT_FILE = os.path.join(DATA_DIR, "support.json")
GAME_HASHES_FILE = os.path.join(DATA_DIR, "game_hashes.json")
MAILING_FILE = os.path.join(DATA_DIR, "mailing.json")

os.makedirs(DATA_DIR, exist_ok=True)

# FSM States
class CrashStates(StatesGroup):
    playing = State()

class MinesStates(StatesGroup):
    playing = State()

class BlackjackStates(StatesGroup):
    playing = State()

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_user_tg = State()
    waiting_for_stars_amount = State()
    waiting_for_task_name = State()
    waiting_for_task_link = State()
    waiting_for_task_reward = State()
    waiting_for_promo_code = State()
    waiting_for_promo_reward = State()
    waiting_for_promo_limit = State()
    waiting_for_check_amount = State()
    waiting_for_setting_value = State()
    waiting_for_ban_hours = State()
    waiting_for_reply_message = State()
    waiting_for_limit_value = State()
    waiting_for_mailing_message = State()
    waiting_for_mailing_confirm = State()

class PromoStates(StatesGroup):
    waiting_for_promo_code = State()

class SupportStates(StatesGroup):
    waiting_for_message = State()

class BuyStates(StatesGroup):
    waiting_for_amount = State()

class GameStates(StatesGroup):
    waiting_for_coin_bet = State()
    waiting_for_coin_choice = State()
    waiting_for_roulette_bet = State()
    waiting_for_roulette_choice = State()
    waiting_for_cubes_bet = State()
    waiting_for_cubes_choice = State()
    waiting_for_crash_bet = State()
    waiting_for_crash_multiplier = State()
    waiting_for_mines_bet = State()
    waiting_for_mines_count = State()
    waiting_for_diamond_bet = State()
    waiting_for_diamond_choice = State()
    waiting_for_blackjack_bet = State()
    waiting_for_fortune_bet = State()
    waiting_for_knb_bet = State()
    waiting_for_knb_choice = State()
    waiting_for_poker_bet = State()
    waiting_for_keno_bet = State()
    waiting_for_keno_numbers = State()
    waiting_for_wheel_bet = State()

# Функции работы с JSON
async def load_json(filename: str, default: dict) -> dict:
    if os.path.exists(filename):
        try:
            async with aiofiles.open(filename, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content) if content else default
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return default
    return default

async def save_json(filename: str, data: dict):
    try:
        async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.error(f"Error saving {filename}: {e}")

# Генерация хеша для честности игры
def generate_game_hash(game_type: str, bet: int, result: any, user_id: int) -> dict:
    timestamp = datetime.now().isoformat()
    random_seed = secrets.token_hex(16)
    data_string = f"{game_type}|{user_id}|{bet}|{result}|{timestamp}|{random_seed}"
    game_hash = hashlib.sha256(data_string.encode()).hexdigest()
    
    return {
        "game": game_type,
        "bet": bet,
        "result": result,
        "timestamp": timestamp,
        "seed": random_seed,
        "hash": game_hash,
        "user_id": user_id
    }

async def save_game_hash(game_data: dict):
    hashes = await load_json(GAME_HASHES_FILE, {"games": []})
    hashes["games"].append(game_data)
    await save_json(GAME_HASHES_FILE, hashes)

# Инициализация данных
async def init_data():
    settings = await load_json(SETTINGS_FILE, {})
    if not settings:
        settings = {
            "start_balance": 100,
            "min_withdraw": 500,
            "referral_reward": 10,
            "referral_percent": 10,
            "exchange_rate": 1,
            "check_system_price": 100,
            "max_daily_loss": 50000,
            "max_daily_win": 100000,
            "max_consecutive_losses": 10,
            "min_balance_for_bet": 10,
            "withdraw_cooldown_hours": 24,
            "max_withdraw_per_day": 3,
            "bot_id": BOT_ID
        }
        await save_json(SETTINGS_FILE, settings)
    
    users = await load_json(USERS_FILE, {})
    for user_id, user_data in users.items():
        required_fields = {
            "stars": settings.get("start_balance", 100),
            "total_earned": 0,
            "total_spent": 0,
            "total_purchases": 0,
            "referral_code": user_id,
            "referrer": None,
            "referral_count": 0,
            "referral_earnings": 0,
            "games_played": 0,
            "games_won": 0,
            "games_lost": 0,
            "achievements": [],
            "check_system_unlocked": False,
            "daily_loss": 0,
            "daily_win": 0,
            "consecutive_losses": 0,
            "last_reset": None,
            "last_withdraw_time": None,
            "withdraw_count_today": 0,
            "is_withdraw_banned": False,
            "withdraw_ban_reason": None,
            "withdraw_ban_until": None,
            "created_at": datetime.now().isoformat(),
            "username": None
        }
        updated = False
        for field, default_value in required_fields.items():
            if field not in user_data:
                user_data[field] = default_value
                updated = True
        if updated:
            await save_json(USERS_FILE, users)
    
    return settings

# Функции работы с пользователями
async def get_user(user_id: int) -> dict:
    users = await load_json(USERS_FILE, {})
    settings = await load_json(SETTINGS_FILE, {})
    user_id_str = str(user_id)
    
    if user_id_str not in users:
        users[user_id_str] = {
            "stars": settings.get("start_balance", 100),
            "total_earned": 0,
            "total_spent": 0,
            "total_purchases": 0,
            "referral_code": str(user_id),
            "referrer": None,
            "referral_count": 0,
            "referral_earnings": 0,
            "games_played": 0,
            "games_won": 0,
            "games_lost": 0,
            "achievements": [],
            "check_system_unlocked": False,
            "daily_loss": 0,
            "daily_win": 0,
            "consecutive_losses": 0,
            "last_reset": None,
            "last_withdraw_time": None,
            "withdraw_count_today": 0,
            "is_withdraw_banned": False,
            "withdraw_ban_reason": None,
            "withdraw_ban_until": None,
            "created_at": datetime.now().isoformat(),
            "username": None
        }
        await save_json(USERS_FILE, users)
    
    user = users[user_id_str]
    
    if user.get("last_reset"):
        last_reset = datetime.fromisoformat(user["last_reset"])
        if last_reset.date() != datetime.now().date():
            user["daily_loss"] = 0
            user["daily_win"] = 0
            user["withdraw_count_today"] = 0
            user["last_reset"] = datetime.now().isoformat()
            await update_user(user_id, daily_loss=0, daily_win=0, withdraw_count_today=0, last_reset=datetime.now().isoformat())
    else:
        await update_user(user_id, last_reset=datetime.now().isoformat())
    
    if user.get("withdraw_ban_until"):
        ban_until = datetime.fromisoformat(user["withdraw_ban_until"])
        if datetime.now() >= ban_until:
            await update_user(user_id, is_withdraw_banned=False, withdraw_ban_reason=None, withdraw_ban_until=None)
            user["is_withdraw_banned"] = False
    
    return user

async def get_user_by_username(username: str) -> Optional[dict]:
    users = await load_json(USERS_FILE, {})
    for user_id, user_data in users.items():
        if user_data.get("username") == username or username in str(user_id):
            return {"user_id": int(user_id), "data": user_data}
    return None

async def update_user(user_id: int, **kwargs):
    users = await load_json(USERS_FILE, {})
    user_id_str = str(user_id)
    
    if user_id_str not in users:
        await get_user(user_id)
    
    for key, value in kwargs.items():
        users[user_id_str][key] = value
    
    await save_json(USERS_FILE, users)

async def add_stars(user_id: int, amount: int, reason: str = ""):
    user = await get_user(user_id)
    new_stars = user["stars"] + amount
    await update_user(user_id, stars=new_stars, total_earned=user["total_earned"] + amount)
    logger.info(f"User {user_id} earned {amount} stars. Reason: {reason}")
    await check_achievements(user_id)

async def remove_stars(user_id: int, amount: int, reason: str = "") -> bool:
    user = await get_user(user_id)
    if user["stars"] >= amount:
        new_stars = user["stars"] - amount
        await update_user(user_id, stars=new_stars, total_spent=user["total_spent"] + amount)
        logger.info(f"User {user_id} spent {amount} stars. Reason: {reason}")
        return True
    return False

async def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def log_admin_action(admin_id: int, action: str, target: str = None, details: str = ""):
    logs = await load_json(ADMIN_LOGS_FILE, [])
    logs.append({
        "admin_id": admin_id,
        "action": action,
        "target": target,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })
    await save_json(ADMIN_LOGS_FILE, logs[-200:])

async def check_achievements(user_id: int):
    user = await get_user(user_id)
    
    achievements = {
        "millionaire": {"name": "💰 Миллионер", "description": "Накопить 1,000,000 звезд", 
                       "condition": user["total_earned"] >= 1000000, "reward": 100000},
        "high_roller": {"name": "🎲 Высокий игрок", "description": "Сыграть 1000 игр",
                       "condition": user["games_played"] >= 1000, "reward": 50000},
        "lucky": {"name": "🍀 Счастливчик", "description": "Выиграть 100 игр",
                 "condition": user["games_won"] >= 100, "reward": 25000},
        "referral_master": {"name": "👥 Мастер рефералов", "description": "Пригласить 100 друзей",
                           "condition": user["referral_count"] >= 100, "reward": 50000},
        "loser": {"name": "😭 Король проигрышей", "description": "Проиграть 500 игр",
                 "condition": user["games_lost"] >= 500, "reward": 10000}
    }
    
    for ach_id, ach in achievements.items():
        if ach_id not in user["achievements"] and ach["condition"]:
            await add_stars(user_id, ach["reward"], f"Достижение: {ach['name']}")
            user["achievements"].append(ach_id)
            await update_user(user_id, achievements=user["achievements"])
            
            try:
                await bot.send_message(
                    user_id,
                    f"🏆 *Новое достижение!*\n\n✨ {ach['name']}\n📝 {ach['description']}\n\n🎁 Награда: {ach['reward']} ⭐",
                    parse_mode="Markdown"
                )
            except:
                pass

async def check_user_limits(user_id: int, bet: int, game: str) -> Tuple[bool, str]:
    user = await get_user(user_id)
    settings = await load_json(SETTINGS_FILE, {})
    
    if user["stars"] < settings.get("min_balance_for_bet", 10):
        return False, f"Минимальный баланс для игры: {settings.get('min_balance_for_bet', 10)} ⭐"
    
    if user["daily_loss"] + bet > settings.get("max_daily_loss", 50000):
        return False, f"Дневной лимит потерь: {settings.get('max_daily_loss', 50000)} ⭐"
    
    if user["daily_win"] >= settings.get("max_daily_win", 100000):
        return False, f"Дневной лимит выигрыша: {settings.get('max_daily_win', 100000)} ⭐"
    
    if user["consecutive_losses"] >= settings.get("max_consecutive_losses", 10):
        return False, f"Вы проиграли {user['consecutive_losses']} раз подряд! Сделайте паузу."
    
    return True, "OK"

async def update_user_limits(user_id: int, amount: int, is_win: bool = False, is_loss: bool = False):
    user = await get_user(user_id)
    
    if is_loss:
        await update_user(user_id, daily_loss=user["daily_loss"] + amount, consecutive_losses=user["consecutive_losses"] + 1, games_lost=user["games_lost"] + 1)
    elif is_win:
        await update_user(user_id, daily_win=user["daily_win"] + amount, consecutive_losses=0, games_won=user["games_won"] + 1)

# Система чеков
async def unlock_check_system(user_id: int) -> bool:
    settings = await load_json(SETTINGS_FILE, {})
    price = settings.get("check_system_price", 100)
    
    if await remove_stars(user_id, price, "Открытие системы чеков"):
        await update_user(user_id, check_system_unlocked=True)
        return True
    return False

async def create_check(user_id: int, amount: int) -> Tuple[bool, str, str, str]:
    settings = await load_json(SETTINGS_FILE, {})
    min_check = 100
    max_check = 100000
    
    user = await get_user(user_id)
    if not user.get("check_system_unlocked", False):
        return False, f"Система чеков заблокирована! Откройте за {settings.get('check_system_price', 100)} ⭐", "", ""
    
    if amount < min_check:
        return False, f"Минимальная сумма чека: {min_check} ⭐", "", ""
    if amount > max_check:
        return False, f"Максимальная сумма чека: {max_check} ⭐", "", ""
    
    if user["stars"] < amount:
        return False, f"Недостаточно звезд! У вас {user['stars']} ⭐", "", ""
    
    await remove_stars(user_id, amount, f"Создание чека")
    
    checks = await load_json(CHECKS_FILE, {"checks": [], "used_checks": []})
    code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
    
    check = {
        "code": code,
        "amount": amount,
        "creator": user_id,
        "created_at": datetime.now().isoformat(),
        "used": False,
        "used_by": None,
        "type": "user"
    }
    
    checks["checks"].append(check)
    await save_json(CHECKS_FILE, checks)
    
    bot_username = (await bot.get_me()).username
    check_link = f"https://t.me/{bot_username}?start=check_{code}"
    
    return True, f"Чек создан!", code, check_link

async def use_check_by_code(user_id: int, code: str) -> Tuple[bool, str, int]:
    checks = await load_json(CHECKS_FILE, {"checks": [], "used_checks": []})
    
    for check in checks["checks"]:
        if check["code"] == code:
            if check["used"]:
                return False, "Чек уже использован!", 0
            
            await add_stars(user_id, check["amount"], f"Активация чека {code}")
            check["used"] = True
            check["used_by"] = user_id
            check["used_at"] = datetime.now().isoformat()
            
            checks["used_checks"].append(check)
            checks["checks"].remove(check)
            
            await save_json(CHECKS_FILE, checks)
            return True, f"Чек активирован! Получено {check['amount']} ⭐", check["amount"]
    
    return False, "Чек не найден!", 0

# Система промокодов
async def create_promo(admin_id: int, code: str, reward: int, limit: int) -> bool:
    promo = await load_json(PROMO_FILE, {"promo_codes": [], "used_promo": {}})
    
    for p in promo["promo_codes"]:
        if p["code"] == code:
            return False
    
    promo["promo_codes"].append({
        "code": code,
        "reward": reward,
        "limit": limit,
        "used": 0,
        "created_by": admin_id,
        "created_at": datetime.now().isoformat(),
        "active": True
    })
    
    await save_json(PROMO_FILE, promo)
    await log_admin_action(admin_id, "create_promo", None, f"Code: {code}, Reward: {reward}, Limit: {limit}")
    return True

async def use_promo(user_id: int, code: str) -> Tuple[bool, str, int]:
    promo = await load_json(PROMO_FILE, {"promo_codes": [], "used_promo": {}})
    
    for promo_code in promo["promo_codes"]:
        if promo_code["code"] == code:
            if not promo_code["active"]:
                return False, "Промокод неактивен!", 0
            
            if promo_code["used"] >= promo_code["limit"]:
                return False, "Промокод достиг лимита!", 0
            
            user_id_str = str(user_id)
            if user_id_str in promo["used_promo"] and code in promo["used_promo"][user_id_str]:
                return False, "Вы уже использовали этот промокод!", 0
            
            await add_stars(user_id, promo_code["reward"], f"Активация промокода {code}")
            promo_code["used"] += 1
            if user_id_str not in promo["used_promo"]:
                promo["used_promo"][user_id_str] = []
            promo["used_promo"][user_id_str].append(code)
            
            await save_json(PROMO_FILE, promo)
            return True, f"Промокод активирован! Получено {promo_code['reward']} ⭐", promo_code["reward"]
    
    return False, "Промокод не найден!", 0

# Система заданий
async def add_task(admin_id: int, name: str, link: str, reward: int) -> int:
    tasks = await load_json(TASKS_FILE, {"sponsor_tasks": [], "completed_tasks": {}})
    task_id = len(tasks["sponsor_tasks"]) + 1
    tasks["sponsor_tasks"].append({
        "id": task_id,
        "name": name,
        "link": link,
        "reward": reward,
        "required_bot": BOT_ID,
        "created_at": datetime.now().isoformat(),
        "created_by": admin_id
    })
    await save_json(TASKS_FILE, tasks)
    await log_admin_action(admin_id, "add_task", None, f"Name: {name}, Reward: {reward}, Link: {link}")
    return task_id

async def check_task_completion(user_id: int, task: dict) -> Tuple[bool, str]:
    channel = task["link"].split("/")[-1]
    
    try:
        member = await bot.get_chat_member(channel, user_id)
        if member.status not in ["member", "administrator", "creator"]:
            return False, "❌ Вы не подписаны на канал!"
        
        bot_member = await bot.get_chat_member(channel, BOT_ID)
        if bot_member.status not in ["member", "administrator", "creator"]:
            return False, "❌ Бот не добавлен в канал администратором!"
        
        return True, "✅ Задание выполнено!"
    except Exception as e:
        return False, f"❌ Ошибка: бот не найден в канале!"

async def complete_task(user_id: int, task_id: int):
    tasks = await load_json(TASKS_FILE, {"sponsor_tasks": [], "completed_tasks": {}})
    if str(user_id) not in tasks["completed_tasks"]:
        tasks["completed_tasks"][str(user_id)] = []
    tasks["completed_tasks"][str(user_id)].append(task_id)
    await save_json(TASKS_FILE, tasks)

async def is_task_completed(user_id: int, task_id: int) -> bool:
    tasks = await load_json(TASKS_FILE, {"completed_tasks": {}})
    return task_id in tasks["completed_tasks"].get(str(user_id), [])

async def get_all_tasks() -> List[dict]:
    tasks = await load_json(TASKS_FILE, {"sponsor_tasks": []})
    return tasks["sponsor_tasks"]

async def delete_task(task_id: int) -> bool:
    tasks = await load_json(TASKS_FILE, {"sponsor_tasks": [], "completed_tasks": {}})
    original_len = len(tasks["sponsor_tasks"])
    tasks["sponsor_tasks"] = [t for t in tasks["sponsor_tasks"] if t["id"] != task_id]
    if len(tasks["sponsor_tasks"]) < original_len:
        await save_json(TASKS_FILE, tasks)
        return True
    return False

# Система поддержки
async def create_support_ticket(user_id: int, message: str) -> int:
    support = await load_json(SUPPORT_FILE, {"tickets": [], "messages": {}})
    ticket_id = len(support["tickets"]) + 1
    
    ticket = {
        "id": ticket_id,
        "user_id": user_id,
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "last_message": datetime.now().isoformat()
    }
    support["tickets"].append(ticket)
    
    if str(ticket_id) not in support["messages"]:
        support["messages"][str(ticket_id)] = []
    
    support["messages"][str(ticket_id)].append({
        "from_user": user_id,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "is_admin": False
    })
    
    await save_json(SUPPORT_FILE, support)
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"📩 *Новый тикет #{ticket_id}*\n\n👤 Пользователь: {user_id}\n💬 Сообщение: {message[:100]}",
                parse_mode="Markdown"
            )
        except:
            pass
    
    return ticket_id

async def reply_to_ticket(admin_id: int, ticket_id: int, message: str) -> bool:
    support = await load_json(SUPPORT_FILE, {"tickets": [], "messages": {}})
    
    ticket = next((t for t in support["tickets"] if t["id"] == ticket_id), None)
    if not ticket or ticket["status"] != "open":
        return False
    
    if str(ticket_id) not in support["messages"]:
        support["messages"][str(ticket_id)] = []
    
    support["messages"][str(ticket_id)].append({
        "from_user": admin_id,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "is_admin": True
    })
    
    ticket["last_message"] = datetime.now().isoformat()
    await save_json(SUPPORT_FILE, support)
    
    try:
        await bot.send_message(
            ticket["user_id"],
            f"📨 *Ответ на тикет #{ticket_id}*\n\n💬 {message}",
            parse_mode="Markdown"
        )
    except:
        pass
    
    return True

async def close_ticket(ticket_id: int) -> bool:
    support = await load_json(SUPPORT_FILE, {"tickets": [], "messages": {}})
    ticket = next((t for t in support["tickets"] if t["id"] == ticket_id), None)
    if ticket:
        ticket["status"] = "closed"
        ticket["closed_at"] = datetime.now().isoformat()
        await save_json(SUPPORT_FILE, support)
        return True
    return False

async def get_user_tickets(user_id: int) -> List[dict]:
    support = await load_json(SUPPORT_FILE, {"tickets": []})
    return [t for t in support["tickets"] if t["user_id"] == user_id]

# Система рассылок
async def create_mailing(admin_id: int, message_text: str, message_type: str = "text", file_id: str = None) -> int:
    mailing = await load_json(MAILING_FILE, {"mailings": [], "stats": {}})
    mailing_id = len(mailing["mailings"]) + 1
    
    mailing["mailings"].append({
        "id": mailing_id,
        "admin_id": admin_id,
        "message": message_text,
        "type": message_type,
        "file_id": file_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "sent_count": 0,
        "total_users": 0
    })
    
    await save_json(MAILING_FILE, mailing)
    return mailing_id

async def start_mailing(mailing_id: int):
    mailing = await load_json(MAILING_FILE, {"mailings": [], "stats": {}})
    mailing_data = next((m for m in mailing["mailings"] if m["id"] == mailing_id), None)
    
    if not mailing_data or mailing_data["status"] != "pending":
        return
    
    users = await load_json(USERS_FILE, {})
    total_users = len(users)
    mailing_data["total_users"] = total_users
    mailing_data["status"] = "running"
    await save_json(MAILING_FILE, mailing)
    
    sent = 0
    failed = 0
    
    for user_id in users.keys():
        try:
            if mailing_data["type"] == "text":
                await bot.send_message(int(user_id), mailing_data["message"], parse_mode="Markdown")
            elif mailing_data["type"] == "photo":
                await bot.send_photo(int(user_id), mailing_data["file_id"], caption=mailing_data["message"], parse_mode="Markdown")
            elif mailing_data["type"] == "video":
                await bot.send_video(int(user_id), mailing_data["file_id"], caption=mailing_data["message"], parse_mode="Markdown")
            sent += 1
        except:
            failed += 1
        await asyncio.sleep(0.05)
    
    mailing_data["status"] = "completed"
    mailing_data["sent_count"] = sent
    mailing_data["failed_count"] = failed
    mailing_data["completed_at"] = datetime.now().isoformat()
    await save_json(MAILING_FILE, mailing)

# ============== ИГРЫ ==============

# Игра Crash
class CrashGame:
    def __init__(self, user_id: int, bet: int, target_multiplier: float):
        self.user_id = user_id
        self.bet = bet
        self.target_multiplier = target_multiplier
        self.current_multiplier = 1.0
        self.is_active = True
        self.crashed_at = None
        self.is_win = False
        self.seed = secrets.token_hex(16)
        
    async def update_multiplier(self) -> float:
        crash_probability = 1 / (self.current_multiplier * 8)
        if random.random() < crash_probability:
            self.is_active = False
            self.crashed_at = self.current_multiplier
            if self.current_multiplier >= self.target_multiplier:
                self.is_win = True
            return 0
        increment = random.uniform(0.02, 0.1) * (1 - (self.current_multiplier / 40))
        self.current_multiplier += max(increment, 0.01)
        return self.current_multiplier
    
    async def check_win(self) -> Tuple[bool, int]:
        if self.current_multiplier >= self.target_multiplier:
            self.is_active = False
            self.is_win = True
            winnings = int(self.bet * self.target_multiplier)
            user = await get_user(self.user_id)
            await add_stars(self.user_id, winnings, f"Выигрыш в Crash (x{self.target_multiplier:.2f})")
            await update_user(self.user_id, games_won=user["games_won"] + 1)
            await update_user_limits(self.user_id, winnings, is_win=True)
            return True, winnings
        return False, 0

# Игра Mines
class MinesGame:
    def __init__(self, user_id: int, bet: int, mines_count: int):
        self.user_id = user_id
        self.bet = bet
        self.mines_count = mines_count
        self.size = 25
        self.opened = set()
        self.mines = set(random.sample(range(self.size), mines_count))
        self.current_multiplier = 1.0
        self.is_active = True
        self.seed = secrets.token_hex(16)
        
    def get_multiplier(self) -> float:
        safe_cells = self.size - self.mines_count
        opened_safe = len([c for c in self.opened if c not in self.mines])
        if opened_safe == 0:
            return 1.0
        multiplier = 1.0 + (opened_safe / safe_cells) * 8.0
        return min(multiplier, 25.0)
    
    async def open_cell(self, cell: int) -> Tuple[bool, bool, float]:
        if cell in self.opened:
            return False, False, self.current_multiplier
        
        self.opened.add(cell)
        
        if cell in self.mines:
            self.is_active = False
            return True, False, self.current_multiplier
        
        self.current_multiplier = self.get_multiplier()
        return True, True, self.current_multiplier
    
    async def cashout(self) -> int:
        if self.is_active:
            winnings = int(self.bet * self.current_multiplier)
            user = await get_user(self.user_id)
            await add_stars(self.user_id, winnings, f"Выигрыш в Mines (x{self.current_multiplier:.2f})")
            await update_user(self.user_id, games_won=user["games_won"] + 1)
            await update_user_limits(self.user_id, winnings, is_win=True)
            return winnings
        return 0

# Игра 21 очко (Blackjack)
class BlackjackGame:
    def __init__(self, user_id: int, bet: int):
        self.user_id = user_id
        self.bet = bet
        self.deck = self.create_deck()
        random.shuffle(self.deck)
        self.player_hand = []
        self.dealer_hand = []
        self.player_score = 0
        self.dealer_score = 0
        self.is_active = True
        self.game_over = False
        
    def create_deck(self):
        suits = ['♥', '♦', '♣', '♠']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        return [f"{v}{s}" for v in values for s in suits]
    
    def card_value(self, card: str) -> int:
        val = card[:-1]
        if val in ['J', 'Q', 'K']:
            return 10
        if val == 'A':
            return 11
        return int(val)
    
    def calculate_score(self, hand: List[str]) -> int:
        score = 0
        aces = 0
        for card in hand:
            val = self.card_value(card)
            if val == 11:
                aces += 1
            score += val
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1
        return score
    
    async def start_game(self):
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]
        self.player_score = self.calculate_score(self.player_hand)
        self.dealer_score = self.calculate_score(self.dealer_hand)
        
    async def player_hit(self) -> Tuple[bool, int, bool]:
        if not self.is_active:
            return False, self.player_score, True
        
        self.player_hand.append(self.deck.pop())
        self.player_score = self.calculate_score(self.player_hand)
        
        if self.player_score > 21:
            self.is_active = False
            self.game_over = True
            await update_user_limits(self.user_id, self.bet, is_loss=True)
            return False, self.player_score, True
        
        return True, self.player_score, False
    
    async def player_stand(self) -> Tuple[int, int, bool]:
        self.is_active = False
        
        while self.dealer_score < 17:
            self.dealer_hand.append(self.deck.pop())
            self.dealer_score = self.calculate_score(self.dealer_hand)
        
        if self.dealer_score > 21 or self.player_score > self.dealer_score:
            winnings = int(self.bet * 2.1)
            await add_stars(self.user_id, winnings, "Выигрыш в 21 очко")
            await update_user_limits(self.user_id, winnings, is_win=True)
            return winnings, self.player_score, True
        elif self.player_score == self.dealer_score:
            winnings = self.bet
            await add_stars(self.user_id, winnings, "Ничья в 21 очко")
            return winnings, self.player_score, False
        else:
            await update_user_limits(self.user_id, self.bet, is_loss=True)
            return 0, self.player_score, False

# Функции игр
async def play_coin(bet: int, choice: str) -> Tuple[int, str, str]:
    result = random.choice(["eagle", "tails"])
    win = (choice == result)
    
    choice_rus = "Орёл" if choice == "eagle" else "Решка"
    result_rus = "Орёл" if result == "eagle" else "Решка"
    
    if win:
        winnings = int(bet * 1.95)
        return winnings, f"Вы выбрали: {choice_rus}\nВыпало: {result_rus}\n\n🎉 Вы выиграли {winnings} ⭐!", result
    else:
        return 0, f"Вы выбрали: {choice_rus}\nВыпало: {result_rus}\n\n😔 Вы проиграли {bet} ⭐", result

async def play_roulette(bet: int, choice: str) -> Tuple[int, str, int]:
    result = random.randint(0, 36)
    red_numbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    black_numbers = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]
    
    win = False
    if choice == "red":
        win = result in red_numbers
    elif choice == "black":
        win = result in black_numbers
    elif choice == "even":
        win = result % 2 == 0 and result != 0
    elif choice == "odd":
        win = result % 2 == 1 and result != 0
    
    color = "Красное" if result in red_numbers else ("Черное" if result in black_numbers else "Зеро")
    
    if win:
        winnings = int(bet * 1.95)
        return winnings, f"Выпало число: {result} ({color})\n\n🎉 Вы выиграли {winnings} ⭐!", result
    else:
        return 0, f"Выпало число: {result} ({color})\n\n😔 Вы проиграли {bet} ⭐", result

async def play_cubes(bet: int, choice: int) -> Tuple[int, str, int]:
    result = random.randint(1, 6)
    
    if choice == result:
        winnings = int(bet * 5.5)
        return winnings, f"Вы выбрали: {choice}\nВыпало: {result}\n\n🎉 Вы выиграли {winnings} ⭐!", result
    else:
        return 0, f"Вы выбрали: {choice}\nВыпало: {result}\n\n😔 Вы проиграли {bet} ⭐", result

async def play_diamond(bet: int, choice: int) -> Tuple[int, str, int]:
    result = random.randint(1, 2)
    
    if choice == result:
        winnings = int(bet * 2)
        return winnings, f"Вы выбрали: {choice}\nВыпало: {result}\n\n🎉 Вы нашли алмаз! Выигрыш: {winnings} ⭐!", result
    else:
        return 0, f"Вы выбрали: {choice}\nВыпало: {result}\n\n😔 Это был обычный камень! Проигрыш: {bet} ⭐", result

async def play_fortune(bet: int) -> Tuple[int, str]:
    multiplier = random.choice([0, 0, 0, 0.5, 1, 1, 1.5, 2, 2, 2.5, 3, 3, 4, 5, 7, 10, 15, 20, 30, 50])
    winnings = int(bet * multiplier)
    
    messages = {
        0: "😭 Увы, сегодня не ваш день...",
        0.5: "😕 Почти получилось!",
        1: "👍 Неплохо, вы вернули ставку!",
        1.5: "🙂 Хороший результат!",
        2: "🎉 Отлично! Удвоили ставку!",
        2.5: "🎉🎉 Прекрасный выигрыш!",
        3: "🤩 Ваша удача сегодня на высоте!",
        4: "🤩🤩 Невероятно!",
        5: "🤯 ВАУ! Умножили в 5 раз!",
        7: "🤯🤯 ФАНТАСТИКА!",
        10: "👑 КОРОЛЕВСКИЙ ВЫИГРЫШ!",
        15: "💎 ЛЕГЕНДАРНЫЙ ВЫИГРЫШ!",
        20: "🏆 МИФИЧЕСКАЯ УДАЧА!",
        30: "🚀 КОСМИЧЕСКАЯ УДАЧА!",
        50: "⚡ БОЖЕСТВЕННЫЙ ВЫИГРЫШ! 50x!"
    }
    return winnings, messages.get(multiplier, f"🎲 Вы выиграли {winnings} ⭐!")

async def play_knb(choice: str) -> Tuple[bool, str, str]:
    options = ["камень", "ножницы", "бумага"]
    bot_choice = random.choice(options)
    
    if choice == bot_choice:
        return False, f"Ничья! Бот выбрал {bot_choice}", bot_choice
    
    wins = {
        ("камень", "ножницы"): True,
        ("ножницы", "бумага"): True,
        ("бумага", "камень"): True
    }
    
    is_win = wins.get((choice, bot_choice), False)
    result = "Вы выиграли!" if is_win else "Вы проиграли!"
    return is_win, f"{result} Бот выбрал {bot_choice}", bot_choice

async def play_poker(bet: int) -> Tuple[int, str]:
    hands = [
        {"name": "Старшая карта", "mult": 0, "prob": 0.5},
        {"name": "Пара", "mult": 2, "prob": 0.2},
        {"name": "Две пары", "mult": 3, "prob": 0.1},
        {"name": "Сет", "mult": 5, "prob": 0.08},
        {"name": "Стрит", "mult": 8, "prob": 0.05},
        {"name": "Флеш", "mult": 10, "prob": 0.03},
        {"name": "Фулл хаус", "mult": 15, "prob": 0.02},
        {"name": "Каре", "mult": 25, "prob": 0.01},
        {"name": "Стрит флеш", "mult": 50, "prob": 0.005},
        {"name": "Роял флеш", "mult": 100, "prob": 0.001}
    ]
    
    rand = random.random()
    cumsum = 0
    for hand in hands:
        cumsum += hand["prob"]
        if rand <= cumsum:
            winnings = int(bet * hand["mult"])
            if hand["mult"] == 0:
                return 0, f"😭 {hand['name']}! Вы проиграли!"
            return winnings, f"🎉 {hand['name']}! Выигрыш x{hand['mult']} = {winnings} ⭐!"
    
    return 0, "😭 Вы проиграли!"

async def play_keno(bet: int, numbers: List[int]) -> Tuple[int, str, List[int]]:
    if len(numbers) != 5:
        return 0, "❌ Нужно выбрать ровно 5 чисел!", []
    
    drawn = set(random.sample(range(1, 81), 20))
    matches = len([n for n in numbers if n in drawn])
    
    payouts = {0: 0, 1: 0, 2: 0, 3: 2, 4: 5, 5: 20}
    multiplier = payouts.get(matches, 0)
    winnings = int(bet * multiplier)
    
    drawn_list = sorted(list(drawn))[:10]
    
    if winnings > 0:
        return winnings, f"🎯 Совпадений: {matches}/5! Выигрыш x{multiplier} = {winnings} ⭐!\nВыпавшие числа: {', '.join(map(str, drawn_list))}...", drawn_list
    else:
        return 0, f"😭 Совпадений: {matches}/5. Вы проиграли!\nВыпавшие числа: {', '.join(map(str, drawn_list))}...", drawn_list

async def play_wheel(bet: int) -> Tuple[int, str]:
    segments = [
        {"mult": 0, "prob": 0.2, "name": "😭 БАНКРОТ"},
        {"mult": 0.5, "prob": 0.15, "name": "😕 ПОЛОВИНА"},
        {"mult": 1, "prob": 0.15, "name": "👍 ВОЗВРАТ"},
        {"mult": 2, "prob": 0.12, "name": "🎉 x2"},
        {"mult": 3, "prob": 0.1, "name": "🎉🎉 x3"},
        {"mult": 5, "prob": 0.08, "name": "🤩 x5"},
        {"mult": 7, "prob": 0.07, "name": "🤩🤩 x7"},
        {"mult": 10, "prob": 0.05, "name": "👑 x10"},
        {"mult": 0, "prob": 0.08, "name": "😭 БАНКРОТ"}
    ]
    
    rand = random.random()
    cumsum = 0
    for seg in segments:
        cumsum += seg["prob"]
        if rand <= cumsum:
            winnings = int(bet * seg["mult"])
            if seg["mult"] == 0:
                return 0, f"{seg['name']}! Вы проиграли {bet} ⭐!"
            return winnings, f"{seg['name']}! Выигрыш {winnings} ⭐!"

# ============== ОБРАБОТЧИКИ КОМАНД ==============

# Главная клавиатура
def get_main_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🎮 Игры"), KeyboardButton(text="⭐ Баланс")],
        [KeyboardButton(text="👥 Рефералы"), KeyboardButton(text="📋 Задания")],
        [KeyboardButton(text="💰 Вывод"), KeyboardButton(text="🛒 Купить")],
        [KeyboardButton(text="🎫 Промокод"), KeyboardButton(text="📦 Чек система")],
        [KeyboardButton(text="💬 Поддержка"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Клавиатура выбора игры
def get_games_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🪙 Монета"), KeyboardButton(text="🎱 Рулетка"), KeyboardButton(text="🎲 Кости")],
        [KeyboardButton(text="📈 Crash"), KeyboardButton(text="💣 Mines"), KeyboardButton(text="🤩 Алмаз")],
        [KeyboardButton(text="♠️ 21 очко"), KeyboardButton(text="🔮 Фортуна"), KeyboardButton(text="✂️ КНБ")],
        [KeyboardButton(text="🃏 Покер"), KeyboardButton(text="🎯 Кено"), KeyboardButton(text="🎰 Колесо")],
        [KeyboardButton(text="🔙 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Команда /start
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    args = message.text.split()
    
    if len(args) > 1:
        if args[1].startswith("check_"):
            code = args[1].replace("check_", "")
            success, msg, _ = await use_check_by_code(message.from_user.id, code)
            await message.answer(f"{'✅' if success else '❌'} *{msg}*", parse_mode="Markdown")
            return
        
        referrer_id = args[1]
        if referrer_id.isdigit():
            referrer_id = int(referrer_id)
            if referrer_id != message.from_user.id:
                user = await get_user(message.from_user.id)
                if not user["referrer"]:
                    settings = await load_json(SETTINGS_FILE, {})
                    await update_user(message.from_user.id, referrer=referrer_id, username=message.from_user.username)
                    referral_reward = settings.get("referral_reward", 10)
                    await add_stars(referrer_id, referral_reward, f"Реферал {message.from_user.id}")
                    referrer = await get_user(referrer_id)
                    await update_user(referrer_id, referral_count=referrer["referral_count"] + 1, referral_earnings=referrer["referral_earnings"] + referral_reward)
    
    user = await get_user(message.from_user.id)
    if not user.get("username"):
        await update_user(message.from_user.id, username=message.from_user.username)
    
    text = (f"✨ *Добро пожаловать, {message.from_user.full_name}!*\n\n"
            f"⭐ Баланс: {user['stars']} ⭐\n\n"
            f"🎮 Выберите игру в меню ниже!\n"
            f"💰 Вывод: `/withdraw [сумма]`")
    
    await message.answer(text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# Обработка кнопок главного меню
@dp.message(F.text == "🎮 Игры")
async def games_menu(message: Message):
    await message.answer("🎮 *Выберите игру:*", parse_mode="Markdown", reply_markup=get_games_keyboard())

@dp.message(F.text == "🔙 Главное меню")
async def back_to_main_menu(message: Message):
    user = await get_user(message.from_user.id)
    await message.answer(f"✨ Главное меню\n\n⭐ У вас {user['stars']} ⭐", reply_markup=get_main_keyboard())

@dp.message(F.text == "⭐ Баланс")
async def stars_info(message: Message):
    user = await get_user(message.from_user.id)
    settings = await load_json(SETTINGS_FILE, {})
    
    text = (f"⭐ *Ваш баланс:* {user['stars']} ⭐\n\n"
            f"📊 *Детальная статистика:*\n"
            f"└ Всего заработано: {user['total_earned']} ⭐\n"
            f"└ Всего потрачено: {user['total_spent']} ⭐\n"
            f"└ Сыграно игр: {user['games_played']}\n"
            f"└ Побед: {user['games_won']}\n"
            f"└ Поражений: {user['games_lost']}\n"
            f"└ Дневные потери: {user['daily_loss']} ⭐\n"
            f"└ Дневные выигрыши: {user['daily_win']} ⭐\n\n"
            f"💱 Минимальный вывод: {settings.get('min_withdraw', 500)} ⭐")
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "👥 Рефералы")
async def referrals_menu(message: Message):
    user = await get_user(message.from_user.id)
    settings = await load_json(SETTINGS_FILE, {})
    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={user['referral_code']}"
    
    text = (f"👥 *Реферальная система*\n\n"
            f"📎 Ваша ссылка:\n`{link}`\n\n"
            f"📊 *Статистика:*\n"
            f"└ Приглашено: {user['referral_count']}\n"
            f"└ Заработано: {user['referral_earnings']} ⭐\n\n"
            f"💡 *Условия:*\n"
            f"• {settings.get('referral_reward', 10)} ⭐ за друга\n"
            f"• {settings.get('referral_percent', 10)}% от покупок друга")
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📋 Задания")
async def tasks_menu(message: Message):
    tasks = await get_all_tasks()
    
    if not tasks:
        text = "📋 *Задания*\n\nНет активных заданий."
        await message.answer(text, parse_mode="Markdown")
        return
    
    text = "📋 *Задания от спонсоров:*\n\n"
    for task in tasks:
        completed = await is_task_completed(message.from_user.id, task["id"])
        status = "✅ Выполнено" if completed else "❌ Не выполнено"
        text += f"• *{task['name']}*\n└ Награда: {task['reward']} ⭐\n└ Статус: {status}\n\n"
        if not completed:
            buttons = [[InlineKeyboardButton(text=f"✅ {task['name']}", callback_data=f"check_task_{task['id']}")]]
            await message.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
            return
    
    await message.answer(text, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("check_task_"))
async def check_task(callback: CallbackQuery):
    task_id = int(callback.data.replace("check_task_", ""))
    tasks = await get_all_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    
    if not task:
        await callback.answer("Задание не найдено!")
        return
    
    if await is_task_completed(callback.from_user.id, task_id):
        await callback.answer("Вы уже выполнили это задание!", show_alert=True)
        return
    
    success, message_text = await check_task_completion(callback.from_user.id, task)
    
    if success:
        await add_stars(callback.from_user.id, task["reward"], f"Задание: {task['name']}")
        await complete_task(callback.from_user.id, task_id)
        await callback.answer(f"✅ +{task['reward']} ⭐", show_alert=True)
        await tasks_menu(callback.message)
    else:
        await callback.answer(message_text, show_alert=True)

@dp.message(F.text == "💰 Вывод")
async def withdraw_menu(message: Message):
    user = await get_user(message.from_user.id)
    settings = await load_json(SETTINGS_FILE, {})
    
    text = (f"💰 *Вывод звезд*\n\n"
            f"⭐ Баланс: {user['stars']}\n"
            f"📉 Минимум: {settings.get('min_withdraw', 500)} ⭐\n"
            f"⏰ КД между выводами: {settings.get('withdraw_cooldown_hours', 24)} часов\n"
            f"📊 Лимит выводов в день: {settings.get('max_withdraw_per_day', 3)}\n\n"
            f"Команда: `/withdraw <сумма>`")
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("withdraw"))
async def withdraw_stars(message: Message):
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ Использование: /withdraw <сумма>")
        return
    
    try:
        amount = int(args[1])
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    user = await get_user(message.from_user.id)
    settings = await load_json(SETTINGS_FILE, {})
    
    if amount < settings.get("min_withdraw", 500):
        await message.answer(f"❌ Минимальная сумма вывода: {settings.get('min_withdraw', 500)} ⭐")
        return
    
    if user["stars"] < amount:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    if user.get("is_withdraw_banned", False):
        await message.answer(f"❌ Вы забанены на вывод!")
        return
    
    await remove_stars(message.from_user.id, amount, "Вывод звезд")
    
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    wid = len(withdrawals) + 1
    withdrawals[str(wid)] = {
        "id": wid,
        "user_id": message.from_user.id,
        "username": message.from_user.username or str(message.from_user.id),
        "stars": amount,
        "tg_stars": amount,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    await save_json(WITHDRAWALS_FILE, withdrawals)
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"💰 *Заявка #{wid}*\n👤 @{message.from_user.username or message.from_user.id}\n⭐ {amount} ⭐",
                parse_mode="Markdown"
            )
        except:
            pass
    
    await message.answer(f"✅ Заявка #{wid} создана! Ожидайте подтверждения администратора.")

@dp.message(F.text == "🛒 Купить")
async def buy_stars_menu(message: Message, state: FSMContext):
    await state.set_state(BuyStates.waiting_for_amount)
    await message.answer(
        "🛒 *Покупка звезд*\n\n"
        "💎 Курс: 1 ⭐ TG = 1 ⭐\n\n"
        "Введите количество звезд для покупки (от 50 до 100000):\n"
        "Для отмены отправьте /cancel",
        parse_mode="Markdown"
    )

@dp.message(BuyStates.waiting_for_amount)
async def buy_stars_amount(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Покупка отменена!")
        return
    
    try:
        amount = int(message.text)
        if amount < 50:
            await message.answer("❌ Минимальная сумма покупки: 50 ⭐")
            return
        if amount > 100000:
            await message.answer("❌ Максимальная сумма покупки: 100000 ⭐")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    await bot.send_invoice(
        chat_id=message.from_user.id,
        title=f"Покупка {amount} звезд",
        description=f"Вы получаете {amount} ⭐ для игры в боте!",
        payload=f"stars_{amount}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"{amount} ⭐", amount=amount)],
        start_parameter="buy_stars"
    )
    await state.clear()

@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    amount = int(message.successful_payment.invoice_payload.replace("stars_", ""))
    await add_stars(message.from_user.id, amount, f"Покупка {amount} звезд")
    user = await get_user(message.from_user.id)
    await update_user(message.from_user.id, total_purchases=user["total_purchases"] + amount)
    
    if user.get("referrer"):
        referrer_id = user["referrer"]
        settings = await load_json(SETTINGS_FILE, {})
        percent = settings.get("referral_percent", 10)
        referral_earn = int(amount * percent / 100)
        await add_stars(referrer_id, referral_earn, f"Реферальные {percent}% от покупки {message.from_user.id}")
        referrer = await get_user(referrer_id)
        await update_user(referrer_id, referral_earnings=referrer["referral_earnings"] + referral_earn)
    
    await message.answer(
        f"✅ *Покупка успешна!*\n\n⭐ Начислено: {amount} ⭐\n💰 Баланс: {user['stars'] + amount} ⭐",
        parse_mode="Markdown"
    )

@dp.message(F.text == "🎫 Промокод")
async def use_promo_menu(message: Message, state: FSMContext):
    await state.set_state(PromoStates.waiting_for_promo_code)
    await message.answer(
        "🎫 *Активация промокода*\n\nВведите промокод:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )

@dp.message(PromoStates.waiting_for_promo_code)
async def use_promo_code(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Отменено!")
        return
    
    success, msg, _ = await use_promo(message.from_user.id, message.text.strip().upper())
    await message.answer(f"{'✅' if success else '❌'} *{msg}*", parse_mode="Markdown")
    await state.clear()

@dp.message(F.text == "📦 Чек система")
async def check_system_menu(message: Message):
    user = await get_user(message.from_user.id)
    settings = await load_json(SETTINGS_FILE, {})
    
    if user.get("check_system_unlocked", False):
        text = (f"📦 *Система чеков*\n\n"
                f"✅ Система разблокирована!\n\n"
                f"💰 Создание чека:\n"
                f"└ Минимальная сумма: 100 ⭐\n"
                f"└ Максимальная сумма: 100000 ⭐\n\n"
                f"📋 Ваши чеки: `/my_checks`\n"
                f"🎫 Активировать чек: `/use_check <код>`")
        
        buttons = [
            [InlineKeyboardButton(text="📝 Создать чек", callback_data="create_check")],
            [InlineKeyboardButton(text="📋 Мои чеки", callback_data="my_checks")]
        ]
        await message.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    else:
        price = settings.get("check_system_price", 100)
        text = (f"📦 *Система чеков*\n\n"
                f"🔒 Система заблокирована!\n\n"
                f"💎 Стоимость разблокировки: {price} ⭐\n\n"
                f"После разблокировки вы сможете:\n"
                f"• Создавать чеки для друзей\n"
                f"• Активировать чеки других пользователей\n"
                f"• Переводить звезды между пользователями")
        
        buttons = [[InlineKeyboardButton(text="🔓 Разблокировать", callback_data="unlock_check_system")]]
        await message.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data == "unlock_check_system")
async def unlock_check_system_callback(callback: CallbackQuery):
    success = await unlock_check_system(callback.from_user.id)
    
    if success:
        await callback.answer("✅ Система чеков разблокирована!", show_alert=True)
    else:
        settings = await load_json(SETTINGS_FILE, {})
        price = settings.get("check_system_price", 100)
        await callback.answer(f"❌ Недостаточно звезд! Нужно {price} ⭐", show_alert=True)
    
    await check_system_menu(callback.message)

@dp.callback_query(F.data == "create_check")
async def create_check_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_check_amount)
    await callback.message.edit_text(
        "📦 *Создание чека*\n\n"
        "💰 Минимальная сумма: 100 ⭐\n"
        "💰 Максимальная сумма: 100000 ⭐\n\n"
        "Введите сумму чека:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(AdminStates.waiting_for_check_amount)
async def create_check_amount(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Отменено!")
        return
    
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    success, msg, code, link = await create_check(message.from_user.id, amount)
    
    if success:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Копировать ссылку", callback_data=f"copy_{link}")]
        ])
        await message.answer(
            f"✅ {msg}\n\n"
            f"📦 Ссылка для активации: {link}\n"
            f"💰 Сумма: {amount} ⭐\n\n"
            f"Отправьте эту ссылку другу для активации чека!",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        await message.answer(f"❌ {msg}")
    
    await state.clear()

@dp.callback_query(F.data == "my_checks")
async def my_checks(callback: CallbackQuery):
    checks = await load_json(CHECKS_FILE, {"checks": [], "used_checks": []})
    user_checks = []
    for check in checks["checks"]:
        if check.get("creator") == callback.from_user.id:
            user_checks.append(check)
    for check in checks["used_checks"]:
        if check.get("creator") == callback.from_user.id:
            user_checks.append(check)
    
    if not user_checks:
        text = "📋 *Ваши чеки*\n\nУ вас нет созданных чеков."
    else:
        text = "📋 *Ваши чеки:*\n\n"
        active = [c for c in user_checks if not c.get("used", False)]
        used = [c for c in user_checks if c.get("used", False)]
        
        if active:
            text += "*Активные чеки:*\n"
            for c in active:
                text += f"└ Сумма: {c['amount']} ⭐\n"
        
        if used:
            text += "\n*Использованные чеки:*\n"
            for c in used[-10:]:
                text += f"└ Сумма: {c['amount']} ⭐ (активировал: {c.get('used_by', '?')})\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()

@dp.message(Command("use_check"))
async def use_check_command(message: Message):
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ Использование: /use_check <код>")
        return
    
    code = args[1]
    success, msg, _ = await use_check_by_code(message.from_user.id, code)
    await message.answer(f"{'✅' if success else '❌'} *{msg}*", parse_mode="Markdown")

@dp.message(F.text == "💬 Поддержка")
async def support_menu(message: Message):
    tickets = await get_user_tickets(message.from_user.id)
    open_tickets = [t for t in tickets if t["status"] == "open"]
    
    text = (f"💬 *Поддержка*\n\n"
            f"📊 Ваши тикеты:\n"
            f"└ Открытых: {len(open_tickets)}\n"
            f"└ Закрытых: {len(tickets) - len(open_tickets)}\n\n"
            f"Выберите действие:")
    
    buttons = [
        [InlineKeyboardButton(text="📝 Создать тикет", callback_data="support_create")],
        [InlineKeyboardButton(text="📋 Мои тикеты", callback_data="support_my_tickets")]
    ]
    
    await message.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data == "support_create")
async def support_create(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting_for_message)
    await callback.message.edit_text(
        "💬 *Создание тикета*\n\n"
        "Опишите вашу проблему или вопрос. Наши администраторы свяжутся с вами в ближайшее время.\n\n"
        "Введите ваше сообщение:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(SupportStates.waiting_for_message)
async def support_send_message(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Отменено!")
        return
    
    ticket_id = await create_support_ticket(message.from_user.id, message.text)
    await message.answer(
        f"✅ *Тикет #{ticket_id} создан!*\n\n"
        f"Наши администраторы свяжутся с вами в ближайшее время.\n"
        f"Вы можете отслеживать статус тикета в разделе 'Мои тикеты'.",
        parse_mode="Markdown"
    )
    await state.clear()

@dp.callback_query(F.data == "support_my_tickets")
async def support_my_tickets(callback: CallbackQuery):
    tickets = await get_user_tickets(callback.from_user.id)
    
    if not tickets:
        text = "📋 *Мои тикеты*\n\nУ вас нет тикетов."
    else:
        text = "📋 *Мои тикеты:*\n\n"
        for ticket in tickets[-10:]:
            status = "🟢 Открыт" if ticket["status"] == "open" else "🔴 Закрыт"
            text += f"*#{ticket['id']}* - {status}\n└ Создан: {ticket['created_at'][:19]}\n\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()

@dp.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    user = await get_user(message.from_user.id)
    text = (f"📊 *Ваша статистика*\n\n"
            f"⭐ Баланс: {user['stars']}\n"
            f"💰 Заработано: {user['total_earned']}\n"
            f"💸 Потрачено: {user['total_spent']}\n"
            f"👥 Рефералов: {user['referral_count']}\n"
            f"🎮 Игр: {user['games_played']}\n"
            f"🏆 Побед: {user['games_won']}\n"
            f"😭 Поражений: {user['games_lost']}\n"
            f"✨ Достижений: {len(user['achievements'])}\n"
            f"📅 Дневные потери: {user['daily_loss']} ⭐\n"
            f"📈 Дневные выигрыши: {user['daily_win']} ⭐\n"
            f"📊 Проигрышей подряд: {user['consecutive_losses']}\n"
            f"📦 Чек система: {'✅' if user.get('check_system_unlocked', False) else '🔒'}\n"
            f"📅 Регистрация: {user['created_at'][:10]}")
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "❓ Помощь")
async def show_help(message: Message):
    settings = await load_json(SETTINGS_FILE, {})
    text = (f"❓ *Помощь*\n\n"
            f"🎮 *Игры (12):*\n"
            f"└ Монета (x1.95) - угадай орёл/решка\n"
            f"└ Рулетка (x1.95) - красное/черное/четное/нечетное\n"
            f"└ Кости (x5.5) - угадай число 1-6\n"
            f"└ Crash (x1.01-50) - лови момент\n"
            f"└ Mines (x1-25) - открывай клетки\n"
            f"└ Алмаз (x2) - найди алмаз\n"
            f"└ 21 очко (x2.1) - блэкджек\n"
            f"└ Фортуна (x0-x50) - случайный множитель\n"
            f"└ КНБ (x2.7) - камень/ножницы/бумага\n"
            f"└ Покер (x0-x100) - случайная комбинация\n"
            f"└ Кено (x0-x20) - 5 чисел от 1 до 80\n"
            f"└ Колесо Фортуны (x0-x10) - крути колесо\n\n"
            f"👥 *Рефералы:* {settings.get('referral_reward', 10)} ⭐ за друга + {settings.get('referral_percent', 10)}% от его покупок\n\n"
            f"📦 *Чеки:*\n"
            f"└ Разблокировка: {settings.get('check_system_price', 100)} ⭐\n"
            f"└ Создание чека: от 100 до 100000 ⭐\n"
            f"└ Активация чека: по ссылке или `/use_check <код>`\n\n"
            f"💰 *Вывод:* `/withdraw <сумма>`, мин. {settings.get('min_withdraw', 500)} ⭐\n"
            f"🛒 *Покупка:* Введите сумму в меню покупки\n\n"
            f"⚠️ *Лимиты:*\n"
            f"└ Дневной лимит потерь: {settings.get('max_daily_loss', 50000)} ⭐\n"
            f"└ Дневной лимит выигрыша: {settings.get('max_daily_win', 100000)} ⭐\n"
            f"└ Макс. проигрышей подряд: {settings.get('max_consecutive_losses', 10)}\n\n"
            f"💬 *Поддержка:* Создайте тикет в меню поддержки")
    
    await message.answer(text, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("copy_"))
async def copy_text(callback: CallbackQuery):
    text = callback.data.replace("copy_", "")
    await callback.answer("✅ Ссылка скопирована!", show_alert=True)

# ============== ИГРЫ - ОБРАБОТЧИКИ ==============

# Игра Монета
@dp.message(F.text == "🪙 Монета")
async def coin_start(message: Message, state: FSMContext):
    await state.set_state(GameStates.waiting_for_coin_bet)
    await message.answer(
        "🪙 *Игра Монета*\n\n"
        "💰 Ставка: от 1 до 1000 ⭐\n"
        "🎯 Множитель: x1.95\n\n"
        "Введите сумму ставки:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )

@dp.message(GameStates.waiting_for_coin_bet)
async def coin_bet(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        bet = int(message.text)
        if bet < 1 or bet > 1000:
            await message.answer("❌ Ставка должна быть от 1 до 1000 ⭐")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    user = await get_user(message.from_user.id)
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "coin")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        await state.clear()
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await state.update_data(coin_bet=bet)
    await state.set_state(GameStates.waiting_for_coin_choice)
    
    buttons = [
        [InlineKeyboardButton(text="🦅 Орёл", callback_data="coin_eagle"),
         InlineKeyboardButton(text="🪙 Решка", callback_data="coin_tails")]
    ]
    await message.answer(f"💰 Ставка: {bet} ⭐\n\nВыберите сторону:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(GameStates.waiting_for_coin_choice, F.data.startswith("coin_"))
async def coin_play(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bet = data.get("coin_bet")
    choice = "eagle" if callback.data == "coin_eagle" else "tails"
    
    user = await get_user(callback.from_user.id)
    
    if user["stars"] < bet:
        await callback.answer("❌ Недостаточно звезд!", show_alert=True)
        await state.clear()
        return
    
    await remove_stars(callback.from_user.id, bet, "Ставка в Монете")
    await update_user(callback.from_user.id, games_played=user["games_played"] + 1)
    
    winnings, result_text, result = await play_coin(bet, choice)
    game_hash = generate_game_hash("coin", bet, result, callback.from_user.id)
    await save_game_hash(game_hash)
    
    if winnings > 0:
        await add_stars(callback.from_user.id, winnings, "Выигрыш в Монете")
        await update_user_limits(callback.from_user.id, winnings, is_win=True)
    else:
        await update_user_limits(callback.from_user.id, bet, is_loss=True)
    
    buttons = [[InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]]
    await callback.message.edit_text(
        f"🪙 *Монета*\n\n{result_text}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.clear()
    await callback.answer()

# Игра Рулетка
@dp.message(F.text == "🎱 Рулетка")
async def roulette_start(message: Message, state: FSMContext):
    await state.set_state(GameStates.waiting_for_roulette_bet)
    await message.answer(
        "🎱 *Игра Рулетка*\n\n"
        "💰 Ставка: от 5 до 2000 ⭐\n"
        "🎯 Множитель: x1.95\n\n"
        "Введите сумму ставки:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )

@dp.message(GameStates.waiting_for_roulette_bet)
async def roulette_bet(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        bet = int(message.text)
        if bet < 5 or bet > 2000:
            await message.answer("❌ Ставка должна быть от 5 до 2000 ⭐")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    user = await get_user(message.from_user.id)
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "roulette")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        await state.clear()
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await state.update_data(roulette_bet=bet)
    await state.set_state(GameStates.waiting_for_roulette_choice)
    
    buttons = [
        [InlineKeyboardButton(text="🔴 Красное", callback_data="roulette_red"),
         InlineKeyboardButton(text="⚫ Черное", callback_data="roulette_black")],
        [InlineKeyboardButton(text="🟢 Четное", callback_data="roulette_even"),
         InlineKeyboardButton(text="🟡 Нечетное", callback_data="roulette_odd")]
    ]
    await message.answer(f"💰 Ставка: {bet} ⭐\n\nВыберите тип ставки:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(GameStates.waiting_for_roulette_choice, F.data.startswith("roulette_"))
async def roulette_play(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bet = data.get("roulette_bet")
    choice = callback.data.replace("roulette_", "")
    
    user = await get_user(callback.from_user.id)
    
    if user["stars"] < bet:
        await callback.answer("❌ Недостаточно звезд!", show_alert=True)
        await state.clear()
        return
    
    await remove_stars(callback.from_user.id, bet, "Ставка в Рулетке")
    await update_user(callback.from_user.id, games_played=user["games_played"] + 1)
    
    winnings, result_text, result = await play_roulette(bet, choice)
    game_hash = generate_game_hash("roulette", bet, result, callback.from_user.id)
    await save_game_hash(game_hash)
    
    if winnings > 0:
        await add_stars(callback.from_user.id, winnings, "Выигрыш в Рулетке")
        await update_user_limits(callback.from_user.id, winnings, is_win=True)
    else:
        await update_user_limits(callback.from_user.id, bet, is_loss=True)
    
    buttons = [[InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]]
    await callback.message.edit_text(
        f"🎱 *Рулетка*\n\n{result_text}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.clear()
    await callback.answer()

# Игра Кости
@dp.message(F.text == "🎲 Кости")
async def cubes_start(message: Message, state: FSMContext):
    await state.set_state(GameStates.waiting_for_cubes_bet)
    await message.answer(
        "🎲 *Игра Кости*\n\n"
        "💰 Ставка: от 5 до 1000 ⭐\n"
        "🎯 Множитель: x5.5\n\n"
        "Введите сумму ставки:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )

@dp.message(GameStates.waiting_for_cubes_bet)
async def cubes_bet(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        bet = int(message.text)
        if bet < 5 or bet > 1000:
            await message.answer("❌ Ставка должна быть от 5 до 1000 ⭐")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    user = await get_user(message.from_user.id)
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "cubes")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        await state.clear()
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await state.update_data(cubes_bet=bet)
    await state.set_state(GameStates.waiting_for_cubes_choice)
    
    buttons = []
    row = []
    for i in range(1, 7):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"cubes_{i}"))
        if i % 3 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    await message.answer(f"💰 Ставка: {bet} ⭐\n\nВыберите число:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(GameStates.waiting_for_cubes_choice, F.data.startswith("cubes_"))
async def cubes_play(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bet = data.get("cubes_bet")
    choice = int(callback.data.replace("cubes_", ""))
    
    user = await get_user(callback.from_user.id)
    
    if user["stars"] < bet:
        await callback.answer("❌ Недостаточно звезд!", show_alert=True)
        await state.clear()
        return
    
    await remove_stars(callback.from_user.id, bet, "Ставка в Костях")
    await update_user(callback.from_user.id, games_played=user["games_played"] + 1)
    
    winnings, result_text, result = await play_cubes(bet, choice)
    game_hash = generate_game_hash("cubes", bet, result, callback.from_user.id)
    await save_game_hash(game_hash)
    
    if winnings > 0:
        await add_stars(callback.from_user.id, winnings, "Выигрыш в Костях")
        await update_user_limits(callback.from_user.id, winnings, is_win=True)
    else:
        await update_user_limits(callback.from_user.id, bet, is_loss=True)
    
    buttons = [[InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]]
    await callback.message.edit_text(
        f"🎲 *Кости*\n\n{result_text}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.clear()
    await callback.answer()

# Игра Crash
@dp.message(F.text == "📈 Crash")
async def crash_start(message: Message, state: FSMContext):
    await state.set_state(GameStates.waiting_for_crash_bet)
    await message.answer(
        "📈 *Игра Crash*\n\n"
        "💰 Ставка: от 5 до 2000 ⭐\n"
        "🎯 Множитель: от 1.01 до 50\n\n"
        "Введите сумму ставки:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )

@dp.message(GameStates.waiting_for_crash_bet)
async def crash_bet(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        bet = int(message.text)
        if bet < 5 or bet > 2000:
            await message.answer("❌ Ставка должна быть от 5 до 2000 ⭐")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    user = await get_user(message.from_user.id)
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "crash")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        await state.clear()
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await state.update_data(crash_bet=bet)
    await state.set_state(GameStates.waiting_for_crash_multiplier)
    await message.answer("💰 Введите целевой множитель (от 1.01 до 50):")

@dp.message(GameStates.waiting_for_crash_multiplier)
async def crash_multiplier(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        target = float(message.text)
        if target < 1.01 or target > 50:
            await message.answer("❌ Множитель должен быть от 1.01 до 50!")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    bet = data.get("crash_bet")
    user = await get_user(message.from_user.id)
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Crash")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    crash_game = CrashGame(message.from_user.id, bet, target)
    await state.update_data(crash_game=crash_game, target_multiplier=target)
    await state.set_state(CrashStates.playing)
    
    msg = await message.answer(
        f"📈 *Crash Game*\n\n"
        f"💰 Ставка: {bet} ⭐\n"
        f"🎯 Цель: x{target:.2f}\n"
        f"📈 Текущий множитель: 1.00x\n\n"
        f"Множитель растет...",
        parse_mode="Markdown"
    )
    
    await state.update_data(message_id=msg.message_id)
    asyncio.create_task(update_crash_game(message.from_user.id, state, msg.message_id))

async def update_crash_game(user_id: int, state: FSMContext, message_id: int):
    data = await state.get_data()
    crash_game = data.get("crash_game")
    target = data.get("target_multiplier", 2.0)
    
    if not crash_game:
        return
    
    while crash_game.is_active:
        await asyncio.sleep(0.3)
        multiplier = await crash_game.update_multiplier()
        
        if not crash_game.is_active:
            game_hash = generate_game_hash("crash", crash_game.bet, crash_game.crashed_at, user_id)
            await save_game_hash(game_hash)
            
            if crash_game.is_win:
                winnings = int(crash_game.bet * target)
                await bot.edit_message_text(
                    f"📈 *Crash Game*\n\n"
                    f"💰 Ставка: {crash_game.bet} ⭐\n"
                    f"🎯 Цель: x{target:.2f}\n"
                    f"✅ Множитель достиг {crash_game.crashed_at:.2f}x!\n"
                    f"🎉 Вы достигли цели! Выигрыш: {winnings} ⭐!",
                    chat_id=user_id,
                    message_id=message_id,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
                    ])
                )
            else:
                await bot.edit_message_text(
                    f"📈 *Crash Game*\n\n"
                    f"💰 Ставка: {crash_game.bet} ⭐\n"
                    f"🎯 Цель: x{target:.2f}\n"
                    f"💥 Крах на {crash_game.crashed_at:.2f}x!\n"
                    f"😔 Вы не достигли цели. Проигрыш: {crash_game.bet} ⭐",
                    chat_id=user_id,
                    message_id=message_id,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
                    ])
                )
            await state.clear()
            return
        else:
            if multiplier >= target:
                win, winnings = await crash_game.check_win()
                if win:
                    game_hash = generate_game_hash("crash", crash_game.bet, target, user_id)
                    await save_game_hash(game_hash)
                    await bot.edit_message_text(
                        f"📈 *Crash Game*\n\n"
                        f"💰 Ставка: {crash_game.bet} ⭐\n"
                        f"🎯 Цель: x{target:.2f}\n"
                        f"✅ Множитель достиг {multiplier:.2f}x!\n"
                        f"🎉 Вы достигли цели! Выигрыш: {winnings} ⭐!",
                        chat_id=user_id,
                        message_id=message_id,
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
                        ])
                    )
                    await state.clear()
                    return
            
            await bot.edit_message_text(
                f"📈 *Crash Game*\n\n"
                f"💰 Ставка: {crash_game.bet} ⭐\n"
                f"🎯 Цель: x{target:.2f}\n"
                f"📈 Текущий множитель: {multiplier:.2f}x\n\n"
                f"Множитель растет...",
                chat_id=user_id,
                message_id=message_id,
                parse_mode="Markdown"
            )
            await state.update_data(current_multiplier=multiplier)

# Игра Mines
@dp.message(F.text == "💣 Mines")
async def mines_start(message: Message, state: FSMContext):
    await state.set_state(GameStates.waiting_for_mines_bet)
    await message.answer(
        "💣 *Игра Mines*\n\n"
        "💰 Ставка: от 10 до 1000 ⭐\n"
        "💣 Количество мин: 1-6\n"
        "🎯 Множитель: до x25\n\n"
        "Введите сумму ставки:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )

@dp.message(GameStates.waiting_for_mines_bet)
async def mines_bet(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        bet = int(message.text)
        if bet < 10 or bet > 1000:
            await message.answer("❌ Ставка должна быть от 10 до 1000 ⭐")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    user = await get_user(message.from_user.id)
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "mines")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        await state.clear()
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await state.update_data(mines_bet=bet)
    await state.set_state(GameStates.waiting_for_mines_count)
    await message.answer("💣 Введите количество мин (1-6):")

@dp.message(GameStates.waiting_for_mines_count)
async def mines_count(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        mines_count = int(message.text)
        if mines_count < 1 or mines_count > 6:
            await message.answer("❌ Количество мин должно быть от 1 до 6!")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    bet = data.get("mines_bet")
    user = await get_user(message.from_user.id)
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Mines")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    mines_game = MinesGame(message.from_user.id, bet, mines_count)
    await state.update_data(mines_game=mines_game)
    await state.set_state(MinesStates.playing)
    
    await message.answer(
        f"💣 *Mines Game*\n\n"
        f"💰 Ставка: {bet} ⭐\n"
        f"💣 Мин на поле: {mines_count}\n"
        f"📈 Текущий множитель: 1.00x\n"
        f"🎯 Потенциальный выигрыш: {bet} ⭐\n\n"
        f"🔍 Открывайте клетки и увеличивайте множитель!\n"
        f"⚠️ Наступите на мину - проиграете!",
        parse_mode="Markdown",
        reply_markup=get_mines_keyboard(mines_game)
    )

def get_mines_keyboard(mines_game: MinesGame) -> InlineKeyboardMarkup:
    buttons = []
    for i in range(5):
        row = []
        for j in range(5):
            cell = i * 5 + j
            if cell in mines_game.opened:
                if cell in mines_game.mines:
                    text = "💣"
                else:
                    text = "✅"
            else:
                text = "❓"
            row.append(InlineKeyboardButton(text=text, callback_data=f"mines_cell_{cell}"))
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="💰 Забрать выигрыш", callback_data="mines_cashout")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.callback_query(MinesStates.playing, F.data.startswith("mines_cell_"))
async def mines_open_cell(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mines_game = data.get("mines_game")
    
    if not mines_game or not mines_game.is_active:
        await callback.answer("Игра уже завершена!")
        return
    
    cell = int(callback.data.replace("mines_cell_", ""))
    
    success, is_safe, multiplier = await mines_game.open_cell(cell)
    
    if not success:
        await callback.answer("Эта клетка уже открыта!")
        return
    
    if not is_safe:
        game_hash = generate_game_hash("mines", mines_game.bet, "mine", callback.from_user.id)
        await save_game_hash(game_hash)
        
        await callback.message.edit_text(
            f"💣 *Mines Game*\n\n"
            f"💰 Ставка: {mines_game.bet} ⭐\n"
            f"💥 Вы наступили на мину!\n"
            f"😔 Вы проиграли {mines_game.bet} ⭐",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
        await update_user_limits(callback.from_user.id, mines_game.bet, is_loss=True)
        await state.clear()
        await callback.answer("💥 Вы наступили на мину!")
        return
    
    potential = int(mines_game.bet * mines_game.current_multiplier)
    await callback.message.edit_text(
        f"💣 *Mines Game*\n\n"
        f"💰 Ставка: {mines_game.bet} ⭐\n"
        f"💣 Мин на поле: {mines_game.mines_count}\n"
        f"📈 Текущий множитель: {mines_game.current_multiplier:.2f}x\n"
        f"🎯 Потенциальный выигрыш: {potential} ⭐\n\n"
        f"🔍 Открывайте клетки и увеличивайте множитель!\n"
        f"⚠️ Наступите на мину - проиграете!",
        parse_mode="Markdown",
        reply_markup=get_mines_keyboard(mines_game)
    )
    await callback.answer("✅ Клетка открыта!")

@dp.callback_query(MinesStates.playing, F.data == "mines_cashout")
async def mines_cashout(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mines_game = data.get("mines_game")
    
    if not mines_game or not mines_game.is_active:
        await callback.answer("Игра уже завершена!")
        return
    
    winnings = await mines_game.cashout()
    
    if winnings > 0:
        game_hash = generate_game_hash("mines", mines_game.bet, winnings, callback.from_user.id)
        await save_game_hash(game_hash)
        
        await callback.message.edit_text(
            f"💣 *Mines Game*\n\n"
            f"💰 Ставка: {mines_game.bet} ⭐\n"
            f"📈 Итоговый множитель: {mines_game.current_multiplier:.2f}x\n"
            f"🎉 Вы выиграли {winnings} ⭐!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    else:
        await callback.answer("Ошибка!")
    
    await state.clear()
    await callback.answer()

# Игра Алмаз
@dp.message(F.text == "🤩 Алмаз")
async def diamond_start(message: Message, state: FSMContext):
    await state.set_state(GameStates.waiting_for_diamond_bet)
    await message.answer(
        "🤩 *Игра Алмаз*\n\n"
        "💰 Ставка: от 5 до 2000 ⭐\n"
        "🎯 Множитель: x2\n\n"
        "Введите сумму ставки:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )

@dp.message(GameStates.waiting_for_diamond_bet)
async def diamond_bet(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        bet = int(message.text)
        if bet < 5 or bet > 2000:
            await message.answer("❌ Ставка должна быть от 5 до 2000 ⭐")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    user = await get_user(message.from_user.id)
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "diamond")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        await state.clear()
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await state.update_data(diamond_bet=bet)
    await state.set_state(GameStates.waiting_for_diamond_choice)
    
    buttons = [
        [InlineKeyboardButton(text="💎 Сундук 1", callback_data="diamond_1"),
         InlineKeyboardButton(text="💎 Сундук 2", callback_data="diamond_2")]
    ]
    await message.answer(f"💰 Ставка: {bet} ⭐\n\nВыберите сундук:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(GameStates.waiting_for_diamond_choice, F.data.startswith("diamond_"))
async def diamond_play(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bet = data.get("diamond_bet")
    choice = int(callback.data.replace("diamond_", ""))
    
    user = await get_user(callback.from_user.id)
    
    if user["stars"] < bet:
        await callback.answer("❌ Недостаточно звезд!", show_alert=True)
        await state.clear()
        return
    
    await remove_stars(callback.from_user.id, bet, "Ставка в Алмазе")
    await update_user(callback.from_user.id, games_played=user["games_played"] + 1)
    
    winnings, result_text, result = await play_diamond(bet, choice)
    game_hash = generate_game_hash("diamond", bet, result, callback.from_user.id)
    await save_game_hash(game_hash)
    
    if winnings > 0:
        await add_stars(callback.from_user.id, winnings, "Выигрыш в Алмазе")
        await update_user_limits(callback.from_user.id, winnings, is_win=True)
    else:
        await update_user_limits(callback.from_user.id, bet, is_loss=True)
    
    buttons = [[InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]]
    await callback.message.edit_text(
        f"🤩 *Алмаз*\n\n{result_text}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.clear()
    await callback.answer()

# Игра 21 очко
@dp.message(F.text == "♠️ 21 очко")
async def blackjack_start(message: Message, state: FSMContext):
    await state.set_state(GameStates.waiting_for_blackjack_bet)
    await message.answer(
        "♠️ *Игра 21 очко (Blackjack)*\n\n"
        "💰 Ставка: от 10 до 1000 ⭐\n"
        "🎯 Множитель: x2.1\n\n"
        "Введите сумму ставки:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )

@dp.message(GameStates.waiting_for_blackjack_bet)
async def blackjack_bet(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        bet = int(message.text)
        if bet < 10 or bet > 1000:
            await message.answer("❌ Ставка должна быть от 10 до 1000 ⭐")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    user = await get_user(message.from_user.id)
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "21")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        await state.clear()
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в 21 очко")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    game = BlackjackGame(message.from_user.id, bet)
    await game.start_game()
    await state.update_data(blackjack_game=game)
    await state.set_state(BlackjackStates.playing)
    
    await message.answer(
        f"♠️ *21 очко (Blackjack)*\n\n"
        f"💰 Ставка: {bet} ⭐\n\n"
        f"🃏 *Ваши карты:* {', '.join(game.player_hand)}\n"
        f"📊 Ваши очки: {game.player_score}\n\n"
        f"🎴 *Карты дилера:* {game.dealer_hand[0]}, ?\n\n"
        f"Выберите действие:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎴 Взять карту", callback_data="bj_hit"),
             InlineKeyboardButton(text="✋ Хватит", callback_data="bj_stand")]
        ])
    )

@dp.callback_query(BlackjackStates.playing, F.data == "bj_hit")
async def blackjack_hit(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    game = data.get("blackjack_game")
    
    if not game or not game.is_active:
        await callback.answer("Игра уже завершена!")
        return
    
    success, score, bust = await game.player_hit()
    
    if bust:
        await callback.message.edit_text(
            f"♠️ *21 очко (Blackjack)*\n\n"
            f"💰 Ставка: {game.bet} ⭐\n\n"
            f"🃏 *Ваши карты:* {', '.join(game.player_hand)}\n"
            f"📊 Ваши очки: {score}\n\n"
            f"😔 Перебор! Вы проиграли {game.bet} ⭐",
            parse_mode="Markdown"
        )
        await state.clear()
        await callback.answer()
        return
    
    await callback.message.edit_text(
        f"♠️ *21 очко (Blackjack)*\n\n"
        f"💰 Ставка: {game.bet} ⭐\n\n"
        f"🃏 *Ваши карты:* {', '.join(game.player_hand)}\n"
        f"📊 Ваши очки: {score}\n\n"
        f"🎴 *Карты дилера:* {game.dealer_hand[0]}, ?\n\n"
        f"Выберите действие:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎴 Взять карту", callback_data="bj_hit"),
             InlineKeyboardButton(text="✋ Хватит", callback_data="bj_stand")]
        ])
    )
    await callback.answer()

@dp.callback_query(BlackjackStates.playing, F.data == "bj_stand")
async def blackjack_stand(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    game = data.get("blackjack_game")
    
    if not game:
        await callback.answer("Игра уже завершена!")
        return
    
    winnings, player_score, win = await game.player_stand()
    game_hash = generate_game_hash("21", game.bet, winnings, callback.from_user.id)
    await save_game_hash(game_hash)
    
    if winnings > game.bet:
        result_text = f"🎉 Вы выиграли {winnings} ⭐!"
    elif winnings == game.bet:
        result_text = f"🤝 Ничья! Возвращено {winnings} ⭐"
    else:
        result_text = f"😔 Вы проиграли {game.bet} ⭐"
    
    await callback.message.edit_text(
        f"♠️ *21 очко (Blackjack)*\n\n"
        f"💰 Ставка: {game.bet} ⭐\n\n"
        f"🃏 *Ваши карты:* {', '.join(game.player_hand)}\n"
        f"📊 Ваши очки: {player_score}\n\n"
        f"🎴 *Карты дилера:* {', '.join(game.dealer_hand)}\n"
        f"📊 Очки дилера: {game.dealer_score}\n\n"
        f"{result_text}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
        ])
    )
    await state.clear()
    await callback.answer()

# Игра Фортуна
@dp.message(F.text == "🔮 Фортуна")
async def fortune_start(message: Message, state: FSMContext):
    await state.set_state(GameStates.waiting_for_fortune_bet)
    await message.answer(
        "🔮 *Игра Фортуна*\n\n"
        "💰 Ставка: от 5 до 1000 ⭐\n"
        "🎯 Множитель: от x0 до x50\n\n"
        "Введите сумму ставки:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )

@dp.message(GameStates.waiting_for_fortune_bet)
async def fortune_bet(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        bet = int(message.text)
        if bet < 5 or bet > 1000:
            await message.answer("❌ Ставка должна быть от 5 до 1000 ⭐")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    user = await get_user(message.from_user.id)
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "fortune")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        await state.clear()
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Фортуне")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    winnings, result_text = await play_fortune(bet)
    game_hash = generate_game_hash("fortune", bet, winnings, message.from_user.id)
    await save_game_hash(game_hash)
    
    if winnings > 0:
        await add_stars(message.from_user.id, winnings, "Выигрыш в Фортуне")
        await update_user_limits(message.from_user.id, winnings, is_win=True)
    else:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
    
    await message.answer(
        f"🔮 *Фортуна*\n\n{result_text}\n\n💰 Выигрыш: {winnings} ⭐",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
        ])
    )
    await state.clear()

# Игра КНБ
@dp.message(F.text == "✂️ КНБ")
async def knb_start(message: Message, state: FSMContext):
    await state.set_state(GameStates.waiting_for_knb_bet)
    await message.answer(
        "✂️ *Игра Камень, Ножницы, Бумага*\n\n"
        "💰 Ставка: от 5 до 1000 ⭐\n"
        "🎯 Множитель: x2.7\n\n"
        "Введите сумму ставки:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )

@dp.message(GameStates.waiting_for_knb_bet)
async def knb_bet(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        bet = int(message.text)
        if bet < 5 or bet > 1000:
            await message.answer("❌ Ставка должна быть от 5 до 1000 ⭐")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    user = await get_user(message.from_user.id)
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "knb")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        await state.clear()
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await state.update_data(knb_bet=bet)
    await state.set_state(GameStates.waiting_for_knb_choice)
    
    buttons = [
        [InlineKeyboardButton(text="🪨 Камень", callback_data="knb_камень"),
         InlineKeyboardButton(text="✂️ Ножницы", callback_data="knb_ножницы"),
         InlineKeyboardButton(text="📄 Бумага", callback_data="knb_бумага")]
    ]
    await message.answer(f"💰 Ставка: {bet} ⭐\n\nВыберите:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(GameStates.waiting_for_knb_choice, F.data.startswith("knb_"))
async def knb_play(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bet = data.get("knb_bet")
    choice = callback.data.replace("knb_", "")
    
    user = await get_user(callback.from_user.id)
    
    if user["stars"] < bet:
        await callback.answer("❌ Недостаточно звезд!", show_alert=True)
        await state.clear()
        return
    
    await remove_stars(callback.from_user.id, bet, "Ставка в КНБ")
    await update_user(callback.from_user.id, games_played=user["games_played"] + 1)
    
    is_win, result_text, bot_choice = await play_knb(choice)
    game_hash = generate_game_hash("knb", bet, bot_choice, callback.from_user.id)
    await save_game_hash(game_hash)
    
    if is_win:
        winnings = int(bet * 2.7)
        await add_stars(callback.from_user.id, winnings, "Выигрыш в КНБ")
        await update_user_limits(callback.from_user.id, winnings, is_win=True)
        await callback.message.edit_text(
            f"✂️ *КНБ*\n\n{result_text}\n\n🎉 Вы выиграли {winnings} ⭐!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    else:
        await update_user_limits(callback.from_user.id, bet, is_loss=True)
        await callback.message.edit_text(
            f"✂️ *КНБ*\n\n{result_text}\n\n😔 Вы проиграли {bet} ⭐",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    
    await state.clear()
    await callback.answer()

# Игра Покер
@dp.message(F.text == "🃏 Покер")
async def poker_start(message: Message, state: FSMContext):
    await state.set_state(GameStates.waiting_for_poker_bet)
    await message.answer(
        "🃏 *Игра Покер*\n\n"
        "💰 Ставка: от 10 до 1000 ⭐\n"
        "🎯 Множитель: от x0 до x100\n\n"
        "Введите сумму ставки:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )

@dp.message(GameStates.waiting_for_poker_bet)
async def poker_bet(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        bet = int(message.text)
        if bet < 10 or bet > 1000:
            await message.answer("❌ Ставка должна быть от 10 до 1000 ⭐")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    user = await get_user(message.from_user.id)
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "poker")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        await state.clear()
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Покер")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    winnings, result_text = await play_poker(bet)
    game_hash = generate_game_hash("poker", bet, winnings, message.from_user.id)
    await save_game_hash(game_hash)
    
    if winnings > 0:
        await add_stars(message.from_user.id, winnings, "Выигрыш в Покере")
        await update_user_limits(message.from_user.id, winnings, is_win=True)
    else:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
    
    await message.answer(
        f"🃏 *Покер*\n\n{result_text}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
        ])
    )
    await state.clear()

# Игра Кено
@dp.message(F.text == "🎯 Кено")
async def keno_start(message: Message, state: FSMContext):
    await state.set_state(GameStates.waiting_for_keno_bet)
    await message.answer(
        "🎯 *Игра Кено*\n\n"
        "💰 Ставка: от 10 до 1000 ⭐\n"
        "🎯 Множитель: до x20\n"
        "🎲 Выберите 5 чисел от 1 до 80\n\n"
        "Введите сумму ставки:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )

@dp.message(GameStates.waiting_for_keno_bet)
async def keno_bet(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        bet = int(message.text)
        if bet < 10 or bet > 1000:
            await message.answer("❌ Ставка должна быть от 10 до 1000 ⭐")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    user = await get_user(message.from_user.id)
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "keno")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        await state.clear()
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await state.update_data(keno_bet=bet)
    await state.set_state(GameStates.waiting_for_keno_numbers)
    await message.answer("🔢 Введите 5 чисел через пробел (от 1 до 80):\nПример: 5 12 23 34 45")

@dp.message(GameStates.waiting_for_keno_numbers)
async def keno_numbers(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        numbers = [int(x) for x in message.text.split()]
        if len(numbers) != 5:
            await message.answer("❌ Нужно ввести ровно 5 чисел!")
            return
        for n in numbers:
            if n < 1 or n > 80:
                await message.answer("❌ Числа должны быть от 1 до 80!")
                return
    except ValueError:
        await message.answer("❌ Введите числа!")
        return
    
    data = await state.get_data()
    bet = data.get("keno_bet")
    user = await get_user(message.from_user.id)
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Кено")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    winnings, result_text, drawn = await play_keno(bet, numbers)
    game_hash = generate_game_hash("keno", bet, drawn, message.from_user.id)
    await save_game_hash(game_hash)
    
    if winnings > 0:
        await add_stars(message.from_user.id, winnings, "Выигрыш в Кено")
        await update_user_limits(message.from_user.id, winnings, is_win=True)
    else:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
    
    await message.answer(
        f"🎯 *Кено*\n\n{result_text}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
        ])
    )
    await state.clear()

# Игра Колесо Фортуны
@dp.message(F.text == "🎰 Колесо")
async def wheel_start(message: Message, state: FSMContext):
    await state.set_state(GameStates.waiting_for_wheel_bet)
    await message.answer(
        "🎰 *Колесо Фортуны*\n\n"
        "💰 Ставка: от 5 до 1000 ⭐\n"
        "🎯 Множитель: от x0 до x10\n\n"
        "Введите сумму ставки:\nДля отмены отправьте /cancel",
        parse_mode="Markdown"
    )

@dp.message(GameStates.waiting_for_wheel_bet)
async def wheel_bet(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Игра отменена!")
        return
    
    try:
        bet = int(message.text)
        if bet < 5 or bet > 1000:
            await message.answer("❌ Ставка должна быть от 5 до 1000 ⭐")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    user = await get_user(message.from_user.id)
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "wheel")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        await state.clear()
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        await state.clear()
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Колесе Фортуны")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    winnings, result_text = await play_wheel(bet)
    game_hash = generate_game_hash("wheel", bet, winnings, message.from_user.id)
    await save_game_hash(game_hash)
    
    if winnings > 0:
        await add_stars(message.from_user.id, winnings, "Выигрыш в Колесе Фортуны")
        await update_user_limits(message.from_user.id, winnings, is_win=True)
    else:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
    
    await message.answer(
        f"🎰 *Колесо Фортуны*\n\n{result_text}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
        ])
    )
    await state.clear()

# Проверка честности
@dp.callback_query(F.data.startswith("verify_hash_"))
async def verify_game_hash(callback: CallbackQuery):
    game_hash = callback.data.replace("verify_hash_", "")
    
    hashes = await load_json(GAME_HASHES_FILE, {"games": []})
    game_data = None
    for game in hashes["games"]:
        if game["hash"] == game_hash:
            game_data = game
            break
    
    if not game_data:
        await callback.answer("❌ Данные не найдены!", show_alert=True)
        return
    
    text = (f"🔍 *Проверка честности игры*\n\n"
            f"🎮 Игра: {game_data['game']}\n"
            f"💰 Ставка: {game_data['bet']} ⭐\n"
            f"📊 Результат: {game_data['result']}\n"
            f"🕒 Время: {game_data['timestamp'][:19]}\n\n"
            f"🔐 *Техническая информация:*\n"
            f"```\n"
            f"Seed: {game_data['seed']}\n"
            f"Hash: {game_data['hash']}\n"
            f"```\n\n"
            f"✅ Этот хеш гарантирует честность игры. Вы можете проверить его в любом SHA256 генераторе.")
    
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

# ============== АДМИН ПАНЕЛЬ ==============

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав!")
        return
    
    buttons = [
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
         InlineKeyboardButton(text="💰 Звезды", callback_data="admin_stars")],
        [InlineKeyboardButton(text="📋 Задания", callback_data="admin_tasks"),
         InlineKeyboardButton(text="🎫 Промокоды", callback_data="admin_promo")],
        [InlineKeyboardButton(text="📦 Чеки", callback_data="admin_checks"),
         InlineKeyboardButton(text="💰 Выводы", callback_data="admin_withdrawals")],
        [InlineKeyboardButton(text="⛔ Бан выводов", callback_data="admin_withdraw_bans"),
         InlineKeyboardButton(text="💬 Поддержка", callback_data="admin_support")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_mailing"),
         InlineKeyboardButton(text="📝 Логи", callback_data="admin_logs")]
    ]
    await message.answer("⚙️ *Админ панель*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data == "admin_users")
async def admin_users_menu(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    buttons = [
        [InlineKeyboardButton(text="🔍 По ID", callback_data="admin_find_user_id")],
        [InlineKeyboardButton(text="🔍 По @username", callback_data="admin_find_user_tg")],
        [InlineKeyboardButton(text="📊 Топ пользователей", callback_data="admin_top_users")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ]
    await callback.message.edit_text("👥 *Управление пользователями*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_find_user_id")
async def admin_find_user_id(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_user_id)
    await callback.message.edit_text("🔍 Введите ID пользователя:\nДля отмены отправьте /cancel", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_find_user_tg")
async def admin_find_user_tg(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_user_tg)
    await callback.message.edit_text("🔍 Введите @username пользователя (без @):\nДля отмены отправьте /cancel", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_user_id)
async def admin_show_user_by_id(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await admin_users_menu(message, state)
        return
    
    try:
        user_id = int(message.text.strip())
        user = await get_user(user_id)
        await show_user_info(message, user_id, user)
    except Exception as e:
        await message.answer(f"❌ Пользователь не найден!")
    await state.clear()

@dp.message(AdminStates.waiting_for_user_tg)
async def admin_show_user_by_tg(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await admin_users_menu(message, state)
        return
    
    username = message.text.strip().lstrip('@')
    user_data = await get_user_by_username(username)
    
    if not user_data:
        await message.answer(f"❌ Пользователь @{username} не найден!")
        await state.clear()
        return
    
    user_id = user_data["user_id"]
    user = user_data["data"]
    
    await show_user_info(message, user_id, user)
    await state.clear()

async def show_user_info(message: Message, user_id: int, user: dict):
    text = (f"👤 *Пользователь {user_id}*\n"
            f"👤 @{user.get('username', user_id)}\n\n"
            f"⭐ Баланс: {user['stars']}\n"
            f"💰 Заработано: {user['total_earned']}\n"
            f"💸 Потрачено: {user['total_spent']}\n"
            f"👥 Рефералов: {user['referral_count']}\n"
            f"🎮 Игр: {user['games_played']}\n"
            f"🏆 Побед: {user['games_won']}\n"
            f"😭 Поражений: {user['games_lost']}\n"
            f"📅 Дневные потери: {user['daily_loss']} ⭐\n"
            f"📈 Дневные выигрыши: {user['daily_win']} ⭐\n"
            f"📊 Проигрышей подряд: {user['consecutive_losses']}\n"
            f"⛔ Бан вывода: {'Да' if user.get('is_withdraw_banned', False) else 'Нет'}\n"
            f"📦 Чек система: {'✅' if user.get('check_system_unlocked', False) else '❌'}\n"
            f"📅 Регистрация: {user['created_at'][:10]}")
    
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить ⭐", callback_data=f"admin_add_stars_{user_id}"),
         InlineKeyboardButton(text="➖ Забрать ⭐", callback_data=f"admin_remove_stars_{user_id}")],
        [InlineKeyboardButton(text="🔓 Разблокировать чеки", callback_data=f"admin_unlock_checks_{user_id}")],
        [InlineKeyboardButton(text="⛔ Забанить вывод", callback_data=f"admin_ban_withdraw_{user_id}"),
         InlineKeyboardButton(text="✅ Разбанить вывод", callback_data=f"admin_unban_withdraw_{user_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
    ]
    await message.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("admin_add_stars_"))
async def admin_add_stars_amount(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.replace("admin_add_stars_", ""))
    await state.update_data(target_user=user_id, action="add")
    await state.set_state(AdminStates.waiting_for_stars_amount)
    await callback.message.edit_text("💰 Введите количество звезд для начисления:\nДля отмены отправьте /cancel", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_users")]
    ]))
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_remove_stars_"))
async def admin_remove_stars_amount(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.replace("admin_remove_stars_", ""))
    await state.update_data(target_user=user_id, action="remove")
    await state.set_state(AdminStates.waiting_for_stars_amount)
    await callback.message.edit_text("💰 Введите количество звезд для списания:\nДля отмены отправьте /cancel", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_users")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_stars_amount)
async def admin_process_stars(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await admin_users_menu(message, state)
        return
    
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    user_id = data["target_user"]
    
    if data["action"] == "add":
        await add_stars(user_id, amount, f"Админ {message.from_user.id} добавил звезды")
        await message.answer(f"✅ Пользователю добавлено {amount} ⭐")
        await log_admin_action(message.from_user.id, "add_stars", str(user_id), f"Amount: {amount}")
    else:
        success = await remove_stars(user_id, amount, f"Админ {message.from_user.id} забрал звезды")
        if success:
            await message.answer(f"✅ У пользователя списано {amount} ⭐")
            await log_admin_action(message.from_user.id, "remove_stars", str(user_id), f"Amount: {amount}")
        else:
            await message.answer(f"❌ У пользователя недостаточно звезд!")
    
    await state.clear()

@dp.callback_query(F.data.startswith("admin_unlock_checks_"))
async def admin_unlock_checks(callback: CallbackQuery):
    user_id = int(callback.data.replace("admin_unlock_checks_", ""))
    await update_user(user_id, check_system_unlocked=True)
    await callback.answer("✅ Система чеков разблокирована!", show_alert=True)
    await admin_users_menu(callback, None)

@dp.callback_query(F.data.startswith("admin_ban_withdraw_"))
async def admin_ban_withdraw(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.replace("admin_ban_withdraw_", ""))
    await state.update_data(target_user=user_id)
    await state.set_state(AdminStates.waiting_for_ban_hours)
    await callback.message.edit_text("⏰ Введите количество часов бана вывода:\nДля отмены отправьте /cancel", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_users")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_ban_hours)
async def admin_process_ban(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await admin_users_menu(message, state)
        return
    
    try:
        hours = int(message.text.strip())
        data = await state.get_data()
        user_id = data["target_user"]
        
        ban_until = datetime.now() + timedelta(hours=hours)
        await update_user(user_id, 
                          is_withdraw_banned=True, 
                          withdraw_ban_reason=f"Администратор {message.from_user.id}", 
                          withdraw_ban_until=ban_until.isoformat())
        await message.answer(f"✅ Пользователь забанен на вывод на {hours} часов!")
        await log_admin_action(message.from_user.id, "ban_withdraw", str(user_id), f"Hours: {hours}")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data.startswith("admin_unban_withdraw_"))
async def admin_unban_withdraw(callback: CallbackQuery):
    user_id = int(callback.data.replace("admin_unban_withdraw_", ""))
    await update_user(user_id, is_withdraw_banned=False, withdraw_ban_reason=None, withdraw_ban_until=None)
    await callback.answer("✅ Бан вывода снят!", show_alert=True)
    await admin_users_menu(callback, None)

@dp.callback_query(F.data == "admin_top_users")
async def admin_top_users(callback: CallbackQuery):
    users = await load_json(USERS_FILE, {})
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("stars", 0), reverse=True)[:10]
    
    text = "🏆 *Топ пользователей по балансу:*\n\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        username = data.get("username", uid)
        text += f"{i}. @{username} - {data.get('stars', 0)} ⭐\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_stars")
async def admin_stars_menu(callback: CallbackQuery):
    users = await load_json(USERS_FILE, {})
    total_stars = sum(u.get("stars", 0) for u in users.values())
    
    text = f"💰 *Управление звездами*\n\nВсего звезд в системе: {total_stars}\nВсего пользователей: {len(users)}\n\nВыберите действие:"
    
    buttons = [
        [InlineKeyboardButton(text="💸 Массовая выдача", callback_data="admin_mass_add")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_mass_add")
async def admin_mass_add(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_stars_amount)
    await state.update_data(action="mass_add")
    await callback.message.edit_text("💰 Введите количество звезд для ВСЕХ пользователей:\nДля отмены отправьте /cancel", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_stars")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_tasks")
async def admin_tasks_menu(callback: CallbackQuery):
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить задание", callback_data="admin_add_task")],
        [InlineKeyboardButton(text="📋 Список заданий", callback_data="admin_list_tasks")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ]
    await callback.message.edit_text("📋 *Управление заданиями*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_add_task")
async def admin_add_task(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_task_name)
    await callback.message.edit_text("📝 Введите название задания:\nДля отмены отправьте /cancel", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_tasks")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_task_name)
async def admin_task_name(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await admin_tasks_menu(message)
        return
    
    await state.update_data(task_name=message.text)
    await state.set_state(AdminStates.waiting_for_task_link)
    await message.answer("🔗 Введите ссылку на канал (например, https://t.me/channel):\n\n⚠️ Бот должен быть добавлен в этот канал администратором!\nДля отмены отправьте /cancel")

@dp.message(AdminStates.waiting_for_task_link)
async def admin_task_link(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await admin_tasks_menu(message)
        return
    
    await state.update_data(task_link=message.text)
    await state.set_state(AdminStates.waiting_for_task_reward)
    await message.answer("💰 Введите награду (звезды):\nДля отмены отправьте /cancel")

@dp.message(AdminStates.waiting_for_task_reward)
async def admin_task_reward(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await admin_tasks_menu(message)
        return
    
    try:
        reward = int(message.text)
        data = await state.get_data()
        
        task_id = await add_task(message.from_user.id, data["task_name"], data["task_link"], reward)
        await message.answer(f"✅ Задание добавлено!\n\n📝 Название: {data['task_name']}\n🔗 Ссылка: {data['task_link']}\n💰 Награда: {reward} ⭐")
        await log_admin_action(message.from_user.id, "add_task", None, f"Name: {data['task_name']}, Reward: {reward}")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "admin_list_tasks")
async def admin_list_tasks(callback: CallbackQuery):
    tasks = await get_all_tasks()
    
    if not tasks:
        text = "📋 *Список заданий*\n\nНет активных заданий."
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_tasks")]]
    else:
        text = "📋 *Список заданий:*\n\n"
        buttons = []
        for task in tasks:
            text += f"*ID {task['id']}:* {task['name']}\n└ Награда: {task['reward']} ⭐\n└ Ссылка: {task['link']}\n\n"
            buttons.append([InlineKeyboardButton(text=f"❌ Удалить {task['name']}", callback_data=f"admin_delete_task_{task['id']}")])
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_tasks")])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_delete_task_"))
async def admin_delete_task(callback: CallbackQuery):
    task_id = int(callback.data.replace("admin_delete_task_", ""))
    success = await delete_task(task_id)
    await callback.answer("✅ Задание удалено!" if success else "❌ Ошибка!")
    await admin_list_tasks(callback)

@dp.callback_query(F.data == "admin_promo")
async def admin_promo_menu(callback: CallbackQuery):
    buttons = [
        [InlineKeyboardButton(text="➕ Создать промокод", callback_data="admin_create_promo")],
        [InlineKeyboardButton(text="📋 Список промокодов", callback_data="admin_list_promo")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ]
    await callback.message.edit_text("🎫 *Управление промокодами*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_create_promo")
async def admin_create_promo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_promo_code)
    await callback.message.edit_text("🎫 Введите код промокода:\nДля отмены отправьте /cancel", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_promo")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_promo_code)
async def admin_promo_code(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await admin_promo_menu(message)
        return
    
    await state.update_data(promo_code=message.text.strip().upper())
    await state.set_state(AdminStates.waiting_for_promo_reward)
    await message.answer("💰 Введите награду (звезды):\nДля отмены отправьте /cancel")

@dp.message(AdminStates.waiting_for_promo_reward)
async def admin_promo_reward(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await admin_promo_menu(message)
        return
    
    try:
        reward = int(message.text)
        await state.update_data(promo_reward=reward)
        await state.set_state(AdminStates.waiting_for_promo_limit)
        await message.answer("📊 Введите лимит использований:\nДля отмены отправьте /cancel")
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(AdminStates.waiting_for_promo_limit)
async def admin_promo_limit(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await admin_promo_menu(message)
        return
    
    try:
        limit = int(message.text)
        data = await state.get_data()
        success = await create_promo(message.from_user.id, data["promo_code"], data["promo_reward"], limit)
        if success:
            await message.answer(f"✅ Промокод создан!\n\n🎫 Код: {data['promo_code']}\n💰 Награда: {data['promo_reward']} ⭐\n📊 Лимит: {limit}")
            await log_admin_action(message.from_user.id, "create_promo", None, f"Code: {data['promo_code']}, Reward: {data['promo_reward']}, Limit: {limit}")
        else:
            await message.answer("❌ Промокод с таким кодом уже существует!")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "admin_list_promo")
async def admin_list_promo(callback: CallbackQuery):
    promo = await load_json(PROMO_FILE, {"promo_codes": []})
    promo_codes = promo["promo_codes"]
    
    if not promo_codes:
        text = "🎫 *Список промокодов*\n\nНет активных промокодов."
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_promo")]]
    else:
        text = "🎫 *Список промокодов:*\n\n"
        buttons = []
        for p in promo_codes:
            text += f"*{p['code']}*\n└ Награда: {p['reward']} ⭐\n└ Использовано: {p['used']}/{p['limit']}\n\n"
            buttons.append([InlineKeyboardButton(text=f"❌ Удалить {p['code']}", callback_data=f"admin_delete_promo_{p['code']}")])
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_promo")])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_delete_promo_"))
async def admin_delete_promo(callback: CallbackQuery):
    code = callback.data.replace("admin_delete_promo_", "")
    promo = await load_json(PROMO_FILE, {"promo_codes": []})
    promo["promo_codes"] = [p for p in promo["promo_codes"] if p["code"] != code]
    await save_json(PROMO_FILE, promo)
    await callback.answer("✅ Промокод удален!")
    await admin_list_promo(callback)

@dp.callback_query(F.data == "admin_checks")
async def admin_checks_menu(callback: CallbackQuery):
    checks = await load_json(CHECKS_FILE, {"checks": [], "used_checks": []})
    active = len(checks["checks"])
    used = len(checks["used_checks"])
    
    text = f"📦 *Управление чеками*\n\n🟢 Активных чеков: {active}\n🔴 Использовано: {used}\n\nВыберите действие:"
    
    buttons = [
        [InlineKeyboardButton(text="➕ Создать чек", callback_data="admin_create_check")],
        [InlineKeyboardButton(text="📋 Список чеков", callback_data="admin_list_checks")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_create_check")
async def admin_create_check(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_check_amount)
    await callback.message.edit_text("📦 Введите сумму чека:\nДля отмены отправьте /cancel", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_checks")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_check_amount)
async def admin_create_check_amount(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await admin_checks_menu(message)
        return
    
    try:
        amount = int(message.text)
        checks = await load_json(CHECKS_FILE, {"checks": [], "used_checks": []})
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        
        check = {
            "code": code,
            "amount": amount,
            "creator": message.from_user.id,
            "created_at": datetime.now().isoformat(),
            "used": False,
            "used_by": None,
            "type": "admin"
        }
        checks["checks"].append(check)
        await save_json(CHECKS_FILE, checks)
        
        bot_username = (await bot.get_me()).username
        link = f"https://t.me/{bot_username}?start=check_{code}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Копировать ссылку", callback_data=f"copy_{link}")]
        ])
        
        await message.answer(f"✅ Чек создан!\n\n📦 Ссылка для активации: {link}\n💰 Сумма: {amount} ⭐", parse_mode="Markdown", reply_markup=keyboard)
        await log_admin_action(message.from_user.id, "create_check", None, f"Amount: {amount}")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "admin_list_checks")
async def admin_list_checks(callback: CallbackQuery):
    checks = await load_json(CHECKS_FILE, {"checks": [], "used_checks": []})
    
    text = "📦 *Список чеков*\n\n"
    
    if checks["checks"]:
        text += "*Активные чеки:*\n"
        for c in checks["checks"][:10]:
            text += f"└ Сумма: {c['amount']} ⭐\n"
    
    if checks["used_checks"]:
        text += "\n*Использованные чеки:*\n"
        for c in checks["used_checks"][-10:]:
            text += f"└ Сумма: {c['amount']} ⭐ (активировал: {c['used_by']})\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_checks")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_withdrawals")
async def admin_withdrawals_menu(callback: CallbackQuery):
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    pending = {k: v for k, v in withdrawals.items() if v["status"] == "pending"}
    
    if not pending:
        text = "💰 *Заявки на вывод*\n\nНет активных заявок."
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]
    else:
        text = f"💰 *Заявки на вывод*\n\nВсего заявок: {len(pending)}\n\n"
        buttons = []
        for wid, w in list(pending.items())[:10]:
            text += f"*ID {wid}:* @{w['username']}\n└ Сумма: {w['stars']} ⭐\n└ Дата: {w['created_at'][:19]}\n\n"
            buttons.append([
                InlineKeyboardButton(text=f"✅ Подтвердить {wid}", callback_data=f"admin_approve_{wid}"),
                InlineKeyboardButton(text=f"❌ Отклонить {wid}", callback_data=f"admin_decline_{wid}")
            ])
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_approve_"))
async def admin_approve_withdrawal(callback: CallbackQuery):
    wid = callback.data.replace("admin_approve_", "")
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    
    if wid in withdrawals and withdrawals[wid]["status"] == "pending":
        withdrawals[wid]["status"] = "approved"
        withdrawals[wid]["approved_at"] = datetime.now().isoformat()
        withdrawals[wid]["approved_by"] = callback.from_user.id
        await save_json(WITHDRAWALS_FILE, withdrawals)
        
        try:
            await bot.send_message(
                withdrawals[wid]["user_id"],
                f"✅ Ваша заявка на вывод #{wid} одобрена!\n⭐ Сумма: {withdrawals[wid]['stars']} ⭐",
                parse_mode="Markdown"
            )
        except:
            pass
        
        await callback.answer("✅ Заявка подтверждена!")
        await log_admin_action(callback.from_user.id, "approve_withdrawal", str(withdrawals[wid]["user_id"]), f"Amount: {withdrawals[wid]['stars']}")
    else:
        await callback.answer("❌ Ошибка!")
    
    await admin_withdrawals_menu(callback)

@dp.callback_query(F.data.startswith("admin_decline_"))
async def admin_decline_withdrawal(callback: CallbackQuery):
    wid = callback.data.replace("admin_decline_", "")
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    
    if wid in withdrawals and withdrawals[wid]["status"] == "pending":
        user_id = withdrawals[wid]["user_id"]
        amount = withdrawals[wid]["stars"]
        await add_stars(user_id, amount, "Возврат при отклонении вывода")
        
        withdrawals[wid]["status"] = "declined"
        withdrawals[wid]["declined_at"] = datetime.now().isoformat()
        withdrawals[wid]["declined_by"] = callback.from_user.id
        await save_json(WITHDRAWALS_FILE, withdrawals)
        
        try:
            await bot.send_message(
                user_id,
                f"❌ Ваша заявка на вывод #{wid} отклонена!\n⭐ Звезды возвращены на баланс.",
                parse_mode="Markdown"
            )
        except:
            pass
        
        await callback.answer("✅ Заявка отклонена!")
        await log_admin_action(callback.from_user.id, "decline_withdrawal", str(user_id), f"Amount: {amount}")
    else:
        await callback.answer("❌ Ошибка!")
    
    await admin_withdrawals_menu(callback)

@dp.callback_query(F.data == "admin_withdraw_bans")
async def admin_withdraw_bans_menu(callback: CallbackQuery):
    users = await load_json(USERS_FILE, {})
    banned_users = [(uid, u) for uid, u in users.items() if u.get("is_withdraw_banned", False)]
    
    if not banned_users:
        text = "⛔ *Забаненные на вывод пользователи*\n\nНет забаненных пользователей."
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]
    else:
        text = "⛔ *Забаненные на вывод пользователи:*\n\n"
        buttons = []
        for uid, u in banned_users[:10]:
            ban_until = u.get("withdraw_ban_until", "Неизвестно")
            if ban_until and ban_until != "Неизвестно":
                ban_until_date = datetime.fromisoformat(ban_until)
                ban_until_str = ban_until_date.strftime("%d.%m.%Y %H:%M")
            else:
                ban_until_str = "Неизвестно"
            text += f"*ID {uid}:* @{u.get('username', uid)} - {u.get('stars', 0)} ⭐\n└ Бан до: {ban_until_str}\n└ Причина: {u.get('withdraw_ban_reason', 'Не указана')}\n\n"
            buttons.append([InlineKeyboardButton(text=f"✅ Разбанить {uid}", callback_data=f"admin_unban_withdraw_{uid}")])
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_support")
async def admin_support_menu(callback: CallbackQuery):
    support = await load_json(SUPPORT_FILE, {"tickets": []})
    open_tickets = [t for t in support["tickets"] if t["status"] == "open"]
    
    if not open_tickets:
        text = "💬 *Тикеты поддержки*\n\nНет открытых тикетов."
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]
    else:
        text = f"💬 *Открытые тикеты:*\n\n"
        buttons = []
        for t in open_tickets:
            text += f"*#{t['id']}* от пользователя {t['user_id']}\n└ Создан: {t['created_at'][:19]}\n\n"
            buttons.append([InlineKeyboardButton(text=f"💬 Ответить в тикет #{t['id']}", callback_data=f"admin_reply_ticket_{t['id']}")])
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_reply_ticket_"))
async def admin_reply_ticket(callback: CallbackQuery, state: FSMContext):
    ticket_id = int(callback.data.replace("admin_reply_ticket_", ""))
    await state.update_data(ticket_id=ticket_id)
    await state.set_state(AdminStates.waiting_for_reply_message)
    await callback.message.edit_text(
        f"💬 *Ответ в тикет #{ticket_id}*\n\nВведите ваш ответ:\nДля отмены отправьте /cancel",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Закрыть тикет", callback_data=f"admin_close_ticket_{ticket_id}"),
             InlineKeyboardButton(text="🔙 Назад", callback_data="admin_support")]
        ])
    )
    await callback.answer()

@dp.message(AdminStates.waiting_for_reply_message)
async def admin_send_reply(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await admin_support_menu(message)
        return
    
    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    
    if ticket_id:
        success = await reply_to_ticket(message.from_user.id, ticket_id, message.text)
        if success:
            await message.answer(f"✅ Ответ отправлен в тикет #{ticket_id}!")
            await log_admin_action(message.from_user.id, "reply_ticket", None, f"Ticket: {ticket_id}")
        else:
            await message.answer(f"❌ Не удалось отправить ответ!")
    
    await state.clear()

@dp.callback_query(F.data.startswith("admin_close_ticket_"))
async def admin_close_ticket(callback: CallbackQuery):
    ticket_id = int(callback.data.replace("admin_close_ticket_", ""))
    success = await close_ticket(ticket_id)
    
    if success:
        await callback.answer("✅ Тикет закрыт!")
        await log_admin_action(callback.from_user.id, "close_ticket", None, f"Ticket: {ticket_id}")
    else:
        await callback.answer("❌ Ошибка!")
    
    await admin_support_menu(callback)

@dp.callback_query(F.data == "admin_settings")
async def admin_settings_menu(callback: CallbackQuery):
    settings = await load_json(SETTINGS_FILE, {})
    
    text = (f"⚙️ *Настройки бота*\n\n"
            f"⭐ Стартовый баланс: {settings.get('start_balance', 5)}\n"
            f"💰 Мин. вывод: {settings.get('min_withdraw', 500)}\n"
            f"👥 Реф. награда: {settings.get('referral_reward', 10)}\n"
            f"📊 Реф. процент: {settings.get('referral_percent', 10)}%\n"
            f"💱 Курс обмена: {settings.get('exchange_rate', 1)}:1\n"
            f"📦 Цена чек системы: {settings.get('check_system_price', 100)} ⭐\n\n"
            f"Выберите параметр для изменения:")
    
    buttons = [
        [InlineKeyboardButton(text="⭐ Стартовый баланс", callback_data="set_start_balance"),
         InlineKeyboardButton(text="💰 Мин. вывод", callback_data="set_min_withdraw")],
        [InlineKeyboardButton(text="👥 Реф. награда", callback_data="set_referral_reward"),
         InlineKeyboardButton(text="📊 Реф. процент", callback_data="set_referral_percent")],
        [InlineKeyboardButton(text="💱 Курс обмена", callback_data="set_exchange_rate"),
         InlineKeyboardButton(text="📦 Цена чек системы", callback_data="set_check_system_price")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("set_"))
async def admin_setting_change(callback: CallbackQuery, state: FSMContext):
    setting = callback.data.replace("set_", "")
    
    await state.update_data(setting=setting)
    await state.set_state(AdminStates.waiting_for_setting_value)
    
    names = {
        "start_balance": "стартовый баланс", "min_withdraw": "мин. вывод",
        "referral_reward": "реф. награду", "referral_percent": "реф. процент",
        "exchange_rate": "курс обмена", "check_system_price": "цену чек системы"
    }
    await callback.message.edit_text(f"📝 Введите {names.get(setting, setting)}:\nДля отмены отправьте /cancel", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_settings")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_setting_value)
async def admin_save_setting(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await admin_settings_menu(message)
        return
    
    try:
        value = int(message.text.strip())
        if value <= 0:
            await message.answer("❌ Значение должно быть больше 0!")
            return
        
        data = await state.get_data()
        settings = await load_json(SETTINGS_FILE, {})
        settings[data["setting"]] = value
        await save_json(SETTINGS_FILE, settings)
        await message.answer(f"✅ {data['setting']} = {value}")
        await log_admin_action(message.from_user.id, "change_setting", None, f"{data['setting']}: {value}")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    users = await load_json(USERS_FILE, {})
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    tasks = await get_all_tasks()
    promo = await load_json(PROMO_FILE, {"promo_codes": []})
    checks = await load_json(CHECKS_FILE, {"checks": [], "used_checks": []})
    support = await load_json(SUPPORT_FILE, {"tickets": []})
    
    total_stars = sum(u.get("stars", 0) for u in users.values())
    total_users = len(users)
    unlocked_checks = len([u for u in users.values() if u.get("check_system_unlocked", False)])
    pending_withdrawals = len([w for w in withdrawals.values() if w.get("status") == "pending"])
    open_tickets = len([t for t in support["tickets"] if t["status"] == "open"])
    banned_withdraw = len([u for u in users.values() if u.get("is_withdraw_banned", False)])
    total_games_played = sum(u.get("games_played", 0) for u in users.values())
    total_games_won = sum(u.get("games_won", 0) for u in users.values())
    
    text = (f"📊 *Общая статистика*\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"⭐ Всего звезд: {total_stars}\n"
            f"📦 Чек система: {unlocked_checks}/{total_users}\n"
            f"⛔ Забанены на вывод: {banned_withdraw}\n"
            f"📈 Средний баланс: {total_stars // total_users if total_users else 0}\n\n"
            f"🎮 Сыграно игр: {total_games_played}\n"
            f"🏆 Побед: {total_games_won}\n"
            f"📉 Процент побед: {round(total_games_won / total_games_played * 100, 1) if total_games_played else 0}%\n\n"
            f"📋 Заданий: {len(tasks)}\n"
            f"🎫 Промокодов: {len(promo['promo_codes'])}\n"
            f"📦 Активных чеков: {len(checks['checks'])}\n"
            f"💬 Открытых тикетов: {open_tickets}\n\n"
            f"💰 Ожидают вывода: {pending_withdrawals}")
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_mailing")
async def admin_mailing_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_mailing_message)
    await callback.message.edit_text(
        "📢 *Создание рассылки*\n\n"
        "Отправьте сообщение для рассылки всем пользователям.\n"
        "Поддерживается текст, фото, видео.\n\n"
        "⚠️ Рассылка будет отправлена всем пользователям бота!\n\n"
        "Для отмены нажмите кнопку:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_back")]
        ])
    )
    await callback.answer()

@dp.message(AdminStates.waiting_for_mailing_message)
async def admin_mailing_message(message: Message, state: FSMContext):
    message_type = "text"
    file_id = None
    text = message.text if message.text else message.caption
    
    if message.photo:
        message_type = "photo"
        file_id = message.photo[-1].file_id
        text = message.caption or "📸 Рассылка"
    elif message.video:
        message_type = "video"
        file_id = message.video.file_id
        text = message.caption or "🎥 Рассылка"
    
    await state.update_data(mailing_text=text, mailing_type=message_type, mailing_file_id=file_id)
    await state.set_state(AdminStates.waiting_for_mailing_confirm)
    
    preview_text = "📢 *Предпросмотр рассылки*\n\n" + text
    buttons = [
        [InlineKeyboardButton(text="✅ Отправить", callback_data="mailing_confirm"),
         InlineKeyboardButton(text="❌ Отмена", callback_data="mailing_cancel")]
    ]
    
    if message_type == "text":
        await message.answer(preview_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    elif message_type == "photo":
        await message.answer_photo(file_id, caption=preview_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    elif message_type == "video":
        await message.answer_video(file_id, caption=preview_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data == "mailing_confirm")
async def mailing_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    mailing_id = await create_mailing(
        callback.from_user.id,
        data.get("mailing_text", ""),
        data.get("mailing_type", "text"),
        data.get("mailing_file_id")
    )
    
    await callback.message.edit_text("📢 *Рассылка запущена!*\n\nОтправка сообщений всем пользователям...", parse_mode="Markdown")
    
    asyncio.create_task(start_mailing(mailing_id))
    await log_admin_action(callback.from_user.id, "start_mailing", None, f"Mailing ID: {mailing_id}")
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "mailing_cancel")
async def mailing_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Рассылка отменена!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_logs")
async def admin_logs(callback: CallbackQuery):
    logs = await load_json(ADMIN_LOGS_FILE, [])
    
    if not logs:
        text = "📝 *Логи действий*\n\nНет записей."
    else:
        text = "📝 *Последние действия:*\n\n"
        for log in logs[-20:]:
            text += f"🕒 {log['timestamp'][:19]}\n"
            text += f"👤 Админ: {log['admin_id']}\n"
            text += f"📌 {log['action']}\n"
            if log.get('target'):
                text += f"🎯 Цель: {log['target']}\n"
            if log.get('details'):
                text += f"📝 {log['details']}\n"
            text += "➖➖➖➖➖➖➖\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Очистить логи", callback_data="admin_clear_logs")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_clear_logs")
async def admin_clear_logs(callback: CallbackQuery):
    await save_json(ADMIN_LOGS_FILE, [])
    await callback.answer("✅ Логи очищены!", show_alert=True)
    await admin_logs(callback)

@dp.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    await admin_panel(callback.message)

# Запуск бота
async def main():
    await init_data()
    logger.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
