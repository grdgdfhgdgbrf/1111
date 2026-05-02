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
TOKEN = '8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE'
ADMIN_ID = 5356400377
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ==================== КОНСТАНТЫ ====================
BODY_PARTS = {
    "head": {"name": "👤 Голова", "multiplier": 1.5},
    "body": {"name": "🦾 Тело", "multiplier": 1.0},
    "legs": {"name": "🦿 Ноги", "multiplier": 0.7}
}

RARITY_COLORS = {
    "common": "⬜", "uncommon": "🟩", "rare": "🟦",
    "epic": "🟪", "legendary": "🟧", "mythic": "🟥",
    "divine": "💛", "apocalyptic": "🖤"
}

ENCHANT_EFFECTS = [
    {"name": "🔥 Огненное", "effect": "fire_damage", "value": 15},
    {"name": "❄ Ледяное", "effect": "freeze_chance", "value": 20},
    {"name": "⚡ Грозовое", "effect": "stun_chance", "value": 15},
    {"name": "💀 Проклятое", "effect": "life_steal", "value": 12},
    {"name": "🛡 Укреплённое", "effect": "defense_bonus", "value": 20},
    {"name": "💪 Мощное", "effect": "damage_boost", "value": 30},
    {"name": "💨 Скоростное", "effect": "speed_bonus", "value": 15},
    {"name": "❤ Живучее", "effect": "hp_bonus", "value": 60},
    {"name": "🎯 Меткое", "effect": "crit_bonus", "value": 20}
]

# ==================== ФАЙЛЫ ====================
DATA_FILES = {
    'users': 'users.json', 'items': 'items.json', 'limited': 'limited_items.json',
    'clans': 'clans.json', 'tournaments': 'tournaments.json', 'market': 'market.json',
    'dungeons': 'dungeon_progress.json', 'events': 'events.json', 'bans': 'bans.json',
    'enchantments': 'enchantments.json', 'matchmaking': 'matchmaking.json',
    'active_tournaments': 'active_tournaments.json'
}

def load_json(filename, default=None):
    if default is None: default = {}
    try:
        with open(filename, 'r', encoding='utf-8') as f: return json.load(f)
    except: 
        save_json(filename, default)
        return default

def save_json(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e: print(f"Error: {e}")

# ==================== ПРЕДМЕТЫ ====================
HELMETS = {
    "leather_cap": {"name": "🎓 Кожаная шапка", "defense": 3, "price": 60, "type": "helmet", "slot": "head", "rarity": "common", "level_req": 1},
    "iron_helmet": {"name": "⛑ Железный шлем", "defense": 8, "price": 250, "type": "helmet", "slot": "head", "rarity": "uncommon", "level_req": 6},
    "dragon_helmet": {"name": "🐉 Шлем дракона", "defense": 18, "price": 2000, "type": "helmet", "slot": "head", "rarity": "epic", "level_req": 20}
}

ARMORS = {
    "leather_vest": {"name": "🧥 Кожаный жилет", "defense": 5, "price": 80, "type": "armor", "slot": "body", "rarity": "common", "level_req": 1},
    "chainmail": {"name": "⛓ Кольчуга", "defense": 12, "price": 400, "type": "armor", "slot": "body", "rarity": "uncommon", "level_req": 8},
    "plate_armor": {"name": "🛡 Латный доспех", "defense": 22, "price": 1500, "type": "armor", "slot": "body", "rarity": "rare", "level_req": 15},
    "phoenix_armor": {"name": "🦅 Броня феникса", "defense": 40, "price": 8000, "type": "armor", "slot": "body", "rarity": "legendary", "level_req": 30}
}

BOOTS = {
    "leather_boots": {"name": "👢 Кожаные сапоги", "defense": 2, "speed": 8, "price": 100, "type": "boots", "slot": "legs", "rarity": "common", "level_req": 1},
    "wind_boots": {"name": "🌪 Сапоги ветра", "defense": 4, "speed": 18, "price": 900, "type": "boots", "slot": "legs", "rarity": "rare", "level_req": 12},
    "blink_boots": {"name": "✨ Сапоги телепортации", "defense": 8, "speed": 28, "price": 4000, "type": "boots", "slot": "legs", "rarity": "epic", "level_req": 25}
}

WEAPONS = {
    "rusty_sword": {"name": "🗡 Ржавый меч", "damage": (5, 10), "price": 50, "type": "weapon", "slot": "weapon", "rarity": "common", "level_req": 1, "skills": ["quick_strike", "slash"]},
    "flame_blade": {"name": "🔥 Пламенный клинок", "damage": (12, 22), "price": 500, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 7, "skills": ["fire_slash", "inferno_strike", "flame_wave"], "element": "fire"},
    "frost_axe": {"name": "❄ Ледяной топор", "damage": (14, 24), "price": 800, "type": "weapon", "slot": "weapon", "rarity": "uncommon", "level_req": 10, "skills": ["frost_strike", "ice_shatter"], "element": "ice"},
    "shadow_dagger": {"name": "🌑 Теневой кинжал", "damage": (25, 40), "price": 4000, "type": "weapon", "slot": "weapon", "rarity": "epic", "level_req": 22, "skills": ["shadow_strike", "assassinate", "soul_drain"], "element": "dark"},
    "divine_spear": {"name": "✨ Божественное копьё", "damage": (32, 48), "price": 7000, "type": "weapon", "slot": "weapon", "rarity": "legendary", "level_req": 28, "skills": ["holy_strike", "divine_judgment"], "element": "light"}
}

POTIONS = {
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 40, "price": 40, "type": "potion", "rarity": "common", "level_req": 1},
    "big_health_potion": {"name": "🧪 Большое зелье", "heal": 90, "price": 120, "type": "potion", "rarity": "uncommon", "level_req": 8}
}

ALL_ITEMS = {}
ALL_ITEMS.update(HELMETS)
ALL_ITEMS.update(ARMORS)
ALL_ITEMS.update(BOOTS)
ALL_ITEMS.update(WEAPONS)
ALL_ITEMS.update(POTIONS)

