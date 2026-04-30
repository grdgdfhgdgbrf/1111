import telebot
from telebot import types
import json
import random
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict
import copy
import uuid
import math

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = '8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE'
ADMIN_ID = 5356400377
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ==================== КОНСТАНТЫ ====================
BODY_PARTS = {
    "head": {"name": "🎯 Голова", "hit_chance": 30, "damage_mult": 2.0, "defense_bonus": 0},
    "body": {"name": "👤 Тело", "hit_chance": 50, "damage_mult": 1.0, "defense_bonus": 5},
    "legs": {"name": "🦵 Ноги", "hit_chance": 20, "damage_mult": 0.7, "defense_bonus": 2}
}

ATTACK_TYPES = {
    "quick": {"name": "⚡ Быстрый", "accuracy": 90, "damage_mult": 0.8, "crit_chance": 10},
    "normal": {"name": "⚔ Обычный", "accuracy": 75, "damage_mult": 1.0, "crit_chance": 15},
    "heavy": {"name": "💪 Тяжёлый", "accuracy": 55, "damage_mult": 1.5, "crit_chance": 25},
    "precision": {"name": "🎯 Точный", "accuracy": 95, "damage_mult": 0.6, "crit_chance": 35},
    "wild": {"name": "💢 Дикий", "accuracy": 45, "damage_mult": 2.0, "crit_chance": 40}
}

DEFENSE_TYPES = {
    "dodge": {"name": "💨 Уклонение", "effectiveness": 60, "stamina_cost": 15},
    "block": {"name": "🛡 Блок", "effectiveness": 80, "stamina_cost": 20},
    "parry": {"name": "⚔ Парирование", "effectiveness": 50, "stamina_cost": 25, "counter_chance": 30},
    "endure": {"name": "💪 Выдержка", "effectiveness": 40, "stamina_cost": 10, "damage_reduction": 0.3}
}

RARITY_COLORS = {
    "common": "⬜", "uncommon": "🟩", "rare": "🟦",
    "epic": "🟪", "legendary": "🟧", "mythic": "🟥",
    "divine": "💛", "apocalyptic": "🖤"
}

ELEMENTS = {
    "fire": {"name": "🔥 Огонь", "strong": "ice", "weak": "water"},
    "ice": {"name": "❄ Лёд", "strong": "nature", "weak": "fire"},
    "lightning": {"name": "⚡ Молния", "strong": "water", "weak": "earth"},
    "water": {"name": "🌊 Вода", "strong": "fire", "weak": "lightning"},
    "nature": {"name": "🌿 Природа", "strong": "earth", "weak": "ice"},
    "earth": {"name": "🏔 Земля", "strong": "lightning", "weak": "nature"},
    "dark": {"name": "🌑 Тьма", "strong": "light", "weak": "light"},
    "light": {"name": "✨ Свет", "strong": "dark", "weak": "dark"}
}

