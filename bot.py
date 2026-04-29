import telebot
from telebot import types
import json
import random
import time
from datetime import datetime, timedelta

# Конфигурация
TOKEN = '8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE'
ADMIN_ID = 5356400377
bot = telebot.TeleBot(TOKEN)

# Файлы для хранения данных
USERS_FILE = 'users.json'
ITEMS_FILE = 'items.json'
DUELS_FILE = 'duels.json'
LIMITED_FILE = 'limited_items.json'

# Стартовые данные
def load_json(filename, default={}):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Загрузка данных
users = load_json(USERS_FILE, {})
items = load_json(ITEMS_FILE, {
    "wooden_sword": {"name": "🗡 Деревянный меч", "damage": 5, "price": 100, "type": "weapon"},
    "iron_sword": {"name": "⚔ Железный меч", "damage": 10, "price": 300, "type": "weapon"},
    "legendary_sword": {"name": "🔥 Легендарный меч", "damage": 25, "price": 1000, "type": "weapon"},
    "wooden_shield": {"name": "🛡 Деревянный щит", "defense": 5, "price": 150, "type": "shield"},
    "iron_shield": {"name": "🛡 Железный щит", "defense": 10, "price": 400, "type": "shield"},
    "health_potion": {"name": "🧪 Зелье здоровья", "heal": 20, "price": 50, "type": "potion"},
    "magic_wand": {"name": "🪄 Волшебная палочка", "damage": 15, "price": 500, "type": "weapon"},
    "dragon_armor": {"name": "🐉 Броня дракона", "defense": 20, "price": 2000, "type": "armor"}
})
duels = load_json(DUELS_FILE, {})
limited_items = load_json(LIMITED_FILE, {
    "excalibur": {"name": "⚡ Экскалибур", "damage": 50, "total": 10, "remaining": 10, "price": 5000, "type": "weapon"},
    "infinity_shield": {"name": "💎 Бесконечный щит", "defense": 40, "total": 5, "remaining": 5, "price": 10000, "type": "shield"},
    "phoenix_feather": {"name": "🦅 Перо Феникса", "heal": 100, "total": 15, "remaining": 15, "price": 3000, "type": "potion"}
})

# Класс пользователя
class User:
    def __init__(self, user_id, username="Неизвестный"):
        if str(user_id) not in users:
            users[str(user_id)] = {
                "username": username,
                "money": 500,
                "level": 1,
                "exp": 0,
                "wins": 0,
                "losses": 0,
                "inventory": [],
                "equipped_weapon": None,
                "equipped_shield": None,
                "equipped_armor": None,
                "last_daily": None,
                "last_work": None,
                "title": "Новичок"
            }
            save_json(USERS_FILE, users)
    
    @property
    def data(self):
        return users[str(self.user_id)]
    
    def save(self):
        users[str(self.user_id)] = self.data
        save_json(USERS_FILE, users)

# Система опыта и уровней
def check_level_up(user_id):
    user = User(user_id)
    level = user.data["level"]
    exp_needed = level * 100
    if user.data["exp"] >= exp_needed:
        user.data["exp"] -= exp_needed
        user.data["level"] += 1
        user.save()
        titles = ["Новичок", "Воитель", "Рыцарь", "Ветеран", "Мастер", "Грандмастер", "Легенда", "Божество"]
        if user.data["level"] <= len(titles):
            user.data["title"] = titles[user.data["level"]-1]
        user.save()
        return True
    return False

# Основное меню
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    User(user_id, username)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⚔ Дуэль", "📊 Профиль")
    markup.row("🎒 Инвентарь", "🏪 Магазин")
    markup.row("💎 Лимитированные", "⚙ Настройки")
    markup.row("🎮 РП Команды", "💰 Работа")
    markup.row("🎁 Ежедневный бонус")
    
    welcome_text = f"""
⚔ *ДУЭЛЬ БОТ* ⚔

Привет, {message.from_user.first_name}!
Добро пожаловать в мир бесконечных сражений!

🎯 Сражайся с другими игроками
🛡 Собирай редкое оружие
💎 Покупай лимитированные предметы
🏆 Стань легендой арены!

Твой баланс: 500 монет
Для начала используй кнопки меню!
    """
    
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

