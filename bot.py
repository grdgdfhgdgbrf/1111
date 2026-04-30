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

RARITY_MULTIPLIERS = {
    "common": 1.0, "uncommon": 1.5, "rare": 2.5,
    "epic": 4.0, "legendary": 7.0, "mythic": 12.0,
    "divine": 20.0, "apocalyptic": 35.0
}

ELEMENT_TYPES = ["🔥", "❄", "⚡", "🌊", "🌿", "🌑", "✨", "💀"]
STATUS_EFFECTS = ["burn", "freeze", "stun", "poison", "bleed", "curse", "bless", "shield"]

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
    'bans': 'bans.json'
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
WEAPONS = {
    "rusty_sword": {
        "name": "🗡 Ржавый меч", "damage": (3, 7), "price": 50, "type": "weapon",
        "rarity": "common", "level_req": 1, "element": None,
        "description": "Старый ржавый меч, но всё ещё острый",
        "effects": {}
    },
    "hunters_bow": {
        "name": "🏹 Лук охотника", "damage": (5, 10), "price": 150, "type": "weapon",
        "rarity": "common", "level_req": 3, "element": "🌿",
        "description": "Надёжный лук для охоты",
        "effects": {"bleed": 15}
    },
    "flame_blade": {
        "name": "🔥 Пламенный клинок", "damage": (8, 15), "price": 400, "type": "weapon",
        "rarity": "uncommon", "level_req": 7, "element": "🔥",
        "description": "Клинок, объятый пламенем",
        "effects": {"burn": 20}
    },
    "frost_axe": {
        "name": "❄ Ледяной топор", "damage": (10, 18), "price": 700, "type": "weapon",
        "rarity": "uncommon", "level_req": 10, "element": "❄",
        "description": "Замораживает противников",
        "effects": {"freeze": 15}
    },
    "storm_staff": {
        "name": "⚡ Посох бурь", "damage": (12, 22), "price": 1200, "type": "weapon",
        "rarity": "rare", "level_req": 14, "element": "⚡",
        "description": "Призывает молнии",
        "effects": {"stun": 10, "chain_damage": 0.3}
    },
    "tidal_blade": {
        "name": "🌊 Приливной клинок", "damage": (15, 25), "price": 2000, "type": "weapon",
        "rarity": "rare", "level_req": 18, "element": "🌊",
        "description": "Волны сокрушают врагов",
        "effects": {"knockback": 25, "heal_on_hit": 0.1}
    },
    "shadow_dagger": {
        "name": "🌑 Теневой кинжал", "damage": (18, 30), "price": 3500, "type": "weapon",
        "rarity": "epic", "level_req": 22, "element": "🌑",
        "description": "Атакует из тени",
        "effects": {"poison": 20, "crit_boost": 10}
    },
    "divine_spear": {
        "name": "✨ Божественное копьё", "damage": (22, 35), "price": 6000, "type": "weapon",
        "rarity": "legendary", "level_req": 28, "element": "✨",
        "description": "Оружие небесных воинов",
        "effects": {"bless": 20, "holy_damage": 0.25}
    },
    "death_scythe": {
        "name": "💀 Коса смерти", "damage": (25, 45), "price": 10000, "type": "weapon",
        "rarity": "mythic", "level_req": 35, "element": "💀",
        "description": "Забирает души врагов",
        "effects": {"curse": 25, "life_steal": 0.2, "execution": 0.1}
    },
    "thunder_hammer": {
        "name": "⚡ Громовой молот", "damage": (20, 40), "price": 8000, "type": "weapon",
        "rarity": "legendary", "level_req": 32, "element": "⚡",
        "description": "Молот громовержца",
        "effects": {"stun": 20, "shock": 15, "area_damage": 0.4}
    }
}

SHIELDS = {
    "wooden_shield": {
        "name": "🛡 Деревянный щит", "defense": 5, "block_chance": 10,
        "price": 100, "type": "shield", "rarity": "common", "level_req": 1,
        "description": "Простой деревянный щит",
        "effects": {}
    },
    "iron_shield": {
        "name": "🛡 Железный щит", "defense": 10, "block_chance": 15,
        "price": 350, "type": "shield", "rarity": "uncommon", "level_req": 6,
        "description": "Прочный железный щит",
        "effects": {"counter_attack": 10}
    },
    "mirror_shield": {
        "name": "🪞 Зеркальный щит", "defense": 15, "block_chance": 20,
        "price": 900, "type": "shield", "rarity": "rare", "level_req": 12,
        "description": "Отражает магию",
        "effects": {"reflect_magic": 20, "magic_defense": 10}
    },
    "dragon_scale_shield": {
        "name": "🐉 Щит драконьей чешуи", "defense": 22, "block_chance": 25,
        "price": 2500, "type": "shield", "rarity": "epic", "level_req": 20,
        "description": "Чешуя древнего дракона",
        "effects": {"fire_resist": 30, "thorns": 15}
    },
    "aegis_divine": {
        "name": "💫 Божественная эгида", "defense": 35, "block_chance": 35,
        "price": 8000, "type": "shield", "rarity": "legendary", "level_req": 30,
        "description": "Щит самой Афины",
        "effects": {"divine_protection": 25, "heal_block": 0.15}
    },
    "void_barrier": {
        "name": "🕳 Барьер пустоты", "defense": 45, "block_chance": 40,
        "price": 15000, "type": "shield", "rarity": "mythic", "level_req": 38,
        "description": "Поглощает саму реальность",
        "effects": {"void_absorption": 30, "damage_to_mana": 0.2}
    }
}

ARMORS = {
    "leather_vest": {
        "name": "🧥 Кожаный жилет", "defense": 3, "hp_bonus": 15,
        "price": 80, "type": "armor", "rarity": "common", "level_req": 1,
        "description": "Лёгкая защита",
        "effects": {}
    },
    "chainmail": {
        "name": "⛓ Кольчуга", "defense": 8, "hp_bonus": 35,
        "price": 400, "type": "armor", "rarity": "uncommon", "level_req": 8,
        "description": "Надёжная кольчуга",
        "effects": {"physical_resist": 10}
    },
    "plate_armor": {
        "name": "🛡 Латный доспех", "defense": 15, "hp_bonus": 60,
        "price": 1200, "type": "armor", "rarity": "rare", "level_req": 15,
        "description": "Тяжёлые латы",
        "effects": {"damage_reduction": 5}
    },
    "shadow_armor": {
        "name": "🌑 Теневая броня", "defense": 20, "hp_bonus": 80,
        "price": 3000, "type": "armor", "rarity": "epic", "level_req": 22,
        "description": "Скрывает в тенях",
        "effects": {"dodge_boost": 10, "shadow_step": 15}
    },
    "phoenix_armor": {
        "name": "🦅 Броня феникса", "defense": 30, "hp_bonus": 150,
        "price": 7000, "type": "armor", "rarity": "legendary", "level_req": 30,
        "description": "Возрождает из пепла",
        "effects": {"rebirth": 1, "fire_heal": 20}
    },
    "titan_armor": {
        "name": "🏛 Броня титана", "defense": 45, "hp_bonus": 250,
        "price": 20000, "type": "armor", "rarity": "mythic", "level_req": 40,
        "description": "Сила древних титанов",
        "effects": {"unstoppable": 20, "super_armor": 15}
    }
}

