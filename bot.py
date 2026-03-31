import asyncio
import json
import os
import random
import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import aiofiles

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery, SuccessfulPayment
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
ACHIEVEMENTS_FILE = os.path.join(DATA_DIR, "achievements.json")
TOURNAMENTS_FILE = os.path.join(DATA_DIR, "tournaments.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
ADMIN_LOGS_FILE = os.path.join(DATA_DIR, "admin_logs.json")
SUPPORT_FILE = os.path.join(DATA_DIR, "support.json")
LOTTERY_FILE = os.path.join(DATA_DIR, "lottery.json")

os.makedirs(DATA_DIR, exist_ok=True)

# FSM States
class GameStates(StatesGroup):
    waiting_for_bet = State()
    playing_coinflip = State()
    playing_dice = State()
    playing_rps = State()
    playing_roulette = State()
    playing_poker = State()
    playing_baccarat = State()
    playing_blackjack = State()
    playing_crash = State()
    playing_mines = State()
    playing_keno = State()
    playing_plinko = State()
    playing_wheel = State()
    playing_hi_lo = State()

class CasinoStates(StatesGroup):
    waiting_for_bet = State()
    waiting_dice_choice = State()
    waiting_roulette_choice = State()
    waiting_keno_choice = State()
    waiting_plinko_drop = State()
    waiting_wheel_spin = State()
    waiting_hi_lo_choice = State()

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_stars_amount = State()
    waiting_for_action = State()
    waiting_for_task_name = State()
    waiting_for_task_link = State()
    waiting_for_task_reward = State()
    waiting_for_promo_code = State()
    waiting_for_promo_reward = State()
    waiting_for_promo_limit = State()
    waiting_for_check_amount = State()
    waiting_for_setting = State()
    waiting_for_setting_value = State()
    waiting_for_tournament_name = State()
    waiting_for_tournament_prize = State()
    waiting_for_tournament_duration = State()
    waiting_for_withdrawal_action = State()
    waiting_for_check_code = State()
    waiting_for_lottery_prize = State()

class PromoStates(StatesGroup):
    waiting_for_promo_code = State()

class CheckStates(StatesGroup):
    waiting_for_check_code = State()

class SupportStates(StatesGroup):
    waiting_for_message = State()

class BuyStates(StatesGroup):
    waiting_for_amount = State()

class LotteryStates(StatesGroup):
    waiting_for_ticket_count = State()

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
            "casino_enabled": True,
            "tournament_enabled": True,
            "min_bet": 1,
            "max_bet": 10000,
            "check_system_price": 100,
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
            "casino_wins": 0,
            "casino_losses": 0,
            "achievements": [],
            "tournament_points": 0,
            "check_system_unlocked": False,
            "created_at": datetime.now().isoformat()
        }
        updated = False
        for field, default_value in required_fields.items():
            if field not in user_data:
                user_data[field] = default_value
                updated = True
        if updated:
            await save_json(USERS_FILE, users)
    
    tasks = await load_json(TASKS_FILE, {"sponsor_tasks": [], "completed_tasks": {}})
    checks = await load_json(CHECKS_FILE, {"checks": [], "used_checks": []})
    promo = await load_json(PROMO_FILE, {"promo_codes": [], "used_promo": {}})
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    tournaments = await load_json(TOURNAMENTS_FILE, {"active": None, "history": []})
    admin_logs = await load_json(ADMIN_LOGS_FILE, [])
    support = await load_json(SUPPORT_FILE, {"tickets": [], "messages": {}})
    lottery = await load_json(LOTTERY_FILE, {"active": None, "history": []})
    
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
            "casino_wins": 0,
            "casino_losses": 0,
            "achievements": [],
            "tournament_points": 0,
            "check_system_unlocked": False,
            "created_at": datetime.now().isoformat()
        }
        await save_json(USERS_FILE, users)
    
    return users[user_id_str]

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
    
    if "покупка" in reason.lower():
        await add_referral_commission(user_id, amount)
    
    await check_achievements(user_id)

async def remove_stars(user_id: int, amount: int, reason: str = "") -> bool:
    user = await get_user(user_id)
    if user["stars"] >= amount:
        new_stars = user["stars"] - amount
        await update_user(user_id, stars=new_stars, total_spent=user["total_spent"] + amount)
        logger.info(f"User {user_id} spent {amount} stars. Reason: {reason}")
        return True
    return False

async def add_referral_commission(user_id: int, purchase_amount: int):
    user = await get_user(user_id)
    settings = await load_json(SETTINGS_FILE, {})
    referrer_id = user.get("referrer")
    
    if referrer_id:
        commission = int(purchase_amount * settings.get("referral_percent", 10) / 100)
        if commission > 0:
            await add_stars(referrer_id, commission, f"Реферальная комиссия от {user_id}")
            referrer = await get_user(referrer_id)
            await update_user(referrer_id, referral_earnings=referrer["referral_earnings"] + commission)

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

