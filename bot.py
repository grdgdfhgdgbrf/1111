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
    "head": {"name": "👤 Голова", "multiplier": 1.5, "base_defense": 3},
    "body": {"name": "🦾 Тело", "multiplier": 1.0, "base_defense": 5},
    "legs": {"name": "🦿 Ноги", "multiplier": 0.7, "base_defense": 2}
}

RARITY_COLORS = {
    "common": "⬜", "uncommon": "🟩", "rare": "🟦",
    "epic": "🟪", "legendary": "🟧", "mythic": "🟥",
    "divine": "💛", "apocalyptic": "🖤"
}

ENCHANT_EFFECTS = [
    {"name": "🔥 Огненное", "effect": "burn_damage", "value": 8},
    {"name": "❄ Ледяное", "effect": "freeze_chance", "value": 25},
    {"name": "⚡ Грозовое", "effect": "stun_chance", "value": 20},
    {"name": "💀 Проклятое", "effect": "life_steal", "value": 15},
    {"name": "🛡 Укреплённое", "effect": "defense_boost", "value": 15},
    {"name": "💪 Мощное", "effect": "damage_boost", "value": 25},
    {"name": "💨 Скоростное", "effect": "speed_boost", "value": 20},
    {"name": "❤ Живучее", "effect": "hp_regen", "value": 5},
    {"name": "🎯 Меткое", "effect": "crit_boost", "value": 20},
    {"name": "🔮 Мистическое", "effect": "random_buff", "value": 10},
    {"name": "🌿 Ядовитое", "effect": "poison_damage", "value": 6},
    {"name": "💎 Магическое", "effect": "mana_steal", "value": 10}
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

# ==================== ПРЕДМЕТЫ (по 10+ в категории) ====================
HELMETS = {
    "leather_cap": {"name": "🎓 Кожаная шапка", "defense": 3, "price": 60, "type": "helmet", "slot": "head", "rarity": "common", "enchantable": True, "skills": ["headbutt"], "description": "Базовая защита головы"},
    "iron_helmet": {"name": "⛑ Железный шлем", "defense": 8, "price": 250, "type": "helmet", "slot": "head", "rarity": "uncommon", "enchantable": True, "skills": ["headbutt", "iron_skull"], "description": "Усиленная защита + атака"},
    "steel_helmet": {"name": "🪖 Стальной шлем", "defense": 12, "price": 600, "type": "helmet", "slot": "head", "rarity": "rare", "enchantable": True, "skills": ["headbutt", "iron_skull", "steel_crash"], "description": "Мощный удар головой"},
    "berserker_helm": {"name": "💢 Шлем берсерка", "defense": 6, "price": 400, "type": "helmet", "slot": "head", "rarity": "uncommon", "enchantable": True, "skills": ["headbutt", "berserk_charge"], "description": "Яростная атака"},
    "dragon_helmet": {"name": "🐉 Шлем дракона", "defense": 18, "price": 2000, "type": "helmet", "slot": "head", "rarity": "epic", "enchantable": True, "element": "fire", "skills": ["dragon_roar", "fire_breath", "headbutt"], "description": "Дышит огнём!"},
    "shadow_hood": {"name": "🌑 Теневой капюшон", "defense": 8, "price": 1800, "type": "helmet", "slot": "head", "rarity": "epic", "enchantable": True, "element": "dark", "skills": ["shadow_step", "dark_veil", "headbutt"], "description": "Скрывает во тьме"},
    "crown_of_wisdom": {"name": "👑 Корона мудрости", "defense": 12, "mana_bonus": 40, "price": 3500, "type": "helmet", "slot": "head", "rarity": "legendary", "enchantable": True, "skills": ["mind_blast", "telepathy", "psychic_wave"], "description": "Психические атаки"},
    "thunder_crown": {"name": "⚡ Корона грома", "defense": 15, "price": 5000, "type": "helmet", "slot": "head", "rarity": "legendary", "enchantable": True, "element": "lightning", "skills": ["lightning_bolt", "thunder_storm", "headbutt"], "description": "Молнии с небес"},
    "frost_crown": {"name": "❄ Ледяная корона", "defense": 14, "price": 4500, "type": "helmet", "slot": "head", "rarity": "legendary", "enchantable": True, "element": "ice", "skills": ["frost_strike", "blizzard", "headbutt"], "description": "Вечный холод"},
    "phoenix_crown": {"name": "🦅 Корона феникса", "defense": 16, "price": 5500, "type": "helmet", "slot": "head", "rarity": "mythic", "enchantable": True, "element": "fire", "skills": ["phoenix_flame", "rebirth", "fire_breath", "headbutt"], "description": "Возрождение из пепла"}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "defense": 5, "price": 80, "type": "armor", "slot": "body", "rarity": "common", "enchantable": True, "skills": ["dodge_roll"], "description": "Лёгкая защита"},
    "chainmail": {"name": "⛓ Кольчуга", "defense": 12, "price": 400, "type": "armor", "slot": "body", "rarity": "uncommon", "enchantable": True, "skills": ["fortify", "spike_armor"], "description": "Шипы для ответного урона"},
    "plate_armor": {"name": "🛡 Латный доспех", "defense": 22, "price": 1500, "type": "armor", "slot": "body", "rarity": "rare", "enchantable": True, "skills": ["iron_wall", "bastion", "shield_slam"], "description": "Мощная защита"},
    "shadow_armor": {"name": "🌑 Теневая броня", "defense": 18, "price": 3000, "type": "armor", "slot": "body", "rarity": "epic", "enchantable": True, "element": "dark", "skills": ["shadow_step", "vanish", "dark_explosion"], "description": "Исчезает в тенях"},
    "phoenix_armor": {"name": "🦅 Броня феникса", "defense": 28, "price": 6000, "type": "armor", "slot": "body", "rarity": "legendary", "enchantable": True, "element": "fire", "skills": ["rebirth", "phoenix_flame", "fire_nova"], "description": "Возрождение"},
    "dragon_armor": {"name": "🐉 Драконья броня", "defense": 32, "price": 7000, "type": "armor", "slot": "body", "rarity": "legendary", "enchantable": True, "element": "fire", "skills": ["fortify", "dragon_roar", "fire_breath"], "description": "Чешуя дракона"},
    "frost_armor": {"name": "❄ Ледяная броня", "defense": 30, "price": 6500, "type": "armor", "slot": "body", "rarity": "legendary", "enchantable": True, "element": "ice", "skills": ["frost_strike", "blizzard", "fortify"], "description": "Ледяная защита"},
    "thunder_armor": {"name": "⚡ Грозовая броня", "defense": 28, "price": 6200, "type": "armor", "slot": "body", "rarity": "legendary", "enchantable": True, "element": "lightning", "skills": ["lightning_bolt", "thunder_storm", "fortify"], "description": "Электрическая защита"},
    "divine_armor": {"name": "✨ Божественная броня", "defense": 35, "price": 9000, "type": "armor", "slot": "body", "rarity": "mythic", "enchantable": True, "element": "light", "skills": ["divine_judgment", "purification", "holy_strike"], "description": "Святая защита"},
    "titan_armor": {"name": "🏛 Броня титана", "defense": 45, "price": 15000, "type": "armor", "slot": "body", "rarity": "mythic", "enchantable": True, "skills": ["iron_wall", "bastion", "shield_slam", "fortify"], "description": "Несокрушимая броня"}
}

BOOTS = {
    "leather_boots": {"name": "👢 Кожаные сапоги", "defense": 2, "speed": 8, "price": 100, "type": "boots", "slot": "legs", "rarity": "common", "enchantable": True, "skills": ["kick", "stomp"], "description": "Базовые удары ногами"},
    "iron_boots": {"name": "🥾 Железные сапоги", "defense": 6, "speed": 4, "price": 300, "type": "boots", "slot": "legs", "rarity": "uncommon", "enchantable": True, "skills": ["stomp", "heavy_kick", "kick"], "description": "Тяжёлые удары"},
    "wind_boots": {"name": "🌪 Сапоги ветра", "defense": 4, "speed": 18, "price": 900, "type": "boots", "slot": "legs", "rarity": "rare", "enchantable": True, "skills": ["tailwind", "gust_kick", "tornado", "kick"], "description": "Ураганные атаки"},
    "blink_boots": {"name": "✨ Сапоги телепортации", "defense": 8, "speed": 28, "price": 4000, "type": "boots", "slot": "legs", "rarity": "epic", "enchantable": True, "skills": ["blink_kick", "phase_strike", "teleport_combo", "kick"], "description": "Телепортация"},
    "hermes_boots": {"name": "👟 Сандалии Гермеса", "defense": 12, "speed": 45, "price": 10000, "type": "boots", "slot": "legs", "rarity": "legendary", "enchantable": True, "skills": ["divine_kick", "mercury_strike", "god_speed", "lightning_feet"], "description": "Скорость бога"},
    "frost_boots": {"name": "❄ Ледяные сапоги", "defense": 10, "speed": 15, "price": 3500, "type": "boots", "slot": "legs", "rarity": "epic", "enchantable": True, "element": "ice", "skills": ["frost_strike", "ice_shatter", "kick", "stomp"], "description": "Замораживает"},
    "flame_boots": {"name": "🔥 Огненные сапоги", "defense": 8, "speed": 20, "price": 3800, "type": "boots", "slot": "legs", "rarity": "epic", "enchantable": True, "element": "fire", "skills": ["fire_slash", "inferno_strike", "kick"], "description": "Огненные следы"},
    "shadow_boots": {"name": "🌑 Теневые сапоги", "defense": 7, "speed": 25, "price": 4200, "type": "boots", "slot": "legs", "rarity": "epic", "enchantable": True, "element": "dark", "skills": ["shadow_step", "assassinate", "kick"], "description": "Шаг в тень"},
    "thunder_boots": {"name": "⚡ Грозовые сапоги", "defense": 9, "speed": 22, "price": 4000, "type": "boots", "slot": "legs", "rarity": "epic", "enchantable": True, "element": "lightning", "skills": ["lightning_bolt", "thunder_storm", "kick"], "description": "Молниеносные"},
    "divine_boots": {"name": "✨ Божественные сапоги", "defense": 14, "speed": 35, "price": 12000, "type": "boots", "slot": "legs", "rarity": "mythic", "enchantable": True, "element": "light", "skills": ["divine_kick", "holy_strike", "purification"], "description": "Святая скорость"}
}

