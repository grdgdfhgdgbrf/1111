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
import re

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = '8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE'
ADMIN_ID = 5356400377
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ==================== КОНСТАНТЫ ====================
BODY_PARTS = {
    "head": {"name": "👤 Голова", "multiplier": 1.5, "base_defense": 5},
    "body": {"name": "🦾 Тело", "multiplier": 1.0, "base_defense": 10},
    "legs": {"name": "🦿 Ноги", "multiplier": 0.7, "base_defense": 3}
}

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
    "fire": {"name": "🔥 Огонь", "strong": "ice", "weak": "water", "effect": "burn"},
    "ice": {"name": "❄ Лёд", "strong": "nature", "weak": "fire", "effect": "freeze"},
    "lightning": {"name": "⚡ Молния", "strong": "water", "weak": "earth", "effect": "stun"},
    "water": {"name": "🌊 Вода", "strong": "fire", "weak": "lightning", "effect": "soak"},
    "nature": {"name": "🌿 Природа", "strong": "earth", "weak": "ice", "effect": "poison"},
    "earth": {"name": "🏔 Земля", "strong": "lightning", "weak": "nature", "effect": "bleed"},
    "dark": {"name": "🌑 Тьма", "strong": "light", "weak": "light", "effect": "curse"},
    "light": {"name": "✨ Свет", "strong": "dark", "weak": "dark", "effect": "bless"}
}

ENCHANT_EFFECTS = [
    {"name": "🔥 Огненное", "effect": "fire_damage", "value": 15},
    {"name": "❄ Ледяное", "effect": "freeze_chance", "value": 20},
    {"name": "⚡ Грозовое", "effect": "stun_chance", "value": 15},
    {"name": "💀 Проклятое", "effect": "life_steal", "value": 12},
    {"name": "🛡 Укреплённое", "effect": "defense_bonus", "value": 20},
    {"name": "💪 Мощное", "effect": "damage_boost", "value": 30},
    {"name": "💨 Скоростное", "effect": "speed_bonus", "value": 15},
    {"name": "❤ Живучее", "effect": "hp_bonus", "value": 60},
    {"name": "💎 Магическое", "effect": "mana_bonus", "value": 40},
    {"name": "🍀 Удачливое", "effect": "luck_bonus", "value": 12},
    {"name": "🎯 Меткое", "effect": "crit_bonus", "value": 20},
    {"name": "🔮 Мистическое", "effect": "random_effect", "value": 0}
]

# ==================== ФАЙЛЫ ДАННЫХ ====================
DATA_FILES = {
    'users': 'users.json',
    'items': 'items.json',
    'limited': 'limited_items.json',
    'clans': 'clans.json',
    'tournaments': 'tournaments.json',
    'market': 'market.json',
    'dungeons': 'dungeon_progress.json',
    'events': 'events.json',
    'bans': 'bans.json',
    'battle_history': 'battle_history.json',
    'enchantments': 'enchantments.json',
    'matchmaking': 'matchmaking.json'
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
HELMETS = {
    "leather_cap": {"name": "🎓 Кожаная шапка", "defense": 3, "hp_bonus": 10, "price": 60, "type": "helmet", "slot": "head", "rarity": "common", "level_req": 1, "enchantable": True},
    "iron_helmet": {"name": "⛑ Железный шлем", "defense": 8, "hp_bonus": 20, "price": 250, "type": "helmet", "slot": "head", "rarity": "uncommon", "level_req": 6, "enchantable": True},
    "dragon_helmet": {"name": "🐉 Шлем дракона", "defense": 18, "hp_bonus": 50, "price": 2000, "type": "helmet", "slot": "head", "rarity": "epic", "level_req": 20, "enchantable": True, "element": "fire"},
    "crown_of_wisdom": {"name": "👑 Корона мудрости", "defense": 12, "hp_bonus": 35, "mana_bonus": 40, "price": 3500, "type": "helmet", "slot": "head", "rarity": "legendary", "level_req": 28, "enchantable": True}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "defense": 5, "hp_bonus": 25, "price": 80, "type": "armor", "slot": "body", "rarity": "common", "level_req": 1, "enchantable": True},
    "chainmail": {"name": "⛓ Кольчуга", "defense": 12, "hp_bonus": 50, "price": 400, "type": "armor", "slot": "body", "rarity": "uncommon", "level_req": 8, "enchantable": True},
    "plate_armor": {"name": "🛡 Латный доспех", "defense": 22, "hp_bonus": 90, "price": 1500, "type": "armor", "slot": "body", "rarity": "rare", "level_req": 15, "enchantable": True},
    "shadow_armor": {"name": "🌑 Теневая броня", "defense": 28, "hp_bonus": 120, "price": 3500, "type": "armor", "slot": "body", "rarity": "epic", "level_req": 22, "enchantable": True, "element": "dark"},
    "phoenix_armor": {"name": "🦅 Броня феникса", "defense": 40, "hp_bonus": 200, "price": 8000, "type": "armor", "slot": "body", "rarity": "legendary", "level_req": 30, "enchantable": True, "element": "fire"}
}

BOOTS = {
    "leather_boots": {"name": "👢 Кожаные сапоги", "defense": 2, "speed": 8, "price": 100, "type": "boots", "slot": "legs", "rarity": "common", "level_req": 1, "enchantable": True},
    "wind_boots": {"name": "🌪 Сапоги ветра", "defense": 4, "speed": 18, "price": 900, "type": "boots", "slot": "legs", "rarity": "rare", "level_req": 12, "enchantable": True},
    "blink_boots": {"name": "✨ Сапоги телепортации", "defense": 8, "speed": 28, "price": 4000, "type": "boots", "slot": "legs", "rarity": "epic", "level_req": 25, "enchantable": True},
    "hermes_boots": {"name": "👟 Сандалии Гермеса", "defense": 12, "speed": 45, "price": 12000, "type": "boots", "slot": "legs", "rarity": "legendary", "level_req": 35, "enchantable": True}
}

WEAPONS = {
    "rusty_sword": {"name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 1, "skills": ["slash", "quick_strike"], "enchantable": True},
    "hunters_bow": {"name": "🏹 Лук охотника", "damage": (7, 14), "price": 150, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 3, "skills": ["power_shot", "multi_shot"], "enchantable": True, "element": "nature"},
    "flame_blade": {"name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 7, "skills": ["fire_slash", "inferno_strike", "flame_wave"], "enchantable": True, "element": "fire"},
    "frost_axe": {"name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 10, "skills": ["frost_strike", "ice_shatter", "blizzard"], "enchantable": True, "element": "ice"},
    "storm_staff": {"name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500, "type": "weapon", "slot": "weapon", "rarity": "rare", "level_req": 14, "skills": ["lightning_bolt", "thunder_storm", "chain_lightning"], "enchantable": True, "element": "lightning"},
    "tidal_blade": {"name": "🌊 Приливной клинок", "damage": (20, 32), "price": 2500, "type": "weapon", "slot": "weapon", "rarity": "rare", "level_req": 18, "skills": ["water_slash", "tsunami", "drown"], "enchantable": True, "element": "water"},
    "shadow_dagger": {"name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "slot": "weapon", "rarity": "epic", "level_req": 22, "skills": ["shadow_strike", "assassinate", "dark_veil", "soul_drain"], "enchantable": True, "element": "dark"},
    "divine_spear": {"name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "slot": "weapon", "rarity": "legendary", "level_req": 28, "skills": ["holy_strike", "divine_judgment", "heavenly_light"], "enchantable": True, "element": "light"},
    "death_scythe": {"name": "💀 Коса смерти", "damage": (40, 65), "price": 12000, "type": "weapon", "slot": "weapon", "rarity": "mythic", "level_req": 35, "skills": ["reap", "death_sentence", "soul_harvest"], "enchantable": True, "element": "dark"}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 200, "price": 350, "type": "potion", "rarity": "rare", "level_req": 15},
    "mana_potion": {"name": "💎 Зелье маны", "mana_restore": 60, "price": 60, "type": "potion", "rarity": "common", "level_req": 5}
}

LIMITED_ITEMS = {
    "thunderfury": {"name": "⚡ Ярость грома", "damage": (60, 95), "total": 3, "remaining": 3, "price": 50000, "type": "weapon", "slot": "weapon", "rarity": "divine", "element": "lightning", "skills": ["thunder_gods_wrath", "eye_of_the_storm", "lightning_apocalypse"], "enchantable": True},
    "immortal_helmet": {"name": "✨ Шлем бессмертия", "defense": 80, "hp_bonus": 300, "total": 2, "remaining": 2, "price": 75000, "type": "helmet", "slot": "head", "rarity": "divine", "enchantable": True}
}

ALL_ITEMS = {}
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(BOOTS)
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(POTIONS)

# ==================== БАЗА НАВЫКОВ ====================
SKILLS_DB = {
    "quick_strike": {"name": "⚡ Быстрый удар", "damage_mult": 0.8, "mana_cost": 5, "cooldown": 0, "hits": 2},
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 8, "cooldown": 0},
    "power_shot": {"name": "🎯 Мощный выстрел", "damage_mult": 1.8, "mana_cost": 15, "cooldown": 1},
    "multi_shot": {"name": "🏹 Залп", "damage_mult": 0.6, "mana_cost": 20, "hits": 3, "cooldown": 2},
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.5, "mana_cost": 18, "element": "fire", "burn_chance": 30, "cooldown": 1},
    "inferno_strike": {"name": "🌋 Инферно удар", "damage_mult": 2.2, "mana_cost": 35, "element": "fire", "burn_chance": 60, "cooldown": 2},
    "flame_wave": {"name": "🔥 Волна пламени", "damage_mult": 2.5, "mana_cost": 45, "element": "fire", "aoe": True, "cooldown": 3},
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.4, "mana_cost": 16, "element": "ice", "freeze_chance": 25, "cooldown": 0},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.0, "mana_cost": 30, "element": "ice", "freeze_chance": 50, "cooldown": 2},
    "blizzard": {"name": "🌨 Метель", "damage_mult": 2.4, "mana_cost": 42, "element": "ice", "aoe": True, "cooldown": 3},
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.6, "mana_cost": 20, "element": "lightning", "stun_chance": 20, "cooldown": 0},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.3, "mana_cost": 40, "element": "lightning", "stun_chance": 35, "aoe": True, "cooldown": 3},
    "chain_lightning": {"name": "⚡ Цепная молния", "damage_mult": 1.8, "mana_cost": 28, "element": "lightning", "chain_hits": 3, "cooldown": 2},
    "water_slash": {"name": "🌊 Водяной разрез", "damage_mult": 1.3, "mana_cost": 15, "element": "water", "cooldown": 0},
    "tsunami": {"name": "🌊 Цунами", "damage_mult": 2.1, "mana_cost": 38, "element": "water", "aoe": True, "cooldown": 3},
    "drown": {"name": "💧 Утопление", "damage_mult": 1.9, "mana_cost": 32, "element": "water", "cooldown": 2},
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.6, "mana_cost": 22, "element": "dark", "poison_chance": 25, "cooldown": 0},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.2, "mana_cost": 55, "element": "dark", "ignore_defense": 50, "cooldown": 4},
    "soul_drain": {"name": "💀 Похищение души", "damage_mult": 2.0, "mana_cost": 35, "element": "dark", "life_steal": 0.4, "cooldown": 3},
    "dark_veil": {"name": "🌑 Завеса тьмы", "defense_boost": 30, "mana_cost": 25, "element": "dark", "cooldown": 2},
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.5, "mana_cost": 20, "element": "light", "cooldown": 0},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 2.8, "mana_cost": 48, "element": "light", "cooldown": 3},
    "heavenly_light": {"name": "🌟 Небесный свет", "hp_restore": 60, "mana_cost": 30, "element": "light", "cooldown": 2},
    "reap": {"name": "💀 Жатва", "damage_mult": 2.5, "mana_cost": 42, "element": "dark", "life_steal": 0.3, "cooldown": 2},
    "death_sentence": {"name": "☠ Смертный приговор", "damage_mult": 4.0, "mana_cost": 70, "element": "dark", "cooldown": 5},
    "soul_harvest": {"name": "👻 Сбор душ", "damage_mult": 2.8, "mana_cost": 50, "element": "dark", "life_steal": 0.5, "cooldown": 3},
    "thunder_gods_wrath": {"name": "⚡ Гнев бога грома", "damage_mult": 4.5, "mana_cost": 80, "element": "lightning", "stun_chance": 50, "aoe": True, "cooldown": 5},
    "eye_of_the_storm": {"name": "🌀 Глаз бури", "damage_mult": 3.0, "mana_cost": 55, "element": "lightning", "cooldown": 3},
    "lightning_apocalypse": {"name": "⚡ Молниевый апокалипсис", "damage_mult": 5.0, "mana_cost": 90, "element": "lightning", "aoe": True, "cooldown": 6}
}

