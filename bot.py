import telebot
from telebot import types
import json
import random
import time
import threading
from datetime import datetime, timedelta
import math
import re

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = '8670879387:AAGz1v65wqhThDmwGNzCaEY9SY24XDJYLFE'
ADMIN_ID = 5356400377
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ==================== ФАЙЛЫ ДАННЫХ ====================
DATA_FILES = {
    'users': 'users.json',
    'items': 'items.json',
    'limited': 'limited_items.json',
    'duels': 'active_duels.json',
    'clans': 'clans.json',
    'market': 'market.json',
    'achievements': 'achievements.json',
    'quests': 'quests.json',
    'reports': 'reports.json'
}

def load_json(filename, default=None):
    if default is None: default = {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: 
        save_json(filename, default)
        return default

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==================== ИНИЦИАЛИЗАЦИЯ ====================
ITEMS = {
    "wood_sword": {"n":"🗡 Деревянный меч","d":5,"p":100,"t":"weapon","r":"common","lvl":1},
    "stone_sword": {"n":"🗿 Каменный меч","d":8,"p":200,"t":"weapon","r":"common","lvl":3},
    "iron_sword": {"n":"⚔ Железный меч","d":12,"p":500,"t":"weapon","r":"uncommon","lvl":5},
    "steel_sword": {"n":"🔪 Стальной меч","d":18,"p":1200,"t":"weapon","r":"uncommon","lvl":10},
    "mythril_sword": {"n":"✨ Мифриловый меч","d":25,"p":3000,"t":"weapon","r":"rare","lvl":15},
    "dragon_sword": {"n":"🐉 Драконий меч","d":35,"p":7000,"t":"weapon","r":"epic","lvl":20},
    "excalibur": {"n":"⚡ Экскалибур","d":50,"p":15000,"t":"weapon","r":"legendary","lvl":30},
    "chaos_blade": {"n":"🌑 Клинок Хаоса","d":75,"p":30000,"t":"weapon","r":"mythic","lvl":40},
    "wood_shield": {"n":"🛡 Деревянный щит","df":5,"p":150,"t":"shield","r":"common","lvl":1},
    "iron_shield": {"n":"🛡 Железный щит","df":12,"p":600,"t":"shield","r":"uncommon","lvl":5},
    "dragon_shield": {"n":"🐉 Щит Дракона","df":25,"p":5000,"t":"shield","r":"epic","lvl":20},
    "aegis": {"n":"💫 Эгида","df":40,"p":20000,"t":"shield","r":"legendary","lvl":35},
    "lth_armor": {"n":"🧥 Кож. броня","df":3,"hp":10,"p":120,"t":"armor","r":"common","lvl":1},
    "iron_armor": {"n":"🛡 Жел. броня","df":8,"hp":25,"p":800,"t":"armor","r":"uncommon","lvl":8},
    "dragon_armor": {"n":"🐉 Драк. броня","df":20,"hp":60,"p":8000,"t":"armor","r":"epic","lvl":25},
    "hp_pot": {"n":"🧪 Зелье HP","heal":25,"p":50,"t":"potion","r":"common","lvl":1},
    "big_hp": {"n":"🧪 Большое зелье","heal":60,"p":150,"t":"potion","r":"uncommon","lvl":5},
    "elixir": {"n":"💊 Эликсир","heal":150,"p":500,"t":"potion","r":"rare","lvl":15},
    "str_amulet": {"n":"📿 Амулет Силы","db":15,"p":3500,"t":"accessory","r":"epic","lvl":18},
    "lucky_charm": {"n":"🍀 Талисман Удачи","cc":15,"p":3000,"t":"accessory","r":"rare","lvl":15},
    "speed_boots": {"n":"👢 Сапоги Скорости","spd":10,"p":2500,"t":"boots","r":"uncommon","lvl":12},
}

LIMITED = {
    "thunderfury": {"n":"⚡ Гроза Богов","d":100,"total":3,"rem":3,"p":50000,"t":"weapon","r":"divine","spec":"chain"},
    "phoenix_armor": {"n":"🦅 Броня Феникса","df":80,"hp":200,"total":5,"rem":5,"p":75000,"t":"armor","r":"divine","spec":"rebirth"},
    "invis_cloak": {"n":"👻 Плащ-невидимка","df":30,"dodge":25,"total":7,"rem":7,"p":45000,"t":"armor","r":"mythic","spec":"invis"},
    "god_ring": {"n":"💍 Кольцо Бога","db":30,"cc":25,"total":3,"rem":3,"p":100000,"t":"accessory","r":"divine","spec":"all"}
}

ACHIEVEMENTS_LIST = {
    "first_blood": {"n":"🩸 Первая кровь","desc":"Выиграйте 1 дуэль","rw":200},
    "warrior": {"n":"⚔ Воин","desc":"Выиграйте 10 дуэлей","rw":500},
    "veteran": {"n":"🎖 Ветеран","desc":"Выиграйте 50 дуэлей","rw":2000},
    "legend": {"n":"👑 Легенда","desc":"Выиграйте 100 дуэлей","rw":5000},
    "rich": {"n":"💰 Богач","desc":"Накопите 10000 монет","rw":1000},
    "millionaire": {"n":"💎 Миллионер","desc":"Накопите 100000 монет","rw":10000},
    "collector": {"n":"🎒 Коллекционер","desc":"20 предметов","rw":1500},
    "perfect": {"n":"✨ Идеальная победа","desc":"Победите без потерь","rw":1000},
    "streak3": {"n":"🔥 Серия 3","desc":"3 победы подряд","rw":300},
    "streak5": {"n":"🔥🔥 Серия 5","desc":"5 побед подряд","rw":800},
    "streak10": {"n":"💀 Серия 10","desc":"10 побед подряд","rw":3000},
}

DAILY_QUESTS = [
    {"n":"Дуэлянт","desc":"3 дуэли","tg":3,"t":"duels","rm":300,"re":50},
    {"n":"Шопоголик","desc":"Купите 2 предмета","tg":2,"t":"buy","rm":250,"re":40},
    {"n":"Тренер","desc":"Тренировка 5 раз","tg":5,"t":"train","rm":200,"re":60},
    {"n":"Исследователь","desc":"Исследуйте 3 раза","tg":3,"t":"explore","rm":350,"re":45},
    {"n":"Победитель","desc":"2 победы в дуэлях","tg":2,"t":"wins","rm":400,"re":70},
    {"n":"Богатей","desc":"Заработайте 500 монет","tg":500,"t":"earn","rm":200,"re":30},
    {"n":"Целитель","desc":"Исп. 3 зелья","tg":3,"t":"potion","rm":150,"re":35},
]

# Загрузка всех данных
users = load_json(DATA_FILES['users'])
items = load_json(DATA_FILES['items'], ITEMS)
limited = load_json(DATA_FILES['limited'], LIMITED)
duels = load_json(DATA_FILES['duels'])
clans = load_json(DATA_FILES['clans'])
market = load_json(DATA_FILES['market'])
achievements = load_json(DATA_FILES['achievements'])
quests = load_json(DATA_FILES['quests'])
reports = load_json(DATA_FILES['reports'])

# ==================== КЛАСС USER ====================
class User:
    def __init__(self, uid, uname="", fname=""):
        uid = str(uid)
        if uid not in users:
            users[uid] = {
                "uname": uname or f"user_{uid}",
                "fname": fname or "Игрок",
                "money": 500,
                "lvl": 1, "exp": 0,
                "hp": 100, "max_hp": 100,
                "wins": 0, "losses": 0, "draws": 0,
                "winstreak": 0, "beststreak": 0,
                "inv": [],
                "eq_w": None, "eq_s": None, "eq_a": None, "eq_acc": None, "eq_b": None,
                "last_daily": None, "last_work": None,
                "title": "Новичок", "titles": ["Новичок"],
                "ach": [], "aq": {}, "cq": 0,
                "clan": None, "twins": 0,
                "tdmg": 0, "tdmgtaken": 0,
                "crits": 0, "items_used": 0,
                "reg_date": datetime.now().isoformat(),
                "settings": {"notif": True, "duel_req": True, "effects": True},
                "banned": False, "ban_reason": "",
                "muted": False, "reports": 0
            }
            save_json(DATA_FILES['users'], users)
        self.id = uid
    
    @property
    def data(self): return users[self.id]
    def save(self): save_json(DATA_FILES['users'], users)

# ==================== ФУНКЦИИ УРОВНЕЙ ====================
def get_exp(level): return int(100 * (1.5 ** (level - 1)))

def check_lvl(uid):
    u = User(uid)
    while u.data["exp"] >= get_exp(u.data["lvl"]):
        u.data["exp"] -= get_exp(u.data["lvl"])
        u.data["lvl"] += 1
        u.data["max_hp"] = 100 + (u.data["lvl"] - 1) * 10
        u.data["hp"] = u.data["max_hp"]
        titles = [(1,"Новичок"),(5,"Боец"),(10,"Воитель"),(15,"Рыцарь"),(20,"Ветеран"),
                  (25,"Мастер"),(30,"Грандмастер"),(40,"Герой"),(50,"Легенда"),
                  (60,"Миф"),(75,"Полубог"),(100,"Бог")]
        for lvl, title in titles:
            if u.data["lvl"] >= lvl and title not in u.data["titles"]:
                u.data["titles"].append(title)
                u.data["title"] = title
    u.save()
    return u.data["lvl"]

# ==================== СТАТЫ ====================
def calc_stats(uid):
    u = User(uid)
    s = {"bd":u.data["lvl"]*2,"bonus_d":0,"df":0,"hp":u.data["hp"],"mhp":u.data["max_hp"],
         "cc":5,"cm":1.5,"spd":0,"dodge":3,"ls":0,"ref":0}
    for slot, it in [("eq_w",u.data["eq_w"]),("eq_s",u.data["eq_s"]),("eq_a",u.data["eq_a"]),
                      ("eq_acc",u.data["eq_acc"]),("eq_b",u.data["eq_b"])]:
        if it:
            item = items.get(it) or limited.get(it)
            if item:
                if "d" in item: s["bonus_d"] += item["d"]
                if "df" in item: s["df"] += item["df"]
                if "hp" in item: s["mhp"] += item["hp"]
                if "cc" in item: s["cc"] += item["cc"]
                if "db" in item: s["bonus_d"] += item["db"]
                if "spd" in item: s["spd"] += item["spd"]
                if "dodge" in item: s["dodge"] += item["dodge"]
    s["cc"] = min(s["cc"], 80)
    s["dodge"] = min(s["dodge"], 50)
    return s

# ==================== ГЛАВНОЕ МЕНЮ (4 КНОПКИ) ====================
def main_menu():
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    mk.add("⚔ Битва", "👤 Герой")
    mk.add("🏪 Рынок", "📜 Меню")
    return mk

# ==================== КОМАНДА START ====================
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    User(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    bot.send_message(msg.chat.id, f"""
<b>⚔ ДУЭЛЬ БОТ v4.0</b>

Привет, <b>{msg.from_user.first_name}</b>!

🎯 <b>Главное меню:</b>
⚔ Битва - дуэли, PvP, турниры
👤 Герой - профиль, инвентарь
🏪 Рынок - магазин, торговля
📜 Меню - кланы, квесты, рейтинг

💰 Баланс: <b>500 монет</b>
🎁 /daily - ежедневный бонус
📖 /help - все команды
""", reply_markup=main_menu())

# ==================== КНОПКА "⚔ БИТВА" ====================
@bot.message_handler(func=lambda m: m.text == "⚔ Битва")
def battle_menu(msg):
    mk = types.InlineKeyboardMarkup(row_width=1)
    mk.add(
        types.InlineKeyboardButton("⚡ Быстрая дуэль (50💰)", callback_data="b_quick"),
        types.InlineKeyboardButton("👤 PvP дуэль (100💰)", callback_data="b_pvp_info"),
        types.InlineKeyboardButton("🏆 Рейтинговая (200💰)", callback_data="b_ranked_info"),
        types.InlineKeyboardButton("💀 Хардкор (500💰)", callback_data="b_hc_info"),
        types.InlineKeyboardButton("🎯 Дружеская (без ставок)", callback_data="b_friendly_info"),
        types.InlineKeyboardButton("🔥 На выживание (300💰)", callback_data="b_surv_info"),
        types.InlineKeyboardButton("⚔ Командная 2x2", callback_data="b_team_info"),
        types.InlineKeyboardButton("📊 Мои дуэли", callback_data="b_stats"),
        types.InlineKeyboardButton("« Назад", callback_data="main_menu")
    )
    bot.send_message(msg.chat.id, """
<b>⚔ АРЕНА ДУЭЛЕЙ</b>

Выберите режим:

⚡ <b>Быстрая</b> - бой с ботом
👤 <b>PvP</b> - дуэль с игроком
🏆 <b>Рейтинговая</b> - за рейтинг
💀 <b>Хардкор</b> - высокие ставки
🎯 <b>Дружеская</b> - без потерь
🔥 <b>Выживание</b> - до конца
⚔ <b>Командная</b> - 2 на 2
""", reply_markup=mk)

# ==================== КНОПКА "👤 ГЕРОЙ" ====================
@bot.message_handler(func=lambda m: m.text == "👤 Герой")
def hero_menu(msg):
    uid = msg.from_user.id
    u = User(uid)
    s = calc_stats(uid)
    
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("📊 Характеристики", callback_data="h_stats"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="h_inv"),
        types.InlineKeyboardButton("⚔ Экипировка", callback_data="h_eq"),
        types.InlineKeyboardButton("🏅 Достижения", callback_data="h_ach"),
        types.InlineKeyboardButton("💊 Лечение", callback_data="h_heal"),
        types.InlineKeyboardButton("⚙ Настройки", callback_data="h_settings"),
        types.InlineKeyboardButton("« Назад", callback_data="main_menu")
    )
    
    eq = []
    if u.data["eq_w"]:
        w = items.get(u.data["eq_w"]) or limited.get(u.data["eq_w"])
        eq.append(f"⚔ {w['n']}" if w else "")
    if u.data["eq_s"]:
        sh = items.get(u.data["eq_s"]) or limited.get(u.data["eq_s"])
        eq.append(f"🛡 {sh['n']}" if sh else "")
    if u.data["eq_a"]:
        a = items.get(u.data["eq_a"]) or limited.get(u.data["eq_a"])
        eq.append(f"🧥 {a['n']}" if a else "")
    
    wr = (u.data["wins"]/(u.data["wins"]+u.data["losses"])*100) if (u.data["wins"]+u.data["losses"])>0 else 0
    
    bot.send_message(msg.chat.id, f"""
<b>👤 {u.data['fname']}</b> | {u.data['title']}
🆔 <code>{uid}</code>
⭐ Ур.{u.data['lvl']} | ✨ {u.data['exp']}/{get_exp(u.data['lvl'])}
❤ {u.data['hp']}/{u.data['max_hp']}

⚔ Урон: {s['bd']+s['bonus_d']} | 🛡 Защита: {s['df']}
💥 Крит: {s['cc']}% | 🌀 Уклон: {s['dodge']}%

🏆 {u.data['wins']}W / 💀 {u.data['losses']}L
📊 Винрейт: {wr:.1f}% | 🔥 Серия: {u.data['winstreak']}

💰 {u.data['money']} монет
🎒 Предметов: {len(u.data['inv'])}
🛡 Клан: {u.data.get('clan') or 'Нет'}

<b>Экипировка:</b>
{chr(10).join(eq) if eq else 'Пусто'}
""", reply_markup=mk)

# ==================== КНОПКА "🏪 РЫНОК" ====================
@bot.message_handler(func=lambda m: m.text == "🏪 Рынок")
def market_menu(msg):
    mk = types.InlineKeyboardMarkup(row_width=1)
    mk.add(
        types.InlineKeyboardButton("🛒 Магазин оружия", callback_data="m_shop_w"),
        types.InlineKeyboardButton("🛡 Магазин защиты", callback_data="m_shop_d"),
        types.InlineKeyboardButton("🧪 Зелья и аксессуары", callback_data="m_shop_a"),
        types.InlineKeyboardButton("💎 Лимит. предметы", callback_data="m_limited"),
        types.InlineKeyboardButton("💱 Торговая площадка", callback_data="m_trade"),
        types.InlineKeyboardButton("💰 Продать предмет", callback_data="m_sell_info"),
        types.InlineKeyboardButton("« Назад", callback_data="main_menu")
    )
    bot.send_message(msg.chat.id, """
<b>🏪 РЫНОК</b>

🛒 <b>Магазины</b> - покупка снаряжения
💎 <b>Лимитированные</b> - редкие предметы
💱 <b>Торговая площадка</b> - обмен с игроками
💰 <b>Продажа</b> - продать предметы за 50% цены
""", reply_markup=mk)

# ==================== КНОПКА "📜 МЕНЮ" ====================
@bot.message_handler(func=lambda m: m.text == "📜 Меню")
def other_menu(msg):
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("💰 Работа", callback_data="o_work"),
        types.InlineKeyboardButton("🎁 Бонус", callback_data="o_daily"),
        types.InlineKeyboardButton("📊 Топ игроков", callback_data="o_top"),
        types.InlineKeyboardButton("🛡 Кланы", callback_data="o_clan"),
        types.InlineKeyboardButton("📜 Квесты", callback_data="o_quests"),
        types.InlineKeyboardButton("🎮 РП команды", callback_data="o_rp"),
        types.InlineKeyboardButton("🏆 Турниры", callback_data="o_tourn"),
        types.InlineKeyboardButton("📖 Помощь", callback_data="o_help"),
        types.InlineKeyboardButton("« Назад", callback_data="main_menu")
    )
    bot.send_message(msg.chat.id, """
<b>📜 ДОПОЛНИТЕЛЬНОЕ МЕНЮ</b>

💰 Работа - заработок монет
🎁 Бонус - ежедневная награда
📊 Топ - рейтинг игроков
🛡 Кланы - клановая система
📜 Квесты - ежедневные задания
🎮 РП - ролевые команды
🏆 Турниры - соревнования
📖 Помощь - список команд
""", reply_markup=mk)