ACCESSORIES = {
    "strength_ring": {
        "name": "💍 Кольцо силы", "bonus": "damage", "value": 5,
        "price": 600, "type": "accessory", "rarity": "uncommon", "level_req": 5,
        "description": "+5 к минимальному урону",
        "effects": {"min_damage_boost": 5}
    },
    "crit_amulet": {
        "name": "📿 Амулет крита", "bonus": "crit", "value": 10,
        "price": 1500, "type": "accessory", "rarity": "rare", "level_req": 15,
        "description": "+10% к шансу крита",
        "effects": {"crit_chance_boost": 10}
    },
    "lucky_charm": {
        "name": "🍀 Талисман удачи", "bonus": "luck", "value": 15,
        "price": 2500, "type": "accessory", "rarity": "epic", "level_req": 20,
        "description": "Увеличивает удачу во всём",
        "effects": {"luck_boost": 15, "drop_rate": 10}
    },
    "berserker_ring": {
        "name": "💢 Кольцо берсерка", "bonus": "berserk", "value": 20,
        "price": 4000, "type": "accessory", "rarity": "epic", "level_req": 25,
        "description": "Ярость в бою",
        "effects": {"low_hp_damage_boost": 30, "berserk_mode": 15}
    },
    "philosophers_stone": {
        "name": "🧿 Философский камень", "bonus": "all", "value": 10,
        "price": 12000, "type": "accessory", "rarity": "legendary", "level_req": 35,
        "description": "Усиливает все характеристики",
        "effects": {"all_stats_boost": 10, "exp_boost": 20}
    }
}

POTIONS = {
    "health_potion": {
        "name": "🧪 Зелье здоровья", "heal": 30, "price": 40,
        "type": "potion", "rarity": "common", "level_req": 1,
        "description": "Восстанавливает 30 HP",
        "effects": {"instant_heal": 30}
    },
    "big_health_potion": {
        "name": "🧪 Большое зелье", "heal": 75, "price": 120,
        "type": "potion", "rarity": "uncommon", "level_req": 8,
        "description": "Восстанавливает 75 HP",
        "effects": {"instant_heal": 75}
    },
    "elixir_of_life": {
        "name": "💊 Эликсир жизни", "heal": 150, "price": 350,
        "type": "potion", "rarity": "rare", "level_req": 15,
        "description": "Полное восстановление",
        "effects": {"full_heal": True, "cleanse": True}
    },
    "berserk_potion": {
        "name": "💢 Зелье ярости", "heal": 0, "price": 200,
        "type": "potion", "rarity": "rare", "level_req": 12,
        "description": "Удваивает урон на 3 хода",
        "effects": {"damage_boost": 100, "duration": 3}
    },
    "invisibility_potion": {
        "name": "👻 Зелье невидимости", "heal": 0, "price": 500,
        "type": "potion", "rarity": "epic", "level_req": 20,
        "description": "Уклонение от атак",
        "effects": {"dodge_boost": 50, "duration": 2}
    }
}

BOOTS = {
    "leather_boots": {
        "name": "👢 Кожаные сапоги", "speed": 5, "price": 150,
        "type": "boots", "rarity": "common", "level_req": 1,
        "description": "+5 к скорости",
        "effects": {"speed_boost": 5}
    },
    "wind_boots": {
        "name": "🌪 Сапоги ветра", "speed": 12, "price": 800,
        "type": "boots", "rarity": "rare", "level_req": 12,
        "description": "+12 к скорости",
        "effects": {"speed_boost": 12, "dodge_boost": 5}
    },
    "blink_boots": {
        "name": "✨ Сапоги телепортации", "speed": 20, "price": 3500,
        "type": "boots", "rarity": "epic", "level_req": 25,
        "description": "Мгновенное перемещение",
        "effects": {"speed_boost": 20, "blink_chance": 15}
    },
    "hermes_boots": {
        "name": "👟 Сандалии Гермеса", "speed": 35, "price": 10000,
        "type": "boots", "rarity": "legendary", "level_req": 35,
        "description": "Скорость бога",
        "effects": {"speed_boost": 35, "first_strike": True, "double_turn": 20}
    }
}

# Лимитированные предметы
LIMITED_ITEMS = {
    "thunderfury": {
        "name": "⚡ Ярость грома", "damage": (50, 80), "total": 3,
        "remaining": 3, "price": 50000, "type": "weapon",
        "rarity": "divine", "element": "⚡",
        "description": "Меч бога грома. Уничтожает всё на своём пути",
        "effects": {"chain_lightning": 0.5, "stun": 30, "thunderstorm": 20}
    },
    "apocalypse": {
        "name": "🌋 Апокалипсис", "damage": (70, 120), "total": 1,
        "remaining": 1, "price": 100000, "type": "weapon",
        "rarity": "apocalyptic", "element": "💀",
        "description": "Единственный в мире. Конец всего сущего",
        "effects": {"armageddon": 40, "soul_drain": 0.3, "obliterate": 25}
    },
    "immortal_shield": {
        "name": "✨ Щит бессмертия", "defense": 100, "total": 2,
        "remaining": 2, "price": 75000, "type": "shield",
        "rarity": "divine",
        "description": "Делает владельца неуязвимым на 2 хода",
        "effects": {"invincibility": 2, "full_block": 50, "hp_regen": 0.1}
    },
    "cloak_of_infinity": {
        "name": "🌀 Плащ бесконечности", "defense": 60, "hp_bonus": 500,
        "total": 4, "remaining": 4, "price": 60000, "type": "armor",
        "rarity": "divine",
        "description": "Бесконечная защита космоса",
        "effects": {"infinity_guard": 30, "cosmic_power": 25, "black_hole": 15}
    }
}

# Объединение всех предметов
ALL_ITEMS = {}
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(SHIELDS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(ACCESSORIES)
ALL_ITEMS.update(POTIONS)
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

# ==================== КЛАСС ПОЛЬЗОВАТЕЛЯ ====================
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
                "total_damage_dealt": 0,
                "total_damage_taken": 0,
                "critical_hits_landed": 0,
                "duels_by_type": defaultdict(int),
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
                "active_effects": [],
                "clan": None,
                "clan_role": None,
                "tournament_wins": 0,
                "registration_date": datetime.now().isoformat(),
                "premium_until": None,
                "settings": {
                    "notifications": True,
                    "duel_requests": True,
                    "show_battle_log": True,
                    "auto_equip": False
                },
                "pvp_rating": 1000,
                "kda": 0.0,
                "favorite_weapon": None,
                "battle_history": []
            }
            self.save()
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    def save(self):
        save_json(DATA_FILES['users'], users)
    
    def get_equipment_stats(self):
        """Расчёт характеристик от экипировки"""
        stats = {
            "min_damage": 0,
            "max_damage": 0,
            "defense": 0,
            "hp_bonus": 0,
            "mana_bonus": 0,
            "speed": 0,
            "crit_chance": 5,
            "crit_multiplier": 1.5,
            "dodge_chance": 3,
            "block_chance": 0,
            "life_steal": 0,
            "damage_reflect": 0,
            "elemental_bonus": {},
            "status_effects": [],
            "special_effects": []
        }
        
        for slot, item_key in self.data["equipment"].items():
            if not item_key:
                continue
            
            item = items.get(item_key) or limited_items.get(item_key)
            if not item:
                continue
            
            if item["type"] == "weapon":
                if "damage" in item:
                    min_d, max_d = item["damage"]
                    stats["min_damage"] += min_d
                    stats["max_damage"] += max_d
                if "element" in item and item["element"]:
                    stats["elemental_bonus"][item["element"]] = stats["elemental_bonus"].get(item["element"], 0) + 20
            
            elif item["type"] == "shield":
                stats["defense"] += item.get("defense", 0)
                stats["block_chance"] += item.get("block_chance", 0)
            
            elif item["type"] == "armor":
                stats["defense"] += item.get("defense", 0)
                stats["hp_bonus"] += item.get("hp_bonus", 0)
            
            elif item["type"] == "accessory":
                for effect, value in item.get("effects", {}).items():
                    if "crit" in effect:
                        stats["crit_chance"] += value
                    elif "damage" in effect:
                        stats["min_damage"] += value
                        stats["max_damage"] += value
            
            elif item["type"] == "boots":
                stats["speed"] += item.get("speed", 0)
                for effect, value in item.get("effects", {}).items():
                    if "dodge" in effect:
                        stats["dodge_chance"] += value
            
            # Особые эффекты
            for effect, value in item.get("effects", {}).items():
                if effect in ["life_steal", "damage_reflect"]:
                    stats[effect] += value
                elif isinstance(value, bool) and value:
                    stats["special_effects"].append(effect)
        
        # Базовые статы от силы и ловкости
        stats["min_damage"] += self.data["stats"]["strength"] * 2
        stats["max_damage"] += self.data["stats"]["strength"] * 3
        stats["speed"] += self.data["stats"]["agility"]
        stats["crit_chance"] += self.data["stats"]["luck"] * 0.5
        
        # Ограничения
        stats["crit_chance"] = min(stats["crit_chance"], 80)
        stats["dodge_chance"] = min(stats["dodge_chance"], 50)
        stats["block_chance"] = min(stats["block_chance"], 60)
        
        return stats

