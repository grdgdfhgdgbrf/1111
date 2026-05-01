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
TOKEN = '8670879387:AAEKtP7bRZrCOR7vwuh05EFbWuTDSILcnAE'
ADMIN_ID = 5356400377
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ==================== КОНСТАНТЫ ====================
BODY_PARTS = {
    "head": {"name": "👤 Голова", "multiplier": 1.5},
    "body": {"name": "🦾 Тело", "multiplier": 1.0},
    "legs": {"name": "🦿 Ноги", "multiplier": 0.7}
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
    {"name": "🔥 Огненное", "effect": "fire_damage", "value": 15},
    {"name": "❄ Ледяное", "effect": "freeze_chance", "value": 20},
    {"name": "⚡ Грозовое", "effect": "stun_chance", "value": 15},
    {"name": "💀 Вампирическое", "effect": "life_steal", "value": 12},
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
    'matchmaking': 'matchmaking.json',
    'tournament_brackets': 'tournament_brackets.json'
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
    "leather_cap": {"name": "🎓 Кожаная шапка", "defense": 3, "price": 60, "type": "helmet", "slot": "head", "rarity": "common", "level_req": 1, "enchantable": True},
    "iron_helmet": {"name": "⛑ Железный шлем", "defense": 8, "price": 250, "type": "helmet", "slot": "head", "rarity": "uncommon", "level_req": 6, "enchantable": True},
    "dragon_helmet": {"name": "🐉 Шлем дракона", "defense": 18, "price": 2000, "type": "helmet", "slot": "head", "rarity": "epic", "level_req": 20, "enchantable": True, "element": "fire"},
    "crown_of_wisdom": {"name": "👑 Корона мудрости", "defense": 12, "price": 3500, "type": "helmet", "slot": "head", "rarity": "legendary", "level_req": 28, "enchantable": True}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "defense": 5, "price": 80, "type": "armor", "slot": "body", "rarity": "common", "level_req": 1, "enchantable": True},
    "chainmail": {"name": "⛓ Кольчуга", "defense": 12, "price": 400, "type": "armor", "slot": "body", "rarity": "uncommon", "level_req": 8, "enchantable": True},
    "plate_armor": {"name": "🛡 Латный доспех", "defense": 22, "price": 1500, "type": "armor", "slot": "body", "rarity": "rare", "level_req": 15, "enchantable": True},
    "shadow_armor": {"name": "🌑 Теневая броня", "defense": 28, "price": 3500, "type": "armor", "slot": "body", "rarity": "epic", "level_req": 22, "enchantable": True, "element": "dark"},
    "phoenix_armor": {"name": "🦅 Броня феникса", "defense": 40, "price": 8000, "type": "armor", "slot": "body", "rarity": "legendary", "level_req": 30, "enchantable": True, "element": "fire"}
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
    "immortal_helmet": {"name": "✨ Шлем бессмертия", "defense": 80, "total": 2, "remaining": 2, "price": 75000, "type": "helmet", "slot": "head", "rarity": "divine", "enchantable": True}
}

ALL_ITEMS = {}
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(BOOTS)
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(POTIONS)

# ==================== БАЗА НАВЫКОВ ====================
SKILLS_DB = {
    "quick_strike": {"name": "⚡ Быстрый удар", "damage_mult": 0.8, "cooldown": 0, "tier": 1},
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.2, "cooldown": 0, "tier": 1},
    "power_shot": {"name": "🎯 Мощный выстрел", "damage_mult": 1.8, "cooldown": 1, "tier": 2},
    "multi_shot": {"name": "🏹 Залп", "damage_mult": 0.6, "hits": 3, "cooldown": 2, "tier": 2},
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.5, "element": "fire", "burn_chance": 30, "cooldown": 1, "tier": 2},
    "inferno_strike": {"name": "🌋 Инферно удар", "damage_mult": 2.2, "element": "fire", "burn_chance": 60, "cooldown": 3, "tier": 3},
    "flame_wave": {"name": "🔥 Волна пламени", "damage_mult": 2.5, "element": "fire", "aoe": True, "cooldown": 4, "tier": 4},
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.4, "element": "ice", "freeze_chance": 25, "cooldown": 1, "tier": 2},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.0, "element": "ice", "freeze_chance": 50, "cooldown": 3, "tier": 3},
    "blizzard": {"name": "🌨 Метель", "damage_mult": 2.4, "element": "ice", "aoe": True, "cooldown": 4, "tier": 4},
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.6, "element": "lightning", "stun_chance": 20, "cooldown": 1, "tier": 2},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.3, "element": "lightning", "stun_chance": 35, "aoe": True, "cooldown": 3, "tier": 3},
    "chain_lightning": {"name": "⚡ Цепная молния", "damage_mult": 1.8, "element": "lightning", "chain_hits": 3, "cooldown": 2, "tier": 3},
    "water_slash": {"name": "🌊 Водяной разрез", "damage_mult": 1.3, "element": "water", "cooldown": 1, "tier": 2},
    "tsunami": {"name": "🌊 Цунами", "damage_mult": 2.1, "element": "water", "aoe": True, "cooldown": 3, "tier": 3},
    "drown": {"name": "💧 Утопление", "damage_mult": 1.9, "element": "water", "cooldown": 2, "tier": 3},
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.6, "element": "dark", "poison_chance": 25, "cooldown": 1, "tier": 2},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.2, "element": "dark", "ignore_defense": 50, "cooldown": 5, "tier": 4},
    "soul_drain": {"name": "💀 Похищение души", "damage_mult": 2.0, "element": "dark", "life_steal": 0.4, "cooldown": 3, "tier": 3},
    "dark_veil": {"name": "🌑 Завеса тьмы", "defense_boost": 30, "element": "dark", "cooldown": 2, "tier": 2},
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.5, "element": "light", "cooldown": 1, "tier": 2},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 2.8, "element": "light", "cooldown": 4, "tier": 4},
    "heavenly_light": {"name": "🌟 Небесный свет", "hp_restore": 60, "element": "light", "cooldown": 2, "tier": 2},
    "reap": {"name": "💀 Жатва", "damage_mult": 2.5, "element": "dark", "life_steal": 0.3, "cooldown": 3, "tier": 3},
    "death_sentence": {"name": "☠ Смертный приговор", "damage_mult": 4.0, "element": "dark", "cooldown": 6, "tier": 4},
    "soul_harvest": {"name": "👻 Сбор душ", "damage_mult": 2.8, "element": "dark", "life_steal": 0.5, "cooldown": 4, "tier": 4},
    "thunder_gods_wrath": {"name": "⚡ Гнев бога грома", "damage_mult": 4.5, "element": "lightning", "stun_chance": 50, "aoe": True, "cooldown": 6, "tier": 4},
    "eye_of_the_storm": {"name": "🌀 Глаз бури", "damage_mult": 3.0, "element": "lightning", "cooldown": 4, "tier": 3},
    "lightning_apocalypse": {"name": "⚡ Молниевый апокалипсис", "damage_mult": 5.0, "element": "lightning", "aoe": True, "cooldown": 7, "tier": 4}
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
tournament_brackets = load_json(DATA_FILES['tournament_brackets'], {})

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
                "base_damage": 10,
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
    
    def get_equipment_defense(self, slot):
        """Получить защиту от экипировки в слоте"""
        ik = self.data["equipment"].get(slot)
        if not ik:
            return 0
        item = items.get(ik) or limited_items.get(ik)
        if not item:
            return 0
        
        defense = item.get("defense", 0)
        
        # Зачарования
        ench = self.data.get("enchantments", {}).get(ik, {})
        if ench and ench.get("effect") == "defense_bonus":
            defense += ench.get("value", 0)
        
        return defense
    
    def get_weapon_damage(self):
        """Получить урон от оружия"""
        ik = self.data["equipment"].get("weapon")
        if not ik:
            return (5, 10)  # Базовый урон
        
        item = items.get(ik) or limited_items.get(ik)
        if not item or "damage" not in item:
            return (5, 10)
        
        min_d, max_d = item["damage"]
        
        # Зачарования
        ench = self.data.get("enchantments", {}).get(ik, {})
        if ench:
            if ench.get("effect") == "damage_boost":
                boost = ench.get("value", 0) / 100
                min_d = int(min_d * (1 + boost))
                max_d = int(max_d * (1 + boost))
            elif ench.get("effect") == "fire_damage":
                min_d += ench.get("value", 0)
                max_d += ench.get("value", 0)
        
        return (min_d, max_d)
    
    def get_weapon_skills(self):
        """Получить навыки оружия"""
        ik = self.data["equipment"].get("weapon")
        if not ik:
            return ["quick_strike", "slash"]
        
        item = items.get(ik) or limited_items.get(ik)
        if item and "skills" in item:
            return item["skills"]
        
        return ["quick_strike", "slash"]
    
    def get_total_defense(self):
        """Общая защита"""
        total = 0
        for slot in ["head", "body", "legs"]:
            total += self.get_equipment_defense(slot)
        return total

