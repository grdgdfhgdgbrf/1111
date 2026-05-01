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
    'dungeons': 'dungeons.json',
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
    "rusty_sword": {"name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 1, "skills": ["slash", "quick_strike", "heavy_slash"], "enchantable": True},
    "hunters_bow": {"name": "🏹 Лук охотника", "damage": (7, 14), "price": 150, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 3, "skills": ["power_shot", "multi_shot", "aimed_shot"], "enchantable": True, "element": "nature"},
    "flame_blade": {"name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 7, "skills": ["fire_slash", "inferno_strike", "flame_wave"], "enchantable": True, "element": "fire"},
    "frost_axe": {"name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 10, "skills": ["frost_strike", "ice_shatter", "blizzard"], "enchantable": True, "element": "ice"},
    "storm_staff": {"name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500, "type": "weapon", "slot": "weapon", "rarity": "rare", "level_req": 14, "skills": ["lightning_bolt", "thunder_storm", "chain_lightning", "static_field"], "enchantable": True, "element": "lightning"},
    "tidal_blade": {"name": "🌊 Приливной клинок", "damage": (20, 32), "price": 2500, "type": "weapon", "slot": "weapon", "rarity": "rare", "level_req": 18, "skills": ["water_slash", "tsunami", "drown", "healing_wave"], "enchantable": True, "element": "water"},
    "shadow_dagger": {"name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "slot": "weapon", "rarity": "epic", "level_req": 22, "skills": ["shadow_strike", "assassinate", "dark_veil", "soul_drain"], "enchantable": True, "element": "dark"},
    "divine_spear": {"name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "slot": "weapon", "rarity": "legendary", "level_req": 28, "skills": ["holy_strike", "divine_judgment", "heavenly_light", "purification"], "enchantable": True, "element": "light"},
    "death_scythe": {"name": "💀 Коса смерти", "damage": (40, 65), "price": 12000, "type": "weapon", "slot": "weapon", "rarity": "mythic", "level_req": 35, "skills": ["reap", "death_sentence", "soul_harvest", "darkness_falls"], "enchantable": True, "element": "dark"}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 200, "price": 350, "type": "potion", "rarity": "rare", "level_req": 15},
    "mana_potion": {"name": "💎 Зелье маны", "mana_restore": 60, "price": 60, "type": "potion", "rarity": "common", "level_req": 5}
}

LIMITED_ITEMS = {
    "thunderfury": {"name": "⚡ Ярость грома", "damage": (60, 95), "total": 3, "remaining": 3, "price": 50000, "type": "weapon", "slot": "weapon", "rarity": "divine", "element": "lightning", "skills": ["thunder_gods_wrath", "eye_of_the_storm", "lightning_apocalypse", "zeus_fury"], "enchantable": True},
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
    "quick_strike": {"name": "⚡ Быстрый удар", "damage_mult": 0.8, "mana_cost": 5, "cooldown": 0, "hits": 2, "category": "basic"},
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 10, "cooldown": 1, "category": "basic"},
    "heavy_slash": {"name": "💪 Тяжёлый разрез", "damage_mult": 1.8, "mana_cost": 20, "cooldown": 2, "category": "heavy"},
    "defend": {"name": "🛡 Защита", "defense_boost": 30, "mana_cost": 5, "cooldown": 0, "category": "defense"},
    "power_shot": {"name": "🎯 Мощный выстрел", "damage_mult": 1.8, "mana_cost": 18, "cooldown": 1, "category": "heavy"},
    "multi_shot": {"name": "🏹 Залп", "damage_mult": 0.7, "mana_cost": 22, "hits": 3, "cooldown": 2, "category": "heavy"},
    "aimed_shot": {"name": "👁 Прицельный выстрел", "damage_mult": 2.5, "mana_cost": 35, "cooldown": 3, "crit_boost": 30, "category": "ultimate"},
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.5, "mana_cost": 18, "element": "fire", "burn_chance": 30, "cooldown": 1, "category": "elemental"},
    "inferno_strike": {"name": "🌋 Инферно удар", "damage_mult": 2.2, "mana_cost": 38, "element": "fire", "burn_chance": 60, "cooldown": 3, "category": "heavy"},
    "flame_wave": {"name": "🔥 Волна пламени", "damage_mult": 2.8, "mana_cost": 50, "element": "fire", "burn_chance": 40, "cooldown": 4, "category": "ultimate"},
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.4, "mana_cost": 16, "element": "ice", "freeze_chance": 25, "cooldown": 0, "category": "elemental"},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.0, "mana_cost": 32, "element": "ice", "freeze_chance": 50, "cooldown": 2, "category": "heavy"},
    "blizzard": {"name": "🌨 Метель", "damage_mult": 2.6, "mana_cost": 48, "element": "ice", "freeze_chance": 35, "cooldown": 4, "category": "ultimate"},
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.6, "mana_cost": 20, "element": "lightning", "stun_chance": 20, "cooldown": 0, "category": "elemental"},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.4, "mana_cost": 42, "element": "lightning", "stun_chance": 35, "cooldown": 3, "category": "heavy"},
    "chain_lightning": {"name": "⚡ Цепная молния", "damage_mult": 1.8, "mana_cost": 30, "element": "lightning", "chain_hits": 3, "cooldown": 2, "category": "heavy"},
    "static_field": {"name": "🔌 Статическое поле", "damage_mult": 3.0, "mana_cost": 60, "element": "lightning", "stun_chance": 50, "cooldown": 5, "category": "ultimate"},
    "water_slash": {"name": "🌊 Водяной разрез", "damage_mult": 1.3, "mana_cost": 15, "element": "water", "cooldown": 0, "category": "elemental"},
    "tsunami": {"name": "🌊 Цунами", "damage_mult": 2.3, "mana_cost": 40, "element": "water", "cooldown": 3, "category": "heavy"},
    "drown": {"name": "💧 Утопление", "damage_mult": 2.0, "mana_cost": 35, "element": "water", "cooldown": 2, "category": "heavy"},
    "healing_wave": {"name": "💚 Целительная волна", "hp_restore": 60, "mana_cost": 30, "element": "water", "cooldown": 3, "category": "support"},
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.6, "mana_cost": 22, "element": "dark", "poison_chance": 25, "cooldown": 0, "category": "elemental"},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.5, "mana_cost": 60, "element": "dark", "ignore_defense": 50, "cooldown": 4, "category": "ultimate"},
    "dark_veil": {"name": "🌑 Завеса тьмы", "defense_boost": 40, "mana_cost": 25, "element": "dark", "cooldown": 2, "category": "defense"},
    "soul_drain": {"name": "💀 Похищение души", "damage_mult": 2.2, "mana_cost": 40, "element": "dark", "life_steal": 0.4, "cooldown": 3, "category": "heavy"},
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.5, "mana_cost": 20, "element": "light", "cooldown": 0, "category": "elemental"},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 3.0, "mana_cost": 55, "element": "light", "cooldown": 4, "category": "ultimate"},
    "heavenly_light": {"name": "🌟 Небесный свет", "hp_restore": 80, "mana_cost": 35, "element": "light", "cooldown": 3, "category": "support"},
    "purification": {"name": "💫 Очищение", "cure_all": True, "hp_restore": 40, "mana_cost": 30, "element": "light", "cooldown": 3, "category": "support"},
    "reap": {"name": "💀 Жатва", "damage_mult": 2.8, "mana_cost": 48, "element": "dark", "life_steal": 0.3, "cooldown": 3, "category": "heavy"},
    "death_sentence": {"name": "☠ Смертный приговор", "damage_mult": 4.0, "mana_cost": 75, "element": "dark", "cooldown": 5, "category": "ultimate"},
    "soul_harvest": {"name": "👻 Сбор душ", "damage_mult": 3.0, "mana_cost": 55, "element": "dark", "life_steal": 0.5, "cooldown": 4, "category": "ultimate"},
    "darkness_falls": {"name": "🕳 Падение тьмы", "damage_mult": 4.5, "mana_cost": 85, "element": "dark", "cooldown": 6, "category": "ultimate"},
    "thunder_gods_wrath": {"name": "⚡ Гнев бога грома", "damage_mult": 4.5, "mana_cost": 85, "element": "lightning", "stun_chance": 50, "cooldown": 5, "category": "ultimate"},
    "eye_of_the_storm": {"name": "🌀 Глаз бури", "damage_mult": 3.2, "mana_cost": 58, "element": "lightning", "cooldown": 4, "category": "ultimate"},
    "lightning_apocalypse": {"name": "⚡ Молниевый апокалипсис", "damage_mult": 5.5, "mana_cost": 100, "element": "lightning", "cooldown": 7, "category": "ultimate"},
    "zeus_fury": {"name": "⚡ Ярость Зевса", "damage_mult": 6.0, "mana_cost": 120, "element": "lightning", "stun_chance": 70, "cooldown": 8, "category": "ultimate"}
}

