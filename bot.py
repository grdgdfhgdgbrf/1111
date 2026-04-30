import telebot
from telebot import types
import json
import random
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict
import math
import copy
import uuid
import re

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = '8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE'
ADMIN_ID = 5356400377
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ==================== КОНСТАНТЫ ====================
BODY_PARTS = {
    "head": {"name": "👤 Голова", "multiplier": 1.5, "hit_chance": 20, "defense_bonus": 0},
    "body": {"name": "🦾 Тело", "multiplier": 1.0, "hit_chance": 50, "defense_bonus": 0},
    "legs": {"name": "🦿 Ноги", "multiplier": 0.7, "hit_chance": 30, "defense_bonus": 0, "speed_penalty": 5}
}

EQUIPMENT_SLOTS = {
    "head": {"name": "👤 Голова", "item_type": "helmet"},
    "body": {"name": "🦾 Тело", "item_type": "armor"},
    "legs": {"name": "🦿 Ноги", "item_type": "boots"}
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
    "fire": {"name": "🔥 Огонь", "strong": "ice", "weak": "water", "effect": "burn", "effect_name": "Горение"},
    "ice": {"name": "❄ Лёд", "strong": "nature", "weak": "fire", "effect": "freeze", "effect_name": "Заморозка"},
    "lightning": {"name": "⚡ Молния", "strong": "water", "weak": "earth", "effect": "stun", "effect_name": "Оглушение"},
    "water": {"name": "🌊 Вода", "strong": "fire", "weak": "lightning", "effect": "soak", "effect_name": "Промокание"},
    "nature": {"name": "🌿 Природа", "strong": "earth", "weak": "ice", "effect": "poison", "effect_name": "Отравление"},
    "earth": {"name": "🏔 Земля", "strong": "lightning", "weak": "nature", "effect": "bleed", "effect_name": "Кровотечение"},
    "dark": {"name": "🌑 Тьма", "strong": "light", "weak": "light", "effect": "curse", "effect_name": "Проклятие"},
    "light": {"name": "✨ Свет", "strong": "dark", "weak": "dark", "effect": "bless", "effect_name": "Благословение"}
}

STATUS_EFFECTS = {
    "burn": {"name": "🔥 Горение", "damage_per_turn": 12, "duration": 3, "stat_penalty": {"defense": -5}},
    "freeze": {"name": "❄ Заморозка", "skip_turn_chance": 40, "duration": 2, "stat_penalty": {"speed": -10}},
    "stun": {"name": "⚡ Оглушение", "skip_turn": True, "duration": 1},
    "poison": {"name": "☠ Отравление", "damage_per_turn": 15, "duration": 4, "stat_penalty": {"strength": -3}},
    "bleed": {"name": "🩸 Кровотечение", "damage_per_turn": 10, "duration": 3, "stat_penalty": {"vitality": -3}},
    "curse": {"name": "👁 Проклятие", "damage_per_turn": 8, "duration": 5, "stat_penalty": {"luck": -5}},
    "bless": {"name": "✨ Благословение", "heal_per_turn": 10, "duration": 3, "stat_bonus": {"all": 3}},
    "soak": {"name": "💧 Промокание", "lightning_vulnerability": True, "duration": 3},
    "shield": {"name": "🛡 Щит", "damage_reduction": 30, "duration": 2},
    "rage": {"name": "💢 Ярость", "damage_bonus": 25, "duration": 3, "defense_penalty": -10}
}