# ==================== ПОШАГОВАЯ ДУЭЛЬ ====================
class DuelInstance:
    def __init__(self, p1_id, p2_id, duel_type="quick", bet=0, is_tournament=False):
        self.battle_id = str(uuid.uuid4())[:8]
        self.p1_id = str(p1_id)
        self.p2_id = str(p2_id)
        self.duel_type = duel_type
        self.bet = bet
        self.is_tournament = is_tournament
        self.turn = 1
        self.max_turns = 30
        self.active = True
        self.winner = None
        self.log_p1 = []
        self.log_p2 = []
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        # HP зависит от уровня и экипировки
        self.p1_max_hp = 100 + self.p1.data["level"] * 5
        self.p2_max_hp = 100 + self.p2.data["level"] * 5
        
        # Добавляем HP от брони
        for slot in ["head", "body", "legs"]:
            ik = self.p1.data["equipment"].get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                if item:
                    self.p1_max_hp += item.get("hp_bonus", 0)
            
            ik = self.p2.data["equipment"].get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                if item:
                    self.p2_max_hp += item.get("hp_bonus", 0)
        
        self.p1_hp = self.p1_max_hp
        self.p2_hp = self.p2_max_hp
        
        # MP
        self.p1_mp = 50 + self.p1.data["level"] * 3
        self.p2_mp = 50 + self.p2.data["level"] * 3
        self.p1_max_mp = self.p1_mp
        self.p2_max_mp = self.p2_mp
        
        # Фазы: defend -> attack
        self.p1_phase = "defend"
        self.p2_phase = "defend"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        
        # Очерёдность
        self.p1_speed = 10 + random.randint(1, 10)
        self.p2_speed = 10 + random.randint(1, 10)
        
        # Бонус скорости от обуви
        p1_boots = self.p1.data["equipment"].get("legs")
        if p1_boots:
            item = items.get(p1_boots)
            if item:
                self.p1_speed += item.get("speed", 0)
        
        p2_boots = self.p2.data["equipment"].get("legs")
        if p2_boots:
            item = items.get(p2_boots)
            if item:
                self.p2_speed += item.get("speed", 0)
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Эффекты
        self.p1_effects = []
        self.p2_effects = []
        
        # Арена
        arenas = ["Колизей", "Лес", "Вулкан", "Тундра", "Храм"]
        self.arena = random.choice(arenas)
        
        self.log_p1.append(f"⚔ Битва началась на арене: {self.arena}")
        self.log_p2.append(f"⚔ Битва началась на арене: {self.arena}")
    
    def get_player_name(self, num):
        return self.p1.data["first_name"] if num == 1 else self.p2.data["first_name"]
    
    def get_available_skills(self, player_num):
        """Доступные навыки: базовая атака + навыки оружия"""
        player = self.p1 if player_num == 1 else self.p2
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        
        available = []
        
        # Базовая атака всегда доступна
        if "basic_attack" not in cooldowns or cooldowns["basic_attack"] <= 0:
            available.append("basic_attack")
        
        # Навыки оружия
        weapon_skills = player.get_weapon_skills()
        for sid in weapon_skills:
            if sid in SKILLS_DB:
                cd = cooldowns.get(sid, 0)
                if cd <= 0:
                    available.append(sid)
        
        return available
    
    def set_defend(self, player_num, part):
        if player_num == 1:
            self.p1_defend = part
            self.p1_phase = "attack"
            self.log_p1.append(f"🛡 Вы защищаете {BODY_PARTS[part]['name']}")
        else:
            self.p2_defend = part
            self.p2_phase = "attack"
            self.log_p2.append(f"🛡 Вы защищаете {BODY_PARTS[part]['name']}")
    
    def execute_attack(self, player_num, skill_id, target_part):
        if player_num == 1:
            self.p1_skill = skill_id
            self.p1_target = target_part
            self.p1_phase = "waiting"
        else:
            self.p2_skill = skill_id
            self.p2_target = target_part
            self.p2_phase = "waiting"
        
        # Проверяем, готовы ли оба к атаке
        if self.p1_phase == "waiting" and self.p2_phase == "waiting":
            self._resolve_round()
    
    def _resolve_round(self):
        """Разрешение раунда: оба атакуют"""
        # Обработка эффектов
        self._process_effects(1)
        self._process_effects(2)
        
        # Определение очерёдности атаки
        if self.p1_speed >= self.p2_speed:
            first, second = 1, 2
        else:
            first, second = 2, 1
        
        # Первая атака
        self._perform_attack(first, second)
        if self._check_end():
            return
        
        # Вторая атака
        self._perform_attack(second, first)
        self._check_end()
        
        # Сброс фаз для нового раунда
        self.p1_phase = "defend"
        self.p2_phase = "defend"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        
        # Уменьшение кулдаунов
        self._reduce_cooldowns(1)
        self._reduce_cooldowns(2)
        
        # Восстановление маны
        self.p1_mp = min(self.p1_max_mp, self.p1_mp + 5)
        self.p2_mp = min(self.p2_max_mp, self.p2_mp + 5)
        
        self.turn += 1
        if self.turn > self.max_turns:
            self.active = False
            self.winner = 0
    
    def _perform_attack(self, attacker, defender):
        skill_id = self.p1_skill if attacker == 1 else self.p2_skill
        target_part = self.p1_target if attacker == 1 else self.p2_target
        defend_part = self.p2_defend if attacker == 1 else self.p1_defend
        
        if not skill_id or not target_part:
            return
        
        # Данные
        attacker_player = self.p1 if attacker == 1 else self.p2
        defender_player = self.p2 if attacker == 1 else self.p1
        cooldowns = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
        log = self.log_p1 if attacker == 1 else self.log_p2
        
        # Получаем навык
        if skill_id == "basic_attack":
            skill = {"name": "👊 Базовая атака", "damage_mult": 1.0, "cooldown": 0, "tier": 1}
        else:
            skill = SKILLS_DB.get(skill_id, {"name": "Атака", "damage_mult": 1.0, "cooldown": 1, "tier": 1})
        
        # Проверка маны (для навыков tier > 1)
        mana_cost = skill.get("tier", 1) * 5
        if attacker == 1:
            if self.p1_mp < mana_cost:
                log.append("❌ Недостаточно маны!")
                return
            self.p1_mp -= mana_cost
        else:
            if self.p2_mp < mana_cost:
                log.append("❌ Недостаточно маны!")
                return
            self.p2_mp -= mana_cost
        
        # Базовый урон
        min_d, max_d = attacker_player.get_weapon_damage()
        base_damage = random.randint(min_d, max_d)
        damage = int(base_damage * skill.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_mult = BODY_PARTS.get(target_part, {}).get("multiplier", 1.0)
        damage = int(damage * body_mult)
        
        # Проверка защиты
        if defend_part == target_part:
            # Защита сработала - уменьшаем урон
            defense = defender_player.get_equipment_defense(defend_part)
            reduction = defense / (defense + 50)  # Формула уменьшения урона
            damage = int(damage * (1 - reduction))
            log.append(f"🛡 {defender_player.data['first_name']} защитил {BODY_PARTS[defend_part]['name']}! Урон снижен до {damage}")
        else:
            log.append(f"🎯 Удар в {BODY_PARTS[target_part]['name']}!")
        
        # Крит (шанс 10%)
        is_crit = random.random() < 0.10
        if is_crit:
            damage = int(damage * 1.5)
            log.append("💥 КРИТИЧЕСКИЙ УДАР!")
        
        # Уклонение (шанс 5%)
        if random.random() < 0.05:
            damage = 0
            log.append("💨 Уклонение!")
        
        # Нанесение урона
        if damage > 0:
            if defender == 1:
                self.p1_hp = max(0, self.p1_hp - damage)
            else:
                self.p2_hp = max(0, self.p2_hp - damage)
            
            log.append(f"⚔ Нанесено {damage} урона")
            
            # Вампиризм
            if "life_steal" in skill:
                heal = int(damage * skill["life_steal"])
                if attacker == 1:
                    self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
                else:
                    self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
                log.append(f"💚 Вампиризм +{heal} HP")
            
            # Эффекты
            if "burn_chance" in skill and random.random() * 100 < skill["burn_chance"]:
                if defender == 1:
                    self.p1_effects.append({"type": "burn", "duration": 3})
                else:
                    self.p2_effects.append({"type": "burn", "duration": 3})
                log.append("🔥 Горение!")
            
            if "freeze_chance" in skill and random.random() * 100 < skill["freeze_chance"]:
                if defender == 1:
                    self.p1_effects.append({"type": "freeze", "duration": 2})
                else:
                    self.p2_effects.append({"type": "freeze", "duration": 2})
                log.append("❄ Заморозка!")
            
            if "stun_chance" in skill and random.random() * 100 < skill["stun_chance"]:
                if defender == 1:
                    self.p1_effects.append({"type": "stun", "duration": 1})
                else:
                    self.p2_effects.append({"type": "stun", "duration": 1})
                log.append("⚡ Оглушение!")
        
        # Лечение
        if "hp_restore" in skill:
            heal = skill["hp_restore"]
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            log.append(f"💚 +{heal} HP")
        
        # Кулдаун
        if skill.get("cooldown", 0) > 0:
            cooldowns[skill_id] = skill["cooldown"]
    
    def _process_effects(self, player_num):
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        hp = self.p1_hp if player_num == 1 else self.p2_hp
        log = self.log_p1 if player_num == 1 else self.log_p2
        
        for effect in effects[:]:
            if effect["type"] == "burn":
                d = 10
                hp -= d
                log.append(f"🔥 Горение -{d} HP")
            elif effect["type"] == "poison":
                d = 12
                hp -= d
                log.append(f"☠ Яд -{d} HP")
            
            effect["duration"] -= 1
            if effect["duration"] <= 0:
                effects.remove(effect)
        
        if player_num == 1:
            self.p1_hp = max(0, hp)
        else:
            self.p2_hp = max(0, hp)
    
    def _reduce_cooldowns(self, player_num):
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        for sid in list(cooldowns.keys()):
            cooldowns[sid] -= 1
            if cooldowns[sid] <= 0:
                del cooldowns[sid]
    
    def _check_end(self):
        if self.p1_hp <= 0:
            self.active = False
            self.winner = 2
            return True
        elif self.p2_hp <= 0:
            self.active = False
            self.winner = 1
            return True
        return False
    
    def get_state_text(self, player_num):
        """Текст состояния для конкретного игрока"""
        log = self.log_p1 if player_num == 1 else self.log_p2
        phase = self.p1_phase if player_num == 1 else self.p2_phase
        my_defend = self.p1_defend if player_num == 1 else self.p2_defend
        
        my_hp = self.p1_hp if player_num == 1 else self.p2_hp
        my_max_hp = self.p1_max_hp if player_num == 1 else self.p2_max_hp
        my_mp = self.p1_mp if player_num == 1 else self.p2_mp
        my_max_mp = self.p1_max_mp if player_num == 1 else self.p2_max_mp
        
        opp_hp = self.p2_hp if player_num == 1 else self.p1_hp
        opp_max_hp = self.p2_max_hp if player_num == 1 else self.p1_max_hp
        
        def hp_bar(cur, mx):
            pct = cur / mx * 100 if mx > 0 else 0
            f = int(pct / 10)
            e = 10 - f
            return f"[{'█'*f}{'░'*e}] {cur}/{mx} ({pct:.0f}%)"
        
        text = f"""
<b>⚔ ДУЭЛЬ — Ход {self.turn}</b>
🏟 {self.arena}

<b>ВЫ:</b> {self.get_player_name(player_num)}
❤ {hp_bar(my_hp, my_max_hp)}
💎 MP: {my_mp}/{my_max_mp}
🛡 Защита: {BODY_PARTS.get(my_defend, {}).get('name', 'Не выбрана') if my_defend else 'Не выбрана'}

<b>ПРОТИВНИК:</b> {self.get_player_name(3-player_num)}
❤ {hp_bar(opp_hp, opp_max_hp)}
"""
        
        if phase == "defend":
            text += "\n🛡 <b>Выберите часть тела для защиты:</b>"
        elif phase == "attack":
            text += "\n🎯 <b>Выберите цель и навык атаки:</b>"
        elif phase == "waiting":
            text += "\n⏳ <b>Ожидание хода противника...</b>"
        
        # Последние логи
        if log:
            text += f"\n\n<i>{log[-1]}</i>"
        
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

# ==================== КЭШ ДУЭЛЕЙ ====================
active_duels = {}  # {user_id: DuelInstance}
duel_messages = {}  # {user_id: {"chat_id": chat_id, "message_id": message_id}}

def send_duel_message(duel, user_id):
    """Отправить или обновить сообщение дуэли для игрока"""
    player_num = 1 if str(user_id) == duel.p1_id else 2
    text = duel.get_state_text(player_num)
    
    if str(user_id) in duel_messages:
        msg_data = duel_messages[str(user_id)]
        try:
            bot.edit_message_text(
                text[:4000],
                msg_data["chat_id"],
                msg_data["message_id"],
                reply_markup=get_duel_markup(duel, user_id)
            )
        except:
            pass
    else:
        # Отправляем новое сообщение (в ЛС или чат)
        try:
            msg = bot.send_message(
                int(user_id),
                text[:4000],
                reply_markup=get_duel_markup(duel, user_id)
            )
            duel_messages[str(user_id)] = {"chat_id": msg.chat.id, "message_id": msg.message_id}
        except:
            pass

def get_duel_markup(duel, user_id):
    """Клавиатура для дуэли"""
    player_num = 1 if str(user_id) == duel.p1_id else 2
    phase = duel.p1_phase if player_num == 1 else duel.p2_phase
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if phase == "defend":
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']}",
                callback_data=f"d_def_{part}"
            ))
    
    elif phase == "attack":
        # Сначала выбор цели
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🎯 {data['name']}",
                callback_data=f"d_tgt_{part}"
            ))
    
    elif phase == "waiting":
        markup.add(types.InlineKeyboardButton("⏳ Ждём...", callback_data="d_wait"))
    
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="d_surr"))
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="d_ref"))
    
    return markup

