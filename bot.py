import telebot
from telebot import types
import json
import random
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict
import math
import re
import copy

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = '8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE'
ADMIN_ID = 5356400377
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ==================== КОНСТАНТЫ ====================
RARITY_COLORS = {
    "common": "⬜", "uncommon": "🟩", "rare": "🟦",
    "epic": "🟪", "legendary": "🟧", "mythic": "🟥",
    "divine": "💛", "apocalyptic": "🖤"
}

ELEMENTS = {
    "fire": {"name": "🔥 Огонь", "strong_against": "ice", "weak_against": "water"},
    "ice": {"name": "❄ Лёд", "strong_against": "nature", "weak_against": "fire"},
    "lightning": {"name": "⚡ Молния", "strong_against": "water", "weak_against": "earth"},
    "water": {"name": "🌊 Вода", "strong_against": "fire", "weak_against": "lightning"},
    "nature": {"name": "🌿 Природа", "strong_against": "earth", "weak_against": "ice"},
    "earth": {"name": "⛰ Земля", "strong_against": "lightning", "weak_against": "nature"},
    "light": {"name": "✨ Свет", "strong_against": "dark", "weak_against": "chaos"},
    "dark": {"name": "🌑 Тьма", "strong_against": "light", "weak_against": "light"},
    "chaos": {"name": "🌀 Хаос", "strong_against": "all", "weak_against": "all"}
}

SKILL_TYPES = ["attack", "defense", "heal", "buff", "debuff", "ultimate"]
STATUS_EFFECTS = ["burn", "freeze", "stun", "poison", "bleed", "curse", "bless", "shield", "berserk", "invisible"]

WEATHER_EFFECTS = {
    "clear": {"description": "☀ Ясно", "effect": None},
    "rain": {"description": "🌧 Дождь", "effect": "water_boost"},
    "storm": {"description": "⛈ Буря", "effect": "lightning_boost"},
    "fog": {"description": "🌫 Туман", "effect": "accuracy_down"},
    "eclipse": {"description": "🌑 Затмение", "effect": "dark_boost"},
    "blizzard": {"description": "❄ Метель", "effect": "ice_boost"},
    "heatwave": {"description": "🔥 Зной", "effect": "fire_boost"}
}

ARENA_TYPES = {
    "colosseum": {"name": "🏟 Колизей", "effect": "balanced"},
    "forest": {"name": "🌲 Лес", "effect": "nature_boost"},
    "volcano": {"name": "🌋 Вулкан", "effect": "fire_damage"},
    "tundra": {"name": "🏔 Тундра", "effect": "ice_boost"},
    "void": {"name": "🕳 Бездна", "effect": "random_effect"},
    "temple": {"name": "🏛 Храм", "effect": "heal_boost"},
    "graveyard": {"name": "💀 Кладбище", "effect": "dark_boost"},
    "arena": {"name": "⚔ Арена", "effect": "damage_boost"}
}

# ==================== ФАЙЛЫ ====================
DATA_FILES = {
    'users': 'users.json',
    'items': 'items.json',
    'limited': 'limited_items.json',
    'duels': 'active_duels.json',
    'clans': 'clans.json',
    'tournaments': 'tournaments.json',
    'market': 'market.json',
    'dungeons': 'dungeons.json',
    'events': 'events.json',
    'bans': 'bans.json'
}

def load_json(filename, default=None):
    if default is None: default = {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return default

def save_json(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error: {e}")

# ==================== ПРЕДМЕТЫ И ЭКИПИРОВКА ====================
WEAPONS = {
    "rusty_sword": {"name": "🗡 Ржавый меч", "damage": (3, 7), "price": 50, "type": "weapon", "rarity": "common", "level_req": 1, "element": None, "skills": ["slash"]},
    "hunters_bow": {"name": "🏹 Лук охотника", "damage": (5, 10), "price": 150, "type": "weapon", "rarity": "common", "level_req": 3, "element": "nature", "skills": ["power_shot"]},
    "flame_blade": {"name": "🔥 Пламенный клинок", "damage": (8, 15), "price": 400, "type": "weapon", "rarity": "uncommon", "level_req": 7, "element": "fire", "skills": ["flame_slash", "fireball"]},
    "frost_axe": {"name": "❄ Ледяной топор", "damage": (10, 18), "price": 700, "type": "weapon", "rarity": "uncommon", "level_req": 10, "element": "ice", "skills": ["ice_slash", "frost_nova"]},
    "storm_staff": {"name": "⚡ Посох бурь", "damage": (12, 22), "price": 1200, "type": "weapon", "rarity": "rare", "level_req": 14, "element": "lightning", "skills": ["thunder_strike", "chain_lightning"]},
    "tidal_blade": {"name": "🌊 Приливной клинок", "damage": (15, 25), "price": 2000, "type": "weapon", "rarity": "rare", "level_req": 18, "element": "water", "skills": ["wave_slash", "tsunami"]},
    "shadow_dagger": {"name": "🌑 Теневой кинжал", "damage": (18, 30), "price": 3500, "type": "weapon", "rarity": "epic", "level_req": 22, "element": "dark", "skills": ["shadow_strike", "assassinate", "vanish"]},
    "divine_spear": {"name": "✨ Божественное копьё", "damage": (22, 35), "price": 6000, "type": "weapon", "rarity": "legendary", "level_req": 28, "element": "light", "skills": ["holy_strike", "divine_judgment", "heal_light"]},
    "death_scythe": {"name": "💀 Коса смерти", "damage": (25, 45), "price": 10000, "type": "weapon", "rarity": "mythic", "level_req": 35, "element": "dark", "skills": ["reap", "death_curse", "soul_drain", "necromancy"]},
    "thunder_hammer": {"name": "⚡ Громовой молот", "damage": (20, 40), "price": 8000, "type": "weapon", "rarity": "legendary", "level_req": 32, "element": "lightning", "skills": ["thunder_clap", "hammer_smash", "electrocute"]},
    "chaos_blade": {"name": "🌀 Клинок хаоса", "damage": (30, 60), "price": 20000, "type": "weapon", "rarity": "mythic", "level_req": 45, "element": "chaos", "skills": ["chaos_slash", "reality_break", "entropy", "void_strike"]}
}

SHIELDS = {
    "wooden_shield": {"name": "🛡 Деревянный щит", "defense": 5, "block_chance": 10, "price": 100, "type": "shield", "rarity": "common", "level_req": 1, "skills": ["block"]},
    "iron_shield": {"name": "🛡 Железный щит", "defense": 10, "block_chance": 15, "price": 350, "type": "shield", "rarity": "uncommon", "level_req": 6, "skills": ["block", "shield_bash"]},
    "mirror_shield": {"name": "🪞 Зеркальный щит", "defense": 15, "block_chance": 20, "price": 900, "type": "shield", "rarity": "rare", "level_req": 12, "skills": ["block", "reflect_magic"]},
    "dragon_scale_shield": {"name": "🐉 Щит драконьей чешуи", "defense": 22, "block_chance": 25, "price": 2500, "type": "shield", "rarity": "epic", "level_req": 20, "skills": ["block", "dragon_breath", "scale_armor"]},
    "aegis_divine": {"name": "💫 Божественная эгида", "defense": 35, "block_chance": 35, "price": 8000, "type": "shield", "rarity": "legendary", "level_req": 30, "skills": ["block", "divine_protection", "holy_barrier"]},
    "void_barrier": {"name": "🕳 Барьер пустоты", "defense": 45, "block_chance": 40, "price": 15000, "type": "shield", "rarity": "mythic", "level_req": 38, "skills": ["block", "void_absorption", "black_hole"]}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "defense": 3, "hp_bonus": 15, "price": 80, "type": "armor", "rarity": "common", "level_req": 1, "skills": ["dodge"]},
    "chainmail": {"name": "⛓ Кольчуга", "defense": 8, "hp_bonus": 35, "price": 400, "type": "armor", "rarity": "uncommon", "level_req": 8, "skills": ["endure"]},
    "plate_armor": {"name": "🛡 Латный доспех", "defense": 15, "hp_bonus": 60, "price": 1200, "type": "armor", "rarity": "rare", "level_req": 15, "skills": ["fortify"]},
    "shadow_armor": {"name": "🌑 Теневая броня", "defense": 20, "hp_bonus": 80, "price": 3000, "type": "armor", "rarity": "epic", "level_req": 22, "skills": ["shadow_step", "evasion"]},
    "phoenix_armor": {"name": "🦅 Броня феникса", "defense": 30, "hp_bonus": 150, "price": 7000, "type": "armor", "rarity": "legendary", "level_req": 30, "skills": ["rebirth", "fire_heal"]},
    "titan_armor": {"name": "🏛 Броня титана", "defense": 45, "hp_bonus": 250, "price": 20000, "type": "armor", "rarity": "mythic", "level_req": 40, "skills": ["unstoppable", "titan_rage"]}
}

BOOTS = {
    "leather_boots": {"name": "👢 Кожаные сапоги", "speed": 5, "price": 150, "type": "boots", "rarity": "common", "level_req": 1, "skills": ["quick_step"]},
    "wind_boots": {"name": "🌪 Сапоги ветра", "speed": 12, "price": 800, "type": "boots", "rarity": "rare", "level_req": 12, "skills": ["wind_walk", "gust"]},
    "blink_boots": {"name": "✨ Сапоги телепортации", "speed": 20, "price": 3500, "type": "boots", "rarity": "epic", "level_req": 25, "skills": ["blink", "teleport_strike"]},
    "hermes_boots": {"name": "👟 Сандалии Гермеса", "speed": 35, "price": 10000, "type": "boots", "rarity": "legendary", "level_req": 35, "skills": ["god_speed", "time_warp"]}
}

ACCESSORIES = {
    "strength_ring": {"name": "💍 Кольцо силы", "price": 600, "type": "accessory", "rarity": "uncommon", "level_req": 5, "skills": ["power_surge"]},
    "crit_amulet": {"name": "📿 Амулет крита", "price": 1500, "type": "accessory", "rarity": "rare", "level_req": 15, "skills": ["deadly_strike"]},
    "lucky_charm": {"name": "🍀 Талисман удачи", "price": 2500, "type": "accessory", "rarity": "epic", "level_req": 20, "skills": ["lucky_break", "fortune"]},
    "berserker_ring": {"name": "💢 Кольцо берсерка", "price": 4000, "type": "accessory", "rarity": "epic", "level_req": 25, "skills": ["berserk", "blood_rage"]},
    "philosophers_stone": {"name": "🧿 Философский камень", "price": 12000, "type": "accessory", "rarity": "legendary", "level_req": 35, "skills": ["transmute", "elixir"]}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 30, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 75, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 150, "price": 350, "type": "potion", "rarity": "rare", "level_req": 15},
    "mana_potion": {"name": "💎 Зелье маны", "mana_restore": 50, "price": 60, "type": "potion", "rarity": "common", "level_req": 3},
    "berserk_potion": {"name": "💢 Зелье ярости", "price": 200, "type": "potion", "rarity": "rare", "level_req": 12, "effects": {"berserk": 3}},
    "invisibility_potion": {"name": "👻 Зелье невидимости", "price": 500, "type": "potion", "rarity": "epic", "level_req": 20, "effects": {"invisible": 2}}
}

