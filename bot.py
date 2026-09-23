#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
⚔️ АРЕНА ДУЭЛЯНТОВ (DUEL ARENA) — Ultimate Edition v5.0
================================================================================
Полнофункциональный Telegram-бот для PvP дуэлей, казино, RP-действий,
боссов и системы промокодов. Поддержка чатовых команд без префикса '/'.

Требования:
    - Python 3.10+
    - aiogram >= 3.0.0
    - sqlite3 (встроен)

Особенности:
    - 9 видов оружия с уникальными эффектами
    - 24 предмета брони (6 на каждый из 4 слотов)
    - 4 босса с уникальной экипировкой
    - 20 RP-действий с кулдаунами
    - 5 игр казино (слоты, кости, монетка, рулетка, больше/меньше)
    - Система промокодов с ограничениями
    - Скрытые боты для быстрого матчмейкинга
    - Балансировка по аренам
================================================================================
"""

import asyncio
import html
import logging
import os
import random
import re
import sqlite3
import time
import traceback
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any, Union, Callable

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    User,
)

# ==============================================================================
# 1. КОНФИГУРАЦИЯ И КОНСТАНТЫ
# ==============================================================================

class Config:
    """
    Класс конфигурации бота.
    В продакшене рекомендуется использовать переменные окружения.
    """
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
    DB_PATH: str = os.getenv("DB_PATH", "arena.db")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "5356400377"))
    
    START_CHIPS: int = 500
    TURN_TIMEOUT: int = 45
    RP_COOLDOWN: int = 5
    
    LOG_LEVEL: int = logging.INFO
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"

# Премиум эмодзи (замените ID на реальные через @getidsbot)
PREMIUM_EMOJI_IDS: Dict[str, str] = {
    "fire":   "5368324170671202286",
    "sword":  "5368324170671202287",
    "coin":   "5368324170671202288",
    "chips":  "5368324170671202289",
    "trophy": "5368324170671202290",
    "skull":  "5368324170671202291",
    "shield": "5368324170671202292",
    "heart":  "5368324170671202293",
    "slot":   "5368324170671202294",
    "dice":   "5368324170671202295",
    "boss":   "5368324170671202296",
    "glove":  "5368324170671202297",
    "star":   "5368324170671202298",
    "magic":  "5368324170671202299",
    "gift":   "5368324170671202300",
    "promo":  "5368324170671202301",
}

def get_premium_emoji(key: str, fallback: str) -> str:
    """
    Генерирует HTML-тег для премиум эмодзи или возвращает fallback.
    
    Args:
        key: Ключ из словаря PREMIUM_EMOJI_IDS
        fallback: Стандартный эмодзи для отката
        
    Returns:
        Строка с HTML-тегом <tg-emoji> или fallback
    """
    eid = PREMIUM_EMOJI_IDS.get(key)
    if not eid:
        return fallback
    return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'

# Глобальные переменные эмодзи
E_FIRE   = get_premium_emoji("fire", "🔥")
E_SWORD  = get_premium_emoji("sword", "⚔️")
E_COIN   = get_premium_emoji("coin", "🪙")
E_CHIPS  = get_premium_emoji("chips", "💰")
E_TROPHY = get_premium_emoji("trophy", "🏆")
E_SKULL  = get_premium_emoji("skull", "💀")
E_SHIELD = get_premium_emoji("shield", "🛡")
E_HEART  = get_premium_emoji("heart", "❤️")
E_SLOT   = get_premium_emoji("slot", "🎰")
E_DICE   = get_premium_emoji("dice", "🎲")
E_BOSS   = get_premium_emoji("boss", "👹")
E_GLOVE  = get_premium_emoji("glove", "🧤")
E_STAR   = get_premium_emoji("star", "⭐")
E_MAGIC  = get_premium_emoji("magic", "✨")
E_GIFT   = get_premium_emoji("gift", "🎁")
E_PROMO  = get_premium_emoji("promo", "🎟")

# ==============================================================================
# 2. ИГРОВЫЕ ДАННЫЕ И КОНТЕНТ
# ==============================================================================

ZONES: List[str] = ["head", "torso", "arms", "legs"]

ZONE_INFO: Dict[str, Dict[str, Any]] = {
    "head":  dict(name="Голова", emoji="🧠", mult=1.5, desc="Высокий урон, сложно попасть"),
    "torso": dict(name="Торс",   emoji="🫀", mult=1.0, desc="Средний урон, стандартная цель"),
    "arms":  dict(name="Руки",   emoji="💪", mult=0.8, desc="Низкий урон, высокая точность"),
    "legs":  dict(name="Ноги",   emoji="🦵", mult=0.9, desc="Средний урон, шанс замедлить"),
}

WEAPONS: Dict[str, Dict[str, Any]] = {
    "fists":  dict(emoji="👊", name="Кулаки", dmg=10, price=0, chance=25, effect="triple", spec="Серия ударов", desc="3 быстрых удара по 50% урона"),
    "dagger": dict(emoji="🗡", name="Кинжал", dmg=14, price=200, chance=30, effect="triple", spec="Тысяча порезов", desc="3 удара по 50% урона"),
    "sword":  dict(emoji="⚔️", name="Меч", dmg=20, price=500, chance=28, effect="exec", spec="Казнь", desc="Двойной урон по выбранной зоне"),
    "axe":    dict(emoji="🪓", name="Топор", dmg=26, price=800, chance=24, effect="bleed", spec="Кровопускание", desc="Кровотечение: 4% макс. HP, 3 раунда"),
    "bow":    dict(emoji="🏹", name="Лук", dmg=32, price=1200, chance=22, effect="pierce", spec="Снайперский выстрел", desc="Игнорирует 50% защиты брони"),
    "staff":  dict(emoji="🔥", name="Посох", dmg=38, price=1700, chance=22, effect="burn", spec="Огненный шторм", desc="Горение: 40% от урона, 3 раунда"),
    "hammer": dict(emoji="🔨", name="Молот", dmg=46, price=2500, chance=18, effect="stun", spec="Землетрясение", desc="×2 урона и оглушение на 1 ход"),
    "spear":  dict(emoji="🔱", name="Копье", dmg=28, price=950, chance=26, effect="pierce", spec="Пронзающий выпад", desc="Игнорирует 30% защиты, высокий шанс"),
    "whip":   dict(emoji="🪢", name="Кнут", dmg=18, price=600, chance=35, effect="stun", spec="Хлесткий удар", desc="Низкий урон, но высокий шанс оглушить"),
}

ARMOR_DATA: Dict[str, List[Dict[str, Any]]] = {
    "head": [
        dict(key="head_none", name="Без шлема", emoji="👕", df=0, hp=0, price=0, chance=0, dmg_bonus=0, desc="Полная уязвимость"),
        dict(key="head_leather", name="Кожаный капюшон", emoji="🧢", df=2, hp=3, price=120, chance=3, dmg_bonus=0, desc="+3% шанс спец-атаки"),
        dict(key="head_iron", name="Железный шлем", emoji="⛑", df=4, hp=8, price=380, chance=0, dmg_bonus=0, desc="Базовая защита головы"),
        dict(key="head_steel", name="Стальной шлем", emoji="🪖", df=7, hp=15, price=850, chance=0, dmg_bonus=10, desc="+10% урон спец-атаки"),
        dict(key="head_dragon", name="Драконий шлем", emoji="🐲", df=11, hp=25, price=1800, chance=8, dmg_bonus=20, desc="+8% шанс, +20% урон спец-атаки"),
        dict(key="head_crown", name="Корона Лорда", emoji="👑", df=14, hp=30, price=3000, chance=12, dmg_bonus=25, desc="Максимальная защита и престиж"),
    ],
    "torso": [
        dict(key="torso_none", name="Без брони", emoji="👕", df=0, hp=0, price=0, chance=0, dmg_bonus=0, desc="Полная уязвимость"),
        dict(key="torso_robe", name="Мантия", emoji="🥋", df=3, hp=5, price=150, chance=4, dmg_bonus=0, desc="+4% шанс спец-атаки"),
        dict(key="torso_chain", name="Кольчуга", emoji="🛡", df=6, hp=12, price=480, chance=0, dmg_bonus=0, desc="Надежная защита корпуса"),
        dict(key="torso_plate", name="Латный доспех", emoji="🏋️", df=11, hp=22, price=1000, chance=0, dmg_bonus=15, desc="+15% урон спец-атаки"),
        dict(key="torso_titan", name="Титановый панцирь", emoji="✨", df=17, hp=35, price=2200, chance=10, dmg_bonus=25, desc="+10% шанс, +25% урон спец-атаки"),
        dict(key="torso_aegis", name="Эгида", emoji="🌟", df=22, hp=45, price=3500, chance=15, dmg_bonus=30, desc="Легендарная защита"),
    ],
    "arms": [
        dict(key="arms_none", name="Без наручей", emoji="👕", df=0, hp=0, price=0, chance=0, dmg_bonus=0, desc="Полная уязвимость"),
        dict(key="arms_cloth", name="Тканевые бинты", emoji="🩹", df=2, hp=2, price=100, chance=3, dmg_bonus=0, desc="+3% шанс спец-атаки"),
        dict(key="arms_iron", name="Железные наручи", emoji="🛡", df=4, hp=8, price=350, chance=0, dmg_bonus=0, desc="Базовая защита рук"),
        dict(key="arms_steel", name="Стальные латы", emoji="⚙️", df=7, hp=14, price=800, chance=0, dmg_bonus=10, desc="+10% урон спец-атаки"),
        dict(key="arms_runic", name="Рунические наручи", emoji="🔮", df=11, hp=22, price=1700, chance=8, dmg_bonus=20, desc="+8% шанс, +20% урон спец-атаки"),
        dict(key="arms_berserk", name="Наручи Берсерка", emoji="🩸", df=9, hp=18, price=1500, chance=5, dmg_bonus=35, desc="-2 защиты, но +35% урона"),
    ],
    "legs": [
        dict(key="legs_none", name="Без поножей", emoji="👕", df=0, hp=0, price=0, chance=0, dmg_bonus=0, desc="Полная уязвимость"),
        dict(key="legs_cloth", name="Тканевые штаны", emoji="👖", df=2, hp=3, price=110, chance=3, dmg_bonus=0, desc="+3% шанс спец-атаки"),
        dict(key="legs_iron", name="Железные поножи", emoji="🛡", df=5, hp=10, price=400, chance=0, dmg_bonus=0, desc="Базовая защита ног"),
        dict(key="legs_steel", name="Стальные поножи", emoji="⚙️", df=8, hp=16, price=900, chance=0, dmg_bonus=10, desc="+10% урон спец-атаки"),
        dict(key="legs_demon", name="Демонические поножи", emoji="😈", df=12, hp=25, price=1900, chance=8, dmg_bonus=20, desc="+8% шанс, +20% урон спец-атаки"),
        dict(key="legs_wind", name="Поножи Ветра", emoji="💨", df=6, hp=12, price=1100, chance=10, dmg_bonus=5, desc="Высокая мобильность, +10% шанс уворота"),
    ],
}

START_ARMOR_KEYS: List[str] = ["head_none", "torso_none", "arms_none", "legs_none"]
BASE_STATS: Dict[str, int] = dict(hp=150)

ARENAS: Dict[str, Dict[str, Any]] = {
    "bronze": dict(name="Бронзовая арена", emoji="🥉", min_wins=0, max_wins=9, prize=50, color="#cd7f32"),
    "silver": dict(name="Серебряная арена", emoji="🥈", min_wins=10, max_wins=29, prize=100, color="#c0c0c0"),
    "gold": dict(name="Золотая арена", emoji="🥇", min_wins=30, max_wins=10**9, prize=200, color="#ffd700"),
}
ARENA_ORDER: List[str] = ["bronze", "silver", "gold"]

BOSSES: Dict[str, Dict[str, Any]] = {
    "goblin": dict(
        key="goblin", name="👺 Гоблин-Вождь", 
        desc="Хитрый и злой. Бьёт по слабой броне, использует кинжал.", 
        hp=160, weapon="dagger", 
        armor_keys={"head": "head_leather", "torso": "torso_robe", "arms": "arms_none", "legs": "legs_none"}, 
        reward_mult=3, min_wins=0
    ),
    "dragon": dict(
        key="dragon", name="🐉 Древний Дракон", 
        desc="Огнедышащий ужас. Оружие — посох, драконья чешуя вместо брони.", 
        hp=260, weapon="staff", 
        armor_keys={"head": "head_steel", "torso": "torso_plate", "arms": "arms_iron", "legs": "legs_iron"}, 
        reward_mult=5, min_wins=5
    ),
    "lord": dict(
        key="lord", name="👹 Древний Лорд", 
        desc="Владыка арены. Молот разрушения и полная драконья экипировка.", 
        hp=380, weapon="hammer", 
        armor_keys={"head": "head_dragon", "torso": "torso_titan", "arms": "arms_runic", "legs": "legs_demon"}, 
        reward_mult=10, min_wins=15
    ),
    "titan": dict(
        key="titan", name="🗿 Каменный Титан", 
        desc="Неуязвимая глыба. Огромная защита, но медленные атаки.", 
        hp=500, weapon="fists", 
        armor_keys={"head": "head_crown", "torso": "torso_aegis", "arms": "arms_berserk", "legs": "legs_wind"}, 
        reward_mult=15, min_wins=35
    ),
}

# ==============================================================================
# 3. УТИЛИТЫ И UI ХЕЛПЕРЫ
# ==============================================================================

def esc(text: str) -> str:
    """Безопасное экранирование HTML-тегов в пользовательском вводе."""
    return html.escape(str(text))

def create_button(text: str, callback_data: str) -> InlineKeyboardButton:
    """
    Создает Inline-кнопку.
    
    Args:
        text: Текст на кнопке
        callback_data: Данные для обработки нажатия
        
    Returns:
        Объект InlineKeyboardButton
    """
    return InlineKeyboardButton(text=text, callback_data=callback_data)

def build_inline_keyboard(*rows: List[Tuple[str, str]]) -> InlineKeyboardMarkup:
    """
    Строит Inline-клавиатуру из кортежей (текст, callback_data).
    
    Args:
        *rows: Переменное количество строк, каждая строка — список кортежей
        
    Returns:
        Объект InlineKeyboardMarkup
    """
    keyboard = []
    for row in rows:
        keyboard.append([create_button(item[0], item[1]) for item in row])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def safe_edit_message(
    cb: CallbackQuery, 
    text: str, 
    markup: Optional[InlineKeyboardMarkup] = None
) -> bool:
    """
    Безопасно редактирует сообщение, обрабатывая ошибки 'not modified'.
    
    Args:
        cb: Объект CallbackQuery
        text: Новый текст сообщения
        markup: Новая клавиатура (опционально)
        
    Returns:
        True если успешно, False если произошла критическая ошибка
    """
    try:
        await cb.message.edit_text(text[:4090], reply_markup=markup, parse_mode=ParseMode.HTML)
        return True
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            return True
        try:
            await cb.message.answer(text[:4090], reply_markup=markup, parse_mode=ParseMode.HTML)
            return True
        except Exception as fallback_err:
            logging.error(f"Critical fallback error in safe_edit_message: {fallback_err}")
            return False
    except Exception as e:
        logging.error(f"Unexpected error in safe_edit_message: {e}")
        return False

# ==============================================================================
# 4. СИСТЕМА БАЗЫ ДАННЫХ (SQLite Wrapper)
# ==============================================================================

class DatabaseManager:
    """
    Менеджер базы данных для управления состоянием игроков, уведомлений,
    статистики и промокодов.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Инициализирует схему базы данных при первом запуске."""
        schema = """
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY, 
                username TEXT, 
                name TEXT NOT NULL, 
                chips INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0, 
                losses INTEGER NOT NULL DEFAULT 0, 
                weapon TEXT NOT NULL DEFAULT 'fists',
                armor_head TEXT NOT NULL DEFAULT 'head_none', 
                armor_torso TEXT NOT NULL DEFAULT 'torso_none',
                armor_arms TEXT NOT NULL DEFAULT 'arms_none', 
                armor_legs TEXT NOT NULL DEFAULT 'legs_none',
                weapons_owned TEXT NOT NULL DEFAULT 'fists', 
                armors_owned TEXT NOT NULL DEFAULT 'head_none,torso_none,arms_none,legs_none',
                banned INTEGER NOT NULL DEFAULT 0, 
                is_bot INTEGER NOT NULL DEFAULT 0, 
                created REAL NOT NULL DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                user_id INTEGER NOT NULL, 
                text TEXT NOT NULL, 
                ts REAL NOT NULL, 
                seen INTEGER NOT NULL DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                reward_chips INTEGER NOT NULL DEFAULT 0,
                reward_wins INTEGER NOT NULL DEFAULT 0,
                max_uses INTEGER NOT NULL DEFAULT 1,
                current_uses INTEGER NOT NULL DEFAULT 0,
                expires_at REAL NOT NULL DEFAULT 0,
                created_by INTEGER NOT NULL,
                created_at REAL NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS promo_activations (
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                activated_at REAL NOT NULL,
                PRIMARY KEY (user_id, code)
            );
            
            CREATE INDEX IF NOT EXISTS ix_notif_user ON notifications(user_id, seen);
            CREATE INDEX IF NOT EXISTS ix_players_wins ON players(wins, is_bot, banned);
            CREATE INDEX IF NOT EXISTS ix_promo_active ON promo_codes(active, expires_at);
            CREATE INDEX IF NOT EXISTS ix_promo_act_user ON promo_activations(user_id);
        """
        try:
            self._connection.executescript(schema)
            logging.info("Database schema initialized successfully.")
        except sqlite3.Error as e:
            logging.critical(f"Failed to initialize database schema: {e}")
            raise

    def fetch_one(self, sql: str, args: tuple = ()) -> Optional[sqlite3.Row]:
        """Выполняет SELECT запрос и возвращает одну строку."""
        try:
            return self._connection.execute(sql, args).fetchone()
        except sqlite3.Error as e:
            logging.error(f"DB fetch_one error: {e} | SQL: {sql} | Args: {args}")
            return None

    def fetch_all(self, sql: str, args: tuple = ()) -> List[sqlite3.Row]:
        """Выполняет SELECT запрос и возвращает все строки."""
        try:
            return self._connection.execute(sql, args).fetchall()
        except sqlite3.Error as e:
            logging.error(f"DB fetch_all error: {e} | SQL: {sql} | Args: {args}")
            return []

    def execute(self, sql: str, args: tuple = ()) -> bool:
        """Выполняет модифицирующий запрос (INSERT, UPDATE, DELETE)."""
        try:
            self._connection.execute(sql, args)
            return True
        except sqlite3.Error as e:
            logging.error(f"DB execute error: {e} | SQL: {sql} | Args: {args}")
            return False

    def close(self) -> None:
        """Закрывает соединение с базой данных."""
        if self._connection:
            self._connection.close()

# Глобальный экземпляр БД
db = DatabaseManager(Config.DB_PATH)

# ==============================================================================
# 5. МОДЕЛИ ДАННЫХ: БОЕЦ И ДУЭЛЬ
# ==============================================================================

@dataclass
class Fighter:
    """
    Представление бойца в бою.
    Содержит текущие и максимальные характеристики, экипировку и статусы.
    """
    name: str
    max_hp: int
    hp: int
    weapon: str
    armor_slots: Dict[str, str] = field(default_factory=dict)
    dots: List[Dict[str, Any]] = field(default_factory=list)
    stun: bool = False

    def __post_init__(self) -> None:
        """Валидация и расчет бонусов после инициализации."""
        if self.weapon not in WEAPONS:
            self.weapon = "fists"
        
        w = WEAPONS[self.weapon]
        self.weapon_dmg = w["dmg"]

        slots = self.armor_slots or {}
        fixed_slots = {}
        for s in ZONES:
            key = slots.get(s) or f"{s}_none"
            if not get_armor_item_by_key(key):
                key = f"{s}_none"
            fixed_slots[s] = key
        self.armor_slots = fixed_slots

        self.armor_def = {}
        total_chance = 0
        total_bonus = 0
        
        for slot in ZONES:
            key = self.armor_slots[slot]
            item = get_armor_item_by_key(key) or get_armor_item_by_key(f"{slot}_none")
            self.armor_def[slot] = item["df"]
            total_chance += item["chance"]
            total_bonus += item["dmg_bonus"]

        self.spec_chance = min(w["chance"] + total_chance, 70)
        self.spec_dmg_bonus = total_bonus / 100.0

    def is_alive(self) -> bool:
        """Проверяет, жив ли боец (HP > 0)."""
        return self.hp > 0

    def get_armor_def(self, zone: str) -> int:
        """Возвращает значение защиты для конкретной зоны."""
        return self.armor_def.get(zone, 0)

    def get_weapon_dmg_for_zone(self, zone: str) -> int:
        """Рассчитывает базовый урон оружия по конкретной зоне с учетом множителя."""
        return max(1, round(self.weapon_dmg * ZONE_INFO[zone]["mult"]))

def get_armor_item_by_key(key: str) -> Optional[Dict[str, Any]]:
    """Поиск предмета брони по ключу во всем массиве данных."""
    for slot, items in ARMOR_DATA.items():
        for it in items:
            if it["key"] == key:
                return {**it, "slot": slot}
    return None

def generate_hp_bar(fighter: Fighter, width: int = 12) -> str:
    """Генерирует визуальную полосу здоровья."""
    if fighter.max_hp <= 0:
        return "⬛" * width
    
    filled = max(0, min(width, int(round(width * fighter.hp / fighter.max_hp))))
    ratio = fighter.hp / fighter.max_hp
    
    if ratio > 0.6:
        char = "🟩"
    elif ratio > 0.3:
        char = "🟨"
    else:
        char = "🟥"
        
    return char * filled + "⬛" * (width - filled)

def format_fighter_card(fighter: Fighter) -> str:
    """Форматирует информацию о бойце для отображения в чате."""
    w = WEAPONS[fighter.weapon]
    ad = fighter.armor_def
    return (
        f"│ <b>{fighter.name}</b>\n"
        f"│ {E_HEART} <b>{fighter.hp}</b>/{fighter.max_hp}  {generate_hp_bar(fighter)}\n"
        f"│ {w['emoji']} {w['name']} · урон {fighter.weapon_dmg}\n"
        f"│ {E_SHIELD} 🧠{ad['head']} 🫀{ad['torso']} 💪{ad['arms']} 🦵{ad['legs']}"
    )

@dataclass
class Duel:
    """
    Состояние активной дуэли.
    Управляет ходами, таймерами, логами и специальными состояниями.
    """
    a_id: int
    b_id: int
    a: Fighter
    b: Fighter
    attacker_is_a: bool = True
    round_no: int = 1
    atk_zone: Optional[str] = None
    log: List[str] = field(default_factory=list)
    started: float = field(default_factory=time.time)
    is_boss: bool = False
    boss_key: Optional[str] = None
    reward_mult: int = 1
    finished: bool = False
    
    bot_last_block_round: int = -10
    bot_block_streak: int = 0
    
    timer_task: Optional[asyncio.Task] = None
    timer_deadline: float = 0.0
    timer_for: Optional[int] = None
    timer_role: Optional[str] = None

    def get_state_for(self, uid: int) -> str:
        """Определяет роль пользователя в текущем раунде."""
        if uid == self.a_id:
            return "attacker" if self.attacker_is_a else "defender"
        if uid == self.b_id:
            return "defender" if self.attacker_is_a else "attacker"
        return "none"

    def get_attacker(self) -> Fighter:
        return self.a if self.attacker_is_a else self.b

    def get_defender(self) -> Fighter:
        return self.b if self.attacker_is_a else self.a

    def get_attacker_id(self) -> int:
        return self.a_id if self.attacker_is_a else self.b_id

    def get_defender_id(self) -> int:
        return self.b_id if self.attacker_is_a else self.a_id

    def get_fighter(self, uid: int) -> Optional[Fighter]:
        return self.a if uid == self.a_id else (self.b if uid == self.b_id else None)

    def get_opponent(self, uid: int) -> Optional[Fighter]:
        return self.b if uid == self.a_id else (self.a if uid == self.b_id else None)

# Глобальное хранилище активных дуэлей
ACTIVE_DUELS: Dict[int, Duel] = {}

# ==============================================================================
# 6. БОЕВАЯ ЛОГИКА И МЕХАНИКИ
# ==============================================================================

def calculate_damage(
    attacker: Fighter, 
    defender: Fighter, 
    atk_zone: str, 
    def_zone: Optional[str],
    ignore_armor: bool = False, 
    extra_mult: float = 1.0
) -> Tuple[int, str]:
    """
    Рассчитывает итоговый урон с учетом брони, зон и множителей.
    
    Returns:
        Кортеж (нанесенный урон, строка примечания)
    """
    if def_zone == atk_zone:
        return 0, f"{E_SHIELD} <b>Блок!</b>"
    
    weapon_dmg = attacker.get_weapon_dmg_for_zone(atk_zone)
    armor = 0 if ignore_armor else defender.get_armor_def(atk_zone)
    
    raw_dmg = weapon_dmg - armor
    final_dmg = max(1, round(raw_dmg * extra_mult))
    
    return final_dmg, ""

def process_dots(fighter: Fighter, log: List[str]) -> None:
    """Обрабатывает периодический урон (яд, горение, кровотечение)."""
    for dot in list(fighter.dots):
        fighter.hp = max(0, fighter.hp - dot["dmg"])
        log.append(f"{dot['name']}: {fighter.name} −{dot['dmg']} HP")
        dot["left"] -= 1
        
        if dot["left"] <= 0:
            fighter.dots.remove(dot)
            
        if fighter.hp <= 0:
            log.append(f"☠️ {fighter.name} гибнет от эффектов")
            return

def apply_dot_effect(target: Fighter, name: str, dmg: int, rounds: int) -> None:
    """Накладывает или обновляет эффект периодического урона."""
    target.dots = [d for d in target.dots if d["name"] != name]
    target.dots.append({"name": name, "dmg": dmg, "left": rounds})

def resolve_special_attack(
    attacker: Fighter, 
    defender: Fighter, 
    atk_zone: str, 
    def_zone: Optional[str], 
    log: List[str]
) -> bool:
    """
    Пытается применить специальную атаку оружия.
    
    Returns:
        True, если спец-атака была применена, False иначе
    """
    w = WEAPONS[attacker.weapon]
    
    if def_zone == atk_zone:
        log.append(f"{E_SHIELD} {defender.name} заблокировал <b>{w['spec']}</b>")
        return True

    effect = w["effect"]
    
    if effect == "triple":
        hits = [max(1, round(calculate_damage(attacker, defender, atk_zone, def_zone)[0] * 0.5)) for _ in range(3)]
        total_dmg = sum(hits)
        defender.hp = max(0, defender.hp - total_dmg)
        log.append(f"{w['emoji']} <b>{w['spec']}</b>: {' + '.join(map(str, hits))} = <b>−{total_dmg}</b>")
        return True
        
    elif effect == "exec":
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, extra_mult=2.0)
        defender.hp = max(0, defender.hp - dmg)
        log.append(f"{E_SWORD} <b>{w['spec']}</b>: {attacker.name} → {defender.name} [{ZONE_INFO[atk_zone]['emoji']}] <b>−{dmg}</b>")
        return True
        
    elif effect == "bleed":
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone)
        defender.hp = max(0, defender.hp - dmg)
        bleed_dmg = max(1, round(defender.max_hp * 0.04))
        apply_dot_effect(defender, "🩸 Кровотечение", bleed_dmg, 3)
        log.append(f"🪓 <b>{w['spec']}</b>: −{dmg}, кровь по <b>{bleed_dmg}</b> ×3 раунда")
        return True
        
    elif effect == "pierce":
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, ignore_armor=True, extra_mult=1.5)
        defender.hp = max(0, defender.hp - dmg)
        log.append(f"🏹 <b>{w['spec']}</b>: {attacker.name} пробивает броню на <b>−{dmg}</b>")
        return True
        
    elif effect == "burn":
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone)
        defender.hp = max(0, defender.hp - dmg)
        burn_dmg = max(1, round(dmg * 0.4))
        apply_dot_effect(defender, f"{E_FIRE} Горение", burn_dmg, 3)
        log.append(f"{E_FIRE} <b>{w['spec']}</b>: −{dmg}, огонь по <b>{burn_dmg}</b> ×3 раунда")
        return True
        
    elif effect == "stun":
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, extra_mult=2.0)
        defender.hp = max(0, defender.hp - dmg)
        defender.stun = True
        log.append(f"🔨 <b>{w['spec']}</b>: {attacker.name} оглушает цель на <b>−{dmg}</b>")
        return True

    return False

def execute_attack_phase(
    attacker: Fighter, 
    defender: Fighter, 
    atk_zone: str, 
    def_zone: Optional[str], 
    log: List[str]
) -> None:
    """Выполняет полный цикл атаки: проверка оглушения -> спец-атака -> обычная атака."""
    if attacker.stun:
        attacker.stun = False
        log.append(f"💫 {attacker.name} оглушён и пропускает ход!")
        return

    if random.random() * 100 < attacker.spec_chance:
        if resolve_special_attack(attacker, defender, atk_zone, def_zone, log):
            return

    dmg, note = calculate_damage(attacker, defender, atk_zone, def_zone)
    if note:
        log.append(f"{ZONE_INFO[atk_zone]['emoji']} {attacker.name} бьёт в «{ZONE_INFO[atk_zone]['name']}» — {note}")
    else:
        defender.hp = max(0, defender.hp - dmg)
        log.append(f"👊 {attacker.name} → {defender.name} [{ZONE_INFO[atk_zone]['emoji']}] <b>−{dmg}</b>")

# ==============================================================================
# 7. УПРАВЛЕНИЕ ДУЭЛЬЮ И ТАЙМЕРАМИ
# ==============================================================================

def stop_duel_timer(duel: Duel) -> None:
    """Безопасно останавливает и очищает задачу таймера дуэли."""
    if duel.timer_task and not duel.timer_task.done():
        duel.timer_task.cancel()
    duel.timer_task = None
    duel.timer_deadline = 0.0
    duel.timer_for = None
    duel.timer_role = None

def terminate_duel(duel: Duel) -> None:
    """Завершает дуэль и удаляет её из глобального хранилища."""
    duel.finished = True
    stop_duel_timer(duel)
    ACTIVE_DUELS.pop(duel.a_id, None)
    if duel.b_id > 0:
        ACTIVE_DUELS.pop(duel.b_id, None)

def start_duel_timer(duel: Duel, uid: int, role: str, bot: Bot) -> None:
    """Инициализирует таймер хода для конкретного игрока."""
    if uid < 0:
        return
    stop_duel_timer(duel)
    duel.timer_for = uid
    duel.timer_role = role
    duel.timer_deadline = time.time() + Config.TURN_TIMEOUT
    duel.timer_task = asyncio.create_task(_timer_runner_task(duel, uid, role, bot))

async def _timer_runner_task(duel: Duel, uid: int, role: str, bot: Bot) -> None:
    """Асинхронная задача, отслеживающая истечение времени хода."""
    try:
        while True:
            if duel.finished:
                return
            time_left = int(round(duel.timer_deadline - time.time()))
            if time_left <= 0:
                break
            await asyncio.sleep(1)
            
        if duel.finished or duel.timer_for != uid or duel.get_state_for(uid) != role:
            return
        if uid not in ACTIVE_DUELS:
            return
            
        await handle_timeout_defeat(duel, uid, bot)
        
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Critical error in duel timer for user {uid}: {e}\n{traceback.format_exc()}")

async def handle_timeout_defeat(duel: Duel, loser_uid: int, bot: Bot) -> None:
    """Обрабатывает автоматическое поражение из-за таймаута."""
    loser = duel.get_fighter(loser_uid)
    duel.log.append(f"⏱ <b>{loser.name if loser else 'Неизвестный'} не успел за {Config.TURN_TIMEOUT} сек — авто-поражение!</b>")
    
    winner_is_a = not (loser_uid == duel.a_id)
    await finalize_duel(duel, winner_is_a=winner_is_a, bot=bot, reason="timeout")

# ==============================================================================
# 8. ИИ БОТА И ГЕНЕРАЦИЯ СОПЕРНИКОВ
# ==============================================================================

def get_player_armor_slots(player_row: sqlite3.Row) -> Dict[str, str]:
    """Извлекает и валидирует слоты брони из записи БД."""
    if not player_row:
        return {s: f"{s}_none" for s in ZONES}
    return {
        "head":  player_row["armor_head"] or "head_none",
        "torso": player_row["armor_torso"] or "torso_none",
        "arms":  player_row["armor_arms"] or "arms_none",
        "legs":  player_row["armor_legs"] or "legs_none",
    }

def create_fighter_from_db(player_row: sqlite3.Row) -> Fighter:
    """Создает объект Fighter на основе данных из БД."""
    slots = get_player_armor_slots(player_row)
    total_hp = BASE_STATS["hp"]
    
    for key in slots.values():
        item = get_armor_item_by_key(key)
        if item:
            total_hp += item.get("hp", 0)
            
    return Fighter(
        name=esc(player_row["name"]),
        max_hp=total_hp,
        hp=total_hp,
        weapon=player_row["weapon"] if player_row["weapon"] in WEAPONS else "fists",
        armor_slots=slots,
    )

def create_boss_fighter(boss_data: Dict[str, Any]) -> Fighter:
    """Создает объект Fighter для босса."""
    return Fighter(
        name=boss_data["name"],
        max_hp=boss_data["hp"],
        hp=boss_data["hp"],
        weapon=boss_data["weapon"],
        armor_slots=boss_data["armor_keys"],
    )

def determine_arena(wins: int) -> str:
    """Определяет текущую арену игрока на основе количества побед."""
    for k in ARENA_ORDER:
        a = ARENAS[k]
        if a["min_wins"] <= wins <= a["max_wins"]:
            return k
    return "gold"

def generate_random_bot_name(existing_names: set) -> str:
    """Генерирует уникальное имя для скрытого бота."""
    human_names = ["Максим", "Артём", "Данил", "Кирилл", "Егор", "Иван", "Никита", "Рома", "Саня", "Дима", "Влад", "Серёга", "Паша", "Толя", "Женя", "Костя", "Лёха", "Миша", "Гриша", "Стас", "Олег", "Ден", "Марк", "Тимур", "Алина", "Катя", "Настя", "Даша", "Лера", "Соня", "Вика", "Полина", "Крис", "Милана", "Аня", "Юля", "Оля", "Маша", "Ксюша", "Ника"]
    titles = ["", "", "", "xd", "pro", "god", "real", "top", "_", "007", "tvoy", "cz"]
    
    for _ in range(300):
        base = random.choice(human_names)
        title = random.choice(titles)
        suffix = str(random.randint(1, 99)) if random.random() < 0.35 else ""
        name = f"{base}{title}{suffix}"
        
        if name.lower() not in existing_names and 2 <= len(name) <= 16:
            existing_names.add(name.lower())
            return name
            
    return f"Игрок{random.randint(1000, 9999)}"

def ensure_masked_bots_exist(target_count: int = 50) -> None:
    """
    Гарантирует наличие минимального количества скрытых ботов в базе данных
    для быстрого матчмейкинга.
    """
    existing_names = {r["name"].lower() for r in db.fetch_all("SELECT name FROM players")}
    bots = db.fetch_all("SELECT user_id, wins FROM players WHERE is_bot=1")
    need = max(0, target_count - len(bots))
    
    for _ in range(need):
        name = generate_random_bot_name(existing_names)
        uid = -random.randint(10_000_000, 99_999_999)
        
        wins = random.choices(
            [random.randint(0, 9), random.randint(10, 29), random.randint(30, 60)], 
            weights=[5, 4, 2]
        )[0]
        losses = random.randint(max(0, wins // 2), wins * 2 + 3)
        arena_key = determine_arena(wins)
        
        if arena_key == "bronze":
            weapon = random.choice(["fists", "dagger", "sword"])
            tier_max = 2
        elif arena_key == "silver":
            weapon = random.choice(["sword", "axe", "bow", "spear"])
            tier_max = 3
        else:
            weapon = random.choice(["bow", "staff", "hammer", "spear", "whip"])
            tier_max = 4
            
        slots = {}
        for s in ZONES:
            items = ARMOR_DATA[s]
            idx = min(random.randint(0, tier_max), len(items) - 1)
            slots[s] = items[idx]["key"]
            
        owned_armors = set(list(slots.values()) + START_ARMOR_KEYS)
        
        db.execute("""
            INSERT INTO players (user_id, username, name, chips, wins, losses, weapon, 
            armor_head, armor_torso, armor_arms, armor_legs, weapons_owned, armors_owned, is_bot, created) 
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            uid, None, name, random.randint(0, 400), wins, losses, weapon,
            slots["head"], slots["torso"], slots["arms"], slots["legs"],
            weapon, ",".join(owned_armors), 1, time.time()
        ))