SPECIAL_EFFECTS = {
    "burn": {"name": "🔥 Горение", "duration": 3, "damage_per_turn": 10},
    "freeze": {"name": "❄ Заморозка", "duration": 2, "speed_reduction": 50},
    "stun": {"name": "⚡ Оглушение", "duration": 1, "skip_turn": True},
    "poison": {"name": "☠ Отравление", "duration": 4, "damage_per_turn": 8},
    "bleed": {"name": "🩸 Кровотечение", "duration": 3, "damage_per_turn": 12},
    "blind": {"name": "🌑 Ослепление", "duration": 2, "accuracy_reduction": 40},
    "weakness": {"name": "💔 Слабость", "duration": 3, "damage_reduction": 25},
    "haste": {"name": "💨 Ускорение", "duration": 2, "speed_boost": 30},
    "regen": {"name": "💚 Регенерация", "duration": 3, "heal_per_turn": 15},
    "shield": {"name": "🛡 Щит", "duration": 2, "damage_absorption": 30}
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
    'dungeons': 'dungeons.json',
    'events': 'events.json',
    'bans': 'bans.json',
    'quests': 'quests.json',
    'battle_history': 'battle_history.json'
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

# ==================== ПРЕДМЕТЫ С УНИКАЛЬНЫМИ АТАКАМИ ====================
# Каждый предмет имеет уникальные атаки и эффекты
WEAPONS = {
    "rusty_sword": {
        "name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon",
        "rarity": "common", "level_req": 1, "element": None, "slot": "weapon",
        "attacks": {
            "slash": {"name": "Разрез", "damage_mult": 1.0, "accuracy": 85, "stamina_cost": 10},
            "stab": {"name": "Укол", "damage_mult": 0.8, "accuracy": 90, "stamina_cost": 8, "bleed_chance": 10}
        },
        "description": "Старый ржавый меч"
    },
    "hunters_bow": {
        "name": "🏹 Лук охотника", "damage": (8, 14), "price": 150, "type": "weapon",
        "rarity": "common", "level_req": 3, "element": "nature", "slot": "weapon",
        "attacks": {
            "quick_shot": {"name": "Быстрый выстрел", "damage_mult": 0.9, "accuracy": 80, "stamina_cost": 12},
            "aimed_shot": {"name": "Прицельный", "damage_mult": 1.3, "accuracy": 70, "stamina_cost": 18, "crit_chance": 15},
            "multi_shot": {"name": "Залп", "damage_mult": 0.6, "accuracy": 60, "stamina_cost": 25, "hits": 3}
        },
        "description": "Надёжный лук для охоты"
    },
    "flame_blade": {
        "name": "🔥 Пламенный клинок", "damage": (12, 20), "price": 400, "type": "weapon",
        "rarity": "uncommon", "level_req": 7, "element": "fire", "slot": "weapon",
        "attacks": {
            "fire_slash": {"name": "Огненный разрез", "damage_mult": 1.2, "accuracy": 80, "stamina_cost": 15, "burn_chance": 25},
            "inferno": {"name": "Инферно", "damage_mult": 1.6, "accuracy": 65, "stamina_cost": 25, "burn_chance": 50},
            "flame_wave": {"name": "Волна пламени", "damage_mult": 2.0, "accuracy": 50, "stamina_cost": 35, "burn_chance": 40, "aoe": True}
        },
        "description": "Клинок в вечном пламени"
    },
    "frost_axe": {
        "name": "❄ Ледяной топор", "damage": (14, 22), "price": 700, "type": "weapon",
        "rarity": "uncommon", "level_req": 10, "element": "ice", "slot": "weapon",
        "attacks": {
            "frost_strike": {"name": "Ледяной удар", "damage_mult": 1.1, "accuracy": 80, "stamina_cost": 15, "freeze_chance": 20},
            "ice_shatter": {"name": "Ледяной раскол", "damage_mult": 1.5, "accuracy": 65, "stamina_cost": 25, "freeze_chance": 45},
            "blizzard": {"name": "Метель", "damage_mult": 1.8, "accuracy": 55, "stamina_cost": 35, "freeze_chance": 35, "aoe": True}
        },
        "description": "Замораживает противников"
    },
    "storm_staff": {
        "name": "⚡ Посох бурь", "damage": (16, 26), "price": 1200, "type": "weapon",
        "rarity": "rare", "level_req": 14, "element": "lightning", "slot": "weapon",
        "attacks": {
            "lightning_bolt": {"name": "Молния", "damage_mult": 1.3, "accuracy": 75, "stamina_cost": 18, "stun_chance": 15},
            "thunder_strike": {"name": "Удар грома", "damage_mult": 1.7, "accuracy": 60, "stamina_cost": 28, "stun_chance": 35},
            "chain_lightning": {"name": "Цепная молния", "damage_mult": 1.4, "accuracy": 70, "stamina_cost": 30, "chain_hits": 3}
        },
        "description": "Призывает молнии"
    },
    "shadow_dagger": {
        "name": "🌑 Теневой кинжал", "damage": (20, 32), "price": 3500, "type": "weapon",
        "rarity": "epic", "level_req": 22, "element": "dark", "slot": "weapon",
        "attacks": {
            "shadow_strike": {"name": "Теневой удар", "damage_mult": 1.4, "accuracy": 85, "stamina_cost": 20, "blind_chance": 20},
            "backstab": {"name": "Удар в спину", "damage_mult": 2.2, "accuracy": 60, "stamina_cost": 30, "crit_chance": 30, "bleed_chance": 40},
            "assassinate": {"name": "Убийство", "damage_mult": 3.0, "accuracy": 40, "stamina_cost": 45, "ignore_defense": 50}
        },
        "description": "Атакует из тени"
    },
    "divine_spear": {
        "name": "✨ Божественное копьё", "damage": (25, 40), "price": 6000, "type": "weapon",
        "rarity": "legendary", "level_req": 28, "element": "light", "slot": "weapon",
        "attacks": {
            "holy_strike": {"name": "Святой удар", "damage_mult": 1.5, "accuracy": 80, "stamina_cost": 20, "regen_chance": 15},
            "divine_judgment": {"name": "Божий суд", "damage_mult": 2.5, "accuracy": 55, "stamina_cost": 40, "stun_chance": 30},
            "purification": {"name": "Очищение", "damage_mult": 1.8, "accuracy": 70, "stamina_cost": 30, "cure_self": True}
        },
        "description": "Оружие небес"
    },
    "death_scythe": {
        "name": "💀 Коса смерти", "damage": (30, 50), "price": 10000, "type": "weapon",
        "rarity": "mythic", "level_req": 35, "element": "dark", "slot": "weapon",
        "attacks": {
            "reap": {"name": "Жатва", "damage_mult": 1.8, "accuracy": 75, "stamina_cost": 25, "life_steal": 30},
            "death_sentence": {"name": "Смертный приговор", "damage_mult": 2.8, "accuracy": 50, "stamina_cost": 45, "execute_threshold": 25},
            "soul_harvest": {"name": "Сбор душ", "damage_mult": 2.2, "accuracy": 65, "stamina_cost": 35, "curse_chance": 40}
        },
        "description": "Забирает души"
    }
}

# Шлемы (голова)
HELMETS = {
    "leather_cap": {
        "name": "🎩 Кожаная шапка", "defense": 3, "price": 60, "type": "helmet",
        "rarity": "common", "level_req": 1, "slot": "head",
        "description": "Простая защита головы"
    },
    "iron_helmet": {
        "name": "⛑ Железный шлем", "defense": 8, "price": 300, "type": "helmet",
        "rarity": "uncommon", "level_req": 8, "slot": "head",
        "special": {"stun_resist": 20},
        "description": "+20% сопротивление оглушению"
    },
    "dragon_helmet": {
        "name": "🐉 Шлем дракона", "defense": 15, "price": 2000, "type": "helmet",
        "rarity": "epic", "level_req": 20, "slot": "head",
        "special": {"fire_resist": 40, "intimidation": 15},
        "description": "Устрашает врагов"
    },
    "crown_of_wisdom": {
        "name": "👑 Корона мудрости", "defense": 10, "price": 4000, "type": "helmet",
        "rarity": "legendary", "level_req": 30, "slot": "head",
        "special": {"mana_regen": 10, "skill_cooldown": 20},
        "description": "Уменьшает кулдауны навыков"
    }
}

# Нагрудники (тело)
CHESTPIECES = {
    "leather_vest": {
        "name": "🧥 Кожаный жилет", "defense": 5, "hp_bonus": 20, "price": 80,
        "type": "chest", "rarity": "common", "level_req": 1, "slot": "body",
        "description": "Лёгкая защита"
    },
    "chainmail": {
        "name": "⛓ Кольчуга", "defense": 12, "hp_bonus": 40, "price": 400,
        "type": "chest", "rarity": "uncommon", "level_req": 8, "slot": "body",
        "description": "Надёжная кольчуга"
    },
    "plate_armor": {
        "name": "🛡 Латный доспех", "defense": 20, "hp_bonus": 80, "price": 1200,
        "type": "chest", "rarity": "rare", "level_req": 15, "slot": "body",
        "special": {"physical_resist": 15},
        "description": "Тяжёлые латы"
    },
    "phoenix_armor": {
        "name": "🦅 Броня феникса", "defense": 30, "hp_bonus": 150, "price": 7000,
        "type": "chest", "rarity": "legendary", "level_req": 30, "slot": "body",
        "special": {"rebirth": True, "fire_heal": 25},
        "description": "Возрождает из пепла"
    }
}

# Поножи (ноги)
LEGPIECES = {
    "leather_pants": {
        "name": "👖 Кожаные штаны", "defense": 3, "speed": 2, "price": 70,
        "type": "legs", "rarity": "common", "level_req": 1, "slot": "legs",
        "description": "Защита ног"
    },
    "iron_greaves": {
        "name": "🦿 Железные поножи", "defense": 8, "speed": -2, "price": 350,
        "type": "legs", "rarity": "uncommon", "level_req": 8, "slot": "legs",
        "description": "Тяжёлая защита ног"
    },
    "wind_striders": {
        "name": "🌪 Набедренники ветра", "defense": 10, "speed": 15, "price": 2500,
        "type": "legs", "rarity": "epic", "level_req": 22, "slot": "legs",
        "special": {"dodge_chance": 10, "first_strike": True},
        "description": "Даруют скорость ветра"
    },
    "hermes_greaves": {
        "name": "👟 Поножи Гермеса", "defense": 15, "speed": 30, "price": 8000,
        "type": "legs", "rarity": "legendary", "level_req": 35, "slot": "legs",
        "special": {"double_turn_chance": 15, "blink": True},
        "description": "Скорость бога"
    }
}

# Аксессуары
ACCESSORIES = {
    "strength_ring": {
        "name": "💍 Кольцо силы", "price": 600, "type": "accessory",
        "rarity": "uncommon", "level_req": 5, "slot": "accessory",
        "stats": {"strength": 5, "min_damage": 4},
        "description": "+5 к силе"
    },
    "crit_amulet": {
        "name": "📿 Амулет крита", "price": 1500, "type": "accessory",
        "rarity": "rare", "level_req": 15, "slot": "accessory",
        "stats": {"crit_chance": 15},
        "description": "+15% к шансу крита"
    },
    "lucky_charm": {
        "name": "🍀 Талисман удачи", "price": 2500, "type": "accessory",
        "rarity": "epic", "level_req": 20, "slot": "accessory",
        "stats": {"luck": 15, "drop_rate": 10},
        "description": "Увеличивает удачу"
    }
}

# Зелья
POTIONS = {
    "health_potion": {
        "name": "🧪 Зелье здоровья", "heal": 40, "price": 40,
        "type": "potion", "rarity": "common", "level_req": 1,
        "description": "Восстанавливает 40 HP"
    },
    "big_health_potion": {
        "name": "🧪 Большое зелье", "heal": 100, "price": 120,
        "type": "potion", "rarity": "uncommon", "level_req": 8,
        "description": "Восстанавливает 100 HP"
    },
    "elixir_of_life": {
        "name": "💊 Эликсир жизни", "heal": 250, "price": 350,
        "type": "potion", "rarity": "rare", "level_req": 15,
        "description": "Полное восстановление"
    },
    "mana_potion": {
        "name": "💎 Зелье маны", "mana_restore": 80, "price": 60,
        "type": "potion", "rarity": "common", "level_req": 5,
        "description": "Восстанавливает 80 MP"
    },
    "antidote": {
        "name": "💚 Противоядие", "price": 100, "type": "potion",
        "rarity": "common", "level_req": 1,
        "effects": ["cure_poison", "cure_bleed"],
        "description": "Снимает яд и кровотечение"
    }
}

# Лимитированные предметы
LIMITED_ITEMS = {
    "thunderfury": {
        "name": "⚡ Ярость грома", "damage": (60, 90), "total": 3,
        "remaining": 3, "price": 50000, "type": "weapon",
        "rarity": "divine", "element": "lightning", "slot": "weapon",
        "attacks": {
            "thunder_gods_wrath": {"name": "Гнев бога грома", "damage_mult": 4.0, "accuracy": 70, "stamina_cost": 50, "stun_chance": 60, "aoe": True},
            "eye_of_the_storm": {"name": "Глаз бури", "damage_mult": 3.0, "accuracy": 80, "stamina_cost": 40, "chain_hits": 5},
            "lightning_apocalypse": {"name": "Молниевый апокалипсис", "damage_mult": 5.0, "accuracy": 45, "stamina_cost": 80, "stun_chance": 80}
        },
        "description": "Меч бога грома"
    },
    "apocalypse": {
        "name": "🌋 Апокалипсис", "damage": (80, 140), "total": 1,
        "remaining": 1, "price": 100000, "type": "weapon",
        "rarity": "apocalyptic", "element": "dark", "slot": "weapon",
        "attacks": {
            "world_ender": {"name": "Конец света", "damage_mult": 6.0, "accuracy": 50, "stamina_cost": 100, "ignore_defense": 100},
            "obliterate": {"name": "Уничтожение", "damage_mult": 4.5, "accuracy": 65, "stamina_cost": 70, "execute_threshold": 40},
            "void_annihilation": {"name": "Аннигиляция пустоты", "damage_mult": 5.5, "accuracy": 55, "stamina_cost": 85, "curse_chance": 70}
        },
        "description": "Единственный в мире"
    }
}

# Объединение всех предметов
ALL_ITEMS = {}
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(CHESTPIECES)
ALL_ITEMS.update(LEGPIECES)
ALL_ITEMS.update(ACCESSORIES)
ALL_ITEMS.update(POTIONS)

# Загрузка данных
items = load_json(DATA_FILES['items'], ALL_ITEMS)
limited_items = load_json(DATA_FILES['limited'], LIMITED_ITEMS)
users = load_json(DATA_FILES['users'], {})
active_duels = load_json(DATA_FILES['duels'], {})
clans = load_json(DATA_FILES['clans'], {})
tournaments = load_json(DATA_FILES['tournaments'], {})
market_listings = load_json(DATA_FILES['market'], {})
dungeons = load_json(DATA_FILES['dungeons'], {})
events = load_json(DATA_FILES['events'], {})
banned_users = load_json(DATA_FILES['bans'], {})
quests_data = load_json(DATA_FILES['quests'], {})
battle_history = load_json(DATA_FILES['battle_history'], {})

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
                "stamina": 100,
                "max_stamina": 100,
                "mana": 50,
                "max_mana": 50,
                "stats": {
                    "strength": 5,
                    "agility": 5,
                    "intelligence": 5,
                    "vitality": 5,
                    "luck": 5
                },
                "stat_points": 0,
                "wins": 0, "losses": 0, "draws": 0,
                "win_streak": 0, "best_streak": 0,
                "total_duels": 0, "pvp_rating": 1000,
                "total_damage_dealt": 0, "total_damage_taken": 0,
                "critical_hits": 0, "skills_used": 0,
                "inventory": [],
                "equipment": {
                    "weapon": None,
                    "head": None,
                    "body": None,
                    "legs": None,
                    "accessory": None
                },
                "last_daily": None,
                "last_dungeon": None,
                "last_work": None,
                "title": "Новичок",
                "titles_collected": ["Новичок"],
                "achievements": [],
                "active_quests": {},
                "completed_quests": 0,
                "clan": None,
                "clan_role": None,
                "tournament_wins": 0,
                "registration_date": datetime.now().isoformat(),
                "settings": {"notifications": True, "duel_requests": True, "show_battle_log": True},
                "battle_history": [],
                "dungeons_completed": 0,
                "items_found": 0,
                "defense_stance": {"head": 0, "body": 0, "legs": 0}
            }
            self.save()
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    def save(self):
        save_json(DATA_FILES['users'], users)
    
    def get_full_stats(self):
        """Полный расчёт характеристик"""
        base = copy.deepcopy(self.data["stats"])
        bonuses = {
            "min_damage": base["strength"] * 2,
            "max_damage": base["strength"] * 3,
            "defense": base["vitality"] * 2,
            "speed": base["agility"] * 1.5,
            "crit_chance": 5 + base["luck"] * 0.5,
            "crit_multiplier": 1.5,
            "dodge_chance": 3 + base["agility"] * 0.3,
            "block_chance": 0,
            "hp": self.data["max_hp"] + base["vitality"] * 15,
            "max_hp": self.data["max_hp"] + base["vitality"] * 15,
            "stamina": self.data["max_stamina"] + base["vitality"] * 5,
            "max_stamina": self.data["max_stamina"] + base["vitality"] * 5,
            "mana": self.data["max_mana"] + base["intelligence"] * 8,
            "max_mana": self.data["max_mana"] + base["intelligence"] * 8,
            "life_steal": 0,
            "damage_reflect": 0,
            "elemental_bonus": {},
            "exp_boost": 0,
            "money_boost": 0,
            "defense_head": 0,
            "defense_body": 0,
            "defense_legs": 0
        }
        
        for slot, item_key in self.data["equipment"].items():
            if not item_key:
                continue
            item = items.get(item_key) or limited_items.get(item_key)
            if not item:
                continue
            
            if item["type"] == "weapon" and "damage" in item:
                bonuses["min_damage"] += item["damage"][0]
                bonuses["max_damage"] += item["damage"][1]
                if "element" in item and item["element"]:
                    bonuses["elemental_bonus"][item["element"]] = bonuses["elemental_bonus"].get(item["element"], 0) + 20
            
            elif item["type"] == "helmet":
                bonuses["defense_head"] += item.get("defense", 0)
            
            elif item["type"] == "chest":
                bonuses["defense_body"] += item.get("defense", 0)
                bonuses["max_hp"] += item.get("hp_bonus", 0)
                bonuses["hp"] = bonuses["max_hp"]
            
            elif item["type"] == "legs":
                bonuses["defense_legs"] += item.get("defense", 0)
                bonuses["speed"] += item.get("speed", 0)
                if "dodge_chance" in item.get("special", {}):
                    bonuses["dodge_chance"] += item["special"]["dodge_chance"]
            
            elif item["type"] == "accessory":
                for stat, value in item.get("stats", {}).items():
                    if stat == "strength":
                        bonuses["min_damage"] += value * 2
                        bonuses["max_damage"] += value * 3
                    elif stat == "crit_chance":
                        bonuses["crit_chance"] += value
                    elif stat == "luck":
                        bonuses["crit_chance"] += value * 0.5
                    elif stat == "min_damage":
                        bonuses["min_damage"] += value
                    elif stat == "drop_rate":
                        bonuses["money_boost"] += value
        
        bonuses["crit_chance"] = min(80, bonuses["crit_chance"])
        bonuses["dodge_chance"] = min(50, bonuses["dodge_chance"])
        
        return bonuses

