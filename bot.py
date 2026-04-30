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
from enum import Enum

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = '8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE'
ADMIN_ID = 5356400377
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ==================== ENUM КЛАССЫ ====================
class ActionType(Enum):
    ATTACK = "attack"
    HEAVY_ATTACK = "heavy_attack"
    QUICK_ATTACK = "quick_attack"
    DEFEND = "defend"
    COUNTER = "counter"
    HEAL = "heal"
    SPECIAL = "special"
    ULTIMATE = "ultimate"
    USE_ITEM = "use_item"
    CHARGE = "charge"
    DODGE = "dodge"
    PARRY = "parry"

class DuelPhase(Enum):
    WAITING = "waiting"
    PREPARATION = "preparation"
    ACTION_SELECT = "action_select"
    EXECUTION = "execution"
    RESULT = "result"
    FINISHED = "finished"

class Element(Enum):
    FIRE = "🔥"
    ICE = "❄"
    LIGHTNING = "⚡"
    WATER = "🌊"
    EARTH = "🌍"
    WIND = "💨"
    LIGHT = "✨"
    DARK = "🌑"
    POISON = "☠"
    HOLY = "👼"
    CHAOS = "🌀"
    VOID = "🕳"

class StatusEffect(Enum):
    BURN = ("Горение", "🔥", "damage_over_time", 3)
    FREEZE = ("Заморозка", "❄", "skip_turn", 2)
    POISON = ("Отравление", "☠", "damage_over_time", 4)
    BLEED = ("Кровотечение", "🩸", "damage_over_time", 3)
    STUN = ("Оглушение", "💫", "skip_turn", 1)
    SHIELD = ("Щит", "🛡", "damage_reduction", 2)
    BLESS = ("Благословение", "✨", "heal_over_time", 3)
    CURSE = ("Проклятие", "😈", "stat_reduction", 3)
    BERSERK = ("Берсерк", "💢", "damage_boost", 2)
    INVISIBLE = ("Невидимость", "👻", "dodge_boost", 2)

