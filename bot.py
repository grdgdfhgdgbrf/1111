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

DUEL_TYPES = {
    "quick": {"name": "⚡ Быстрая", "bet": 50, "max_turns": 30, "description": "Короткий бой с ботом"},
    "ranked": {"name": "🏆 Рейтинговая", "bet": 100, "max_turns": 50, "description": "Влияет на рейтинг"},
    "hardcore": {"name": "💀 Хардкор", "bet": 500, "max_turns": 40, "description": "Высокие ставки, высокие риски"},
    "survival": {"name": "🔥 Выживание", "bet": 200, "max_turns": 60, "description": "Без ограничений по времени"},
    "sparring": {"name": "🎯 Спарринг", "bet": 0, "max_turns": 20, "description": "Тренировочный бой без ставок"},
    "timed": {"name": "⏰ На время", "bet": 150, "max_turns": 15, "description": "Кто быстрее нанесёт больше урона"},
    "reversal": {"name": "🔄 Реверс", "bet": 300, "max_turns": 35, "description": "Урон по незащищённым частям x2"}
}

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
    "leather_cap": {"name": "🎓 Кожаная шапка", "defense": 5, "price": 60, "type": "helmet", "slot": "head", "rarity": "common", "level_req": 1, "enchantable": True},
    "iron_helmet": {"name": "⛑ Железный шлем", "defense": 12, "price": 250, "type": "helmet", "slot": "head", "rarity": "uncommon", "level_req": 6, "enchantable": True},
    "dragon_helmet": {"name": "🐉 Шлем дракона", "defense": 22, "price": 2000, "type": "helmet", "slot": "head", "rarity": "epic", "level_req": 20, "enchantable": True, "element": "fire"},
    "crown_of_wisdom": {"name": "👑 Корона мудрости", "defense": 18, "price": 3500, "type": "helmet", "slot": "head", "rarity": "legendary", "level_req": 28, "enchantable": True}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "defense": 8, "price": 80, "type": "armor", "slot": "body", "rarity": "common", "level_req": 1, "enchantable": True},
    "chainmail": {"name": "⛓ Кольчуга", "defense": 18, "price": 400, "type": "armor", "slot": "body", "rarity": "uncommon", "level_req": 8, "enchantable": True},
    "plate_armor": {"name": "🛡 Латный доспех", "defense": 30, "price": 1500, "type": "armor", "slot": "body", "rarity": "rare", "level_req": 15, "enchantable": True},
    "shadow_armor": {"name": "🌑 Теневая броня", "defense": 38, "price": 3500, "type": "armor", "slot": "body", "rarity": "epic", "level_req": 22, "enchantable": True, "element": "dark"},
    "phoenix_armor": {"name": "🦅 Броня феникса", "defense": 50, "price": 8000, "type": "armor", "slot": "body", "rarity": "legendary", "level_req": 30, "enchantable": True, "element": "fire"}
}

BOOTS = {
    "leather_boots": {"name": "👢 Кожаные сапоги", "defense": 3, "speed": 8, "price": 100, "type": "boots", "slot": "legs", "rarity": "common", "level_req": 1, "enchantable": True},
    "wind_boots": {"name": "🌪 Сапоги ветра", "defense": 6, "speed": 18, "price": 900, "type": "boots", "slot": "legs", "rarity": "rare", "level_req": 12, "enchantable": True},
    "blink_boots": {"name": "✨ Сапоги телепортации", "defense": 10, "speed": 28, "price": 4000, "type": "boots", "slot": "legs", "rarity": "epic", "level_req": 25, "enchantable": True},
    "hermes_boots": {"name": "👟 Сандалии Гермеса", "defense": 15, "speed": 45, "price": 12000, "type": "boots", "slot": "legs", "rarity": "legendary", "level_req": 35, "enchantable": True}
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
    "immortal_helmet": {"name": "✨ Шлем бессмертия", "defense": 100, "total": 2, "remaining": 2, "price": 75000, "type": "helmet", "slot": "head", "rarity": "divine", "enchantable": True}
}

ALL_ITEMS = {}
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(BOOTS)
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(POTIONS)