# Загрузка данных
items = load_json(DATA_FILES['items'], ALL_ITEMS)
limited_items = load_json(DATA_FILES['limited'], LIMITED_ITEMS)
users = load_json(DATA_FILES['users'], {})
clans = load_json(DATA_FILES['clans'], {})
tournaments = load_json(DATA_FILES['tournaments'], {})
market_listings = load_json(DATA_FILES['market'], {})
dungeon_progress = load_json(DATA_FILES['dungeons'], {})
events = load_json(DATA_FILES['events'], {})
banned_users = load_json(DATA_FILES['bans'], {})
battle_history_data = load_json(DATA_FILES['battle_history'], {})
enchantments_data = load_json(DATA_FILES['enchantments'], {})
matchmaking_queue = load_json(DATA_FILES['matchmaking'], {})

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
                "stats": {"strength": 5, "agility": 5, "intelligence": 5, "vitality": 5, "luck": 5, "defense": 0},
                "stat_points": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "win_streak": 0,
                "best_streak": 0,
                "total_duels": 0,
                "pvp_rating": 1000,
                "inventory": [],
                "equipment": {"weapon": None, "head": None, "body": None, "legs": None},
                "enchantments": {},
                "last_daily": None,
                "last_dungeon": None,
                "title": "Новичок",
                "titles_collected": ["Новичок"],
                "achievements": [],
                "clan": None,
                "clan_role": None,
                "registration_date": datetime.now().isoformat(),
                "settings": {"notifications": True, "duel_requests": True},
                "battle_history": [],
                "dungeons_completed": 0,
                "items_found": 0
            }
            self.save()
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    def save(self):
        save_json(DATA_FILES['users'], users)
    
    def get_full_stats(self):
        base = copy.deepcopy(self.data["stats"])
        bonuses = {
            "min_damage": base["strength"] * 2,
            "max_damage": base["strength"] * 3,
            "defense": base["defense"] + base["vitality"] * 2,
            "speed": base["agility"] * 1.5,
            "crit_chance": 5 + base["luck"] * 0.5,
            "crit_multiplier": 1.5,
            "dodge_chance": 3 + base["agility"] * 0.3,
            "block_chance": 0,
            "hp": self.data["max_hp"] + base["vitality"] * 15,
            "max_hp": self.data["max_hp"] + base["vitality"] * 15,
            "mana": self.data["max_mana"] + base["intelligence"] * 8,
            "max_mana": self.data["max_mana"] + base["intelligence"] * 8,
            "head_defense": 5,
            "body_defense": 10,
            "legs_defense": 3,
            "fire_damage": 0,
            "freeze_chance": 0,
            "stun_chance": 0,
            "life_steal": 0,
            "damage_boost": 0,
            "speed_bonus": 0,
            "hp_bonus": 0,
            "mana_bonus": 0,
            "luck_bonus": 0,
            "crit_bonus": 0,
            "defense_bonus": 0
        }
        
        for slot, ik in self.data["equipment"].items():
            if not ik:
                continue
            item = items.get(ik) or limited_items.get(ik)
            if not item:
                continue
            
            if item.get("slot") == "weapon" and "damage" in item:
                bonuses["min_damage"] += item["damage"][0]
                bonuses["max_damage"] += item["damage"][1]
                if "element" in item and item["element"]:
                    bonuses["elemental_bonus"] = bonuses.get("elemental_bonus", {})
                    bonuses["elemental_bonus"][item["element"]] = bonuses["elemental_bonus"].get(item["element"], 0) + 20
            
            if item.get("slot") == "head":
                bonuses["head_defense"] += item.get("defense", 0)
                bonuses["max_hp"] += item.get("hp_bonus", 0)
                bonuses["max_mana"] += item.get("mana_bonus", 0)
                bonuses["block_chance"] += 5
            elif item.get("slot") == "body":
                bonuses["body_defense"] += item.get("defense", 0)
                bonuses["max_hp"] += item.get("hp_bonus", 0)
                bonuses["block_chance"] += 10
            elif item.get("slot") == "legs":
                bonuses["legs_defense"] += item.get("defense", 0)
                bonuses["speed"] += item.get("speed", 0)
                bonuses["dodge_chance"] += 5
            
            ench = self.data.get("enchantments", {}).get(ik, {})
            if ench:
                eff = ench.get("effect")
                val = ench.get("value", 0)
                if eff in bonuses:
                    bonuses[eff] += val
        
        bonuses["hp"] = bonuses["max_hp"]
        bonuses["mana"] = bonuses["max_mana"]
        bonuses["crit_chance"] += bonuses["crit_bonus"]
        bonuses["crit_chance"] = min(80, bonuses["crit_chance"])
        bonuses["dodge_chance"] = min(50, bonuses["dodge_chance"])
        bonuses["block_chance"] = min(60, bonuses["block_chance"])
        bonuses["min_damage"] += bonuses["fire_damage"]
        bonuses["max_damage"] += bonuses["fire_damage"]
        bonuses["speed"] += bonuses["speed_bonus"]
        bonuses["max_hp"] += bonuses["hp_bonus"]
        bonuses["max_mana"] += bonuses["mana_bonus"]
        bonuses["hp"] = bonuses["max_hp"]
        bonuses["mana"] = bonuses["max_mana"]
        bonuses["defense"] += bonuses["defense_bonus"]
        
        return bonuses

# ==================== ХРАНИЛИЩЕ ДУЭЛЕЙ ====================
active_duels = {}

