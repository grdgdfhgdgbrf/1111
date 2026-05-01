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
    {"name": "🎯 Меткое", "effect": "crit_bonus", "value": 20}
]

# ==================== ФАЙЛЫ ====================
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
    'dungeon_bosses': 'dungeon_bosses.json'
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
    "rusty_sword": {"name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 1, "skills": ["slash", "quick_strike"]},
    "hunters_bow": {"name": "🏹 Лук охотника", "damage": (7, 14), "price": 150, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 3, "skills": ["power_shot", "multi_shot"], "element": "nature"},
    "flame_blade": {"name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 7, "skills": ["fire_slash", "inferno_strike", "flame_wave"], "element": "fire"},
    "frost_axe": {"name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 10, "skills": ["frost_strike", "ice_shatter", "blizzard"], "element": "ice"},
    "storm_staff": {"name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500, "type": "weapon", "slot": "weapon", "rarity": "rare", "level_req": 14, "skills": ["lightning_bolt", "thunder_storm", "chain_lightning"], "element": "lightning"},
    "shadow_dagger": {"name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "slot": "weapon", "rarity": "epic", "level_req": 22, "skills": ["shadow_strike", "assassinate", "dark_veil", "soul_drain"], "element": "dark"},
    "divine_spear": {"name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "slot": "weapon", "rarity": "legendary", "level_req": 28, "skills": ["holy_strike", "divine_judgment", "heavenly_light"], "element": "light"},
    "death_scythe": {"name": "💀 Коса смерти", "damage": (40, 65), "price": 12000, "type": "weapon", "slot": "weapon", "rarity": "mythic", "level_req": 35, "skills": ["reap", "death_sentence", "soul_harvest"], "element": "dark"}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 200, "price": 350, "type": "potion", "rarity": "rare", "level_req": 15},
    "mana_potion": {"name": "💎 Зелье маны", "mana_restore": 60, "price": 60, "type": "potion", "rarity": "common", "level_req": 5}
}

LIMITED_ITEMS = {
    "thunderfury": {"name": "⚡ Ярость грома", "damage": (60, 95), "total": 3, "remaining": 3, "price": 50000, "type": "weapon", "slot": "weapon", "rarity": "divine", "element": "lightning", "skills": ["thunder_gods_wrath", "eye_of_the_storm", "lightning_apocalypse"]},
    "immortal_helmet": {"name": "✨ Шлем бессмертия", "defense": 80, "hp_bonus": 300, "total": 2, "remaining": 2, "price": 75000, "type": "helmet", "slot": "head", "rarity": "divine"}
}

ALL_ITEMS = {}
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(BOOTS)
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(POTIONS)

# ==================== БАЗА НАВЫКОВ ====================
SKILLS_DB = {
    # Быстрые (восстановление 0-1 ход)
    "quick_strike": {"name": "⚡ Быстрый удар", "damage_mult": 0.8, "mana_cost": 5, "cooldown": 0, "hits": 2, "tier": 1},
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 8, "cooldown": 0, "tier": 1},
    "power_shot": {"name": "🎯 Мощный выстрел", "damage_mult": 1.5, "mana_cost": 12, "cooldown": 1, "tier": 1},
    # Средние (восстановление 1-2 хода)
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.6, "mana_cost": 18, "cooldown": 1, "element": "fire", "burn_chance": 25, "tier": 2},
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.5, "mana_cost": 16, "cooldown": 1, "element": "ice", "freeze_chance": 20, "tier": 2},
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.7, "mana_cost": 20, "cooldown": 1, "element": "lightning", "stun_chance": 15, "tier": 2},
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.7, "mana_cost": 22, "cooldown": 1, "element": "dark", "poison_chance": 20, "tier": 2},
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.6, "mana_cost": 20, "cooldown": 1, "element": "light", "tier": 2},
    "water_slash": {"name": "🌊 Водяной разрез", "damage_mult": 1.4, "mana_cost": 15, "cooldown": 1, "element": "water", "tier": 2},
    # Сильные (восстановление 2-3 хода)
    "inferno_strike": {"name": "🌋 Инферно удар", "damage_mult": 2.3, "mana_cost": 35, "cooldown": 2, "element": "fire", "burn_chance": 50, "tier": 3},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.1, "mana_cost": 30, "cooldown": 2, "element": "ice", "freeze_chance": 45, "tier": 3},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.4, "mana_cost": 40, "cooldown": 2, "element": "lightning", "stun_chance": 30, "tier": 3},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.2, "mana_cost": 55, "cooldown": 3, "element": "dark", "ignore_defense": 50, "tier": 4},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 2.8, "mana_cost": 48, "cooldown": 3, "element": "light", "tier": 4},
    # Ультимативные (восстановление 4-5 ходов)
    "flame_wave": {"name": "🔥 Волна пламени", "damage_mult": 3.0, "mana_cost": 50, "cooldown": 4, "element": "fire", "aoe": True, "tier": 5},
    "blizzard": {"name": "🌨 Метель", "damage_mult": 2.8, "mana_cost": 48, "cooldown": 4, "element": "ice", "aoe": True, "tier": 5},
    "chain_lightning": {"name": "⚡ Цепная молния", "damage_mult": 2.5, "mana_cost": 42, "cooldown": 4, "element": "lightning", "chain_hits": 3, "tier": 5},
    "reap": {"name": "💀 Жатва", "damage_mult": 3.5, "mana_cost": 60, "cooldown": 5, "element": "dark", "life_steal": 0.3, "tier": 5},
    "thunder_gods_wrath": {"name": "⚡ Гнев бога грома", "damage_mult": 4.5, "mana_cost": 80, "cooldown": 5, "element": "lightning", "stun_chance": 50, "tier": 5}
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
matchmaking_queue = load_json(DATA_FILES['matchmaking'], {})
dungeon_bosses_progress = load_json(DATA_FILES['dungeon_bosses'], {})

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
    
    def get_equipment_stats(self):
        """Только статы от экипировки"""
        stats = {
            "head_def": 0, "body_def": 0, "legs_def": 0,
            "min_dmg": 0, "max_dmg": 0, "speed": 0,
            "hp_bonus": 0, "mana_bonus": 0, "element": None,
            "skills": [], "enchant_effects": {}
        }
        
        for slot, ik in self.data["equipment"].items():
            if not ik:
                continue
            item = items.get(ik) or limited_items.get(ik)
            if not item:
                continue
            
            if item.get("slot") == "weapon":
                if "damage" in item:
                    stats["min_dmg"] += item["damage"][0]
                    stats["max_dmg"] += item["damage"][1]
                if "element" in item:
                    stats["element"] = item["element"]
                if "skills" in item:
                    stats["skills"].extend(item["skills"])
            
            elif item.get("slot") == "head":
                stats["head_def"] += item.get("defense", 0)
                stats["hp_bonus"] += item.get("hp_bonus", 0)
                stats["mana_bonus"] += item.get("mana_bonus", 0)
            
            elif item.get("slot") == "body":
                stats["body_def"] += item.get("defense", 0)
                stats["hp_bonus"] += item.get("hp_bonus", 0)
            
            elif item.get("slot") == "legs":
                stats["legs_def"] += item.get("defense", 0)
                stats["speed"] += item.get("speed", 0)
            
            # Зачарования
            ench = self.data.get("enchantments", {}).get(ik, {})
            if ench:
                eff = ench.get("effect")
                val = ench.get("value", 0)
                stats["enchant_effects"][eff] = stats["enchant_effects"].get(eff, 0) + val
        
        return stats

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
        
        # Статы от экипировки
        self.p1_eq = self.p1.get_equipment_stats()
        self.p2_eq = self.p2.get_equipment_stats()
        
        # HP (одинаковые для честного боя)
        self.p1_hp = 150 + self.p1_eq["hp_bonus"]
        self.p2_hp = 150 + self.p2_eq["hp_bonus"]
        self.p1_max_hp = self.p1_hp
        self.p2_max_hp = self.p2_hp
        
        # MP
        self.p1_mp = 50 + self.p1_eq["mana_bonus"]
        self.p2_mp = 50 + self.p2_eq["mana_bonus"]
        self.p1_max_mp = self.p1_mp
        self.p2_max_mp = self.p2_mp
        
        # Фазы
        self.p1_phase = "defend_select"  # defend_select, attack_select, done
        self.p2_phase = "defend_select"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        
        # Очерёдность
        p1_spd = random.randint(1, 20) + self.p1_eq["speed"]
        p2_spd = random.randint(1, 20) + self.p2_eq["speed"]
        self.first_attacker = 1 if p1_spd >= p2_spd else 2
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Арена
        self.arena = random.choice(["colosseum", "forest", "volcano", "tundra", "void"])
        
        self._log_both(f"⚔ Битва началась! Арена: {self._arena_name()}")
    
    def _arena_name(self):
        return {"colosseum": "Колизей", "forest": "Лес", "volcano": "Вулкан", "tundra": "Тундра", "void": "Пустота"}.get(self.arena, self.arena)
    
    def _log_both(self, msg):
        self.log_p1.append(msg)
        self.log_p2.append(msg)
    
    def _log_player(self, player_num, msg):
        if player_num == 1:
            self.log_p1.append(msg)
        else:
            self.log_p2.append(msg)
    
    def get_player_name(self, num):
        return self.p1.data["first_name"] if num == 1 else self.p2.data["first_name"]
    
    def get_available_skills(self, player_num):
        eq = self.p1_eq if player_num == 1 else self.p2_eq
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        
        available = []
        
        # Базовые
        base = ["quick_strike", "slash"]
        for sid in base:
            if sid not in cooldowns or cooldowns[sid] <= 0:
                available.append(sid)
        
        # Навыки оружия
        for sid in eq["skills"]:
            if sid in SKILLS_DB:
                cd = cooldowns.get(sid, 0)
                if cd <= 0:
                    available.append(sid)
        
        return list(set(available))
    
    def set_defend(self, player_num, part):
        if player_num == 1:
            self.p1_defend = part
            self.p1_phase = "attack_select"
            self._log_player(1, f"🛡 Вы защищаете {BODY_PARTS[part]['name']}")
        else:
            self.p2_defend = part
            self.p2_phase = "attack_select"
            self._log_player(2, f"🛡 Вы защищаете {BODY_PARTS[part]['name']}")
    
    def execute_attack(self, player_num, skill_id, target_part):
        if player_num == 1:
            self.p1_skill = skill_id
            self.p1_target = target_part
            self.p1_phase = "done"
        else:
            self.p2_skill = skill_id
            self.p2_target = target_part
            self.p2_phase = "done"
        
        # Если оба готовы - разрешаем раунд
        if self.p1_phase == "done" and self.p2_phase == "done":
            self._resolve_round()
    
    def _resolve_round(self):
        """Разрешение раунда: оба атакуют по очереди"""
        # Очерёдность
        first = self.first_attacker
        second = 3 - first
        
        # Атака первого
        self._do_attack(first, second)
        if self.p1_hp <= 0 or self.p2_hp <= 0:
            self._check_end()
            return
        
        # Атака второго
        self._do_attack(second, first)
        self._check_end()
        
        # Декей кулдаунов
        for cd in [self.p1_cooldowns, self.p2_cooldowns]:
            for sid in list(cd.keys()):
                cd[sid] -= 1
                if cd[sid] <= 0:
                    del cd[sid]
        
        # Смена очерёдности
        self.first_attacker = 3 - self.first_attacker
        
        # Сброс фаз
        self.p1_phase = "defend_select"
        self.p2_phase = "defend_select"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        
        self.turn += 1
        if self.turn > self.max_turns:
            self.active = False
            self.winner = 0
    
    def _do_attack(self, attacker, defender):
        skill_id = self.p1_skill if attacker == 1 else self.p2_skill
        target_part = self.p1_target if attacker == 1 else self.p2_target
        defend_part = self.p2_defend if attacker == 1 else self.p1_defend
        
        if not skill_id or not target_part:
            return
        
        skill = SKILLS_DB.get(skill_id, {"name": "Атака", "damage_mult": 1.0, "mana_cost": 0, "cooldown": 0, "tier": 1})
        
        # Статы атакующего и защищающегося
        a_eq = self.p1_eq if attacker == 1 else self.p2_eq
        d_eq = self.p2_eq if attacker == 1 else self.p1_eq
        
        # Проверка маны
        mc = skill.get("mana_cost", 0)
        if attacker == 1:
            if self.p1_mp < mc:
                self._log_both(f"❌ {self.get_player_name(attacker)}: нет маны!")
                return
            self.p1_mp -= mc
        else:
            if self.p2_mp < mc:
                self._log_both(f"❌ {self.get_player_name(attacker)}: нет маны!")
                return
            self.p2_mp -= mc
        
        # Проверка: попал ли в защищённую часть?
        if defend_part == target_part:
            # Заблокировано частично или полностью
            def_value = 0
            if defend_part == "head":
                def_value = d_eq["head_def"]
            elif defend_part == "body":
                def_value = d_eq["body_def"]
            elif defend_part == "legs":
                def_value = d_eq["legs_def"]
            
            reduction = def_value / (def_value + 50)  # Формула снижения урона
            reduction = min(0.9, reduction)  # Максимум 90% снижения
            
            # Расчёт урона
            base_dmg = random.randint(a_eq["min_dmg"], a_eq["max_dmg"])
            base_dmg = int(base_dmg * skill.get("damage_mult", 1.0))
            body_m = BODY_PARTS.get(target_part, {}).get("multiplier", 1.0)
            base_dmg = int(base_dmg * body_m)
            
            final_dmg = int(base_dmg * (1 - reduction))
            
            self._log_both(f"🛡 {self.get_player_name(attacker)} бьёт в {BODY_PARTS[target_part]['name']}, но {self.get_player_name(defender)} защитил! Урон: {final_dmg} (снижен на {int(reduction*100)}%)")
            
            if defender == 1:
                self.p1_hp = max(0, self.p1_hp - final_dmg)
            else:
                self.p2_hp = max(0, self.p2_hp - final_dmg)
            
            return
        
        # Урон без защиты
        base_dmg = random.randint(a_eq["min_dmg"], a_eq["max_dmg"])
        base_dmg = int(base_dmg * skill.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_m = BODY_PARTS.get(target_part, {}).get("multiplier", 1.0)
        base_dmg = int(base_dmg * body_m)
        
        # Элементальный бонус
        if a_eq.get("element") and d_eq.get("element"):
            if ELEMENTS.get(a_eq["element"], {}).get("strong") == d_eq["element"]:
                base_dmg = int(base_dmg * 1.5)
                self._log_both("💥 СУПЕРЭФФЕКТИВНО!")
            elif ELEMENTS.get(a_eq["element"], {}).get("weak") == d_eq["element"]:
                base_dmg = int(base_dmg * 0.7)
                self._log_both("🔻 Неэффективно...")
        
        # Эффекты зачарований
        for eff, val in a_eq.get("enchant_effects", {}).items():
            if eff == "fire_damage":
                base_dmg += val
            elif eff == "damage_boost":
                base_dmg = int(base_dmg * (1 + val / 100))
        
        # Нанесение урона
        if defender == 1:
            self.p1_hp = max(0, self.p1_hp - base_dmg)
        else:
            self.p2_hp = max(0, self.p2_hp - base_dmg)
        
        self._log_both(f"⚔ {self.get_player_name(attacker)} [{skill['name']}] → {BODY_PARTS[target_part]['name']} {self.get_player_name(defender)}: <b>-{base_dmg} HP</b>")
        
        # Вампиризм
        if "life_steal" in skill:
            heal = int(base_dmg * skill["life_steal"])
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self._log_both(f"💚 Вампиризм +{heal} HP")
        
        # Кулдауны
        if skill.get("cooldown", 0) > 0:
            if attacker == 1:
                self.p1_cooldowns[skill_id] = skill["cooldown"]
            else:
                self.p2_cooldowns[skill_id] = skill["cooldown"]
    
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
        log = self.log_p1 if pn == 1 else self.log_p2
        
        def bar(cur, mx, icon):
            pct = cur / mx * 100 if mx > 0 else 0
            f = int(pct / 10)
            e = 10 - f
            color = "🟢" if pct > 50 else "🟡" if pct > 25 else "🔴"
            return f"{icon} {color}[{'█'*f}{'░'*e}] {cur}/{mx}"
        
        text = f"""
<b>⚔ ДУЭЛЬ #{self.battle_id}</b>
━━━━━━━━━━━━━━━━━━━━
🏟 {self._arena_name()} | Ход: <b>#{self.turn}</b> | Ставка: <b>{self.bet}💰</b>

<b>Вы ({self.get_player_name(pn)})</b>
❤ {bar(self.p1_hp if pn == 1 else self.p2_hp, self.p1_max_hp if pn == 1 else self.p2_max_hp, '❤')}
💎 MP: {self.p1_mp if pn == 1 else self.p2_mp}/{self.p1_max_mp if pn == 1 else self.p2_max_mp}
🛡 Защита: {BODY_PARTS.get(self.p1_defend if pn == 1 else self.p2_defend, {}).get('name', 'Не выбрана') if (self.p1_defend if pn == 1 else self.p2_defend) else 'Не выбрана'}

<b>Противник ({self.get_player_name(3-pn)})</b>
❤ {bar(self.p2_hp if pn == 1 else self.p1_hp, self.p2_max_hp if pn == 1 else self.p1_max_hp, '❤')}
━━━━━━━━━━━━━━━━━━━━
"""
        
        if phase == "defend_select":
            text += "\n🛡 <b>Выберите часть тела для защиты:</b>"
        elif phase == "attack_select":
            text += "\n🎯 <b>Выберите цель и навык атаки:</b>"
        elif phase == "done":
            text += "\n⏳ <b>Ожидание хода противника...</b>"
        
        if log:
            text += f"\n\n<i>{log[-1][:100]}</i>"
        
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

🎯 <b>СИСТЕМА:</b>
• Броня СНИЖАЕТ урон, а не даёт HP
• Навыки с кулдаунами (чем сильнее — тем дольше)
• Очерёдность: защита → атака → ждать
• Противник не видит вашу защиту!
• Сдаться = поражение

💰 Старт: <b>500 монет</b>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль (бот)", callback_data="quick_duel"),
        types.InlineKeyboardButton("🔍 Найти соперника", callback_data="find_opponent"),
        types.InlineKeyboardButton("🏆 Рейтинговая (100💰)", callback_data="ranked_duel"),
        types.InlineKeyboardButton("💀 Хардкор (500+💰)", callback_data="hardcore_duel"),
        types.InlineKeyboardButton("🎯 Спарринг (0💰)", callback_data="sparring_duel")
    )
    
    text = """
<b>⚔️ ДУЭЛИ</b>

🛡 Защита → 🎯 Атака → ⏳ Ждать
Броня снижает урон!
Навыки имеют кулдаун!
"""
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="hero_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="hero_inventory"),
        types.InlineKeyboardButton("👁 Экипировка", callback_data="hero_equipped"),
        types.InlineKeyboardButton("🏅 Достижения", callback_data="hero_achievements"),
        types.InlineKeyboardButton("✨ Зачарования", callback_data="hero_enchantments"),
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
        types.InlineKeyboardButton("🐉 Рейд-босс", callback_data="world_raid"),
        types.InlineKeyboardButton("🛡 Кланы", callback_data="world_clans"),
        types.InlineKeyboardButton("🏟 Турниры", callback_data="world_tournaments"),
        types.InlineKeyboardButton("🌍 Ивенты", callback_data="world_events"),
        types.InlineKeyboardButton("📊 Топ", callback_data="world_top")
    )
    bot.send_message(message.chat.id, "<b>🌍 МИР</b>", reply_markup=markup)