# Временное хранилище для выбора цели
target_temp = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("d_tgt_"))
def duel_target_handler(call):
    user_id = str(call.from_user.id)
    part = call.data.split("_")[2]
    
    duel = active_duels.get(user_id)
    if not duel or not duel.active:
        return
    
    target_temp[user_id] = part
    
    # Показываем навыки
    player_num = 1 if user_id == duel.p1_id else 2
    skills = duel.get_available_skills(player_num)
    
    text = duel.get_state_text(player_num) + f"\n🎯 Цель: <b>{BODY_PARTS[part]['name']}</b>\n<b>Выберите навык:</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for sid in skills:
        skill = SKILLS_DB.get(sid, {"name": sid, "cooldown": 0, "tier": 1})
        name = skill.get("name", sid)
        cd = skill.get("cooldown", 0)
        tier = skill.get("tier", 1)
        stars = "⭐" * tier
        
        if cd > 0:
            name = f"⏳ {name} (CD:{cd})"
        
        markup.add(types.InlineKeyboardButton(
            f"{stars} {name} (x{skill.get('damage_mult', 1.0)})",
            callback_data=f"d_skl_{sid}"
        ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="d_back"))
    
    try:
        bot.edit_message_text(
            text[:4000],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "d_back")
def duel_back_handler(call):
    user_id = str(call.from_user.id)
    duel = active_duels.get(user_id)
    if duel:
        send_duel_message(duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("d_skl_"))
