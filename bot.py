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
    'world_boss': 'world_boss.json'
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
        "name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "slot": "weapon",
        "rarity": "common", "level_req": 1, "enchantable": True,
        "skills": [
            {"id": "quick_strike", "name": "⚡ Быстрый удар", "damage_mult": 0.8, "mana_cost": 0, "cooldown": 0, "description": "Базовая атака без кулдауна"},
            {"id": "slash", "name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 5, "cooldown": 1, "description": "Усиленный удар мечом"}
        ],
        "description": "Старый меч с базовыми атаками"
    },
    "flame_blade": {
        "name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "slot": "weapon",
        "rarity": "uncommon", "level_req": 7, "enchantable": True, "element": "fire",
        "skills": [
            {"id": "fire_slash", "name": "🔥 Огненный разрез", "damage_mult": 1.0, "mana_cost": 0, "cooldown": 0, "description": "Базовая огненная атака"},
            {"id": "inferno_strike", "name": "🌋 Инферно удар", "damage_mult": 2.2, "mana_cost": 25, "cooldown": 3, "element": "fire", "burn_chance": 60, "description": "Мощный удар с горением (CD: 3)"},
            {"id": "flame_wave", "name": "🔥 Волна пламени", "damage_mult": 2.5, "mana_cost": 35, "cooldown": 4, "element": "fire", "description": "Огненная волна (CD: 4)"}
        ],
        "description": "Клинок с огненными атаками"
    },
    "frost_axe": {
        "name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "slot": "weapon",
        "rarity": "uncommon", "level_req": 10, "enchantable": True, "element": "ice",
        "skills": [
            {"id": "frost_strike", "name": "❄ Ледяной удар", "damage_mult": 1.0, "mana_cost": 0, "cooldown": 0, "description": "Базовая ледяная атака"},
            {"id": "ice_shatter", "name": "💠 Ледяной раскол", "damage_mult": 2.0, "mana_cost": 22, "cooldown": 3, "element": "ice", "freeze_chance": 50, "description": "Мощный удар с заморозкой (CD: 3)"},
            {"id": "blizzard", "name": "🌨 Метель", "damage_mult": 2.4, "mana_cost": 32, "cooldown": 4, "element": "ice", "description": "Ледяная буря (CD: 4)"}
        ],
        "description": "Топор с ледяными атаками"
    },
    "storm_staff": {
        "name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500, "type": "weapon", "slot": "weapon",
        "rarity": "rare", "level_req": 14, "enchantable": True, "element": "lightning",
        "skills": [
            {"id": "lightning_bolt", "name": "⚡ Молния", "damage_mult": 1.0, "mana_cost": 0, "cooldown": 0, "description": "Базовая молния"},
            {"id": "thunder_storm", "name": "⛈ Грозовой шторм", "damage_mult": 2.3, "mana_cost": 30, "cooldown": 3, "element": "lightning", "stun_chance": 35, "description": "Шторм с оглушением (CD: 3)"},
            {"id": "chain_lightning", "name": "⚡ Цепная молния", "damage_mult": 1.8, "mana_cost": 20, "cooldown": 2, "element": "lightning", "description": "Цепная атака (CD: 2)"}
        ],
        "description": "Посох с молниями"
    },
    "shadow_dagger": {
        "name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "slot": "weapon",
        "rarity": "epic", "level_req": 22, "enchantable": True, "element": "dark",
        "skills": [
            {"id": "shadow_strike", "name": "🌑 Теневой удар", "damage_mult": 1.0, "mana_cost": 0, "cooldown": 0, "description": "Базовая теневая атака"},
            {"id": "assassinate", "name": "🗡 Убийство", "damage_mult": 3.2, "mana_cost": 40, "cooldown": 5, "element": "dark", "description": "Смертельный удар (CD: 5)"},
            {"id": "soul_drain", "name": "💀 Похищение души", "damage_mult": 2.0, "mana_cost": 25, "cooldown": 3, "element": "dark", "life_steal": 0.4, "description": "Кража жизни (CD: 3)"}
        ],
        "description": "Кинжал с вампиризмом"
    },
    "divine_spear": {
        "name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "slot": "weapon",
        "rarity": "legendary", "level_req": 28, "enchantable": True, "element": "light",
        "skills": [
            {"id": "holy_strike", "name": "✨ Святой удар", "damage_mult": 1.0, "mana_cost": 0, "cooldown": 0, "description": "Базовая святая атака"},
            {"id": "divine_judgment", "name": "⚖ Божий суд", "damage_mult": 2.8, "mana_cost": 35, "cooldown": 4, "element": "light", "description": "Мощная святая атака (CD: 4)"},
            {"id": "heavenly_light", "name": "🌟 Небесный свет", "hp_restore": 60, "mana_cost": 25, "cooldown": 3, "description": "Лечение (CD: 3)"}
        ],
        "description": "Копьё с лечением"
    },
    "death_scythe": {
        "name": "💀 Коса смерти", "damage": (40, 65), "price": 12000, "type": "weapon", "slot": "weapon",
        "rarity": "mythic", "level_req": 35, "enchantable": True, "element": "dark",
        "skills": [
            {"id": "reap", "name": "💀 Жатва", "damage_mult": 1.0, "mana_cost": 0, "cooldown": 0, "description": "Базовая атака"},
            {"id": "death_sentence", "name": "☠ Смертный приговор", "damage_mult": 4.0, "mana_cost": 55, "cooldown": 6, "element": "dark", "description": "Ультимативная атака (CD: 6)"},
            {"id": "soul_harvest", "name": "👻 Сбор душ", "damage_mult": 2.8, "mana_cost": 40, "cooldown": 4, "element": "dark", "life_steal": 0.5, "description": "Кража душ (CD: 4)"}
        ],
        "description": "Коса с мощнейшими атаками"
    }
}

