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
ELEMENTS = {
    "fire": {"name": "🔥 Огонь", "strong_against": "ice", "weak_against": "water"},
    "ice": {"name": "❄ Лёд", "strong_against": "wind", "weak_against": "fire"},
    "water": {"name": "🌊 Вода", "strong_against": "fire", "weak_against": "lightning"},
    "lightning": {"name": "⚡ Молния", "strong_against": "water", "weak_against": "earth"},
    "wind": {"name": "🌪 Ветер", "strong_against": "earth", "weak_against": "ice"},
    "earth": {"name": "🏔 Земля", "strong_against": "lightning", "weak_against": "wind"},
    "light": {"name": "✨ Свет", "strong_against": "dark", "weak_against": "chaos"},
    "dark": {"name": "🌑 Тьма", "strong_against": "light", "weak_against": "light"},
    "chaos": {"name": "💀 Хаос", "strong_against": "light", "weak_against": "order"},
    "order": {"name": "⚖ Порядок", "strong_against": "chaos", "weak_against": "chaos"}
}

RARITY_COLORS = {
    "common": "⬜", "uncommon": "🟩", "rare": "🟦",
    "epic": "🟪", "legendary": "🟧", "mythic": "🟥",
    "divine": "💛", "apocalyptic": "🖤"
}

RARITY_MULTIPLIER = {
    "common": 1.0, "uncommon": 1.3, "rare": 1.8,
    "epic": 2.5, "legendary": 4.0, "mythic": 7.0,
    "divine": 12.0, "apocalyptic": 20.0
}