def pick_balanced_opponent(player_uid: int, player_wins: int) -> Optional[int]:
    """
    Подбирает соперника строго того же уровня (арены), что и игрок.
    """
    arena = determine_arena(player_wins)
    limits = ARENAS[arena]
    
    humans = [r["user_id"] for r in db.fetch_all("""
        SELECT user_id FROM players 
        WHERE user_id != ? AND banned=0 AND is_bot=0 AND wins BETWEEN ? AND ? 
        ORDER BY RANDOM() LIMIT 6
    """, (player_uid, limits["min_wins"], limits["max_wins"]))]
    
    bots = [r["user_id"] for r in db.fetch_all("""
        SELECT user_id FROM players 
        WHERE is_bot=1 AND banned=0 AND wins BETWEEN ? AND ? 
        ORDER BY RANDOM() LIMIT 6
    """, (limits["min_wins"], limits["max_wins"]))]
    
    if humans and bots:
        return random.choice(bots if random.random() < 0.6 else humans)
    if humans:
        return random.choice(humans)
    if bots:
        return random.choice(bots)
    
    ensure_masked_bots_exist(10)
    rows = db.fetch_all("""
        SELECT user_id FROM players 
        WHERE is_bot=1 AND wins BETWEEN ? AND ? 
        ORDER BY RANDOM() LIMIT 1
    """, (limits["min_wins"], limits["max_wins"]))
    
    return rows[0]["user_id"] if rows else None

