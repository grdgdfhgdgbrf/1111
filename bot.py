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

RARITY_NAMES = {
    "common": "Обычный", "uncommon": "Необычный", "rare": "Редкий",
    "epic": "Эпический", "legendary": "Легендарный", "mythic": "Мифический",
    "divine": "Божественный", "apocalyptic": "Апокалиптический"
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
    {"name": "🔥 Огненное", "effect": "burn_damage", "value": 8, "description": "+8 урона огнём каждый ход"},
    {"name": "❄ Ледяное", "effect": "freeze_chance", "value": 25, "description": "+25% шанс заморозки"},
    {"name": "⚡ Грозовое", "effect": "stun_chance", "value": 20, "description": "+20% шанс оглушения"},
    {"name": "💀 Проклятое", "effect": "life_steal", "value": 15, "description": "+15% вампиризма"},
    {"name": "🛡 Укреплённое", "effect": "defense_boost", "value": 15, "description": "+15 к защите"},
    {"name": "💪 Мощное", "effect": "damage_boost", "value": 25, "description": "+25% к урону"},
    {"name": "💨 Скоростное", "effect": "speed_boost", "value": 20, "description": "+20 к скорости"},
    {"name": "❤ Живучее", "effect": "hp_regen", "value": 5, "description": "+5 HP регенерации"},
    {"name": "💎 Магическое", "effect": "mana_steal", "value": 10, "description": "+10 MP при атаке"},
    {"name": "🎯 Меткое", "effect": "crit_boost", "value": 20, "description": "+20% крита"},
    {"name": "🔮 Мистическое", "effect": "random_buff", "value": 10, "description": "Случайный бафф в бою"},
    {"name": "🌿 Ядовитое", "effect": "poison_damage", "value": 6, "description": "+6 урона ядом"}
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
    'achievements': 'achievements.json',
    'notifications': 'notifications.json'
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

# ==================== ПРЕДМЕТЫ (по 5+ в каждой категории) ====================
HELMETS = {
    "leather_cap": {"name": "🎓 Кожаная шапка", "defense": 3, "price": 60, "type": "helmet", "slot": "head", "rarity": "common", "level_req": 1, "enchantable": True, "skills": [], "description": "Простая защита головы"},
    "iron_helmet": {"name": "⛑ Железный шлем", "defense": 8, "price": 250, "type": "helmet", "slot": "head", "rarity": "uncommon", "level_req": 6, "enchantable": True, "skills": ["headbutt"], "description": "Позволяет атаковать головой"},
    "steel_helmet": {"name": "🪖 Стальной шлем", "defense": 12, "price": 600, "type": "helmet", "slot": "head", "rarity": "rare", "level_req": 12, "enchantable": True, "skills": ["headbutt", "iron_skull"], "description": "Усиленная защита + атака"},
    "dragon_helmet": {"name": "🐉 Шлем дракона", "defense": 18, "price": 2000, "type": "helmet", "slot": "head", "rarity": "epic", "level_req": 20, "enchantable": True, "element": "fire", "skills": ["dragon_roar", "fire_breath"], "description": "Дышит огнём! Уникальные атаки"},
    "crown_of_wisdom": {"name": "👑 Корона мудрости", "defense": 12, "mana_bonus": 40, "price": 3500, "type": "helmet", "slot": "head", "rarity": "legendary", "level_req": 28, "enchantable": True, "skills": ["mind_blast", "telepathy", "psychic_wave"], "description": "Психические атаки"}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "defense": 5, "price": 80, "type": "armor", "slot": "body", "rarity": "common", "level_req": 1, "enchantable": True, "skills": ["dodge_roll"], "description": "Лёгкая защита с перекатом"},
    "chainmail": {"name": "⛓ Кольчуга", "defense": 12, "price": 400, "type": "armor", "slot": "body", "rarity": "uncommon", "level_req": 8, "enchantable": True, "skills": ["fortify", "spike_armor"], "description": "Шипы наносят ответный урон"},
    "plate_armor": {"name": "🛡 Латный доспех", "defense": 22, "price": 1500, "type": "armor", "slot": "body", "rarity": "rare", "level_req": 15, "enchantable": True, "skills": ["iron_wall", "bastion", "shield_slam"], "description": "Мощная защита с контратакой"},
    "shadow_armor": {"name": "🌑 Теневая броня", "defense": 28, "price": 3500, "type": "armor", "slot": "body", "rarity": "epic", "level_req": 22, "enchantable": True, "element": "dark", "skills": ["shadow_step", "vanish", "dark_explosion"], "description": "Исчезает в тенях"},
    "phoenix_armor": {"name": "🦅 Броня феникса", "defense": 40, "price": 8000, "type": "armor", "slot": "body", "rarity": "legendary", "level_req": 30, "enchantable": True, "element": "fire", "skills": ["rebirth", "phoenix_flame", "fire_nova"], "description": "Возрождение из пепла"}
}

BOOTS = {
    "leather_boots": {"name": "👢 Кожаные сапоги", "defense": 2, "speed": 8, "price": 100, "type": "boots", "slot": "legs", "rarity": "common", "level_req": 1, "enchantable": True, "skills": ["kick"], "description": "Базовый пинок"},
    "iron_boots": {"name": "🥾 Железные сапоги", "defense": 6, "speed": 4, "price": 300, "type": "boots", "slot": "legs", "rarity": "uncommon", "level_req": 7, "enchantable": True, "skills": ["stomp", "heavy_kick"], "description": "Тяжёлые удары ногами"},
    "wind_boots": {"name": "🌪 Сапоги ветра", "defense": 4, "speed": 18, "price": 900, "type": "boots", "slot": "legs", "rarity": "rare", "level_req": 12, "enchantable": True, "skills": ["tailwind", "gust_kick", "tornado"], "description": "Ураганные атаки ногами"},
    "blink_boots": {"name": "✨ Сапоги телепортации", "defense": 8, "speed": 28, "price": 4000, "type": "boots", "slot": "legs", "rarity": "epic", "level_req": 25, "enchantable": True, "skills": ["blink_kick", "phase_strike", "teleport_combo"], "description": "Телепортация и удары"},
    "hermes_boots": {"name": "👟 Сандалии Гермеса", "defense": 12, "speed": 45, "price": 12000, "type": "boots", "slot": "legs", "rarity": "legendary", "level_req": 35, "enchantable": True, "skills": ["divine_kick", "mercury_strike", "god_speed", "lightning_feet"], "description": "Божественная скорость"}
}