# ==================== ФАЙЛЫ ДАННЫХ ====================
DATA_FILES = {
    'users': 'users.json',
    'items': 'items.json',
    'limited': 'limited_items.json',
    'duels': 'active_duels.json',
    'clans': 'clans.json',
    'market': 'market.json',
    'dungeons': 'dungeons.json',
    'events': 'events.json',
    'bans': 'bans.json',
    'active_battles': 'active_battles.json'
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

# ==================== ПРЕДМЕТЫ И ЭКИПИРОВКА ====================
WEAPONS = {
    "rusty_sword": {
        "name": "🗡 Ржавый меч", "damage": (5, 10), "price": 80,
        "type": "weapon", "rarity": "common", "level_req": 1,
        "actions_unlock": [ActionType.ATTACK.value, ActionType.DEFEND.value],
        "element": None, "crit_bonus": 0, "speed_penalty": 0,
        "description": "Старый меч для начинающих"
    },
    "hunter_bow": {
        "name": "🏹 Лук охотника", "damage": (8, 14), "price": 200,
        "type": "weapon", "rarity": "common", "level_req": 3,
        "actions_unlock": [ActionType.ATTACK.value, ActionType.QUICK_ATTACK.value],
        "element": None, "crit_bonus": 5, "speed_penalty": 0,
        "description": "Быстрые выстрелы"
    },
    "flame_blade": {
        "name": "🔥 Пламенный меч", "damage": (12, 20), "price": 500,
        "type": "weapon", "rarity": "uncommon", "level_req": 7,
        "actions_unlock": [ActionType.ATTACK.value, ActionType.HEAVY_ATTACK.value],
        "element": Element.FIRE.value, "crit_bonus": 0, "speed_penalty": 5,
        "description": "Наносит урон огнём",
        "effects": {"burn_chance": 20}
    },
    "frost_axe": {
        "name": "❄ Ледяной топор", "damage": (15, 25), "price": 800,
        "type": "weapon", "rarity": "uncommon", "level_req": 10,
        "actions_unlock": [ActionType.ATTACK.value, ActionType.HEAVY_ATTACK.value, ActionType.COUNTER.value],
        "element": Element.ICE.value, "crit_bonus": 0, "speed_penalty": 10,
        "description": "Замораживает противников",
        "effects": {"freeze_chance": 15}
    },
    "storm_spear": {
        "name": "⚡ Копьё бурь", "damage": (18, 30), "price": 1500,
        "type": "weapon", "rarity": "rare", "level_req": 15,
        "actions_unlock": [ActionType.ATTACK.value, ActionType.QUICK_ATTACK.value, 
                          ActionType.COUNTER.value],
        "element": Element.LIGHTNING.value, "crit_bonus": 10, "speed_penalty": 0,
        "description": "Молниеносные атаки",
        "effects": {"stun_chance": 10, "chain_lightning": 0.3}
    },
    "shadow_dagger": {
        "name": "🌑 Теневой кинжал", "damage": (20, 35), "price": 3000,
        "type": "weapon", "rarity": "epic", "level_req": 20,
        "actions_unlock": [ActionType.ATTACK.value, ActionType.QUICK_ATTACK.value,
                          ActionType.DODGE.value, ActionType.COUNTER.value],
        "element": Element.DARK.value, "crit_bonus": 15, "speed_penalty": -5,
        "description": "Атаки из тени",
        "effects": {"poison_chance": 20, "backstab_bonus": 25}
    },
    "divine_blade": {
        "name": "✨ Божественный меч", "damage": (25, 45), "price": 7000,
        "type": "weapon", "rarity": "legendary", "level_req": 30,
        "actions_unlock": [ActionType.ATTACK.value, ActionType.HEAVY_ATTACK.value,
                          ActionType.SPECIAL.value, ActionType.COUNTER.value],
        "element": Element.LIGHT.value, "crit_bonus": 10, "speed_penalty": 0,
        "description": "Священная мощь",
        "effects": {"bless_chance": 20, "holy_damage": 0.2}
    },
    "chaos_blade": {
        "name": "🌀 Клинок хаоса", "damage": (30, 55), "price": 15000,
        "type": "weapon", "rarity": "mythic", "level_req": 40,
        "actions_unlock": [ActionType.ATTACK.value, ActionType.HEAVY_ATTACK.value,
                          ActionType.QUICK_ATTACK.value, ActionType.SPECIAL.value,
                          ActionType.COUNTER.value, ActionType.ULTIMATE.value],
        "element": Element.CHAOS.value, "crit_bonus": 20, "speed_penalty": -10,
        "description": "Непредсказуемая мощь хаоса",
        "effects": {"random_effect": True, "chaos_bolt": 0.25}
    }
}

SHIELDS = {
    "wooden_shield": {
        "name": "🛡 Деревянный щит", "defense": 5, "block_chance": 10,
        "price": 100, "type": "shield", "rarity": "common", "level_req": 1,
        "actions_unlock": [ActionType.DEFEND.value],
        "description": "Базовая защита",
        "effects": {}
    },
    "iron_shield": {
        "name": "🛡 Железный щит", "defense": 12, "block_chance": 18,
        "price": 400, "type": "shield", "rarity": "uncommon", "level_req": 8,
        "actions_unlock": [ActionType.DEFEND.value, ActionType.COUNTER.value],
        "description": "Надёжная защита",
        "effects": {"counter_damage": 10}
    },
    "mirror_shield": {
        "name": "🪞 Зеркальный щит", "defense": 20, "block_chance": 25,
        "price": 1200, "type": "shield", "rarity": "rare", "level_req": 15,
        "actions_unlock": [ActionType.DEFEND.value, ActionType.COUNTER.value,
                          ActionType.PARRY.value],
        "description": "Отражает магию",
        "effects": {"magic_reflect": 20}
    },
    "dragon_shield": {
        "name": "🐉 Щит дракона", "defense": 30, "block_chance": 35,
        "price": 3500, "type": "shield", "rarity": "epic", "level_req": 25,
        "actions_unlock": [ActionType.DEFEND.value, ActionType.COUNTER.value,
                          ActionType.PARRY.value, ActionType.SPECIAL.value],
        "description": "Чешуя древнего дракона",
        "effects": {"fire_resist": 30, "thorns": 15}
    }
}

ARMORS = {
    "leather_armor": {
        "name": "🧥 Кожаная броня", "defense": 3, "hp_bonus": 20,
        "price": 70, "type": "armor", "rarity": "common", "level_req": 1,
        "description": "Лёгкая защита",
        "effects": {"dodge_bonus": 3}
    },
    "chainmail": {
        "name": "⛓ Кольчуга", "defense": 8, "hp_bonus": 40,
        "price": 350, "type": "armor", "rarity": "uncommon", "level_req": 8,
        "description": "Надёжная кольчуга",
        "effects": {"physical_resist": 10}
    },
    "plate_armor": {
        "name": "🛡 Латный доспех", "defense": 15, "hp_bonus": 70,
        "price": 1000, "type": "armor", "rarity": "rare", "level_req": 15,
        "description": "Тяжёлая броня",
        "effects": {"damage_reduction": 8}
    },
    "shadow_armor": {
        "name": "🌑 Теневая броня", "defense": 20, "hp_bonus": 100,
        "price": 3000, "type": "armor", "rarity": "epic", "level_req": 22,
        "description": "Скрытность и защита",
        "effects": {"dodge_bonus": 10, "shadow_step": 15}
    },
    "phoenix_armor": {
        "name": "🦅 Броня феникса", "defense": 30, "hp_bonus": 180,
        "price": 8000, "type": "armor", "rarity": "legendary", "level_req": 30,
        "description": "Возрождение из пепла",
        "effects": {"rebirth": 1, "fire_heal": 25}
    }
}

ACCESSORIES = {
    "strength_ring": {
        "name": "💍 Кольцо силы", "bonus_type": "strength", "bonus_value": 5,
        "price": 600, "type": "accessory", "rarity": "uncommon", "level_req": 5,
        "description": "+5 к силе",
        "effects": {"min_damage_boost": 3}
    },
    "crit_amulet": {
        "name": "📿 Амулет крита", "bonus_type": "crit", "bonus_value": 10,
        "price": 1500, "type": "accessory", "rarity": "rare", "level_req": 15,
        "description": "+10% к шансу крита",
        "effects": {"crit_chance_boost": 10}
    },
    "berserker_ring": {
        "name": "💢 Кольцо берсерка", "bonus_type": "berserk", "bonus_value": 20,
        "price": 4000, "type": "accessory", "rarity": "epic", "level_req": 25,
        "description": "Ярость в бою",
        "effects": {"low_hp_boost": 30}
    }
}

POTIONS = {
    "health_potion": {
        "name": "🧪 Зелье здоровья", "heal": 35, "price": 50,
        "type": "potion", "rarity": "common", "level_req": 1,
        "description": "Восстанавливает 35 HP"
    },
    "big_potion": {
        "name": "🧪 Большое зелье", "heal": 80, "price": 150,
        "type": "potion", "rarity": "uncommon", "level_req": 8,
        "description": "Восстанавливает 80 HP"
    },
    "elixir": {
        "name": "💊 Эликсир", "heal": 200, "price": 400,
        "type": "potion", "rarity": "rare", "level_req": 15,
        "description": "Мощное исцеление"
    },
    "berserk_potion": {
        "name": "💢 Зелье ярости", "heal": 0, "price": 250,
        "type": "potion", "rarity": "rare", "level_req": 12,
        "description": "Удваивает урон на 3 хода",
        "effects": {"berserk_effect": True, "duration": 3}
    }
}

BOOTS = {
    "leather_boots": {
        "name": "👢 Кожаные сапоги", "speed": 5, "price": 120,
        "type": "boots", "rarity": "common", "level_req": 1,
        "description": "+5 к скорости"
    },
    "wind_boots": {
        "name": "🌪 Сапоги ветра", "speed": 15, "price": 800,
        "type": "boots", "rarity": "rare", "level_req": 12,
        "description": "+15 к скорости",
        "effects": {"dodge_bonus": 5}
    },
    "hermes_boots": {
        "name": "👟 Сандалии Гермеса", "speed": 30, "price": 5000,
        "type": "boots", "rarity": "legendary", "level_req": 30,
        "description": "Скорость бога",
        "effects": {"first_strike": True, "double_action": 20}
    }
}

LIMITED_ITEMS = {
    "thunderfury": {
        "name": "⚡ Ярость грома", "damage": (50, 90), "total": 3, "remaining": 3,
        "price": 50000, "type": "weapon", "rarity": "divine",
        "element": Element.LIGHTNING.value,
        "actions_unlock": [a.value for a in ActionType],
        "description": "Легендарное оружие бога грома",
        "effects": {"chain_lightning": 0.5, "thunderstorm": 25, "stun_chance": 30}
    },
    "apocalypse": {
        "name": "🌋 Апокалипсис", "damage": (80, 150), "total": 1, "remaining": 1,
        "price": 100000, "type": "weapon", "rarity": "apocalyptic",
        "element": Element.VOID.value,
        "actions_unlock": [a.value for a in ActionType],
        "description": "Единственный в мире. Конец всего",
        "effects": {"obliterate": 30, "soul_drain": 0.3, "void_storm": 40}
    }
}

# Сбор всех предметов
ALL_ITEMS = {}
for items_dict in [WEAPONS, SHIELDS, ARMORS, ACCESSORIES, POTIONS, BOOTS]:
    ALL_ITEMS.update(items_dict)

# Загрузка данных
items = load_json(DATA_FILES['items'], ALL_ITEMS)
limited_items = load_json(DATA_FILES['limited'], LIMITED_ITEMS)
users = load_json(DATA_FILES['users'], {})
active_duels = load_json(DATA_FILES['duels'], {})
clans = load_json(DATA_FILES['clans'], {})
market_listings = load_json(DATA_FILES['market'], {})
dungeons = load_json(DATA_FILES['dungeons'], {})
events = load_json(DATA_FILES['events'], {})
banned_users = load_json(DATA_FILES['bans'], {})
active_battles = load_json(DATA_FILES['active_battles'], {})

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
                "hp": 150,
                "max_hp": 150,
                "mana": 50,
                "max_mana": 50,
                "ultimate_charge": 0,
                "max_ultimate": 100,
                "stats": {
                    "strength": 5,
                    "agility": 5,
                    "intelligence": 5,
                    "vitality": 5,
                    "luck": 5
                },
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
                "duels_by_type": {},
                "inventory": [],
                "equipment": {
                    "weapon": None,
                    "shield": None,
                    "armor": None,
                    "accessory": None,
                    "boots": None
                },
                "last_daily": None,
                "last_dungeon": None,
                "title": "Новичок",
                "titles_collected": ["Новичок"],
                "achievements": [],
                "active_effects": [],
                "clan": None,
                "clan_role": None,
                "tournament_wins": 0,
                "registration_date": datetime.now().isoformat(),
                "pvp_rating": 1000,
                "favorite_action": None,
                "battle_history": []
            }
            self.save()
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    def save(self):
        save_json(DATA_FILES['users'], users)
    
    def get_full_stats(self):
        """Полные боевые характеристики"""
        stats = {
            "min_damage": 5,
            "max_damage": 10,
            "defense": 0,
            "hp_bonus": 0,
            "mana_bonus": 0,
            "speed": 0,
            "crit_chance": 5,
            "crit_multiplier": 1.5,
            "dodge_chance": 3,
            "block_chance": 0,
            "life_steal": 0,
            "damage_reflect": 0,
            "heal_bonus": 0,
            "elemental_bonus": {},
            "unlocked_actions": [ActionType.ATTACK.value, ActionType.DEFEND.value],
            "special_effects": [],
            "passive_abilities": []
        }
        
        # Базовые статы от характеристик
        stats["min_damage"] += self.data["stats"]["strength"] * 3
        stats["max_damage"] += self.data["stats"]["strength"] * 5
        stats["speed"] += self.data["stats"]["agility"] * 2
        stats["crit_chance"] += self.data["stats"]["luck"] * 0.8
        
        for slot, item_key in self.data["equipment"].items():
            if not item_key:
                continue
            
            item = items.get(item_key) or limited_items.get(item_key)
            if not item:
                continue
            
            if item["type"] == "weapon":
                if "damage" in item:
                    min_d, max_d = item["damage"]
                    stats["min_damage"] += min_d
                    stats["max_damage"] += max_d
                if "element" in item and item["element"]:
                    stats["elemental_bonus"][item["element"]] = \
                        stats["elemental_bonus"].get(item["element"], 0) + 25
                if "crit_bonus" in item:
                    stats["crit_chance"] += item["crit_bonus"]
                if "speed_penalty" in item:
                    stats["speed"] -= item["speed_penalty"]
                if "actions_unlock" in item:
                    for action in item["actions_unlock"]:
                        if action not in stats["unlocked_actions"]:
                            stats["unlocked_actions"].append(action)
                for effect, value in item.get("effects", {}).items():
                    if effect in ["life_steal", "damage_reflect"]:
                        stats[effect] += value
            
            elif item["type"] == "shield":
                stats["defense"] += item.get("defense", 0)
                stats["block_chance"] += item.get("block_chance", 0)
                if "actions_unlock" in item:
                    for action in item["actions_unlock"]:
                        if action not in stats["unlocked_actions"]:
                            stats["unlocked_actions"].append(action)
            
            elif item["type"] == "armor":
                stats["defense"] += item.get("defense", 0)
                stats["hp_bonus"] += item.get("hp_bonus", 0)
            
            elif item["type"] == "accessory":
                for effect, value in item.get("effects", {}).items():
                    if "crit" in effect:
                        stats["crit_chance"] += value
                    elif "damage" in effect:
                        stats["min_damage"] += value
                        stats["max_damage"] += value * 2
            
            elif item["type"] == "boots":
                stats["speed"] += item.get("speed", 0)
                for effect, value in item.get("effects", {}).items():
                    if "dodge" in effect:
                        stats["dodge_chance"] += value
                    elif effect == "first_strike" and value:
                        stats["passive_abilities"].append("first_strike")
                    elif effect == "double_action" and value:
                        stats["passive_abilities"].append(f"double_action_{value}")
        
        # Ограничения
        stats["crit_chance"] = min(stats["crit_chance"], 75)
        stats["dodge_chance"] = min(stats["dodge_chance"], 45)
        stats["block_chance"] = min(stats["block_chance"], 55)
        stats["speed"] = max(0, stats["speed"])
        
        return stats

