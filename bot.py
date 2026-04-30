import telebot
from telebot import types
import json
import random
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict
import math
import re

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = '8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE'
ADMIN_ID = 5356400377
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ==================== КОНСТАНТЫ ====================
RARITY_COLORS = {
    "common": "⬜", "uncommon": "🟩", "rare": "🟦",
    "epic": "🟪", "legendary": "🟧", "mythic": "🟥",
    "divine": "💛", "apocalyptic": "🖤"
}

RARITY_NAMES = {
    "common": "Обычный", "uncommon": "Необычный", "rare": "Редкий",
    "epic": "Эпический", "legendary": "Легендарный", "mythic": "Мифический",
    "divine": "Божественный", "apocalyptic": "Апокалиптический"
}

ELEMENTS = {
    "🔥": {"name": "Огонь", "strong_against": "🌿", "weak_against": "🌊"},
    "❄": {"name": "Лёд", "strong_against": "🌊", "weak_against": "🔥"},
    "⚡": {"name": "Молния", "strong_against": "🌊", "weak_against": "🌿"},
    "🌊": {"name": "Вода", "strong_against": "🔥", "weak_against": "⚡"},
    "🌿": {"name": "Природа", "strong_against": "⚡", "weak_against": "🔥"},
    "🌑": {"name": "Тьма", "strong_against": "✨", "weak_against": "✨"},
    "✨": {"name": "Свет", "strong_against": "🌑", "weak_against": "🌑"},
    "💀": {"name": "Смерть", "strong_against": "🌿", "weak_against": "✨"}
}

DUEL_ACTIONS = {
    "light_attack": {"name": "⚡ Быстрый удар", "damage_mult": 0.7, "accuracy": 95, "crit_bonus": 5, "mana_cost": 0, "speed": 3},
    "heavy_attack": {"name": "💪 Тяжёлый удар", "damage_mult": 1.5, "accuracy": 70, "crit_bonus": 10, "mana_cost": 0, "speed": 1},
    "precise_strike": {"name": "🎯 Точный удар", "damage_mult": 1.0, "accuracy": 90, "crit_bonus": 20, "mana_cost": 0, "speed": 2},
    "defend": {"name": "🛡 Защита", "damage_mult": 0, "accuracy": 100, "defense_bonus": 50, "mana_cost": 0, "speed": 3},
    "counter_attack": {"name": "↩ Контратака", "damage_mult": 1.2, "accuracy": 75, "counter": True, "mana_cost": 5, "speed": 2},
    "fire_strike": {"name": "🔥 Огненный удар", "damage_mult": 1.4, "accuracy": 80, "element": "🔥", "burn_chance": 30, "mana_cost": 15, "speed": 2},
    "ice_shard": {"name": "❄ Ледяной шип", "damage_mult": 1.3, "accuracy": 85, "element": "❄", "freeze_chance": 20, "mana_cost": 15, "speed": 2},
    "lightning_bolt": {"name": "⚡ Разряд молнии", "damage_mult": 1.6, "accuracy": 75, "element": "⚡", "stun_chance": 15, "mana_cost": 20, "speed": 3},
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.5, "accuracy": 70, "element": "🌑", "poison_chance": 25, "mana_cost": 18, "speed": 2},
    "holy_smite": {"name": "✨ Святая кара", "damage_mult": 1.7, "accuracy": 80, "element": "✨", "heal_self": 0.2, "mana_cost": 25, "speed": 1},
    "death_touch": {"name": "💀 Прикосновение смерти", "damage_mult": 2.0, "accuracy": 60, "element": "💀", "curse_chance": 20, "mana_cost": 30, "speed": 1},
    "berserk": {"name": "💢 Берсерк", "damage_mult": 2.5, "accuracy": 50, "self_damage": 0.1, "mana_cost": 20, "speed": 2},
    "meditate": {"name": "🧘 Медитация", "damage_mult": 0, "accuracy": 100, "heal_self": 0.15, "mana_restore": 20, "mana_cost": 0, "speed": 1},
    "power_up": {"name": "⬆ Усиление", "damage_mult": 0, "accuracy": 100, "damage_buff": 30, "mana_cost": 15, "speed": 2},
    "weaken": {"name": "⬇ Ослабление", "damage_mult": 0.6, "accuracy": 85, "defense_debuff": 20, "mana_cost": 15, "speed": 2}
}

# ==================== ФАЙЛЫ ДАННЫХ ====================
DATA_FILES = {
    'users': 'users.json',
    'items': 'items.json',
    'limited': 'limited_items.json',
    'duels': 'active_duels.json',
    'clans': 'clans.json',
    'tournaments': 'tournaments.json',
    'market': 'market.json',
    'quests': 'quests.json',
    'events': 'events.json',
    'bans': 'bans.json'
}

