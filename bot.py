import asyncio
import random
import logging
from typing import Dict, Any, Optional, Tuple
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import aiosqlite

# ==================== НАСТРОЙКИ И КОНФИГУРАЦИЯ ====================
BOT_TOKEN = "8996813076:AAGcvKnpHgpDAYcHw7NUWGtqI31pxllzWp4"
ADMIN_ID = 5356400377
DB_NAME = "arena_duels.db"

logging.basicConfig(level=logging.INFO)

# ==================== ДАННЫЕ И МЕХАНИКИ ====================
WEAPONS = {
    "dagger": {"name": "🗡 Кинжал", "price": 0, "spec_name": "Тысяча порезов", "type": "dagger"},
    "sword": {"name": "⚔️ Меч", "price": 300, "spec_name": "Казнь", "type": "sword"},
    "axe": {"name": "🪓 Топор", "price": 600, "spec_name": "Кровопускание", "type": "axe"},
    "bow": {"name": "🏹 Лук", "price": 800, "spec_name": "Снайперский выстрел", "type": "bow"},
    "staff": {"name": "🔥 Посох", "price": 1200, "spec_name": "Огненный шторм", "type": "staff"},
    "hammer": {"name": "🔨 Молот", "price": 1500, "spec_name": "Землетрясение", "type": "hammer"}
}

ARMORS = {
    "none": {"name": "👕 Без брони", "def_bonus": 0, "hp_bonus": 0, "price": 0, "type": "none"},
    "light": {"name": "🥋 Лёгкая", "def_bonus": 3, "hp_bonus": 10, "price": 200, "type": "light"},
    "medium": {"name": "🛡 Средняя", "def_bonus": 6, "hp_bonus": 25, "price": 500, "type": "medium"},
    "heavy": {"name": "🏋️ Тяжёлая", "def_bonus": 10, "hp_bonus": 50, "price": 1000, "type": "heavy"},
    "legendary": {"name": "✨ Легендарная", "def_bonus": 15, "hp_bonus": 80, "price": 3000, "type": "legendary"}
}

PVE_BOTS = [
    {"name": "🤖 Тренировочный Манекен", "level": 1, "hp": 50, "atk": 8, "def": 1, "speed": 5, "crit": 5, "weapon": "dagger", "armor": "none", "reward_chips": 30, "reward_exp": 25},
    {"name": "🐀 Гигантская Крыса", "level": 2, "hp": 75, "atk": 13, "def": 3, "speed": 12, "crit": 10, "weapon": "dagger", "armor": "none", "reward_chips": 60, "reward_exp": 50},
    {"name": "🧌 Гоблин-Налётчик", "level": 3, "hp": 110, "atk": 20, "def": 6, "speed": 15, "crit": 12, "weapon": "axe", "armor": "light", "reward_chips": 120, "reward_exp": 100},
    {"name": "🦁 Пещерный Лев", "level": 4, "hp": 160, "atk": 30, "def": 10, "speed": 22, "crit": 18, "weapon": "bow", "armor": "medium", "reward_chips": 220, "reward_exp": 180},
    {"name": "👹 Древний Огр", "level": 5, "hp": 240, "atk": 42, "def": 16, "speed": 8, "crit": 15, "weapon": "hammer", "armor": "heavy", "reward_chips": 400, "reward_exp": 320}
]

BOSSES = [
    {"id": "dragon", "name": "🐉 Древний Дракон", "hp": 500, "atk": 65, "def": 25, "speed": 20, "crit": 25, "weapon": "staff", "armor": "legendary", "reward_chips": 1500, "reward_exp": 1000},
    {"id": "necromancer", "name": "🔮 Некромант Тьмы", "hp": 750, "atk": 90, "def": 35, "speed": 30, "crit": 30, "weapon": "staff", "armor": "legendary", "reward_chips": 3000, "reward_exp": 2000},
    {"id": "titan", "name": "🗿 Каменный Титан", "hp": 1200, "atk": 120, "def": 50, "speed": 10, "crit": 20, "weapon": "hammer", "armor": "legendary", "reward_chips": 6000, "reward_exp": 4000}
]