# ==============================================================================
# 9. ИСКУССТВЕННЫЙ ИНТЕЛЛЕКТ БОТА В БОЮ
# ==============================================================================

def bot_decide_attack_zone(attacker: Fighter, defender: Fighter) -> str:
    """Логика выбора зоны атаки для бота."""
    if random.random() < 0.10:
        return random.choice(ZONES)
    
    if defender.hp <= defender.max_hp * 0.30:
        return max(ZONES, key=lambda z: attacker.get_weapon_dmg_for_zone(z))

    def score_zone(z: str) -> tuple:
        dmg = attacker.get_weapon_dmg_for_zone(z) - defender.get_armor_def(z)
        return (dmg, ZONE_INFO[z]["mult"])
        
    return max(ZONES, key=score_zone)

def bot_decide_to_defend(duel: Duel, bot_is_a: bool) -> bool:
    """Определяет, будет ли бот пытаться блокировать атаку."""
    if duel.bot_block_streak >= 2:
        return False
    if duel.round_no - duel.bot_last_block_round < 3:
        return False
        
    bot_fighter = duel.a if bot_is_a else duel.b
    hp_ratio = bot_fighter.hp / bot_fighter.max_hp
    
    if hp_ratio < 0.30:
        base_chance = 0.65
    elif hp_ratio < 0.60:
        base_chance = 0.40
    else:
        base_chance = 0.25
        
    return random.random() < base_chance

def bot_decide_defend_zone(attacker: Fighter, defender: Fighter) -> str:
    """Выбирает зону для защиты, основываясь на наиболее опасной зоне атаки."""
    def danger_level(z: str) -> int:
        return attacker.get_weapon_dmg_for_zone(z) - defender.get_armor_def(z)
        
    sorted_zones = sorted(ZONES, key=danger_level, reverse=True)
    
    if random.random() < 0.25 and len(sorted_zones) > 1:
        return sorted_zones[1]
    return sorted_zones[0]

# ==============================================================================
# 10. КАЗИНО И ЭКОНОМИКА
# ==============================================================================

def play_casino_slots(uid: int, bet: int) -> Tuple[Optional[str], Optional[str]]:
    """Логика игры в слоты."""
    p = db.fetch_one("SELECT chips FROM players WHERE user_id=?", (uid,))
    if not p or p["chips"] < bet:
        return None, "Недостаточно фишек на балансе."
        
    symbols = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣"]
    weights = [25, 22, 20, 15, 12, 6]
    spin = random.choices(symbols, weights=weights, k=3)
    
    db.execute("UPDATE players SET chips=chips-? WHERE user_id=?", (bet, uid))
    
    if spin[0] == spin[1] == spin[2]:
        mult = {"7️⃣": 10, "💎": 8}.get(spin[0], 5)
        win = bet * mult
        db.execute("UPDATE players SET chips=chips+? WHERE user_id=?", (win, uid))
        return f"{' | '.join(spin)}\n\n{E_TROPHY} <b>ДЖЕКПОТ ×{mult}!</b>\nВы выиграли: +{win}💰", None
        
    if spin[0] == spin[1] or spin[1] == spin[2] or spin[0] == spin[2]:
        win = int(bet * 2)
        db.execute("UPDATE players SET chips=chips+? WHERE user_id=?", (win, uid))
        return f"{' | '.join(spin)}\n\n✅ <b>Пара!</b>\nВы выиграли: +{win}💰", None
        
    return f"{' | '.join(spin)}\n\n{E_SKULL} <b>Мимо.</b>\nВы проиграли: −{bet}💰", None

def play_casino_dice(uid: int, bet: int) -> Tuple[Optional[str], Optional[str]]:
    """Логика игры в кости."""
    p = db.fetch_one("SELECT chips FROM players WHERE user_id=?", (uid,))
    if not p or p["chips"] < bet:
        return None, "Недостаточно фишек на балансе."
        
    player_roll = random.randint(1, 6)
    dealer_roll = random.randint(1, 6)
    
    db.execute("UPDATE players SET chips=chips-? WHERE user_id=?", (bet, uid))
    
    if player_roll > dealer_roll:
        win = bet * 2
        db.execute("UPDATE players SET chips=chips+? WHERE user_id=?", (win, uid))
        return f"{E_DICE} Ты: {player_roll} · Дилер: {dealer_roll}\n\n{E_TROPHY} <b>Победа!</b> +{win}💰", None
    elif player_roll == dealer_roll:
        db.execute("UPDATE players SET chips=chips+? WHERE user_id=?", (bet, uid))
        return f"{E_DICE} Ты: {player_roll} · Дилер: {dealer_roll}\n\n🤝 <b>Ничья.</b> Ставка возвращена.", None
    else:
        return f"{E_DICE} Ты: {player_roll} · Дилер: {dealer_roll}\n\n{E_SKULL} <b>Поражение.</b> −{bet}💰", None

def play_casino_coin(uid: int, bet: int, choice: str = "heads") -> Tuple[Optional[str], Optional[str]]:
    """Логика игры в монетку."""
    p = db.fetch_one("SELECT chips FROM players WHERE user_id=?", (uid,))
    if not p or p["chips"] < bet:
        return None, "Недостаточно фишек на балансе."
        
    result = random.choice(["heads", "tails"])
    db.execute("UPDATE players SET chips=chips-? WHERE user_id=?", (bet, uid))
    
    result_text = "Орёл" if result == "heads" else "Решка"
    
    if result == choice:
        win = bet * 2
        db.execute("UPDATE players SET chips=chips+? WHERE user_id=?", (win, uid))
        return f"{E_COIN} Выпало: <b>{result_text}</b>\n\n{E_TROPHY} <b>Победа!</b> +{win}💰", None
    else:
        return f"{E_COIN} Выпало: <b>{result_text}</b>\n\n{E_SKULL} <b>Поражение.</b> −{bet}💰", None

def play_casino_roulette(uid: int, bet: int, color: str = "red") -> Tuple[Optional[str], Optional[str]]:
    """Логика игры в упрощенную рулетку."""
    p = db.fetch_one("SELECT chips FROM players WHERE user_id=?", (uid,))
    if not p or p["chips"] < bet:
        return None, "Недостаточно фишек на балансе."
        
    reds = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    num = random.randint(0, 36)
    
    if num == 0:
        res_color = "green"
    elif num in reds:
        res_color = "red"
    else:
        res_color = "black"
        
    db.execute("UPDATE players SET chips=chips-? WHERE user_id=?", (bet, uid))
    
    if color == res_color:
        mult = 14 if color == "green" else 2
        win = bet * mult
        db.execute("UPDATE players SET chips=chips+? WHERE user_id=?", (win, uid))
        return f"🎡 Выпало: <b>{num} ({res_color})</b>\n\n{E_TROPHY} <b>Победа ×{mult}!</b> +{win}💰", None
    else:
        return f"🎡 Выпало: <b>{num} ({res_color})</b>\n\n{E_SKULL} <b>Поражение.</b> −{bet}💰", None

def play_casino_highlow(uid: int, bet: int, choice: str = "high") -> Tuple[Optional[str], Optional[str]]:
    """Логика игры Больше/Меньше (число от 1 до 100)."""
    p = db.fetch_one("SELECT chips FROM players WHERE user_id=?", (uid,))
    if not p or p["chips"] < bet:
        return None, "Недостаточно фишек на балансе."
        
    result_num = random.randint(1, 100)
    db.execute("UPDATE players SET chips=chips-? WHERE user_id=?", (bet, uid))
    
    is_high = result_num > 50
    is_low = result_num < 50
    
    win = False
    if choice == "high" and is_high: win = True
    elif choice == "low" and is_low: win = True
    elif result_num == 50:
        db.execute("UPDATE players SET chips=chips+? WHERE user_id=?", (bet, uid))
        return f"📊 Выпало число: <b>{result_num}</b>\n\n🤝 <b>Ровно 50!</b> Ставка возвращена.", None
        
    if win:
        payout = int(bet * 1.9)
        db.execute("UPDATE players SET chips=chips+? WHERE user_id=?", (payout, uid))
        return f"📊 Выпало число: <b>{result_num}</b>\n\n{E_TROPHY} <b>Победа!</b> +{payout}💰", None
    else:
        return f"📊 Выпало число: <b>{result_num}</b>\n\n{E_SKULL} <b>Поражение.</b> −{bet}💰", None

# ==============================================================================
# 11. СИСТЕМА ПРОМОКОДОВ
# ==============================================================================