# ==================== CALLBACK ОБРАБОТЧИК ====================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = str(call.from_user.id)
    User(uid)
    data = call.data
    
    try:
        # Главное меню
        if data == "main_menu":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "📋 Главное меню", reply_markup=main_menu())
        
        # ==================== БИТВЫ ====================
        elif data == "b_quick":
            quick_duel(call)
        
        elif data == "b_pvp_info":
            bot.answer_callback_query(call.id)
            bot.edit_message_text("""
<b>👤 PvP ДУЭЛЬ</b>

Для дуэли с игроком:
1. Ответьте на сообщение соперника
2. Используйте /duel

Ставка: 100💰 с каждого
Победитель забирает всё!
""", call.message.chat.id, call.message.message_id,
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("« Назад", callback_data="battle_menu_back")))
        
        elif data == "battle_menu_back":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            battle_menu(call.message)
        
        elif data in ["b_ranked_info", "b_hc_info", "b_friendly_info", "b_surv_info"]:
            info_texts = {
                "b_ranked_info": ("🏆 Рейтинговая дуэль", "Ставка: 200💰\nВлияет на рейтинг\nИспользуйте /ranked"),
                "b_hc_info": ("💀 Хардкор дуэль", "Ставка: 500💰\nВысокий риск!\nИспользуйте /hardcore"),
                "b_friendly_info": ("🎯 Дружеская дуэль", "Без ставок\nБез потерь\nИспользуйте /friendly"),
                "b_surv_info": ("🔥 На выживание", "Ставка: 300💰\nБой до 0 HP\nИспользуйте /survival")
            }
            title, text = info_texts[data]
            bot.answer_callback_query(call.id)
            bot.edit_message_text(f"<b>{title}</b>\n\n{text}", 
                call.message.chat.id, call.message.message_id,
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("« Назад", callback_data="battle_menu_back")))
        
        elif data == "b_stats":
            u = User(uid)
            bot.answer_callback_query(call.id)
            bot.edit_message_text(f"""
<b>📊 СТАТИСТИКА ДУЭЛЕЙ</b>

🏆 Побед: {u.data['wins']}
💀 Поражений: {u.data['losses']}
🤝 Ничьих: {u.data['draws']}
🔥 Лучшая серия: {u.data['beststreak']}
💥 Всего урона: {u.data['tdmg']}
🛡 Получено урона: {u.data['tdmgtaken']}
⚡ Крит. ударов: {u.data['crits']}
""", call.message.chat.id, call.message.message_id,
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("« Назад", callback_data="battle_menu_back")))
        
        # ==================== ГЕРОЙ ====================
        elif data == "h_stats":
            u = User(uid)
            s = calc_stats(uid)
            bot.answer_callback_query(call.id)
            bot.edit_message_text(f"""
<b>📊 ХАРАКТЕРИСТИКИ</b>

⚔ Базовый урон: {s['bd']}
➕ Бонус урона: {s['bonus_d']}
💥 Общий урон: {s['bd']+s['bonus_d']}
🛡 Защита: {s['df']}
💥 Крит: {s['cc']}% (x{s['cm']})
🌀 Уклонение: {s['dodge']}%
⚡ Скорость: {s['spd']}
❤ HP: {u.data['hp']}/{s['mhp']}
""", call.message.chat.id, call.message.message_id,
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("« Назад", callback_data="hero_menu_back")))
        
        elif data == "hero_menu_back":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            hero_menu(call.message)
        
        elif data == "h_inv":
            show_inventory(call)
        
        elif data == "h_eq":
            show_equipment(call)
        
        elif data == "h_ach":
            show_achievements(call)
        
        elif data == "h_heal":
            heal_player(call)
        
        elif data == "h_settings":
            show_settings(call)
        
        # ==================== РЫНОК ====================
        elif data.startswith("m_shop_"):
            cat = data.split("_")[2]
            show_shop(call, cat)
        
        elif data == "m_limited":
            show_limited(call)
        
        elif data == "m_trade":
            show_trade(call)
        
        elif data == "market_menu_back":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            market_menu(call.message)
        
        # ==================== ДРУГОЕ ====================
        elif data == "o_work":
            do_work(call)
        
        elif data == "o_daily":
            do_daily(call)
        
        elif data == "o_top":
            show_top_menu(call)
        
        elif data == "o_clan":
            show_clan_menu(call)
        
        elif data == "o_quests":
            show_quests(call)
        
        elif data == "o_rp":
            show_rp(call)
        
        elif data == "o_tourn":
            show_tournaments(call)
        
        elif data == "o_help":
            show_help(call)
        
        elif data == "other_menu_back":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            other_menu(call.message)
        
        # Покупка предмета
        elif data.startswith("buy_"):
            item_key = data[4:]
            buy_item(call, item_key)
        
        # Покупка лимитированного
        elif data.startswith("buyl_"):
            item_key = data[5:]
            buy_limited(call, item_key)
        
        # Экипировка
        elif data.startswith("eq_"):
            item_key = data[3:]
            equip_item(call, item_key)
        
        # Использование зелья
        elif data.startswith("use_"):
            item_key = data[4:]
            use_potion(call, item_key)
        
        # Продажа предмета
        elif data.startswith("sell_"):
            item_key = data[5:]
            sell_item(call, item_key)
        
        # Топ категории
        elif data.startswith("top_"):
            show_top(call, data[4:])
        
        # Клан действия
        elif data.startswith("clan_"):
            handle_clan(call, data[5:])
        
        # Настройки
        elif data.startswith("set_"):
            handle_settings(call, data[4:])
        
        else:
            bot.answer_callback_query(call.id, "⚠ Неизвестное действие")
    
    except Exception as e:
        print(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")

# ==================== ФУНКЦИИ ДУЭЛЕЙ ====================
def quick_duel(call):
    uid = str(call.from_user.id)
    u = User(uid)
    
    if u.data["money"] < 50:
        bot.answer_callback_query(call.id, "❌ Нужно 50💰")
        return
    
    if u.data.get("banned"):
        bot.answer_callback_query(call.id, "❌ Вы забанены!")
        return
    
    u.data["money"] -= 50
    u.save()
    
    # Создание бота
    bot_lvl = random.randint(max(1, u.data["lvl"]-3), u.data["lvl"]+3)
    bot_id = f"bot_{random.randint(10000,99999)}"
    users[bot_id] = {
        "uname": f"Bot_{bot_lvl}", "fname": f"Бот Ур.{bot_lvl}",
        "money": 0, "lvl": bot_lvl, "exp": 0,
        "hp": 100+bot_lvl*10, "max_hp": 100+bot_lvl*10,
        "wins": 0, "losses": 0,
        "inv": [], "eq_w": random.choice([k for k in items if items[k]["t"]=="weapon"]),
        "eq_s": None, "eq_a": None, "eq_acc": None, "eq_b": None,
        "banned": False
    }
    
    result = execute_duel(uid, bot_id)
    
    # Удаление бота
    if bot_id in users: del users[bot_id]
    
    u = User(uid)
    if result["winner"] == uid:
        u.data["money"] += 100
        u.data["wins"] += 1
        u.data["winstreak"] += 1
        if u.data["winstreak"] > u.data["beststreak"]:
            u.data["beststreak"] = u.data["winstreak"]
        u.data["exp"] += 30
        check_achievements(uid)
    else:
        u.data["losses"] += 1
        u.data["winstreak"] = 0
        u.data["exp"] += 10
    
    u.data["hp"] = min(u.data["max_hp"], u.data["hp"] + 20)
    u.save()
    check_lvl(uid)
    check_quests(uid, "duels", 1)
    if result["winner"] == uid: check_quests(uid, "wins", 1)
    
    bot.answer_callback_query(call.id, f"{'✅ Победа!' if result['winner']==uid else '💀 Поражение'}")
    
    u = User(uid)
    bot.edit_message_text(f"""
<b>{'🏆 ПОБЕДА!' if result['winner']==uid else '💀 ПОРАЖЕНИЕ'}</b>

Противник: Бот Ур.{bot_lvl}
Ходов: {result['turns']}
Урон: {result['dmg_dealt']}

{'💰 +100 монет' if result['winner']==uid else '💰 -50 монет'}
✨ +{30 if result['winner']==uid else 10} опыта
🔥 Серия: {u.data['winstreak']}
""", call.message.chat.id, call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("⚔ Ещё дуэль", callback_data="b_quick"),
            types.InlineKeyboardButton("« Назад", callback_data="battle_menu_back")))