HELMETS = {
    "leather_cap": {"name": "🎓 Кожаная шапка", "defense": 2, "price": 60, "type": "helmet", "slot": "head", "rarity": "common", "level_req": 1, "enchantable": True},
    "iron_helmet": {"name": "⛑ Железный шлем", "defense": 6, "price": 250, "type": "helmet", "slot": "head", "rarity": "uncommon", "level_req": 6, "enchantable": True},
    "dragon_helmet": {"name": "🐉 Шлем дракона", "defense": 14, "price": 2000, "type": "helmet", "slot": "head", "rarity": "epic", "level_req": 20, "enchantable": True, "element": "fire", "skills": [{"id": "dragon_roar", "name": "🐉 Рёв дракона", "damage_mult": 1.5, "mana_cost": 15, "cooldown": 3, "description": "Звуковая атака (CD: 3)"}]},
    "crown_of_wisdom": {"name": "👑 Корона мудрости", "defense": 10, "mana_bonus": 40, "price": 3500, "type": "helmet", "slot": "head", "rarity": "legendary", "level_req": 28, "enchantable": True, "skills": [{"id": "mind_blast", "name": "🧠 Ментальный удар", "damage_mult": 2.0, "mana_cost": 20, "cooldown": 3, "description": "Психическая атака (CD: 3)"}]}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "defense": 4, "price": 80, "type": "armor", "slot": "body", "rarity": "common", "level_req": 1, "enchantable": True},
    "chainmail": {"name": "⛓ Кольчуга", "defense": 10, "price": 400, "type": "armor", "slot": "body", "rarity": "uncommon", "level_req": 8, "enchantable": True},
    "plate_armor": {"name": "🛡 Латный доспех", "defense": 18, "price": 1500, "type": "armor", "slot": "body", "rarity": "rare", "level_req": 15, "enchantable": True, "skills": [{"id": "fortify", "name": "🛡 Укрепление", "defense_boost": 30, "mana_cost": 15, "cooldown": 3, "description": "Временная защита (CD: 3)"}]},
    "phoenix_armor": {"name": "🦅 Броня феникса", "defense": 30, "price": 8000, "type": "armor", "slot": "body", "rarity": "legendary", "level_req": 30, "enchantable": True, "element": "fire", "skills": [{"id": "rebirth", "name": "🦅 Возрождение", "hp_restore": 50, "mana_cost": 30, "cooldown": 5, "description": "Лечение (CD: 5)"}]}
}

BOOTS = {
    "leather_boots": {"name": "👢 Кожаные сапоги", "defense": 2, "speed": 5, "price": 100, "type": "boots", "slot": "legs", "rarity": "common", "level_req": 1, "enchantable": True},
    "wind_boots": {"name": "🌪 Сапоги ветра", "defense": 4, "speed": 15, "price": 900, "type": "boots", "slot": "legs", "rarity": "rare", "level_req": 12, "enchantable": True, "skills": [{"id": "tailwind", "name": "💨 Попутный ветер", "speed_boost": 20, "mana_cost": 10, "cooldown": 3, "description": "Ускорение (CD: 3)"}]},
    "hermes_boots": {"name": "👟 Сандалии Гермеса", "defense": 10, "speed": 35, "price": 12000, "type": "boots", "slot": "legs", "rarity": "legendary", "level_req": 35, "enchantable": True, "skills": [{"id": "divine_speed", "name": "⚡ Божественная скорость", "double_attack": True, "mana_cost": 25, "cooldown": 4, "description": "Двойная атака (CD: 4)"}]}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 200, "price": 350, "type": "potion", "rarity": "rare", "level_req": 15},
    "mana_potion": {"name": "💎 Зелье маны", "mana_restore": 60, "price": 60, "type": "potion", "rarity": "common", "level_req": 5}
}