# Загрузка данных
items = load_json(DATA_FILES['items'], ALL_ITEMS)
limited_items = load_json(DATA_FILES['limited'], LIMITED_ITEMS)
users = load_json(DATA_FILES['users'], {})
clans = load_json(DATA_FILES['clans'], {})
tournaments = load_json(DATA_FILES['tournaments'], {})
market_listings = load_json(DATA_FILES['market'], {})
dungeons_data = load_json(DATA_FILES['dungeons'], {})
events = load_json(DATA_FILES['events'], {})
banned_users = load_json(DATA_FILES['bans'], {})
enchantments_data = load_json(DATA_FILES['enchantments'], {})
matchmaking_queue = load_json(DATA_FILES['matchmaking'], {})

# ==================== КЛАСС ИГРОКА ====================
class Player:
    def __init__(self, user_id, username="Unknown", first_name="Player"):
        self.user_id = str(user_id)
        username = str(username).replace('@', '').strip()
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
                "items_found": 0,
                "world_boss_damage": 0
            }
            self.save()
        elif users[self.user_id].get("username") == "Unknown" and username != "Unknown":
            users[self.user_id]["username"] = username
            self.save()
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    def save(self):
        save_json(DATA_FILES['users'], users)
    
    def get_defense_for_part(self, part):
        """Получить защиту для части тела с учётом брони"""
        defense = 0
        slot_map = {"head": "head", "body": "body", "legs": "legs"}
        slot = slot_map.get(part)
        
        if slot and self.data["equipment"].get(slot):
            ik = self.data["equipment"][slot]
            item = items.get(ik) or limited_items.get(ik)
            if item:
                defense = item.get("defense", 0)
                # Добавляем бонус от зачарования
                ench = self.data.get("enchantments", {}).get(ik, {})
                if ench.get("effect") == "defense_bonus":
                    defense += ench.get("value", 0)
        
        return defense
    
    def calculate_damage(self, base_damage, target_part=None):
        """Рассчитать урон с учётом брони"""
        if target_part and target_part in BODY_PARTS:
            defense = self.get_defense_for_part(target_part)
            reduction = defense / (defense + 100)
            return max(1, int(base_damage * (1 - reduction)))
        return base_damage

