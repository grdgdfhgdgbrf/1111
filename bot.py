import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import random
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict
import re
import math

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = '8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE'
ADMIN_ID = 5356400377
BOT_NAME = "ДУЭЛЬ БОТ v4.0"

# Инициализация бота с увеличенным таймаутом
bot = telebot.TeleBot(TOKEN, parse_mode='HTML', num_workers=4)

# ==================== КОНСТАНТЫ ====================
RARITY_COLORS = {
    "common": "⬜",
    "uncommon": "🟩",
    "rare": "🟦",
    "epic": "🟪",
    "legendary": "🟧",
    "mythic": "🟥",
    "divine": "💛",
    "apocalyptic": "🖤"
}

RARITY_NAMES = {
    "common": "Обычный",
    "uncommon": "Необычный",
    "rare": "Редкий",
    "epic": "Эпический",
    "legendary": "Легендарный",
    "mythic": "Мифический",
    "divine": "Божественный",
    "apocalyptic": "Апокалиптический"
}

DUEL_TYPES = {
    "quick": {"name": "⚡ Быстрая дуэль", "min_bet": 50, "max_bet": 200, "default_bet": 50, "reward_mult": 1.0},
    "normal": {"name": "⚔ Обычная дуэль", "min_bet": 30, "max_bet": 500, "default_bet": 100, "reward_mult": 1.5},
    "ranked": {"name": "🏆 Рейтинговая дуэль", "min_bet": 100, "max_bet": 1000, "default_bet": 200, "reward_mult": 2.0},
    "hardcore": {"name": "💀 Хардкорная дуэль", "min_bet": 500, "max_bet": 5000, "default_bet": 500, "reward_mult": 3.0},
    "friendly": {"name": "🎯 Дружеская дуэль", "min_bet": 0, "max_bet": 0, "default_bet": 0, "reward_mult": 0.0},
    "survival": {"name": "🔥 Дуэль на выживание", "min_bet": 100, "max_bet": 2000, "default_bet": 200, "reward_mult": 2.5}
}

# ==================== ФАЙЛЫ ДАННЫХ ====================
DATA_FILES = {
    'users': 'users.json',
    'items': 'items.json',
    'limited_items': 'limited_items.json',
    'active_duels': 'active_duels.json',
    'clans': 'clans.json',
    'tournaments': 'tournaments.json',
    'achievements': 'achievements.json',
    'daily_quests': 'daily_quests.json',
    'market': 'market.json',
    'global_stats': 'global_stats.json'
}