# Система достижений
async def check_achievements(user_id: int):
    user = await get_user(user_id)
    
    achievements = {
        "millionaire": {"name": "💰 Миллионер", "description": "Накопить 1,000,000 звезд", 
                       "condition": user["total_earned"] >= 1000000, "reward": 100000},
        "high_roller": {"name": "🎲 Высокий игрок", "description": "Сыграть 1000 игр",
                       "condition": user["games_played"] >= 1000, "reward": 50000},
        "lucky": {"name": "🍀 Счастливчик", "description": "Выиграть 100 игр",
                 "condition": user["games_won"] >= 100, "reward": 25000},
        "casino_king": {"name": "👑 Король казино", "description": "Выиграть 500 раз в казино",
                       "condition": user["casino_wins"] >= 500, "reward": 75000},
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

# Система чеков
async def unlock_check_system(user_id: int) -> bool:
    settings = await load_json(SETTINGS_FILE, {})
    price = settings.get("check_system_price", 100)
    
    if await remove_stars(user_id, price, "Открытие системы чеков"):
        await update_user(user_id, check_system_unlocked=True)
        return True
    return False

async def create_check(user_id: int, amount: int) -> Tuple[bool, str, str]:
    settings = await load_json(SETTINGS_FILE, {})
    min_check = 100
    max_check = 100000
    
    user = await get_user(user_id)
    if not user.get("check_system_unlocked", False):
        return False, f"Система чеков заблокирована! Откройте за {settings.get('check_system_price', 100)} ⭐", ""
    
    if amount < min_check:
        return False, f"Минимальная сумма чека: {min_check} ⭐", ""
    if amount > max_check:
        return False, f"Максимальная сумма чека: {max_check} ⭐", ""
    
    if user["stars"] < amount:
        return False, f"Недостаточно звезд! У вас {user['stars']} ⭐", ""
    
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
    
    return True, f"Чек создан!", code

async def use_check(user_id: int, code: str) -> Tuple[bool, str, int]:
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

async def get_user_checks(user_id: int) -> List[dict]:
    checks = await load_json(CHECKS_FILE, {"checks": [], "used_checks": []})
    user_checks = []
    for check in checks["checks"]:
        if check.get("creator") == user_id:
            user_checks.append(check)
    for check in checks["used_checks"]:
        if check.get("creator") == user_id:
            user_checks.append(check)
    return user_checks

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
        return False, f"❌ Ошибка проверки!"

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

# Лотерейная система
async def create_lottery(admin_id: int, prize_pool: int) -> int:
    lottery = await load_json(LOTTERY_FILE, {"active": None, "history": []})
    
    if lottery["active"]:
        return 0
    
    lottery_id = len(lottery["history"]) + 1
    lottery["active"] = {
        "id": lottery_id,
        "prize_pool": prize_pool,
        "tickets": [],
        "created_at": datetime.now().isoformat(),
        "end_time": (datetime.now() + timedelta(hours=24)).isoformat(),
        "created_by": admin_id
    }
    await save_json(LOTTERY_FILE, lottery)
    await log_admin_action(admin_id, "create_lottery", None, f"Prize: {prize_pool}")
    return lottery_id

async def buy_lottery_ticket(user_id: int, ticket_count: int) -> Tuple[bool, str, int]:
    lottery = await load_json(LOTTERY_FILE, {"active": None})
    
    if not lottery["active"]:
        return False, "Нет активной лотереи!", 0
    
    ticket_price = 50
    total_cost = ticket_count * ticket_price
    
    user = await get_user(user_id)
    if user["stars"] < total_cost:
        return False, f"Недостаточно звезд! Нужно {total_cost} ⭐", 0
    
    await remove_stars(user_id, total_cost, f"Покупка билетов лотереи")
    
    ticket_numbers = []
    for _ in range(ticket_count):
        ticket_num = len(lottery["active"]["tickets"]) + 1
        lottery["active"]["tickets"].append({
            "user_id": user_id,
            "ticket_number": ticket_num,
            "purchased_at": datetime.now().isoformat()
        })
        ticket_numbers.append(ticket_num)
    
    await save_json(LOTTERY_FILE, lottery)
    return True, f"✅ Куплено {ticket_count} билетов!", ticket_numbers

async def get_lottery_info() -> Tuple[bool, dict]:
    lottery = await load_json(LOTTERY_FILE, {"active": None})
    if lottery["active"]:
        end_time = datetime.fromisoformat(lottery["active"]["end_time"])
        time_left = end_time - datetime.now()
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        return True, {
            "prize_pool": lottery["active"]["prize_pool"],
            "tickets_count": len(lottery["active"]["tickets"]),
            "hours_left": hours,
            "minutes_left": minutes,
            "ticket_price": 50
        }
    return False, {}

async def end_lottery() -> Tuple[bool, str, dict]:
    lottery = await load_json(LOTTERY_FILE, {"active": None, "history": []})
    
    if not lottery["active"]:
        return False, "Нет активной лотереи!", {}
    
    tickets = lottery["active"]["tickets"]
    if not tickets:
        lottery["active"]["ended_at"] = datetime.now().isoformat()
        lottery["history"].append(lottery["active"])
        lottery["active"] = None
        await save_json(LOTTERY_FILE, lottery)
        return False, "Нет купленных билетов!", {}
    
    winner_index = random.randint(0, len(tickets) - 1)
    winner = tickets[winner_index]
    prize = lottery["active"]["prize_pool"]
    
    await add_stars(winner["user_id"], prize, f"Выигрыш в лотерее")
    
    lottery["active"]["winner"] = winner
    lottery["active"]["ended_at"] = datetime.now().isoformat()
    lottery["history"].append(lottery["active"])
    lottery["active"] = None
    
    await save_json(LOTTERY_FILE, lottery)
    
    try:
        await bot.send_message(
            winner["user_id"],
            f"🎉 *ПОЗДРАВЛЯЕМ!*\n\nВы выиграли в лотерее!\n🏆 Приз: {prize} ⭐\n🎫 Билет #{winner['ticket_number']}",
            parse_mode="Markdown"
        )
    except:
        pass
    
    return True, f"Победитель: {winner['user_id']}, Приз: {prize} ⭐", winner

# Система турниров
async def create_tournament(admin_id: int, name: str, prize_pool: int, duration_hours: int):
    tournaments = await load_json(TOURNAMENTS_FILE, {"active": None, "history": []})
    
    tournament = {
        "id": len(tournaments["history"]) + 1,
        "name": name,
        "prize_pool": prize_pool,
        "duration_hours": duration_hours,
        "start_time": datetime.now().isoformat(),
        "end_time": (datetime.now() + timedelta(hours=duration_hours)).isoformat(),
        "participants": {},
        "active": True,
        "created_by": admin_id
    }
    
    tournaments["active"] = tournament
    await save_json(TOURNAMENTS_FILE, tournaments)
    await log_admin_action(admin_id, "create_tournament", None, f"Name: {name}, Prize: {prize_pool}")

async def update_tournament_points(user_id: int, points: int):
    tournaments = await load_json(TOURNAMENTS_FILE, {"active": None, "history": []})
    settings = await load_json(SETTINGS_FILE, {})
    
    if tournaments["active"] and settings.get("tournament_enabled", True):
        user_id_str = str(user_id)
        if user_id_str not in tournaments["active"]["participants"]:
            tournaments["active"]["participants"][user_id_str] = 0
        tournaments["active"]["participants"][user_id_str] += points
        await save_json(TOURNAMENTS_FILE, tournaments)
        
        user = await get_user(user_id)
        await update_user(user_id, tournament_points=user["tournament_points"] + points)

async def end_tournament():
    tournaments = await load_json(TOURNAMENTS_FILE, {"active": None, "history": []})
    
    if tournaments["active"]:
        participants = tournaments["active"]["participants"]
        sorted_participants = sorted(participants.items(), key=lambda x: x[1], reverse=True)
        
        prize_pool = tournaments["active"]["prize_pool"]
        winners = []
        
        for i, (user_id, points) in enumerate(sorted_participants[:3]):
            if i == 0:
                prize = int(prize_pool * 0.5)
            elif i == 1:
                prize = int(prize_pool * 0.3)
            else:
                prize = int(prize_pool * 0.2)
            
            await add_stars(int(user_id), prize, f"Приз турнира {tournaments['active']['name']}")
            winners.append((user_id, prize, points))
        
        tournaments["active"]["winners"] = winners
        tournaments["active"]["ended_at"] = datetime.now().isoformat()
        tournaments["history"].append(tournaments["active"])
        tournaments["active"] = None
        
        await save_json(TOURNAMENTS_FILE, tournaments)
        
        for user_id, prize, points in winners:
            try:
                await bot.send_message(
                    int(user_id),
                    f"🏆 *Турнир завершен!*\n\n✨ {tournaments['history'][-1]['name']}\n📊 Ваше место: {[w[0] for w in winners].index(user_id) + 1}\n🎁 Приз: {prize} ⭐",
                    parse_mode="Markdown"
                )
            except:
                pass

async def get_active_tournament() -> Optional[dict]:
    tournaments = await load_json(TOURNAMENTS_FILE, {"active": None})
    return tournaments["active"]

async def get_tournament_history() -> List[dict]:
    tournaments = await load_json(TOURNAMENTS_FILE, {"history": []})
    return tournaments["history"]

# ИГРЫ (13 игр)
GAMES = {
    "coinflip": {"name": "🎲 Орёл или Решка", "min_bet": 1, "max_bet": 1000, "multiplier": 1.95},
    "dice": {"name": "🎲 Кости", "min_bet": 1, "max_bet": 500, "multiplier": 5.5},
    "rps": {"name": "✊ КНБ", "min_bet": 1, "max_bet": 500, "multiplier": 2.7},
    "roulette": {"name": "🎡 Рулетка", "min_bet": 5, "max_bet": 2000, "multiplier": 1.95},
    "poker": {"name": "🃏 Покер", "min_bet": 10, "max_bet": 5000, "multiplier": 2.2},
    "baccarat": {"name": "🎴 Баккара", "min_bet": 10, "max_bet": 5000, "multiplier": 1.95},
    "blackjack": {"name": "🃏 Блэкджек", "min_bet": 5, "max_bet": 3000, "multiplier": 2.1},
    "crash": {"name": "💥 Crash", "min_bet": 5, "max_bet": 2000, "multiplier": 1.5},
    "mines": {"name": "💣 Mines", "min_bet": 10, "max_bet": 1000, "multiplier": 2.5},
    "keno": {"name": "🎯 Кено", "min_bet": 5, "max_bet": 1000, "multiplier": 3.0},
    "plinko": {"name": "📌 Плинко", "min_bet": 5, "max_bet": 2000, "multiplier": 2.0},
    "wheel": {"name": "🎡 Колесо фортуны", "min_bet": 10, "max_bet": 5000, "multiplier": 2.5},
    "hi_lo": {"name": "⬆️ Выше/Ниже", "min_bet": 5, "max_bet": 1000, "multiplier": 1.9}
}

# Реализация новых игр
async def play_keno(user_id: int, bet: int) -> Tuple[bool, int, str]:
    numbers = list(range(1, 81))
    chosen = random.sample(numbers, 10)
    drawn = random.sample(numbers, 20)
    hits = len(set(chosen) & set(drawn))
    
    multipliers = {0: 0, 1: 0, 2: 0, 3: 0.5, 4: 1, 5: 2, 6: 5, 7: 10, 8: 25, 9: 50, 10: 100}
    multiplier = multipliers.get(hits, 0)
    
    if multiplier > 0:
        winnings = int(bet * multiplier)
        await add_stars(user_id, winnings, f"Выигрыш в Кено")
        await update_tournament_points(user_id, winnings)
        user = await get_user(user_id)
        await update_user(user_id, games_won=user["games_won"] + 1)
        return True, winnings, f"🎯 Попаданий: {hits}/10\n💰 Выигрыш: {winnings} ⭐ (x{multiplier})!"
    else:
        await update_tournament_points(user_id, bet)
        return False, bet, f"🎯 Попаданий: {hits}/10\n😔 Проигрыш: {bet} ⭐"

async def play_plinko(user_id: int, bet: int) -> Tuple[bool, int, str]:
    multipliers = [0.2, 0.5, 1, 2, 5, 10, 5, 2, 1, 0.5, 0.2]
    result = random.choice(multipliers)
    
    if result > 1:
        winnings = int(bet * result)
        await add_stars(user_id, winnings, f"Выигрыш в Плинко")
        await update_tournament_points(user_id, winnings)
        user = await get_user(user_id)
        await update_user(user_id, games_won=user["games_won"] + 1)
        return True, winnings, f"📌 Мяч упал на x{result}!\n💰 Выигрыш: {winnings} ⭐!"
    else:
        await update_tournament_points(user_id, bet)
        return False, bet, f"📌 Мяч упал на x{result}!\n😔 Проигрыш: {bet} ⭐"

async def play_wheel(user_id: int, bet: int) -> Tuple[bool, int, str]:
    segments = [0.5, 1, 1.5, 2, 2.5, 3, 5, 7.5, 10, 15, 20, 25]
    result = random.choice(segments)
    
    if result >= 1:
        winnings = int(bet * result)
        await add_stars(user_id, winnings, f"Выигрыш в Колесе фортуны")
        await update_tournament_points(user_id, winnings)
        user = await get_user(user_id)
        await update_user(user_id, games_won=user["games_won"] + 1)
        return True, winnings, f"🎡 Колесо остановилось на x{result}!\n💰 Выигрыш: {winnings} ⭐!"
    else:
        await update_tournament_points(user_id, bet)
        return False, bet, f"🎡 Колесо остановилось на x{result}!\n😔 Проигрыш: {bet} ⭐"

async def play_hi_lo(user_id: int, bet: int, choice: str) -> Tuple[bool, int, str]:
    current = random.randint(1, 13)
    next_card = random.randint(1, 13)
    
    if choice == "higher":
        win = next_card > current
    else:
        win = next_card < current
    
    if win:
        winnings = int(bet * 1.9)
        await add_stars(user_id, winnings, f"Выигрыш в Выше/Ниже")
        await update_tournament_points(user_id, winnings)
        user = await get_user(user_id)
        await update_user(user_id, games_won=user["games_won"] + 1)
        return True, winnings, f"🃏 Текущая карта: {current}\n🃏 Следующая: {next_card}\n🎉 Вы угадали! Выигрыш: {winnings} ⭐!"
    else:
        await update_tournament_points(user_id, bet)
        return False, bet, f"🃏 Текущая карта: {current}\n🃏 Следующая: {next_card}\n😔 Проигрыш: {bet} ⭐"

# Реализация основных игр
async def play_coinflip(user_id: int, bet: int, choice: str) -> Tuple[bool, int, str]:
    result = random.choice(["eagle", "tails"])
    win = (choice == result)
    
    if win:
        winnings = int(bet * 1.95)
        await add_stars(user_id, winnings, f"Выигрыш в Орёл/Решка")
        await update_tournament_points(user_id, winnings)
        user = await get_user(user_id)
        await update_user(user_id, games_won=user["games_won"] + 1)
        return True, winnings, f"🦅 Вы выбрали: {'Орёл' if choice == 'eagle' else 'Решка'}\n🎲 Выпало: {'Орёл' if result == 'eagle' else 'Решка'}\n\n🎉 Вы выиграли {winnings} ⭐!"
    else:
        await update_tournament_points(user_id, bet)
        return False, bet, f"🦅 Вы выбрали: {'Орёл' if choice == 'eagle' else 'Решка'}\n🎲 Выпало: {'Орёл' if result == 'eagle' else 'Решка'}\n\n😔 Вы проиграли {bet} ⭐"

async def play_dice(user_id: int, bet: int, choice: int) -> Tuple[bool, int, str]:
    result = random.randint(1, 6)
    win = (choice == result)
    
    if win:
        winnings = int(bet * 5.5)
        await add_stars(user_id, winnings, f"Выигрыш в Кости")
        await update_tournament_points(user_id, winnings)
        user = await get_user(user_id)
        await update_user(user_id, games_won=user["games_won"] + 1)
        return True, winnings, f"🎲 Ваше число: {choice}\n🎲 Выпало: {result}\n\n🎉 Вы угадали! Выигрыш: {winnings} ⭐!"
    else:
        await update_tournament_points(user_id, bet)
        return False, bet, f"🎲 Ваше число: {choice}\n🎲 Выпало: {result}\n\n😔 Проигрыш: {bet} ⭐"

async def play_rps(user_id: int, bet: int, choice: str) -> Tuple[bool, int, str]:
    bot_choice = random.choice(["rock", "scissors", "paper"])
    choice_map = {"rock": "✊", "scissors": "✌️", "paper": "✋"}
    
    if choice == bot_choice:
        await add_stars(user_id, bet, f"Ничья в КНБ")
        return True, bet, f"✊ Ваш ход: {choice_map[choice]}\n🤖 Ход бота: {choice_map[bot_choice]}\n\n🤝 Ничья! Ставка возвращена."
    elif (choice == "rock" and bot_choice == "scissors") or \
         (choice == "scissors" and bot_choice == "paper") or \
         (choice == "paper" and bot_choice == "rock"):
        winnings = int(bet * 2.7)
        await add_stars(user_id, winnings, f"Выигрыш в КНБ")
        await update_tournament_points(user_id, winnings)
        user = await get_user(user_id)
        await update_user(user_id, games_won=user["games_won"] + 1)
        return True, winnings, f"✊ Ваш ход: {choice_map[choice]}\n🤖 Ход бота: {choice_map[bot_choice]}\n\n🎉 Выигрыш: {winnings} ⭐!"
    else:
        await update_tournament_points(user_id, bet)
        return False, bet, f"✊ Ваш ход: {choice_map[choice]}\n🤖 Ход бота: {choice_map[bot_choice]}\n\n😔 Проигрыш: {bet} ⭐"

async def play_roulette(user_id: int, bet: int, choice: str) -> Tuple[bool, int, str]:
    numbers = list(range(37))
    result = random.choice(numbers)
    
    if choice == "red":
        red_numbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        win = result in red_numbers and result != 0
        if win:
            winnings = int(bet * 1.95)
            await add_stars(user_id, winnings, f"Выигрыш в Рулетке")
            await update_tournament_points(user_id, winnings)
            user = await get_user(user_id)
            await update_user(user_id, games_won=user["games_won"] + 1)
            return True, winnings, f"🎡 Выпало: {result} (Красное)\n\n🎉 Вы выиграли {winnings} ⭐!"
        else:
            await update_tournament_points(user_id, bet)
            color = "Черное" if result != 0 else "Зеро"
            return False, bet, f"🎡 Выпало: {result} ({color})\n\n😔 Проигрыш: {bet} ⭐"
    elif choice == "black":
        black_numbers = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]
        win = result in black_numbers
        if win:
            winnings = int(bet * 1.95)
            await add_stars(user_id, winnings, f"Выигрыш в Рулетке")
            await update_tournament_points(user_id, winnings)
            user = await get_user(user_id)
            await update_user(user_id, games_won=user["games_won"] + 1)
            return True, winnings, f"🎡 Выпало: {result} (Черное)\n\n🎉 Вы выиграли {winnings} ⭐!"
        else:
            await update_tournament_points(user_id, bet)
            color = "Красное" if result != 0 else "Зеро"
            return False, bet, f"🎡 Выпало: {result} ({color})\n\n😔 Проигрыш: {bet} ⭐"
    elif choice == "even":
        win = result % 2 == 0 and result != 0
        if win:
            winnings = int(bet * 1.95)
            await add_stars(user_id, winnings, f"Выигрыш в Рулетке")
            await update_tournament_points(user_id, winnings)
            user = await get_user(user_id)
            await update_user(user_id, games_won=user["games_won"] + 1)
            return True, winnings, f"🎡 Выпало: {result} (Четное)\n\n🎉 Вы выиграли {winnings} ⭐!"
        else:
            await update_tournament_points(user_id, bet)
            parity = "Нечетное" if result != 0 else "Зеро"
            return False, bet, f"🎡 Выпало: {result} ({parity})\n\n😔 Проигрыш: {bet} ⭐"
    elif choice == "odd":
        win = result % 2 == 1 and result != 0
        if win:
            winnings = int(bet * 1.95)
            await add_stars(user_id, winnings, f"Выигрыш в Рулетке")
            await update_tournament_points(user_id, winnings)
            user = await get_user(user_id)
            await update_user(user_id, games_won=user["games_won"] + 1)
            return True, winnings, f"🎡 Выпало: {result} (Нечетное)\n\n🎉 Вы выиграли {winnings} ⭐!"
        else:
            await update_tournament_points(user_id, bet)
            parity = "Четное" if result != 0 else "Зеро"
            return False, bet, f"🎡 Выпало: {result} ({parity})\n\n😔 Проигрыш: {bet} ⭐"
    return False, bet, "Ошибка"

