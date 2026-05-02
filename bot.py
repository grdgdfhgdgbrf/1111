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
    'events': 'events.json',
    'bans': 'bans.json',
    'enchantments': 'enchantments.json',
    'matchmaking': 'matchmaking.json',
    'duels': 'active_duels.json',
    'dungeons': 'dungeons.json'
}

def load_json(filename, default=None):
    if default is None:
        default = {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
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
    "dragon_helmet": {"name": "🐉 Шлем дракона", "defense": 18, "hp_bonus": 50, "price": 2000, "type": "helmet", "slot": "head", "rarity": "epic", "level_req": 20, "enchantable": True},
    "crown_of_wisdom": {"name": "👑 Корона мудрости", "defense": 12, "hp_bonus": 35, "mana_bonus": 40, "price": 3500, "type": "helmet", "slot": "head", "rarity": "legendary", "level_req": 28, "enchantable": True}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "defense": 5, "hp_bonus": 25, "price": 80, "type": "armor", "slot": "body", "rarity": "common", "level_req": 1, "enchantable": True},
    "chainmail": {"name": "⛓ Кольчуга", "defense": 12, "hp_bonus": 50, "price": 400, "type": "armor", "slot": "body", "rarity": "uncommon", "level_req": 8, "enchantable": True},
    "plate_armor": {"name": "🛡 Латный доспех", "defense": 22, "hp_bonus": 90, "price": 1500, "type": "armor", "slot": "body", "rarity": "rare", "level_req": 15, "enchantable": True},
    "phoenix_armor": {"name": "🦅 Броня феникса", "defense": 40, "hp_bonus": 200, "price": 8000, "type": "armor", "slot": "body", "rarity": "legendary", "level_req": 30, "enchantable": True}
}

BOOTS = {
    "leather_boots": {"name": "👢 Кожаные сапоги", "defense": 2, "speed": 8, "price": 100, "type": "boots", "slot": "legs", "rarity": "common", "level_req": 1, "enchantable": True},
    "wind_boots": {"name": "🌪 Сапоги ветра", "defense": 4, "speed": 18, "price": 900, "type": "boots", "slot": "legs", "rarity": "rare", "level_req": 12, "enchantable": True},
    "hermes_boots": {"name": "👟 Сандалии Гермеса", "defense": 12, "speed": 45, "price": 12000, "type": "boots", "slot": "legs", "rarity": "legendary", "level_req": 35, "enchantable": True}
}

WEAPONS = {
    "rusty_sword": {"name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 1, "skills": ["quick_strike", "slash"], "enchantable": True},
    "flame_blade": {"name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 7, "skills": ["fire_slash", "inferno_strike", "flame_wave"], "enchantable": True, "element": "fire"},
    "frost_axe": {"name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 10, "skills": ["frost_strike", "ice_shatter", "blizzard"], "enchantable": True, "element": "ice"},
    "storm_staff": {"name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500, "type": "weapon", "slot": "weapon", "rarity": "rare", "level_req": 14, "skills": ["lightning_bolt", "thunder_storm", "chain_lightning"], "enchantable": True, "element": "lightning"},
    "shadow_dagger": {"name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "slot": "weapon", "rarity": "epic", "level_req": 22, "skills": ["shadow_strike", "assassinate", "soul_drain"], "enchantable": True, "element": "dark"},
    "divine_spear": {"name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "slot": "weapon", "rarity": "legendary", "level_req": 28, "skills": ["holy_strike", "divine_judgment", "purification"], "enchantable": True, "element": "light"},
    "death_scythe": {"name": "💀 Коса смерти", "damage": (40, 65), "price": 12000, "type": "weapon", "slot": "weapon", "rarity": "mythic", "level_req": 35, "skills": ["reap", "death_sentence", "soul_harvest"], "enchantable": True, "element": "dark"}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 200, "price": 350, "type": "potion", "rarity": "rare", "level_req": 15},
    "mana_potion": {"name": "💎 Зелье маны", "mana_restore": 60, "price": 60, "type": "potion", "rarity": "common", "level_req": 5}
}

LIMITED_ITEMS = {
    "thunderfury": {"name": "⚡ Ярость грома", "damage": (60, 95), "total": 3, "remaining": 3, "price": 50000, "type": "weapon", "slot": "weapon", "rarity": "divine", "element": "lightning", "skills": ["thunder_gods_wrath", "eye_of_the_storm", "lightning_apocalypse"], "enchantable": True}
}

ALL_ITEMS = {}
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(BOOTS)
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(POTIONS)

# ==================== БАЗА НАВЫКОВ ====================
SKILLS_DB = {
    # Базовые (всегда доступны)
    "quick_strike": {"name": "⚡ Быстрый удар", "damage_mult": 0.8, "mana_cost": 5, "cooldown": 0, "hits": 2},
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 8, "cooldown": 0},
    "defend": {"name": "🛡 Укрепиться", "defense_boost": 30, "mana_cost": 10, "cooldown": 1},
    
    # Огненные
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.5, "mana_cost": 18, "element": "fire", "burn_chance": 30, "cooldown": 1},
    "inferno_strike": {"name": "🌋 Инферно удар", "damage_mult": 2.2, "mana_cost": 35, "element": "fire", "burn_chance": 60, "cooldown": 3},
    "flame_wave": {"name": "🔥 Волна пламени", "damage_mult": 2.5, "mana_cost": 45, "element": "fire", "cooldown": 4},
    
    # Ледяные
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.4, "mana_cost": 16, "element": "ice", "freeze_chance": 25, "cooldown": 1},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.0, "mana_cost": 30, "element": "ice", "freeze_chance": 50, "cooldown": 2},
    "blizzard": {"name": "🌨 Метель", "damage_mult": 2.4, "mana_cost": 42, "element": "ice", "cooldown": 3},
    
    # Молнии
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.6, "mana_cost": 20, "element": "lightning", "stun_chance": 20, "cooldown": 1},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.3, "mana_cost": 40, "element": "lightning", "cooldown": 3},
    "chain_lightning": {"name": "⚡ Цепная молния", "damage_mult": 1.8, "mana_cost": 28, "element": "lightning", "cooldown": 2},
    
    # Теневые
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.6, "mana_cost": 22, "element": "dark", "cooldown": 1},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.2, "mana_cost": 55, "element": "dark", "cooldown": 4},
    "soul_drain": {"name": "💀 Похищение души", "damage_mult": 2.0, "mana_cost": 35, "element": "dark", "life_steal": 0.4, "cooldown": 3},
    
    # Святые
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.5, "mana_cost": 20, "element": "light", "cooldown": 1},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 2.8, "mana_cost": 48, "element": "light", "cooldown": 3},
    "purification": {"name": "🌟 Очищение", "hp_restore": 80, "mana_cost": 35, "element": "light", "cooldown": 3},
    
    # Ульты
    "reap": {"name": "💀 Жатва", "damage_mult": 2.5, "mana_cost": 42, "element": "dark", "life_steal": 0.3, "cooldown": 3},
    "death_sentence": {"name": "☠ Смертный приговор", "damage_mult": 4.0, "mana_cost": 70, "element": "dark", "cooldown": 5},
    "soul_harvest": {"name": "👻 Сбор душ", "damage_mult": 2.8, "mana_cost": 50, "element": "dark", "life_steal": 0.5, "cooldown": 4},
    "thunder_gods_wrath": {"name": "⚡ Гнев бога грома", "damage_mult": 4.5, "mana_cost": 80, "element": "lightning", "stun_chance": 50, "cooldown": 5},
    "eye_of_the_storm": {"name": "🌀 Глаз бури", "damage_mult": 3.0, "mana_cost": 55, "element": "lightning", "cooldown": 3},
    "lightning_apocalypse": {"name": "⚡ Молниевый апокалипсис", "damage_mult": 5.0, "mana_cost": 90, "element": "lightning", "cooldown": 6}
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
enchantments_data = load_json(DATA_FILES['enchantments'], {})
matchmaking_queue = load_json(DATA_FILES['matchmaking'], {"quick": [], "ranked": [], "hardcore": [], "sparring": []})
active_duels_data = load_json(DATA_FILES['duels'], {})
dungeons_data = load_json(DATA_FILES['dungeons'], {})