# ==================== ЗАГРУЗКА/СОХРАНЕНИЕ ДАННЫХ ====================
def safe_load_json(filename, default=None):
    """Безопасная загрузка JSON с обработкой ошибок"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data is None:
                return default if default is not None else {}
            return data
    except FileNotFoundError:
        if default is not None:
            safe_save_json(filename, default)
        return default if default is not None else {}
    except json.JSONDecodeError:
        print(f"⚠ Ошибка чтения {filename}, создаю новый")
        if default is not None:
            safe_save_json(filename, default)
        return default if default is not None else {}
    except Exception as e:
        print(f"⚠ Критическая ошибка загрузки {filename}: {e}")
        return default if default is not None else {}

def safe_save_json(filename, data):
    """Безопасное сохранение JSON с созданием резервной копии"""
    try:
        # Создаем резервную копию
        backup_filename = f"{filename}.backup"
        if __import__('os').path.exists(filename):
            __import__('shutil').copy2(filename, backup_filename)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠ Ошибка сохранения {filename}: {e}")
        return False

def load_all_data():
    """Загрузка всех данных бота"""
    global users, items, limited_items, active_duels
    global clans, tournaments, achievements_data
    global daily_quests, market_listings, global_stats
    
    users = safe_load_json(DATA_FILES['users'], {})
    items = safe_load_json(DATA_FILES['items'], {})
    limited_items = safe_load_json(DATA_FILES['limited_items'], {})
    active_duels = safe_load_json(DATA_FILES['active_duels'], {})
    clans = safe_load_json(DATA_FILES['clans'], {})
    tournaments = safe_load_json(DATA_FILES['tournaments'], {})
    achievements_data = safe_load_json(DATA_FILES['achievements'], {})
    daily_quests = safe_load_json(DATA_FILES['daily_quests'], {})
    market_listings = safe_load_json(DATA_FILES['market'], {})
    global_stats = safe_load_json(DATA_FILES['global_stats'], {
        "total_duels": 0,
        "total_money_spent": 0,
        "total_items_sold": 0,
        "server_started": datetime.now().isoformat()
    })

# ==================== ИНИЦИАЛИЗАЦИЯ ПРЕДМЕТОВ ====================
def init_items():
    """Инициализация предметов если файл пустой"""
    if not items:
        default_items = {
            # ОРУЖИЕ
            "wooden_sword": {
                "name": "🗡 Деревянный меч",
                "damage": 5,
                "price": 100,
                "type": "weapon",
                "rarity": "common",
                "level_req": 1,
                "description": "Простой меч для начинающих воинов",
                "stats_bonus": {"damage": 5}
            },
            "stone_sword": {
                "name": "🗿 Каменный меч",
                "damage": 8,
                "price": 200,
                "type": "weapon",
                "rarity": "common",
                "level_req": 3,
                "description": "Более прочный меч из камня",
                "stats_bonus": {"damage": 8}
            },
            "iron_sword": {
                "name": "⚔ Железный меч",
                "damage": 15,
                "price": 500,
                "type": "weapon",
                "rarity": "uncommon",
                "level_req": 5,
                "description": "Надёжный железный меч",
                "stats_bonus": {"damage": 15, "crit_chance": 3}
            },
            "steel_sword": {
                "name": "🔪 Стальной меч",
                "damage": 22,
                "price": 1200,
                "type": "weapon",
                "rarity": "uncommon",
                "level_req": 10,
                "description": "Острый стальной клинок",
                "stats_bonus": {"damage": 22, "crit_chance": 5}
            },
            "shadow_blade": {
                "name": "🌑 Теневой клинок",
                "damage": 30,
                "price": 2500,
                "type": "weapon",
                "rarity": "rare",
                "level_req": 15,
                "description": "Клинок, пропитанный тьмой",
                "stats_bonus": {"damage": 30, "dodge_chance": 5}
            },
            "dragon_sword": {
                "name": "🐉 Драконий меч",
                "damage": 40,
                "price": 5000,
                "type": "weapon",
                "rarity": "epic",
                "level_req": 20,
                "description": "Меч, выкованный из клыка дракона",
                "stats_bonus": {"damage": 40, "crit_chance": 10, "crit_multiplier": 0.3}
            },
            "excalibur": {
                "name": "⚡ Экскалибур",
                "damage": 55,
                "price": 10000,
                "type": "weapon",
                "rarity": "legendary",
                "level_req": 30,
                "description": "Легендарный меч короля Артура",
                "stats_bonus": {"damage": 55, "crit_chance": 15, "lifesteal": 5}
            },
            "chaos_blade": {
                "name": "💥 Клинок Хаоса",
                "damage": 75,
                "price": 25000,
                "type": "weapon",
                "rarity": "mythic",
                "level_req": 45,
                "description": "Клинок из самого сердца хаоса",
                "stats_bonus": {"damage": 75, "crit_chance": 20, "crit_multiplier": 0.5, "lifesteal": 10}
            },
            # ЩИТЫ
            "wooden_shield": {
                "name": "🛡 Деревянный щит",
                "defense": 5,
                "price": 150,
                "type": "shield",
                "rarity": "common",
                "level_req": 1,
                "description": "Простой деревянный щит",
                "stats_bonus": {"defense": 5}
            },
            "iron_shield": {
                "name": "🔰 Железный щит",
                "defense": 12,
                "price": 600,
                "type": "shield",
                "rarity": "uncommon",
                "level_req": 5,
                "description": "Надёжный железный щит",
                "stats_bonus": {"defense": 12}
            },
            "dragon_shield": {
                "name": "🐉 Драконий щит",
                "defense": 25,
                "price": 4000,
                "type": "shield",
                "rarity": "epic",
                "level_req": 20,
                "description": "Щит из драконьей чешуи",
                "stats_bonus": {"defense": 25, "damage_reflect": 10}
            },
            "aegis": {
                "name": "💫 Эгида",
                "defense": 40,
                "price": 15000,
                "type": "shield",
                "rarity": "legendary",
                "level_req": 35,
                "description": "Божественный щит Зевса",
                "stats_bonus": {"defense": 40, "damage_reflect": 20}
            },
            # БРОНЯ
            "leather_armor": {
                "name": "🧥 Кожаная броня",
                "defense": 5,
                "price": 200,
                "type": "armor",
                "rarity": "common",
                "level_req": 1,
                "description": "Лёгкая кожаная броня",
                "stats_bonus": {"defense": 5, "hp_bonus": 20}
            },
            "iron_armor": {
                "name": "🛡 Железная броня",
                "defense": 12,
                "price": 1000,
                "type": "armor",
                "rarity": "uncommon",
                "level_req": 8,
                "description": "Прочная железная броня",
                "stats_bonus": {"defense": 12, "hp_bonus": 50}
            },
            "dragon_armor": {
                "name": "🐉 Драконья броня",
                "defense": 25,
                "price": 8000,
                "type": "armor",
                "rarity": "epic",
                "level_req": 25,
                "description": "Великая броня из драконьей шкуры",
                "stats_bonus": {"defense": 25, "hp_bonus": 100}
            },
            "phoenix_armor": {
                "name": "🦅 Броня Феникса",
                "defense": 40,
                "price": 25000,
                "type": "armor",
                "rarity": "legendary",
                "level_req": 40,
                "description": "Возрождает владельца после смерти",
                "stats_bonus": {"defense": 40, "hp_bonus": 200, "special": "rebirth"}
            },
            # ЗЕЛЬЯ
            "health_potion": {
                "name": "🧪 Зелье здоровья",
                "heal": 30,
                "price": 50,
                "type": "potion",
                "rarity": "common",
                "level_req": 1,
                "description": "Восстанавливает 30 HP"
            },
            "big_health_potion": {
                "name": "🧪 Большое зелье",
                "heal": 75,
                "price": 150,
                "type": "potion",
                "rarity": "uncommon",
                "level_req": 5,
                "description": "Восстанавливает 75 HP"
            },
            "elixir_of_life": {
                "name": "💊 Эликсир жизни",
                "heal": 200,
                "price": 500,
                "type": "potion",
                "rarity": "rare",
                "level_req": 15,
                "description": "Мощное исцеляющее средство"
            },
            # АКСЕССУАРЫ
            "strength_amulet": {
                "name": "📿 Амулет Силы",
                "price": 3000,
                "type": "accessory",
                "rarity": "epic",
                "level_req": 20,
                "description": "Увеличивает урон на 15%",
                "stats_bonus": {"damage_percent": 15}
            },
            "lucky_charm": {
                "name": "🍀 Талисман Удачи",
                "price": 2500,
                "type": "accessory",
                "rarity": "rare",
                "level_req": 18,
                "description": "+10% к шансу критического удара",
                "stats_bonus": {"crit_chance": 10}
            },
            "vampire_ring": {
                "name": "💍 Кольцо Вампира",
                "price": 5000,
                "type": "accessory",
                "rarity": "epic",
                "level_req": 25,
                "description": "Вампиризм 15%",
                "stats_bonus": {"lifesteal": 15}
            },
            # ОБУВЬ
            "speed_boots": {
                "name": "👢 Сапоги Скорости",
                "price": 2000,
                "type": "boots",
                "rarity": "uncommon",
                "level_req": 12,
                "description": "+10 к скорости",
                "stats_bonus": {"speed": 10}
            },
            "wind_walkers": {
                "name": "💨 Ветроступы",
                "price": 5000,
                "type": "boots",
                "rarity": "epic",
                "level_req": 25,
                "description": "+20 к скорости и уклонению",
                "stats_bonus": {"speed": 20, "dodge_chance": 5}
            }
        }
        safe_save_json(DATA_FILES['items'], default_items)
        return default_items
    return items

def init_limited_items():
    """Инициализация лимитированных предметов"""
    if not limited_items:
        default_limited = {
            "thunderfury": {
                "name": "⚡ Гроза Богов",
                "damage": 100,
                "total": 3,
                "remaining": 3,
                "price": 50000,
                "type": "weapon",
                "rarity": "divine",
                "level_req": 50,
                "description": "Оружие самого Зевса! Молниеносные атаки",
                "special": "chain_lightning",
                "stats_bonus": {"damage": 100, "crit_chance": 25, "special": "chain_lightning"}
            },
            "world_ender": {
                "name": "🌋 Конец Света",
                "damage": 150,
                "total": 1,
                "remaining": 1,
                "price": 100000,
                "type": "weapon",
                "rarity": "apocalyptic",
                "level_req": 60,
                "description": "Единственный в своём роде! Уничтожает всё",
                "special": "armageddon",
                "stats_bonus": {"damage": 150, "crit_chance": 35, "special": "armageddon"}
            },
            "infinity_shield": {
                "name": "♾ Бесконечный щит",
                "defense": 80,
                "total": 5,
                "remaining": 5,
                "price": 75000,
                "type": "shield",
                "rarity": "divine",
                "level_req": 55,
                "description": "Щит, способный отразить любую атаку",
                "special": "perfect_defense",
                "stats_bonus": {"defense": 80, "damage_reflect": 30, "special": "perfect_defense"}
            },
            "invisibility_cloak": {
                "name": "👻 Плащ-невидимка",
                "defense": 30,
                "total": 7,
                "remaining": 7,
                "price": 45000,
                "type": "armor",
                "rarity": "mythic",
                "level_req": 45,
                "description": "Шанс избежать атаки противника",
                "special": "invisibility",
                "stats_bonus": {"defense": 30, "dodge_chance": 25, "special": "invisibility"}
            },
            "phoenix_feather": {
                "name": "🦅 Перо Феникса",
                "heal": 500,
                "total": 10,
                "remaining": 10,
                "price": 15000,
                "type": "potion",
                "rarity": "legendary",
                "level_req": 30,
                "description": "Полное восстановление здоровья",
                "special": "full_heal",
                "stats_bonus": {"heal": 500, "special": "full_heal"}
            }
        }
        safe_save_json(DATA_FILES['limited_items'], default_limited)
        return default_limited
    return limited_items

# ==================== КЛАСС ИГРОКА ====================
class Player:
    """Класс для работы с данными игрока"""
    
    def __init__(self, user_id, username=None, first_name=None):
        self.user_id = str(user_id)
        self._ensure_exists(username, first_name)
    
    def _ensure_exists(self, username, first_name):
        """Создание профиля игрока если не существует"""
        if self.user_id not in users:
            users[self.user_id] = {
                "username": username or f"user_{self.user_id}",
                "first_name": first_name or "Игрок",
                "money": 500,
                "crystals": 0,
                "level": 1,
                "exp": 0,
                "total_exp": 0,
                "hp": 100,
                "max_hp": 100,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "win_streak": 0,
                "best_streak": 0,
                "total_duels": 0,
                "inventory": [],
                "equipped": {
                    "weapon": None,
                    "shield": None,
                    "armor": None,
                    "accessory": None,
                    "boots": None
                },
                "last_daily": None,
                "last_duel": None,
                "title": "Новичок",
                "titles": ["Новичок"],
                "achievements": [],
                "clan": None,
                "tournament_wins": 0,
                "total_damage_dealt": 0,
                "total_damage_taken": 0,
                "critical_hits": 0,
                "items_used": 0,
                "registration_date": datetime.now().isoformat(),
                "settings": {
                    "notifications": True,
                    "duel_requests": True,
                    "show_effects": True,
                    "auto_equip": False
                },
                "stats": {
                    "strength": 5,
                    "agility": 5,
                    "vitality": 5,
                    "luck": 5,
                    "stat_points": 0
                }
            }
            safe_save_json(DATA_FILES['users'], users)
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    @data.setter
    def data(self, value):
        users[self.user_id] = value
    
    def save(self):
        """Сохранение данных игрока"""
        return safe_save_json(DATA_FILES['users'], users)
    
    def add_money(self, amount):
        """Добавление монет"""
        self.data["money"] += amount
        if self.data["money"] < 0:
            self.data["money"] = 0
        self.save()
    
    def add_exp(self, amount):
        """Добавление опыта"""
        self.data["exp"] += amount
        self.data["total_exp"] += amount
        self.check_level_up()
    
    def check_level_up(self):
        """Проверка повышения уровня"""
        level = self.data["level"]
        exp_needed = self._exp_for_level(level)
        leveled_up = False
        
        while self.data["exp"] >= exp_needed:
            self.data["exp"] -= exp_needed
            self.data["level"] += 1
            self.data["max_hp"] = 100 + (self.data["level"] - 1) * 15
            self.data["hp"] = self.data["max_hp"]
            self.data["stats"]["stat_points"] += 3
            leveled_up = True
            
            # Обновление титула
            self._update_title()
            
            level = self.data["level"]
            exp_needed = self._exp_for_level(level)
        
        if leveled_up:
            self.save()
        
        return leveled_up
    
    def _exp_for_level(self, level):
        """Расчёт опыта для уровня"""
        return int(100 * (1.5 ** (level - 1)))
    
    def _update_title(self):
        """Обновление титула игрока"""
        titles = [
            (1, "Новичок"), (5, "Боец"), (10, "Воитель"),
            (15, "Рыцарь"), (20, "Ветеран"), (25, "Мастер"),
            (30, "Грандмастер"), (40, "Герой"), (50, "Легенда"),
            (60, "Мифический воин"), (75, "Полубог"), (100, "Божество")
        ]
        
        for req_level, title in titles:
            if self.data["level"] >= req_level and title not in self.data["titles"]:
                self.data["titles"].append(title)
                self.data["title"] = title
    
    def get_stats(self):
        """Получение полных характеристик"""
        base_stats = {
            "damage": self.data["stats"]["strength"] * 2 + self.data["level"] * 3,
            "defense": self.data["stats"]["vitality"] * 1.5,
            "hp": self.data["hp"],
            "max_hp": self.data["max_hp"],
            "crit_chance": 5 + self.data["stats"]["luck"] * 2,
            "crit_multiplier": 1.5,
            "dodge_chance": 3 + self.data["stats"]["agility"] * 2,
            "speed": self.data["stats"]["agility"] * 1.5,
            "lifesteal": 0,
            "damage_reflect": 0,
            "damage_percent": 0
        }
        
        # Применение бонусов от экипировки
        for slot, item_key in self.data["equipped"].items():
            if item_key:
                item = items.get(item_key) or limited_items.get(item_key)
                if item and "stats_bonus" in item:
                    for stat, value in item["stats_bonus"].items():
                        if stat == "special":
                            base_stats["special"] = value
                        elif stat == "damage_percent":
                            base_stats["damage_percent"] += value
                        elif stat in base_stats:
                            base_stats[stat] += value
        
        # Применение процентов
        base_stats["damage"] = int(base_stats["damage"] * (1 + base_stats["damage_percent"] / 100))
        
        # Ограничения
        base_stats["crit_chance"] = min(base_stats["crit_chance"], 85)
        base_stats["dodge_chance"] = min(base_stats["dodge_chance"], 50)
        
        return base_stats
    
    def has_item(self, item_key):
        """Проверка наличия предмета"""
        return item_key in self.data["inventory"]
    
    def add_item(self, item_key):
        """Добавление предмета в инвентарь"""
        self.data["inventory"].append(item_key)
        self.save()
    
    def remove_item(self, item_key):
        """Удаление предмета из инвентаря"""
        if item_key in self.data["inventory"]:
            self.data["inventory"].remove(item_key)
            
            # Снимаем предмет если экипирован
            for slot, equipped in self.data["equipped"].items():
                if equipped == item_key:
                    self.data["equipped"][slot] = None
            
            self.save()
            return True
        return False
    
    def equip_item(self, item_key):
        """Экипировка предмета"""
        item = items.get(item_key) or limited_items.get(item_key)
        if not item:
            return False
        
        if not self.has_item(item_key):
            return False
        
        if self.data["level"] < item.get("level_req", 1):
            return False
        
        item_type = item["type"]
        slot_mapping = {
            "weapon": "weapon",
            "shield": "shield",
            "armor": "armor",
            "accessory": "accessory",
            "boots": "boots"
        }
        
        if item_type in slot_mapping:
            old_item = self.data["equipped"][slot_mapping[item_type]]
            self.data["equipped"][slot_mapping[item_type]] = item_key
            
            # Если был предмет - оставляем в инвентаре
            if old_item and old_item != item_key:
                pass  # Старый предмет уже в инвентаре
            
            self.save()
            return True
        
        return False

# ==================== СИСТЕМА ДУЭЛЕЙ ====================
class DuelSystem:
    """Система управления дуэлями"""
    
    def __init__(self):
        self.active_duels = active_duels
    
    def create_duel(self, player1_id, player2_id, duel_type="normal", bet=0):
        """Создание новой дуэли"""
        duel_id = f"duel_{int(time.time())}_{random.randint(1000, 9999)}"
        
        duel = {
            "id": duel_id,
            "player1_id": str(player1_id),
            "player2_id": str(player2_id),
            "type": duel_type,
            "bet": bet,
            "status": "waiting",  # waiting, active, finished
            "current_turn": 1,
            "p1_hp": None,
            "p2_hp": None,
            "p1_max_hp": None,
            "p2_max_hp": None,
            "effects": {"p1": [], "p2": []},
            "turn_count": 0,
            "max_turns": 30,
            "battle_log": [],
            "created_at": datetime.now().isoformat()
        }
        
        self.active_duels[duel_id] = duel
        safe_save_json(DATA_FILES['active_duels'], self.active_duels)
        
        return duel_id
    
    def start_duel(self, duel_id):
        """Запуск дуэли"""
        if duel_id not in self.active_duels:
            return False
        
        duel = self.active_duels[duel_id]
        duel["status"] = "active"
        
        # Инициализация HP
        p1 = Player(duel["player1_id"])
        p2 = Player(duel["player2_id"])
        
        duel["p1_hp"] = p1.get_stats()["max_hp"]
        duel["p2_hp"] = p2.get_stats()["max_hp"]
        duel["p1_max_hp"] = duel["p1_hp"]
        duel["p2_max_hp"] = duel["p2_hp"]
        
        # Определение первого хода
        p1_speed = p1.get_stats()["speed"]
        p2_speed = p2.get_stats()["speed"]
        
        if p1_speed > p2_speed:
            duel["current_turn"] = 1
        elif p2_speed > p1_speed:
            duel["current_turn"] = 2
        else:
            duel["current_turn"] = random.choice([1, 2])
        
        self.active_duels[duel_id] = duel
        safe_save_json(DATA_FILES['active_duels'], self.active_duels)
        
        return True
    
    def execute_turn(self, duel_id):
        """Выполнение хода в дуэли"""
        if duel_id not in self.active_duels:
            return None
        
        duel = self.active_duels[duel_id]
        
        if duel["status"] != "active":
            return None
        
        # Определение атакующего и защищающегося
        if duel["current_turn"] == 1:
            attacker_id = duel["player1_id"]
            defender_id = duel["player2_id"]
            attacker_hp_key = "p1_hp"
            defender_hp_key = "p2_hp"
            next_turn = 2
        else:
            attacker_id = duel["player2_id"]
            defender_id = duel["player1_id"]
            attacker_hp_key = "p2_hp"
            defender_hp_key = "p1_hp"
            next_turn = 1
        
        attacker = Player(attacker_id)
        defender = Player(defender_id)
        
        att_stats = attacker.get_stats()
        def_stats = defender.get_stats()
        
        # Проверка спецэффектов
        if "special" in def_stats and def_stats["special"] == "invisibility":
            if random.random() < 0.3:  # 30% шанс невидимости
                duel["battle_log"].append(f"👻 {defender.data['first_name']} исчезает в тени! Атака промахнулась!")
                duel[attacker_hp_key] = max(0, duel[attacker_hp_key] - random.randint(5, 15))  # Контратака тени
                duel["current_turn"] = next_turn
                duel["turn_count"] += 1
                self.active_duels[duel_id] = duel
                safe_save_json(DATA_FILES['active_duels'], self.active_duels)
                return duel
        
        # Расчёт урона
        base_damage = att_stats["damage"] + random.randint(-5, 10)
        
        # Критический удар
        is_crit = random.random() * 100 < att_stats["crit_chance"]
        if is_crit:
            base_damage = int(base_damage * att_stats["crit_multiplier"])
            attacker.data["critical_hits"] += 1
            duel["battle_log"].append(f"💥 КРИТИЧЕСКИЙ УДАР! x{att_stats['crit_multiplier']}")
        
        # Проверка спецэффектов оружия
        if "special" in att_stats:
            if att_stats["special"] == "chain_lightning":
                bonus_damage = random.randint(20, 40)
                base_damage += bonus_damage
                duel["battle_log"].append(f"⚡ Цепная молния! +{bonus_damage} урона")
            elif att_stats["special"] == "armageddon":
                base_damage = int(base_damage * 1.5)
                duel["battle_log"].append(f"🌋 АРМАГЕДДОН! Урон увеличен в 1.5 раза")
        
        # Уклонение
        if random.random() * 100 < def_stats["dodge_chance"]:
            duel["battle_log"].append(f"🌀 {defender.data['first_name']} уклоняется от атаки!")
            base_damage = 0
        
        # Применение защиты
        final_damage = max(1, base_damage - def_stats["defense"])
        
        # Вампиризм
        lifesteal_heal = int(final_damage * att_stats["lifesteal"] / 100)
        if lifesteal_heal > 0:
            duel[attacker_hp_key] = min(att_stats["max_hp"], duel[attacker_hp_key] + lifesteal_heal)
            duel["battle_log"].append(f"💚 Вампиризм: +{lifesteal_heal} HP")
        
        # Отражение урона
        reflect_damage = int(final_damage * def_stats["damage_reflect"] / 100)
        if reflect_damage > 0:
            duel[attacker_hp_key] -= reflect_damage
            duel["battle_log"].append(f"🔄 Отражение: -{reflect_damage} HP атакующему")
        
        # Нанесение урона
        duel[defender_hp_key] -= final_damage
        duel["battle_log"].append(f"⚔ {attacker.data['first_name']} наносит {final_damage} урона {defender.data['first_name']}")
        
        # Обновление счётчиков
        attacker.data["total_damage_dealt"] += final_damage
        defender.data["total_damage_taken"] += final_damage
        
        # Проверка спецэффекта rebirth
        if "special" in def_stats and def_stats["special"] == "rebirth":
            if duel[defender_hp_key] <= 0 and random.random() < 0.4:  # 40% шанс возрождения
                duel[defender_hp_key] = int(def_stats["max_hp"] * 0.5)
                duel["battle_log"].append(f"🦅 {defender.data['first_name']} ВОЗРОЖДАЕТСЯ ИЗ ПЕПЛА! +50% HP")
        
        duel["current_turn"] = next_turn
        duel["turn_count"] += 1
        
        # Проверка завершения
        if duel[defender_hp_key] <= 0 or duel[attacker_hp_key] <= 0 or duel["turn_count"] >= duel["max_turns"]:
            duel["status"] = "finished"
            self._finish_duel(duel_id)
        
        attacker.save()
        defender.save()
        
        self.active_duels[duel_id] = duel
        safe_save_json(DATA_FILES['active_duels'], self.active_duels)
        
        return duel
    
    def _finish_duel(self, duel_id):
        """Завершение дуэли и распределение наград"""
        duel = self.active_duels[duel_id]
        
        p1 = Player(duel["player1_id"])
        p2 = Player(duel["player2_id"])
        
        duel_type_config = DUEL_TYPES.get(duel["type"], DUEL_TYPES["quick"])
        reward_mult = duel_type_config["reward_mult"]
        
        if duel["p1_hp"] <= 0 and duel["p2_hp"] <= 0:
            # Ничья
            winner = None
            p1.data["draws"] += 1
            p2.data["draws"] += 1
            duel["winner"] = None
        elif duel["p1_hp"] <= 0:
            # Победил игрок 2
            winner = p2
            loser = p1
            duel["winner"] = duel["player2_id"]
        elif duel["p2_hp"] <= 0:
            # Победил игрок 1
            winner = p1
            loser = p2
            duel["winner"] = duel["player1_id"]
        else:
            # Истекло время - победа по очкам
            if duel["p1_hp"] > duel["p2_hp"]:
                winner = p1
                loser = p2
                duel["winner"] = duel["player1_id"]
            elif duel["p2_hp"] > duel["p1_hp"]:
                winner = p2
                loser = p1
                duel["winner"] = duel["player2_id"]
            else:
                winner = None
                p1.data["draws"] += 1
                p2.data["draws"] += 1
                duel["winner"] = None
        
        if winner:
            winner.data["wins"] += 1
            winner.data["win_streak"] += 1
            if winner.data["win_streak"] > winner.data["best_streak"]:
                winner.data["best_streak"] = winner.data["win_streak"]
            
            loser.data["losses"] += 1
            loser.data["win_streak"] = 0
            
            # Награда
            if duel["bet"] > 0:
                reward = int(duel["bet"] * 2 * reward_mult)
                winner.add_money(reward)
                loser.add_money(-duel["bet"])
            
            # Опыт
            exp_reward = 30 + int(duel["bet"] / 10) * reward_mult
            winner.add_exp(exp_reward)
            loser.add_exp(exp_reward // 3)
            
            # Проверка достижений
            self._check_achievements(winner)
            self._check_achievements(loser)
        
        # Обновление статистики
        p1.data["total_duels"] += 1
        p2.data["total_duels"] += 1
        p1.data["last_duel"] = datetime.now().isoformat()
        p2.data["last_duel"] = datetime.now().isoformat()
        
        p1.save()
        p2.save()
        
        global_stats["total_duels"] += 1
        safe_save_json(DATA_FILES['global_stats'], global_stats)
    
    def _check_achievements(self, player):
        """Проверка достижений игрока"""
        achieved = []
        
        if player.data["wins"] >= 1 and "first_blood" not in player.data["achievements"]:
            achieved.append("first_blood")
        if player.data["wins"] >= 10 and "warrior" not in player.data["achievements"]:
            achieved.append("warrior")
        if player.data["wins"] >= 50 and "veteran" not in player.data["achievements"]:
            achieved.append("veteran")
        if player.data["wins"] >= 100 and "legend" not in player.data["achievements"]:
            achieved.append("legend")
        if player.data["money"] >= 10000 and "rich" not in player.data["achievements"]:
            achieved.append("rich")
        if player.data["money"] >= 100000 and "millionaire" not in player.data["achievements"]:
            achieved.append("millionaire")
        
        for ach in achieved:
            player.data["achievements"].append(ach)
            # Награда за достижение
            rewards = {
                "first_blood": 200,
                "warrior": 500,
                "veteran": 2000,
                "legend": 5000,
                "rich": 1000,
                "millionaire": 10000
            }
            player.add_money(rewards.get(ach, 0))

duel_system = DuelSystem()

# ==================== ИНТЕРФЕЙС БОТА ====================
def create_main_menu():
    """Создание компактного главного меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    buttons = [
        "⚔Дуэль", "👤Профиль", "🎒Инв", "🏪Магаз",
        "💎Редк", "📊Топ", "🛡Клан", "📜Квест",
        "🏅Ачив", "💊Хил", "📈Буст", "⚙Настр"
    ]
    markup.add(*[types.KeyboardButton(b) for b in buttons])
    return markup

