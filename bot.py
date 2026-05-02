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
    "head": {"name": "👤 Голова", "multiplier": 1.5, "base_defense": 3},
    "body": {"name": "🦾 Тело", "multiplier": 1.0, "base_defense": 5},
    "legs": {"name": "🦿 Ноги", "multiplier": 0.7, "base_defense": 2}
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
    {"name": "🔥 Огненное", "effect": "burn_on_hit", "value": 25, "description": "+25% шанс поджечь врага"},
    {"name": "❄ Ледяное", "effect": "freeze_on_hit", "value": 20, "description": "+20% шанс заморозить врага"},
    {"name": "⚡ Грозовое", "effect": "stun_on_hit", "value": 15, "description": "+15% шанс оглушить врага"},
    {"name": "💀 Проклятое", "effect": "life_steal", "value": 15, "description": "+15% вампиризма"},
    {"name": "🛡 Укреплённое", "effect": "defense_bonus", "value": 25, "description": "+25 защиты"},
    {"name": "💪 Мощное", "effect": "damage_boost", "value": 35, "description": "+35% урона"},
    {"name": "💨 Скоростное", "effect": "speed_bonus", "value": 20, "description": "+20 скорости"},
    {"name": "❤ Живучее", "effect": "hp_bonus", "value": 80, "description": "+80 HP"},
    {"name": "💎 Магическое", "effect": "mana_bonus", "value": 50, "description": "+50 MP"},
    {"name": "🎯 Меткое", "effect": "crit_bonus", "value": 25, "description": "+25% крита"},
    {"name": "🔮 Мистическое", "effect": "random_buff", "value": 0, "description": "Случайный бафф каждый ход"},
    {"name": "🌿 Природное", "effect": "poison_on_hit", "value": 20, "description": "+20% шанс отравить"},
    {"name": "🩸 Кровавое", "effect": "bleed_on_hit", "value": 18, "description": "+18% шанс кровотечения"},
    {"name": "👁 Всевидящее", "effect": "dodge_ignore", "value": 30, "description": "Игнорирует 30% уклонения"},
    {"name": "🔄 Отражение", "effect": "damage_reflect", "value": 20, "description": "Отражает 20% урона"}
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
    'world_boss': 'world_boss.json',
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

# ==================== ПРЕДМЕТЫ С УНИКАЛЬНЫМИ АТАКАМИ ====================
WEAPONS = {
    "rusty_sword": {
        "name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "rarity": "common", "level_req": 1,
        "skills": [
            {"id": "slash", "name": "Разрез", "mult": 1.2, "mp": 0, "cd": 0, "desc": "Базовый удар мечом"},
            {"id": "quick_strike", "name": "Быстрый удар", "mult": 0.7, "mp": 0, "cd": 0, "desc": "Два быстрых удара", "hits": 2}
        ]
    },
    "hunters_bow": {
        "name": "🏹 Лук охотника", "damage": (7, 14), "price": 150, "type": "weapon", "rarity": "common", "level_req": 3,
        "skills": [
            {"id": "quick_shot", "name": "Быстрый выстрел", "mult": 1.0, "mp": 0, "cd": 0, "desc": "Базовый выстрел"},
            {"id": "power_shot", "name": "Мощный выстрел", "mult": 2.0, "mp": 20, "cd": 3, "desc": "Мощный прицельный выстрел"},
            {"id": "multi_shot", "name": "Залп стрел", "mult": 0.6, "mp": 25, "cd": 3, "desc": "Три стрелы за раз", "hits": 3}
        ]
    },
    "flame_blade": {
        "name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "rarity": "uncommon", "level_req": 7,
        "skills": [
            {"id": "fire_slash_base", "name": "Огненный разрез", "mult": 1.2, "mp": 0, "cd": 0, "desc": "Базовый огненный удар", "burn_chance": 15},
            {"id": "inferno_strike", "name": "Инферно удар", "mult": 2.5, "mp": 30, "cd": 4, "desc": "Мощный огненный удар", "burn_chance": 50},
            {"id": "flame_wave", "name": "Волна пламени", "mult": 2.0, "mp": 35, "cd": 5, "desc": "Огненная волна по всем частям", "aoe": True}
        ]
    },
    "frost_axe": {
        "name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "rarity": "uncommon", "level_req": 10,
        "skills": [
            {"id": "frost_chop", "name": "Ледяной удар", "mult": 1.2, "mp": 0, "cd": 0, "desc": "Базовый ледяной удар", "freeze_chance": 10},
            {"id": "ice_shatter", "name": "Ледяной раскол", "mult": 2.2, "mp": 28, "cd": 4, "desc": "Мощный удар с заморозкой", "freeze_chance": 40},
            {"id": "blizzard", "name": "Метель", "mult": 1.8, "mp": 32, "cd": 5, "desc": "Ледяная буря", "aoe": True, "freeze_chance": 20}
        ]
    },
    "storm_staff": {
        "name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500, "type": "weapon", "rarity": "rare", "level_req": 14,
        "skills": [
            {"id": "spark", "name": "Искра", "mult": 1.1, "mp": 0, "cd": 0, "desc": "Базовый разряд", "stun_chance": 5},
            {"id": "lightning_bolt", "name": "Молния", "mult": 1.8, "mp": 20, "cd": 2, "desc": "Мощный разряд", "stun_chance": 25},
            {"id": "thunder_storm", "name": "Грозовой шторм", "mult": 2.5, "mp": 40, "cd": 5, "desc": "Гроза по всем целям", "aoe": True, "stun_chance": 30},
            {"id": "chain_lightning", "name": "Цепная молния", "mult": 2.0, "mp": 30, "cd": 3, "desc": "Молния с вампиризмом", "life_steal": 0.3}
        ]
    },
    "shadow_dagger": {
        "name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "rarity": "epic", "level_req": 22,
        "skills": [
            {"id": "shadow_cut", "name": "Теневой порез", "mult": 1.3, "mp": 0, "cd": 0, "desc": "Базовый удар из тени", "poison_chance": 10},
            {"id": "assassinate", "name": "Убийство", "mult": 3.5, "mp": 50, "cd": 6, "desc": "Смертельный удар в голову", "ignore_defense": 50},
            {"id": "soul_drain", "name": "Похищение души", "mult": 2.2, "mp": 35, "cd": 4, "desc": "Кража жизни", "life_steal": 0.5},
            {"id": "dark_veil", "name": "Завеса тьмы", "mult": 1.5, "mp": 25, "cd": 3, "desc": "Удар с ослеплением", "dodge_ignore": 40}
        ]
    },
    "divine_spear": {
        "name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "rarity": "legendary", "level_req": 28,
        "skills": [
            {"id": "holy_poke", "name": "Святой укол", "mult": 1.2, "mp": 0, "cd": 0, "desc": "Базовый святой удар", "heal_on_hit": 5},
            {"id": "divine_judgment", "name": "Божий суд", "mult": 3.0, "mp": 45, "cd": 5, "desc": "Мощная святая атака"},
            {"id": "heavenly_light", "name": "Небесный свет", "mult": 0, "mp": 30, "cd": 4, "desc": "Лечение вместо атаки", "hp_restore": 80},
            {"id": "purification", "name": "Очищение", "mult": 1.8, "mp": 35, "cd": 3, "desc": "Снимает отрицательные эффекты"}
        ]
    },
    "death_scythe": {
        "name": "💀 Коса смерти", "damage": (40, 65), "price": 12000, "type": "weapon", "rarity": "mythic", "level_req": 35,
        "skills": [
            {"id": "reap_base", "name": "Жатва", "mult": 1.3, "mp": 0, "cd": 0, "desc": "Базовый удар косой", "life_steal": 0.1},
            {"id": "death_sentence", "name": "Смертный приговор", "mult": 4.5, "mp": 60, "cd": 6, "desc": "УЛЬТИМАТИВНАЯ АТАКА", "ignore_defense": 80},
            {"id": "soul_harvest", "name": "Сбор душ", "mult": 2.8, "mp": 45, "cd": 4, "desc": "Массовый вампиризм", "life_steal": 0.6},
            {"id": "darkness_falls", "name": "Падение тьмы", "mult": 3.2, "mp": 55, "cd": 5, "desc": "Удар с проклятием", "curse_chance": 40}
        ]
    }
}