# ==================== УЛУЧШЕННАЯ БОЕВАЯ СИСТЕМА ====================
class AdvancedBattle:
    def __init__(self, player1_id, player2_id, duel_type="quick", bet=0):
        self.battle_id = str(uuid.uuid4())[:8]
        self.p1_id = str(player1_id)
        self.p2_id = str(player2_id)
        self.duel_type = duel_type
        self.bet = bet
        self.turn = 0
        self.max_turns = 50
        self.active = True
        self.winner = None
        self.battle_log = []
        self.phase = "attack_select"  # attack_select, defense_select, execute
        self.p1_attack = None
        self.p2_attack = None
        self.p1_defense = None
        self.p2_defense = None
        self.p1_target = None
        self.p2_target = None
        
        # Инициализация игроков
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        # Статы
        self.p1_stats = self.p1.get_full_stats()
        self.p2_stats = self.p2.get_full_stats()
        
        # HP и ресурсы
        self.p1_hp = self.p1_stats["max_hp"]
        self.p2_hp = self.p2_stats["max_hp"]
        self.p1_max_hp = self.p1_hp
        self.p2_max_hp = self.p2_hp
        
        self.p1_stamina = self.p1_stats["max_stamina"]
        self.p2_stamina = self.p2_stats["max_stamina"]
        self.p1_max_stamina = self.p1_stamina
        self.p2_max_stamina = self.p2_stamina
        
        self.p1_mana = self.p1_stats["max_mana"]
        self.p2_mana = self.p2_stats["max_mana"]
        
        # Определение первого хода
        p1_speed = self.p1_stats["speed"] + random.randint(-10, 10)
        p2_speed = self.p2_stats["speed"] + random.randint(-10, 10)
        
        if p1_speed >= p2_speed:
            self.current_player = 1
            self.defending_player = 2
        else:
            self.current_player = 2
            self.defending_player = 1
        
        # Активные эффекты
        self.p1_effects = []
        self.p2_effects = []
        
        # Кулдауны защиты
        self.p1_defense_cooldowns = {"head": 0, "body": 0, "legs": 0}
        self.p2_defense_cooldowns = {"head": 0, "body": 0, "legs": 0}
        
        self._save_to_active()
        
        self.battle_log.append(f"⚔ <b>БИТВА НАЧАЛАСЬ!</b>")
        self.battle_log.append(f"Первый ход: <b>{self._get_name(self.current_player)}</b>")
    
    def _get_name(self, player_num):
        return self.p1.data["first_name"] if player_num == 1 else self.p2.data["first_name"]
    
    def _get_player(self, player_num):
        return self.p1 if player_num == 1 else self.p2
    
    def _get_stats(self, player_num):
        return self.p1_stats if player_num == 1 else self.p2_stats
    
    def _save_to_active(self):
        active_duels[self.battle_id] = {
            "p1_id": self.p1_id, "p2_id": self.p2_id,
            "type": self.duel_type, "bet": self.bet,
            "turn": self.turn, "phase": self.phase,
            "current_player": self.current_player,
            "started_at": datetime.now().isoformat()
        }
        save_json(DATA_FILES['duels'], active_duels)
    
    def get_available_attacks(self, player_num):
        """Получить доступные атаки для игрока"""
        player = self._get_player(player_num)
        weapon_key = player.data["equipment"].get("weapon")
        
        attacks = {}
        
        # Базовые атаки (всегда доступны)
        attacks["basic_punch"] = {
            "name": "👊 Базовый удар",
            "damage_mult": 0.6,
            "accuracy": 85,
            "stamina_cost": 5,
            "description": "Удар кулаком"
        }
        attacks["basic_kick"] = {
            "name": "🦵 Базовый пинок",
            "damage_mult": 0.7,
            "accuracy": 80,
            "stamina_cost": 8,
            "description": "Удар ногой"
        }
        
        # Атаки оружия
        if weapon_key:
            weapon = items.get(weapon_key) or limited_items.get(weapon_key)
            if weapon and "attacks" in weapon:
                for attack_id, attack_data in weapon["attacks"].items():
                    attacks[attack_id] = attack_data
        
        # Фильтрация по стамине
        available = {}
        stamina = self.p1_stamina if player_num == 1 else self.p2_stamina
        for aid, adata in attacks.items():
            if stamina >= adata.get("stamina_cost", 0):
                available[aid] = adata
        
        return available
    
    def get_available_defenses(self, player_num):
        """Получить доступные защиты"""
        defenses = copy.deepcopy(DEFENSE_TYPES)
        stamina = self.p1_stamina if player_num == 1 else self.p2_stamina
        
        available = {}
        for did, ddata in defenses.items():
            if stamina >= ddata.get("stamina_cost", 0):
                available[did] = ddata
        
        return available
    
    def set_attack(self, player_num, attack_id, target_part):
        """Установить атаку игрока"""
        if self.phase != "attack_select":
            return "Сейчас не фаза выбора атаки!"
        
        if player_num != self.current_player:
            return "Сейчас не ваш ход!"
        
        attacks = self.get_available_attacks(player_num)
        if attack_id not in attacks:
            return "Атака недоступна!"
        
        if target_part not in BODY_PARTS:
            return "Неверная часть тела!"
        
        if player_num == 1:
            self.p1_attack = attack_id
            self.p1_target = target_part
        else:
            self.p2_attack = attack_id
            self.p2_target = target_part
        
        self.phase = "defense_select"
        self._save_to_active()
        
        return f"✅ Атака выбрана! Цель: {BODY_PARTS[target_part]['name']}"
    
    def set_defense(self, player_num, defense_id, protect_part):
        """Установить защиту"""
        if self.phase != "defense_select":
            return "Сейчас не фаза выбора защиты!"
        
        if player_num != self.defending_player:
            return "Сейчас не ваша очередь защищаться!"
        
        defenses = self.get_available_defenses(player_num)
        if defense_id not in defenses:
            return "Защита недоступна!"
        
        if protect_part not in BODY_PARTS:
            return "Неверная часть тела!"
        
        if player_num == 1:
            self.p1_defense = defense_id
            self.p1_protect = protect_part
        else:
            self.p2_defense = defense_id
            self.p2_protect = protect_part
        
        # Выполнение раунда
        self._execute_round()
        
        return "✅ Защита выбрана!"
    
    def _execute_round(self):
        """Выполнить раунд боя"""
        attacker = self.current_player
        defender = self.defending_player
        
        attack_id = self.p1_attack if attacker == 1 else self.p2_attack
        target_part = self.p1_target if attacker == 1 else self.p2_target
        defense_id = self.p1_defense if defender == 1 else self.p2_defense
        protect_part = self.p1_protect if defender == 1 else self.p2_protect
        
        attacker_player = self._get_player(attacker)
        attacker_stats = self._get_stats(attacker)
        defender_stats = self._get_stats(defender)
        
        # Получение данных атаки
        attacks = self.get_available_attacks(attacker)
        attack_data = attacks.get(attack_id, {"name": "Базовая атака", "damage_mult": 0.6, "accuracy": 80, "stamina_cost": 5})
        
        # Трата стамины
        stamina_cost = attack_data.get("stamina_cost", 5)
        if attacker == 1:
            self.p1_stamina -= stamina_cost
        else:
            self.p2_stamina -= stamina_cost
        
        result = f"\n<b>Ход {self.turn + 1}</b>\n"
        result += f"⚔ {self._get_name(attacker)} атакует {attack_data['name']} в {BODY_PARTS[target_part]['name']}!\n"
        result += f"🛡 {self._get_name(defender)} защищает {BODY_PARTS[protect_part]['name']} используя {DEFENSE_TYPES.get(defense_id, {}).get('name', 'Защита')}\n"
        
        # Расчёт урона
        min_dmg = int(attacker_stats["min_damage"])
        max_dmg = int(attacker_stats["max_damage"])
        base_damage = random.randint(min_dmg, max_dmg)
        damage = int(base_damage * attack_data.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_mult = BODY_PARTS[target_part]["damage_mult"]
        damage = int(damage * body_mult)
        
        # Проверка точности
        accuracy = attack_data.get("accuracy", 80)
        if random.randint(1, 100) > accuracy:
            damage = 0
            result += "💨 ПРОМАХ!\n"
        else:
            # Проверка защиты
            if target_part == protect_part:
                # Защита сработала
                defense_eff = DEFENSE_TYPES.get(defense_id, {}).get("effectiveness", 50)
                damage = int(damage * (1 - defense_eff / 100))
                result += "🛡 ЗАЩИТА СРАБОТАЛА!\n"
            
            # Защита части тела
            if target_part == "head":
                def_bonus = defender_stats["defense_head"]
            elif target_part == "body":
                def_bonus = defender_stats["defense_body"]
            else:
                def_bonus = defender_stats["defense_legs"]
            
            damage = max(1, damage - def_bonus)
            
            # Крит
            crit_chance = attacker_stats["crit_chance"] + attack_data.get("crit_chance", 0)
            if random.random() * 100 < crit_chance:
                damage = int(damage * attacker_stats["crit_multiplier"])
                result += "💥 КРИТИЧЕСКИЙ УДАР!\n"
                attacker_player.data["critical_hits"] += 1
            
            # Эффекты
            for effect_name in ["burn", "freeze", "stun", "poison", "bleed", "blind", "curse"]:
                chance = attack_data.get(f"{effect_name}_chance", 0)
                if chance > 0 and random.random() * 100 < chance:
                    if defender == 1:
                        self.p1_effects.append({"type": effect_name, "duration": SPECIAL_EFFECTS[effect_name]["duration"]})
                    else:
                        self.p2_effects.append({"type": effect_name, "duration": SPECIAL_EFFECTS[effect_name]["duration"]})
                    result += f"{SPECIAL_EFFECTS[effect_name]['name']}!\n"
            
            result += f"💢 Урон: <b>{damage}</b>\n"
        
        # Применение урона
        if defender == 1:
            self.p1_hp = max(0, self.p1_hp - damage)
        else:
            self.p2_hp = max(0, self.p2_hp - damage)
        
        # Обработка эффектов
        result += self._process_effects(defender)
        
        # Восстановление стамины
        self.p1_stamina = min(self.p1_max_stamina, self.p1_stamina + 10)
        self.p2_stamina = min(self.p2_max_stamina, self.p2_stamina + 10)
        
        # Сброс выборов
        self.p1_attack = None
        self.p2_attack = None
        self.p1_defense = None
        self.p2_defense = None
        self.p1_target = None
        self.p2_target = None
        
        # Смена ролей
        self.current_player, self.defending_player = self.defending_player, self.current_player
        self.phase = "attack_select"
        self.turn += 1
        
        self.battle_log.append(result)
        
        # Проверка завершения
        if self.p1_hp <= 0:
            self.active = False
            self.winner = 2
        elif self.p2_hp <= 0:
            self.active = False
            self.winner = 1
        elif self.turn >= self.max_turns:
            self.active = False
            self.winner = 0
        
        self._save_to_active()
    
    def _process_effects(self, player_num):
        """Обработка эффектов"""
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        result = ""
        
        for effect in effects[:]:
            eff_data = SPECIAL_EFFECTS.get(effect["type"], {})
            
            if "damage_per_turn" in eff_data:
                dmg = eff_data["damage_per_turn"]
                if player_num == 1:
                    self.p1_hp -= dmg
                else:
                    self.p2_hp -= dmg
                result += f"{eff_data['name']} -{dmg} HP\n"
            
            if "heal_per_turn" in eff_data:
                heal = eff_data["heal_per_turn"]
                if player_num == 1:
                    self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
                else:
                    self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
                result += f"💚 +{heal} HP\n"
            
            effect["duration"] -= 1
            if effect["duration"] <= 0:
                effects.remove(effect)
        
        return result
    
    def get_state_for_player(self, player_num):
        """Получить состояние боя для конкретного игрока"""
        is_attacker = (player_num == self.current_player)
        is_defender = (player_num == self.defending_player)
        
        state = f"""
<b>⚔ БИТВА #{self.battle_id}</b>
━━━━━━━━━━━━━━━━━━
Ход: <b>{self.turn}</b> | Фаза: <b>{"⚔ Атака" if self.phase == "attack_select" else "🛡 Защита"}</b>

<b>ВЫ:</b> {self._get_name(player_num)}
❤ {self._hp_bar(player_num)}
💪 Стамина: {self._stamina_bar(player_num)}

<b>ПРОТИВНИК:</b> {self._get_name(3 - player_num)}
❤ {self._hp_bar(3 - player_num)}
💪 Стамина: {self._stamina_bar(3 - player_num)}
━━━━━━━━━━━━━━━━━━
"""
        
        if self.phase == "attack_select" and is_attacker:
            state += "\n🟢 <b>ВАША ФАЗА АТАКИ!</b>\nВыберите атаку и цель:"
        elif self.phase == "defense_select" and is_defender:
            state += "\n🛡 <b>ВАША ФАЗА ЗАЩИТЫ!</b>\nВыберите защиту и часть тела:"
        else:
            state += "\n⏳ <b>Ожидание действий противника...</b>"
        
        if self.battle_log:
            state += f"\n\n<i>Последнее: {self.battle_log[-1][:150]}</i>"
        
        return state
    
    def _hp_bar(self, player_num):
        hp = self.p1_hp if player_num == 1 else self.p2_hp
        max_hp = self.p1_max_hp if player_num == 1 else self.p2_max_hp
        pct = hp / max_hp if max_hp > 0 else 0
        filled = int(pct * 10)
        color = "🟢" if pct > 0.5 else "🟡" if pct > 0.25 else "🔴"
        return f"{color} [{'█' * filled}{'░' * (10 - filled)}] {hp}/{max_hp}"
    
    def _stamina_bar(self, player_num):
        stam = self.p1_stamina if player_num == 1 else self.p2_stamina
        max_stam = self.p1_max_stamina if player_num == 1 else self.p2_max_stamina
        pct = stam / max_stam if max_stam > 0 else 0
        filled = int(pct * 10)
        return f"[{'█' * filled}{'░' * (10 - filled)}] {stam}/{max_stam}"

# ==================== ИНТЕРФЕЙС БИТВЫ (В ЧАТЕ) ====================
def show_battle_interface(chat_id, message_id, battle, user_id):
    """Показать интерфейс битвы"""
    if not battle.active:
        finish_battle(chat_id, message_id, battle)
        return
    
    player_num = 1 if str(user_id) == battle.p1_id else 2
    
    state_text = battle.get_state_for_player(player_num)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if battle.phase == "attack_select" and player_num == battle.current_player:
        # Показываем выбор атаки
        attacks = battle.get_available_attacks(player_num)
        for attack_id, attack_data in list(attacks.items())[:6]:
            markup.add(types.InlineKeyboardButton(
                f"{attack_data['name']} ({attack_data.get('stamina_cost', 0)}💪)",
                callback_data=f"batk_{attack_id}"
            ))
        
        # Выбор цели
        markup.add(
            types.InlineKeyboardButton("🎯 Голова", callback_data="btarget_head"),
            types.InlineKeyboardButton("👤 Тело", callback_data="btarget_body"),
            types.InlineKeyboardButton("🦵 Ноги", callback_data="btarget_legs")
        )
    
    elif battle.phase == "defense_select" and player_num == battle.defending_player:
        # Показываем выбор защиты
        defenses = battle.get_available_defenses(player_num)
        for def_id, def_data in defenses.items():
            markup.add(types.InlineKeyboardButton(
                f"{def_data['name']} ({def_data.get('stamina_cost', 0)}💪)",
                callback_data=f"bdef_{def_id}"
            ))
        
        # Выбор защищаемой части
        markup.add(
            types.InlineKeyboardButton("🎯 Голова", callback_data="bprotect_head"),
            types.InlineKeyboardButton("👤 Тело", callback_data="bprotect_body"),
            types.InlineKeyboardButton("🦵 Ноги", callback_data="bprotect_legs")
        )
    
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="battle_refresh"))
    
    bot.edit_message_text(state_text[:4000], chat_id, message_id, reply_markup=markup)