class DuelInstance:
    def __init__(self, p1_id, p2_id, duel_type="quick", bet=0):
        self.battle_id = str(uuid.uuid4())[:8]
        self.p1_id = str(p1_id)
        self.p2_id = str(p2_id)
        self.duel_type = duel_type
        self.bet = bet
        self.turn = 1
        self.max_turns = 40
        self.active = True
        self.winner = None
        self.log = []
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        self.p1_stats = self.p1.get_full_stats()
        self.p2_stats = self.p2.get_full_stats()
        
        # Уравниваем HP для честного боя
        avg_hp = (self.p1_stats["max_hp"] + self.p2_stats["max_hp"]) // 2
        self.p1_hp = avg_hp
        self.p2_hp = avg_hp
        self.p1_max_hp = avg_hp
        self.p2_max_hp = avg_hp
        
        self.p1_mp = self.p1_stats["max_mana"]
        self.p2_mp = self.p2_stats["max_mana"]
        self.p1_max_mp = self.p1_mp
        self.p2_max_mp = self.p2_mp
        
        # Фазы: defend_select -> attack_skill -> done
        self.p1_phase = "defend_select"
        self.p2_phase = "defend_select"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        
        # Очерёдность
        p1_spd = self.p1_stats["speed"] + random.randint(-10, 10)
        p2_spd = self.p2_stats["speed"] + random.randint(-10, 10)
        self.first_attacker = 1 if p1_spd >= p2_spd else 2
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Эффекты
        self.p1_effects = []
        self.p2_effects = []
        
        # Баффы
        self.p1_buffs = {"defense": 0, "damage": 0, "crit": 0, "dodge": 0}
        self.p2_buffs = {"defense": 0, "damage": 0, "crit": 0, "dodge": 0}
        
        # Арена
        self.arena = random.choice(["colosseum", "forest", "volcano", "tundra", "void", "temple"])
        self.weather = random.choice(["clear", "rain", "storm", "fog", "blizzard"])
        
        self.log.append(f"⚔ <b>БИТВА НАЧАЛАСЬ!</b>")
        self.log.append(f"🏟 Арена: <b>{self._arena_name()}</b> | 🌤 Погода: <b>{self._weather_name()}</b>")
    
    def _arena_name(self):
        names = {"colosseum": "Колизей", "forest": "Лес", "volcano": "Вулкан", "tundra": "Тундра", "void": "Пустота", "temple": "Храм"}
        return names.get(self.arena, self.arena)
    
    def _weather_name(self):
        names = {"clear": "Ясно", "rain": "Дождь", "storm": "Шторм", "fog": "Туман", "blizzard": "Буран"}
        return names.get(self.weather, self.weather)
    
    def get_player_name(self, num):
        return self.p1.data["first_name"] if num == 1 else self.p2.data["first_name"]
    
    def get_available_skills(self, player_num):
        player = self.p1 if player_num == 1 else self.p2
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        equip = player.data["equipment"]
        
        available = []
        
        # Базовые навыки
        base = ["quick_strike", "slash"]
        for sid in base:
            if sid not in cooldowns or cooldowns[sid] <= 0:
                available.append(sid)
        
        # Навыки оружия
        weapon_key = equip.get("weapon")
        if weapon_key:
            weapon = items.get(weapon_key) or limited_items.get(weapon_key)
            if weapon and "skills" in weapon:
                for sid in weapon["skills"]:
                    if sid in SKILLS_DB:
                        cd = cooldowns.get(sid, 0)
                        if cd <= 0:
                            available.append(sid)
        
        # Защитные
        if "defend" not in cooldowns or cooldowns.get("defend", 0) <= 0:
            available.append("defend")
        
        return list(set(available))
    
    def set_defend(self, player_num, part):
        if player_num == 1:
            self.p1_defend = part
            self.p1_phase = "attack_select"
        else:
            self.p2_defend = part
            self.p2_phase = "attack_select"
    
    def execute_attack(self, player_num, skill_id, target_part):
        if player_num == 1:
            self.p1_skill = skill_id
            self.p1_target = target_part
            self.p1_phase = "done"
        else:
            self.p2_skill = skill_id
            self.p2_target = target_part
            self.p2_phase = "done"
        
        # Если оба готовы - разрешаем ход
        if self.p1_phase == "done" and self.p2_phase == "done":
            self._resolve_turn()
    
    def _resolve_turn(self):
        """Разрешение полного хода"""
        # Обработка эффектов
        self._process_effects(1)
        self._process_effects(2)
        
        # Атаки по очерёдности
        first = self.first_attacker
        second = 3 - first
        
        self._do_attack(first, second)
        if self.p1_hp <= 0 or self.p2_hp <= 0:
            self._check_end()
            return
        
        self._do_attack(second, first)
        self._check_end()
        
        # Декей баффов
        for b in [self.p1_buffs, self.p2_buffs]:
            for k in b:
                b[k] = max(0, b[k] - 5)
        
        # Смена очерёдности
        self.first_attacker = 3 - self.first_attacker
        
        # Сброс фаз
        self.p1_phase = "defend_select"
        self.p2_phase = "defend_select"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        
        self.turn += 1
        if self.turn > self.max_turns:
            self.active = False
            self.winner = 0
    
    def _do_attack(self, attacker, defender):
        skill_id = self.p1_skill if attacker == 1 else self.p2_skill
        target_part = self.p1_target if attacker == 1 else self.p2_target
        defend_part = self.p2_defend if attacker == 1 else self.p1_defend
        
        if not skill_id:
            return
        
        skill = SKILLS_DB.get(skill_id, {"name": "Атака", "damage_mult": 1.0, "mana_cost": 0})
        
        # Статы
        a_stats = self.p1_stats if attacker == 1 else self.p2_stats
        a_buffs = self.p1_buffs if attacker == 1 else self.p2_buffs
        a_cooldowns = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
        d_stats = self.p2_stats if attacker == 1 else self.p1_stats
        d_buffs = self.p2_buffs if attacker == 1 else self.p1_buffs
        
        # Мана
        mc = skill.get("mana_cost", 0)
        if attacker == 1:
            if self.p1_mp < mc:
                self.log.append(f"❌ {self.get_player_name(attacker)}: нет маны!")
                return
            self.p1_mp -= mc
        else:
            if self.p2_mp < mc:
                self.log.append(f"❌ {self.get_player_name(attacker)}: нет маны!")
                return
            self.p2_mp -= mc
        
        # Проверка защиты
        if defend_part == target_part:
            # Заблокировано
            def_bonus = 30
            if defend_part == "head":
                def_bonus += d_stats["head_defense"]
            elif defend_part == "body":
                def_bonus += d_stats["body_defense"]
            elif defend_part == "legs":
                def_bonus += d_stats["legs_defense"]
            
            reduction = def_bonus / (def_bonus + 100)
            
            # Базовый урон для отображения
            min_d = int(a_stats["min_damage"] * (1 + a_buffs["damage"] / 100))
            max_d = int(a_stats["max_damage"] * (1 + a_buffs["damage"] / 100))
            base_dmg = random.randint(min_d, max_d)
            base_dmg = int(base_dmg * skill.get("damage_mult", 1.0))
            blocked_dmg = int(base_dmg * (1 - reduction))
            
            self.log.append(f"🛡 {self.get_player_name(attacker)} бьёт в {BODY_PARTS[target_part]['name']}, но {self.get_player_name(defender)} защитил! Урон снижен: {blocked_dmg} HP (было бы {base_dmg})")
            
            if defender == 1:
                self.p1_hp = max(0, self.p1_hp - blocked_dmg)
            else:
                self.p2_hp = max(0, self.p2_hp - blocked_dmg)
            
            return
        
        # Урон (не заблокирован)
        min_d = int(a_stats["min_damage"] * (1 + a_buffs["damage"] / 100))
        max_d = int(a_stats["max_damage"] * (1 + a_buffs["damage"] / 100))
        dmg = random.randint(min_d, max_d)
        dmg = int(dmg * skill.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_m = BODY_PARTS.get(target_part, {}).get("multiplier", 1.0)
        dmg = int(dmg * body_m)
        
        # Крит
        is_crit = False
        if random.random() * 100 < (a_stats["crit_chance"] + a_buffs["crit"]):
            dmg = int(dmg * a_stats["crit_multiplier"])
            is_crit = True
        
        # Элемент
        weapon_key = (self.p1 if attacker == 1 else self.p2).data["equipment"].get("weapon")
        if weapon_key and "element" in skill:
            pass  # Элемент уже в навыке
        
        # Уклонение
        if random.random() * 100 < (d_stats["dodge_chance"] + d_buffs["dodge"]):
            dmg = 0
            self.log.append(f"💨 {self.get_player_name(defender)} уклонился от удара в {BODY_PARTS[target_part]['name']}!")
        
        # Нанесение урона
        if dmg > 0:
            if defender == 1:
                self.p1_hp = max(0, self.p1_hp - dmg)
            else:
                self.p2_hp = max(0, self.p2_hp - dmg)
            
            ct = "💥 КРИТ! " if is_crit else ""
            self.log.append(f"{ct}⚔ {self.get_player_name(attacker)} [{skill['name']}] → {BODY_PARTS[target_part]['name']} {self.get_player_name(defender)}: <b>-{dmg} HP</b>")
            
            # Вампиризм
            if "life_steal" in skill:
                hl = int(dmg * skill["life_steal"])
                if attacker == 1:
                    self.p1_hp = min(self.p1_max_hp, self.p1_hp + hl)
                else:
                    self.p2_hp = min(self.p2_max_hp, self.p2_hp + hl)
                self.log.append(f"💚 Вампиризм +{hl} HP")
            
            # Эффекты
            self._apply_effects(defender, skill)
        
        # Лечение
        if "hp_restore" in skill:
            hl = skill["hp_restore"]
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + hl)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + hl)
            self.log.append(f"💚 +{hl} HP")
        
        # Кулдауны
        if "cooldown" in skill and skill["cooldown"] > 0:
            a_cooldowns[skill_id] = skill["cooldown"]
        
        for sid in list(a_cooldowns.keys()):
            a_cooldowns[sid] -= 1
            if a_cooldowns[sid] <= 0:
                del a_cooldowns[sid]
    
    def _apply_effects(self, target, skill):
        effects = []
        if "burn_chance" in skill and random.random() * 100 < skill["burn_chance"]:
            effects.append({"type": "burn", "duration": 3})
            self.log.append("🔥 Горение!")
        if "freeze_chance" in skill and random.random() * 100 < skill["freeze_chance"]:
            effects.append({"type": "freeze", "duration": 2})
            self.log.append("❄ Заморозка!")
        if "stun_chance" in skill and random.random() * 100 < skill["stun_chance"]:
            effects.append({"type": "stun", "duration": 1})
            self.log.append("⚡ Оглушение!")
        if "poison_chance" in skill and random.random() * 100 < skill["poison_chance"]:
            effects.append({"type": "poison", "duration": 4})
            self.log.append("☠ Отравление!")
        
        if target == 1:
            self.p1_effects.extend(effects)
        else:
            self.p2_effects.extend(effects)
    
    def _process_effects(self, player_num):
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        hp = self.p1_hp if player_num == 1 else self.p2_hp
        
        for eff in effects[:]:
            if eff["type"] == "burn":
                d = 12
                hp -= d
                self.log.append(f"🔥 Горение -{d} HP")
            elif eff["type"] == "poison":
                d = 15
                hp -= d
                self.log.append(f"☠ Яд -{d} HP")
            
            eff["duration"] -= 1
            if eff["duration"] <= 0:
                effects.remove(eff)
        
        if player_num == 1:
            self.p1_hp = max(0, hp)
        else:
            self.p2_hp = max(0, hp)
    
    def _check_end(self):
        if self.p1_hp <= 0:
            self.active = False
            self.winner = 2
        elif self.p2_hp <= 0:
            self.active = False
            self.winner = 1
    
    def get_state_text(self, for_player_id):
        pn = 1 if str(for_player_id) == self.p1_id else 2
        phase = self.p1_phase if pn == 1 else self.p2_phase
        
        p1_hp_pct = self.p1_hp / self.p1_max_hp * 100 if self.p1_max_hp > 0 else 0
        p2_hp_pct = self.p2_hp / self.p2_max_hp * 100 if self.p2_max_hp > 0 else 0
        
        p1_mp_pct = self.p1_mp / self.p1_max_mp * 100 if self.p1_max_mp > 0 else 0
        p2_mp_pct = self.p2_mp / self.p2_max_mp * 100 if self.p2_max_mp > 0 else 0
        
        def bar(pct, icon, cur, mx):
            f = int(pct / 10)
            e = 10 - f
            color = "🟢" if pct > 50 else "🟡" if pct > 25 else "🔴"
            return f"{icon} {color}[{'█'*f}{'░'*e}] {cur}/{mx} ({pct:.0f}%)"
        
        text = f"""
<b>⚔ ДУЭЛЬ #{self.battle_id}</b>
━━━━━━━━━━━━━━━━━━━━
🏟 {self._arena_name()} | 🌤 {self._weather_name()}
Ход: <b>#{self.turn}</b> | Ставка: <b>{self.bet}💰</b>

<b>{self.get_player_name(1)}</b>
{bar(p1_hp_pct, '❤', self.p1_hp, self.p1_max_hp)}
{bar(p1_mp_pct, '💎', self.p1_mp, self.p1_max_mp)}
🛡 Защита: {BODY_PARTS.get(self.p1_defend, {}).get('name', 'Не выбрана') if self.p1_defend else 'Не выбрана'}

<b>{self.get_player_name(2)}</b>
{bar(p2_hp_pct, '❤', self.p2_hp, self.p2_max_hp)}
{bar(p2_mp_pct, '💎', self.p2_mp, self.p2_max_mp)}
🛡 Защита: {BODY_PARTS.get(self.p2_defend, {}).get('name', 'Не выбрана') if self.p2_defend else 'Не выбрана'}
━━━━━━━━━━━━━━━━━━━━
"""
        
        if phase == "defend_select":
            text += "\n🛡 <b>Выберите часть тела для защиты:</b>"
        elif phase == "attack_select":
            text += "\n🎯 <b>Выберите цель и навык атаки:</b>"
        elif phase == "done":
            text += "\n⏳ <b>Ожидание хода противника...</b>"
        
        # Эффекты
        effs = self.p1_effects if pn == 1 else self.p2_effects
        if effs:
            text += "\n<b>Эффекты:</b> "
            text += ", ".join([f"{e['type']}({e['duration']})" for e in effs])
        
        # Лог
        if self.log:
            text += f"\n<i>{self.log[-1][:100]}</i>"
        
        return text

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

# ==================== ОБРАБОТЧИКИ ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if str(user_id) in banned_users:
        bot.send_message(message.chat.id, "⛔ Вы забанены!")
        return
    
    username = message.from_user.username or f"user_{user_id}"
    first_name = message.from_user.first_name or "Игрок"
    Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v10.0 ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