def create_promo_code(
    code: str,
    reward_chips: int,
    reward_wins: int,
    max_uses: int,
    hours_valid: int,
    created_by: int
) -> Tuple[bool, str]:
    """
    Создает новый промокод.
    
    Args:
        code: Уникальный код (будет приведен к верхнему регистру)
        reward_chips: Награда в фишках
        reward_wins: Награда в победах
        max_uses: Максимальное количество активаций
        hours_valid: Срок действия в часах
        created_by: ID админа, создавшего код
        
    Returns:
        Кортеж (успех, сообщение)
    """
    code = code.strip().upper()
    
    if not code or len(code) < 3 or len(code) > 20:
        return False, "Код должен быть от 3 до 20 символов."
    
    if not re.match(r'^[A-Z0-9_-]+$', code):
        return False, "Код может содержать только буквы, цифры, _ и -"
    
    if reward_chips < 0 or reward_wins < 0:
        return False, "Награды не могут быть отрицательными."
    
    if max_uses < 1:
        return False, "Максимум активаций должен быть ≥ 1."
    
    if hours_valid < 1:
        return False, "Срок действия должен быть ≥ 1 часа."
    
    existing = db.fetch_one("SELECT code FROM promo_codes WHERE code=?", (code,))
    if existing:
        return False, f"Промокод <code>{code}</code> уже существует."
    
    now = time.time()
    expires_at = now + (hours_valid * 3600)
    
    db.execute("""
        INSERT INTO promo_codes (code, reward_chips, reward_wins, max_uses, current_uses, expires_at, created_by, created_at, active)
        VALUES (?, ?, ?, ?, 0, ?, ?, ?, 1)
    """, (code, reward_chips, reward_wins, max_uses, expires_at, created_by, now))
    
    return True, f"{E_PROMO} Промокод <code>{code}</code> создан!\n\n💰 Фишки: {reward_chips}\n🏆 Победы: {reward_wins}\n👥 Макс. активаций: {max_uses}\n⏳ Действует: {hours_valid} ч."

def deactivate_promo_code(code: str) -> Tuple[bool, str]:
    """Деактивирует промокод."""
    code = code.strip().upper()
    existing = db.fetch_one("SELECT * FROM promo_codes WHERE code=?", (code,))
    if not existing:
        return False, "Промокод не найден."
    
    db.execute("UPDATE promo_codes SET active=0 WHERE code=?", (code,))
    return True, f"{E_PROMO} Промокод <code>{code}</code> деактивирован."

def get_promo_info(code: str) -> Optional[Dict[str, Any]]:
    """Получает информацию о промокоде."""
    code = code.strip().upper()
    row = db.fetch_one("SELECT * FROM promo_codes WHERE code=?", (code,))
    if not row:
        return None
    
    now = time.time()
    is_expired = row["expires_at"] < now
    is_maxed = row["current_uses"] >= row["max_uses"]
    
    return {
        "code": row["code"],
        "reward_chips": row["reward_chips"],
        "reward_wins": row["reward_wins"],
        "max_uses": row["max_uses"],
        "current_uses": row["current_uses"],
        "expires_at": row["expires_at"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "active": bool(row["active"]),
        "is_expired": is_expired,
        "is_maxed": is_maxed,
        "is_valid": row["active"] and not is_expired and not is_maxed,
    }

def activate_promo_code(user_id: int, code: str) -> Tuple[bool, str]:
    """
    Активирует промокод для игрока.
    
    Args:
        user_id: ID игрока
        code: Код для активации
        
    Returns:
        Кортеж (успех, сообщение)
    """
    code = code.strip().upper()
    
    player = db.fetch_one("SELECT * FROM players WHERE user_id=?", (user_id,))
    if not player:
        return False, "Сначала отправь /start в ЛС бота."
    
    if player["banned"]:
        return False, "🚫 Тебе недоступна активация промокодов."
    
    promo = get_promo_info(code)
    if not promo:
        return False, f"❌ Промокод <code>{code}</code> не найден."
    
    if not promo["active"]:
        return False, f"❌ Промокод <code>{code}</code> деактивирован администратором."
    
    if promo["is_expired"]:
        return False, f"❌ Промокод <code>{code}</code> истёк."
    
    if promo["is_maxed"]:
        return False, f"❌ Промокод <code>{code}</code> исчерпан (все активации использованы)."
    
    already_activated = db.fetch_one(
        "SELECT 1 FROM promo_activations WHERE user_id=? AND code=?",
        (user_id, code)
    )
    if already_activated:
        return False, f"❌ Ты уже активировал промокод <code>{code}</code>."
    
    now = time.time()
    
    try:
        db.execute(
            "INSERT INTO promo_activations (user_id, code, activated_at) VALUES (?, ?, ?)",
            (user_id, code, now)
        )
        db.execute(
            "UPDATE promo_codes SET current_uses=current_uses+1 WHERE code=?",
            (code,)
        )
        
        if promo["reward_chips"] > 0:
            db.execute(
                "UPDATE players SET chips=chips+? WHERE user_id=?",
                (promo["reward_chips"], user_id)
            )
        
        if promo["reward_wins"] > 0:
            db.execute(
                "UPDATE players SET wins=wins+? WHERE user_id=?",
                (promo["reward_wins"], user_id)
            )
        
        rewards = []
        if promo["reward_chips"] > 0:
            rewards.append(f"💰 +{promo['reward_chips']} фишек")
        if promo["reward_wins"] > 0:
            rewards.append(f"🏆 +{promo['reward_wins']} побед")
        
        rewards_text = "\n".join(rewards) if rewards else "🎁 Секретный бонус!"
        
        return True, (
            f"{E_GIFT} <b>ПРОМОКОД АКТИВИРОВАН!</b>\n\n"
            f"🎟 Код: <code>{code}</code>\n"
            f"{rewards_text}\n\n"
            f"📊 Осталось активаций: {promo['max_uses'] - promo['current_uses'] - 1}/{promo['max_uses']}"
        )
        
    except sqlite3.Error as e:
        logging.error(f"Error activating promo code: {e}")
        return False, "❌ Произошла ошибка при активации. Попробуй позже."

def list_active_promos() -> List[Dict[str, Any]]:
    """Возвращает список всех активных промокодов."""
    rows = db.fetch_all("""
        SELECT * FROM promo_codes 
        WHERE active=1 
        ORDER BY created_at DESC
    """)
    
    result = []
    now = time.time()
    for row in rows:
        is_expired = row["expires_at"] < now
        is_maxed = row["current_uses"] >= row["max_uses"]
        result.append({
            "code": row["code"],
            "reward_chips": row["reward_chips"],
            "reward_wins": row["reward_wins"],
            "max_uses": row["max_uses"],
            "current_uses": row["current_uses"],
            "expires_at": row["expires_at"],
            "created_by": row["created_by"],
            "is_expired": is_expired,
            "is_maxed": is_maxed,
            "is_valid": not is_expired and not is_maxed,
        })
    
    return result

def format_promo_info(promo: Dict[str, Any]) -> str:
    """Форматирует информацию о промокоде для отображения."""
    expires_str = time.strftime("%d.%m.%Y %H:%M", time.localtime(promo["expires_at"]))
    
    status = "✅ Активен" if promo["is_valid"] else ("⏰ Истёк" if promo["is_expired"] else ("🚫 Исчерпан" if promo["is_maxed"] else "❌ Деактивирован"))
    
    return (
        f"{E_PROMO} <b>Промокод: <code>{promo['code']}</code></b>\n\n"
        f"📊 Статус: {status}\n"
        f"💰 Награда фишками: <b>{promo['reward_chips']}</b>\n"
        f"🏆 Награда победами: <b>{promo['reward_wins']}</b>\n"
        f"👥 Активаций: <b>{promo['current_uses']}</b> / {promo['max_uses']}\n"
        f"⏰ Истекает: {expires_str}\n"
        f"🛠 Создан админом: <code>{promo['created_by']}</code>"
    )

# ==============================================================================
# 12. RP (ROLEPLAY) СИСТЕМА
# ==============================================================================

RP_ACTIONS: Dict[str, Tuple[str, str]] = {
    "ударить": ("👊", "ударил(а)"),
    "обнять": ("🤗", "обнял(а)"),
    "поцеловать": ("😘", "поцеловал(а)"),
    "пнуть": ("🦵", "пнул(а)"),
    "погладить": ("🤚", "погладил(а)"),
    "укусить": ("😬", "укусил(а)"),
    "пожать": ("🤝", "пожал(а) руку"),
    "толкнуть": ("💥", "толкнул(а)"),
    "кинуть": ("🥊", "кинул(а) в"),
    "лечить": ("💊", "подлечил(а)"),
    "игнорировать": ("💅", "проигнорировал(а)"),
    "смеяться": ("😂", "посмеялся(ась) над"),
    "плакать": ("😭", "заплакал(а) у ног"),
    "танцевать": ("💃", "станцевал(а) для"),
    "шлепнуть": ("👋", "шлепнул(а)"),
    "обозвать": ("🤬", "обозвал(а)"),
    "восхититься": ("😍", "восхитился(ась)"),
    "испугаться": ("😱", "испугался(ась)"),
    "подмигнуть": ("😉", "подмигнул(а)"),
    "пожать_плечами": ("🤷", "пожал(а) плечами при виде"),
}

RP_COOLDOWNS: Dict[Tuple[int, int, str], float] = {}

def generate_rp_text(actor_name: str, target_name: str, action_key: str) -> str:
    """Генерирует отформатированный текст RP-действия."""
    emoji, verb = RP_ACTIONS.get(action_key, ("✨", "взаимодействовал(а) с"))
    return f"{emoji} <b>{esc(actor_name)}</b> {verb} <b>{esc(target_name)}</b>!"

# ==============================================================================
# 13. УНИВЕРСАЛЬНЫЙ ПАРСЕР ЦЕЛЕЙ
# ==============================================================================

def resolve_command_target(m: Message, command_word: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Универсальная функция для определения цели команды в чате.
    Поддерживает: 1. Reply. 2. @username. 3. Числовой ID.
    """
    if m.reply_to_message and m.reply_to_message.from_user and not m.reply_to_message.from_user.is_bot:
        return m.reply_to_message.from_user.id, None

    text = m.text or ""
    if text.lower().startswith(command_word.lower()):
        rest_of_text = text[len(command_word):].strip()
    else:
        rest_of_text = text

    match = re.search(r'@(\w+)|(-?\d+)', rest_of_text)
    if match:
        val = match.group(1) or match.group(2)
        
        if val.lstrip('-').isdigit():
            row = db.fetch_one("SELECT user_id FROM players WHERE user_id=? AND banned=0", (int(val),))
            if row:
                return row["user_id"], None
        else:
            row = db.fetch_one(
                "SELECT user_id FROM players WHERE (LOWER(username)=LOWER(?) OR LOWER(name)=LOWER(?)) AND banned=0 LIMIT 1",
                (val, val)
            )
            if row:
                return row["user_id"], None
                
    if m.chat.type == "private":
        return None, f"Укажи цель: ответь на сообщение или напиши <code>{command_word} @user</code> / <code>{command_word} ID</code>"
    else:
        return None, f"⚠️ В группе команда работает <b>только ответом</b> на сообщение игрока или через <code>@username</code> / <code>ID</code>."

# ==============================================================================
# 14. ГЕНЕРАТОРЫ UI ЭКРАНОВ
# ==============================================================================

def generate_gear_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует экран управления снаряжением."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
        
    w = WEAPONS[p["weapon"]]
    f = create_fighter_from_db(p)
    slots = get_player_armor_slots(p)
    
    lines = [
        f"🎒 <b>{esc(p['name'])}</b>", "",
        f"{E_TROPHY} Победы: <b>{p['wins']}</b>  ·  {E_SKULL} Поражения: {p['losses']}",
        f"{E_CHIPS} Фишки: <b>{p['chips']}</b>",
        f"📍 {ARENAS[determine_arena(p['wins'])]['emoji']} {ARENAS[determine_arena(p['wins'])]['name']}", "",
        f"❤️ HP: <b>{f.max_hp}</b>   ⚔️ Атака: <b>{f.weapon_dmg}</b>", "",
        "<b>⚔️ Оружие:</b>", 
        f"  {w['emoji']} {w['name']} — <i>{w['spec']}</i> (урон <b>{w['dmg']}</b>, шанс {w['chance']}%)", "",
        "<b>🛡 Броня по слотам:</b>"
    ]
    
    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"  {ZONE_INFO[slot]['emoji']} {ZONE_INFO[slot]['name']}: {item['emoji']} <b>{item['name']}</b> (защита {item['df']})")
        
    kb = build_inline_keyboard(
        [("⚔️ Оружие", "gear:w"), ("🛡 Броня", "gear:armor_menu")],
        [("👤 Мой профиль", "duel:myprofile")]
    )
    return "\n".join(lines), kb

def generate_arena_menu_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует главное меню арены."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
        
    key = determine_arena(p["wins"])
    a = ARENAS[key]
    
    text = (
        f"╔══════════════════════════╗\n      ⚔️ <b>АРЕНА ДУЭЛЯНТОВ</b>\n╚══════════════════════════╝\n\n"
        f"{E_TROPHY} Победы: <b>{p['wins']}</b>  ·  {E_SKULL} Поражения: {p['losses']}\n"
        f"{E_CHIPS} Фишки: <b>{p['chips']}</b>\n📍 {a['emoji']} <b>{a['name']}</b>\n\n"
        f"🥉 Бронза — 0–9 побед  ·  <b>{ARENAS['bronze']['prize']}💰</b>\n"
        f"🥈 Серебро — 10–29 побед  ·  <b>{ARENAS['silver']['prize']}💰</b>\n"
        f"🥇 Золото — 30+ побед  ·  <b>{ARENAS['gold']['prize']}💰</b>\n\n"
        "<b>📜 Правила боя:</b>\n"
        f"• Атакующий выбирает зону удара — <b>{Config.TURN_TIMEOUT} сек</b>\n"
        f"• Защищающийся — зону защиты — <b>{Config.TURN_TIMEOUT} сек</b>\n"
        "• Совпало → блок. Иначе урон = оружие − броня зоны\n"
        "• Бой идёт <b>до 0 HP</b> у одного из бойцов\n"
        "• <i>Поражение: только −1 🏆, без награды</i>"
    )
    
    kb = build_inline_keyboard(
        [("🎲 Найти соперника", "arena:find"), ("👹 Боссы", "arena:bosses")],
        [("📋 Список соперников", "arena:list"), ("🔎 Вызвать по нику", "arena:find_name")],
        [("🏆 Топ арен", "top:cur"), ("👤 Мой профиль", "duel:myprofile")]
    )
    return text, kb

def generate_bosses_menu_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует экран выбора босса."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
        
    lines = ["╔══════════════════════════╗\n      👹 <b>БОССЫ АРЕНЫ</b>\n╚══════════════════════════╝\n"]
    rows = []
    
    for bkey, b in BOSSES.items():
        locked = p["wins"] < b["min_wins"]
        lock_text = f"🔒 нужен {b['min_wins']} {E_TROPHY}" if locked else f"награда ×{b['reward_mult']}"
        lines.append(f"{b['name']}\n  ❤️ HP {b['hp']} · ⚔️ {WEAPONS[b['weapon']]['name']}\n  {b['desc']}\n  → {lock_text}\n")
        rows.append([(b["name"] if not locked else f"{b['name']} 🔒", f"arena:boss:{bkey}")])
        
    rows.append([("⬅️ Назад", "arena:menu")])
    return "\n".join(lines), build_inline_keyboard(*rows)

def generate_profile_text(row: sqlite3.Row) -> str:
    """Генерирует текстовое описание профиля игрока."""
    if not row:
        return "Профиль не найден."
        
    w = WEAPONS[row["weapon"]] if row["weapon"] in WEAPONS else WEAPONS["fists"]
    f = create_fighter_from_db(row)
    slots = get_player_armor_slots(row)
    arena = ARENAS[determine_arena(row["wins"])]
    
    lines = [
        f"👤 <b>{esc(row['name'])}</b>", "",
        f"{E_TROPHY} {row['wins']}  ·  {E_SKULL} {row['losses']}  ·  {E_CHIPS} {row['chips']}",
        f"📍 {arena['emoji']} {arena['name']}", "",
        f"❤️ HP: <b>{f.max_hp}</b>", 
        f"{w['emoji']} {w['name']} — урон <b>{w['dmg']}</b>", "", 
        "<b>🛡 Броня:</b>"
    ]
    
    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"  {ZONE_INFO[slot]['emoji']} {ZONE_INFO[slot]['name']}: {item['emoji']} {item['name']} ({item['df']})")
        
    return "\n".join(lines)

def generate_duel_status_text(duel: Duel, for_uid: int, extra: str = "", timer_left: Optional[int] = None) -> str:
    """Генерирует статус боя для конкретного участника."""
    role = duel.get_state_for(for_uid)
    atk_name = duel.get_attacker().name
    me = duel.get_fighter(for_uid) or duel.a
    opp = duel.get_opponent(for_uid) or duel.b

    if role == "attacker":
        prompt = "🎯 <b>Твой ход</b> — выбери, куда бить"
    elif role == "defender":
        prompt = f"{E_SHIELD} <b>{atk_name}</b> атакует — выбери, что защищать"
    else:
        prompt = "⏳ Бой идёт…"

    if timer_left is not None and role in ("attacker", "defender"):
        prompt += f"\n⏱ Осталось: <b>{timer_left} сек</b>"

    body = "\n".join(f"  {ln}" for ln in duel.log[-5:]) if duel.log else "  <i>Бой начинается…</i>"
    boss_line = f"{E_BOSS} <b>БОЙ С БОССОМ</b>  ·  награда ×{duel.reward_mult}\n\n" if duel.is_boss else ""

    return (
        f"╔══════════════════════════╗\n      ⚔️ <b>РАУНД {duel.round_no}</b>\n╚══════════════════════════╝\n\n"
        f"{boss_line}┌─ 🔵 <b>ТЫ</b>\n{format_fighter_card(me)}\n└────────────\n\n"
        f"┌─ 🔴 <b>СОПЕРНИК</b>\n{format_fighter_card(opp)}\n└────────────\n\n"
        f"📜 <b>Последние действия:</b>\n{body}\n\n━━━━━━━━━━━━━━━━━━━━\n{prompt}" + (f"\n\n{extra}" if extra else "")
    )

def get_attack_zone_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора зоны атаки."""
    return build_inline_keyboard(
        [("🧠 Голова ×1.5", "duel:atk:head"), ("🫀 Торс ×1.0", "duel:atk:torso")],
        [("💪 Руки ×0.8", "duel:atk:arms"), ("🦵 Ноги ×0.9", "duel:atk:legs")]
    )

def get_defend_zone_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора зоны защиты."""
    return build_inline_keyboard(
        [("🧠 Голова", "duel:def:head"), ("🫀 Торс", "duel:def:torso")],
        [("💪 Руки", "duel:def:arms"), ("🦵 Ноги", "duel:def:legs")]
    )

def get_finish_duel_kb() -> InlineKeyboardMarkup:
    """Клавиатура окончания боя."""
    return build_inline_keyboard(
        [("🔁 Ещё раз", "duel:again")],
        [("🏠 В главное меню", "arena:menu")]
    )

# ==============================================================================
# 15. ХЕНДЛЕРЫ: СТАРТ, МЕНЮ, ПОМОЩЬ
# ==============================================================================

router = Router()

class RegistrationState(StatesGroup):
    waiting_for_name = State()

class DuelFindState(StatesGroup):
    waiting_for_target = State()

HELP_TEXT = (
    "╔══════════════════════════╗\n   ⚔️ <b>АРЕНА ДУЭЛЯНТОВ</b>\n╚══════════════════════════╝\n\n"
    "<b>📌 Как использовать команды в чате:</b>\n"
    "• Ответь на сообщение игрока командой\n"
    "• Или напиши: <code>команда @username</code> / <code>команда ID</code>\n\n"
    "<b>⚔️ Дуэли:</b>\n"
    "• <code>перчатка</code> или <code>перч</code> — вызвать на бой\n"
    "• <code>фото</code> или <code>профиль</code> — статистика игрока\n\n"
    "<b>🎰 Казино (в чате):</b>\n"
    "• <code>слоты [сумма]</code> или <code>сл [сумма]</code>\n"
    "• <code>кости [сумма]</code> или <code>кост [сумма]</code>\n"
    "• <code>монетка [сумма] [орел/решка]</code> или <code>мон [сумма] [о/р]</code>\n"
    "• <code>рулетка [сумма] [красное/черное/зеленое]</code> или <code>рул [сумма] [к/ч/з]</code>\n"
    "• <code>больше [сумма]</code> или <code>меньше [сумма]</code>\n\n"
    "<b>🎟 Промокоды:</b>\n"
    "• <code>#код [промокод]</code> или <code>активировать [код]</code> — активировать\n"
    "• <code>промо</code> — список активных промокодов\n\n"
    "<b>🎭 RP действия:</b>\n"
    "• <code>ударить</code>, <code>уд</code> | <code>обнять</code>, <code>обн</code>\n"
    "• <code>поцеловать</code>, <code>поц</code> | <code>пнуть</code>, <code>пн</code>\n"
    "• <code>погладить</code>, <code>погл</code> | <code>укусить</code>, <code>ук</code>\n"
    "• <code>пожать</code>, <code>пож</code> | <code>толкнуть</code>, <code>толк</code>\n"
    "• <code>кинуть</code>, <code>кин</code> | <code>лечить</code>, <code>леч</code>\n"
    "• <code>игнор</code>, <code>смеяться</code>, <code>плакать</code>, <code>танцевать</code>\n\n"
    "<b>👑 Админ:</b>\n"
    "• <code>бан</code> / <code>разбан</code>\n"
    "• <code>выдать [сумма]</code>\n"
    "• <code>очки [число]</code> | <code>винрейт [число]</code>\n"
    "• <code>стоп</code> | <code>рассылка [текст]</code> | <code>ботов [число]</code>\n"
    "• <code>промо создать [код] [фишки] [победы] [макс] [часов]</code>\n"
    "• <code>промо удалить [код]</code>\n"
    "• <code>промо инфо [код]</code>\n"
    "• <code>промо список</code>"
)

@router.message(CommandStart())
async def handle_start_command(m: Message, state: FSMContext) -> None:
    """Обрабатывает команду /start."""
    await state.clear()
    ensure_masked_bots_exist(50)
    
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if p:
        db.execute("UPDATE players SET username=? WHERE user_id=?", (m.from_user.username, m.from_user.id))
        if m.chat.type == "private":
            await m.answer(f"С возвращением, <b>{esc(p['name'])}</b>! Арена ждёт 👇", reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="⚔️ Арена"), KeyboardButton(text="🎰 Казино")],
                    [KeyboardButton(text="🎒 Снаряжение"), KeyboardButton(text="🏆 Топ")],
                ],
                resize_keyboard=True,
            ))
            await flush_notifications(m)
        else:
            await m.answer(f"С возвращением, <b>{esc(p['name'])}</b>! Пиши <code>help</code> для списка команд.")
        return
        
    await state.set_state(RegistrationState.waiting_for_name)
    await m.answer(
        "⚔️ <b>Добро пожаловать на Арену Дуэлянтов!</b>\n\n"
        "PvP + казино + боссы + промокоды.\n"
        "Уникальная броня на 4 части тела и множество видов оружия.\n\n"
        "Как зовут твоего бойца? (2–16 символов)", 
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(RegistrationState.waiting_for_name, F.text)
async def handle_registration_name(m: Message, state: FSMContext) -> None:
    """Обрабатывает ввод имени при регистрации."""
    name = " ".join(m.text.split())
    if not 2 <= len(name) <= 16 or name.startswith("/"):
        await m.answer("Имя должно быть от 2 до 16 символов и не начинаться с '/'. Попробуй ещё раз:")
        return
        
    if db.fetch_one("SELECT 1 FROM players WHERE LOWER(name)=LOWER(?)", (name,)):
        name = f"{name}{random.randint(1, 99)}"
        
    db.execute("""
        INSERT OR IGNORE INTO players (user_id, username, name, chips, wins, losses, weapon, 
        armor_head, armor_torso, armor_arms, armor_legs, weapons_owned, armors_owned, created) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        m.from_user.id, m.from_user.username, name, Config.START_CHIPS, 0, 0, "fists", 
        "head_none", "torso_none", "arms_none", "legs_none", "fists", ",".join(START_ARMOR_KEYS), time.time()
    ))
    
    ensure_masked_bots_exist(50)
    await state.clear()
    await m.answer(
        f"Боец <b>{esc(name)}</b> создан! 🎉\n\n"
        f"{E_CHIPS} Стартовый баланс: {Config.START_CHIPS}\n"
        f"{E_PROMO} Активируй промокоды командой <code>#код [код]</code>", 
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⚔️ Арена"), KeyboardButton(text="🎰 Казино")],
                [KeyboardButton(text="🎒 Снаряжение"), KeyboardButton(text="🏆 Топ")],
            ],
            resize_keyboard=True,
        ) if m.chat.type == "private" else None
    )