WEAPONS = {
    "rusty_sword": {"name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "slot": "weapon", "rarity": "common", "skills": ["slash", "quick_strike", "heavy_attack"], "enchantable": True, "description": "Базовые атаки"},
    "hunters_bow": {"name": "🏹 Лук охотника", "damage": (7, 14), "price": 150, "type": "weapon", "slot": "weapon", "rarity": "common", "element": "nature", "skills": ["power_shot", "multi_shot", "poison_arrow", "quick_strike"], "enchantable": True, "description": "Ядовитые стрелы"},
    "war_hammer": {"name": "🔨 Боевой молот", "damage": (10, 18), "price": 300, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "skills": ["heavy_attack", "stomp", "shield_slam", "slash"], "enchantable": True, "description": "Сокрушительные удары"},
    "flame_blade": {"name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "element": "fire", "skills": ["fire_slash", "inferno_strike", "flame_wave", "slash", "quick_strike"], "enchantable": True, "description": "Огненные атаки"},
    "frost_axe": {"name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "element": "ice", "skills": ["frost_strike", "ice_shatter", "blizzard", "slash", "heavy_attack"], "enchantable": True, "description": "Замораживает"},
    "storm_staff": {"name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500, "type": "weapon", "slot": "weapon", "rarity": "rare", "element": "lightning", "skills": ["lightning_bolt", "thunder_storm", "chain_lightning", "static_field", "quick_strike"], "enchantable": True, "description": "Молнии"},
    "tidal_blade": {"name": "🌊 Приливной клинок", "damage": (20, 32), "price": 2500, "type": "weapon", "slot": "weapon", "rarity": "rare", "element": "water", "skills": ["water_slash", "tsunami", "drown", "healing_rain", "slash"], "enchantable": True, "description": "Волны"},
    "shadow_dagger": {"name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "slot": "weapon", "rarity": "epic", "element": "dark", "skills": ["shadow_strike", "assassinate", "dark_veil", "soul_drain", "death_mark", "quick_strike"], "enchantable": True, "description": "Теневые атаки"},
    "divine_spear": {"name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "slot": "weapon", "rarity": "legendary", "element": "light", "skills": ["holy_strike", "divine_judgment", "heavenly_light", "purification", "angel_wings", "slash"], "enchantable": True, "description": "Святые атаки"},
    "death_scythe": {"name": "💀 Коса смерти", "damage": (40, 65), "price": 12000, "type": "weapon", "slot": "weapon", "rarity": "mythic", "element": "dark", "skills": ["reap", "death_sentence", "soul_harvest", "darkness_falls", "reaper_fury", "slash", "heavy_attack"], "enchantable": True, "description": "Ультимативная коса"}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common"},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon"},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 200, "price": 350, "type": "potion", "rarity": "rare"},
    "mana_potion": {"name": "💎 Зелье маны", "mana_restore": 60, "price": 60, "type": "potion", "rarity": "common"},
    "berserk_potion": {"name": "💢 Зелье ярости", "damage_boost": 50, "price": 200, "type": "potion", "rarity": "rare"},
    "invisibility_potion": {"name": "👻 Зелье невидимости", "dodge_boost": 50, "price": 400, "type": "potion", "rarity": "epic"},
    "antidote": {"name": "💚 Противоядие", "cure_poison": True, "price": 100, "type": "potion", "rarity": "common"},
    "freeze_potion": {"name": "❄ Замораживающее зелье", "freeze_chance": 80, "price": 300, "type": "potion", "rarity": "rare"},
    "fire_potion": {"name": "🔥 Огненное зелье", "burn_damage": 15, "price": 250, "type": "potion", "rarity": "rare"},
    "speed_potion": {"name": "💨 Зелье скорости", "speed_boost": 30, "price": 350, "type": "potion", "rarity": "epic"}
}

LIMITED_ITEMS = {
    "thunderfury": {"name": "⚡ Ярость грома", "damage": (60, 95), "total": 3, "remaining": 3, "price": 50000, "type": "weapon", "slot": "weapon", "rarity": "divine", "element": "lightning", "skills": ["thunder_gods_wrath", "eye_of_the_storm", "lightning_apocalypse", "zeus_anger", "stormcaller", "slash", "quick_strike"], "enchantable": True, "description": "Меч бога грома"},
    "apocalypse": {"name": "🌋 Апокалипсис", "damage": (80, 140), "total": 2, "remaining": 2, "price": 80000, "type": "weapon", "slot": "weapon", "rarity": "apocalyptic", "element": "dark", "skills": ["world_ender", "obliterate", "void_annihilation", "absolute_zero", "death_sentence", "slash"], "enchantable": True, "description": "Конец всего"},
    "immortal_helmet": {"name": "✨ Шлем бессмертия", "defense": 80, "total": 2, "remaining": 2, "price": 75000, "type": "helmet", "slot": "head", "rarity": "divine", "skills": ["immortality", "divine_shield", "sacred_light", "headbutt"], "enchantable": True, "description": "Неуязвимость"},
    "infinity_armor": {"name": "🌀 Броня бесконечности", "defense": 100, "total": 3, "remaining": 3, "price": 90000, "type": "armor", "slot": "body", "rarity": "divine", "skills": ["infinity", "cosmic_armor", "reality_warp", "fortify", "spike_armor"], "enchantable": True, "description": "Бесконечная защита"},
    "eternal_boots": {"name": "👁 Сапоги вечности", "defense": 50, "speed": 60, "total": 3, "remaining": 3, "price": 60000, "type": "boots", "slot": "legs", "rarity": "divine", "skills": ["god_speed", "divine_kick", "mercury_strike", "blink_kick", "kick"], "enchantable": True, "description": "Вечная скорость"},
    "excalibur": {"name": "⚔ Экскалибур", "damage": (70, 110), "total": 2, "remaining": 2, "price": 100000, "type": "weapon", "slot": "weapon", "rarity": "divine", "element": "light", "skills": ["excalibur_strike", "holy_judgment", "avalon_blessing", "divine_judgment", "holy_strike", "slash"], "enchantable": True, "description": "Меч короля Артура"},
    "void_blade": {"name": "🕳 Клинок пустоты", "damage": (75, 130), "total": 2, "remaining": 2, "price": 95000, "type": "weapon", "slot": "weapon", "rarity": "apocalyptic", "element": "dark", "skills": ["void_slash", "obliterate", "darkness_falls", "reap", "soul_drain", "slash"], "enchantable": True, "description": "Пустота"},
    "phoenix_crown_limited": {"name": "🦅 Корона феникса+", "defense": 60, "total": 3, "remaining": 3, "price": 70000, "type": "helmet", "slot": "head", "rarity": "divine", "element": "fire", "skills": ["rebirth", "phoenix_flame", "fire_nova", "fire_breath", "headbutt"], "enchantable": True, "description": "Возрождение+"},
    "titan_armor_limited": {"name": "🏛 Броня титана+", "defense": 120, "total": 2, "remaining": 2, "price": 110000, "type": "armor", "slot": "body", "rarity": "apocalyptic", "skills": ["iron_wall", "bastion", "shield_slam", "fortify", "spike_armor", "divine_shield"], "enchantable": True, "description": "Несокрушимая+"},
    "lightning_boots_limited": {"name": "⚡ Сапоги молний", "defense": 40, "speed": 70, "total": 3, "remaining": 3, "price": 65000, "type": "boots", "slot": "legs", "rarity": "divine", "element": "lightning", "skills": ["lightning_apocalypse", "thunder_gods_wrath", "god_speed", "lightning_feet", "blink_kick", "kick"], "enchantable": True, "description": "Скорость молнии"}
}

ALL_ITEMS = {}
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(BOOTS)
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(POTIONS)

# ==================== БАЗА НАВЫКОВ (ВСЕ С CD) ====================
SKILLS_DB = {
    # Базовые (CD=0)
    "quick_strike": {"name": "⚡ Быстрый удар", "damage_mult": 0.8, "mana_cost": 0, "cooldown": 0, "description": "Мгновенная атака"},
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 0, "cooldown": 0, "description": "Базовый разрез"},
    "kick": {"name": "👢 Пинок", "damage_mult": 0.6, "mana_cost": 0, "cooldown": 0, "description": "Базовый пинок"},
    "stomp": {"name": "🦶 Топот", "damage_mult": 0.9, "mana_cost": 0, "cooldown": 0, "description": "Тяжёлый топот"},
    "headbutt": {"name": "💢 Удар головой", "damage_mult": 1.3, "mana_cost": 5, "cooldown": 1, "description": "Удар шлемом, CD:1"},
    
    # Оружейные (CD 1-2)
    "power_shot": {"name": "🎯 Мощный выстрел", "damage_mult": 1.8, "mana_cost": 10, "cooldown": 2, "description": "Прицельный выстрел, CD:2"},
    "multi_shot": {"name": "🏹 Залп", "damage_mult": 0.7, "mana_cost": 15, "cooldown": 2, "hits": 3, "description": "Три стрелы, CD:2"},
    "poison_arrow": {"name": "🌿 Ядовитая стрела", "damage_mult": 1.3, "mana_cost": 12, "cooldown": 2, "poison_chance": 60, "description": "Яд, CD:2"},
    "heavy_attack": {"name": "💪 Тяжёлая атака", "damage_mult": 1.6, "mana_cost": 12, "cooldown": 1, "description": "Мощный удар, CD:1"},
    
    # Огненные (CD 1-3)
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.5, "mana_cost": 12, "cooldown": 1, "element": "fire", "burn_chance": 30, "description": "Огонь, CD:1"},
    "inferno_strike": {"name": "🌋 Инферно удар", "damage_mult": 2.3, "mana_cost": 28, "cooldown": 3, "element": "fire", "burn_chance": 60, "description": "Мощный огонь, CD:3"},
    "flame_wave": {"name": "🔥 Волна пламени", "damage_mult": 2.8, "mana_cost": 35, "cooldown": 3, "element": "fire", "description": "Огненная волна, CD:3"},
    "fire_breath": {"name": "🐉 Огненное дыхание", "damage_mult": 2.0, "mana_cost": 20, "cooldown": 2, "element": "fire", "burn_chance": 50, "description": "Дыхание дракона, CD:2"},
    
    # Ледяные (CD 1-3)
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.4, "mana_cost": 10, "cooldown": 1, "element": "ice", "freeze_chance": 25, "description": "Лёд, CD:1"},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.0, "mana_cost": 22, "cooldown": 2, "element": "ice", "freeze_chance": 50, "description": "Мощный лёд, CD:2"},
    "blizzard": {"name": "🌨 Метель", "damage_mult": 2.4, "mana_cost": 32, "cooldown": 3, "element": "ice", "description": "Ледяной шторм, CD:3"},
    
    # Молнии (CD 1-3)
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.6, "mana_cost": 14, "cooldown": 1, "element": "lightning", "stun_chance": 20, "description": "Электричество, CD:1"},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.3, "mana_cost": 30, "cooldown": 3, "element": "lightning", "stun_chance": 35, "description": "Гроза, CD:3"},
    "chain_lightning": {"name": "⚡ Цепная молния", "damage_mult": 1.8, "mana_cost": 20, "cooldown": 2, "element": "lightning", "description": "Цепь, CD:2"},
    "static_field": {"name": "🔌 Статическое поле", "damage_mult": 2.5, "mana_cost": 35, "cooldown": 3, "element": "lightning", "description": "Поле, CD:3"},
    
    # Водяные (CD 1-3)
    "water_slash": {"name": "🌊 Водяной разрез", "damage_mult": 1.3, "mana_cost": 10, "cooldown": 1, "element": "water", "description": "Вода, CD:1"},
    "tsunami": {"name": "🌊 Цунами", "damage_mult": 2.1, "mana_cost": 28, "cooldown": 3, "element": "water", "description": "Волна, CD:3"},
    "drown": {"name": "💧 Утопление", "damage_mult": 1.9, "mana_cost": 22, "cooldown": 2, "element": "water", "description": "Захлёбывание, CD:2"},
    "healing_rain": {"name": "🌧 Исцеляющий дождь", "hp_restore": 80, "mana_cost": 30, "cooldown": 3, "element": "water", "description": "Лечение +80 HP, CD:3"},
    
    # Теневые (CD 1-5)
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.6, "mana_cost": 14, "cooldown": 1, "element": "dark", "poison_chance": 25, "description": "Тень, CD:1"},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.5, "mana_cost": 45, "cooldown": 4, "element": "dark", "ignore_defense": 50, "description": "Игнор 50% защиты, CD:4"},
    "soul_drain": {"name": "💀 Похищение души", "damage_mult": 2.0, "mana_cost": 25, "cooldown": 3, "element": "dark", "life_steal": 0.4, "description": "Вампиризм 40%, CD:3"},
    "dark_veil": {"name": "🌑 Завеса тьмы", "defense_boost": 30, "mana_cost": 20, "cooldown": 2, "element": "dark", "description": "Защита +30, CD:2"},
    "death_mark": {"name": "💀 Метка смерти", "damage_mult": 2.5, "mana_cost": 30, "cooldown": 4, "element": "dark", "description": "Метка, CD:4"},
    "reap": {"name": "💀 Жатва", "damage_mult": 2.5, "mana_cost": 30, "cooldown": 3, "element": "dark", "life_steal": 0.3, "description": "Жатва, CD:3"},
    "death_sentence": {"name": "☠ Смертный приговор", "damage_mult": 4.0, "mana_cost": 55, "cooldown": 5, "element": "dark", "description": "Ультиматум, CD:5"},
    "soul_harvest": {"name": "👻 Сбор душ", "damage_mult": 3.0, "mana_cost": 40, "cooldown": 4, "element": "dark", "life_steal": 0.5, "description": "Вампиризм 50%, CD:4"},
    "darkness_falls": {"name": "🌑 Падение тьмы", "damage_mult": 4.5, "mana_cost": 60, "cooldown": 6, "element": "dark", "description": "Тьма, CD:6"},
    "reaper_fury": {"name": "💢 Ярость жнеца", "damage_mult": 5.0, "mana_cost": 70, "cooldown": 6, "element": "dark", "life_steal": 0.5, "description": "Ультиматум, CD:6"},
    
    # Святые (CD 1-5)
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.5, "mana_cost": 12, "cooldown": 1, "element": "light", "description": "Святость, CD:1"},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 2.8, "mana_cost": 35, "cooldown": 3, "element": "light", "description": "Суд, CD:3"},
    "heavenly_light": {"name": "🌟 Небесный свет", "hp_restore": 60, "mana_cost": 25, "cooldown": 2, "element": "light", "description": "Лечение +60, CD:2"},
    "purification": {"name": "🌟 Очищение", "hp_restore": 100, "mana_cost": 40, "cooldown": 4, "element": "light", "cure_all": True, "description": "Полное исцеление, CD:4"},
    "angel_wings": {"name": "👼 Крылья ангела", "dodge_boost": 50, "mana_cost": 35, "cooldown": 4, "element": "light", "description": "Уклонение +50%, CD:4"},
    
    # Защитные (CD 1-3)
    "dodge_roll": {"name": "🔄 Перекат", "dodge_boost": 40, "mana_cost": 8, "cooldown": 2, "description": "Уклонение +40%, CD:2"},
    "fortify": {"name": "🛡 Укрепление", "defense_boost": 30, "mana_cost": 12, "cooldown": 2, "description": "Защита +30, CD:2"},
    "spike_armor": {"name": "🦔 Шипы", "damage_reflect": 25, "mana_cost": 15, "cooldown": 3, "description": "Отражает 25% урона, CD:3"},
    "iron_wall": {"name": "🧱 Железная стена", "defense_boost": 50, "mana_cost": 20, "cooldown": 3, "description": "Защита +50, CD:3"},
    "bastion": {"name": "🏰 Бастион", "defense_boost": 40, "hp_restore": 30, "mana_cost": 25, "cooldown": 3, "description": "Защита + лечение, CD:3"},
    "shield_slam": {"name": "💥 Удар щитом", "damage_mult": 1.8, "mana_cost": 15, "cooldown": 2, "stun_chance": 25, "description": "Контратака, CD:2"},
    "shadow_step": {"name": "👣 Шаг в тень", "dodge_boost": 60, "mana_cost": 15, "cooldown": 3, "description": "Уклонение +60%, CD:3"},
    "vanish": {"name": "🌫 Исчезновение", "invincible": 1, "mana_cost": 30, "cooldown": 4, "description": "Неуязвимость, CD:4"},
    "dark_explosion": {"name": "💥 Тёмный взрыв", "damage_mult": 3.0, "mana_cost": 35, "cooldown": 4, "element": "dark", "description": "Взрыв тьмы, CD:4"},
    "rebirth": {"name": "🦅 Возрождение", "hp_restore": 150, "mana_cost": 50, "cooldown": 5, "description": "+150 HP, CD:5"},
    "phoenix_flame": {"name": "🔥 Пламя феникса", "damage_mult": 3.0, "mana_cost": 35, "cooldown": 4, "element": "fire", "hp_restore": 50, "description": "Атака + лечение, CD:4"},
    "fire_nova": {"name": "💫 Огненная нова", "damage_mult": 3.5, "mana_cost": 45, "cooldown": 5, "element": "fire", "description": "Мощный взрыв, CD:5"},
    
    # Ноги (CD 1-4)
    "tailwind": {"name": "💨 Попутный ветер", "speed_boost": 25, "mana_cost": 10, "cooldown": 2, "description": "Скорость +25, CD:2"},
    "gust_kick": {"name": "🌬 Удар ветра", "damage_mult": 1.8, "mana_cost": 15, "cooldown": 2, "description": "Ветряной удар, CD:2"},
    "tornado": {"name": "🌪 Торнадо", "damage_mult": 2.5, "mana_cost": 28, "cooldown": 3, "description": "Вихрь, CD:3"},
    "heavy_kick": {"name": "🦶 Тяжёлый пинок", "damage_mult": 1.5, "mana_cost": 10, "cooldown": 1, "description": "Тяжёлый удар, CD:1"},
    "blink_kick": {"name": "✨ Телепорт-удар", "damage_mult": 2.0, "mana_cost": 20, "cooldown": 3, "description": "Телепортация, CD:3"},
    "phase_strike": {"name": "🌌 Фазовый удар", "damage_mult": 2.5, "mana_cost": 25, "cooldown": 3, "ignore_defense": 30, "description": "Игнор 30% защиты, CD:3"},
    "teleport_combo": {"name": "⚡ Телепорт-комбо", "damage_mult": 3.0, "mana_cost": 35, "cooldown": 4, "hits": 3, "description": "Три удара, CD:4"},
    "divine_kick": {"name": "✨ Божественный пинок", "damage_mult": 3.5, "mana_cost": 40, "cooldown": 4, "element": "light", "description": "Божественный, CD:4"},
    "mercury_strike": {"name": "💫 Удар Меркурия", "damage_mult": 4.0, "mana_cost": 50, "cooldown": 5, "description": "Ультимативный, CD:5"},
    "god_speed": {"name": "⚡ Скорость бога", "speed_boost": 50, "mana_cost": 35, "cooldown": 4, "description": "Скорость +50, CD:4"},
    "lightning_feet": {"name": "👟 Молниеносные ноги", "damage_mult": 3.0, "mana_cost": 30, "cooldown": 3, "element": "lightning", "description": "Молнии, CD:3"},
    
    # Голова (CD 1-3)
    "iron_skull": {"name": "🪖 Железный череп", "damage_mult": 1.8, "mana_cost": 15, "cooldown": 2, "stun_chance": 30, "description": "Мощный удар, CD:2"},
    "steel_crash": {"name": "💥 Стальной удар", "damage_mult": 2.2, "mana_cost": 20, "cooldown": 2, "stun_chance": 40, "description": "Сокрушительный, CD:2"},
    "berserk_charge": {"name": "💢 Берсерк", "damage_mult": 2.5, "mana_cost": 25, "cooldown": 3, "description": "Яростная атака, CD:3"},
    "dragon_roar": {"name": "🐉 Рёв дракона", "damage_mult": 2.2, "mana_cost": 25, "cooldown": 3, "element": "fire", "stun_chance": 30, "description": "Оглушение, CD:3"},
    "mind_blast": {"name": "🧠 Ментальный удар", "damage_mult": 2.0, "mana_cost": 22, "cooldown": 2, "stun_chance": 40, "description": "Пси-атака, CD:2"},
    "telepathy": {"name": "👁 Телепатия", "damage_mult": 1.8, "mana_cost": 18, "cooldown": 1, "description": "Чтение мыслей, CD:1"},
    "psychic_wave": {"name": "🌊 Пси-волна", "damage_mult": 3.0, "mana_cost": 35, "cooldown": 4, "description": "Пси-шторм, CD:4"},
    
    # Ультимативные (CD 5-7)
    "thunder_gods_wrath": {"name": "⚡ Гнев бога грома", "damage_mult": 4.5, "mana_cost": 70, "cooldown": 5, "element": "lightning", "stun_chance": 50, "description": "Ультимейт, CD:5"},
    "eye_of_the_storm": {"name": "🌀 Глаз бури", "damage_mult": 3.0, "mana_cost": 45, "cooldown": 4, "element": "lightning", "description": "Ураган, CD:4"},
    "lightning_apocalypse": {"name": "⚡ Апокалипсис", "damage_mult": 5.0, "mana_cost": 85, "cooldown": 6, "element": "lightning", "description": "Абсолют, CD:6"},
    "zeus_anger": {"name": "🔱 Гнев Зевса", "damage_mult": 5.5, "mana_cost": 90, "cooldown": 7, "element": "lightning", "description": "Божественный гнев, CD:7"},
    "stormcaller": {"name": "🌩 Призыв бури", "damage_mult": 3.5, "mana_cost": 50, "cooldown": 4, "element": "lightning", "description": "Буря, CD:4"},
    
    "world_ender": {"name": "🌋 Конец света", "damage_mult": 5.5, "mana_cost": 100, "cooldown": 7, "element": "dark", "description": "Абсолют, CD:7"},
    "obliterate": {"name": "💥 Уничтожение", "damage_mult": 6.0, "mana_cost": 110, "cooldown": 8, "element": "dark", "description": "Полное, CD:8"},
    "void_annihilation": {"name": "🕳 Аннигиляция", "damage_mult": 7.0, "mana_cost": 120, "cooldown": 10, "element": "dark", "description": "Аннигиляция, CD:10"},
    "absolute_zero": {"name": "❄ Абсолютный ноль", "damage_mult": 6.0, "mana_cost": 100, "cooldown": 8, "element": "ice", "description": "Заморозка, CD:8"},
    
    "immortality": {"name": "✨ Бессмертие", "invincible": 2, "mana_cost": 50, "cooldown": 6, "description": "Неуязвимость 2 хода, CD:6"},
    "divine_shield": {"name": "🛡 Божественный щит", "defense_boost": 100, "mana_cost": 40, "cooldown": 5, "description": "Защита +100, CD:5"},
    "sacred_light": {"name": "🌟 Священный свет", "hp_restore": 200, "mana_cost": 60, "cooldown": 5, "description": "+200 HP, CD:5"},
    
    "excalibur_strike": {"name": "⚔ Удар Экскалибура", "damage_mult": 5.0, "mana_cost": 80, "cooldown": 6, "element": "light", "description": "Легендарный, CD:6"},
    "holy_judgment": {"name": "⚖ Святой суд", "damage_mult": 4.5, "mana_cost": 70, "cooldown": 5, "element": "light", "description": "Суд, CD:5"},
    "avalon_blessing": {"name": "🏰 Благословение", "hp_restore": 150, "mana_cost": 50, "cooldown": 5, "element": "light", "description": "+150 HP, CD:5"},
    
    "infinity": {"name": "🌀 Бесконечность", "invincible": 2, "mana_cost": 60, "cooldown": 7, "description": "Неуязвимость 2 хода, CD:7"},
    "cosmic_armor": {"name": "🌌 Космическая броня", "defense_boost": 150, "mana_cost": 50, "cooldown": 6, "description": "Защита +150, CD:6"},
    "reality_warp": {"name": "🔮 Искажение", "damage_mult": 5.0, "mana_cost": 80, "cooldown": 7, "description": "Искажение, CD:7"}
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
world_boss_data = load_json(DATA_FILES['world_boss'], {})

# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================
def find_user_by_identifier(identifier):
    identifier = str(identifier).strip()
    if identifier.startswith('@'):
        identifier = identifier[1:]
    identifier_lower = identifier.lower()
    
    if identifier in users:
        return identifier
    
    for uid, data in users.items():
        if data.get("username", "").lower() == identifier_lower:
            return uid
        if data.get("first_name", "").lower() == identifier_lower:
            return uid
        if identifier_lower in data.get("username", "").lower():
            return uid
        if identifier_lower in data.get("first_name", "").lower():
            return uid
    
    return None

def get_player_display_name(uid):
    if uid.startswith("bot_"):
        return users.get(uid, {}).get("first_name", "🤖 Бот")
    if uid.startswith("boss_"):
        return users.get(uid, {}).get("first_name", "👹 Босс")
    data = users.get(uid, {})
    name = data.get("first_name", "Игрок")
    uname = data.get("username", "")
    if uname:
        return f"{name} (@{uname})"
    return name

def send_notification(user_id, message):
    try:
        bot.send_message(int(user_id), message)
    except:
        pass

def safe_edit_or_send(chat_id, message_id, text, reply_markup=None):
    try:
        bot.edit_message_text(text[:4000], chat_id, message_id, reply_markup=reply_markup)
    except:
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        new_msg = bot.send_message(chat_id, text[:4000], reply_markup=reply_markup)
        return new_msg.message_id
    return message_id