def create_duel_menu():
    """Создание меню дуэлей"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for duel_type, config in DUEL_TYPES.items():
        bet_range = f"{config['min_bet']}-{config['max_bet']}💰" if config['max_bet'] > 0 else "Без ставок"
        markup.add(types.InlineKeyboardButton(
            f"{config['name']} | {bet_range}",
            callback_data=f"duelmenu_{duel_type}"
        ))
    
    markup.add(types.InlineKeyboardButton("🎲 Случайная дуэль", callback_data="duel_random"))
    
    return markup

def create_shop_menu(category=None):
    """Создание меню магазина"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if not category:
        # Главное меню магазина
        categories = [
            ("⚔ Оружие", "weapon"),
            ("🛡 Щиты", "shield"),
            ("🧥 Броня", "armor"),
            ("🧪 Зелья", "potion"),
            ("📿 Аксессуары", "accessory"),
            ("👢 Обувь", "boots")
        ]
        
        for cat_name, cat_type in categories:
            markup.add(types.InlineKeyboardButton(cat_name, callback_data=f"shopcat_{cat_type}"))
        
        markup.add(types.InlineKeyboardButton("💎 Лимитированные", callback_data="shop_limited"))
        markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="shop_main"))
    else:
        # Категория товаров
        cat_items = {k: v for k, v in items.items() 
                     if v["type"] == category and v.get("level_req", 1) <= 1000}
        
        sorted_items = sorted(cat_items.items(), key=lambda x: x[1]["price"])
        
        for item_key, item in sorted_items:
            rarity_icon = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
            markup.add(types.InlineKeyboardButton(
                f"{rarity_icon} {item['name']} - {item['price']}💰",
                callback_data=f"buyitem_{item_key}"
            ))
        
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="shop_main"))
    
    return markup