# ==================== БАЗА НАВЫКОВ ====================
SKILLS_DB = {
    # Базовые (быстрые, слабые)
    "quick_strike": {"name": "⚡ Быстрый удар", "damage_mult": 0.8, "mana_cost": 0, "cooldown": 0, "tier": 1},
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.1, "mana_cost": 5, "cooldown": 0, "tier": 1},
    # Средние
    "power_shot": {"name": "🎯 Мощный выстрел", "damage_mult": 1.5, "mana_cost": 12, "cooldown": 1, "tier": 2},
    "multi_shot": {"name": "🏹 Залп", "damage_mult": 0.6, "mana_cost": 18, "hits": 3, "cooldown": 2, "tier": 2},
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.4, "mana_cost": 15, "element": "fire", "burn_chance": 25, "cooldown": 1, "tier": 2},
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.3, "mana_cost": 14, "element": "ice", "freeze_chance": 20, "cooldown": 1, "tier": 2},
    # Сильные
    "inferno_strike": {"name": "🌋 Инферно удар", "damage_mult": 2.2, "mana_cost": 30, "element": "fire", "burn_chance": 55, "cooldown": 3, "tier": 3},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.0, "mana_cost": 28, "element": "ice", "freeze_chance": 45, "cooldown": 3, "tier": 3},
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.6, "mana_cost": 18, "element": "lightning", "stun_chance": 18, "cooldown": 1, "tier": 2},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.3, "mana_cost": 35, "element": "lightning", "stun_chance": 35, "cooldown": 3, "tier": 3},
    # Ультимейты
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.5, "mana_cost": 50, "element": "dark", "ignore_defense": 50, "cooldown": 5, "tier": 4},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 3.0, "mana_cost": 45, "element": "light", "cooldown": 4, "tier": 4},
    "thunder_gods_wrath": {"name": "⚡ Гнев бога грома", "damage_mult": 4.5, "mana_cost": 70, "element": "lightning", "stun_chance": 50, "cooldown": 6, "tier": 5},
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
                "hp": 200,
                "max_hp": 200,
                "mana": 80,
                "max_mana": 80,
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
                "tournament_wins": 0
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
        base_def = item.get("defense", 0)
        # Зачарования
        ench = self.data.get("enchantments", {}).get(ik, {})
        if ench and ench.get("effect") == "defense_bonus":
            base_def += ench.get("value", 0)
        return base_def
    
    def get_weapon_damage(self):
        """Получить урон оружия"""
        ik = self.data["equipment"].get("weapon")
        if not ik:
            return (3, 6)  # Базовый урон без оружия
        item = items.get(ik) or limited_items.get(ik)
        if not item or "damage" not in item:
            return (3, 6)
        dmg = list(item["damage"])
        # Зачарования
        ench = self.data.get("enchantments", {}).get(ik, {})
        if ench:
            if ench.get("effect") == "fire_damage":
                dmg[0] += ench.get("value", 0)
                dmg[1] += ench.get("value", 0)
            elif ench.get("effect") == "damage_boost":
                dmg[0] = int(dmg[0] * (1 + ench.get("value", 0) / 100))
                dmg[1] = int(dmg[1] * (1 + ench.get("value", 0) / 100))
        return tuple(dmg)

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
        self.max_turns = DUEL_TYPES.get(duel_type, {}).get("max_turns", 30)
        self.active = True
        self.winner = None
        self.log = []
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        # Базовые HP (одинаковые для честного боя)
        base_hp = 200 + random.randint(0, 20)
        self.p1_hp = base_hp
        self.p2_hp = base_hp
        self.p1_max_hp = base_hp
        self.p2_max_hp = base_hp
        
        self.p1_mp = 80
        self.p2_mp = 80
        self.p1_max_mp = 80
        self.p2_max_mp = 80
        
        # Фазы: p1_defend -> p1_done, затем p2_defend -> p2_attack -> p2_done
        self.p1_phase = "defend_select"
        self.p2_phase = "defend_select"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_attack_part = None
        self.p2_attack_part = None
        self.p1_skill = None
        self.p2_skill = None
        
        # Очерёдность атаки (кто первый бьёт в этом раунде)
        self.round_attacker = random.choice([1, 2])
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Эффекты
        self.p1_effects = []
        self.p2_effects = []
        
        # Арена
        self.arena = random.choice(["colosseum", "forest", "volcano", "tundra", "void", "temple"])
        
        self.log.append(f"⚔ <b>БИТВА НАЧАЛАСЬ!</b>")
        self.log.append(f"🏟 Арена: <b>{self._arena_name()}</b> | Тип: <b>{DUEL_TYPES.get(duel_type, {}).get('name', duel_type)}</b>")
    
    def _arena_name(self):
        names = {"colosseum": "Колизей", "forest": "Лес", "volcano": "Вулкан", "tundra": "Тундра", "void": "Пустота", "temple": "Храм"}
        return names.get(self.arena, self.arena)
    
    def get_player_name(self, num):
        return self.p1.data["first_name"] if num == 1 else self.p2.data["first_name"]
    
    def get_available_skills(self, player_num):
        player = self.p1 if player_num == 1 else self.p2
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        equip = player.data["equipment"]
        
        available = []
        
        # Базовые всегда доступны
        for sid in ["quick_strike", "slash"]:
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
    
    def set_defend(self, player_num, part):
        if player_num == 1:
            self.p1_defend = part
            self.p1_phase = "done"
        else:
            self.p2_defend = part
            self.p2_phase = "attack_select"
    
    def set_attack(self, player_num, part, skill_id):
        if player_num == 1:
            self.p1_attack_part = part
            self.p1_skill = skill_id
        else:
            self.p2_attack_part = part
            self.p2_skill = skill_id
            self.p2_phase = "done"
        
        # Проверка готовности обоих
        if self.p1_phase == "done" and self.p2_phase == "done":
            self._resolve_round()
    
    def _resolve_round(self):
        """Разрешение раунда"""
        # Обработка эффектов
        self._process_effects(1)
        self._process_effects(2)
        
        # Атака первого
        attacker = self.round_attacker
        defender = 3 - attacker
        
        self._do_attack(attacker, defender)
        if self.p1_hp <= 0 or self.p2_hp <= 0:
            self._check_end()
            return
        
        # Атака второго
        self._do_attack(defender, attacker)
        self._check_end()
        
        # Смена очерёдности
        self.round_attacker = 3 - self.round_attacker
        
        # Сброс фаз
        self.p1_phase = "defend_select"
        self.p2_phase = "defend_select"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_attack_part = None
        self.p2_attack_part = None
        self.p1_skill = None
        self.p2_skill = None
        
        # Уменьшение кулдаунов
        self._reduce_cooldowns(1)
        self._reduce_cooldowns(2)
        
        self.turn += 1
        if self.turn > self.max_turns:
            self.active = False
            self.winner = 0
    
    def _do_attack(self, attacker, defender):
        skill_id = self.p1_skill if attacker == 1 else self.p2_skill
        attack_part = self.p1_attack_part if attacker == 1 else self.p2_attack_part
        defend_part = self.p2_defend if attacker == 1 else self.p1_defend
        
        if not skill_id or not attack_part:
            return
        
        skill = SKILLS_DB.get(skill_id, {"name": "Атака", "damage_mult": 1.0, "mana_cost": 0, "cooldown": 0})
        
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
        
        # Урон оружия
        attacker_player = self.p1 if attacker == 1 else self.p2
        weapon_dmg = attacker_player.get_weapon_damage()
        base_dmg = random.randint(weapon_dmg[0], weapon_dmg[1])
        dmg = int(base_dmg * skill.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_m = BODY_PARTS.get(attack_part, {}).get("multiplier", 1.0)
        dmg = int(dmg * body_m)
        
        # Проверка защиты
        if defend_part == attack_part:
            defender_player = self.p2 if attacker == 1 else self.p1
            defense = defender_player.get_equipment_defense(defend_part)
            
            # Броня уменьшает урон на процент защиты
            reduction_pct = min(80, defense)  # Максимум 80% снижения
            dmg = int(dmg * (1 - reduction_pct / 100))
            
            self.log.append(f"🛡 {self.get_player_name(defender)} защитил {BODY_PARTS[defend_part]['name']}! Броня снизила урон на {reduction_pct}%")
        
        # Особые правила типов дуэлей
        if self.duel_type == "reversal" and defend_part != attack_part:
            dmg = int(dmg * 2)
            self.log.append("🔄 РЕВЕРС: урон по незащищённой части x2!")
        
        # Крит (базовый шанс 5%)
        is_crit = random.random() < 0.05
        if is_crit:
            dmg = int(dmg * 1.5)
        
        # Элемент
        weapon_key = attacker_player.data["equipment"].get("weapon")
        if weapon_key:
            weapon = items.get(weapon_key) or limited_items.get(weapon_key)
            if weapon and "element" in weapon:
                defender_weapon_key = (self.p2 if attacker == 1 else self.p1).data["equipment"].get("weapon")
                if defender_weapon_key:
                    def_weapon = items.get(defender_weapon_key) or limited_items.get(defender_weapon_key)
                    if def_weapon and "element" in def_weapon:
                        if ELEMENTS.get(weapon["element"], {}).get("strong") == def_weapon["element"]:
                            dmg = int(dmg * 1.4)
                            self.log.append(f"💥 СУПЕРЭФФЕКТИВНО! {ELEMENTS[weapon['element']]['name']} > {ELEMENTS[def_weapon['element']]['name']}")
        
        # Применение урона
        if defender == 1:
            self.p1_hp = max(0, self.p1_hp - dmg)
        else:
            self.p2_hp = max(0, self.p2_hp - dmg)
        
        ct = "💥 КРИТ! " if is_crit else ""
        self.log.append(f"{ct}⚔ {self.get_player_name(attacker)} [{skill['name']}] → {BODY_PARTS[attack_part]['name']} {self.get_player_name(defender)}: <b>-{dmg} HP</b>")
        
        # Кулдаун навыка
        if skill.get("cooldown", 0) > 0:
            if attacker == 1:
                self.p1_cooldowns[skill_id] = skill["cooldown"]
            else:
                self.p2_cooldowns[skill_id] = skill["cooldown"]
    
    def _process_effects(self, player_num):
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        hp = self.p1_hp if player_num == 1 else self.p2_hp
        
        for eff in effects[:]:
            if eff["type"] == "burn":
                hp -= 10
                self.log.append(f"🔥 Горение -10 HP")
            elif eff["type"] == "poison":
                hp -= 12
                self.log.append(f"☠ Яд -12 HP")
            
            eff["duration"] -= 1
            if eff["duration"] <= 0:
                effects.remove(eff)
        
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
        elif self.p2_hp <= 0:
            self.active = False
            self.winner = 1
    
    def get_state_text(self, for_player_id):
        pn = 1 if str(for_player_id) == self.p1_id else 2
        phase = self.p1_phase if pn == 1 else self.p2_phase
        my_defend = self.p1_defend if pn == 1 else self.p2_defend
        opponent_defend = self.p2_defend if pn == 1 else self.p1_defend
        
        def bar(cur, mx, icon):
            pct = cur / mx * 100 if mx > 0 else 0
            f = int(pct / 10)
            e = 10 - f
            color = "🟢" if pct > 50 else "🟡" if pct > 25 else "🔴"
            return f"{icon} {color}[{'█'*f}{'░'*e}] {cur}/{mx} ({pct:.0f}%)"
        
        text = f"""
<b>⚔ ДУЭЛЬ #{self.battle_id}</b>
━━━━━━━━━━━━━━━━━━━━
🏟 {self._arena_name()} | Тип: <b>{DUEL_TYPES.get(self.duel_type, {}).get('name', self.duel_type)}</b>
Ход: <b>{self.turn}</b> | Ставка: <b>{self.bet}💰</b>

<b>Вы ({self.get_player_name(pn)})</b>
{bar(self.p1_hp if pn == 1 else self.p2_hp, self.p1_max_hp if pn == 1 else self.p2_max_hp, '❤')}
💎 MP: {self.p1_mp if pn == 1 else self.p2_mp}/{self.p1_max_mp if pn == 1 else self.p2_max_mp}
🛡 Ваша защита: {BODY_PARTS.get(my_defend, {}).get('name', 'Не выбрана') if my_defend else 'Не выбрана'}

<b>Противник ({self.get_player_name(3-pn)})</b>
{bar(self.p2_hp if pn == 1 else self.p1_hp, self.p2_max_hp if pn == 1 else self.p1_max_hp, '❤')}
💎 MP: {self.p2_mp if pn == 1 else self.p1_mp}/{self.p2_max_mp if pn == 1 else self.p1_max_mp}
🛡 Защита противника: {BODY_PARTS.get(opponent_defend, {}).get('name', 'Не выбрана') if opponent_defend else 'Не выбрана'}
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
            text += "\n<b>Эффекты:</b> " + ", ".join([f"{e['type']}({e['duration']})" for e in effs])
        
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
    
    username = message.from_user.username or f"id{user_id}"
    first_name = message.from_user.first_name or "Игрок"
    Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v11.0 ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

🎯 <b>НОВОЕ:</b>
• 7 видов дуэлей с разными правилами!
• Броня уменьшает урон (макс 80%)
• У каждого оружия свои атаки
• Навыки: слабые/средние/сильные/ультимейты
• Данжи с 3 боссами
• Турниры с сеткой плей-офф
• Ивенты с реальными наградами
• Админ-панель с полным функционалом

💰 Старт: <b>500 монет</b>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for dtype, dinfo in DUEL_TYPES.items():
        markup.add(types.InlineKeyboardButton(
            f"{dinfo['name']} — {dinfo['description']} ({dinfo['bet']}💰)",
            callback_data=f"dueltype_{dtype}"
        ))
    markup.add(types.InlineKeyboardButton("🔍 Найти соперника", callback_data="find_opponent"))
    
    text = """
<b>⚔️ ДУЭЛИ</b>

<b>7 уникальных режимов:</b>
⚡ Быстрая — короткий бой
🏆 Рейтинговая — за рейтинг
💀 Хардкор — высокие ставки
🔥 Выживание — долгий бой
🎯 Спарринг — без ставок
⏰ На время — кто быстрее
🔄 Реверс — x2 урон по незащищённым

<i>Броня защищает от урона!</i>
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
        types.InlineKeyboardButton("💊 Лечение", callback_data="hero_heal"),
        types.InlineKeyboardButton("🎁 Бонус", callback_data="trade_daily")
    )
    bot.send_message(message.chat.id, "<b>👤 ГЕРОЙ</b>", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🏪 Торговля")
def trade_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛒 Магазин", callback_data="trade_shop"),
        types.InlineKeyboardButton("💎 Лимитированные", callback_data="trade_limited"),
        types.InlineKeyboardButton("💱 Рынок", callback_data="trade_market"),
        types.InlineKeyboardButton("💰 Продать", callback_data="trade_sell"),
        types.InlineKeyboardButton("📦 Мои лоты", callback_data="trade_my_lots"),
        types.InlineKeyboardButton("📤 Передать", callback_data="trade_transfer")
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
@bot.callback_query_handler(func=lambda call: call.data.startswith("dueltype_"))
def duel_type_selected(call):
    dtype = call.data.split("_")[1]
    info = DUEL_TYPES.get(dtype, {})
    
    # Запуск поиска соперника для этого типа
    start_duel_search(call, dtype, info.get("bet", 50))

@bot.callback_query_handler(func=lambda call: call.data == "find_opponent")
def find_opponent_generic(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for dtype, dinfo in DUEL_TYPES.items():
        markup.add(types.InlineKeyboardButton(
            f"{dinfo['name']} ({dinfo['bet']}💰)",
            callback_data=f"dueltype_{dtype}"
        ))
    bot.edit_message_text("<b>🔍 ВЫБЕРИТЕ ТИП ДУЭЛИ</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

def start_duel_search(call, duel_type, bet):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    # Очередь матчмейкинга
    queue = matchmaking_queue.get(duel_type, [])
    queue = [q for q in queue if q != user_id]
    
    if queue and queue[0] != user_id:
        opponent_id = queue.pop(0)
        matchmaking_queue[duel_type] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        # Начинаем дуэль
        if bet > 0:
            player.data["money"] -= bet
            opponent = Player(opponent_id)
            opponent.data["money"] -= bet
            player.save()
            opponent.save()
        
        duel = DuelInstance(user_id, opponent_id, duel_type, bet)
        active_duels[user_id] = duel
        active_duels[opponent_id] = duel
        
        # Уведомляем обоих
        bot.edit_message_text(f"⚔ Соперник найден! Дуэль начинается!\nТип: {DUEL_TYPES.get(duel_type, {}).get('name', duel_type)}", 
                              call.message.chat.id, call.message.message_id)
        
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        
        # Отправляем сообщение сопернику
        try:
            bot.send_message(int(opponent_id), f"⚔ Вас вызвали на дуэль!\nТип: {DUEL_TYPES.get(duel_type, {}).get('name', duel_type)}")
            # Здесь нужно показать интерфейс и сопернику (в реальном боте — через другой чат)
        except:
            pass
    else:
        # Ставим в очередь
        queue.append(user_id)
        matchmaking_queue[duel_type] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        # Бот через 5 секунд
        bot.edit_message_text(f"🔍 Поиск соперника... Ждите 5 сек.", call.message.chat.id, call.message.message_id)
        threading.Timer(5.0, start_bot_duel, args=[call.message.chat.id, call.message.message_id, user_id, duel_type, bet]).start()

def start_bot_duel(chat_id, message_id, user_id, duel_type, bet):
    if user_id in active_duels:
        return
    
    player = Player(user_id)
    if bet > 0 and player.data.get("money", 0) < bet:
        bot.edit_message_text(f"❌ Недостаточно монет!", chat_id, message_id)
        return
    
    bot_id = f"bot_{random.randint(100000, 999999)}"
    bot_level = random.randint(max(1, player.data.get("level", 1) - 3), player.data.get("level", 1) + 3)
    
    # Экипировка бота
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    for slot, itype in [("head", "helmet"), ("body", "armor"), ("legs", "boots")]:
        sitems = [k for k, v in items.items() if v.get("type") == itype and v.get("level_req", 1) <= bot_level]
        if sitems and random.random() < 0.7:
            equip[slot] = random.choice(sitems)
    wpns = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= bot_level]
    if wpns:
        equip["weapon"] = random.choice(wpns)
    
    users[bot_id] = {
        "username": f"bot_{bot_id}", "first_name": f"🤖 Бот Lv.{bot_level}",
        "money": 0, "level": bot_level, "exp": 0, "total_exp": 0,
        "hp": 200, "max_hp": 200, "mana": 80, "max_mana": 80,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000, "inventory": [], "equipment": equip,
        "enchantments": {}, "last_daily": None, "last_dungeon": None,
        "title": "Бот", "titles_collected": ["Бот"], "achievements": [],
        "clan": None, "clan_role": None, "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    if bet > 0:
        player.data["money"] -= bet
        player.save()
    
    duel = DuelInstance(user_id, bot_id, duel_type, bet)
    active_duels[user_id] = duel
    
    # Бот выбирает защиту
    duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
    # Бот выбирает атаку
    bot_skills = duel.get_available_skills(2)
    if bot_skills:
        duel.set_attack(2, random.choice(list(BODY_PARTS.keys())), random.choice(bot_skills))
    
    bot.edit_message_text(f"⚔ Бой с ботом! ({DUEL_TYPES.get(duel_type, {}).get('name', duel_type)})", chat_id, message_id)
    show_duel_interface(chat_id, message_id, duel, user_id)

def show_duel_interface(chat_id, message_id, duel, user_id):
    if not duel.active:
        finish_duel(chat_id, message_id, duel, user_id)
        return
    
    state_text = duel.get_state_text(user_id)
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    phase = duel.p1_phase if pn == 1 else duel.p2_phase
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if phase == "defend_select":
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']}",
                callback_data=f"def_{part}"
            ))
    
    elif phase == "attack_select":
        # Сначала цель
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🎯 {data['name']}",
                callback_data=f"tgt_{part}"
            ))
    
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="duel_refresh"))
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="duel_surrender"))
    
    try:
        bot.edit_message_text(state_text[:4000], chat_id, message_id, reply_markup=markup)
    except:
        pass