# ==================== СЛОЖНАЯ БОЕВАЯ СИСТЕМА ====================
class BattleSystem:
    def __init__(self, player1_id, player2_id, bet=0, duel_type="normal"):
        self.p1_id = str(player1_id)
        self.p2_id = str(player2_id)
        self.bet = bet
        self.duel_type = duel_type
        self.turn = 1
        self.max_turns = 50
        
        # Инициализация игроков
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        # Получение характеристик
        self.p1_stats = self.p1.get_equipment_stats()
        self.p2_stats = self.p2.get_equipment_stats()
        
        # Здоровье и мана
        self.p1_hp = self.p1.data["max_hp"] + self.p1_stats["hp_bonus"]
        self.p2_hp = self.p2.data["max_hp"] + self.p2_stats["hp_bonus"]
        self.p1_max_hp = self.p1_hp
        self.p2_max_hp = self.p2_hp
        
        self.p1_mana = self.p1.data["max_mana"] + self.p1_stats["mana_bonus"]
        self.p2_mana = self.p2.data["max_mana"] + self.p2_stats["mana_bonus"]
        
        # Эффекты
        self.p1_effects = []
        self.p2_effects = []
        
        # Определение очерёдности
        self.p1_speed = self.p1_stats["speed"] + random.randint(-5, 5)
        self.p2_speed = self.p2_stats["speed"] + random.randint(-5, 5)
        
        if self.p1_speed >= self.p2_speed:
            self.first_player = 1
            self.second_player = 2
        else:
            self.first_player = 2
            self.second_player = 1
        
        # История боя
        self.battle_log = []
        self.turn_count = 0
        
        # Боевые модификаторы
        self.weather = random.choice(["clear", "rain", "storm", "fog", "eclipse"])
        self.arena = random.choice(["colosseum", "forest", "volcano", "tundra", "void"])
        
        self.battle_log.append(f"⚔ <b>НАЧАЛО БИТВЫ!</b>")
        self.battle_log.append(f"🌍 Арена: <b>{self.arena}</b>")
        self.battle_log.append(f"🌤 Погода: <b>{self.weather}</b>")
        self.battle_log.append(f"⚡ Первый ход: <b>{self._get_player_name(self.first_player)}</b>")
    
    def _get_player_name(self, player_num):
        if player_num == 1:
            return self.p1.data["first_name"]
        return self.p2.data["first_name"]
    
    def _get_hp(self, player_num):
        return self.p1_hp if player_num == 1 else self.p2_hp
    
    def _set_hp(self, player_num, value):
        if player_num == 1:
            self.p1_hp = max(0, min(self.p1_max_hp, value))
        else:
            self.p2_hp = max(0, min(self.p2_max_hp, value))
    
    def _get_max_hp(self, player_num):
        return self.p1_max_hp if player_num == 1 else self.p2_max_hp
    
    def calculate_damage(self, attacker_num, defender_num):
        """Сложный расчёт урона"""
        attacker_stats = self.p1_stats if attacker_num == 1 else self.p2_stats
        defender_stats = self.p2_stats if defender_num == 1 else self.p1_stats
        
        attacker_player = self.p1 if attacker_num == 1 else self.p2
        
        # Базовый урон
        min_dmg = attacker_stats["min_damage"] + attacker_player.data["stats"]["strength"]
        max_dmg = attacker_stats["max_damage"] + attacker_player.data["stats"]["strength"] * 2
        base_damage = random.randint(int(min_dmg), int(max_dmg))
        
        # Модификатор уровня
        level_mod = 1 + (attacker_player.data["level"] - self._get_opponent_level(attacker_num)) * 0.02
        base_damage *= max(0.7, min(1.3, level_mod))
        
        # Критический удар
        is_crit = random.random() * 100 < attacker_stats["crit_chance"]
        if is_crit:
            base_damage *= attacker_stats["crit_multiplier"]
            attacker_player.data["critical_hits_landed"] += 1
        
        # Элементальный бонус
        if attacker_stats["elemental_bonus"]:
            element = random.choice(list(attacker_stats["elemental_bonus"].keys()))
            element_bonus = attacker_stats["elemental_bonus"][element]
            base_damage *= (1 + element_bonus / 100)
        
        # Погодные эффекты
        if self.weather == "storm":
            if random.random() < 0.2:
                base_damage += random.randint(10, 30)
                self.battle_log.append("⛈ Буря усиливает атаку!")
        elif self.weather == "rain":
            if "🔥" in str(attacker_stats.get("elemental_bonus", {})):
                base_damage *= 0.7
                self.battle_log.append("🌧 Дождь ослабляет огонь")
        
        # Эффекты арены
        if self.arena == "volcano":
            base_damage *= 1.1
        elif self.arena == "void":
            if random.random() < 0.15:
                base_damage *= 1.5
                self.battle_log.append("🕳 Пустота усиливает урон!")
        
        # Защита
        defense = defender_stats["defense"]
        damage_reduction = defense / (defense + 100)
        base_damage *= (1 - damage_reduction)
        
        # Блокирование
        block_chance = defender_stats["block_chance"]
        if random.random() * 100 < block_chance:
            base_damage *= 0.5
            self.battle_log.append(f"🛡 {self._get_player_name(defender_num)} блокирует часть урона!")
        
        # Уклонение
        dodge_chance = defender_stats["dodge_chance"]
        if random.random() * 100 < dodge_chance:
            self.battle_log.append(f"💨 {self._get_player_name(defender_num)} уклоняется!")
            return 0, False, []
        
        # Вампиризм
        lifesteal = attacker_stats["life_steal"]
        if lifesteal > 0:
            heal = int(base_damage * lifesteal)
            self._set_hp(attacker_num, self._get_hp(attacker_num) + heal)
            if heal > 0:
                self.battle_log.append(f"💚 Вампиризм +{heal} HP")
        
        # Отражение урона
        reflect = defender_stats["damage_reflect"]
        if reflect > 0:
            reflected = int(base_damage * reflect)
            self._set_hp(attacker_num, self._get_hp(attacker_num) - reflected)
            self.battle_log.append(f"🔄 Отражено {reflected} урона!")
        
        # Статусные эффекты
        status_effects = []
        for effect in attacker_stats.get("status_effects", []):
            if random.random() < 0.2:  # 20% шанс наложения
                status_effects.append(effect)
                self.battle_log.append(f"✨ Наложен эффект: {effect}")
        
        final_damage = int(base_damage)
        final_damage = max(1, final_damage)  # Минимальный урон 1
        
        return final_damage, is_crit, status_effects
    
    def _get_opponent_level(self, player_num):
        if player_num == 1:
            return self.p2.data["level"]
        return self.p1.data["level"]
    
    def execute_turn(self):
        """Выполнение одного хода битвы"""
        if self.turn % 2 == 1:
            attacker = self.first_player
            defender = self.second_player
        else:
            attacker = self.second_player
            defender = self.first_player
        
        self.turn_count += 1
        self.battle_log.append(f"\n<b>Ход {self.turn_count}</b>")
        
        # Обработка активных эффектов
        self._process_effects(attacker)
        self._process_effects(defender)
        
        # Нанесение урона
        damage, is_crit, effects = self.calculate_damage(attacker, defender)
        
        crit_text = "💥 <b>КРИТИЧЕСКИЙ УДАР!</b> " if is_crit else ""
        self.battle_log.append(f"{crit_text}⚔ {self._get_player_name(attacker)} наносит {damage} урона")
        
        # Применение урона
        self._set_hp(defender, self._get_hp(defender) - damage)
        
        # Применение эффектов
        if attacker == 1:
            self.p2_effects.extend(effects)
        else:
            self.p1_effects.extend(effects)
        
        # Проверка на смерть
        if self._get_hp(defender) <= 0:
            return defender  # Проигравший
        
        # Отображение HP
        hp_bar1 = self._get_hp_bar(1)
        hp_bar2 = self._get_hp_bar(2)
        
        self.battle_log.append(
            f"❤ {self._get_player_name(1)}: {hp_bar1} {self._get_hp(1)}/{self._get_max_hp(1)}"
        )
        self.battle_log.append(
            f"❤ {self._get_player_name(2)}: {hp_bar2} {self._get_hp(2)}/{self._get_max_hp(2)}"
        )
        
        self.turn += 1
        
        if self.turn_count >= self.max_turns:
            return 0  # Ничья по превышению ходов
        
        return None  # Бой продолжается
    
    def _process_effects(self, player_num):
        """Обработка эффектов игрока"""
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        
        for effect in effects[:]:
            if effect == "burn":
                damage = random.randint(5, 15)
                self._set_hp(player_num, self._get_hp(player_num) - damage)
                self.battle_log.append(f"🔥 Горение наносит {damage} урона")
                if random.random() < 0.3:
                    effects.remove(effect)
            
            elif effect == "freeze":
                if random.random() < 0.3:
                    effects.remove(effect)
                    self.battle_log.append("❄ Заморозка спадает")
                else:
                    self.battle_log.append("❄ Игрок заморожен!")
                    self.turn += 1  # Пропуск хода
            
            elif effect == "poison":
                damage = random.randint(8, 18)
                self._set_hp(player_num, self._get_hp(player_num) - damage)
                self.battle_log.append(f"☠ Яд наносит {damage} урона")
                if random.random() < 0.2:
                    effects.remove(effect)
            
            elif effect == "bless":
                heal = random.randint(10, 25)
                self._set_hp(player_num, self._get_hp(player_num) + heal)
                self.battle_log.append(f"✨ Благословение +{heal} HP")
                if random.random() < 0.3:
                    effects.remove(effect)
    
    def _get_hp_bar(self, player_num):
        hp = self._get_hp(player_num)
        max_hp = self._get_max_hp(player_num)
        percentage = hp / max_hp
        filled = int(percentage * 10)
        empty = 10 - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    def execute_full_battle(self):
        """Полное выполнение битвы"""
        result = None
        
        while result is None:
            result = self.execute_turn()
        
        # Определение победителя
        if result == 0:
            winner = None
            loser = None
            result_type = "draw"
        elif result == 1:
            winner = self.p2_id
            loser = self.p1_id
            result_type = "win"
        else:
            winner = self.p1_id
            loser = self.p2_id
            result_type = "win"
        
        return {
            "winner_id": winner,
            "loser_id": loser,
            "result": result_type,
            "turns": self.turn_count,
            "battle_log": self.battle_log,
            "final_hp": {
                "p1": self.p1_hp,
                "p2": self.p2_hp
            }
        }

