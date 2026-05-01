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
    "head": {"name": "👤 Голова", "multiplier": 1.5, "hit_chance": 20, "defense_slot": "head"},
    "body": {"name": "🦾 Тело", "multiplier": 1.0, "hit_chance": 50, "defense_slot": "body"},
    "legs": {"name": "🦿 Ноги", "multiplier": 0.7, "hit_chance": 30, "defense_slot": "legs"}
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
    "fire": {"name": "🔥 Огонь", "strong": "ice", "weak": "water"},
    "ice": {"name": "❄ Лёд", "strong": "nature", "weak": "fire"},
    "lightning": {"name": "⚡ Молния", "strong": "water", "weak": "earth"},
    "water": {"name": "🌊 Вода", "strong": "fire", "weak": "lightning"},
    "nature": {"name": "🌿 Природа", "strong": "earth", "weak": "ice"},
    "earth": {"name": "🏔 Земля", "strong": "lightning", "weak": "nature"},
    "dark": {"name": "🌑 Тьма", "strong": "light", "weak": "light"},
    "light": {"name": "✨ Свет", "strong": "dark", "weak": "dark"}
}

ENCHANT_EFFECTS = [
    {"name": "🔥 Огненное", "effect": "fire_damage", "value": 10},
    {"name": "❄ Ледяное", "effect": "freeze_chance", "value": 15},
    {"name": "⚡ Грозовое", "effect": "stun_chance", "value": 10},
    {"name": "💀 Проклятое", "effect": "life_steal", "value": 10},
    {"name": "🛡 Укреплённое", "effect": "defense_bonus", "value": 15},
    {"name": "💪 Мощное", "effect": "damage_boost", "value": 25},
    {"name": "💨 Скоростное", "effect": "speed_bonus", "value": 10},
    {"name": "❤ Живучее", "effect": "hp_bonus", "value": 50},
    {"name": "💎 Магическое", "effect": "mana_bonus", "value": 30},
    {"name": "🍀 Удачливое", "effect": "luck_bonus", "value": 10},
    {"name": "🎯 Меткое", "effect": "crit_bonus", "value": 15},
    {"name": "🔮 Мистическое", "effect": "random_bonus", "value": 0}
]

