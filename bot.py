"""
╔══════════════════════════════════════════════════════════╗
║          🌾  HARVEST VALLEY  •  Farm Bot  🌾             ║
║                                                          ║
║   Установка:  pip install aiogram==3.7.0 aiosqlite       ║
║   Запуск:     python bot.py                              ║
║                                                          ║
║   ⚡ Эксклюзивные механики:                              ║
║      • Погодная система (влияет на урожай)               ║
║      • Питомцы-помощники                                 ║
║      • Достижения и титулы                               ║
║      • Случайные события на ферме                        ║
║      • Система Prestige (перерождение)                   ║
║      • VIP-зоны и редкие культуры                        ║
║      • Ежедневные задания                                ║
║      • Рейтинг фермеров                                  ║
╚══════════════════════════════════════════════════════════╝
"""

import asyncio
import aiosqlite
import random
import json
from datetime import datetime, timezone, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

# ═══════════════════════════════════════════════════════════════════
#  ⚙️  КОНФИГ — замени токен!
# ═══════════════════════════════════════════════════════════════════

BOT_TOKEN = "8996813076:AAGq74gyRRW5fMxvHaIE190_B-tmzXk8aNA"
DB_PATH   = "harvest_valley.db"

# ═══════════════════════════════════════════════════════════════════
#  🎨  ВИЗУАЛЬНЫЕ КОНСТАНТЫ
# ═══════════════════════════════════════════════════════════════════

LOGO = "🌾 <b>HARVEST VALLEY</b> 🌾"

BORDERS = {
    "top":    "╔═══════════════════════════╗",
    "mid":    "╠═══════════════════════════╣",
    "bot":    "╚═══════════════════════════╝",
    "line":   "║",
}

RANK_ICONS = ["🥉","🥈","🥇","💎","👑"]

# ─── Прогресс-бар ─────────────────────────────────────────────────
def progress_bar(current: float, total: float, length: int = 10) -> str:
    filled = int(current / total * length) if total > 0 else 0
    filled = min(filled, length)
    blocks = ["░","▒","▓","█"]
    bar = "█" * filled + "░" * (length - filled)
    pct = int(current / total * 100) if total > 0 else 0
    return f"[{bar}] {pct}%"

# ═══════════════════════════════════════════════════════════════════
#  🌤  ПОГОДНАЯ СИСТЕМА
# ═══════════════════════════════════════════════════════════════════

WEATHER_LIST = [
    {"key": "sunny",    "name": "Солнечно",    "emoji": "☀️",  "bonus": 1.3,  "desc": "Урожай +30%"},
    {"key": "cloudy",   "name": "Облачно",     "emoji": "☁️",  "bonus": 1.0,  "desc": "Обычный день"},
    {"key": "rainy",    "name": "Дождь",       "emoji": "🌧️", "bonus": 1.5,  "desc": "Урожай +50%! Дождик питает поля"},
    {"key": "windy",    "name": "Ветрено",     "emoji": "💨",  "bonus": 0.8,  "desc": "Урожай −20%"},
    {"key": "foggy",    "name": "Туман",       "emoji": "🌫️", "bonus": 0.9,  "desc": "Урожай −10%"},
    {"key": "storm",    "name": "Гроза",       "emoji": "⛈️", "bonus": 0.5,  "desc": "Урожай −50%! Прячь урожай"},
    {"key": "snow",     "name": "Снег",        "emoji": "❄️",  "bonus": 0.7,  "desc": "Урожай −30%"},
    {"key": "rainbow",  "name": "Радуга",      "emoji": "🌈",  "bonus": 2.0,  "desc": "Урожай x2! Волшебная погода"},
]
WEATHER_WEIGHTS = [25, 20, 15, 10, 10, 5, 10, 5]

_current_weather: dict = WEATHER_LIST[0]
_weather_changed_at: datetime = datetime.now(timezone.utc)

def get_weather() -> dict:
    return _current_weather

async def rotate_weather():
    """Меняет погоду каждые 30 минут."""
    global _current_weather, _weather_changed_at
    while True:
        await asyncio.sleep(1800)
        _current_weather = random.choices(WEATHER_LIST, weights=WEATHER_WEIGHTS, k=1)[0]
        _weather_changed_at = datetime.now(timezone.utc)

# ═══════════════════════════════════════════════════════════════════
#  🐾  ПИТОМЦЫ
# ═══════════════════════════════════════════════════════════════════

PETS = {
    "cat": {
        "name": "Мурзик 🐱", "emoji": "🐱",
        "price": 800,
        "bonus_type": "speed",    # ускорение роста
        "bonus_val":  0.8,        # ×0.8 от времени роста
        "desc": "Ускоряет рост на 20%",
    },
    "dog": {
        "name": "Шарик 🐶", "emoji": "🐶",
        "price": 1000,
        "bonus_type": "yield",    # бонус к урожаю
        "bonus_val":  1.5,        # +50% урожая
        "desc": "Урожай +50%",
    },
    "chicken": {
        "name": "Кукуша 🐔", "emoji": "🐔",
        "price": 600,
        "bonus_type": "coins",    # бонус при продаже
        "bonus_val":  1.3,        # +30% монет
        "desc": "Выручка +30%",
    },
    "bee": {
        "name": "Жужа 🐝", "emoji": "🐝",
        "price": 1500,
        "bonus_type": "all",      # всё по чуть-чуть
        "bonus_val":  1.2,
        "desc": "Все бонусы +20%",
    },
    "fox": {
        "name": "Лиска 🦊", "emoji": "🦊",
        "price": 3000,
        "bonus_type": "luck",     # шанс x2 урожай
        "bonus_val":  0.25,       # 25% шанс
        "desc": "25% шанс двойного урожая",
    },
    "dragon": {
        "name": "Дракоша 🐉", "emoji": "🐉",
        "price": 10000,
        "bonus_type": "super",    # скорость + урожай
        "bonus_val":  2.0,
        "desc": "Скорость ×2, урожай ×2 🔥",
    },
}

# ═══════════════════════════════════════════════════════════════════
#  🌿  КУЛЬТУРЫ (обычные + редкие + легендарные)
# ═══════════════════════════════════════════════════════════════════

