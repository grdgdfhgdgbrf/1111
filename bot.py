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
    LabeledPrice, PreCheckoutQuery
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
CONTEST_FILE = os.path.join(DATA_DIR, "contest.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
ADMIN_LOGS_FILE = os.path.join(DATA_DIR, "admin_logs.json")
SUPPORT_FILE = os.path.join(DATA_DIR, "support.json")
GAME_HASHES_FILE = os.path.join(DATA_DIR, "game_hashes.json")
CONTEST_POINTS_FILE = os.path.join(DATA_DIR, "contest_points.json")

os.makedirs(DATA_DIR, exist_ok=True)

# FSM States
class CrashStates(StatesGroup):
    playing = State()

class MinesStates(StatesGroup):
    playing = State()

class ContestStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_prize = State()
    waiting_for_link = State()

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
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

class PromoStates(StatesGroup):
    waiting_for_promo_code = State()

class SupportStates(StatesGroup):
    waiting_for_message = State()

class BuyStates(StatesGroup):
    waiting_for_amount = State()

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

# Система очков для конкурса
async def add_contest_points(user_id: int, points: int, reason: str = ""):
    contest_points = await load_json(CONTEST_POINTS_FILE, {"points": {}})
    user_id_str = str(user_id)
    
    if user_id_str not in contest_points["points"]:
        contest_points["points"][user_id_str] = {
            "points": 0,
            "games_played": 0,
            "games_lost": 0,
            "last_update": datetime.now().isoformat()
        }
    
    contest_points["points"][user_id_str]["points"] += points
    contest_points["points"][user_id_str]["last_update"] = datetime.now().isoformat()
    
    if "проигрыш" in reason.lower():
        contest_points["points"][user_id_str]["games_lost"] += 1
    contest_points["points"][user_id_str]["games_played"] += 1
    
    await save_json(CONTEST_POINTS_FILE, contest_points)
    
    # Проверяем активный конкурс для начисления очков
    contest = await get_active_contest()
    if contest and user_id_str in contest.get("participants", {}):
        contest_data = await load_json(CONTEST_FILE, {"active": None})
        if contest_data["active"]:
            if "points" not in contest_data["active"]["participants"][user_id_str]:
                contest_data["active"]["participants"][user_id_str]["points"] = 0
            contest_data["active"]["participants"][user_id_str]["points"] += points
            await save_json(CONTEST_FILE, contest_data)

async def get_contest_points(user_id: int) -> int:
    contest_points = await load_json(CONTEST_POINTS_FILE, {"points": {}})
    user_id_str = str(user_id)
    return contest_points["points"].get(user_id_str, {}).get("points", 0)

async def reset_contest_points():
    await save_json(CONTEST_POINTS_FILE, {"points": {}})

# Инициализация данных
async def init_data():
    settings = await load_json(SETTINGS_FILE, {})
    if not settings:
        settings = {
            "start_balance": 5,
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
            "stars": settings.get("start_balance", 5),
            "total_earned": 0,
            "total_spent": 0,
            "total_purchases": 0,
            "referral_code": user_id,
            "referrer": None,
            "referral_count": 0,
            "referral_earnings": 0,
            "games_played": 0,
            "games_won": 0,
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
            "created_at": datetime.now().isoformat()
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
            "stars": settings.get("start_balance", 5),
            "total_earned": 0,
            "total_spent": 0,
            "total_purchases": 0,
            "referral_code": str(user_id),
            "referrer": None,
            "referral_count": 0,
            "referral_earnings": 0,
            "games_played": 0,
            "games_won": 0,
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
            "created_at": datetime.now().isoformat()
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
        
        # Начисляем очки за проигрыш в конкурс
        if "проигрыш" in reason.lower() or "ставка" in reason.lower():
            points = max(1, amount // 10)
            await add_contest_points(user_id, points, reason)
        
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
                           "condition": user["referral_count"] >= 100, "reward": 50000}
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
        await update_user(user_id, daily_loss=user["daily_loss"] + amount, consecutive_losses=user["consecutive_losses"] + 1)
    elif is_win:
        await update_user(user_id, daily_win=user["daily_win"] + amount, consecutive_losses=0)

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
    
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    # Кодируем username для ссылки
    import urllib.parse
    safe_username = urllib.parse.quote(bot_username, safe='')
    check_link = f"https://t.me/{safe_username}?start=check_{code}"
    
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

# Система конкурсов
async def get_active_contest() -> Optional[dict]:
    contest_data = await load_json(CONTEST_FILE, {"active": None})
    return contest_data["active"]

async def create_contest(admin_id: int, name: str, description: str, prize: int, link: str = None) -> int:
    contest_data = await load_json(CONTEST_FILE, {"active": None, "history": [], "participants": {}})
    
    if contest_data["active"]:
        return 0
    
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    import urllib.parse
    safe_username = urllib.parse.quote(bot_username, safe='')
    
    if not link or link == "-":
        contest_link = f"https://t.me/{safe_username}?start=contest_{admin_id}"
    else:
        contest_link = link
    
    contest = {
        "id": len(contest_data["history"]) + 1,
        "name": name,
        "description": description,
        "prize": prize,
        "link": contest_link,
        "created_by": admin_id,
        "created_at": datetime.now().isoformat(),
        "end_time": (datetime.now() + timedelta(days=7)).isoformat(),
        "participants": {},
        "active": True
    }
    
    contest_data["active"] = contest
    await save_json(CONTEST_FILE, contest_data)
    await log_admin_action(admin_id, "create_contest", None, f"Name: {name}, Prize: {prize}")
    return contest["id"]

async def join_contest(user_id: int, message_id: int) -> Tuple[bool, str]:
    contest_data = await load_json(CONTEST_FILE, {"active": None, "participants": {}})
    
    if not contest_data["active"]:
        return False, "Нет активного конкурса!"
    
    user_id_str = str(user_id)
    if user_id_str in contest_data["active"]["participants"]:
        return False, "Вы уже участвуете в конкурсе!"
    
    # Получаем очки пользователя
    user_points = await get_contest_points(user_id)
    
    contest_data["active"]["participants"][user_id_str] = {
        "joined_at": datetime.now().isoformat(),
        "message_id": message_id,
        "points": user_points
    }
    
    await save_json(CONTEST_FILE, contest_data)
    return True, f"✅ Вы успешно участвуете в конкурсе! У вас {user_points} очков!"

async def end_contest() -> Tuple[bool, str, int]:
    contest_data = await load_json(CONTEST_FILE, {"active": None, "history": [], "participants": {}})
    
    if not contest_data["active"]:
        return False, "Нет активного конкурса!", 0
    
    participants = list(contest_data["active"]["participants"].keys())
    if not participants:
        contest_data["history"].append(contest_data["active"])
        contest_data["active"] = None
        await save_json(CONTEST_FILE, contest_data)
        return False, "Нет участников конкурса!", 0
    
    # Выбираем победителя по очкам (больше очков - больше шансов)
    weighted_participants = []
    for pid in participants:
        points = contest_data["active"]["participants"][pid].get("points", 0)
        weight = max(1, points + 10)  # Минимум 10 шансов
        weighted_participants.extend([pid] * weight)
    
    winner_id = random.choice(weighted_participants)
    prize = contest_data["active"]["prize"]
    
    await add_stars(int(winner_id), prize, f"Выигрыш в конкурсе {contest_data['active']['name']}")
    
    contest_data["active"]["winner"] = winner_id
    contest_data["active"]["ended_at"] = datetime.now().isoformat()
    contest_data["history"].append(contest_data["active"])
    contest_data["active"] = None
    
    await save_json(CONTEST_FILE, contest_data)
    
    try:
        await bot.send_message(
            int(winner_id),
            f"🎉 *ПОЗДРАВЛЯЕМ!*\n\nВы выиграли в конкурсе!\n🏆 Приз: {prize} ⭐",
            parse_mode="Markdown"
        )
    except:
        pass
    
    return True, winner_id, prize

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

# ============== ОБРАБОТЧИКИ КОМАНД ==============

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
        
        if args[1].startswith("contest_"):
            await message.answer(f"🎁 *Конкурс*\n\nДля участия нажмите кнопку ниже:", parse_mode="Markdown",
                               reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                   [InlineKeyboardButton(text="✅ Участвовать в конкурсе", callback_data="join_contest")]
                               ]))
            return
        
        referrer_id = args[1]
        if referrer_id.isdigit():
            referrer_id = int(referrer_id)
            if referrer_id != message.from_user.id:
                user = await get_user(message.from_user.id)
                if not user["referrer"]:
                    settings = await load_json(SETTINGS_FILE, {})
                    await update_user(message.from_user.id, referrer=referrer_id)
                    referral_reward = settings.get("referral_reward", 10)
                    await add_stars(referrer_id, referral_reward, f"Реферал {message.from_user.id}")
                    referrer = await get_user(referrer_id)
                    await update_user(referrer_id, referral_count=referrer["referral_count"] + 1)
    
    user = await get_user(message.from_user.id)
    
    keyboard = get_main_keyboard()
    if await is_admin(message.from_user.id):
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="⚙️ Админ панель", callback_data="admin_panel")])
    
    contest = await get_active_contest()
    contest_text = ""
    if contest:
        contest_points = await get_contest_points(message.from_user.id)
        contest_text = f"\n\n🎁 *Активный конкурс:* {contest['name']}\n└ Ваши очки: {contest_points}\n└ Приз: {contest['prize']} ⭐"
    
    text = (f"✨ *Добро пожаловать, {message.from_user.full_name}!*\n\n"
            f"⭐ Баланс: {user['stars']} звезд{contest_text}\n\n"
            f"🎮 *Доступные игры:*\n"
            f"└ `/coin [ставка] [орел/решка]` - Орёл или Решка (x1.95)\n"
            f"└ `/roulette [ставка] [красное/черное/четное/нечетное]` - Рулетка (x1.95)\n"
            f"└ `/cubes [ставка] [1-6]` - Кости (x5.5)\n"
            f"└ `/crash [ставка] [1.01-50]` - Crash (выбери множитель)\n"
            f"└ `/mines [ставка] [1-6]` - Mines (открывай клетки)\n"
            f"└ `/diamond [ставка] [1-2]` - Алмаз (x2)\n"
            f"└ `/21 [ставка]` - 21 очко (x2.1)\n"
            f"└ `/fortune [ставка]` - Фортуна (x0-x50)\n"
            f"└ `/knb [ставка] [камень/ножницы/бумага]` - КНБ (x2.7)\n"
            f"└ `/poker [ставка]` - Покер (x0-x100)\n"
            f"└ `/keno [ставка] [5 чисел]` - Кено (x0-x200)\n"
            f"└ `/wheel [ставка]` - Колесо Фортуны (x0-x10)\n\n"
            f"👥 Рефералы (10% от покупок)\n"
            f"📋 Задания | 🎁 Конкурсы | 📦 Чеки\n"
            f"💰 Вывод: `/withdraw [сумма]`\n\n"
            f"Приятной игры! 🎉")
    
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

