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
TOKEN = '8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE'
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
HELMETS = {
    "leather_cap": {"name": "🎓 Кожаная шапка", "defense": 3, "price": 60, "type": "helmet", "slot": "head", "rarity": "common", "level_req": 1, "enchantable": True, "skills": [], "description": "Простая защита"},
    "iron_helmet": {"name": "⛑ Железный шлем", "defense": 8, "price": 250, "type": "helmet", "slot": "head", "rarity": "uncommon", "level_req": 6, "enchantable": True, "skills": ["headbutt"], "description": "Позволяет атаковать головой"},
    "dragon_helmet": {"name": "🐉 Шлем дракона", "defense": 18, "price": 2000, "type": "helmet", "slot": "head", "rarity": "epic", "level_req": 20, "enchantable": True, "element": "fire", "skills": ["dragon_roar", "fire_breath"], "description": "Дышит огнём! Уникальные атаки"},
    "crown_of_wisdom": {"name": "👑 Корона мудрости", "defense": 12, "mana_bonus": 40, "price": 3500, "type": "helmet", "slot": "head", "rarity": "legendary", "level_req": 28, "enchantable": True, "skills": ["mind_blast", "telepathy", "psychic_wave"], "description": "Психические атаки"}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "defense": 5, "price": 80, "type": "armor", "slot": "body", "rarity": "common", "level_req": 1, "enchantable": True, "skills": ["dodge_roll"], "description": "Позволяет делать перекат"},
    "chainmail": {"name": "⛓ Кольчуга", "defense": 12, "price": 400, "type": "armor", "slot": "body", "rarity": "uncommon", "level_req": 8, "enchantable": True, "skills": ["fortify", "spike_armor"], "description": "Шипы наносят ответный урон"},
    "plate_armor": {"name": "🛡 Латный доспех", "defense": 22, "price": 1500, "type": "armor", "slot": "body", "rarity": "rare", "level_req": 15, "enchantable": True, "skills": ["iron_wall", "bastion", "shield_slam"], "description": "Мощная защита с контратакой"},
    "shadow_armor": {"name": "🌑 Теневая броня", "defense": 28, "price": 3500, "type": "armor", "slot": "body", "rarity": "epic", "level_req": 22, "enchantable": True, "element": "dark", "skills": ["shadow_step", "vanish", "dark_explosion"], "description": "Исчезает в тенях"},
    "phoenix_armor": {"name": "🦅 Броня феникса", "defense": 40, "price": 8000, "type": "armor", "slot": "body", "rarity": "legendary", "level_req": 30, "enchantable": True, "element": "fire", "skills": ["rebirth", "phoenix_flame", "fire_nova"], "description": "Возрождение из пепла"}
}

BOOTS = {
    "leather_boots": {"name": "👢 Кожаные сапоги", "defense": 2, "speed": 8, "price": 100, "type": "boots", "slot": "legs", "rarity": "common", "level_req": 1, "enchantable": True, "skills": ["kick"], "description": "Базовый пинок"},
    "wind_boots": {"name": "🌪 Сапоги ветра", "defense": 4, "speed": 18, "price": 900, "type": "boots", "slot": "legs", "rarity": "rare", "level_req": 12, "enchantable": True, "skills": ["tailwind", "gust_kick", "tornado"], "description": "Ураганные атаки ногами"},
    "blink_boots": {"name": "✨ Сапоги телепортации", "defense": 8, "speed": 28, "price": 4000, "type": "boots", "slot": "legs", "rarity": "epic", "level_req": 25, "enchantable": True, "skills": ["blink_kick", "phase_strike", "teleport_combo"], "description": "Телепортация и удары"},
    "hermes_boots": {"name": "👟 Сандалии Гермеса", "defense": 12, "speed": 45, "price": 12000, "type": "boots", "slot": "legs", "rarity": "legendary", "level_req": 35, "enchantable": True, "skills": ["divine_kick", "mercury_strike", "god_speed", "lightning_feet"], "description": "Божественная скорость"}
}