# ==================== КЛАСС ИГРОКА ====================
class Player:
    def __init__(self, user_id, username="", first_name=""):
        self.user_id = str(user_id)
        if self.user_id not in users:
            users[self.user_id] = {
                "username": username or "",
                "first_name": first_name or f"Игрок{user_id}",
                "money": 500, "level": 1, "exp": 0, "total_exp": 0,
                "hp": 100, "max_hp": 100, "mana": 50, "max_mana": 50,
                "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
                "total_duels": 0, "pvp_rating": 1000,
                "inventory": [],
                "equipment": {"weapon": None, "head": None, "body": None, "legs": None},
                "enchantments": {},
                "last_daily": None, "last_dungeon": None,
                "title": "Новичок", "titles_collected": ["Новичок"],
                "achievements": [], "clan": None, "clan_role": None,
                "registration_date": datetime.now().isoformat(),
                "settings": {"notifications": True, "duel_requests": True},
                "battle_history": [], "dungeons_completed": 0, "items_found": 0,
                "world_boss_damage": 0, "clan_donations": 0
            }
            self.save()
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    def save(self):
        save_json(DATA_FILES['users'], users)
    
    def get_all_skills(self):
        all_skills = []
        for slot, ik in self.data["equipment"].items():
            if not ik:
                continue
            item = items.get(ik) or limited_items.get(ik)
            if item and "skills" in item:
                all_skills.extend(item["skills"])
        # Добавляем базовые атаки всегда
        all_skills.extend(["quick_strike", "slash", "kick", "stomp"])
        return list(set(all_skills))
    
    def get_equipment_defense(self, part):
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
        ench = self.data.get("enchantments", {}).get(ik, {})
        if ench.get("effect") == "defense_boost":
            defense += ench.get("value", 0)
        return defense
    
    def get_total_defense_display(self):
        parts = {
            "head": self.get_equipment_defense("head") + BODY_PARTS["head"]["base_defense"],
            "body": self.get_equipment_defense("body") + BODY_PARTS["body"]["base_defense"],
            "legs": self.get_equipment_defense("legs") + BODY_PARTS["legs"]["base_defense"]
        }
        return f"🛡 Защита: Г:{parts['head']} Т:{parts['body']} Н:{parts['legs']}"