@router.message(F.text.regexp(r"(?i)^(help|помощь|хелп)$"))
async def handle_help_command(m: Message) -> None:
    """Обрабатывает команду помощи."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        await m.answer("Сначала отправь /start в ЛС бота.")
        return
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚔️ Арена"), KeyboardButton(text="🎰 Казино")],
            [KeyboardButton(text="🎒 Снаряжение"), KeyboardButton(text="🏆 Топ")],
        ],
        resize_keyboard=True,
    ) if m.chat.type == "private" else None
    await m.answer(HELP_TEXT, reply_markup=kb)

async def flush_notifications(m: Message) -> None:
    """Выводит непрочитанные уведомления игрока."""
    rows = db.fetch_all("SELECT id, text FROM notifications WHERE user_id=? AND seen=0 ORDER BY id LIMIT 15", (m.from_user.id,))
    if not rows:
        return
        
    ids = [r["id"] for r in rows]
    if ids:
        placeholders = ",".join("?" * len(ids))
        db.execute(f"UPDATE notifications SET seen=1 WHERE id IN ({placeholders})", tuple(ids))
        
    await m.answer("📬 <b>Пока тебя не было:</b>\n\n" + "\n\n".join(r["text"] for r in rows))

# ==============================================================================
# 16. ХЕНДЛЕРЫ: ЧАТОВЫЕ КОМАНДЫ
# ==============================================================================

def is_admin(uid: int) -> bool:
    return uid == Config.ADMIN_ID

def is_user_banned(uid: int) -> bool:
    p = db.fetch_one("SELECT banned FROM players WHERE user_id=?", (uid,))
    return bool(p and p["banned"])

def notify_player(uid: int, text: str) -> None:
    """Добавляет уведомление для игрока в БД."""
    if uid <= 0:
        return
    db.execute("INSERT INTO notifications (user_id, text, ts) VALUES (?,?,?)", (uid, text, time.time()))

# --- ДУЭЛИ ---
@router.message(F.text.regexp(r"(?i)^(перчатка|перч|glove|вызов)(\s|$)"))
async def cmd_challenge_duel(m: Message, bot: Bot) -> None:
    """Обработка вызова на дуэль."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        await m.answer("Сначала отправь /start в ЛС бота.")
        return
        
    command_word = m.text.split()[0]
    tid, err = resolve_command_target(m, command_word)
    if err:
        await m.answer(err)
        return
    if tid == m.from_user.id:
        await m.answer("🤨 Нельзя вызвать себя на дуэль.")
        return
        
    target = db.fetch_one("SELECT * FROM players WHERE user_id=?", (tid,))
    if not target:
        await m.answer("Игрок не найден в базе данных.")
        return
    if target["banned"]:
        await m.answer("Этот игрок забанен и не может участвовать в боях.")
        return
        
    if tid < 0:
        await initiate_duel_message(m.from_user.id, tid, m, bot)
    else:
        attacker_row = db.fetch_one("SELECT name FROM players WHERE user_id=?", (m.from_user.id,))
        attacker_name = attacker_row["name"] if attacker_row else "Неизвестный"
        notify_player(tid, f"{E_GLOVE} <b>{esc(attacker_name)}</b> кинул тебе перчатку! Открой бота для принятия вызова.")
        await m.answer(f"{E_GLOVE} Ты кинул перчатку <b>{esc(target['name'])}</b>. Ожидай ответа в ЛС.")

@router.message(F.text.regexp(r"(?i)^(фото|профиль|stat)(\s|$)"))
async def cmd_show_profile(m: Message) -> None:
    """Показывает профиль игрока."""
    row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not row:
        await m.answer("Сначала /start в ЛС бота.")
        return
        
    command_word = m.text.split()[0]
    tid, err = resolve_command_target(m, command_word)
    
    if tid:
        target_row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (tid,))
        if target_row:
            await m.answer(generate_profile_text(target_row))
            return
            
    await m.answer(generate_profile_text(row))

# --- RP ДЕЙСТВИЯ ---
async def process_rp_action(m: Message, action_key: str) -> None:
    """Обрабатывает RP-действие с проверкой кулдаунов."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        await m.answer("Сначала /start в ЛС бота.")
        return
        
    command_word = m.text.split()[0]
    tid, err = resolve_command_target(m, command_word)
    if err:
        await m.answer(err)
        return
    if tid == m.from_user.id:
        await m.answer("🤨 Себе это делать странно.")
        return
        
    target = db.fetch_one("SELECT * FROM players WHERE user_id=?", (tid,))
    if not target:
        await m.answer("Игрок не найден.")
        return
    if target["banned"]:
        await m.answer("Этот игрок забанен.")
        return
        
    cooldown_key = (m.from_user.id, tid, action_key)
    now = time.time()
    
    if now - RP_COOLDOWNS.get(cooldown_key, 0) < Config.RP_COOLDOWN:
        left = int(Config.RP_COOLDOWN - (now - RP_COOLDOWNS[cooldown_key])) + 1
        await m.answer(f"⏱ Подожди ещё {left} сек. между одинаковыми действиями с этим игроком.")
        return
        
    RP_COOLDOWNS[cooldown_key] = now
    actor = db.fetch_one("SELECT name FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(generate_rp_text(actor["name"], target["name"], action_key))

# Динамическая регистрация RP handlers
RP_MAPPINGS = {
    "ударить": ["ударить", "уд", "hit"],
    "обнять": ["обнять", "обн", "hug"],
    "поцеловать": ["поцеловать", "поц", "kiss"],
    "пнуть": ["пнуть", "пн", "kick"],
    "погладить": ["погладить", "погл", "pet"],
    "укусить": ["укусить", "ук", "bite"],
    "пожать": ["пожать", "пож", "handshake"],
    "толкнуть": ["толкнуть", "толк", "push"],
    "кинуть": ["кинуть", "кин", "throw"],
    "лечить": ["лечить", "леч", "heal"],
    "игнорировать": ["игнор", "игнорировать"],
    "смеяться": ["смеяться", "смех"],
    "плакать": ["плакать", "плач"],
    "танцевать": ["танцевать", "танец"],
    "шлепнуть": ["шлепнуть", "шлеп"],
    "обозвать": ["обозвать", "обзывать"],
    "восхититься": ["восхититься", "восхищение"],
    "испугаться": ["испугаться", "испуг"],
    "подмигнуть": ["подмигнуть", "подмигивание"],
    "пожать_плечами": ["пожать_плечами", "плечи"],
}

for action, variants in RP_MAPPINGS.items():
    pattern = r"(?i)^(" + "|".join(re.escape(v) for v in variants) + r")(\s|$)"
    
    def make_rp_handler(act: str) -> Callable:
        async def handler(m: Message) -> None:
            await process_rp_action(m, act)
        return handler
        
    router.message(F.text.regexp(pattern))(make_rp_handler(action))

# --- КАЗИНО В ЧАТЕ ---
@router.message(F.text.regexp(r"(?i)^(слоты|slot|сл)(\s+)(\d+)$"))
async def cmd_chat_slots(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    bet = int(m.text.split()[-1])
    result, err = play_casino_slots(m.from_user.id, bet)
    if err:
        await m.answer(err)
        return
    p2 = db.fetch_one("SELECT chips FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CHIPS} Баланс: <b>{p2['chips']}</b>")

@router.message(F.text.regexp(r"(?i)^(кости|dice|кост)(\s+)(\d+)$"))
async def cmd_chat_dice(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    bet = int(m.text.split()[-1])
    result, err = play_casino_dice(m.from_user.id, bet)
    if err:
        await m.answer(err)
        return
    p2 = db.fetch_one("SELECT chips FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CHIPS} Баланс: <b>{p2['chips']}</b>")

@router.message(F.text.regexp(r"(?i)^(монетка|coin|мон)(\s+)(\d+)(\s+)(орел|решка|о|р)$"))
async def cmd_chat_coin(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    parts = m.text.split()
    bet = int(parts[1])
    choice_raw = parts[3].lower()
    choice = "heads" if choice_raw in ["орел", "о"] else "tails"
    
    result, err = play_casino_coin(m.from_user.id, bet, choice)
    if err:
        await m.answer(err)
        return
    p2 = db.fetch_one("SELECT chips FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CHIPS} Баланс: <b>{p2['chips']}</b>")

@router.message(F.text.regexp(r"(?i)^(рулетка|roulette|рул)(\s+)(\d+)(\s+)(красное|черное|зеленое|к|ч|з)$"))
async def cmd_chat_roulette(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    parts = m.text.split()
    bet = int(parts[1])
    color_raw = parts[3].lower()
    color = "red" if color_raw in ["красное", "к"] else ("black" if color_raw in ["черное", "ч"] else "green")
    
    result, err = play_casino_roulette(m.from_user.id, bet, color)
    if err:
        await m.answer(err)
        return
    p2 = db.fetch_one("SELECT chips FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CHIPS} Баланс: <b>{p2['chips']}</b>")

@router.message(F.text.regexp(r"(?i)^(больше|high)(\s+)(\d+)$"))
async def cmd_chat_highlow_high(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    bet = int(m.text.split()[-1])
    result, err = play_casino_highlow(m.from_user.id, bet, "high")
    if err:
        await m.answer(err)
        return
    p2 = db.fetch_one("SELECT chips FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CHIPS} Баланс: <b>{p2['chips']}</b>")

@router.message(F.text.regexp(r"(?i)^(меньше|low)(\s+)(\d+)$"))
async def cmd_chat_highlow_low(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    bet = int(m.text.split()[-1])
    result, err = play_casino_highlow(m.from_user.id, bet, "low")
    if err:
        await m.answer(err)
        return
    p2 = db.fetch_one("SELECT chips FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CHIPS} Баланс: <b>{p2['chips']}</b>")

# --- ПРОМОКОДЫ (ИГРОК) ---
@router.message(F.text.regexp(r"(?i)^#код\s+(\S+)$"))
async def cmd_promo_hash(m: Message) -> None:
    """Активация промокода через #код [код]."""
    match = re.search(r"(?i)^#код\s+(\S+)$", m.text or "")
    if not match:
        return
    
    code = match.group(1)
    success, message = activate_promo_code(m.from_user.id, code)
    await m.answer(message)