DUNGEONS = {
    "crypt": {"name": "🏚 Склеп", "rooms": 3, "fee": 50, "final": 250, "mult": 1.0},
    "cave": {"name": "🕳 Пещера", "rooms": 5, "fee": 150, "final": 750, "mult": 1.3},
    "castle": {"name": "🏰 Крепость", "rooms": 7, "fee": 400, "final": 2000, "mult": 1.6}
}

BODY_PARTS = {
    "head": "💥 Голова",
    "chest": "🛡 Грудь",
    "belly": "🩸 Живот",
    "legs": "🦵 Ноги"
}

# ==================== БАЗА ДАННЫХ ====================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                chips INTEGER DEFAULT 150,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                base_hp INTEGER DEFAULT 100,
                base_atk INTEGER DEFAULT 12,
                base_def INTEGER DEFAULT 2,
                speed INTEGER DEFAULT 10,
                crit INTEGER DEFAULT 10,
                weapon TEXT DEFAULT 'dagger',
                armor TEXT DEFAULT 'none',
                inventory_weapons TEXT DEFAULT 'dagger',
                inventory_armors TEXT DEFAULT 'none'
            )
        """)
        await db.commit()

async def get_player(user_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def create_player(user_id: int, username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR IGNORE INTO players (user_id, username) 
            VALUES (?, ?)
        """, (user_id, username or f"Боец_{user_id}"))
        await db.commit()

async def update_player(user_id: int, **kwargs):
    async with aiosqlite.connect(DB_NAME) as db:
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        await db.execute(f"UPDATE players SET {set_clause} WHERE user_id = ?", values)
        await db.commit()

# ==================== ВЫЧИСЛЕНИЯ СТАТИСТИКИ ====================
def calculate_stats(player: Dict[str, Any]) -> Dict[str, Any]:
    armor = ARMORS.get(player['armor'], ARMORS['none'])
    max_hp = player['base_hp'] + armor['hp_bonus']
    total_def = player['base_def'] + armor['def_bonus']
    return {
        "name": player['username'] or f"Игрок #{player['user_id']}",
        "max_hp": max_hp,
        "hp": max_hp,
        "atk": player['base_atk'],
        "def": total_def,
        "speed": player['speed'],
        "crit": player['crit'],
        "weapon": player['weapon'],
        "armor": player['armor'],
        "user_id": player['user_id']
    }

def add_exp_and_level_up(player: Dict[str, Any], exp_gained: int) -> Tuple[Dict[str, Any], bool]:
    new_exp = player['exp'] + exp_gained
    new_level = player['level']
    leveled_up = False
    
    exp_needed = new_level * 100
    while new_exp >= exp_needed:
        new_exp -= exp_needed
        new_level += 1
        player['base_hp'] += 15
        player['base_atk'] += 3
        player['base_def'] += 1
        leveled_up = True
        exp_needed = new_level * 100
        
    player['exp'] = new_exp
    player['level'] = new_level
    return player, leveled_up

def get_hp_bar(current: int, max_hp: int) -> str:
    current = max(0, current)
    percent = int((current / max_hp) * 10)
    bar = "█" * percent + "░" * (10 - percent)
    return f"[{bar}] {current}/{max_hp} HP"

# ==================== СОСТОЯНИЯ FSM ====================
class GameStates(StatesGroup):
    in_fight = State()
    casino_bet = State()
    admin_give_chips = State()

# ==================== КЛАВИАТУРЫ ====================
def main_menu_kb(user_id: int):
    kb = [
        [InlineKeyboardButton(text="⚔️ PvE (Боты)", callback_data="menu_pve"), InlineKeyboardButton(text="🤺 PvP (Игроки)", callback_data="menu_pvp")],
        [InlineKeyboardButton(text="👾 Боссы", callback_data="menu_bosses"), InlineKeyboardButton(text="🏚 Данжи", callback_data="menu_dungeons")],
        [InlineKeyboardButton(text="🎒 Персонаж", callback_data="menu_profile"), InlineKeyboardButton(text="🏪 Магазин", callback_data="menu_shop")],
        [InlineKeyboardButton(text="🎰 Казино", callback_data="menu_casino"), InlineKeyboardButton(text="🏆 Топ игроков", callback_data="menu_top")]
    ]
    if user_id == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="👑 Админ Панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_to_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="menu_main")]
    ])