# ==================== КЛАСС ИГРОКА ====================
class Player:
    def __init__(self, user_id, username=None, first_name=None):
        self.user_id = str(user_id)
        if self.user_id not in users:
            # Пытаемся получить username через бота
            try:
                user_info = bot.get_chat(user_id)
                username = username or user_info.username or f"user_{user_id}"
                first_name = first_name or user_info.first_name or "Игрок"
            except:
                username = username or f"user_{user_id}"
                first_name = first_name or "Игрок"
            
            users[self.user_id] = {
                "username": username,
                "first_name": first_name,
                "money": 500,
                "level": 1,
                "exp": 0,
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
        """Получить защиту экипировки в слоте"""
        ik = self.data["equipment"].get(slot)
        if not ik:
            return 0
        item = items.get(ik) or limited_items.get(ik)
        if not item:
            return 0
        base_def = item.get("defense", 0)
        # Зачарования
        ench = self.data.get("enchantments", {}).get(ik, {})
        if ench.get("effect") == "defense_bonus":
            base_def += ench.get("value", 0)
        return base_def
    
    def get_weapon_damage(self):
        """Получить урон оружия"""
        ik = self.data["equipment"].get("weapon")
        if not ik:
            return (5, 10)  # Базовый урон без оружия
        item = items.get(ik) or limited_items.get(ik)
        if not item or "damage" not in item:
            return (5, 10)
        dmg = list(item["damage"])
        # Зачарования
        ench = self.data.get("enchantments", {}).get(ik, {})
        if ench.get("effect") == "damage_boost":
            boost = ench.get("value", 0) / 100
            dmg[0] = int(dmg[0] * (1 + boost))
            dmg[1] = int(dmg[1] * (1 + boost))
        if ench.get("effect") == "fire_damage":
            dmg[0] += ench.get("value", 0)
            dmg[1] += ench.get("value", 0)
        return tuple(dmg)

# ==================== ХРАНИЛИЩЕ ДУЭЛЕЙ ====================
active_duels = {}  # battle_id -> DuelInstance

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
        
        # HP одинаковые
        avg_hp = 120
        self.p1_hp = avg_hp
        self.p2_hp = avg_hp
        self.p1_max_hp = avg_hp
        self.p2_max_hp = avg_hp
        
        self.p1_mp = 60
        self.p2_mp = 60
        self.p1_max_mp = 60
        self.p2_max_mp = 60
        
        # Фазы: защита -> атака
        self.p1_phase = "defend"  # defend, attack
        self.p2_phase = "defend"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_attack_data = None  # (target, skill_id)
        self.p2_attack_data = None
        
        # Кто ходит первым (меняется каждый раунд)
        self.round = 1
        self.attacker_order = random.choice([1, 2])  # Кто атакует первым в этом раунде
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Эффекты
        self.p1_effects = []
        self.p2_effects = []
        
        # Таймаут для AFK
        self.last_action_time = time.time()
        self.afk_timeout = 120  # 2 минуты
        
        # Арена
        self.arena = random.choice(["colosseum", "forest", "volcano", "void"])
        
        self.log_p1.append("⚔ Битва началась!")
        self.log_p2.append("⚔ Битва началась!")
    
    def get_player_name(self, num):
        return self.p1.data["first_name"] if num == 1 else self.p2.data["first_name"]
    
    def get_available_skills(self, player_num):
        player = self.p1 if player_num == 1 else self.p2
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        equip = player.data["equipment"]
        
        available = []
        
        # Базовые всегда
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
        """Игрок выбирает защиту и ждёт второго"""
        self.last_action_time = time.time()
        if player_num == 1:
            self.p1_defend = part
            self.p1_phase = "waiting"
        else:
            self.p2_defend = part
            self.p2_phase = "waiting"
        
        # Проверяем, выбрали ли оба защиту
        if self.p1_defend and self.p2_defend:
            # Переходим к фазе атаки
            self.p1_phase = "attack"
            self.p2_phase = "attack"
    
    def set_attack(self, player_num, target, skill_id):
        """Игрок выбирает атаку и ждёт второго"""
        self.last_action_time = time.time()
        if player_num == 1:
            self.p1_attack_data = (target, skill_id)
            self.p1_phase = "waiting"
        else:
            self.p2_attack_data = (target, skill_id)
            self.p2_phase = "waiting"
        
        # Проверяем, выбрали ли оба атаку
        if self.p1_attack_data and self.p2_attack_data:
            self._resolve_round()
    
    def _resolve_round(self):
        """Разрешение раунда: атакуют оба"""
        # Обработка эффектов
        self._process_effects(1)
        self._process_effects(2)
        
        # Атака первого
        first = self.attacker_order
        second = 3 - first
        
        self._do_attack(first, second, self.p1_attack_data if first == 1 else self.p2_attack_data,
                       self.p2_defend if first == 1 else self.p1_defend)
        
        if self.p1_hp <= 0 or self.p2_hp <= 0:
            self._check_end()
            return
        
        # Атака второго
        self._do_attack(second, first, self.p1_attack_data if second == 1 else self.p2_attack_data,
                       self.p2_defend if second == 1 else self.p1_defend)
        
        self._check_end()
        
        # Сброс для следующего раунда
        self.p1_phase = "defend"
        self.p2_phase = "defend"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_attack_data = None
        self.p2_attack_data = None
        
        # Меняем очерёдность
        self.attacker_order = 3 - self.attacker_order
        
        # Декей кулдаунов
        for cd_dict in [self.p1_cooldowns, self.p2_cooldowns]:
            for sid in list(cd_dict.keys()):
                cd_dict[sid] -= 1
                if cd_dict[sid] <= 0:
                    del cd_dict[sid]
        
        self.round += 1
        self.turn = self.round
        
        if self.round > self.max_turns:
            self.active = False
            self.winner = 0
    
    def _do_attack(self, attacker, defender, attack_data, defend_part):
        if not attack_data:
            return
        
        target_part, skill_id = attack_data
        skill = SKILLS_DB.get(skill_id, {"name": "Атака", "damage_mult": 1.0, "mana_cost": 0})
        
        # Проверка маны
        mc = skill.get("mana_cost", 0)
        if attacker == 1:
            if self.p1_mp < mc:
                self.log_p1.append(f"❌ Недостаточно маны!")
                self.log_p2.append(f"❌ {self.get_player_name(attacker)} не хватило маны!")
                return
            self.p1_mp -= mc
        else:
            if self.p2_mp < mc:
                self.log_p2.append(f"❌ Недостаточно маны!")
                self.log_p1.append(f"❌ {self.get_player_name(attacker)} не хватило маны!")
                return
            self.p2_mp -= mc
        
        # Урон оружия
        attacker_player = self.p1 if attacker == 1 else self.p2
        min_d, max_d = attacker_player.get_weapon_damage()
        base_dmg = random.randint(min_d, max_d)
        
        # Множитель навыка
        dmg = int(base_dmg * skill.get("damage_mult", 1.0))
        
        # Множитель части тела
        body_mult = BODY_PARTS.get(target_part, {}).get("multiplier", 1.0)
        dmg = int(dmg * body_mult)
        
        # Защита экипировки (если атакуют в эту часть)
        defender_player = self.p2 if attacker == 1 else self.p1
        slot_map = {"head": "head", "body": "body", "legs": "legs"}
        def_slot = slot_map.get(target_part)
        if def_slot:
            armor_def = defender_player.get_equipment_defense(def_slot)
            # Броня уменьшает урон, а не даёт HP
            dmg = max(1, dmg - armor_def)
            
            # Дополнительная защита если игрок защищает эту часть
            if defend_part == target_part:
                dmg = max(0, dmg - 15)  # Доп. защита от правильного выбора
        
        # Крит (базовый шанс 10%)
        is_crit = random.random() < 0.10
        if is_crit:
            dmg = int(dmg * 1.5)
        
        # Применение урона
        if dmg > 0:
            if defender == 1:
                self.p1_hp = max(0, self.p1_hp - dmg)
            else:
                self.p2_hp = max(0, self.p2_hp - dmg)
            
            crit_text = "💥 КРИТ! " if is_crit else ""
            msg = f"{crit_text}⚔ {self.get_player_name(attacker)} [{skill['name']}] → {BODY_PARTS[target_part]['name']}: -{dmg} HP"
            self.log_p1.append(msg)
            self.log_p2.append(msg)
            
            # Вампиризм
            if "life_steal" in skill:
                heal = int(dmg * skill["life_steal"])
                if attacker == 1:
                    self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
                else:
                    self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
                msg2 = f"💚 Вампиризм +{heal} HP"
                self.log_p1.append(msg2)
                self.log_p2.append(msg2)
            
            # Эффекты
            self._apply_effects(defender, skill)
        else:
            msg = f"🛡 {self.get_player_name(attacker)} бьёт в {BODY_PARTS[target_part]['name']}, но броня {self.get_player_name(defender)} поглотила урон!"
            self.log_p1.append(msg)
            self.log_p2.append(msg)
        
        # Лечение
        if "hp_restore" in skill:
            heal = skill["hp_restore"]
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
        
        # Кулдауны
        cooldowns = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
        if "cooldown" in skill and skill["cooldown"] > 0:
            cooldowns[skill_id] = skill["cooldown"]
    
    def _apply_effects(self, target, skill):
        effects = []
        if "burn_chance" in skill and random.random() * 100 < skill["burn_chance"]:
            effects.append({"type": "burn", "duration": 3})
        if "freeze_chance" in skill and random.random() * 100 < skill["freeze_chance"]:
            effects.append({"type": "freeze", "duration": 2})
        if "stun_chance" in skill and random.random() * 100 < skill["stun_chance"]:
            effects.append({"type": "stun", "duration": 1})
        
        if target == 1:
            self.p1_effects.extend(effects)
        else:
            self.p2_effects.extend(effects)
    
    def _process_effects(self, player_num):
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        hp = self.p1_hp if player_num == 1 else self.p2_hp
        
        for eff in effects[:]:
            if eff["type"] == "burn":
                d = 10
                hp -= d
            elif eff["type"] == "poison":
                d = 12
                hp -= d
            
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
    
    def check_afk(self):
        """Проверка AFK"""
        if time.time() - self.last_action_time > self.afk_timeout:
            # Определяем кто AFK
            if self.p1_phase == "waiting" and self.p2_phase != "waiting":
                self.active = False
                self.winner = 2
                return True
            elif self.p2_phase == "waiting" and self.p1_phase != "waiting":
                self.active = False
                self.winner = 1
                return True
        return False
    
    def get_state_text(self, for_player_id):
        pn = 1 if str(for_player_id) == self.p1_id else 2
        phase = self.p1_phase if pn == 1 else self.p2_phase
        log = self.log_p1 if pn == 1 else self.log_p2
        
        def bar(cur, mx, icon):
            pct = cur / mx * 100 if mx > 0 else 0
            f = int(pct / 10)
            e = 10 - f
            return f"{icon} [{'█'*f}{'░'*e}] {cur}/{mx}"
        
        text = f"""
<b>⚔ ДУЭЛЬ #{self.battle_id}</b>
━━━━━━━━━━━━━━━━━━━━
Раунд: <b>{self.round}</b> | Ставка: <b>{self.bet}💰</b>

<b>{self.get_player_name(1)}</b>
{bar(self.p1_hp, self.p1_max_hp, '❤')}
{bar(self.p1_mp, self.p1_max_mp, '💎')}

<b>{self.get_player_name(2)}</b>
{bar(self.p2_hp, self.p2_max_hp, '❤')}
{bar(self.p2_mp, self.p2_max_mp, '💎')}
━━━━━━━━━━━━━━━━━━━━
"""
        
        if phase == "defend":
            text += "\n🛡 <b>Выберите часть тела для защиты:</b>"
        elif phase == "attack":
            text += "\n🎯 <b>Выберите цель и навык атаки:</b>"
        elif phase == "waiting":
            text += "\n⏳ <b>Ожидание действий противника...</b>"
        
        # Последние 3 события
        if log:
            text += "\n\n<i>" + "\n".join(log[-3:]) + "</i>"
        
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

# ==================== ОБРАБОТЧИКИ МЕНЮ ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if str(user_id) in banned_users:
        bot.send_message(message.chat.id, "⛔ Вы забанены!")
        return
    
    username = message.from_user.username
    first_name = message.from_user.first_name or "Игрок"
    Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v11.0 ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

🎯 <b>НОВАЯ СИСТЕМА БОЯ:</b>
• Сначала ВСЕ защищаются
• Потом ВСЕ атакуют
• Броня УМЕНЬШАЕТ урон
• 3 вида атак: базовая, средняя, мощная
• Мощные атаки дольше перезаряжаются
• AFK-защита: 2 минуты ожидания

💰 Старт: <b>500 монет</b>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль", callback_data="quick_duel"),
        types.InlineKeyboardButton("👥 Найти соперника", callback_data="find_opponent"),
        types.InlineKeyboardButton("🏆 Рейтинговая", callback_data="ranked_duel"),
        types.InlineKeyboardButton("💀 Хардкор", callback_data="hardcore_duel"),
        types.InlineKeyboardButton("🎯 Спарринг", callback_data="sparring_duel"),
        types.InlineKeyboardButton("🏟 Турнир", callback_data="tournament_duel")
    )
    
    text = """
<b>⚔️ ДУЭЛИ</b>

<b>Новая система:</b>
🛡 Все игроки выбирают защиту
⚔ Все игроки выбирают атаку
🔄 Броня уменьшает урон
⏰ AFK = поражение
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
        types.InlineKeyboardButton("🌍 Ивенты", callback_data="world_events"),
        types.InlineKeyboardButton("📊 Топ", callback_data="world_top"),
        types.InlineKeyboardButton("ℹ Помощь", callback_data="world_help")
    )
    bot.send_message(message.chat.id, "<b>🌍 МИР</b>", reply_markup=markup)

# ==================== ДУЭЛИ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["quick_duel", "find_opponent", "ranked_duel", "hardcore_duel", "sparring_duel", "tournament_duel"])
def duel_type_handler(call):
    dt = call.data
    
    if dt == "quick_duel":
        show_quick_duel_menu(call)
    elif dt == "find_opponent":
        start_matchmaking(call, "quick", 50)
    elif dt == "ranked_duel":
        start_matchmaking(call, "ranked", 100)
    elif dt == "hardcore_duel":
        start_matchmaking(call, "hardcore", 500)
    elif dt == "sparring_duel":
        start_matchmaking(call, "sparring", 0)
    elif dt == "tournament_duel":
        show_tournament_menu(call)

def show_quick_duel_menu(call):
    player = Player(call.from_user.id)
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    for bet in [50, 100, 200, 500, 1000]:
        markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"qduel_{bet}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
    
    bot.edit_message_text(
        f"<b>⚡ БЫСТРАЯ ДУЭЛЬ (БОТ)</b>\n\n💰 Баланс: <b>{player.data['money']}💰</b>",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_duels")
def back_to_duels(call):
    duel_section(call.message)

def start_matchmaking(call, duel_type, bet):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    queue = matchmaking_queue.get(duel_type, [])
    queue = [q for q in queue if q["user_id"] != user_id]
    
    if queue:
        # Нашли соперника
        opponent = queue.pop(0)
        matchmaking_queue[duel_type] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        start_duel_between_players(call.message, user_id, opponent["user_id"], duel_type, bet)
    else:
        # Встаём в очередь
        queue.append({"user_id": user_id, "chat_id": call.message.chat.id, "message_id": call.message.message_id, "bet": bet})
        matchmaking_queue[duel_type] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        bot.edit_message_text("🔍 Поиск соперника... Через 5 сек — бот.", call.message.chat.id, call.message.message_id)
        
        # Таймер на бота
        threading.Timer(5.0, create_bot_duel, args=[call.message.chat.id, call.message.message_id, user_id, duel_type, bet]).start()

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def quick_duel_start(call):
    user_id = str(call.from_user.id)
    bet = int(call.data.split("_")[1])
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    create_bot_duel(call.message.chat.id, call.message.message_id, user_id, "quick", bet)

def create_bot_duel(chat_id, message_id, user_id, duel_type, bet):
    """Создать дуэль с ботом"""
    if str(user_id) in active_duels:
        return  # Уже в дуэли
    
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.edit_message_text(f"❌ Недостаточно монет!", chat_id, message_id)
        return
    
    # Создание бота
    bot_level = random.randint(max(1, player.data["level"] - 3), player.data["level"] + 3)
    bot_id = f"bot_{random.randint(100000, 999999)}"
    
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    for slot, itype in [("head", "helmet"), ("body", "armor"), ("legs", "boots")]:
        sitems = [k for k, v in items.items() if v.get("type") == itype and v.get("level_req", 1) <= bot_level]
        if sitems:
            equip[slot] = random.choice(sitems)
    wpns = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= bot_level]
    if wpns:
        equip["weapon"] = random.choice(wpns)
    
    users[bot_id] = {
        "username": f"Bot_{bot_level}", "first_name": f"🤖 Бот Lv.{bot_level}",
        "money": 0, "level": bot_level, "exp": 0, "hp": 120, "max_hp": 120,
        "mana": 60, "max_mana": 60,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000, "inventory": [], "equipment": equip,
        "enchantments": {}, "last_daily": None, "last_dungeon": None,
        "title": "Бот", "titles_collected": ["Бот"], "achievements": [],
        "clan": None, "clan_role": None, "registration_date": datetime.now().isoformat(),
        "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    if bet > 0:
        player.data["money"] -= bet
        player.save()
    
    duel = DuelInstance(user_id, bot_id, duel_type, bet)
    active_duels[str(user_id)] = duel
    active_duels[bot_id] = duel
    
    # Бот выбирает защиту
    bot_def = random.choice(list(BODY_PARTS.keys()))
    duel.set_defend(2, bot_def)
    
    # Бот выбирает атаку
    bot_skills = duel.get_available_skills(2)
    if bot_skills:
        bot_skill = random.choice(bot_skills)
        bot_target = random.choice(list(BODY_PARTS.keys()))
        duel.set_attack(2, bot_target, bot_skill)
    
    bot.edit_message_text("⚔ Бой с ботом начинается!", chat_id, message_id)
    show_duel_interface(chat_id, message_id, duel, user_id)

def start_duel_between_players(message, p1_id, p2_id, duel_type, bet):
    """Начать дуэль между двумя игроками"""
    if p1_id in active_duels or p2_id in active_duels:
        bot.edit_message_text("❌ Один из игроков уже в дуэли!", message.chat.id, message.message_id)
        return
    
    p1 = Player(p1_id)
    p2 = Player(p2_id)
    
    if bet > 0:
        if p1.data["money"] < bet or p2.data["money"] < bet:
            bot.edit_message_text("❌ Недостаточно монет у одного из игроков!", message.chat.id, message.message_id)
            return
        p1.data["money"] -= bet
        p2.data["money"] -= bet
        p1.save()
        p2.save()
    
    duel = DuelInstance(p1_id, p2_id, duel_type, bet)
    active_duels[p1_id] = duel
    active_duels[p2_id] = duel
    
    # Отправляем интерфейс обоим
    bot.edit_message_text("⚔ Соперник найден! Дуэль начинается!", message.chat.id, message.message_id)
    
    # Отправляем интерфейс первому игроку
    show_duel_interface(message.chat.id, message.message_id, duel, p1_id)
    
    # Отправляем интерфейс второму игроку
    try:
        msg2 = bot.send_message(int(p2_id), "⚔ Дуэль начинается!")
        show_duel_interface(int(p2_id), msg2.message_id, duel, p2_id)
    except:
        pass

def show_duel_interface(chat_id, message_id, duel, user_id):
    """Показать интерфейс дуэли"""
    if not duel.active:
        # Проверка AFK
        if duel.check_afk():
            finish_duel(chat_id, message_id, duel)
            return
        finish_duel(chat_id, message_id, duel)
        return
    
    state_text = duel.get_state_text(user_id)
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    phase = duel.p1_phase if pn == 1 else duel.p2_phase
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if phase == "defend":
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']}",
                callback_data=f"duel_defend_{part}"
            ))
    
    elif phase == "attack":
        # Сначала цель, потом навык
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🎯 {data['name']}",
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
    except Exception as e:
        print(f"Edit error: {e}")

# Временное хранилище целей
temp_targets = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_target_"))
def duel_target_selected(call):
    user_id = str(call.from_user.id)
    part = call.data.split("_", 2)[2]
    
    duel = active_duels.get(user_id)
    if not duel or not duel.active:
        return
    
    temp_targets[user_id] = part
    
    # Показываем навыки
    pn = 1 if user_id == duel.p1_id else 2
    skills = duel.get_available_skills(pn)
    
    text = duel.get_state_text(user_id) + f"\n🎯 Цель: <b>{BODY_PARTS[part]['name']}</b>\n<b>Выберите навык:</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for sid in skills[:10]:
        skill = SKILLS_DB.get(sid, {})
        name = skill.get("name", sid)
        mana = skill.get("mana_cost", 0)
        cd = skill.get("cooldown", 0)
        cd_text = f" 🔄{cd}х" if cd > 0 else ""
        
        markup.add(types.InlineKeyboardButton(
            f"{name} [{mana}MP]{cd_text}",
            callback_data=f"duel_skill_{sid}"
        ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="duel_back_target"))
    
    try:
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "duel_back_target")
def duel_back_target(call):
    duel = active_duels.get(str(call.from_user.id))
    if duel:
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, call.from_user.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_skill_"))
def duel_skill_selected(call):
    user_id = str(call.from_user.id)
    skill_id = call.data.split("_", 2)[2]
    
    duel = active_duels.get(user_id)
    if not duel or not duel.active:
        return
    
    target = temp_targets.get(user_id, "body")
    pn = 1 if user_id == duel.p1_id else 2
    
    duel.set_attack(pn, target, skill_id)
    
    bot.answer_callback_query(call.id, "⚔ Атака выбрана!")
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_"))
def duel_action_handler(call):
    user_id = str(call.from_user.id)
    action = call.data.split("_", 1)[1]
    
    if action == "refresh":
        duel = active_duels.get(user_id)
        if duel and duel.active:
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        else:
            bot.edit_message_text("❌ Дуэль завершена", call.message.chat.id, call.message.message_id)
        return
    
    if action == "wait":
        duel = active_duels.get(user_id)
        if duel and duel.active:
            # Проверяем бота
            pn = 1 if user_id == duel.p1_id else 2
            other_pn = 3 - pn
            other_id = duel.p2_id if pn == 1 else duel.p1_id
            
            if other_id.startswith("bot_"):
                other_phase = duel.p2_phase if pn == 1 else duel.p1_phase
                if other_phase == "defend":
                    duel.set_defend(other_pn, random.choice(list(BODY_PARTS.keys())))
                if other_phase == "attack":
                    skills = duel.get_available_skills(other_pn)
                    if skills:
                        duel.set_attack(other_pn, random.choice(list(BODY_PARTS.keys())), random.choice(skills))
            
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        return
    
    if action == "surrender":
        duel = active_duels.get(user_id)
        if duel and duel.active:
            duel.active = False
            duel.winner = 2 if user_id == duel.p1_id else 1
            finish_duel(call.message.chat.id, call.message.message_id, duel)
        return
    
    if action.startswith("defend_"):
        part = action.split("_")[1]
        duel = active_duels.get(user_id)
        if duel and duel.active:
            pn = 1 if user_id == duel.p1_id else 2
            duel.set_defend(pn, part)
            bot.answer_callback_query(call.id, f"🛡 Защита: {BODY_PARTS[part]['name']}")
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

def finish_duel(chat_id, message_id, duel):
    """Завершение дуэли и рассылка результатов"""
    # Очистка активных дуэлей
    for uid in [duel.p1_id, duel.p2_id]:
        if uid in active_duels and active_duels[uid].battle_id == duel.battle_id:
            del active_duels[uid]
    
    # Удаление ботов
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") and uid in users:
            del users[uid]
    save_json(DATA_FILES['users'], users)
    
    if duel.winner == 0:
        result = "<b>🤝 НИЧЬЯ!</b>\nРаундов: " + str(duel.round)
        send_result_to_players(duel, result)
        try:
            bot.edit_message_text(result, chat_id, message_id)
        except:
            pass
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
        if winner.data["win_streak"] > winner.data["best_streak"]:
            winner.data["best_streak"] = winner.data["win_streak"]
        exp_w = duel.round * 10 + duel.bet // 2
        winner.data["exp"] += exp_w
        check_level_up(winner)
        
        # История
        winner.data.setdefault("battle_history", []).append({
            "date": datetime.now().isoformat(),
            "opponent": loser.data["first_name"],
            "result": "win", "type": duel.duel_type,
            "rounds": duel.round
        })
        winner.save()
    
    if not loser_id.startswith("bot_"):
        loser.data["losses"] += 1
        loser.data["win_streak"] = 0
        loser.data["total_duels"] += 1
        exp_l = duel.round * 5 + duel.bet // 5
        loser.data["exp"] += exp_l
        check_level_up(loser)
        
        loser.data.setdefault("battle_history", []).append({
            "date": datetime.now().isoformat(),
            "opponent": winner.data["first_name"],
            "result": "loss", "type": duel.duel_type,
            "rounds": duel.round
        })
        loser.save()
    
    winner_name = duel.get_player_name(duel.winner)
    loser_name = duel.get_player_name(3 - duel.winner)
    
    result = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

👑 <b>{winner_name}</b> побеждает!
💀 <b>{loser_name}</b> проигрывает

💰 Ставка: <b>{duel.bet}💰</b>
📊 Раундов: <b>{duel.round}</b>
"""
    
    send_result_to_players(duel, result)
    
    try:
        bot.edit_message_text(result, chat_id, message_id)
    except:
        pass