def duel_skill_handler(call):
    user_id = str(call.from_user.id)
    skill_id = call.data.split("_")[2]
    
    duel = active_duels.get(user_id)
    if not duel or not duel.active:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    target = target_temp.get(user_id, "body")
    player_num = 1 if user_id == duel.p1_id else 2
    
    duel.execute_attack(player_num, skill_id, target)
    
    # Обновляем сообщения обоим игрокам
    send_duel_message(duel, duel.p1_id)
    send_duel_message(duel, duel.p2_id)
    
    # Проверка завершения
    if not duel.active:
        finish_duel(duel)

@bot.callback_query_handler(func=lambda call: call.data.startswith("d_"))
def duel_actions_handler(call):
    user_id = str(call.from_user.id)
    action = call.data.split("_")[1]
    
    if action == "def":
        part = call.data.split("_")[2]
        duel = active_duels.get(user_id)
        if duel and duel.active:
            player_num = 1 if user_id == duel.p1_id else 2
            duel.set_defend(player_num, part)
            
            # Если бот - он сразу выбирает защиту и атаку
            other_id = duel.p2_id if user_id == duel.p1_id else duel.p1_id
            if other_id.startswith("bot_"):
                other_num = 3 - player_num
                # Бот выбирает защиту
                if duel.p2_phase == "defend" if other_num == 2 else duel.p1_phase == "defend":
                    bot_def = random.choice(list(BODY_PARTS.keys()))
                    duel.set_defend(other_num, bot_def)
                
                # Бот выбирает атаку
                if duel.p2_phase == "attack" if other_num == 2 else duel.p1_phase == "attack":
                    bot_target = random.choice(list(BODY_PARTS.keys()))
                    bot_skills = duel.get_available_skills(other_num)
                    if bot_skills:
                        duel.execute_attack(other_num, random.choice(bot_skills), bot_target)
            
            send_duel_message(duel, duel.p1_id)
            send_duel_message(duel, duel.p2_id)
            
            if not duel.active:
                finish_duel(duel)
    
    elif action == "wait":
        duel = active_duels.get(user_id)
        if duel and duel.active:
            send_duel_message(duel, user_id)
    
    elif action == "ref":
        duel = active_duels.get(user_id)
        if duel and duel.active:
            send_duel_message(duel, user_id)
    
    elif action == "surr":
        duel = active_duels.get(user_id)
        if duel and duel.active:
            duel.active = False
            duel.winner = 2 if user_id == duel.p1_id else 1
            finish_duel(duel)

def finish_duel(duel):
    """Завершение дуэли и отправка результатов"""
    # Очистка ботов
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") and uid in users:
            del users[uid]
    save_json(DATA_FILES['users'], users)
    
    # Очистка активных дуэлей
    for uid in list(active_duels.keys()):
        if active_duels[uid] == duel:
            del active_duels[uid]
    
    if duel.winner == 0:
        result = "<b>🤝 НИЧЬЯ!</b>"
        for uid in [duel.p1_id, duel.p2_id]:
            send_result(uid, result)
        return
    
    winner_id = duel.p1_id if duel.winner == 1 else duel.p2_id
    loser_id = duel.p2_id if duel.winner == 1 else duel.p1_id
    
    # Результаты для победителя
    if not winner_id.startswith("bot_"):
        winner = Player(winner_id)
        reward = duel.bet * 2 if not duel.is_tournament else 0
        if reward > 0:
            winner.data["money"] += reward
        winner.data["wins"] += 1
        winner.data["total_duels"] += 1
        winner.data["exp"] += 50
        check_level_up(winner)
        winner.save()
        
        win_text = f"""
<b>🏆 ПОБЕДА!</b>

Противник: <b>{duel.get_player_name(3 - duel.winner)}</b>
💰 Награда: <b>{reward} монет</b>
📊 Ходов: <b>{duel.turn}</b>
"""
        send_result(winner_id, win_text)
    
    # Результаты для проигравшего
    if not loser_id.startswith("bot_"):
        loser = Player(loser_id)
        loser.data["losses"] += 1
        loser.data["total_duels"] += 1
        loser.data["exp"] += 20
        check_level_up(loser)
        loser.save()
        
        lose_text = f"""
<b>💀 ПОРАЖЕНИЕ</b>

Противник: <b>{duel.get_player_name(duel.winner)}</b>
📊 Ходов: <b>{duel.turn}</b>
"""
        send_result(loser_id, lose_text)
    
    # Очистка сообщений дуэли
    for uid in [duel.p1_id, duel.p2_id]:
        duel_messages.pop(str(uid), None)

def send_result(user_id, text):
    """Отправить результат игроку"""
    try:
        bot.send_message(int(user_id), text)
    except:
        pass

# ==================== ОБРАБОТЧИКИ КОМАНД ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if str(user_id) in banned_users:
        bot.send_message(message.chat.id, "⛔ Вы забанены!")
        return
    
    # Исправленное определение username
    username = message.from_user.username
    if not username:
        username = f"user_{user_id}"
    
    first_name = message.from_user.first_name or "Игрок"
    Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v11.0 ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

🎯 <b>СИСТЕМА БОЯ:</b>
• Выберите защиту → выберите атаку
• Броня уменьшает урон!
• Навыки оружия с кулдаунами
• Разные виды дуэлей

💰 Старт: <b>500 монет</b>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль (бот)", callback_data="duel_quick"),
        types.InlineKeyboardButton("👥 Найти соперника", callback_data="duel_find"),
        types.InlineKeyboardButton("🏆 Рейтинговая", callback_data="duel_ranked"),
        types.InlineKeyboardButton("💀 Хардкор (500💰)", callback_data="duel_hardcore"),
        types.InlineKeyboardButton("🎯 Спарринг (0💰)", callback_data="duel_sparring")
    )
    
    bot.send_message(message.chat.id, "<b>⚔️ ДУЭЛИ</b>\n\nВыберите тип дуэли:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="hero_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="hero_inventory"),
        types.InlineKeyboardButton("🏅 Достижения", callback_data="hero_achievements"),
        types.InlineKeyboardButton("✨ Зачарования", callback_data="hero_enchantments"),
        types.InlineKeyboardButton("👁 Экипировка", callback_data="hero_equipped"),
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
        types.InlineKeyboardButton("💱 Рынок", callback_data="trade_market")
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
@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_"))
def duel_type_handler(call):
    dt = call.data.split("_")[1]
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if dt == "quick":
        markup = types.InlineKeyboardMarkup(row_width=3)
        for bet in [50, 100, 200, 500]:
            markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"qduel_{bet}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_duel"))
        
        bot.edit_message_text(
            f"<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n💰 Баланс: {player.data['money']}💰\nВыберите ставку:",
            call.message.chat.id, call.message.message_id, reply_markup=markup
        )
    
    elif dt == "find":
        # Поиск соперника
        find_opponent(call)
    
    elif dt in ["ranked", "hardcore", "sparring"]:
        bets = {"ranked": 100, "hardcore": 500, "sparring": 0}
        bet = bets[dt]
        
        if bet > 0 and player.data["money"] < bet:
            bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
            return
        
        start_bot_duel(call, dt, bet)

def find_opponent(call):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    # Проверяем очередь
    queue = matchmaking_queue.get("quick", [])
    queue = [q for q in queue if q != user_id]
    
    if queue:
        opponent_id = queue.pop(0)
        matchmaking_queue["quick"] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        # Проверяем баланс
        bet = 50
        opponent = Player(opponent_id)
        if player.data["money"] < bet or opponent.data["money"] < bet:
            bot.edit_message_text("❌ У одного из игроков недостаточно монет!", call.message.chat.id, call.message.message_id)
            return
        
        player.data["money"] -= bet
        opponent.data["money"] -= bet
        player.save()
        opponent.save()
        
        duel = DuelInstance(user_id, opponent_id, "pvp", bet)
        active_duels[user_id] = duel
        active_duels[opponent_id] = duel
        
        bot.edit_message_text("⚔ Соперник найден! Дуэль начинается!", call.message.chat.id, call.message.message_id)
        send_duel_message(duel, user_id)
        send_duel_message(duel, opponent_id)
    else:
        queue.append(user_id)
        matchmaking_queue["quick"] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        # Запускаем бота через 5 секунд
        threading.Timer(5.0, start_bot_duel_timer, args=[call.message.chat.id, call.message.message_id, user_id]).start()
        
        bot.edit_message_text("🔍 Поиск соперника... Ожидание 5 сек.", call.message.chat.id, call.message.message_id)