def execute_duel(p1_id, p2_id):
    s1 = calc_stats(p1_id)
    s2 = calc_stats(p2_id)
    
    hp1 = s1["mhp"]
    hp2 = s2["mhp"]
    
    turns = 0
    dmg_dealt = 0
    
    # Определение очерёдности
    first, second = (p1_id, p2_id) if s1["spd"] >= s2["spd"] else (p2_id, p1_id)
    f_hp, s_hp = (hp1, hp2) if first == p1_id else (hp2, hp1)
    f_stats, s_stats = (s1, s2) if first == p1_id else (s2, s1)
    
    while turns < 30 and f_hp > 0 and s_hp > 0:
        turns += 1
        dmg = f_stats["bd"] + f_stats["bonus_d"] + random.randint(-5, 5)
        
        if random.random()*100 < f_stats["cc"]:
            dmg = int(dmg * f_stats["cm"])
        
        if random.random()*100 < s_stats["dodge"]:
            dmg = 0
        
        dmg = max(0, dmg - s_stats["df"])
        s_hp -= dmg
        dmg_dealt += dmg
        
        if dmg > 0 and f_stats.get("ls", 0) > 0:
            f_hp = min(f_stats["mhp"], f_hp + int(dmg * f_stats["ls"]/100))
        
        if s_hp <= 0: break
        
        # Смена хода
        first, second = second, first
        f_hp, s_hp = s_hp, f_hp
        f_stats, s_stats = s_stats, f_stats
    
    winner = p1_id if (first == p1_id and s_hp <= 0) or (first == p2_id and f_hp <= 0) else None
    if f_hp <= 0 and s_hp <= 0: winner = None
    
    return {"winner": winner, "turns": turns, "dmg_dealt": dmg_dealt}