WEAPONS = {
    "rusty_sword": {"name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 1, "skills": ["slash", "quick_strike"], "enchantable": True, "description": "Базовые атаки мечом"},
    "hunters_bow": {"name": "🏹 Лук охотника", "damage": (7, 14), "price": 150, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 3, "element": "nature", "skills": ["power_shot", "multi_shot", "poison_arrow"], "enchantable": True, "description": "Ядовитые стрелы"},
    "flame_blade": {"name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 7, "element": "fire", "skills": ["fire_slash", "inferno_strike", "flame_wave"], "enchantable": True, "description": "Огненные комбо-атаки"},
    "frost_axe": {"name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 10, "element": "ice", "skills": ["frost_strike", "ice_shatter", "blizzard"], "enchantable": True, "description": "Замораживает противников"},
    "storm_staff": {"name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500, "type": "weapon", "slot": "weapon", "rarity": "rare", "level_req": 14, "element": "lightning", "skills": ["lightning_bolt", "thunder_storm", "chain_lightning"], "enchantable": True, "description": "Электрические цепи"},
    "tidal_blade": {"name": "🌊 Приливной клинок", "damage": (20, 32), "price": 2500, "type": "weapon", "slot": "weapon", "rarity": "rare", "level_req": 18, "element": "water", "skills": ["water_slash", "tsunami", "drown"], "enchantable": True, "description": "Волны сокрушают"},
    "shadow_dagger": {"name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "slot": "weapon", "rarity": "epic", "level_req": 22, "element": "dark", "skills": ["shadow_strike", "assassinate", "dark_veil", "soul_drain"], "enchantable": True, "description": "Метка смерти + вампиризм"},
    "divine_spear": {"name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "slot": "weapon", "rarity": "legendary", "level_req": 28, "element": "light", "skills": ["holy_strike", "divine_judgment", "heavenly_light", "purification"], "enchantable": True, "description": "Святые атаки + лечение"},
    "death_scythe": {"name": "💀 Коса смерти", "damage": (40, 65), "price": 12000, "type": "weapon", "slot": "weapon", "rarity": "mythic", "level_req": 35, "element": "dark", "skills": ["reap", "death_sentence", "soul_harvest", "darkness_falls", "reaper_fury"], "enchantable": True, "description": "Ультимативная коса"}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 200, "price": 350, "type": "potion", "rarity": "rare", "level_req": 15},
    "mana_potion": {"name": "💎 Зелье маны", "mana_restore": 60, "price": 60, "type": "potion", "rarity": "common", "level_req": 5},
    "berserk_potion": {"name": "💢 Зелье ярости", "damage_boost": 50, "price": 200, "type": "potion", "rarity": "rare", "level_req": 12, "description": "+50% урона на 3 хода"}
}

LIMITED_ITEMS = {
    "thunderfury": {"name": "⚡ Ярость грома", "damage": (60, 95), "total": 3, "remaining": 3, "price": 50000, "type": "weapon", "slot": "weapon", "rarity": "divine", "element": "lightning", "skills": ["thunder_gods_wrath", "eye_of_the_storm", "lightning_apocalypse", "zeus_anger", "stormcaller"], "enchantable": True, "description": "5 уникальных молниевых атак"},
    "immortal_helmet": {"name": "✨ Шлем бессмертия", "defense": 80, "total": 2, "remaining": 2, "price": 75000, "type": "helmet", "slot": "head", "rarity": "divine", "skills": ["immortality", "divine_shield", "sacred_light"], "enchantable": True, "description": "Неуязвимость на ход"}
}

ALL_ITEMS = {}
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(BOOTS)
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(POTIONS)

# ==================== БАЗА НАВЫКОВ ====================
SKILLS_DB = {
    "quick_strike": {"name": "⚡ Быстрый удар", "damage_mult": 0.8, "mana_cost": 0, "cooldown": 0, "category": "basic", "description": "Мгновенная атака, всегда доступна"},
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 0, "cooldown": 0, "category": "basic", "description": "Базовый разрез, всегда доступен"},
    "kick": {"name": "👢 Пинок", "damage_mult": 0.6, "mana_cost": 0, "cooldown": 0, "category": "basic", "description": "Базовый пинок, всегда доступен"},
    "stomp": {"name": "🦶 Топот", "damage_mult": 0.9, "mana_cost": 0, "cooldown": 0, "category": "basic", "description": "Тяжёлый топот, всегда доступен"},
    
    "power_shot": {"name": "🎯 Мощный выстрел", "damage_mult": 1.8, "mana_cost": 10, "cooldown": 2, "description": "Прицельный выстрел, CD:2"},
    "multi_shot": {"name": "🏹 Залп", "damage_mult": 0.7, "mana_cost": 15, "cooldown": 2, "hits": 3, "description": "Три стрелы, CD:2"},
    "poison_arrow": {"name": "🌿 Ядовитая стрела", "damage_mult": 1.3, "mana_cost": 12, "cooldown": 2, "poison_chance": 60, "description": "Отравляет цель, CD:2"},
    
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.5, "mana_cost": 12, "cooldown": 1, "element": "fire", "burn_chance": 30, "description": "Огненная атака, CD:1"},
    "inferno_strike": {"name": "🌋 Инферно удар", "damage_mult": 2.3, "mana_cost": 28, "cooldown": 3, "element": "fire", "burn_chance": 60, "description": "Мощный огонь, CD:3"},
    "flame_wave": {"name": "🔥 Волна пламени", "damage_mult": 2.8, "mana_cost": 35, "cooldown": 3, "element": "fire", "burn_chance": 40, "description": "Огненная волна, CD:3"},
    
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.4, "mana_cost": 10, "cooldown": 1, "element": "ice", "freeze_chance": 25, "description": "Ледяная атака, CD:1"},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.0, "mana_cost": 22, "cooldown": 2, "element": "ice", "freeze_chance": 50, "description": "Мощный лёд, CD:2"},
    "blizzard": {"name": "🌨 Метель", "damage_mult": 2.4, "mana_cost": 32, "cooldown": 3, "element": "ice", "description": "Ледяной шторм, CD:3"},
    
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.6, "mana_cost": 14, "cooldown": 1, "element": "lightning", "stun_chance": 20, "description": "Электрическая атака, CD:1"},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.3, "mana_cost": 30, "cooldown": 3, "element": "lightning", "stun_chance": 35, "description": "Гроза, CD:3"},
    "chain_lightning": {"name": "⚡ Цепная молния", "damage_mult": 1.8, "mana_cost": 20, "cooldown": 2, "element": "lightning", "description": "Цепная атака, CD:2"},
    
    "water_slash": {"name": "🌊 Водяной разрез", "damage_mult": 1.3, "mana_cost": 10, "cooldown": 1, "element": "water", "description": "Водяная атака, CD:1"},
    "tsunami": {"name": "🌊 Цунами", "damage_mult": 2.1, "mana_cost": 28, "cooldown": 3, "element": "water", "description": "Волна, CD:3"},
    "drown": {"name": "💧 Утопление", "damage_mult": 1.9, "mana_cost": 22, "cooldown": 2, "element": "water", "description": "Захлёбывание, CD:2"},
    
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.6, "mana_cost": 14, "cooldown": 1, "element": "dark", "poison_chance": 25, "description": "Теневая атака, CD:1"},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.5, "mana_cost": 45, "cooldown": 4, "element": "dark", "ignore_defense": 50, "description": "Игнорирует 50% защиты, CD:4"},
    "soul_drain": {"name": "💀 Похищение души", "damage_mult": 2.0, "mana_cost": 25, "cooldown": 3, "element": "dark", "life_steal": 0.4, "description": "Вампиризм 40%, CD:3"},
    "dark_veil": {"name": "🌑 Завеса тьмы", "defense_boost": 30, "mana_cost": 20, "cooldown": 2, "element": "dark", "description": "Теневая защита, CD:2"},
    
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.5, "mana_cost": 12, "cooldown": 1, "element": "light", "description": "Святая атака, CD:1"},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 2.8, "mana_cost": 35, "cooldown": 3, "element": "light", "description": "Святая мощь, CD:3"},
    "heavenly_light": {"name": "🌟 Небесный свет", "hp_restore": 60, "mana_cost": 25, "cooldown": 2, "element": "light", "description": "Лечение +60 HP, CD:2"},
    "purification": {"name": "🌟 Очищение", "hp_restore": 100, "mana_cost": 40, "cooldown": 4, "element": "light", "cure_all": True, "description": "Полное исцеление, CD:4"},
    
    "headbutt": {"name": "💢 Удар головой", "damage_mult": 1.3, "mana_cost": 8, "cooldown": 1, "stun_chance": 15, "description": "Удар шлемом, CD:1"},
    "iron_skull": {"name": "🪖 Железный череп", "damage_mult": 1.8, "mana_cost": 15, "cooldown": 2, "stun_chance": 30, "description": "Мощный удар головой, CD:2"},
    "dragon_roar": {"name": "🐉 Рёв дракона", "damage_mult": 2.2, "mana_cost": 25, "cooldown": 3, "element": "fire", "stun_chance": 30, "description": "Оглушающий рёв, CD:3"},
    "fire_breath": {"name": "🔥 Огненное дыхание", "damage_mult": 2.0, "mana_cost": 20, "cooldown": 2, "element": "fire", "burn_chance": 50, "description": "Дыхание дракона, CD:2"},
    "mind_blast": {"name": "🧠 Ментальный удар", "damage_mult": 2.0, "mana_cost": 22, "cooldown": 2, "stun_chance": 40, "description": "Психическая атака, CD:2"},
    "telepathy": {"name": "👁 Телепатия", "damage_mult": 1.8, "mana_cost": 18, "cooldown": 1, "description": "Чтение мыслей, CD:1"},
    "psychic_wave": {"name": "🌊 Пси-волна", "damage_mult": 3.0, "mana_cost": 35, "cooldown": 4, "description": "Мощная психическая атака, CD:4"},
    
    "dodge_roll": {"name": "🔄 Перекат", "dodge_boost": 40, "mana_cost": 8, "cooldown": 2, "description": "+40% уклонения, CD:2"},
    "fortify": {"name": "🛡 Укрепление", "defense_boost": 30, "mana_cost": 12, "cooldown": 2, "description": "+30 защиты, CD:2"},
    "spike_armor": {"name": "🦔 Шипованная броня", "damage_reflect": 25, "mana_cost": 15, "cooldown": 3, "description": "Отражает 25% урона, CD:3"},
    "iron_wall": {"name": "🧱 Железная стена", "defense_boost": 50, "mana_cost": 20, "cooldown": 3, "description": "+50 защиты, CD:3"},
    "bastion": {"name": "🏰 Бастион", "defense_boost": 40, "hp_restore": 30, "mana_cost": 25, "cooldown": 3, "description": "Защита + лечение, CD:3"},
    "shield_slam": {"name": "💥 Удар щитом", "damage_mult": 1.8, "mana_cost": 15, "cooldown": 2, "stun_chance": 25, "description": "Контратака щитом, CD:2"},
    "shadow_step": {"name": "👣 Шаг в тень", "dodge_boost": 60, "mana_cost": 15, "cooldown": 3, "description": "+60% уклонения, CD:3"},
    "vanish": {"name": "🌫 Исчезновение", "invincible": 1, "mana_cost": 30, "cooldown": 4, "description": "Неуязвимость на ход, CD:4"},
    "dark_explosion": {"name": "💥 Тёмный взрыв", "damage_mult": 3.0, "mana_cost": 35, "cooldown": 4, "element": "dark", "description": "Взрыв тьмы, CD:4"},
    "rebirth": {"name": "🦅 Возрождение", "hp_restore": 150, "mana_cost": 50, "cooldown": 5, "description": "Полное восстановление, CD:5"},
    "phoenix_flame": {"name": "🔥 Пламя феникса", "damage_mult": 3.0, "mana_cost": 35, "cooldown": 4, "element": "fire", "hp_restore": 50, "description": "Атака + лечение, CD:4"},
    "fire_nova": {"name": "💫 Огненная нова", "damage_mult": 3.5, "mana_cost": 45, "cooldown": 5, "element": "fire", "description": "Мощнейший взрыв, CD:5"},
    
    "tailwind": {"name": "💨 Попутный ветер", "speed_boost": 25, "mana_cost": 10, "cooldown": 2, "description": "+25 скорости, CD:2"},
    "gust_kick": {"name": "🌬 Удар ветра", "damage_mult": 1.8, "mana_cost": 15, "cooldown": 2, "description": "Ветряной удар, CD:2"},
    "tornado": {"name": "🌪 Торнадо", "damage_mult": 2.5, "mana_cost": 28, "cooldown": 3, "description": "Вихрь, CD:3"},
    "heavy_kick": {"name": "🦶 Тяжёлый пинок", "damage_mult": 1.5, "mana_cost": 10, "cooldown": 1, "description": "Тяжёлый удар ногой, CD:1"},
    "blink_kick": {"name": "✨ Телепорт-удар", "damage_mult": 2.0, "mana_cost": 20, "cooldown": 3, "description": "Телепортация + удар, CD:3"},
    "phase_strike": {"name": "🌌 Фазовый удар", "damage_mult": 2.5, "mana_cost": 25, "cooldown": 3, "ignore_defense": 30, "description": "Игнорирует 30% защиты, CD:3"},
    "teleport_combo": {"name": "⚡ Телепорт-комбо", "damage_mult": 3.0, "mana_cost": 35, "cooldown": 4, "hits": 3, "description": "Три удара с телепортацией, CD:4"},
    "divine_kick": {"name": "✨ Божественный пинок", "damage_mult": 3.5, "mana_cost": 40, "cooldown": 4, "element": "light", "description": "Божественный удар, CD:4"},
    "mercury_strike": {"name": "💫 Удар Меркурия", "damage_mult": 4.0, "mana_cost": 50, "cooldown": 5, "description": "Ультимативный удар, CD:5"},
    "god_speed": {"name": "⚡ Скорость бога", "speed_boost": 50, "mana_cost": 35, "cooldown": 4, "description": "+50 скорости, CD:4"},
    "lightning_feet": {"name": "👟 Молниеносные ноги", "damage_mult": 3.0, "mana_cost": 30, "cooldown": 3, "element": "lightning", "description": "Молниеносная атака, CD:3"},
    
    "reap": {"name": "💀 Жатва", "damage_mult": 2.5, "mana_cost": 30, "cooldown": 3, "element": "dark", "life_steal": 0.3, "description": "Жатва душ, CD:3"},
    "death_sentence": {"name": "☠ Смертный приговор", "damage_mult": 4.0, "mana_cost": 55, "cooldown": 5, "element": "dark", "description": "Ультимативная атака, CD:5"},
    "soul_harvest": {"name": "👻 Сбор душ", "damage_mult": 3.0, "mana_cost": 40, "cooldown": 4, "element": "dark", "life_steal": 0.5, "description": "50% вампиризма, CD:4"},
    "darkness_falls": {"name": "🌑 Падение тьмы", "damage_mult": 4.5, "mana_cost": 60, "cooldown": 6, "element": "dark", "description": "Абсолютная тьма, CD:6"},
    "reaper_fury": {"name": "💢 Ярость жнеца", "damage_mult": 5.0, "mana_cost": 70, "cooldown": 6, "element": "dark", "life_steal": 0.5, "description": "Ультиматум жнеца, CD:6"},
    
    "immortality": {"name": "✨ Бессмертие", "invincible": 1, "mana_cost": 50, "cooldown": 5, "description": "Неуязвимость на ход, CD:5"},
    "divine_shield": {"name": "🛡 Божественный щит", "defense_boost": 80, "mana_cost": 40, "cooldown": 4, "description": "+80 защиты, CD:4"},
    "sacred_light": {"name": "🌟 Священный свет", "hp_restore": 200, "mana_cost": 60, "cooldown": 5, "description": "Полное исцеление, CD:5"}
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
achievements_data = load_json(DATA_FILES['achievements'], {})
notifications_data = load_json(DATA_FILES['notifications'], {})

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def find_user_by_identifier(identifier):
    """Поиск пользователя по username, ID, или имени"""
    identifier = str(identifier).strip()
    if identifier.startswith('@'):
        identifier = identifier[1:]
    identifier_lower = identifier.lower()
    
    if identifier in users:
        return identifier
    
    for uid, data in users.items():
        if data.get("username", "").lower() == identifier_lower:
            return uid
    
    for uid, data in users.items():
        if data.get("first_name", "").lower() == identifier_lower:
            return uid
    
    for uid, data in users.items():
        if identifier_lower in data.get("username", "").lower():
            return uid
    
    for uid, data in users.items():
        if identifier_lower in data.get("first_name", "").lower():
            return uid
    
    return None