async def play_poker(user_id: int, bet: int) -> Tuple[bool, int, str]:
    hands = ["High Card", "Pair", "Two Pair", "Three of Kind", "Straight", "Flush", "Full House", "Four of Kind", "Straight Flush", "Royal Flush"]
    weights = [50, 25, 15, 8, 5, 3, 2, 1, 0.5, 0.2]
    multipliers = [0, 1, 2, 3, 5, 8, 12, 20, 50, 100]
    
    hand = random.choices(hands, weights=weights)[0]
    idx = hands.index(hand)
    multiplier = multipliers[idx]
    
    if multiplier > 0:
        winnings = int(bet * multiplier)
        await add_stars(user_id, winnings, f"Выигрыш в Покере")
        await update_tournament_points(user_id, winnings)
        user = await get_user(user_id)
        await update_user(user_id, games_won=user["games_won"] + 1)
        return True, winnings, f"🃏 Ваша комбинация: {hand}\n\n🎉 Вы выиграли {winnings} ⭐ (x{multiplier})!"
    else:
        await update_tournament_points(user_id, bet)
        return False, bet, f"🃏 Ваша комбинация: {hand}\n\n😔 Проигрыш: {bet} ⭐"

async def play_baccarat(user_id: int, bet: int, choice: str) -> Tuple[bool, int, str]:
    player = random.randint(0, 9)
    banker = random.randint(0, 9)
    
    if choice == "player":
        win = player > banker
        if win:
            winnings = int(bet * 1.95)
            await add_stars(user_id, winnings, f"Выигрыш в Баккаре")
            await update_tournament_points(user_id, winnings)
            user = await get_user(user_id)
            await update_user(user_id, games_won=user["games_won"] + 1)
            return True, winnings, f"🎴 Игрок: {player} | Банкир: {banker}\n\n🎉 Вы выиграли {winnings} ⭐!"
        else:
            await update_tournament_points(user_id, bet)
            return False, bet, f"🎴 Игрок: {player} | Банкир: {banker}\n\n😔 Проигрыш: {bet} ⭐"
    elif choice == "banker":
        win = banker > player
        if win:
            winnings = int(bet * 1.95)
            await add_stars(user_id, winnings, f"Выигрыш в Баккаре")
            await update_tournament_points(user_id, winnings)
            user = await get_user(user_id)
            await update_user(user_id, games_won=user["games_won"] + 1)
            return True, winnings, f"🎴 Игрок: {player} | Банкир: {banker}\n\n🎉 Вы выиграли {winnings} ⭐!"
        else:
            await update_tournament_points(user_id, bet)
            return False, bet, f"🎴 Игрок: {player} | Банкир: {banker}\n\n😔 Проигрыш: {bet} ⭐"
    else:
        if player == banker:
            await add_stars(user_id, bet, f"Ничья в Баккаре")
            return True, bet, f"🎴 Игрок: {player} | Банкир: {banker}\n\n🤝 Ничья! Ставка возвращена."
        else:
            await update_tournament_points(user_id, bet)
            return False, bet, f"🎴 Игрок: {player} | Банкир: {banker}\n\n😔 Проигрыш: {bet} ⭐"

async def play_blackjack(user_id: int, bet: int) -> Tuple[bool, int, str]:
    player_cards = [random.randint(1, 11), random.randint(1, 11)]
    dealer_cards = [random.randint(1, 11), random.randint(1, 11)]
    
    player_sum = sum(player_cards)
    dealer_sum = sum(dealer_cards)
    
    if player_sum == 21:
        winnings = int(bet * 2.1)
        await add_stars(user_id, winnings, f"Выигрыш в Блэкджек")
        await update_tournament_points(user_id, winnings)
        user = await get_user(user_id)
        await update_user(user_id, games_won=user["games_won"] + 1)
        return True, winnings, f"🃏 Ваши карты: {player_cards} (сумма: {player_sum})\n🃏 Карты дилера: {dealer_cards[0]} (?) \n\n🎉 Блэкджек! Выигрыш: {winnings} ⭐!"
    
    if dealer_sum == 21:
        await update_tournament_points(user_id, bet)
        return False, bet, f"🃏 Ваши карты: {player_cards} (сумма: {player_sum})\n🃏 Карты дилера: {dealer_cards} (сумма: {dealer_sum})\n\n😔 У дилера Блэкджек! Проигрыш: {bet} ⭐"
    
    while player_sum < 17 and player_sum < 21:
        player_cards.append(random.randint(1, 11))
        player_sum = sum(player_cards)
    
    while dealer_sum < 17:
        dealer_cards.append(random.randint(1, 11))
        dealer_sum = sum(dealer_cards)
    
    if player_sum > 21:
        await update_tournament_points(user_id, bet)
        return False, bet, f"🃏 Ваши карты: {player_cards} (сумма: {player_sum})\n🃏 Карты дилера: {dealer_cards} (сумма: {dealer_sum})\n\n😔 Перебор! Проигрыш: {bet} ⭐"
    elif dealer_sum > 21 or player_sum > dealer_sum:
        winnings = int(bet * 2.1)
        await add_stars(user_id, winnings, f"Выигрыш в Блэкджек")
        await update_tournament_points(user_id, winnings)
        user = await get_user(user_id)
        await update_user(user_id, games_won=user["games_won"] + 1)
        return True, winnings, f"🃏 Ваши карты: {player_cards} (сумма: {player_sum})\n🃏 Карты дилера: {dealer_cards} (сумма: {dealer_sum})\n\n🎉 Вы выиграли {winnings} ⭐!"
    elif player_sum == dealer_sum:
        await add_stars(user_id, bet, f"Ничья в Блэкджек")
        return True, bet, f"🃏 Ваши карты: {player_cards} (сумма: {player_sum})\n🃏 Карты дилера: {dealer_cards} (сумма: {dealer_sum})\n\n🤝 Ничья! Ставка возвращена."
    else:
        await update_tournament_points(user_id, bet)
        return False, bet, f"🃏 Ваши карты: {player_cards} (сумма: {player_sum})\n🃏 Карты дилера: {dealer_cards} (сумма: {dealer_sum})\n\n😔 Проигрыш: {bet} ⭐"