# ==================== ИНВЕНТАРЬ ====================
def show_inventory(call):
    uid = str(call.from_user.id)
    u = User(uid)
    
    if not u.data["inv"]:
        bot.answer_callback_query(call.id, "🎒 Инвентарь пуст")
        return
    
    # Группировка
    cnt = {}
    for it in u.data["inv"]:
        cnt[it] = cnt.get(it, 0) + 1
    
    txt = "<b>🎒 ИНВЕНТАРЬ</b>\n\n"
    mk = types.InlineKeyboardMarkup(row_width=2)
    
    for i, (k, c) in enumerate(cnt.items(), 1):
        item = items.get(k) or limited.get(k)
        if not item: continue
        rar = {"common":"⬜","uncommon":"🟩","rare":"🟦","epic":"🟪","legendary":"🟧","mythic":"🟥","divine":"💛"}
        txt += f"{i}. {rar.get(item.get('r','common'),'⬜')} {item['n']} x{c}\n"
        
        if item["t"] in ["weapon","shield","armor","accessory","boots"]:
            mk.add(types.InlineKeyboardButton(f"Экип: {item['n'][:15]}", callback_data=f"eq_{k}"))
        elif item["t"] == "potion":
            mk.add(types.InlineKeyboardButton(f"Исп: {item['n'][:15]}", callback_data=f"use_{k}"))
        mk.add(types.InlineKeyboardButton(f"Продать", callback_data=f"sell_{k}"))
    
    mk.add(types.InlineKeyboardButton("« Назад", callback_data="hero_menu_back"))
    
    bot.answer_callback_query(call.id)
    if call.message.text != txt:
        bot.edit_message_text(txt[:4000], call.message.chat.id, call.message.message_id, reply_markup=mk)

