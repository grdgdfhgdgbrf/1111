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

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = '8670879387:AAH70T6P0ZEn-rvPhQo7rhrNMl9wUKDkILI'
ADMIN_ID = 5356400377
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ==================== КОНСТАНТЫ ====================
BODY_PARTS = {
    "head": {"name": "👤 Голова", "damage_mult": 1.5, "base_armor": 2},
    "body": {"name": "🦾 Тело", "damage_mult": 1.0, "base_armor": 5},
    "legs": {"name": "🦿 Ноги", "damage_mult": 0.7, "base_armor": 3}
}

RARITY_COLORS = {
    "common": "⬜", "uncommon": "🟩", "rare": "🟦",
    "epic": "🟪", "legendary": "🟧", "mythic": "🟥",
    "divine": "💛", "apocalyptic": "🖤"
}

ENCHANT_EFFECTS = [
    {"name": "🔥 Огненное", "effect": "burn_chance", "value": 20},
    {"name": "❄ Ледяное", "effect": "freeze_chance", "value": 20},
    {"name": "⚡ Грозовое", "effect": "stun_chance", "value": 15},
    {"name": "🛡 Укреплённое", "effect": "armor_bonus", "value": 10},
    {"name": "💪 Мощное", "effect": "damage_bonus", "value": 20},
    {"name": "💨 Скоростное", "effect": "speed_bonus", "value": 10},
    {"name": "🎯 Меткое", "effect": "crit_bonus", "value": 15},
    {"name": "💀 Вампирское", "effect": "life_steal", "value": 10}
]

# ==================== ФАЙЛЫ ДАННЫХ ====================
DATA_FILES = {
    'users': 'users.json',
    'items': 'items.json',
    'limited': 'limited_items.json',
    'clans': 'clans.json',
    'tournaments': 'tournaments.json',
    'market': 'market.json',
    'events': 'events.json',
    'bans': 'bans.json',
    'battle_history': 'battle_history.json',
    'enchantments': 'enchantments.json',
    'world_bosses': 'world_bosses.json',
    'duel_invites': 'duel_invites.json'
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
HELMETS = {
    "leather_cap": {"name": "🎓 Кожаная шапка", "armor_head": 3, "armor_body": 1, "armor_legs": 0, "hp_bonus": 10, "price": 60, "type": "helmet", "slot": "head", "rarity": "common", "level_req": 1},
    "iron_helmet": {"name": "⛑ Железный шлем", "armor_head": 8, "armor_body": 2, "armor_legs": 1, "hp_bonus": 20, "price": 250, "type": "helmet", "slot": "head", "rarity": "uncommon", "level_req": 6},
    "dragon_helmet": {"name": "🐉 Шлем дракона", "armor_head": 18, "armor_body": 5, "armor_legs": 3, "hp_bonus": 50, "price": 2000, "type": "helmet", "slot": "head", "rarity": "epic", "level_req": 20},
    "crown_of_wisdom": {"name": "👑 Корона мудрости", "armor_head": 12, "armor_body": 3, "armor_legs": 2, "hp_bonus": 35, "mana_bonus": 40, "price": 3500, "type": "helmet", "slot": "head", "rarity": "legendary", "level_req": 28}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "armor_head": 1, "armor_body": 5, "armor_legs": 2, "hp_bonus": 25, "price": 80, "type": "armor", "slot": "body", "rarity": "common", "level_req": 1},
    "chainmail": {"name": "⛓ Кольчуга", "armor_head": 3, "armor_body": 12, "armor_legs": 5, "hp_bonus": 50, "price": 400, "type": "armor", "slot": "body", "rarity": "uncommon", "level_req": 8},
    "plate_armor": {"name": "🛡 Латный доспех", "armor_head": 5, "armor_body": 22, "armor_legs": 10, "hp_bonus": 90, "price": 1500, "type": "armor", "slot": "body", "rarity": "rare", "level_req": 15},
    "shadow_armor": {"name": "🌑 Теневая броня", "armor_head": 8, "armor_body": 28, "armor_legs": 15, "hp_bonus": 120, "price": 3500, "type": "armor", "slot": "body", "rarity": "epic", "level_req": 22},
    "phoenix_armor": {"name": "🦅 Броня феникса", "armor_head": 12, "armor_body": 40, "armor_legs": 20, "hp_bonus": 200, "price": 8000, "type": "armor", "slot": "body", "rarity": "legendary", "level_req": 30}
}

BOOTS = {
    "leather_boots": {"name": "👢 Кожаные сапоги", "armor_head": 0, "armor_body": 1, "armor_legs": 3, "hp_bonus": 5, "speed": 8, "price": 100, "type": "boots", "slot": "legs", "rarity": "common", "level_req": 1},
    "wind_boots": {"name": "🌪 Сапоги ветра", "armor_head": 1, "armor_body": 2, "armor_legs": 6, "hp_bonus": 10, "speed": 18, "price": 900, "type": "boots", "slot": "legs", "rarity": "rare", "level_req": 12},
    "blink_boots": {"name": "✨ Сапоги телепортации", "armor_head": 2, "armor_body": 4, "armor_legs": 10, "hp_bonus": 20, "speed": 28, "price": 4000, "type": "boots", "slot": "legs", "rarity": "epic", "level_req": 25},
    "hermes_boots": {"name": "👟 Сандалии Гермеса", "armor_head": 4, "armor_body": 8, "armor_legs": 18, "hp_bonus": 40, "speed": 45, "price": 12000, "type": "boots", "slot": "legs", "rarity": "legendary", "level_req": 35}
}

