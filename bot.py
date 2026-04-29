import telebot
from telebot import types
import json
import random
import time
import threading
from datetime import datetime, timedelta
import re
import math

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = '8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE'
ADMIN_ID = 5356400377
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ==================== ФАЙЛЫ ДАННЫХ ====================
USERS_FILE = 'users.json'
ITEMS_FILE = 'items.json'
DUELS_FILE = 'active_duels.json'
LIMITED_FILE = 'limited_items.json'
CLANS_FILE = 'clans.json'
TOURNAMENTS_FILE = 'tournaments.json'
ACHIEVEMENTS_FILE = 'achievements.json'
QUESTS_FILE = 'quests.json'
MARKET_FILE = 'market.json'

# ==================== ЗАГРУЗКА/СОХРАНЕНИЕ ====================
def load_json(filename, default=None):
    if default is None:
        default = {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        save_json(filename, default)
        return default
    except json.JSONDecodeError:
        save_json(filename, default)
        return default

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==================== ИНИЦИАЛИЗАЦИЯ ДАННЫХ ====================
# Предметы
DEFAULT_ITEMS = {
    "wooden_sword": {
        "name": "🗡 Деревянный меч", "damage": 5, "price": 100,
        "type": "weapon", "rarity": "common", "level_req": 1,
        "description": "Простой меч для начинающих воинов"
    },
    "stone_sword": {
        "name": "🗿 Каменный меч", "damage": 8, "price": 200,
        "type": "weapon", "rarity": "common", "level_req": 2,
        "description": "Более прочный меч из камня"
    },
    "iron_sword": {
        "name": "⚔ Железный меч", "damage": 12, "price": 500,
        "type": "weapon", "rarity": "uncommon", "level_req": 5,
        "description": "Надёжный железный меч"
    },
    "steel_sword": {
        "name": "🔪 Стальной меч", "damage": 18, "price": 1000,
        "type": "weapon", "rarity": "uncommon", "level_req": 10,
        "description": "Острый стальной клинок"
    },
    "mythril_sword": {
        "name": "✨ Мифриловый меч", "damage": 25, "price": 2500,
        "type": "weapon", "rarity": "rare", "level_req": 15,
        "description": "Лёгкий и прочный мифриловый меч"
    },
    "dragon_sword": {
        "name": "🐉 Драконий меч", "damage": 35, "price": 5000,
        "type": "weapon", "rarity": "epic", "level_req": 20,
        "description": "Меч, выкованный из клыка дракона"
    },
    "excalibur": {
        "name": "⚡ Экскалибур", "damage": 50, "price": 10000,
        "type": "weapon", "rarity": "legendary", "level_req": 30,
        "description": "Легендарный меч короля Артура"
    },
    "chaos_blade": {
        "name": "🌑 Клинок Хаоса", "damage": 75, "price": 25000,
        "type": "weapon", "rarity": "mythic", "level_req": 40,
        "description": "Клинок из самого сердца хаоса"
    },
    "wooden_shield": {
        "name": "🛡 Деревянный щит", "defense": 5, "price": 150,
        "type": "shield", "rarity": "common", "level_req": 1,
        "description": "Простой деревянный щит"
    },
    "iron_shield": {
        "name": "🛡 Железный щит", "defense": 12, "price": 600,
        "type": "shield", "rarity": "uncommon", "level_req": 5,
        "description": "Надёжный железный щит"
    },
    "dragon_shield": {
        "name": "🐉 Щит Дракона", "defense": 25, "price": 4000,
        "type": "shield", "rarity": "epic", "level_req": 20,
        "description": "Щит из драконьей чешуи"
    },
    "aegis": {
        "name": "💫 Эгида", "defense": 40, "price": 15000,
        "type": "shield", "rarity": "legendary", "level_req": 35,
        "description": "Божественный щит Зевса"
    },
    "leather_armor": {
        "name": "🧥 Кожаная броня", "defense": 3, "hp_bonus": 10,
        "price": 120, "type": "armor", "rarity": "common", "level_req": 1,
        "description": "Лёгкая кожаная броня"
    },
    "iron_armor": {
        "name": "🛡 Железная броня", "defense": 8, "hp_bonus": 25,
        "price": 800, "type": "armor", "rarity": "uncommon", "level_req": 8,
        "description": "Прочная железная броня"
    },
    "dragon_armor": {
        "name": "🐉 Драконья броня", "defense": 20, "hp_bonus": 60,
        "price": 6000, "type": "armor", "rarity": "epic", "level_req": 25,
        "description": "Великая броня из драконьей шкуры"
    },
    "health_potion": {
        "name": "🧪 Зелье здоровья", "heal": 25, "price": 50,
        "type": "potion", "rarity": "common", "level_req": 1,
        "description": "Восстанавливает 25 HP"
    },
    "big_health_potion": {
        "name": "🧪 Большое зелье здоровья", "heal": 60, "price": 150,
        "type": "potion", "rarity": "uncommon", "level_req": 5,
        "description": "Восстанавливает 60 HP"
    },
    "elixir": {
        "name": "💊 Эликсир жизни", "heal": 150, "price": 500,
        "type": "potion", "rarity": "rare", "level_req": 15,
        "description": "Полностью восстанавливает здоровье"
    },
    "strength_amulet": {
        "name": "📿 Амулет Силы", "damage_bonus": 15, "price": 3000,
        "type": "accessory", "rarity": "epic", "level_req": 20,
        "description": "Увеличивает урон на 15"
    },
    "lucky_charm": {
        "name": "🍀 Талисман Удачи", "crit_chance": 15, "price": 2500,
        "type": "accessory", "rarity": "rare", "level_req": 18,
        "description": "+15% к шансу критического удара"
    },
    "speed_boots": {
        "name": "👢 Сапоги Скорости", "speed_bonus": 10, "price": 2000,
        "type": "boots", "rarity": "uncommon", "level_req": 12,
        "description": "Увеличивает шанс первого удара"
    }
}

# Лимитированные предметы
DEFAULT_LIMITED = {
    "thunderfury": {
        "name": "⚡ Гроза Богов", "damage": 100, "total": 3,
        "remaining": 3, "price": 50000, "type": "weapon",
        "rarity": "divine", "special": "chain_lightning",
        "description": "Оружие самого Зевса! Молниеносные атаки"
    },
    "world_ender": {
        "name": "🌋 Конец Света", "damage": 150, "total": 1,
        "remaining": 1, "price": 100000, "type": "weapon",
        "rarity": "apocalyptic", "special": "armageddon",
        "description": "Единственный в своём роде! Уничтожает всё"
    },
    "phoenix_armor": {
        "name": "🦅 Броня Феникса", "defense": 80, "hp_bonus": 200,
        "total": 5, "remaining": 5, "price": 75000, "type": "armor",
        "rarity": "divine", "special": "rebirth",
        "description": "Возрождает владельца после смерти"
    },
    "invisibility_cloak": {
        "name": "👻 Плащ-невидимка", "defense": 30, "total": 7,
        "remaining": 7, "price": 45000, "type": "armor",
        "rarity": "mythic", "special": "invisibility",
        "description": "Шанс избежать атаки противника"
    }
}

# Достижения
ACHIEVEMENTS = {
    "first_blood": {"name": "🩸 Первая кровь", "description": "Выиграйте первую дуэль", "reward": 200},
    "warrior": {"name": "⚔ Воин", "description": "Выиграйте 10 дуэлей", "reward": 500},
    "veteran": {"name": "🎖 Ветеран", "description": "Выиграйте 50 дуэлей", "reward": 2000},
    "legend": {"name": "👑 Легенда", "description": "Выиграйте 100 дуэлей", "reward": 5000},
    "rich": {"name": "💰 Богач", "description": "Накопите 10000 монет", "reward": 1000},
    "millionaire": {"name": "💎 Миллионер", "description": "Накопите 100000 монет", "reward": 10000},
    "collector": {"name": "🎒 Коллекционер", "description": "Соберите 20 предметов", "reward": 1500},
    "dragon_slayer": {"name": "🐉 Убийца Драконов", "description": "Победите дракона", "reward": 3000},
    "survivor": {"name": "💪 Выживший", "description": "Выиграйте с HP < 10", "reward": 800},
    "perfect": {"name": "✨ Идеальная победа", "description": "Победите без потерь HP", "reward": 1000}
}

# Квесты
DAILY_QUESTS = [
    {"name": "Ежедневная дуэль", "description": "Проведите 3 дуэли", "target": 3,
     "type": "duels", "reward_money": 300, "reward_exp": 50},
    {"name": "Покупки", "description": "Купите 2 предмета", "target": 2,
     "type": "purchases", "reward_money": 250, "reward_exp": 40},
    {"name": "Тренировка", "description": "Потренируйтесь 5 раз", "target": 5,
     "type": "train", "reward_money": 200, "reward_exp": 60},
    {"name": "Исследователь", "description": "Исследуйте 3 раза", "target": 3,
     "type": "explore", "reward_money": 350, "reward_exp": 45},
    {"name": "Победитель", "description": "Выиграйте 2 дуэли", "target": 2,
     "type": "wins", "reward_money": 400, "reward_exp": 70}
]

# Загрузка данных
items = load_json(ITEMS_FILE, DEFAULT_ITEMS)
limited_items = load_json(LIMITED_FILE, DEFAULT_LIMITED)
users = load_json(USERS_FILE, {})
active_duels = load_json(DUELS_FILE, {})
clans = load_json(CLANS_FILE, {})
tournaments = load_json(TOURNAMENTS_FILE, {})
achievements_data = load_json(ACHIEVEMENTS_FILE, {})
quests_data = load_json(QUESTS_FILE, {})
market_listings = load_json(MARKET_FILE, {})

# ==================== ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ ====================
class User:
    def __init__(self, user_id, username="Неизвестный", first_name="Игрок"):
        user_id = str(user_id)
        if user_id not in users:
            users[user_id] = {
                "username": username,
                "first_name": first_name,
                "money": 500,
                "level": 1,
                "exp": 0,
                "hp": 100,
                "max_hp": 100,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "win_streak": 0,
                "best_streak": 0,
                "inventory": [],
                "equipped_weapon": None,
                "equipped_shield": None,
                "equipped_armor": None,
                "equipped_accessory": None,
                "equipped_boots": None,
                "last_daily": None,
                "last_work": None,
                "last_duel": None,
                "title": "Новичок",
                "titles_collected": ["Новичок"],
                "achievements": [],
                "active_quests": {},
                "completed_quests": 0,
                "clan": None,
                "tournament_wins": 0,
                "total_damage_dealt": 0,
                "total_damage_taken": 0,
                "critical_hits": 0,
                "items_used": 0,
                "registration_date": datetime.now().isoformat(),
                "settings": {
                    "notifications": True,
                    "duel_requests": True,
                    "show_effects": True
                }
            }
            save_json(USERS_FILE, users)
    
    @property
    def data(self):
        return users[str(self.user_id)]
    
    def save(self):
        save_json(USERS_FILE, users)

class Duel:
    def __init__(self, player1_id, player2_id, duel_type="normal", bet=0):
        self.id = f"{int(time.time())}_{random.randint(1000,9999)}"
        self.player1_id = str(player1_id)
        self.player2_id = str(player2_id)
        self.duel_type = duel_type
        self.bet = bet
        self.turn = random.choice([1, 2])
        self.status = "waiting"  # waiting, active, finished
        self.p1_hp = 100
        self.p2_hp = 100
        self.p1_max_hp = 100
        self.p2_max_hp = 100
        self.effects_p1 = []
        self.effects_p2 = []
        self.turn_count = 0
        self.max_turns = 20
        self.log = []
        self.created_at = datetime.now().isoformat()
        
        active_duels[self.id] = self.to_dict()
        save_json(DUELS_FILE, active_duels)
    
    def to_dict(self):
        return {
            "id": self.id,
            "player1_id": self.player1_id,
            "player2_id": self.player2_id,
            "duel_type": self.duel_type,
            "bet": self.bet,
            "turn": self.turn,
            "status": self.status,
            "p1_hp": self.p1_hp,
            "p2_hp": self.p2_hp,
            "p1_max_hp": self.p1_max_hp,
            "p2_max_hp": self.p2_max_hp,
            "effects_p1": self.effects_p1,
            "effects_p2": self.effects_p2,
            "turn_count": self.turn_count,
            "max_turns": self.max_turns,
            "log": self.log,
            "created_at": self.created_at
        }
    
    def save(self):
        active_duels[self.id] = self.to_dict()
        save_json(DUELS_FILE, active_duels)

# ==================== СИСТЕМА УРОВНЕЙ ====================
def get_exp_for_level(level):
    """Экспоненциальная система опыта"""
    return int(100 * (1.5 ** (level - 1)))

def check_level_up(user_id):
    user = User(user_id)
    level = user.data["level"]
    exp_needed = get_exp_for_level(level)
    
    while user.data["exp"] >= exp_needed:
        user.data["exp"] -= exp_needed
        user.data["level"] += 1
        user.data["max_hp"] = 100 + (user.data["level"] - 1) * 10
        user.data["hp"] = user.data["max_hp"]
        
        # Титулы по уровням
        titles = [
            (1, "Новичок"), (5, "Боец"), (10, "Воитель"),
            (15, "Рыцарь"), (20, "Ветеран"), (25, "Мастер"),
            (30, "Грандмастер"), (40, "Герой"), (50, "Легенда"),
            (60, "Мифический воин"), (75, "Полубог"), (100, "Божество")
        ]
        
        for req_level, title in titles:
            if user.data["level"] >= req_level and title not in user.data["titles_collected"]:
                user.data["titles_collected"].append(title)
                user.data["title"] = title
        
        level = user.data["level"]
        exp_needed = get_exp_for_level(level)
    
    user.save()
    return user.data["level"]

# ==================== РАСЧЁТ ХАРАКТЕРИСТИК ====================
def calculate_stats(user_id):
    """Расчёт полных характеристик персонажа"""
    user = User(user_id)
    stats = {
        "base_damage": user.data["level"] * 2,
        "bonus_damage": 0,
        "defense": 0,
        "hp": user.data["hp"],
        "max_hp": user.data["max_hp"],
        "crit_chance": 5,  # базовый шанс крита 5%
        "crit_multiplier": 1.5,
        "speed": 0,
        "dodge_chance": 3,  # базовый шанс уклонения 3%
        "lifesteal": 0,
        "damage_reflect": 0
    }
    
    # Оружие
    if user.data["equipped_weapon"]:
        weapon = items.get(user.data["equipped_weapon"]) or limited_items.get(user.data["equipped_weapon"])
        if weapon:
            if "damage" in weapon:
                stats["bonus_damage"] += weapon["damage"]
            if "crit_chance" in weapon:
                stats["crit_chance"] += weapon["crit_chance"]
            if "lifesteal" in weapon:
                stats["lifesteal"] += weapon["lifesteal"]
    
    # Щит
    if user.data["equipped_shield"]:
        shield = items.get(user.data["equipped_shield"]) or limited_items.get(user.data["equipped_shield"])
        if shield:
            if "defense" in shield:
                stats["defense"] += shield["defense"]
            if "damage_reflect" in shield:
                stats["damage_reflect"] += shield["damage_reflect"]
    
    # Броня
    if user.data["equipped_armor"]:
        armor = items.get(user.data["equipped_armor"]) or limited_items.get(user.data["equipped_armor"])
        if armor:
            if "defense" in armor:
                stats["defense"] += armor["defense"]
            if "hp_bonus" in armor:
                stats["max_hp"] += armor["hp_bonus"]
            if "dodge_chance" in armor:
                stats["dodge_chance"] += armor["dodge_chance"]
    
    # Аксессуар
    if user.data["equipped_accessory"]:
        acc = items.get(user.data["equipped_accessory"]) or limited_items.get(user.data["equipped_accessory"])
        if acc:
            if "damage_bonus" in acc:
                stats["bonus_damage"] += acc["damage_bonus"]
            if "crit_chance" in acc:
                stats["crit_chance"] += acc["crit_chance"]
    
    # Обувь
    if user.data["equipped_boots"]:
        boots = items.get(user.data["equipped_boots"]) or limited_items.get(user.data["equipped_boots"])
        if boots:
            if "speed_bonus" in boots:
                stats["speed"] += boots["speed_bonus"]
    
    # Лимиты
    stats["crit_chance"] = min(stats["crit_chance"], 80)
    stats["dodge_chance"] = min(stats["dodge_chance"], 50)
    
    return stats

# ==================== КОМПАКТНОЕ МЕНЮ ====================
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [
        "⚔Дуэль", "👤Профиль", "🎒",
        "🏪Магазин", "💎Редкое", "⚙",
        "🎮РП", "💰Работа", "🎁",
        "📊Топ", "🏆Турнир", "🛡Клан",
        "📜Квесты", "🏅Ачивки", "💊Хил",
        "🗡Атака", "🛡Защита", "✨Скилл"
    ]
    markup.add(*[types.KeyboardButton(b) for b in buttons])
    return markup

# ==================== КОМАНДЫ БОТА ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    first_name = message.from_user.first_name or "Игрок"
    
    user = User(user_id, username, first_name)
    
    welcome_text = f"""
<b>⚔ ДУЭЛЬ БОТ v3.0 ⚔</b>

Привет, <b>{first_name}</b>!
Добро пожаловать в мир эпических сражений!

🎯 <b>Возможности:</b>
• Различные режимы дуэлей
• 20+ видов оружия и брони
• Лимитированные предметы
• Клановая система
• Турниры и квесты
• Система достижений

💰 Стартовый бонус: <b>500 монет</b>
🎁 Ежедневные награды
📈 Система уровней (100+)

Используй кнопки меню для навигации!
"""
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu())

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
<b>📚 СПРАВКА ПО БОТУ</b>