# ==================== ФАЙЛЫ ====================
FILES = {
    'users': 'users.json',
    'items': 'items.json',
    'limited': 'limited.json',
    'duels': 'active_duels.json',
    'clans': 'clans.json'
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
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==================== БАЗА ДАННЫХ ПРЕДМЕТОВ ====================
ITEMS_DB = {
    # ОРУЖИЕ
    "rusty_sword": {
        "name": "🗡 Ржавый меч", "type": "weapon", "rarity": "common",
        "damage": (3, 8), "element": None, "price": 50, "level_req": 1,
        "skills": ["slash", "thrust"],
        "description": "Старый, но острый меч"
    },
    "flame_blade": {
        "name": "🔥 Пламенный клинок", "type": "weapon", "rarity": "uncommon",
        "damage": (8, 15), "element": "fire", "price": 400, "level_req": 5,
        "skills": ["fire_slash", "burning_strike", "inferno"],
        "effects": {"burn": 20},
        "description": "Клинок, объятый пламенем"
    },
    "frost_axe": {
        "name": "❄ Ледяной топор", "type": "weapon", "rarity": "uncommon",
        "damage": (10, 18), "element": "ice", "price": 600, "level_req": 7,
        "skills": ["frost_cleave", "ice_shard", "blizzard"],
        "effects": {"freeze": 15},
        "description": "Замораживает врагов"
    },
    "storm_staff": {
        "name": "⚡ Посох бурь", "type": "weapon", "rarity": "rare",
        "damage": (12, 22), "element": "lightning", "price": 1200, "level_req": 12,
        "skills": ["thunder_bolt", "chain_lightning", "storm_call"],
        "effects": {"stun": 10, "chain": True},
        "description": "Призывает молнии"
    },
    "tidal_blade": {
        "name": "🌊 Приливной клинок", "type": "weapon", "rarity": "rare",
        "damage": (15, 25), "element": "water", "price": 1800, "level_req": 15,
        "skills": ["water_slash", "tidal_wave", "drown"],
        "effects": {"heal_on_hit": 0.1},
        "description": "Волны сокрушают врагов"
    },
    "shadow_dagger": {
        "name": "🌑 Теневой кинжал", "type": "weapon", "rarity": "epic",
        "damage": (18, 32), "element": "dark", "price": 3500, "level_req": 20,
        "skills": ["shadow_strike", "backstab", "assassinate", "vanish"],
        "effects": {"poison": 25, "crit_boost": 15},
        "description": "Атакует из тени"
    },
    "divine_spear": {
        "name": "✨ Божественное копьё", "type": "weapon", "rarity": "legendary",
        "damage": (25, 40), "element": "light", "price": 8000, "level_req": 28,
        "skills": ["holy_smite", "divine_judgment", "light_beam", "purify", "resurrect"],
        "effects": {"bless": 30, "holy_damage": 0.25},
        "description": "Оружие небесного воина"
    },
    "death_scythe": {
        "name": "💀 Коса смерти", "type": "weapon", "rarity": "mythic",
        "damage": (30, 55), "element": "chaos", "price": 15000, "level_req": 35,
        "skills": ["soul_reap", "death_curse", "life_drain", "obliterate", "void_slash"],
        "effects": {"curse": 30, "life_steal": 0.2, "execution": 0.15},
        "description": "Забирает души врагов"
    },
    
    # ЩИТЫ
    "wooden_shield": {
        "name": "🛡 Деревянный щит", "type": "shield", "rarity": "common",
        "defense": 5, "block_chance": 15, "price": 80, "level_req": 1,
        "skills": ["block", "shield_bash"],
        "description": "Простой щит"
    },
    "mirror_shield": {
        "name": "🪞 Зеркальный щит", "type": "shield", "rarity": "rare",
        "defense": 15, "block_chance": 25, "price": 1200, "level_req": 12,
        "skills": ["block", "reflect_magic", "counter"],
        "effects": {"reflect": 20},
        "description": "Отражает магию"
    },
    "dragon_shield": {
        "name": "🐉 Драконий щит", "type": "shield", "rarity": "epic",
        "defense": 25, "block_chance": 35, "price": 4000, "level_req": 22,
        "skills": ["block", "dragon_roar", "fire_wall", "scale_protection"],
        "effects": {"fire_resist": 40, "thorns": 15},
        "description": "Чешуя древнего дракона"
    },
    "aegis": {
        "name": "💫 Эгида", "type": "shield", "rarity": "legendary",
        "defense": 40, "block_chance": 50, "price": 12000, "level_req": 32,
        "skills": ["block", "divine_protection", "heal_barrier", "invincible", "reflect_all"],
        "effects": {"perfect_block": 20, "heal_on_block": 0.1},
        "description": "Щит богини Афины"
    },
    
    # БРОНЯ
    "leather_armor": {
        "name": "🧥 Кожаная броня", "type": "armor", "rarity": "common",
        "defense": 3, "hp_bonus": 20, "price": 60, "level_req": 1,
        "skills": ["endure"],
        "description": "Лёгкая защита"
    },
    "plate_armor": {
        "name": "🛡 Латный доспех", "type": "armor", "rarity": "uncommon",
        "defense": 12, "hp_bonus": 50, "price": 600, "level_req": 10,
        "skills": ["fortify", "iron_wall"],
        "description": "Тяжёлая броня"
    },
    "shadow_armor": {
        "name": "🌑 Теневая броня", "type": "armor", "rarity": "epic",
        "defense": 22, "hp_bonus": 100, "price": 5000, "level_req": 22,
        "skills": ["shadow_step", "vanish", "dodge_mastery"],
        "effects": {"dodge_boost": 20},
        "description": "Скрывает в тенях"
    },
    "phoenix_armor": {
        "name": "🦅 Броня Феникса", "type": "armor", "rarity": "legendary",
        "defense": 35, "hp_bonus": 200, "price": 15000, "level_req": 30,
        "skills": ["rebirth", "fire_wings", "phoenix_flame", "heal_aura"],
        "effects": {"rebirth": 1},
        "description": "Возрождает из пепла"
    },
    
    # АКСЕССУАРЫ
    "strength_ring": {
        "name": "💍 Кольцо силы", "type": "accessory", "rarity": "uncommon",
        "bonus_damage": 5, "price": 500, "level_req": 5,
        "skills": ["power_surge"],
        "description": "+5 к урону"
    },
    "crit_amulet": {
        "name": "📿 Амулет крита", "type": "accessory", "rarity": "rare",
        "crit_chance": 15, "price": 2000, "level_req": 15,
        "skills": ["lethal_strike"],
        "description": "+15% к шансу крита"
    },
    "berserker_ring": {
        "name": "💢 Кольцо берсерка", "type": "accessory", "rarity": "epic",
        "berserk_damage": 30, "price": 5000, "level_req": 25,
        "skills": ["berserk_mode", "rage"],
        "description": "+30% урона при низком HP"
    },
    
    # ЗЕЛЬЯ
    "health_potion": {
        "name": "🧪 Зелье здоровья", "type": "potion", "rarity": "common",
        "heal": 30, "price": 40, "level_req": 1,
        "skills": ["use_potion"],
        "description": "+30 HP"
    },
    "big_potion": {
        "name": "🧪 Большое зелье", "type": "potion", "rarity": "uncommon",
        "heal": 80, "price": 150, "level_req": 8,
        "skills": ["use_potion"],
        "description": "+80 HP"
    },
    "elixir": {
        "name": "💊 Эликсир жизни", "type": "potion", "rarity": "rare",
        "heal": 200, "price": 500, "level_req": 15,
        "skills": ["use_potion"],
        "effects": {"full_heal": True, "cleanse": True},
        "description": "Полное исцеление"
    },
    "berserk_potion": {
        "name": "💢 Зелье ярости", "type": "potion", "rarity": "rare",
        "heal": 0, "price": 300, "level_req": 12,
        "skills": ["use_potion"],
        "effects": {"damage_boost": 50, "duration": 3},
        "description": "+50% урона на 3 хода"
    },
    
    # ОБУВЬ
    "leather_boots": {
        "name": "👢 Кожаные сапоги", "type": "boots", "rarity": "common",
        "speed": 5, "price": 100, "level_req": 1,
        "skills": ["quick_step"],
        "description": "+5 к скорости"
    },
    "wind_boots": {
        "name": "🌪 Сапоги ветра", "type": "boots", "rarity": "rare",
        "speed": 15, "price": 1500, "level_req": 15,
        "skills": ["wind_walk", "gust_dodge"],
        "effects": {"dodge_boost": 10},
        "description": "+15 к скорости"
    },
    "blink_boots": {
        "name": "✨ Сапоги телепортации", "type": "boots", "rarity": "epic",
        "speed": 25, "price": 5000, "level_req": 25,
        "skills": ["blink", "phase_shift", "teleport_dodge"],
        "effects": {"blink_chance": 15},
        "description": "Мгновенное перемещение"
    }
}

# Лимитированные предметы
LIMITED_DB = {
    "thunderfury": {
        "name": "⚡ Ярость Грома", "type": "weapon", "rarity": "divine",
        "damage": (40, 70), "element": "lightning", "price": 50000,
        "total": 3, "remaining": 3, "level_req": 40,
        "skills": ["thunder_god", "lightning_storm", "chain_reaction", "overload", "electric_field"],
        "effects": {"chain_lightning": 0.5, "stun": 35, "shock_field": 20},
        "description": "Оружие бога грома"
    },
    "apocalypse": {
        "name": "🌋 Апокалипсис", "type": "weapon", "rarity": "apocalyptic",
        "damage": (60, 120), "element": "chaos", "price": 100000,
        "total": 1, "remaining": 1, "level_req": 50,
        "skills": ["armageddon", "obliteration", "void_blast", "existence_erase", "universal_collapse"],
        "effects": {"obliterate": 50, "void_touch": 30, "entropy": 25},
        "description": "КОНЕЦ ВСЕГО СУЩЕГО"
    },
    "immortal_shield": {
        "name": "✨ Щит Бессмертия", "type": "shield", "rarity": "divine",
        "defense": 80, "block_chance": 70, "price": 75000,
        "total": 2, "remaining": 2, "level_req": 45,
        "skills": ["immortality", "absolute_defense", "divine_intervention", "time_rewind", "perfect_guard"],
        "effects": {"invincible": 2, "auto_revive": True},
        "description": "Делает неуязвимым"
    }
}

# Загрузка данных
items = load_json(FILES['items'], ITEMS_DB)
limited_items = load_json(FILES['limited'], LIMITED_DB)
users = load_json(FILES['users'], {})
active_duels = load_json(FILES['duels'], {})
clans = load_json(FILES['clans'], {})

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
                "stamina": 100,
                "max_stamina": 100,
                "stats": {
                    "strength": 5,
                    "agility": 5,
                    "intelligence": 5,
                    "vitality": 5,
                    "luck": 5
                },
                "stat_points": 0,
                "skill_points": 0,
                "learned_skills": [],
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "win_streak": 0,
                "best_streak": 0,
                "total_duels": 0,
                "rating": 1000,
                "inventory": [],
                "equipment": {
                    "weapon": None,
                    "shield": None,
                    "armor": None,
                    "accessory": None,
                    "boots": None
                },
                "active_effects": [],
                "buffs": [],
                "debuffs": [],
                "last_daily": None,
                "title": "Новичок",
                "titles_collected": ["Новичок"],
                "achievements": [],
                "clan": None,
                "registration_date": datetime.now().isoformat(),
                "battle_history": []
            }
            self.save()
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    def save(self):
        save_json(FILES['users'], users)
    
    def get_stats(self):
        """Полный расчёт характеристик"""
        d = self.data
        stats = {
            "min_damage": d["stats"]["strength"] * 2,
            "max_damage": d["stats"]["strength"] * 3,
            "defense": 0,
            "hp_bonus": 0,
            "mana_bonus": 0,
            "speed": d["stats"]["agility"],
            "crit_chance": 5 + d["stats"]["luck"] * 0.5,
            "crit_multiplier": 1.5,
            "dodge_chance": 3 + d["stats"]["agility"] * 0.3,
            "block_chance": 0,
            "life_steal": 0,
            "reflect_damage": 0,
            "element": None,
            "element_bonus": {},
            "skills": ["basic_attack", "defend", "use_potion"],
            "effects": []
        }
        
        # Экипировка
        for slot, item_key in d["equipment"].items():
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
                if item.get("element"):
                    stats["element"] = item["element"]
                    stats["element_bonus"][item["element"]] = 20
                if "skills" in item:
                    stats["skills"].extend(item["skills"])
                for effect, value in item.get("effects", {}).items():
                    if effect == "life_steal":
                        stats["life_steal"] += value
                    elif effect == "crit_boost":
                        stats["crit_chance"] += value
                    stats["effects"].append(effect)
            
            elif item["type"] == "shield":
                stats["defense"] += item.get("defense", 0)
                stats["block_chance"] += item.get("block_chance", 0)
                if "skills" in item:
                    stats["skills"].extend(item["skills"])
                for effect, value in item.get("effects", {}).items():
                    if effect == "reflect":
                        stats["reflect_damage"] += value
                    stats["effects"].append(effect)
            
            elif item["type"] == "armor":
                stats["defense"] += item.get("defense", 0)
                stats["hp_bonus"] += item.get("hp_bonus", 0)
                if "skills" in item:
                    stats["skills"].extend(item["skills"])
                for effect, value in item.get("effects", {}).items():
                    if effect == "dodge_boost":
                        stats["dodge_chance"] += value
                    stats["effects"].append(effect)
            
            elif item["type"] == "accessory":
                if "bonus_damage" in item:
                    stats["min_damage"] += item["bonus_damage"]
                    stats["max_damage"] += item["bonus_damage"]
                if "crit_chance" in item:
                    stats["crit_chance"] += item["crit_chance"]
                if "skills" in item:
                    stats["skills"].extend(item["skills"])
            
            elif item["type"] == "boots":
                stats["speed"] += item.get("speed", 0)
                if "skills" in item:
                    stats["skills"].extend(item["skills"])
        
        # Добавляем изученные навыки
        stats["skills"].extend([s for s in d.get("learned_skills", []) if s not in stats["skills"]])
        stats["skills"] = list(set(stats["skills"]))  # Убираем дубликаты
        
        # Ограничения
        stats["crit_chance"] = min(stats["crit_chance"], 80)
        stats["dodge_chance"] = min(stats["dodge_chance"], 50)
        stats["block_chance"] = min(stats["block_chance"], 70)
        
        return stats