# ==================== ДУЭЛИ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["quick_duel", "find_opponent", "ranked_duel", "hardcore_duel", "sparring_duel"])
def duel_type_handler(call):
    dt = call.data
    
    if dt == "quick_duel":
        show_quick_duel_menu(call)
    elif dt == "find_opponent":
        start_matchmaking(call, "quick", 50)
    elif dt == "ranked_duel":
        start_matchmaking(call, "ranked", 100)
    elif dt == "hardcore_duel":
        show_hardcore_menu(call)
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
        f"<b>⚡ БЫСТРАЯ ДУЭЛЬ (БОТ)</b>\n\n💰 Баланс: <b>{player.data['money']}💰</b>",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

def show_hardcore_menu(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    for bet in [500, 1000, 2000, 5000]:
        markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"hduel_{bet}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
    
    bot.edit_message_text(
        f"<b>💀 ХАРДКОРНАЯ ДУЭЛЬ</b>\n\n💰 Баланс: <b>{player.data['money']}💰</b>",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

def start_matchmaking(call, duel_type, bet):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    queue_key = f"queue_{duel_type}"
    queue = matchmaking_queue.get(queue_key, [])
    
    # Убираем себя
    queue = [q for q in queue if q["user_id"] != user_id]
    
    if queue:
        opponent = queue.pop(0)
        matchmaking_queue[queue_key] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        # Начинаем дуэль
        duel = DuelInstance(opponent["user_id"], user_id, duel_type, bet)
        active_duels[user_id] = duel
        active_duels[opponent["user_id"]] = duel
        
        # Уведомляем обоих
        bot.edit_message_text("⚔ Соперник найден! Дуэль начинается!", call.message.chat.id, call.message.message_id)
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        
        # Отправляем противнику
        try:
            bot.send_message(int(opponent["user_id"]), "⚔ Дуэль начинается! Выберите защиту:")
            # Здесь нужно показать интерфейс и противнику
        except:
            pass
    else:
        queue.append({"user_id": user_id, "type": duel_type, "bet": bet})
        matchmaking_queue[queue_key] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        # Таймер на бота
        threading.Timer(5.0, start_bot_duel, args=[call.message.chat.id, call.message.message_id, user_id, duel_type, bet]).start()
        
        bot.edit_message_text("🔍 Поиск соперника... (5 сек)", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_duels")
def back_to_duels(call):
    duel_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def quick_duel_start(call):
    user_id = str(call.from_user.id)
    bet = int(call.data.split("_")[1])
    start_bot_duel(call.message.chat.id, call.message.message_id, user_id, "quick", bet)

@bot.callback_query_handler(func=lambda call: call.data.startswith("hduel_"))
def hardcore_duel_start(call):
    user_id = str(call.from_user.id)
    bet = int(call.data.split("_")[1])
    start_bot_duel(call.message.chat.id, call.message.message_id, user_id, "hardcore", bet)

def start_bot_duel(chat_id, message_id, user_id, duel_type="quick", bet=0):
    if user_id in active_duels:
        return
    
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.edit_message_text(f"❌ Недостаточно монет! Нужно {bet}💰", chat_id, message_id)
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
        "hp": 200, "max_hp": 200, "mana": 50, "max_mana": 50,
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
    active_duels[user_id] = duel
    
    # Бот выбирает защиту
    bot_def = random.choice(list(BODY_PARTS.keys()))
    duel.set_defend(2, bot_def)
    
    # Бот выбирает атаку
    bot_skills = duel.get_available_skills(2)
    if bot_skills:
        # Выбираем навык с умом
        available_tiers = {}
        for sid in bot_skills:
            skill = SKILLS_DB.get(sid, {})
            tier = skill.get("tier", 1)
            if tier not in available_tiers:
                available_tiers[tier] = []
            available_tiers[tier].append(sid)
        
        # 60% шанс использовать слабый, 25% средний, 15% сильный
        roll = random.random()
        if roll < 0.6 and 1 in available_tiers:
            bot_skill = random.choice(available_tiers[1])
        elif roll < 0.85 and 2 in available_tiers:
            bot_skill = random.choice(available_tiers[2])
        elif 3 in available_tiers or 4 in available_tiers or 5 in available_tiers:
            higher = []
            for t in [3, 4, 5]:
                if t in available_tiers:
                    higher.extend(available_tiers[t])
            bot_skill = random.choice(higher) if higher else random.choice(bot_skills)
        else:
            bot_skill = random.choice(bot_skills)
        
        duel.execute_attack(2, bot_skill, random.choice(list(BODY_PARTS.keys())))
    
    bot.edit_message_text(f"⚔ Бой с ботом Lv.{bot_level}!", chat_id, message_id)
    show_duel_interface(chat_id, message_id, duel, user_id)

def show_duel_interface(chat_id, message_id, duel, user_id):
    """Показать интерфейс дуэли"""
    if not duel.active:
        finish_duel(chat_id, message_id, duel, user_id)
        return
    
    state_text = duel.get_state_text(user_id)
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    phase = duel.p1_phase if pn == 1 else duel.p2_phase
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if phase == "defend_select":
        for part, data in BODY_PARTS.items():
            def_bonus = 0
            eq = duel.p1_eq if pn == 1 else duel.p2_eq
            if part == "head":
                def_bonus = eq["head_def"]
            elif part == "body":
                def_bonus = eq["body_def"]
            elif part == "legs":
                def_bonus = eq["legs_def"]
            
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']} (DEF:{def_bonus})",
                callback_data=f"duel_defend_{part}"
            ))
    
    elif phase == "attack_select":
        # Выбор цели
        markup.add(types.InlineKeyboardButton("🎯 Голова", callback_data="duel_target_head"))
        markup.add(types.InlineKeyboardButton("🎯 Тело", callback_data="duel_target_body"))
        markup.add(types.InlineKeyboardButton("🎯 Ноги", callback_data="duel_target_legs"))
    
    elif phase == "done":
        markup.add(types.InlineKeyboardButton("⏳ Ожидание...", callback_data="duel_wait"))
    
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="duel_refresh"))
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="duel_surrender"))
    
    try:
        bot.edit_message_text(state_text[:4000], chat_id, message_id, reply_markup=markup)
    except:
        pass

