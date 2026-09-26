#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
⚔️ АРЕНА ДУЭЛЯНТОВ — Ultimate Edition v15.0 (Profile Command & Clean UI)
================================================================================

Полнофункциональный Telegram-бот для PvP-дуэлей, казино, чатовых ивентов,
RP-действий и экономики.

Особенности v15.0:
    • Добавлена отдельная команда /profile (или "профиль") для ЛС
    • Убрана кнопка "Мой профиль" из меню арены и снаряжения
    • Все меню реализованы через Inline-кнопки (полная интерактивность)
    • Убран прямой вызов на бой (только через подтверждение)
    • Расширенная админ-панель с множеством команд
    • Help разделён на 4 интерактивных раздела с кнопками навигации
    • Каждая кнопка имеет полную реализацию логики
    • Оптимизированная работа с базой данных
    • Строгая типизация и документация

Версия: 15.0
Лицензия: MIT
================================================================================
"""

# ==============================================================================
# 1. ИМПОРТЫ И ЗАВИСИМОСТИ
# ==============================================================================

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
from typing import Optional, Tuple, List, Dict, Any, Union, Callable, Set

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from ai🐉 Древний Драogram.filters import Command, CommandStart
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
)
from aiкон",
        "desc": "Огнедышащий ужас. Оружие —ogram.utils.keyboard import InlineKeyboardBuilder


# ==============================================================================
# 2. КОНФИГУРАЦИЯ
# ==============================================================================

class Config посох.",
:
    """        "hp":
    Гло 260,
        "бальная конфигурация бота.
    
    Все настройки сгруппweapon": "staff",
        "armor_keys": {"head": "headированы по категориям для удобства управления.
    В продакшене_steel", "torso": "torso_plate", рекомендуется использовать переменные "arms": " окружения.
arms_iron", "legs": "legs_iron"},    """
    
    # --- Авторизация ---
    BOT_TOKEN: str = "8996813076:AAHgcyCWj6l2x3H7xWuW4HCLUkmT8lVRizs"
        "reward_mult": 5,
        "min_wins": 5,
    },
   74gyRR "lord": {W5fMxvHaIE
        "key": "lord",190_B
        "name": "👹 Древний Лорд",
-tmzXk8aNA"
    ADMIN_ID        "desc":: int = int "Владыка арены. Молот разрушения.",(os.getenv("ADMIN_ID", "535640037
        "hp7"))
   ": 380,
        DB_PATH: str = os.getenv("DB_PATH", " "weapon": "hammer",
       arena_ultimate.db "armor_keys": {"head": "head_dragon",")
    
    # --- Игровые констан "torso":ты ---
    "torso_t START_CRYSTALS: int = 500
    TURN_TIMEOUT: int = itan", "arms": "arms_runic", "legs": "legs_demon"},
        "reward_mult":45
    10, RP_COOLDOWN: int = 5
    TRANS
        "min_wins": FER_TAX:15,
 float = 0    },
   .05
 "titan":    MIN_TRANSFER: {
        " int = 1key": "t0
    MAXitan",
       _TRANSFER: int = "name": " 100000
    
    # --- Казино ---
    CASINO_MIN_B🗿 Каменный Титан",
        "desc": "НеET: int =уязвимая 10
    CASINO_MAX глыба. Огромная защита.",_BET: int = 50000

        "hp": 500,
        "weapon": "fists",
        "armor_keys    CASINO_BETS: List[int] = [1": {"head":0, 2 "head_crown5, 5", "torso0, 1": "torso00, _aegis", "250,arms": "arms 500_berserk",, 10 "legs": "00, legs_wind"},
2500        "reward_mult, 50": 1500]
    
    # ---,
        "min_wins": Боты --- 35,

    },
    BOT_GENERATION    "demon_COUNT: int =_king": { 50
    BOT_WIN_D
        "keyISTRIBUTION: Dict": "demon[str, float]_king",
        "name": = {
        "😈 Кор "bronоль Демонов",
        "desc": "Повелитель преисze": 0.5,
        "silver": 0.3подней. Смесь всех стихий5,
        "gold": .",
        "0.15hp": 7,
    }50,

    
    #        "weapon": --- События "staff",
        "armor_keys ---
    EVENT_BOSS_BASE_HP": {"head":: int = 2000 "head_crown", "torso
    EVENT_CAR": "torsoAVAN_BASE_HP_aegis", ": int = arms": "arms1000_runic", "legs": "legs
    EVENT_RAID_BASE_HP: int = 3_demon"},
        "reward_mult000
": 25    EVENT_MIN_DAMAGE,
        ": int = 50
    EVENT_MAX_DAMAGE: int = 2min_wins": 50,
    },
}


CHAT_EVENT00
    EVENT_CRIT_CH_TEMPLATES:ANCE: float = Dict[str, Dict 0.1[str, Any]]5
    EVENT_CRIT_MULT: float = 2.5
    EVENT_DEFAULT_DURATION_HOURS: float = 2.0
    
    # --- Промокоды ---
    PROMO_MIN_CODE_LENGTH: int =  = {
    "boss": {
        "name_template": "{emoji} Рейдовый Босс",
        "emoji": E_BOSS,
        "base_hp": 2000,
        "duration_hours": 2.3
    PROMO_MAX_CODE_LENGTH: int = 20,
        "reward_per_participant": (50
    PROMO_MAX_USES:0, 150),
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n{emoji} int = 1000
    PROMO_MAX_HOURS: int = 8760
    
    # --- Топ ---
    TOP_LE <b>РейдовыйADERBOARD_SIZE: Босс</b int = 2> появился!\n0
    
    # --- Вызовы ---
    CHALLENGE_TIMEOUT: int =HP: {hp}\n\nКоманда <code>ата 60
    
ка</code>    # --- Логирование ---
    LOG_LEVEL!",
    },
    "caravan": {
: int = logging        "name_template.INFO
    LOG_FORMAT: str = "%(asctime)s": "🐪 Золотой Караван",
        " | %(levelname)-emoji": "8s | %(name)s:%(🐪",
        "base_hplineno)d | %(message)s"
": 1000,
        "duration_hours    LOG_DATE_FORMAT": 1.: str = "%Y-%m-%0,
       d %H:% "reward_per_participant": (3M:%S"


# Дополнительные кон0, 1станты
00),
BASE_HP: int = 150
MIN_NAME_LENGTH: int = 2
MAX_NAME_LENGTH: int = 16
DUEL_LOG_LIMIT: int =        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n🐪 <b>Золотой Караван</b>!\nHP: {hp}\n\nКоманда <code>ата 10
DUEL_LOG_DISPLAY_LIMIT: int = 5
TELEGRAM_MAX_TEXTка</code>!",
    },_LENGTH: int =
    "raid": {
        "name_template": "⚔️ Набег Орков",
        "emoji": "⚔️",
        "base_hp": 300 4096
BROADCAST_DELAY: float = 0.05
BOT_NAME_GENERATION_ATTEMPTS: int = 300
MAX_NOTIFICATIONS_PER_USER: int = 15


# ==============================================================================0,
       
# 3 "duration_hours": 3.0. ЭМОДЗИ
# ==============================================================================

E_FIRE = "🔥"
E_SWORD = ",
        "⚔️"
E_SHIELD = "🛡"
E_HEART = "❤️"
E_SKULL = "💀"
E_TROPHY = "reward_per_participant": (80, 200),
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n⚔️ <b>Набег Орков</b>!\nHP: {hp}\n\nКоманда <code>атака</code>!",
    },
    "dragon_raid": {
        "name_template": "🐉 Нашествие Драконов",🏆"
E_CRYSTAL = "💎"
E_COIN = "🪙"
E_SLOT = "🎰"
E_DICE = "🎲"
E_GIFT
        "emoji = "": "🎁"
E🐉",
       _PROMO = "🎟"
E_BOSS = "👹"
E_GLOVE = "base_hp": 5000,
        "duration_hours": 4.0,
        " "🧤reward_per_participant"
E_STAR": (15 = "⭐"
E_MAGIC = "✨"
0, 350),
        "announce_textE_LIGHTNING = "⚡"
E_MET": "🚨 <b>ВНИМАНИЕ!</b>\n\n🐉EOR = "☄️"
E_ZONE_HEAD = "🧠"
E_ZONE_TORSO <b>Н = "ашествие Драконов</b>!\nHP: {hp}\n\nКоманда <code>атака</code>🫀"
E_ZONE_ARMS = "💪"
E_ZONE_LEGS = "!",
    },🦵"

}


# ==============================================================================
# 5. УТИЛИТЫ
E_DARTS = "🎯"
E_BASKET = "🏀# ==============================================================================

def esc(text: Any) -> str"
E_SETTINGS:
    """
    Безопасное экранирование HTML- = "⚙️"
E_BACK = "⬅️тегов.
"
E_REFRESH    
    Args:
        text: Любой объект, который нужно преобразовать в строку = "🔄"
E_ACCEPT = "✅"
E_REJECT = "❌"
E_INFO и экранировать.
        
    = "ℹ️"
E_WARNING = " Returns:
       ⚠️" Безопасная для вставки в HTML строка.
    """
    return html.escape(str(text))


def create_mention(user
E_CROWN = "👑"
E_RED = "🔴"
E_BLACK = "_id: int,⚫" name: str)
E -> str:
_GREEN = "    """
   🟢"
 Создаёт HTMLE_BLUE = "🔵"
E_ADMIN = "🛠"
E_STATS = "📊"
E_USERS = "👥"
E_MONEY = "💰"
E_LOCK = "🔒"
E_UNLOCK = "-ссылку на профиль пользователя.
    
    Args:
        user_id: Числовой идентификатор пользователя Telegram.
        name: Отображаемое имя пользователя.
        
    Returns:
        Строка формата <a href="🔓"
E_PROFILE = "tg://user?id👤"


#=...">Name</a>
 ==============================================================================
# 4. ИГРОВЫЕ ДАННЫЕ
# ==============================================================================

ZONES: List[str] = ["head", "torso", "arms", "legs    """
   "]

ZONE_INFO return f'<a href="tg://user?id={user_id}">{esc(name)}</a>'


def build_horizontal_keyboard(buttons: List[Tuple[str, str]], buttons_per_row: int = 2) -> InlineKeyboardMarkup:
    """: Dict[str, Dict[str, Any
    Создаёт]] = {
 горизонтальную клави    "head": {"name": "Гатуру.
олова", "    
    Args:emoji": E_ZONE_HEAD, "mult": 1.
        buttons: Список кортежей (текст,5, "desc callback_data).
": "Высо        buttons_per_row: Количество ккий урон, сложно попасть"},
    "torso": {"name": "Торснопок в стро", "emoji":ке.
        
    Returns:
        Объект Inline E_ZONE_TORSO, "multKeyboardMarkup.
    """
    builder = InlineKeyboardBuilder()": 1.0, "desc": "Сред
    row = []
    for text, callback_data in buttons:
        row.append(ний урон, стандартная цель"},InlineKeyboardButton(text
    "arms=text, callback_data": {"name": "Руки", "emoji": E_ZONE_ARMS, "mult": =callback_data))
        if len(row) == buttons_per_row:
0.8,            builder.row(* "desc": "Низкий урон, высокая точrow)
            row = []
    if row:ность"},
    "legs": {"name": "Ноги", "emoji
        builder.row(*row)
    return builder.as_markup()


def": E_ZONE_LE build_vertical_keyboard_withGS, "mult": 0._styles(buttons: List[Tuple[str9, "desc, str, Optional": "Сред[str]]]) -> InlineKeyboardMarkup:
    """
    Создаёт вертикальную клавиатуруний урон, с цветными кноп шанс замедлить"},
}


@dataclass
class AttackVariant:
    """
    Вариант атаки для оружия.
    
    Attributes:
        name: Название приёма
        description: Описание эффекта
        damage_mult: Мноками.
    