CROPS = {
    # ── Обычные ───────────────────────────────────────────────────
    "wheat":      {"name":"Пшеница",     "emoji":"🌾","tier":"common",    "grow_time":60,    "seed_price":20,   "sell_price":45,    "xp":5,   "yield":2, "min_level":1},
    "carrot":     {"name":"Морковь",     "emoji":"🥕","tier":"common",    "grow_time":120,   "seed_price":30,   "sell_price":75,    "xp":10,  "yield":2, "min_level":1},
    "corn":       {"name":"Кукуруза",    "emoji":"🌽","tier":"common",    "grow_time":300,   "seed_price":60,   "sell_price":150,   "xp":20,  "yield":3, "min_level":3},
    "tomato":     {"name":"Помидор",     "emoji":"🍅","tier":"common",    "grow_time":600,   "seed_price":100,  "sell_price":280,   "xp":35,  "yield":3, "min_level":5},
    "strawberry": {"name":"Клубника",    "emoji":"🍓","tier":"uncommon",  "grow_time":1800,  "seed_price":200,  "sell_price":600,   "xp":80,  "yield":4, "min_level":8},
    "pumpkin":    {"name":"Тыква",       "emoji":"🎃","tier":"uncommon",  "grow_time":3600,  "seed_price":400,  "sell_price":1200,  "xp":150, "yield":5, "min_level":12},
    # ── Редкие ────────────────────────────────────────────────────
    "rose":       {"name":"Роза",        "emoji":"🌹","tier":"rare",      "grow_time":7200,  "seed_price":800,  "sell_price":2800,  "xp":300, "yield":3, "min_level":15},
    "bamboo":     {"name":"Бамбук",      "emoji":"🎋","tier":"rare",      "grow_time":10800, "seed_price":1200, "sell_price":4500,  "xp":450, "yield":4, "min_level":20},
    # ── Легендарные ───────────────────────────────────────────────
    "dragon_fruit":{"name":"Питайя",     "emoji":"🐉","tier":"legendary", "grow_time":86400, "seed_price":5000, "sell_price":25000, "xp":2000,"yield":5, "min_level":30},
    "stardust":   {"name":"Звёздный цвет","emoji":"✨","tier":"legendary","grow_time":43200, "seed_price":3000, "sell_price":15000, "xp":1500,"yield":3, "min_level":25},
}

TIER_STYLE = {
    "common":    ("⬜","Обычная"),
    "uncommon":  ("🟩","Необычная"),
    "rare":      ("🟦","Редкая"),
    "legendary": ("🟨","Легендарная"),
}

PLOT_PRICE  = 500
START_COINS = 500
MAX_PLOTS   = 12

def unlocked_crops(level: int) -> list[str]:
    return [k for k, v in CROPS.items() if level >= v["min_level"]]

# ═══════════════════════════════════════════════════════════════════
#  🏆  ДОСТИЖЕНИЯ
# ═══════════════════════════════════════════════════════════════════

ACHIEVEMENTS = {
    "first_harvest":  {"name":"Первый урожай",    "emoji":"🌱","desc":"Собери свой первый урожай",             "reward":100},
    "rich":           {"name":"Богач",             "emoji":"💰","desc":"Накопи 10 000 монет",                  "reward":500},
    "level10":        {"name":"Опытный фермер",    "emoji":"🏅","desc":"Достигни 10 уровня",                   "reward":1000},
    "full_farm":      {"name":"Аграрий",           "emoji":"🚜","desc":"Купи все 12 грядок",                   "reward":2000},
    "pet_owner":      {"name":"Любитель животных", "emoji":"🐾","desc":"Купи первого питомца",                 "reward":300},
    "rare_harvest":   {"name":"Коллекционер",      "emoji":"💎","desc":"Собери редкую культуру",               "reward":1500},
    "legend_harvest": {"name":"Легенда фермы",     "emoji":"👑","desc":"Собери легендарную культуру",          "reward":10000},
    "sell_100k":      {"name":"Миллиардер",        "emoji":"🤑","desc":"Заработай суммарно 100 000 монет",     "reward":5000},
    "prestige":       {"name":"Перерождение",      "emoji":"⭐","desc":"Соверши первый Prestige",              "reward":20000},
    "all_pets":       {"name":"Ноев ковчег",       "emoji":"🦁","desc":"Купи всех питомцев",                   "reward":15000},
}

TITLES = {
    1:  "🌱 Новичок",
    5:  "🌿 Огородник",
    10: "🌾 Фермер",
    20: "🚜 Агроном",
    30: "💎 Мастер урожая",
    50: "👑 Легенда фермы",
}

def get_title(level: int) -> str:
    t = "🌱 Новичок"
    for lvl, title in TITLES.items():
        if level >= lvl:
            t = title
    return t

# ═══════════════════════════════════════════════════════════════════
#  🎲  СЛУЧАЙНЫЕ СОБЫТИЯ
# ═══════════════════════════════════════════════════════════════════

RANDOM_EVENTS = [
    {"name":"Щедрый урожай",   "emoji":"🎁","effect":"bonus_coins",   "value":500,  "msg":"Ты нашёл клад на поле! +500🪙"},
    {"name":"Налёт саранчи",   "emoji":"🦗","effect":"lose_coins",    "value":200,  "msg":"Саранча съела часть запасов. −200🪙"},
    {"name":"Гости с рынка",   "emoji":"🏪","effect":"bonus_coins",   "value":1000, "msg":"Торговцы заплатили за редкий товар! +1000🪙"},
    {"name":"Удобрение",       "emoji":"🌿","effect":"speed_boost",   "value":0.5,  "msg":"Волшебное удобрение! Следующий урожай вырастет вдвое быстрее 🌿"},
    {"name":"Звёздный дождь",  "emoji":"🌠","effect":"bonus_xp",      "value":500,  "msg":"Звёздный дождь озарил поля! +500 XP ✨"},
    {"name":"Кража",           "emoji":"🦹","effect":"lose_item",     "value":1,    "msg":"Воришка украл немного урожая из инвентаря 😤"},
    {"name":"Фермерская ярмарка","emoji":"🎡","effect":"bonus_coins", "value":2000, "msg":"Победил на ярмарке! Приз +2000🪙 🎉"},
]

async def trigger_random_event(uid: int) -> str | None:
    """10% шанс события при каждом сборе урожая."""
    if random.random() > 0.10:
        return None
    ev = random.choice(RANDOM_EVENTS)
    msg = f"\n\n{ev['emoji']} <b>СОБЫТИЕ: {ev['name']}</b>\n{ev['msg']}"
    if ev["effect"] == "bonus_coins":
        await update_coins(uid, ev["value"])
    elif ev["effect"] == "lose_coins":
        user = await get_user(uid)
        loss = min(ev["value"], user["coins"])
        await update_coins(uid, -loss)
    elif ev["effect"] == "bonus_xp":
        await add_xp(uid, ev["value"])
    elif ev["effect"] == "speed_boost":
        await set_flag(uid, "speed_boost", "1")
    return msg