# ==================== ДУЭЛИ ====================
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
        self.last_action_time = datetime.now()
        self.idle_timeout = 120
        
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
        
        self.round_type = "p1_defend_p2_attack"
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        self.p1_effects = {}
        self.p2_effects = {}
        
        p1_name = get_player_display_name(self.p1_id)
        p2_name = get_player_display_name(self.p2_id)
        p1_def = self.p1.get_total_defense_display()
        p2_def = self.p2.get_total_defense_display()
        
        self._add_log(1, f"⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>\nПротивник: {p2_name}\n{p2_def}\n💰 Ставка: {bet}💰\n⏰ Тайм-аут: 2 мин")
        self._add_log(2, f"⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>\nПротивник: {p1_name}\n{p1_def}\n💰 Ставка: {bet}💰\n⏰ Тайм-аут: 2 мин")
        
        if self.round_type == "p1_defend_p2_attack":
            self._add_log(1, f"\n🛡 <b>ВЫ ЗАЩИЩАЕТЕСЬ!</b>\n{p2_name} будет атаковать.\n{p1_def}\n\nВыберите часть тела для защиты:")
            self._add_log(2, f"\n⚔ <b>ВЫ АТАКУЕТЕ!</b>\n{p1_name} выбирает защиту...\n{p2_def}\n\nОжидание...")
        else:
            self._add_log(2, f"\n🛡 <b>ВЫ ЗАЩИЩАЕТЕСЬ!</b>\n{p1_name} будет атаковать.\n{p2_def}\n\nВыберите часть тела для защиты:")
            self._add_log(1, f"\n⚔ <b>ВЫ АТАКУЕТЕ!</b>\n{p2_name} выбирает защиту...\n{p1_def}\n\nОжидание...")
    
    def _add_log(self, player_num, msg):
        if player_num == 1:
            self.log_p1.append(msg)
        else:
            self.log_p2.append(msg)
    
    def check_idle(self):
        elapsed = (datetime.now() - self.last_action_time).seconds
        if elapsed > self.idle_timeout:
            if self.round_type == "p1_defend_p2_attack":
                self.active = False
                self.winner = 1
                self._add_log(1, "⏰ Противник не ответил! Победа!")
                self._add_log(2, "⏰ Время вышло! Поражение!")
            else:
                self.active = False
                self.winner = 2
                self._add_log(2, "⏰ Противник не ответил! Победа!")
                self._add_log(1, "⏰ Время вышло! Поражение!")
            return True
        return False
    
    def set_defend(self, player_num, part):
        if player_num == 1:
            self.p1_defend = part
            part_def = self.p1.get_equipment_defense(part) + BODY_PARTS[part]["base_defense"]
            self._add_log(1, f"🛡 Вы защищаете: <b>{BODY_PARTS[part]['name']}</b> (DEF: {part_def})")
        else:
            self.p2_defend = part
            part_def = self.p2.get_equipment_defense(part) + BODY_PARTS[part]["base_defense"]
            self._add_log(2, f"🛡 Вы защищаете: <b>{BODY_PARTS[part]['name']}</b> (DEF: {part_def})")
        
        self.last_action_time = datetime.now()
        self._check_round()
    
    def set_attack(self, player_num, skill_id, target_part):
        if player_num == 1:
            self.p1_skill = skill_id
            self.p1_target = target_part
        else:
            self.p2_skill = skill_id
            self.p2_target = target_part
        
        self.last_action_time = datetime.now()
        self._check_round()
    
    def _check_round(self):
        if self.round_type == "p1_defend_p2_attack":
            if self.p1_defend and self.p2_skill and self.p2_target:
                self._execute_attack(2, 1)
                self._switch_round()
        else:
            if self.p2_defend and self.p1_skill and self.p1_target:
                self._execute_attack(1, 2)
                self._switch_round()
    
    def _execute_attack(self, attacker, defender):
        skill_id = self.p1_skill if attacker == 1 else self.p2_skill
        target_part = self.p1_target if attacker == 1 else self.p2_target
        defend_part = self.p1_defend if defender == 1 else self.p2_defend
        
        skill = SKILLS_DB.get(skill_id, {"name": "Атака", "damage_mult": 1.0, "mana_cost": 0})
        attacker_player = self.p1 if attacker == 1 else self.p2
        defender_player = self.p1 if defender == 1 else self.p2
        
        mc = skill.get("mana_cost", 0)
        if attacker == 1:
            if self.p1_mp < mc:
                self._add_log(1, "❌ Недостаточно маны!")
                return
            self.p1_mp -= mc
        else:
            if self.p2_mp < mc:
                self._add_log(2, "❌ Недостаточно маны!")
                return
            self.p2_mp -= mc
        
        # Урон
        weapon = attacker_player.data["equipment"].get("weapon")
        weapon_item = items.get(weapon) or limited_items.get(weapon) if weapon else None
        min_d = weapon_item["damage"][0] if weapon_item else 5
        max_d = weapon_item["damage"][1] if weapon_item else 15
        
        base_dmg = random.randint(min_d, max_d) + attacker_player.data["level"] * 2
        dmg = int(base_dmg * skill.get("damage_mult", 1.0))
        dmg = int(dmg * BODY_PARTS.get(target_part, {}).get("multiplier", 1.0))
        
        # Защита
        base_def = BODY_PARTS.get(target_part, {}).get("base_defense", 3)
        equip_def = defender_player.get_equipment_defense(target_part)
        total_def = base_def + equip_def
        reduction = total_def / (total_def + 40)
        blocked = int(dmg * reduction)
        final_dmg = dmg - blocked
        
        blocked_icon = ""
        if defend_part == target_part:
            final_dmg = 0
            blocked_icon = " 🛡ЗАЩИЩЕНО!"
            blocked = dmg
        
        final_dmg = max(0, final_dmg)
        
        if defender == 1:
            self.p1_hp = max(0, self.p1_hp - final_dmg)
        else:
            self.p2_hp = max(0, self.p2_hp - final_dmg)
        
        attacker_name = get_player_display_name(self.p1_id) if attacker == 1 else get_player_display_name(self.p2_id)
        defender_name = get_player_display_name(self.p2_id) if attacker == 1 else get_player_display_name(self.p1_id)
        skill_name = skill.get("name", "Атака")
        
        if defend_part == target_part:
            self._add_log(attacker, f"⚔ [{skill_name}] → {BODY_PARTS[target_part]['name']}\n🛡 {defender_name} защитил!\n💥 <b>0 HP</b> ✅")
            self._add_log(defender, f"💢 {attacker_name} [{skill_name}] → {BODY_PARTS[target_part]['name']}\n🛡 Вы защитили!\n💥 <b>0 HP</b> ✅")
        else:
            self._add_log(attacker, f"⚔ [{skill_name}] → {BODY_PARTS[target_part]['name']}\n💥 <b>-{final_dmg} HP</b> (броня: -{blocked})")
            self._add_log(defender, f"💢 {attacker_name} [{skill_name}] → {BODY_PARTS[target_part]['name']}\n💥 <b>-{final_dmg} HP</b> (броня: -{blocked})")
        
        # Кулдауны
        if "cooldown" in skill and skill["cooldown"] > 0:
            cd = skill["cooldown"]
            if attacker == 1:
                self.p1_cooldowns[skill_id] = cd
            else:
                self.p2_cooldowns[skill_id] = cd
        
        cooldowns = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
        for sid in list(cooldowns.keys()):
            cooldowns[sid] -= 1
            if cooldowns[sid] <= 0:
                del cooldowns[sid]
        
        if attacker == 1:
            self.p1_mp = min(self.p1_max_mp, self.p1_mp + 3)
        else:
            self.p2_mp = min(self.p2_max_mp, self.p2_mp + 3)
        
        if self.p1_hp <= 0:
            self.active = False
            self.winner = 2
        elif self.p2_hp <= 0:
            self.active = False
            self.winner = 1
    
    def _switch_round(self):
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        
        p1_name = get_player_display_name(self.p1_id)
        p2_name = get_player_display_name(self.p2_id)
        p1_def = self.p1.get_total_defense_display()
        p2_def = self.p2.get_total_defense_display()
        
        if self.round_type == "p1_defend_p2_attack":
            self.round_type = "p2_defend_p1_attack"
            self._add_log(2, f"\n🛡 <b>ВЫ ЗАЩИЩАЕТЕСЬ!</b>\n{p1_name} атакует.\n{p2_def}\n\nВыберите часть тела:")
            self._add_log(1, f"\n⚔ <b>ВЫ АТАКУЕТЕ!</b>\n{p2_name} защищается.\n{p1_def}\n\nОжидание...")
        else:
            self.round_type = "p1_defend_p2_attack"
            self._add_log(1, f"\n🛡 <b>ВЫ ЗАЩИЩАЕТЕСЬ!</b>\n{p2_name} атакует.\n{p1_def}\n\nВыберите часть тела:")
            self._add_log(2, f"\n⚔ <b>ВЫ АТАКУЕТЕ!</b>\n{p1_name} защищается.\n{p2_def}\n\nОжидание...")
        
        self.turn += 1
        if self.turn > self.max_turns:
            self.active = False
            self.winner = 0
    
    def get_state_text(self, for_player_id):
        pn = 1 if str(for_player_id) == self.p1_id else 2
        is_defending = (self.round_type == "p1_defend_p2_attack" and pn == 1) or (self.round_type == "p2_defend_p1_attack" and pn == 2)
        
        my_hp = self.p1_hp if pn == 1 else self.p2_hp
        opp_hp = self.p2_hp if pn == 1 else self.p1_hp
        my_mp = self.p1_mp if pn == 1 else self.p2_mp
        opponent_name = get_player_display_name(self.p2_id) if pn == 1 else get_player_display_name(self.p1_id)
        opponent_player = self.p2 if pn == 1 else self.p1
        opp_def = opponent_player.get_total_defense_display()
        my_def = (self.p1 if pn == 1 else self.p2).get_total_defense_display()
        
        def bar(val, icon):
            pct = min(100, val)
            f = int(pct / 10)
            e = 10 - f
            color = "🟢" if pct > 50 else "🟡" if pct > 25 else "🔴"
            return f"{icon} {color}[{'█'*f}{'░'*e}] {val}/100"
        
        text = f"<b>⚔ ДУЭЛЬ</b> | Ход <b>{self.turn}</b>\n"
        text += f"Вы: {bar(my_hp, '❤')} | MP: {my_mp}\n{my_def}\n\n"
        text += f"{opponent_name}: {bar(opp_hp, '❤')}\n{opp_def}\n"
        text += "━━━━━━━━━━━━\n"
        
        if is_defending:
            text += "\n🛡 <b>ВЫ ЗАЩИЩАЕТЕСЬ!</b>\nВыберите часть тела:"
        else:
            text += "\n⚔ <b>ВЫ АТАКУЕТЕ!</b>\nВыберите цель и навык:"
        
        my_log = self.log_p1 if pn == 1 else self.log_p2
        if my_log:
            text += f"\n\n<i>{my_log[-1][:200]}</i>"
        
        return text
    
    def get_available_skills(self, player_num):
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        player = self.p1 if player_num == 1 else self.p2
        all_skills = player.get_all_skills()
        
        available = []
        for sid in all_skills:
            if sid in SKILLS_DB and sid not in cooldowns:
                available.append(sid)
        
        return list(set(available))

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
    
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or f"Игрок{user_id}"
    
    if str(user_id) in users:
        users[str(user_id)]["username"] = username
        users[str(user_id)]["first_name"] = first_name
        save_json(DATA_FILES['users'], users)
    else:
        Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v14.0 ⚔️</b>

Привет, <b>{first_name}</b>!

🎯 <b>НОВОЕ:</b>
• 10+ предметов в каждой категории!
• 10 лимитированных предметов!
• Кулдауны на ВСЕХ атаках!
• Броня уменьшает урон
• Защита части тела = 0 урона
• Тайм-аут бездействия 2 мин

💰 Старт: <b>500 монет</b>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль (бот)", callback_data="quick_duel"),
        types.InlineKeyboardButton("👥 Найти соперника", callback_data="find_opponent"),
        types.InlineKeyboardButton("🏆 Рейтинговая", callback_data="ranked_duel"),
        types.InlineKeyboardButton("💀 Хардкор", callback_data="hardcore_duel"),
        types.InlineKeyboardButton("🎯 Спарринг", callback_data="sparring_duel")
    )
    bot.send_message(message.chat.id, "<b>⚔️ ДУЭЛИ</b>\n\nПошаговая система!\nЗащита → Атака → Смена ролей\nВыберите тип:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="hero_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="hero_inventory"),
        types.InlineKeyboardButton("⚡ Навыки", callback_data="hero_skills"),
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
        types.InlineKeyboardButton("💎 Лимитированные (10)", callback_data="trade_limited"),
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

