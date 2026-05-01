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
TOKEN = '8670879387:AAH70T6P0ZEn-rvPhQo7rhrNMl9wUKDkILI'
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
    {"name": "❤ Живучее", "effect": "hp_bonus", "value": 60}
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
    'matchmaking': 'matchmaking.json',
    'bosses': 'bosses.json'
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
    "leather_cap": {"name": "🎓 Кожаная шапка", "defense": 3, "price": 60, "type": "helmet", "slot": "head", "rarity": "common", "level_req": 1, "enchantable": True},
    "iron_helmet": {"name": "⛑ Железный шлем", "defense": 8, "price": 250, "type": "helmet", "slot": "head", "rarity": "uncommon", "level_req": 6, "enchantable": True},
    "dragon_helmet": {"name": "🐉 Шлем дракона", "defense": 18, "price": 2000, "type": "helmet", "slot": "head", "rarity": "epic", "level_req": 20, "enchantable": True, "element": "fire"},
    "crown_of_wisdom": {"name": "👑 Корона мудрости", "defense": 12, "price": 3500, "type": "helmet", "slot": "head", "rarity": "legendary", "level_req": 28, "enchantable": True}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "defense": 5, "price": 80, "type": "armor", "slot": "body", "rarity": "common", "level_req": 1, "enchantable": True},
    "chainmail": {"name": "⛓ Кольчуга", "defense": 12, "price": 400, "type": "armor", "slot": "body", "rarity": "uncommon", "level_req": 8, "enchantable": True},
    "plate_armor": {"name": "🛡 Латный доспех", "defense": 22, "price": 1500, "type": "armor", "slot": "body", "rarity": "rare", "level_req": 15, "enchantable": True},
    "shadow_armor": {"name": "🌑 Теневая броня", "defense": 28, "price": 3500, "type": "armor", "slot": "body", "rarity": "epic", "level_req": 22, "enchantable": True},
    "phoenix_armor": {"name": "🦅 Броня феникса", "defense": 40, "price": 8000, "type": "armor", "slot": "body", "rarity": "legendary", "level_req": 30, "enchantable": True}
}

BOOTS = {
    "leather_boots": {"name": "👢 Кожаные сапоги", "defense": 2, "speed": 8, "price": 100, "type": "boots", "slot": "legs", "rarity": "common", "level_req": 1, "enchantable": True},
    "wind_boots": {"name": "🌪 Сапоги ветра", "defense": 4, "speed": 18, "price": 900, "type": "boots", "slot": "legs", "rarity": "rare", "level_req": 12, "enchantable": True},
    "blink_boots": {"name": "✨ Сапоги телепортации", "defense": 8, "speed": 28, "price": 4000, "type": "boots", "slot": "legs", "rarity": "epic", "level_req": 25, "enchantable": True},
    "hermes_boots": {"name": "👟 Сандалии Гермеса", "defense": 12, "speed": 45, "price": 12000, "type": "boots", "slot": "legs", "rarity": "legendary", "level_req": 35, "enchantable": True}
}