# ==================== ОБРАБОТЧИКИ КОМАНД ====================
@bot.message_handler(commands=['start'])
def cmd_start(message):
    """Стартовое сообщение"""
    user_id = message.from_user.id
    player = Player(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    welcome_text = f"""
<b>⚔ {BOT_NAME} ⚔</b>

Добро пожаловать, <b>{message.from_user.first_name}</b>!

🎮 <b>Возможности бота:</b>
• 6 режимов дуэлей с выбором ставок
• Улучшенная боевая система
• 30+ предметов экипировки
• Лимитированные легендарные предметы
• Система кланов и турниров
• Ежедневные задания и достижения
• Система характеристик и прокачки

💰 <b>Стартовый бонус:</b> 500 монет
🎁 <b>Ежедневный бонус:</b> /daily
⚔ <b>Дуэли:</b> кнопка "⚔Дуэль"

Удачных сражений, воин!
"""
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=create_main_menu()
    )

@bot.message_handler(commands=['help'])
def cmd_help(message):
    """Помощь по командам"""
    help_text = """
<b>📚 СПРАВКА ПО КОМАНДАМ</b>

<b>⚔ Дуэли:</b>
/duel [ставка] - вызов на дуэль (ответьте на сообщение)
/quickduel - быстрая дуэль с ботом
/accept - принять дуэль

<b>👤 Профиль:</b>
/profile - ваш профиль
/inventory - инвентарь
/equip [id] - экипировать предмет
/stats - характеристики

<b>🏪 Экономика:</b>
/shop - магазин
/buy [id] - купить предмет
/daily - ежедневный бонус

<b>🎮 Ролевые:</b>
/hi, /dance, /attack, /defend
и другие РП команды

<b>📊 Рейтинг:</b>
/top - таблица лидеров

<b>🛡 Клан:</b>
/clan - информация о клане
/create_clan [имя] - создать клан
"""
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(func=lambda m: m.text == "⚔Дуэль")
@bot.message_handler(commands=['duel_menu'])
def duel_menu(message):
    """Меню дуэлей"""
    bot.send_message(
        message.chat.id,
        "<b>⚔ СИСТЕМА ДУЭЛЕЙ</b>\n\nВыберите тип дуэли:",
        reply_markup=create_duel_menu()
    )

