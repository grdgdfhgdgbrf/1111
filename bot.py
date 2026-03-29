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

os.makedirs(DATA_DIR, exist_ok=True)

# FSM States
class GameStates(StatesGroup):
    waiting_for_bet = State()
    playing_coinflip = State()
    playing_dice = State()
    playing_rps = State()

class CasinoStates(StatesGroup):
    waiting_for_bet = State()
    waiting_dice_choice = State()

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

class PromoStates(StatesGroup):
    waiting_for_promo_code = State()

class CheckStates(StatesGroup):
    waiting_for_check_code = State()

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
            "max_bet": 10000
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
    await save_json(ADMIN_LOGS_FILE, logs[-100:])

# Система достижений
async def check_achievements(user_id: int):
    user = await get_user(user_id)
    
    achievements = {
        "millionaire": {
            "name": "💰 Миллионер",
            "description": "Накопить 1,000,000 звезд",
            "condition": user["total_earned"] >= 1000000,
            "reward": 100000
        },
        "high_roller": {
            "name": "🎲 Высокий игрок",
            "description": "Сыграть 1000 игр",
            "condition": user["games_played"] >= 1000,
            "reward": 50000
        },
        "lucky": {
            "name": "🍀 Счастливчик",
            "description": "Выиграть 100 игр",
            "condition": user["games_won"] >= 100,
            "reward": 25000
        },
        "casino_king": {
            "name": "👑 Король казино",
            "description": "Выиграть 500 раз в казино",
            "condition": user["casino_wins"] >= 500,
            "reward": 75000
        },
        "referral_master": {
            "name": "👥 Мастер рефералов",
            "description": "Пригласить 100 друзей",
            "condition": user["referral_count"] >= 100,
            "reward": 50000
        }
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
async def generate_check(user_id: int, amount: int) -> str:
    checks = await load_json(CHECKS_FILE, {"checks": [], "used_checks": []})
    code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))
    
    check = {
        "code": code,
        "amount": amount,
        "creator": user_id,
        "created_at": datetime.now().isoformat(),
        "used": False,
        "used_by": None
    }
    
    checks["checks"].append(check)
    await save_json(CHECKS_FILE, checks)
    return code

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

async def get_all_checks() -> List[dict]:
    checks = await load_json(CHECKS_FILE, {"checks": [], "used_checks": []})
    return checks["checks"] + checks["used_checks"]

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

async def get_all_promo() -> List[dict]:
    promo = await load_json(PROMO_FILE, {"promo_codes": []})
    return promo["promo_codes"]

async def delete_promo(code: str) -> bool:
    promo = await load_json(PROMO_FILE, {"promo_codes": [], "used_promo": {}})
    original_len = len(promo["promo_codes"])
    promo["promo_codes"] = [p for p in promo["promo_codes"] if p["code"] != code]
    if len(promo["promo_codes"]) < original_len:
        await save_json(PROMO_FILE, promo)
        return True
    return False

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
                    f"🏆 *Турнир завершен!*\n\n✨ {tournaments['history'][-1]['name']}\n📊 Очки: {points}\n🎁 Приз: {prize} ⭐",
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

# Система заданий
async def add_task(admin_id: int, name: str, link: str, reward: int) -> int:
    tasks = await load_json(TASKS_FILE, {"sponsor_tasks": [], "completed_tasks": {}})
    task_id = len(tasks["sponsor_tasks"]) + 1
    tasks["sponsor_tasks"].append({
        "id": task_id,
        "name": name,
        "link": link,
        "reward": reward,
        "created_at": datetime.now().isoformat(),
        "created_by": admin_id
    })
    await save_json(TASKS_FILE, tasks)
    await log_admin_action(admin_id, "add_task", None, f"Name: {name}, Reward: {reward}")
    return task_id

async def delete_task(task_id: int) -> bool:
    tasks = await load_json(TASKS_FILE, {"sponsor_tasks": [], "completed_tasks": {}})
    original_len = len(tasks["sponsor_tasks"])
    tasks["sponsor_tasks"] = [t for t in tasks["sponsor_tasks"] if t["id"] != task_id]
    if len(tasks["sponsor_tasks"]) < original_len:
        await save_json(TASKS_FILE, tasks)
        return True
    return False

async def get_all_tasks() -> List[dict]:
    tasks = await load_json(TASKS_FILE, {"sponsor_tasks": []})
    return tasks["sponsor_tasks"]

async def is_task_completed(user_id: int, task_id: int) -> bool:
    tasks = await load_json(TASKS_FILE, {"completed_tasks": {}})
    completed = tasks["completed_tasks"].get(str(user_id), [])
    return task_id in completed

async def complete_task(user_id: int, task_id: int):
    tasks = await load_json(TASKS_FILE, {"sponsor_tasks": [], "completed_tasks": {}})
    if str(user_id) not in tasks["completed_tasks"]:
        tasks["completed_tasks"][str(user_id)] = []
    tasks["completed_tasks"][str(user_id)].append(task_id)
    await save_json(TASKS_FILE, tasks)