LIMITED_ITEMS = {
    "thunderfury": {
        "name": "⚡ Ярость грома", "damage": (50, 80), "total": 3, "remaining": 3,
        "price": 50000, "type": "weapon", "rarity": "divine", "element": "lightning",
        "skills": ["thunder_gods_wrath", "storm_king", "lightning_apocalypse", "mjolnir_strike"]
    },
    "apocalypse": {
        "name": "🌋 Апокалипсис", "damage": (70, 120), "total": 1, "remaining": 1,
        "price": 100000, "type": "weapon", "rarity": "apocalyptic", "element": "chaos",
        "skills": ["end_of_days", "obliterate", "armageddon", "creation_end"]
    },
    "immortal_shield": {
        "name": "✨ Щит бессмертия", "defense": 100, "total": 2, "remaining": 2,
        "price": 75000, "type": "shield", "rarity": "divine",
        "skills": ["immortality", "perfect_block", "divine_intervention", "eternal_guard"]
    },
    "cloak_of_infinity": {
        "name": "🌀 Плащ бесконечности", "defense": 60, "hp_bonus": 500,
        "total": 4, "remaining": 4, "price": 60000, "type": "armor", "rarity": "divine",
        "skills": ["infinity", "cosmic_shield", "time_stop", "reality_warp"]
    }
}

# Объединение всех предметов
ALL_ITEMS = {}
for items_dict in [WEAPONS, SHIELDS, ARMORS, BOOTS, ACCESSORIES, POTIONS]:
    ALL_ITEMS.update(items_dict)

items = load_json(DATA_FILES['items'], ALL_ITEMS)
limited_items = load_json(DATA_FILES['limited'], LIMITED_ITEMS)
users = load_json(DATA_FILES['users'], {})

# ==================== СИСТЕМА НАВЫКОВ ====================
SKILLS_DATABASE = {
    "slash": {"name": "🔪 Разрез", "type": "attack", "damage_mult": 1.2, "mana_cost": 0, "cooldown": 0, "description": "Базовый удар мечом"},
    "power_shot": {"name": "🎯 Мощный выстрел", "type": "attack", "damage_mult": 1.5, "mana_cost": 10, "cooldown": 1, "description": "Усиленный выстрел из лука"},
    "flame_slash": {"name": "🔥 Огненный разрез", "type": "attack", "damage_mult": 1.8, "mana_cost": 15, "cooldown": 2, "element": "fire", "status": "burn", "status_chance": 30, "description": "Удар с огненным эффектом"},
    "fireball": {"name": "💥 Огненный шар", "type": "attack", "damage_mult": 2.0, "mana_cost": 20, "cooldown": 3, "element": "fire", "description": "Мощный огненный шар"},
    "ice_slash": {"name": "❄ Ледяной удар", "type": "attack", "damage_mult": 1.6, "mana_cost": 12, "cooldown": 2, "element": "ice", "status": "freeze", "status_chance": 25, "description": "Замораживающий удар"},
    "frost_nova": {"name": "💠 Ледяная волна", "type": "attack", "damage_mult": 1.9, "mana_cost": 25, "cooldown": 4, "element": "ice", "status": "freeze", "status_chance": 40, "description": "Взрывная волна холода"},
    "thunder_strike": {"name": "⚡ Удар молнии", "type": "attack", "damage_mult": 2.2, "mana_cost": 30, "cooldown": 3, "element": "lightning", "status": "stun", "status_chance": 20, "description": "Молниеносная атака"},
    "chain_lightning": {"name": "⚡⚡ Цепная молния", "type": "attack", "damage_mult": 1.5, "mana_cost": 35, "cooldown": 4, "element": "lightning", "chain_hits": 3, "description": "Молния бьёт по цепной реакции"},
    "shadow_strike": {"name": "🌑 Теневой удар", "type": "attack", "damage_mult": 2.5, "mana_cost": 25, "cooldown": 3, "element": "dark", "status": "curse", "status_chance": 35, "description": "Удар из тени"},
    "assassinate": {"name": "💀 Убийство", "type": "attack", "damage_mult": 3.0, "mana_cost": 40, "cooldown": 5, "element": "dark", "execution_threshold": 0.3, "description": "Мгновенное убийство цели с HP ниже 30%"},
    "holy_strike": {"name": "✨ Святой удар", "type": "attack", "damage_mult": 2.3, "mana_cost": 30, "cooldown": 3, "element": "light", "status": "bless", "status_chance": 40, "description": "Удар божественной силы"},
    "divine_judgment": {"name": "⚖ Божественный суд", "type": "attack", "damage_mult": 3.5, "mana_cost": 50, "cooldown": 6, "element": "light", "description": "Высшая божественная атака"},
    "reap": {"name": "💀 Жатва", "type": "attack", "damage_mult": 2.8, "mana_cost": 35, "cooldown": 4, "element": "dark", "life_steal": 0.3, "description": "Крадёт часть здоровья противника"},
    "block": {"name": "🛡 Блок", "type": "defense", "damage_reduction": 0.5, "mana_cost": 5, "cooldown": 1, "description": "Уменьшает получаемый урон на 50%"},
    "shield_bash": {"name": "💢 Удар щитом", "type": "attack", "damage_mult": 0.8, "mana_cost": 10, "cooldown": 2, "status": "stun", "status_chance": 20, "description": "Оглушающий удар щитом"},
    "reflect_magic": {"name": "🪞 Отражение", "type": "defense", "reflect_chance": 50, "mana_cost": 20, "cooldown": 3, "description": "Шанс отразить магическую атаку"},
    "dragon_breath": {"name": "🐉 Дыхание дракона", "type": "attack", "damage_mult": 2.5, "mana_cost": 40, "cooldown": 5, "element": "fire", "description": "Атака драконьим пламенем"},
    "divine_protection": {"name": "💫 Божественная защита", "type": "defense", "invincible_turns": 2, "mana_cost": 50, "cooldown": 8, "description": "Полная неуязвимость на 2 хода"},
    "void_absorption": {"name": "🕳 Поглощение", "type": "defense", "absorb_percent": 0.5, "mana_cost": 45, "cooldown": 5, "description": "Поглощает 50% урона в ману"},
    "berserk": {"name": "💢 Берсерк", "type": "buff", "damage_boost": 50, "defense_penalty": 30, "duration": 3, "mana_cost": 25, "cooldown": 5, "description": "+50% урона, -30% защиты на 3 хода"},
    "shadow_step": {"name": "🌑 Шаг тени", "type": "buff", "dodge_boost": 40, "duration": 2, "mana_cost": 20, "cooldown": 4, "description": "+40% к уклонению на 2 хода"},
    "rebirth": {"name": "🦅 Возрождение", "type": "heal", "revive_hp": 0.5, "mana_cost": 60, "cooldown": 10, "once_per_battle": True, "description": "Возрождает с 50% HP один раз за бой"},
    "heal_light": {"name": "💚 Исцеляющий свет", "type": "heal", "heal_percent": 0.3, "mana_cost": 25, "cooldown": 3, "description": "Восстанавливает 30% HP"},
    "meditate": {"name": "🧘 Медитация", "type": "heal", "mana_restore": 0.4, "cooldown": 4, "description": "Восстанавливает 40% маны"},
    "quick_step": {"name": "💨 Быстрый шаг", "type": "buff", "speed_boost": 20, "duration": 2, "mana_cost": 15, "cooldown": 3, "description": "+20 к скорости на 2 хода"},
    "ultimate_slash": {"name": "⚔ Финальный удар", "type": "ultimate", "damage_mult": 5.0, "mana_cost": 100, "cooldown": 15, "description": "Сверхмощная атака", "requires_full_mana": True}
}