@bot.message_handler(func=lambda m: m.text == "👤Профиль")
@bot.message_handler(commands=['profile'])
def profile(message):
    """Профиль игрока"""
    user_id = message.from_user.id
    player = Player(user_id)
    stats = player.get_stats()
    
    # Расчет винрейта
    total_games = player.data["wins"] + player.data["losses"] + player.data["draws"]
    winrate = (player.data["wins"] / total_games * 100) if total_games > 0 else 0
    
    # Экипировка
    equipped_text = []
    for slot, item_key in player.data["equipped"].items():
        if item_key:
            item = items.get(item_key) or limited_items.get(item_key)
            equipped_text.append(f"{item['name']}" if item else "Пусто")
        else:
            equipped_text.append("Пусто")
    
    profile_text = f"""
<b>👤 ПРОФИЛЬ ИГРОКА</b>

<b>{player.data['first_name']}</b> | {player.data['title']}
🆔 ID: <code>{user_id}</code>
⭐ Уровень: <b>{player.data['level']}</b>
✨ Опыт: {player.data['exp']}/{player._exp_for_level(player.data['level'])}
💎 Кристаллы: {player.data['crystals']}

<b>⚔ Боевые характеристики:</b>
❤ HP: {player.data['hp']}/{player.data['max_hp']}
⚔ Урон: {stats['damage']}
🛡 Защита: {stats['defense']}
💥 Крит: {stats['crit_chance']}%
🌀 Уклонение: {stats['dodge_chance']}%
💨 Скорость: {stats['speed']}

<b>📊 Статистика:</b>
🏆 Побед: {player.data['wins']}
💀 Поражений: {player.data['losses']}
🤝 Ничьих: {player.data['draws']}
📈 Винрейт: {winrate:.1f}%
🔥 Серия побед: {player.data['win_streak']}
👑 Лучшая серия: {player.data['best_streak']}

💰 Баланс: <b>{player.data['money']} монет</b>
🎒 Предметов: {len(player.data['inventory'])}
🏅 Достижений: {len(player.data['achievements'])}

<b>⚙ Экипировка:</b>
⚔ Оружие: {equipped_text[0] if len(equipped_text) > 0 else 'Нет'}
🛡 Щит: {equipped_text[1] if len(equipped_text) > 1 else 'Нет'}
🧥 Броня: {equipped_text[2] if len(equipped_text) > 2 else 'Нет'}
📿 Аксессуар: {equipped_text[3] if len(equipped_text) > 3 else 'Нет'}
👢 Обувь: {equipped_text[4] if len(equipped_text) > 4 else 'Нет'}
"""
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Характеристики", callback_data="show_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="show_inventory"),
        types.InlineKeyboardButton("🏅 Достижения", callback_data="show_achievements"),
        types.InlineKeyboardButton("⬆ Прокачка", callback_data="upgrade_stats")
    )
    
    bot.send_message(message.chat.id, profile_text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🏪Магаз")
@bot.message_handler(commands=['shop'])
def shop_main(message):
    """Главное меню магазина"""
    shop_text = """
<b>🏪 МАГАЗИН ПРЕДМЕТОВ</b>

Выберите категорию товаров:

⚔ <b>Оружие</b> - увеличивает урон
🛡 <b>Щиты</b> - увеличивают защиту
🧥 <b>Броня</b> - увеличивает защиту и HP
🧪 <b>Зелья</b> - восстанавливают здоровье
📿 <b>Аксессуары</b> - особые бонусы
👢 <b>Обувь</b> - скорость и уклонение

💎 <b>Лимитированные</b> - уникальные предметы!
"""
    bot.send_message(
        message.chat.id,
        shop_text,
        reply_markup=create_shop_menu()
    )

@bot.message_handler(func=lambda m: m.text == "💊Хил")
@bot.message_handler(commands=['heal'])
def heal(message):
    """Использование зелий здоровья"""
    user_id = message.from_user.id
    player = Player(user_id)
    
    if player.data["hp"] >= player.data["max_hp"]:
        bot.send_message(message.chat.id, "✅ У вас полное здоровье!")
        return
    
    # Поиск зелий в инвентаре
    potions = []
    for item_key in player.data["inventory"]:
        item = items.get(item_key) or limited_items.get(item_key)
        if item and item["type"] == "potion":
            potions.append((item_key, item))
    
    if not potions:
        bot.send_message(message.chat.id, "❌ У вас нет зелий здоровья! Купите их в магазине.")
        return
    
    # Использование самого слабого зелья
    potions.sort(key=lambda x: x[1].get("heal", 0))
    item_key, potion = potions[0]
    
    heal_amount = potion.get("heal", 30)
    player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + heal_amount)
    player.remove_item(item_key)
    player.data["items_used"] += 1
    player.save()
    
    bot.send_message(
        message.chat.id,
        f"💊 Вы использовали <b>{potion['name']}</b>\n"
        f"❤ Восстановлено: +{heal_amount} HP\n"
        f"Текущее здоровье: {player.data['hp']}/{player.data['max_hp']}"
    )

@bot.message_handler(func=lambda m: m.text == "📈Буст")
@bot.message_handler(commands=['boost'])
def boost_menu(message):
    """Меню усилений"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💪 Усиление атаки (100💰)", callback_data="boost_attack"),
        types.InlineKeyboardButton("🛡 Усиление защиты (100💰)", callback_data="boost_defense"),
        types.InlineKeyboardButton("💨 Ускорение (150💰)", callback_data="boost_speed"),
        types.InlineKeyboardButton("💥 Шанс крита (200💰)", callback_data="boost_crit")
    )
    
    bot.send_message(
        message.chat.id,
        "<b>📈 ВРЕМЕННЫЕ УСИЛЕНИЯ</b>\n\n"
        "Усиления действуют 1 час и дают бонус:\n\n"
        "💪 Атака: +20% к урону\n"
        "🛡 Защита: +30% к защите\n"
        "💨 Скорость: +25 к скорости\n"
        "💥 Крит: +15% к шансу крита",
        reply_markup=markup
    )

@bot.message_handler(commands=['duel'])
def duel_challenge(message):
    """Вызов на дуэль с выбором ставки"""
    if not message.reply_to_message:
        bot.send_message(
            message.chat.id,
            "❌ Ответьте на сообщение игрока, которого хотите вызвать на дуэль!\n"
            "Использование: /duel [ставка]"
        )
        return
    
    challenger_id = message.from_user.id
    opponent_id = message.reply_to_message.from_user.id
    
    if challenger_id == opponent_id:
        bot.send_message(message.chat.id, "❌ Нельзя вызвать на дуэль самого себя!")
        return
    
    # Парсинг ставки
    parts = message.text.split()
    if len(parts) > 1:
        try:
            bet = int(parts[1])
            if bet < 0:
                bet = 100
            elif bet > 10000:
                bet = 10000
        except ValueError:
            bet = 100
    else:
        bet = 100
    
    challenger = Player(challenger_id)
    opponent = Player(opponent_id)
    
    if bet > 0:
        if challenger.data["money"] < bet:
            bot.send_message(message.chat.id, f"❌ У вас недостаточно монет! Ваш баланс: {challenger.data['money']}💰")
            return
        if opponent.data["money"] < bet:
            bot.send_message(message.chat.id, f"❌ У противника недостаточно монет для ставки {bet}💰!")
            return
    
    # Создание дуэли
    duel_id = duel_system.create_duel(challenger_id, opponent_id, "normal", bet)
    
    # Кнопки подтверждения
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"accept_duel_{duel_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_duel_{duel_id}")
    )
    
    challenge_text = f"""