async def play_crash(user_id: int, bet: int) -> Tuple[bool, int, str]:
    multiplier = random.uniform(1.0, 10.0)
    cash_out_point = random.uniform(1.1, 5.0)
    
    if multiplier >= cash_out_point:
        winnings = int(bet * cash_out_point)
        await add_stars(user_id, winnings, f"Выигрыш в Crash")
        await update_tournament_points(user_id, winnings)
        user = await get_user(user_id)
        await update_user(user_id, games_won=user["games_won"] + 1)
        return True, winnings, f"💥 Множитель достиг {multiplier:.2f}x!\n💰 Вы выиграли {winnings} ⭐!"
    else:
        await update_tournament_points(user_id, bet)
        return False, bet, f"💥 Крах на {multiplier:.2f}x!\n😔 Вы проиграли {bet} ⭐"

async def play_mines(user_id: int, bet: int) -> Tuple[bool, int, str]:
    mines_count = random.randint(1, 5)
    safe_count = 25 - mines_count
    win = random.random() < (safe_count / 25)
    
    if win:
        multiplier = (safe_count / mines_count) * 1.5
        winnings = int(bet * multiplier)
        await add_stars(user_id, winnings, f"Выигрыш в Mines")
        await update_tournament_points(user_id, winnings)
        user = await get_user(user_id)
        await update_user(user_id, games_won=user["games_won"] + 1)
        return True, winnings, f"💣 Вы нашли сокровище!\n💰 Выигрыш: {winnings} ⭐!"
    else:
        await update_tournament_points(user_id, bet)
        return False, bet, f"💣 Вы наступили на мину!\n😔 Проигрыш: {bet} ⭐"

# КАЗИНО ИГРЫ (6 игр)
async def casino_slots(user_id: int, bet: int) -> Tuple[bool, int, str]:
    symbols = ["🍒", "🍋", "🍊", "🔔", "💎", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    
    win_multiplier = 0
    if result[0] == result[1] == result[2]:
        if result[0] == "7️⃣":
            win_multiplier = 6
        elif result[0] == "💎":
            win_multiplier = 3
        else:
            win_multiplier = 2
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        win_multiplier = 1.2
    
    if win_multiplier > 0:
        winnings = int(bet * win_multiplier)
        await add_stars(user_id, winnings, f"Выигрыш в казино (слоты)")
        user = await get_user(user_id)
        await update_user(user_id, casino_wins=user["casino_wins"] + 1)
        await update_tournament_points(user_id, winnings)
        return True, winnings, f"🎰 {result[0]} | {result[1]} | {result[2]}\n\n🎉 Выигрыш: {winnings} ⭐ (x{win_multiplier})!"
    else:
        user = await get_user(user_id)
        await update_user(user_id, casino_losses=user["casino_losses"] + 1)
        await update_tournament_points(user_id, bet)
        return False, bet, f"🎰 {result[0]} | {result[1]} | {result[2]}\n\n😔 Проигрыш: {bet} ⭐"

async def casino_dice(user_id: int, bet: int, choice: int) -> Tuple[bool, int, str]:
    result = random.randint(1, 6)
    
    if choice == result:
        winnings = int(bet * 5)
        await add_stars(user_id, winnings, f"Выигрыш в казино (кости)")
        user = await get_user(user_id)
        await update_user(user_id, casino_wins=user["casino_wins"] + 1)
        await update_tournament_points(user_id, winnings)
        return True, winnings, f"🎲 Ваше число: {choice}\n🎲 Выпало: {result}\n\n🎉 Вы угадали! Выигрыш: {winnings} ⭐!"
    else:
        user = await get_user(user_id)
        await update_user(user_id, casino_losses=user["casino_losses"] + 1)
        await update_tournament_points(user_id, bet)
        return False, bet, f"🎲 Ваше число: {choice}\n🎲 Выпало: {result}\n\n😔 Проигрыш: {bet} ⭐"

async def casino_roulette(user_id: int, bet: int, choice: int) -> Tuple[bool, int, str]:
    numbers = list(range(37))
    result = random.choice(numbers)
    
    if choice == result:
        winnings = int(bet * 35)
        await add_stars(user_id, winnings, f"Выигрыш в казино (рулетка)")
        user = await get_user(user_id)
        await update_user(user_id, casino_wins=user["casino_wins"] + 1)
        await update_tournament_points(user_id, winnings)
        return True, winnings, f"🎡 Выпало число {result}!\n🎉 Вы выиграли {winnings} ⭐!"
    else:
        user = await get_user(user_id)
        await update_user(user_id, casino_losses=user["casino_losses"] + 1)
        await update_tournament_points(user_id, bet)
        return False, bet, f"🎡 Выпало число {result}!\n😔 Проигрыш: {bet} ⭐"

async def casino_blackjack(user_id: int, bet: int) -> Tuple[bool, int, str]:
    player = random.randint(1, 21)
    dealer = random.randint(1, 21)
    
    if player > dealer and player <= 21:
        winnings = int(bet * 2)
        await add_stars(user_id, winnings, f"Выигрыш в казино (блэкджек)")
        user = await get_user(user_id)
        await update_user(user_id, casino_wins=user["casino_wins"] + 1)
        await update_tournament_points(user_id, winnings)
        return True, winnings, f"🃏 Игрок: {player} | Дилер: {dealer}\n🎉 Вы выиграли {winnings} ⭐!"
    elif player == dealer:
        await add_stars(user_id, bet, f"Ничья в казино")
        return True, bet, f"🃏 Игрок: {player} | Дилер: {dealer}\n🤝 Ничья! Ставка возвращена."
    else:
        user = await get_user(user_id)
        await update_user(user_id, casino_losses=user["casino_losses"] + 1)
        await update_tournament_points(user_id, bet)
        return False, bet, f"🃏 Игрок: {player} | Дилер: {dealer}\n😔 Проигрыш: {bet} ⭐"

async def casino_poker(user_id: int, bet: int) -> Tuple[bool, int, str]:
    hands = ["High Card", "Pair", "Two Pair", "Three of Kind", "Straight", "Flush", "Full House", "Four of Kind"]
    multipliers = [0, 1, 2, 3, 5, 8, 12, 20]
    
    hand = random.choice(hands)
    idx = hands.index(hand)
    multiplier = multipliers[idx]
    
    if multiplier > 0:
        winnings = int(bet * multiplier)
        await add_stars(user_id, winnings, f"Выигрыш в казино (покер)")
        user = await get_user(user_id)
        await update_user(user_id, casino_wins=user["casino_wins"] + 1)
        await update_tournament_points(user_id, winnings)
        return True, winnings, f"🃏 Комбинация: {hand}\n🎉 Вы выиграли {winnings} ⭐ (x{multiplier})!"
    else:
        user = await get_user(user_id)
        await update_user(user_id, casino_losses=user["casino_losses"] + 1)
        await update_tournament_points(user_id, bet)
        return False, bet, f"🃏 Комбинация: {hand}\n😔 Проигрыш: {bet} ⭐"

async def casino_wheel(user_id: int, bet: int) -> Tuple[bool, int, str]:
    segments = ["1x", "2x", "3x", "5x", "10x", "20x", "50x"]
    weights = [30, 25, 20, 15, 5, 3, 2]
    result = random.choices(segments, weights=weights)[0]
    multiplier = int(result.replace("x", ""))
    
    if multiplier > 1:
        winnings = int(bet * multiplier)
        await add_stars(user_id, winnings, f"Выигрыш в казино (колесо)")
        user = await get_user(user_id)
        await update_user(user_id, casino_wins=user["casino_wins"] + 1)
        await update_tournament_points(user_id, winnings)
        return True, winnings, f"🎡 Колесо показало {result}!\n🎉 Вы выиграли {winnings} ⭐!"
    else:
        user = await get_user(user_id)
        await update_user(user_id, casino_losses=user["casino_losses"] + 1)
        await update_tournament_points(user_id, bet)
        return False, bet, f"🎡 Колесо показало {result}!\n😔 Проигрыш: {bet} ⭐"

# Клавиатуры
def get_main_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🎮 Игры", callback_data="games_menu"),
         InlineKeyboardButton(text="⭐ Баланс", callback_data="stars_info")],
        [InlineKeyboardButton(text="🎰 Казино", callback_data="casino_menu"),
         InlineKeyboardButton(text="🏆 Турниры", callback_data="tournaments_menu")],
        [InlineKeyboardButton(text="📋 Задания", callback_data="tasks_menu"),
         InlineKeyboardButton(text="👥 Рефералы", callback_data="referrals_menu")],
        [InlineKeyboardButton(text="💰 Вывод", callback_data="withdraw_menu"),
         InlineKeyboardButton(text="🛒 Купить", callback_data="buy_stars")],
        [InlineKeyboardButton(text="🎫 Промокод", callback_data="use_promo"),
         InlineKeyboardButton(text="🎲 Лотерея", callback_data="lottery_menu")],
        [InlineKeyboardButton(text="📦 Чек система", callback_data="check_system_menu"),
         InlineKeyboardButton(text="💬 Поддержка", callback_data="support_menu")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
         InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Обработчик /start
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    args = message.text.split()
    if len(args) > 1:
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
    settings = await load_json(SETTINGS_FILE, {})
    
    keyboard = get_main_keyboard()
    if await is_admin(message.from_user.id):
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="⚙️ Админ панель", callback_data="admin_panel")])
    
    text = (f"✨ Добро пожаловать, {message.from_user.full_name}!\n\n"
            f"⭐ Баланс: {user['stars']} звезд\n\n"
            f"🎮 13 игр | 🎰 6 казино игр | 🏆 Турниры\n"
            f"📋 Задания на каналы (бот должен быть в канале)\n"
            f"👥 Рефералы (10% от покупок)\n"
            f"📦 Система чеков (доступ за {settings.get('check_system_price', 100)} ⭐)\n"
            f"🎲 Лотерея с крупными призами\n"
            f"💰 Вывод от {settings.get('min_withdraw', 500)} ⭐\n\n"
            f"Приятной игры! 🎉")
    
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