def get_player_display_name(uid):
    """Получить отображаемое имя игрока"""
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
    """Отправить уведомление игроку"""
    try:
        bot.send_message(int(user_id), message)
    except:
        pass

# Удаление старых сообщений
sent_messages = {}

def safe_edit_or_send(chat_id, message_id, text, reply_markup=None):
    """Безопасное редактирование или отправка нового сообщения"""
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
                "items_found": 0,
                "world_boss_damage": 0,
                "clan_donations": 0
            }
            self.save()
            send_notification(user_id, f"🎉 Добро пожаловать в игру, {first_name or 'Игрок'}!\n\n💰 Вы получили 500 стартовых монет!\n⚔ Используйте /start для начала игры.")
    
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
    
    def get_damage_bonus(self):
        bonus = 0
        for ik, ench in self.data.get("enchantments", {}).items():
            if ench.get("effect") == "damage_boost":
                bonus += ench.get("value", 0)
        return bonus / 100.0
    
    def get_total_defense_display(self):
        """Получить отображение всей защиты"""
        parts = {
            "head": self.get_equipment_defense("head") + BODY_PARTS["head"]["base_defense"],
            "body": self.get_equipment_defense("body") + BODY_PARTS["body"]["base_defense"],
            "legs": self.get_equipment_defense("legs") + BODY_PARTS["legs"]["base_defense"]
        }
        return f"🛡 Защита: Г:{parts['head']} Т:{parts['body']} Н:{parts['legs']}"

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
        self.last_action_time = datetime.now()
        self.idle_timeout = 120  # 2 минуты на ход
        
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
        self.p1_ready = False
        self.p2_ready = False
        
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        self.p1_effects = {}
        self.p2_effects = {}
        
        self.p1_buffs = {"defense": 0, "damage": 0, "dodge": 0}
        self.p2_buffs = {"defense": 0, "damage": 0, "dodge": 0}
        
        p1_name = get_player_display_name(self.p1_id)
        p2_name = get_player_display_name(self.p2_id)
        p1_def = self.p1.get_total_defense_display()
        p2_def = self.p2.get_total_defense_display()
        
        self._add_log(1, f"⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>\nПротивник: {p2_name}\n{p2_def}\n💰 Ставка: {bet}💰\n⏰ Тайм-аут хода: 2 мин")
        self._add_log(2, f"⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>\nПротивник: {p1_name}\n{p1_def}\n💰 Ставка: {bet}💰\n⏰ Тайм-аут хода: 2 мин")
        
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
        self.last_action_time = datetime.now()
    
    def check_idle(self):
        """Проверка бездействия"""
        elapsed = (datetime.now() - self.last_action_time).seconds
        if elapsed > self.idle_timeout:
            if self.round_type == "p1_defend_p2_attack":
                # P2 не атаковал вовремя
                self.active = False
                self.winner = 1
                self._add_log(1, "⏰ Противник не сделал ход вовремя! Вы победили!")
                self._add_log(2, "⏰ Вы не сделали ход вовремя! Поражение!")
            else:
                # P1 не атаковал вовремя
                self.active = False
                self.winner = 2
                self._add_log(2, "⏰ Противник не сделал ход вовремя! Вы победили!")
                self._add_log(1, "⏰ Вы не сделали ход вовремя! Поражение!")
            return True
        return False
    
    def set_defend(self, player_num, part):
        if player_num == 1:
            self.p1_defend = part
            self.p1_ready = True
            part_def = self.p1.get_equipment_defense(part) + BODY_PARTS[part]["base_defense"]
            self._add_log(1, f"🛡 Вы защищаете: <b>{BODY_PARTS[part]['name']}</b> (DEF: {part_def})")
        else:
            self.p2_defend = part
            self.p2_ready = True
            part_def = self.p2.get_equipment_defense(part) + BODY_PARTS[part]["base_defense"]
            self._add_log(2, f"🛡 Вы защищаете: <b>{BODY_PARTS[part]['name']}</b> (DEF: {part_def})")
        
        self._check_round()
    
    def set_attack(self, player_num, skill_id, target_part):
        if player_num == 1:
            self.p1_skill = skill_id
            self.p1_target = target_part
            self.p1_ready = True
        else:
            self.p2_skill = skill_id
            self.p2_target = target_part
            self.p2_ready = True
        
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
                self._add_log(1, "❌ Недостаточно маны! Атака не выполнена.")
                return
            self.p1_mp -= mc
        else:
            if self.p2_mp < mc:
                self._add_log(2, "❌ Недостаточно маны! Атака не выполнена.")
                return
            self.p2_mp -= mc
        
        # Расчёт урона
        base_dmg = random.randint(15, 30) + attacker_player.data["level"] * 2
        dmg_bonus = attacker_player.get_damage_bonus()
        base_dmg = int(base_dmg * (1 + dmg_bonus))
        dmg = int(base_dmg * skill.get("damage_mult", 1.0))
        
        body_mult = BODY_PARTS.get(target_part, {}).get("multiplier", 1.0)
        dmg = int(dmg * body_mult)
        
        # Защита цели
        base_def = BODY_PARTS.get(target_part, {}).get("base_defense", 3)
        equip_def = defender_player.get_equipment_defense(target_part)
        total_def = base_def + equip_def
        
        # Уменьшение урона защитой
        reduction = total_def / (total_def + 40)
        blocked = int(dmg * reduction)
        final_dmg = dmg - blocked
        
        blocked_icon = ""
        if defend_part == target_part:
            final_dmg = 0  # Полная защита
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
            self._add_log(attacker, f"⚔ Вы атаковали [{skill_name}] → {BODY_PARTS[target_part]['name']}\n🛡 {defender_name} защитил эту часть!\n💥 Урон: <b>0 HP</b> (заблокировано) ✅")
            self._add_log(defender, f"💢 {attacker_name} атаковал [{skill_name}] → {BODY_PARTS[target_part]['name']}\n🛡 Вы защитили эту часть!\n💥 Урон: <b>0 HP</b> ✅")
        else:
            self._add_log(attacker, f"⚔ Вы атаковали [{skill_name}] → {BODY_PARTS[target_part]['name']}\n💥 Урон: <b>-{final_dmg} HP</b> (броня поглотила {blocked})")
            self._add_log(defender, f"💢 {attacker_name} атаковал [{skill_name}] → {BODY_PARTS[target_part]['name']}\n💥 Урон: <b>-{final_dmg} HP</b> (ваша броня поглотила {blocked})")
        
        # Эффекты
        self._apply_skill_effects(attacker, defender, skill, final_dmg)
        
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
    
    def _apply_skill_effects(self, attacker, defender, skill, dmg):
        attacker_name = get_player_display_name(self.p1_id) if attacker == 1 else get_player_display_name(self.p2_id)
        defender_name = get_player_display_name(self.p2_id) if attacker == 1 else get_player_display_name(self.p1_id)
        
        if "burn_chance" in skill and random.random() * 100 < skill["burn_chance"]:
            self._add_log(defender, f"🔥 <b>ГОРЕНИЕ!</b> Вы будете получать урон 3 хода")
        
        if "freeze_chance" in skill and random.random() * 100 < skill["freeze_chance"]:
            self._add_log(defender, f"❄ <b>ЗАМОРОЗКА!</b> Пропуск следующего хода")
        
        if "stun_chance" in skill and random.random() * 100 < skill["stun_chance"]:
            self._add_log(defender, f"⚡ <b>ОГЛУШЕНИЕ!</b> Пропуск хода")
        
        if "life_steal" in skill and dmg > 0:
            heal = int(dmg * skill["life_steal"])
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self._add_log(attacker, f"💚 <b>ВАМПИРИЗМ +{heal} HP</b>")
        
        if "hp_restore" in skill:
            heal = skill["hp_restore"]
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self._add_log(attacker, f"💚 <b>ЛЕЧЕНИЕ +{heal} HP</b>")
    
    def _switch_round(self):
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        self.p1_ready = False
        self.p2_ready = False
        
        p1_name = get_player_display_name(self.p1_id)
        p2_name = get_player_display_name(self.p2_id)
        p1_def = self.p1.get_total_defense_display()
        p2_def = self.p2.get_total_defense_display()
        
        if self.round_type == "p1_defend_p2_attack":
            self.round_type = "p2_defend_p1_attack"
            self._add_log(2, f"\n🛡 <b>ВЫ ЗАЩИЩАЕТЕСЬ!</b>\n{p1_name} будет атаковать.\n{p2_def}\n\nВыберите часть тела для защиты:")
            self._add_log(1, f"\n⚔ <b>ВЫ АТАКУЕТЕ!</b>\n{p2_name} выбирает защиту...\n{p1_def}\n\nОжидание...")
        else:
            self.round_type = "p1_defend_p2_attack"
            self._add_log(1, f"\n🛡 <b>ВЫ ЗАЩИЩАЕТЕСЬ!</b>\n{p2_name} будет атаковать.\n{p1_def}\n\nВыберите часть тела для защиты:")
            self._add_log(2, f"\n⚔ <b>ВЫ АТАКУЕТЕ!</b>\n{p1_name} выбирает защиту...\n{p2_def}\n\nОжидание...")
        
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
        text += f"Вы: {bar(my_hp, '❤')} | MP: {my_mp}\n"
        text += f"{my_def}\n\n"
        text += f"{opponent_name}: {bar(opp_hp, '❤')}\n"
        text += f"{opp_def}\n"
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
        player = self.p1 if player_num == 1 else self.p2
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        
        available = []
        all_player_skills = player.get_all_skills()
        
        basic = ["quick_strike", "slash", "kick", "stomp"]
        for sid in basic:
            if sid in SKILLS_DB and sid not in cooldowns:
                available.append(sid)
        
        for sid in all_player_skills:
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
        send_notification(user_id, f"🎉 <b>ДОСТИЖЕНИЕ РАЗБЛОКИРОВАНО!</b>\n🩸 Первая кровь — Зарегистрируйтесь и начните игру!")
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v13.0 ⚔️</b>