# ==================== ПОШАГОВАЯ БОЕВАЯ СИСТЕМА ====================
class DuelSession:
    def __init__(self, player1_id, player2_id, bet=0, duel_type="normal"):
        self.duel_id = f"duel_{int(time.time())}_{random.randint(1000,9999)}"
        self.p1_id = str(player1_id)
        self.p2_id = str(player2_id)
        self.bet = bet
        self.duel_type = duel_type
        self.turn = 0
        self.max_turns = 50
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        self.p1_stats = self.p1.get_stats()
        self.p2_stats = self.p2.get_stats()
        
        self.p1_hp = self.p1.data["max_hp"] + self.p1_stats["hp_bonus"]
        self.p2_hp = self.p2.data["max_hp"] + self.p2_stats["hp_bonus"]
        self.p1_max_hp = self.p1_hp
        self.p2_max_hp = self.p2_hp
        
        self.p1_mana = self.p1.data["max_mana"] + self.p1_stats["mana_bonus"]
        self.p2_mana = self.p2.data["max_mana"] + self.p2_stats["mana_bonus"]
        self.p1_max_mana = self.p1_mana
        self.p2_max_mana = self.p2_mana
        
        self.p1_stamina = 100
        self.p2_stamina = 100
        
        self.p1_effects = []
        self.p2_effects = []
        
        self.battle_log = []
        self.status = "active"
        self.current_player = None
        self.waiting_for = None  # ID игрока, чей ход ожидается
        
        # Определение первого хода
        if self.p1_stats["speed"] >= self.p2_stats["speed"]:
            self.current_player = 1
        else:
            self.current_player = 2
        
        self.battle_log.append("⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>")
        self.battle_log.append(f"👤 {self.p1.data['first_name']} vs {self.p2.data['first_name']}")
        self.battle_log.append(f"💨 Первый ход: <b>{self.get_player_name(self.current_player)}</b>")
        self.battle_log.append(f"Выберите действие:")
        
        self.save_duel()
    
    def get_player_name(self, num):
        return self.p1.data["first_name"] if num == 1 else self.p2.data["first_name"]
    
    def get_player_id(self, num):
        return self.p1_id if num == 1 else self.p2_id
    
    def get_hp(self, num):
        return self.p1_hp if num == 1 else self.p2_hp
    
    def set_hp(self, num, value):
        if num == 1:
            self.p1_hp = max(0, min(self.p1_max_hp, value))
        else:
            self.p2_hp = max(0, min(self.p2_max_hp, value))
    
    def get_max_hp(self, num):
        return self.p1_max_hp if num == 1 else self.p2_max_hp
    
    def get_mana(self, num):
        return self.p1_mana if num == 1 else self.p2_mana
    
    def set_mana(self, num, value):
        if num == 1:
            self.p1_mana = max(0, min(self.p1_max_mana, value))
        else:
            self.p2_mana = max(0, min(self.p2_max_mana, value))
    
    def get_stamina(self, num):
        return self.p1_stamina if num == 1 else self.p2_stamina
    
    def set_stamina(self, num, value):
        if num == 1:
            self.p1_stamina = max(0, min(100, value))
        else:
            self.p2_stamina = max(0, min(100, value))
    
    def get_stats(self, num):
        return self.p1_stats if num == 1 else self.p2_stats
    
    def get_opponent_num(self, player_num):
        return 2 if player_num == 1 else 1
    
    def save_duel(self):
        active_duels[self.duel_id] = {
            "id": self.duel_id,
            "p1_id": self.p1_id,
            "p2_id": self.p2_id,
            "bet": self.bet,
            "type": self.duel_type,
            "turn": self.turn,
            "current_player": self.current_player,
            "waiting_for": self.waiting_for,
            "p1_hp": self.p1_hp,
            "p2_hp": self.p2_hp,
            "p1_max_hp": self.p1_max_hp,
            "p2_max_hp": self.p2_max_hp,
            "p1_mana": self.p1_mana,
            "p2_mana": self.p2_mana,
            "p1_stamina": self.p1_stamina,
            "p2_stamina": self.p2_stamina,
            "status": self.status,
            "battle_log": self.battle_log[-20:]  # Храним последние 20 строк
        }
        save_json(FILES['duels'], active_duels)
    
    def remove_duel(self):
        if self.duel_id in active_duels:
            del active_duels[self.duel_id]
            save_json(FILES['duels'], active_duels)
    
    def get_hp_bar(self, current, maximum):
        pct = current / maximum if maximum > 0 else 0
        filled = int(pct * 10)
        return f"[{'█' * filled}{'░' * (10 - filled)}] {current}/{maximum}"
    
    def calculate_skill_damage(self, attacker_num, defender_num, skill_name):
        """Расчёт урона для конкретного навыка"""
        attacker_stats = self.get_stats(attacker_num)
        defender_stats = self.get_stats(defender_num)
        
        # Базовый урон
        base_min = attacker_stats["min_damage"]
        base_max = attacker_stats["max_damage"]
        base_damage = random.randint(base_min, base_max)
        
        # Множители навыка
        skill_multipliers = {
            "basic_attack": 1.0,
            "slash": 1.2,
            "thrust": 1.5,
            "fire_slash": 1.8,
            "burning_strike": 2.2,
            "inferno": 3.5,
            "frost_cleave": 1.8,
            "ice_shard": 1.6,
            "blizzard": 3.0,
            "thunder_bolt": 2.0,
            "chain_lightning": 2.5,
            "storm_call": 3.5,
            "water_slash": 1.5,
            "tidal_wave": 2.8,
            "shadow_strike": 2.0,
            "backstab": 2.5,
            "assassinate": 4.0,
            "holy_smite": 2.5,
            "divine_judgment": 3.5,
            "light_beam": 3.0,
            "death_curse": 3.0,
            "soul_reap": 4.5,
            "life_drain": 2.5,
            "obliterate": 5.0,
            "shield_bash": 0.8,
            "counter": 1.5,
            "thunder_god": 5.0,
            "lightning_storm": 4.5,
            "armageddon": 6.0,
            "void_blast": 5.5,
            "existence_erase": 8.0
        }
        
        multiplier = skill_multipliers.get(skill_name, 1.0)
        damage = int(base_damage * multiplier)
        
        # Стоимость маны
        mana_costs = {
            "fire_slash": 15, "burning_strike": 25, "inferno": 50,
            "frost_cleave": 20, "blizzard": 45, "thunder_bolt": 20,
            "chain_lightning": 30, "storm_call": 50, "tidal_wave": 35,
            "shadow_strike": 25, "assassinate": 60, "holy_smite": 30,
            "divine_judgment": 55, "death_curse": 35, "soul_reap": 70,
            "obliterate": 80, "thunder_god": 60, "lightning_storm": 55,
            "armageddon": 100, "existence_erase": 150
        }
        mana_cost = mana_costs.get(skill_name, 0)
        
        # Стоимость выносливости
        stamina_costs = {
            "basic_attack": 10, "slash": 15, "thrust": 20,
            "fire_slash": 20, "inferno": 40, "backstab": 25,
            "assassinate": 50, "soul_reap": 60, "obliterate": 70,
            "armageddon": 80, "existence_erase": 100
        }
        stamina_cost = stamina_costs.get(skill_name, 10)
        
        # Критический удар
        is_crit = random.random() * 100 < attacker_stats["crit_chance"]
        if is_crit:
            damage = int(damage * attacker_stats["crit_multiplier"])
        
        # Элементальное взаимодействие
        if attacker_stats.get("element"):
            attacker_element = attacker_stats["element"]
            if attacker_element in ELEMENTS:
                if ELEMENTS[attacker_element]["strong_against"]:
                    damage = int(damage * 1.3)
                    self.battle_log.append(f"💥 СУПЕРЭФФЕКТИВНО!")
        
        # Защита
        defense = defender_stats["defense"]
        damage_reduction = defense / (defense + 100)
        damage = int(damage * (1 - damage_reduction))
        
        # Блок
        if random.random() * 100 < defender_stats["block_chance"]:
            damage = int(damage * 0.5)
            self.battle_log.append(f"🛡 ЧАСТИЧНЫЙ БЛОК!")
        
        # Уклонение
        if random.random() * 100 < defender_stats["dodge_chance"]:
            self.battle_log.append(f"💨 УКЛОНЕНИЕ!")
            return 0, False, mana_cost, stamina_cost
        
        # Вампиризм
        if attacker_stats["life_steal"] > 0:
            heal = int(damage * attacker_stats["life_steal"])
            self.set_hp(attacker_num, self.get_hp(attacker_num) + heal)
            if heal > 0:
                self.battle_log.append(f"💚 Вампиризм +{heal} HP")
        
        damage = max(1, damage)
        return damage, is_crit, mana_cost, stamina_cost
    
    def execute_action(self, player_id, action, skill_name="basic_attack"):
        """Выполнение действия игрока"""
        if self.status != "active":
            return False, "Дуэль уже завершена!"
        
        current_player_id = self.get_player_id(self.current_player)
        if str(player_id) != current_player_id:
            return False, "Сейчас не ваш ход!"
        
        attacker_num = self.current_player
        defender_num = self.get_opponent_num(attacker_num)
        
        self.turn += 1
        self.battle_log.append(f"\n<b>ХОД {self.turn}</b>")
        self.battle_log.append(f"▶ {self.get_player_name(attacker_num)} использует <b>{skill_name}</b>")
        
        if action == "attack":
            damage, is_crit, mana_cost, stamina_cost = self.calculate_skill_damage(
                attacker_num, defender_num, skill_name
            )
            
            # Проверка маны
            if self.get_mana(attacker_num) < mana_cost:
                self.battle_log.append("❌ Недостаточно маны! Использована базовая атака")
                damage, is_crit, mana_cost, stamina_cost = self.calculate_skill_damage(
                    attacker_num, defender_num, "basic_attack"
                )
            
            # Проверка выносливости
            if self.get_stamina(attacker_num) < stamina_cost:
                self.battle_log.append("😫 Недостаточно выносливости! Пропуск хода")
                damage = 0
            
            self.set_mana(attacker_num, self.get_mana(attacker_num) - mana_cost)
            self.set_stamina(attacker_num, self.get_stamina(attacker_num) - stamina_cost)
            
            if damage > 0:
                crit_text = "💥 <b>КРИТИЧЕСКИЙ УДАР!</b> " if is_crit else ""
                self.battle_log.append(f"{crit_text}⚔ Нанесено <b>{damage}</b> урона!")
                self.set_hp(defender_num, self.get_hp(defender_num) - damage)
                
                # Проверка смертельного удара
                if self.get_hp(defender_num) <= 0:
                    self.end_duel(attacker_num)
                    return True, "Дуэль завершена!"
        
        elif action == "defend":
            # Защита: восстанавливает выносливость и уменьшает урон в след.ходу
            self.set_stamina(attacker_num, self.get_stamina(attacker_num) + 30)
            self.battle_log.append(f"🛡 {self.get_player_name(attacker_num)} встаёт в защиту! +30 выносливости")
            
            # Добавляем временный бафф защиты
            if attacker_num == 1:
                self.p1_effects.append({"type": "defense_up", "turns": 1, "value": 20})
            else:
                self.p2_effects.append({"type": "defense_up", "turns": 1, "value": 20})
        
        elif action == "use_potion":
            # Использование зелья
            player = self.p1 if attacker_num == 1 else self.p2
            potions = [k for k in player.data["inventory"] if 
                      (items.get(k) or limited_items.get(k, {})).get("type") == "potion"]
            
            if not potions:
                self.battle_log.append("❌ Нет зелий! Пропуск хода")
            else:
                potion_key = potions[0]  # Берём первое доступное
                potion = items.get(potion_key) or limited_items.get(potion_key)
                
                if potion:
                    heal = potion.get("heal", 30)
                    self.set_hp(attacker_num, self.get_hp(attacker_num) + heal)
                    player.data["inventory"].remove(potion_key)
                    player.save()
                    
                    self.battle_log.append(f"🧪 Использовано {potion['name']}! +{heal} HP")
        
        elif action == "special":
            # Специальные навыки
            special_skills = ["shield_bash", "counter", "defend", "dodge_mastery"]
            if skill_name in special_skills:
                self.battle_log.append(f"✨ Использован специальный приём: {skill_name}")
                self.set_stamina(attacker_num, self.get_stamina(attacker_num) + 20)
        
        # Восстановление выносливости каждый ход
        self.set_stamina(attacker_num, self.get_stamina(attacker_num) + 5)
        self.set_stamina(defender_num, self.get_stamina(defender_num) + 5)
        
        # Восстановление маны
        self.set_mana(attacker_num, self.get_mana(attacker_num) + 3)
        self.set_mana(defender_num, self.get_mana(defender_num) + 3)
        
        # Отображение HP
        self.battle_log.append(f"❤ {self.get_player_name(1)}: {self.get_hp_bar(self.p1_hp, self.p1_max_hp)}")
        self.battle_log.append(f"❤ {self.get_player_name(2)}: {self.get_hp_bar(self.p2_hp, self.p2_max_hp)}")
        self.battle_log.append(f"💎 Мана P1: {self.p1_mana}/{self.p1_max_mana} | P2: {self.p2_mana}/{self.p2_max_mana}")
        self.battle_log.append(f"⚡ Стамина P1: {self.p1_stamina}/100 | P2: {self.p2_stamina}/100")
        
        # Смена хода
        self.current_player = defender_num
        self.battle_log.append(f"\n▶ Ход переходит к <b>{self.get_player_name(self.current_player)}</b>")
        self.battle_log.append("Выберите действие:")
        
        # Проверка на превышение ходов
        if self.turn >= self.max_turns:
            self.end_duel(None)  # Ничья
            return True, "Дуэль завершена! Ничья по ходам"
        
        self.save_duel()
        return True, "Ход выполнен"
    
    def end_duel(self, winner_num):
        """Завершение дуэли"""
        self.status = "finished"
        
        if winner_num is None:
            winner_id = None
            loser_id = None
            result = "draw"
            self.battle_log.append("\n🤝 <b>НИЧЬЯ!</b>")
        else:
            winner_id = self.get_player_id(winner_num)
            loser_id = self.get_player_id(self.get_opponent_num(winner_num))
            result = "win"
            self.battle_log.append(f"\n🏆 <b>ПОБЕДИТЕЛЬ: {self.get_player_name(winner_num)}!</b>")
        
        # Обработка результатов
        if result == "win":
            winner = Player(winner_id)
            loser = Player(loser_id)
            
            # Ставка
            if self.bet > 0:
                winner.data["money"] += self.bet * 2
                winner.data["wins"] += 1
                loser.data["losses"] += 1
            else:
                winner.data["wins"] += 1
                loser.data["losses"] += 1
            
            winner.data["win_streak"] += 1
            loser.data["win_streak"] = 0
            
            if winner.data["win_streak"] > winner.data["best_streak"]:
                winner.data["best_streak"] = winner.data["win_streak"]
            
            winner.data["total_duels"] += 1
            loser.data["total_duels"] += 1
            
            # Опыт
            exp_gain = 50 + self.turn * 5
            winner.data["exp"] += exp_gain
            winner.data["total_exp"] += exp_gain
            loser.data["exp"] += exp_gain // 2
            
            # Изменение рейтинга
            winner.data["rating"] += 25
            loser.data["rating"] = max(0, loser.data["rating"] - 15)
            
            if check_level_up(winner):
                self.battle_log.append(f"🎉 {winner.data['first_name']} повысил уровень до {winner.data['level']}!")
            
            winner.save()
            loser.save()
        
        elif result == "draw":
            p1 = Player(self.p1_id)
            p2 = Player(self.p2_id)
            p1.data["draws"] += 1
            p2.data["draws"] += 1
            
            if self.bet > 0:
                p1.data["money"] += self.bet  # Возврат ставки
                p2.data["money"] += self.bet
            
            p1.save()
            p2.save()
        
        self.remove_duel()