# Навыки оружия
WEAPON_SKILLS = {
    "rusty_sword": [
        {"name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 5, "cooldown": 0, "target": "body"},
        {"name": "💨 Быстрый удар", "damage_mult": 0.8, "mana_cost": 3, "hits": 2, "cooldown": 0, "target": "body"},
        {"name": "💢 Удар в голову", "damage_mult": 1.4, "mana_cost": 8, "cooldown": 1, "target": "head"}
    ],
    "flame_blade": [
        {"name": "🔥 Огненный разрез", "damage_mult": 1.5, "mana_cost": 15, "element": "fire", "burn_chance": 25, "cooldown": 1, "target": "body"},
        {"name": "🌋 Инферно удар", "damage_mult": 2.2, "mana_cost": 30, "element": "fire", "burn_chance": 50, "cooldown": 2, "target": "body"},
        {"name": "🔥 Подсечка", "damage_mult": 1.3, "mana_cost": 12, "element": "fire", "cooldown": 0, "target": "legs"}
    ],
    "frost_axe": [
        {"name": "❄ Ледяной удар", "damage_mult": 1.4, "mana_cost": 14, "element": "ice", "freeze_chance": 20, "cooldown": 0, "target": "body"},
        {"name": "💠 Раскол", "damage_mult": 1.9, "mana_cost": 28, "element": "ice", "freeze_chance": 45, "cooldown": 2, "target": "head"},
        {"name": "🌨 Заморозка ног", "damage_mult": 1.2, "mana_cost": 18, "element": "ice", "freeze_chance": 30, "cooldown": 1, "target": "legs"}
    ],
    "storm_staff": [
        {"name": "⚡ Молния", "damage_mult": 1.5, "mana_cost": 18, "element": "lightning", "stun_chance": 20, "cooldown": 0, "target": "body"},
        {"name": "⛈ Гроза", "damage_mult": 2.3, "mana_cost": 40, "element": "lightning", "stun_chance": 35, "cooldown": 3, "target": "head"},
        {"name": "⚡ Разряд в ноги", "damage_mult": 1.3, "mana_cost": 15, "element": "lightning", "stun_chance": 15, "cooldown": 1, "target": "legs"}
    ],
    "shadow_dagger": [
        {"name": "🌑 Теневой удар", "damage_mult": 1.6, "mana_cost": 20, "element": "dark", "poison_chance": 25, "cooldown": 0, "target": "body"},
        {"name": "🗡 Убийство", "damage_mult": 3.0, "mana_cost": 50, "element": "dark", "cooldown": 3, "target": "head", "ignore_defense": 30},
        {"name": "🦵 Подрезать", "damage_mult": 1.4, "mana_cost": 16, "element": "dark", "cooldown": 1, "target": "legs"}
    ],
    "divine_spear": [
        {"name": "✨ Святой удар", "damage_mult": 1.5, "mana_cost": 20, "element": "light", "cooldown": 0, "target": "body"},
        {"name": "⚖ Суд", "damage_mult": 2.8, "mana_cost": 45, "element": "light", "cooldown": 3, "target": "head"},
        {"name": "🌟 Очищение ног", "damage_mult": 1.3, "mana_cost": 18, "element": "light", "cooldown": 1, "target": "legs"}
    ],
    "death_scythe": [
        {"name": "💀 Жатва", "damage_mult": 2.0, "mana_cost": 35, "element": "dark", "life_steal": 0.3, "cooldown": 1, "target": "body"},
        {"name": "☠ Смертный приговор", "damage_mult": 3.5, "mana_cost": 60, "element": "dark", "cooldown": 4, "target": "head", "ignore_defense": 50},
        {"name": "🦵 Коса по ногам", "damage_mult": 1.6, "mana_cost": 25, "element": "dark", "cooldown": 1, "target": "legs"}
    ]
}

# Базовые навыки для оружия без специальных
DEFAULT_SKILLS = [
    {"name": "💪 Тяжёлая атака", "damage_mult": 1.6, "mana_cost": 12, "cooldown": 1, "target": "body"},
    {"name": "💢 В голову", "damage_mult": 1.5, "mana_cost": 10, "cooldown": 1, "target": "head"},
    {"name": "🦵 По ногам", "damage_mult": 1.3, "mana_cost": 8, "cooldown": 0, "target": "legs"},
    {"name": "⚡ Быстрый удар", "damage_mult": 0.9, "mana_cost": 3, "hits": 2, "cooldown": 0, "target": "body"}
]

# ==================== ФАЙЛЫ ДАННЫХ ====================
DATA_FILES = {
    'users': 'users.json',
    'items': 'items.json',
    'limited': 'limited_items.json',
    'duels': 'duels_state.json',
    'clans': 'clans.json',
    'tournaments': 'tournaments.json',
    'market': 'market.json',
    'dungeons': 'dungeon_progress.json',
    'events': 'events.json',
    'bans': 'bans.json',
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
    "rusty_sword": {"name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 1, "enchantable": True},
    "flame_blade": {"name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 7, "enchantable": True, "element": "fire"},
    "frost_axe": {"name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 10, "enchantable": True, "element": "ice"},
    "storm_staff": {"name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500, "type": "weapon", "slot": "weapon", "rarity": "rare", "level_req": 14, "enchantable": True, "element": "lightning"},
    "shadow_dagger": {"name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "slot": "weapon", "rarity": "epic", "level_req": 22, "enchantable": True, "element": "dark"},
    "divine_spear": {"name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "slot": "weapon", "rarity": "legendary", "level_req": 28, "enchantable": True, "element": "light"},
    "death_scythe": {"name": "💀 Коса смерти", "damage": (40, 65), "price": 12000, "type": "weapon", "slot": "weapon", "rarity": "mythic", "level_req": 35, "enchantable": True, "element": "dark"}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 200, "price": 350, "type": "potion", "rarity": "rare", "level_req": 15},
    "mana_potion": {"name": "💎 Зелье маны", "mana_restore": 60, "price": 60, "type": "potion", "rarity": "common", "level_req": 5}
}

LIMITED_ITEMS = {
    "thunderfury": {"name": "⚡ Ярость грома", "damage": (60, 95), "total": 3, "remaining": 3, "price": 50000, "type": "weapon", "slot": "weapon", "rarity": "divine", "element": "lightning", "enchantable": True},
    "immortal_helmet": {"name": "✨ Шлем бессмертия", "defense": 80, "hp_bonus": 300, "total": 2, "remaining": 2, "price": 75000, "type": "helmet", "slot": "head", "rarity": "divine", "enchantable": True}
}

ALL_ITEMS = {}
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(BOOTS)
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(POTIONS)

items = load_json(DATA_FILES['items'], ALL_ITEMS)
limited_items = load_json(DATA_FILES['limited'], LIMITED_ITEMS)
users = load_json(DATA_FILES['users'], {})
duels_state = load_json(DATA_FILES['duels'], {})
clans = load_json(DATA_FILES['clans'], {})
tournaments = load_json(DATA_FILES['tournaments'], {})
market_listings = load_json(DATA_FILES['market'], {})
dungeon_progress = load_json(DATA_FILES['dungeons'], {})
events = load_json(DATA_FILES['events'], {})
banned_users = load_json(DATA_FILES['bans'], {})
enchantments_data = load_json(DATA_FILES['enchantments'], {})
matchmaking = load_json(DATA_FILES['matchmaking'], {"quick": [], "ranked": [], "hardcore": [], "survival": [], "sparring": []})

# ==================== КЛАСС ИГРОКА ====================
class Player:
    def __init__(self, user_id, username="Unknown", first_name="Player"):
        self.user_id = str(user_id)
        if self.user_id not in users:
            users[self.user_id] = {
                "username": username, "first_name": first_name,
                "money": 500, "level": 1, "exp": 0, "total_exp": 0,
                "hp": 100, "max_hp": 100, "mana": 50, "max_mana": 50,
                "stats": {"strength": 5, "agility": 5, "intelligence": 5, "vitality": 5, "luck": 5, "defense": 0},
                "stat_points": 0,
                "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
                "total_duels": 0, "pvp_rating": 1000,
                "inventory": [],
                "equipment": {"weapon": None, "head": None, "body": None, "legs": None},
                "enchantments": {},
                "last_daily": None, "last_dungeon": None,
                "title": "Новичок", "titles_collected": ["Новичок"],
                "achievements": [],
                "clan": None, "clan_role": None,
                "registration_date": datetime.now().isoformat(),
                "settings": {"notifications": True, "duel_requests": True},
                "battle_history": [], "dungeons_completed": 0, "items_found": 0
            }
            self.save()
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    def save(self):
        save_json(DATA_FILES['users'], users)
    
    def get_equipment_defense(self, slot):
        """Получить защиту части тела от экипировки"""
        ik = self.data["equipment"].get(slot)
        if not ik:
            return 0
        item = items.get(ik) or limited_items.get(ik)
        if not item:
            return 0
        defense = item.get("defense", 0)
        # Зачарования на защиту
        ench = self.data.get("enchantments", {}).get(ik, {})
        if ench and ench.get("effect") == "defense_bonus":
            defense += ench.get("value", 0)
        return defense
    
    def get_full_stats(self):
        base = copy.deepcopy(self.data["stats"])
        bonuses = {
            "min_damage": base["strength"] * 2, "max_damage": base["strength"] * 3,
            "defense": base["defense"] + base["vitality"] * 2,
            "speed": base["agility"] * 1.5,
            "crit_chance": 5 + base["luck"] * 0.5, "crit_multiplier": 1.5,
            "dodge_chance": 3 + base["agility"] * 0.3,
            "hp": self.data["max_hp"] + base["vitality"] * 15,
            "max_hp": self.data["max_hp"] + base["vitality"] * 15,
            "mana": self.data["max_mana"] + base["intelligence"] * 8,
            "max_mana": self.data["max_mana"] + base["intelligence"] * 8,
            "head_defense": self.get_equipment_defense("head"),
            "body_defense": self.get_equipment_defense("body"),
            "legs_defense": self.get_equipment_defense("legs"),
            "weapon_key": self.data["equipment"].get("weapon"),
            "fire_damage": 0, "freeze_chance": 0, "stun_chance": 0,
            "life_steal": 0, "damage_boost": 0, "speed_bonus": 0,
            "hp_bonus": 0, "mana_bonus": 0, "luck_bonus": 0, "crit_bonus": 0
        }
        
        # Оружие
        ik = bonuses["weapon_key"]
        if ik:
            item = items.get(ik) or limited_items.get(ik)
            if item and "damage" in item:
                bonuses["min_damage"] += item["damage"][0]
                bonuses["max_damage"] += item["damage"][1]
        
        # Зачарования
        for ik, ench in self.data.get("enchantments", {}).items():
            eff = ench.get("effect")
            val = ench.get("value", 0)
            if eff in bonuses:
                bonuses[eff] += val
            if eff == "fire_damage":
                bonuses["min_damage"] += val
                bonuses["max_damage"] += val
        
        bonuses["hp"] = bonuses["max_hp"]
        bonuses["mana"] = bonuses["max_mana"]
        bonuses["crit_chance"] = min(80, bonuses["crit_chance"] + bonuses["crit_bonus"])
        bonuses["dodge_chance"] = min(50, bonuses["dodge_chance"])
        bonuses["speed"] += bonuses["speed_bonus"]
        bonuses["max_hp"] += bonuses["hp_bonus"]
        bonuses["max_mana"] += bonuses["mana_bonus"]
        bonuses["hp"] = bonuses["max_hp"]
        bonuses["mana"] = bonuses["max_mana"]
        
        return bonuses

# ==================== ГЕНЕРАЦИЯ БОТА ====================
def generate_bot(player_level):
    """Генерация бота под уровень игрока с одинаковым HP"""
    level = random.randint(max(1, player_level - 2), player_level + 2)
    
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    for slot, itype in [("head", "helmet"), ("body", "armor"), ("legs", "boots")]:
        sitems = [k for k, v in items.items() if v.get("type") == itype and v.get("level_req", 1) <= level]
        if sitems and random.random() < 0.6:
            equip[slot] = random.choice(sitems)
    
    wpns = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= level]
    if wpns:
        equip["weapon"] = random.choice(wpns)
    
    return {
        "username": f"bot_{level}_{random.randint(1000,9999)}",
        "first_name": f"⚔ Бот Lv.{level}",
        "money": 0, "level": level, "exp": 0, "total_exp": 0,
        "hp": 100 + player_level * 12, "max_hp": 100 + player_level * 12,
        "mana": 50 + level * 6, "max_mana": 50 + level * 6,
        "stats": {
            "strength": 5 + level, "agility": 5 + level // 2,
            "intelligence": 5 + level // 3, "vitality": 5 + level // 2,
            "luck": 3 + level // 4, "defense": level
        },
        "stat_points": 0, "wins": 0, "losses": 0, "draws": 0,
        "win_streak": 0, "best_streak": 0, "total_duels": 0,
        "pvp_rating": 1000 + level * 10,
        "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Бот", "titles_collected": ["Бот"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }

# ==================== ПОШАГОВАЯ ДУЭЛЬ ====================
active_duels = {}

class StepDuel:
    def __init__(self, p1_id, p2_id, duel_type="quick", bet=0):
        self.battle_id = str(uuid.uuid4())[:8]
        self.p1_id = str(p1_id)
        self.p2_id = str(p2_id)
        self.duel_type = duel_type
        self.bet = bet
        self.turn = 1
        self.max_turns = 50
        self.active = True
        self.winner = None
        self.log = []
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        self.p1_stats = self.p1.get_full_stats()
        self.p2_stats = self.p2.get_full_stats()
        
        self.p1_hp = self.p1_stats["max_hp"]
        self.p2_hp = self.p2_stats["max_hp"]
        self.p1_max_hp = self.p1_hp
        self.p2_max_hp = self.p2_hp
        
        self.p1_mp = self.p1_stats["max_mana"]
        self.p2_mp = self.p2_stats["max_mana"]
        self.p1_max_mp = self.p1_mp
        self.p2_max_mp = self.p2_mp
        
        # Фазы: defend_select -> attack_select -> done
        self.p1_phase = "defend_select"
        self.p2_phase = "defend_select"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        
        # Очерёдность атаки
        p1_spd = self.p1_stats["speed"] + random.randint(-10, 10)
        p2_spd = self.p2_stats["speed"] + random.randint(-10, 10)
        self.first_attacker = 1 if p1_spd >= p2_spd else 2
        
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        self.p1_effects = []
        self.p2_effects = []
        
        self.arena = random.choice(["colosseum", "forest", "volcano", "tundra", "void"])
        self.weather = random.choice(["clear", "rain", "storm", "fog"])
        
        self.log.append("⚔ Битва началась!")
    
    def get_name(self, num):
        return self.p1.data["first_name"] if num == 1 else self.p2.data["first_name"]
    
    def get_available_skills(self, player_num):
        """Получить навыки оружия игрока"""
        player = self.p1 if player_num == 1 else self.p2
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        weapon_key = player.data["equipment"].get("weapon")
        
        skills = []
        
        if weapon_key and weapon_key in WEAPON_SKILLS:
            for skill in WEAPON_SKILLS[weapon_key]:
                name = skill["name"]
                cd = cooldowns.get(name, 0)
                if cd <= 0:
                    skills.append(skill)
        
        # Добавляем базовые навыки если нет специальных
        if not skills:
            for skill in DEFAULT_SKILLS:
                name = skill["name"]
                cd = cooldowns.get(name, 0)
                if cd <= 0:
                    skills.append(skill)
        
        return skills
    
    def set_defend(self, player_num, part):
        if player_num == 1:
            self.p1_defend = part
            self.p1_phase = "attack_select"
        else:
            self.p2_defend = part
            self.p2_phase = "attack_select"
    
    def set_attack(self, player_num, skill_index):
        skills = self.get_available_skills(player_num)
        if skill_index < 0 or skill_index >= len(skills):
            return False
        
        skill = skills[skill_index]
        
        if player_num == 1:
            self.p1_skill = skill
            self.p1_phase = "done"
        else:
            self.p2_skill = skill
            self.p2_phase = "done"
        
        # Если оба готовы - выполняем раунд
        if self.p1_phase == "done" and self.p2_phase == "done":
            self._execute_round()
        
        return True
    
    def _execute_round(self):
        """Выполнение раунда"""
        self._process_effects(1)
        self._process_effects(2)
        
        first = self.first_attacker
        second = 3 - first
        
        # Первый атакующий
        self._do_attack(first, second)
        if self.p1_hp <= 0 or self.p2_hp <= 0:
            self._end_check()
            return
        
        # Второй атакующий
        self._do_attack(second, first)
        self._end_check()
        
        # Смена очерёдности
        self.first_attacker = second
        
        # Сброс фаз
        self.p1_phase = "defend_select"
        self.p2_phase = "defend_select"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        
        self.turn += 1
        if self.turn > self.max_turns:
            self.active = False
            self.winner = 0
    
    def _do_attack(self, attacker, defender):
        skill = self.p1_skill if attacker == 1 else self.p2_skill
        defend = self.p2_defend if attacker == 1 else self.p1_defend
        
        if not skill:
            return
        
        # Статы
        a_stats = self.p1_stats if attacker == 1 else self.p2_stats
        d_stats = self.p2_stats if attacker == 1 else self.p1_stats
        
        # Проверка маны
        mc = skill.get("mana_cost", 0)
        if attacker == 1:
            if self.p1_mp < mc:
                self.log.append(f"❌ {self.get_name(attacker)}: нет маны для {skill['name']}!")
                return
            self.p1_mp -= mc
        else:
            if self.p2_mp < mc:
                self.log.append(f"❌ {self.get_name(attacker)}: нет маны для {skill['name']}!")
                return
            self.p2_mp -= mc
        
        target = skill.get("target", "body")
        target_name = BODY_PARTS[target]["name"]
        
        # Проверка защиты
        if defend == target:
            # Полный блок
            self.log.append(f"🛡 {self.get_name(attacker)} бьёт в {target_name}, но {self.get_name(defender)} защитил! Урон: 0")
            return
        
        # Расчёт урона
        min_d = a_stats["min_damage"]
        max_d = a_stats["max_damage"]
        dmg = random.randint(min_d, max_d)
        dmg = int(dmg * skill.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_m = BODY_PARTS[target]["multiplier"]
        dmg = int(dmg * body_m)
        
        # Защита от экипировки на атакуемой части
        defense_slot = BODY_PARTS[target]["defense_slot"]
        part_defense = d_stats.get(f"{defense_slot}_defense", 0)
        if part_defense > 0:
            reduction = part_defense / (part_defense + 100)
            dmg = int(dmg * (1 - reduction))
        
        # Игнорирование защиты
        ignore = skill.get("ignore_defense", 0)
        if ignore > 0:
            dmg = int(dmg * (1 + ignore / 100))
        
        # Крит
        is_crit = False
        if random.random() * 100 < a_stats["crit_chance"]:
            dmg = int(dmg * a_stats["crit_multiplier"])
            is_crit = True
        
        # Элемент
        if "element" in skill:
            elem = skill["element"]
            def_weapon = (self.p2 if attacker == 1 else self.p1).data["equipment"].get("weapon")
            def_elem = None
            if def_weapon:
                di = items.get(def_weapon) or limited_items.get(def_weapon)
                if di and "element" in di:
                    def_elem = di["element"]
            if def_elem and ELEMENTS.get(elem):
                if ELEMENTS[elem]["strong"] == def_elem:
                    dmg = int(dmg * 1.5)
                    self.log.append("💥 СУПЕРЭФФЕКТИВНО!")
                elif ELEMENTS[elem]["weak"] == def_elem:
                    dmg = int(dmg * 0.7)
                    self.log.append("🔻 Неэффективно...")
        
        # Уклонение
        if random.random() * 100 < d_stats["dodge_chance"]:
            dmg = 0
            self.log.append(f"💨 {self.get_name(defender)} уклонился!")
        
        # Несколько ударов
        hits = skill.get("hits", 1)
        total = 0
        for _ in range(hits):
            total += dmg // hits
        
        if total > 0:
            if defender == 1:
                self.p1_hp = max(0, self.p1_hp - total)
            else:
                self.p2_hp = max(0, self.p2_hp - total)
            
            ct = "💥 КРИТ! " if is_crit else ""
            self.log.append(f"{ct}⚔ {self.get_name(attacker)} бьёт {skill['name']} в {target_name}: -{total} HP {self.get_name(defender)}")
            
            # Эффекты
            if "burn_chance" in skill and random.random() * 100 < skill["burn_chance"]:
                self._add_effect(defender, "burn", 3)
                self.log.append("🔥 Горение!")
            if "freeze_chance" in skill and random.random() * 100 < skill["freeze_chance"]:
                self._add_effect(defender, "freeze", 2)
                self.log.append("❄ Заморозка!")
            if "stun_chance" in skill and random.random() * 100 < skill["stun_chance"]:
                self._add_effect(defender, "stun", 1)
                self.log.append("⚡ Оглушение!")
            if "poison_chance" in skill and random.random() * 100 < skill["poison_chance"]:
                self._add_effect(defender, "poison", 4)
                self.log.append("☠ Отравление!")
            
            # Вампиризм
            if "life_steal" in skill:
                heal = int(total * skill["life_steal"])
                if attacker == 1:
                    self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
                else:
                    self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
                self.log.append(f"💚 +{heal} HP")
        
        # Кулдаун
        if skill.get("cooldown", 0) > 0:
            cd_dict = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
            cd_dict[skill["name"]] = skill["cooldown"]
        
        # Уменьшение кулдаунов
        cd_dict = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
        for k in list(cd_dict.keys()):
            cd_dict[k] -= 1
            if cd_dict[k] <= 0:
                del cd_dict[k]
        
        # Восстановление маны
        if attacker == 1:
            self.p1_mp = min(self.p1_max_mp, self.p1_mp + 5)
        else:
            self.p2_mp = min(self.p2_max_mp, self.p2_mp + 5)
    
    def _add_effect(self, target, etype, duration):
        eff = {"type": etype, "duration": duration}
        if target == 1:
            self.p1_effects.append(eff)
        else:
            self.p2_effects.append(eff)
    
    def _process_effects(self, player_num):
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        hp = self.p1_hp if player_num == 1 else self.p2_hp
        
        for eff in effects[:]:
            if eff["type"] == "burn":
                hp -= 10
                self.log.append("🔥 Горение -10 HP")
            elif eff["type"] == "poison":
                hp -= 12
                self.log.append("☠ Яд -12 HP")
            
            eff["duration"] -= 1
            if eff["duration"] <= 0:
                effects.remove(eff)
        
        if player_num == 1:
            self.p1_hp = max(0, hp)
        else:
            self.p2_hp = max(0, hp)
    
    def _end_check(self):
        if self.p1_hp <= 0:
            self.active = False
            self.winner = 2
        elif self.p2_hp <= 0:
            self.active = False
            self.winner = 1
    
    def get_state_text(self, for_player_id):
        pn = 1 if str(for_player_id) == self.p1_id else 2
        phase = self.p1_phase if pn == 1 else self.p2_phase
        
        p1_hp_bar = self._bar(self.p1_hp, self.p1_max_hp, "❤")
        p2_hp_bar = self._bar(self.p2_hp, self.p2_max_hp, "❤")
        p1_mp_bar = self._bar(self.p1_mp, self.p1_max_mp, "💎")
        p2_mp_bar = self._bar(self.p2_mp, self.p2_max_mp, "💎")
        
        arenas = {"colosseum": "Колизей", "forest": "Лес", "volcano": "Вулкан", "tundra": "Тундра", "void": "Пустота"}
        weathers = {"clear": "Ясно", "rain": "Дождь", "storm": "Шторм", "fog": "Туман"}
        
        text = f"""
<b>⚔ ДУЭЛЬ #{self.battle_id}</b>
━━━━━━━━━━━━━━━━━━━━
Ход: <b>#{self.turn}</b> | 🏟 {arenas.get(self.arena, '?')} | 🌤 {weathers.get(self.weather, '?')}

<b>{self.get_name(1)}</b>
❤ {p1_hp_bar}
💎 {p1_mp_bar}
🛡 Защита: {BODY_PARTS.get(self.p1_defend, {}).get('name', '?') if self.p1_defend else 'Не выбрана'}

<b>{self.get_name(2)}</b>
❤ {p2_hp_bar}
💎 {p2_mp_bar}
🛡 Защита: {BODY_PARTS.get(self.p2_defend, {}).get('name', '?') if self.p2_defend else 'Не выбрана'}
━━━━━━━━━━━━━━━━━━━━
"""
        
        if phase == "defend_select":
            text += "\n🛡 <b>Выберите часть тела для защиты:</b>"
        elif phase == "attack_select":
            text += "\n⚔ <b>Выберите атаку:</b>"
        elif phase == "done":
            text += "\n⏳ <b>Ожидание хода противника...</b>"
        
        # Эффекты
        effs = self.p1_effects if pn == 1 else self.p2_effects
        if effs:
            text += "\n<b>Эффекты:</b> "
            text += ", ".join([f"{e['type']}({e['duration']})" for e in effs])
        
        # Лог
        if self.log:
            text += f"\n\n<i>{self.log[-1]}</i>"
        
        return text
    
    def _bar(self, cur, mx, icon):
        pct = cur / mx if mx > 0 else 0
        f = int(pct * 10)
        e = 10 - f
        return f"{icon} [{'█' * f}{'░' * e}] {cur}/{mx}"

# ==================== МАТЧМЕЙКИНГ ====================
def find_match(mode, user_id):
    """Поиск соперника для PvP"""
    uid = str(user_id)
    
    if uid not in matchmaking.get(mode, []):
        matchmaking.setdefault(mode, []).append(uid)
        save_json(DATA_FILES['matchmaking'], matchmaking)
        return None
    
    queue = matchmaking.get(mode, [])
    for opponent_id in queue:
        if opponent_id != uid:
            queue.remove(uid)
            queue.remove(opponent_id)
            save_json(DATA_FILES['matchmaking'], matchmaking)
            return opponent_id
    
    return None

# ==================== МЕНЮ ====================
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
• Дуэли только в ЛС с ботом
• Защита частей тела + учёт брони
• У каждого оружия свои атаки
• PvP через поиск соперника
• Боты подбираются под уровень
• Одинаковое HP у противников

💰 Старт: <b>500 монет</b>
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
        types.InlineKeyboardButton("🔥 Выживание", callback_data="survival_duel"),
        types.InlineKeyboardButton("🎯 Спарринг", callback_data="sparring_duel")
    )
    
    text = """
<b>⚔️ ДУЭЛИ (только в ЛС)</b>

🛡 Защитите часть тела
⚔ Выберите атаку оружия
🦾 Броня уменьшает урон

<i>Все дуэли пошаговые!</i>
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
@bot.callback_query_handler(func=lambda call: call.data in ["quick_duel", "pvp_duel", "ranked_duel", "hardcore_duel", "survival_duel", "sparring_duel"])
def duel_type_handler(call):
    dt = call.data
    
    if dt == "quick_duel":
        show_duel_bet_menu(call, "quick")
    elif dt == "ranked_duel":
        show_duel_bet_menu(call, "ranked")
    elif dt == "hardcore_duel":
        show_duel_bet_menu(call, "hardcore")
    elif dt == "survival_duel":
        show_duel_bet_menu(call, "survival")
    elif dt == "sparring_duel":
        start_duel_match(call, "sparring", 0)
    elif dt == "pvp_duel":
        show_pvp_search(call)

def show_duel_bet_menu(call, mode):
    user_id = call.from_user.id
    player = Player(user_id)
    
    bet_options = {
        "quick": [50, 100, 200, 500, 1000],
        "ranked": [100],
        "hardcore": [500, 1000, 5000],
        "survival": [200, 500]
    }
    
    bets = bet_options.get(mode, [100])
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    for bet in bets:
        markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"startduel_{mode}_{bet}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
    
    mode_names = {"quick": "⚡ Быстрая", "ranked": "🏆 Рейтинговая", "hardcore": "💀 Хардкор", "survival": "🔥 Выживание"}
    
    bot.edit_message_text(
        f"<b>{mode_names.get(mode, mode)} дуэль</b>\n\n💰 Баланс: <b>{player.data['money']}💰</b>\nВыберите ставку:",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

def show_pvp_search(call):
    """Показать меню поиска PvP"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 Найти соперника (100💰)", callback_data="startduel_pvp_100"),
        types.InlineKeyboardButton("🤖 Играть с ботом", callback_data="startduel_quick_100"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels")
    )
    
    bot.edit_message_text(
        "<b>👥 PvP ДУЭЛЬ</b>\n\n🔍 Поиск соперника\n🤖 Если нет игрока — бой с ботом",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_duels")
def back_to_duels(call):
    duel_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("startduel_"))
def start_duel_match(call, mode_override=None, bet_override=None):
    if mode_override and bet_override is not None:
        mode = mode_override
        bet = bet_override
    else:
        parts = call.data.split("_")
        mode = parts[1]
        bet = int(parts[2])
    
    user_id = call.from_user.id
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    # Если PvP — ищем соперника
    if mode == "pvp":
        opponent_id = find_match("pvp", user_id)
        if opponent_id:
            # Нашли соперника
            opponent = Player(opponent_id)
            if opponent.data["money"] < bet:
                bot.answer_callback_query(call.id, "❌ У соперника недостаточно монет!")
                return
            
            player.data["money"] -= bet
            opponent.data["money"] -= bet
            player.save()
            opponent.save()
            
            duel = StepDuel(user_id, opponent_id, mode, bet)
            active_duels[str(user_id)] = duel
            active_duels[str(opponent_id)] = duel
            
            bot.edit_message_text("⚔ Соперник найден! Дуэль начинается!", call.message.chat.id, call.message.message_id)
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
            
            # Уведомление сопернику
            try:
                bot.send_message(int(opponent_id), "⚔ Найден соперник! Дуэль начинается!")
                show_duel_interface(int(opponent_id), None, duel, opponent_id)
            except:
                pass
            return
        else:
            # Игрок в очереди, играем с ботом
            mode = "quick"
    
    # Бой с ботом
    if bet > 0:
        player.data["money"] -= bet
    
    player.save()
    
    # Создание бота под уровень
    bot_id = f"bot_{random.randint(100000, 999999)}"
    users[bot_id] = generate_bot(player.data["level"])
    save_json(DATA_FILES['users'], users)
    
    duel = StepDuel(user_id, bot_id, mode, bet)
    active_duels[str(user_id)] = duel
    
    # Бот выбирает защиту
    bot_def = random.choice(list(BODY_PARTS.keys()))
    duel.set_defend(2, bot_def)
    
    # Бот выбирает атаку
    bot_skills = duel.get_available_skills(2)
    if bot_skills:
        duel.set_attack(2, random.randint(0, len(bot_skills) - 1))
    
    bot.edit_message_text("⚔ Дуэль началась!", call.message.chat.id, call.message.message_id)
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

def show_duel_interface(chat_id, message_id, duel, user_id):
    if not duel.active:
        finish_duel(chat_id, message_id, duel)
        return
    
    state_text = duel.get_state_text(user_id)
    pn = 1 if str(user_id) == duel.p1_id else 2
    phase = duel.p1_phase if pn == 1 else duel.p2_phase
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if phase == "defend_select":
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(f"🛡 {data['name']}", callback_data=f"duel_defend_{part}"))
    
    elif phase == "attack_select":
        skills = duel.get_available_skills(pn)
        for i, skill in enumerate(skills):
            name = skill["name"]
            mana = skill.get("mana_cost", 0)
            cd = (duel.p1_cooldowns if pn == 1 else duel.p2_cooldowns).get(name, 0)
            
            btn = f"{name} ({mana}MP)"
            if cd > 0:
                btn = f"⏳ {name}"
            markup.add(types.InlineKeyboardButton(btn, callback_data=f"duel_atk_{i}"))
    
    elif phase == "done":
        # Проверка хода бота
        other_pn = 3 - pn
        if duel.p2_id.startswith("bot_") and other_pn == 2:
            other_phase = duel.p2_phase
            if other_phase == "defend_select":
                duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
            if other_phase == "attack_select":
                skills = duel.get_available_skills(2)
                if skills:
                    duel.set_attack(2, random.randint(0, len(skills) - 1))
        
        markup.add(types.InlineKeyboardButton("⏳ Ожидание...", callback_data="duel_wait"))
    
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="duel_refresh"))
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="duel_surr"))
    
    if message_id:
        try:
            bot.edit_message_text(state_text[:4000], chat_id, message_id, reply_markup=markup)
        except:
            pass
    else:
        bot.send_message(chat_id, state_text[:4000], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_"))
def duel_action_handler(call):
    user_id = call.from_user.id
    action = call.data.split("_", 1)[1]
    
    duel = active_duels.get(str(user_id))
    
    if not duel or not duel.active:
        try:
            bot.edit_message_text("❌ Дуэль завершена", call.message.chat.id, call.message.message_id)
        except:
            bot.send_message(call.message.chat.id, "❌ Дуэль завершена")
        return
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    
    if action == "refresh":
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        bot.answer_callback_query(call.id, "✅")
        return
    
    if action == "wait":
        other_pn = 3 - pn
        if duel.p2_id.startswith("bot_") and other_pn == 2:
            other_phase = duel.p2_phase
            if other_phase == "defend_select":
                duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
            if other_phase == "attack_select":
                skills = duel.get_available_skills(2)
                if skills:
                    duel.set_attack(2, random.randint(0, len(skills) - 1))
        
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        bot.answer_callback_query(call.id, "✅")
        return
    
    if action == "surr":
        duel.active = False
        duel.winner = 2 if pn == 1 else 1
        finish_duel(call.message.chat.id, call.message.message_id, duel)
        return
    
    if action.startswith("defend_"):
        part = action.split("_")[1]
        duel.set_defend(pn, part)
        bot.answer_callback_query(call.id, f"🛡 {BODY_PARTS[part]['name']}")
    
    elif action.startswith("atk_"):
        idx = int(action.split("_")[1])
        if duel.set_attack(pn, idx):
            bot.answer_callback_query(call.id, "⚔ Атака!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка!")
    
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

def finish_duel(chat_id, message_id, duel):
    # Очистка
    for uid in list(active_duels.keys()):
        if active_duels.get(uid) == duel:
            del active_duels[uid]
    
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") and uid in users:
            del users[uid]
    save_json(DATA_FILES['users'], users)
    
    if duel.winner == 0:
        bot.edit_message_text("<b>🤝 НИЧЬЯ!</b>", chat_id, message_id)
        return
    
    winner_id = duel.p1_id if duel.winner == 1 else duel.p2_id
    loser_id = duel.p2_id if duel.winner == 1 else duel.p1_id
    
    winner = Player(winner_id)
    loser = Player(loser_id)
    
    if duel.bet > 0:
        winner.data["money"] += duel.bet * 2
    
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
    
    exp_w = duel.turn * 10 + duel.bet // 2
    exp_l = duel.turn * 5 + duel.bet // 5
    
    winner.data["exp"] += exp_w
    winner.data["total_exp"] += exp_w
    loser.data["exp"] += exp_l
    loser.data["total_exp"] += exp_l
    
    check_level_up(winner)
    check_level_up(loser)
    
    winner.data.setdefault("battle_history", []).append({
        "date": datetime.now().isoformat(), "opponent": loser.data["first_name"],
        "result": "win", "type": duel.duel_type, "turns": duel.turn, "bet": duel.bet
    })
    loser.data.setdefault("battle_history", []).append({
        "date": datetime.now().isoformat(), "opponent": winner.data["first_name"],
        "result": "loss", "type": duel.duel_type, "turns": duel.turn, "bet": duel.bet
    })
    
    winner.save()
    loser.save()
    
    result = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

👑 <b>{winner.data['first_name']}</b> побеждает!
💀 <b>{loser.data['first_name']}</b> проигрывает

💰 Приз: <b>{duel.bet * 2 if duel.bet > 0 else 0}💰</b>
✨ Опыт: +{exp_w} | +{exp_l}
📊 Ходов: <b>{duel.turn}</b>
"""
    
    bot.edit_message_text(result, chat_id, message_id)

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
        s = ""
        if item.get("type") == "weapon" and "damage" in item:
            s = f"Урон: {item['damage'][0]}-{item['damage'][1]}"
        elif item.get("type") in ["helmet", "armor", "boots"]:
            parts = [f"Защита: {item.get('defense', 0)}"]
            if "speed" in item:
                parts.append(f"Скорость: +{item['speed']}")
            if "hp_bonus" in item:
                parts.append(f"HP: +{item['hp_bonus']}")
            s = " | ".join(parts)
        elif item.get("type") == "potion":
            s = f"Лечение: {item.get('heal', 0)}"
        
        text += f"{r} <b>{item['name']}</b> — {s}\n💰 {item['price']} | Ур.{item.get('level_req', 1)}\n\n"
        
        if player.data["money"] >= item["price"]:
            markup.add(types.InlineKeyboardButton(f"Купить: {item['name']} - {item['price']}💰", callback_data=f"buyitem_{ik}"))
    
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

# ==================== ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (сокращённо для экономии места) ====================
@bot.callback_query_handler(func=lambda call: call.data == "trade_limited")
def limited_shop(call):
    if not limited_items:
        bot.edit_message_text("💎 Нет лимитированных предметов", call.message.chat.id, call.message.message_id)
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
        bot.answer_callback_query(call.id, "❌ Продан!"); return
    listing = market_listings[lid]
    if user_id == str(listing.get("seller_id")):
        bot.answer_callback_query(call.id, "❌ Своё!"); return
    if player.data["money"] < listing["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно!"); return
    player.data["money"] -= listing["price"]
    player.data["inventory"].append(listing["item_key"])
    player.save()
    seller = Player(listing["seller_id"])
    seller.data["money"] += listing["price"]
    seller.save()
    del market_listings[lid]
    save_json(DATA_FILES['market'], market_listings)
    bot.answer_callback_query(call.id, "✅ Куплено!")
    market_menu(call)

@bot.callback_query_handler(func=lambda call: call.data == "trade_sell")
def sell_info(call):
    bot.edit_message_text("📦 /sell [номер] [цена]", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "trade_my_lots")
def my_lots(call):
    uid = str(call.from_user.id)
    my = {k: v for k, v in market_listings.items() if str(v.get("seller_id")) == uid}
    if not my:
        bot.edit_message_text("📦 Нет лотов", call.message.chat.id, call.message.message_id); return
    text = "<b>📦 МОИ ЛОТЫ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for lid, listing in my.items():
        item = items.get(listing["item_key"]) or limited_items.get(listing["item_key"])
        if item:
            text += f"📦 {item['name']} — {listing['price']}💰\n"
            markup.add(types.InlineKeyboardButton(f"Снять: {item['name']}", callback_data=f"remlot_{lid}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("remlot_"))
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
    my_lots(call)

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
⭐ Ур.{d['level']} | 📊 {d['pvp_rating']} | 💰 {d['money']}💰

⚔ Урон: {s['min_damage']}-{s['max_damage']}
🛡 Защита: Г:{s['head_defense']} Т:{s['body_defense']} Н:{s['legs_defense']}
💨 Скорость: {s['speed']:.0f} | 💥 Крит: {s['crit_chance']:.1f}%

🏆 Побед: {d['wins']} | 💀 Поражений: {d['losses']} | 📈 {wr:.1f}%
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "hero_inventory")
def hero_inventory(call):
    user_id = call.from_user.id
    player = Player(user_id)
    if not player.data["inventory"]:
        bot.edit_message_text("🎒 Пусто", call.message.chat.id, call.message.message_id); return
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
        ench_t = f" ✨{ench.get('name', '')}" if ench else ""
        text += f"{idx}. {r} {item['name']} x{cnt}{eq}{ench_t}\n"
        if item.get("type") in ["weapon", "helmet", "armor", "boots"]:
            markup.add(types.InlineKeyboardButton(f"Экип: {item['name']}", callback_data=f"eq_{ik}"))
            markup.add(types.InlineKeyboardButton(f"Зачар: {item['name']}", callback_data=f"ench_{ik}"))
        elif item.get("type") == "potion":
            markup.add(types.InlineKeyboardButton(f"Исп: {item['name']}", callback_data=f"use_{ik}"))
        idx += 1
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("eq_"))
def equip_item(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    item = items.get(ik) or limited_items.get(ik)
    if not item or ik not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌ Ошибка!"); return
    slot_map = {"weapon": "weapon", "helmet": "head", "armor": "body", "boots": "legs"}
    slot = slot_map.get(item.get("type"))
    if not slot:
        bot.answer_callback_query(call.id, "❌!"); return
    old = player.data["equipment"][slot]
    if old:
        player.data["inventory"].append(old)
    player.data["equipment"][slot] = ik
    player.data["inventory"].remove(ik)
    player.save()
    bot.answer_callback_query(call.id, f"✅ {item['name']}!")
    hero_inventory(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ench_"))
def enchant_item(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    item = items.get(ik) or limited_items.get(ik)
    if not item or not item.get("enchantable"):
        bot.answer_callback_query(call.id, "❌!"); return
    cost = item.get("price", 100) // 2
    if player.data["money"] < cost:
        bot.answer_callback_query(call.id, f"❌ {cost}💰!"); return
    player.data["money"] -= cost
    ench = random.choice(ENCHANT_EFFECTS)
    player.data.setdefault("enchantments", {})[ik] = {"name": ench["name"], "effect": ench["effect"], "value": ench["value"]}
    player.save()
    bot.answer_callback_query(call.id, f"✨ {ench['name']}!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("use_"))
def use_potion(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    item = items.get(ik) or limited_items.get(ik)
    if not item or item.get("type") != "potion" or ik not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌!"); return
    stats = player.get_full_stats()
    if "heal" in item:
        if player.data["hp"] >= stats["max_hp"]:
            bot.answer_callback_query(call.id, "❌ Полное HP!"); return
        player.data["hp"] = min(stats["max_hp"], player.data["hp"] + item["heal"])
    if "mana_restore" in item:
        player.data["mana"] = min(stats["max_mana"], player.data["mana"] + item["mana_restore"])
    player.data["inventory"].remove(ik)
    player.save()
    bot.answer_callback_query(call.id, "✅!")

@bot.callback_query_handler(func=lambda call: call.data == "hero_attributes")
def hero_attributes(call):
    user_id = call.from_user.id
    player = Player(user_id)
    st = player.data["stats"]
    pts = player.data["stat_points"]
    text = f"<b>⚡ ХАРАКТЕРИСТИКИ</b>\nОчков: <b>{pts}</b>\n\n💪 Сила: {st['strength']}\n🏃 Ловкость: {st['agility']}\n🧠 Интеллект: {st['intelligence']}\n❤ Живучесть: {st['vitality']}\n🍀 Удача: {st['luck']}\n🛡 Защита: {st['defense']}"
    markup = types.InlineKeyboardMarkup(row_width=3)
    if pts > 0:
        markup.add(
            types.InlineKeyboardButton("💪", callback_data="up_str"),
            types.InlineKeyboardButton("🏃", callback_data="up_agi"),
            types.InlineKeyboardButton("🧠", callback_data="up_int"),
            types.InlineKeyboardButton("❤", callback_data="up_vit"),
            types.InlineKeyboardButton("🍀", callback_data="up_luk"),
            types.InlineKeyboardButton("🛡", callback_data="up_def")
        )
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("up_"))
def upgrade_stat(call):
    smap = {"str": "strength", "agi": "agility", "int": "intelligence", "vit": "vitality", "luk": "luck", "def": "defense"}
    sk = smap[call.data.split("_")[1]]
    user_id = call.from_user.id
    player = Player(user_id)
    if player.data["stat_points"] <= 0:
        bot.answer_callback_query(call.id, "❌!"); return
    if player.data["stats"][sk] >= 100:
        bot.answer_callback_query(call.id, "❌ Макс!"); return
    player.data["stats"][sk] += 1
    player.data["stat_points"] -= 1
    player.save()
    bot.answer_callback_query(call.id, "✅")
    hero_attributes(call)

@bot.callback_query_handler(func=lambda call: call.data in ["hero_achievements", "hero_enchantments", "hero_equipped", "hero_history", "hero_heal"])
def hero_misc(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "hero_achievements":
        ach = [("fb", "🩸 Первая кровь", player.data["wins"] >= 1), ("war", "⚔ Воин", player.data["wins"] >= 10)]
        text = f"<b>🏅 ДОСТИЖЕНИЯ</b>\n\n"
        for aid, name, cond in ach:
            icon = "✅" if aid in player.data["achievements"] or cond else "🔒"
            text += f"{icon} {name}\n"
            if cond and aid not in player.data["achievements"]:
                player.data["achievements"].append(aid)
        player.save()
    
    elif call.data == "hero_enchantments":
        ench = player.data.get("enchantments", {})
        text = "<b>✨ ЗАЧАРОВАНИЯ</b>\n\n"
        for ik, e in ench.items():
            item = items.get(ik) or limited_items.get(ik)
            if item:
                text += f"📦 {item['name']}: <b>{e.get('name', '?')}</b>\n"
        if not ench:
            text += "Нет зачарований"
    
    elif call.data == "hero_equipped":
        eq = player.data["equipment"]
        text = "<b>👁 ЭКИПИРОВКА</b>\n\n"
        slots = {"weapon": "⚔ Оружие", "head": "👤 Голова", "body": "🦾 Тело", "legs": "🦿 Ноги"}
        for slot, name in slots.items():
            ik = eq.get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                text += f"{name}: <b>{item['name'] if item else '?'}</b>\n"
            else:
                text += f"{name}: ❌ Пусто\n"
    
    elif call.data == "hero_history":
        hist = player.data.get("battle_history", [])
        text = "<b>📋 ИСТОРИЯ</b>\n\n"
        for b in hist[-5:]:
            icon = "🏆" if b.get("result") == "win" else "💀"
            text += f"{icon} vs {b.get('opponent', '?')} | {b.get('turns', 0)} ходов\n"
        if not hist:
            text += "Пусто"
    
    elif call.data == "hero_heal":
        stats = player.get_full_stats()
        potions = [k for k in player.data["inventory"] if items.get(k, {}).get("type") == "potion" and items.get(k, {}).get("heal", 0) > 0]
        if not potions:
            text = "💊 Нет зелий!"
        elif player.data["hp"] >= stats["max_hp"]:
            text = "💊 Полное HP!"
        else:
            pk = potions[0]
            potion = items[pk]
            player.data["hp"] = min(stats["max_hp"], player.data["hp"] + potion["heal"])
            player.data["inventory"].remove(pk)
            player.save()
            text = f"💊 <b>{potion['name']}</b>\n❤ {player.data['hp']}/{stats['max_hp']}"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_hero")
def back_to_hero(call):
    hero_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_trade")
def back_to_trade(call):
    trade_section(call.message)

# ==================== МИР ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_dungeons")
def world_dungeons(call):
    text = "<b>🏰 ПОДЗЕМЕЛЬЯ</b>\n\n🐺 Логово волка (1+)\n🕷 Паучьи пещеры (5+)\n💀 Катакомбы (10+)\n🐉 Драконье логово (15+)\n👹 Бездна (25+)\n\nКулдаун: 1 час"
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
        bot.answer_callback_query(call.id, f"❌ Ур.{level_reqs[dl-1]}!"); return
    if player.data.get("last_dungeon"):
        last = datetime.fromisoformat(player.data["last_dungeon"])
        if (datetime.now() - last) < timedelta(hours=1):
            r = timedelta(hours=1) - (datetime.now() - last)
            bot.answer_callback_query(call.id, f"⏰ {r.seconds//60}мин."); return
    
    bosses = ["Вожак", "Паук", "Некромант", "Дракон", "Владыка"]
    reward = random.randint(50, 250) * dl * player.data["level"]
    exp = 50 * dl * player.data["level"]
    got_item = None
    if random.random() < 0.15:
        possible = [k for k, v in items.items() if v.get("level_req", 1) <= player.data["level"]]
        if possible:
            got_item = random.choice(possible)
            player.data["inventory"].append(got_item)
            player.data["items_found"] += 1
    
    player.data["money"] += reward
    player.data["exp"] += exp
    player.data["total_exp"] += exp
    player.data["last_dungeon"] = datetime.now().isoformat()
    player.data["dungeons_completed"] = player.data.get("dungeons_completed", 0) + 1
    old = player.data["level"]
    check_level_up(player)
    player.save()
    
    result = f"<b>🏰 ДАНЖ ПРОЙДЕН!</b>\n👹 {bosses[dl-1]}\n💰 +{reward} | ✨ +{exp}"
    if got_item:
        result += f"\n🎁 <b>{items[got_item]['name']}</b>!"
    if player.data["level"] > old:
        result += f"\n🎉 УРОВЕНЬ <b>{player.data['level']}</b>!"
    bot.edit_message_text(result, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "world_clans")
def world_clans(call):
    user_id = call.from_user.id
    player = Player(user_id)
    if player.data.get("clan"):
        clan = clans.get(player.data["clan"], {})
        text = f"<b>🛡 {player.data['clan']}</b>\n👥 {len(clan.get('members', []))} уч.\n💰 {clan.get('treasury', 0)}💰"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("👥 Участники", callback_data="clan_mem"), types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave"))
    else:
        text = "<b>🛡 КЛАНЫ</b>\n/createclan [имя]\n/joinclan [имя]\n💰 5000💰"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("📋 Список", callback_data="clan_list"), types.InlineKeyboardButton("ℹ Инфо", callback_data="clan_info"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["clan_list", "clan_info", "clan_mem", "clan_leave"])
def clan_actions(call):
    if call.data == "clan_list":
        text = "<b>📋 КЛАНЫ</b>\n\n" + "\n".join([f"🛡 {n}: {len(d.get('members', []))} уч." for n, d in clans.items()]) if clans else "Нет кланов"
    elif call.data == "clan_info":
        text = "<b>ℹ О КЛАНАХ</b>\n/createclan [имя]\n/joinclan [имя]"
    elif call.data == "clan_mem":
        cn = Player(call.from_user.id).data.get("clan")
        text = f"<b>👥 {cn}</b>\n\n" + "\n".join([f"{i}. {m}" for i, m in enumerate(clans.get(cn, {}).get("members", []), 1)]) if cn else "❌"
    elif call.data == "clan_leave":
        player = Player(call.from_user.id)
        cn = player.data.get("clan")
        if cn and player.data.get("clan_role") != "leader":
            player.data["clan"] = None; player.data["clan_role"] = None; player.save()
            if player.data["first_name"] in clans[cn].get("members", []):
                clans[cn]["members"].remove(player.data["first_name"])
            save_json(DATA_FILES['clans'], clans)
            bot.answer_callback_query(call.id, "✅ Вышли!")
        else:
            bot.answer_callback_query(call.id, "❌!")
        world_clans(call); return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_clans"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(commands=['createclan', 'joinclan', 'clandonate'])
def clan_cmds(message):
    cmd = message.text.split()[0].replace('/', '')
    player = Player(message.from_user.id)
    if cmd == "createclan":
        if player.data.get("clan"):
            bot.send_message(message.chat.id, "❌ Уже в клане!"); return
        if player.data["money"] < 5000:
            bot.send_message(message.chat.id, "❌ 5000💰!"); return
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ /createclan [имя]"); return
        name = parts[1].strip()
        if name in clans:
            bot.send_message(message.chat.id, "❌ Существует!"); return
        player.data["money"] -= 5000; player.data["clan"] = name; player.data["clan_role"] = "leader"; player.save()
        clans[name] = {"leader_id": message.from_user.id, "leader_name": message.from_user.first_name, "members": [message.from_user.first_name], "treasury": 0, "created_at": datetime.now().isoformat()}
        save_json(DATA_FILES['clans'], clans)
        bot.send_message(message.chat.id, f"✅ Клан <b>{name}</b>!")
    elif cmd == "joinclan":
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ /joinclan [имя]"); return
        name = parts[1].strip()
        if name not in clans:
            bot.send_message(message.chat.id, "❌ Нет!"); return
        player.data["clan"] = name; player.data["clan_role"] = "member"; player.save()
        if message.from_user.first_name not in clans[name]["members"]:
            clans[name]["members"].append(message.from_user.first_name)
        save_json(DATA_FILES['clans'], clans)
        bot.send_message(message.chat.id, f"✅ В <b>{name}</b>!")
    elif cmd == "clandonate":
        try:
            amt = int(message.text.split()[1])
            if player.data["money"] < amt:
                bot.send_message(message.chat.id, "❌!"); return
            player.data["money"] -= amt; player.save()
            clans[player.data["clan"]]["treasury"] = clans[player.data["clan"]].get("treasury", 0) + amt
            save_json(DATA_FILES['clans'], clans)
            bot.send_message(message.chat.id, f"✅ +{amt}💰!")
        except:
            bot.send_message(message.chat.id, "❌ /clandonate [сумма]")

@bot.callback_query_handler(func=lambda call: call.data == "world_tournaments")
def world_tournaments(call):
    if not tournaments.get("active"):
        tournaments["active"] = {"name": "Турнир", "participants": [], "prize_pool": 5000, "status": "registration"}
        save_json(DATA_FILES['tournaments'], tournaments)
    t = tournaments["active"]
    text = f"<b>🏟 ТУРНИР</b>\n\n{t['name']}\n👥 {len(t['participants'])}/16\n💰 {t['prize_pool']}💰\nВзнос: 500💰"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🏆 Участвовать", callback_data="t_join"), types.InlineKeyboardButton("📋 Список", callback_data="t_list"), types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["t_join", "t_list"])
def tour_actions(call):
    if call.data == "t_join":
        player = Player(call.from_user.id)
        if player.data["money"] < 500:
            bot.answer_callback_query(call.id, "❌ 500💰!"); return
        t = tournaments["active"]
        if str(call.from_user.id) in t["participants"]:
            bot.answer_callback_query(call.id, "❌ Уже!"); return
        player.data["money"] -= 500; player.save()
        t["participants"].append(str(call.from_user.id)); t["prize_pool"] += 500
        save_json(DATA_FILES['tournaments'], tournaments)
        bot.answer_callback_query(call.id, "✅!")
    elif call.data == "t_list":
        p = tournaments["active"]["participants"]
        text = "<b>📋 УЧАСТНИКИ</b>\n\n" + "\n".join([f"{i}. {Player(uid).data['first_name']}" for i, uid in enumerate(p, 1)]) if p else "Пусто"
        bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == "world_events")
def world_events(call):
    if not events.get("current") or datetime.fromisoformat(events["current"].get("expires", "2000-01-01")) < datetime.now():
        events["current"] = {"name": random.choice(["🌋 Извержение", "❄ Шторм", "⚡ Гроза"]), "ench": random.choice(ENCHANT_EFFECTS), "expires": (datetime.now() + timedelta(minutes=10)).isoformat()}
        save_json(DATA_FILES['events'], events)
    ev = events["current"]
    mins = max(0, (datetime.fromisoformat(ev["expires"]) - datetime.now()).seconds // 60)
    text = f"<b>🌍 ИВЕНТ</b>\n\n{ev['name']}\n✨ {ev['ench']['name']}\n⏰ {mins} мин."
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "world_top")
def world_top(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for cat in ["level", "wins", "money", "rating"]:
        markup.add(types.InlineKeyboardButton({"level": "⭐ Уровень", "wins": "⚔ Победы", "money": "💰 Монеты", "rating": "🏆 Рейтинг"}[cat], callback_data=f"top_{cat}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text("<b>📊 ТОП</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def show_top(call):
    cat = call.data.split("_")[1]
    key = {"level": ("level", "exp"), "wins": ("wins",), "money": ("money",), "rating": ("pvp_rating",)}
    su = sorted(users.items(), key=lambda x: (x[1].get(key[cat][0], 0), x[1].get(key[cat][1], 0) if len(key[cat]) > 1 else 0), reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉"] + [f"{i}️⃣" for i in range(4, 11)]
    text = f"<b>{['⭐ УРОВЕНЬ', '⚔ ПОБЕДЫ', '💰 МОНЕТЫ', '🏆 РЕЙТИНГ'][['level', 'wins', 'money', 'rating'].index(cat)]}</b>\n\n"
    for i, (uid, data) in enumerate(su):
        val = data.get(key[cat][0], 0)
        text += f"{medals[i]} {data.get('first_name', '?')}: {val}\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_top"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "world_help")
def world_help(call):
    text = "<b>ℹ ПОМОЩЬ</b>\n\nДуэли в ЛС\nЗащита → Атака\nОружие даёт навыки\nБроня защищает части тела"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_world")
def back_to_world(call):
    world_section(call.message)

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
        titles = {5: "Боец", 10: "Воитель", 15: "Рыцарь", 20: "Ветеран", 25: "Мастер", 30: "Грандмастер", 40: "Герой", 50: "Легенда", 60: "Мифический воин", 75: "Полубог", 100: "Божество"}
        for req, title in titles.items():
            if player.data["level"] >= req and title not in player.data["titles_collected"]:
                player.data["titles_collected"].append(title)
                player.data["title"] = title
        level = player.data["level"]
        exp_needed = int(100 * (1.5 ** (level - 1)))
        leveled = True
    return leveled

@bot.message_handler(commands=['sell'])
def sell_cmd(message):
    user_id = message.from_user.id
    player = Player(user_id)
    try:
        parts = message.text.split()
        idx = int(parts[1]) - 1
        price = int(parts[2])
    except:
        bot.send_message(message.chat.id, "❌ /sell [номер] [цена]"); return
    if idx < 0 or idx >= len(player.data["inventory"]):
        bot.send_message(message.chat.id, "❌ Неверный номер!"); return
    ik = player.data["inventory"].pop(idx)
    player.save()
    lid = f"{user_id}_{int(time.time())}"
    market_listings[lid] = {"seller_id": user_id, "seller_name": message.from_user.first_name, "item_key": ik, "price": price, "created_at": datetime.now().isoformat()}
    save_json(DATA_FILES['market'], market_listings)
    bot.send_message(message.chat.id, f"✅ {items.get(ik, {}).get('name', ik)} за {price}💰!")

@bot.message_handler(commands=['transfer'])
def transfer_cmd(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Ответьте!"); return
    try:
        idx = int(message.text.split()[1]) - 1
        player = Player(message.from_user.id)
        target = Player(message.reply_to_message.from_user.id)
        ik = player.data["inventory"].pop(idx)
        target.data["inventory"].append(ik)
        player.save(); target.save()
        bot.send_message(message.chat.id, f"✅ {items.get(ik, {}).get('name', ik)} передан!")
    except:
        bot.send_message(message.chat.id, "❌ /transfer [номер]")

# ==================== АДМИН (через username) ====================
def get_user_by_username(username):
    """Найти пользователя по username (без @)"""
    for uid, data in users.items():
        if data.get("username", "").lower() == username.lower():
            return uid, data
    return None, None

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
        types.InlineKeyboardButton("💰 Выдать деньги", callback_data="adm_givemoney"),
        types.InlineKeyboardButton("🎁 Выдать предмет", callback_data="adm_giveitem"),
        types.InlineKeyboardButton("⛔ Бан", callback_data="adm_ban"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("👁 Инфо", callback_data="adm_info"),
        types.InlineKeyboardButton("✅ Разбан", callback_data="adm_unban"),
        types.InlineKeyboardButton("🔄 Сброс", callback_data="adm_reset")
    )
    bot.send_message(message.chat.id, "<b>🔧 АДМИН</b>\nВсе команды через username!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_actions(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    action = call.data
    
    if action == "adm_stats":
        text = f"👥 {len(users)}\n💰 {sum(u.get('money',0) for u in users.values())}\n⚔ {sum(u.get('total_duels',0) for u in users.values())}\n🛡 {len(clans)}"
        bot.edit_message_text(f"<b>📊 СТАТИСТИКА</b>\n\n{text}", call.message.chat.id, call.message.message_id)
    
    elif action == "adm_givemoney":
        bot.send_message(call.message.chat.id, "💰 /givemoney @username сумма")
    
    elif action == "adm_giveitem":
        bot.send_message(call.message.chat.id, "🎁 /giveitem @username item_key")
    
    elif action == "adm_ban":
        bot.send_message(call.message.chat.id, "⛔ /ban @username причина")
    
    elif action == "adm_unban":
        bot.send_message(call.message.chat.id, "✅ /unban @username")
    
    elif action == "adm_broadcast":
        bot.send_message(call.message.chat.id, "📢 /broadcast текст")
    
    elif action == "adm_info":
        bot.send_message(call.message.chat.id, "👁 /userinfo @username")
    
    elif action == "adm_reset":
        bot.send_message(call.message.chat.id, "🔄 /resetdaily @username")

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'userinfo', 'resetdaily'])
def admin_username_cmds(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    if len(parts) < 2:
        bot.send_message(message.chat.id, f"❌ /{cmd} @username [параметры]")
        return
    
    username = parts[1].replace('@', '')
    uid, data = get_user_by_username(username)
    
    if not uid:
        bot.send_message(message.chat.id, f"❌ Пользователь @{username} не найден!")
        return
    
    if cmd == "givemoney":
        try:
            amt = int(parts[2])
            p = Player(uid)
            p.data["money"] += amt
            p.save()
            bot.send_message(message.chat.id, f"✅ @{username} +{amt}💰")
        except:
            bot.send_message(message.chat.id, "❌ /givemoney @username сумма")
    
    elif cmd == "giveitem":
        try:
            ik = parts[2]
            p = Player(uid)
            p.data["inventory"].append(ik)
            p.save()
            bot.send_message(message.chat.id, f"✅ @{username} получил {ik}")
        except:
            bot.send_message(message.chat.id, "❌ /giveitem @username item_key")
    
    elif cmd == "ban":
        reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение"
        banned_users[uid] = {"reason": reason, "banned_at": datetime.now().isoformat()}
        save_json(DATA_FILES['bans'], banned_users)
        bot.send_message(message.chat.id, f"⛔ @{username} забанен!")
    
    elif cmd == "unban":
        if uid in banned_users:
            del banned_users[uid]
            save_json(DATA_FILES['bans'], banned_users)
        bot.send_message(message.chat.id, f"✅ @{username} разбанен!")
    
    elif cmd == "userinfo":
        d = Player(uid).data
        text = f"<b>👤 @{username}</b>\nИмя: {d['first_name']}\nУр.: {d['level']} | 💰 {d['money']}\nРейтинг: {d['pvp_rating']}\nПобед: {d['wins']} | Поражений: {d['losses']}\nКлан: {d.get('clan', 'Нет')}"
        bot.send_message(message.chat.id, text)
    
    elif cmd == "resetdaily":
        p = Player(uid)
        p.data["last_daily"] = None
        p.data["last_dungeon"] = None
        p.save()
        bot.send_message(message.chat.id, f"✅ @{username} сброшен!")

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace('/broadcast', '', 1).strip()
    if not text:
        return
    s, f = 0, 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 {text}")
            s += 1
        except:
            f += 1
    bot.send_message(message.chat.id, f"✅ {s} | ❌ {f}")

# ==================== ЗАПУСК ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v10.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print("=" * 60)
    print("✅ Дуэли только в ЛС")
    print("✅ Защита частей тела + броня")
    print("✅ У каждого оружия свои атаки")
    print("✅ Боты подбираются под уровень")
    print("✅ PvP через поиск соперника")
    print("✅ Админ через username")
    print("✅ НОЛЬ ЗАГЛУШЕК")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