# ==================== ХРАНИЛИЩЕ ДУЭЛЕЙ ====================
active_duels = {}
duel_timers = {}

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
        
        # Базовые статы для дуэли
        self.p1_hp = 150
        self.p2_hp = 150
        self.p1_max_hp = 150
        self.p2_max_hp = 150
        
        self.p1_mp = 50
        self.p2_mp = 50
        self.p1_max_mp = 50
        self.p2_max_mp = 50
        
        # Фазы: p1 выбирает защиту и атаку, p2 выбирает защиту
        self.p1_defend = None
        self.p2_defend = None
        self.p1_attack_part = None
        self.p2_attack_part = None
        self.p1_skill = None
        self.p2_skill = None
        
        # Состояния
        self.p1_phase = "defend_select"  # defend_select, attack_select, waiting
        self.p2_phase = "defend_select"
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Эффекты
        self.p1_effects = []
        self.p2_effects = []
        
        # Таймер на ход (45 секунд)
        self.start_turn_timer()
        
        self.log_p1.append("⚔ Битва началась!")
        self.log_p2.append("⚔ Битва началась!")
    
    def start_turn_timer(self):
        """Запуск таймера на ход"""
        if self.battle_id in duel_timers:
            duel_timers[self.battle_id].cancel()
        
        timer = threading.Timer(45.0, self.timeout_turn)
        timer.daemon = True
        duel_timers[self.battle_id] = timer
        timer.start()
    
    def timeout_turn(self):
        """Таймаут хода - авто-проигрыш"""
        if not self.active:
            return
        
        # Определяем кто не сделал ход
        if self.p1_phase != "waiting" and self.p2_phase == "waiting":
            self.winner = 2
        elif self.p2_phase != "waiting" and self.p1_phase == "waiting":
            self.winner = 1
        else:
            self.winner = 2
        
        self.active = False
        self.log_p1.append("⏰ Время вышло!")
        self.log_p2.append("⏰ Время вышло!")
    
    def get_player_name(self, num):
        return self.p1.data["first_name"] if num == 1 else self.p2.data["first_name"]
    
    def get_available_skills(self, player_num):
        player = self.p1 if player_num == 1 else self.p2
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        equip = player.data["equipment"]
        
        available = []
        
        # Базовые навыки всегда доступны
        base = ["quick_strike", "slash", "heavy_slash", "defend"]
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
        
        return list(set(available))
    
    def player_set_defend(self, player_num, part):
        """Игрок выбирает защиту и атаку"""
        if player_num == 1:
            self.p1_defend = part
            self.p1_phase = "attack_select"
        else:
            self.p2_defend = part
            self.p2_phase = "attack_select"
    
    def player_set_attack(self, player_num, part, skill_id):
        """Игрок выбирает атаку и ждёт другого"""
        if player_num == 1:
            self.p1_attack_part = part
            self.p1_skill = skill_id
            self.p1_phase = "waiting"
        else:
            self.p2_attack_part = part
            self.p2_skill = skill_id
            self.p2_phase = "waiting"
        
        # Проверяем, готовы ли оба
        if self.p1_phase == "waiting" and self.p2_phase == "waiting":
            self.resolve_turn()
    
    def resolve_turn(self):
        """Разрешение хода"""
        self.start_turn_timer()
        
        # Обработка эффектов
        self._process_effects(1)
        self._process_effects(2)
        
        # Атака P1 → P2
        self._do_attack(1, 2, self.p1_attack_part, self.p1_skill)
        
        if self.p2_hp <= 0:
            self.winner = 1
            self.active = False
            return
        
        # Атака P2 → P1
        self._do_attack(2, 1, self.p2_attack_part, self.p2_skill)
        
        if self.p1_hp <= 0:
            self.winner = 2
            self.active = False
            return
        
        # Сброс фаз
        self.p1_phase = "defend_select"
        self.p2_phase = "defend_select"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_attack_part = None
        self.p2_attack_part = None
        self.p1_skill = None
        self.p2_skill = None
        
        self.turn += 1
        if self.turn > self.max_turns:
            self.active = False
            if self.p1_hp > self.p2_hp:
                self.winner = 1
            elif self.p2_hp > self.p1_hp:
                self.winner = 2
            else:
                self.winner = 0
    
    def _do_attack(self, attacker, defender, target_part, skill_id):
        if not skill_id or skill_id == "defend":
            return
        
        skill = SKILLS_DB.get(skill_id, {"name": "Атака", "damage_mult": 1.0, "mana_cost": 0})
        
        # Статы
        a_player = self.p1 if attacker == 1 else self.p2
        d_player = self.p2 if attacker == 1 else self.p1
        a_cooldowns = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
        
        # Мана
        mc = skill.get("mana_cost", 0)
        if attacker == 1:
            if self.p1_mp < mc:
                self.log_p1.append("❌ Недостаточно маны!")
                self.log_p2.append(f"❌ {self.get_player_name(attacker)} не хватило маны!")
                return
            self.p1_mp -= mc
        else:
            if self.p2_mp < mc:
                self.log_p2.append("❌ Недостаточно маны!")
                self.log_p1.append(f"❌ {self.get_player_name(attacker)} не хватило маны!")
                return
            self.p2_mp -= mc
        
        # Базовый урон
        weapon_key = a_player.data["equipment"].get("weapon")
        min_d = 5
        max_d = 10
        if weapon_key:
            weapon = items.get(weapon_key) or limited_items.get(weapon_key)
            if weapon and "damage" in weapon:
                min_d = weapon["damage"][0]
                max_d = weapon["damage"][1]
        
        base_dmg = random.randint(min_d, max_d)
        dmg = int(base_dmg * skill.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_m = BODY_PARTS.get(target_part, {}).get("multiplier", 1.0)
        dmg = int(dmg * body_m)
        
        # Проверка защиты противника
        d_defend = self.p2_defend if attacker == 1 else self.p1_defend
        if d_defend == target_part:
            # Часть тела защищена - уменьшаем урон бронёй
            defense = d_player.get_defense_for_part(target_part)
            reduction = defense / (defense + 100)
            dmg = int(dmg * (1 - reduction))
            
            msg = f"🛡 {self.get_player_name(defender)} защитил {BODY_PARTS[target_part]['name']}! Броня ({defense} DEF) снижает урон до {dmg}"
            self.log_p1.append(msg)
            self.log_p2.append(msg)
        else:
            # Часть тела не защищена - полный урон
            msg = f"⚔ {self.get_player_name(attacker)} бьёт в {BODY_PARTS[target_part]['name']}! Урон: {dmg}"
            self.log_p1.append(msg)
            self.log_p2.append(msg)
        
        # Крит
        if random.random() < 0.1:
            dmg = int(dmg * 1.5)
            self.log_p1.append("💥 КРИТ!")
            self.log_p2.append("💥 КРИТ!")
        
        # Нанесение урона
        if defender == 1:
            self.p1_hp = max(0, self.p1_hp - dmg)
        else:
            self.p2_hp = max(0, self.p2_hp - dmg)
        
        # Вампиризм
        if "life_steal" in skill:
            hl = int(dmg * skill["life_steal"])
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + hl)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + hl)
        
        # Лечение
        if "hp_restore" in skill:
            hl = skill["hp_restore"]
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + hl)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + hl)
        
        # Эффекты
        self._apply_effects(defender, skill)
        
        # Кулдауны
        if "cooldown" in skill and skill["cooldown"] > 0:
            a_cooldowns[skill_id] = skill["cooldown"]
        
        for sid in list(a_cooldowns.keys()):
            a_cooldowns[sid] -= 1
            if a_cooldowns[sid] <= 0:
                del a_cooldowns[sid]
        
        # Восстановление маны
        if attacker == 1:
            self.p1_mp = min(self.p1_max_mp, self.p1_mp + 3)
        else:
            self.p2_mp = min(self.p2_max_mp, self.p2_mp + 3)
    
    def _apply_effects(self, target, skill):
        effects = []
        if "burn_chance" in skill and random.random() * 100 < skill["burn_chance"]:
            effects.append({"type": "burn", "duration": 3})
        if "freeze_chance" in skill and random.random() * 100 < skill["freeze_chance"]:
            effects.append({"type": "freeze", "duration": 2})
        if "stun_chance" in skill and random.random() * 100 < skill["stun_chance"]:
            effects.append({"type": "stun", "duration": 1})
        if "poison_chance" in skill and random.random() * 100 < skill["poison_chance"]:
            effects.append({"type": "poison", "duration": 4})
        
        if target == 1:
            self.p1_effects.extend(effects)
        else:
            self.p2_effects.extend(effects)
    
    def _process_effects(self, player_num):
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        hp = self.p1_hp if player_num == 1 else self.p2_hp
        
        for eff in effects[:]:
            if eff["type"] == "burn":
                d = 8
                hp -= d
                self.log_p1.append(f"🔥 Горение -{d} HP")
                self.log_p2.append(f"🔥 Горение -{d} HP")
            elif eff["type"] == "poison":
                d = 10
                hp -= d
                self.log_p1.append(f"☠ Яд -{d} HP")
                self.log_p2.append(f"☠ Яд -{d} HP")
            
            eff["duration"] -= 1
            if eff["duration"] <= 0:
                effects.remove(eff)
        
        if player_num == 1:
            self.p1_hp = max(0, hp)
        else:
            self.p2_hp = max(0, hp)
    
    def get_state_text(self, player_num):
        """Текст состояния для конкретного игрока"""
        phase = self.p1_phase if player_num == 1 else self.p2_phase
        log = self.log_p1 if player_num == 1 else self.log_p2
        
        p1_hp_pct = self.p1_hp / self.p1_max_hp * 100
        p2_hp_pct = self.p2_hp / self.p2_max_hp * 100
        
        text = f"""
<b>⚔ ДУЭЛЬ #{self.battle_id}</b>
━━━━━━━━━━━━━━━━━━━━
Ход: <b>#{self.turn}</b> | Ставка: <b>{self.bet}💰</b>

<b>Вы: {self.get_player_name(player_num)}</b>
❤ [{'█'*int(p1_hp_pct//10)}{'░'*(10-int(p1_hp_pct//10))}] {self.p1_hp}/{self.p1_max_hp}
💎 MP: {self.p1_mp}/{self.p1_max_mp}

<b>Противник: {self.get_player_name(3-player_num)}</b>
❤ [{'█'*int(p2_hp_pct//10)}{'░'*(10-int(p2_hp_pct//10))}] {self.p2_hp}/{self.p2_max_hp}
━━━━━━━━━━━━━━━━━━━━
"""
        
        if phase == "defend_select":
            text += "\n🛡 <b>Выберите часть тела для защиты и атаку:</b>"
        elif phase == "attack_select":
            defend = self.p1_defend if player_num == 1 else self.p2_defend
            text += f"\n🛡 Защита: <b>{BODY_PARTS.get(defend, {}).get('name', 'Не выбрана')}</b>"
            text += "\n🎯 <b>Выберите цель и навык атаки:</b>"
        elif phase == "waiting":
            text += "\n⏳ <b>Ожидание хода противника...</b>"
        
        # Эффекты
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        if effects:
            text += "\n<b>Эффекты:</b> " + ", ".join([e['type'] for e in effects])
        
        # Последний лог
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
• Броня уменьшает урон при попадании
• Вы защищаетесь → противник атакует → вы атакуете
• 3+ навыка на каждое оружие
• Ультимейты с долгим кулдауном
• Таймер 45 сек на ход
• Турниры с сеткой плей-офф
• Мировые боссы
• Ивенты с реальными наградами