def send_result_to_players(duel, result_text):
    """Отправить результат обоим игрокам"""
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_"):
            continue
        try:
            bot.send_message(int(uid), result_text)
        except:
            pass

# ==================== ПОДЗЕМЕЛЬЯ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_dungeons")
def world_dungeons(call):
    text = """
<b>🏰 ПОДЗЕМЕЛЬЯ</b>

🐺 Логово волка (3 босса)
🕷 Паучьи пещеры (3 босса)
💀 Катакомбы (3 босса)
🐉 Драконье логово (3 босса)
👹 Бездна (финальный босс 1 000 000 HP)

Кулдаун: 2 часа
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, name in enumerate(["🐺 Логово волка", "🕷 Паучьи пещеры", "💀 Катакомбы", "🐉 Драконье логово", "👹 Бездна (1M HP)"], 1):
        markup.add(types.InlineKeyboardButton(name, callback_data=f"dung_{i}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dung_"))
def start_dungeon(call):
    dl = int(call.data.split("_")[1])
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    level_reqs = [1, 5, 10, 15, 25]
    if player.data["level"] < level_reqs[dl - 1]:
        bot.answer_callback_query(call.id, f"❌ Нужен {level_reqs[dl-1]} ур.!")
        return
    
    if player.data.get("last_dungeon"):
        last = datetime.fromisoformat(player.data["last_dungeon"])
        if (datetime.now() - last) < timedelta(hours=2):
            r = timedelta(hours=2) - (datetime.now() - last)
            bot.answer_callback_query(call.id, f"⏰ {r.seconds//60} мин.")
            return
    
    if dl == 5:
        # Финальный босс с 1M HP
        start_raid_boss(call)
        return
    
    # Обычный данж с 3 боссами
    bosses = [
        [("🐺 Волк-страж", 15), ("🐺 Волк-воин", 20), ("🐺 Вожак стаи", 30)],
        [("🕷 Паук-охотник", 25), ("🕷 Паук-ткач", 35), ("🕷 Королева пауков", 50)],
        [("💀 Скелет-воин", 40), ("💀 Скелет-маг", 55), ("💀 Некромант", 75)],
        [("🐉 Молодой дракон", 60), ("🐉 Дракон-страж", 80), ("🐉 Древний дракон", 120)]
    ]
    
    dungeon_info = {
        "user_id": user_id,
        "level": dl,
        "bosses": bosses[dl - 1],
        "current_boss": 0,
        "boss_hp": bosses[dl - 1][0][1],
        "reward_per_boss": 100 * dl,
        "total_reward": 0,
        "completed": False
    }
    
    dungeons_data[user_id] = dungeon_info
    save_json(DATA_FILES['dungeons'], dungeons_data)
    
    text = f"⚔ <b>Данж начался!</b>\nБосс 1/3: <b>{bosses[dl-1][0][0]}</b> ({bosses[dl-1][0][1]} HP)"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⚔ Атаковать босса", callback_data="dung_attack"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "dung_attack")
def dungeon_attack(call):
    user_id = str(call.from_user.id)
    
    if user_id not in dungeons_data:
        bot.answer_callback_query(call.id, "❌ Данж не найден!")
        return
    
    dungeon = dungeons_data[user_id]
    
    # Простая атака
    player = Player(user_id)
    min_d, max_d = player.get_weapon_damage()
    dmg = random.randint(min_d, max_d)
    
    # Крит
    if random.random() < 0.1:
        dmg = int(dmg * 1.5)
    
    dungeon["boss_hp"] -= dmg
    
    if dungeon["boss_hp"] <= 0:
        # Босс побеждён
        dungeon["current_boss"] += 1
        dungeon["total_reward"] += dungeon["reward_per_boss"]
        
        if dungeon["current_boss"] >= 3:
            # Данж пройден
            player.data["money"] += dungeon["total_reward"]
            player.data["exp"] += 100 * dungeon["level"]
            player.data["total_exp"] += 100 * dungeon["level"]
            player.data["dungeons_completed"] = player.data.get("dungeons_completed", 0) + 1
            player.data["last_dungeon"] = datetime.now().isoformat()
            check_level_up(player)
            player.save()
            
            del dungeons_data[user_id]
            save_json(DATA_FILES['dungeons'], dungeons_data)
            
            bot.edit_message_text(
                f"🎉 <b>ДАНЖ ПРОЙДЕН!</b>\n💰 +{dungeon['total_reward']} | ✨ +{100 * dungeon['level']}",
                call.message.chat.id, call.message.message_id
            )
        else:
            # Следующий босс
            bosses = dungeon["bosses"]
            dungeon["boss_hp"] = bosses[dungeon["current_boss"]][1]
            save_json(DATA_FILES['dungeons'], dungeons_data)
            
            text = f"💀 Босс побеждён!\n⚔ Босс {dungeon['current_boss']+1}/3: <b>{bosses[dungeon['current_boss']][0]}</b> ({dungeon['boss_hp']} HP)"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚔ Атаковать", callback_data="dung_attack"))
            
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    else:
        # Продолжаем бить
        save_json(DATA_FILES['dungeons'], dungeons_data)
        
        text = f"⚔ Урон: <b>{dmg}</b>\n❤ HP босса: <b>{dungeon['boss_hp']}</b>"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚔ Атаковать", callback_data="dung_attack"))
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

def start_raid_boss(call):
    """Финальный босс с 1 000 000 HP"""
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    dungeon_info = {
        "user_id": user_id,
        "level": 5,
        "bosses": [("👹 Владыка бездны", 1000000)],
        "current_boss": 0,
        "boss_hp": 1000000,
        "reward_per_boss": 10000,
        "total_reward": 0,
        "completed": False
    }
    
    dungeons_data[user_id] = dungeon_info
    save_json(DATA_FILES['dungeons'], dungeons_data)
    
    text = f"⚔ <b>РЕЙД-БОСС!</b>\n👹 <b>Владыка бездны</b>\n❤ HP: <b>1 000 000</b>\n💰 Награда: 10 000"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⚔ Атаковать (500 урона)", callback_data="dung_attack"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== ТУРНИРЫ ====================
def show_tournament_menu(call):
    if not tournaments.get("active"):
        tournaments["active"] = {
            "name": "Еженедельный турнир",
            "participants": [],
            "rounds": [],
            "status": "registration",
            "prize_pool": 10000,
            "entry_fee": 1000
        }
        save_json(DATA_FILES['tournaments'], tournaments)
    
    tour = tournaments["active"]
    
    text = f"""