# ==================== ЗАПУСК ДУЭЛЕЙ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["quick_duel", "find_opponent", "ranked_duel", "hardcore_duel", "sparring_duel"])
def duel_type_handler(call):
    dt = call.data
    
    if dt == "quick_duel":
        markup = types.InlineKeyboardMarkup(row_width=3)
        for bet in [50, 100, 200, 500, 1000]:
            markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"qduel_{bet}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
        player = Player(call.from_user.id)
        bot.edit_message_text(f"<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n💰 {player.data['money']}💰\nСтавка:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif dt == "find_opponent":
        start_matchmaking(call, "pvp", 50)
    elif dt == "ranked_duel":
        start_matchmaking(call, "ranked", 100)
    elif dt == "hardcore_duel":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for bet in [500, 1000, 2000]:
            markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"hduel_{bet}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
        player = Player(call.from_user.id)
        bot.edit_message_text(f"<b>💀 ХАРДКОР</b>\n💰 {player.data['money']}💰\nСтавка:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif dt == "sparring_duel":
        start_bot_duel(call.message.chat.id, call.message.message_id, call.from_user.id, "sparring", 0)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_duels")
def back_to_duels(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    duel_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def quick_duel_start(call):
    bet = int(call.data.split("_")[1])
    start_bot_duel(call.message.chat.id, call.message.message_id, call.from_user.id, "quick", bet)

@bot.callback_query_handler(func=lambda call: call.data.startswith("hduel_"))
def hardcore_duel_start(call):
    bet = int(call.data.split("_")[1])
    start_bot_duel(call.message.chat.id, call.message.message_id, call.from_user.id, "hardcore", bet)

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
            op = Player(opponent["user_id"])
            op.data["money"] -= bet
            player.save()
            op.save()
        
        duel = DuelInstance(opponent["user_id"], user_id, duel_type, bet)
        active_duels[user_id] = duel
        active_duels[opponent["user_id"]] = duel
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        new_msg = bot.send_message(call.message.chat.id, "⚔ Соперник найден!")
        show_duel_interface(call.message.chat.id, new_msg.message_id, duel, user_id)
        
        try:
            opp_msg = bot.send_message(int(opponent["user_id"]), "⚔ Дуэль!")
            show_duel_interface(int(opponent["user_id"]), opp_msg.message_id, duel, opponent["user_id"])
        except:
            pass
    else:
        queue.append({"user_id": user_id, "bet": bet})
        matchmaking_queue[duel_type] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        bot.edit_message_text("🔍 Поиск... Бот через 7с", call.message.chat.id, call.message.message_id)
        threading.Timer(7.0, start_bot_if_no_opponent, args=[call.message.chat.id, call.message.message_id, user_id, duel_type, bet]).start()

def start_bot_if_no_opponent(chat_id, message_id, user_id, duel_type, bet):
    if str(user_id) in active_duels:
        return
    start_bot_duel(chat_id, message_id, user_id, duel_type, bet)

def start_bot_duel(chat_id, message_id, user_id, duel_type, bet):
    player = Player(user_id)
    if bet > 0 and player.data["money"] < bet:
        bot.edit_message_text(f"❌ Нужно {bet}💰!", chat_id, message_id)
        return
    
    bot_level = random.randint(max(1, player.data["level"] - 5), player.data["level"] + 5)
    bot_id = f"bot_{random.randint(100000, 999999)}"
    
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    for slot, itype in [("head", "helmet"), ("body", "armor"), ("legs", "boots")]:
        sitems = [k for k, v in items.items() if v.get("type") == itype]
        if sitems and random.random() < 0.7:
            equip[slot] = random.choice(sitems)
    wpns = [k for k, v in items.items() if v.get("type") == "weapon"]
    if wpns:
        equip["weapon"] = random.choice(wpns)
    
    users[bot_id] = {"username": "", "first_name": f"🤖 Бот Lv.{bot_level}", "money": 0, "level": bot_level, "exp": 0, "total_exp": 0, "hp": 100, "max_hp": 100, "mana": 50, "max_mana": 50, "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0, "total_duels": 0, "pvp_rating": 1000, "inventory": [], "equipment": equip, "enchantments": {}, "last_daily": None, "last_dungeon": None, "title": "Бот", "titles_collected": ["Бот"], "achievements": [], "clan": None, "clan_role": None, "registration_date": datetime.now().isoformat(), "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0, "world_boss_damage": 0, "clan_donations": 0}
    save_json(DATA_FILES['users'], users)
    
    if bet > 0:
        player.data["money"] -= bet
        player.save()
    
    duel = DuelInstance(user_id, bot_id, duel_type, bet)
    active_duels[str(user_id)] = duel
    
    bot.edit_message_text("⚔ Бой с ботом!", chat_id, message_id)
    show_duel_interface(chat_id, message_id, duel, user_id)

def show_duel_interface(chat_id, message_id, duel, user_id):
    if duel.check_idle():
        finish_duel(chat_id, message_id, duel, user_id)
        return
    
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
            def_val = player.get_equipment_defense(part) + data["base_defense"]
            markup.add(types.InlineKeyboardButton(f"🛡 {data['name']} (DEF:{def_val})", callback_data=f"ddef_{part}"))
    else:
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(f"🎯 {data['name']}", callback_data=f"dtgt_{part}"))
    
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="dsurr"))
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="drefr"))
    
    safe_edit_or_send(chat_id, message_id, state_text, markup)

temp_target = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("dtgt_"))
def duel_target_handler(call):
    user_id = call.from_user.id
    part = call.data.split("_")[1]
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.answer_callback_query(call.id, "❌ Дуэль не найдена")
        return
    
    temp_target[str(user_id)] = part
    pn = 1 if str(user_id) == duel.p1_id else 2
    skills = duel.get_available_skills(pn)
    
    state_text = duel.get_state_text(user_id) + f"\n\n🎯 Цель: <b>{BODY_PARTS[part]['name']}</b>\n\n<b>Выберите навык (CD указан):</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    cooldowns = duel.p1_cooldowns if pn == 1 else duel.p2_cooldowns
    
    for sid in skills[:12]:
        skill = SKILLS_DB.get(sid, {})
        name = skill.get("name", sid)
        mana = skill.get("mana_cost", 0)
        dmg_mult = skill.get("damage_mult", 1.0)
        cd = skill.get("cooldown", 0)
        cd_text = f" CD:{cd}" if cd > 0 else ""
        current_cd = cooldowns.get(sid, 0)
        
        if current_cd > 0:
            btn_text = f"⏳ {name} (ждём {current_cd}х.)"
        else:
            btn_text = f"{name} x{dmg_mult} [{mana}MP]{cd_text}"
        
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"dskl_{sid}"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="dback"))
    safe_edit_or_send(call.message.chat.id, call.message.message_id, state_text, markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "dback")
def duel_back(call):
    duel = active_duels.get(str(call.from_user.id))
    if duel:
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, call.from_user.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dskl_"))
def duel_skill_handler(call):
    user_id = call.from_user.id
    skill_id = call.data.split("_")[1]
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    target = temp_target.get(str(user_id), "body")
    pn = 1 if str(user_id) == duel.p1_id else 2
    duel.set_attack(pn, skill_id, target)
    
    other_pn = 3 - pn
    if str(duel.p2_id).startswith("bot_") and other_pn == 2:
        time.sleep(0.5)
        if duel.round_type == "p1_defend_p2_attack":
            duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
        elif duel.round_type == "p2_defend_p1_attack":
            duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
            time.sleep(0.3)
            if duel.round_type == "p2_defend_p1_attack":
                skills = duel.get_available_skills(2)
                if skills:
                    duel.set_attack(2, random.choice(skills), random.choice(list(BODY_PARTS.keys())))
    
    skill_name = SKILLS_DB.get(skill_id, {}).get('name', 'Атака')
    bot.answer_callback_query(call.id, f"⚔ {skill_name}!")
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ddef_"))
def duel_defend_handler(call):
    user_id = call.from_user.id
    part = call.data.split("_")[1]
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.answer_callback_query(call.id, "❌ Дуэль не найдена")
        return
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    duel.set_defend(pn, part)
    bot.answer_callback_query(call.id, f"🛡 {BODY_PARTS[part]['name']}")
    
    other_pn = 3 - pn
    if str(duel.p2_id).startswith("bot_") and other_pn == 2:
        if duel.round_type == "p1_defend_p2_attack":
            time.sleep(0.3)
            skills = duel.get_available_skills(2)
            if skills:
                duel.set_attack(2, random.choice(skills), random.choice(list(BODY_PARTS.keys())))
    
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data in ["drefr", "dsurr"])
def duel_misc(call):
    user_id = call.from_user.id
    duel = active_duels.get(str(user_id))
    
    if call.data == "drefr":
        if duel and duel.active:
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
            bot.answer_callback_query(call.id, "✅ Обновлено")
        else:
            bot.delete_message(call.message.chat.id, call.message.message_id)
    elif call.data == "dsurr":
        if duel and duel.active:
            duel.active = False
            duel.winner = 2 if str(user_id) == duel.p1_id else 1
            finish_duel(call.message.chat.id, call.message.message_id, duel, user_id)