HELMETS = {
    "leather_cap": {"name": "🎓 Кожаная шапка", "defense": 3, "price": 60, "type": "helmet", "slot": "head", "rarity": "common", "level_req": 1, "skills": []},
    "iron_helmet": {"name": "⛑ Железный шлем", "defense": 8, "price": 250, "type": "helmet", "slot": "head", "rarity": "uncommon", "level_req": 6, "skills": [{"id": "headbutt", "name": "Удар головой", "mult": 1.4, "mp": 10, "cd": 2, "desc": "Атака головой", "stun_chance": 20}]},
    "dragon_helmet": {"name": "🐉 Шлем дракона", "defense": 18, "price": 2000, "type": "helmet", "slot": "head", "rarity": "epic", "level_req": 20, "skills": [{"id": "dragon_roar", "name": "Рёв дракона", "mult": 2.0, "mp": 30, "cd": 4, "desc": "Оглушающий рёв", "stun_chance": 40}]},
    "crown_of_wisdom": {"name": "👑 Корона мудрости", "defense": 12, "price": 3500, "type": "helmet", "slot": "head", "rarity": "legendary", "level_req": 28, "skills": [{"id": "mind_blast", "name": "Ментальный удар", "mult": 2.5, "mp": 35, "cd": 4, "desc": "Психическая атака", "ignore_defense": 30}]}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "defense": 5, "price": 80, "type": "armor", "slot": "body", "rarity": "common", "level_req": 1, "skills": []},
    "chainmail": {"name": "⛓ Кольчуга", "defense": 12, "price": 400, "type": "armor", "slot": "body", "rarity": "uncommon", "level_req": 8, "skills": [{"id": "fortify", "name": "Укрепление", "mult": 0, "mp": 15, "cd": 3, "desc": "+30 защиты на 2 хода", "defense_boost": 30}]},
    "plate_armor": {"name": "🛡 Латный доспех", "defense": 22, "price": 1500, "type": "armor", "slot": "body", "rarity": "rare", "level_req": 15, "skills": [{"id": "iron_will", "name": "Железная воля", "mult": 0, "mp": 20, "cd": 3, "desc": "+40 защиты на 2 хода", "defense_boost": 40}]},
    "shadow_armor": {"name": "🌑 Теневая броня", "defense": 28, "price": 3500, "type": "armor", "slot": "body", "rarity": "epic", "level_req": 22, "skills": [{"id": "shadow_step", "name": "Шаг тени", "mult": 0, "mp": 25, "cd": 3, "desc": "+30% уклонения на 1 ход", "dodge_boost": 30}]},
    "phoenix_armor": {"name": "🦅 Броня феникса", "defense": 40, "price": 8000, "type": "armor", "slot": "body", "rarity": "legendary", "level_req": 30, "skills": [{"id": "rebirth", "name": "Возрождение", "mult": 0, "mp": 50, "cd": 6, "desc": "Полное исцеление", "hp_restore": 100}]}
}

BOOTS = {
    "leather_boots": {"name": "👢 Кожаные сапоги", "defense": 2, "speed": 5, "price": 100, "type": "boots", "slot": "legs", "rarity": "common", "level_req": 1, "skills": []},
    "wind_boots": {"name": "🌪 Сапоги ветра", "defense": 4, "speed": 12, "price": 900, "type": "boots", "slot": "legs", "rarity": "rare", "level_req": 12, "skills": [{"id": "tailwind", "name": "Попутный ветер", "mult": 0, "mp": 15, "cd": 3, "desc": "+15 скорости на 2 хода", "speed_boost": 15}]},
    "blink_boots": {"name": "✨ Сапоги телепортации", "defense": 8, "speed": 20, "price": 4000, "type": "boots", "slot": "legs", "rarity": "epic", "level_req": 25, "skills": [{"id": "blink", "name": "Телепортация", "mult": 0, "mp": 20, "cd": 3, "desc": "Уклонение от атаки", "dodge_boost": 40}]},
    "hermes_boots": {"name": "👟 Сандалии Гермеса", "defense": 12, "speed": 30, "price": 12000, "type": "boots", "slot": "legs", "rarity": "legendary", "level_req": 35, "skills": [{"id": "divine_speed", "name": "Божественная скорость", "mult": 0, "mp": 25, "cd": 3, "desc": "Двойной ход", "double_turn": True}]}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 200, "price": 350, "type": "potion", "rarity": "rare", "level_req": 15},
    "mana_potion": {"name": "💎 Зелье маны", "mana_restore": 60, "price": 60, "type": "potion", "rarity": "common", "level_req": 5},
    "berserk_potion": {"name": "💢 Зелье ярости", "price": 200, "type": "potion", "rarity": "rare", "level_req": 12, "effects": {"damage_boost": 50, "duration": 3}},
    "antidote": {"name": "💚 Противоядие", "price": 100, "type": "potion", "rarity": "common", "level_req": 1, "effects": {"cure_poison": True, "cure_bleed": True}}
}

LIMITED_ITEMS = {
    "thunderfury": {
        "name": "⚡ Ярость грома", "damage": (60, 95), "total": 3, "remaining": 3, "price": 50000,
        "type": "weapon", "rarity": "divine", "level_req": 30,
        "skills": [
            {"id": "thunder_gods_wrath", "name": "Гнев бога грома", "mult": 5.0, "mp": 80, "cd": 6, "desc": "УЛЬТИМАТИВНАЯ АТАКА", "stun_chance": 60, "aoe": True},
            {"id": "eye_of_the_storm", "name": "Глаз бури", "mult": 3.5, "mp": 50, "cd": 4, "desc": "Мощный разряд", "stun_chance": 40},
            {"id": "lightning_apocalypse", "name": "Молниевый апокалипсис", "mult": 4.0, "mp": 65, "cd": 5, "desc": "Цепная молния + вампиризм", "life_steal": 0.4, "aoe": True}
        ]
    },
    "apocalypse": {
        "name": "🌋 Апокалипсис", "damage": (80, 140), "total": 1, "remaining": 1, "price": 100000,
        "type": "weapon", "rarity": "apocalyptic", "level_req": 40,
        "skills": [
            {"id": "world_ender", "name": "Конец света", "mult": 6.0, "mp": 100, "cd": 7, "desc": "АБСОЛЮТНОЕ УНИЧТОЖЕНИЕ", "ignore_defense": 100, "aoe": True},
            {"id": "obliterate", "name": "Уничтожение", "mult": 4.5, "mp": 70, "cd": 5, "desc": "Игнорирует всю защиту", "ignore_defense": 80},
            {"id": "void_annihilation", "name": "Аннигиляция пустоты", "mult": 5.0, "mp": 85, "cd": 6, "desc": "Вампиризм 80%", "life_steal": 0.8}
        ]
    },
    "immortal_helmet": {
        "name": "✨ Шлем бессмертия", "defense": 80, "total": 2, "remaining": 2, "price": 75000,
        "type": "helmet", "slot": "head", "rarity": "divine", "level_req": 35,
        "skills": [
            {"id": "immortality", "name": "Бессмертие", "mult": 0, "mp": 60, "cd": 6, "desc": "Иммунитет к смерти на 2 хода", "death_immune": 2}
        ]
    }
}

ALL_ITEMS = {}
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(BOOTS)
ALL_ITEMS.update(POTIONS)

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
world_boss_data = load_json(DATA_FILES['world_boss'], {"hp": 1000000, "max_hp": 1000000, "name": "🌋 Древний титан", "participants": {}, "total_reward": 50000})
active_battles = load_json(DATA_FILES['active_battles'], {})

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def find_user_by_username(username):
    """Поиск пользователя по username (исправлено)"""
    username = username.replace('@', '').strip().lower()
    for uid, data in users.items():
        stored_username = data.get("username", "").strip().lower()
        if stored_username == username:
            return uid
    # Поиск по first_name если username не найден
    for uid, data in users.items():
        first_name = data.get("first_name", "").strip().lower()
        if first_name == username:
            return uid
    return None