<b>🏟 ТУРНИР</b>

<b>{tour['name']}</b>
👥 Участников: {len(tour.get('participants', []))}/16
💰 Приз: <b>{tour.get('prize_pool', 0)}💰</b>
💵 Взнос: {tour.get('entry_fee', 1000)}💰
📊 Статус: {tour.get('status', 'registration')}
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🏆 Участвовать", callback_data="tour_register"),
        types.InlineKeyboardButton("📋 Участники", callback_data="tour_list"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world")
    )
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "tour_register")
def tournament_register(call):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    tour = tournaments.get("active", {})
    
    if player.data["money"] < tour.get("entry_fee", 1000):
        bot.answer_callback_query(call.id, f"❌ Нужно {tour.get('entry_fee', 1000)}💰!")
        return
    
    participants = tour.get("participants", [])
    if user_id in participants:
        bot.answer_callback_query(call.id, "❌ Уже участвуете!")
        return
    if len(participants) >= 16:
        bot.answer_callback_query(call.id, "❌ Заполнен!")
        return
    
    player.data["money"] -= tour.get("entry_fee", 1000)
    player.save()
    
    participants.append(user_id)
    tour["participants"] = participants
    tour["prize_pool"] = tour.get("prize_pool", 0) + tour.get("entry_fee", 1000)
    tournaments["active"] = tour
    save_json(DATA_FILES['tournaments'], tournaments)
    
    bot.answer_callback_query(call.id, "✅ Зарегистрированы!")
    show_tournament_menu(call)