LIMITED_ITEMS = {
    "thunderfury": {
        "name": "⚡ Ярость грома", "damage": (60, 95), "total": 3, "remaining": 3, "price": 50000,
        "type": "weapon", "slot": "weapon", "rarity": "divine", "element": "lightning", "enchantable": True,
        "skills": [
            {"id": "zeus_strike", "name": "⚡ Удар Зевса", "damage_mult": 1.0, "mana_cost": 0, "cooldown": 0, "description": "Базовая атака"},
            {"id": "thunder_gods_wrath", "name": "⚡ Гнев бога грома", "damage_mult": 4.5, "mana_cost": 70, "cooldown": 6, "element": "lightning", "stun_chance": 50, "description": "Ультимативная атака (CD: 6)"},
            {"id": "lightning_apocalypse", "name": "⚡ Молниевый апокалипсис", "damage_mult": 5.0, "mana_cost": 85, "cooldown": 7, "element": "lightning", "description": "Абсолютная атака (CD: 7)"}
        ],
        "description": "Меч бога грома"
    },
    "immortal_helmet": {
        "name": "✨ Шлем бессмертия", "defense": 60, "total": 2, "remaining": 2, "price": 75000,
        "type": "helmet", "slot": "head", "rarity": "divine", "enchantable": True,
        "skills": [
            {"id": "immortality", "name": "✨ Бессмертие", "invincible": 1, "mana_cost": 50, "cooldown": 8, "description": "Неуязвимость на 1 ход (CD: 8)"}
        ],
        "description": "Дарует неуязвимость"
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
enchantments_data = load_json(DATA_FILES['enchantments'], {})
matchmaking_queue = load_json(DATA_FILES['matchmaking'], {})
world_boss_data = load_json(DATA_FILES['world_boss'], {})

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def normalize_username(username):
    """Нормализация username"""
    if not username:
        return None
    return username.replace('@', '').strip().lower()

def find_user_by_username(username):
    """Поиск пользователя по username"""
    username = normalize_username(username)
    if not username:
        return None
    
    # Прямой поиск
    for uid, data in users.items():
        stored_username = normalize_username(data.get("username", ""))
        if stored_username == username:
            return uid
    
    # Поиск по частичному совпадению
    for uid, data in users.items():
        stored_username = normalize_username(data.get("username", ""))
        if stored_username and username in stored_username:
            return uid
    
    return None

def get_user_display_name(uid):
    """Получить отображаемое имя пользователя"""
    if uid.startswith("bot_") or uid.startswith("boss_"):
        return users.get(uid, {}).get("first_name", "Противник")
    
    data = users.get(uid, {})
    uname = data.get("username", "")
    if uname:
        return f"@{uname}"
    return data.get("first_name", "Игрок")

def send_message_safe(chat_id, text, reply_markup=None):
    """Безопасная отправка сообщения"""
    try:
        if reply_markup:
            return bot.send_message(chat_id, text, reply_markup=reply_markup)
        return bot.send_message(chat_id, text)
    except Exception as e:
        print(f"Send error to {chat_id}: {e}")
        return None

def edit_message_safe(chat_id, message_id, text, reply_markup=None):
    """Безопасное редактирование сообщения"""
    try:
        if reply_markup:
            return bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup)
        return bot.edit_message_text(text, chat_id, message_id)
    except Exception as e:
        print(f"Edit error: {e}")
        return None

# ==================== КЛАСС ИГРОКА ====================
class Player:
    def __init__(self, user_id, username="", first_name="Игрок"):
        self.user_id = str(user_id)
        username = normalize_username(username) or ""
        
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
                "battle_history": [], "dungeons_completed": 0, "items_found": 0,
                "world_boss_damage": 0
            }
            self.save()
        else:
            # Обновляем username если изменился
            if username and users[self.user_id].get("username", "") != username:
                users[self.user_id]["username"] = username
                users[self.user_id]["first_name"] = first_name
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
    
    def get_all_skills(self):
        """Получить все доступные навыки со всей экипировки"""
        all_skills = []
        
        for slot in ["weapon", "head", "body", "legs"]:
            ik = self.data["equipment"].get(slot)
            if not ik:
                continue
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
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        # HP одинаковые
        self.p1_hp = 100
        self.p2_hp = 100
        self.p1_max_hp = 100
        self.p2_max_hp = 100
        self.p1_mp = 50
        self.p2_mp = 50
        self.p1_max_mp = 50
        self.p2_max_mp = 50
        
        # Фазы: P1_defend_P2_attack или P2_defend_P1_attack
        self.round_type = "p1_defend_p2_attack"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill_id = None
        self.p2_skill_id = None
        self.p1_target = None
        self.p2_target = None
        
        # Логи для каждого игрока
        self.messages_p1 = []
        self.messages_p2 = []
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Арена
        self.arena = random.choice(["colosseum", "forest", "volcano", "tundra", "void"])
        
        self._add_message(1, f"⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>")
        self._add_message(2, f"⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>")
        
        if self.round_type == "p1_defend_p2_attack":
            self._add_message(1, "🛡 <b>Вы защищаетесь!</b> Выберите часть тела.")
            self._add_message(2, "⚔ <b>Противник защищается.</b> Ожидайте...")
        else:
            self._add_message(2, "🛡 <b>Вы защищаетесь!</b> Выберите часть тела.")
            self._add_message(1, "⚔ <b>Противник защищается.</b> Ожидайте...")
    
    def _add_message(self, player_num, msg):
        if player_num == 1:
            self.messages_p1.append(msg)
        else:
            self.messages_p2.append(msg)
    
    def get_player_name(self, num):
        return get_user_display_name(self.p1_id if num == 1 else self.p2_id)
    
    def get_my_messages(self, for_user_id):
        """Получить сообщения для конкретного игрока"""
        pn = 1 if str(for_user_id) == self.p1_id else 2
        return self.messages_p1 if pn == 1 else self.messages_p2
    
    def set_defend(self, player_num, part):
        """Игрок выбрал защиту"""
        if player_num == 1:
            self.p1_defend = part
        else:
            self.p2_defend = part
        
        # Проверяем готовность
        self._check_and_resolve()
    
    def set_attack(self, player_num, skill_id, target):
        """Игрок выбрал атаку"""
        if player_num == 1:
            self.p1_skill_id = skill_id
            self.p1_target = target
        else:
            self.p2_skill_id = skill_id
            self.p2_target = target
        
        self._check_and_resolve()
    
    def _check_and_resolve(self):
        """Проверка и разрешение раунда"""
        if self.round_type == "p1_defend_p2_attack":
            if self.p1_defend and self.p2_skill_id and self.p2_target:
                self._do_attack(2, 1)  # Атакует P2, защищается P1
                self._switch_round()
        else:
            if self.p2_defend and self.p1_skill_id and self.p1_target:
                self._do_attack(1, 2)  # Атакует P1, защищается P2
                self._switch_round()
    
    def _do_attack(self, attacker, defender):
        """Выполнение атаки"""
        skill_id = self.p1_skill_id if attacker == 1 else self.p2_skill_id
        target = self.p1_target if attacker == 1 else self.p2_target
        defend = self.p1_defend if attacker == 1 else self.p2_defend
        
        # Поиск навыка в экипировке
        attacker_player = self.p1 if attacker == 1 else self.p2
        all_skills = attacker_player.get_all_skills()
        skill_data = None
        for s in all_skills:
            if s["id"] == skill_id:
                skill_data = s
                break
        
        if not skill_data:
            skill_data = {"name": "Атака", "damage_mult": 1.0, "mana_cost": 0, "cooldown": 0}
        
        # Проверка маны
        mc = skill_data.get("mana_cost", 0)
        if attacker == 1:
            if self.p1_mp < mc:
                self._add_message(1, "❌ Недостаточно маны!")
                self._add_message(2, "❌ Противнику не хватило маны!")
                return
            self.p1_mp -= mc
        else:
            if self.p2_mp < mc:
                self._add_message(2, "❌ Недостаточно маны!")
                self._add_message(1, "❌ Противнику не хватило маны!")
                return
            self.p2_mp -= mc
        
        # Расчёт урона
        weapon_ik = attacker_player.data["equipment"].get("weapon")
        if weapon_ik:
            weapon = items.get(weapon_ik) or limited_items.get(weapon_ik)
            if weapon and "damage" in weapon:
                min_d, max_d = weapon["damage"]
            else:
                min_d, max_d = 5, 10
        else:
            min_d, max_d = 5, 10
        
        base_dmg = random.randint(min_d, max_d)
        dmg = int(base_dmg * skill_data.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_mult = BODY_PARTS.get(target, {}).get("multiplier", 1.0)
        dmg = int(dmg * body_mult)
        
        # Защита
        defender_player = self.p1 if defender == 1 else self.p2
        def_value = defender_player.get_equipment_defense(target)
        base_def = {"head": 3, "body": 5, "legs": 2}.get(target, 3)
        total_def = base_def + def_value
        
        reduction = total_def / (total_def + 50)
        blocked = int(dmg * reduction)
        final_dmg = dmg - blocked
        
        # Бонус защиты при совпадении
        blocked_text = ""
        if defend == target:
            final_dmg = int(final_dmg * 0.5)
            blocked_text = " (вдвое меньше — часть защищена!)"
        
        final_dmg = max(1, final_dmg)
        
        # Нанесение урона
        if defender == 1:
            self.p1_hp = max(0, self.p1_hp - final_dmg)
            defender_hp = self.p1_hp
        else:
            self.p2_hp = max(0, self.p2_hp - final_dmg)
            defender_hp = self.p2_hp
        
        skill_name = skill_data.get("name", "Атака")
        target_name = BODY_PARTS.get(target, {}).get("name", "тело")
        attacker_name = self.get_player_name(attacker)
        defender_name = self.get_player_name(defender)
        
        # Сообщение атакующему
        self._add_message(attacker, 
            f"⚔ Вы атаковали [{skill_name}] → {target_name} {defender_name}!\n"
            f"💢 <b>-{final_dmg} HP</b> (броня поглотила {blocked}){blocked_text}\n"
            f"❤ HP противника: {defender_hp}/100")
        
        # Сообщение защищающемуся
        self._add_message(defender,
            f"💢 {attacker_name} атаковал [{skill_name}] → {target_name}!\n"
            f"💔 <b>-{final_dmg} HP</b> (ваша броня поглотила {blocked}){blocked_text}\n"
            f"❤ Ваше HP: {defender_hp}/100")
        
        # Эффекты
        if "burn_chance" in skill_data and random.random() * 100 < skill_data["burn_chance"]:
            self._add_message(defender, "🔥 <b>Горение!</b>")
            self._add_message(attacker, "🔥 Противник горит!")
        
        if "freeze_chance" in skill_data and random.random() * 100 < skill_data["freeze_chance"]:
            self._add_message(defender, "❄ <b>Заморозка!</b> Пропуск хода.")
            self._add_message(attacker, "❄ Противник заморожен!")
        
        if "stun_chance" in skill_data and random.random() * 100 < skill_data["stun_chance"]:
            self._add_message(defender, "⚡ <b>Оглушение!</b>")
            self._add_message(attacker, "⚡ Противник оглушён!")
        
        # Вампиризм
        if "life_steal" in skill_data:
            heal = int(final_dmg * skill_data["life_steal"])
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self._add_message(attacker, f"💚 Вампиризм +{heal} HP")
        
        # Лечение
        if "hp_restore" in skill_data:
            heal = skill_data["hp_restore"]
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self._add_message(attacker, f"💚 Лечение +{heal} HP")
        
        # Кулдауны
        cd = skill_data.get("cooldown", 0)
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
        self.p1_skill_id = None
        self.p2_skill_id = None
        self.p1_target = None
        self.p2_target = None
        
        if self.round_type == "p1_defend_p2_attack":
            self.round_type = "p2_defend_p1_attack"
            self._add_message(2, "🛡 <b>Теперь вы защищаетесь!</b> Выберите часть тела.")
            self._add_message(1, "⚔ <b>Теперь вы атакуете!</b> Противник выбирает защиту...")
        else:
            self.round_type = "p1_defend_p2_attack"
            self._add_message(1, "🛡 <b>Теперь вы защищаетесь!</b> Выберите часть тела.")
            self._add_message(2, "⚔ <b>Теперь вы атакуете!</b> Противник выбирает защиту...")
        
        self.turn += 1
        if self.turn > self.max_turns:
            self.active = False
            self.winner = 0
    
    def get_state_text(self, for_user_id):
        """Получить текст состояния"""
        pn = 1 if str(for_user_id) == self.p1_id else 2
        is_defending = (self.round_type == "p1_defend_p2_attack" and pn == 1) or \
                       (self.round_type == "p2_defend_p1_attack" and pn == 2)
        
        my_hp = self.p1_hp if pn == 1 else self.p2_hp
        opp_hp = self.p2_hp if pn == 1 else self.p1_hp
        my_mp = self.p1_mp if pn == 1 else self.p2_mp
        opp_name = self.get_player_name(3 - pn)
        
        my_hp_bar = self._bar(my_hp, 100, "❤")
        opp_hp_bar = self._bar(opp_hp, 100, "❤")
        
        text = f"""
<b>⚔ ДУЭЛЬ #{self.battle_id}</b>
━━━━━━━━━━━━━━━━━━━━
Ход: <b>{self.turn}</b> | Ставка: <b>{self.bet}💰</b>

<b>Вы:</b> {my_hp_bar}
💎 MP: {my_mp}/50

<b>{opp_name}:</b> {opp_hp_bar}
━━━━━━━━━━━━━━━━━━━━
"""
        
        if is_defending:
            text += "\n🛡 <b>Вы защищаетесь!</b> Выберите часть тела:"
        else:
            text += "\n⚔ <b>Вы атакуете!</b> Выберите цель и навык:"
        
        # Последнее сообщение
        msgs = self.get_my_messages(for_user_id)
        if msgs:
            text += f"\n\n<i>{msgs[-1][:200]}</i>"
        
        return text
    
    def _bar(self, cur, mx, icon):
        pct = cur / mx * 100 if mx > 0 else 0
        f = int(pct / 10)
        e = 10 - f
        color = "🟢" if pct > 50 else "🟡" if pct > 25 else "🔴"
        return f"{icon} {color}[{'█'*f}{'░'*e}] {cur}/{mx}"
    
    def get_available_skills(self, player_num):
        """Получить доступные навыки (с учётом кулдаунов)"""
        player = self.p1 if player_num == 1 else self.p2
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        all_skills = player.get_all_skills()
        
        available = []
        for skill in all_skills:
            sid = skill["id"]
            cd = cooldowns.get(sid, 0)
            if cd <= 0:
                available.append(skill)
        
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
    
    Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v12.0 ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

🎯 <b>НОВОЕ:</b>
• У каждого предмета уникальные атаки
• Кулдауны на все способности
• Базовая атака всегда доступна
• Ивенты с рассылкой
• Мировой босс (1 000 000 HP)

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
        types.InlineKeyboardButton("🔥 На выживание", callback_data="survival_duel"),
        types.InlineKeyboardButton("🎯 Спарринг", callback_data="sparring_duel")
    )
    
    text = """
<b>⚔️ ДУЭЛИ</b>

<b>Система боя:</b>
🛡 Один защищается → другой атакует
🔄 Роли меняются каждый ход
⚔ У каждого оружия уникальные атаки
⏳ Кулдауны на способности
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
        types.InlineKeyboardButton("👹 Мировой босс", callback_data="world_boss"),
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
        show_bet_menu(call, "quick", "⚡ БЫСТРАЯ ДУЭЛЬ")
    elif dt == "find_opponent":
        start_matchmaking(call, "pvp", 50)
    elif dt == "ranked_duel":
        start_matchmaking(call, "ranked", 100)
    elif dt == "hardcore_duel":
        show_bet_menu(call, "hardcore", "💀 ХАРДКОРНАЯ ДУЭЛЬ", [500, 1000, 2000, 5000, 10000])
    elif dt == "survival_duel":
        start_matchmaking(call, "survival", 200)
    elif dt == "sparring_duel":
        start_matchmaking(call, "sparring", 0)

def show_bet_menu(call, duel_type, title, bets=[50, 100, 200, 500, 1000]):
    user_id = call.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    for bet in bets:
        markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"duelbet_{duel_type}_{bet}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
    
    bot.edit_message_text(
        f"<b>{title}</b>\n\n💰 Баланс: <b>{player.data['money']}💰</b>\nВыберите ставку:",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_duels")
def back_to_duels(call):
    duel_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duelbet_"))
def start_duel_with_bet(call):
    parts = call.data.split("_")
    duel_type = parts[1]
    bet = int(parts[2])
    
    start_bot_duel(call.message.chat.id, call.message.message_id, call.from_user.id, duel_type, bet)

def start_matchmaking(call, duel_type, bet):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    queue = matchmaking_queue.get(duel_type, [])
    queue = [q for q in queue if q["user_id"] != user_id]
    
    if queue:
        opponent = queue.pop(0)
        matchmaking_queue[duel_type] = queue
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
        
        bot.edit_message_text("⚔ Соперник найден! Дуэль начинается!", call.message.chat.id, call.message.message_id)
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        
        try:
            opp_name = get_user_display_name(user_id)
            msg = send_message_safe(int(opponent["user_id"]), f"⚔ Дуэль с {opp_name} начинается!")
            if msg:
                show_duel_interface(int(opponent["user_id"]), msg.message_id, duel, opponent["user_id"])
        except:
            pass
    else:
        queue.append({"user_id": user_id, "bet": bet})
        matchmaking_queue[duel_type] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        bot.edit_message_text("🔍 Поиск соперника... Если не найдём — бот!", call.message.chat.id, call.message.message_id)
        threading.Timer(7.0, start_bot_duel_fallback, args=[call.message.chat.id, call.message.message_id, user_id, duel_type, bet]).start()

def start_bot_duel_fallback(chat_id, message_id, user_id, duel_type, bet):
    if str(user_id) in active_duels:
        return
    start_bot_duel(chat_id, message_id, user_id, duel_type, bet)

def start_bot_duel(chat_id, message_id, user_id, duel_type="quick", bet=50):
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        edit_message_safe(chat_id, message_id, f"❌ Недостаточно монет! Нужно {bet}💰")
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
        "username": "", "first_name": f"🤖 Бот Lv.{bot_level}",
        "money": 0, "level": bot_level, "exp": 0, "total_exp": 0,
        "hp": 100, "max_hp": 100, "mana": 50, "max_mana": 50,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000,
        "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Бот", "titles_collected": ["Бот"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0,
        "world_boss_damage": 0
    }
    save_json(DATA_FILES['users'], users)
    
    if bet > 0:
        player.data["money"] -= bet
        player.save()
    
    duel = DuelInstance(user_id, bot_id, duel_type, bet)
    active_duels[str(user_id)] = duel
    
    edit_message_safe(chat_id, message_id, "⚔ Бой с ботом!")
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
        player = duel.p1 if pn == 1 else duel.p2
        for part, data in BODY_PARTS.items():
            defense = player.get_equipment_defense(part)
            base_def = {"head": 3, "body": 5, "legs": 2}.get(part, 3)
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']} (DEF:{base_def + defense})",
                callback_data=f"duel_defend_{part}"
            ))
    else:
        # Выбор цели
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🎯 {data['name']} (x{data['multiplier']})",
                callback_data=f"duel_target_{part}"
            ))
    
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="duel_surrender"))
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="duel_refresh"))
    
    edit_message_safe(chat_id, message_id, state_text[:4000], reply_markup=markup)

# Временное хранилище цели
temp_target_store = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_target_"))
def duel_target_handler(call):
    user_id = call.from_user.id
    part = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.answer_callback_query(call.id, "❌ Дуэль не найдена")
        return
    
    temp_target_store[str(user_id)] = part
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    skills = duel.get_available_skills(pn)
    
    state_text = duel.get_state_text(user_id)
    state_text += f"\n\n🎯 Цель: <b>{BODY_PARTS[part]['name']}</b>\n<b>Выберите навык:</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for skill in skills[:10]:
        sid = skill["id"]
        name = skill["name"]
        mana = skill.get("mana_cost", 0)
        dmg = skill.get("damage_mult", 1.0)
        cd = skill.get("cooldown", 0)
        desc = skill.get("description", "")
        
        cd_text = f" | ⏳CD:{cd}" if cd > 0 else " | ✅Базовая"
        
        markup.add(types.InlineKeyboardButton(
            f"{name} (x{dmg}) [{mana}MP]{cd_text}",
            callback_data=f"duel_skill_{sid}"
        ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="duel_back"))
    
    edit_message_safe(call.message.chat.id, call.message.message_id, state_text[:4000], reply_markup=markup)

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
        bot.answer_callback_query(call.id, "❌ Дуэль не найдена")
        return
    
    target = temp_target_store.get(str(user_id), "body")
    pn = 1 if str(user_id) == duel.p1_id else 2
    
    duel.set_attack(pn, skill_id, target)
    
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
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data in ["duel_refresh", "duel_surrender"])
def duel_misc_handler(call):
    user_id = call.from_user.id
    duel = active_duels.get(str(user_id))
    
    if call.data == "duel_refresh":
        if duel and duel.active:
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
            bot.answer_callback_query(call.id, "✅ Обновлено")
        else:
            bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
    
    elif call.data == "duel_surrender":
        if duel and duel.active:
            duel.active = False
            duel.winner = 2 if str(user_id) == duel.p1_id else 1
            finish_duel(call.message.chat.id, call.message.message_id, duel, user_id)

def finish_duel(chat_id, message_id, duel, for_user_id=None):
    """Завершение дуэли"""
    for uid in [duel.p1_id, duel.p2_id]:
        if uid in active_duels and active_duels[uid].battle_id == duel.battle_id:
            del active_duels[uid]
    
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") or uid.startswith("boss_"):
            if uid in users:
                del users[uid]
    save_json(DATA_FILES['users'], users)
    
    p1_name = get_user_display_name(duel.p1_id)
    p2_name = get_user_display_name(duel.p2_id)
    
    if duel.winner == 0:
        result = "<b>🤝 НИЧЬЯ!</b>"
        winner_id = None
    elif duel.winner == 1:
        result = f"👑 <b>{p1_name}</b> побеждает!\n💀 <b>{p2_name}</b> проигрывает"
        winner_id = duel.p1_id
        loser_id = duel.p2_id
    else:
        result = f"👑 <b>{p2_name}</b> побеждает!\n💀 <b>{p1_name}</b> проигрывает"
        winner_id = duel.p2_id
        loser_id = duel.p1_id
    
    result_text = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

{result}

💰 Ставка: <b>{duel.bet}💰</b>
📊 Ходов: <b>{duel.turn}</b>
"""
    
    if winner_id and not winner_id.startswith("bot_") and not winner_id.startswith("boss_"):
        winner = Player(winner_id)
        if duel.bet > 0:
            winner.data["money"] += duel.bet * 2
        winner.data["wins"] += 1
        winner.data["win_streak"] += 1
        winner.data["total_duels"] += 1
        winner.data["pvp_rating"] += random.randint(20, 35)
        if winner.data["win_streak"] > winner.data["best_streak"]:
            winner.data["best_streak"] = winner.data["win_streak"]
        winner.data["exp"] += duel.turn * 10 + duel.bet // 2
        winner.data["total_exp"] += duel.turn * 10 + duel.bet // 2
        check_level_up(winner)
        winner.save()
        
        # Проверка ивента
        check_event_reward(winner_id)
    
    if winner_id and loser_id and not loser_id.startswith("bot_") and not loser_id.startswith("boss_"):
        loser = Player(loser_id)
        loser.data["losses"] += 1
        loser.data["win_streak"] = 0
        loser.data["total_duels"] += 1
        loser.data["pvp_rating"] = max(0, loser.data["pvp_rating"] - random.randint(10, 25))
        loser.save()
    
    edit_message_safe(chat_id, message_id, result_text)
    
    # Отправка второму игроку
    other_id = duel.p2_id if str(for_user_id) == duel.p1_id else duel.p1_id
    if other_id and not other_id.startswith("bot_") and not other_id.startswith("boss_"):
        send_message_safe(int(other_id), result_text)

