import telebot
from telebot import types
import json
import random
import time
import threading
from datetime import datetime, timedelta
import re
import math
import copy

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = '8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE'
ADMIN_ID = 5356400377
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ==================== ФАЙЛЫ ДАННЫХ ====================
DATA_FILES = {
    'users': 'users.json',
    'items': 'items.json',
    'active_duels': 'active_duels.json',
    'limited_items': 'limited_items.json',
    'clans': 'clans.json',
    'tournaments': 'tournaments.json',
    'achievements': 'achievements.json',
    'quests': 'quests.json',
    'market': 'market.json',
    'duel_history': 'duel_history.json',
    'guild_wars': 'guild_wars.json'
}

# ==================== ЗАГРУЗКА/СОХРАНЕНИЕ ДАННЫХ ====================
def load_json(filename, default=None):
    if default is None:
        default = {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data is None:
                return default
            return data
    except FileNotFoundError:
        save_json(filename, default)
        return default
    except json.JSONDecodeError:
        print(f"⚠ Ошибка чтения {filename}, создаю новый")
        save_json(filename, default)
        return default
    except Exception as e:
        print(f"❌ Критическая ошибка загрузки {filename}: {e}")
        return default

def save_json(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения {filename}: {e}")
        return False

def safe_get(dictionary, key, default=None):
    """Безопасное получение значения из словаря"""
    try:
        return dictionary.get(key, default)
    except:
        return default

# ==================== ИНИЦИАЛИЗАЦИЯ ПРЕДМЕТОВ ====================
SHOP_ITEMS = {
    # ОРУЖИЕ
    "wooden_sword": {
        "id": "wooden_sword",
        "name": "🗡 Деревянный меч",
        "type": "weapon",
        "rarity": "common",
        "price": 100,
        "damage": 5,
        "level_req": 1,
        "description": "Простой меч из дуба. Надёжен для новичка.",
        "emoji": "🗡",
        "stats": {"damage": 5}
    },
    "stone_blade": {
        "id": "stone_blade",
        "name": "🗿 Каменный клинок",
        "type": "weapon",
        "rarity": "common",
        "price": 250,
        "damage": 8,
        "level_req": 3,
        "description": "Грубый, но мощный каменный клинок.",
        "emoji": "🗿",
        "stats": {"damage": 8, "crit_chance": 2}
    },
    "iron_sword": {
        "id": "iron_sword",
        "name": "⚔ Железный меч",
        "type": "weapon",
        "rarity": "uncommon",
        "price": 500,
        "damage": 12,
        "level_req": 5,
        "description": "Крепкий железный меч, проверенный в боях.",
        "emoji": "⚔",
        "stats": {"damage": 12, "crit_chance": 5}
    },
    "shadow_blade": {
        "id": "shadow_blade",
        "name": "🌑 Теневой клинок",
        "type": "weapon",
        "rarity": "rare",
        "price": 1200,
        "damage": 18,
        "level_req": 8,
        "description": "Клинок, скрывающийся в тенях. Шанс критического удара.",
        "emoji": "🌑",
        "stats": {"damage": 18, "crit_chance": 10, "crit_multiplier": 2.0}
    },
    "mythril_blade": {
        "id": "mythril_blade",
        "name": "✨ Мифриловый меч",
        "type": "weapon",
        "rarity": "epic",
        "price": 3000,
        "damage": 25,
        "level_req": 12,
        "description": "Лёгкий мифриловый меч с магическим уроном.",
        "emoji": "✨",
        "stats": {"damage": 25, "crit_chance": 12, "magic_damage": 10}
    },
    "dragon_fang": {
        "id": "dragon_fang",
        "name": "🐉 Клык Дракона",
        "type": "weapon",
        "rarity": "legendary",
        "price": 8000,
        "damage": 40,
        "level_req": 20,
        "description": "Меч из клыка древнего дракона. Наносит огромный урон.",
        "emoji": "🐉",
        "stats": {"damage": 40, "crit_chance": 20, "fire_damage": 15}
    },
    "excalibur": {
        "id": "excalibur",
        "name": "⚡ Экскалибур",
        "type": "weapon",
        "rarity": "mythic",
        "price": 20000,
        "damage": 60,
        "level_req": 30,
        "description": "Легендарный меч короля Артура. Молнии поражают врагов!",
        "emoji": "⚡",
        "stats": {"damage": 60, "crit_chance": 25, "chain_lightning": 30}
    },
    
    # ЩИТЫ
    "wooden_shield": {
        "id": "wooden_shield",
        "name": "🛡 Деревянный щит",
        "type": "shield",
        "rarity": "common",
        "price": 150,
        "defense": 5,
        "level_req": 1,
        "description": "Простой деревянный щит. Базовая защита.",
        "emoji": "🛡",
        "stats": {"defense": 5}
    },
    "iron_shield": {
        "id": "iron_shield",
        "name": "🛡 Железный щит",
        "type": "shield",
        "rarity": "uncommon",
        "price": 600,
        "defense": 12,
        "level_req": 5,
        "description": "Надёжный железный щит с шипами.",
        "emoji": "🛡",
        "stats": {"defense": 12, "damage_reflect": 5}
    },
    "tower_shield": {
        "id": "tower_shield",
        "name": "🏰 Башенный щит",
        "type": "shield",
        "rarity": "rare",
        "price": 2000,
        "defense": 25,
        "level_req": 10,
        "description": "Огромный щит, закрывающий всё тело.",
        "emoji": "🏰",
        "stats": {"defense": 25, "block_chance": 15}
    },
    "dragon_scale_shield": {
        "id": "dragon_scale_shield",
        "name": "🐉 Щит Драконьей Чешуи",
        "type": "shield",
        "rarity": "epic",
        "price": 6000,
        "defense": 40,
        "level_req": 18,
        "description": "Щит из чешуи дракона. Отражает часть урона.",
        "emoji": "🐉",
        "stats": {"defense": 40, "damage_reflect": 15, "fire_resist": 20}
    },
    "aegis": {
        "id": "aegis",
        "name": "💫 Эгида",
        "type": "shield",
        "rarity": "legendary",
        "price": 15000,
        "defense": 60,
        "level_req": 25,
        "description": "Божественный щит Зевса. Непробиваемая защита!",
        "emoji": "💫",
        "stats": {"defense": 60, "block_chance": 30, "magic_resist": 25}
    },
    
    # БРОНЯ
    "leather_armor": {
        "id": "leather_armor",
        "name": "🧥 Кожаная броня",
        "type": "armor",
        "rarity": "common",
        "price": 120,
        "hp_bonus": 15,
        "defense": 3,
        "level_req": 1,
        "description": "Лёгкая кожаная броня для начинающих.",
        "emoji": "🧥",
        "stats": {"hp_bonus": 15, "defense": 3}
    },
    "chainmail": {
        "id": "chainmail",
        "name": "⛓ Кольчуга",
        "type": "armor",
        "rarity": "uncommon",
        "price": 500,
        "hp_bonus": 30,
        "defense": 8,
        "level_req": 5,
        "description": "Прочная кольчуга, проверенная временем.",
        "emoji": "⛓",
        "stats": {"hp_bonus": 30, "defense": 8}
    },
    "plate_armor": {
        "id": "plate_armor",
        "name": "🛡 Латная броня",
        "type": "armor",
        "rarity": "rare",
        "price": 2000,
        "hp_bonus": 60,
        "defense": 15,
        "level_req": 12,
        "description": "Тяжёлая латная броня. Отличная защита!",
        "emoji": "🛡",
        "stats": {"hp_bonus": 60, "defense": 15}
    },
    "dragon_armor": {
        "id": "dragon_armor",
        "name": "🐉 Драконья броня",
        "type": "armor",
        "rarity": "legendary",
        "price": 10000,
        "hp_bonus": 120,
        "defense": 25,
        "level_req": 25,
        "description": "Великая броня из драконьей шкуры.",
        "emoji": "🐉",
        "stats": {"hp_bonus": 120, "defense": 25, "fire_resist": 30}
    },
    
    # АКСЕССУАРЫ
    "strength_ring": {
        "id": "strength_ring",
        "name": "💍 Кольцо Силы",
        "type": "accessory",
        "rarity": "uncommon",
        "price": 800,
        "level_req": 7,
        "description": "Увеличивает физический урон.",
        "emoji": "💍",
        "stats": {"damage": 7}
    },
    "lucky_charm": {
        "id": "lucky_charm",
        "name": "🍀 Талисман Удачи",
        "type": "accessory",
        "rarity": "rare",
        "price": 1500,
        "level_req": 10,
        "description": "Повышает шанс критического удара.",
        "emoji": "🍀",
        "stats": {"crit_chance": 15}
    },
    "vampire_amulet": {
        "id": "vampire_amulet",
        "name": "🩸 Амулет Вампира",
        "type": "accessory",
        "rarity": "epic",
        "price": 5000,
        "level_req": 15,
        "description": "Крадёт здоровье у противника.",
        "emoji": "🩸",
        "stats": {"lifesteal": 15}
    },
    "phoenix_feather": {
        "id": "phoenix_feather",
        "name": "🦅 Перо Феникса",
        "type": "accessory",
        "rarity": "legendary",
        "price": 12000,
        "level_req": 22,
        "description": "Даёт шанс воскреснуть после смерти.",
        "emoji": "🦅",
        "stats": {"revive_chance": 20}
    },
    
    # ЗЕЛЬЯ
    "health_potion": {
        "id": "health_potion",
        "name": "🧪 Зелье здоровья",
        "type": "potion",
        "rarity": "common",
        "price": 50,
        "heal": 30,
        "description": "Восстанавливает 30 HP.",
        "emoji": "🧪",
        "stats": {"heal": 30}
    },
    "big_potion": {
        "id": "big_potion",
        "name": "🧪 Большое зелье",
        "type": "potion",
        "rarity": "uncommon",
        "price": 150,
        "heal": 75,
        "description": "Восстанавливает 75 HP.",
        "emoji": "🧪",
        "stats": {"heal": 75}
    },
    "elixir": {
        "id": "elixir",
        "name": "💊 Эликсир жизни",
        "type": "potion",
        "rarity": "epic",
        "price": 500,
        "heal": 200,
        "description": "Мощное исцеление! +200 HP.",
        "emoji": "💊",
        "stats": {"heal": 200}
    },
    "full_restore": {
        "id": "full_restore",
        "name": "🌟 Полное восстановление",
        "type": "potion",
        "rarity": "legendary",
        "price": 1500,
        "heal": 9999,
        "description": "Полностью восстанавливает здоровье!",
        "emoji": "🌟",
        "stats": {"full_heal": True}
    },
    
    # ОБУВЬ
    "leather_boots": {
        "id": "leather_boots",
        "name": "👢 Кожаные сапоги",
        "type": "boots",
        "rarity": "common",
        "price": 200,
        "speed": 5,
        "level_req": 3,
        "description": "Увеличивает скорость на 5%.",
        "emoji": "👢",
        "stats": {"speed": 5}
    },
    "wind_walkers": {
        "id": "wind_walkers",
        "name": "💨 Сапоги Ветра",
        "type": "boots",
        "rarity": "rare",
        "price": 2500,
        "speed": 15,
        "level_req": 12,
        "description": "Значительно увеличивают скорость.",
        "emoji": "💨",
        "stats": {"speed": 15, "dodge_chance": 5}
    },
    "hermes_boots": {
        "id": "hermes_boots",
        "name": "👟 Сапоги Гермеса",
        "type": "boots",
        "rarity": "legendary",
        "price": 8000,
        "speed": 30,
        "level_req": 20,
        "description": "Божественная скорость! +30% к первому удару.",
        "emoji": "👟",
        "stats": {"speed": 30, "dodge_chance": 15}
    }
}

# Лимитированные предметы
LIMITED_ITEMS = {
    "thunderfury": {
        "id": "thunderfury",
        "name": "⚡ Ярость Грома",
        "type": "weapon",
        "rarity": "divine",
        "price": 50000,
        "damage": 100,
        "total": 5,
        "remaining": 5,
        "level_req": 35,
        "description": "Благословлённый богами меч. Вызывает цепные молнии!",
        "emoji": "⚡",
        "stats": {"damage": 100, "chain_lightning": 50, "crit_chance": 30},
        "special": "Молнии поражают всех врагов"
    },
    "world_ender": {
        "id": "world_ender",
        "name": "🌋 Конец Света",
        "type": "weapon",
        "rarity": "apocalyptic",
        "price": 100000,
        "damage": 150,
        "total": 1,
        "remaining": 1,
        "level_req": 50,
        "description": "Единственный в мире! Уничтожает всё на своём пути.",
        "emoji": "🌋",
        "stats": {"damage": 150, "armageddon": 100, "crit_chance": 50},
        "special": "Шанс уничтожить врага одной атакой (10%)"
    },
    "infinity_gauntlet": {
        "id": "infinity_gauntlet",
        "name": "🔮 Перчатка Бесконечности",
        "type": "accessory",
        "rarity": "divine",
        "price": 75000,
        "total": 3,
        "remaining": 3,
        "level_req": 40,
        "description": "Дарует невероятную силу! Все характеристики повышены.",
        "emoji": "🔮",
        "stats": {"damage": 25, "crit_chance": 20, "lifesteal": 10, 
                  "dodge_chance": 10, "defense": 15},
        "special": "+25% ко всем характеристикам"
    },
    "cloak_of_invisibility": {
        "id": "cloak_of_invisibility",
        "name": "👻 Плащ Невидимка",
        "type": "armor",
        "rarity": "mythic",
        "price": 45000,
        "total": 7,
        "remaining": 7,
        "hp_bonus": 80,
        "defense": 30,
        "level_req": 30,
        "description": "Делает владельца невидимым! Шанс избежать атаки.",
        "emoji": "👻",
        "stats": {"hp_bonus": 80, "defense": 30, "dodge_chance": 25},
        "special": "Шанс стать невидимым на 2 хода (15%)"
    },
    "phoenix_armor": {
        "id": "phoenix_armor",
        "name": "🦅 Броня Феникса",
        "type": "armor",
        "rarity": "divine",
        "price": 80000,
        "total": 5,
        "remaining": 5,
        "hp_bonus": 200,
        "defense": 50,
        "level_req": 45,
        "description": "Легендарная броня! Возрождает после смерти!",
        "emoji": "🦅",
        "stats": {"hp_bonus": 200, "defense": 50, "revive_chance": 50},
        "special": "Шанс полного восстановления HP (25%)"
    }
}

# Система достижений
ACHIEVEMENTS_LIST = {
    "first_blood": {
        "name": "🩸 Первая кровь",
        "desc": "Одержите победу в дуэли",
        "reward": 200,
        "condition": lambda u: u.get("wins", 0) >= 1
    },
    "warrior": {
        "name": "⚔ Воитель",
        "desc": "Одержите 10 побед",
        "reward": 500,
        "condition": lambda u: u.get("wins", 0) >= 10
    },
    "veteran": {
        "name": "🎖 Ветеран",
        "desc": "Одержите 50 побед",
        "reward": 2000,
        "condition": lambda u: u.get("wins", 0) >= 50
    },
    "legend": {
        "name": "👑 Легенда",
        "desc": "Одержите 100 побед",
        "reward": 5000,
        "condition": lambda u: u.get("wins", 0) >= 100
    },
    "god_of_war": {
        "name": "⚡ Бог Войны",
        "desc": "Достигните 500 побед",
        "reward": 25000,
        "condition": lambda u: u.get("wins", 0) >= 500
    },
    "rich": {
        "name": "💰 Богач",
        "desc": "Накопите 10,000 монет",
        "reward": 1000,
        "condition": lambda u: u.get("money", 0) >= 10000
    },
    "millionaire": {
        "name": "💎 Миллионер",
        "desc": "Накопите 100,000 монет",
        "reward": 10000,
        "condition": lambda u: u.get("money", 0) >= 100000
    },
    "collector": {
        "name": "🎒 Коллекционер",
        "desc": "Соберите 20 предметов",
        "reward": 1500,
        "condition": lambda u: len(u.get("inventory", [])) >= 20
    },
    "dragon_slayer": {
        "name": "🐉 Убийца Драконов",
        "desc": "Победите в 10 дуэлях подряд",
        "reward": 3000,
        "condition": lambda u: u.get("best_streak", 0) >= 10
    },
    "undefeated": {
        "name": "🔥 Непобедимый",
        "desc": "Достигните серии из 25 побед",
        "reward": 10000,
        "condition": lambda u: u.get("best_streak", 0) >= 25
    },
    "level_master": {
        "name": "⭐ Мастер Уровней",
        "desc": "Достигните 30 уровня",
        "reward": 3000,
        "condition": lambda u: u.get("level", 1) >= 30
    },
    "level_god": {
        "name": "🌟 Бог Уровней",
        "desc": "Достигните 50 уровня",
        "reward": 10000,
        "condition": lambda u: u.get("level", 1) >= 50
    },
    "critical_master": {
        "name": "💥 Мастер Крита",
        "desc": "Нанесите 50 критических ударов",
        "reward": 2000,
        "condition": lambda u: u.get("critical_hits", 0) >= 50
    },
    "survivor": {
        "name": "💪 Выживший",
        "desc": "Выиграйте дуэль с HP < 10",
        "reward": 1000,
        "condition": lambda u: u.get("close_wins", 0) >= 5
    },
    "perfect_warrior": {
        "name": "✨ Идеальный Воин",
        "desc": "Выиграйте без потери HP",
        "reward": 2500,
        "condition": lambda u: u.get("perfect_wins", 0) >= 3
    }
}

# Ежедневные квесты
DAILY_QUESTS_POOL = [
    {
        "name": "Тренировочный день",
        "desc": "Проведите 3 дуэли",
        "type": "duels",
        "target": 3,
        "reward_money": 300,
        "reward_exp": 50
    },
    {
        "name": "Победный марш",
        "desc": "Выиграйте 2 дуэли",
        "type": "wins",
        "target": 2,
        "reward_money": 500,
        "reward_exp": 80
    },
    {
        "name": "Шопинг",
        "desc": "Купите 3 предмета",
        "type": "purchases",
        "target": 3,
        "reward_money": 250,
        "reward_exp": 40
    },
    {
        "name": "Исследователь",
        "desc": "Используйте /explore 5 раз",
        "type": "explore",
        "target": 5,
        "reward_money": 350,
        "reward_exp": 60
    },
    {
        "name": "Коллекционер зелий",
        "desc": "Используйте 3 зелья",
        "type": "potions",
        "target": 3,
        "reward_money": 200,
        "reward_exp": 45
    },
    {
        "name": "Смертельная битва",
        "desc": "Нанесите 500 урона в дуэлях",
        "type": "damage",
        "target": 500,
        "reward_money": 400,
        "reward_exp": 70
    },
    {
        "name": "Критический успех",
        "desc": "Нанесите 5 критических ударов",
        "type": "crits",
        "target": 5,
        "reward_money": 600,
        "reward_exp": 90
    },
    {
        "name": "Богатый день",
        "desc": "Заработайте 1000 монет",
        "type": "earn",
        "target": 1000,
        "reward_money": 500,
        "reward_exp": 50
    }
]

# Загрузка всех данных
users = load_json(DATA_FILES['users'], {})
active_duels = load_json(DATA_FILES['active_duels'], {})
clans = load_json(DATA_FILES['clans'], {})
tournaments = load_json(DATA_FILES['tournaments'], {})
achievements_data = load_json(DATA_FILES['achievements'], {})
quests_data = load_json(DATA_FILES['quests'], {})
market_listings = load_json(DATA_FILES['market'], {})
duel_history = load_json(DATA_FILES['duel_history'], [])
limited_items_data = load_json(DATA_FILES['limited_items'], LIMITED_ITEMS)

# ==================== КЛАССЫ ====================
class Player:
    """Класс для управления игроком"""
    
    def __init__(self, user_id, username=None, first_name=None):
        self.user_id = str(user_id)
        if self.user_id not in users:
            users[self.user_id] = self._create_new_player(username, first_name)
            self._save()
    
    def _create_new_player(self, username, first_name):
        return {
            "user_id": self.user_id,
            "username": username or f"user_{self.user_id}",
            "first_name": first_name or "Игрок",
            "money": 500,
            "level": 1,
            "exp": 0,
            "hp": 100,
            "max_hp": 100,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "win_streak": 0,
            "best_streak": 0,
            "inventory": [],
            "equipped": {
                "weapon": None,
                "shield": None,
                "armor": None,
                "accessory": None,
                "boots": None
            },
            "last_daily": None,
            "last_explore": None,
            "title": "Новичок",
            "titles": ["Новичок"],
            "achievements": [],
            "active_quests": {},
            "quests_date": None,
            "completed_quests": 0,
            "clan": None,
            "total_damage_dealt": 0,
            "total_damage_taken": 0,
            "critical_hits": 0,
            "close_wins": 0,
            "perfect_wins": 0,
            "items_used": 0,
            "purchases_today": 0,
            "duels_today": 0,
            "wins_today": 0,
            "explore_today": 0,
            "potions_used_today": 0,
            "damage_today": 0,
            "crits_today": 0,
            "earned_today": 0,
            "registration_date": datetime.now().isoformat(),
            "settings": {
                "notifications": True,
                "duel_requests": True,
                "show_effects": True,
                "auto_use_potions": False
            }
        }
    
    @property
    def data(self):
        return users.get(self.user_id, self._create_new_player(None, None))
    
    def _save(self):
        users[self.user_id] = self.data
        save_json(DATA_FILES['users'], users)
    
    def get_stat(self, key, default=None):
        return self.data.get(key, default)
    
    def set_stat(self, key, value):
        self.data[key] = value
        self._save()
    
    def add_money(self, amount):
        self.data["money"] = self.data.get("money", 0) + amount
        self.data["earned_today"] = self.data.get("earned_today", 0) + max(0, amount)
        self._save()
    
    def add_exp(self, amount):
        self.data["exp"] = self.data.get("exp", 0) + amount
        self._save()
        return self.check_level_up()
    
    def check_level_up(self):
        level = self.data.get("level", 1)
        exp_needed = self._exp_for_level(level)
        leveled_up = False
        
        while self.data.get("exp", 0) >= exp_needed:
            self.data["exp"] -= exp_needed
            self.data["level"] = level + 1
            level += 1
            self.data["max_hp"] = 100 + (level - 1) * 10
            self.data["hp"] = self.data["max_hp"]
            leveled_up = True
            exp_needed = self._exp_for_level(level)
            
            # Проверка титулов
            titles_map = [
                (1, "Новичок"), (5, "Боец"), (10, "Воитель"),
                (15, "Рыцарь"), (20, "Ветеран"), (25, "Мастер"),
                (30, "Грандмастер"), (40, "Герой"), (50, "Легенда"),
                (60, "Мифический воин"), (75, "Полубог"), (100, "Божество")
            ]
            for req_lvl, title in titles_map:
                if level >= req_lvl and title not in self.data.get("titles", []):
                    self.data.setdefault("titles", []).append(title)
                    self.data["title"] = title
        
        self._save()
        return leveled_up
    
    def _exp_for_level(self, level):
        return int(100 * (1.5 ** (level - 1)))
    
    def has_item(self, item_id):
        return item_id in self.data.get("inventory", [])
    
    def add_item(self, item_id):
        self.data.setdefault("inventory", []).append(item_id)
        self._save()
    
    def remove_item(self, item_id):
        inventory = self.data.get("inventory", [])
        if item_id in inventory:
            inventory.remove(item_id)
            self._save()
            return True
        return False
    
    def equip_item(self, item_id):
        item = SHOP_ITEMS.get(item_id) or limited_items_data.get(item_id)
        if not item:
            return False, "Предмет не найден"
        
        if not self.has_item(item_id):
            return False, "Предмета нет в инвентаре"
        
        item_type = item["type"]
        equipped = self.data.get("equipped", {})
        
        if item_type not in equipped:
            return False, f"Нельзя экипировать предмет типа {item_type}"
        
        # Снимаем предыдущий предмет
        old_item = equipped[item_type]
        equipped[item_type] = item_id
        
        # Добавляем старый предмет обратно в инвентарь
        if old_item and old_item in self.data.get("inventory", []):
            pass  # Оставляем в инвентаре
        
        # Удаляем новый предмет из инвентаря
        inventory = self.data.get("inventory", [])
        if item_id in inventory:
            inventory.remove(item_id)
        
        self.data["equipped"] = equipped
        self._save()
        return True, f"{item['emoji']} {item['name']} экипирован!"
    
    def use_potion(self, item_id):
        item = SHOP_ITEMS.get(item_id) or limited_items_data.get(item_id)
        if not item or item.get("type") != "potion":
            return False, "Это не зелье"
        
        if not self.has_item(item_id):
            return False, "Зелья нет в инвентаре"
        
        current_hp = self.data.get("hp", 0)
        max_hp = self.data.get("max_hp", 100)
        
        if current_hp >= max_hp:
            return False, "У вас полное здоровье!"
        
        if item.get("stats", {}).get("full_heal"):
            heal_amount = max_hp - current_hp
        else:
            heal_amount = min(item.get("heal", 30), max_hp - current_hp)
        
        self.data["hp"] = current_hp + heal_amount
        self.remove_item(item_id)
        self.data["items_used"] = self.data.get("items_used", 0) + 1
        self.data["potions_used_today"] = self.data.get("potions_used_today", 0) + 1
        self._save()
        
        return True, f"💚 +{heal_amount} HP! Здоровье: {self.data['hp']}/{max_hp}"
    
    def calculate_stats(self):
        """Расчёт всех характеристик"""
        equipped = self.data.get("equipped", {})
        level = self.data.get("level", 1)
        
        stats = {
            "damage": level * 2,
            "defense": 0,
            "hp": self.data.get("hp", 100),
            "max_hp": self.data.get("max_hp", 100),
            "crit_chance": 5,
            "crit_multiplier": 1.5,
            "dodge_chance": 3,
            "speed": 0,
            "lifesteal": 0,
            "damage_reflect": 0,
            "block_chance": 0,
            "magic_resist": 0,
            "fire_resist": 0,
            "revive_chance": 0,
            "chain_lightning": 0,
            "armageddon": 0,
            "magic_damage": 0,
            "fire_damage": 0
        }
        
        # Применяем бонусы от экипировки
        for slot, item_id in equipped.items():
            if item_id:
                item = SHOP_ITEMS.get(item_id) or limited_items_data.get(item_id)
                if item:
                    item_stats = item.get("stats", {})
                    for key in stats:
                        if key in item_stats:
                            stats[key] += item_stats[key]
        
        # Ограничения
        stats["crit_chance"] = min(stats["crit_chance"], 80)
        stats["dodge_chance"] = min(stats["dodge_chance"], 50)
        stats["lifesteal"] = min(stats["lifesteal"], 50)
        stats["block_chance"] = min(stats["block_chance"], 40)
        
        return stats

class DuelSystem:
    """Система управления дуэлями"""
    
    @staticmethod
    def create_duel(challenger_id, opponent_id, duel_type="normal", bet=0):
        duel_id = f"duel_{int(time.time())}_{random.randint(1000,9999)}"
        
        duel_data = {
            "id": duel_id,
            "challenger_id": str(challenger_id),
            "opponent_id": str(opponent_id),
            "type": duel_type,
            "bet": bet,
            "status": "active",
            "turn": 1,
            "round": 0,
            "max_rounds": 30,
            "p1_hp": 0,
            "p2_hp": 0,
            "p1_max_hp": 0,
            "p2_max_hp": 0,
            "log": [],
            "effects": {
                "p1": [],
                "p2": []
            },
            "created_at": datetime.now().isoformat()
        }
        
        active_duels[duel_id] = duel_data
        save_json(DATA_FILES['active_duels'], active_duels)
        return duel_id
    
    @staticmethod
    def execute_duel(duel_id):
        """Выполнение дуэли и определение победителя"""
        if duel_id not in active_duels:
            return None
        
        duel = active_duels[duel_id]
        p1 = Player(duel["challenger_id"])
        p2 = Player(duel["opponent_id"])
        
        if not p1.data or not p2.data:
            return None
        
        stats1 = p1.calculate_stats()
        stats2 = p2.calculate_stats()
        
        p1_hp = stats1["max_hp"]
        p2_hp = stats2["max_hp"]
        p1_max_hp = p1_hp
        p2_max_hp = p2_hp
        
        # Определяем очередность по скорости
        if stats1["speed"] > stats2["speed"]:
            attacker, defender = "p1", "p2"
        elif stats2["speed"] > stats1["speed"]:
            attacker, defender = "p2", "p1"
        else:
            attacker, defender = random.choice([("p1", "p2"), ("p2", "p1")])
        
        battle_log = []
        round_num = 0
        
        while round_num < duel["max_rounds"] and p1_hp > 0 and p2_hp > 0:
            round_num += 1
            
            # Получаем статы атакующего и защищающегося
            if attacker == "p1":
                atk_stats, def_stats = stats1, stats2
                atk_name = p1.data.get("first_name", "Игрок 1")
                def_name = p2.data.get("first_name", "Игрок 2")
            else:
                atk_stats, def_stats = stats2, stats1
                atk_name = p2.data.get("first_name", "Игрок 2")
                def_name = p1.data.get("first_name", "Игрок 1")
            
            # Расчёт урона
            base_damage = atk_stats["damage"]
            bonus_damage = atk_stats.get("magic_damage", 0) + atk_stats.get("fire_damage", 0)
            
            # Критический удар
            is_crit = random.random() * 100 < atk_stats["crit_chance"]
            if is_crit:
                crit_mult = atk_stats["crit_multiplier"]
                base_damage = int(base_damage * crit_mult)
                battle_log.append(f"💥 {atk_name} наносит КРИТИЧЕСКИЙ УДАР!")
                p1.set_stat("critical_hits", p1.get_stat("critical_hits", 0) + 1)
                p1.set_stat("crits_today", p1.get_stat("crits_today", 0) + 1)
            
            total_damage = base_damage + bonus_damage + random.randint(-5, 5)
            
            # Проверка уклонения
            if random.random() * 100 < def_stats["dodge_chance"]:
                battle_log.append(f"🌀 {def_name} уклоняется от атаки!")
                total_damage = 0
            
            # Проверка блока
            if total_damage > 0 and random.random() * 100 < def_stats["block_chance"]:
                blocked = int(total_damage * 0.5)
                total_damage -= blocked
                battle_log.append(f"🛡 {def_name} блокирует {blocked} урона!")
            
            # Применение защиты
            if total_damage > 0:
                total_damage = max(1, total_damage - def_stats["defense"])
            
            # Вампиризм
            if atk_stats["lifesteal"] > 0 and total_damage > 0:
                heal = int(total_damage * atk_stats["lifesteal"] / 100)
                if heal > 0:
                    if attacker == "p1":
                        p1_hp = min(p1_max_hp, p1_hp + heal)
                    else:
                        p2_hp = min(p2_max_hp, p2_hp + heal)
                    battle_log.append(f"💚 {atk_name} крадёт {heal} здоровья!")
            
            # Отражение урона
            if def_stats["damage_reflect"] > 0 and total_damage > 0:
                reflect = int(total_damage * def_stats["damage_reflect"] / 100)
                if reflect > 0:
                    if attacker == "p1":
                        p2_hp -= reflect
                    else:
                        p1_hp -= reflect
                    battle_log.append(f"🔄 {def_name} отражает {reflect} урона!")
            
            # Нанесение урона
            if total_damage > 0:
                if attacker == "p1":
                    p2_hp -= total_damage
                else:
                    p1_hp -= total_damage
                battle_log.append(f"⚔ {atk_name} наносит {total_damage} урона!")
                
                # Специальные эффекты
                if atk_stats.get("chain_lightning", 0) > 0:
                    bonus_dmg = int(atk_stats["chain_lightning"] * 0.3)
                    if attacker == "p1":
                        p2_hp -= bonus_dmg
                    else:
                        p1_hp -= bonus_dmg
                    battle_log.append(f"⚡ Цепная молния наносит {bonus_dmg} доп. урона!")
                
                if atk_stats.get("armageddon", 0) > 0 and random.random() < 0.1:
                    if attacker == "p1":
                        p2_hp = 0
                    else:
                        p1_hp = 0
                    battle_log.append(f"🌋 АРМАГЕДДОН! Мгновенное поражение!")
            
            # Проверка воскрешения
            if p1_hp <= 0 and stats1.get("revive_chance", 0) > 0:
                if random.random() * 100 < stats1["revive_chance"]:
                    p1_hp = int(p1_max_hp * 0.5)
                    battle_log.append(f"🦅 {p1.data.get('first_name')} ВОСКРЕСАЕТ!")
            
            if p2_hp <= 0 and stats2.get("revive_chance", 0) > 0:
                if random.random() * 100 < stats2["revive_chance"]:
                    p2_hp = int(p2_max_hp * 0.5)
                    battle_log.append(f"🦅 {p2.data.get('first_name')} ВОСКРЕСАЕТ!")
            
            # Меняем атакующего и защищающегося
            attacker, defender = defender, attacker
        
        # Определение победителя
        if p1_hp <= 0 and p2_hp <= 0:
            winner = None
            result = "draw"
        elif p2_hp <= 0:
            winner = p1
            result = "p1_win"
        elif p1_hp <= 0:
            winner = p2
            result = "p2_win"
        else:
            # Закончились раунды
            if p1_hp > p2_hp:
                winner = p1
                result = "p1_win"
            elif p2_hp > p1_hp:
                winner = p2
                result = "p2_win"
            else:
                winner = None
                result = "draw"
        
        # Обновление статистики
        if result == "p1_win":
            p1.set_stat("wins", p1.get_stat("wins", 0) + 1)
            p1.set_stat("win_streak", p1.get_stat("win_streak", 0) + 1)
            p1.set_stat("duels_today", p1.get_stat("duels_today", 0) + 1)
            p1.set_stat("wins_today", p1.get_stat("wins_today", 0) + 1)
            if p1.get_stat("win_streak", 0) > p1.get_stat("best_streak", 0):
                p1.set_stat("best_streak", p1.get_stat("win_streak", 0))
            p2.set_stat("losses", p2.get_stat("losses", 0) + 1)
            p2.set_stat("win_streak", 0)
            p2.set_stat("duels_today", p2.get_stat("duels_today", 0) + 1)
            
            if p1_hp < 10:
                p1.set_stat("close_wins", p1.get_stat("close_wins", 0) + 1)
            if p1_hp == p1_max_hp:
                p1.set_stat("perfect_wins", p1.get_stat("perfect_wins", 0) + 1)
            
        elif result == "p2_win":
            p2.set_stat("wins", p2.get_stat("wins", 0) + 1)
            p2.set_stat("win_streak", p2.get_stat("win_streak", 0) + 1)
            p2.set_stat("duels_today", p2.get_stat("duels_today", 0) + 1)
            p2.set_stat("wins_today", p2.get_stat("wins_today", 0) + 1)
            if p2.get_stat("win_streak", 0) > p2.get_stat("best_streak", 0):
                p2.set_stat("best_streak", p2.get_stat("win_streak", 0))
            p1.set_stat("losses", p1.get_stat("losses", 0) + 1)
            p1.set_stat("win_streak", 0)
            p1.set_stat("duels_today", p1.get_stat("duels_today", 0) + 1)
            
            if p2_hp < 10:
                p2.set_stat("close_wins", p2.get_stat("close_wins", 0) + 1)
            if p2_hp == p2_max_hp:
                p2.set_stat("perfect_wins", p2.get_stat("perfect_wins", 0) + 1)
        else:
            p1.set_stat("draws", p1.get_stat("draws", 0) + 1)
            p2.set_stat("draws", p2.get_stat("draws", 0) + 1)
        
        # Обновление урона
        p1.set_stat("total_damage_dealt", p1.get_stat("total_damage_dealt", 0) + (p2_max_hp - p2_hp))
        p2.set_stat("total_damage_dealt", p2.get_stat("total_damage_dealt", 0) + (p1_max_hp - p1_hp))
        p1.set_stat("damage_today", p1.get_stat("damage_today", 0) + (p2_max_hp - p2_hp))
        p2.set_stat("damage_today", p2.get_stat("damage_today", 0) + (p1_max_hp - p1_hp))
        
        # Выплата ставок
        bet = duel.get("bet", 0)
        if bet > 0:
            p1_initial = copy.deepcopy(p1.data)
            p2_initial = copy.deepcopy(p2.data)
            
            p1.add_money(-bet)
            p2.add_money(-bet)
            
            if winner:
                winner.add_money(bet * 2)
        
        # Начисление опыта
        if result == "p1_win":
            p1.add_exp(50 + bet // 10)
            p2.add_exp(25 + bet // 20)
        elif result == "p2_win":
            p2.add_exp(50 + bet // 10)
            p1.add_exp(25 + bet // 20)
        else:
            p1.add_exp(30)
            p2.add_exp(30)
        
        # Проверка достижений
        DuelSystem.check_achievements(p1)
        DuelSystem.check_achievements(p2)
        
        # Удаление дуэли
        del active_duels[duel_id]
        save_json(DATA_FILES['active_duels'], active_duels)
        
        # Сохранение в историю
        history_entry = {
            "duel_id": duel_id,
            "challenger": p1.data["first_name"],
            "opponent": p2.data["first_name"],
            "winner": winner.data["first_name"] if winner else "Ничья",
            "result": result,
            "bet": bet,
            "rounds": round_num,
            "date": datetime.now().isoformat()
        }
        duel_history.append(history_entry)
        save_json(DATA_FILES['duel_history'], duel_history)
        
        return {
            "winner": winner,
            "result": result,
            "p1": p1,
            "p2": p2,
            "rounds": round_num,
            "battle_log": battle_log,
            "p1_hp": p1_hp,
            "p2_hp": p2_hp,
            "p1_max_hp": p1_max_hp,
            "p2_max_hp": p2_max_hp
        }
    
    @staticmethod
    def check_achievements(player):
        """Проверка и выдача достижений"""
        achievements = player.get_stat("achievements", [])
        user_data = player.data
        
        for ach_id, ach_data in ACHIEVEMENTS_LIST.items():
            if ach_id not in achievements:
                condition = ach_data["condition"]
                try:
                    if condition(user_data):
                        achievements.append(ach_id)
                        player.set_stat("achievements", achievements)
                        player.add_money(ach_data["reward"])
                        return ach_data
                except:
                    pass
        
        return None

# ==================== КОМПАКТНОЕ МЕНЮ ====================
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [
        ["⚔ Дуэль", "👤 Профиль", "🎒 Инв"],
        ["🏪 Магазин", "💎 Редкое", "📊 Топ"],
        ["🎮 РП", "📜 Квесты", "🏅 Ачив"],
        ["🛡 Клан", "🎁 Бонус", "💊 Лечить"],
        ["ℹ Помощь", "⚙ Настр", "📈 Стат"]
    ]
    for row in buttons:
        markup.add(*[types.KeyboardButton(b) for b in row])
    return markup

# ==================== ОБРАБОТЧИКИ КОМАНД ====================
@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    player = Player(user_id, 
                    username=message.from_user.username,
                    first_name=message.from_user.first_name)
    
    start_text = f"""
<b>⚔ ДУЭЛЬ БОТ v4.0 ⚔</b>

Добро пожаловать, <b>{message.from_user.first_name}</b>!

🎯 <b>Возможности:</b>
• 7 типов дуэлей с выбором ставок
• Расширенный магазин: 30+ предметов
• Система экипировки (5 слотов)
• Боевые механики: криты, уклонение, вампиризм
• Лимитированные предметы (5 видов)
• Клановая система
• Ежедневные квесты и достижения

💰 Стартовый баланс: <b>500 монет</b>
🎁 Ежедневные награды ждут!

Используй кнопки меню для навигации!
"""
    bot.send_message(message.chat.id, start_text, reply_markup=get_main_menu())

@bot.message_handler(commands=['help'])
def cmd_help(message):
    help_text = """
<b>📚 ПОЛНАЯ СПРАВКА</b>

<b>⚔ ДУЭЛИ:</b>
/duel - вызов на дуэль (ответ на сообщение)
/quickduel - быстрая дуэль против бота
/ranked - рейтинговая дуэль
/hardcore - хардкорная дуэль (высокие ставки)
/friendly - дружеская дуэль без ставок

<b>👤 ПРОФИЛЬ:</b>
/profile - полная статистика
/inventory - управление инвентарём
/equip [id] - экипировать предмет
/stats - боевые характеристики

<b>🏪 МАГАЗИН:</b>
/shop - все товары
/buy [id] - купить предмет
/sell [id] - продать предмет
/limited - лимитированные предметы

<b>💰 ЭКОНОМИКА:</b>
/daily - ежедневный бонус
/explore - исследование (награда)
/give [сумма] - передать монеты

<b>🎮 РП:</b>
/rp - список всех РП команд

<b>🛡 КЛАН:</b>
/clan create [имя] - создать клан (5000💰)
/clan info - информация о клане

<b>📜 ДРУГОЕ:</b>
/quests - ежедневные задания
/achievements - достижения
/top - рейтинги игроков
"""
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(func=lambda m: m.text and "⚔ Дуэль" in m.text)
@bot.message_handler(commands=['duel_menu'])
def menu_duel(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль (бот)", callback_data="dueltype_quick"),
        types.InlineKeyboardButton("👤 Дуэль с игроком", callback_data="dueltype_player"),
        types.InlineKeyboardButton("🏆 Рейтинговая дуэль", callback_data="dueltype_ranked"),
        types.InlineKeyboardButton("💀 Хардкорная дуэль", callback_data="dueltype_hardcore"),
        types.InlineKeyboardButton("🎯 Дружеская дуэль", callback_data="dueltype_friendly"),
        types.InlineKeyboardButton("🔥 Дуэль на выживание", callback_data="dueltype_survival"),
        types.InlineKeyboardButton("⚔ Команда vs Команда", callback_data="dueltype_team")
    )
    
    text = """
<b>⚔ ВЫБЕРИТЕ ТИП ДУЭЛИ</b>

<b>⚡ Быстрая</b> - против бота (ставка: выбор)
<b>👤 С игроком</b> - PvP с выбором ставки
<b>🏆 Рейтинговая</b> - влияет на рейтинг
<b>💀 Хардкорная</b> - мин. ставка 500💰
<b>🎯 Дружеская</b> - без ставок и потерь
<b>🔥 На выживание</b> - до последней капли крови!
<b>⚔ Командная</b> - сражение кланов
"""
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dueltype_"))
def callback_duel_type(call):
    duel_type = call.data.split("_")[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    # Сохраняем тип дуэли в данных пользователя
    player.set_stat("pending_duel_type", duel_type)
    
    if duel_type == "quick":
        # Выбор ставки для быстрой дуэли
        markup = types.InlineKeyboardMarkup(row_width=3)
        bets = [50, 100, 250, 500, 1000, 2500]
        buttons = []
        for bet in bets:
            if player.get_stat("money", 0) >= bet:
                buttons.append(types.InlineKeyboardButton(
                    f"{bet}💰", callback_data=f"quickduelbet_{bet}"))
        markup.add(*buttons)
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="duel_back"))
        
        bot.edit_message_text(
            f"<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n\nВаш баланс: {player.get_stat('money', 0)}💰\nВыберите ставку:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif duel_type == "player":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="duel_back"))
        bot.edit_message_text(
            "<b>👤 ДУЭЛЬ С ИГРОКОМ</b>\n\n"
            "Ответьте на сообщение игрока командой:\n"
            "<code>/duel [ставка]</code>\n\n"
            "Например: <code>/duel 500</code>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif duel_type == "hardcore":
        markup = types.InlineKeyboardMarkup(row_width=2)
        bets = [500, 1000, 2500, 5000, 10000]
        buttons = []
        for bet in bets:
            if player.get_stat("money", 0) >= bet:
                buttons.append(types.InlineKeyboardButton(
                    f"{bet}💰", callback_data=f"hardcoreduelbet_{bet}"))
        markup.add(*buttons)
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="duel_back"))
        
        bot.edit_message_text(
            f"<b>💀 ХАРДКОРНАЯ ДУЭЛЬ</b>\n\n"
            f"Баланс: {player.get_stat('money', 0)}💰\n"
            f"Выберите ставку (мин. 500💰):",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif duel_type == "friendly":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="duel_back"))
        bot.edit_message_text(
            "<b>🎯 ДРУЖЕСКАЯ ДУЭЛЬ</b>\n\n"
            "Без ставок и потерь!\n"
            "Ответьте на сообщение друга: <code>/friendly</code>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif duel_type in ["ranked", "survival", "team"]:
        # Для этих типов просто показываем информацию
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="duel_back"))
        
        texts = {
            "ranked": "🏆 Рейтинговая дуэль\nСтавка: 100💰\nИспользуйте: /ranked",
            "survival": "🔥 Дуэль на выживание\nСтавка: 200💰\nИспользуйте: /survival",
            "team": "⚔ Командная дуэль\nСкоро в обновлении!"
        }
        bot.edit_message_text(
            texts.get(duel_type, "Дуэль"),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("quickduelbet_"))
def callback_quick_duel(call):
    bet = int(call.data.split("_")[1])
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.get_stat("money", 0) < bet:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    # Создаём бота-противника
    player_level = player.get_stat("level", 1)
    bot_level = random.randint(max(1, player_level - 5), player_level + 5)
    
    # Генерируем боту предметы
    bot_weapon = random.choice([k for k, v in SHOP_ITEMS.items() 
                                if v["type"] == "weapon" and v["level_req"] <= bot_level])
    
    bot_user_id = f"bot_{random.randint(10000,99999)}"
    
    # Создаём временного игрока-бота
    users[bot_user_id] = {
        "user_id": bot_user_id,
        "username": f"Bot_{bot_level}",
        "first_name": f"🤖 Бот Lv.{bot_level}",
        "money": 0,
        "level": bot_level,
        "exp": 0,
        "hp": 100 + bot_level * 10,
        "max_hp": 100 + bot_level * 10,
        "wins": 0,
        "losses": 0,
        "inventory": [bot_weapon],
        "equipped": {
            "weapon": bot_weapon,
            "shield": None,
            "armor": None,
            "accessory": None,
            "boots": None
        },
        "settings": {}
    }
    
    # Создаём дуэль
    duel_id = DuelSystem.create_duel(str(user_id), bot_user_id, "quick", bet)
    
    # Снимаем ставку
    player.add_money(-bet)
    
    # Выполняем дуэль
    result = DuelSystem.execute_duel(duel_id)
    
    # Удаляем бота
    if bot_user_id in users:
        del users[bot_user_id]
    save_json(DATA_FILES['users'], users)
    
    if result and result["winner"] and result["winner"].user_id == str(user_id):
        # Победа игрока
        player = Player(user_id)  # Обновляем данные
        result_text = f"""
<b>⚔ ПОБЕДА В ДУЭЛИ!</b>

Противник: <b>🤖 Бот Lv.{bot_level}</b>
Ставка: <b>{bet}💰</b>
Раундов: <b>{result['rounds']}</b>

💰 Выигрыш: <b>+{bet * 2}💰</b>
✨ Опыт: <b>+{50 + bet // 10}</b>

⚜ Текущая серия побед: <b>{player.get_stat('win_streak', 0)}</b>
"""
    else:
        player = Player(user_id)
        result_text = f"""
<b>💀 ПОРАЖЕНИЕ</b>

Противник: <b>🤖 Бот Lv.{bot_level}</b>
Ставка: <b>{bet}💰</b>
Раундов: <b>{result['rounds'] if result else '?'}</b>

Потеряно: <b>{bet}💰</b>
✨ Утешительный опыт: <b>+{25 + bet // 20}</b>
"""
    
    bot.edit_message_text(result_text, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("hardcoreduelbet_"))
def callback_hardcore_duel(call):
    bet = int(call.data.split("_")[1])
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.get_stat("money", 0) < bet:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    player.set_stat("pending_duel_bet", bet)
    
    bot.edit_message_text(
        f"<b>💀 ХАРДКОРНАЯ ДУЭЛЬ</b>\n\n"
        f"Ставка: <b>{bet}💰</b>\n"
        f"Ответьте на сообщение противника: <code>/hardcore {bet}</code>",
        call.message.chat.id,
        call.message.message_id
    )

@bot.callback_query_handler(func=lambda call: call.data == "duel_back")
def callback_duel_back(call):
    # Возврат в главное меню дуэлей
    menu_duel(call.message)

@bot.message_handler(commands=['duel', 'ranked', 'hardcore', 'friendly', 'survival'])
def cmd_duel_types(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Ответьте на сообщение игрока, которого вызываете!")
        return
    
    command = message.text.split()[0].replace('/', '')
    user_id = message.from_user.id
    opponent_id = message.reply_to_message.from_user.id
    
    if user_id == opponent_id:
        bot.send_message(message.chat.id, "❌ Нельзя драться с самим собой!")
        return
    
    player = Player(user_id)
    opponent = Player(opponent_id)
    
    # Определяем ставку
    if command == "duel":
        try:
            parts = message.text.split()
            bet = int(parts[1]) if len(parts) > 1 else 50
        except:
            bet = 50
        duel_type = "player"
    elif command == "ranked":
        bet = 100
        duel_type = "ranked"
    elif command == "hardcore":
        try:
            parts = message.text.split()
            bet = int(parts[1]) if len(parts) > 1 else 500
        except:
            bet = 500
        duel_type = "hardcore"
    elif command == "friendly":
        bet = 0
        duel_type = "friendly"
    elif command == "survival":
        bet = 200
        duel_type = "survival"
    
    # Проверка баланса
    if bet > 0:
        if player.get_stat("money", 0) < bet:
            bot.send_message(message.chat.id, f"❌ Недостаточно монет! Нужно {bet}💰")
            return
        if opponent.get_stat("money", 0) < bet:
            bot.send_message(message.chat.id, f"❌ У противника недостаточно монет! Нужно {bet}💰")
            return
    
    # Подтверждение дуэли
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Принять", 
            callback_data=f"acceptduel_{user_id}_{duel_type}_{bet}"),
        types.InlineKeyboardButton("❌ Отклонить", 
            callback_data=f"declineduel_{user_id}")
    )
    
    duel_text = f"""
<b>⚔ ВЫЗОВ НА ДУЭЛЬ!</b>

<b>{message.from_user.first_name}</b> вызывает <b>{message.reply_to_message.from_user.first_name}</b>!

Тип: <b>{duel_type.upper()}</b>
Ставка: <b>{bet}💰</b>

Противник должен принять вызов!
"""
    bot.send_message(message.chat.id, duel_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("acceptduel_"))
def callback_accept_duel(call):
    parts = call.data.split("_")
    challenger_id = parts[1]
    duel_type = parts[2]
    bet = int(parts[3])
    acceptor_id = call.from_user.id
    
    if str(acceptor_id) == challenger_id:
        bot.answer_callback_query(call.id, "❌ Вы не можете принять свой вызов!")
        return
    
    # Проверяем баланс ещё раз
    acceptor = Player(acceptor_id)
    if bet > 0 and acceptor.get_stat("money", 0) < bet:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    # Создаём и выполняем дуэль
    duel_id = DuelSystem.create_duel(challenger_id, acceptor_id, duel_type, bet)
    result = DuelSystem.execute_duel(duel_id)
    
    if result:
        if result["result"] == "p1_win":
            winner = result["p1"]
            loser = result["p2"]
        elif result["result"] == "p2_win":
            winner = result["p2"]
            loser = result["p1"]
        else:
            winner = None
            loser = None
        
        if winner:
            win_name = winner.get_stat( "first_name", "Игрок")
            lose_name = loser.get_stat("first_name", "Игрок")
            result_text = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

🏆 Победитель: <b>{win_name}</b>
💀 Проигравший: <b>{lose_name}</b>

Ставка: <b>{bet}💰</b>
Раундов: <b>{result['rounds']}</b>

💰 Приз победителю: <b>{bet * 2}💰</b>
"""
        else:
            result_text = f"""
<b>🤝 НИЧЬЯ!</b>

Раундов: <b>{result['rounds']}</b>
Ставки возвращены игрокам.

Редкий случай! Оба воина равны по силе.
"""
        
        # Добавляем лог битвы
        if result.get("battle_log"):
            log_text = "\n".join(result["battle_log"][-10:])  # Последние 10 событий
            if len(result["battle_log"]) > 10:
                log_text = f"...\n{log_text}"
            result_text += f"\n\n<b>📜 Лог битвы:</b>\n{log_text}"
    
    bot.edit_message_text(result_text, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("declineduel_"))
def callback_decline_duel(call):
    bot.edit_message_text("❌ Вызов отклонён!", call.message.chat.id, call.message.message_id)

# ==================== ПРОФИЛЬ ====================
@bot.message_handler(func=lambda m: m.text and "👤 Профиль" in m.text)
@bot.message_handler(commands=['profile'])
def cmd_profile(message):
    user_id = message.from_user.id
    player = Player(user_id)
    stats = player.calculate_stats()
    data = player.data
    
    winrate = 0
    total_duels = data.get("wins", 0) + data.get("losses", 0)
    if total_duels > 0:
        winrate = (data.get("wins", 0) / total_duels) * 100
    
    equipped_list = []
    for slot, item_id in data.get("equipped", {}).items():
        if item_id:
            item = SHOP_ITEMS.get(item_id) or limited_items_data.get(item_id)
            if item:
                equipped_list.append(f"{item.get('emoji', '')} {item['name']}")
    
    profile_text = f"""
<b>👤 ПРОФИЛЬ ИГРОКА</b>

<b>{data.get('first_name', 'Игрок')}</b>
🏅 Титул: <b>{data.get('title', 'Новичок')}</b>
⭐ Уровень: <b>{data.get('level', 1)}</b>
✨ Опыт: {data.get('exp', 0)}/{int(100 * (1.5 ** (data.get('level', 1) - 1)))}

❤ Здоровье: {stats['hp']}/{stats['max_hp']}
⚔ Урон: <b>{stats['damage']}</b>
🛡 Защита: <b>{stats['defense']}</b>
💥 Крит: <b>{stats['crit_chance']}%</b>
🌀 Уклонение: <b>{stats['dodge_chance']}%</b>

<b>📊 Статистика дуэлей:</b>
🏆 Побед: {data.get('wins', 0)}
💀 Поражений: {data.get('losses', 0)}
🤝 Ничьих: {data.get('draws', 0)}
📊 Винрейт: {winrate:.1f}%
🔥 Лучшая серия: {data.get('best_streak', 0)}
💥 Крит. ударов: {data.get('critical_hits', 0)}

💰 Баланс: <b>{data.get('money', 0)} монет</b>
🎒 Предметов: {len(data.get('inventory', []))}
🏅 Достижений: {len(data.get('achievements', []))}/{len(ACHIEVEMENTS_LIST)}
🛡 Клан: {data.get('clan') or 'Нет'}

<b>🎯 Экипировка:</b>
{chr(10).join(equipped_list) if equipped_list else 'Нет экипировки'}
"""
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Характеристики", callback_data="show_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory_menu"),
        types.InlineKeyboardButton("🏅 Достижения", callback_data="show_achievements"),
        types.InlineKeyboardButton("📈 История дуэлей", callback_data="duel_history")
    )
    
    bot.send_message(message.chat.id, profile_text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text and "🎒 Инв" in m.text)
def menu_inventory(message):
    show_inventory(message.chat.id, message.from_user.id)

def show_inventory(chat_id, user_id):
    player = Player(user_id)
    inventory = player.get_stat("inventory", [])
    
    if not inventory:
        bot.send_message(chat_id, "🎒 Ваш инвентарь пуст!")
        return
    
    # Группируем предметы
    item_counts = {}
    for item_id in inventory:
        item_counts[item_id] = item_counts.get(item_id, 0) + 1
    
    inv_text = "<b>🎒 ИНВЕНТАРЬ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for i, (item_id, count) in enumerate(item_counts.items(), 1):
        item = SHOP_ITEMS.get(item_id) or limited_items_data.get(item_id)
        if item:
            rarity_emoji = {
                "common": "⬜", "uncommon": "🟩", "rare": "🟦",
                "epic": "🟪", "legendary": "🟧", "mythic": "🟥",
                "divine": "💛", "apocalyptic": "🖤"
            }.get(item.get("rarity", "common"), "⬜")
            
            inv_text += f"{i}. {rarity_emoji} {item['emoji']} {item['name']} x{count}\n"
            
            # Кнопки действий
            if item["type"] in ["weapon", "shield", "armor", "accessory", "boots"]:
                markup.add(types.InlineKeyboardButton(
                    f"Экипировать {item['name'][:15]}",
                    callback_data=f"equipitem_{item_id}"
                ))
            elif item["type"] == "potion":
                markup.add(types.InlineKeyboardButton(
                    f"Использовать {item['name'][:15]}",
                    callback_data=f"useitem_{item_id}"
                ))
    
    if len(inv_text) > 4000:
        for x in range(0, len(inv_text), 4000):
            bot.send_message(chat_id, inv_text[x:x+4000])
        bot.send_message(chat_id, "Действия:", reply_markup=markup)
    else:
        bot.send_message(chat_id, inv_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("equipitem_"))
def callback_equip_item(call):
    item_id = call.data.split("_", 1)[1]
    player = Player(call.from_user.id)
    
    success, message = player.equip_item(item_id)
    bot.answer_callback_query(call.id, message)
    
    if success:
        # Обновляем сообщение
        show_inventory(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("useitem_"))
def callback_use_item(call):
    item_id = call.data.split("_", 1)[1]
    player = Player(call.from_user.id)
    
    success, message = player.use_potion(item_id)
    bot.answer_callback_query(call.id, message)
    
    if success:
        bot.answer_callback_query(call.id, message)

# ==================== МАГАЗИН ====================
@bot.message_handler(func=lambda m: m.text and "🏪 Магазин" in m.text)
@bot.message_handler(commands=['shop'])
def cmd_shop(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Категории
    categories = [
        ("⚔ Оружие", "cat_weapon"),
        ("🛡 Щиты", "cat_shield"),
        ("🧥 Броня", "cat_armor"),
        ("📿 Аксессуары", "cat_accessory"),
        ("👢 Обувь", "cat_boots"),
        ("🧪 Зелья", "cat_potion")
    ]
    
    for name, callback in categories:
        markup.add(types.InlineKeyboardButton(name, callback_data=callback))
    
    markup.add(types.InlineKeyboardButton("💎 Лимитированные", callback_data="shop_limited"))
    markup.add(types.InlineKeyboardButton("💰 Продать предмет", callback_data="shop_sell"))
    
    shop_text = f"""
<b>🏪 МАГАЗИН СНАРЯЖЕНИЯ</b>

💰 Ваш баланс: <b>{Player(message.from_user.id).get_stat('money', 0)} монет</b>

Выберите категорию товаров:
• ⚔ Оружие - увеличивает урон
• 🛡 Щиты - защита и отражение
• 🧥 Броня - здоровье и защита
• 📿 Аксессуары - особые эффекты
• 👢 Обувь - скорость и уклонение
• 🧪 Зелья - восстановление HP
"""
    bot.send_message(message.chat.id, shop_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def callback_shop_category(call):
    category = call.data.split("_")[1]
    player = Player(call.from_user.id)
    player_level = player.get_stat("level", 1)
    player_money = player.get_stat("money", 0)
    
    # Фильтруем предметы по категории
    category_items = {k: v for k, v in SHOP_ITEMS.items() if v["type"] == category}
    
    shop_text = f"<b>🏪 {category.upper()}</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_id, item in sorted(category_items.items(), key=lambda x: x[1]["price"]):
        req_level = item.get("level_req", 1)
        can_buy = player_money >= item["price"] and player_level >= req_level
        
        rarity_symbol = {
            "common": "⬜", "uncommon": "🟩", "rare": "🟦",
            "epic": "🟪", "legendary": "🟧", "mythic": "🟥"
        }.get(item.get("rarity", "common"), "⬜")
        
        shop_text += f"{rarity_symbol} {item['emoji']} <b>{item['name']}</b>\n"
        shop_text += f"💰 Цена: {item['price']} | ⭐ Ур: {req_level}\n"
        
        if "damage" in item:
            shop_text += f"⚔ Урон: +{item['damage']}\n"
        if "defense" in item:
            shop_text += f"🛡 Защита: +{item['defense']}\n"
        if "hp_bonus" in item:
            shop_text += f"❤ HP: +{item['hp_bonus']}\n"
        if "heal" in item:
            shop_text += f"💚 Лечение: {item['heal']} HP\n"
        
        shop_text += f"📝 {item.get('description', '')}\n\n"
        
        if can_buy:
            markup.add(types.InlineKeyboardButton(
                f"Купить {item['name']} - {item['price']}💰",
                callback_data=f"buyitem_{item_id}"
            ))
    
    markup.add(types.InlineKeyboardButton("🔙 Назад в магазин", callback_data="shop_back"))
    
    try:
        bot.edit_message_text(shop_text[:4000], call.message.chat.id, 
                             call.message.message_id, reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, shop_text[:4000], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buyitem_"))
def callback_buy_item(call):
    item_id = call.data.split("_", 1)[1]
    item = SHOP_ITEMS.get(item_id)
    
    if not item:
        bot.answer_callback_query(call.id, "❌ Предмет не найден!")
        return
    
    player = Player(call.from_user.id)
    
    if player.get_stat("level", 1) < item.get("level_req", 1):
        bot.answer_callback_query(call.id, f"❌ Нужен {item.get('level_req', 1)} уровень!")
        return
    
    if player.get_stat("money", 0) < item["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    player.add_money(-item["price"])
    player.add_item(item_id)
    player.set_stat("purchases_today", player.get_stat("purchases_today", 0) + 1)
    
    bot.answer_callback_query(call.id, f"✅ Куплено: {item['name']}!")
    bot.send_message(call.message.chat.id, 
        f"✅ Вы приобрели {item['emoji']} <b>{item['name']}</b> за {item['price']}💰!")

@bot.callback_query_handler(func=lambda call: call.data == "shop_limited")
def callback_shop_limited(call):
    player = Player(call.from_user.id)
    player_money = player.get_stat("money", 0)
    
    limit_text = "<b>💎 ЛИМИТИРОВАННЫЕ ПРЕДМЕТЫ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    has_items = False
    for item_id, item in limited_items_data.items():
        if item.get("remaining", 0) > 0:
            has_items = True
            progress = int(item["remaining"] / item["total"] * 10)
            bar = "█" * progress + "░" * (10 - progress)
            
            limit_text += f"{item['emoji']} <b>{item['name']}</b>\n"
            limit_text += f"📦 [{bar}] {item['remaining']}/{item['total']}\n"
            limit_text += f"💰 Цена: <b>{item['price']} монет</b>\n"
            limit_text += f"⭐ Требуемый уровень: {item.get('level_req', 1)}\n"
            limit_text += f"📝 {item.get('description', '')}\n"
            
            if item.get("special"):
                limit_text += f"✨ <b>Особое свойство:</b> {item['special']}\n"
            
            limit_text += "\n"
            
            if player_money >= item["price"]:
                markup.add(types.InlineKeyboardButton(
                    f"Купить {item['name']} - {item['price']}💰",
                    callback_data=f"buylimited_{item_id}"
                ))
    
    if not has_items:
        limit_text += "😔 Все лимитированные предметы распроданы!"
    
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="shop_back"))
    
    try:
        bot.edit_message_text(limit_text, call.message.chat.id, 
                             call.message.message_id, reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, limit_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buylimited_"))
def callback_buy_limited(call):
    item_id = call.data.split("_", 1)[1]
    item = limited_items_data.get(item_id)
    
    if not item or item.get("remaining", 0) <= 0:
        bot.answer_callback_query(call.id, "❌ Предмета нет в наличии!")
        return
    
    player = Player(call.from_user.id)
    
    if player.get_stat("level", 1) < item.get("level_req", 1):
        bot.answer_callback_query(call.id, f"❌ Нужен {item.get('level_req', 1)} уровень!")
        return
    
    if player.get_stat("money", 0) < item["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    player.add_money(-item["price"])
    player.add_item(item_id)
    item["remaining"] -= 1
    save_json(DATA_FILES['limited_items'], limited_items_data)
    
    bot.answer_callback_query(call.id, f"💎 Куплено: {item['name']}!")
    bot.send_message(call.message.chat.id,
        f"💎 <b>ЛЕГЕНДАРНАЯ ПОКУПКА!</b>\n\n"
        f"Вы приобрели {item['emoji']} <b>{item['name']}</b>!\n"
        f"Осталось в продаже: {item['remaining']}/{item['total']}\n"
        f"💰 Потрачено: {item['price']} монет")

@bot.callback_query_handler(func=lambda call: call.data == "shop_back")
def callback_shop_back(call):
    cmd_shop(call.message)

# ==================== ЕЖЕДНЕВНЫЙ БОНУС И ИССЛЕДОВАНИЕ ====================
@bot.message_handler(func=lambda m: m.text and "🎁 Бонус" in m.text)
@bot.message_handler(commands=['daily'])
def cmd_daily(message):
    user_id = message.from_user.id
    player = Player(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if player.get_stat("last_daily") == today:
        bot.send_message(message.chat.id, "🎁 Вы уже получили сегодняшний бонус!\nПриходите завтра в 00:00 по МСК.")
        return
    
    # Рассчитываем бонус в зависимости от уровня
    level = player.get_stat("level", 1)
    money_bonus = random.randint(100, 500) + level * 10
    exp_bonus = random.randint(30, 100) + level * 5
    
    # Шанс на предмет
    got_item = None
    if random.random() < 0.15:  # 15% шанс
        common_items = [k for k, v in SHOP_ITEMS.items() if v.get("rarity") == "common"]
        if common_items:
            got_item = random.choice(common_items)
            player.add_item(got_item)
    
    player.add_money(money_bonus)
    player.add_exp(exp_bonus)
    player.set_stat("last_daily", today)
    
    level_up = player.check_level_up()
    
    result_text = f"""
<b>🎁 ЕЖЕДНЕВНЫЙ БОНУС</b>

💰 Монет: <b>+{money_bonus}</b>
✨ Опыта: <b>+{exp_bonus}</b>
"""
    if got_item:
        item = SHOP_ITEMS[got_item]
        result_text += f"\n🎒 Предмет: {item['emoji']} <b>{item['name']}</b>"
    
    if level_up:
        result_text += f"\n\n🎉 <b>НОВЫЙ УРОВЕНЬ: {player.get_stat('level', 1)}!</b>"
    
    bot.send_message(message.chat.id, result_text)

@bot.message_handler(commands=['explore'])
def cmd_explore(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    player.set_stat("explore_today", player.get_stat("explore_today", 0) + 1)
    
    # Случайное событие
    events = [
        {
            "text": "исследовали древние руины и нашли сокровище! 🏛",
            "money": random.randint(50, 200),
            "exp": random.randint(10, 30),
            "chance": 40
        },
        {
            "text": "встретили торговца и заключили выгодную сделку! 🤝",
            "money": random.randint(100, 300),
            "exp": random.randint(15, 40),
            "chance": 25
        },
        {
            "text": "победили дикого монстра! 🐗",
            "money": random.randint(30, 150),
            "exp": random.randint(20, 50),
            "chance": 20
        },
        {
            "text": "нашли редкий артефакт! 💎",
            "money": random.randint(200, 500),
            "exp": random.randint(25, 60),
            "chance": 10
        },
        {
            "text": "попали в ловушку и потеряли немного монет... 😢",
            "money": random.randint(-100, -30),
            "exp": random.randint(5, 15),
            "chance": 5
        }
    ]
    
    # Выбираем событие на основе шансов
    total_chance = sum(e["chance"] for e in events)
    roll = random.randint(1, total_chance)
    
    cumulative = 0
    chosen_event = events[0]
    for event in events:
        cumulative += event["chance"]
        if roll <= cumulative:
            chosen_event = event
            break
    
    player.add_money(chosen_event["money"])
    player.add_exp(chosen_event["exp"])
    
    level_up = player.check_level_up()
    
    result_text = f"""
<b>🔍 ИССЛЕДОВАНИЕ</b>

Вы {chosen_event['text']}

💰 Монет: <b>{chosen_event['money']:+d}</b>
✨ Опыта: <b>+{chosen_event['exp']}</b>
"""
    
    if level_up:
        result_text += f"\n🎉 <b>НОВЫЙ УРОВЕНЬ: {player.get_stat('level', 1)}!</b>"
    
    bot.send_message(message.chat.id, result_text)

# ==================== КВЕСТЫ И ДОСТИЖЕНИЯ ====================
@bot.message_handler(func=lambda m: m.text and "📜 Квесты" in m.text)
@bot.message_handler(commands=['quests'])
def cmd_quests(message):
    user_id = message.from_user.id
    player = Player(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Инициализация квестов на сегодня
    if player.get_stat("quests_date") != today:
        # Выбираем 3 случайных квеста
        daily_quests = random.sample(DAILY_QUESTS_POOL, min(3, len(DAILY_QUESTS_POOL)))
        quests_dict = {}
        for i, quest in enumerate(daily_quests):
            quest_copy = quest.copy()
            quest_copy["id"] = f"{today}_{i}"
            quest_copy["progress"] = 0
            quest_copy["completed"] = False
            quests_dict[quest_copy["id"]] = quest_copy
        
        player.set_stat("active_quests", quests_dict)
        player.set_stat("quests_date", today)
    
    quests = player.get_stat("active_quests", {})
    
    quests_text = f"<b>📜 ЕЖЕДНЕВНЫЕ КВЕСТЫ</b> ({today})\n\n"
    
    for quest_id, quest in quests.items():
        progress = quest.get("progress", 0)
        target = quest["target"]
        completed = quest.get("completed", False)
        
        if completed:
            status = "✅"
            bar = "█" * 10
        else:
            status = "🔄"
            filled = int(progress / target * 10) if target > 0 else 0
            bar = "█" * filled + "░" * (10 - filled)
        
        quests_text += f"{status} <b>{quest['name']}</b>\n"
        quests_text += f"📊 [{bar}] {progress}/{target}\n"
        quests_text += f"📝 {quest['desc']}\n"
        quests_text += f"🎁 Награда: {quest['reward_money']}💰 + {quest['reward_exp']} EXP\n\n"
        
        # Кнопка получения награды
        if progress >= target and not completed:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"🎁 Забрать награду за '{quest['name']}'",
                callback_data=f"completequest_{quest_id}"
            ))
            bot.send_message(message.chat.id, quests_text, reply_markup=markup)
            return
    
    bot.send_message(message.chat.id, quests_text)

@bot.callback_query_handler(func=lambda call: call.data.startswith("completequest_"))
def callback_complete_quest(call):
    quest_id = call.data.split("_", 1)[1]
    player = Player(call.from_user.id)
    
    quests = player.get_stat("active_quests", {})
    if quest_id in quests and not quests[quest_id].get("completed", False):
        quest = quests[quiz_id]
        if quest.get("progress", 0) >= quest.get("target", 1):
            player.add_money(quest["reward_money"])
            player.add_exp(quest["reward_exp"])
            quest["completed"] = True
            quests[quest_id] = quest
            player.set_stat("active_quests", quests)
            player.set_stat("completed_quests", player.get_stat("completed_quests", 0) + 1)
            
            bot.answer_callback_query(call.id, "✅ Квест выполнен! Награда получена!")
            cmd_quests(call.message)
    
    bot.answer_callback_query(call.id, "❌ Квест ещё не выполнен!")

@bot.message_handler(func=lambda m: m.text and "🏅 Ачив" in m.text)
@bot.message_handler(commands=['achievements'])
def cmd_achievements(message):
    user_id = message.from_user.id
    player = Player(user_id)
    user_achievements = player.get_stat("achievements", [])
    
    ach_text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(user_achievements)}/{len(ACHIEVEMENTS_LIST)})\n\n"
    
    for ach_id, ach_data in ACHIEVEMENTS_LIST.items():
        if ach_id in user_achievements:
            ach_text += f"✅ {ach_data['name']} - {ach_data['desc']}\n"
        else:
            ach_text += f"🔒 {ach_data['name']} - {ach_data['desc']}\n"
    
    if len(ach_text) > 4000:
        for x in range(0, len(ach_text), 4000):
            bot.send_message(message.chat.id, ach_text[x:x+4000])
    else:
        bot.send_message(message.chat.id, ach_text)

# ==================== РП КОМАНДЫ ====================
@bot.message_handler(func=lambda m: m.text and "🎮 РП" in m.text)
@bot.message_handler(commands=['rp'])
def cmd_rp(message):
    rp_text = """
<b>🎮 РОЛЕВЫЕ КОМАНДЫ</b>

<b>Приветствия:</b>
/hi, /hello, /hey - поздороваться
/bye - попрощаться

<b>Эмоции:</b>
/happy - радоваться
/sad - грустить
/angry - злиться
/laugh - смеяться
/cry - плакать

<b>Действия:</b>
/dance - танцевать
/sing - петь
/think - задуматься
/eat - поесть
/drink - попить
/sleep - спать
/read - читать

<b>Боевые:</b>
/attack - атаковать (ответ на сообщение)
/defend - защищаться
/meditate - медитировать (+EXP)

<b>Другое:</b>
/hug - обнять
/punch - ударить (шутка)
/flip - подбросить монетку
/roll - бросить кубик
"""
    bot.send_message(message.chat.id, rp_text)

@bot.message_handler(commands=['hi', 'hello', 'hey'])
def rp_hi(message):
    greetings = [
        f"👋 {message.from_user.first_name} приветствует всех!",
        f"🤗 {message.from_user.first_name} машет рукой!",
        f"🌟 {message.from_user.first_name} желает всем отличного дня!"
    ]
    bot.send_message(message.chat.id, random.choice(greetings))

@bot.message_handler(commands=['bye'])
def rp_bye(message):
    bot.send_message(message.chat.id, f"👋 {message.from_user.first_name} прощается со всеми!")

@bot.message_handler(commands=['dance'])
def rp_dance(message):
    dances = ["💃 зажигательный танец", "🕺 брейк-данс", "💃🕺 вальс", "🔥 энергичный танец"]
    bot.send_message(message.chat.id, f"{message.from_user.first_name} исполняет {random.choice(dances)}!")

@bot.message_handler(commands=['hug'])
def rp_hug(message):
    if message.reply_to_message:
        target = message.reply_to_message.from_user.first_name
        bot.send_message(message.chat.id, f"🤗 {message.from_user.first_name} крепко обнимает {target}!")
    else:
        bot.send_message(message.chat.id, f"🤗 {message.from_user.first_name} обнимает всех!")

@bot.message_handler(commands=['attack'])
def rp_attack(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, f"{message.from_user.first_name} атакует воздух! 💨")
        return
    
    target = message.reply_to_message.from_user.first_name
    attacks = ["мощный удар", "молниеносную атаку", "сокрушительный удар", "серию ударов"]
    bot.send_message(message.chat.id, 
        f"⚔ {message.from_user.first_name} наносит {random.choice(attacks)} по {target}!")

@bot.message_handler(commands=['meditate'])
def rp_meditate(message):
    player = Player(message.from_user.id)
    exp = random.randint(5, 25)
    player.add_exp(exp)
    level_up = player.check_level_up()
    
    result = f"🧘 {message.from_user.first_name} медитирует и получает {exp} опыта!"
    if level_up:
        result += f"\n🎉 Уровень повышен до {player.get_stat('level', 1)}!"
    
    bot.send_message(message.chat.id, result)

@bot.message_handler(commands=['flip'])
def rp_flip(message):
    result = random.choice(["Орёл 🦅", "Решка 👑"])
    bot.send_message(message.chat.id, f"🪙 {message.from_user.first_name} подбрасывает монетку... {result}!")

@bot.message_handler(commands=['roll'])
def rp_roll(message):
    result = random.randint(1, 6)
    dice = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    bot.send_message(message.chat.id, f"🎲 {message.from_user.first_name} бросает кубик: {dice[result-1]} ({result})")

# ==================== КЛАНЫ ====================
@bot.message_handler(func=lambda m: m.text and "🛡 Клан" in m.text)
@bot.message_handler(commands=['clan'])
def cmd_clan(message):
    user_id = message.from_user.id
    player = Player(user_id)
    clan_name = player.get_stat("clan")
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if clan_name and clan_name in clans:
        clan = clans[clan_name]
        clan_text = f"""
<b>🛡 КЛАН: {clan_name}</b>

👑 Лидер: {clan.get('leader_name', 'Неизвестно')}
👥 Участников: {len(clan.get('members', []))}
💰 Казна: {clan.get('treasury', 0)} монет
⚔ Побед: {clan.get('wins', 0)}

<b>Состав:</b>
{chr(10).join(f'• {m}' for m in clan.get('members', [])[:15])}
"""
        markup.add(
            types.InlineKeyboardButton("ℹ Информация", callback_data="clan_info"),
            types.InlineKeyboardButton("💰 Пополнить казну", callback_data="clan_donate"),
            types.InlineKeyboardButton("🚪 Покинуть клан", callback_data="clan_leave")
        )
    else:
        clan_text = """
<b>🛡 КЛАНЫ</b>

Вы не состоите в клане!

Создайте свой клан за 5000💰:
<code>/clan create [название]</code>

Или вступите в существующий:
<code>/clan join [название]</code>
"""
        markup.add(
            types.InlineKeyboardButton("🛡 Создать клан", callback_data="clan_create"),
            types.InlineKeyboardButton("📋 Список кланов", callback_data="clan_list")
        )
    
    bot.send_message(message.chat.id, clan_text, reply_markup=markup)

@bot.message_handler(commands=['create_clan'])
def cmd_create_clan(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    if player.get_stat("clan"):
        bot.send_message(message.chat.id, "❌ Вы уже в клане! Сначала покиньте текущий клан.")
        return
    
    if player.get_stat("money", 0) < 5000:
        bot.send_message(message.chat.id, "❌ Недостаточно монет! Нужно 5000💰")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ Укажите название: /create_clan [название]")
        return
    
    clan_name = parts[1].strip()[:20]
    
    if clan_name in clans:
        bot.send_message(message.chat.id, "❌ Такой клан уже существует!")
        return
    
    player.add_money(-5000)
    player.set_stat("clan", clan_name)
    
    clans[clan_name] = {
        "leader_id": user_id,
        "leader_name": message.from_user.first_name,
        "members": [message.from_user.first_name],
        "treasury": 0,
        "wins": 0,
        "created_at": datetime.now().isoformat()
    }
    save_json(DATA_FILES['clans'], clans)
    
    bot.send_message(message.chat.id, 
        f"🛡 <b>Клан '{clan_name}' создан!</b>\n"
        f"Лидер: {message.from_user.first_name}\n"
        f"Приглашайте игроков: /clan invite [имя]")

# ==================== ТОПЫ ====================
@bot.message_handler(func=lambda m: m.text and "📊 Топ" in m.text)
@bot.message_handler(commands=['top'])
def cmd_top(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🏆 По уровню", callback_data="top_level"),
        types.InlineKeyboardButton("⚔ По победам", callback_data="top_wins"),
        types.InlineKeyboardButton("💰 По монетам", callback_data="top_money"),
        types.InlineKeyboardButton("🔥 По серии побед", callback_data="top_streak"),
        types.InlineKeyboardButton("🏅 По достижениям", callback_data="top_achievements")
    )
    
    bot.send_message(message.chat.id, "<b>📊 ТОП ИГРОКОВ</b>\nВыберите категорию:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def callback_top(call):
    category = call.data.split("_")[1]
    
    # Фильтруем ботов
    real_users = {k: v for k, v in users.items() if not k.startswith("bot_")}
    
    if category == "level":
        sorted_users = sorted(real_users.items(), 
                            key=lambda x: (x[1].get("level", 1), x[1].get("exp", 0)), 
                            reverse=True)[:10]
        title = "🏆 ТОП ПО УРОВНЮ"
        value_func = lambda d: f"Ур.{d.get('level', 1)}"
    elif category == "wins":
        sorted_users = sorted(real_users.items(), 
                            key=lambda x: x[1].get("wins", 0), 
                            reverse=True)[:10]
        title = "⚔ ТОП ПО ПОБЕДАМ"
        value_func = lambda d: f"{d.get('wins', 0)} побед"
    elif category == "money":
        sorted_users = sorted(real_users.items(), 
                            key=lambda x: x[1].get("money", 0), 
                            reverse=True)[:10]
        title = "💰 ТОП БОГАЧЕЙ"
        value_func = lambda d: f"{d.get('money', 0)}💰"
    elif category == "streak":
        sorted_users = sorted(real_users.items(), 
                            key=lambda x: x[1].get("best_streak", 0), 
                            reverse=True)[:10]
        title = "🔥 ТОП ПО СЕРИИ ПОБЕД"
        value_func = lambda d: f"Серия: {d.get('best_streak', 0)}"
    elif category == "achievements":
        sorted_users = sorted(real_users.items(), 
                            key=lambda x: len(x[1].get("achievements", [])), 
                            reverse=True)[:10]
        title = "🏅 ТОП ПО ДОСТИЖЕНИЯМ"
        value_func = lambda d: f"{len(d.get('achievements', []))} ачивок"
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    top_text = f"<b>{title}</b>\n\n"
    
    for i, (uid, data) in enumerate(sorted_users):
        name = data.get("first_name", data.get("username", "Игрок"))
        top_text += f"{medals[i]} <b>{name}</b>: {value_func(data)}\n"
    
    try:
        bot.edit_message_text(top_text, call.message.chat.id, call.message.message_id)
    except:
        bot.send_message(call.message.chat.id, top_text)

# ==================== АДМИН-ПАНЕЛЬ ====================
@bot.message_handler(commands=['admin'])
def cmd_admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("💰 Выдать монеты", callback_data="admin_give_money"),
        types.InlineKeyboardButton("🎁 Выдать предмет", callback_data="admin_give_item"),
        types.InlineKeyboardButton("👤 Инфо игрока", callback_data="admin_user_info"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🔄 Сброс дня", callback_data="admin_reset"),
        types.InlineKeyboardButton("💎 Упр. лимит.", callback_data="admin_manage_limited"),
        types.InlineKeyboardButton("❌ Удалить данные", callback_data="admin_delete")
    )
    
    admin_text = """
<b>🔧 АДМИН-ПАНЕЛЬ</b>

Выберите действие для управления ботом:
"""
    bot.send_message(message.chat.id, admin_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def callback_admin(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Доступ запрещён!")
        return
    
    action = call.data.split("_")[1]
    
    if action == "stats":
        total_users = len([u for u in users if not u.startswith("bot_")])
        total_money = sum(u.get("money", 0) for u in users.values() if not u.get("user_id", "").startswith("bot_"))
        total_duels = sum(u.get("wins", 0) + u.get("losses", 0) for u in users.values())
        
        stats_text = f"""
<b>📊 СТАТИСТИКА БОТА</b>

👥 Игроков: {total_users}
💰 Монет в игре: {total_money}
⚔ Всего дуэлей: {total_duels}
🛡 Кланов: {len(clans)}
💎 Лимит. предметов: {sum(v.get('remaining', 0) for v in limited_items_data.values())}
📦 Предметов в магазине: {len(SHOP_ITEMS)}
📜 Достижений: {len(ACHIEVEMENTS_LIST)}

Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id)
    
    elif action == "give_money":
        bot.send_message(call.message.chat.id, 
            "💰 <b>Выдача монет</b>\n\n"
            "Используйте команду:\n"
            "<code>/give_money [ID] [сумма]</code>")
    
    elif action == "broadcast":
        bot.send_message(call.message.chat.id,
            "📢 <b>Рассылка</b>\n\n"
            "Используйте команду:\n"
            "<code>/broadcast [текст]</code>")

@bot.message_handler(commands=['give_money'])
def cmd_give_money(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        amount = int(parts[2])
        
        player = Player(target_id)
        player.add_money(amount)
        
        bot.send_message(message.chat.id, 
            f"✅ Игроку {target_id} выдано {amount}💰\n"
            f"Новый баланс: {player.get_stat('money', 0)}💰")
    except:
        bot.send_message(message.chat.id, "❌ Формат: /give_money [ID] [сумма]")

@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text.replace('/broadcast', '', 1).strip()
    if not text:
        bot.send_message(message.chat.id, "❌ Введите текст рассылки!")
        return
    
    sent = 0
    failed = 0
    for user_id in users:
        if not user_id.startswith("bot_"):
            try:
                bot.send_message(int(user_id), 
                    f"📢 <b>Сообщение от администрации:</b>\n\n{text}")
                sent += 1
            except:
                failed += 1
    
    bot.send_message(message.chat.id, 
        f"✅ Рассылка завершена!\n"
        f"Отправлено: {sent}\n"
        f"Ошибок: {failed}")

# ==================== ОБРАБОТКА КНОПОК МЕНЮ ====================
@bot.message_handler(func=lambda m: m.text and "ℹ Помощь" in m.text)
def menu_help(message):
    cmd_help(message)

@bot.message_handler(func=lambda m: m.text and "📈 Стат" in m.text)
def menu_stats(message):
    player = Player(message.from_user.id)
    stats = player.calculate_stats()
    
    stats_text = f"""
<b>📈 БОЕВЫЕ ХАРАКТЕРИСТИКИ</b>

⚔ Базовый урон: {stats['damage']}
🛡 Защита: {stats['defense']}
❤ Здоровье: {stats['hp']}/{stats['max_hp']}
💥 Крит. шанс: {stats['crit_chance']}%
💫 Множ. крита: x{stats['crit_multiplier']}
🌀 Уклонение: {stats['dodge_chance']}%
🛡 Блок: {stats['block_chance']}%
💚 Вампиризм: {stats['lifesteal']}%
🔄 Отражение: {stats['damage_reflect']}%
⚡ Скорость: {stats['speed']}%

✨ Маг. урон: {stats.get('magic_damage', 0)}
🔥 Огн. урон: {stats.get('fire_damage', 0)}
🦅 Шанс воскрешения: {stats.get('revive_chance', 0)}%
"""
    bot.send_message(message.chat.id, stats_text)

@bot.message_handler(func=lambda m: m.text and "💊 Лечить" in m.text)
def menu_heal(message):
    player = Player(message.from_user.id)
    current_hp = player.get_stat("hp", 0)
    max_hp = player.get_stat("max_hp", 100)
    
    if current_hp >= max_hp:
        bot.send_message(message.chat.id, "💚 У вас полное здоровье! Лечение не требуется.")
        return
    
    # Ищем зелья в инвентаре
    inventory = player.get_stat("inventory", [])
    potions = []
    for item_id in inventory:
        item = SHOP_ITEMS.get(item_id) or limited_items_data.get(item_id)
        if item and item.get("type") == "potion":
            potions.append(item_id)
    
    if not potions:
        bot.send_message(message.chat.id, 
            "❌ У вас нет зелий!\n"
            "Купите их в магазине: 🏪 Магазин -> 🧪 Зелья")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for potion_id in list(set(potions))[:5]:  # Показываем до 5 разных зелий
        item = SHOP_ITEMS.get(potion_id) or limited_items_data.get(potion_id)
        if item:
            count = potions.count(potion_id)
            markup.add(types.InlineKeyboardButton(
                f"{item['emoji']} {item['name']} (x{count})",
                callback_data=f"useitem_{potion_id}"
            ))
    
    bot.send_message(message.chat.id, 
        f"<b>💊 ЛЕЧЕНИЕ</b>\n\n"
        f"Текущее HP: {current_hp}/{max_hp}\n"
        f"Выберите зелье:",
        reply_markup=markup)

@bot.message_handler(func=lambda m: m.text and "⚙ Настр" in m.text)
def menu_settings(message):
    player = Player(message.from_user.id)
    settings = player.get_stat("settings", {})
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            f"🔔 Уведомления: {'ВКЛ' if settings.get('notifications', True) else 'ВЫКЛ'}",
            callback_data="toggle_notifications"
        ),
        types.InlineKeyboardButton(
            f"⚔ Запросы дуэлей: {'ВКЛ' if settings.get('duel_requests', True) else 'ВЫКЛ'}",
            callback_data="toggle_duel_requests"
        )
    )
    
    bot.send_message(message.chat.id, 
        "<b>⚙ НАСТРОЙКИ</b>\n\nВыберите параметр для изменения:",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
def callback_toggle_settings(call):
    player = Player(call.from_user.id)
    settings = player.get_stat("settings", {})
    setting_key = call.data.split("_", 1)[1]
    
    settings[setting_key] = not settings.get(setting_key, True)
    player.set_stat("settings", settings)
    
    bot.answer_callback_query(call.id, "✅ Настройка изменена!")
    menu_settings(call.message)

# ==================== ЗАПУСК БОТА ====================
def main():
    print("=" * 60)
    print("⚔ ДУЭЛЬ БОТ v4.0 - ПОЛНАЯ ВЕРСИЯ")
    print("=" * 60)
    print(f"📅 Запуск: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👤 Админ ID: {ADMIN_ID}")
    print(f"📦 Предметов в магазине: {len(SHOP_ITEMS)}")
    print(f"💎 Лимитированных предметов: {len(limited_items_data)}")
    print(f"🏅 Достижений: {len(ACHIEVEMENTS_LIST)}")
    print(f"📜 Типов квестов: {len(DAILY_QUESTS_POOL)}")
    print(f"👥 Пользователей в базе: {len(users)}")
    print(f"🛡 Кланов: {len(clans)}")
    print("=" * 60)
    print("✅ Бот успешно инициализирован!")
    print("📡 Запуск polling...")
    print("=" * 60)
    
    # Удаляем вебхук на всякий случай
    bot.remove_webhook()
    
    # Запускаем бота с защитой от падений
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠ Критическая ошибка: {e}")
            print(f"🔄 Перезапуск через 5 секунд...")
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Фатальная ошибка: {e}")