def get_user_display(uid):
    """Получить отображаемое имя пользователя"""
    if uid.startswith("bot_") or uid.startswith("boss_"):
        return users.get(uid, {}).get("first_name", "Противник")
    data = users.get(uid, {})
    uname = data.get("username", "")
    if uname:
        return f"@{uname}"
    return data.get("first_name", f"ID:{uid}")

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
                "title": "Новичок", "titles_collected": ["Новичок"],
                "achievements": [],
                "clan": None, "clan_role": None,
                "registration_date": datetime.now().isoformat(),
                "settings": {"notifications": True, "duel_requests": True},
                "battle_history": [],
                "dungeons_completed": 0, "items_found": 0
            }
            self.save()
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    def save(self):
        save_json(DATA_FILES['users'], users)
    
    def get_equipment_defense(self, slot):
        ik = self.data["equipment"].get(slot)
        if not ik:
            return 0
        item = items.get(ik) or limited_items.get(ik)
        return item.get("defense", 0) if item else 0
    
    def get_all_skills(self):
        """Получить все навыки от всей экипировки"""
        all_skills = []
        for slot in ["weapon", "head", "body", "legs"]:
            ik = self.data["equipment"].get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                if item and "skills" in item:
                    all_skills.extend(item["skills"])
        return all_skills

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
        self.log_p1 = []
        self.log_p2 = []
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        self.p1_hp = 100
        self.p2_hp = 100
        self.p1_max_hp = 100
        self.p2_max_hp = 100
        self.p1_mp = 50
        self.p2_mp = 50
        self.p1_max_mp = 50
        self.p2_max_mp = 50
        
        # Фазы: P1 защищается → P2 атакует → затем наоборот
        self.round_type = "p1_defend_p2_attack"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        self.p1_ready = False
        self.p2_ready = False
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Баффы
        self.p1_buffs = {"defense": 0, "dodge": 0, "damage": 0, "speed": 0}
        self.p2_buffs = {"defense": 0, "dodge": 0, "damage": 0, "speed": 0}
        
        # Статус-эффекты
        self.p1_effects = []
        self.p2_effects = []
        
        # Арена
        arenas = ["🏟 Колизей", "🌲 Лес", "🌋 Вулкан", "❄ Тундра", "🕳 Пустота", "⛪ Храм"]
        self.arena = random.choice(arenas)
        
        msg = f"⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>\n{self.arena}\nХод 1: <b>{get_user_display(p1_id)}</b> защищается, <b>{get_user_display(p2_id)}</b> атакует"
        self.log_p1.append(msg)
        self.log_p2.append(msg)
    
    def _add_log(self, pn, msg):
        if pn == 1:
            self.log_p1.append(msg)
        else:
            self.log_p2.append(msg)
    
    def set_defend(self, player_num, part):
        if player_num == 1:
            self.p1_defend = part
            self._add_log(1, f"🛡 Вы защищаете <b>{BODY_PARTS[part]['name']}</b>")
            self._add_log(2, f"🛡 {get_user_display(self.p1_id)} защищает <b>{BODY_PARTS[part]['name']}</b>")
        else:
            self.p2_defend = part
            self._add_log(2, f"🛡 Вы защищаете <b>{BODY_PARTS[part]['name']}</b>")
            self._add_log(1, f"🛡 {get_user_display(self.p2_id)} защищает <b>{BODY_PARTS[part]['name']}</b>")
        
        # После выбора защиты — атакующий выбирает навык и цель
        self._check_attack_phase()
    
    def _check_attack_phase(self):
        """Проверить, может ли атакующий выбрать действие"""
        pass  # Атакующий выбирает через set_attack
    
    def set_attack(self, player_num, skill_id, target_part):
        """Атакующий выбрал навык и цель"""
        if player_num == 1:
            self.p1_skill = skill_id
            self.p1_target = target_part
        else:
            self.p2_skill = skill_id
            self.p2_target = target_part
        
        # Разрешаем атаку
        if self.round_type == "p1_defend_p2_attack" and self.p1_defend and self.p2_skill:
            self._resolve_attack(2, 1)
            self._switch_round()
        elif self.round_type == "p2_defend_p1_attack" and self.p2_defend and self.p1_skill:
            self._resolve_attack(1, 2)
            self._switch_round()
    
    def _resolve_attack(self, attacker, defender):
        """Разрешить атаку"""
        skill_id = self.p1_skill if attacker == 1 else self.p2_skill
        target_part = self.p1_target if attacker == 1 else self.p2_target
        defend_part = self.p2_defend if attacker == 1 else self.p1_defend
        
        # Найти данные навыка
        attacker_player = self.p1 if attacker == 1 else self.p2
        all_skills = attacker_player.get_all_skills()
        skill_data = None
        for s in all_skills:
            if s["id"] == skill_id:
                skill_data = s
                break
        
        if not skill_data:
            skill_data = {"name": "Атака", "mult": 1.0, "mp": 0, "cd": 0}
        
        # Проверка маны
        mc = skill_data.get("mp", 0)
        if attacker == 1:
            if self.p1_mp < mc:
                self._add_log(1, "❌ Недостаточно маны!")
                self._add_log(2, f"❌ {get_user_display(self.p1_id)} не хватило маны!")
                return
            self.p1_mp -= mc
        else:
            if self.p2_mp < mc:
                self._add_log(2, "❌ Недостаточно маны!")
                self._add_log(1, f"❌ {get_user_display(self.p2_id)} не хватило маны!")
                return
            self.p2_mp -= mc
        
        # Базовый урон
        defender_player = self.p1 if defender == 1 else self.p2
        min_dmg = 10 + attacker_player.data["level"] * 2
        max_dmg = 20 + attacker_player.data["level"] * 3
        base_dmg = random.randint(min_dmg, max_dmg)
        dmg = int(base_dmg * skill_data.get("mult", 1.0))
        
        # Множитель части тела
        body_mult = BODY_PARTS.get(target_part, {}).get("multiplier", 1.0)
        dmg = int(dmg * body_mult)
        
        # Защита цели
        defense_val = defender_player.get_equipment_defense(target_part)
        base_def = BODY_PARTS.get(target_part, {}).get("base_defense", 3)
        total_def = base_def + defense_val
        
        # Снижение урона бронёй
        reduction = total_def / (total_def + 50)
        blocked = int(dmg * reduction)
        dmg = dmg - blocked
        
        # Если цель защищена — доп. снижение
        if defend_part == target_part:
            dmg = int(dmg * 0.4)
            self._add_log(attacker, f"🛡 {get_user_display(defender_player.user_id)} защитил эту часть! Урон снижен.")
            self._add_log(defender, f"🛡 Вы успешно защитили {BODY_PARTS[target_part]['name']}! Урон снижен.")
        
        dmg = max(1, dmg)
        
        # Применение урона
        if defender == 1:
            self.p1_hp = max(0, self.p1_hp - dmg)
        else:
            self.p2_hp = max(0, self.p2_hp - dmg)
        
        # Сообщение об атаке
        atk_name = get_user_display(self.p1_id if attacker == 1 else self.p2_id)
        def_name = get_user_display(self.p1_id if defender == 1 else self.p2_id)
        
        self._add_log(attacker, f"⚔ Вы атаковали [{skill_data['name']}] → {BODY_PARTS[target_part]['name']}: <b>-{dmg} HP</b> (защита: -{blocked})")
        self._add_log(defender, f"💢 {atk_name} атаковал [{skill_data['name']}] → {BODY_PARTS[target_part]['name']}: <b>-{dmg} HP</b>")
        
        # Эффекты
        if "burn_chance" in skill_data and random.random() * 100 < skill_data["burn_chance"]:
            self.p1_effects.append({"type": "burn", "duration": 3}) if defender == 1 else self.p2_effects.append({"type": "burn", "duration": 3})
            self._add_log(defender, "🔥 Горение! -10 HP/ход")
            self._add_log(attacker, f"🔥 {def_name} горит!")
        
        if "freeze_chance" in skill_data and random.random() * 100 < skill_data["freeze_chance"]:
            self._add_log(defender, "❄ Заморозка! Пропуск следующего хода")
            self._add_log(attacker, f"❄ {def_name} заморожен!")
        
        if "stun_chance" in skill_data and random.random() * 100 < skill_data["stun_chance"]:
            self._add_log(defender, "⚡ Оглушение!")
            self._add_log(attacker, f"⚡ {def_name} оглушён!")
        
        if "life_steal" in skill_data:
            heal = int(dmg * skill_data["life_steal"])
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self._add_log(attacker, f"💚 Вампиризм +{heal} HP")
        
        # Лечение
        if "hp_restore" in skill_data:
            heal = skill_data["hp_restore"]
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self._add_log(attacker, f"💚 +{heal} HP")
        
        # Кулдаун
        cd = skill_data.get("cd", 0)
        if cd > 0:
            if attacker == 1:
                self.p1_cooldowns[skill_id] = cd
            else:
                self.p2_cooldowns[skill_id] = cd
        
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
        """Смена ролей"""
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        
        if self.round_type == "p1_defend_p2_attack":
            self.round_type = "p2_defend_p1_attack"
            self._add_log(2, f"🛡 <b>Теперь вы защищаетесь!</b> Выберите часть тела.")
            self._add_log(1, f"⚔ <b>Теперь вы атакуете!</b> Ожидание защиты противника...")
        else:
            self.round_type = "p1_defend_p2_attack"
            self._add_log(1, f"🛡 <b>Теперь вы защищаетесь!</b> Выберите часть тела.")
            self._add_log(2, f"⚔ <b>Теперь вы атакуете!</b> Ожидание защиты противника...")
        
        self.turn += 1
        if self.turn > self.max_turns:
            self.active = False
            self.winner = 0
    
    def get_state_text(self, for_player_id):
        pn = 1 if str(for_player_id) == self.p1_id else 2
        is_defending = (self.round_type == "p1_defend_p2_attack" and pn == 1) or (self.round_type == "p2_defend_p1_attack" and pn == 2)
        
        opp_id = self.p2_id if pn == 1 else self.p1_id
        my_hp = self.p1_hp if pn == 1 else self.p2_hp
        opp_hp = self.p2_hp if pn == 1 else self.p1_hp
        my_mp = self.p1_mp if pn == 1 else self.p2_mp
        
        def bar(val, icon):
            pct = val / 100 * 100
            f = int(pct / 10)
            e = 10 - f
            return f"{icon} [{'█'*f}{'░'*e}] {val}/100"
        
        text = f"<b>⚔ ДУЭЛЬ #{self.battle_id}</b>\n{self.arena}\nХод: <b>{self.turn}</b> | Ставка: <b>{self.bet}💰</b>\n\n"
        text += f"<b>Вы:</b> {bar(my_hp, '❤')} | MP: {my_mp}/50\n"
        text += f"<b>{get_user_display(opp_id)}:</b> {bar(opp_hp, '❤')}\n"
        
        if is_defending:
            text += "\n🛡 <b>Вы защищаетесь!</b> Выберите часть тела:"
        else:
            text += "\n⚔ <b>Вы атакуете!</b> Выберите цель и навык:"
        
        my_log = self.log_p1 if pn == 1 else self.log_p2
        if my_log:
            text += f"\n\n<i>{my_log[-1][:150]}</i>"
        
        return text
    
    def get_available_skills(self, player_num):
        player = self.p1 if player_num == 1 else self.p2
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        all_skills = player.get_all_skills()
        
        available = []
        for s in all_skills:
            cd = cooldowns.get(s["id"], 0)
            if cd <= 0:
                available.append(s)
        
        return available

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

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    if str(user_id) in banned_users:
        bot.send_message(message.chat.id, "⛔ Вы забанены!")
        return
    
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or "Игрок"
    
    if str(user_id) in users:
        users[str(user_id)]["username"] = username
        users[str(user_id)]["first_name"] = first_name
        save_json(DATA_FILES['users'], users)
    else:
        Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v12.0 ⚔️</b>