def check_event_reward(user_id):
    """Проверка ивента при победе"""
    current = events_data.get("current", {})
    if not current:
        return
    
    if random.random() * 100 < current.get("ench_chance", 15):
        player = Player(user_id)
        ench = current.get("ench_reward", random.choice(ENCHANT_EFFECTS))
        # Даём зачарование на случайный предмет в инвентаре
        if player.data["inventory"]:
            ik = random.choice(player.data["inventory"])
            item = items.get(ik) or limited_items.get(ik)
            if item and item.get("enchantable"):
                player.data.setdefault("enchantments", {})[ik] = {
                    "name": ench["name"],
                    "effect": ench["effect"],
                    "value": ench["value"]
                }
                player.save()
                send_message_safe(int(user_id), 
                    f"🌍 <b>ИВЕНТ!</b>\nВы получили зачарование <b>{ench['name']}</b> на предмет <b>{item['name']}</b>!\n{ench['description']}")

# ==================== МИРОВОЙ БОСС ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_boss")
def world_boss_menu(call):
    if not world_boss_data.get("active"):
        world_boss_data["active"] = {
            "name": "👹 Древний титан",
            "hp": 1000000,
            "max_hp": 1000000,
            "participants": {},
            "total_damage": 0,
            "reward_pool": 100000,
            "expires": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        save_json(DATA_FILES['world_boss'], world_boss_data)
    
    wb = world_boss_data["active"]
    hp_pct = wb["hp"] / wb["max_hp"] * 100
    hp_bar = "█" * int(hp_pct / 10) + "░" * (10 - int(hp_pct / 10))
    
    text = f"""
<b>👹 МИРОВОЙ БОСС</b>

<b>{wb['name']}</b>
❤ [{hp_bar}] {wb['hp']:,}/{wb['max_hp']:,} ({hp_pct:.1f}%)

💰 Призовой фонд: <b>{wb['reward_pool']:,}💰</b>
👥 Участников: {len(wb.get('participants', {}))}

Наносите урон! Последний удар получает бонус!
"""
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚔ Атаковать босса", callback_data="wb_attack"),
        types.InlineKeyboardButton("📊 Мой урон", callback_data="wb_my_damage"),
        types.InlineKeyboardButton("📋 Топ урона", callback_data="wb_top"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world")
    )
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "wb_attack")
def world_boss_attack(call):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    wb = world_boss_data.get("active", {})
    if not wb or wb["hp"] <= 0:
        bot.answer_callback_query(call.id, "❌ Босс уже повержен!")
        return
    
    # Расчёт урона
    weapon_ik = player.data["equipment"].get("weapon")
    if weapon_ik:
        weapon = items.get(weapon_ik) or limited_items.get(weapon_ik)
        if weapon and "damage" in weapon:
            min_d, max_d = weapon["damage"]
        else:
            min_d, max_d = 5, 10
    else:
        min_d, max_d = 5, 10
    
    dmg = random.randint(min_d, max_d) * player.data["level"]
    
    # Шанс крита
    if random.random() < 0.2:
        dmg = int(dmg * 2)
        crit_text = "💥 КРИТ! "
    else:
        crit_text = ""
    
    # Нанесение урона
    old_hp = wb["hp"]
    wb["hp"] = max(0, wb["hp"] - dmg)
    actual_dmg = old_hp - wb["hp"]
    
    # Запись урона
    participants = wb.get("participants", {})
    participants[user_id] = participants.get(user_id, 0) + actual_dmg
    wb["participants"] = participants
    wb["total_damage"] = wb.get("total_damage", 0) + actual_dmg
    
    # Проверка смерти
    if wb["hp"] <= 0:
        # Босс убит
        last_hitter = get_user_display_name(user_id)
        # Распределение наград
        for pid, pdmg in participants.items():
            if not pid.startswith("bot_"):
                share = int(wb["reward_pool"] * pdmg / wb["total_damage"])
                p = Player(pid)
                p.data["money"] += share
                p.save()
                send_message_safe(int(pid), 
                    f"👹 <b>БОСС ПОВЕРЖЕН!</b>\nВаш урон: {pdmg:,}\nНаграда: <b>{share:,}💰</b>\nПоследний удар: {last_hitter}")
        
        wb["hp"] = 0
    
    world_boss_data["active"] = wb
    save_json(DATA_FILES['world_boss'], world_boss_data)
    
    bot.answer_callback_query(call.id, f"{crit_text}Нанесено {actual_dmg:,} урона!")
    world_boss_menu(call)