# Игры меню
@dp.callback_query(F.data == "games_menu")
async def games_menu(callback: CallbackQuery):
    text = "🎮 *Игры (13 игр)*\n\nВыберите игру:"
    buttons = []
    for game_id, game in GAMES.items():
        buttons.append([InlineKeyboardButton(text=game['name'], callback_data=f"game_{game_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("game_"))
async def game_start(callback: CallbackQuery, state: FSMContext):
    game_id = callback.data.replace("game_", "")
    game = GAMES[game_id]
    
    await state.update_data(game_id=game_id)
    await state.set_state(GameStates.waiting_for_bet)
    
    await callback.message.edit_text(
        f"🎮 *{game['name']}*\n\n"
        f"💰 Ставки: от {game['min_bet']} до {game['max_bet']} ⭐\n\n"
        f"Введите сумму ставки:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="games_menu")]])
    )
    await callback.answer()

@dp.message(GameStates.waiting_for_bet)
async def process_bet(message: Message, state: FSMContext):
    try:
        bet = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    game_id = data["game_id"]
    game = GAMES[game_id]
    
    user = await get_user(message.from_user.id)
    
    if bet < game["min_bet"] or bet > game["max_bet"]:
        await message.answer(f"❌ Ставка должна быть от {game['min_bet']} до {game['max_bet']} ⭐")
        return
    
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    await remove_stars(message.from_user.id, bet, f"Ставка в игре {game['name']}")
    await update_user(message.from_user.id, games_played=user["games_played"] + 1)
    await state.update_data(bet=bet)
    
    if game_id == "coinflip":
        await state.set_state(GameStates.playing_coinflip)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🦅 Орёл", callback_data="coinflip_eagle"),
             InlineKeyboardButton(text="💿 Решка", callback_data="coinflip_tails")]
        ])
        await message.answer("🎲 Выберите сторону:", reply_markup=keyboard)
    
    elif game_id == "dice":
        await state.set_state(GameStates.playing_dice)
        await message.answer("🎲 Введите число от 1 до 6:")
    
    elif game_id == "rps":
        await state.set_state(GameStates.playing_rps)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✊ Камень", callback_data="rps_rock"),
             InlineKeyboardButton(text="✌️ Ножницы", callback_data="rps_scissors"),
             InlineKeyboardButton(text="✋ Бумага", callback_data="rps_paper")]
        ])
        await message.answer("✊ Выберите ход:", reply_markup=keyboard)
    
    elif game_id == "roulette":
        await state.set_state(GameStates.playing_roulette)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔴 Красное", callback_data="roulette_red"),
             InlineKeyboardButton(text="⚫ Черное", callback_data="roulette_black")],
            [InlineKeyboardButton(text="🟢 Четное", callback_data="roulette_even"),
             InlineKeyboardButton(text="🔵 Нечетное", callback_data="roulette_odd")]
        ])
        await message.answer("🎡 Выберите ставку:", reply_markup=keyboard)
    
    elif game_id == "poker":
        await state.set_state(GameStates.playing_poker)
        win, winnings, result_text = await play_poker(message.from_user.id, bet)
        await message.answer(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🃏 Ещё раз", callback_data="game_poker"),
             InlineKeyboardButton(text="🔙 В меню", callback_data="games_menu")]
        ]))
        await state.clear()
    
    elif game_id == "baccarat":
        await state.set_state(GameStates.playing_baccarat)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Игрок", callback_data="baccarat_player"),
             InlineKeyboardButton(text="👔 Банкир", callback_data="baccarat_banker")],
            [InlineKeyboardButton(text="🤝 Ничья", callback_data="baccarat_tie")]
        ])
        await message.answer("🎴 Выберите ставку:", reply_markup=keyboard)
    
    elif game_id == "blackjack":
        await state.set_state(GameStates.playing_blackjack)
        win, winnings, result_text = await play_blackjack(message.from_user.id, bet)
        await message.answer(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🃏 Ещё раз", callback_data="game_blackjack"),
             InlineKeyboardButton(text="🔙 В меню", callback_data="games_menu")]
        ]))
        await state.clear()
    
    elif game_id == "crash":
        await state.set_state(GameStates.playing_crash)
        win, winnings, result_text = await play_crash(message.from_user.id, bet)
        await message.answer(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💥 Ещё раз", callback_data="game_crash"),
             InlineKeyboardButton(text="🔙 В меню", callback_data="games_menu")]
        ]))
        await state.clear()
    
    elif game_id == "mines":
        await state.set_state(GameStates.playing_mines)
        win, winnings, result_text = await play_mines(message.from_user.id, bet)
        await message.answer(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💣 Ещё раз", callback_data="game_mines"),
             InlineKeyboardButton(text="🔙 В меню", callback_data="games_menu")]
        ]))
        await state.clear()
    
    elif game_id == "keno":
        await state.set_state(GameStates.playing_keno)
        win, winnings, result_text = await play_keno(message.from_user.id, bet)
        await message.answer(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Ещё раз", callback_data="game_keno"),
             InlineKeyboardButton(text="🔙 В меню", callback_data="games_menu")]
        ]))
        await state.clear()
    
    elif game_id == "plinko":
        await state.set_state(GameStates.playing_plinko)
        win, winnings, result_text = await play_plinko(message.from_user.id, bet)
        await message.answer(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📌 Ещё раз", callback_data="game_plinko"),
             InlineKeyboardButton(text="🔙 В меню", callback_data="games_menu")]
        ]))
        await state.clear()
    
    elif game_id == "wheel":
        await state.set_state(GameStates.playing_wheel)
        win, winnings, result_text = await play_wheel(message.from_user.id, bet)
        await message.answer(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎡 Ещё раз", callback_data="game_wheel"),
             InlineKeyboardButton(text="🔙 В меню", callback_data="games_menu")]
        ]))
        await state.clear()
    
    elif game_id == "hi_lo":
        await state.set_state(GameStates.playing_hi_lo)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬆️ Выше", callback_data="hi_lo_higher"),
             InlineKeyboardButton(text="⬇️ Ниже", callback_data="hi_lo_lower")]
        ])
        await message.answer("🃏 Следующая карта будет выше или ниже?", reply_markup=keyboard)

@dp.callback_query(GameStates.playing_coinflip, F.data.startswith("coinflip_"))
async def coinflip_play(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("coinflip_", "")
    data = await state.get_data()
    bet = data["bet"]
    
    win, winnings, result_text = await play_coinflip(callback.from_user.id, bet, choice)
    
    await callback.message.edit_text(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Ещё раз", callback_data="game_coinflip"),
         InlineKeyboardButton(text="🔙 В меню", callback_data="games_menu")]
    ]))
    await state.clear()
    await callback.answer()

@dp.message(GameStates.playing_dice)
async def dice_play(message: Message, state: FSMContext):
    try:
        choice = int(message.text)
        if choice < 1 or choice > 6:
            await message.answer("❌ Введите число от 1 до 6!")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    bet = data["bet"]
    
    win, winnings, result_text = await play_dice(message.from_user.id, bet, choice)
    
    await message.answer(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Ещё раз", callback_data="game_dice"),
         InlineKeyboardButton(text="🔙 В меню", callback_data="games_menu")]
    ]))
    await state.clear()

@dp.callback_query(GameStates.playing_rps, F.data.startswith("rps_"))
async def rps_play(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("rps_", "")
    data = await state.get_data()
    bet = data["bet"]
    
    win, winnings, result_text = await play_rps(callback.from_user.id, bet, choice)
    
    await callback.message.edit_text(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Ещё раз", callback_data="game_rps"),
         InlineKeyboardButton(text="🔙 В меню", callback_data="games_menu")]
    ]))
    await state.clear()
    await callback.answer()

@dp.callback_query(GameStates.playing_roulette, F.data.startswith("roulette_"))
async def roulette_play(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("roulette_", "")
    data = await state.get_data()
    bet = data["bet"]
    
    win, winnings, result_text = await play_roulette(callback.from_user.id, bet, choice)
    
    await callback.message.edit_text(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎡 Ещё раз", callback_data="game_roulette"),
         InlineKeyboardButton(text="🔙 В меню", callback_data="games_menu")]
    ]))
    await state.clear()
    await callback.answer()

@dp.callback_query(GameStates.playing_baccarat, F.data.startswith("baccarat_"))
async def baccarat_play(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("baccarat_", "")
    data = await state.get_data()
    bet = data["bet"]
    
    win, winnings, result_text = await play_baccarat(callback.from_user.id, bet, choice)
    
    await callback.message.edit_text(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎴 Ещё раз", callback_data="game_baccarat"),
         InlineKeyboardButton(text="🔙 В меню", callback_data="games_menu")]
    ]))
    await state.clear()
    await callback.answer()

@dp.callback_query(GameStates.playing_hi_lo, F.data.startswith("hi_lo_"))
async def hi_lo_play(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("hi_lo_", "")
    data = await state.get_data()
    bet = data["bet"]
    
    win, winnings, result_text = await play_hi_lo(callback.from_user.id, bet, choice)
    
    await callback.message.edit_text(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬆️ Ещё раз", callback_data="game_hi_lo"),
         InlineKeyboardButton(text="🔙 В меню", callback_data="games_menu")]
    ]))
    await state.clear()
    await callback.answer()

# Казино меню
@dp.callback_query(F.data == "casino_menu")
async def casino_menu(callback: CallbackQuery):
    settings = await load_json(SETTINGS_FILE, {})
    if not settings.get("casino_enabled", True):
        await callback.answer("❌ Казино временно закрыто!", show_alert=True)
        return
    
    text = "🎰 *Казино (6 игр)*\n\nВыберите игру:"
    buttons = [
        [InlineKeyboardButton(text="🎰 Слоты", callback_data="casino_slots"),
         InlineKeyboardButton(text="🎲 Кости", callback_data="casino_dice")],
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data="casino_roulette"),
         InlineKeyboardButton(text="🃏 Блэкджек", callback_data="casino_blackjack")],
        [InlineKeyboardButton(text="🃏 Покер", callback_data="casino_poker"),
         InlineKeyboardButton(text="🎡 Колесо", callback_data="casino_wheel")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("casino_"))