Привет, <b>{first_name}</b>!

🎯 <b>ПОЛНАЯ ВЕРСИЯ:</b>
• Пошаговые дуэли с защитой и атакой
• Детальные сообщения о ходе боя
• Каждый предмет даёт уникальные атаки
• Кулдауны на все способности
• Кланы с казной и взносами
• Зачарования с эффектами
• Мировой босс 1M HP
• Ивенты с рассылкой

💰 Старт: <b>500 монет</b>
⏰ Тайм-аут хода: 2 минуты
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
        types.InlineKeyboardButton("🎯 Спарринг", callback_data="sparring_duel")
    )
    bot.send_message(message.chat.id, "<b>⚔️ ДУЭЛИ</b>\n\nПошаговая система с уникальными атаками!\nТайм-аут хода: 2 минуты\nВыберите тип дуэли:", reply_markup=markup)

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
        types.InlineKeyboardButton("👹 Мировой босс", callback_data="world_boss"),
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
        markup = types.InlineKeyboardMarkup(row_width=3)
        for bet in [50, 100, 200, 500, 1000]:
            markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"qduel_{bet}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
        player = Player(call.from_user.id)
        bot.edit_message_text(f"<b>⚡ БЫСТРАЯ ДУЭЛЬ (БОТ)</b>\n💰 {player.data['money']}💰\nСтавка:", call.message.chat.id, call.message.message_id, reply_markup=markup)
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
            opp_msg = bot.send_message(int(opponent["user_id"]), "⚔ Соперник найден! Дуэль начинается!")
            show_duel_interface(int(opponent["user_id"]), opp_msg.message_id, duel, opponent["user_id"])
        except:
            pass
    else:
        queue.append({"user_id": user_id, "bet": bet})
        matchmaking_queue[duel_type] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        bot.edit_message_text("🔍 Поиск соперника... Если не найдём — бот!", call.message.chat.id, call.message.message_id)
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
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0, "world_boss_damage": 0, "clan_donations": 0
    }
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
    
    state_text = duel.get_state_text(user_id) + f"\n\n🎯 Цель: <b>{BODY_PARTS[part]['name']}</b>\n\n<b>Выберите навык:</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    cooldowns = duel.p1_cooldowns if pn == 1 else duel.p2_cooldowns
    
    for sid in skills[:12]:
        skill = SKILLS_DB.get(sid, {})
        name = skill.get("name", sid)
        mana = skill.get("mana_cost", 0)
        dmg_mult = skill.get("damage_mult", 1.0)
        cd = skill.get("cooldown", 0)
        cd_text = f" | CD:{cd}" if cd > 0 else " | Мгнов."
        current_cd = cooldowns.get(sid, 0)
        
        if current_cd > 0:
            btn_text = f"⏳ {name} (ждём {current_cd} х.)"
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
                skills = duel.get_available_skills(1)
                if skills:
                    duel.set_attack(1, random.choice(skills), random.choice(list(BODY_PARTS.keys())))
    
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
            bot.answer_callback_query(call.id, "✅")
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
            exp_gain = duel.turn * 10 + duel.bet // 2
            w.data["exp"] += exp_gain
            w.data["total_exp"] += exp_gain
            old_level = w.data["level"]
            check_level_up(w)
            w.save()
            
            if w.data["level"] > old_level:
                result_text += f"\n🎉 <b>{w.data['first_name']}</b> получает уровень <b>{w.data['level']}</b>!"
                send_notification(wid, f"🎉 <b>ПОЗДРАВЛЯЕМ!</b>\nВы достигли уровня <b>{w.data['level']}</b>!\nВаш титул: {w.data['title']}")
            
            # Проверка достижений
            check_achievements(w)
            
            # Шанс зачарования из ивента
            check_event_enchant_reward(w)
        
        if not lid.startswith("bot_") and not lid.startswith("boss_"):
            l = Player(lid)
            l.data["losses"] += 1
            l.data["total_duels"] += 1
            l.data["exp"] += duel.turn * 5
            l.data["total_exp"] += l.data["exp"]
            check_level_up(l)
            l.save()
    
    # Уведомление о результате дуэли
    if duel.winner != 0:
        winner_id = duel.p1_id if duel.winner == 1 else duel.p2_id
        loser_id = duel.p2_id if duel.winner == 1 else duel.p1_id
        if not winner_id.startswith("bot_") and not winner_id.startswith("boss_"):
            send_notification(winner_id, f"🏆 <b>ПОБЕДА В ДУЭЛИ!</b>\n\nПротивник: {get_player_display_name(loser_id)}\n💰 Выигрыш: {duel.bet * 2 if duel.bet > 0 else 0}💰\n📊 +{duel.turn * 10 + duel.bet // 2} EXP")
        if not loser_id.startswith("bot_") and not loser_id.startswith("boss_"):
            send_notification(loser_id, f"💀 <b>ПОРАЖЕНИЕ В ДУЭЛИ</b>\n\nПротивник: {get_player_display_name(winner_id)}\nНе расстраивайтесь, попробуйте снова!")
    
    bot.edit_message_text(result_text, chat_id, message_id)
    
    other_id = duel.p2_id if str(for_user_id) == duel.p1_id else duel.p1_id
    if other_id and not other_id.startswith("bot_") and not other_id.startswith("boss_"):
        try:
            send_notification(other_id, result_text)
        except:
            pass