# ==================== КЛАСС ИГРОКА ====================
class Player:
    def __init__(self, user_id, username="Unknown", first_name="Player"):
        self.user_id = str(user_id)
        if self.user_id not in users:
            users[self.user_id] = {
                "username": username,
                "first_name": first_name,
                "money": 1000,
                "level": 1,
                "exp": 0,
                "hp": 100,
                "max_hp": 100,
                "mana": 50,
                "max_mana": 50,
                "stats": {"strength": 5, "agility": 5, "intelligence": 5, "vitality": 5, "luck": 5},
                "stat_points": 5,
                "wins": 0, "losses": 0, "draws": 0,
                "win_streak": 0, "best_streak": 0,
                "total_duels": 0,
                "total_damage_dealt": 0,
                "total_damage_taken": 0,
                "inventory": [],
                "equipment": {"weapon": None, "shield": None, "armor": None, "accessory": None, "boots": None},
                "skills": ["slash", "block", "meditate"],
                "equipped_skills": ["slash", "block", "meditate"],
                "last_daily": None,
                "title": "Новичок",
                "achievements": [],
                "clan": None,
                "pvp_rating": 1000,
                "registration_date": datetime.now().isoformat(),
                "settings": {"notifications": True, "auto_skills": False}
            }
            self.save()
    
    @property
    def data(self):
        return users[self.user_id]
    
    def save(self):
        save_json(DATA_FILES['users'], users)
    
    def get_skills(self):
        """Получение доступных навыков с учётом экипировки"""
        available = list(self.data["skills"])  # Базовые навыки
        
        for slot, item_key in self.data["equipment"].items():
            if item_key:
                item = items.get(item_key) or limited_items.get(item_key)
                if item and "skills" in item:
                    available.extend(item["skills"])
        
        return list(set(available))
    
    def get_stats(self):
        """Расчёт полных характеристик"""
        s = copy.deepcopy(self.data["stats"])
        equip_stats = {"defense": 0, "hp_bonus": 0, "speed": 0, 
                       "min_damage": 0, "max_damage": 0, "block_chance": 0,
                       "crit_chance": 5, "dodge_chance": 3, "life_steal": 0}
        
        for slot, item_key in self.data["equipment"].items():
            if not item_key: continue
            item = items.get(item_key) or limited_items.get(item_key)
            if not item: continue
            
            if item["type"] == "weapon" and "damage" in item:
                equip_stats["min_damage"] += item["damage"][0]
                equip_stats["max_damage"] += item["damage"][1]
            elif item["type"] in ["shield", "armor"]:
                equip_stats["defense"] += item.get("defense", 0)
                equip_stats["block_chance"] += item.get("block_chance", 0)
                equip_stats["hp_bonus"] += item.get("hp_bonus", 0)
            elif item["type"] == "boots":
                equip_stats["speed"] += item.get("speed", 0)
        
        equip_stats["min_damage"] += s["strength"] * 2
        equip_stats["max_damage"] += s["strength"] * 3
        equip_stats["speed"] += s["agility"]
        equip_stats["crit_chance"] += s["luck"] * 0.5
        equip_stats["dodge_chance"] += s["agility"] * 0.3
        
        return equip_stats