# ==================== МЕНЮ ====================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("⚔ Дуэли"),
        types.KeyboardButton("👤 Персонаж"),
        types.KeyboardButton("🏪 Магазин"),
        types.KeyboardButton("🌍 Мир")
    )
    return markup

def get_duel_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("⚡ Быстрая дуэль"),
        types.KeyboardButton("👥 PvP Дуэль"),
        types.KeyboardButton("🏆 Рейтинговая"),
        types.KeyboardButton("💀 Хардкорная"),
        types.KeyboardButton("◀ Назад")
    )
    return markup

def get_character_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📊 Статистика"),
        types.KeyboardButton("🎒 Инвентарь"),
        types.KeyboardButton("⚡ Характеристики"),
        types.KeyboardButton("📜 Навыки"),
        types.KeyboardButton("◀ Назад")
    )
    return markup

def get_shop_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 Магазин оружия"),
        types.KeyboardButton("💎 Редкие предметы"),
        types.KeyboardButton("🎁 Ежедневный бонус"),
        types.KeyboardButton("💰 Баланс"),
        types.KeyboardButton("◀ Назад")
    )
    return markup

def get_world_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🏰 Подземелья"),
        types.KeyboardButton("🛡 Кланы"),
        types.KeyboardButton("🏟 Турниры"),
        types.KeyboardButton("📋 Квесты"),
        types.KeyboardButton("◀ Назад")
    )
    return markup