# ==================== ФАЙЛЫ ДАННЫХ ====================
DATA_FILES = {
    'users': 'users.json',
    'items': 'items.json',
    'limited': 'limited_items.json',
    'duels': 'active_duels.json',
    'clans': 'clans.json',
    'tournaments': 'tournaments.json',
    'market': 'market.json',
    'dungeons': 'dungeon_progress.json',
    'events': 'events.json',
    'bans': 'bans.json',
    'quests': 'quests_progress.json',
    'battle_history': 'battle_history.json'
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

# ==================== ПРЕДМЕТЫ ПО СЛОТАМ ====================
HELMETS = {
    "leather_cap": {
        "name": "🎓 Кожаная шапка", "defense": 3, "hp_bonus": 10, "price": 60,
        "type": "helmet", "slot": "head", "rarity": "common", "level_req": 1,
        "skills": [],
        "special_effects": {},
        "description": "Простая защита головы"
    },
    "iron_helmet": {
        "name": "⛑ Железный шлем", "defense": 8, "hp_bonus": 20, "price": 250,
        "type": "helmet", "slot": "head", "rarity": "uncommon", "level_req": 6,
        "skills": ["headbutt"],
        "special_effects": {"stun_resist": 15},
        "description": "Надёжный железный шлем"
    },
    "dragon_helmet": {
        "name": "🐉 Шлем дракона", "defense": 18, "hp_bonus": 50, "price": 2000,
        "type": "helmet", "slot": "head", "rarity": "epic", "level_req": 20,
        "skills": ["dragon_roar", "fire_breath"],
        "special_effects": {"fire_resist": 25, "intimidation": 15},
        "element": "fire",
        "description": "Шлем из черепа дракона"
    },
    "crown_of_wisdom": {
        "name": "👑 Корона мудрости", "defense": 12, "hp_bonus": 35, "mana_bonus": 40, "price": 3500,
        "type": "helmet", "slot": "head", "rarity": "legendary", "level_req": 28,
        "skills": ["mind_blast", "telepathy"],
        "special_effects": {"mana_regen": 5, "spell_power": 20},
        "description": "Увеличивает магическую силу"
    }
}

ARMORS = {
    "leather_vest": {
        "name": "🧥 Кожаный жилет", "defense": 5, "hp_bonus": 25, "price": 80,
        "type": "armor", "slot": "body", "rarity": "common", "level_req": 1,
        "skills": ["dodge"],
        "special_effects": {},
        "description": "Лёгкая защита тела"
    },
    "chainmail": {
        "name": "⛓ Кольчуга", "defense": 12, "hp_bonus": 50, "price": 400,
        "type": "armor", "slot": "body", "rarity": "uncommon", "level_req": 8,
        "skills": ["fortify", "endure"],
        "special_effects": {"physical_resist": 10},
        "description": "Надёжная кольчуга"
    },
    "plate_armor": {
        "name": "🛡 Латный доспех", "defense": 22, "hp_bonus": 90, "price": 1500,
        "type": "armor", "slot": "body", "rarity": "rare", "level_req": 15,
        "skills": ["iron_will", "bastion", "reinforce"],
        "special_effects": {"damage_reduction": 15},
        "description": "Тяжёлые латы рыцаря"
    },
    "shadow_armor": {
        "name": "🌑 Теневая броня", "defense": 28, "hp_bonus": 120, "price": 3500,
        "type": "armor", "slot": "body", "rarity": "epic", "level_req": 22,
        "skills": ["shadow_step", "vanish", "dark_mantle"],
        "special_effects": {"dodge_boost": 15, "darkness_cloak": True},
        "element": "dark",
        "description": "Скрывает в тенях"
    },
    "phoenix_armor": {
        "name": "🦅 Броня феникса", "defense": 40, "hp_bonus": 200, "price": 8000,
        "type": "armor", "slot": "body", "rarity": "legendary", "level_req": 30,
        "skills": ["rebirth", "phoenix_flame", "fire_immunity"],
        "special_effects": {"rebirth_chance": 20, "fire_heal": 30},
        "element": "fire",
        "description": "Возрождает из пепла"
    }
}

BOOTS = {
    "leather_boots": {
        "name": "👢 Кожаные сапоги", "defense": 2, "speed": 8, "price": 100,
        "type": "boots", "slot": "legs", "rarity": "common", "level_req": 1,
        "skills": ["kick"],
        "special_effects": {},
        "description": "+8 к скорости"
    },
    "iron_boots": {
        "name": "🥾 Железные сапоги", "defense": 6, "speed": 4, "price": 300,
        "type": "boots", "slot": "legs", "rarity": "uncommon", "level_req": 7,
        "skills": ["stomp", "heavy_kick"],
        "special_effects": {"knockback_resist": 15},
        "description": "Тяжёлые, но прочные"
    },
    "wind_boots": {
        "name": "🌪 Сапоги ветра", "defense": 4, "speed": 18, "price": 900,
        "type": "boots", "slot": "legs", "rarity": "rare", "level_req": 12,
        "skills": ["tailwind", "gust_kick"],
        "special_effects": {"dodge_boost": 10, "move_first_chance": 20},
        "description": "Невероятно быстрые"
    },
    "blink_boots": {
        "name": "✨ Сапоги телепортации", "defense": 8, "speed": 28, "price": 4000,
        "type": "boots", "slot": "legs", "rarity": "epic", "level_req": 25,
        "skills": ["blink", "phase_kick", "teleport_strike"],
        "special_effects": {"blink_chance": 20, "avoid_trap": True},
        "description": "Мгновенное перемещение"
    },
    "hermes_boots": {
        "name": "👟 Сандалии Гермеса", "defense": 12, "speed": 45, "price": 12000,
        "type": "boots", "slot": "legs", "rarity": "legendary", "level_req": 35,
        "skills": ["divine_speed", "double_kick", "mercury_strike"],
        "special_effects": {"speed_boost": 20, "first_strike": True, "double_turn_chance": 15},
        "description": "Скорость бога"
    }
}

WEAPONS = {
    "rusty_sword": {
        "name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50,
        "type": "weapon", "rarity": "common", "level_req": 1,
        "skills": ["slash", "quick_strike"],
        "special_effects": {},
        "element": None,
        "description": "Старый ржавый меч"
    },
    "hunters_bow": {
        "name": "🏹 Лук охотника", "damage": (7, 14), "price": 150,
        "type": "weapon", "rarity": "common", "level_req": 3,
        "skills": ["power_shot", "multi_shot", "aimed_shot"],
        "special_effects": {"range_attack": True},
        "element": "nature",
        "description": "Надёжный лук для охоты"
    },
    "flame_blade": {
        "name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500,
        "type": "weapon", "rarity": "uncommon", "level_req": 7,
        "skills": ["fire_slash", "inferno_strike", "flame_wave"],
        "special_effects": {"burn_on_hit": 25},
        "element": "fire",
        "description": "Клинок, объятый пламенем"
    },
    "frost_axe": {
        "name": "❄ Ледяной топор", "damage": (14, 24), "price": 800,
        "type": "weapon", "rarity": "uncommon", "level_req": 10,
        "skills": ["frost_strike", "ice_shatter", "blizzard"],
        "special_effects": {"freeze_on_hit": 20},
        "element": "ice",
        "description": "Замораживает противников"
    },
    "storm_staff": {
        "name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500,
        "type": "weapon", "rarity": "rare", "level_req": 14,
        "skills": ["lightning_bolt", "thunder_storm", "chain_lightning", "static_field"],
        "special_effects": {"chain_damage": 30, "stun_on_hit": 15},
        "element": "lightning",
        "description": "Призывает молнии"
    },
    "tidal_blade": {
        "name": "🌊 Приливной клинок", "damage": (20, 32), "price": 2500,
        "type": "weapon", "rarity": "rare", "level_req": 18,
        "skills": ["water_slash", "tsunami", "drown", "healing_wave"],
        "special_effects": {"heal_on_hit": 15, "soak_chance": 25},
        "element": "water",
        "description": "Волны сокрушают врагов"
    },
    "shadow_dagger": {
        "name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000,
        "type": "weapon", "rarity": "epic", "level_req": 22,
        "skills": ["shadow_strike", "assassinate", "dark_veil", "soul_drain"],
        "special_effects": {"poison_on_hit": 20, "life_steal": 15},
        "element": "dark",
        "description": "Атакует из тьмы"
    },
    "divine_spear": {
        "name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000,
        "type": "weapon", "rarity": "legendary", "level_req": 28,
        "skills": ["holy_strike", "divine_judgment", "heavenly_light", "purification"],
        "special_effects": {"holy_damage": 25, "bless_chance": 20},
        "element": "light",
        "description": "Оружие небесных воинов"
    },
    "death_scythe": {
        "name": "💀 Коса смерти", "damage": (40, 65), "price": 12000,
        "type": "weapon", "rarity": "mythic", "level_req": 35,
        "skills": ["reap", "death_sentence", "soul_harvest", "darkness_falls"],
        "special_effects": {"curse_on_hit": 30, "execution": 10, "soul_steal": True},
        "element": "dark",
        "description": "Забирает души"
    }
}

POTIONS = {
    "health_potion": {
        "name": "🧪 Зелье здоровья", "heal": 40, "price": 40,
        "type": "potion", "rarity": "common", "level_req": 1,
        "description": "Восстанавливает 40 HP"
    },
    "big_health_potion": {
        "name": "🧪 Большое зелье", "heal": 90, "price": 120,
        "type": "potion", "rarity": "uncommon", "level_req": 8,
        "description": "Восстанавливает 90 HP"
    },
    "elixir_of_life": {
        "name": "💊 Эликсир жизни", "heal": 200, "price": 350,
        "type": "potion", "rarity": "rare", "level_req": 15,
        "description": "Полное восстановление"
    },
    "mana_potion": {
        "name": "💎 Зелье маны", "mana_restore": 60, "price": 60,
        "type": "potion", "rarity": "common", "level_req": 5,
        "description": "Восстанавливает 60 MP"
    },
    "berserk_potion": {
        "name": "💢 Зелье ярости", "price": 200, "type": "potion",
        "rarity": "rare", "level_req": 12,
        "effects": {"damage_boost": 50, "duration": 3},
        "description": "+50% урона на 3 хода"
    },
    "invisibility_potion": {
        "name": "👻 Зелье невидимости", "price": 500, "type": "potion",
        "rarity": "epic", "level_req": 20,
        "effects": {"dodge_boost": 40, "duration": 2},
        "description": "+40% уклонения на 2 хода"
    },
    "antidote": {
        "name": "💚 Противоядие", "price": 100, "type": "potion",
        "rarity": "common", "level_req": 1,
        "effects": {"cure_poison": True, "cure_bleed": True},
        "description": "Снимает яд и кровотечение"
    }
}

LIMITED_ITEMS = {
    "thunderfury": {
        "name": "⚡ Ярость грома", "damage": (60, 95), "total": 3,
        "remaining": 3, "price": 50000, "type": "weapon",
        "rarity": "divine", "element": "lightning",
        "skills": ["thunder_gods_wrath", "eye_of_the_storm", "lightning_apocalypse", "zeus_fury"],
        "special_effects": {"chain_lightning": 40, "stun_on_hit": 30, "lightning_immunity": True},
        "description": "Меч бога грома"
    },
    "apocalypse": {
        "name": "🌋 Апокалипсис", "damage": (80, 140), "total": 1,
        "remaining": 1, "price": 100000, "type": "weapon",
        "rarity": "apocalyptic", "element": "dark",
        "skills": ["world_ender", "obliterate", "void_annihilation", "absolute_zero"],
        "special_effects": {"armageddon": 50, "soul_destroy": True, "unstoppable": True},
        "description": "Конец всего сущего"
    },
    "immortal_helmet": {
        "name": "✨ Шлем бессмертия", "defense": 80, "hp_bonus": 300, "total": 2,
        "remaining": 2, "price": 75000, "type": "helmet", "slot": "head",
        "rarity": "divine",
        "skills": ["immortality", "mind_shield", "divine_vision"],
        "special_effects": {"death_prevent": True, "see_invisible": True},
        "description": "Защищает от смерти"
    },
    "cloak_of_infinity": {
        "name": "🌀 Плащ бесконечности", "defense": 60, "hp_bonus": 500, "total": 4,
        "remaining": 4, "price": 60000, "type": "armor", "slot": "body",
        "rarity": "divine",
        "skills": ["infinity", "cosmic_armor", "reality_warp", "time_stop"],
        "special_effects": {"infinity_guard": 40, "cosmic_power": 30},
        "description": "Бесконечная защита"
    }
}

# Объединение всех предметов
ALL_ITEMS = {}
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(BOOTS)
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(POTIONS)

# Загрузка данных
items = load_json(DATA_FILES['items'], ALL_ITEMS)
limited_items = load_json(DATA_FILES['limited'], LIMITED_ITEMS)
users = load_json(DATA_FILES['users'], {})
active_duels_data = load_json(DATA_FILES['duels'], {})
clans = load_json(DATA_FILES['clans'], {})
tournaments = load_json(DATA_FILES['tournaments'], {})
market_listings = load_json(DATA_FILES['market'], {})
dungeon_progress = load_json(DATA_FILES['dungeons'], {})
events = load_json(DATA_FILES['events'], {})
banned_users = load_json(DATA_FILES['bans'], {})
quests_progress = load_json(DATA_FILES['quests'], {})
battle_history_data = load_json(DATA_FILES['battle_history'], {})

# ==================== БАЗА НАВЫКОВ ====================
SKILLS_DB = {
    # Базовые атаки
    "quick_attack": {
        "name": "⚡ Быстрая атака", "damage_mult": 1.0, "mana_cost": 0,
        "cooldown": 0, "category": "attack", "target": "random",
        "description": "Базовая быстрая атака"
    },
    "heavy_attack": {
        "name": "💪 Тяжёлая атака", "damage_mult": 1.7, "mana_cost": 15,
        "cooldown": 1, "category": "attack", "target": "random",
        "description": "Мощная атака"
    },
    "defend": {
        "name": "🛡 Защита", "defense_boost": 25, "mana_cost": 8,
        "cooldown": 1, "category": "defense", "target": "self",
        "description": "Усиливает защиту"
    },
    "meditate": {
        "name": "🧘 Медитация", "mana_restore": 35, "cooldown": 2,
        "category": "support", "target": "self",
        "description": "Восстанавливает ману"
    },
    "focus": {
        "name": "🎯 Концентрация", "crit_boost": 25, "mana_cost": 12,
        "cooldown": 2, "category": "support", "target": "self",
        "description": "Повышает шанс крита"
    },
    "first_aid": {
        "name": "💊 Первая помощь", "hp_restore": 50, "mana_cost": 18,
        "cooldown": 2, "category": "support", "target": "self",
        "description": "Лечит раны"
    },
    
    # Атаки по частям тела
    "headbutt": {
        "name": "💢 Удар головой", "damage_mult": 1.3, "mana_cost": 10,
        "cooldown": 1, "category": "attack", "target": "head", "stun_chance": 20,
        "description": "Атака в голову, шанс оглушить"
    },
    "slash": {
        "name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 8,
        "cooldown": 0, "category": "attack", "target": "body",
        "description": "Удар по телу"
    },
    "kick": {
        "name": "👢 Пинок", "damage_mult": 0.9, "mana_cost": 5,
        "cooldown": 0, "category": "attack", "target": "legs", "slow_chance": 15,
        "description": "Удар по ногам, шанс замедлить"
    },
    
    # Специальные атаки
    "fire_slash": {
        "name": "🔥 Огненный разрез", "damage_mult": 1.5, "mana_cost": 20,
        "element": "fire", "burn_chance": 30, "cooldown": 1, "category": "attack", "target": "body",
        "description": "Удар с пламенем"
    },
    "inferno_strike": {
        "name": "🌋 Инферно удар", "damage_mult": 2.3, "mana_cost": 38,
        "element": "fire", "burn_chance": 60, "cooldown": 3, "category": "attack", "target": "body",
        "description": "Мощнейшая огненная атака"
    },
    "frost_strike": {
        "name": "❄ Ледяной удар", "damage_mult": 1.4, "mana_cost": 18,
        "element": "ice", "freeze_chance": 25, "cooldown": 0, "category": "attack", "target": "body",
        "description": "Замораживающий удар"
    },
    "ice_shatter": {
        "name": "💠 Ледяной раскол", "damage_mult": 2.0, "mana_cost": 32,
        "element": "ice", "freeze_chance": 50, "cooldown": 2, "category": "attack", "target": "head",
        "description": "Разбивает лёд"
    },
    "lightning_bolt": {
        "name": "⚡ Молния", "damage_mult": 1.6, "mana_cost": 22,
        "element": "lightning", "stun_chance": 20, "cooldown": 0, "category": "attack", "target": "head",
        "description": "Разряд молнии"
    },
    "thunder_storm": {
        "name": "⛈ Грозовой шторм", "damage_mult": 2.5, "mana_cost": 45,
        "element": "lightning", "stun_chance": 35, "cooldown": 3, "category": "attack", "target": "all",
        "description": "Вызывает грозу"
    },
    "shadow_strike": {
        "name": "🌑 Теневой удар", "damage_mult": 1.7, "mana_cost": 24,
        "element": "dark", "poison_chance": 25, "cooldown": 0, "category": "attack", "target": "body",
        "description": "Удар из тени"
    },
    "assassinate": {
        "name": "🗡 Убийство", "damage_mult": 3.5, "mana_cost": 60,
        "element": "dark", "cooldown": 4, "ignore_defense": 50, "category": "attack", "target": "head",
        "description": "Смертельный удар в голову"
    },
    "soul_drain": {
        "name": "💀 Похищение души", "damage_mult": 2.2, "mana_cost": 40,
        "element": "dark", "life_steal": 0.4, "cooldown": 3, "category": "attack", "target": "body",
        "description": "Крадёт жизнь"
    },
    "holy_strike": {
        "name": "✨ Святой удар", "damage_mult": 1.6, "mana_cost": 22,
        "element": "light", "cooldown": 0, "category": "attack", "target": "body",
        "description": "Удар светом"
    },
    "divine_judgment": {
        "name": "⚖ Божий суд", "damage_mult": 3.0, "mana_cost": 50,
        "element": "light", "cooldown": 3, "category": "attack", "target": "all",
        "description": "Мощная святая атака"
    },
    
    # Защитные
    "shield_wall": {
        "name": "🧱 Стена щитов", "defense_boost": 50, "mana_cost": 28,
        "cooldown": 2, "category": "defense", "target": "self",
        "description": "Мощная защита"
    },
    "counter_attack": {
        "name": "↩ Контратака", "damage_mult": 1.5, "mana_cost": 22,
        "reflect_damage": 0.3, "cooldown": 2, "category": "defense", "target": "body",
        "description": "Отражает урон"
    },
    "divine_protection": {
        "name": "💫 Божественная защита", "defense_boost": 80, "mana_cost": 45,
        "cooldown": 3, "category": "defense", "target": "self",
        "description": "Сильнейшая защита"
    },
    
    # Ультимейты
    "thunder_gods_wrath": {
        "name": "⚡ Гнев бога грома", "damage_mult": 4.5, "mana_cost": 85,
        "element": "lightning", "stun_chance": 50, "cooldown": 5, "category": "attack", "target": "all",
        "description": "УЛЬТИМАТИВНАЯ АТАКА"
    },
    "world_ender": {
        "name": "🌋 Конец света", "damage_mult": 5.5, "mana_cost": 100,
        "element": "dark", "cooldown": 6, "ignore_defense": 100, "category": "attack", "target": "all",
        "description": "АБСОЛЮТНОЕ УНИЧТОЖЕНИЕ"
    }
}

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
                "stats": {
                    "strength": 5, "agility": 5, "intelligence": 5,
                    "vitality": 5, "luck": 5, "defense": 0
                },
                "stat_points": 0,
                "wins": 0, "losses": 0, "draws": 0,
                "win_streak": 0, "best_streak": 0,
                "total_duels": 0, "pvp_rating": 1000,
                "total_damage_dealt": 0, "total_damage_taken": 0,
                "critical_hits": 0, "skills_used": 0,
                "inventory": [],
                "equipment": {"weapon": None, "head": None, "body": None, "legs": None},
                "last_daily": None, "last_dungeon": None, "last_work": None,
                "title": "Новичок",
                "titles_collected": ["Новичок"],
                "achievements": [],
                "active_quests": {},
                "completed_quests": 0,
                "clan": None, "clan_role": None,
                "tournament_wins": 0,
                "registration_date": datetime.now().isoformat(),
                "settings": {"notifications": True, "duel_requests": True, "show_battle_log": True},
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
    
    def get_full_stats(self):
        """Полный расчёт характеристик с учётом экипировки"""
        base = copy.deepcopy(self.data["stats"])
        bonuses = {
            "min_damage": base["strength"] * 2,
            "max_damage": base["strength"] * 3,
            "defense": base["defense"] + base["vitality"] * 2,
            "speed": base["agility"] * 1.5,
            "crit_chance": 5 + base["luck"] * 0.5,
            "crit_multiplier": 1.5,
            "dodge_chance": 3 + base["agility"] * 0.3,
            "hp": self.data["max_hp"] + base["vitality"] * 15,
            "max_hp": self.data["max_hp"] + base["vitality"] * 15,
            "mana": self.data["max_mana"] + base["intelligence"] * 8,
            "max_mana": self.data["max_mana"] + base["intelligence"] * 8,
            "life_steal": 0,
            "damage_reflect": 0,
            "elemental_bonus": {},
            "head_defense": 0,
            "body_defense": 0,
            "legs_defense": 0
        }
        
        # Обработка экипировки по слотам
        for slot, item_key in self.data["equipment"].items():
            if not item_key:
                continue
            item = items.get(item_key) or limited_items.get(item_key)
            if not item:
                continue
            
            if item.get("type") == "weapon":
                if "damage" in item:
                    bonuses["min_damage"] += item["damage"][0]
                    bonuses["max_damage"] += item["damage"][1]
                if "element" in item and item["element"]:
                    bonuses["elemental_bonus"][item["element"]] = bonuses["elemental_bonus"].get(item["element"], 0) + 20
                for effect, value in item.get("special_effects", {}).items():
                    if effect == "life_steal":
                        bonuses["life_steal"] += value
                    elif effect == "burn_on_hit":
                        bonuses.setdefault("burn_chance", 0)
                        bonuses["burn_chance"] += value
                    elif effect == "freeze_on_hit":
                        bonuses.setdefault("freeze_chance", 0)
                        bonuses["freeze_chance"] += value
            
            elif item.get("slot") == "head":
                bonuses["head_defense"] += item.get("defense", 0)
                bonuses["max_hp"] += item.get("hp_bonus", 0)
                bonuses["max_mana"] += item.get("mana_bonus", 0)
                bonuses["defense"] += item.get("defense", 0)
            
            elif item.get("slot") == "body":
                bonuses["body_defense"] += item.get("defense", 0)
                bonuses["max_hp"] += item.get("hp_bonus", 0)
                bonuses["defense"] += item.get("defense", 0)
                for effect, value in item.get("special_effects", {}).items():
                    if effect == "dodge_boost":
                        bonuses["dodge_chance"] += value
                    elif effect == "damage_reduction":
                        bonuses.setdefault("damage_reduction", 0)
                        bonuses["damage_reduction"] += value
            
            elif item.get("slot") == "legs":
                bonuses["legs_defense"] += item.get("defense", 0)
                bonuses["speed"] += item.get("speed", 0)
                bonuses["defense"] += item.get("defense", 0)
                for effect, value in item.get("special_effects", {}).items():
                    if effect == "dodge_boost":
                        bonuses["dodge_chance"] += value
                    elif effect == "move_first_chance":
                        bonuses.setdefault("first_strike_chance", 0)
                        bonuses["first_strike_chance"] += value
        
        bonuses["hp"] = bonuses["max_hp"]
        bonuses["mana"] = bonuses["max_mana"]
        bonuses["crit_chance"] = min(80, bonuses["crit_chance"])
        bonuses["dodge_chance"] = min(50, bonuses["dodge_chance"])
        
        return bonuses

# ==================== ПОШАГОВАЯ БОЕВАЯ СИСТЕМА С ВЫБОРОМ ЧАСТЕЙ ТЕЛА ====================
class AdvancedDuel:
    def __init__(self, player1_id, player2_id, duel_type="quick", bet=0):
        self.battle_id = str(uuid.uuid4())[:8]
        self.p1_id = str(player1_id)
        self.p2_id = str(player2_id)
        self.duel_type = duel_type
        self.bet = bet
        self.turn = 1
        self.max_turns = 40
        self.active = True
        self.winner = None
        self.battle_log = []
        
        # Игроки
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        # Статы
        self.p1_stats = self.p1.get_full_stats()
        self.p2_stats = self.p2.get_full_stats()
        
        # HP и MP
        self.p1_hp = self.p1_stats["max_hp"]
        self.p2_hp = self.p2_stats["max_hp"]
        self.p1_max_hp = self.p1_hp
        self.p2_max_hp = self.p2_hp
        
        self.p1_mp = self.p1_stats["max_mana"]
        self.p2_mp = self.p2_stats["max_mana"]
        self.p1_max_mp = self.p1_mp
        self.p2_max_mp = self.p2_mp
        
        # Защита частей тела
        self.p1_defending = None
        self.p2_defending = None
        
        # Статус фазы (attack_target - выбор цели, attack_skill - выбор навыка)
        self.p1_phase = "defend_select"  # defend_select, attack_target, attack_skill
        self.p2_phase = "defend_select"
        
        self.p1_target = None
        self.p2_target = None
        self.p1_skill = None
        self.p2_skill = None
        
        # Определение первого хода
        p1_speed = self.p1_stats["speed"] + random.randint(-10, 10)
        p2_speed = self.p2_stats["speed"] + random.randint(-10, 10)
        
        if p1_speed >= p2_speed:
            self.current_player = 1
        else:
            self.current_player = 2
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Активные эффекты
        self.p1_effects = []
        self.p2_effects = []
        
        # Временные баффы
        self.p1_buffs = {"defense": 0, "damage": 0, "crit": 0, "dodge": 0, "speed": 0}
        self.p2_buffs = {"defense": 0, "damage": 0, "crit": 0, "dodge": 0, "speed": 0}
        
        # Погода и арена
        self.arena = random.choice(["colosseum", "forest", "volcano", "tundra", "void", "temple"])
        self.weather = random.choice(["clear", "rain", "storm", "fog", "eclipse", "blizzard"])
        
        self._save_active_duel()
        
        self.battle_log.append(f"⚔ <b>БИТВА НАЧАЛАСЬ!</b>")
        self.battle_log.append(f"🏟 Арена: <b>{self._arena_name()}</b>")
        self.battle_log.append(f"🌤 Погода: <b>{self._weather_name()}</b>")
    
    def _arena_name(self):
        return {
            "colosseum": "Колизей", "forest": "Лес", "volcano": "Вулкан",
            "tundra": "Тундра", "void": "Пустота", "temple": "Храм"
        }.get(self.arena, self.arena)
    
    def _weather_name(self):
        return {
            "clear": "Ясно", "rain": "Дождь", "storm": "Шторм",
            "fog": "Туман", "eclipse": "Затмение", "blizzard": "Буран"
        }.get(self.weather, self.weather)
    
    def _save_active_duel(self):
        active_duels_data[self.battle_id] = {
            "p1_id": self.p1_id, "p2_id": self.p2_id,
            "type": self.duel_type, "bet": self.bet,
            "current_player": self.current_player,
            "turn": self.turn, "started_at": datetime.now().isoformat(),
            "p1_phase": self.p1_phase, "p2_phase": self.p2_phase
        }
        save_json(DATA_FILES['duels'], active_duels_data)
    
    def get_player_name(self, player_num):
        if player_num == 1:
            return self.p1.data["first_name"]
        return self.p2.data["first_name"]
    
    def get_available_skills(self, player_num):
        """Получить доступные навыки"""
        player = self.p1 if player_num == 1 else self.p2
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        equipment = player.data["equipment"]
        
        available = []
        
        # Базовые навыки
        base_skills = ["quick_attack", "heavy_attack", "defend", "meditate", "focus", "first_aid"]
        for skill_id in base_skills:
            if skill_id not in cooldowns or cooldowns[skill_id] <= 0:
                available.append(skill_id)
        
        # Навыки от экипировки
        for slot in ["weapon", "head", "body", "legs"]:
            item_key = equipment.get(slot)
            if not item_key:
                continue
            item = items.get(item_key) or limited_items.get(item_key)
            if item and "skills" in item:
                for skill_id in item["skills"]:
                    if skill_id in SKILLS_DB:
                        cd = cooldowns.get(skill_id, 0)
                        if cd <= 0:
                            available.append(skill_id)
        
        return list(set(available))
    
    def set_defend_part(self, player_num, body_part):
        """Установить защищаемую часть тела"""
        if player_num == 1:
            self.p1_defending = body_part
            self.p1_phase = "attack_target"
        else:
            self.p2_defending = body_part
            self.p2_phase = "attack_target"
        self._save_active_duel()
    
    def set_attack_target(self, player_num, body_part):
        """Установить цель атаки"""
        if player_num == 1:
            self.p1_target = body_part
            self.p1_phase = "attack_skill"
        else:
            self.p2_target = body_part
            self.p2_phase = "attack_skill"
        self._save_active_duel()
    
    def execute_attack(self, player_num, skill_id):
        """Выполнить атаку с выбранным навыком"""
        if not self.active:
            return "Бой завершён"
        
        attacker = player_num
        defender = 3 - player_num
        
        # Сохраняем навык
        if attacker == 1:
            self.p1_skill = skill_id
            self.p1_phase = "done"
        else:
            self.p2_skill = skill_id
            self.p2_phase = "done"
        
        # Проверяем, готовы ли оба игрока
        if self.p1_phase == "done" and self.p2_phase == "done":
            self._resolve_turn()
            self._reset_phases()
        
        self._save_active_duel()
        return "Атака выбрана!"
    
    def _reset_phases(self):
        """Сброс фаз для нового хода"""
        self.p1_phase = "defend_select"
        self.p2_phase = "defend_select"
        self.p1_defending = None
        self.p2_defending = None
        self.p1_target = None
        self.p2_target = None
        self.p1_skill = None
        self.p2_skill = None
    
    def _resolve_turn(self):
        """Разрешение хода — обработка действий обоих игроков"""
        # Обработка эффектов
        self._process_effects(1)
        self._process_effects(2)
        
        # Очерёдность атаки
        p1_speed = self.p1_stats["speed"] + self.p1_buffs["speed"]
        p2_speed = self.p2_stats["speed"] + self.p2_buffs["speed"]
        
        if p1_speed >= p2_speed:
            first, second = (1, 2)
        else:
            first, second = (2, 1)
        
        # Первая атака
        self._perform_attack(first, second)
        
        # Проверка смерти
        if self.p1_hp <= 0 or self.p2_hp <= 0:
            self._check_end()
            return
        
        # Вторая атака
        self._perform_attack(second, first)
        
        # Проверка смерти
        self._check_end()
        
        # Уменьшение баффов
        self._decay_buffs()
        
        self.turn += 1
        
        if self.turn > self.max_turns:
            self.active = False
            self.winner = 0
    
    def _perform_attack(self, attacker, defender):
        """Выполнить атаку одного игрока"""
        skill_id = self.p1_skill if attacker == 1 else self.p2_skill
        target_part = self.p1_target if attacker == 1 else self.p2_target
        defend_part = self.p2_defending if attacker == 1 else self.p1_defending
        
        if not skill_id:
            skill_id = "quick_attack"
        if not target_part:
            target_part = "body"
        
        skill = SKILLS_DB.get(skill_id, {"name": "Атака", "damage_mult": 1.0, "mana_cost": 0})
        
        # Данные атакующего
        attacker_player = self.p1 if attacker == 1 else self.p2
        attacker_stats = self.p1_stats if attacker == 1 else self.p2_stats
        attacker_buffs = self.p1_buffs if attacker == 1 else self.p2_buffs
        attacker_cooldowns = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
        
        # Данные защищающегося
        defender_stats = self.p2_stats if attacker == 1 else self.p1_stats
        defender_buffs = self.p2_buffs if attacker == 1 else self.p1_buffs
        
        # Проверка маны
        mana_cost = skill.get("mana_cost", 0)
        if attacker == 1:
            if self.p1_mp < mana_cost:
                self.battle_log.append(f"❌ {self.get_player_name(attacker)}: недостаточно маны!")
                return
            self.p1_mp -= mana_cost
        else:
            if self.p2_mp < mana_cost:
                self.battle_log.append(f"❌ {self.get_player_name(attacker)}: недостаточно маны!")
                return
            self.p2_mp -= mana_cost
        
        # Расчёт урона
        min_dmg = int(attacker_stats["min_damage"] * (1 + attacker_buffs["damage"] / 100))
        max_dmg = int(attacker_stats["max_damage"] * (1 + attacker_buffs["damage"] / 100))
        base_damage = random.randint(min_dmg, max_dmg)
        damage = int(base_damage * skill.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_mult = BODY_PARTS.get(target_part, {}).get("multiplier", 1.0)
        damage = int(damage * body_mult)
        
        # Проверка защиты части тела
        if defend_part == target_part:
            defense_bonus = 20
            if defend_part == "head":
                defense_bonus += defender_stats["head_defense"]
            elif defend_part == "body":
                defense_bonus += defender_stats["body_defense"]
            elif defend_part == "legs":
                defense_bonus += defender_stats["legs_defense"]
            
            damage_reduction = defense_bonus / (defense_bonus + 100)
            damage = int(damage * (1 - damage_reduction))
            self.battle_log.append(f"🛡 {self.get_player_name(defender)} защитил {BODY_PARTS[defend_part]['name']}!")
        
        # Крит
        is_crit = False
        crit_chance = attacker_stats["crit_chance"] + attacker_buffs["crit"]
        if random.random() * 100 < crit_chance:
            damage = int(damage * attacker_stats["crit_multiplier"])
            is_crit = True
            attacker_player.data["critical_hits"] += 1
        
        # Элементальный бонус
        if "element" in skill and skill["element"]:
            elem = skill["element"]
            defender_element = None
            def_weapon = (self.p2 if attacker == 1 else self.p1).data["equipment"].get("weapon")
            if def_weapon:
                def_item = items.get(def_weapon) or limited_items.get(def_weapon)
                if def_item and "element" in def_item:
                    defender_element = def_item["element"]
            
            if defender_element and ELEMENTS.get(elem):
                if ELEMENTS[elem]["strong"] == defender_element:
                    damage = int(damage * 1.5)
                    self.battle_log.append(f"💥 СУПЕРЭФФЕКТИВНО!")
                elif ELEMENTS[elem]["weak"] == defender_element:
                    damage = int(damage * 0.7)
                    self.battle_log.append(f"🔻 Неэффективно...")
        
        # Уклонение
        dodge_chance = defender_stats["dodge_chance"] + defender_buffs["dodge"]
        if random.random() * 100 < dodge_chance:
            damage = 0
            self.battle_log.append(f"💨 {self.get_player_name(defender)} УКЛОНИЛСЯ!")
        
        # Нанесение урона
        if damage > 0:
            if defender == 1:
                self.p1_hp = max(0, self.p1_hp - damage)
            else:
                self.p2_hp = max(0, self.p2_hp - damage)
            
            crit_text = "💥 КРИТ! " if is_crit else ""
            self.battle_log.append(
                f"{crit_text}⚔ {self.get_player_name(attacker)} → {BODY_PARTS.get(target_part, {}).get('name', 'тело')} "
                f"{self.get_player_name(defender)}: <b>-{damage} HP</b>"
            )
            
            # Вампиризм
            if "life_steal" in skill:
                heal = int(damage * skill["life_steal"])
                if attacker == 1:
                    self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
                else:
                    self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
                self.battle_log.append(f"💚 Вампиризм +{heal} HP")
            
            # Эффекты от навыка
            self._apply_skill_effects(defender, skill)
        
        # Лечение
        if "hp_restore" in skill:
            heal = skill["hp_restore"]
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self.battle_log.append(f"💚 +{heal} HP")
        
        # Восстановление маны
        if "mana_restore" in skill:
            mana = skill["mana_restore"]
            if attacker == 1:
                self.p1_mp = min(self.p1_max_mp, self.p1_mp + mana)
            else:
                self.p2_mp = min(self.p2_max_mp, self.p2_mp + mana)
        
        # Кулдауны
        if "cooldown" in skill and skill["cooldown"] > 0:
            attacker_cooldowns[skill_id] = skill["cooldown"]
        
        # Уменьшение кулдаунов
        for sid in list(attacker_cooldowns.keys()):
            attacker_cooldowns[sid] -= 1
            if attacker_cooldowns[sid] <= 0:
                del attacker_cooldowns[sid]
        
        attacker_player.data["skills_used"] += 1
    
    def _apply_skill_effects(self, target, skill):
        """Применить эффекты навыка"""
        effects = []
        
        if "burn_chance" in skill and random.random() * 100 < skill["burn_chance"]:
            effects.append({"type": "burn", "duration": 3})
            self.battle_log.append("🔥 Горение!")
        
        if "freeze_chance" in skill and random.random() * 100 < skill["freeze_chance"]:
            effects.append({"type": "freeze", "duration": 2})
            self.battle_log.append("❄ Заморозка!")
        
        if "stun_chance" in skill and random.random() * 100 < skill["stun_chance"]:
            effects.append({"type": "stun", "duration": 1})
            self.battle_log.append("⚡ Оглушение!")
        
        if "poison_chance" in skill and random.random() * 100 < skill["poison_chance"]:
            effects.append({"type": "poison", "duration": 4})
            self.battle_log.append("☠ Отравление!")
        
        if target == 1:
            self.p1_effects.extend(effects)
        else:
            self.p2_effects.extend(effects)
    
    def _process_effects(self, player_num):
        """Обработка эффектов"""
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        hp = self.p1_hp if player_num == 1 else self.p2_hp
        max_hp = self.p1_max_hp if player_num == 1 else self.p2_max_hp
        
        for effect in effects[:]:
            if effect["type"] in ["burn", "poison", "bleed", "curse"]:
                dmg = STATUS_EFFECTS.get(effect["type"], {}).get("damage_per_turn", 10)
                hp -= dmg
                self.battle_log.append(f"{STATUS_EFFECTS.get(effect['type'], {}).get('name', 'Эффект')} -{dmg} HP")
            
            if effect["type"] == "bless":
                heal = STATUS_EFFECTS.get("bless", {}).get("heal_per_turn", 10)
                hp = min(max_hp, hp + heal)
                self.battle_log.append(f"✨ Благословение +{heal} HP")
            
            effect["duration"] -= 1
            if effect["duration"] <= 0:
                effects.remove(effect)
        
        if player_num == 1:
            self.p1_hp = hp
        else:
            self.p2_hp = hp
    
    def _decay_buffs(self):
        """Уменьшение баффов"""
        for buffs in [self.p1_buffs, self.p2_buffs]:
            for key in buffs:
                buffs[key] = max(0, buffs[key] - 5)
    
    def _check_end(self):
        """Проверка завершения боя"""
        if self.p1_hp <= 0:
            self.active = False
            self.winner = 2
        elif self.p2_hp <= 0:
            self.active = False
            self.winner = 1
    
    def get_state_text(self, for_player_id=None):
        """Получить текст состояния для игрока"""
        player_num = 1 if str(for_player_id) == self.p1_id else 2
        
        # HP бары
        p1_hp_bar = self._bar(self.p1_hp, self.p1_max_hp, "❤")
        p2_hp_bar = self._bar(self.p2_hp, self.p2_max_hp, "❤")
        p1_mp_bar = self._bar(self.p1_mp, self.p1_max_mp, "💎")
        p2_mp_bar = self._bar(self.p2_mp, self.p2_max_mp, "💎")
        
        # Определение фазы
        phase = self.p1_phase if player_num == 1 else self.p2_phase
        
        text = f"""
<b>⚔ ПОШАГОВАЯ ДУЭЛЬ #{self.battle_id}</b>
━━━━━━━━━━━━━━━━━━━━
Ход: <b>#{self.turn}</b> | {self._arena_name()} | {self._weather_name()}

<b>{self.get_player_name(1)}</b>
❤ {p1_hp_bar}
💎 {p1_mp_bar}
🛡 Защита: {BODY_PARTS.get(self.p1_defending, {}).get('name', 'Нет') if self.p1_defending else 'Не выбрана'}

<b>{self.get_player_name(2)}</b>
❤ {p2_hp_bar}
💎 {p2_mp_bar}
🛡 Защита: {BODY_PARTS.get(self.p2_defending, {}).get('name', 'Нет') if self.p2_defending else 'Не выбрана'}
━━━━━━━━━━━━━━━━━━━━
"""
        
        if phase == "defend_select":
            text += "\n🛡 <b>Выберите часть тела для защиты:</b>"
        elif phase == "attack_target":
            text += "\n🎯 <b>Выберите цель атаки:</b>"
        elif phase == "attack_skill":
            target = self.p1_target if player_num == 1 else self.p2_target
            text += f"\n⚔ <b>Цель: {BODY_PARTS.get(target, {}).get('name', 'Тело')}</b>"
            text += "\n<b>Выберите навык:</b>"
        
        # Эффекты
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        if effects:
            text += "\n<b>Ваши эффекты:</b>\n"
            for eff in effects:
                name = STATUS_EFFECTS.get(eff["type"], {}).get("name", eff["type"])
                text += f"• {name} ({eff['duration']} хода)\n"
        
        # Последние события
        if self.battle_log:
            text += f"\n<i>{self.battle_log[-1][:100]}</i>"
        
        return text
    
    def _bar(self, current, maximum, icon):
        pct = current / maximum if maximum > 0 else 0
        filled = int(pct * 10)
        empty = 10 - filled
        return f"{icon} [{'█' * filled}{'░' * empty}] {current}/{maximum}"

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

# ==================== ОБРАБОТЧИКИ КОМАНД ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    if str(user_id) in banned_users:
        ban = banned_users[str(user_id)]
        bot.send_message(message.chat.id, f"⛔ Вы забанены!\nПричина: {ban.get('reason', 'Нет')}")
        return
    
    username = message.from_user.username or f"user_{user_id}"
    first_name = message.from_user.first_name or "Игрок"
    
    player = Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v7.0 ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

🎯 <b>ПОЛНАЯ ВЕРСИЯ — ВСЕ СИСТЕМЫ:</b>
• ⚔ Пошаговые дуэли с выбором частей тела
• 🎯 Стратегия: защита/атака головы, тела, ног
• 🔥 50+ навыков и стихий
• 🛡 Экипировка: голова, тело, ноги
• 💎 Лимитированные предметы
• 🏰 Подземелья, кланы, турниры
• 💱 Рынок и обмен
• 📜 Квесты и достижения

💰 Стартовый бонус: <b>500 монет</b>
⚡ Выбирайте стратегию каждого хода!

<i>Выбирай раздел:</i>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль (с ботом)", callback_data="quick_duel"),
        types.InlineKeyboardButton("👥 PvP дуэль (с игроком)", callback_data="pvp_duel"),
        types.InlineKeyboardButton("🏆 Рейтинговая дуэль", callback_data="ranked_duel"),
        types.InlineKeyboardButton("💀 Хардкорная дуэль", callback_data="hardcore_duel"),
        types.InlineKeyboardButton("🔥 Дуэль на выживание", callback_data="survival_duel"),
        types.InlineKeyboardButton("🎯 Дружеский спарринг", callback_data="sparring_duel")
    )
    
    text = """
<b>⚔️ РАЗДЕЛ ДУЭЛЕЙ</b>

<b>Новая система боя:</b>
🛡 Выберите часть тела для защиты
🎯 Выберите куда атаковать
⚔ Выберите навык атаки

<i>Все дуэли — пошаговые со стратегией!</i>
"""
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="hero_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="hero_inventory"),
        types.InlineKeyboardButton("⚡ Характеристики", callback_data="hero_attributes"),
        types.InlineKeyboardButton("🏅 Достижения", callback_data="hero_achievements"),
        types.InlineKeyboardButton("📜 Квесты", callback_data="hero_quests"),
        types.InlineKeyboardButton("⚙ Настройки", callback_data="hero_settings"),
        types.InlineKeyboardButton("📋 История боёв", callback_data="hero_history"),
        types.InlineKeyboardButton("💊 Лечение", callback_data="hero_heal")
    )
    bot.send_message(message.chat.id, "<b>👤 МЕНЮ ГЕРОЯ</b>", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🏪 Торговля")
def trade_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛒 Магазин", callback_data="trade_shop"),
        types.InlineKeyboardButton("💎 Лимитированные", callback_data="trade_limited"),
        types.InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="trade_daily"),
        types.InlineKeyboardButton("💱 Рынок игроков", callback_data="trade_market"),
        types.InlineKeyboardButton("💰 Продать предмет", callback_data="trade_sell"),
        types.InlineKeyboardButton("📦 Мои лоты", callback_data="trade_my_lots"),
        types.InlineKeyboardButton("💼 Работа", callback_data="trade_work"),
        types.InlineKeyboardButton("📊 Курс обмена", callback_data="trade_exchange")
    )
    bot.send_message(message.chat.id, "<b>🏪 ТОРГОВЛЯ И ЭКОНОМИКА</b>", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🌍 Мир")
def world_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🏰 Подземелья", callback_data="world_dungeons"),
        types.InlineKeyboardButton("🛡 Кланы", callback_data="world_clans"),
        types.InlineKeyboardButton("🏟 Турниры", callback_data="world_tournaments"),
        types.InlineKeyboardButton("📊 Топ игроков", callback_data="world_top"),
        types.InlineKeyboardButton("🌍 События", callback_data="world_events"),
        types.InlineKeyboardButton("ℹ Помощь", callback_data="world_help")
    )
    bot.send_message(message.chat.id, "<b>🌍 ИГРОВОЙ МИР</b>", reply_markup=markup)