def start_bot_duel_timer(chat_id, message_id, user_id):
    """Запуск дуэли с ботом если соперник не найден"""
    if str(user_id) in active_duels:
        return
    
    # Убираем из очереди
    queue = matchmaking_queue.get("quick", [])
    queue = [q for q in queue if q != user_id]
    matchmaking_queue["quick"] = queue
    save_json(DATA_FILES['matchmaking'], matchmaking_queue)
    
    start_bot_duel_direct(chat_id, message_id, user_id, "quick", 50)

def start_bot_duel(call, duel_type, bet):
    """Запуск дуэли с ботом через callback"""
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if bet > 0:
        player.data["money"] -= bet
        player.save()
    
    create_bot_duel(user_id, duel_type, bet, call.message.chat.id, call.message.message_id)

def start_bot_duel_direct(chat_id, message_id, user_id, duel_type, bet):
    """Запуск дуэли с ботом напрямую"""
    player = Player(user_id)
    if bet > 0 and player.data["money"] >= bet:
        player.data["money"] -= bet
        player.save()
    
    create_bot_duel(user_id, duel_type, bet, chat_id, message_id)

def create_bot_duel(user_id, duel_type, bet, chat_id, message_id):
    """Создание дуэли с ботом"""
    player = Player(user_id)
    bot_level = player.data["level"]
    bot_id = f"bot_{random.randint(100000, 999999)}"
    
    # Генерация бота
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    for slot, item_type in [("head", "helmet"), ("body", "armor"), ("legs", "boots")]:
        slot_items = [k for k, v in items.items() if v.get("type") == item_type and v.get("level_req", 1) <= bot_level]
        if slot_items and random.random() < 0.6:
            equip[slot] = random.choice(slot_items)
    
    weapon_items = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= bot_level]
    if weapon_items:
        equip["weapon"] = random.choice(weapon_items)
    
    users[bot_id] = {
        "username": f"bot_{bot_level}", "first_name": f"🤖 Бот Lv.{bot_level}",
        "money": 0, "level": bot_level, "exp": 0, "total_exp": 0,
        "hp": 100 + bot_level * 5, "max_hp": 100 + bot_level * 5,
        "mana": 50 + bot_level * 3, "max_mana": 50 + bot_level * 3,
        "base_damage": 10 + bot_level,
        "wins": 0, "losses": 0, "draws": 0,
        "win_streak": 0, "best_streak": 0, "total_duels": 0,
        "pvp_rating": 1000, "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Бот", "titles_collected": ["Бот"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    duel = DuelInstance(user_id, bot_id, duel_type, bet)
    active_duels[user_id] = duel
    
    bot.edit_message_text("⚔ Дуэль с ботом начинается!", chat_id, message_id)
    send_duel_message(duel, user_id)
    
    # Бот сразу выбирает защиту
    bot_def = random.choice(list(BODY_PARTS.keys()))
    duel.set_defend(2, bot_def)
    
    # Бот выбирает атаку
    bot_target = random.choice(list(BODY_PARTS.keys()))
    bot_skills = duel.get_available_skills(2)
    if bot_skills:
        duel.execute_attack(2, random.choice(bot_skills), bot_target)
        send_duel_message(duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def quick_duel_bet(call):
    bet = int(call.data.split("_")[1])
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    player.data["money"] -= bet
    player.save()
    
    create_bot_duel(user_id, "quick", bet, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "back_duel")
def back_duel(call):
    duel_section(call.message)

# ==================== МАГАЗИН ====================
@bot.callback_query_handler(func=lambda call: call.data == "trade_shop")
def shop_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚔ Оружие", callback_data="shop_weapon"),
        types.InlineKeyboardButton("👤 Шлемы", callback_data="shop_helmet"),
        types.InlineKeyboardButton("🦾 Броня", callback_data="shop_armor"),
        types.InlineKeyboardButton("🦿 Обувь", callback_data="shop_boots"),
        types.InlineKeyboardButton("🧪 Зелья", callback_data="shop_potion"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_trade")
    )
    
    player = Player(call.from_user.id)
    bot.edit_message_text(
        f"<b>🛒 МАГАЗИН</b>\n💰 {player.data['money']}💰",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("shop_"))
def shop_category(call):
    cat = call.data.split("_")[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    type_map = {"weapon": "weapon", "helmet": "helmet", "armor": "armor", "boots": "boots", "potion": "potion"}
    item_type = type_map.get(cat, cat)
    
    cat_names = {"weapon": "⚔ ОРУЖИЕ", "helmet": "👤 ШЛЕМЫ", "armor": "🦾 БРОНЯ", "boots": "🦿 ОБУВЬ", "potion": "🧪 ЗЕЛЬЯ"}
    
    cat_items = {k: v for k, v in items.items() if v.get("type") == item_type}
    
    text = f"<b>{cat_names.get(cat, cat)}</b>\n💰 {player.data['money']}💰\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for ik, item in sorted(cat_items.items(), key=lambda x: x[1].get("price", 0)):
        if player.data["level"] < item.get("level_req", 1):
            continue
        
        r = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
        
        if item_type == "weapon":
            s = f"Урон: {item['damage'][0]}-{item['damage'][1]}"
        elif item_type in ["helmet", "armor", "boots"]:
            s = f"Защита: {item.get('defense', 0)}"
        elif item_type == "potion":
            s = f"Лечение: {item.get('heal', 0)}"
        else:
            s = ""
        
        text += f"{r} <b>{item['name']}</b> — {s}\n💰 {item['price']} | Ур.{item.get('level_req', 1)}\n\n"
        
        if player.data["money"] >= item["price"]:
            markup.add(types.InlineKeyboardButton(
                f"Купить: {item['name']} - {item['price']}💰",
                callback_data=f"buy_{ik}"
            ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="trade_shop"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_item(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(ik) or limited_items.get(ik)
    if not item:
        bot.answer_callback_query(call.id, "❌ Предмет не найден!")
        return
    
    if player.data["level"] < item.get("level_req", 1):
        bot.answer_callback_query(call.id, f"❌ Нужен {item.get('level_req', 1)} уровень!")
        return
    
    if player.data["money"] < item["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    if ik in limited_items:
        if limited_items[ik]["remaining"] <= 0:
            bot.answer_callback_query(call.id, "❌ Предмет закончился!")
            return
        limited_items[ik]["remaining"] -= 1
        save_json(DATA_FILES['limited'], limited_items)
    
    player.data["money"] -= item["price"]
    player.data["inventory"].append(ik)
    player.data["items_found"] += 1
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ {item['name']} куплен!")
    shop_category(call)

# ==================== ГЕРОЙ ====================
@bot.callback_query_handler(func=lambda call: call.data == "hero_stats")
def hero_stats(call):
    user_id = call.from_user.id
    player = Player(user_id)
    d = player.data
    
    wr = (d["wins"] / d["total_duels"] * 100) if d["total_duels"] > 0 else 0
    
    text = f"""
<b>📊 СТАТИСТИКА</b>

<b>{d['first_name']}</b> | {d['title']}
⭐ Ур.{d['level']} | 📊 {d['pvp_rating']}
💰 {d['money']}💰

⚔ Урон оружия: {player.get_weapon_damage()[0]}-{player.get_weapon_damage()[1]}
🛡 Защита: Г:{player.get_equipment_defense('head')} Т:{player.get_equipment_defense('body')} Н:{player.get_equipment_defense('legs')}

🏆 Побед: {d['wins']} | 💀 Поражений: {d['losses']}
📈 Винрейт: {wr:.1f}%
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_hero"))
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
                eq = " [🟢]"
        
        ench = player.data.get("enchantments", {}).get(ik, {})
        ench_text = f" ✨{ench.get('name', '')}" if ench else ""
        
        text += f"{idx}. {r} {item['name']} x{cnt}{eq}{ench_text}\n"
        
        if item.get("type") in ["weapon", "helmet", "armor", "boots"]:
            markup.add(types.InlineKeyboardButton(f"Экипировать: {item['name']}", callback_data=f"eq_{ik}"))
            if item.get("enchantable"):
                markup.add(types.InlineKeyboardButton(f"Зачаровать: {item['name']}", callback_data=f"ench_{ik}"))
        elif item.get("type") == "potion":
            markup.add(types.InlineKeyboardButton(f"Использовать: {item['name']}", callback_data=f"use_{ik}"))
        
        idx += 1
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_hero"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("eq_"))
def equip_item(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(ik) or limited_items.get(ik)
    if not item:
        bot.answer_callback_query(call.id, "❌ Предмет не найден!")
        return
    
    if ik not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌ Нет в инвентаре!")
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("ench_"))
def enchant_item(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(ik) or limited_items.get(ik)
    if not item or not item.get("enchantable"):
        bot.answer_callback_query(call.id, "❌ Нельзя зачаровать!")
        return
    
    cost = item.get("price", 100) // 2
    if player.data["money"] < cost:
        bot.answer_callback_query(call.id, f"❌ Нужно {cost}💰!")
        return
    
    player.data["money"] -= cost
    ench = random.choice(ENCHANT_EFFECTS)
    player.data.setdefault("enchantments", {})[ik] = {"name": ench["name"], "effect": ench["effect"], "value": ench["value"]}
    player.save()
    
    bot.answer_callback_query(call.id, f"✨ {ench['name']}!")
    hero_inventory(call)

@bot.callback_query_handler(func=lambda call: call.data in ["hero_achievements", "hero_enchantments", "hero_equipped", "hero_heal", "back_hero"])
def hero_handlers(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "hero_achievements":
        text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(player.data['achievements'])}/7)\n\n"
        ach_list = [
            ("first_blood", "🩸 Первая кровь", player.data["wins"] >= 1),
            ("warrior", "⚔ Воин", player.data["wins"] >= 10),
            ("veteran", "🎖 Ветеран", player.data["wins"] >= 50),
            ("legend", "👑 Легенда", player.data["wins"] >= 100),
            ("rich", "💰 Богач", player.data["money"] >= 10000),
            ("dmaster", "🏰 Мастер данжей", player.data.get("dungeons_completed", 0) >= 10),
            ("collector", "🎒 Коллекционер", player.data.get("items_found", 0) >= 20)
        ]
        for aid, name, cond in ach_list:
            icon = "✅" if aid in player.data["achievements"] or cond else "🔒"
            text += f"{icon} {name}\n"
            if cond and aid not in player.data["achievements"]:
                player.data["achievements"].append(aid)
        player.save()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_hero"))
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
                text += f"📦 {item['name']}: {ench.get('name', 'Нет')}\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_hero"))
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
                    text += f"{sn}: <b>{item['name']}</b>\n"
                else:
                    text += f"{sn}: ❌\n"
            else:
                text += f"{sn}: ❌ Пусто\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_heal":
        potions = [k for k in player.data["inventory"] if items.get(k, {}).get("type") == "potion" and items.get(k, {}).get("heal", 0) > 0]
        if not potions:
            bot.edit_message_text("💊 Нет зелий!", call.message.chat.id, call.message.message_id)
            return
        if player.data["hp"] >= player.data["max_hp"]:
            bot.edit_message_text("💊 Полное HP!", call.message.chat.id, call.message.message_id)
            return
        pk = potions[0]
        potion = items[pk]
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + potion["heal"])
        player.data["inventory"].remove(pk)
        player.save()
        bot.edit_message_text(f"💊 {potion['name']}\n❤ HP: {player.data['hp']}/{player.data['max_hp']}", call.message.chat.id, call.message.message_id)
    
    elif call.data == "back_hero":
        hero_section(call.message)

# ==================== ТОРГОВЛЯ ====================
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
            text += f"<b>{item['name']}</b>\n[{pct}{emp}] {item['remaining']}/{item['total']}\n💰 {item['price']}💰\n\n"
            markup.add(types.InlineKeyboardButton(f"Купить - {item['price']}💰", callback_data=f"buy_{ik}"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_trade"))
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
    exp = random.randint(80, 250)
    
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
            markup.add(types.InlineKeyboardButton(f"Купить: {item['name']}", callback_data=f"mkt_{lid}"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_trade"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mkt_"))
def market_buy(call):
    lid = call.data.split("_", 1)[1]
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if lid not in market_listings:
        bot.answer_callback_query(call.id, "❌ Лот продан!")
        return
    
    listing = market_listings[lid]
    if user_id == str(listing.get("seller_id")):
        bot.answer_callback_query(call.id, "❌ Нельзя купить своё!")
        return
    
    if player.data["money"] < listing["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
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
    bot.answer_callback_query(call.id, f"✅ {item.get('name', 'Предмет')} куплен!")
    market_menu(call)

@bot.callback_query_handler(func=lambda call: call.data in ["back_trade", "back_hero"])
def back_handlers(call):
    if call.data == "back_trade":
        trade_section(call.message)
    elif call.data == "back_hero":
        hero_section(call.message)

# ==================== МИР ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_dungeons")
def world_dungeons(call):
    text = """
<b>🏰 ПОДЗЕМЕЛЬЯ</b>

🐺 Логово волка (3 волны)
🕷 Паучьи пещеры (3 волны)
💀 Катакомбы (3 волны)
🐉 Драконье логово (3 волны)
👹 Бездна (3 волны)

Кулдаун: 1 час
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, name in enumerate(["🐺 Логово волка", "🕷 Паучьи пещеры", "💀 Катакомбы", "🐉 Драконье логово", "👹 Бездна"], 1):
        markup.add(types.InlineKeyboardButton(name, callback_data=f"dung_{i}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dung_"))
def start_dungeon(call):
    dungeon_level = int(call.data.split("_")[1])
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    level_reqs = [1, 5, 10, 15, 25]
    if player.data["level"] < level_reqs[dungeon_level - 1]:
        bot.answer_callback_query(call.id, f"❌ Нужен {level_reqs[dungeon_level-1]} уровень!")
        return
    
    if player.data.get("last_dungeon"):
        last = datetime.fromisoformat(player.data["last_dungeon"])
        if (datetime.now() - last) < timedelta(hours=1):
            remaining = timedelta(hours=1) - (datetime.now() - last)
            bot.answer_callback_query(call.id, f"⏰ Ждите {remaining.seconds//60} мин.")
            return
    
    # Создаём 3 волны боссов
    dungeon_progress[user_id] = {
        "level": dungeon_level,
        "wave": 1,
        "total_waves": 3,
        "reward": random.randint(50, 250) * dungeon_level * player.data["level"],
        "exp": 50 * dungeon_level * player.data["level"]
    }
    save_json(DATA_FILES['dungeons'], dungeon_progress)
    
    start_dungeon_wave(call.message.chat.id, call.message.message_id, user_id)

def start_dungeon_wave(chat_id, message_id, user_id):
    """Начать волну данжа"""
    dg = dungeon_progress.get(str(user_id), {})
    wave = dg.get("wave", 1)
    dl = dg.get("level", 1)
    
    player = Player(user_id)
    boss_level = level_reqs = [1, 5, 10, 15, 25][dl - 1] * 2 + wave * 2
    
    boss_id = f"boss_{random.randint(100000, 999999)}"
    boss_names = {
        1: ["🐺 Волк", "🐺 Матёрый волк", "🐺 Вожак стаи"],
        2: ["🕷 Паук", "🕷 Ядовитый паук", "🕷 Королева пауков"],
        3: ["💀 Скелет", "💀 Рыцарь смерти", "💀 Некромант"],
        4: ["🐉 Драконид", "🐉 Огненный дракон", "🐉 Древний дракон"],
        5: ["👹 Бес", "👹 Демон", "👹 Владыка бездны"]
    }
    
    boss_name = boss_names.get(dl, ["Босс"])[wave - 1]
    
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    for slot, itype in [("head", "helmet"), ("body", "armor"), ("legs", "boots")]:
        sitems = [k for k, v in items.items() if v.get("type") == itype and v.get("level_req", 1) <= boss_level]
        if sitems:
            equip[slot] = random.choice(sitems)
    wpns = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= boss_level]
    if wpns:
        equip["weapon"] = random.choice(wpns)
    
    users[boss_id] = {
        "username": f"boss_{boss_level}", "first_name": boss_name,
        "money": 0, "level": boss_level, "exp": 0, "total_exp": 0,
        "hp": 100 + boss_level * 8, "max_hp": 100 + boss_level * 8,
        "mana": 50, "max_mana": 50, "base_damage": 15 + boss_level,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000, "inventory": [],
        "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Босс", "titles_collected": ["Босс"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    duel = DuelInstance(user_id, boss_id, "dungeon", 0)
    active_duels[user_id] = duel
    
    bot.edit_message_text(f"⚔ Волна {wave}/3: <b>{boss_name}</b>!", chat_id, message_id)
    send_duel_message(duel, user_id)
    
    # Босс выбирает защиту
    duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
    
    # Босс выбирает атаку
    boss_target = random.choice(list(BODY_PARTS.keys()))
    boss_skills = duel.get_available_skills(2)
    if boss_skills:
        duel.execute_attack(2, random.choice(boss_skills), boss_target)
        send_duel_message(duel, user_id)

# Переопределяем finish_duel для обработки данжей
original_finish = finish_duel

def finish_duel_with_dungeon(duel):
    """Обёртка для обработки данжей"""
    if duel.duel_type == "dungeon":
        player_id = duel.p1_id
        
        if duel.winner == 1:
            # Игрок победил волну
            dg = dungeon_progress.get(str(player_id), {})
            wave = dg.get("wave", 1)
            
            if wave < 3:
                # Следующая волна
                dg["wave"] = wave + 1
                dungeon_progress[str(player_id)] = dg
                save_json(DATA_FILES['dungeons'], dungeon_progress)
                
                # Отправляем результат
                player = Player(player_id)
                player.data["exp"] += 30
                player.save()
                
                send_result(player_id, f"✅ Волна {wave} пройдена! Следующая волна...")
                
                # Запускаем следующую волну
                start_dungeon_wave(int(player_id), 0, player_id)
            else:
                # Все волны пройдены
                player = Player(player_id)
                player.data["money"] += dg.get("reward", 100)
                player.data["exp"] += dg.get("exp", 50)
                player.data["total_exp"] += dg.get("exp", 50)
                player.data["dungeons_completed"] = player.data.get("dungeons_completed", 0) + 1
                player.data["last_dungeon"] = datetime.now().isoformat()
                
                # Шанс на предмет
                if random.random() < 0.3:
                    possible = [k for k, v in items.items() if v.get("level_req", 1) <= player.data["level"]]
                    if possible:
                        ik = random.choice(possible)
                        player.data["inventory"].append(ik)
                        player.data["items_found"] += 1
                
                check_level_up(player)
                player.save()
                
                send_result(player_id, f"""
<b>🏰 ДАНЖ ПРОЙДЕН!</b>

✅ Все 3 волны побеждены!
💰 +{dg.get('reward', 100)} монет
✨ +{dg.get('exp', 50)} опыта
""")
                
                dungeon_progress.pop(str(player_id), None)
                save_json(DATA_FILES['dungeons'], dungeon_progress)
        else:
            # Игрок проиграл
            send_result(player_id, f"💀 Вы проиграли на волне {dg.get('wave', 1)}")
            dungeon_progress.pop(str(player_id), None)
            save_json(DATA_FILES['dungeons'], dungeon_progress)
        
        # Очистка
        for uid in list(active_duels.keys()):
            if active_duels[uid] == duel:
                del active_duels[uid]
        for uid in [duel.p1_id, duel.p2_id]:
            if uid.startswith("boss_") and uid in users:
                del users[uid]
        save_json(DATA_FILES['users'], users)
    else:
        original_finish(duel)

finish_duel = finish_duel_with_dungeon

# ==================== ТУРНИРЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_tournaments")
def world_tournaments(call):
    if not tournaments.get("active"):
        tournaments["active"] = {
            "name": "Турнир",
            "participants": [],
            "prize_pool": 5000,
            "status": "registration",
            "round": 0,
            "bracket": []
        }
        save_json(DATA_FILES['tournaments'], tournaments)
    
    tour = tournaments["active"]
    
    text = f"""
<b>🏟 ТУРНИР</b>

<b>{tour['name']}</b>
Статус: {tour.get('status', 'Регистрация')}
Участников: {len(tour.get('participants', []))}
Приз: <b>{tour.get('prize_pool', 0)}💰</b>
Взнос: 500💰
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🏆 Участвовать (500💰)", callback_data="tour_join"),
        types.InlineKeyboardButton("📋 Участники", callback_data="tour_list"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_world")
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "tour_join")
def tour_join(call):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if player.data["money"] < 500:
        bot.answer_callback_query(call.id, "❌ Нужно 500💰!")
        return
    
    tour = tournaments.get("active", {})
    participants = tour.get("participants", [])
    
    if user_id in participants:
        bot.answer_callback_query(call.id, "❌ Уже участвуете!")
        return
    
    player.data["money"] -= 500
    player.save()
    
    participants.append(user_id)
    tour["participants"] = participants
    tour["prize_pool"] = tour.get("prize_pool", 0) + 500
    tournaments["active"] = tour
    save_json(DATA_FILES['tournaments'], tournaments)
    
    # Если набралось 4 участника - запускаем турнир
    if len(participants) >= 4:
        start_tournament()
    
    bot.answer_callback_query(call.id, "✅ Зарегистрированы!")
    world_tournaments(call)

def start_tournament():
    """Запуск турнира"""
    tour = tournaments.get("active", {})
    participants = tour.get("participants", [])
    
    if len(participants) < 2:
        return
    
    # Создаём сетку
    bracket = []
    random.shuffle(participants)
    
    # Пары для первого раунда
    for i in range(0, len(participants), 2):
        if i + 1 < len(participants):
            bracket.append({
                "round": 1,
                "p1": participants[i],
                "p2": participants[i + 1],
                "winner": None,
                "status": "pending"
            })
    
    tournament_brackets["current"] = bracket
    save_json(DATA_FILES['tournament_brackets'], tournament_brackets)
    
    tour["status"] = "in_progress"
    tour["round"] = 1
    tournaments["active"] = tour
    save_json(DATA_FILES['tournaments'], tournaments)
    
    # Запускаем первые дуэли
    for match in bracket:
        if match["status"] == "pending":
            duel = DuelInstance(match["p1"], match["p2"], "tournament", 0, is_tournament=True)
            active_duels[match["p1"]] = duel
            active_duels[match["p2"]] = duel
            
            send_duel_message(duel, match["p1"])
            send_duel_message(duel, match["p2"])

# ==================== ИВЕНТЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_events")
def world_events(call):
    current = events.get("current", {})
    
    if not current or datetime.fromisoformat(current.get("expires", "2000-01-01")) < datetime.now():
        new_event = {
            "name": random.choice(["🌋 Извержение", "❄ Буран", "⚡ Гроза", "🌑 Затмение", "✨ Звездопад"]),
            "description": random.choice(["Урон +20%", "Защита +20%", "Крит +15%", "Вампиризм +10%"]),
            "reward_money": random.randint(200, 1000),
            "reward_ench": random.choice(ENCHANT_EFFECTS),
            "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        events["current"] = new_event
        save_json(DATA_FILES['events'], events)
    
    ev = events["current"]
    time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
    minutes = max(0, time_left.seconds // 60)
    
    text = f"""
<b>🌍 ИВЕНТ</b>

<b>{ev['name']}</b>
📝 {ev['description']}
💰 Награда: {ev['reward_money']} монет
✨ Зачарование: {ev['reward_ench']['name']}
⏰ {minutes} мин.
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== ТОП ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_top")
def world_top(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⭐ Уровень", callback_data="top_level"),
        types.InlineKeyboardButton("⚔ Победы", callback_data="top_wins"),
        types.InlineKeyboardButton("💰 Монеты", callback_data="top_money"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_world")
    )
    bot.edit_message_text("<b>📊 ТОП</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

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
    else:
        return
    
    medals = ["🥇", "🥈", "🥉"] + [f"{i}️⃣" for i in range(4, 11)]
    text = f"<b>{t}</b>\n\n"
    
    for i, (uid, data) in enumerate(su):
        if cat == "level":
            val = f"Ур.{data.get('level', 1)}"
        elif cat == "wins":
            val = f"{data.get('wins', 0)} побед"
        else:
            val = f"{data.get('money', 0)}💰"
        
        text += f"{medals[i]} {data.get('first_name', 'Игрок')}: {val}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_top"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "world_help")
def world_help(call):
    text = "<b>ℹ ПОМОЩЬ</b>\n\n⚔ /duel — дуэль\n🛒 /shop — магазин\n👤 /stats — статистика"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["back_world", "tour_list"])
def world_handlers(call):
    if call.data == "back_world":
        world_section(call.message)
    elif call.data == "tour_list":
        participants = tournaments.get("active", {}).get("participants", [])
        if not participants:
            bot.answer_callback_query(call.id, "📋 Нет участников")
            return
        text = "<b>📋 УЧАСТНИКИ</b>\n\n"
        for i, uid in enumerate(participants, 1):
            p = Player(uid)
            text += f"{i}. {p.data['first_name']} (Lv.{p.data['level']})\n"
        bot.send_message(call.message.chat.id, text)

# ==================== КЛАНЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_clans")
def world_clans(call):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if player.data.get("clan"):
        clan = clans.get(player.data["clan"], {})
        text = f"<b>🛡 {player.data['clan']}</b>\n👥 {len(clan.get('members', []))} уч.\n💰 Казна: {clan.get('treasury', 0)}💰"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("👥 Участники", callback_data="clan_m"),
            types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_l")
        )
    else:
        text = "<b>🛡 КЛАНЫ</b>\n/createclan [имя]\n/joinclan [имя]"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("📋 Список", callback_data="clan_list"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(commands=['createclan', 'joinclan'])
def clan_commands(message):
    cmd = message.text.split()[0].replace('/', '')
    user_id = str(message.from_user.id)
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
        clans[name] = {"leader_id": user_id, "leader_name": message.from_user.first_name, "members": [message.from_user.first_name], "treasury": 0}
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

# ==================== АДМИН ====================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
        types.InlineKeyboardButton("💰 Выдать деньги", callback_data="adm_money"),
        types.InlineKeyboardButton("🎁 Выдать предмет", callback_data="adm_item"),
        types.InlineKeyboardButton("⛔ Бан", callback_data="adm_ban"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_bcast"),
        types.InlineKeyboardButton("👁 Инфо", callback_data="adm_info"),
        types.InlineKeyboardButton("🏟 Турнир", callback_data="adm_tour"),
        types.InlineKeyboardButton("🌍 Ивент", callback_data="adm_event")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_handlers(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    action = call.data.split("_")[1]
    
    if action == "stats":
        text = f"<b>📊 СТАТИСТИКА</b>\n👥 Игроков: {len(users)}\n💰 Монет: {sum(u.get('money',0) for u in users.values())}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    
    elif action == "money":
        bot.send_message(call.message.chat.id, "💰 /givemoney @username сумма")
    
    elif action == "item":
        bot.send_message(call.message.chat.id, "🎁 /giveitem @username item_key")
    
    elif action == "ban":
        bot.send_message(call.message.chat.id, "⛔ /ban @username причина")
    
    elif action == "bcast":
        bot.send_message(call.message.chat.id, "📢 /broadcast текст")
    
    elif action == "info":
        bot.send_message(call.message.chat.id, "👁 /userinfo @username")
    
    elif action == "tour":
        # Запуск турнира
        start_tournament()
        bot.answer_callback_query(call.id, "✅ Турнир запущен!")
    
    elif action == "event":
        # Создание ивента
        new_event = {
            "name": "🎉 Специальный ивент",
            "description": "Админский ивент! Удвоенный опыт!",
            "reward_money": 2000,
            "reward_ench": random.choice(ENCHANT_EFFECTS),
            "expires": (datetime.now() + timedelta(minutes=30)).isoformat()
        }
        events["current"] = new_event
        save_json(DATA_FILES['events'], events)
        bot.answer_callback_query(call.id, "✅ Ивент создан!")

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'broadcast', 'userinfo'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd in ["givemoney", "giveitem", "ban", "unban", "userinfo"]:
            username = parts[1].replace('@', '')
            
            # Поиск пользователя по username
            found_uid = None
            for uid, data in users.items():
                if data.get("username") == username:
                    found_uid = uid
                    break
            
            if not found_uid:
                bot.send_message(message.chat.id, "❌ Пользователь не найден!")
                return
            
            if cmd == "givemoney":
                amount = int(parts[2])
                p = Player(found_uid)
                p.data["money"] += amount
                p.save()
                bot.send_message(message.chat.id, f"✅ {amount}💰 → @{username}")
            
            elif cmd == "giveitem":
                ik = parts[2]
                p = Player(found_uid)
                p.data["inventory"].append(ik)
                p.save()
                bot.send_message(message.chat.id, f"✅ {ik} → @{username}")
            
            elif cmd == "ban":
                reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение"
                banned_users[found_uid] = {"reason": reason, "banned_at": datetime.now().isoformat()}
                save_json(DATA_FILES['bans'], banned_users)
                bot.send_message(message.chat.id, f"⛔ @{username} забанен!")
            
            elif cmd == "unban":
                if found_uid in banned_users:
                    del banned_users[found_uid]
                    save_json(DATA_FILES['bans'], banned_users)
                bot.send_message(message.chat.id, f"✅ @{username} разбанен!")
            
            elif cmd == "userinfo":
                p = Player(found_uid)
                d = p.data
                text = f"<b>👤 @{username}</b>\nИмя: {d['first_name']}\nУр.: {d['level']}\n💰 {d['money']}\n🏆 {d['wins']} побед"
                bot.send_message(message.chat.id, text)
        
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
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================
def check_level_up(player):
    level = player.data["level"]
    exp_needed = int(100 * (1.5 ** (level - 1)))
    
    leveled = False
    while player.data["exp"] >= exp_needed:
        player.data["exp"] -= exp_needed
        player.data["level"] += 1
        player.data["max_hp"] += 10
        player.data["max_mana"] += 5
        player.data["hp"] = player.data["max_hp"]
        player.data["mana"] = player.data["max_mana"]
        player.data["base_damage"] += 2
        
        titles = {5: "Боец", 10: "Воитель", 15: "Рыцарь", 20: "Ветеран",
                  25: "Мастер", 30: "Грандмастер", 40: "Герой", 50: "Легенда"}
        
        for req, title in titles.items():
            if player.data["level"] >= req and title not in player.data["titles_collected"]:
                player.data["titles_collected"].append(title)
                player.data["title"] = title
        
        level = player.data["level"]
        exp_needed = int(100 * (1.5 ** (level - 1)))
        leveled = True
    
    return leveled

@bot.message_handler(commands=['sell'])
def sell_item(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
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
        "seller_id": user_id,
        "seller_name": message.from_user.first_name,
        "item_key": ik,
        "price": price,
        "created_at": datetime.now().isoformat()
    }
    save_json(DATA_FILES['market'], market_listings)
    
    bot.send_message(message.chat.id, f"✅ {item.get('name', ik)} за {price}💰!")

# ==================== ЗАПУСК ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v11.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print("=" * 60)
    print("✅ Броня уменьшает урон")
    print("✅ Защита → Атака (пошагово)")
    print("✅ Навыки оружия с кулдаунами")
    print("✅ Данжи: 3 волны")
    print("✅ Турниры: сетка")
    print("✅ Ивенты: награды")
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