Привет, <b>{first_name}</b>!

🎯 <b>НОВОЕ:</b>
• Пошаговые дуэли с защитой и атакой
• Броня реально снижает урон
• Уникальные навыки у каждого предмета
• Кулдауны на мощные атаки
• Мировой босс 1 000 000 HP
• Ивенты с зачарованиями

💰 Старт: <b>500 монет</b>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль", callback_data="quick_duel"),
        types.InlineKeyboardButton("👥 Найти соперника", callback_data="find_opponent"),
        types.InlineKeyboardButton("🐉 Мировой босс", callback_data="world_boss_fight")
    )
    bot.send_message(message.chat.id, "<b>⚔️ ДУЭЛИ</b>\n\nВыберите тип:", reply_markup=markup)

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
        types.InlineKeyboardButton("🐉 Мировой босс", callback_data="world_boss"),
        types.InlineKeyboardButton("📊 Топ", callback_data="world_top"),
        types.InlineKeyboardButton("ℹ Помощь", callback_data="world_help")
    )
    bot.send_message(message.chat.id, "<b>🌍 МИР</b>", reply_markup=markup)

# ==================== ДУЭЛИ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["quick_duel", "find_opponent"])
def duel_start_handler(call):
    if call.data == "quick_duel":
        show_quick_duel_menu(call)
    elif call.data == "find_opponent":
        start_pvp_matchmaking(call)

def show_quick_duel_menu(call):
    user_id = call.from_user.id
    player = Player(user_id)
    markup = types.InlineKeyboardMarkup(row_width=3)
    for bet in [50, 100, 200, 500, 1000]:
        markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"qduel_{bet}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_duel_menu"))
    bot.edit_message_text(f"<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n💰 {player.data['money']}💰\nВыберите ставку:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_duel_menu")
def back_duel_menu(call):
    duel_section(call.message)

def start_pvp_matchmaking(call):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if player.data["money"] < 50:
        bot.answer_callback_query(call.id, "❌ Нужно 50💰!")
        return
    
    queue = matchmaking_queue.get("pvp", [])
    queue = [q for q in queue if q["user_id"] != user_id]
    
    if queue:
        opponent = queue.pop(0)
        matchmaking_queue["pvp"] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        player.data["money"] -= 50
        opponent_player = Player(opponent["user_id"])
        opponent_player.data["money"] -= 50
        player.save()
        opponent_player.save()
        
        duel = DuelInstance(opponent["user_id"], user_id, "pvp", 50)
        active_duels[user_id] = duel
        active_duels[opponent["user_id"]] = duel
        
        bot.edit_message_text("⚔ Соперник найден!", call.message.chat.id, call.message.message_id)
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        
        try:
            opp_msg = bot.send_message(int(opponent["user_id"]), "⚔ Дуэль начинается!")
            show_duel_interface(int(opponent["user_id"]), opp_msg.message_id, duel, opponent["user_id"])
        except:
            pass
    else:
        queue.append({"user_id": user_id, "bet": 50})
        matchmaking_queue["pvp"] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        bot.edit_message_text("🔍 Поиск соперника... (7 сек)", call.message.chat.id, call.message.message_id)
        threading.Timer(7.0, start_bot_duel_timeout, args=[call.message.chat.id, call.message.message_id, user_id]).start()

def start_bot_duel_timeout(chat_id, message_id, user_id):
    if str(user_id) in active_duels:
        return
    start_bot_duel(chat_id, message_id, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def quick_duel_bet(call):
    bet = int(call.data.split("_")[1])
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    start_bot_duel(call.message.chat.id, call.message.message_id, user_id, "quick", bet)

def start_bot_duel(chat_id, message_id, user_id, duel_type="quick", bet=50):
    player = Player(user_id)
    
    if bet > 0:
        if player.data["money"] < bet:
            try:
                bot.edit_message_text(f"❌ Недостаточно монет!", chat_id, message_id)
            except:
                pass
            return
        player.data["money"] -= bet
        player.save()
    
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
    
    duel = DuelInstance(user_id, bot_id, duel_type, bet)
    active_duels[str(user_id)] = duel
    
    # Бот выбирает защиту
    bot_def = random.choice(list(BODY_PARTS.keys()))
    duel.set_defend(2, bot_def)
    
    try:
        bot.edit_message_text("⚔ Бой с ботом!", chat_id, message_id)
    except:
        pass
    
    show_duel_interface(chat_id, message_id, duel, user_id)

def show_duel_interface(chat_id, message_id, duel, user_id):
    if not duel.active:
        finish_duel(chat_id, message_id, duel, user_id)
        return
    
    state_text = duel.get_state_text(user_id)
    pn = 1 if str(user_id) == duel.p1_id else 2
    is_defending = (duel.round_type == "p1_defend_p2_attack" and pn == 1) or (duel.round_type == "p2_defend_p1_attack" and pn == 2)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if is_defending:
        for part, data in BODY_PARTS.items():
            player = duel.p1 if pn == 1 else duel.p2
            defense = player.get_equipment_defense(part)
            base_def = data["base_defense"]
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']} (DEF:{base_def + defense})",
                callback_data=f"duel_def_{part}"
            ))
    else:
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🎯 {data['name']} (x{data['multiplier']})",
                callback_data=f"duel_tgt_{part}"
            ))
    
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="duel_surr"))
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="duel_upd"))
    
    try:
        bot.edit_message_text(state_text[:4000], chat_id, message_id, reply_markup=markup)
    except:
        try:
            bot.send_message(chat_id, state_text[:4000], reply_markup=markup)
        except:
            pass

