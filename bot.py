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
import os

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = '8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE'
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
    'events': 'events.json',
    'bans': 'bans.json',
    'battle_history': 'battle_history.json',
    'matchmaking': 'matchmaking.json',
    'dungeon_bosses': 'dungeon_bosses.json',
    'active_tournaments': 'active_tournaments.json',
    'username_index': 'username_index.json'
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
    "leather_cap": {"name": "🎓 Кожаная шапка", "defense": 3, "price": 60, "type": "helmet", "slot": "head", "rarity": "common", "level_req": 1, "damage_reduction": 5},
    "iron_helmet": {"name": "⛑ Железный шлем", "defense": 8, "price": 250, "type": "helmet", "slot": "head", "rarity": "uncommon", "level_req": 6, "damage_reduction": 12},
    "dragon_helmet": {"name": "🐉 Шлем дракона", "defense": 18, "price": 2000, "type": "helmet", "slot": "head", "rarity": "epic", "level_req": 20, "damage_reduction": 25},
    "crown_of_wisdom": {"name": "👑 Корона мудрости", "defense": 12, "price": 3500, "type": "helmet", "slot": "head", "rarity": "legendary", "level_req": 28, "damage_reduction": 30}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "defense": 5, "price": 80, "type": "armor", "slot": "body", "rarity": "common", "level_req": 1, "damage_reduction": 8},
    "chainmail": {"name": "⛓ Кольчуга", "defense": 12, "price": 400, "type": "armor", "slot": "body", "rarity": "uncommon", "level_req": 8, "damage_reduction": 18},
    "plate_armor": {"name": "🛡 Латный доспех", "defense": 22, "price": 1500, "type": "armor", "slot": "body", "rarity": "rare", "level_req": 15, "damage_reduction": 30},
    "shadow_armor": {"name": "🌑 Теневая броня", "defense": 28, "price": 3500, "type": "armor", "slot": "body", "rarity": "epic", "level_req": 22, "damage_reduction": 35},
    "phoenix_armor": {"name": "🦅 Броня феникса", "defense": 40, "price": 8000, "type": "armor", "slot": "body", "rarity": "legendary", "level_req": 30, "damage_reduction": 45}
}

BOOTS = {
    "leather_boots": {"name": "👢 Кожаные сапоги", "defense": 2, "price": 100, "type": "boots", "slot": "legs", "rarity": "common", "level_req": 1, "damage_reduction": 3},
    "wind_boots": {"name": "🌪 Сапоги ветра", "defense": 4, "price": 900, "type": "boots", "slot": "legs", "rarity": "rare", "level_req": 12, "damage_reduction": 8},
    "blink_boots": {"name": "✨ Сапоги телепортации", "defense": 8, "price": 4000, "type": "boots", "slot": "legs", "rarity": "epic", "level_req": 25, "damage_reduction": 15},
    "hermes_boots": {"name": "👟 Сандалии Гермеса", "defense": 12, "price": 12000, "type": "boots", "slot": "legs", "rarity": "legendary", "level_req": 35, "damage_reduction": 20}
}

WEAPONS = {
    "rusty_sword": {"name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "rarity": "common", "level_req": 1, "skills": ["quick_strike", "slash"]},
    "hunters_bow": {"name": "🏹 Лук охотника", "damage": (7, 14), "price": 150, "type": "weapon", "rarity": "common", "level_req": 3, "skills": ["power_shot", "multi_shot"], "element": "nature"},
    "flame_blade": {"name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "rarity": "uncommon", "level_req": 7, "skills": ["fire_slash", "inferno_strike", "flame_wave"], "element": "fire"},
    "frost_axe": {"name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "rarity": "uncommon", "level_req": 10, "skills": ["frost_strike", "ice_shatter", "blizzard"], "element": "ice"},
    "storm_staff": {"name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500, "type": "weapon", "rarity": "rare", "level_req": 14, "skills": ["lightning_bolt", "thunder_storm", "chain_lightning"], "element": "lightning"},
    "tidal_blade": {"name": "🌊 Приливной клинок", "damage": (20, 32), "price": 2500, "type": "weapon", "rarity": "rare", "level_req": 18, "skills": ["water_slash", "tsunami", "drown"], "element": "water"},
    "shadow_dagger": {"name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "rarity": "epic", "level_req": 22, "skills": ["shadow_strike", "assassinate", "dark_veil", "soul_drain"], "element": "dark"},
    "divine_spear": {"name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "rarity": "legendary", "level_req": 28, "skills": ["holy_strike", "divine_judgment", "heavenly_light"], "element": "light"},
    "death_scythe": {"name": "💀 Коса смерти", "damage": (40, 65), "price": 12000, "type": "weapon", "rarity": "mythic", "level_req": 35, "skills": ["reap", "death_sentence", "soul_harvest"], "element": "dark"}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 200, "price": 350, "type": "potion", "rarity": "rare", "level_req": 15},
    "mana_potion": {"name": "💎 Зелье маны", "mana_restore": 60, "price": 60, "type": "potion", "rarity": "common", "level_req": 5}
}

LIMITED_ITEMS = {
    "thunderfury": {"name": "⚡ Ярость грома", "damage": (60, 95), "total": 3, "remaining": 3, "price": 50000, "type": "weapon", "rarity": "divine", "element": "lightning", "skills": ["thunder_gods_wrath", "eye_of_the_storm", "lightning_apocalypse"]},
    "immortal_helmet": {"name": "✨ Шлем бессмертия", "defense": 80, "total": 2, "remaining": 2, "price": 75000, "type": "helmet", "slot": "head", "rarity": "divine", "damage_reduction": 60},
    "cloak_of_infinity": {"name": "🌀 Плащ бесконечности", "defense": 60, "total": 4, "remaining": 4, "price": 60000, "type": "armor", "slot": "body", "rarity": "divine", "damage_reduction": 55}
}

ALL_ITEMS = {}
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(BOOTS)
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(POTIONS)

# ==================== НАВЫКИ С КУЛДАУНАМИ ====================
SKILLS_DB = {
    "quick_strike": {"name": "⚡ Быстрый удар", "damage_mult": 0.9, "mana_cost": 5, "cooldown": 1, "tier": 1},
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 8, "cooldown": 1, "tier": 1},
    "power_shot": {"name": "🎯 Мощный выстрел", "damage_mult": 1.8, "mana_cost": 15, "cooldown": 2, "tier": 2},
    "multi_shot": {"name": "🏹 Залп", "damage_mult": 0.7, "mana_cost": 20, "hits": 3, "cooldown": 2, "tier": 2},
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.5, "mana_cost": 18, "element": "fire", "burn_chance": 30, "cooldown": 2, "tier": 2},
    "inferno_strike": {"name": "🌋 Инферно удар", "damage_mult": 2.2, "mana_cost": 35, "element": "fire", "burn_chance": 60, "cooldown": 3, "tier": 3},
    "flame_wave": {"name": "🔥 Волна пламени", "damage_mult": 2.5, "mana_cost": 45, "element": "fire", "aoe": True, "cooldown": 4, "tier": 4},
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.4, "mana_cost": 16, "element": "ice", "freeze_chance": 25, "cooldown": 2, "tier": 2},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.0, "mana_cost": 30, "element": "ice", "freeze_chance": 50, "cooldown": 3, "tier": 3},
    "blizzard": {"name": "🌨 Метель", "damage_mult": 2.4, "mana_cost": 42, "element": "ice", "aoe": True, "cooldown": 4, "tier": 4},
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.6, "mana_cost": 20, "element": "lightning", "stun_chance": 20, "cooldown": 2, "tier": 2},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.3, "mana_cost": 40, "element": "lightning", "stun_chance": 35, "aoe": True, "cooldown": 4, "tier": 4},
    "chain_lightning": {"name": "⚡ Цепная молния", "damage_mult": 1.8, "mana_cost": 28, "element": "lightning", "cooldown": 3, "tier": 3},
    "water_slash": {"name": "🌊 Водяной разрез", "damage_mult": 1.3, "mana_cost": 15, "element": "water", "cooldown": 2, "tier": 2},
    "tsunami": {"name": "🌊 Цунами", "damage_mult": 2.1, "mana_cost": 38, "element": "water", "aoe": True, "cooldown": 4, "tier": 4},
    "drown": {"name": "💧 Утопление", "damage_mult": 1.9, "mana_cost": 32, "element": "water", "cooldown": 3, "tier": 3},
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.6, "mana_cost": 22, "element": "dark", "poison_chance": 25, "cooldown": 2, "tier": 2},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.2, "mana_cost": 55, "element": "dark", "cooldown": 4, "tier": 4},
    "soul_drain": {"name": "💀 Похищение души", "damage_mult": 2.0, "mana_cost": 35, "element": "dark", "life_steal": 0.4, "cooldown": 3, "tier": 3},
    "dark_veil": {"name": "🌑 Завеса тьмы", "defense_boost": 30, "mana_cost": 25, "element": "dark", "cooldown": 3, "tier": 3},
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.5, "mana_cost": 20, "element": "light", "cooldown": 2, "tier": 2},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 2.8, "mana_cost": 48, "element": "light", "cooldown": 4, "tier": 4},
    "heavenly_light": {"name": "🌟 Небесный свет", "hp_restore": 60, "mana_cost": 30, "element": "light", "cooldown": 3, "tier": 3},
    "reap": {"name": "💀 Жатва", "damage_mult": 2.5, "mana_cost": 42, "element": "dark", "life_steal": 0.3, "cooldown": 3, "tier": 3},
    "death_sentence": {"name": "☠ Смертный приговор", "damage_mult": 4.0, "mana_cost": 70, "element": "dark", "cooldown": 5, "tier": 5},
    "soul_harvest": {"name": "👻 Сбор душ", "damage_mult": 2.8, "mana_cost": 50, "element": "dark", "life_steal": 0.5, "cooldown": 4, "tier": 4},
    "thunder_gods_wrath": {"name": "⚡ Гнев бога грома", "damage_mult": 4.5, "mana_cost": 80, "element": "lightning", "stun_chance": 50, "cooldown": 5, "tier": 5},
    "eye_of_the_storm": {"name": "🌀 Глаз бури", "damage_mult": 3.0, "mana_cost": 55, "element": "lightning", "cooldown": 4, "tier": 4},
    "lightning_apocalypse": {"name": "⚡ Молниевый апокалипсис", "damage_mult": 5.0, "mana_cost": 90, "element": "lightning", "aoe": True, "cooldown": 6, "tier": 6}
}