# Временное хранилище выборов игроков
pending_actions = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("batk_"))
def handle_attack_select(call):
    user_id = call.from_user.id
    attack_id = call.data[5:]
    
    battle = find_active_battle(user_id)
    if not battle:
        bot.edit_message_text("❌ Битва не найдена", call.message.chat.id, call.message.message_id)
        return
    
    # Сохраняем выбор атаки
    pending_actions[str(user_id)] = {"attack": attack_id}
    bot.answer_callback_query(call.id, "✅ Атака выбрана! Теперь выберите цель.")
    show_battle_interface(call.message.chat.id, call.message.message_id, battle, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("btarget_"))
def handle_target_select(call):
    user_id = call.from_user.id
    target = call.data[8:]
    
    if str(user_id) not in pending_actions or "attack" not in pending_actions[str(user_id)]:
        bot.answer_callback_query(call.id, "❌ Сначала выберите атаку!")
        return
    
    attack_id = pending_actions[str(user_id)]["attack"]
    
    battle = find_active_battle(user_id)
    if not battle:
        bot.edit_message_text("❌ Битва не найдена", call.message.chat.id, call.message.message_id)
        return
    
    player_num = 1 if str(user_id) == battle.p1_id else 2
    result = battle.set_attack(player_num, attack_id, target)
    
    if result.startswith("❌") or result.startswith("Сейчас"):
        bot.answer_callback_query(call.id, result)
        return
    
    del pending_actions[str(user_id)]
    bot.answer_callback_query(call.id, result)
    
    # Если бот, автоматически выбираем защиту
    if battle.p2_id.startswith("bot_") and battle.phase == "defense_select":
        time.sleep(0.5)
        auto_bot_defense(battle, call.message.chat.id, call.message.message_id)
    else:
        show_battle_interface(call.message.chat.id, call.message.message_id, battle, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("bdef_"))