def load_json(filename, default=None):
    if default is None:
        default = {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        save_json(filename, default)
        return default

def save_json(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving {filename}: {e}")

# ==================== ПРЕДМЕТЫ ====================
WEAPONS = {
    "rusty_sword": {
        "name": "🗡 Ржавый меч", "damage": (3, 7), "price": 50, "type": "weapon",
        "rarity": "common", "level_req": 1, "element": None,
        "description": "Старый ржавый меч",
        "actions_unlock": ["light_attack", "heavy_attack"]
    },
    "hunters_bow": {
        "name": "🏹 Лук охотника", "damage": (5, 10), "price": 150, "type": "weapon",
        "rarity": "common", "level_req": 3, "element": "🌿",
        "description": "Надёжный лук",
        "actions_unlock": ["light_attack", "precise_strike"]
    },
    "flame_blade": {
        "name": "🔥 Пламенный клинок", "damage": (8, 15), "price": 400, "type": "weapon",
        "rarity": "uncommon", "level_req": 7, "element": "🔥",
        "description": "Клинок, объятый пламенем",
        "actions_unlock": ["fire_strike", "light_attack", "heavy_attack"]
    },
    "frost_axe": {
        "name": "❄ Ледяной топор", "damage": (10, 18), "price": 700, "type": "weapon",
        "rarity": "uncommon", "level_req": 10, "element": "❄",
        "description": "Замораживает противников",
        "actions_unlock": ["ice_shard", "heavy_attack", "defend"]
    },
    "storm_staff": {
        "name": "⚡ Посох бурь", "damage": (12, 22), "price": 1200, "type": "weapon",
        "rarity": "rare", "level_req": 14, "element": "⚡",
        "description": "Призывает молнии",
        "actions_unlock": ["lightning_bolt", "light_attack", "meditate"]
    },
    "shadow_dagger": {
        "name": "🌑 Теневой кинжал", "damage": (18, 30), "price": 3500, "type": "weapon",
        "rarity": "epic", "level_req": 22, "element": "🌑",
        "description": "Атакует из тени",
        "actions_unlock": ["shadow_strike", "precise_strike", "counter_attack"]
    },
    "divine_spear": {
        "name": "✨ Божественное копьё", "damage": (22, 35), "price": 6000, "type": "weapon",
        "rarity": "legendary", "level_req": 28, "element": "✨",
        "description": "Оружие небесных воинов",
        "actions_unlock": ["holy_smite", "precise_strike", "power_up"]
    },
    "death_scythe": {
        "name": "💀 Коса смерти", "damage": (25, 45), "price": 10000, "type": "weapon",
        "rarity": "mythic", "level_req": 35, "element": "💀",
        "description": "Забирает души врагов",
        "actions_unlock": ["death_touch", "shadow_strike", "berserk", "weaken"]
    },
    "thunder_hammer": {
        "name": "⚡ Громовой молот", "damage": (20, 40), "price": 8000, "type": "weapon",
        "rarity": "legendary", "level_req": 32, "element": "⚡",
        "description": "Молот громовержца",
        "actions_unlock": ["lightning_bolt", "heavy_attack", "power_up"]
    },
    "phoenix_blade": {
        "name": "🦅 Клинок феникса", "damage": (30, 50), "price": 15000, "type": "weapon",
        "rarity": "mythic", "level_req": 40, "element": "🔥",
        "description": "Возрождается из пепла",
        "actions_unlock": ["fire_strike", "holy_smite", "meditate", "berserk"]
    }
}

SHIELDS = {
    "wooden_shield": {
        "name": "🛡 Деревянный щит", "defense": 5, "block_chance": 10,
        "price": 100, "type": "shield", "rarity": "common", "level_req": 1,
        "description": "Простой деревянный щит",
        "actions_unlock": ["defend"]
    },
    "iron_shield": {
        "name": "🛡 Железный щит", "defense": 10, "block_chance": 15,
        "price": 350, "type": "shield", "rarity": "uncommon", "level_req": 6,
        "description": "Прочный железный щит",
        "actions_unlock": ["defend", "counter_attack"]
    },
    "mirror_shield": {
        "name": "🪞 Зеркальный щит", "defense": 15, "block_chance": 20,
        "price": 900, "type": "shield", "rarity": "rare", "level_req": 12,
        "description": "Отражает магию",
        "actions_unlock": ["defend", "counter_attack", "meditate"]
    },
    "dragon_scale_shield": {
        "name": "🐉 Щит драконьей чешуи", "defense": 22, "block_chance": 25,
        "price": 2500, "type": "shield", "rarity": "epic", "level_req": 20,
        "description": "Чешуя древнего дракона",
        "actions_unlock": ["defend", "counter_attack", "power_up"]
    },
    "aegis_divine": {
        "name": "💫 Божественная эгида", "defense": 35, "block_chance": 35,
        "price": 8000, "type": "shield", "rarity": "legendary", "level_req": 30,
        "description": "Щит самой Афины",
        "actions_unlock": ["defend", "counter_attack", "holy_smite", "meditate"]
    }
}

ARMORS = {
    "leather_vest": {
        "name": "🧥 Кожаный жилет", "defense": 3, "hp_bonus": 15,
        "price": 80, "type": "armor", "rarity": "common", "level_req": 1,
        "description": "Лёгкая защита"
    },
    "chainmail": {
        "name": "⛓ Кольчуга", "defense": 8, "hp_bonus": 35,
        "price": 400, "type": "armor", "rarity": "uncommon", "level_req": 8,
        "description": "Надёжная кольчуга"
    },
    "plate_armor": {
        "name": "🛡 Латный доспех", "defense": 15, "hp_bonus": 60,
        "price": 1200, "type": "armor", "rarity": "rare", "level_req": 15,
        "description": "Тяжёлые латы"
    },
    "shadow_armor": {
        "name": "🌑 Теневая броня", "defense": 20, "hp_bonus": 80,
        "price": 3000, "type": "armor", "rarity": "epic", "level_req": 22,
        "description": "Скрывает в тенях"
    },
    "phoenix_armor": {
        "name": "🦅 Броня феникса", "defense": 30, "hp_bonus": 150,
        "price": 7000, "type": "armor", "rarity": "legendary", "level_req": 30,
        "description": "Возрождает из пепла",
        "special": "rebirth"
    },
    "titan_armor": {
        "name": "🏛 Броня титана", "defense": 45, "hp_bonus": 250,
        "price": 20000, "type": "armor", "rarity": "mythic", "level_req": 40,
        "description": "Сила древних титанов"
    }
}

ACCESSORIES = {
    "strength_ring": {
        "name": "💍 Кольцо силы", "price": 600, "type": "accessory",
        "rarity": "uncommon", "level_req": 5,
        "description": "+5 к минимальному урону",
        "bonus": {"min_damage": 5}
    },
    "crit_amulet": {
        "name": "📿 Амулет крита", "price": 1500, "type": "accessory",
        "rarity": "rare", "level_req": 15,
        "description": "+10% к шансу крита",
        "bonus": {"crit_chance": 10}
    },
    "lucky_charm": {
        "name": "🍀 Талисман удачи", "price": 2500, "type": "accessory",
        "rarity": "epic", "level_req": 20,
        "description": "+15% к удаче",
        "bonus": {"luck": 15}
    },
    "berserker_ring": {
        "name": "💢 Кольцо берсерка", "price": 4000, "type": "accessory",
        "rarity": "epic", "level_req": 25,
        "description": "+20% урона при низком HP",
        "bonus": {"berserk_damage": 20}
    },
    "philosophers_stone": {
        "name": "🧿 Философский камень", "price": 12000, "type": "accessory",
        "rarity": "legendary", "level_req": 35,
        "description": "Усиливает всё",
        "bonus": {"all_stats": 10}
    }
}

POTIONS = {
    "health_potion": {
        "name": "🧪 Зелье здоровья", "heal": 30, "price": 40,
        "type": "potion", "rarity": "common", "level_req": 1,
        "description": "Восстанавливает 30 HP"
    },
    "big_health_potion": {
        "name": "🧪 Большое зелье", "heal": 75, "price": 120,
        "type": "potion", "rarity": "uncommon", "level_req": 8,
        "description": "Восстанавливает 75 HP"
    },
    "elixir_of_life": {
        "name": "💊 Эликсир жизни", "heal": 150, "price": 350,
        "type": "potion", "rarity": "rare", "level_req": 15,
        "description": "Полное восстановление"
    },
    "mana_potion": {
        "name": "💎 Зелье маны", "mana_restore": 30, "price": 50,
        "type": "potion", "rarity": "common", "level_req": 5,
        "description": "Восстанавливает 30 маны"
    },
    "berserk_potion": {
        "name": "💢 Зелье ярости", "price": 200,
        "type": "potion", "rarity": "rare", "level_req": 12,
        "description": "+50% урона на 3 хода",
        "buff": {"damage_boost": 50, "duration": 3}
    },
    "invisibility_potion": {
        "name": "👻 Зелье невидимости", "price": 500,
        "type": "potion", "rarity": "epic", "level_req": 20,
        "description": "+50% уклонения на 2 хода",
        "buff": {"dodge_boost": 50, "duration": 2}
    }
}

BOOTS = {
    "leather_boots": {
        "name": "👢 Кожаные сапоги", "speed": 5, "price": 150,
        "type": "boots", "rarity": "common", "level_req": 1,
        "description": "+5 к скорости"
    },
    "wind_boots": {
        "name": "🌪 Сапоги ветра", "speed": 12, "price": 800,
        "type": "boots", "rarity": "rare", "level_req": 12,
        "description": "+12 к скорости, +5% уклонения"
    },
    "blink_boots": {
        "name": "✨ Сапоги телепортации", "speed": 20, "price": 3500,
        "type": "boots", "rarity": "epic", "level_req": 25,
        "description": "Шанс на двойной ход"
    },
    "hermes_boots": {
        "name": "👟 Сандалии Гермеса", "speed": 35, "price": 10000,
        "type": "boots", "rarity": "legendary", "level_req": 35,
        "description": "Всегда первый ход"
    }
}

LIMITED_ITEMS = {
    "thunderfury": {
        "name": "⚡ Ярость грома", "damage": (60, 100), "total": 3,
        "remaining": 3, "price": 50000, "type": "weapon",
        "rarity": "divine", "element": "⚡",
        "description": "Меч бога грома",
        "actions_unlock": ["lightning_bolt", "heavy_attack", "berserk", "power_up", "meditate"]
    },
    "apocalypse": {
        "name": "🌋 Апокалипсис", "damage": (80, 150), "total": 1,
        "remaining": 1, "price": 100000, "type": "weapon",
        "rarity": "apocalyptic", "element": "💀",
        "description": "Конец всего сущего",
        "actions_unlock": ["death_touch", "shadow_strike", "fire_strike", "berserk", "weaken", "power_up"]
    },
    "immortal_shield": {
        "name": "✨ Щит бессмертия", "defense": 100, "total": 2,
        "remaining": 2, "price": 75000, "type": "shield",
        "rarity": "divine",
        "description": "Делает владельца неуязвимым",
        "actions_unlock": ["defend", "counter_attack", "meditate", "power_up", "holy_smite"]
    },
    "cloak_of_infinity": {
        "name": "🌀 Плащ бесконечности", "defense": 60, "hp_bonus": 500,
        "total": 4, "remaining": 4, "price": 60000, "type": "armor",
        "rarity": "divine",
        "description": "Бесконечная защита космоса"
    }
}

ALL_ITEMS = {}
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(SHIELDS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(ACCESSORIES)
ALL_ITEMS.update(POTIONS)
ALL_ITEMS.update(BOOTS)

# Загрузка данных
items = load_json(DATA_FILES['items'], ALL_ITEMS)
limited_items = load_json(DATA_FILES['limited'], LIMITED_ITEMS)
users = load_json(DATA_FILES['users'], {})
active_duels = load_json(DATA_FILES['duels'], {})
clans = load_json(DATA_FILES['clans'], {})
tournaments = load_json(DATA_FILES['tournaments'], {})
market_listings = load_json(DATA_FILES['market'], {})
quests_data = load_json(DATA_FILES['quests'], {})
events_data = load_json(DATA_FILES['events'], {})
banned_users = load_json(DATA_FILES['bans'], {})

# ==================== ДОСТИЖЕНИЯ ====================
ACHIEVEMENTS_LIST = {
    "first_blood": {"name": "🩸 Первая кровь", "desc": "Выиграть первую дуэль", "reward_money": 200, "reward_exp": 50, "condition": lambda p: p.data["wins"] >= 1},
    "warrior": {"name": "⚔ Воин", "desc": "Выиграть 10 дуэлей", "reward_money": 500, "reward_exp": 150, "condition": lambda p: p.data["wins"] >= 10},
    "veteran": {"name": "🎖 Ветеран", "desc": "Выиграть 50 дуэлей", "reward_money": 2000, "reward_exp": 500, "condition": lambda p: p.data["wins"] >= 50},
    "legend": {"name": "👑 Легенда", "desc": "Выиграть 100 дуэлей", "reward_money": 5000, "reward_exp": 1000, "condition": lambda p: p.data["wins"] >= 100},
    "rich": {"name": "💰 Богач", "desc": "Накопить 10000 монет", "reward_money": 1000, "reward_exp": 200, "condition": lambda p: p.data["money"] >= 10000},
    "millionaire": {"name": "💎 Миллионер", "desc": "Накопить 100000 монет", "reward_money": 10000, "reward_exp": 2000, "condition": lambda p: p.data["money"] >= 100000},
    "collector": {"name": "🎒 Коллекционер", "desc": "Собрать 20 предметов", "reward_money": 1500, "reward_exp": 300, "condition": lambda p: len(p.data["inventory"]) >= 20},
    "dragon_slayer": {"name": "🐉 Убийца драконов", "desc": "Пройти данж дракона", "reward_money": 3000, "reward_exp": 600, "condition": lambda p: "dragon_slain" in p.data.get("achievements_data", {})},
    "perfectionist": {"name": "✨ Идеалист", "desc": "Выиграть без потери HP", "reward_money": 2000, "reward_exp": 400, "condition": lambda p: "perfect_win" in p.data.get("achievements_data", {})},
    "crit_master": {"name": "💥 Крит-мастер", "desc": "Нанести 50 крит. ударов", "reward_money": 1000, "reward_exp": 250, "condition": lambda p: p.data["critical_hits_landed"] >= 50}
}

# ==================== КВЕСТЫ ====================
DAILY_QUESTS_TEMPLATES = [
    {"name": "Дуэлянт", "desc": "Провести 3 дуэли", "type": "duels", "target": 3, "reward_money": 300, "reward_exp": 50},
    {"name": "Победитель", "desc": "Выиграть 2 дуэли", "type": "wins", "target": 2, "reward_money": 400, "reward_exp": 70},
    {"name": "Шопоголик", "desc": "Купить 2 предмета", "type": "purchases", "target": 2, "reward_money": 250, "reward_exp": 40},
    {"name": "Исследователь", "desc": "Пройти 2 данжа", "type": "dungeons", "target": 2, "reward_money": 500, "reward_exp": 100},
    {"name": "Критический успех", "desc": "Нанести 10 крит. ударов", "type": "crits", "target": 10, "reward_money": 350, "reward_exp": 60},
    {"name": "Тактик", "desc": "Использовать разные действия", "type": "actions", "target": 8, "reward_money": 450, "reward_exp": 80}
]

# ==================== КЛАСС ИГРОКА ====================
class Player:
    def __init__(self, user_id, username="Unknown", first_name="Player"):
        self.user_id = str(user_id)
        if self.user_id not in users:
            users[self.user_id] = {
                "username": username,
                "first_name": first_name,
                "money": 500,
                "level": 1,
                "exp": 0,
                "total_exp": 0,
                "hp": 100,
                "max_hp": 100,
                "mana": 50,
                "max_mana": 50,
                "stats": {"strength": 5, "agility": 5, "intelligence": 5, "vitality": 5, "luck": 5},
                "stat_points": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "win_streak": 0,
                "best_streak": 0,
                "total_duels": 0,
                "total_damage_dealt": 0,
                "total_damage_taken": 0,
                "critical_hits_landed": 0,
                "inventory": [],
                "equipment": {"weapon": None, "shield": None, "armor": None, "accessory": None, "boots": None},
                "last_daily": None,
                "last_dungeon": None,
                "last_work": None,
                "title": "Новичок",
                "titles_collected": ["Новичок"],
                "achievements": [],
                "achievements_data": {},
                "active_quests": {},
                "quests_date": None,
                "completed_quests": 0,
                "clan": None,
                "clan_role": None,
                "tournament_wins": 0,
                "pvp_rating": 1000,
                "registration_date": datetime.now().isoformat(),
                "settings": {"notifications": True, "duel_requests": True}
            }
            self.save()
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    def save(self):
        save_json(DATA_FILES['users'], users)
    
    def get_equipment_stats(self):
        stats = {
            "min_damage": 0, "max_damage": 0,
            "defense": 0, "hp_bonus": 0, "mana_bonus": 0,
            "speed": 0, "crit_chance": 5, "dodge_chance": 3,
            "block_chance": 0, "element": None,
            "actions": ["light_attack", "heavy_attack", "defend", "meditate"]
        }
        
        for slot, item_key in self.data["equipment"].items():
            if not item_key:
                continue
            item = items.get(item_key) or limited_items.get(item_key)
            if not item:
                continue
            
            if item["type"] == "weapon":
                if "damage" in item:
                    stats["min_damage"] += item["damage"][0]
                    stats["max_damage"] += item["damage"][1]
                if "element" in item and item["element"]:
                    stats["element"] = item["element"]
                if "actions_unlock" in item:
                    for action in item["actions_unlock"]:
                        if action not in stats["actions"]:
                            stats["actions"].append(action)
            
            elif item["type"] == "shield":
                stats["defense"] += item.get("defense", 0)
                stats["block_chance"] += item.get("block_chance", 0)
                if "actions_unlock" in item:
                    for action in item["actions_unlock"]:
                        if action not in stats["actions"]:
                            stats["actions"].append(action)
            
            elif item["type"] == "armor":
                stats["defense"] += item.get("defense", 0)
                stats["hp_bonus"] += item.get("hp_bonus", 0)
            
            elif item["type"] == "accessory":
                bonus = item.get("bonus", {})
                if "min_damage" in bonus:
                    stats["min_damage"] += bonus["min_damage"]
                    stats["max_damage"] += bonus["min_damage"] * 1.5
                if "crit_chance" in bonus:
                    stats["crit_chance"] += bonus["crit_chance"]
                if "all_stats" in bonus:
                    stats["min_damage"] += bonus["all_stats"]
                    stats["max_damage"] += bonus["all_stats"] * 1.5
                    stats["crit_chance"] += bonus["all_stats"] * 0.5
            
            elif item["type"] == "boots":
                stats["speed"] += item.get("speed", 0)
        
        stats["min_damage"] += self.data["stats"]["strength"] * 2
        stats["max_damage"] += self.data["stats"]["strength"] * 3
        stats["speed"] += self.data["stats"]["agility"]
        stats["crit_chance"] += self.data["stats"]["luck"] * 0.5
        stats["crit_chance"] = min(stats["crit_chance"], 80)
        stats["dodge_chance"] = min(stats["dodge_chance"], 50)
        stats["block_chance"] = min(stats["block_chance"], 60)
        
        return stats

# ==================== ПОШАГОВАЯ СИСТЕМА БОЯ ====================
class StepDuel:
    def __init__(self, player1_id, player2_id, bet=0, duel_type="normal"):
        self.p1_id = str(player1_id)
        self.p2_id = str(player2_id)
        self.bet = bet
        self.duel_type = duel_type
        self.turn = 0
        self.max_turns = 20
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        self.p1_stats = self.p1.get_equipment_stats()
        self.p2_stats = self.p2.get_equipment_stats()
        
        self.p1_hp = self.p1.data["max_hp"] + self.p1_stats["hp_bonus"]
        self.p2_hp = self.p2.data["max_hp"] + self.p2_stats["hp_bonus"]
        self.p1_max_hp = self.p1_hp
        self.p2_max_hp = self.p2_hp
        
        self.p1_mana = self.p1.data["max_mana"] + self.p1_stats["mana_bonus"]
        self.p2_mana = self.p2.data["max_mana"] + self.p2_stats["mana_bonus"]
        self.p1_max_mana = self.p1_mana
        self.p2_max_mana = self.p2_mana
        
        self.p1_buffs = []
        self.p2_buffs = []
        self.p1_debuffs = []
        self.p2_debuffs = []
        
        self.p1_actions_used = set()
        self.p2_actions_used = set()
        
        p1_speed = self.p1_stats["speed"] + random.randint(-5, 5)
        p2_speed = self.p2_stats["speed"] + random.randint(-5, 5)
        
        if p1_speed >= p2_speed:
            self.current_player = 1
            self.opponent = 2
        else:
            self.current_player = 2
            self.opponent = 1
        
        self.battle_log = []
        self.status = "active"
        self.winner = None
        self.last_actions = {1: None, 2: None}
        
        self.weather = random.choice(["clear", "rain", "storm", "fog", "eclipse"])
        self.arena = random.choice(["colosseum", "forest", "volcano", "void", "tundra"])
        
        active_duels[self.p1_id] = {"opponent": self.p2_id, "bet": bet, "type": duel_type, "state": self.to_dict(), "timestamp": datetime.now().isoformat()}
        save_json(DATA_FILES['duels'], active_duels)
    
    def to_dict(self):
        return {
            "turn": self.turn,
            "p1_hp": self.p1_hp, "p2_hp": self.p2_hp,
            "p1_mana": self.p1_mana, "p2_mana": self.p2_mana,
            "current_player": self.current_player,
            "battle_log": self.battle_log[-10:],
            "status": self.status
        }
    
    def get_available_actions(self, player_num):
        if player_num == 1:
            stats = self.p1_stats
            mana = self.p1_mana
        else:
            stats = self.p2_stats
            mana = self.p2_mana
        
        available = []
        for action_key, action_data in DUEL_ACTIONS.items():
            if action_key in stats["actions"]:
                if action_data.get("mana_cost", 0) <= mana:
                    available.append({"key": action_key, "data": action_data})
        
        return available
    
    def execute_action(self, player_num, action_key):
        if self.status != "active":
            return False
        
        if player_num != self.current_player:
            return False
        
        action_data = DUEL_ACTIONS.get(action_key)
        if not action_data:
            return False
        
        if action_data.get("mana_cost", 0) > (self.p1_mana if player_num == 1 else self.p2_mana):
            return False
        
        attacker = player_num
        defender = 2 if attacker == 1 else 1
        
        if attacker == 1:
            self.p1_mana -= action_data.get("mana_cost", 0)
            self.p1_actions_used.add(action_key)
        else:
            self.p2_mana -= action_data.get("mana_cost", 0)
            self.p2_actions_used.add(action_key)
        
        self.last_actions[attacker] = action_key
        self.turn += 1
        
        # Обработка баффов/дебаффов
        self._process_effects(attacker)
        self._process_effects(defender)
        
        # Выполнение действия
        damage = 0
        heal = 0
        effects_applied = []
        
        stats = self.p1_stats if attacker == 1 else self.p2_stats
        defender_stats = self.p2_stats if attacker == 1 else self.p1_stats
        
        if action_data.get("damage_mult", 0) > 0:
            # Расчёт урона
            min_dmg = stats["min_damage"]
            max_dmg = stats["max_damage"]
            base_damage = random.randint(int(min_dmg), int(max_dmg))
            
            # Модификатор действия
            base_damage *= action_data["damage_mult"]
            
            # Баффы/дебаффы
            buffs = self.p1_buffs if attacker == 1 else self.p2_buffs
            for buff in buffs:
                if buff["type"] == "damage_boost":
                    base_damage *= (1 + buff["value"] / 100)
            
            # Точность
            if random.random() * 100 > action_data.get("accuracy", 90):
                self.battle_log.append(f"❌ {self._get_name(attacker)} промахивается!")
                base_damage = 0
            else:
                # Критический удар
                crit_chance = stats["crit_chance"] + action_data.get("crit_bonus", 0)
                is_crit = random.random() * 100 < crit_chance
                if is_crit:
                    base_damage *= 2
                    if attacker == 1:
                        self.p1.data["critical_hits_landed"] += 1
                    else:
                        self.p2.data["critical_hits_landed"] += 1
                    self.battle_log.append(f"💥 <b>КРИТИЧЕСКИЙ УДАР!</b>")
                
                # Элементальный бонус
                if "element" in action_data and stats.get("element"):
                    element_data = ELEMENTS.get(action_data["element"])
                    if element_data and defender_stats.get("element"):
                        if defender_stats["element"] == element_data["strong_against"]:
                            base_damage *= 1.5
                            self.battle_log.append(f"💪 Сильно против {defender_stats['element']}!")
                        elif defender_stats["element"] == element_data["weak_against"]:
                            base_damage *= 0.7
                            self.battle_log.append(f"👎 Слабо против {defender_stats['element']}!")
                
                # Защита
                defense = defender_stats["defense"]
                reduction = defense / (defense + 100)
                base_damage *= (1 - reduction)
                
                # Блок
                if action_data.get("counter") and self.last_actions.get(defender) == "defend":
                    block_chance = 60
                else:
                    block_chance = defender_stats["block_chance"]
                
                if random.random() * 100 < block_chance:
                    base_damage *= 0.5
                    self.battle_log.append(f"🛡 {self._get_name(defender)} блокирует!")
                
                # Уклонение
                dodge = defender_stats["dodge_chance"]
                for buff in (self.p2_buffs if defender == 2 else self.p1_buffs):
                    if buff["type"] == "dodge_boost":
                        dodge += buff["value"]
                
                if random.random() * 100 < dodge:
                    self.battle_log.append(f"💨 {self._get_name(defender)} уклоняется!")
                    base_damage = 0
            
            damage = max(1, int(base_damage))
            
            # Применение эффектов
            if "burn_chance" in action_data and random.random() * 100 < action_data["burn_chance"]:
                effects_applied.append({"type": "burn", "damage": 10, "duration": 3})
                self.battle_log.append("🔥 Горение!")
            
            if "freeze_chance" in action_data and random.random() * 100 < action_data["freeze_chance"]:
                effects_applied.append({"type": "freeze", "duration": 2})
                self.battle_log.append("❄ Заморозка!")
            
            if "stun_chance" in action_data and random.random() * 100 < action_data["stun_chance"]:
                effects_applied.append({"type": "stun", "duration": 1})
                self.battle_log.append("⚡ Оглушение!")
            
            if "poison_chance" in action_data and random.random() * 100 < action_data["poison_chance"]:
                effects_applied.append({"type": "poison", "damage": 8, "duration": 4})
                self.battle_log.append("☠ Отравление!")
            
            if "curse_chance" in action_data and random.random() * 100 < action_data["curse_chance"]:
                effects_applied.append({"type": "curse", "damage_mult": 15, "duration": 3})
                self.battle_log.append("💀 Проклятие!")
            
            if "self_damage" in action_data:
                self_dmg = int(self.p1_max_hp * action_data["self_damage"]) if attacker == 1 else int(self.p2_max_hp * action_data["self_damage"])
                if attacker == 1:
                    self.p1_hp -= self_dmg
                else:
                    self.p2_hp -= self_dmg
                self.battle_log.append(f"💢 Урон себе: {self_dmg}")
            
            if "heal_self" in action_data:
                heal_pct = action_data["heal_self"]
                heal = int((self.p1_max_hp if attacker == 1 else self.p2_max_hp) * heal_pct)
                if attacker == 1:
                    self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
                else:
                    self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
                self.battle_log.append(f"💚 Исцеление: +{heal} HP")
        
        elif action_data.get("damage_mult", 0) == 0:
            if "heal_self" in action_data:
                heal_pct = action_data["heal_self"]
                heal = int((self.p1_max_hp if attacker == 1 else self.p2_max_hp) * heal_pct)
                if attacker == 1:
                    self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
                else:
                    self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
                self.battle_log.append(f"💚 Исцеление: +{heal} HP")
            
            if "mana_restore" in action_data:
                mana_restore = action_data["mana_restore"]
                if attacker == 1:
                    self.p1_mana = min(self.p1_max_mana, self.p1_mana + mana_restore)
                else:
                    self.p2_mana = min(self.p2_max_mana, self.p2_mana + mana_restore)
                self.battle_log.append(f"💎 Мана: +{mana_restore}")
            
            if "damage_buff" in action_data:
                if attacker == 1:
                    self.p1_buffs.append({"type": "damage_boost", "value": action_data["damage_buff"], "duration": 3})
                else:
                    self.p2_buffs.append({"type": "damage_boost", "value": action_data["damage_buff"], "duration": 3})
                self.battle_log.append(f"⬆ Усиление атаки!")
            
            if "defense_debuff" in action_data:
                if defender == 1:
                    self.p1_debuffs.append({"type": "defense_down", "value": action_data["defense_debuff"], "duration": 2})
                else:
                    self.p2_debuffs.append({"type": "defense_down", "value": action_data["defense_debuff"], "duration": 2})
                self.battle_log.append(f"⬇ Ослабление защиты!")
        
        # Применение урона
        if damage > 0:
            if defender == 1:
                self.p1_hp -= damage
                self.p1.data["total_damage_taken"] += damage
            else:
                self.p2_hp -= damage
                self.p2.data["total_damage_taken"] += damage
            
            if attacker == 1:
                self.p1.data["total_damage_dealt"] += damage
            else:
                self.p2.data["total_damage_dealt"] += damage
            
            self.battle_log.append(f"⚔ {self._get_name(attacker)} наносит <b>{damage}</b> урона!")
        
        # Применение эффектов к противнику
        for effect in effects_applied:
            if defender == 1:
                self.p1_debuffs.append(effect)
            else:
                self.p2_debuffs.append(effect)
        
        # Отображение HP
        self.battle_log.append(f"❤ {self._get_name(1)}: {self._hp_bar(1)} ({self.p1_hp}/{self.p1_max_hp})")
        self.battle_log.append(f"💎 Мана: {'█' * int(self.p1_mana/self.p1_max_mana*10)} ({self.p1_mana}/{self.p1_max_mana})")
        self.battle_log.append(f"❤ {self._get_name(2)}: {self._hp_bar(2)} ({self.p2_hp}/{self.p2_max_hp})")
        self.battle_log.append(f"💎 Мана: {'█' * int(self.p2_mana/self.p2_max_mana*10)} ({self.p2_mana}/{self.p2_max_mana})")
        
        # Проверка на смерть
        if self.p1_hp <= 0:
            self.status = "finished"
            self.winner = 2
            self.battle_log.append(f"\n💀 <b>{self._get_name(1)} повержен!</b>")
            self.battle_log.append(f"🏆 <b>ПОБЕДИТЕЛЬ: {self._get_name(2)}!</b>")
        elif self.p2_hp <= 0:
            self.status = "finished"
            self.winner = 1
            self.battle_log.append(f"\n💀 <b>{self._get_name(2)} повержен!</b>")
            self.battle_log.append(f"🏆 <b>ПОБЕДИТЕЛЬ: {self._get_name(1)}!</b>")
        elif self.turn >= self.max_turns:
            self.status = "finished"
            self.winner = 0
            self.battle_log.append(f"\n⏰ <b>Время вышло! Ничья!</b>")
        else:
            # Смена хода
            self.current_player, self.opponent = self.opponent, self.current_player
            self.battle_log.append(f"\n➡ Ход переходит к <b>{self._get_name(self.current_player)}</b>")
        
        self.save_state()
        return True
    
    def _process_effects(self, player_num):
        debuffs = self.p1_debuffs if player_num == 1 else self.p2_debuffs
        buffs = self.p1_buffs if player_num == 1 else self.p2_buffs
        hp = self.p1_hp if player_num == 1 else self.p2_hp
        max_hp = self.p1_max_hp if player_num == 1 else self.p2_max_hp
        
        for effect in debuffs[:]:
            if "damage" in effect:
                hp -= effect["damage"]
                self.battle_log.append(f"💔 {self._get_name(player_num)} получает {effect['damage']} урона от эффекта")
            
            effect["duration"] -= 1
            if effect["duration"] <= 0:
                debuffs.remove(effect)
                self.battle_log.append(f"✨ Эффект спадает с {self._get_name(player_num)}")
        
        for buff in buffs[:]:
            buff["duration"] -= 1
            if buff["duration"] <= 0:
                buffs.remove(buff)
        
        if player_num == 1:
            self.p1_hp = max(0, min(max_hp, hp))
        else:
            self.p2_hp = max(0, min(max_hp, hp))
    
    def _hp_bar(self, player_num):
        hp = self.p1_hp if player_num == 1 else self.p2_hp
        max_hp = self.p1_max_hp if player_num == 1 else self.p2_max_hp
        pct = hp / max_hp * 10
        filled = int(pct)
        color = "🟢" if pct > 6 else "🟡" if pct > 3 else "🔴"
        return f"{'█' * filled}{'░' * (10 - filled)} {color}"
    
    def _get_name(self, player_num):
        if player_num == 1:
            return self.p1.data["first_name"]
        return self.p2.data["first_name"]
    
    def save_state(self):
        active_duels[self.p1_id] = {"opponent": self.p2_id, "bet": self.bet, "type": self.duel_type, "state": self.to_dict(), "timestamp": datetime.now().isoformat()}
        active_duels[self.p2_id] = {"opponent": self.p1_id, "bet": self.bet, "type": self.duel_type, "state": self.to_dict(), "timestamp": datetime.now().isoformat()}
        save_json(DATA_FILES['duels'], active_duels)
    
    def finish(self):
        self.p1.save()
        self.p2.save()
        if self.p1_id in active_duels:
            del active_duels[self.p1_id]
        if self.p2_id in active_duels:
            del active_duels[self.p2_id]
        save_json(DATA_FILES['duels'], active_duels)

# ==================== ГЛАВНОЕ МЕНЮ ====================
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("⚔️ Дуэли"),
        types.KeyboardButton("👤 Герой"),
        types.KeyboardButton("🏪 Торговля"),
        types.KeyboardButton("🌍 Мир")
    )
    return markup

def get_duel_submenu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("⚡ Быстрая дуэль"),
        types.KeyboardButton("👥 PvP дуэль"),
        types.KeyboardButton("🏆 Рейтинговая"),
        types.KeyboardButton("💀 Хардкор"),
        types.KeyboardButton("🎯 Пошаговая PvP"),
        types.KeyboardButton("◀️ Назад")
    )
    return markup

def get_hero_submenu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📊 Статистика"),
        types.KeyboardButton("🎒 Инвентарь"),
        types.KeyboardButton("⚡ Характеристики"),
        types.KeyboardButton("🏅 Достижения"),
        types.KeyboardButton("📜 Квесты"),
        types.KeyboardButton("◀️ Назад")
    )
    return markup