# Загрузка данных
items = load_json(DATA_FILES['items'], ALL_ITEMS)
limited_items = load_json(DATA_FILES['limited'], LIMITED_ITEMS)
users = load_json(DATA_FILES['users'], {})
clans = load_json(DATA_FILES['clans'], {})
tournaments = load_json(DATA_FILES['tournaments'], {})
market_listings = load_json(DATA_FILES['market'], {})
events = load_json(DATA_FILES['events'], {})
banned_users = load_json(DATA_FILES['bans'], {})
battle_history_data = load_json(DATA_FILES['battle_history'], {})
matchmaking_queue = load_json(DATA_FILES['matchmaking'], {})
dungeon_bosses_data = load_json(DATA_FILES['dungeon_bosses'], {})
active_tournaments_data = load_json(DATA_FILES['active_tournaments'], {})
username_index = load_json(DATA_FILES['username_index'], {})

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
                "wins": 0, "losses": 0, "draws": 0,
                "win_streak": 0, "best_streak": 0,
                "total_duels": 0, "pvp_rating": 1000,
                "inventory": [],
                "equipment": {"weapon": None, "head": None, "body": None, "legs": None},
                "enchantments": {},
                "last_daily": None, "last_dungeon": None,
                "title": "Новичок",
                "titles_collected": ["Новичок"],
                "achievements": [],
                "clan": None, "clan_role": None,
                "registration_date": datetime.now().isoformat(),
                "settings": {"notifications": True, "duel_requests": True},
                "battle_history": [],
                "dungeons_completed": 0,
                "items_found": 0,
                "stat_points": 0
            }
            self.save()
        
        # Обновление username_index
        if username and username != "Unknown":
            username_index[username.lower()] = self.user_id
            save_json(DATA_FILES['username_index'], username_index)
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    def save(self):
        save_json(DATA_FILES['users'], users)
    
    def get_damage_reduction(self, part):
        """Получить снижение урона для части тела"""
        reduction = 0
        slot_map = {"head": "head", "body": "body", "legs": "legs"}
        slot = slot_map.get(part)
        
        if slot:
            ik = self.data["equipment"].get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                if item:
                    reduction = item.get("damage_reduction", 0)
            
            # Зачарования
            if ik:
                ench = self.data.get("enchantments", {}).get(ik, {})
                if ench.get("effect") == "defense_bonus":
                    reduction += ench.get("value", 0)
        
        return reduction
    
    def get_weapon_skills(self):
        """Получить навыки оружия"""
        ik = self.data["equipment"].get("weapon")
        if ik:
            item = items.get(ik) or limited_items.get(ik)
            if item and "skills" in item:
                return item["skills"]
        return ["quick_strike", "slash"]