# Профиль
@bot.message_handler(func=lambda m: m.text == "📊 Профиль")
def profile(message):
    user_id = message.from_user.id
    user = User(user_id)
    u = user.data
    
    equipped = []
    if u["equipped_weapon"]:
        equipped.append(f"Оружие: {items[u['equipped_weapon']]['name']}")
    if u["equipped_shield"]:
        equipped.append(f"Щит: {items[u['equipped_shield']]['name']}")
    if u["equipped_armor"]:
        equipped.append(f"Броня: {items[u['equipped_armor']]['name']}")
    
    profile_text = f"""
📊 *Профиль игрока*

👤 Имя: {u['username']}
🏅 Титул: {u['title']}
⭐ Уровень: {u['level']}
✨ Опыт: {u['exp']}/{u['level']*100}

💰 Баланс: {u['money']} монет

⚔ Статистика дуэлей:
✅ Побед: {u['wins']}
❌ Поражений: {u['losses']}
📊 Винрейт: {(u['wins']/(u['wins']+u['losses'])*100 if (u['wins']+u['losses']) > 0 else 0):.1f}%

🛡 Экипировка:
{chr(10).join(equipped) if equipped else 'Нет экипировки'}

🎒 Предметов в инвентаре: {len(u['inventory'])}
    """
    bot.send_message(message.chat.id, profile_text, parse_mode="Markdown")

# Инвентарь
@bot.message_handler(func=lambda m: m.text == "🎒 Инвентарь")
def inventory(message):
    user_id = message.from_user.id
    user = User(user_id)
    
    if not user.data["inventory"]:
        bot.send_message(message.chat.id, "🎒 Ваш инвентарь пуст!")
        return
    
    inv_text = "🎒 *Ваш инвентарь:*\n\n"
    for i, item_key in enumerate(user.data["inventory"], 1):
        item = items.get(item_key, limited_items.get(item_key))
        if item:
            inv_text += f"{i}. {item['name']}\n"
    
    markup = types.InlineKeyboardMarkup()
    for item_key in set(user.data["inventory"]):
        item = items.get(item_key, limited_items.get(item_key))
        if item and item["type"] in ["weapon", "shield", "armor"]:
            markup.add(types.InlineKeyboardButton(
                f"Экипировать {item['name']}", 
                callback_data=f"equip_{item_key}"
            ))
    
    bot.send_message(message.chat.id, inv_text, parse_mode="Markdown", reply_markup=markup)

# Магазин
@bot.message_handler(func=lambda m: m.text == "🏪 Магазин")
def shop(message):
    shop_text = "🏪 *МАГАЗИН ОРУЖИЯ*\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, item in items.items():
        shop_text += f"{item['name']}\n"
        if item["type"] == "weapon":
            shop_text += f"⚔ Урон: {item['damage']}\n"
        elif item["type"] == "shield":
            shop_text += f"🛡 Защита: {item['defense']}\n"
        elif item["type"] == "potion":
            shop_text += f"💊 Лечение: {item['heal']}\n"
        shop_text += f"💰 Цена: {item['price']} монет\n\n"
        
        markup.add(types.InlineKeyboardButton(
            f"Купить {item['name']} - {item['price']}💰", 
            callback_data=f"buy_{item_key}"
        ))
    
    bot.send_message(message.chat.id, shop_text, parse_mode="Markdown", reply_markup=markup)

# Лимитированные предметы
@bot.message_handler(func=lambda m: m.text == "💎 Лимитированные")
def limited_shop(message):
    if not limited_items:
        bot.send_message(message.chat.id, "💎 Лимитированных предметов нет в наличии!")
        return
    
    limit_text = "💎 *ЛИМИТИРОВАННЫЕ ПРЕДМЕТЫ*\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for item_key, item in limited_items.items():
        if item["remaining"] > 0:
            limit_text += f"{item['name']}\n"
            limit_text += f"📦 Осталось: {item['remaining']}/{item['total']}\n"
            if item["type"] == "weapon":
                limit_text += f"⚔ Урон: {item['damage']}\n"
            elif item["type"] == "shield":
                limit_text += f"🛡 Защита: {item['defense']}\n"
            elif item["type"] == "potion":
                limit_text += f"💊 Лечение: {item['heal']}\n"
            limit_text += f"💰 Цена: {item['price']} монет\n\n"
            
            markup.add(types.InlineKeyboardButton(
                f"Купить {item['name']} - {item['price']}💰", 
                callback_data=f"buylimited_{item_key}"
            ))
    
    bot.send_message(message.chat.id, limit_text, parse_mode="Markdown", reply_markup=markup)