def get_trade_submenu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 Магазин"),
        types.KeyboardButton("💎 Лимит. предметы"),
        types.KeyboardButton("🎁 Ежедневный"),
        types.KeyboardButton("💱 Обмен"),
        types.KeyboardButton("🏪 Рынок"),
        types.KeyboardButton("◀️ Назад")
    )
    return markup

def get_world_submenu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🏰 Подземелья"),
        types.KeyboardButton("🛡 Кланы"),
        types.KeyboardButton("🏟 Турниры"),
        types.KeyboardButton("🌍 События"),
        types.KeyboardButton("📊 Рейтинг"),
        types.KeyboardButton("◀️ Назад")
    )
    return markup

# ==================== ОБРАБОТЧИКИ КОМАНД ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if str(user_id) in banned_users:
        ban = banned_users[str(user_id)]
        bot.send_message(message.chat.id, f"⛔ Забанены!\nПричина: {ban.get('reason')}\nДата: {ban.get('date')}")
        return
    
    username = message.from_user.username or f"user_{user_id}"
    first_name = message.from_user.first_name or "Игрок"
    player = Player(user_id, username, first_name)
    
    # Проверка достижений при входе
    check_achievements(player)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v5.0 - ПОЛНАЯ ВЕРСИЯ ⚔️</b>