# ==================== ПОШАГОВАЯ БОЕВАЯ СИСТЕМА ====================
class TacticalBattle:
    """Полная пошаговая боевая система с выбором действий"""
    
    def __init__(self, player1_id, player2_id, bet=0, duel_type="normal"):
        self.battle_id = f"battle_{int(time.time())}_{random.randint(1000,9999)}"
        self.p1_id = str(player1_id)
        self.p2_id = str(player2_id)
        self.bet = bet
        self.duel_type = duel_type
        
        # Игроки
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        # Полные статы
        self.p1_stats = self.p1.get_full_stats()
        self.p2_stats = self.p2.get_full_stats()
        
        # Боевые параметры
        self.p1_hp = self.p1.data["max_hp"] + self.p1_stats["hp_bonus"]
        self.p2_hp = self.p2.data["max_hp"] + self.p2_stats["hp_bonus"]
        self.p1_max_hp = self.p1_hp
        self.p2_max_hp = self.p2_hp
        
        self.p1_mana = self.p1.data["max_mana"] + self.p1_stats["mana_bonus"]
        self.p2_mana = self.p2.data["max_mana"] + self.p2_stats["mana_bonus"]
        
        self.p1_ultimate = 0
        self.p2_ultimate = 0
        
        # Состояние битвы
        self.phase = DuelPhase.WAITING
        self.turn = 1
        self.max_turns = 30
        self.current_player = None
        self.waiting_for = None
        
        # Действия игроков
        self.p1_action = None
        self.p2_action = None
        
        # Активные эффекты
        self.p1_effects = []
        self.p2_effects = []
        
        # Модификаторы битвы
        self.weather = random.choice(["clear", "rain", "storm", "fog", "eclipse", "blizzard"])
        self.arena = random.choice(["colosseum", "forest", "volcano", "tundra", "void", "temple"])
        
        # История боя
        self.battle_log = []
        self.turn_log = []
        
        # Определение первого хода
        self.p1_speed = self.p1_stats["speed"] + random.randint(-10, 10)
        self.p2_speed = self.p2_stats["speed"] + random.randint(-10, 10)
        
        if "first_strike" in self.p1_stats["passive_abilities"]:
            self.p1_speed += 50
        if "first_strike" in self.p2_stats["passive_abilities"]:
            self.p2_speed += 50
        
        if self.p1_speed >= self.p2_speed:
            self.current_player = 1
            self.waiting_for = self.p1_id
        else:
            self.current_player = 2
            self.waiting_for = self.p2_id
        
        self.phase = DuelPhase.ACTION_SELECT
        
        # Сохранение битвы
        self.save_battle()
    
    def save_battle(self):
        active_battles[self.battle_id] = {
            "battle_id": self.battle_id,
            "p1_id": self.p1_id,
            "p2_id": self.p2_id,
            "bet": self.bet,
            "duel_type": self.duel_type,
            "phase": self.phase.value,
            "turn": self.turn,
            "current_player": self.current_player,
            "waiting_for": self.waiting_for,
            "p1_action": self.p1_action,
            "p2_action": self.p2_action,
            "p1_hp": self.p1_hp,
            "p2_hp": self.p2_hp,
            "p1_max_hp": self.p1_max_hp,
            "p2_max_hp": self.p2_max_hp,
            "p1_mana": self.p1_mana,
            "p2_mana": self.p2_mana,
            "p1_ultimate": self.p1_ultimate,
            "p2_ultimate": self.p2_ultimate,
            "weather": self.weather,
            "arena": self.arena,
            "battle_log": self.battle_log[-10:]
        }
        save_json(DATA_FILES['active_battles'], active_battles)
    
    def get_available_actions(self, player_num):
        """Получение доступных действий для игрока"""
        stats = self.p1_stats if player_num == 1 else self.p2_stats
        mana = self.p1_mana if player_num == 1 else self.p2_mana
        ultimate = self.p1_ultimate if player_num == 1 else self.p2_ultimate
        hp = self.p1_hp if player_num == 1 else self.p2_hp
        max_hp = self.p1_max_hp if player_num == 1 else self.p2_max_hp
        
        actions = []
        
        # Базовые действия
        if ActionType.ATTACK.value in stats["unlocked_actions"]:
            actions.append({
                "id": ActionType.ATTACK.value,
                "name": "⚔ Атака",
                "description": "Базовая атака (100% урона)",
                "mana_cost": 0,
                "damage_mod": 1.0,
                "accuracy": 95
            })
        
        if ActionType.HEAVY_ATTACK.value in stats["unlocked_actions"]:
            actions.append({
                "id": ActionType.HEAVY_ATTACK.value,
                "name": "💥 Тяжёлая атака",
                "description": "Мощный удар (150% урона, -15% точность)",
                "mana_cost": 15,
                "damage_mod": 1.5,
                "accuracy": 80,
                "bonus_effects": ["stun_chance_10"]
            })
        
        if ActionType.QUICK_ATTACK.value in stats["unlocked_actions"]:
            actions.append({
                "id": ActionType.QUICK_ATTACK.value,
                "name": "💨 Быстрая атака",
                "description": "Две быстрые атаки (70% урона каждая)",
                "mana_cost": 10,
                "damage_mod": 0.7,
                "accuracy": 90,
                "hits": 2
            })
        
        if ActionType.DEFEND.value in stats["unlocked_actions"]:
            actions.append({
                "id": ActionType.DEFEND.value,
                "name": "🛡 Защита",
                "description": "Увеличивает защиту на 50% на этот ход",
                "mana_cost": 5,
                "defense_boost": 50,
                "heal": int(max_hp * 0.05)
            })
        
        if ActionType.COUNTER.value in stats["unlocked_actions"]:
            actions.append({
                "id": ActionType.COUNTER.value,
                "name": "↩ Контратака",
                "description": "Отражает 50% урона обратно",
                "mana_cost": 20,
                "counter_damage": 0.5
            })
        
        if ActionType.DODGE.value in stats["unlocked_actions"]:
            actions.append({
                "id": ActionType.DODGE.value,
                "name": "💨 Уклонение",
                "description": "+30% к шансу уклонения на ход",
                "mana_cost": 15,
                "dodge_boost": 30
            })
        
        if ActionType.HEAL.value in stats["unlocked_actions"]:
            heal_amount = int(max_hp * 0.2)
            actions.append({
                "id": ActionType.HEAL.value,
                "name": "💚 Исцеление",
                "description": f"Восстанавливает {heal_amount} HP",
                "mana_cost": 25,
                "heal": heal_amount
            })
        
        if ActionType.SPECIAL.value in stats["unlocked_actions"]:
            actions.append({
                "id": ActionType.SPECIAL.value,
                "name": "✨ Особая атака",
                "description": "Уникальная атака с элементом (200% урона)",
                "mana_cost": 35,
                "damage_mod": 2.0,
                "accuracy": 85,
                "elemental": True
            })
        
        if ActionType.ULTIMATE.value in stats["unlocked_actions"] and ultimate >= 100:
            actions.append({
                "id": ActionType.ULTIMATE.value,
                "name": "🌟 УЛЬТИМАТИВНАЯ",
                "description": "Максимальный урон + все эффекты (300% урона)",
                "mana_cost": 50,
                "damage_mod": 3.0,
                "accuracy": 100,
                "ignore_defense": True,
                "ultimate_required": True
            })
        
        if ActionType.USE_ITEM.value in stats["unlocked_actions"]:
            player = self.p1 if player_num == 1 else self.p2
            potions = [k for k in player.data["inventory"] 
                      if items.get(k, {}).get("type") == "potion"]
            if potions:
                actions.append({
                    "id": ActionType.USE_ITEM.value,
                    "name": "🧪 Зелье",
                    "description": "Использовать зелье из инвентаря",
                    "mana_cost": 0,
                    "available_potions": potions
                })
        
        # Фильтрация по мане
        available = []
        for action in actions:
            mana = self.p1_mana if player_num == 1 else self.p2_mana
            if action["mana_cost"] <= mana:
                available.append(action)
        
        return available
    
    def execute_actions(self):
        """Выполнение действий обоих игроков"""
        if not self.p1_action or not self.p2_action:
            return False
        
        self.battle_log.append(f"\n<b>═══ ХОД {self.turn} ═══</b>")
        
        # Определение очерёдности действий
        actions_order = []
        p1_action_data = self._get_action_data(self.p1_action, 1)
        p2_action_data = self._get_action_data(self.p2_action, 2)
        
        # Проверка скорости действий
        p1_priority = self._get_action_priority(self.p1_action) + self.p1_stats["speed"]
        p2_priority = self._get_action_priority(self.p2_action) + self.p2_stats["speed"]
        
        if p1_priority >= p2_priority:
            actions_order = [(1, self.p1_action), (2, self.p2_action)]
        else:
            actions_order = [(2, self.p2_action), (1, self.p1_action)]
        
        # Выполнение действий
        for player_num, action_id in actions_order:
            self._execute_single_action(player_num, action_id)
            
            # Проверка на смерть
            if self.p1_hp <= 0 or self.p2_hp <= 0:
                break
        
        # Обработка эффектов конца хода
        self._process_end_of_turn_effects()
        
        # Отображение HP
        self._log_hp_status()
        
        # Проверка завершения
        if self.p1_hp <= 0 and self.p2_hp <= 0:
            self.phase = DuelPhase.FINISHED
            return "draw"
        elif self.p1_hp <= 0:
            self.phase = DuelPhase.FINISHED
            return 2  # Победил игрок 2
        elif self.p2_hp <= 0:
            self.phase = DuelPhase.FINISHED
            return 1  # Победил игрок 1
        elif self.turn >= self.max_turns:
            self.phase = DuelPhase.FINISHED
            return "draw"
        
        # Подготовка к следующему ходу
        self.turn += 1
        self.p1_action = None
        self.p2_action = None
        self.p1_mana = min(self.p1.data["max_mana"] + self.p1_stats["mana_bonus"], 
                          self.p1_mana + 10)
        self.p2_mana = min(self.p2.data["max_mana"] + self.p2_stats["mana_bonus"],
                          self.p2_mana + 10)
        
        # Зарядка ульты
        self.p1_ultimate = min(100, self.p1_ultimate + random.randint(15, 25))
        self.p2_ultimate = min(100, self.p2_ultimate + random.randint(15, 25))
        
        # Смена ходящего
        self.current_player = 3 - self.current_player
        self.waiting_for = self.p1_id if self.current_player == 1 else self.p2_id
        self.phase = DuelPhase.ACTION_SELECT
        
        self.save_battle()
        return None  # Бой продолжается
    
    def _execute_single_action(self, player_num, action_id):
        """Выполнение одного действия"""
        attacker = self.p1 if player_num == 1 else self.p2
        defender = self.p2 if player_num == 1 else self.p1
        attacker_stats = self.p1_stats if player_num == 1 else self.p2_stats
        defender_stats = self.p2_stats if player_num == 1 else self.p1_stats
        attacker_hp = self.p1_hp if player_num == 1 else self.p2_hp
        defender_hp = self.p2_hp if player_num == 1 else self.p1_hp
        
        action_data = self._get_action_data(action_id, player_num)
        
        if action_id == ActionType.ATTACK.value:
            damage = self._calculate_damage(attacker_stats, defender_stats, 1.0)
            if self._check_hit(95, attacker_stats, defender_stats):
                self._apply_damage(player_num, 3 - player_num, damage)
                self.battle_log.append(f"⚔ {attacker.data['first_name']} атакует: {damage} урона")
            else:
                self.battle_log.append(f"💨 {attacker.data['first_name']} промахивается!")
        
        elif action_id == ActionType.HEAVY_ATTACK.value:
            if self._check_hit(80, attacker_stats, defender_stats):
                damage = self._calculate_damage(attacker_stats, defender_stats, 1.5)
                self._apply_damage(player_num, 3 - player_num, damage)
                self.battle_log.append(f"💥 {attacker.data['first_name']} наносит ТЯЖЁЛЫЙ УДАР: {damage} урона")
                
                if random.random() < 0.1:
                    self._apply_effect(3 - player_num, "stun", 1)
                    self.battle_log.append(f"💫 {defender.data['first_name']} оглушён!")
            else:
                self.battle_log.append(f"💨 Тяжёлая атака промахивается!")
        
        elif action_id == ActionType.QUICK_ATTACK.value:
            for i in range(2):
                if self._check_hit(90, attacker_stats, defender_stats):
                    damage = self._calculate_damage(attacker_stats, defender_stats, 0.7)
                    self._apply_damage(player_num, 3 - player_num, damage)
                    self.battle_log.append(f"💨 Быстрая атака {i+1}: {damage} урона")
        
        elif action_id == ActionType.DEFEND.value:
            self._apply_effect(player_num, "shield", 1)
            heal = int((self.p1_max_hp if player_num == 1 else self.p2_max_hp) * 0.05)
            if player_num == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self.battle_log.append(f"🛡 {attacker.data['first_name']} защищается (+{heal} HP)")
        
        elif action_id == ActionType.COUNTER.value:
            self._apply_effect(player_num, "counter", 1)
            self.battle_log.append(f"↩ {attacker.data['first_name']} готовит контратаку!")
        
        elif action_id == ActionType.DODGE.value:
            self._apply_effect(player_num, "dodge_boost", 1)
            self.battle_log.append(f"💨 {attacker.data['first_name']} повышает уклонение!")
        
        elif action_id == ActionType.HEAL.value:
            heal = int((self.p1_max_hp if player_num == 1 else self.p2_max_hp) * 0.2)
            if player_num == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self.battle_log.append(f"💚 {attacker.data['first_name']} исцеляется: +{heal} HP")
        
        elif action_id == ActionType.SPECIAL.value:
            if self._check_hit(85, attacker_stats, defender_stats):
                damage = self._calculate_damage(attacker_stats, defender_stats, 2.0, elemental=True)
                self._apply_damage(player_num, 3 - player_num, damage)
                self.battle_log.append(f"✨ {attacker.data['first_name']} использует ОСОБУЮ АТАКУ: {damage} урона")
        
        elif action_id == ActionType.ULTIMATE.value:
            damage = self._calculate_damage(attacker_stats, defender_stats, 3.0, 
                                           ignore_defense=True)
            self._apply_damage(player_num, 3 - player_num, damage)
            if player_num == 1:
                self.p1_ultimate = 0
            else:
                self.p2_ultimate = 0
            self.battle_log.append(f"🌟 {attacker.data['first_name']} использует УЛЬТИМАТИВНУЮ АТАКУ: {damage} урона!")
        
        # Расход маны
        mana_cost = action_data.get("mana_cost", 0)
        if player_num == 1:
            self.p1_mana -= mana_cost
        else:
            self.p2_mana -= mana_cost
        
        # Проверка эффектов оружия
        self._check_weapon_effects(player_num, 3 - player_num)
    
    def _calculate_damage(self, attacker_stats, defender_stats, multiplier, 
                         ignore_defense=False, elemental=False):
        """Расчёт урона с учётом всех модификаторов"""
        base_damage = random.randint(
            int(attacker_stats["min_damage"] * multiplier),
            int(attacker_stats["max_damage"] * multiplier)
        )
        
        # Критический удар
        is_crit = random.random() * 100 < attacker_stats["crit_chance"]
        if is_crit:
            base_damage = int(base_damage * attacker_stats["crit_multiplier"])
        
        # Защита
        if not ignore_defense:
            defense = defender_stats["defense"]
            reduction = defense / (defense + 150)
            base_damage = int(base_damage * (1 - reduction))
        
        # Элементальный бонус
        if elemental and attacker_stats["elemental_bonus"]:
            element = random.choice(list(attacker_stats["elemental_bonus"].keys()))
            bonus = attacker_stats["elemental_bonus"][element]
            base_damage = int(base_damage * (1 + bonus / 100))
        
        # Погодные эффекты
        if self.weather == "storm":
            if random.random() < 0.2:
                base_damage = int(base_damage * 1.3)
                self.battle_log.append("⛈ Буря усиливает атаку!")
        
        # Эффекты арены
        if self.arena == "volcano":
            base_damage = int(base_damage * 1.1)
        elif self.arena == "void":
            if random.random() < 0.15:
                base_damage = int(base_damage * 1.5)
        
        return max(1, base_damage)
    
    def _check_hit(self, base_accuracy, attacker_stats, defender_stats):
        """Проверка попадания"""
        accuracy = base_accuracy
        # Уклонение защитника
        accuracy -= defender_stats["dodge_chance"] * 0.5
        # Ловкость атакующего
        accuracy += attacker_stats["speed"] * 0.2
        
        accuracy = max(10, min(95, accuracy))
        return random.random() * 100 < accuracy
    
    def _apply_damage(self, attacker_num, defender_num, damage):
        """Применение урона с учётом щитов и эффектов"""
        if defender_num == 1:
            # Проверка щита
            if any(e[0] == "shield" for e in self.p1_effects):
                damage = int(damage * 0.5)
                self.battle_log.append("🛡 Щит поглощает половину урона!")
            
            # Проверка уклонения
            if any(e[0] == "dodge_boost" for e in self.p1_effects):
                if random.random() < 0.3:
                    self.battle_log.append("💨 Уклонение! Урон не нанесён")
                    return
            
            # Вампиризм атакующего
            if attacker_num == 2 and self.p2_stats["life_steal"] > 0:
                heal = int(damage * self.p2_stats["life_steal"])
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            
            self.p1_hp -= damage
            
            # Зарядка ульты от получения урона
            self.p1_ultimate = min(100, self.p1_ultimate + int(damage * 0.2))
        else:
            if any(e[0] == "shield" for e in self.p2_effects):
                damage = int(damage * 0.5)
            
            if any(e[0] == "dodge_boost" for e in self.p2_effects):
                if random.random() < 0.3:
                    self.battle_log.append("💨 Уклонение! Урон не нанесён")
                    return
            
            if attacker_num == 1 and self.p1_stats["life_steal"] > 0:
                heal = int(damage * self.p1_stats["life_steal"])
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            
            self.p2_hp -= damage
            self.p2_ultimate = min(100, self.p2_ultimate + int(damage * 0.2))
        
        # Зарядка ульты атакующего
        if attacker_num == 1:
            self.p1_ultimate = min(100, self.p1_ultimate + random.randint(10, 20))
        else:
            self.p2_ultimate = min(100, self.p2_ultimate + random.randint(10, 20))
    
    def _apply_effect(self, player_num, effect_type, duration):
        """Наложение эффекта"""
        if player_num == 1:
            self.p1_effects.append((effect_type, duration))
        else:
            self.p2_effects.append((effect_type, duration))
    
    def _check_weapon_effects(self, attacker_num, defender_num):
        """Проверка эффектов оружия"""
        attacker = self.p1 if attacker_num == 1 else self.p2
        weapon_key = attacker.data["equipment"]["weapon"]
        weapon = items.get(weapon_key) or limited_items.get(weapon_key)
        
        if not weapon or "effects" not in weapon:
            return
        
        effects = weapon["effects"]
        
        for effect, chance in effects.items():
            if isinstance(chance, (int, float)) and chance < 1:
                if random.random() < chance:
                    if "burn" in effect:
                        self._apply_effect(defender_num, "burn", 3)
                        self.battle_log.append("🔥 Горение!")
                    elif "freeze" in effect:
                        self._apply_effect(defender_num, "freeze", 2)
                        self.battle_log.append("❄ Заморозка!")
                    elif "poison" in effect:
                        self._apply_effect(defender_num, "poison", 4)
                        self.battle_log.append("☠ Отравление!")
                    elif "stun" in effect:
                        self._apply_effect(defender_num, "stun", 1)
                        self.battle_log.append("💫 Оглушение!")
    
    def _get_action_data(self, action_id, player_num):
        """Получение данных действия"""
        actions = self.get_available_actions(player_num)
        for action in actions:
            if action["id"] == action_id:
                return action
        return {"mana_cost": 0}
    
    def _get_action_priority(self, action_id):
        """Приоритет действия для определения очерёдности"""
        priorities = {
            ActionType.QUICK_ATTACK.value: 3,
            ActionType.DODGE.value: 3,
            ActionType.ATTACK.value: 2,
            ActionType.COUNTER.value: 2,
            ActionType.SPECIAL.value: 1,
            ActionType.HEAVY_ATTACK.value: 0,
            ActionType.ULTIMATE.value: 0,
            ActionType.DEFEND.value: -1,
            ActionType.HEAL.value: -1
        }
        return priorities.get(action_id, 0)
    
    def _process_end_of_turn_effects(self):
        """Обработка эффектов в конце хода"""
        # Горение/яд/кровотечение
        for effect_list, hp, max_hp in [(self.p1_effects, 'p1_hp', 'p1_max_hp'),
                                         (self.p2_effects, 'p2_hp', 'p2_max_hp')]:
            new_effects = []
            for effect, duration in effect_list:
                if effect == "burn":
                    damage = random.randint(8, 18)
                    setattr(self, hp, max(0, getattr(self, hp) - damage))
                    self.battle_log.append(f"🔥 Горение: -{damage} HP")
                elif effect == "poison":
                    damage = random.randint(5, 15)
                    setattr(self, hp, max(0, getattr(self, hp) - damage))
                    self.battle_log.append(f"☠ Яд: -{damage} HP")
                
                if duration > 1:
                    new_effects.append((effect, duration - 1))
            
            if effect_list is self.p1_effects:
                self.p1_effects = new_effects
            else:
                self.p2_effects = new_effects
    
    def _log_hp_status(self):
        """Отображение статуса HP"""
        p1_bar = self._get_bar(self.p1_hp, self.p1_max_hp)
        p2_bar = self._get_bar(self.p2_hp, self.p2_max_hp)
        
        self.battle_log.append(
            f"❤ {self.p1.data['first_name']}: {p1_bar} {self.p1_hp}/{self.p1_max_hp} "
            f"💎MP:{self.p1_mana} ⚡ULT:{self.p1_ultimate}%"
        )
        self.battle_log.append(
            f"❤ {self.p2.data['first_name']}: {p2_bar} {self.p2_hp}/{self.p2_max_hp} "
            f"💎MP:{self.p2_mana} ⚡ULT:{self.p2_ultimate}%"
        )
    
    def _get_bar(self, current, maximum):
        filled = int((current / maximum) * 10)
        return f"[{'█' * filled}{'░' * (10 - filled)}]"