def check_achievements(player):
    """Проверка и выдача достижений"""
    ach = [
        ("first_blood", "🩸 Первая кровь", "Выиграйте 1 дуэль", player.data["wins"] >= 1),
        ("warrior", "⚔ Воин", "Выиграйте 10 дуэлей", player.data["wins"] >= 10),
        ("veteran", "🎖 Ветеран", "Выиграйте 50 дуэлей", player.data["wins"] >= 50),
        ("rich", "💰 Богач", "Накопите 10,000 монет", player.data["money"] >= 10000),
        ("dmaster", "🏰 Мастер данжей", "Пройти 10 данжей", player.data.get("dungeons_completed", 0) >= 10),
        ("collector", "🎒 Коллекционер", "Найти 20 предметов", player.data.get("items_found", 0) >= 20),
        ("clan_member", "🛡 Клановец", "Вступить в клан", player.data.get("clan") is not None)
    ]
    
    for aid, name, desc, cond in ach:
        if cond and aid not in player.data["achievements"]:
            player.data["achievements"].append(aid)
            player.save()
            send_notification(player.user_id, f"🏅 <b>ДОСТИЖЕНИЕ РАЗБЛОКИРОВАНО!</b>\n\n{name}\n{desc}")

def check_event_enchant_reward(player):
    """Проверка шанса получения зачарования из ивента"""
    current_event = events_data.get("current", {})
    if current_event:
        ench_chance = current_event.get("ench_chance", 10)
        if random.random() * 100 < ench_chance:
            ench = current_event.get("ench_reward", random.choice(ENCHANT_EFFECTS))
            weapon = player.data["equipment"].get("weapon")
            if weapon:
                player.data.setdefault("enchantments", {})[weapon] = {
                    "name": ench["name"],
                    "effect": ench["effect"],
                    "value": ench["value"],
                    "description": ench["description"]
                }
                player.save()
                send_notification(player.user_id, f"🌍 <b>ИВЕНТ!</b>\n\nВы получили зачарование <b>{ench['name']}</b> на ваше оружие!\n📝 {ench['description']}")