@router.message(F.text.regexp(r"(?i)^(активировать|актив|redeem)\s+(\S+)$"))
async def cmd_promo_activate(m: Message) -> None:
    """Активация промокода через активировать [код]."""
    match = re.search(r"(?i)^(?:активировать|актив|redeem)\s+(\S+)$", m.text or "")
    if not match:
        return
    
    code = match.group(1)
    success, message = activate_promo_code(m.from_user.id, code)
    await m.answer(message)

@router.message(F.text.regexp(r"(?i)^промо$"))
async def cmd_promo_list_player(m: Message) -> None:
    """Список активных промокодов для игрока."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        await m.answer("Сначала /start в ЛС бота.")
        return
    
    promos = list_active_promos()
    valid_promos = [p for p in promos if p["is_valid"]]
    
    if not valid_promos:
        await m.answer(f"{E_PROMO} <b>Активных промокодов сейчас нет.</b>\n\nСледи за новостями — администратор периодически выпускает новые коды!")
        return
    
    lines = [f"{E_PROMO} <b>АКТИВНЫЕ ПРОМОКОДЫ</b>\n", f"Найдено: <b>{len(valid_promos)}</b>\n"]
    
    for i, promo in enumerate(valid_promos[:10], 1):
        remaining = promo["max_uses"] - promo["current_uses"]
        lines.append(f"{i}. <code>{promo['code']}</code>")
        rewards = []
        if promo["reward_chips"] > 0:
            rewards.append(f"💰{promo['reward_chips']}")
        if promo["reward_wins"] > 0:
            rewards.append(f"🏆{promo['reward_wins']}")
        lines.append(f"   Награда: {' + '.join(rewards) if rewards else '🎁'}")
        lines.append(f"   Осталось активаций: {remaining}/{promo['max_uses']}\n")
    
    lines.append(f"{E_MAGIC} Активируй: <code>#код [код]</code>")
    
    await m.answer("\n".join(lines))

# --- ПРОМОКОДЫ (АДМИН) ---
@router.message(F.text.regexp(r"(?i)^промо создать\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$"))
async def cmd_promo_create(m: Message) -> None:
    """Создание промокода: промо создать [код] [фишки] [победы] [макс] [часов]."""
    if not is_admin(m.from_user.id):
        return
    
    match = re.search(r"(?i)^промо создать\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$", m.text or "")
    if not match:
        await m.answer("Использование: <code>промо создать [код] [фишки] [победы] [макс] [часов]</code>")
        return
    
    code = match.group(1)
    reward_chips = int(match.group(2))
    reward_wins = int(match.group(3))
    max_uses = int(match.group(4))
    hours = int(match.group(5))
    
    success, message = create_promo_code(code, reward_chips, reward_wins, max_uses, hours, m.from_user.id)
    await m.answer(message)

@router.message(F.text.regexp(r"(?i)^промо удалить\s+(\S+)$"))
async def cmd_promo_delete(m: Message) -> None:
    """Удаление (деактивация) промокода."""
    if not is_admin(m.from_user.id):
        return
    
    match = re.search(r"(?i)^промо удалить\s+(\S+)$", m.text or "")
    if not match:
        return
    
    code = match.group(1)
    success, message = deactivate_promo_code(code)
    await m.answer(message)

@router.message(F.text.regexp(r"(?i)^промо инфо\s+(\S+)$"))
async def cmd_promo_info(m: Message) -> None:
    """Информация о промокоде."""
    if not is_admin(m.from_user.id):
        return
    
    match = re.search(r"(?i)^промо инфо\s+(\S+)$", m.text or "")
    if not match:
        return
    
    code = match.group(1)
    promo = get_promo_info(code)
    if not promo:
        await m.answer(f"❌ Промокод <code>{code}</code> не найден.")
        return
    
    await m.answer(format_promo_info(promo))

@router.message(F.text.regexp(r"(?i)^промо список$"))
async def cmd_promo_list_admin(m: Message) -> None:
    """Список всех промокодов для админа."""
    if not is_admin(m.from_user.id):
        return
    
    promos = list_active_promos()
    
    if not promos:
        await m.answer(f"{E_PROMO} <b>Промокодов пока нет.</b>\n\nСоздай первый: <code>промо создать [код] [фишки] [победы] [макс] [часов]</code>")
        return
    
    lines = [f"{E_PROMO} <b>ВСЕ ПРОМОКОДЫ ({len(promos)})</b>\n"]
    
    for i, promo in enumerate(promos[:20], 1):
        status = "✅" if promo["is_valid"] else ("⏰" if promo["is_expired"] else ("🚫" if promo["is_maxed"] else "❌"))
        expires_str = time.strftime("%d.%m %H:%M", time.localtime(promo["expires_at"]))
        lines.append(f"{i}. {status} <code>{promo['code']}</code>")
        rewards = []
        if promo["reward_chips"] > 0:
            rewards.append(f"💰{promo['reward_chips']}")
        if promo["reward_wins"] > 0:
            rewards.append(f"🏆{promo['reward_wins']}")
        lines.append(f"   Награда: {' + '.join(rewards) if rewards else '—'}")
        lines.append(f"   Активаций: {promo['current_uses']}/{promo['max_uses']}")
        lines.append(f"   Истекает: {expires_str}\n")
    
    if len(promos) > 20:
        lines.append(f"… и ещё {len(promos) - 20} промокодов")
    
    await m.answer("\n".join(lines))

# --- АДМИН КОМАНДЫ ---
@router.message(F.text.regexp(r"(?i)^бан(\s|$)"))
async def adm_cmd_ban(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_command_target(m, "бан")
    if err or not tid:
        await m.answer(err or "Не найдено.")
        return
    db.execute("UPDATE players SET banned=1 WHERE user_id=?", (tid,))
    ACTIVE_DUELS.pop(tid, None)
    await m.answer(f"🚫 Игрок <code>{tid}</code> забанен.")

@router.message(F.text.regexp(r"(?i)^разбан(\s|$)"))
async def adm_cmd_unban(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_command_target(m, "разбан")
    if err or not tid:
        await m.answer(err or "Не найдено.")
        return
    db.execute("UPDATE players SET banned=0 WHERE user_id=?", (tid,))
    await m.answer(f"✅ Игрок <code>{tid}</code> разбанен.")

@router.message(F.text.regexp(r"(?i)^выдать(\s|$)"))
async def adm_cmd_give(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_command_target(m, "выдать")
    if err or not tid:
        await m.answer(err or "Не найдено.")
        return
        
    amount = next((int(p) for p in (m.text or "").split() if p.lstrip("-").isdigit()), None)
    if not amount:
        await m.answer("Укажи сумму: <code>выдать @user 1000</code>")
        return
        
    db.execute("UPDATE players SET chips=chips+? WHERE user_id=?", (amount, tid))
    await m.answer(f"✅ Выдано {amount}💰 игроку <code>{tid}</code>.")
    notify_player(tid, f"🎁 Админ выдал тебе {amount}💰")

@router.message(F.text.regexp(r"(?i)^очки(\s|$)"))
async def adm_cmd_points(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_command_target(m, "очки")
    if err or not tid:
        await m.answer(err or "Не найдено.")
        return
        
    amount = next((int(p) for p in (m.text or "").split() if p.lstrip("-").isdigit()), None)
    if not amount:
        await m.answer("Укажи число: <code>очки @user 5</code>")
        return
        
    db.execute("UPDATE players SET wins=wins+? WHERE user_id=?", (amount, tid))
    await m.answer(f"✅ Игроку <code>{tid}</code> начислено {amount} 🏆.")
    notify_player(tid, f"🎁 Админ начислил тебе {amount} {E_TROPHY}")

@router.message(F.text.regexp(r"(?i)^винрейт(\s|$)"))
async def adm_cmd_setwins(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_command_target(m, "винрейт")
    if err or not tid:
        await m.answer(err or "Не найдено.")
        return
        
    amount = next((int(p) for p in (m.text or "").split() if p.isdigit()), None)
    if amount is None:
        await m.answer("Укажи число: <code>винрейт @user 50</code>")
        return
        
    db.execute("UPDATE players SET wins=? WHERE user_id=?", (amount, tid))
    await m.answer(f"✅ Игроку <code>{tid}</code> установлено {amount} 🏆.")
    notify_player(tid, f"🎁 Админ установил тебе {amount} {E_TROPHY}")

@router.message(F.text.regexp(r"(?i)^стоп(\s|$)"))
async def adm_cmd_stop_duel(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_command_target(m, "стоп")
    if err or not tid:
        await m.answer(err or "Не найдено.")
        return
        
    if tid in ACTIVE_DUELS:
        terminate_duel(ACTIVE_DUELS[tid])
        await m.answer(f"✅ Бой игрока <code>{tid}</code> принудительно завершен.")
    else:
        await m.answer("У игрока нет активного боя.")

@router.message(F.text.regexp(r"(?i)^рассылка\s+"))
async def adm_cmd_broadcast(m: Message, bot: Bot) -> None:
    if not is_admin(m.from_user.id):
        return
    text = (m.text or "").split(" ", 1)[1].strip()
    if not text:
        await m.answer("Использование: <code>рассылка текст</code>")
        return
        
    rows = db.fetch_all("SELECT user_id FROM players WHERE banned=0 AND is_bot=0")
    ok_count = 0
    for r in rows:
        try:
            await bot.send_message(r["user_id"], f"📢 <b>Сообщение:</b>\n\n{text}")
            ok_count += 1
            await asyncio.sleep(0.05)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except Exception:
            pass
            
    await m.answer(f"✅ Рассылка завершена. Доставлено: {ok_count} игрокам.")

@router.message(F.text.regexp(r"(?i)^ботов(\s|$)"))
async def adm_cmd_addbots(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    n = next((int(p) for p in (m.text or "").split() if p.isdigit()), 10)
    before = db.fetch_one("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    ensure_masked_bots_exist(before + n)
    after = db.fetch_one("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    await m.answer(f"✅ Добавлено: {after - before} ботов.")

@router.message(Command("admin"))
async def cmd_admin_panel(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    await m.answer(
        "🛠 <b>Админ-команды</b>\n\n"
        "• <code>бан</code> / <code>разбан</code>\n"
        "• <code>выдать [сумма]</code>\n"
        "• <code>очки [число]</code>\n"
        "• <code>винрейт [число]</code>\n"
        "• <code>стоп</code>\n"
        "• <code>рассылка [текст]</code>\n"
        "• <code>ботов [число]</code>\n\n"
        "<b>🎟 Промокоды:</b>\n"
        "• <code>промо создать [код] [фишки] [победы] [макс] [часов]</code>\n"
        "• <code>промо удалить [код]</code>\n"
        "• <code>промо инфо [код]</code>\n"
        "• <code>промо список</code>"
    )

@router.message(Command("stats"))
async def cmd_bot_stats(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    total = db.fetch_one("SELECT COUNT(*) c FROM players WHERE is_bot=0")["c"]
    bots = db.fetch_one("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    banned = db.fetch_one("SELECT COUNT(*) c FROM players WHERE banned=1")["c"]
    promos = db.fetch_one("SELECT COUNT(*) c FROM promo_codes WHERE active=1")["c"]
    await m.answer(
        f"📊 <b>Статистика бота:</b>\n"
        f"👥 Игроков: {total}\n"
        f"🤖 Скрытых ботов: {bots}\n"
        f"🚫 В бане: {banned}\n"
        f"⚔️ Активных боёв: {len({id(d) for d in ACTIVE_DUELS.values()})}\n"
        f"🎟 Активных промокодов: {promos}"
    )

# ==============================================================================
# 17. ЛОГИКА ДУЭЛИ: ЗАПУСК, РАУНДЫ, ЗАВЕРШЕНИЕ
# ==============================================================================

def initiate_duel(a_id: int, b_id: int, is_boss: bool = False, boss_key: Optional[str] = None, reward_mult: int = 1) -> Optional[Duel]:
    """Создает и инициализирует объект дуэли."""
    a_row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (a_id,))
    if not a_row:
        return None
        
    fa = create_fighter_from_db(a_row)
    
    if is_boss and boss_key in BOSSES:
        fb = create_boss_fighter(BOSSES[boss_key])
    else:
        b_row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (b_id,))
        if not b_row:
            return None
        fb = create_fighter_from_db(b_row)
        
    duel = Duel(
        a_id=a_id, b_id=b_id, a=fa, b=fb, 
        attacker_is_a=random.random() < 0.5, 
        is_boss=is_boss, boss_key=boss_key, reward_mult=reward_mult
    )
    
    first_name = fa.name if duel.attacker_is_a else fb.name
    prefix = f"{E_BOSS} <b>БОСС</b> " if is_boss else ""
    duel.log.append(f"{prefix}Бой начался! Первым атакует <b>{first_name}</b>.")
    
    ACTIVE_DUELS[a_id] = duel
    if b_id > 0:
        ACTIVE_DUELS[b_id] = duel
        
    return duel

async def initiate_duel_message(aid: int, bid: int, m: Message, bot: Bot, is_boss: bool = False, boss_key: Optional[str] = None, reward_mult: int = 1) -> None:
    """Отправляет начальные сообщения о дуэли и запускает таймеры."""
    if bid == aid:
        await m.answer("🤨 Нельзя драться с самим собой.")
        return
    if aid in ACTIVE_DUELS:
        await m.answer("У тебя уже идёт активный бой.")
        return
        
    duel = initiate_duel(aid, bid, is_boss=is_boss, boss_key=boss_key, reward_mult=reward_mult)
    if not duel:
        await m.answer("Не удалось начать бой (соперник недоступен).")
        return
        
    role = duel.get_state_for(aid)
    if role == "attacker":
        await m.answer(generate_duel_status_text(duel, aid, timer_left=Config.TURN_TIMEOUT), reply_markup=get_attack_zone_kb())
        start_duel_timer(duel, aid, "attacker", bot)
    else:
        atk_id = duel.get_attacker_id()
        if atk_id < 0:
            duel.atk_zone = bot_decide_attack_zone(duel.get_attacker(), duel.get_defender())
            await m.answer(generate_duel_status_text(duel, aid, extra="⚔️ Соперник уже выбрал удар.", timer_left=Config.TURN_TIMEOUT), reply_markup=get_defend_zone_kb())
            start_duel_timer(duel, aid, "defender", bot)
        else:
            await m.answer(generate_duel_status_text(duel, aid, extra="⏳ Соперник выбирает удар…"), reply_markup=build_inline_keyboard([("🔄 Обновить", "duel:refresh")]))
            
    if bid > 0 and not is_boss:
        attacker_name = db.fetch_one("SELECT name FROM players WHERE user_id=?", (aid,))["name"]
        notify_player(bid, f"{E_GLOVE} <b>{esc(attacker_name)}</b> кинул тебе перчатку! Открой «⚔️ Арена» в ЛС бота.")

async def process_duel_round(duel: Duel, bot: Bot, cb: Optional[CallbackQuery], atk_zone: str, def_zone: Optional[str]) -> None:
    """Обрабатывает один раунд боя."""
    if duel.finished:
        return
    stop_duel_timer(duel)
    
    attacker = duel.get_attacker()
    defender = duel.get_defender()

    duel.log.append(f"── Раунд {duel.round_no} ──")
    duel.log.append(f"⚔️ {attacker.name} → {ZONE_INFO[atk_zone]['emoji']} {ZONE_INFO[atk_zone]['name']}")
    if def_zone:
        duel.log.append(f"🛡 {defender.name} → {ZONE_INFO[def_zone]['emoji']} {ZONE_INFO[def_zone]['name']}")

    process_dots(attacker, duel.log)
    if not attacker.is_alive():
        await finalize_duel(duel, winner_is_a=(attacker is duel.b), bot=bot)
        return

    execute_attack_phase(attacker, defender, atk_zone, def_zone, duel.log)
    if not defender.is_alive():
        await finalize_duel(duel, winner_is_a=(defender is duel.a), bot=bot)
        return

    duel.atk_zone = None
    duel.attacker_is_a = not duel.attacker_is_a
    duel.round_no += 1
    
    if duel.round_no - duel.bot_last_block_round > 4:
        duel.bot_block_streak = 0
        
    await start_next_duel_round(duel, bot)

async def start_next_duel_round(duel: Duel, bot: Bot) -> None:
    """Инициализирует следующий раунд."""
    if duel.finished:
        return
        
    atk_id = duel.get_attacker_id()
    def_id = duel.get_defender_id()

    if atk_id > 0:
        await bot.send_message(
            atk_id, 
            generate_duel_status_text(duel, atk_id, extra="🎯 Твой ход — выбери зону удара.", timer_left=Config.TURN_TIMEOUT), 
            reply_markup=get_attack_zone_kb()
        )
        start_duel_timer(duel, atk_id, "attacker", bot)
    else:
        duel.atk_zone = bot_decide_attack_zone(duel.get_attacker(), duel.get_defender())
        duel.log.append(f"⚔️ {duel.get_attacker().name} выбрал удар")
        if def_id > 0:
            await bot.send_message(
                def_id, 
                generate_duel_status_text(duel, def_id, extra=f"{E_SHIELD} Соперник атакует — выбери зону защиты.", timer_left=Config.TURN_TIMEOUT), 
                reply_markup=get_defend_zone_kb()
            )
            start_duel_timer(duel, def_id, "defender", bot)

async def finalize_duel(duel: Duel, winner_is_a: bool, bot: Bot, reason: str = "ko") -> None:
    """Завершает дуэль, начисляет награды и отправляет итоги."""
    if duel.finished:
        return
        
    aid, bid = duel.a_id, duel.b_id
    a_row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (aid,))
    if not a_row:
        terminate_duel(duel)
        return
        
    mult = duel.reward_mult if duel.is_boss else 1

    if winner_is_a:
        db.execute("UPDATE players SET wins=wins+1 WHERE user_id=?", (aid,))
        current_wins = db.fetch_one("SELECT wins FROM players WHERE user_id=?", (aid,))["wins"]
        prize = ARENAS[determine_arena(current_wins)]["prize"] * mult
        db.execute("UPDATE players SET chips=chips+? WHERE user_id=?", (prize, aid))
        
        if bid and bid > 0:
            db.execute("UPDATE players SET losses=losses+1, wins=CASE WHEN wins>0 THEN wins-1 ELSE 0 END WHERE user_id=?", (bid,))
            a_name = a_row["name"]
            notify_player(bid, f"{E_SKULL} <b>{esc(a_name)}</b> одолел тебя. −1 {E_TROPHY}, без награды.")
            
        result_line = f"{E_TROPHY} <b>ТЫ ПОБЕДИЛ!</b>  +1 {E_TROPHY}  ·  +{prize}{E_CHIPS}"
    else:
        if bid and bid > 0:
            db.execute("UPDATE players SET wins=wins+1 WHERE user_id=?", (bid,))
            current_wins_b = db.fetch_one("SELECT wins FROM players WHERE user_id=?", (bid,))["wins"]
            prize_b = ARENAS[determine_arena(current_wins_b)]["prize"] * mult
            db.execute("UPDATE players SET chips=chips+? WHERE user_id=?", (prize_b, bid))
            
            a_name = a_row["name"]
            notify_player(bid, f"{E_TROPHY} <b>{esc(a_name)}</b> проиграл тебе! +1 {E_TROPHY}, +{prize_b}{E_CHIPS}")
            
        db.execute("UPDATE players SET losses=losses+1, wins=CASE WHEN wins>0 THEN wins-1 ELSE 0 END WHERE user_id=?", (aid,))
        result_line = f"{E_SKULL} <b>ТЫ ПРОИГРАЛ.</b>  −1 {E_TROPHY}  ·  без награды"

    terminate_duel(duel)
    reason_line = f"\n⏱ Соперник не успел за {Config.TURN_TIMEOUT} сек." if reason == "timeout" else ""
    
    new_a = db.fetch_one("SELECT * FROM players WHERE user_id=?", (aid,))
    a_arena = ARENAS[determine_arena(new_a["wins"])]

    text = (
        f"╔══════════════════════════╗\n        ⚔️ <b>ИТОГ БОЯ</b>\n╚══════════════════════════╝\n\n"
        f"{result_line}\n\n"
        f"{E_TROPHY} Кубки: <b>{new_a['wins']}</b>\n"
        f"{E_SKULL} Поражения: <b>{new_a['losses']}</b>\n"
        f"{E_CHIPS} Фишки: <b>{new_a['chips']}</b>\n"
        f"📍 {a_arena['emoji']} {a_arena['name']}"
        f"{reason_line}\n\nВыбери действие:"
    )
    try:
        await bot.send_message(aid, text, reply_markup=get_finish_duel_kb())
    except Exception:
        pass

    if bid and bid > 0:
        new_b = db.fetch_one("SELECT * FROM players WHERE user_id=?", (bid,))
        if new_b:
            b_arena = ARENAS[determine_arena(new_b["wins"])]
            res_b = f"{E_SKULL} <b>ТЫ ПРОИГРАЛ.</b>  −1 {E_TROPHY}  ·  без награды" if winner_is_a else f"{E_TROPHY} <b>ТЫ ПОБЕДИЛ!</b>  +1 {E_TROPHY}"
            text_b = (
                f"╔══════════════════════════╗\n        ⚔️ <b>ИТОГ БОЯ</b>\n╚══════════════════════════╝\n\n"
                f"{res_b}\n\n"
                f"{E_TROPHY} Кубки: <b>{new_b['wins']}</b>\n"
                f"{E_SKULL} Поражения: <b>{new_b['losses']}</b>\n"
                f"{E_CHIPS} Фишки: <b>{new_b['chips']}</b>\n"
                f"📍 {b_arena['emoji']} {b_arena['name']}"
                f"{reason_line}\n\nВыбери действие:"
            )
            try:
                await bot.send_message(bid, text_b, reply_markup=get_finish_duel_kb())
            except Exception:
                pass

# ==============================================================================
# 18. CALLBACK HANDLERS (INLINE КНОПКИ)
# ==============================================================================

@router.callback_query(F.data == "arena:menu")
async def cb_arena_menu(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    await safe_edit_message(cb, *generate_arena_menu_screen(cb.from_user.id))
    await cb.answer()

@router.callback_query(F.data == "arena:bosses")
async def cb_arena_bosses(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    await safe_edit_message(cb, *generate_bosses_menu_screen(cb.from_user.id))
    await cb.answer()

@router.callback_query(F.data.regexp(r"^arena:boss:\w+$"))
async def cb_arena_boss_fight(cb: CallbackQuery, bot: Bot) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p or cb.from_user.id in ACTIVE_DUELS:
        await cb.answer("Сначала /start или бой уже идёт", show_alert=True)
        return
        
    bkey = cb.data.split(":")[2]
    if bkey not in BOSSES or p["wins"] < BOSSES[bkey]["min_wins"]:
        await cb.answer(f"Нужно {BOSSES[bkey]['min_wins']} {E_TROPHY} для этого босса.", show_alert=True)
        return
        
    duel = initiate_duel(cb.from_user.id, -1, is_boss=True, boss_key=bkey, reward_mult=BOSSES[bkey]["reward_mult"])
    if not duel:
        await cb.answer("Ошибка запуска боя.", show_alert=True)
        return
        
    role = duel.get_state_for(cb.from_user.id)
    if role == "attacker":
        await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, timer_left=Config.TURN_TIMEOUT), get_attack_zone_kb())
        start_duel_timer(duel, cb.from_user.id, "attacker", bot)
    else:
        duel.atk_zone = bot_decide_attack_zone(duel.get_attacker(), duel.get_defender())
        await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⚔️ Босс уже выбрал удар.", timer_left=Config.TURN_TIMEOUT), get_defend_zone_kb())
        start_duel_timer(duel, cb.from_user.id, "defender", bot)
        
    await cb.answer(f"Бой с {BOSSES[bkey]['name']} начался!")

@router.callback_query(F.data == "arena:find")
async def cb_arena_find(cb: CallbackQuery, bot: Bot) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p or cb.from_user.id in ACTIVE_DUELS:
        await cb.answer("Сначала /start или бой уже идёт", show_alert=True)
        return
        
    oid = pick_balanced_opponent(cb.from_user.id, p["wins"])
    if not oid:
        await cb.answer("Не удалось подобрать соперника.", show_alert=True)
        return
        
    duel = initiate_duel(cb.from_user.id, oid)
    if not duel:
        await cb.answer("Не удалось начать бой.", show_alert=True)
        return
        
    role = duel.get_state_for(cb.from_user.id)
    if role == "attacker":
        await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, timer_left=Config.TURN_TIMEOUT), get_attack_zone_kb())
        start_duel_timer(duel, cb.from_user.id, "attacker", bot)
    else:
        atk_id = duel.get_attacker_id()
        if atk_id < 0:
            duel.atk_zone = bot_decide_attack_zone(duel.get_attacker(), duel.get_defender())
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⚔️ Соперник уже выбрал удар.", timer_left=Config.TURN_TIMEOUT), get_defend_zone_kb())
            start_duel_timer(duel, cb.from_user.id, "defender", bot)
        else:
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Соперник выбирает удар…"), build_inline_keyboard([("🔄 Обновить", "duel:refresh")]))
    await cb.answer()

@router.callback_query(F.data == "arena:list")
async def cb_arena_list(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
        
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    key = determine_arena(p["wins"])
    a = ARENAS[key]
    
    rows = db.fetch_all("""
        SELECT user_id, name, wins, losses FROM players 
        WHERE user_id != ? AND banned=0 AND wins BETWEEN ? AND ? 
        ORDER BY RANDOM() LIMIT 8
    """, (cb.from_user.id, a["min_wins"], a["max_wins"]))
    
    if not rows:
        await safe_edit_message(cb, "Сейчас на твоей арене никого нет — жми «Найти соперника».", build_inline_keyboard([("🎲 Найти", "arena:find")], [("⬅️ Назад", "arena:menu")]))
        return
        
    kb_rows = [[(f"{r['name'][:16]} · {r['wins']}{E_TROPHY}/{r['losses']}{E_SKULL}", f"duel:pick:{r['user_id']}"), ("👁", f"duel:profile:{r['user_id']}")] for r in rows]
    kb_rows.append([("⬅️ Назад", "arena:menu")])
    
    await safe_edit_message(cb, f"{a['emoji']} <b>{a['name']}</b> — соперники:", build_inline_keyboard(*kb_rows))
    await cb.answer()

@router.callback_query(F.data == "arena:find_name")
async def cb_arena_find_name(cb: CallbackQuery, state: FSMContext) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    await state.set_state(DuelFindState.waiting_for_target)
    await cb.message.answer("🔎 Отправь @username, ID или имя бойца.")
    await cb.answer()

@router.callback_query(F.data.regexp(r"^duel:pick:-?\d+$"))
async def cb_duel_pick(cb: CallbackQuery, bot: Bot) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p or cb.from_user.id in ACTIVE_DUELS:
        await cb.answer("Сначала /start или бой уже идёт", show_alert=True)
        return
        
    tid = int(cb.data.split(":")[2])
    if tid == cb.from_user.id:
        await cb.answer("Нельзя драться с собой.", show_alert=True)
        return
        
    duel = initiate_duel(cb.from_user.id, tid)
    if not duel:
        await cb.answer("Соперник недоступен.", show_alert=True)
        return
        
    role = duel.get_state_for(cb.from_user.id)
    if role == "attacker":
        await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, timer_left=Config.TURN_TIMEOUT), get_attack_zone_kb())
        start_duel_timer(duel, cb.from_user.id, "attacker", bot)
    else:
        atk_id = duel.get_attacker_id()
        if atk_id < 0:
            duel.atk_zone = bot_decide_attack_zone(duel.get_attacker(), duel.get_defender())
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⚔️ Соперник уже выбрал удар.", timer_left=Config.TURN_TIMEOUT), get_defend_zone_kb())
            start_duel_timer(duel, cb.from_user.id, "defender", bot)
        else:
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Соперник выбирает удар…"), build_inline_keyboard([("🔄 Обновить", "duel:refresh")]))
    await cb.answer()

@router.callback_query(F.data.regexp(r"^duel:profile:-?\d+$"))
async def cb_duel_profile(cb: CallbackQuery) -> None:
    tid = int(cb.data.split(":")[2])
    row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (tid,))
    if not row:
        await cb.answer("Игрок не найден.", show_alert=True)
        return
    await safe_edit_message(cb, generate_profile_text(row), build_inline_keyboard([("⬅️ Назад", "arena:list")], [("⚔️ Вызвать на бой", f"duel:pick:{tid}")]))
    await cb.answer()

@router.callback_query(F.data == "duel:myprofile")
async def cb_my_profile(cb: CallbackQuery) -> None:
    row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not row:
        await cb.answer("Сначала /start", show_alert=True)
        return
    await safe_edit_message(cb, generate_profile_text(row), build_inline_keyboard([("⬅️ Назад", "arena:menu")], [("🎒 Снаряжение", "gear:menu")]))
    await cb.answer()

@router.callback_query(F.data == "duel:again")
async def cb_duel_again(cb: CallbackQuery, bot: Bot) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p or cb.from_user.id in ACTIVE_DUELS:
        await cb.answer("Сначала /start или бой уже идёт", show_alert=True)
        return
        
    oid = pick_balanced_opponent(cb.from_user.id, p["wins"])
    if not oid:
        await cb.answer("Не удалось подобрать соперника.", show_alert=True)
        return
        
    duel = initiate_duel(cb.from_user.id, oid)
    if not duel:
        await cb.answer("Не удалось начать бой.", show_alert=True)
        return
        
    role = duel.get_state_for(cb.from_user.id)
    if role == "attacker":
        await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, timer_left=Config.TURN_TIMEOUT), get_attack_zone_kb())
        start_duel_timer(duel, cb.from_user.id, "attacker", bot)
    else:
        atk_id = duel.get_attacker_id()
        if atk_id < 0:
            duel.atk_zone = bot_decide_attack_zone(duel.get_attacker(), duel.get_defender())
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⚔️ Соперник уже выбрал удар.", timer_left=Config.TURN_TIMEOUT), get_defend_zone_kb())
            start_duel_timer(duel, cb.from_user.id, "defender", bot)
        else:
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Соперник выбирает удар…"), build_inline_keyboard([("🔄 Обновить", "duel:refresh")]))
    await cb.answer()

@router.callback_query(F.data.regexp(r"^duel:atk:(head|torso|arms|legs)$"))
async def cb_duel_attack(cb: CallbackQuery, bot: Bot) -> None:
    duel = ACTIVE_DUELS.get(cb.from_user.id)
    if not duel or duel.finished or duel.get_state_for(cb.from_user.id) != "attacker" or duel.timer_for != cb.from_user.id:
        await cb.answer("Бой не найден, завершён или не твой ход.", show_alert=True)
        return
        
    stop_duel_timer(duel)
    atk_zone = cb.data.split(":")[2]
    duel.atk_zone = atk_zone
    def_id = duel.get_defender_id()

    if def_id < 0:
        bot_is_a = (def_id == duel.a_id)
        bot_f = duel.a if bot_is_a else duel.b
        attacker = duel.b if bot_is_a else duel.a
        
        if bot_decide_to_defend(duel, bot_is_a):
            def_zone = bot_decide_defend_zone(attacker, bot_f)
            duel.bot_last_block_round = duel.round_no
            duel.bot_block_streak += 1
            duel.log.append(f"🛡 {bot_f.name} встаёт в защиту")
        else:
            def_zone = None
            duel.bot_block_streak = 0
            
        await process_duel_round(duel, bot, cb=cb, atk_zone=atk_zone, def_zone=def_zone)
    else:
        await bot.send_message(
            def_id, 
            generate_duel_status_text(duel, def_id, extra=f"⚔️ {duel.get_attacker().name} выбрал зону удара!", timer_left=Config.TURN_TIMEOUT), 
            reply_markup=get_defend_zone_kb()
        )
        start_duel_timer(duel, def_id, "defender", bot)
        await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Ждём защиту соперника…"), build_inline_keyboard([("🔄 Обновить", "duel:refresh")]))
    await cb.answer("Удар выбран.")

@router.callback_query(F.data.regexp(r"^duel:def:(head|torso|arms|legs)$"))
async def cb_duel_defend(cb: CallbackQuery, bot: Bot) -> None:
    duel = ACTIVE_DUELS.get(cb.from_user.id)
    if not duel or duel.finished or duel.get_state_for(cb.from_user.id) != "defender" or duel.atk_zone is None or duel.timer_for != cb.from_user.id:
        await cb.answer("Бой не найден, завершён или не твой ход.", show_alert=True)
        return
        
    stop_duel_timer(duel)
    def_zone = cb.data.split(":")[2]
    await process_duel_round(duel, bot, cb=cb, atk_zone=duel.atk_zone, def_zone=def_zone)

@router.callback_query(F.data == "duel:refresh")
async def cb_duel_refresh(cb: CallbackQuery) -> None:
    duel = ACTIVE_DUELS.get(cb.from_user.id)
    if not duel or duel.finished:
        await cb.answer("Бой не найден или завершён.", show_alert=True)
        return
        
    role = duel.get_state_for(cb.from_user.id)
    if role == "attacker":
        if duel.timer_for == cb.from_user.id:
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="🎯 Выбери зону удара.", timer_left=max(0, int(round(duel.timer_deadline - time.time())))), get_attack_zone_kb())
        else:
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Ждём защиту соперника…"), build_inline_keyboard([("🔄 Обновить", "duel:refresh")]))
    else:
        if duel.atk_zone is None:
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Соперник ещё выбирает удар…"), build_inline_keyboard([("🔄 Обновить", "duel:refresh")]))
        else:
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra=f"{E_SHIELD} Выбери зону защиты.", timer_left=max(0, int(round(duel.timer_deadline - time.time())))), get_defend_zone_kb())
    await cb.answer("Обновлено")

@router.callback_query(F.data == "gear:menu")
async def cb_gear_menu(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    await safe_edit_message(cb, *generate_gear_screen(cb.from_user.id))
    await cb.answer()

@router.callback_query(F.data == "gear:w")
async def cb_gear_weapon(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p:
        await cb.answer("Сначала /start", show_alert=True)
        return
        
    equipped = p["weapon"]
    owned = set((p["weapons_owned"] or "").split(","))
    lines = ["⚔️ <b>Оружие</b>", f"{E_CHIPS} Фишки: <b>{p['chips']}</b>", ""]
    rows = []
    
    for key, it in WEAPONS.items():
        lines.append(f"{it['emoji']} <b>{it['name']}</b> — <i>{it['spec']}</i>\n    урон {it['dmg']} · шанс {it['chance']}% · {it['desc']}")
        if key == equipped:
            label = "✅ надето"
        elif key in owned:
            label = "🎒 надеть"
        else:
            label = f"{it['price']}💰"
        rows.append([(f"{it['emoji']} {it['name']} · {label}", f"buy_weapon:{key}")])
    rows.append([("⬅️ Назад", "gear:menu")])
    
    await safe_edit_message(cb, "\n".join(lines), build_inline_keyboard(*rows))
    await cb.answer()

@router.callback_query(F.data.regexp(r"^buy_weapon:(\w+)$"))
async def cb_buy_weapon(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p:
        await cb.answer("Сначала /start", show_alert=True)
        return
        
    key = cb.data.split(":")[1]
    if key not in WEAPONS:
        await cb.answer()
        return
        
    item = WEAPONS[key]
    owned = set((p["weapons_owned"] or "").split(","))
    
    if key in owned:
        db.execute("UPDATE players SET weapon=? WHERE user_id=?", (key, cb.from_user.id))
        toast = f"Надето: {item['name']}"
    elif p["chips"] >= item["price"]:
        db.execute("UPDATE players SET chips=chips-?, weapons_owned=?, weapon=? WHERE user_id=?", (item["price"], ",".join(owned | {key}), key, cb.from_user.id))
        toast = f"Куплено: {item['name']}"
    else:
        await cb.answer(f"Нужно {item['price']}💰", show_alert=True)
        return
        
    await cb_gear_weapon(cb)
    await cb.answer(toast)

@router.callback_query(F.data == "gear:armor_menu")
async def cb_gear_armor_menu(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p:
        await cb.answer("Сначала /start", show_alert=True)
        return
        
    slots = get_player_armor_slots(p)
    lines = ["🛡 <b>Броня — выбери часть тела</b>", f"{E_CHIPS} Фишки: <b>{p['chips']}</b>", ""]
    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"{ZONE_INFO[slot]['emoji']} <b>{ZONE_INFO[slot]['name']}</b> — {item['emoji']} {item['name']} (защита {item['df']})")
        
    await safe_edit_message(cb, "\n".join(lines), build_inline_keyboard(
        [("🧠 Голова", "gear:head"), ("🫀 Торс", "gear:torso")],
        [("💪 Руки", "gear:arms"), ("🦵 Ноги", "gear:legs")],
        [("⬅️ Назад", "gear:menu")]
    ))
    await cb.answer()

@router.callback_query(F.data.regexp(r"^gear:(head|torso|arms|legs)$"))
async def cb_gear_armor_slot(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p:
        await cb.answer("Сначала /start", show_alert=True)
        return
        
    slot = cb.data.split(":")[1]
    slots = get_player_armor_slots(p)
    equipped = slots.get(slot, f"{slot}_none")
    owned = set((p["armors_owned"] or "").split(","))
    lines = [f"🛡 <b>Броня на {ZONE_INFO[slot]['name'].lower()}</b>", f"{E_CHIPS} Фишки: <b>{p['chips']}</b>", ""]
    rows = []
    
    for item in ARMOR_DATA[slot]:
        key = item["key"]
        lines.append(f"{item['emoji']} <b>{item['name']}</b> — защита <b>{item['df']}</b>, HP +{item['hp']}\n    {item['desc']}")
        if key == equipped:
            label = "✅ надето"
        elif key in owned:
            label = "🎒 надеть"
        else:
            label = f"{item['price']}💰"
        rows.append([(f"{item['emoji']} {item['name']} · {label}", f"buy_armor:{slot}:{key}")])
    rows.append([("⬅️ К слотам", "gear:armor_menu")])
    
    await safe_edit_message(cb, "\n".join(lines), build_inline_keyboard(*rows))
    await cb.answer()

@router.callback_query(F.data.regexp(r"^buy_armor:(head|torso|arms|legs):(\w+)$"))
async def cb_buy_armor(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p:
        await cb.answer("Сначала /start", show_alert=True)
        return
        
    _, slot, key = cb.data.split(":")
    item = get_armor_item_by_key(key)
    if not item or item["slot"] != slot:
        await cb.answer("Предмет не найден.", show_alert=True)
        return
        
    owned = set((p["armors_owned"] or "").split(","))
    col = f"armor_{slot}"
    
    if key in owned:
        db.execute(f"UPDATE players SET {col}=? WHERE user_id=?", (key, cb.from_user.id))
        toast = f"Надето: {item['name']}"
    elif p["chips"] >= item["price"]:
        db.execute(f"UPDATE players SET chips=chips-?, armors_owned=?, {col}=? WHERE user_id=?", (item["price"], ",".join(owned | {key}), key, cb.from_user.id))
        toast = f"Куплено: {item['name']}"
    else:
        await cb.answer(f"Нужно {item['price']}💰", show_alert=True)
        return
        
    await cb_gear_armor_slot(cb)
    await cb.answer(toast)

@router.callback_query(F.data.regexp(r"^top:(cur|bronze|silver|gold)$"))
async def cb_top_leaderboard(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p:
        await cb.answer("Сначала /start", show_alert=True)
        return
        
    key = cb.data.split(":")[1]
    if key == "cur":
        key = determine_arena(p["wins"])
        
    a = ARENAS[key]
    rows = db.fetch_all("""
        SELECT user_id, name, wins, losses FROM players 
        WHERE is_bot=0 AND banned=0 AND wins BETWEEN ? AND ? 
        ORDER BY wins DESC, losses ASC LIMIT 20
    """, (a["min_wins"], a["max_wins"]))
    
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"{a['emoji']} <b>{a['name']}</b> — топ по победам", ""]
    
    if not rows:
        lines.append("<i>Пока никого нет на этой арене.</i>")
        
    for i, r in enumerate(rows):
        mark = medals[i] if i < 3 else f"{i + 1}."
        you = " ← ты" if r["user_id"] == cb.from_user.id else ""
        lines.append(f"{mark} <b>{esc(r['name'])}</b> — {r['wins']} {E_TROPHY} / {r['losses']} {E_SKULL}{you}")
        
    me = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if me and all(r["user_id"] != cb.from_user.id for r in rows) and a["min_wins"] <= me["wins"] <= a["max_wins"]:
        rank_row = db.fetch_one("""
            SELECT COUNT(*) c FROM players 
            WHERE is_bot=0 AND banned=0 AND wins BETWEEN ? AND ? AND wins > ?
        """, (a["min_wins"], a["max_wins"], me["wins"]))
        rank = (rank_row["c"] if rank_row else 0) + 1
        lines += ["…", f"{rank}. <b>{esc(me['name'])}</b> — {me['wins']} {E_TROPHY} / {me['losses']} {E_SKULL} ← ты"]
        
    lines += ["", f"{E_TROPHY} Победа: +1 и деньги. {E_SKULL} Поражение: −1 без награды."]
    
    await safe_edit_message(cb, "\n".join(lines), build_inline_keyboard(
        [("🥉 Бронза", "top:bronze"), ("🥈 Серебро", "top:silver"), ("🥇 Золото", "top:gold")],
        [("⬅️ Назад", "arena:menu")]
    ))
    await cb.answer()

# ==============================================================================
# 19. FALLBACK И ЗАПУСК
# ==============================================================================

@router.message(DuelFindState.waiting_for_target, F.text)
async def duel_find_target_handler(m: Message, state: FSMContext, bot: Bot) -> None:
    if m.chat.type != "private":
        await state.clear()
        return
        
    if m.text in {"⚔️ Арена", "🎰 Казино", "🎒 Снаряжение", "🏆 Топ"}:
        await state.clear()
        return
        
    await state.clear()
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start.")
        return
        
    key = m.text.strip().lstrip("@")
    row = db.fetch_one("SELECT user_id FROM players WHERE user_id=? AND banned=0", (int(key),)) if key.isdigit() else None
    
    if not row:
        row = db.fetch_one("""
            SELECT user_id FROM players 
            WHERE (LOWER(username)=LOWER(?) OR LOWER(name)=LOWER(?)) AND banned=0 
            LIMIT 1
        """, (key, key))
        
    if not row:
        target = pick_balanced_opponent(m.from_user.id, p["wins"])
        if not target:
            await m.answer("Не удалось подобрать соперника.")
            return
        await initiate_duel_message(m.from_user.id, target, m, bot)
    else:
        await initiate_duel_message(m.from_user.id, row["user_id"], m, bot)

@router.message()
async def fallback_handler(m: Message) -> None:
    if not m.from_user:
        return
        
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        if m.chat.type == "private":
            await m.answer("Отправь /start, чтобы создать бойца ⚔️")
        return
        
    if is_user_banned(m.from_user.id):
        await m.answer("🚫 Доступ закрыт.")
        return
        
    if m.chat.type == "private":
        await m.answer("Пиши <code>help</code> или пользуйся меню внизу 👇", reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⚔️ Арена"), KeyboardButton(text="🎰 Казино")],
                [KeyboardButton(text="🎒 Снаряжение"), KeyboardButton(text="🏆 Топ")],
            ],
            resize_keyboard=True,
        ))
    else:
        await m.answer("В группе команды работают <b>ответом</b> на сообщение игрока или через <code>@username</code> / <code>ID</code>. Пиши <code>help</code> для списка.")

async def main() -> None:
    """Основная точка входа в приложение."""
    logging.basicConfig(level=Config.LOG_LEVEL, format=Config.LOG_FORMAT)
    
    if not Config.BOT_TOKEN or Config.BOT_TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        logging.critical("❌ ОШИБКА: Задай BOT_TOKEN в переменных окружения или в коде!")
        raise SystemExit("Missing BOT_TOKEN")
        
    logging.info("Initializing database...")
    logging.info("Generating masked bots...")
    ensure_masked_bots_exist(50)
    
    logging.info("Starting bot...")
    bot = Bot(Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать / вернуться"),
        BotCommand(command="help", description="Правила и команды"),
        BotCommand(command="admin", description="Админ-панель"),
        BotCommand(command="stats", description="Статистика бота"),
    ])
    
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("✅ Bot successfully started and polling!")
    
    try:
        await dp.start_polling(bot)
    finally:
        db.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