<b>⚔ Дуэли:</b>
/duel - дуэль с игроком (ответ на сообщение)
/quickduel - быстрая дуэль
/ranked - рейтинговая дуэль
/tournament - участие в турнире

<b>👤 Профиль:</b>
/profile - статистика
/inventory - инвентарь
/equip [id] - экипировать предмет
/stats - характеристики

<b>💰 Экономика:</b>
/shop - магазин
/buy [id] - купить предмет
/sell [id] - продать предмет
/market - рынок игроков
/daily - ежедневный бонус
/work - работа

<b>🎮 РП команды:</b>
/rp - список РП команд

<b>🛡 Клан:</b>
/clan create [name] - создать клан
/clan join [name] - вступить в клан
/clan info - информация о клане

<b>📜 Квесты:</b>
/quests - активные квесты

<b>🏆 Рейтинг:</b>
/top - топ игроков
"""
    bot.send_message(message.chat.id, help_text)

# ==================== ПРОФИЛЬ И ИНВЕНТАРЬ ====================
@bot.message_handler(func=lambda m: m.text == "👤Профиль")
@bot.message_handler(commands=['profile'])
def profile_handler(message):
    user_id = message.from_user.id
    user = User(user_id)
    stats = calculate_stats(user_id)
    u = user.data
    
    equipment = []
    if u["equipped_weapon"]:
        w = items.get(u["equipped_weapon"]) or limited_items.get(u["equipped_weapon"])
        equipment.append(f"⚔ {w['name']}" if w else "⚔ Нет")
    if u["equipped_shield"]:
        s = items.get(u["equipped_shield"]) or limited_items.get(u["equipped_shield"])
        equipment.append(f"🛡 {s['name']}" if s else "🛡 Нет")
    if u["equipped_armor"]:
        a = items.get(u["equipped_armor"]) or limited_items.get(u["equipped_armor"])
        equipment.append(f"🧥 {a['name']}" if a else "🧥 Нет")
    
    winrate = (u["wins"] / (u["wins"] + u["losses"]) * 100) if (u["wins"] + u["losses"]) > 0 else 0
    
    profile_text = f"""