def get_battle_keyboard(duel):
    """Клавиатура для боя с доступными навыками"""
    current_player_id = duel.get_player_id(duel.current_player)
    player = duel.p1 if duel.current_player == 1 else duel.p2
    stats = duel.get_stats(duel.current_player)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Базовые действия
    markup.add(
        types.InlineKeyboardButton("⚔ Атаковать", callback_data=f"battle_attack_{duel.duel_id}"),
        types.InlineKeyboardButton("🛡 Защита", callback_data=f"battle_defend_{duel.duel_id}")
    )
    
    # Доступные навыки оружия
    weapon_skills = [s for s in stats["skills"] if s not in ["basic_attack", "defend", "use_potion"]]
    for skill in weapon_skills[:4]:  # Показываем до 4 навыков
        skill_display = skill.replace("_", " ").title()
        markup.add(types.InlineKeyboardButton(
            f"✨ {skill_display}", 
            callback_data=f"battle_skill_{duel.duel_id}_{skill}"
        ))
    
    # Зелья
    potions = [k for k in player.data["inventory"] if 
              (items.get(k) or limited_items.get(k, {})).get("type") == "potion"]
    if potions:
        markup.add(types.InlineKeyboardButton(
            f"🧪 Зелье ({len(potions)} шт.)", 
            callback_data=f"battle_potion_{duel.duel_id}"
        ))
    
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data=f"battle_surrender_{duel.duel_id}"))
    
    return markup

# ==================== ОБРАБОТЧИКИ КОМАНД ====================
@bot.message_handler(commands=['start'])
def start(message):
    if str(message.from_user.id) in banned_users:
        bot.send_message(message.chat.id, "⛔ Вы забанены!")
        return
    
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    first_name = message.from_user.first_name or "Игрок"
    
    Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔ ДУЭЛЬ БОТ v5.0 ⚔</b>
<i>Пошаговая стратегическая дуэльная система</i>

Добро пожаловать, <b>{first_name}</b>!

<b>🎯 Особенности:</b>
• Пошаговые дуэли с выбором навыков
• Система маны и выносливости
• Элементальные взаимодействия
• 100+ навыков и заклинаний
• Стратегическая боевая система
• Редкие и лимитированные предметы

<b>💰 Стартовый бонус: 500 монет</b>
<b>📊 Система уровней и навыков</b>

Выберите раздел в меню:
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "◀ Назад")
def back_to_main(message):
    bot.send_message(message.chat.id, "🔙 Главное меню", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "⚔ Дуэли")
def duel_menu(message):
    bot.send_message(message.chat.id, """
<b>⚔ РАЗДЕЛ ДУЭЛЕЙ</b>

<b>⚡ Быстрая дуэль</b> - сражение с ботом
<b>👥 PvP Дуэль</b> - пошаговый бой с игроком
<b>🏆 Рейтинговая</b> - за рейтинг и награды
<b>💀 Хардкорная</b> - высокие ставки

<b>🕹 Пошаговая система:</b>
• Выбирайте навыки каждый ход
• Управляйте маной и выносливостью
• Используйте зелья в бою
• Стратегия важнее силы!
""", reply_markup=get_duel_keyboard())