WEAPONS = {
    "rusty_sword": {"name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 1, "skills": ["quick_strike"]},
    "hunters_bow": {"name": "🏹 Лук охотника", "damage": (7, 14), "price": 150, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 3, "skills": ["power_shot", "multi_shot"]},
    "flame_blade": {"name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 7, "skills": ["fire_slash", "inferno_strike"], "element": "fire"},
    "frost_axe": {"name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 10, "skills": ["frost_strike", "ice_shatter"], "element": "ice"},
    "storm_staff": {"name": "⚡ Посох бурь", "damage": (18, 30), "price": 1500, "type": "weapon", "slot": "weapon", "rarity": "rare", "level_req": 14, "skills": ["lightning_bolt", "thunder_storm"], "element": "lightning"},
    "shadow_dagger": {"name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "slot": "weapon", "rarity": "epic", "level_req": 22, "skills": ["shadow_strike", "assassinate"], "element": "dark"},
    "divine_spear": {"name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "slot": "weapon", "rarity": "legendary", "level_req": 28, "skills": ["holy_strike", "divine_judgment"], "element": "light"},
    "death_scythe": {"name": "💀 Коса смерти", "damage": (40, 65), "price": 12000, "type": "weapon", "slot": "weapon", "rarity": "mythic", "level_req": 35, "skills": ["reap", "death_sentence"]}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8},
    "elixir_of_life": {"name": "💊 Эликсир жизни", "heal": 200, "price": 350, "type": "potion", "rarity": "rare", "level_req": 15},
    "mana_potion": {"name": "💎 Зелье маны", "mana_restore": 60, "price": 60, "type": "potion", "rarity": "common", "level_req": 5}
}

LIMITED_ITEMS = {
    "thunderfury": {"name": "⚡ Ярость грома", "damage": (60, 95), "total": 3, "remaining": 3, "price": 50000, "type": "weapon", "slot": "weapon", "rarity": "divine", "skills": ["thunder_gods_wrath", "lightning_apocalypse"], "element": "lightning"},
    "immortal_helmet": {"name": "✨ Шлем бессмертия", "armor_head": 80, "armor_body": 30, "armor_legs": 20, "hp_bonus": 300, "total": 2, "remaining": 2, "price": 75000, "type": "helmet", "slot": "head", "rarity": "divine"}
}

ALL_ITEMS = {}
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(BOOTS)
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(POTIONS)

# ==================== БАЗА НАВЫКОВ ====================
SKILLS_DB = {
    "quick_strike": {"name": "⚡ Быстрый удар", "damage_mult": 1.0, "mana_cost": 0, "cooldown": 0, "speed": "fast"},
    "strong_strike": {"name": "💪 Сильный удар", "damage_mult": 1.5, "mana_cost": 10, "cooldown": 1, "speed": "medium"},
    "power_shot": {"name": "🎯 Мощный выстрел", "damage_mult": 1.8, "mana_cost": 15, "cooldown": 2, "speed": "slow"},
    "multi_shot": {"name": "🏹 Залп", "damage_mult": 0.6, "hits": 3, "mana_cost": 20, "cooldown": 2, "speed": "medium"},
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.6, "mana_cost": 18, "cooldown": 2, "speed": "medium", "burn_chance": 30},
    "inferno_strike": {"name": "🌋 Инферно удар", "damage_mult": 2.5, "mana_cost": 40, "cooldown": 4, "speed": "slow", "burn_chance": 60},
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.5, "mana_cost": 16, "cooldown": 1, "speed": "medium", "freeze_chance": 25},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.3, "mana_cost": 35, "cooldown": 3, "speed": "slow", "freeze_chance": 50},
    "lightning_bolt": {"name": "⚡ Молния", "damage_mult": 1.7, "mana_cost": 20, "cooldown": 2, "speed": "fast", "stun_chance": 20},
    "thunder_storm": {"name": "⛈ Грозовой шторм", "damage_mult": 2.8, "mana_cost": 50, "cooldown": 4, "speed": "slow", "stun_chance": 35},
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.8, "mana_cost": 22, "cooldown": 2, "speed": "fast", "poison_chance": 25},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.5, "mana_cost": 60, "cooldown": 5, "speed": "slow"},
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.6, "mana_cost": 20, "cooldown": 1, "speed": "medium"},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 3.0, "mana_cost": 55, "cooldown": 4, "speed": "slow"},
    "reap": {"name": "💀 Жатва", "damage_mult": 2.5, "mana_cost": 42, "cooldown": 3, "speed": "medium", "life_steal": 30},
    "death_sentence": {"name": "☠ Смертный приговор", "damage_mult": 4.0, "mana_cost": 75, "cooldown": 5, "speed": "slow"},
    "thunder_gods_wrath": {"name": "⚡ Гнев бога грома", "damage_mult": 5.0, "mana_cost": 90, "cooldown": 6, "speed": "slow", "stun_chance": 50},
    "lightning_apocalypse": {"name": "⚡ Молниевый апокалипсис", "damage_mult": 6.0, "mana_cost": 100, "cooldown": 7, "speed": "slow"}
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
battle_history_data = load_json(DATA_FILES['battle_history'], {})
enchantments_data = load_json(DATA_FILES['enchantments'], {})
world_bosses = load_json(DATA_FILES['world_bosses'], {})
duel_invites = load_json(DATA_FILES['duel_invites'], {})

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
                "settings": {"notifications": True},
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
    
    def get_armor_for_part(self, part):
        """Получить броню для части тела"""
        total_armor = BODY_PARTS[part]["base_armor"]
        
        for slot, ik in self.data["equipment"].items():
            if not ik:
                continue
            item = items.get(ik) or limited_items.get(ik)
            if not item:
                continue
            
            armor_key = f"armor_{part}"
            if armor_key in item:
                total_armor += item[armor_key]
            
            # Зачарования
            ench = self.data.get("enchantments", {}).get(ik, {})
            if ench.get("effect") == "armor_bonus":
                total_armor += ench.get("value", 0)
        
        return total_armor
    
    def get_damage_range(self):
        """Получить диапазон урона"""
        min_d, max_d = 5, 10  # Базовый
        
        weapon_key = self.data["equipment"].get("weapon")
        if weapon_key:
            weapon = items.get(weapon_key) or limited_items.get(weapon_key)
            if weapon and "damage" in weapon:
                min_d = weapon["damage"][0]
                max_d = weapon["damage"][1]
        
        # Зачарования
        for ik, ench in self.data.get("enchantments", {}).items():
            if ench.get("effect") == "damage_bonus":
                val = ench.get("value", 0)
                min_d += val // 3
                max_d += val // 2
        
        return (min_d, max_d)
    
    def get_max_hp(self):
        """Получить максимальное HP"""
        hp = 100 + self.data["level"] * 10
        
        for slot, ik in self.data["equipment"].items():
            if not ik:
                continue
            item = items.get(ik) or limited_items.get(ik)
            if item and "hp_bonus" in item:
                hp += item["hp_bonus"]
        
        for ik, ench in self.data.get("enchantments", {}).items():
            if ench.get("effect") == "hp_bonus":
                hp += ench.get("value", 0)
        
        return hp

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
        self.log = []
        self.timeout_timer = None
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        # Одинаковое HP для честного боя
        p1_hp = self.p1.get_max_hp()
        p2_hp = self.p2.get_max_hp()
        avg_hp = (p1_hp + p2_hp) // 2
        
        self.p1_hp = avg_hp
        self.p2_hp = avg_hp
        self.p1_max_hp = avg_hp
        self.p2_max_hp = avg_hp
        
        self.p1_mp = 50
        self.p2_mp = 50
        self.p1_max_mp = 50
        self.p2_max_mp = 50
        
        # Фазы: p1_phase и p2_phase
        # defend_select -> waiting_opponent_defend -> attack_select -> waiting_opponent_attack
        self.p1_phase = "defend_select"
        self.p2_phase = "defend_select"
        
        self.p1_defend = None
        self.p2_defend = None
        self.p1_skill = None
        self.p2_skill = None
        self.p1_target = None
        self.p2_target = None
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Эффекты
        self.p1_effects = []
        self.p2_effects = []
        
        self.log.append(f"⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>")
        self._start_timeout()
    
    def _start_timeout(self):
        """Таймаут 60 секунд на выбор"""
        if self.timeout_timer:
            self.timeout_timer.cancel()
        
        self.timeout_timer = threading.Timer(60.0, self._handle_timeout)
        self.timeout_timer.start()
    
    def _handle_timeout(self):
        """Обработка таймаута"""
        if not self.active:
            return
        
        # Определяем кто не сделал ход
        if self.p1_phase in ["defend_select", "attack_select"]:
            self.active = False
            self.winner = 2
            self.log.append("⏰ Игрок 1 не успел сделать ход!")
        elif self.p2_phase in ["defend_select", "attack_select"]:
            self.active = False
            self.winner = 1
            self.log.append("⏰ Игрок 2 не успел сделать ход!")
        
        self._finish_timeout()
    
    def _finish_timeout(self):
        """Завершение по таймауту"""
        if self.timeout_timer:
            self.timeout_timer.cancel()
        
        for uid in [self.p1_id, self.p2_id]:
            if uid in active_duels:
                duel = active_duels[uid]
                if duel.battle_id == self.battle_id:
                    # Уведомить игрока
                    try:
                        chat_id = int(uid)
                        bot.send_message(chat_id, f"⚔ Дуэль #{self.battle_id} завершена по таймауту!")
                    except:
                        pass
        
        # Очистка
        for uid in [self.p1_id, self.p2_id]:
            if uid in active_duels and active_duels[uid].battle_id == self.battle_id:
                del active_duels[uid]
    
    def get_player_name(self, num):
        if num == 1:
            return self.p1.data["first_name"]
        return self.p2.data["first_name"]
    
    def get_available_skills(self, player_num):
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        equipment = (self.p1 if player_num == 1 else self.p2).data["equipment"]
        
        available = []
        
        # Базовые навыки всегда доступны
        base = ["quick_strike", "strong_strike"]
        for sid in base:
            if sid not in cooldowns or cooldowns[sid] <= 0:
                available.append(sid)
        
        # Навыки оружия
        weapon_key = equipment.get("weapon")
        if weapon_key:
            weapon = items.get(weapon_key) or limited_items.get(weapon_key)
            if weapon and "skills" in weapon:
                for sid in weapon["skills"]:
                    if sid in SKILLS_DB:
                        cd = cooldowns.get(sid, 0)
                        if cd <= 0:
                            available.append(sid)
        
        return list(set(available))
    
    def set_defend(self, player_num, part):
        if player_num == 1:
            self.p1_defend = part
            self.p1_phase = "waiting_opponent_defend"
        else:
            self.p2_defend = part
            self.p2_phase = "waiting_opponent_defend"
        
        # Проверяем, выбрали ли оба защиту
        if self.p1_phase == "waiting_opponent_defend" and self.p2_phase == "waiting_opponent_defend":
            # Оба выбрали защиту, теперь выбор атаки
            self.p1_phase = "attack_select"
            self.p2_phase = "attack_select"
        
        self._start_timeout()
    
    def set_attack(self, player_num, skill_id, target_part):
        if player_num == 1:
            self.p1_skill = skill_id
            self.p1_target = target_part
            self.p1_phase = "waiting_opponent_attack"
        else:
            self.p2_skill = skill_id
            self.p2_target = target_part
            self.p2_phase = "waiting_opponent_attack"
        
        # Проверяем, атаковали ли оба
        if self.p1_phase == "waiting_opponent_attack" and self.p2_phase == "waiting_opponent_attack":
            # Оба атаковали - разрешаем ход
            self._resolve_turn()
        
        self._start_timeout()
    
    def _resolve_turn(self):
        """Разрешение хода"""
        if self.timeout_timer:
            self.timeout_timer.cancel()
        
        # Обработка эффектов
        self._process_effects(1)
        self._process_effects(2)
        
        # Атаки происходят одновременно
        self._do_attack(1, 2)
        if not self.active:
            return
        
        self._do_attack(2, 1)
        if not self.active:
            return
        
        # Сброс фаз для нового хода
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
        
        self._start_timeout()
    
    def _do_attack(self, attacker, defender):
        skill_id = self.p1_skill if attacker == 1 else self.p2_skill
        target_part = self.p1_target if attacker == 1 else self.p2_target
        defend_part = self.p2_defend if attacker == 1 else self.p1_defend
        
        if not skill_id or not target_part:
            return
        
        skill = SKILLS_DB.get(skill_id, {"name": "Атака", "damage_mult": 1.0, "mana_cost": 0})
        
        # Проверка маны
        mc = skill.get("mana_cost", 0)
        if attacker == 1:
            if self.p1_mp < mc:
                self.log.append(f"❌ {self.get_player_name(attacker)}: нет маны для {skill['name']}!")
                return
            self.p1_mp -= mc
        else:
            if self.p2_mp < mc:
                self.log.append(f"❌ {self.get_player_name(attacker)}: нет маны для {skill['name']}!")
                return
            self.p2_mp -= mc
        
        # Базовый урон
        dmg_range = (self.p1 if attacker == 1 else self.p2).get_damage_range()
        base_dmg = random.randint(dmg_range[0], dmg_range[1])
        dmg = int(base_dmg * skill.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_mult = BODY_PARTS[target_part]["damage_mult"]
        dmg = int(dmg * body_mult)
        
        # Проверка защиты
        if defend_part:
            # Защита работает только для той части которую защищают
            if target_part == defend_part:
                armor = (self.p2 if attacker == 1 else self.p1).get_armor_for_part(target_part)
                reduction = armor / (armor + 50)
                blocked = int(dmg * reduction)
                dmg -= blocked
                self.log.append(f"🛡 {self.get_player_name(defender)} защитил {BODY_PARTS[defend_part]['name']}! Броня поглотила {blocked} урона")
            else:
                # Частичная защита (половина брони)
                armor = (self.p2 if attacker == 1 else self.p1).get_armor_for_part(target_part)
                reduction = (armor // 2) / ((armor // 2) + 50)
                blocked = int(dmg * reduction)
                dmg -= blocked
        else:
            # Без защиты - базовый урон с естественной бронёй
            armor = (self.p2 if attacker == 1 else self.p1).get_armor_for_part(target_part)
            reduction = armor / (armor + 80)
            blocked = int(dmg * reduction)
            dmg -= blocked
        
        dmg = max(1, dmg)
        
        # Нанесение урона
        if defender == 1:
            self.p1_hp = max(0, self.p1_hp - dmg)
        else:
            self.p2_hp = max(0, self.p2_hp - dmg)
        
        self.log.append(f"⚔ {self.get_player_name(attacker)} [{skill['name']}] → {BODY_PARTS[target_part]['name']}: <b>-{dmg} HP</b>")
        
        # Эффекты
        self._apply_effects(defender, skill, dmg)
        
        # Вампиризм
        if "life_steal" in skill:
            heal = int(dmg * skill["life_steal"] / 100)
            if attacker == 1:
                self.p1_hp = min(self.p1_max_hp, self.p1_hp + heal)
            else:
                self.p2_hp = min(self.p2_max_hp, self.p2_hp + heal)
            if heal > 0:
                self.log.append(f"💚 Вампиризм +{heal} HP")
        
        # Кулдауны
        cooldowns = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
        if "cooldown" in skill and skill["cooldown"] > 0:
            cooldowns[skill_id] = skill["cooldown"]
        
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
    
    def _apply_effects(self, target, skill, dmg):
        effects = []
        if "burn_chance" in skill and random.random() * 100 < skill["burn_chance"]:
            effects.append({"type": "burn", "duration": 3})
            self.log.append("🔥 Горение!")
        if "freeze_chance" in skill and random.random() * 100 < skill["freeze_chance"]:
            effects.append({"type": "freeze", "duration": 2})
            self.log.append("❄ Заморозка!")
        if "stun_chance" in skill and random.random() * 100 < skill["stun_chance"]:
            effects.append({"type": "stun", "duration": 1})
            self.log.append("⚡ Оглушение!")
        if "poison_chance" in skill and random.random() * 100 < skill["poison_chance"]:
            effects.append({"type": "poison", "duration": 4})
            self.log.append("☠ Отравление!")
        
        if target == 1:
            self.p1_effects.extend(effects)
        else:
            self.p2_effects.extend(effects)
    
    def _process_effects(self, player_num):
        effects = self.p1_effects if player_num == 1 else self.p2_effects
        
        for eff in effects[:]:
            if eff["type"] == "burn":
                d = 10
                if player_num == 1:
                    self.p1_hp = max(0, self.p1_hp - d)
                else:
                    self.p2_hp = max(0, self.p2_hp - d)
                self.log.append(f"🔥 Горение -{d} HP")
            elif eff["type"] == "poison":
                d = 12
                if player_num == 1:
                    self.p1_hp = max(0, self.p1_hp - d)
                else:
                    self.p2_hp = max(0, self.p2_hp - d)
                self.log.append(f"☠ Яд -{d} HP")
            elif eff["type"] == "freeze":
                if random.random() < 0.4:
                    self.log.append(f"❄ Заморозка! Пропуск хода")
            elif eff["type"] == "stun":
                self.log.append(f"⚡ Оглушение!")
            
            eff["duration"] -= 1
            if eff["duration"] <= 0:
                effects.remove(eff)
    
    def get_state_text(self, for_player_id):
        pn = 1 if str(for_player_id) == self.p1_id else 2
        
        def hp_bar(cur, mx):
            pct = cur / mx * 100 if mx > 0 else 0
            f = int(pct / 10)
            e = 10 - f
            color = "🟢" if pct > 50 else "🟡" if pct > 25 else "🔴"
            return f"{color}[{'█'*f}{'░'*e}] {cur}/{mx} ({pct:.0f}%)"
        
        text = f"""
<b>⚔ ДУЭЛЬ #{self.battle_id}</b>
━━━━━━━━━━━━━━━━━━━━
Ход: <b>{self.turn}</b> | Ставка: <b>{self.bet}💰</b>

<b>⚔ {self.get_player_name(1)}</b>
❤ {hp_bar(self.p1_hp, self.p1_max_hp)}
💎 MP: {self.p1_mp}/{self.p1_max_mp}
🛡 Защита: {BODY_PARTS.get(self.p1_defend, {}).get('name', 'Не выбрана') if self.p1_defend else 'Не выбрана'}

<b>⚔ {self.get_player_name(2)}</b>
❤ {hp_bar(self.p2_hp, self.p2_max_hp)}
💎 MP: {self.p2_mp}/{self.p2_max_mp}
🛡 Защита: {BODY_PARTS.get(self.p2_defend, {}).get('name', 'Не выбрана') if self.p2_defend else 'Не выбрана'}
━━━━━━━━━━━━━━━━━━━━
"""
        
        phase = self.p1_phase if pn == 1 else self.p2_phase
        
        if phase == "defend_select":
            text += "\n🛡 <b>ВЫБЕРИТЕ ЧАСТЬ ТЕЛА ДЛЯ ЗАЩИТЫ:</b>"
        elif phase == "waiting_opponent_defend":
            text += "\n⏳ <b>Ожидание выбора защиты противником...</b>"
        elif phase == "attack_select":
            text += "\n🎯 <b>ВЫБЕРИТЕ ЦЕЛЬ И НАВЫК АТАКИ:</b>"
        elif phase == "waiting_opponent_attack":
            text += "\n⏳ <b>Ожидание атаки противника...</b>"
        
        # Эффекты
        effs = self.p1_effects if pn == 1 else self.p2_effects
        if effs:
            text += "\n<b>Эффекты:</b> " + ", ".join([f"{e['type']}({e['duration']})" for e in effs])
        
        # Лог
        if self.log:
            text += f"\n\n<i>{self.log[-1][:150]}</i>"
        
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
    
    username = message.from_user.username
    if not username:
        username = f"user_{user_id}"
    
    first_name = message.from_user.first_name or "Игрок"
    Player(user_id, username, first_name)
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v11.0 FINAL ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!
Ваш username: @{username}

🎯 <b>НОВОЕ:</b>
• Броня поглощает урон (не даёт HP!)
• Сначала защита, потом атака
• Три типа атак: быстрая/средняя/медленная
• Медленные атаки мощнее, дольше кулдаун
• Таймаут 60 сек на ход
• Мировые боссы с 1M HP
• Турниры с плей-офф
• Ивенты приходят в ЛС

💰 Старт: <b>500 монет</b>
"""
    bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "⚔️ Дуэли")
def duel_section(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль (бот)", callback_data="quick_duel"),
        types.InlineKeyboardButton("👥 Дуэль с игроком", callback_data="pvp_duel"),
        types.InlineKeyboardButton("🏆 Рейтинговая", callback_data="ranked_duel"),
        types.InlineKeyboardButton("💀 Хардкор (x2 ставка)", callback_data="hardcore_duel"),
        types.InlineKeyboardButton("🔥 Выживание (до 0 HP)", callback_data="survival_duel"),
        types.InlineKeyboardButton("🎯 Спарринг (без ставок)", callback_data="sparring_duel")
    )
    
    text = """
<b>⚔️ ДУЭЛИ</b>

<b>Система боя:</b>
🛡 Шаг 1: Выберите защиту
⏳ Шаг 2: Ожидание противника
🎯 Шаг 3: Выберите цель и навык
⏳ Шаг 4: Ожидание атаки противника
⚔ Шаг 5: Одновременная атака!

<i>Броня поглощает урон, не даёт HP!</i>
"""
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="hero_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="hero_inventory"),
        types.InlineKeyboardButton("🏅 Достижения", callback_data="hero_achievements"),
        types.InlineKeyboardButton("✨ Зачарования", callback_data="hero_enchantments"),
        types.InlineKeyboardButton("👁 Экипировка", callback_data="hero_equipped"),
        types.InlineKeyboardButton("📋 История", callback_data="hero_history"),
        types.InlineKeyboardButton("💊 Лечение", callback_data="hero_heal"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_main")
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
        types.InlineKeyboardButton("📦 Мои лоты", callback_data="trade_my_lots"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_main")
    )
    bot.send_message(message.chat.id, "<b>🏪 ТОРГОВЛЯ</b>", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🌍 Мир")
def world_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🏰 Подземелья", callback_data="world_dungeons"),
        types.InlineKeyboardButton("👹 Мировые боссы", callback_data="world_bosses"),
        types.InlineKeyboardButton("🛡 Кланы", callback_data="world_clans"),
        types.InlineKeyboardButton("🏟 Турниры", callback_data="world_tournaments"),
        types.InlineKeyboardButton("🌍 Ивенты", callback_data="world_events"),
        types.InlineKeyboardButton("📊 Топ", callback_data="world_top"),
        types.InlineKeyboardButton("ℹ Помощь", callback_data="world_help"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_main")
    )
    bot.send_message(message.chat.id, "<b>🌍 МИР</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    bot.edit_message_text("🔙 Главное меню", call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "Выберите раздел:", reply_markup=get_main_menu())

# ==================== ДУЭЛИ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["quick_duel", "pvp_duel", "ranked_duel", "hardcore_duel", "survival_duel", "sparring_duel"])
def duel_type_handler(call):
    dt = call.data
    
    bets = {
        "quick_duel": (50, "⚡ Быстрая"),
        "pvp_duel": (100, "👥 PvP"),
        "ranked_duel": (100, "🏆 Рейтинговая"),
        "hardcore_duel": (500, "💀 Хардкор"),
        "survival_duel": (200, "🔥 Выживание"),
        "sparring_duel": (0, "🎯 Спарринг")
    }
    
    bet, name = bets.get(dt, (100, "Дуэль"))
    
    if dt == "quick_duel":
        # Сразу бот
        start_bot_duel(call, "quick", bet)
    else:
        # Поиск соперника или создание приглашения
        show_duel_invite_menu(call, dt, bet)

def start_bot_duel(call, duel_type, bet):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    if bet > 0:
        player.data["money"] -= bet
        player.save()
    
    # Создание бота с экипировкой
    bot_level = random.randint(max(1, player.data["level"] - 3), player.data["level"] + 3)
    bot_id = f"bot_{random.randint(100000, 999999)}"
    
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    slot_item_types = {"head": "helmet", "body": "armor", "legs": "boots"}
    for slot, itype in slot_item_types.items():
        slot_items = [k for k, v in items.items() if v.get("type") == itype and v.get("level_req", 1) <= bot_level]
        if slot_items and random.random() < 0.7:
            equip[slot] = random.choice(slot_items)
    wpns = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= bot_level]
    if wpns:
        equip["weapon"] = random.choice(wpns)
    
    users[bot_id] = {
        "username": f"Bot_{bot_level}", "first_name": f"🤖 Бот Lv.{bot_level}",
        "money": 0, "level": bot_level, "exp": 0, "total_exp": 0,
        "hp": 100 + bot_level * 12, "max_hp": 100 + bot_level * 12,
        "mana": 50, "max_mana": 50,
        "wins": 0, "losses": 0, "draws": 0,
        "win_streak": 0, "best_streak": 0, "total_duels": 0,
        "pvp_rating": 1000, "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Бот", "titles_collected": ["Бот"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    duel = DuelInstance(user_id, bot_id, duel_type, bet)
    active_duels[user_id] = duel
    active_duels[bot_id] = duel
    
    # Бот выбирает защиту
    bot_def = random.choice(list(BODY_PARTS.keys()))
    duel.set_defend(2, bot_def)
    
    # Бот выбирает атаку
    bot_skills = duel.get_available_skills(2)
    if bot_skills:
        duel.set_attack(2, random.choice(bot_skills), random.choice(list(BODY_PARTS.keys())))
    
    bot.edit_message_text("⚔ Дуэль с ботом началась!", call.message.chat.id, call.message.message_id)
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

def show_duel_invite_menu(call, duel_type, bet):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 Найти соперника", callback_data=f"find_{duel_type}_{bet}"),
        types.InlineKeyboardButton("📨 Пригласить игрока", callback_data=f"invite_{duel_type}_{bet}"),
        types.InlineKeyboardButton("🤖 Играть с ботом", callback_data=f"botduel_{duel_type}_{bet}"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels")
    )
    bot.edit_message_text(f"<b>Выберите режим</b>\nСтавка: {bet}💰", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("find_"))
def find_opponent(call):
    parts = call.data.split("_")
    duel_type = parts[1]
    bet = int(parts[2])
    user_id = str(call.from_user.id)
    
    # В будущем - поиск из очереди, сейчас сразу бот
    start_bot_duel(call, duel_type, bet)

@bot.callback_query_handler(func=lambda call: call.data.startswith("invite_"))
def invite_player(call):
    parts = call.data.split("_")
    duel_type = parts[1]
    bet = int(parts[2])
    user_id = str(call.from_user.id)
    
    bot.edit_message_text(
        "📨 Для приглашения ответьте на сообщение игрока командой:\n"
        f"<code>/invite_duel {duel_type} {bet}</code>",
        call.message.chat.id, call.message.message_id
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("botduel_"))
def bot_duel_callback(call):
    parts = call.data.split("_")
    duel_type = parts[1]
    bet = int(parts[2])
    start_bot_duel(call, duel_type, bet)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_duels")
def back_to_duels(call):
    duel_section(call.message)

def show_duel_interface(chat_id, message_id, duel, user_id):
    if not duel.active:
        finish_duel(chat_id, message_id, duel, user_id)
        return
    
    state_text = duel.get_state_text(user_id)
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    phase = duel.p1_phase if pn == 1 else duel.p2_phase
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if phase == "defend_select":
        for part, data in BODY_PARTS.items():
            armor = (duel.p1 if pn == 1 else duel.p2).get_armor_for_part(part)
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']} (броня:{armor})",
                callback_data=f"duel_defend_{part}"
            ))
    
    elif phase == "attack_select":
        # Сначала цель
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🎯 {data['name']}",
                callback_data=f"duel_target_{part}"
            ))
    
    elif phase in ["waiting_opponent_defend", "waiting_opponent_attack"]:
        markup.add(types.InlineKeyboardButton("⏳ Ожидание противника...", callback_data="duel_wait"))
    
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="duel_refresh"))
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="duel_surrender"))
    
    try:
        bot.edit_message_text(state_text[:4000], chat_id, message_id, reply_markup=markup)
    except Exception as e:
        pass

# Временное хранилище цели
temp_target = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_target_"))
def duel_target_selected(call):
    user_id = call.from_user.id
    part = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    temp_target[str(user_id)] = part
    
    skills = duel.get_available_skills(pn)
    
    state_text = duel.get_state_text(user_id) + f"\n🎯 Цель: <b>{BODY_PARTS[part]['name']}</b>\n<b>Выберите навык:</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for sid in skills[:10]:
        skill = SKILLS_DB.get(sid, {})
        name = skill.get("name", sid)
        mana = skill.get("mana_cost", 0)
        dmg_mult = skill.get("damage_mult", 1.0)
        cd = skill.get("cooldown", 0)
        speed = skill.get("speed", "fast")
        speed_icon = {"fast": "⚡", "medium": "🟡", "slow": "🐌"}.get(speed, "")
        
        markup.add(types.InlineKeyboardButton(
            f"{speed_icon} {name} x{dmg_mult} [{mana}MP] CD:{cd}",
            callback_data=f"duel_skill_{sid}"
        ))
    
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="duel_back_target"))
    
    try:
        bot.edit_message_text(state_text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "duel_back_target")
def duel_back_target(call):
    user_id = call.from_user.id
    duel = active_duels.get(str(user_id))
    if duel:
        show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_skill_"))
def duel_skill_selected(call):
    user_id = call.from_user.id
    skill_id = call.data.split("_", 2)[2]
    
    duel = active_duels.get(str(user_id))
    if not duel or not duel.active:
        bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
        return
    
    target = temp_target.get(str(user_id), "body")
    pn = 1 if str(user_id) == duel.p1_id else 2
    
    duel.set_attack(pn, skill_id, target)
    
    bot.answer_callback_query(call.id, "⚔ Атака!")
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_"))
def duel_action_handler(call):
    user_id = call.from_user.id
    action = call.data.split("_", 1)[1]
    
    duel = active_duels.get(str(user_id))
    
    if action == "refresh":
        if duel and duel.active:
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
            bot.answer_callback_query(call.id, "✅")
        else:
            bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
    
    elif action == "wait":
        if duel and duel.active:
            # Проверяем ход бота
            pn = 1 if str(user_id) == duel.p1_id else 2
            other_pn = 3 - pn
            other_phase = duel.p2_phase if pn == 1 else duel.p1_phase
            
            # Бот делает ход автоматически
            if str(duel.p2_id).startswith("bot_") and other_pn == 2:
                if other_phase == "defend_select":
                    duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
                elif other_phase == "attack_select":
                    skills = duel.get_available_skills(2)
                    if skills:
                        duel.set_attack(2, random.choice(skills), random.choice(list(BODY_PARTS.keys())))
            
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
            bot.answer_callback_query(call.id, "✅")
    
    elif action == "surrender":
        if duel and duel.active:
            duel.active = False
            duel.winner = 2 if str(user_id) == duel.p1_id else 1
            finish_duel(call.message.chat.id, call.message.message_id, duel, user_id)
            bot.answer_callback_query(call.id, "🏳 Вы сдались")
    
    elif action.startswith("defend_"):
        part = action.split("_")[1]
        if duel and duel.active:
            pn = 1 if str(user_id) == duel.p1_id else 2
            duel.set_defend(pn, part)
            bot.answer_callback_query(call.id, f"🛡 {BODY_PARTS[part]['name']}")
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

def finish_duel(chat_id, message_id, duel, user_id):
    """Завершение дуэли и отправка результатов"""
    # Очистка
    for uid in [duel.p1_id, duel.p2_id]:
        if uid in active_duels and active_duels[uid].battle_id == duel.battle_id:
            del active_duels[uid]
    
    # Удаление ботов
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") and uid in users:
            del users[uid]
    save_json(DATA_FILES['users'], users)
    
    if duel.winner == 0:
        result_text = f"<b>🤝 НИЧЬЯ!</b>\nХодов: {duel.turn}"
        
        # Отправляем обоим
        try:
            bot.send_message(int(duel.p1_id), result_text)
        except:
            pass
        try:
            bot.send_message(int(duel.p2_id), result_text)
        except:
            pass
        
        bot.edit_message_text(result_text, chat_id, message_id)
        return
    
    winner_id = duel.p1_id if duel.winner == 1 else duel.p2_id
    loser_id = duel.p2_id if duel.winner == 1 else duel.p1_id
    
    winner_name = duel.get_player_name(duel.winner)
    loser_name = duel.get_player_name(3 - duel.winner)
    
    # Награды
    if duel.bet > 0:
        if not winner_id.startswith("bot_"):
            winner_p = Player(winner_id)
            winner_p.data["money"] += duel.bet * 2
            winner_p.save()
    
    # Статистика
    if not winner_id.startswith("bot_"):
        wp = Player(winner_id)
        wp.data["wins"] += 1
        wp.data["win_streak"] += 1
        wp.data["total_duels"] += 1
        wp.data["pvp_rating"] += random.randint(20, 35)
        if wp.data["win_streak"] > wp.data["best_streak"]:
            wp.data["best_streak"] = wp.data["win_streak"]
        exp_w = duel.turn * 10 + duel.bet // 2
        wp.data["exp"] += exp_w
        wp.data["total_exp"] += exp_w
        check_level_up(wp)
        wp.save()
    
    if not loser_id.startswith("bot_"):
        lp = Player(loser_id)
        lp.data["losses"] += 1
        lp.data["win_streak"] = 0
        lp.data["total_duels"] += 1
        lp.data["pvp_rating"] = max(0, lp.data["pvp_rating"] - random.randint(10, 25))
        exp_l = duel.turn * 5 + duel.bet // 5
        lp.data["exp"] += exp_l
        lp.data["total_exp"] += exp_l
        check_level_up(lp)
        lp.save()
    
    winner_text = f"""
<b>🏆 ПОБЕДА!</b>

Противник: {loser_name}
💰 Приз: <b>{duel.bet * 2 if duel.bet > 0 else 0}💰</b>
📊 Ходов: {duel.turn}
"""
    
    loser_text = f"""
<b>💀 ПОРАЖЕНИЕ</b>

Противник: {winner_name}
💰 Потеряно: <b>{duel.bet}💰</b>
📊 Ходов: {duel.turn}
"""
    
    # Отправляем результаты обоим игрокам
    try:
        if not winner_id.startswith("bot_"):
            bot.send_message(int(winner_id), winner_text)
    except:
        pass
    
    try:
        if not loser_id.startswith("bot_"):
            bot.send_message(int(loser_id), loser_text)
    except:
        pass
    
    # Обновляем сообщение дуэли
    result_display = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

👑 <b>{winner_name}</b> побеждает!
💀 <b>{loser_name}</b> проигрывает

💰 Ставка: <b>{duel.bet}💰</b>
📊 Ходов: <b>{duel.turn}</b>
"""
    
    try:
        bot.edit_message_text(result_display, chat_id, message_id)
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
    bot.edit_message_text(
        f"<b>🛒 МАГАЗИН</b>\n💰 <b>{player.data['money']}💰</b>",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

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
        elif item.get("type") in ["helmet", "armor", "boots"]:
            s = f"Броня: Г:{item.get('armor_head',0)} Т:{item.get('armor_body',0)} Н:{item.get('armor_legs',0)}"
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
            markup.add(types.InlineKeyboardButton(
                f"Купить: {item['name']} - {item['price']}💰",
                callback_data=f"buyitem_{ik}"
            ))
    
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

@bot.callback_query_handler(func=lambda call: call.data == "trade_market")
def market_menu(call):
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
    market_menu(call)

@bot.callback_query_handler(func=lambda call: call.data in ["trade_sell", "trade_my_lots", "back_to_trade"])
def trade_handlers(call):
    if call.data == "trade_sell":
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
    d = player.data
    
    wr = (d["wins"] / d["total_duels"] * 100) if d["total_duels"] > 0 else 0
    
    text = f"""
<b>📊 СТАТИСТИКА</b>

<b>{d['first_name']}</b> | @{d['username']}
⭐ Ур.{d['level']} | 📊 {d['pvp_rating']}
💰 {d['money']}💰

🛡 Броня: Г:{player.get_armor_for_part('head')} Т:{player.get_armor_for_part('body')} Н:{player.get_armor_for_part('legs')}
❤ HP: {player.get_max_hp()}

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
        
        markup.add(types.InlineKeyboardButton(f"Продать {item['name']}", callback_data=f"sellitem_{idx-1}"))
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
        bot.answer_callback_query(call.id, "❌ Нельзя!")
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
    player.data.setdefault("enchantments", {})[ik] = {
        "name": ench["name"],
        "effect": ench["effect"],
        "value": ench["value"]
    }
    player.save()
    
    bot.answer_callback_query(call.id, f"✨ {ench['name']}!")
    hero_inventory(call)

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
    hero_inventory(call)

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
    
    max_hp = player.get_max_hp()
    
    if "heal" in item:
        if player.data["hp"] >= max_hp:
            bot.answer_callback_query(call.id, "❌ Полное HP!")
            return
        player.data["hp"] = min(max_hp, player.data["hp"] + item["heal"])
    
    if "mana_restore" in item:
        player.data["mana"] = min(50, player.data["mana"] + item["mana_restore"])
    
    player.data["inventory"].remove(ik)
    player.save()
    
    bot.answer_callback_query(call.id, "✅ Использовано!")
    hero_inventory(call)

@bot.callback_query_handler(func=lambda call: call.data in ["hero_achievements", "hero_enchantments", "hero_equipped", "hero_history", "hero_heal", "back_to_hero"])
def hero_handlers(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "hero_achievements":
        ach_list = [
            ("first_blood", "🩸 Первая кровь", player.data["wins"] >= 1),
            ("warrior", "⚔ Воин", player.data["wins"] >= 10),
            ("veteran", "🎖 Ветеран", player.data["wins"] >= 50),
            ("legend", "👑 Легенда", player.data["wins"] >= 100),
            ("rich", "💰 Богач", player.data["money"] >= 10000)
        ]
        
        text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(player.data['achievements'])}/5)\n\n"
        
        for aid, name, cond in ach_list:
            done = aid in player.data["achievements"] or cond
            icon = "✅" if done else "🔒"
            text += f"{icon} <b>{name}</b>\n"
            if cond and aid not in player.data["achievements"]:
                player.data["achievements"].append(aid)
        
        player.save()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_enchantments":
        ench_data = player.data.get("enchantments", {})
        if not ench_data:
            bot.edit_message_text("✨ Нет зачарований", call.message.chat.id, call.message.message_id)
            return
        
        text = "<b>✨ ЗАЧАРОВАНИЯ</b>\n\n"
        for ik, ench in ench_data.items():
            item = items.get(ik) or limited_items.get(ik)
            if item:
                text += f"📦 {item['name']}: <b>{ench.get('name', 'Нет')}</b>\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_equipped":
        equip = player.data["equipment"]
        text = "<b>👁 ЭКИПИРОВКА</b>\n\n"
        slot_names = {"weapon": "⚔ Оружие", "head": "👤 Голова", "body": "🦾 Тело", "legs": "🦿 Ноги"}
        
        for slot, sn in slot_names.items():
            ik = equip.get(slot)
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
        markup.add(
            types.InlineKeyboardButton("🔴 Снять всё", callback_data="unequip_all"),
            types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_history":
        history = player.data.get("battle_history", [])
        if not history:
            bot.edit_message_text("📋 История пуста", call.message.chat.id, call.message.message_id)
            return
        
        text = "<b>📋 ПОСЛЕДНИЕ 10 БОЁВ</b>\n\n"
        for battle in history[-10:]:
            icon = "🏆" if battle.get("result") == "win" else "💀"
            text += f"{icon} vs {battle.get('opponent', 'Нет')}\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_heal":
        max_hp = player.get_max_hp()
        potions = [k for k in player.data["inventory"] if items.get(k, {}).get("type") == "potion" and items.get(k, {}).get("heal", 0) > 0]
        
        if not potions:
            bot.edit_message_text("💊 Нет зелий!", call.message.chat.id, call.message.message_id)
            return
        
        if player.data["hp"] >= max_hp:
            bot.edit_message_text("💊 Полное здоровье!", call.message.chat.id, call.message.message_id)
            return
        
        pk = potions[0]
        potion = items[pk]
        
        player.data["hp"] = min(max_hp, player.data["hp"] + potion["heal"])
        player.data["inventory"].remove(pk)
        player.save()
        
        bot.edit_message_text(f"💊 <b>{potion['name']}</b>\n❤ HP: {player.data['hp']}/{max_hp}", call.message.chat.id, call.message.message_id)
    
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
    bot.answer_callback_query(call.id, "✅ Всё снято!")
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
        bot.answer_callback_query(call.id, f"❌ Нужен {level_reqs[dl-1]} ур.!")
        return
    
    if player.data.get("last_dungeon"):
        last = datetime.fromisoformat(player.data["last_dungeon"])
        if (datetime.now() - last) < timedelta(hours=1):
            r = timedelta(hours=1) - (datetime.now() - last)
            bot.answer_callback_query(call.id, f"⏰ {r.seconds//60} мин.")
            return
    
    # Запуск цепочки из 3 боёв
    bot.edit_message_text(f"⚔ Начинается зачистка подземелья! Бой 1/3", call.message.chat.id, call.message.message_id)
    
    # Создаём босса и дуэль
    boss_level = level_reqs[dl - 1] * 2 + random.randint(1, 3)
    boss_id = f"boss_{random.randint(100000, 999999)}"
    
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    slot_item_types = {"head": "helmet", "body": "armor", "legs": "boots"}
    for slot, itype in slot_item_types.items():
        slot_items = [k for k, v in items.items() if v.get("type") == itype and v.get("level_req", 1) <= boss_level]
        if slot_items and random.random() < 0.8:
            equip[slot] = random.choice(slot_items)
    wpns = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= boss_level]
    if wpns:
        equip["weapon"] = random.choice(wpns)
    
    boss_names_1 = ["🐺 Волк-страж", "🕷 Паук-охотник", "💀 Скелет-воин", "🐉 Молодой дракон", "👹 Бес"]
    
    users[boss_id] = {
        "username": f"Boss_{boss_level}", "first_name": boss_names_1[dl - 1],
        "money": 0, "level": boss_level, "exp": 0, "total_exp": 0,
        "hp": 100 + boss_level * 12, "max_hp": 100 + boss_level * 12,
        "mana": 50, "max_mana": 50,
        "wins": 0, "losses": 0, "draws": 0,
        "win_streak": 0, "best_streak": 0, "total_duels": 0,
        "pvp_rating": 1000, "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Босс", "titles_collected": ["Босс"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    player.data["last_dungeon"] = datetime.now().isoformat()
    player.save()
    
    duel = DuelInstance(user_id, boss_id, "dungeon_1", 0)
    active_duels[str(user_id)] = duel
    active_duels[boss_id] = duel
    
    bot_def = random.choice(list(BODY_PARTS.keys()))
    duel.set_defend(2, bot_def)
    boss_skills = duel.get_available_skills(2)
    if boss_skills:
        duel.set_attack(2, random.choice(boss_skills), random.choice(list(BODY_PARTS.keys())))
    
    show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "world_bosses")
def world_bosses_menu(call):
    if not world_bosses.get("active"):
        # Создаём мирового босса
        world_bosses["active"] = {
            "name": "🐉 Древний дракон",
            "hp": 1000000,
            "max_hp": 1000000,
            "attackers": [],
            "total_damage": 0,
            "reward": 50000,
            "expires": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        save_json(DATA_FILES['world_bosses'], world_bosses)
    
    wb = world_bosses["active"]
    pct = wb["hp"] / wb["max_hp"] * 100
    
    text = f"""
<b>👹 МИРОВОЙ БОСС</b>

<b>{wb['name']}</b>
❤ HP: {wb['hp']:,} / {wb['max_hp']:,} ({pct:.1f}%)
👥 Атаковало: {len(wb['attackers'])} игроков
💰 Награда: <b>{wb['reward']}💰</b> (делится между всеми)

Каждая атака стоит 100💰 и наносит случайный урон!
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚔ Атаковать (100💰)", callback_data="wb_attack"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world")
    )
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "wb_attack")
def wb_attack(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data["money"] < 100:
        bot.answer_callback_query(call.id, "❌ Нужно 100💰!")
        return
    
    wb = world_bosses.get("active", {})
    if wb.get("hp", 0) <= 0:
        bot.answer_callback_query(call.id, "✅ Босс уже повержен!")
        return
    
    player.data["money"] -= 100
    player.save()
    
    # Наносим урон
    dmg_range = player.get_damage_range()
    dmg = random.randint(dmg_range[0] * 10, dmg_range[1] * 10)
    wb["hp"] -= dmg
    
    if str(user_id) not in wb["attackers"]:
        wb["attackers"].append(str(user_id))
    wb["total_damage"] = wb.get("total_damage", 0) + dmg
    
    if wb["hp"] <= 0:
        wb["hp"] = 0
        # Раздача награды
        reward_per_player = wb["reward"] // max(1, len(wb["attackers"]))
        for uid in wb["attackers"]:
            p = Player(uid)
            p.data["money"] += reward_per_player
            p.save()
        
        save_json(DATA_FILES['world_bosses'], world_bosses)
        
        # Уведомление всем
        for uid in wb["attackers"]:
            try:
                bot.send_message(int(uid), f"👹 <b>{wb['name']}</b> повержен!\n💰 Ваша доля: <b>{reward_per_player}💰</b>")
            except:
                pass
        
        bot.edit_message_text(f"👹 Босс повержен! Вы нанесли {dmg} урона!", call.message.chat.id, call.message.message_id)
    else:
        save_json(DATA_FILES['world_bosses'], world_bosses)
        bot.edit_message_text(f"⚔ Вы нанесли <b>{dmg}</b> урона!\n❤ HP босса: {wb['hp']:,}", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "world_clans")
def world_clans(call):
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
        
        clans[name] = {"leader_id": user_id, "leader_name": message.from_user.first_name, "members": [message.from_user.first_name], "treasury": 0, "created_at": datetime.now().isoformat()}
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
            "rounds": [],
            "current_round": 0,
            "prize_pool": 5000,
            "status": "registration",
            "started_at": datetime.now().isoformat()
        }
        save_json(DATA_FILES['tournaments'], tournaments)
    
    tour = tournaments["active"]
    
    text = f"""
<b>🏟 ТУРНИР</b>

<b>{tour['name']}</b>
Статус: {tour.get('status', 'Ожидание')}
Участников: {len(tour.get('participants', []))}
Приз: <b>{tour.get('prize_pool', 0)}💰</b>
Взнос: 500💰

Формат: плей-офф (1/8 → 1/4 → 1/2 → Финал)
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
        try:
            p = Player(uid)
            text += f"{i}. {p.data['first_name']} (Lv.{p.data['level']})\n"
        except:
            text += f"{i}. {uid}\n"
    bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == "world_events")
def world_events(call):
    current_event = events.get("current", {})
    if not current_event or datetime.fromisoformat(current_event.get("expires", "2000-01-01")) < datetime.now():
        new_event = {
            "name": random.choice(["🌋 Извержение", "❄ Шторм", "⚡ Гроза", "🌑 Затмение", "✨ Звездопад"]),
            "description": random.choice(["Двойной опыт в дуэлях!", "+50% монет в данжах!", "Шанс зачарования +20%!"]),
            "ench_reward": random.choice(ENCHANT_EFFECTS) if random.random() < 0.5 else None,
            "reward_money": random.randint(100, 500) if random.random() < 0.5 else 0,
            "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        events["current"] = new_event
        save_json(DATA_FILES['events'], events)
        
        # Рассылка ивента всем игрокам
        for uid in users:
            try:
                bot.send_message(int(uid), f"🌍 <b>НОВЫЙ ИВЕНТ!</b>\n\n<b>{new_event['name']}</b>\n{new_event['description']}\n⏰ {10} мин.")
            except:
                pass
    
    ev = events["current"]
    time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
    minutes_left = max(0, time_left.seconds // 60)
    
    text = f"""