# Хранение временной цели
temp_target = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("def_"))
def defend_selected(call):
    part = call.data.split("_")[1]
    user_id = str(call.from_user.id)
    duel = active_duels.get(user_id)
    
    if not duel or not duel.active:
        return
    
    pn = 1 if user_id == duel.p1_id else 2
    duel.set_defend(pn, part)
    
    bot.answer_callback_query(call.id, f"🛡 Защита: {BODY_PARTS[part]['name']}")
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tgt_"))
def target_selected(call):
    part = call.data.split("_")[1]
    user_id = str(call.from_user.id)
    duel = active_duels.get(user_id)
    
    if not duel or not duel.active:
        return
    
    # Сохраняем цель
    temp_target[user_id] = part
    
    # Показываем навыки
    pn = 1 if user_id == duel.p1_id else 2
    skills = duel.get_available_skills(pn)
    
    state_text = duel.get_state_text(user_id) + f"\n🎯 Цель: <b>{BODY_PARTS[part]['name']}</b>\n<b>Выберите навык:</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for sid in skills[:8]:
        skill = SKILLS_DB.get(sid, {})
        name = skill.get("name", sid)
        mana = skill.get("mana_cost", 0)
        cd = skill.get("cooldown", 0)
        tier = skill.get("tier", 1)
        tier_text = "⭐" * tier
        
        markup.add(types.InlineKeyboardButton(
            f"{name} {tier_text} [{mana}MP] CD:{cd}",
            callback_data=f"skl_{sid}"
        ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="duel_back"))
    
    try:
        bot.edit_message_text(state_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "duel_back")