# ==================== БАЗА НАВЫКОВ ====================
SKILLS_DB = {
    "quick_strike": {"name": "⚡ Быстрый удар", "damage_mult": 0.8, "mana_cost": 3, "cooldown": 0, "tier": 1},
    "slash": {"name": "🗡 Разрез", "damage_mult": 1.2, "mana_cost": 5, "cooldown": 0, "tier": 1},
    "fire_slash": {"name": "🔥 Огненный разрез", "damage_mult": 1.5, "mana_cost": 12, "cooldown": 1, "tier": 2, "element": "fire", "burn_chance": 30},
    "inferno_strike": {"name": "🌋 Инферно удар", "damage_mult": 2.2, "mana_cost": 25, "cooldown": 3, "tier": 3, "element": "fire", "burn_chance": 60},
    "flame_wave": {"name": "🔥 Волна пламени", "damage_mult": 2.8, "mana_cost": 35, "cooldown": 4, "tier": 4, "element": "fire", "aoe": True},
    "frost_strike": {"name": "❄ Ледяной удар", "damage_mult": 1.4, "mana_cost": 10, "cooldown": 1, "tier": 2, "element": "ice", "freeze_chance": 25},
    "ice_shatter": {"name": "💠 Ледяной раскол", "damage_mult": 2.0, "mana_cost": 22, "cooldown": 3, "tier": 3, "element": "ice", "freeze_chance": 50},
    "shadow_strike": {"name": "🌑 Теневой удар", "damage_mult": 1.6, "mana_cost": 15, "cooldown": 1, "tier": 2, "element": "dark", "poison_chance": 25},
    "assassinate": {"name": "🗡 Убийство", "damage_mult": 3.2, "mana_cost": 40, "cooldown": 4, "tier": 4, "element": "dark", "ignore_defense": 50},
    "soul_drain": {"name": "💀 Похищение души", "damage_mult": 2.0, "mana_cost": 28, "cooldown": 3, "tier": 3, "element": "dark", "life_steal": 0.3},
    "holy_strike": {"name": "✨ Святой удар", "damage_mult": 1.5, "mana_cost": 14, "cooldown": 1, "tier": 2, "element": "light"},
    "divine_judgment": {"name": "⚖ Божий суд", "damage_mult": 2.8, "mana_cost": 35, "cooldown": 4, "tier": 4, "element": "light"}
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
matchmaking_queue = load_json(DATA_FILES['matchmaking'], {"queue": {}, "duel_queue": [], "ranked_queue": [], "hardcore_queue": [], "sparring_queue": []})
active_tournaments = load_json(DATA_FILES['active_tournaments'], {})

# ==================== КЛАСС ИГРОКА ====================
class Player:
    def __init__(self, user_id, username="Unknown", first_name="Player"):
        self.user_id = str(user_id)
        if self.user_id not in users:
            users[self.user_id] = {
                "username": username if username else f"user_{user_id}",
                "first_name": first_name if first_name else "Игрок",
                "money": 500, "level": 1, "exp": 0, "total_exp": 0,
                "hp": 100, "max_hp": 100, "mana": 50, "max_mana": 50,
                "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
                "total_duels": 0, "pvp_rating": 1000,
                "inventory": [],
                "equipment": {"weapon": None, "head": None, "body": None, "legs": None},
                "enchantments": {},
                "last_daily": None, "last_dungeon": None,
                "title": "Новичок", "titles_collected": ["Новичок"],
                "achievements": [],
                "clan": None, "clan_role": None,
                "registration_date": datetime.now().isoformat(),
                "settings": {"notifications": True, "duel_requests": True},
                "battle_history": [], "dungeons_completed": 0, "items_found": 0
            }
            self.save()
    
    @property
    def data(self): return users.get(self.user_id, {})
    def save(self): save_json(DATA_FILES['users'], users)
    
    def get_defense_for_part(self, part):
        """Защита для части тела от экипировки"""
        defense = 0
        slot_map = {"head": "head", "body": "body", "legs": "legs"}
        slot = slot_map.get(part)
        if slot:
            ik = self.data["equipment"].get(slot)
            if ik:
                item = items.get(ik) or limited_items.get(ik)
                if item:
                    defense = item.get("defense", 0)
        return defense
    
    def get_weapon_damage(self):
        ik = self.data["equipment"].get("weapon")
        if ik:
            item = items.get(ik) or limited_items.get(ik)
            if item and "damage" in item:
                return item["damage"]
        return (3, 7)

# ==================== ПОШАГОВАЯ ДУЭЛЬ ====================
active_duels = {}

class DuelInstance:
    def __init__(self, p1_id, p2_id, duel_type="quick", bet=0):
        self.battle_id = str(uuid.uuid4())[:8]
        self.p1_id = str(p1_id)
        self.p2_id = str(p2_id)
        self.duel_type = duel_type
        self.bet = bet
        self.turn = 1
        self.max_turns = 30
        self.active = True
        self.winner = None
        self.log_p1 = []
        self.log_p2 = []
        
        self.p1 = Player(self.p1_id)
        self.p2 = Player(self.p2_id)
        
        # Базовые статы
        self.p1_damage = self.p1.get_weapon_damage()
        self.p2_damage = self.p2.get_weapon_damage()
        
        # HP одинаковые
        base_hp = 150
        self.p1_hp = base_hp
        self.p2_hp = base_hp
        self.p1_max_hp = base_hp
        self.p2_max_hp = base_hp
        
        self.p1_mp = 50
        self.p2_mp = 50
        self.p1_max_mp = 50
        self.p2_max_mp = 50
        
        # Фазы: раунд делится на два полураунда
        # Полураунд 1: P1 защищается, P2 атакует
        # Полураунд 2: P2 защищается, P1 атакует
        self.current_attacker = random.choice([1, 2])
        self.current_defender = 3 - self.current_attacker
        
        self.defender_defend = None
        self.attacker_target = None
        self.attacker_skill = None
        
        self.phase = "defend_select"  # defend_select, attack_select, attack_skill, done
        
        # Кулдауны
        self.p1_cooldowns = {}
        self.p2_cooldowns = {}
        
        # Эффекты
        self.p1_effects = []
        self.p2_effects = []
        
        # Таймер на ход (60 секунд)
        self.last_action_time = time.time()
        self.turn_timeout = 60
        
        # Арена
        self.arena = random.choice(["colosseum", "forest", "volcano", "tundra", "void"])
        
        msg = f"⚔ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>\n🏟 {self._arena_name()}\n💰 Ставка: {bet}💰"
        self.log_p1.append(msg)
        self.log_p2.append(msg)
        
        self._notify_players()
    
    def _arena_name(self):
        names = {"colosseum": "Колизей", "forest": "Лес", "volcano": "Вулкан", "tundra": "Тундра", "void": "Пустота"}
        return names.get(self.arena, self.arena)
    
    def _notify_players(self):
        """Отправить уведомление о текущей фазе"""
        pass
    
    def get_player_name(self, num):
        return self.p1.data["first_name"] if num == 1 else self.p2.data["first_name"]
    
    def check_timeout(self):
        """Проверка таймаута хода"""
        if time.time() - self.last_action_time > self.turn_timeout:
            # Игрок не сделал ход - авто-поражение
            self.active = False
            if self.phase == "defend_select":
                self.winner = self.current_attacker
            else:
                self.winner = self.current_defender
            return True
        return False
    
    def set_defend(self, player_num, part):
        """Защитник выбирает часть тела"""
        if player_num != self.current_defender:
            return False
        
        self.defender_defend = part
        self.phase = "attack_select"
        self.last_action_time = time.time()
        return True
    
    def set_attack_target(self, player_num, part):
        """Атакующий выбирает цель"""
        if player_num != self.current_attacker:
            return False
        
        self.attacker_target = part
        self.phase = "attack_skill"
        self.last_action_time = time.time()
        return True
    
    def execute_attack(self, player_num, skill_id):
        """Атакующий выбирает навык и выполняет атаку"""
        if player_num != self.current_attacker:
            return False
        
        self.attacker_skill = skill_id
        self._resolve_attack()
        return True
    
    def _resolve_attack(self):
        """Разрешение атаки"""
        attacker = self.current_attacker
        defender = self.current_defender
        
        # Данные
        a_damage = self.p1_damage if attacker == 1 else self.p2_damage
        a_cooldowns = self.p1_cooldowns if attacker == 1 else self.p2_cooldowns
        a_mp = self.p1_mp if attacker == 1 else self.p2_mp
        
        skill = SKILLS_DB.get(self.attacker_skill, {"name": "Атака", "damage_mult": 1.0, "mana_cost": 0, "cooldown": 0, "tier": 1})
        
        # Проверка маны
        mc = skill.get("mana_cost", 0)
        if a_mp < mc:
            self.log_p1.append(f"❌ {self.get_player_name(attacker)}: нет маны!")
            self.log_p2.append(f"❌ {self.get_player_name(attacker)}: нет маны!")
            self._switch_roles()
            return
        
        if attacker == 1:
            self.p1_mp -= mc
        else:
            self.p2_mp -= mc
        
        # Урон
        min_d, max_d = a_damage
        base_dmg = random.randint(min_d, max_d)
        dmg = int(base_dmg * skill.get("damage_mult", 1.0))
        
        # Модификатор части тела
        body_m = BODY_PARTS.get(self.attacker_target, {}).get("multiplier", 1.0)
        dmg = int(dmg * body_m)
        
        # Защита: если попали в незащищённую часть - полный урон
        # Если попали в защищённую - урон уменьшается на defence части тела
        if self.defender_defend == self.attacker_target:
            # Защитник угадал - урон уменьшен
            defense = (self.p1 if defender == 1 else self.p2).get_defense_for_part(self.attacker_target)
            reduction = defense / (defense + 50)
            dmg = int(dmg * (1 - reduction))
            
            msg = f"🛡 {self.get_player_name(attacker)} бьёт в {BODY_PARTS[self.attacker_target]['name']}, но {self.get_player_name(defender)} защитил! Урон снижен на {int(reduction*100)}%: <b>-{dmg} HP</b>"
        else:
            msg = f"⚔ {self.get_player_name(attacker)} бьёт в {BODY_PARTS[self.attacker_target]['name']} ({skill['name']}): <b>-{dmg} HP</b>"
        
        # Применение урона
        if defender == 1:
            self.p1_hp = max(0, self.p1_hp - dmg)
        else:
            self.p2_hp = max(0, self.p2_hp - dmg)
        
        self.log_p1.append(msg)
        self.log_p2.append(msg)
        
        # Кулдаун
        if skill.get("cooldown", 0) > 0:
            a_cooldowns[self.attacker_skill] = skill["cooldown"]
        
        # Уменьшение кулдаунов
        for sid in list(a_cooldowns.keys()):
            a_cooldowns[sid] -= 1
            if a_cooldowns[sid] <= 0:
                del a_cooldowns[sid]
        
        # Восстановление маны
        if attacker == 1:
            self.p1_mp = min(self.p1_max_mp, self.p1_mp + 5)
        else:
            self.p2_mp = min(self.p2_max_mp, self.p2_mp + 5)
        
        # Проверка смерти
        if self.p1_hp <= 0 or self.p2_hp <= 0:
            self._check_end()
            return
        
        # Переключение ролей
        self._switch_roles()
    
    def _switch_roles(self):
        """Смена атакующего и защитника"""
        self.current_attacker, self.current_defender = self.current_defender, self.current_attacker
        self.defender_defend = None
        self.attacker_target = None
        self.attacker_skill = None
        self.phase = "defend_select"
        self.turn += 1
        self.last_action_time = time.time()
        
        if self.turn > self.max_turns:
            self.active = False
            self.winner = 0
    
    def _check_end(self):
        self.active = False
        if self.p1_hp <= 0 and self.p2_hp <= 0:
            self.winner = 0
        elif self.p1_hp <= 0:
            self.winner = 2
        elif self.p2_hp <= 0:
            self.winner = 1
    
    def get_state_text(self, for_player_id):
        """Текст состояния для конкретного игрока"""
        pn = 1 if str(for_player_id) == self.p1_id else 2
        log = self.log_p1 if pn == 1 else self.log_p2
        
        def bar(cur, mx, icon):
            pct = cur / mx if mx > 0 else 0
            f = int(pct * 10)
            e = 10 - f
            return f"{icon} [{'█'*f}{'░'*e}] {cur}/{mx}"
        
        text = f"""
<b>⚔ ДУЭЛЬ #{self.battle_id}</b>
🏟 {self._arena_name()} | Ход: <b>#{self.turn}</b>

<b>{self.get_player_name(1)}</b>
{bar(self.p1_hp, self.p1_max_hp, '❤')}
💎 {self.p1_mp}/{self.p1_max_mp}

<b>{self.get_player_name(2)}</b>
{bar(self.p2_hp, self.p2_max_hp, '❤')}
💎 {self.p2_mp}/{self.p2_max_mp}
"""
        
        if self.phase == "defend_select" and self.current_defender == pn:
            text += "\n🛡 <b>Вы защищаетесь! Выберите часть тела:</b>"
        elif self.phase == "attack_select" and self.current_attacker == pn:
            text += "\n🎯 <b>Вы атакуете! Выберите цель:</b>"
        elif self.phase == "attack_skill" and self.current_attacker == pn:
            text += f"\n🎯 Цель: <b>{BODY_PARTS.get(self.attacker_target, {}).get('name', 'Тело')}</b>\n<b>Выберите навык:</b>"
        else:
            text += "\n⏳ <b>Ожидание хода противника...</b>"
        
        if log:
            text += f"\n\n<i>{log[-1][:150]}</i>"
        
        return text
    
    def get_available_skills(self, player_num):
        cooldowns = self.p1_cooldowns if player_num == 1 else self.p2_cooldowns
        player = self.p1 if player_num == 1 else self.p2
        weapon_key = player.data["equipment"].get("weapon")
        
        skills = []
        if weapon_key:
            weapon = items.get(weapon_key) or limited_items.get(weapon_key)
            if weapon and "skills" in weapon:
                for sid in weapon["skills"]:
                    if sid in SKILLS_DB and (sid not in cooldowns or cooldowns[sid] <= 0):
                        skills.append(sid)
        
        return skills

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
    first_name = message.from_user.first_name
    
    # Всегда обновляем username и first_name
    p = Player(user_id, username, first_name)
    if username and p.data.get("username") != username:
        p.data["username"] = username
        p.save()
    if first_name and p.data.get("first_name") != first_name:
        p.data["first_name"] = first_name
        p.save()
    
    welcome = f"""
<b>⚔️ ДУЭЛЬ БОТ v11.0 ⚔️</b>

Добро пожаловать, <b>{first_name}</b>!

🎯 <b>НОВАЯ СИСТЕМА БОЯ:</b>
• Поочерёдные атаки
• Защита уменьшает урон
• Таймер на ход (60 сек)
• Разные типы дуэлей

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
        types.InlineKeyboardButton("💀 Хардкор (x3 ставка)", callback_data="hardcore_duel"),
        types.InlineKeyboardButton("🎯 Спарринг (без ставок)", callback_data="sparring_duel"),
        types.InlineKeyboardButton("⚡ Блиц-дуэль (30% HP)", callback_data="blitz_duel")
    )
    
    text = """
<b>⚔️ ДУЭЛИ</b>

<b>Виды дуэлей:</b>
⚡ Быстрая — бот, ставка 50-1000💰
👥 Поиск — найти игрока или бот
🏆 Рейтинговая — влияет на рейтинг
💀 Хардкор — ставка x3, высокий риск
🎯 Спарринг — без ставок
⚡ Блиц — 30% HP, быстрые бои
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
        types.InlineKeyboardButton("📦 Мои лоты", callback_data="trade_my_lots")
    )
    bot.send_message(message.chat.id, "<b>🏪 ТОРГОВЛЯ</b>", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🌍 Мир")
def world_section(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🏰 Подземелья", callback_data="world_dungeons"),
        types.InlineKeyboardButton("🛡 Кланы", callback_data="world_clans"),
        types.InlineKeyboardButton("🏟 Турниры", callback_data="world_tournaments"),
        types.InlineKeyboardButton("🌍 Ивенты", callback_data="world_events"),
        types.InlineKeyboardButton("📊 Топ", callback_data="world_top"),
        types.InlineKeyboardButton("ℹ Помощь", callback_data="world_help")
    )
    bot.send_message(message.chat.id, "<b>🌍 МИР</b>", reply_markup=markup)

# ==================== ДУЭЛИ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["quick_duel", "find_opponent", "ranked_duel", "hardcore_duel", "sparring_duel", "blitz_duel"])
def duel_type_handler(call):
    dt = call.data
    user_id = call.from_user.id
    player = Player(user_id)
    
    if dt == "quick_duel":
        markup = types.InlineKeyboardMarkup(row_width=3)
        for bet in [50, 100, 200, 500, 1000]:
            markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"qduel_{bet}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
        bot.edit_message_text(
            f"<b>⚡ БЫСТРАЯ ДУЭЛЬ</b>\n💰 Баланс: <b>{player.data['money']}💰</b>",
            call.message.chat.id, call.message.message_id, reply_markup=markup
        )
    
    elif dt == "find_opponent":
        start_matchmaking(call, "duel", 100)
    
    elif dt == "ranked_duel":
        start_matchmaking(call, "ranked", 100)
    
    elif dt == "hardcore_duel":
        markup = types.InlineKeyboardMarkup(row_width=3)
        for bet in [500, 1000, 2000, 5000]:
            markup.add(types.InlineKeyboardButton(f"{bet}💰", callback_data=f"hduel_{bet}"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_duels"))
        bot.edit_message_text(
            f"<b>💀 ХАРДКОР</b>\nСтавка x3!\n💰 Баланс: <b>{player.data['money']}💰</b>",
            call.message.chat.id, call.message.message_id, reply_markup=markup
        )
    
    elif dt == "sparring_duel":
        start_sparring(call)
    
    elif dt == "blitz_duel":
        start_blitz(call)

def start_matchmaking(call, duel_type, bet):
    user_id = str(call.from_user.id)
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    queue_key = f"{duel_type}_queue"
    queue = matchmaking_queue.get(queue_key, [])
    queue = [q for q in queue if q["user_id"] != user_id]
    
    if queue:
        opponent = queue.pop(0)
        matchmaking_queue[queue_key] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        if bet > 0:
            opp_player = Player(opponent["user_id"])
            if opp_player.data["money"] < bet:
                bot.edit_message_text("❌ У соперника недостаточно монет!", call.message.chat.id, call.message.message_id)
                return
            player.data["money"] -= bet
            opp_player.data["money"] -= bet
            player.save()
            opp_player.save()
        
        duel = DuelInstance(opponent["user_id"], user_id, duel_type, bet)
        active_duels[user_id] = duel
        active_duels[opponent["user_id"]] = duel
        
        try:
            bot.edit_message_text("⚔ Соперник найден! Дуэль начинается!", call.message.chat.id, call.message.message_id)
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        except:
            pass
        
        try:
            bot.send_message(opponent["user_id"], "⚔ Ваша дуэль начинается!")
        except:
            pass
    else:
        queue.append({"user_id": user_id, "type": duel_type, "bet": bet})
        matchmaking_queue[queue_key] = queue
        save_json(DATA_FILES['matchmaking'], matchmaking_queue)
        
        bot.edit_message_text("🔍 Поиск соперника... Через 5 сек — бот", call.message.chat.id, call.message.message_id)
        threading.Timer(5.0, create_bot_duel, args=[call.message.chat.id, call.message.message_id, user_id, duel_type, bet]).start()

def create_bot_duel(chat_id, message_id, user_id, duel_type, bet):
    if str(user_id) in active_duels:
        return
    
    player = Player(user_id)
    
    if bet > 0 and player.data["money"] < bet:
        return
    
    bot_level = random.randint(max(1, player.data["level"] - 3), player.data["level"] + 3)
    bot_id = f"bot_{random.randint(100000, 999999)}"
    
    # Экипировка бота
    equip = {"weapon": None, "head": None, "body": None, "legs": None}
    for slot, itype in [("head", "helmet"), ("body", "armor"), ("legs", "boots")]:
        sitems = [k for k, v in items.items() if v.get("type") == itype and v.get("level_req", 1) <= bot_level]
        if sitems and random.random() < 0.7:
            equip[slot] = random.choice(sitems)
    wpns = [k for k, v in items.items() if v.get("type") == "weapon" and v.get("level_req", 1) <= bot_level]
    if wpns:
        equip["weapon"] = random.choice(wpns)
    
    users[bot_id] = {
        "username": f"bot_{bot_id}", "first_name": f"🤖 Бот Lv.{bot_level}",
        "money": 0, "level": bot_level, "exp": 0, "total_exp": 0,
        "hp": 150, "max_hp": 150, "mana": 50, "max_mana": 50,
        "wins": 0, "losses": 0, "draws": 0, "win_streak": 0, "best_streak": 0,
        "total_duels": 0, "pvp_rating": 1000,
        "inventory": [], "equipment": equip, "enchantments": {},
        "last_daily": None, "last_dungeon": None,
        "title": "Бот", "titles_collected": ["Бот"],
        "achievements": [], "clan": None, "clan_role": None,
        "registration_date": datetime.now().isoformat(),
        "settings": {}, "battle_history": [], "dungeons_completed": 0, "items_found": 0
    }
    save_json(DATA_FILES['users'], users)
    
    if bet > 0:
        player.data["money"] -= bet
        player.save()
    
    duel = DuelInstance(user_id, bot_id, duel_type, bet)
    active_duels[str(user_id)] = duel
    
    try:
        bot.edit_message_text("⚔ Соперник не найден. Бой с ботом!", chat_id, message_id)
        show_duel_interface(chat_id, message_id, duel, user_id)
    except:
        pass

def start_sparring(call):
    create_bot_duel(call.message.chat.id, call.message.message_id, str(call.from_user.id), "sparring", 0)

def start_blitz(call):
    player = Player(call.from_user.id)
    if player.data["money"] < 200:
        bot.answer_callback_query(call.id, "❌ Нужно 200💰!")
        return
    create_bot_duel(call.message.chat.id, call.message.message_id, str(call.from_user.id), "blitz", 200)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_duels")
def back_to_duels(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    duel_section(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qduel_"))
def start_quick_duel(call):
    user_id = call.from_user.id
    bet = int(call.data.split("_")[1])
    player = Player(user_id)
    
    if player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    create_bot_duel(call.message.chat.id, call.message.message_id, str(user_id), "quick", bet)

@bot.callback_query_handler(func=lambda call: call.data.startswith("hduel_"))
def start_hardcore_duel(call):
    user_id = call.from_user.id
    bet = int(call.data.split("_")[1]) * 3
    player = Player(user_id)
    
    if player.data["money"] < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}💰!")
        return
    
    create_bot_duel(call.message.chat.id, call.message.message_id, str(user_id), "hardcore", bet)

def show_duel_interface(chat_id, message_id, duel, user_id):
    """Показать интерфейс дуэли для игрока"""
    if duel.check_timeout():
        finish_duel(chat_id, message_id, duel)
        return
    
    if not duel.active:
        finish_duel(chat_id, message_id, duel)
        return
    
    state_text = duel.get_state_text(user_id)
    
    pn = 1 if str(user_id) == duel.p1_id else 2
    phase = duel.phase
    is_defender = (duel.current_defender == pn)
    is_attacker = (duel.current_attacker == pn)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if phase == "defend_select" and is_defender:
        for part, data in BODY_PARTS.items():
            defense = (duel.p1 if pn == 1 else duel.p2).get_defense_for_part(part)
            markup.add(types.InlineKeyboardButton(
                f"🛡 {data['name']} (DEF:{defense})",
                callback_data=f"duel_def_{part}"
            ))
    elif phase == "attack_select" and is_attacker:
        for part, data in BODY_PARTS.items():
            markup.add(types.InlineKeyboardButton(
                f"🎯 {data['name']} (x{data['multiplier']})",
                callback_data=f"duel_tgt_{part}"
            ))
    elif phase == "attack_skill" and is_attacker:
        skills = duel.get_available_skills(pn)
        for sid in skills:
            skill = SKILLS_DB.get(sid, {})
            name = skill.get("name", sid)
            mana = skill.get("mana_cost", 0)
            cd = skill.get("cooldown", 0)
            tier = skill.get("tier", 1)
            stars = "⭐" * tier
            markup.add(types.InlineKeyboardButton(
                f"{name} {stars} [{mana}MP] (CD:{cd})",
                callback_data=f"duel_skl_{sid}"
            ))
    else:
        markup.add(types.InlineKeyboardButton("⏳ Ожидание...", callback_data="duel_wait"))
    
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="duel_ref"))
    markup.add(types.InlineKeyboardButton("🏳 Сдаться", callback_data="duel_sur"))
    
    try:
        bot.edit_message_text(state_text[:4000], chat_id, message_id, reply_markup=markup)
    except Exception as e:
        print(f"Edit error: {e}")

# Сохраняем выбранную цель для атаки
temp_target = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_"))
def duel_action_handler(call):
    user_id = call.from_user.id
    action = call.data.split("_", 1)[1]
    
    if action in ["ref", "wait", "sur"]:
        duel = active_duels.get(str(user_id))
        if not duel or not duel.active:
            try:
                bot.edit_message_text("❌ Дуэль не найдена", call.message.chat.id, call.message.message_id)
            except:
                pass
            return
        
        if action == "ref":
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        
        elif action == "wait":
            # Проверяем ход бота
            pn = 1 if str(user_id) == duel.p1_id else 2
            other_pn = 3 - pn
            if str(duel.p2_id).startswith("bot_") and other_pn == 2:
                if duel.phase == "defend_select" and duel.current_defender == 2:
                    duel.set_defend(2, random.choice(list(BODY_PARTS.keys())))
                if duel.phase == "attack_select" and duel.current_attacker == 2:
                    duel.set_attack_target(2, random.choice(list(BODY_PARTS.keys())))
                if duel.phase == "attack_skill" and duel.current_attacker == 2:
                    skills = duel.get_available_skills(2)
                    if skills:
                        duel.execute_attack(2, random.choice(skills))
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
        
        elif action == "sur":
            duel.active = False
            duel.winner = 3 - (1 if str(user_id) == duel.p1_id else 2)
            finish_duel(call.message.chat.id, call.message.message_id, duel)
    
    elif action.startswith("def_"):
        part = action.split("_")[1]
        duel = active_duels.get(str(user_id))
        if duel and duel.active:
            pn = 1 if str(user_id) == duel.p1_id else 2
            if duel.set_defend(pn, part):
                bot.answer_callback_query(call.id, f"🛡 {BODY_PARTS[part]['name']}")
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
    
    elif action.startswith("tgt_"):
        part = action.split("_")[1]
        duel = active_duels.get(str(user_id))
        if duel and duel.active:
            pn = 1 if str(user_id) == duel.p1_id else 2
            if duel.set_attack_target(pn, part):
                temp_target[str(user_id)] = part
                bot.answer_callback_query(call.id, f"🎯 Цель: {BODY_PARTS[part]['name']}")
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)
    
    elif action.startswith("skl_"):
        sid = action.split("_")[1]
        duel = active_duels.get(str(user_id))
        if duel and duel.active:
            pn = 1 if str(user_id) == duel.p1_id else 2
            if duel.execute_attack(pn, sid):
                bot.answer_callback_query(call.id, "⚔ Атака!")
            show_duel_interface(call.message.chat.id, call.message.message_id, duel, user_id)

def finish_duel(chat_id, message_id, duel):
    """Завершение дуэли и отправка результатов обоим игрокам"""
    # Очистка
    for uid in [duel.p1_id, duel.p2_id]:
        if uid in active_duels and active_duels[uid].battle_id == duel.battle_id:
            del active_duels[uid]
    
    for uid in [duel.p1_id, duel.p2_id]:
        if uid.startswith("bot_") and uid in users:
            del users[uid]
    save_json(DATA_FILES['users'], users)
    
    if duel.winner == 0:
        result = "<b>🤝 НИЧЬЯ!</b>\nХодов: " + str(duel.turn)
        try:
            bot.edit_message_text(result, chat_id, message_id)
        except:
            pass
        return
    
    winner_id = duel.p1_id if duel.winner == 1 else duel.p2_id
    loser_id = duel.p2_id if duel.winner == 1 else duel.p1_id
    
    winner = Player(winner_id)
    loser = Player(loser_id)
    
    reward = duel.bet * 2 if duel.bet > 0 else 0
    
    if not winner_id.startswith("bot_"):
        winner.data["money"] += reward
        winner.data["wins"] += 1
        winner.data["win_streak"] += 1
        winner.data["total_duels"] += 1
        winner.data["pvp_rating"] += random.randint(20, 35)
        if winner.data["win_streak"] > winner.data["best_streak"]:
            winner.data["best_streak"] = winner.data["win_streak"]
        exp_w = duel.turn * 10 + reward // 2
        winner.data["exp"] += exp_w
        winner.data["total_exp"] += exp_w
        check_level_up(winner)
        winner.save()
    
    if not loser_id.startswith("bot_"):
        loser.data["losses"] += 1
        loser.data["win_streak"] = 0
        loser.data["total_duels"] += 1
        loser.data["pvp_rating"] = max(0, loser.data["pvp_rating"] - random.randint(10, 25))
        exp_l = duel.turn * 5 + reward // 5
        loser.data["exp"] += exp_l
        loser.data["total_exp"] += exp_l
        check_level_up(loser)
        loser.save()
    
    result_text = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

👑 <b>{duel.get_player_name(duel.winner)}</b> побеждает!
💀 <b>{duel.get_player_name(3 - duel.winner)}</b> проигрывает

💰 Приз: <b>{reward}💰</b>
📊 Ходов: <b>{duel.turn}</b>
"""
    
    # Отправляем результат обоим игрокам
    try:
        bot.edit_message_text(result_text, chat_id, message_id)
    except:
        try:
            bot.send_message(chat_id, result_text)
        except:
            pass
    
    # Отправляем результат второму игроку
    other_id = winner_id if str(chat_id) != winner_id else loser_id
    if not other_id.startswith("bot_"):
        try:
            bot.send_message(int(other_id), result_text)
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
            s = f"Защита: {item.get('defense', 0)}"
        elif item.get("type") == "potion":
            s = f"Лечение: {item.get('heal', 0)}"
        else:
            s = ""
        
        text += f"{r} <b>{item['name']}</b> — {s}\n💰 {item['price']}\n\n"
        
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
    
    player.data["money"] -= item["price"]
    player.data["inventory"].append(ik)
    player.data["items_found"] += 1
    player.save()
    
    bot.answer_callback_query(call.id, f"✅ {item['name']}!")
    shop_category(call)

# ==================== ГЕРОЙ ====================
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
        
        text += f"{idx}. {r} {item['name']} x{cnt}{eq}\n"
        
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
        bot.answer_callback_query(call.id, "❌ Не найден!")
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
        "name": ench["name"], "effect": ench["effect"], "value": ench["value"]
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
    
    if player.data["hp"] >= player.data["max_hp"] and "heal" in item:
        bot.answer_callback_query(call.id, "❌ Полное HP!")
        return
    
    if "heal" in item:
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + item["heal"])
    
    if "mana_restore" in item:
        player.data["mana"] = min(player.data["max_mana"], player.data["mana"] + item.get("mana_restore", 0))
    
    player.data["inventory"].remove(ik)
    player.save()
    
    bot.answer_callback_query(call.id, "✅ Использовано!")
    hero_inventory(call)

@bot.callback_query_handler(func=lambda call: call.data in ["hero_stats", "hero_achievements", "hero_enchantments", "hero_equipped", "hero_heal", "back_to_hero"])
def hero_handlers(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "hero_stats":
        d = player.data
        wr = (d["wins"] / d["total_duels"] * 100) if d["total_duels"] > 0 else 0
        
        text = f"""
<b>📊 СТАТИСТИКА</b>

<b>{d['first_name']}</b> | {d['title']}
⭐ Ур.{d['level']} | 📊 {d['pvp_rating']}
💰 {d['money']}💰

🏆 Побед: {d['wins']} | 💀 Поражений: {d['losses']}
📈 Винрейт: {wr:.1f}%
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_hero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "hero_achievements":
        ach_list = [
            ("first_blood", "🩸 Первая кровь", "1 победа", player.data["wins"] >= 1),
            ("warrior", "⚔ Воин", "10 побед", player.data["wins"] >= 10),
            ("legend", "👑 Легенда", "100 побед", player.data["wins"] >= 100),
            ("rich", "💰 Богач", "10000 монет", player.data["money"] >= 10000)
        ]
        
        text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(player.data['achievements'])}/4)\n\n"
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
        
        player.data["hp"] = min(player.data["max_hp"], player.data["hp"] + potion["heal"])
        player.data["inventory"].remove(pk)
        player.save()
        
        bot.edit_message_text(f"💊 <b>{potion['name']}</b>\n❤ HP: {player.data['hp']}/{player.data['max_hp']}", call.message.chat.id, call.message.message_id)
    
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