@bot.callback_query_handler(func=lambda call: call.data == "tour_list")
def tournament_list(call):
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
    current = events.get("current", {})
    
    if not current or datetime.fromisoformat(current.get("expires", "2000-01-01")) < datetime.now():
        new_event = {
            "name": random.choice(["🌋 Извержение", "❄ Буран", "⚡ Гроза", "🌑 Затмение", "✨ Звездопад"]),
            "description": "Участвуйте в дуэлях для получения наград!",
            "reward_money": random.randint(500, 2000),
            "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        events["current"] = new_event
        save_json(DATA_FILES['events'], events)
        
        # Рассылка всем игрокам
        broadcast_event(new_event)
    
    ev = events["current"]
    time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
    minutes_left = max(0, time_left.seconds // 60)
    
    text = f"""
<b>🌍 ИВЕНТ</b>

<b>{ev['name']}</b>
📝 {ev.get('description', '')}
💰 Награда: <b>{ev.get('reward_money', 0)}💰</b>
⏰ Осталось: {minutes_left} мин.
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

def broadcast_event(event):
    """Рассылка ивента всем игрокам"""
    text = f"🌍 <b>НОВЫЙ ИВЕНТ!</b>\n\n<b>{event['name']}</b>\n{event.get('description', '')}\n💰 Награда: <b>{event.get('reward_money', 0)}💰</b>"
    for uid in users:
        if uid.startswith("bot_"):
            continue
        try:
            bot.send_message(int(uid), text)
        except:
            pass

# ==================== ТОП ====================
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
        else:
            val = f"{data.get('money', 0)}💰"
        
        text += f"{medals[i]} {data.get('first_name', 'Игрок')}: {val}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_top"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

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
⭐ Ур.{d['level']}
💰 {d['money']}💰
🏆 Побед: {d['wins']} | 💀 Поражений: {d['losses']}
📈 Винрейт: {wr:.1f}%
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
                    eq = " [🟢]"
            
            text += f"{idx}. {r} {item['name']} x{cnt}{eq}\n"
            
            if item.get("type") in ["weapon", "helmet", "armor", "boots"]:
                markup.add(types.InlineKeyboardButton(f"Экипировать: {item['name']}", callback_data=f"equip_{ik}"))
                markup.add(types.InlineKeyboardButton(f"Зачаровать: {item['name']}", callback_data=f"enchant_{ik}"))
            elif item.get("type") == "potion":
                markup.add(types.InlineKeyboardButton(f"Использовать: {item['name']}", callback_data=f"use_{ik}"))
            
            idx += 1
        
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_achievements":
        ach_list = [
            ("first_blood", "🩸 Первая кровь", "1 победа", player.data["wins"] >= 1),
            ("warrior", "⚔ Воин", "10 побед", player.data["wins"] >= 10),
            ("veteran", "🎖 Ветеран", "50 побед", player.data["wins"] >= 50),
            ("legend", "👑 Легенда", "100 побед", player.data["wins"] >= 100),
            ("rich", "💰 Богач", "10000 монет", player.data["money"] >= 10000),
            ("dmaster", "🏰 Мастер данжей", "10 данжей", player.data.get("dungeons_completed", 0) >= 10)
        ]
        
        text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(player.data['achievements'])}/6)\n\n"
        
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
                    text += f"{sn}: <b>{item['name']}</b> (DEF:{item.get('defense', 0)})\n"
                else:
                    text += f"{sn}: ❌\n"
            else:
                text += f"{sn}: ❌\n"
        
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
            bot.edit_message_text("💊 Полное HP!", call.message.chat.id, call.message.message_id)
            return
        
        pk = potions[0]
        potion = items[pk]
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + potion["heal"])
        player.data["inventory"].remove(pk)
        player.save()
        
        bot.edit_message_text(f"💊 {potion['name']}\n❤ HP: {player.data['hp']}/{player.data['max_hp']}", call.message.chat.id, call.message.message_id)
    
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
        bot.answer_callback_query(call.id, "❌ Нельзя!")
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
        bot.answer_callback_query(call.id, f"❌ {cost}💰!")
        return
    
    player.data["money"] -= cost
    ench = random.choice(ENCHANT_EFFECTS)
    player.data.setdefault("enchantments", {})[ik] = {"name": ench["name"], "effect": ench["effect"], "value": ench["value"]}
    player.save()
    
    bot.answer_callback_query(call.id, f"✨ {ench['name']}!")
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
    bot.answer_callback_query(call.id, "✅ Снято!")
    hero_handlers(call)

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
            if "hp_bonus" in item:
                s += f" | HP: +{item['hp_bonus']}"
        else:
            s = f"Лечение: {item.get('heal', 0)}"
        
        text += f"{r} <b>{item['name']}</b> — {s}\n💰 {item['price']} | Ур.{item.get('level_req', 1)}\n\n"
        
        if player.data["money"] >= item["price"]:
            markup.add(types.InlineKeyboardButton(f"Купить - {item['price']}💰", callback_data=f"buyitem_{ik}"))
    
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
                text += f"<b>{item['name']}</b>\n💰 <b>{item['price']}💰</b>\n\n"
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
        text = "<b>🛡 КЛАНЫ</b>\n/createclan [имя] — 5000💰\n/joinclan [имя]"
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
        types.InlineKeyboardButton("⛔ Бан", callback_data="admin_ban"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("✅ Разбан", callback_data="admin_unban"),
        types.InlineKeyboardButton("🏟 Создать турнир", callback_data="admin_tournament"),
        types.InlineKeyboardButton("🌍 Создать ивент", callback_data="admin_event")
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
        bot.send_message(call.message.chat.id, "💰 /givemoney @username сумма")
    elif call.data == "admin_giveitem":
        bot.send_message(call.message.chat.id, "🎁 /giveitem @username item_key")
    elif call.data == "admin_ban":
        bot.send_message(call.message.chat.id, "⛔ /ban @username причина")
    elif call.data == "admin_unban":
        bot.send_message(call.message.chat.id, "✅ /unban @username")
    elif call.data == "admin_broadcast":
        bot.send_message(call.message.chat.id, "📢 /broadcast текст")
    elif call.data == "admin_tournament":
        bot.send_message(call.message.chat.id, "🏟 /createtournament название приз взнос")
    elif call.data == "admin_event":
        bot.send_message(call.message.chat.id, "🌍 /createevent название награда")

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'broadcast', 'createtournament', 'createevent'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd in ['givemoney', 'giveitem', 'ban', 'unban']:
            username = parts[1].replace('@', '')
            
            for uid, data in users.items():
                if data.get("username", "").lower() == username.lower():
                    if cmd == "givemoney":
                        amt = int(parts[2])
                        p = Player(uid)
                        p.data["money"] += amt
                        p.save()
                        bot.send_message(message.chat.id, f"✅ {amt}💰 → @{username}")
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
                    return
            
            bot.send_message(message.chat.id, f"❌ @{username} не найден!")
        
        elif cmd == "broadcast":
            text = message.text.replace('/broadcast', '', 1).strip()
            if text:
                s, f = 0, 0
                for uid in users:
                    if uid.startswith("bot_"):
                        continue
                    try:
                        bot.send_message(int(uid), f"📢 {text}")
                        s += 1
                    except:
                        f += 1
                bot.send_message(message.chat.id, f"✅ {s} | ❌ {f}")
        
        elif cmd == "createtournament":
            name = parts[1]
            prize = int(parts[2]) if len(parts) > 2 else 10000
            fee = int(parts[3]) if len(parts) > 3 else 1000
            
            tournaments["active"] = {
                "name": name, "participants": [], "rounds": [],
                "status": "registration", "prize_pool": prize, "entry_fee": fee
            }
            save_json(DATA_FILES['tournaments'], tournaments)
            
            # Рассылка
            for uid in users:
                if uid.startswith("bot_"):
                    continue
                try:
                    bot.send_message(int(uid), f"🏟 <b>НОВЫЙ ТУРНИР!</b>\n\n<b>{name}</b>\n💰 Приз: <b>{prize}💰</b>\n💵 Взнос: {fee}💰")
                except:
                    pass
            
            bot.send_message(message.chat.id, f"✅ Турнир <b>{name}</b> создан!")
        
        elif cmd == "createevent":
            name = " ".join(parts[1:]) if len(parts) > 1 else "Событие"
            reward = random.randint(500, 2000)
            
            events["current"] = {
                "name": name, "reward_money": reward,
                "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
            }
            save_json(DATA_FILES['events'], events)
            
            # Рассылка
            for uid in users:
                if uid.startswith("bot_"):
                    continue
                try:
                    bot.send_message(int(uid), f"🌍 <b>НОВЫЙ ИВЕНТ!</b>\n\n<b>{name}</b>\n💰 Награда: <b>{reward}💰</b>")
                except:
                    pass
            
            bot.send_message(message.chat.id, f"✅ Ивент <b>{name}</b> создан!")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================
def check_level_up(player):
    level = player.data["level"]
    exp_needed = int(100 * (1.5 ** (level - 1)))
    
    while player.data["exp"] >= exp_needed:
        player.data["exp"] -= exp_needed
        player.data["level"] += 1
        player.data["max_hp"] += 10
        player.data["max_mana"] += 5
        player.data["hp"] = player.data["max_hp"]
        player.data["mana"] = player.data["max_mana"]
        
        titles = {5: "Боец", 10: "Воитель", 20: "Рыцарь", 30: "Ветеран", 50: "Мастер", 75: "Легенда", 100: "Божество"}
        for req, title in titles.items():
            if player.data["level"] >= req and title not in player.data["titles_collected"]:
                player.data["titles_collected"].append(title)
                player.data["title"] = title
        
        level = player.data["level"]
        exp_needed = int(100 * (1.5 ** (level - 1)))

@bot.message_handler(commands=['sell'])
def sell_cmd(message):
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
    
    ik = player.data["inventory"].pop(idx)
    player.save()
    
    lid = f"{user_id}_{int(time.time())}"
    market_listings[lid] = {
        "seller_id": user_id, "seller_name": message.from_user.first_name,
        "item_key": ik, "price": price, "created_at": datetime.now().isoformat()
    }
    save_json(DATA_FILES['market'], market_listings)
    
    item = items.get(ik) or limited_items.get(ik)
    bot.send_message(message.chat.id, f"✅ {item.get('name', ik)} за {price}💰!")

@bot.callback_query_handler(func=lambda call: call.data in ["world_help", "back_to_world"])
def world_helpers(call):
    if call.data == "world_help":
        text = "<b>ℹ ПОМОЩЬ</b>\n⚔ Дуэли: защита → атака\n🛒 /shop\n💰 /sell"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data == "back_to_world":
        world_section(call.message)

# ==================== ЗАПУСК ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v11.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ: {ADMIN_ID}")
    print("=" * 60)
    print("✅ Защита → все выбирают → атака")
    print("✅ Броня УМЕНЬШАЕТ урон")
    print("✅ Навыки с кулдаунами")
    print("✅ AFK = поражение")
    print("✅ Данжи с 3 боссами + рейд-босс 1M HP")
    print("✅ Турниры с турнирной сеткой")
    print("✅ Ивенты с рассылкой")
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