# Система выводов
async def create_withdrawal(user_id: int, amount: int, username: str) -> int:
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    wid = len(withdrawals) + 1
    withdrawals[str(wid)] = {
        "user_id": user_id,
        "username": username,
        "stars": amount,
        "tg_stars": amount,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    await save_json(WITHDRAWALS_FILE, withdrawals)
    return wid

async def get_pending_withdrawals() -> List[dict]:
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    return [{"id": k, **v} for k, v in withdrawals.items() if v["status"] == "pending"]

async def get_all_withdrawals() -> List[dict]:
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    return [{"id": k, **v} for k, v in withdrawals.items()]

async def approve_withdrawal(wid: str, admin_id: int) -> bool:
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    if wid in withdrawals and withdrawals[wid]["status"] == "pending":
        withdrawals[wid]["status"] = "approved"
        withdrawals[wid]["approved_at"] = datetime.now().isoformat()
        withdrawals[wid]["approved_by"] = admin_id
        await save_json(WITHDRAWALS_FILE, withdrawals)
        await log_admin_action(admin_id, "approve_withdrawal", withdrawals[wid]["user_id"], f"Amount: {withdrawals[wid]['stars']}")
        return True
    return False

async def decline_withdrawal(wid: str, admin_id: int) -> bool:
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    if wid in withdrawals and withdrawals[wid]["status"] == "pending":
        user_id = withdrawals[wid]["user_id"]
        amount = withdrawals[wid]["stars"]
        await add_stars(user_id, amount, "Возврат при отклонении вывода")
        withdrawals[wid]["status"] = "declined"
        withdrawals[wid]["declined_at"] = datetime.now().isoformat()
        withdrawals[wid]["declined_by"] = admin_id
        await save_json(WITHDRAWALS_FILE, withdrawals)
        await log_admin_action(admin_id, "decline_withdrawal", user_id, f"Amount: {amount}")
        return True
    return False

# Игры
GAMES = {
    "coinflip": {"name": "🎲 Орёл или Решка", "min_bet": 1, "max_bet": 1000},
    "dice": {"name": "🎲 Кости", "min_bet": 1, "max_bet": 500},
    "rps": {"name": "✊ Камень-Ножницы-Бумага", "min_bet": 1, "max_bet": 500}
}

async def play_coinflip(user_id: int, bet: int, choice: str) -> Tuple[bool, int, str]:
    result = random.choice(["eagle", "tails"])
    win = (choice == result)
    
    if win:
        winnings = bet * 2
        await add_stars(user_id, winnings, f"Выигрыш в Орёл/Решка")
        await update_tournament_points(user_id, winnings)
        return True, winnings, f"🦅 Вы выбрали: {'Орёл' if choice == 'eagle' else 'Решка'}\n🎲 Выпало: {'Орёл' if result == 'eagle' else 'Решка'}\n\n🎉 Вы выиграли {winnings} ⭐!"
    else:
        await update_tournament_points(user_id, bet)
        return False, bet, f"🦅 Вы выбрали: {'Орёл' if choice == 'eagle' else 'Решка'}\n🎲 Выпало: {'Орёл' if result == 'eagle' else 'Решка'}\n\n😔 Вы проиграли {bet} ⭐"

async def play_dice(user_id: int, bet: int, choice: int) -> Tuple[bool, int, str]:
    result = random.randint(1, 6)
    win = (choice == result)
    
    if win:
        winnings = bet * 5
        await add_stars(user_id, winnings, f"Выигрыш в Кости")
        await update_tournament_points(user_id, winnings)
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
        winnings = bet * 2
        await add_stars(user_id, winnings, f"Выигрыш в КНБ")
        await update_tournament_points(user_id, winnings)
        return True, winnings, f"✊ Ваш ход: {choice_map[choice]}\n🤖 Ход бота: {choice_map[bot_choice]}\n\n🎉 Выигрыш: {winnings} ⭐!"
    else:
        await update_tournament_points(user_id, bet)
        return False, bet, f"✊ Ваш ход: {choice_map[choice]}\n🤖 Ход бота: {choice_map[bot_choice]}\n\n😔 Проигрыш: {bet} ⭐"

# Казино игры
async def casino_slots(user_id: int, bet: int) -> Tuple[bool, int, str]:
    symbols = ["🍒", "🍋", "🍊", "🔔", "💎", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    
    win_multiplier = 0
    if result[0] == result[1] == result[2]:
        if result[0] == "7️⃣":
            win_multiplier = 10
        elif result[0] == "💎":
            win_multiplier = 5
        else:
            win_multiplier = 3
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        win_multiplier = 2
    
    if win_multiplier > 0:
        winnings = bet * win_multiplier
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
        winnings = bet * 6
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
         InlineKeyboardButton(text="📦 Чек", callback_data="use_check")],
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
    
    text = (f"✨ Добро пожаловать, {message.from_user.full_name}!\n\n⭐ Баланс: {user['stars']} звезд\n\n"
            f"🎮 Игры | 🎰 Казино | 🏆 Турниры\n"
            f"📋 Задания | 👥 Рефералы (10% от покупок)\n"
            f"💰 Вывод от {settings.get('min_withdraw', 500)} ⭐\n\nПриятной игры! 🎉")
    
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

# Игры
@dp.callback_query(F.data == "games_menu")
async def games_menu(callback: CallbackQuery):
    text = "🎮 *Игры*\n\nВыберите игру:"
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
        f"🎮 *{game['name']}*\n\n💰 Ставки: от {game['min_bet']} до {game['max_bet']} ⭐\n\nВведите сумму ставки:",
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

@dp.callback_query(GameStates.playing_coinflip, F.data.startswith("coinflip_"))
async def coinflip_play(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("coinflip_", "")
    data = await state.get_data()
    bet = data["bet"]
    
    win, winnings, result_text = await play_coinflip(callback.from_user.id, bet, choice)
    if win:
        user = await get_user(callback.from_user.id)
        await update_user(callback.from_user.id, games_won=user["games_won"] + 1)
    
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
    if win:
        user = await get_user(message.from_user.id)
        await update_user(message.from_user.id, games_won=user["games_won"] + 1)
    
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
    if win and winnings > bet:
        user = await get_user(callback.from_user.id)
        await update_user(callback.from_user.id, games_won=user["games_won"] + 1)
    
    await callback.message.edit_text(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Ещё раз", callback_data="game_rps"),
         InlineKeyboardButton(text="🔙 В меню", callback_data="games_menu")]
    ]))
    await state.clear()
    await callback.answer()

