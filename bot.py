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
import math

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = '8670879387:AAH70T6P0ZEn-rvPhQo7rhrNMl9wUKDkILI'
ADMIN_ID = 5356400377
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ==================== КОНСТАНТЫ ====================
BODY_PARTS = {
    "head": {"name": "👤 Голова", "multiplier": 1.5, "base_defense": 3},
    "body": {"name": "🦾 Тело", "multiplier": 1.0, "base_defense": 8},
    "legs": {"name": "🦿 Ноги", "multiplier": 0.7, "base_defense": 2}
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

# ==================== ФАЙЛЫ ====================
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
    'enchantments': 'enchantments.json',
    'matchmaking': 'matchmaking.json',
    'active_battles': 'active_battles.json'
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
        print(f"Error: {e}")

# ==================== ПРЕДМЕТЫ ====================
HELMETS = {
    "leather_cap": {"name": "🎓 Кожаная шапка", "defense": 3, "price": 60, "type": "helmet", "slot": "head", "rarity": "common", "level_req": 1},
    "iron_helmet": {"name": "⛑ Железный шлем", "defense": 8, "price": 250, "type": "helmet", "slot": "head", "rarity": "uncommon", "level_req": 6},
    "dragon_helmet": {"name": "🐉 Шлем дракона", "defense": 18, "price": 2000, "type": "helmet", "slot": "head", "rarity": "epic", "level_req": 20, "element": "fire"},
    "crown_of_wisdom": {"name": "👑 Корона мудрости", "defense": 12, "price": 3500, "type": "helmet", "slot": "head", "rarity": "legendary", "level_req": 28}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "defense": 5, "price": 80, "type": "armor", "slot": "body", "rarity": "common", "level_req": 1},
    "chainmail": {"name": "⛓ Кольчуга", "defense": 12, "price": 400, "type": "armor", "slot": "body", "rarity": "uncommon", "level_req": 8},
    "plate_armor": {"name": "🛡 Латный доспех", "defense": 22, "price": 1500, "type": "armor", "slot": "body", "rarity": "rare", "level_req": 15},
    "shadow_armor": {"name": "🌑 Теневая броня", "defense": 28, "price": 3500, "type": "armor", "slot": "body", "rarity": "epic", "level_req": 22, "element": "dark"},
    "phoenix_armor": {"name": "🦅 Броня феникса", "defense": 40, "price": 8000, "type": "armor", "slot": "body", "rarity": "legendary", "level_req": 30, "element": "fire"}
}

BOOTS = {
    "leather_boots": {"name": "👢 Кожаные сапоги", "defense": 2, "speed_bonus": 5, "price": 100, "type": "boots", "slot": "legs", "rarity": "common", "level_req": 1},
    "wind_boots": {"name": "🌪 Сапоги ветра", "defense": 4, "speed_bonus": 12, "price": 900, "type": "boots", "slot": "legs", "rarity": "rare", "level_req": 12},
    "blink_boots": {"name": "✨ Сапоги телепортации", "defense": 8, "speed_bonus": 20, "price": 4000, "type": "boots", "slot": "legs", "rarity": "epic", "level_req": 25},
    "hermes_boots": {"name": "👟 Сандалии Гермеса", "defense": 12, "speed_bonus": 30, "price": 12000, "type": "boots", "slot": "legs", "rarity": "legendary", "level_req": 35}
}

WEAPONS = {
    "rusty_sword": {"name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 1, "skills": ["quick_strike", "slash"]},
    "flame_blade": {"name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 7, "skills": ["fire_slash", "inferno_strike", "flame_wave"], "element": "fire"},
    "frost_axe": {"name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 10, "skills": ["frost_strike", "ice_shatter", "blizzard"], "element": "ice"},
    "storm_staff": {"name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500, "type": "weapon", "slot": "weapon", "rarity": "rare", "level_req": 14, "skills": ["lightning_bolt", "thunder_storm", "chain_lightning"], "element": "lightning"},
    "shadow_dagger": {"name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "slot": "weapon", "rarity": "epic", "level_req": 22, "skills": ["shadow_strike", "assassinate", "soul_drain"], "element": "dark"},
    "divine_spear": {"name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "slot": "weapon", "rarity": "legendary", "level_req": 28, "skills": ["holy_strike", "divine_judgment"], "element": "light"},
    "death_scythe": {"name": "💀 Коса смерти", "damage": (40, 65), "price": 12000, "type": "weapon", "slot": "weapon", "rarity": "mythic", "level_req": 35, "skills": ["reap", "death_sentence", "soul_harvest"], "element": "dark"}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 200, "price": 350, "type": "potion", "rarity": "rare", "level_req": 15}
}

ALL_ITEMS = {}
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(BOOTS)
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(POTIONS)

# ==================== НАВЫКИ ====================
SKILLS_DB = {
    "quick_strike": {"name": "⚡ Быстрый удар", "damage_mult": 0.8, "cooldown": 0, "speed": "fast", "description": "Мгновенная атака"},
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.2, "cooldown": 1, "speed": "normal", "description": "Базовый удар"},
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.5, "cooldown": 2, "element": "fire", "speed": "normal", "burn_chance": 25},
    "inferno_strike": {"name": "🌋 Инферно", "damage_mult": 2.2, "cooldown": 3, "element": "fire", "speed": "slow", "burn_chance": 50},
    "flame_wave": {"name": "🔥 Волна пламени", "damage_mult": 2.5, "cooldown": 4, "element": "fire", "speed": "very_slow", "aoe": True},
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.4, "cooldown": 2, "element": "ice", "speed": "normal", "freeze_chance": 20},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.0, "cooldown": 3, "element": "ice", "speed": "slow", "freeze_chance": 40},
    "blizzard": {"name": "🌨 Метель", "damage_mult": 2.4, "cooldown": 4, "element": "ice", "speed": "very_slow", "aoe": True},
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.6, "cooldown": 2, "element": "lightning", "speed": "fast", "stun_chance": 15},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.3, "cooldown": 3, "element": "lightning", "speed": "slow", "stun_chance": 30},
    "chain_lightning": {"name": "⚡ Цепная молния", "damage_mult": 1.8, "cooldown": 3, "element": "lightning", "speed": "normal", "chain": True},
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.6, "cooldown": 2, "element": "dark", "speed": "fast", "poison_chance": 20},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.2, "cooldown": 4, "element": "dark", "speed": "very_slow", "ignore_defense": 40},
    "soul_drain": {"name": "💀 Похищение души", "damage_mult": 2.0, "cooldown": 3, "element": "dark", "speed": "slow", "life_steal": 40},
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.5, "cooldown": 2, "element": "light", "speed": "normal"},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 2.8, "cooldown": 3, "element": "light", "speed": "slow", "ignore_defense": 30},
    "reap": {"name": "💀 Жатва", "damage_mult": 2.5, "cooldown": 3, "element": "dark", "speed": "slow", "life_steal": 30},
    "death_sentence": {"name": "☠ Смертный приговор", "damage_mult": 4.0, "cooldown": 5, "element": "dark", "speed": "very_slow", "ignore_defense": 60},
    "soul_harvest": {"name": "👻 Сбор душ", "damage_mult": 2.8, "cooldown": 4, "element": "dark", "speed": "slow", "life_steal": 50}
}

