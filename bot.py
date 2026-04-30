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
    "earth": {"name": "🏔 Земля", "strong_against": "lightning", "weak_against": "nature"},
    "dark": {"name": "🌑 Тьма", "strong_against": "light", "weak_against": "light"},
    "light": {"name": "✨ Свет", "strong_against": "dark", "weak_against": "dark"}
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
    'dungeons': 'dungeons.json',
    'events': 'events.json',
    'bans': 'bans.json',
    'quests': 'quests.json'
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

# ==================== ИНИЦИАЛИЗАЦИЯ ПРЕДМЕТОВ ====================
WEAPONS = {
    "rusty_sword": {
        "name": "🗡 Ржавый меч", "damage": (3, 7), "price": 50, "type": "weapon",
        "rarity": "common", "level_req": 1, "element": None,
        "skills": ["slash", "quick_strike"],
        "description": "Старый ржавый меч"
    },
    "hunters_bow": {
        "name": "🏹 Лук охотника", "damage": (5, 10), "price": 150, "type": "weapon",
        "rarity": "common", "level_req": 3, "element": "nature",
        "skills": ["power_shot", "multi_shot"],
        "description": "Надёжный лук для охоты"
    },
    "flame_blade": {
        "name": "🔥 Пламенный клинок", "damage": (8, 15), "price": 400, "type": "weapon",
        "rarity": "uncommon", "level_req": 7, "element": "fire",
        "skills": ["fire_slash", "inferno_strike", "flame_wave"],
        "description": "Клинок, объятый пламенем"
    },
    "frost_axe": {
        "name": "❄ Ледяной топор", "damage": (10, 18), "price": 700, "type": "weapon",
        "rarity": "uncommon", "level_req": 10, "element": "ice",
        "skills": ["frost_strike", "ice_shatter", "blizzard"],
        "description": "Замораживает противников"
    },
    "storm_staff": {
        "name": "⚡ Посох бурь", "damage": (12, 22), "price": 1200, "type": "weapon",
        "rarity": "rare", "level_req": 14, "element": "lightning",
        "skills": ["lightning_bolt", "thunder_storm", "chain_lightning", "static_field"],
        "description": "Призывает молнии"
    },
    "tidal_blade": {
        "name": "🌊 Приливной клинок", "damage": (15, 25), "price": 2000, "type": "weapon",
        "rarity": "rare", "level_req": 18, "element": "water",
        "skills": ["water_slash", "tsunami", "drown", "healing_wave"],
        "description": "Волны сокрушают врагов"
    },
    "shadow_dagger": {
        "name": "🌑 Теневой кинжал", "damage": (18, 30), "price": 3500, "type": "weapon",
        "rarity": "epic", "level_req": 22, "element": "dark",
        "skills": ["shadow_strike", "assassinate", "dark_veil", "soul_drain"],
        "description": "Атакует из тени"
    },
    "divine_spear": {
        "name": "✨ Божественное копьё", "damage": (22, 35), "price": 6000, "type": "weapon",
        "rarity": "legendary", "level_req": 28, "element": "light",
        "skills": ["holy_strike", "divine_judgment", "heavenly_light", "purification"],
        "description": "Оружие небесных воинов"
    },
    "death_scythe": {
        "name": "💀 Коса смерти", "damage": (25, 45), "price": 10000, "type": "weapon",
        "rarity": "mythic", "level_req": 35, "element": "dark",
        "skills": ["reap", "death_sentence", "soul_harvest", "darkness_falls"],
        "description": "Забирает души врагов"
    }
}

SHIELDS = {
    "wooden_shield": {
        "name": "🛡 Деревянный щит", "defense": 5, "block_chance": 10,
        "price": 100, "type": "shield", "rarity": "common", "level_req": 1,
        "skills": ["block", "shield_bash"],
        "description": "Простой деревянный щит"
    },
    "iron_shield": {
        "name": "🛡 Железный щит", "defense": 10, "block_chance": 15,
        "price": 350, "type": "shield", "rarity": "uncommon", "level_req": 6,
        "skills": ["shield_wall", "counter_attack"],
        "description": "Прочный железный щит"
    },
    "mirror_shield": {
        "name": "🪞 Зеркальный щит", "defense": 15, "block_chance": 20,
        "price": 900, "type": "shield", "rarity": "rare", "level_req": 12,
        "skills": ["reflect", "magic_barrier"],
        "description": "Отражает магию"
    },
    "dragon_scale_shield": {
        "name": "🐉 Щит драконьей чешуи", "defense": 22, "block_chance": 25,
        "price": 2500, "type": "shield", "rarity": "epic", "level_req": 20,
        "skills": ["dragon_guard", "fire_shield", "scales_of_protection"],
        "description": "Чешуя древнего дракона"
    },
    "aegis_divine": {
        "name": "💫 Божественная эгида", "defense": 35, "block_chance": 35,
        "price": 8000, "type": "shield", "rarity": "legendary", "level_req": 30,
        "skills": ["divine_protection", "holy_bulwark", "blessing_of_protection"],
        "description": "Щит самой Афины"
    }
}

ARMORS = {
    "leather_vest": {
        "name": "🧥 Кожаный жилет", "defense": 3, "hp_bonus": 15,
        "price": 80, "type": "armor", "rarity": "common", "level_req": 1,
        "skills": ["dodge"],
        "description": "Лёгкая защита"
    },
    "chainmail": {
        "name": "⛓ Кольчуга", "defense": 8, "hp_bonus": 35,
        "price": 400, "type": "armor", "rarity": "uncommon", "level_req": 8,
        "skills": ["fortify", "endure"],
        "description": "Надёжная кольчуга"
    },
    "plate_armor": {
        "name": "🛡 Латный доспех", "defense": 15, "hp_bonus": 60,
        "price": 1200, "type": "armor", "rarity": "rare", "level_req": 15,
        "skills": ["iron_will", "bastion", "reinforce"],
        "description": "Тяжёлые латы"
    },
    "shadow_armor": {
        "name": "🌑 Теневая броня", "defense": 20, "hp_bonus": 80,
        "price": 3000, "type": "armor", "rarity": "epic", "level_req": 22,
        "skills": ["shadow_step", "vanish", "dark_mantle"],
        "description": "Скрывает в тенях"
    },
    "phoenix_armor": {
        "name": "🦅 Броня феникса", "defense": 30, "hp_bonus": 150,
        "price": 7000, "type": "armor", "rarity": "legendary", "level_req": 30,
        "skills": ["rebirth", "phoenix_flame", "fire_immunity"],
        "description": "Возрождает из пепла"
    }
}

POTIONS = {
    "health_potion": {
        "name": "🧪 Зелье здоровья", "heal": 30, "price": 40,
        "type": "potion", "rarity": "common", "level_req": 1,
        "description": "Восстанавливает 30 HP"
    },
    "big_health_potion": {
        "name": "🧪 Большое зелье", "heal": 75, "price": 120,
        "type": "potion", "rarity": "uncommon", "level_req": 8,
        "description": "Восстанавливает 75 HP"
    },
    "elixir_of_life": {
        "name": "💊 Эликсир жизни", "heal": 150, "price": 350,
        "type": "potion", "rarity": "rare", "level_req": 15,
        "description": "Полное восстановление"
    },
    "mana_potion": {
        "name": "💎 Зелье маны", "heal": 0, "mana_restore": 50, "price": 60,
        "type": "potion", "rarity": "common", "level_req": 5,
        "description": "Восстанавливает 50 маны"
    },
    "berserk_potion": {
        "name": "💢 Зелье ярости", "heal": 0, "price": 200,
        "type": "potion", "rarity": "rare", "level_req": 12,
        "description": "Удваивает урон на 3 хода"
    },
    "invisibility_potion": {
        "name": "👻 Зелье невидимости", "heal": 0, "price": 500,
        "type": "potion", "rarity": "epic", "level_req": 20,
        "description": "Уклонение от атак"
    }
}

ACCESSORIES = {
    "strength_ring": {
        "name": "💍 Кольцо силы", "price": 600, "type": "accessory",
        "rarity": "uncommon", "level_req": 5,
        "stats": {"strength": 3},
        "description": "+3 к силе"
    },
    "crit_amulet": {
        "name": "📿 Амулет крита", "price": 1500, "type": "accessory",
        "rarity": "rare", "level_req": 15,
        "stats": {"crit_chance": 10},
        "description": "+10% к шансу крита"
    },
    "lucky_charm": {
        "name": "🍀 Талисман удачи", "price": 2500, "type": "accessory",
        "rarity": "epic", "level_req": 20,
        "stats": {"luck": 10, "dodge_chance": 5},
        "description": "Увеличивает удачу"
    },
    "berserker_ring": {
        "name": "💢 Кольцо берсерка", "price": 4000, "type": "accessory",
        "rarity": "epic", "level_req": 25,
        "stats": {"strength": 8, "vitality": 5},
        "description": "Ярость в бою"
    }
}

BOOTS = {
    "leather_boots": {
        "name": "👢 Кожаные сапоги", "speed": 5, "price": 150,
        "type": "boots", "rarity": "common", "level_req": 1,
        "description": "+5 к скорости"
    },
    "wind_boots": {
        "name": "🌪 Сапоги ветра", "speed": 12, "price": 800,
        "type": "boots", "rarity": "rare", "level_req": 12,
        "description": "+12 к скорости"
    },
    "blink_boots": {
        "name": "✨ Сапоги телепортации", "speed": 20, "price": 3500,
        "type": "boots", "rarity": "epic", "level_req": 25,
        "description": "Мгновенное перемещение"
    }
}