def fight_attack_kb():
    buttons = []
    keys = list(BODY_PARTS.keys())
    buttons.append([InlineKeyboardButton(text=BODY_PARTS[keys[0]], callback_data=f"attack_{keys[0]}"),
                    InlineKeyboardButton(text=BODY_PARTS[keys[1]], callback_data=f"attack_{keys[1]}")])
    buttons.append([InlineKeyboardButton(text=BODY_PARTS[keys[2]], callback_data=f"attack_{keys[2]}"),
                    InlineKeyboardButton(text=BODY_PARTS[keys[3]], callback_data=f"attack_{keys[3]}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def fight_defend_kb(attack_part: str):
    buttons = []
    keys = list(BODY_PARTS.keys())
    buttons.append([InlineKeyboardButton(text=BODY_PARTS[keys[0]], callback_data=f"defend_{attack_part}_{keys[0]}"),
                    InlineKeyboardButton(text=BODY_PARTS[keys[1]], callback_data=f"defend_{attack_part}_{keys[1]}")])
    buttons.append([InlineKeyboardButton(text=BODY_PARTS[keys[2]], callback_data=f"defend_{attack_part}_{keys[2]}"),
                    InlineKeyboardButton(text=BODY_PARTS[keys[3]], callback_data=f"defend_{attack_part}_{keys[3]}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ==================== ДВИЖОК ИНТЕРАКТИВНОГО БОЯ ====================
def calculate_turn(p_stat: Dict, e_stat: Dict, p_attack: str, p_defend: str) -> Tuple[int, int, str]:
    e_attack = random.choice(list(BODY_PARTS.keys()))
    e_defend = random.choice(list(BODY_PARTS.keys()))
    
    log = []
    
    # 1. Атака Игрока
    is_e_blocked = (p_attack == e_defend)
    p_crit = random.randint(1, 100) <= p_stat['crit']
    raw_p_dmg = p_stat['atk'] * (2.0 if p_crit else 1.0)
    
    if is_e_blocked:
        p_dmg = max(1, int((raw_p_dmg - e_stat['def']) * 0.3))
        log.append(f"🎯 Вы атаковали в **{BODY_PARTS[p_attack]}**, но враг **ЗАБЛОКИРОВАЛ** урон! (-{p_dmg} HP)")
    else:
        p_dmg = max(1, int(raw_p_dmg - e_stat['def']))
        crit_str = " 💥 **КРИТ!**" if p_crit else ""
        log.append(f"⚔️ Вы успешно ударили в **{BODY_PARTS[p_attack]}**{crit_str}! (-{p_dmg} HP)")

    # 2. Атака Врага
    is_p_blocked = (e_attack == p_defend)
    e_crit = random.randint(1, 100) <= e_stat['crit']
    raw_e_dmg = e_stat['atk'] * (2.0 if e_crit else 1.0)
    
    if is_p_blocked:
        e_dmg = max(1, int((raw_e_dmg - p_stat['def']) * 0.3))
        log.append(f"🛡 Враг бился в **{BODY_PARTS[e_attack]}**, но вы **ЗАБЛОКИРОВАЛИ** удар! (-{e_dmg} HP)")
    else:
        e_dmg = max(1, int(raw_e_dmg - p_stat['def']))
        crit_str = " 💥 **КРИТ!**" if e_crit else ""
        log.append(f"🩸 Враг попал вам в **{BODY_PARTS[e_attack]}**{crit_str}! (-{e_dmg} HP)")

    return p_dmg, e_dmg, "\n".join(log)

# ==================== ХЕНДЛЕРЫ ====================
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await create_player(message.from_user.id, message.from_user.full_name)
    await message.answer(
        "⚔️ **Арена ДуэлянтовПриветствует тебя, Воин!**\n\n"
        "🔥 Настраивай билды, сражайся в асинхронном и интерактивном PvP, побеждай монстров и эпических Боссов, проходи подземелья и попытай удачу в Казино!",
        reply_markup=main_menu_kb(message.from_user.id),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "menu_main")
async def cb_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "⚔️ **Главное меню Арены**\nВыбери желаемый режим:",
        reply_markup=main_menu_kb(call.from_user.id),
        parse_mode="Markdown"
    )

# -------------------- ПРОФИЛЬ --------------------
@router.callback_query(F.data == "menu_profile")
async def cb_profile(call: CallbackQuery):
    p = await get_player(call.from_user.id)
    stats = calculate_stats(p)
    w_info = WEAPONS.get(p['weapon'], WEAPONS['dagger'])
    a_info = ARMORS.get(p['armor'], ARMORS['none'])
    
    text = (
        f"🎒 **ПРОФИЛЬ БОЙЦА**: {stats['name']}\n"
        f"🆔 ID: `{p['user_id']}`\n"
        f"🏆 Уровень: {p['level']} (EXP: {p['exp']}/{p['level']*100})\n"
        f"💰 Фишки: **{p['chips']}**\n"
        f"📊 Статистика: {p['wins']} Побед / {p['losses']} Поражений\n\n"
        f"❤️ **HP**: {stats['max_hp']}\n"
        f"⚔️ **Атака**: {stats['atk']}\n"
        f"🛡 **Защита**: {stats['def']}\n"
        f"⚡️ **Скорость**: {stats['speed']}\n"
        f"💥 **Крит**: {stats['crit']}%\n\n"
        f"🗡 **Оружие**: {w_info['name']}\n"
        f"🛡 **Броня**: {a_info['name']}"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎒 Инвентарь", callback_data="menu_inventory")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "menu_inventory")
async def cb_inventory(call: CallbackQuery):
    p = await get_player(call.from_user.id)
    inv_w = p['inventory_weapons'].split(",")
    inv_a = p['inventory_armors'].split(",")
    
    buttons = [[InlineKeyboardButton(text="--- 🗡 Сменить Оружие ---", callback_data="ignore")]]
    for w_key in inv_w:
        w = WEAPONS[w_key]
        status = " (Экипировано)" if p['weapon'] == w_key else ""
        buttons.append([InlineKeyboardButton(text=f"{w['name']}{status}", callback_data=f"equip_w_{w_key}")])
        
    buttons.append([InlineKeyboardButton(text="--- 🛡 Сменить Броню ---", callback_data="ignore")])
    for a_key in inv_a:
        a = ARMORS[a_key]
        status = " (Экипировано)" if p['armor'] == a_key else ""
        buttons.append([InlineKeyboardButton(text=f"{a['name']}{status}", callback_data=f"equip_a_{a_key}")])
        
    buttons.append([InlineKeyboardButton(text="🔙 В профиль", callback_data="menu_profile")])
    await call.message.edit_text("🎒 **Ваш Инвентарь**:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data.startswith("equip_w_"))
async def cb_equip_w(call: CallbackQuery):
    w_key = call.data.split("_")[2]
    await update_player(call.from_user.id, weapon=w_key)
    await call.answer("🗡 Оружие успешно сменено!")
    await cb_inventory(call)

@router.callback_query(F.data.startswith("equip_a_"))
async def cb_equip_a(call: CallbackQuery):
    a_key = call.data.split("_")[2]
    await update_player(call.from_user.id, armor=a_key)
    await call.answer("🛡 Броня успешно сменена!")
    await cb_inventory(call)

# -------------------- МАГАЗИН --------------------
@router.callback_query(F.data == "menu_shop")
async def cb_shop(call: CallbackQuery):
    p = await get_player(call.from_user.id)
    inv_w = p['inventory_weapons'].split(",")
    inv_a = p['inventory_armors'].split(",")
    
    text = f"🏪 **Магазин Снаряжения**\nБаланс: **{p['chips']}** 💰\n"
    buttons = [[InlineKeyboardButton(text="--- 🗡 Оружие ---", callback_data="ignore")]]
    
    for k, w in WEAPONS.items():
        if k not in inv_w:
            buttons.append([InlineKeyboardButton(text=f"{w['name']} — {w['price']}💰", callback_data=f"buy_w_{k}")])
            
    buttons.append([InlineKeyboardButton(text="--- 🛡 Броня ---", callback_data="ignore")])
    for k, a in ARMORS.items():
        if k not in inv_a:
            buttons.append([InlineKeyboardButton(text=f"{a['name']} — {a['price']}💰", callback_data=f"buy_a_{k}")])
            
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data.startswith("buy_w_"))
async def cb_buy_w(call: CallbackQuery):
    w_key = call.data.split("_")[2]
    w = WEAPONS[w_key]
    p = await get_player(call.from_user.id)
    
    if p['chips'] < w['price']:
        await call.answer("❌ Недостаточно фишек!", show_alert=True)
        return
        
    inv_w = p['inventory_weapons'].split(",")
    inv_w.append(w_key)
    await update_player(call.from_user.id, chips=p['chips'] - w['price'], inventory_weapons=",".join(inv_w), weapon=w_key)
    await call.answer(f"✅ Куплено: {w['name']}!")
    await cb_shop(call)

@router.callback_query(F.data.startswith("buy_a_"))
async def cb_buy_a(call: CallbackQuery):
    a_key = call.data.split("_")[2]
    a = ARMORS[a_key]
    p = await get_player(call.from_user.id)
    
    if p['chips'] < a['price']:
        await call.answer("❌ Недостаточно фишек!", show_alert=True)
        return
        
    inv_a = p['inventory_armors'].split(",")
    inv_a.append(a_key)
    await update_player(call.from_user.id, chips=p['chips'] - a['price'], inventory_armors=",".join(inv_a), armor=a_key)
    await call.answer(f"✅ Куплено: {a['name']}!")
    await cb_shop(call)

# -------------------- СИСТЕМА БОЯ (PVE / PVP / БОССЫ) --------------------
@router.callback_query(F.data == "menu_pve")
async def cb_pve_select(call: CallbackQuery):
    text = "⚔️ **PvE Арена**\nВыберите соперника для дуэли:"
    buttons = []
    for idx, b in enumerate(PVE_BOTS):
        buttons.append([InlineKeyboardButton(text=f"{b['name']} (Lvl {b['level']})", callback_data=f"start_fight_pve_{idx}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data == "menu_bosses")
async def cb_bosses_select(call: CallbackQuery):
    text = "👾 **Рейдовые Боссы**\nМощные противники с огромными наградами!"
    buttons = []
    for b in BOSSES:
        buttons.append([InlineKeyboardButton(text=f"{b['name']} — Награда: {b['reward_chips']}💰", callback_data=f"start_fight_boss_{b['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data == "menu_pvp")
async def cb_pvp_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("🔎 **Поиск соперника для PvP...**\nПодождите пару секунд.")
    await asyncio.sleep(2)
    
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM players WHERE user_id != ? ORDER BY RANDOM() LIMIT 1", (call.from_user.id,)) as cursor:
            opponent = await cursor.fetchone()
            
    if opponent:
        opp_dict = dict(opponent)
        enemy_stat = calculate_stats(opp_dict)
    else:
        # Если игроков нет — генерируем сильного PvP-бота
        enemy_stat = {
            "name": "🤖 PvP-Бот Бронзового Ранга",
            "max_hp": 120, "hp": 120, "atk": 18, "def": 5,
            "speed": 12, "crit": 12, "weapon": "sword", "armor": "light", "user_id": 0
        }
        
    p = await get_player(call.from_user.id)
    p_stat = calculate_stats(p)
    
    fight_data = {
        "p_stat": p_stat,
        "e_stat": enemy_stat,
        "type": "pvp",
        "reward_chips": 100,
        "reward_exp": 80
    }
    
    await state.set_state(GameStates.in_fight)
    await state.update_data(fight_data=fight_data)
    
    await render_fight_step(call.message, fight_data, "⚔️ **PvP Бой Начался! Выберите зону для атаки:**")

@router.callback_query(F.data.startswith("start_fight_pve_"))
async def cb_start_pve(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.split("_")[3])
    bot = PVE_BOTS[idx]
    p = await get_player(call.from_user.id)
    
    p_stat = calculate_stats(p)
    e_stat = {
        "name": bot['name'], "max_hp": bot['hp'], "hp": bot['hp'],
        "atk": bot['atk'], "def": bot['def'], "speed": bot['speed'],
        "crit": bot['crit'], "weapon": bot['weapon'], "armor": bot['armor'], "user_id": 0
    }
    
    fight_data = {
        "p_stat": p_stat, "e_stat": e_stat, "type": "pve",
        "reward_chips": bot['reward_chips'], "reward_exp": bot['reward_exp']
    }
    await state.set_state(GameStates.in_fight)
    await state.update_data(fight_data=fight_data)
    await render_fight_step(call.message, fight_data, f"⚔️ **Бой с {bot['name']}! Выберите зону атаки:**")

@router.callback_query(F.data.startswith("start_fight_boss_"))
async def cb_start_boss(call: CallbackQuery, state: FSMContext):
    b_id = call.data.split("_")[3]
    boss = next(b for b in BOSSES if b['id'] == b_id)
    p = await get_player(call.from_user.id)
    
    p_stat = calculate_stats(p)
    e_stat = {
        "name": boss['name'], "max_hp": boss['hp'], "hp": boss['hp'],
        "atk": boss['atk'], "def": boss['def'], "speed": boss['speed'],
        "crit": boss['crit'], "weapon": boss['weapon'], "armor": boss['armor'], "user_id": 0
    }
    
    fight_data = {
        "p_stat": p_stat, "e_stat": e_stat, "type": "boss",
        "reward_chips": boss['reward_chips'], "reward_exp": boss['reward_exp']
    }
    await state.set_state(GameStates.in_fight)
    await state.update_data(fight_data=fight_data)
    await render_fight_step(call.message, fight_data, f"👾 **РЕЙД НА БОССА: {boss['name']}! Выберите зону атаки:**")

async def render_fight_step(message: Message, fight_data: Dict, comment: str, kb=None):
    p = fight_data['p_stat']
    e = fight_data['e_stat']
    
    text = (
        f"🔴 **{p['name']}**: {get_hp_bar(p['hp'], p['max_hp'])}\n"
        f"🔵 **{e['name']}**: {get_hp_bar(e['hp'], e['max_hp'])}\n\n"
        f"{comment}"
    )
    if kb is None:
        kb = fight_attack_kb()
    await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(GameStates.in_fight, F.data.startswith("attack_"))
async def cb_fight_attack(call: CallbackQuery, state: FSMContext):
    attack_part = call.data.split("_")[1]
    data = await state.get_data()
    fight_data = data['fight_data']
    
    await render_fight_step(
        call.message, 
        fight_data, 
        f"🎯 Атака выбрана: **{BODY_PARTS[attack_part]}**.\n Теперь выберите **зону ЗАЩИТЫ**:", 
        kb=fight_defend_kb(attack_part)
    )

@router.callback_query(GameStates.in_fight, F.data.startswith("defend_"))
async def cb_fight_defend(call: CallbackQuery, state: FSMContext):
    _, attack_part, defend_part = call.data.split("_")
    data = await state.get_data()
    fight_data = data['fight_data']
    
    p_stat = fight_data['p_stat']
    e_stat = fight_data['e_stat']
    
    p_dmg, e_dmg, turn_log = calculate_turn(p_stat, e_stat, attack_part, defend_part)
    
    p_stat['hp'] -= e_dmg
    e_stat['hp'] -= p_dmg
    
    if p_stat['hp'] <= 0 or e_stat['hp'] <= 0:
        await state.clear()
        p_win = p_stat['hp'] > 0
        p_db = await get_player(call.from_user.id)
        
        if p_win:
            p_db, lvl_up = add_exp_and_level_up(p_db, fight_data['reward_exp'])
            p_db['chips'] += fight_data['reward_chips']
            p_db['wins'] += 1
            await update_player(call.from_user.id, **p_db)
            
            res_text = (
                f"🎉 **ПОБЕДА!**\n\n{turn_log}\n\n"
                f"🏆 Награда: **+{fight_data['reward_chips']}** 💰 | **+{fight_data['reward_exp']}** EXP!"
            )
            if lvl_up:
                res_text += f"\n🎊 **НОВЫЙ УРОВЕНЬ: {p_db['level']}!**"
        else:
            p_db['losses'] += 1
            await update_player(call.from_user.id, losses=p_db['losses'])
            res_text = f"💀 **ПОРАЖЕНИЕ!**\n\n{turn_log}\n\nУлучшите бронирование и оружие!"
            
        await call.message.edit_text(res_text, reply_markup=back_to_menu_kb(), parse_mode="Markdown")
    else:
        await state.update_data(fight_data=fight_data)
        await render_fight_step(call.message, fight_data, f"📝 **Результат раунда:**\n{turn_log}\n\nВыберите следующую атаку:")

# -------------------- ДАНЖИ --------------------
@router.callback_query(F.data == "menu_dungeons")
async def cb_dungeons(call: CallbackQuery):
    text = (
        "🏚 **ПОДЗЕМЕЛЬЯ**\n\n"
        "Пройдите комнаты без восстановления HP! Рискните всем ради куша."
    )
    buttons = []
    for k, d in DUNGEONS.items():
        buttons.append([InlineKeyboardButton(text=f"{d['name']} ({d['rooms']} комн.) — {d['final']}💰", callback_data=f"enter_dungeon_{k}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data.startswith("enter_dungeon_"))
async def cb_enter_dungeon(call: CallbackQuery):
    d_key = call.data.split("_")[2]
    dungeon = DUNGEONS[d_key]
    p = await get_player(call.from_user.id)
    
    if p['chips'] < dungeon['fee']:
        await call.answer("❌ Недостаточно фишек для входа!", show_alert=True)
        return
        
    p['chips'] -= dungeon['fee']
    await update_player(p['user_id'], chips=p['chips'])
    
    p_stat = calculate_stats(p)
    c_hp = p_stat['max_hp']
    log = [f"🏚 **ПОХОД В {dungeon['name'].upper()}**"]
    
    success = True
    for r in range(1, dungeon['rooms'] + 1):
        m_hp = int(35 * (1 + r * 0.25) * dungeon['mult'])
        m_atk = int(8 * (1 + r * 0.2) * dungeon['mult'])
        
        # Упрощенная симуляция комнат
        c_hp -= max(5, m_atk - p_stat['def'])
        if c_hp <= 0:
            log.append(f"💀 Вы погибли в комнате {r}...")
            success = False
            break
        else:
            log.append(f"✅ Комната {r} очищена! (Ост. HP: {c_hp}/{p_stat['max_hp']})")

    if success:
        p, lvl_up = add_exp_and_level_up(p, dungeon['rooms'] * 60)
        p['chips'] += dungeon['final']
        await update_player(p['user_id'], **p)
        log.append(f"\n🎉 **ДАНЖ ПРОЙДЕН!** Получено **+{dungeon['final']}** 💰!")
    else:
        log.append(f"\n⚰️ Поход провален!")

    await call.message.edit_text("\n".join(log), reply_markup=back_to_menu_kb(), parse_mode="Markdown")

# -------------------- КАЗИНО --------------------
@router.callback_query(F.data == "menu_casino")
async def cb_casino(call: CallbackQuery):
    text = "🎰 **КАЗИНО АРЕНЫ**\nИспытайте свою удачу и удвойте фишки!"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Слот-Машина (100💰)", callback_data="casino_slots")],
        [InlineKeyboardButton(text="🎲 Кости (50💰)", callback_data="casino_dice")],
        [InlineKeyboardButton(text="🪙 Монетка (50💰)", callback_data="casino_coin")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "casino_slots")
async def cb_casino_slots(call: CallbackQuery):
    p = await get_player(call.from_user.id)
    if p['chips'] < 100:
        await call.answer("❌ Нужно минимум 100 💰!", show_alert=True)
        return
        
    p['chips'] -= 100
    icons = ["🍎", "🍋", "7️⃣", "💎"]
    res = [random.choice(icons) for _ in range(3)]
    res_str = " | ".join(res)
    
    if res[0] == res[1] == res[2]:
        win = 500
        p['chips'] += win
        msg = f"🎰 **[{res_str}]**\n🔥 **ДЖЕКПОТ!** Вы выиграли **+{win}** 💰!"
    elif res[0] == res[1] or res[1] == res[2] or res[0] == res[2]:
        win = 150
        p['chips'] += win
        msg = f"🎰 **[{res_str}]**\n🎉 **Совпадение!** Вы выиграли **+{win}** 💰!"
    else:
        msg = f"🎰 **[{res_str}]**\n❌ Поражение! Удача улыбнётся в следующий раз."
        
    await update_player(call.from_user.id, chips=p['chips'])
    await call.message.edit_text(msg, reply_markup=back_to_menu_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "casino_dice")
async def cb_casino_dice(call: CallbackQuery):
    p = await get_player(call.from_user.id)
    if p['chips'] < 50:
        await call.answer("❌ Нужно 50 💰!", show_alert=True)
        return
        
    p['chips'] -= 50
    p_d = random.randint(1, 6)
    b_d = random.randint(1, 6)
    
    if p_d > b_d:
        p['chips'] += 100
        msg = f"🎲 Ваш бросок: **{p_d}** | Дилер: **{b_d}**\n🎉 Вы победили и получили **+100** 💰!"
    elif p_d == b_d:
        p['chips'] += 50
        msg = f"🎲 Ваши кости: **{p_d}** | Дилер: **{b_d}**\n🤝 Ничья! Ставка возвращена."
    else:
        msg = f"🎲 Ваш бросок: **{p_d}** | Дилер: **{b_d}**\n❌ Вы проиграли 50 💰!"

    await update_player(call.from_user.id, chips=p['chips'])
    await call.message.edit_text(msg, reply_markup=back_to_menu_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "casino_coin")
async def cb_casino_coin(call: CallbackQuery):
    p = await get_player(call.from_user.id)
    if p['chips'] < 50:
        await call.answer("❌ Нужно 50 💰!", show_alert=True)
        return
        
    p['chips'] -= 50
    if random.choice([True, False]):
        p['chips'] += 100
        msg = "🪙 Выпал **Орёл**! Вы удвоили ставку: **+100** 💰!"
    else:
        msg = "🪙 Выпала **Решка**! Ставка проиграна."
        
    await update_player(call.from_user.id, chips=p['chips'])
    await call.message.edit_text(msg, reply_markup=back_to_menu_kb(), parse_mode="Markdown")

# -------------------- ТОП --------------------
@router.callback_query(F.data == "menu_top")
async def cb_top(call: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT username, level, wins FROM players ORDER BY wins DESC LIMIT 10") as cursor:
            players = await cursor.fetchall()
            
    text = "🏆 **ТОП-10 БОЙЦОВ АРЕНЫ**\n\n"
    for i, pl in enumerate(players, 1):
        text += f"{i}. **{pl['username']}** — Lvl {pl['level']} | ⚔️ {pl['wins']} Побед\n"
        
    await call.message.edit_text(text, reply_markup=back_to_menu_kb(), parse_mode="Markdown")

# -------------------- АДМИН ПАНЕЛЬ --------------------
@router.callback_query(F.data == "admin_panel")
async def cb_admin_panel(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Выдать фишки себе (+5000)", callback_data="admin_add_chips")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="menu_main")]
    ])
    await call.message.edit_text("👑 **Административная панель**", reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "admin_add_chips")
async def cb_admin_add_chips(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    p = await get_player(ADMIN_ID)
    await update_player(ADMIN_ID, chips=p['chips'] + 5000)
    await call.answer("💰 Выдано 5000 фишек!", show_alert=True)
    await cb_admin_panel(call)

# ==================== ЗАПУСК ====================
async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    print("⚔️ Бот «Арена Дуэлянтов» запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