# Загрузка данных
items = load_json(DATA_FILES['items'], ALL_ITEMS)
limited_items = load_json(DATA_FILES['limited'], {})
users = load_json(DATA_FILES['users'], {})
clans = load_json(DATA_FILES['clans'], {})
tournaments = load_json(DATA_FILES['tournaments'], {})
market_listings = load_json(DATA_FILES['market'], {})
dungeon_progress = load_json(DATA_FILES['dungeons'], {})
events = load_json(DATA_FILES['events'], {})
banned_users = load_json(DATA_FILES['bans'], {})
enchantments_data = load_json(DATA_FILES['enchantments'], {})
matchmaking_queue = load_json(DATA_FILES['matchmaking'], {"queue_pvp": [], "queue_ranked": [], "queue_hardcore": [], "queue_sparring": []})

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
                "settings": {"notifications": True, "duel_requests": True},
                "battle_history": [],
                "dungeons_completed": 0,
                "items_found": 0,
                "tournament_wins": 0,
                "events_participated": 0
            }
            self.save()
    
    @property
    def data(self):
        return users.get(self.user_id, {})
    
    def save(self):
        save_json(DATA_FILES['users'], users)
    
    def get_defense_for_part(self, part):
        """Получить защиту для конкретной части тела"""
        base_def = BODY_PARTS.get(part, {}).get("base_defense", 0)
        bonus_def = 0
        
        # Проверяем экипировку на этой части
        slot_map = {"head": "head", "body": "body", "legs": "legs"}
        slot = slot_map.get(part)
        if slot:
            ik = self.data["equipment"].get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                if item and "defense" in item:
                    bonus_def += item["defense"]
        
        # Зачарования
        for ik, ench in self.data.get("enchantments", {}).items():
            if ench.get("effect") == "defense_bonus":
                # Проверяем, надет ли этот предмет
                if ik in self.data["equipment"].values():
                    bonus_def += ench.get("value", 0)
        
        return base_def + bonus_def
    
    def get_weapon_skills(self):
        """Получить навыки оружия"""
        weapon_key = self.data["equipment"].get("weapon")
        if not weapon_key:
            return ["quick_strike", "slash"]
        
        weapon = items.get(weapon_key) or limited_items.get(weapon_key)
        if weapon and "skills" in weapon:
            return weapon["skills"]
        
        return ["quick_strike", "slash"]

# ==================== ДУЭЛЬ ====================
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
        self.timeout_turn = 60  # секунд на ход
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        # Базовое HP (одинаковое)
        base_hp = 100 + max(self.p1.data["level"], self.p2.data["level"]) * 5
        self.p1_hp = base_hp
        self.p2_hp = base_hp
        self.p1_max_hp = base_hp
        self.p2_max_hp = base_hp
        
        self.p1_mp = 50
        self.p2_mp = 50
        self.p1_max_mp = 50
        self.p2_max_mp = 50
        
        # Очерёдность: p1_defend -> p2_attack -> p2_defend -> p1_attack
        self.phase = "p1_defend"  # p1_defend, p2_attack, p2_defend, p1_attack
        self.p1_defend = None
        self.p2_defend = None
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Эффекты
        self.p1_effects = []
        self.p2_effects = []
        
        # Время последнего хода
        self.last_action_time = datetime.now()
        
        self._save_battle()
    
    def _save_battle(self):
        battles = load_json(DATA_FILES['active_battles'], {})
        battles[self.battle_id] = {
            "p1_id": self.p1_id, "p2_id": self.p2_id,
            "type": self.duel_type, "bet": self.bet,
            "phase": self.phase, "turn": self.turn
        }
        save_json(DATA_FILES['active_battles'], battles)
    
    def _delete_battle(self):
        battles = load_json(DATA_FILES['active_battles'], {})
        if self.battle_id in battles:
            del battles[self.battle_id]
        save_json(DATA_FILES['active_battles'], battles)
    
    def get_player_name(self, num):
        return self.p1.data["first_name"] if num == 1 else self.p2.data["first_name"]
    
    def get_player_chat_id(self, num):
        return int(self.p1_id) if num == 1 else int(self.p2_id)
    
    def get_available_skills(self, player_num):
        player = self.p1 if player_num == 1 else self.p2
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        
        weapon_skills = player.get_weapon_skills()
        available = []
        
        for sid in weapon_skills:
            if sid in SKILLS_DB:
                cd = cooldowns.get(sid, 0)
                if cd <= 0:
                    available.append(sid)
        
        return available
    
    def set_defend(self, player_num, part):
        if player_num == 1 and self.phase == "p1_defend":
            self.p1_defend = part
            self.phase = "p2_attack"
            self.last_action_time = datetime.now()
            self._save_battle()
            return True
        elif player_num == 2 and self.phase == "p2_defend":
            self.p2_defend = part
            self.phase = "p1_attack"
            self.last_action_time = datetime.now()
            self._save_battle()
            return True
        return False
    
    def execute_attack(self, attacker_num, skill_id, target_part):
        """Выполнить атаку"""
        if attacker_num == 1 and self.phase != "p1_attack":
            return "Не ваша очередь атаковать!"
        if attacker_num == 2 and self.phase != "p2_attack":
            return "Не ваша очередь атаковать!"
        
        if skill_id not in SKILLS_DB:
            return "Навык не найден!"
        
        skill = SKILLS_DB[skill_id]
        cooldowns = self.p1_cooldowns if attacker_num == 1 else self.p2_cooldowns
        
        if cooldowns.get(skill_id, 0) > 0:
            return "Навык на перезарядке!"
        
        attacker = self.p1 if attacker_num == 1 else self.p2
        defender = self.p2 if attacker_num == 1 else self.p1
        
        defender_num = 2 if attacker_num == 1 else 1
        defend_part = self.p2_defend if attacker_num == 1 else self.p1_defend
        
        # Расчёт урона
        weapon_key = attacker.data["equipment"].get("weapon")
        weapon = None
        if weapon_key:
            weapon = items.get(weapon_key) or limited_items.get(weapon_key)
        
        base_damage = 10
        if weapon and "damage" in weapon:
            base_damage = random.randint(weapon["damage"][0], weapon["damage"][1])
        
        damage = int(base_damage * skill.get("damage_mult", 1.0))
        
        # Бонус части тела
        body_mult = BODY_PARTS.get(target_part, {}).get("multiplier", 1.0)
        damage = int(damage * body_mult)
        
        # Проверка защиты
        blocked = False
        if defend_part and defend_part == target_part:
            defense = defender.get_defense_for_part(target_part)
            reduction = defense / (defense + 50)
            damage = int(damage * (1 - reduction))
            blocked = True
        
        # Игнорирование защиты
        if "ignore_defense" in skill:
            ignore = skill["ignore_defense"] / 100
            damage = int(damage * (1 + ignore))
        
        # Нанесение урона
        if defender_num == 1:
            self.p1_hp = max(0, self.p1_hp - damage)
        else:
            self.p2_hp = max(0, self.p2_hp - damage)
        
        # Лог
        attacker_name = self.get_player_name(attacker_num)
        defender_name = self.get_player_name(defender_num)
        target_name = BODY_PARTS.get(target_part, {}).get("name", "тело")
        skill_name = skill.get("name", "атака")
        
        block_text = " (ЗАБЛОКИРОВАНО)" if blocked else ""
        log_text = f"⚔ {attacker_name} → {skill_name} → {target_name} {defender_name}: -{damage} HP{block_text}"
        
        self.log_p1.append(log_text)
        self.log_p2.append(log_text)
        
        # Эффекты
        self._apply_effects(defender_num, skill)
        
        # Вампиризм
        if "life_steal" in skill:
            heal = int(damage * skill["life_steal"] / 100)
            if attacker_num == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            self.log_p1.append(f"💚 Вампиризм +{heal} HP")
            self.log_p2.append(f"💚 Вампиризм +{heal} HP")
        
        # Кулдауны
        if "cooldown" in skill and skill["cooldown"] > 0:
            cooldowns[skill_id] = skill["cooldown"]
        
        # Уменьшение кулдаунов
        for sid in list(cooldowns.keys()):
            cooldowns[sid] -= 1
            if cooldowns[sid] <= 0:
                del cooldowns[sid]
        
        # Смена фазы
        if attacker_num == 2:
            self.phase = "p2_defend"
        elif attacker_num == 1:
            self.phase = "p1_defend"
            self.turn += 1
        
        self.last_action_time = datetime.now()
        self._save_battle()
        
        # Проверка завершения
        if self.p1_hp <= 0:
            self.active = False
            self.winner = 2
        elif self.p2_hp <= 0:
            self.active = False
            self.winner = 1
        elif self.turn > self.max_turns:
            self.active = False
            self.winner = 1 if self.p1_hp > self.p2_hp else 2 if self.p2_hp > self.p1_hp else 0
        
        return "OK"
    
    def _apply_effects(self, target_num, skill):
        effects = []
        if "burn_chance" in skill and random.random() * 100 < skill["burn_chance"]:
            effects.append({"type": "burn", "duration": 3, "damage": 10})
        if "freeze_chance" in skill and random.random() * 100 < skill["freeze_chance"]:
            effects.append({"type": "freeze", "duration": 2, "skip_next": True})
        if "stun_chance" in skill and random.random() * 100 < skill["stun_chance"]:
            effects.append({"type": "stun", "duration": 1})
        if "poison_chance" in skill and random.random() * 100 < skill["poison_chance"]:
            effects.append({"type": "poison", "duration": 4, "damage": 12})
        
        if target_num == 1:
            self.p1_effects.extend(effects)
        else:
            self.p2_effects.extend(effects)
    
    def process_effects(self, player_num):
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        hp = self.p1_hp if player_num == 1 else self.p2_hp
        
        for eff in effects[:]:
            if "damage" in eff:
                hp -= eff["damage"]
                self.log_p1.append(f"🔥 Эффект -{eff['damage']} HP")
                self.log_p2.append(f"🔥 Эффект -{eff['damage']} HP")
            eff["duration"] -= 1
            if eff["duration"] <= 0:
                effects.remove(eff)
        
        if player_num == 1:
            self.p1_hp = max(0, hp)
        else:
            self.p2_hp = max(0, hp)
    
    def check_timeout(self):
        """Проверка таймаута хода"""
        elapsed = (datetime.now() - self.last_action_time).total_seconds()
        if elapsed > self.timeout_turn:
            self.active = False
            if self.phase in ["p1_defend", "p1_attack"]:
                self.winner = 2  # P1 не сделал ход
            else:
                self.winner = 1  # P2 не сделал ход
            return True
        return False
    
    def get_state_text(self, player_num):
        """Текст состояния для конкретного игрока"""
        log = self.log_p1 if player_num == 1 else self.log_p2
        
        p1_hp_pct = self.p1_hp / self.p1_max_hp * 100
        p2_hp_pct = self.p2_hp / self.p2_max_hp * 100
        
        def bar(pct, cur, mx):
            f = int(pct / 10)
            e = 10 - f
            return f"[{'█'*f}{'░'*e}] {cur}/{mx} ({pct:.0f}%)"
        
        text = f"""
<b>⚔ ДУЭЛЬ #{self.battle_id}</b>
━━━━━━━━━━━━━━━━━━━━
Ход: <b>{self.turn}</b> | Ставка: <b>{self.bet}💰</b>

<b>{self.get_player_name(1)}</b>
❤ {bar(p1_hp_pct, self.p1_hp, self.p1_max_hp)}
💎 MP: {self.p1_mp}/{self.p1_max_mp}
🛡 Защита: {BODY_PARTS.get(self.p1_defend, {}).get('name', 'Не выбрана') if self.p1_defend else 'Не выбрана'}

<b>{self.get_player_name(2)}</b>
❤ {bar(p2_hp_pct, self.p2_hp, self.p2_max_hp)}
💎 MP: {self.p2_mp}/{self.p2_max_mp}
🛡 Защита: {BODY_PARTS.get(self.p2_defend, {}).get('name', 'Не выбрана') if self.p2_defend else 'Не выбрана'}
━━━━━━━━━━━━━━━━━━━━
"""
        
        # Инструкция
        if player_num == 1:
            if self.phase == "p1_defend":
                text += "\n🛡 <b>ВЫБЕРИТЕ ЧАСТЬ ТЕЛА ДЛЯ ЗАЩИТЫ:</b>"
            elif self.phase == "p1_attack":
                text += "\n⚔ <b>ВАША ОЧЕРЕДЬ АТАКОВАТЬ!</b>"
                text += "\nВыберите цель и навык:"
            else:
                text += "\n⏳ <b>ОЖИДАНИЕ ХОДА ПРОТИВНИКА...</b>"
        else:
            if self.phase == "p2_defend":
                text += "\n🛡 <b>ВЫБЕРИТЕ ЧАСТЬ ТЕЛА ДЛЯ ЗАЩИТЫ:</b>"
            elif self.phase == "p2_attack":
                text += "\n⚔ <b>ВАША ОЧЕРЕДЬ АТАКОВАТЬ!</b>"
                text += "\nВыберите цель и навык:"
            else:
                text += "\n⏳ <b>ОЖИДАНИЕ ХОДА ПРОТИВНИКА...</b>"
        
        # Эффекты
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        if effects:
            text += "\n<b>Эффекты:</b> " + ", ".join([f"{e['type']}({e['duration']})" for e in effects])
        
        # Лог
        if log:
            text += f"\n<i>{log[-1]}</i>"
        
        return text