def equip_item(call, key):
    uid = str(call.from_user.id)
    u = User(uid)
    
    if key not in u.data["inv"]:
        bot.answer_callback_query(call.id, "❌ Нет в инвентаре")
        return
    
    item = items.get(key) or limited.get(key)
    if not item:
        bot.answer_callback_query(call.id, "❌ Предмет не найден")
        return
    
    slot_map = {"weapon":"eq_w", "shield":"eq_s", "armor":"eq_a", "accessory":"eq_acc", "boots":"eq_b"}
    slot = slot_map.get(item["t"])
    
    if slot:
        u.data[slot] = key
        u.save()
        bot.answer_callback_query(call.id, f"✅ {item['n']} экипирован!")
        show_inventory(call)
    else:
        bot.answer_callback_query(call.id, "❌ Нельзя экипировать")

def use_potion(call, key):
    uid = str(call.from_user.id)
    u = User(uid)
    
    if key not in u.data["inv"]:
        bot.answer_callback_query(call.id, "❌ Нет в инвентаре")
        return
    
    item = items.get(key) or limited.get(key)
    if not item or item["t"] != "potion":
        bot.answer_callback_query(call.id, "❌ Не зелье")
        return
    
    if u.data["hp"] >= u.data["max_hp"]:
        bot.answer_callback_query(call.id, "❤ Полное HP!")
        return
    
    heal = item.get("heal", 25)
    u.data["hp"] = min(u.data["max_hp"], u.data["hp"] + heal)
    u.data["inv"].remove(key)
    u.data["items_used"] += 1
    u.save()
    
    check_quests(uid, "potion", 1)
    bot.answer_callback_query(call.id, f"💚 +{heal} HP")
    show_inventory(call)

def sell_item(call, key):
    uid = str(call.from_user.id)
    u = User(uid)
    
    if key not in u.data["inv"]:
        bot.answer_callback_query(call.id, "❌ Нет в инвентаре")
        return
    
    item = items.get(key) or limited.get(key)
    if not item:
        bot.answer_callback_query(call.id, "❌ Ошибка")
        return
    
    price = item.get("p", 100) // 2
    u.data["inv"].remove(key)
    u.data["money"] += price
    u.save()
    
    bot.answer_callback_query(call.id, f"💰 Продано за {price} монет")
    show_inventory(call)

# ==================== МАГАЗИН ====================
def show_shop(call, cat):
    cat_map = {"w":"weapon", "d":"shield,armor", "a":"potion,accessory,boots"}
    cat_types = cat_map.get(cat, "weapon").split(",")
    
    txt = f"<b>🏪 МАГАЗИН</b>\n\n"
    mk = types.InlineKeyboardMarkup(row_width=1)
    
    for k, item in sorted(items.items(), key=lambda x: x[1].get("p",0)):
        if item["t"] in cat_types:
            txt += f"• {item['n']} - {item['p']}💰\n"
            txt += f"  Ур.{item.get('lvl',1)} | "
            if "d" in item: txt += f"⚔{item['d']} "
            if "df" in item: txt += f"🛡{item['df']} "
            if "hp" in item: txt += f"❤{item['hp']} "
            txt += "\n"
            mk.add(types.InlineKeyboardButton(f"Купить: {item['n']} ({item['p']}💰)", callback_data=f"buy_{k}"))
    
    if len(txt) > 4000: txt = txt[:4000] + "..."
    mk.add(types.InlineKeyboardButton("« Назад", callback_data="market_menu_back"))
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=mk)

def show_limited(call):
    txt = "<b>💎 ЛИМИТИРОВАННЫЕ ПРЕДМЕТЫ</b>\n\n"
    mk = types.InlineKeyboardMarkup(row_width=1)
    
    for k, item in limited.items():
        if item["rem"] > 0:
            txt += f"<b>{item['n']}</b> [{item['rem']}/{item['total']}]\n"
            if "d" in item: txt += f"⚔ {item['d']} "
            if "df" in item: txt += f"🛡 {item['df']} "
            if "hp" in item: txt += f"❤ {item['hp']} "
            txt += f"\n💰 {item['p']} монет\n"
            if "spec" in item: txt += f"✨ {item['spec']}\n"
            txt += "\n"
            mk.add(types.InlineKeyboardButton(f"Купить {item['n']} - {item['p']}💰", callback_data=f"buyl_{k}"))
    
    if not mk.keyboard:
        txt += "Все предметы распроданы!"
    
    mk.add(types.InlineKeyboardButton("« Назад", callback_data="market_menu_back"))
    bot.answer_callback_query(call.id)
    bot.edit_message_text(txt[:4000], call.message.chat.id, call.message.message_id, reply_markup=mk)

def buy_item(call, key):
    uid = str(call.from_user.id)
    u = User(uid)
    item = items.get(key)
    
    if not item:
        bot.answer_callback_query(call.id, "❌ Не найдено")
        return
    
    if u.data["lvl"] < item.get("lvl", 1):
        bot.answer_callback_query(call.id, f"❌ Нужен {item.get('lvl',1)} ур.")
        return
    
    if u.data["money"] < item["p"]:
        bot.answer_callback_query(call.id, "❌ Мало денег")
        return
    
    u.data["money"] -= item["p"]
    u.data["inv"].append(key)
    u.save()
    
    check_quests(uid, "buy", 1)
    bot.answer_callback_query(call.id, f"✅ Куплено: {item['n']}")

def buy_limited(call, key):
    uid = str(call.from_user.id)
    u = User(uid)
    item = limited.get(key)
    
    if not item or item["rem"] <= 0:
        bot.answer_callback_query(call.id, "❌ Закончилось")
        return
    
    if u.data["money"] < item["p"]:
        bot.answer_callback_query(call.id, "❌ Мало денег")
        return
    
    u.data["money"] -= item["p"]
    u.data["inv"].append(key)
    item["rem"] -= 1
    u.save()
    save_json(DATA_FILES['limited'], limited)
    
    bot.answer_callback_query(call.id, f"💎 {item['n']} куплен!")
    show_limited(call)