@bot.callback_query_handler(func=lambda call: call.data == "wb_my_damage")
def wb_my_damage(call):
    user_id = str(call.from_user.id)
    wb = world_boss_data.get("active", {})
    my_dmg = wb.get("participants", {}).get(user_id, 0)
    total = wb.get("total_damage", 1)
    share = my_dmg / total * 100 if total > 0 else 0
    
    text = f"""
<b>👹 МОЙ УРОН</b>

💢 Урон: <b>{my_dmg:,}</b>
📊 Доля: <b>{share:.2f}%</b>
💰 Ожидаемая награда: <b>{int(wb.get('reward_pool', 0) * my_dmg / max(1, total)):,}💰</b>
"""
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "wb_top")
def wb_top_damage(call):
    wb = world_boss_data.get("active", {})
    participants = wb.get("participants", {})
    sorted_p = sorted(participants.items(), key=lambda x: x[1], reverse=True)[:10]
    
    if not sorted_p:
        bot.answer_callback_query(call.id, "📋 Нет участников")
        return
    
    medals = ["🥇", "🥈", "🥉"] + [f"{i}️⃣" for i in range(4, 11)]
    text = "<b>📋 ТОП УРОНА</b>\n\n"
    
    for i, (pid, dmg) in enumerate(sorted_p):
        name = get_user_display_name(pid)
        text += f"{medals[i]} {name}: <b>{dmg:,}</b> урона\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_boss"))
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
        rn = RARITY_NAMES.get(item.get("rarity", "common"), "")
        
        if item.get("type") == "weapon":
            s = f"Урон: {item['damage'][0]}-{item['damage'][1]} | {len(item.get('skills', []))} атаки"
        elif item.get("type") in ["helmet", "armor", "boots"]:
            s = f"Защита: {item.get('defense', 0)}"
            if "skills" in item:
                s += f" | +{len(item['skills'])} навык"
            if "speed" in item:
                s += f" | Скорость: +{item['speed']}"
        else:
            s = ""
        
        text += f"{r} <b>{item['name']}</b> [{rn}]\n   {s}\n   💰 {item['price']} | Ур.{item.get('level_req', 1)}\n\n"
        
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
def trade_extra_handlers(call):
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
                text += f"<b>{item['name']}</b>\n[{pct}{emp}] {item['remaining']}/{item['total']}\n💰 <b>{item['price']}💰</b>\n"
                if "skills" in item:
                    text += f"⚔ Навыков: {len(item['skills'])}\n"
                text += "\n"
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
        player.data["money"] += bonus
        player.data["exp"] += random.randint(80, 250)
        player.data["last_daily"] = today
        old = player.data["level"]
        check_level_up(player)
        player.save()
        text = f"<b>🎁 БОНУС</b>\n💰 +{bonus}"
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
                text += f"📦 {item['name']} — <b>{listing['price']}💰</b>\n"
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
def mkt_buy(call):
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("removelot_"))
def remove_lot_handler(call):
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