# Казино
@dp.callback_query(F.data == "casino_menu")
async def casino_menu(callback: CallbackQuery):
    settings = await load_json(SETTINGS_FILE, {})
    if not settings.get("casino_enabled", True):
        await callback.answer("❌ Казино временно закрыто!", show_alert=True)
        return
    
    text = "🎰 *Казино*\n\nВыберите игру:"
    buttons = [
        [InlineKeyboardButton(text="🎰 Слоты (x2-x10)", callback_data="casino_slots"),
         InlineKeyboardButton(text="🎲 Кости (x6)", callback_data="casino_dice")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("casino_"))
async def casino_start(callback: CallbackQuery, state: FSMContext):
    game = callback.data.replace("casino_", "")
    await state.update_data(casino_game=game)
    await state.set_state(CasinoStates.waiting_for_bet)
    
    min_bet = 5 if game == "dice" else 10
    await callback.message.edit_text(
        f"🎰 *Казино - {'Слоты' if game == 'slots' else 'Кости'}*\n\n💰 Ставки: от {min_bet} до 5000 ⭐\n\nВведите сумму ставки:",
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
    
    min_bet = 5 if game == "dice" else 10
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
            text += f"{i}. {pid}: {points} очков\n"
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
    
    channel = task["link"].split("/")[-1]
    try:
        member = await bot.get_chat_member(channel, callback.from_user.id)
        if member.status in ["member", "administrator", "creator"]:
            await add_stars(callback.from_user.id, task["reward"], f"Задание: {task['name']}")
            await complete_task(callback.from_user.id, task_id)
            await callback.answer(f"✅ +{task['reward']} ⭐", show_alert=True)
            await tasks_menu(callback)
        else:
            await callback.answer("❌ Вы не подписаны на канал!", show_alert=True)
    except:
        await callback.answer("❌ Ошибка проверки!", show_alert=True)

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
    wid = await create_withdrawal(message.from_user.id, amount, message.from_user.username or str(message.from_user.id))
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, f"💰 *Заявка #{wid}*\n👤 @{message.from_user.username or message.from_user.id}\n⭐ {amount} ⭐", parse_mode="Markdown")
        except:
            pass
    
    await message.answer(f"✅ Заявка #{wid} создана! Ожидайте подтверждения.")

# Покупка
@dp.callback_query(F.data == "buy_stars")
async def buy_stars_menu(callback: CallbackQuery):
    text = "🛒 *Покупка звезд*\n\n💎 Курс: 1 звезда TG = 1 ⭐\n\nВыберите сумму:"
    buttons = [
        [InlineKeyboardButton(text="🔹 50 ⭐", callback_data="buy_50"), InlineKeyboardButton(text="🔸 100 ⭐", callback_data="buy_100")],
        [InlineKeyboardButton(text="🔹 250 ⭐", callback_data="buy_250"), InlineKeyboardButton(text="🔸 500 ⭐", callback_data="buy_500")],
        [InlineKeyboardButton(text="🔹 1000 ⭐", callback_data="buy_1000"), InlineKeyboardButton(text="🔸 2500 ⭐", callback_data="buy_2500")],
        [InlineKeyboardButton(text="🔹 5000 ⭐", callback_data="buy_5000"), InlineKeyboardButton(text="🔸 10000 ⭐", callback_data="buy_10000")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def create_invoice(callback: CallbackQuery):
    stars = int(callback.data.replace("buy_", ""))
    await bot.send_invoice(
        chat_id=callback.from_user.id, title=f"Покупка {stars} звезд",
        description=f"Вы получаете {stars} ⭐", payload=f"stars_{stars}",
        provider_token="", currency="XTR", prices=[LabeledPrice(label=f"{stars} ⭐", amount=stars)],
        start_parameter="buy_stars"
    )
    await callback.answer()

@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    stars = int(message.successful_payment.invoice_payload.replace("stars_", ""))
    await add_stars(message.from_user.id, stars, f"Покупка {stars} звезд")
    user = await get_user(message.from_user.id)
    await update_user(message.from_user.id, total_purchases=user["total_purchases"] + stars)
    await message.answer(f"✅ *Покупка успешна!*\n\n⭐ Начислено: {stars} ⭐\n💰 Баланс: {user['stars'] + stars} ⭐", parse_mode="Markdown")

# Промокод
@dp.callback_query(F.data == "use_promo")
async def use_promo_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromoStates.waiting_for_promo_code)
    await callback.message.edit_text("🎫 *Активация промокода*\n\nВведите промокод:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_main")]
    ]))
    await callback.answer()