<b>⚔ ВЫЗОВ НА ДУЭЛЬ!</b>

<b>{message.from_user.first_name}</b> вызывает <b>{message.reply_to_message.from_user.first_name}</b>!

💰 Ставка: <b>{bet} монет</b>
⚔ Тип: Обычная дуэль

Ожидание подтверждения...
"""
    bot.send_message(message.chat.id, challenge_text, reply_markup=markup)

@bot.message_handler(commands=['daily'])
def daily_bonus(message):
    """Ежедневный бонус"""
    user_id = message.from_user.id
    player = Player(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player.data["last_daily"] == today:
        bot.send_message(message.chat.id, "🎁 Вы уже получили ежедневный бонус! Приходите завтра.")
        return
    
    # Расчёт бонуса с учётом уровня
    base_bonus = 100
    level_bonus = player.data["level"] * 15
    streak_bonus = player.data["win_streak"] * 10
    total_bonus = base_bonus + level_bonus + streak_bonus
    
    # Бонусный опыт
    exp_bonus = 50 + player.data["level"] * 10
    
    # Шанс на предмет
    got_item = None
    if random.random() < 0.15:  # 15% шанс
        rare_items = [k for k, v in items.items() if v.get("rarity") in ["uncommon", "rare"]]
        if rare_items:
            got_item = random.choice(rare_items)
            player.add_item(got_item)
    
    player.data["money"] += total_bonus
    player.data["exp"] += exp_bonus
    player.data["last_daily"] = today
    
    old_level = player.data["level"]
    leveled_up = player.check_level_up()
    player.save()
    
    result_text = f"""
<b>🎁 ЕЖЕДНЕВНЫЙ БОНУС</b>

💰 Монет: <b>+{total_bonus}</b>
  • Базовый: {base_bonus}
  • За уровень: +{level_bonus}
  • За серию побед: +{streak_bonus}

✨ Опыта: <b>+{exp_bonus}</b>
"""
    
    if got_item:
        item = items[got_item]
        result_text += f"\n🎒 Найден предмет: <b>{item['name']}</b>!"
    
    if leveled_up:
        result_text += f"\n🎉 НОВЫЙ УРОВЕНЬ: <b>{player.data['level']}</b>!"
    
    bot.send_message(message.chat.id, result_text)

@bot.message_handler(commands=['top'])
def top_players(message):
    """Топ игроков"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🏆 По уровню", callback_data="top_level"),
        types.InlineKeyboardButton("⚔ По победам", callback_data="top_wins"),
        types.InlineKeyboardButton("💰 По богатству", callback_data="top_money"),
        types.InlineKeyboardButton("🔥 По серии побед", callback_data="top_streak")
    )
    
    bot.send_message(
        message.chat.id,
        "<b>📊 ТОП ИГРОКОВ</b>\n\nВыберите категорию:",
        reply_markup=markup
    )

# ==================== ОБРАБОТКА CALLBACK ЗАПРОСОВ ====================
@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    """Обработка всех callback запросов"""
    user_id = call.from_user.id
    player = Player(user_id)
    
    try:
        # Меню дуэлей
        if call.data.startswith("duelmenu_"):
            duel_type = call.data.split("_")[1]
            handle_duel_type_selection(call, duel_type)
        
        # Принятие дуэли
        elif call.data.startswith("accept_duel_"):
            duel_id = call.data.split("_", 2)[2]
            handle_accept_duel(call, duel_id)
        
        # Отклонение дуэли
        elif call.data.startswith("decline_duel_"):
            duel_id = call.data.split("_", 2)[2]
            handle_decline_duel(call, duel_id)
        
        # Магазин
        elif call.data == "shop_main":
            shop_main(call.message)
        
        elif call.data.startswith("shopcat_"):
            category = call.data.split("_")[1]
            show_shop_category(call, category)
        
        elif call.data == "shop_limited":
            show_limited_shop(call)
        
        elif call.data.startswith("buyitem_"):
            item_key = call.data.split("_", 1)[1]
            handle_buy_item(call, item_key)
        
        elif call.data.startswith("buylimited_"):
            item_key = call.data.split("_", 1)[1]
            handle_buy_limited(call, item_key)
        
        # Инвентарь и экипировка
        elif call.data == "show_inventory":
            show_inventory(call)
        
        elif call.data.startswith("equip_"):
            item_key = call.data.split("_", 1)[1]
            handle_equip_item(call, item_key)
        
        elif call.data.startswith("use_"):
            item_key = call.data.split("_", 1)[1]
            handle_use_potion(call, item_key)
        
        # Профиль
        elif call.data == "show_stats":
            show_stats(call)
        
        elif call.data == "show_achievements":
            show_achievements(call)
        
        elif call.data == "upgrade_stats":
            show_upgrade_menu(call)
        
        elif call.data.startswith("upgrade_"):
            stat = call.data.split("_")[1]
            handle_upgrade_stat(call, stat)
        
        # Топы
        elif call.data.startswith("top_"):
            category = call.data.split("_")[1]
            show_top(call, category)
        
        # Усиления
        elif call.data.startswith("boost_"):
            boost_type = call.data.split("_")[1]
            handle_boost(call, boost_type)
        
        # Закрыть сообщение
        elif call.data == "close":
            bot.delete_message(call.message.chat.id, call.message.message_id)
        
        else:
            bot.answer_callback_query(call.id, "❓ Неизвестная команда")
    
    except Exception as e:
        print(f"Ошибка в callback: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка. Попробуйте снова.")