# Ежедневный бонус
@bot.message_handler(func=lambda m: m.text == "🎁 Ежедневный бонус")
def daily_bonus(message):
    user_id = message.from_user.id
    user = User(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if user.data["last_daily"] == today:
        bot.send_message(message.chat.id, "🎁 Вы уже получили ежедневный бонус! Приходите завтра.")
        return
    
    bonus = random.randint(50, 200)
    exp_bonus = random.randint(10, 50)
    user.data["money"] += bonus
    user.data["exp"] += exp_bonus
    user.data["last_daily"] = today
    user.save()
    
    bonus_text = f"""
🎁 *ЕЖЕДНЕВНЫЙ БОНУС*

Вы получили:
💰 Монет: +{bonus}
✨ Опыта: +{exp_bonus}

Приходите завтра за новой наградой!
    """
    bot.send_message(message.chat.id, bonus_text, parse_mode="Markdown")
    
    if check_level_up(user_id):
        user = User(user_id)
        bot.send_message(message.chat.id, f"🎉 Поздравляем! Вы достигли уровня {user.data['level']}!")

# Работа
@bot.message_handler(func=lambda m: m.text == "💰 Работа")
def work(message):
    user_id = message.from_user.id
    user = User(user_id)
    
    now = datetime.now()
    if user.data["last_work"] and (now - datetime.fromisoformat(user.data["last_work"])) < timedelta(hours=2):
        remaining = timedelta(hours=2) - (now - datetime.fromisoformat(user.data["last_work"]))
        bot.send_message(message.chat.id, f"⏰ Вы устали! Отдохните ещё {remaining.seconds//3600}ч {remaining.seconds%3600//60}м")
        return
    
    jobs = [
        "Охотились на монстров",
        "Собирали травы",
        "Защищали деревню",
        "Тренировали новобранцев",
        "Исследовали подземелье",
        "Торговали на рынке",
        "Выполняли поручения гильдии"
    ]
    
    reward = random.randint(30, 100) * user.data["level"]
    exp_reward = random.randint(20, 60)
    
    user.data["money"] += reward
    user.data["exp"] += exp_reward
    user.data["last_work"] = now.isoformat()
    user.save()
    
    work_text = f"""
⚒ *РАБОТА*
Вы {random.choice(jobs)}

Награда:
💰 Монет: +{reward}
✨ Опыта: +{exp_reward}
    """
    bot.send_message(message.chat.id, work_text, parse_mode="Markdown")
    
    if check_level_up(user_id):
        user = User(user_id)
        bot.send_message(message.chat.id, f"🎉 Поздравляем! Вы достигли уровня {user.data['level']}! Титул: {user.data['title']}")

# РП команды
@bot.message_handler(func=lambda m: m.text == "🎮 РП Команды")
def rp_commands(message):
    rp_text = """
🎮 *РП КОМАНДЫ*

Боевые:
/attack [имя] - Атаковать противника
/defend - Встать в защиту
/use_potion - Использовать зелье

Социальные:
/hello - Поздороваться
/dance - Танцевать
/sit - Сесть
/meditate - Медитировать
/train - Тренироваться
/explore - Исследовать

Экономика:
/give [сумма] @user - Передать монеты
/bet [сумма] - Сделать ставку

Прочее:
/flip - Подбросить монетку
/roll - Бросить кубик
/hug @user - Обнять игрока
/punch @user - Ударить игрока (шутка)
    """
    bot.send_message(message.chat.id, rp_text, parse_mode="Markdown")

# РП команды
@bot.message_handler(commands=['hello'])
def hello(message):
    greetings = [
        f"{message.from_user.first_name} приветствует всех! 👋",
        f"{message.from_user.first_name} машет рукой! 🌟",
        f"Привет от {message.from_user.first_name}! 🤗"
    ]
    bot.send_message(message.chat.id, random.choice(greetings))

@bot.message_handler(commands=['dance'])
def dance(message):
    bot.send_message(message.chat.id, f"💃 {message.from_user.first_name} зажигательно танцует!")

@bot.message_handler(commands=['sit'])
def sit(message):
    bot.send_message(message.chat.id, f"🪑 {message.from_user.first_name} присел отдохнуть.")

@bot.message_handler(commands=['meditate'])
def meditate(message):
    user_id = message.from_user.id
    user = User(user_id)
    exp = random.randint(5, 15)
    user.data["exp"] += exp
    user.save()
    bot.send_message(message.chat.id, f"🧘 {message.from_user.first_name} медитирует и получает {exp} опыта!")
    check_level_up(user_id)

@bot.message_handler(commands=['train'])
def train(message):
    user_id = message.from_user.id
    user = User(user_id)
    exp = random.randint(10, 30)
    user.data["exp"] += exp
    user.save()
    bot.send_message(message.chat.id, f"💪 {message.from_user.first_name} усердно тренируется! +{exp} опыта")
    check_level_up(user_id)

@bot.message_handler(commands=['explore'])
def explore(message):
    user_id = message.from_user.id
    user = User(user_id)
    
    discoveries = [
        "нашел древние руины! 🏛",
        "обнаружил пещеру с сокровищами! 💎",
        "встретил дружелюбного дракона! 🐉",
        "нашел заброшенный храм! ⛩",
        "открыл новый торговый путь! 🗺"
    ]
    
    reward = random.randint(20, 80)
    user.data["money"] += reward
    user.save()
    bot.send_message(message.chat.id, f"🔍 {message.from_user.first_name} {random.choice(discoveries)} +{reward}💰")

@bot.message_handler(commands=['flip'])
def flip_coin(message):
    result = random.choice(["Орёл 🦅", "Решка 👑"])
    bot.send_message(message.chat.id, f"🪙 {message.from_user.first_name} подбрасывает монетку... {result}!")

@bot.message_handler(commands=['roll'])
def roll_dice(message):
    result = random.randint(1, 6)
    dice_faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    bot.send_message(message.chat.id, f"🎲 {message.from_user.first_name} бросает кубик: {dice_faces[result-1]} ({result})")

@bot.message_handler(commands=['hug'])
def hug(message):
    if message.reply_to_message:
        target = message.reply_to_message.from_user.first_name
        bot.send_message(message.chat.id, f"🤗 {message.from_user.first_name} крепко обнимает {target}!")
    else:
        bot.send_message(message.chat.id, f"🤗 {message.from_user.first_name} обнимает всех!")

@bot.message_handler(commands=['punch'])
def punch(message):
    if message.reply_to_message:
        target = message.reply_to_message.from_user.first_name
        bot.send_message(message.chat.id, f"👊 {message.from_user.first_name} шутливо бьёт {target}! Это не больно 😄")
    else:
        bot.send_message(message.chat.id, f"👊 {message.from_user.first_name} бьёт воздух!")

@bot.message_handler(commands=['give'])
def give_money(message):
    try:
        parts = message.text.split()
        amount = int(parts[1])
        
        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
        else:
            bot.send_message(message.chat.id, "❌ Ответьте на сообщение игрока, которому хотите передать монеты!")
            return
        
        user_id = message.from_user.id
        user = User(user_id)
        
        if user.data["money"] < amount:
            bot.send_message(message.chat.id, "❌ Недостаточно монет!")
            return
        
        if amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма должна быть положительной!")
            return
        
        target = User(target_id)
        user.data["money"] -= amount
        target.data["money"] += amount
        user.save()
        target.save()
        
        bot.send_message(message.chat.id, f"💰 {message.from_user.first_name} передал {amount} монет игроку {target_name}!")
    except:
        bot.send_message(message.chat.id, "❌ Использование: /give [сумма] (в ответ на сообщение игрока)")

# Дуэль
@bot.message_handler(func=lambda m: m.text == "⚔ Дуэль")
def duel_start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Быстрая дуэль", callback_data="quick_duel"))
    markup.add(types.InlineKeyboardButton("Дуэль с игроком", callback_data="player_duel"))
    
    duel_text = """
⚔ *СИСТЕМА ДУЭЛЕЙ*

Выберите тип дуэли:
• Быстрая дуэль - случайный противник
• Дуэль с игроком - ответьте на сообщение игрока

Ставка: 50 монет с каждого участника
Победитель забирает всё!
    """
    bot.send_message(message.chat.id, duel_text, parse_mode="Markdown", reply_markup=markup)

# Настройки
@bot.message_handler(func=lambda m: m.text == "⚙ Настройки")
def settings(message):
    user_id = message.from_user.id
    user = User(user_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Сменить никнейм", callback_data="change_nick"))
    markup.add(types.InlineKeyboardButton("Сбросить статистику", callback_data="reset_stats"))
    
    settings_text = f"""
⚙ *НАСТРОЙКИ*

👤 Текущий ник: {user.data['username']}
🎮 Уровень: {user.data['level']}
🏆 Побед: {user.data['wins']}
    """
    bot.send_message(message.chat.id, settings_text, parse_mode="Markdown", reply_markup=markup)

# Админ-панель
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к админ-панели!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📊 Статистика бота", callback_data="admin_stats"))
    markup.add(types.InlineKeyboardButton("💰 Выдать монеты", callback_data="admin_give_money"))
    markup.add(types.InlineKeyboardButton("🎁 Выдать предмет", callback_data="admin_give_item"))
    markup.add(types.InlineKeyboardButton("👤 Информация об игроке", callback_data="admin_user_info"))
    markup.add(types.InlineKeyboardButton("🔄 Сбросить бонусы", callback_data="admin_reset_bonuses"))
    markup.add(types.InlineKeyboardButton("📦 Управление лимитированными", callback_data="admin_limited"))
    markup.add(types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"))
    
    bot.send_message(message.chat.id, "🔧 *АДМИН-ПАНЕЛЬ*", parse_mode="Markdown", reply_markup=markup)

# Обработка callback
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    user = User(user_id)
    
    # Покупка обычных предметов
    if call.data.startswith("buy_"):
        item_key = call.data[4:]
        item = items.get(item_key)
        
        if not item:
            bot.answer_callback_query(call.id, "❌ Предмет не найден!")
            return
        
        if user.data["money"] < item["price"]:
            bot.answer_callback_query(call.id, "❌ Недостаточно монет!")
            return
        
        user.data["money"] -= item["price"]
        user.data["inventory"].append(item_key)
        user.save()
        
        bot.answer_callback_query(call.id, f"✅ Вы купили {item['name']}!")
        bot.send_message(call.message.chat.id, f"✅ Поздравляем с покупкой: {item['name']}!")
    
    # Покупка лимитированных предметов
    elif call.data.startswith("buylimited_"):
        item_key = call.data[12:]
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
        
        bot.answer_callback_query(call.id, f"✅ Вы купили лимитированный предмет: {item['name']}!")
        bot.send_message(call.message.chat.id, f"💎 Поздравляем! Вы приобрели редкий предмет: {item['name']}!\nОсталось: {item['remaining']}/{item['total']}")
    
    # Экипировка предметов
    elif call.data.startswith("equip_"):
        item_key = call.data[6:]
        item = items.get(item_key, limited_items.get(item_key))
        
        if not item:
            bot.answer_callback_query(call.id, "❌ Предмет не найден!")
            return
        
        if item["type"] == "weapon":
            user.data["equipped_weapon"] = item_key
        elif item["type"] in ["shield", "armor"]:
            user.data["equipped_shield"] = item_key
        
        user.save()
        bot.answer_callback_query(call.id, f"✅ {item['name']} экипирован!")
    
    # Быстрая дуэль
    elif call.data == "quick_duel":
        if user.data["money"] < 50:
            bot.answer_callback_query(call.id, "❌ Нужно 50 монет для дуэли!")
            return
        
        user.data["money"] -= 50
        user.save()
        
        # Генерация бота-противника
        bot_level = random.randint(max(1, user.data["level"]-2), user.data["level"]+2)
        bot_weapon = random.choice(list(items.keys()) + list(limited_items.keys()))
        
        player_damage = 0
        if user.data["equipped_weapon"]:
            weapon = items.get(user.data["equipped_weapon"], limited_items.get(user.data["equipped_weapon"]))
            if weapon and "damage" in weapon:
                player_damage = weapon["damage"]
        
        player_defense = 0
        if user.data["equipped_shield"]:
            shield = items.get(user.data["equipped_shield"], limited_items.get(user.data["equipped_shield"]))
            if shield and "defense" in shield:
                player_defense = shield["defense"]
        
        player_power = player_damage + user.data["level"] * 2 - bot_level
        bot_power = random.randint(5, 15) * bot_level - player_defense
        
        if player_power > bot_power:
            reward = 100
            user.data["money"] += reward
            user.data["wins"] += 1
            user.data["exp"] += 30
            user.save()
            result_text = f"⚔ Победа! Вы победили бота уровня {bot_level}!\n💰 Награда: {reward} монет\n✨ Опыт: +30"
        else:
            user.data["losses"] += 1
            user.data["exp"] += 10
            user.save()
            result_text = f"💀 Поражение! Бот уровня {bot_level} оказался сильнее.\n✨ Утешительный опыт: +10"
        
        if check_level_up(user_id):
            user = User(user_id)
            result_text += f"\n🎉 Новый уровень: {user.data['level']}!"
        
        bot.send_message(call.message.chat.id, result_text)
    
    # Дуэль с игроком
    elif call.data == "player_duel":
        bot.send_message(call.message.chat.id, "⚔ Для дуэли с игроком, ответьте на его сообщение командой /duel")
    
    # Админ-колбэки
    elif call.data == "admin_stats":
        if user_id != ADMIN_ID: return
        total_users = len(users)
        total_money = sum(u["money"] for u in users.values())
        total_duels = sum(u["wins"] + u["losses"] for u in users.values())
        
        stats = f"""
📊 *СТАТИСТИКА БОТА*

👥 Пользователей: {total_users}
💰 Всего монет в обороте: {total_money}
⚔ Всего дуэлей: {total_duels}
🎁 Лимитированных предметов: {len(limited_items)}
        """
        bot.send_message(call.message.chat.id, stats, parse_mode="Markdown")
    
    elif call.data == "admin_give_money":
        if user_id != ADMIN_ID: return
        bot.send_message(call.message.chat.id, "💰 Введите команду: /give_money [ID] [сумма]")
    
    elif call.data == "admin_broadcast":
        if user_id != ADMIN_ID: return
        bot.send_message(call.message.chat.id, "📢 Введите команду: /broadcast [текст рассылки]")

# Админ команды
@bot.message_handler(commands=['give_money'])
def admin_give_money_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        amount = int(parts[2])
        
        target = User(target_id)
        target.data["money"] += amount
        target.save()
        
        bot.send_message(message.chat.id, f"✅ Выдано {amount} монет игроку {target_id}")
    except:
        bot.send_message(message.chat.id, "❌ Формат: /give_money [ID] [сумма]")

@bot.message_handler(commands=['give_item'])
def admin_give_item(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        item_key = parts[2]
        
        target = User(target_id)
        target.data["inventory"].append(item_key)
        target.save()
        
        item_name = items.get(item_key, limited_items.get(item_key, {}))
        bot.send_message(message.chat.id, f"✅ Предмет {item_name.get('name', item_key)} выдан игроку {target_id}")
    except:
        bot.send_message(message.chat.id, "❌ Формат: /give_item [ID] [item_key]")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text.replace('/broadcast', '', 1).strip()
    if not text:
        bot.send_message(message.chat.id, "❌ Введите текст рассылки!")
        return
    
    success = 0
    for user_id in users:
        try:
            bot.send_message(user_id, f"📢 *Рассылка:*\n{text}", parse_mode="Markdown")
            success += 1
        except:
            pass
    
    bot.send_message(message.chat.id, f"✅ Рассылка отправлена {success} пользователям!")

@bot.message_handler(commands=['user_info'])
def admin_user_info(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        user_id = int(message.text.split()[1])
        user = User(user_id)
        u = user.data
        
        info = f"""
👤 *Информация об игроке {user_id}:*
Имя: {u['username']}
Уровень: {u['level']}
Баланс: {u['money']}
Побед: {u['wins']}
Поражений: {u['losses']}
Предметов: {len(u['inventory'])}
        """
        bot.send_message(message.chat.id, info, parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ Формат: /user_info [ID]")

@bot.message_handler(commands=['add_limited'])
def admin_add_limited(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        key = parts[1]
        name = parts[2]
        total = int(parts[3])
        price = int(parts[4])
        item_type = parts[5]
        
        item_data = {
            "name": name,
            "total": total,
            "remaining": total,
            "price": price,
            "type": item_type
        }
        
        if item_type == "weapon":
            item_data["damage"] = int(parts[6])
        elif item_type == "shield":
            item_data["defense"] = int(parts[6])
        elif item_type == "potion":
            item_data["heal"] = int(parts[6])
        
        limited_items[key] = item_data
        save_json(LIMITED_FILE, limited_items)
        
        bot.send_message(message.chat.id, f"✅ Лимитированный предмет '{name}' добавлен!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}\nФормат: /add_limited [key] [name] [total] [price] [type] [value]")

# Обработка дуэли
@bot.message_handler(commands=['duel'])
def duel_player(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Ответьте на сообщение игрока, с которым хотите драться!")
        return
    
    challenger_id = message.from_user.id
    opponent_id = message.reply_to_message.from_user.id
    
    if challenger_id == opponent_id:
        bot.send_message(message.chat.id, "❌ Нельзя драться с самим собой!")
        return
    
    challenger = User(challenger_id)
    opponent = User(opponent_id)
    
    if challenger.data["money"] < 50:
        bot.send_message(message.chat.id, "❌ У вас недостаточно монет для дуэли!")
        return
    
    if opponent.data["money"] < 50:
        bot.send_message(message.chat.id, "❌ У противника недостаточно монет для дуэли!")
        return
    
    # Снимаем ставку
    challenger.data["money"] -= 50
    opponent.data["money"] -= 50
    
    # Расчёт силы
    def get_power(user_data):
        power = user_data["level"] * 3
        if user_data["equipped_weapon"]:
            weapon = items.get(user_data["equipped_weapon"], limited_items.get(user_data["equipped_weapon"]))
            if weapon and "damage" in weapon:
                power += weapon["damage"]
        return power
    
    def get_defense(user_data):
        defense = 0
        if user_data["equipped_shield"]:
            shield = items.get(user_data["equipped_shield"], limited_items.get(user_data["equipped_shield"]))
            if shield and "defense" in shield:
                defense += shield["defense"]
        return defense
    
    ch_power = get_power(challenger.data) + random.randint(-10, 10)
    ch_total = ch_power - get_defense(opponent.data)
    
    op_power = get_power(opponent.data) + random.randint(-10, 10)
    op_total = op_power - get_defense(challenger.data)
    
    if ch_total > op_total:
        winner = challenger
        loser = opponent
        winner_name = message.from_user.first_name
        loser_name = message.reply_to_message.from_user.first_name
    else:
        winner = opponent
        loser = challenger
        winner_name = message.reply_to_message.from_user.first_name
        loser_name = message.from_user.first_name
    
    winner.data["money"] += 100
    winner.data["wins"] += 1
    winner.data["exp"] += 50
    
    loser.data["losses"] += 1
    loser.data["exp"] += 25
    
    winner.save()
    loser.save()
    
    result = f"""
⚔ *ДУЭЛЬ ЗАВЕРШЕНА!*

Победитель: {winner_name} 🏆
Сила: {ch_power if winner == challenger else op_power}

Проигравший: {loser_name} 💀
Сила: {op_power if winner == challenger else ch_power}

💰 Приз: 100 монет!
✨ Опыт: +50 победителю, +25 проигравшему
    """
    
    bot.send_message(message.chat.id, result, parse_mode="Markdown")
    
    if check_level_up(winner_id := (challenger_id if winner == challenger else opponent_id)):
        winner = User(winner_id)
        bot.send_message(message.chat.id, f"🎉 {winner_name} достиг уровня {winner.data['level']}!")

# Запуск бота
print("⚔ ДУЭЛЬ БОТ запущен!")
print(f"Админ ID: {ADMIN_ID}")
print("Бот готов к битвам!")

if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)