@dp.message(PromoStates.waiting_for_promo_code)
async def use_promo_code(message: Message, state: FSMContext):
    success, msg, _ = await use_promo(message.from_user.id, message.text.strip().upper())
    await message.answer(f"{'✅' if success else '❌'} *{msg}*", parse_mode="Markdown")
    await state.clear()
    await cmd_start(message, state)

# Чек
@dp.callback_query(F.data == "use_check")
async def use_check_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CheckStates.waiting_for_check_code)
    await callback.message.edit_text("📦 *Активация чека*\n\nВведите код чека:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_main")]
    ]))
    await callback.answer()

@dp.message(CheckStates.waiting_for_check_code)
async def use_check_code(message: Message, state: FSMContext):
    success, msg, _ = await use_check(message.from_user.id, message.text.strip().upper())
    await message.answer(f"{'✅' if success else '❌'} *{msg}*", parse_mode="Markdown")
    await state.clear()
    await cmd_start(message, state)

# Статистика
@dp.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    text = (f"📊 *Ваша статистика*\n\n⭐ Баланс: {user['stars']}\n💰 Заработано: {user['total_earned']}\n"
            f"💸 Потрачено: {user['total_spent']}\n🛒 Покупок: {user['total_purchases']}\n"
            f"👥 Рефералов: {user['referral_count']}\n🎮 Игр: {user['games_played']}\n"
            f"🏆 Побед: {user['games_won']}\n🎰 Выигрышей казино: {user['casino_wins']}\n"
            f"🏆 Очки турнира: {user['tournament_points']}\n✨ Достижений: {len(user['achievements'])}\n"
            f"📅 Регистрация: {user['created_at'][:10]}")
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    settings = await load_json(SETTINGS_FILE, {})
    text = (f"❓ *Помощь*\n\n🎮 *Игры:* Орёл/Решка, Кости, КНБ\n"
            f"🎰 *Казино:* Слоты (x2-x10), Кости (x6)\n🏆 *Турниры:* Участвуйте, получайте очки, выигрывайте призы\n"
            f"📋 *Задания:* Подписывайтесь на каналы, получайте звезды\n"
            f"👥 *Рефералы:* {settings.get('referral_reward', 10)} ⭐ за друга + {settings.get('referral_percent', 10)}% от его покупок\n"
            f"💰 *Вывод:* /withdraw <сумма>, мин. {settings.get('min_withdraw', 500)} ⭐\n"
            f"🛒 *Покупка:* Через Telegram Stars, курс 1:1\n\nПо вопросам: @admin")
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

# =============== АДМИН ПАНЕЛЬ (ПОЛНАЯ РЕАЛИЗАЦИЯ) ===============

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    buttons = [
        [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 Управление звездами", callback_data="admin_stars")],
        [InlineKeyboardButton(text="📋 Управление заданиями", callback_data="admin_tasks")],
        [InlineKeyboardButton(text="🎫 Управление промокодами", callback_data="admin_promo")],
        [InlineKeyboardButton(text="📦 Управление чеками", callback_data="admin_checks")],
        [InlineKeyboardButton(text="🏆 Управление турнирами", callback_data="admin_tournaments")],
        [InlineKeyboardButton(text="💰 Управление выводами", callback_data="admin_withdrawals")],
        [InlineKeyboardButton(text="⚙️ Настройки бота", callback_data="admin_settings")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📝 Логи действий", callback_data="admin_logs")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    await callback.message.edit_text("⚙️ *Админ панель*\n\nВыберите действие:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

# ===== Управление пользователями =====
@dp.callback_query(F.data == "admin_users")
async def admin_users_menu(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    buttons = [
        [InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="admin_find_user")],
        [InlineKeyboardButton(text="📊 Топ пользователей", callback_data="admin_top_users")],
        [InlineKeyboardButton(text="📋 Список пользователей", callback_data="admin_list_users")],
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
                f"✨ Достижений: {len(user['achievements'])}\n📅 Регистрация: {user['created_at'][:10]}")
        buttons = [
            [InlineKeyboardButton(text="➕ Добавить звезды", callback_data=f"admin_add_stars_{user_id}"),
             InlineKeyboardButton(text="➖ Забрать звезды", callback_data=f"admin_remove_stars_{user_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
        ]
        await message.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except Exception as e:
        await message.answer("❌ Пользователь не найден!")
    await state.clear()

@dp.callback_query(F.data.startswith("admin_add_stars_"))
async def admin_add_stars_amount(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    user_id = int(callback.data.replace("admin_add_stars_", ""))
    await state.update_data(target_user=user_id, action="add")
    await state.set_state(AdminStates.waiting_for_stars_amount)
    await callback.message.edit_text("💰 Введите количество звезд для начисления:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_users")]
    ]))
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_remove_stars_"))
async def admin_remove_stars_amount(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    user_id = int(callback.data.replace("admin_remove_stars_", ""))
    await state.update_data(target_user=user_id, action="remove")
    await state.set_state(AdminStates.waiting_for_stars_amount)
    await callback.message.edit_text("💰 Введите количество звезд для списания:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_users")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_stars_amount)
async def admin_process_stars(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав!")
        await state.clear()
        return
    
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
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    users = await load_json(USERS_FILE, {})
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("stars", 0), reverse=True)[:10]
    
    text = "🏆 *Топ пользователей по балансу:*\n\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        text += f"{i}. ID: {uid} - {data.get('stars', 0)} ⭐\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_list_users")
async def admin_list_users(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    users = await load_json(USERS_FILE, {})
    text = f"📋 *Всего пользователей:* {len(users)}\n\n"
    text += "Последние 10 пользователей:\n"
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("created_at", ""), reverse=True)[:10]
    for uid, data in sorted_users:
        text += f"• ID: {uid} - {data.get('stars', 0)} ⭐ - {data.get('created_at', '')[:10]}\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
    ]))
    await callback.answer()