# ==================== ТОРГОВЛЯ ====================
@bot.callback_query_handler(func=lambda call: call.data in ["trade_limited", "trade_daily", "trade_market", "trade_my_lots", "back_to_trade"])
def trade_handlers(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if call.data == "trade_limited":
        if not limited_items:
            bot.edit_message_text("💎 Нет лимитированных", call.message.chat.id, call.message.message_id)
            return
        
        text = "<b>💎 ЛИМИТИРОВАННЫЕ</b>\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for ik, item in limited_items.items():
            if item.get("remaining", 0) > 0:
                text += f"<b>{item['name']}</b> — 💰 {item['price']}\n\n"
                markup.add(types.InlineKeyboardButton(f"Купить - {item['price']}💰", callback_data=f"buyitem_{ik}"))
        
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "trade_daily":
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
    
    elif call.data == "trade_market":
        if not market_listings:
            bot.edit_message_text("📦 Рынок пуст", call.message.chat.id, call.message.message_id)
            return
        
        text = "<b>💱 РЫНОК</b>\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for lid, listing in list(market_listings.items())[:10]:
            item = items.get(listing["item_key"]) or limited_items.get(listing["item_key"])
            if item:
                text += f"📦 {item['name']} — <b>{listing['price']}💰</b>\n\n"
                markup.add(types.InlineKeyboardButton(f"Купить: {item['name']}", callback_data=f"mktbuy_{lid}"))
        
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_trade"))
        bot.edit_message_text(text[:4000], call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "trade_my_lots":
        uid = str(user_id)
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
                markup.add(types.InlineKeyboardButton(f"Снять: {item['name']}", callback_data=f"remlot_{lid}"))
        
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("remlot_"))
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

# ==================== МИР ====================
@bot.callback_query_handler(func=lambda call: call.data == "world_dungeons")
def world_dungeons(call):
    text = """
<b>🏰 ПОДЗЕМЕЛЬЯ</b>

🐺 Логово волка (Ур. 1+) — 3 босса
🕷 Паучьи пещеры (Ур. 5+) — 3 босса
💀 Катакомбы (Ур. 10+) — 4 босса
🐉 Драконье логово (Ур. 15+) — 4 босса
👹 Бездна (Ур. 25+) — 5 боссов

В каждом данже несколько боссов подряд!
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, name in enumerate(["🐺 Логово волка", "🕷 Паучьи пещеры", "💀 Катакомбы", "🐉 Драконье логово", "👹 Бездна"], 1):
        markup.add(types.InlineKeyboardButton(name, callback_data=f"dung_{i}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "world_clans")
def world_clans(call):
    text = "<b>🛡 КЛАНЫ</b>\n/createclan [имя] — создать\n/joinclan [имя] — вступить"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📋 Список", callback_data="clan_list"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "world_tournaments")
def world_tournaments(call):
    text = """
<b>🏟 ТУРНИРЫ</b>

Турниры проходят по олимпийской системе!
Игроки сражаются 1 на 1, победитель проходит дальше.

Призовой фонд растёт с каждым участником!
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🏆 Участвовать (500💰)", callback_data="tour_join"),
        types.InlineKeyboardButton("📋 Участники", callback_data="tour_list"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world")
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "world_events")
def world_events(call):
    # Генерация ивента
    current_event = events.get("current", {})
    if not current_event or datetime.fromisoformat(current_event.get("expires", "2000-01-01")) < datetime.now():
        new_event = {
            "name": random.choice(["🌋 Извержение вулкана", "❄ Ледяной шторм", "⚡ Грозовой фронт", "🌑 Затмение"]),
            "description": "Участвуйте в дуэлях для получения зачарований!",
            "ench_reward": random.choice(ENCHANT_EFFECTS),
            "ench_chance": random.randint(15, 35),
            "expires": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        events["current"] = new_event
        save_json(DATA_FILES['events'], events)
    
    ev = events["current"]
    time_left = datetime.fromisoformat(ev["expires"]) - datetime.now()
    minutes_left = max(0, time_left.seconds // 60)
    
    text = f"""
<b>🌍 ГЛОБАЛЬНЫЙ ИВЕНТ</b>

<b>{ev['name']}</b>
📝 {ev['description']}
✨ Награда: <b>{ev['ench_reward']['name']}</b> (шанс {ev['ench_chance']}%)
⏰ Обновление через: {minutes_left} мин.
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

@bot.callback_query_handler(func=lambda call: call.data == "world_help")
def world_help(call):
    text = """
<b>ℹ ПОМОЩЬ</b>

<b>Дуэли:</b> /duel, /ranked, /sparring
<b>Магазин:</b> /shop
<b>Продать:</b> /sell [номер] [цена]
<b>Клан:</b> /createclan, /joinclan

<b>Бой:</b>
🛡 Защита → ⚔ Атака (по очереди)
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_world"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_world")
def back_to_world(call):
    world_section(call.message)

# ==================== ТУРНИРЫ ====================
@bot.callback_query_handler(func=lambda call: call.data == "tour_join")
def tour_join(call):
    user_id = call.from_user.id
    player = Player(user_id)
    
    if player.data["money"] < 500:
        bot.answer_callback_query(call.id, "❌ 500💰!")
        return
    
    # Находим активный турнир
    tour_key = None
    for key, tour in active_tournaments.items():
        if tour.get("status") == "registration" and len(tour.get("participants", [])) < 16:
            tour_key = key
            break
    
    if not tour_key:
        tour_key = str(uuid.uuid4())[:8]
        active_tournaments[tour_key] = {
            "name": f"Турнир #{tour_key}",
            "participants": [],
            "prize_pool": 0,
            "status": "registration",
            "rounds": [],
            "created_at": datetime.now().isoformat()
        }
    
    tour = active_tournaments[tour_key]
    
    if str(user_id) in tour["participants"]:
        bot.answer_callback_query(call.id, "❌ Уже участвуете!")
        return
    
    player.data["money"] -= 500
    player.save()
    
    tour["participants"].append(str(user_id))
    tour["prize_pool"] += 500
    
    if len(tour["participants"]) >= 4:
        tour["status"] = "in_progress"
        # Создаём раунды
        participants = tour["participants"][:]
        random.shuffle(participants)
        tour["rounds"] = []
        while len(participants) >= 2:
            p1 = participants.pop(0)
            p2 = participants.pop(0)
            tour["rounds"].append({"p1": p1, "p2": p2, "winner": None})
    
    save_json(DATA_FILES['active_tournaments'], active_tournaments)
    bot.answer_callback_query(call.id, "✅ Зарегистрированы!")

@bot.callback_query_handler(func=lambda call: call.data == "tour_list")
def tour_list(call):
    if not active_tournaments:
        bot.answer_callback_query(call.id, "📋 Нет турниров")
        return
    
    text = "<b>📋 ТУРНИРЫ</b>\n\n"
    for key, tour in list(active_tournaments.items())[:5]:
        text += f"🏟 {tour['name']}: {len(tour.get('participants', []))} уч. | Приз: {tour.get('prize_pool', 0)}💰\n"
    
    bot.send_message(call.message.chat.id, text)

# ==================== ТОП ====================
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

# ==================== КЛАНЫ ====================
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

# ==================== ДАНЖИ ====================
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
    
    boss_count = [3, 3, 4, 4, 5][dl - 1]
    boss_names_pool = {
        1: ["🐺 Волк", "🐺 Альфа-волк", "🐺 Вожак"],
        2: ["🕷 Паук", "🕷 Ядовитый паук", "🕷 Королева"],
        3: ["💀 Скелет", "💀 Рыцарь смерти", "💀 Некромант", "💀 Лич"],
        4: ["🐉 Драконид", "🐉 Молодой дракон", "🐉 Дракон", "🐉 Древний дракон"],
        5: ["👹 Бес", "👹 Демон", "👹 Архидемон", "👹 Князь тьмы", "👹 Владыка"]
    }
    
    bosses = boss_names_pool[dl]
    total_reward = 0
    total_exp = 0
    
    # Симуляция боёв с боссами
    for i, boss_name in enumerate(bosses):
        boss_hp = 50 * dl * (i + 1)
        player_dmg = random.randint(10, 30) * dl
        turns = 0
        
        while boss_hp > 0 and turns < 20:
            boss_hp -= player_dmg
            turns += 1
        
        if boss_hp <= 0:
            reward = random.randint(30, 100) * dl * (i + 1)
            exp = random.randint(20, 80) * dl * (i + 1)
            total_reward += reward
            total_exp += exp
    
    player.data["money"] += total_reward
    player.data["exp"] += total_exp
    player.data["total_exp"] += total_exp
    player.data["last_dungeon"] = datetime.now().isoformat()
    player.data["dungeons_completed"] = player.data.get("dungeons_completed", 0) + 1
    
    # Шанс на предмет
    got_item = None
    if random.random() < 0.2:
        possible = [k for k, v in items.items() if v.get("level_req", 1) <= player.data["level"]]
        if possible:
            got_item = random.choice(possible)
            player.data["inventory"].append(got_item)
            player.data["items_found"] += 1
    
    check_level_up(player)
    player.save()
    
    result = f"""
<b>🏰 ДАНЖ ПРОЙДЕН!</b>

Боссы повержены: {len(bosses)}/{len(bosses)}
💰 +{total_reward} | ✨ +{total_exp}
"""
    if got_item:
        result += f"\n🎁 <b>{items[got_item]['name']}</b>!"
    
    bot.edit_message_text(result, call.message.chat.id, call.message.message_id)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================
def check_level_up(player):
    level = player.data["level"]
    exp_needed = int(100 * (1.5 ** (level - 1)))
    
    leveled = False
    while player.data["exp"] >= exp_needed:
        player.data["exp"] -= exp_needed
        player.data["level"] += 1
        player.data["max_hp"] += 20
        player.data["max_mana"] += 10
        player.data["hp"] = player.data["max_hp"]
        player.data["mana"] = player.data["max_mana"]
        
        titles = {5: "Боец", 10: "Воитель", 15: "Рыцарь", 20: "Ветеран",
                  30: "Мастер", 40: "Герой", 50: "Легенда", 75: "Полубог", 100: "Божество"}
        
        for req, title in titles.items():
            if player.data["level"] >= req and title not in player.data["titles_collected"]:
                player.data["titles_collected"].append(title)
                player.data["title"] = title
        
        level = player.data["level"]
        exp_needed = int(100 * (1.5 ** (level - 1)))
        leveled = True
    
    return leveled

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
            "item_key": ik, "price": price, "created_at": datetime.now().isoformat()
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
        types.InlineKeyboardButton("🔄 Сброс дня", callback_data="admin_reset"),
        types.InlineKeyboardButton("👁 Инфо игрока", callback_data="admin_info"),
        types.InlineKeyboardButton("✅ Разбан", callback_data="admin_unban"),
        types.InlineKeyboardButton("🏟 Создать турнир", callback_data="admin_create_tour"),
        types.InlineKeyboardButton("💎 Добавить лимитку", callback_data="admin_add_limited")
    )
    
    bot.send_message(message.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>\n\nВсе команды через @username", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_handlers(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Нет доступа!")
        return
    
    if call.data == "admin_stats":
        total = len(users)
        total_money = sum(u.get("money", 0) for u in users.values())
        total_duels = sum(u.get("total_duels", 0) for u in users.values())
        
        text = f"""
<b>📊 СТАТИСТИКА БОТА</b>

👥 Игроков: {total}
💰 Монет: {total_money}
⚔ Дуэлей: {total_duels}
🛡 Кланов: {len(clans)}
📦 Лотов: {len(market_listings)}
⛔ Банов: {len(banned_users)}
🏟 Турниров: {len(active_tournaments)}
"""
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    
    elif call.data == "admin_givemoney":
        bot.send_message(call.message.chat.id, "💰 Используйте: <code>/givemoney @username сумма</code>")
    
    elif call.data == "admin_giveitem":
        bot.send_message(call.message.chat.id, "🎁 Используйте: <code>/giveitem @username item_key</code>")
    
    elif call.data == "admin_banuser":
        bot.send_message(call.message.chat.id, "⛔ Используйте: <code>/ban @username причина</code>")
    
    elif call.data == "admin_broadcast":
        bot.send_message(call.message.chat.id, "📢 Используйте: <code>/broadcast текст</code>")
    
    elif call.data == "admin_reset":
        bot.send_message(call.message.chat.id, "🔄 Используйте: <code>/resetdaily @username</code>")
    
    elif call.data == "admin_info":
        bot.send_message(call.message.chat.id, "👁 Используйте: <code>/userinfo @username</code>")
    
    elif call.data == "admin_unban":
        bot.send_message(call.message.chat.id, "✅ Используйте: <code>/unban @username</code>")
    
    elif call.data == "admin_create_tour":
        tour_id = str(uuid.uuid4())[:8]
        active_tournaments[tour_id] = {
            "name": f"Турнир #{tour_id}",
            "participants": [],
            "prize_pool": 10000,
            "status": "registration",
            "rounds": [],
            "created_at": datetime.now().isoformat()
        }
        save_json(DATA_FILES['active_tournaments'], active_tournaments)
        bot.send_message(call.message.chat.id, f"✅ Турнир создан! ID: <code>{tour_id}</code>\nПризовой фонд: 10000💰")
    
    elif call.data == "admin_add_limited":
        bot.send_message(call.message.chat.id, "💎 Используйте: <code>/addlimited name total price type damage_min damage_max</code>")

@bot.message_handler(commands=['givemoney', 'giveitem', 'ban', 'unban', 'broadcast', 'resetdaily', 'userinfo', 'addlimited'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Нет доступа!")
        return
    
    cmd = message.text.split()[0].replace('/', '')
    parts = message.text.split()
    
    def find_user_by_username(username):
        username = username.replace('@', '').lower()
        for uid, data in users.items():
            if data.get("username", "").lower() == username:
                return uid
        return None
    
    try:
        if cmd == "givemoney":
            username = parts[1]
            amount = int(parts[2])
            uid = find_user_by_username(username)
            if uid:
                p = Player(uid)
                p.data["money"] += amount
                p.save()
                bot.send_message(message.chat.id, f"✅ Выдано {amount}💰 игроку @{username}")
            else:
                bot.send_message(message.chat.id, f"❌ Игрок @{username} не найден")
        
        elif cmd == "giveitem":
            username = parts[1]
            ik = parts[2]
            uid = find_user_by_username(username)
            if uid:
                p = Player(uid)
                p.data["inventory"].append(ik)
                p.save()
                bot.send_message(message.chat.id, f"✅ Предмет {ik} выдан @{username}")
            else:
                bot.send_message(message.chat.id, f"❌ Игрок @{username} не найден")
        
        elif cmd == "ban":
            username = parts[1]
            reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение правил"
            uid = find_user_by_username(username)
            if uid:
                banned_users[uid] = {"reason": reason, "banned_at": datetime.now().isoformat(), "banned_by": message.from_user.username}
                save_json(DATA_FILES['bans'], banned_users)
                bot.send_message(message.chat.id, f"⛔ @{username} забанен!\nПричина: {reason}")
            else:
                bot.send_message(message.chat.id, f"❌ Игрок @{username} не найден")
        
        elif cmd == "unban":
            username = parts[1]
            uid = find_user_by_username(username)
            if uid and uid in banned_users:
                del banned_users[uid]
                save_json(DATA_FILES['bans'], banned_users)
                bot.send_message(message.chat.id, f"✅ @{username} разбанен!")
            else:
                bot.send_message(message.chat.id, f"❌ Игрок не в бане или не найден")
        
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
                bot.send_message(message.chat.id, f"✅ Отправлено: {s}\n❌ Ошибок: {f}")
        
        elif cmd == "resetdaily":
            username = parts[1]
            uid = find_user_by_username(username)
            if uid:
                p = Player(uid)
                p.data["last_daily"] = None
                p.data["last_dungeon"] = None
                p.save()
                bot.send_message(message.chat.id, f"✅ Сброс для @{username} выполнен")
            else:
                bot.send_message(message.chat.id, f"❌ Игрок не найден")
        
        elif cmd == "userinfo":
            username = parts[1]
            uid = find_user_by_username(username)
            if uid:
                p = Player(uid)
                d = p.data
                text = f"""
<b>👤 ИНФОРМАЦИЯ ОБ ИГРОКЕ</b>

ID: <code>{uid}</code>
Username: @{d.get('username', 'Нет')}
Имя: {d.get('first_name', 'Нет')}
Уровень: {d.get('level', 1)}
💰 Баланс: {d.get('money', 0)}
🏆 Побед: {d.get('wins', 0)} | 💀 Поражений: {d.get('losses', 0)}
📊 Рейтинг: {d.get('pvp_rating', 1000)}
🛡 Клан: {d.get('clan', 'Нет')}
📦 Предметов: {len(d.get('inventory', []))}
📅 Регистрация: {d.get('registration_date', '')[:10]}
"""
                bot.send_message(message.chat.id, text)
            else:
                bot.send_message(message.chat.id, f"❌ Игрок @{username} не найден")
        
        elif cmd == "addlimited":
            name = parts[1]
            total = int(parts[2])
            price = int(parts[3])
            item_type = parts[4]
            dmg_min = int(parts[5])
            dmg_max = int(parts[6])
            
            key = f"limited_{int(time.time())}"
            limited_items[key] = {
                "name": name, "total": total, "remaining": total,
                "price": price, "type": item_type,
                "damage": (dmg_min, dmg_max),
                "rarity": "divine"
            }
            save_json(DATA_FILES['limited'], limited_items)
            bot.send_message(message.chat.id, f"✅ Лимитированный предмет '{name}' добавлен!")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}\nПроверьте формат команды.")

# ==================== ЗАПУСК ====================
def main():
    print("=" * 60)
    print("⚔️ ДУЭЛЬ БОТ v11.0 FINAL ⚔️")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👥 Игроков: {len(users)}")
    print("=" * 60)
    print("✅ Поочерёдные атаки (защита → атака)")
    print("✅ Защита уменьшает урон от экипировки")
    print("✅ Навыки с кулдаунами (чем сильнее - тем дольше CD)")
    print("✅ Таймер на ход (60 сек)")
    print("✅ 6 видов дуэлей")
    print("✅ Данжи с несколькими боссами")
    print("✅ Турниры с раундами")
    print("✅ Ивенты с реальными наградами")
    print("✅ Админ через @username")
    print("✅ Кнопки Назад закрывают меню")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