def duel_back(call):
    user_id = str(call.from_user.id)
    duel = active_duels.get(user_id)
    if duel:
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("skl_"))
def skill_selected(call):
    skill_id = call.data.split("_")[1]
    user_id = str(call.from_user.id)
    duel = active_duels.get(user_id)
    
    if not duel or not duel.active:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    target = temp_target.get(user_id, "body")
    pn = 1 if user_id == duel.p1_id else 2
    
    duel.set_attack(pn, target, skill_id)
    
    bot.answer_callback_query(call.id, "⚔ Атака!")
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data in ["duel_refresh", "duel_surrender"])
def duel_controls(call):
    user_id = str(call.from_user.id)
    duel = active_duels.get(user_id)
    
    if call.data == "duel_refresh":
        if duel and duel.active:
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
            bot.answer_callback_query(call.id, "✅ Обновлено")
        else:
            bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
    
    elif call.data == "duel_surrender":
        if duel and duel.active:
            duel.active = False
            # Определяем победителя
            pn = 1 if user_id == duel.p1_id else 2
            duel.winner = 3 - pn  # Противник выигрывает
            finish_duel(call.message.chat.id, call.message.message_id, duel, user_id)
            bot.answer_callback_query(call.id, "🏳 Вы сдались")

def finish_duel(chat_id, message_id, duel, user_id=None):
    """Завершение дуэли и рассылка результатов"""
    # Очистка
    for uid in list(active_duels.keys()):
        if active_duels[uid].battle_id == duel.battle_id:
            del active_duels[uid]
    
    # Удаление ботов
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") and uid in users:
            del users[uid]
    save_json(DATA_FILES['users'], users)
    
    # Очистка очереди
    for dtype in matchmaking_queue:
        q = matchmaking_queue[dtype]
        q = [x for x in q if x not in [duel.p1_id, duel.p2_id]]
        matchmaking_queue[dtype] = q
    save_json(DATA_FILES['matchmaking'], matchmaking_queue)
    
    if duel.winner == 0:
        result = "<b>🤝 НИЧЬЯ!</b>\nСтавки возвращены"
        
        for pid in [duel.p1_id, duel.p2_id]:
            if not pid.startswith("bot_"):
                p = Player(pid)
                p.data["draws"] += 1
                p.data["total_duels"] += 1
                if duel.bet > 0:
                    p.data["money"] += duel.bet
                p.save()
        
        bot.edit_message_text(result, chat_id, message_id)
    else:
        winner_id = duel.p1_id if duel.winner == 1 else duel.p2_id
        loser_id = duel.p2_id if duel.winner == 1 else duel.p1_id
        
        result_for_winner = ""
        result_for_loser = ""
        
        if not winner_id.startswith("bot_"):
            winner = Player(winner_id)
            winner.data["wins"] += 1
            winner.data["win_streak"] += 1
            winner.data["total_duels"] += 1
            winner.data["pvp_rating"] += random.randint(20, 35)
            if winner.data["win_streak"] > winner.data["best_streak"]:
                winner.data["best_streak"] = winner.data["win_streak"]
            if duel.bet > 0:
                winner.data["money"] += duel.bet * 2
            exp_w = duel.turn * 10 + duel.bet // 2
            winner.data["exp"] += exp_w
            winner.data["total_exp"] += exp_w
            check_level_up(winner)
            winner.save()
            
            result_for_winner = f"""
<b>🏆 ПОБЕДА!</b>

Противник: <b>{duel.get_player_name(3 - duel.winner)}</b>
💰 Приз: <b>{duel.bet * 2 if duel.bet > 0 else 0}💰</b>
✨ Опыт: +{exp_w}
📊 Ходов: <b>{duel.turn}</b>
"""
        
        if not loser_id.startswith("bot_"):
            loser = Player(loser_id)
            loser.data["losses"] += 1
            loser.data["win_streak"] = 0
            loser.data["total_duels"] += 1
            loser.data["pvp_rating"] = max(0, loser.data["pvp_rating"] - random.randint(10, 25))
            exp_l = duel.turn * 5 + duel.bet // 5
            loser.data["exp"] += exp_l
            loser.data["total_exp"] += exp_l
            check_level_up(loser)
            loser.save()
            
            result_for_loser = f"""
<b>💀 ПОРАЖЕНИЕ</b>

Противник: <b>{duel.get_player_name(duel.winner)}</b>
✨ Опыт: +{exp_l}
📊 Ходов: <b>{duel.turn}</b>
"""
        
        # Отправляем результат в этот чат
        current_pid = str(user_id) if user_id else duel.p1_id
        if current_pid == winner_id:
            bot.edit_message_text(result_for_winner, chat_id, message_id)
        else:
            bot.edit_message_text(result_for_loser, chat_id, message_id)
        
        # Отправляем результат сопернику
        other_pid = duel.p2_id if current_pid == duel.p1_id else duel.p1_id
        if not other_pid.startswith("bot_"):
            try:
                if other_pid == winner_id:
                    bot.send_message(int(other_pid), result_for_winner)
                else:
                    bot.send_message(int(other_pid), result_for_loser)
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
        types.InlineKeyboardButton("🧪 Зелья", callback_data="shopcat_potion")
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
            s = f"Урон: {item['damage'][0]}-{item['damage'][1]}"
            if "element" in item:
                s += f" | {ELEMENTS.get(item['element'], {}).get('name', '')}"
        elif item.get("type") in ["helmet", "armor", "boots"]:
            s = f"Защита: {item.get('defense', 0)}%"
            if "speed" in item:
                s += f" | Скорость: +{item['speed']}"
        elif item.get("type") == "potion":
            s = f"Лечение: {item.get('heal', 0)}"
        else:
            s = ""
        
        text += f"{r} <b>{item['name']}</b> [{rn}]\n📊 {s}\n💰 {item['price']} | Ур.{item.get('level_req', 1)}\n\n"
        
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
            markup.add(types.InlineKeyboardButton(f"Купить - {item['price']}💰", callback_data=f"buy_{ik}"))
    
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