# ═══════════════════════════════════════════════════════════════════
#  🗄  БАЗА ДАННЫХ
# ═══════════════════════════════════════════════════════════════════

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id      INTEGER PRIMARY KEY,
                username     TEXT,
                coins        INTEGER DEFAULT 500,
                xp           INTEGER DEFAULT 0,
                level        INTEGER DEFAULT 1,
                prestige     INTEGER DEFAULT 0,
                total_earned INTEGER DEFAULT 0,
                joined       TEXT    DEFAULT (datetime('now')),
                last_daily   TEXT    DEFAULT NULL,
                flags        TEXT    DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS plots (
                user_id    INTEGER,
                slot       INTEGER,
                crop       TEXT,
                planted_at TEXT,
                PRIMARY KEY (user_id, slot)
            );
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                item    TEXT,
                qty     INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, item)
            );
            CREATE TABLE IF NOT EXISTS achievements (
                user_id INTEGER,
                ach_key TEXT,
                earned_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, ach_key)
            );
            CREATE TABLE IF NOT EXISTS pets (
                user_id  INTEGER,
                pet_key  TEXT,
                active   INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, pet_key)
            );
            CREATE TABLE IF NOT EXISTS daily_tasks (
                user_id  INTEGER,
                task_key TEXT,
                progress INTEGER DEFAULT 0,
                done     INTEGER DEFAULT 0,
                date     TEXT,
                PRIMARY KEY (user_id, task_key, date)
            );
        """)
        await db.commit()


async def get_user(uid: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id=?", (uid,)) as c:
            row = await c.fetchone()
            return dict(row) if row else None


async def ensure_user(uid: int, username: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)",
            (uid, username or "Фермер"),
        )
        for slot in range(3):
            await db.execute("INSERT OR IGNORE INTO plots (user_id, slot) VALUES (?,?)", (uid, slot))
        await db.commit()
    return await get_user(uid)


async def update_coins(uid: int, delta: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET coins=MAX(0,coins+?) WHERE user_id=?", (delta, uid))
        if delta > 0:
            await db.execute("UPDATE users SET total_earned=total_earned+? WHERE user_id=?", (delta, uid))
        await db.commit()


async def add_xp(uid: int, xp: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET xp=xp+? WHERE user_id=?", (xp, uid))
        await db.execute("UPDATE users SET level=(xp/100)+1 WHERE user_id=?", (uid,))
        await db.commit()


async def get_plots(uid: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM plots WHERE user_id=? ORDER BY slot", (uid,)) as c:
            return [dict(r) for r in await c.fetchall()]


async def plant(uid: int, slot: int, crop: str):
    ts = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE plots SET crop=?, planted_at=? WHERE user_id=? AND slot=?", (crop, ts, uid, slot)
        )
        await db.commit()


async def clear_plot(uid: int, slot: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE plots SET crop=NULL, planted_at=NULL WHERE user_id=? AND slot=?", (uid, slot)
        )
        await db.commit()


async def buy_plot_db(uid: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM plots WHERE user_id=?", (uid,)) as c:
            slot = (await c.fetchone())[0]
        await db.execute("INSERT INTO plots (user_id, slot) VALUES (?,?)", (uid, slot))
        await db.commit()
        return slot


async def get_inv(uid: int) -> dict[str, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT item, qty FROM inventory WHERE user_id=? AND qty>0", (uid,)
        ) as c:
            return {r["item"]: r["qty"] for r in await c.fetchall()}


async def add_item(uid: int, item: str, qty: int = 1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO inventory(user_id,item,qty) VALUES(?,?,?) "
            "ON CONFLICT(user_id,item) DO UPDATE SET qty=qty+excluded.qty",
            (uid, item, qty),
        )
        await db.commit()


async def remove_item(uid: int, item: str, qty: int = 1) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT qty FROM inventory WHERE user_id=? AND item=?", (uid, item)
        ) as c:
            row = await c.fetchone()
        if not row or row[0] < qty:
            return False
        await db.execute(
            "UPDATE inventory SET qty=qty-? WHERE user_id=? AND item=?", (qty, uid, item)
        )
        await db.commit()
        return True


# ─── Достижения ───────────────────────────────────────────────────

async def get_achievements(uid: int) -> set[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT ach_key FROM achievements WHERE user_id=?", (uid,)
        ) as c:
            return {r[0] for r in await c.fetchall()}


async def grant_achievement(uid: int, key: str) -> bool:
    """Выдаёт достижение если ещё нет. Возвращает True если выдано впервые."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM achievements WHERE user_id=? AND ach_key=?", (uid, key)
        ) as c:
            if await c.fetchone():
                return False
        await db.execute(
            "INSERT INTO achievements(user_id, ach_key) VALUES(?,?)", (uid, key)
        )
        await db.commit()
    reward = ACHIEVEMENTS[key]["reward"]
    await update_coins(uid, reward)
    return True


async def check_achievements(uid: int) -> list[str]:
    """Проверяет все достижения, выдаёт новые. Возвращает список новых."""
    user = await get_user(uid)
    inv  = await get_inv(uid)
    earned = await get_achievements(uid)
    new = []

    checks = {
        "rich":       user["coins"] >= 10000,
        "level10":    user["level"] >= 10,
        "full_farm":  len(await get_plots(uid)) >= MAX_PLOTS,
        "sell_100k":  user["total_earned"] >= 100000,
    }
    for key, cond in checks.items():
        if cond and key not in earned:
            if await grant_achievement(uid, key):
                new.append(key)
    return new


# ─── Питомцы ──────────────────────────────────────────────────────

async def get_user_pets(uid: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM pets WHERE user_id=?", (uid,)) as c:
            return [dict(r) for r in await c.fetchall()]


async def get_active_pet(uid: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT pet_key FROM pets WHERE user_id=? AND active=1", (uid,)
        ) as c:
            row = await c.fetchone()
            if row:
                return PETS.get(row["pet_key"])
    return None


async def set_active_pet(uid: int, pet_key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE pets SET active=0 WHERE user_id=?", (uid,))
        await db.execute("UPDATE pets SET active=1 WHERE user_id=? AND pet_key=?", (uid, pet_key))
        await db.commit()


async def buy_pet_db(uid: int, pet_key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO pets(user_id, pet_key) VALUES(?,?)", (uid, pet_key)
        )
        await db.commit()


# ─── Флаги (временные буферы) ─────────────────────────────────────

async def set_flag(uid: int, key: str, val: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT flags FROM users WHERE user_id=?", (uid,)) as c:
            row = await c.fetchone()
        flags = json.loads(row[0]) if row else {}
        flags[key] = val
        await db.execute("UPDATE users SET flags=? WHERE user_id=?", (json.dumps(flags), uid))
        await db.commit()


async def get_flag(uid: int, key: str) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT flags FROM users WHERE user_id=?", (uid,)) as c:
            row = await c.fetchone()
        flags = json.loads(row[0]) if row else {}
        return flags.get(key)


async def clear_flag(uid: int, key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT flags FROM users WHERE user_id=?", (uid,)) as c:
            row = await c.fetchone()
        flags = json.loads(row[0]) if row else {}
        flags.pop(key, None)
        await db.execute("UPDATE users SET flags=? WHERE user_id=?", (json.dumps(flags), uid))
        await db.commit()


# ─── Рейтинг ──────────────────────────────────────────────────────

async def get_leaderboard() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT username, level, total_earned, prestige FROM users "
            "ORDER BY prestige DESC, total_earned DESC LIMIT 10"
        ) as c:
            return [dict(r) for r in await c.fetchall()]


# ─── Ежедневные задания ───────────────────────────────────────────

DAILY_TASKS_POOL = [
    {"key":"harvest_5",   "name":"Собери 5 урожаев",          "goal":5,  "reward":300},
    {"key":"sell_500",    "name":"Продай на 500🪙",            "goal":500,"reward":250},
    {"key":"plant_3",     "name":"Посади 3 культуры",          "goal":3,  "reward":200},
    {"key":"buy_seed_3",  "name":"Купи 3 семени",              "goal":3,  "reward":150},
]

def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


async def get_daily_tasks(uid: int) -> list[dict]:
    today = today_str()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM daily_tasks WHERE user_id=? AND date=?", (uid, today)
        ) as c:
            rows = [dict(r) for r in await c.fetchall()]

    if not rows:
        # Генерируем 3 задания на день
        chosen = random.sample(DAILY_TASKS_POOL, min(3, len(DAILY_TASKS_POOL)))
        async with aiosqlite.connect(DB_PATH) as db:
            for t in chosen:
                await db.execute(
                    "INSERT OR IGNORE INTO daily_tasks(user_id,task_key,progress,done,date) VALUES(?,?,0,0,?)",
                    (uid, t["key"], today),
                )
            await db.commit()
        return await get_daily_tasks(uid)

    result = []
    for row in rows:
        task_def = next((t for t in DAILY_TASKS_POOL if t["key"] == row["task_key"]), None)
        if task_def:
            result.append({**task_def, "progress": row["progress"], "done": bool(row["done"])})
    return result


async def update_daily_task(uid: int, task_key: str, delta: int = 1) -> int:
    """Обновляет прогресс задания. Возвращает награду если выполнено."""
    today = today_str()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT progress, done FROM daily_tasks WHERE user_id=? AND task_key=? AND date=?",
            (uid, task_key, today),
        ) as c:
            row = await c.fetchone()
        if not row or row[1]:
            return 0
        new_prog = row[0] + delta
        task_def = next((t for t in DAILY_TASKS_POOL if t["key"] == task_key), None)
        if not task_def:
            return 0
        done = new_prog >= task_def["goal"]
        await db.execute(
            "UPDATE daily_tasks SET progress=?, done=? WHERE user_id=? AND task_key=? AND date=?",
            (new_prog, int(done), uid, task_key, today),
        )
        await db.commit()
    if done:
        await update_coins(uid, task_def["reward"])
        return task_def["reward"]
    return 0


# ─── Prestige ─────────────────────────────────────────────────────

async def do_prestige(uid: int) -> bool:
    """Сброс уровня/монет в обмен на Prestige-звезду и постоянные бонусы."""
    user = await get_user(uid)
    if user["level"] < 50:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET prestige=prestige+1, xp=0, level=1, coins=500 WHERE user_id=?",
            (uid,),
        )
        await db.commit()
    await grant_achievement(uid, "prestige")
    return True