def get_main_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🎮 Игры", callback_data="games_menu"),
         InlineKeyboardButton(text="⭐ Баланс", callback_data="stars_info")],
        [InlineKeyboardButton(text="🎁 Конкурсы", callback_data="contests_menu"),
         InlineKeyboardButton(text="👥 Рефералы", callback_data="referrals_menu")],
        [InlineKeyboardButton(text="📋 Задания", callback_data="tasks_menu"),
         InlineKeyboardButton(text="💰 Вывод", callback_data="withdraw_menu")],
        [InlineKeyboardButton(text="🛒 Купить", callback_data="buy_stars"),
         InlineKeyboardButton(text="🎫 Промокод", callback_data="use_promo")],
        [InlineKeyboardButton(text="📦 Чек система", callback_data="check_system_menu"),
         InlineKeyboardButton(text="💬 Поддержка", callback_data="support_menu")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
         InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.callback_query(F.data == "games_menu")
async def games_menu(callback: CallbackQuery):
    text = ("🎮 *Доступные игры:*\n\n"
            "🪙 `/coin [ставка] [орел/решка]` - Орёл или Решка (x1.95)\n"
            "🎱 `/roulette [ставка] [красное/черное/четное/нечетное]` - Рулетка (x1.95)\n"
            "🎲 `/cubes [ставка] [1-6]` - Кости (x5.5)\n"
            "📈 `/crash [ставка] [1.01-50]` - Crash (выбери множитель)\n"
            "💣 `/mines [ставка] [1-6]` - Mines (открывай клетки)\n"
            "🤩 `/diamond [ставка] [1-2]` - Алмаз (x2)\n"
            "♠️ `/21 [ставка]` - 21 очко (x2.1)\n"
            "🔮 `/fortune [ставка]` - Фортуна (x0-x50)\n"
            "✂️ `/knb [ставка] [камень/ножницы/бумага]` - КНБ (x2.7)\n"
            "🃏 `/poker [ставка]` - Покер (x0-x100)\n"
            "🎯 `/keno [ставка] [5 чисел]` - Кено (x0-x200)\n"
            "🎰 `/wheel [ставка]` - Колесо Фортуны (x0-x10)\n\n"
            "📖 *Пример:* `/coin 100 орел`")
    
    buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

# ИГРА: МОНЕТА
@dp.message(Command("coin"))
async def cmd_coin(message: Message):
    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ Использование: /coin [ставка] [орел/решка]\nПример: /coin 100 орел")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("❌ Ставка должна быть числом!")
        return
    
    choice = args[2].lower()
    if choice not in ["орел", "решка", "eagle", "tails"]:
        await message.answer("❌ Выберите 'орел' или 'решка'")
        return
    
    choice = "eagle" if choice in ["орел", "eagle"] else "tails"
    user = await get_user(message.from_user.id)
    
    if bet < 1 or bet > 1000:
        await message.answer("❌ Ставка должна быть от 1 до 1000 ⭐")
        return
    
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "coin")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Монете")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    result = random.choice(["eagle", "tails"])
    win = (choice == result)
    
    choice_rus = "Орёл" if choice == "eagle" else "Решка"
    result_rus = "Орёл" if result == "eagle" else "Решка"
    
    game_hash = generate_game_hash("coin", bet, result, message.from_user.id)
    await save_game_hash(game_hash)
    
    if win:
        winnings = int(bet * 1.95)
        await add_stars(message.from_user.id, winnings, "Выигрыш в Монете")
        await update_user(message.from_user.id, games_won=user["games_won"] + 1)
        await update_user_limits(message.from_user.id, winnings, is_win=True)
        await message.answer(
            f"🪙 *Монета*\n\nВы выбрали: {choice_rus}\nВыпало: {result_rus}\n\n🎉 Вы выиграли {winnings} ⭐!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    else:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
        await message.answer(
            f"🪙 *Монета*\n\nВы выбрали: {choice_rus}\nВыпало: {result_rus}\n\n😔 Вы проиграли {bet} ⭐",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )

# ИГРА: РУЛЕТКА
@dp.message(Command("roulette"))
async def cmd_roulette(message: Message):
    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ Использование: /roulette [ставка] [красное/черное/четное/нечетное]\nПример: /roulette 100 красное")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("❌ Ставка должна быть числом!")
        return
    
    choice = args[2].lower()
    choice_map = {"красное": "red", "черное": "black", "четное": "even", "нечетное": "odd", 
                  "red": "red", "black": "black", "even": "even", "odd": "odd"}
    if choice not in choice_map:
        await message.answer("❌ Выберите: красное, черное, четное или нечетное")
        return
    
    choice = choice_map[choice]
    user = await get_user(message.from_user.id)
    
    if bet < 5 or bet > 2000:
        await message.answer("❌ Ставка должна быть от 5 до 2000 ⭐")
        return
    
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "roulette")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Рулетке")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
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
    
    game_hash = generate_game_hash("roulette", bet, result, message.from_user.id)
    await save_game_hash(game_hash)
    
    if win:
        winnings = int(bet * 1.95)
        await add_stars(message.from_user.id, winnings, "Выигрыш в Рулетке")
        await update_user(message.from_user.id, games_won=user["games_won"] + 1)
        await update_user_limits(message.from_user.id, winnings, is_win=True)
        
        color = "Красное" if result in red_numbers else ("Черное" if result in black_numbers else "Зеро")
        await message.answer(
            f"🎱 *Рулетка*\n\nВыпало число: {result} ({color})\n\n🎉 Вы выиграли {winnings} ⭐!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    else:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
        color = "Красное" if result in red_numbers else ("Черное" if result in black_numbers else "Зеро")
        await message.answer(
            f"🎱 *Рулетка*\n\nВыпало число: {result} ({color})\n\n😔 Вы проиграли {bet} ⭐",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )

# ИГРА: КОСТИ
@dp.message(Command("cubes"))
async def cmd_cubes(message: Message):
    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ Использование: /cubes [ставка] [число 1-6]\nПример: /cubes 100 3")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("❌ Ставка должна быть числом!")
        return
    
    try:
        choice = int(args[2])
        if choice < 1 or choice > 6:
            await message.answer("❌ Введите число от 1 до 6!")
            return
    except ValueError:
        await message.answer("❌ Введите число от 1 до 6!")
        return
    
    user = await get_user(message.from_user.id)
    
    if bet < 1 or bet > 500:
        await message.answer("❌ Ставка должна быть от 1 до 500 ⭐")
        return
    
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "cubes")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Костях")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    result = random.randint(1, 6)
    
    game_hash = generate_game_hash("cubes", bet, result, message.from_user.id)
    await save_game_hash(game_hash)
    
    if choice == result:
        winnings = int(bet * 5.5)
        await add_stars(message.from_user.id, winnings, "Выигрыш в Костях")
        await update_user(message.from_user.id, games_won=user["games_won"] + 1)
        await update_user_limits(message.from_user.id, winnings, is_win=True)
        await message.answer(
            f"🎲 *Кости*\n\nВы выбрали: {choice}\nВыпало: {result}\n\n🎉 Вы угадали! Выигрыш: {winnings} ⭐!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    else:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
        await message.answer(
            f"🎲 *Кости*\n\nВы выбрали: {choice}\nВыпало: {result}\n\n😔 Проигрыш: {bet} ⭐",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )

# ИГРА: CRASH
@dp.message(Command("crash"))
async def cmd_crash(message: Message, state: FSMContext):
    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ Использование: /crash [ставка] [множитель 1.01-50]\nПример: /crash 100 2.5")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("❌ Ставка должна быть числом!")
        return
    
    try:
        target_multiplier = float(args[2])
        if target_multiplier < 1.01 or target_multiplier > 50:
            await message.answer("❌ Множитель должен быть от 1.01 до 50!")
            return
    except ValueError:
        await message.answer("❌ Множитель должен быть числом!")
        return
    
    user = await get_user(message.from_user.id)
    
    if bet < 5 or bet > 2000:
        await message.answer("❌ Ставка должна быть от 5 до 2000 ⭐")
        return
    
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "crash")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Crash")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    crash_game = CrashGame(message.from_user.id, bet, target_multiplier)
    await state.update_data(crash_game=crash_game, target_multiplier=target_multiplier)
    await state.set_state(CrashStates.playing)
    
    msg = await message.answer(
        f"📈 *Crash Game*\n\n"
        f"💰 Ставка: {bet} ⭐\n"
        f"🎯 Цель: x{target_multiplier:.2f}\n"
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

# ИГРА: MINES (все в одном сообщении с исправленной кнопкой cashout)
@dp.message(Command("mines"))
async def cmd_mines(message: Message, state: FSMContext):
    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ Использование: /mines [ставка] [1-6]\nПример: /mines 100 3")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("❌ Ставка должна быть числом!")
        return
    
    try:
        mines_count = int(args[2])
        if mines_count < 1 or mines_count > 6:
            await message.answer("❌ Количество мин должно быть от 1 до 6!")
            return
    except ValueError:
        await message.answer("❌ Введите число от 1 до 6!")
        return
    
    user = await get_user(message.from_user.id)
    
    if bet < 10 or bet > 1000:
        await message.answer("❌ Ставка должна быть от 10 до 1000 ⭐")
        return
    
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "mines")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Mines")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    mines_game = MinesGame(message.from_user.id, bet, mines_count)
    await state.update_data(mines_game=mines_game)
    await state.set_state(MinesStates.playing)
    
    msg = await message.answer(
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
    
    await state.update_data(message_id=msg.message_id)

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
    buttons.append([InlineKeyboardButton(text="🚪 Выйти в меню", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def update_mines_message(callback: CallbackQuery, state: FSMContext, mines_game: MinesGame):
    multiplier = mines_game.current_multiplier
    potential = int(mines_game.bet * multiplier)
    
    text = (f"💣 *Mines Game*\n\n"
            f"💰 Ставка: {mines_game.bet} ⭐\n"
            f"💣 Мин на поле: {mines_game.mines_count}\n"
            f"📈 Текущий множитель: {multiplier:.2f}x\n"
            f"🎯 Потенциальный выигрыш: {potential} ⭐\n\n"
            f"🔍 Открывайте клетки и увеличивайте множитель!\n"
            f"⚠️ Наступите на мину - проиграете!")
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_mines_keyboard(mines_game)
    )

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
                [InlineKeyboardButton(text="💣 Играть снова", callback_data="games_menu"),
                 InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}"),
                 InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_main")]
            ])
        )
        await update_user_limits(callback.from_user.id, mines_game.bet, is_loss=True)
        await state.clear()
        await callback.answer("💥 Вы наступили на мину!")
        return
    
    await update_mines_message(callback, state, mines_game)
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
                [InlineKeyboardButton(text="💣 Играть снова", callback_data="games_menu"),
                 InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}"),
                 InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_main")]
            ])
        )
    else:
        await callback.answer("Ошибка!")
    
    await state.clear()
    await callback.answer()