💰 Старт: <b>500 монет</b>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль (бот)", callback_data="quick_duel"),
        types.InlineKeyboardButton("👥 Поиск соперника", callback_data="find_opponent"),
        types.InlineKeyboardButton("🏆 Рейтинговая дуэль", callback_data="ranked_duel"),
        types.InlineKeyboardButton("💀 Хардкорная дуэль", callback_data="hardcore_duel"),
        types.InlineKeyboardButton("🔥 Дуэль на выживание", callback_data="survival_duel"),
        types.InlineKeyboardButton("🎯 Дружеский спарринг", callback_data="sparring_duel")
    )
    
    text = """
<b>⚔️ ДУЭЛИ</b>

<b>Система боя:</b>
🛡 Защитите часть тела
🎯 Противник атакует → вы атакуете
🛡 Броня снижает урон при попадании
⚡ Ультимейты с кулдауном 5-8 ходов
⏰ Таймер 45 сек на ход
"""
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="hero_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="hero_inventory"),
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
        types.InlineKeyboardButton("👹 Мировой босс", callback_data="world_boss"),
        types.InlineKeyboardButton("🛡 Кланы", callback_data="world_clans"),
        types.InlineKeyboardButton("🏟 Турниры", callback_data="world_tournaments"),
        types.InlineKeyboardButton("🌍 Ивенты", callback_data="world_events"),
        types.InlineKeyboardButton("📊 Топ", callback_data="world_top")
    )
    bot.send_message(message.chat.id, "<b>🌍 МИР</b>", reply_markup=markup)

# ==================== ДУЭЛИ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["quick_duel", "find_opponent", "ranked_duel", "hardcore_duel", "survival_duel", "sparring_duel"])
def duel_type_handler(call):
    dt = call.data
    
    if dt == "quick_duel":
        show_quick_duel_menu(call)
    elif dt == "find_opponent":
        start_pvp_search(call, "quick", 100)
    elif dt == "ranked_duel":
        start_pvp_search(call, "ranked", 200)
    elif dt == "hardcore_duel":
        start_pvp_search(call, "hardcore", 500)
    elif dt == "survival_duel":
        start_pvp_search(call, "survival", 300)
    elif dt == "sparring_duel":
        start_pvp_search(call, "sparring", 0)

