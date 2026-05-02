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
TOKEN = '8670879387:AAH70T6P0ZEn-rvPhQo7rhrNMl9wUKDkILI'
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

ENCHANT_EFFECTS = [
    {"name": "🔥 Огненное", "effect": "fire_damage", "value": 15, "description": "+15 урона огнём"},
    {"name": "❄ Ледяное", "effect": "freeze_chance", "value": 20, "description": "+20% шанс заморозки"},
    {"name": "⚡ Грозовое", "effect": "stun_chance", "value": 15, "description": "+15% шанс оглушения"},
    {"name": "💀 Проклятое", "effect": "life_steal", "value": 12, "description": "+12% вампиризма"},
    {"name": "🛡 Укреплённое", "effect": "defense_bonus", "value": 20, "description": "+20 защиты"},
    {"name": "💪 Мощное", "effect": "damage_boost", "value": 30, "description": "+30% урона"},
    {"name": "💨 Скоростное", "effect": "speed_bonus", "value": 15, "description": "+15 скорости"},
    {"name": "❤ Живучее", "effect": "hp_bonus", "value": 60, "description": "+60 HP"},
    {"name": "💎 Магическое", "effect": "mana_bonus", "value": 40, "description": "+40 MP"},
    {"name": "🍀 Удачливое", "effect": "luck_bonus", "value": 12, "description": "+12 удачи"},
    {"name": "🎯 Меткое", "effect": "crit_bonus", "value": 20, "description": "+20% крита"},
    {"name": "🔮 Мистическое", "effect": "random_effect", "value": 0, "description": "Случайный эффект"}
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
    'battles': 'active_battles.json',
    'admin_announcements': 'admin_announcements.json'
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
    "crown_of_wisdom": {"name": "👑 Корона мудрости", "defense": 12, "mana_bonus": 40, "price": 3500, "type": "helmet", "slot": "head", "rarity": "legendary", "level_req": 28, "enchantable": True}
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

# ==================== НАВЫКИ ====================
SKILLS_DB = {
    "quick_strike": {"name": "⚡ Быстрый удар", "damage_mult": 0.8, "mana_cost": 0, "cooldown": 0},
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 0, "cooldown": 0},
    "power_shot": {"name": "🎯 Мощный выстрел", "damage_mult": 1.8, "mana_cost": 10, "cooldown": 2},
    "multi_shot": {"name": "🏹 Залп", "damage_mult": 0.6, "mana_cost": 15, "cooldown": 2},
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.5, "mana_cost": 12, "cooldown": 1, "element": "fire", "burn_chance": 30},
    "inferno_strike": {"name": "🌋 Инферно удар", "damage_mult": 2.2, "mana_cost": 25, "cooldown": 3, "element": "fire", "burn_chance": 60},
    "flame_wave": {"name": "🔥 Волна пламени", "damage_mult": 2.5, "mana_cost": 35, "cooldown": 4, "element": "fire"},
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.4, "mana_cost": 10, "cooldown": 1, "element": "ice", "freeze_chance": 25},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.0, "mana_cost": 22, "cooldown": 3, "element": "ice", "freeze_chance": 50},
    "blizzard": {"name": "🌨 Метель", "damage_mult": 2.4, "mana_cost": 32, "cooldown": 4, "element": "ice"},
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.6, "mana_cost": 14, "cooldown": 1, "element": "lightning", "stun_chance": 20},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.3, "mana_cost": 30, "cooldown": 3, "element": "lightning", "stun_chance": 35},
    "chain_lightning": {"name": "⚡ Цепная молния", "damage_mult": 1.8, "mana_cost": 20, "cooldown": 2, "element": "lightning"},
    "water_slash": {"name": "🌊 Водяной разрез", "damage_mult": 1.3, "mana_cost": 10, "cooldown": 0, "element": "water"},
    "tsunami": {"name": "🌊 Цунами", "damage_mult": 2.1, "mana_cost": 28, "cooldown": 3, "element": "water"},
    "drown": {"name": "💧 Утопление", "damage_mult": 1.9, "mana_cost": 22, "cooldown": 2, "element": "water"},
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.6, "mana_cost": 14, "cooldown": 1, "element": "dark", "poison_chance": 25},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.2, "mana_cost": 40, "cooldown": 5, "element": "dark"},
    "soul_drain": {"name": "💀 Похищение души", "damage_mult": 2.0, "mana_cost": 25, "cooldown": 3, "element": "dark", "life_steal": 0.4},
    "dark_veil": {"name": "🌑 Завеса тьмы", "defense_boost": 30, "mana_cost": 20, "cooldown": 2},
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.5, "mana_cost": 12, "cooldown": 1, "element": "light"},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 2.8, "mana_cost": 35, "cooldown": 4, "element": "light"},
    "heavenly_light": {"name": "🌟 Небесный свет", "hp_restore": 60, "mana_cost": 25, "cooldown": 3, "element": "light"},
    "reap": {"name": "💀 Жатва", "damage_mult": 2.5, "mana_cost": 30, "cooldown": 3, "element": "dark", "life_steal": 0.3},
    "death_sentence": {"name": "☠ Смертный приговор", "damage_mult": 4.0, "mana_cost": 55, "cooldown": 6, "element": "dark"},
    "soul_harvest": {"name": "👻 Сбор душ", "damage_mult": 2.8, "mana_cost": 40, "cooldown": 4, "element": "dark", "life_steal": 0.5},
    "thunder_gods_wrath": {"name": "⚡ Гнев бога грома", "damage_mult": 4.5, "mana_cost": 70, "cooldown": 6, "element": "lightning", "stun_chance": 50},
    "eye_of_the_storm": {"name": "🌀 Глаз бури", "damage_mult": 3.0, "mana_cost": 45, "cooldown": 4, "element": "lightning"},
    "lightning_apocalypse": {"name": "⚡ Молниевый апокалипсис", "damage_mult": 5.0, "mana_cost": 85, "cooldown": 7, "element": "lightning"}
}

# Загрузка данных
items = load_json(DATA_FILES['items'], ALL_ITEMS)
limited_items = load_json(DATA_FILES['limited'], LIMITED_ITEMS)
users = load_json(DATA_FILES['users'], {})
clans = load_json(DATA_FILES['clans'], {})
tournaments = load_json(DATA_FILES['tournaments'], {})
market_listings = load_json(DATA_FILES['market'], {})
dungeon_progress = load_json(DATA_FILES['dungeons'], {})
events_data = load_json(DATA_FILES['events'], {})
banned_users = load_json(DATA_FILES['bans'], {})
battle_history_data = load_json(DATA_FILES['battle_history'], {})
enchantments_data = load_json(DATA_FILES['enchantments'], {})
matchmaking_queue = load_json(DATA_FILES['matchmaking'], {})
active_battles = load_json(DATA_FILES['battles'], {})
admin_announcements = load_json(DATA_FILES['admin_announcements'], {})

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def find_user_by_username(username):
    """Поиск пользователя по username"""
    username = username.replace('@', '').lower()
    for uid, data in users.items():
        if data.get("username", "").lower() == username:
            return uid
    return None