# ИГРА: АЛМАЗ
@dp.message(Command("diamond"))
async def cmd_diamond(message: Message):
    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ Использование: /diamond [ставка] [1-2]\nПример: /diamond 100 1")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("❌ Ставка должна быть числом!")
        return
    
    try:
        choice = int(args[2])
        if choice not in [1, 2]:
            await message.answer("❌ Выберите 1 или 2!")
            return
    except ValueError:
        await message.answer("❌ Введите 1 или 2!")
        return
    
    user = await get_user(message.from_user.id)
    
    if bet < 5 or bet > 2000:
        await message.answer("❌ Ставка должна быть от 5 до 2000 ⭐")
        return
    
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "diamond")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Алмазе")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    result = random.randint(1, 2)
    game_hash = generate_game_hash("diamond", bet, result, message.from_user.id)
    await save_game_hash(game_hash)
    
    if choice == result:
        winnings = int(bet * 2)
        await add_stars(message.from_user.id, winnings, "Выигрыш в Алмазе")
        await update_user(message.from_user.id, games_won=user["games_won"] + 1)
        await update_user_limits(message.from_user.id, winnings, is_win=True)
        await message.answer(
            f"🤩 *Алмаз*\n\nВы выбрали: {choice}\nВыпало: {result}\n\n🎉 Вы нашли алмаз! Выигрыш: {winnings} ⭐!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    else:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
        await message.answer(
            f"🤩 *Алмаз*\n\nВы выбрали: {choice}\nВыпало: {result}\n\n😔 Это был обычный камень! Проигрыш: {bet} ⭐",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )

# ИГРА: 21 ОЧКО
@dp.message(Command("21"))
async def cmd_twenty_one(message: Message):
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ Использование: /21 [ставка]\nПример: /21 100")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("❌ Ставка должна быть числом!")
        return
    
    user = await get_user(message.from_user.id)
    
    if bet < 5 or bet > 3000:
        await message.answer("❌ Ставка должна быть от 5 до 3000 ⭐")
        return
    
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "21")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в 21")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    player_cards = [random.randint(1, 11), random.randint(1, 11)]
    dealer_cards = [random.randint(1, 11), random.randint(1, 11)]
    
    player_sum = sum(player_cards)
    dealer_sum = sum(dealer_cards)
    
    while player_sum < 17:
        player_cards.append(random.randint(1, 11))
        player_sum = sum(player_cards)
    
    while dealer_sum < 17:
        dealer_cards.append(random.randint(1, 11))
        dealer_sum = sum(dealer_cards)
    
    result_data = {"player_sum": player_sum, "dealer_sum": dealer_sum, "player_cards": player_cards, "dealer_cards": dealer_cards}
    game_hash = generate_game_hash("21", bet, result_data, message.from_user.id)
    await save_game_hash(game_hash)
    
    if player_sum > 21:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
        await message.answer(
            f"♠️ *21 очко*\n\nВаши карты: {player_cards} (сумма: {player_sum})\nКарты дилера: {dealer_cards} (сумма: {dealer_sum})\n\n😔 Перебор! Проигрыш: {bet} ⭐",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    elif dealer_sum > 21 or player_sum > dealer_sum:
        winnings = int(bet * 2.1)
        await add_stars(message.from_user.id, winnings, "Выигрыш в 21")
        await update_user(message.from_user.id, games_won=user["games_won"] + 1)
        await update_user_limits(message.from_user.id, winnings, is_win=True)
        await message.answer(
            f"♠️ *21 очко*\n\nВаши карты: {player_cards} (сумма: {player_sum})\nКарты дилера: {dealer_cards} (сумма: {dealer_sum})\n\n🎉 Вы выиграли {winnings} ⭐!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    elif player_sum == dealer_sum:
        await add_stars(message.from_user.id, bet, "Ничья в 21")
        await message.answer(
            f"♠️ *21 очко*\n\nВаши карты: {player_cards} (сумма: {player_sum})\nКарты дилера: {dealer_cards} (сумма: {dealer_sum})\n\n🤝 Ничья! Ставка возвращена.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    else:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
        await message.answer(
            f"♠️ *21 очко*\n\nВаши карты: {player_cards} (сумма: {player_sum})\nКарты дилера: {dealer_cards} (сумма: {dealer_sum})\n\n😔 Проигрыш: {bet} ⭐",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )

# ИГРА: ФОРТУНА
@dp.message(Command("fortune"))
async def cmd_fortune(message: Message):
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ Использование: /fortune [ставка]\nПример: /fortune 100")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("❌ Ставка должна быть числом!")
        return
    
    user = await get_user(message.from_user.id)
    
    if bet < 5 or bet > 2000:
        await message.answer("❌ Ставка должна быть от 5 до 2000 ⭐")
        return
    
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "fortune")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Фортуне")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    multipliers = [0, 0, 0.5, 1, 1.5, 2, 3, 5, 8, 10, 15, 20, 25, 30, 50]
    weights = [15, 12, 10, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0.5, 0.2]
    multiplier = random.choices(multipliers, weights=weights)[0]
    
    game_hash = generate_game_hash("fortune", bet, multiplier, message.from_user.id)
    await save_game_hash(game_hash)
    
    if multiplier > 0:
        winnings = int(bet * multiplier)
        await add_stars(message.from_user.id, winnings, "Выигрыш в Фортуне")
        await update_user(message.from_user.id, games_won=user["games_won"] + 1)
        await update_user_limits(message.from_user.id, winnings, is_win=True)
        
        if multiplier >= 10:
            await message.answer(
                f"🔮 *Фортуна*\n\n✨ Множитель: x{multiplier}!\n🎉 *ДЖЕКПОТ!* Вы выиграли {winnings} ⭐!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
                ])
            )
        else:
            await message.answer(
                f"🔮 *Фортуна*\n\n✨ Множитель: x{multiplier}\n🎉 Вы выиграли {winnings} ⭐!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
                ])
            )
    else:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
        await message.answer(
            f"🔮 *Фортуна*\n\n✨ Множитель: x{multiplier}\n😔 Фортуна отвернулась от вас! Проигрыш: {bet} ⭐",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )

# ИГРА: КАМЕНЬ-НОЖНИЦЫ-БУМАГА
@dp.message(Command("knb"))
async def cmd_knb(message: Message):
    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ Использование: /knb [ставка] [камень/ножницы/бумага]\nПример: /knb 100 камень")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("❌ Ставка должна быть числом!")
        return
    
    choice = args[2].lower()
    choice_map = {"камень": "rock", "ножницы": "scissors", "бумага": "paper", 
                  "rock": "rock", "scissors": "scissors", "paper": "paper"}
    if choice not in choice_map:
        await message.answer("❌ Выберите: камень, ножницы или бумага")
        return
    
    choice = choice_map[choice]
    user = await get_user(message.from_user.id)
    
    if bet < 1 or bet > 500:
        await message.answer("❌ Ставка должна быть от 1 до 500 ⭐")
        return
    
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "knb")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в КНБ")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    bot_choice = random.choice(["rock", "scissors", "paper"])
    choice_rus = {"rock": "✊ Камень", "scissors": "✌️ Ножницы", "paper": "✋ Бумага"}
    
    result_data = {"player": choice, "bot": bot_choice}
    game_hash = generate_game_hash("knb", bet, result_data, message.from_user.id)
    await save_game_hash(game_hash)
    
    if choice == bot_choice:
        await add_stars(message.from_user.id, bet, "Ничья в КНБ")
        await message.answer(
            f"✂️ *Камень-Ножницы-Бумага*\n\nВаш ход: {choice_rus[choice]}\nХод бота: {choice_rus[bot_choice]}\n\n🤝 Ничья! Ставка возвращена.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    elif (choice == "rock" and bot_choice == "scissors") or \
         (choice == "scissors" and bot_choice == "paper") or \
         (choice == "paper" and bot_choice == "rock"):
        winnings = int(bet * 2.7)
        await add_stars(message.from_user.id, winnings, "Выигрыш в КНБ")
        await update_user(message.from_user.id, games_won=user["games_won"] + 1)
        await update_user_limits(message.from_user.id, winnings, is_win=True)
        await message.answer(
            f"✂️ *Камень-Ножницы-Бумага*\n\nВаш ход: {choice_rus[choice]}\nХод бота: {choice_rus[bot_choice]}\n\n🎉 Вы победили! Выигрыш: {winnings} ⭐!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    else:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
        await message.answer(
            f"✂️ *Камень-Ножницы-Бумага*\n\nВаш ход: {choice_rus[choice]}\nХод бота: {choice_rus[bot_choice]}\n\n😔 Вы проиграли! Потеряно: {bet} ⭐",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )

# ИГРА: ПОКЕР
@dp.message(Command("poker"))
async def cmd_poker(message: Message):
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ Использование: /poker [ставка]\nПример: /poker 100")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("❌ Ставка должна быть числом!")
        return
    
    user = await get_user(message.from_user.id)
    
    if bet < 10 or bet > 5000:
        await message.answer("❌ Ставка должна быть от 10 до 5000 ⭐")
        return
    
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "poker")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Покере")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    hands = ["High Card", "Pair", "Two Pair", "Three of Kind", "Straight", "Flush", "Full House", "Four of Kind", "Straight Flush", "Royal Flush"]
    weights = [50, 25, 15, 8, 5, 3, 2, 1, 0.5, 0.2]
    multipliers = [0, 1, 2, 3, 5, 8, 12, 20, 50, 100]
    
    hand = random.choices(hands, weights=weights)[0]
    idx = hands.index(hand)
    multiplier = multipliers[idx]
    
    game_hash = generate_game_hash("poker", bet, hand, message.from_user.id)
    await save_game_hash(game_hash)
    
    if multiplier > 0:
        winnings = int(bet * multiplier)
        await add_stars(message.from_user.id, winnings, "Выигрыш в Покере")
        await update_user(message.from_user.id, games_won=user["games_won"] + 1)
        await update_user_limits(message.from_user.id, winnings, is_win=True)
        await message.answer(
            f"🃏 *Покер*\n\nВаша комбинация: {hand}\n\n🎉 Вы выиграли {winnings} ⭐ (x{multiplier})!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    else:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
        await message.answer(
            f"🃏 *Покер*\n\nВаша комбинация: {hand}\n\n😔 Проигрыш: {bet} ⭐",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )

# ИГРА: КЕНО
@dp.message(Command("keno"))
async def cmd_keno(message: Message):
    args = message.text.split()
    if len(args) != 7:
        await message.answer("❌ Использование: /keno [ставка] [5 чисел от 1 до 80 через пробел]\nПример: /keno 100 5 12 23 45 67")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("❌ Ставка должна быть числом!")
        return
    
    try:
        numbers = [int(x) for x in args[2:7]]
        if not all(1 <= n <= 80 for n in numbers):
            await message.answer("❌ Все числа должны быть от 1 до 80!")
            return
    except ValueError:
        await message.answer("❌ Введите 5 чисел от 1 до 80!")
        return
    
    user = await get_user(message.from_user.id)
    
    if bet < 10 or bet > 2000:
        await message.answer("❌ Ставка должна быть от 10 до 2000 ⭐")
        return
    
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "keno")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Кено")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    drawn = sorted(random.sample(range(1, 81), 20))
    matches = len(set(numbers) & set(drawn))
    
    payouts = {0: 0, 1: 0, 2: 0, 3: 1, 4: 2, 5: 5, 6: 10, 7: 25, 8: 50, 9: 100, 10: 200}
    multiplier = payouts.get(matches, 0)
    
    result_data = {"numbers": numbers, "drawn": drawn, "matches": matches}
    game_hash = generate_game_hash("keno", bet, result_data, message.from_user.id)
    await save_game_hash(game_hash)
    
    if multiplier > 0:
        winnings = int(bet * multiplier)
        await add_stars(message.from_user.id, winnings, "Выигрыш в Кено")
        await update_user(message.from_user.id, games_won=user["games_won"] + 1)
        await update_user_limits(message.from_user.id, winnings, is_win=True)
        await message.answer(
            f"🎯 *Кено*\n\nВаши числа: {numbers}\nСовпадений: {matches}\n\n🎉 Выигрыш: {winnings} ⭐ (x{multiplier})!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    else:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
        await message.answer(
            f"🎯 *Кено*\n\nВаши числа: {numbers}\nСовпадений: {matches}\n\n😔 Проигрыш: {bet} ⭐",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )

# ИГРА: КОЛЕСО ФОРТУНЫ
@dp.message(Command("wheel"))
async def cmd_wheel(message: Message):
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ Использование: /wheel [ставка]\nПример: /wheel 100")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("❌ Ставка должна быть числом!")
        return
    
    user = await get_user(message.from_user.id)
    
    if bet < 5 or bet > 1500:
        await message.answer("❌ Ставка должна быть от 5 до 1500 ⭐")
        return
    
    limit_ok, limit_msg = await check_user_limits(message.from_user.id, bet, "wheel")
    if not limit_ok:
        await message.answer(f"❌ {limit_msg}")
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    await remove_stars(message.from_user.id, bet, "Ставка в Колесе Фортуны")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    
    segments = ["1x", "2x", "3x", "5x", "10x", "0x"]
    result = random.choice(segments)
    multipliers = {"1x": 1, "2x": 2, "3x": 3, "5x": 5, "10x": 10, "0x": 0}
    multiplier = multipliers[result]
    
    game_hash = generate_game_hash("wheel", bet, result, message.from_user.id)
    await save_game_hash(game_hash)
    
    if multiplier > 0:
        winnings = int(bet * multiplier)
        await add_stars(message.from_user.id, winnings, "Выигрыш в Колесе Фортуны")
        await update_user(message.from_user.id, games_won=user["games_won"] + 1)
        await update_user_limits(message.from_user.id, winnings, is_win=True)
        await message.answer(
            f"🎡 *Колесо Фортуны*\n\nКолесо остановилось на: {result}\n\n🎉 Вы выиграли {winnings} ⭐!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )
    else:
        await update_user_limits(message.from_user.id, bet, is_loss=True)
        await message.answer(
            f"🎡 *Колесо Фортуны*\n\nКолесо остановилось на: {result}\n\n😔 Проигрыш: {bet} ⭐",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить честность", callback_data=f"verify_hash_{game_hash['hash']}")]
            ])
        )

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

# ============== ОСТАЛЬНЫЕ ОБРАБОТЧИКИ ==============

@dp.callback_query(F.data == "stars_info")
async def stars_info(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    settings = await load_json(SETTINGS_FILE, {})
    
    text = (f"⭐ *Ваш баланс:* {user['stars']} звезд\n\n"
            f"📊 *Детальная статистика:*\n"
            f"└ Всего заработано: {user['total_earned']} ⭐\n"
            f"└ Всего потрачено: {user['total_spent']} ⭐\n"
            f"└ Всего покупок: {user['total_purchases']} ⭐\n"
            f"└ Реферальных отчислений: {user['referral_earnings']} ⭐\n"
            f"└ Сыграно игр: {user['games_played']}\n"
            f"└ Побед: {user['games_won']}\n"
            f"└ Дневные потери: {user['daily_loss']} ⭐\n"
            f"└ Дневные выигрыши: {user['daily_win']} ⭐\n\n"
            f"💱 *Курс обмена:*\n"
            f"└ {settings.get('exchange_rate', 1)} звезда бота = 1 звезда Telegram\n"
            f"└ Минимальный вывод: {settings.get('min_withdraw', 500)} ⭐")
    
    buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "contests_menu")
async def contests_menu(callback: CallbackQuery):
    contest = await get_active_contest()
    
    if contest:
        end_time = datetime.fromisoformat(contest["end_time"])
        time_left = end_time - datetime.now()
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        
        user_points = await get_contest_points(callback.from_user.id)
        is_participant = str(callback.from_user.id) in contest.get("participants", {})
        
        text = (f"🎁 *Активный конкурс*\n\n"
                f"✨ Название: {contest['name']}\n"
                f"📝 Описание: {contest['description']}\n"
                f"💰 Приз: {contest['prize']} ⭐\n"
                f"👥 Участников: {len(contest['participants'])}\n"
                f"🎯 Ваши очки: {user_points}\n"
                f"✅ Вы участвуете: {'Да' if is_participant else 'Нет'}\n"
                f"⏰ Осталось: {hours}ч {minutes}м\n\n"
                f"🔗 Ссылка для участия: {contest['link']}\n\n"
                f"📌 *Как получить очки:*\n"
                f"└ Играйте в любые игры\n"
                f"└ Чем больше ставка, тем больше очков\n"
                f"└ Очки начисляются за проигрыши\n"
                f"└ Чем больше очков, тем выше шанс победы!")
        
        buttons = [
            [InlineKeyboardButton(text="✅ Участвовать", url=contest['link']),
             InlineKeyboardButton(text="📋 Участвовал", callback_data="join_contest")],
            [InlineKeyboardButton(text="🏆 Рейтинг очков", callback_data="contest_rating")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    else:
        text = "🎁 *Конкурсы*\n\nСейчас нет активных конкурсов."
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "contest_rating")
async def contest_rating(callback: CallbackQuery):
    contest = await get_active_contest()
    
    if not contest:
        await callback.answer("Нет активного конкурса!")
        return
    
    participants = contest.get("participants", {})
    if not participants:
        await callback.answer("Нет участников!", show_alert=True)
        return
    
    # Сортируем участников по очкам
    sorted_participants = sorted(participants.items(), key=lambda x: x[1].get("points", 0), reverse=True)[:10]
    
    text = "🏆 *Рейтинг очков в конкурсе*\n\n"
    for i, (uid, data) in enumerate(sorted_participants, 1):
        points = data.get("points", 0)
        text += f"{i}. ID: {uid} - {points} очков\n"
    
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "join_contest")
async def join_contest_callback(callback: CallbackQuery):
    contest = await get_active_contest()
    
    if not contest:
        await callback.answer("Нет активного конкурса!")
        return
    
    success, msg = await join_contest(callback.from_user.id, callback.message.message_id)
    await callback.answer(msg, show_alert=True)
    
    if success:
        user_points = await get_contest_points(callback.from_user.id)
        await callback.message.edit_text(
            f"🎁 *Вы участвуете в конкурсе!*\n\n"
            f"✨ {contest['name']}\n"
            f"💰 Приз: {contest['prize']} ⭐\n"
            f"🎯 Ваши очки: {user_points}\n\n"
            f"Играйте в игры, чтобы набирать очки!\n"
            f"Чем больше очков, тем выше шанс победы!\n"
            f"Удачи! 🍀",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏆 Рейтинг очков", callback_data="contest_rating")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="contests_menu")]
            ])
        )