def show_quick_duel_menu(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    for bet in [50, 100, 200, 500, 1000]:
        markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"qduel_{bet}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_main"))
    
    bot.edit_message_text(
        f"<b>⚡ БЫСТРАЯ ДУЭЛЬ (БОТ)</b>\n\n💰 Баланс: <b>{player.data['money']}💰</b>\nВыберите ставку:",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

def start_pvp_search(call, duel_type, bet):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    # Ищем в очереди
    queue = matchmaking_queue.get(f"queue_{duel_type}", [])
    queue = [q for q in queue if q["user_id"] != user_id]
    
    if queue:
        opponent = queue.pop(0)
        matchmaking_queue[f"queue_{duel_type}"] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        if bet > 0:
            player.data["money"] -= bet
            player.save()
            opp = Player(opponent["user_id"])
            opp.data["money"] -= bet
            opp.save()
        
        duel = DuelInstance(opponent["user_id"], user_id, duel_type, bet)
        active_duels[user_id] = duel
        active_duels[opponent["user_id"]] = duel
        
        bot.edit_message_text("⚔ Соперник найден!", call.message.chat.id, call.message.message_id)
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id, 2)
        
        # Уведомление противнику
        try:
            bot.send_message(int(opponent["user_id"]), "⚔ Соперник найден! Дуэль начинается!")
        except:
            pass
    else:
        queue.append({"user_id": user_id, "type": duel_type, "bet": bet})
        matchmaking_queue[f"queue_{duel_type}"] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        # Бот через 5 секунд
        threading.Timer(5.0, create_bot_duel, args=[call.message.chat.id, call.message.message_id, user_id, duel_type, bet]).start()
        
        bot.edit_message_text("🔍 Поиск соперника...", call.message.chat.id, call.message.message_id)

def create_bot_duel(chat_id, message_id, user_id, duel_type, bet):
    if str(user_id) in active_duels:
        return
    
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.edit_message_text(f"❌ Недостаточно монет!", chat_id, message_id)
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
        "hp": 150, "max_hp": 150, "mana": 50, "max_mana": 50,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0, "total_duels": 0,
        "pvp_rating": 1000, "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Бот", "titles_collected": ["Бот"], "achievements": [],
        "clan": None, "clan_role": None, "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    if bet > 0:
        player.data["money"] -= bet
        player.save()
    
    duel = DuelInstance(user_id, bot_id, duel_type, bet)
    active_duels[str(user_id)] = duel
    
    # Бот выбирает защиту и атаку
    bot_def = random.choice(list(BODY_PARTS.keys()))
    duel.set_defend(2, bot_def)
    bot_skills = duel.get_available_skills(2)
    if bot_skills:
        bot_skill = random.choice(bot_skills)
        bot_target = random.choice(list(BODY_PARTS.keys()))
        duel.player_set_attack(2, bot_target, bot_skill)
    
    bot.edit_message_text("⚔ Соперник не найден. Бой с ботом!", chat_id, message_id)
    show_duel_interface(chat_id, message_id, duel, user_id, 1)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def start_quick_duel(call):
    user_id = call.from_user.id
    bet = int(call.data.split("_")[1])
    create_bot_duel(call.message.chat.id, call.message.message_id, user_id, "quick", bet)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    bot.edit_message_text("Главное меню", call.message.chat.id, call.message.message_id)

def show_duel_interface(chat_id, message_id, duel, user_id, player_num=None):
    """Показать интерфейс дуэли"""
    if player_num is None:
        player_num = 1 if str(user_id) == duel.p1_id else 2
    
    if not duel.active:
        finish_duel(chat_id, message_id, duel, user_id)
        return
    
    state_text = duel.get_state_text(player_num)
    
    phase = duel.p1_phase if player_num == 1 else duel.p2_phase
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if phase == "defend_select":
        for part, data in BODY_PARTS.items():
            defense = (Player(duel.p1_id if player_num == 1 else duel.p2_id).get_defense_for_part(part) 
                      if player_num == 1 else Player(duel.p2_id if player_num == 2 else duel.p1_id).get_defense_for_part(part))
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']} (DEF:{defense})",
                callback_data=f"duel_defend_{part}"
            ))
    
    elif phase == "attack_select":
        # Показываем цели для атаки
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🎯 В {data['name']}",
                callback_data=f"duel_target_{part}"
            ))
    
    elif phase == "waiting":
        markup.add(types.InlineKeyboardButton("⏳ Ожидание...", callback_data="duel_wait"))
    
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="duel_refresh"))
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="duel_surrender"))
    
    try:
        bot.edit_message_text(
            state_text[:4000],
            chat_id, message_id,
            reply_markup=markup
        )
    except:
        pass

# Хранение выбранной защиты для фазы attack_select
temp_defend = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_defend_"))
def duel_defend_handler(call):
    user_id = call.from_user.id
    part = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    duel.player_set_defend(pn, part)
    temp_defend[str(user_id)] = part
    
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id, pn)
    bot.answer_callback_query(call.id, f"🛡 Защита: {BODY_PARTS[part]['name']}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_target_"))
def duel_target_handler(call):
    user_id = call.from_user.id
    target_part = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        return
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    
    # Показываем навыки для выбранной цели
    skills = duel.get_available_skills(pn)
    
    state_text = duel.get_state_text(pn) + f"\n🎯 Цель: <b>{BODY_PARTS[target_part]['name']}</b>\n<b>Выберите навык:</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for sid in skills[:12]:
        skill = SKILLS_DB.get(sid, {})
        name = skill.get("name", sid)
        mana = skill.get("mana_cost", 0)
        cd = skill.get("cooldown", 0)
        dmg_mult = skill.get("damage_mult", 1.0)
        category = skill.get("category", "basic")
        
        cat_icon = {"basic": "⚡", "heavy": "💪", "elemental": "✨", "ultimate": "💥", "defense": "🛡", "support": "💚"}.get(category, "")
        
        markup.add(types.InlineKeyboardButton(
            f"{cat_icon} {name} (x{dmg_mult}) [{mana}MP] CD:{cd}",
            callback_data=f"duel_skill_{sid}_{target_part}"
        ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="duel_back_defend"))
    
    try:
        bot.edit_message_text(state_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "duel_back_defend")
def duel_back_defend(call):
    user_id = call.from_user.id
    duel = active_duels.get(str(user_id))
    if duel:
        pn = 1 if str(user_id) == duel.p1_id else 2
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id, pn)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_skill_"))
def duel_skill_handler(call):
    user_id = call.from_user.id
    parts = call.data.split("_", 2)[2].rsplit("_", 1)
    skill_id = parts[0]
    target_part = parts[1] if len(parts) > 1 else "body"
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    duel.player_set_attack(pn, target_part, skill_id)
    
    bot.answer_callback_query(call.id, "⚔ Атака выбрана!")
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id, pn)
    
    # Если бот - он автоматически делает ход
    other_pn = 3 - pn
    if str(duel.p2_id).startswith("bot_") and other_pn == 2:
        # Бот выбирает если ещё не выбрал
        if duel.p2_phase == "defend_select":
            duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
        if duel.p2_phase == "attack_select":
            skills = duel.get_available_skills(2)
            if skills:
                duel.player_set_attack(2, random.choice(list(BODY_PARTS.keys())), random.choice(skills))