# ==================== ОБРАБОТЧИКИ ДУЭЛЕЙ ====================
@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_menu_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("⚡ Быстрая дуэль"),
        types.KeyboardButton("👥 Дуэль с игроком"),
        types.KeyboardButton("🏆 Рейтинговая"),
        types.KeyboardButton("💀 Хардкорная"),
        types.KeyboardButton("🎯 Стратегическая"),
        types.KeyboardButton("◀️ Назад")
    )
    
    bot.send_message(message.chat.id, 
        "<b>⚔️ ДУЭЛИ</b>\n\n"
        "🎮 <b>Стратегическая дуэль</b> - полный контроль над боем!\n"
        "• Выбирайте действия каждый ход\n"
        "• Управляйте маной и ультой\n"
        "• Используйте зелья в бою\n\n"
        "<i>Выберите тип дуэли:</i>",
        reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🎯 Стратегическая")
def strategic_duel_start(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Против бота", callback_data="strat_bot"),
        types.InlineKeyboardButton("Против игрока", callback_data="strat_player")
    )
    
    bot.send_message(message.chat.id,
        "<b>🎯 СТРАТЕГИЧЕСКАЯ ДУЭЛЬ</b>\n\n"
        "Полный контроль над каждым ходом!\n\n"
        "<b>Особенности:</b>\n"
        "• Выбор действия каждый ход\n"
        "• Система маны и ультимативных атак\n"
        "• Статус-эффекты и погодные условия\n"
        "• Возможность использовать зелья\n\n"
        "Выберите противника:",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("strat_"))
def start_strategic_duel(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "strat_bot":
        if player.data["money"] < 100:
            bot.answer_callback_query(call.id, "❌ Нужно 100💰")
            return
        
        player.data["money"] -= 100
        
        # Создание бота
        bot_level = random.randint(max(1, player.data["level"] - 3), player.data["level"] + 3)
        bot_id = f"bot_{random.randint(10000, 99999)}"
        
        # Генерация бота
        users[bot_id] = {
            "username": f"Bot_{bot_level}",
            "first_name": f"🤖 Бот Lv.{bot_level}",
            "money": 0, "level": bot_level, "exp": 0, "total_exp": 0,
            "hp": 150 + bot_level * 10, "max_hp": 150 + bot_level * 10,
            "mana": 50 + bot_level * 5, "max_mana": 50 + bot_level * 5,
            "ultimate_charge": 0, "max_ultimate": 100,
            "stats": {
                "strength": 5 + bot_level,
                "agility": 5 + bot_level // 2,
                "intelligence": 5 + bot_level // 3,
                "vitality": 5 + bot_level // 2,
                "luck": 3 + bot_level // 4
            },
            "stat_points": 0,
            "wins": 0, "losses": 0, "win_streak": 0,
            "inventory": [],
            "equipment": {},
            "title": "Бот"
        }
        
        # Выдача оружия боту
        bot_weapons = [k for k, v in items.items() 
                      if v["type"] == "weapon" and v.get("level_req", 1) <= bot_level]
        if bot_weapons:
            users[bot_id]["equipment"]["weapon"] = random.choice(bot_weapons)
        
        player.save()
        
        # Создание битвы
        battle = TacticalBattle(user_id, bot_id, 100, "strategic")
        
        # Показ интерфейса битвы
        show_battle_interface(call.message, battle, user_id)
    
    elif call.data == "strat_player":
        bot.send_message(call.message.chat.id,
            "👥 Для стратегической дуэли с игроком ответьте на его сообщение:\n"
            "/strat_duel [ставка]")

@bot.message_handler(commands=['strat_duel'])
def strat_duel_command(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Ответьте на сообщение игрока!")
        return
    
    user_id = message.from_user.id
    opponent_id = message.reply_to_message.from_user.id
    
    if user_id == opponent_id:
        bot.send_message(message.chat.id, "❌ Нельзя вызвать себя!")
        return
    
    try:
        bet = int(message.text.split()[1]) if len(message.text.split()) > 1 else 200
        bet = max(50, min(5000, bet))
    except:
        bet = 200
    
    player = Player(user_id)
    opponent = Player(opponent_id)
    
    if player.data["money"] < bet:
        bot.send_message(message.chat.id, f"❌ Нужно {bet}💰")
        return
    if opponent.data["money"] < bet:
        bot.send_message(message.chat.id, f"❌ У противника недостаточно монет!")
        return
    
    # Создание запроса на дуэль
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"strat_accept_{user_id}_{bet}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data="strat_decline")
    )
    
    bot.send_message(message.chat.id,
        f"<b>🎯 ВЫЗОВ НА СТРАТЕГИЧЕСКУЮ ДУЭЛЬ!</b>\n\n"
        f"{message.from_user.first_name} вызывает {message.reply_to_message.from_user.first_name}!\n"
        f"Ставка: <b>{bet}💰</b>\n"
        f"Тип: пошаговая с выбором действий",
        reply_markup=markup)

def show_battle_interface(message, battle, player_id):
    """Отображение интерфейса битвы"""
    player_num = 1 if battle.p1_id == str(player_id) else 2
    player_stats = battle.p1_stats if player_num == 1 else battle.p2_stats
    player_hp = battle.p1_hp if player_num == 1 else battle.p2_hp
    player_max_hp = battle.p1_max_hp if player_num == 1 else battle.p2_max_hp
    player_mana = battle.p1_mana if player_num == 1 else battle.p2_mana
    player_ult = battle.p1_ultimate if player_num == 1 else battle.p2_ultimate
    
    opponent_num = 3 - player_num
    opponent = battle.p2 if player_num == 1 else battle.p1
    opponent_hp = battle.p2_hp if player_num == 1 else battle.p1_hp
    opponent_max_hp = battle.p2_max_hp if player_num == 1 else battle.p1_max_hp
    
    # Текст битвы
    hp_bar_self = battle._get_bar(player_hp, player_max_hp)
    hp_bar_opp = battle._get_bar(opponent_hp, opponent_max_hp)
    
    battle_text = f"""
<b>🎯 СТРАТЕГИЧЕСКАЯ ДУЭЛЬ - ХОД {battle.turn}</b>

🌤 Погода: <b>{battle.weather}</b>
🏟 Арена: <b>{battle.arena}</b>

<b>Противник: {opponent.data['first_name']} Lv.{opponent.data['level']}</b>
❤ {hp_bar_opp} {opponent_hp}/{opponent_max_hp}

<b>Вы: {player_hp}/{player_max_hp} HP | 💎{player_mana} MP | ⚡{player_ult}%</b>
❤ {hp_bar_self}

<b>Активные эффекты:</b>
{' '.join([f'{e[0]}({e[1]})' for e in (battle.p1_effects if player_num == 1 else battle.p2_effects)]) or 'Нет'}

<b>История боя:</b>
{chr(10).join(battle.battle_log[-5:])}
"""
    
    # Кнопки действий
    markup = types.InlineKeyboardMarkup(row_width=2)
    available_actions = battle.get_available_actions(player_num)
    
    for action in available_actions[:8]:  # Максимум 8 кнопок
        button_text = f"{action['name']}"
        if action['mana_cost'] > 0:
            button_text += f" ({action['mana_cost']}MP)"
        markup.add(types.InlineKeyboardButton(
            button_text, 
            callback_data=f"battle_{battle.battle_id}_{action['id']}"
        ))
    
    # Отправка или редактирование
    if hasattr(message, 'message_id'):
        try:
            bot.edit_message_text(battle_text, message.chat.id, message.message_id, reply_markup=markup)
        except:
            bot.send_message(message.chat.id, battle_text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, battle_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("battle_"))
def handle_battle_action(call):
    """Обработка действий в битве"""
    parts = call.data.split("_")
    battle_id = f"{parts[1]}_{parts[2]}"
    action_id = parts[3] if len(parts) > 3 else parts[2]
    
    user_id = call.from_user.id
    
    if battle_id not in active_battles:
        bot.answer_callback_query(call.id, "❌ Битва не найдена!")
        return
    
    # Восстановление битвы
    battle_data = active_battles[battle_id]
    
    # Только для демонстрации, создаём новую битву
    # В реальном коде нужно сохранять/загружать состояние битвы
    battle = TacticalBattle(battle_data["p1_id"], battle_data["p2_id"], 
                          battle_data["bet"], battle_data["duel_type"])
    
    # Установка действия игрока
    if str(user_id) == battle.p1_id:
        battle.p1_action = action_id
    elif str(user_id) == battle.p2_id:
        battle.p2_action = action_id
    else:
        bot.answer_callback_query(call.id, "❌ Вы не в этой битве!")
        return
    
    # Для бота - автоматический выбор
    if battle.p2_id.startswith("bot_"):
        bot_actions = battle.get_available_actions(2)
        if bot_actions:
            battle.p2_action = random.choice(bot_actions)["id"]
    
    # Если оба действия выбраны - выполняем ход
    if battle.p1_action and battle.p2_action:
        result = battle.execute_actions()
        
        if result is not None:
            # Битва завершена
            finish_battle(call.message, battle, result)
        else:
            # Показ следующего хода
            if not battle.p2_id.startswith("bot_"):
                # PvP - ждём второго игрока
                show_battle_interface(call.message, battle, 
                                    battle.p2_id if str(user_id) == battle.p1_id else battle.p1_id)
            else:
                # Против бота - сразу показываем ход игрока
                show_battle_interface(call.message, battle, user_id)
    else:
        # Ждём второго игрока
        bot.answer_callback_query(call.id, "⏳ Ожидание хода противника...")
        if not battle.p2_id.startswith("bot_"):
            # Отправляем интерфейс второму игроку
            try:
                other_id = battle.p2_id if str(user_id) == battle.p1_id else battle.p1_id
                show_battle_interface(call.message, battle, int(other_id))
            except:
                pass

def finish_battle(message, battle, result):
    """Завершение битвы и начисление наград"""
    # Очистка бота
    if battle.p2_id.startswith("bot_"):
        if battle.p2_id in users:
            del users[battle.p2_id]
    
    # Обработка результатов
    if result == "draw":
        text = "<b>🤝 НИЧЬЯ!</b>\n\n"
        if not battle.p2_id.startswith("bot_"):
            Player(battle.p1_id).data["money"] += battle.bet
            Player(battle.p2_id).data["money"] += battle.bet
    elif result == 1:
        winner = Player(battle.p1_id)
        winner.data["money"] += battle.bet * 2
        winner.data["wins"] += 1
        winner.data["win_streak"] += 1
        if winner.data["win_streak"] > winner.data["best_streak"]:
            winner.data["best_streak"] = winner.data["win_streak"]
        winner.save()
        
        text = f"<b>🏆 ПОБЕДИТЕЛЬ: {winner.data['first_name']}!</b>\n\n"
        text += f"💰 Награда: +{battle.bet * 2} монет\n"
    else:
        winner = Player(battle.p2_id)
        if not battle.p2_id.startswith("bot_"):
            winner.data["money"] += battle.bet * 2
            winner.data["wins"] += 1
            winner.save()
        
        text = f"<b>🏆 ПОБЕДИТЕЛЬ: {winner.data['first_name']}!</b>\n\n"
    
    text += f"Ходов: {battle.turn}\n"
    text += f"Ставка: {battle.bet}💰\n\n"
    text += "<b>История боя:</b>\n"
    text += "\n".join(battle.battle_log[-8:])
    
    # Очистка битвы
    if battle.battle_id in active_battles:
        del active_battles[battle.battle_id]
        save_json(DATA_FILES['active_battles'], active_battles)
    
    bot.edit_message_text(text[:4000], message.chat.id, message.message_id)

# ==================== МАГАЗИН С ИНТЕРФЕЙСОМ ====================
@bot.message_handler(func=lambda m: m.text == "🏪 Торговля")
def trade_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 Магазин"),
        types.KeyboardButton("💎 Редкости"),
        types.KeyboardButton("🎁 Бонус"),
        types.KeyboardButton("◀️ Назад")
    )
    bot.send_message(message.chat.id, "🏪 Раздел торговли", reply_markup=markup)

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
        f"<b>🛒 МАГАЗИН</b>\n\n💰 Ваш баланс: <b>{player.data['money']} монет</b>\n"
        f"⭐ Уровень: <b>{player.data['level']}</b>\n\nВыберите категорию:",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shopcat_"))
def show_shop_category(call):
    category = call.data.split("_")[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    cat_items = {k: v for k, v in items.items() 
                if v.get("type") == category}
    
    shop_text = f"<b>{category.upper()}</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, item in sorted(cat_items.items(), key=lambda x: x[1]["price"]):
        if player.data["level"] < item.get("level_req", 1):
            continue
        
        rarity_color = {
            "common": "⬜", "uncommon": "🟩", "rare": "🟦",
            "epic": "🟪", "legendary": "🟧", "mythic": "🟥"
        }.get(item.get("rarity", "common"), "⬜")
        
        if item["type"] == "weapon":
            stats = f"Урон: {item['damage'][0]}-{item['damage'][1]}"
        elif item["type"] == "shield":
            stats = f"Защита: {item.get('defense', 0)}"
        elif item["type"] == "armor":
            stats = f"Защита: {item.get('defense', 0)}, HP: +{item.get('hp_bonus', 0)}"
        elif item["type"] == "potion":
            stats = f"Лечение: {item.get('heal', 0)}"
        else:
            stats = item.get("description", "")
        
        shop_text += f"{rarity_color} <b>{item['name']}</b> - {item['price']}💰\n"
        shop_text += f"   {stats} | Ур.{item.get('level_req', 1)}\n\n"
        
        if player.data["money"] >= item["price"]:
            markup.add(types.InlineKeyboardButton(
                f"Купить {item['name']}", callback_data=f"buy_{item_key}"
            ))
    
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_shop"))
    
    bot.edit_message_text(shop_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

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
        bot.send_message(message.chat.id, "⛔ Вы забанены!")
        return
    
    username = message.from_user.username or f"user_{user_id}"
    first_name = message.from_user.first_name or "Игрок"
    
    player = Player(user_id, username, first_name)
    
    welcome_text = f"""
<b>⚔️ ДУЭЛЬ БОТ v5.0 ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

<b>🔥 НОВОЕ В v5.0:</b>
🎯 <b>Стратегические дуэли</b> - полный контроль над боем!
• Выбирайте действия каждый ход
• Система маны и ультимативных атак  
• Статус-эффекты и погода влияют на бой
• Используйте зелья прямо во время битвы

💰 Ваш стартовый баланс: <b>500 монет</b>
🗡 Соберите мощное снаряжение
🏆 Станьте чемпионом арены!

<i>Выбирайте раздел в меню ниже:</i>
"""
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "◀️ Назад")
def back_to_main(message):
    bot.send_message(message.chat.id, "🔙 Главное меню", reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_section(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📊 Статистика"),
        types.KeyboardButton("🎒 Инвентарь"),
        types.KeyboardButton("⚡ Характеристики"),
        types.KeyboardButton("◀️ Назад")
    )
    bot.send_message(message.chat.id, "👤 Раздел персонажа", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🌍 Мир")
def world_section(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🏰 Данжи"),
        types.KeyboardButton("🛡 Кланы"),
        types.KeyboardButton("📜 Квесты"),
        types.KeyboardButton("◀️ Назад")
    )
    bot.send_message(message.chat.id, "🌍 Игровой мир", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def show_stats(message):
    user_id = message.from_user.id
    player = Player(user_id)
    d = player.data
    stats = player.get_full_stats()
    
    winrate = (d["wins"] / d["total_duels"] * 100) if d["total_duels"] > 0 else 0
    
    text = f"""
<b>📊 СТАТИСТИКА</b>

<b>{d['first_name']}</b> | {d['title']} | Ур.{d['level']}
💰 {d['money']} монет | 📊 {d['pvp_rating']} рейтинга

<b>Боевые характеристики:</b>
⚔ Урон: {stats['min_damage']}-{stats['max_damage']}
🛡 Защита: {stats['defense']}
💨 Скорость: {stats['speed']}
💥 Крит: {stats['crit_chance']:.1f}%

<b>Дуэли:</b>
🏆 Побед: {d['wins']} | 💀 Поражений: {d['losses']}
📈 Винрейт: {winrate:.1f}% | 🔥 Серия: {d['win_streak']}

<b>Экипировка:</b>
⚔ {items.get(d['equipment']['weapon'], {}).get('name', 'Нет')}
🛡 {items.get(d['equipment']['shield'], {}).get('name', 'Нет')}
🧥 {items.get(d['equipment']['armor'], {}).get('name', 'Нет')}
"""
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "🎁 Бонус")
@bot.message_handler(commands=['daily'])
def daily_bonus(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player.data["last_daily"] == today:
        bot.send_message(message.chat.id, "🎁 Вы уже получили бонус сегодня!")
        return
    
    bonus_money = random.randint(150, 600) + player.data["level"] * 15
    bonus_exp = random.randint(70, 250) + player.data["level"] * 8
    
    player.data["money"] += bonus_money
    player.data["exp"] += bonus_exp
    player.data["total_exp"] += bonus_exp
    player.data["last_daily"] = today
    player.save()
    
    text = f"""
<b>🎁 ЕЖЕДНЕВНЫЙ БОНУС</b>

💰 Монет: <b>+{bonus_money}</b>
✨ Опыта: <b>+{bonus_exp}</b>

Приходите завтра за новой наградой!
"""
    bot.send_message(message.chat.id, text)

# ==================== ЗАПУСК БОТА ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v5.0 - ПОЛНАЯ СТРАТЕГИЧЕСКАЯ ВЕРСИЯ ⚔️")
    print("=" * 60)
    print(f"🕒 Запуск: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print(f"⚔ Предметов: {len(items)}")
    print(f"💎 Лимитированных: {len(limited_items)}")
    print("=" * 60)
    print("✅ Бот запущен и готов к стратегическим битвам!")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