# ==================== СТРАТЕГИЧЕСКАЯ БОЕВАЯ СИСТЕМА ====================
class StrategicBattle:
    def __init__(self, player1_id, player2_id, bet=0, duel_type="normal"):
        self.p1_id = str(player1_id)
        self.p2_id = str(player2_id)
        self.bet = bet
        self.duel_type = duel_type
        self.turn = 0
        self.max_turns = 30
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        self.p1_stats = self.p1.get_stats()
        self.p2_stats = self.p2.get_stats()
        
        self.p1_hp = self.p1.data["max_hp"] + self.p1_stats["hp_bonus"]
        self.p2_hp = self.p2.data["max_hp"] + self.p2_stats["hp_bonus"]
        self.p1_max_hp = self.p1_hp
        self.p2_max_hp = self.p2_hp
        
        self.p1_mana = self.p1.data["max_mana"]
        self.p2_mana = self.p2.data["max_mana"]
        self.p1_max_mana = self.p1_mana
        self.p2_max_mana = self.p2_mana
        
        self.p1_effects = {}
        self.p2_effects = {}
        
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        self.p1_used_rebirth = False
        self.p2_used_rebirth = False
        
        # Определение первого хода
        p1_speed = self.p1_stats["speed"] + random.randint(-5, 5)
        p2_speed = self.p2_stats["speed"] + random.randint(-5, 5)
        self.first_player = 1 if p1_speed >= p2_speed else 2
        
        # Арена и погода
        self.arena = random.choice(list(ARENA_TYPES.keys()))
        self.weather = random.choice(list(WEATHER_EFFECTS.keys()))
        
        # История боя
        self.battle_log = []
        self.state = "waiting_action"  # waiting_action, processing, finished
        self.current_player = self.first_player
        self.waiting_for = self._get_player_id(self.first_player)
        
        # Статистика битвы
        self.p1_damage_dealt = 0
        self.p2_damage_dealt = 0
        self.p1_damage_taken = 0
        self.p2_damage_taken = 0
        
        self._init_battle()
    
    def _get_player_id(self, num):
        return self.p1_id if num == 1 else self.p2_id
    
    def _get_player(self, num):
        return self.p1 if num == 1 else self.p2
    
    def _get_name(self, num):
        return self._get_player(num).data["first_name"]
    
    def _get_opponent(self, player_num):
        return 2 if player_num == 1 else 1
    
    def _init_battle(self):
        self.battle_log.append(f"⚔ <b>БИТВА НАЧИНАЕТСЯ!</b>")
        self.battle_log.append(f"🏟 Арена: <b>{ARENA_TYPES[self.arena]['name']}</b>")
        self.battle_log.append(f"🌤 Погода: <b>{WEATHER_EFFECTS[self.weather]['description']}</b>")
        self.battle_log.append(f"⚡ Первый ход: <b>{self._get_name(self.first_player)}</b>")
        self.battle_log.append("")
        self._show_status()
    
    def _show_status(self):
        p1_bar = self._hp_bar(1)
        p2_bar = self._hp_bar(2)
        self.battle_log.append(f"❤ {self._get_name(1)}: {p1_bar} {self.p1_hp}/{self.p1_max_hp} | 💎 {self.p1_mana}/{self.p1_max_mana}")
        self.battle_log.append(f"❤ {self._get_name(2)}: {p2_bar} {self.p2_hp}/{self.p2_max_hp} | 💎 {self.p2_mana}/{self.p2_max_mana}")
        self.battle_log.append("")
    
    def _hp_bar(self, player_num):
        hp = self.p1_hp if player_num == 1 else self.p2_hp
        max_hp = self.p1_max_hp if player_num == 1 else self.p2_max_hp
        pct = max(0, hp / max_hp)
        filled = int(pct * 10)
        return f"[{'█'*filled}{'░'*(10-filled)}]"
    
    def get_available_actions(self, player_id):
        """Получение доступных действий для игрока"""
        player_num = 1 if str(player_id) == self.p1_id else 2
        player = self._get_player(player_num)
        
        actions = {
            "attack": {"name": "⚔ Атака", "description": "Базовая атака", "cost": 0},
            "defend": {"name": "🛡 Защита", "description": "Уменьшить урон на 50%", "cost": 0},
            "skills": {},
            "item": {"name": "🎒 Предмет", "description": "Использовать зелье", "cost": 0}
        }
        
        # Добавление навыков
        for skill_id in player.data["equipped_skills"]:
            if skill_id in SKILLS_DATABASE:
                skill = SKILLS_DATABASE[skill_id]
                cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
                
                if skill_id in cooldowns and cooldowns[skill_id] > 0:
                    actions["skills"][skill_id] = {
                        "name": f"{skill['name']} (⏳{cooldowns[skill_id]})",
                        "available": False,
                        "cooldown": cooldowns[skill_id]
                    }
                else:
                    mana = self.p1_mana if player_num == 1 else self.p2_mana
                    if mana >= skill.get("mana_cost", 0):
                        actions["skills"][skill_id] = {
                            "name": f"{skill['name']} ({skill.get('mana_cost', 0)}💎)",
                            "available": True,
                            "description": skill["description"]
                        }
                    else:
                        actions["skills"][skill_id] = {
                            "name": f"{skill['name']} (Нет маны)",
                            "available": False
                        }
        
        return actions
    
    def execute_action(self, player_id, action_type, action_data=None):
        """Выполнение действия игрока"""
        if str(player_id) != self.waiting_for:
            return False, "Не ваш ход!"
        
        player_num = 1 if str(player_id) == self.p1_id else 2
        opponent_num = self._get_opponent(player_num)
        
        self.turn += 1
        self.battle_log.append(f"\n<b>Ход {self.turn}</b> - {self._get_name(player_num)}")
        
        # Обработка эффектов
        self._process_effects(player_num)
        self._process_effects(opponent_num)
        
        # Уменьшение кулдаунов
        self._decrease_cooldowns(player_num)
        
        if action_type == "attack":
            self._basic_attack(player_num, opponent_num)
        elif action_type == "defend":
            self._defend_action(player_num)
        elif action_type == "skill":
            self._use_skill(player_num, opponent_num, action_data)
        elif action_type == "item":
            self._use_item(player_num, action_data)
        else:
            return False, "Неизвестное действие!"
        
        # Проверка на завершение боя
        if self.p1_hp <= 0 and self.p2_hp <= 0:
            self.state = "finished"
            return True, "draw"
        elif self.p1_hp <= 0:
            if self.p1_effects.get("rebirth") and not self.p1_used_rebirth:
                self.p1_hp = int(self.p1_max_hp * 0.5)
                self.p1_used_rebirth = True
                self.battle_log.append(f"🦅 {self._get_name(1)} возрождается из пепла!")
                del self.p1_effects["rebirth"]
            else:
                self.state = "finished"
                return True, "p2_wins"
        elif self.p2_hp <= 0:
            if self.p2_effects.get("rebirth") and not self.p2_used_rebirth:
                self.p2_hp = int(self.p2_max_hp * 0.5)
                self.p2_used_rebirth = True
                self.battle_log.append(f"🦅 {self._get_name(2)} возрождается из пепла!")
                del self.p2_effects["rebirth"]
            else:
                self.state = "finished"
                return True, "p1_wins"
        
        if self.turn >= self.max_turns:
            self.state = "finished"
            return True, "draw"
        
        # Переключение хода
        self.current_player = opponent_num
        self.waiting_for = self._get_player_id(opponent_num)
        self._show_status()
        
        return True, "continue"
    
    def _basic_attack(self, attacker, defender):
        stats = self.p1_stats if attacker == 1 else self.p2_stats
        base_dmg = random.randint(stats["min_damage"], stats["max_damage"])
        
        # Крит
        is_crit = random.random() * 100 < stats["crit_chance"]
        if is_crit: base_dmg = int(base_dmg * 1.5)
        
        # Эффект арены
        if self.arena == "arena":
            base_dmg = int(base_dmg * 1.1)
        
        # Защита
        def_stats = self.p2_stats if defender == 2 else self.p1_stats
        defense = def_stats["defense"]
        dmg_reduction = defense / (defense + 100)
        
        # Блок
        if random.random() * 100 < def_stats["block_chance"]:
            dmg_reduction += 0.3
            self.battle_log.append("🛡 Заблокировано!")
        
        # Уклонение
        if random.random() * 100 < def_stats["dodge_chance"]:
            self.battle_log.append("💨 Уклонение!")
            self._apply_damage(attacker, defender, 0)
            return
        
        final_dmg = max(1, int(base_dmg * (1 - dmg_reduction)))
        
        crit_text = "💥 КРИТ! " if is_crit else ""
        self.battle_log.append(f"{crit_text}⚔ Нанесено {final_dmg} урона")
        
        self._apply_damage(attacker, defender, final_dmg)
    
    def _defend_action(self, player_num):
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        effects["defending"] = 1
        self.battle_log.append(f"🛡 {self._get_name(player_num)} встаёт в защитную стойку!")
    
    def _use_skill(self, attacker, defender, skill_id):
        if skill_id not in SKILLS_DATABASE:
            self.battle_log.append("❌ Навык не найден!")
            return
        
        skill = SKILLS_DATABASE[skill_id]
        mana_pool = self.p1_mana if attacker == 1 else self.p2_mana
        mana_cost = skill.get("mana_cost", 0)
        
        if mana_pool < mana_cost:
            self.battle_log.append("❌ Недостаточно маны!")
            return
        
        # Трата маны
        if attacker == 1:
            self.p1_mana -= mana_cost
        else:
            self.p2_mana -= mana_cost
        
        # Установка кулдауна
        cooldowns = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
        cooldowns[skill_id] = skill.get("cooldown", 0)
        
        self.battle_log.append(f"✨ Использован навык: {skill['name']}!")
        
        if skill["type"] == "attack":
            self._execute_attack_skill(attacker, defender, skill)
        elif skill["type"] == "defense":
            self._execute_defense_skill(attacker, skill)
        elif skill["type"] == "heal":
            self._execute_heal_skill(attacker, skill)
        elif skill["type"] == "buff":
            self._execute_buff_skill(attacker, skill)
    
    def _execute_attack_skill(self, attacker, defender, skill):
        stats = self.p1_stats if attacker == 1 else self.p2_stats
        base_dmg = random.randint(stats["min_damage"], stats["max_damage"])
        dmg = int(base_dmg * skill.get("damage_mult", 1.0))
        
        # Элементальные модификаторы
        if "element" in skill:
            element = skill["element"]
            if self.weather == "storm" and element == "lightning":
                dmg = int(dmg * 1.5)
                self.battle_log.append("⛈ Буря усиливает молнию!")
            elif self.weather == "rain" and element == "fire":
                dmg = int(dmg * 0.7)
                self.battle_log.append("🌧 Дождь ослабляет огонь")
        
        # Применение урона
        self._apply_damage(attacker, defender, dmg)
        
        # Статус эффекты
        if "status" in skill and random.random() * 100 < skill.get("status_chance", 50):
            self._apply_status(defender, skill["status"])
        
        # Вампиризм
        if "life_steal" in skill:
            heal = int(dmg * skill["life_steal"])
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self.battle_log.append(f"💚 Вампиризм +{heal} HP")
    
    def _execute_defense_skill(self, player_num, skill):
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        
        if "invincible_turns" in skill:
            effects["invincible"] = skill["invincible_turns"]
            self.battle_log.append(f"✨ Неуязвимость на {skill['invincible_turns']} хода!")
        elif "absorb_percent" in skill:
            effects["absorbing"] = skill["absorb_percent"]
            self.battle_log.append("🕳 Поглощение урона активировано!")
    
    def _execute_heal_skill(self, player_num, skill):
        if "heal_percent" in skill:
            max_hp = self.p1_max_hp if player_num == 1 else self.p2_max_hp
            heal = int(max_hp * skill["heal_percent"])
            if player_num == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self.battle_log.append(f"💚 Исцеление +{heal} HP")
        elif "mana_restore" in skill:
            if player_num == 1:
                self.p1_mana = min(self.p1_max_mana, self.p1_mana + int(self.p1_max_mana * skill["mana_restore"]))
                self.battle_log.append(f"💎 Мана +{int(self.p1_max_mana * skill['mana_restore'])}")
            else:
                self.p2_mana = min(self.p2_max_mana, self.p2_mana + int(self.p2_max_mana * skill["mana_restore"]))
                self.battle_log.append(f"💎 Мана +{int(self.p2_max_mana * skill['mana_restore'])}")
    
    def _execute_buff_skill(self, player_num, skill):
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        
        if "damage_boost" in skill:
            effects["damage_boost"] = {"value": skill["damage_boost"], "duration": skill.get("duration", 2)}
            self.battle_log.append(f"💢 Урон +{skill['damage_boost']}% на {skill.get('duration', 2)} хода!")
        if "dodge_boost" in skill:
            effects["dodge_boost"] = {"value": skill["dodge_boost"], "duration": skill.get("duration", 2)}
            self.battle_log.append(f"💨 Уклонение +{skill['dodge_boost']}% на {skill.get('duration', 2)} хода!")
    
    def _apply_damage(self, attacker, defender, damage):
        if damage <= 0:
            return
        
        # Проверка неуязвимости
        def_effects = self.p1_effects if defender == 1 else self.p2_effects
        if "invincible" in def_effects:
            self.battle_log.append("✨ Урон поглощён неуязвимостью!")
            return
        
        # Поглощение урона
        if "absorbing" in def_effects:
            absorbed = int(damage * def_effects["absorbing"])
            if defender == 1:
                self.p1_mana = min(self.p1_max_mana, self.p1_mana + absorbed)
            else:
                self.p2_mana = min(self.p2_max_mana, self.p2_mana + absorbed)
            damage -= absorbed
            self.battle_log.append(f"🕳 Поглощено {absorbed} урона в ману!")
        
        # Уменьшение урона при защите
        if "defending" in def_effects:
            damage = int(damage * 0.5)
            del def_effects["defending"]
        
        # Применение урона
        if defender == 1:
            self.p1_hp -= damage
        else:
            self.p2_hp -= damage
        
        # Статистика
        if attacker == 1:
            self.p1_damage_dealt += damage
            self.p2_damage_taken += damage
        else:
            self.p2_damage_dealt += damage
            self.p1_damage_taken += damage
    
    def _apply_status(self, player_num, status):
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        duration = random.randint(2, 4)
        effects[status] = duration
        status_names = {"burn": "🔥 Горение", "freeze": "❄ Заморозка", "stun": "💫 Оглушение",
                        "poison": "☠ Отравление", "curse": "🌑 Проклятие", "bless": "✨ Благословение"}
        self.battle_log.append(f"{status_names.get(status, status)} на {duration} хода!")
    
    def _process_effects(self, player_num):
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        hp = self.p1_hp if player_num == 1 else self.p2_hp
        max_hp = self.p1_max_hp if player_num == 1 else self.p2_max_hp
        
        for effect, duration in list(effects.items()):
            if effect == "burn":
                dmg = random.randint(5, 15)
                hp -= dmg
                self.battle_log.append(f"🔥 Горение: -{dmg} HP")
            elif effect == "poison":
                dmg = random.randint(8, 20)
                hp -= dmg
                self.battle_log.append(f"☠ Яд: -{dmg} HP")
            elif effect == "bless":
                heal = random.randint(10, 25)
                hp = min(max_hp, hp + heal)
                self.battle_log.append(f"✨ Благословение: +{heal} HP")
            elif effect == "freeze" and player_num == self.current_player:
                self.battle_log.append("❄ Заморожен! Пропуск хода")
                self.current_player = self._get_opponent(player_num)
                self.waiting_for = self._get_player_id(self.current_player)
            
            if isinstance(duration, int) and duration > 0:
                effects[effect] = duration - 1
                if effects[effect] <= 0:
                    del effects[effect]
            elif isinstance(duration, dict):
                duration["duration"] -= 1
                if duration["duration"] <= 0:
                    del effects[effect]
        
        if player_num == 1:
            self.p1_hp = hp
        else:
            self.p2_hp = hp
    
    def _decrease_cooldowns(self, player_num):
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        for skill_id in list(cooldowns.keys()):
            if cooldowns[skill_id] > 0:
                cooldowns[skill_id] -= 1
    
    def _use_item(self, player_num, item_key):
        player = self._get_player(player_num)
        if item_key not in player.data["inventory"]:
            self.battle_log.append("❌ Нет такого предмета!")
            return
        
        item = items.get(item_key) or limited_items.get(item_key)
        if not item or item["type"] != "potion":
            self.battle_log.append("❌ Нельзя использовать!")
            return
        
        player.data["inventory"].remove(item_key)
        
        if "heal" in item:
            if player_num == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + item["heal"])
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + item["heal"])
            self.battle_log.append(f"💚 +{item['heal']} HP от {item['name']}")
        
        if "mana_restore" in item:
            if player_num == 1:
                self.p1_mana = min(self.p1_max_mana, self.p1_mana + item["mana_restore"])
            else:
                self.p2_mana = min(self.p2_max_mana, self.p2_mana + item["mana_restore"])
            self.battle_log.append(f"💎 +{item['mana_restore']} маны")
        
        player.save()