Привет, <b>{first_name}</b>!

🎯 <b>ПОШАГОВАЯ БОЕВАЯ СИСТЕМА:</b>
• Выбирай действия каждый ход
• 15+ боевых приёмов
• Элементы и статус-эффекты
• Баффы/дебаффы
• Стратегические решения!

💰 Баланс: <b>500 монет</b>
⭐ Уровень: <b>1</b>

<b>Новые системы:</b>
• Пошаговые PvP дуэли
• Клановая система
• Турниры
• Рынок игроков
• Ежедневные квесты
• Достижения
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "◀️ Назад")
def back_handler(message):
    bot.send_message(message.chat.id, "🔙 Главное меню", reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_menu(message):
    bot.send_message(message.chat.id, "<b>⚔️ ДУЭЛИ</b>\n\nВыберите тип дуэли:", reply_markup=get_duel_submenu())

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_menu(message):
    bot.send_message(message.chat.id, "<b>👤 ГЕРОЙ</b>", reply_markup=get_hero_submenu())

@bot.message_handler(func=lambda m: m.text == "🏪 Торговля")
def trade_menu(message):
    bot.send_message(message.chat.id, "<b>🏪 ТОРГОВЛЯ</b>", reply_markup=get_trade_submenu())

@bot.message_handler(func=lambda m: m.text == "🌍 Мир")
def world_menu(message):
    bot.send_message(message.chat.id, "<b>🌍 МИР</b>", reply_markup=get_world_submenu())

# ==================== ПОШАГОВАЯ ДУЭЛЬ ====================
@bot.message_handler(func=lambda m: m.text == "🎯 Пошаговая PvP")
def step_duel_handler(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, """
<b>🎯 ПОШАГОВАЯ PvP ДУЭЛЬ</b>

Для начала:
1. Ответьте на сообщение соперника
2. Укажите ставку (по умолчанию 100💰)

Пример: /stepduel 500

<b>В бою доступны:</b>
• 15+ уникальных действий
• Элементальные атаки
• Баффы и дебаффы
• Стратегическая система

Каждый ход вы выбираете действие из меню!
""")
        return
    
    user_id = message.from_user.id
    opponent_id = message.reply_to_message.from_user.id
    
    if user_id == opponent_id:
        bot.send_message(message.chat.id, "❌ Нельзя играть с собой!")
        return
    
    try:
        parts = message.text.split()
        bet = int(parts[1]) if len(parts) > 1 else 100
        bet = max(50, min(10000, bet))
    except:
        bet = 100
    
    player = Player(user_id)
    opponent = Player(opponent_id)
    
    if player.data["money"] < bet or opponent.data["money"] < bet:
        bot.send_message(message.chat.id, "❌ Недостаточно монет у одного из игроков!")
        return
    
    # Создание дуэли
    duel = StepDuel(user_id, opponent_id, bet, "step")
    
    # Снятие ставки
    player.data["money"] -= bet
    opponent.data["money"] -= bet
    player.save()
    opponent.save()
    
    # Отправка интерфейса первому игроку
    send_duel_interface(message.chat.id, duel)

def send_duel_interface(chat_id, duel):
    current = duel.current_player
    available = duel.get_available_actions(current)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    for action in available:
        btn_text = f"{action['data']['name']} ({action['data'].get('mana_cost', 0)}💎)"
        buttons.append(types.InlineKeyboardButton(
            btn_text,
            callback_data=f"duelaction_{action['key']}_{current}"
        ))
    
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data=f"duelaction_surrender_{current}"))
    
    battle_text = f"""
<b>⚔ ПОШАГОВАЯ ДУЭЛЬ</b>
Ход: <b>#{duel.turn + 1}</b> | 🌤 {duel.weather} | 🏟 {duel.arena}

<b>Ходит: {duel._get_name(current)}</b>

{chr(10).join(duel.battle_log[-8:] if duel.battle_log else ['Бой начинается!'])}

Выберите действие:
"""
    
    bot.send_message(chat_id, battle_text[:4000], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duelaction_"))
def handle_duel_action(call):
    user_id = str(call.from_user.id)
    parts = call.data.split("_")
    action_key = parts[1]
    player_num = int(parts[2])
    
    # Поиск активной дуэли
    if user_id not in active_duels:
        bot.answer_callback_query(call.id, "❌ Нет активной дуэли!")
        return
    
    duel_data = active_duels[user_id]
    opponent_id = duel_data["opponent"]
    
    # Восстановление дуэли
    duel = StepDuel(user_id, opponent_id, duel_data["bet"], duel_data["type"])
    duel.turn = duel_data["state"]["turn"]
    duel.p1_hp = duel_data["state"]["p1_hp"]
    duel.p2_hp = duel_data["state"]["p2_hp"]
    duel.p1_mana = duel_data["state"]["p1_mana"]
    duel.p2_mana = duel_data["state"]["p2_mana"]
    duel.current_player = duel_data["state"]["current_player"]
    duel.battle_log = duel_data["state"]["battle_log"]
    
    if action_key == "surrender":
        duel.status = "finished"
        duel.winner = 2 if player_num == 1 else 1
        duel.battle_log.append(f"🏳 {duel._get_name(player_num)} сдаётся!")
    else:
        if player_num != duel.current_player:
            bot.answer_callback_query(call.id, "❌ Сейчас не ваш ход!")
            return
        
        success = duel.execute_action(player_num, action_key)
        if not success:
            bot.answer_callback_query(call.id, "❌ Недостаточно маны или действие недоступно!")
            return
    
    # Удаление предыдущего сообщения
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    if duel.status == "finished":
        finish_duel(call.message.chat.id, duel, call.from_user)
    else:
        # Отправка интерфейса следующему игроку
        next_player_id = opponent_id if duel.current_player == 2 else user_id
        try:
            bot.send_message(int(next_player_id), 
                f"⚔ Ваш ход в дуэли против {duel._get_name(duel.opponent)}!")
        except:
            pass
        
        bot.answer_callback_query(call.id, "✅ Действие выполнено!")

def finish_duel(chat_id, duel, caller):
    winner_id = str(duel.p1_id) if duel.winner == 1 else str(duel.p2_id) if duel.winner == 2 else None
    
    if winner_id:
        winner = Player(winner_id)
        loser_id = duel.p2_id if winner_id == duel.p1_id else duel.p1_id
        loser = Player(loser_id)
        
        winner.data["money"] += duel.bet * 2
        winner.data["wins"] += 1
        winner.data["win_streak"] += 1
        winner.data["total_duels"] += 1
        
        if winner.data["win_streak"] > winner.data["best_streak"]:
            winner.data["best_streak"] = winner.data["win_streak"]
        
        exp_gain = duel.bet // 2 + duel.turn * 10
        winner.data["exp"] += exp_gain
        winner.data["total_exp"] += exp_gain
        
        loser.data["losses"] += 1
        loser.data["win_streak"] = 0
        loser.data["total_duels"] += 1
        loser.data["exp"] += exp_gain // 2
        loser.data["total_exp"] += exp_gain // 2
        
        check_level_up(winner)
        check_level_up(loser)
        check_achievements(winner)
        check_achievements(loser)
        
        winner.save()
        loser.save()
        
        result_text = f"""
<b>🏆 ДУЭЛЬ ЗАВЕРШЕНА!</b>

<b>Победитель: {winner.data['first_name']}</b>
💰 Награда: +{duel.bet * 2} монет
✨ Опыт: +{exp_gain}

{chr(10).join(duel.battle_log[-10:])}

Длительность: {duel.turn} ходов
"""
    else:
        p1 = Player(duel.p1_id)
        p2 = Player(duel.p2_id)
        p1.data["money"] += duel.bet
        p2.data["money"] += duel.bet
        p1.data["draws"] += 1
        p2.data["draws"] += 1
        p1.save()
        p2.save()
        
        result_text = f"""
<b>🤝 НИЧЬЯ!</b>

Ставки возвращены.
{chr(10).join(duel.battle_log[-10:])}
"""
    
    duel.finish()
    bot.send_message(chat_id, result_text[:4000], reply_markup=get_main_menu())

# ==================== БЫСТРАЯ ДУЭЛЬ (УЛУЧШЕННАЯ) ====================
@bot.message_handler(func=lambda m: m.text == "⚡ Быстрая дуэль")
def quick_duel_handler(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("50💰", callback_data="qduel_50"),
        types.InlineKeyboardButton("100💰", callback_data="qduel_100"),
        types.InlineKeyboardButton("200💰", callback_data="qduel_200"),
        types.InlineKeyboardButton("500💰", callback_data="qduel_500"),
        types.InlineKeyboardButton("1000💰", callback_data="qduel_1000"),
        types.InlineKeyboardButton("Отмена", callback_data="cancel_duel")
    )
    
    bot.send_message(message.chat.id,
        f"<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n\nВыберите ставку:\n💰 Баланс: <b>{player.data['money']}</b>",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def quick_duel_execute(call):
    user_id = call.from_user.id
    bet = int(call.data.split("_")[1])
    player = Player(user_id)
    
    if player.data["money"] < bet:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    player.data["money"] -= bet
    player.save()
    
    # Создание бота
    bot_level = random.randint(max(1, player.data["level"] - 5), player.data["level"] + 5)
    bot_id = f"bot_{random.randint(10000,99999)}"
    
    # Экипировка бота
    bot_equip = {}
    weapon_keys = [k for k, v in WEAPONS.items() if v.get("level_req", 1) <= bot_level]
    shield_keys = [k for k, v in SHIELDS.items() if v.get("level_req", 1) <= bot_level]
    armor_keys = [k for k, v in ARMORS.items() if v.get("level_req", 1) <= bot_level]
    
    if weapon_keys and random.random() < 0.8:
        bot_equip["weapon"] = random.choice(weapon_keys)
    if shield_keys and random.random() < 0.5:
        bot_equip["shield"] = random.choice(shield_keys)
    if armor_keys and random.random() < 0.6:
        bot_equip["armor"] = random.choice(armor_keys)
    
    users[bot_id] = {
        "username": f"Bot_{bot_level}",
        "first_name": f"⚔ Бот Lv.{bot_level}",
        "money": 1000,
        "level": bot_level,
        "exp": 0,
        "total_exp": bot_level * 100,
        "hp": 100 + bot_level * 10,
        "max_hp": 100 + bot_level * 10,
        "mana": 50 + bot_level * 5,
        "max_mana": 50 + bot_level * 5,
        "stats": {"strength": 5 + bot_level, "agility": 5 + bot_level//2, "intelligence": 5 + bot_level//3, "vitality": 5 + bot_level//2, "luck": 3 + bot_level//4},
        "stat_points": 0,
        "wins": 0, "losses": 0, "draws": 0,
        "win_streak": 0, "best_streak": 0,
        "total_duels": 0,
        "total_damage_dealt": 0, "total_damage_taken": 0,
        "critical_hits_landed": 0,
        "inventory": [],
        "equipment": bot_equip,
        "last_daily": None, "last_dungeon": None, "last_work": None,
        "title": "Бот",
        "titles_collected": ["Бот"],
        "achievements": [], "achievements_data": {},
        "active_quests": {}, "quests_date": None,
        "completed_quests": 0,
        "clan": None, "clan_role": None,
        "tournament_wins": 0,
        "pvp_rating": 1000 + bot_level * 10,
        "registration_date": datetime.now().isoformat(),
        "settings": {}
    }
    
    # Симуляция боя
    p1_stats = player.get_equipment_stats()
    bot_player = Player(bot_id)
    p2_stats = bot_player.get_equipment_stats()
    
    p1_hp = player.data["max_hp"] + p1_stats["hp_bonus"]
    p2_hp = bot_player.data["max_hp"] + p2_stats["hp_bonus"]
    p1_max_hp = p1_hp
    p2_max_hp = p2_hp
    
    battle_log = [f"⚔ <b>Быстрая дуэль: {player.data['first_name']} vs Бот Lv.{bot_level}</b>"]
    
    for turn in range(1, 21):
        # Ход игрока
        available = [k for k in p1_stats["actions"] if k in DUEL_ACTIONS]
        if not available:
            available = ["light_attack"]
        action = random.choice(available)
        
        action_data = DUEL_ACTIONS[action]
        dmg = random.randint(int(p1_stats["min_damage"]), int(p1_stats["max_damage"]))
        dmg *= action_data.get("damage_mult", 1.0)
        
        if random.random() * 100 < action_data.get("accuracy", 90):
            if random.random() * 100 < p1_stats["crit_chance"]:
                dmg *= 2
                battle_log.append(f"💥 КРИТ! {dmg:.0f} урона")
            p2_hp -= int(dmg)
            battle_log.append(f"⚔ {player.data['first_name']} использует {action_data['name']}: -{int(dmg)} HP")
        else:
            battle_log.append(f"❌ Промах!")
        
        if p2_hp <= 0:
            break
        
        # Ход бота
        bot_available = [k for k in p2_stats["actions"] if k in DUEL_ACTIONS]
        if not bot_available:
            bot_available = ["light_attack"]
        bot_action = random.choice(bot_available)
        bot_action_data = DUEL_ACTIONS[bot_action]
        
        bot_dmg = random.randint(int(p2_stats["min_damage"]), int(p2_stats["max_damage"]))
        bot_dmg *= bot_action_data.get("damage_mult", 1.0)
        
        if random.random() * 100 < bot_action_data.get("accuracy", 90):
            p1_hp -= int(bot_dmg)
            battle_log.append(f"⚔ Бот использует {bot_action_data['name']}: -{int(bot_dmg)} HP")
        else:
            battle_log.append(f"❌ Бот промахивается!")
        
        if p1_hp <= 0:
            break
    
    # Определение победителя
    if p1_hp > 0 and p2_hp <= 0:
        winner_id = user_id
        player.data["money"] += bet * 2
        player.data["wins"] += 1
        player.data["win_streak"] += 1
        exp_gain = bet // 2
        result_text = f"🏆 <b>ПОБЕДА!</b>\n\n"
    elif p2_hp > 0 and p1_hp <= 0:
        winner_id = bot_id
        player.data["losses"] += 1
        player.data["win_streak"] = 0
        exp_gain = bet // 4
        result_text = f"💀 <b>ПОРАЖЕНИЕ</b>\n\n"
    else:
        winner_id = None
        player.data["money"] += bet
        player.data["draws"] += 1
        exp_gain = bet // 3
        result_text = f"🤝 <b>НИЧЬЯ</b>\n\n"
    
    player.data["exp"] += exp_gain
    player.data["total_exp"] += exp_gain
    player.data["total_duels"] += 1
    
    if player.data["win_streak"] > player.data["best_streak"]:
        player.data["best_streak"] = player.data["win_streak"]
    
    old_level = player.data["level"]
    check_level_up(player)
    check_achievements(player)
    player.save()
    
    if bot_id in users:
        del users[bot_id]
    save_json(DATA_FILES['users'], users)
    
    result_text += f"💰 Ставка: {bet}\n"
    result_text += f"✨ Опыт: +{exp_gain}\n"
    result_text += "\n".join(battle_log[-8:])
    
    if player.data["level"] > old_level:
        result_text += f"\n\n🎉 <b>НОВЫЙ УРОВЕНЬ: {player.data['level']}!</b>"
    
    bot.edit_message_text(result_text[:4000], call.message.chat.id, call.message.message_id)

# ==================== МАГАЗИН И ТОРГОВЛЯ ====================
@bot.message_handler(func=lambda m: m.text == "🛒 Магазин")
def shop_handler(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚔ Оружие", callback_data="shopcat_weapon"),
        types.InlineKeyboardButton("🛡 Щиты", callback_data="shopcat_shield"),
        types.InlineKeyboardButton("🧥 Броня", callback_data="shopcat_armor"),
        types.InlineKeyboardButton("📿 Аксессуары", callback_data="shopcat_accessory"),
        types.InlineKeyboardButton("🧪 Зелья", callback_data="shopcat_potion"),
        types.InlineKeyboardButton("👢 Обувь", callback_data="shopcat_boots")
    )
    
    bot.send_message(message.chat.id,
        f"<b>🛒 МАГАЗИН</b>\n\n💰 Баланс: <b>{player.data['money']}💰</b>\n⭐ Уровень: <b>{player.data['level']}</b>\n\nВыберите категорию:",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shopcat_"))
def shop_category_handler(call):
    category = call.data.split("_")[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    cat_names = {"weapon": "⚔ Оружие", "shield": "🛡 Щиты", "armor": "🧥 Броня", 
                 "accessory": "📿 Аксессуары", "potion": "🧪 Зелья", "boots": "👢 Обувь"}
    
    cat_items = {k: v for k, v in items.items() if v["type"] == category}
    
    shop_text = f"<b>{cat_names[category]}</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, item in sorted(cat_items.items(), key=lambda x: x[1]["price"]):
        if player.data["level"] < item.get("level_req", 1):
            continue
        
        rarity = RARITY_COLORS.get(item["rarity"], "⬜")
        shop_text += f"{rarity} <b>{item['name']}</b> - {item['price']}💰\n"
        shop_text += f"   📝 {item['description']}\n"
        shop_text += f"   📊 Требуется: Ур.{item.get('level_req', 1)}\n\n"
        
        if player.data["money"] >= item["price"]:
            markup.add(types.InlineKeyboardButton(
                f"Купить: {item['name']}",
                callback_data=f"buy_{item_key}"
            ))
    
    markup.add(types.InlineKeyboardButton("◀️ Назад к категориям", callback_data="back_to_shop"))
    
    if not markup.keyboard:
        shop_text += "Нет доступных предметов\n"
    
    bot.edit_message_text(shop_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_shop")
def back_to_shop_handler(call):
    shop_handler(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_item_handler(call):
    item_key = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(item_key) or limited_items.get(item_key)
    if not item:
        bot.answer_callback_query(call.id, "❌ Предмет не найден!")
        return
    
    if player.data["level"] < item.get("level_req", 1):
        bot.answer_callback_query(call.id, f"❌ Нужен {item.get('level_req', 1)} уровень!")
        return
    
    if player.data["money"] < item["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    if item_key in limited_items:
        if limited_items[item_key]["remaining"] <= 0:
            bot.answer_callback_query(call.id, "❌ Предмет закончился!")
            return
        limited_items[item_key]["remaining"] -= 1
        save_json(DATA_FILES['limited'], limited_items)
    
    player.data["money"] -= item["price"]
    player.data["inventory"].append(item_key)
    player.save()
    
    # Обновление квестов
    update_quest_progress(player, "purchases", 1)
    
    bot.answer_callback_query(call.id, f"✅ Куплено: {item['name']}!")
    bot.send_message(call.message.chat.id, f"✅ Вы приобрели <b>{item['name']}</b> за {item['price']}💰!")

# ==================== ЕЖЕДНЕВНЫЙ БОНУС ====================
@bot.message_handler(func=lambda m: m.text == "🎁 Ежедневный")
def daily_handler(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player.data["last_daily"] == today:
        bot.send_message(message.chat.id, "🎁 Вы уже получили бонус сегодня! Приходите завтра.")
        return
    
    bonus = random.randint(100, 500) + player.data["level"] * 10
    exp_bonus = random.randint(50, 200) + player.data["level"] * 5
    got_item = None
    
    if random.random() < 0.15:
        common = [k for k, v in items.items() if v.get("rarity") == "common"]
        if common:
            got_item = random.choice(common)
            player.data["inventory"].append(got_item)
    
    player.data["money"] += bonus
    player.data["exp"] += exp_bonus
    player.data["total_exp"] += exp_bonus
    player.data["last_daily"] = today
    
    old_level = player.data["level"]
    check_level_up(player)
    player.save()
    
    result = f"<b>🎁 ЕЖЕДНЕВНЫЙ БОНУС</b>\n\n💰 Монет: +{bonus}\n✨ Опыта: +{exp_bonus}"
    if got_item:
        result += f"\n🎒 Предмет: <b>{items[got_item]['name']}</b>"
    if player.data["level"] > old_level:
        result += f"\n🎉 <b>НОВЫЙ УРОВЕНЬ: {player.data['level']}!</b>"
    
    bot.send_message(message.chat.id, result)

# ==================== ДОСТИЖЕНИЯ И КВЕСТЫ ====================
def check_achievements(player):
    for ach_id, ach_data in ACHIEVEMENTS_LIST.items():
        if ach_id not in player.data["achievements"] and ach_data["condition"](player):
            player.data["achievements"].append(ach_id)
            player.data["money"] += ach_data["reward_money"]
            player.data["exp"] += ach_data["reward_exp"]
            player.data["total_exp"] += ach_data["reward_exp"]
            # Здесь можно отправить уведомление

def update_quest_progress(player, quest_type, amount=1):
    if not player.data["active_quests"]:
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player.data.get("quests_date") != today:
        return
    
    for quest_id, quest in player.data["active_quests"].items():
        if quest.get("type") == quest_type:
            quest["progress"] = quest.get("progress", 0) + amount
            
            if quest["progress"] >= quest["target"] and not quest.get("completed"):
                quest["completed"] = True
                player.data["money"] += quest["reward_money"]
                player.data["exp"] += quest["reward_exp"]
                player.data["total_exp"] += quest["reward_exp"]
                player.data["completed_quests"] += 1
    
    player.save()

@bot.message_handler(func=lambda m: m.text == "📜 Квесты")
def quests_handler(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player.data.get("quests_date") != today:
        player.data["active_quests"] = {}
        for i, quest_template in enumerate(random.sample(DAILY_QUESTS_TEMPLATES, 3)):
            quest = quest_template.copy()
            quest["id"] = f"{today}_{i}"
            quest["progress"] = 0
            quest["completed"] = False
            player.data["active_quests"][quest["id"]] = quest
        player.data["quests_date"] = today
        player.save()
    
    quests_text = f"<b>📜 ЕЖЕДНЕВНЫЕ КВЕСТЫ</b> ({today})\n\n"
    
    for quest_id, quest in player.data["active_quests"].items():
        status = "✅" if quest.get("completed") else "📋"
        progress = quest.get("progress", 0)
        target = quest["target"]
        bar = "█" * min(10, int(progress/target*10)) + "░" * max(0, 10 - int(progress/target*10))
        
        quests_text += f"{status} <b>{quest['name']}</b>\n"
        quests_text += f"   [{bar}] {progress}/{target}\n"
        quests_text += f"   📝 {quest['desc']}\n"
        quests_text += f"   🎁 {quest['reward_money']}💰 + {quest['reward_exp']} EXP\n\n"
    
    bot.send_message(message.chat.id, quests_text[:4000])

@bot.message_handler(func=lambda m: m.text == "🏅 Достижения")
def achievements_handler(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    ach_text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(player.data['achievements'])}/{len(ACHIEVEMENTS_LIST)})\n\n"
    
    for ach_id, ach in ACHIEVEMENTS_LIST.items():
        if ach_id in player.data["achievements"]:
            ach_text += f"✅ {ach['name']}: {ach['desc']}\n"
        else:
            ach_text += f"🔒 {ach['name']}: {ach['desc']}\n"
    
    bot.send_message(message.chat.id, ach_text)

# ==================== РЫНОК ИГРОКОВ ====================
@bot.message_handler(func=lambda m: m.text == "🏪 Рынок")
def market_handler(message):
    if not market_listings:
        bot.send_message(message.chat.id, "🏪 На рынке пока нет предложений.\nИспользуйте /sell [предмет] [цена] для продажи!")
        return
    
    market_text = "<b>🏪 РЫНОК ИГРОКОВ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for i, (listing_id, listing) in enumerate(list(market_listings.items())[:20], 1):
        seller = Player(listing["seller_id"])
        item = items.get(listing["item_key"]) or limited_items.get(listing["item_key"])
        if not item:
            continue
        
        market_text += f"{i}. {item['name']}\n"
        market_text += f"   Продавец: {seller.data['first_name']}\n"
        market_text += f"   💰 {listing['price']} монет\n\n"
        
        markup.add(types.InlineKeyboardButton(
            f"Купить: {item['name']}",
            callback_data=f"mktbuy_{listing_id}"
        ))
    
    bot.send_message(message.chat.id, market_text[:4000], reply_markup=markup)

@bot.message_handler(commands=['sell'])
def sell_item(message):
    try:
        parts = message.text.split(maxsplit=2)
        item_name = parts[1]
        price = int(parts[2])
        
        if price < 10 or price > 100000:
            bot.send_message(message.chat.id, "❌ Цена должна быть от 10 до 100000💰")
            return
        
        user_id = message.from_user.id
        player = Player(user_id)
        
        # Поиск предмета в инвентаре
        found_key = None
        for item_key in player.data["inventory"]:
            item = items.get(item_key) or limited_items.get(item_key)
            if item and item_name.lower() in item["name"].lower():
                found_key = item_key
                break
        
        if not found_key:
            bot.send_message(message.chat.id, "❌ Предмет не найден в инвентаре!")
            return
        
        # Создание листинга
        listing_id = f"{user_id}_{int(time.time())}"
        market_listings[listing_id] = {
            "seller_id": user_id,
            "item_key": found_key,
            "price": price,
            "created_at": datetime.now().isoformat()
        }
        
        player.data["inventory"].remove(found_key)
        player.save()
        save_json(DATA_FILES['market'], market_listings)
        
        item = items.get(found_key) or limited_items.get(found_key)
        bot.send_message(message.chat.id, f"✅ <b>{item['name']}</b> выставлен на рынок за {price}💰!")
    except:
        bot.send_message(message.chat.id, "❌ Формат: /sell [название] [цена]")

@bot.callback_query_handler(func=lambda call: call.data.startswith("mktbuy_"))
def market_buy(call):
    listing_id = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    
    if listing_id not in market_listings:
        bot.answer_callback_query(call.id, "❌ Лот уже продан!")
        return
    
    listing = market_listings[listing_id]
    if str(listing["seller_id"]) == str(user_id):
        bot.answer_callback_query(call.id, "❌ Нельзя купить свой предмет!")
        return
    
    player = Player(user_id)
    if player.data["money"] < listing["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    player.data["money"] -= listing["price"]
    player.data["inventory"].append(listing["item_key"])
    
    seller = Player(listing["seller_id"])
    seller.data["money"] += int(listing["price"] * 0.95)  # Комиссия 5%
    
    del market_listings[listing_id]
    
    player.save()
    seller.save()
    save_json(DATA_FILES['market'], market_listings)
    
    item = items.get(listing["item_key"]) or limited_items.get(listing["item_key"])
    bot.answer_callback_query(call.id, f"✅ Куплено: {item['name']}!")
    bot.send_message(call.message.chat.id, f"✅ Вы купили <b>{item['name']}</b> за {listing['price']}💰!")

# ==================== КЛАНЫ ====================
@bot.message_handler(func=lambda m: m.text == "🛡 Кланы")
def clan_menu(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if player.data.get("clan"):
        clan_name = player.data["clan"]
        clan = clans.get(clan_name, {})
        
        clan_text = f"""
<b>🛡 КЛАН: {clan_name}</b>

👑 Лидер: {clan.get('leader_name', 'Нет')}
👥 Участников: {len(clan.get('members', []))}
💰 Казна: {clan.get('treasury', 0)}💰
🏆 Побед: {clan.get('wins', 0)}

<b>Участники (ТОП-10):</b>
{chr(10).join(f'• {m}' for m in clan.get('members', [])[:10])}
"""
        markup.add(
            types.InlineKeyboardButton("📊 Инфо", callback_data="clan_info"),
            types.InlineKeyboardButton("💰 Внести в казну", callback_data="clan_donate"),
            types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave")
        )
    else:
        clan_text = """
<b>🛡 КЛАНЫ</b>

Вы не состоите в клане!

<b>Команды:</b>
/create_clan [название] - создать (5000💰)
/join_clan [название] - вступить
/clans_list - список кланов
"""
        markup.add(
            types.InlineKeyboardButton("🆕 Создать клан", callback_data="clan_create"),
            types.InlineKeyboardButton("📋 Список", callback_data="clan_list")
        )
    
    bot.send_message(message.chat.id, clan_text, reply_markup=markup)

@bot.message_handler(commands=['create_clan'])
def create_clan(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    if player.data.get("clan"):
        bot.send_message(message.chat.id, "❌ Вы уже в клане!")
        return
    
    if player.data["money"] < 5000:
        bot.send_message(message.chat.id, "❌ Нужно 5000💰!")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ /create_clan [название]")
        return
    
    name = parts[1].strip()[:20]
    if name in clans:
        bot.send_message(message.chat.id, "❌ Такой клан уже есть!")
        return
    
    player.data["money"] -= 5000
    player.data["clan"] = name
    player.data["clan_role"] = "leader"
    
    clans[name] = {
        "leader_id": user_id,
        "leader_name": player.data["first_name"],
        "members": [player.data["first_name"]],
        "treasury": 0,
        "wins": 0,
        "created_at": datetime.now().isoformat()
    }
    
    player.save()
    save_json(DATA_FILES['clans'], clans)
    
    bot.send_message(message.chat.id, f"✅ Клан <b>{name}</b> создан!\nПриглашайте: /invite_clan [@username]")

@bot.message_handler(commands=['clans_list'])
def clans_list(message):
    if not clans:
        bot.send_message(message.chat.id, "📋 Нет активных кланов")
        return
    
    text = "<b>📋 СПИСОК КЛАНОВ</b>\n\n"
    for name, data in clans.items():
        text += f"🛡 <b>{name}</b>: {len(data['members'])} уч. | 👑 {data['leader_name']}\n"
    
    bot.send_message(message.chat.id, text[:4000])

@bot.message_handler(commands=['join_clan'])
def join_clan(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    if player.data.get("clan"):
        bot.send_message(message.chat.id, "❌ Вы уже в клане!")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ /join_clan [название]")
        return
    
    name = parts[1].strip()
    if name not in clans:
        bot.send_message(message.chat.id, "❌ Клан не найден!")
        return
    
    player.data["clan"] = name
    player.data["clan_role"] = "member"
    clans[name]["members"].append(player.data["first_name"])
    
    player.save()
    save_json(DATA_FILES['clans'], clans)
    
    bot.send_message(message.chat.id, f"✅ Вы вступили в клан <b>{name}</b>!")

# ==================== ТУРНИРЫ ====================
@bot.message_handler(func=lambda m: m.text == "🏟 Турниры")
def tournament_handler(message):
    if not tournaments:
        bot.send_message(message.chat.id, """
<b>🏟 ТУРНИРЫ</b>

Сейчас нет активных турниров!

<b>Администратор может создать:</b>
/create_tournament [название] [взнос] [приз]

Участвуйте в турнирах для получения эксклюзивных наград!
""")
        return
    
    text = "<b>🏟 АКТИВНЫЕ ТУРНИРЫ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for t_id, t_data in tournaments.items():
        if t_data.get("status") == "open":
            text += f"<b>{t_data['name']}</b>\n"
            text += f"💰 Взнос: {t_data['fee']} | 🏆 Приз: {t_data['prize']}\n"
            text += f"👥 Участников: {len(t_data.get('players', []))}/{t_data.get('max_players', 8)}\n\n"
            
            markup.add(types.InlineKeyboardButton(
                f"Участвовать: {t_data['name']}",
                callback_data=f"tour_join_{t_id}"
            ))
    
    bot.send_message(message.chat.id, text[:4000], reply_markup=markup)

@bot.message_handler(commands=['create_tournament'])
def create_tournament(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        name = parts[1]
        fee = int(parts[2])
        prize = int(parts[3])
        
        t_id = f"tour_{int(time.time())}"
        tournaments[t_id] = {
            "name": name,
            "fee": fee,
            "prize": prize,
            "max_players": 8,
            "players": [],
            "status": "open",
            "bracket": {},
            "created_at": datetime.now().isoformat()
        }
        save_json(DATA_FILES['tournaments'], tournaments)
        
        bot.send_message(message.chat.id, f"✅ Турнир <b>{name}</b> создан!\nВзнос: {fee}💰 | Приз: {prize}💰")
    except:
        bot.send_message(message.chat.id, "❌ /create_tournament [название] [взнос] [приз]")

@bot.callback_query_handler(func=lambda call: call.data.startswith("tour_join_"))
def join_tournament(call):
    t_id = call.data.split("_", 2)[2]
    user_id = call.from_user.id
    
    if t_id not in tournaments:
        bot.answer_callback_query(call.id, "❌ Турнир не найден!")
        return
    
    t_data = tournaments[t_id]
    if str(user_id) in t_data["players"]:
        bot.answer_callback_query(call.id, "❌ Вы уже участвуете!")
        return
    
    player = Player(user_id)
    if player.data["money"] < t_data["fee"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    player.data["money"] -= t_data["fee"]
    t_data["players"].append(str(user_id))
    
    player.save()
    save_json(DATA_FILES['tournaments'], tournaments)
    
    bot.answer_callback_query(call.id, "✅ Вы в турнире!")

# ==================== РЕЙТИНГ ====================
@bot.message_handler(func=lambda m: m.text == "📊 Рейтинг")
def rating_handler(message):
    # Сортировка по PvP рейтингу
    sorted_players = sorted(
        [(uid, data) for uid, data in users.items() if not uid.startswith("bot_")],
        key=lambda x: (x[1].get("pvp_rating", 1000), x[1].get("wins", 0)),
        reverse=True
    )[:20]
    
    text = "<b>📊 ТОП-20 ИГРОКОВ</b>\n\n"
    medals = ["🥇", "🥈", "🥉"] + ["4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"] + ["📌"]*10
    
    for i, (uid, data) in enumerate(sorted_players):
        text += f"{medals[i]} {data['first_name']}: {data.get('pvp_rating', 1000)} PTS | ⭐{data['level']}\n"
    
    bot.send_message(message.chat.id, text)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def check_level_up(player):
    level = player.data["level"]
    exp_needed = int(100 * (1.5 ** (level - 1)))
    
    leveled = False
    while player.data["exp"] >= exp_needed:
        player.data["exp"] -= exp_needed
        player.data["level"] += 1
        player.data["stat_points"] += 3
        player.data["max_hp"] += 10
        player.data["max_mana"] += 5
        player.data["hp"] = player.data["max_hp"]
        player.data["mana"] = player.data["max_mana"]
        
        titles = {5: "Боец", 10: "Воитель", 15: "Рыцарь", 20: "Ветеран",
                  25: "Мастер", 30: "Грандмастер", 40: "Герой", 50: "Легенда",
                  60: "Мифический воин", 75: "Полубог", 100: "Божество"}
        
        for req, title in titles.items():
            if player.data["level"] >= req and title not in player.data["titles_collected"]:
                player.data["titles_collected"].append(title)
                player.data["title"] = title
        
        level = player.data["level"]
        exp_needed = int(100 * (1.5 ** (level - 1)))
        leveled = True
    
    return leveled

# ==================== АДМИН-ПАНЕЛЬ ====================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Стата", callback_data="adm_stats"),
        types.InlineKeyboardButton("💰 Деньги", callback_data="adm_money"),
        types.InlineKeyboardButton("🎁 Предмет", callback_data="adm_item"),
        types.InlineKeyboardButton("👁 Юзер", callback_data="adm_user"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_bcast"),
        types.InlineKeyboardButton("⛔ Бан", callback_data="adm_ban"),
        types.InlineKeyboardButton("💎 Лимит", callback_data="adm_limited"),
        types.InlineKeyboardButton("🏟 Турнир", callback_data="adm_tour")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ v5.0</b>", reply_markup=markup)

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        target_id = int(parts[1])
        reason = parts[2] if len(parts) > 2 else "Нарушение правил"
        
        banned_users[str(target_id)] = {
            "reason": reason,
            "date": datetime.now().isoformat(),
            "until": "permanent",
            "banned_by": ADMIN_ID
        }
        save_json(DATA_FILES['bans'], banned_users)
        
        bot.send_message(message.chat.id, f"✅ Пользователь {target_id} забанен!\nПричина: {reason}")
    except:
        bot.send_message(message.chat.id, "❌ /ban [ID] [причина]")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        target_id = str(int(message.text.split()[1]))
        if target_id in banned_users:
            del banned_users[target_id]
            save_json(DATA_FILES['bans'], banned_users)
            bot.send_message(message.chat.id, f"✅ Пользователь {target_id} разбанен!")
        else:
            bot.send_message(message.chat.id, "❌ Пользователь не забанен!")
    except:
        bot.send_message(message.chat.id, "❌ /unban [ID]")

# ==================== ЗАПУСК БОТА ====================
def main():
    print("="*60)
    print("⚔️ ДУЭЛЬ БОТ v5.0 - ПОЛНАЯ РЕАЛИЗАЦИЯ")
    print("="*60)
    print(f"🕒 Запуск: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print(f"⚔ Предметов: {len(items)}")
    print(f"💎 Лимитированных: {len(limited_items)}")
    print(f"🛡 Кланов: {len(clans)}")
    print(f"🏟 Турниров: {len(tournaments)}")
    print(f"🏪 Лотов на рынке: {len(market_listings)}")
    print(f"📜 Достижений: {len(ACHIEVEMENTS_LIST)}")
    print(f"🎮 Действий в бою: {len(DUEL_ACTIONS)}")
    print("="*60)
    print("✅ ВСЕ СИСТЕМЫ РЕАЛИЗОВАНЫ!")
    print("✅ Пошаговая боевая система")
    print("✅ Кланы, турниры, рынок")
    print("✅ Квесты и достижения")
    print("✅ Админ-панель с банами")
    print("="*60)
    print("🚀 Бот запущен!")
    print("="*60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