def find_user_by_username(username):
    """Найти пользователя по username"""
    username = username.lower().replace('@', '')
    
    # Поиск в индексе
    if username in username_index:
        return username_index[username]
    
    # Поиск по всем пользователям
    for uid, data in users.items():
        if data.get("username", "").lower() == username:
            username_index[username] = uid
            save_json(DATA_FILES['username_index'], username_index)
            return uid
    
    return None

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
        self.max_turns = 30
        self.active = True
        self.winner = None
        self.log_p1 = []
        self.log_p2 = []
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        # Одинаковое HP для честного боя
        avg_hp = 120
        self.p1_hp = avg_hp
        self.p2_hp = avg_hp
        self.p1_max_hp = avg_hp
        self.p2_max_hp = avg_hp
        
        self.p1_mp = 60
        self.p2_mp = 60
        self.p1_max_mp = 60
        self.p2_max_mp = 60
        
        # Фазы поочерёдные
        self.p1_phase = "defend_select"
        self.p2_phase = "wait"
        
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Счётчик бездействия
        self.p1_inactivity = 0
        self.p2_inactivity = 0
        self.max_inactivity = 12
        
        # Арена
        self.arena = random.choice(["colosseum", "forest", "volcano", "tundra", "void", "temple"])
        self.weather = random.choice(["clear", "rain", "storm", "fog", "blizzard"])
        
        self.log_p1.append("⚔ Битва началась!")
        self.log_p2.append("⚔ Битва началась!")
    
    def get_player_name(self, num):
        return self.p1.data["first_name"] if num == 1 else self.p2.data["first_name"]
    
    def get_available_skills(self, player_num):
        player = self.p1 if player_num == 1 else self.p2
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        weapon_skills = player.get_weapon_skills()
        
        available = []
        for sid in weapon_skills:
            if sid in SKILLS_DB:
                cd = cooldowns.get(sid, 0)
                if cd <= 0:
                    available.append(sid)
        
        return available
    
    def set_defend(self, player_num, part):
        if player_num == 1:
            self.p1_defend = part
            self.p1_phase = "wait"
            self.p2_phase = "defend_select"
            self.p1_inactivity = 0
            msg = f"🛡 {self.get_player_name(1)} защищает {BODY_PARTS[part]['name']}"
            self.log_p1.append(msg)
            self.log_p2.append(msg)
        else:
            self.p2_defend = part
            self.p2_phase = "wait"
            self.p1_phase = "attack_select"
            self.p2_inactivity = 0
            msg = f"🛡 {self.get_player_name(2)} защищает {BODY_PARTS[part]['name']}"
            self.log_p1.append(msg)
            self.log_p2.append(msg)
        
        self._check_inactivity()
    
    def execute_attack(self, player_num, skill_id, target_part):
        if player_num == 1:
            self.p1_skill = skill_id
            self.p1_target = target_part
            self.p1_inactivity = 0
        else:
            self.p2_skill = skill_id
            self.p2_target = target_part
            self.p2_inactivity = 0
        
        # Выполняем атаку
        self._do_attack(player_num, 3 - player_num)
        
        # Смена фаз
        if player_num == 1:
            self.p2_phase = "attack_select"
            self.p1_phase = "defend_select"
        else:
            self.p1_phase = "attack_select"
            self.p2_phase = "defend_select"
        
        self.turn += 1
        
        if self.turn > self.max_turns:
            self.active = False
            self.winner = 0
        
        self._check_inactivity()
    
    def _do_attack(self, attacker, defender):
        skill_id = self.p1_skill if attacker == 1 else self.p2_skill
        target_part = self.p1_target if attacker == 1 else self.p2_target
        defend_part = self.p2_defend if attacker == 1 else self.p1_defend
        
        if not skill_id or not target_part:
            return
        
        skill = SKILLS_DB.get(skill_id, {"name": "Атака", "damage_mult": 1.0, "mana_cost": 0})
        
        # Мана
        mc = skill.get("mana_cost", 0)
        if attacker == 1:
            if self.p1_mp < mc:
                self.log_p1.append("❌ Недостаточно маны!")
                self.log_p2.append(f"❌ {self.get_player_name(1)} не хватает маны!")
                return
            self.p1_mp -= mc
        else:
            if self.p2_mp < mc:
                self.log_p2.append("❌ Недостаточно маны!")
                self.log_p1.append(f"❌ {self.get_player_name(2)} не хватает маны!")
                return
            self.p2_mp -= mc
        
        # Базовый урон
        attacker_player = self.p1 if attacker == 1 else self.p2
        weapon_ik = attacker_player.data["equipment"].get("weapon")
        min_d, max_d = 5, 10
        if weapon_ik:
            item = items.get(weapon_ik) or limited_items.get(weapon_ik)
            if item and "damage" in item:
                min_d, max_d = item["damage"]
        
        base_dmg = random.randint(min_d, max_d)
        dmg = int(base_dmg * skill.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_m = BODY_PARTS.get(target_part, {}).get("multiplier", 1.0)
        dmg = int(dmg * body_m)
        
        # Проверка защиты
        if defend_part == target_part:
            defender_player = self.p2 if attacker == 1 else self.p1
            reduction = defender_player.get_damage_reduction(target_part)
            
            if reduction > 0:
                reduced = int(dmg * (reduction / 100))
                dmg = max(1, dmg - reduced)
                
                msg = f"⚔ {self.get_player_name(attacker)} [{skill['name']}] → {BODY_PARTS[target_part]['name']}: <b>-{dmg} HP</b> (броня -{reduced})"
                self.log_p1.append(msg)
                self.log_p2.append(msg)
            else:
                msg = f"⚔ {self.get_player_name(attacker)} [{skill['name']}] → {BODY_PARTS[target_part]['name']}: <b>-{dmg} HP</b>"
                self.log_p1.append(msg)
                self.log_p2.append(msg)
        else:
            msg = f"⚔ {self.get_player_name(attacker)} [{skill['name']}] → {BODY_PARTS[target_part]['name']}: <b>-{dmg} HP</b> (незащищено!)"
            self.log_p1.append(msg)
            self.log_p2.append(msg)
        
        # Нанесение урона
        if defender == 1:
            self.p1_hp = max(0, self.p1_hp - dmg)
        else:
            self.p2_hp = max(0, self.p2_hp - dmg)
        
        # Восстановление маны
        if attacker == 1:
            self.p1_mp = min(self.p1_max_mp, self.p1_mp + 5)
        else:
            self.p2_mp = min(self.p2_max_mp, self.p2_mp + 5)
        
        # Кулдауны
        if "cooldown" in skill and skill["cooldown"] > 0:
            if attacker == 1:
                self.p1_cooldowns[skill_id] = skill["cooldown"]
            else:
                self.p2_cooldowns[skill_id] = skill["cooldown"]
        
        # Уменьшение кулдаунов
        cooldowns = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
        for sid in list(cooldowns.keys()):
            cooldowns[sid] -= 1
            if cooldowns[sid] <= 0:
                del cooldowns[sid]
        
        # Проверка смерти
        if self.p1_hp <= 0:
            self.active = False
            self.winner = 2
        elif self.p2_hp <= 0:
            self.active = False
            self.winner = 1
    
    def _check_inactivity(self):
        """Проверка бездействия"""
        if self.p1_phase == "defend_select" or self.p1_phase == "attack_select":
            self.p1_inactivity += 1
            if self.p1_inactivity >= self.max_inactivity:
                self.active = False
                self.winner = 2
                self.log_p1.append("⏰ Время вышло! Вы бездействовали слишком долго.")
                self.log_p2.append(f"⏰ {self.get_player_name(1)} бездействовал. Победа {self.get_player_name(2)}!")
                return
        
        if self.p2_phase == "defend_select" or self.p2_phase == "attack_select":
            self.p2_inactivity += 1
            if self.p2_inactivity >= self.max_inactivity:
                self.active = False
                self.winner = 1
                self.log_p2.append("⏰ Время вышло! Вы бездействовали слишком долго.")
                self.log_p1.append(f"⏰ {self.get_player_name(2)} бездействовал. Победа {self.get_player_name(1)}!")
                return
    
    def get_state_text(self, for_player_id):
        pn = 1 if str(for_player_id) == self.p1_id else 2
        phase = self.p1_phase if pn == 1 else self.p2_phase
        log = self.log_p1 if pn == 1 else self.log_p2
        
        p1_hp_pct = self.p1_hp / self.p1_max_hp * 100
        p2_hp_pct = self.p2_hp / self.p2_max_hp * 100
        
        def bar(pct, icon, cur, mx):
            f = int(pct / 10)
            e = 10 - f
            color = "🟢" if pct > 50 else "🟡" if pct > 25 else "🔴"
            return f"{icon} {color}[{'█'*f}{'░'*e}] {cur}/{mx}"
        
        arena_names = {"colosseum": "Колизей", "forest": "Лес", "volcano": "Вулкан", "tundra": "Тундра", "void": "Пустота", "temple": "Храм"}
        weather_names = {"clear": "Ясно", "rain": "Дождь", "storm": "Шторм", "fog": "Туман", "blizzard": "Буран"}
        
        text = f"""
<b>⚔ ДУЭЛЬ #{self.battle_id}</b>
━━━━━━━━━━━━━━━━━━━━
🏟 {arena_names.get(self.arena, self.arena)} | 🌤 {weather_names.get(self.weather, self.weather)}
Ход: <b>#{self.turn}</b> | Ставка: <b>{self.bet}💰</b>

<b>{self.get_player_name(1)}</b>
{bar(p1_hp_pct, '❤', self.p1_hp, self.p1_max_hp)}
💎 MP: {self.p1_mp}/{self.p1_max_mp}
🛡 Защита: {BODY_PARTS.get(self.p1_defend, {}).get('name', 'Не выбрана') if self.p1_defend else 'Не выбрана'}

<b>{self.get_player_name(2)}</b>
{bar(p2_hp_pct, '❤', self.p2_hp, self.p2_max_hp)}
💎 MP: {self.p2_mp}/{self.p2_max_mp}
🛡 Защита: {BODY_PARTS.get(self.p2_defend, {}).get('name', 'Не выбрана') if self.p2_defend else 'Не выбрана'}
━━━━━━━━━━━━━━━━━━━━
"""
        
        if phase == "defend_select":
            text += "\n🛡 <b>Выберите часть тела для защиты:</b>"
        elif phase == "attack_select":
            text += "\n🎯 <b>Выберите цель и навык атаки:</b>"
        elif phase == "wait":
            if self.p1_phase == "defend_select" or self.p2_phase == "defend_select":
                text += "\n⏳ <b>Противник выбирает защиту...</b>"
            else:
                text += "\n⏳ <b>Противник выбирает атаку...</b>"
        
        if log:
            text += f"\n\n<i>{log[-1][:120]}</i>"
        
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
<b>⚔️ ДУЭЛЬ БОТ v11.0 ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

🎯 <b>НОВОЕ:</b>
• Поочерёдные ходы: защита → атака
• Броня уменьшает урон (не даёт HP!)
• Бездействие → поражение
• Навыки оружия с кулдаунами
• Данжи с 3 боссами
• Турниры по олимпийской системе
• Ивенты с реальными наградами

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
        types.InlineKeyboardButton("🎯 Спарринг", callback_data="sparring_duel"),
        types.InlineKeyboardButton("⏱ Дуэль на время", callback_data="timed_duel")
    )
    
    bot.send_message(message.chat.id, "<b>⚔️ ДУЭЛИ</b>\n\nПоочерёдные ходы: защита → атака", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="hero_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="hero_inventory"),
        types.InlineKeyboardButton("👁 Экипировка", callback_data="hero_equipped"),
        types.InlineKeyboardButton("✨ Зачарования", callback_data="hero_enchantments"),
        types.InlineKeyboardButton("🏅 Достижения", callback_data="hero_achievements"),
        types.InlineKeyboardButton("📋 История", callback_data="hero_history"),
        types.InlineKeyboardButton("💊 Лечение", callback_data="hero_heal"),
        types.InlineKeyboardButton("📦 Передать", callback_data="hero_transfer_info")
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
        types.InlineKeyboardButton("💰 Мировой босс", callback_data="world_boss"),
        types.InlineKeyboardButton("📊 Топ", callback_data="world_top"),
        types.InlineKeyboardButton("ℹ Помощь", callback_data="world_help")
    )
    bot.send_message(message.chat.id, "<b>🌍 МИР</b>", reply_markup=markup)