def handle_defense_select(call):
    user_id = call.from_user.id
    defense_id = call.data[5:]
    
    # Сохраняем выбор защиты
    if str(user_id) not in pending_actions:
        pending_actions[str(user_id)] = {}
    pending_actions[str(user_id)]["defense"] = defense_id
    bot.answer_callback_query(call.id, "🛡 Защита выбрана! Теперь выберите часть тела для защиты.")
    
    battle = find_active_battle(user_id)
    if battle:
        show_battle_interface(call.message.chat.id, call.message.message_id, battle, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("bprotect_"))
def handle_protect_select(call):
    user_id = call.from_user.id
    protect = call.data[9:]
    
    if str(user_id) not in pending_actions or "defense" not in pending_actions.get(str(user_id), {}):
        bot.answer_callback_query(call.id, "❌ Сначала выберите тип защиты!")
        return
    
    defense_id = pending_actions[str(user_id)]["defense"]
    
    battle = find_active_battle(user_id)
    if not battle:
        bot.edit_message_text("❌ Битва не найдена", call.message.chat.id, call.message.message_id)
        return
    
    player_num = 1 if str(user_id) == battle.p1_id else 2
    result = battle.set_defense(player_num, defense_id, protect)
    
    if result.startswith("❌") or result.startswith("Сейчас"):
        bot.answer_callback_query(call.id, result)
        return
    
    del pending_actions[str(user_id)]
    bot.answer_callback_query(call.id, result)
    
    show_battle_interface(call.message.chat.id, call.message.message_id, battle, user_id)