# Хранение временных целей
target_selection = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_target_"))
def duel_target_selected(call):
    user_id = str(call.from_user.id)
    part = call.data.split("_", 2)[2]
    
    duel = active_duels.get(user_id)
    if not duel or not duel.active:
        return
    
    target_selection[user_id] = part
    
    pn = 1 if user_id == duel.p1_id else 2
    skills = duel.get_available_skills(pn)
    
    state_text = duel.get_state_text(user_id) + f"\n🎯 Цель: <b>{BODY_PARTS[part]['name']}</b>\n<b>Выберите навык:</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for sid in skills[:10]:
        skill = SKILLS_DB.get(sid, {})
        name = skill.get("name", sid)
        mana = skill.get("mana_cost", 0)
        cd = skill.get("cooldown", 0)
        dmg = skill.get("damage_mult", 1.0)
        
        cd_text = f" [CD:{cd}]" if cd > 0 else ""
        markup.add(types.InlineKeyboardButton(
            f"{name} x{dmg} [{mana}MP]{cd_text}",
            callback_data=f"duel_skill_{sid}"
        ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="duel_back_target"))
    
    try:
        bot.edit_message_text(state_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
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
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    target = target_selection.get(user_id, "body")
    pn = 1 if user_id == duel.p1_id else 2
    
    duel.execute_attack(pn, skill_id, target)
    
    bot.answer_callback_query(call.id, "⚔ Атака!")
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_"))
def duel_actions(call):
    user_id = str(call.from_user.id)
    action = call.data.split("_", 1)[1]
    
    if action == "refresh":
        duel = active_duels.get(user_id)
        if duel and duel.active:
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
            bot.answer_callback_query(call.id, "✅")
        else:
            bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
    
    elif action == "wait":
        duel = active_duels.get(user_id)
        if duel and duel.active:
            pn = 1 if user_id == duel.p1_id else 2
            other_pn = 3 - pn
            other_phase = duel.p2_phase if pn == 1 else duel.p1_phase
            
            # Бот ходит автоматически
            if str(duel.p2_id).startswith("bot_") and other_pn == 2:
                if other_phase == "defend_select":
                    duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
                if other_phase == "attack_select":
                    skills = duel.get_available_skills(2)
                    if skills:
                        duel.execute_attack(2, random.choice(skills), random.choice(list(BODY_PARTS.keys())))
            
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
            bot.answer_callback_query(call.id, "✅")
    
    elif action == "surrender":
        duel = active_duels.get(user_id)
        if duel and duel.active:
            duel.active = False
            duel.winner = 2 if user_id == duel.p1_id else 1
            finish_duel(call.message.chat.id, call.message.message_id, duel, user_id)
            bot.answer_callback_query(call.id, "🏳 Вы сдались!")
    
    elif action.startswith("defend_"):
        part = action.split("_")[1]
        duel = active_duels.get(user_id)
        if duel and duel.active:
            pn = 1 if user_id == duel.p1_id else 2
            duel.set_defend(pn, part)
            bot.answer_callback_query(call.id, f"🛡 Защита: {BODY_PARTS[part]['name']}")
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

def finish_duel(chat_id, message_id, duel, user_id=None):
    """Завершение дуэли"""
    # Очистка
    for uid in [duel.p1_id, duel.p2_id]:
        if uid in active_duels and active_duels[uid].battle_id == duel.battle_id:
            del active_duels[uid]
    
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") and uid in users:
            del users[uid]
    save_json(DATA_FILES['users'], users)
    
    if duel.winner == 0:
        result = f"<b>🤝 НИЧЬЯ!</b>\nХодов: {duel.turn}"
        bot.edit_message_text(result, chat_id, message_id)
        return
    
    winner_id = duel.p1_id if duel.winner == 1 else duel.p2_id
    loser_id = duel.p2_id if duel.winner == 1 else duel.p1_id
    
    winner = Player(winner_id)
    loser = Player(loser_id)
    
    if duel.bet > 0 and not winner_id.startswith("bot_"):
        reward = duel.bet * 2
        winner.data["money"] += reward
    
    if not winner_id.startswith("bot_"):
        winner.data["wins"] += 1
        winner.data["win_streak"] += 1
        winner.data["total_duels"] += 1
        winner.data["pvp_rating"] += random.randint(20, 35)
        if winner.data["win_streak"] > winner.data["best_streak"]:
            winner.data["best_streak"] = winner.data["win_streak"]
        exp_w = duel.turn * 10 + duel.bet // 2
        winner.data["exp"] += exp_w
        winner.data["total_exp"] += exp_w
        old_w = winner.data["level"]
        check_level_up(winner)
        winner.save()
    
    if not loser_id.startswith("bot_"):
        loser.data["losses"] += 1
        loser.data["win_streak"] = 0
        loser.data["total_duels"] += 1
        loser.data["pvp_rating"] = max(0, loser.data["pvp_rating"] - random.randint(10, 25))
        exp_l = duel.turn * 5 + duel.bet // 5
        loser.data["exp"] += exp_l
        loser.data["total_exp"] += exp_l
        check_level_up(loser)
        loser.save()
    
    result_text = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

👑 <b>{duel.get_player_name(duel.winner)}</b> побеждает!
💀 <b>{duel.get_player_name(3 - duel.winner)}</b> проигрывает

💰 Ставка: <b>{duel.bet}💰</b>
📊 Ходов: <b>{duel.turn}</b>
"""
    
    bot.edit_message_text(result_text, chat_id, message_id)
    
    # Отправляем результат обоим игрокам
    other_id = duel.p2_id if user_id and str(user_id) == duel.p1_id else duel.p1_id
    if other_id and not other_id.startswith("bot_"):
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
    bot.edit_message_text(f"<b>🛒 МАГАЗИН</b>\n💰 <b>{player.data['money']}💰</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

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
            if "speed" in item:
                s += f" | Скорость: +{item['speed']}"
            if "hp_bonus" in item:
                s += f" | HP: +{item['hp_bonus']}"
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

@bot.callback_query_handler(func=lambda call: call.data in ["trade_market", "trade_sell", "trade_my_lots", "back_to_trade"])
def trade_handlers(call):
    if call.data == "trade_market":
        if not market_listings:
            bot.edit_message_text("📦 Рынок пуст\n/sell [номер] [цена]", call.message.chat.id, call.message.message_id)
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
    
    trade_handlers(call)

# ==================== ГЕРОЙ ====================
@bot.callback_query_handler(func=lambda call: call.data == "hero_stats")
def hero_stats(call):
    user_id = call.from_user.id
    player = Player(user_id)
    eq = player.get_equipment_stats()
    d = player.data
    
    wr = (d["wins"] / d["total_duels"] * 100) if d["total_duels"] > 0 else 0
    
    text = f"""
<b>📊 СТАТИСТИКА</b>

<b>{d['first_name']}</b> | {d['title']}
⭐ Ур.{d['level']} | 📊 {d['pvp_rating']}
💰 {d['money']}💰

⚔ Урон: {eq['min_dmg']}-{eq['max_dmg']}
🛡 Защита: Г:{eq['head_def']} Т:{eq['body_def']} Н:{eq['legs_def']}
💨 Скорость: {eq['speed']}

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
    if not item:
        bot.answer_callback_query(call.id, "❌ Не найден!")
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
    player.data.setdefault("enchantments", {})[ik] = {"name": ench["name"], "effect": ench["effect"], "value": ench["value"]}
    player.save()
    
    bot.answer_callback_query(call.id, f"✨ {ench['name']}!")

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
    
    if player.data["hp"] >= player.data["max_hp"] and "heal" in item:
        bot.answer_callback_query(call.id, "❌ Полное HP!")
        return
    
    if "heal" in item:
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + item["heal"])
    if "mana_restore" in item:
        player.data["mana"] = min(player.data["max_mana"], player.data["mana"] + item["mana_restore"])
    
    player.data["inventory"].remove(ik)
    player.save()
    
    bot.answer_callback_query(call.id, "✅ Использовано!")