@bot.callback_query_handler(func=lambda call: call.data in ["trade_sell", "trade_my_lots", "trade_transfer", "back_to_trade"])
def trade_misc(call):
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
                markup.add(types.InlineKeyboardButton(f"Снять: {item['name']}", callback_data=f"remlot_{lid}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data == "trade_transfer":
        bot.edit_message_text("📤 /transfer [номер] (ответьте на сообщение игрока)", call.message.chat.id, call.message.message_id)
    elif call.data == "back_to_trade":
        trade_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("remlot_"))
def remove_lot(call):
    lid = call.data.split("_")[1]
    uid = str(call.from_user.id)
    if lid in market_listings and str(market_listings[lid].get("seller_id")) == uid:
        listing = market_listings[lid]
        player = Player(uid)
        player.data["inventory"].append(listing["item_key"])
        player.save()
        del market_listings[lid]
        save_json(DATA_FILES['market'], market_listings)
        bot.answer_callback_query(call.id, "✅ Снят!")
    trade_misc(call)

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

⚔ Оружие: {player.get_weapon_damage()[0]}-{player.get_weapon_damage()[1]}
🛡 Защита: Г:{player.get_equipment_defense('head')}% Т:{player.get_equipment_defense('body')}% Н:{player.get_equipment_defense('legs')}%

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
            markup.add(types.InlineKeyboardButton(f"Экипировать: {item['name']}", callback_data=f"eq_{ik}"))
            markup.add(types.InlineKeyboardButton(f"Зачаровать: {item['name']}", callback_data=f"ench_{ik}"))
        elif item.get("type") == "potion":
            markup.add(types.InlineKeyboardButton(f"Использовать: {item['name']}", callback_data=f"use_{ik}"))
        
        markup.add(types.InlineKeyboardButton(f"Продать {item['name']}", callback_data=f"sel_{idx-1}"))
        idx += 1
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("eq_"))
def equip_item(call):
    ik = call.data.split("_")[1]
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("ench_"))
def enchant_item(call):
    ik = call.data.split("_")[1]
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("sel_"))
def sell_from_inv(call):
    idx = int(call.data.split("_")[1])
    user_id = call.from_user.id
    player = Player(user_id)
    
    if idx < 0 or idx >= len(player.data["inventory"]):
        bot.answer_callback_query(call.id, "❌ Ошибка!")
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
    ik = call.data.split("_")[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(ik) or limited_items.get(ik)
    if not item or item.get("type") != "potion":
        bot.answer_callback_query(call.id, "❌ Нельзя!")
        return
    
    if "heal" in item:
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + item["heal"])
    if "mana_restore" in item:
        player.data["mana"] = min(player.data["max_mana"], player.data["mana"] + item["mana_restore"])
    
    player.data["inventory"].remove(ik)
    player.save()
    
    bot.answer_callback_query(call.id, "✅ Использовано!")
    hero_inventory(call)