def auto_bot_defense(battle, chat_id, message_id):
    """Автоматический выбор защиты ботом"""
    if battle.phase == "defense_select" and battle.p2_id.startswith("bot_"):
        defenses = battle.get_available_defenses(2)
        if defenses:
            defense_id = random.choice(list(defenses.keys()))
            protect = random.choice(list(BODY_PARTS.keys()))
            battle.set_defense(2, defense_id, protect)
            show_battle_interface(chat_id, message_id, battle, battle.p1_id)

def auto_bot_attack(battle, chat_id, message_id):
    """Автоматический выбор атаки ботом"""
    if battle.phase == "attack_select" and battle.p2_id.startswith("bot_") and battle.current_player == 2:
        attacks = battle.get_available_attacks(2)
        if attacks:
            attack_id = random.choice(list(attacks.keys()))
            target = random.choice(list(BODY_PARTS.keys()))
            battle.set_attack(2, attack_id, target)
            
            # Авто-защита для игрока
            time.sleep(0.5)
            show_battle_interface(chat_id, message_id, battle, battle.p1_id)

# ==================== БЫСТРАЯ ДУЭЛЬ ====================
@bot.callback_query_handler(func=lambda call: call.data == "quick_duel")
def quick_duel_menu(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    for bet in [50, 100, 200, 500, 1000, 5000]:
        markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"qduel_{bet}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
    
    bot.edit_message_text(
        f"<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n💰 Баланс: <b>{player.data['money']}💰</b>\nВыберите ставку:",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def start_quick_duel(call):
    user_id = call.from_user.id
    bet = int(call.data.split("_")[1])
    player = Player(user_id)
    
    if player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Недостаточно монет!")
        return
    
    # Создание бота
    bot_level = random.randint(max(1, player.data["level"] - 5), player.data["level"] + 5)
    bot_id = f"bot_{random.randint(100000, 999999)}"
    
    users[bot_id] = generate_bot(bot_level)
    save_json(DATA_FILES['users'], users)
    
    player.data["money"] -= bet
    player.save()
    
    # Создание битвы
    battle = AdvancedBattle(user_id, bot_id, "quick", bet)
    
    bot.edit_message_text("⚔ Битва начинается!", call.message.chat.id, call.message.message_id)
    show_battle_interface(call.message.chat.id, call.message.message_id, battle, user_id)

def generate_bot(level):
    """Генерация бота с экипировкой"""
    equipment = {"weapon": None, "head": None, "body": None, "legs": None, "accessory": None}
    
    for slot in ["weapon", "head", "body", "legs"]:
        slot_type = {"weapon": "weapon", "head": "helmet", "body": "chest", "legs": "legs"}[slot]
        slot_items = [k for k, v in items.items() if v.get("type") == slot_type and v.get("level_req", 1) <= level]
        if slot_items and random.random() < 0.6:
            equipment[slot] = random.choice(slot_items)
    
    return {
        "username": f"Bot_{level}",
        "first_name": f"🤖 Бот Lv.{level}",
        "money": 0, "level": level, "exp": 0, "total_exp": 0,
        "hp": 100 + level * 12, "max_hp": 100 + level * 12,
        "stamina": 100 + level * 5, "max_stamina": 100 + level * 5,
        "mana": 50 + level * 6, "max_mana": 50 + level * 6,
        "stats": {
            "strength": 5 + level, "agility": 5 + level // 2,
            "intelligence": 5 + level // 3, "vitality": 5 + level // 2,
            "luck": 3 + level // 4
        },
        "stat_points": 0, "wins": 0, "losses": 0, "draws": 0,
        "win_streak": 0, "best_streak": 0, "total_duels": 0,
        "pvp_rating": 1000 + level * 10,
        "total_damage_dealt": 0, "total_damage_taken": 0,
        "critical_hits": 0, "skills_used": 0,
        "inventory": [], "equipment": equipment,
        "last_daily": None, "last_dungeon": None, "last_work": None,
        "title": "Бот", "titles_collected": ["Бот"],
        "achievements": [], "active_quests": {}, "completed_quests": 0,
        "clan": None, "clan_role": None, "tournament_wins": 0,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [],
        "dungeons_completed": 0, "items_found": 0,
        "defense_stance": {"head": 0, "body": 0, "legs": 0}
    }

def find_active_battle(user_id):
    """Найти активную битву"""
    uid = str(user_id)
    for battle_id, data in list(active_duels.items()):
        if uid in [str(data.get("p1_id")), str(data.get("p2_id"))]:
            return AdvancedBattle(data["p1_id"], data["p2_id"], data.get("type", "quick"), data.get("bet", 0))
    return None

def finish_battle(chat_id, message_id, battle):
    """Завершение битвы"""
    for bid in list(active_duels.keys()):
        if bid == battle.battle_id:
            del active_duels[bid]
    save_json(DATA_FILES['duels'], active_duels)
    
    # Удаление ботов
    for uid in [battle.p1_id, battle.p2_id]:
        if uid.startswith("bot_"):
            if uid in users:
                del users[uid]
    save_json(DATA_FILES['users'], users)
    
    if battle.winner == 0:
        result_text = "<b>🤝 НИЧЬЯ!</b>"
        p1 = Player(battle.p1_id)
        p2 = Player(battle.p2_id)
        if battle.bet > 0:
            p1.data["money"] += battle.bet
            p2.data["money"] += battle.bet
        p1.data["draws"] += 1
        p2.data["draws"] += 1
        p1.save()
        p2.save()
        bot.edit_message_text(result_text, chat_id, message_id)
        return
    
    winner_num = battle.winner
    winner_id = battle.p1_id if winner_num == 1 else battle.p2_id
    loser_id = battle.p2_id if winner_num == 1 else battle.p1_id
    
    winner = Player(winner_id)
    loser = Player(loser_id)
    
    if battle.bet > 0:
        reward = battle.bet * 2
        winner.data["money"] += reward
    
    winner.data["wins"] += 1
    winner.data["win_streak"] += 1
    winner.data["total_duels"] += 1
    winner.data["pvp_rating"] += random.randint(20, 35)
    
    if winner.data["win_streak"] > winner.data["best_streak"]:
        winner.data["best_streak"] = winner.data["win_streak"]
    
    loser.data["losses"] += 1
    loser.data["win_streak"] = 0
    loser.data["total_duels"] += 1
    loser.data["pvp_rating"] = max(0, loser.data["pvp_rating"] - random.randint(10, 25))
    
    exp_winner = battle.turn * 10 + battle.bet // 2
    exp_loser = battle.turn * 5 + battle.bet // 5
    
    winner.data["exp"] += exp_winner
    winner.data["total_exp"] += exp_winner
    loser.data["exp"] += exp_loser
    loser.data["total_exp"] += exp_loser
    
    check_level_up(winner)
    check_level_up(loser)
    
    winner.save()
    loser.save()
    
    result_text = f"""
<b>⚔ БИТВА ЗАВЕРШЕНА!</b>

👑 Победитель: <b>{winner.data['first_name']}</b>
💰 Приз: <b>{battle.bet * 2 if battle.bet > 0 else 0}💰</b>
📊 Ходов: <b>{battle.turn}</b>
"""
    bot.edit_message_text(result_text, chat_id, message_id)

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

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    if str(user_id) in banned_users:
        ban = banned_users[str(user_id)]
        bot.send_message(message.chat.id, f"⛔ Вы забанены!\nПричина: {ban.get('reason', 'Нет')}")
        return
    
    username = message.from_user.username or f"user_{user_id}"
    first_name = message.from_user.first_name or "Игрок"
    
    player = Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v7.0 ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

🎯 <b>НОВАЯ БОЕВАЯ СИСТЕМА:</b>
• Выбирайте атаку и часть тела для удара!
• Защищайте голову, тело или ноги!
• У каждого оружия свои уникальные атаки!
• Система стамины и состояний!
• Пошаговые дуэли в чате!

💰 Стартовый бонус: <b>500 монет</b>
⚡ Полная экипировка по 5 слотам!

<i>Выбирайте раздел:</i>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль", callback_data="quick_duel"),
        types.InlineKeyboardButton("👥 PvP дуэль", callback_data="pvp_duel"),
        types.InlineKeyboardButton("🏆 Рейтинговая", callback_data="ranked_duel"),
        types.InlineKeyboardButton("💀 Хардкор", callback_data="hardcore_duel"),
        types.InlineKeyboardButton("🔥 На выживание", callback_data="survival_duel"),
        types.InlineKeyboardButton("🎯 Спарринг", callback_data="sparring_duel")
    )
    bot.send_message(message.chat.id, "<b>⚔️ РАЗДЕЛ ДУЭЛЕЙ</b>\nВыберите тип:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="hero_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="hero_inventory"),
        types.InlineKeyboardButton("⚡ Характеристики", callback_data="hero_attributes"),
        types.InlineKeyboardButton("🏅 Достижения", callback_data="hero_achievements"),
        types.InlineKeyboardButton("📜 Квесты", callback_data="hero_quests"),
        types.InlineKeyboardButton("⚙ Настройки", callback_data="hero_settings"),
        types.InlineKeyboardButton("📋 История боёв", callback_data="hero_history"),
        types.InlineKeyboardButton("💊 Лечение", callback_data="hero_heal")
    )
    bot.send_message(message.chat.id, "<b>👤 МЕНЮ ГЕРОЯ</b>", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🏪 Торговля")
def trade_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛒 Магазин", callback_data="trade_shop"),
        types.InlineKeyboardButton("💎 Лимитированные", callback_data="trade_limited"),
        types.InlineKeyboardButton("🎁 Бонус", callback_data="trade_daily"),
        types.InlineKeyboardButton("💱 Рынок", callback_data="trade_market"),
        types.InlineKeyboardButton("💰 Продать", callback_data="trade_sell"),
        types.InlineKeyboardButton("📦 Мои лоты", callback_data="trade_my_lots"),
        types.InlineKeyboardButton("💼 Работа", callback_data="trade_work"),
        types.InlineKeyboardButton("📊 Курс", callback_data="trade_exchange")
    )
    bot.send_message(message.chat.id, "<b>🏪 ТОРГОВЛЯ</b>", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🌍 Мир")
def world_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🏰 Подземелья", callback_data="world_dungeons"),
        types.InlineKeyboardButton("🛡 Кланы", callback_data="world_clans"),
        types.InlineKeyboardButton("🏟 Турниры", callback_data="world_tournaments"),
        types.InlineKeyboardButton("📊 Топ", callback_data="world_top"),
        types.InlineKeyboardButton("🌍 События", callback_data="world_events"),
        types.InlineKeyboardButton("ℹ Помощь", callback_data="world_help")
    )
    bot.send_message(message.chat.id, "<b>🌍 МИР</b>", reply_markup=markup)