<b>👤 ПРОФИЛЬ ИГРОКА</b>

<b>{u['first_name']}</b> | {u['title']}
🆔 ID: <code>{user_id}</code>
⭐ Уровень: <b>{u['level']}</b>
✨ Опыт: {u['exp']}/{get_exp_for_level(u['level'])}

❤ Здоровье: {u['hp']}/{u['max_hp']}
⚔ Урон: {stats['base_damage'] + stats['bonus_damage']}
🛡 Защита: {stats['defense']}
💥 Крит: {stats['crit_chance']}%

<b>Статистика дуэлей:</b>
🏆 Побед: {u['wins']}
💀 Поражений: {u['losses']}
🤝 Ничьих: {u['draws']}
📊 Винрейт: {winrate:.1f}%
🔥 Лучшая серия: {u['best_streak']}

💰 Баланс: <b>{u['money']} монет</b>
🎒 Предметов: {len(u['inventory'])}
🏅 Достижений: {len(u['achievements'])}/{len(ACHIEVEMENTS)}
🛡 Клан: {u.get('clan', 'Нет')}

<b>Экипировка:</b>
{chr(10).join(equipment) if equipment else 'Нет экипировки'}
"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="full_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory"),
        types.InlineKeyboardButton("🏅 Достижения", callback_data="achievements"),
        types.InlineKeyboardButton("⚙ Настройки", callback_data="settings")
    )
    
    bot.send_message(message.chat.id, profile_text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🎒")
@bot.message_handler(commands=['inventory'])
def inventory_handler(message):
    user_id = message.from_user.id
    user = User(user_id)
    
    if not user.data["inventory"]:
        bot.send_message(message.chat.id, "🎒 Ваш инвентарь пуст! Купите предметы в магазине.")
        return
    
    # Группировка предметов
    item_counts = {}
    for item_key in user.data["inventory"]:
        item_counts[item_key] = item_counts.get(item_key, 0) + 1
    
    inventory_text = "<b>🎒 ИНВЕНТАРЬ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for i, (item_key, count) in enumerate(item_counts.items(), 1):
        item = items.get(item_key) or limited_items.get(item_key)
        if item:
            rarity_star = {
                "common": "⬜", "uncommon": "🟩", "rare": "🟦",
                "epic": "🟪", "legendary": "🟧", "mythic": "🟥",
                "divine": "💛", "apocalyptic": "🖤"
            }.get(item.get("rarity", "common"), "⬜")
            
            inventory_text += f"{i}. {rarity_star} {item['name']} x{count}\n"
            
            if item["type"] in ["weapon", "shield", "armor", "accessory", "boots"]:
                markup.add(types.InlineKeyboardButton(
                    f"Экипировать: {item['name'][:20]}",
                    callback_data=f"equip_{item_key}"
                ))
            elif item["type"] == "potion":
                markup.add(types.InlineKeyboardButton(
                    f"Использовать: {item['name'][:20]}",
                    callback_data=f"use_{item_key}"
                ))
    
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="inventory"))
    
    if len(inventory_text) > 4000:
        # Разбиваем на части
        for x in range(0, len(inventory_text), 4000):
            bot.send_message(message.chat.id, inventory_text[x:x+4000], reply_markup=markup if x == 0 else None)
    else:
        bot.send_message(message.chat.id, inventory_text, reply_markup=markup)