# ===== Управление звездами =====
@dp.callback_query(F.data == "admin_stars")
async def admin_stars_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    users = await load_json(USERS_FILE, {})
    total_stars = sum(u.get("stars", 0) for u in users.values())
    
    text = (f"💰 *Управление звездами*\n\n"
            f"📊 Всего звезд в системе: {total_stars}\n"
            f"👥 Всего пользователей: {len(users)}\n"
            f"📈 Средний баланс: {total_stars // len(users) if users else 0}\n\n"
            f"Выберите действие:")
    
    buttons = [
        [InlineKeyboardButton(text="💸 Массовая выдача", callback_data="admin_mass_add")],
        [InlineKeyboardButton(text="📊 Статистика звезд", callback_data="admin_stars_stats")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_mass_add")
async def admin_mass_add(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    await state.set_state(AdminStates.waiting_for_stars_amount)
    await state.update_data(action="mass_add")
    await callback.message.edit_text("💰 Введите количество звезд для ВСЕХ пользователей:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_stars")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_stars_stats")
async def admin_stars_stats(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    users = await load_json(USERS_FILE, {})
    stars_list = [u.get("stars", 0) for u in users.values()]
    
    if stars_list:
        text = (f"📊 *Статистика звезд*\n\n"
                f"💰 Всего звезд: {sum(stars_list)}\n"
                f"📈 Средний баланс: {sum(stars_list) // len(stars_list)}\n"
                f"🔝 Максимальный: {max(stars_list)}\n"
                f"📉 Минимальный: {min(stars_list)}\n"
                f"👥 Всего пользователей: {len(stars_list)}")
    else:
        text = "📊 Нет данных"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_stars")]
    ]))
    await callback.answer()

# ===== Управление заданиями =====
@dp.callback_query(F.data == "admin_tasks")
async def admin_tasks_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tasks = await get_all_tasks()
    text = f"📋 *Управление заданиями*\n\nАктивных заданий: {len(tasks)}\n\nВыберите действие:"
    
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить задание", callback_data="admin_add_task")],
        [InlineKeyboardButton(text="📋 Список заданий", callback_data="admin_list_tasks")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
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
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав!")
        await state.clear()
        return
    
    await state.update_data(task_name=message.text)
    await state.set_state(AdminStates.waiting_for_task_link)
    await message.answer("🔗 Введите ссылку на канал (например, https://t.me/channel):")

@dp.message(AdminStates.waiting_for_task_link)
async def admin_task_link(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав!")
        await state.clear()
        return
    
    await state.update_data(task_link=message.text)
    await state.set_state(AdminStates.waiting_for_task_reward)
    await message.answer("💰 Введите награду (звезды):")

@dp.message(AdminStates.waiting_for_task_reward)
async def admin_task_reward(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав!")
        await state.clear()
        return
    
    try:
        reward = int(message.text)
        data = await state.get_data()
        
        task_id = await add_task(message.from_user.id, data["task_name"], data["task_link"], reward)
        await message.answer(f"✅ Задание добавлено!\n\n📝 {data['task_name']}\n💰 Награда: {reward} ⭐\n🆔 ID: {task_id}")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "admin_list_tasks")
async def admin_list_tasks(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
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
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    task_id = int(callback.data.replace("admin_delete_task_", ""))
    success = await delete_task(task_id)
    
    if success:
        await callback.answer("✅ Задание удалено!")
    else:
        await callback.answer("❌ Задание не найдено!")
    
    await admin_list_tasks(callback)

# ===== Управление промокодами =====
@dp.callback_query(F.data == "admin_promo")
async def admin_promo_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    promo_list = await get_all_promo()
    text = f"🎫 *Управление промокодами*\n\nАктивных промокодов: {len(promo_list)}\n\nВыберите действие:"
    
    buttons = [
        [InlineKeyboardButton(text="➕ Создать промокод", callback_data="admin_create_promo")],
        [InlineKeyboardButton(text="📋 Список промокодов", callback_data="admin_list_promo")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_create_promo")
async def admin_create_promo(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    await state.set_state(AdminStates.waiting_for_promo_code)
    await callback.message.edit_text("🎫 Введите код промокода:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_promo")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_promo_code)
async def admin_promo_code(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав!")
        await state.clear()
        return
    
    await state.update_data(promo_code=message.text.strip().upper())
    await state.set_state(AdminStates.waiting_for_promo_reward)
    await message.answer("💰 Введите награду (звезды):")

@dp.message(AdminStates.waiting_for_promo_reward)
async def admin_promo_reward(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав!")
        await state.clear()
        return
    
    try:
        reward = int(message.text)
        await state.update_data(promo_reward=reward)
        await state.set_state(AdminStates.waiting_for_promo_limit)
        await message.answer("📊 Введите лимит использований:")
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(AdminStates.waiting_for_promo_limit)
async def admin_promo_limit(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав!")
        await state.clear()
        return
    
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
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    promo_list = await get_all_promo()
    
    if not promo_list:
        text = "🎫 *Список промокодов*\n\nНет активных промокодов."
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_promo")]]
    else:
        text = "🎫 *Список промокодов:*\n\n"
        buttons = []
        for promo in promo_list:
            text += f"*{promo['code']}*\n"
            text += f"└ Награда: {promo['reward']} ⭐\n"
            text += f"└ Использовано: {promo['used']}/{promo['limit']}\n"
            text += f"└ Создан: {promo['created_at'][:10]}\n\n"
            buttons.append([InlineKeyboardButton(text=f"❌ Удалить {promo['code']}", callback_data=f"admin_delete_promo_{promo['code']}")])
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_promo")])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_delete_promo_"))
async def admin_delete_promo(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    code = callback.data.replace("admin_delete_promo_", "")
    success = await delete_promo(code)
    
    if success:
        await callback.answer("✅ Промокод удален!")
    else:
        await callback.answer("❌ Промокод не найден!")
    
    await admin_list_promo(callback)

# ===== Управление чеками =====
@dp.callback_query(F.data == "admin_checks")
async def admin_checks_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    checks = await get_all_checks()
    active_checks = [c for c in checks if not c.get("used", False)]
    
    text = f"📦 *Управление чеками*\n\nАктивных чеков: {len(active_checks)}\nВсего создано: {len(checks)}\n\nВыберите действие:"
    
    buttons = [
        [InlineKeyboardButton(text="➕ Создать чек", callback_data="admin_create_check")],
        [InlineKeyboardButton(text="📋 Список чеков", callback_data="admin_list_checks")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_create_check")
async def admin_create_check(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    await state.set_state(AdminStates.waiting_for_check_amount)
    await callback.message.edit_text("📦 Введите сумму чека:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_checks")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_check_amount)
async def admin_create_check_amount(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав!")
        await state.clear()
        return
    
    try:
        amount = int(message.text)
        code = await generate_check(message.from_user.id, amount)
        await message.answer(f"✅ Чек создан!\n\n📦 Код: `{code}`\n💰 Сумма: {amount} ⭐\n\nОтправьте этот код пользователю.", parse_mode="Markdown")
        await log_admin_action(message.from_user.id, "create_check", None, f"Amount: {amount}, Code: {code}")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "admin_list_checks")
async def admin_list_checks(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    checks = await get_all_checks()
    active = [c for c in checks if not c.get("used", False)]
    used = [c for c in checks if c.get("used", False)]
    
    text = f"📦 *Список чеков*\n\n"
    text += f"🟢 Активных: {len(active)}\n"
    text += f"🔴 Использовано: {len(used)}\n\n"
    
    if active:
        text += "*Активные чеки:*\n"
        for c in active[:10]:
            text += f"└ `{c['code']}` - {c['amount']} ⭐\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_checks")]
    ]))
    await callback.answer()

# ===== Управление турнирами =====
@dp.callback_query(F.data == "admin_tournaments")
async def admin_tournaments_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    active = await get_active_tournament()
    history = await get_tournament_history()
    
    text = f"🏆 *Управление турнирами*\n\n"
    text += f"🟢 Активный турнир: {'Да' if active else 'Нет'}\n"
    text += f"📜 Завершено турниров: {len(history)}\n\n"
    text += "Выберите действие:"
    
    buttons = [
        [InlineKeyboardButton(text="➕ Создать турнир", callback_data="admin_create_tournament")],
        [InlineKeyboardButton(text="📜 История турниров", callback_data="admin_tournament_history")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]
    
    if active:
        buttons.insert(1, [InlineKeyboardButton(text="🏆 Текущий турнир", callback_data="admin_current_tournament")])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "admin_create_tournament")
async def admin_create_tournament(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
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
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав!")
        await state.clear()
        return
    
    await state.update_data(tournament_name=message.text)
    await state.set_state(AdminStates.waiting_for_tournament_prize)
    await message.answer("💰 Введите призовой фонд (звезды):")

@dp.message(AdminStates.waiting_for_tournament_prize)
async def admin_tournament_prize(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав!")
        await state.clear()
        return
    
    try:
        prize = int(message.text)
        await state.update_data(tournament_prize=prize)
        await state.set_state(AdminStates.waiting_for_tournament_duration)
        await message.answer("⏰ Введите длительность в часах:")
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(AdminStates.waiting_for_tournament_duration)
async def admin_tournament_duration(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав!")
        await state.clear()
        return
    
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
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    active = await get_active_tournament()
    if not active:
        await callback.answer("Нет активного турнира!")
        return
    
    end_time = datetime.fromisoformat(active["end_time"])
    time_left = end_time - datetime.now()
    hours = time_left.seconds // 3600
    minutes = (time_left.seconds % 3600) // 60
    
    text = f"🏆 *Текущий турнир*\n\n"
    text += f"✨ Название: {active['name']}\n"
    text += f"💰 Призовой фонд: {active['prize_pool']} ⭐\n"
    text += f"👥 Участников: {len(active['participants'])}\n"
    text += f"⏰ Осталось: {hours}ч {minutes}м\n\n"
    text += "*Топ 10 участников:*\n"
    
    top = sorted(active["participants"].items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (uid, points) in enumerate(top, 1):
        text += f"{i}. ID: {uid} - {points} очков\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_tournaments")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_tournament_history")
async def admin_tournament_history(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    history = await get_tournament_history()
    
    if not history:
        text = "📜 *История турниров*\n\nНет завершенных турниров."
    else:
        text = "📜 *История турниров:*\n\n"
        for t in history[-5:]:
            text += f"🏆 {t['name']}\n"
            text += f"└ Приз: {t['prize_pool']} ⭐\n"
            text += f"└ Участников: {len(t['participants'])}\n"
            text += f"└ Завершен: {t['ended_at'][:10]}\n\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_tournaments")]
    ]))
    await callback.answer()

# ===== Управление выводами =====
@dp.callback_query(F.data == "admin_withdrawals")
async def admin_withdrawals_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    pending = await get_pending_withdrawals()
    
    if not pending:
        text = "💰 *Заявки на вывод*\n\nНет активных заявок."
        buttons = [[InlineKeyboardButton(text="📜 История выводов", callback_data="admin_withdrawal_history")],
                   [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]]
    else:
        text = f"💰 *Заявки на вывод*\n\nВсего заявок: {len(pending)}\n\n"
        buttons = []
        for w in pending[:10]:
            text += f"*ID {w['id']}:* @{w['username']}\n└ Сумма: {w['stars']} ⭐\n└ Дата: {w['created_at'][:19]}\n\n"
            buttons.append([
                InlineKeyboardButton(text=f"✅ Подтвердить {w['id']}", callback_data=f"admin_approve_{w['id']}"),
                InlineKeyboardButton(text=f"❌ Отклонить {w['id']}", callback_data=f"admin_decline_{w['id']}")
            ])
        buttons.append([InlineKeyboardButton(text="📜 История выводов", callback_data="admin_withdrawal_history")])
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_approve_"))
async def admin_approve_withdrawal(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    wid = callback.data.replace("admin_approve_", "")
    success = await approve_withdrawal(wid, callback.from_user.id)
    
    if success:
        withdrawals = await load_json(WITHDRAWALS_FILE, {})
        w = withdrawals[wid]
        try:
            await bot.send_message(w["user_id"], f"✅ Ваша заявка на вывод #{wid} одобрена!\n⭐ Сумма: {w['stars']} звезд", parse_mode="Markdown")
        except:
            pass
        await callback.answer("✅ Заявка подтверждена!")
    else:
        await callback.answer("❌ Ошибка!")
    
    await admin_withdrawals_menu(callback)

@dp.callback_query(F.data.startswith("admin_decline_"))
async def admin_decline_withdrawal(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    wid = callback.data.replace("admin_decline_", "")
    success = await decline_withdrawal(wid, callback.from_user.id)
    
    if success:
        withdrawals = await load_json(WITHDRAWALS_FILE, {})
        w = withdrawals[wid]
        try:
            await bot.send_message(w["user_id"], f"❌ Ваша заявка на вывод #{wid} отклонена!\n⭐ Звезды возвращены на баланс.", parse_mode="Markdown")
        except:
            pass
        await callback.answer("✅ Заявка отклонена!")
    else:
        await callback.answer("❌ Ошибка!")
    
    await admin_withdrawals_menu(callback)

@dp.callback_query(F.data == "admin_withdrawal_history")
async def admin_withdrawal_history(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    withdrawals = await get_all_withdrawals()
    approved = [w for w in withdrawals if w["status"] == "approved"]
    declined = [w for w in withdrawals if w["status"] == "declined"]
    
    text = f"📜 *История выводов*\n\n"
    text += f"✅ Подтверждено: {len(approved)}\n"
    text += f"❌ Отклонено: {len(declined)}\n"
    text += f"⏳ В обработке: {len([w for w in withdrawals if w['status'] == 'pending'])}\n\n"
    
    if approved[-10:]:
        text += "*Последние 10 выводов:*\n"
        for w in approved[-10:]:
            text += f"└ #{w['id']} - @{w['username']} - {w['stars']} ⭐ - {w['approved_at'][:10]}\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_withdrawals")]
    ]))
    await callback.answer()

# ===== Настройки бота =====
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
            f"🎰 Казино: {'✅ Вкл' if settings.get('casino_enabled', True) else '❌ Выкл'}\n"
            f"🏆 Турниры: {'✅ Вкл' if settings.get('tournament_enabled', True) else '❌ Выкл'}\n"
            f"🎲 Мин. ставка: {settings.get('min_bet', 1)}\n"
            f"🎲 Макс. ставка: {settings.get('max_bet', 10000)}\n\n"
            f"Выберите параметр для изменения:")
    
    buttons = [
        [InlineKeyboardButton(text="⭐ Стартовый баланс", callback_data="set_start_balance"),
         InlineKeyboardButton(text="💰 Мин. вывод", callback_data="set_min_withdraw")],
        [InlineKeyboardButton(text="👥 Реф. награда", callback_data="set_referral_reward"),
         InlineKeyboardButton(text="📊 Реф. процент", callback_data="set_referral_percent")],
        [InlineKeyboardButton(text="💱 Курс обмена", callback_data="set_exchange_rate"),
         InlineKeyboardButton(text="🎰 Казино", callback_data="set_casino")],
        [InlineKeyboardButton(text="🏆 Турниры", callback_data="set_tournaments"),
         InlineKeyboardButton(text="🎲 Мин. ставка", callback_data="set_min_bet")],
        [InlineKeyboardButton(text="🎲 Макс. ставка", callback_data="set_max_bet"),
         InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("set_"))
async def admin_setting_change(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    setting = callback.data.replace("set_", "")
    
    # Toggle settings
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
    
    # Numeric settings
    await state.update_data(setting=setting)
    await state.set_state(AdminStates.waiting_for_setting_value)
    
    names = {
        "start_balance": "стартовый баланс", "min_withdraw": "мин. вывод",
        "referral_reward": "реф. награду", "referral_percent": "реф. процент",
        "exchange_rate": "курс обмена", "min_bet": "мин. ставку", "max_bet": "макс. ставку"
    }
    await callback.message.edit_text(f"📝 Введите {names.get(setting, setting)}:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_settings")]
    ]))
    await callback.answer()