# ==================== ДУЭЛИ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["quick_duel", "find_opponent", "ranked_duel", "hardcore_duel", "sparring_duel", "timed_duel"])
def duel_type_handler(call):
    dt = call.data
    
    bets = {"quick_duel": 50, "ranked_duel": 100, "hardcore_duel": 500, "sparring_duel": 0, "timed_duel": 100}
    
    if dt == "quick_duel":
        show_bet_menu(call, "quick")
    elif dt == "find_opponent":
        start_matchmaking(call, "quick", 50)
    else:
        bet = bets.get(dt, 100)
        start_matchmaking(call, dt, bet)

def show_bet_menu(call, duel_type):
    user_id = call.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    for bet in [50, 100, 200, 500, 1000]:
        markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"startduel_{duel_type}_{bet}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
    
    bot.edit_message_text(
        f"<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n\n💰 Баланс: <b>{player.data['money']}💰</b>\nВыберите ставку:",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_duels")
def back_to_duels(call):
    duel_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("startduel_"))
def start_duel_with_bet(call):
    parts = call.data.split("_")
    duel_type = parts[1]
    bet = int(parts[2])
    start_bot_duel(call.message.chat.id, call.message.message_id, call.from_user.id, duel_type, bet)

def start_bot_duel(chat_id, message_id, user_id, duel_type="quick", bet=50):
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.edit_message_text(f"❌ Недостаточно монет! Нужно {bet}💰", chat_id, message_id)
        return
    
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
        "hp": 100, "max_hp": 100, "mana": 60, "max_mana": 60,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000,
        "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Бот", "titles_collected": ["Бот"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0,
        "stat_points": 0
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
    
    bot.edit_message_text("⚔ Дуэль начинается! Ваш ход — выберите защиту.", chat_id, message_id)
    
    # Бот автоматически атакует (если его очередь)
    if duel.p2_phase == "attack_select":
        skills = duel.get_available_skills(2)
        if skills:
            duel.execute_attack(2, random.choice(skills), random.choice(list(BODY_PARTS.keys())))
    
    show_duel_interface(chat_id, message_id, duel, user_id)

def start_matchmaking(call, duel_type, bet):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.edit_message_text(f"❌ Недостаточно монет! Нужно {bet}💰", call.message.chat.id, call.message.message_id)
        return
    
    queue_key = f"queue_{duel_type}"
    queue = matchmaking_queue.get(queue_key, [])
    queue = [q for q in queue if q["user_id"] != user_id]
    
    if queue:
        opponent = queue.pop(0)
        matchmaking_queue[queue_key] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        if bet > 0:
            player.data["money"] -= bet
            opp = Player(opponent["user_id"])
            opp.data["money"] -= bet
            player.save()
            opp.save()
        
        duel = DuelInstance(opponent["user_id"], user_id, duel_type, bet)
        active_duels[user_id] = duel
        active_duels[opponent["user_id"]] = duel
        
        bot.edit_message_text("⚔ Соперник найден! Выберите защиту.", call.message.chat.id, call.message.message_id)
        
        # Отправляем сообщение противнику
        try:
            bot.send_message(int(opponent["user_id"]), "⚔ Соперник найден! Выберите защиту.", reply_markup=get_main_menu())
            show_duel_interface(opponent["user_id"], None, duel, opponent["user_id"])
        except:
            pass
        
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
    else:
        queue.append({"user_id": user_id, "type": duel_type, "bet": bet})
        matchmaking_queue[queue_key] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        threading.Timer(5.0, start_bot_duel_if_no_opponent, args=[call.message.chat.id, call.message.message_id, user_id, duel_type, bet]).start()
        bot.edit_message_text("🔍 Поиск соперника...", call.message.chat.id, call.message.message_id)

def start_bot_duel_if_no_opponent(chat_id, message_id, user_id, duel_type, bet):
    if str(user_id) not in active_duels:
        start_bot_duel(chat_id, message_id, user_id, duel_type, bet)

def show_duel_interface(chat_id, message_id, duel, user_id):
    """Показать интерфейс дуэли"""
    if not duel.active:
        finish_duel(chat_id, user_id, duel)
        return
    
    state_text = duel.get_state_text(user_id)
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    phase = duel.p1_phase if pn == 1 else duel.p2_phase
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if phase == "defend_select":
        for part, data in BODY_PARTS.items():
            p = Player(user_id)
            reduction = p.get_damage_reduction(part)
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']} (🛡{reduction}%)",
                callback_data=f"duel_defend_{part}"
            ))
    
    elif phase == "attack_select":
        markup.add(types.InlineKeyboardButton("🎯 В голову", callback_data="duel_target_head"))
        markup.add(types.InlineKeyboardButton("🎯 В тело", callback_data="duel_target_body"))
        markup.add(types.InlineKeyboardButton("🎯 В ноги", callback_data="duel_target_legs"))
    
    elif phase == "wait":
        markup.add(types.InlineKeyboardButton("⏳ Ожидание...", callback_data="duel_wait"))
    
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="duel_refresh"))
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="duel_surrender"))
    
    if message_id and chat_id:
        try:
            bot.edit_message_text(
                state_text[:4000],
                chat_id, message_id,
                reply_markup=markup
            )
        except Exception as e:
            print(f"Edit error: {e}")
    elif chat_id:
        bot.send_message(chat_id, state_text[:4000], reply_markup=markup)