# ==================== МАГАЗИН И ПРЕДМЕТЫ ====================
@bot.message_handler(func=lambda m: m.text == "🏪Магазин")
@bot.message_handler(commands=['shop'])
def shop_handler(message):
    shop_text = "<b>🏪 МАГАЗИН</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Категории
    categories = {
        "⚔ Оружие": "weapon",
        "🛡 Щиты": "shield",
        "🧥 Броня": "armor",
        "🧪 Зелья": "potion",
        "📿 Аксессуары": "accessory",
        "👢 Обувь": "boots"
    }
    
    for cat_name, cat_type in categories.items():
        shop_text += f"<b>{cat_name}:</b>\n"
        cat_items = {k: v for k, v in items.items() if v["type"] == cat_type}
        
        for item_key, item in sorted(cat_items.items(), key=lambda x: x[1].get("price", 0)):
            if item.get("level_req", 1) <= 100:  # Показываем все до 100 уровня
                shop_text += f"• {item['name']} - {item['price']}💰 | Ур.{item.get('level_req', 1)}\n"
        
        shop_text += "\n"
        markup.add(types.InlineKeyboardButton(f"Купить {cat_name}", callback_data=f"shopcat_{cat_type}"))
    
    markup.add(types.InlineKeyboardButton("💎 Лимитированные предметы", callback_data="limited_shop"))
    
    bot.send_message(message.chat.id, shop_text[:4000], reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "💎Редкое")
def limited_shop_handler(message):
    if not limited_items:
        bot.send_message(message.chat.id, "💎 Лимитированных предметов нет в наличии!")
        return
    
    limit_text = "<b>💎 ЛИМИТИРОВАННЫЕ ПРЕДМЕТЫ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, item in limited_items.items():
        if item["remaining"] > 0:
            progress = "█" * int(item["remaining"] / item["total"] * 10)
            empty = "░" * (10 - len(progress))
            
            limit_text += f"<b>{item['name']}</b>\n"
            limit_text += f"📦 [{progress}{empty}] {item['remaining']}/{item['total']}\n"
            limit_text += f"{item['description']}\n"
            
            if "damage" in item:
                limit_text += f"⚔ Урон: <b>{item['damage']}</b>\n"
            if "defense" in item:
                limit_text += f"🛡 Защита: <b>{item['defense']}</b>\n"
            if "hp_bonus" in item:
                limit_text += f"❤ Бонус HP: <b>{item['hp_bonus']}</b>\n"
            
            limit_text += f"💰 Цена: <b>{item['price']} монет</b>\n"
            
            if "special" in item:
                limit_text += f"✨ Особое свойство: <b>{item['special']}</b>\n"
            
            limit_text += "\n"
            
            markup.add(types.InlineKeyboardButton(
                f"Купить {item['name']} - {item['price']}💰",
                callback_data=f"buylimited_{item_key}"
            ))
    
    if not markup.keyboard:
        bot.send_message(message.chat.id, "💎 Все лимитированные предметы распроданы!")
        return
    
    bot.send_message(message.chat.id, limit_text[:4000], reply_markup=markup)

# ==================== СИСТЕМА ДУЭЛЕЙ ====================
@bot.message_handler(func=lambda m: m.text == "⚔Дуэль")
def duel_menu_handler(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль", callback_data="duel_quick"),
        types.InlineKeyboardButton("👤 Дуэль с игроком", callback_data="duel_player"),
        types.InlineKeyboardButton("🏆 Рейтинговая дуэль", callback_data="duel_ranked"),
        types.InlineKeyboardButton("💀 Хардкорная дуэль", callback_data="duel_hardcore"),
        types.InlineKeyboardButton("🎯 Дружеская дуэль", callback_data="duel_friendly"),
        types.InlineKeyboardButton("🔥 Дуэль на выживание", callback_data="duel_survival"),
        types.InlineKeyboardButton("⚔ Командная дуэль 2x2", callback_data="duel_team")
    )
    
    duel_text = """
<b>⚔ СИСТЕМА ДУЭЛЕЙ</b>

Выберите тип дуэли:

<b>⚡ Быстрая</b> - против бота, ставка 50💰
<b>👤 С игроком</b> - PvP дуэль
<b>🏆 Рейтинговая</b> - влияет на рейтинг, ставка 100💰
<b>💀 Хардкорная</b> - высокие ставки (500💰)
<b>🎯 Дружеская</b> - без ставок и потерь
<b>🔥 На выживание</b> - до 0 HP, приз 200💰
<b>⚔ Командная 2x2</b> - сражение команд
"""
    bot.send_message(message.chat.id, duel_text, reply_markup=markup)