# ==================== ХРАНИЛИЩЕ ДУЭЛЕЙ ====================
active_duels = {}  # {user_id: duel_instance}

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
    
    # Фикс: определяем username
    username = message.from_user.username
    first_name = message.from_user.first_name or "Игрок"
    
    if not username:
        # Если нет username, используем ID
        username = f"id{user_id}"
    
    # Обновляем данные если пользователь уже существует
    player = Player(user_id, username, first_name)
    # Всегда обновляем username при старте
    player.data["username"] = username
    player.data["first_name"] = first_name
    player.save()
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v11.0 ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!
Ваш @username: <b>@{username}</b>

🎯 <b>НОВОЕ:</b>
• Пошаговые дуэли: защита → атака по очереди!
• Броня уменьшает урон (НЕ даёт HP!)
• 3+ навыка у каждого оружия
• Кулдауны: сильные атаки дольше
• Данжи с несколькими боссами
• Турниры с сеткой
• Ивенты с реальными наградами
• Таймаут хода = 60 сек

💰 Старт: <b>500 монет</b>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль (бот)", callback_data="duel_quick"),
        types.InlineKeyboardButton("👥 PvP дуэль", callback_data="duel_pvp"),
        types.InlineKeyboardButton("🏆 Рейтинговая", callback_data="duel_ranked"),
        types.InlineKeyboardButton("💀 Хардкор", callback_data="duel_hardcore"),
        types.InlineKeyboardButton("🎯 Спарринг", callback_data="duel_sparring")
    )
    
    text = """
<b>⚔️ ДУЭЛИ</b>

<b>Система боя:</b>
🛡 Сначала защита
⚔ Потом атака противника
🛡 Потом защита противника
⚔ Потом ваша атака

<i>Броня уменьшает урон, а не даёт HP!</i>
"""
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="hero_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="hero_inventory"),
        types.InlineKeyboardButton("👁 Экипировка", callback_data="hero_equipped"),
        types.InlineKeyboardButton("💊 Лечение", callback_data="hero_heal")
    )
    bot.send_message(message.chat.id, "<b>👤 ГЕРОЙ</b>", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🏪 Торговля")
def trade_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛒 Магазин", callback_data="shop_menu"),
        types.InlineKeyboardButton("💎 Лимитированные", callback_data="limited_menu"),
        types.InlineKeyboardButton("🎁 Бонус", callback_data="daily_bonus"),
        types.InlineKeyboardButton("💱 Рынок", callback_data="market_menu")
    )
    bot.send_message(message.chat.id, "<b>🏪 ТОРГОВЛЯ</b>", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🌍 Мир")
def world_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🏰 Подземелья", callback_data="dungeons_menu"),
        types.InlineKeyboardButton("🛡 Кланы", callback_data="clans_menu"),
        types.InlineKeyboardButton("🏟 Турниры", callback_data="tournaments_menu"),
        types.InlineKeyboardButton("🌍 Ивенты", callback_data="events_menu"),
        types.InlineKeyboardButton("📊 Топ", callback_data="top_menu"),
        types.InlineKeyboardButton("ℹ Помощь", callback_data="help_menu")
    )
    bot.send_message(message.chat.id, "<b>🌍 МИР</b>", reply_markup=markup)