# ═══════════════════════════════════════════════════════════════════
#  🔧  УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════════

def fmt_time(sec: float) -> str:
    h, r = divmod(int(sec), 3600)
    m, s = divmod(r, 60)
    parts = []
    if h: parts.append(f"{h}ч")
    if m: parts.append(f"{m}м")
    parts.append(f"{s}с")
    return " ".join(parts)


def elapsed(planted_at: str) -> float:
    t = datetime.fromisoformat(planted_at).replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - t).total_seconds()


async def get_grow_time(uid: int, crop_key: str) -> float:
    """Время роста с учётом питомца и буфера."""
    base = CROPS[crop_key]["grow_time"]
    pet  = await get_active_pet(uid)
    mult = 1.0
    if pet:
        bt = pet["bonus_type"]
        if bt in ("speed", "super", "all"):
            mult *= pet["bonus_val"] if bt == "speed" else (0.5 if bt == "super" else 0.8)
    # Временный буфер
    boost = await get_flag(uid, "speed_boost")
    if boost:
        mult *= 0.5
        await clear_flag(uid, "speed_boost")
    return base * mult


async def get_sell_mult(uid: int) -> float:
    """Мультипликатор продажи с учётом питомца и погоды."""
    mult = get_weather()["bonus"]
    pet  = await get_active_pet(uid)
    if pet:
        bt = pet["bonus_type"]
        if bt in ("coins", "super", "all"):
            mult *= pet["bonus_val"] if bt == "coins" else (2.0 if bt == "super" else 1.2)
    return mult


async def get_yield_bonus(uid: int, base_yield: int) -> int:
    """Итоговый урожай с учётом питомца."""
    pet = await get_active_pet(uid)
    mult = 1.0
    if pet:
        bt = pet["bonus_type"]
        if bt in ("yield", "super", "all"):
            mult *= pet["bonus_val"] if bt == "yield" else (2.0 if bt == "super" else 1.2)
        if bt == "luck" and random.random() < pet["bonus_val"]:
            mult *= 2.0
    return max(1, int(base_yield * mult))


# ═══════════════════════════════════════════════════════════════════
#  🎹  КЛАВИАТУРЫ
# ═══════════════════════════════════════════════════════════════════

def kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌱 Ферма",      callback_data="farm"),
            InlineKeyboardButton(text="🏪 Магазин",    callback_data="shop"),
        ],
        [
            InlineKeyboardButton(text="🎒 Инвентарь",  callback_data="inventory"),
            InlineKeyboardButton(text="📊 Профиль",    callback_data="profile"),
        ],
        [
            InlineKeyboardButton(text="🐾 Питомцы",    callback_data="pets"),
            InlineKeyboardButton(text="📋 Задания",    callback_data="daily"),
        ],
        [
            InlineKeyboardButton(text="🏆 Рейтинг",    callback_data="leaderboard"),
            InlineKeyboardButton(text="🌤 Погода",     callback_data="weather"),
        ],
        [
            InlineKeyboardButton(text="💰 Продать всё", callback_data="sell_all"),
        ],
    ])