@bot.message_handler(func=lambda m: m.text == "⚡ Быстрая дуэль")
def quick_duel_start(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    for bet in [50, 100, 200, 500, 1000, 2000]:
        markup.add(types.InlineKeyboardButton(
            f"{bet}💰", callback_data=f"quick_bet_{bet}"
        ))
    markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_duel"))
    
    bot.send_message(message.chat.id, 
        f"<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n\nВыберите ставку:\nВаш баланс: {player.data['money']}💰",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("quick_bet_"))
def start_quick_duel(call):
    user_id = call.from_user.id
    bet = int(call.data.split("_")[2])
    player = Player(user_id)
    
    if player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    player.data["money"] -= bet
    player.save()
    
    # Создание бота
    bot_level = random.randint(max(1, player.data["level"] - 3), player.data["level"] + 3)
    bot_id = f"bot_{random.randint(10000,99999)}"
    
    # Генерация экипировки бота
    bot_equip = {}
    for slot, item_type in [("weapon", "weapon"), ("shield", "shield"), 
                             ("armor", "armor"), ("accessory", "accessory"), 
                             ("boots", "boots")]:
        available = [k for k, v in items.items() 
                    if v["type"] == item_type and v.get("level_req", 1) <= bot_level
                    and v.get("rarity", "common") in ["common", "uncommon", "rare"]]
        if available and random.random() < 0.6:
            bot_equip[slot] = random.choice(available)
    
    users[bot_id] = {
        "username": f"Bot_{bot_level}",
        "first_name": f"🤖 Бот Lv.{bot_level}",
        "money": 0, "level": bot_level, "exp": 0, "total_exp": 0,
        "hp": 100 + bot_level * 10, "max_hp": 100 + bot_level * 10,
        "mana": 50 + bot_level * 5, "max_mana": 50 + bot_level * 5,
        "stamina": 100, "max_stamina": 100,
        "stats": {
            "strength": 5 + bot_level,
            "agility": 5 + bot_level // 2,
            "intelligence": 5 + bot_level // 3,
            "vitality": 5 + bot_level // 2,
            "luck": 3 + bot_level // 4
        },
        "stat_points": 0, "skill_points": 0, "learned_skills": [],
        "wins": 0, "losses": 0, "draws": 0,
        "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "rating": 1000,
        "inventory": ["health_potion"],
        "equipment": bot_equip,
        "active_effects": [], "buffs": [], "debuffs": [],
        "last_daily": None,
        "title": "Бот", "titles_collected": ["Бот"],
        "achievements": [], "clan": None,
        "registration_date": datetime.now().isoformat(),
        "battle_history": []
    }
    
    # Запуск дуэли
    duel = DuelSession(user_id, bot_id, bet, "quick")
    
    # Удаляем бота после дуэли
    def cleanup_bot():
        time.sleep(2)
        if bot_id in users:
            del users[bot_id]
    
    # Автоматические ходы бота
    def bot_turns():
        while duel.status == "active":
            time.sleep(3)  # Бот думает 3 секунды
            
            if duel.status != "active":
                break
            
            if str(duel.get_player_id(duel.current_player)) == bot_id:
                # Выбор действия ботом
                actions = ["attack"]
                if random.random() < 0.3:
                    actions.append("defend")
                if random.random() < 0.2:
                    actions.append("use_potion")
                
                action = random.choice(actions)
                
                if action == "attack":
                    bot_skills = duel.get_stats(2 if duel.current_player == 2 else 1)["skills"]
                    available_skills = [s for s in bot_skills 
                                      if s not in ["basic_attack", "defend", "use_potion"]]
                    
                    if available_skills and duel.get_mana(duel.current_player) >= 20:
                        skill = random.choice(available_skills)
                    else:
                        skill = "basic_attack"
                    
                    duel.execute_action(bot_id, "attack", skill)
                else:
                    duel.execute_action(bot_id, action)
                
                # Отправка обновления после хода бота
                try:
                    markup = get_battle_keyboard(duel)
                    log_text = "\n".join(duel.battle_log[-15:])
                    
                    if duel.status == "active":
                        bot.edit_message_text(
                            f"<b>⚔ БИТВА С БОТОМ</b>\n\n{log_text}",
                            call.message.chat.id,
                            call.message.message_id,
                            reply_markup=markup
                        )
                    else:
                        # Завершение дуэли
                        finish_duel(duel, call.message)
                except:
                    pass
                
                # Небольшая пауза между ходами
                time.sleep(2)
    
    # Запуск бота в потоке
    bot_thread = threading.Thread(target=bot_turns, daemon=True)
    bot_thread.start()
    
    # Первый ход
    log_text = "\n".join(duel.battle_log[-15:])
    markup = get_battle_keyboard(duel)
    
    bot.edit_message_text(
        f"<b>⚔ БИТВА С БОТОМ (Lv.{bot_level})</b>\nСтавка: {bet}💰\n\n{log_text}",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "👥 PvP Дуэль")
def pvp_duel_info(message):
    bot.send_message(message.chat.id, """
<b>👥 PvP ДУЭЛЬ</b>

Пошаговая стратегическая дуэль против другого игрока!

<b>Как вызвать:</b>
1. Ответьте на сообщение противника
2. Команда: <b>/duel [ставка]</b>

<b>Особенности:</b>
• Каждый ход вы выбираете действие
• Используйте навыки оружия и брони
• Управляйте маной и выносливостью
• Применяйте зелья во время боя

Ставка: от 50 до 10000💰
Пример: /duel 500
""")

@bot.message_handler(commands=['duel'])
def pvp_duel_command(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Ответьте на сообщение противника!")
        return
    
    user_id = message.from_user.id
    opponent = message.reply_to_message.from_user
    
    if user_id == opponent.id:
        bot.send_message(message.chat.id, "❌ Нельзя вызвать себя!")
        return
    
    try:
        bet = int(message.text.split()[1]) if len(message.text.split()) > 1 else 100
        bet = max(50, min(10000, bet))
    except:
        bet = 100
    
    player = Player(user_id)
    target = Player(opponent.id)
    
    if player.data["money"] < bet:
        bot.send_message(message.chat.id, f"❌ Недостаточно монет! Нужно {bet}💰")
        return
    
    if target.data["money"] < bet:
        bot.send_message(message.chat.id, f"❌ У противника недостаточно монет!")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Принять вызов", callback_data=f"pvp_accept_{user_id}_{bet}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"pvp_decline_{user_id}")
    )
    
    bot.send_message(message.chat.id,
        f"<b>⚔ ВЫЗОВ НА ДУЭЛЬ!</b>\n\n"
        f"{message.from_user.first_name} вызывает {opponent.first_name}!\n"
        f"💰 Ставка: <b>{bet} монет</b>\n"
        f"🕹 Режим: <b>Пошаговая стратегия</b>\n\n"
        f"Ожидание ответа...",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pvp_accept_"))
def accept_pvp_duel(call):
    parts = call.data.split("_")
    challenger_id = int(parts[2])
    bet = int(parts[3])
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
    
    # Запуск дуэли
    duel = DuelSession(challenger_id, opponent_id, bet, "pvp")
    
    log_text = "\n".join(duel.battle_log)
    markup = get_battle_keyboard(duel)
    
    bot.edit_message_text(
        f"<b>⚔ PvP ДУЭЛЬ</b>\n"
        f"{challenger.data['first_name']} vs {opponent.data['first_name']}\n"
        f"💰 Ставка: {bet}\n\n{log_text}",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("battle_"))
def handle_battle_action(call):
    parts = call.data.split("_")
    action = parts[1]
    duel_id = parts[2]
    
    if duel_id not in active_duels:
        bot.answer_callback_query(call.id, "❌ Дуэль не найдена!")
        return
    
    duel_data = active_duels[duel_id]
    user_id = call.from_user.id
    
    # Восстанавливаем дуэль
    duel = DuelSession.__new__(DuelSession)
    duel.duel_id = duel_data["id"]
    duel.p1_id = duel_data["p1_id"]
    duel.p2_id = duel_data["p2_id"]
    duel.bet = duel_data["bet"]
    duel.duel_type = duel_data["type"]
    duel.turn = duel_data["turn"]
    duel.current_player = duel_data["current_player"]
    duel.p1_hp = duel_data["p1_hp"]
    duel.p2_hp = duel_data["p2_hp"]
    duel.p1_max_hp = duel_data["p1_max_hp"]
    duel.p2_max_hp = duel_data["p2_max_hp"]
    duel.p1_mana = duel_data["p1_mana"]
    duel.p2_mana = duel_data["p2_mana"]
    duel.p1_stamina = duel_data["p1_stamina"]
    duel.p2_stamina = duel_data["p2_stamina"]
    duel.status = duel_data["status"]
    duel.battle_log = duel_data["battle_log"]
    duel.max_turns = 50
    
    duel.p1 = Player(duel.p1_id)
    duel.p2 = Player(duel.p2_id)
    duel.p1_stats = duel.p1.get_stats()
    duel.p2_stats = duel.p2.get_stats()
    
    if action == "attack":
        skill = "basic_attack"
        if len(parts) > 3:
            skill = parts[3]
        
        success, msg = duel.execute_action(user_id, "attack", skill)
        
        if not success:
            bot.answer_callback_query(call.id, msg)
            return
        
    elif action == "skill":
        skill = parts[3] if len(parts) > 3 else "basic_attack"
        success, msg = duel.execute_action(user_id, "attack", skill)
        
        if not success:
            bot.answer_callback_query(call.id, msg)
            return
    
    elif action == "defend":
        success, msg = duel.execute_action(user_id, "defend")
        if not success:
            bot.answer_callback_query(call.id, msg)
            return
    
    elif action == "potion":
        success, msg = duel.execute_action(user_id, "use_potion")
        if not success:
            bot.answer_callback_query(call.id, msg)
            return
    
    elif action == "surrender":
        loser_num = 1 if str(user_id) == duel.p1_id else 2
        winner_num = 2 if loser_num == 1 else 1
        duel.end_duel(winner_num)
    
    # Обновление сообщения
    log_text = "\n".join(duel.battle_log[-20:])
    
    if duel.status == "active":
        markup = get_battle_keyboard(duel)
    else:
        markup = None
        finish_duel(duel, call.message)
    
    try:
        bot.edit_message_text(
            f"<b>⚔ ДУЭЛЬ</b>\nХод: {duel.turn}\n\n{log_text}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    except Exception as e:
        print(f"Error updating: {e}")
    
    bot.answer_callback_query(call.id, msg if 'msg' in locals() else "✅")

def finish_duel(duel, message):
    """Отправка результатов дуэли"""
    log_text = "\n".join(duel.battle_log[-10:])
    
    result_text = f"<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>\n\n{log_text}"
    
    if duel.bet > 0:
        if duel.status == "finished":
            result_text += f"\n\n💰 Ставка: {duel.bet} монет"
    
    bot.send_message(message.chat.id, result_text)

# ==================== МАГАЗИН ====================
@bot.message_handler(func=lambda m: m.text == "🛒 Магазин оружия")
def shop_main(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    categories = {
        "weapon": "⚔ Оружие",
        "shield": "🛡 Щиты",
        "armor": "🧥 Броня",
        "accessory": "📿 Аксессуары",
        "potion": "🧪 Зелья",
        "boots": "👢 Обувь"
    }
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    for cat_key, cat_name in categories.items():
        markup.add(types.InlineKeyboardButton(cat_name, callback_data=f"shopcat_{cat_key}"))
    markup.add(types.InlineKeyboardButton("💎 Редкие предметы", callback_data="shop_limited"))
    
    bot.send_message(message.chat.id,
        f"<b>🏪 МАГАЗИН</b>\n\n💰 Баланс: <b>{player.data['money']} монет</b>\n⭐ Уровень: <b>{player.data['level']}</b>\n\nВыберите категорию:",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shopcat_"))
def shop_category(call):
    cat = call.data.split("_")[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    cat_names = {
        "weapon": "⚔ ОРУЖИЕ", "shield": "🛡 ЩИТЫ", "armor": "🧥 БРОНЯ",
        "accessory": "📿 АКСЕССУАРЫ", "potion": "🧪 ЗЕЛЬЯ", "boots": "👢 ОБУВЬ"
    }
    
    cat_items = {k: v for k, v in items.items() if v["type"] == cat}
    
    text = f"<b>{cat_names.get(cat, cat)}</b>\n\n"
    text += f"💰 Баланс: {player.data['money']} | ⭐ Ур.{player.data['level']}\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, item in sorted(cat_items.items(), key=lambda x: x[1]["price"]):
        if player.data["level"] < item.get("level_req", 1):
            continue
        
        rarity = RARITY_COLORS.get(item["rarity"], "⬜")
        
        if item["type"] == "weapon":
            min_d, max_d = item["damage"]
            stats = f"Урон: {min_d}-{max_d}"
        elif item["type"] in ["shield", "armor"]:
            stats = f"Защита: {item.get('defense', 0)}"
        elif item["type"] == "potion":
            stats = f"Лечение: {item.get('heal', 0)}"
        elif item["type"] == "accessory":
            stats = f"Бонус: +{item.get('bonus_damage', item.get('crit_chance', 0))}"
        elif item["type"] == "boots":
            stats = f"Скорость: +{item.get('speed', 0)}"
        
        text += f"{rarity} <b>{item['name']}</b> - {item['price']}💰\n   {stats} | Ур.{item.get('level_req', 1)}\n"
        
        if player.data["money"] >= item["price"]:
            markup.add(types.InlineKeyboardButton(
                f"Купить: {item['name']} - {item['price']}💰",
                callback_data=f"buy_{item_key}"
            ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_shop"))
    
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
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
    
    if item_key in limited_items and limited_items[item_key]["remaining"] <= 0:
        bot.answer_callback_query(call.id, "❌ Предмет закончился!")
        return
    
    player.data["money"] -= item["price"]
    player.data["inventory"].append(item_key)
    
    if item_key in limited_items:
        limited_items[item_key]["remaining"] -= 1
        save_json(FILES['limited'], limited_items)
    
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ Куплено: {item['name']}!")
    bot.send_message(call.message.chat.id, f"✅ Вы приобрели <b>{item['name']}</b>!")
    shop_category(call)

@bot.callback_query_handler(func=lambda call: call.data == "back_shop")
def back_shop(call):
    shop_main(call.message)
    bot.answer_callback_query(call.id)

# ==================== ИНВЕНТАРЬ ====================
@bot.message_handler(func=lambda m: m.text == "🎒 Инвентарь")
def inventory(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    if not player.data["inventory"]:
        bot.send_message(message.chat.id, "🎒 Инвентарь пуст!")
        return
    
    item_counts = {}
    for k in player.data["inventory"]:
        item_counts[k] = item_counts.get(k, 0) + 1
    
    text = "<b>🎒 ИНВЕНТАРЬ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, count in item_counts.items():
        item = items.get(item_key) or limited_items.get(item_key)
        if not item:
            continue
        
        rarity = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
        
        equipped = ""
        for slot, eq in player.data["equipment"].items():
            if eq == item_key:
                equipped = f" [{slot}]"
                break
        
        text += f"{rarity} {item['name']} x{count}{equipped}\n"
        
        equip_types = ["weapon", "shield", "armor", "accessory", "boots"]
        if item["type"] in equip_types:
            markup.add(types.InlineKeyboardButton(
                f"Экипировать: {item['name'][:30]}", 
                callback_data=f"equip_{item_key}"
            ))
        elif item["type"] == "potion":
            markup.add(types.InlineKeyboardButton(
                f"Использовать: {item['name'][:30]}", 
                callback_data=f"use_{item_key}"
            ))
    
    bot.send_message(message.chat.id, text[:4000], reply_markup=markup)

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
        bot.answer_callback_query(call.id, "❌ Нет в инвентаре!")
        return
    
    slot = item["type"]
    if slot not in player.data["equipment"]:
        bot.answer_callback_query(call.id, "❌ Нельзя экипировать!")
        return
    
    # Снимаем старый
    old = player.data["equipment"][slot]
    if old:
        player.data["inventory"].append(old)
    
    # Экипируем новый
    player.data["equipment"][slot] = item_key
    player.data["inventory"].remove(item_key)
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ {item['name']} экипирован!")
    inventory(call.message)

# ==================== ХАРАКТЕРИСТИКИ ====================
@bot.message_handler(func=lambda m: m.text == "⚡ Характеристики")
def stats(message):
    user_id = message.from_user.id
    player = Player(user_id)
    stats = player.get_stats()
    d = player.data
    
    text = f"""
<b>⚡ ХАРАКТЕРИСТИКИ</b>
Доступно очков: <b>{d['stat_points']}</b>

<b>Базовые:</b>
💪 Сила: {d['stats']['strength']}
🏃 Ловкость: {d['stats']['agility']}
🧠 Интеллект: {d['stats']['intelligence']}
❤ Живучесть: {d['stats']['vitality']}
🍀 Удача: {d['stats']['luck']}

<b>Боевые:</b>
⚔ Урон: {stats['min_damage']}-{stats['max_damage']}
🛡 Защита: {stats['defense']}
💨 Скорость: {stats['speed']}
💥 Крит: {stats['crit_chance']:.1f}%
🔄 Уклонение: {stats['dodge_chance']:.1f}%
🛡 Блок: {stats['block_chance']:.1f}%

❤ HP: {d['hp']}/{d['max_hp'] + stats['hp_bonus']}
💎 Мана: {d['mana']}/{d['max_mana'] + stats['mana_bonus']}

<b>Навыки:</b>
{', '.join(stats['skills'][:10])}
"""
    
    if d['stat_points'] > 0:
        markup = types.InlineKeyboardMarkup(row_width=5)
        markup.add(
            types.InlineKeyboardButton("💪", callback_data="up_stat_strength"),
            types.InlineKeyboardButton("🏃", callback_data="up_stat_agility"),
            types.InlineKeyboardButton("🧠", callback_data="up_stat_intelligence"),
            types.InlineKeyboardButton("❤", callback_data="up_stat_vitality"),
            types.InlineKeyboardButton("🍀", callback_data="up_stat_luck")
        )
    else:
        markup = None
    
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("up_stat_"))
def upgrade_stat(call):
    stat = call.data.split("_")[2]
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data["stat_points"] <= 0:
        bot.answer_callback_query(call.id, "❌ Нет очков!")
        return
    
    if player.data["stats"][stat] >= 100:
        bot.answer_callback_query(call.id, "❌ Максимум!")
        return
    
    player.data["stats"][stat] += 1
    player.data["stat_points"] -= 1
    player.save()
    
    stat_names = {
        "strength": "Сила", "agility": "Ловкость",
        "intelligence": "Интеллект", "vitality": "Живучесть", "luck": "Удача"
    }
    
    bot.answer_callback_query(call.id, f"⬆ {stat_names[stat]}: {player.data['stats'][stat]}")
    stats(call.message)

# ==================== ЕЖЕДНЕВНЫЙ БОНУС ====================
@bot.message_handler(func=lambda m: m.text == "🎁 Ежедневный бонус")
def daily_bonus(message):
    user_id = message.from_user.id
    player = Player(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player.data["last_daily"] == today:
        bot.send_message(message.chat.id, "🎁 Вы уже получили бонус сегодня!")
        return
    
    bonus = random.randint(100, 500) + player.data["level"] * 10
    exp = random.randint(50, 200) + player.data["level"] * 5
    
    player.data["money"] += bonus
    player.data["exp"] += exp
    player.data["total_exp"] += exp
    player.data["last_daily"] = today
    
    # Шанс предмета
    if random.random() < 0.2:
        common_items = [k for k, v in items.items() if v.get("rarity") == "common"]
        if common_items:
            item = random.choice(common_items)
            player.data["inventory"].append(item)
            item_name = items[item]["name"]
        else:
            item_name = None
    else:
        item_name = None
    
    old_level = player.data["level"]
    check_level_up(player)
    player.save()
    
    text = f"<b>🎁 ЕЖЕДНЕВНЫЙ БОНУС</b>\n\n💰 Монет: +{bonus}\n✨ Опыта: +{exp}"
    
    if item_name:
        text += f"\n🎒 Предмет: {item_name}"
    
    if player.data["level"] > old_level:
        text += f"\n🎉 НОВЫЙ УРОВЕНЬ: {player.data['level']}!"
    
    bot.send_message(message.chat.id, text)

# ==================== ПОДЗЕМЕЛЬЯ ====================
@bot.message_handler(func=lambda m: m.text == "🏰 Подземелья")
def dungeon(message):
    text = """
<b>🏰 ПОДЗЕМЕЛЬЯ</b>

<b>🐺 Логово волка</b> (Ур.1-5)
Босс: Вожак стаи | 50-200💰

<b>🕷 Паучьи пещеры</b> (Ур.5-10)
Босс: Королева пауков | 100-400💰

<b>💀 Катакомбы</b> (Ур.10-15)
Босс: Некромант | 200-700💰

<b>🐉 Драконье логово</b> (Ур.15-25)
Босс: Древний дракон | 500-2000💰

<b>👹 Бездна</b> (Ур.25+)
Босс: Владыка бездны | 1000-5000💰
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🐺 Логово волка", callback_data="dungeon_1"),
        types.InlineKeyboardButton("🕷 Паучьи пещеры", callback_data="dungeon_2"),
        types.InlineKeyboardButton("💀 Катакомбы", callback_data="dungeon_3"),
        types.InlineKeyboardButton("🐉 Драконье логово", callback_data="dungeon_4"),
        types.InlineKeyboardButton("👹 Бездна", callback_data="dungeon_5")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dungeon_"))
def start_dungeon(call):
    level = int(call.data.split("_")[1])
    user_id = call.from_user.id
    player = Player(user_id)
    
    level_req = [1, 5, 10, 15, 25][level - 1]
    if player.data["level"] < level_req:
        bot.answer_callback_query(call.id, f"❌ Нужен {level_req} уровень!")
        return
    
    # Награды
    rewards = [(50, 200), (100, 400), (200, 700), (500, 2000), (1000, 5000)]
    min_r, max_r = rewards[level - 1]
    reward = random.randint(min_r, max_r) * player.data["level"] // 10
    exp = 50 * level * player.data["level"]
    
    # Шанс предмета
    drop = None
    if random.random() < 0.1 * level:
        rarities = ["common", "uncommon", "rare", "epic", "legendary"]
        possible = [k for k, v in items.items() 
                   if v.get("rarity") in rarities[:level]]
        if possible:
            drop = random.choice(possible)
            player.data["inventory"].append(drop)
    
    player.data["money"] += reward
    player.data["exp"] += exp
    player.data["total_exp"] += exp
    
    old_level = player.data["level"]
    check_level_up(player)
    player.save()
    
    bosses = ["Вожак стаи", "Королева пауков", "Некромант", "Дракон", "Владыка бездны"]
    
    text = f"<b>🏰 ДАНЖ ПРОЙДЕН!</b>\n\n"
    text += f"Босс: <b>{bosses[level-1]}</b>\n"
    text += f"💰 Награда: +{reward} монет\n"
    text += f"✨ Опыт: +{exp}\n"
    
    if drop:
        text += f"\n🎁 Найден предмет: <b>{items[drop]['name']}</b>!"
    
    if player.data["level"] > old_level:
        text += f"\n🎉 НОВЫЙ УРОВЕНЬ: <b>{player.data['level']}</b>!"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "✅ Данж пройден!")

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def check_level_up(player):
    level = player.data["level"]
    exp_needed = int(100 * (1.5 ** (level - 1)))
    
    leveled = False
    while player.data["exp"] >= exp_needed:
        player.data["exp"] -= exp_needed
        player.data["level"] += 1
        player.data["stat_points"] += 3
        player.data["skill_points"] += 1
        player.data["max_hp"] += 10
        player.data["max_mana"] += 5
        player.data["hp"] = player.data["max_hp"]
        player.data["mana"] = player.data["max_mana"]
        
        titles = {
            5: "Боец", 10: "Воитель", 15: "Рыцарь",
            20: "Ветеран", 25: "Мастер", 30: "Грандмастер",
            40: "Герой", 50: "Легенда", 75: "Полубог", 100: "Божество"
        }
        
        for req, title in titles.items():
            if player.data["level"] >= req and title not in player.data["titles_collected"]:
                player.data["titles_collected"].append(title)
                player.data["title"] = title
        
        level = player.data["level"]
        exp_needed = int(100 * (1.5 ** (level - 1)))
        leveled = True
    
    return leveled

@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def statistics(message):
    user_id = message.from_user.id
    d = Player(user_id).data
    
    winrate = (d["wins"] / d["total_duels"] * 100) if d["total_duels"] > 0 else 0
    
    text = f"""
<b>📊 СТАТИСТИКА</b>

<b>{d['first_name']}</b> | {d['title']}
⭐ Уровень: <b>{d['level']}</b>
📊 Рейтинг: <b>{d['rating']}</b>
💰 Баланс: <b>{d['money']}💰</b>

<b>Дуэли:</b>
🏆 Побед: {d['wins']}
💀 Поражений: {d['losses']}
🤝 Ничьих: {d['draws']}
📈 Винрейт: {winrate:.1f}%
🔥 Лучшая серия: {d['best_streak']}
⚔ Всего дуэлей: {d['total_duels']}

<b>Прогресс:</b>
✨ Опыт: {d['exp']}/{int(100 * (1.5 ** (d['level']-1)))}
📊 Всего опыта: {d['total_exp']}
🎒 Предметов: {len(d['inventory'])}
⚡ Очков статов: {d['stat_points']}
📜 Очков навыков: {d['skill_points']}
"""
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def balance(message):
    player = Player(message.from_user.id)
    bot.send_message(message.chat.id, 
        f"💰 Ваш баланс: <b>{player.data['money']} монет</b>")

# ==================== АДМИН-ПАНЕЛЬ ====================
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
        types.InlineKeyboardButton("💰 Выдать деньги", callback_data="adm_money"),
        types.InlineKeyboardButton("🎁 Выдать предмет", callback_data="adm_item"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>", reply_markup=markup)

@bot.message_handler(commands=['give_money'])
def give_money(message):
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
        bot.send_message(message.chat.id, "❌ /give_money [ID] [сумма]")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text.replace('/broadcast', '', 1).strip()
    if not text:
        return
    
    sent = 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 <b>Объявление:</b>\n{text}")
            sent += 1
        except:
            pass
    
    bot.send_message(message.chat.id, f"✅ Отправлено: {sent}")

# ==================== ЗАПУСК ====================
def main():
    print("=" * 60)
    print("⚔ ДУЭЛЬ БОТ v5.0 - ПОШАГОВАЯ СТРАТЕГИЯ ⚔")
    print("=" * 60)
    print(f"🕒 Запуск: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print(f"⚔ Предметов: {len(items)}")
    print(f"💎 Лимитированных: {len(limited_items)}")
    print("")
    print("🎯 Системы:")
    print("  • Пошаговая боевая система")
    print("  • Мана и выносливость")
    print("  • Элементальные взаимодействия")
    print("  • 80+ навыков")
    print("  • Стратегические дуэли")
    print("=" * 60)
    print("✅ Бот запущен!")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠ Ошибка: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