🎯 <b>НОВОЕ:</b>
• Пошаговые дуэли: защита → атака с навыком
• HP одинаковые для честного боя!
• Урон зависит от защиты экипировки
• Навыки оружия: у каждого свои атаки
• Поиск соперника или бот
• Данжи с боссами (пошаговые)

💰 Старт: <b>500 монет</b>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль (бот)", callback_data="quick_duel"),
        types.InlineKeyboardButton("👥 Найти соперника", callback_data="find_opponent"),
        types.InlineKeyboardButton("🏆 Рейтинговая", callback_data="ranked_duel"),
        types.InlineKeyboardButton("💀 Хардкор", callback_data="hardcore_duel"),
        types.InlineKeyboardButton("🎯 Спарринг", callback_data="sparring_duel")
    )
    
    text = """
<b>⚔️ ДУЭЛИ</b>

<b>Система боя:</b>
🛡 Выберите защиту
🎯 Выберите цель и навык оружия
⚔ Каждое оружие имеет свои атаки!

<i>Пошаговая стратегия!</i>
"""
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="hero_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="hero_inventory"),
        types.InlineKeyboardButton("⚡ Характеристики", callback_data="hero_attributes"),
        types.InlineKeyboardButton("🏅 Достижения", callback_data="hero_achievements"),
        types.InlineKeyboardButton("✨ Зачарования", callback_data="hero_enchantments"),
        types.InlineKeyboardButton("👁 Экипировка", callback_data="hero_equipped"),
        types.InlineKeyboardButton("📋 История", callback_data="hero_history"),
        types.InlineKeyboardButton("💊 Лечение", callback_data="hero_heal")
    )
    bot.send_message(message.chat.id, "<b>👤 ГЕРОЙ</b>", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🏪 Торговля")
def trade_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛒 Магазин", callback_data="trade_shop"),
        types.InlineKeyboardButton("💎 Лимитированные", callback_data="trade_limited"),
        types.InlineKeyboardButton("🎁 Бонус", callback_data="trade_daily"),
        types.InlineKeyboardButton("💱 Рынок", callback_data="trade_market"),
        types.InlineKeyboardButton("💰 Продать", callback_data="trade_sell"),
        types.InlineKeyboardButton("📦 Мои лоты", callback_data="trade_my_lots")
    )
    bot.send_message(message.chat.id, "<b>🏪 ТОРГОВЛЯ</b>", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🌍 Мир")
def world_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🏰 Подземелья", callback_data="world_dungeons"),
        types.InlineKeyboardButton("🛡 Кланы", callback_data="world_clans"),
        types.InlineKeyboardButton("🏟 Турниры", callback_data="world_tournaments"),
        types.InlineKeyboardButton("🌍 Ивенты", callback_data="world_events"),
        types.InlineKeyboardButton("📊 Топ", callback_data="world_top"),
        types.InlineKeyboardButton("ℹ Помощь", callback_data="world_help")
    )
    bot.send_message(message.chat.id, "<b>🌍 МИР</b>", reply_markup=markup)

# ==================== ДУЭЛИ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["quick_duel", "find_opponent", "ranked_duel", "hardcore_duel", "sparring_duel"])
def duel_type_handler(call):
    dt = call.data
    
    if dt == "quick_duel":
        show_quick_duel_menu(call)
    elif dt == "find_opponent":
        find_opponent(call)
    else:
        names = {
            "ranked_duel": ("🏆 Рейтинговая", 100),
            "hardcore_duel": ("💀 Хардкор", 500),
            "sparring_duel": ("🎯 Спарринг", 0)
        }
        n, bet = names.get(dt, ("Дуэль", 100))
        start_matchmaking(call, dt, bet)

def show_quick_duel_menu(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    for bet in [50, 100, 200, 500, 1000]:
        markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"qduel_{bet}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
    
    bot.edit_message_text(
        f"<b>⚡ БЫСТРАЯ ДУЭЛЬ (БОТ)</b>\n\n💰 Баланс: <b>{player.data['money']}💰</b>\nВыберите ставку:",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

def find_opponent(call):
    user_id = str(call.from_user.id)
    
    # Проверяем очередь
    queue = matchmaking_queue.get("queue", [])
    
    # Убираем себя из очереди если уже есть
    queue = [q for q in queue if q["user_id"] != user_id]
    
    # Ищем соперника
    if queue:
        opponent = queue.pop(0)
        matchmaking_queue["queue"] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        # Начинаем дуэль
        duel = DuelInstance(opponent["user_id"], user_id, opponent["type"], opponent["bet"])
        active_duels[user_id] = duel
        active_duels[opponent["user_id"]] = duel
        
        bot.edit_message_text("⚔ Соперник найден! Дуэль начинается!", call.message.chat.id, call.message.message_id)
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
    else:
        # Встаём в очередь
        queue.append({"user_id": user_id, "type": "quick", "bet": 50})
        matchmaking_queue["queue"] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        # Запускаем бота через 5 секунд если не нашли
        threading.Timer(5.0, start_bot_duel_if_no_opponent, args=[call.message.chat.id, call.message.message_id, user_id]).start()
        
        bot.edit_message_text("🔍 Поиск соперника... Если не найдём — будет бот!", call.message.chat.id, call.message.message_id)

def start_matchmaking(call, duel_type, bet):
    user_id = str(call.from_user.id)
    
    # Проверяем очередь для этого типа
    queue_key = f"queue_{duel_type}"
    queue = matchmaking_queue.get(queue_key, [])
    
    queue = [q for q in queue if q["user_id"] != user_id]
    
    if queue:
        opponent = queue.pop(0)
        matchmaking_queue[queue_key] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        duel = DuelInstance(opponent["user_id"], user_id, duel_type, bet)
        active_duels[user_id] = duel
        active_duels[opponent["user_id"]] = duel
        
        bot.edit_message_text("⚔ Соперник найден!", call.message.chat.id, call.message.message_id)
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
    else:
        queue.append({"user_id": user_id, "type": duel_type, "bet": bet})
        matchmaking_queue[queue_key] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        threading.Timer(5.0, start_bot_duel_if_no_opponent, args=[call.message.chat.id, call.message.message_id, user_id, duel_type, bet]).start()
        
        bot.edit_message_text("🔍 Поиск соперника...", call.message.chat.id, call.message.message_id)

def start_bot_duel_if_no_opponent(chat_id, message_id, user_id, duel_type="quick", bet=50):
    # Проверяем, не нашли ли уже соперника
    if str(user_id) in active_duels:
        return
    
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.edit_message_text(f"❌ Недостаточно монет! Нужно {bet}💰", chat_id, message_id)
        return
    
    # Создаём бота
    bot_level = random.randint(max(1, player.data["level"] - 3), player.data["level"] + 3)
    bot_id = f"bot_{random.randint(100000, 999999)}"
    
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    for slot, itype in [("head", "helmet"), ("body", "armor"), ("legs", "boots")]:
        sitems = [k for k, v in items.items() if v.get("type") == itype and v.get("level_req", 1) <= bot_level]
        if sitems and random.random() < 0.7:
            equip[slot] = random.choice(sitems)
    wpns = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= bot_level]
    if wpns:
        equip["weapon"] = random.choice(wpns)
    
    users[bot_id] = {
        "username": f"Bot_{bot_level}", "first_name": f"🤖 Бот Lv.{bot_level}",
        "money": 0, "level": bot_level, "exp": 0, "total_exp": 0,
        "hp": 100 + bot_level * 12, "max_hp": 100 + bot_level * 12,
        "mana": 50 + bot_level * 6, "max_mana": 50 + bot_level * 6,
        "stats": {"strength": 5 + bot_level, "agility": 5 + bot_level // 2,
                  "intelligence": 5 + bot_level // 3, "vitality": 5 + bot_level // 2,
                  "luck": 3 + bot_level // 4, "defense": bot_level},
        "stat_points": 0, "wins": 0, "losses": 0, "draws": 0,
        "win_streak": 0, "best_streak": 0, "total_duels": 0,
        "pvp_rating": 1000, "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Бот", "titles_collected": ["Бот"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    if bet > 0:
        player.data["money"] -= bet
        player.save()
    
    duel = DuelInstance(user_id, bot_id, duel_type, bet)
    active_duels[str(user_id)] = duel
    
    # Бот выбирает защиту
    bot_def = random.choice(list(BODY_PARTS.keys()))
    duel.set_defend(2, bot_def)
    
    # Бот выбирает атаку
    bot_skills = duel.get_available_skills(2)
    if bot_skills:
        bot_skill = random.choice(bot_skills)
        bot_target = random.choice(list(BODY_PARTS.keys()))
        duel.execute_attack(2, bot_skill, bot_target)
    
    bot.edit_message_text("⚔ Соперник не найден. Бой с ботом!", chat_id, message_id)
    show_duel_interface(chat_id, message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_duels")
def back_to_duels(call):
    duel_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def start_quick_duel(call):
    user_id = call.from_user.id
    bet = int(call.data.split("_")[1])
    
    start_bot_duel_if_no_opponent(call.message.chat.id, call.message.message_id, user_id, "quick", bet)

def show_duel_interface(chat_id, message_id, duel, user_id):
    """Показать интерфейс дуэли"""
    if not duel.active:
        finish_duel(chat_id, message_id, duel)
        return
    
    state_text = duel.get_state_text(user_id)
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    phase = duel.p1_phase if pn == 1 else duel.p2_phase
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if phase == "defend_select":
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']} (DEF:{data['base_defense']})",
                callback_data=f"duel_defend_{part}"
            ))
    
    elif phase == "attack_select":
        # Сначала цель
        markup.add(types.InlineKeyboardButton("🎯 В голову", callback_data="duel_target_head"))
        markup.add(types.InlineKeyboardButton("🎯 В тело", callback_data="duel_target_body"))
        markup.add(types.InlineKeyboardButton("🎯 В ноги", callback_data="duel_target_legs"))
    
    elif phase == "done":
        markup.add(types.InlineKeyboardButton("⏳ Ожидание...", callback_data="duel_wait"))
    
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="duel_refresh"))
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="duel_surrender"))
    
    try:
        bot.edit_message_text(
            state_text[:4000],
            chat_id, message_id,
            reply_markup=markup
        )
    except Exception as e:
        print(f"Edit error: {e}")

# Для выбора цели (сохраняем временно)
target_selection = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_target_"))
def duel_target_selected(call):
    user_id = call.from_user.id
    part = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        return
    
    # Сохраняем цель
    target_selection[str(user_id)] = part
    
    # Показываем навыки
    pn = 1 if str(user_id) == duel.p1_id else 2
    skills = duel.get_available_skills(pn)
    
    state_text = duel.get_state_text(user_id) + f"\n🎯 Цель: <b>{BODY_PARTS[part]['name']}</b>\n<b>Выберите навык:</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for sid in skills[:10]:
        skill = SKILLS_DB.get(sid, {})
        name = skill.get("name", sid)
        mana = skill.get("mana_cost", 0)
        dmg_mult = skill.get("damage_mult", 1.0)
        
        markup.add(types.InlineKeyboardButton(
            f"{name} (x{dmg_mult}) [{mana}MP]",
            callback_data=f"duel_skill_{sid}"
        ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="duel_back_to_target"))
    
    try:
        bot.edit_message_text(state_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "duel_back_to_target")