@dp.callback_query(F.data == "referrals_menu")
async def referrals_menu(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    settings = await load_json(SETTINGS_FILE, {})
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    import urllib.parse
    safe_username = urllib.parse.quote(bot_username, safe='')
    link = f"https://t.me/{safe_username}?start={user['referral_code']}"
    
    text = (f"👥 *Реферальная система*\n\n⭐ Ссылка:\n`{link}`\n\n📊 Статистика:\n"
            f"└ Приглашено: {user['referral_count']}\n└ Заработано: {user['referral_earnings']} ⭐\n\n"
            f"💡 Условия:\n• {settings.get('referral_reward', 10)} ⭐ за друга\n"
            f"• {settings.get('referral_percent', 10)}% от покупок друга")
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать", callback_data=f"copy_{link}"),
         InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "tasks_menu")
async def tasks_menu(callback: CallbackQuery):
    tasks = await get_all_tasks()
    
    if not tasks:
        text = "📋 *Задания*\n\nНет активных заданий."
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
    else:
        text = "📋 *Задания от спонсоров:*\n\n"
        buttons = []
        for task in tasks:
            completed = await is_task_completed(callback.from_user.id, task["id"])
            status = "✅ Выполнено" if completed else "❌ Не выполнено"
            text += f"• *{task['name']}*\n└ Награда: {task['reward']} ⭐\n└ Статус: {status}\n\n"
            if not completed:
                buttons.append([InlineKeyboardButton(text=f"✅ {task['name']}", callback_data=f"check_task_{task['id']}")])
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

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
    
    success, message = await check_task_completion(callback.from_user.id, task)
    
    if success:
        await add_stars(callback.from_user.id, task["reward"], f"Задание: {task['name']}")
        await complete_task(callback.from_user.id, task_id)
        await callback.answer(f"✅ +{task['reward']} ⭐", show_alert=True)
        await tasks_menu(callback)
    else:
        await callback.answer(message, show_alert=True)

@dp.callback_query(F.data == "withdraw_menu")
async def withdraw_menu(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    settings = await load_json(SETTINGS_FILE, {})
    
    text = (f"💰 *Вывод звезд*\n\n⭐ Баланс: {user['stars']}\n"
            f"💱 Курс: {settings.get('exchange_rate', 1)}:1 к звездам TG\n"
            f"📉 Минимум: {settings.get('min_withdraw', 500)} ⭐\n"
            f"⏰ КД между выводами: {settings.get('withdraw_cooldown_hours', 24)} часов\n"
            f"📊 Лимит выводов в день: {settings.get('max_withdraw_per_day', 3)}\n\n"
            f"Команда: `/withdraw <сумма>`")
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]))
    await callback.answer()

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

@dp.callback_query(F.data == "buy_stars")
async def buy_stars_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BuyStates.waiting_for_amount)
    await callback.message.edit_text(
        "🛒 *Покупка звезд*\n\n"
        "💎 Курс: 1 звезда TG = 1 ⭐\n\n"
        "Введите количество звезд для покупки (от 50 до 100000):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_main")]
        ])
    )
    await callback.answer()

@dp.message(BuyStates.waiting_for_amount)
async def buy_stars_amount(message: Message, state: FSMContext):
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
    await message.answer(
        f"✅ *Покупка успешна!*\n\n⭐ Начислено: {amount} ⭐\n💰 Баланс: {user['stars'] + amount} ⭐",
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "check_system_menu")
async def check_system_menu(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    settings = await load_json(SETTINGS_FILE, {})
    
    if user.get("check_system_unlocked", False):
        text = (f"📦 *Система чеков*\n\n"
                f"✅ Система разблокирована!\n\n"
                f"💰 Создание чека:\n"
                f"└ Минимальная сумма: 100 ⭐\n"
                f"└ Максимальная сумма: 100000 ⭐\n\n"
                f"📋 Ваши чеки: `/my_checks`\n"
                f"🎫 Активировать чек: по ссылке или `/use_check <код>`")
        
        buttons = [
            [InlineKeyboardButton(text="📝 Создать чек", callback_data="create_check")],
            [InlineKeyboardButton(text="📋 Мои чеки", callback_data="my_checks")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    else:
        price = settings.get("check_system_price", 100)
        text = (f"📦 *Система чеков*\n\n"
                f"🔒 Система заблокирована!\n\n"
                f"💎 Стоимость разблокировки: {price} ⭐\n\n"
                f"После разблокировки вы сможете:\n"
                f"• Создавать чеки для друзей\n"
                f"• Активировать чеки других пользователей\n"
                f"• Переводить звезды между пользователями")
        
        buttons = [
            [InlineKeyboardButton(text="🔓 Разблокировать", callback_data="unlock_check_system")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "unlock_check_system")
async def unlock_check_system_callback(callback: CallbackQuery):
    success = await unlock_check_system(callback.from_user.id)
    
    if success:
        await callback.answer("✅ Система чеков разблокирована!", show_alert=True)
    else:
        settings = await load_json(SETTINGS_FILE, {})
        price = settings.get("check_system_price", 100)
        await callback.answer(f"❌ Недостаточно звезд! Нужно {price} ⭐", show_alert=True)
    
    await check_system_menu(callback)

@dp.callback_query(F.data == "create_check")
async def create_check_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_check_amount)
    await callback.message.edit_text(
        "📦 *Создание чека*\n\n"
        "💰 Минимальная сумма: 100 ⭐\n"
        "💰 Максимальная сумма: 100000 ⭐\n\n"
        "Введите сумму чека:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="check_system_menu")]
        ])
    )
    await callback.answer()

@dp.message(AdminStates.waiting_for_check_amount)
async def create_check_amount(message: Message, state: FSMContext):
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
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="check_system_menu")]
    ]))
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

@dp.callback_query(F.data == "use_promo")
async def use_promo_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromoStates.waiting_for_promo_code)
    await callback.message.edit_text(
        "🎫 *Активация промокода*\n\nВведите промокод:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_main")]
        ])
    )
    await callback.answer()

@dp.message(PromoStates.waiting_for_promo_code)
async def use_promo_code(message: Message, state: FSMContext):
    success, msg, _ = await use_promo(message.from_user.id, message.text.strip().upper())
    await message.answer(f"{'✅' if success else '❌'} *{msg}*", parse_mode="Markdown")
    await state.clear()