def handle_duel_type_selection(call, duel_type):
    """Обработка выбора типа дуэли"""
    if duel_type not in DUEL_TYPES:
        bot.answer_callback_query(call.id, "❌ Неизвестный тип дуэли!")
        return
    
    config = DUEL_TYPES[duel_type]
    player = Player(call.from_user.id)
    
    # Проверка баланса для ставок
    if config["min_bet"] > 0 and player.data["money"] < config["min_bet"]:
        bot.answer_callback_query(
            call.id,
            f"❌ Недостаточно монет! Минимальная ставка: {config['min_bet']}💰\n"
            f"Ваш баланс: {player.data['money']}💰"
        )
        return
    
    # Создание клавиатуры выбора ставки
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    if config["max_bet"] > 0:
        # Предустановленные ставки
        bets = []
        current = config["min_bet"]
        while current <= config["max_bet"]:
            bets.append(current)
            if current < 100:
                current *= 2
            elif current < 1000:
                current += 200
            else:
                current += 1000
        
        for bet in bets[:9]:  # Максимум 9 кнопок
            markup.add(types.InlineKeyboardButton(
                f"{bet}💰",
                callback_data=f"startduel_{duel_type}_{bet}"
            ))
    else:
        # Бесплатная дуэль
        markup.add(types.InlineKeyboardButton(
            "🎯 Начать бесплатную дуэль",
            callback_data=f"startduel_{duel_type}_0"
        ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="close"))
    
    bet_info = ""
    if config["max_bet"] > 0:
        bet_info = f"\n💰 Ставка: {config['min_bet']}-{config['max_bet']} монет"
    else:
        bet_info = "\n🎯 Без ставок"
    
    bot.edit_message_text(
        f"<b>{config['name']}</b>{bet_info}\n\n"
        f"Множитель награды: x{config['reward_mult']}\n\n"
        f"Выберите ставку:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

def handle_accept_duel(call, duel_id):
    """Обработка принятия дуэли"""
    if duel_id not in active_duels:
        bot.answer_callback_query(call.id, "❌ Дуэль не найдена или уже завершена!")
        return
    
    duel = active_duels[duel_id]
    
    # Проверка что это тот игрок
    if str(call.from_user.id) != duel["player2_id"]:
        bot.answer_callback_query(call.id, "❌ Это не ваша дуэль!")
        return
    
    # Проверка статуса
    if duel["status"] != "waiting":
        bot.answer_callback_query(call.id, "❌ Дуэль уже началась!")
        return
    
    # Списание ставки
    if duel["bet"] > 0:
        p1 = Player(duel["player1_id"])
        p2 = Player(duel["player2_id"])
        
        if p1.data["money"] < duel["bet"] or p2.data["money"] < duel["bet"]:
            bot.answer_callback_query(call.id, "❌ Недостаточно монет у одного из игроков!")
            return
        
        p1.data["money"] -= duel["bet"]
        p2.data["money"] -= duel["bet"]
        p1.save()
        p2.save()
    
    # Запуск дуэли
    duel_system.start_duel(duel_id)
    
    # Выполнение всех ходов
    while duel["status"] == "active":
        duel_system.execute_turn(duel_id)
        duel = active_duels[duel_id]
    
    # Отправка результата
    show_duel_result(call.message, duel_id)

def show_duel_result(message, duel_id):
    """Отображение результата дуэли"""
    duel = active_duels.get(duel_id)
    if not duel:
        return
    
    p1 = Player(duel["player1_id"])
    p2 = Player(duel["player2_id"])
    
    winner_id = duel.get("winner")
    winner_name = Player(winner_id).data["first_name"] if winner_id else "Ничья"
    
    result_text = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

<b>{p1.data['first_name']}</b> vs <b>{p2.data['first_name']}</b>

🏆 Победитель: <b>{winner_name}</b>
⚔ Ходов: {duel['turn_count']}
💰 Ставка: {duel['bet']} монет

<b>📊 Итоги боя:</b>
{p1.data['first_name']}: ❤ {duel['p1_hp']}/{duel['p1_max_hp']} HP
{p2.data['first_name']}: ❤ {duel['p2_hp']}/{duel['p2_max_hp']} HP

<b>📜 Лог боя:</b>
{chr(10).join(duel['battle_log'][-5:])}
"""
    
    # Награда победителю
    if winner_id and duel["bet"] > 0:
        winner = Player(winner_id)
        reward = duel["bet"] * 2
        result_text += f"\n💰 Победитель получает: <b>{reward} монет</b>"
    
    bot.send_message(message.chat.id, result_text)

def show_shop_category(call, category):
    """Показ категории магазина"""
    cat_items = {k: v for k, v in items.items() if v["type"] == category}
    
    if not cat_items:
        bot.answer_callback_query(call.id, "❌ В этой категории пока нет предметов")
        return
    
    shop_text = f"<b>🏪 {category.upper()}</b>\n\n"
    
    for item_key, item in sorted(cat_items.items(), key=lambda x: x[1]["price"]):
        rarity_icon = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
        shop_text += f"{rarity_icon} <b>{item['name']}</b>\n"
        shop_text += f"💰 Цена: {item['price']} | ⭐ Ур: {item.get('level_req', 1)}\n"
        
        if "damage" in item:
            shop_text += f"⚔ Урон: +{item['damage']}\n"
        if "defense" in item:
            shop_text += f"🛡 Защита: +{item['defense']}\n"
        if "heal" in item:
            shop_text += f"💊 Лечение: {item['heal']} HP\n"
        if "hp_bonus" in item:
            shop_text += f"❤ HP: +{item['hp_bonus']}\n"
        
        shop_text += f"📝 {item.get('description', '')}\n\n"
    
    bot.edit_message_text(
        shop_text[:4000],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_shop_menu(category)
    )

def show_limited_shop(call):
    """Показ лимитированных предметов"""
    if not limited_items:
        bot.answer_callback_query(call.id, "💎 Лимитированных предметов нет!")
        return
    
    limit_text = "<b>💎 ЛИМИТИРОВАННЫЕ ПРЕДМЕТЫ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, item in limited_items.items():
        if item["remaining"] > 0:
            progress = int(item["remaining"] / item["total"] * 10)
            bar = "█" * progress + "░" * (10 - progress)
            
            rarity_icon = "💎" if item.get("rarity") == "divine" else "🔥"
            limit_text += f"{rarity_icon} <b>{item['name']}</b>\n"
            limit_text += f"📦 [{bar}] {item['remaining']}/{item['total']}\n"
            limit_text += f"💰 Цена: <b>{item['price']} монет</b>\n"
            
            if "damage" in item:
                limit_text += f"⚔ Урон: <b>{item['damage']}</b>\n"
            if "defense" in item:
                limit_text += f"🛡 Защита: <b>{item['defense']}</b>\n"
            if "special" in item:
                limit_text += f"✨ Особое: <b>{item['special']}</b>\n"
            
            limit_text += f"📝 {item.get('description', '')}\n\n"
            
            markup.add(types.InlineKeyboardButton(
                f"Купить {item['name']} - {item['price']}💰",
                callback_data=f"buylimited_{item_key}"
            ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад в магазин", callback_data="shop_main"))
    
    bot.edit_message_text(
        limit_text[:4000],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

def handle_buy_item(call, item_key):
    """Покупка обычного предмета"""
    item = items.get(item_key)
    
    if not item:
        bot.answer_callback_query(call.id, "❌ Предмет не найден!")
        return
    
    player = Player(call.from_user.id)
    
    if player.data["level"] < item.get("level_req", 1):
        bot.answer_callback_query(
            call.id,
            f"❌ Нужен {item.get('level_req', 1)} уровень! Ваш: {player.data['level']}"
        )
        return
    
    if player.data["money"] < item["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    player.data["money"] -= item["price"]
    player.add_item(item_key)
    global_stats["total_items_sold"] = global_stats.get("total_items_sold", 0) + 1
    global_stats["total_money_spent"] = global_stats.get("total_money_spent", 0) + item["price"]
    safe_save_json(DATA_FILES['global_stats'], global_stats)
    
    bot.answer_callback_query(call.id, f"✅ Куплено: {item['name']}!")
    
    # Авто-экипировка если включена
    if player.data["settings"]["auto_equip"]:
        player.equip_item(item_key)
        bot.send_message(
            call.message.chat.id,
            f"✅ Вы приобрели и экипировали <b>{item['name']}</b>!"
        )
    else:
        bot.send_message(
            call.message.chat.id,
            f"✅ Вы приобрели <b>{item['name']}</b>!\n"
            f"💰 Потрачено: {item['price']} монет\n"
            f"🎒 Предмет добавлен в инвентарь"
        )

def handle_buy_limited(call, item_key):
    """Покупка лимитированного предмета"""
    item = limited_items.get(item_key)
    
    if not item or item["remaining"] <= 0:
        bot.answer_callback_query(call.id, "❌ Предмет закончился!")
        return
    
    player = Player(call.from_user.id)
    
    if player.data["money"] < item["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    player.data["money"] -= item["price"]
    player.add_item(item_key)
    item["remaining"] -= 1
    safe_save_json(DATA_FILES['limited_items'], limited_items)
    
    global_stats["total_money_spent"] = global_stats.get("total_money_spent", 0) + item["price"]
    safe_save_json(DATA_FILES['global_stats'], global_stats)
    
    bot.answer_callback_query(call.id, f"💎 Куплен легендарный предмет: {item['name']}!")
    
    bot.send_message(
        call.message.chat.id,
        f"💎 <b>ПОЗДРАВЛЯЕМ С ПОКУПКОЙ!</b>\n\n"
        f"Вы приобрели <b>{item['name']}</b>!\n"
        f"Осталось в наличии: <b>{item['remaining']}/{item['total']}</b>\n"
        f"💰 Потрачено: {item['price']} монет"
    )

def show_inventory(call):
    """Показ инвентаря"""
    player = Player(call.from_user.id)
    
    if not player.data["inventory"]:
        bot.answer_callback_query(call.id, "🎒 Инвентарь пуст!")
        return
    
    # Группировка предметов
    item_counts = {}
    for item_key in player.data["inventory"]:
        item_counts[item_key] = item_counts.get(item_key, 0) + 1
    
    inventory_text = "<b>🎒 ИНВЕНТАРЬ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for item_key, count in item_counts.items():
        item = items.get(item_key) or limited_items.get(item_key)
        if item:
            rarity_icon = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
            equipped = ""
            for slot, equipped_key in player.data["equipped"].items():
                if equipped_key == item_key:
                    equipped = " ✅"
                    break
            
            inventory_text += f"{rarity_icon} {item['name']} x{count}{equipped}\n"
            
            if item["type"] in ["weapon", "shield", "armor", "accessory", "boots"]:
                markup.add(types.InlineKeyboardButton(
                    f"Экип: {item['name'][:15]}",
                    callback_data=f"equip_{item_key}"
                ))
            elif item["type"] == "potion":
                markup.add(types.InlineKeyboardButton(
                    f"Исп: {item['name'][:15]}",
                    callback_data=f"use_{item_key}"
                ))
    
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="show_inventory"))
    markup.add(types.InlineKeyboardButton("❌ Закрыть", callback_data="close"))
    
    if len(inventory_text) > 4000:
        for i in range(0, len(inventory_text), 4000):
            bot.send_message(
                call.message.chat.id,
                inventory_text[i:i+4000],
                reply_markup=markup if i == 0 else None
            )
    else:
        bot.edit_message_text(
            inventory_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

def handle_equip_item(call, item_key):
    """Экипировка предмета"""
    player = Player(call.from_user.id)
    
    if player.equip_item(item_key):
        item = items.get(item_key) or limited_items.get(item_key)
        bot.answer_callback_query(call.id, f"✅ {item['name']} экипирован!")
    else:
        bot.answer_callback_query(call.id, "❌ Ошибка экипировки!")

def handle_use_potion(call, item_key):
    """Использование зелья"""
    player = Player(call.from_user.id)
    
    item = items.get(item_key) or limited_items.get(item_key)
    if not item or item["type"] != "potion":
        bot.answer_callback_query(call.id, "❌ Это не зелье!")
        return
    
    if player.data["hp"] >= player.data["max_hp"]:
        bot.answer_callback_query(call.id, "❌ У вас полное здоровье!")
        return
    
    heal = item.get("heal", 30)
    old_hp = player.data["hp"]
    player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + heal)
    actual_heal = player.data["hp"] - old_hp
    
    player.remove_item(item_key)
    player.data["items_used"] += 1
    player.save()
    
    bot.answer_callback_query(call.id, f"💊 +{actual_heal} HP!")
    
    bot.send_message(
        call.message.chat.id,
        f"💊 Использовано: <b>{item['name']}</b>\n"
        f"❤ Восстановлено: +{actual_heal} HP\n"
        f"Текущее здоровье: {player.data['hp']}/{player.data['max_hp']}"
    )

def show_stats(call):
    """Показ характеристик"""
    player = Player(call.from_user.id)
    stats = player.get_stats()
    
    stats_text = f"""
<b>📊 ХАРАКТЕРИСТИКИ</b>

<b>Базовые параметры:</b>
💪 Сила: {player.data['stats']['strength']}
🏃 Ловкость: {player.data['stats']['agility']}
❤ Живучесть: {player.data['stats']['vitality']}
🍀 Удача: {player.data['stats']['luck']}
⭐ Очки прокачки: {player.data['stats']['stat_points']}

<b>Боевые показатели:</b>
⚔ Урон: {stats['damage']}
🛡 Защита: {stats['defense']}
💥 Крит: {stats['crit_chance']}% (x{stats['crit_multiplier']})
🌀 Уклонение: {stats['dodge_chance']}%
💨 Скорость: {stats['speed']}
🩸 Вампиризм: {stats['lifesteal']}%
🔄 Отражение: {stats['damage_reflect']}%

<b>Бонусы экипировки:</b>
"""
    for slot, item_key in player.data["equipped"].items():
        if item_key:
            item = items.get(item_key) or limited_items.get(item_key)
            if item:
                bonuses = ", ".join([f"{k}: +{v}" for k, v in item.get("stats_bonus", {}).items() if k != "special"])
                stats_text += f"• {item['name']}: {bonuses}\n"
    
    markup = types.InlineKeyboardMarkup()
    if player.data['stats']['stat_points'] > 0:
        markup.add(types.InlineKeyboardButton("⬆ Прокачать характеристики", callback_data="upgrade_stats"))
    
    bot.edit_message_text(
        stats_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

def show_upgrade_menu(call):
    """Меню прокачки характеристик"""
    player = Player(call.from_user.id)
    
    if player.data['stats']['stat_points'] <= 0:
        bot.answer_callback_query(call.id, "❌ Нет очков прокачки! Повышайте уровень.")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💪 Сила +1", callback_data="upgrade_strength"),
        types.InlineKeyboardButton("🏃 Ловкость +1", callback_data="upgrade_agility"),
        types.InlineKeyboardButton("❤ Живучесть +1", callback_data="upgrade_vitality"),
        types.InlineKeyboardButton("🍀 Удача +1", callback_data="upgrade_luck")
    )
    
    stats = player.data['stats']
    
    upgrade_text = f"""
<b>⬆ ПРОКАЧКА ХАРАКТЕРИСТИК</b>

Доступно очков: <b>{stats['stat_points']}</b>

💪 Сила: {stats['strength']} (+2 к урону)
🏃 Ловкость: {stats['agility']} (+2 к уклонению и скорости)
❤ Живучесть: {stats['vitality']} (+1.5 к защите)
🍀 Удача: {stats['luck']} (+2% к криту)

Выберите характеристику для улучшения:
"""
    bot.edit_message_text(
        upgrade_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

def show_top(call, category):
    """Показ топа игроков"""
    if category == "level":
        sorted_players = sorted(users.items(), 
            key=lambda x: (x[1].get("level", 0), x[1].get("exp", 0)), reverse=True)[:10]
        title = "🏆 ТОП ПО УРОВНЮ"
        get_value = lambda d: f"Ур.{d.get('level', 1)}"
    elif category == "wins":
        sorted_players = sorted(users.items(), 
            key=lambda x: x[1].get("wins", 0), reverse=True)[:10]
        title = "⚔ ТОП ПО ПОБЕДАМ"
        get_value = lambda d: f"{d.get('wins', 0)} побед"
    elif category == "money":
        sorted_players = sorted(users.items(), 
            key=lambda x: x[1].get("money", 0), reverse=True)[:10]
        title = "💰 ТОП ПО БОГАТСТВУ"
        get_value = lambda d: f"{d.get('money', 0)}💰"
    elif category == "streak":
        sorted_players = sorted(users.items(), 
            key=lambda x: x[1].get("best_streak", 0), reverse=True)[:10]
        title = "🔥 ТОП ПО СЕРИИ ПОБЕД"
        get_value = lambda d: f"Серия: {d.get('best_streak', 0)}"
    
    top_text = f"<b>{title}</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, (uid, data) in enumerate(sorted_players):
        name = data.get('first_name', 'Игрок')
        value = get_value(data)
        top_text += f"{medals[i]} <b>{name}</b>: {value}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="close"))
    
    bot.edit_message_text(
        top_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

# ==================== ИНИЦИАЛИЗАЦИЯ И ЗАПУСК ====================
def initialize_bot():
    """Инициализация всех систем бота"""
    print("=" * 60)
    print(f"⚔ {BOT_NAME} - ИНИЦИАЛИЗАЦИЯ")
    print("=" * 60)
    
    # Загрузка данных
    load_all_data()
    
    # Инициализация предметов
    global items, limited_items
    items = init_items()
    limited_items = init_limited_items()
    
    # Статистика
    print(f"📦 Загружено предметов: {len(items)}")
    print(f"💎 Лимитированных: {len(limited_items)}")
    print(f"👥 Игроков в базе: {len(users)}")
    print(f"⚔ Всего дуэлей: {global_stats.get('total_duels', 0)}")
    print(f"💰 Потрачено монет: {global_stats.get('total_money_spent', 0)}")
    
    print("=" * 60)
    print("✅ Бот готов к работе!")
    print("=" * 60)

def run_bot():
    """Запуск бота с обработкой ошибок"""
    initialize_bot()
    
    while True:
        try:
            print("🔄 Запуск polling...")
            bot.polling(none_stop=True, interval=1, timeout=30)
        except KeyboardInterrupt:
            print("\n⏹ Бот остановлен пользователем")
            break
        except Exception as e:
            print(f"⚠ Критическая ошибка: {e}")
            print(f"🔄 Перезапуск через 10 секунд...")
            time.sleep(10)

if __name__ == "__main__":
    run_bot()