# ==================== ДУЭЛИ: ВСЕ ТИПЫ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["quick_duel", "pvp_duel", "ranked_duel", "hardcore_duel", "survival_duel", "sparring_duel"])
def duel_type_selected(call):
    duel_type = call.data
    
    if duel_type == "quick_duel":
        show_quick_duel_menu(call)
    elif duel_type == "pvp_duel":
        show_duel_info(call, "👥 PVP ДУЭЛЬ", "Для вызова используйте: /duel [ставка]")
    elif duel_type == "ranked_duel":
        show_duel_info(call, "🏆 РЕЙТИНГОВАЯ ДУЭЛЬ", "Ставка: 100💰\nИспользуйте: /ranked")
    elif duel_type == "hardcore_duel":
        show_duel_info(call, "💀 ХАРДКОРНАЯ ДУЭЛЬ", "Ставка: от 500💰\nИспользуйте: /hardcore [ставка]")
    elif duel_type == "survival_duel":
        show_duel_info(call, "🔥 ДУЭЛЬ НА ВЫЖИВАНИЕ", "Ставка: 200💰\nИспользуйте: /survival")
    elif duel_type == "sparring_duel":
        show_duel_info(call, "🎯 ДРУЖЕСКИЙ СПАРРИНГ", "Без ставок!\nИспользуйте: /sparring")