# ==================== ГЕРОЙ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["hero_stats", "hero_inventory", "hero_achievements", "hero_enchantments", "hero_equipped", "hero_heal", "back_to_hero"])
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
🏆 {d['wins']} | 💀 {d['losses']} | 📈 {wr:.1f}%
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
            eq = ""
            for s, ek in player.data["equipment"].items():
                if ek == ik:
                    eq = f" [🟢 {s}]"
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
    
    elif call.data == "hero_equipped":
        eq = player.data["equipment"]
        text = "<b>👁 ЭКИПИРОВКА</b>\n\n"
        sn = {"weapon": "⚔ Оружие", "head": "👤 Голова", "body": "🦾 Тело", "legs": "🦿 Ноги"}
        for slot, name in sn.items():
            ik = eq.get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                if item:
                    text += f"{name}: <b>{item['name']}</b>\n"
                    if "skills" in item:
                        text += f"  Навыки: {', '.join([s['name'] for s in item['skills'][:3]])}\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔴 Снять всё", callback_data="unequip_all"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
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
        bot.edit_message_text(f"💊 {potion['name']}\n❤ HP: {player.data['hp']}", call.message.chat.id, call.message.message_id)
    
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
        ]
        text = f"<b>🏅 ДОСТИЖЕНИЯ</b>\n\n"
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
    
    elif call.data == "back_to_hero":
        hero_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