@dp.message(AdminStates.waiting_for_setting_value)
async def admin_save_setting(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав!")
        await state.clear()
        return
    
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

# ===== Статистика =====
@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    users = await load_json(USERS_FILE, {})
    withdrawals = await load_json(WITHDRAWALS_FILE, {})
    tasks = await get_all_tasks()
    promo = await get_all_promo()
    checks = await get_all_checks()
    active_tournament = await get_active_tournament()
    
    total_stars = sum(u.get("stars", 0) for u in users.values())
    total_earned = sum(u.get("total_earned", 0) for u in users.values())
    total_spent = sum(u.get("total_spent", 0) for u in users.values())
    total_purchases = sum(u.get("total_purchases", 0) for u in users.values())
    total_users = len(users)
    pending_withdrawals = len([w for w in withdrawals.values() if w.get("status") == "pending"])
    total_withdrawals = len([w for w in withdrawals.values() if w.get("status") == "approved"])
    active_checks = len([c for c in checks if not c.get("used", False)])
    
    text = (f"📊 *Общая статистика*\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"⭐ Всего звезд: {total_stars}\n"
            f"💰 Всего заработано: {total_earned}\n"
            f"💸 Всего потрачено: {total_spent}\n"
            f"🛒 Всего покупок: {total_purchases}\n"
            f"💰 Средний баланс: {total_stars // total_users if total_users else 0}\n\n"
            f"📋 Заданий: {len(tasks)}\n"
            f"🎫 Промокодов: {len(promo)}\n"
            f"📦 Активных чеков: {active_checks}\n"
            f"🏆 Активный турнир: {'Да' if active_tournament else 'Нет'}\n\n"
            f"💰 Выводов: {total_withdrawals}\n"
            f"⏳ Ожидают вывода: {pending_withdrawals}")
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]))
    await callback.answer()