def execute_duel(player1_id, player2_id, duel_type="normal", bet=0):
    """Исполнение дуэли между двумя игроками"""
    p1 = User(player1_id)
    p2 = User(player2_id)
    
    stats1 = calculate_stats(player1_id)
    stats2 = calculate_stats(player2_id)
    
    p1_hp = stats1["max_hp"]
    p2_hp = stats2["max_hp"]
    
    # Определение очерёдности
    if stats1["speed"] > stats2["speed"]:
        first, second = player1_id, player2_id
        first_hp, second_hp = p1_hp, p2_hp
        first_stats, second_stats = stats1, stats2
    elif stats2["speed"] > stats1["speed"]:
        first, second = player2_id, player1_id
        first_hp, second_hp = p2_hp, p1_hp
        first_stats, second_stats = stats2, stats1
    else:
        # Одинаковая скорость - случайный выбор
        if random.random() < 0.5:
            first, second = player1_id, player2_id
            first_hp, second_hp = p1_hp, p2_hp
            first_stats, second_stats = stats1, stats2
        else:
            first, second = player2_id, player1_id
            first_hp, second_hp = p2_hp, p1_hp
            first_stats, second_stats = stats2, stats1
    
    battle_log = []
    turns = 0
    max_turns = 30
    
    while turns < max_turns and first_hp > 0 and second_hp > 0:
        turns += 1
        # Ход первого игрока
        damage = first_stats["base_damage"] + first_stats["bonus_damage"] + random.randint(-5, 5)
        
        # Критический удар
        is_crit = random.random() * 100 < first_stats["crit_chance"]
        if is_crit:
            damage = int(damage * first_stats["crit_multiplier"])
            battle_log.append(f"💥 КРИТИЧЕСКИЙ УДАР!")
        
        # Проверка уклонения
        dodge_chance = second_stats["dodge_chance"]
        if random.random() * 100 < dodge_chance:
            battle_log.append(f"🌀 Уклонение! Урон не нанесён")
            damage = 0
        
        # Применение защиты
        damage = max(0, damage - second_stats["defense"])
        
        # Вампиризм
        if first_stats["lifesteal"] > 0:
            heal = int(damage * first_stats["lifesteal"] / 100)
            first_hp = min(first_stats["max_hp"], first_hp + heal)
            if heal > 0:
                battle_log.append(f"💚 Вампиризм +{heal} HP")
        
        # Отражение урона
        if second_stats["damage_reflect"] > 0:
            reflect = int(damage * second_stats["damage_reflect"] / 100)
            first_hp -= reflect
            if reflect > 0:
                battle_log.append(f"🔄 Отражение урона: -{reflect} HP атакующему")
        
        second_hp -= damage
        battle_log.append(f"⚔ Ход {turns}: Нанесено {damage} урона")
        
        if first_hp <= 0 or second_hp <= 0:
            break
        
        # Обмен ролями
        first, second = second, first
        first_hp, second_hp = second_hp, first_hp
        first_stats, second_stats = second_stats, first_stats
    
    # Определение победителя
    if first_hp <= 0 and second_hp <= 0:
        winner_id = None
        result = "draw"
    elif second_hp <= 0:
        winner_id = first
        result = "win"
    else:
        winner_id = second
        result = "win"
    
    return {
        "winner_id": winner_id,
        "loser_id": player2_id if winner_id == player1_id else player1_id,
        "result": result,
        "turns": turns,
        "battle_log": battle_log,
        "final_hp": {"p1": p1_hp, "p2": p2_hp}
    }

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_"))
def handle_duel_callback(call):
    user_id = call.from_user.id
    user = User(user_id)
    
    duel_type = call.data.split("_")[1]
    
    if duel_type == "quick":
        if user.data["money"] < 50:
            bot.answer_callback_query(call.id, "❌ Недостаточно монет! Нужно 50💰")
            return
        
        # Создание бота-противника
        bot_level = random.randint(max(1, user.data["level"] - 3), user.data["level"] + 3)
        
        # Временный бот
        bot_id = f"bot_{random.randint(10000,99999)}"
        users[bot_id] = {
            "username": f"Bot_{bot_level}",
            "first_name": f"Бот Lv.{bot_level}",
            "money": 0,
            "level": bot_level,
            "exp": 0,
            "hp": 100 + bot_level * 10,
            "max_hp": 100 + bot_level * 10,
            "wins": 0, "losses": 0,
            "inventory": [],
            "equipped_weapon": random.choice(list(items.keys())),
            "equipped_shield": None,
            "equipped_armor": None,
            "equipped_accessory": None,
            "equipped_boots": None
        }
        
        user.data["money"] -= 50
        user.save()
        
        result = execute_duel(str(user_id), bot_id, "quick", 50)
        
        # Удаление бота
        if bot_id in users:
            del users[bot_id]
        
        if result["winner_id"] == str(user_id):
            reward = 100
            user = User(user_id)
            user.data["money"] += reward
            user.data["wins"] += 1
            user.data["win_streak"] += 1
            user.data["exp"] += 30
            if user.data["win_streak"] > user.data["best_streak"]:
                user.data["best_streak"] = user.data["win_streak"]
            
            old_level = user.data["level"]
            check_level_up(user_id)
            user = User(user_id)
            
            result_text = f"""
<b>⚔ ПОБЕДА!</b>

Противник: Бот уровня {bot_level}
Ходов: {result['turns']}

💰 Награда: +100 монет
✨ Опыт: +30
🔥 Серия побед: {user.data['win_streak']}
"""
            if user.data["level"] > old_level:
                result_text += f"\n🎉 НОВЫЙ УРОВЕНЬ: {user.data['level']}!"
        else:
            user = User(user_id)
            user.data["losses"] += 1
            user.data["win_streak"] = 0
            user.data["exp"] += 10
            user.save()
            
            result_text = f"""
<b>💀 ПОРАЖЕНИЕ</b>

Противник: Бот уровня {bot_level}
Ходов: {result['turns']}

Утешительный опыт: +10
Серия побед сброшена
"""
        
        bot.edit_message_text(
            result_text,
            call.message.chat.id,
            call.message.message_id
        )
    
    elif duel_type == "ranked":
        if user.data["money"] < 100:
            bot.answer_callback_query(call.id, "❌ Недостаточно монет! Нужно 100💰")
            return
        
        bot.send_message(call.message.chat.id, 
            "🏆 Для рейтинговой дуэли используйте команду /ranked в ответ на сообщение противника")
    
    elif duel_type == "hardcore":
        if user.data["money"] < 500:
            bot.answer_callback_query(call.id, "❌ Недостаточно монет! Нужно 500💰")
            return
        
        bot.send_message(call.message.chat.id,
            "💀 Для хардкорной дуэли используйте команду /hardcore в ответ на сообщение противника\nСтавка: 500💰")
    
    elif duel_type == "friendly":
        bot.send_message(call.message.chat.id,
            "🎯 Для дружеской дуэли используйте команду /friendly в ответ на сообщение противника\nБез ставок и потерь!")
    
    elif duel_type == "survival":
        bot.send_message(call.message.chat.id,
            "🔥 Для дуэли на выживание используйте команду /survival в ответ на сообщение противника\nПриз: 200💰")
    
    elif duel_type == "team":
        bot.send_message(call.message.chat.id,
            "⚔ Командные дуэли 2x2 скоро появятся! Следите за обновлениями.")

@bot.message_handler(commands=['duel', 'quickduel', 'ranked', 'hardcore', 'friendly', 'survival'])
def duel_commands(message):
    command = message.text.split()[0].replace('/', '')
    user_id = message.from_user.id
    user = User(user_id)
    
    if command == "quickduel":
        # Быстрая дуэль
        handle_duel_callback(types.CallbackQuery(id="0", from_user=message.from_user, 
            message=message, data="duel_quick", chat_instance="0"))
        return
    
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Ответьте на сообщение игрока, с которым хотите сразиться!")
        return
    
    opponent_id = message.reply_to_message.from_user.id
    
    if opponent_id == user_id:
        bot.send_message(message.chat.id, "❌ Нельзя сражаться с самим собой!")
        return
    
    opponent = User(opponent_id)
    
    # Определение ставок
    if command == "duel":
        bet = 50
        duel_type = "normal"
    elif command == "ranked":
        bet = 100
        duel_type = "ranked"
    elif command == "hardcore":
        bet = 500
        duel_type = "hardcore"
    elif command == "friendly":
        bet = 0
        duel_type = "friendly"
    elif command == "survival":
        bet = 200
        duel_type = "survival"
    
    # Проверка баланса
    if bet > 0:
        if user.data["money"] < bet:
            bot.send_message(message.chat.id, f"❌ У вас недостаточно монет! Нужно {bet}💰")
            return
        if opponent.data["money"] < bet:
            bot.send_message(message.chat.id, f"❌ У противника недостаточно монет! Нужно {bet}💰")
            return
    
    # Подтверждение дуэли
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"acceptduel_{user_id}_{duel_type}_{bet}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"declineduel_{user_id}")
    )
    
    duel_request_text = f"""
<b>⚔ ВЫЗОВ НА ДУЭЛЬ!</b>

<b>{message.from_user.first_name}</b> вызывает <b>{message.reply_to_message.from_user.first_name}</b>!

Тип: <b>{duel_type.upper()}</b>
Ставка: <b>{bet}💰</b>

Ожидание подтверждения...
"""
    bot.send_message(message.chat.id, duel_request_text, reply_markup=markup)

# ==================== РП СИСТЕМА ====================
@bot.message_handler(func=lambda m: m.text == "🎮РП")
@bot.message_handler(commands=['rp'])
def rp_menu(message):
    rp_text = """
<b>🎮 РОЛЕВЫЕ КОМАНДЫ</b>

<b>Социальные:</b>
/hi - поздороваться
/bye - попрощаться
/dance - танцевать
/sing - петь
/whistle - свистеть
/think - задуматься

<b>Эмоции:</b>
/happy - радоваться
/sad - грустить
/angry - злиться
/love - признаться в любви

<b>Действия:</b>
/eat - поесть
/drink - попить
/sleep - поспать
/read - почитать
/write - написать

<b>Боевые стойки:</b>
/stance_attack - атакующая
/stance_defense - защитная
/stance_balanced - сбалансированная
"""
    bot.send_message(message.chat.id, rp_text)

@bot.message_handler(commands=['hi', 'hello', 'hey'])
def rp_hi(message):
    greetings = [
        f"{message.from_user.first_name} приветствует всех! 👋",
        f"{message.from_user.first_name} машет рукой!",
        f"Привет от {message.from_user.first_name}! 😊"
    ]
    bot.send_message(message.chat.id, random.choice(greetings))