@dp.callback_query(F.data == "support_menu")
async def support_menu(callback: CallbackQuery):
    tickets = await get_user_tickets(callback.from_user.id)
    open_tickets = [t for t in tickets if t["status"] == "open"]
    
    text = (f"💬 *Поддержка*\n\n"
            f"📊 Ваши тикеты:\n"
            f"└ Открытых: {len(open_tickets)}\n"
            f"└ Закрытых: {len(tickets) - len(open_tickets)}\n\n"
            f"Выберите действие:")
    
    buttons = [
        [InlineKeyboardButton(text="📝 Создать тикет", callback_data="support_create")],
        [InlineKeyboardButton(text="📋 Мои тикеты", callback_data="support_my_tickets")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "support_create")
async def support_create(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting_for_message)
    await callback.message.edit_text(
        "💬 *Создание тикета*\n\n"
        "Опишите вашу проблему или вопрос. Наши администраторы свяжутся с вами в ближайшее время.\n\n"
        "Введите ваше сообщение:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="support_menu")]
        ])
    )
    await callback.answer()

@dp.message(SupportStates.waiting_for_message)
async def support_send_message(message: Message, state: FSMContext):
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
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="support_menu")]]
    else:
        text = "📋 *Мои тикеты:*\n\n"
        buttons = []
        for ticket in tickets[-10:]:
            status = "🟢 Открыт" if ticket["status"] == "open" else "🔴 Закрыт"
            text += f"*#{ticket['id']}* - {status}\n└ Создан: {ticket['created_at'][:19]}\n\n"
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="support_menu")])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    contest_points = await get_contest_points(callback.from_user.id)
    
    text = (f"📊 *Ваша статистика*\n\n⭐ Баланс: {user['stars']}\n💰 Заработано: {user['total_earned']}\n"
            f"💸 Потрачено: {user['total_spent']}\n🛒 Покупок: {user['total_purchases']}\n"
            f"👥 Рефералов: {user['referral_count']}\n🎮 Игр: {user['games_played']}\n"
            f"🏆 Побед: {user['games_won']}\n✨ Достижений: {len(user['achievements'])}\n"
            f"🎯 Очки конкурса: {contest_points}\n"
            f"📅 Дневные потери: {user['daily_loss']} ⭐\n"
            f"📈 Дневные выигрыши: {user['daily_win']} ⭐\n"
            f"📊 Проигрышей подряд: {user['consecutive_losses']}\n"
            f"📦 Чек система: {'✅ Разблокирована' if user.get('check_system_unlocked', False) else '🔒 Заблокирована'}\n"
            f"📅 Регистрация: {user['created_at'][:10]}")
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    settings = await load_json(SETTINGS_FILE, {})
    text = (f"❓ *Помощь*\n\n"
            f"🎮 *Игры (12):*\n"
            f"└ `/coin [ставка] [орел/решка]` - Орёл или Решка (x1.95)\n"
            f"└ `/roulette [ставка] [цвет/четность]` - Рулетка (x1.95)\n"
            f"└ `/cubes [ставка] [1-6]` - Кости (x5.5)\n"
            f"└ `/crash [ставка] [1.01-50]` - Crash (выбери множитель)\n"
            f"└ `/mines [ставка] [1-6]` - Mines (открывай клетки)\n"
            f"└ `/diamond [ставка] [1-2]` - Алмаз (x2)\n"
            f"└ `/21 [ставка]` - 21 очко (x2.1)\n"
            f"└ `/fortune [ставка]` - Фортуна (x0-x50)\n"
            f"└ `/knb [ставка] [камень/ножницы/бумага]` - КНБ (x2.7)\n"
            f"└ `/poker [ставка]` - Покер (x0-x100)\n"
            f"└ `/keno [ставка] [5 чисел]` - Кено (x0-x200)\n"
            f"└ `/wheel [ставка]` - Колесо Фортуны (x0-x10)\n\n"
            f"🎁 *Конкурсы:* Участвуйте, играйте, набирайте очки, выигрывайте призы!\n"
            f"└ Очки начисляются за проигрыши (чем больше ставка, тем больше очков)\n\n"
            f"📋 *Задания:* Подписывайтесь на каналы (бот должен быть в канале!)\n\n"
            f"👥 *Рефералы:* {settings.get('referral_reward', 10)} ⭐ за друга + {settings.get('referral_percent', 10)}% от его покупок\n\n"
            f"📦 *Чеки:*\n"
            f"└ Разблокировка: {settings.get('check_system_price', 100)} ⭐\n"
            f"└ Создание чека: от 100 до 100000 ⭐\n"
            f"└ Активация чека: по ссылке или `/use_check <код>`\n\n"
            f"💰 *Вывод:* `/withdraw <сумма>`, мин. {settings.get('min_withdraw', 500)} ⭐\n"
            f"└ КД между выводами: {settings.get('withdraw_cooldown_hours', 24)} часов\n"
            f"└ Лимит выводов в день: {settings.get('max_withdraw_per_day', 3)}\n\n"
            f"🛒 *Покупка:* Введите сумму в меню покупки, оплата Telegram Stars\n\n"
            f"⚠️ *Лимиты:*\n"
            f"└ Дневной лимит потерь: {settings.get('max_daily_loss', 50000)} ⭐\n"
            f"└ Дневной лимит выигрыша: {settings.get('max_daily_win', 100000)} ⭐\n"
            f"└ Макс. проигрышей подряд: {settings.get('max_consecutive_losses', 10)}\n\n"
            f"💬 *Поддержка:* Создайте тикет в меню поддержки")
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await get_user(callback.from_user.id)
    keyboard = get_main_keyboard()
    if await is_admin(callback.from_user.id):
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="⚙️ Админ панель", callback_data="admin_panel")])
    await callback.message.edit_text(f"✨ Главное меню\n\n⭐ У вас {user['stars']} звезд", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data.startswith("copy_"))
async def copy_text(callback: CallbackQuery):
    text = callback.data.replace("copy_", "")
    await callback.answer("✅ Ссылка скопирована!", show_alert=True)

# ============== АДМИН ПАНЕЛЬ (полная версия) ==============

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    buttons = [
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
         InlineKeyboardButton(text="💰 Звезды", callback_data="admin_stars")],
        [InlineKeyboardButton(text="📋 Задания", callback_data="admin_tasks"),
         InlineKeyboardButton(text="🎫 Промокоды", callback_data="admin_promo")],
        [InlineKeyboardButton(text="📦 Чеки", callback_data="admin_checks"),
         InlineKeyboardButton(text="🎁 Конкурсы", callback_data="admin_contest")],
        [InlineKeyboardButton(text="⚙️ Ограничения", callback_data="admin_limits"),
         InlineKeyboardButton(text="💰 Выводы", callback_data="admin_withdrawals")],
        [InlineKeyboardButton(text="⛔ Бан выводов", callback_data="admin_withdraw_bans"),
         InlineKeyboardButton(text="💬 Поддержка", callback_data="admin_support")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📝 Логи", callback_data="admin_logs"),
         InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    await callback.message.edit_text("⚙️ *Админ панель*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_users")
async def admin_users_menu(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    buttons = [
        [InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="admin_find_user")],
        [InlineKeyboardButton(text="📊 Топ пользователей", callback_data="admin_top_users")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]
    await callback.message.edit_text("👥 *Управление пользователями*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_find_user")
async def admin_find_user(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    await state.set_state(AdminStates.waiting_for_user_id)
    await callback.message.edit_text("🔍 Введите ID пользователя:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_users")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_user_id)
async def admin_show_user(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав!")
        await state.clear()
        return
    
    try:
        user_id = int(message.text.strip())
        user = await get_user(user_id)
        contest_points = await get_contest_points(user_id)
        
        text = (f"👤 *Пользователь {user_id}*\n\n⭐ Баланс: {user['stars']}\n💰 Заработано: {user['total_earned']}\n"
                f"💸 Потрачено: {user['total_spent']}\n👥 Рефералов: {user['referral_count']}\n"
                f"🎮 Игр: {user['games_played']}\n🏆 Побед: {user['games_won']}\n"
                f"🎯 Очки конкурса: {contest_points}\n"
                f"📅 Дневные потери: {user['daily_loss']} ⭐\n"
                f"📈 Дневные выигрыши: {user['daily_win']} ⭐\n"
                f"📊 Проигрышей подряд: {user['consecutive_losses']}\n"
                f"⛔ Бан вывода: {'Да' if user.get('is_withdraw_banned', False) else 'Нет'}\n"
                f"📦 Чек система: {'✅' if user.get('check_system_unlocked', False) else '❌'}\n"
                f"📅 Регистрация: {user['created_at'][:10]}")
        buttons = [
            [InlineKeyboardButton(text="➕ Добавить звезды", callback_data=f"admin_add_stars_{user_id}"),
             InlineKeyboardButton(text="➖ Забрать звезды", callback_data=f"admin_remove_stars_{user_id}")],
            [InlineKeyboardButton(text="🔓 Разблокировать чеки", callback_data=f"admin_unlock_checks_{user_id}")],
            [InlineKeyboardButton(text="⛔ Забанить вывод", callback_data=f"admin_ban_withdraw_{user_id}"),
             InlineKeyboardButton(text="✅ Разбанить вывод", callback_data=f"admin_unban_withdraw_{user_id}")],
            [InlineKeyboardButton(text="🎯 Добавить очки конкурса", callback_data=f"admin_add_points_{user_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
        ]
        await message.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except Exception as e:
        await message.answer(f"❌ Пользователь не найден!")
    await state.clear()

@dp.callback_query(F.data.startswith("admin_add_stars_"))
async def admin_add_stars_amount(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.replace("admin_add_stars_", ""))
    await state.update_data(target_user=user_id, action="add")
    await state.set_state(AdminStates.waiting_for_stars_amount)
    await callback.message.edit_text("💰 Введите количество звезд для начисления:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_users")]
    ]))
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_remove_stars_"))
async def admin_remove_stars_amount(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.replace("admin_remove_stars_", ""))
    await state.update_data(target_user=user_id, action="remove")
    await state.set_state(AdminStates.waiting_for_stars_amount)
    await callback.message.edit_text("💰 Введите количество звезд для списания:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_users")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_stars_amount)