def find_user_by_id_or_username(identifier):
    """Поиск по ID или username"""
    identifier = str(identifier).replace('@', '')
    # Сначала ищем по ID
    if identifier in users:
        return identifier
    # Затем по username
    return find_user_by_username(identifier)

def get_player_name(uid):
    """Получить имя игрока"""
    if uid.startswith("bot_") or uid.startswith("boss_"):
        return users.get(uid, {}).get("first_name", "Противник")
    return users.get(uid, {}).get("first_name", "Игрок")

def get_player_username(uid):
    """Получить username игрока"""
    if uid.startswith("bot_") or uid.startswith("boss_"):
        return None
    uname = users.get(uid, {}).get("username", "")
    return f"@{uname}" if uname else f"ID:{uid}"

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
        """Получить защиту экипировки для слота"""
        ik = self.data["equipment"].get(slot)
        if not ik:
            return 0
        item = items.get(ik) or limited_items.get(ik)
        if not item:
            return 0
        return item.get("defense", 0)
    
    def get_weapon_skills(self):
        """Получить навыки оружия"""
        ik = self.data["equipment"].get("weapon")
        if not ik:
            return ["quick_strike", "slash"]
        item = items.get(ik) or limited_items.get(ik)
        if not item or "skills" not in item:
            return ["quick_strike", "slash"]
        return item["skills"]
    
    def get_element(self):
        """Получить элемент оружия"""
        ik = self.data["equipment"].get("weapon")
        if not ik:
            return None
        item = items.get(ik) or limited_items.get(ik)
        if not item:
            return None
        return item.get("element")

# ==================== ХРАНИЛИЩЕ ДУЭЛЕЙ ====================
active_duels = {}