temp_data = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_tgt_"))
def duel_target_pick(call):
    user_id = call.from_user.id
    part = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.answer_callback_query(call.id, "❌ Дуэль не найдена")
        return
    
    temp_data[str(user_id)] = {"target": part}
    pn = 1 if str(user_id) == duel.p1_id else 2
    skills = duel.get_available_skills(pn)
    
    state_text = duel.get_state_text(user_id) + f"\n\n🎯 Цель: <b>{BODY_PARTS[part]['name']}</b>\n<b>Выберите навык:</b>"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for s in skills[:8]:
        cd_text = f" | CD:{s.get('cd', 0)}" if s.get("cd", 0) > 0 else ""
        markup.add(types.InlineKeyboardButton(
            f"{s['name']} (x{s.get('mult', 1.0)}) [{s.get('mp', 0)}MP]{cd_text}\n{s.get('desc', '')[:30]}",
            callback_data=f"duel_sk_{s['id']}"
        ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="duel_back_tgt"))
    
    try:
        bot.edit_message_text(state_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "duel_back_tgt")
def duel_back_target(call):
    duel = active_duels.get(str(call.from_user.id))
    if duel:
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, call.from_user.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_sk_"))
def duel_skill_pick(call):
    user_id = call.from_user.id
    skill_id = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.answer_callback_query(call.id, "❌ Дуэль не найдена")
        return
    
    target = temp_data.get(str(user_id), {}).get("target", "body")
    pn = 1 if str(user_id) == duel.p1_id else 2
    
    duel.set_attack(pn, skill_id, target)
    
    # Ход бота
    other_pn = 3 - pn
    if str(duel.p2_id).startswith("bot_") and other_pn == 2:
        if duel.round_type == "p1_defend_p2_attack":
            time.sleep(0.5)
            bot_skills = duel.get_available_skills(2)
            if bot_skills:
                duel.set_attack(2, random.choice(bot_skills)["id"], random.choice(list(BODY_PARTS.keys())))
        else:
            duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
    
    bot.answer_callback_query(call.id, "⚔ Атака!")
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_def_"))
def duel_defend_pick(call):
    user_id = call.from_user.id
    part = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.answer_callback_query(call.id, "❌ Дуэль не найдена")
        return
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    duel.set_defend(pn, part)
    
    # Ход бота (атака)
    other_pn = 3 - pn
    if str(duel.p2_id).startswith("bot_") and other_pn == 2:
        if duel.round_type == "p1_defend_p2_attack":
            time.sleep(0.5)
            bot_skills = duel.get_available_skills(2)
            if bot_skills:
                duel.set_attack(2, random.choice(bot_skills)["id"], random.choice(list(BODY_PARTS.keys())))
    
    bot.answer_callback_query(call.id, f"🛡 {BODY_PARTS[part]['name']}")
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data in ["duel_upd", "duel_surr"])
def duel_misc(call):
    user_id = call.from_user.id
    duel = active_duels.get(str(user_id))
    
    if call.data == "duel_upd":
        if duel and duel.active:
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
            bot.answer_callback_query(call.id, "✅")
        else:
            bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
    
    elif call.data == "duel_surr":
        if duel and duel.active:
            duel.active = False
            duel.winner = 2 if str(user_id) == duel.p1_id else 1
            finish_duel(call.message.chat.id, call.message.message_id, duel, user_id)

def finish_duel(chat_id, message_id, duel, for_user_id=None):
    for uid in [duel.p1_id, duel.p2_id]:
        if uid in active_duels and active_duels[uid].battle_id == duel.battle_id:
            del active_duels[uid]
    
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") and uid in users:
            del users[uid]
    save_json(DATA_FILES['users'], users)
    
    p1_name = get_user_display(duel.p1_id)
    p2_name = get_user_display(duel.p2_id)
    
    if duel.winner == 0:
        result = f"🤝 <b>НИЧЬЯ!</b>\n{p1_name} vs {p2_name}"
    elif duel.winner == 1:
        result = f"👑 <b>{p1_name}</b> побеждает!\n💀 {p2_name} проигрывает"
    else:
        result = f"👑 <b>{p2_name}</b> побеждает!\n💀 {p1_name} проигрывает"
    
    result_text = f"<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>\n\n{result}\n💰 Ставка: {duel.bet}💰\n📊 Ходов: {duel.turn}"
    
    if duel.winner != 0:
        wid = duel.p1_id if duel.winner == 1 else duel.p2_id
        lid = duel.p2_id if duel.winner == 1 else duel.p1_id
        
        if not wid.startswith("bot_"):
            w = Player(wid)
            if duel.bet > 0:
                w.data["money"] += duel.bet * 2
            w.data["wins"] += 1
            w.data["win_streak"] += 1
            w.data["total_duels"] += 1
            w.data["pvp_rating"] += random.randint(15, 30)
            if w.data["win_streak"] > w.data["best_streak"]:
                w.data["best_streak"] = w.data["win_streak"]
            exp_w = duel.turn * 8 + duel.bet // 2
            w.data["exp"] += exp_w
            w.data["total_exp"] += exp_w
            check_level_up(w)
            w.save()
        
        if not lid.startswith("bot_"):
            l = Player(lid)
            l.data["losses"] += 1
            l.data["win_streak"] = 0
            l.data["total_duels"] += 1
            check_level_up(l)
            l.save()
    
    try:
        bot.edit_message_text(result_text, chat_id, message_id)
    except:
        pass
    
    # Отправляем второму игроку
    other_id = duel.p2_id if str(for_user_id) == duel.p1_id else duel.p1_id
    if not other_id.startswith("bot_"):
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
        types.InlineKeyboardButton("◀ Назад", callback_data="back_trade_menu")
    )
    player = Player(call.from_user.id)
    bot.edit_message_text(f"<b>🛒 МАГАЗИН</b>\n💰 <b>{player.data['money']}💰</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_trade_menu")
def back_trade_menu(call):
    trade_section(call.message)

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
            if "skills" in item:
                s += f" | Навыков: {len(item['skills'])}"
        elif item.get("type") in ["helmet", "armor", "boots"]:
            s = f"Защита: {item.get('defense', 0)}"
            if "skills" in item and item["skills"]:
                s += f" | Навык: {item['skills'][0]['name']}"
        elif item.get("type") == "potion":
            s = f"Лечение: {item.get('heal', 0)}"
        else:
            s = ""
        
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