def duel_back_to_target(call):
    duel = active_duels.get(str(call.from_user.id))
    if duel:
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, call.from_user.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_skill_"))
def duel_skill_selected(call):
    user_id = call.from_user.id
    skill_id = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    target = target_selection.get(str(user_id), "body")
    pn = 1 if str(user_id) == duel.p1_id else 2
    
    duel.execute_attack(pn, skill_id, target)
    
    bot.answer_callback_query(call.id, "⚔ Атака!")
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_"))
def duel_action_handler(call):
    user_id = call.from_user.id
    action = call.data.split("_", 1)[1]
    
    if action in ["refresh", "wait", "surrender"]:
        duel = active_duels.get(str(user_id))
        
        if action == "refresh":
            if duel and duel.active:
                show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
                bot.answer_callback_query(call.id, "✅ Обновлено")
            else:
                bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        
        elif action == "wait":
            if duel and duel.active:
                # Проверяем ход бота
                pn = 1 if str(user_id) == duel.p1_id else 2
                other_pn = 3 - pn
                other_phase = duel.p2_phase if pn == 1 else duel.p1_phase
                
                if other_phase == "defend_select" and str(duel.p2_id).startswith("bot_") and other_pn == 2:
                    duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
                
                if other_phase == "attack_select" and str(duel.p2_id).startswith("bot_") and other_pn == 2:
                    skills = duel.get_available_skills(2)
                    if skills:
                        duel.execute_attack(2, random.choice(skills), random.choice(list(BODY_PARTS.keys())))
                
                show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
                bot.answer_callback_query(call.id, "✅")
        
        elif action == "surrender":
            if duel and duel.active:
                duel.active = False
                duel.winner = 2 if str(user_id) == duel.p1_id else 1
                finish_duel(call.message.chat.id, call.message.message_id, duel)
    
    elif action.startswith("defend_"):
        part = action.split("_")[1]
        duel = active_duels.get(str(user_id))
        if duel and duel.active:
            pn = 1 if str(user_id) == duel.p1_id else 2
            duel.set_defend(pn, part)
            bot.answer_callback_query(call.id, f"🛡 Защита: {BODY_PARTS[part]['name']}")
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

def finish_duel(chat_id, message_id, duel):
    """Завершение дуэли"""
    # Очистка
    for uid in [duel.p1_id, duel.p2_id]:
        if uid in active_duels and active_duels[uid].battle_id == duel.battle_id:
            del active_duels[uid]
    
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") and uid in users:
            del users[uid]
    save_json(DATA_FILES['users'], users)
    
    if duel.winner == 0:
        bot.edit_message_text("<b>🤝 НИЧЬЯ!</b>\nХодов: " + str(duel.turn), chat_id, message_id)
        return
    
    winner_id = duel.p1_id if duel.winner == 1 else duel.p2_id
    loser_id = duel.p2_id if duel.winner == 1 else duel.p1_id
    
    winner = Player(winner_id)
    loser = Player(loser_id)
    
    if duel.bet > 0 and not winner_id.startswith("bot_"):
        winner.data["money"] += duel.bet * 2
    
    if not winner_id.startswith("bot_"):
        winner.data["wins"] += 1
        winner.data["win_streak"] += 1
        winner.data["total_duels"] += 1
        winner.data["pvp_rating"] += random.randint(20, 35)
        if winner.data["win_streak"] > winner.data["best_streak"]:
            winner.data["best_streak"] = winner.data["win_streak"]
        exp_w = duel.turn * 10 + duel.bet // 2
        winner.data["exp"] += exp_w
        winner.data["total_exp"] += exp_w
        old_w = winner.data["level"]
        check_level_up(winner)
        winner.save()
    
    if not loser_id.startswith("bot_"):
        loser.data["losses"] += 1
        loser.data["win_streak"] = 0
        loser.data["total_duels"] += 1
        loser.data["pvp_rating"] = max(0, loser.data["pvp_rating"] - random.randint(10, 25))
        exp_l = duel.turn * 5 + duel.bet // 5
        loser.data["exp"] += exp_l
        loser.data["total_exp"] += exp_l
        check_level_up(loser)
        loser.save()
    
    result_text = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

👑 <b>{duel.get_player_name(duel.winner)}</b> побеждает!
💀 <b>{duel.get_player_name(3 - duel.winner)}</b> проигрывает

💰 Ставка: <b>{duel.bet}💰</b>
📊 Ходов: <b>{duel.turn}</b>
"""
    
    bot.edit_message_text(result_text, chat_id, message_id)

# ==================== МАГАЗИН ====================
@bot.callback_query_handler(func=lambda call: call.data == "trade_shop")
def shop_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚔ Оружие", callback_data="shopcat_weapon"),
        types.InlineKeyboardButton("👤 Шлемы", callback_data="shopcat_helmet"),
        types.InlineKeyboardButton("🦾 Броня", callback_data="shopcat_armor"),
        types.InlineKeyboardButton("🦿 Обувь", callback_data="shopcat_boots"),
        types.InlineKeyboardButton("🧪 Зелья", callback_data="shopcat_potion"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade")
    )
    
    player = Player(call.from_user.id)
    bot.edit_message_text(
        f"<b>🛒 МАГАЗИН</b>\n💰 <b>{player.data['money']}💰</b>",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("shopcat_"))
def shop_category(call):
    cat = call.data.split("_")[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    cat_names = {"weapon": "⚔ ОРУЖИЕ", "helmet": "👤 ШЛЕМЫ", "armor": "🦾 БРОНЯ", "boots": "🦿 ОБУВЬ", "potion": "🧪 ЗЕЛЬЯ"}
    cat_items = {k: v for k, v in items.items() if v.get("type") == cat}
    
    text = f"<b>{cat_names.get(cat, cat)}</b>\n💰 {player.data['money']}💰\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for ik, item in sorted(cat_items.items(), key=lambda x: x[1].get("price", 0)):
        if player.data["level"] < item.get("level_req", 1):
            continue
        
        r = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
        
        if item.get("type") == "weapon":
            s = f"Урон: {item['damage'][0]}-{item['damage'][1]}"
            if "element" in item:
                s += f" | {ELEMENTS.get(item['element'], {}).get('name', '')}"
        elif item.get("type") in ["helmet", "armor", "boots"]:
            s = f"Защита: {item.get('defense', 0)}"
            if "speed" in item:
                s += f" | Скорость: +{item['speed']}"
            if "hp_bonus" in item:
                s += f" | HP: +{item['hp_bonus']}"
        elif item.get("type") == "potion":
            s = f"Лечение: {item.get('heal', 0)}"
        else:
            s = ""
        
        text += f"{r} <b>{item['name']}</b> — {s}\n💰 {item['price']} | Ур.{item.get('level_req', 1)}\n\n"
        
        if player.data["money"] >= item["price"]:
            markup.add(types.InlineKeyboardButton(
                f"Купить: {item['name']} - {item['price']}💰",
                callback_data=f"buyitem_{ik}"
            ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="trade_shop"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buyitem_"))
def buy_item(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(ik) or limited_items.get(ik)
    if not item:
        bot.answer_callback_query(call.id, "❌ Не найден!")
        return
    
    if player.data["level"] < item.get("level_req", 1):
        bot.answer_callback_query(call.id, f"❌ Нужен {item.get('level_req', 1)} ур.!")
        return
    
    if player.data["money"] < item["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно!")
        return
    
    if ik in limited_items:
        if limited_items[ik]["remaining"] <= 0:
            bot.answer_callback_query(call.id, "❌ Закончился!")
            return
        limited_items[ik]["remaining"] -= 1
        save_json(DATA_FILES['limited'], limited_items)
    
    player.data["money"] -= item["price"]
    player.data["inventory"].append(ik)
    player.data["items_found"] += 1
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ {item['name']}!")
    shop_category(call)

# ==================== ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (кратко) ====================
@bot.callback_query_handler(func=lambda call: call.data == "trade_limited")
def limited_shop(call):
    if not limited_items:
        bot.edit_message_text("💎 Нет лимитированных", call.message.chat.id, call.message.message_id)
        return
    
    text = "<b>💎 ЛИМИТИРОВАННЫЕ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for ik, item in limited_items.items():
        if item["remaining"] > 0:
            pct = "█" * int(item["remaining"] / item["total"] * 10)
            emp = "░" * (10 - len(pct))
            text += f"<b>{item['name']}</b>\n[{pct}{emp}] {item['remaining']}/{item['total']}\n💰 <b>{item['price']}💰</b>\n\n"
            markup.add(types.InlineKeyboardButton(f"Купить - {item['price']}💰", callback_data=f"buyitem_{ik}"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "trade_daily")
def daily_bonus(call):
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
    
    old = player.data["level"]
    check_level_up(player)
    player.save()
    
    text = f"<b>🎁 БОНУС</b>\n💰 +{bonus}\n✨ +{exp}"
    if player.data["level"] > old:
        text += f"\n🎉 УРОВЕНЬ <b>{player.data['level']}</b>!"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "trade_market")
def market_menu(call):
    if not market_listings:
        bot.edit_message_text("📦 Рынок пуст\n/sell [номер] [цена]", call.message.chat.id, call.message.message_id)
        return
    
    text = "<b>💱 РЫНОК</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for lid, listing in list(market_listings.items())[:10]:
        item = items.get(listing["item_key"]) or limited_items.get(listing["item_key"])
        if item:
            text += f"📦 {item['name']} — <b>{listing['price']}💰</b>\n   👤 {listing.get('seller_name', 'Нет')}\n\n"
            markup.add(types.InlineKeyboardButton(f"Купить: {item['name']}", callback_data=f"mktbuy_{lid}"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mktbuy_"))
def market_buy(call):
    lid = call.data.split("_", 1)[1]
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if lid not in market_listings:
        bot.answer_callback_query(call.id, "❌ Продан!")
        return
    
    listing = market_listings[lid]
    if user_id == str(listing.get("seller_id")):
        bot.answer_callback_query(call.id, "❌ Своё!")
        return
    
    if player.data["money"] < listing["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно!")
        return
    
    player.data["money"] -= listing["price"]
    player.data["inventory"].append(listing["item_key"])
    player.save()
    
    seller = Player(listing["seller_id"])
    seller.data["money"] += listing["price"]
    seller.save()
    
    del market_listings[lid]
    save_json(DATA_FILES['market'], market_listings)
    
    item = items.get(listing["item_key"], {})
    bot.answer_callback_query(call.id, f"✅ {item.get('name', 'Предмет')}!")
    market_menu(call)

@bot.callback_query_handler(func=lambda call: call.data in ["trade_sell", "trade_my_lots", "back_to_trade"])
def trade_handlers(call):
    if call.data == "trade_sell":
        bot.edit_message_text("📦 /sell [номер] [цена]", call.message.chat.id, call.message.message_id)
    elif call.data == "trade_my_lots":
        uid = str(call.from_user.id)
        my = {k: v for k, v in market_listings.items() if str(v.get("seller_id")) == uid}
        
        if not my:
            bot.edit_message_text("📦 Нет лотов", call.message.chat.id, call.message.message_id)
            return
        
        text = "<b>📦 МОИ ЛОТЫ</b>\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for lid, listing in my.items():
            item = items.get(listing["item_key"]) or limited_items.get(listing["item_key"])
            if item:
                text += f"📦 {item['name']} — {listing['price']}💰\n"
                markup.add(types.InlineKeyboardButton(f"Снять: {item['name']}", callback_data=f"removelot_{lid}"))
        
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data == "back_to_trade":
        trade_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("removelot_"))
def remove_lot(call):
    lid = call.data.split("_", 1)[1]
    uid = str(call.from_user.id)
    
    if lid in market_listings and str(market_listings[lid].get("seller_id")) == uid:
        listing = market_listings[lid]
        player = Player(uid)
        player.data["inventory"].append(listing["item_key"])
        player.save()
        del market_listings[lid]
        save_json(DATA_FILES['market'], market_listings)
        bot.answer_callback_query(call.id, "✅ Снят!")
    
    trade_handlers(call)

# ==================== ГЕРОЙ ====================
@bot.callback_query_handler(func=lambda call: call.data == "hero_stats")
def hero_stats(call):
    user_id = call.from_user.id
    player = Player(user_id)
    s = player.get_full_stats()
    d = player.data
    
    wr = (d["wins"] / d["total_duels"] * 100) if d["total_duels"] > 0 else 0
    
    text = f"""