# ===== Логи =====
@dp.callback_query(F.data == "admin_logs")
async def admin_logs(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    logs = await load_json(ADMIN_LOGS_FILE, [])
    
    if not logs:
        text = "📝 *Логи действий*\n\nНет записей."
    else:
        text = "📝 *Последние действия:*\n\n"
        for log in logs[-20:]:
            text += f"🕒 {log['timestamp'][:19]}\n"
            text += f"👤 Админ: {log['admin_id']}\n"
            text += f"📌 Действие: {log['action']}\n"
            if log.get('target'):
                text += f"🎯 Цель: {log['target']}\n"
            if log.get('details'):
                text += f"📝 Детали: {log['details']}\n"
            text += "➖➖➖➖➖➖➖\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Очистить логи", callback_data="admin_clear_logs")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_clear_logs")
async def admin_clear_logs(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    await save_json(ADMIN_LOGS_FILE, [])
    await callback.answer("✅ Логи очищены!", show_alert=True)
    await admin_logs(callback)

# Фоновая задача для проверки турниров
async def check_tournaments_task():
    while True:
        await asyncio.sleep(60)
        tournaments = await load_json(TOURNAMENTS_FILE, {"active": None})
        if tournaments["active"]:
            end_time = datetime.fromisoformat(tournaments["active"]["end_time"])
            if datetime.now() >= end_time:
                await end_tournament()

# Запуск бота
async def main():
    await init_data()
    asyncio.create_task(check_tournaments_task())
    logger.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