@bot.callback_query_handler(func=lambda call: call.data in ["duel_wait", "duel_refresh", "duel_surrender"])
def duel_misc_handler(call):
    user_id = call.from_user.id
    duel = active_duels.get(str(user_id))
    
    if call.data == "duel_wait":
        if duel and duel.active:
            pn = 1 if str(user_id) == duel.p1_id else 2
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id, pn)
    
    elif call.data == "duel_refresh":
        if duel and duel.active:
            pn = 1 if str(user_id) == duel.p1_id else 2
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id, pn)
        else:
            bot.edit_message_text("❌ Дуэль не найдена или завершена", call.message.chat.id, call.message.message_id)
    
    elif call.data == "duel_surrender":
        if duel and duel.active:
            duel.active = False
            duel.winner = 2 if str(user_id) == duel.p1_id else 1
            finish_duel(call.message.chat.id, call.message.message_id, duel, user_id)

def finish_duel(chat_id, message_id, duel, user_id=None):
    """Завершение дуэли и уведомление обоих игроков"""
    # Очистка таймера
    if duel.battle_id in duel_timers:
        duel_timers[duel.battle_id].cancel()
        del duel_timers[duel.battle_id]
    
    # Очистка активных дуэлей
    for uid in list(active_duels.keys()):
        if active_duels.get(uid) and active_duels[uid].battle_id == duel.battle_id:
            del active_duels[uid]
    
    # Удаление ботов
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") and uid in users:
            del users[uid]
    save_json(DATA_FILES['users'], users)
    
    if duel.winner == 0:
        result = "<b>🤝 НИЧЬЯ!</b>"
    elif duel.winner == 1:
        result = f"👑 <b>{duel.get_player_name(1)}</b> побеждает!\n💀 {duel.get_player_name(2)} проигрывает"
    else:
        result = f"👑 <b>{duel.get_player_name(2)}</b> побеждает!\n💀 {duel.get_player_name(1)} проигрывает"
    
    result_text = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

{result}

💰 Ставка: <b>{duel.bet}💰</b>
📊 Ходов: <b>{duel.turn}</b>
"""
    
    # Обновление статистики
    if duel.winner != 0:
        winner_id = duel.p1_id if duel.winner == 1 else duel.p2_id
        loser_id = duel.p2_id if duel.winner == 1 else duel.p1_id
        
        if not winner_id.startswith("bot_"):
            w = Player(winner_id)
            w.data["wins"] += 1
            w.data["win_streak"] += 1
            w.data["total_duels"] += 1
            if w.data["win_streak"] > w.data["best_streak"]:
                w.data["best_streak"] = w.data["win_streak"]
            if duel.bet > 0 and not loser_id.startswith("bot_"):
                w.data["money"] += duel.bet * 2
            w.save()
        
        if not loser_id.startswith("bot_"):
            l = Player(loser_id)
            l.data["losses"] += 1
            l.data["win_streak"] = 0
            l.data["total_duels"] += 1
            l.save()
    
    # Уведомление обоим игрокам
    try:
        bot.edit_message_text(result_text, chat_id, message_id)
    except:
        pass
    
    # Отправляем результат второму игроку
    other_id = duel.p2_id if str(user_id) == duel.p1_id else duel.p1_id
    if not other_id.startswith("bot_") and str(other_id) != str(user_id):
        try:
            bot.send_message(int(other_id), result_text)
        except:
            pass

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
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_main_inline")
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
        elif item.get("type") in ["helmet", "armor", "boots"]:
            s = f"DEF: {item.get('defense', 0)}"
            if "speed" in item:
                s += f" | SPD: +{item['speed']}"
        elif item.get("type") == "potion":
            s = f"HP: +{item.get('heal', 0)}"
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

# ==================== ГЕРОЙ ====================
@bot.callback_query_handler(func=lambda call: call.data == "hero_stats")
def hero_stats(call):
    user_id = call.from_user.id
    player = Player(user_id)
    d = player.data
    
    wr = (d["wins"] / d["total_duels"] * 100) if d["total_duels"] > 0 else 0
    
    head_def = player.get_defense_for_part("head")
    body_def = player.get_defense_for_part("body")
    legs_def = player.get_defense_for_part("legs")
    
    text = f"""
<b>📊 СТАТИСТИКА</b>

<b>{d['first_name']}</b> | {d['title']}
⭐ Ур.{d['level']} | 📊 {d['pvp_rating']}
💰 {d['money']}💰

🛡 Защита: Г:{head_def} Т:{body_def} Н:{legs_def}

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
    
    if "heal" in item:
        if player.data["hp"] >= player.data["max_hp"]:
            bot.answer_callback_query(call.id, "❌ Полное HP!")
            return
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + item["heal"])
    
    if "mana_restore" in item:
        player.data["mana"] = min(player.data["max_mana"], player.data["mana"] + item["mana_restore"])
    
    player.data["inventory"].remove(ik)
    player.save()
    
    bot.answer_callback_query(call.id, "✅ Использовано!")
    hero_inventory(call)