LIMITED_ITEMS = {
    "thunderfury": {
        "name": "⚡ Ярость грома", "damage": (50, 80), "total": 3,
        "remaining": 3, "price": 50000, "type": "weapon",
        "rarity": "divine", "element": "lightning",
        "skills": ["thunder_gods_wrath", "eye_of_the_storm", "lightning_apocalypse"],
        "description": "Меч бога грома"
    },
    "apocalypse": {
        "name": "🌋 Апокалипсис", "damage": (70, 120), "total": 1,
        "remaining": 1, "price": 100000, "type": "weapon",
        "rarity": "apocalyptic", "element": "dark",
        "skills": ["world_ender", "obliterate", "void_annihilation"],
        "description": "Конец всего сущего"
    },
    "immortal_shield": {
        "name": "✨ Щит бессмертия", "defense": 100, "total": 2,
        "remaining": 2, "price": 75000, "type": "shield",
        "rarity": "divine",
        "skills": ["immortality", "absolute_defense", "divine_intervention"],
        "description": "Делает владельца неуязвимым"
    },
    "cloak_of_infinity": {
        "name": "🌀 Плащ бесконечности", "defense": 60, "hp_bonus": 500,
        "total": 4, "remaining": 4, "price": 60000, "type": "armor",
        "rarity": "divine",
        "skills": ["infinity", "cosmic_armor", "reality_warp"],
        "description": "Бесконечная защита космоса"
    }
}

# Объединение всех предметов
ALL_ITEMS = {}
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(SHIELDS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(POTIONS)
ALL_ITEMS.update(ACCESSORIES)
ALL_ITEMS.update(BOOTS)

# Загрузка данных
items = load_json(DATA_FILES['items'], ALL_ITEMS)
limited_items = load_json(DATA_FILES['limited'], LIMITED_ITEMS)
users = load_json(DATA_FILES['users'], {})
active_duels = load_json(DATA_FILES['duels'], {})
clans = load_json(DATA_FILES['clans'], {})
tournaments = load_json(DATA_FILES['tournaments'], {})
market_listings = load_json(DATA_FILES['market'], {})
dungeons = load_json(DATA_FILES['dungeons'], {})
events = load_json(DATA_FILES['events'], {})
banned_users = load_json(DATA_FILES['bans'], {})
quests_data = load_json(DATA_FILES['quests'], {})

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
                    "strength": 5,
                    "agility": 5,
                    "intelligence": 5,
                    "vitality": 5,
                    "luck": 5
                },
                "stat_points": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "win_streak": 0,
                "best_streak": 0,
                "total_duels": 0,
                "pvp_rating": 1000,
                "inventory": [],
                "equipment": {
                    "weapon": None,
                    "shield": None,
                    "armor": None,
                    "accessory": None,
                    "boots": None
                },
                "last_daily": None,
                "last_dungeon": None,
                "title": "Новичок",
                "titles_collected": ["Новичок"],
                "achievements": [],
                "active_quests": {},
                "completed_quests": 0,
                "clan": None,
                "clan_role": None,
                "tournament_wins": 0,
                "registration_date": datetime.now().isoformat(),
                "settings": {
                    "notifications": True,
                    "duel_requests": True
                }
            }
            self.save()
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    def save(self):
        save_json(DATA_FILES['users'], users)
    
    def get_effective_stats(self):
        """Расчёт эффективных характеристик с учётом экипировки"""
        base = copy.deepcopy(self.data["stats"])
        bonuses = {
            "min_damage": base["strength"] * 2,
            "max_damage": base["strength"] * 3,
            "defense": base["vitality"],
            "speed": base["agility"],
            "crit_chance": 5 + base["luck"] * 0.5,
            "crit_multiplier": 1.5,
            "dodge_chance": 3 + base["agility"] * 0.3,
            "block_chance": 0,
            "hp": self.data["max_hp"] + base["vitality"] * 10,
            "mana": self.data["max_mana"] + base["intelligence"] * 5,
            "max_hp": self.data["max_hp"] + base["vitality"] * 10,
            "max_mana": self.data["max_mana"] + base["intelligence"] * 5
        }
        
        # Обработка экипировки
        for slot, item_key in self.data["equipment"].items():
            if not item_key:
                continue
            item = items.get(item_key) or limited_items.get(item_key)
            if not item:
                continue
            
            if item["type"] == "weapon" and "damage" in item:
                bonuses["min_damage"] += item["damage"][0]
                bonuses["max_damage"] += item["damage"][1]
            elif item["type"] == "shield":
                bonuses["defense"] += item.get("defense", 0)
                bonuses["block_chance"] += item.get("block_chance", 0)
            elif item["type"] == "armor":
                bonuses["defense"] += item.get("defense", 0)
                bonuses["max_hp"] += item.get("hp_bonus", 0)
                bonuses["hp"] = bonuses["max_hp"]
            elif item["type"] == "accessory":
                for stat, value in item.get("stats", {}).items():
                    if stat == "strength":
                        bonuses["min_damage"] += value * 2
                        bonuses["max_damage"] += value * 3
                    elif stat == "crit_chance":
                        bonuses["crit_chance"] += value
                    elif stat == "luck":
                        bonuses["crit_chance"] += value * 0.5
                    elif stat == "dodge_chance":
                        bonuses["dodge_chance"] += value
            elif item["type"] == "boots":
                bonuses["speed"] += item.get("speed", 0)
        
        bonuses["crit_chance"] = min(80, bonuses["crit_chance"])
        bonuses["dodge_chance"] = min(50, bonuses["dodge_chance"])
        bonuses["block_chance"] = min(60, bonuses["block_chance"])
        
        return bonuses

# ==================== СИСТЕМА НАВЫКОВ ====================
SKILLS_DB = {
    # Оружейные навыки
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 10, "cooldown": 0, "description": "Базовый удар мечом"},
    "quick_strike": {"name": "💨 Быстрый удар", "damage_mult": 0.8, "mana_cost": 5, "hits": 2, "description": "Два быстрых удара"},
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.5, "mana_cost": 20, "element": "fire", "burn_chance": 30, "description": "Удар с огнём"},
    "inferno_strike": {"name": "🌋 Удар инферно", "damage_mult": 2.0, "mana_cost": 35, "element": "fire", "burn_chance": 60, "cooldown": 2, "description": "Мощная огненная атака"},
    "flame_wave": {"name": "🔥 Волна пламени", "damage_mult": 2.5, "mana_cost": 50, "element": "fire", "aoe": True, "cooldown": 3, "description": "Огненная волна"},
    
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.3, "mana_cost": 15, "element": "ice", "freeze_chance": 25, "description": "Замораживающий удар"},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 1.8, "mana_cost": 30, "element": "ice", "freeze_chance": 50, "cooldown": 2, "description": "Разбивает лёд"},
    "blizzard": {"name": "🌨 Метель", "damage_mult": 2.2, "mana_cost": 45, "element": "ice", "aoe": True, "cooldown": 3, "description": "Ледяная буря"},
    
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.4, "mana_cost": 18, "element": "lightning", "stun_chance": 20, "description": "Разряд молнии"},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.0, "mana_cost": 40, "element": "lightning", "aoe": True, "stun_chance": 30, "cooldown": 3, "description": "Вызывает грозу"},
    "chain_lightning": {"name": "⚡ Цепная молния", "damage_mult": 1.6, "mana_cost": 30, "element": "lightning", "chain": 3, "cooldown": 2, "description": "Молния перепрыгивает"},
    
    "power_shot": {"name": "🎯 Мощный выстрел", "damage_mult": 1.8, "mana_cost": 20, "cooldown": 1, "description": "Прицельный выстрел"},
    "multi_shot": {"name": "🏹 Залп", "damage_mult": 0.6, "mana_cost": 25, "hits": 3, "description": "Три стрелы"},
    
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.5, "mana_cost": 20, "element": "dark", "poison_chance": 25, "description": "Удар из тени"},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.0, "mana_cost": 50, "element": "dark", "cooldown": 4, "description": "Смертельный удар"},
    "soul_drain": {"name": "💀 Похищение души", "damage_mult": 1.8, "mana_cost": 35, "element": "dark", "life_steal": 0.5, "cooldown": 3, "description": "Крадёт жизнь"},
    
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.4, "mana_cost": 20, "element": "light", "description": "Удар светом"},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 2.5, "mana_cost": 45, "element": "light", "cooldown": 3, "description": "Мощная святая атака"},
    
    # Защитные навыки
    "block": {"name": "🛡 Блок", "defense_boost": 20, "mana_cost": 10, "cooldown": 1, "description": "Усиленная защита"},
    "shield_bash": {"name": "💥 Удар щитом", "damage_mult": 0.8, "mana_cost": 15, "stun_chance": 30, "description": "Оглушающий удар"},
    "shield_wall": {"name": "🧱 Стена щитов", "defense_boost": 40, "mana_cost": 25, "cooldown": 2, "description": "Мощная защита"},
    "counter_attack": {"name": "↩ Контратака", "damage_mult": 1.3, "mana_cost": 20, "reflect": 0.3, "cooldown": 2, "description": "Отражает урон"},
    "divine_protection": {"name": "💫 Божественная защита", "defense_boost": 60, "mana_cost": 40, "cooldown": 3, "description": "Сильная защита"},
    
    # Броня
    "fortify": {"name": "🛡 Укрепление", "defense_boost": 15, "hp_restore": 20, "mana_cost": 15, "cooldown": 1, "description": "Восстанавливает HP и защиту"},
    "endure": {"name": "💪 Выносливость", "defense_boost": 25, "damage_reduction": 0.3, "mana_cost": 25, "cooldown": 2, "description": "Уменьшает входящий урон"},
    "iron_will": {"name": "⚙ Железная воля", "defense_boost": 30, "hp_restore": 40, "mana_cost": 30, "cooldown": 2, "description": "Восстановление и защита"},
    "rebirth": {"name": "🦅 Возрождение", "hp_restore": 100, "mana_cost": 60, "cooldown": 5, "description": "Полное исцеление"},
    
    # Универсальные
    "meditate": {"name": "🧘 Медитация", "mana_restore": 30, "cooldown": 1, "description": "Восстанавливает ману"},
    "focus": {"name": "🎯 Концентрация", "crit_boost": 20, "mana_cost": 15, "cooldown": 2, "description": "Повышает шанс крита"},
    "berserk": {"name": "💢 Берсерк", "damage_mult": 1.5, "defense_penalty": 10, "mana_cost": 25, "cooldown": 3, "description": "Сильная атака ценой защиты"},
    "first_aid": {"name": "💊 Первая помощь", "hp_restore": 40, "mana_cost": 20, "cooldown": 2, "description": "Лечит раны"}
}