# ==================== МАГАЗИН ====================
@bot.callback_query_handler(func=lambda call: call.data == "trade_shop")
def shop_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for cat, name in [("weapon", "⚔ Оружие"), ("helmet", "👤 Шлемы"), ("armor", "🦾 Броня"), ("boots", "🦿 Обувь"), ("potion", "🧪 Зелья")]:
        markup.add(types.InlineKeyboardButton(name, callback_data=f"shopcat_{cat}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
    player = Player(call.from_user.id)
    bot.edit_message_text(f"<b>🛒 МАГАЗИН</b>\n💰 {player.data['money']}💰\n\nКаждый предмет даёт уникальные навыки!\nЗащита уменьшает урон.\nВыберите категорию:", call.message.chat.id, call.message.message_id, reply_markup=markup)

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
        
        skills_count = len(item.get("skills", []))
        skill_names = [SKILLS_DB.get(s, {}).get('name', s) for s in item.get('skills', [])]
        
        text += f"{r} <b>{item['name']}</b> | {s}\n"
        text += f"💰 {item['price']} | Ур.{item.get('level_req', 1)} | Атак: {skills_count}\n"
        text += f"📝 {item.get('description', '')}\n"
        if skill_names:
            text += f"⚔ Навыки: {', '.join(skill_names[:4])}\n"
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
    
    skill_names = [SKILLS_DB.get(s, {}).get('name', s) for s in item.get('skills', [])]
    skills_text = "\n".join([f"• {s} (CD:{SKILLS_DB.get(s, {}).get('cooldown', 0)})" for s in skill_names]) if skill_names else "Базовые атаки"
    
    bot.send_message(call.message.chat.id, f"✅ Куплено: <b>{item['name']}</b>\n\n📝 {item.get('description', '')}\n\n⚔ <b>Новые атаки:</b>\n{skills_text}\n\nЭкипируйте в 👤 Герой → 🎒 Инвентарь")
    shop_category(call)

@bot.callback_query_handler(func=lambda call: call.data in ["trade_limited", "trade_daily", "trade_market", "trade_sell", "trade_my_lots", "back_to_trade"])
def trade_handlers(call):
    if call.data == "trade_limited":
        if not limited_items:
            bot.edit_message_text("💎 Нет лимитированных предметов", call.message.chat.id, call.message.message_id)
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
        text = f"<b>🎁 ЕЖЕДНЕВНЫЙ БОНУС</b>\n💰 +{bonus}\n✨ +{exp}"
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
        bot.delete_message(call.message.chat.id, call.message.message_id)
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
@bot.callback_query_handler(func=lambda call: call.data in ["hero_stats", "hero_inventory", "hero_skills", "hero_achievements", "hero_enchantments", "hero_equipped", "hero_history", "hero_heal", "back_to_hero"])
def hero_handlers(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "hero_stats":
        d = player.data
        wr = (d["wins"] / max(1, d["total_duels"]) * 100) if d["total_duels"] > 0 else 0
        stats = player.get_full_stats() if hasattr(player, 'get_full_stats') else {}
        text = f"<b>📊 СТАТИСТИКА</b>\n\n{d['first_name']} | {d['title']}\n⭐ Ур.{d['level']}\n💰 {d['money']:,}💰\n🏆 {d['wins']} побед | 📈 {wr:.1f}%\n📊 Рейтинг: {d['pvp_rating']}\n\n{player.get_total_defense_display()}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_skills":
        skills = player.get_all_skills()
        text = "<b>⚡ ВАШИ НАВЫКИ</b>\n\n"
        if not skills:
            text += "Нет навыков! Экипируйте предметы.\n\nБазовые всегда доступны:\n• ⚡ Быстрый удар (x0.8) [0MP] Мгнов.\n• 🗡 Разрез (x1.2) [0MP] Мгнов.\n• 👢 Пинок (x0.6) [0MP] Мгнов.\n• 🦶 Топот (x0.9) [0MP] Мгнов."
        else:
            for sid in skills:
                skill = SKILLS_DB.get(sid, {})
                cd = skill.get("cooldown", 0)
                cd_text = f" | CD:{cd}" if cd > 0 else " | Мгнов."
                text += f"• {skill.get('name', sid)} (x{skill.get('damage_mult', 1.0)}) [{skill.get('mana_cost', 0)}MP]{cd_text}\n"
                text += f"  {skill.get('description', '')}\n\n"
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
            ench = player.data.get("enchantments", {}).get(ik, {})
            ench_text = f" ✨{ench.get('name', '')}" if ench else ""
            text += f"{idx}. {r} {item['name']} x{cnt}{ench_text}\n"
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
                text += f"📦 {item['name']}: <b>{e.get('name')}</b>\n{e.get('description', '')}\n\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_achievements":
        ach_list = [
            ("first_blood", "🩸 Первая кровь", "1 победа", player.data["wins"] >= 1),
            ("warrior", "⚔ Воин", "10 побед", player.data["wins"] >= 10),
            ("veteran", "🎖 Ветеран", "50 побед", player.data["wins"] >= 50),
            ("rich", "💰 Богач", "10000 монет", player.data["money"] >= 10000),
            ("dmaster", "🏰 Мастер данжей", "10 данжей", player.data.get("dungeons_completed", 0) >= 10),
            ("collector", "🎒 Коллекционер", "20 предметов", player.data.get("items_found", 0) >= 20),
            ("clan_member", "🛡 Клановец", "Вступить в клан", player.data.get("clan") is not None)
        ]
        text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(player.data['achievements'])}/7)\n\n"
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
    
    elif call.data == "hero_history":
        history = player.data.get("battle_history", [])
        if not history:
            bot.edit_message_text("📋 История пуста", call.message.chat.id, call.message.message_id)
            return
        text = "<b>📋 ПОСЛЕДНИЕ 10 БОЁВ</b>\n\n"
        for b in history[-10:]:
            icon = "🏆" if b.get("result") == "win" else "💀" if b.get("result") == "loss" else "🤝"
            text += f"{icon} vs {b.get('opponent','Нет')} — {b.get('date','')[:10]}\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
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
    player.data.setdefault("enchantments", {})[ik] = {
        "name": ench["name"], "effect": ench["effect"], "value": ench["value"], "description": ench["description"]
    }
    player.save()
    
    bot.answer_callback_query(call.id, f"✨ {ench['name']}!")
    bot.send_message(call.message.chat.id, f"✨ Зачарование: <b>{ench['name']}</b>\n📝 {ench['description']}")
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
        wb = {
            "active": True, "name": "👹 ДРЕВНИЙ ТИТАН",
            "hp": 1000000, "max_hp": 1000000,
            "level": 100, "defense": 200, "damage": 500,
            "participants": {}, "total_attacks": 0,
            "spawned_at": datetime.now().isoformat()
        }
        world_boss_data.update(wb)
        save_json(DATA_FILES['world_boss'], world_boss_data)
    
    hp_pct = wb["hp"] / wb["max_hp"] * 100
    f = int(hp_pct / 10)
    e = 10 - f
    
    user_id = str(call.from_user.id)
    my_dmg = wb.get("participants", {}).get(user_id, 0)
    
    participants = wb.get("participants", {})
    sorted_parts = sorted(participants.items(), key=lambda x: x[1], reverse=True)[:5]
    top_text = ""
    for i, (uid, dmg) in enumerate(sorted_parts):
        medals = ["🥇", "🥈", "🥉", "4.", "5."]
        top_text += f"{medals[i]} {get_player_display_name(uid)}: {dmg:,} урона\n"
    
    text = f"""
<b>👹 МИРОВОЙ БОСС</b>

<b>{wb['name']}</b> (Ур.{wb['level']})
❤ [{'█'*f}{'░'*e}] {wb['hp']:,}/{wb['max_hp']:,} ({hp_pct:.1f}%)

🛡 Защита: {wb['defense']} | ⚔ Урон: {wb['damage']}
👥 Участников: {len(participants)}

<b>🏆 Топ-5:</b>
{top_text if top_text else 'Нет участников'}

💥 Ваш урон: <b>{my_dmg:,}</b>
💰 Награды: Топ-1: 50,000💰 | Топ-3: 10,000💰
"""
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚔ АТАКОВАТЬ (10 MP)", callback_data="wb_attack"),
        types.InlineKeyboardButton("💥 СУПЕР-УДАР (30 MP)", callback_data="wb_super"),
        types.InlineKeyboardButton("📊 Топ", callback_data="wb_top"),
        types.InlineKeyboardButton("🔄 Обновить", callback_data="wb_refresh"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world")
    )
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("wb_"))
def world_boss_actions(call):
    action = call.data.split("_")[1]
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    wb = world_boss_data
    if not wb.get("active"):
        bot.answer_callback_query(call.id, "❌ Босс уже повержен!")
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
        
        dmg_bonus = player.get_damage_bonus()
        base_dmg = int(base_dmg * (1 + dmg_bonus))
        
        reduction = wb["defense"] / (wb["defense"] + 500)
        final_dmg = int(base_dmg * (1 - reduction))
        final_dmg = max(10, final_dmg)
        
        wb["hp"] = max(0, wb["hp"] - final_dmg)
        wb["total_attacks"] += 1
        
        participants = wb.get("participants", {})
        participants[user_id] = participants.get(user_id, 0) + final_dmg
        wb["participants"] = participants
        
        boss_dmg = random.randint(50, wb["damage"])
        player.data["hp"] = max(1, player.data["hp"] - boss_dmg)
        
        player.save()
        world_boss_data.update(wb)
        save_json(DATA_FILES['world_boss'], world_boss_data)
        
        bot.answer_callback_query(call.id, f"⚔ -{final_dmg:,} HP боссу! Босс ответил: -{boss_dmg} HP")
        
        if wb["hp"] <= 0:
            sorted_parts = sorted(participants.items(), key=lambda x: x[1], reverse=True)
            announcement = f"🎉 <b>МИРОВОЙ БОСС ПОВЕРЖЕН!</b>\n\n"
            
            if sorted_parts:
                w1 = Player(sorted_parts[0][0])
                w1.data["money"] += 50000
                w1.save()
                announcement += f"👑 Топ-1: {get_player_display_name(sorted_parts[0][0])} — <b>50,000💰</b>\n"
                send_notification(sorted_parts[0][0], f"🏆 <b>ПОЗДРАВЛЯЕМ!</b>\nВы заняли 1 место в битве с мировым боссом!\n💰 Награда: 50,000💰")
            
            if len(sorted_parts) > 1:
                w2 = Player(sorted_parts[1][0])
                w2.data["money"] += 10000
                w2.save()
                announcement += f"🥈 Топ-2: {get_player_display_name(sorted_parts[1][0])} — <b>10,000💰</b>\n"
            
            if len(sorted_parts) > 2:
                w3 = Player(sorted_parts[2][0])
                w3.data["money"] += 5000
                w3.save()
                announcement += f"🥉 Топ-3: {get_player_display_name(sorted_parts[2][0])} — <b>5,000💰</b>\n"
            
            world_boss_data.clear()
            world_boss_data["active"] = False
            save_json(DATA_FILES['world_boss'], world_boss_data)
            
            for uid in users:
                if not uid.startswith("bot_") and not uid.startswith("boss_"):
                    send_notification(uid, announcement)
            
            bot.edit_message_text(announcement, call.message.chat.id, call.message.message_id)
        else:
            world_boss_handler(call)
    
    elif action == "top":
        participants = wb.get("participants", {})
        sorted_parts = sorted(participants.items(), key=lambda x: x[1], reverse=True)[:20]
        text = "<b>📊 ТОП-20</b>\n\n"
        for i, (uid, dmg) in enumerate(sorted_parts):
            medals = ["🥇", "🥈", "🥉"] + [f"{i+1}." for i in range(3, 20)]
            text += f"{medals[i]} {get_player_display_name(uid)}: <b>{dmg:,}</b>\n"
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
        text = f"<b>🛡 КЛАН: {player.data['clan']}</b>\n\n👥 Участников: {len(clan.get('members', []))}\n💰 Казна: {clan.get('treasury', 0):,}💰\n👑 Лидер: {clan.get('leader_name', 'Нет')}\n\nВаши взносы: {player.data.get('clan_donations', 0):,}💰"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("👥 Участники", callback_data="clan_members"),
            types.InlineKeyboardButton("💰 Пополнить казну", callback_data="clan_donate"),
            types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave")
        )
    else:
        text = "<b>🛡 КЛАНЫ</b>\n\nВы не состоите в клане.\n\nСоздать: /createclan [имя] (5000💰)\nВступить: /joinclan [имя]"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("📋 Список кланов", callback_data="clan_list"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(commands=['createclan', 'joinclan', 'clandonate'])
def clan_commands(message):
    cmd = message.text.split()[0].replace('/', '')
    user_id = message.from_user.id
    player = Player(user_id)
    
    if cmd == "createclan":
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
            bot.send_message(message.chat.id, "❌ Клан существует!")
            return
        player.data["money"] -= 5000
        player.data["clan"] = name
        player.data["clan_role"] = "leader"
        player.save()
        clans[name] = {"leader_id": user_id, "leader_name": get_player_display_name(str(user_id)), "members": [get_player_display_name(str(user_id))], "treasury": 0, "created_at": datetime.now().isoformat()}
        save_json(DATA_FILES['clans'], clans)
        bot.send_message(message.chat.id, f"✅ Клан <b>{name}</b> создан!")
    
    elif cmd == "joinclan":
        if player.data.get("clan"):
            bot.send_message(message.chat.id, "❌ Вы уже в клане!")
            return
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ /joinclan [имя]")
            return
        name = parts[1].strip()
        if name not in clans:
            bot.send_message(message.chat.id, "❌ Клан не найден!")
            return
        player.data["clan"] = name
        player.data["clan_role"] = "member"
        player.save()
        if get_player_display_name(str(user_id)) not in clans[name].get("members", []):
            clans[name]["members"].append(get_player_display_name(str(user_id)))
        save_json(DATA_FILES['clans'], clans)
        bot.send_message(message.chat.id, f"✅ Вы вступили в <b>{name}</b>!")
    
    elif cmd == "clandonate":
        if not player.data.get("clan"):
            bot.send_message(message.chat.id, "❌ Вы не в клане!")
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
        player.data["clan_donations"] = player.data.get("clan_donations", 0) + amount
        player.save()
        cn = player.data["clan"]
        clans[cn]["treasury"] = clans[cn].get("treasury", 0) + amount
        save_json(DATA_FILES['clans'], clans)
        bot.send_message(message.chat.id, f"✅ +{amount:,}💰 в казну клана!")

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
        types.InlineKeyboardButton("✨ Зачаровать всем", callback_data="adm_enchant_all"),
        types.InlineKeyboardButton("👹 Спавн босса", callback_data="adm_spawn_boss"),
        types.InlineKeyboardButton("🌍 Новый ивент", callback_data="adm_event"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("⛔ Бан", callback_data="adm_ban"),
        types.InlineKeyboardButton("✅ Разбан", callback_data="adm_unban"),
        types.InlineKeyboardButton("👁 Инфо", callback_data="adm_info")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>", reply_markup=markup)

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'broadcast', 'userinfo', 'enchantall'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd in ["givemoney", "giveitem", "ban", "unban", "userinfo"]:
            identifier = parts[1]
            uid = find_user_by_identifier(identifier)
            
            if not uid:
                bot.send_message(message.chat.id, f"❌ Пользователь '{identifier}' не найден!")
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
                bot.send_message(message.chat.id, f"✅ Предмет выдан → {get_player_display_name(uid)}")
            
            elif cmd == "ban":
                reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение"
                banned_users[uid] = {"reason": reason, "banned_at": datetime.now().isoformat()}
                save_json(DATA_FILES['bans'], banned_users)
                bot.send_message(message.chat.id, f"⛔ {get_player_display_name(uid)} забанен!")
            
            elif cmd == "unban":
                if uid in banned_users:
                    del banned_users[uid]
                    save_json(DATA_FILES['bans'], banned_users)
                    bot.send_message(message.chat.id, f"✅ {get_player_display_name(uid)} разбанен!")
            
            elif cmd == "userinfo":
                p = Player(uid)
                d = p.data
                text = f"<b>👤 {get_player_display_name(uid)}</b>\nID: {uid}\nУр.: {d['level']}\n💰 {d['money']:,}\nРейтинг: {d['pvp_rating']}\nКлан: {d.get('clan', 'Нет')}\nПредметов: {len(d['inventory'])}"
                bot.send_message(message.chat.id, text)
        
        elif cmd == "broadcast":
            text = message.text.replace('/broadcast', '', 1).strip()
            if text:
                s, f = 0, 0
                for uid in users:
                    if not uid.startswith("bot_") and not uid.startswith("boss_"):
                        try:
                            bot.send_message(int(uid), f"📢 <b>ОБЪЯВЛЕНИЕ:</b>\n\n{text}")
                            s += 1
                        except:
                            f += 1
                bot.send_message(message.chat.id, f"✅ {s} | ❌ {f}")
        
        elif cmd == "enchantall":
            effect = parts[1] if len(parts) > 1 else "damage_boost"
            ench = next((e for e in ENCHANT_EFFECTS if e["effect"] == effect), ENCHANT_EFFECTS[0])
            count = 0
            for uid in users:
                if not uid.startswith("bot_") and not uid.startswith("boss_"):
                    p = Player(uid)
                    weapon = p.data["equipment"].get("weapon")
                    if weapon:
                        p.data.setdefault("enchantments", {})[weapon] = {"name": ench["name"], "effect": ench["effect"], "value": ench["value"], "description": ench["description"]}
                        p.save()
                        count += 1
            bot.send_message(message.chat.id, f"✅ Зачарование '{ench['name']}' наложено на оружие {count} игроков!")
    
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

# ==================== ПОДЗЕМЕЛЬЯ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_dungeons")
def world_dungeons(call):
    text = "<b>🏰 ПОДЗЕМЕЛЬЯ</b>\n\n🐺 Логово волка (Ур. 1+)\n🕷 Паучьи пещеры (Ур. 5+)\n💀 Катакомбы (Ур. 10+)\n🐉 Драконье логово (Ур. 15+)\n👹 Бездна (Ур. 25+)\n\nПо 3 босса в каждом!"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, name in enumerate(["🐺 Логово волка", "🕷 Паучьи пещеры", "💀 Катакомбы", "🐉 Драконье логово", "👹 Бездна"], 1):
        markup.add(types.InlineKeyboardButton(name, callback_data=f"dung_{i}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== ИВЕНТЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_events")
def world_events(call):
    current = events_data.get("current", {})
    if not current or datetime.fromisoformat(current.get("expires", "2000-01-01")) < datetime.now():
        new_event = {
            "name": random.choice(["🌋 Извержение", "❄ Шторм", "⚡ Гроза", "🌑 Затмение", "✨ Звездопад"]),
            "ench_reward": random.choice(ENCHANT_EFFECTS),
            "ench_chance": random.randint(15, 40),
            "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        events_data["current"] = new_event
        save_json(DATA_FILES['events'], events_data)
        
        for uid in users:
            if not uid.startswith("bot_") and not uid.startswith("boss_"):
                send_notification(uid, f"🌍 <b>НОВЫЙ ИВЕНТ!</b>\n\n{new_event['name']}\n🎁 Шанс: {new_event['ench_reward']['name']}\n{new_event['ench_reward']['description']}")
    
    ev = events_data["current"]
    time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
    minutes_left = max(0, time_left.seconds // 60)
    
    text = f"<b>🌍 ИВЕНТ</b>\n\n<b>{ev['name']}</b>\n✨ {ev['ench_reward']['name']}\n⏰ {minutes_left} мин."
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="world_events"))
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
    
    medals = ["🥇", "🥈", "🥉"] + [f"{i}." for i in range(4, 11)]
    text = f"<b>{t}</b>\n\n"
    
    for i, (uid, data) in enumerate(su):
        if cat == "level":
            val = f"Ур.{data.get('level', 1)}"
        elif cat == "wins":
            val = f"{data.get('wins', 0)} побед"
        elif cat == "money":
            val = f"{data.get('money', 0):,}💰"
        else:
            val = f"{data.get('pvp_rating', 1000)}"
        
        text += f"{medals[i]} {get_player_display_name(uid)}: {val}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="world_top"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_world")
def back_to_world(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    world_section(call.message)

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
    print("⚔️ ДУЭЛЬ БОТ v13.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👥 Игроков: {len(users)}")
    print("=" * 60)
    print("✅ Пошаговые дуэли с защитой")
    print("✅ Тайм-аут бездействия 2 мин")
    print("✅ Кнопки назад удаляют старые сообщения")
    print("✅ Кланы с казной и взносами")
    print("✅ Уведомления о достижениях/ивентах")
    print("✅ Защита уменьшает урон (0 при совпадении)")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