@bot.callback_query_handler(func=lambda call: call.data in ["hero_achievements", "hero_enchantments", "hero_equipped", "hero_history", "hero_heal", "back_to_hero"])
def hero_other_handlers(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "hero_achievements":
        ach_list = [
            ("first_blood", "🩸 Первая кровь", player.data["wins"] >= 1),
            ("warrior", "⚔ Воин", player.data["wins"] >= 10),
            ("veteran", "🎖 Ветеран", player.data["wins"] >= 50),
            ("rich", "💰 Богач", player.data["money"] >= 10000),
            ("dmaster", "🏰 Мастер данжей", player.data.get("dungeons_completed", 0) >= 10),
            ("collector", "🎒 Коллекционер", player.data.get("items_found", 0) >= 20)
        ]
        
        text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(player.data['achievements'])}/6)\n\n"
        
        for aid, name, cond in ach_list:
            done = aid in player.data["achievements"] or cond
            icon = "✅" if done else "🔒"
            text += f"{icon} <b>{name}</b>\n"
            if cond and aid not in player.data["achievements"]:
                player.data["achievements"].append(aid)
        
        player.save()
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
                    text += f"{sn}: <b>{item['name']}</b> (DEF:{item.get('defense', 0)}){ench_text}\n"
                else:
                    text += f"{sn}: ❌ Удалён\n"
            else:
                text += f"{sn}: ❌ Пусто\n"
    elif call.data == "hero_history":
        history = player.data.get("battle_history", [])
        if not history:
            bot.edit_message_text("📋 История пуста", call.message.chat.id, call.message.message_id)
            return
        
        text = "<b>📋 ПОСЛЕДНИЕ 10 БОЁВ</b>\n\n"
        for battle in history[-10:]:
            icon = "🏆" if battle.get("result") == "win" else "💀" if battle.get("result") == "loss" else "🤝"
            text += f"{icon} vs {battle.get('opponent', 'Нет')}\n"
    elif call.data == "hero_heal":
        potions = [k for k in player.data["inventory"] if items.get(k, {}).get("type") == "potion" and items.get(k, {}).get("heal", 0) > 0]
        
        if not potions:
            bot.edit_message_text("💊 Нет зелий!", call.message.chat.id, call.message.message_id)
            return
        
        if player.data["hp"] >= player.data["max_hp"]:
            bot.edit_message_text("💊 Полное здоровье!", call.message.chat.id, call.message.message_id)
            return
        
        pk = potions[0]
        potion = items[pk]
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + potion["heal"])
        player.data["inventory"].remove(pk)
        player.save()
        
        bot.edit_message_text(f"💊 <b>{potion['name']}</b>\n❤ HP: {player.data['hp']}/{player.data['max_hp']}", call.message.chat.id, call.message.message_id)
        return
    
    if call.data == "back_to_hero":
        hero_section(call.message)
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text[:4000] if 'text' in locals() else "OK", call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== МИР ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_dungeons")
def world_dungeons(call):
    text = """
<b>🏰 ПОДЗЕМЕЛЬЯ</b>

🐺 Логово волка (3 босса)
🕷 Паучьи пещеры (3 босса)
💀 Катакомбы (3 босса)
🐉 Драконье логово (3 босса)
👹 Бездна (3 босса)

Кулдаун: 1 час
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, name in enumerate(["🐺 Логово волка", "🕷 Паучьи пещеры", "💀 Катакомбы", "🐉 Драконье логово", "👹 Бездна"], 1):
        markup.add(types.InlineKeyboardButton(name, callback_data=f"dung_{i}_1"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dung_"))
def start_dungeon_boss(call):
    parts = call.data.split("_")
    dl = int(parts[1])
    boss_num = int(parts[2])
    
    user_id = call.from_user.id
    player = Player(user_id)
    
    level_reqs = [1, 5, 10, 15, 25]
    if player.data["level"] < level_reqs[dl - 1]:
        bot.answer_callback_query(call.id, f"❌ Нужен {level_reqs[dl-1]} ур.!")
        return
    
    boss_names = {
        1: {1: "🐺 Волк", 2: "🐺 Альфа-волк", 3: "🐺 Вожак стаи"},
        2: {1: "🕷 Паук", 2: "🕷 Ядовитый паук", 3: "🕷 Королева пауков"},
        3: {1: "💀 Скелет", 2: "💀 Рыцарь смерти", 3: "💀 Некромант"},
        4: {1: "🐉 Драконид", 2: "🐉 Огненный дракон", 3: "🐉 Древний дракон"},
        5: {1: "👹 Бес", 2: "👹 Демон", 3: "👹 Владыка бездны"}
    }
    
    boss_name = boss_names.get(dl, {}).get(boss_num, "Босс")
    boss_hp = 50 + dl * 30 + boss_num * 20
    
    # Создаём босса
    boss_id = f"dungboss_{random.randint(10000, 99999)}"
    users[boss_id] = {
        "username": f"Boss_{dl}_{boss_num}", "first_name": boss_name,
        "money": 0, "level": dl * 5 + boss_num * 2, "exp": 0, "total_exp": 0,
        "hp": boss_hp, "max_hp": boss_hp, "mana": 50, "max_mana": 50,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0, "total_duels": 0,
        "pvp_rating": 1000, "inventory": [], "equipment": {"weapon": None, "head": None, "body": None, "legs": None},
        "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Босс", "titles_collected": ["Босс"], "achievements": [],
        "clan": None, "clan_role": None, "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    reward = {1: 50, 2: 75, 3: 150}[boss_num] * dl
    exp = {1: 30, 2: 50, 3: 100}[boss_num] * dl
    
    duel = DuelInstance(user_id, boss_id, "dungeon", 0)
    active_duels[str(user_id)] = duel
    
    # Босс выбирает
    duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
    skills = duel.get_available_skills(2)
    if skills:
        duel.player_set_attack(2, random.choice(list(BODY_PARTS.keys())), random.choice(skills))
    
    dungeons_data[str(user_id)] = {"dl": dl, "boss_num": boss_num, "reward": reward, "exp": exp}
    save_json(DATA_FILES['dungeons'], dungeons_data)
    
    bot.edit_message_text(f"⚔ Бой с <b>{boss_name}</b> (HP: {boss_hp})!", call.message.chat.id, call.message.message_id)
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id, 1)

@bot.callback_query_handler(func=lambda call: call.data == "world_boss")
def world_boss_menu(call):
    text = """
<b>👹 МИРОВОЙ БОСС</b>

🐉 <b>Древний дракон</b>
❤ HP: 1 000 000
Награда за участие: 1000💰