@bot.message_handler(commands=['bye', 'goodbye'])
def rp_bye(message):
    bot.send_message(message.chat.id, f"{message.from_user.first_name} прощается со всеми! 👋")

@bot.message_handler(commands=['dance'])
def rp_dance(message):
    dances = ["💃 зажигательный танец!", "🕺 брейк-данс!", "💃🕺 вальс!", "🔥 танец с огнём!"]
    bot.send_message(message.chat.id, f"{message.from_user.first_name} исполняет {random.choice(dances)}")

@bot.message_handler(commands=['sing'])
def rp_sing(message):
    songs = ["🎵 'Yesterday'", "🎶 оперную арию", "🎤 рэп", "🎵 народную песню"]
    bot.send_message(message.chat.id, f"{message.from_user.first_name} поёт {random.choice(songs)}!")

@bot.message_handler(commands=['attack'])
def rp_attack(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, f"{message.from_user.first_name} атакует воздух! 💨")
        return
    
    target = message.reply_to_message.from_user.first_name
    attacks = [
        f"наносит мощный удар {target}! 💥",
        f"использует специальную атаку на {target}! ⚡",
        f"атакует {target} с невероятной скоростью! 🔥",
        f"проводит серию ударов по {target}! 👊"
    ]
    bot.send_message(message.chat.id, f"{message.from_user.first_name} {random.choice(attacks)}")

@bot.message_handler(commands=['heal'])
def rp_heal(message):
    heal_amount = random.randint(10, 30)
    bot.send_message(message.chat.id, f"{message.from_user.first_name} использует исцеление! 💚 +{heal_amount}")

# ==================== ЭКОНОМИКА ====================
@bot.message_handler(func=lambda m: m.text == "💰Работа")
@bot.message_handler(commands=['work'])
def work_handler(message):
    user_id = message.from_user.id
    user = User(user_id)
    
    now = datetime.now()
    if user.data.get("last_work"):
        last = datetime.fromisoformat(user.data["last_work"])
        if (now - last) < timedelta(hours=1):
            remaining = timedelta(hours=1) - (now - last)
            minutes = remaining.seconds // 60
            bot.send_message(message.chat.id, f"⏰ Вы устали! Отдохните ещё {minutes} мин.")
            return
    
    jobs = [
        {"name": "Охота на монстров", "min": 50, "max": 150, "exp": 20},
        {"name": "Защита каравана", "min": 60, "max": 120, "exp": 25},
        {"name": "Сбор редких трав", "min": 40, "max": 100, "exp": 15},
        {"name": "Тренировка новобранцев", "min": 70, "max": 160, "exp": 30},
        {"name": "Исследование руин", "min": 80, "max": 200, "exp": 35},
        {"name": "Охрана гильдии", "min": 55, "max": 130, "exp": 22},
        {"name": "Поиск сокровищ", "min": 100, "max": 300, "exp": 40},
        {"name": "Уборка в таверне", "min": 30, "max": 80, "exp": 10}
    ]
    
    job = random.choice(jobs)
    reward = random.randint(job["min"], job["max"]) * user.data["level"]
    exp_reward = job["exp"] * user.data["level"]
    
    user.data["money"] += reward
    user.data["exp"] += exp_reward
    user.data["last_work"] = now.isoformat()
    user.save()
    
    old_level = user.data["level"]
    check_level_up(user_id)
    user = User(user_id)
    
    result_text = f"""
<b>⚒ РАБОТА</b>

Вы {job['name'].lower()}!

💰 Награда: <b>+{reward} монет</b>
✨ Опыт: <b>+{exp_reward}</b>
"""
    if user.data["level"] > old_level:
        result_text += f"\n🎉 НОВЫЙ УРОВЕНЬ: <b>{user.data['level']}</b>!"
    
    bot.send_message(message.chat.id, result_text)