<b>📊 СТАТИСТИКА</b>

<b>{d['first_name']}</b> | {d['title']}
⭐ Ур.{d['level']} | 📊 {d['pvp_rating']}
💰 {d['money']}💰

⚔ Урон: {s['min_damage']}-{s['max_damage']}
🛡 Защита: Г:{s['head_defense']} Т:{s['body_defense']} Н:{s['legs_defense']}
💨 Скорость: {s['speed']:.0f}
💥 Крит: {s['crit_chance']:.1f}%

🏆 Побед: {d['wins']} | 💀 Поражений: {d['losses']}
📈 Винрейт: {wr:.1f}%
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "hero_inventory")
def hero_inventory(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if not player.data["inventory"]:
        bot.edit_message_text("🎒 Инвентарь пуст", call.message.chat.id, call.message.message_id)
        return
    
    counts = {}
    for ik in player.data["inventory"]:
        counts[ik] = counts.get(ik, 0) + 1
    
    text = "<b>🎒 ИНВЕНТАРЬ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    idx = 1
    for ik, cnt in counts.items():
        item = items.get(ik) or limited_items.get(ik)
        if not item:
            continue
        
        r = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
        eq = ""
        for slot, ek in player.data["equipment"].items():
            if ek == ik:
                eq = f" [🟢 {slot}]"
        
        ench = player.data.get("enchantments", {}).get(ik, {})
        ench_text = f" ✨{ench.get('name', '')}" if ench else ""
        
        text += f"{idx}. {r} {item['name']} x{cnt}{eq}{ench_text}\n"
        
        if item.get("type") in ["weapon", "helmet", "armor", "boots"]:
            markup.add(types.InlineKeyboardButton(f"Экипировать: {item['name']}", callback_data=f"equip_{ik}"))
            markup.add(types.InlineKeyboardButton(f"Зачаровать: {item['name']}", callback_data=f"enchant_{ik}"))
        elif item.get("type") == "potion":
            markup.add(types.InlineKeyboardButton(f"Использовать: {item['name']}", callback_data=f"use_{ik}"))
        
        markup.add(types.InlineKeyboardButton(f"Продать {item['name']}", callback_data=f"sellitem_{idx-1}"))
        idx += 1
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
def equip_item(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(ik) or limited_items.get(ik)
    if not item or ik not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌ Нельзя!")
        return
    
    slot_map = {"weapon": "weapon", "helmet": "head", "armor": "body", "boots": "legs"}
    slot = slot_map.get(item.get("type"))
    
    if not slot:
        bot.answer_callback_query(call.id, "❌ Нельзя экипировать!")
        return
    
    old = player.data["equipment"][slot]
    if old:
        player.data["inventory"].append(old)
    
    player.data["equipment"][slot] = ik
    player.data["inventory"].remove(ik)
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ {item['name']} экипирован!")
    hero_inventory(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("enchant_"))
def enchant_item(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(ik) or limited_items.get(ik)
    if not item or not item.get("enchantable"):
        bot.answer_callback_query(call.id, "❌ Нельзя зачаровать!")
        return
    
    if ik not in player.data["inventory"] and ik not in player.data["equipment"].values():
        bot.answer_callback_query(call.id, "❌ Предмет не у вас!")
        return
    
    cost = item.get("price", 100) // 2
    if player.data["money"] < cost:
        bot.answer_callback_query(call.id, f"❌ Нужно {cost}💰!")
        return
    
    player.data["money"] -= cost
    
    ench = random.choice(ENCHANT_EFFECTS)
    player.data.setdefault("enchantments", {})[ik] = {
        "name": ench["name"],
        "effect": ench["effect"],
        "value": ench["value"]
    }
    player.save()
    
    bot.answer_callback_query(call.id, f"✨ {ench['name']}!")
    hero_inventory(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sellitem_"))
def sell_item_inv(call):
    idx = int(call.data.split("_")[1])
    user_id = call.from_user.id
    player = Player(user_id)
    
    if idx < 0 or idx >= len(player.data["inventory"]):
        bot.answer_callback_query(call.id, "❌ Неверный индекс!")
        return
    
    ik = player.data["inventory"][idx]
    item = items.get(ik) or limited_items.get(ik)
    
    if not item:
        bot.answer_callback_query(call.id, "❌ Ошибка!")
        return
    
    sell_price = int(item.get("price", 10) * 0.6)
    
    player.data["inventory"].pop(idx)
    player.data["money"] += sell_price
    player.save()
    
    bot.answer_callback_query(call.id, f"💰 Продано за {sell_price}!")
    hero_inventory(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("use_"))
def use_potion(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(ik) or limited_items.get(ik)
    if not item or item.get("type") != "potion":
        bot.answer_callback_query(call.id, "❌ Нельзя!")
        return
    
    if ik not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌ Нет!")
        return
    
    stats = player.get_full_stats()
    
    if "heal" in item:
        if player.data["hp"] >= stats["max_hp"]:
            bot.answer_callback_query(call.id, "❌ Полное HP!")
            return
        player.data["hp"] = min(stats["max_hp"], player.data["hp"] + item["heal"])
    
    if "mana_restore" in item:
        player.data["mana"] = min(stats["max_mana"], player.data["mana"] + item["mana_restore"])
    
    player.data["inventory"].remove(ik)
    player.save()
    
    bot.answer_callback_query(call.id, "✅ Использовано!")
    hero_inventory(call)

@bot.callback_query_handler(func=lambda call: call.data == "hero_attributes")
def hero_attributes(call):
    user_id = call.from_user.id
    player = Player(user_id)
    st = player.data["stats"]
    pts = player.data["stat_points"]
    
    text = f"""
<b>⚡ ХАРАКТЕРИСТИКИ</b>
Очков: <b>{pts}</b>

💪 Сила: {st['strength']}
🏃 Ловкость: {st['agility']}
🧠 Интеллект: {st['intelligence']}
❤ Живучесть: {st['vitality']}
🍀 Удача: {st['luck']}
🛡 Защита: {st['defense']}
"""
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    if pts > 0:
        markup.add(
            types.InlineKeyboardButton("💪", callback_data="upstat_str"),
            types.InlineKeyboardButton("🏃", callback_data="upstat_agi"),
            types.InlineKeyboardButton("🧠", callback_data="upstat_int"),
            types.InlineKeyboardButton("❤", callback_data="upstat_vit"),
            types.InlineKeyboardButton("🍀", callback_data="upstat_luk"),
            types.InlineKeyboardButton("🛡", callback_data="upstat_def")
        )
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("upstat_"))
def upgrade_stat(call):
    smap = {"str": "strength", "agi": "agility", "int": "intelligence", "vit": "vitality", "luk": "luck", "def": "defense"}
    sk = smap[call.data.split("_")[1]]
    
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data["stat_points"] <= 0:
        bot.answer_callback_query(call.id, "❌ Нет очков!")
        return
    if player.data["stats"][sk] >= 100:
        bot.answer_callback_query(call.id, "❌ Максимум!")
        return
    
    player.data["stats"][sk] += 1
    player.data["stat_points"] -= 1
    player.save()
    
    nm = {"strength": "Сила", "agility": "Ловкость", "intelligence": "Интеллект", "vitality": "Живучесть", "luck": "Удача", "defense": "Защита"}
    bot.answer_callback_query(call.id, f"⬆ {nm[sk]}: {player.data['stats'][sk]}")
    hero_attributes(call)

@bot.callback_query_handler(func=lambda call: call.data in ["hero_achievements", "hero_enchantments", "hero_equipped", "hero_history", "hero_heal", "back_to_hero"])
def hero_handlers(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "hero_achievements":
        ach_list = [
            ("first_blood", "🩸 Первая кровь", "1 победа", player.data["wins"] >= 1),
            ("warrior", "⚔ Воин", "10 побед", player.data["wins"] >= 10),
            ("veteran", "🎖 Ветеран", "50 побед", player.data["wins"] >= 50),
            ("legend", "👑 Легенда", "100 побед", player.data["wins"] >= 100),
            ("rich", "💰 Богач", "10000 монет", player.data["money"] >= 10000),
            ("dmaster", "🏰 Мастер данжей", "10 данжей", player.data.get("dungeons_completed", 0) >= 10),
            ("collector", "🎒 Коллекционер", "20 предметов", player.data.get("items_found", 0) >= 20)
        ]
        
        text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(player.data['achievements'])}/7)\n\n"
        
        for aid, name, desc, cond in ach_list:
            done = aid in player.data["achievements"] or cond
            icon = "✅" if done else "🔒"
            text += f"{icon} <b>{name}</b>: {desc}\n"
            if cond and aid not in player.data["achievements"]:
                player.data["achievements"].append(aid)
        
        player.save()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_enchantments":
        ench_data = player.data.get("enchantments", {})
        if not ench_data:
            bot.edit_message_text("✨ Нет зачарований", call.message.chat.id, call.message.message_id)
            return
        
        text = "<b>✨ ЗАЧАРОВАНИЯ</b>\n\n"
        for ik, ench in ench_data.items():
            item = items.get(ik) or limited_items.get(ik)
            if item:
                text += f"📦 {item['name']}: <b>{ench.get('name', 'Нет')}</b>\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_equipped":
        equip = player.data["equipment"]
        text = "<b>👁 ЭКИПИРОВКА</b>\n\n"
        slot_names = {"weapon": "⚔ Оружие", "head": "👤 Голова", "body": "🦾 Тело", "legs": "🦿 Ноги"}
        
        for slot, sn in slot_names.items():
            ik = equip.get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                if item:
                    ench = player.data.get("enchantments", {}).get(ik, {})
                    ench_text = f" ✨{ench.get('name', '')}" if ench else ""
                    text += f"{sn}: <b>{item['name']}</b>{ench_text}\n"
                else:
                    text += f"{sn}: ❌ Удалён\n"
            else:
                text += f"{sn}: ❌ Пусто\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🔴 Снять всё", callback_data="unequip_all"),
            types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_history":
        history = player.data.get("battle_history", [])
        if not history:
            bot.edit_message_text("📋 История пуста", call.message.chat.id, call.message.message_id)
            return
        
        text = "<b>📋 ПОСЛЕДНИЕ 10 БОЁВ</b>\n\n"
        for battle in history[-10:]:
            icon = "🏆" if battle.get("result") == "win" else "💀" if battle.get("result") == "loss" else "🤝"
            text += f"{icon} vs {battle.get('opponent', 'Нет')}\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_heal":
        stats = player.get_full_stats()
        potions = [k for k in player.data["inventory"] if items.get(k, {}).get("type") == "potion" and items.get(k, {}).get("heal", 0) > 0]
        
        if not potions:
            bot.edit_message_text("💊 Нет зелий!", call.message.chat.id, call.message.message_id)
            return
        
        if player.data["hp"] >= stats["max_hp"]:
            bot.edit_message_text("💊 Полное здоровье!", call.message.chat.id, call.message.message_id)
            return
        
        pk = potions[0]
        potion = items[pk]
        
        player.data["hp"] = min(stats["max_hp"], player.data["hp"] + potion["heal"])
        player.data["inventory"].remove(pk)
        player.save()
        
        bot.edit_message_text(f"💊 <b>{potion['name']}</b>\n❤ HP: {player.data['hp']}/{stats['max_hp']}", call.message.chat.id, call.message.message_id)
    
    elif call.data == "back_to_hero":
        hero_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "unequip_all")
def unequip_all(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    for slot in ["weapon", "head", "body", "legs"]:
        ik = player.data["equipment"][slot]
        if ik:
            player.data["inventory"].append(ik)
            player.data["equipment"][slot] = None
    
    player.save()
    bot.answer_callback_query(call.id, "✅ Всё снято!")
    hero_handlers(call)

# ==================== МИР ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_dungeons")
def world_dungeons(call):
    text = """
<b>🏰 ПОДЗЕМЕЛЬЯ</b>

🐺 Логово волка (Ур. 1+)
🕷 Паучьи пещеры (Ур. 5+)
💀 Катакомбы (Ур. 10+)
🐉 Драконье логово (Ур. 15+)
👹 Бездна (Ур. 25+)

Кулдаун: 1 час
Пошаговые бои с боссами!
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, name in enumerate(["🐺 Логово волка", "🕷 Паучьи пещеры", "💀 Катакомбы", "🐉 Драконье логово", "👹 Бездна"], 1):
        markup.add(types.InlineKeyboardButton(name, callback_data=f"dung_{i}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dung_"))
def start_dungeon(call):
    dl = int(call.data.split("_")[1])
    user_id = call.from_user.id
    player = Player(user_id)
    
    level_reqs = [1, 5, 10, 15, 25]
    if player.data["level"] < level_reqs[dl - 1]:
        bot.answer_callback_query(call.id, f"❌ Нужен {level_reqs[dl-1]} ур.!")
        return
    
    if player.data.get("last_dungeon"):
        last = datetime.fromisoformat(player.data["last_dungeon"])
        if (datetime.now() - last) < timedelta(hours=1):
            r = timedelta(hours=1) - (datetime.now() - last)
            bot.answer_callback_query(call.id, f"⏰ {r.seconds//60} мин.")
            return
    
    # Создание босса (как бот)
    boss_level = level_reqs[dl - 1] * 2 + random.randint(1, 5)
    boss_id = f"boss_{random.randint(100000, 999999)}"
    
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    for slot, itype in [("head", "helmet"), ("body", "armor"), ("legs", "boots")]:
        sitems = [k for k, v in items.items() if v.get("type") == itype and v.get("level_req", 1) <= boss_level]
        if sitems and random.random() < 0.8:
            equip[slot] = random.choice(sitems)
    wpns = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= boss_level]
    if wpns:
        equip["weapon"] = random.choice(wpns)
    
    bosses = ["🐺 Вожак стаи", "🕷 Королева пауков", "💀 Некромант", "🐉 Древний дракон", "👹 Владыка бездны"]
    
    users[boss_id] = {
        "username": f"Boss_{boss_level}", "first_name": bosses[dl - 1],
        "money": 0, "level": boss_level, "exp": 0, "total_exp": 0,
        "hp": 100 + boss_level * 15, "max_hp": 100 + boss_level * 15,
        "mana": 50 + boss_level * 8, "max_mana": 50 + boss_level * 8,
        "stats": {"strength": 8 + boss_level, "agility": 6 + boss_level // 2,
                  "intelligence": 6 + boss_level // 3, "vitality": 8 + boss_level // 2,
                  "luck": 4 + boss_level // 4, "defense": boss_level + 5},
        "stat_points": 0, "wins": 0, "losses": 0, "draws": 0,
        "win_streak": 0, "best_streak": 0, "total_duels": 0,
        "pvp_rating": 1000, "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Босс", "titles_collected": ["Босс"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    reward = random.randint(50, 250) * dl * player.data["level"]
    exp = 50 * dl * player.data["level"]
    
    player.data["last_dungeon"] = datetime.now().isoformat()
    player.save()
    
    # Создание дуэли с боссом
    duel = DuelInstance(user_id, boss_id, "dungeon", 0)
    active_duels[str(user_id)] = duel
    
    # Босс выбирает защиту
    duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
    # Босс выбирает атаку
    boss_skills = duel.get_available_skills(2)
    if boss_skills:
        duel.execute_attack(2, random.choice(boss_skills), random.choice(list(BODY_PARTS.keys())))
    
    dungeon_progress[str(user_id)] = {"dungeon_level": dl, "reward": reward, "exp": exp, "boss_name": bosses[dl-1]}
    save_json(DATA_FILES['dungeons'], dungeon_progress)
    
    bot.edit_message_text(f"⚔ Бой с боссом <b>{bosses[dl-1]}</b>!", call.message.chat.id, call.message.message_id)
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

# Обработчик завершения дуэли для данжа
original_finish_duel = finish_duel

def finish_duel_wrapper(chat_id, message_id, duel):
    """Обёртка для обработки данжей"""
    if duel.duel_type == "dungeon":
        player_id = duel.p1_id if not duel.p1_id.startswith("boss_") else duel.p2_id
        
        if duel.winner == 1 and not duel.p1_id.startswith("boss_"):
            # Игрок победил босса
            dg = dungeon_progress.get(str(player_id), {})
            player = Player(player_id)
            player.data["money"] += dg.get("reward", 100)
            player.data["exp"] += dg.get("exp", 50)
            player.data["total_exp"] += dg.get("exp", 50)
            player.data["dungeons_completed"] = player.data.get("dungeons_completed", 0) + 1
            
            # Шанс на предмет
            if random.random() < 0.2:
                possible = [k for k, v in items.items() if v.get("level_req", 1) <= player.data["level"]]
                if possible:
                    ik = random.choice(possible)
                    player.data["inventory"].append(ik)
                    player.data["items_found"] += 1
            
            check_level_up(player)
            player.save()
            
            boss_name = dg.get("boss_name", "Босс")
            result_text = f"""
<b>🏰 ДАНЖ ПРОЙДЕН!</b>

Босс <b>{boss_name}</b> повержен!
💰 +{dg.get('reward', 100)} | ✨ +{dg.get('exp', 50)}
"""
            bot.edit_message_text(result_text, chat_id, message_id)
    else:
        original_finish_duel(chat_id, message_id, duel)

# Переопределяем finish_duel
finish_duel = finish_duel_wrapper

# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================
def check_level_up(player):
    level = player.data["level"]
    exp_needed = int(100 * (1.5 ** (level - 1)))
    
    leveled = False
    while player.data["exp"] >= exp_needed:
        player.data["exp"] -= exp_needed
        player.data["level"] += 1
        player.data["stat_points"] += 3
        player.data["max_hp"] += 15
        player.data["max_mana"] += 8
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

@bot.message_handler(commands=['sell', 'transfer'])
def misc_commands(message):
    cmd = message.text.split()[0].replace('/', '')
    user_id = message.from_user.id
    player = Player(user_id)
    
    if cmd == "sell":
        try:
            parts = message.text.split()
            idx = int(parts[1]) - 1
            price = int(parts[2])
        except:
            bot.send_message(message.chat.id, "❌ /sell [номер] [цена]")
            return
        
        if idx < 0 or idx >= len(player.data["inventory"]):
            bot.send_message(message.chat.id, "❌ Неверный номер!")
            return
        
        ik = player.data["inventory"][idx]
        item = items.get(ik) or limited_items.get(ik)
        
        player.data["inventory"].pop(idx)
        player.save()
        
        lid = f"{user_id}_{int(time.time())}"
        market_listings[lid] = {
            "seller_id": user_id, "seller_name": message.from_user.first_name,
            "item_key": ik, "price": price,
            "created_at": datetime.now().isoformat()
        }
        save_json(DATA_FILES['market'], market_listings)
        
        bot.send_message(message.chat.id, f"✅ {item.get('name', ik)} за {price}💰!")
    
    elif cmd == "transfer":
        if not message.reply_to_message:
            bot.send_message(message.chat.id, "❌ Ответьте на сообщение!")
            return
        
        target_id = message.reply_to_message.from_user.id
        
        try:
            idx = int(message.text.split()[1]) - 1
        except:
            bot.send_message(message.chat.id, "❌ /transfer [номер]")
            return
        
        if idx < 0 or idx >= len(player.data["inventory"]):
            bot.send_message(message.chat.id, "❌ Неверный номер!")
            return
        
        ik = player.data["inventory"].pop(idx)
        target = Player(target_id)
        target.data["inventory"].append(ik)
        
        player.save()
        target.save()
        
        item = items.get(ik) or limited_items.get(ik)
        bot.send_message(message.chat.id, f"✅ {item.get('name', ik)} передан!")

# ==================== КЛАНЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_clans")
def world_clans(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data.get("clan"):
        clan = clans.get(player.data["clan"], {})
        text = f"<b>🛡 {player.data['clan']}</b>\n👥 {len(clan.get('members', []))} уч.\n💰 Казна: {clan.get('treasury', 0)}💰"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("👥 Участники", callback_data="clan_members"),
            types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave")
        )
    else:
        text = "<b>🛡 КЛАНЫ</b>\n/createclan [имя]\n/joinclan [имя]"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("📋 Список", callback_data="clan_list"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(commands=['createclan', 'joinclan'])
def clan_commands(message):
    cmd = message.text.split()[0].replace('/', '')
    user_id = message.from_user.id
    player = Player(user_id)
    
    if cmd == "createclan":
        if player.data.get("clan"):
            bot.send_message(message.chat.id, "❌ Уже в клане!")
            return
        if player.data["money"] < 5000:
            bot.send_message(message.chat.id, "❌ 5000💰!")
            return
        
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ /createclan [имя]")
            return
        
        name = parts[1].strip()
        if name in clans:
            bot.send_message(message.chat.id, "❌ Существует!")
            return
        
        player.data["money"] -= 5000
        player.data["clan"] = name
        player.data["clan_role"] = "leader"
        player.save()
        
        clans[name] = {"leader_id": user_id, "leader_name": message.from_user.first_name, "members": [message.from_user.first_name], "treasury": 0, "created_at": datetime.now().isoformat()}
        save_json(DATA_FILES['clans'], clans)
        bot.send_message(message.chat.id, f"✅ Клан <b>{name}</b> создан!")
    
    elif cmd == "joinclan":
        if player.data.get("clan"):
            bot.send_message(message.chat.id, "❌ Уже в клане!")
            return
        
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ /joinclan [имя]")
            return
        
        name = parts[1].strip()
        if name not in clans:
            bot.send_message(message.chat.id, "❌ Не найден!")
            return
        
        player.data["clan"] = name
        player.data["clan_role"] = "member"
        player.save()
        
        if message.from_user.first_name not in clans[name].get("members", []):
            clans[name]["members"].append(message.from_user.first_name)
        save_json(DATA_FILES['clans'], clans)
        bot.send_message(message.chat.id, f"✅ Вы в <b>{name}</b>!")

# ==================== ТУРНИРЫ, ИВЕНТЫ, ТОП ====================
@bot.callback_query_handler(func=lambda call: call.data in ["world_tournaments", "world_events", "world_top", "world_help", "back_to_world"])
def world_handlers(call):
    if call.data == "world_tournaments":
        if not tournaments.get("active"):
            tournaments["active"] = {"name": "Турнир", "participants": [], "prize_pool": 5000, "status": "registration"}
            save_json(DATA_FILES['tournaments'], tournaments)
        
        tour = tournaments["active"]
        text = f"<b>🏟 ТУРНИР</b>\nУчастников: {len(tour.get('participants', []))}/16\nПриз: <b>{tour.get('prize_pool', 0)}💰</b>\nВзнос: 500💰"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🏆 Участвовать (500💰)", callback_data="tour_join"),
            types.InlineKeyboardButton("📋 Участники", callback_data="tour_list"),
            types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "world_events":
        current_event = events.get("current", {})
        if not current_event or datetime.fromisoformat(current_event.get("expires", "2000-01-01")) < datetime.now():
            new_event = {
                "name": random.choice(["🌋 Извержение", "❄ Шторм", "⚡ Гроза", "🌑 Затмение", "✨ Звездопад"]),
                "ench_reward": random.choice(ENCHANT_EFFECTS),
                "ench_chance": random.randint(10, 30),
                "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
            }
            events["current"] = new_event
            save_json(DATA_FILES['events'], events)
        
        ev = events["current"]
        time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
        minutes_left = max(0, time_left.seconds // 60)
        
        text = f"<b>🌍 ИВЕНТ</b>\n<b>{ev['name']}</b>\n✨ {ev['ench_reward']['name']}\n⏰ {minutes_left} мин."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "world_top":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("⭐ Уровень", callback_data="top_level"),
            types.InlineKeyboardButton("⚔ Победы", callback_data="top_wins"),
            types.InlineKeyboardButton("💰 Монеты", callback_data="top_money"),
            types.InlineKeyboardButton("🏆 Рейтинг", callback_data="top_rating"),
            types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world")
        )
        bot.edit_message_text("<b>📊 ТОП</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "world_help":
        text = "<b>ℹ ПОМОЩЬ</b>\n⚔ /duel\n🛒 /shop\n👤 /stats"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "back_to_world":
        world_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "tour_join")
def tour_join(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data["money"] < 500:
        bot.answer_callback_query(call.id, "❌ 500💰!")
        return
    
    tour = tournaments.get("active", {})
    participants = tour.get("participants", [])
    
    if str(user_id) in participants:
        bot.answer_callback_query(call.id, "❌ Уже участвуете!")
        return
    if len(participants) >= 16:
        bot.answer_callback_query(call.id, "❌ Заполнен!")
        return
    
    player.data["money"] -= 500
    player.save()
    
    participants.append(str(user_id))
    tour["participants"] = participants
    tour["prize_pool"] = tour.get("prize_pool", 0) + 500
    tournaments["active"] = tour
    save_json(DATA_FILES['tournaments'], tournaments)
    
    bot.answer_callback_query(call.id, "✅ Зарегистрированы!")

@bot.callback_query_handler(func=lambda call: call.data == "tour_list")
def tour_list(call):
    participants = tournaments.get("active", {}).get("participants", [])
    if not participants:
        bot.answer_callback_query(call.id, "📋 Пусто")
        return
    
    text = "<b>📋 УЧАСТНИКИ</b>\n\n"
    for i, uid in enumerate(participants[:16], 1):
        p = Player(uid)
        text += f"{i}. {p.data['first_name']} (Lv.{p.data['level']})\n"
    bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def show_top(call):
    cat = call.data.split("_")[1]
    
    if cat == "level":
        su = sorted(users.items(), key=lambda x: (x[1].get("level", 1), x[1].get("exp", 0)), reverse=True)[:10]
        t = "⭐ УРОВЕНЬ"
    elif cat == "wins":
        su = sorted(users.items(), key=lambda x: x[1].get("wins", 0), reverse=True)[:10]
        t = "⚔ ПОБЕДЫ"
    elif cat == "money":
        su = sorted(users.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]
        t = "💰 МОНЕТЫ"
    elif cat == "rating":
        su = sorted(users.items(), key=lambda x: x[1].get("pvp_rating", 1000), reverse=True)[:10]
        t = "🏆 РЕЙТИНГ"
    else:
        return
    
    medals = ["🥇", "🥈", "🥉"] + [f"{i}️⃣" for i in range(4, 11)]
    text = f"<b>{t}</b>\n\n"
    
    for i, (uid, data) in enumerate(su):
        if cat == "level":
            val = f"Ур.{data.get('level', 1)}"
        elif cat == "wins":
            val = f"{data.get('wins', 0)} побед"
        elif cat == "money":
            val = f"{data.get('money', 0)}💰"
        else:
            val = f"{data.get('pvp_rating', 1000)}"
        
        text += f"{medals[i]} {data.get('first_name', 'Игрок')}: {val}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_top"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== АДМИН ====================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("💰 Выдать деньги", callback_data="admin_givemoney"),
        types.InlineKeyboardButton("🎁 Выдать предмет", callback_data="admin_giveitem"),
        types.InlineKeyboardButton("⛔ Бан", callback_data="admin_banuser"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🔄 Сброс", callback_data="admin_reset"),
        types.InlineKeyboardButton("👁 Инфо", callback_data="admin_info"),
        types.InlineKeyboardButton("✅ Разбан", callback_data="admin_unban")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_handlers(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    if call.data == "admin_stats":
        text = f"👥 {len(users)} | 💰 {sum(u.get('money',0) for u in users.values())} | ⚔ {sum(u.get('total_duels',0) for u in users.values())}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    
    elif call.data == "admin_givemoney":
        bot.send_message(call.message.chat.id, "💰 /givemoney @username [сумма]")
    elif call.data == "admin_giveitem":
        bot.send_message(call.message.chat.id, "🎁 /giveitem @username [item_key]")
    elif call.data == "admin_banuser":
        bot.send_message(call.message.chat.id, "⛔ /ban @username [причина]")
    elif call.data == "admin_broadcast":
        bot.send_message(call.message.chat.id, "📢 /broadcast [текст]")
    elif call.data == "admin_reset":
        bot.send_message(call.message.chat.id, "🔄 /resetdaily @username")
    elif call.data == "admin_info":
        bot.send_message(call.message.chat.id, "👁 /userinfo @username")
    elif call.data == "admin_unban":
        bot.send_message(call.message.chat.id, "✅ /unban @username")

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'broadcast', 'resetdaily', 'userinfo'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd == "givemoney":
            # Ищем по username
            username = parts[1].replace('@', '')
            amount = int(parts[2])
            for uid, data in users.items():
                if data.get("username") == username:
                    p = Player(uid)
                    p.data["money"] += amount
                    p.save()
                    bot.send_message(message.chat.id, f"✅ {amount}💰 → @{username}")
                    return
            bot.send_message(message.chat.id, "❌ Пользователь не найден")
        
        elif cmd == "giveitem":
            username = parts[1].replace('@', '')
            ik = parts[2]
            for uid, data in users.items():
                if data.get("username") == username:
                    p = Player(uid)
                    p.data["inventory"].append(ik)
                    p.save()
                    bot.send_message(message.chat.id, f"✅ {ik} → @{username}")
                    return
            bot.send_message(message.chat.id, "❌ Пользователь не найден")
        
        elif cmd == "ban":
            username = parts[1].replace('@', '')
            reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение"
            for uid, data in users.items():
                if data.get("username") == username:
                    banned_users[uid] = {"reason": reason, "banned_at": datetime.now().isoformat()}
                    save_json(DATA_FILES['bans'], banned_users)
                    bot.send_message(message.chat.id, f"⛔ @{username} забанен!")
                    return
            bot.send_message(message.chat.id, "❌ Пользователь не найден")
        
        elif cmd == "unban":
            username = parts[1].replace('@', '')
            for uid, data in users.items():
                if data.get("username") == username and uid in banned_users:
                    del banned_users[uid]
                    save_json(DATA_FILES['bans'], banned_users)
                    bot.send_message(message.chat.id, f"✅ @{username} разбанен!")
                    return
            bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "broadcast":
            text = message.text.replace('/broadcast', '', 1).strip()
            if text:
                s, f = 0, 0
                for uid in users:
                    try:
                        bot.send_message(int(uid), f"📢 {text}")
                        s += 1
                    except:
                        f += 1
                bot.send_message(message.chat.id, f"✅ {s} | ❌ {f}")
        
        elif cmd == "resetdaily":
            username = parts[1].replace('@', '')
            for uid, data in users.items():
                if data.get("username") == username:
                    p = Player(uid)
                    p.data["last_daily"] = None
                    p.data["last_dungeon"] = None
                    p.save()
                    bot.send_message(message.chat.id, f"✅ @{username}")
                    return
            bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "userinfo":
            username = parts[1].replace('@', '')
            for uid, data in users.items():
                if data.get("username") == username:
                    p = Player(uid)
                    d = p.data
                    text = f"<b>👤 @{username}</b>\nИмя: {d['first_name']}\nУр.: {d['level']}\n💰 {d['money']}\nРейтинг: {d['pvp_rating']}"
                    bot.send_message(message.chat.id, text)
                    return
            bot.send_message(message.chat.id, "❌ Не найден")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== ЗАПУСК ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v10.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print("=" * 60)
    print("✅ HP одинаковые в дуэлях")
    print("✅ Защита зависит от экипировки")
    print("✅ Навыки оружия")
    print("✅ Поиск соперника / бот")
    print("✅ Данжи с пошаговыми боями")
    print("✅ Админ через @username")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