def finish_duel(chat_id, message_id, duel, for_user_id=None):
    for uid in [duel.p1_id, duel.p2_id]:
        if uid in active_duels and active_duels[uid].battle_id == duel.battle_id:
            del active_duels[uid]
    
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") or uid.startswith("boss_"):
            if uid in users:
                del users[uid]
    save_json(DATA_FILES['users'], users)
    
    p1_name = get_player_display_name(duel.p1_id)
    p2_name = get_player_display_name(duel.p2_id)
    
    if duel.winner == 0:
        result = f"<b>🤝 НИЧЬЯ!</b>\n{p1_name} vs {p2_name}"
    elif duel.winner == 1:
        result = f"👑 <b>{p1_name}</b> ПОБЕЖДАЕТ!\n💀 {p2_name} проигрывает"
    else:
        result = f"👑 <b>{p2_name}</b> ПОБЕЖДАЕТ!\n💀 {p1_name} проигрывает"
    
    result_text = f"<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>\n\n{result}\n\n💰 Ставка: <b>{duel.bet}💰</b>\n📊 Ходов: <b>{duel.turn}</b>"
    
    if duel.winner != 0:
        wid = duel.p1_id if duel.winner == 1 else duel.p2_id
        lid = duel.p2_id if duel.winner == 1 else duel.p1_id
        
        if not wid.startswith("bot_") and not wid.startswith("boss_"):
            w = Player(wid)
            if duel.bet > 0:
                w.data["money"] += duel.bet * 2
            w.data["wins"] += 1
            w.data["total_duels"] += 1
            w.data["exp"] += duel.turn * 10 + duel.bet // 2
            w.data["total_exp"] += w.data["exp"]
            check_level_up(w)
            w.save()
        
        if not lid.startswith("bot_") and not lid.startswith("boss_"):
            l = Player(lid)
            l.data["losses"] += 1
            l.data["total_duels"] += 1
            l.data["exp"] += duel.turn * 5
            l.data["total_exp"] += l.data["exp"]
            check_level_up(l)
            l.save()
    
    bot.edit_message_text(result_text, chat_id, message_id)
    
    other_id = duel.p2_id if str(for_user_id) == duel.p1_id else duel.p1_id
    if other_id and not other_id.startswith("bot_") and not other_id.startswith("boss_"):
        try:
            bot.send_message(int(other_id), result_text)
        except:
            pass

# ==================== МАГАЗИН ====================
@bot.callback_query_handler(func=lambda call: call.data == "trade_shop")
def shop_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for cat, name in [("weapon", "⚔ Оружие"), ("helmet", "👤 Шлемы"), ("armor", "🦾 Броня"), ("boots", "🦿 Обувь"), ("potion", "🧪 Зелья")]:
        markup.add(types.InlineKeyboardButton(name, callback_data=f"shopcat_{cat}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
    player = Player(call.from_user.id)
    bot.edit_message_text(f"<b>🛒 МАГАЗИН</b>\n💰 {player.data['money']}💰\n{player.get_total_defense_display()}\n\nВыберите категорию:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shopcat_"))
def shop_category(call):
    cat = call.data.split("_")[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    cat_names = {"weapon": "⚔ ОРУЖИЕ", "helmet": "👤 ШЛЕМЫ", "armor": "🦾 БРОНЯ", "boots": "🦿 ОБУВЬ", "potion": "🧪 ЗЕЛЬЯ"}
    cat_items = {k: v for k, v in items.items() if v.get("type") == cat}
    
    text = f"<b>{cat_names.get(cat, cat)}</b>\n💰 {player.data['money']}💰 | {player.get_total_defense_display()}\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for ik, item in sorted(cat_items.items(), key=lambda x: x[1].get("price", 0)):
        if player.data["level"] < item.get("level_req", 1):
            continue
        
        r = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
        
        if item.get("type") == "weapon":
            s = f"Урон: {item['damage'][0]}-{item['damage'][1]}"
        elif item.get("type") == "potion":
            s = f"Лечение: {item.get('heal', 0)}"
        else:
            s = f"DEF:{item.get('defense', 0)}"
            if "speed" in item:
                s += f" SPD:+{item['speed']}"
        
        skill_names = [SKILLS_DB.get(s, {}).get('name', s) for s in item.get('skills', [])]
        
        text += f"{r} <b>{item['name']}</b> | {s}\n💰 {item['price']} | Атак: {len(item.get('skills', []))}\n"
        text += f"📝 {item.get('description', '')}\n"
        if skill_names:
            text += f"⚔ {', '.join(skill_names[:5])}\n"
        text += "\n"
        
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
    
    skill_names = [SKILLS_DB.get(s, {}).get('name', s) for s in item.get('skills', [])]
    skills_text = "\n".join([f"• {s} (CD:{SKILLS_DB.get(s, {}).get('cooldown', 0)})" for s in skill_names]) if skill_names else "Базовые атаки"
    
    bot.answer_callback_query(call.id, f"✅ {item['name']}!")
    bot.send_message(call.message.chat.id, f"✅ Куплено: <b>{item['name']}</b>\n\n⚔ Атаки:\n{skills_text}")
    shop_category(call)

@bot.callback_query_handler(func=lambda call: call.data == "trade_limited")
def limited_shop(call):
    text = "<b>💎 ЛИМИТИРОВАННЫЕ ПРЕДМЕТЫ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for ik, item in limited_items.items():
        pct = "█" * int(item["remaining"] / item["total"] * 10)
        emp = "░" * (10 - len(pct))
        text += f"<b>{item['name']}</b> [{item['rarity']}]\n[{pct}{emp}] {item['remaining']}/{item['total']}\n💰 <b>{item['price']:,}💰</b>\n📝 {item.get('description', '')}\n\n"
        markup.add(types.InlineKeyboardButton(f"Купить: {item['name']} - {item['price']:,}💰", callback_data=f"buyitem_{ik}"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["trade_daily", "trade_market", "trade_sell", "trade_my_lots", "back_to_trade"])
def trade_handlers(call):
    if call.data == "trade_daily":
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
    
    elif call.data == "back_to_trade":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        trade_section(call.message)

# ==================== ГЕРОЙ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["hero_stats", "hero_inventory", "hero_skills", "hero_achievements", "hero_enchantments", "hero_equipped", "hero_history", "hero_heal", "back_to_hero"])
def hero_handlers(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "hero_stats":
        d = player.data
        wr = (d["wins"] / max(1, d["total_duels"]) * 100) if d["total_duels"] > 0 else 0
        text = f"<b>📊 СТАТИСТИКА</b>\n\n{d['first_name']} | {d['title']}\n⭐ Ур.{d['level']}\n💰 {d['money']:,}💰\n🏆 {d['wins']} побед | 📈 {wr:.1f}%\n\n{player.get_total_defense_display()}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_skills":
        skills = player.get_all_skills()
        text = "<b>⚡ ВАШИ НАВЫКИ</b>\n\n"
        for sid in skills:
            skill = SKILLS_DB.get(sid, {})
            cd = skill.get("cooldown", 0)
            cd_text = f" CD:{cd}" if cd > 0 else " [Мгнов.]"
            text += f"• {skill.get('name', sid)} x{skill.get('damage_mult', 1.0)} [{skill.get('mana_cost', 0)}MP]{cd_text}\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_equipped":
        equip = player.data["equipment"]
        text = f"<b>👁 ЭКИПИРОВКА</b>\n\n{player.get_total_defense_display()}\n\n"
        for slot, name in [("weapon", "⚔ Оружие"), ("head", "👤 Голова"), ("body", "🦾 Тело"), ("legs", "🦿 Ноги")]:
            ik = equip.get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                if item:
                    ench = player.data.get("enchantments", {}).get(ik, {})
                    ench_text = f" [✨{ench.get('name', '')}]" if ench else ""
                    text += f"{name}: <b>{item['name']}</b>{ench_text}\n"
                    if item.get("type") == "weapon":
                        text += f"  Урон: {item['damage'][0]}-{item['damage'][1]}\n"
                    else:
                        text += f"  DEF: {item.get('defense', 0)}\n"
            else:
                text += f"{name}: ❌\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔴 Снять всё", callback_data="unequip_all"))
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
        for ik, cnt in list(counts.items())[:20]:
            item = items.get(ik) or limited_items.get(ik)
            if not item:
                continue
            r = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
            text += f"{idx}. {r} {item['name']} x{cnt}\n"
            if item.get("type") in ["weapon", "helmet", "armor", "boots"]:
                markup.add(types.InlineKeyboardButton(f"Экип.: {item['name']}", callback_data=f"equip_{ik}"))
                if item.get("enchantable"):
                    markup.add(types.InlineKeyboardButton(f"Зачар.: {item['name']}", callback_data=f"enchant_{ik}"))
            elif item.get("type") == "potion":
                markup.add(types.InlineKeyboardButton(f"Исп.: {item['name']}", callback_data=f"use_{ik}"))
            idx += 1
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
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
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + potion.get("heal", 40))
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
                text += f"📦 {item['name']}: <b>{e.get('name')}</b>\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data in ["hero_achievements", "hero_history"]:
        text = "<b>🏅 ДОСТИЖЕНИЯ</b>\n\n✅ 🩸 Первая кровь\n🔒 ⚔ Воин\n🔒 🎖 Ветеран" if call.data == "hero_achievements" else "<b>📋 История пуста</b>"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "back_to_hero":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        hero_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
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
        bot.answer_callback_query(call.id, "❌ Нельзя!")
        return
    
    old = player.data["equipment"][slot]
    if old:
        player.data["inventory"].append(old)
    
    player.data["equipment"][slot] = ik
    player.data["inventory"].remove(ik)
    player.save()
    
    skill_names = [SKILLS_DB.get(s, {}).get('name', s) for s in item.get('skills', [])]
    skills_text = "\n".join([f"• {s} (CD:{SKILLS_DB.get(s, {}).get('cooldown', 0)})" for s in skill_names]) if skill_names else "Базовые атаки"
    
    bot.answer_callback_query(call.id, f"✅ {item['name']}!")
    bot.send_message(call.message.chat.id, f"✅ Экипировано: <b>{item['name']}</b>\n\n⚔ Атаки:\n{skills_text}\n\n{player.get_total_defense_display()}")
    hero_handlers(call)

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
    
    player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + item.get("heal", 40))
    player.data["mana"] = min(player.data["max_mana"], player.data["mana"] + item.get("mana_restore", 0))
    player.data["inventory"].remove(ik)
    player.save()
    
    bot.answer_callback_query(call.id, "✅ Использовано!")
    hero_handlers(call)

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
    hero_handlers(call)