@bot.message_handler(func=lambda m: m.text == "🎁")
@bot.message_handler(commands=['daily'])
def daily_handler(message):
    user_id = message.from_user.id
    user = User(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if user.data["last_daily"] == today:
        bot.send_message(message.chat.id, "🎁 Вы уже получили ежедневный бонус! Приходите завтра.")
        return
    
    bonus = random.randint(100, 500)
    exp_bonus = random.randint(30, 100)
    
    # Шанс получить предмет
    got_item = None
    if random.random() < 0.1:  # 10% шанс
        common_items = [k for k, v in items.items() if v.get("rarity") == "common"]
        if common_items:
            got_item = random.choice(common_items)
            user.data["inventory"].append(got_item)
    
    user.data["money"] += bonus
    user.data["exp"] += exp_bonus
    user.data["last_daily"] = today
    user.save()
    
    old_level = user.data["level"]
    check_level_up(user_id)
    user = User(user_id)
    
    result_text = f"""
<b>🎁 ЕЖЕДНЕВНЫЙ БОНУС</b>

💰 Монет: <b>+{bonus}</b>
✨ Опыта: <b>+{exp_bonus}</b>
"""
    if got_item:
        item = items[got_item]
        result_text += f"\n🎒 Предмет: <b>{item['name']}</b>"
    
    if user.data["level"] > old_level:
        result_text += f"\n🎉 НОВЫЙ УРОВЕНЬ: <b>{user.data['level']}</b>!"
    
    bot.send_message(message.chat.id, result_text)

# ==================== ТОП И СТАТИСТИКА ====================
@bot.message_handler(func=lambda m: m.text == "📊Топ")
@bot.message_handler(commands=['top'])
def top_handler(message):
    # Сортировка игроков по разным критериям
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🏆 По уровню", callback_data="top_level"),
        types.InlineKeyboardButton("⚔ По победам", callback_data="top_wins"),
        types.InlineKeyboardButton("💰 По богатству", callback_data="top_money"),
        types.InlineKeyboardButton("🔥 По серии побед", callback_data="top_streak"),
        types.InlineKeyboardButton("🏅 По достижениям", callback_data="top_achievements")
    )
    
    bot.send_message(message.chat.id, "<b>📊 ТОП ИГРОКОВ</b>\nВыберите категорию:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def top_callback(call):
    category = call.data.split("_")[1]
    
    if category == "level":
        sorted_users = sorted(users.items(), key=lambda x: (x[1].get("level", 1), x[1].get("exp", 0)), reverse=True)[:10]
        title = "🏆 ТОП ПО УРОВНЮ"
    elif category == "wins":
        sorted_users = sorted(users.items(), key=lambda x: x[1].get("wins", 0), reverse=True)[:10]
        title = "⚔ ТОП ПО ПОБЕДАМ"
    elif category == "money":
        sorted_users = sorted(users.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]
        title = "💰 ТОП ПО БОГАТСТВУ"
    elif category == "streak":
        sorted_users = sorted(users.items(), key=lambda x: x[1].get("best_streak", 0), reverse=True)[:10]
        title = "🔥 ТОП ПО СЕРИИ ПОБЕД"
    elif category == "achievements":
        sorted_users = sorted(users.items(), key=lambda x: len(x[1].get("achievements", [])), reverse=True)[:10]
        title = "🏅 ТОП ПО ДОСТИЖЕНИЯМ"
    
    top_text = f"<b>{title}</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, (user_id, data) in enumerate(sorted_users):
        if category == "level":
            value = f"Ур.{data.get('level', 1)} ({data.get('exp', 0)} EXP)"
        elif category == "wins":
            value = f"{data.get('wins', 0)} побед"
        elif category == "money":
            value = f"{data.get('money', 0)}💰"
        elif category == "streak":
            value = f"Серия: {data.get('best_streak', 0)}"
        elif category == "achievements":
            value = f"{len(data.get('achievements', []))} достижений"
        
        top_text += f"{medals[i]} {data.get('first_name', 'Игрок')}: {value}\n"
    
    bot.edit_message_text(top_text, call.message.chat.id, call.message.message_id)

# ==================== СИСТЕМА КЛАНОВ ====================
@bot.message_handler(func=lambda m: m.text == "🛡Клан")
@bot.message_handler(commands=['clan'])
def clan_handler(message):
    user_id = message.from_user.id
    user = User(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if user.data.get("clan"):
        clan_name = user.data["clan"]
        if clan_name in clans:
            clan = clans[clan_name]
            clan_text = f"""
<b>🛡 КЛАН: {clan_name}</b>

👑 Лидер: {clan.get('leader_name', 'Неизвестно')}
👥 Участников: {len(clan.get('members', []))}
💰 Казна клана: {clan.get('treasury', 0)}
🏆 Побед: {clan.get('wins', 0)}

<b>Участники:</b>
{chr(10).join([f'• {m}' for m in clan.get('members', [])[:10]])}
"""
            markup.add(
                types.InlineKeyboardButton("📊 Инфо клана", callback_data="clan_info"),
                types.InlineKeyboardButton("👥 Участники", callback_data="clan_members"),
                types.InlineKeyboardButton("💰 Пополнить казну", callback_data="clan_donate"),
                types.InlineKeyboardButton("🚪 Покинуть клан", callback_data="clan_leave")
            )
        else:
            clan_text = "🛡 Ваш клан не найден. Возможно, он был удалён."
            markup.add(types.InlineKeyboardButton("🛡 Создать клан", callback_data="clan_create"))
    else:
        clan_text = """
<b>🛡 СИСТЕМА КЛАНОВ</b>

Вы не состоите в клане!

<b>Доступные действия:</b>
• Создать свой клан (5000💰)
• Вступить в существующий
• Участвовать в клановых войнах
"""
        markup.add(
            types.InlineKeyboardButton("🛡 Создать клан", callback_data="clan_create"),
            types.InlineKeyboardButton("📋 Список кланов", callback_data="clan_list"),
            types.InlineKeyboardButton("ℹ О кланах", callback_data="clan_about")
        )
    
    bot.send_message(message.chat.id, clan_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_"))
def clan_callback(call):
    user_id = call.from_user.id
    user = User(user_id)
    action = call.data.split("_")[1]
    
    if action == "create":
        if user.data["money"] < 5000:
            bot.answer_callback_query(call.id, "❌ Нужно 5000💰 для создания клана!")
            return
        bot.send_message(call.message.chat.id, 
            "🛡 Для создания клана используйте команду:\n/create_clan [название]")
    
    elif action == "list":
        if not clans:
            bot.answer_callback_query(call.id, "📋 Нет активных кланов")
            return
        clan_list = "<b>📋 СПИСОК КЛАНОВ</b>\n\n"
        for clan_name, clan_data in clans.items():
            clan_list += f"🛡 {clan_name}: {len(clan_data.get('members', []))} уч.\n"
        bot.send_message(call.message.chat.id, clan_list)

@bot.message_handler(commands=['create_clan'])
def create_clan(message):
    user_id = message.from_user.id
    user = User(user_id)
    
    if user.data.get("clan"):
        bot.send_message(message.chat.id, "❌ Вы уже состоите в клане!")
        return
    
    if user.data["money"] < 5000:
        bot.send_message(message.chat.id, "❌ Недостаточно монет! Нужно 5000💰")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ Укажите название клана: /create_clan [название]")
        return
    
    clan_name = parts[1].strip()
    if clan_name in clans:
        bot.send_message(message.chat.id, "❌ Клан с таким названием уже существует!")
        return
    
    if len(clan_name) > 20:
        bot.send_message(message.chat.id, "❌ Название клана не должно превышать 20 символов!")
        return
    
    user.data["money"] -= 5000
    user.data["clan"] = clan_name
    user.save()
    
    clans[clan_name] = {
        "leader_id": user_id,
        "leader_name": message.from_user.first_name,
        "members": [message.from_user.first_name],
        "treasury": 0,
        "wins": 0,
        "created_at": datetime.now().isoformat()
    }
    save_json(CLANS_FILE, clans)
    
    bot.send_message(message.chat.id, f"""
<b>🛡 КЛАН СОЗДАН!</b>

Название: <b>{clan_name}</b>
Лидер: {message.from_user.first_name}
Стоимость: 5000💰

Приглашайте игроков командой /invite_clan [имя]
""")

# ==================== КВЕСТЫ ====================
@bot.message_handler(func=lambda m: m.text == "📜Квесты")
@bot.message_handler(commands=['quests'])
def quests_handler(message):
    user_id = message.from_user.id
    user = User(user_id)
    
    # Инициализация квестов для нового дня
    today = datetime.now().strftime("%Y-%m-%d")
    if "quests_date" not in user.data or user.data["quests_date"] != today:
        user.data["active_quests"] = {}
        for i, quest in enumerate(random.sample(DAILY_QUESTS, 3)):
            quest_copy = quest.copy()
            quest_copy["id"] = f"quest_{today}_{i}"
            quest_copy["progress"] = 0
            user.data["active_quests"][quest_copy["id"]] = quest_copy
        user.data["quests_date"] = today
        user.save()
    
    quests_text = f"<b>📜 ЕЖЕДНЕВНЫЕ КВЕСТЫ</b> ({today})\n\n"
    
    for quest_id, quest in user.data["active_quests"].items():
        progress = quest.get("progress", 0)
        target = quest["target"]
        progress_bar = "█" * int(progress / target * 10) if target > 0 else "█" * 10
        empty_bar = "░" * (10 - len(progress_bar))
        
        quests_text += f"<b>{quest['name']}</b>\n"
        quests_text += f"📊 [{progress_bar}{empty_bar}] {progress}/{target}\n"
        quests_text += f"📝 {quest['description']}\n"
        quests_text += f"🎁 Награда: {quest['reward_money']}💰 + {quest['reward_exp']} EXP\n\n"
    
    bot.send_message(message.chat.id, quests_text)

# ==================== ДОСТИЖЕНИЯ ====================
@bot.message_handler(func=lambda m: m.text == "🏅Ачивки")
@bot.message_handler(commands=['achievements'])
def achievements_handler(message):
    user_id = message.from_user.id
    user = User(user_id)
    
    ach_text = f"<b>🏅 ДОСТИЖЕНИЯ</b> ({len(user.data['achievements'])}/{len(ACHIEVEMENTS)})\n\n"
    
    for ach_id, ach_data in ACHIEVEMENTS.items():
        if ach_id in user.data["achievements"]:
            ach_text += f"✅ {ach_data['name']}: {ach_data['description']}\n"
        else:
            ach_text += f"🔒 {ach_data['name']}: {ach_data['description']}\n"
    
    bot.send_message(message.chat.id, ach_text)

# ==================== АДМИН-ПАНЕЛЬ ====================
@bot.message_handler(commands=['admin'])
def admin_handler(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Доступ запрещён!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("💰 Выдать монеты", callback_data="admin_money"),
        types.InlineKeyboardButton("🎁 Выдать предмет", callback_data="admin_item"),
        types.InlineKeyboardButton("👤 Инфо игрока", callback_data="admin_user"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🔄 Сброс дня", callback_data="admin_reset"),
        types.InlineKeyboardButton("💎 Лимит. предметы", callback_data="admin_limited"),
        types.InlineKeyboardButton("❌ Бан игрока", callback_data="admin_ban")
    )
    
    admin_text = """
<b>🔧 АДМИН-ПАНЕЛЬ</b>

Выберите действие:
"""
    bot.send_message(message.chat.id, admin_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Доступ запрещён!")
        return
    
    action = call.data.split("_")[1]
    
    if action == "stats":
        total_users = len(users)
        total_money = sum(u.get("money", 0) for u in users.values())
        total_duels = sum(u.get("wins", 0) + u.get("losses", 0) for u in users.values())
        active_clans = len(clans)
        
        stats_text = f"""
<b>📊 СТАТИСТИКА БОТА</b>

👥 Пользователей: {total_users}
💰 Монет в обороте: {total_money}
⚔ Всего дуэлей: {total_duels}
🛡 Кланов: {active_clans}
💎 Лимит. предметов: {sum(v['remaining'] for v in limited_items.values())}
📦 Обычных предметов: {len(items)}
        
        Бот активен с: {datetime.now().strftime('%d.%m.%Y')}
        """
        bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id)
    
    elif action == "broadcast":
        bot.send_message(call.message.chat.id, "📢 Введите сообщение для рассылки:\n/broadcast [текст]")

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text.replace('/broadcast', '', 1).strip()
    if not text:
        bot.send_message(message.chat.id, "❌ Введите текст рассылки!")
        return
    
    success = 0
    failed = 0
    for user_id in users:
        try:
            bot.send_message(int(user_id), f"📢 <b>Рассылка от администрации:</b>\n\n{text}")
            success += 1
        except:
            failed += 1
    
    bot.send_message(message.chat.id, f"✅ Рассылка отправлена!\nУспешно: {success}\nОшибок: {failed}")

# ==================== ОБРАБОТКА CALLBACK ====================
@bot.callback_query_handler(func=lambda call: True)
def global_callback_handler(call):
    user_id = call.from_user.id
    user = User(user_id)
    
    # Покупка предметов
    if call.data.startswith("buy_"):
        item_key = call.data[4:]
        item = items.get(item_key)
        
        if not item:
            bot.answer_callback_query(call.id, "❌ Предмет не найден!")
            return
        
        if user.data["level"] < item.get("level_req", 1):
            bot.answer_callback_query(call.id, f"❌ Нужен {item.get('level_req', 1)} уровень!")
            return
        
        if user.data["money"] < item["price"]:
            bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
            return
        
        user.data["money"] -= item["price"]
        user.data["inventory"].append(item_key)
        user.save()
        
        bot.answer_callback_query(call.id, f"✅ Куплено: {item['name']}!")
        bot.send_message(call.message.chat.id, f"✅ Вы приобрели <b>{item['name']}</b> за {item['price']}💰!")
    
    # Покупка лимитированных
    elif call.data.startswith("buylimited_"):
        item_key = call.data[11:]
        item = limited_items.get(item_key)
        
        if not item or item["remaining"] <= 0:
            bot.answer_callback_query(call.id, "❌ Предмет закончился!")
            return
        
        if user.data["money"] < item["price"]:
            bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
            return
        
        user.data["money"] -= item["price"]
        user.data["inventory"].append(item_key)
        item["remaining"] -= 1
        user.save()
        save_json(LIMITED_FILE, limited_items)
        
        bot.answer_callback_query(call.id, f"💎 Куплен легендарный предмет: {item['name']}!")
        bot.send_message(call.message.chat.id, 
            f"💎 ПОЗДРАВЛЯЕМ! Вы приобрели <b>{item['name']}</b>!\n"
            f"Осталось: {item['remaining']}/{item['total']}")
    
    # Экипировка
    elif call.data.startswith("equip_"):
        item_key = call.data[6:]
        item = items.get(item_key) or limited_items.get(item_key)
        
        if not item:
            bot.answer_callback_query(call.id, "❌ Предмет не найден!")
            return
        
        if item_key not in user.data["inventory"]:
            bot.answer_callback_query(call.id, "❌ Предмета нет в инвентаре!")
            return
        
        if item["type"] == "weapon":
            # Возвращаем старый предмет в инвентарь
            if user.data["equipped_weapon"] and user.data["equipped_weapon"] in user.data["inventory"]:
                pass  # Оставляем в инвентаре
            user.data["equipped_weapon"] = item_key
        elif item["type"] == "shield":
            if user.data["equipped_shield"] and user.data["equipped_shield"] in user.data["inventory"]:
                pass
            user.data["equipped_shield"] = item_key
        elif item["type"] == "armor":
            if user.data["equipped_armor"] and user.data["equipped_armor"] in user.data["inventory"]:
                pass
            user.data["equipped_armor"] = item_key
        elif item["type"] == "accessory":
            if user.data["equipped_accessory"] and user.data["equipped_accessory"] in user.data["inventory"]:
                pass
            user.data["equipped_accessory"] = item_key
        elif item["type"] == "boots":
            if user.data["equipped_boots"] and user.data["equipped_boots"] in user.data["inventory"]:
                pass
            user.data["equipped_boots"] = item_key
        
        user.save()
        bot.answer_callback_query(call.id, f"✅ {item['name']} экипирован!")
    
    # Использование зелья
    elif call.data.startswith("use_"):
        item_key = call.data[4:]
        item = items.get(item_key) or limited_items.get(item_key)
        
        if not item or item["type"] != "potion":
            bot.answer_callback_query(call.id, "❌ Нельзя использовать этот предмет!")
            return
        
        if item_key not in user.data["inventory"]:
            bot.answer_callback_query(call.id, "❌ Предмета нет в инвентаре!")
            return
        
        if user.data["hp"] >= user.data["max_hp"]:
            bot.answer_callback_query(call.id, "❌ У вас полное здоровье!")
            return
        
        heal = item.get("heal", 25)
        user.data["hp"] = min(user.data["max_hp"], user.data["hp"] + heal)
        user.data["inventory"].remove(item_key)
        user.data["items_used"] += 1
        user.save()
        
        bot.answer_callback_query(call.id, f"💚 +{heal} HP! Здоровье: {user.data['hp']}/{user.data['max_hp']}")
    
    # Принятие дуэли
    elif call.data.startswith("acceptduel_"):
        parts = call.data.split("_")
        challenger_id = int(parts[1])
        duel_type = parts[2]
        bet = int(parts[3])
        
        if call.from_user.id != challenger_id:
            # Принимающий игрок
            opponent_id = call.from_user.id
            result = execute_duel(str(challenger_id), str(opponent_id), duel_type, bet)
            
            # Выплата ставок
            if bet > 0:
                challenger = User(challenger_id)
                opponent = User(opponent_id)
                
                challenger.data["money"] -= bet
                opponent.data["money"] -= bet
                
                if result["winner_id"]:
                    winner = User(result["winner_id"])
                    winner.data["money"] += bet * 2
                    winner.data["wins"] += 1
                    winner.save()
                    
                    loser_id = result["loser_id"]
                    loser = User(loser_id)
                    loser.data["losses"] += 1
                    loser.save()
                
                challenger.save()
                opponent.save()
            
            result_text = f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>

Победитель: <b>{User(result['winner_id']).data['first_name']}</b>
Ходов: {result['turns']}
Ставка: {bet}💰
"""
            bot.edit_message_text(result_text, call.message.chat.id, call.message.message_id)

# ==================== ЗАПУСК БОТА ====================
def init_bot():
    """Инициализация и запуск бота"""
    print("=" * 50)
    print("⚔ ДУЭЛЬ БОТ v3.0 ЗАПУСКАЕТСЯ...")
    print("=" * 50)
    print(f"📅 Дата запуска: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"👤 Администратор ID: {ADMIN_ID}")
    print(f"📦 Предметов загружено: {len(items)}")
    print(f"💎 Лимитированных: {len(limited_items)}")
    print(f"👥 Пользователей: {len(users)}")
    print(f"🛡 Кланов: {len(clans)}")
    print("=" * 50)
    print("✅ Бот готов к работе!")
    print("=" * 50)
    
    # Запуск с обработкой ошибок
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"⚠ Ошибка: {e}")
            print(f"🔄 Перезапуск через 5 секунд...")
            time.sleep(5)

if __name__ == "__main__":
    init_bot()