def show_quick_duel_menu(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("50💰", callback_data="qduel_50"),
        types.InlineKeyboardButton("100💰", callback_data="qduel_100"),
        types.InlineKeyboardButton("200💰", callback_data="qduel_200"),
        types.InlineKeyboardButton("500💰", callback_data="qduel_500"),
        types.InlineKeyboardButton("1000💰", callback_data="qduel_1000"),
        types.InlineKeyboardButton("5000💰", callback_data="qduel_5000"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels")
    )
    
    bot.edit_message_text(
        f"<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n\n"
        f"💰 Ваш баланс: <b>{player.data['money']}💰</b>\n"
        f"Выберите ставку:",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

def show_duel_info(call, title, info):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
    bot.edit_message_text(
        f"<b>{title}</b>\n\n{info}",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_duels")
def back_to_duels(call):
    duel_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def start_quick_duel(call):
    user_id = call.from_user.id
    bet = int(call.data.split("_")[1])
    player = Player(user_id)
    
    if player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Недостаточно монет! Нужно {bet}💰")
        return
    
    # Создание бота
    bot_level = random.randint(max(1, player.data["level"] - 5), player.data["level"] + 5)
    bot_id = f"bot_{random.randint(100000, 999999)}"
    
    users[bot_id] = generate_bot(bot_level)
    save_json(DATA_FILES['users'], users)
    
    player.data["money"] -= bet
    player.save()
    
    # Создание дуэли
    duel = AdvancedDuel(user_id, bot_id, "quick", bet)
    
    # Показ интерфейса
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

def generate_bot(level):
    """Генерация бота с экипировкой"""
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    
    slot_map = {"head": "helmet", "body": "armor", "legs": "boots"}
    for slot, item_type in slot_map.items():
        slot_items = [k for k, v in items.items() if v.get("type") == item_type and v.get("level_req", 1) <= level]
        if slot_items and random.random() < 0.6:
            equip[slot] = random.choice(slot_items)
    
    weapon_items = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= level]
    if weapon_items:
        equip["weapon"] = random.choice(weapon_items)
    
    return {
        "username": f"Bot_{level}",
        "first_name": f"⚔ Бот Lv.{level}",
        "money": 0, "level": level, "exp": 0, "total_exp": 0,
        "hp": 100 + level * 12, "max_hp": 100 + level * 12,
        "mana": 50 + level * 6, "max_mana": 50 + level * 6,
        "stats": {
            "strength": 5 + level, "agility": 5 + level // 2,
            "intelligence": 5 + level // 3, "vitality": 5 + level // 2,
            "luck": 3 + level // 4, "defense": level
        },
        "stat_points": 0, "wins": 0, "losses": 0, "draws": 0,
        "win_streak": 0, "best_streak": 0, "total_duels": 0,
        "pvp_rating": 1000 + level * 10,
        "total_damage_dealt": 0, "total_damage_taken": 0,
        "critical_hits": 0, "skills_used": 0,
        "inventory": [],
        "equipment": equip,
        "last_daily": None, "last_dungeon": None, "last_work": None,
        "title": "Бот", "titles_collected": ["Бот"],
        "achievements": [], "active_quests": {}, "completed_quests": 0,
        "clan": None, "clan_role": None, "tournament_wins": 0,
        "registration_date": datetime.now().isoformat(),
        "settings": {},
        "battle_history": [],
        "dungeons_completed": 0, "items_found": 0
    }

def show_duel_interface(chat_id, message_id, duel, user_id):
    """Показать интерфейс дуэли"""
    if not duel.active:
        finish_duel(chat_id, message_id, duel)
        return
    
    player_num = 1 if str(user_id) == duel.p1_id else 2
    state_text = duel.get_state_text(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    phase = duel.p1_phase if player_num == 1 else duel.p2_phase
    
    if phase == "defend_select":
        # Выбор защиты
        for part_key, part_data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🛡 {part_data['name']}",
                callback_data=f"defend_{part_key}"
            ))
    
    elif phase == "attack_target":
        # Выбор цели атаки
        for part_key, part_data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🎯 {part_data['name']}",
                callback_data=f"target_{part_key}"
            ))
    
    elif phase == "attack_skill":
        # Выбор навыка
        skills = duel.get_available_skills(player_num)
        for skill_id in skills[:8]:
            skill = SKILLS_DB.get(skill_id, {})
            name = skill.get("name", skill_id)
            mana = skill.get("mana_cost", 0)
            cd = (duel.p1_cooldowns if player_num == 1 else duel.p2_cooldowns).get(skill_id, 0)
            
            btn_text = f"{name} ({mana}MP)"
            if cd > 0:
                btn_text = f"⏳ {name} ({cd})"
            
            markup.add(types.InlineKeyboardButton(
                btn_text,
                callback_data=f"skill_{skill_id}"
            ))
    
    elif phase == "done":
        markup.add(types.InlineKeyboardButton("⏳ Ожидание противника...", callback_data="wait_turn"))
    
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="surrender_duel"))
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh_duel"))
    
    try:
        bot.edit_message_text(
            state_text[:4000],
            chat_id, message_id,
            reply_markup=markup
        )
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("defend_"))
def defend_handler(call):
    user_id = call.from_user.id
    body_part = call.data.split("_")[1]
    
    duel = find_duel(user_id)
    if not duel:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    player_num = 1 if str(user_id) == duel.p1_id else 2
    duel.set_defend_part(player_num, body_part)
    
    # Бот автоматически выбирает защиту
    other_player = 3 - player_num
    if str(duel.p2_id).startswith("bot_") and other_player == 2:
        bot_defend = random.choice(list(BODY_PARTS.keys()))
        duel.set_defend_part(2, bot_defend)
        
        # Бот выбирает цель
        bot_target = random.choice(list(BODY_PARTS.keys()))
        duel.set_attack_target(2, bot_target)
        
        # Бот выбирает навык
        bot_skills = duel.get_available_skills(2)
        if bot_skills:
            duel.execute_attack(2, random.choice(bot_skills))
    
    bot.answer_callback_query(call.id, f"🛡 Защита: {BODY_PARTS[body_part]['name']}")
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("target_"))
def target_handler(call):
    user_id = call.from_user.id
    body_part = call.data.split("_")[1]
    
    duel = find_duel(user_id)
    if not duel:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    player_num = 1 if str(user_id) == duel.p1_id else 2
    duel.set_attack_target(player_num, body_part)
    
    bot.answer_callback_query(call.id, f"🎯 Цель: {BODY_PARTS[body_part]['name']}")
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("skill_"))
def skill_handler(call):
    user_id = call.from_user.id
    skill_id = call.data.split("_", 1)[1]
    
    duel = find_duel(user_id)
    if not duel:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    player_num = 1 if str(user_id) == duel.p1_id else 2
    result = duel.execute_attack(player_num, skill_id)
    
    bot.answer_callback_query(call.id, result[:50])
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "wait_turn")
def wait_turn_handler(call):
    user_id = call.from_user.id
    duel = find_duel(user_id)
    if duel:
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
    else:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "refresh_duel")