# ==================== МИРОВОЙ БОСС ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_boss")
def world_boss_handler(call):
    wb = world_boss_data
    if not wb.get("active"):
        wb = {"active": True, "name": "👹 ДРЕВНИЙ ТИТАН", "hp": 1000000, "max_hp": 1000000, "level": 100, "defense": 200, "damage": 500, "participants": {}, "total_attacks": 0, "spawned_at": datetime.now().isoformat()}
        world_boss_data.update(wb)
        save_json(DATA_FILES['world_boss'], world_boss_data)
    
    hp_pct = wb["hp"] / wb["max_hp"] * 100
    f = int(hp_pct / 10)
    e = 10 - f
    
    user_id = str(call.from_user.id)
    my_dmg = wb.get("participants", {}).get(user_id, 0)
    
    text = f"<b>👹 МИРОВОЙ БОСС</b>\n\n{wb['name']}\n❤ [{'█'*f}{'░'*e}] {wb['hp']:,}/{wb['max_hp']:,}\n💥 Ваш урон: {my_dmg:,}"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("⚔ АТАКОВАТЬ (10 MP)", callback_data="wb_attack"))
    markup.add(types.InlineKeyboardButton("💥 СУПЕР-УДАР (30 MP)", callback_data="wb_super"))
    markup.add(types.InlineKeyboardButton("📊 Топ", callback_data="wb_top"))
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="wb_refresh"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("wb_"))
def world_boss_actions(call):
    action = call.data.split("_")[1]
    user_id = str(call.from_user.id)
    player = Player(user_id)
    wb = world_boss_data
    
    if not wb.get("active"):
        bot.answer_callback_query(call.id, "❌ Босс повержен!")
        return
    
    if action in ["attack", "super"]:
        mp_cost = 30 if action == "super" else 10
        if player.data["mana"] < mp_cost:
            bot.answer_callback_query(call.id, f"❌ Нужно {mp_cost} MP!")
            return
        
        player.data["mana"] -= mp_cost
        base_dmg = random.randint(100, 500) + player.data["level"] * 10
        if action == "super":
            base_dmg *= 3
        
        reduction = wb["defense"] / (wb["defense"] + 500)
        final_dmg = int(base_dmg * (1 - reduction))
        final_dmg = max(10, final_dmg)
        
        wb["hp"] = max(0, wb["hp"] - final_dmg)
        participants = wb.get("participants", {})
        participants[user_id] = participants.get(user_id, 0) + final_dmg
        wb["participants"] = participants
        
        boss_dmg = random.randint(50, wb["damage"])
        player.data["hp"] = max(1, player.data["hp"] - boss_dmg)
        player.save()
        world_boss_data.update(wb)
        save_json(DATA_FILES['world_boss'], world_boss_data)
        
        bot.answer_callback_query(call.id, f"⚔ -{final_dmg:,} HP боссу! -{boss_dmg} HP вам")
        
        if wb["hp"] <= 0:
            sorted_parts = sorted(participants.items(), key=lambda x: x[1], reverse=True)
            announcement = "🎉 <b>БОСС ПОВЕРЖЕН!</b>\n\n"
            if sorted_parts:
                w1 = Player(sorted_parts[0][0])
                w1.data["money"] += 50000
                w1.save()
                announcement += f"👑 Топ-1: {get_player_display_name(sorted_parts[0][0])} — 50,000💰\n"
            world_boss_data.clear()
            world_boss_data["active"] = False
            save_json(DATA_FILES['world_boss'], world_boss_data)
            bot.edit_message_text(announcement, call.message.chat.id, call.message.message_id)
        else:
            world_boss_handler(call)
    
    elif action == "top":
        participants = wb.get("participants", {})
        sorted_parts = sorted(participants.items(), key=lambda x: x[1], reverse=True)[:10]
        text = "<b>📊 ТОП-10</b>\n\n"
        for i, (uid, dmg) in enumerate(sorted_parts):
            text += f"{i+1}. {get_player_display_name(uid)}: {dmg:,}\n"
        bot.send_message(call.message.chat.id, text)
    
    elif action == "refresh":
        world_boss_handler(call)

# ==================== КЛАНЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_clans")
def world_clans(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data.get("clan"):
        clan = clans.get(player.data["clan"], {})
        text = f"<b>🛡 {player.data['clan']}</b>\n👥 {len(clan.get('members', []))} уч.\n💰 Казна: {clan.get('treasury', 0):,}💰"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("👥 Участники", callback_data="clan_members"))
        markup.add(types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave"))
    else:
        text = "<b>🛡 КЛАНЫ</b>\n/createclan [имя] (5000💰)\n/joinclan [имя]"
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
            return
        name = parts[1].strip()
        if name in clans:
            bot.send_message(message.chat.id, "❌ Существует!")
            return
        player.data["money"] -= 5000
        player.data["clan"] = name
        player.data["clan_role"] = "leader"
        player.save()
        clans[name] = {"leader_id": user_id, "leader_name": get_player_display_name(str(user_id)), "members": [get_player_display_name(str(user_id))], "treasury": 0}
        save_json(DATA_FILES['clans'], clans)
        bot.send_message(message.chat.id, f"✅ Клан <b>{name}</b> создан!")
    
    elif cmd == "joinclan":
        if player.data.get("clan"):
            bot.send_message(message.chat.id, "❌ Уже в клане!")
            return
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            return
        name = parts[1].strip()
        if name not in clans:
            bot.send_message(message.chat.id, "❌ Не найден!")
            return
        player.data["clan"] = name
        player.data["clan_role"] = "member"
        player.save()
        if get_player_display_name(str(user_id)) not in clans[name].get("members", []):
            clans[name]["members"].append(get_player_display_name(str(user_id)))
        save_json(DATA_FILES['clans'], clans)
        bot.send_message(message.chat.id, f"✅ Вы в <b>{name}</b>!")

# ==================== ТУРНИРЫ, ИВЕНТЫ, ТОП ====================
@bot.callback_query_handler(func=lambda call: call.data in ["world_tournaments", "world_events", "world_top", "world_help", "back_to_world"])
def world_handlers(call):
    if call.data == "world_tournaments":
        text = "<b>🏟 ТУРНИРЫ</b>\n\nСкоро..."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "world_events":
        current = events_data.get("current", {})
        if not current or datetime.fromisoformat(current.get("expires", "2000-01-01")) < datetime.now():
            new_event = {"name": random.choice(["🌋 Извержение", "❄ Шторм", "⚡ Гроза"]), "ench_reward": random.choice(ENCHANT_EFFECTS), "ench_chance": 25, "expires": (datetime.now() + timedelta(minutes=10)).isoformat()}
            events_data["current"] = new_event
            save_json(DATA_FILES['events'], events_data)
        
        ev = events_data["current"]
        time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
        text = f"<b>🌍 ИВЕНТ</b>\n\n{ev['name']}\n✨ {ev['ench_reward']['name']}\n⏰ {max(0, time_left.seconds//60)} мин."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄", callback_data="world_events"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "world_top":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("⭐ Уровень", callback_data="top_level"))
        markup.add(types.InlineKeyboardButton("⚔ Победы", callback_data="top_wins"))
        markup.add(types.InlineKeyboardButton("💰 Монеты", callback_data="top_money"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
        bot.edit_message_text("<b>📊 ТОП</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "back_to_world":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        world_section(call.message)

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
    else:
        return
    
    text = f"<b>{t}</b>\n\n"
    medals = ["🥇", "🥈", "🥉"] + [f"{i}." for i in range(4, 11)]
    for i, (uid, data) in enumerate(su):
        if cat == "level":
            val = f"Ур.{data.get('level', 1)}"
        elif cat == "wins":
            val = f"{data.get('wins', 0)} побед"
        else:
            val = f"{data.get('money', 0):,}💰"
        text += f"{medals[i]} {get_player_display_name(uid)}: {val}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_top"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

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
        types.InlineKeyboardButton("👹 Спавн босса", callback_data="adm_boss"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("⛔ Бан", callback_data="adm_ban")
    )
    bot.send_message(message.chat.id, "<b>🔧 АДМИН</b>", reply_markup=markup)

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'broadcast', 'userinfo'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd in ["givemoney", "giveitem", "ban", "userinfo"]:
            identifier = parts[1]
            uid = find_user_by_identifier(identifier)
            if not uid:
                bot.send_message(message.chat.id, f"❌ '{identifier}' не найден!")
                return
            
            if cmd == "givemoney":
                amount = int(parts[2])
                p = Player(uid)
                p.data["money"] += amount
                p.save()
                bot.send_message(message.chat.id, f"✅ {amount:,}💰 → {get_player_display_name(uid)}")
            
            elif cmd == "giveitem":
                ik = parts[2]
                p = Player(uid)
                p.data["inventory"].append(ik)
                p.save()
                bot.send_message(message.chat.id, f"✅ Предмет → {get_player_display_name(uid)}")
            
            elif cmd == "ban":
                reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение"
                banned_users[uid] = {"reason": reason, "banned_at": datetime.now().isoformat()}
                save_json(DATA_FILES['bans'], banned_users)
                bot.send_message(message.chat.id, f"⛔ {get_player_display_name(uid)} забанен!")
            
            elif cmd == "userinfo":
                p = Player(uid)
                d = p.data
                text = f"<b>👤 {get_player_display_name(uid)}</b>\nID: {uid}\nУр.: {d['level']}\n💰 {d['money']:,}\nРейтинг: {d['pvp_rating']}"
                bot.send_message(message.chat.id, text)
        
        elif cmd == "broadcast":
            text = message.text.replace('/broadcast', '', 1).strip()
            if text:
                s, f = 0, 0
                for uid in users:
                    if not uid.startswith("bot_") and not uid.startswith("boss_"):
                        try:
                            bot.send_message(int(uid), f"📢 {text}")
                            s += 1
                        except:
                            f += 1
                bot.send_message(message.chat.id, f"✅ {s} | ❌ {f}")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== ПРОДАЖА ====================
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
    market_listings[lid] = {"seller_id": user_id, "seller_name": get_player_display_name(str(user_id)), "item_key": ik, "price": price}
    save_json(DATA_FILES['market'], market_listings)
    
    item = items.get(ik) or limited_items.get(ik)
    bot.send_message(message.chat.id, f"✅ {item.get('name', ik)} за {price}💰!")

# ==================== УРОВНИ ====================
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

# ==================== ЗАПУСК ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v14.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👥 Игроков: {len(users)}")
    print(f"⚔ Предметов: {len(items)}")
    print(f"💎 Лимитированных: {len(limited_items)}")
    print("=" * 60)
    print("✅ По 10+ предметов в категории")
    print("✅ 10 лимитированных предметов")
    print("✅ Кулдауны на ВСЕХ атаках")
    print("✅ Броня уменьшает урон")
    print("✅ Защита = 0 урона при совпадении")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