# ==================== РАБОТА И БОНУСЫ ====================
def do_work(call):
    uid = str(call.from_user.id)
    u = User(uid)
    
    now = datetime.now()
    if u.data.get("last_work"):
        last = datetime.fromisoformat(u.data["last_work"])
        if (now - last) < timedelta(hours=1):
            mins = 60 - (now - last).seconds//60
            bot.answer_callback_query(call.id, f"⏰ Ждите {mins} мин.")
            return
    
    jobs = [("Охота", 50, 150), ("Защита", 60, 120), ("Сбор трав", 40, 100),
            ("Тренировка", 70, 160), ("Руины", 80, 200)]
    job = random.choice(jobs)
    reward = random.randint(job[1], job[2]) * u.data["lvl"]
    exp_r = random.randint(20, 50) * u.data["lvl"]
    
    u.data["money"] += reward
    u.data["exp"] += exp_r
    u.data["last_work"] = now.isoformat()
    u.save()
    
    check_quests(uid, "earn", reward)
    old_lvl = u.data["lvl"]
    check_lvl(uid)
    u = User(uid)
    
    txt = f"""
<b>⚒ РАБОТА: {job[0]}</b>

💰 +{reward} монет
✨ +{exp_r} опыта
"""
    if u.data["lvl"] > old_lvl: txt += f"\n🎉 УРОВЕНЬ {u.data['lvl']}!"
    
    bot.answer_callback_query(call.id, f"💰 +{reward} монет")
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("« Назад", callback_data="other_menu_back")))

def do_daily(call):
    uid = str(call.from_user.id)
    u = User(uid)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if u.data["last_daily"] == today:
        bot.answer_callback_query(call.id, "🎁 Уже получено!")
        return
    
    bonus = random.randint(100, 500)
    exp_b = random.randint(30, 100)
    
    u.data["money"] += bonus
    u.data["exp"] += exp_b
    u.data["last_daily"] = today
    u.save()
    
    old_lvl = u.data["lvl"]
    check_lvl(uid)
    u = User(uid)
    
    txt = f"""
<b>🎁 ЕЖЕДНЕВНЫЙ БОНУС</b>

💰 +{bonus} монет
✨ +{exp_b} опыта
"""
    if u.data["lvl"] > old_lvl: txt += f"\n🎉 УРОВЕНЬ {u.data['lvl']}!"
    
    bot.answer_callback_query(call.id, f"🎁 +{bonus}💰")
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("« Назад", callback_data="other_menu_back")))

# ==================== ДОСТИЖЕНИЯ ====================
def check_achievements(uid):
    u = User(uid)
    checks = {
        "first_blood": u.data["wins"] >= 1,
        "warrior": u.data["wins"] >= 10,
        "veteran": u.data["wins"] >= 50,
        "legend": u.data["wins"] >= 100,
        "rich": u.data["money"] >= 10000,
        "millionaire": u.data["money"] >= 100000,
        "streak3": u.data["winstreak"] >= 3,
        "streak5": u.data["winstreak"] >= 5,
        "streak10": u.data["winstreak"] >= 10,
    }
    
    for ach, cond in checks.items():
        if cond and ach not in u.data["ach"]:
            u.data["ach"].append(ach)
            u.data["money"] += ACHIEVEMENTS_LIST[ach]["rw"]
            u.data["exp"] += 50
    u.save()

def show_achievements(call):
    uid = str(call.from_user.id)
    u = User(uid)
    
    txt = f"<b>🏅 ДОСТИЖЕНИЯ ({len(u.data['ach'])}/{len(ACHIEVEMENTS_LIST)})</b>\n\n"
    for k, v in ACHIEVEMENTS_LIST.items():
        icon = "✅" if k in u.data["ach"] else "🔒"
        txt += f"{icon} {v['n']}: {v['desc']} (+{v['rw']}💰)\n"
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(txt[:4000], call.message.chat.id, call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("« Назад", callback_data="hero_menu_back")))

# ==================== КВЕСТЫ ====================
def check_quests(uid, qtype, amount):
    u = User(uid)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if u.data.get("qdate") != today:
        u.data["aq"] = {}
        for i, q in enumerate(random.sample(DAILY_QUESTS, 3)):
            qc = q.copy()
            qc["id"] = f"q_{today}_{i}"
            qc["progress"] = 0
            u.data["aq"][qc["id"]] = qc
        u.data["qdate"] = today
    
    for qid, q in u.data["aq"].items():
        if q["t"] == qtype and q["progress"] < q["tg"]:
            q["progress"] += amount
            if q["progress"] >= q["tg"]:
                u.data["money"] += q["rm"]
                u.data["exp"] += q["re"]
                u.data["cq"] += 1
    u.save()

def show_quests(call):
    uid = str(call.from_user.id)
    u = User(uid)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if u.data.get("qdate") != today:
        check_quests(uid, "none", 0)
        u = User(uid)
    
    txt = f"<b>📜 КВЕСТЫ ({today})</b>\n\n"
    for qid, q in u.data.get("aq", {}).items():
        p, t = q["progress"], q["tg"]
        bar = "█"*min(10, int(p/t*10)) + "░"*max(0, 10-int(p/t*10))
        txt += f"<b>{q['n']}</b>\n[{bar}] {p}/{t}\n{q['desc']}\n💰{q['rm']} + ✨{q['re']}\n\n"
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(txt[:4000], call.message.chat.id, call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("« Назад", callback_data="other_menu_back")))

# ==================== ТОПЫ ====================
def show_top_menu(call):
    mk = types.InlineKeyboardMarkup(row_width=1)
    mk.add(
        types.InlineKeyboardButton("⭐ По уровню", callback_data="top_lvl"),
        types.InlineKeyboardButton("⚔ По победам", callback_data="top_wins"),
        types.InlineKeyboardButton("💰 По монетам", callback_data="top_money"),
        types.InlineKeyboardButton("« Назад", callback_data="other_menu_back")
    )
    bot.answer_callback_query(call.id)
    bot.edit_message_text("<b>📊 ТОП ИГРОКОВ</b>\nВыберите категорию:", 
        call.message.chat.id, call.message.message_id, reply_markup=mk)

def show_top(call, cat):
    if cat == "lvl":
        srt = sorted(users.items(), key=lambda x: (x[1].get("lvl",1), x[1].get("exp",0)), reverse=True)[:10]
        title = "⭐ ТОП ПО УРОВНЮ"
        fmt = lambda d: f"Ур.{d.get('lvl',1)}"
    elif cat == "wins":
        srt = sorted(users.items(), key=lambda x: x[1].get("wins",0), reverse=True)[:10]
        title = "⚔ ТОП ПО ПОБЕДАМ"
        fmt = lambda d: f"{d.get('wins',0)} побед"
    elif cat == "money":
        srt = sorted(users.items(), key=lambda x: x[1].get("money",0), reverse=True)[:10]
        title = "💰 ТОП ПО МОНЕТАМ"
        fmt = lambda d: f"{d.get('money',0)}💰"
    
    medals = ["🥇","🥈","🥉","4","5","6","7","8","9","10"]
    txt = f"<b>{title}</b>\n\n"
    for i, (uid, data) in enumerate(srt):
        txt += f"{medals[i]} {data.get('fname','Игрок')}: {fmt(data)}\n"
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("« Назад", callback_data="o_top")))

# ==================== КЛАНЫ ====================
def show_clan_menu(call):
    uid = str(call.from_user.id)
    u = User(uid)
    
    mk = types.InlineKeyboardMarkup(row_width=1)
    if u.data.get("clan"):
        mk.add(types.InlineKeyboardButton("📊 Мой клан", callback_data="clan_info"))
        mk.add(types.InlineKeyboardButton("🚪 Покинуть", callback_data="clan_leave"))
    else:
        mk.add(types.InlineKeyboardButton("🛡 Создать (5000💰)", callback_data="clan_create"))
        mk.add(types.InlineKeyboardButton("📋 Список кланов", callback_data="clan_list"))
    mk.add(types.InlineKeyboardButton("« Назад", callback_data="other_menu_back"))
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text("<b>🛡 КЛАНЫ</b>", call.message.chat.id, call.message.message_id, reply_markup=mk)