# ==================== ДУЭЛИ ====================
@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_"))
def duel_menu_handler(call):
    duel_type = call.data.split("_")[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    if duel_type == "quick":
        markup = types.InlineKeyboardMarkup(row_width=3)
        for bet in [50, 100, 200, 500, 1000]:
            markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"start_quick_{bet}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
        
        bot.edit_message_text(
            f"<b>⚡ БЫСТРАЯ ДУЭЛЬ (БОТ)</b>\n💰 Баланс: <b>{player.data['money']}💰</b>",
            call.message.chat.id, call.message.message_id, reply_markup=markup
        )
    
    elif duel_type == "pvp":
        markup = types.InlineKeyboardMarkup(row_width=3)
        for bet in [50, 100, 200, 500, 1000]:
            markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"find_pvp_{bet}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
        
        bot.edit_message_text(
            f"<b>👥 PvP ДУЭЛЬ</b>\n💰 Баланс: <b>{player.data['money']}💰</b>\n🔍 Поиск соперника...",
            call.message.chat.id, call.message.message_id, reply_markup=markup
        )
    
    elif duel_type == "ranked":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🔍 Найти соперника", callback_data="find_ranked_100"),
            types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels")
        )
        
        bot.edit_message_text(
            f"<b>🏆 РЕЙТИНГОВАЯ</b>\nСтавка: 100💰\n🔍 Поиск соперника...",
            call.message.chat.id, call.message.message_id, reply_markup=markup
        )
    
    elif duel_type == "hardcore":
        markup = types.InlineKeyboardMarkup(row_width=3)
        for bet in [500, 1000, 2000, 5000]:
            markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"find_hardcore_{bet}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
        
        bot.edit_message_text(
            f"<b>💀 ХАРДКОР</b>\n💰 Баланс: <b>{player.data['money']}💰</b>",
            call.message.chat.id, call.message.message_id, reply_markup=markup
        )
    
    elif duel_type == "sparring":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🔍 Найти соперника", callback_data="find_sparring_0"),
            types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels")
        )
        
        bot.edit_message_text(
            "<b>🎯 СПАРРИНГ</b>\nБез ставок!\n🔍 Поиск соперника...",
            call.message.chat.id, call.message.message_id, reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_duels")
def back_to_duels_handler(call):
    duel_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("start_quick_"))
def start_quick_duel(call):
    user_id = call.from_user.id
    bet = int(call.data.split("_")[2])
    player = Player(user_id)
    
    if player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    player.data["money"] -= bet
    player.save()
    
    # Создаём бота
    bot_id = f"bot_{random.randint(100000, 999999)}"
    users[bot_id] = create_bot_player(max(1, player.data["level"] - 3), player.data["level"] + 3)
    save_json(DATA_FILES['users'], users)
    
    # Создаём дуэль
    duel = DuelInstance(user_id, bot_id, "quick", bet)
    active_duels[str(user_id)] = duel
    
    bot.edit_message_text("⚔ Дуэль начинается! Выберите защиту.", call.message.chat.id, call.message.message_id)
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
    bot.answer_callback_query(call.id, "⚔ Начали!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("find_"))
def find_opponent(call):
    parts = call.data.split("_")
    duel_type = parts[1]
    bet = int(parts[2])
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    # Проверка очереди
    queue_key = f"queue_{duel_type}"
    queue = matchmaking_queue.get(queue_key, [])
    
    # Убираем себя
    queue = [q for q in queue if q["user_id"] != user_id]
    
    if queue:
        # Нашли соперника
        opponent = queue.pop(0)
        matchmaking_queue[queue_key] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        # Снимаем ставку
        if bet > 0:
            player.data["money"] -= bet
            player.save()
            opp = Player(opponent["user_id"])
            opp.data["money"] -= bet
            opp.save()
        
        # Создаём дуэль
        duel = DuelInstance(opponent["user_id"], user_id, duel_type, bet)
        active_duels[user_id] = duel
        active_duels[opponent["user_id"]] = duel
        
        # Отправляем сообщения обоим
        bot.edit_message_text("⚔ Соперник найден! Выберите защиту.", call.message.chat.id, call.message.message_id)
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        
        # Отправляем противнику
        try:
            opp_chat_id = int(opponent["user_id"])
            bot.send_message(opp_chat_id, "⚔ Соперник найден! Дуэль начинается!")
            show_duel_interface(opp_chat_id, None, duel, opponent["user_id"])
        except:
            pass
    else:
        # Ставим в очередь
        queue.append({"user_id": user_id, "type": duel_type, "bet": bet})
        matchmaking_queue[queue_key] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        # Запускаем таймер на бота
        threading.Timer(5.0, start_bot_duel, args=[call.message.chat.id, call.message.message_id, user_id, duel_type, bet]).start()
        
        bot.edit_message_text("🔍 Поиск соперника... Если не найдём — будет бот!", call.message.chat.id, call.message.message_id)

def create_bot_player(min_level, max_level):
    """Создать бота с уровнем между min и max"""
    level = random.randint(max(1, min_level), max(1, max_level))
    bot_id = f"bot_{random.randint(100000, 999999)}"
    
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    for slot, itype in [("head", "helmet"), ("body", "armor"), ("legs", "boots")]:
        slot_items = [k for k, v in items.items() if v.get("type") == itype and v.get("level_req", 1) <= level]
        if slot_items and random.random() < 0.7:
            equip[slot] = random.choice(slot_items)
    
    weapon_items = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= level]
    if weapon_items:
        equip["weapon"] = random.choice(weapon_items)
    
    return {
        "username": f"Bot_{level}", "first_name": f"🤖 Бот Lv.{level}",
        "money": 0, "level": level, "exp": 0, "total_exp": 0,
        "hp": 100 + level * 5, "max_hp": 100 + level * 5,
        "mana": 50, "max_mana": 50,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000 + level * 10,
        "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Бот", "titles_collected": ["Бот"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0,
        "items_found": 0, "tournament_wins": 0, "events_participated": 0
    }

def start_bot_duel(chat_id, message_id, user_id, duel_type, bet):
    """Запустить дуэль с ботом если не нашли соперника"""
    if str(user_id) in active_duels:
        return  # Уже есть дуэль
    
    player = Player(user_id)
    
    # Создаём бота
    bot_id = f"bot_{random.randint(100000, 999999)}"
    users[bot_id] = create_bot_player(max(1, player.data["level"] - 3), player.data["level"] + 3)
    save_json(DATA_FILES['users'], users)
    
    if bet > 0:
        player.data["money"] -= bet
        player.save()
    
    duel = DuelInstance(user_id, bot_id, duel_type, bet)
    active_duels[str(user_id)] = duel
    
    # Бот выбирает защиту (фаза p2_defend начнётся после p1_defend)
    # Но сначала p1 должен выбрать защиту
    
    try:
        bot.edit_message_text("⚔ Соперник не найден. Бой с ботом! Выберите защиту.", chat_id, message_id)
    except:
        pass
    
    show_duel_interface(chat_id, message_id, duel, user_id)

def show_duel_interface(chat_id, message_id, duel, user_id):
    """Показать интерфейс дуэли"""
    if not duel or not duel.active:
        if duel:
            finish_duel(duel)
        return
    
    player_num = 1 if str(user_id) == duel.p1_id else 2
    state_text = duel.get_state_text(player_num)
    phase = duel.phase
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Определяем, может ли игрок действовать
    can_defend = (player_num == 1 and phase == "p1_defend") or (player_num == 2 and phase == "p2_defend")
    can_attack = (player_num == 1 and phase == "p1_attack") or (player_num == 2 and phase == "p2_attack")
    
    if can_defend:
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']}",
                callback_data=f"defend_{part}"
            ))
    
    elif can_attack:
        # Сначала цель
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🎯 {data['name']}",
                callback_data=f"target_{part}"
            ))
    
    else:
        markup.add(types.InlineKeyboardButton("⏳ Ожидание...", callback_data="wait_turn"))
    
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh_duel"))
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="surrender_duel"))
    
    if message_id:
        try:
            bot.edit_message_text(state_text[:4000], chat_id, message_id, reply_markup=markup)
        except:
            pass
    else:
        try:
            bot.send_message(chat_id, state_text[:4000], reply_markup=markup)
        except:
            pass