# ==================== АКТИВНЫЕ БИТВЫ ====================
active_battles = {}

# ==================== ГЛАВНОЕ МЕНЮ ====================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("⚔️ Дуэли", "👤 Герой", "🏪 Торговля", "🌍 Мир")
    return markup

def duel_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("⚡ Быстрая дуэль", "👥 PvP дуэль")
    markup.add("🏆 Рейтинговая", "💀 Хардкор")
    markup.add("◀️ Назад")
    return markup

def hero_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 Статистика", "🎒 Инвентарь")
    markup.add("⚡ Характеристики", "✨ Навыки")
    markup.add("◀️ Назад")
    return markup

def trade_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🛒 Магазин", "💎 Редкости")
    markup.add("🎁 Бонус", "💱 Обмен")
    markup.add("◀️ Назад")
    return markup

def world_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🏰 Данжи", "🛡 Кланы")
    markup.add("🏟 Турниры", "📜 Квесты")
    markup.add("◀️ Назад")
    return markup

# ==================== ОБРАБОТЧИКИ КОМАНД ====================
@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    first_name = message.from_user.first_name or "Player"
    
    player = Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ - СТРАТЕГИЧЕСКАЯ БИТВА ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

🎮 <b>Пошаговая стратегическая система:</b>
• Выбирайте действия каждый ход
• Используйте навыки и заклинания
• Комбинируйте атаки и защиту
• Управляйте маной и кулдаунами

<b>Системы:</b>
⚔ Стратегические дуэли с выбором действий
✨ 30+ уникальных навыков
🔥 Элементы и статус-эффекты
🏟 Разные арены с модификаторами
🌤 Погода влияет на битву
💎 Лимитированные артефакты

💰 Старт: <b>1000 монет</b>
🎁 Ежедневные бонусы
📈 Система уровней до 100+