def equip_handler(call):
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("use_"))
def use_handler(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    item = items.get(ik) or limited_items.get(ik)
    if not item or item.get("type") != "potion" or ik not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌ Нельзя!")
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
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, name in enumerate(["🐺 Логово волка", "🕷 Паучьи пещеры", "💀 Катакомбы", "🐉 Драконье логово", "👹 Бездна"], 1):
        markup.add(types.InlineKeyboardButton(name, callback_data=f"dung_{i}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dung_"))
def start_dungeon_handler(call):
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
    
    # Создание босса и дуэли
    boss_level = level_reqs[dl - 1] * 2 + 3
    boss_id = f"boss_{random.randint(100000, 999999)}"
    boss_names = ["🐺 Вожак стаи", "🕷 Королева пауков", "💀 Некромант", "🐉 Древний дракон", "👹 Владыка бездны"]
    
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    for slot, itype in [("head", "helmet"), ("body", "armor"), ("legs", "boots")]:
        sitems = [k for k, v in items.items() if v.get("type") == itype and v.get("level_req", 1) <= boss_level]
        if sitems:
            equip[slot] = random.choice(sitems)
    wpns = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= boss_level]
    if wpns:
        equip["weapon"] = random.choice(wpns)
    
    users[boss_id] = {
        "username": "", "first_name": boss_names[dl - 1],
        "money": 0, "level": boss_level, "exp": 0,
        "hp": 100, "max_hp": 100, "mana": 50, "max_mana": 50,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000,
        "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Босс", "titles_collected": ["Босс"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0,
        "world_boss_damage": 0
    }
    save_json(DATA_FILES['users'], users)
    
    duel = DuelInstance(user_id, boss_id, "dungeon", 0)
    active_duels[str(user_id)] = duel
    
    bot.edit_message_text(f"⚔ Босс: <b>{boss_names[dl-1]}</b>!", call.message.chat.id, call.message.message_id)
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

# ==================== ТУРНИРЫ, ИВЕНТЫ, ТОП ====================
@bot.callback_query_handler(func=lambda call: call.data in ["world_tournaments", "world_events", "world_top", "world_help", "back_to_world"])
def world_extra_handlers(call):
    if call.data == "world_tournaments":
        if not tournaments.get("active"):
            tournaments["active"] = {"name": "Турнир", "participants": [], "prize_pool": 5000, "status": "registration"}
            save_json(DATA_FILES['tournaments'], tournaments)
        tour = tournaments["active"]
        text = f"<b>🏟 ТУРНИР</b>\nУчастников: {len(tour.get('participants', []))}\nПриз: <b>{tour.get('prize_pool', 0)}💰</b>"
        markup = types.InlineKeyboardMarkup(row_width=1)
        if tour.get("status") == "registration":
            markup.add(types.InlineKeyboardButton("🏆 Участвовать (500💰)", callback_data="tour_join"))
        markup.add(types.InlineKeyboardButton("📋 Участники", callback_data="tour_list"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "world_events":
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
            # Рассылка
            for uid in users:
                if not uid.startswith("bot_") and not uid.startswith("boss_"):
                    try:
                        bot.send_message(int(uid), f"🌍 <b>НОВЫЙ ИВЕНТ!</b>\n{new_event['name']}\nШанс: {new_event['ench_reward']['name']}")
                    except:
                        pass
        
        ev = events_data["current"]
        time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
        minutes_left = max(0, time_left.seconds // 60)
        text = f"<b>🌍 ИВЕНТ</b>\n<b>{ev['name']}</b>\n✨ {ev['ench_reward']['name']}\n⏰ {minutes_left} мин."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "world_top":
        markup = types.InlineKeyboardMarkup(row_width=1)
        for cat, name in [("level", "⭐ Уровень"), ("wins", "⚔ Победы"), ("money", "💰 Монеты"), ("rating", "🏆 Рейтинг")]:
            markup.add(types.InlineKeyboardButton(name, callback_data=f"top_{cat}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
        bot.edit_message_text("<b>📊 ТОП</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "world_help":
        text = "<b>ℹ ПОМОЩЬ</b>\n⚔ /duel | 🛒 /shop | 👤 /stats\n📦 /sell | 🎁 /daily"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "back_to_world":
        world_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "tour_join")
def tour_join_handler(call):
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

@bot.callback_query_handler(func=lambda call: call.data == "tour_list")
def tour_list_handler(call):
    participants = tournaments.get("active", {}).get("participants", [])
    if not participants:
        bot.answer_callback_query(call.id, "📋 Пусто")
        return
    text = "<b>📋 УЧАСТНИКИ</b>\n\n"
    for i, uid in enumerate(participants, 1):
        text += f"{i}. {get_user_display_name(uid)}\n"
    bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def top_show_handler(call):
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
        text += f"{medals[i]} {get_user_display_name(uid)}: {val}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_top"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== КЛАНЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_clans")
def world_clans_handler(call):
    user_id = call.from_user.id
    player = Player(user_id)
    if player.data.get("clan"):
        clan = clans.get(player.data["clan"], {})
        text = f"<b>🛡 {player.data['clan']}</b>\n👥 {len(clan.get('members', []))} уч."
    else:
        text = "<b>🛡 КЛАНЫ</b>\n/createclan [имя]\n/joinclan [имя]"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== АДМИН-ПАНЕЛЬ ====================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
        types.InlineKeyboardButton("💰 Выдать деньги", callback_data="adm_money"),
        types.InlineKeyboardButton("🎁 Выдать предмет", callback_data="adm_item"),
        types.InlineKeyboardButton("✨ Выдать зачарование", callback_data="adm_enchant"),
        types.InlineKeyboardButton("⛔ Бан", callback_data="adm_ban"),
        types.InlineKeyboardButton("✅ Разбан", callback_data="adm_unban"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("🔄 Сброс дня", callback_data="adm_reset"),
        types.InlineKeyboardButton("👁 Инфо игрока", callback_data="adm_info"),
        types.InlineKeyboardButton("🌍 Новый ивент", callback_data="adm_event"),
        types.InlineKeyboardButton("👹 Создать босса", callback_data="adm_boss"),
        types.InlineKeyboardButton("🏟 Турнир", callback_data="adm_tournament")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Нет доступа!")
        return
    
    action = call.data.split("_")[1]
    
    prompts = {
        "stats": None,
        "money": "💰 /givemoney @username [сумма]",
        "item": "🎁 /giveitem @username [item_key]",
        "enchant": "✨ /giveenchant @username [эффект]",
        "ban": "⛔ /ban @username [причина]",
        "unban": "✅ /unban @username",
        "broadcast": "📢 /broadcast [текст]",
        "reset": "🔄 /resetdaily @username",
        "info": "👁 /userinfo @username",
        "event": "🌍 /newevent [название]",
        "boss": "👹 /createboss [имя] [HP] [награда]",
        "tournament": "🏟 /starttournament"
    }
    
    if action == "stats":
        real = {k: v for k, v in users.items() if not k.startswith("bot_") and not k.startswith("boss_")}
        text = f"""
<b>📊 СТАТИСТИКА</b>
👥 Игроков: {len(real)}
💰 Монет: {sum(u.get('money',0) for u in real.values())}
⚔ Дуэлей: {sum(u.get('total_duels',0) for u in real.values())}
🛡 Кланов: {len(clans)}
💎 Лимиток: {sum(v.get('remaining',0) for v in limited_items.values())}
"""
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    else:
        bot.send_message(call.message.chat.id, prompts.get(action, ""))

@bot.message_handler(commands=['givemoney', 'giveitem', 'giveenchant', 'ban', 'unban', 'broadcast', 'resetdaily', 'userinfo', 'newevent', 'createboss', 'starttournament'])
def admin_commands_handler(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Нет доступа!")
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd in ["givemoney", "giveitem", "giveenchant", "ban", "unban", "resetdaily", "userinfo"]:
            username = parts[1].replace('@', '') if len(parts) > 1 else ""
            uid = find_user_by_username(username)
            
            if not uid:
                bot.send_message(message.chat.id, f"❌ @{username} не найден! Проверьте username.")
                # Показать список пользователей
                sample = []
                for u, d in list(users.items())[:5]:
                    if not u.startswith("bot_"):
                        sample.append(f"@{d.get('username', '')} - {d.get('first_name', '')}")
                if sample:
                    bot.send_message(message.chat.id, "Примеры:\n" + "\n".join(sample))
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
            
            elif cmd == "giveenchant":
                effect_name = " ".join(parts[2:])
                ench = None
                for e in ENCHANT_EFFECTS:
                    if e["name"].lower() in effect_name.lower() or e["effect"].lower() in effect_name.lower():
                        ench = e
                        break
                if not ench:
                    ench = random.choice(ENCHANT_EFFECTS)
                
                p = Player(uid)
                if p.data["inventory"]:
                    ik = random.choice(p.data["inventory"])
                    p.data.setdefault("enchantments", {})[ik] = {"name": ench["name"], "effect": ench["effect"], "value": ench["value"]}
                    p.save()
                    bot.send_message(message.chat.id, f"✨ {ench['name']} → @{username}")
            
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
            
            elif cmd == "resetdaily":
                p = Player(uid)
                p.data["last_daily"] = None
                p.data["last_dungeon"] = None
                p.save()
                bot.send_message(message.chat.id, f"✅ Сброс @{username}")
            
            elif cmd == "userinfo":
                p = Player(uid)
                d = p.data
                text = f"""
<b>👤 @{username}</b>
ID: {uid}
Имя: {d['first_name']}
Ур.: {d['level']} | 💰 {d['money']}
Рейтинг: {d['pvp_rating']}
Побед: {d['wins']} | Поражений: {d['losses']}
"""
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
        
        elif cmd == "newevent":
            name = " ".join(parts[1:]) if len(parts) > 1 else "Специальный ивент"
            new_event = {
                "name": name,
                "ench_reward": random.choice(ENCHANT_EFFECTS),
                "ench_chance": random.randint(10, 30),
                "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
            }
            events_data["current"] = new_event
            save_json(DATA_FILES['events'], events_data)
            for uid in users:
                if not uid.startswith("bot_") and not uid.startswith("boss_"):
                    try:
                        bot.send_message(int(uid), f"🌍 <b>НОВЫЙ ИВЕНТ!</b>\n{name}")
                    except:
                        pass
            bot.send_message(message.chat.id, "✅ Ивент создан и разослан!")
        
        elif cmd == "createboss":
            name = parts[1] if len(parts) > 1 else "Древний титан"
            hp = int(parts[2]) if len(parts) > 2 else 1000000
            reward = int(parts[3]) if len(parts) > 3 else 100000
            
            world_boss_data["active"] = {
                "name": f"👹 {name}",
                "hp": hp,
                "max_hp": hp,
                "participants": {},
                "total_damage": 0,
                "reward_pool": reward,
                "expires": (datetime.now() + timedelta(hours=24)).isoformat()
            }
            save_json(DATA_FILES['world_boss'], world_boss_data)
            
            for uid in users:
                if not uid.startswith("bot_") and not uid.startswith("boss_"):
                    try:
                        bot.send_message(int(uid), f"👹 <b>МИРОВОЙ БОСС!</b>\n{name}\nHP: {hp:,}\nНаграда: {reward:,}💰\nИспользуйте /start для атаки!")
                    except:
                        pass
            bot.send_message(message.chat.id, "✅ Босс создан!")
        
        elif cmd == "starttournament":
            if tournaments.get("active", {}).get("participants", []):
                tour = tournaments["active"]
                tour["status"] = "in_progress"
                tournaments["active"] = tour
                save_json(DATA_FILES['tournaments'], tournaments)
                bot.send_message(message.chat.id, f"🏟 Турнир начат!")
            else:
                bot.send_message(message.chat.id, "❌ Нет участников!")
    
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
def misc_commands_handler(message):
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
        player.data["inventory"].pop(idx)
        player.save()
        lid = f"{user_id}_{int(time.time())}"
        market_listings[lid] = {"seller_id": user_id, "item_key": ik, "price": price, "created_at": datetime.now().isoformat()}
        save_json(DATA_FILES['market'], market_listings)
        item = items.get(ik) or limited_items.get(ik)
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

# ==================== ЗАПУСК ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v12.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print("=" * 60)
    print("✅ У каждого предмета уникальные атаки")
    print("✅ Кулдауны на способности (базовая всегда доступна)")
    print("✅ Мировой босс (1 000 000 HP)")
    print("✅ Ивенты с рассылкой")
    print("✅ Админ через @username (исправлено)")
    print("✅ Зачарования через админку")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