def refresh_duel_handler(call):
    user_id = call.from_user.id
    duel = find_duel(user_id)
    if duel:
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
    else:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "surrender_duel")
def surrender_handler(call):
    user_id = call.from_user.id
    duel = find_duel(user_id)
    if duel:
        duel.active = False
        duel.winner = 2 if str(user_id) == duel.p1_id else 1
        finish_duel(call.message.chat.id, call.message.message_id, duel)
    else:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)

def find_duel(user_id):
    """Найти активную дуэль"""
    uid = str(user_id)
    for bid, data in list(active_duels_data.items()):
        if uid in [str(data.get("p1_id")), str(data.get("p2_id"))]:
            return AdvancedDuel(
                data["p1_id"], data["p2_id"],
                data.get("type", "quick"),
                data.get("bet", 0)
            )
    return None

def finish_duel(chat_id, message_id, duel):
    """Завершение дуэли"""
    # Очистка
    for bid in list(active_duels_data.keys()):
        if bid == duel.battle_id:
            del active_duels_data[bid]
    save_json(DATA_FILES['duels'], active_duels_data)
    
    # Удаление ботов
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_"):
            if uid in users:
                del users[uid]
    save_json(DATA_FILES['users'], users)
    
    if duel.winner == 0:
        result_text = "<b>🤝 НИЧЬЯ!</b>"
        p1 = Player(duel.p1_id)
        p2 = Player(duel.p2_id)
        if duel.bet > 0:
            p1.data["money"] += duel.bet
            p2.data["money"] += duel.bet
        p1.data["draws"] += 1
        p2.data["draws"] += 1
        p1.save()
        p2.save()
        bot.edit_message_text(result_text, chat_id, message_id)
        return
    
    winner_id = duel.p1_id if duel.winner == 1 else duel.p2_id
    loser_id = duel.p2_id if duel.winner == 1 else duel.p1_id
    
    winner = Player(winner_id)
    loser = Player(loser_id)
    
    if duel.bet > 0:
        reward = duel.bet * 2
        winner.data["money"] += reward
    
    winner.data["wins"] += 1
    winner.data["win_streak"] += 1
    winner.data["total_duels"] += 1
    winner.data["pvp_rating"] += random.randint(20, 35)
    
    if winner.data["win_streak"] > winner.data["best_streak"]:
        winner.data["best_streak"] = winner.data["win_streak"]
    
    loser.data["losses"] += 1
    loser.data["win_streak"] = 0
    loser.data["total_duels"] += 1
    loser.data["pvp_rating"] = max(0, loser.data["pvp_rating"] - random.randint(10, 25))
    
    exp_winner = duel.turn * 10 + duel.bet // 2
    exp_loser = duel.turn * 5 + duel.bet // 5
    
    winner.data["exp"] += exp_winner
    winner.data["total_exp"] += exp_winner
    loser.data["exp"] += exp_loser
    loser.data["total_exp"] += exp_loser
    
    old_w = winner.data["level"]
    check_level_up(winner)
    old_l = loser.data["level"]
    check_level_up(loser)
    
    winner.data.setdefault("battle_history", []).append({
        "date": datetime.now().isoformat(),
        "opponent": loser.data["first_name"],
        "result": "win",
        "type": duel.duel_type,
        "turns": duel.turn,
        "bet": duel.bet
    })
    
    loser.data.setdefault("battle_history", []).append({
        "date": datetime.now().isoformat(),
        "opponent": winner.data["first_name"],
        "result": "loss",
        "type": duel.duel_type,
        "turns": duel.turn,
        "bet": duel.bet
    })
    
    winner.save()
    loser.save()
    
    result_text = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

👑 Победитель: <b>{winner.data['first_name']}</b>
💀 Проигравший: <b>{loser.data['first_name']}</b>