<i>Используйте кнопки меню!</i>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "◀️ Назад")
def back_main(message):
    bot.send_message(message.chat.id, "🔙 Главное меню", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def section_duel(message):
    txt = """
<b>⚔️ ДУЭЛИ - СТРАТЕГИЧЕСКИЙ РЕЖИМ</b>

<b>Пошаговая система битвы:</b>
Каждый ход вы выбираете действие:
• ⚔ Атака - базовый удар
• 🛡 Защита - снижение урона на 50%
• ✨ Навыки - особые умения (тратят ману)
• 🎒 Предмет - использовать зелье

<b>Стратегия:</b>
Управляйте маной, следите за кулдаунами
Комбинируйте навыки для максимального эффекта
Учитывайте погоду и арену!

<b>Режимы:</b>
⚡ Быстрая дуэль - против бота
👥 PvP дуэль - пошаговая битва с игроком
🏆 Рейтинговая - за рейтинг
💀 Хардкор - высокие ставки
"""
    bot.send_message(message.chat.id, txt, reply_markup=duel_menu())

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def section_hero(message):
    txt = """
<b>👤 ГЕРОЙ</b>

Управляйте своим персонажем:
📊 Статистика - ваши показатели
🎒 Инвентарь - предметы и экипировка
⚡ Характеристики - распределение очков
✨ Навыки - выбор активных умений
"""
    bot.send_message(message.chat.id, txt, reply_markup=hero_menu())

@bot.message_handler(func=lambda m: m.text == "🏪 Торговля")
def section_trade(message):
    txt = """
<b>🏪 ТОРГОВЛЯ</b>

🛒 Магазин - покупка снаряжения
💎 Редкости - лимитированные предметы
🎁 Бонус - ежедневная награда
💱 Обмен - торговля с игроками
"""
    bot.send_message(message.chat.id, txt, reply_markup=trade_menu())

@bot.message_handler(func=lambda m: m.text == "🌍 Мир")
def section_world(message):
    txt = """
<b>🌍 ИГРОВОЙ МИР</b>

🏰 Данжи - подземелья с боссами
🛡 Кланы - объединения игроков
🏟 Турниры - соревнования
📜 Квесты - задания и награды
"""
    bot.send_message(message.chat.id, txt, reply_markup=world_menu())

# ==================== НАВЫКИ ====================
@bot.message_handler(func=lambda m: m.text == "✨ Навыки")
def skills_menu(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    all_skills = player.get_skills()
    equipped = player.data["equipped_skills"]
    
    txt = "<b>✨ НАВЫКИ</b>\n\n"
    txt += "<b>Активные навыки (макс 6):</b>\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for i, skill_id in enumerate(equipped, 1):
        skill = SKILLS_DATABASE.get(skill_id, {})
        txt += f"{i}. {skill.get('name', skill_id)} "
        txt += f"[{skill.get('type', '?')}] "
        txt += f"💎{skill.get('mana_cost', 0)}\n"
        txt += f"   {skill.get('description', '')}\n"
        markup.add(types.InlineKeyboardButton(
            f"❌ Снять: {skill.get('name', skill_id)}",
            callback_data=f"unequip_skill_{skill_id}"
        ))
    
    txt += "\n<b>Доступные навыки:</b>\n"
    available = [s for s in all_skills if s not in equipped]
    
    for skill_id in available[:10]:
        skill = SKILLS_DATABASE.get(skill_id, {})
        txt += f"• {skill.get('name', skill_id)} [{skill.get('type', '?')}]\n"
        markup.add(types.InlineKeyboardButton(
            f"✅ Экипировать: {skill.get('name', skill_id)}",
            callback_data=f"equip_skill_{skill_id}"
        ))
    
    bot.send_message(message.chat.id, txt[:4000], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("equip_skill_"))
def equip_skill(call):
    skill_id = call.data.split("_", 2)[2]
    user_id = call.from_user.id
    player = Player(user_id)
    
    if len(player.data["equipped_skills"]) >= 6:
        bot.answer_callback_query(call.id, "❌ Максимум 6 навыков!")
        return
    
    if skill_id not in player.get_skills():
        bot.answer_callback_query(call.id, "❌ Навык недоступен!")
        return
    
    if skill_id in player.data["equipped_skills"]:
        bot.answer_callback_query(call.id, "❌ Уже экипирован!")
        return
    
    player.data["equipped_skills"].append(skill_id)
    player.save()
    bot.answer_callback_query(call.id, f"✅ {SKILLS_DATABASE[skill_id]['name']} экипирован!")
    skills_menu(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("unequip_skill_"))
def unequip_skill(call):
    skill_id = call.data.split("_", 2)[2]
    user_id = call.from_user.id
    player = Player(user_id)
    
    if skill_id in player.data["equipped_skills"]:
        player.data["equipped_skills"].remove(skill_id)
        player.save()
    
    bot.answer_callback_query(call.id, "✅ Навык снят!")
    skills_menu(call.message)

# ==================== БЫСТРАЯ ДУЭЛЬ ====================
@bot.message_handler(func=lambda m: m.text == "⚡ Быстрая дуэль")
def quick_duel(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    # Проверка на активную битву
    if str(user_id) in active_battles:
        battle = active_battles[str(user_id)]
        if battle.state != "finished":
            show_battle_interface(message.chat.id, user_id, battle)
            return
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    for bet in [50, 100, 200, 500, 1000, 2000]:
        markup.add(types.InlineKeyboardButton(
            f"{bet}💰", callback_data=f"qduel_{bet}"
        ))
    markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_duel"))
    
    bot.send_message(message.chat.id,
        f"<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n\n"
        f"Выберите ставку:\n"
        f"💰 Баланс: <b>{player.data['money']} монет</b>",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def start_quick_duel(call):
    user_id = call.from_user.id
    bet = int(call.data.split("_")[1])
    player = Player(user_id)
    
    if player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    player.data["money"] -= bet
    player.save()
    
    # Создание бота
    bot_level = random.randint(max(1, player.data["level"] - 3), player.data["level"] + 3)
    bot_id = f"bot_{random.randint(10000,99999)}"
    
    bot_equipment = {}
    for slot, item_type in [("weapon", "weapon"), ("shield", "shield"), ("armor", "armor")]:
        available = [k for k, v in items.items() if v["type"] == item_type and v.get("level_req", 1) <= bot_level]
        if available:
            bot_equipment[slot] = random.choice(available)
    
    users[bot_id] = {
        "username": f"Bot_{bot_level}", "first_name": f"🤖 Бот Lv.{bot_level}",
        "money": 0, "level": bot_level, "exp": 0, "hp": 100 + bot_level * 10,
        "max_hp": 100 + bot_level * 10, "mana": 50 + bot_level * 5,
        "max_mana": 50 + bot_level * 5,
        "stats": {"strength": 5 + bot_level, "agility": 5 + bot_level//2,
                  "intelligence": 5 + bot_level//3, "vitality": 5 + bot_level//2,
                  "luck": 3 + bot_level//4},
        "stat_points": 0, "wins": 0, "losses": 0, "inventory": [],
        "equipment": bot_equipment,
        "skills": ["slash", "block", "meditate", "fireball"],
        "equipped_skills": ["slash", "block", "meditate", "fireball"],
        "last_daily": None, "title": "Бот", "achievements": [],
        "clan": None, "pvp_rating": 1000 + bot_level * 10
    }
    
    # Запуск битвы
    battle = StrategicBattle(user_id, bot_id, bet, "quick")
    active_battles[str(user_id)] = battle
    active_battles[bot_id] = battle
    
    bot.edit_message_text(
        "<b>⚔ БИТВА НАЧАЛАСЬ!</b>\n\n" + "\n".join(battle.battle_log),
        call.message.chat.id, call.message.message_id
    )
    
    # Показ интерфейса битвы
    show_battle_interface(call.message.chat.id, user_id, battle)

# ==================== PVP ДУЭЛЬ ====================
@bot.message_handler(func=lambda m: m.text == "👥 PvP дуэль")
def pvp_duel_info(message):
    bot.send_message(message.chat.id, """
<b>👥 PvP ДУЭЛЬ - ПОШАГОВАЯ СТРАТЕГИЯ</b>

Для вызова на дуэль:
1. Ответьте на сообщение противника
2. Используйте команду: <code>/duel [ставка]</code>

Ставка от 50 до 5000💰
Победитель забирает всё!

<b>Битва проходит пошагово:</b>
Каждый игрок выбирает действие в свой ход
Доступны атаки, защита, навыки и предметы
""")

@bot.message_handler(commands=['duel'])
def duel_command(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Ответьте на сообщение игрока!")
        return
    
    user_id = message.from_user.id
    opponent_id = message.reply_to_message.from_user.id
    
    if user_id == opponent_id:
        bot.send_message(message.chat.id, "❌ Нельзя вызвать себя!")
        return
    
    if str(opponent_id) not in users:
        bot.send_message(message.chat.id, "❌ Игрок не зарегистрирован!")
        return
    
    try:
        parts = message.text.split()
        bet = int(parts[1]) if len(parts) > 1 else 100
        bet = max(50, min(5000, bet))
    except:
        bet = 100
    
    player = Player(user_id)
    opponent = Player(opponent_id)
    
    if player.data["money"] < bet:
        bot.send_message(message.chat.id, f"❌ У вас недостаточно монет! Нужно {bet}💰")
        return
    
    if opponent.data["money"] < bet:
        bot.send_message(message.chat.id, f"❌ У противника недостаточно монет! Нужно {bet}💰")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"accept_pvp_{user_id}_{bet}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data="cancel_duel")
    )
    
    bot.send_message(message.chat.id,
        f"<b>⚔ ВЫЗОВ НА ПОШАГОВУЮ ДУЭЛЬ!</b>\n\n"
        f"<b>{message.from_user.first_name}</b> вызывает <b>{message.reply_to_message.from_user.first_name}</b>!\n"
        f"Ставка: <b>{bet}💰</b>\n\n"
        f"<i>Битва будет проходить пошагово с выбором действий!</i>",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_pvp_"))
def accept_pvp_duel(call):
    parts = call.data.split("_")
    challenger_id = int(parts[2])
    bet = int(parts[3])
    opponent_id = call.from_user.id
    
    if opponent_id == challenger_id:
        bot.answer_callback_query(call.id, "❌ Ошибка!")
        return
    
    challenger = Player(challenger_id)
    opponent = Player(opponent_id)
    
    if challenger.data["money"] < bet or opponent.data["money"] < bet:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    challenger.data["money"] -= bet
    opponent.data["money"] -= bet
    challenger.save()
    opponent.save()
    
    battle = StrategicBattle(challenger_id, opponent_id, bet, "pvp")
    active_battles[str(challenger_id)] = battle
    active_battles[str(opponent_id)] = battle
    
    bot.edit_message_text(
        "<b>⚔ ПОШАГОВАЯ БИТВА НАЧАЛАСЬ!</b>\n\n" + "\n".join(battle.battle_log),
        call.message.chat.id, call.message.message_id
    )
    
    show_battle_interface(call.message.chat.id, challenger_id, battle)

# ==================== ИНТЕРФЕЙС БИТВЫ ====================
def show_battle_interface(chat_id, player_id, battle):
    """Отображение интерфейса битвы с доступными действиями"""
    if battle.state == "finished":
        finish_battle(chat_id, battle)
        return
    
    if str(player_id) != battle.waiting_for:
        opponent_id = battle.p1_id if str(player_id) == battle.p2_id else battle.p2_id
        bot.send_message(chat_id,
            f"⏳ Ожидание хода противника...\n\n" + "\n".join(battle.battle_log[-5:]),
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh_{player_id}")
            ))
        return
    
    actions = battle.get_available_actions(player_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚔ Атака", callback_data=f"battle_attack_{player_id}"),
        types.InlineKeyboardButton("🛡 Защита", callback_data=f"battle_defend_{player_id}")
    )
    
    # Навыки
    for skill_id, skill_data in actions["skills"].items():
        if skill_data.get("available"):
            markup.add(types.InlineKeyboardButton(
                skill_data["name"],
                callback_data=f"battle_skill_{player_id}_{skill_id}"
            ))
    
    markup.add(types.InlineKeyboardButton(
        "🎒 Предмет", callback_data=f"battle_items_{player_id}"
    ))
    markup.add(types.InlineKeyboardButton(
        "🔄 Обновить", callback_data=f"refresh_{player_id}"
    ))
    
    battle_text = "\n".join(battle.battle_log[-10:])
    battle_text += f"\n\n<b>🎯 ВАШ ХОД!</b>\nВыберите действие:"
    
    try:
        bot.send_message(chat_id, battle_text[:4000], reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("battle_"))
def handle_battle_action(call):
    parts = call.data.split("_")
    action = parts[1]
    
    if action in ["attack", "defend"]:
        player_id = int(parts[2])
        process_battle_action(call, player_id, action)
    
    elif action == "skill":
        player_id = int(parts[2])
        skill_id = parts[3]
        process_battle_action(call, player_id, "skill", skill_id)
    
    elif action == "items":
        player_id = int(parts[2])
        show_battle_items(call, player_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("refresh_"))
def refresh_battle(call):
    player_id = int(call.data.split("_")[1])
    if str(player_id) in active_battles:
        battle = active_battles[str(player_id)]
        bot.edit_message_text(
            "\n".join(battle.battle_log[-15:]),
            call.message.chat.id, call.message.message_id
        )
        show_battle_interface(call.message.chat.id, player_id, battle)

def process_battle_action(call, player_id, action_type, skill_id=None):
    """Обработка действия в битве"""
    if str(player_id) not in active_battles:
        bot.answer_callback_query(call.id, "❌ Битва завершена!")
        return
    
    battle = active_battles[str(player_id)]
    
    if battle.state == "finished":
        bot.answer_callback_query(call.id, "❌ Битва завершена!")
        finish_battle(call.message.chat.id, battle)
        return
    
    result, message = battle.execute_action(player_id, action_type, skill_id)
    
    if not result:
        bot.answer_callback_query(call.id, message)
        return
    
    if message == "draw":
        bot.edit_message_text(
            "🤝 <b>НИЧЬЯ!</b>\n\n" + "\n".join(battle.battle_log),
            call.message.chat.id, call.message.message_id
        )
        finish_battle(call.message.chat.id, battle)
    elif message in ["p1_wins", "p2_wins"]:
        winner_id = battle.p1_id if message == "p1_wins" else battle.p2_id
        bot.edit_message_text(
            f"🏆 <b>ПОБЕДИТЕЛЬ!</b>\n\n" + "\n".join(battle.battle_log),
            call.message.chat.id, call.message.message_id
        )
        finish_battle(call.message.chat.id, battle)
    else:
        bot.edit_message_text(
            "\n".join(battle.battle_log[-15:]),
            call.message.chat.id, call.message.message_id
        )
        show_battle_interface(call.message.chat.id, player_id, battle)
    
    bot.answer_callback_query(call.id)

def show_battle_items(call, player_id):
    """Показ доступных предметов во время битвы"""
    player = Player(player_id)
    potions = [k for k in player.data["inventory"] 
               if (items.get(k) or limited_items.get(k, {})).get("type") == "potion"]
    
    if not potions:
        bot.answer_callback_query(call.id, "❌ Нет зелий в инвентаре!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for pot_key in potions[:5]:
        pot = items.get(pot_key) or limited_items.get(pot_key)
        markup.add(types.InlineKeyboardButton(
            pot['name'], callback_data=f"battle_useitem_{player_id}_{pot_key}"
        ))
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data=f"refresh_{player_id}"))
    
    bot.edit_message_text("🎒 Выберите зелье:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("battle_useitem_"))
def use_battle_item(call):
    parts = call.data.split("_")
    player_id = int(parts[2])
    item_key = parts[3]
    
    if str(player_id) not in active_battles:
        bot.answer_callback_query(call.id, "❌ Битва завершена!")
        return
    
    battle = active_battles[str(player_id)]
    battle.execute_action(player_id, "item", item_key)
    
    bot.edit_message_text(
        "\n".join(battle.battle_log[-15:]),
        call.message.chat.id, call.message.message_id
    )
    
    show_battle_interface(call.message.chat.id, player_id, battle)
    bot.answer_callback_query(call.id, "✅ Предмет использован!")

def finish_battle(chat_id, battle):
    """Завершение битвы и начисление наград"""
    p1 = Player(battle.p1_id)
    p2 = Player(battle.p2_id)
    
    # Определение победителя
    if battle.p1_hp > battle.p2_hp:
        winner, loser = p1, p2
    elif battle.p2_hp > battle.p1_hp:
        winner, loser = p2, p1
    else:
        # Ничья - возврат ставок
        if battle.duel_type != "quick":
            p1.data["money"] += battle.bet
            p2.data["money"] += battle.bet
        p1.data["draws"] += 1
        p2.data["draws"] += 1
        p1.save()
        p2.save()
        
        # Очистка ботов
        if "bot_" in battle.p1_id: del users[battle.p1_id]
        if "bot_" in battle.p2_id: del users[battle.p2_id]
        
        cleanup_battle(battle)
        return
    
    # Награды
    reward = battle.bet * 2
    winner.data["money"] += reward
    winner.data["wins"] += 1
    winner.data["win_streak"] += 1
    winner.data["total_duels"] += 1
    if winner.data["win_streak"] > winner.data["best_streak"]:
        winner.data["best_streak"] = winner.data["win_streak"]
    
    loser.data["losses"] += 1
    loser.data["win_streak"] = 0
    loser.data["total_duels"] += 1
    
    # Опыт
    exp_winner = battle.bet // 2 + battle.turn * 5
    exp_loser = battle.bet // 4 + battle.turn * 2
    winner.data["exp"] += exp_winner
    loser.data["exp"] += exp_loser
    
    # Статистика урона
    if winner == p1:
        winner.data["total_damage_dealt"] += battle.p1_damage_dealt
        loser.data["total_damage_dealt"] += battle.p2_damage_dealt
    else:
        winner.data["total_damage_dealt"] += battle.p2_damage_dealt
        loser.data["total_damage_dealt"] += battle.p1_damage_dealt
    
    check_level_up(winner)
    check_level_up(loser)
    winner.save()
    loser.save()
    
    # Очистка ботов
    if "bot_" in battle.p1_id: del users[battle.p1_id]
    if "bot_" in battle.p2_id: del users[battle.p2_id]
    
    cleanup_battle(battle)
    
    result_text = f"""
<b>🏆 БИТВА ЗАВЕРШЕНА!</b>

Победитель: <b>{winner.data['first_name']}</b>
💰 Награда: <b>{reward} монет</b>
⚔ Урона нанесено: <b>{battle.p1_damage_dealt if winner == p1 else battle.p2_damage_dealt}</b>
🛡 Урона получено: <b>{battle.p1_damage_taken if winner == p1 else battle.p2_damage_taken}</b>
📊 Ходов: <b>{battle.turn}</b>
    """
    
    try:
        bot.send_message(chat_id, result_text)
    except:
        pass

def cleanup_battle(battle):
    """Очистка активной битвы"""
    for pid in [battle.p1_id, battle.p2_id]:
        if pid in active_battles:
            del active_battles[pid]
    save_json(DATA_FILES['users'], users)

# ==================== МАГАЗИН ====================
@bot.message_handler(func=lambda m: m.text == "🛒 Магазин")
def shop_main(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚔ Оружие", callback_data="shop_cat_weapon"),
        types.InlineKeyboardButton("🛡 Щиты", callback_data="shop_cat_shield"),
        types.InlineKeyboardButton("🧥 Броня", callback_data="shop_cat_armor"),
        types.InlineKeyboardButton("👢 Обувь", callback_data="shop_cat_boots"),
        types.InlineKeyboardButton("📿 Аксессуары", callback_data="shop_cat_accessory"),
        types.InlineKeyboardButton("🧪 Зелья", callback_data="shop_cat_potion")
    )
    
    bot.send_message(message.chat.id,
        f"<b>🛒 МАГАЗИН</b>\n\n💰 Баланс: <b>{player.data['money']} монет</b>\n⭐ Уровень: <b>{player.data['level']}</b>\n\nВыберите категорию:",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shop_cat_"))
def shop_category_view(call):
    category = call.data.split("_")[2]
    user_id = call.from_user.id
    player = Player(user_id)
    
    cat_names = {"weapon": "⚔ ОРУЖИЕ", "shield": "🛡 ЩИТЫ", "armor": "🧥 БРОНЯ",
                 "boots": "👢 ОБУВЬ", "accessory": "📿 АКСЕССУАРЫ", "potion": "🧪 ЗЕЛЬЯ"}
    
    cat_items = {k: v for k, v in items.items() if v["type"] == category}
    
    txt = f"<b>{cat_names[category]}</b>\n"
    txt += f"💰 {player.data['money']} монет | ⭐ Ур.{player.data['level']}\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, item in sorted(cat_items.items(), key=lambda x: x[1]["price"]):
        rarity = RARITY_COLORS.get(item["rarity"], "⬜")
        
        if category == "weapon":
            stats = f"Урон: {item['damage'][0]}-{item['damage'][1]}"
        elif category in ["shield", "armor"]:
            stats = f"Защита: {item.get('defense', 0)}"
            if "hp_bonus" in item: stats += f" | HP: +{item['hp_bonus']}"
        elif category == "boots":
            stats = f"Скорость: +{item.get('speed', 0)}"
        elif category == "potion":
            stats = f"Лечение: {item.get('heal', 0)}" if "heal" in item else "Эффект"
        else:
            stats = item.get("description", "")
        
        txt += f"{rarity} <b>{item['name']}</b> - {item['price']}💰\n"
        txt += f"   {stats} | Ур.{item.get('level_req', 1)}\n\n"
        
        if player.data["money"] >= item["price"] and player.data["level"] >= item.get("level_req", 1):
            markup.add(types.InlineKeyboardButton(
                f"Купить: {item['name']}",
                callback_data=f"buy_{item_key}"
            ))
    
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back_shop"))
    bot.edit_message_text(txt[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_shop")
def back_shop(call):
    shop_main(call.message)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_item(call):
    item_key = call.data[4:]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(item_key) or limited_items.get(item_key)
    if not item:
        bot.answer_callback_query(call.id, "❌ Предмет не найден!")
        return
    
    if player.data["level"] < item.get("level_req", 1):
        bot.answer_callback_query(call.id, f"❌ Нужен {item.get('level_req', 1)} ур.!")
        return
    
    if player.data["money"] < item["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    if item_key in limited_items and limited_items[item_key]["remaining"] <= 0:
        bot.answer_callback_query(call.id, "❌ Закончился!")
        return
    
    player.data["money"] -= item["price"]
    player.data["inventory"].append(item_key)
    
    if item_key in limited_items:
        limited_items[item_key]["remaining"] -= 1
        save_json(DATA_FILES['limited'], limited_items)
    
    player.save()
    bot.answer_callback_query(call.id, f"✅ {item['name']} куплен!")
    shop_category_view(call)

# ==================== ИНВЕНТАРЬ ====================
@bot.message_handler(func=lambda m: m.text == "🎒 Инвентарь")
def inventory_show(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    if not player.data["inventory"]:
        bot.send_message(message.chat.id, "🎒 Инвентарь пуст!")
        return
    
    item_counts = defaultdict(int)
    for k in player.data["inventory"]:
        item_counts[k] += 1
    
    txt = "<b>🎒 ИНВЕНТАРЬ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, count in sorted(item_counts.items()):
        item = items.get(item_key) or limited_items.get(item_key)
        if not item: continue
        
        equipped = ""
        for slot, eq in player.data["equipment"].items():
            if eq == item_key:
                equipped = f" [{slot}]"
                break
        
        rarity = RARITY_COLORS.get(item.get("rarity", "common"), "")
        txt += f"{rarity} {item['name']} x{count}{equipped}\n"
        
        if item["type"] in ["weapon", "shield", "armor", "boots", "accessory"]:
            markup.add(types.InlineKeyboardButton(
                f"Экипировать: {item['name']}",
                callback_data=f"equip_{item_key}"
            ))
        elif item["type"] == "potion" and "heal" in item:
            markup.add(types.InlineKeyboardButton(
                f"Использовать: {item['name']}",
                callback_data=f"usepot_{item_key}"
            ))
    
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh_inv"))
    bot.send_message(message.chat.id, txt[:4000], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
def equip_item(call):
    item_key = call.data[6:]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(item_key) or limited_items.get(item_key)
    if not item or item_key not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌ Ошибка!")
        return
    
    type_to_slot = {"weapon": "weapon", "shield": "shield", "armor": "armor",
                    "boots": "boots", "accessory": "accessory"}
    
    slot = type_to_slot.get(item["type"])
    if not slot:
        bot.answer_callback_query(call.id, "❌ Нельзя экипировать!")
        return
    
    old = player.data["equipment"][slot]
    if old:
        player.data["inventory"].append(old)
    
    player.data["equipment"][slot] = item_key
    player.data["inventory"].remove(item_key)
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ {item['name']} экипирован!")
    inventory_show(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("usepot_"))
def use_potion(call):
    item_key = call.data[7:]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(item_key) or limited_items.get(item_key)
    if not item or item_key not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌ Ошибка!")
        return
    
    stats = player.get_stats()
    max_hp = player.data["max_hp"] + stats["hp_bonus"]
    
    if player.data["hp"] >= max_hp:
        bot.answer_callback_query(call.id, "❌ Полное HP!")
        return
    
    heal = item.get("heal", 0)
    player.data["hp"] = min(max_hp, player.data["hp"] + heal)
    player.data["inventory"].remove(item_key)
    player.save()
    
    bot.answer_callback_query(call.id, f"💚 +{heal} HP!")
    bot.send_message(call.message.chat.id,
        f"✅ Использовано: <b>{item['name']}</b>\n❤ HP: {player.data['hp']}/{max_hp}")

# ==================== ХАРАКТЕРИСТИКИ ====================
@bot.message_handler(func=lambda m: m.text == "⚡ Характеристики")
def stats_view(message):
    user_id = message.from_user.id
    player = Player(user_id)
    s = player.data["stats"]
    eq = player.get_stats()
    
    txt = f"""
<b>⚡ ХАРАКТЕРИСТИКИ</b>
Очков: <b>{player.data['stat_points']}</b>

💪 Сила: {s['strength']}
🏃 Ловкость: {s['agility']}
🧠 Интеллект: {s['intelligence']}
❤ Живучесть: {s['vitality']}
🍀 Удача: {s['luck']}

<b>Боевые:</b>
⚔ Урон: {eq['min_damage']}-{eq['max_damage']}
🛡 Защита: {eq['defense']}
💨 Скорость: {eq['speed']}
💥 Крит: {eq['crit_chance']:.1f}%
🔄 Уклонение: {eq['dodge_chance']:.1f}%

❤ HP: {player.data['hp']}/{player.data['max_hp'] + eq['hp_bonus']}
💎 Мана: {player.data['mana']}/{player.data['max_mana']}
"""
    
    if player.data["stat_points"] > 0:
        markup = types.InlineKeyboardMarkup(row_width=5)
        markup.add(
            types.InlineKeyboardButton("💪", callback_data="up_str"),
            types.InlineKeyboardButton("🏃", callback_data="up_agi"),
            types.InlineKeyboardButton("🧠", callback_data="up_int"),
            types.InlineKeyboardButton("❤", callback_data="up_vit"),
            types.InlineKeyboardButton("🍀", callback_data="up_luk")
        )
        txt += "\n<i>Нажмите для повышения:</i>"
        bot.send_message(message.chat.id, txt, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, txt)

@bot.callback_query_handler(func=lambda call: call.data.startswith("up_"))
def upgrade_stat(call):
    stat_map = {"str": "strength", "agi": "agility", "int": "intelligence",
                "vit": "vitality", "luk": "luck"}
    stat_names = {"strength": "Сила", "agility": "Ловкость", "intelligence": "Интеллект",
                  "vitality": "Живучесть", "luck": "Удача"}
    
    stat_key = stat_map[call.data[3:]]
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data["stat_points"] <= 0:
        bot.answer_callback_query(call.id, "❌ Нет очков!")
        return
    
    if player.data["stats"][stat_key] >= 100:
        bot.answer_callback_query(call.id, "❌ Максимум!")
        return
    
    player.data["stats"][stat_key] += 1
    player.data["stat_points"] -= 1
    player.save()
    
    bot.answer_callback_query(call.id, f"⬆ {stat_names[stat_key]}: {player.data['stats'][stat_key]}")
    stats_view(call.message)

# ==================== ВСПОМОГАТЕЛЬНОЕ ====================
def check_level_up(player):
    level = player.data["level"]
    exp_needed = int(100 * (1.5 ** (level - 1)))
    leveled = False
    
    while player.data["exp"] >= exp_needed:
        player.data["exp"] -= exp_needed
        player.data["level"] += 1
        player.data["stat_points"] += 3
        player.data["max_hp"] += 10
        player.data["max_mana"] += 5
        player.data["hp"] = player.data["max_hp"]
        player.data["mana"] = player.data["max_mana"]
        
        titles = {5: "Боец", 10: "Воитель", 15: "Рыцарь", 20: "Ветеран",
                  30: "Мастер", 40: "Грандмастер", 50: "Легенда", 75: "Полубог", 100: "Божество"}
        
        for req, title in titles.items():
            if player.data["level"] >= req and title not in player.data.get("titles", []):
                player.data["title"] = title
        
        level = player.data["level"]
        exp_needed = int(100 * (1.5 ** (level - 1)))
        leveled = True
    
    if leveled:
        player.save()
    return leveled

@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats_show(message):
    user_id = message.from_user.id
    player = Player(user_id)
    d = player.data
    
    wr = (d["wins"] / d["total_duels"] * 100) if d["total_duels"] > 0 else 0
    
    txt = f"""
<b>📊 СТАТИСТИКА</b>

<b>{d['first_name']}</b> | {d['title']}
⭐ Уровень: {d['level']}
📊 PvP Рейтинг: {d['pvp_rating']}
💰 Монет: {d['money']}

<b>Дуэли:</b>
🏆 Побед: {d['wins']}
💀 Поражений: {d['losses']}
🤝 Ничьих: {d['draws']}
📈 Винрейт: {wr:.1f}%
🔥 Лучшая серия: {d['best_streak']}

<b>Урон:</b>
💥 Нанесено: {d['total_damage_dealt']}
🛡 Получено: {d['total_damage_taken']}

✨ Опыт: {d['exp']}/{int(100 * (1.5 ** (d['level'] - 1)))}
🎒 Предметов: {len(d['inventory'])}
✨ Навыков: {len(d['equipped_skills'])}
"""
    bot.send_message(message.chat.id, txt)

@bot.message_handler(func=lambda m: m.text == "🎁 Бонус")
@bot.message_handler(commands=['daily'])
def daily_bonus(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player.data["last_daily"] == today:
        bot.send_message(message.chat.id, "🎁 Уже получен сегодня!")
        return
    
    bonus = random.randint(100, 500) + player.data["level"] * 10
    exp = random.randint(50, 200)
    
    player.data["money"] += bonus
    player.data["exp"] += exp
    player.data["last_daily"] = today
    
    got_item = None
    if random.random() < 0.1:
        common = [k for k, v in items.items() if v.get("rarity") == "common"]
        if common:
            got_item = random.choice(common)
            player.data["inventory"].append(got_item)
    
    check_level_up(player)
    player.save()
    
    txt = f"<b>🎁 ЕЖЕДНЕВНЫЙ БОНУС</b>\n\n💰 +{bonus} монет\n✨ +{exp} опыта"
    if got_item:
        txt += f"\n🎒 +{items[got_item]['name']}"
    
    bot.send_message(message.chat.id, txt)

@bot.message_handler(func=lambda m: m.text == "🏰 Данжи")
def dungeon_main(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    dungeons_list = [
        ("🐺 Логово волка", 1, 50, 150),
        ("🕷 Паучьи пещеры", 5, 100, 300),
        ("💀 Катакомбы", 10, 200, 500),
        ("🐉 Логово дракона", 15, 500, 2000),
        ("👹 Бездна", 25, 1000, 5000)
    ]
    
    txt = "<b>🏰 ПОДЗЕМЕЛЬЯ</b>\n\n"
    for i, (name, req, min_r, max_r) in enumerate(dungeons_list, 1):
        txt += f"{name} (Ур.{req}+): {min_r}-{max_r}💰\n"
        if player.data["level"] >= req:
            markup.add(types.InlineKeyboardButton(name, callback_data=f"dungeon_{i}"))
    
    bot.send_message(message.chat.id, txt, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dungeon_"))
def dungeon_start(call):
    dlevel = int(call.data.split("_")[1])
    user_id = call.from_user.id
    player = Player(user_id)
    
    level_reqs = {1: 1, 2: 5, 3: 10, 4: 15, 5: 25}
    if player.data["level"] < level_reqs[dlevel]:
        bot.answer_callback_query(call.id, f"❌ Нужен {level_reqs[dlevel]} ур.!")
        return
    
    reward = random.randint(50, 150) * dlevel * player.data["level"]
    exp = 50 * dlevel * player.data["level"]
    
    player.data["money"] += reward
    player.data["exp"] += exp
    check_level_up(player)
    player.save()
    
    bot.edit_message_text(
        f"🏰 Данж пройден!\n💰 +{reward} монет\n✨ +{exp} опыта",
        call.message.chat.id, call.message.message_id
    )
    bot.answer_callback_query(call.id, "✅ Пройдено!")

# ==================== АДМИН ====================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
        types.InlineKeyboardButton("💰 Выдать", callback_data="adm_money"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("❌ Бан", callback_data="adm_ban")
    )
    bot.send_message(message.chat.id, "<b>🔧 АДМИН</b>", reply_markup=markup)

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    
    text = message.text.replace('/broadcast', '', 1).strip()
    if not text:
        bot.send_message(message.chat.id, "❌ /broadcast [текст]")
        return
    
    ok, fail = 0, 0
    for uid in list(users.keys())[:100]:
        try:
            bot.send_message(int(uid), f"📢 {text}")
            ok += 1
        except: fail += 1
    
    bot.send_message(message.chat.id, f"✅ {ok} | ❌ {fail}")

# ==================== ЗАПУСК ====================
def main():
    print("="*60)
    print("⚔️ ДУЭЛЬ БОТ - СТРАТЕГИЧЕСКАЯ БИТВА ⚔️")
    print("="*60)
    print("✅ Системы: Пошаговые дуэли, Навыки, Магазин, Данжи")
    print("✅ 30+ навыков, Элементы, Статус-эффекты")
    print("✅ Стратегический выбор действий каждый ход")
    print("="*60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