# ==================== ГЛАВНОЕ МЕНЮ (4 кнопки) ====================
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("⚔️ Дуэли"),
        types.KeyboardButton("👤 Герой"),
        types.KeyboardButton("🏪 Торговля"),
        types.KeyboardButton("🌍 Мир")
    )
    return markup

def get_duel_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("⚡ Быстрая дуэль"),
        types.KeyboardButton("👥 PvP дуэль"),
        types.KeyboardButton("🏆 Рейтинговая"),
        types.KeyboardButton("💀 Хардкор"),
        types.KeyboardButton("◀️ Назад")
    )
    return markup

def get_hero_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📊 Статистика"),
        types.KeyboardButton("🎒 Инвентарь"),
        types.KeyboardButton("⚡ Характеристики"),
        types.KeyboardButton("🏅 Достижения"),
        types.KeyboardButton("◀️ Назад")
    )
    return markup

def get_trade_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 Магазин"),
        types.KeyboardButton("💎 Редкости"),
        types.KeyboardButton("🎁 Бонус"),
        types.KeyboardButton("💱 Обмен"),
        types.KeyboardButton("◀️ Назад")
    )
    return markup

def get_world_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🏰 Данжи"),
        types.KeyboardButton("🛡 Кланы"),
        types.KeyboardButton("🏟 Турниры"),
        types.KeyboardButton("📜 Квесты"),
        types.KeyboardButton("◀️ Назад")
    )
    return markup

# ==================== ОБРАБОТЧИКИ МЕНЮ ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    # Проверка бана
    if str(user_id) in banned_users:
        ban_data = banned_users[str(user_id)]
        bot.send_message(message.chat.id, 
            f"⛔ Вы забанены!\nПричина: {ban_data.get('reason', 'Не указана')}\n"
            f"До: {ban_data.get('until', 'Навсегда')}")
        return
    
    username = message.from_user.username or f"user_{user_id}"
    first_name = message.from_user.first_name or "Игрок"
    
    player = Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v4.0 ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

🎯 <b>Эпическая боевая система:</b>
• Сложная механика боёв
• Элементы и статус-эффекты
• Погода и арены влияют на бой!
• 50+ видов оружия и брони
• Лимитированные артефакты

💰 Стартовый бонус: <b>500 монет</b>
📊 Рейтинговая система
🏰 Подземелья и боссы
🛡 Клановая система