💰 Приз: <b>{duel.bet * 2 if duel.bet > 0 else 0}💰</b>
✨ Опыт: +{exp_winner} | +{exp_loser}
📊 Ходов: <b>{duel.turn}</b>
"""
    
    if winner.data["level"] > old_w:
        result_text += f"\n🎉 {winner.data['first_name']} получает уровень <b>{winner.data['level']}</b>!"
    if loser.data["level"] > old_l:
        result_text += f"\n🎉 {loser.data['first_name']} получает уровень <b>{loser.data['level']}</b>!"
    
    bot.edit_message_text(result_text, chat_id, message_id)

# ==================== ДУЭЛЬНЫЕ КОМАНДЫ ====================
@bot.message_handler(commands=['duel', 'ranked', 'hardcore', 'survival', 'sparring'])
def duel_commands(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Ответьте на сообщение игрока!")
        return
    
    user_id = message.from_user.id
    opponent_id = message.reply_to_message.from_user.id
    
    if user_id == opponent_id:
        bot.send_message(message.chat.id, "❌ Нельзя вызвать себя!")
        return
    
    command = message.text.split()[0].replace('/', '')
    
    if command == "duel":
        try:
            bet = int(message.text.split()[1]) if len(message.text.split()) > 1 else 100
            bet = max(50, min(10000, bet))
        except:
            bet = 100
        duel_type = "pvp"
    elif command == "ranked":
        bet = 100
        duel_type = "ranked"
    elif command == "hardcore":
        try:
            bet = int(message.text.split()[1]) if len(message.text.split()) > 1 else 500
            bet = max(500, min(50000, bet))
        except:
            bet = 500
        duel_type = "hardcore"
    elif command == "survival":
        bet = 200
        duel_type = "survival"
    elif command == "sparring":
        bet = 0
        duel_type = "sparring"
    else:
        bet = 100
        duel_type = "pvp"
    
    player = Player(user_id)
    opponent = Player(opponent_id)
    
    if bet > 0:
        if player.data["money"] < bet:
            bot.send_message(message.chat.id, f"❌ У вас недостаточно монет! Нужно {bet}💰")
            return
        if opponent.data["money"] < bet:
            bot.send_message(message.chat.id, "❌ У противника недостаточно монет!")
            return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"accept_{user_id}_{duel_type}_{bet}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_{user_id}")
    )
    
    names = {"pvp": "PvP", "ranked": "Рейтинговая", "hardcore": "Хардкор", "survival": "На выживание", "sparring": "Спарринг"}
    
    bot.send_message(message.chat.id,
        f"<b>⚔ ВЫЗОВ НА ДУЭЛЬ!</b>\n\n"
        f"Тип: <b>{names.get(duel_type, duel_type)}</b>\n"
        f"{message.from_user.first_name} → {message.reply_to_message.from_user.first_name}\n"
        f"Ставка: <b>{bet}💰</b>",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def accept_duel(call):
    parts = call.data.split("_")
    challenger_id = parts[1]
    duel_type = parts[2]
    bet = int(parts[3])
    opponent_id = str(call.from_user.id)
    
    challenger = Player(challenger_id)
    opponent = Player(opponent_id)
    
    if bet > 0:
        if challenger.data["money"] < bet or opponent.data["money"] < bet:
            bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
            return
        challenger.data["money"] -= bet
        opponent.data["money"] -= bet
        challenger.save()
        opponent.save()
    
    duel = AdvancedDuel(challenger_id, opponent_id, duel_type, bet)
    
    bot.edit_message_text("⚔ Дуэль начинается! Выбирайте защиту.", 
                          call.message.chat.id, call.message.message_id)
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, opponent_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("decline_"))
def decline_duel(call):
    bot.edit_message_text("❌ Вызов отклонён", call.message.chat.id, call.message.message_id)

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
        f"<b>🛒 МАГАЗИН</b>\n💰 Баланс: <b>{player.data['money']}💰</b>",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("shopcat_"))
def shop_category(call):
    category = call.data.split("_")[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    cat_names = {
        "weapon": "⚔ ОРУЖИЕ", "helmet": "👤 ШЛЕМЫ",
        "armor": "🦾 БРОНЯ", "boots": "🦿 ОБУВЬ", "potion": "🧪 ЗЕЛЬЯ"
    }
    
    cat_items = {k: v for k, v in items.items() if v.get("type") == category}
    
    text = f"<b>{cat_names.get(category, category)}</b>\n💰 Баланс: <b>{player.data['money']}</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, item in sorted(cat_items.items(), key=lambda x: x[1].get("price", 0)):
        if player.data["level"] < item.get("level_req", 1):
            continue
        
        rarity = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
        
        if item.get("type") == "weapon":
            stats = f"Урон: {item['damage'][0]}-{item['damage'][1]}"
        elif item.get("type") in ["helmet", "armor", "boots"]:
            stats = f"Защита: {item.get('defense', 0)}"
            if "speed" in item:
                stats += f" | Скорость: +{item['speed']}"
            if "hp_bonus" in item:
                stats += f" | HP: +{item['hp_bonus']}"
        elif item.get("type") == "potion":
            stats = f"Лечение: {item.get('heal', 0)}"
        else:
            stats = ""
        
        text += f"{rarity} <b>{item['name']}</b> — {stats}\n💰 {item['price']} | Ур.{item.get('level_req', 1)}\n\n"
        
        if player.data["money"] >= item["price"]:
            markup.add(types.InlineKeyboardButton(
                f"Купить: {item['name']} - {item['price']}💰",
                callback_data=f"buyitem_{item_key}"
            ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="trade_shop"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buyitem_"))
def buy_item(call):
    item_key = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(item_key) or limited_items.get(item_key)
    if not item:
        bot.answer_callback_query(call.id, "❌ Предмет не найден!")
        return
    
    if player.data["level"] < item.get("level_req", 1):
        bot.answer_callback_query(call.id, f"❌ Нужен {item.get('level_req', 1)} уровень!")
        return
    
    if player.data["money"] < item["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    if item_key in limited_items:
        if limited_items[item_key]["remaining"] <= 0:
            bot.answer_callback_query(call.id, "❌ Предмет закончился!")
            return
        limited_items[item_key]["remaining"] -= 1
        save_json(DATA_FILES['limited'], limited_items)
    
    player.data["money"] -= item["price"]
    player.data["inventory"].append(item_key)
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ Куплено: {item['name']}!")
    shop_category(call)

# ==================== ЛИМИТИРОВАННЫЕ ====================
@bot.callback_query_handler(func=lambda call: call.data == "trade_limited")
def limited_shop(call):
    if not limited_items:
        bot.edit_message_text("💎 Нет лимитированных предметов", 
                              call.message.chat.id, call.message.message_id)
        return
    
    text = "<b>💎 ЛИМИТИРОВАННЫЕ ПРЕДМЕТЫ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, item in limited_items.items():
        if item["remaining"] > 0:
            pct = "█" * int(item["remaining"] / item["total"] * 10)
            empty = "░" * (10 - len(pct))
            text += f"<b>{item['name']}</b>\n[{pct}{empty}] {item['remaining']}/{item['total']}\n"
            text += f"💰 <b>{item['price']}💰</b>\n\n"
            
            markup.add(types.InlineKeyboardButton(
                f"Купить {item['name']} - {item['price']}💰",
                callback_data=f"buyitem_{item_key}"
            ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== ЕЖЕДНЕВНЫЙ БОНУС ====================
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
    
    text = f"<b>🎁 ЕЖЕДНЕВНЫЙ БОНУС</b>\n💰 +{bonus}\n✨ +{exp}"
    if player.data["level"] > old:
        text += f"\n🎉 УРОВЕНЬ <b>{player.data['level']}</b>!"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

# ==================== РЫНОК ====================
@bot.callback_query_handler(func=lambda call: call.data == "trade_market")
def market_menu(call):
    if not market_listings:
        bot.edit_message_text("📦 Рынок пуст\n/sell [номер] [цена] — создать лот", 
                              call.message.chat.id, call.message.message_id)
        return
    
    text = "<b>💱 РЫНОК</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for lid, listing in list(market_listings.items())[:10]:
        item = items.get(listing["item_key"]) or limited_items.get(listing["item_key"])
        if item:
            text += f"📦 {item['name']} — <b>{listing['price']}💰</b>\n"
            text += f"   👤 {listing.get('seller_name', 'Нет')}\n\n"
            markup.add(types.InlineKeyboardButton(
                f"Купить: {item['name']}",
                callback_data=f"mktbuy_{lid}"
            ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mktbuy_"))
def market_buy_handler(call):
    lid = call.data.split("_", 1)[1]
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if lid not in market_listings:
        bot.answer_callback_query(call.id, "❌ Лот продан!")
        return
    
    listing = market_listings[lid]
    if user_id == str(listing.get("seller_id")):
        bot.answer_callback_query(call.id, "❌ Нельзя купить своё!")
        return
    
    if player.data["money"] < listing["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
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
    bot.answer_callback_query(call.id, f"✅ Куплено: {item.get('name', 'Предмет')}!")
    market_menu(call)

@bot.callback_query_handler(func=lambda call: call.data == "trade_sell")
def sell_info(call):
    bot.edit_message_text(
        "📦 /sell [номер] [цена]\nНомер из /inventory",
        call.message.chat.id, call.message.message_id
    )

@bot.callback_query_handler(func=lambda call: call.data == "trade_my_lots")
def my_lots(call):
    uid = str(call.from_user.id)
    my = {k: v for k, v in market_listings.items() if str(v.get("seller_id")) == uid}
    
    if not my:
        bot.edit_message_text("📦 У вас нет лотов", call.message.chat.id, call.message.message_id)
        return
    
    text = "<b>📦 МОИ ЛОТЫ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for lid, listing in my.items():
        item = items.get(listing["item_key"]) or limited_items.get(listing["item_key"])
        if item:
            text += f"📦 {item['name']} — {listing['price']}💰\n"
            markup.add(types.InlineKeyboardButton(
                f"Снять: {item['name']}",
                callback_data=f"removelot_{lid}"
            ))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

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
        bot.answer_callback_query(call.id, "✅ Лот снят!")
    else:
        bot.answer_callback_query(call.id, "❌ Ошибка!")
    
    my_lots(call)

# ==================== ГЕРОЙ ====================
@bot.callback_query_handler(func=lambda call: call.data == "hero_stats")
def hero_stats(call):
    user_id = call.from_user.id
    player = Player(user_id)
    s = player.get_full_stats()
    d = player.data
    
    wr = (d["wins"] / d["total_duels"] * 100) if d["total_duels"] > 0 else 0
    
    text = f"""
<b>📊 СТАТИСТИКА</b>

<b>{d['first_name']}</b> | {d['title']}
⭐ Ур.{d['level']} | Рейтинг: {d['pvp_rating']}
💰 {d['money']}💰

⚔ Урон: {s['min_damage']}-{s['max_damage']}
🛡 Защита: {s['defense']} (Г:{s['head_defense']} Т:{s['body_defense']} Н:{s['legs_defense']})
💨 Скорость: {s['speed']:.0f}
💥 Крит: {s['crit_chance']:.1f}%
🔄 Уклон: {s['dodge_chance']:.1f}%

🏆 Побед: {d['wins']} | 💀 Поражений: {d['losses']}
📈 Винрейт: {wr:.1f}% | ⚔ Боёв: {d['total_duels']}
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
        
        rarity = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
        eq = ""
        for slot, ek in player.data["equipment"].items():
            if ek == ik:
                eq = f" [{slot}]"
        
        text += f"{idx}. {rarity} {item['name']} x{cnt}{eq}\n"
        
        # Кнопка экипировки
        slot_type = item.get("type")
        if slot_type in ["weapon", "helmet", "armor", "boots"]:
            slot_map = {"weapon": "weapon", "helmet": "head", "armor": "body", "boots": "legs"}
            markup.add(types.InlineKeyboardButton(
                f"Экипировать: {item['name']}",
                callback_data=f"equip_{ik}"
            ))
        elif slot_type == "potion":
            markup.add(types.InlineKeyboardButton(
                f"Использовать: {item['name']}",
                callback_data=f"use_{ik}"
            ))
        
        idx += 1
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
def equip_item(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(ik) or limited_items.get(ik)
    if not item:
        bot.answer_callback_query(call.id, "❌ Предмет не найден!")
        return
    
    if ik not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌ Нет в инвентаре!")
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("use_"))
def use_potion(call):
    ik = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(ik) or limited_items.get(ik)
    if not item or item.get("type") != "potion":
        bot.answer_callback_query(call.id, "❌ Нельзя использовать!")
        return
    
    if ik not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌ Нет в инвентаре!")
        return
    
    stats = player.get_full_stats()
    
    if "heal" in item:
        if player.data["hp"] >= stats["max_hp"]:
            bot.answer_callback_query(call.id, "❌ Полное HP!")
            return
        player.data["hp"] = min(stats["max_hp"], player.data["hp"] + item["heal"])
    
    if "mana_restore" in item:
        player.data["mana"] = min(stats["max_mana"], player.data["mana"] + item["mana_restore"])
    
    player.data["inventory"].remove(ik)
    player.save()
    
    bot.answer_callback_query(call.id, "✅ Использовано!")
    hero_inventory(call)