# ==================== ПОШАГОВАЯ БОЕВАЯ СИСТЕМА ====================
class TurnBasedDuel:
    def __init__(self, player1_id, player2_id, bet=0, duel_type="normal"):
        self.p1_id = str(player1_id)
        self.p2_id = str(player2_id)
        self.bet = bet
        self.duel_type = duel_type
        self.current_turn = 1
        self.max_turns = 30
        self.is_active = True
        
        # Инициализация игроков
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        # Получение статов
        self.p1_eff = self.p1.get_effective_stats()
        self.p2_eff = self.p2.get_effective_stats()
        
        # Инициализация HP и MP
        self.p1_hp = self.p1_eff["max_hp"]
        self.p2_hp = self.p2_eff["max_hp"]
        self.p1_max_hp = self.p1_hp
        self.p2_max_hp = self.p2_hp
        
        self.p1_mp = self.p1_eff["max_mana"]
        self.p2_mp = self.p2_eff["max_mana"]
        self.p1_max_mp = self.p1_mp
        self.p2_max_mp = self.p2_mp
        
        # Определение очерёдности
        p1_speed = self.p1_eff["speed"] + random.randint(-10, 10)
        p2_speed = self.p2_eff["speed"] + random.randint(-10, 10)
        
        if p1_speed >= p2_speed:
            self.current_player = 1
            self.waiting_player = 2
        else:
            self.current_player = 2
            self.waiting_player = 1
        
        # Кулдауны навыков
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Активные эффекты
        self.p1_effects = []
        self.p2_effects = []
        
        # Баффы/дебаффы
        self.p1_buffs = {"defense_boost": 0, "damage_mult": 1.0, "crit_boost": 0, "damage_reduction": 0}
        self.p2_buffs = {"defense_boost": 0, "damage_mult": 1.0, "crit_boost": 0, "damage_reduction": 0}
        
        # Лог боя
        self.battle_log = []
        
        # Сохранение в активные дуэли
        active_duels[f"{self.p1_id}_vs_{self.p2_id}"] = {
            "p1_id": self.p1_id,
            "p2_id": self.p2_id,
            "bet": bet,
            "type": duel_type,
            "current_turn": self.current_turn,
            "current_player": self.current_player,
            "started_at": datetime.now().isoformat()
        }
        save_json(DATA_FILES['duels'], active_duels)
    
    def get_available_skills(self, player_num):
        """Получить доступные навыки для игрока"""
        player = self.p1 if player_num == 1 else self.p2
        equipment = player.data["equipment"]
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        
        available = []
        
        # Базовые навыки (всегда доступны)
        base_skills = ["quick_attack", "heavy_attack", "defend", "meditate"]
        for skill_id in base_skills:
            if skill_id not in cooldowns or cooldowns[skill_id] <= 0:
                available.append(skill_id)
        
        # Навыки оружия
        weapon_key = equipment.get("weapon")
        if weapon_key:
            weapon = items.get(weapon_key) or limited_items.get(weapon_key)
            if weapon and "skills" in weapon:
                for skill_id in weapon["skills"]:
                    if skill_id in SKILLS_DB:
                        cd = cooldowns.get(skill_id, 0)
                        if cd <= 0:
                            available.append(skill_id)
        
        # Навыки щита
        shield_key = equipment.get("shield")
        if shield_key:
            shield = items.get(shield_key) or limited_items.get(shield_key)
            if shield and "skills" in shield:
                for skill_id in shield["skills"]:
                    if skill_id in SKILLS_DB:
                        cd = cooldowns.get(skill_id, 0)
                        if cd <= 0:
                            available.append(skill_id)
        
        # Навыки брони
        armor_key = equipment.get("armor")
        if armor_key:
            armor = items.get(armor_key) or limited_items.get(armor_key)
            if armor and "skills" in armor:
                for skill_id in armor["skills"]:
                    if skill_id in SKILLS_DB:
                        cd = cooldowns.get(skill_id, 0)
                        if cd <= 0:
                            available.append(skill_id)
        
        return list(set(available))
    
    def use_skill(self, player_num, skill_id):
        """Использовать навык"""
        if not self.is_active:
            return "Бой завершён"
        
        if player_num != self.current_player:
            return "Сейчас не ваш ход!"
        
        available = self.get_available_skills(player_num)
        if skill_id not in available:
            return "Навык недоступен или на перезарядке!"
        
        attacker = player_num
        defender = 3 - player_num  # 1->2, 2->1
        
        attacker_player = self.p1 if attacker == 1 else self.p2
        defender_player = self.p2 if attacker == 1 else self.p1
        
        attacker_hp = self.p1_hp if attacker == 1 else self.p2_hp
        defender_hp = self.p2_hp if attacker == 1 else self.p1_hp
        
        attacker_mp = self.p1_mp if attacker == 1 else self.p2_mp
        defender_mp = self.p2_mp if attacker == 1 else self.p1_mp
        
        attacker_eff = self.p1_eff if attacker == 1 else self.p2_eff
        defender_eff = self.p2_eff if attacker == 1 else self.p1_eff
        
        attacker_buffs = self.p1_buffs if attacker == 1 else self.p2_buffs
        defender_buffs = self.p2_buffs if attacker == 1 else self.p1_buffs
        
        cooldowns = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
        
        # Получение данных навыка
        skill = None
        if skill_id == "quick_attack":
            skill = {"name": "⚡ Быстрая атака", "damage_mult": 1.0, "mana_cost": 0, "cooldown": 0, "description": "Базовая быстрая атака"}
        elif skill_id == "heavy_attack":
            skill = {"name": "💪 Тяжёлая атака", "damage_mult": 1.5, "mana_cost": 15, "cooldown": 1, "description": "Мощная атака"}
        elif skill_id == "defend":
            skill = {"name": "🛡 Защита", "defense_boost": 15, "mana_cost": 5, "cooldown": 1, "description": "Усиление защиты"}
        elif skill_id == "meditate":
            skill = {"name": "🧘 Медитация", "mana_restore": 30, "cooldown": 2, "description": "Восстановление маны"}
        elif skill_id in SKILLS_DB:
            skill = SKILLS_DB[skill_id]
        
        if not skill:
            return "Навык не найден"
        
        # Проверка маны
        mana_cost = skill.get("mana_cost", 0)
        if attacker_mp < mana_cost:
            return f"❌ Недостаточно маны! Нужно {mana_cost} MP"
        
        # Трата маны
        if attacker == 1:
            self.p1_mp -= mana_cost
        else:
            self.p2_mp -= mana_cost
        
        result_text = ""
        
        # Обработка атакующих навыков
        if "damage_mult" in skill:
            # Расчёт урона
            min_dmg = int(attacker_eff["min_damage"] * attacker_buffs["damage_mult"])
            max_dmg = int(attacker_eff["max_damage"] * attacker_buffs["damage_mult"])
            base_damage = random.randint(min_dmg, max_dmg)
            
            # Множитель навыка
            damage = int(base_damage * skill["damage_mult"])
            
            # Критический удар
            is_crit = False
            crit_chance = attacker_eff["crit_chance"] + attacker_buffs["crit_boost"]
            if random.random() * 100 < crit_chance:
                damage = int(damage * attacker_eff["crit_multiplier"])
                is_crit = True
            
            # Элементальный бонус
            if "element" in skill:
                element = skill["element"]
                defender_element = defender_eff.get("element")
                if defender_element and ELEMENTS.get(element, {}).get("strong_against") == defender_element:
                    damage = int(damage * 1.5)
                    result_text += f"💥 СУПЕРЭФФЕКТИВНО! {ELEMENTS[element]['name']} vs {defender_element}\n"
            
            # Защита противника
            defense = defender_eff["defense"] + defender_buffs["defense_boost"]
            damage_reduction = defense / (defense + 150)
            damage = int(damage * (1 - damage_reduction))
            
            # Дополнительное уменьшение урона
            if defender_buffs["damage_reduction"] > 0:
                damage = int(damage * (1 - defender_buffs["damage_reduction"]))
            
            # Блок
            block_chance = defender_eff["block_chance"]
            if random.random() * 100 < block_chance:
                damage = int(damage * 0.5)
                result_text += "🛡 ЧАСТИЧНЫЙ БЛОК!\n"
            
            # Уклонение
            dodge_chance = defender_eff["dodge_chance"]
            if random.random() * 100 < dodge_chance:
                damage = 0
                result_text += "💨 УКЛОНЕНИЕ!\n"
            
            # Несколько ударов
            hits = skill.get("hits", 1)
            total_damage = 0
            for h in range(hits):
                hit_damage = damage // hits
                total_damage += hit_damage
                
                # Применение эффектов
                if "burn_chance" in skill and random.random() * 100 < skill["burn_chance"]:
                    self._apply_effect(defender, "burn", 3)
                    result_text += "🔥 Горение!\n"
                if "freeze_chance" in skill and random.random() * 100 < skill["freeze_chance"]:
                    self._apply_effect(defender, "freeze", 2)
                    result_text += "❄ Заморозка!\n"
                if "stun_chance" in skill and random.random() * 100 < skill["stun_chance"]:
                    self._apply_effect(defender, "stun", 1)
                    result_text += "⚡ Оглушение!\n"
                if "poison_chance" in skill and random.random() * 100 < skill["poison_chance"]:
                    self._apply_effect(defender, "poison", 4)
                    result_text += "☠ Отравление!\n"
            
            # Применение урона
            if defender == 1:
                self.p1_hp = max(0, self.p1_hp - total_damage)
            else:
                self.p2_hp = max(0, self.p2_hp - total_damage)
            
            # Вампиризм
            if "life_steal" in skill:
                heal = int(total_damage * skill["life_steal"])
                if attacker == 1:
                    self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
                else:
                    self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
                result_text += f"💚 Вампиризм +{heal} HP\n"
            
            crit_text = "💥 КРИТ! " if is_crit else ""
            result_text += f"{crit_text}⚔ Нанесено {total_damage} урона"
        
        # Обработка защитных навыков
        if "defense_boost" in skill:
            if attacker == 1:
                self.p1_buffs["defense_boost"] += skill["defense_boost"]
            else:
                self.p2_buffs["defense_boost"] += skill["defense_boost"]
            result_text += f"🛡 Защита +{skill['defense_boost']}"
        
        # Восстановление HP
        if "hp_restore" in skill:
            heal = skill["hp_restore"]
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            result_text += f"💚 +{heal} HP"
        
        # Восстановление маны
        if "mana_restore" in skill:
            mana = skill["mana_restore"]
            if attacker == 1:
                self.p1_mp = min(self.p1_max_mp, self.p1_mp + mana)
            else:
                self.p2_mp = min(self.p2_max_mp, self.p2_mp + mana)
            result_text += f"💎 +{mana} MP"
        
        # Установка кулдауна
        if "cooldown" in skill and skill["cooldown"] > 0:
            cooldowns[skill_id] = skill["cooldown"]
        
        # Уменьшение кулдаунов
        self._reduce_cooldowns(attacker)
        
        # Обработка эффектов
        result_text += "\n" + self._process_effects(defender)
        
        # Переключение хода
        self.current_player, self.waiting_player = self.waiting_player, self.current_player
        self.current_turn += 1
        
        # Сброс временных баффов
        self.p1_buffs["defense_boost"] = max(0, self.p1_buffs["defense_boost"] - 3)
        self.p2_buffs["defense_boost"] = max(0, self.p2_buffs["defense_boost"] - 3)
        
        # Проверка завершения
        if self.p1_hp <= 0 or self.p2_hp <= 0 or self.current_turn > self.max_turns:
            self.is_active = False
        
        return result_text
    
    def _apply_effect(self, player_num, effect, duration):
        """Наложить эффект"""
        if player_num == 1:
            self.p1_effects.append({"type": effect, "duration": duration})
        else:
            self.p2_effects.append({"type": effect, "duration": duration})
    
    def _process_effects(self, player_num):
        """Обработать активные эффекты"""
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        result = ""
        
        for effect in effects[:]:
            if effect["type"] == "burn":
                damage = random.randint(8, 18)
                if player_num == 1:
                    self.p1_hp -= damage
                else:
                    self.p2_hp -= damage
                result += f"🔥 Горение -{damage} HP\n"
                effect["duration"] -= 1
                
            elif effect["type"] == "poison":
                damage = random.randint(10, 20)
                if player_num == 1:
                    self.p1_hp -= damage
                else:
                    self.p2_hp -= damage
                result += f"☠ Яд -{damage} HP\n"
                effect["duration"] -= 1
                
            elif effect["type"] == "freeze":
                result += "❄ Заморожен! Пропуск хода\n"
                effect["duration"] -= 1
                
            elif effect["type"] == "stun":
                result += "⚡ Оглушён! Пропуск хода\n"
                effect["duration"] -= 1
            
            if effect["duration"] <= 0:
                effects.remove(effect)
        
        return result
    
    def _reduce_cooldowns(self, player_num):
        """Уменьшить кулдауны"""
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        for skill_id in list(cooldowns.keys()):
            cooldowns[skill_id] -= 1
            if cooldowns[skill_id] <= 0:
                del cooldowns[skill_id]
    
    def get_battle_state(self):
        """Получить текущее состояние боя для отображения"""
        if self.current_player == 1:
            active_player = self.p1
            active_hp = self.p1_hp
            active_max_hp = self.p1_max_hp
            active_mp = self.p1_mp
            active_max_mp = self.p1_max_mp
            waiting_hp = self.p2_hp
            waiting_max_hp = self.p2_max_hp
            waiting_mp = self.p2_mp
            waiting_max_mp = self.p2_max_mp
        else:
            active_player = self.p2
            active_hp = self.p2_hp
            active_max_hp = self.p2_max_hp
            active_mp = self.p2_mp
            active_max_mp = self.p2_max_mp
            waiting_hp = self.p1_hp
            waiting_max_hp = self.p1_max_hp
            waiting_mp = self.p1_mp
            waiting_max_mp = self.p2_max_mp
        
        def hp_bar(current, maximum):
            pct = current / maximum if maximum > 0 else 0
            filled = int(pct * 10)
            return f"[{'█' * filled}{'░' * (10 - filled)}] {current}/{maximum}"
        
        return {
            "turn": self.current_turn,
            "active_name": active_player.data["first_name"],
            "active_hp_bar": hp_bar(active_hp, active_max_hp),
            "active_mp_bar": hp_bar(active_mp, active_max_mp),
            "waiting_name": self.p2.data["first_name"] if self.current_player == 1 else self.p1.data["first_name"],
            "waiting_hp_bar": hp_bar(waiting_hp, waiting_max_hp),
            "waiting_mp_bar": hp_bar(waiting_mp, waiting_max_mp),
            "available_skills": self.get_available_skills(self.current_player),
            "active_effects": self.p1_effects if self.current_player == 1 else self.p2_effects
        }