@bot.callback_query_handler(func=lambda call: call.data in ["hero_achievements", "hero_enchantments", "hero_equipped", "hero_history", "hero_heal", "back_to_hero"])
def hero_misc(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "hero_achievements":
        ach = [("fb", "🩸 Первая кровь", player.data["wins"] >= 1), ("war", "⚔ Воин", player.data["wins"] >= 10)]
        text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(player.data['achievements'])}/7)\n\n"
        for aid, name, cond in ach:
            done = aid in player.data["achievements"] or cond
            text += f"{'✅' if done else '🔒'} <b>{name}</b>\n"
            if cond and aid not in player.data["achievements"]:
                player.data["achievements"].append(aid)
        player.save()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_enchantments":
        ench = player.data.get("enchantments", {})
        if not ench:
            bot.edit_message_text("✨ Нет зачарований", call.message.chat.id, call.message.message_id)
            return
        text = "<b>✨ ЗАЧАРОВАНИЯ</b>\n\n"
        for ik, e in ench.items():
            item = items.get(ik) or limited_items.get(ik)
            if item:
                text += f"📦 {item['name']}: <b>{e.get('name', '')}</b>\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_equipped":
        eq = player.data["equipment"]
        text = "<b>👁 ЭКИПИРОВКА</b>\n\n"
        slots = {"weapon": "⚔ Оружие", "head": "👤 Голова", "body": "🦾 Тело", "legs": "🦿 Ноги"}
        for slot, sn in slots.items():
            ik = eq.get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                text += f"{sn}: <b>{item['name'] if item else '❌'}</b>\n"
            else:
                text += f"{sn}: ❌\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔴 Снять всё", callback_data="uneq_all"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_history":
        hist = player.data.get("battle_history", [])
        if not hist:
            bot.edit_message_text("📋 Пусто", call.message.chat.id, call.message.message_id)
            return
        text = "<b>📋 ИСТОРИЯ</b>\n\n"
        for b in hist[-5:]:
            icon = "🏆" if b.get("result") == "win" else "💀"
            text += f"{icon} vs {b.get('opponent', 'Нет')}\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_heal":
        potions = [k for k in player.data["inventory"] if items.get(k, {}).get("type") == "potion"]
        if not potions:
            bot.edit_message_text("💊 Нет зелий!", call.message.chat.id, call.message.message_id)
            return
        pk = potions[0]
        potion = items[pk]
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + potion.get("heal", 40))
        player.data["inventory"].remove(pk)
        player.save()
        bot.edit_message_text(f"💊 +{potion.get('heal', 40)} HP", call.message.chat.id, call.message.message_id)
    
    elif call.data == "back_to_hero":
        hero_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "uneq_all")
def unequip_all(call):
    user_id = call.from_user.id
    player = Player(user_id)
    for slot in ["weapon", "head", "body", "legs"]:
        ik = player.data["equipment"][slot]
        if ik:
            player.data["inventory"].append(ik)
            player.data["equipment"][slot] = None
    player.save()
    bot.answer_callback_query(call.id, "✅ Снято!")
    hero_misc(call)

# ==================== МИР ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_dungeons")
def world_dungeons(call):
    text = """
<b>🏰 ПОДЗЕМЕЛЬЯ</b>

🐺 Логово волка (3 босса, Ур. 1+)
🕷 Паучьи пещеры (3 босса, Ур. 5+)
💀 Катакомбы (3 босса, Ур. 10+)
🐉 Драконье логово (3 босса, Ур. 15+)
👹 Бездна (3 босса, Ур. 25+)

🪓 Босс-манекен (1M HP) — средняя награда
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, name in enumerate(["🐺 Логово волка", "🕷 Паучьи пещеры", "💀 Катакомбы", "🐉 Драконье логово", "👹 Бездна"], 1):
        markup.add(types.InlineKeyboardButton(name, callback_data=f"dung_{i}"))
    markup.add(types.InlineKeyboardButton("🪓 Босс-манекен (1M HP)", callback_data="dung_boss_dummy"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dung_"))
def start_dungeon(call):
    if call.data == "dung_boss_dummy":
        # Особый босс-манекен
        user_id = call.from_user.id
        player = Player(user_id)
        
        if player.data.get("last_dungeon"):
            last = datetime.fromisoformat(player.data["last_dungeon"])
            if (datetime.now() - last) < timedelta(hours=1):
                r = timedelta(hours=1) - (datetime.now() - last)
                bot.answer_callback_query(call.id, f"⏰ {r.seconds//60} мин.")
                return
        
        dummy_id = f"dummy_{random.randint(100000, 999999)}"
        users[dummy_id] = {
            "username": "dummy", "first_name": "🪓 Босс-манекен",
            "money": 0, "level": 100, "exp": 0, "total_exp": 0,
            "hp": 1000000, "max_hp": 1000000, "mana": 0, "max_mana": 0,
            "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
            "total_duels": 0, "pvp_rating": 1000, "inventory": [], "equipment": {"weapon": None, "head": None, "body": None, "legs": None},
            "enchantments": {}, "last_daily": None, "last_dungeon": None,
            "title": "Босс", "titles_collected": [], "achievements": [],
            "clan": None, "clan_role": None, "registration_date": datetime.now().isoformat(),
            "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
        }
        save_json(DATA_FILES['users'], users)
        
        # Создаём специальную дуэль с огромным HP
        duel = DuelInstance(user_id, dummy_id, "survival", 0)
        duel.p2_hp = 1000000
        duel.p2_max_hp = 1000000
        duel.max_turns = 999
        active_duels[str(user_id)] = duel
        
        duel.set_defend(2, "head")
        duel.set_attack(2, "body", "quick_strike")
        
        player.data["last_dungeon"] = datetime.now().isoformat()
        player.save()
        
        bot.edit_message_text("🪓 Бой с Боссом-манекеном (1M HP)!", call.message.chat.id, call.message.message_id)
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        return
    
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
    
    # Создаём первого босса данжа
    boss_level = level_reqs[dl - 1] * 2 + random.randint(1, 3)
    boss_id = f"boss_{random.randint(100000, 999999)}"
    
    bosses = ["🐺 Волк-страж", "🕷 Паук-охотник", "💀 Скелет-воин", "🐉 Молодой дракон", "👹 Бес"]
    
    users[boss_id] = generate_boss(boss_level, bosses[dl - 1])
    save_json(DATA_FILES['users'], users)
    
    duel = DuelInstance(user_id, boss_id, "quick", 0)
    active_duels[str(user_id)] = duel
    
    dungeon_progress[str(user_id)] = {"dungeon_level": dl, "boss_index": 1, "total_bosses": 3, "reward_base": dl * 100}
    save_json(DATA_FILES['dungeons'], dungeon_progress)
    
    duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
    bot_skills = duel.get_available_skills(2)
    if bot_skills:
        duel.set_attack(2, random.choice(list(BODY_PARTS.keys())), random.choice(bot_skills))
    
    bot.edit_message_text(f"⚔ Босс 1/3: <b>{bosses[dl-1]}</b>", call.message.chat.id, call.message.message_id)
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

def generate_boss(level, name):
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    for slot, itype in [("head", "helmet"), ("body", "armor"), ("legs", "boots")]:
        sitems = [k for k, v in items.items() if v.get("type") == itype and v.get("level_req", 1) <= level]
        if sitems and random.random() < 0.8:
            equip[slot] = random.choice(sitems)
    wpns = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= level]
    if wpns:
        equip["weapon"] = random.choice(wpns)
    
    return {
        "username": f"boss_{level}", "first_name": name,
        "money": 0, "level": level, "exp": 0, "total_exp": 0,
        "hp": 200, "max_hp": 200, "mana": 80, "max_mana": 80,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000, "inventory": [], "equipment": equip,
        "enchantments": {}, "last_daily": None, "last_dungeon": None,
        "title": "Босс", "titles_collected": [], "achievements": [],
        "clan": None, "clan_role": None, "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }

# ==================== ТУРНИРЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_tournaments")
def world_tournaments(call):
    if not tournaments.get("active"):
        tournaments["active"] = {
            "name": "Еженедельный турнир",
            "participants": [],
            "rounds": [],
            "current_round": 0,
            "prize_pool": 5000,
            "status": "registration"
        }
        save_json(DATA_FILES['tournaments'], tournaments)
    
    tour = tournaments["active"]
    
    text = f"""