<i>Выбирай раздел в меню:</i>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "◀️ Назад")
def back_to_main(message):
    bot.send_message(message.chat.id, "🔙 Главное меню", reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    duel_text = """
<b>⚔️ РАЗДЕЛ ДУЭЛЕЙ</b>

<b>⚡ Быстрая дуэль</b> - против бота
<b>👥 PvP дуэль</b> - против игрока (выбор ставки)
<b>🏆 Рейтинговая</b> - за рейтинг и награды
<b>💀 Хардкор</b> - высокие ставки и риски

<i>Сложная боевая система:</i>
• Критические удары и уклонения
• Элементальные атаки
• Статус-эффекты (горение, яд, заморозка)
• Погодные условия на арене
"""
    bot.send_message(message.chat.id, duel_text, reply_markup=get_duel_menu())

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_section(message):
    bot.send_message(message.chat.id, "👤 Раздел персонажа", reply_markup=get_hero_menu())

@bot.message_handler(func=lambda m: m.text == "🏪 Торговля")
def trade_section(message):
    bot.send_message(message.chat.id, "🏪 Раздел торговли", reply_markup=get_trade_menu())

@bot.message_handler(func=lambda m: m.text == "🌍 Мир")
def world_section(message):
    bot.send_message(message.chat.id, "🌍 Игровой мир", reply_markup=get_world_menu())

# ==================== СИСТЕМА ДУЭЛЕЙ ====================
@bot.message_handler(func=lambda m: m.text == "⚡ Быстрая дуэль")
def quick_duel_start(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("50💰", callback_data="quickduel_50"),
        types.InlineKeyboardButton("100💰", callback_data="quickduel_100"),
        types.InlineKeyboardButton("200💰", callback_data="quickduel_200"),
        types.InlineKeyboardButton("500💰", callback_data="quickduel_500"),
        types.InlineKeyboardButton("1000💰", callback_data="quickduel_1000"),
        types.InlineKeyboardButton("Отмена", callback_data="cancel_duel")
    )
    
    bot.send_message(message.chat.id, 
        "<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n\n"
        "Выберите ставку:\n"
        f"Ваш баланс: <b>{player.data['money']}💰</b>",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("quickduel_"))
def handle_quick_duel(call):
    user_id = call.from_user.id
    player = Player(user_id)
    bet = int(call.data.split("_")[1])
    
    if player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Недостаточно монет! Нужно {bet}💰")
        return
    
    player.data["money"] -= bet
    player.save()
    
    # Создание противника-бота
    bot_level = random.randint(max(1, player.data["level"] - 5), player.data["level"] + 5)
    bot_id = f"bot_{random.randint(10000, 99999)}"
    
    # Генерация бота с предметами
    bot_equipment = {}
    for slot in ["weapon", "shield", "armor", "accessory", "boots"]:
        slot_items = [k for k, v in items.items() if v["type"] == slot 
                     and v.get("level_req", 1) <= bot_level]
        if slot_items and random.random() < 0.7:
            bot_equipment[slot] = random.choice(slot_items)
    
    users[bot_id] = {
        "username": f"Bot_{bot_level}",
        "first_name": f"⚔ Бот Lv.{bot_level}",
        "money": 0,
        "level": bot_level,
        "exp": 0,
        "total_exp": bot_level * 100,
        "hp": 100 + bot_level * 10,
        "max_hp": 100 + bot_level * 10,
        "mana": 50 + bot_level * 5,
        "max_mana": 50 + bot_level * 5,
        "stats": {
            "strength": 5 + bot_level,
            "agility": 5 + bot_level // 2,
            "intelligence": 5 + bot_level // 3,
            "vitality": 5 + bot_level // 2,
            "luck": 3 + bot_level // 4
        },
        "stat_points": 0,
        "wins": 0, "losses": 0, "draws": 0,
        "win_streak": 0, "best_streak": 0,
        "total_duels": 0,
        "total_damage_dealt": 0,
        "total_damage_taken": 0,
        "critical_hits_landed": 0,
        "duels_by_type": {},
        "inventory": [],
        "equipment": bot_equipment,
        "last_daily": None,
        "last_dungeon": None,
        "title": "Бот",
        "titles_collected": ["Бот"],
        "achievements": [],
        "active_effects": [],
        "clan": None,
        "clan_role": None,
        "tournament_wins": 0,
        "registration_date": datetime.now().isoformat(),
        "premium_until": None,
        "settings": {},
        "pvp_rating": 1000 + bot_level * 10,
        "kda": 0.0,
        "favorite_weapon": None,
        "battle_history": []
    }
    
    # Запуск битвы
    battle = BattleSystem(user_id, bot_id, bet, "quick")
    result = battle.execute_full_battle()
    
    # Очистка бота
    if bot_id in users:
        del users[bot_id]
    save_json(DATA_FILES['users'], users)
    
    # Обработка результатов
    player = Player(user_id)
    
    if result["winner_id"] == str(user_id):
        reward = bet * 2
        player.data["money"] += reward
        player.data["wins"] += 1
        player.data["win_streak"] += 1
        player.data["total_duels"] += 1
        player.data["total_damage_dealt"] += (100 - result["final_hp"]["p2"])
        player.data["total_damage_taken"] += (100 - result["final_hp"]["p1"])
        
        if player.data["win_streak"] > player.data["best_streak"]:
            player.data["best_streak"] = player.data["win_streak"]
        
        exp_gain = bet // 2 + result["turns"] * 5
        player.data["exp"] += exp_gain
        player.data["total_exp"] += exp_gain
        
        result_text = f"<b>🏆 ПОБЕДА!</b>\n\n"
    else:
        player.data["losses"] += 1
        player.data["win_streak"] = 0
        player.data["total_duels"] += 1
        
        exp_gain = bet // 4 + result["turns"] * 2
        player.data["exp"] += exp_gain
        player.data["total_exp"] += exp_gain
        
        result_text = f"<b>💀 ПОРАЖЕНИЕ</b>\n\n"
    
    # Проверка уровня
    old_level = player.data["level"]
    level_up = check_level_up(player)
    player.save()
    
    # Формирование результата
    result_text += f"Противник: Бот Lv.{bot_level}\n"
    result_text += f"Ставка: {bet}💰\n"
    result_text += f"Ходов: {result['turns']}\n"
    result_text += f"Опыт: +{exp_gain}\n"
    
    if result["winner_id"] == str(user_id):
        result_text += f"Награда: +{reward}💰\n"
    
    result_text += f"\n<i>Детали боя:</i>\n"
    result_text += "\n".join(result["battle_log"][-5:])  # Последние 5 строк
    
    if level_up:
        result_text += f"\n\n🎉 <b>НОВЫЙ УРОВЕНЬ: {player.data['level']}!</b>"
        result_text += f"\nПолучено +3 очка характеристик!"
    
    bot.edit_message_text(result_text[:4000], call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: m.text == "👥 PvP дуэль")
def pvp_duel_start(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    msg = bot.send_message(message.chat.id, """
<b>👥 PvP ДУЭЛЬ</b>

Для вызова на дуэль:
1. Ответьте на сообщение противника
2. Используйте команду: /duel [ставка]

Ставка от 50 до 10000💰
Победитель забирает всё!

Пример: /duel 500
""")

@bot.message_handler(commands=['duel'])
def duel_command(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Ответьте на сообщение игрока, которого хотите вызвать!")
        return
    
    user_id = message.from_user.id
    opponent_id = message.reply_to_message.from_user.id
    
    if user_id == opponent_id:
        bot.send_message(message.chat.id, "❌ Нельзя вызвать себя на дуэль!")
        return
    
    try:
        parts = message.text.split()
        bet = int(parts[1]) if len(parts) > 1 else 100
        
        if bet < 50 or bet > 10000:
            bot.send_message(message.chat.id, "❌ Ставка должна быть от 50 до 10000💰")
            return
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
    
    # Запрос на дуэль
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"accept_{user_id}_{bet}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_{user_id}")
    )
    
    bot.send_message(message.chat.id,
        f"<b>⚔ ВЫЗОВ НА ДУЭЛЬ!</b>\n\n"
        f"{message.from_user.first_name} вызывает {message.reply_to_message.from_user.first_name}!\n"
        f"Ставка: <b>{bet}💰</b>\n\n"
        f"Ожидание ответа...",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def accept_duel(call):
    parts = call.data.split("_")
    challenger_id = int(parts[1])
    bet = int(parts[2])
    opponent_id = call.from_user.id
    
    if opponent_id == challenger_id:
        bot.answer_callback_query(call.id, "❌ Нельзя принять свой же вызов!")
        return
    
    challenger = Player(challenger_id)
    opponent = Player(opponent_id)
    
    if challenger.data["money"] < bet or opponent.data["money"] < bet:
        bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
        return
    
    # Снятие ставки
    challenger.data["money"] -= bet
    opponent.data["money"] -= bet
    challenger.save()
    opponent.save()
    
    # Запуск битвы
    battle = BattleSystem(challenger_id, opponent_id, bet, "pvp")
    result = battle.execute_full_battle()
    
    # Обработка результатов
    challenger = Player(challenger_id)
    opponent = Player(opponent_id)
    
    if result["result"] == "win":
        winner = Player(result["winner_id"])
        loser = Player(result["loser_id"])
        
        winner.data["money"] += bet * 2
        winner.data["wins"] += 1
        winner.data["win_streak"] += 1
        winner.data["total_duels"] += 1
        
        loser.data["losses"] += 1
        loser.data["win_streak"] = 0
        loser.data["total_duels"] += 1
        
        winner.save()
        loser.save()
        
        result_text = f"<b>🏆 ПОБЕДИТЕЛЬ: {winner.data['first_name']}!</b>\n"
    else:
        challenger.data["money"] += bet
        opponent.data["money"] += bet
        challenger.data["draws"] += 1
        opponent.data["draws"] += 1
        challenger.save()
        opponent.save()
        
        result_text = "<b>🤝 НИЧЬЯ!</b>\nСтавки возвращены\n"
    
    result_text += f"Ходов: {result['turns']}\n"
    result_text += f"Ставка: {bet}💰\n\n"
    result_text += "<i>История боя:</i>\n"
    result_text += "\n".join(result["battle_log"][:10])
    
    bot.edit_message_text(result_text[:4000], call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("decline_"))
def decline_duel(call):
    challenger_id = int(call.data.split("_")[1])
    challenger = Player(challenger_id)
    
    bot.edit_message_text(
        f"❌ {call.from_user.first_name} отклонил вызов от {challenger.data['first_name']}",
        call.message.chat.id,
        call.message.message_id
    )

# ==================== МАГАЗИН ====================
@bot.message_handler(func=lambda m: m.text == "🛒 Магазин")
def shop_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚔ Оружие", callback_data="shop_weapon"),
        types.InlineKeyboardButton("🛡 Щиты", callback_data="shop_shield"),
        types.InlineKeyboardButton("🧥 Броня", callback_data="shop_armor"),
        types.InlineKeyboardButton("📿 Аксессуары", callback_data="shop_accessory"),
        types.InlineKeyboardButton("🧪 Зелья", callback_data="shop_potion"),
        types.InlineKeyboardButton("👢 Обувь", callback_data="shop_boots")
    )
    
    bot.send_message(message.chat.id,
        "<b>🛒 МАГАЗИН</b>\n\n"
        "Выберите категорию:\n"
        "💰 У вас: <b>{}</b> монет".format(Player(message.from_user.id).data["money"]),
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shop_"))
def shop_category(call):
    category = call.data.split("_")[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    category_name = {
        "weapon": "⚔ ОРУЖИЕ",
        "shield": "🛡 ЩИТЫ",
        "armor": "🧥 БРОНЯ",
        "accessory": "📿 АКСЕССУАРЫ",
        "potion": "🧪 ЗЕЛЬЯ",
        "boots": "👢 ОБУВЬ"
    }
    
    cat_items = {k: v for k, v in items.items() 
                 if v["type"] == category and v.get("level_req", 1) <= 100}
    
    shop_text = f"<b>{category_name.get(category, category.upper())}</b>\n\n"
    shop_text += f"💰 Баланс: <b>{player.data['money']} монет</b>\n"
    shop_text += f"⭐ Ваш уровень: <b>{player.data['level']}</b>\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, item in sorted(cat_items.items(), key=lambda x: x[1]["price"]):
        if player.data["level"] < item.get("level_req", 1):
            continue
        
        rarity_star = RARITY_COLORS.get(item["rarity"], "⬜")
        
        if item["type"] == "weapon":
            min_d, max_d = item["damage"]
            stats_text = f"⚔ Урон: {min_d}-{max_d}"
        elif item["type"] in ["shield", "armor"]:
            stats_text = f"🛡 Защита: {item.get('defense', 0)}"
        elif item["type"] == "potion":
            stats_text = f"💊 Лечение: {item.get('heal', 0)}"
        elif item["type"] == "accessory":
            stats_text = f"✨ Бонус: {item.get('description', '')}"
        elif item["type"] == "boots":
            stats_text = f"👟 Скорость: +{item.get('speed', 0)}"
        
        shop_text += f"{rarity_star} <b>{item['name']}</b>\n"
        shop_text += f"   {stats_text}\n"
        shop_text += f"   Требование: Ур.{item.get('level_req', 1)}\n"
        shop_text += f"   💰 {item['price']} монет\n\n"
        
        if player.data["money"] >= item["price"]:
            markup.add(types.InlineKeyboardButton(
                f"Купить: {item['name']}",
                callback_data=f"purchase_{item_key}"
            ))
    
    if not shop_text.endswith("монет\n\n"):
        shop_text += "Нет доступных предметов\n"
    
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_shop"))
    
    bot.edit_message_text(shop_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_shop")
def back_to_shop(call):
    shop_menu(call.message)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("purchase_"))
def purchase_item(call):
    item_key = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    # Проверяем в обычных и лимитированных предметах
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
    
    # Проверка лимита для лимитированных
    if item_key in limited_items and limited_items[item_key]["remaining"] <= 0:
        bot.answer_callback_query(call.id, "❌ Предмет закончился!")
        return
    
    # Покупка
    player.data["money"] -= item["price"]
    player.data["inventory"].append(item_key)
    
    if item_key in limited_items:
        limited_items[item_key]["remaining"] -= 1
        save_json(DATA_FILES['limited'], limited_items)
    
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ Куплено: {item['name']}!")
    bot.send_message(call.message.chat.id, 
        f"✅ Вы приобрели <b>{item['name']}</b> за {item['price']}💰!\n"
        f"Используйте раздел 👤 Герой > 🎒 Инвентарь для экипировки")
    
    # Обновление магазина
    shop_category(call)

# ==================== ИНВЕНТАРЬ И ЭКИПИРОВКА ====================
@bot.message_handler(func=lambda m: m.text == "🎒 Инвентарь")
def inventory_handler(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    if not player.data["inventory"]:
        bot.send_message(message.chat.id, "🎒 Ваш инвентарь пуст! Купите предметы в магазине.")
        return
    
    # Группировка предметов
    item_counts = {}
    for item_key in player.data["inventory"]:
        item_counts[item_key] = item_counts.get(item_key, 0) + 1
    
    inventory_text = "<b>🎒 ИНВЕНТАРЬ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, count in sorted(item_counts.items()):
        item = items.get(item_key) or limited_items.get(item_key)
        if not item:
            continue
        
        rarity = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
        equipped = ""
        
        for slot, equipped_key in player.data["equipment"].items():
            if equipped_key == item_key:
                equipped = f" [Экипировано: {slot}]"
                break
        
        inventory_text += f"{rarity} {item['name']} x{count}{equipped}\n"
        
        if item["type"] in ["weapon", "shield", "armor", "accessory", "boots"]:
            markup.add(types.InlineKeyboardButton(
                f"Экипировать: {item['name']}",
                callback_data=f"equip_{item_key}"
            ))
        elif item["type"] == "potion":
            markup.add(types.InlineKeyboardButton(
                f"Использовать: {item['name']}",
                callback_data=f"use_{item_key}"
            ))
    
    markup.add(types.InlineKeyboardButton("🗑 Выбросить предмет", callback_data="discard_menu"))
    
    bot.send_message(message.chat.id, inventory_text[:4000], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
def equip_item(call):
    item_key = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(item_key) or limited_items.get(item_key)
    if not item:
        bot.answer_callback_query(call.id, "❌ Предмет не найден!")
        return
    
    if item_key not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌ Предмета нет в инвентаре!")
        return
    
    # Экипировка в соответствующий слот
    item_type_map = {
        "weapon": "weapon",
        "shield": "shield",
        "armor": "armor",
        "accessory": "accessory",
        "boots": "boots"
    }
    
    slot = item_type_map.get(item["type"])
    if not slot:
        bot.answer_callback_query(call.id, "❌ Нельзя экипировать этот тип предмета!")
        return
    
    # Снимаем старый предмет
    old_item = player.data["equipment"][slot]
    if old_item:
        player.data["inventory"].append(old_item)
    
    # Экипируем новый
    player.data["equipment"][slot] = item_key
    player.data["inventory"].remove(item_key)
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ {item['name']} экипирован!")
    inventory_handler(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("use_"))
def use_item(call):
    item_key = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    item = items.get(item_key) or limited_items.get(item_key)
    if not item or item["type"] != "potion":
        bot.answer_callback_query(call.id, "❌ Нельзя использовать!")
        return
    
    if item_key not in player.data["inventory"]:
        bot.answer_callback_query(call.id, "❌ Нет в инвентаре!")
        return
    
    stats = player.get_equipment_stats()
    max_hp = player.data["max_hp"] + stats["hp_bonus"]
    
    if player.data["hp"] >= max_hp and item.get("heal", 0) > 0:
        bot.answer_callback_query(call.id, "❌ У вас полное здоровье!")
        return
    
    # Применение эффектов зелья
    if "instant_heal" in item.get("effects", {}):
        heal = item["effects"]["instant_heal"]
        player.data["hp"] = min(max_hp, player.data["hp"] + heal)
        bot.answer_callback_query(call.id, f"💚 +{heal} HP!")
    
    if "full_heal" in item.get("effects", {}):
        player.data["hp"] = max_hp
        bot.answer_callback_query(call.id, "💚 Полное исцеление!")
    
    # Удаление предмета
    player.data["inventory"].remove(item_key)
    player.save()
    
    bot.send_message(call.message.chat.id,
        f"✅ Использовано: <b>{item['name']}</b>\n"
        f"❤ Здоровье: {player.data['hp']}/{max_hp}")

# ==================== ХАРАКТЕРИСТИКИ ====================
@bot.message_handler(func=lambda m: m.text == "⚡ Характеристики")
def stats_handler(message):
    user_id = message.from_user.id
    player = Player(user_id)
    equipment_stats = player.get_equipment_stats()
    
    stats = player.data["stats"]
    stat_points = player.data["stat_points"]
    
    stats_text = f"""
<b>⚡ ХАРАКТЕРИСТИКИ</b>
Доступно очков: <b>{stat_points}</b>

<b>Базовые статы:</b>
💪 Сила: {stats['strength']} (+{(stats['strength']-5)*2} к мин. урону)
🏃 Ловкость: {stats['agility']} (+{stats['agility']-5} к скорости)
🧠 Интеллект: {stats['intelligence']} (+{(stats['intelligence']-5)*5} к мане)
❤ Живучесть: {stats['vitality']} (+{(stats['vitality']-5)*10} к HP)
🍀 Удача: {stats['luck']} (+{(stats['luck']-5)*0.5}% крита)

<b>Боевые характеристики:</b>
⚔ Урон: {equipment_stats['min_damage']}-{equipment_stats['max_damage']}
🛡 Защита: {equipment_stats['defense']}
💨 Скорость: {equipment_stats['speed']}
💥 Крит: {equipment_stats['crit_chance']:.1f}%
🔄 Уклонение: {equipment_stats['dodge_chance']:.1f}%
🛡 Блок: {equipment_stats['block_chance']:.1f}%

❤ HP: {player.data['hp']}/{player.data['max_hp'] + equipment_stats['hp_bonus']}
💎 Мана: {player.data['mana']}/{player.data['max_mana'] + equipment_stats['mana_bonus']}
"""
    
    if stat_points > 0:
        markup = types.InlineKeyboardMarkup(row_width=5)
        markup.add(
            types.InlineKeyboardButton("💪", callback_data="stat_str"),
            types.InlineKeyboardButton("🏃", callback_data="stat_agi"),
            types.InlineKeyboardButton("🧠", callback_data="stat_int"),
            types.InlineKeyboardButton("❤", callback_data="stat_vit"),
            types.InlineKeyboardButton("🍀", callback_data="stat_luk")
        )
        stats_text += "\n<i>Нажмите на кнопку для повышения:</i>"
    else:
        markup = None
        stats_text += "\n<i>Повышайте уровень для получения очков!</i>"
    
    bot.send_message(message.chat.id, stats_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("stat_"))
def upgrade_stat(call):
    stat_map = {
        "str": "strength",
        "agi": "agility",
        "int": "intelligence",
        "vit": "vitality",
        "luk": "luck"
    }
    
    stat_key = call.data.split("_")[1]
    stat_name = stat_map[stat_key]
    
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data["stat_points"] <= 0:
        bot.answer_callback_query(call.id, "❌ Нет очков характеристик!")
        return
    
    if player.data["stats"][stat_name] >= 100:
        bot.answer_callback_query(call.id, "❌ Максимальное значение!")
        return
    
    player.data["stats"][stat_name] += 1
    player.data["stat_points"] -= 1
    player.save()
    
    stat_names = {
        "strength": "Силы",
        "agility": "Ловкости",
        "intelligence": "Интеллекта",
        "vitality": "Живучести",
        "luck": "Удачи"
    }
    
    bot.answer_callback_query(call.id, f"⬆ {stat_names[stat_name]}: {player.data['stats'][stat_name]}")
    stats_handler(call.message)

# ==================== ДАНЖИ ====================
@bot.message_handler(func=lambda m: m.text == "🏰 Данжи")
def dungeon_menu(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    dungeon_text = """
<b>🏰 ПОДЗЕМЕЛЬЯ</b>

<b>Доступные данжи:</b>

🐺 <b>Логово волка</b> (Ур. 1-5)
Босс: Вожак стаи
Награда: 50-150💰

🕷 <b>Паучьи пещеры</b> (Ур. 5-10)
Босс: Королева пауков
Награда: 100-300💰

💀 <b>Катакомбы</b> (Ур. 10-15)
Босс: Некромант
Награда: 200-500💰

🐉 <b>Драконье логово</b> (Ур. 15-25)
Босс: Древний дракон
Награда: 500-2000💰

👹 <b>Бездна</b> (Ур. 25+)
Босс: Владыка бездны
Награда: 1000-5000💰
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🐺 Логово волка", callback_data="dungeon_1"),
        types.InlineKeyboardButton("🕷 Паучьи пещеры", callback_data="dungeon_2"),
        types.InlineKeyboardButton("💀 Катакомбы", callback_data="dungeon_3"),
        types.InlineKeyboardButton("🐉 Драконье логово", callback_data="dungeon_4"),
        types.InlineKeyboardButton("👹 Бездна", callback_data="dungeon_5")
    )
    
    bot.send_message(message.chat.id, dungeon_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dungeon_"))
def start_dungeon(call):
    dungeon_level = int(call.data.split("_")[1])
    user_id = call.from_user.id
    player = Player(user_id)
    
    level_req = [1, 5, 10, 15, 25][dungeon_level - 1]
    if player.data["level"] < level_req:
        bot.answer_callback_query(call.id, f"❌ Нужен {level_req} уровень!")
        return
    
    # Ограничение по времени
    if player.data.get("last_dungeon"):
        last = datetime.fromisoformat(player.data["last_dungeon"])
        if (datetime.now() - last) < timedelta(hours=1):
            remaining = timedelta(hours=1) - (datetime.now() - last)
            bot.answer_callback_query(call.id, f"⏰ Подождите {remaining.seconds//60} мин.")
            return
    
    # Создание босса
    boss_names = ["Волк", "Паук", "Некромант", "Дракон", "Владыка бездны"]
    boss_name = boss_names[dungeon_level - 1]
    boss_level = level_req * 2 + random.randint(1, 5)
    
    # Шанс выпадения предмета
    drop_chance = 0.1 + dungeon_level * 0.05
    got_item = None
    
    if random.random() < drop_chance:
        possible_items = [k for k, v in items.items() 
                         if v.get("level_req", 1) <= player.data["level"]
                         and v.get("rarity", "common") in 
                         ["rare", "epic", "legendary", "mythic"][:dungeon_level]]
        if possible_items:
            got_item = random.choice(possible_items)
            player.data["inventory"].append(got_item)
    
    reward = random.randint(50, 150) * dungeon_level * player.data["level"]
    exp_reward = 50 * dungeon_level * player.data["level"]
    
    player.data["money"] += reward
    player.data["exp"] += exp_reward
    player.data["total_exp"] += exp_reward
    player.data["last_dungeon"] = datetime.now().isoformat()
    
    old_level = player.data["level"]
    check_level_up(player)
    player.save()
    
    result_text = f"""
<b>🏰 ДАНЖ ПРОЙДЕН!</b>

Противник: <b>{boss_name}</b> Lv.{boss_level}
💰 Награда: <b>+{reward} монет</b>
✨ Опыт: <b>+{exp_reward}</b>
"""
    if got_item:
        item = items[got_item]
        result_text += f"\n🎁 Найден предмет: <b>{item['name']}</b>!"
    
    if player.data["level"] > old_level:
        result_text += f"\n🎉 НОВЫЙ УРОВЕНЬ: <b>{player.data['level']}</b>!"
    
    bot.edit_message_text(result_text, call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "✅ Данж пройден!")

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def check_level_up(player):
    """Проверка и выполнение повышения уровня"""
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
        
        # Титулы
        titles = {
            5: "Боец", 10: "Воитель", 15: "Рыцарь", 20: "Ветеран",
            25: "Мастер", 30: "Грандмастер", 40: "Герой", 50: "Легенда",
            60: "Мифический воин", 75: "Полубог", 100: "Божество"
        }
        
        for req_level, title in titles.items():
            if player.data["level"] >= req_level and title not in player.data["titles_collected"]:
                player.data["titles_collected"].append(title)
                player.data["title"] = title
        
        level = player.data["level"]
        exp_needed = int(100 * (1.5 ** (level - 1)))
        leveled = True
    
    return leveled

@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def statistics_handler(message):
    user_id = message.from_user.id
    player = Player(user_id)
    d = player.data
    
    winrate = (d["wins"] / d["total_duels"] * 100) if d["total_duels"] > 0 else 0
    
    stats_text = f"""
<b>📊 СТАТИСТИКА ИГРОКА</b>

<b>{d['first_name']}</b> | {d['title']}
⭐ Уровень: <b>{d['level']}</b>
📊 Рейтинг: <b>{d['pvp_rating']}</b>
💰 Баланс: <b>{d['money']} монет</b>

<b>Дуэли:</b>
🏆 Побед: {d['wins']}
💀 Поражений: {d['losses']}
🤝 Ничьих: {d['draws']}
📈 Винрейт: {winrate:.1f}%
🔥 Лучшая серия: {d['best_streak']}
⚔ Всего дуэлей: {d['total_duels']}

<b>Урон:</b>
💥 Всего нанесено: {d['total_damage_dealt']}
🛡 Всего получено: {d['total_damage_taken']}
💫 Критических ударов: {d['critical_hits_landed']}

<b>Прогресс:</b>
✨ Опыт: {d['exp']}/{int(100 * (1.5 ** (d['level'] - 1)))}
📊 Всего опыта: {d['total_exp']}
🏅 Достижений: {len(d['achievements'])}
🎒 Предметов: {len(d['inventory'])}
"""
    
    bot.send_message(message.chat.id, stats_text)

@bot.message_handler(func=lambda m: m.text == "🎁 Бонус")
@bot.message_handler(commands=['daily'])
def daily_bonus(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player.data["last_daily"] == today:
        bot.send_message(message.chat.id, "🎁 Вы уже получили бонус сегодня!")
        return
    
    bonus_money = random.randint(100, 500) + player.data["level"] * 10
    bonus_exp = random.randint(50, 200) + player.data["level"] * 5
    
    # Шанс на предмет
    got_item = None
    if random.random() < 0.15:
        common_items = [k for k, v in items.items() if v.get("rarity") == "common"]
        if common_items:
            got_item = random.choice(common_items)
            player.data["inventory"].append(got_item)
    
    player.data["money"] += bonus_money
    player.data["exp"] += bonus_exp
    player.data["total_exp"] += bonus_exp
    player.data["last_daily"] = today
    
    old_level = player.data["level"]
    check_level_up(player)
    player.save()
    
    result_text = f"""
<b>🎁 ЕЖЕДНЕВНЫЙ БОНУС</b>

💰 Монет: <b>+{bonus_money}</b>
✨ Опыта: <b>+{bonus_exp}</b>
"""
    if got_item:
        item = items[got_item]
        result_text += f"\n🎒 Предмет: <b>{item['name']}</b>"
    
    if player.data["level"] > old_level:
        result_text += f"\n🎉 НОВЫЙ УРОВЕНЬ: <b>{player.data['level']}</b>!"
    
    bot.send_message(message.chat.id, result_text)

# ==================== АДМИН ПАНЕЛЬ ====================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("💰 Выдать деньги", callback_data="admin_money"),
        types.InlineKeyboardButton("🎁 Выдать предмет", callback_data="admin_item"),
        types.InlineKeyboardButton("👁 Инфо игрока", callback_data="admin_info"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("⛔ Бан", callback_data="admin_ban"),
        types.InlineKeyboardButton("💎 Лимитки", callback_data="admin_limited"),
        types.InlineKeyboardButton("🔄 Ресет дня", callback_data="admin_reset")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>", reply_markup=markup)

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text.replace('/broadcast', '', 1).strip()
    if not text:
        bot.send_message(message.chat.id, "❌ /broadcast [текст]")
        return
    
    success, fail = 0, 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 <b>Объявление:</b>\n{text}")
            success += 1
        except:
            fail += 1
    
    bot.send_message(message.chat.id, f"✅ Отправлено: {success}\n❌ Ошибок: {fail}")

# ==================== ЗАПУСК БОТА ====================
def main():
    print("="*60)
    print("⚔️ ДУЭЛЬ БОТ v4.0 - ПОЛНАЯ ВЕРСИЯ ⚔️")
    print("="*60)
    print(f"🕒 Запуск: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print(f"⚔ Предметов: {len(items)}")
    print(f"💎 Лимитированных: {len(limited_items)}")
    print(f"🛡 Кланов: {len(clans)}")
    print("="*60)
    print("✅ Бот запущен и готов к работе!")
    print("="*60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