class DuelInstance:
    def __init__(self, p1_id, p2_id, duel_type="quick", bet=0, tournament_match=False):
        self.battle_id = str(uuid.uuid4())[:8]
        self.p1_id = str(p1_id)
        self.p2_id = str(p2_id)
        self.duel_type = duel_type
        self.bet = bet
        self.turn = 1
        self.max_turns = 40
        self.active = True
        self.winner = None
        self.log_p1 = []
        self.log_p2 = []
        self.tournament_match = tournament_match
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        # HP одинаковые для честного боя
        self.p1_hp = 100
        self.p2_hp = 100
        self.p1_max_hp = 100
        self.p2_max_hp = 100
        
        self.p1_mp = 50
        self.p2_mp = 50
        self.p1_max_mp = 50
        self.p2_max_mp = 50
        
        # Фазы: пошагово - P1 защищается, P2 атакует; потом наоборот
        self.round_type = "p1_defend_p2_attack"  # или "p2_defend_p1_attack"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        
        # Кто сделал выбор
        self.p1_ready = False
        self.p2_ready = False
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Счётчик бездействия
        self.idle_turns = 0
        self.max_idle_turns = 3
        
        # Арена
        self.arena = random.choice(["colosseum", "forest", "volcano", "tundra", "void", "temple"])
        
        self._add_log(1, f"⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>")
        self._add_log(2, f"⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>")
        self._add_log(1, f"Тип: <b>{self._duel_type_name()}</b> | Ставка: <b>{bet}💰</b>")
        self._add_log(2, f"Тип: <b>{self._duel_type_name()}</b> | Ставка: <b>{bet}💰</b>")
        
        if self.round_type == "p1_defend_p2_attack":
            self._add_log(1, f"🛡 <b>Вы защищаетесь!</b> Выберите часть тела для защиты.")
            self._add_log(2, f"⚔ <b>Вы атакуете!</b> Ожидание выбора защиты противника...")
        else:
            self._add_log(2, f"🛡 <b>Вы защищаетесь!</b> Выберите часть тела для защиты.")
            self._add_log(1, f"⚔ <b>Вы атакуете!</b> Ожидание выбора защиты противника...")
    
    def _duel_type_name(self):
        names = {
            "quick": "Быстрая дуэль",
            "pvp": "PvP дуэль",
            "ranked": "Рейтинговая дуэль",
            "hardcore": "Хардкорная дуэль",
            "sparring": "Дружеский спарринг",
            "survival": "Дуэль на выживание",
            "dungeon": "Подземелье",
            "tournament": "Турнир"
        }
        return names.get(self.duel_type, self.duel_type)
    
    def _add_log(self, player_num, msg):
        if player_num == 1:
            self.log_p1.append(msg)
        else:
            self.log_p2.append(msg)
    
    def set_defend(self, player_num, part):
        """Игрок выбрал защиту"""
        if player_num == 1:
            self.p1_defend = part
            self.p1_ready = True
            self._add_log(1, f"🛡 Вы защищаете: <b>{BODY_PARTS[part]['name']}</b>")
            self._add_log(2, f"🛡 Противник защитил: <b>{BODY_PARTS[part]['name']}</b>")
        else:
            self.p2_defend = part
            self.p2_ready = True
            self._add_log(2, f"🛡 Вы защищаете: <b>{BODY_PARTS[part]['name']}</b>")
            self._add_log(1, f"🛡 Противник защитил: <b>{BODY_PARTS[part]['name']}</b>")
        
        self._check_round_resolution()
    
    def set_attack(self, player_num, skill_id, target_part):
        """Игрок выбрал атаку"""
        if player_num == 1:
            self.p1_skill = skill_id
            self.p1_target = target_part
            self.p1_ready = True
        else:
            self.p2_skill = skill_id
            self.p2_target = target_part
            self.p2_ready = True
        
        self._check_round_resolution()
    
    def _check_round_resolution(self):
        """Проверка готовности к разрешению раунда"""
        if self.round_type == "p1_defend_p2_attack":
            # P1 защищается, P2 атакует
            if self.p1_defend and self.p2_skill and self.p2_target:
                self._resolve_attack(2, 1)  # Атакующий=2, Защитник=1
                self._switch_round()
        else:
            # P2 защищается, P1 атакует
            if self.p2_defend and self.p1_skill and self.p1_target:
                self._resolve_attack(1, 2)  # Атакующий=1, Защитник=2
                self._switch_round()
    
    def _resolve_attack(self, attacker, defender):
        """Разрешение атаки"""
        skill_id = self.p1_skill if attacker == 1 else self.p2_skill
        target_part = self.p1_target if attacker == 1 else self.p2_target
        defend_part = self.p1_defend if attacker == 1 else self.p2_defend
        
        skill = SKILLS_DB.get(skill_id, {"name": "Атака", "damage_mult": 1.0, "mana_cost": 0})
        
        # Проверка маны
        mc = skill.get("mana_cost", 0)
        if attacker == 1:
            if self.p1_mp < mc:
                self._add_log(1, "❌ Недостаточно маны!")
                self._add_log(2, "❌ Противнику не хватило маны!")
                return
            self.p1_mp -= mc
        else:
            if self.p2_mp < mc:
                self._add_log(2, "❌ Недостаточно маны!")
                self._add_log(1, "❌ Противнику не хватило маны!")
                return
            self.p2_mp -= mc
        
        # Базовый урон
        attacker_player = self.p1 if attacker == 1 else self.p2
        weapon_skills = attacker_player.get_weapon_skills()
        
        min_dmg = 5 + (attacker_player.data["level"] * 2)
        max_dmg = 15 + (attacker_player.data["level"] * 3)
        dmg = random.randint(min_dmg, max_dmg)
        dmg = int(dmg * skill.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_mult = BODY_PARTS.get(target_part, {}).get("multiplier", 1.0)
        dmg = int(dmg * body_mult)
        
        # Проверка защиты
        defender_player = self.p1 if defender == 1 else self.p2
        defense_value = defender_player.get_equipment_defense(target_part)
        
        # Базовая защита части тела
        base_defense = {"head": 3, "body": 5, "legs": 2}.get(target_part, 3)
        total_defense = base_defense + defense_value
        
        # Уменьшение урона бронёй
        damage_reduction = total_defense / (total_defense + 50)
        blocked = int(dmg * damage_reduction)
        final_dmg = dmg - blocked
        
        # Если цель совпадает с защитой - дополнительное снижение
        if defend_part == target_part:
            final_dmg = int(final_dmg * 0.5)
            self._add_log(attacker, f"🛡 Противник защитил эту часть! Урон снижен вдвое.")
            self._add_log(defender, f"🛡 Вы успешно защитили эту часть! Урон снижен вдвое.")
        
        final_dmg = max(1, final_dmg)  # Минимальный урон 1
        
        # Нанесение урона
        if defender == 1:
            self.p1_hp = max(0, self.p1_hp - final_dmg)
        else:
            self.p2_hp = max(0, self.p2_hp - final_dmg)
        
        skill_name = skill.get("name", "Атака")
        self._add_log(attacker, f"⚔ Вы атаковали [{skill_name}] → {BODY_PARTS[target_part]['name']}: <b>-{final_dmg} HP</b> (защита поглотила {blocked})")
        self._add_log(defender, f"💢 Противник атаковал [{skill_name}] → {BODY_PARTS[target_part]['name']}: <b>-{final_dmg} HP</b>")
        
        # Эффекты
        if "burn_chance" in skill and random.random() * 100 < skill["burn_chance"]:
            self._add_log(defender, "🔥 Горение!")
            self._add_log(attacker, "🔥 Противник горит!")
        if "freeze_chance" in skill and random.random() * 100 < skill["freeze_chance"]:
            self._add_log(defender, "❌ Заморозка! Пропуск хода.")
            self._add_log(attacker, "❌ Противник заморожен!")
        if "stun_chance" in skill and random.random() * 100 < skill["stun_chance"]:
            self._add_log(defender, "⚡ Оглушение!")
            self._add_log(attacker, "⚡ Противник оглушён!")
        
        # Вампиризм
        if "life_steal" in skill:
            heal = int(final_dmg * skill["life_steal"])
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self._add_log(attacker, f"💚 Вампиризм +{heal} HP")
        
        # Лечение
        if "hp_restore" in skill:
            heal = skill["hp_restore"]
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self._add_log(attacker, f"💚 +{heal} HP")
        
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
    
    def _switch_round(self):
        """Переключение раунда"""
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        self.p1_ready = False
        self.p2_ready = False
        
        if self.round_type == "p1_defend_p2_attack":
            self.round_type = "p2_defend_p1_attack"
            self._add_log(2, f"🛡 <b>Вы защищаетесь!</b> Выберите часть тела для защиты.")
            self._add_log(1, f"⚔ <b>Вы атакуете!</b> Ожидание выбора защиты противника...")
        else:
            self.round_type = "p1_defend_p2_attack"
            self._add_log(1, f"🛡 <b>Вы защищаетесь!</b> Выберите часть тела для защиты.")
            self._add_log(2, f"⚔ <b>Вы атакуете!</b> Ожидание выбора защиты противника...")
        
        self.turn += 1
        
        if self.turn > self.max_turns:
            self.active = False
            self.winner = 0
    
    def get_state_text(self, for_player_id):
        """Получить текст состояния для игрока"""
        pn = 1 if str(for_player_id) == self.p1_id else 2
        is_defending = (self.round_type == "p1_defend_p2_attack" and pn == 1) or \
                       (self.round_type == "p2_defend_p1_attack" and pn == 2)
        
        opponent_name = get_player_name(self.p2_id) if pn == 1 else get_player_name(self.p1_id)
        
        my_hp = self.p1_hp if pn == 1 else self.p2_hp
        opp_hp = self.p2_hp if pn == 1 else self.p1_hp
        my_mp = self.p1_mp if pn == 1 else self.p2_mp
        
        my_hp_pct = my_hp / 100 * 100
        opp_hp_pct = opp_hp / 100 * 100
        
        def bar(pct, cur, icon):
            f = int(pct / 10)
            e = 10 - f
            color = "🟢" if pct > 50 else "🟡" if pct > 25 else "🔴"
            return f"{icon} {color}[{'█'*f}{'░'*e}] {cur}/100"
        
        text = f"""
<b>⚔ ДУЭЛЬ #{self.battle_id}</b>
━━━━━━━━━━━━━━━━━━━━
Ход: <b>#{self.turn}</b> | Ставка: <b>{self.bet}💰</b>

<b>Вы:</b> {bar(my_hp_pct, my_hp, '❤')}
💎 MP: {my_mp}/50

<b>{opponent_name}:</b> {bar(opp_hp_pct, opp_hp, '❤')}
━━━━━━━━━━━━━━━━━━━━
"""
        
        if is_defending:
            text += "\n🛡 <b>Вы защищаетесь!</b> Выберите часть тела для защиты:"
        else:
            text += "\n⚔ <b>Вы атакуете!</b> Выберите цель и навык:"
        
        # Лог
        my_log = self.log_p1 if pn == 1 else self.log_p2
        if my_log:
            text += f"\n<i>{my_log[-1][:100]}</i>"
        
        return text
    
    def get_available_skills(self, player_num):
        """Получить доступные навыки"""
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

# ==================== ОБРАБОТЧИКИ КОМАНД ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    if str(user_id) in banned_users:
        ban = banned_users[str(user_id)]
        bot.send_message(message.chat.id, f"⛔ Вы забанены!\nПричина: {ban.get('reason', 'Нет')}")
        return
    
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or "Игрок"
    
    # Обновляем username если изменился
    if str(user_id) in users:
        users[str(user_id)]["username"] = username
        users[str(user_id)]["first_name"] = first_name
        save_json(DATA_FILES['users'], users)
    else:
        Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v11.0 ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

🎯 <b>СИСТЕМА БОЯ:</b>
• Пошагово: один защищается, другой атакует
• Броня уменьшает урон по частям тела
• У каждого оружия свои навыки
• Кулдауны на мощные атаки
• Поиск соперника или бот

💰 Старт: <b>500 монет</b>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль", callback_data="quick_duel"),
        types.InlineKeyboardButton("👥 Найти соперника", callback_data="find_opponent"),
        types.InlineKeyboardButton("🏆 Рейтинговая дуэль", callback_data="ranked_duel"),
        types.InlineKeyboardButton("💀 Хардкорная дуэль", callback_data="hardcore_duel"),
        types.InlineKeyboardButton("🔥 Дуэль на выживание", callback_data="survival_duel"),
        types.InlineKeyboardButton("🎯 Дружеский спарринг", callback_data="sparring_duel")
    )
    
    text = """
<b>⚔️ ДУЭЛИ</b>

<b>Пошаговая система:</b>
🛡 Один защищается → другой атакует
🔄 Затем меняются ролями
🛡 Броня уменьшает урон

<i>Выберите тип дуэли:</i>
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
        types.InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="trade_daily"),
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
@bot.callback_query_handler(func=lambda call: call.data in ["quick_duel", "find_opponent", "ranked_duel", "hardcore_duel", "survival_duel", "sparring_duel"])
def duel_type_handler(call):
    dt = call.data
    
    if dt == "quick_duel":
        show_quick_duel_menu(call)
    elif dt == "find_opponent":
        start_matchmaking(call, "pvp", 50)
    elif dt == "ranked_duel":
        start_matchmaking(call, "ranked", 100)
    elif dt == "hardcore_duel":
        show_hardcore_menu(call)
    elif dt == "survival_duel":
        start_matchmaking(call, "survival", 200)
    elif dt == "sparring_duel":
        start_matchmaking(call, "sparring", 0)

def show_quick_duel_menu(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    for bet in [50, 100, 200, 500, 1000]:
        markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"qduel_{bet}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
    
    bot.edit_message_text(
        f"<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n\n💰 Баланс: <b>{player.data['money']}💰</b>\nВыберите ставку:",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

def show_hardcore_menu(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    for bet in [500, 1000, 2000, 5000, 10000]:
        markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"hduel_{bet}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
    
    bot.edit_message_text(
        f"<b>💀 ХАРДКОРНАЯ ДУЭЛЬ</b>\n\n💰 Баланс: <b>{player.data['money']}💰</b>\nВыберите ставку:",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_duels")
def back_to_duels(call):
    duel_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def start_quick_duel_bet(call):
    bet = int(call.data.split("_")[1])
    start_bot_duel(call.message.chat.id, call.message.message_id, call.from_user.id, "quick", bet)

@bot.callback_query_handler(func=lambda call: call.data.startswith("hduel_"))
def start_hardcore_duel_bet(call):
    bet = int(call.data.split("_")[1])
    start_bot_duel(call.message.chat.id, call.message.message_id, call.from_user.id, "hardcore", bet)

def start_matchmaking(call, duel_type, bet):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    # Проверяем очередь
    queue = matchmaking_queue.get(duel_type, [])
    queue = [q for q in queue if q["user_id"] != user_id]
    
    if queue:
        opponent = queue.pop(0)
        matchmaking_queue[duel_type] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        if bet > 0:
            player.data["money"] -= bet
            opponent_player = Player(opponent["user_id"])
            opponent_player.data["money"] -= bet
            player.save()
            opponent_player.save()
        
        duel = DuelInstance(opponent["user_id"], user_id, duel_type, bet)
        active_duels[user_id] = duel
        active_duels[opponent["user_id"]] = duel
        
        bot.edit_message_text("⚔ Соперник найден!", call.message.chat.id, call.message.message_id)
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        # Отправляем сообщение сопернику
        try:
            opponent_msg = bot.send_message(int(opponent["user_id"]), "⚔ Дуэль начинается!")
            show_duel_interface(int(opponent["user_id"]), opponent_msg.message_id, duel, opponent["user_id"])
        except:
            pass
    else:
        queue.append({"user_id": user_id, "bet": bet})
        matchmaking_queue[duel_type] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        bot.edit_message_text("🔍 Поиск соперника... Если не найдём — бот!", call.message.chat.id, call.message.message_id)
        threading.Timer(7.0, start_bot_duel_if_no_opponent, args=[call.message.chat.id, call.message.message_id, user_id, duel_type, bet]).start()

def start_bot_duel_if_no_opponent(chat_id, message_id, user_id, duel_type="quick", bet=50):
    if str(user_id) in active_duels:
        return
    
    start_bot_duel(chat_id, message_id, user_id, duel_type, bet)

def start_bot_duel(chat_id, message_id, user_id, duel_type="quick", bet=50):
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        try:
            bot.edit_message_text(f"❌ Недостаточно монет! Нужно {bet}💰", chat_id, message_id)
        except:
            pass
        return
    
    # Создание бота
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
        "username": f"Bot_{bot_level}",
        "first_name": f"🤖 Бот Lv.{bot_level}",
        "money": 0, "level": bot_level, "exp": 0, "total_exp": 0,
        "hp": 100, "max_hp": 100, "mana": 50, "max_mana": 50,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000,
        "inventory": [], "equipment": equip, "enchantments": {},
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
    
    try:
        bot.edit_message_text("⚔ Бой с ботом!", chat_id, message_id)
    except:
        pass
    
    show_duel_interface(chat_id, message_id, duel, user_id)

def show_duel_interface(chat_id, message_id, duel, user_id):
    """Показать интерфейс дуэли"""
    if not duel.active:
        finish_duel(chat_id, message_id, duel, user_id)
        return
    
    state_text = duel.get_state_text(user_id)
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    is_defending = (duel.round_type == "p1_defend_p2_attack" and pn == 1) or \
                   (duel.round_type == "p2_defend_p1_attack" and pn == 2)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if is_defending:
        for part, data in BODY_PARTS.items():
            player = duel.p1 if pn == 1 else duel.p2
            defense = player.get_equipment_defense(part)
            base_def = {"head": 3, "body": 5, "legs": 2}.get(part, 3)
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']} (DEF:{base_def + defense})",
                callback_data=f"duel_defend_{part}"
            ))
    else:
        # Атакующий - сначала цель, потом навык
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🎯 {data['name']}",
                callback_data=f"duel_target_{part}"
            ))
    
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="duel_surrender"))
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="duel_refresh"))
    
    try:
        bot.edit_message_text(
            state_text[:4000],
            chat_id, message_id,
            reply_markup=markup
        )
    except Exception as e:
        try:
            bot.send_message(chat_id, state_text[:4000], reply_markup=markup)
        except:
            pass

# Временное хранилище для выбора цели
temp_target = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_target_"))
def duel_target_handler(call):
    user_id = call.from_user.id
    part = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.answer_callback_query(call.id, "❌ Дуэль не найдена")
        return
    
    temp_target[str(user_id)] = part
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    skills = duel.get_available_skills(pn)
    
    state_text = duel.get_state_text(user_id) + f"\n\n🎯 Цель: <b>{BODY_PARTS[part]['name']}</b>\n<b>Выберите навык:</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for sid in skills[:8]:
        skill = SKILLS_DB.get(sid, {})
        name = skill.get("name", sid)
        mana = skill.get("mana_cost", 0)
        dmg = skill.get("damage_mult", 1.0)
        cd = skill.get("cooldown", 0)
        cd_text = f" | CD:{cd}" if cd > 0 else ""
        
        markup.add(types.InlineKeyboardButton(
            f"{name} (x{dmg}) [{mana}MP]{cd_text}",
            callback_data=f"duel_skill_{sid}"
        ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="duel_back"))
    
    try:
        bot.edit_message_text(state_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "duel_back")
def duel_back_handler(call):
    duel = active_duels.get(str(call.from_user.id))
    if duel:
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, call.from_user.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_skill_"))
def duel_skill_handler(call):
    user_id = call.from_user.id
    skill_id = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    target = temp_target.get(str(user_id), "body")
    pn = 1 if str(user_id) == duel.p1_id else 2
    
    duel.set_attack(pn, skill_id, target)
    
    # Бот делает ход автоматически
    other_pn = 3 - pn
    if str(duel.p2_id).startswith("bot_") and other_pn == 2:
        if duel.round_type == "p1_defend_p2_attack":
            # Бот защищается
            duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
        else:
            # Бот атакует
            duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
            # Ждём немного
            time.sleep(0.5)
            if duel.round_type == "p2_defend_p1_attack":
                bot_skills = duel.get_available_skills(1)
                if bot_skills:
                    duel.set_attack(1, random.choice(bot_skills), random.choice(list(BODY_PARTS.keys())))
    
    bot.answer_callback_query(call.id, "⚔ Атака!")
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_defend_"))
def duel_defend_handler(call):
    user_id = call.from_user.id
    part = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.answer_callback_query(call.id, "❌ Дуэль не найдена")
        return
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    duel.set_defend(pn, part)
    
    bot.answer_callback_query(call.id, f"🛡 Защита: {BODY_PARTS[part]['name']}")
    
    # Бот атакует если его очередь
    other_pn = 3 - pn
    if str(duel.p2_id).startswith("bot_") and other_pn == 2:
        if duel.round_type == "p1_defend_p2_attack":
            time.sleep(0.5)
            bot_skills = duel.get_available_skills(2)
            if bot_skills:
                duel.set_attack(2, random.choice(bot_skills), random.choice(list(BODY_PARTS.keys())))
    
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data in ["duel_refresh", "duel_surrender"])
def duel_misc_handler(call):
    user_id = call.from_user.id
    duel = active_duels.get(str(user_id))
    
    if call.data == "duel_refresh":
        if duel and duel.active:
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
            bot.answer_callback_query(call.id, "✅")
        else:
            bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
    
    elif call.data == "duel_surrender":
        if duel and duel.active:
            duel.active = False
            duel.winner = 2 if str(user_id) == duel.p1_id else 1
            finish_duel(call.message.chat.id, call.message.message_id, duel, user_id)

def finish_duel(chat_id, message_id, duel, for_user_id=None):
    """Завершение дуэли с уведомлением обоих игроков"""
    # Очистка
    for uid in [duel.p1_id, duel.p2_id]:
        if uid in active_duels and active_duels[uid].battle_id == duel.battle_id:
            del active_duels[uid]
    
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") or uid.startswith("boss_"):
            if uid in users:
                del users[uid]
    save_json(DATA_FILES['users'], users)
    
    p1_name = get_player_name(duel.p1_id)
    p2_name = get_player_name(duel.p2_id)
    
    if duel.winner == 0:
        result = "<b>🤝 НИЧЬЯ!</b>"
    elif duel.winner == 1:
        result = f"👑 <b>{p1_name}</b> побеждает!\n💀 <b>{p2_name}</b> проигрывает"
    else:
        result = f"👑 <b>{p2_name}</b> побеждает!\n💀 <b>{p1_name}</b> проигрывает"
    
    result_text = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

{result}

💰 Ставка: <b>{duel.bet}💰</b>
📊 Ходов: <b>{duel.turn}</b>
"""
    
    # Начисление наград
    if duel.winner != 0:
        winner_id = duel.p1_id if duel.winner == 1 else duel.p2_id
        loser_id = duel.p2_id if duel.winner == 1 else duel.p1_id
        
        if not winner_id.startswith("bot_") and not winner_id.startswith("boss_"):
            winner = Player(winner_id)
            if duel.bet > 0:
                winner.data["money"] += duel.bet * 2
            winner.data["wins"] += 1
            winner.data["win_streak"] += 1
            winner.data["total_duels"] += 1
            winner.data["pvp_rating"] += random.randint(20, 35)
            if winner.data["win_streak"] > winner.data["best_streak"]:
                winner.data["best_streak"] = winner.data["win_streak"]
            exp_w = duel.turn * 10 + duel.bet // 2
            winner.data["exp"] += exp_w
            winner.data["total_exp"] += exp_w
            check_level_up(winner)
            winner.save()
        
        if not loser_id.startswith("bot_") and not loser_id.startswith("boss_"):
            loser = Player(loser_id)
            loser.data["losses"] += 1
            loser.data["win_streak"] = 0
            loser.data["total_duels"] += 1
            loser.data["pvp_rating"] = max(0, loser.data["pvp_rating"] - random.randint(10, 25))
            check_level_up(loser)
            loser.save()
    
    # Отправка результата обоим игрокам
    try:
        bot.edit_message_text(result_text, chat_id, message_id)
    except:
        pass
    
    # Отправляем второму игроку
    other_id = duel.p2_id if str(for_user_id) == duel.p1_id else duel.p1_id
    if not other_id.startswith("bot_") and not other_id.startswith("boss_"):
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
        elif item.get("type") in ["helmet", "armor", "boots"]:
            s = f"Защита: {item.get('defense', 0)}"
            if "speed" in item:
                s += f" | Скорость: +{item['speed']}"
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
    
    elif call.data == "trade_market":
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
    
    item = items.get(listing["item_key"], {})
    bot.answer_callback_query(call.id, f"✅ {item.get('name', 'Предмет')}!")
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
@bot.callback_query_handler(func=lambda call: call.data in ["hero_stats", "hero_inventory", "hero_attributes", "hero_achievements", "hero_enchantments", "hero_equipped", "hero_history", "hero_heal", "back_to_hero"])
def hero_handlers(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "hero_stats":
        d = player.data
        wr = (d["wins"] / d["total_duels"] * 100) if d["total_duels"] > 0 else 0
        text = f"""
<b>📊 СТАТИСТИКА</b>

<b>{d['first_name']}</b> | {d['title']}
⭐ Ур.{d['level']} | 📊 {d['pvp_rating']}
💰 {d['money']}💰

🏆 Побед: {d['wins']} | 💀 Поражений: {d['losses']}
📈 Винрейт: {wr:.1f}%

🛡 Защита: Г:{player.get_equipment_defense('head')} Т:{player.get_equipment_defense('body')} Н:{player.get_equipment_defense('legs')}
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_inventory":
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
    
    elif call.data == "hero_equipped":
        equip = player.data["equipment"]
        text = "<b>👁 ЭКИПИРОВКА</b>\n\n"
        slot_names = {"weapon": "⚔ Оружие", "head": "👤 Голова (DEF:{})", "body": "🦾 Тело (DEF:{})", "legs": "🦿 Ноги (DEF:{})"}
        for slot, sn in slot_names.items():
            ik = equip.get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                if item:
                    defense = item.get("defense", 0)
                    text += sn.format(defense) + f": <b>{item['name']}</b>\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔴 Снять всё", callback_data="unequip_all"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
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
    
    elif call.data == "hero_enchantments":
        ench = player.data.get("enchantments", {})
        if not ench:
            bot.edit_message_text("✨ Нет зачарований", call.message.chat.id, call.message.message_id)
            return
        text = "<b>✨ ЗАЧАРОВАНИЯ</b>\n\n"
        for ik, e in ench.items():
            item = items.get(ik) or limited_items.get(ik)
            if item:
                text += f"📦 {item['name']}: <b>{e.get('name', 'Нет')}</b>\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_achievements":
        ach_list = [
            ("first_blood", "🩸 Первая кровь", player.data["wins"] >= 1),
            ("warrior", "⚔ Воин", player.data["wins"] >= 10),
            ("veteran", "🎖 Ветеран", player.data["wins"] >= 50),
            ("legend", "👑 Легенда", player.data["wins"] >= 100),
            ("rich", "💰 Богач", player.data["money"] >= 10000),
            ("dmaster", "🏰 Мастер данжей", player.data.get("dungeons_completed", 0) >= 10),
            ("collector", "🎒 Коллекционер", player.data.get("items_found", 0) >= 20)
        ]
        text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(player.data['achievements'])}/7)\n\n"
        for aid, name, cond in ach_list:
            done = aid in player.data["achievements"] or cond
            icon = "✅" if done else "🔒"
            text += f"{icon} <b>{name}</b>\n"
            if cond and aid not in player.data["achievements"]:
                player.data["achievements"].append(aid)
        player.save()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
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
    
    elif call.data == "back_to_hero":
        hero_section(call.message)

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
    hero_handlers(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("enchant_"))
def enchant_item(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(ik) or limited_items.get(ik)
    if not item or not item.get("enchantable"):
        bot.answer_callback_query(call.id, "❌ Нельзя!")
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
    hero_handlers(call)

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
        if player.data["hp"] >= player.data["max_hp"]:
            bot.answer_callback_query(call.id, "❌ Полное HP!")
            return
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + item["heal"])
    
    if "mana_restore" in item:
        player.data["mana"] = min(player.data["max_mana"], player.data["mana"] + item["mana_restore"])
    
    player.data["inventory"].remove(ik)
    player.save()
    
    bot.answer_callback_query(call.id, "✅ Использовано!")
    hero_handlers(call)

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
    hero_handlers(call)

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
В каждом 3 босса!
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
    
    player.data["last_dungeon"] = datetime.now().isoformat()
    player.save()
    
    # Запускаем первого босса
    start_dungeon_boss(call.message.chat.id, call.message.message_id, user_id, dl, 1)

def start_dungeon_boss(chat_id, message_id, user_id, dungeon_level, boss_num):
    boss_names = {
        1: {1: "🐺 Волк-страж", 2: "🕷 Паук-охотник", 3: "💀 Скелет-воин", 4: "🐉 Молодой дракон", 5: "👹 Бес"},
        2: {1: "🐺 Вожак стаи", 2: "🕷 Королева пауков", 3: "💀 Некромант", 4: "🐉 Древний дракон", 5: "👹 Демон"},
        3: {1: "🐺 Альфа-волк", 2: "🕷 Матриарх", 3: "💀 Лич", 4: "🐉 Владыка драконов", 5: "👹 Архидемон"}
    }
    
    boss_name = boss_names.get(boss_num, {}).get(dungeon_level, "Босс")
    boss_level = level_reqs[dungeon_level - 1] * 2 + boss_num * 3
    
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
        "username": f"Boss_{boss_level}", "first_name": boss_name,
        "money": 0, "level": boss_level, "exp": 0, "total_exp": 0,
        "hp": 100, "max_hp": 100, "mana": 50, "max_mana": 50,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000,
        "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Босс", "titles_collected": ["Босс"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    dungeon_progress[str(user_id)] = {
        "dungeon_level": dungeon_level,
        "boss_num": boss_num,
        "max_bosses": 3,
        "reward_per_boss": random.randint(50, 200) * dungeon_level,
        "exp_per_boss": 30 * dungeon_level,
        "boss_name": boss_name
    }
    save_json(DATA_FILES['dungeons'], dungeon_progress)
    
    duel = DuelInstance(user_id, boss_id, "dungeon", 0)
    active_duels[str(user_id)] = duel
    
    bot.edit_message_text(f"⚔ Босс {boss_num}/3: <b>{boss_name}</b>!", chat_id, message_id)
    show_duel_interface(chat_id, message_id, duel, user_id)

# ==================== ТУРНИРЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_tournaments")
def world_tournaments(call):
    if not tournaments.get("active"):
        tournaments["active"] = {
            "name": "Турнир",
            "participants": [],
            "prize_pool": 5000,
            "rounds": [],
            "current_round": 0,
            "status": "registration"
        }
        save_json(DATA_FILES['tournaments'], tournaments)
    
    tour = tournaments["active"]
    text = f"""
<b>🏟 ТУРНИР</b>

<b>{tour['name']}</b>
Участников: {len(tour.get('participants', []))}
Приз: <b>{tour.get('prize_pool', 0)}💰</b>
Статус: {tour.get('status', 'registration')}
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    if tour.get("status") == "registration":
        markup.add(types.InlineKeyboardButton("🏆 Участвовать (500💰)", callback_data="tour_join"))
    markup.add(types.InlineKeyboardButton("📋 Участники", callback_data="tour_list"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
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
    
    player.data["money"] -= 500
    player.save()
    
    participants.append(str(user_id))
    tour["participants"] = participants
    tour["prize_pool"] = tour.get("prize_pool", 0) + 500
    tournaments["active"] = tour
    save_json(DATA_FILES['tournaments'], tournaments)
    
    bot.answer_callback_query(call.id, "✅ Зарегистрированы!")
    world_tournaments(call)

@bot.callback_query_handler(func=lambda call: call.data == "tour_list")
def tour_list(call):
    participants = tournaments.get("active", {}).get("participants", [])
    if not participants:
        bot.answer_callback_query(call.id, "📋 Пусто")
        return
    text = "<b>📋 УЧАСТНИКИ</b>\n\n"
    for i, uid in enumerate(participants, 1):
        p = Player(uid)
        text += f"{i}. {p.data['first_name']} (Lv.{p.data['level']})\n"
    bot.send_message(call.message.chat.id, text)

# ==================== ИВЕНТЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_events")
def world_events(call):
    current = events_data.get("current", {})
    if not current or datetime.fromisoformat(current.get("expires", "2000-01-01")) < datetime.now():
        new_event = {
            "name": random.choice(["🌋 Извержение", "❄ Шторм", "⚡ Гроза", "🌑 Затмение", "✨ Звездопад"]),
            "ench_reward": random.choice(ENCHANT_EFFECTS),
            "ench_chance": random.randint(10, 30),
            "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        events_data["current"] = new_event
        save_json(DATA_FILES['events'], events_data)
        # Рассылка ивента
        for uid in users:
            if not uid.startswith("bot_") and not uid.startswith("boss_"):
                try:
                    bot.send_message(int(uid), f"🌍 <b>НОВЫЙ ИВЕНТ!</b>\n{new_event['name']}\nШанс получить: {new_event['ench_reward']['name']}")
                except:
                    pass
    
    ev = events_data["current"]
    time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
    minutes_left = max(0, time_left.seconds // 60)
    
    text = f"<b>🌍 ИВЕНТ</b>\n<b>{ev['name']}</b>\n✨ {ev['ench_reward']['name']}\n⏰ {minutes_left} мин."
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== ТОП ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_top")
def world_top(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⭐ Уровень", callback_data="top_level"),
        types.InlineKeyboardButton("⚔ Победы", callback_data="top_wins"),
        types.InlineKeyboardButton("💰 Монеты", callback_data="top_money"),
        types.InlineKeyboardButton("🏆 Рейтинг", callback_data="top_rating"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world")
    )
    bot.edit_message_text("<b>📊 ТОП</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def show_top(call):
    cat = call.data.split("_")[1]
    real_users = {k: v for k, v in users.items() if not k.startswith("bot_") and not k.startswith("boss_")}
    
    if cat == "level":
        su = sorted(real_users.items(), key=lambda x: (x[1].get("level", 1), x[1].get("exp", 0)), reverse=True)[:10]
        t = "⭐ УРОВЕНЬ"
    elif cat == "wins":
        su = sorted(real_users.items(), key=lambda x: x[1].get("wins", 0), reverse=True)[:10]
        t = "⚔ ПОБЕДЫ"
    elif cat == "money":
        su = sorted(real_users.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]
        t = "💰 МОНЕТЫ"
    elif cat == "rating":
        su = sorted(real_users.items(), key=lambda x: x[1].get("pvp_rating", 1000), reverse=True)[:10]
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

@bot.callback_query_handler(func=lambda call: call.data in ["world_help", "back_to_world"])
def world_help_back(call):
    if call.data == "world_help":
        text = "<b>ℹ ПОМОЩЬ</b>\n⚔ /duel\n🛒 /shop\n👤 /stats"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data == "back_to_world":
        world_section(call.message)

# ==================== КЛАНЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_clans")
def world_clans(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data.get("clan"):
        clan = clans.get(player.data["clan"], {})
        text = f"<b>🛡 {player.data['clan']}</b>\n👥 {len(clan.get('members', []))} уч.\n💰 Казна: {clan.get('treasury', 0)}💰"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("👥 Участники", callback_data="clan_members"))
        markup.add(types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave"))
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

@bot.message_handler(commands=['sell', 'transfer', 'shop', 'inventory', 'daily', 'stats'])
def misc_commands(message):
    cmd = message.text.split()[0].replace('/', '')
    
    if cmd == "sell":
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
        player.data["inventory"].pop(idx)
        player.save()
        lid = f"{user_id}_{int(time.time())}"
        market_listings[lid] = {"seller_id": user_id, "seller_name": message.from_user.first_name, "item_key": ik, "price": price, "created_at": datetime.now().isoformat()}
        save_json(DATA_FILES['market'], market_listings)
        item = items.get(ik) or limited_items.get(ik)
        bot.send_message(message.chat.id, f"✅ {item.get('name', ik)} за {price}💰!")
    
    elif cmd == "transfer":
        if not message.reply_to_message:
            bot.send_message(message.chat.id, "❌ Ответьте на сообщение!")
            return
        user_id = message.from_user.id
        target_id = message.reply_to_message.from_user.id
        player = Player(user_id)
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

# ==================== АДМИН-ПАНЕЛЬ ====================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("💰 Выдать деньги", callback_data="admin_money"),
        types.InlineKeyboardButton("🎁 Выдать предмет", callback_data="admin_item"),
        types.InlineKeyboardButton("⛔ Бан", callback_data="admin_ban"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🔄 Сброс дня", callback_data="admin_reset"),
        types.InlineKeyboardButton("👁 Инфо игрока", callback_data="admin_info"),
        types.InlineKeyboardButton("✅ Разбан", callback_data="admin_unban"),
        types.InlineKeyboardButton("🏟 Старт турнира", callback_data="admin_tournament"),
        types.InlineKeyboardButton("🌍 Новый ивент", callback_data="admin_event")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_handlers(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Нет доступа!")
        return
    
    action = call.data.split("_")[1]
    
    if action == "stats":
        real_users = {k: v for k, v in users.items() if not k.startswith("bot_") and not k.startswith("boss_")}
        text = f"""
<b>📊 СТАТИСТИКА</b>
👥 Игроков: {len(real_users)}
💰 Монет: {sum(u.get('money',0) for u in real_users.values())}
⚔ Дуэлей: {sum(u.get('total_duels',0) for u in real_users.values())}
🛡 Кланов: {len(clans)}
💎 Лимиток: {sum(v.get('remaining',0) for v in limited_items.values())}
📦 Лотов: {len(market_listings)}
⛔ Банов: {len(banned_users)}
"""
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    
    elif action == "money":
        bot.send_message(call.message.chat.id, "💰 /givemoney @username [сумма]")
    elif action == "item":
        bot.send_message(call.message.chat.id, "🎁 /giveitem @username [item_key]")
    elif action == "ban":
        bot.send_message(call.message.chat.id, "⛔ /ban @username [причина]")
    elif action == "broadcast":
        bot.send_message(call.message.chat.id, "📢 /broadcast [текст]")
    elif action == "reset":
        bot.send_message(call.message.chat.id, "🔄 /resetdaily @username")
    elif action == "info":
        bot.send_message(call.message.chat.id, "👁 /userinfo @username")
    elif action == "unban":
        bot.send_message(call.message.chat.id, "✅ /unban @username")
    elif action == "tournament":
        bot.send_message(call.message.chat.id, "🏟 /starttournament")
    elif action == "event":
        bot.send_message(call.message.chat.id, "🌍 /newevent [название]")

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'broadcast', 'resetdaily', 'userinfo', 'starttournament', 'newevent'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Нет доступа!")
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd == "givemoney":
            username = parts[1].replace('@', '')
            amount = int(parts[2])
            uid = find_user_by_username(username)
            if uid:
                p = Player(uid)
                p.data["money"] += amount
                p.save()
                bot.send_message(message.chat.id, f"✅ {amount}💰 → @{username}")
            else:
                bot.send_message(message.chat.id, f"❌ @{username} не найден!")
        
        elif cmd == "giveitem":
            username = parts[1].replace('@', '')
            ik = parts[2]
            uid = find_user_by_username(username)
            if uid:
                p = Player(uid)
                p.data["inventory"].append(ik)
                p.save()
                bot.send_message(message.chat.id, f"✅ {ik} → @{username}")
            else:
                bot.send_message(message.chat.id, f"❌ @{username} не найден!")
        
        elif cmd == "ban":
            username = parts[1].replace('@', '')
            reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение"
            uid = find_user_by_username(username)
            if uid:
                banned_users[uid] = {"reason": reason, "banned_at": datetime.now().isoformat()}
                save_json(DATA_FILES['bans'], banned_users)
                bot.send_message(message.chat.id, f"⛔ @{username} забанен!")
            else:
                bot.send_message(message.chat.id, f"❌ @{username} не найден!")
        
        elif cmd == "unban":
            username = parts[1].replace('@', '')
            uid = find_user_by_username(username)
            if uid and uid in banned_users:
                del banned_users[uid]
                save_json(DATA_FILES['bans'], banned_users)
                bot.send_message(message.chat.id, f"✅ @{username} разбанен!")
            else:
                bot.send_message(message.chat.id, f"❌ @{username} не найден в бане!")
        
        elif cmd == "broadcast":
            text = message.text.replace('/broadcast', '', 1).strip()
            if text:
                s, f = 0, 0
                for uid in users:
                    if not uid.startswith("bot_") and not uid.startswith("boss_"):
                        try:
                            bot.send_message(int(uid), f"📢 <b>ОБЪЯВЛЕНИЕ:</b>\n{text}")
                            s += 1
                        except:
                            f += 1
                bot.send_message(message.chat.id, f"✅ Отправлено: {s} | ❌ Ошибок: {f}")
        
        elif cmd == "resetdaily":
            username = parts[1].replace('@', '')
            uid = find_user_by_username(username)
            if uid:
                p = Player(uid)
                p.data["last_daily"] = None
                p.data["last_dungeon"] = None
                p.save()
                bot.send_message(message.chat.id, f"✅ Сброс @{username}")
            else:
                bot.send_message(message.chat.id, f"❌ @{username} не найден!")
        
        elif cmd == "userinfo":
            username = parts[1].replace('@', '')
            uid = find_user_by_username(username)
            if uid:
                p = Player(uid)
                d = p.data
                text = f"""
<b>👤 @{username}</b>
ID: {uid}
Имя: {d['first_name']}
Ур.: {d['level']} | 💰 {d['money']}
Рейтинг: {d['pvp_rating']}
Побед: {d['wins']} | Поражений: {d['losses']}
Клан: {d.get('clan', 'Нет')}
Предметов: {len(d['inventory'])}
"""
                bot.send_message(message.chat.id, text)
            else:
                bot.send_message(message.chat.id, f"❌ @{username} не найден!")
        
        elif cmd == "starttournament":
            if tournaments.get("active", {}).get("participants", []):
                tour = tournaments["active"]
                tour["status"] = "in_progress"
                tournaments["active"] = tour
                save_json(DATA_FILES['tournaments'], tournaments)
                bot.send_message(message.chat.id, f"🏟 Турнир начат! Участников: {len(tour['participants'])}")
            else:
                bot.send_message(message.chat.id, "❌ Нет участников!")
        
        elif cmd == "newevent":
            event_name = " ".join(parts[1:]) if len(parts) > 1 else "Специальный ивент"
            new_event = {
                "name": event_name,
                "ench_reward": random.choice(ENCHANT_EFFECTS),
                "ench_chance": random.randint(10, 30),
                "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
            }
            events_data["current"] = new_event
            save_json(DATA_FILES['events'], events_data)
            
            # Рассылка
            for uid in users:
                if not uid.startswith("bot_") and not uid.startswith("boss_"):
                    try:
                        bot.send_message(int(uid), f"🌍 <b>НОВЫЙ ИВЕНТ!</b>\n{event_name}\nШанс получить: {new_event['ench_reward']['name']}")
                    except:
                        pass
            
            bot.send_message(message.chat.id, f"✅ Ивент создан и разослан!")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== ЗАПУСК ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v11.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print("=" * 60)
    print("✅ Пошаговые дуэли: защита → атака → смена ролей")
    print("✅ Броня уменьшает урон по частям тела")
    print("✅ 3 босса в каждом подземелье")
    print("✅ Ивенты с рассылкой всем игрокам")
    print("✅ Админ через @username")
    print("✅ Результаты дуэлей обоим игрокам")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