Наносите урон и получайте награду!
Босс не атакует в ответ.
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚔ Атаковать босса", callback_data="wboss_attack"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world")
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "wboss_attack")
def world_boss_attack(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    damage = random.randint(10, 50) + player.data["level"] * 2
    player.data["world_boss_damage"] = player.data.get("world_boss_damage", 0) + damage
    player.data["money"] += damage // 2
    player.save()
    
    bot.answer_callback_query(call.id, f"⚔ Нанесено {damage} урона! +{damage//2}💰")
    bot.send_message(call.message.chat.id, f"⚔ Вы нанесли <b>{damage}</b> урона Мировому боссу!\n💰 +{damage//2} монет")

# ==================== ТУРНИРЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_tournaments")
def world_tournaments(call):
    if not tournaments.get("active"):
        tournaments["active"] = {
            "name": "Турнир", "participants": [], "rounds": [], "current_round": 0,
            "prize_pool": 5000, "status": "registration"
        }
        save_json(DATA_FILES['tournaments'], tournaments)
    
    tour = tournaments["active"]
    
    text = f"""
<b>🏟 ТУРНИР</b>

<b>{tour['name']}</b>
Участников: {len(tour.get('participants', []))}/16
Приз: <b>{tour.get('prize_pool', 0)}💰</b>
Взнос: 500💰
Статус: {tour.get('status', 'registration')}
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🏆 Участвовать (500💰)", callback_data="tour_join"),
        types.InlineKeyboardButton("📋 Участники", callback_data="tour_list"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world")
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

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
    world_tournaments(call)

# ==================== ИВЕНТЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_events")
def world_events(call):
    current_event = events.get("current", {})
    
    if not current_event or datetime.fromisoformat(current_event.get("expires", "2000-01-01")) < datetime.now():
        new_event = {
            "name": random.choice(["🌋 Извержение", "❄ Ледяной шторм", "⚡ Гроза", "🌑 Затмение", "✨ Звездопад"]),
            "ench_reward": random.choice(ENCHANT_EFFECTS),
            "ench_chance": random.randint(10, 30),
            "reward_money": random.randint(100, 500),
            "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        events["current"] = new_event
        save_json(DATA_FILES['events'], events)
    
    ev = events["current"]
    time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
    minutes_left = max(0, time_left.seconds // 60)
    
    text = f"""
<b>🌍 ИВЕНТ</b>

<b>{ev['name']}</b>
✨ Награда: <b>{ev['ench_reward']['name']}</b>
💰 Монеты: <b>{ev['reward_money']}💰</b>
⏰ Обновление через: {minutes_left} мин.

Участвуйте в дуэлях для шанса получить зачарование!
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "world_top")
def world_top(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⭐ Уровень", callback_data="top_level"),
        types.InlineKeyboardButton("⚔ Победы", callback_data="top_wins"),
        types.InlineKeyboardButton("💰 Монеты", callback_data="top_money"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world")
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
        elif cat == "money":
            val = f"{data.get('money', 0)}💰"
        else:
            val = "0"
        
        text += f"{medals[i]} {data.get('first_name', 'Игрок')}: {val}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_top"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_world")
def back_to_world(call):
    world_section(call.message)

# ==================== РЫНОК ====================
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

@bot.callback_query_handler(func=lambda call: call.data in ["trade_limited", "trade_daily", "trade_sell", "trade_my_lots", "back_to_trade"])
def trade_other_handlers(call):
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
                text += f"<b>{item['name']}</b>\n[{pct}{emp}] {item['remaining']}/{item['total']}\n💰 <b>{item['price']}💰</b>\n\n"
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
        
        bonus = random.randint(150, 600) + player.data["level"] * 10
        exp = random.randint(80, 250)
        
        player.data["money"] += bonus
        player.data["exp"] += exp
        player.data["total_exp"] += exp
        player.data["last_daily"] = today
        
        old = player.data["level"]
        level_up = check_level_up(player)
        player.save()
        
        text = f"<b>🎁 БОНУС</b>\n💰 +{bonus}\n✨ +{exp}"
        if level_up:
            text += f"\n🎉 УРОВЕНЬ <b>{player.data['level']}</b>!"
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    
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
            types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave"),
            types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world")
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
        types.InlineKeyboardButton("🏟 Создать турнир", callback_data="admin_createtour"),
        types.InlineKeyboardButton("👹 Создать босса", callback_data="admin_createboss")
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
    elif call.data == "admin_createtour":
        bot.send_message(call.message.chat.id, "🏟 /createtour [название] [приз]")
    elif call.data == "admin_createboss":
        bot.send_message(call.message.chat.id, "👹 /createboss [имя] [HP]")

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'broadcast', 'resetdaily', 'userinfo', 'createtour', 'createboss'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd == "givemoney":
            username = parts[1].replace('@', '')
            amount = int(parts[2])
            for uid, data in users.items():
                if data.get("username", "").lower() == username.lower():
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
                if data.get("username", "").lower() == username.lower():
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
                if data.get("username", "").lower() == username.lower():
                    banned_users[uid] = {"reason": reason, "banned_at": datetime.now().isoformat()}
                    save_json(DATA_FILES['bans'], banned_users)
                    bot.send_message(message.chat.id, f"⛔ @{username} забанен!")
                    return
            bot.send_message(message.chat.id, "❌ Пользователь не найден")
        
        elif cmd == "unban":
            username = parts[1].replace('@', '')
            for uid, data in users.items():
                if data.get("username", "").lower() == username.lower() and uid in banned_users:
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
                if data.get("username", "").lower() == username.lower():
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
                if data.get("username", "").lower() == username.lower():
                    p = Player(uid)
                    d = p.data
                    text = f"<b>👤 @{username}</b>\nИмя: {d['first_name']}\nУр.: {d['level']}\n💰 {d['money']}\nРейтинг: {d['pvp_rating']}"
                    bot.send_message(message.chat.id, text)
                    return
            bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "createtour":
            name = " ".join(parts[1:-1])
            prize = int(parts[-1])
            tournaments["active"] = {
                "name": name, "participants": [], "rounds": [], "current_round": 0,
                "prize_pool": prize, "status": "registration"
            }
            save_json(DATA_FILES['tournaments'], tournaments)
            bot.send_message(message.chat.id, f"✅ Турнир <b>{name}</b> создан! Приз: {prize}💰")
        
        elif cmd == "createboss":
            name = " ".join(parts[1:-1])
            hp = int(parts[-1])
            events["world_boss"] = {"name": name, "hp": hp, "max_hp": hp}
            save_json(DATA_FILES['events'], events)
            bot.send_message(message.chat.id, f"✅ Босс <b>{name}</b> создан! HP: {hp}")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== ЗАПУСК ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v11.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print("=" * 60)
    print("✅ Броня уменьшает урон")
    print("✅ Защита → атака → ожидание")
    print("✅ Ультимейты с кулдауном")
    print("✅ Таймер 45 сек")
    print("✅ Турниры с сеткой")
    print("✅ Мировой босс")
    print("✅ Ивенты с наградами")
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