async def casino_start(callback: CallbackQuery, state: FSMContext):
    game = callback.data.replace("casino_", "")
    await state.update_data(casino_game=game)
    await state.set_state(CasinoStates.waiting_for_bet)
    
    min_bet = 5 if game in ["dice", "roulette"] else 10
    max_bet = 5000
    
    await callback.message.edit_text(
        f"🎰 *Казино - {game.capitalize()}*\n\n💰 Ставки: от {min_bet} до {max_bet} ⭐\n\nВведите сумму ставки:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="casino_menu")]])
    )
    await callback.answer()

@dp.message(CasinoStates.waiting_for_bet)
async def casino_bet(message: Message, state: FSMContext):
    try:
        bet = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    game = data["casino_game"]
    
    min_bet = 5 if game in ["dice", "roulette"] else 10
    max_bet = 5000
    
    if bet < min_bet or bet > max_bet:
        await message.answer(f"❌ Ставка должна быть от {min_bet} до {max_bet} ⭐")
        return
    
    user = await get_user(message.from_user.id)
    if user["stars"] < bet:
        await message.answer(f"❌ Недостаточно звезд! У вас {user['stars']} ⭐")
        return
    
    await remove_stars(message.from_user.id, bet, f"Ставка в казино")
    await state.update_data(casino_bet=bet)
    
    if game == "slots":
        win, winnings, result_text = await casino_slots(message.from_user.id, bet)
        await message.answer(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎰 Ещё раз", callback_data="casino_slots"),
             InlineKeyboardButton(text="🔙 В меню", callback_data="casino_menu")]
        ]))
        await state.clear()
    
    elif game == "dice":
        await state.set_state(CasinoStates.waiting_dice_choice)
        await message.answer("🎲 Введите число от 1 до 6:")
    
    elif game == "roulette":
        await state.set_state(CasinoStates.waiting_roulette_choice)
        await message.answer("🎡 Введите число от 0 до 36:")
    
    elif game == "blackjack":
        win, winnings, result_text = await casino_blackjack(message.from_user.id, bet)
        await message.answer(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🃏 Ещё раз", callback_data="casino_blackjack"),
             InlineKeyboardButton(text="🔙 В меню", callback_data="casino_menu")]
        ]))
        await state.clear()
    
    elif game == "poker":
        win, winnings, result_text = await casino_poker(message.from_user.id, bet)
        await message.answer(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🃏 Ещё раз", callback_data="casino_poker"),
             InlineKeyboardButton(text="🔙 В меню", callback_data="casino_menu")]
        ]))
        await state.clear()
    
    elif game == "wheel":
        win, winnings, result_text = await casino_wheel(message.from_user.id, bet)
        await message.answer(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎡 Ещё раз", callback_data="casino_wheel"),
             InlineKeyboardButton(text="🔙 В меню", callback_data="casino_menu")]
        ]))
        await state.clear()

@dp.message(CasinoStates.waiting_dice_choice)
async def casino_dice_choice(message: Message, state: FSMContext):
    try:
        choice = int(message.text)
        if choice < 1 or choice > 6:
            await message.answer("❌ Введите число от 1 до 6!")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    bet = data["casino_bet"]
    
    win, winnings, result_text = await casino_dice(message.from_user.id, bet, choice)
    await message.answer(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Ещё раз", callback_data="casino_dice"),
         InlineKeyboardButton(text="🔙 В меню", callback_data="casino_menu")]
    ]))
    await state.clear()

@dp.message(CasinoStates.waiting_roulette_choice)
async def casino_roulette_choice(message: Message, state: FSMContext):
    try:
        choice = int(message.text)
        if choice < 0 or choice > 36:
            await message.answer("❌ Введите число от 0 до 36!")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    bet = data["casino_bet"]
    
    win, winnings, result_text = await casino_roulette(message.from_user.id, bet, choice)
    await message.answer(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎡 Ещё раз", callback_data="casino_roulette"),
         InlineKeyboardButton(text="🔙 В меню", callback_data="casino_menu")]
    ]))
    await state.clear()

# Турниры
@dp.callback_query(F.data == "tournaments_menu")
async def tournaments_menu(callback: CallbackQuery):
    tournaments = await load_json(TOURNAMENTS_FILE, {"active": None, "history": []})
    settings = await load_json(SETTINGS_FILE, {})
    
    if not settings.get("tournament_enabled", True):
        await callback.answer("❌ Турниры временно отключены!", show_alert=True)
        return
    
    if tournaments["active"]:
        end_time = datetime.fromisoformat(tournaments["active"]["end_time"])
        time_left = end_time - datetime.now()
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        
        user_points = tournaments["active"]["participants"].get(str(callback.from_user.id), 0)
        
        text = f"🏆 *Активный турнир*\n\n✨ {tournaments['active']['name']}\n💰 Приз: {tournaments['active']['prize_pool']} ⭐\n📊 Ваши очки: {user_points}\n⏰ Осталось: {hours}ч {minutes}м\n\n🏅 Топ игроков:\n"
        
        top_players = sorted(tournaments["active"]["participants"].items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (pid, points) in enumerate(top_players, 1):
            text += f"{i}. ID:{pid}: {points} очков\n"
    else:
        text = "🏆 *Турниры*\n\nСейчас нет активных турниров."
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]))
    await callback.answer()

# Задания
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
            text += f"• *{task['name']}*\n└ Награда: {task['reward']} ⭐\n└ Ссылка: {task['link']}\n└ Статус: {status}\n\n"
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

# Рефералы
@dp.callback_query(F.data == "referrals_menu")
async def referrals_menu(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    settings = await load_json(SETTINGS_FILE, {})
    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={user['referral_code']}"
    
    text = (f"👥 *Реферальная система*\n\n⭐ Ссылка:\n`{link}`\n\n📊 Статистика:\n"
            f"└ Приглашено: {user['referral_count']}\n└ Заработано: {user['referral_earnings']} ⭐\n\n"
            f"💡 Условия:\n• {settings.get('referral_reward', 10)} ⭐ за друга\n"
            f"• {settings.get('referral_percent', 10)}% от покупок друга")
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать", callback_data=f"copy_{link}"),
         InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]))
    await callback.answer()

# Вывод
@dp.callback_query(F.data == "withdraw_menu")
async def withdraw_menu(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    settings = await load_json(SETTINGS_FILE, {})
    
    text = (f"💰 *Вывод звезд*\n\n⭐ Баланс: {user['stars']}\n"
            f"💱 Курс: {settings.get('exchange_rate', 1)}:1 к звездам TG\n"
            f"📉 Минимум: {settings.get('min_withdraw', 500)} ⭐\n\n"
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
    min_withdraw = settings.get("min_withdraw", 500)
    
    if amount < min_withdraw:
        await message.answer(f"❌ Минимум {min_withdraw} ⭐")
        return
    
    if user["stars"] < amount:
        await message.answer(f"❌ Недостаточно звезд!")
        return
    
    await remove_stars(message.from_user.id, amount, f"Вывод звезд")
    
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    wid = len(withdrawals) + 1
    withdrawals[str(wid)] = {
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
    
    await message.answer(f"✅ Заявка #{wid} создана! Ожидайте подтверждения.")

# Покупка звезд
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

# Система чеков
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
                f"📋 Ваши чеки: /my_checks\n"
                f"🎫 Активировать чек: /use_check <код>")
        
        buttons = [
            [InlineKeyboardButton(text="📝 Создать чек", callback_data="create_check")],
            [InlineKeyboardButton(text="🎫 Активировать чек", callback_data="use_check")],
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
    
    success, msg, code = await create_check(message.from_user.id, amount)
    
    if success:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎫 Активировать чек", callback_data=f"activate_check_{code}")],
            [InlineKeyboardButton(text="📋 Мои чеки", callback_data="my_checks")],
            [InlineKeyboardButton(text="🔙 В меню", callback_data="check_system_menu")]
        ])
        await message.answer(
            f"✅ {msg}\n\n"
            f"📦 Код чека: `{code}`\n"
            f"💰 Сумма: {amount} ⭐\n\n"
            f"Отправьте этот код другу или нажмите кнопку для активации!",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        await message.answer(f"❌ {msg}")
    
    await state.clear()

@dp.callback_query(F.data.startswith("activate_check_"))
async def activate_check_button(callback: CallbackQuery):
    code = callback.data.replace("activate_check_", "")
    success, msg, _ = await use_check(callback.from_user.id, code)
    await callback.answer(f"{'✅' if success else '❌'} {msg}", show_alert=True)
    await check_system_menu(callback)

@dp.callback_query(F.data == "use_check")
async def use_check_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CheckStates.waiting_for_check_code)
    await callback.message.edit_text(
        "📦 *Активация чека*\n\nВведите код чека:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="check_system_menu")]
        ])
    )
    await callback.answer()

@dp.message(CheckStates.waiting_for_check_code)
async def use_check_code(message: Message, state: FSMContext):
    success, msg, _ = await use_check(message.from_user.id, message.text.strip().upper())
    await message.answer(f"{'✅' if success else '❌'} *{msg}*", parse_mode="Markdown")
    await state.clear()

@dp.callback_query(F.data == "my_checks")
async def my_checks(callback: CallbackQuery):
    checks = await get_user_checks(callback.from_user.id)
    
    if not checks:
        text = "📋 *Ваши чеки*\n\nУ вас нет созданных чеков."
    else:
        text = "📋 *Ваши чеки:*\n\n"
        active = [c for c in checks if not c.get("used", False)]
        used = [c for c in checks if c.get("used", False)]
        
        if active:
            text += "*Активные чеки:*\n"
            for c in active:
                text += f"└ `{c['code']}` - {c['amount']} ⭐\n"
        
        if used:
            text += "\n*Использованные чеки:*\n"
            for c in used[-10:]:
                text += f"└ `{c['code']}` - {c['amount']} ⭐ (активировал: {c.get('used_by', '?')})\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="check_system_menu")]
    ]))
    await callback.answer()

# Промокоды
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