WEAPONS = {
    "rusty_sword": {"name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 1, "skills": ["slash", "quick_strike"], "enchantable": True, "description": "Базовые атаки мечом"},
    "hunters_bow": {"name": "🏹 Лук охотника", "damage": (7, 14), "price": 150, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 3, "element": "nature", "skills": ["power_shot", "multi_shot", "poison_arrow"], "enchantable": True, "description": "Ядовитые стрелы"},
    "flame_blade": {"name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 7, "element": "fire", "skills": ["fire_slash", "inferno_strike", "flame_wave", "burning_fury"], "enchantable": True, "description": "Огненные комбо-атаки"},
    "frost_axe": {"name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 10, "element": "ice", "skills": ["frost_strike", "ice_shatter", "blizzard", "frozen_prison"], "enchantable": True, "description": "Замораживает противников"},
    "storm_staff": {"name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500, "type": "weapon", "slot": "weapon", "rarity": "rare", "level_req": 14, "element": "lightning", "skills": ["lightning_bolt", "thunder_storm", "chain_lightning", "static_field"], "enchantable": True, "description": "Электрические цепи"},
    "tidal_blade": {"name": "🌊 Приливной клинок", "damage": (20, 32), "price": 2500, "type": "weapon", "slot": "weapon", "rarity": "rare", "level_req": 18, "element": "water", "skills": ["water_slash", "tsunami", "drown", "healing_rain"], "enchantable": True, "description": "Лечит союзников"},
    "shadow_dagger": {"name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "slot": "weapon", "rarity": "epic", "level_req": 22, "element": "dark", "skills": ["shadow_strike", "assassinate", "dark_veil", "soul_drain", "death_mark"], "enchantable": True, "description": "Метка смерти + вампиризм"},
    "divine_spear": {"name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "slot": "weapon", "rarity": "legendary", "level_req": 28, "element": "light", "skills": ["holy_strike", "divine_judgment", "heavenly_light", "purification", "angel_wings"], "enchantable": True, "description": "Крылья ангела на ход"},
    "death_scythe": {"name": "💀 Коса смерти", "damage": (40, 65), "price": 12000, "type": "weapon", "slot": "weapon", "rarity": "mythic", "level_req": 35, "element": "dark", "skills": ["reap", "death_sentence", "soul_harvest", "darkness_falls", "reaper_fury"], "enchantable": True, "description": "Ультимативная коса"}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 200, "price": 350, "type": "potion", "rarity": "rare", "level_req": 15},
    "mana_potion": {"name": "💎 Зелье маны", "mana_restore": 60, "price": 60, "type": "potion", "rarity": "common", "level_req": 5}
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
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 0, "cooldown": 0, "category": "basic", "description": "Базовый разрез"},
    "kick": {"name": "👢 Пинок", "damage_mult": 0.6, "mana_cost": 0, "cooldown": 0, "category": "basic", "description": "Базовый пинок"},
    
    "power_shot": {"name": "🎯 Мощный выстрел", "damage_mult": 1.8, "mana_cost": 10, "cooldown": 2, "description": "Прицельный выстрел"},
    "multi_shot": {"name": "🏹 Залп", "damage_mult": 0.7, "mana_cost": 15, "cooldown": 2, "hits": 3, "description": "Три стрелы"},
    "poison_arrow": {"name": "🌿 Ядовитая стрела", "damage_mult": 1.3, "mana_cost": 12, "cooldown": 2, "poison_chance": 60, "description": "Отравляет цель"},
    
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.5, "mana_cost": 12, "cooldown": 1, "element": "fire", "burn_chance": 30, "description": "Огненная атака"},
    "inferno_strike": {"name": "🌋 Инферно удар", "damage_mult": 2.3, "mana_cost": 28, "cooldown": 3, "element": "fire", "burn_chance": 60, "description": "Мощный огонь"},
    "flame_wave": {"name": "🔥 Волна пламени", "damage_mult": 2.8, "mana_cost": 35, "cooldown": 3, "element": "fire", "burn_chance": 40, "description": "Огненная волна"},
    "burning_fury": {"name": "💢 Ярость пламени", "damage_mult": 3.0, "mana_cost": 40, "cooldown": 4, "element": "fire", "description": "Ультимативный огонь"},
    
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.4, "mana_cost": 10, "cooldown": 1, "element": "ice", "freeze_chance": 25, "description": "Ледяная атака"},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.0, "mana_cost": 22, "cooldown": 2, "element": "ice", "freeze_chance": 50, "description": "Мощный лёд"},
    "blizzard": {"name": "🌨 Метель", "damage_mult": 2.4, "mana_cost": 32, "cooldown": 3, "element": "ice", "description": "Ледяной шторм"},
    "frozen_prison": {"name": "🔒 Ледяная тюрьма", "damage_mult": 2.8, "mana_cost": 38, "cooldown": 4, "element": "ice", "freeze_chance": 80, "description": "Гарантированная заморозка"},
    
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.6, "mana_cost": 14, "cooldown": 1, "element": "lightning", "stun_chance": 20, "description": "Электрическая атака"},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.3, "mana_cost": 30, "cooldown": 3, "element": "lightning", "stun_chance": 35, "description": "Гроза"},
    "chain_lightning": {"name": "⚡ Цепная молния", "damage_mult": 1.8, "mana_cost": 20, "cooldown": 2, "element": "lightning", "description": "Цепная атака"},
    "static_field": {"name": "🔌 Статическое поле", "damage_mult": 2.5, "mana_cost": 35, "cooldown": 3, "element": "lightning", "description": "Электрическое поле"},
    
    "water_slash": {"name": "🌊 Водяной разрез", "damage_mult": 1.3, "mana_cost": 10, "cooldown": 1, "element": "water", "description": "Водяная атака"},
    "tsunami": {"name": "🌊 Цунами", "damage_mult": 2.1, "mana_cost": 28, "cooldown": 3, "element": "water", "description": "Волна"},
    "drown": {"name": "💧 Утопление", "damage_mult": 1.9, "mana_cost": 22, "cooldown": 2, "element": "water", "description": "Захлёбывание"},
    "healing_rain": {"name": "🌧 Исцеляющий дождь", "hp_restore": 80, "mana_cost": 30, "cooldown": 3, "element": "water", "description": "Мощное лечение"},
    
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.6, "mana_cost": 14, "cooldown": 1, "element": "dark", "poison_chance": 25, "description": "Теневая атака"},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.5, "mana_cost": 45, "cooldown": 4, "element": "dark", "ignore_defense": 50, "description": "Игнорирует 50% защиты"},
    "dark_veil": {"name": "🌑 Завеса тьмы", "defense_boost": 30, "mana_cost": 20, "cooldown": 2, "element": "dark", "description": "Теневая защита"},
    "soul_drain": {"name": "💀 Похищение души", "damage_mult": 2.0, "mana_cost": 25, "cooldown": 3, "element": "dark", "life_steal": 0.4, "description": "Вампиризм 40%"},
    "death_mark": {"name": "💀 Метка смерти", "damage_mult": 2.5, "mana_cost": 30, "cooldown": 4, "element": "dark", "description": "Метка: +50% урона"},
    
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.5, "mana_cost": 12, "cooldown": 1, "element": "light", "description": "Святая атака"},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 2.8, "mana_cost": 35, "cooldown": 3, "element": "light", "description": "Святая мощь"},
    "heavenly_light": {"name": "🌟 Небесный свет", "hp_restore": 60, "mana_cost": 25, "cooldown": 2, "element": "light", "description": "Лечение +60 HP"},
    "purification": {"name": "🌟 Очищение", "hp_restore": 100, "mana_cost": 40, "cooldown": 4, "element": "light", "cure_all": True, "description": "Полное исцеление"},
    "angel_wings": {"name": "👼 Крылья ангела", "dodge_boost": 50, "mana_cost": 35, "cooldown": 4, "element": "light", "description": "+50% уклонения"},
    
    "headbutt": {"name": "💢 Удар головой", "damage_mult": 1.3, "mana_cost": 8, "cooldown": 1, "stun_chance": 15, "description": "Удар шлемом"},
    "dragon_roar": {"name": "🐉 Рёв дракона", "damage_mult": 2.2, "mana_cost": 25, "cooldown": 3, "element": "fire", "stun_chance": 30, "description": "Оглушающий рёв"},
    "fire_breath": {"name": "🔥 Огненное дыхание", "damage_mult": 2.0, "mana_cost": 20, "cooldown": 2, "element": "fire", "burn_chance": 50, "description": "Дыхание дракона"},
    "mind_blast": {"name": "🧠 Ментальный удар", "damage_mult": 2.0, "mana_cost": 22, "cooldown": 2, "stun_chance": 40, "description": "Психическая атака"},
    "telepathy": {"name": "👁 Телепатия", "damage_mult": 1.8, "mana_cost": 18, "cooldown": 1, "description": "Чтение мыслей"},
    "psychic_wave": {"name": "🌊 Пси-волна", "damage_mult": 3.0, "mana_cost": 35, "cooldown": 4, "description": "Мощная психическая атака"},
    
    "dodge_roll": {"name": "🔄 Перекат", "dodge_boost": 40, "mana_cost": 8, "cooldown": 2, "description": "+40% уклонения"},
    "fortify": {"name": "🛡 Укрепление", "defense_boost": 30, "mana_cost": 12, "cooldown": 2, "description": "+30 защиты"},
    "spike_armor": {"name": "🦔 Шипованная броня", "damage_reflect": 25, "mana_cost": 15, "cooldown": 3, "description": "Отражает 25% урона"},
    "iron_wall": {"name": "🧱 Железная стена", "defense_boost": 50, "mana_cost": 20, "cooldown": 3, "description": "+50 защиты"},
    "bastion": {"name": "🏰 Бастион", "defense_boost": 40, "hp_restore": 30, "mana_cost": 25, "cooldown": 3, "description": "Защита + лечение"},
    "shield_slam": {"name": "💥 Удар щитом", "damage_mult": 1.8, "mana_cost": 15, "cooldown": 2, "stun_chance": 25, "description": "Контратака щитом"},
    "shadow_step": {"name": "👣 Шаг в тень", "dodge_boost": 60, "mana_cost": 15, "cooldown": 3, "description": "+60% уклонения"},
    "vanish": {"name": "🌫 Исчезновение", "invincible": 1, "mana_cost": 30, "cooldown": 4, "description": "Неуязвимость на ход"},
    "dark_explosion": {"name": "💥 Тёмный взрыв", "damage_mult": 3.0, "mana_cost": 35, "cooldown": 4, "element": "dark", "description": "Взрыв тьмы"},
    "rebirth": {"name": "🦅 Возрождение", "hp_restore": 150, "mana_cost": 50, "cooldown": 5, "description": "Полное восстановление"},
    "phoenix_flame": {"name": "🔥 Пламя феникса", "damage_mult": 3.0, "mana_cost": 35, "cooldown": 4, "element": "fire", "hp_restore": 50, "description": "Атака + лечение"},
    "fire_nova": {"name": "💫 Огненная нова", "damage_mult": 3.5, "mana_cost": 45, "cooldown": 5, "element": "fire", "description": "Мощнейший взрыв"},
    
    "tailwind": {"name": "💨 Попутный ветер", "speed_boost": 25, "mana_cost": 10, "cooldown": 2, "description": "+25 скорости"},
    "gust_kick": {"name": "🌬 Удар ветра", "damage_mult": 1.8, "mana_cost": 15, "cooldown": 2, "description": "Ветряной удар"},
    "tornado": {"name": "🌪 Торнадо", "damage_mult": 2.5, "mana_cost": 28, "cooldown": 3, "description": "Вихрь"},
    "blink_kick": {"name": "✨ Телепорт-удар", "damage_mult": 2.0, "mana_cost": 20, "cooldown": 3, "description": "Телепортация + удар"},
    "phase_strike": {"name": "🌌 Фазовый удар", "damage_mult": 2.5, "mana_cost": 25, "cooldown": 3, "ignore_defense": 30, "description": "Игнорирует 30% защиты"},
    "teleport_combo": {"name": "⚡ Телепорт-комбо", "damage_mult": 3.0, "mana_cost": 35, "cooldown": 4, "hits": 3, "description": "Три удара с телепортацией"},
    "divine_kick": {"name": "✨ Божественный пинок", "damage_mult": 3.5, "mana_cost": 40, "cooldown": 4, "element": "light", "description": "Божественный удар"},
    "mercury_strike": {"name": "💫 Удар Меркурия", "damage_mult": 4.0, "mana_cost": 50, "cooldown": 5, "description": "Ультимативный удар"},
    "god_speed": {"name": "⚡ Скорость бога", "speed_boost": 50, "mana_cost": 35, "cooldown": 4, "description": "+50 скорости"},
    "lightning_feet": {"name": "👟 Молниеносные ноги", "damage_mult": 3.0, "mana_cost": 30, "cooldown": 3, "element": "lightning", "description": "Молниеносная атака"},
    
    "reap": {"name": "💀 Жатва", "damage_mult": 2.5, "mana_cost": 30, "cooldown": 3, "element": "dark", "life_steal": 0.3, "description": "Жатва душ"},
    "death_sentence": {"name": "☠ Смертный приговор", "damage_mult": 4.0, "mana_cost": 55, "cooldown": 5, "element": "dark", "description": "Ультимативная атака"},
    "soul_harvest": {"name": "👻 Сбор душ", "damage_mult": 3.0, "mana_cost": 40, "cooldown": 4, "element": "dark", "life_steal": 0.5, "description": "50% вампиризма"},
    "darkness_falls": {"name": "🌑 Падение тьмы", "damage_mult": 4.5, "mana_cost": 60, "cooldown": 6, "element": "dark", "description": "Абсолютная тьма"},
    "reaper_fury": {"name": "💢 Ярость жнеца", "damage_mult": 5.0, "mana_cost": 70, "cooldown": 6, "element": "dark", "life_steal": 0.5, "description": "Ультиматум жнеца"},
    
    "thunder_gods_wrath": {"name": "⚡ Гнев бога грома", "damage_mult": 4.5, "mana_cost": 70, "cooldown": 5, "element": "lightning", "stun_chance": 50, "description": "Ультимейт молний"},
    "eye_of_the_storm": {"name": "🌀 Глаз бури", "damage_mult": 3.0, "mana_cost": 45, "cooldown": 4, "element": "lightning", "description": "Центр урагана"},
    "lightning_apocalypse": {"name": "⚡ Апокалипсис", "damage_mult": 5.0, "mana_cost": 85, "cooldown": 6, "element": "lightning", "description": "Абсолютная молния"},
    "zeus_anger": {"name": "🔱 Гнев Зевса", "damage_mult": 5.5, "mana_cost": 90, "cooldown": 7, "element": "lightning", "description": "Божественный гнев"},
    "stormcaller": {"name": "🌩 Призыв бури", "damage_mult": 3.5, "mana_cost": 50, "cooldown": 4, "element": "lightning", "description": "Призывает бурю"},
    
    "immortality": {"name": "✨ Бессмертие", "invincible": 1, "mana_cost": 50, "cooldown": 5, "description": "Неуязвимость"},
    "divine_shield": {"name": "🛡 Божественный щит", "defense_boost": 80, "mana_cost": 40, "cooldown": 4, "description": "+80 защиты"},
    "sacred_light": {"name": "🌟 Священный свет", "hp_restore": 200, "mana_cost": 60, "cooldown": 5, "description": "Полное исцеление"}
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

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def find_user_by_identifier(identifier):
    """Поиск пользователя по username, ID, или имени"""
    identifier = str(identifier).strip()
    
    # Убираем @ если есть
    if identifier.startswith('@'):
        identifier = identifier[1:]
    
    identifier_lower = identifier.lower()
    
    # 1. Поиск по точному ID
    if identifier in users:
        return identifier
    
    # 2. Поиск по username (точное совпадение)
    for uid, data in users.items():
        if data.get("username", "").lower() == identifier_lower:
            return uid
    
    # 3. Поиск по имени (точное совпадение)
    for uid, data in users.items():
        if data.get("first_name", "").lower() == identifier_lower:
            return uid
    
    # 4. Поиск по частичному совпадению username
    for uid, data in users.items():
        if identifier_lower in data.get("username", "").lower():
            return uid
    
    # 5. Поиск по частичному совпадению имени
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
                "world_boss_damage": 0
            }
            self.save()
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    def save(self):
        save_json(DATA_FILES['users'], users)
    
    def get_all_skills(self):
        """Получить все навыки от всей экипировки"""
        all_skills = []
        for slot, ik in self.data["equipment"].items():
            if not ik:
                continue
            item = items.get(ik) or limited_items.get(ik)
            if item and "skills" in item:
                all_skills.extend(item["skills"])
        return list(set(all_skills))
    
    def get_equipment_defense(self, part):
        """Защита для части тела"""
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
        """Бонус к урону от зачарований"""
        bonus = 0
        for ik, ench in self.data.get("enchantments", {}).items():
            if ench.get("effect") == "damage_boost":
                bonus += ench.get("value", 0)
        return bonus / 100.0

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
        
        # Раунд: кто защищается, кто атакует
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
        
        # Активные эффекты
        self.p1_effects = {}
        self.p2_effects = {}
        
        # Имена для сообщений
        p1_name = get_player_display_name(self.p1_id)
        p2_name = get_player_display_name(self.p2_id)
        
        self._add_log(1, f"⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>\nПротивник: {p2_name}\nСтавка: {bet}💰")
        self._add_log(2, f"⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>\nПротивник: {p1_name}\nСтавка: {bet}💰")
        
        if self.round_type == "p1_defend_p2_attack":
            self._add_log(1, f"\n🛡 <b>ВЫ ЗАЩИЩАЕТЕСЬ!</b>\n{p2_name} будет атаковать.\nВыберите часть тела для защиты:")
            self._add_log(2, f"\n⚔ <b>ВЫ АТАКУЕТЕ!</b>\n{p1_name} выбирает защиту...\nОжидание...")
        else:
            self._add_log(2, f"\n🛡 <b>ВЫ ЗАЩИЩАЕТЕСЬ!</b>\n{p1_name} будет атаковать.\nВыберите часть тела для защиты:")
            self._add_log(1, f"\n⚔ <b>ВЫ АТАКУЕТЕ!</b>\n{p2_name} выбирает защиту...\nОжидание...")
    
    def _add_log(self, player_num, msg):
        if player_num == 1:
            self.log_p1.append(msg)
        else:
            self.log_p2.append(msg)
    
    def set_defend(self, player_num, part):
        if player_num == 1:
            self.p1_defend = part
            self.p1_ready = True
            part_def = self.p1.get_equipment_defense(part) + BODY_PARTS[part]["base_defense"]
            self._add_log(1, f"🛡 Вы защищаете: <b>{BODY_PARTS[part]['name']}</b> (Защита: {part_def})")
        else:
            self.p2_defend = part
            self.p2_ready = True
            part_def = self.p2.get_equipment_defense(part) + BODY_PARTS[part]["base_defense"]
            self._add_log(2, f"🛡 Вы защищаете: <b>{BODY_PARTS[part]['name']}</b> (Защита: {part_def})")
        
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
                self._execute_attack(2, 1)  # Атакующий=2, Защитник=1
                self._switch_round()
        else:
            if self.p2_defend and self.p1_skill and self.p1_target:
                self._execute_attack(1, 2)  # Атакующий=1, Защитник=2
                self._switch_round()
    
    def _execute_attack(self, attacker, defender):
        skill_id = self.p1_skill if attacker == 1 else self.p2_skill
        target_part = self.p1_target if attacker == 1 else self.p2_target
        defend_part = self.p1_defend if defender == 1 else self.p2_defend
        
        skill = SKILLS_DB.get(skill_id, {"name": "Атака", "damage_mult": 1.0, "mana_cost": 0})
        attacker_player = self.p1 if attacker == 1 else self.p2
        defender_player = self.p1 if defender == 1 else self.p2
        
        # Проверка маны
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
        
        # Базовый урон
        base_dmg = random.randint(15, 30) + attacker_player.data["level"] * 2
        dmg_bonus = attacker_player.get_damage_bonus()
        base_dmg = int(base_dmg * (1 + dmg_bonus))
        dmg = int(base_dmg * skill.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_mult = BODY_PARTS.get(target_part, {}).get("multiplier", 1.0)
        dmg = int(dmg * body_mult)
        
        # Защита цели
        base_def = BODY_PARTS.get(target_part, {}).get("base_defense", 3)
        equip_def = defender_player.get_equipment_defense(target_part)
        total_def = base_def + equip_def
        
        # Уменьшение урона бронёй
        reduction = total_def / (total_def + 40)
        blocked = int(dmg * reduction)
        final_dmg = dmg - blocked
        
        # Доп. снижение если часть защищена
        blocked_icon = ""
        if defend_part == target_part:
            final_dmg = int(final_dmg * 0.5)
            blocked_icon = " 🛡ЗАЩИЩЕНО!"
        
        final_dmg = max(1, final_dmg)
        
        # Нанесение урона
        if defender == 1:
            self.p1_hp = max(0, self.p1_hp - final_dmg)
        else:
            self.p2_hp = max(0, self.p2_hp - final_dmg)
        
        attacker_name = get_player_display_name(self.p1_id) if attacker == 1 else get_player_display_name(self.p2_id)
        defender_name = get_player_display_name(self.p2_id) if attacker == 1 else get_player_display_name(self.p1_id)
        skill_name = skill.get("name", "Атака")
        
        # Сообщение атакующему
        self._add_log(attacker, f"⚔ Вы атаковали [{skill_name}] → {BODY_PARTS[target_part]['name']}\n💥 Урон: <b>-{final_dmg} HP</b> (броня поглотила {blocked}){blocked_icon}")
        
        # Сообщение защищающемуся
        self._add_log(defender, f"💢 {attacker_name} атаковал [{skill_name}] → {BODY_PARTS[target_part]['name']}\n💥 Урон: <b>-{final_dmg} HP</b> (ваша броня поглотила {blocked}){blocked_icon}")
        
        # Эффекты
        self._apply_skill_effects(attacker, defender, skill, final_dmg)
        
        # Кулдауны
        if "cooldown" in skill and skill["cooldown"] > 0:
            cd = skill["cooldown"]
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
        
        # Мана реген
        if attacker == 1:
            self.p1_mp = min(self.p1_max_mp, self.p1_mp + 3)
        else:
            self.p2_mp = min(self.p2_max_mp, self.p2_mp + 3)
        
        # Проверка смерти
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
            self._add_log(attacker, f"🔥 {defender_name} горит!")
        
        if "freeze_chance" in skill and random.random() * 100 < skill["freeze_chance"]:
            self._add_log(defender, f"❄ <b>ЗАМОРОЗКА!</b> Пропуск следующего хода")
            self._add_log(attacker, f"❄ {defender_name} заморожен!")
        
        if "stun_chance" in skill and random.random() * 100 < skill["stun_chance"]:
            self._add_log(defender, f"⚡ <b>ОГЛУШЕНИЕ!</b> Пропуск хода")
            self._add_log(attacker, f"⚡ {defender_name} оглушён!")
        
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
        
        if "invincible" in skill:
            self._add_log(attacker, f"✨ <b>НЕУЯЗВИМОСТЬ</b> на следующий ход!")
    
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
        
        if self.round_type == "p1_defend_p2_attack":
            self.round_type = "p2_defend_p1_attack"
            self._add_log(2, f"\n🛡 <b>ВЫ ЗАЩИЩАЕТЕСЬ!</b>\n{p1_name} будет атаковать.\nВыберите часть тела для защиты:")
            self._add_log(1, f"\n⚔ <b>ВЫ АТАКУЕТЕ!</b>\n{p2_name} выбирает защиту...\nОжидание...")
        else:
            self.round_type = "p1_defend_p2_attack"
            self._add_log(1, f"\n🛡 <b>ВЫ ЗАЩИЩАЕТЕСЬ!</b>\n{p2_name} будет атаковать.\nВыберите часть тела для защиты:")
            self._add_log(2, f"\n⚔ <b>ВЫ АТАКУЕТЕ!</b>\n{p1_name} выбирает защиту...\nОжидание...")
        
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
        
        def bar(val, icon):
            pct = min(100, val)
            f = int(pct / 10)
            e = 10 - f
            color = "🟢" if pct > 50 else "🟡" if pct > 25 else "🔴"
            return f"{icon} {color}[{'█'*f}{'░'*e}] {val}/100"
        
        text = f"<b>⚔ ДУЭЛЬ</b> | Ход <b>{self.turn}</b>\n"
        text += f"Вы: {bar(my_hp, '❤')} | MP: {my_mp}\n"
        text += f"{opponent_name}: {bar(opp_hp, '❤')}\n"
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
        
        # Базовые (всегда доступны если не на CD)
        basic = ["quick_strike", "slash", "kick"]
        for sid in basic:
            if sid in SKILLS_DB and sid not in cooldowns:
                available.append(sid)
        
        # Навыки экипировки
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
        ban_data = banned_users[str(user_id)]
        bot.send_message(message.chat.id, f"⛔ Вы забанены!\nПричина: {ban_data.get('reason', 'Нет')}")
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
<b>⚔️ ДУЭЛЬ БОТ v12.0 ⚔️</b>

Привет, <b>{first_name}</b>!

🎯 <b>НОВОЕ:</b>
• Каждый предмет даёт уникальные атаки!
• Кулдауны на способности (всегда доступна базовая)
• Зачарования с реальными эффектами
• Мировой босс с 1M HP
• Подземелья с 3 боссами
• Ивенты с наградами и рассылкой

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
        types.InlineKeyboardButton("🎯 Спарринг", callback_data="sparring_duel")
    )
    bot.send_message(message.chat.id, "<b>⚔️ ДУЭЛИ</b>\n\nПошаговая система с уникальными атаками!\nВыберите тип дуэли:", reply_markup=markup)

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
        
        bot.edit_message_text("⚔ Соперник найден!", call.message.chat.id, call.message.message_id)
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        
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
        try:
            bot.edit_message_text(f"❌ Нужно {bet}💰!", chat_id, message_id)
        except:
            pass
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
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0, "world_boss_damage": 0
    }
    save_json(DATA_FILES['users'], users)
    
    if bet > 0:
        player.data["money"] -= bet
        player.save()
    
    duel = DuelInstance(user_id, bot_id, duel_type, bet)
    active_duels[str(user_id)] = duel
    
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
            def_val = player.get_equipment_defense(part) + data["base_defense"]
            markup.add(types.InlineKeyboardButton(f"🛡 {data['name']} (DEF:{def_val})", callback_data=f"ddef_{part}"))
    else:
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(f"🎯 {data['name']} (x{data['multiplier']})", callback_data=f"dtgt_{part}"))
    
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="dsurr"))
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="drefr"))
    
    try:
        bot.edit_message_text(state_text[:4000], chat_id, message_id, reply_markup=markup)
    except:
        pass