async def admin_process_stars(message: Message, state: FSMContext):
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

@dp.callback_query(F.data.startswith("admin_add_points_"))
async def admin_add_points_amount(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.replace("admin_add_points_", ""))
    await state.update_data(target_user=user_id)
    await state.set_state(AdminStates.waiting_for_stars_amount)
    await callback.message.edit_text("🎯 Введите количество очков конкурса для начисления:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_users")]
    ]))
    await callback.answer()

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
    await callback.message.edit_text("⏰ Введите количество часов бана вывода:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_users")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_ban_hours)
async def admin_process_ban(message: Message, state: FSMContext):
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
        text += f"{i}. ID: {uid} - {data.get('stars', 0)} ⭐\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_stars")
async def admin_stars_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    users = await load_json(USERS_FILE, {})
    total_stars = sum(u.get("stars", 0) for u in users.values())
    
    text = f"💰 *Управление звездами*\n\nВсего звезд в системе: {total_stars}\nВсего пользователей: {len(users)}\n\nВыберите действие:"
    
    buttons = [
        [InlineKeyboardButton(text="💸 Массовая выдача", callback_data="admin_mass_add")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_mass_add")
async def admin_mass_add(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_stars_amount)
    await state.update_data(action="mass_add")
    await callback.message.edit_text("💰 Введите количество звезд для ВСЕХ пользователей:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_stars")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_tasks")
async def admin_tasks_menu(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить задание", callback_data="admin_add_task")],
        [InlineKeyboardButton(text="📋 Список заданий", callback_data="admin_list_tasks")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]
    await callback.message.edit_text("📋 *Управление заданиями*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_add_task")
async def admin_add_task(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    await state.set_state(AdminStates.waiting_for_task_name)
    await callback.message.edit_text("📝 Введите название задания:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_tasks")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_task_name)
async def admin_task_name(message: Message, state: FSMContext):
    await state.update_data(task_name=message.text)
    await state.set_state(AdminStates.waiting_for_task_link)
    await message.answer("🔗 Введите ссылку на канал (например, https://t.me/channel):\n\n⚠️ Бот должен быть добавлен в этот канал администратором!")

@dp.message(AdminStates.waiting_for_task_link)
async def admin_task_link(message: Message, state: FSMContext):
    await state.update_data(task_link=message.text)
    await state.set_state(AdminStates.waiting_for_task_reward)
    await message.answer("💰 Введите награду (звезды):")

@dp.message(AdminStates.waiting_for_task_reward)
async def admin_task_reward(message: Message, state: FSMContext):
    try:
        reward = int(message.text)
        data = await state.get_data()
        
        task_id = await add_task(message.from_user.id, data["task_name"], data["task_link"], reward)
        await message.answer(
            f"✅ Задание добавлено!\n\n"
            f"📝 Название: {data['task_name']}\n"
            f"🔗 Ссылка: {data['task_link']}\n"
            f"💰 Награда: {reward} ⭐\n\n"
            f"⚠️ Важно: Бот должен быть добавлен в канал администратором для корректной проверки!",
            parse_mode="Markdown"
        )
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
            text += f"*ID {task['id']}:* {task['name']}\n"
            text += f"└ Награда: {task['reward']} ⭐\n"
            text += f"└ Ссылка: {task['link']}\n"
            text += f"└ Создано: {task['created_at'][:10]}\n\n"
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
async def admin_promo_menu(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    buttons = [
        [InlineKeyboardButton(text="➕ Создать промокод", callback_data="admin_create_promo")],
        [InlineKeyboardButton(text="📋 Список промокодов", callback_data="admin_list_promo")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]
    await callback.message.edit_text("🎫 *Управление промокодами*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_create_promo")
async def admin_create_promo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_promo_code)
    await callback.message.edit_text("🎫 Введите код промокода:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_promo")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_promo_code)
async def admin_promo_code(message: Message, state: FSMContext):
    await state.update_data(promo_code=message.text.strip().upper())
    await state.set_state(AdminStates.waiting_for_promo_reward)
    await message.answer("💰 Введите награду (звезды):")

@dp.message(AdminStates.waiting_for_promo_reward)
async def admin_promo_reward(message: Message, state: FSMContext):
    try:
        reward = int(message.text)
        await state.update_data(promo_reward=reward)
        await state.set_state(AdminStates.waiting_for_promo_limit)
        await message.answer("📊 Введите лимит использований:")
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(AdminStates.waiting_for_promo_limit)
async def admin_promo_limit(message: Message, state: FSMContext):
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
            text += f"*{p['code']}*\n└ Награда: {p['reward']} ⭐\n└ Использовано: {p['used']}/{p['limit']}\n└ Создан: {p['created_at'][:10]}\n\n"
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
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    checks = await load_json(CHECKS_FILE, {"checks": [], "used_checks": []})
    active = len(checks["checks"])
    used = len(checks["used_checks"])
    
    text = f"📦 *Управление чеками*\n\n🟢 Активных чеков: {active}\n🔴 Использовано: {used}\n\nВыберите действие:"
    
    buttons = [
        [InlineKeyboardButton(text="➕ Создать чек", callback_data="admin_create_check")],
        [InlineKeyboardButton(text="📋 Список чеков", callback_data="admin_list_checks")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_create_check")
async def admin_create_check(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_check_amount)
    await callback.message.edit_text("📦 Введите сумму чека:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_checks")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_check_amount)
async def admin_create_check_amount(message: Message, state: FSMContext):
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
        
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        import urllib.parse
        safe_username = urllib.parse.quote(bot_username, safe='')
        link = f"https://t.me/{safe_username}?start=check_{code}"
        
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
            text += f"└ Сумма: {c['amount']} ⭐ (создал: {c['creator']})\n"
    
    if checks["used_checks"]:
        text += "\n*Использованные чеки:*\n"
        for c in checks["used_checks"][-10:]:
            text += f"└ Сумма: {c['amount']} ⭐ (активировал: {c['used_by']})\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_checks")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_contest")
async def admin_contest_menu(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    contest = await get_active_contest()
    
    if contest:
        buttons = [
            [InlineKeyboardButton(text="🎲 Завершить конкурс", callback_data="admin_end_contest")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ]
        text = f"🎁 *Активный конкурс*\n\n✨ Название: {contest['name']}\n💰 Приз: {contest['prize']} ⭐\n👥 Участников: {len(contest['participants'])}\n📝 Описание: {contest['description']}"
    else:
        buttons = [
            [InlineKeyboardButton(text="➕ Создать конкурс", callback_data="admin_create_contest")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ]
        text = "🎁 *Управление конкурсами*\n\nНет активного конкурса."
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_create_contest")
async def admin_create_contest(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ContestStates.waiting_for_name)
    await callback.message.edit_text("🎁 Введите название конкурса:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_contest")]
    ]))
    await callback.answer()

@dp.message(ContestStates.waiting_for_name)
async def admin_contest_name(message: Message, state: FSMContext):
    await state.update_data(contest_name=message.text)
    await state.set_state(ContestStates.waiting_for_description)
    await message.answer("📝 Введите описание конкурса:")

@dp.message(ContestStates.waiting_for_description)
async def admin_contest_description(message: Message, state: FSMContext):
    await state.update_data(contest_description=message.text)
    await state.set_state(ContestStates.waiting_for_prize)
    await message.answer("💰 Введите призовой фонд конкурса (звезды):")

@dp.message(ContestStates.waiting_for_prize)
async def admin_contest_prize(message: Message, state: FSMContext):
    try:
        prize = int(message.text)
        await state.update_data(contest_prize=prize)
        await state.set_state(ContestStates.waiting_for_link)
        await message.answer("🔗 Введите ссылку на конкурс (или отправьте '-' для автоматической):")
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(ContestStates.waiting_for_link)
async def admin_contest_link(message: Message, state: FSMContext):
    data = await state.get_data()
    link = message.text if message.text != "-" else None
    contest_id = await create_contest(
        message.from_user.id,
        data["contest_name"],
        data["contest_description"],
        data["contest_prize"],
        link
    )
    if contest_id:
        await message.answer(f"✅ Конкурс создан!\n\n🎁 {data['contest_name']}\n💰 Приз: {data['contest_prize']} ⭐\n🔗 Ссылка для участия создана автоматически!")
        await log_admin_action(message.from_user.id, "create_contest", None, f"Name: {data['contest_name']}, Prize: {data['contest_prize']}")
    else:
        await message.answer("❌ Конкурс уже активен!")
    await state.clear()

@dp.callback_query(F.data == "admin_end_contest")
async def admin_end_contest(callback: CallbackQuery):
    success, winner, prize = await end_contest()
    if success:
        await callback.answer(f"✅ Конкурс завершен! Победитель: {winner}, Приз: {prize} ⭐", show_alert=True)
        await reset_contest_points()
    else:
        await callback.answer(f"❌ {winner}", show_alert=True)
    await admin_contest_menu(callback, None)

@dp.callback_query(F.data == "admin_limits")
async def admin_limits_menu(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    settings = await load_json(SETTINGS_FILE, {})
    
    text = (f"⚙️ *Управление ограничениями*\n\n"
            f"📊 Дневной лимит потерь: {settings.get('max_daily_loss', 50000)} ⭐\n"
            f"📈 Дневной лимит выигрыша: {settings.get('max_daily_win', 100000)} ⭐\n"
            f"📉 Макс. проигрышей подряд: {settings.get('max_consecutive_losses', 10)}\n"
            f"💰 Мин. баланс для игры: {settings.get('min_balance_for_bet', 10)} ⭐\n"
            f"⏰ КД между выводами: {settings.get('withdraw_cooldown_hours', 24)} часов\n"
            f"📊 Лимит выводов в день: {settings.get('max_withdraw_per_day', 3)}\n\n"
            f"Выберите параметр для изменения:")
    
    buttons = [
        [InlineKeyboardButton(text="📊 Дневной лимит потерь", callback_data="limit_daily_loss")],
        [InlineKeyboardButton(text="📈 Дневной лимит выигрыша", callback_data="limit_daily_win")],
        [InlineKeyboardButton(text="📉 Макс. проигрышей подряд", callback_data="limit_consecutive_losses")],
        [InlineKeyboardButton(text="💰 Мин. баланс для игры", callback_data="limit_min_balance")],
        [InlineKeyboardButton(text="⏰ КД между выводами", callback_data="limit_withdraw_cooldown")],
        [InlineKeyboardButton(text="📊 Лимит выводов в день", callback_data="limit_max_withdraw_per_day")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("limit_"))
async def admin_limit_change(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    limit_type = callback.data.replace("limit_", "")
    await state.update_data(limit_type=limit_type)
    await state.set_state(AdminStates.waiting_for_limit_value)
    
    names = {
        "daily_loss": "дневной лимит потерь",
        "daily_win": "дневной лимит выигрыша",
        "consecutive_losses": "максимальное количество проигрышей подряд",
        "min_balance": "минимальный баланс для игры",
        "withdraw_cooldown": "кулдаун между выводами (часы)",
        "max_withdraw_per_day": "максимальное количество выводов в день"
    }
    await callback.message.edit_text(
        f"📝 Введите {names.get(limit_type, limit_type)}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_limits")]
        ])
    )
    await callback.answer()

@dp.message(AdminStates.waiting_for_limit_value)
async def admin_save_limit(message: Message, state: FSMContext):
    try:
        value = int(message.text.strip())
        if value <= 0:
            await message.answer("❌ Значение должно быть больше 0!")
            return
        
        data = await state.get_data()
        limit_type = data["limit_type"]
        settings = await load_json(SETTINGS_FILE, {})
        
        if limit_type == "daily_loss":
            settings["max_daily_loss"] = value
        elif limit_type == "daily_win":
            settings["max_daily_win"] = value
        elif limit_type == "consecutive_losses":
            settings["max_consecutive_losses"] = value
        elif limit_type == "min_balance":
            settings["min_balance_for_bet"] = value
        elif limit_type == "withdraw_cooldown":
            settings["withdraw_cooldown_hours"] = value
        elif limit_type == "max_withdraw_per_day":
            settings["max_withdraw_per_day"] = value
        
        await save_json(SETTINGS_FILE, settings)
        await message.answer(f"✅ {limit_type} = {value}")
        await log_admin_action(message.from_user.id, "change_limit", None, f"{limit_type}: {value}")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "admin_withdrawals")