def handle_clan(call, action):
    uid = str(call.from_user.id)
    u = User(uid)
    
    if action == "create":
        if u.data["money"] < 5000:
            bot.answer_callback_query(call.id, "❌ 5000💰 нужно")
            return
        bot.edit_message_text("Введите название клана:\n<code>/clancreate [название]</code>",
            call.message.chat.id, call.message.message_id)
    
    elif action == "list":
        if not clans:
            bot.answer_callback_query(call.id, "Нет кланов")
            return
        txt = "<b>📋 КЛАНЫ</b>\n\n"
        for name, data in list(clans.items())[:10]:
            txt += f"🛡 {name}: {len(data.get('members',[]))} уч.\n"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("« Назад", callback_data="o_clan")))
    
    elif action == "info":
        clan = u.data.get("clan")
        if clan and clan in clans:
            c = clans[clan]
            txt = f"<b>🛡 {clan}</b>\n👑 {c.get('leader','')}\n👥 {len(c.get('members',[]))}\n💰 Казна: {c.get('treasury',0)}"
            bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("« Назад", callback_data="o_clan")))

@bot.message_handler(commands=['clancreate'])
def clan_create(msg):
    uid = str(msg.from_user.id)
    u = User(uid)
    parts = msg.text.split(maxsplit=1)
    
    if len(parts) < 2:
        bot.send_message(msg.chat.id, "❌ /clancreate [название]")
        return
    
    name = parts[1].strip()[:20]
    if u.data["money"] < 5000:
        bot.send_message(msg.chat.id, "❌ 5000💰 нужно")
        return
    
    if name in clans:
        bot.send_message(msg.chat.id, "❌ Занято")
        return
    
    u.data["money"] -= 5000
    u.data["clan"] = name
    u.save()
    clans[name] = {"leader": msg.from_user.first_name, "lid": uid, "members": [msg.from_user.first_name], "treasury": 0}
    save_json(DATA_FILES['clans'], clans)
    bot.send_message(msg.chat.id, f"✅ Клан <b>{name}</b> создан!")

# ==================== РП КОМАНДЫ ====================
def show_rp(call):
    txt = """
<b>🎮 РП КОМАНДЫ</b>

/dance - танцевать
/hi - поздороваться
/attack (reply) - атаковать
/heal - лечиться
/meditate - медитировать
/explore - исследовать
/flip - монетка
/roll - кубик
/hug (reply) - обнять
/punch (reply) - ударить
"""
    bot.answer_callback_query(call.id)
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("« Назад", callback_data="other_menu_back")))

@bot.message_handler(commands=['dance','hi','attack','heal','meditate','explore','flip','roll','hug','punch'])
def rp_commands(msg):
    cmd = msg.text.split()[0].replace('/','')
    uid = str(msg.from_user.id)
    u = User(uid)
    
    actions = {
        'dance': [f"💃 {msg.from_user.first_name} танцует!"],
        'hi': [f"👋 {msg.from_user.first_name} приветствует всех!"],
        'attack': [f"⚔ {msg.from_user.first_name} атакует {msg.reply_to_message.from_user.first_name}!" if msg.reply_to_message else f"⚔ {msg.from_user.first_name} атакует воздух!"],
        'heal': [f"💚 {msg.from_user.first_name} лечится! +{random.randint(10,30)} HP"],
        'meditate': [f"🧘 {msg.from_user.first_name} медитирует! +{random.randint(5,15)} EXP"],
        'explore': [f"🔍 {msg.from_user.first_name} исследует локацию! +{random.randint(20,80)}💰"],
        'flip': [f"🪙 {random.choice(['Орёл','Решка'])}!"],
        'roll': [f"🎲 {random.randint(1,6)}"],
        'hug': [f"🤗 {msg.from_user.first_name} обнимает {msg.reply_to_message.from_user.first_name}!" if msg.reply_to_message else f"🤗 {msg.from_user.first_name} обнимает всех!"],
        'punch': [f"👊 {msg.from_user.first_name} бьёт {msg.reply_to_message.from_user.first_name}!" if msg.reply_to_message else f"👊 {msg.from_user.first_name} бьёт воздух!"]
    }
    
    bot.send_message(msg.chat.id, random.choice(actions.get(cmd, ["❓"])))
    
    if cmd == "explore":
        u.data["money"] += random.randint(20, 80)
        u.save()

# ==================== ПОМОЩЬ ====================
def show_help(call):
    txt = """
<b>📖 КОМАНДЫ</b>

/start - перезапуск
/profile - профиль
/inv - инвентарь
/duel - PvP дуэль
/ranked - рейтинговая
/hardcore - хардкор
/friendly - дружеская
/survival - выживание
/daily - бонус
/work - работа
/top - рейтинг
/clan - кланы
/quests - квесты
/ach - достижения
/admin - админка
"""
    bot.answer_callback_query(call.id)
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("« Назад", callback_data="other_menu_back")))

# ==================== АДМИН-ПАНЕЛЬ ====================
@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "❌ Нет доступа")
        return
    
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
        types.InlineKeyboardButton("👤 Инфо игрока", callback_data="adm_user_info"),
        types.InlineKeyboardButton("💰 Выдать монеты", callback_data="adm_give_money"),
        types.InlineKeyboardButton("🎁 Выдать предмет", callback_data="adm_give_item"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("💎 Лимит. предметы", callback_data="adm_limited"),
        types.InlineKeyboardButton("❌ Забанить", callback_data="adm_ban"),
        types.InlineKeyboardButton("✅ Разбанить", callback_data="adm_unban"),
        types.InlineKeyboardButton("🔄 Сброс дня", callback_data="adm_reset"),
        types.InlineKeyboardButton("📋 Репорты", callback_data="adm_reports")
    )
    bot.send_message(msg.chat.id, "<b>🔧 АДМИН-ПАНЕЛЬ</b>", reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Нет доступа")
        return
    
    action = call.data[4:]
    
    if action == "stats":
        total_u = len(users)
        total_m = sum(u.get("money",0) for u in users.values())
        total_d = sum(u.get("wins",0)+u.get("losses",0) for u in users.values())
        total_banned = sum(1 for u in users.values() if u.get("banned"))
        
        txt = f"""
<b>📊 СТАТИСТИКА</b>
👥 Юзеров: {total_u}
💰 Монет: {total_m}
⚔ Дуэлей: {total_d}
❌ Забанено: {total_banned}
🛡 Кланов: {len(clans)}
💎 Лимит: {sum(v['rem'] for v in limited.values())}
"""
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("« Назад", callback_data="admin_back")))
    
    elif action == "give_money":
        bot.edit_message_text("💰 Формат:\n<code>/givemoney [ID] [сумма]</code>",
            call.message.chat.id, call.message.message_id)
    
    elif action == "give_item":
        bot.edit_message_text("🎁 Формат:\n<code>/giveitem [ID] [item_key]</code>",
            call.message.chat.id, call.message.message_id)
    
    elif action == "broadcast":
        bot.edit_message_text("📢 Формат:\n<code>/broadcast [текст]</code>",
            call.message.chat.id, call.message.message_id)
    
    elif action == "ban":
        bot.edit_message_text("❌ Формат:\n<code>/ban [ID] [причина]</code>",
            call.message.chat.id, call.message.message_id)
    
    elif action == "unban":
        bot.edit_message_text("✅ Формат:\n<code>/unban [ID]</code>",
            call.message.chat.id, call.message.message_id)
    
    elif action == "reset":
        for uid in users:
            users[uid]["last_daily"] = None
            users[uid]["last_work"] = None
        save_json(DATA_FILES['users'], users)
        bot.answer_callback_query(call.id, "✅ Бонусы сброшены")
    
    elif action == "reports":
        txt = "<b>📋 РЕПОРТЫ</b>\n\n"
        if reports:
            for rid, r in list(reports.items())[:10]:
                txt += f"🚫 {r.get('reporter','')} → {r.get('target','')}: {r.get('reason','')}\n"
        else:
            txt += "Нет репортов"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("« Назад", callback_data="admin_back")))
    
    elif action == "back":
        admin_panel(call.message)