@bot.callback_query_handler(func=lambda call: call.data in ["trade_limited", "trade_daily", "trade_market", "trade_sell", "trade_my_lots"])
def trade_handlers(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
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
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_trade_menu"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "trade_daily":
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
            bot.edit_message_text("📦 Рынок пуст", call.message.chat.id, call.message.message_id)
            return
        text = "<b>💱 РЫНОК</b>\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for lid, listing in list(market_listings.items())[:10]:
            item = items.get(listing["item_key"]) or limited_items.get(listing["item_key"])
            if item:
                text += f"📦 {item['name']} — <b>{listing['price']}💰</b>\n   👤 {listing.get('seller_name', 'Нет')}\n\n"
                markup.add(types.InlineKeyboardButton(f"Купить: {item['name']}", callback_data=f"mktbuy_{lid}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_trade_menu"))
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
                markup.add(types.InlineKeyboardButton(f"Снять: {item['name']}", callback_data=f"remlot_{lid}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_trade_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

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
    trade_handlers(call)

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
    trade_handlers(call)

# ==================== ГЕРОЙ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["hero_stats", "hero_inventory", "hero_achievements", "hero_enchantments", "hero_equipped", "hero_heal", "back_hero_menu"])
def hero_handlers(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "hero_stats":
        d = player.data
        wr = (d["wins"] / d["total_duels"] * 100) if d["total_duels"] > 0 else 0
        text = f"<b>📊 {d['first_name']}</b> | {d['title']}\n⭐ Ур.{d['level']} | 📊 {d['pvp_rating']}\n💰 {d['money']}💰\n🏆 Побед: {d['wins']} | 💀 Поражений: {d['losses']}\n📈 Винрейт: {wr:.1f}%"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_hero_menu"))
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
            eq = ""
            for slot, ek in player.data["equipment"].items():
                if ek == ik:
                    eq = f" [🟢 {slot}]"
            ench = player.data.get("enchantments", {}).get(ik, {})
            ench_text = f" ✨{ench.get('name', '')}" if ench else ""
            text += f"{idx}. {r} {item['name']} x{cnt}{eq}{ench_text}\n"
            if item.get("type") in ["weapon", "helmet", "armor", "boots"]:
                markup.add(types.InlineKeyboardButton(f"Экипировать: {item['name']}", callback_data=f"hequip_{ik}"))
            if item.get("type") == "potion":
                markup.add(types.InlineKeyboardButton(f"Использовать: {item['name']}", callback_data=f"heuse_{ik}"))
            idx += 1
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_hero_menu"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_equipped":
        equip = player.data["equipment"]
        text = "<b>👁 ЭКИПИРОВКА</b>\n\n"
        slot_names = {"weapon": "⚔ Оружие", "head": "👤 Голова", "body": "🦾 Тело", "legs": "🦿 Ноги"}
        for slot, sn in slot_names.items():
            ik = equip.get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                text += f"{sn}: <b>{item['name']}</b> (DEF:{item.get('defense', 0)})\n" if item else f"{sn}: ❌\n"
            else:
                text += f"{sn}: ❌\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔴 Снять всё", callback_data="heunequip"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_hero_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_heal":
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
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_hero_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_achievements":
        ach_list = [("first_blood", "🩸 Первая кровь", player.data["wins"] >= 1), ("warrior", "⚔ Воин", player.data["wins"] >= 10), ("rich", "💰 Богач", player.data["money"] >= 10000)]
        text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(player.data['achievements'])}/3)\n\n"
        for aid, name, cond in ach_list:
            done = aid in player.data["achievements"] or cond
            text += f"{'✅' if done else '🔒'} <b>{name}</b>\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_hero_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "back_hero_menu":
        hero_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("hequip_"))
def hero_equip(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    item = items.get(ik) or limited_items.get(ik)
    if not item or ik not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌ Нельзя!"); return
    slot_map = {"weapon": "weapon", "helmet": "head", "armor": "body", "boots": "legs"}
    slot = slot_map.get(item.get("type"))
    if not slot:
        bot.answer_callback_query(call.id, "❌ Нельзя!"); return
    old = player.data["equipment"][slot]
    if old:
        player.data["inventory"].append(old)
    player.data["equipment"][slot] = ik
    player.data["inventory"].remove(ik)
    player.save()
    bot.answer_callback_query(call.id, f"✅ {item['name']}!")
    hero_handlers(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("heuse_"))
def hero_use(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    item = items.get(ik) or limited_items.get(ik)
    if not item or item.get("type") != "potion":
        bot.answer_callback_query(call.id, "❌ Нельзя!"); return
    if "heal" in item:
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + item["heal"])
    if "mana_restore" in item:
        player.data["mana"] = min(player.data["max_mana"], player.data["mana"] + item["mana_restore"])
    player.data["inventory"].remove(ik)
    player.save()
    bot.answer_callback_query(call.id, "✅ Использовано!")
    hero_handlers(call)

@bot.callback_query_handler(func=lambda call: call.data == "heunequip")
def hero_unequip(call):
    user_id = call.from_user.id
    player = Player(user_id)
    for slot in ["weapon", "head", "body", "legs"]:
        ik = player.data["equipment"][slot]
        if ik:
            player.data["inventory"].append(ik)
            player.data["equipment"][slot] = None
    player.save()
    bot.answer_callback_query(call.id, "✅ Снято!")
    hero_handlers(call)

# ==================== МИР ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_dungeons")
def world_dungeons(call):
    text = "<b>🏰 ПОДЗЕМЕЛЬЯ</b>\n\n🐺 Логово волка (Ур.1+)\n🕷 Паучьи пещеры (Ур.5+)\n💀 Катакомбы (Ур.10+)\n🐉 Драконье логово (Ур.15+)\n👹 Бездна (Ур.25+)\n\nПо 3 босса в каждом!"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, name in enumerate(["🐺 Логово волка", "🕷 Паучьи пещеры", "💀 Катакомбы", "🐉 Драконье логово", "👹 Бездна"], 1):
        markup.add(types.InlineKeyboardButton(name, callback_data=f"dung_{i}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_world_menu"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_world_menu")
def back_world_menu(call):
    world_section(call.message)

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
    start_dungeon_boss(call.message.chat.id, call.message.message_id, user_id, dl, 1)

def start_dungeon_boss(chat_id, message_id, user_id, dungeon_level, boss_num):
    boss_names = {
        1: {1: "🐺 Волк-страж", 2: "🐺 Вожак стаи", 3: "🐺 Альфа-волк"},
        2: {1: "🕷 Паук-охотник", 2: "🕷 Королева", 3: "🕷 Матриарх"},
        3: {1: "💀 Скелет", 2: "💀 Некромант", 3: "💀 Лич"},
        4: {1: "🐉 Молодой дракон", 2: "🐉 Древний дракон", 3: "🐉 Владыка"},
        5: {1: "👹 Бес", 2: "👹 Демон", 3: "👹 Архидемон"}
    }
    boss_name = boss_names.get(dungeon_level, {}).get(boss_num, "Босс")
    boss_level = level_reqs[dungeon_level - 1] * 2 + boss_num * 3
    boss_id = f"boss_{random.randint(100000, 999999)}"
    
    equip = {"weapon": random.choice([k for k, v in items.items() if v.get("type") == "weapon"]) or None,
             "head": None, "body": None, "legs": None}
    for slot, itype in [("head", "helmet"), ("body", "armor"), ("legs", "boots")]:
        sitems = [k for k, v in items.items() if v.get("type") == itype]
        if sitems:
            equip[slot] = random.choice(sitems)
    
    users[boss_id] = {"username": f"Boss_{boss_level}", "first_name": boss_name, "money": 0, "level": boss_level, "exp": 0, "total_exp": 0, "hp": 100, "max_hp": 100, "mana": 50, "max_mana": 50, "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0, "total_duels": 0, "pvp_rating": 1000, "inventory": [], "equipment": equip, "enchantments": {}, "last_daily": None, "last_dungeon": None, "title": "Босс", "titles_collected": ["Босс"], "achievements": [], "clan": None, "clan_role": None, "registration_date": datetime.now().isoformat(), "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0}
    save_json(DATA_FILES['users'], users)
    
    dungeon_progress[str(user_id)] = {"dungeon_level": dungeon_level, "boss_num": boss_num, "max_bosses": 3}
    save_json(DATA_FILES['dungeons'], dungeon_progress)
    
    duel = DuelInstance(user_id, boss_id, "dungeon", 0)
    active_duels[str(user_id)] = duel
    
    duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
    
    bot.edit_message_text(f"⚔ Босс {boss_num}/3: <b>{boss_name}</b>!", chat_id, message_id)
    show_duel_interface(chat_id, message_id, duel, user_id)

# ==================== МИРОВОЙ БОСС ====================
@bot.callback_query_handler(func=lambda call: call.data in ["world_boss", "world_boss_fight"])
def world_boss_handler(call):
    wb = world_boss_data
    
    if call.data == "world_boss_fight":
        user_id = call.from_user.id
        dmg = random.randint(100, 500) * (Player(user_id).data["level"])
        wb["hp"] = max(0, wb["hp"] - dmg)
        wb["participants"][str(user_id)] = wb["participants"].get(str(user_id), 0) + dmg
        world_boss_data.update(wb)
        save_json(DATA_FILES['world_boss'], world_boss_data)
        
        hp_pct = wb["hp"] / wb["max_hp"] * 100
        text = f"<b>🐉 МИРОВОЙ БОСС</b>\n\n<b>{wb['name']}</b>\n❤ HP: {wb['hp']:,} / {wb['max_hp']:,} ({hp_pct:.1f}%)\n\nВы нанесли: <b>{dmg}</b> урона!\nВаш общий урон: <b>{wb['participants'].get(str(user_id), 0):,}</b>"
        
        if wb["hp"] <= 0:
            # Определение победителя
            top_dmg = max(wb["participants"].items(), key=lambda x: x[1])
            winner = Player(top_dmg[0])
            reward = wb["total_reward"]
            winner.data["money"] += reward
            winner.save()
            
            text += f"\n\n🎉 <b>БОСС ПОВЕРЖЕН!</b>\nПобедитель: <b>{get_user_display(top_dmg[0])}</b>\nНаграда: <b>{reward}💰</b>"
            
            # Сброс босса
            world_boss_data["hp"] = 1000000
            world_boss_data["max_hp"] = 1000000
            world_boss_data["participants"] = {}
            world_boss_data["total_reward"] = random.randint(30000, 100000)
            world_boss_data["name"] = random.choice(["🌋 Древний титан", "🐉 Мировой змей", "👹 Князь тьмы", "⚡ Громовой великан"])
            save_json(DATA_FILES['world_boss'], world_boss_data)
            
            # Рассылка всем
            for uid in users:
                if not uid.startswith("bot_") and not uid.startswith("boss_"):
                    try:
                        bot.send_message(int(uid), f"🎉 <b>МИРОВОЙ БОСС ПОВЕРЖЕН!</b>\n{world_boss_data['name']}\nПобедитель: <b>{get_user_display(top_dmg[0])}</b>\nНаграда: {reward}💰")
                    except:
                        pass
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚔ Атаковать ещё!", callback_data="world_boss_fight"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_world_menu"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    else:
        hp_pct = wb["hp"] / wb["max_hp"] * 100
        text = f"<b>🐉 МИРОВОЙ БОСС</b>\n\n<b>{wb['name']}</b>\n❤ HP: {wb['hp']:,} / {wb['max_hp']:,} ({hp_pct:.1f}%)\n🏆 Награда: <b>{wb['total_reward']}💰</b>\n\nТоп-5 по урону:\n"
        top = sorted(wb["participants"].items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (uid, dmg) in enumerate(top, 1):
            text += f"{i}. {get_user_display(uid)}: {dmg:,}\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚔ Атаковать!", callback_data="world_boss_fight"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_world_menu"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== ИВЕНТЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_events")
def world_events(call):
    current = events_data.get("current", {})
    if not current or datetime.fromisoformat(current.get("expires", "2000-01-01")) < datetime.now():
        new_event = {
            "name": random.choice(["🌋 Извержение", "❄ Ледяной шторм", "⚡ Грозовой фронт", "🌑 Затмение", "✨ Звездопад"]),
            "ench_reward": random.choice(ENCHANT_EFFECTS),
            "ench_chance": random.randint(15, 35),
            "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        events_data["current"] = new_event
        save_json(DATA_FILES['events'], events_data)
        # Рассылка
        for uid in users:
            if not uid.startswith("bot_") and not uid.startswith("boss_"):
                try:
                    bot.send_message(int(uid), f"🌍 <b>НОВЫЙ ИВЕНТ!</b>\n{new_event['name']}\n🎁 Шанс: {new_event['ench_reward']['name']}\n⏰ 10 минут!")
                except:
                    pass
    
    ev = events_data["current"]
    time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
    minutes_left = max(0, time_left.seconds // 60)
    
    text = f"<b>🌍 ИВЕНТ</b>\n<b>{ev['name']}</b>\n🎁 {ev['ench_reward']['name']}: {ev['ench_reward']['description']}\n🎲 Шанс: {ev['ench_chance']}%\n⏰ {minutes_left} мин."
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_world_menu"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== ТУРНИРЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_tournaments")
def world_tournaments(call):
    if not tournaments.get("active"):
        tournaments["active"] = {"name": "Турнир", "participants": [], "prize_pool": 5000, "status": "registration"}
        save_json(DATA_FILES['tournaments'], tournaments)
    tour = tournaments["active"]
    text = f"<b>🏟 ТУРНИР</b>\n<b>{tour['name']}</b>\nУчастников: {len(tour.get('participants', []))}\nПриз: <b>{tour.get('prize_pool', 0)}💰</b>\nСтатус: {tour.get('status', 'registration')}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    if tour.get("status") == "registration":
        markup.add(types.InlineKeyboardButton("🏆 Участвовать (500💰)", callback_data="tour_join"))
    markup.add(types.InlineKeyboardButton("📋 Участники", callback_data="tour_list"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_world_menu"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "tour_join")
def tour_join(call):
    user_id = call.from_user.id
    player = Player(user_id)
    if player.data["money"] < 500:
        bot.answer_callback_query(call.id, "❌ 500💰!"); return
    tour = tournaments.get("active", {})
    if str(user_id) in tour.get("participants", []):
        bot.answer_callback_query(call.id, "❌ Уже участвуете!"); return
    player.data["money"] -= 500
    player.save()
    tour["participants"] = tour.get("participants", []) + [str(user_id)]
    tour["prize_pool"] = tour.get("prize_pool", 0) + 500
    tournaments["active"] = tour
    save_json(DATA_FILES['tournaments'], tournaments)
    bot.answer_callback_query(call.id, "✅ Зарегистрированы!")

@bot.callback_query_handler(func=lambda call: call.data == "tour_list")
def tour_list(call):
    participants = tournaments.get("active", {}).get("participants", [])
    if not participants:
        bot.answer_callback_query(call.id, "📋 Пусто"); return
    text = "<b>📋 УЧАСТНИКИ</b>\n\n"
    for i, uid in enumerate(participants, 1):
        text += f"{i}. {get_user_display(uid)}\n"
    bot.send_message(call.message.chat.id, text)

# ==================== ТОП ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_top")
def world_top(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("⭐ Уровень", callback_data="top_level"), types.InlineKeyboardButton("⚔ Победы", callback_data="top_wins"), types.InlineKeyboardButton("💰 Монеты", callback_data="top_money"), types.InlineKeyboardButton("◀ Назад", callback_data="back_world_menu"))
    bot.edit_message_text("<b>📊 ТОП</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def show_top(call):
    cat = call.data.split("_")[1]
    real = {k: v for k, v in users.items() if not k.startswith("bot_") and not k.startswith("boss_")}
    if cat == "level":
        su = sorted(real.items(), key=lambda x: (x[1].get("level", 1), x[1].get("exp", 0)), reverse=True)[:10]
        t = "⭐ УРОВЕНЬ"
    elif cat == "wins":
        su = sorted(real.items(), key=lambda x: x[1].get("wins", 0), reverse=True)[:10]
        t = "⚔ ПОБЕДЫ"
    elif cat == "money":
        su = sorted(real.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]
        t = "💰 МОНЕТЫ"
    else:
        return
    medals = ["🥇", "🥈", "🥉"] + [f"{i}️⃣" for i in range(4, 11)]
    text = f"<b>{t}</b>\n\n"
    for i, (uid, data) in enumerate(su):
        text += f"{medals[i]} {get_user_display(uid)}: {data.get('level', 1) if cat == 'level' else data.get('wins', 0) if cat == 'wins' else data.get('money', 0)}\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_top"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== КЛАНЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_clans")
def world_clans(call):
    user_id = call.from_user.id
    player = Player(user_id)
    if player.data.get("clan"):
        clan = clans.get(player.data["clan"], {})
        text = f"<b>🛡 {player.data['clan']}</b>\n👥 {len(clan.get('members', []))} уч.\n💰 Казна: {clan.get('treasury', 0)}💰"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave"))
    else:
        text = "<b>🛡 КЛАНЫ</b>\n/createclan [имя]\n/joinclan [имя]"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("📋 Список", callback_data="clan_list"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_world_menu"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(commands=['createclan', 'joinclan'])
def clan_commands(message):
    cmd = message.text.split()[0].replace('/', '')
    user_id = message.from_user.id
    player = Player(user_id)
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
        player.data["money"] -= 5000
        player.data["clan"] = name
        player.data["clan_role"] = "leader"
        player.save()
        clans[name] = {"leader_id": user_id, "leader_name": message.from_user.first_name, "members": [message.from_user.first_name], "treasury": 0, "created_at": datetime.now().isoformat()}
        save_json(DATA_FILES['clans'], clans)
        bot.send_message(message.chat.id, f"✅ Клан <b>{name}</b> создан!")
    elif cmd == "joinclan":
        if player.data.get("clan"):
            bot.send_message(message.chat.id, "❌ Уже в клане!"); return
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ /joinclan [имя]"); return
        name = parts[1].strip()
        if name not in clans:
            bot.send_message(message.chat.id, "❌ Не найден!"); return
        player.data["clan"] = name
        player.data["clan_role"] = "member"
        player.save()
        if message.from_user.first_name not in clans[name].get("members", []):
            clans[name]["members"].append(message.from_user.first_name)
        save_json(DATA_FILES['clans'], clans)
        bot.send_message(message.chat.id, f"✅ Вы в <b>{name}</b>!")

# ==================== ПОМОЩЬ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_help")
def world_help(call):
    text = "<b>ℹ ПОМОЩЬ</b>\n⚔ /duel\n🛒 /shop\n👤 /stats\n🐉 /boss — мировой босс"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_world_menu"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

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
        titles = {5: "Боец", 10: "Воитель", 15: "Рыцарь", 20: "Ветеран", 25: "Мастер", 30: "Грандмастер", 40: "Герой", 50: "Легенда"}
        for req, title in titles.items():
            if player.data["level"] >= req and title not in player.data["titles_collected"]:
                player.data["titles_collected"].append(title)
                player.data["title"] = title
        level = player.data["level"]
        exp_needed = int(100 * (1.5 ** (level - 1)))
        leveled = True
    return leveled

@bot.message_handler(commands=['sell', 'shop', 'inventory', 'daily', 'stats', 'boss'])
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
            bot.send_message(message.chat.id, "❌ /sell [номер] [цена]"); return
        if idx < 0 or idx >= len(player.data["inventory"]):
            bot.send_message(message.chat.id, "❌ Неверный номер!"); return
        ik = player.data["inventory"][idx]
        player.data["inventory"].pop(idx)
        player.save()
        lid = f"{user_id}_{int(time.time())}"
        market_listings[lid] = {"seller_id": user_id, "seller_name": message.from_user.first_name, "item_key": ik, "price": price, "created_at": datetime.now().isoformat()}
        save_json(DATA_FILES['market'], market_listings)
        item = items.get(ik) or limited_items.get(ik)
        bot.send_message(message.chat.id, f"✅ {item.get('name', ik)} за {price}💰!")
    elif cmd == "boss":
        world_boss_handler(types.CallbackQuery(id="0", from_user=message.from_user, message=message, data="world_boss", chat_instance="0"))

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
        types.InlineKeyboardButton("🔄 Сброс дня", callback_data="adm_reset"),
        types.InlineKeyboardButton("👁 Инфо", callback_data="adm_info"),
        types.InlineKeyboardButton("✅ Разбан", callback_data="adm_unban"),
        types.InlineKeyboardButton("✨ Зачарование всем", callback_data="adm_ench_all"),
        types.InlineKeyboardButton("🌍 Новый ивент", callback_data="adm_event"),
        types.InlineKeyboardButton("🐉 Сброс босса", callback_data="adm_boss"),
        types.InlineKeyboardButton("🏟 Старт турнира", callback_data="adm_tour")
    )
    bot.send_message(message.chat.id, "<b>🔧 АДМИН</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_handlers(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Нет доступа!")
        return
    action = call.data.split("_")[1]
    
    if action == "stats":
        real = {k: v for k, v in users.items() if not k.startswith("bot_") and not k.startswith("boss_")}
        text = f"👥 {len(real)} | 💰 {sum(u.get('money',0) for u in real.values())} | ⚔ {sum(u.get('total_duels',0) for u in real.values())}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    elif action == "money":
        bot.send_message(call.message.chat.id, "💰 /givemoney @username сумма")
    elif action == "item":
        bot.send_message(call.message.chat.id, "🎁 /giveitem @username item_key")
    elif action == "ban":
        bot.send_message(call.message.chat.id, "⛔ /ban @username причина")
    elif action == "bcast":
        bot.send_message(call.message.chat.id, "📢 /broadcast текст")
    elif action == "reset":
        bot.send_message(call.message.chat.id, "🔄 /resetdaily @username")
    elif action == "info":
        bot.send_message(call.message.chat.id, "👁 /userinfo @username")
    elif action == "unban":
        bot.send_message(call.message.chat.id, "✅ /unban @username")
    elif action == "ench_all":
        # Выдать всем случайное зачарование
        ench = random.choice(ENCHANT_EFFECTS)
        count = 0
        for uid in users:
            if not uid.startswith("bot_") and not uid.startswith("boss_"):
                p = Player(uid)
                # Зачаровать оружие если есть
                weapon = p.data["equipment"].get("weapon")
                if weapon:
                    p.data.setdefault("enchantments", {})[weapon] = {"name": ench["name"], "effect": ench["effect"], "value": ench["value"]}
                    p.save()
                    count += 1
        bot.send_message(call.message.chat.id, f"✅ Выдано зачарование <b>{ench['name']}</b> для {count} игроков!")
    elif action == "event":
        new_event = {"name": "Админ-ивент", "ench_reward": random.choice(ENCHANT_EFFECTS), "ench_chance": 50, "expires": (datetime.now() + timedelta(minutes=10)).isoformat()}
        events_data["current"] = new_event
        save_json(DATA_FILES['events'], events_data)
        for uid in users:
            if not uid.startswith("bot_") and not uid.startswith("boss_"):
                try:
                    bot.send_message(int(uid), f"🌍 <b>АДМИН-ИВЕНТ!</b>\n{new_event['ench_reward']['name']}")
                except:
                    pass
        bot.send_message(call.message.chat.id, "✅ Ивент запущен!")
    elif action == "boss":
        world_boss_data["hp"] = 1000000
        world_boss_data["max_hp"] = 1000000
        world_boss_data["participants"] = {}
        world_boss_data["total_reward"] = random.randint(30000, 100000)
        world_boss_data["name"] = random.choice(["🌋 Древний титан", "🐉 Мировой змей", "👹 Князь тьмы"])
        save_json(DATA_FILES['world_boss'], world_boss_data)
        bot.send_message(call.message.chat.id, "✅ Мировой босс сброшен!")
    elif action == "tour":
        if tournaments.get("active", {}).get("participants", []):
            tournaments["active"]["status"] = "in_progress"
            save_json(DATA_FILES['tournaments'], tournaments)
            bot.send_message(call.message.chat.id, "✅ Турнир начат!")
        else:
            bot.send_message(call.message.chat.id, "❌ Нет участников!")

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'broadcast', 'resetdaily', 'userinfo'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Нет доступа!")
        return
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd in ["givemoney", "giveitem", "ban", "unban", "resetdaily", "userinfo"]:
            username = parts[1].replace('@', '').strip().lower()
            uid = find_user_by_username(username)
            
            if not uid:
                bot.send_message(message.chat.id, f"❌ @{username} не найден! Проверьте username.")
                return
            
            if cmd == "givemoney":
                amount = int(parts[2])
                p = Player(uid)
                p.data["money"] += amount
                p.save()
                bot.send_message(message.chat.id, f"✅ {amount}💰 → @{username}")
            elif cmd == "giveitem":
                ik = parts[2]
                p = Player(uid)
                p.data["inventory"].append(ik)
                p.save()
                bot.send_message(message.chat.id, f"✅ {ik} → @{username}")
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
                else:
                    bot.send_message(message.chat.id, "❌ Не в бане!")
            elif cmd == "resetdaily":
                p = Player(uid)
                p.data["last_daily"] = None
                p.data["last_dungeon"] = None
                p.save()
                bot.send_message(message.chat.id, f"✅ Сброс @{username}")
            elif cmd == "userinfo":
                p = Player(uid)
                d = p.data
                text = f"<b>👤 @{username}</b>\nID: {uid}\nИмя: {d['first_name']}\nУр.: {d['level']} | 💰 {d['money']}\nРейтинг: {d['pvp_rating']}\nПобед: {d['wins']} | Поражений: {d['losses']}\nКлан: {d.get('clan', 'Нет')}"
                bot.send_message(message.chat.id, text)
        
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
                bot.send_message(message.chat.id, f"✅ {s} | ❌ {f}")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== ЗАПУСК ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v12.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print("=" * 60)
    print("✅ Пошаговые дуэли с защитой и атакой")
    print("✅ Броня снижает урон")
    print("✅ Уникальные навыки у предметов")
    print("✅ Кулдауны на атаки")
    print("✅ Мировой босс 1M HP")
    print("✅ Ивенты с зачарованиями")
    print("✅ Админ через @username (ИСПРАВЛЕНО)")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()