# Лотерея
@dp.callback_query(F.data == "lottery_menu")
async def lottery_menu(callback: CallbackQuery):
    active, info = await get_lottery_info()
    
    if active:
        text = (f"🎲 *Лотерея*\n\n"
                f"💰 Призовой фонд: {info['prize_pool']} ⭐\n"
                f"🎫 Билетов продано: {info['tickets_count']}\n"
                f"💎 Цена билета: {info['ticket_price']} ⭐\n"
                f"⏰ До розыгрыша: {info['hours_left']}ч {info['minutes_left']}м\n\n"
                f"🏆 Победитель получает ВЕСЬ призовой фонд!")
        
        buttons = [
            [InlineKeyboardButton(text="🎫 Купить билет", callback_data="buy_lottery_ticket")],
            [InlineKeyboardButton(text="🎫 Купить 10 билетов", callback_data="buy_lottery_10")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    else:
        text = "🎲 *Лотерея*\n\nСейчас нет активной лотереи. Заходите позже!"
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "buy_lottery_ticket")
async def buy_lottery_ticket_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(LotteryStates.waiting_for_ticket_count)
    await callback.message.edit_text(
        "🎫 *Покупка билетов лотереи*\n\n"
        "💎 Цена билета: 50 ⭐\n\n"
        "Введите количество билетов (1-100):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="lottery_menu")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "buy_lottery_10")
async def buy_lottery_10(callback: CallbackQuery):
    success, msg, tickets = await buy_lottery_ticket(callback.from_user.id, 10)
    if success:
        await callback.answer(f"✅ Куплено 10 билетов!", show_alert=True)
    else:
        await callback.answer(msg, show_alert=True)
    await lottery_menu(callback)

@dp.message(LotteryStates.waiting_for_ticket_count)
async def process_lottery_tickets(message: Message, state: FSMContext):
    try:
        count = int(message.text)
        if count < 1 or count > 100:
            await message.answer("❌ Количество билетов должно быть от 1 до 100!")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    success, msg, tickets = await buy_lottery_ticket(message.from_user.id, count)
    if success:
        await message.answer(f"✅ {msg}\n\nВаши билеты: {', '.join(map(str, tickets))}", parse_mode="Markdown")
    else:
        await message.answer(f"❌ {msg}")
    await state.clear()

# Поддержка
@dp.callback_query(F.data == "support_menu")
async def support_menu(callback: CallbackQuery, state: FSMContext):
    user = await get_user(callback.from_user.id)
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

# Статистика
@dp.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    text = (f"📊 *Ваша статистика*\n\n⭐ Баланс: {user['stars']}\n💰 Заработано: {user['total_earned']}\n"
            f"💸 Потрачено: {user['total_spent']}\n🛒 Покупок: {user['total_purchases']}\n"
            f"👥 Рефералов: {user['referral_count']}\n🎮 Игр: {user['games_played']}\n"
            f"🏆 Побед: {user['games_won']}\n🎰 Выигрышей казино: {user['casino_wins']}\n"
            f"🏆 Очки турнира: {user['tournament_points']}\n✨ Достижений: {len(user['achievements'])}\n"
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
            f"🎮 *Игры (13 игр):* Орёл/Решка, Кости, КНБ, Рулетка, Покер, Баккара, Блэкджек, Crash, Mines, Кено, Плинко, Колесо фортуны, Выше/Ниже\n\n"
            f"🎰 *Казино (6 игр):* Слоты, Кости, Рулетка, Блэкджек, Покер, Колесо\n\n"
            f"🏆 *Турниры:* Участвуйте, получайте очки, выигрывайте призы\n\n"
            f"📋 *Задания:* Подписывайтесь на каналы (бот должен быть в канале!)\n\n"
            f"👥 *Рефералы:* {settings.get('referral_reward', 10)} ⭐ за друга + {settings.get('referral_percent', 10)}% от его покупок\n\n"
            f"📦 *Чеки:*\n"
            f"• Разблокировка: {settings.get('check_system_price', 100)} ⭐\n"
            f"• Создание чека: от 100 до 100000 ⭐\n"
            f"• Активация чека: /use_check <код>\n\n"
            f"🎲 *Лотерея:* Покупайте билеты, выигрывайте весь призовой фонд\n\n"
            f"💰 *Вывод:* /withdraw <сумма>, мин. {settings.get('min_withdraw', 500)} ⭐\n\n"
            f"🛒 *Покупка:* Введите сумму в меню покупки, оплата Telegram Stars\n\n"
            f"💬 *Поддержка:* Создайте тикет в меню поддержки\n\n"
            f"По вопросам: @admin")
    
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

@dp.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()

@dp.callback_query(F.data.startswith("copy_"))
async def copy_text(callback: CallbackQuery):
    await callback.answer("✅ Ссылка скопирована!", show_alert=True)

# =============== АДМИН ПАНЕЛЬ ===============
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
         InlineKeyboardButton(text="🏆 Турниры", callback_data="admin_tournaments")],
        [InlineKeyboardButton(text="🎲 Лотерея", callback_data="admin_lottery"),
         InlineKeyboardButton(text="💰 Выводы", callback_data="admin_withdrawals")],
        [InlineKeyboardButton(text="💬 Поддержка", callback_data="admin_support"),
         InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
         InlineKeyboardButton(text="📝 Логи", callback_data="admin_logs")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    await callback.message.edit_text("⚙️ *Админ панель*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

# Управление пользователями
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
        user_id = int(message.text)
        user = await get_user(user_id)
        text = (f"👤 *Пользователь {user_id}*\n\n⭐ Баланс: {user['stars']}\n💰 Заработано: {user['total_earned']}\n"
                f"💸 Потрачено: {user['total_spent']}\n👥 Рефералов: {user['referral_count']}\n"
                f"🎮 Игр: {user['games_played']}\n🏆 Побед: {user['games_won']}\n"
                f"🎰 Выигрышей казино: {user['casino_wins']}\n🏆 Очки турнира: {user['tournament_points']}\n"
                f"📦 Чек система: {'✅' if user.get('check_system_unlocked', False) else '❌'}\n"
                f"✨ Достижений: {len(user['achievements'])}\n📅 Регистрация: {user['created_at'][:10]}")
        buttons = [
            [InlineKeyboardButton(text="➕ Добавить звезды", callback_data=f"admin_add_stars_{user_id}"),
             InlineKeyboardButton(text="➖ Забрать звезды", callback_data=f"admin_remove_stars_{user_id}")],
            [InlineKeyboardButton(text="🔓 Разблокировать чеки", callback_data=f"admin_unlock_checks_{user_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
        ]
        await message.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except Exception as e:
        await message.answer("❌ Пользователь не найден!")
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

@dp.callback_query(F.data.startswith("admin_unlock_checks_"))
async def admin_unlock_checks(callback: CallbackQuery):
    user_id = int(callback.data.replace("admin_unlock_checks_", ""))
    await update_user(user_id, check_system_unlocked=True)
    await callback.answer("✅ Система чеков разблокирована!", show_alert=True)
    await admin_users_menu(callback, None)

@dp.message(AdminStates.waiting_for_stars_amount)
async def admin_process_stars(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
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

# Управление заданиями
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
            f"💰 Награда: {reward} ⭐\n"
            f"🤖 Бот для проверки: {BOT_ID}\n\n"
            f"⚠️ Важно: Бот должен быть добавлен в канал администратором для корректной проверки!",
            parse_mode="Markdown"
        )
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
            text += f"└ Требуемый бот: {task.get('required_bot', BOT_ID)}\n"
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

# Управление промокодами
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

# Управление чеками
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
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎫 Активировать чек", callback_data=f"activate_check_{code}")]
        ])
        
        await message.answer(f"✅ Чек создан!\n\n📦 Код: `{code}`\n💰 Сумма: {amount} ⭐", parse_mode="Markdown", reply_markup=keyboard)
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
            text += f"└ `{c['code']}` - {c['amount']} ⭐ (создал: {c['creator']})\n"
    
    if checks["used_checks"]:
        text += "\n*Использованные чеки:*\n"
        for c in checks["used_checks"][-10:]:
            text += f"└ `{c['code']}` - {c['amount']} ⭐ (активировал: {c['used_by']})\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_checks")]
    ]))
    await callback.answer()

# Управление турнирами
@dp.callback_query(F.data == "admin_tournaments")
async def admin_tournaments_menu(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    active = await get_active_tournament()
    
    buttons = [
        [InlineKeyboardButton(text="➕ Создать турнир", callback_data="admin_create_tournament")],
        [InlineKeyboardButton(text="📜 История турниров", callback_data="admin_tournament_history")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]
    
    if active:
        buttons.insert(1, [InlineKeyboardButton(text="🏆 Текущий турнир", callback_data="admin_current_tournament")])
    
    await callback.message.edit_text("🏆 *Управление турнирами*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_create_tournament")
async def admin_create_tournament(callback: CallbackQuery, state: FSMContext):
    active = await get_active_tournament()
    if active:
        await callback.answer("❌ Сначала завершите текущий турнир!", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_for_tournament_name)
    await callback.message.edit_text("🏆 Введите название турнира:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_tournaments")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_tournament_name)
async def admin_tournament_name(message: Message, state: FSMContext):
    await state.update_data(tournament_name=message.text)
    await state.set_state(AdminStates.waiting_for_tournament_prize)
    await message.answer("💰 Введите призовой фонд (звезды):")

@dp.message(AdminStates.waiting_for_tournament_prize)
async def admin_tournament_prize(message: Message, state: FSMContext):
    try:
        prize = int(message.text)
        await state.update_data(tournament_prize=prize)
        await state.set_state(AdminStates.waiting_for_tournament_duration)
        await message.answer("⏰ Введите длительность в часах:")
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(AdminStates.waiting_for_tournament_duration)
async def admin_tournament_duration(message: Message, state: FSMContext):
    try:
        duration = int(message.text)
        data = await state.get_data()
        await create_tournament(message.from_user.id, data["tournament_name"], data["tournament_prize"], duration)
        await message.answer(f"✅ Турнир создан!\n\n🏆 {data['tournament_name']}\n💰 {data['tournament_prize']} ⭐\n⏰ {duration} часов")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "admin_current_tournament")
async def admin_current_tournament(callback: CallbackQuery):
    active = await get_active_tournament()
    
    if not active:
        await callback.answer("Нет активного турнира!")
        return
    
    end_time = datetime.fromisoformat(active["end_time"])
    time_left = end_time - datetime.now()
    hours = time_left.seconds // 3600
    minutes = (time_left.seconds % 3600) // 60
    
    text = f"🏆 *Текущий турнир*\n\n✨ {active['name']}\n💰 Приз: {active['prize_pool']} ⭐\n👥 Участников: {len(active['participants'])}\n⏰ Осталось: {hours}ч {minutes}м\n\n*Топ 10 участников:*\n"
    
    top = sorted(active["participants"].items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (uid, points) in enumerate(top, 1):
        text += f"{i}. ID: {uid} - {points} очков\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_tournaments")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_tournament_history")