# Временное хранилище для выбора цели
target_storage = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("target_"))
def target_selected(call):
    user_id = str(call.from_user.id)
    part = call.data.split("_")[1]
    
    duel = active_duels.get(user_id)
    if not duel or not duel.active:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    # Сохраняем цель
    target_storage[user_id] = part
    
    # Показываем навыки
    player_num = 1 if user_id == duel.p1_id else 2
    skills = duel.get_available_skills(player_num)
    
    state_text = duel.get_state_text(player_num)
    state_text += f"\n🎯 Цель: <b>{BODY_PARTS[part]['name']}</b>\n<b>Выберите навык:</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for sid in skills:
        skill = SKILLS_DB.get(sid, {})
        name = skill.get("name", sid)
        dmg = skill.get("damage_mult", 1.0)
        cd = skill.get("cooldown", 0)
        speed = skill.get("speed", "normal")
        
        markup.add(types.InlineKeyboardButton(
            f"{name} (x{dmg}) [CD:{cd}]",
            callback_data=f"skill_{sid}"
        ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_target"))
    
    try:
        bot.edit_message_text(state_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "back_to_target")
def back_to_target(call):
    user_id = str(call.from_user.id)
    duel = active_duels.get(user_id)
    if duel:
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("skill_"))
def skill_selected(call):
    user_id = str(call.from_user.id)
    skill_id = call.data.split("_")[1]
    
    duel = active_duels.get(user_id)
    if not duel or not duel.active:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    target = target_storage.get(user_id, "body")
    player_num = 1 if user_id == duel.p1_id else 2
    
    result = duel.execute_attack(player_num, skill_id, target)
    
    if result != "OK":
        bot.answer_callback_query(call.id, result)
        return
    
    bot.answer_callback_query(call.id, "⚔ Атака!")
    
    # Если бот - автоматически делаем его ход
    other_id = duel.p2_id if player_num == 1 else duel.p1_id
    if other_id.startswith("bot_") and duel.active:
        other_num = 3 - player_num
        
        # Бот защищается если надо
        if (other_num == 1 and duel.phase == "p1_defend") or (other_num == 2 and duel.phase == "p2_defend"):
            bot_part = random.choice(list(BODY_PARTS.keys()))
            duel.set_defend(other_num, bot_part)
        
        # Бот атакует если надо
        if (other_num == 2 and duel.phase == "p2_attack") or (other_num == 1 and duel.phase == "p1_attack"):
            bot_skills = duel.get_available_skills(other_num)
            if bot_skills:
                bot_skill = random.choice(bot_skills)
                bot_target = random.choice(list(BODY_PARTS.keys()))
                duel.execute_attack(other_num, bot_skill, bot_target)
    
    # Обновляем интерфейс для текущего игрока
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
    
    # Отправляем обновление противнику если это не бот
    other_player = duel.p2_id if player_num == 1 else duel.p1_id
    if not other_player.startswith("bot_"):
        try:
            other_chat_id = int(other_player)
            show_duel_interface(other_chat_id, None, duel, other_player)
        except:
            pass
    
    # Проверяем завершение
    if not duel.active:
        finish_duel(duel)

@bot.callback_query_handler(func=lambda call: call.data.startswith("defend_"))
def defend_selected(call):
    user_id = str(call.from_user.id)
    part = call.data.split("_")[1]
    
    duel = active_duels.get(user_id)
    if not duel or not duel.active:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    player_num = 1 if user_id == duel.p1_id else 2
    if not duel.set_defend(player_num, part):
        bot.answer_callback_query(call.id, "❌ Не ваша очередь!")
        return
    
    bot.answer_callback_query(call.id, f"🛡 Защита: {BODY_PARTS[part]['name']}")
    
    # Если бот - делаем его ход
    other_id = duel.p2_id if player_num == 1 else duel.p1_id
    if other_id.startswith("bot_") and duel.active:
        other_num = 3 - player_num
        
        if (other_num == 2 and duel.phase == "p2_attack") or (other_num == 1 and duel.phase == "p1_attack"):
            bot_skills = duel.get_available_skills(other_num)
            if bot_skills:
                bot_skill = random.choice(bot_skills)
                bot_target = random.choice(list(BODY_PARTS.keys()))
                duel.execute_attack(other_num, bot_skill, bot_target)
        
        if duel.active and ((other_num == 1 and duel.phase == "p1_defend") or (other_num == 2 and duel.phase == "p2_defend")):
            bot_part = random.choice(list(BODY_PARTS.keys()))
            duel.set_defend(other_num, bot_part)
    
    # Обновляем интерфейс
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
    
    # Уведомляем противника
    other_player = duel.p2_id if player_num == 1 else duel.p1_id
    if not other_player.startswith("bot_"):
        try:
            other_chat_id = int(other_player)
            show_duel_interface(other_chat_id, None, duel, other_player)
        except:
            pass
    
    if not duel.active:
        finish_duel(duel)

@bot.callback_query_handler(func=lambda call: call.data in ["refresh_duel", "wait_turn", "surrender_duel"])
def duel_actions(call):
    user_id = str(call.from_user.id)
    duel = active_duels.get(user_id)
    
    if call.data == "refresh_duel":
        if duel and duel.active:
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
            bot.answer_callback_query(call.id, "✅ Обновлено")
        else:
            bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
    
    elif call.data == "wait_turn":
        if duel and duel.active:
            # Проверяем таймаут
            if duel.check_timeout():
                finish_duel(duel)
                return
            
            # Проверяем ход бота
            other_id = duel.p2_id if str(user_id) == duel.p1_id else duel.p1_id
            if other_id.startswith("bot_") and duel.active:
                other_num = 2 if str(user_id) == duel.p1_id else 1
                
                if (other_num == 1 and duel.phase == "p1_defend") or (other_num == 2 and duel.phase == "p2_defend"):
                    duel.set_defend(other_num, random.choice(list(BODY_PARTS.keys())))
                
                if (other_num == 2 and duel.phase == "p2_attack") or (other_num == 1 and duel.phase == "p1_attack"):
                    bot_skills = duel.get_available_skills(other_num)
                    if bot_skills:
                        duel.execute_attack(other_num, random.choice(bot_skills), random.choice(list(BODY_PARTS.keys())))
            
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
            bot.answer_callback_query(call.id, "✅")
        else:
            bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
    
    elif call.data == "surrender_duel":
        if duel and duel.active:
            duel.active = False
            duel.winner = 2 if str(user_id) == duel.p1_id else 1
            finish_duel(duel)

def finish_duel(duel):
    """Завершение дуэли и рассылка результатов"""
    # Очистка
    for uid in [duel.p1_id, duel.p2_id]:
        if uid in active_duels and active_duels[uid].battle_id == duel.battle_id:
            del active_duels[uid]
    
    duel._delete_battle()
    
    # Удаление ботов
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") and uid in users:
            del users[uid]
    save_json(DATA_FILES['users'], users)
    
    # Формируем результаты
    if duel.winner == 0:
        result_text = f"<b>🤝 НИЧЬЯ!</b>\nХодов: {duel.turn}\n"
    else:
        winner_id = duel.p1_id if duel.winner == 1 else duel.p2_id
        loser_id = duel.p2_id if duel.winner == 1 else duel.p1_id
        
        if not winner_id.startswith("bot_"):
            winner = Player(winner_id)
            winner.data["wins"] += 1
            winner.data["win_streak"] += 1
            winner.data["total_duels"] += 1
            if winner.data["win_streak"] > winner.data["best_streak"]:
                winner.data["best_streak"] = winner.data["win_streak"]
            
            if duel.bet > 0:
                winner.data["money"] += duel.bet * 2
            
            exp_gain = duel.turn * 5 + duel.bet // 2
            winner.data["exp"] += exp_gain
            winner.data["total_exp"] += exp_gain
            check_level_up(winner)
            winner.save()
        
        if not loser_id.startswith("bot_"):
            loser = Player(loser_id)
            loser.data["losses"] += 1
            loser.data["win_streak"] = 0
            loser.data["total_duels"] += 1
            exp_gain = duel.turn * 2 + duel.bet // 5
            loser.data["exp"] += exp_gain
            loser.data["total_exp"] += exp_gain
            check_level_up(loser)
            loser.save()
        
        winner_name = duel.get_player_name(duel.winner)
        loser_name = duel.get_player_name(3 - duel.winner)
        
        result_text = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

👑 <b>{winner_name}</b> побеждает!
💀 <b>{loser_name}</b> проигрывает

💰 Ставка: <b>{duel.bet}💰</b>
📊 Ходов: <b>{duel.turn}</b>
"""
    
    # Отправляем результат обоим игрокам
    for uid in [duel.p1_id, duel.p2_id]:
        if not uid.startswith("bot_"):
            try:
                bot.send_message(int(uid), result_text)
            except:
                pass

def check_level_up(player):
    level = player.data["level"]
    exp_needed = int(100 * (1.5 ** (level - 1)))
    
    while player.data["exp"] >= exp_needed:
        player.data["exp"] -= exp_needed
        player.data["level"] += 1
        player.data["max_hp"] += 10
        player.data["max_mana"] += 5
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

# ==================== МАГАЗИН ====================
@bot.callback_query_handler(func=lambda call: call.data == "shop_menu")
def shop_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚔ Оружие", callback_data="shop_weapon"),
        types.InlineKeyboardButton("👤 Шлемы", callback_data="shop_helmet"),
        types.InlineKeyboardButton("🦾 Броня", callback_data="shop_armor"),
        types.InlineKeyboardButton("🦿 Обувь", callback_data="shop_boots"),
        types.InlineKeyboardButton("🧪 Зелья", callback_data="shop_potion")
    )
    
    player = Player(call.from_user.id)
    bot.edit_message_text(
        f"<b>🛒 МАГАЗИН</b>\n💰 <b>{player.data['money']}💰</b>",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("shop_"))
def shop_category_handler(call):
    cat = call.data.split("_")[1]
    user_id = call.from_user.id
    player = Player(user_id)
    
    cat_map = {"weapon": ("weapon", "⚔ ОРУЖИЕ"), "helmet": ("helmet", "👤 ШЛЕМЫ"), 
               "armor": ("armor", "🦾 БРОНЯ"), "boots": ("boots", "🦿 ОБУВЬ"),
               "potion": ("potion", "🧪 ЗЕЛЬЯ")}
    
    item_type, cat_name = cat_map.get(cat, (cat, cat))
    cat_items = {k: v for k, v in items.items() if v.get("type") == item_type}
    
    text = f"<b>{cat_name}</b>\n💰 {player.data['money']}💰\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for ik, item in sorted(cat_items.items(), key=lambda x: x[1].get("price", 0)):
        if player.data["level"] < item.get("level_req", 1):
            continue
        
        r = RARITY_COLORS.get(item.get("rarity", "common"), "⬜")
        
        if item_type == "weapon":
            s = f"Урон: {item['damage'][0]}-{item['damage'][1]}"
        elif item_type in ["helmet", "armor", "boots"]:
            s = f"Защита: {item.get('defense', 0)}"
        elif item_type == "potion":
            s = f"Лечение: {item.get('heal', 0)}"
        else:
            s = ""
        
        text += f"{r} <b>{item['name']}</b> — {s}\n💰 {item['price']} | Ур.{item.get('level_req', 1)}\n\n"
        
        if player.data["money"] >= item["price"]:
            markup.add(types.InlineKeyboardButton(
                f"Купить: {item['name']} - {item['price']}💰",
                callback_data=f"buy_{ik}"
            ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="shop_menu"))
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
    
    player.data["money"] -= item["price"]
    player.data["inventory"].append(ik)
    player.data["items_found"] += 1
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ {item['name']}!")

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
@{d['username']}
⭐ Ур.{d['level']} | 📊 {d['pvp_rating']}
💰 {d['money']}💰

🏆 Побед: {d['wins']} | 💀 Поражений: {d['losses']}
📈 Винрейт: {wr:.1f}%
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
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
                eq = f" [🟢 {slot}]"
        
        text += f"{idx}. {r} {item['name']} x{cnt}{eq}\n"
        
        if item.get("type") in ["weapon", "helmet", "armor", "boots"]:
            markup.add(types.InlineKeyboardButton(f"Экипировать: {item['name']}", callback_data=f"equip_{ik}"))
        elif item.get("type") == "potion":
            markup.add(types.InlineKeyboardButton(f"Использовать: {item['name']}", callback_data=f"use_{ik}"))
        
        idx += 1
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

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
    
    bot.answer_callback_query(call.id, f"✅ {item['name']} экипирован!")

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
    
    if "heal" in item:
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + item["heal"])
    
    player.data["inventory"].remove(ik)
    player.save()
    
    bot.answer_callback_query(call.id, "✅ Использовано!")

@bot.callback_query_handler(func=lambda call: call.data == "hero_equipped")
def hero_equipped_handler(call):
    user_id = call.from_user.id
    player = Player(user_id)
    equip = player.data["equipment"]
    
    text = "<b>👁 ЭКИПИРОВКА</b>\n\n"
    slot_names = {"weapon": "⚔ Оружие", "head": "👤 Голова", "body": "🦾 Тело", "legs": "🦿 Ноги"}
    
    for slot, sn in slot_names.items():
        ik = equip.get(slot)
        if ik:
            item = items.get(ik) or limited_items.get(ik)
            if item:
                defense = item.get("defense", 0)
                text += f"{sn}: <b>{item['name']}</b> (DEF: {defense})\n"
            else:
                text += f"{sn}: ❌ Удалён\n"
        else:
            text += f"{sn}: ❌ Пусто\n"
    
    text += "\n<i>Защита уменьшает урон по этой части тела!</i>"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "hero_heal")
def hero_heal_handler(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    potions = [k for k in player.data["inventory"] if items.get(k, {}).get("type") == "potion" and items.get(k, {}).get("heal", 0) > 0]
    
    if not potions:
        bot.edit_message_text("💊 Нет зелий!", call.message.chat.id, call.message.message_id)
        return
    
    if player.data["hp"] >= player.data["max_hp"]:
        bot.edit_message_text("💊 Полное здоровье!", call.message.chat.id, call.message.message_id)
        return
    
    pk = potions[0]
    potion = items[pk]
    
    player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + potion["heal"])
    player.data["inventory"].remove(pk)
    player.save()
    
    bot.edit_message_text(f"💊 <b>{potion['name']}</b>\n❤ HP: {player.data['hp']}/{player.data['max_hp']}", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_hero")
def back_to_hero_handler(call):
    hero_section(call.message)

# ==================== ДАНЖИ ====================
@bot.callback_query_handler(func=lambda call: call.data == "dungeons_menu")
def dungeons_menu(call):
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
        markup.add(types.InlineKeyboardButton(name, callback_data=f"dungeon_{i}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dungeon_"))
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
    
    # Создание первого босса данжа
    boss_level = level_reqs[dl - 1] * 2
    boss_id = f"boss_{random.randint(100000, 999999)}"
    
    boss_names = [
        ["🐺 Волк", "🐺 Матёрый волк", "🐺 Вожак стаи"],
        ["🕷 Паук", "🕷 Ядовитый паук", "🕷 Королева пауков"],
        ["💀 Скелет", "💀 Рыцарь смерти", "💀 Некромант"],
        ["🐉 Дракончик", "🐉 Дракон", "🐉 Древний дракон"],
        ["👹 Бес", "👹 Демон", "👹 Владыка бездны"]
    ]
    
    users[boss_id] = create_bot_player(boss_level - 2, boss_level + 2)
    users[boss_id]["first_name"] = boss_names[dl-1][0]
    save_json(DATA_FILES['users'], users)
    
    # Сохраняем прогресс данжа
    dungeon_progress[str(user_id)] = {
        "dungeon_level": dl,
        "current_boss": 1,
        "boss_id": boss_id,
        "bosses_defeated": 0,
        "total_reward": 0,
        "total_exp": 0,
        "boss_names": boss_names[dl-1]
    }
    save_json(DATA_FILES['dungeons'], dungeon_progress)
    
    # Создаём дуэль
    duel = DuelInstance(user_id, boss_id, "dungeon", 0)
    active_duels[str(user_id)] = duel
    
    bot.edit_message_text(f"⚔ Бой с боссом <b>{boss_names[dl-1][0]}</b>! Выберите защиту.", call.message.chat.id, call.message.message_id)
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

# Модифицируем finish_duel для данжей
original_finish_duel = finish_duel

def finish_duel_with_dungeon(duel):
    if duel.duel_type == "dungeon":
        player_id = duel.p1_id if not duel.p1_id.startswith("boss_") else duel.p2_id
        dg = dungeon_progress.get(str(player_id), {})
        
        if duel.winner == 1 and not duel.p1_id.startswith("boss_"):
            # Игрок победил босса
            dg["bosses_defeated"] = dg.get("bosses_defeated", 0) + 1
            dg["total_reward"] = dg.get("total_reward", 0) + random.randint(20, 100)
            dg["total_exp"] = dg.get("total_exp", 0) + random.randint(10, 50)
            
            if dg["bosses_defeated"] < 3:
                # Следующий босс
                dg["current_boss"] += 1
                boss_level = [1, 5, 10, 15, 25][dg["dungeon_level"]-1] * 2 + dg["current_boss"] * 2
                new_boss_id = f"boss_{random.randint(100000, 999999)}"
                users[new_boss_id] = create_bot_player(boss_level - 2, boss_level + 2)
                users[new_boss_id]["first_name"] = dg["boss_names"][dg["current_boss"]-1]
                save_json(DATA_FILES['users'], users)
                
                dg["boss_id"] = new_boss_id
                dungeon_progress[str(player_id)] = dg
                save_json(DATA_FILES['dungeons'], dungeon_progress)
                
                # Новая дуэль
                new_duel = DuelInstance(player_id, new_boss_id, "dungeon", 0)
                active_duels[str(player_id)] = new_duel
                
                try:
                    bot.send_message(int(player_id), f"⚔ Следующий босс: <b>{dg['boss_names'][dg['current_boss']-1]}</b>! Выберите защиту.")
                except:
                    pass
                return
            else:
                # Все боссы побеждены
                player = Player(player_id)
                player.data["money"] += dg["total_reward"]
                player.data["exp"] += dg["total_exp"]
                player.data["total_exp"] += dg["total_exp"]
                player.data["dungeons_completed"] = player.data.get("dungeons_completed", 0) + 1
                player.data["last_dungeon"] = datetime.now().isoformat()
                check_level_up(player)
                player.save()
                
                try:
                    bot.send_message(int(player_id), f"<b>🏰 ДАНЖ ПРОЙДЕН!</b>\n💰 +{dg['total_reward']}\n✨ +{dg['total_exp']}")
                except:
                    pass
        else:
            # Проигрыш боссу
            try:
                bot.send_message(int(player_id), f"💀 Вы проиграли боссу <b>{dg.get('boss_names', [''])[dg.get('current_boss', 1)-1]}</b>!")
            except:
                pass
    else:
        original_finish_duel(duel)

finish_duel = finish_duel_with_dungeon

# ==================== ТУРНИРЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "tournaments_menu")
def tournaments_menu(call):
    if not tournaments.get("active"):
        tournaments["active"] = {
            "name": "Турнир",
            "participants": [],
            "prize_pool": 5000,
            "status": "registration",
            "rounds": [],
            "current_round": 0,
            "started_at": datetime.now().isoformat()
        }
        save_json(DATA_FILES['tournaments'], tournaments)
    
    tour = tournaments["active"]
    
    text = f"""
<b>🏟 ТУРНИР</b>

<b>{tour['name']}</b>
Участников: {len(tour.get('participants', []))}/16
Приз: <b>{tour.get('prize_pool', 0)}💰</b>
Статус: {tour.get('status', 'registration')}
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

@bot.callback_query_handler(func=lambda call: call.data == "tour_list")
def tour_list_handler(call):
    participants = tournaments.get("active", {}).get("participants", [])
    if not participants:
        bot.answer_callback_query(call.id, "📋 Пусто")
        return
    
    text = "<b>📋 УЧАСТНИКИ</b>\n\n"
    for i, uid in enumerate(participants[:16], 1):
        p = Player(uid)
        text += f"{i}. {p.data['first_name']} (@{p.data['username']}) - Lv.{p.data['level']}\n"
    
    bot.send_message(call.message.chat.id, text)

# ==================== ИВЕНТЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "events_menu")
def events_menu(call):
    current_event = events.get("current", {})
    
    if not current_event or datetime.fromisoformat(current_event.get("expires", "2000-01-01")) < datetime.now():
        new_event = {
            "name": random.choice(["🌋 Извержение", "❄ Шторм", "⚡ Гроза", "🌑 Затмение", "✨ Звездопад"]),
            "description": "Участвуйте в дуэлях для получения наград!",
            "reward_money": random.randint(200, 1000),
            "reward_exp": random.randint(50, 300),
            "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        events["current"] = new_event
        save_json(DATA_FILES['events'], events)
        
        # Рассылаем уведомление всем игрокам
        for uid in users:
            try:
                bot.send_message(int(uid), f"🌍 <b>НОВЫЙ ИВЕНТ!</b>\n<b>{new_event['name']}</b>\n{new_event['description']}\n🎁 Награда: {new_event['reward_money']}💰 + {new_event['reward_exp']} EXP")
            except:
                pass
    
    ev = events["current"]
    time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
    minutes_left = max(0, time_left.seconds // 60)
    
    text = f"""
<b>🌍 ИВЕНТ</b>

<b>{ev['name']}</b>
📝 {ev['description']}
🎁 {ev['reward_money']}💰 + {ev['reward_exp']} EXP
⏰ {minutes_left} мин.
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== ЕЖЕДНЕВНЫЙ БОНУС ====================
@bot.callback_query_handler(func=lambda call: call.data == "daily_bonus")
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
    player.data["total_exp"] += exp
    player.data["last_daily"] = today
    
    old = player.data["level"]
    check_level_up(player)
    player.save()
    
    text = f"<b>🎁 БОНУС</b>\n💰 +{bonus}\n✨ +{exp}"
    if player.data["level"] > old:
        text += f"\n🎉 УРОВЕНЬ <b>{player.data['level']}</b>!"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

# ==================== ТОП ====================
@bot.callback_query_handler(func=lambda call: call.data == "top_menu")
def top_menu_handler(call):
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
def show_top_handler(call):
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
        
        text += f"{medals[i]} {data.get('first_name', 'Игрок')} (@{data.get('username', 'Нет')}): {val}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="top_menu"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== КЛАНЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "clans_menu")
def clans_menu_handler(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data.get("clan"):
        clan = clans.get(player.data["clan"], {})
        text = f"<b>🛡 {player.data['clan']}</b>\n👥 {len(clan.get('members', []))} уч.\n💰 Казна: {clan.get('treasury', 0)}💰"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("👥 Участники", callback_data="clan_members"),
            types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave")
        )
    else:
        text = "<b>🛡 КЛАНЫ</b>\n/createclan [имя]\n/joinclan [имя]"
        markup = types.InlineKeyboardMarkup()
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
        
        clans[name] = {
            "leader_id": user_id, "leader_name": message.from_user.first_name,
            "members": [message.from_user.first_name], "treasury": 0,
            "created_at": datetime.now().isoformat()
        }
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

# ==================== РЫНОК ====================
@bot.callback_query_handler(func=lambda call: call.data == "market_menu")
def market_menu_handler(call):
    if not market_listings:
        bot.edit_message_text("📦 Рынок пуст\n/sell [номер] [цена]", call.message.chat.id, call.message.message_id)
        return
    
    text = "<b>💱 РЫНОК</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for lid, listing in list(market_listings.items())[:10]:
        item = items.get(listing["item_key"]) or limited_items.get(listing["item_key"])
        if item:
            text += f"📦 {item['name']} — <b>{listing['price']}💰</b>\n"
            markup.add(types.InlineKeyboardButton(f"Купить: {item['name']}", callback_data=f"mkt_buy_{lid}"))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
    bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mkt_buy_"))
def market_buy_handler(call):
    lid = call.data.split("_", 2)[2]
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

# ==================== АДМИН ====================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("💰 Выдать деньги", callback_data="admin_money"),
        types.InlineKeyboardButton("🎁 Выдать предмет", callback_data="admin_item"),
        types.InlineKeyboardButton("⛔ Бан", callback_data="admin_ban"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🏟 Турниры", callback_data="admin_tournament"),
        types.InlineKeyboardButton("👁 Инфо", callback_data="admin_info"),
        types.InlineKeyboardButton("✅ Разбан", callback_data="admin_unban")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_handlers(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    action = call.data.split("_")[1]
    
    if action == "stats":
        text = f"""
<b>📊 СТАТИСТИКА</b>
👥 {len(users)} игроков
💰 {sum(u.get('money',0) for u in users.values())} монет
⚔ {sum(u.get('total_duels',0) for u in users.values())} дуэлей
🛡 {len(clans)} кланов
"""
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    
    elif action == "money":
        bot.send_message(call.message.chat.id, "💰 /givemoney @username [сумма]")
    elif action == "item":
        bot.send_message(call.message.chat.id, "🎁 /giveitem @username [item_key]")
    elif action == "ban":
        bot.send_message(call.message.chat.id, "⛔ /ban @username [причина]")
    elif action == "broadcast":
        bot.send_message(call.message.chat.id, "📢 /broadcast [текст]")
    elif action == "tournament":
        bot.send_message(call.message.chat.id, "🏟 /createtournament [имя] [приз]")
    elif action == "info":
        bot.send_message(call.message.chat.id, "👁 /userinfo @username")
    elif action == "unban":
        bot.send_message(call.message.chat.id, "✅ /unban @username")

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'broadcast', 'userinfo', 'createtournament'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd == "createtournament":
            name = parts[1] if len(parts) > 1 else "Турнир"
            prize = int(parts[2]) if len(parts) > 2 else 5000
            
            tournaments["active"] = {
                "name": name,
                "participants": [],
                "prize_pool": prize,
                "status": "registration",
                "rounds": [],
                "current_round": 0,
                "started_at": datetime.now().isoformat()
            }
            save_json(DATA_FILES['tournaments'], tournaments)
            
            # Рассылка
            for uid in users:
                try:
                    bot.send_message(int(uid), f"🏟 <b>НОВЫЙ ТУРНИР!</b>\n<b>{name}</b>\nПриз: {prize}💰\n/start для участия")
                except:
                    pass
            
            bot.send_message(message.chat.id, f"✅ Турнир <b>{name}</b> создан!")
            return
        
        # Поиск по username
        username = parts[1].replace('@', '')
        found_uid = None
        for uid, data in users.items():
            if data.get("username", "").lower() == username.lower():
                found_uid = uid
                break
        
        if not found_uid and cmd not in ["broadcast"]:
            bot.send_message(message.chat.id, f"❌ @{username} не найден!")
            return
        
        if cmd == "givemoney":
            amount = int(parts[2])
            p = Player(found_uid)
            p.data["money"] += amount
            p.save()
            bot.send_message(message.chat.id, f"✅ {amount}💰 → @{username}")
        
        elif cmd == "giveitem":
            ik = parts[2]
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
        
        elif cmd == "broadcast":
            text = message.text.replace('/broadcast', '', 1).strip()
            if text:
                s, f = 0, 0
                for uid in users:
                    try:
                        bot.send_message(int(uid), f"📢 <b>ОБЪЯВЛЕНИЕ:</b>\n{text}")
                        s += 1
                    except:
                        f += 1
                bot.send_message(message.chat.id, f"✅ {s} | ❌ {f}")
        
        elif cmd == "userinfo":
            p = Player(found_uid)
            d = p.data
            text = f"""
<b>👤 @{username}</b>
Имя: {d['first_name']}
Ур.: {d['level']} | 💰 {d['money']}
Рейтинг: {d['pvp_rating']}
Побед: {d['wins']} | Поражений: {d['losses']}
Клан: {d.get('clan', 'Нет')}
Предметов: {len(d['inventory'])}
"""
            bot.send_message(message.chat.id, text)
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== ОБРАБОТЧИКИ НАВИГАЦИИ ====================
@bot.callback_query_handler(func=lambda call: call.data == "back_to_world")
def back_to_world_handler(call):
    world_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_trade")
def back_to_trade_handler(call):
    trade_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "help_menu")
def help_menu_handler(call):
    text = """
<b>ℹ ПОМОЩЬ</b>

<b>Дуэли:</b>
Защита → атака противника → ваша атака
Броня уменьшает урон по защищённой части

<b>Команды:</b>
/sell [номер] [цена]
/transfer [номер]
/createclan [имя]
/joinclan [имя]

@username используется для админ-команд
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==================== ЗАПУСК ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v11.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print("=" * 60)
    print("✅ Броня уменьшает урон (не даёт HP)")
    print("✅ Пошаговые дуэли: защита → атака по очереди")
    print("✅ Кулдауны навыков (сильные = дольше)")
    print("✅ Данжи с несколькими боссами")
    print("✅ Таймаут хода = 60 сек")
    print("✅ Ивенты с реальными наградами")
    print("✅ @username для админ-команд")
    print("✅ Результаты дуэлей обоим игрокам")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