<b>🌍 ТЕКУЩИЙ ИВЕНТ</b>

<b>{ev['name']}</b>
📝 {ev['description']}
⏰ Осталось: {minutes_left} мин.
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

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

@bot.callback_query_handler(func=lambda call: call.data == "world_help")
def world_help(call):
    text = """
<b>ℹ ПОМОЩЬ</b>

<b>Дуэли:</b>
/quick - быстрая с ботом
/invite_duel [тип] [ставка] - пригласить

<b>Бой:</b>
🛡 Защита → ⏳ Ожидание → 🎯 Атака

<b>Команды:</b>
/sell [номер] [цена] - продать на рынке
/transfer [номер] - передать предмет
/createclan [имя] - создать клан
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_world")
def back_to_world(call):
    world_section(call.message)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================
def check_level_up(player):
    level = player.data["level"]
    exp_needed = int(100 * (1.5 ** (level - 1)))
    
    while player.data["exp"] >= exp_needed:
        player.data["exp"] -= exp_needed
        player.data["level"] += 1
        player.data["max_hp"] += 15
        player.data["hp"] = player.data["max_hp"]
        player.data["mana"] = 50
        
        titles = {5: "Боец", 10: "Воитель", 15: "Рыцарь", 20: "Ветеран",
                  25: "Мастер", 30: "Грандмастер", 40: "Герой", 50: "Легенда",
                  60: "Мифический воин", 75: "Полубог", 100: "Божество"}
        
        for req, title in titles.items():
            if player.data["level"] >= req and title not in player.data["titles_collected"]:
                player.data["titles_collected"].append(title)
                player.data["title"] = title
        
        level = player.data["level"]
        exp_needed = int(100 * (1.5 ** (level - 1)))

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

# ==================== АДМИН ====================
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
        types.InlineKeyboardButton("✅ Разбан", callback_data="admin_unban"),
        types.InlineKeyboardButton("🏟 Турнир", callback_data="admin_tournament"),
        types.InlineKeyboardButton("👹 Босс", callback_data="admin_wboss")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_handlers(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    action = call.data.split("_")[1]
    
    if action == "stats":
        text = f"👥 {len(users)} | 💰 {sum(u.get('money',0) for u in users.values())} | ⚔ {sum(u.get('total_duels',0) for u in users.values())}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    
    elif action == "givemoney":
        bot.send_message(call.message.chat.id, "💰 /givemoney @username [сумма]")
    elif action == "giveitem":
        bot.send_message(call.message.chat.id, "🎁 /giveitem @username [item_key]")
    elif action == "banuser":
        bot.send_message(call.message.chat.id, "⛔ /ban @username [причина]")
    elif action == "broadcast":
        bot.send_message(call.message.chat.id, "📢 /broadcast [текст]")
    elif action == "reset":
        bot.send_message(call.message.chat.id, "🔄 /resetdaily @username")
    elif action == "info":
        bot.send_message(call.message.chat.id, "👁 /userinfo @username")
    elif action == "unban":
        bot.send_message(call.message.chat.id, "✅ /unban @username")
    elif action == "tournament":
        bot.send_message(call.message.chat.id, "🏟 /start_tournament [имя] [взнос]")
    elif action == "wboss":
        bot.send_message(call.message.chat.id, "👹 /create_wboss [имя] [hp] [награда]")

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'broadcast', 'resetdaily', 'userinfo', 'start_tournament', 'create_wboss'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    try:
        if cmd == "givemoney":
            username = parts[1].replace('@', '')
            amount = int(parts[2])
            for uid, data in users.items():
                if data.get("username") == username:
                    p = Player(uid)
                    p.data["money"] += amount
                    p.save()
                    bot.send_message(message.chat.id, f"✅ {amount}💰 → @{username}")
                    return
            bot.send_message(message.chat.id, "❌ Пользователь не найден по username")
        
        elif cmd == "giveitem":
            username = parts[1].replace('@', '')
            ik = parts[2]
            for uid, data in users.items():
                if data.get("username") == username:
                    p = Player(uid)
                    p.data["inventory"].append(ik)
                    p.save()
                    bot.send_message(message.chat.id, f"✅ {ik} → @{username}")
                    return
            bot.send_message(message.chat.id, "❌ Пользователь не найден по username")
        
        elif cmd == "ban":
            username = parts[1].replace('@', '')
            reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение"
            for uid, data in users.items():
                if data.get("username") == username:
                    banned_users[uid] = {"reason": reason, "banned_at": datetime.now().isoformat()}
                    save_json(DATA_FILES['bans'], banned_users)
                    bot.send_message(message.chat.id, f"⛔ @{username} забанен!")
                    return
            bot.send_message(message.chat.id, "❌ Пользователь не найден по username")
        
        elif cmd == "unban":
            username = parts[1].replace('@', '')
            for uid, data in users.items():
                if data.get("username") == username and uid in banned_users:
                    del banned_users[uid]
                    save_json(DATA_FILES['bans'], banned_users)
                    bot.send_message(message.chat.id, f"✅ @{username} разбанен!")
                    return
            bot.send_message(message.chat.id, "❌ Не найден в бане")
        
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
            for uid, data in users.items():
                if data.get("username") == username:
                    p = Player(uid)
                    p.data["last_daily"] = None
                    p.data["last_dungeon"] = None
                    p.save()
                    bot.send_message(message.chat.id, f"✅ @{username}")
                    return
            bot.send_message(message.chat.id, "❌ Не найден")
        
        elif cmd == "userinfo":
            username = parts[1].replace('@', '')
            for uid, data in users.items():
                if data.get("username") == username:
                    p = Player(uid)
                    d = p.data
                    text = f"<b>👤 @{username}</b>\nID: {uid}\nИмя: {d['first_name']}\nУр.: {d['level']}\n💰 {d['money']}\nРейтинг: {d['pvp_rating']}\nКлан: {d.get('clan', 'Нет')}"
                    bot.send_message(message.chat.id, text)
                    return
            bot.send_message(message.chat.id, "❌ Не найден по username")
        
        elif cmd == "start_tournament":
            name = parts[1] if len(parts) > 1 else "Турнир"
            fee = int(parts[2]) if len(parts) > 2 else 500
            tournaments["active"] = {
                "name": name, "participants": [], "rounds": [],
                "current_round": 0, "prize_pool": fee * 8,
                "status": "registration", "started_at": datetime.now().isoformat()
            }
            save_json(DATA_FILES['tournaments'], tournaments)
            bot.send_message(message.chat.id, f"✅ Турнир <b>{name}</b> создан! Взнос: {fee}💰")
        
        elif cmd == "create_wboss":
            name = parts[1] if len(parts) > 1 else "Мировой босс"
            hp = int(parts[2]) if len(parts) > 2 else 1000000
            reward = int(parts[3]) if len(parts) > 3 else 50000
            world_bosses["active"] = {
                "name": name, "hp": hp, "max_hp": hp,
                "attackers": [], "total_damage": 0,
                "reward": reward,
                "expires": (datetime.now() + timedelta(hours=24)).isoformat()
            }
            save_json(DATA_FILES['world_bosses'], world_bosses)
            
            # Рассылка всем
            for uid in users:
                try:
                    bot.send_message(int(uid), f"👹 <b>МИРОВОЙ БОСС ПОЯВИЛСЯ!</b>\n\n<b>{name}</b>\n❤ HP: {hp:,}\n💰 Награда: {reward:,}💰")
                except:
                    pass
            
            bot.send_message(message.chat.id, f"✅ Мировой босс <b>{name}</b> создан!")
    
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
    print("✅ Броня поглощает урон (не даёт HP)")
    print("✅ Защита → Ожидание → Атака")
    print("✅ 3 типа атак: быстрая/средняя/медленная")
    print("✅ Таймаут 60 сек")
    print("✅ Мировые боссы 1M HP")
    print("✅ Турниры с плей-офф")
    print("✅ Ивенты приходят в ЛС")
    print("✅ Админ через @username")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