async def admin_tournament_history(callback: CallbackQuery):
    history = await get_tournament_history()
    
    if not history:
        text = "📜 *История турниров*\n\nНет завершенных турниров."
    else:
        text = "📜 *История турниров:*\n\n"
        for t in history[-5:]:
            text += f"🏆 {t['name']}\n└ Приз: {t['prize_pool']} ⭐\n└ Участников: {len(t['participants'])}\n└ Завершен: {t['ended_at'][:10]}\n\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_tournaments")]
    ]))
    await callback.answer()

# Управление лотереей
@dp.callback_query(F.data == "admin_lottery")
async def admin_lottery_menu(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    lottery = await load_json(LOTTERY_FILE, {"active": None, "history": []})
    
    if lottery["active"]:
        buttons = [
            [InlineKeyboardButton(text="🎲 Завершить лотерею", callback_data="admin_end_lottery")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ]
        text = f"🎲 *Активная лотерея*\n\n💰 Приз: {lottery['active']['prize_pool']} ⭐\n🎫 Билетов: {len(lottery['active']['tickets'])}\n⏰ До конца: {max(0, (datetime.fromisoformat(lottery['active']['end_time']) - datetime.now()).seconds // 3600)} часов"
    else:
        buttons = [
            [InlineKeyboardButton(text="➕ Создать лотерею", callback_data="admin_create_lottery")],
            [InlineKeyboardButton(text="📜 История лотерей", callback_data="admin_lottery_history")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ]
        text = "🎲 *Управление лотереей*\n\nНет активной лотереи."
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_create_lottery")
async def admin_create_lottery(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_lottery_prize)
    await callback.message.edit_text("🎲 Введите призовой фонд лотереи:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_lottery")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_lottery_prize)
async def admin_lottery_prize(message: Message, state: FSMContext):
    try:
        prize = int(message.text)
        lottery_id = await create_lottery(message.from_user.id, prize)
        if lottery_id:
            await message.answer(f"✅ Лотерея создана!\n\n💰 Призовой фонд: {prize} ⭐\n🎫 Цена билета: 50 ⭐\n⏰ Длительность: 24 часа")
        else:
            await message.answer("❌ Лотерея уже активна!")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "admin_end_lottery")
async def admin_end_lottery(callback: CallbackQuery):
    success, msg, winner = await end_lottery()
    await callback.answer(msg, show_alert=True)
    await admin_lottery_menu(callback, None)

@dp.callback_query(F.data == "admin_lottery_history")
async def admin_lottery_history(callback: CallbackQuery):
    lottery = await load_json(LOTTERY_FILE, {"history": []})
    history = lottery["history"]
    
    if not history:
        text = "📜 *История лотерей*\n\nНет завершенных лотерей."
    else:
        text = "📜 *История лотерей:*\n\n"
        for l in history[-5:]:
            text += f"🎲 Лотерея #{l['id']}\n└ Приз: {l['prize_pool']} ⭐\n└ Билетов: {len(l['tickets'])}\n└ Победитель: {l['winner']['user_id']}\n└ Завершена: {l['ended_at'][:10]}\n\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_lottery")]
    ]))
    await callback.answer()

# Управление выводами
@dp.callback_query(F.data == "admin_withdrawals")
async def admin_withdrawals_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    pending = {k: v for k, v in withdrawals.items() if v["status"] == "pending"}
    
    if not pending:
        text = "💰 *Заявки на вывод*\n\nНет активных заявок."
        buttons = [[InlineKeyboardButton(text="📜 История выводов", callback_data="admin_withdrawal_history")],
                   [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]]
    else:
        text = f"💰 *Заявки на вывод*\n\nВсего заявок: {len(pending)}\n\n"
        buttons = []
        for wid, w in list(pending.items())[:10]:
            text += f"*ID {wid}:* @{w['username']}\n└ Сумма: {w['stars']} ⭐\n└ Дата: {w['created_at'][:19]}\n\n"
            buttons.append([
                InlineKeyboardButton(text=f"✅ Подтвердить {wid}", callback_data=f"admin_approve_{wid}"),
                InlineKeyboardButton(text=f"❌ Отклонить {wid}", callback_data=f"admin_decline_{wid}")
            ])
        buttons.append([InlineKeyboardButton(text="📜 История выводов", callback_data="admin_withdrawal_history")])
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
        await log_admin_action(callback.from_user.id, "approve_withdrawal", withdrawals[wid]["user_id"], f"Amount: {withdrawals[wid]['stars']}")
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

@dp.callback_query(F.data == "admin_withdrawal_history")
async def admin_withdrawal_history(callback: CallbackQuery):
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    approved = [w for w in withdrawals.values() if w["status"] == "approved"]
    declined = [w for w in withdrawals.values() if w["status"] == "declined"]
    
    text = f"📜 *История выводов*\n\n✅ Подтверждено: {len(approved)}\n❌ Отклонено: {len(declined)}\n\n"
    
    if approved[-10:]:
        text += "*Последние 10 выводов:*\n"
        for w in approved[-10:]:
            text += f"└ #{w.get('id', '?')} - @{w['username']} - {w['stars']} ⭐ - {w.get('approved_at', w['created_at'])[:10]}\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_withdrawals")]
    ]))
    await callback.answer()

# Поддержка для админов
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
    await state.set_state(AdminStates.waiting_for_action)
    await callback.message.edit_text(
        f"💬 *Ответ в тикет #{ticket_id}*\n\nВведите ваш ответ:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Закрыть тикет", callback_data=f"admin_close_ticket_{ticket_id}"),
             InlineKeyboardButton(text="🔙 Назад", callback_data="admin_support")]
        ])
    )
    await callback.answer()

@dp.message(AdminStates.waiting_for_action)
async def admin_send_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    
    if ticket_id:
        success = await reply_to_ticket(message.from_user.id, ticket_id, message.text)
        if success:
            await message.answer(f"✅ Ответ отправлен в тикет #{ticket_id}!")
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

# Настройки
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
            f"📦 Цена чек системы: {settings.get('check_system_price', 100)} ⭐\n"
            f"🎰 Казино: {'✅ Вкл' if settings.get('casino_enabled', True) else '❌ Выкл'}\n"
            f"🏆 Турниры: {'✅ Вкл' if settings.get('tournament_enabled', True) else '❌ Выкл'}\n\n"
            f"Выберите параметр для изменения:")
    
    buttons = [
        [InlineKeyboardButton(text="⭐ Стартовый баланс", callback_data="set_start_balance"),
         InlineKeyboardButton(text="💰 Мин. вывод", callback_data="set_min_withdraw")],
        [InlineKeyboardButton(text="👥 Реф. награда", callback_data="set_referral_reward"),
         InlineKeyboardButton(text="📊 Реф. процент", callback_data="set_referral_percent")],
        [InlineKeyboardButton(text="💱 Курс обмена", callback_data="set_exchange_rate"),
         InlineKeyboardButton(text="📦 Цена чек системы", callback_data="set_check_system_price")],
        [InlineKeyboardButton(text="🎰 Казино", callback_data="set_casino"),
         InlineKeyboardButton(text="🏆 Турниры", callback_data="set_tournaments")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("set_"))
async def admin_setting_change(callback: CallbackQuery, state: FSMContext):
    setting = callback.data.replace("set_", "")
    
    if setting in ["casino", "tournaments"]:
        settings = await load_json(SETTINGS_FILE, {})
        if setting == "casino":
            settings["casino_enabled"] = not settings.get("casino_enabled", True)
        else:
            settings["tournament_enabled"] = not settings.get("tournament_enabled", True)
        await save_json(SETTINGS_FILE, settings)
        await callback.answer("✅ Настройка обновлена!")
        await admin_settings_menu(callback)
        return
    
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
        value = int(message.text)
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

# Статистика админа
@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    users = await load_json(USERS_FILE, {})
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    tasks = await get_all_tasks()
    promo = await load_json(PROMO_FILE, {"promo_codes": []})
    checks = await load_json(CHECKS_FILE, {"checks": [], "used_checks": []})
    tournaments = await load_json(TOURNAMENTS_FILE, {"active": None})
    support = await load_json(SUPPORT_FILE, {"tickets": []})
    lottery = await load_json(LOTTERY_FILE, {"active": None})
    
    total_stars = sum(u.get("stars", 0) for u in users.values())
    total_users = len(users)
    unlocked_checks = len([u for u in users.values() if u.get("check_system_unlocked", False)])
    pending_withdrawals = len([w for w in withdrawals.values() if w.get("status") == "pending"])
    open_tickets = len([t for t in support["tickets"] if t["status"] == "open"])
    
    text = (f"📊 *Общая статистика*\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"⭐ Всего звезд: {total_stars}\n"
            f"📦 Чек система: {unlocked_checks}/{total_users}\n"
            f"📈 Средний баланс: {total_stars // total_users if total_users else 0}\n\n"
            f"📋 Заданий: {len(tasks)}\n"
            f"🎫 Промокодов: {len(promo['promo_codes'])}\n"
            f"📦 Активных чеков: {len(checks['checks'])}\n"
            f"🏆 Активный турнир: {'Да' if tournaments['active'] else 'Нет'}\n"
            f"🎲 Активная лотерея: {'Да' if lottery['active'] else 'Нет'}\n"
            f"💬 Открытых тикетов: {open_tickets}\n\n"
            f"💰 Ожидают вывода: {pending_withdrawals}")
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]))
    await callback.answer()

# Логи
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
async def tournament_checker():
    while True:
        await asyncio.sleep(60)
        tournaments = await load_json(TOURNAMENTS_FILE, {"active": None})
        if tournaments["active"]:
            end_time = datetime.fromisoformat(tournaments["active"]["end_time"])
            if datetime.now() >= end_time:
                await end_tournament()

async def lottery_checker():
    while True:
        await asyncio.sleep(60)
        lottery = await load_json(LOTTERY_FILE, {"active": None})
        if lottery["active"]:
            end_time = datetime.fromisoformat(lottery["active"]["end_time"])
            if datetime.now() >= end_time:
                await end_lottery()

# Запуск бота
async def main():
    await init_data()
    asyncio.create_task(tournament_checker())
    asyncio.create_task(lottery_checker())
    logger.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())