@bot.callback_query_handler(func=lambda call: call.data == "hero_attributes")
def hero_attributes(call):
    user_id = call.from_user.id
    player = Player(user_id)
    st = player.data["stats"]
    pts = player.data["stat_points"]
    
    text = f"""
<b>⚡ ХАРАКТЕРИСТИКИ</b>
Очков: <b>{pts}</b>

💪 Сила: {st['strength']} (+{(st['strength']-5)*2} к урону)
🏃 Ловкость: {st['agility']} (+{(st['agility']-5)*1.5} скорости)
🧠 Интеллект: {st['intelligence']} (+{(st['intelligence']-5)*8} маны)
❤ Живучесть: {st['vitality']} (+{(st['vitality']-5)*15} HP)
🍀 Удача: {st['luck']} (+{(st['luck']-5)*0.5}% крита)
🛡 Защита: {st['defense']} (+ защита тела)
"""
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    if pts > 0:
        markup.add(
            types.InlineKeyboardButton("💪", callback_data="up_stat_str"),
            types.InlineKeyboardButton("🏃", callback_data="up_stat_agi"),
            types.InlineKeyboardButton("🧠", callback_data="up_stat_int"),
            types.InlineKeyboardButton("❤", callback_data="up_stat_vit"),
            types.InlineKeyboardButton("🍀", callback_data="up_stat_luk"),
            types.InlineKeyboardButton("🛡", callback_data="up_stat_def")
        )
        text += "\n<i>Нажмите для повышения:</i>"
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("up_stat_"))
def upgrade_stat(call):
    stat_map = {
        "str": "strength", "agi": "agility", "int": "intelligence",
        "vit": "vitality", "luk": "luck", "def": "defense"
    }
    stat_key = stat_map[call.data.split("_")[2]]
    
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
    
    names = {"strength": "Сила", "agility": "Ловкость", "intelligence": "Интеллект",
             "vitality": "Живучесть", "luck": "Удача", "defense": "Защита"}
    bot.answer_callback_query(call.id, f"⬆ {names[stat_key]}: {player.data['stats'][stat_key]}")
    hero_attributes(call)

@bot.callback_query_handler(func=lambda call: call.data == "hero_achievements")
def hero_achievements(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    achievements_list = [
        ("first_blood", "🩸 Первая кровь", "Выиграть 1 дуэль", player.data["wins"] >= 1),
        ("warrior", "⚔ Воин", "10 побед", player.data["wins"] >= 10),
        ("veteran", "🎖 Ветеран", "50 побед", player.data["wins"] >= 50),
        ("legend", "👑 Легенда", "100 побед", player.data["wins"] >= 100),
        ("rich", "💰 Богач", "10000 монет", player.data["money"] >= 10000),
        ("dungeon_master", "🏰 Мастер данжей", "10 данжей", player.data.get("dungeons_completed", 0) >= 10),
        ("collector", "🎒 Коллекционер", "20 предметов", player.data.get("items_found", 0) >= 20)
    ]
    
    text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(player.data['achievements'])}/7)\n\n"
    
    for aid, name, desc, cond in achievements_list:
        done = aid in player.data["achievements"] or cond
        icon = "✅" if done else "🔒"
        text += f"{icon} <b>{name}</b>: {desc}\n"
        if cond and aid not in player.data["achievements"]:
            player.data["achievements"].append(aid)
    
    player.save()
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "hero_quests")
def hero_quests(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player.data.get("quests_date") != today:
        player.data["active_quests"] = {
            "daily_duels": {"name": "Дуэлянт", "target": 3, "progress": 0, "reward": 300},
            "daily_wins": {"name": "Победитель", "target": 2, "progress": 0, "reward": 400},
            "daily_dungeons": {"name": "Исследователь", "target": 1, "progress": 0, "reward": 500}
        }
        player.data["quests_date"] = today
        player.save()
    
    text = f"<b>📜 КВЕСТЫ ({today})</b>\n\n"
    
    for qid, quest in player.data["active_quests"].items():
        pct = min(quest["progress"] / quest["target"], 1.0)
        bar = "█" * int(pct * 10) + "░" * (10 - int(pct * 10))
        text += f"<b>{quest['name']}</b>\n[{bar}] {quest['progress']}/{quest['target']}\n🎁 {quest['reward']}💰\n\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "hero_settings")
def hero_settings(call):
    user_id = call.from_user.id
    player = Player(user_id)
    s = player.data.get("settings", {})
    
    text = f"""
<b>⚙ НАСТРОЙКИ</b>

🔔 Уведомления: {'✅' if s.get('notifications', True) else '❌'}
⚔ Запросы дуэлей: {'✅' if s.get('duel_requests', True) else '❌'}
📋 Лог боя: {'✅' if s.get('show_battle_log', True) else '❌'}
"""
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔔 Уведомления", callback_data="set_notify"),
        types.InlineKeyboardButton("⚔ Запросы", callback_data="set_duelreq"),
        types.InlineKeyboardButton("📋 Лог", callback_data="set_log"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero")
    )
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def toggle_setting(call):
    smap = {"notify": "notifications", "duelreq": "duel_requests", "log": "show_battle_log"}
    setting = smap[call.data.split("_")[1]]
    
    user_id = call.from_user.id
    player = Player(user_id)
    
    player.data["settings"][setting] = not player.data["settings"].get(setting, True)
    player.save()
    
    bot.answer_callback_query(call.id, "✅ Изменено!")
    hero_settings(call)

@bot.callback_query_handler(func=lambda call: call.data == "hero_history")
def hero_history(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    history = player.data.get("battle_history", [])
    if not history:
        bot.edit_message_text("📋 История пуста", call.message.chat.id, call.message.message_id)
        return
    
    text = "<b>📋 ПОСЛЕДНИЕ 10 БОЁВ</b>\n\n"
    
    for battle in history[-10:]:
        icon = "🏆" if battle.get("result") == "win" else "💀" if battle.get("result") == "loss" else "🤝"
        text += f"{icon} vs {battle.get('opponent', 'Нет')}\n"
        text += f"   {battle.get('type', '')} | {battle.get('turns', 0)} ходов | {battle.get('bet', 0)}💰\n"
        text += f"   {battle.get('date', '')[:10]}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "hero_heal")
def hero_heal(call):
    user_id = call.from_user.id
    player = Player(user_id)
    stats = player.get_full_stats()
    
    potions = [k for k in player.data["inventory"] if items.get(k, {}).get("type") == "potion" and items.get(k, {}).get("heal", 0) > 0]
    
    if not potions:
        bot.edit_message_text("💊 Нет лечебных зелий!", call.message.chat.id, call.message.message_id)
        return
    
    if player.data["hp"] >= stats["max_hp"]:
        bot.edit_message_text("💊 Полное здоровье!", call.message.chat.id, call.message.message_id)
        return
    
    potion_key = potions[0]
    potion = items[potion_key]
    
    player.data["hp"] = min(stats["max_hp"], player.data["hp"] + potion["heal"])
    player.data["inventory"].remove(potion_key)
    player.save()
    
    bot.edit_message_text(
        f"💊 Использовано: <b>{potion['name']}</b>\n❤ HP: {player.data['hp']}/{stats['max_hp']}",
        call.message.chat.id, call.message.message_id
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_hero")
def back_to_hero(call):
    hero_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_trade")
def back_to_trade(call):
    trade_section(call.message)

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
def start_dungeon(call):
    dl = int(call.data.split("_")[1])
    user_id = call.from_user.id
    player = Player(user_id)
    
    level_reqs = [1, 5, 10, 15, 25]
    if player.data["level"] < level_reqs[dl - 1]:
        bot.answer_callback_query(call.id, f"❌ Нужен {level_reqs[dl-1]} уровень!")
        return
    
    if player.data.get("last_dungeon"):
        last = datetime.fromisoformat(player.data["last_dungeon"])
        if (datetime.now() - last) < timedelta(hours=1):
            remaining = timedelta(hours=1) - (datetime.now() - last)
            bot.answer_callback_query(call.id, f"⏰ Ждите {remaining.seconds//60} мин.")
            return
    
    boss_names = ["Вожак стаи", "Королева пауков", "Некромант", "Древний дракон", "Владыка бездны"]
    reward = random.randint(50, 250) * dl * player.data["level"]
    exp = 50 * dl * player.data["level"]
    
    got_item = None
    if random.random() < 0.1 + dl * 0.05:
        possible = [k for k, v in items.items() if v.get("level_req", 1) <= player.data["level"]]
        if possible:
            got_item = random.choice(possible)
            player.data["inventory"].append(got_item)
            player.data["items_found"] += 1
    
    player.data["money"] += reward
    player.data["exp"] += exp
    player.data["total_exp"] += exp
    player.data["last_dungeon"] = datetime.now().isoformat()
    player.data["dungeons_completed"] = player.data.get("dungeons_completed", 0) + 1
    
    old = player.data["level"]
    check_level_up(player)
    player.save()
    
    result = f"""
<b>🏰 ДАНЖ ПРОЙДЕН!</b>

Босс: <b>{boss_names[dl-1]}</b>
💰 +{reward} | ✨ +{exp}
"""
    if got_item:
        result += f"\n🎁 <b>{items[got_item]['name']}</b>!"
    if player.data["level"] > old:
        result += f"\n🎉 УРОВЕНЬ <b>{player.data['level']}</b>!"
    
    bot.edit_message_text(result, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "world_clans")
def world_clans(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data.get("clan"):
        clan = clans.get(player.data["clan"], {})
        text = f"""
<b>🛡 КЛАН: {player.data['clan']}</b>

👥 {len(clan.get('members', []))} уч.
💰 Казна: {clan.get('treasury', 0)}💰
👑 {clan.get('leader_name', 'Нет')}
"""
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("👥 Участники", callback_data="clan_members"),
            types.InlineKeyboardButton("💰 Взнос", callback_data="clan_donate_info"),
            types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave")
        )
    else:
        text = "<b>🛡 КЛАНЫ</b>\n\n/createclan [имя] — создать\n/joinclan [имя] — вступить\n💰 Создание: 5000💰"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📋 Список", callback_data="clan_list"),
            types.InlineKeyboardButton("ℹ Инфо", callback_data="clan_info")
        )
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "clan_list")
def clan_list(call):
    if not clans:
        bot.edit_message_text("📋 Нет кланов", call.message.chat.id, call.message.message_id)
        return
    
    text = "<b>📋 КЛАНЫ</b>\n\n"
    for name, data in clans.items():
        text += f"🛡 <b>{name}</b>: {len(data.get('members', []))} уч.\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_clans"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "clan_info")
def clan_info(call):
    text = "<b>ℹ О КЛАНАХ</b>\n\n/createclan [имя] — создать (5000💰)\n/joinclan [имя] — вступить"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_clans"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "clan_members")
def clan_members(call):
    user_id = call.from_user.id
    player = Player(user_id)
    clan_name = player.data.get("clan")
    
    if not clan_name:
        bot.answer_callback_query(call.id, "❌ Не в клане!")
        return
    
    members = clans.get(clan_name, {}).get("members", [])
    text = f"<b>👥 {clan_name}</b>\n\n"
    for i, m in enumerate(members, 1):
        text += f"{i}. {m}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_clans"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "clan_donate_info")
def clan_donate_info(call):
    bot.send_message(call.message.chat.id, "💰 /clandonate [сумма]")