<b>🏟 ТУРНИР</b>

<b>{tour['name']}</b>
Участников: {len(tour.get('participants', []))}/16
Раунд: {tour.get('current_round', 0)}/{len(tour.get('rounds', []))}
Приз: <b>{tour.get('prize_pool', 0)}💰</b>
Взнос: 500💰
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
    if len(participants) >= 16:
        bot.answer_callback_query(call.id, "❌ Заполнен!")
        return
    
    player.data["money"] -= 500
    player.save()
    
    participants.append(str(user_id))
    tour["participants"] = participants
    tour["prize_pool"] = tour.get("prize_pool", 0) + 500
    
    # Если набралось 16 — начинаем турнир
    if len(participants) == 16:
        tour["status"] = "in_progress"
        tour["rounds"] = generate_tournament_bracket(participants)
        tour["current_round"] = 1
    
    tournaments["active"] = tour
    save_json(DATA_FILES['tournaments'], tournaments)
    
    bot.answer_callback_query(call.id, "✅ Зарегистрированы!")

def generate_tournament_bracket(participants):
    """Генерация сетки турнира"""
    random.shuffle(participants)
    rounds = []
    current = participants
    while len(current) > 1:
        pairs = []
        for i in range(0, len(current), 2):
            if i + 1 < len(current):
                pairs.append([current[i], current[i+1]])
        rounds.append(pairs)
        current = [f"winner_{i}" for i in range(len(pairs))]
    return rounds

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