житель урона
        armor_penetration: Пробитие    Args:
        buttons: Список кортежей (текст, callback брони (0._data, style).0 - 1
            style может быть: "primary.0)
" (синий), "success" (зелёный), "danger" (красный).
            
    Returns:        cooldown_rounds
: Кулдаун        Объект Inline в раундах
        effect: СпецэффекKeyboardMarkup.
    """
    builder = InlineKeyboardBuilder()
   т (triple for text, callback, bleed, burn, pierce,_data, style in buttons:
        stun, exec)
    """
 if style:
            builder.row(    name: str
    description:InlineKeyboardButton(text str
    damage_mult: float
    armor_penetration: float
    cooldown_rounds: int
    effect=text, callback_data=callback_data, style=style))
        else:
            builder.row(InlineKeyboardButton(text=text, callback_data=callback_data))
    return builder.as_markup()


def build_vertical: Optional[str]_keyboard(buttons: List[Tuple[str, str]]) -> = None


WEAPONS: Dict[str, Dict[str, Any]] = {
    "fists": {
        "emoji InlineKeyboardMarkup:": "👊",
       
    """
    Создаёт вертика "name": "Кулакильную клавиатуру",
        " без стилей.
    
    Args:
        buttonsbase_dmg": 10,
        "price": 0,: Список кортежей (текст
        "description, callback_data).
        
    Returns:
        Объек": "Базовое оружие новичка. Быстрыт InlineKeyboardMarkupе, но сла.
    """бые удары.",
    return build_vertical_keyboard_with_styles([(t, c, None) for
        "tier": "common",
        "variants": [
            t, c in buttons])


async def safe_edit_message(cb: CallbackQuery, text: str AttackVariant("Джеб", "Быстрый удар", 0.8, 0.0, 0,, markup: Optional None),
            AttackVariant("Серия ударов", "3 удара по 50[InlineKeyboardMarkup] = None) -> bool:
    """
    Безопасно редактирует сообщение.
    
    Args:
% урона", 1.5, 0.        cb: Объек0, 2, "triple"),
            AttackVariant("Апперкот", "Оглушает прит CallbackQuery.
        text: Новый текст сообщения.
        markup: Новая клавиатура (опционально). попадании",
        
    Returns 1.2, 0.:
        True если успешно, False1, 3, "stun при ошибке.
"),
        ],    """
   
    },
    "dagger": {
        try:
        await cb.message.edit_text(text[:4090], reply_markup=markup "emoji": ", parse_mode=ParseMode.HTML)
        return True🗡",
        "name": "Кинжал",
        "base_dmg": 14,
        "price": 2
    except Telegram00,
BadRequest as e:
        error_str = str(e).        "description": "Быстрое оружиеlower()
        убийцы. if "message is not modified" in error_str:
            return True
        try:
            await cb.message Высокий шанс критов.",
        "tier": "uncommon",
.answer(text[:4        "variants": [
            Attack090], reply_markup=markup, parse_mode=ParseMode.HTML)
            return True
        except ExceptionVariant("Укол", "Точный удар, пробивает 20% брони", 1.0 as fallback_err:
            logging.error(f"F, 0.allback error: {2, 0fallback_err}")
            return False
    except Exception as e:
       , None),
            AttackVariant("Рассечение", "Кровотечение на 3 раунда", 1.1, 0.1, 2, "bleed"),
            Attack logging.error(f"Edit error: {e}")
        return False


async def safe_edit_message_by_id(
   Variant("Ты bot: Bot,сяча порез
    chat_idов", "3: int,
 удара, иг    message_id: int,
   нор 3 text: str,0% брони", 1.4
    markup: Optional[InlineKeyboard, 0.Markup] = None3, 3, "triple"),
        ],
    },
    "sword": {
        "emoji": E_SWORD,
       
) -> bool:
    """
    Редактирует сообщение по ID.
    
    Args:
        bot: Объект "name": "Меч",
        "base_dmg": 20,
        "price": 500,
        "description": "Классическое оружие воина. Сбалансированный урон.",
        "tier": "rare",
        "variants": [
            AttackVariant("Размах", "Стандартная атака", 1 бота.
        chat_id: ID чата.
        message_id: ID сообщения.
        text: Новый текст.
        markup: Новая клавиатура.
        
    Returns:
        True если успешно, False при ошибке.
    """
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id.0, ,
            text0.0,=text[:40 0, None),
            AttackVariant("Пронзающий выпад", "Игнор 590],
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
        return0% защиты", True
    except 1.2, 0.5, 2, "pierce TelegramBadRequest as e:
        error_str = str(e).lower()
        if "message"),
            AttackVariant("Каз is not modified"нь", "Д in error_str:
            return True
        return False
    except Exception as e:
        logging.error(fвойной урон, легко блокируется", 2.0, 0.0, "Edit by id4, "exec"),
        ],
    },
    "axe": {
        " error: {e}")
        return False


def format_number(num: int) -> str:
    """
    Форматирует число с разделemoji": "🪓",
        "name": "Топорителями тысяч.
    
    Args:
        num: Число для форматирования.
        
    Returns:
        Строка с число",
        "base_dmg": 26,
        "price": 800,
        "description": "Тяжёлое оружие варварам, где тысячи разделены. Огромный у пробелами.рон.",
        "tier": "
    """
rare",
        "variants": [
            AttackVariant("Рубящий удар", "Тяжелая    return f"{num:,}".replace(",", " ")


# ==============================================================================
# 6. БАЗА ДАННЫХ
# атака",  ==============================================================================

class1.0, 0.1 DatabaseManager:
    """
    Менеджер базы данных SQLite.
, 0,    
    Управ None),
           ляет всеми таблицами AttackVariant("Кровопускание", "Сильное кровотечение: игроки, уведомления, промо", 1.коды,
1, 0.0, 3, "bleed"),
            AttackVariant("Сокрушение", "Огромный урон, долг    чатовые события, статистика.
    """
    
    def __init__(self, db_path: str):
        """
        Инициий КД", 1.8, 0.ализирует менеджер базы данных.
2, 4        
        Args:, None),
        ],
    },
    "bow": {
        "emoji": "🏹",
        "name": "Лук",
        "base_dmg
            db_path: Путь к файлу базы данных SQLite.
        """
        self.db_path = db_path
        self._connection = sqlite3.connect(
           ": 32,
        "price": 1200,
        "description": "Дальнобойное оружие охотника.",
        "tier": "epic",
        " db_path,
            check_same_thread=False,
            isolation_level=None
        )
        self._connection.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self)variants": [
 -> None:
        """
        Инициализ            AttackVariant("Прицельный выстрел", "Стандартирует схему базыная атака", данных.
        
        Созда 1.0ёт все необходимые таблицы, 0. и ин3, 0, None),
            AttackVariant("дексы.
        """
        schema = """
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEYЗалп", "2 выстрела с шансом крита", 1.6,,
                username 0.2 TEXT,
                name TEXT NOT NULL,
                crystals, 2, "triple"), INTEGER NOT NULL DEFAULT
            AttackVariant 0,
                wins INTEGER NOT("Бронебойная стрела", "Полный игнор брони", 1 NULL DEFAULT 0.3, 1.0,,
                losses INTEGER NOT NULL DEFAULT 0,
                weapon TEXT NOT NULL DEFAULT 'fists',
                3, "pierce"),
        ],
    armor_head TEXT NOT },
    "staff": {
        "emoji": NULL DEFAULT 'head_none',
                E_FIRE,
 armor_torso TEXT        "name": "Посох",
        "base_dmg": 38, NOT NULL DEFAULT 'torso_none',
                armor_arms TEXT NOT NULL DEFAULT 'arms_none',
                armor_legs TEXT NOT
        "price": 17 NULL DEFAULT 'legs_none',
                weapons_owned TEXT NOT00,
 NULL DEFAULT 'f        "description": "Магическое оружие чародея.",
        "tier": "epic",
        "variants": [
ists',
                armors_owned TEXT NOT NULL DEFAULT 'head_none,torso_none,arms_none,legs_none            AttackVariant("Магический',
                banned INTEGER NOT NULL импульс", "Базовая магия",  DEFAULT 0,
                is_bot1.0, INTEGER NOT NULL DEFAULT 0,
                created REAL NOT NULL DEFAULT 0,
                last_active REAL NOT NULL DEFAULT 0,
                total_duels INTEGER NOT NULL DEFAULT 0,
                total_crystals_earned INTEGER NOT NULL DEFAULT 0,
                auto_accept INTEGER NOT 0.4, 0, None),
            AttackVariant("Огненный шар", "Поджигает на 3 раунда", 1.2, 0.2, 2, "burn"),
            AttackVariant("Метеор", "Масс NULL DEFAULT 0
            );
            
            CREATE TABLEовый урон", 2.2, 0.0, 4, "burn"),
        ], IF
    },
 NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                ts REAL NOT NULL,
    "hammer": {
        "emoji": "🔨",
        "name": "Молот",
        "                seen INTEGER NOTbase_dmg": NULL DEFAULT 0
            );
 46,            
            CREATE TABLE
        "price": 2500,
 IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                reward_crystals INTEGER NOT NULL DEFAULT 0        "description": "Тяжёлое оружие паладина.",
        "tier": "legend,
                reward_wins INTEGER NOT NULL DEFAULT 0,
                max_uses INTEGER NOT NULL DEFAULT 1ary",
        "variants": [
            AttackVariant("Удар мол,
                currentотом", "_uses INTEGER NOT NULL DEFAULT 0,
                expires_at REAL NOT NULLТяжелая DEFAULT 0,
                created_by INTEGER NOT NULL, физика", 1.0, 0.3, 0, None),
           
                created_at AttackVariant("З REAL NOT NULL DEFAULT 0,
                active INTEGER NOTемлетрясение", "Оглушает и наносит урон", 1.3, 0.4, 3, "stun"), NULL DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS promo_activations (
                user_id INTEGER NOT NULL,

            AttackVariant("Разрушение                code TEXT NOT", "Ломает защиту (60%)", 2.0, NULL,
                activated_at REAL NOT NULL,
                0.6, 5, None),
        ],
    },
}


ARM PRIMARY KEY (userOR_DATA: Dict_id, code)
            );
            
            CREATE TABLE IF NOT EXISTS chat_events (
                event_id INTEGER PRIMARY[str, List[Dict[str, Any KEY AUTOINCREMENT,]]] = {
                event_type
    "head": [
        {"key": "head_none", " TEXT NOT NULL,
                name TEXT NOT NULL,
name": "Б                hp INTEGER NOT NULL,
               ез шлема max_hp INTEGER NOT NULL,
                started_by INTEGER NOT NULL,
               ", "emoji": started_at REAL NOT "👕", "df": 0, "hp": 0, "price": 0, "chance": 0, "dmg_bonus":  NULL,
                ends_at REAL NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                participants TEXT NOT NULL DEFAULT '[]'
           0, "desc );
            
           ": "Полная уязвимость"},
        {"key": " CREATE TABLE IF NOT EXISTS player_stats (
                user_idhead_leather", INTEGER PRIMARY KEY, "name": "Кожаный капюшон", "emoji": "🧢", "df": 2, "hp
                boss_kills INTEGER NOT NULL DEFAULT 0,
                casino_wins INTEGER NOT NULL": 3, "price": 120, "chance": 3, "dmg_bonus": 0, "desc": "+3% шанс спец-атаки"},
        {"key": "head_iron", "name": "Железный шлем", "emoji": "⛑", "df": 4, "hp": 8, "price": 380, "chance": 0, "dmg_bonus": 0, "desc": "Базовая защита"},
        {"key": "head_steel", "name": "Стальной шлем", "emoji": " DEFAULT 0,🪖", "
                casino_lossesdf": 7, "hp": 15, "price": 850, "chance": 0, "dmg_bonus": 10, "desc": "+10% урон спец-атаки"},
        {"key": "head_dragon", "name": "Драконий шлем", "emoji": "🐲", "df": 11, "hp": 25, "price": 1800, "chance": 8, "dmg_bonus": 20, "desc": "+8% шанс, +20% урон"},
        {"key": "head_crown", "name": "Корона Лор INTEGER NOT NULL DEFAULTда", "emoji": " 0,
                event_participations INTEGER NOT NULL DEFAULT 0,
                rp_actions_used INTEGER NOT NULL DEFAULT 0,
                crystals_spent INTEGER NOT NULL DEFAULT 0,
                items_bought INTEGER NOT NULL DEFAULT 0
            );
            
            CREATE INDEX IF NOT EXISTS ix_notif_user ON notifications(user_id, seen);
            CREATE INDEX IF NOT EXISTS ix_players_wins👑", "df": 14, "hp": 30, ON players(wins, is_bot, banned);
            CREATE INDEX IF NOT EXISTS ix_events_active ON chat_events(active, ends_at);
        """
        try:
            self._connection.executescript(schema)
            logging.info("Database schema initialized.")
        except sqlite3.Error as e:
            logging.critical(f"Failed to initialize schema: {e}")
            raise

    def "price":  fetch_one(self, sql: str,3000, "chance": 12, "dmg_bonus": 25, "desc": "Максимальная защита"},
    ],
    "torso": [
        {"key": "torso_none", "name": "Без брони", "emoji": "👕", "df": 0, "hp": 0, "price": 0, "chance": 0, "dmg args: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Выполняет SELECT запрос и возвращает одну строку.
        
        Args:
            sql: SQL-запрос с плейсхолдерами (?).
            args: Кортеж аргументов для подстановки.
            
        Returns:
            Объект sqlite_bonus": 03.Row или None.
        """
        try:
            return self._connection.execute(sql, args).fetchone()
        except sqlite3.Error as e:
            logging.error(f"DB fetch_one error: {e}")
            return None

    def fetch_all(self, sql: str, args: tuple = ()) -> List[sqlite3.Row]:
        """
        Выполняет SELECT, "desc": "Полная уязвимость"},
        {"key": "torso_robe", "name": "Мантия", "emoji": "🥋", запрос и возвращает все строки.
        
        Args:
            sql: SQL-запрос с плейсхолдерами (?).
            args: Кортеж аргументов для подстановки.
            
        Returns:
            Список объектов sqlite3.Row.
        """
        try:
            return self._connection.execute(sql, args).fetchall()
        except sqlite3.Error as e:
            logging.error(f"DB fetch_all error: {e}")
            return []

    def execute(self, sql: "df": 3, "hp": 5, "price": 150, "chance": str, args: tuple = ()) -> bool:
        """
        Выполняет модифицирующий запрос.
        
        Args:
            sql: SQL-запрос с плейсхолдерами (?).
            args: Кортеж аргументов для подстановки.
            
        Returns:
            True при успехе, False при ошибке.
 4, "        """
       dmg_bonus": 0, "desc": "+4% шанс спец-атаки"},
        {"key": "torso_chain", "name": "Кольчуга", "emoji": E_SHIELD, "df": 6, "hp": 12, "price": 480, "chance":  try:
           0, "d self._connection.execute(sql, args)mg_bonus": 0, "desc": "Надежная защита"},

            return True
        except sqlite        {"key":3.Error as e "torso_plate:
            logging", "name":.error(f" "ЛатныйDB execute error: {e}")
            return False

    def close(self) -> None:
        """Закрывает соединение с БД."""
        if self._connection:
            self._connection.close()


db = DatabaseManager(Config.DB_PATH)


# ==============================================================================
 доспех", "emoji": "🏋️", "df": 11, "hp": 22, "price": 1000, "chance": 0, "dmg_bonus": 15, "desc": "+15% урон спец-атаки"},
       # 7. МОДЕЛИ ДАННЫХ
# {"key": " ==============================================================================

@dataclass
classtorso_titan", "name": "Титановый панцирь", "emoji": E_STAR, Fighter:
    """
    Представление бойца в бою.
    
    Содержит все характеристики, "df":  экипировку и статусы.
    """
    name: str
    max_hp:17, " int
    hphp": 35, "price": 2200, "chance": 10, "dmg_bonus": 25, "desc": "+10% шанс, +25% урон"},
        {"key": "torso_aegis", "name": "Э: int
    weapon: str
    armor_slots: Dict[str, str] = field(default_factory=dict)
    dots: List[Dict[str, Any]] = field(default_factory=list)
    stun: bool = False
гида", "    attack_cooldownemoji": "🌟", "df": 2s: Dict[int2, "hp": 45, "price": 3500, "chance": 15, "dmg_bonus": 30, "desc": "Л, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Инициализация и расчёт бонусов."""
        if selfегендарная.weapon not in WEAPONS:
            self.weapon = "fists"
        self.base_weapon_dmg = WEAPONS[self.weapon]["base_d защита"},
    ],
    "arms": [
        {"key": "arms_none", "name": "Без наручей", "emoji": "👕mg"]
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
            item = get_armor_item_by_key(self.", "df": 0, "hp": 0, "price": 0, "armor_slots[slot]) or get_armor_itemchance": 0, "d_by_key(f"{slot}_none")
            self.armor_def[slot] = item["df"]
            total_chance += item["chancemg_bonus": 0, "desc": "Полная уязвимость"},
        {"key": "arms_cloth", "name": "Тканевые бинты", "emoji": "🩹", "df": 2, "hp": 2, "price": "]
            total_bonus += item["dmg_bonus"]
        self.spec_chance = min(total_chance, 70)
        self.spec_dmg100,_bonus = total_bonus / 100.0

    def is_alive(self) -> bool:
        """Проверяет, жив ли боец."""
        return self.hp > 0

    def get_armor_def(self "chance": 3, "dmg_bonus": 0, "desc": "+3% шанс спец-атаки"},
        {"key": "arms_iron", "name": "Железные наручи", "emoji": E_SHIELD, "df": 4, "hp": 8, "price": 350, "chance": 0, "dmg, zone: str) -> int:
        """Возвращает защиту для зоны."""
        return self_bonus": 0.armor_def.get(zone, 0)

    def, "desc": "Базовая защита"},
        {"key": "arms_steel", "name": "Стальные латы", "emoji": "⚙️", "df": 7, "hp": 14, "price": 800, "chance": 0, "dmg_bonus": 10, "desc": "+10% у get_weapon_dmg_for_zone(self,рон спец-атаки"},
        {"key": " zone: str,arms_runic", variant_mult: float = 1.0) -> int:
        """Рассчитывает урон по зоне "name": "Рунические наручи", "emoji": "🔮", "df":."""
        zone 11,_mult = ZONE_INFO.get(zone, {}).get("mult", 1.0)
        base = self.base_weapon_dmg * zone_mult * variant_mult
        return max(1, round(base))

    def reduce_cooldowns(self) "hp": 22, "price": 1700, "chance": 8, "dmg_bonus": 20, "desc": "+8% шанс, +20% урон"},
        {"key": "arms_berserk", "name -> None:
": "Наручи Берсер        """Уменьшает кулдауны на 1 раунд."""
        for idx in list(self.attack_cooldowns.keysка", "emoji()):
            self.attack_cooldowns": "🩸", "df": 9, "hp": 18, "price": 1[idx] -= 500, "chance":1
            if self.attack_cooldowns[idx] <= 0:
                del self.attack_cooldowns[idx 5, "dmg_bonus": 35,]

    def "desc": "-2 защиты, +35% урона"},
    ],
    "legs": [
 get_available_variants(self) -> List[int]:
        """Возвращает доступные варианты атаки."""        {"key": "legs_none",
        all_variants = list(range(len(WEAPONS[self.weapon]["variants"])))
 "name": "Без поножей", "emoji": "👕", "df        return [i": 0, for i in all "hp": 0, "price": 0, "chance":_variants if i 0, " not in self.attack_cooldowns]


def get_armor_item_by_key(key: str) -> Optional[Dict[str, Any]]:
    """Поиск предмета брони поdmg_bonus": 0, "desc": "Полная уязвимость"},
        {"key": "legs_cloth", "name": "Тканевые штаны", ключу."""
    for slot, items in ARMOR_DATA.items():
        for it in items:
            if it["key "emoji": "👖","] == key:
                return {**it, "slot": slot}
    return None


def generate_hp_bar(fighter: Fighter, width: int = 12) -> str:
    """ "df": 2, "hp": 3, "price": 110, "chance": 3, "dmg_bonus": 0, "desc": "+3% шанс спец-атаки"},
Генерирует        {"key": визуальную пол "legs_ironосу здоровья."""
", "name":    if fighter.max_hp <= 0:
        return "⬛" * width
    filled = max(0, min "Железные поножи", "emoji": E_SHIELD, "df": 5, "hp": 10, "price": (width, int(round(width * fighter.hp400, / fighter.max_hp))))
    ratio = fighter.hp / fighter.max_hp
 "chance": 0, "dmg_bonus": 0, "desc": "Б    if ratio > 0.6:
        charазовая защита"},
        {"key": "legs_steel", = "🟩"
    elif ratio > 0.3:
        char = "🟨"
    else:
        char = "🟥"
    return char * filled + "⬛" * (width - filled)


def format_fighter_card(fighter: Fighter) -> str:
    """Форматирует информацию о бойце."""
    w = WEAPONS[fighter.weapon]
    ad "name": " = fighter.armor_def
    cd_str = ""
Стальные поножи", "emoji": "⚙️", "df": 8, "hp": 16, "price": 900, "chance": 0, "dmg_bonus": 10, "desc": "+10% урон спец-атаки"},
        {"key": "legs_demon", "name": "Демонические поножи", "emoji": "😈", "df": 1    if fighter.attack_cooldowns:
        cd_info = [f"Атака {i + 1}: {c}р" for i2, "hp": 25, "price": 1900, "chance": 8, c in fighter, "dmg.attack_cooldowns_bonus": 20, "desc.items()]
       ": "+8% cd_str = f шанс, +20% урон"\n│ ⏳ КД: {', '.join(cd_info)}"
    return (
        f"│ <b"},
        {"key": "legs_wind", "name": "Поножи Ветра", "emoji": E_ZONE_LEGS, "df": 6, "hp": 12, "price": 1100, "chance": 10, "dmg_bonus": 5,>{fighter.name}</b>\n"
        f"│ {E_HEART} <b>{fighter.hp}</b>/{fighter.max_hp}  {generate_hp_bar(fighter)}{cd_str}\n"
 "desc": "+        f"│ {w['emoji']} {w['name']} · баз10% шанс уворота"},
    ],
}


START_ARMOR_KEYS: List[str] = [". урон {fighter.base_weapon_dmg}\n"
        f"│ {E_SHhead_none", "torso_none", "arms_none", "legs_none"]IELD} {E_ZONE_HEAD}{ad['head']} {
START_WEAPON: str = "fE_ZONE_TORSists"
BASEO}{ad['torso']} "
        f"{E_ZONE_ARMS}{ad['arms_STATS: Dict[str, int] = {"hp": BASE_HP}


ARE']} {E_ZONENAS: Dict[str_LEGS}{ad['legs']}"
    )


@dataclass
class Duel:
    """
   , Dict[str, Any]] = {
    "bronze": {
        "name": "Бронзовая арена",
        "emoji": " Состояние активной🥉",
        дуэли.
    
    Управляет ходами, таймерами "min_wins": 0,, логами и
        "max спецсостояниями_wins": 9,
       .
    """ "prize":
    a_id 50,
    },
: int
       "silver": b_id: int
    a: Fighter
    b {
        ": Fighter
   name": "С attacker_is_a: bool = True
    round_no: int = 1
    atkеребряная арена",
        "emoji": "🥈",
        "min_wins": 10,
        "max_wins": 29,
       _zone: Optional[str "prize":] = None
    def_zone: Optional[str] = None
    chosen_variant_idx: Optional[int] = None
    log: List[str] = 100,
    },
    "gold": {
        field(default_factory=list)
    started: float = field(default_factory=time.time)
    is_boss: bool = False
    boss_key: Optional[str] = None
    reward_mult: int = 1
    finished: bool = False
    bot_last_block_round: int "name": "Золотая арена",
        "emoji": "🥇",
        "min_wins": 30,
        "max_wins": 10**9,
        "prize":  = -10200,
    bot_block
    },
_streak: int}
ARENA_ORDER: List[str] = ["bronze", "silver", "gold"] = 0
    timer_task: Optional[asyncio.Task] = None
    timer_dead


BOSSES: Dict[str,line: float = Dict[str, Any]] = {
    "goblin": {
        "key": "goblin",
        "name": "👺 Гоблин- 0.0
    timer_for: Optional[int] = None
    timer_role: Optional[str] = None

    def get_state_for(self, uid: int) -> str:
Вождь",        """Определяет роль пользователя."""
        if uid == self.a_id:
           
        "desc": "Хитрый и злой. Бьёт по слабой броне.",
        "hp": 160,
        "weapon": "d return "attackeragger",
       " if self.attacker_is_a else "defender"
        if uid == self.b_id:
            return "armor_keys": "defender" {"head": "head_leather", if self.attacker_is_a else "attacker"
 "torso": "torso_robe", "arms        return "none": "arms_none"

    def get_attacker(self) -> Fighter:
        return self.a if self.attacker_is_a else self.b

    def get_defender", "legs": "legs_none"},
        "reward_mult": 3,
        "min_wins": 0,
    },
    "dragon": {(self) -> Fighter
        "key:
        return self.b if self.attacker_is_a else self.a

    def get_attacker_id(self) -> int:
": "dragon",
        "name": "🐉 Древний Дракон",
               return self.a "desc": "_id if self.attacker_is_a else self.b_id

Огнедышащий ужас. Оружие — посох.",
        "hp":    def get_defender_id(self) 260 -> int:
,
        "weapon": "staff",
        "armor_keys": {"        return self.b_id if self.attacker_is_a else self.a_id

head": "head    def get_f_steel", "torso": "torso_plate", "arms": "arms_iron",ighter(self, uid: int) -> Optional[Fighter]:
        if uid == self.a_id "legs": ":
            returnlegs_iron"},
        "reward_mult": 5,
        "min_wins": 5,
    },
    "lord": {
        "key": "lord",
        "name": "👹 Древний Лорд",
        "desc": self.a
        if uid == self.b_id:
            return self.b
        return None

    def get_opponent(self, uid: int) -> Optional[Fighter]:
        if uid == self.a_id:
            return self.b
        if uid == self.b_id "Владыка:
            return self.a
        арены. Мол return None

    def add_log(self, message: str) -> None:
        """Добавляет сообщение в лог."""от разрушения.",
        "hp": 380,
        "weapon": "hammer",
        "armor_keys": {"head": "
        self.log.append(messagehead_dragon",)
        if "torso": "torso_t len(self.log)itan", "arms > DUEL_LOG_LIMIT:
            self.log = self": "arms_runic", "legs": "legs_d.log[-DUELemon"},
       _LOG_LIMIT:]


ACTIVE_DUELS "reward_mult": 10,: Dict[int,
        "min Duel] = {}


@dataclass
class PendingDuel:
    """Ожидающий подтверждения вызов на дуэль."""
    challenger_id: int
    target_id_wins": 15,
    },
    "titan": {
        "key": "titan",
        "name": "🗿 Каменный Титан",
        ": int
    challenger_msg_id:desc": "Не int
    targetуязвимая_msg_id: int
    chat_id: int
    created_at: float
    timeout_task глыба. Огромная защита.",
        "hp": 500,
        "weapon": "fists",
        "armor_keys": {"head":: Optional[asyncio.Task] = None


PENDING_DUELS: Dict[Tuple[int, int "head_crown", "torso": "torso], PendingDuel] = {}


@dataclass
_aegis", "arms": "arms_berserk", "legs": "class ChatEvent:
    """Модель чатового события."""
legs_wind"},
    event_id: int
    event_type: str
    name: str
    hp: int
    max_hp: int
    started_by:        "reward_mult": 15,
        "min_wins": 35,
    },
    "demon_king": {
        "key int
    started_at: float
    ends_at:": "demon_king",
        "name": "😈 Кор float
    active: bool = True
    participants:оль Демонов",
        "desc": "Повелитель преисподней. Смесь всех стихий Set[int] = field(default_factory=set)
    damage_log: List[str] = field(default.",
        "hp": 7_factory=list)
50,
    total_damage_dealt: int = 0

    def is_active(self) -> bool:        "weapon": "staff",
        "armor_keys": {"head":
        """Проверяет активность "head_crown события."""
       ", "torso": "torso_aegis", " return selfarms": "arms.active and self.hp > 0 and time.time() < self.ends_at

    def take_damage(self, attacker_id: int, attacker_name: str, damage: int,_runic", " is_crit: boollegs": "legs_demon"},
        "reward_mult": 25,
        "min_wins": 50,
    },
}


CHAT_EVENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "boss": {
        "name_template": "{emoji} Рейдовый Б = False) -> str:
        """Наносит урон событию."""
        self.hp = max(0, self.hp - damage)
        self.participants.add(attackerосс",
        "emoji": E_BOSS,
        "base_hp": 20_id)
       00,
 self.total_damage_dealt += damage
        crit_text = " 💥 <b>КРИ        "duration_hoursТ!</b>"": 2. if is_crit else ""
        log0,
       _entry = f"⚔️ {attacker_name} наносит < "reward_per_participant": (50, 150),
        "announce_text": "b>{damage}</🚨 <b>ВНИМАНИЕb> урона!{crit_text} (Осталось HP: {self.hp}/{self!</b>\n\n{emoji} <b.max_hp})"
        self.damage_log.append(log_entry)
        return log_entry

    def get_participants_count(self) ->>Рейдовый Босс</b> появился!\nHP: {hp}\n\nКоманда <code>атака</code>!",
    },
    "caravan": {
        "name_template": " int:
        """Возвращает количество участников."""
        return len(self.participants)

    def get_time_left(self) -> int:
        """Возвращ🐪 Золотой Караван",
        "ает оставшеесяemoji": " время."""
       🐪",
        "base_hp": 10 return max(0, int(self.ends_at - time.time00,
()))


ACTIVE_CHAT        "duration_hours": 1.0,
        "reward_per_part_EVENT: Optional[ChatEvent] = None
NEXT_SCHEDULED_EVENT: Optional[float] = None


# ==============================================================================
# 8. БОЕВАЯ ЛОГИКА
# ==============================================================================

def calculate_damage(
    attacker: Fightericipant": (3,
    defender0, 100),
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n🐪 <b>Золотой Караван</b>!\nHP: Fighter,
: {hp}\    atk_zonen\nКоманда <code>атака</code>!",
    },: str,
    def_zone: Optional[str],
    variant: AttackVariant
) -> Tuple[int, str
    "raid": {
       ]:
    """Рассчитывает "name_template": итоговый урон."""
    if def_zone == atk_zone:
 "⚔        return 0️ Набег Орков",
        "emoji": "⚔️",
        "base_hp": 3000,
       , f"{E_SHIELD} < "duration_hours":b>Блок!</b>"
    weapon_dmg 3.0 = attacker.get_weapon,
        "_dmg_for_zone(atk_zone,reward_per_participant": (80, 2 variant.damage_mult)00),

    base_armor        "announce_text": "🚨 <b>ВНИМАНИЕ = defender.get_armor_def(atk_zone)
    effective_armor = max(0, round(base_armor * (1!</b>\n\n⚔.0 - variant️ <b>Набег Орков</b>!\nHP: {hp}\n\nКоманда <code>атака</code>!",
    },
    "dragon_.armor_penetration)))
    final_dmg = max(1, round(weapon_dmg - effective_armor))
    return final_dmg, ""


def process_dots(fighter: Fighter, log: List[str]) -> None:
    """Обрабатывает периодический урон."""
   raid": {
 for dot in list(fighter.dots):
        fighter.hp = max(        "name_template": "🐉 Нашествие Драконов",
        "emoji": "🐉",
        "base_hp": 5000, fighter.hp0,
        "duration_hours": 4.0,
        "reward_per_participant": (150, 3 - dot["dmg"])
        log.append(f"{dot['name']}: {fighter.name} −{dot['dmg']} HP")
        dot["left"] -= 1
50),
        "announce_text": "🚨 <b>ВНИМАНИЕ        if dot["!</b>\n\n🐉 <b>Нашествие Драконов</b>!\nHPleft"] <= 0:
            fighter.dots.remove(dot)
        if fighter.hp <= 0:
            log.append(f: {hp}\n\nКоманда"☠️ <code>ата {fighter.name}ка</code>!",
    },
}


# ==============================================================================
# 5. УТИЛИТЫ
 гибнет от эффектов")
            return


def apply_dot_effect(target: Fighter, name: str, dmg: int# ==============================================================================

, rounds: intdef esc(text: Any) -> str:
    """
    Безопасное экранирование HTML-тегов.
    
    Args:
        text) -> None:
    """Накладывает эффект периодического урона."""
    target.dots = [d for d in target.dots if d["name"] !=: Любой объект, name]
    target.dots.append который нужно преобраз({"name": nameовать в строку, "dmg": dmg, "left": rounds})


def resolve_special_attack(
    attacker: Fighter,
    defender: и экранировать Fighter,
    atk_zone: str,
   .
        
    def_zone: Optional Returns:
        Безопасная для вставки в HTML строка.
    """
    return html.escape(str(text))


def create_mention(user_id: int, name: str) -> str:
    """
    Создаёт HTML-ссылку[str],
    variant: AttackVariant,
    log: List[str]
) -> bool:
    """ на профиль пользователя.Применяет спецэффект варианта атаки."""
    if def_zone == atk_zone:
        log.append(f"{
    
    ArgsE_SHIELD}:
        user_id: Чис {defender.name} заблокировал <b>{variant.name}</b>")
        return True
ловой идентификатор пользователя Telegram.
        name    effect = variant: Отобра.effect
    ifжаемое имя пользователя.
        
    Returns:
        Строка формата <a href="tg://user?id=...">Name</a>
    """
    effect == "tr return f'<a href="tg://user?id={user_id}">{esc(name)}</a>'


def build_horizontal_keyboard(buttons: List[Tuple[str, str]], buttons_per_row: int = 2) -> InlineKeyboardMarkup:
    """
    Создаёт горизонтальную клавиатуру.
iple":
           
    Args:
        buttons: Список кортежей (текст, callback_data).
        buttons_per_row: Количество кнопок в строке.
        
    Returns:
 hits = [max(1, round(calculate_damage(attacker, defender, atk_zone, def_zone, variant)[0] / 3)) for _ in range(3)]
        total_dmg = sum(hits)
        defender.hp = max(0, defender.hp - total_dmg)
        log.append(f"⚡ <b>{variant.name}</b>: {' + '.join(map(str, hits))} = <b>−{total_dmg}</b>")
        Объект Inline        return True
    elif effect == "exec":
        dmg, _ = calculate_damage(attKeyboardMarkupacker, defender,.
    """
    builder = InlineKeyboardBuilder()
    row = []
    for text, callback_data in buttons:
        row.append(InlineKeyboardButton(text=text, callback_data atk_zone,=callback_data))
        if len(row) == buttons_per_row:
            builder.row(*row)
            def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        log.append(f"{E_SWORD} <b>{variant.name}</b>: {attacker.name} → { row = []
    if row:
        builder.row(*row)
    return builder.as_markup()


def build_vertical_keyboard_withdefender.name} <b>−{dmg}</b>")
        return True
    elif effect == "_styles(buttons:bleed":
        dmg, _ List[Tuple[str, str, Optional[str]]]) -> = calculate_damage(attacker, defender, atk_zone, def_zone, variant InlineKeyboardMarkup:
    """
    Создаёт вертикальную клавиатуру с цветными кнопками.
    
    Args:
        buttons: Список)
        defender кортежей (.hp = max(0, defender.hp - dmg)
        bleed_dmg = max(1, round(defender.max_hp * 0.04текст, callback))
        apply_data, style)._dot_effect(defender, "🩸 Кровотечение", bleed_dmg, 3
            style может быть: "primary" (синий), "success" (зелёный), "danger" (красный).
            
    Returns:
        Объект InlineKeyboardMarkup.
    """
    builder = InlineKeyboardBuilder()
   )
        log.append(f"🪓 <b>{variant.name}</b>: −{dmg}, кровь по <b>{ for text, callbackbleed_dmg_data, style in}</b> ×3")
        return True
    elif effect == "pierce":
        dmg, _ = calculate_damage(att buttons:
       acker, defender, if style:
            builder.row(InlineKeyboardButton(text atk_zone, def_zone, variant)
        defender.hp = max(0, defender.hp=text, callback_data=callback_data, style=style))
        else:
            builder.row(InlineKeyboardButton(text=text, callback_data=callback_data))
    return - dmg)
        log.append(f"🏹 builder.as_markup() <b>{variant.name}</b>: пробивает брон


def build_vertical_keyboard(buttons: List[Tuple[strю на <b>−{dmg}</b>")
        return True
    elif effect == "burn":
        dmg, _ = calculate_damage(attacker, defender, str]]) -> InlineKeyboardMarkup:
    """
    Создаёт вертикальную клавиатуру без стилей.
    
    Args, atk_zone:
        buttons, def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        burn_d: Список кортежей (текст, callback_data).
        
    Returns:
        Объект InlineKeyboardMarkup.
    """
    return build_vertical_keyboard_with_stylesmg = max(1, round(dmg * 0([(t, c.4))
        apply_dot_effect(defender, f"{E_FIRE} Горение", burn_dmg, , None) for t, c in3)
        buttons])


async log.append(f"{E_FIRE} <b>{variant.name}</b>: −{dmg}, def safe_edit_message(cb: CallbackQuery, text: str, markup: Optional[InlineKeyboardMarkup] = None) -> bool:
    """
    Безопасно редактирует огонь по <b сообщение.
    
>{burn_dmg    Args:
        cb: Объек}</b> ×3")
        return True
    elif effect == "stun":
т CallbackQuery.
        text: Новый текст сообщения.
        markup: Новая клавиатура (опционально).
        
    Returns:
        True если успешно, False при ошибке.
        dmg, _    """
    = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        defender.stun = True
        try:
        log.append(f"🔨 < await cb.message.edit_text(text[:4090],b>{variant.name reply_markup=markup, parse_mode=}</b>: огParseMode.HTML)лушает цель на <b>−{dmg}</b>")
        return True
    return False


def
        return True
    except TelegramBadRequest as e:
        error_str = str(e). execute_attack_phase(lower()
       
    attacker: Fighter,
    defender: Fighter,
    atk_zone: str, if "message is not modified" in error_str:

    def_zone            return True
: Optional[str],
    variant_idx: int,
    log: List[str]
) -> None:
    """Выполняет полный цикл атаки."""
    if attacker.stun        try:
            await cb.message.answer(text[:4090], reply_markup=markup, parse_mode=ParseMode.HTML)
            return True
        except Exception as fallback_err:
            logging.error(f"F:
        attacker.stun = False
        log.append(f"💫allback error: {fallback_err}")
            return False
    except Exception as e:
        logging.error(f" {attacker.name} оглушEdit error: {ён и пропускает ход!")
        return
    weapon_data = WEAPe}")
        return False


async def safe_edit_message_by_id(
   ONS[attacker.weapon]
    variant = weapon_data["variants"][variant bot: Bot,_idx]
   
    chat_id: int,
 if variant.cooldown    message_id: int,
    text: str,
    markup: Optional[InlineKeyboardMarkup] = None_rounds > 
) -> bool0:
        attacker.attack_cooldowns[variant_idx] = variant.cooldown_rounds
    if variant.effect and random.random() * 10:
    """
    Редактирует сообщение по ID.
    
   0 < attacker.spec_chance:
        if resolve_special_attack(attacker, Args:
        bot: Объект defender, atk бота._zone, def_zone
        chat_id: ID чата.
        message_id: ID сообщения.
        text, variant, log):
            return
    dmg, note = calculate_damage(attacker, defender: Новый текст., atk_zone, def_zone,
        markup: Новая клавиатура. variant)
   
        
    Returns if note:
        log.append(f"{ZONE_INFO[atk_zone]['emoji']} {attacker:
        True если успешно, False при ошибке.
    """
    try:
        await bot.edit_message.name} бьёт — {note}")
    else:
        defender_text(
            chat_id=chat_id,
            message_id=message_id.hp = max(,
            text=text[:4090],
            reply_markup=markup,
            parse_mode=ParseMode.HTML
       0, defender.hp )
        return True
    except TelegramBadRequest as e - dmg)
        log.append(f"👊 {attacker.name} [{variant.name}] → {def:
        error_str = str(e).lower()
        if "message is not modified" in error_str:
            return True
        return False
    except Exception as e:
ender.name} <b>−{dmg}</b>")


def stop_duel_timer(duel: Duel) -> None:
    """Останавливает таймер дуэли."""
    if duel.timer_task and not duel.timer_task.done():
        duel        logging.error(f.timer_task.cancel()
    duel.timer_task = None
    duel.timer_deadline = 0.0
   "Edit by id error: {e}")
        return False


def format_number(num: int) -> str:
    """
 duel.timer_for =    Формати None
    duelрует число с раздел.timer_role = None


def terminate_dителями тысяч.
    
    Argsuel(duel:
        num: Число для форматирования.
        
    Returns:
        Строка с число: Duel) ->м, где тысячи None:
    """Завершает дуэль."""
    duel.finished = True
    stop_duel_timer(duel)
    ACTIVE_DUELS.pop(du разделены пробелами.
    """
el.a_id, None)
    if duel.b_id > 0:
        ACTIVE_DUELS.pop(duel.b_id, None)


    return f"{num:,}".replacedef start_duel(",", " ")


# ==============================================================================
# 6. БАЗА ДАННЫХ
# ==============================================================================

class DatabaseManager:
_timer(duel    """
   : Duel, uid Менеджер базы: int, role: str, bot: Bot) -> None:
    """Запускает таймер хода."""
    if uid < 0:
        return
    stop_duel_timer(duel)
    duel.timer_for = uid
    duel.timer_role = role
    duel.timer_deadline = time.time данных SQLite.
    
    Управляет всеми таблицами: игроки, уведомления, промокоды,
    чатовые события, статистика.
    """
    
    def __init__(self, db_path: str):
        """
        Инициализирует менеджер базы данных.
() + Config.T        
        Args:
            db_path: Путь кURN_TIMEOUT
    файлу базы данных duel.timer_task = asyncio.create_task(_timer_runner_task(duel, uid, role, bot))


async def _timer_runner_task(duel: Duel, uid: SQLite.
        """
        self.db_path = db_path
        self._connection = sqlite3.connect(
            int, role: str, bot: Bot) -> None:
    """Задача таймера db_path,
."""
               check_same_thread=False,
            isolation_level=None
        )
        self._connection.row_factory = sqlite3 try:
        while True:
.Row
        self            if duel.finished:
                return._init_schema()

    def _init_schema(self) -> None:
        """
        Инициализ
            time_leftирует схему базы = int(round(duel.timer_deadline - time.time()))
            if time_left <=  данных.
        
        Созда0:
               ёт все необходимые таблицы break
            await asyncio.sleep(1 и индексы.
)
        if        """
        schema = """ duel.finished or duel.timer_for != uid or duel.get_state
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY_for(uid) !=,
                username TEXT,
                name TEXT NOT NULL,
                crystals INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                weapon TEXT NOT NULL DEFAULT 'f role or uid not in ACTIVE_DUELS:
            return
        await handle_timeout_defeat(duel, uid, bot)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Timer error for {uid}: {eists',
                armor_head TEXT NOT NULL DEFAULT 'head_none',
                armor_torso TEXT NOT NULL DEFAULT 'torso_none',
                armor_}")


async def handle_timeout_defeat(duel: Duel, loser_uid: int, bot: Bot) -> None:
   arms TEXT NOT NULL """Обрабатывает DEFAULT 'arms_none',
                armor_legs TEXT NOT NULL DEFAULT 'legs_none',
                weapons_owned TEXT NOT поражение по таймауту."""
    loser = duel.get_fighter(loser_uid)
    loser_name = loser.name if loser else "Неизвест NULL DEFAULT 'fists',
                armors_owned TEXT NOT NULL DEFAULT 'head_none,torso_none,arms_none,legs_none',
                banned INTEGER NOT NULL DEFAULT 0,ный"
    duel.log.append(f"⏱ <b>{loser_name} не успел за {Config.TURN_TIMEOUT} сек!</b>")
    winner_is
                is_bot INTEGER NOT NULL DEFAULT_a = not ( 0,
loser_uid == duel                created REAL NOT NULL DEFAULT 0,
                last_active REAL NOT NULL DEFAULT 0,.a_id)
    await finalize_duel(duel, winner_is_a=winner_is_a, bot=bot, reason="timeout
                total_d")


# =================================================================uels INTEGER NOT NULL=============
# DEFAULT 0,
                total_crystals_earned INTEGER NOT NULL DEFAULT 0,
                auto_accept INTEGER NOT 9. ИИ БОТА И ГЕНЕРАЦИЯ
# ================================================================= NULL DEFAULT 0=============


            );
            
            CREATE TABLEdef get_player_armor IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_slots(player_row: sqlite3.Row) -> Dict[str, str]:
    """Извлекает слоты брони из записи БД."""
_id INTEGER NOT NULL    if not player,
                text TEXT NOT NULL,_row:
       
                ts REAL return {s: NOT NULL,
                seen INTEGER NOT f"{s}_none" for s in ZONES}
    return { NULL DEFAULT 0
        "head
            );
            
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                reward_crystals INTEGER NOT": player_row["armor_head"] or "head_none",
        "torso": player_row["armor_torso"] or "tor NULL DEFAULT 0,
                reward_wins INTEGER NOTso_none",
 NULL DEFAULT 0,
                max_uses INTEGER NOT NULL DEFAULT 1,
                current        "arms": player_row["armor_arms"] or "arms_none",
        "legs_uses INTEGER NOT": player_row[" NULL DEFAULT 0,
                expires_at REAL NOT NULLarmor_legs"] or "legs_none",
    }


def create_fighter_from_db(player_row: sqlite3 DEFAULT 0,.Row) -> Fighter:
    """Создаёт Fighter из запис
                created_by INTEGER NOT NULL,
                created_atи БД."""
    slots = REAL NOT NULL DEFAULT get_player_armor_slots 0,
                active INTEGER NOT NULL DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS promo_activations (
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                activated_at REAL NOT NULL,
                PRIMARY KEY (user_id, code)
            );
            
            CREATE TABLE IF NOT EXISTS chat_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                name TEXT NOT NULL,
(player_row)
    total_hp = BASE_STATS["hp"]
    for key in slots.values():
        item = get_armor_item_by_key(key)
        if item:
            total_hp += item.get("hp", 0)
    weapon = player_row["weapon"] if player_row["weapon"] in WEAPONS else "fists"
                   hp INTEGER NOT NULL,
                max_hp INTEGER NOT NULL,
                started_by INTEGER NOT NULL,
                started_at REAL NOT NULL,
                ends_at REAL NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                participants TEXT NOT NULL DEFAULT '[]'
            );
            
            CREATE TABLE IF NOT EXISTS player_stats (
                user_id INTEGER PRIMARY KEY,
                boss_kills INTEGER NOT NULL DEFAULT 0, return Fighter(name=esc(player_row["name"]), max_hp=total_hp, hp=total_hp, weapon=weapon, armor_slots=slots)


def determine_arena(wins: int) -> str:
    """Определяет арену по количеству побед."""
    for k in ARENA_ORDER:
        if ARENAS[k]["min_wins"] <= wins <= ARENAS[k]["max_wins"]:
            return k
    return "gold"
                casino_w


HUMAN_NAMES: List[str] = [
   ins INTEGER NOT NULL DEFAULT 0,
                casino_losses INTEGER NOT NULL DEFAULT 0,
                event_particip "Максим",ations INTEGER NOT NULL "Артём", "Данил", "Кирилл", "Егор", "Иван", "Никита", "Рома",
    "Саня", "Дима", "Влад", "Серёга", "Паша", "Толя", "Женя", "Костя",
    "Лёха", "Миша", "Г DEFAULT 0,
                rp_actions_used INTEGER NOT NULL DEFAULT 0,
                crystals_spent INTEGER NOT NULL DEFAULT 0,
                items_bought INTEGER NOT NULL DEFAULT 0
            );
            
            CREATE INDEX IF NOT EXISTS ix_notif_user ON notifications(user_id, seen);
            CREATE INDEX IF NOT EXISTS ix_players_wins ON players(wins, is_bot, banned);
            CREATE INDEX IF NOT EXISTS ix_events_active ON chat_events(active, ends_at);риша", "Стас", "Олег", "Ден", "Марк", "Тимур",
        """

    "Алина", "К        try:
атя", "            self._connection.executescript(schema)
            logging.info("Database schema initialized.")
       Настя", "Даша", "Лера", "Соня", "В except sqlite3.Error as e:
            logging.critical(f"Failed to initialize schema: {e}")
           ика", "По raise

    defлина",
    "Крис", "Милана", "Аня", "Юля", "Оля", "Маша", "К fetch_one(self, sql: str, args: tuple = ()) -> Optional[сюша", "Ника",
sqlite3.Row]:]

HUMAN
        """
        Выполняет SELECT запрос и возвращает_TITLES: List[str] = ["", "", "", "xd", "pro", "god", "real", "top", "_ одну строку.", "00
        
        Args:
            sql: SQL-запрос с плейс7", "tvхолдерами (?).
            argsoy", "cz: Кортеж аргументов", "boss", "king"]


def ensure_masked_bots_exist(target_count: int = 50) -> None:
    """Генерирует скрытых ботов для матч для подстановки.
            
        Returns:
            Объект sqlite3.Row или None.
        """
        try:
            return self._connection.execute(sql, args).fetchone()
        except sqlite3.Errorмейкинга."""
    existing_names = {r["name"].lower() as e:
            logging.error(f"DB fetch_one error: {e for r in db.fetch_all("SELECT name FROM players")}
    bots = db.fetch_all("SELECT user_id, wins FROM players WHERE is_bot=1")
    need = max(0}")
            return None

    def fetch_all(self, sql: str, args: tuple =, target_count - ()) -> List[ len(bots))
    for _ in range(need):
        name = ""
        for _ in range(BOT_NAME_GENERATION_ATTEMPTS):
            basesqlite3.Row]:
        """
        Выполняет SELECT запрос и возвращает все строки.
        
        Args:
            sql: SQL-запрос с плейсхолдерами = random.choice(HUMAN_NAMES)
            title = random.choice(HUMAN_TITLES)
            suffix = str(random.randint(1 (?).
            args: Кортеж аргументов для подстановки.
            
        Returns:
            Список объектов sqlite3.Row.
        """
, 99        try:
)) if random.random            return self._connection.execute(sql,() < 0.35 else ""
            candidate = f"{base}{title}{suffix args).fetchall()
        except sqlite3.Error as e:
           }"
            if logging.error(f" candidate.lower() not in existing_names and MIN_NAME_LENGTH <= len(candidate) <= 16:
                existing_names.add(candidate.lower())
                name = candidate
                break
DB fetch_all error: {e}")
            return []

    def execute(self, sql: str, args: tuple = ()) -> bool:
               if not name:
            name = f"Игрок{random.randint(1000,  """
        Выполняет модифицирующий запрос.
        
        Args:
            sql: SQL-запрос с плейс9999холдерами (?).
            args)}"
        uid = -random.randint(10_000_000, 99_999_999)
        arena_rand = random.random()
        if arena_rand < Config.BOT_WIN_D: Кортеж аргументов для подстановки.
            
        Returns:
            True при успехе, False при ошибке.
        """
        try:
            self._connection.execute(sql, args)
            return TrueISTRIBUTION["bronze"]:
            wins = random.randint(0, 9)
       
        except sqlite3.Error as e:
            logging.error(f"DB execute error: {e}")
            return False

 elif arena_rand < Config.BOT_WIN_DISTRIBUTION["bronze"] + Config.BOT_WIN    def close(self_DISTRIBUTION[") -> None:
        """Закрывает соединение с БД."""
        if self._connection:
            self._connection.close()


db = DatabaseManager(Configsilver"]:
            wins = random.randint(10, 29)
        else:
            wins = random.randint(30, 60)
        losses = random.randint(max(0, wins // 2), wins * 2 + 3)
        arena_key = determine_arena(wins.DB_PATH)


)
        if arena_key == "bronze":
            weapon = random.choice(["fists", "dagger# ==============================================================================
# 7. МОДЕЛИ ДАННЫХ
# ==============================================================================

@dataclass
class Fighter:
    """
    Представление бойца в бою.
    
    Содержит все характеристики, эки", "sword"])пировку и
            tier_max = 2
 статусы.
        elif arena_key    """
    name: str
 == "silver":    max_hp:
            weapon = random.choice(["sword", " int
    hp: int
   axe", "bow", "dagger"])
            tier_max = 3
        else: weapon: str
    armor_slots: Dict[str, str] = field(default_factory=dict)
    dots: List
            weapon =[Dict[str, random.choice(["bow", "staff", "hammer", "axe", "sword"])
            tier Any]] = field(default_factory=list)
    stun: bool = False
_max = 4    attack_cooldowns: Dict[int
        slots = {}
        for, int] = s in ZONES field(default_factory=dict)

    def:
            items = ARMOR_DATA[s]
            idx = min(random.randint(0, tier_max), len __post_init__(self) -> None:
        """Инициализация и расчёт б(items) - онусов."""
        if self.weapon not in WEAPONS:
            self.weapon = "fists"
        self.base_weapon_dmg = WEAPONS[self.weapon]["base_dmg"]
        slots = self.armor_slots or {}
        fixed_slots = {}
        for s in ZONES:
            key = slots.get1)
            slots[s] = items[idx]["key"]
        owned_armors = set(list(slots.values()) + START_ARMOR_KEYS)
        db.execute(
            """INSERT INTO players (user_id, username, name, crystals, wins, losses, weapon,
                armor_head, armor_torso, armor_arms(s) or f, armor_leg"{s}_none"
            if not get_armor_items, weapons_owned, armors_owned_by_key(key):, is_bot,
                key = f"{s}_none"
            fixed_slots[s] = key
        self.armor_slots = fixed_slots
        self.armor_def = {}
        total_chance = 0
        total_bonus = 0
        for created, last_active)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (uid, None, name, random.randint(0, 400), wins, losses, weapon,
             slots["head"], slots["torso slot in ZONES"], slots["arms"], slots["legs"],
             weapon, ",".join(owned_armors), 1:
            item = get_armor_item_by_key(self.armor_slots[slot]) or get_armor_item_by_key(f"{, time.time(),slot}_none")
            self. time.time())
        )


defarmor_def pick_balanced[slot] = item_opponent(player_uid: int, player_wins: int) -> Optional[int]:
    """Подбирает соперника того же уровня."""
    arena = determine_arena(player_wins)
    limits = ARENAS[arena]
    humans = [r["user_id"] for["df"]
            total_chance += item["chance"]
            total_bonus += item["dmg_bonus"]
        self.spec_chance = min(total_chance, 70)
        self.spec_dmg_bonus = total_bonus / 100.0

    def is_alive r in db.fetch(self) -> bool_all(
        """SELECT user_id FROM players WHERE user_id != ? AND:
        """Проверяет, banned=0 AND жив ли боец."""
        return self.hp >  is_bot=00

    def
           AND wins BETWEEN ? AND ? ORDER BY RANDOM() LIMIT 6""",
        (player_uid, limits["min_wins"], limits["max_wins"])
    )]
 get_armor_def(self, zone: str) -> int:
        """Возвращает защиту для зоны."""
        return self.armor_def.get(zone, 0)

    def get_weapon_dmg    bots = [r["user_id_for_zone(self,"] for r in zone: str, variant_mult: float = 1.0) -> int:
        """Рассчитывает урон по зоне db.fetch_all(
        """SELECT user_id FROM players WHERE is_bot=1 AND banned=0
           AND wins BETWEEN ? AND ? ORDER BY RANDOM."""
        zone_mult = ZONE() LIMIT 6_INFO.get(zone, {}).get("mult", 1.0)
        base = self.base_weapon_dmg * zone_mult * variant_mult
        return max(1, round(base))

    def reduce_cooldowns(self) -> None:
        """Уменьшает кулдауны на 1 раунд."""
        for idx""",
        (limits["min_wins"], limits["max_wins"])
    )]
    if humans and bots:
        return random.choice(bots if random.random() < 0.6 else humans)
    if humans:
        return random.choice(humans)
    if bots:
        return random.choice(bots)
    in list(self.attack ensure_masked_b_cooldowns.keys()):
            selfots_exist(10)
    rows = db.fetch_all(
        """SELECT user_id.attack_cooldowns FROM players WHERE is_bot=1 AND[idx] -= 1
            if self.attack_cooldowns[idx] <= 0:
                del self.attack wins BETWEEN ? AND_cooldowns[idx ?
           ORDER]

    def get_available_variants(self) -> List[int]:
        """Возвращает доступные варианты атаки.""" BY RANDOM() LIMIT 1""",
        (limits["min_wins"], limits["max_wins"])
    )
    return rows[0]["user_id"] if rows else None


def bot_dec
        all_varide_attack_zone(attiants = list(range(len(WEAPONS[self.weapon]["variants"])))
        return [i for i in all_variants if i not in self.attack_cooldowns]


def get_armor_item_by_key(key: str) -> Optional[Dict[str, Any]]:
    """Поиск предмета брони по ключу."""
    for slot, items in ARMORacker: Fighter, defender: Fighter) -> str:
    """ИИ выбора зоны атаки."""
    if random.random() < 0.10:
        return random.choice(ZONES)
    if defender.hp <= defender.max_hp * 0.30:
        return max(ZONES, key=lambda z: attacker.get_weapon_dmg_for_zone(z))
    def score_zone(z: str) -> tuple:
        dmg = attacker.get_weapon_dmg_for_zone(z) - defender.get_armor_def(z)
        return (dmg, ZONE_INFO[z]["mult"])_DATA.items():

    return max        for it in items:
            if it["key"] == key:
                return {**it, "slot": slot}
    return None


def generate_hp_bar(fighter: Fighter, width: int = 12) -> str:
    """Генерирует визуальную полосу здоровья."""
    if fighter.max_hp <= 0:
        return "⬛" * width
(ZONES, key=score_zone)


def bot_decide_attack_variant(attacker: Fighter)    filled = max -> int:
    """ИИ выбора варианта атаки."""
    variants = WEAPONS[attacker.weapon]["variants"]
    available = attacker.get_available_variants()
    if(0, min(width, int(round(width * fighter.hp / fighter.max_hp))))
    ratio = fighter.hp / fighter.max_hp
    if ratio > not available:
 0.6        return 0
    return max(available, key=lambda i: variants[i].damage_mult)


def bot_decide_to_def:
        char = "🟩"
    elif ratio > 0.3:
        char = "🟨"
    else:
        charend(duel: Duel, bot = "_is_a: bool) -> bool:
    """И🟥"
    return char * filledИ решения защищаться + "."""
    if duel.bot_block_streak >= 2 or duel.round_no - duel.bot_last_block_round < 3:
        return False
    bot_fighter = duel.a if bot_is_a else duel.b
    hp_ratio = bot_fighter.hp / bot_fighter.max_hp
    if hp_ratio < 0.30:
        base_chance = 0.65
    elif hp_ratio < 0.6⬛" * (width - filled)


def format_fighter_card(fighter: Fighter) -> str:
    """Форматирует информацию о бойце."""
    w = WEAPONS[fighter.weapon]
    ad = fighter.armor_def
    cd_str = ""
    if fighter.attack_cooldowns:
        cd_info = [f"Атака {i + 1}: {c}р" for i, c in fighter.attack_cooldowns.items()]
       0:
        cd_str = f base_chance = "\n│ ⏳ КД: {', '.join(cd_info)}"
    return (
        f0.40"│ <b>{fighter.name}</b>\n"
        f"│ {E_HEART} <b>{fighter.hp}</
    else:
        base_chance = 0.25
    return random.random() < base_chance


def bot_decide_defend_zone(attacker: Fighter, defender: Fighter) -> str:
    """ИИ выбора зоны защиты."""
    def danger_level(z: str) -> int:b>
        return attacker.get_weapon_dmg_for_zone(z) - defender.get_armor/{fighter.max_hp}  {generate_hp_bar(fighter)}{cd_str}\n"
        f"│ {w['emoji']} {w['name']} · баз_def(z)
    sorted_zones = sorted(ZONES,. урон { key=danger_level, reverse=True)fighter.base_weapon_dmg}\n"
    if random
        f".random() < │ {E_SHIELD} {E_ZONE_HEAD}{ad['head']} {E_ZONE_TORSO}{ad['torso']} "
        f"{E_ZONE_ARMS}{ad['arms']} {E_ZONE_LEGS}{ad['legs']}"
    )


@dataclass
class Duel:
    """
   0.25 and len(sorted_zones) > 1:
        return sorted_zones[1]
    return sorted_zones[0]


# ==============================================================================
# 10. КАЗИНО
# ==============================================================================

async def play_casino_slots_animated(chat_id: int, bet: int, uid: int, bot: Состояние активной дуэли. Bot) ->
    
    У Tuple[Optional[strправляет ходами], Optional[str]]:
    """Слоты с анимацией."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."
    if bet <, таймерами, логами и спецсостояниями.
    """
    a_id: int
    b_id: int
    a: Fighter
    b: Fighter
    attacker_is_a: bool = True
    round_no: int = 1
    atk Config.CASINO_zone: Optional[str_MIN_BET:
        return None] = None
    def_zone: Optional[str] = None
    chosen, f"Минимальная ставка: {Config.C_variant_idx: OptionalASINO_MIN_BET} {E_CRYSTAL}"
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))
    sent_message = await bot.send_dice(chat_id=chat_id, emoji="🎰")
    dice_value = sent_message.dice.value
    if dice_value == 1:
        mult =[int] = None
    log: List[str] = field(default_factory=list)
    started: float = field(default_factory=time.time)
    is_boss: bool = False
    boss_key: Optional[str] = None
    reward_mult: int = 1
    finished: bool = False
    bot_last_block_round: int = -10
    bot_block 10
_streak: int        win = bet * mult
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (win, uid))
        db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
        return f"{E_SLOT} Выпало: <b>{dice_value}</b>\n\n{E_TROPHY} = 0
    timer_task: Optional[asyncio.Task] = None
    timer_deadline: float = 0.0
    timer_for: Optional[int] = None
    timer_role: Optional[str] = None

    def get_state_for(self, uid: int) -> str:
        """Определяет роль пользователя."""
        if uid == self.a_id:
            return "attacker" if self.attacker_is_a else <b>ДЖЕКПОТ ×{mult} "defender"!</b>\n
        if uid == self.b_id:
            return "defender" if self.attacker_is_a else "attacker"
        return "none"

    def get_attacker(self) -> Fighter:💎 +{win} кристаллов", None
    else:
        db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
        return f"{E_SLOT}
        return self.a if self.att Выпало:acker_is_a else <b>{dice_value}</b>\n\n{E_SKULL} <b>Нет комбинации.</b>\n💎 −{bet} кристаллов", None


async def play_casino_dice_game(chat_id: int, bet: int, uid: int, bot: Bot, mode: str, value: Any = None) self.b

    def get_defender(self) -> Fighter:
        return self.b if self.attacker_is_a else self.a

    def get_attacker_id(self) -> int:
        return self.a_id if self.attacker_is_a else self.b_id

    def get_defender_id(self) -> int:
        return self.b -> Tuple[Optional[str], Optional[str_id if self.att]]:
   acker_is_a else self.a_id

    def get_fighter(self, uid: int) -> Optional[Fighter]:
        if uid == self.a_id:
            return self.a
        if uid == self.b_id:
            return self.b
        return """Кости с разными режимами."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."
 None

    def    if bet < get_opponent(self, uid: int) -> Optional[Fighter]:
        if uid == self.a_id:
            return self.b
        if uid == self.b_id:
            return Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    db self.a
       .execute("UPDATE players return None

    def add_log(self, message: str) -> None:
        """Добавляет сообщение в лог."""
        self.log.append(message SET crystals=crystals-? WHERE user_id=?", (bet, uid))
    sent_message = await bot.send_dice(chat_id=chat_id, emoji="🎲)
        if")
    dice_value = sent_message len(self.log) > DUEL_LOG_LIMIT:
            self.log = self.log[-DUEL_LOG_LIMIT:]


.dice.value
    win = False
    mult = 0
    if mode == "even_odd":
        is_even = (dice_value %ACTIVE_DUELS 2 == : Dict[int, Duel] = {}


@dataclass0)
        if (value == "even" and is_even) or
class PendingDuel:
    """Ожидающий подтверждения вызов на дуэль."""
    (value == " challenger_id: int
    target_id: int
    challenger_msg_id: int
    target_msg_id: int
    chat_idodd" and not is_even):
            mult = 2
            win = True
    elif mode == "high_low":
        if (value: int
    == "high" and dice_value >= 4) or (value == " created_at: float
    timeout_task: Optional[asyncio.Task] = None


PENDING_DUELS: Dict[Tuple[int, intlow" and dice_value <= 3):
            mult], PendingDuel = 2
            win = True
    elif mode == "number":
        if dice_value == value:
            mult = 6
           ] = {}


@dataclass
class ChatEvent:
    """Модель чатового события."""
    event_id: win = True
 int
    event_type: str
    name: str    if win:
        payout = bet * mult
        db.execute("UPDATE players SET crystals=crystals+
    hp: int
    max_hp: int
? WHERE user_id    started_by:=?", (payout, uid))
        db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
        return f"{E_DICE} Выпало: <b>{dice_value int
    started_at: float
    ends_at: float
    active: bool = True
    participants: Set[int] = field(default_factory=set)
    damage_log: List[str] = field(default_factory=list)
    total_damage_dealt: int = 0

   }</b>\n def is_active(self\n{E_TROPHY} <) -> bool:
        """Проверяет активностьb>Победа ×{mult}!</b>\n💎 + события."""
       {payout} return self.active and self.hp > 0 and time.time() < кристаллов", None
    else:
        db.execute("UPDATE player_stats SET casino_losses self.ends_at

    def take_damage=casino_losses(self, attacker_id: int, attacker_name: str, damage: int,+1 WHERE user is_crit: bool_id=?", (uid,))
        return f"{E_DICE} Выпало: <b>{dice_value}</b>\n = False) -> str:
        """Наносит урон событию."""
        self.hp = max(0, self.hp - damage)
        self.participants.add(attacker_id)
       \n{E_SKULL} <b self.total_damage_dealt += damage
>Поражение.</b>\n💎 −{        crit_text = " 💥 <b>КРИbet} кристалТ!</b>"лов", None


async def play_casino_darts_animated(chat_id: int, bet: int, uid if is_crit else: int, bot: Bot, bet_on_miss: bool = False) -> ""
        log_entry = f"⚔️ Tuple[Optional[str {attacker_name} наносит <b>{damage}</b> урона], Optional[str]]:
    """Дротик с анимацией."""
    p = db.fetch_one("!{crit_textSELECT crystals FROM players} (Осталось HP: {self.hp}/{self.max_hp})"
        self.damage_log.append(log_entry WHERE user_id=?", (uid,))
    if not p or p["crystals"] <)
        return bet:
        return None, "Недостаточно кристаллов."
    if bet < log_entry

    def get_participants_count(self) -> int:
        """Возвращает количество участников Config.CASINO."""
        return_MIN_BET:
        return None len(self.part, f"Мicipants)

    def get_time_left(self) -> int:
        """Возвращает оставшееся время."""
        return max(0, int(self.ends_at - time.time()))


ACTIVE_CHATинимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))
    sent_message_EVENT: Optional[ChatEvent] = None
NEXT = await bot.send_SCHEDULED_EVENT:_dice(chat_id=chat_id, emoji="🎯")
    dice_value = sent_message.dice.value
 Optional[float] = None


# ==============================================================================
# 8. БОЕВАЯ ЛОГИКА
# ==============================================================================

def calculate_damage(
    attacker: Fighter,
    defender    is_hit =: Fighter,
 dice_value >= 4
    if bet_on_miss:
        if not is_hit:
            payout = int(bet * 1.9)    atk_zone: str,
    def_zone:
            db.execute Optional[str],
("UPDATE players SET crystals=crystals+? WHERE user    variant: AttackVariant
) -> Tuple[int, str_id=?", (p]:
    """ayout, uid))Рассчитывает итоговый урон."""
    if def_zone == atk_zone:

            db.execute("UPDATE player_stats SET casino_wins=casino_w        return 0ins+1 WHERE, f"{E_SHIELD} < user_id=?", (uid,))
            return f"{b>БлокE_DARTS!</b>"
    weapon_dmg = attacker.get_weapon_dmg_for_zone} Выпало(atk_zone, variant.damage_mult)
    base_armor = defender.get_armor_def(atk_zone)
    effective: <b>{dice_value}</b>\n\n{E_TROPHY} <b>Промах! Ты выиграл!</b>\n💎 +{payout} кристаллов", None
        else:
            db.execute("UPDATE player_stats SET casino_losses=cas_armor = max(0, round(base_armor * (1.0 - variant.armor_penetration)))
    final_dmg = max(1, roundino_losses+1 WHERE user_id=?", (uid,))(weapon_dmg - effective_armor))
    return final
            return f"{E_DARTS} Выпало: <b>{dice_value}</b>\n\n{E_SKULL} <b>Попадание. Ты про_dmg, ""


def process_dots(fighter: Fighter, log: List[str]) -> None:
    """Обрабатывает периодический урон."""
    for dot in list(fighter.dots):
        fighter.hp = max(играл.</b>\n💎 −{bet} кристаллов", None
    else:
        if is_hit:
            payout = int(bet * 1.9)
            db.execute("UPDATE players SET0, fighter.hp - dot["dmg"])
        log.append(f"{dot['name']}: {fighter.name} −{dot['dmg']} HP")
        dot["left"] -= 1
        if dot["left"] <= 0:
            fighter.dots.remove(dot)
        if fighter.hp <= crystals=crystals+? WHERE user_id=?", (payout, uid))
            db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
            return f"{E_DARTS} Выпало: <b>{dice_value}</b>\n\n{E_TROPHY} <b>Попадание!</ 0:
            log.append(f"☠️ {fighter.name} гибнет от эффектов")
            return


def apply_dot_effect(target: Fighter, name: str, dmg: int, rounds: intb>\n) -> None:
    """На💎 +{payout} кристалкладывает эффект периодического урона."""лов", None

    target.d        else:
            db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
            return fots = [d for d in target.dots if d["name"] != name]
    target.dots.append({"name": name"{E_DART, "dmg": dmg, "left": rounds})


def resolve_special_attack(
    attacker: Fighter,
    defender:S} Выпало: <b>{dice_value}</b>\n\n{E_SKULL} <b>Промах.</b>\n💎 −{bet} кристаллов", Fighter,
    atk_zone: str,
    def_zone: Optional[str],
    variant: AttackVariant,
    log: List[str]
) -> bool:
    """Применяет спецэффект None


async def варианта атаки.""" play_casino_basketball_animated(chat_id: int, bet: int, uid: int, bot: Bot, bet_on_miss: bool
    if def_zone == atk_zone:
        = False) -> Tuple[Optional[str], Optional[str]]:
    """Баскетбол с анимацией."""
    p = db.fetch_one("SELECT crystals FROM log.append(f"{E_SHIELD} {defender.name} заблокировал <b>{variant.name}</b>")
        return True
    effect = variant players WHERE user_id=?", (uid,))
    if.effect
    if not p or p["crystals"] < bet:
        return None, "Недостаточно effect == "triple":
        hits = [max(1, round кристаллов."(calculate_damage(att
    if betacker, defender, atk_zone, def_zone, variant < Config.CAS)[0] /INO_MIN_BET 3)) for:
        return _ in range(3)]
        total_dmg = sum(hits) None, f"
        defender.hpМинимальная ставка: {Config.CASINO_MIN = max(0_BET} {, defender.hp - total_dmg)
        log.append(f"⚡ <b>{variant.name}</b>: {' + '.join(map(str, hits))} = <b>−{total_dmgE_CRYSTAL}"
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))
    sent_message = await bot.send_dice(chat_id=chat_id, emoji="🏀")
    dice_value = sent_message.dice.value
    is_hit = dice_value == 5
    if bet_on_miss}</b>")
        return True
    elif effect == "exec":
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        log.append(f"{E_SWORD:
        if not is_hit:
            payout =} <b>{variant.name}</b int(bet *>: {attacker.name} → {defender.name} <b>− 1.9)
            db.execute("UPDATE players SET crystals=cr{dmg}</b>")
       ystals+? WHERE return True
    elif effect == "bleed":
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, variant user_id=?", (payout, uid))
            db.execute("UPDATE player_stats SET casino_w)
        defenderins=casino_wins+1 WHERE user_id=?",.hp = max(0, defender.hp - dmg)
        bleed_dmg = max(1, round(defender.max_hp *  (uid,))0.04
            return f))
        apply"{E_BASK_dot_effect(defender, "ET} Вып🩸 Кровотало: <bечение", bleed_dmg, 3)
        log.append(f"🪓 <b>{variant.name}</b>: −{dmg}, кровь по <b>{bleed_dmg}</b> ×3")
        return True
    elif effect == "pierce":
        dmg, _>{dice_value}</b>\n\n{E_TROPHY} <b>Промах! Ты выиграл!</b>\n💎 +{payout} кристаллов", None
        else: = calculate_damage(att
            db.executeacker, defender, atk_zone, def_zone, variant)
        defender("UPDATE player_stats.hp = max( SET casino_losses=casino_losses+0, defender.hp - dmg)
1 WHERE user_id        log.append(f"🏹 <b>{variant.name}</b>:=?", (uid,))
            return f"{E_BASKET} Выпало: <b>{dice_value}</b>\n\n{E пробивает броню на <b>−{dmg}</b>")
        return True
    elif effect == "burn":
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        burn_d_SKULL} <mg = max(1, round(dmg * 0.4))
        apply_dot_effectb>Слэм-данк. Ты проиграл.</b>\n💎 −{bet} кристаллов", None
    else:
        if is_hit:
            payout = int(bet * 1.9)
            db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
            db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
            return f"{E_BASKET} Выпало: <b>{dice_value}</b>\n\n{E_TROPHY} <b>СЛЭМ-ДАНК!</b>\n💎 +{payout} кристаллов", None
        else:
            db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
            return f"{E_BASKET} Выпало: <b>{dice_value}</b>\n\n{E_SKULL} <b>Промах.</b>\n💎 −{bet} кристаллов", None


def play_casino_roulette(uid: int, bet: int, bet_type: str, bet_value: Any = None) -> Tuple[Optional[str], Optional[str]]:
    """Рулетка с разными типами ставок."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."
    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка(defender, f: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    reds = {1, 3,"{E_FIRE} Горение", burn_dmg, 3)
        log.append(f"{E_FIRE} <b>{variant.name}</b>: −{dmg}, огонь по <b>{burn_dmg}</b> ×3")
        return True
    elif effect == "stun":
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        defender.stun = True
        log.append(f"🔨 <b>{variant.name}</b>: оглушает цель на <b>−{dmg}</b>")
        return True
    return False


def execute_attack_phase(
    attacker: Fighter,
    defender: Fighter,
    atk 5, _zone: str,
    def_zone: Optional[str],
    variant_idx: int,
    log: List[str]
) -> None:
    """Выполняет полный цикл атаки."""
    if attacker.stun:
        attacker.stun = False
        log.append(f"💫 {attacker.name} оглуш7, 9, 12, 14, 16, 18ён и пропускает ход!")
       , 19 return
    weapon, 21_data = WEAPONS[attacker, 23, 25.weapon]
    variant = weapon_data, 27, 30, 32, 34, 36}
    num["variants"][variant = random.randint(_idx]
    if variant.cooldown_rounds > 0:
       0, 3 attacker.attack_cooldown6)
   s[variant_idx] = variant.cooldown_rounds
    if variant.effect and random.random() * 100 < attacker.spec_chance:
        if resolve_special_attack(attacker, defender, atk_zone, def_zone, variant, log):
            return
    dmg, note = calculate_damage(attacker, defender, atk_zone if num == 0:
        res_color = ", def_zone, variant)
    if note:
green"
        color_emoji = E_GREEN
    elif num in reds:
        res_color = "red"
        color_emoji = E_RED
    else:
        res_color = "black"
        color_emoji = E_BLACK
    db.execute("UPDATE players SET crystals=crystals-?        log.append(f WHERE user_id=?","{ZONE_INFO[atk_zone]['emoji']} {attacker (bet, uid))
    win = False
   .name} бь mult = 0
    if bet_type == "color":
        if bet_value == res_color:
            mult = 1ёт — {note}")
    else:
        defender.hp = max(4 if res_color0, defender.hp == "green" else 2
            win = True
    elif bet_type == "even - dmg)
        log.append(f"👊 {attacker.name} [{variant.name}] → {defender.name} <b>−{dmg}</b_odd":
        if num != >")


def stop_duel_timer(0:
            is_even = (duel: Duel) -> None:
    """Останавливает таймер дуэли."""
    if duel.timer_task and not duel.timer_task.done():
        duelnum % 2.timer_task.cancel() == 0)
            if (bet_value == "even" and is_even) or (bet_value == "odd" and not is_even):
                mult = 2
                win = True
    elif bet_type == "half":
        if num != 0:
            if (bet_value == "low" and 1 <= num <= 
    duel.timer_task = None
    duel.timer_deadline = 0.0
    duel.timer_for = None
    duel.timer_role = None


def terminate_duel(duel: Duel) ->18) or None:
    (bet_value == """Завершает "high" and 19 <= num <= 36):
                mult = 2
                win = дуэль."""
    duel.finished = True
    stop_duel_timer(duel)
    ACTIVE_DUELS.pop(du True
    elif bet_type == "el.a_id,number":
        if num == bet_value:
            mult = 36
            win = True
    elif bet_type == None)
    if duel.b_id > 0:
        ACTIVE_DUELS.pop(duel.b_id, None)


def start_duel_timer(duel: Duel, uid: int, role: str, bot: Bot) -> None:
    """Запускает таймер хода."""
    if uid < 0:
        return
    stop_duel_timer(duel)
    duel "dozen":
        if num != 0:
            if (bet_value == 1 and 1 <= num <= 12) or (bet_value == 2 and 13 <= num <= 24) or (bet_value == 3 and 25 <= num <= 36):
                mult = 3
                win = True
    if win:
        payout = bet * mult
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
        db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id.timer_for = uid
    duel.timer_role = role
    duel.timer_deadline = time.time() + Config.TURN_TIMEOUT
    duel.timer_task = asyncio.create_task(_timer_runner_task(duel, uid, role, bot))


async def _timer_runner_task(duel: Duel, uid: int, role: str, bot: Bot) -> None:
    """Задача таймера."""
    try:
        while True:
            if duel.finished:
                return
            time_left = int(round(duel.timer_deadline - time.time()))
            if time_left <= 0:
                break
            await asyncio.sleep(1)
        if duel.finished or duel.timer_for != uid or duel.get_state_for(uid) != role or uid not in ACTIVE_DUELS:
            return
        await handle_timeout_defeat(duel, uid, bot)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Timer error for {uid}: {e}")


async def handle_timeout_defeat(duel: Duel, loser_uid: int, bot: Bot) -> None:
    """Обрабатывает поражение по таймауту."""
    loser = duel.get_fighter(loser_uid)
    loser_name = loser.name if loser else "Неизвестный"
    duel.log.append(f"⏱ <b>{loser_name} не успел за {Config.TURN_TIMEOUT} сек!</b>")
    winner_is_a = not (loser_uid == duel.a_id)
    await finalize_duel(duel=?", (uid,))
        return, winner_is_a f"=winner_is_a, bot=bot, reason="timeout")


# ==============================================================================
# 9. ИИ БОТА И ГЕНЕРАЦИЯ
# ==============================================================================

def get_player_armor🎡 Вып_slots(player_row:ало: {color_emoji} <b>{num}</b>\n\n{E_TROPHY} <b sqlite3.Row) -> Dict[str,>Победа ×{mult}!</b>\n str]:
   💎 +{payout} кристаллов", None
    else:
        db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
        return f"🎡 Выпало: {color_emoji} <b>{num}</b>\n\n{E_SKULL} <b>Поражение.</b>\n💎 −{bet} кристаллов", None


def play_casino_coin(uid: int, bet: int, choice: str = "heads") -> Tuple[Optional[str], Optional[str]]:
    """Монетка."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."
    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    result = random.choice(["heads", "tails"])
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))
    result_text """Извлекает = "Орёл" if result == "heads" else "Решка"
    result_emoji = "🔵" if result == "heads" else "🔴"
    if result == choice:
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (bet * 2, uid))
        db.execute("UPDATE слоты брони из записи БД."""
 player_stats SET casino_wins=casino_wins+    if not player_row:
        return {s: f"{s}_none" for s1 WHERE user_id in ZONES}
    return {=?", (uid,))
        return f"{E_COIN} Выпало: {result_emoji} <b>{result_text
        "head": player_row["armor_head"] or "head_none",
        "torso": player_row["armor_torso"] or "torso_none",
        "arms": player_row["armor_arms"] or}</b>\n "arms_none",
        "legs": player_row["\n{E_Tarmor_legs"] or "legs_none",
    }


def create_fighter_from_db(player_row: sqlite3.Row) -> Fighter:
    """ROPHY} <b>Победа!</b>\n💎 +{bet * 2} кристаллов", None
    db.execute("UPDATE player_stats SETСоздаёт casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
    return f Fighter из записи БД."""
    slots = get_player_armor_slots(player_row)
    total_hp = BASE_STATS["hp"]
    for key in slots.values():
        item"{E_COIN = get_armor_item_by_key(key)
        if item} Выпало: {result_emoji} <b>{result_text}</b>\n\n{E_SKULL} <b>Поражение.</:
            total_hp += item.getb>\n("hp", 0)
    weapon = player_row["weapon"] if💎 − player_row["weapon{bet} кристаллов", None


def play_casino_highlow(uid: int, bet: int, choice: str ="] in WEAPONS else "fists"
    return Fighter(name=esc(player_row["name"]), max_hp=total_hp, "high") -> hp=total_hp, weapon=weapon, armor_slots=slots)


def determine_arena(wins: int) -> str:
    """Определяет арену Tuple[Optional[str], Optional[str]]:
    """Больше/Меньше."""
    p = db.fetch_one("SELECT crystals FROM players по количеству поб WHERE user_id=?",ед."""
    for k in ARE (uid,))
    if notNA_ORDER:
        if ARENAS[k]["min_w p or p["ins"] <= wins <= ARENAS[k]["max_wins"]:
            return k
    return "gold"crystals"] < bet:
        return None, "Недостаточно кристаллов."
    if bet < Config.CASINO_MIN_BET:
        return None


HUMAN_NAMES, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    result: List[str] = [
    "Максим", "Артём", "Данил", "Кирилл", "Егор", "_num = random.randint(1, 100)
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (betИван", "Никита", "Рома",
    "Саня", "Дима", "В, uid))
лад", "Сер    if result_numёга", " == 50Паша",:
        db "Толя", "Женя", "Костя",
    "Лёха", "Ми.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (bet, uid))ша", "Г
        return f"📊 Выпало:риша", " <b>{resultСтас", "Олег", "Ден", "Марк", "Тимур",
    "Алина", "К_num}</b>\n\n🤝 <b>Ровно атя", "50!</bНастя", "Даша", "Лера", "Соня", "В> Ставка возвращена.", None
    win = (choice == "high" and result_num > 50ика", "По) or (choiceлина",
    "Крис", == "low" and result_num < 50)
    if win:
        payout = int(bet * 1.9)
        db.execute("UPDATE players SET crystals= "Миланаcrystals+? WHERE user_id=?",", "Аня", "Юля", "Оля", "Маша", "Ксюша", "Ника",
]

HUMAN_TITLES: (payout, List[str] = uid))
        db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id ["", "", "", "xd", "pro", "god", "real", "top", "_", "007", "tv=?", (uid,oy", "cz))
       ", "boss", return f"📊 Вып "king"]


ало: <b>{result_num}</b>\n\n{E_TROPHY} <b>Победаdef ensure_masked_bots_exist(target_count: int = 50) -> None:
    """Генерирует скрытых ботов для матч!</b>\nмейкинга."""💎 +{
    existing_names = {r["name"].lower()payout} кри for r in dbсталлов", None
    db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
    return f"📊 Выпало: <b>{result_num}</b>\n\n{.fetch_all("SELECT name FROM players")}
    bots = db.fetch_all("SELECT user_id, wins FROM players WHERE is_bot=1")
    need = max(0, target_count -E_SKULL} len(bots)) <b>П
    for _ in range(need):
        name = ""
        for _ in range(BOT_NAME_GENERATION_ATTEMPTS):
            base = random.choice(HUMAN_NAMES)
            title = random.choice(HUMAN_TITLES)
оражение.</b>\n💎 −{bet} кристаллов", None


# ==============================================================================
# 11. ЧАТОВЫЕ СОБЫТИЯ
# ==============================================================================

def spawn_chat_event(
    event_type: str,            suffix = str(random.randint(1, 99)) if random.random() < 0.35 else ""
            candidate = f"{base}{title}{suffix}"
            if candidate.lower() not in existing_names
    started_by: int,
    custom_hp: Optional[int] = None,
    custom_duration: Optional[float] = None
) -> Optional[ChatEvent]:
    """Создаёт чатовое событие.""" and MIN_NAME_LENGTH
    global ACTIVE <= len(candidate) <= 16:
                existing_names.add(candidate.lower())
                name = candidate_CHAT_EVENT
    if ACTIVE_CHAT_EVENT and ACTIVE_CHAT_EVENT.is_active():
        return None

                break
    template = CH        if not name:
            nameAT_EVENT_TEMPLATES.get(event_type)
    if not template:
        return None
    hp = custom_hp or template["base_hp"]
    duration = custom = f"Игрок{random_duration or template[".randint(1000, 9999)}"
        uid = -random.randint(10_000duration_hours"]
_000    name = template["name_template"].format(emoji=template["emoji"])
    now = time.time()
, 99_999_999)
        arena_rand = random.random()
        if arena_rand < Config    ends_at =.BOT_WIN_D now + (duration * 36ISTRIBUTION["bron00)
ze"]:
            wins = random.randint    event = ChatEvent(
        event_id=int(now(0, ), event_type=event_type, name=name,
        hp9)
        elif arena_rand < Config.BOT_WIN=hp, max_hp=hp, started_by=started_by, started_at_DISTRIBUTION["=now, endsbronze"] + Config.BOT_WIN_DISTRIBUTION["silver"]:
            wins = random.randint(10, 29)
        else:
            wins = random.randint(3_at=ends_at,
    )
    ACTIVE_CHAT_EVENT = event
    db.execute(
        """INSERT INTO chat_events (event_type, name0, 60)
        losses = random.randint, hp, max(max(0,_hp, started_by wins // 2, started_at, ends_at, active)
           VALUES (?,?,?,?,?,?,?,1)""",
        (event_type, name, hp, hp, started_by, now, ends_at)), wins * 
    )
    return event


2 + 3)
        arena_key = determine_arena(wins)
        if arena_key == "bronze":
            weapon = random.choice(["fists", "daggerdef attack_chat_event", "sword"])
            tier_max = 2
        elif arena_key == "silver":
            weapon = random.choice(attacker_id: int, attacker_name: str) -> Optional[str]:
    """Атакует чатовое событие."""
    global ACTIVE_CHAT_EVENT
    if(["sword", "axe", "bow", "dagger"])
            tier not ACTIVE_CHAT_EVENT or not ACTIVE_CHAT_EVENT.is_active():_max = 3
        else:
            weapon =
        return None random.choice(["bow", "staff", "hammer", "axe", "sword"])
            tier
    base_dmg = random.randint(Config.EVENT_MIN_DAMAGE, Config.EVENT_MAX_DAMAGE)
    is_crit = random_max = 4.random() < Config.EVENT_CRIT_CHANCE
    if
        slots = {}
        for s in ZONES:
            items is_crit:
 = ARMOR_DATA        base_dmg = int(base_dmg * Config.EVENT_CRIT_MULT)[s]
           
    log_entry idx = min(random = ACTIVE_CHAT_EVENT.take_damage(attacker.randint(0,_id, attacker_name, base_dmg, is_crit)
    db.execute tier_max), len(items) - 1)
            slots[s] = items[idx]["key"]
        owned_armors = set(list(slots.values("UPDATE player_stats()) + START_ARMOR_KEYS)
        db.execute( SET event_participations=event_participations+1 WHERE user_id=?", (
            """INSERTattacker_id, INTO players (user_id, username, name, crystals, wins, losses, weapon,
                armor_head))
    if, armor_torso ACTIVE_CHAT_EVENT.hp <= 0:
        ACTIVE_CHAT_EVENT.active = False
        db.execute("UPDATE chat_events SET active=0, armor_arms, armor_legs, weapons_owned WHERE event_id=?", (ACTIVE_CHAT_EVENT, armors_owned, is_bot,.event_id,)) created, last_active
        template =)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?, CHAT_EVENT_T?,?,?,?)""EMPLATES.get(ACTIVE_CHAT_EVENT.event_type, {})
        reward_range",
            (uid, None, name, random.randint(0,  = template.get("400), wins, losses, weapon,
             slots["head"], slots["torso"], slots["arms"], slots["legsreward_per_participant", (30, 100))
        total_rewards = 0
        for pid in ACTIVE_CHAT_EVENT.participants:
            reward = random.randint"],
             weapon(reward_range[0], reward_range[1])
            db.execute("UPDATE players SET crystals=crystals+, ",".join(owned_armors), 1, time.time(), time.time())
        )


def pick_balanced_opponent(player_uid? WHERE user_id: int, player=?", (reward, pid))
            total_rewards += reward
        log_entry += (
_wins: int) -> Optional[int]:
    """Подбирает сопер            f"\nника того же уровня."""
    arena\n{E_TROPHY} < = determine_arena(player_wins)
    limits = ARENAS[arenab>СОБ]
    humans = [r["user_id"] for r in db.fetch_all(
        """SELECT user_id FROM players WHERE userЫТИЕ ЗА_id != ? ANDВЕРШЕ banned=0 ANDНО!</b>\n"
            f" is_bot=0
           AND wins BETWEEN ? AND ? ORDER BY RANDOM() LIMIT 6""",
        (player_uid, limits["min_wins"], limits["max_wins"])
    )]
    bots = [r["user_id👥 Участников: {ACTIVE_CHAT_EVENT.get_participants_count()}\n"
            f"💎 Роздано наград: {total_rewards}"
        )
    return log_entry


def get_chat_event_status() -> Optional[str]:
    """Возвращает статус"] for r in db.fetch_all(
        """SELECT user_id FROM players WHERE is_bot=1 AND banned=0
           AND wins BETWEEN ? AND ? ORDER BY RANDOM() LIMIT 6""",
        (limits["min_wins"], limits["max_wins"])
    )]
    if humans and bots:
        return random текущего события."""
.choice(bots if    global ACTIVE_CHAT_EVENT
    if not ACTIVE_CHAT_EVENT or not ACTIVE_CHAT_EVENT.is_active():
        return None
    time_left = ACTIVE_CHAT_EVENT.get_time_left()
    minutes = time_left // 60
    seconds = time_left % 60 random.random() <
    hp_percent 0.6 else humans)
    if humans:
        return random.choice(humans)
    if bots:
        return random.choice(bots)
    = (ACTIVE_CHAT_EVENT.hp / ACTIVE_CHAT_EVENT.max_hp ensure_masked_bots_exist(10)
    rows = db.fetch_all(
       ) * 100
    """SELECT user_id FROM players WHERE is_bot=1 AND return (
        f"{ACTIVE_CHAT_EVENT.name}\n"
        f"❤️ HP: <b>{ACTIVE_CHAT_EVENT.hp}</b>/{ACTIVE_CHAT_EVENT.max_hp} ({hp_percent:.0f}%)\n"
        f"👥 Участников: <b>{ACTIVE_CHAT_EVENT.get_participants_count()}</b>\n"
        wins BETWEEN ? AND f" ?
           ORDER BY RANDOM() LIMIT⏱ Осталось 1""",
        (limits["min_wins"], limits["max: <b>{minutes}:{seconds:02d}</b>\n\n"
        f"Используйте_wins"])
 команду <code>атака</code> для нанесения урона!"
    )


# =================================================================    )
    return rows[0]["user_id"] if rows else None


def bot_dec=============
#ide_attack_zone(att 12. ПРОМОКОДacker: Fighter,Ы
# ==============================================================================

def create defender: Fighter)_promo_code( -> str:

    code: str,
       """ИИ выбора зоны атаки."""
    if random.random() < reward_crystals: int,
    reward_wins 0.10:
        return random.choice(Z: int,
    max_usesONES)
   : int,
 if defender.hp <= defender.max_hp * 0.3    hours_valid: int,
    created_by: int
) -> Tuple[bool, str]:
    """0:
       Создаёт промокод."""
 return max(ZONES, key=lambda z: attacker.get_weapon_dmg_for_zone(z))
    def score_zone(z    code = code: str) -> tuple:
        dmg = attacker.get_weapon_dmg_for_zone(z) -.strip().upper()
    if not code or len(code) < Config.PROMO_MIN_CODE defender.get_armor_def_LENGTH or len(code) > Config.PROMO_MAX_CODE_LENGTH:
        return False, f"Код должен быть от {Config.PROMO_MIN_CODE_LENGTH} до {Config.PROMO_MAX_CODE_LENGTH} символов."
    if not re.match(r'^[A-Z(z)
        return (dmg0-9_-, ZONE_INFO]+$', code):
        return False, "Код может содержать только буквы, цифры, _[z]["mult"])
    return max(ZONES, key=score_zone)


def bot_decide_attack_variant(attacker: Fighter) -> int:
    """ИИ выбора варианта атаки."""
    variants = WEAPONS[attacker.weapon]["variants"]
    available = attacker.get_available_variants()
    if not available:
        return 0
    return max(available, key и -"
    if reward_crystals < 0 or reward_wins < 0:=lambda i: variants
        return False[i].damage_mult)


def bot_decide_to_defend(duel, "Награ: Duel, botды не могут быть_is_a: bool) -> bool:
    """ИИ решения защищаться."""
    if отрицательными."
    if max_uses < 1 or max duel.bot_block_streak >= 2 or duel.round_no - duel.bot_last_block_round < 3:
        return False
    bot_fighter =_uses > Config.PROMO_MAX_USES:
 duel.a if bot        return False,_is_a else duel f"Максимум активаций: от 1 до {Config.PROMO_MAX_USES}."
    if hours_valid < 1 or hours_valid > Config.PROMO_MAX_H.b
    hpOURS:
        return False, f_ratio = bot_fighter.hp / bot_fighter.max_hp"Срок действия
    if hp_ratio < 0.30:
        base_chance: от 1 до {Config.PROMO_MAX_HOURS} часов."
    existing = db.fetch_one(" = 0.65
    elif hp_ratio < 0.60:
        base_chance = SELECT code FROM promo_codes WHERE code=?", (code,))0.40
    if existing
    else:
        base_chance:
        return False, f"Промокод <code>{code}</code> = 0.25
    return random.random() < base_chance


 уже существует."
    now = time.time()
   def bot_decide expires_at = now_defend_zone(att + (hours_validacker: Fighter, defender: Fighter) * 3600)
    db.execute( -> str:
    """ИИ выбора зоны защиты."""
        """INSERT
    def danger_level(z: str INTO promo_codes
) -> int:
        return attacker.get_weapon_dmg_for_zone(z) - defender.get_armor_def(z)
    sorted_zones = sorted(ZONES, key=danger_level           (code, reward_crystals, reward_wins, max_uses, current_uses, expires_at, created_by, created_at, active)
           VALUES (?, ?, ?, ?, 0, reverse=True), ?, ?,
    if random.random() <  ?, 1)""",
        (code, reward_crystals, reward_wins, max_uses0.25 and len(sorted_zones) > 1:
        return sorted_zones[1, expires_at,]
    return created_by, now sorted_zones[0]


# =================================================================)
    )=============
# 10. КАЗИНО
# ==============================================================================

async def play_c
    return Trueasino_slots_animated(chat_id: int, bet: int, uid:, (
        f"{E_PROMO} Промокод <code>{code}</code> создан!\n\n"
        f"💎 Кристаллы: {reward_crystals int, bot: Bot) -> Tuple[Optional[str}\n🏆 Победы: {], Optional[str]]reward_wins}\n"
        f"👥 Макс. актив:
    """Слоты с анимацией."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if notаций: {max p or p["_uses}\n⏳ Действует: {hours_valid} ч."
    )


def activate_promo_code(user_id: int, code: str) -> Tuple[bool, str]:
    """Активирует промокод."""
   crystals"] < bet:
        return None, "Недостаточно кристаллов."
    if bet < Config.CASINO_MIN_BET: code = code.strip
        return None().upper()
    player = db.fetch_one("SELECT, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E * FROM players WHERE user_id=?", (user_id,))
    if not_CRYSTAL player:
        return False, "}"
    db.execute("UPDATE players SET crystals=crystals-? WHEREСначала отправь /start в Л user_id=?", (С бота."bet, uid))
    if player
    sent_message["banned"]: = await bot.send_dice(chat_id=chat_id, emoji="🎰
        return False, "🚫 Тебе недоступна активация промокодов."
    promo = db.fetch_one("SELECT")
    dice * FROM promo_codes_value = sent_message.dice.value
    if dice_value == 1:
        mult = 10
 WHERE code=?", (code,))
    if not promo        win = bet:
        return False, f" * mult
       ❌ Пром db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (win, uidокод <code>{code}</code> не найден."
    if not promo["active"]:
        return False, f"))
        db❌ Пром.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
        return fокод <code>{code}</code> деактивирован."
    if promo[""{E_SLOT}expires_at"] < time.time():
 Выпало:        return False, <b>{dice_value}</b>\n\n{E_TROPHY} <b>ДЖЕКПОТ ×{mult}!</b>\n f"❌ Промокод <code>{code}</code> истёк."
    if promo["💎 +{current_uses"]win} кристал >= promo["max_uses"]:
        return False, f"❌ Промокод <code>{code}</code> исчерпан."
    already = db.fetch_one("SELECT 1 FROM promo_activations WHERE userлов", None
    else:
        db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
        return f"{E_SLOT} Выпало:_id=? AND code <b>{dice=?", (user_id_value}</b>\n\n{E_SKULL} <b>Нет комбина, code))
    if already:
        return Falseции.</b>\, f"n💎 −{bet} кри❌ Ты уже активировал промокод <code>{code}</code>."
    now = time.time()
сталлов", None


async def play_casino_dice_game(chat_id: int, bet:    db.execute(" int, uid:INSERT INTO promo_activ int, bot:ations (user_id, code, activated_at) VALUES (?, ?, ?)", (user_id, code Bot, mode: str, value: Any = None) -> Tuple[Optional[str], Optional[str]]:
   , now))
 """Кости с    db.execute("UPDATE promo_codes SET current_uses=current разными режимами."""_uses+1 WHERE code=?", (code,))
    rewards = []
    if promo["reward_crystals"] > 0
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] <:
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", ( bet:
        return None, "Недостаточно кристаллов."
promo["reward_cr    if bet <ystals"], user_id))
        rewards.append(f"💎 +{promo['reward_crystals']} кристаллов")
    if Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E promo["reward_w_CRYSTALins"] > 0:
        db.execute("UPDATE players SET wins=w}"
    db.execute("UPDATE players SET crystals=crystals-? WHEREins+? WHERE user_id=?", ( user_id=?", (bet, uid))
    sent_message = await bot.sendpromo["reward_wins"], user_id))
        rewards.append(f"🏆 +{promo['reward_w_dice(chat_id=ins']} победchat_id, emoji="🎲")
    dice_value = sent_message.dice.value
    win = False
    mult = 0
    if mode == "even_odd":
        is_even =")
    rewards_text = "\n".join(rewards) if rewards else "🎁 Секретный бонус!"
    remaining = promo (dice_value %["max_uses"] - promo["current_uses"] - 1
    return True, 2 == 0)
        if (value == "even" and is_even) or (
        f (value == "odd" and not"{E_GIFT} <b> is_even):
ПРОМОКОД            mult = 2
            win = True
    АКТИВИРОВАН!</b>\n\n"
        f"🎟 Код: elif mode == " <code>{codehigh_low":
        if (value == "high" and dice_value >= 4) or (value == "}</code>\n{rewards_text}\n\n"
        f"low" and dice_value <= 3):
            mult = 2
            win = True
    elif mode == "number":
        if dice📊 О_value == value:сталось активаций: {remaining}/{promo['max_uses']}"
    )


# ==============================================================================
# 13. RP СИСТЕМА
#
            mult = 6
            ==============================================================================

RP win = True
_ACTIONS: Dict[str, Tuple[str,    if win:
        payout = bet * mult
 str]] = {
    "удар        db.execute("ить": ("👊", "UPDATE players SET crystalsударил(а=crystals+? WHERE user_id=?", (payout, uid))
        db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user)"),
    "обнять": ("🤗", "обнял(а)"),
    "поцеловать":_id=?", (uid,))
        ("😘", "поцеловал(а return f"{E)"),
    "пнуть":_DICE} Выпало: <b>{dice_value}</b>\n ("🦵", "пнул(а)"),\n{E_T
    "поROPHY} <b>Победа ×{multгладить": ("🤚", "пог}!</b>\ладил(аn💎 +{payout} кристаллов",)"),
    "укусить": ("😬 None
    else", "укус:
        db.execute("UPDATE player_stats SET casino_losses=casino_lossesил(а)"),
    "пожать": ("🤝",+1 WHERE user_id=?", (uid,))
        return f"{E_DICE} Выпало: < "пожал(b>{dice_valueа) руку"),
    "толкнуть": ("💥", "толкнул(а)"),
    "кинуть":}</b>\n\n{E_SKULL} <b ("🥊", "кинул>Поражение.</b>\n💎 −{(а) в"),
    "лечить":bet} кристал ("💊",лов", None


async def play_casino_darts_animated(chat_id: int, bet: int, uid: int, bot: Bot, bet "подлечил(а)"),
    "игнорировать": ("💅", "проигнорировал(а)"),
    "_on_miss: bool = False) -> Tuple[Optional[strсмеяться": ("], Optional[str]]😂", "посмеялся(ась) над"),
   :
    """Дротик с анимацией.""" "плакать":
    p = ("😭", db.fetch_one(" "заплакал(а)SELECT crystals FROM players у ног"),
    "танцевать": ("💃", "стан WHERE user_id=?", (uid,))
    if not p or p["crystals"] <цевал(а bet:
       ) для"),
 return None, "Недостаточно кристаллов."
    "шлепнуть": ("👋", "шлепнул(а)    if bet <"),
    " Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_Bобозвать": ("🤬", "обозвал(а)"),
    "ET} {Eвосхититься": ("😍", "восхитился(ась)"),
    "испуг_CRYSTAL}"
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (аться": ("bet, uid))😱", "испугался
    sent_message = await bot.send_dice(chat_id=(ась)"),
    "подchat_id, emojiмигнуть": ("="🎯")
    dice_value = sent_message.dice.value
    is_hit = dice_value >= 4
    if bet_on_miss:
        if not is_hit:
            payout = int(bet * 1.9)
            db.execute("UPDATE players SET😉", "подмигнул(а)"),
    "пожать_плечами": ("🤷", "пожал(а) плечами при виде"),
    "покормить": ("🍕", "покормил(а)"),
    "напоить": ("🍺", "напоил(а)"),
    crystals=crystals+? WHERE user_id=?", (payout, uid))
            db.execute("UPDATE player_stats SET casino_wins=casino_w "щекотins+1 WHERE user_id=?", (ать": ("🤣", "пощекотал(а)"),
uid,))
    "благословить": ("🙏            return f"{E_DARTS} Выпало: <b>{", "благословил(dice_value}</b>\n\n{а)"),
    "прокE_TROPHYлясть": ("} <b>💀", "проклялПромах! Ты(а)"),
}

RP выиграл!</b>\n💎 +{payout} кристаллов", None
_COOLDOWNS: Dict[Tuple        else:
[int, int,            db.execute(" str], float]UPDATE player_stats SET casino_losses=cas = {}


def generate_rp_text(actorino_losses+1_id: int, WHERE user_id=?", (uid,))
            return f"{E_DARTS} Выпало: <b>{dice_value}</b>\n\n{E_SKULL} <b>Попа actor_name: str, target_id: int, target_name: str, action_key: str) -> str:
    """Генерирует текст RP-действия."""
    emoji, verb = RP_ACTIONS.getдание. Ты про(action_key, ("✨", "взаимодействовал(а) с"))
    actorиграл.</b>\n💎 −{bet} кристаллов",_mention = create None
    else:
        if_mention(actor_id is_hit:
, actor_name)            payout = int(bet * 
    target_mention = create_ment1.9)ion(target_id,
            db.execute target_name)
    return f"{("UPDATE players SET crystals=crystals+? WHERE useremoji} {actor_id=?", (payout, uid))
            db.execute_mention} {verb} {target_mention}!"("UPDATE player_stats


# ============================================================================== SET casino_wins=casino_wins+1 WHERE user_id=?", (
# 14. ПАРСЕР ЦЕЛЕЙ
# ==============================================================================uid,))
            return f"{

def resolve_command_target(m: MessageE_DARTS, command_word:} Выпало str) -> Tuple: <b>{[Optional[int], Optional[str]]:
    """Универсальный парсер целей."""
    if m.reply_to_message and m.reply_to_message.from_user and not m.reply_to_message.from_user.is_bot:
        return m.reply_to_message.from_user.id, Nonedice_value}</b>\n\n{E_TROPHY} <b>Попадание!</b>\n💎 +{payout} кристаллов", None
        else:
            db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?",
    text = (uid,))
            return f"{E_DARTS} Выпало: <b>{dice_value}</ m.text or ""b>\n\n
    if text.lower().startswith(command_word.lower()):
        rest_of_text = text[len(command_word):].strip()
    else:
        rest_of_text = text
    match = re.search(r'@(\w+{E_SKULL} <b>Промах.</b>\n💎)|(-?\d −{bet}+)', rest_of_text)
    кристаллов", None


async def play_casino_basketball_animated(chat_id: int, bet: int, uid: int, bot: Bot, bet_on_miss: bool = False) -> Tuple[Optional[str if match:
        val = match.group(1) or match.group(2)
        if val.lstrip('-').isdigit():
            row = db.fetch_one("SELECT user_id FROM players WHERE user_id=? AND banned=0", (int(val),))
            if row:
                return row["user_id"], None
        else:
            row = db.fetch_one(
                """SELECT user_id FROM players
                   WHERE (LOWER(username)=LOWER(?) OR LOWER(name)=LOWER(?)) AND banned=0 LIMIT 1""",
                (val, val)
            )
            if row:
                return row["user_id"], None
    if m.chat.type == "private":
        return None, f"Укажи цель: ответь на сообщение или напиши <code>{command_word} @user</code> / <code>{command_word} ID</code>"
    return None, f"⚠️ В группе команда работает <b>ответом</b> или через <code>@username</code> / <code>ID</code>."


# ==============================================================================
# 15. МЕНЮ И КЛАВИАТУРЫ
# ==============================================================================

BTN_ARENA = "⚔️ Арена"
BTN_CASINO = "🎰 Казино"
BTN_GEAR = "], Optional[str]]:
    """Баскетбол с анимацией."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."
    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))
    sent_message = await bot.send_dice(chat_id=chat_id, emoji="🏀")
    dice_value = sent_message.dice.value
    is_hit = dice_value == 5
    if bet_on_miss:
        if not is_hit:
            payout = int(bet * 1.9)
            db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
            db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
            return f"{E_BASKET} Выпало: <b>{dice_value}</🎒 Снаряжение"
BTN_TOP = "🏆b>\n\n Топ"
MENU_TEXTS = {BTN_ARE{E_TROPHY} <b>Промах!NA, BTN_C Ты выигралASINO, BTN_GEAR, BTN_TOP}

MENU!</b>\n💎 +{_KB = Replypayout} криKeyboardMarkup(
сталлов", None
        else:
            db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id    keyboard=[
        [KeyboardButton(text=BTN_ARENA), KeyboardButton(text=BTN_CASINO)],=?", (uid,
        [Keyboard))
           Button(text=BTN_GEAR), KeyboardButton(text=BTN_TOP)],
    ],
    resize_keyboard=True,
)


# ================================================================= return f"{E_BASKET} Выпало: <b>{dice_value}</b>\n\n{E_SKULL} <=============
# 16. Гb>СлЕНЕРАТОРЫ UI
#эм-данк. Ты проиг ==============================================================================

рал.</b>\def generate_arena_menu_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Генерирует меню арены.
    
   n💎 −{bet} кристаллов", None
    else:
        if is_hit:
            payout = int(bet * 1.9)
 ВАЖНО:            db.execute(" КUPDATE players SET crystals=crystals+? WHERE user_id=?", (payoutнопка "Мой профиль" уб, uid))
            db.executeрана — теперь используется отдель("UPDATE player_statsная команда /profile.
    """
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
    a SET casino_wins = ARENAS[d=casino_wins+1 WHERE user_id=?", (uid,))
            return f"{E_BASKET} Выпало: <b>{dice_value}</b>\n\n{etermine_arena(p["wins"])]E_TROPHY
    text =} <b>СЛЭМ-ДАНК!</b>\n💎 +{payout} кристаллов", None (
        f"╔══════════════════════════╗\n      ⚔️
        else: <b>АР
            db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
            returnЕНА ДУЭЛЯНТОВ</b>\n╚══════════════════════════╝\n\n f"{E_BASKET} Выпало: <b>{dice_value}</b>\n"
        f"{E_TROPHY} Победы: <b>{p['wins']}</b>\n"
\n{E_SKULL} <b>Промах.</        f"{Eb>\n_SKULL} Поражения: {p💎 −{bet} кристаллов['losses']", None


def}\n"
        f"{E_CRYSTAL} Кристаллы play_casino_roulette(uid: int, bet: int, bet_type: str, bet_value: Any = None) -> Tuple[Optional[str], Optional[str]]:
    """Рулетка с разными типами ставок."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] <: <b>{format_number(p['crystals'])}</b>\n"
        f"📍 {a['emoji']} <b>{a['name']}</b>\n\n"
        f"🥉 Бронза — 0–9 побед · <b>{ARENAS['bronze']['prize']} {E_CRYSTAL bet:
        return None, "Недостаточно кристаллов."
    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    reds = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19}</b>\n"
        f"🥈 Серебро — 10–29 побед · <b>{ARENAS['silver']['prize']} {E_CRYSTAL}</b>\, 21, 23, 25, 27, 30, 32, 34, 36}
    num = random.randint(0, 3n"
        f"🥇 Золото — 30+ побед ·6)
    if num ==  <b>{ARENAS['gold']['prize']} {E_CRYSTAL}</b>"
    )
    kb = build_vertical_keyboard_with_styles([
        ("🎲 Найти соперника", "arena:find", "success"),
        ("👹 Боссы", "arena:bosses", "danger"),
        ("📋 Список соперников", "arena:list", "primary"),
0:
        res_color = "green"
        color_emoji = E_GREEN
    elif num in reds:
        res_color = "        ("🔎 Вызвать по нику", "arena:find_name", "primaryred"
       "),
        (" color_emoji =🏆 Т E_RED
    else:
       оп арен", "top:cur", res_color = " "primary"),
black"
        color_emoji =    ])
    return text, kb


def generate_bosses_menu_screen E_BLACK
    db.execute("UPDATE players SET crystals=crystals-?(uid: int) WHERE user_id=?", (bet, uid))
    win = False
    mult = 0
    if bet_type == "color":
        if bet_value == res_color:
            -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует меню боссов."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
 mult = 1    if not p4 if res_color == "green" else 2
:
        return "Профиль не найден.", None
    lines =            win = True ["╔════
    elif bet_type == "even_odd":
        if num != 0:
            is_even = (num % 2 == 0)══════════════════════╗\n      👹 <b>БОССЫ АРЕНЫ</
            if (bet_value == "even" and is_even) or (bet_value == "odd" and not is_even):
                mult = 2
                win = True
    elif bet_type == "half":
        if num != 0:
            if (bet_value == "low" and 1 <= num <= 18) or (bet_value == "high" and 19 <= num <= 3b>\n6):
                mult = 2
                win =╚══════════════════════════╝\n"]
    buttons = []
    for bkey, b in BOSSES.items():
        locked True
    elif = p["wins"] < b["min_wins"] bet_type == "
        lock_text = f"🔒 нужен {number":
       b['min_wins']} {E_TROPHY}" if num == bet_value:
            mult = 3 if locked else f6
            win"награда ×{b['reward_mult']}"
        lines.append(f"{b['name']}\n  ❤️ HP {b['hp']} · ⚔️ {WEAPONS[b['weapon']]['name']}\n  {b['desc']}\n  → {lock_text}\n")
        buttons.append((b = True
    elif bet_type == "dozen":
        if num["name"] if not locked else f"{b['name']} 🔒", f"arena:boss:{bkey != 0:
            if (bet_value == 1 and 1 <= num <= 12) or}", "danger" (bet_value == if not locked else "primary"))
 2 and 13 <= num    buttons.append(( <= 24) or (bet_value == 3 and 25 <= num <= f"{E_BACK} Назад", "arena:menu", "success"))36):

    return "\n".join(lines), build_vertical_keyboard_with_styles(buttons)


def generate_gear_screen(uid                mult = 3
                win = True
    if win:
        payout = bet: int) -> * mult
        Tuple[str, Optional db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
        db.execute("UPDATE player_stats SET casino[InlineKeyboardMarkup]]:
    """
    Генерирует экран снаряжения.
    
    ВАЖНО: Кнопка "Мой профиль_wins=casino_wins+" убрана — теперь используется отдельная1 WHERE user_id команда /profile.
    """
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (=?", (uid,))
        return f"🎡 Выпало: {color_emoji} <b>{num}</uid,))
b>\n\n    if not p:
        return "Профиль не{E_TROPHY} <b>Победа найден.", None
    w = WEAPONS[p["weapon"]]
    f = create ×{mult}_fighter_from_db(p)
    slots = get_player_armor_slots(p)
    lines!</b>\n💎 +{payout} кристаллов", None
    else:
        db.execute("UPDATE player_stats SET casino_losses=c = [
       asino_losses+ f"🎒 <b>{esc(p['name'])}</b>",1 WHERE user_id=?", (uid,))
        return f" "",
        f🎡 Выпало"{E_TROPHY} Победы: <b>{p['wins']}</b>",
        f"{E_SKULL} Поражения:: {color_emoji} <b>{num}</b>\n\n{E_SKULL} <b>Поражение.</b {p['loss>\n💎 −{bet} кристаллов", None


def play_casino_coin(uid: int, bet: int,es']}",
 choice: str =        f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>",
        f"📍 {ARENAS "heads") -> Tuple[Optional[str[determine_arena], Optional[str]]:
    """(p['wins'])]['emoji']} {Монетка."""
    p = db.fetch_one("SELECT crystals FROM playersARENAS[determine_arena(p['wins'])]['name']}", "",
        f"❤ WHERE user_id=?",️ HP: <b>{f.max (uid,))
    if not p or p["crystals"] < bet:
       _hp}</b>", return None, "Недостаточно кристаллов."
    if bet < Config.CASINO
        f"⚔️ Атака: <b>{f.base_weapon_dmg}</b>", "",
        "<b>⚔_MIN_BET:️ Оружие
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    result:</b>",
        f"  {w['emoji']} {w['name']} — <i>{w['description']}</i>",
        f"  Базов = random.choice(["ый урон:heads", "tails"])
    db.execute("UPDATE players SET crystals=crystals-? WHERE <b>{w['base_dmg user_id=?", (']}</b>", "",bet, uid))
    result_text = "Орёл" if result
        "<b == "heads">🛡 else "Реш Броня по слотам:</b>"
   ка"
    result_emoji = "🔵 ]
    for slot in ZONES:
        item" if result == = get_armor_item "heads" else "🔴_by_key(slots[slot]) or get"
    if_armor_item_by_key result == choice:
        db.execute("UPDATE players SET crystals=crystals+? WHERE user(f"{slot}_none")
        lines.append(f"  {ZONE_INFO[slot]['emoji']}_id=?", (bet {ZONE_INFO[slot]['name']}: {item['emoji']} <b>{item['name']}</b> (защита {item['df']}) * 2, uid))
        db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
        return f"{E_CO")
    kb = build_vertical_keyboard_with_styles([
        ("⚔️ Оружие", "gear:w", "primary"),
        ("🛡 БIN} Выпроня", "gear:armor_menu", "primary"),
    ])
ало: {result_emoji} <b>{result_text}</b>\n\n{E_TROPHY} <b>Победа!</b>\n💎 +    return "\n".join(lines), kb


def generate_weapon_list(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует список оружия."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
    equipped = p["weapon"]
    owned = set((p["weapons_owned"] or "").split(","))
    lines = ["⚔{bet * 2} кристаллов", None
    db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
    return f"{E_COIN} Выпало: {result_emoji} <b>{result_text}</b>\n\n{E_SKULL} <b>Поражение.</b>\n💎 −{bet} кристаллов", None


def play_casino_highlow(uid: int, bet: int,️ <b>Оружие</b>", f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>", ""]
    buttons = []
    for key, it in WEAPONS.items():
        lines.append(f"{it['emoji']} <b>{it['name']}</b> — <i>{it['description']}</i>")
        lines.append(f"  Базовый урон: {it['base_dmg']} · Цена: {it['price']}💎")
        lines.append("  Варианты атаки:")
        for i, v in enumerate(it["variants"]):
            effect_text = f" [{v.effect}]" if v.effect else ""
            lines.append(f"    {i+1}. {v.name} ×{v.damage_mult}{effect_text} (КД: {v.cooldown_rounds})")
        lines.append("")
        if key == equipped:
            label = "✅ надето"
            style = "success"
        elif key in owned:
            label = "🎒 надеть"
            style = "primary"
        else:
            label = f"{it['price']}💎"
            style = "danger"
        buttons.append((f"{it['emoji']} {it['name']} · {label}", f"buy_weapon:{key}", style))
    buttons.append((f"{E choice: str = "high") -> Tuple[Optional[str], Optional[str]]:
    """Больше/Меньше."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."
    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    result_num = random.randint_BACK} Назад", "gear:(1, 100)
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))
    if result_num == 50:
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (bet, uid))
        return f"📊 Выпало: <b>{result_num}</b>\n\n🤝 <b>Ровно 50!</b> Ставка возвращена.", None
    win = (choice == "high" and result_num > 50) or (choice == "low" and result_num < 50)
    if win:
        payout = int(betmenu", "success * 1.9)
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
       "))
    return "\n".join(lines), build_vertical_keyboard_with_styles(buttons)


def generate_armor_slot_menu(uid: int) -> Tuple[str, Optional[InlineKeyboard db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
        return f"📊 Выпало: <b>{result_num}</b>\n\n{E_TROPHY} <b>Победа!</b>\nMarkup]]:
💎 +{    """Генерирует меню слотов брони."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль неpayout} кристаллов", None
    db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id найден.", None=?", (uid,
    slots =))
    return f"📊 Выпало: <b>{result_num}</b get_player_armor_slots>\n\n{(p)
    lines = ["🛡 <b>Броня — выбери часть тела</b>", f"{E_CRYSTAL} Кристаллы: <b>{formatE_SKULL} <b>Поражение.</b>\n💎 −{bet} кристаллов", None


# =================================================================_number(p['cr=============
# 11. ЧАТОВЫЕ СОБЫТИЯ
ystals'])}</b>", ""]
    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item# ==============================================================================

def spawn_chat_event(
    event_by_key(f"{_type: str,
    started_by: int,
slot}_none")
        lines.append(f"{ZONE_INFO[slot]['emoji']} <b>{ZONE_INFO[slot]['name']}</b> — {item['emoji']} {item['    custom_hp:name']} (за Optional[int] = None,
    custom_duration: Optional[float] = None
) -> Optional[ChatEvent]:
    """Создаёт чатовое событие."""
    global ACTIVE_CHAT_EVENT
    if ACTIVE_CHAT_EVENTщита {item['df']})")
    kb = build_vertical_keyboard_with_styles([
        ("🧠 Голова", and ACTIVE_CHAT_EVENT.is_active():
 "gear:head        return None
", "primary"),    template = CH
        ("🫀 Торс", "gear:AT_EVENT_TEMPLATES.get(event_type)
    iftorso", "primary"),
        ("💪 Руки", "gear not template:
        return None
    hp = custom_hp or template[":arms", "base_hp"]
    duration = custom_duration or template["duration_hours"]
primary"),
        ("🦵 Ноги", "gear:legs", "primary"),
    name = template["name_template"].        (f"{E_BACK} Назад", "gear:menu", "success"),
    ])
    returnformat(emoji=template["emoji"])
    now = time.time()
    ends_at = now + (duration * 3600)
    event = Chat "\n".joinEvent(
       (lines), kb


def generate_armor_slot_list(uid: int, slot: str) -> Tuple[str event_id=int(now, Optional[Inline), event_type=event_type, name=nameKeyboardMarkup]]:
    """Генерирует список брони для слота,
        hp=hp, max_hp=hp, started_by=started."""
    p_by, started_at=now, ends_at=ends_at = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,,
    )))
    if
    ACTIVE_CHAT_EVENT = event
 not p or slot    db.execute( not in ZONES:
        return
        """INSERT INTO chat_events (event_type, name "Ошибка.", None
    slots = get_player_armor_slots(p)
    equipped = slots.get(slot, f"{slot}_none")
    owned = set((p["armors_owned"], hp, max or "").split(","_hp, started_by, started_at, ends_at, active)
           VALUES (?,?,?,?,?,?,?,1)""",
        (event_type, name, hp, hp, started_by, now))
    lines = [f"🛡 <b>Брон, ends_at)я на {ZONE
    )
    return event


def attack_chat_event(attacker_id:_INFO[slot]['name'].lower()}</b>", f"{E int, attacker_name_CRYSTAL} Кристаллы: <b>{format_number(p[': str) -> Optional[str]:
    """Атакует чатовое событие."""
    global ACTIVE_CHATcrystals'])}</_EVENT
    ifb>", ""]
    buttons = []
    for item in ARMOR_DATA[slot]:
        key = item not ACTIVE_CHAT_EVENT or not ACTIVE_CHAT_EVENT.is_active():
        return None
    base_dmg = random.randint(Config.EVENT_MIN_DAMAGE, Config.EVENT_MAX_DAMAGE)
   ["key"]
        lines.append(f"{item['emoji']} <b>{item['name']}</ is_crit = randomb> — защита.random() < Config <b>{item['df']}</b.EVENT_CRIT_CHANCE
    if>, HP +{ is_crit:
        base_dmg = int(base_dmg * Config.EVENT_CRIT_MULT)
    log_entry = ACTIVE_CHAT_EVENT.take_damage(attackeritem['hp']}")
        lines.append(f"    {item['desc']}")
        if key == equipped:
            label = "✅ на_id, attacker_name, base_dmg, is_crit)
    db.execute("UPDATE player_stats SET event_participations=event_participдето"
            style = "success"
        elif key in owned:
            label = "🎒 надеть"
            style =ations+1 WHERE "primary"
 user_id=?", (attacker_id,))
    if ACTIVE_CHAT_EVENT.hp        else:
            label = f"{item['price <= 0:']}💎"
        ACTIVE_CHAT
            style = "danger"
        buttons.append((f"{item['emoji']} {item['name']} · {label}", f"buy_armor:{slot}:{key}", style))
    buttons.append((f_EVENT.active = False
        db.execute("UPDATE chat_events SET active=0 WHERE event_id=?", (ACTIVE_CHAT_EVENT.event_id,))
        template = CHAT_EVENT_TEMPLATES.get(A"{E_BACK}CTIVE_CHAT_EVENT К слотам", "gear:armor_menu", ".event_type, {})
        reward_range = template.get("reward_per_participant", (30success"))
    return "\n"., 100))
        total_rewards = 0
        forjoin(lines), build_vertical_keyboard_with_styles(buttons)


 pid in ACTIVE_CHATdef generate_top_screen_EVENT.participants:
            reward = random.randint(reward_range[(uid: int, arena_key: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует экран0], reward_range[1])
            db.execute(" топа."""
UPDATE players SET crystals    a = ARENAS[arena_key]
    rows = db.fetch_all(
        """SELECT user_id, name, wins, losses FROM players
           WHERE is_bot=0 AND banned=0 AND wins=crystals+? WHERE user_id=?", (reward, pid))
            total_rewards += reward
        log_entry += (
            f"\n\n{E_TROPHY} <b>СОБ BETWEEN ? AND ?ЫТИЕ ЗА
           ORDER BY wins DESC, losses ASC LIMIT ?""ВЕРШЕНО!</b>\n"
           ",
        ( f"a["min_wins"], a["max_wins"],👥 Участников: {ACTIVE_CHAT_EVENT.get_participants_count()}\n" Config.TOP_LEADERBOARD_SIZE)

            f"    )
    medals = ["🥇", "💎 Роздано наград: {total_rewards}"
        )
🥈",    return log_entry "🥉"]
    lines = [f"{a['emoji']} <b>{a['name']}</b> — топ по


def get_chat_event_status() -> Optional[str]:
    """Возвращает статус текущего события."""
    global ACTIVE_CHAT победам", ""]
    if not rows:
        lines.append("<_EVENT
    if not ACTIVE_CHAT_EVENT or not ACTIVE_CHAT_EVENT.is_active():
        return None
    time_left = ACTIVE_CHAT_EVENT.get_time_left()
    minutes = time_left // i>Пока никого нет на этой арене.</i>")
    for i, r in enumerate(rows):
        mark = medals[i] if i < 3 else60
    seconds = time_left % 60
    hp_percent = (ACTIVE_CHAT f"{i + 1}."
        you = " ← ты"_EVENT.hp / ACTIVE if r["user_CHAT_EVENT.max_hp) * 100
    return (
        f"{ACTIVE_CHAT_id"] == uid else ""
        lines.append(f"{mark} <b>{esc(r['name'])}</b> — {r_EVENT.name}\n['wins']} {E_TROPHY} / {r['losses']} {E_SKULL}{you}")
    me = db"
        f"❤️ HP: <b>{ACTIVE_CHAT_EVENT.hp}</b>/{ACTIVE_CHAT_EVENT.max_hp} ({hp_percent:.0f}%)\n"
        f"👥.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if me and all(r["user Участников: <_id"] != uidb>{ACTIVE_CHAT_EVENT.get_participants_count()}</b>\ for r in rows) and a["n"
        f"⏱ Осталось: <b>{min_wins"]minutes}:{seconds:02d}</b>\n\n"
        f <= me["wins"] <= a["max_wins"]:
        rank_row = db.fetch_one"Используйте(
            """ команду <code>атака</codeSELECT COUNT(*) c FROM players
              > для нанесения у WHERE is_bot=0 AND banned=0 AND winsрона!"
    )


# ==============================================================================
# 12. ПРОМОКОДЫ
# ================================================================= BETWEEN ? AND ? AND wins > ?""",
            (a["min_wins"], a["max_wins"], me["wins"])
        )=============

def create_promo_code(
    code: str,
    reward_crystals
        rank =: int,
 (rank_row["    reward_winsc"] if rank: int,
_row else 0    max_uses: int,
    hours_valid: int,
   ) + 1 created_by: int
        lines +=
) -> Tuple[bool, str]:
    """ ["…", f"{rank}. <b>{esc(me['name'])}</Создаётb> — { промокод."""
    code = code.strip().upper()
    if not code or len(code) < Config.PROMO_MIN_CODE_LENGTH or len(code) > Config.Pme['wins']} {E_TROPHY} / {me['losses']} {E_SKULL} ← ты"]
    lines += ["", f"{E_TROPHY} Победа: +1 и деньги. {E_SKULL} Поражение: −1 без награды."]
    kb = build_vertical_keyboard_withROMO_MAX_CODE_LENGTH:
        return False, f"Код должен быть от {Config.PROMO_MIN_CODE_LENGTH} до_styles([
        {Config.PROM ("🥉 Бронза",O_MAX_CODE_LENGTH} символов."
    if "top:bron not re.match(rze", "danger"),
        ("🥈 Серебро", "top:silver", "'^[A-Z0-9_-]+$', code):
        return Falseprimary"),
       , "Код может содержать только буквы ("🥇 Золото",, цифры, _ и -"
    if reward_cr "top:gold", "success"),
        (fystals < 0 or reward_wins"{E_BACK} < 0: Назад", "
        return Falsearena:menu",, "Награ "success"),
    ])
    return "\n".ды не могут быть отрицательными."
    if max_uses < 1 or max_uses > Config.PROMO_MAX_USES:
        return False, f"Максимум активаций:join(lines), kb от 1 до {Config.PROMO_MAX_USES


def generate_arena_list_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует список соперников."""
    p = db.fetch_one("SELECT * FROM}."
    players WHERE user_id=?", (uid,))
    if not p:
        return "Про if hours_valid < 1 or hours_valid > Config.PROMO_MAX_Hфиль не найденOURS:
       .", None
    key = determine_arena(p["wins"])
    a return False, f"Срок действия: от 1 до {Config.PROMO_MAX_H = ARENAS[key]
    rows = db.fetch_allOURS} часов."
    existing = db.fetch_one("SELECT code FROM promo_codes WHERE code=?",(
        """SELECT user_id, name, wins, (code,))
    if existing:
        return False, f"Промокод <code>{code}</code> losses FROM players
 уже существует."
    now = time           WHERE user_id != ? AND banned=0 AND wins BETWEEN ? AND ?
           ORDER BY RANDOM() LIMIT 8""",
        (uid,.time()
    a["min_w expires_at = now + (hours_validins"], a["max_wins"])
    )
    if not rows:
        return (
            "Сейчас * 3600)
    db.execute(
        """INSERT INTO promo_codes
 на твоей           (code, reward_crystals, reward_wins, max_uses, арене никого нет — жми «Найти соперника».",
            build_vertical_keyboard_with_styles([
                ("🎲 Найти", "arena current_uses, expires_at, created_by, created_at, active)
           VALUES (?, ?, ?, ?, 0, ?, ?,:find", " ?, 1)success"),
                (f"{E_BACK} Назад""",
        (code, reward_crystals, reward_wins, max_uses", "arena:, expires_at, created_by, nowmenu", "primary"),
            ])
        )
    buttons = [])
    )
    return True
    for r in rows:
        buttons.append((, (
       f"{r['name'][:16]} · {r['wins']}{E_TRO f"{E_PROMO} Промокод <code>{code}</code> создан!\nPHY}/{r['\n"
        f"💎losses']}{E_SKULL}", f"duel Кристаллы: {reward_crystals}\n:pick:{r['user_id']}", "primary"))🏆 Победы: {
    buttons.appendreward_wins}\n"
        f"((f"{E_BACK} Назад", "arena:👥 Макс. активаций: {maxmenu", "success_uses}\n"))
    return f"{a['emoji']} <b⏳ Действует: {hours>{a['name_valid} ч."']}</b> — соперники:", build_vertical_keyboard_with_styles(buttons)


def generate_profile_text(row: sqlite3.Row) -> str:
    """Генерирует
    )


def activate_promo_code(user_id: int, code: str) -> Tuple[bool, str]:
    """Активирует промокод."""
    текст code = code.strip профиля."""
   ().upper()
 if not row:
        return "    player = db.fetch_one("SELECT * FROM players WHERE user_id=?", (user_id,))
    if notПрофиль не найден."
    w = WEAPONS[row["weapon player:
        return False, ""]] if row["weapon"] in WEAPONS else WEСначала отправьAPONS[" /start в ЛС бота."
    if player["banned"]:fists"]
    f = create_fighter_from_db(row)
    slots = get_player_armor_slots(row)
    arena
        return False, "🚫 Тебе недоступна активация промо = ARENAS[determine_arena(row["wins"])]
    auto_acceptкодов."
    promo = db.fetch_one("SELECT = "✅ ВКЛ" if row.get("auto_accept", 0) else " * FROM promo_codes❌ ВЫКЛ"
    lines WHERE code=?", (code,))
    if not promo:
        return False, f" = [
       ❌ Пром f"👤 <b>{esc(row['nameокод <code>{code}</code> не найден."
    if not promo["active'])}</b>", "",
        f"]:
        return"{E_TRO False, f"❌ Промокод <code>{code}</codePHY} Победы: {row['wins']}",
        f"{E_SK> деактивирован."
    if promo["expires_at"] <ULL} Поражения time.time():
: {row['losses']}",
        f"{E_CRYSTAL} Кристал        return False, f"❌ Промокодлы: {format <code>{code_number(row['crystals'])}",
        f"📍 {arena['emoji']}}</code> истёк."
    if promo["current_uses"] >= promo["max_uses"]:
 {arena['name']}", "",
        f"❤️ HP: <b>{f.max_hp}</b>",        return False,
        f"{ f"❌ Промокод <code>{code}</code> исчерпан."
w['emoji']}    already = db {w['name.fetch_one("SELECT 1 FROM promo']} — баз. урон <b>{w['_activations WHERE userbase_dmg']}</_id=? AND code=?", (user_id, code))
b>", "",
        f"⚡ Авто-приём вызов    if already:
        return False, f"❌ Ты уже активировал промокод <code>{code}</code>."ов: <b>{auto_accept}</b>", "",
        "<b>
    now = time.time()
    db.execute("🛡 Броня:</bINSERT INTO promo_activ>"
    ]
    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armorations (user_id, code, activated_at) VALUES (?, ?, ?)", (user_id, code, now))
    db.execute("UPDATE promo_codes SET_item_by_key(f current_uses=current"{slot}_none")
        lines.append(f"  {ZONE_INFO[slot]['emoji']}_uses+1 WHERE code=?", ( {ZONE_INFO[slot]['name']}: {item['emoji']} {item['name']} ({item['df']})code,))
")
    return    rewards = []
    if promo["reward_crystals"] > 0:
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (promo["reward_cr "\n".join(lines)


def generate_profile_kb(uid: int) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуystals"], user_idру профиля.
))
        rewards.append(f"💎 +{promo    
    Содержит кнопки: Снаряжение, Настройки, На['reward_crystals']} кристаллов")
    if promo["reward_wins"] > 0:
        db.execute("UPDATEзад.
    players SET wins=w """
    return build_vertical_keyboard_with_styles([
        ("🎒 Снаряжение", "gear:menu", "primaryins+? WHERE user_id=?", (promo["reward_wins"], user_id))
        rewards.append(f"🏆 +{promo['reward_w"),
        (f"{E_SETTINGS} Настройки", "profile:settingsins']} побед", "primary"),")
    rewards_text = "\n".join(rewards
        (f"{E_BACK} Назад", "arena:menu",) if rewards else "success"),
    ])


def "🎁 Секретный бонус!"
    remaining = promo["max_uses"] - promo["current_uses"] generate_settings_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
 - 1
    """Ген    return True, (
        f"{E_GIFT} <b>ПРОМОКОД АКТИВИРОВерирует экран настроек."""
    p = db.fetch_one("SELECT * FROM players WHERE userАН!</b>\n\n"
        f"🎟 Код: <code>{code_id=?", (uid,))
    if not p:
        return "Профиль не най}</code>\n{rewards_text}\n\n"
        f"📊 Осталось активацийден.", None
    auto_accept = bool(p.get("auto_accept", 0))
    status = "✅ ВКЛЮ: {remaining}/{ЧЕНО"promo['max_ if auto_accept elseuses']}"
    )


# ==============================================================================
# 13. RP СИСТЕМА
# ==============================================================================

RP_ACTIONS: Dict[str, Tuple[str, str]] = {
    "ударить": ("👊", " "❌ ОТКЛЮЧЕНО"
    text = (
        f"{E_SETTINGS} <b>НАСТРОЙКИ</b>\n\n"
        f"👤ударил(а <b>{esc)"),
    "обнять": ("🤗(p['name'])}</b>\n\n"
        f"⚡ <b>", "обнялАвто-приём(а)"), вызовов:</b>\n"
        f"{status}\n\n"
        f"<i>Если включено, то при вызове на
    "по дуэль бой начинается сразу, "
        f"без ожидания подтверждения.</iцеловать": ("😘", "поцеловал(а)"),
    "пнуть": ("🦵", "пнул(а)"),
    "погладить": ("🤚", "пог>"
    )
    kb = build_vertical_keyboard_with_styles([
        (f"{'🔴 Отключить' ifладил(а auto_accept else ')"),
   🟢 В "укусить": ("😬", "укусил(а)"),
    "ключить'} авто-приём", "settings:toggle_auto_accept", "danger" if auto_accept else "success"),
        (f"{E_BACK} Назад к профилю", "profile:back",пожать": (" "primary"),
🤝", "пожал(а) руку"),
    "толкнуть": ("💥", "толкнул(а)"),
    "кинуть": ("🥊", "кинул(а) в"),
    "лечить": ("💊",    ])
    "подлеч return text, kbил(а)"),
    "


def generate_duel_status_text(duel: Duel, for_uid: int, extra: str = "", timerигнориров_left: Optional[intать": ("💅", "проигнориров] = None) -> str:
ал(а)"),
    "смеяться": ("😂", "посмеялся(ась) над"),
       """Генерирует статус боя."""
    role = duel.get_state_for(for_uid)
    me = "плакать": duel.get_fighter(for_uid) or duel.a
    opp = duel.get_opponent(for_uid) or duel.b
    if role == "attacker ("😭", "заплакал(а) у ног"),
    "танцевать": ("💃", "стан" and duel.chцевал(а) для"),
    "шлепнуть": ("👋", "шлепosen_variant_idx is None:
        prompt = "🎯 <b>Твой ход</b> —нул(а) выбери вариант а"),
    "таки"
   обозвать": elif role == " ("🤬", "обозвал(а)"),
    "attacker":
        prompt = "🎯 <b>Твой ход</b>восхититься — выбери зону": ("😍", "восхитился(ась удара"
    elif role ==)"),
    "испугаться": (" "defender":
        prompt = f"{E_SHIELD} <b>{duel.get😱", "испугался(ась)"),_attacker().name}</b> атакует — выб
    "подмигнуть": ("😉", "подмигнул(ери, что защищать"
    else:
       а)"),
 prompt = "    "пожать⏳ Бой_плечами": ("🤷", "пожал(а) плечами при виде"),
    идёт…"
    if timer_left is "покормить not None and role": (" in ("attacker🍕", "пок", "defender"):
        prompt += f"\n⏱ Оормил(асталось: <)"),
    "напоить": ("b>{timer_left} сек</b>"
    body = "\n".🍺", "наjoin(f"  {ln}" forпоил(а)"),
    ln in duel.log[-DUEL_LOG_DISPLAY_LIMIT:]) if "щекотать": ("🤣", "пощ duel.log else "  <i>Бой начинается…</i>"
    boss_line = f"{E_BOекотал(а)"),
    "благSS} <bословить": ("🙏", "благ>БОЙ Сословил(а)"),
    "прок БОССОМ</b>  ·  награда ×{duel.reward_mult}\n\n" if duelлясть": ("💀", "проклял(а)"),.is_boss else
}

RP ""
    return (
        f"╔════_COOLDOWNS: Dict[Tuple[int, int, str], float]════════════════ = {}


def generate_rp_text(actor_id: int, actor_name: str══════╗\n      ⚔️ <b>РАУНД {, target_id: int, target_name: str, action_key: str) -> str:
    """Генерирует текст RP-действия."""
    emoji, verb = RP_ACTIONS.getduel.round_no}</b>\n╚══════════════════════════╝\n\n"
        f"{boss_line}┌─ 🔵 <b(action_key, (">ТЫ</b✨", "взаимодействовал(а) с>\n{format_fighter_card(me)}\n└────────────\"))
    actorn\n"
_mention = create        f"_mention(actor_id, actor_name)┌─ 🔴
    target_mention = create_mention(target_id, target_name)
 <b>СОПЕРНИК</b>\n{format_fighter    return f"{_card(opp)}emoji} {actor_mention} {verb} {target_mention}!"\n└


# ==============================================================================
#────────────\n\n"
        f"📜 <b>Последние действия 14.:</b>\n{body}\n ПАРСЕР\n━━━━━━━━━━━━━━━━━━━━\n{prompt}"
        + (f"\n\n{extra}" if extra else "")
    )


def get_attack_variant_kb(uid: int) -> InlineKeyboard ЦЕЛЕЙ
# ==============================================================================

def resolve_commandMarkup:
   _target(m: Message """Клавиатура, command_word: str) -> Tuple[Optional[int], Optional[str]]:
    """Универсальный парсер целей."""
    if m.reply выбора варианта атаки."""
    duel = ACTIVE_DUELS.get(uid)
    if not duel:
        return build_vertical_keyboard([])
   _to_message and m.reply_to_message.from_user and not m.reply_to_message.from_user.is_bot:
        return m.reply_to_message.from weapon = WEAP_user.id, None
    text =ONS[duel m.text or ""
    if text.lower().startswith(command_word.lower()):
        rest_of_text = text[len(command.get_attacker().weapon]
    buttons = []
    for i, v in enumerate(_word):].strip()
    else:
        rest_of_text = text
    match =weapon["variants"] re.search(r'):
        cd = duel.get_attacker().attack_cooldowns.get(i@(\w+, 0))|(-?\d+)', rest_of_text)
   
        if cd > 0:
            text = f"⏳ {i + if match:
 1}. {        val = match.group(1) or match.group(2)
       v.name} (КД: {cd}р)" if val.lstrip
            buttons.append('-').isdigit():
            row = db.fetch_one("SELECT user_id FROM((text, f"duel: players WHERE user_idvariant_disabled:{i=? AND banned=}", "primary"))
        else:
            effect_text0", (int(val),))
 = f" [{v.effect}]"            if row:
                return row["user_id"], if v.effect else None
        else:
            ""
            text = f"{i + 1}. {v.name} · x{v.damage_mult}{effect_text}"
            row = db.fetch_one(
                """SELECT user_id FROM players
                   WHERE (LOWER buttons.append((text, f"duel:variant:{i}", "success"))
    return(username)=LOWER(?) OR LOWER(name)=LOWER(?)) AND banned=0 LIMIT 1""", build_vertical_keyboard_with
                (val_styles(buttons)


def get_attack_zone_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора зоны атаки."""
, val)
            )
            if row:
                return row["user_id"], None
    if m.chat.type == "private":
        return None, f"Укажи цель: ответь    return build_vertical на сообщение или напи_keyboard_with_styles([
        (f"{E_ZONE_HEAD} Голова ×1.5", "duel:ши <code>{atk:head",command_word} @ "danger"),
        (f"{user</code> / <code>{E_ZONE_TORScommand_word} IDO} Торс ×1.0", "duel:atk:torso", "danger"),
        (f"{E_ZONE_ARMS} Руки ×0.8", "duel:atk:arms", "danger"),
        (f"{E_ZONE_LEGS} Ноги ×0.9", "duel:atk:legs", "danger</code>"
    return None, f"⚠️ В группе команда работает <b>ответом</b> или через <code>@username</code> / <code>ID</code>."


# ==============================================================================
# 15. МЕНЮ И КЛАВИАТУРЫ
# ==============================================================================

BTN_ARENA = ""),
    ])


def get_defend_zone_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора⚔️ Арена"
BTN_CASINO = "🎰 Казино"
BTN_GEAR = " зоны защиты."""
🎒 Снаряжение"
BTN_TOP = "🏆 Топ"
MENU_TEXTS = {BTN_ARENA, BTN_CASINO, BTN_GEAR, BTN    return build_vertical_keyboard_with_styles([
        (f"{E_ZONE_HEAD} Голова", "duel:def:head", "success"),
        (f"{E_ZONE_TORSO} Торс",_TOP}

MENU_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_A "duel:defRENA), Keyboard:torso", "success"),
        (f"{E_ZONE_ARMS} Руки", "duel:def:arms", "success"),
        (f"{EButton(text=BTN_CASINO)],
        [KeyboardButton(text=BTN_GEAR), Keyboard_ZONE_LEGS} Ноги", "duel:def:legs", "success"),
    ])


def get_finish_duel_kb() -> InlineKeyboardMarkup:
    """Клавиатура окончания боя."""
   Button(text=BTN_TOP)],
    ],
    resize_keyboard=True,
)


# ================================================================= return build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "duel:again", "primary"),
        ("🏠 В главное меню", "arena:menu", "success"),
    ])


def get_challenge_accept_kb(challenger_id: int, target_id: int)=============
# 16. ГЕНЕРАТО -> InlineKeyboardMarkup:
    """Клавиатура принятия вызова."""
РЫ UI
#    return build_vertical_keyboard_with_styles([
        (f"{E_ACCEPT} Принять вызов ==============================================================================

def generate_arena_menu_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Генерирует меню арены.
    
    ВАЖНО: Кнопка "Мой профиль" убрана — теперь используется отдельная команда /profile.
    """
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?",", f"challenge:accept:{challenger_id}:{target_id}", "success"),
        (f"{E_REJECT} Отклонить", f"challenge:reject:{challenger_id}:{target_id}", "danger"),
    ])


def get_challenge_waiting_kb(challenger_id: int, target_id: int (uid,))) -> InlineKeyboard
    if not p:
        return "Профиль не найден.", None
    a = ARENAS[determine_arena(p["wins"])]
    text = (
        f"╔══════════════════════════╗\n      ⚔️ <b>АРЕНА ДУЭЛЯНТОВ</b>\n╚══════════════════════════╝\n\n"
        f"{E_TROPHY} Победы: <b>{p['wins']}</b>\n"
        f"{E_SKULL} Поражения: {p['losses']}\n"
        f"{EMarkup:
    """Клавиатура ожидания ответа."""
    return build_vertical_keyboard_with_styles([
        (f"{E_REFRESH} Обновить статус", f"challenge:refresh:{challenger_id}:{target_id}", "primary"),
        (f"{E_REJECT} Отменить выз_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>\n"ов", f"challenge:cancel:{challenger_id}:{target_id}",
        f" "danger"),
    ])


def📍 {a['emoji']} get_bet_kb(game <b>{a: str) ->['name']}</b>\n\n"
        f"🥉 Б InlineKeyboardMarkup:
    """Клавиатура выбора ставки."""
    buttons = [(f"{b} 💎ронза — 0–9 поб", f"casinoед · <b>{ARENAS['bronze']['prize']} {E_CRYSTAL}</b>\n"
        f"🥈 Серебро — 10–29 побед · <b>{ARENAS['silver']['prize']} {E_CRYSTAL}</b>\n"
        f"🥇 Золото — 30+ побед · <b>{ARENAS['gold']['prize']} {E_CRYSTAL}</b>"
    )
    kb = build_vertical_keyboard_with_styles([
        ("🎲 Найти соперника", "arena:find", "success"),
        ("👹 Боссы", "arena:bosses", "danger"),
        ("📋 Список соперников", "arena:list", "primary"),
        ("🔎 Вызвать по нику", "arena:find_name", "primary"),
        ("🏆 Топ арен", "top:cur", "primary"),
    ])
    return text, kb


def generate_bosses_menu_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует меню боссов."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
    lines = ["╔══════════════════════════╗\n      👹 <b>БОССЫ АРЕНЫ</b>\n╚══════════════════════════╝\n"]
    buttons = []
    for bkey, b in BOSSES.items():
        locked = p["wins"] < b["min_wins"]
        lock_text = f"🔒 нужен {b['min_wins']} {E_TROPHY}" if locked else f"награда ×{b['reward_mult']}"
        lines.append(f"{b['name']}\n  ❤️ HP {b['hp']} · ⚔️ {WEAPONS[b['weapon']]['name']}\n  {b['desc']}\n  → {lock_text}\n")
        buttons.append((b["name"] if not locked else f"{b['name']} 🔒", f"arena:boss:{bkey}", "danger" if not locked else "primary"))
:{game}:bet:{b}", "    buttons.append((f"{E_BACK} Назад", "arena:menuprimary") for b", "success"))
    return "\n".join(lines), build_vertical_keyboard in Config.CAS_with_styles(buttons)


def generate_gear_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Генерирует экран снаряжения.
    
    ВАЖНО: Кнопка "Мой профиль" убрана — теперь используется отдельная команда /profile.
    """
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
    w = WEAPONS[p["weapon"]]
    f = create_fighter_from_db(p)
    slots = get_player_armor_slots(p)
    lines = [
        f"🎒 <b>{esc(p['name'])}</b>", "",
        f"{E_TROPHY} Победы: <b>{p['wins']}</b>",
        f"{E_SKULL} Поражения: {p['lossINO_BETS]es']}",
        f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>",
        f"📍 {ARENAS[determine_arena(p['wins'])]['emoji']} {ARENAS[determine_arena(p['wins'])]['name']}", "",
        f"❤️ HP: <b>{f.max_hp}</b>",
        f"⚔️ Атака: <b>{f.base_weapon_dmg}</b>", "",
        "<b>⚔️ Оружие:</b>",
        f"  {w['emoji']} {w['name']} — <i>{w['description']}</i>",
        f"  Базовый урон: <b>{w['base_dmg']}</b>", "",
        "<b>🛡 Броня по слотам:</b>"
    ]
    for slot in ZONES
    buttons.append:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"  {ZONE_INFO[slot]['emoji']} {ZONE_INFO[slot]['name']}: {item['emoji']} <b>{item['name']}</b> (защита {item['df']})")
    kb = build_vertical_keyboard_with_styles([
        ("⚔️ Оружие", "gear:w", "primary"),
        ("🛡 Броня", "gear:armor_menu", "primary"),
    ])
    return "\n".join(lines), kb


def generate_weapon_list(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует список оружия."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
    equipped = p["weapon"]
    owned = set((p["weapons_owned"] or "").split(","))
    lines = ["⚔️ <b>Оружие</b>", f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>", ""]
    buttons = []
    for key, it in WEAPONS.items():
        lines.append(f"{it['emoji']} <b>{it['name']}</b> — <i>{it['description']}</i>")
        lines.append(f"  Базовый урон: {it['base_dmg']} · Цена: {it['price']}💎")
        lines.append("  Варианты атаки:")
        for i, v in enumerate(it["variants"]):
            effect_text = f" [{v.effect}]" if v.effect else ""
            lines.append(f"    {i+1}. {v.name} ×{v.damage_mult}{effect_text}((f"{E (КД: {v.cooldown_rounds})")
        lines.append("")
        if key == equipped:
            label = "✅ надето"
            style = "success"
        elif key in owned:
            label = "🎒 надеть"
            style = "primary"
        else:
            label = f"{it['price']}💎"
            style = "danger"
        buttons.append((f"{it['emoji']} {it['name']} · {label}", f"buy_weapon:{key}", style))
    buttons.append((f"{E_BACK} Назад", "gear:menu", "success"))
    return "\n".join(lines), build_vertical_keyboard_with_styles(buttons)


def generate_armor_slot_menu(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует меню слотов брони."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
_BACK} Назад    if not p:
        return "Профиль не найден.", None
    slots = get_player_armor_slots(p)
    lines = ["🛡 <b>Броня — выбери часть тела</b>", f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>", ""]
    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"{ZONE_INFO[slot]['emoji']} <b>{ZONE_INFO[slot]['name']}</b> — {item['emoji']} {item['name']} (защита {item['df']})")
    kb = build_vertical_keyboard_with_styles([
        ("🧠 Голова",", "casino: "gear:head", "primary"),
        ("🫀 Торс", "gear:torso", "primary"),
        ("💪 Руки", "gear:arms", "primary"),
        ("🦵 Ноги", "gear:legs", "primary"),
        (f"{E_BACK} Назад", "gear:menu", "success"),
    ])
    return "\n".join(lines), kb


def generate_armor_slot_list(uid: int, slot: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует список брони для слота."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p or slot not in ZONES:
        return "Ошибка.", None
    slots = get_player_armor_slots(p)
    equipped = slots.get(slot, f"{slot}_none")
    owned = set((p["armors_owned"] or "").split(","))
    lines = [f"🛡 <b>Броня на {ZONE_INFO[slot]['name'].lower()}</b>", f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>", ""]
    buttons = []
    for item in ARMOR_DATA[slot]:
        key = item["key"]
        lines.append(f"{item['emoji']} <b>{item['name']}</b> — защита <b>{item['df']}</b>, HP +{item['hp']}")
        lines.append(f"    {item['desc']}")
        if key == equipped:
            label = "✅ надето"
            style = "success"
        elif key in ownedmenu", "success:
            label = "🎒 надеть"
            style = "primary"
        else:
            label = f"{item['price']}💎"
            style = "danger"
        buttons.append((f"{item['emoji']} {item['name']} · {label}", f"buy_armor:{slot}:{key}", style))
    buttons.append((f"{E_BACK} К слотам", "gear:armor_menu", "success"))
    return "\n".join(lines), build_vertical_keyboard_with_styles(buttons)


def generate_top_screen(uid: int, arena_key: str) -> Tuple[str, Optional[Inline"))
    returnKeyboardMarkup]]:
    """Генерирует экран топа."""
    a = ARENAS[arena_key]
    rows = db.fetch_all(
        """SELECT user_id, name, wins, losses FROM players
           WHERE is_bot=0 AND banned=0 AND wins BETWEEN ? AND ?
           ORDER BY wins DESC, losses ASC LIMIT ?""",
        (a["min_wins"], a["max_wins"], Config.TOP_LEADERBOARD_SIZE)
    )
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"{a['emoji']} <b>{a['name']}</b> — топ по победам", ""]
    if not rows:
        lines.append("<i>Пока никого нет на этой арене.</i>")
    for i, r in enumerate(rows):
        mark = medals[i] if i < 3 else f"{i + 1}."
        you = " ← ты" build_vertical_keyboard_with if r["user_id"] == uid else ""
        lines.append(f"{mark} <b>{esc(r['name'])}</b> — {r['wins']} {E_TROPHY} / {r['losses']} {E_SKULL}{you}")
    me = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if me and all(r["user_id"] != uid for r in rows) and a["min_wins"] <= me["wins"] <= a["max_wins"]:
        rank_row = db.fetch_one(
            """SELECT COUNT(*) c FROM players
               WHERE is_bot=0 AND banned=0 AND wins BETWEEN ? AND ? AND wins > ?""",
            (a["min_wins"], a["max_wins"], me["wins"])
        )
        rank = (rank_row["c"] if rank_row else 0) + 1
        lines += ["…", f"{rank}. <b>{esc(me['name'])}</b> — {me['wins']} {E_TRO_styles(buttons)PHY} / {me['losses']} {E_SKULL} ← ты"]
    lines += ["", f"{E_TROPHY} Победа: +1 и деньги. {E_SKULL} Поражение: −1 без награды."]
    kb = build_vertical_keyboard_with_styles([
        ("🥉 Бронза", "top:bronze", "danger"),
        ("🥈 Серебро", "top:silver", "primary"),
        ("🥇 Золото", "top:gold", "success"),
        (f"{E_BACK} Назад", "arena:menu", "success"),
    ])
    return "\n".join(lines), kb


def generate_arena_list_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует список соперников."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,


def get_d))
    if not p:
        return "Профиль не найден.", None
    key = determine_arena(p["wins"])
    a = ARENAS[key]
    rows = db.fetch_all(
        """SELECT user_id, name, wins, losses FROM players
           WHERE user_id != ? AND banned=0 AND wins BETWEEN ? AND ?
           ORDER BY RANDOM() LIMIT 8""",
        (uid, a["min_wins"], a["max_wins"])
    )
    if not rows:
        return (
            "Сейчас на твоей арене никого нет — жми «Найти соперника».",
            build_vertical_keyboard_with_styles([
                ("🎲 Найти", "arena:find", "success"),
                (f"{E_BACK} Назад", "arena:menu", "primary"),
            ])
        )
    buttons = []
    for r in rows:
        buttons.append((f"{r['name'][:16]} · {r['wins']}{E_TROPHY}/{r['losses']}{E_SKULL}", f"duel:pick:{r['user_id']}", "primary"))
    buttons.append((f"{E_BACK} Назад", "arena:arts_mode_kb()menu", "success"))
    return f"{a['emoji']} <b>{a['name']}</b> — соперники:", build_vertical_keyboard_with_styles(buttons)


def generate_profile_text(row: sqlite3.Row) -> str:
    """Генерирует текст профиля."""
    if not row:
        return "Профиль не найден."
    w = WEAPONS[row["weapon"]] if row["weapon"] in WEAPONS else WEAPONS["fists"]
    f = create_fighter_from_db(row)
    slots = get_player_armor_slots(row)
    arena = ARENAS[determine_arena(row["wins"])]
    auto_accept = "✅ ВКЛ" if row.get("auto_accept", 0) else "❌ ВЫКЛ"
    lines = [
        f"👤 <b>{esc(row['name'])}</b>", "",
        f"{E_TROPHY} Победы: {row['wins']}",
        f"{E_SKULL} Поражения: {row['losses']}",
        f"{E_CRYSTAL} Кристаллы: {format_number(row['crystals'])}",
        f"📍 {arena['emoji']} {arena['name']}", "",
        f"❤️ HP: <b>{f.max_hp}</b>",
        f"{w['emoji']} {w['name']} — баз. урон <b>{w['base_dmg']}</b>", "",
        f" -> InlineKeyboardMarkup⚡ Авто-приём вызовов: <b>{auto_accept}</b>", "",
        "<b>🛡 Броня:</b>"
    ]
    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"  {ZONE_INFO[slot]['emoji']} {ZONE_INFO[slot]['name']}: {item['emoji']} {item['name']} ({item['df']})")
    return "\n".join(lines)


def generate_profile_kb(uid: int) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру профиля.
    
    Содержит кнопки: Снаряжение, Настройки, Назад.
    """
    return build_vertical_keyboard_with_styles([
        ("🎒 Снаряжение", "gear:menu", "primary"),
        (f"{E_SETTINGS} Настройки", "profile:settings", "primary"),
        (f"{E_BACK} Назад", "arena:menu", "success"),
    ])


def generate_settings_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует экран настроек."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
    auto_accept = bool(p.get("auto_accept", :
    """0))
    status = "✅ ВКЛЮЧЕНО" if auto_accept else "❌ ОТКЛЮЧЕНО"
    text = (
        f"{E_SETTINGS} <b>НАСТРОЙКИ</b>\n\n"
        f"👤 <b>{esc(p['name'])}</b>\n\n"
        f"⚡ <b>Авто-приём вызовов:</b>\n"
        f"{status}\n\n"
        f"<i>Если включено, то при вызове на дуэль бой начинается сразу, "
        f"без ожидания подтверждения.</i>"
    )
    kb = build_vertical_keyboard_with_styles([
        (f"{'🔴 Отключить' if auto_accept else '🟢 Включить'} авто-приём", "settings:toggle_auto_accept", "danger" if auto_accept else "successКлавиатура режим"),
        (f"{E_BACK} Назад к профилю", "profile:back", "primary"),
    ])
    return text, kb


def generate_duel_status_text(duel: Duel, for_uid: int, extra: str = "", timer_left: Optional[int] = None) -> str:
    """Генерирует статус боя."""
    role = duel.get_state_for(for_uid)
    me = duel.get_fighter(for_uid) or duel.a
    opp = duel.get_opponent(for_uid) or duel.b
    if role == "attacker" and duel.chosen_variant_idx is None:
        prompt = "🎯 <b>Твой ход</b> — выбери вариант атаки"
    elif role == "attacker":
        prompt = "🎯 <b>Твой ход</b> — выбери зонуов дротика удара"
    elif role == "defender":
        prompt = f"{E_SHIELD} <b>{duel.get_attacker().name}</b> атакует — выбери, что защищать"
    else:
        prompt = "⏳ Бой идёт…"
    if timer_left is not None and role in ("attacker", "defender"):
        prompt += f"\n⏱ Осталось: <b>{timer_left} сек</b>"
    body = "\n".join(f"  {ln}" for ln in duel.log[-DUEL_LOG_DISPLAY_LIMIT:]) if duel.log else "  <i>Бой начинается…</i>"
    boss_line = f"{E_BOSS} <b>БОЙ С БОССОМ</b>  ·  награда ×{duel.reward_mult}\n\n" if duel.is_boss else ""
    return (
        f"╔══════════════════════════╗\n      ⚔️ <b>РАУНД {duel.round_no}</b>\n╚══════════════════════════╝\n\n"
        f"{boss_line}┌─ 🔵 <b>ТЫ</b>\n{format."""
    return_fighter_card(me)}\n└────────────\n\n"
        f"┌─ 🔴 <b>СОПЕРНИК</b>\n{format_fighter_card(opp)}\n└────────────\n\n"
        f"📜 <b>Последние действия:</b>\n{body}\n\n━━━━━━━━━━━━━━━━━━━━\n{prompt}"
        + (f"\n\n{extra}" if extra else "")
    )


def get_attack_variant_kb(uid: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора варианта атаки."""
    duel = ACTIVE_DUELS.get(uid)
    if not duel:
        return build_vertical_keyboard([])
    weapon = WEAPONS[duel.get_attacker().weapon]
    buttons = []
    for i, v in enumerate(weapon["variants"]):
        cd = duel.get_attacker().attack_cooldowns.get(i, 0)
        if cd > 0:
            text = f"⏳ {i + 1}. {v.name} (КД: {cd}р)"
            buttons.append((text, f"duel:variant_disabled:{i build_vertical_keyboard_with}", "primary"))
        else:
            effect_text = f" [{v.effect}]" if v.effect else ""
            text = f"{i + 1}. {v.name} · x{v.damage_mult}{effect_text}"
            buttons.append((text, f"duel:variant:{i}", "success"))
    return build_vertical_keyboard_with_styles(buttons)


def get_attack_zone_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора зоны атаки."""
    return build_vertical_keyboard_with_styles([
        (f"{E_ZONE_HEAD} Голова ×1.5", "duel:atk:head", "danger"),
        (f"{E_ZONE_TORSO} Торс ×1.0", "duel:atk:torso", "danger"),
        (f"{E_ZONE_ARMS} Руки ×0.8", "duel:atk:arms", "danger"),
        (f"{E_ZONE_LEGS} Ноги ×0.9", "duel:atk:legs", "danger"),
    ])


def get_defend_zone_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора зоны защиты."""
    return build_vertical_keyboard_with_styles([
        (f"{E_ZONE_HEAD} Голова", "duel:def:head", "success"),
        (f"{E_ZONE_TORSO} Торс", "duel:def:torso", "success"),
        (f"{E_ZONE_ARMS} Руки", "duel:def_styles([
       :arms", "success"),
        (f"{E_ZONE_LEGS} Ноги", "duel:def:legs", "success"),
    ])


def get_finish_duel_kb() -> InlineKeyboardMarkup:
    """Клавиатура окончания боя."""
    return build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "duel:again", "primary"),
        ("🏠 В главное меню", "arena:menu", "success"),
    ])


def get_challenge_accept_kb(challenger_id: int, target_id: int) -> InlineKeyboardMarkup:
    """Клавиатура принятия вызова."""
    return build_vertical_keyboard_with_styles([
        (f"{E_ACCEPT} Принять вызов", f"challenge:accept:{challenger_id}:{target_id}", "success"),
        (f"{E_REJECT} Отклонить", f"challenge:reject:{challenger_id}:{target_id}", "danger"),
    ])


def get_challenge_waiting_kb(challenger_id: int, target_id: int) -> InlineKeyboardMarkup:
    """Клавиатура ожидания ответа."""
    return build_vertical_keyboard_with_styles([
        (f"{E_REFRESH} Обновить статус", f"challenge:refresh:{challenger_id}:{target_id}", "primary"),
        (f"{E_REJECT ("🎯} Отменить вызов", f"challenge:cancel:{challenger_id}:{target_id}", "danger"),
    ])


def get_bet_kb(game: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора ставки."""
    buttons = [(f"{b} 💎", f"casino:{game}:bet:{b}", "primary") for b in Config.CASINO_BETS]
    buttons.append((f"{E_BACK} Назад", "casino:menu", "success"))
    return build_vertical_keyboard_with_styles(buttons)


def get_darts_mode_kb() На попадание (×1.9)", "casino:d -> InlineKeyboardMarkup:
    """Клавиатура режимов дротика."""
    return build_vertical_keyboard_with_styles([
        ("🎯 На попадание (×1.9)", "casino:darts:hit",arts:hit", "success"),
 "success"),
        ("💨        ("💨 На промах ( На промах (×1.9×1.9)", "casino:d)", "casino:darts:miss",arts:miss", "danger"),
 "danger"),
        (f"{        (f"{E_BACK} НаE_BACK} Назад", "casinoзад", "casino:menu", ":menu", "success"),
   success"),
    ])


def get ])


def get_basket_mode_kb_basket_mode_kb() -> InlineKeyboard() -> InlineKeyboardMarkup:
   Markup:
    """Клавиатура """Клавиатура режимов баскет режимов баскетбола."""
бола."""
    return build_vertical    return build_vertical_keyboard_with_styles([_keyboard_with_styles([
        ("
        ("🏀 На попа🏀 На попадание (×1дание (×1.9)", ".9)", "casino:basket:casino:basket:hit", "successhit", "success"),
        (""),
        ("💨 На промах (×💨 На промах (×1.9)",1.9)", "casino:basket "casino:basket:miss", ":miss", "danger"),
       danger"),
        (f"{E (f"{E_BACK} Назад_BACK} Назад", "casino:", "casino:menu", "successmenu", "success"),
    ])"),
    ])


def get_dice


def get_dice_mode_kb() ->_mode_kb() -> InlineKeyboardMarkup: InlineKeyboardMarkup:
    """Кла
    """Клавиатура режимоввиатура режимов костей."""
 костей."""
    return build_vertical    return build_vertical_keyboard_with_styles([_keyboard_with_styles([
        ("
        ("🔢 На число🔢 На число (×6)", (×6)", "casino:dice "casino:dice:number", "primary:number", "primary"),
        (""),
        ("⚖️⚖️ Чёт / Н Чёт / Нечет (×ечет (×2)", "casino2)", "casino:dice:even:dice:even_odd", "primary_odd", "primary"),
        (""),
        ("📈 Больше📈 Больше / Меньше / Меньше (×2)", (×2)", "casino:dice "casino:dice:high_low",:high_low", "primary"),
 "primary"),
        (f"{        (f"{E_BACK} НаE_BACK} Назад", "casinoзад", "casino:menu", ":menu", "success"),
   success"),
    ])


def get ])


def get_dice_number_kb(b_dice_number_kb(bet: int)et: int) -> InlineKeyboardMarkup -> InlineKeyboardMarkup:
    """:
    """Клавиатура выбораКлавиатура выбора числа для костей.""" числа для костей."""
    buttons =
    buttons = [(f"{i [(f"{i} (×6} (×6)", f"casino)", f"casino:dice:num:{:dice:num:{bet}:{i}",bet}:{i}", "primary") for "primary") for i in range( i in range(1, 71, 7)]
    buttons)]
    buttons.append((f"{E_BACK} На.append((f"{E_BACK} Назад", "casinoзад", "casino:dice", ":dice", "success"))
    return build_vertical_keyboardsuccess"))
    return build_vertical_keyboard_with_styles(buttons)


def get_dice_even_odd_kb(bet: int_with_styles(buttons)


def get_dice_even_odd_kb(bet: int) -> InlineKeyboard) -> InlineKeyboardMarkup:
    """Клавиатура чёт/нMarkup:
    """Клавиатура чёт/нечет для костейечет для костей."""
    return build_vertical_keyboard_with_styles([
       ."""
    return build_vertical_keyboard_with_styles([
        ("🔵 ("🔵 Чёт (× Чёт (×2)", f"2)", f"casino:dice:casino:dice:even:{bet}",even:{bet}", "primary"),
        ("🔴 Нечет (×2)", "primary"),
        ("🔴 Нечет (×2)", f"casino:d f"casino:dice:odd:{ice:odd:{bet}", "dangerbet}", "danger"),
        ("),
        (f"{E_BACKf"{E_BACK} Назад",} Назад", "casino:dice "casino:dice", "success"),
    ])


", "success"),
    ])


def get_dice_highdef get_dice_high_low_kb(bet: int) ->_low_kb(bet: int) -> InlineKeyboardMarkup: InlineKeyboardMarkup:
    """Клавиатура больше/
    """Клавиатура больше/меньше для костейменьше для костей."""
    return."""
    return build_vertical_keyboard_with build_vertical_keyboard_with_styles([
       _styles([
        ("📈 ("📈 Больше (4- Больше (4-6) (×6) (×2)", f"2)", f"casino:dice:casino:dice:high:{bet}", "success"),
high:{bet}", "success"),
        ("        ("📉 Меньше📉 Меньше (1-3 (1-3) (×2)", f"casino) (×2:dice:low)", f"casino:dice:low:{bet}", ":{bet}", "danger"),
       danger"),
        (f"{E (f"{E_BACK} Назад_BACK} Назад", "casino:dice", "success"),
    ])


def get_", "casino:dice", "success"),
    ])


def get_roulette_mode_kb()roulette_mode_kb() -> InlineKeyboardMarkup -> InlineKeyboardMarkup:
    """:
    """Клавиатура режимКлавиатура режимов рулеткиов рулетки."""
    return."""
    return build_vertical_keyboard_with build_vertical_keyboard_with_styles([
       _styles([
        ("🎨 ("🎨 На цвет (× На цвет (×2 / ×14)", "casino:roulette:color", "primary"),
        ("⚖️ Чёт / Нечет (×2)", "casino:roulette:even_odd", "primary"),
        ("📈 Половина (×2)", "casino:roulette:half", "primary"),
        ("🔢 На число (×36)", "casino:roulette:number", "danger"),
        ("🎯 На дюжину (×3)", "casino:roulette:dozen", "primary2 / ×14)", "casino:roulette:color", "primary"),
        ("⚖️ Чёт / Нечет (×2)", "casino:roulette:even_odd", "primary"),
        ("📈 Половина (×2)", "casino:roulette:half", "primary"),
        ("🔢 На число (×36)", "casino:roulette:number", "danger"),
        ("🎯 На дюжину (×3)", "casino:roulette:dozen", "primary"),
        ("),
        (f"{E_BACKf"{E_BACK} Назад", "casino:menu} Назад", "casino:menu", "success"),", "success"),
    ])



    ])


def get_roulettedef get_roulette_color_kb(bet_color_kb(bet: int) ->: int) -> InlineKeyboardMarkup: InlineKeyboardMarkup:
    """Клавиатура выбора цвета
    """Клавиатура выбора цвета рулетки.""" рулетки."""
    return build
    return build_vertical_keyboard_with_styles([
        ("🔴 Красное (×2)", f"casino:roulette:color:red:{bet}", "danger"),
_vertical_keyboard_with_styles([
        ("🔴 Красное (×2)", f"casino:roulette:color:red:{bet}", "danger"),
        ("        ("⚫ Чёрное⚫ Чёрное (×2)", (×2)", f"casino: f"casino:roulette:color:blackroulette:color:black:{bet}", ":{bet}", "primary"),
       primary"),
        ("🟢 ("🟢 Зеро ( Зеро (×14)",×14)", f"casino: f"casino:roulette:color:green:{bet}", "success"),
        (f"{E_BACK} Назад", "casino:roulette:color:green:{bet}", "success"),
        (f"{E_BACK} Назад", "casino:roulette", "successroulette", "success"),
    ])


def get_"),
    ])roulette_even_odd_kb


def get_roulette_even_odd_kb(bet: int(bet: int) -> InlineKeyboard) -> InlineKeyboardMarkup:
   Markup:
    """Клавиатура """Клавиатура чёт/н чёт/нечет рулетечет рулетки."""
ки."""
    return build_vertical    return build_vertical_keyboard_with_styles([_keyboard_with_styles([
        ("
        ("🔵 Чёт🔵 Чёт (×2)", (×2)", f"casino:roulette:even_odd:even:{bet f"casino:}", "primary"),roulette:even_odd:even:{bet}", "primary"),
        ("🔴 Неч
        ("🔴 Нечет (×2)", f"casinoет (×2)", f"casino:roulette:even:roulette:even_odd:odd:{_odd:odd:{bet}", "dangerbet}", "danger"),
        ("),
        (f"{E_BACKf"{E_BACK} Назад",} Назад", "casino:roulette "casino:roulette", "success"),", "success"),
    ])



    ])


def get_roulettedef get_roulette_half_kb(bet_half_kb(bet: int) ->: int) -> InlineKeyboardMarkup: InlineKeyboardMarkup:
    """Клавиатура половины ру
    """Клавиатура половины рулетки."""
летки."""
    return build_vertical    return build_vertical_keyboard_with_styles([_keyboard_with_styles([
        ("
        ("📉 1📉 1-18 (-18 (×2)", f×2)", f"casino:roulette"casino:roulette:half:low:half:low:{bet}", ":{bet}", "primary"),
       primary"),
        ("📈 ("📈 19- 19-36 (×36 (×2)", f"2)", f"casino:roulette:casino:roulette:half:high:{half:high:{bet}", "successbet}", "success"),
        ("),
        (f"{E_BACKf"{E_BACK} Назад",} Назад", "casino:roulette "casino:roulette", "success"),", "success"),
    ])



    ])


def get_roulettedef get_roulette_number_kb(bet_number_kb(bet: int) ->: int) -> InlineKeyboardMarkup: InlineKeyboardMarkup:
    """Кла
    """Клавиатура выбора числавиатура выбора числа рулетки.""" рулетки."""
    buttons =
    buttons = []
    for []
    for i in range( i in range(0, 30, 37):
       7):
        buttons.append((f buttons.append((f"{i} ("{i} (×36)",×36)", f"casino: f"casino:roulette:num:{betroulette:num:{bet}:{i}", "}:{i}", "danger"))
   danger"))
    buttons.append((f buttons.append((f"{E_BACK}"{E_BACK} Назад", " Назад", "casino:roulette",casino:roulette", "success"))
 "success"))
    return build_horizontal    return build_horizontal_keyboard([(t,_keyboard([(t, c) for t c) for t, c, _, c, _ in buttons],  in buttons], 3)


def3)


def get_roulette_do get_roulette_dozen_kb(betzen_kb(bet: int) ->: int) -> InlineKeyboardMarkup: InlineKeyboardMarkup:
    """Кла
    """Клавиатура выбора дювиатура выбора дюжины рулетжины рулетки."""
   ки."""
    return build_vertical_keyboard return build_vertical_keyboard_with_styles([
_with_styles([
        ("1️        ("1️⃣ 1-12 (×3)", f"casino:⃣ 1-12 (×3)", f"casino:roulette:dozenroulette:dozen:1:{bet:1:{bet}", "primary"),}", "primary"),
        ("2
        ("2️⃣️⃣ 13- 13-24 (×24 (×3)", f"3)", f"casino:roulette:casino:roulette:dozen:2dozen:2:{bet}", ":{bet}", "primary"),
       primary"),
        ("3️ ("3️⃣ 2⃣ 25-365-36 (×3)", (×3)", f"casino: f"casino:roulette:dozenroulette:dozen:3:{bet:3:{bet}", "primary"),}", "primary"),
        (f
        (f"{E_BACK}"{E_BACK} Назад", " Назад", "casino:roulette",casino:roulette", "success"),
 "success"),
    ])


def    ])


def generate_casino generate_casino_menu(uid: int_menu(uid: int) -> Tuple[str) -> Tuple[str, Optional[Inline, Optional[InlineKeyboardMarkup]]:KeyboardMarkup]]:
    """Г
    """Генерирует менюенерирует меню казино."""
 казино."""
    p = db    p = db.fetch_one("SELECT.fetch_one("SELECT crystals FROM players WHERE crystals FROM players WHERE user_id=?", ( user_id=?", (uid,))
uid,))
    if not p    if not p:
        return:
        return "Профиль не "Профиль не найден.", None найден.", None
    text =
    text = (
        f (
        f"╔════"╔══════════════════════════════════════════╗\══════╗\n     n      {E_SLOT} {E_SLOT} <b>КА <b>КАЗИНО</bЗИНО</b>\n╚>\n╚══════════════════════════════════════════╝══════════╝\n\n\n\n"
        f"
        f"{E_CRY"{E_CRYSTAL} БSTAL} Баланс: <аланс: <b>{format_numberb>{format_number(p['crystals(p['crystals'])}</b>\'])}</b>\n\n"
n\n"
        f"<b        f"<b>Выбери игру>Выбери игру:</b>"
:</b>"
    )
       )
    kb = build_vertical kb = build_vertical_keyboard_with_styles([_keyboard_with_styles([
        (f
        (f"{E_SLOT}"{E_SLOT} Слоты ( Слоты (только комбинациятолько комбинация ×10)", ×10)", "casino:slots "casino:slots", "primary"),", "primary"),
        (f
        (f"{E_DICE"{E_DICE} Кости (} Кости (число/чётчисло/чёт/больше)",/больше)", "casino:dice "casino:dice", "primary"),", "primary"),
        (f
        (f"{E_DART"{E_DARTS} ДротS} Дротик (×1ик (×1.9)", ".9)", "casino:darts",casino:darts", "primary"),
 "primary"),
        (f"{        (f"{E_BASKETE_BASKET} Баскет} Баскетбол (×1бол (×1.9)", ".9)", "casino:basket",casino:basket", "primary"),
 "primary"),
        ("        ("🎡 Рулетка🎡 Рулетка (цвет/чёт (цвет/чёт/число)",/число)", "casino:roulette "casino:roulette", "primary"),", "primary"),
        (f
        (f"{E_COIN"{E_COIN} Монетка (} Монетка (×2)", "×2)", "casino:coin",casino:coin", "primary"),
 "primary"),
        ("        ("📊 Больше/М📊 Больше/Меньше (×еньше (×1.9)",1.9)", "casino:high "casino:highlow", "primarylow", "primary"),
        ("),
        (f"{E_BACKf"{E_BACK} Назад",} Назад", "arena:menu", "success"), "arena:menu", "success"),
    ])

    ])
    return text,    return text, kb


# ==============================================================================
# kb


# ==============================================================================
# 17. 17. HELP С 4 HELP С 4 РАЗДЕЛА РАЗДЕЛАМИ
# =================================================================МИ
# ==============================================================================

HELP_SE=============

HELP_SECTIONS: Dict[strCTIONS: Dict[str, Dict[str,, Dict[str, Any]] = { Any]] = {
    "du
    "duels": {
els": {
        "title":        "title": f"{E_S f"{E_SWORD} <bWORD} <b>⚔>⚔️ ДУЭ️ ДУЭЛИ</b>",ЛИ</b>",
        "text
        "text": (
           ": (
            "• <code "• <code>перчатка>перчатка</code> или</code> или <code>пер <code>перч</code>ч</code> — вызов с — вызов с подтверждением\n" подтверждением\n"
            "•
            "• <code>про <code>профиль</code>филь</code> или <code>/ или <code>/profile</code>profile</code> — статистика\n — статистика\n"
            "• <code"
            "• <code>перевод>перевод [сумма [сумма]</code> —]</code> — перевести кристал перевести кристаллы\n"
лы\n"
            "• <            "• <code>балансcode>баланс</code> —</code> — проверить баланс\n\n проверить баланс\n\n"
            "<"
            "<i>Комi>Команды работают ответанды работают ответом на сообщение илиом на сообщение или через @username / через @username / ID</i>" ID</i>"
       
        ),
    }, ),
    },
    "casino
    "casino": {
       ": {
        "title": f "title": f"{E_SLOT}"{E_SLOT} <b> <b>🎰 КАЗ🎰 КАЗИНО</bИНО</b>",
        ">",
        "text": (
text": (
            "• <            "• <code>сл [code>сл [сумма]</сумма]</code> — слcode> — слоты ×1оты ×10\n"0\n"
            "•
            "• <code>кости <code>кости число [сум число [сумма] [1ма] [1-6]</code-6]</code> — ×6> — ×6\n"
           \n"
            "• <code "• <code>кости чет [>кости чет [сумма]сумма] [чет/н [чет/нечет]</codeечет]</code> — ×2> — ×2\n"
           \n"
            "• <code "• <code>кости больше [>кости больше [сумма]сумма] [больше/ [больше/меньше]</codeменьше]</code> — ×2> — ×2\n"
           \n"
            "• <code "• <code>дротик>дротик [сумма [сумма]</code> —]</code> — ×1.9 ×1.9\n"
           \n"
            "• <code "• <code>дротик>дротик промах [с промах [сумма]</codeумма]</code> — ×1> — ×1.9\n".9\n"
            "•
            "• <code>б <code>баскет [саскет [сумма]</codeумма]</code> — ×1> — ×1.9\n".9\n"
            "•
            "• <code <code>баскет>баскет промах [с промах [сумма]</codeумма]</code> — ×1> — ×1.9\n".9\n"
            "• <code
            "• <code>рул цвет>рул цвет [сумма [сумма] [к/] [к/ч/з]</ч/з]</code>\n"code>\n"
            "•
            "• <code <code>рул чет>рул чет [сумма [сумма] [чет/] [чет/нечет]</нечет]</code>\n"code>\n"
            "• <code
            "• <code>рул половина>рул половина [сумма [сумма] [верх/] [верх/низ]</code>\низ]</code>\n"
           n"
            "• <code "• <code>рул число>рул число [сумма [сумма] [0-] [0-36]</code36]</code> — ×3> — ×36\n"
6\n"
            "• <code            "• <code>рул дю>рул дюжина [сумжина [сумма] [1ма] [1/2/3/2/3]</code> —]</code> — ×3\n" ×3\n"
            "• <code
            "• <code>мон [с>мон [сумма] [умма] [о/р]</о/р]</code>\n"code>\n"
            "•
            "• <code <code>больше [>больше [сумма]</сумма]</code> / <code> / <code>меньшеcode>меньше [сумма [сумма]</code>"
]</code>"
        ),
           ),
    },
    " },
    "rp": {
rp": {
        "title":        "title": f"{E_MAGIC f"{E_MAGIC} <b>} <b>🎭 RP🎭 RP ДЕЙСТВИ ДЕЙСТВИЯ</b>",Я</b>",
        "text
        "text": (
           ": (
            "• <code "• <code>ударить</>ударить</code>, <code>обнять</code>, <code>обнять</code>, <codecode>, <code>поцеловать</code>\>поцеловать</code>\n"
           n"
            "• <code>пнуть</ "• <codecode>, <code>пнуть</code>, <code>погладить</code>,>погладить</code>, <code>у <code>укусить</codeкусить</code>\n"
>\n"
            "• <code>пожать</code>, <code>толкнуть</code>, <code>кинуть</code>\n"
            "• <code>лечить</code>, <code>игнор</code>, <code>смеяться</code>\n"
            "• <code>танцевать</code>, <code>шлепнуть</code>, <code>обозвать</code>\n"
            "• <code>покормить</code>, <code>напоить</code>, <code>щекот            "• <code>пожать</code>, <code>толкнуть</code>, <code>кинуть</code>\n"
            "• <code>лечить</code>, <code>игнор</code>, <code>смеяться</code>\n"
            "• <code>танцевать</code>, <code>шлепнуть</code>, <code>обозвать</code>\n"
            "• <code>покормить</code>, <code>напоить</code>, <codeать</code>\n"
            "• <code>благословить</code>, <code>>щекотать</code>\n"
            "• <code>благословить</code>, <code>проклястьпроклясть</code>, <</code>, <code>подмиcode>подмигнуть</code>\гнуть</code>\n\n"
n\n"
            "<b>            "<b>👹 С👹 События:</bобытия:</b>\n"
>\n"
            "• <            "• <code>атакаcode>атака</code> —</code> — ударить бос ударить босса/каравса/караван\n"
ан\n"
            "• <            "• <code>событиеcode>событие</code> —</code> — статус текущего события\n статус текущего события\n\n"
           \n"
            "<b> "<b>🎟 Пром🎟 Промокоды:</окоды:</b>\n"b>\n"
            "•
            "• <code <code>#код [про>#код [промокод]</codeмокод]</code> — активиров> — активировать\n"
ать\n"
            "• <            "• <code>активcode>активировать [кодировать [код]</code> —]</code> — альтернатив альтернатива"
       а"
        ),
    }, ),
    },
    "admin
    "admin": {
       ": {
        "title": f "title": f"{E_CROWN"{E_CROWN} <b>} <b>👑 АД👑 АДМИН</bМИН</b>",
        ">",
        "text": (
text": (
            "• <            "• <code>бан</code>бан</code> / <code> / <code>разбанcode>разбан</code>\n</code>\n"
            ""
            "• <code• <code>выдать [>выдать [сумма]</сумма]</code>\n"code>\n"
            "•
            "• <code <code>событие б>событие босс/каравосс/караван/набан/набег/драконег/дракон</code>\n</code>\n"
            "• <code"
            "• <code>босс [>босс [ключ]</code>ключ]</code> — активировать — активировать босса\n босса\n"
            ""
            "• <code• <code>следующее>следующее событие</code>\ событие</code>\n"
           n"
            "• <code "• <code>промо создать>промо создать/удалить/удалить/список/список</code>\n</code>\n"
            ""
            "• <code• <code>рассыл>рассылка текст</codeка текст</code>\n"
            "• <>\n"
            "• <code>статcode>статистика</codeистика</code> — статист> — статистика бота\nика бота\n"
            ""
            "• <code• <code>список>список игроков</code> игроков</code> — список всех игроков — список всех игроков\n"
           \n"
            "• <code "• <code>очистить>очистить ботов</code ботов</code> — удалить всех> — удалить всех ботов\n" ботов\n"
            "•
            "• <code <code>добавить>добавить ботов [чис ботов [число]</code>ло]</code> — добавить ботов — добавить ботов"
        ),"
        ),
    },
    },
}


HELP
}


HELP_CHAT_SHORT = (_CHAT_SHORT = (
    f"{
    f"{E_INFO} <E_INFO} <b>КРАb>КРАТКАЯ СПРАВКА</bТКАЯ СПРАВКА</b>\n\n">\n\n"
    f"<
    f"<b>b>⚔️ Дуэ⚔️ Дуэли:</b>\ли:</b>\n"
   n"
    f"• < f"• <code>перчатcode>перчатка</code>ка</code> — вызвать на бой — вызвать на бой\n"
   \n"
    f"• < f"• <code>профильcode>профиль</code> /</code> / <code>/profile <code>/profile</code></code> — статистика — статистика\n"
   \n"
    f"• < f"• <code>балансcode>баланс</code> —</code> — проверить баланс\n\n проверить баланс\n\n"
    f"
    f"<b>"<b>💎 Экономика:</b💎 Экономика:</b>\n"
>\n"
    f"•    f"• <code>пер <code>перевод [севод [сумма]</code> — перевести кристаллы\nумма]</code> — перевести кристаллы\n\n"
   \n"
    f"<b> f"<b>🎰 Ка🎰 Казино:</b>\зино:</b>\n"
   n"
    f"• < f"• <code>сл code>сл 100</100</code> — слcode> — слоты\n"оты\n"
    f"
    f"• <code>• <code>кости число 1кости число 100 300 3</code> —</code> — кости\n"
 кости\n"
    f"•    f"• <code>др <code>дротик 1отик 100</code00</code> — дрот> — дротик\n"
ик\n"
    f"•    f"• <code>б <code>баскет 1аскет 100</00</code> — басcode> — баскетбол\n"кетбол\n"
    f"
    f"• <code>• <code>рул цвет рул цвет 100 к100 к</code> —</code> — рулетка\n рулетка\n"
    f"
    f"• <code"• <code>мон 1>мон 100 о</00 о</code> — монcode> — монетка\n\n"етка\n\n"
    f"<
    f"<b>b>🎭 RP:</b🎭 RP:</b>\n">\n"
    f"
    f"• <code>• <code>ударить</codeударить</code>, <code>>, <code>обнять</codeобнять</code>, <code>>, <code>поцеловатьпоцеловать</code> и</code> и др.\n\n др.\n\n"
    f"
    f"<b>"<b>👹 Собы👹 События:</b>\тия:</b>\n"
   n"
    f"• < f"• <code>атакаcode>атака</code> —</code> — ударить бос ударить босса/каравса/караван\n"
ан\n"
    f"•    f"• <code>собы <code>событие</code>тие</code> — статус события\n — статус события\n\n"
   \n"
    f"{E_INFO f"{E_INFO} <i>} <i>Полная справкаПолная справка в ЛС с в ЛС с ботом: ботом: напиши <code напиши <code>help</code>help</code></i>"
></i>"
)


def get)


def get_help_keyboard() ->_help_keyboard() -> InlineKeyboardMarkup: InlineKeyboardMarkup:
    """С
    """Создаёт клавиоздаёт клавиатуру с атуру с 4 разделами help4 разделами help."""
    return."""
    return build_horizontal_keyboard([ build_horizontal_keyboard([
        (f
        (f"{E_SWORD"{E_SWORD} Дуэли} Дуэли", "help:", "help:section:duelssection:duels"),
        ("),
        (f"{E_SLOTf"{E_SLOT} Казино",} Казино", "help:section "help:section:casino"),
:casino"),
        (f"{        (f"{E_MAGIC} RPE_MAGIC} RP", "help:", "help:section:rp"),section:rp"),
        (f
        (f"{E_CROWN"{E_CROWN} Админ",} Админ", "help:section "help:section:admin"),
:admin"),
    ], 2    ], 2)


# =================================================================)


# ==============================================================================
#=============
# 18. 18. РОУТЕР И РОУТЕР И FSM
# ================================================================= FSM
# ==============================================================================

router ==============

router = Router()


class Router()


class RegistrationState( RegistrationState(StatesGroup):
StatesGroup):
    waiting_for_name    waiting_for_name = State()


 = State()


class DuelFindStateclass DuelFindState(StatesGroup):(StatesGroup):
    waiting_for
    waiting_for_target = State()_target = State()


# ==============================================================================


# ==============================================================================
# 1
# 19. ХЕН9. ХЕНДЛЕРЫДЛЕРЫ СТАРТА И СТАРТА И МЕНЮ
 МЕНЮ
# ==============================================================================

# ==============================================================================

@router.message(Command@router.message(CommandStart())
asyncStart())
async def handle_start_command def handle_start_command(m: Message,(m: Message, state: FSMContext state: FSMContext) -> None:) -> None:
    """Обра
    """Обрабатывает /startбатывает /start."""
   ."""
    await state.clear() await state.clear()
    ensure_mask
    ensure_masked_bots_existed_bots_exist(Config.BOT_GENER(Config.BOT_GENERATION_COUNT)
ATION_COUNT)
    p = db    p = db.fetch_one("SELECT.fetch_one("SELECT * FROM players WHERE * FROM players WHERE user_id=?", ( user_id=?", (m.from_user.idm.from_user.id,))
   ,))
    if p:
 if p:
        db.execute("        db.execute("UPDATE players SET usernameUPDATE players SET username=?, last_active=?=?, last_active=? WHERE user_id=?", WHERE user_id=?",
                   (m
                   (m.from_user.username,.from_user.username, time.time(), m time.time(), m.from_user.id)).from_user.id))
        if m
        if m.chat.type == ".chat.type == "private":
           private":
            await m.answer(f await m.answer(f"С возвращением"С возвращением, <b>{, <b>{esc(p['name'])}</b>esc(p['name'])}</b>! Арена ж! Арена ждёт 👇",дёт 👇",