target_selection = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_target_"))
def duel_target_selected(call):
    user_id = call.from_user.id
    part = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    target_selection[str(user_id)] = part
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    skills = duel.get_available_skills(pn)
    
    state_text = duel.get_state_text(user_id) + f"\n🎯 Цель: <b>{BODY_PARTS[part]['name']}</b>\n<b>Выберите навык:</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for sid in skills[:10]:
        skill = SKILLS_DB.get(sid, {})
        name = skill.get("name", sid)
        mana = skill.get("mana_cost", 0)
        dmg_mult = skill.get("damage_mult", 1.0)
        cd = skill.get("cooldown", 0)
        tier = skill.get("tier", 1)
        
        markup.add(types.InlineKeyboardButton(
            f"{name} x{dmg_mult} [{mana}MP] ⏱{cd}х",
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
                show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
                bot.answer_callback_query(call.id, "✅")
        
        elif action == "surrender":
            if duel and duel.active:
                duel.active = False
                duel.winner = 2 if str(user_id) == duel.p1_id else 1
                finish_duel(call.message.chat.id, user_id, duel)
    
    elif action.startswith("defend_"):
        part = action.split("_")[1]
        duel = active_duels.get(str(user_id))
        if duel and duel.active:
            pn = 1 if str(user_id) == duel.p1_id else 2
            duel.set_defend(pn, part)
            bot.answer_callback_query(call.id, f"🛡 {BODY_PARTS[part]['name']}")
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

def finish_duel(chat_id, user_id, duel):
    """Завершение дуэли и отправка результатов"""
    # Очистка
    for uid in [duel.p1_id, duel.p2_id]:
        if uid in active_duels and active_duels[uid].battle_id == duel.battle_id:
            del active_duels[uid]
    
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") and uid in users:
            del users[uid]
    save_json(DATA_FILES['users'], users)
    
    # Результат для игрока 1
    if duel.winner == 0:
        result_text = "<b>🤝 НИЧЬЯ!</b>\nХодов: " + str(duel.turn)
    elif duel.winner == 1:
        result_text = f"<b>🏆 ПОБЕДА!</b>\nВы победили {duel.get_player_name(2)}!\nХодов: {duel.turn}"
    else:
        result_text = f"<b>💀 ПОРАЖЕНИЕ</b>\n{duel.get_player_name(1)} победил!\nХодов: {duel.turn}"
    
    # Отправка результата игроку, нажавшему сдаться
    try:
        if chat_id and user_id:
            if message_id := None:  # Ищем message_id
                bot.edit_message_text(result_text, chat_id, message_id)
            else:
                bot.send_message(chat_id, result_text)
    except:
        pass
    
    # Отправка результата обоим игрокам
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_"):
            continue
        
        try:
            if str(uid) == str(user_id):
                continue  # Уже отправили
            
            if duel.winner == 0:
                r = "<b>🤝 НИЧЬЯ!</b>"
            elif (duel.winner == 1 and uid == duel.p1_id) or (duel.winner == 2 and uid == duel.p2_id):
                r = f"<b>🏆 ПОБЕДА!</b>\nВы победили!\nХодов: {duel.turn}"
            else:
                r = f"<b>💀 ПОРАЖЕНИЕ</b>\nПротивник победил!\nХодов: {duel.turn}"
            
            bot.send_message(int(uid), r)
        except:
            pass
    
    # Награды
    winner_id = None
    if duel.winner == 1:
        winner_id = duel.p1_id
    elif duel.winner == 2:
        winner_id = duel.p2_id
    
    if winner_id and not winner_id.startswith("bot_"):
        winner = Player(winner_id)
        if duel.bet > 0:
            winner.data["money"] += duel.bet * 2
        winner.data["wins"] += 1
        winner.data["win_streak"] += 1
        winner.data["total_duels"] += 1
        winner.data["pvp_rating"] += random.randint(20, 35)
        if winner.data["win_streak"] > winner.data["best_streak"]:
            winner.data["best_streak"] = winner.data["win_streak"]
        winner.data["exp"] += duel.turn * 10
        winner.data["total_exp"] += duel.turn * 10
        check_level_up(winner)
        winner.save()
    
    loser_id = duel.p2_id if winner_id == duel.p1_id else duel.p1_id
    if loser_id and not loser_id.startswith("bot_"):
        loser = Player(loser_id)
        loser.data["losses"] += 1
        loser.data["win_streak"] = 0
        loser.data["total_duels"] += 1
        loser.data["pvp_rating"] = max(0, loser.data["pvp_rating"] - random.randint(10, 25))
        loser.data["exp"] += duel.turn * 5
        loser.data["total_exp"] += duel.turn * 5
        check_level_up(loser)
        loser.save()

# ==================== ДАНЖИ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_dungeons")
def world_dungeons(call):
    dungeon_list = [
        {"name": "🐺 Логово волка", "level": 1, "bosses": ["Волк-страж", "Вожак стаи", "Древний волк"]},
        {"name": "🕷 Паучьи пещеры", "level": 5, "bosses": ["Паук-охотник", "Королева пауков", "Паучий lord"]},
        {"name": "💀 Катакомбы", "level": 10, "bosses": ["Скелет-воин", "Некромант", "Король мёртвых"]},
        {"name": "🐉 Драконье логово", "level": 15, "bosses": ["Драконий страж", "Молодой дракон", "Древний дракон"]},
        {"name": "👹 Бездна", "level": 25, "bosses": ["Демон", "Архидемон", "Владыка бездны"]}
    ]
    
    text = "<b>🏰 ПОДЗЕМЕЛЬЯ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for i, dung in enumerate(dungeon_list):
        text += f"<b>{dung['name']}</b> (Ур. {dung['level']}+)\n"
        text += f"Боссы: {', '.join(dung['bosses'])}\n\n"
        markup.add(types.InlineKeyboardButton(dung['name'], callback_data=f"dung_{i+1}"))
    
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
    
    # Создаём прогресс данжа
    dg_key = str(user_id)
    dungeon_progress[dg_key] = {
        "level": dl,
        "current_boss": 0,
        "bosses_defeated": 0,
        "total_bosses": 3,
        "reward_accumulated": 0,
        "exp_accumulated": 0,
        "active": True
    }
    save_json(DATA_FILES['dungeons'], dungeon_progress)
    
    start_dungeon_boss(call.message.chat.id, call.message.message_id, user_id)

def start_dungeon_boss(chat_id, message_id, user_id):
    dg_key = str(user_id)
    dg = dungeon_progress.get(dg_key, {})
    
    if not dg.get("active") or dg.get("current_boss", 0) >= dg.get("total_bosses", 3):
        # Данж завершён
        finish_dungeon(chat_id, message_id, user_id)
        return
    
    boss_num = dg["current_boss"] + 1
    boss_names = {
        1: ["Волк-страж", "Паук-охотник", "Скелет-воин", "Драконий страж", "Демон"],
        2: ["Вожак стаи", "Королева пауков", "Некромант", "Молодой дракон", "Архидемон"],
        3: ["Древний волк", "Паучий lord", "Король мёртвых", "Древний дракон", "Владыка бездны"]
    }
    
    dl = dg.get("level", 1)
    boss_name = boss_names.get(boss_num, ["Босс"] * 5)[dl - 1]
    boss_level = (dl * 5) + (boss_num * 3)
    
    # Создаём босса
    boss_id = f"boss_{random.randint(100000, 999999)}"
    
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    for slot, itype in [("head", "helmet"), ("body", "armor"), ("legs", "boots")]:
        sitems = [k for k, v in items.items() if v.get("type") == itype and v.get("level_req", 1) <= boss_level]
        if sitems and random.random() < 0.8:
            equip[slot] = random.choice(sitems)
    wpns = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= boss_level]
    if wpns:
        equip["weapon"] = random.choice(wpns)
    
    users[boss_id] = {
        "username": f"Boss_{boss_level}", "first_name": f"👹 {boss_name}",
        "money": 0, "level": boss_level, "exp": 0, "total_exp": 0,
        "hp": 100, "max_hp": 100, "mana": 60, "max_mana": 60,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000,
        "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Босс", "titles_collected": ["Босс"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0,
        "stat_points": 0
    }
    save_json(DATA_FILES['users'], users)
    
    duel = DuelInstance(user_id, boss_id, "dungeon", 0)
    active_duels[str(user_id)] = duel
    
    bot_def = random.choice(list(BODY_PARTS.keys()))
    duel.set_defend(2, bot_def)
    
    bot.edit_message_text(f"⚔ Босс #{boss_num}: <b>{boss_name}</b>!", chat_id, message_id)
    show_duel_interface(chat_id, message_id, duel, user_id)

def finish_dungeon(chat_id, message_id, user_id):
    dg_key = str(user_id)
    dg = dungeon_progress.get(dg_key, {})
    
    player = Player(user_id)
    reward = dg.get("reward_accumulated", 100)
    exp = dg.get("exp_accumulated", 50)
    
    player.data["money"] += reward
    player.data["exp"] += exp
    player.data["total_exp"] += exp
    player.data["dungeons_completed"] = player.data.get("dungeons_completed", 0) + 1
    
    if random.random() < 0.3:
        possible = [k for k, v in items.items() if v.get("level_req", 1) <= player.data["level"]]
        if possible:
            ik = random.choice(possible)
            player.data["inventory"].append(ik)
            player.data["items_found"] += 1
    
    check_level_up(player)
    player.save()
    
    del dungeon_progress[dg_key]
    save_json(DATA_FILES['dungeons'], dungeon_progress)
    
    text = f"<b>🏰 ДАНЖ ПРОЙДЕН!</b>\n💰 +{reward} | ✨ +{exp}"
    bot.edit_message_text(text, chat_id, message_id)

# Модифицируем finish_duel для данжей
original_finish_duel = finish_duel

def finish_duel_with_dungeon(chat_id, user_id, duel):
    if duel.duel_type == "dungeon":
        player_id = None
        if not duel.p1_id.startswith("boss_"):
            player_id = duel.p1_id
        elif not duel.p2_id.startswith("boss_"):
            player_id = duel.p2_id
        
        if player_id:
            dg_key = str(player_id)
            dg = dungeon_progress.get(dg_key, {})
            
            if duel.winner == 1 and not duel.p1_id.startswith("boss_"):
                dg["bosses_defeated"] = dg.get("bosses_defeated", 0) + 1
                dg["current_boss"] = dg.get("current_boss", 0) + 1
                dg["reward_accumulated"] = dg.get("reward_accumulated", 0) + random.randint(30, 100)
                dg["exp_accumulated"] = dg.get("exp_accumulated", 0) + random.randint(20, 60)
                dungeon_progress[dg_key] = dg
                save_json(DATA_FILES['dungeons'], dungeon_progress)
                
                # Следующий босс
                start_dungeon_boss(chat_id, None, player_id)
            else:
                # Поражение
                del dungeon_progress[dg_key]
                save_json(DATA_FILES['dungeons'], dungeon_progress)
                bot.send_message(chat_id, "<b>💀 ПОРАЖЕНИЕ В ДАНЖЕ</b>")
    else:
        original_finish_duel(chat_id, user_id, duel)

finish_duel = finish_duel_with_dungeon

# ==================== МИРОВОЙ БОСС ====================
world_boss_data = {"name": "🐉 Мировой дракон", "hp": 1000000, "max_hp": 1000000, "defeated": False}

@bot.callback_query_handler(func=lambda call: call.data == "world_boss")
def world_boss_menu(call):
    global world_boss_data
    
    text = f"""
<b>💰 МИРОВОЙ БОСС</b>

<b>{world_boss_data['name']}</b>
❤ HP: {world_boss_data['hp']:,} / {world_boss_data['max_hp']:,}
{'✅ ПОВЕРЖЕН!' if world_boss_data['defeated'] else '⚔ В атаку!'}

Награда за участие: 100-500💰
Последний удар: +1000💰
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if not world_boss_data['defeated']:
        markup.add(types.InlineKeyboardButton("⚔ Атаковать босса!", callback_data="attack_world_boss"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "attack_world_boss")
def attack_world_boss(call):
    global world_boss_data
    
    if world_boss_data['defeated']:
        bot.answer_callback_query(call.id, "Босс уже повержен!")
        return
    
    user_id = call.from_user.id
    player = Player(user_id)
    
    # Урон игрока
    weapon_ik = player.data["equipment"].get("weapon")
    min_d, max_d = 5, 10
    if weapon_ik:
        item = items.get(weapon_ik) or limited_items.get(weapon_ik)
        if item and "damage" in item:
            min_d, max_d = item["damage"]
    
    damage = random.randint(min_d, max_d)
    world_boss_data['hp'] -= damage
    
    reward = random.randint(10, 50)
    player.data["money"] += reward
    player.save()
    
    if world_boss_data['hp'] <= 0:
        world_boss_data['hp'] = 0
        world_boss_data['defeated'] = True
        player.data["money"] += 1000
        player.save()
        
        bot.edit_message_text(
            f"<b>🎉 БОСС ПОВЕРЖЕН!</b>\n\nВы нанесли {damage} урона!\n💰 +{reward} (+1000 за последний удар!)",
            call.message.chat.id, call.message.message_id
        )
    else:
        bot.edit_message_text(
            f"<b>⚔ АТАКА!</b>\n\nВы нанесли <b>{damage}</b> урона!\n❤ HP босса: {world_boss_data['hp']:,}/{world_boss_data['max_hp']:,}\n💰 +{reward}",
            call.message.chat.id, call.message.message_id
        )
    
    # Сброс босса через час
    if world_boss_data['defeated']:
        threading.Timer(3600, reset_world_boss).start()

def reset_world_boss():
    global world_boss_data
    world_boss_data = {"name": "🐉 Мировой дракон", "hp": 1000000, "max_hp": 1000000, "defeated": False}

# ==================== ТУРНИРЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_tournaments")
def world_tournaments(call):
    active_tour = active_tournaments_data.get("current")
    
    if not active_tour:
        text = "<b>🏟 ТУРНИРЫ</b>\n\nНет активных турниров.\nСоздать: /createtournament [имя] [взнос]"
    else:
        text = f"""
<b>🏟 ТУРНИР: {active_tour['name']}</b>

Статус: {active_tour.get('status', 'registration')}
Участников: {len(active_tour.get('participants', []))}/{active_tour.get('max_participants', 16)}
Призовой фонд: <b>{active_tour.get('prize_pool', 0)}💰</b>
Взнос: {active_tour.get('entry_fee', 500)}💰
"""
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    if active_tour and active_tour.get('status') == 'registration':
        markup.add(types.InlineKeyboardButton("🏆 Участвовать", callback_data="tour_join"))
    markup.add(types.InlineKeyboardButton("📋 Участники", callback_data="tour_list"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "tour_join")
def tour_join(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    active_tour = active_tournaments_data.get("current")
    if not active_tour:
        bot.answer_callback_query(call.id, "❌ Нет активных турниров!")
        return
    
    entry_fee = active_tour.get("entry_fee", 500)
    if player.data["money"] < entry_fee:
        bot.answer_callback_query(call.id, f"❌ Нужно {entry_fee}💰!")
        return
    
    participants = active_tour.get("participants", [])
    if str(user_id) in participants:
        bot.answer_callback_query(call.id, "❌ Уже участвуете!")
        return
    
    if len(participants) >= active_tour.get("max_participants", 16):
        bot.answer_callback_query(call.id, "❌ Заполнен!")
        return
    
    player.data["money"] -= entry_fee
    player.save()
    
    participants.append(str(user_id))
    active_tour["participants"] = participants
    active_tour["prize_pool"] = active_tour.get("prize_pool", 0) + entry_fee
    active_tournaments_data["current"] = active_tour
    save_json(DATA_FILES['active_tournaments'], active_tournaments_data)
    
    bot.answer_callback_query(call.id, "✅ Зарегистрированы!")
    world_tournaments(call)

@bot.callback_query_handler(func=lambda call: call.data == "tour_list")
def tour_list(call):
    active_tour = active_tournaments_data.get("current", {})
    participants = active_tour.get("participants", [])
    
    if not participants:
        bot.answer_callback_query(call.id, "📋 Пусто")
        return
    
    text = "<b>📋 УЧАСТНИКИ</b>\n\n"
    for i, uid in enumerate(participants[:16], 1):
        p = Player(uid)
        text += f"{i}. {p.data['first_name']} (Lv.{p.data['level']})\n"
    
    bot.send_message(call.message.chat.id, text)

@bot.message_handler(commands=['createtournament'])
def create_tournament_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ /createtournament [имя] [взнос]")
        return
    
    name = parts[1]
    entry_fee = int(parts[2]) if len(parts) > 2 else 500
    
    active_tournaments_data["current"] = {
        "name": name,
        "entry_fee": entry_fee,
        "prize_pool": 0,
        "participants": [],
        "max_participants": 16,
        "status": "registration",
        "created_at": datetime.now().isoformat()
    }
    save_json(DATA_FILES['active_tournaments'], active_tournaments_data)
    
    bot.send_message(message.chat.id, f"✅ Турнир <b>{name}</b> создан! Взнос: {entry_fee}💰")

@bot.message_handler(commands=['starttournament'])
def start_tournament_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    active_tour = active_tournaments_data.get("current")
    if not active_tour:
        bot.send_message(message.chat.id, "❌ Нет турнира!")
        return
    
    participants = active_tour.get("participants", [])
    if len(participants) < 2:
        bot.send_message(message.chat.id, "❌ Мало участников!")
        return
    
    active_tour["status"] = "in_progress"
    active_tour["round"] = 1
    active_tour["matches"] = []
    
    # Перемешиваем и создаём пары
    random.shuffle(participants)
    for i in range(0, len(participants), 2):
        if i + 1 < len(participants):
            active_tour["matches"].append({
                "p1": participants[i],
                "p2": participants[i + 1],
                "winner": None
            })
    
    active_tournaments_data["current"] = active_tour
    save_json(DATA_FILES['active_tournaments'], active_tournaments_data)
    
    # Уведомление участников
    for uid in participants:
        try:
            bot.send_message(int(uid), f"🏟 Турнир <b>{active_tour['name']}</b> начался! Ожидайте соперника.")
        except:
            pass
    
    bot.send_message(message.chat.id, f"✅ Турнир начат! Участников: {len(participants)}")

# ==================== ИВЕНТЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_events")
def world_events(call):
    current_event = events.get("current")
    
    if not current_event or datetime.fromisoformat(current_event.get("expires", "2000-01-01")) < datetime.now():
        # Создаём новый ивент
        event_types = [
            {"name": "🌋 Извержение вулкана", "description": "Двойной опыт за дуэли!", "reward_type": "exp_boost", "value": 2},
            {"name": "❄ Ледяной шторм", "description": "Шанс получить зачарование!", "reward_type": "enchant_chance", "value": 30},
            {"name": "⚡ Грозовой фронт", "description": "Удвоенные монеты!", "reward_type": "money_boost", "value": 2},
            {"name": "🌑 Затмение", "description": "Редкие предметы в данжах!", "reward_type": "rare_drop", "value": 50},
            {"name": "✨ Звёздный дождь", "description": "Бесплатные зачарования!", "reward_type": "free_enchant", "value": 1}
        ]
        
        current_event = random.choice(event_types)
        current_event["expires"] = (datetime.now() + timedelta(minutes=10)).isoformat()
        events["current"] = current_event
        save_json(DATA_FILES['events'], events)
        
        # Рассылка ивента
        for uid in users:
            try:
                if users[uid].get("settings", {}).get("notifications", True):
                    bot.send_message(int(uid), f"🌍 <b>НОВЫЙ ИВЕНТ!</b>\n\n{current_event['name']}\n{current_event['description']}\n⏰ 10 минут!")
            except:
                pass
    
    time_left = datetime.fromisoformat(current_event["expires"]) - datetime.now()
    minutes_left = max(0, time_left.seconds // 60)
    
    text = f"""
<b>🌍 ТЕКУЩИЙ ИВЕНТ</b>

<b>{current_event['name']}</b>
📝 {current_event['description']}
⏰ Осталось: {minutes_left} мин.
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

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
        else:
            s = f"🛡 -{item.get('damage_reduction', 0)}% урона"
        
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

# ==================== ОСТАЛЬНЫЕ ОБРАБОТЧИКИ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["trade_limited", "trade_daily", "trade_market", "trade_sell", "trade_my_lots", "back_to_trade"])
def trade_handlers(call):
    if call.data == "trade_limited":
        if not limited_items:
            bot.edit_message_text("💎 Нет лимитированных", call.message.chat.id, call.message.message_id)
            return
        text = "<b>💎 ЛИМИТИРОВАННЫЕ</b>\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for ik, item in limited_items.items():
            if item["remaining"] > 0:
                pct = "█" * int(item["remaining"] / item["total"] * 10)
                emp = "░" * (10 - len(pct))
                text += f"<b>{item['name']}</b>\n[{pct}{emp}] {item['remaining']}/{item['total']}\n💰 {item['price']}💰\n\n"
                markup.add(types.InlineKeyboardButton(f"Купить - {item['price']}💰", callback_data=f"buyitem_{ik}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "trade_daily":
        user_id = call.from_user.id
        player = Player(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        if player.data.get("last_daily") == today:
            bot.answer_callback_query(call.id, "❌ Уже получен!")
            return
        bonus = random.randint(150, 600)
        exp = random.randint(80, 250)
        player.data["money"] += bonus
        player.data["exp"] += exp
        player.data["total_exp"] += exp
        player.data["last_daily"] = today
        check_level_up(player)
        player.save()
        bot.edit_message_text(f"<b>🎁 БОНУС</b>\n💰 +{bonus}\n✨ +{exp}", call.message.chat.id, call.message.message_id)
    
    elif call.data == "trade_market":
        if not market_listings:
            bot.edit_message_text("📦 Рынок пуст", call.message.chat.id, call.message.message_id)
            return
        text = "<b>💱 РЫНОК</b>\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for lid, listing in list(market_listings.items())[:10]:
            item = items.get(listing["item_key"]) or limited_items.get(listing["item_key"])
            if item:
                text += f"📦 {item['name']} — <b>{listing['price']}💰</b>\n\n"
                markup.add(types.InlineKeyboardButton(f"Купить: {item['name']}", callback_data=f"mktbuy_{lid}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "trade_sell":
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
    
    bot.answer_callback_query(call.id, "✅ Куплено!")
    trade_handlers(call)

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
@bot.callback_query_handler(func=lambda call: call.data in ["hero_stats", "hero_inventory", "hero_equipped", "hero_enchantments", "hero_achievements", "hero_history", "hero_heal", "hero_transfer_info", "back_to_hero"])
def hero_handlers(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "hero_stats":
        s = player.get_damage_reduction("head")
        d = player.data
        wr = (d["wins"] / d["total_duels"] * 100) if d["total_duels"] > 0 else 0
        text = f"""
<b>📊 СТАТИСТИКА</b>
<b>{d['first_name']}</b> | {d['title']}
⭐ Ур.{d['level']} | 📊 {d['pvp_rating']}
💰 {d['money']}💰
🏆 Побед: {d['wins']} | 💀 Поражений: {d['losses']}
📈 Винрейт: {wr:.1f}%
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_inventory":
        if not player.data["inventory"]:
            bot.edit_message_text("🎒 Пусто", call.message.chat.id, call.message.message_id)
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
            text += f"{idx}. {r} {item['name']} x{cnt}\n"
            if item.get("type") in ["weapon", "helmet", "armor", "boots"]:
                markup.add(types.InlineKeyboardButton(f"Экипировать: {item['name']}", callback_data=f"equip_{ik}"))
                markup.add(types.InlineKeyboardButton(f"Зачаровать: {item['name']}", callback_data=f"enchant_{ik}"))
            elif item.get("type") == "potion":
                markup.add(types.InlineKeyboardButton(f"Использовать: {item['name']}", callback_data=f"use_{ik}"))
            idx += 1
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_equipped":
        equip = player.data["equipment"]
        text = "<b>👁 ЭКИПИРОВКА</b>\n\n"
        sn = {"weapon": "⚔ Оружие", "head": "👤 Голова", "body": "🦾 Тело", "legs": "🦿 Ноги"}
        for slot, name in sn.items():
            ik = equip.get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                if item:
                    text += f"{name}: <b>{item['name']}</b> (🛡-{item.get('damage_reduction', 0)}%)\n"
            else:
                text += f"{name}: ❌\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔴 Снять всё", callback_data="unequip_all"))
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
    
    elif call.data == "hero_achievements":
        ach = [
            ("first_blood", "🩸 Первая кровь", "1 победа", player.data["wins"] >= 1),
            ("warrior", "⚔ Воин", "10 побед", player.data["wins"] >= 10),
            ("veteran", "🎖 Ветеран", "50 побед", player.data["wins"] >= 50),
            ("rich", "💰 Богач", "10000 монет", player.data["money"] >= 10000),
            ("dmaster", "🏰 Мастер данжей", "10 данжей", player.data.get("dungeons_completed", 0) >= 10)
        ]
        text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(player.data['achievements'])}/5)\n\n"
        for aid, name, desc, cond in ach:
            done = aid in player.data["achievements"] or cond
            text += f"{'✅' if done else '🔒'} <b>{name}</b>: {desc}\n"
            if cond and aid not in player.data["achievements"]:
                player.data["achievements"].append(aid)
        player.save()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_history":
        history = player.data.get("battle_history", [])
        if not history:
            bot.edit_message_text("📋 Пусто", call.message.chat.id, call.message.message_id)
            return
        text = "<b>📋 ИСТОРИЯ</b>\n\n"
        for b in history[-10:]:
            icon = "🏆" if b.get("result") == "win" else "💀"
            text += f"{icon} vs {b.get('opponent', 'Нет')}\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_heal":
        stats = player.get_full_stats() if hasattr(player, 'get_full_stats') else {"max_hp": 100}
        potions = [k for k in player.data["inventory"] if items.get(k, {}).get("type") == "potion" and items.get(k, {}).get("heal", 0) > 0]
        if not potions:
            bot.edit_message_text("💊 Нет зелий!", call.message.chat.id, call.message.message_id)
            return
        pk = potions[0]
        potion = items[pk]
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + potion["heal"])
        player.data["inventory"].remove(pk)
        player.save()
        bot.edit_message_text(f"💊 <b>{potion['name']}</b>\n❤ HP: {player.data['hp']}/{player.data['max_hp']}", call.message.chat.id, call.message.message_id)
    
    elif call.data == "hero_transfer_info":
        bot.edit_message_text("📦 /transfer [номер] (ответьте на сообщение)", call.message.chat.id, call.message.message_id)
    
    elif call.data == "back_to_hero":
        hero_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
def equip_item_handler(call):
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
        bot.answer_callback_query(call.id, "❌ Нельзя!")
        return
    
    old = player.data["equipment"][slot]
    if old:
        player.data["inventory"].append(old)
    
    player.data["equipment"][slot] = ik
    player.data["inventory"].remove(ik)
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ {item['name']}!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("enchant_"))
def enchant_handler(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(ik) or limited_items.get(ik)
    if not item:
        bot.answer_callback_query(call.id, "❌ Нельзя!")
        return
    
    if ik not in player.data["inventory"] and ik not in player.data["equipment"].values():
        bot.answer_callback_query(call.id, "❌ Не у вас!")
        return
    
    cost = item.get("price", 100) // 2
    if player.data["money"] < cost:
        bot.answer_callback_query(call.id, f"❌ {cost}💰!")
        return
    
    player.data["money"] -= cost
    ench = random.choice(ENCHANT_EFFECTS)
    player.data.setdefault("enchantments", {})[ik] = {"name": ench["name"], "effect": ench["effect"], "value": ench["value"]}
    player.save()
    bot.answer_callback_query(call.id, f"✨ {ench['name']}!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("use_"))
def use_potion_handler(call):
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
    
    if "heal" in item:
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + item["heal"])
    if "mana_restore" in item:
        player.data["mana"] = min(player.data["max_mana"], player.data["mana"] + item["mana_restore"])
    
    player.data["inventory"].remove(ik)
    player.save()
    bot.answer_callback_query(call.id, "✅ Использовано!")

@bot.callback_query_handler(func=lambda call: call.data == "unequip_all")
def unequip_all_handler(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    for slot in ["weapon", "head", "body", "legs"]:
        ik = player.data["equipment"][slot]
        if ik:
            player.data["inventory"].append(ik)
            player.data["equipment"][slot] = None
    
    player.save()
    bot.answer_callback_query(call.id, "✅ Снято!")

# ==================== МИР ====================
@bot.callback_query_handler(func=lambda call: call.data in ["world_clans", "world_top", "world_help", "back_to_world"])
def world_other_handlers(call):
    if call.data == "world_clans":
        user_id = call.from_user.id
        player = Player(user_id)
        if player.data.get("clan"):
            clan = clans.get(player.data["clan"], {})
            text = f"<b>🛡 {player.data['clan']}</b>\n👥 {len(clan.get('members', []))} уч."
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave"))
        else:
            text = "<b>🛡 КЛАНЫ</b>\n/createclan [имя]\n/joinclan [имя]"
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("📋 Список", callback_data="clan_list"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "world_top":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("⭐ Уровень", callback_data="top_level"),
            types.InlineKeyboardButton("⚔ Победы", callback_data="top_wins"),
            types.InlineKeyboardButton("💰 Монеты", callback_data="top_money"),
            types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world")
        )
        bot.edit_message_text("<b>📊 ТОП</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "world_help":
        text = "<b>ℹ ПОМОЩЬ</b>\n⚔ /duel\n🛒 /shop\n📦 /sell"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "back_to_world":
        world_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def show_top(call):
    cat = call.data.split("_")[1]
    if cat == "level":
        su = sorted(users.items(), key=lambda x: x[1].get("level", 1), reverse=True)[:10]
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
        val = f"Ур.{data.get('level', 1)}" if cat == "level" else f"{data.get('wins', 0)} побед" if cat == "wins" else f"{data.get('money', 0)}💰"
        text += f"{medals[i]} {data.get('first_name', 'Игрок')}: {val}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_top"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== КЛАНЫ ====================
@bot.message_handler(commands=['createclan', 'joinclan'])
def clan_cmds(message):
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
        clans[name] = {"leader_id": user_id, "leader_name": message.from_user.first_name, "members": [message.from_user.first_name], "treasury": 0}
        save_json(DATA_FILES['clans'], clans)
        bot.send_message(message.chat.id, f"✅ Клан <b>{name}</b>!")
    
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
        bot.send_message(message.chat.id, f"✅ В <b>{name}</b>!")

# ==================== ОБЩИЕ КОМАНДЫ ====================
@bot.message_handler(commands=['sell', 'transfer'])
def misc_cmds(message):
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
        market_listings[lid] = {"seller_id": user_id, "seller_name": message.from_user.first_name, "item_key": ik, "price": price, "created_at": datetime.now().isoformat()}
        save_json(DATA_FILES['market'], market_listings)
        bot.send_message(message.chat.id, f"✅ {item.get('name', ik)} за {price}💰!")
    
    elif cmd == "transfer":
        if not message.reply_to_message:
            bot.send_message(message.chat.id, "❌ Ответьте!")
            return
        target_id = message.reply_to_message.from_user.id
        try:
            idx = int(message.text.split()[1]) - 1
        except:
            bot.send_message(message.chat.id, "❌ /transfer [номер]")
            return
        if idx < 0 or idx >= len(player.data["inventory"]):
            bot.send_message(message.chat.id, "❌ Неверный!")
            return
        ik = player.data["inventory"].pop(idx)
        target = Player(target_id)
        target.data["inventory"].append(ik)
        player.save()
        target.save()
        item = items.get(ik) or limited_items.get(ik)
        bot.send_message(message.chat.id, f"✅ {item.get('name', ik)}!")

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
        types.InlineKeyboardButton("✅ Разбан", callback_data="admin_unban"),
        types.InlineKeyboardButton("🏟 Турнир", callback_data="admin_tournament"),
        types.InlineKeyboardButton("🐉 Босс", callback_data="admin_boss")
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
    elif call.data == "admin_tournament":
        bot.send_message(call.message.chat.id, "🏟 /createtournament [имя] [взнос]\n/starttournament")
    elif call.data == "admin_boss":
        bot.send_message(call.message.chat.id, "🐉 /resetworldboss")

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'broadcast', 'resetdaily', 'userinfo', 'resetworldboss'])
def admin_cmds(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd == "givemoney":
            username = parts[1].replace('@', '').lower()
            amount = int(parts[2])
            uid = find_user_by_username(username)
            if uid:
                p = Player(uid)
                p.data["money"] += amount
                p.save()
                bot.send_message(message.chat.id, f"✅ {amount}💰 → @{username}")
            else:
                bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "giveitem":
            username = parts[1].replace('@', '').lower()
            ik = parts[2]
            uid = find_user_by_username(username)
            if uid:
                p = Player(uid)
                p.data["inventory"].append(ik)
                p.save()
                bot.send_message(message.chat.id, f"✅ {ik} → @{username}")
            else:
                bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "ban":
            username = parts[1].replace('@', '').lower()
            reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение"
            uid = find_user_by_username(username)
            if uid:
                banned_users[uid] = {"reason": reason, "banned_at": datetime.now().isoformat()}
                save_json(DATA_FILES['bans'], banned_users)
                bot.send_message(message.chat.id, f"⛔ @{username} забанен!")
            else:
                bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "unban":
            username = parts[1].replace('@', '').lower()
            uid = find_user_by_username(username)
            if uid and uid in banned_users:
                del banned_users[uid]
                save_json(DATA_FILES['bans'], banned_users)
                bot.send_message(message.chat.id, f"✅ @{username} разбанен!")
            else:
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
            username = parts[1].replace('@', '').lower()
            uid = find_user_by_username(username)
            if uid:
                p = Player(uid)
                p.data["last_daily"] = None
                p.data["last_dungeon"] = None
                p.save()
                bot.send_message(message.chat.id, f"✅ @{username}")
            else:
                bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "userinfo":
            username = parts[1].replace('@', '').lower()
            uid = find_user_by_username(username)
            if uid:
                p = Player(uid)
                d = p.data
                text = f"<b>👤 @{username}</b>\nИмя: {d['first_name']}\nУр.: {d['level']}\n💰 {d['money']}\nРейтинг: {d['pvp_rating']}"
                bot.send_message(message.chat.id, text)
            else:
                bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "resetworldboss":
            global world_boss_data
            world_boss_data = {"name": "🐉 Мировой дракон", "hp": 1000000, "max_hp": 1000000, "defeated": False}
            bot.send_message(message.chat.id, "✅ Мировой босс сброшен!")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================
def check_level_up(player):
    level = player.data["level"]
    exp_needed = int(100 * (1.5 ** (level - 1)))
    
    while player.data["exp"] >= exp_needed:
        player.data["exp"] -= exp_needed
        player.data["level"] += 1
        player.data["stat_points"] += 3
        player.data["max_hp"] += 10
        player.data["max_mana"] += 5
        player.data["hp"] = player.data["max_hp"]
        player.data["mana"] = player.data["max_mana"]
        
        titles = {5: "Боец", 10: "Воитель", 15: "Рыцарь", 20: "Ветеран",
                  25: "Мастер", 30: "Грандмастер", 40: "Герой", 50: "Легенда"}
        
        for req, title in titles.items():
            if player.data["level"] >= req and title not in player.data["titles_collected"]:
                player.data["titles_collected"].append(title)
                player.data["title"] = title
        
        level = player.data["level"]
        exp_needed = int(100 * (1.5 ** (level - 1)))

# ==================== ЗАПУСК ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v11.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print("=" * 60)
    print("✅ Поочерёдные ходы: защита → атака")
    print("✅ Броня уменьшает урон (не даёт HP)")
    print("✅ Навыки с кулдаунами")
    print("✅ Данжи с 3 боссами")
    print("✅ Мировой босс")
    print("✅ Турниры по олимпийской системе")
    print("✅ Ивенты с реальными наградами")
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