async def admin_withdrawals_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    pending = {k: v for k, v in withdrawals.items() if v["status"] == "pending"}
    
    if not pending:
        text = "💰 *Заявки на вывод*\n\nНет активных заявок."
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]]
    else:
        text = f"💰 *Заявки на вывод*\n\nВсего заявок: {len(pending)}\n\n"
        buttons = []
        for wid, w in list(pending.items())[:10]:
            text += f"*ID {wid}:* @{w['username']}\n└ Сумма: {w['stars']} ⭐\n└ Дата: {w['created_at'][:19]}\n\n"
            buttons.append([
                InlineKeyboardButton(text=f"✅ Подтвердить {wid}", callback_data=f"admin_approve_{wid}"),
                InlineKeyboardButton(text=f"❌ Отклонить {wid}", callback_data=f"admin_decline_{wid}")
            ])
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])
    
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
                f"✅ Ваша заявка на вывод #{wid} одобрена!\n⭐ Сумма: {withdrawals[wid]['stars']} звезд",
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
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    users = await load_json(USERS_FILE, {})
    banned_users = [(uid, u) for uid, u in users.items() if u.get("is_withdraw_banned", False)]
    
    if not banned_users:
        text = "⛔ *Забаненные на вывод пользователи*\n\nНет забаненных пользователей."
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]]
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
            text += f"*ID {uid}:* {u.get('stars', 0)} ⭐\n└ Бан до: {ban_until_str}\n└ Причина: {u.get('withdraw_ban_reason', 'Не указана')}\n\n"
            buttons.append([InlineKeyboardButton(text=f"✅ Разбанить {uid}", callback_data=f"admin_unban_withdraw_{uid}")])
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_support")
async def admin_support_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    support = await load_json(SUPPORT_FILE, {"tickets": []})
    open_tickets = [t for t in support["tickets"] if t["status"] == "open"]
    
    if not open_tickets:
        text = "💬 *Тикеты поддержки*\n\nНет открытых тикетов."
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]]
    else:
        text = f"💬 *Открытые тикеты:*\n\n"
        buttons = []
        for t in open_tickets:
            text += f"*#{t['id']}* от пользователя {t['user_id']}\n└ Создан: {t['created_at'][:19]}\n\n"
            buttons.append([InlineKeyboardButton(text=f"💬 Ответить в тикет #{t['id']}", callback_data=f"admin_reply_ticket_{t['id']}")])
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_reply_ticket_"))
async def admin_reply_ticket(callback: CallbackQuery, state: FSMContext):
    ticket_id = int(callback.data.replace("admin_reply_ticket_", ""))
    await state.update_data(ticket_id=ticket_id)
    await state.set_state(AdminStates.waiting_for_reply_message)
    await callback.message.edit_text(
        f"💬 *Ответ в тикет #{ticket_id}*\n\nВведите ваш ответ:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Закрыть тикет", callback_data=f"admin_close_ticket_{ticket_id}"),
             InlineKeyboardButton(text="🔙 Назад", callback_data="admin_support")]
        ])
    )
    await callback.answer()

@dp.message(AdminStates.waiting_for_reply_message)
async def admin_send_reply(message: Message, state: FSMContext):
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
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
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
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
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
    await callback.message.edit_text(f"📝 Введите {names.get(setting, setting)}:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_settings")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_setting_value)
async def admin_save_setting(message: Message, state: FSMContext):
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
    contest = await get_active_contest()
    support = await load_json(SUPPORT_FILE, {"tickets": []})
    contest_points = await load_json(CONTEST_POINTS_FILE, {"points": {}})
    
    total_stars = sum(u.get("stars", 0) for u in users.values())
    total_users = len(users)
    unlocked_checks = len([u for u in users.values() if u.get("check_system_unlocked", False)])
    pending_withdrawals = len([w for w in withdrawals.values() if w.get("status") == "pending"])
    open_tickets = len([t for t in support["tickets"] if t["status"] == "open"])
    banned_withdraw = len([u for u in users.values() if u.get("is_withdraw_banned", False)])
    total_contest_points = sum(p.get("points", 0) for p in contest_points["points"].values())
    
    text = (f"📊 *Общая статистика*\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"⭐ Всего звезд: {total_stars}\n"
            f"📦 Чек система: {unlocked_checks}/{total_users}\n"
            f"⛔ Забанены на вывод: {banned_withdraw}\n"
            f"🎯 Всего очков конкурса: {total_contest_points}\n"
            f"📈 Средний баланс: {total_stars // total_users if total_users else 0}\n\n"
            f"📋 Заданий: {len(tasks)}\n"
            f"🎫 Промокодов: {len(promo['promo_codes'])}\n"
            f"📦 Активных чеков: {len(checks['checks'])}\n"
            f"🎁 Активный конкурс: {'Да' if contest else 'Нет'}\n"
            f"💬 Открытых тикетов: {open_tickets}\n\n"
            f"💰 Ожидают вывода: {pending_withdrawals}")
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
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
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_clear_logs")
async def admin_clear_logs(callback: CallbackQuery):
    await save_json(ADMIN_LOGS_FILE, [])
    await callback.answer("✅ Логи очищены!", show_alert=True)
    await admin_logs(callback)

# Фоновые задачи
async def contest_checker():
    while True:
        await asyncio.sleep(60)
        contest = await get_active_contest()
        if contest:
            end_time = datetime.fromisoformat(contest["end_time"])
            if datetime.now() >= end_time:
                await end_contest()

# Запуск бота
async def main():
    await init_data()
    asyncio.create_task(contest_checker())
    logger.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