@bot.callback_query_handler(func=lambda call: call.data in ["hero_equipped", "hero_achievements", "hero_enchantments", "hero_history", "hero_heal", "hero_settings", "back_to_hero"])
def hero_handlers(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "hero_equipped":
        eq = player.data["equipment"]
        text = "<b>👁 ЭКИПИРОВКА</b>\n\n"
        slots = {"weapon": "⚔ Оружие", "head": "👤 Голова", "body": "🦾 Тело", "legs": "🦿 Ноги"}
        
        for slot, sn in slots.items():
            ik = eq.get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                if item:
                    ench = player.data.get("enchantments", {}).get(ik, {})
                    ench_text = f" ✨{ench.get('name', '')}" if ench else ""
                    text += f"{sn}: <b>{item['name']}</b>{ench_text}\n"
                else:
                    text += f"{sn}: ❌ Удалён\n"
            else:
                text += f"{sn}: ❌ Пусто\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔴 Снять всё", callback_data="unequip_all"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_achievements":
        ach = [("first_blood", "🩸 Первая кровь"), ("warrior", "⚔ Воин"), ("legend", "👑 Легенда")]
        text = "<b>🏅 ДОСТИЖЕНИЯ</b>\n\n"
        for aid, name in ach:
            done = aid in player.data["achievements"]
            text += f"{'✅' if done else '🔒'} {name}\n"
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
                text += f"📦 {item['name']}: <b>{e['name']}</b>\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_history":
        hist = player.data.get("battle_history", [])
        if not hist:
            bot.edit_message_text("📋 Пусто", call.message.chat.id, call.message.message_id)
            return
        text = "<b>📋 ПОСЛЕДНИЕ 10</b>\n\n"
        for b in hist[-10:]:
            icon = "🏆" if b.get("result") == "win" else "💀"
            text += f"{icon} vs {b.get('opponent', 'Нет')}\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
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
        bot.edit_message_text(f"💊 {potion['name']}\n❤ {player.data['hp']}/{player.data['max_hp']}", call.message.chat.id, call.message.message_id)
    
    elif call.data == "hero_settings":
        s = player.data.get("settings", {})
        text = f"🔔 Уведомления: {'✅' if s.get('notifications', True) else '❌'}\n⚔ Запросы: {'✅' if s.get('duel_requests', True) else '❌'}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔔 Уведомления", callback_data="set_notify"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "back_to_hero":
        hero_section(call.message)

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

@bot.callback_query_handler(func=lambda call: call.data == "set_notify")
def set_notify(call):
    user_id = call.from_user.id
    player = Player(user_id)
    player.data["settings"]["notifications"] = not player.data["settings"].get("notifications", True)
    player.save()
    bot.answer_callback_query(call.id, "✅ Изменено!")
    hero_handlers(call)

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

Пошаговые бои с боссами!
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
    
    # Создаём первого босса
    boss_names = [["Волк-разведчик", "Вожак стаи", "Альфа-волк"],
                  ["Малый паук", "Паук-охотник", "Королева пауков"],
                  ["Скелет", "Некромант", "Лич"],
                  ["Драконид", "Дрейк", "Древний дракон"],
                  ["Бес", "Демон", "Владыка бездны"]]
    
    dungeon_progress[str(user_id)] = {"dungeon_level": dl, "current_boss": 0, "bosses": boss_names[dl-1]}
    save_json(DATA_FILES['dungeons'], dungeon_progress)
    
    start_dungeon_boss(call, user_id)

def start_dungeon_boss(call, user_id):
    """Начать бой с текущим боссом"""
    dg = dungeon_progress.get(str(user_id), {})
    boss_idx = dg.get("current_boss", 0)
    
    if boss_idx >= 3:
        # Все боссы побеждены
        player = Player(user_id)
        reward = random.randint(100, 500) * dg["dungeon_level"] * player.data["level"]
        exp = 100 * dg["dungeon_level"] * player.data["level"]
        
        player.data["money"] += reward
        player.data["exp"] += exp
        player.data["total_exp"] += exp
        player.data["last_dungeon"] = datetime.now().isoformat()
        player.data["dungeons_completed"] = player.data.get("dungeons_completed", 0) + 1
        
        check_level_up(player)
        player.save()
        
        del dungeon_progress[str(user_id)]
        save_json(DATA_FILES['dungeons'], dungeon_progress)
        
        bot.edit_message_text(f"🏰 Данж пройден!\n💰 +{reward}\n✨ +{exp}", call.message.chat.id, call.message.message_id)
        return
    
    boss_name = dg["bosses"][boss_idx]
    boss_level = dg["dungeon_level"] * 2 + boss_idx * 3
    
    # Создание босса
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
        "hp": 200, "max_hp": 200, "mana": 50, "max_mana": 50,
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
    
    duel = DuelInstance(user_id, boss_id, "dungeon", 0)
    active_duels[str(user_id)] = duel
    
    # Босс выбирает защиту и атаку
    duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
    boss_skills = duel.get_available_skills(2)
    if boss_skills:
        duel.execute_attack(2, random.choice(boss_skills), random.choice(list(BODY_PARTS.keys())))
    
    bot.edit_message_text(f"⚔ Босс {boss_idx+1}/3: <b>{boss_name}</b>!", call.message.chat.id, call.message.message_id)
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

# Расширенный finish_duel для данжей
original_finish = finish_duel

def finish_duel_extended(chat_id, message_id, duel, user_id=None):
    if duel.duel_type == "dungeon":
        player_id = duel.p1_id if not duel.p1_id.startswith("boss_") else duel.p2_id
        
        if duel.winner == 1 and not duel.p1_id.startswith("boss_"):
            # Игрок победил босса
            dg = dungeon_progress.get(str(player_id), {})
            dg["current_boss"] = dg.get("current_boss", 0) + 1
            dungeon_progress[str(player_id)] = dg
            save_json(DATA_FILES['dungeons'], dungeon_progress)
            
            # Очистка
            for uid in list(active_duels.keys()):
                if active_duels[uid].battle_id == duel.battle_id:
                    del active_duels[uid]
            for uid in [duel.p1_id, duel.p2_id]:
                if uid.startswith("boss_") and uid in users:
                    del users[uid]
            save_json(DATA_FILES['users'], users)
            
            boss_idx = dg.get("current_boss", 1)
            if boss_idx >= 3:
                # Все боссы побеждены
                player = Player(player_id)
                dl = dg["dungeon_level"]
                reward = random.randint(100, 500) * dl * player.data["level"]
                exp = 100 * dl * player.data["level"]
                
                player.data["money"] += reward
                player.data["exp"] += exp
                player.data["total_exp"] += exp
                player.data["last_dungeon"] = datetime.now().isoformat()
                player.data["dungeons_completed"] = player.data.get("dungeons_completed", 0) + 1
                
                if random.random() < 0.3:
                    possible = [k for k, v in items.items() if v.get("level_req", 1) <= player.data["level"]]
                    if possible:
                        ik = random.choice(possible)
                        player.data["inventory"].append(ik)
                
                check_level_up(player)
                player.save()
                
                if str(player_id) in dungeon_progress:
                    del dungeon_progress[str(player_id)]
                save_json(DATA_FILES['dungeons'], dungeon_progress)
                
                bot.edit_message_text(f"🏰 Данж пройден!\n💰 +{reward}\n✨ +{exp}", chat_id, message_id)
            else:
                # Следующий босс
                fake_call = types.CallbackQuery(id="0", from_user=types.User(id=int(player_id), is_bot=False, first_name=""), message=types.Message(id=message_id, chat=types.Chat(id=chat_id)), data="")
                start_dungeon_boss(fake_call, player_id)
        else:
            # Проигрыш боссу
            bot.edit_message_text(f"💀 Вы проиграли боссу!\nПопробуйте снова через час.", chat_id, message_id)
            if str(player_id) in dungeon_progress:
                del dungeon_progress[str(player_id)]
            save_json(DATA_FILES['dungeons'], dungeon_progress)
    else:
        original_finish(chat_id, message_id, duel, user_id)

finish_duel = finish_duel_extended

# ==================== РЕЙД-БОСС ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_raid")
def world_raid(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data["level"] < 10:
        bot.answer_callback_query(call.id, "❌ Нужен 10 уровень!")
        return
    
    # Создание рейд-босса с 1000000 HP
    boss_id = f"raid_{random.randint(100000, 999999)}"
    
    users[boss_id] = {
        "username": "RaidBoss", "first_name": "🐉 МИРОВОЙ БОСС",
        "money": 0, "level": 100, "exp": 0, "total_exp": 0,
        "hp": 1000000, "max_hp": 1000000, "mana": 999, "max_mana": 999,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000,
        "inventory": [], "equipment": {"weapon": "death_scythe", "head": "dragon_helmet", "body": "phoenix_armor", "legs": "hermes_boots"}, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Мировой босс", "titles_collected": [],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    duel = DuelInstance(user_id, boss_id, "raid", 0)
    # Переопределяем HP босса
    duel.p2_hp = 1000000
    duel.p2_max_hp = 1000000
    active_duels[str(user_id)] = duel
    
    duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
    boss_skills = duel.get_available_skills(2)
    if boss_skills:
        duel.execute_attack(2, random.choice(boss_skills), random.choice(list(BODY_PARTS.keys())))
    
    bot.edit_message_text("🐉 Битва с МИРОВЫМ БОССОМ!\n❤ 1,000,000 HP\nНаграда зависит от нанесённого урона!", call.message.chat.id, call.message.message_id)
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

# ==================== КЛАНЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_clans")
def world_clans(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data.get("clan"):
        clan = clans.get(player.data["clan"], {})
        text = f"<b>🛡 {player.data['clan']}</b>\n👥 {len(clan.get('members', []))} уч.\n💰 {clan.get('treasury', 0)}💰"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("👥 Участники", callback_data="clan_members"))
        markup.add(types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave"))
    else:
        text = "<b>🛡 КЛАНЫ</b>\n/createclan [имя]\n/joinclan [имя]\n💰 5000💰"
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

# ==================== ТУРНИРЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_tournaments")
def world_tournaments(call):
    if not tournaments.get("active"):
        tournaments["active"] = {
            "name": "Еженедельный турнир",
            "participants": [],
            "prize_pool": 5000,
            "status": "registration",
            "rounds": [],
            "current_round": 0
        }
        save_json(DATA_FILES['tournaments'], tournaments)
    
    tour = tournaments["active"]
    text = f"<b>🏟 ТУРНИР</b>\n<b>{tour['name']}</b>\nУчастников: {len(tour.get('participants', []))}/8\nПриз: <b>{tour.get('prize_pool', 0)}💰</b>\nВзнос: 500💰"
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
    if len(participants) >= 8:
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

@bot.callback_query_handler(func=lambda call: call.data == "tour_list")
def tour_list(call):
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
def world_events(call):
    current = events.get("current", {})
    if not current or datetime.fromisoformat(current.get("expires", "2000-01-01")) < datetime.now():
        new_event = {
            "name": random.choice(["🌋 Извержение", "❄ Шторм", "⚡ Гроза", "🌑 Затмение", "✨ Звездопад"]),
            "ench_reward": random.choice(ENCHANT_EFFECTS),
            "ench_chance": random.randint(15, 35),
            "progress": {},
            "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        events["current"] = new_event
        save_json(DATA_FILES['events'], events)
    
    ev = events["current"]
    uid = str(call.from_user.id)
    prog = ev.get("progress", {}).get(uid, 0)
    time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
    mins = max(0, time_left.seconds // 60)
    
    text = f"""
<b>🌍 ИВЕНТ</b>

<b>{ev['name']}</b>
✨ Награда: <b>{ev['ench_reward']['name']}</b>
📊 Ваш прогресс: {prog}/3 дуэлей
⏰ {mins} мин.

Участвуйте в дуэлях для шанса!
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
        player.data["max_hp"] += 15
        player.data["max_mana"] += 8
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

# ==================== АДМИН-ПАНЕЛЬ ====================
def find_user_by_username(username):
    """Поиск пользователя по username"""
    username = username.replace('@', '').lower()
    for uid, data in users.items():
        if data.get("username", "").lower() == username:
            return uid
    return None

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
        types.InlineKeyboardButton("✅ Разбан", callback_data="admin_unban"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🔄 Сброс", callback_data="admin_reset"),
        types.InlineKeyboardButton("👁 Инфо", callback_data="admin_info"),
        types.InlineKeyboardButton("➕ Создать турнир", callback_data="admin_tournament"),
        types.InlineKeyboardButton("🌍 Создать ивент", callback_data="admin_event"),
        types.InlineKeyboardButton("💎 Создать лимитку", callback_data="admin_limited")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>\n\nВсе команды через @username", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_handlers(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    action = call.data.split("_")[1]
    
    if action == "stats":
        total = len(users)
        total_money = sum(u.get("money", 0) for u in users.values())
        total_duels = sum(u.get("total_duels", 0) for u in users.values())
        text = f"<b>📊 СТАТИСТИКА</b>\n👥 {total}\n💰 {total_money}\n⚔ {total_duels}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    
    elif action == "givemoney":
        bot.send_message(call.message.chat.id, "💰 /givemoney @username [сумма]")
    
    elif action == "giveitem":
        bot.send_message(call.message.chat.id, "🎁 /giveitem @username [item_key]")
    
    elif action == "ban":
        bot.send_message(call.message.chat.id, "⛔ /ban @username [причина]")
    
    elif action == "unban":
        bot.send_message(call.message.chat.id, "✅ /unban @username")
    
    elif action == "broadcast":
        bot.send_message(call.message.chat.id, "📢 /broadcast [текст]")
    
    elif action == "reset":
        bot.send_message(call.message.chat.id, "🔄 /resetdaily @username")
    
    elif action == "info":
        bot.send_message(call.message.chat.id, "👁 /userinfo @username")
    
    elif action == "tournament":
        bot.send_message(call.message.chat.id, "🏟 /createtournament [название] [приз]")
    
    elif action == "event":
        bot.send_message(call.message.chat.id, "🌍 /createevent [название] [награда]")
    
    elif action == "limited":
        bot.send_message(call.message.chat.id, "💎 /createlimited [item_key] [total] [price]")

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'broadcast', 'resetdaily', 'userinfo', 'createtournament', 'createevent', 'createlimited'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
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
                bot.send_message(message.chat.id, f"❌ @{username} не найден")
        
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
                bot.send_message(message.chat.id, f"❌ @{username} не найден")
        
        elif cmd == "ban":
            username = parts[1].replace('@', '')
            reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение"
            uid = find_user_by_username(username)
            if uid:
                banned_users[uid] = {"reason": reason, "banned_at": datetime.now().isoformat()}
                save_json(DATA_FILES['bans'], banned_users)
                bot.send_message(message.chat.id, f"⛔ @{username} забанен!")
            else:
                bot.send_message(message.chat.id, f"❌ @{username} не найден")
        
        elif cmd == "unban":
            username = parts[1].replace('@', '')
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
            username = parts[1].replace('@', '')
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
            username = parts[1].replace('@', '')
            uid = find_user_by_username(username)
            if uid:
                p = Player(uid)
                d = p.data
                text = f"<b>👤 @{username}</b>\nИмя: {d['first_name']}\nУр.: {d['level']}\n💰 {d['money']}\nРейтинг: {d['pvp_rating']}\nКлан: {d.get('clan', 'Нет')}"
                bot.send_message(message.chat.id, text)
            else:
                bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "createtournament":
            name = " ".join(parts[1:-1]) if len(parts) > 2 else parts[1]
            prize = int(parts[-1]) if parts[-1].isdigit() else 5000
            tournaments["active"] = {
                "name": name, "participants": [], "prize_pool": prize,
                "status": "registration", "rounds": [], "current_round": 0
            }
            save_json(DATA_FILES['tournaments'], tournaments)
            bot.send_message(message.chat.id, f"✅ Турнир <b>{name}</b> создан! Приз: {prize}💰")
        
        elif cmd == "createevent":
            name = " ".join(parts[1:-1]) if len(parts) > 2 else parts[1]
            events["current"] = {
                "name": name, "ench_reward": random.choice(ENCHANT_EFFECTS),
                "ench_chance": 25, "progress": {},
                "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
            }
            save_json(DATA_FILES['events'], events)
            bot.send_message(message.chat.id, f"✅ Ивент <b>{name}</b> создан!")
        
        elif cmd == "createlimited":
            ik = parts[1]
            total = int(parts[2]) if len(parts) > 2 else 5
            price = int(parts[3]) if len(parts) > 3 else 10000
            if ik in items:
                item = items[ik]
                limited_items[ik] = {
                    "name": item.get("name", ik), "total": total, "remaining": total,
                    "price": price, "type": item.get("type"), "slot": item.get("slot"),
                    "rarity": "divine"
                }
                if "damage" in item:
                    limited_items[ik]["damage"] = item["damage"]
                if "defense" in item:
                    limited_items[ik]["defense"] = item["defense"]
                if "skills" in item:
                    limited_items[ik]["skills"] = item["skills"]
                
                save_json(DATA_FILES['limited'], limited_items)
                bot.send_message(message.chat.id, f"✅ Лимитка {ik} создана!")
            else:
                bot.send_message(message.chat.id, "❌ Предмет не найден")
    
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
    print("✅ Броня СНИЖАЕТ урон")
    print("✅ Навыки с кулдаунами")
    print("✅ Данжи: 3 босса")
    print("✅ Рейд-босс 1M HP")
    print("✅ Турниры: одиночное выбывание")
    print("✅ Админ через @username")
    print("✅ Кнопка Сдаться работает")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