WEAPONS = {
    "rusty_sword": {"name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 1, "skills": ["quick_strike", "slash"], "enchantable": True},
    "flame_blade": {"name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 7, "skills": ["fire_slash", "inferno_strike", "flame_wave"], "enchantable": True, "element": "fire"},
    "frost_axe": {"name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 10, "skills": ["frost_strike", "ice_shatter", "blizzard"], "enchantable": True, "element": "ice"},
    "storm_staff": {"name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500, "type": "weapon", "slot": "weapon", "rarity": "rare", "level_req": 14, "skills": ["lightning_bolt", "thunder_storm", "chain_lightning"], "enchantable": True, "element": "lightning"},
    "shadow_dagger": {"name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "slot": "weapon", "rarity": "epic", "level_req": 22, "skills": ["shadow_strike", "assassinate", "soul_drain"], "enchantable": True, "element": "dark"},
    "divine_spear": {"name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "slot": "weapon", "rarity": "legendary", "level_req": 28, "skills": ["holy_strike", "divine_judgment", "heavenly_light"], "enchantable": True, "element": "light"},
    "death_scythe": {"name": "💀 Коса смерти", "damage": (40, 65), "price": 12000, "type": "weapon", "slot": "weapon", "rarity": "mythic", "level_req": 35, "skills": ["reap", "death_sentence", "soul_harvest"], "enchantable": True, "element": "dark"}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 200, "price": 350, "type": "potion", "rarity": "rare", "level_req": 15}
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
    "quick_strike": {"name": "⚡ Быстрый удар", "damage_mult": 0.8, "mana_cost": 5, "cooldown": 0, "hits": 2},
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 8, "cooldown": 0},
    "heavy_strike": {"name": "💪 Тяжёлый удар", "damage_mult": 1.8, "mana_cost": 18, "cooldown": 1},
    "defend": {"name": "🛡 Укрепление", "defense_boost": 30, "mana_cost": 10, "cooldown": 2},
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.5, "mana_cost": 18, "element": "fire", "burn_chance": 30, "cooldown": 1},
    "inferno_strike": {"name": "🌋 Инферно удар", "damage_mult": 2.5, "mana_cost": 40, "element": "fire", "burn_chance": 60, "cooldown": 3},
    "flame_wave": {"name": "🔥 Волна пламени", "damage_mult": 3.0, "mana_cost": 50, "element": "fire", "aoe": True, "cooldown": 4},
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.4, "mana_cost": 16, "element": "ice", "freeze_chance": 25, "cooldown": 0},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.2, "mana_cost": 35, "element": "ice", "freeze_chance": 50, "cooldown": 2},
    "blizzard": {"name": "🌨 Метель", "damage_mult": 2.8, "mana_cost": 45, "element": "ice", "aoe": True, "cooldown": 3},
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.6, "mana_cost": 20, "element": "lightning", "stun_chance": 20, "cooldown": 0},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.5, "mana_cost": 42, "element": "lightning", "stun_chance": 35, "aoe": True, "cooldown": 3},
    "chain_lightning": {"name": "⚡ Цепная молния", "damage_mult": 2.0, "mana_cost": 30, "element": "lightning", "chain_hits": 3, "cooldown": 2},
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.6, "mana_cost": 22, "element": "dark", "poison_chance": 25, "cooldown": 0},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.5, "mana_cost": 60, "element": "dark", "ignore_defense": 50, "cooldown": 4},
    "soul_drain": {"name": "💀 Похищение души", "damage_mult": 2.2, "mana_cost": 38, "element": "dark", "life_steal": 0.4, "cooldown": 3},
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.5, "mana_cost": 20, "element": "light", "cooldown": 0},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 3.0, "mana_cost": 50, "element": "light", "cooldown": 3},
    "heavenly_light": {"name": "🌟 Небесный свет", "hp_restore": 60, "mana_cost": 30, "element": "light", "cooldown": 2},
    "reap": {"name": "💀 Жатва", "damage_mult": 2.5, "mana_cost": 42, "element": "dark", "life_steal": 0.3, "cooldown": 2},
    "death_sentence": {"name": "☠ Смертный приговор", "damage_mult": 4.5, "mana_cost": 75, "element": "dark", "cooldown": 5},
    "soul_harvest": {"name": "👻 Сбор душ", "damage_mult": 3.0, "mana_cost": 55, "element": "dark", "life_steal": 0.5, "cooldown": 3},
    "thunder_gods_wrath": {"name": "⚡ Гнев бога грома", "damage_mult": 5.0, "mana_cost": 85, "element": "lightning", "stun_chance": 50, "aoe": True, "cooldown": 5},
    "eye_of_the_storm": {"name": "🌀 Глаз бури", "damage_mult": 3.2, "mana_cost": 55, "element": "lightning", "cooldown": 3},
    "lightning_apocalypse": {"name": "⚡ Молниевый апокалипсис", "damage_mult": 6.0, "mana_cost": 95, "element": "lightning", "aoe": True, "cooldown": 6}
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
world_bosses = load_json(DATA_FILES['bosses'], {})

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
    
    def get_equipment_defense(self, part):
        """Получить защиту части тела от экипировки"""
        slot_map = {"head": "head", "body": "body", "legs": "legs"}
        slot = slot_map.get(part)
        if not slot:
            return 0
        
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
        """Получить урон оружия"""
        ik = self.data["equipment"].get("weapon")
        if not ik:
            return (5, 10)  # Базовый урон без оружия
        
        item = items.get(ik) or limited_items.get(ik)
        if not item or "damage" not in item:
            return (5, 10)
        
        min_d, max_d = item["damage"]
        
        # Зачарования
        ench = self.data.get("enchantments", {}).get(ik, {})
        if ench:
            if ench.get("effect") == "damage_boost":
                boost = ench.get("value", 0)
                min_d = int(min_d * (1 + boost / 100))
                max_d = int(max_d * (1 + boost / 100))
            elif ench.get("effect") == "fire_damage":
                bonus = ench.get("value", 0)
                min_d += bonus
                max_d += bonus
        
        return (min_d, max_d)
    
    def get_speed(self):
        """Получить скорость"""
        speed = 10  # Базовая скорость
        ik = self.data["equipment"].get("legs")
        if ik:
            item = items.get(ik) or limited_items.get(ik)
            if item:
                speed += item.get("speed", 0)
        
        # Зачарования
        for slot, ik in self.data["equipment"].items():
            if ik:
                ench = self.data.get("enchantments", {}).get(ik, {})
                if ench and ench.get("effect") == "speed_bonus":
                    speed += ench.get("value", 0)
        
        return speed

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
        self.log = []
        self.timeout_timer = None
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        # HP одинаковые
        base_hp = 150 + (self.p1.data["level"] + self.p2.data["level"]) * 3
        self.p1_hp = base_hp
        self.p2_hp = base_hp
        self.p1_max_hp = base_hp
        self.p2_max_hp = base_hp
        
        self.p1_mp = 60
        self.p2_mp = 60
        self.p1_max_mp = 60
        self.p2_max_mp = 60
        
        # Фазы: p1_defend -> p2_attack -> p2_defend -> p1_attack
        self.phase = "p1_defend"  # p1_defend, p2_attack_select, p2_defend, p1_attack_select
        self.p1_defend = None
        self.p2_defend = None
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Арена
        self.arena = random.choice(["colosseum", "forest", "volcano", "void"])
        
        # Время на ход (45 секунд)
        self.last_action_time = datetime.now()
        self.start_timeout()
        
        self.log.append(f"⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>")
    
    def start_timeout(self):
        """Запуск таймера на ход"""
        if self.timeout_timer:
            self.timeout_timer.cancel()
        
        self.timeout_timer = threading.Timer(45.0, self.handle_timeout)
        self.timeout_timer.start()
    
    def handle_timeout(self):
        """Обработка таймаута"""
        if not self.active:
            return
        
        if self.phase == "p1_defend":
            self.active = False
            self.winner = 2
            self.log.append("⏰ Игрок 1 не выбрал защиту! Победа игрока 2!")
        elif self.phase == "p2_attack_select":
            self.active = False
            self.winner = 1
            self.log.append("⏰ Игрок 2 не выбрал атаку! Победа игрока 1!")
        elif self.phase == "p2_defend":
            self.active = False
            self.winner = 1
            self.log.append("⏰ Игрок 2 не выбрал защиту! Победа игрока 1!")
        elif self.phase == "p1_attack_select":
            self.active = False
            self.winner = 2
            self.log.append("⏰ Игрок 1 не выбрал атаку! Победа игрока 2!")
        
        # Сохраняем результаты
        self._save_results()
    
    def get_player_name(self, num):
        return self.p1.data["first_name"] if num == 1 else self.p2.data["first_name"]
    
    def get_available_skills(self, player_num):
        """Получить доступные навыки"""
        player = self.p1 if player_num == 1 else self.p2
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        
        available = []
        
        # Базовые атаки
        base = ["quick_strike", "slash", "heavy_strike"]
        for sid in base:
            if sid not in cooldowns or cooldowns[sid] <= 0:
                available.append(sid)
        
        # Навыки оружия
        weapon_key = player.data["equipment"].get("weapon")
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
        """Установить защиту"""
        if player_num == 1:
            self.p1_defend = part
            if self.phase == "p1_defend":
                self.phase = "p2_attack_select"
        else:
            self.p2_defend = part
            if self.phase == "p2_defend":
                self.phase = "p1_attack_select"
        
        self.last_action_time = datetime.now()
        self.start_timeout()
    
    def execute_attack(self, player_num, skill_id, target_part):
        """Выполнить атаку"""
        attacker = player_num
        defender = 3 - player_num
        
        skill = SKILLS_DB.get(skill_id, {"name": "Атака", "damage_mult": 1.0, "mana_cost": 0})
        
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
        
        # Урон
        attacker_player = self.p1 if attacker == 1 else self.p2
        defender_player = self.p2 if attacker == 1 else self.p1
        
        min_d, max_d = attacker_player.get_weapon_damage()
        base_dmg = random.randint(min_d, max_d)
        dmg = int(base_dmg * skill.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_m = BODY_PARTS.get(target_part, {}).get("multiplier", 1.0)
        dmg = int(dmg * body_m)
        
        # Защита части тела
        defend_part = self.p2_defend if attacker == 1 else self.p1_defend
        if defend_part == target_part:
            # Броня уменьшает урон
            defense = defender_player.get_equipment_defense(target_part)
            reduction = defense / (defense + 80)
            dmg = int(dmg * (1 - reduction))
            self.log.append(f"🛡 {self.get_player_name(defender)} защитил {BODY_PARTS[target_part]['name']}! Броня снизила урон на {int(reduction*100)}%")
        else:
            # Попадание в незащищённую часть
            # Базовая защита части тела
            base_def = BODY_PARTS.get(target_part, {}).get("base_defense", 0)
            defense = defender_player.get_equipment_defense(target_part) + base_def
            reduction = defense / (defense + 100)
            dmg = int(dmg * (1 - reduction))
        
        # Крит (случайный)
        if random.random() < 0.1:
            dmg = int(dmg * 1.8)
            self.log.append("💥 КРИТИЧЕСКИЙ УДАР!")
        
        # Нанесение урона
        if defender == 1:
            self.p1_hp = max(0, self.p1_hp - dmg)
        else:
            self.p2_hp = max(0, self.p2_hp - dmg)
        
        self.log.append(f"⚔ {self.get_player_name(attacker)} [{skill['name']}] → {BODY_PARTS[target_part]['name']} {self.get_player_name(defender)}: <b>-{dmg} HP</b>")
        
        # Кулдауны
        if "cooldown" in skill and skill["cooldown"] > 0:
            cooldowns = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
            cooldowns[skill_id] = skill["cooldown"]
        
        # Уменьшение кулдаунов
        cooldowns = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
        for sid in list(cooldowns.keys()):
            cooldowns[sid] -= 1
            if cooldowns[sid] <= 0:
                del cooldowns[sid]
        
        # Восстановление маны
        if attacker == 1:
            self.p1_mp = min(self.p1_max_mp, self.p1_mp + 8)
        else:
            self.p2_mp = min(self.p2_max_mp, self.p2_mp + 8)
        
        # Проверка завершения
        if self.p1_hp <= 0:
            self.active = False
            self.winner = 2
        elif self.p2_hp <= 0:
            self.active = False
            self.winner = 1
        
        # Смена фазы
        if self.phase == "p2_attack_select" and attacker == 2:
            self.phase = "p2_defend"
        elif self.phase == "p1_attack_select" and attacker == 1:
            self.phase = "p1_defend"
            self.p1_defend = None
            self.p2_defend = None
            self.turn += 1
            if self.turn > self.max_turns:
                self.active = False
                self.winner = 0
        
        self.last_action_time = datetime.now()
        
        if self.active:
            self.start_timeout()
        else:
            self._save_results()
    
    def _save_results(self):
        """Сохранение результатов"""
        if self.winner is not None and self.winner > 0:
            winner_id = self.p1_id if self.winner == 1 else self.p2_id
            loser_id = self.p2_id if self.winner == 1 else self.p1_id
            
            if not winner_id.startswith("bot_") and not winner_id.startswith("boss_"):
                winner = Player(winner_id)
                if self.bet > 0:
                    winner.data["money"] += self.bet * 2
                winner.data["wins"] += 1
                winner.data["win_streak"] += 1
                winner.data["total_duels"] += 1
                if winner.data["win_streak"] > winner.data["best_streak"]:
                    winner.data["best_streak"] = winner.data["win_streak"]
                exp_w = self.turn * 10 + self.bet // 2
                winner.data["exp"] += exp_w
                winner.data["total_exp"] += exp_w
                check_level_up(winner)
                winner.save()
            
            if not loser_id.startswith("bot_") and not loser_id.startswith("boss_"):
                loser = Player(loser_id)
                loser.data["losses"] += 1
                loser.data["win_streak"] = 0
                loser.data["total_duels"] += 1
                exp_l = self.turn * 5 + self.bet // 5
                loser.data["exp"] += exp_l
                loser.data["total_exp"] += exp_l
                check_level_up(loser)
                loser.save()
    
    def get_state_text(self, for_player_id):
        """Текст состояния для игрока"""
        pn = 1 if str(for_player_id) == self.p1_id else 2
        
        def bar(cur, mx, icon):
            pct = cur / mx * 100 if mx > 0 else 0
            f = int(pct / 10)
            e = 10 - f
            return f"{icon} [{'█'*f}{'░'*e}] {cur}/{mx} ({pct:.0f}%)"
        
        text = f"""
<b>⚔ ДУЭЛЬ #{self.battle_id}</b>
━━━━━━━━━━━━━━━━━━━━
🏟 {self.arena} | Ход: <b>#{self.turn}</b> | Ставка: <b>{self.bet}💰</b>

<b>{self.get_player_name(1)}</b>
{bar(self.p1_hp, self.p1_max_hp, '❤')}
{bar(self.p1_mp, self.p1_max_mp, '💎')}

<b>{self.get_player_name(2)}</b>
{bar(self.p2_hp, self.p2_max_hp, '❤')}
{bar(self.p2_mp, self.p2_max_mp, '💎')}
━━━━━━━━━━━━━━━━━━━━
"""
        
        if not self.active:
            if self.winner == 0:
                text += "\n<b>🤝 НИЧЬЯ!</b>"
            else:
                text += f"\n<b>👑 Победитель: {self.get_player_name(self.winner)}!</b>"
            return text
        
        if self.phase == "p1_defend":
            if pn == 1:
                text += "\n🛡 <b>Выберите часть тела для защиты:</b>"
            else:
                text += "\n⏳ <b>Игрок 1 выбирает защиту...</b>"
        
        elif self.phase == "p2_attack_select":
            if pn == 2:
                text += f"\n🎯 <b>Выберите цель и навык атаки:</b>\n🛡 Игрок 1 защищает: {BODY_PARTS.get(self.p1_defend, {}).get('name', 'Не выбрано')}"
            else:
                text += "\n⏳ <b>Игрок 2 выбирает атаку...</b>"
        
        elif self.phase == "p2_defend":
            if pn == 2:
                text += "\n🛡 <b>Выберите часть тела для защиты:</b>"
            else:
                text += "\n⏳ <b>Игрок 2 выбирает защиту...</b>"
        
        elif self.phase == "p1_attack_select":
            if pn == 1:
                text += f"\n🎯 <b>Выберите цель и навык атаки:</b>\n🛡 Игрок 2 защищает: {BODY_PARTS.get(self.p2_defend, {}).get('name', 'Не выбрано')}"
            else:
                text += "\n⏳ <b>Игрок 1 выбирает атаку...</b>"
        
        if self.log:
            text += f"\n<i>{self.log[-1]}</i>"
        
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
    
    username = message.from_user.username
    first_name = message.from_user.first_name or "Игрок"
    
    # Всегда обновляем username
    if username and str(user_id) in users:
        users[str(user_id)]["username"] = username
        users[str(user_id)]["first_name"] = first_name
        save_json(DATA_FILES['users'], users)
    
    Player(user_id, username or f"user_{user_id}", first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v11.0 FINAL ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

🎯 <b>СИСТЕМА БОЯ:</b>
• Сначала защита → потом атака
• Броня уменьшает урон
• Каждое оружие имеет свои навыки
• Таймаут 45 сек на ход

💰 Старт: <b>500 монет</b>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль (бот)", callback_data="quick_duel"),
        types.InlineKeyboardButton("👥 Найти соперника", callback_data="find_opponent"),
        types.InlineKeyboardButton("🏆 Рейтинговая дуэль", callback_data="ranked_duel"),
        types.InlineKeyboardButton("💀 Хардкорная дуэль", callback_data="hardcore_duel"),
        types.InlineKeyboardButton("🎯 Дружеский спарринг", callback_data="sparring_duel"),
        types.InlineKeyboardButton("🔥 Дуэль на выживание", callback_data="survival_duel")
    )
    
    text = """
<b>⚔️ ДУЭЛИ</b>

<b>Пошаговая система:</b>
1️⃣ Игрок 1 защищает часть тела
2️⃣ Игрок 2 атакует
3️⃣ Игрок 2 защищает часть тела
4️⃣ Игрок 1 атакует
🔄 Повтор

<i>Броня уменьшает урон!</i>
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
        types.InlineKeyboardButton("⚙ Настройки", callback_data="hero_settings")
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
        types.InlineKeyboardButton("👹 Мировые боссы", callback_data="world_bosses"),
        types.InlineKeyboardButton("🌍 Ивенты", callback_data="world_events"),
        types.InlineKeyboardButton("📊 Топ", callback_data="world_top"),
        types.InlineKeyboardButton("ℹ Помощь", callback_data="world_help")
    )
    bot.send_message(message.chat.id, "<b>🌍 МИР</b>", reply_markup=markup)

# ==================== ДУЭЛИ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["quick_duel", "find_opponent", "ranked_duel", "hardcore_duel", "sparring_duel", "survival_duel"])
def duel_menu_handler(call):
    dt = call.data
    
    if dt == "quick_duel":
        show_quick_duel(call)
    elif dt == "find_opponent":
        show_matchmaking(call, "quick", 50)
    elif dt == "ranked_duel":
        show_matchmaking(call, "ranked", 100)
    elif dt == "hardcore_duel":
        show_matchmaking(call, "hardcore", 500)
    elif dt == "sparring_duel":
        show_matchmaking(call, "sparring", 0)
    elif dt == "survival_duel":
        show_matchmaking(call, "survival", 200)

def show_quick_duel(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    for bet in [50, 100, 200, 500]:
        markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"qduel_{bet}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="duel_back"))
    
    bot.edit_message_text(
        f"<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n\n💰 Баланс: <b>{player.data['money']}💰</b>",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

def show_matchmaking(call, duel_type, bet):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    # Проверка очереди
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
            opponent_player.save()
            player.save()
        
        duel = DuelInstance(opponent["user_id"], user_id, duel_type, bet)
        active_duels[user_id] = duel
        active_duels[opponent["user_id"]] = duel
        
        bot.edit_message_text("⚔ Соперник найден! Дуэль начинается!", call.message.chat.id, call.message.message_id)
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        
        # Отправляем сообщение второму игроку
        try:
            opponent_msg = bot.send_message(opponent["user_id"], "⚔ Дуэль началась!")
            show_duel_interface(opponent["user_id"], opponent_msg.message_id, duel, opponent["user_id"])
        except:
            pass
    else:
        queue.append({"user_id": user_id, "type": duel_type, "bet": bet})
        matchmaking_queue[duel_type] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        bot.edit_message_text("🔍 Поиск соперника...", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "duel_back")
def duel_back(call):
    duel_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def start_bot_duel(call):
    user_id = call.from_user.id
    bet = int(call.data.split("_")[1])
    player = Player(user_id)
    
    if player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
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
        "username": f"Bot_{bot_level}", "first_name": f"🤖 Бот Lv.{bot_level}",
        "money": 0, "level": bot_level, "exp": 0, "total_exp": 0,
        "hp": 100, "max_hp": 100, "mana": 60, "max_mana": 60,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000, "inventory": [], "equipment": equip,
        "enchantments": {}, "last_daily": None, "last_dungeon": None,
        "title": "Бот", "titles_collected": ["Бот"], "achievements": [],
        "clan": None, "clan_role": None, "registration_date": datetime.now().isoformat(),
        "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    player.data["money"] -= bet
    player.save()
    
    duel = DuelInstance(user_id, bot_id, "quick", bet)
    active_duels[str(user_id)] = duel
    
    bot.edit_message_text("⚔ Дуэль с ботом!", call.message.chat.id, call.message.message_id)
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

def show_duel_interface(chat_id, message_id, duel, user_id):
    """Показать интерфейс дуэли"""
    if not duel.active:
        finish_duel_display(chat_id, message_id, duel)
        return
    
    state_text = duel.get_state_text(user_id)
    pn = 1 if str(user_id) == duel.p1_id else 2
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if duel.phase == "p1_defend" and pn == 1:
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']}", callback_data=f"d_def_{part}"
            ))
    
    elif duel.phase == "p2_defend" and pn == 2:
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']}", callback_data=f"d_def_{part}"
            ))
    
    elif duel.phase == "p2_attack_select" and pn == 2:
        # Выбор цели
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🎯 {data['name']}", callback_data=f"d_tgt_{part}"
            ))
    
    elif duel.phase == "p1_attack_select" and pn == 1:
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🎯 {data['name']}", callback_data=f"d_tgt_{part}"
            ))
    
    # Бот автоматически делает ход
    if str(duel.p2_id).startswith("bot_"):
        if duel.phase == "p2_defend" and pn == 2:
            duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
            show_duel_interface(chat_id, message_id, duel, user_id)
            return
        elif duel.phase == "p1_defend" and pn == 1:
            duel.set_defend(1, random.choice(list(BODY_PARTS.keys())))
            show_duel_interface(chat_id, message_id, duel, user_id)
            return
    
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="d_refresh"))
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="d_surrender"))
    
    try:
        bot.edit_message_text(state_text[:4000], chat_id, message_id, reply_markup=markup)
    except:
        pass

# Временное хранилище для выбора цели
target_cache = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("d_tgt_"))
def duel_target_handler(call):
    user_id = call.from_user.id
    part = call.data.split("_")[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        return
    
    target_cache[str(user_id)] = part
    
    # Показать навыки
    pn = 1 if str(user_id) == duel.p1_id else 2
    skills = duel.get_available_skills(pn)
    
    state_text = duel.get_state_text(user_id) + f"\n🎯 Цель: <b>{BODY_PARTS[part]['name']}</b>\n<b>Выберите навык:</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for sid in skills[:8]:
        skill = SKILLS_DB.get(sid, {})
        name = skill.get("name", sid)
        mana = skill.get("mana_cost", 0)
        mult = skill.get("damage_mult", 1.0)
        cd = skill.get("cooldown", 0)
        
        btn_text = f"{name} x{mult} [{mana}MP]"
        if cd > 0:
            btn_text += f" CD:{cd}"
        
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"d_skill_{sid}"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="d_back_target"))
    
    try:
        bot.edit_message_text(state_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "d_back_target")
def duel_back_target(call):
    user_id = call.from_user.id
    duel = active_duels.get(str(user_id))
    if duel:
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("d_skill_"))
def duel_skill_handler(call):
    user_id = call.from_user.id
    skill_id = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        return
    
    target = target_cache.get(str(user_id), "body")
    pn = 1 if str(user_id) == duel.p1_id else 2
    
    duel.execute_attack(pn, skill_id, target)
    
    bot.answer_callback_query(call.id, "⚔ Атака!")
    
    if not duel.active:
        finish_duel_display(call.message.chat.id, call.message.message_id, duel)
    else:
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("d_def_"))
def duel_defend_handler(call):
    user_id = call.from_user.id
    part = call.data.split("_")[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        return
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    duel.set_defend(pn, part)
    
    bot.answer_callback_query(call.id, f"🛡 Защита: {BODY_PARTS[part]['name']}")
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data in ["d_refresh", "d_surrender"])
def duel_actions(call):
    user_id = call.from_user.id
    duel = active_duels.get(str(user_id))
    
    if call.data == "d_refresh":
        if duel and duel.active:
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        else:
            bot.edit_message_text("❌ Дуэль завершена", call.message.chat.id, call.message.message_id)
    
    elif call.data == "d_surrender":
        if duel and duel.active:
            duel.active = False
            duel.winner = 2 if str(user_id) == duel.p1_id else 1
            duel._save_results()
            finish_duel_display(call.message.chat.id, call.message.message_id, duel)
        else:
            bot.edit_message_text("❌ Дуэль завершена", call.message.chat.id, call.message.message_id)

def finish_duel_display(chat_id, message_id, duel):
    """Отображение результатов дуэли"""
    # Очистка
    for uid in [duel.p1_id, duel.p2_id]:
        if uid in active_duels and active_duels[uid].battle_id == duel.battle_id:
            del active_duels[uid]
    
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") and uid in users:
            del users[uid]
    save_json(DATA_FILES['users'], users)
    
    if duel.winner == 0:
        result = "<b>🤝 НИЧЬЯ!</b>\nХодов: " + str(duel.turn)
    else:
        winner_name = duel.get_player_name(duel.winner)
        loser_name = duel.get_player_name(3 - duel.winner)
        result = f"<b>👑 {winner_name} ПОБЕЖДАЕТ!</b>\n💀 {loser_name} проигрывает\n💰 Ставка: {duel.bet}💰\n📊 Ходов: {duel.turn}"
    
    bot.edit_message_text(result, chat_id, message_id)

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
        types.InlineKeyboardButton("◀ Назад", callback_data="trade_back")
    )
    player = Player(call.from_user.id)
    bot.edit_message_text(f"<b>🛒 МАГАЗИН</b>\n💰 <b>{player.data['money']}💰</b>", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shop_"))
def shop_category_handler(call):
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
        elif item.get("type") == "potion":
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
def buy_item_handler(call):
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

@bot.callback_query_handler(func=lambda call: call.data == "trade_back")
def trade_back(call):
    trade_section(call.message)

# ==================== ОСТАЛЬНЫЕ ОБРАБОТЧИКИ ====================
@bot.callback_query_handler(func=lambda call: call.data == "trade_limited")
def limited_shop_handler(call):
    if not limited_items:
        bot.edit_message_text("💎 Нет лимитированных", call.message.chat.id, call.message.message_id)
        return
    
    text = "<b>💎 ЛИМИТИРОВАННЫЕ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for ik, item in limited_items.items():
        if item["remaining"] > 0:
            text += f"<b>{item['name']}</b> — {item['remaining']}/{item['total']} — 💰 {item['price']}\n\n"
            markup.add(types.InlineKeyboardButton(f"Купить - {item['price']}💰", callback_data=f"buy_{ik}"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="trade_back"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "trade_daily")
def daily_bonus_handler(call):
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
    
    old = player.data["level"]
    check_level_up(player)
    player.save()
    
    text = f"<b>🎁 БОНУС</b>\n💰 +{bonus}\n✨ +{exp}"
    if player.data["level"] > old:
        text += f"\n🎉 УРОВЕНЬ <b>{player.data['level']}</b>!"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "trade_market")
def market_menu_handler(call):
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
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="trade_back"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mktbuy_"))
def market_buy_handler(call):
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

@bot.callback_query_handler(func=lambda call: call.data in ["trade_sell", "trade_my_lots"])
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
                markup.add(types.InlineKeyboardButton(f"Снять: {item['name']}", callback_data=f"rmlot_{lid}"))
        
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="trade_back"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rmlot_"))
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
@bot.callback_query_handler(func=lambda call: call.data == "hero_stats")
def hero_stats_handler(call):
    user_id = call.from_user.id
    player = Player(user_id)
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
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="hero_back"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "hero_inventory")
def hero_inventory_handler(call):
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
                eq = " [Экип.]"
        
        text += f"{idx}. {r} {item['name']} x{cnt}{eq}\n"
        
        if item.get("type") in ["weapon", "helmet", "armor", "boots"]:
            markup.add(types.InlineKeyboardButton(f"Экипировать: {item['name']}", callback_data=f"eq_{ik}"))
        elif item.get("type") == "potion":
            markup.add(types.InlineKeyboardButton(f"Использовать: {item['name']}", callback_data=f"use_{ik}"))
        
        idx += 1
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="hero_back"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("eq_"))
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
        bot.answer_callback_query(call.id, "❌ Нельзя экипировать!")
        return
    
    old = player.data["equipment"][slot]
    if old:
        player.data["inventory"].append(old)
    
    player.data["equipment"][slot] = ik
    player.data["inventory"].remove(ik)
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ {item['name']}!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("use_"))
def use_item_handler(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(ik)
    if not item or item.get("type") != "potion" or ik not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌ Нельзя!")
        return
    
    if "heal" in item:
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + item["heal"])
    
    player.data["inventory"].remove(ik)
    player.save()
    bot.answer_callback_query(call.id, "✅ Использовано!")

@bot.callback_query_handler(func=lambda call: call.data == "hero_back")
def hero_back(call):
    hero_section(call.message)

# ==================== МИР: ПОДЗЕМЕЛЬЯ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_dungeons")
def world_dungeons_handler(call):
    text = """
<b>🏰 ПОДЗЕМЕЛЬЯ</b>

🐺 Логово волка (Ур. 1+) - 3 босса
🕷 Паучьи пещеры (Ур. 5+) - 3 босса
💀 Катакомбы (Ур. 10+) - 3 босса
🐉 Драконье логово (Ур. 15+) - 3 босса
👹 Бездна (Ур. 25+) - 3 босса

Кулдаун: 1 час
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, name in enumerate(["🐺 Логово волка", "🕷 Паучьи пещеры", "💀 Катакомбы", "🐉 Драконье логово", "👹 Бездна"], 1):
        markup.add(types.InlineKeyboardButton(name, callback_data=f"dung_{i}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_back"))
    
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
    
    # Создание 3 боссов для данжа
    boss_names = [["🐺 Волк", "🐺 Вожак", "🐺 Альфа"], 
                  ["🕷 Паук", "🕷 Матка", "🕷 Королева"],
                  ["💀 Скелет", "💀 Лич", "💀 Некромант"],
                  ["🐉 Драконид", "🐉 Дракон", "🐉 Архидракон"],
                  ["👹 Бес", "👹 Демон", "👹 Владыка"]]
    
    current_boss = dungeons_data.get(str(user_id), {}).get("current_boss", 0)
    
    if current_boss >= 3:
        # Все боссы побеждены
        reward = random.randint(200, 500) * dl
        player.data["money"] += reward
        player.data["dungeons_completed"] = player.data.get("dungeons_completed", 0) + 1
        dungeons_data[str(user_id)] = {}
        save_json(DATA_FILES['dungeons'], dungeons_data)
        player.save()
        
        bot.edit_message_text(f"🏰 Все боссы повержены!\n💰 +{reward}", call.message.chat.id, call.message.message_id)
        return
    
    # Создание босса
    boss_level = level_reqs[dl - 1] * 2 + dl * 2 + current_boss * 3
    boss_id = f"boss_{random.randint(100000, 999999)}"
    
    equip = {"weapon": random.choice([k for k, v in items.items() if v.get("type") == "weapon"]) if random.random() < 0.5 else None,
             "head": random.choice([k for k, v in items.items() if v.get("type") == "helmet"]) if random.random() < 0.5 else None,
             "body": random.choice([k for k, v in items.items() if v.get("type") == "armor"]) if random.random() < 0.5 else None,
             "legs": random.choice([k for k, v in items.items() if v.get("type") == "boots"]) if random.random() < 0.5 else None}
    
    users[boss_id] = {
        "username": f"Boss_{boss_level}", "first_name": boss_names[dl-1][current_boss],
        "money": 0, "level": boss_level, "exp": 0, "total_exp": 0,
        "hp": 100, "max_hp": 100, "mana": 60, "max_mana": 60,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000, "inventory": [], "equipment": equip,
        "enchantments": {}, "last_daily": None, "last_dungeon": None,
        "title": "Босс", "titles_collected": ["Босс"], "achievements": [],
        "clan": None, "clan_role": None, "registration_date": datetime.now().isoformat(),
        "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    dungeons_data[str(user_id)] = {"dungeon_level": dl, "current_boss": current_boss, "boss_id": boss_id, "boss_names": boss_names[dl-1]}
    save_json(DATA_FILES['dungeons'], dungeons_data)
    
    duel = DuelInstance(user_id, boss_id, "dungeon", 0)
    active_duels[str(user_id)] = duel
    
    bot.edit_message_text(f"⚔ Босс {current_boss+1}/3: <b>{boss_names[dl-1][current_boss]}</b>!", 
                          call.message.chat.id, call.message.message_id)
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

# ==================== МИРОВЫЕ БОССЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_bosses")
def world_bosses_handler(call):
    if not world_bosses.get("active"):
        world_bosses["active"] = {
            "name": "🐉 Мировой дракон",
            "hp": 1000000,
            "max_hp": 1000000,
            "level": 50,
            "reward": 10000,
            "participants": {}
        }
        save_json(DATA_FILES['bosses'], world_bosses)
    
    boss = world_bosses["active"]
    user_id = str(call.from_user.id)
    player_dmg = boss.get("participants", {}).get(user_id, 0)
    
    text = f"""
<b>👹 МИРОВОЙ БОСС</b>

<b>{boss['name']}</b>
❤ HP: {boss['hp']}/{boss['max_hp']} ({boss['hp']/boss['max_hp']*100:.1f}%)
⭐ Уровень: {boss['level']}
💰 Награда: {boss['reward']}💰

Ваш урон: <b>{player_dmg}</b>
Нажмите кнопку для атаки!
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("⚔ Атаковать босса!", callback_data="boss_attack"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_back"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "boss_attack")
def boss_attack_handler(call):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if not world_bosses.get("active"):
        bot.answer_callback_query(call.id, "❌ Нет активного босса!")
        return
    
    boss = world_bosses["active"]
    
    # Игрок наносит урон
    min_d, max_d = player.get_weapon_damage()
    dmg = random.randint(min_d, max_d) * random.randint(1, 5)
    
    boss["hp"] = max(0, boss["hp"] - dmg)
    boss["participants"][user_id] = boss.get("participants", {}).get(user_id, 0) + dmg
    
    if boss["hp"] <= 0:
        # Босс побеждён
        top_dmg = sorted(boss["participants"].items(), key=lambda x: x[1], reverse=True)
        
        # Награда топ-3
        for i, (uid, dmg_dealt) in enumerate(top_dmg[:3]):
            try:
                p = Player(uid)
                if i == 0:
                    p.data["money"] += boss["reward"]
                elif i == 1:
                    p.data["money"] += boss["reward"] // 2
                else:
                    p.data["money"] += boss["reward"] // 3
                p.save()
            except:
                pass
        
        world_bosses["active"] = None
        save_json(DATA_FILES['bosses'], world_bosses)
        
        bot.edit_message_text(f"🎉 БОСС ПОВЕРЖЕН!\nВаш урон: {dmg}", call.message.chat.id, call.message.message_id)
    else:
        save_json(DATA_FILES['bosses'], world_bosses)
        bot.answer_callback_query(call.id, f"⚔ -{dmg} HP боссу!")
        world_bosses_handler(call)

# ==================== ТУРНИРЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_tournaments")
def world_tournaments_handler(call):
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
Статус: {tour.get('status', 'Ожидание')}
Участников: {len(tour.get('participants', []))}/8
Приз: <b>{tour.get('prize_pool', 0)}💰</b>
Взнос: 500💰

Система: 1/4 → 1/2 → Финал
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🏆 Участвовать (500💰)", callback_data="tour_join"),
        types.InlineKeyboardButton("📋 Участники", callback_data="tour_list"),
        types.InlineKeyboardButton("◀ Назад", callback_data="world_back")
    )
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

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
    if len(participants) >= 8:
        bot.answer_callback_query(call.id, "❌ Турнир заполнен!")
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
    for i, uid in enumerate(participants[:8], 1):
        p = Player(uid)
        text += f"{i}. {p.data['first_name']} (Lv.{p.data['level']})\n"
    
    bot.send_message(call.message.chat.id, text)

# ==================== ИВЕНТЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_events")
def world_events_handler(call):
    current_event = events.get("current", {})
    
    if not current_event or datetime.fromisoformat(current_event.get("expires", "2000-01-01")) < datetime.now():
        new_event = {
            "name": random.choice(["🌋 Извержение", "❄ Буря", "⚡ Гроза", "🌑 Затмение", "✨ Звездопад"]),
            "description": "Участвуйте в дуэлях!",
            "ench_reward": random.choice(ENCHANT_EFFECTS),
            "reward_money": random.randint(500, 2000),
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
🎁 Награда: {ev['reward_money']}💰 + зачарование
⏰ {minutes} мин.
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_back"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== ТОП ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_top")
def world_top_handler(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⭐ Уровень", callback_data="top_level"),
        types.InlineKeyboardButton("⚔ Победы", callback_data="top_wins"),
        types.InlineKeyboardButton("💰 Монеты", callback_data="top_money"),
        types.InlineKeyboardButton("◀ Назад", callback_data="world_back")
    )
    bot.edit_message_text("<b>📊 ТОП</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def show_top_handler(call):
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

@bot.callback_query_handler(func=lambda call: call.data == "world_help")
def world_help_handler(call):
    text = "<b>ℹ ПОМОЩЬ</b>\n⚔ /duel\n🛒 /shop\n👤 /stats\n/sell [№] [цена]"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_back"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "world_back")
def world_back(call):
    world_section(call.message)

# ==================== КЛАНЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_clans")
def world_clans_handler(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data.get("clan"):
        clan = clans.get(player.data["clan"], {})
        text = f"<b>🛡 {player.data['clan']}</b>\n👥 {len(clan.get('members', []))} уч.\n💰 {clan.get('treasury', 0)}💰"
    else:
        text = "<b>🛡 КЛАНЫ</b>\n/createclan [имя]\n/joinclan [имя]"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_back"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(commands=['createclan', 'joinclan'])
def clan_commands_handler(message):
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
        player.save()
        
        if message.from_user.first_name not in clans[name].get("members", []):
            clans[name]["members"].append(message.from_user.first_name)
        save_json(DATA_FILES['clans'], clans)
        bot.send_message(message.chat.id, f"✅ Вы в <b>{name}</b>!")

# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================
def check_level_up(player):
    level = player.data["level"]
    exp_needed = int(100 * (1.5 ** (level - 1)))
    
    while player.data["exp"] >= exp_needed:
        player.data["exp"] -= exp_needed
        player.data["level"] += 1
        player.data["max_hp"] += 15
        player.data["max_mana"] += 8
        player.data["hp"] = player.data["max_hp"]
        player.data["mana"] = player.data["max_mana"]
        
        titles = {5: "Боец", 10: "Воитель", 15: "Рыцарь", 20: "Ветеран", 30: "Мастер", 40: "Герой", 50: "Легенда"}
        for req, title in titles.items():
            if player.data["level"] >= req and title not in player.data["titles_collected"]:
                player.data["titles_collected"].append(title)
                player.data["title"] = title
        
        level = player.data["level"]
        exp_needed = int(100 * (1.5 ** (level - 1)))

@bot.message_handler(commands=['sell'])
def sell_command(message):
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
    
    item = items.get(ik, {})
    bot.send_message(message.chat.id, f"✅ {item.get('name', ik)} за {price}💰!")

@bot.message_handler(commands=['transfer'])
def transfer_command(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Ответьте на сообщение!")
        return
    
    user_id = message.from_user.id
    target_id = message.reply_to_message.from_user.id
    
    try:
        idx = int(message.text.split()[1]) - 1
    except:
        bot.send_message(message.chat.id, "❌ /transfer [номер]")
        return
    
    player = Player(user_id)
    target = Player(target_id)
    
    if idx < 0 or idx >= len(player.data["inventory"]):
        bot.send_message(message.chat.id, "❌ Неверный номер!")
        return
    
    ik = player.data["inventory"].pop(idx)
    target.data["inventory"].append(ik)
    player.save()
    target.save()
    
    item = items.get(ik, {})
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
        types.InlineKeyboardButton("🏟 Создать турнир", callback_data="adm_tour"),
        types.InlineKeyboardButton("👹 Создать босса", callback_data="adm_boss"),
        types.InlineKeyboardButton("🌍 Новый ивент", callback_data="adm_event"),
        types.InlineKeyboardButton("📋 Список игроков", callback_data="adm_list")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Доступ запрещён!")
        return
    
    action = call.data.split("_")[1]
    
    if action == "stats":
        text = f"👥 Игроков: {len(users)}\n💰 Монет: {sum(u.get('money',0) for u in users.values())}\n⚔ Дуэлей: {sum(u.get('total_duels',0) for u in users.values())}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    
    elif action == "money":
        bot.send_message(call.message.chat.id, "💰 /givemoney @username [сумма]")
    
    elif action == "item":
        bot.send_message(call.message.chat.id, "🎁 /giveitem @username [item_key]")
    
    elif action == "ban":
        bot.send_message(call.message.chat.id, "⛔ /ban @username [причина]")
    
    elif action == "bc":
        bot.send_message(call.message.chat.id, "📢 /broadcast [текст]")
    
    elif action == "reset":
        bot.send_message(call.message.chat.id, "🔄 /resetdaily @username")
    
    elif action == "info":
        bot.send_message(call.message.chat.id, "👁 /userinfo @username")
    
    elif action == "unban":
        bot.send_message(call.message.chat.id, "✅ /unban @username")
    
    elif action == "tour":
        tournaments["active"] = {
            "name": "Новый турнир",
            "participants": [],
            "rounds": [],
            "current_round": 0,
            "prize_pool": 0,
            "status": "registration"
        }
        save_json(DATA_FILES['tournaments'], tournaments)
        bot.answer_callback_query(call.id, "✅ Турнир создан!")
    
    elif action == "boss":
        world_bosses["active"] = {
            "name": "👹 Новый босс",
            "hp": 500000,
            "max_hp": 500000,
            "level": 50,
            "reward": 5000,
            "participants": {}
        }
        save_json(DATA_FILES['bosses'], world_bosses)
        bot.answer_callback_query(call.id, "✅ Босс создан!")
    
    elif action == "event":
        events["current"] = {
            "name": "🌍 Новый ивент",
            "description": "Участвуйте в дуэлях!",
            "ench_reward": random.choice(ENCHANT_EFFECTS),
            "reward_money": 2000,
            "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        save_json(DATA_FILES['events'], events)
        bot.answer_callback_query(call.id, "✅ Ивент создан!")
    
    elif action == "list":
        text = "<b>📋 ИГРОКИ</b>\n\n"
        for uid, data in list(users.items())[:20]:
            text += f"• @{data.get('username', 'нет')} — {data.get('first_name', 'Игрок')} (Ур.{data.get('level',1)})\n"
        bot.send_message(call.message.chat.id, text[:4000])

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'broadcast', 'resetdaily', 'userinfo'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd in ["givemoney", "giveitem", "ban", "unban", "resetdaily", "userinfo"]:
            username = parts[1].replace('@', '') if len(parts) > 1 else ""
            
            # Поиск пользователя по username
            found_uid = None
            for uid, data in users.items():
                if data.get("username", "").lower() == username.lower():
                    found_uid = uid
                    break
            
            if not found_uid:
                bot.send_message(message.chat.id, f"❌ Игрок @{username} не найден!")
                return
            
            if cmd == "givemoney":
                amount = int(parts[2]) if len(parts) > 2 else 0
                p = Player(found_uid)
                p.data["money"] += amount
                p.save()
                bot.send_message(message.chat.id, f"✅ {amount}💰 → @{username}")
            
            elif cmd == "giveitem":
                ik = parts[2] if len(parts) > 2 else ""
                if ik:
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
            
            elif cmd == "resetdaily":
                p = Player(found_uid)
                p.data["last_daily"] = None
                p.data["last_dungeon"] = None
                p.save()
                bot.send_message(message.chat.id, f"✅ @{username} сброшен!")
            
            elif cmd == "userinfo":
                p = Player(found_uid)
                d = p.data
                text = f"<b>👤 @{username}</b>\nИмя: {d['first_name']}\nУр.: {d['level']}\n💰 {d['money']}\nПобед: {d['wins']}"
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

# ==================== ЗАПУСК ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v11.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print(f"⚔ Предметов: {len(items)}")
    print("=" * 60)
    print("✅ Пошаговые дуэли: защита → атака по очереди")
    print("✅ Броня уменьшает урон на защищённые части")
    print("✅ Таймаут 45 сек на ход")
    print("✅ Данжи с 3 боссами")
    print("✅ Мировые боссы")
    print("✅ Турниры")
    print("✅ Ивенты с наградами")
    print("✅ Админ-панель с поиском по @username")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