# ==================== ИВЕНТЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_events")
def world_events(call):
    current_event = events.get("current", {})
    if not current_event or datetime.fromisoformat(current_event.get("expires", "2000-01-01")) < datetime.now():
        rewards = [
            {"type": "money", "amount": random.randint(500, 2000), "name": "💰 Монеты"},
            {"type": "item", "item_key": random.choice(list(items.keys())), "name": "🎁 Предмет"},
            {"type": "enchant", "enchant": random.choice(ENCHANT_EFFECTS), "name": "✨ Зачарование"}
        ]
        new_event = {
            "name": random.choice(["🌋 Извержение", "❄ Ледяной шторм", "⚡ Гроза", "🌑 Затмение", "✨ Звездопад"]),
            "description": "Выиграйте 3 дуэли для получения награды!",
            "target": 3,
            "progress": {},
            "reward": random.choice(rewards),
            "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        events["current"] = new_event
        save_json(DATA_FILES['events'], events)
    
    ev = events["current"]
    uid = str(call.from_user.id)
    prog = ev.get("progress", {}).get(uid, 0)
    time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
    mins = max(0, time_left.seconds // 60)
    
    reward_text = ""
    rw = ev.get("reward", {})
    if rw.get("type") == "money":
        reward_text = f"💰 {rw.get('amount', 0)} монет"
    elif rw.get("type") == "item":
        item = items.get(rw.get("item_key", ""), {})
        reward_text = f"🎁 {item.get('name', 'Предмет')}"
    elif rw.get("type") == "enchant":
        reward_text = f"✨ {rw.get('enchant', {}).get('name', 'Зачарование')}"
    
    text = f"""
<b>🌍 ИВЕНТ</b>

<b>{ev['name']}</b>
📝 {ev['description']}
🎁 Награда: <b>{reward_text}</b>
📊 Прогресс: {prog}/{ev['target']}
⏰ {mins} мин.
"""
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

@bot.callback_query_handler(func=lambda call: call.data in ["world_help", "back_to_world"])
def world_misc(call):
    if call.data == "world_help":
        text = "<b>ℹ ПОМОЩЬ</b>\n⚔ 7 типов дуэлей\n🛒 /shop\n👤 /stats"
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
        text = f"<b>🛡 {player.data['clan']}</b>\n👥 {len(clan.get('members', []))} уч."
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave"))
    else:
        text = "<b>🛡 КЛАНЫ</b>\n/createclan [имя]\n/joinclan [имя]"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("📋 Список", callback_data="clan_list"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(commands=['createclan', 'joinclan'])
def clan_cmd(message):
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
        player.data["max_hp"] += 20
        player.data["max_mana"] += 10
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
def misc_cmd(message):
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
            "item_key": ik, "price": price, "created_at": datetime.now().isoformat()
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
        types.InlineKeyboardButton("⛔ Бан", callback_data="adm_ban"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_bc"),
        types.InlineKeyboardButton("🔄 Сброс дня", callback_data="adm_reset"),
        types.InlineKeyboardButton("👁 Инфо игрока", callback_data="adm_info"),
        types.InlineKeyboardButton("✅ Разбан", callback_data="adm_unban"),
        types.InlineKeyboardButton("🏟 Управление турнирами", callback_data="adm_tour"),
        types.InlineKeyboardButton("🌍 Управление ивентами", callback_data="adm_event")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_handlers(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Нет доступа!")
        return
    
    action = call.data.split("_")[1]
    
    if action == "stats":
        text = f"👥 {len(users)} | 💰 {sum(u.get('money',0) for u in users.values())} | ⚔ {sum(u.get('total_duels',0) for u in users.values())}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    
    elif action == "money":
        bot.send_message(call.message.chat.id, "💰 /adm_givemoney @username [сумма]")
    elif action == "item":
        bot.send_message(call.message.chat.id, "🎁 /adm_giveitem @username [item_key]")
    elif action == "ban":
        bot.send_message(call.message.chat.id, "⛔ /adm_ban @username [причина]")
    elif action == "bc":
        bot.send_message(call.message.chat.id, "📢 /adm_broadcast [текст]")
    elif action == "reset":
        bot.send_message(call.message.chat.id, "🔄 /adm_reset @username")
    elif action == "info":
        bot.send_message(call.message.chat.id, "👁 /adm_info @username")
    elif action == "unban":
        bot.send_message(call.message.chat.id, "✅ /adm_unban @username")
    elif action == "tour":
        bot.send_message(call.message.chat.id, "🏟 /adm_tournament_create [название]\n🏟 /adm_tournament_start\n🏟 /adm_tournament_reset")
    elif action == "event":
        bot.send_message(call.message.chat.id, "🌍 /adm_event_create [название] [цель] [тип_награды]\n🌍 /adm_event_reset")

@bot.message_handler(commands=['adm_givemoney', 'adm_giveitem', 'adm_ban', 'adm_unban', 'adm_broadcast', 'adm_reset', 'adm_info', 'adm_tournament_create', 'adm_tournament_start', 'adm_tournament_reset', 'adm_event_create', 'adm_event_reset'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd == "adm_givemoney":
            username = parts[1].replace('@', '')
            amount = int(parts[2])
            for uid, data in users.items():
                if data.get("username") == username:
                    p = Player(uid)
                    p.data["money"] += amount
                    p.save()
                    bot.send_message(message.chat.id, f"✅ {amount}💰 → @{username}")
                    return
            bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "adm_giveitem":
            username = parts[1].replace('@', '')
            ik = parts[2]
            for uid, data in users.items():
                if data.get("username") == username:
                    p = Player(uid)
                    p.data["inventory"].append(ik)
                    p.save()
                    bot.send_message(message.chat.id, f"✅ {ik} → @{username}")
                    return
            bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "adm_ban":
            username = parts[1].replace('@', '')
            reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение"
            for uid, data in users.items():
                if data.get("username") == username:
                    banned_users[uid] = {"reason": reason, "banned_at": datetime.now().isoformat()}
                    save_json(DATA_FILES['bans'], banned_users)
                    bot.send_message(message.chat.id, f"⛔ @{username} забанен!")
                    return
            bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "adm_unban":
            username = parts[1].replace('@', '')
            for uid in list(banned_users.keys()):
                if users.get(uid, {}).get("username") == username:
                    del banned_users[uid]
                    save_json(DATA_FILES['bans'], banned_users)
                    bot.send_message(message.chat.id, f"✅ @{username} разбанен!")
                    return
            bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "adm_broadcast":
            text = message.text.replace('/adm_broadcast', '', 1).strip()
            if text:
                s, f = 0, 0
                for uid in users:
                    try:
                        bot.send_message(int(uid), f"📢 {text}")
                        s += 1
                    except:
                        f += 1
                bot.send_message(message.chat.id, f"✅ {s} | ❌ {f}")
        
        elif cmd == "adm_reset":
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
        
        elif cmd == "adm_info":
            username = parts[1].replace('@', '')
            for uid, data in users.items():
                if data.get("username") == username:
                    p = Player(uid)
                    d = p.data
                    text = f"<b>👤 @{username}</b>\nID: {uid}\nИмя: {d['first_name']}\nУр.: {d['level']}\n💰 {d['money']}\nРейтинг: {d['pvp_rating']}"
                    bot.send_message(message.chat.id, text)
                    return
            bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "adm_tournament_create":
            name = parts[1] if len(parts) > 1 else "Турнир"
            tournaments["active"] = {
                "name": name, "participants": [], "rounds": [],
                "current_round": 0, "prize_pool": 5000, "status": "registration"
            }
            save_json(DATA_FILES['tournaments'], tournaments)
            bot.send_message(message.chat.id, f"✅ Турнир '{name}' создан!")
        
        elif cmd == "adm_tournament_start":
            tour = tournaments.get("active", {})
            if tour and len(tour.get("participants", [])) >= 2:
                tour["status"] = "in_progress"
                tour["rounds"] = generate_tournament_bracket(tour["participants"])
                tour["current_round"] = 1
                save_json(DATA_FILES['tournaments'], tournaments)
                bot.send_message(message.chat.id, "✅ Турнир начат!")
            else:
                bot.send_message(message.chat.id, "❌ Недостаточно участников!")
        
        elif cmd == "adm_tournament_reset":
            tournaments["active"] = None
            save_json(DATA_FILES['tournaments'], tournaments)
            bot.send_message(message.chat.id, "✅ Турнир сброшен!")
        
        elif cmd == "adm_event_create":
            name = parts[1] if len(parts) > 1 else "Ивент"
            target = int(parts[2]) if len(parts) > 2 else 3
            events["current"] = {
                "name": name, "description": f"Выполните цель: {target}",
                "target": target, "progress": {},
                "reward": {"type": "money", "amount": 1000, "name": "💰 1000 монет"},
                "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
            }
            save_json(DATA_FILES['events'], events)
            bot.send_message(message.chat.id, f"✅ Ивент '{name}' создан!")
        
        elif cmd == "adm_event_reset":
            events["current"] = {}
            save_json(DATA_FILES['events'], events)
            bot.send_message(message.chat.id, "✅ Ивент сброшен!")
    
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
    print("✅ 7 типов дуэлей с разными правилами")
    print("✅ Броня уменьшает урон (макс 80%)")
    print("✅ Пошаговые дуэли: защита → атака")
    print("✅ Навыки с кулдаунами (слабые/средние/сильные/ультимейты)")
    print("✅ Данжи с 3 боссами + манекен 1M HP")
    print("✅ Турниры с сеткой плей-офф")
    print("✅ Ивенты с реальными наградами")
    print("✅ Админ-панель: 12 функций")
    print("✅ Результаты присылаются обоим игрокам")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