@bot.message_handler(commands=['clandonate'])
def clan_donate_cmd(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    if not player.data.get("clan"):
        bot.send_message(message.chat.id, "❌ Не в клане!")
        return
    
    try:
        amount = int(message.text.split()[1])
    except:
        bot.send_message(message.chat.id, "❌ /clandonate [сумма]")
        return
    
    if player.data["money"] < amount:
        bot.send_message(message.chat.id, "❌ Недостаточно!")
        return
    
    player.data["money"] -= amount
    player.save()
    
    clan_name = player.data["clan"]
    clans[clan_name]["treasury"] = clans[clan_name].get("treasury", 0) + amount
    save_json(DATA_FILES['clans'], clans)
    
    bot.send_message(message.chat.id, f"✅ +{amount}💰 в казну!")

@bot.callback_query_handler(func=lambda call: call.data == "clan_leave")
def clan_leave_handler(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if not player.data.get("clan"):
        bot.answer_callback_query(call.id, "❌ Не в клане!")
        return
    
    clan_name = player.data["clan"]
    if player.data.get("clan_role") == "leader":
        bot.answer_callback_query(call.id, "❌ Лидер не может выйти!")
        return
    
    player.data["clan"] = None
    player.data["clan_role"] = None
    player.save()
    
    if player.data["first_name"] in clans[clan_name].get("members", []):
        clans[clan_name]["members"].remove(player.data["first_name"])
    save_json(DATA_FILES['clans'], clans)
    
    bot.answer_callback_query(call.id, "✅ Вы вышли!")
    world_clans(call)

@bot.message_handler(commands=['createclan'])
def create_clan_cmd(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    if player.data.get("clan"):
        bot.send_message(message.chat.id, "❌ Вы уже в клане!")
        return
    if player.data["money"] < 5000:
        bot.send_message(message.chat.id, "❌ Нужно 5000💰!")
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
    
    clans[name] = {
        "leader_id": user_id, "leader_name": message.from_user.first_name,
        "members": [message.from_user.first_name], "treasury": 0,
        "created_at": datetime.now().isoformat()
    }
    save_json(DATA_FILES['clans'], clans)
    
    bot.send_message(message.chat.id, f"✅ Клан <b>{name}</b> создан!")

@bot.message_handler(commands=['joinclan'])
def join_clan_cmd(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    if player.data.get("clan"):
        bot.send_message(message.chat.id, "❌ Вы уже в клане!")
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
    
    bot.send_message(message.chat.id, f"✅ Вы вступили в <b>{name}</b>!")

@bot.callback_query_handler(func=lambda call: call.data == "world_tournaments")
def world_tournaments(call):
    if not tournaments.get("active"):
        tournaments["active"] = {
            "name": "Турнир", "participants": [], "prize_pool": 5000,
            "status": "registration", "started_at": datetime.now().isoformat()
        }
        save_json(DATA_FILES['tournaments'], tournaments)
    
    tour = tournaments["active"]
    
    text = f"""
<b>🏟 ТУРНИР</b>

<b>{tour['name']}</b>
Участников: {len(tour.get('participants', []))}/16
Приз: <b>{tour.get('prize_pool', 0)}💰</b>
Взнос: 500💰
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
        title = "⭐ УРОВЕНЬ"
    elif cat == "wins":
        su = sorted(users.items(), key=lambda x: x[1].get("wins", 0), reverse=True)[:10]
        title = "⚔ ПОБЕДЫ"
    elif cat == "money":
        su = sorted(users.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]
        title = "💰 МОНЕТЫ"
    elif cat == "rating":
        su = sorted(users.items(), key=lambda x: x[1].get("pvp_rating", 1000), reverse=True)[:10]
        title = "🏆 РЕЙТИНГ"
    else:
        return
    
    medals = ["🥇", "🥈", "🥉"] + [f"{i}️⃣" for i in range(4, 11)]
    text = f"<b>{title}</b>\n\n"
    
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

@bot.callback_query_handler(func=lambda call: call.data == "world_events")
def world_events(call):
    if not events.get("current"):
        events["current"] = {
            "name": "🌍 Нашествие", "description": "Выиграйте 5 дуэлей!",
            "target": 5, "progress": {}, "reward": 1000,
            "expires": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        save_json(DATA_FILES['events'], events)
    
    ev = events["current"]
    uid = str(call.from_user.id)
    prog = ev.get("progress", {}).get(uid, 0)
    
    text = f"""
<b>🌍 СОБЫТИЕ</b>

<b>{ev['name']}</b>
📝 {ev['description']}
🎁 {ev['reward']}💰
📊 {prog}/{ev['target']}
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "world_help")
def world_help(call):
    text = """
<b>ℹ ПОМОЩЬ</b>

<b>Дуэли:</b> /duel, /ranked, /hardcore, /survival, /sparring
<b>Магазин:</b> /shop
<b>Инвентарь:</b> /inventory
<b>Продать:</b> /sell [№] [цена]
<b>Бонус:</b> /daily
<b>Работа:</b> /work
<b>Клан:</b> /createclan, /joinclan

<b>Бой:</b>
🛡 Выберите защиту → 🎯 Цель → ⚔ Навык
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_world")
def back_to_world(call):
    world_section(call.message)

# ==================== РАБОТА ====================
@bot.callback_query_handler(func=lambda call: call.data == "trade_work")
def work_action(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    now = datetime.now()
    if player.data.get("last_work"):
        last = datetime.fromisoformat(player.data["last_work"])
        if (now - last) < timedelta(hours=1):
            r = timedelta(hours=1) - (now - last)
            bot.answer_callback_query(call.id, f"⏰ {r.seconds//60} мин.")
            return
    
    jobs = ["Охота", "Защита", "Сбор трав", "Тренировка", "Руины", "Охрана"]
    reward = random.randint(80, 250) + player.data["level"] * 10
    exp = random.randint(30, 100) + player.data["level"] * 5
    
    player.data["money"] += reward
    player.data["exp"] += exp
    player.data["total_exp"] += exp
    player.data["last_work"] = now.isoformat()
    
    old = player.data["level"]
    check_level_up(player)
    player.save()
    
    text = f"<b>💼 {random.choice(jobs)}</b>\n💰 +{reward}\n✨ +{exp}"
    if player.data["level"] > old:
        text += f"\n🎉 УРОВЕНЬ <b>{player.data['level']}</b>!"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "trade_exchange")
def exchange_info(call):
    bot.edit_message_text("<b>📊 КУРС</b>\n1 ур. = 100 EXP\n/sell [№] [цена]", 
                          call.message.chat.id, call.message.message_id)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def check_level_up(player):
    level = player.data["level"]
    exp_needed = int(100 * (1.5 ** (level - 1)))
    
    leveled = False
    while player.data["exp"] >= exp_needed:
        player.data["exp"] -= exp_needed
        player.data["level"] += 1
        player.data["stat_points"] += 3
        player.data["max_hp"] += 15
        player.data["max_mana"] += 8
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
    
    ik = player.data["inventory"][idx]
    item = items.get(ik) or limited_items.get(ik)
    
    player.data["inventory"].pop(idx)
    player.save()
    
    lid = f"{user_id}_{int(time.time())}"
    market_listings[lid] = {
        "seller_id": user_id,
        "seller_name": message.from_user.first_name,
        "item_key": ik,
        "price": price,
        "created_at": datetime.now().isoformat()
    }
    save_json(DATA_FILES['market'], market_listings)
    
    bot.send_message(message.chat.id, f"✅ {item.get('name', ik)} за {price}💰!")

# ==================== АДМИН-ПАНЕЛЬ ====================
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
        types.InlineKeyboardButton("✅ Разбан", callback_data="admin_unban")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    text = f"""
<b>📊 СТАТИСТИКА</b>

👥 Игроков: {len(users)}
💰 Монет: {sum(u.get('money', 0) for u in users.values())}
⚔ Дуэлей: {sum(u.get('total_duels', 0) for u in users.values())}
🛡 Кланов: {len(clans)}
💎 Лимиток: {sum(v.get('remaining', 0) for v in limited_items.values())}
📦 Лотов: {len(market_listings)}
⛔ Банов: {len(banned_users)}
"""
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_givemoney")
def admin_givemoney_prompt(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.send_message(call.message.chat.id, "💰 /givemoney [ID] [сумма]")

@bot.message_handler(commands=['givemoney'])
def admin_givemoney_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        tid, amt = str(parts[1]), int(parts[2])
        p = Player(tid)
        p.data["money"] += amt
        p.save()
        bot.send_message(message.chat.id, f"✅ {amt}💰 → {tid}")
    except:
        bot.send_message(message.chat.id, "❌ /givemoney [ID] [сумма]")

@bot.callback_query_handler(func=lambda call: call.data == "admin_giveitem")
def admin_giveitem_prompt(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.send_message(call.message.chat.id, "🎁 /giveitem [ID] [item_key]")

@bot.message_handler(commands=['giveitem'])
def admin_giveitem_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        tid, ik = str(parts[1]), parts[2]
        p = Player(tid)
        p.data["inventory"].append(ik)
        p.save()
        bot.send_message(message.chat.id, f"✅ {ik} → {tid}")
    except:
        bot.send_message(message.chat.id, "❌ /giveitem [ID] [item_key]")

@bot.callback_query_handler(func=lambda call: call.data == "admin_banuser")
def admin_ban_prompt(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.send_message(call.message.chat.id, "⛔ /ban [ID] [причина]")

@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.split(maxsplit=2)
        tid = str(parts[1])
        reason = parts[2] if len(parts) > 2 else "Нарушение"
        banned_users[tid] = {"reason": reason, "banned_at": datetime.now().isoformat()}
        save_json(DATA_FILES['bans'], banned_users)
        bot.send_message(message.chat.id, f"⛔ {tid} забанен!")
    except:
        bot.send_message(message.chat.id, "❌ /ban [ID] [причина]")

@bot.callback_query_handler(func=lambda call: call.data == "admin_unban")
def admin_unban_prompt(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.send_message(call.message.chat.id, "✅ /unban [ID]")

@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        tid = str(message.text.split()[1])
        if tid in banned_users:
            del banned_users[tid]
            save_json(DATA_FILES['bans'], banned_users)
            bot.send_message(message.chat.id, f"✅ {tid} разбанен!")
    except:
        bot.send_message(message.chat.id, "❌ /unban [ID]")

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def admin_broadcast_prompt(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.send_message(call.message.chat.id, "📢 /broadcast [текст]")

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace('/broadcast', '', 1).strip()
    if not text:
        return
    s, f = 0, 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 {text}")
            s += 1
        except:
            f += 1
    bot.send_message(message.chat.id, f"✅ {s} | ❌ {f}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_reset")
def admin_reset_prompt(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.send_message(call.message.chat.id, "🔄 /resetdaily [ID]")

@bot.message_handler(commands=['resetdaily'])
def reset_daily_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        tid = str(message.text.split()[1])
        p = Player(tid)
        p.data["last_daily"] = None
        p.data["last_dungeon"] = None
        p.data["last_work"] = None
        p.save()
        bot.send_message(message.chat.id, f"✅ Сброс {tid}")
    except:
        bot.send_message(message.chat.id, "❌ /resetdaily [ID]")

@bot.callback_query_handler(func=lambda call: call.data == "admin_info")
def admin_info_prompt(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.send_message(call.message.chat.id, "👁 /userinfo [ID]")

@bot.message_handler(commands=['userinfo'])
def user_info_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        tid = str(message.text.split()[1])
        p = Player(tid)
        d = p.data
        text = f"""
<b>👤 {tid}</b>
Имя: {d['first_name']}
Ур.: {d['level']} | 💰 {d['money']}
Рейтинг: {d['pvp_rating']}
Побед: {d['wins']} | Поражений: {d['losses']}
Клан: {d.get('clan', 'Нет')}
Предметов: {len(d['inventory'])}
"""
        bot.send_message(message.chat.id, text)
    except:
        bot.send_message(message.chat.id, "❌ /userinfo [ID]")

# ==================== ЗАПУСК БОТА ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v7.0 — ПОЛНАЯ РЕАЛИЗАЦИЯ ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print(f"⚔ Предметов: {len(items)}")
    print(f"💎 Лимиток: {len(limited_items)}")
    print(f"🛡 Кланов: {len(clans)}")
    print(f"🏟 Турниров: {len(tournaments)}")
    print(f"📦 Лотов: {len(market_listings)}")
    print("=" * 60)
    print("✅ ВСЕ СИСТЕМЫ АКТИВНЫ!")
    print("✅ ПОШАГОВЫЕ ДУЭЛИ С ВЫБОРОМ ЧАСТЕЙ ТЕЛА!")
    print("✅ ЭКИПИРОВКА: ГОЛОВА, ТЕЛО, НОГИ!")
    print("✅ НОЛЬ ЗАГЛУШЕК!")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