# Админ команды
@bot.message_handler(commands=['givemoney'])
def adm_give_money(msg):
    if msg.from_user.id != ADMIN_ID: return
    try:
        _, tid, amount = msg.text.split()
        tid, amount = str(tid), int(amount)
        u = User(tid)
        u.data["money"] += amount
        u.save()
        bot.send_message(msg.chat.id, f"✅ {amount}💰 → {tid}")
    except:
        bot.send_message(msg.chat.id, "❌ /givemoney [ID] [сумма]")

@bot.message_handler(commands=['giveitem'])
def adm_give_item(msg):
    if msg.from_user.id != ADMIN_ID: return
    try:
        _, tid, item_key = msg.text.split()
        u = User(tid)
        u.data["inv"].append(item_key)
        u.save()
        item = items.get(item_key) or limited.get(item_key)
        bot.send_message(msg.chat.id, f"✅ {item['n'] if item else item_key} → {tid}")
    except:
        bot.send_message(msg.chat.id, "❌ /giveitem [ID] [key]")

@bot.message_handler(commands=['broadcast'])
def adm_broadcast(msg):
    if msg.from_user.id != ADMIN_ID: return
    text = msg.text.replace('/broadcast', '', 1).strip()
    if not text:
        bot.send_message(msg.chat.id, "❌ /broadcast [текст]")
        return
    s = f = 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 {text}")
            s += 1
        except: f += 1
    bot.send_message(msg.chat.id, f"✅ {s} | ❌ {f}")

@bot.message_handler(commands=['ban'])
def adm_ban(msg):
    if msg.from_user.id != ADMIN_ID: return
    try:
        parts = msg.text.split(maxsplit=2)
        tid = str(parts[1])
        reason = parts[2] if len(parts) > 2 else "Нет причины"
        u = User(tid)
        u.data["banned"] = True
        u.data["ban_reason"] = reason
        u.save()
        bot.send_message(msg.chat.id, f"❌ {tid} забанен: {reason}")
        try: bot.send_message(int(tid), f"❌ Вы забанены: {reason}")
        except: pass
    except:
        bot.send_message(msg.chat.id, "❌ /ban [ID] [причина]")

@bot.message_handler(commands=['unban'])
def adm_unban(msg):
    if msg.from_user.id != ADMIN_ID: return
    try:
        tid = str(msg.text.split()[1])
        u = User(tid)
        u.data["banned"] = False
        u.data["ban_reason"] = ""
        u.save()
        bot.send_message(msg.chat.id, f"✅ {tid} разбанен")
    except:
        bot.send_message(msg.chat.id, "❌ /unban [ID]")

@bot.message_handler(commands=['report'])
def report_player(msg):
    if not msg.reply_to_message:
        bot.send_message(msg.chat.id, "❌ Ответьте на сообщение нарушителя")
        return
    
    rid = str(int(time.time()))
    reports[rid] = {
        "reporter": str(msg.from_user.id),
        "target": str(msg.reply_to_message.from_user.id),
        "reason": msg.text.replace('/report', '', 1).strip() or "Не указана",
        "time": datetime.now().isoformat()
    }
    save_json(DATA_FILES['reports'], reports)
    bot.send_message(msg.chat.id, "✅ Репорт отправлен администратору")

# ==================== ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ ====================
@bot.message_handler(commands=['profile'])
def cmd_profile(msg): hero_menu(msg)

@bot.message_handler(commands=['inv'])
def cmd_inv(msg):
    uid = str(msg.from_user.id)
    u = User(uid)
    if not u.data["inv"]:
        bot.send_message(msg.chat.id, "🎒 Пусто")
        return
    cnt = {}
    for it in u.data["inv"]: cnt[it] = cnt.get(it, 0) + 1
    txt = "<b>🎒 ИНВЕНТАРЬ</b>\n"
    for k, c in cnt.items():
        item = items.get(k) or limited.get(k)
        txt += f"• {item['n']} x{c}\n" if item else ""
    bot.send_message(msg.chat.id, txt[:4000])

@bot.message_handler(commands=['duel', 'ranked', 'hardcore', 'friendly', 'survival'])
def duel_cmd(msg):
    cmd = msg.text.split()[0].replace('/', '')
    if not msg.reply_to_message:
        bot.send_message(msg.chat.id, "❌ Ответьте на сообщение соперника")
        return
    
    uid, oid = str(msg.from_user.id), str(msg.reply_to_message.from_user.id)
    if uid == oid:
        bot.send_message(msg.chat.id, "❌ Нельзя с собой")
        return
    
    bets = {"duel": 100, "ranked": 200, "hardcore": 500, "survival": 300, "friendly": 0}
    bet = bets.get(cmd, 0)
    
    u, o = User(uid), User(oid)
    if bet > 0:
        if u.data["money"] < bet:
            bot.send_message(msg.chat.id, f"❌ Нужно {bet}💰")
            return
        if o.data["money"] < bet:
            bot.send_message(msg.chat.id, f"❌ У соперника нет {bet}💰")
            return
    
    if bet > 0:
        u.data["money"] -= bet
        o.data["money"] -= bet
        u.save()
        o.save()
    
    result = execute_duel(uid, oid)
    
    u, o = User(uid), User(oid)
    if result["winner"]:
        winner = User(result["winner"])
        loser = User(oid if result["winner"] == uid else uid)
        if bet > 0:
            winner.data["money"] += bet * 2
        winner.data["wins"] += 1
        loser.data["losses"] += 1
        winner.save()
        loser.save()
    
    wname = User(result["winner"]).data["fname"] if result["winner"] else "Ничья"
    bot.send_message(msg.chat.id, f"""
<b>⚔ ДУЭЛЬ ЗАВЕРШЕНА!</b>
Победитель: <b>{wname}</b>
Ходов: {result['turns']}
Ставка: {bet}💰
""")

# ==================== ЗАПУСК ====================
print("=" * 50)
print("⚔ ДУЭЛЬ БОТ v4.0 ЗАПУЩЕН")
print(f"👤 Админ ID: {ADMIN_ID}")
print(f"👥 Пользователей: {len(users)}")
print(f"📦 Предметов: {len(items)}")
print(f"💎 Лимит: {len(limited)}")
print("=" * 50)

if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"⚠ {e}")
            time.sleep(5)