# ==================== ОСНОВНОЕ МЕНЮ ====================
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
        ban = banned_users[str(user_id)]
        bot.send_message(message.chat.id, f"⛔ Вы забанены!\nПричина: {ban.get('reason', 'Нет')}")
        return
    
    username = message.from_user.username or f"user_{user_id}"
    first_name = message.from_user.first_name or "Игрок"
    
    player = Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v5.0 ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

🎯 <b>ПОЛНАЯ ВЕРСИЯ:</b>
• Пошаговые дуэли со стратегией
• 30+ навыков и способностей
• Стихии и контр-элементы
• Статус-эффекты в реальном времени
• Данжи, кланы, турниры
• Рынок и обмен предметами
• Квесты и достижения
• Рейтинговая система

💰 Стартовый бонус: <b>500 монет</b>
⚡ Боевая система с MP и кулдаунами

<i>Выбирай раздел в меню:</i>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль", callback_data="quick_duel_menu"),
        types.InlineKeyboardButton("👥 Дуэль с игроком", callback_data="pvp_duel_info"),
        types.InlineKeyboardButton("🏆 Рейтинговая дуэль", callback_data="ranked_duel_info"),
        types.InlineKeyboardButton("💀 Хардкорная дуэль", callback_data="hardcore_info"),
        types.InlineKeyboardButton("🔥 Дуэль на выживание", callback_data="survival_info"),
        types.InlineKeyboardButton("🎯 Дружеский спарринг", callback_data="sparring_info")
    )
    
    text = """
<b>⚔️ РАЗДЕЛ ДУЭЛЕЙ</b>

<b>⚡ Быстрая дуэль</b> — против бота с выбором ставки
<b>👥 Дуэль с игроком</b> — PvP пошаговый бой
<b>🏆 Рейтинговая</b> — за очки рейтинга
<b>💀 Хардкорная</b> — высокие ставки (500+)
<b>🔥 На выживание</b> — до последнего HP
<b>🎯 Дружеский спарринг</b> — без потерь

<i>Все дуэли — пошаговые со стратегией!</i>
"""
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="hero_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="hero_inventory"),
        types.InlineKeyboardButton("⚡ Характеристики", callback_data="hero_attributes"),
        types.InlineKeyboardButton("🏅 Достижения", callback_data="hero_achievements"),
        types.InlineKeyboardButton("📜 Квесты", callback_data="hero_quests"),
        types.InlineKeyboardButton("⚙ Настройки", callback_data="hero_settings")
    )
    bot.send_message(message.chat.id, "<b>👤 МЕНЮ ГЕРОЯ</b>", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🏪 Торговля")
def trade_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛒 Магазин", callback_data="trade_shop"),
        types.InlineKeyboardButton("💎 Лимитированные", callback_data="trade_limited"),
        types.InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="trade_daily"),
        types.InlineKeyboardButton("💱 Рынок игроков", callback_data="trade_market"),
        types.InlineKeyboardButton("💰 Продать предмет", callback_data="trade_sell"),
        types.InlineKeyboardButton("📦 Мои лоты", callback_data="trade_my_lots")
    )
    bot.send_message(message.chat.id, "<b>🏪 ТОРГОВЛЯ</b>", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🌍 Мир")
def world_menu(message):
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

# ==================== БЫСТРАЯ ДУЭЛЬ С ВЫБОРОМ СТАВКИ ====================
@bot.callback_query_handler(func=lambda call: call.data == "quick_duel_menu")
def quick_duel_menu(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("50💰", callback_data="qduel_50"),
        types.InlineKeyboardButton("100💰", callback_data="qduel_100"),
        types.InlineKeyboardButton("200💰", callback_data="qduel_200"),
        types.InlineKeyboardButton("500💰", callback_data="qduel_500"),
        types.InlineKeyboardButton("1000💰", callback_data="qduel_1000"),
        types.InlineKeyboardButton("5000💰", callback_data="qduel_5000"),
        types.InlineKeyboardButton("Отмена", callback_data="cancel_action")
    )
    
    bot.edit_message_text(
        f"<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n\n"
        f"💰 Ваш баланс: <b>{player.data['money']} монет</b>\n"
        f"Выберите ставку:",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def start_quick_duel(call):
    user_id = call.from_user.id
    bet = int(call.data.split("_")[1])
    player = Player(user_id)
    
    if player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Недостаточно монет! Нужно {bet}💰")
        return
    
    # Создание бота-противника
    bot_level = random.randint(max(1, player.data["level"] - 3), player.data["level"] + 3)
    bot_id = f"bot_{random.randint(10000, 99999)}"
    
    # Генерация экипировки для бота
    bot_equip = {"weapon": None, "shield": None, "armor": None, "accessory": None, "boots": None}
    for slot in ["weapon", "shield", "armor", "accessory", "boots"]:
        slot_items = [k for k, v in items.items() if v["type"] == slot and v.get("level_req", 1) <= bot_level]
        if slot_items and random.random() < 0.6:
            bot_equip[slot] = random.choice(slot_items)
    
    users[bot_id] = {
        "username": f"Bot_{bot_level}",
        "first_name": f"⚔ Бот Lv.{bot_level}",
        "money": 0, "level": bot_level, "exp": 0, "total_exp": 0,
        "hp": 100 + bot_level * 10, "max_hp": 100 + bot_level * 10,
        "mana": 50 + bot_level * 5, "max_mana": 50 + bot_level * 5,
        "stats": {
            "strength": 5 + bot_level,
            "agility": 5 + bot_level // 2,
            "intelligence": 5 + bot_level // 3,
            "vitality": 5 + bot_level // 2,
            "luck": 3 + bot_level // 4
        },
        "stat_points": 0, "wins": 0, "losses": 0, "draws": 0,
        "win_streak": 0, "best_streak": 0, "total_duels": 0,
        "pvp_rating": 1000 + bot_level * 10,
        "inventory": [],
        "equipment": bot_equip,
        "last_daily": None, "last_dungeon": None,
        "title": "Бот", "titles_collected": ["Бот"],
        "achievements": [], "active_quests": {}, "completed_quests": 0,
        "clan": None, "clan_role": None, "tournament_wins": 0,
        "registration_date": datetime.now().isoformat(),
        "settings": {}
    }
    save_json(DATA_FILES['users'], users)
    
    player.data["money"] -= bet
    player.save()
    
    # Создание пошаговой дуэли
    duel = TurnBasedDuel(user_id, bot_id, bet, "quick")
    
    # Показываем интерфейс дуэли
    show_duel_interface(call.message, duel, user_id)

def show_duel_interface(message, duel, user_id):
    """Отображение интерфейса пошаговой дуэли"""
    state = duel.get_battle_state()
    current_player = duel.current_player
    
    is_player_turn = (current_player == 1 and str(user_id) == duel.p1_id) or \
                     (current_player == 2 and str(user_id) == duel.p2_id)
    
    if not duel.is_active:
        # Бой завершён
        finish_duel(message, duel, user_id)
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if is_player_turn:
        # Показываем доступные навыки
        skills = state["available_skills"]
        for skill_id in skills[:8]:  # Ограничиваем 8 навыками
            skill_info = SKILLS_DB.get(skill_id, {})
            name = skill_info.get("name", skill_id)
            mana = skill_info.get("mana_cost", 0)
            markup.add(types.InlineKeyboardButton(
                f"{name} ({mana}MP)", callback_data=f"useskill_{skill_id}"
            ))
        
        markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh_duel"))
    else:
        # Ход противника
        markup.add(types.InlineKeyboardButton("⏳ Ожидание хода противника...", callback_data="wait_turn"))
        if duel.current_player == 2:
            # Ход бота
            bot_skill = random.choice(state["available_skills"])
            result = duel.use_skill(duel.current_player, bot_skill)
            time.sleep(1)
            show_duel_interface(message, duel, user_id)
            return
    
    # Формирование текста
    text = f"""
<b>⚔ ПОШАГОВАЯ ДУЭЛЬ</b>
Ход: <b>#{state['turn']}</b>

<b>⚔ Вы:</b>
❤ {state['active_hp_bar'] if is_player_turn else state['waiting_hp_bar']}
💎 MP: {state['active_mp_bar'] if is_player_turn else state['waiting_mp_bar']}

<b>Противник:</b>
❤ {state['waiting_hp_bar'] if is_player_turn else state['active_hp_bar']}
💎 MP: {state['waiting_mp_bar'] if is_player_turn else state['active_mp_bar']}

{'🟢 <b>ВАШ ХОД</b>' if is_player_turn else '🔴 <b>ХОД ПРОТИВНИКА</b>'}
Выберите навык:
"""
    
    bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup)

def finish_duel(message, duel, user_id):
    """Завершение дуэли и начисление наград"""
    p1 = Player(duel.p1_id)
    p2 = Player(duel.p2_id)
    
    if duel.p1_hp <= 0:
        winner_id = duel.p2_id
        loser_id = duel.p1_id
    elif duel.p2_hp <= 0:
        winner_id = duel.p1_id
        loser_id = duel.p2_id
    else:
        # Ничья
        p1.data["draws"] += 1
        p2.data["draws"] += 1
        if duel.bet > 0:
            p1.data["money"] += duel.bet
            p2.data["money"] += duel.bet
        p1.save()
        p2.save()
        result_text = "<b>🤝 НИЧЬЯ!</b>\nСтавки возвращены"
        bot.edit_message_text(result_text, message.chat.id, message.message_id)
        cleanup_duel(duel)
        return
    
    winner = Player(winner_id)
    loser = Player(loser_id)
    
    if duel.bet > 0:
        reward = duel.bet * 2
        winner.data["money"] += reward
    
    winner.data["wins"] += 1
    winner.data["win_streak"] += 1
    winner.data["total_duels"] += 1
    winner.data["pvp_rating"] += random.randint(15, 30)
    
    loser.data["losses"] += 1
    loser.data["win_streak"] = 0
    loser.data["total_duels"] += 1
    loser.data["pvp_rating"] = max(0, loser.data["pvp_rating"] - random.randint(10, 25))
    
    # Опыт
    exp_winner = duel.bet // 2 + duel.current_turn * 5
    exp_loser = duel.bet // 5 + duel.current_turn * 2
    
    winner.data["exp"] += exp_winner
    winner.data["total_exp"] += exp_winner
    loser.data["exp"] += exp_loser
    loser.data["total_exp"] += exp_loser
    
    # Проверка уровней
    old_level_w = winner.data["level"]
    check_level_up(winner)
    old_level_l = loser.data["level"]
    check_level_up(loser)
    
    winner.save()
    loser.save()
    
    result_text = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

🏆 Победитель: <b>{winner.data['first_name']}</b>
💀 Проигравший: <b>{loser.data['first_name']}</b>

💰 Приз: <b>{duel.bet * 2 if duel.bet > 0 else 0} монет</b>
✨ Опыт: +{exp_winner} / +{exp_loser}
📊 Ходов: <b>{duel.current_turn}</b>
"""
    if winner.data["level"] > old_level_w:
        result_text += f"\n🎉 {winner.data['first_name']} получает уровень <b>{winner.data['level']}</b>!"
    if loser.data["level"] > old_level_l:
        result_text += f"\n🎉 {loser.data['first_name']} получает уровень <b>{loser.data['level']}</b>!"
    
    bot.edit_message_text(result_text, message.chat.id, message.message_id)
    cleanup_duel(duel)

def cleanup_duel(duel):
    """Очистка данных дуэли"""
    duel_key = f"{duel.p1_id}_vs_{duel.p2_id}"
    if duel_key in active_duels:
        del active_duels[duel_key]
        save_json(DATA_FILES['duels'], active_duels)
    
    # Удаление ботов
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_"):
            if uid in users:
                del users[uid]
    save_json(DATA_FILES['users'], users)

@bot.callback_query_handler(func=lambda call: call.data.startswith("useskill_"))
def use_skill_handler(call):
    user_id = call.from_user.id
    skill_id = call.data.split("_", 1)[1]
    
    # Поиск активной дуэли
    duel_found = None
    for key, duel_data in active_duels.items():
        if str(user_id) in [duel_data["p1_id"], duel_data["p2_id"]]:
            # Восстановление дуэли
            p1_id = duel_data["p1_id"]
            p2_id = duel_data["p2_id"]
            bet = duel_data["bet"]
            duel_type = duel_data["type"]
            duel_found = TurnBasedDuel(p1_id, p2_id, bet, duel_type)
            break
    
    if not duel_found:
        bot.answer_callback_query(call.id, "❌ Дуэль не найдена!")
        return
    
    # Использование навыка
    player_num = 1 if str(user_id) == duel_found.p1_id else 2
    result = duel_found.use_skill(player_num, skill_id)
    
    if result.startswith("❌") or result.startswith("Сейчас") or result.startswith("Навык"):
        bot.answer_callback_query(call.id, result)
        show_duel_interface(call.message, duel_found, user_id)
        return
    
    bot.answer_callback_query(call.id, result[:50])
    show_duel_interface(call.message, duel_found, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "refresh_duel")
def refresh_duel(call):
    user_id = call.from_user.id
    for key, duel_data in active_duels.items():
        if str(user_id) in [duel_data["p1_id"], duel_data["p2_id"]]:
            p1_id = duel_data["p1_id"]
            p2_id = duel_data["p2_id"]
            bet = duel_data["bet"]
            duel_type = duel_data["type"]
            duel_found = TurnBasedDuel(p1_id, p2_id, bet, duel_type)
            show_duel_interface(call.message, duel_found, user_id)
            return
    
    bot.answer_callback_query(call.id, "❌ Дуэль не найдена")

# ==================== PVP ДУЭЛЬ ====================
@bot.callback_query_handler(func=lambda call: call.data == "pvp_duel_info")
def pvp_duel_info(call):
    text = """
<b>👥 PVP ДУЭЛЬ</b>

Для вызова игрока:
1. Ответьте на его сообщение
2. Используйте команду: <code>/duel [ставка]</code>

Пример: <code>/duel 500</code>

Ставка от 50 до 10000💰
Победитель получает всё!
Пошаговый бой со стратегией!
"""
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.message_handler(commands=['duel'])
def duel_command_handler(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Ответьте на сообщение игрока!")
        return
    
    user_id = message.from_user.id
    opponent_id = message.reply_to_message.from_user.id
    
    if user_id == opponent_id:
        bot.send_message(message.chat.id, "❌ Нельзя вызвать себя!")
        return
    
    try:
        parts = message.text.split()
        bet = int(parts[1]) if len(parts) > 1 else 100
        bet = max(50, min(10000, bet))
    except:
        bet = 100
    
    player = Player(user_id)
    opponent = Player(opponent_id)
    
    if player.data["money"] < bet:
        bot.send_message(message.chat.id, f"❌ У вас недостаточно монет! Нужно {bet}💰")
        return
    if opponent.data["money"] < bet:
        bot.send_message(message.chat.id, f"❌ У противника недостаточно монет!")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"acceptduel_{user_id}_{bet}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"declineduel_{user_id}")
    )
    
    bot.send_message(message.chat.id, 
        f"<b>⚔ ВЫЗОВ НА ДУЭЛЬ!</b>\n\n"
        f"{message.from_user.first_name} вызывает {message.reply_to_message.from_user.first_name}!\n"
        f"Ставка: <b>{bet}💰</b>",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("acceptduel_"))
def accept_duel_handler(call):
    parts = call.data.split("_")
    challenger_id = int(parts[1])
    bet = int(parts[2])
    opponent_id = call.from_user.id
    
    if opponent_id == challenger_id:
        bot.answer_callback_query(call.id, "❌ Нельзя принять свой вызов!")
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
    
    duel = TurnBasedDuel(challenger_id, opponent_id, bet, "pvp")
    bot.edit_message_text("⚔ Дуэль начинается!", call.message.chat.id, call.message.message_id)
    show_duel_interface(call.message, duel, opponent_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("declineduel_"))
def decline_duel_handler(call):
    bot.edit_message_text("❌ Вызов отклонён", call.message.chat.id, call.message.message_id)

# ==================== МАГАЗИН ====================
@bot.callback_query_handler(func=lambda call: call.data == "trade_shop")
def shop_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚔ Оружие", callback_data="shopcat_weapon"),
        types.InlineKeyboardButton("🛡 Щиты", callback_data="shopcat_shield"),
        types.InlineKeyboardButton("🧥 Броня", callback_data="shopcat_armor"),
        types.InlineKeyboardButton("📿 Аксессуары", callback_data="shopcat_accessory"),
        types.InlineKeyboardButton("🧪 Зелья", callback_data="shopcat_potion"),
        types.InlineKeyboardButton("👢 Обувь", callback_data="shopcat_boots")
    )
    bot.edit_message_text("<b>🛒 МАГАЗИН</b>\nВыберите категорию:", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shopcat_"))
def shop_category(call):
    category = call.data.split("_")[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    cat_names = {
        "weapon": "⚔ ОРУЖИЕ", "shield": "🛡 ЩИТЫ", "armor": "🧥 БРОНЯ",
        "accessory": "📿 АКСЕССУАРЫ", "potion": "🧪 ЗЕЛЬЯ", "boots": "👢 ОБУВЬ"
    }
    
    cat_items = {k: v for k, v in items.items() if v["type"] == category}
    
    shop_text = f"<b>{cat_names.get(category, category)}</b>\n"
    shop_text += f"💰 Баланс: <b>{player.data['money']}</b>\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, item in sorted(cat_items.items(), key=lambda x: x[1]["price"]):
        if player.data["level"] < item.get("level_req", 1):
            continue
        
        rarity = RARITY_COLORS.get(item["rarity"], "⬜")
        
        if item["type"] == "weapon":
            stats = f"Урон: {item['damage'][0]}-{item['damage'][1]}"
        elif item["type"] in ["shield", "armor"]:
            stats = f"Защита: {item.get('defense', 0)}"
        elif item["type"] == "potion":
            stats = f"Лечение: {item.get('heal', 0)}"
        elif item["type"] == "accessory":
            stats = f"Бонус: {item.get('description', '')}"
        elif item["type"] == "boots":
            stats = f"Скорость: +{item.get('speed', 0)}"
        else:
            stats = ""
        
        shop_text += f"{rarity} <b>{item['name']}</b> — {stats}\n"
        shop_text += f"   💰 {item['price']} | Ур.{item.get('level_req', 1)}\n\n"
        
        markup.add(types.InlineKeyboardButton(
            f"Купить: {item['name']}",
            callback_data=f"buyitem_{item_key}"
        ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="trade_shop"))
    bot.edit_message_text(shop_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

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

# ==================== ТУРНИРЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_tournaments")
def tournaments_menu(call):
    if not tournaments:
        tournaments["active"] = {
            "name": "Еженедельный турнир",
            "participants": [],
            "prize_pool": 5000,
            "started_at": datetime.now().isoformat(),
            "status": "registration"
        }
        save_json(DATA_FILES['tournaments'], tournaments)
    
    tour = tournaments.get("active", {})
    
    text = f"""
<b>🏟 ТУРНИРЫ</b>

<b>{tour.get('name', 'Турнир')}</b>
Статус: {tour.get('status', 'Ожидание')}
Участников: {len(tour.get('participants', []))}
Призовой фонд: <b>{tour.get('prize_pool', 0)}💰</b>

Взнос: 500💰
Победитель получает всё!
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🏆 Участвовать (500💰)", callback_data="tour_join"),
        types.InlineKeyboardButton("📋 Список участников", callback_data="tour_list"),
        types.InlineKeyboardButton("ℹ Правила", callback_data="tour_rules")
    )
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "tour_join")
def tournament_join(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data["money"] < 500:
        bot.answer_callback_query(call.id, "❌ Нужно 500💰 для участия!")
        return
    
    tour = tournaments.get("active", {})
    participants = tour.get("participants", [])
    
    if str(user_id) in participants:
        bot.answer_callback_query(call.id, "❌ Вы уже участвуете!")
        return
    
    player.data["money"] -= 500
    player.save()
    
    participants.append(str(user_id))
    tour["participants"] = participants
    tour["prize_pool"] += 500
    tournaments["active"] = tour
    save_json(DATA_FILES['tournaments'], tournaments)
    
    bot.answer_callback_query(call.id, "✅ Вы зарегистрированы на турнир!")
    tournaments_menu(call)

@bot.callback_query_handler(func=lambda call: call.data == "tour_list")
def tournament_list(call):
    tour = tournaments.get("active", {})
    participants = tour.get("participants", [])
    
    if not participants:
        bot.answer_callback_query(call.id, "📋 Нет участников")
        return
    
    text = "<b>📋 УЧАСТНИКИ ТУРНИРА</b>\n\n"
    for i, uid in enumerate(participants[:20], 1):
        p = Player(uid)
        text += f"{i}. {p.data['first_name']} (Lv.{p.data['level']})\n"
    
    bot.answer_callback_query(call.id, "Список загружен")
    bot.send_message(call.message.chat.id, text)

# ==================== КЛАНЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_clans")
def clans_menu(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data["clan"]:
        clan = clans.get(player.data["clan"], {})
        text = f"""
<b>🛡 ВАШ КЛАН</b>

Название: <b>{player.data['clan']}</b>
Участников: {len(clan.get('members', []))}
Казна: {clan.get('treasury', 0)}💰
Лидер: {clan.get('leader_name', 'Нет')}
"""
    else:
        text = """
<b>🛡 КЛАНЫ</b>

Вы не состоите в клане.
Создайте свой или вступите в существующий!

Создать клан: <code>/createclan [название]</code>
Вступить: <code>/joinclan [название]</code>
Стоимость создания: 5000💰
"""
    
    markup = types.InlineKeyboardMarkup()
    if player.data["clan"]:
        markup.add(
            types.InlineKeyboardButton("👥 Участники", callback_data="clan_members"),
            types.InlineKeyboardButton("💰 Пополнить казну", callback_data="clan_donate"),
            types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave")
        )
    else:
        markup.add(
            types.InlineKeyboardButton("📋 Список кланов", callback_data="clan_list"),
            types.InlineKeyboardButton("ℹ Информация", callback_data="clan_info")
        )
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(commands=['createclan'])
def create_clan(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    if player.data["clan"]:
        bot.send_message(message.chat.id, "❌ Вы уже в клане!")
        return
    
    if player.data["money"] < 5000:
        bot.send_message(message.chat.id, "❌ Нужно 5000💰!")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ /createclan [название]")
        return
    
    clan_name = parts[1].strip()
    if clan_name in clans:
        bot.send_message(message.chat.id, "❌ Клан уже существует!")
        return
    
    player.data["money"] -= 5000
    player.data["clan"] = clan_name
    player.data["clan_role"] = "leader"
    player.save()
    
    clans[clan_name] = {
        "leader_id": user_id,
        "leader_name": message.from_user.first_name,
        "members": [message.from_user.first_name],
        "treasury": 0,
        "created_at": datetime.now().isoformat()
    }
    save_json(DATA_FILES['clans'], clans)
    
    bot.send_message(message.chat.id, f"✅ Клан <b>{clan_name}</b> создан!")

@bot.message_handler(commands=['joinclan'])
def join_clan(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    if player.data["clan"]:
        bot.send_message(message.chat.id, "❌ Вы уже в клане!")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ /joinclan [название]")
        return
    
    clan_name = parts[1].strip()
    if clan_name not in clans:
        bot.send_message(message.chat.id, "❌ Клан не найден!")
        return
    
    player.data["clan"] = clan_name
    player.data["clan_role"] = "member"
    player.save()
    
    clans[clan_name]["members"].append(message.from_user.first_name)
    save_json(DATA_FILES['clans'], clans)
    
    bot.send_message(message.chat.id, f"✅ Вы вступили в клан <b>{clan_name}</b>!")

# ==================== РЫНОК ====================
@bot.callback_query_handler(func=lambda call: call.data == "trade_market")
def market_menu(call):
    if not market_listings:
        bot.edit_message_text("📦 На рынке нет активных предложений", 
                              call.message.chat.id, call.message.message_id)
        return
    
    text = "<b>💱 РЫНОК ИГРОКОВ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for listing_id, listing in list(market_listings.items())[:10]:
        item = items.get(listing["item_key"]) or limited_items.get(listing["item_key"])
        if item:
            text += f"📦 {item['name']} — {listing['price']}💰\n"
            text += f"   Продавец: {listing.get('seller_name', 'Нет')}\n\n"
            markup.add(types.InlineKeyboardButton(
                f"Купить: {item['name']}",
                callback_data=f"marketbuy_{listing_id}"
            ))
    
    markup.add(types.InlineKeyboardButton("📦 Создать лот", callback_data="market_create"))
    
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "market_create")
def market_create(call):
    bot.send_message(call.message.chat.id, 
        "📦 Для создания лота используйте команду:\n"
        "<code>/sell [ID предмета] [цена]</code>\n\n"
        "ID предмета можно узнать в инвентаре по команде /inventory")

@bot.message_handler(commands=['sell'])
def sell_item(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    try:
        parts = message.text.split()
        item_index = int(parts[1]) - 1
        price = int(parts[2])
    except:
        bot.send_message(message.chat.id, "❌ /sell [номер предмета] [цена]")
        return
    
    if item_index < 0 or item_index >= len(player.data["inventory"]):
        bot.send_message(message.chat.id, "❌ Неверный номер предмета!")
        return
    
    item_key = player.data["inventory"][item_index]
    item = items.get(item_key) or limited_items.get(item_key)
    
    if not item:
        bot.send_message(message.chat.id, "❌ Предмет не найден!")
        return
    
    player.data["inventory"].pop(item_index)
    player.save()
    
    listing_id = f"{user_id}_{int(time.time())}"
    market_listings[listing_id] = {
        "seller_id": user_id,
        "seller_name": message.from_user.first_name,
        "item_key": item_key,
        "price": price,
        "created_at": datetime.now().isoformat()
    }
    save_json(DATA_FILES['market'], market_listings)
    
    bot.send_message(message.chat.id, 
        f"✅ Предмет <b>{item['name']}</b> выставлен на рынок за <b>{price}💰</b>!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("marketbuy_"))
def market_buy(call):
    listing_id = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    if listing_id not in market_listings:
        bot.answer_callback_query(call.id, "❌ Лот уже продан!")
        return
    
    listing = market_listings[listing_id]
    
    if str(user_id) == str(listing["seller_id"]):
        bot.answer_callback_query(call.id, "❌ Нельзя купить свой предмет!")
        return
    
    if player.data["money"] < listing["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    # Покупка
    player.data["money"] -= listing["price"]
    player.data["inventory"].append(listing["item_key"])
    player.save()
    
    seller = Player(listing["seller_id"])
    seller.data["money"] += listing["price"]
    seller.save()
    
    del market_listings[listing_id]
    save_json(DATA_FILES['market'], market_listings)
    
    item = items.get(listing["item_key"], {})
    bot.answer_callback_query(call.id, f"✅ Куплено: {item.get('name', 'Предмет')}!")
    market_menu(call)

# ==================== ПОДЗЕМЕЛЬЯ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_dungeons")
def dungeons_menu(call):
    text = """
<b>🏰 ПОДЗЕМЕЛЬЯ</b>

<b>Доступные данжи:</b>
🐺 Логово волка (Ур. 1+)
🕷 Паучьи пещеры (Ур. 5+)
💀 Катакомбы (Ур. 10+)
🐉 Драконье логово (Ур. 15+)
👹 Бездна (Ур. 25+)

Каждый час можно проходить заново!
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🐺 Логово волка", callback_data="dungeon_1"),
        types.InlineKeyboardButton("🕷 Паучьи пещеры", callback_data="dungeon_2"),
        types.InlineKeyboardButton("💀 Катакомбы", callback_data="dungeon_3"),
        types.InlineKeyboardButton("🐉 Драконье логово", callback_data="dungeon_4"),
        types.InlineKeyboardButton("👹 Бездна", callback_data="dungeon_5")
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dungeon_"))
def start_dungeon(call):
    dungeon_level = int(call.data.split("_")[1])
    user_id = call.from_user.id
    player = Player(user_id)
    
    level_reqs = [1, 5, 10, 15, 25]
    if player.data["level"] < level_reqs[dungeon_level - 1]:
        bot.answer_callback_query(call.id, f"❌ Нужен {level_reqs[dungeon_level-1]} уровень!")
        return
    
    if player.data.get("last_dungeon"):
        last = datetime.fromisoformat(player.data["last_dungeon"])
        if (datetime.now() - last) < timedelta(hours=1):
            remaining = timedelta(hours=1) - (datetime.now() - last)
            bot.answer_callback_query(call.id, f"⏰ Подождите {remaining.seconds//60} мин.")
            return
    
    boss_names = ["Вожак стаи", "Королева пауков", "Некромант", "Древний дракон", "Владыка бездны"]
    reward = random.randint(50, 200) * dungeon_level * player.data["level"]
    exp = 50 * dungeon_level * player.data["level"]
    
    # Шанс на предмет
    got_item = None
    if random.random() < 0.1 + dungeon_level * 0.05:
        possible = [k for k, v in items.items() if v.get("level_req", 1) <= player.data["level"] 
                   and v.get("rarity") in ["rare", "epic", "legendary", "mythic"][:dungeon_level]]
        if possible:
            got_item = random.choice(possible)
            player.data["inventory"].append(got_item)
    
    player.data["money"] += reward
    player.data["exp"] += exp
    player.data["total_exp"] += exp
    player.data["last_dungeon"] = datetime.now().isoformat()
    
    old_level = player.data["level"]
    check_level_up(player)
    player.save()
    
    result = f"""
<b>🏰 ДАНЖ ПРОЙДЕН!</b>

Босс: <b>{boss_names[dungeon_level-1]}</b>
💰 Награда: <b>+{reward} монет</b>
✨ Опыт: <b>+{exp}</b>
"""
    if got_item:
        item = items[got_item]
        result += f"\n🎁 Найден предмет: <b>{item['name']}</b>!"
    if player.data["level"] > old_level:
        result += f"\n🎉 УРОВЕНЬ <b>{player.data['level']}</b>!"
    
    bot.edit_message_text(result, call.message.chat.id, call.message.message_id)

# ==================== СОБЫТИЯ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_events")
def events_menu(call):
    if not events:
        # Генерация события
        events["current"] = {
            "name": "Нашествие монстров",
            "description": "Убейте 5 монстров в дуэлях и получите награду!",
            "target": 5,
            "progress": defaultdict(int),
            "reward": 1000,
            "expires": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        save_json(DATA_FILES['events'], events)
    
    ev = events.get("current", {})
    user_id = call.from_user.id
    
    text = f"""
<b>🌍 ГЛОБАЛЬНОЕ СОБЫТИЕ</b>

<b>{ev.get('name', 'Событие')}</b>
📝 {ev.get('description', '')}

🎁 Награда: <b>{ev.get('reward', 0)}💰</b>
⏰ До: {ev.get('expires', 'Скоро')}

Ваш прогресс: {ev.get('progress', {}).get(str(user_id), 0)}/{ev.get('target', 5)}
"""
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

# ==================== КВЕСТЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "hero_quests")
def quests_menu(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    # Генерация квестов
    today = datetime.now().strftime("%Y-%m-%d")
    if "quests_date" not in player.data or player.data["quests_date"] != today:
        player.data["active_quests"] = {
            "daily_duels": {"name": "Ежедневные дуэли", "target": 3, "progress": 0, "reward": 300},
            "daily_wins": {"name": "Победитель", "target": 2, "progress": 0, "reward": 400},
            "daily_dungeons": {"name": "Исследователь", "target": 1, "progress": 0, "reward": 500}
        }
        player.data["quests_date"] = today
        player.save()
    
    text = f"<b>📜 КВЕСТЫ ({today})</b>\n\n"
    for qid, quest in player.data["active_quests"].items():
        prog = quest["progress"]
        target = quest["target"]
        pct = "█" * int(prog / target * 10) if target > 0 else "█" * 10
        empty = "░" * (10 - len(pct))
        text += f"<b>{quest['name']}</b>\n[{pct}{empty}] {prog}/{target}\n"
        text += f"Награда: {quest['reward']}💰\n\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

# ==================== ДОСТИЖЕНИЯ ====================
ACHIEVEMENTS_DB = {
    "first_win": {"name": "🩸 Первая кровь", "desc": "Выиграть первую дуэль", "reward": 200},
    "ten_wins": {"name": "⚔ Воин", "desc": "10 побед", "reward": 500},
    "fifty_wins": {"name": "🎖 Ветеран", "desc": "50 побед", "reward": 2000},
    "hundred_wins": {"name": "👑 Легенда", "desc": "100 побед", "reward": 5000},
    "rich": {"name": "💰 Богач", "desc": "10000 монет", "reward": 1000},
    "dungeon_master": {"name": "🏰 Мастер данжей", "desc": "10 данжей", "reward": 1500},
    "collector": {"name": "🎒 Коллекционер", "desc": "20 предметов", "reward": 1000}
}

@bot.callback_query_handler(func=lambda call: call.data == "hero_achievements")
def achievements_menu(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(player.data['achievements'])}/{len(ACHIEVEMENTS_DB)})\n\n"
    for aid, ach in ACHIEVEMENTS_DB.items():
        done = aid in player.data["achievements"]
        icon = "✅" if done else "🔒"
        text += f"{icon} <b>{ach['name']}</b>: {ach['desc']} (+{ach['reward']}💰)\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

# ==================== ТОП ИГРОКОВ ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_top")
def top_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⭐ По уровню", callback_data="top_level"),
        types.InlineKeyboardButton("⚔ По победам", callback_data="top_wins"),
        types.InlineKeyboardButton("💰 По монетам", callback_data="top_money"),
        types.InlineKeyboardButton("🏆 По рейтингу", callback_data="top_rating")
    )
    bot.edit_message_text("<b>📊 ТОП ИГРОКОВ</b>\nВыберите категорию:", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def show_top(call):
    category = call.data.split("_")[1]
    
    if category == "level":
        sorted_users = sorted(users.items(), key=lambda x: (x[1].get("level", 1), x[1].get("exp", 0)), reverse=True)[:10]
        title = "⭐ ТОП ПО УРОВНЮ"
    elif category == "wins":
        sorted_users = sorted(users.items(), key=lambda x: x[1].get("wins", 0), reverse=True)[:10]
        title = "⚔ ТОП ПО ПОБЕДАМ"
    elif category == "money":
        sorted_users = sorted(users.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]
        title = "💰 ТОП ПО МОНЕТАМ"
    elif category == "rating":
        sorted_users = sorted(users.items(), key=lambda x: x[1].get("pvp_rating", 1000), reverse=True)[:10]
        title = "🏆 ТОП ПО РЕЙТИНГУ"
    else:
        return
    
    medals = ["🥇", "🥈", "🥉"] + [f"{i}️⃣" for i in range(4, 11)]
    text = f"<b>{title}</b>\n\n"
    
    for i, (uid, data) in enumerate(sorted_users):
        if category == "level":
            value = f"Ур.{data.get('level', 1)}"
        elif category == "wins":
            value = f"{data.get('wins', 0)} побед"
        elif category == "money":
            value = f"{data.get('money', 0)}💰"
        else:
            value = f"Рейтинг: {data.get('pvp_rating', 1000)}"
        
        text += f"{medals[i]} {data.get('first_name', 'Игрок')}: {value}\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

# ==================== АДМИН ПАНЕЛЬ ====================
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
        types.InlineKeyboardButton("🔄 Сброс", callback_data="admin_reset")
    )
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>", reply_markup=markup)

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение правил"
        
        banned_users[str(target_id)] = {
            "reason": reason,
            "banned_at": datetime.now().isoformat(),
            "until": "permanent"
        }
        save_json(DATA_FILES['bans'], banned_users)
        
        bot.send_message(message.chat.id, f"⛔ Игрок {target_id} забанен!\nПричина: {reason}")
    except:
        bot.send_message(message.chat.id, "❌ /ban [ID] [причина]")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        target_id = str(int(message.text.split()[1]))
        if target_id in banned_users:
            del banned_users[target_id]
            save_json(DATA_FILES['bans'], banned_users)
            bot.send_message(message.chat.id, f"✅ Игрок {target_id} разбанен!")
        else:
            bot.send_message(message.chat.id, "❌ Игрок не в бане!")
    except:
        bot.send_message(message.chat.id, "❌ /unban [ID]")

@bot.message_handler(commands=['givemoney'])
def admin_give_money(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        amount = int(parts[2])
        
        target = Player(target_id)
        target.data["money"] += amount
        target.save()
        
        bot.send_message(message.chat.id, f"✅ Выдано {amount}💰 игроку {target_id}")
    except:
        bot.send_message(message.chat.id, "❌ /givemoney [ID] [сумма]")

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
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

@bot.callback_query_handler(func=lambda call: call.data == "cancel_action")
def cancel_action(call):
    bot.edit_message_text("❌ Действие отменено", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "trade_daily")
def daily_bonus(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player.data["last_daily"] == today:
        bot.answer_callback_query(call.id, "❌ Уже получен!")
        return
    
    bonus = random.randint(100, 500) + player.data["level"] * 10
    exp = random.randint(50, 200) + player.data["level"] * 5
    
    player.data["money"] += bonus
    player.data["exp"] += exp
    player.data["total_exp"] += exp
    player.data["last_daily"] = today
    
    old_level = player.data["level"]
    check_level_up(player)
    player.save()
    
    text = f"""
<b>🎁 ЕЖЕДНЕВНЫЙ БОНУС</b>

💰 +{bonus} монет
✨ +{exp} опыта
"""
    if player.data["level"] > old_level:
        text += f"\n🎉 УРОВЕНЬ {player.data['level']}!"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

# ==================== ЗАПУСК БОТА ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v5.0 — ПОЛНАЯ РЕАЛИЗАЦИЯ ⚔️")
    print("=" * 60)
    print(f"🕒 Запуск: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print(f"⚔ Предметов: {len(items)}")
    print(f"💎 Лимитированных: {len(limited_items)}")
    print(f"🛡 Кланов: {len(clans)}")
    print(f"🏟 Турниров: {len(tournaments)}")
    print(f"📦 Лотов на рынке: {len(market_listings)}")
    print("=" * 60)
    print("✅ ВСЕ СИСТЕМЫ АКТИВНЫ!")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