# Временное хранилище для цели атаки
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
    
    markup.add(types.InlineKeyboardButton("◀ Назад к выбору цели", callback_data="dback"))
    
    try:
        bot.edit_message_text(state_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    except Exception as e:
        print(f"Edit error: {e}")

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
    
    # Бот ходит автоматически
    other_pn = 3 - pn
    if str(duel.p2_id).startswith("bot_") and other_pn == 2:
        time.sleep(0.5)
        # Бот защищается если его очередь
        if duel.round_type == "p1_defend_p2_attack":
            duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
        elif duel.round_type == "p2_defend_p1_attack":
            duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
            time.sleep(0.3)
            if duel.round_type == "p2_defend_p1_attack":
                skills = duel.get_available_skills(1)
                if skills:
                    duel.set_attack(1, random.choice(skills), random.choice(list(BODY_PARTS.keys())))
    
    bot.answer_callback_query(call.id, f"⚔ {SKILLS_DB.get(skill_id, {}).get('name', 'Атака')}!")
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
    
    # Бот атакует
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
            bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
    elif call.data == "dsurr":
        if duel and duel.active:
            duel.active = False
            duel.winner = 2 if str(user_id) == duel.p1_id else 1
            finish_duel(call.message.chat.id, call.message.message_id, duel, user_id)

def finish_duel(chat_id, message_id, duel, for_user_id=None):
    # Очистка
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
    
    # Награды
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
    
    try:
        bot.edit_message_text(result_text, chat_id, message_id)
    except:
        pass
    
    # Отправка второму игроку
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
    bot.edit_message_text(f"<b>🛒 МАГАЗИН</b>\n💰 {player.data['money']}💰\n\nКаждый предмет даёт уникальные навыки!\nВыберите категорию:", call.message.chat.id, call.message.message_id, reply_markup=markup)

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
        elif item.get("type") == "potion":
            s = f"Лечение: {item.get('heal', 0)}"
        else:
            s = f"DEF:{item.get('defense', 0)}"
            if "speed" in item:
                s += f" SPD:+{item['speed']}"
            if "mana_bonus" in item:
                s += f" MP:+{item['mana_bonus']}"
        
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
    
    if len(text) > 4000:
        text = text[:3900] + "\n..."
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

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
    
    # Показываем навыки предмета
    skill_names = [SKILLS_DB.get(s, {}).get('name', s) for s in item.get('skills', [])]
    skills_text = "\n".join([f"• {s}" for s in skill_names]) if skill_names else "Нет специальных атак"
    
    bot.send_message(call.message.chat.id, f"✅ Куплено: <b>{item['name']}</b>\n\n📝 {item.get('description', '')}\n\n⚔ <b>Новые атаки:</b>\n{skills_text}\n\nЭкипируйте предмет в разделе 👤 Герой → 🎒 Инвентарь")
    shop_category(call)

@bot.callback_query_handler(func=lambda call: call.data in ["trade_limited", "trade_daily", "trade_market", "trade_sell", "trade_my_lots", "back_to_trade"])
def trade_handlers(call):
    if call.data == "trade_limited":
        if not limited_items:
            bot.edit_message_text("💎 Нет лимитированных предметов", call.message.chat.id, call.message.message_id)
            return
        text = "<b>💎 ЛИМИТИРОВАННЫЕ ПРЕДМЕТЫ</b>\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for ik, item in limited_items.items():
            if item["remaining"] > 0:
                pct = "█" * int(item["remaining"] / item["total"] * 10)
                emp = "░" * (10 - len(pct))
                text += f"<b>{item['name']}</b>\n[{pct}{emp}] {item['remaining']}/{item['total']}\n💰 <b>{item['price']}💰</b>\n📝 {item.get('description', '')}\n\n"
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
        bot.edit_message_text("📦 /sell [номер] [цена]\nНомер из инвентаря", call.message.chat.id, call.message.message_id)
    
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
        text = f"<b>📊 СТАТИСТИКА</b>\n\n{d['first_name']} | {d['title']}\n⭐ Ур.{d['level']}\n💰 {d['money']:,}💰\n🏆 {d['wins']} побед | 📈 {wr:.1f}%\n📊 Рейтинг: {d['pvp_rating']}\n🎒 Предметов: {len(d['inventory'])}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_skills":
        skills = player.get_all_skills()
        text = "<b>⚡ ВАШИ НАВЫКИ</b>\n\n"
        if not skills:
            text += "Нет навыков! Экипируйте предметы.\n\nБазовые всегда доступны:\n• ⚡ Быстрый удар (x0.8) [0MP]\n• 🗡 Разрез (x1.2) [0MP]\n• 👢 Пинок (x0.6) [0MP]"
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
        text = "<b>👁 ЭКИПИРОВКА</b>\n\n"
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
            markup.add(types.InlineKeyboardButton(f"Продать {item['name']}", callback_data=f"sellitem_{idx-1}"))
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
        ach = [
            ("first_blood", "🩸 Первая кровь", player.data["wins"] >= 1),
            ("warrior", "⚔ Воин", player.data["wins"] >= 10),
            ("veteran", "🎖 Ветеран", player.data["wins"] >= 50),
            ("legend", "👑 Легенда", player.data["wins"] >= 100),
            ("rich", "💰 Богач", player.data["money"] >= 10000),
            ("dmaster", "🏰 Мастер данжей", player.data.get("dungeons_completed", 0) >= 10),
            ("collector", "🎒 Коллекционер", player.data.get("items_found", 0) >= 20)
        ]
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
        bot.answer_callback_query(call.id, "❌ Нельзя экипировать!")
        return
    
    old = player.data["equipment"][slot]
    if old:
        player.data["inventory"].append(old)
    
    player.data["equipment"][slot] = ik
    player.data["inventory"].remove(ik)
    player.save()
    
    skill_names = [SKILLS_DB.get(s, {}).get('name', s) for s in item.get('skills', [])]
    skills_text = "\n".join([f"• {s}" for s in skill_names]) if skill_names else "Базовые атаки"
    
    bot.answer_callback_query(call.id, f"✅ {item['name']} экипирован!")
    bot.send_message(call.message.chat.id, f"✅ Экипировано: <b>{item['name']}</b>\n\n⚔ Доступные атаки:\n{skills_text}")
    hero_handlers(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("enchant_"))
def enchant_handler(call):
    ik = call.data.split("_", 1)[1]
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
    player.data.setdefault("enchantments", {})[ik] = {
        "name": ench["name"],
        "effect": ench["effect"],
        "value": ench["value"],
        "description": ench["description"]
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("sellitem_"))
def sell_item_inv(call):
    idx = int(call.data.split("_")[1])
    user_id = call.from_user.id
    player = Player(user_id)
    
    if idx < 0 or idx >= len(player.data["inventory"]):
        bot.answer_callback_query(call.id, "❌ Неверный индекс!")
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
    bot.answer_callback_query(call.id, "✅ Всё снято!")
    hero_handlers(call)

# ==================== МИРОВОЙ БОСС ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_boss")
def world_boss_handler(call):
    wb = world_boss_data
    
    if not wb.get("active"):
        wb = {
            "active": True,
            "name": "👹 ДРЕВНИЙ ТИТАН",
            "hp": 1000000,
            "max_hp": 1000000,
            "level": 100,
            "defense": 200,
            "damage": 500,
            "participants": {},
            "total_attacks": 0,
            "spawned_at": datetime.now().isoformat()
        }
        world_boss_data.update(wb)
        save_json(DATA_FILES['world_boss'], world_boss_data)
    
    hp_pct = wb["hp"] / wb["max_hp"] * 100
    f = int(hp_pct / 10)
    e = 10 - f
    
    user_id = str(call.from_user.id)
    my_dmg = wb.get("participants", {}).get(user_id, 0)
    
    # Топ участников
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
💰 Награды: Топ-1: 50,000💰 | Топ-3: 10,000💰 | Последний удар: 25,000💰 + предмет
"""
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚔ АТАКОВАТЬ (10 MP)", callback_data="wb_attack"),
        types.InlineKeyboardButton("💥 СУПЕР-УДАР x3 (30 MP)", callback_data="wb_super"),
        types.InlineKeyboardButton("📊 Полный топ", callback_data="wb_top"),
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
        
        # Расчёт урона
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
        
        # Контратака босса
        boss_dmg = random.randint(50, wb["damage"])
        player.data["hp"] = max(1, player.data["hp"] - boss_dmg)
        player.data["mana"] = min(player.data["max_mana"], player.data["mana"] + 5)
        
        player.save()
        world_boss_data.update(wb)
        save_json(DATA_FILES['world_boss'], world_boss_data)
        
        bot.answer_callback_query(call.id, f"⚔ Вы нанесли {final_dmg:,} урона! Босс ответил: -{boss_dmg} HP")
        
        # Проверка смерти босса
        if wb["hp"] <= 0:
            sorted_parts = sorted(participants.items(), key=lambda x: x[1], reverse=True)
            
            announcement = f"🎉 <b>МИРОВОЙ БОСС ПОВЕРЖЕН!</b>\n\n"
            
            if sorted_parts:
                # Топ-1
                w1 = Player(sorted_parts[0][0])
                w1.data["money"] += 50000
                w1.save()
                announcement += f"👑 Топ-1: {get_player_display_name(sorted_parts[0][0])} — <b>50,000💰</b>\n"
            
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
            
            # Сброс босса
            world_boss_data.clear()
            world_boss_data["active"] = False
            save_json(DATA_FILES['world_boss'], world_boss_data)
            
            # Рассылка
            for uid in users:
                if not uid.startswith("bot_") and not uid.startswith("boss_"):
                    try:
                        bot.send_message(int(uid), announcement)
                    except:
                        pass
            
            bot.edit_message_text(announcement, call.message.chat.id, call.message.message_id)
        else:
            world_boss_handler(call)
    
    elif action == "top":
        participants = wb.get("participants", {})
        sorted_parts = sorted(participants.items(), key=lambda x: x[1], reverse=True)[:20]
        
        text = "<b>📊 ТОП-20 УЧАСТНИКОВ</b>\n\n"
        medals = ["🥇", "🥈", "🥉"] + [f"{i}." for i in range(4, 21)]
        
        for i, (uid, dmg) in enumerate(sorted_parts):
            text += f"{medals[i]} {get_player_display_name(uid)}: <b>{dmg:,}</b> урона\n"
        
        if not sorted_parts:
            text += "Нет участников"
        
        bot.send_message(call.message.chat.id, text)
    
    elif action == "refresh":
        world_boss_handler(call)

# ==================== ПОДЗЕМЕЛЬЯ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_dungeons")
def world_dungeons(call):
    text = """
<b>🏰 ПОДЗЕМЕЛЬЯ</b>

🐺 Логово волка (Ур. 1+) — 3 босса
🕷 Паучьи пещеры (Ур. 5+) — 3 босса
💀 Катакомбы (Ур. 10+) — 3 босса
🐉 Драконье логово (Ур. 15+) — 3 босса
👹 Бездна (Ур. 25+) — 3 босса

Кулдаун: 1 час
В каждом данже нужно победить 3 боссов!
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
    
    player.data["last_dungeon"] = datetime.now().isoformat()
    player.save()
    
    start_dungeon_boss(call.message.chat.id, call.message.message_id, user_id, dl, 1)

def start_dungeon_boss(chat_id, message_id, user_id, dungeon_level, boss_num):
    bosses = {
        1: {1: "🐺 Волк-страж", 2: "🐺 Вожак стаи", 3: "🐺 Альфа-волк"},
        2: {1: "🕷 Паук-охотник", 2: "🕷 Королева пауков", 3: "🕷 Матриарх"},
        3: {1: "💀 Скелет-воин", 2: "💀 Некромант", 3: "💀 Лич"},
        4: {1: "🐉 Молодой дракон", 2: "🐉 Древний дракон", 3: "🐉 Владыка драконов"},
        5: {1: "👹 Бес", 2: "👹 Демон", 3: "👹 Архидемон"}
    }
    
    boss_name = bosses.get(dungeon_level, {}).get(boss_num, "Босс")
    level_reqs = [1, 5, 10, 15, 25]
    boss_level = level_reqs[dungeon_level - 1] * 2 + boss_num * 3
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
        "username": "", "first_name": boss_name,
        "money": 0, "level": boss_level, "exp": 0, "total_exp": 0,
        "hp": 100, "max_hp": 100, "mana": 50, "max_mana": 50,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000,
        "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Босс", "titles_collected": ["Босс"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0, "world_boss_damage": 0
    }
    save_json(DATA_FILES['users'], users)
    
    dungeon_progress[str(user_id)] = {
        "dungeon_level": dungeon_level,
        "boss_num": boss_num,
        "reward": random.randint(50, 200) * dungeon_level * boss_num,
        "exp": 30 * dungeon_level * boss_num,
        "boss_name": boss_name
    }
    save_json(DATA_FILES['dungeons'], dungeon_progress)
    
    duel = DuelInstance(user_id, boss_id, "dungeon", 0)
    active_duels[str(user_id)] = duel
    
    bot.edit_message_text(f"⚔ Босс {boss_num}/3: <b>{boss_name}</b>!\nПошаговый бой начинается!", chat_id, message_id)
    show_duel_interface(chat_id, message_id, duel, user_id)

# ==================== ТУРНИРЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_tournaments")
def world_tournaments(call):
    if not tournaments.get("active"):
        tournaments["active"] = {"name": "Еженедельный турнир", "participants": [], "prize_pool": 5000, "status": "registration", "rounds": []}
        save_json(DATA_FILES['tournaments'], tournaments)
    
    tour = tournaments["active"]
    text = f"<b>🏟 ТУРНИР</b>\n\n<b>{tour['name']}</b>\nУчастников: {len(tour.get('participants', []))}\nПриз: <b>{tour.get('prize_pool', 0):,}💰</b>\nСтатус: {tour.get('status', 'registration')}\n\nВзнос: 500💰\nФормат: Single Elimination"
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
    text = "<b>📋 УЧАСТНИКИ ТУРНИРА</b>\n\n"
    for i, uid in enumerate(participants, 1):
        p = Player(uid)
        text += f"{i}. {get_player_display_name(uid)} (Ур.{p.data['level']})\n"
    bot.send_message(call.message.chat.id, text)

# ==================== ИВЕНТЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_events")
def world_events(call):
    current = events_data.get("current", {})
    if not current or datetime.fromisoformat(current.get("expires", "2000-01-01")) < datetime.now():
        new_event = {
            "name": random.choice(["🌋 Извержение вулкана", "❄ Ледяной шторм", "⚡ Грозовой фронт", "🌑 Затмение", "✨ Звёздный дождь", "🔥 Огненный смерч", "💀 Нашествие нежити"]),
            "ench_reward": random.choice(ENCHANT_EFFECTS),
            "ench_chance": random.randint(15, 40),
            "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        events_data["current"] = new_event
        save_json(DATA_FILES['events'], events_data)
        
        # Рассылка всем игрокам
        for uid in users:
            if not uid.startswith("bot_") and not uid.startswith("boss_"):
                try:
                    bot.send_message(int(uid), f"🌍 <b>НОВЫЙ ИВЕНТ!</b>\n\n{new_event['name']}\n🎁 Шанс получить зачарование: <b>{new_event['ench_reward']['name']}</b>\n📝 {new_event['ench_reward']['description']}\n🎲 Шанс выпадения: {new_event['ench_chance']}%\n⏰ Длительность: 10 минут\n\nУчаствуйте в дуэлях для получения!")
                except:
                    pass
    
    ev = events_data["current"]
    time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
    minutes_left = max(0, time_left.seconds // 60)
    
    text = f"""
<b>🌍 ТЕКУЩИЙ ИВЕНТ</b>

<b>{ev['name']}</b>
✨ Награда: <b>{ev['ench_reward']['name']}</b>
📝 {ev['ench_reward']['description']}
🎲 Шанс получения: <b>{ev['ench_chance']}%</b>
⏰ Обновление через: <b>{minutes_left} мин.</b>

Участвуйте в дуэлях для шанса получить зачарование!
"""
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
    bot.edit_message_text("<b>📊 ТОП ИГРОКОВ</b>\nВыберите категорию:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def show_top(call):
    cat = call.data.split("_")[1]
    real_users = {k: v for k, v in users.items() if not k.startswith("bot_") and not k.startswith("boss_")}
    
    if cat == "level":
        su = sorted(real_users.items(), key=lambda x: (x[1].get("level", 1), x[1].get("exp", 0)), reverse=True)[:10]
        t = "⭐ ТОП ПО УРОВНЮ"
    elif cat == "wins":
        su = sorted(real_users.items(), key=lambda x: x[1].get("wins", 0), reverse=True)[:10]
        t = "⚔ ТОП ПО ПОБЕДАМ"
    elif cat == "money":
        su = sorted(real_users.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]
        t = "💰 ТОП ПО МОНЕТАМ"
    elif cat == "rating":
        su = sorted(real_users.items(), key=lambda x: x[1].get("pvp_rating", 1000), reverse=True)[:10]
        t = "🏆 ТОП ПО РЕЙТИНГУ"
    else:
        return
    
    medals = ["🥇", "🥈", "🥉"] + [f"{i}." for i in range(4, 11)]
    text = f"<b>{t}</b>\n\n"
    
    for i, (uid, data) in enumerate(su):
        if cat == "level":
            val = f"Ур.{data.get('level', 1)} ({data.get('exp', 0)} EXP)"
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
    world_section(call.message)

# ==================== КЛАНЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_clans")
def world_clans(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data.get("clan"):
        clan = clans.get(player.data["clan"], {})
        text = f"<b>🛡 КЛАН: {player.data['clan']}</b>\n\n👥 Участников: {len(clan.get('members', []))}\n💰 Казна: {clan.get('treasury', 0):,}💰\n👑 Лидер: {clan.get('leader_name', 'Нет')}"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("👥 Участники", callback_data="clan_members"))
        markup.add(types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave"))
    else:
        text = "<b>🛡 КЛАНЫ</b>\n\nВы не состоите в клане.\n\nСоздать: /createclan [имя] (5000💰)\nВступить: /joinclan [имя]"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("📋 Список кланов", callback_data="clan_list"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(commands=['createclan', 'joinclan'])
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
            bot.send_message(message.chat.id, "❌ Клан уже существует!")
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
        bot.send_message(message.chat.id, f"✅ Вы вступили в клан <b>{name}</b>!")

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
        types.InlineKeyboardButton("✨ Зачаровать всем", callback_data="adm_enchant_all"),
        types.InlineKeyboardButton("👹 Спавн босса", callback_data="adm_spawn_boss"),
        types.InlineKeyboardButton("🌍 Новый ивент", callback_data="adm_event"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("⛔ Бан", callback_data="adm_ban"),
        types.InlineKeyboardButton("✅ Разбан", callback_data="adm_unban"),
        types.InlineKeyboardButton("👁 Инфо игрока", callback_data="adm_info")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>\n\nВсе команды также доступны через:\n/givemoney @username сумма\n/giveitem @username item_key\n/ban @username причина\n/unban @username\n/broadcast текст\n/userinfo @username\n/enchantall эффект", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_handlers(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Нет доступа!")
        return
    
    action = call.data.split("_")[1]
    
    if action == "stats":
        real = {k: v for k, v in users.items() if not k.startswith("bot_") and not k.startswith("boss_")}
        text = f"<b>📊 СТАТИСТИКА БОТА</b>\n\n👥 Игроков: {len(real)}\n💰 Монет: {sum(u.get('money',0) for u in real.values()):,}\n⚔ Дуэлей: {sum(u.get('total_duels',0) for u in real.values())}\n🛡 Кланов: {len(clans)}\n💎 Лимиток: {sum(v.get('remaining',0) for v in limited_items.values())}\n📦 Лотов: {len(market_listings)}\n⛔ Банов: {len(banned_users)}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    
    elif action == "money":
        bot.send_message(call.message.chat.id, "💰 <b>Выдать деньги:</b>\n/givemoney @username сумма\n\nПример: /givemoney @user 1000")
    elif action == "item":
        bot.send_message(call.message.chat.id, "🎁 <b>Выдать предмет:</b>\n/giveitem @username item_key\n\nПример: /giveitem @user flame_blade")
    elif action == "ban":
        bot.send_message(call.message.chat.id, "⛔ <b>Забанить:</b>\n/ban @username причина\n\nПример: /ban @user читерство")
    elif action == "unban":
        bot.send_message(call.message.chat.id, "✅ <b>Разбанить:</b>\n/unban @username")
    elif action == "broadcast":
        bot.send_message(call.message.chat.id, "📢 <b>Рассылка:</b>\n/broadcast текст сообщения")
    elif action == "info":
        bot.send_message(call.message.chat.id, "👁 <b>Информация об игроке:</b>\n/userinfo @username")
    
    elif action == "enchant_all":
        bot.send_message(call.message.chat.id, "✨ <b>Зачаровать всем оружие:</b>\n/enchantall [эффект]\n\nДоступные эффекты:\n• burn_damage — огненный урон\n• freeze_chance — шанс заморозки\n• stun_chance — шанс оглушения\n• life_steal — вампиризм\n• defense_boost — защита\n• damage_boost — урон\n• speed_boost — скорость\n• hp_regen — регенерация HP\n• crit_boost — шанс крита\n\nПример: /enchantall damage_boost")
    
    elif action == "spawn_boss":
        world_boss_data.clear()
        world_boss_data.update({
            "active": True, "name": "👹 ДРЕВНИЙ ТИТАН",
            "hp": 1000000, "max_hp": 1000000,
            "level": 100, "defense": 200, "damage": 500,
            "participants": {}, "total_attacks": 0,
            "spawned_at": datetime.now().isoformat()
        })
        save_json(DATA_FILES['world_boss'], world_boss_data)
        
        # Рассылка всем
        for uid in users:
            if not uid.startswith("bot_") and not uid.startswith("boss_"):
                try:
                    bot.send_message(int(uid), "👹 <b>МИРОВОЙ БОСС ПОЯВИЛСЯ!</b>\n\n⚔ Сразитесь с ним в разделе 🌍 Мир → 👹 Мировой босс!\n❤ 1,000,000 HP\n💰 Награды за топ урон и последний удар!")
                except:
                    pass
        bot.send_message(call.message.chat.id, "✅ Мировой босс заспавнен и объявлен всем игрокам!")
    
    elif action == "event":
        new_event = {
            "name": "🌟 Специальный ивент от администратора",
            "ench_reward": random.choice(ENCHANT_EFFECTS),
            "ench_chance": 50,
            "expires": (datetime.now() + timedelta(minutes=30)).isoformat()
        }
        events_data["current"] = new_event
        save_json(DATA_FILES['events'], events_data)
        
        for uid in users:
            if not uid.startswith("bot_") and not uid.startswith("boss_"):
                try:
                    bot.send_message(int(uid), f"🌟 <b>СПЕЦИАЛЬНЫЙ ИВЕНТ!</b>\n\n{new_event['name']}\n🎁 50% шанс получить: <b>{new_event['ench_reward']['name']}</b>\n📝 {new_event['ench_reward']['description']}\n⏰ Длительность: 30 минут")
                except:
                    pass
        bot.send_message(call.message.chat.id, "✅ Ивент создан и объявлен всем игрокам!")

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'broadcast', 'userinfo', 'enchantall'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Нет доступа!")
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd in ["givemoney", "giveitem", "ban", "unban", "userinfo"]:
            if len(parts) < 2:
                bot.send_message(message.chat.id, f"❌ Укажите пользователя!\nПример: /{cmd} @username")
                return
            
            identifier = parts[1]
            uid = find_user_by_identifier(identifier)
            
            if not uid:
                bot.send_message(message.chat.id, f"❌ Пользователь '{identifier}' не найден!\n\nПроверьте:\n• Правильность username (с @ или без)\n• ID пользователя\n• Имя пользователя\n\nКоманда: /userinfo @username")
                return
            
            if cmd == "givemoney":
                if len(parts) < 3:
                    bot.send_message(message.chat.id, "❌ Укажите сумму!\n/givemoney @username 1000")
                    return
                amount = int(parts[2])
                p = Player(uid)
                p.data["money"] += amount
                p.save()
                bot.send_message(message.chat.id, f"✅ Выдано {amount:,}💰 → {get_player_display_name(uid)}")
            
            elif cmd == "giveitem":
                if len(parts) < 3:
                    bot.send_message(message.chat.id, "❌ Укажите предмет!\n/giveitem @username flame_blade")
                    return
                ik = parts[2]
                p = Player(uid)
                p.data["inventory"].append(ik)
                p.save()
                item = items.get(ik, {})
                bot.send_message(message.chat.id, f"✅ Предмет '{item.get('name', ik)}' выдан → {get_player_display_name(uid)}")
            
            elif cmd == "ban":
                reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение правил"
                banned_users[uid] = {"reason": reason, "banned_at": datetime.now().isoformat()}
                save_json(DATA_FILES['bans'], banned_users)
                bot.send_message(message.chat.id, f"⛔ {get_player_display_name(uid)} забанен!\nПричина: {reason}")
            
            elif cmd == "unban":
                if uid in banned_users:
                    del banned_users[uid]
                    save_json(DATA_FILES['bans'], banned_users)
                    bot.send_message(message.chat.id, f"✅ {get_player_display_name(uid)} разбанен!")
                else:
                    bot.send_message(message.chat.id, "❌ Пользователь не в бане!")
            
            elif cmd == "userinfo":
                p = Player(uid)
                d = p.data
                text = f"""
<b>👤 ИНФОРМАЦИЯ ОБ ИГРОКЕ</b>

Имя: {d['first_name']}
Username: @{d.get('username', 'Нет')}
ID: {uid}
Уровень: {d['level']} (EXP: {d['exp']})
💰 Монет: {d['money']:,}
📊 Рейтинг: {d['pvp_rating']}
🏆 Побед: {d['wins']} | 💀 Поражений: {d['losses']}
🛡 Клан: {d.get('clan', 'Нет')}
🎒 Предметов: {len(d['inventory'])}
✨ Зачарований: {len(d.get('enchantments', {}))}
📅 Регистрация: {d.get('registration_date', '')[:10]}
"""
                bot.send_message(message.chat.id, text)
        
        elif cmd == "broadcast":
            text = message.text.replace('/broadcast', '', 1).strip()
            if not text:
                bot.send_message(message.chat.id, "❌ Введите текст рассылки!\n/broadcast Ваш текст")
                return
            s, f = 0, 0
            for uid in users:
                if not uid.startswith("bot_") and not uid.startswith("boss_"):
                    try:
                        bot.send_message(int(uid), f"📢 <b>ОБЪЯВЛЕНИЕ:</b>\n\n{text}")
                        s += 1
                    except:
                        f += 1
            bot.send_message(message.chat.id, f"✅ Рассылка отправлена!\nУспешно: {s}\nОшибок: {f}")
        
        elif cmd == "enchantall":
            if len(parts) < 2:
                bot.send_message(message.chat.id, "❌ Укажите эффект!\n/enchantall damage_boost\n\nДоступные: burn_damage, freeze_chance, stun_chance, life_steal, defense_boost, damage_boost, speed_boost, hp_regen, crit_boost")
                return
            
            effect = parts[1]
            ench = next((e for e in ENCHANT_EFFECTS if e["effect"] == effect), None)
            
            if not ench:
                bot.send_message(message.chat.id, f"❌ Эффект '{effect}' не найден!\nДоступные: {', '.join([e['effect'] for e in ENCHANT_EFFECTS])}")
                return
            
            count = 0
            for uid in users:
                if not uid.startswith("bot_") and not uid.startswith("boss_"):
                    p = Player(uid)
                    weapon = p.data["equipment"].get("weapon")
                    if weapon:
                        p.data.setdefault("enchantments", {})[weapon] = {
                            "name": ench["name"],
                            "effect": ench["effect"],
                            "value": ench["value"],
                            "description": ench["description"]
                        }
                        p.save()
                        count += 1
                        try:
                            bot.send_message(int(uid), f"✨ Администратор наложил зачарование <b>{ench['name']}</b> на ваше оружие!\n📝 {ench['description']}")
                        except:
                            pass
            
            bot.send_message(message.chat.id, f"✅ Зачарование <b>{ench['name']}</b> наложено на оружие {count} игроков!\n\nЭффект: {ench['description']}")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}\n\nПроверьте правильность команды.")

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
        bot.send_message(message.chat.id, "❌ /sell [номер] [цена]\nНомер предмета из инвентаря (/inventory)")
        return
    
    if idx < 0 or idx >= len(player.data["inventory"]):
        bot.send_message(message.chat.id, "❌ Неверный номер!")
        return
    
    ik = player.data["inventory"].pop(idx)
    player.save()
    
    lid = f"{user_id}_{int(time.time())}"
    market_listings[lid] = {"seller_id": user_id, "seller_name": get_player_display_name(str(user_id)), "item_key": ik, "price": price, "created_at": datetime.now().isoformat()}
    save_json(DATA_FILES['market'], market_listings)
    
    item = items.get(ik) or limited_items.get(ik)
    bot.send_message(message.chat.id, f"✅ {item.get('name', ik)} выставлен на рынок за {price}💰!")

@bot.message_handler(commands=['shop', 'inventory', 'daily', 'stats'])
def quick_commands(message):
    cmd = message.text.split()[0].replace('/', '')
    user_id = message.from_user.id
    
    if cmd == "shop":
        shop_menu(message)
    elif cmd == "inventory":
        hero_handlers(types.CallbackQuery(id="0", from_user=message.from_user, message=message, data="hero_inventory", chat_instance="0"))
    elif cmd == "daily":
        trade_handlers(types.CallbackQuery(id="0", from_user=message.from_user, message=message, data="trade_daily", chat_instance="0"))
    elif cmd == "stats":
        hero_handlers(types.CallbackQuery(id="0", from_user=message.from_user, message=message, data="hero_stats", chat_instance="0"))

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
        
        titles = {5: "Боец", 10: "Воитель", 15: "Рыцарь", 20: "Ветеран", 25: "Мастер", 30: "Грандмастер", 40: "Герой", 50: "Легенда", 60: "Мифический воин", 75: "Полубог", 100: "Божество"}
        
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
    print("⚔️ ДУЭЛЬ БОТ v12.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 Запуск: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print(f"⚔ Предметов: {len(items)}")
    print(f"💎 Лимитированных: {len(limited_items)}")
    print(f"👹 Мировой босс: {'Активен' if world_boss_data.get('active') else 'Нет'}")
    print("=" * 60)
    print("✅ Пошаговые дуэли с защитой и атакой")
    print("✅ Детальные сообщения о ходе боя")
    print("✅ Уникальные атаки у каждого предмета")
    print("✅ Кулдауны на способности")
    print("✅ Зачарования с реальными эффектами")
    print("✅ Мировой босс 1,000,000 HP")
    print("✅ Ивенты с автоматической рассылкой")
    print("✅ Админ-панель с поиском по username")
    print("✅ Подземелья с 3 боссами")
    print("✅ Турниры с призовым фондом")
    print("=" * 60)
    print("ВСЕ СИСТЕМЫ АКТИВНЫ!")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