# ==================== ОБРАБОТЧИКИ МАГАЗИНА (с учётом слотов) ====================
@bot.callback_query_handler(func=lambda call: call.data == "trade_shop")
def shop_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚔ Оружие", callback_data="shopcat_weapon"),
        types.InlineKeyboardButton("🎩 Шлемы", callback_data="shopcat_helmet"),
        types.InlineKeyboardButton("🧥 Нагрудники", callback_data="shopcat_chest"),
        types.InlineKeyboardButton("👖 Поножи", callback_data="shopcat_legs"),
        types.InlineKeyboardButton("📿 Аксессуары", callback_data="shopcat_accessory"),
        types.InlineKeyboardButton("🧪 Зелья", callback_data="shopcat_potion")
    )
    
    user = Player(call.from_user.id)
    bot.edit_message_text(
        f"<b>🛒 МАГАЗИН</b>\n💰 Баланс: <b>{user.data['money']}💰</b>\nВыберите категорию:",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("shopcat_"))
def shop_category(call):
    category = call.data.split("_")[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    cat_names = {
        "weapon": "⚔ ОРУЖИЕ", "helmet": "🎩 ШЛЕМЫ", "chest": "🧥 НАГРУДНИКИ",
        "legs": "👖 ПАНОЖИ", "accessory": "📿 АКСЕССУАРЫ", "potion": "🧪 ЗЕЛЬЯ"
    }
    
    cat_items = {k: v for k, v in items.items() if v.get("type") == category.replace("helmet", "helmet").replace("chest", "chest").replace("legs", "legs")}
    
    shop_text = f"<b>{cat_names.get(category, category)}</b>\n💰 {player.data['money']} | Ур.{player.data['level']}\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, item in sorted(cat_items.items(), key=lambda x: x[1].get("price", 0)):
        if player.data["level"] < item.get("level_req", 1):
            continue
        
        rarity = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
        
        if item["type"] == "weapon":
            stats = f"Урон: {item['damage'][0]}-{item['damage'][1]}"
        elif item["type"] in ["helmet", "chest", "legs"]:
            stats = f"Защита: {item.get('defense', 0)}"
        elif item["type"] == "potion":
            stats = f"Лечение: {item.get('heal', 0)}"
        else:
            stats = item.get("description", "")
        
        shop_text += f"{rarity} <b>{item['name']}</b>\n   {stats} | 💰 {item['price']}\n\n"
        
        if player.data["money"] >= item["price"]:
            markup.add(types.InlineKeyboardButton(
                f"Купить {item['name']} - {item['price']}💰",
                callback_data=f"buyitem_{item_key}"
            ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="trade_shop"))
    bot.edit_message_text(shop_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buyitem_"))
def buy_item(call):
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
            bot.answer_callback_query(call.id, "❌ Закончился!")
            return
        limited_items[item_key]["remaining"] -= 1
        save_json(DATA_FILES['limited'], limited_items)
    
    player.data["money"] -= item["price"]
    player.data["inventory"].append(item_key)
    player.data["items_found"] += 1
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ Куплено: {item['name']}!")
    shop_category(call)

# ==================== ИНВЕНТАРЬ С ЭКИПИРОВКОЙ ПО СЛОТАМ ====================
@bot.callback_query_handler(func=lambda call: call.data == "hero_inventory")
def hero_inventory(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if not player.data["inventory"]:
        bot.edit_message_text("🎒 Инвентарь пуст", call.message.chat.id, call.message.message_id)
        return
    
    # Показываем экипировку
    text = "<b>⚔ ЭКИПИРОВКА:</b>\n"
    slots = {
        "weapon": "⚔ Оружие",
        "head": "🎩 Голова",
        "body": "🧥 Тело",
        "legs": "👖 Ноги",
        "accessory": "📿 Аксессуар"
    }
    
    for slot, slot_name in slots.items():
        item_key = player.data["equipment"].get(slot)
        if item_key:
            item = items.get(item_key) or limited_items.get(item_key)
            text += f"{slot_name}: {item['name'] if item else 'Нет'}\n"
        else:
            text += f"{slot_name}: ❌ Нет\n"
    
    text += "\n<b>🎒 ИНВЕНТАРЬ:</b>\n"
    
    item_counts = {}
    for ik in player.data["inventory"]:
        item_counts[ik] = item_counts.get(ik, 0) + 1
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    idx = 1
    
    for item_key, count in item_counts.items():
        item = items.get(item_key) or limited_items.get(item_key)
        if not item:
            continue
        
        rarity = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
        text += f"{idx}. {rarity} {item['name']} x{count}\n"
        
        # Определяем слот для экипировки
        slot = item.get("slot")
        if slot:
            markup.add(types.InlineKeyboardButton(
                f"Экипировать: {item['name']}",
                callback_data=f"equip_{item_key}"
            ))
        elif item["type"] == "potion":
            markup.add(types.InlineKeyboardButton(
                f"Использовать: {item['name']}",
                callback_data=f"use_{item_key}"
            ))
        
        idx += 1
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
def equip_item(call):
    item_key = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(item_key) or limited_items.get(item_key)
    if not item:
        bot.answer_callback_query(call.id, "❌ Предмет не найден!")
        return
    
    slot = item.get("slot")
    if not slot:
        bot.answer_callback_query(call.id, "❌ Нельзя экипировать!")
        return
    
    if item_key not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌ Нет в инвентаре!")
        return
    
    # Снимаем старый предмет
    old = player.data["equipment"].get(slot)
    if old:
        player.data["inventory"].append(old)
    
    player.data["equipment"][slot] = item_key
    player.data["inventory"].remove(item_key)
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ {item['name']} экипирован!")
    hero_inventory(call)

@bot.callback_query_handler(func=lambda call: call.data == "hero_attributes")
def hero_attributes(call):
    user_id = call.from_user.id
    player = Player(user_id)
    stats = player.data["stats"]
    pts = player.data["stat_points"]
    
    text = f"""
<b>⚡ ХАРАКТЕРИСТИКИ</b>
Очков: <b>{pts}</b>

💪 Сила: <b>{stats['strength']}</b> (+{(stats['strength']-5)*2} к урону)
🏃 Ловкость: <b>{stats['agility']}</b> (+{(stats['agility']-5)*1.5} к скорости)
🧠 Интеллект: <b>{stats['intelligence']}</b> (+{(stats['intelligence']-5)*8} к мане)
❤ Живучесть: <b>{stats['vitality']}</b> (+{(stats['vitality']-5)*15} к HP)
🍀 Удача: <b>{stats['luck']}</b> (+{(stats['luck']-5)*0.5}% крита)
"""
    
    markup = types.InlineKeyboardMarkup(row_width=5)
    if pts > 0:
        markup.add(
            types.InlineKeyboardButton("💪", callback_data="upstat_str"),
            types.InlineKeyboardButton("🏃", callback_data="upstat_agi"),
            types.InlineKeyboardButton("🧠", callback_data="upstat_int"),
            types.InlineKeyboardButton("❤", callback_data="upstat_vit"),
            types.InlineKeyboardButton("🍀", callback_data="upstat_luk")
        )
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("upstat_"))
def upgrade_stat(call):
    stat_map = {"str": "strength", "agi": "agility", "int": "intelligence", "vit": "vitality", "luk": "luck"}
    stat_key = stat_map[call.data.split("_")[1]]
    
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data["stat_points"] <= 0:
        bot.answer_callback_query(call.id, "❌ Нет очков!")
        return
    if player.data["stats"][stat_key] >= 100:
        bot.answer_callback_query(call.id, "❌ Максимум!")
        return
    
    player.data["stats"][stat_key] += 1
    player.data["stat_points"] -= 1
    player.save()
    
    names = {"strength": "Сила", "agility": "Ловкость", "intelligence": "Интеллект", "vitality": "Живучесть", "luck": "Удача"}
    bot.answer_callback_query(call.id, f"⬆ {names[stat_key]}: {player.data['stats'][stat_key]}")
    hero_attributes(call)

@bot.callback_query_handler(func=lambda call: call.data == "hero_history")
def hero_history(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    history = player.data.get("battle_history", [])
    if not history:
        bot.edit_message_text("📋 История пуста", call.message.chat.id, call.message.message_id)
        return
    
    text = "<b>📋 ИСТОРИЯ БОЁВ (10)</b>\n\n"
    for battle in history[-10:]:
        icon = "🏆" if battle.get("result") == "win" else "💀"
        text += f"{icon} vs {battle.get('opponent', 'Нет')}\n"
        text += f"   Тип: {battle.get('type', '')} | Ходов: {battle.get('turns', 0)}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_hero")
def back_to_hero(call):
    hero_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_duels")
def back_to_duels(call):
    duel_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "battle_refresh")
def battle_refresh(call):
    user_id = call.from_user.id
    battle = find_active_battle(user_id)
    if battle:
        show_battle_interface(call.message.chat.id, call.message.message_id, battle, user_id)
    else:
        bot.edit_message_text("❌ Битва не найдена", call.message.chat.id, call.message.message_id)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def check_level_up(player):
    level = player.data["level"]
    exp_needed = int(100 * (1.5 ** (level - 1)))
    
    leveled = False
    while player.data["exp"] >= exp_needed:
        player.data["exp"] -= exp_needed
        player.data["level"] += 1
        player.data["stat_points"] += 3
        player.data["max_hp"] += 15
        player.data["max_stamina"] += 8
        player.data["max_mana"] += 8
        player.data["hp"] = player.data["max_hp"]
        player.data["stamina"] = player.data["max_stamina"]
        player.data["mana"] = player.data["max_mana"]
        
        titles = {
            5: "Боец", 10: "Воитель", 15: "Рыцарь", 20: "Ветеран",
            25: "Мастер", 30: "Грандмастер", 40: "Герой", 50: "Легенда",
            60: "Мифический", 75: "Полубог", 100: "Божество"
        }
        
        for req, title in titles.items():
            if player.data["level"] >= req and title not in player.data["titles_collected"]:
                player.data["titles_collected"].append(title)
                player.data["title"] = title
        
        level = player.data["level"]
        exp_needed = int(100 * (1.5 ** (level - 1)))
        leveled = True
    
    return leveled

# ==================== ОБРАБОТЧИКИ КОЛБЭКОВ ДЛЯ МЕНЮ ====================
@bot.callback_query_handler(func=lambda call: call.data == "trade_daily")
def daily_bonus_callback(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player.data.get("last_daily") == today:
        bot.answer_callback_query(call.id, "❌ Уже получен!")
        return
    
    bonus = random.randint(150, 600) + player.data["level"] * 10
    exp = random.randint(80, 250) + player.data["level"] * 5
    
    player.data["money"] += bonus
    player.data["exp"] += exp
    player.data["total_exp"] += exp
    player.data["last_daily"] = today
    
    old_level = player.data["level"]
    check_level_up(player)
    player.save()
    
    text = f"<b>🎁 БОНУС</b>\n💰 +{bonus}\n✨ +{exp}"
    if player.data["level"] > old_level:
        text += f"\n🎉 УРОВЕНЬ {player.data['level']}!"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "trade_work")
def work_callback(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    now = datetime.now()
    if player.data.get("last_work"):
        last = datetime.fromisoformat(player.data["last_work"])
        if (now - last) < timedelta(hours=1):
            remaining = timedelta(hours=1) - (now - last)
            bot.answer_callback_query(call.id, f"⏰ Ждите {remaining.seconds//60} мин.")
            return
    
    reward = random.randint(80, 250) + player.data["level"] * 10
    exp = random.randint(30, 100) + player.data["level"] * 5
    
    player.data["money"] += reward
    player.data["exp"] += exp
    player.data["last_work"] = now.isoformat()
    
    old_level = player.data["level"]
    check_level_up(player)
    player.save()
    
    text = f"<b>💼 РАБОТА</b>\n💰 +{reward}\n✨ +{exp}"
    if player.data["level"] > old_level:
        text += f"\n🎉 УРОВЕНЬ {player.data['level']}!"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

# ==================== ЗАПУСК БОТА ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v7.0 — ПОЛНАЯ БОЕВАЯ СИСТЕМА ⚔️")
    print("=" * 60)
    print(f"🕒 Запуск: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print(f"⚔ Предметов: {len(items)}")
    print(f"💎 Лимитированных: {len(limited_items)}")
    print("=" * 60)
    print("✅ УЛУЧШЕННАЯ БОЕВАЯ СИСТЕМА АКТИВНА!")
    print("✅ ВЫБОР АТАКИ, ЦЕЛИ И ЗАЩИТЫ!")
    print("✅ УНИКАЛЬНЫЕ АТАКИ ДЛЯ КАЖДОГО ОРУЖИЯ!")
    print("✅ ЭКИПИРОВКА ПО 5 СЛОТАМ!")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