def kb_farm(plots: list[dict], uid_plots_grow: list) -> InlineKeyboardMarkup:
    rows = []
    for i, p in enumerate(plots):
        s   = p["slot"]
        gt  = uid_plots_grow[i]  # реальное время роста с бонусами
        if p["crop"] is None:
            rows.append([InlineKeyboardButton(text=f"🟫 Грядка {s+1} — пусто", callback_data=f"plot_{s}")])
        else:
            c = CROPS[p["crop"]]
            e = elapsed(p["planted_at"])
            if e >= gt:
                tier_icon = TIER_STYLE[c["tier"]][0]
                rows.append([InlineKeyboardButton(
                    text=f"✅ Грядка {s+1} {tier_icon} {c['emoji']} ГОТОВО!",
                    callback_data=f"harvest_{s}",
                )])
            else:
                left = gt - e
                rows.append([InlineKeyboardButton(
                    text=f"⏳ Грядка {s+1} — {c['emoji']} {fmt_time(left)}",
                    callback_data=f"pinfo_{s}",
                )])
    plots_count = len(plots)
    if plots_count < MAX_PLOTS:
        rows.append([InlineKeyboardButton(
            text=f"➕ Купить грядку ({PLOT_PRICE}🪙)",
            callback_data="buy_plot",
        )])
    rows.append([InlineKeyboardButton(text="🔙 Меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_plant(slot: int, level: int) -> InlineKeyboardMarkup:
    rows = []
    for key in unlocked_crops(level):
        c    = CROPS[key]
        tier = TIER_STYLE[c["tier"]][0]
        rows.append([InlineKeyboardButton(
            text=f"{tier}{c['emoji']} {c['name']} | ⏱{fmt_time(c['grow_time'])} | {c['seed_price']}🪙",
            callback_data=f"plant_{slot}_{key}",
        )])
    rows.append([InlineKeyboardButton(text="🔙 Ферма", callback_data="farm")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_shop(level: int) -> InlineKeyboardMarkup:
    rows = []
    for key in unlocked_crops(level):
        c    = CROPS[key]
        tier = TIER_STYLE[c["tier"]][0]
        rows.append([InlineKeyboardButton(
            text=f"{tier}{c['emoji']} {c['name']} — {c['seed_price']}🪙",
            callback_data=f"buyseed_{key}",
        )])
    rows.append([InlineKeyboardButton(text="🔙 Меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_pets_shop(owned: set[str]) -> InlineKeyboardMarkup:
    rows = []
    for key, p in PETS.items():
        if key in owned:
            rows.append([InlineKeyboardButton(
                text=f"✅ {p['name']} — в наличии",
                callback_data=f"petact_{key}",
            )])
        else:
            rows.append([InlineKeyboardButton(
                text=f"🛒 {p['name']} — {p['price']}🪙 ({p['desc']})",
                callback_data=f"petbuy_{key}",
            )])
    rows.append([InlineKeyboardButton(text="🔙 Меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_back(dest: str = "menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=dest)]
    ])


def kb_prestige() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Совершить Prestige!", callback_data="do_prestige")],
        [InlineKeyboardButton(text="🔙 Профиль",            callback_data="profile")],
    ])


# ═══════════════════════════════════════════════════════════════════
#  📝  ТЕКСТОВЫЕ БЛОКИ
# ═══════════════════════════════════════════════════════════════════

async def text_farm(uid: int, plots: list[dict]) -> tuple[str, list]:
    w = get_weather()
    pet = await get_active_pet(uid)
    pet_str = f"{pet['emoji']} {pet['name']}" if pet else "нет"

    # Считаем grow_time для каждой грядки
    grow_times = []
    for p in plots:
        if p["crop"]:
            gt = await get_grow_time(uid, p["crop"])
        else:
            gt = 0
        grow_times.append(gt)

    lines = [
        f"🌾 <b>HARVEST VALLEY</b> — <b>Ферма</b>",
        f"",
        f"{w['emoji']} Погода: <b>{w['name']}</b> • {w['desc']}",
        f"🐾 Питомец: <b>{pet_str}</b>",
        f"",
        f"<b>Грядки:</b>",
    ]
    for i, p in enumerate(plots):
        s  = p["slot"]
        gt = grow_times[i]
        if p["crop"] is None:
            lines.append(f"  {s+1}. 🟫 Пусто")
        else:
            c  = CROPS[p["crop"]]
            e  = elapsed(p["planted_at"])
            tier_icon = TIER_STYLE[c["tier"]][0]
            if e >= gt:
                lines.append(f"  {s+1}. {tier_icon}{c['emoji']} <b>{c['name']}</b> ✅ ГОТОВО!")
            else:
                left = gt - e
                bar  = progress_bar(e, gt, 8)
                lines.append(f"  {s+1}. {c['emoji']} {c['name']} {bar} {fmt_time(left)}")
    return "\n".join(lines), grow_times


def text_profile(user: dict, achs: set[str], pet: dict | None) -> str:
    title    = get_title(user["level"])
    xp_cur   = user["xp"] % 100
    bar      = progress_bar(xp_cur, 100, 10)
    prestige = "⭐" * user["prestige"] if user["prestige"] else "—"
    ach_cnt  = len(achs)
    pet_str  = f"{pet['emoji']} {pet['name']}" if pet else "нет"
    return (
        f"╔══ 📊 <b>ПРОФИЛЬ</b> ══╗\n"
        f"\n"
        f"👤 <b>{user['username']}</b>\n"
        f"{title}\n"
        f"\n"
        f"🏆 Уровень:    <b>{user['level']}</b>\n"
        f"⭐ XP:         <b>{user['xp']}</b> / {user['level']*100}\n"
        f"   {bar}\n"
        f"💰 Монеты:     <b>{user['coins']:,}</b>🪙\n"
        f"📈 Заработано: <b>{user['total_earned']:,}</b>🪙\n"
        f"\n"
        f"✨ Prestige:   {prestige}\n"
        f"🏅 Достижений: <b>{ach_cnt}/{len(ACHIEVEMENTS)}</b>\n"
        f"🐾 Питомец:    {pet_str}\n"
        f"\n"
        f"📅 В игре с: {user['joined'][:10]}\n"
        f"╚══════════════════╝"
    )


def text_weather() -> str:
    w    = get_weather()
    mins = int((datetime.now(timezone.utc) - _weather_changed_at).total_seconds() / 60)
    left = max(0, 30 - mins)
    lines = [f"🌤 <b>Погода в Harvest Valley</b>\n"]
    for ww in WEATHER_LIST:
        mark = "▶️" if ww["key"] == w["key"] else "   "
        lines.append(f"{mark} {ww['emoji']} <b>{ww['name']}</b> — {ww['desc']}")
    lines.append(f"\n⏱ Текущая погода сменится через <b>~{left} мин</b>")
    return "\n".join(lines)


def text_inv(inv: dict[str, int]) -> str:
    if not inv:
        return "🎒 <b>Инвентарь пуст</b>\n\nКупи семена в 🏪 магазине!"
    lines = ["🎒 <b>ИНВЕНТАРЬ</b>\n"]
    seeds   = {k: v for k, v in inv.items() if k.endswith("_seed")}
    harvest = {k: v for k, v in inv.items() if not k.endswith("_seed")}
    if seeds:
        lines.append("🌱 <b>Семена:</b>")
        for item, qty in seeds.items():
            key = item.replace("_seed", "")
            if key in CROPS:
                c    = CROPS[key]
                tier = TIER_STYLE[c["tier"]][0]
                lines.append(f"  {tier}{c['emoji']} {c['name']} × {qty}")
    if harvest:
        lines.append("\n🌽 <b>Урожай:</b>")
        for item, qty in harvest.items():
            if item in CROPS:
                c     = CROPS[item]
                tier  = TIER_STYLE[c["tier"]][0]
                total = c["sell_price"] * qty
                lines.append(f"  {tier}{c['emoji']} {c['name']} × {qty} → {total:,}🪙")
    return "\n".join(lines)


def text_achievements(achs: set[str]) -> str:
    lines = ["🏅 <b>ДОСТИЖЕНИЯ</b>\n"]
    for key, a in ACHIEVEMENTS.items():
        if key in achs:
            lines.append(f"✅ {a['emoji']} <b>{a['name']}</b> — {a['desc']} (+{a['reward']}🪙)")
        else:
            lines.append(f"🔒 {a['emoji']} {a['name']} — {a['desc']}")
    return "\n".join(lines)


def text_daily(tasks: list[dict]) -> str:
    lines = ["📋 <b>ЕЖЕДНЕВНЫЕ ЗАДАНИЯ</b>\n"]
    for t in tasks:
        if t["done"]:
            lines.append(f"✅ <b>{t['name']}</b> — выполнено! +{t['reward']}🪙")
        else:
            bar = progress_bar(t["progress"], t["goal"], 8)
            lines.append(
                f"📌 <b>{t['name']}</b>\n"
                f"   {bar} {t['progress']}/{t['goal']}\n"
                f"   Награда: {t['reward']}🪙"
            )
    lines.append("\n🕛 Задания обновляются каждый день")
    return "\n".join(lines)


def text_leaderboard(rows: list[dict]) -> str:
    lines = ["🏆 <b>ТОП ФЕРМЕРОВ</b>\n"]
    icons = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    for i, r in enumerate(rows):
        stars = "⭐" * r["prestige"] if r["prestige"] else ""
        lines.append(
            f"{icons[i]} <b>{r['username']}</b> {stars}\n"
            f"   Уровень {r['level']} • заработано {r['total_earned']:,}🪙"
        )
    return "\n".join(lines)


def text_pets(user_pets: list[dict], active_pet: dict | None) -> str:
    lines = ["🐾 <b>ПИТОМЦЫ</b>\n"]
    owned_keys = {p["pet_key"] for p in user_pets}
    for key, p in PETS.items():
        if key in owned_keys:
            mark = "▶️ АКТИВЕН" if (active_pet and active_pet == p) else "✅ есть"
            lines.append(f"{mark} {p['emoji']} <b>{p['name']}</b> — {p['desc']}")
        else:
            lines.append(f"🔒 {p['emoji']} {p['name']} — {p['desc']} | цена {p['price']:,}🪙")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
#  🤖  БОТ
# ═══════════════════════════════════════════════════════════════════

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()


async def notify_achievements(new_achs: list[str], msg_or_call):
    """Отправляет уведомление о новых достижениях."""
    for key in new_achs:
        a = ACHIEVEMENTS[key]
        text = (
            f"🎉 <b>ДОСТИЖЕНИЕ РАЗБЛОКИРОВАНО!</b>\n\n"
            f"{a['emoji']} <b>{a['name']}</b>\n"
            f"{a['desc']}\n\n"
            f"💰 Награда: <b>+{a['reward']}🪙</b>"
        )
        if isinstance(msg_or_call, Message):
            await msg_or_call.answer(text, parse_mode="HTML")
        else:
            await msg_or_call.message.answer(text, parse_mode="HTML")


# ── КОМАНДЫ ───────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(msg: Message):
    user = await ensure_user(msg.from_user.id, msg.from_user.username)
    w    = get_weather()
    text = (
        f"🌾 <b>HARVEST VALLEY</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Привет, <b>{msg.from_user.first_name}</b>! 👋\n\n"
        f"Добро пожаловать на лучшую ферму в Telegram!\n\n"
        f"💰 Стартовый капитал: <b>{user['coins']}🪙</b>\n"
        f"{w['emoji']} Погода сейчас: <b>{w['name']}</b>\n\n"
        f"🌱 Сажай культуры, собирай урожай,\n"
        f"🐾 заводи питомцев и становись\n"
        f"👑 легендой своей фермы!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    await msg.answer(text, reply_markup=kb_main(), parse_mode="HTML")


@dp.message(Command("help"))
async def cmd_help(msg: Message):
    text = (
        f"📖 <b>КАК ИГРАТЬ В HARVEST VALLEY</b>\n\n"
        f"<b>Основы:</b>\n"
        f"  🏪 Магазин → купи семена\n"
        f"  🌱 Ферма → посади на грядку\n"
        f"  ✅ Дождись и собери урожай\n"
        f"  💰 Продай всё — получи монеты\n\n"
        f"<b>Эксклюзивные фишки:</b>\n"
        f"  🌤 Погода — влияет на стоимость урожая\n"
        f"  🐾 Питомцы — дают уникальные бонусы\n"
        f"  🏅 Достижения — получай награды\n"
        f"  📋 Задания — выполняй каждый день\n"
        f"  🏆 Рейтинг — соревнуйся с другими\n"
        f"  ⭐ Prestige — перерождение на 50 уровне\n\n"
        f"<b>Культуры по редкости:</b>\n"
        f"  ⬜ Обычные  🟩 Необычные\n"
        f"  🟦 Редкие   🟨 Легендарные\n\n"
        f"<b>Команды:</b>\n"
        f"  /start /farm /shop /profile\n"
        f"  /achievements /help"
    )
    await msg.answer(text, parse_mode="HTML", reply_markup=kb_back("menu"))


@dp.message(Command("achievements"))
async def cmd_achievements(msg: Message):
    await ensure_user(msg.from_user.id, msg.from_user.username)
    achs = await get_achievements(msg.from_user.id)
    await msg.answer(text_achievements(achs), parse_mode="HTML", reply_markup=kb_back("menu"))


# ── CALLBACK: МЕНЮ ────────────────────────────────────────────────

@dp.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery):
    user = await ensure_user(call.from_user.id, call.from_user.username)
    w    = get_weather()
    text = (
        f"🌾 <b>HARVEST VALLEY</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>{user['username']}</b>  🏆 Ур. {user['level']}  ⭐×{user['prestige']}\n"
        f"💰 <b>{user['coins']:,}</b>🪙\n"
        f"{w['emoji']} {w['name']} — {w['desc']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    await call.message.edit_text(text, reply_markup=kb_main(), parse_mode="HTML")
    await call.answer()


# ── CALLBACK: ФЕРМА ───────────────────────────────────────────────

@dp.callback_query(F.data == "farm")
async def cb_farm(call: CallbackQuery):
    uid   = call.from_user.id
    user  = await ensure_user(uid, call.from_user.username)
    plots = await get_plots(uid)
    farm_txt, grow_times = await text_farm(uid, plots)
    await call.message.edit_text(
        farm_txt, reply_markup=kb_farm(plots, grow_times), parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data.startswith("pinfo_"))
async def cb_pinfo(call: CallbackQuery):
    slot  = int(call.data.split("_")[1])
    uid   = call.from_user.id
    plots = await get_plots(uid)
    p = next((x for x in plots if x["slot"] == slot), None)
    if p and p["crop"]:
        c  = CROPS[p["crop"]]
        gt = await get_grow_time(uid, p["crop"])
        e  = elapsed(p["planted_at"])
        left = max(0, gt - e)
        pct  = int(e / gt * 100) if gt else 100
        await call.answer(
            f"{c['emoji']} {c['name']}\nПрогресс: {pct}%\nОсталось: {fmt_time(left)}",
            show_alert=True,
        )
    else:
        await call.answer("Грядка пуста")


@dp.callback_query(F.data.startswith("plot_"))
async def cb_plot_click(call: CallbackQuery):
    slot = int(call.data.split("_")[1])
    uid  = call.from_user.id
    user = await ensure_user(uid, call.from_user.username)
    inv  = await get_inv(uid)
    if not any(k.endswith("_seed") for k in inv):
        await call.answer("🌱 Семян нет! Купи в 🏪 магазине.", show_alert=True)
        return
    await call.message.edit_text(
        f"🌱 <b>Грядка {slot+1}</b> — что посадить?\n\n"
        f"⬜ Обычные  🟩 Необычные  🟦 Редкие  🟨 Легендарные",
        reply_markup=kb_plant(slot, user["level"]),
        parse_mode="HTML",
    )
    await call.answer()


@dp.callback_query(F.data.startswith("plant_"))
async def cb_plant(call: CallbackQuery):
    _, slot_s, crop_key = call.data.split("_", 2)
    slot = int(slot_s)
    uid  = call.from_user.id
    seed = f"{crop_key}_seed"

    if not await remove_item(uid, seed, 1):
        await call.answer("❌ Нет семян! Купи в магазине.", show_alert=True)
        return

    await plant(uid, slot, crop_key)
    c  = CROPS[crop_key]
    gt = await get_grow_time(uid, crop_key)

    # Задание
    reward = await update_daily_task(uid, "plant_3", 1)
    bonus  = f"\n✅ Задание +{reward}🪙!" if reward else ""

    await call.answer(f"🌱 {c['name']} посажена! {fmt_time(gt)}{bonus}")

    user  = await get_user(uid)
    plots = await get_plots(uid)
    farm_txt, grow_times = await text_farm(uid, plots)
    await call.message.edit_text(
        farm_txt, reply_markup=kb_farm(plots, grow_times), parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("harvest_"))
async def cb_harvest(call: CallbackQuery):
    slot  = int(call.data.split("_")[1])
    uid   = call.from_user.id
    plots = await get_plots(uid)
    p = next((x for x in plots if x["slot"] == slot), None)

    if not p or not p["crop"]:
        await call.answer("Грядка уже пуста", show_alert=True)
        return

    c  = CROPS[p["crop"]]
    gt = await get_grow_time(uid, p["crop"])
    if elapsed(p["planted_at"]) < gt:
        left = gt - elapsed(p["planted_at"])
        await call.answer(f"⏳ Ещё не готово! {fmt_time(left)}", show_alert=True)
        return

    qty = await get_yield_bonus(uid, c["yield"])
    await add_item(uid, p["crop"], qty)
    await add_xp(uid, c["xp"])
    await clear_plot(uid, slot)

    # Первый урожай
    achs = await get_achievements(uid)
    if "first_harvest" not in achs:
        await grant_achievement(uid, "first_harvest")
    if c["tier"] == "rare" and "rare_harvest" not in achs:
        await grant_achievement(uid, "rare_harvest")
    if c["tier"] == "legendary" and "legend_harvest" not in achs:
        await grant_achievement(uid, "legend_harvest")

    # Задание
    task_reward = await update_daily_task(uid, "harvest_5", 1)

    # Случайное событие
    event_msg = await trigger_random_event(uid)

    # Проверка достижений
    new_achs = await check_achievements(uid)

    tier_icon = TIER_STYLE[c["tier"]][0]
    bonus_str = f"\n✅ Задание +{task_reward}🪙!" if task_reward else ""
    await call.answer(
        f"✅ {tier_icon}{c['emoji']} {c['name']} ×{qty} собрано! +{c['xp']} XP{bonus_str}",
        show_alert=bool(event_msg or task_reward),
    )

    if event_msg or new_achs:
        notif = event_msg or ""
        for key in new_achs:
            a = ACHIEVEMENTS[key]
            notif += f"\n\n🎉 <b>Достижение!</b> {a['emoji']} {a['name']} +{a['reward']}🪙"
        if notif:
            await call.message.answer(notif.strip(), parse_mode="HTML")

    user  = await get_user(uid)
    plots = await get_plots(uid)
    farm_txt, grow_times = await text_farm(uid, plots)
    await call.message.edit_text(
        farm_txt, reply_markup=kb_farm(plots, grow_times), parse_mode="HTML"
    )


@dp.callback_query(F.data == "buy_plot")
async def cb_buy_plot(call: CallbackQuery):
    uid   = call.from_user.id
    user  = await get_user(uid)
    plots = await get_plots(uid)
    if len(plots) >= MAX_PLOTS:
        await call.answer("🚫 Максимум грядок достигнут!", show_alert=True)
        return
    if user["coins"] < PLOT_PRICE:
        await call.answer(f"❌ Нужно {PLOT_PRICE}🪙, у тебя {user['coins']}🪙", show_alert=True)
        return
    await update_coins(uid, -PLOT_PRICE)
    new_slot = await buy_plot_db(uid)
    await call.answer(f"🎉 Куплена грядка {new_slot+1}!")

    new_achs = await check_achievements(uid)
    plots = await get_plots(uid)
    farm_txt, grow_times = await text_farm(uid, plots)
    await call.message.edit_text(
        farm_txt, reply_markup=kb_farm(plots, grow_times), parse_mode="HTML"
    )
    if new_achs:
        for key in new_achs:
            a = ACHIEVEMENTS[key]
            await call.message.answer(
                f"🎉 <b>Достижение!</b> {a['emoji']} {a['name']} +{a['reward']}🪙",
                parse_mode="HTML",
            )


# ── CALLBACK: МАГАЗИН ─────────────────────────────────────────────

@dp.callback_query(F.data == "shop")
async def cb_shop(call: CallbackQuery):
    user = await ensure_user(call.from_user.id, call.from_user.username)
    await call.message.edit_text(
        f"🏪 <b>МАГАЗИН СЕМЯН</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Баланс: <b>{user['coins']:,}🪙</b>\n\n"
        f"⬜ Обычные  🟩 Необычные\n"
        f"🟦 Редкие   🟨 Легендарные\n"
        f"━━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=kb_shop(user["level"]),
        parse_mode="HTML",
    )
    await call.answer()


@dp.callback_query(F.data.startswith("buyseed_"))
async def cb_buy_seed(call: CallbackQuery):
    crop_key = call.data.replace("buyseed_", "")
    if crop_key not in CROPS:
        await call.answer("Неизвестная культура")
        return
    uid  = call.from_user.id
    user = await get_user(uid)
    c    = CROPS[crop_key]
    if user["coins"] < c["seed_price"]:
        await call.answer(f"❌ Нужно {c['seed_price']}🪙, у тебя {user['coins']}🪙", show_alert=True)
        return
    await update_coins(uid, -c["seed_price"])
    await add_item(uid, f"{crop_key}_seed", 1)

    task_r = await update_daily_task(uid, "buy_seed_3", 1)
    bonus  = f" | Задание +{task_r}🪙!" if task_r else ""
    await call.answer(f"✅ Куплено {c['emoji']} {c['name']}!{bonus}")

    user = await get_user(uid)
    await call.message.edit_text(
        f"🏪 <b>МАГАЗИН СЕМЯН</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Баланс: <b>{user['coins']:,}🪙</b>\n\n"
        f"⬜ Обычные  🟩 Необычные\n"
        f"🟦 Редкие   🟨 Легендарные\n"
        f"━━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=kb_shop(user["level"]),
        parse_mode="HTML",
    )


# ── CALLBACK: ИНВЕНТАРЬ ───────────────────────────────────────────

@dp.callback_query(F.data == "inventory")
async def cb_inventory(call: CallbackQuery):
    await ensure_user(call.from_user.id, call.from_user.username)
    inv = await get_inv(call.from_user.id)
    await call.message.edit_text(text_inv(inv), reply_markup=kb_back(), parse_mode="HTML")
    await call.answer()


# ── CALLBACK: ПРОФИЛЬ ─────────────────────────────────────────────

@dp.callback_query(F.data == "profile")
async def cb_profile(call: CallbackQuery):
    uid  = call.from_user.id
    user = await ensure_user(uid, call.from_user.username)
    achs = await get_achievements(uid)
    pet  = await get_active_pet(uid)

    kb = kb_back()
    if user["level"] >= 50:
        kb = kb_prestige()

    await call.message.edit_text(
        text_profile(user, achs, pet), reply_markup=kb, parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "do_prestige")
async def cb_do_prestige(call: CallbackQuery):
    uid = call.from_user.id
    ok  = await do_prestige(uid)
    if ok:
        await call.answer("⭐ Поздравляем с Prestige! Ферма перерождена.", show_alert=True)
        user = await get_user(uid)
        achs = await get_achievements(uid)
        pet  = await get_active_pet(uid)
        await call.message.edit_text(
            text_profile(user, achs, pet), reply_markup=kb_back("profile"), parse_mode="HTML"
        )
    else:
        await call.answer("❌ Нужен 50 уровень для Prestige!", show_alert=True)


# ── CALLBACK: ПИТОМЦЫ ─────────────────────────────────────────────

@dp.callback_query(F.data == "pets")
async def cb_pets(call: CallbackQuery):
    uid        = call.from_user.id
    user       = await ensure_user(uid, call.from_user.username)
    user_pets  = await get_user_pets(uid)
    active_pet = await get_active_pet(uid)
    owned      = {p["pet_key"] for p in user_pets}
    await call.message.edit_text(
        f"{text_pets(user_pets, active_pet)}\n\n💰 Монеты: <b>{user['coins']:,}🪙</b>",
        reply_markup=kb_pets_shop(owned),
        parse_mode="HTML",
    )
    await call.answer()


@dp.callback_query(F.data.startswith("petbuy_"))
async def cb_pet_buy(call: CallbackQuery):
    pet_key = call.data.replace("petbuy_", "")
    if pet_key not in PETS:
        await call.answer("Неизвестный питомец")
        return
    uid  = call.from_user.id
    user = await get_user(uid)
    p    = PETS[pet_key]
    if user["coins"] < p["price"]:
        await call.answer(f"❌ Нужно {p['price']:,}🪙, у тебя {user['coins']:,}🪙", show_alert=True)
        return
    await update_coins(uid, -p["price"])
    await buy_pet_db(uid, pet_key)
    await set_active_pet(uid, pet_key)
    await call.answer(f"🎉 {p['emoji']} {p['name']} теперь твой питомец!")

    # Достижение
    achs = await get_achievements(uid)
    if "pet_owner" not in achs:
        await grant_achievement(uid, "pet_owner")
    all_keys = set(PETS.keys())
    user_pets = await get_user_pets(uid)
    if {pp["pet_key"] for pp in user_pets} >= all_keys:
        if await grant_achievement(uid, "all_pets"):
            a = ACHIEVEMENTS["all_pets"]
            await call.message.answer(
                f"🎉 <b>Достижение!</b> {a['emoji']} {a['name']} +{a['reward']}🪙",
                parse_mode="HTML",
            )

    user_pets  = await get_user_pets(uid)
    active_pet = await get_active_pet(uid)
    owned      = {pp["pet_key"] for pp in user_pets}
    user       = await get_user(uid)
    await call.message.edit_text(
        f"{text_pets(user_pets, active_pet)}\n\n💰 Монеты: <b>{user['coins']:,}🪙</b>",
        reply_markup=kb_pets_shop(owned),
        parse_mode="HTML",
    )


@dp.callback_query(F.data.startswith("petact_"))
async def cb_pet_activate(call: CallbackQuery):
    pet_key = call.data.replace("petact_", "")
    uid     = call.from_user.id
    await set_active_pet(uid, pet_key)
    p = PETS[pet_key]
    await call.answer(f"✅ {p['emoji']} {p['name']} активирован!", show_alert=True)

    user_pets  = await get_user_pets(uid)
    active_pet = await get_active_pet(uid)
    owned      = {pp["pet_key"] for pp in user_pets}
    user       = await get_user(uid)
    await call.message.edit_text(
        f"{text_pets(user_pets, active_pet)}\n\n💰 Монеты: <b>{user['coins']:,}🪙</b>",
        reply_markup=kb_pets_shop(owned),
        parse_mode="HTML",
    )


# ── CALLBACK: ЗАДАНИЯ ─────────────────────────────────────────────

@dp.callback_query(F.data == "daily")
async def cb_daily(call: CallbackQuery):
    await ensure_user(call.from_user.id, call.from_user.username)
    tasks = await get_daily_tasks(call.from_user.id)
    await call.message.edit_text(
        text_daily(tasks), reply_markup=kb_back(), parse_mode="HTML"
    )
    await call.answer()


# ── CALLBACK: РЕЙТИНГ ─────────────────────────────────────────────

@dp.callback_query(F.data == "leaderboard")
async def cb_leaderboard(call: CallbackQuery):
    rows = await get_leaderboard()
    await call.message.edit_text(
        text_leaderboard(rows), reply_markup=kb_back(), parse_mode="HTML"
    )
    await call.answer()


# ── CALLBACK: ПОГОДА ──────────────────────────────────────────────

@dp.callback_query(F.data == "weather")
async def cb_weather(call: CallbackQuery):
    await call.message.edit_text(
        text_weather(), reply_markup=kb_back(), parse_mode="HTML"
    )
    await call.answer()


# ── CALLBACK: ПРОДАТЬ ВСЁ ─────────────────────────────────────────

@dp.callback_query(F.data == "sell_all")
async def cb_sell_all(call: CallbackQuery):
    uid  = call.from_user.id
    inv  = await get_inv(uid)
    mult = await get_sell_mult(uid)
    total = 0
    lines = []

    for item, qty in inv.items():
        if item in CROPS:
            c      = CROPS[item]
            earned = int(c["sell_price"] * qty * mult)
            total += earned
            tier   = TIER_STYLE[c["tier"]][0]
            lines.append(f"  {tier}{c['emoji']} {c['name']} ×{qty} → {earned:,}🪙")
            await remove_item(uid, item, qty)

    if total == 0:
        await call.answer("🤷 Нечего продавать!", show_alert=True)
        return

    await update_coins(uid, total)

    # Задание
    task_r = await update_daily_task(uid, "sell_500", total)

    # Достижения
    new_achs = await check_achievements(uid)

    w    = get_weather()
    user = await get_user(uid)
    bonus_str = f"\n✅ Задание выполнено! +{task_r}🪙" if task_r else ""
    await call.message.edit_text(
        f"💰 <b>ПРОДАНО:</b>\n\n"
        + "\n".join(lines) +
        f"\n\n{w['emoji']} Погодный бонус: ×{mult:.1f}\n"
        f"<b>Итого: +{total:,}🪙</b>\n"
        f"Баланс: <b>{user['coins']:,}🪙</b>{bonus_str}",
        reply_markup=kb_back(),
        parse_mode="HTML",
    )
    await call.answer(f"✅ Продано на {total:,}🪙!")

    if new_achs:
        for key in new_achs:
            a = ACHIEVEMENTS[key]
            await call.message.answer(
                f"🎉 <b>Достижение!</b> {a['emoji']} {a['name']} +{a['reward']}🪙",
                parse_mode="HTML",
            )


# ═══════════════════════════════════════════════════════════════════
#  🚀  ЗАПУСК
# ═══════════════════════════════════════════════════════════════════

async def main():
    await init_db()
    print("╔══════════════════════════════════╗")
    print("║   🌾  HARVEST VALLEY BOT  🌾     ║")
    print("║   ✅  База данных готова          ║")
    print("║   🚀  Бот запущен!               ║")
    print("║   🌤  Погодная система активна    ║")
    print("╚══════════════════════════════════╝")

    asyncio.create_task(rotate_weather())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

