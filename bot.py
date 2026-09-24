#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "5356400377"))
    DB_PATH: str = os.getenv("DB_PATH", "arena_ultimate.db")
    START_CRYSTALS: int = 500
    TURN_TIMEOUT: int = 45
    RP_COOLDOWN: int = 5
    TRANSFER_TAX: float = 0.05
    MIN_TRANSFER: int = 10
    MAX_TRANSFER: int = 100000
    CASINO_MIN_BET: int = 10
    CASINO_MAX_BET: int = 50000
    BOT_GENERATION_COUNT: int = 50
    BOT_WIN_DISTRIBUTION: Dict[str, float] = {"bronze": 0.5, "silver": 0.35, "gold": 0.15}
    EVENT_BOSS_BASE_HP: int = 2000
    EVENT_CARAVAN_BASE_HP: int = 1000
    EVENT_RAID_BASE_HP: int = 3000
    EVENT_MIN_DAMAGE: int = 50
    EVENT_MAX_DAMAGE: int = 200
    EVENT_CRIT_CHANCE: float = 0.15
    EVENT_CRIT_MULT: float = 2.5
    EVENT_DEFAULT_DURATION_HOURS: float = 2.0
    PROMO_MIN_CODE_LENGTH: int = 3
    PROMO_MAX_CODE_LENGTH: int = 20
    PROMO_MAX_USES: int = 1000
    PROMO_MAX_HOURS: int = 8760
    TOP_LEADERBOARD_SIZE: int = 20
    CHALLENGE_TIMEOUT: int = 60
    LOG_LEVEL: int = logging.INFO
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


BASE_HP: int = 150
MIN_NAME_LENGTH: int = 2
MAX_NAME_LENGTH: int = 16
DUEL_LOG_LIMIT: int = 10
DUEL_LOG_DISPLAY_LIMIT: int = 5
TELEGRAM_MAX_TEXT_LENGTH: int = 4096
BROADCAST_DELAY: float = 0.05
BOT_NAME_GENERATION_ATTEMPTS: int = 300
MAX_NOTIFICATIONS_PER_USER: int = 15


E_FIRE = "🔥"
E_SWORD = "⚔️"
E_SHIELD = "🛡"
E_HEART = "❤️"
E_SKULL = "💀"
E_TROPHY = "🏆"
E_CRYSTAL = "💎"
E_COIN = "🪙"
E_SLOT = "🎰"
E_DICE = "🎲"
E_GIFT = "🎁"
E_PROMO = "🎟"
E_BOSS = "👹"
E_GLOVE = "🧤"
E_STAR = "⭐"
E_MAGIC = "✨"
E_LIGHTNING = "⚡"
E_METEOR = "☄️"
E_ZONE_HEAD = "🧠"
E_ZONE_TORSO = "🫀"
E_ZONE_ARMS = "💪"
E_ZONE_LEGS = "🦵"
E_DARTS = "🎯"
E_BASKET = "🏀"
E_SETTINGS = "⚙️"
E_BACK = "⬅️"
E_REFRESH = "🔄"
E_ACCEPT = "✅"
E_REJECT = "❌"
E_INFO = "ℹ️"
E_WARNING = "⚠️"
E_CROWN = "👑"
E_RED = "🔴"
E_WHITE = "⚪"
E_YELLOW = "🟡"
E_GREEN = "🟢"
E_BLUE = "🔵"
E_ORANGE = "🟠"


ZONES: List[str] = ["head", "torso", "arms", "legs"]

ZONE_INFO: Dict[str, Dict[str, Any]] = {
    "head": {"name": "Голова", "emoji": E_ZONE_HEAD, "mult": 1.5, "desc": "Высокий урон, сложно попасть"},
    "torso": {"name": "Торс", "emoji": E_ZONE_TORSO, "mult": 1.0, "desc": "Средний урон, стандартная цель"},
    "arms": {"name": "Руки", "emoji": E_ZONE_ARMS, "mult": 0.8, "desc": "Низкий урон, высокая точность"},
    "legs": {"name": "Ноги", "emoji": E_ZONE_LEGS, "mult": 0.9, "desc": "Средний урон, шанс замедлить"},
}


@dataclass
class AttackVariant:
    name: str
    description: str
    damage_mult: float
    armor_penetration: float
    cooldown_rounds: int
    effect: Optional[str] = None


WEAPONS: Dict[str, Dict[str, Any]] = {
    "fists": {
        "emoji": "👊", "name": "Кулаки", "base_dmg": 10, "price": 0,
        "description": "Базовое оружие новичка. Быстрые, но слабые удары.",
        "variants": [
            AttackVariant("Джеб", "Быстрый удар", 0.8, 0.0, 0, None),
            AttackVariant("Серия ударов", "3 удара по 50% урона", 1.5, 0.0, 2, "triple"),
            AttackVariant("Апперкот", "Оглушает при попадании", 1.2, 0.1, 3, "stun"),
        ],
    },
    "dagger": {
        "emoji": "🗡", "name": "Кинжал", "base_dmg": 14, "price": 200,
        "description": "Быстрое оружие убийцы. Высокий шанс критов.",
        "variants": [
            AttackVariant("Укол", "Точный удар, пробивает 20% брони", 1.0, 0.2, 0, None),
            AttackVariant("Рассечение", "Кровотечение на 3 раунда", 1.1, 0.1, 2, "bleed"),
            AttackVariant("Тысяча порезов", "3 удара, игнор 30% брони", 1.4, 0.3, 3, "triple"),
        ],
    },
    "sword": {
        "emoji": E_SWORD, "name": "Меч", "base_dmg": 20, "price": 500,
        "description": "Классическое оружие воина. Сбалансированный урон.",
        "variants": [
            AttackVariant("Размах", "Стандартная атака", 1.0, 0.0, 0, None),
            AttackVariant("Пронзающий выпад", "Игнор 50% защиты", 1.2, 0.5, 2, "pierce"),
            AttackVariant("Казнь", "Двойной урон, легко блокируется", 2.0, 0.0, 4, "exec"),
        ],
    },
    "axe": {
        "emoji": "🪓", "name": "Топор", "base_dmg": 26, "price": 800,
        "description": "Тяжёлое оружие варвара. Огромный урон.",
        "variants": [
            AttackVariant("Рубящий удар", "Тяжелая атака", 1.0, 0.1, 0, None),
            AttackVariant("Кровопускание", "Сильное кровотечение", 1.1, 0.0, 3, "bleed"),
            AttackVariant("Сокрушение", "Огромный урон, долгий КД", 1.8, 0.2, 4, None),
        ],
    },
    "bow": {
        "emoji": "🏹", "name": "Лук", "base_dmg": 32, "price": 1200,
        "description": "Дальнобойное оружие охотника.",
        "variants": [
            AttackVariant("Прицельный выстрел", "Стандартная атака", 1.0, 0.3, 0, None),
            AttackVariant("Залп", "2 выстрела с шансом крита", 1.6, 0.2, 2, "triple"),
            AttackVariant("Бронебойная стрела", "Полный игнор брони", 1.3, 1.0, 3, "pierce"),
        ],
    },
    "staff": {
        "emoji": E_FIRE, "name": "Посох", "base_dmg": 38, "price": 1700,
        "description": "Магическое оружие чародея.",
        "variants": [
            AttackVariant("Магический импульс", "Базовая магия", 1.0, 0.4, 0, None),
            AttackVariant("Огненный шар", "Поджигает на 3 раунда", 1.2, 0.2, 2, "burn"),
            AttackVariant("Метеор", "Массовый урон", 2.2, 0.0, 4, "burn"),
        ],
    },
    "hammer": {
        "emoji": "🔨", "name": "Молот", "base_dmg": 46, "price": 2500,
        "description": "Тяжёлое оружие паладина.",
        "variants": [
            AttackVariant("Удар молотом", "Тяжелая физика", 1.0, 0.3, 0, None),
            AttackVariant("Землетрясение", "Оглушает и наносит урон", 1.3, 0.4, 3, "stun"),
            AttackVariant("Разрушение", "Ломает защиту (60%)", 2.0, 0.6, 5, None),
        ],
    },
}


ARMOR_DATA: Dict[str, List[Dict[str, Any]]] = {
    "head": [
        {"key": "head_none", "name": "Без шлема", "emoji": "👕", "df": 0, "hp": 0, "price": 0, "chance": 0, "dmg_bonus": 0, "desc": "Полная уязвимость"},
        {"key": "head_leather", "name": "Кожаный капюшон", "emoji": "🧢", "df": 2, "hp": 3, "price": 120, "chance": 3, "dmg_bonus": 0, "desc": "+3% шанс спец-атаки"},
        {"key": "head_iron", "name": "Железный шлем", "emoji": "⛑", "df": 4, "hp": 8, "price": 380, "chance": 0, "dmg_bonus": 0, "desc": "Базовая защита"},
        {"key": "head_steel", "name": "Стальной шлем", "emoji": "🪖", "df": 7, "hp": 15, "price": 850, "chance": 0, "dmg_bonus": 10, "desc": "+10% урон спец-атаки"},
        {"key": "head_dragon", "name": "Драконий шлем", "emoji": "🐲", "df": 11, "hp": 25, "price": 1800, "chance": 8, "dmg_bonus": 20, "desc": "+8% шанс, +20% урон"},
        {"key": "head_crown", "name": "Корона Лорда", "emoji": "👑", "df": 14, "hp": 30, "price": 3000, "chance": 12, "dmg_bonus": 25, "desc": "Максимальная защита"},
    ],
    "torso": [
        {"key": "torso_none", "name": "Без брони", "emoji": "👕", "df": 0, "hp": 0, "price": 0, "chance": 0, "dmg_bonus": 0, "desc": "Полная уязвимость"},
        {"key": "torso_robe", "name": "Мантия", "emoji": "🥋", "df": 3, "hp": 5, "price": 150, "chance": 4, "dmg_bonus": 0, "desc": "+4% шанс спец-атаки"},
        {"key": "torso_chain", "name": "Кольчуга", "emoji": E_SHIELD, "df": 6, "hp": 12, "price": 480, "chance": 0, "dmg_bonus": 0, "desc": "Надежная защита"},
        {"key": "torso_plate", "name": "Латный доспех", "emoji": "🏋️", "df": 11, "hp": 22, "price": 1000, "chance": 0, "dmg_bonus": 15, "desc": "+15% урон спец-атаки"},
        {"key": "torso_titan", "name": "Титановый панцирь", "emoji": E_STAR, "df": 17, "hp": 35, "price": 2200, "chance": 10, "dmg_bonus": 25, "desc": "+10% шанс, +25% урон"},
        {"key": "torso_aegis", "name": "Эгида", "emoji": "🌟", "df": 22, "hp": 45, "price": 3500, "chance": 15, "dmg_bonus": 30, "desc": "Легендарная защита"},
    ],
    "arms": [
        {"key": "arms_none", "name": "Без наручей", "emoji": "👕", "df": 0, "hp": 0, "price": 0, "chance": 0, "dmg_bonus": 0, "desc": "Полная уязвимость"},
        {"key": "arms_cloth", "name": "Тканевые бинты", "emoji": "🩹", "df": 2, "hp": 2, "price": 100, "chance": 3, "dmg_bonus": 0, "desc": "+3% шанс спец-атаки"},
        {"key": "arms_iron", "name": "Железные наручи", "emoji": E_SHIELD, "df": 4, "hp": 8, "price": 350, "chance": 0, "dmg_bonus": 0, "desc": "Базовая защита"},
        {"key": "arms_steel", "name": "Стальные латы", "emoji": "⚙️", "df": 7, "hp": 14, "price": 800, "chance": 0, "dmg_bonus": 10, "desc": "+10% урон спец-атаки"},
        {"key": "arms_runic", "name": "Рунические наручи", "emoji": "🔮", "df": 11, "hp": 22, "price": 1700, "chance": 8, "dmg_bonus": 20, "desc": "+8% шанс, +20% урон"},
        {"key": "arms_berserk", "name": "Наручи Берсерка", "emoji": "🩸", "df": 9, "hp": 18, "price": 1500, "chance": 5, "dmg_bonus": 35, "desc": "-2 защиты, +35% урона"},
    ],
    "legs": [
        {"key": "legs_none", "name": "Без поножей", "emoji": "👕", "df": 0, "hp": 0, "price": 0, "chance": 0, "dmg_bonus": 0, "desc": "Полная уязвимость"},
        {"key": "legs_cloth", "name": "Тканевые штаны", "emoji": "👖", "df": 2, "hp": 3, "price": 110, "chance": 3, "dmg_bonus": 0, "desc": "+3% шанс спец-атаки"},
        {"key": "legs_iron", "name": "Железные поножи", "emoji": E_SHIELD, "df": 5, "hp": 10, "price": 400, "chance": 0, "dmg_bonus": 0, "desc": "Базовая защита"},
        {"key": "legs_steel", "name": "Стальные поножи", "emoji": "⚙️", "df": 8, "hp": 16, "price": 900, "chance": 0, "dmg_bonus": 10, "desc": "+10% урон спец-атаки"},
        {"key": "legs_demon", "name": "Демонические поножи", "emoji": "😈", "df": 12, "hp": 25, "price": 1900, "chance": 8, "dmg_bonus": 20, "desc": "+8% шанс, +20% урон"},
        {"key": "legs_wind", "name": "Поножи Ветра", "emoji": E_ZONE_LEGS, "df": 6, "hp": 12, "price": 1100, "chance": 10, "dmg_bonus": 5, "desc": "+10% шанс уворота"},
    ],
}


START_ARMOR_KEYS: List[str] = ["head_none", "torso_none", "arms_none", "legs_none"]
START_WEAPON: str = "fists"
BASE_STATS: Dict[str, int] = {"hp": BASE_HP}


ARENAS: Dict[str, Dict[str, Any]] = {
    "bronze": {"name": "Бронзовая арена", "emoji": "🥉", "min_wins": 0, "max_wins": 9, "prize": 50},
    "silver": {"name": "Серебряная арена", "emoji": "🥈", "min_wins": 10, "max_wins": 29, "prize": 100},
    "gold": {"name": "Золотая арена", "emoji": "🥇", "min_wins": 30, "max_wins": 10**9, "prize": 200},
}
ARENA_ORDER: List[str] = ["bronze", "silver", "gold"]


BOSSES: Dict[str, Dict[str, Any]] = {
    "goblin": {
        "key": "goblin", "name": "👺 Гоблин-Вождь",
        "desc": "Хитрый и злой. Бьёт по слабой броне.",
        "hp": 160, "weapon": "dagger",
        "armor_keys": {"head": "head_leather", "torso": "torso_robe", "arms": "arms_none", "legs": "legs_none"},
        "reward_mult": 3, "min_wins": 0,
    },
    "dragon": {
        "key": "dragon", "name": "🐉 Древний Дракон",
        "desc": "Огнедышащий ужас. Оружие — посох.",
        "hp": 260, "weapon": "staff",
        "armor_keys": {"head": "head_steel", "torso": "torso_plate", "arms": "arms_iron", "legs": "legs_iron"},
        "reward_mult": 5, "min_wins": 5,
    },
    "lord": {
        "key": "lord", "name": "👹 Древний Лорд",
        "desc": "Владыка арены. Молот разрушения.",
        "hp": 380, "weapon": "hammer",
        "armor_keys": {"head": "head_dragon", "torso": "torso_titan", "arms": "arms_runic", "legs": "legs_demon"},
        "reward_mult": 10, "min_wins": 15,
    },
    "titan": {
        "key": "titan", "name": "🗿 Каменный Титан",
        "desc": "Неуязвимая глыба. Огромная защита.",
        "hp": 500, "weapon": "fists",
        "armor_keys": {"head": "head_crown", "torso": "torso_aegis", "arms": "arms_berserk", "legs": "legs_wind"},
        "reward_mult": 15, "min_wins": 35,
    },
    "demon_king": {
        "key": "demon_king", "name": "😈 Король Демонов",
        "desc": "Повелитель преисподней. Смесь всех стихий.",
        "hp": 750, "weapon": "staff",
        "armor_keys": {"head": "head_crown", "torso": "torso_aegis", "arms": "arms_runic", "legs": "legs_demon"},
        "reward_mult": 25, "min_wins": 50,
    },
}


CHAT_EVENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "boss": {
        "name_template": "{emoji} Рейдовый Босс",
        "emoji": E_BOSS,
        "base_hp": 2000,
        "duration_hours": 2.0,
        "reward_per_participant": (50, 150),
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n{emoji} <b>Рейдовый Босс</b> появился в чате!\nHP: {hp}\n\nИспользуйте команду <code>атака</code>!",
    },
    "caravan": {
        "name_template": "🐪 Золотой Караван",
        "emoji": "🐪",
        "base_hp": 1000,
        "duration_hours": 1.0,
        "reward_per_participant": (30, 100),
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n🐪 <b>Золотой Караван</b> проезжает через чат!\nHP: {hp}\n\nИспользуйте команду <code>атака</code>!",
    },
    "raid": {
        "name_template": "⚔️ Набег Орков",
        "emoji": "⚔️",
        "base_hp": 3000,
        "duration_hours": 3.0,
        "reward_per_participant": (80, 200),
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n⚔️ <b>Набег Орков</b> начался!\nHP: {hp}\n\nИспользуйте команду <code>атака</code>!",
    },
    "dragon_raid": {
        "name_template": "🐉 Нашествие Драконов",
        "emoji": "🐉",
        "base_hp": 5000,
        "duration_hours": 4.0,
        "reward_per_participant": (150, 350),
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n🐉 <b>Нашествие Драконов</b> началось!\nHP: {hp}\n\nИспользуйте команду <code>атака</code>!",
    },
}


def esc(text: Any) -> str:
    return html.escape(str(text))


def create_mention(user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{esc(name)}</a>'


def build_colored_vertical_keyboard(
    buttons: List[Tuple[str, str, str]]
) -> InlineKeyboardMarkup:
    """
    Создаёт вертикальную клавиатуру с цветными кнопками.
    buttons: список кортежей (text, callback_data, style)
    style: "primary" (синий), "success" (зелёный), "danger" (красный), "warning" (жёлтый)
    """
    builder = InlineKeyboardBuilder()
    for text, callback_data, style in buttons:
        builder.row(InlineKeyboardButton(text=text, callback_data=callback_data, style=style))
    return builder.as_markup()


def build_colored_grid_keyboard(
    rows: List[List[Tuple[str, str, str]]]
) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру-сетку с цветными кнопками.
    rows: список строк, где каждая строка - список кортежей (text, callback_data, style)
    """
    builder = InlineKeyboardBuilder()
    for row in rows:
        row_buttons = []
        for text, callback_data, style in row:
            row_buttons.append(InlineKeyboardButton(text=text, callback_data=callback_data, style=style))
        builder.row(*row_buttons)
    return builder.as_markup()


def build_grid_keyboard(
    rows: List[List[Tuple[str, str]]]
) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру-сетку без цветов.
    rows: список строк, где каждая строка - список кортежей (text, callback_data)
    """
    builder = InlineKeyboardBuilder()
    for row in rows:
        row_buttons = [InlineKeyboardButton(text=t, callback_data=c) for t, c in row]
        builder.row(*row_buttons)
    return builder.as_markup()


def build_vertical_keyboard(buttons: List[Tuple[str, str]]) -> InlineKeyboardMarkup:
    """Создаёт вертикальную клавиатуру без цветов."""
    builder = InlineKeyboardBuilder()
    for text, callback_data in buttons:
        builder.row(InlineKeyboardButton(text=text, callback_data=callback_data))
    return builder.as_markup()


async def safe_edit_message(
    cb: CallbackQuery,
    text: str,
    markup: Optional[InlineKeyboardMarkup] = None
) -> bool:
    try:
        await cb.message.edit_text(text[:4090], reply_markup=markup, parse_mode=ParseMode.HTML)
        return True
    except TelegramBadRequest as e:
        error_str = str(e).lower()
        if "message is not modified" in error_str:
            return True
        try:
            await cb.message.answer(text[:4090], reply_markup=markup, parse_mode=ParseMode.HTML)
            return True
        except Exception as fallback_err:
            logging.error(f"Fallback error: {fallback_err}")
            return False
    except Exception as e:
        logging.error(f"Edit error: {e}")
        return False


async def safe_edit_message_by_id(
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str,
    markup: Optional[InlineKeyboardMarkup] = None
) -> bool:
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text[:4090],
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
        return True
    except TelegramBadRequest as e:
        error_str = str(e).lower()
        if "message is not modified" in error_str:
            return True
        return False
    except Exception as e:
        logging.error(f"Edit by id error: {e}")
        return False


def format_number(num: int) -> str:
    return f"{num:,}".replace(",", " ")


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        schema = """
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                name TEXT NOT NULL,
                crystals INTEGER NOT NULL DEFAULT 0,
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
                created REAL NOT NULL DEFAULT 0,
                last_active REAL NOT NULL DEFAULT 0,
                total_duels INTEGER NOT NULL DEFAULT 0,
                total_crystals_earned INTEGER NOT NULL DEFAULT 0,
                auto_accept INTEGER NOT NULL DEFAULT 0
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
                reward_crystals INTEGER NOT NULL DEFAULT 0,
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
            CREATE TABLE IF NOT EXISTS chat_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                name TEXT NOT NULL,
                hp INTEGER NOT NULL,
                max_hp INTEGER NOT NULL,
                started_by INTEGER NOT NULL,
                started_at REAL NOT NULL,
                ends_at REAL NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                participants TEXT NOT NULL DEFAULT '[]'
            );
            CREATE INDEX IF NOT EXISTS ix_notif_user ON notifications(user_id, seen);
            CREATE INDEX IF NOT EXISTS ix_players_wins ON players(wins, is_bot, banned);
            CREATE INDEX IF NOT EXISTS ix_events_active ON chat_events(active, ends_at);
        """
        try:
            self._connection.executescript(schema)
            logging.info("Database schema initialized.")
        except sqlite3.Error as e:
            logging.critical(f"Failed to initialize schema: {e}")
            raise

    def fetch_one(self, sql: str, args: tuple = ()) -> Optional[sqlite3.Row]:
        try:
            return self._connection.execute(sql, args).fetchone()
        except sqlite3.Error as e:
            logging.error(f"DB fetch_one error: {e}")
            return None

    def fetch_all(self, sql: str, args: tuple = ()) -> List[sqlite3.Row]:
        try:
            return self._connection.execute(sql, args).fetchall()
        except sqlite3.Error as e:
            logging.error(f"DB fetch_all error: {e}")
            return []

    def execute(self, sql: str, args: tuple = ()) -> bool:
        try:
            self._connection.execute(sql, args)
            return True
        except sqlite3.Error as e:
            logging.error(f"DB execute error: {e}")
            return False

    def close(self) -> None:
        if self._connection:
            self._connection.close()


db = DatabaseManager(Config.DB_PATH)


@dataclass
class Fighter:
    name: str
    max_hp: int
    hp: int
    weapon: str
    armor_slots: Dict[str, str] = field(default_factory=dict)
    dots: List[Dict[str, Any]] = field(default_factory=list)
    stun: bool = False
    attack_cooldowns: Dict[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.weapon not in WEAPONS:
            self.weapon = "fists"
        self.base_weapon_dmg = WEAPONS[self.weapon]["base_dmg"]
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
            item = get_armor_item_by_key(self.armor_slots[slot]) or get_armor_item_by_key(f"{slot}_none")
            self.armor_def[slot] = item["df"]
            total_chance += item["chance"]
            total_bonus += item["dmg_bonus"]
        self.spec_chance = min(total_chance, 70)
        self.spec_dmg_bonus = total_bonus / 100.0

    def is_alive(self) -> bool:
        return self.hp > 0

    def get_armor_def(self, zone: str) -> int:
        return self.armor_def.get(zone, 0)

    def get_weapon_dmg_for_zone(self, zone: str, variant_mult: float = 1.0) -> int:
        zone_mult = ZONE_INFO.get(zone, {}).get("mult", 1.0)
        base = self.base_weapon_dmg * zone_mult * variant_mult
        return max(1, round(base))

    def reduce_cooldowns(self) -> None:
        for idx in list(self.attack_cooldowns.keys()):
            self.attack_cooldowns[idx] -= 1
            if self.attack_cooldowns[idx] <= 0:
                del self.attack_cooldowns[idx]

    def get_available_variants(self) -> List[int]:
        all_variants = list(range(len(WEAPONS[self.weapon]["variants"])))
        return [i for i in all_variants if i not in self.attack_cooldowns]


def get_armor_item_by_key(key: str) -> Optional[Dict[str, Any]]:
    for slot, items in ARMOR_DATA.items():
        for it in items:
            if it["key"] == key:
                return {**it, "slot": slot}
    return None


def generate_hp_bar(fighter: Fighter, width: int = 12) -> str:
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
    w = WEAPONS[fighter.weapon]
    ad = fighter.armor_def
    cd_str = ""
    if fighter.attack_cooldowns:
        cd_info = [f"Атака {i + 1}: {c}р" for i, c in fighter.attack_cooldowns.items()]
        cd_str = f"\n│ ⏳ КД: {', '.join(cd_info)}"
    return (
        f"│ <b>{fighter.name}</b>\n"
        f"│ {E_HEART} <b>{fighter.hp}</b>/{fighter.max_hp}  {generate_hp_bar(fighter)}{cd_str}\n"
        f"│ {w['emoji']} {w['name']} · баз. урон {fighter.base_weapon_dmg}\n"
        f"│ {E_SHIELD} {E_ZONE_HEAD}{ad['head']} {E_ZONE_TORSO}{ad['torso']} "
        f"{E_ZONE_ARMS}{ad['arms']} {E_ZONE_LEGS}{ad['legs']}"
    )


@dataclass
class Duel:
    a_id: int
    b_id: int
    a: Fighter
    b: Fighter
    attacker_is_a: bool = True
    round_no: int = 1
    atk_zone: Optional[str] = None
    def_zone: Optional[str] = None
    chosen_variant_idx: Optional[int] = None
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
        if uid == self.a_id:
            return self.a
        if uid == self.b_id:
            return self.b
        return None

    def get_opponent(self, uid: int) -> Optional[Fighter]:
        if uid == self.a_id:
            return self.b
        if uid == self.b_id:
            return self.a
        return None

    def add_log(self, message: str) -> None:
        self.log.append(message)
        if len(self.log) > DUEL_LOG_LIMIT:
            self.log = self.log[-DUEL_LOG_LIMIT:]


ACTIVE_DUELS: Dict[int, Duel] = {}


@dataclass
class PendingDuel:
    challenger_id: int
    target_id: int
    challenger_msg_id: int
    target_msg_id: int
    chat_id: int
    created_at: float
    timeout_task: Optional[asyncio.Task] = None
    direct: bool = False


PENDING_DUELS: Dict[Tuple[int, int], PendingDuel] = {}


@dataclass
class ChatEvent:
    event_id: int
    event_type: str
    name: str
    hp: int
    max_hp: int
    started_by: int
    started_at: float
    ends_at: float
    active: bool = True
    participants: Set[int] = field(default_factory=set)
    damage_log: List[str] = field(default_factory=list)
    total_damage_dealt: int = 0

    def is_active(self) -> bool:
        return self.active and self.hp > 0 and time.time() < self.ends_at

    def take_damage(self, attacker_id: int, attacker_name: str, damage: int, is_crit: bool = False) -> str:
        self.hp = max(0, self.hp - damage)
        self.participants.add(attacker_id)
        self.total_damage_dealt += damage
        crit_text = " 💥 <b>КРИТ!</b>" if is_crit else ""
        log_entry = f"⚔️ {attacker_name} наносит <b>{damage}</b> урона!{crit_text} (Осталось HP: {self.hp}/{self.max_hp})"
        self.damage_log.append(log_entry)
        return log_entry

    def get_participants_count(self) -> int:
        return len(self.participants)

    def get_time_left(self) -> int:
        return max(0, int(self.ends_at - time.time()))


ACTIVE_CHAT_EVENT: Optional[ChatEvent] = None
NEXT_SCHEDULED_EVENT: Optional[float] = None


def calculate_damage(
    attacker: Fighter,
    defender: Fighter,
    atk_zone: str,
    def_zone: Optional[str],
    variant: AttackVariant
) -> Tuple[int, str]:
    if def_zone == atk_zone:
        return 0, f"{E_SHIELD} <b>Блок!</b>"
    weapon_dmg = attacker.get_weapon_dmg_for_zone(atk_zone, variant.damage_mult)
    base_armor = defender.get_armor_def(atk_zone)
    effective_armor = max(0, round(base_armor * (1.0 - variant.armor_penetration)))
    final_dmg = max(1, round(weapon_dmg - effective_armor))
    return final_dmg, ""


def process_dots(fighter: Fighter, log: List[str]) -> None:
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
    target.dots = [d for d in target.dots if d["name"] != name]
    target.dots.append({"name": name, "dmg": dmg, "left": rounds})


def resolve_special_attack(
    attacker: Fighter,
    defender: Fighter,
    atk_zone: str,
    def_zone: Optional[str],
    variant: AttackVariant,
    log: List[str]
) -> bool:
    if def_zone == atk_zone:
        log.append(f"{E_SHIELD} {defender.name} заблокировал <b>{variant.name}</b>")
        return True
    effect = variant.effect
    if effect == "triple":
        hits = [max(1, round(calculate_damage(attacker, defender, atk_zone, def_zone, variant)[0] / 3)) for _ in range(3)]
        total_dmg = sum(hits)
        defender.hp = max(0, defender.hp - total_dmg)
        log.append(f"⚡ <b>{variant.name}</b>: {' + '.join(map(str, hits))} = <b>−{total_dmg}</b>")
        return True
    elif effect == "exec":
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        log.append(f"{E_SWORD} <b>{variant.name}</b>: {attacker.name} → {defender.name} <b>−{dmg}</b>")
        return True
    elif effect == "bleed":
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        bleed_dmg = max(1, round(defender.max_hp * 0.04))
        apply_dot_effect(defender, "🩸 Кровотечение", bleed_dmg, 3)
        log.append(f"🪓 <b>{variant.name}</b>: −{dmg}, кровь по <b>{bleed_dmg}</b> ×3")
        return True
    elif effect == "pierce":
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        log.append(f"🏹 <b>{variant.name}</b>: пробивает броню на <b>−{dmg}</b>")
        return True
    elif effect == "burn":
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        burn_dmg = max(1, round(dmg * 0.4))
        apply_dot_effect(defender, f"{E_FIRE} Горение", burn_dmg, 3)
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
    atk_zone: str,
    def_zone: Optional[str],
    variant_idx: int,
    log: List[str]
) -> None:
    if attacker.stun:
        attacker.stun = False
        log.append(f"💫 {attacker.name} оглушён и пропускает ход!")
        return
    weapon_data = WEAPONS[attacker.weapon]
    variant = weapon_data["variants"][variant_idx]
    if variant.cooldown_rounds > 0:
        attacker.attack_cooldowns[variant_idx] = variant.cooldown_rounds
    if variant.effect and random.random() * 100 < attacker.spec_chance:
        if resolve_special_attack(attacker, defender, atk_zone, def_zone, variant, log):
            return
    dmg, note = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
    if note:
        log.append(f"{ZONE_INFO[atk_zone]['emoji']} {attacker.name} бьёт — {note}")
    else:
        defender.hp = max(0, defender.hp - dmg)
        log.append(f"👊 {attacker.name} [{variant.name}] → {defender.name} <b>−{dmg}</b>")


def stop_duel_timer(duel: Duel) -> None:
    if duel.timer_task and not duel.timer_task.done():
        duel.timer_task.cancel()
    duel.timer_task = None
    duel.timer_deadline = 0.0
    duel.timer_for = None
    duel.timer_role = None


def terminate_duel(duel: Duel) -> None:
    duel.finished = True
    stop_duel_timer(duel)
    ACTIVE_DUELS.pop(duel.a_id, None)
    if duel.b_id > 0:
        ACTIVE_DUELS.pop(duel.b_id, None)


def start_duel_timer(duel: Duel, uid: int, role: str, bot: Bot) -> None:
    if uid < 0:
        return
    stop_duel_timer(duel)
    duel.timer_for = uid
    duel.timer_role = role
    duel.timer_deadline = time.time() + Config.TURN_TIMEOUT
    duel.timer_task = asyncio.create_task(_timer_runner_task(duel, uid, role, bot))


async def _timer_runner_task(duel: Duel, uid: int, role: str, bot: Bot) -> None:
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
    loser = duel.get_fighter(loser_uid)
    loser_name = loser.name if loser else "Неизвестный"
    duel.log.append(f"⏱ <b>{loser_name} не успел за {Config.TURN_TIMEOUT} сек!</b>")
    winner_is_a = not (loser_uid == duel.a_id)
    await finalize_duel(duel, winner_is_a=winner_is_a, bot=bot, reason="timeout")


def get_player_armor_slots(player_row: sqlite3.Row) -> Dict[str, str]:
    if not player_row:
        return {s: f"{s}_none" for s in ZONES}
    return {
        "head": player_row["armor_head"] or "head_none",
        "torso": player_row["armor_torso"] or "torso_none",
        "arms": player_row["armor_arms"] or "arms_none",
        "legs": player_row["armor_legs"] or "legs_none",
    }


def create_fighter_from_db(player_row: sqlite3.Row) -> Fighter:
    slots = get_player_armor_slots(player_row)
    total_hp = BASE_STATS["hp"]
    for key in slots.values():
        item = get_armor_item_by_key(key)
        if item:
            total_hp += item.get("hp", 0)
    weapon = player_row["weapon"] if player_row["weapon"] in WEAPONS else "fists"
    return Fighter(name=esc(player_row["name"]), max_hp=total_hp, hp=total_hp, weapon=weapon, armor_slots=slots)


def determine_arena(wins: int) -> str:
    for k in ARENA_ORDER:
        if ARENAS[k]["min_wins"] <= wins <= ARENAS[k]["max_wins"]:
            return k
    return "gold"


HUMAN_NAMES: List[str] = [
    "Максим", "Артём", "Данил", "Кирилл", "Егор", "Иван", "Никита", "Рома",
    "Саня", "Дима", "Влад", "Серёга", "Паша", "Толя", "Женя", "Костя",
    "Лёха", "Миша", "Гриша", "Стас", "Олег", "Ден", "Марк", "Тимур",
    "Алина", "Катя", "Настя", "Даша", "Лера", "Соня", "Вика", "Полина",
    "Крис", "Милана", "Аня", "Юля", "Оля", "Маша", "Ксюша", "Ника",
]

HUMAN_TITLES: List[str] = ["", "", "", "xd", "pro", "god", "real", "top", "_", "007", "tvoy", "cz", "boss", "king"]


def ensure_masked_bots_exist(target_count: int = 50) -> None:
    existing_names = {r["name"].lower() for r in db.fetch_all("SELECT name FROM players")}
    bots = db.fetch_all("SELECT user_id, wins FROM players WHERE is_bot=1")
    need = max(0, target_count - len(bots))
    for _ in range(need):
        name = ""
        for _ in range(BOT_NAME_GENERATION_ATTEMPTS):
            base = random.choice(HUMAN_NAMES)
            title = random.choice(HUMAN_TITLES)
            suffix = str(random.randint(1, 99)) if random.random() < 0.35 else ""
            candidate = f"{base}{title}{suffix}"
            if candidate.lower() not in existing_names and MIN_NAME_LENGTH <= len(candidate) <= 16:
                existing_names.add(candidate.lower())
                name = candidate
                break
        if not name:
            name = f"Игрок{random.randint(1000, 9999)}"
        uid = -random.randint(10_000_000, 99_999_999)
        arena_rand = random.random()
        if arena_rand < Config.BOT_WIN_DISTRIBUTION["bronze"]:
            wins = random.randint(0, 9)
        elif arena_rand < Config.BOT_WIN_DISTRIBUTION["bronze"] + Config.BOT_WIN_DISTRIBUTION["silver"]:
            wins = random.randint(10, 29)
        else:
            wins = random.randint(30, 60)
        losses = random.randint(max(0, wins // 2), wins * 2 + 3)
        arena_key = determine_arena(wins)
        if arena_key == "bronze":
            weapon = random.choice(["fists", "dagger", "sword"])
            tier_max = 2
        elif arena_key == "silver":
            weapon = random.choice(["sword", "axe", "bow", "dagger"])
            tier_max = 3
        else:
            weapon = random.choice(["bow", "staff", "hammer", "axe", "sword"])
            tier_max = 4
        slots = {}
        for s in ZONES:
            items = ARMOR_DATA[s]
            idx = min(random.randint(0, tier_max), len(items) - 1)
            slots[s] = items[idx]["key"]
        owned_armors = set(list(slots.values()) + START_ARMOR_KEYS)
        db.execute(
            """INSERT INTO players (user_id, username, name, crystals, wins, losses, weapon,
                armor_head, armor_torso, armor_arms, armor_legs, weapons_owned, armors_owned, is_bot, created, last_active)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (uid, None, name, random.randint(0, 400), wins, losses, weapon,
             slots["head"], slots["torso"], slots["arms"], slots["legs"],
             weapon, ",".join(owned_armors), 1, time.time(), time.time())
        )


def pick_balanced_opponent(player_uid: int, player_wins: int) -> Optional[int]:
    arena = determine_arena(player_wins)
    limits = ARENAS[arena]
    humans = [r["user_id"] for r in db.fetch_all(
        """SELECT user_id FROM players WHERE user_id != ? AND banned=0 AND is_bot=0
           AND wins BETWEEN ? AND ? ORDER BY RANDOM() LIMIT 6""",
        (player_uid, limits["min_wins"], limits["max_wins"])
    )]
    bots = [r["user_id"] for r in db.fetch_all(
        """SELECT user_id FROM players WHERE is_bot=1 AND banned=0
           AND wins BETWEEN ? AND ? ORDER BY RANDOM() LIMIT 6""",
        (limits["min_wins"], limits["max_wins"])
    )]
    if humans and bots:
        return random.choice(bots if random.random() < 0.6 else humans)
    if humans:
        return random.choice(humans)
    if bots:
        return random.choice(bots)
    ensure_masked_bots_exist(10)
    rows = db.fetch_all(
        """SELECT user_id FROM players WHERE is_bot=1 AND wins BETWEEN ? AND ?
           ORDER BY RANDOM() LIMIT 1""",
        (limits["min_wins"], limits["max_wins"])
    )
    return rows[0]["user_id"] if rows else None


def bot_decide_attack_zone(attacker: Fighter, defender: Fighter) -> str:
    if random.random() < 0.10:
        return random.choice(ZONES)
    if defender.hp <= defender.max_hp * 0.30:
        return max(ZONES, key=lambda z: attacker.get_weapon_dmg_for_zone(z))
    def score_zone(z: str) -> tuple:
        dmg = attacker.get_weapon_dmg_for_zone(z) - defender.get_armor_def(z)
        return (dmg, ZONE_INFO[z]["mult"])
    return max(ZONES, key=score_zone)


def bot_decide_attack_variant(attacker: Fighter) -> int:
    variants = WEAPONS[attacker.weapon]["variants"]
    available = attacker.get_available_variants()
    if not available:
        return 0
    return max(available, key=lambda i: variants[i].damage_mult)


def bot_decide_to_defend(duel: Duel, bot_is_a: bool) -> bool:
    if duel.bot_block_streak >= 2 or duel.round_no - duel.bot_last_block_round < 3:
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
    def danger_level(z: str) -> int:
        return attacker.get_weapon_dmg_for_zone(z) - defender.get_armor_def(z)
    sorted_zones = sorted(ZONES, key=danger_level, reverse=True)
    if random.random() < 0.25 and len(sorted_zones) > 1:
        return sorted_zones[1]
    return sorted_zones[0]


async def play_casino_slots_animated(chat_id: int, bet: int, uid: int, bot: Bot, bet_type: str = "jackpot") -> Tuple[Optional[str], Optional[str]]:
    """
    Игра в слоты с анимацией.
    bet_type: "jackpot" (ставка на 1, выплата ×10) или "miss" (ставка на не-1, выплата ×1.5)
    """
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."
    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))
    sent_message = await bot.send_dice(chat_id=chat_id, emoji="🎰")
    dice_value = sent_message.dice.value
    if bet_type == "jackpot":
        if dice_value == 1:
            mult = 10
            win = bet * mult
            db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (win, uid))
            return (
                f"🎰 <b>{dice_value}</b>\n\n"
                f"{E_TROPHY} <b>ДЖЕКПОТ!</b>\n"
                f"Вы выиграли: <b>+{win} {E_CRYSTAL}</b> (×{mult})",
                None
            )
        else:
            return (
                f"🎰 <b>{dice_value}</b>\n\n"
                f"{E_SKULL} <b>Промах.</b>\n"
                f"Вы проиграли: <b>−{bet} {E_CRYSTAL}</b>",
                None
            )
    else:
        if dice_value != 1:
            mult = 1.5
            win = int(bet * mult)
            db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (win, uid))
            return (
                f"🎰 <b>{dice_value}</b>\n\n"
                f"{E_TROPHY} <b>Промах! Вы выиграли!</b>\n"
                f"Вы выиграли: <b>+{win} {E_CRYSTAL}</b> (×{mult})",
                None
            )
        else:
            return (
                f"🎰 <b>{dice_value}</b>\n\n"
                f"{E_SKULL} <b>Джекпот! Вы проиграли.</b>\n"
                f"Вы проиграли: <b>−{bet} {E_CRYSTAL}</b>",
                None
            )


async def play_casino_darts_animated(chat_id: int, bet: int, uid: int, bot: Bot, bet_type: str = "hit", bet_zone: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Игра в дартс с анимацией.
    Значения дротика:
      1-2: промах мимо мишени
      3: жёлтая зона (внешнее кольцо)
      4: красная зона (среднее кольцо)
      5: зелёная зона (внутреннее кольцо)
      6: яблочко (центр)
    
    bet_type:
      "hit" — попадание (3-6), выплата ×1.9
      "miss" — промах (1-2), выплата ×2
      "red" — красная зона (4), выплата ×3
      "white" — белая/жёлтая зона (3), выплата ×4
      "yellow" — жёлтая зона (3), выплата ×4 (синоним white)
      "bullseye" — яблочко (6), выплата ×10
    """
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."
    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))
    sent_message = await bot.send_dice(chat_id=chat_id, emoji="🎯")
    dice_value = sent_message.dice.value
    
    zone_name = ""
    zone_emoji = ""
    if dice_value <= 2:
        zone_name = "промах"
        zone_emoji = "❌"
    elif dice_value == 3:
        zone_name = "жёлтая зона"
        zone_emoji = E_YELLOW
    elif dice_value == 4:
        zone_name = "красная зона"
        zone_emoji = E_RED
    elif dice_value == 5:
        zone_name = "зелёная зона"
        zone_emoji = E_GREEN
    elif dice_value == 6:
        zone_name = "яблочко"
        zone_emoji = "🎯"
    
    win = False
    mult = 0
    
    if bet_type == "hit":
        if 3 <= dice_value <= 6:
            mult = 1.9
            win = True
    elif bet_type == "miss":
        if dice_value <= 2:
            mult = 2
            win = True
    elif bet_type == "red":
        if dice_value == 4:
            mult = 3
            win = True
    elif bet_type in ("white", "yellow"):
        if dice_value == 3:
            mult = 4
            win = True
    elif bet_type == "bullseye":
        if dice_value == 6:
            mult = 10
            win = True
    
    if win:
        payout = int(bet * mult)
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
        return (
            f"🎯 <b>{dice_value}</b> — {zone_emoji} {zone_name}\n\n"
            f"{E_TROPHY} <b>Победа!</b>\n"
            f"Вы выиграли: <b>+{payout} {E_CRYSTAL}</b> (×{mult})",
            None
        )
    else:
        return (
            f"🎯 <b>{dice_value}</b> — {zone_emoji} {zone_name}\n\n"
            f"{E_SKULL} <b>Поражение.</b>\n"
            f"Вы проиграли: <b>−{bet} {E_CRYSTAL}</b>",
            None
        )


async def play_casino_basketball_animated(chat_id: int, bet: int, uid: int, bot: Bot, bet_type: str = "hit") -> Tuple[Optional[str], Optional[str]]:
    """
    Игра в баскетбол с анимацией.
    Значения:
      1-4: промах
      5: попадание (слэм-данк)
    
    bet_type:
      "hit" — попадание (5), выплата ×1.9
      "miss" — промах (1-4), выплата ×1.3
    """
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."
    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))
    sent_message = await bot.send_dice(chat_id=chat_id, emoji="🏀")
    dice_value = sent_message.dice.value
    
    result_name = "слэм-данк!" if dice_value == 5 else "промах"
    result_emoji = "🏀" if dice_value == 5 else "❌"
    
    win = False
    mult = 0
    
    if bet_type == "hit":
        if dice_value == 5:
            mult = 1.9
            win = True
    elif bet_type == "miss":
        if dice_value <= 4:
            mult = 1.3
            win = True
    
    if win:
        payout = int(bet * mult)
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
        return (
            f"🏀 <b>{dice_value}</b> — {result_emoji} {result_name}\n\n"
            f"{E_TROPHY} <b>Победа!</b>\n"
            f"Вы выиграли: <b>+{payout} {E_CRYSTAL}</b> (×{mult})",
            None
        )
    else:
        return (
            f"🏀 <b>{dice_value}</b> — {result_emoji} {result_name}\n\n"
            f"{E_SKULL} <b>Поражение.</b>\n"
            f"Вы проиграли: <b>−{bet} {E_CRYSTAL}</b>",
            None
        )


def play_casino_roulette(uid: int, bet: int, bet_type: str, bet_value: Any = None) -> Tuple[Optional[str], Optional[str]]:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."
    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    reds = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    num = random.randint(0, 36)
    if num == 0:
        res_color = "green"
        color_emoji = E_GREEN
    elif num in reds:
        res_color = "red"
        color_emoji = E_RED
    else:
        res_color = "black"
        color_emoji = "⚫"
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))
    win = False
    mult = 0
    if bet_type == "color":
        if bet_value == res_color:
            mult = 14 if res_color == "green" else 2
            win = True
    elif bet_type == "even_odd":
        if num != 0:
            is_even = (num % 2 == 0)
            if (bet_value == "even" and is_even) or (bet_value == "odd" and not is_even):
                mult = 2
                win = True
    elif bet_type == "half":
        if num != 0:
            if (bet_value == "low" and 1 <= num <= 18) or (bet_value == "high" and 19 <= num <= 36):
                mult = 2
                win = True
    elif bet_type == "number":
        if num == bet_value:
            mult = 36
            win = True
    elif bet_type == "dozen":
        if num != 0:
            if (bet_value == 1 and 1 <= num <= 12) or (bet_value == 2 and 13 <= num <= 24) or (bet_value == 3 and 25 <= num <= 36):
                mult = 3
                win = True
    if win:
        payout = bet * mult
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
        return (
            f"🎡 <b>{num}</b> {color_emoji} ({res_color})\n\n"
            f"{E_TROPHY} <b>Победа ×{mult}!</b>\n"
            f"Вы выиграли: <b>+{payout} {E_CRYSTAL}</b>",
            None
        )
    else:
        return (
            f"🎡 <b>{num}</b> {color_emoji} ({res_color})\n\n"
            f"{E_SKULL} <b>Поражение.</b>\n"
            f"Вы проиграли: <b>−{bet} {E_CRYSTAL}</b>",
            None
        )


def play_casino_coin(uid: int, bet: int, choice: str = "heads") -> Tuple[Optional[str], Optional[str]]:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."
    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    result = random.choice(["heads", "tails"])
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))
    result_text = "Орёл" if result == "heads" else "Решка"
    result_emoji = "🔵" if result == "heads" else "🔴"
    if result == choice:
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (bet * 2, uid))
        return (
            f"{E_COIN} <b>{result_text}</b> {result_emoji}\n\n"
            f"{E_TROPHY} <b>Победа!</b>\n"
            f"Вы выиграли: <b>+{bet * 2} {E_CRYSTAL}</b> (×2)",
            None
        )
    return (
        f"{E_COIN} <b>{result_text}</b> {result_emoji}\n\n"
        f"{E_SKULL} <b>Поражение.</b>\n"
        f"Вы проиграли: <b>−{bet} {E_CRYSTAL}</b>",
        None
    )


def play_casino_highlow(uid: int, bet: int, choice: str = "high") -> Tuple[Optional[str], Optional[str]]:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."
    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    result_num = random.randint(1, 100)
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))
    if result_num == 50:
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (bet, uid))
        return (
            f"📊 <b>{result_num}</b>\n\n"
            f"🤝 <b>Ровно 50!</b>\n"
            f"Ставка возвращена.",
            None
        )
    win = (choice == "high" and result_num > 50) or (choice == "low" and result_num < 50)
    if win:
        payout = int(bet * 1.9)
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
        return (
            f"📊 <b>{result_num}</b>\n\n"
            f"{E_TROPHY} <b>Победа!</b>\n"
            f"Вы выиграли: <b>+{payout} {E_CRYSTAL}</b> (×1.9)",
            None
        )
    return (
        f"📊 <b>{result_num}</b>\n\n"
        f"{E_SKULL} <b>Поражение.</b>\n"
        f"Вы проиграли: <b>−{bet} {E_CRYSTAL}</b>",
        None
    )


def spawn_chat_event(
    event_type: str,
    started_by: int,
    custom_hp: Optional[int] = None,
    custom_duration: Optional[float] = None
) -> Optional[ChatEvent]:
    global ACTIVE_CHAT_EVENT
    if ACTIVE_CHAT_EVENT and ACTIVE_CHAT_EVENT.is_active():
        return None
    template = CHAT_EVENT_TEMPLATES.get(event_type)
    if not template:
        return None
    hp = custom_hp or template["base_hp"]
    duration = custom_duration or template["duration_hours"]
    name = template["name_template"].format(emoji=template["emoji"])
    now = time.time()
    ends_at = now + (duration * 3600)
    event = ChatEvent(
        event_id=int(now), event_type=event_type, name=name,
        hp=hp, max_hp=hp, started_by=started_by, started_at=now, ends_at=ends_at,
    )
    ACTIVE_CHAT_EVENT = event
    db.execute(
        """INSERT INTO chat_events (event_type, name, hp, max_hp, started_by, started_at, ends_at, active)
           VALUES (?,?,?,?,?,?,?,1)""",
        (event_type, name, hp, hp, started_by, now, ends_at)
    )
    return event


def attack_chat_event(attacker_id: int, attacker_name: str) -> Optional[str]:
    global ACTIVE_CHAT_EVENT
    if not ACTIVE_CHAT_EVENT or not ACTIVE_CHAT_EVENT.is_active():
        return None
    base_dmg = random.randint(Config.EVENT_MIN_DAMAGE, Config.EVENT_MAX_DAMAGE)
    is_crit = random.random() < Config.EVENT_CRIT_CHANCE
    if is_crit:
        base_dmg = int(base_dmg * Config.EVENT_CRIT_MULT)
    log_entry = ACTIVE_CHAT_EVENT.take_damage(attacker_id, attacker_name, base_dmg, is_crit)
    if ACTIVE_CHAT_EVENT.hp <= 0:
        ACTIVE_CHAT_EVENT.active = False
        db.execute("UPDATE chat_events SET active=0 WHERE event_id=?", (ACTIVE_CHAT_EVENT.event_id,))
        template = CHAT_EVENT_TEMPLATES.get(ACTIVE_CHAT_EVENT.event_type, {})
        reward_range = template.get("reward_per_participant", (30, 100))
        total_rewards = 0
        for pid in ACTIVE_CHAT_EVENT.participants:
            reward = random.randint(reward_range[0], reward_range[1])
            db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (reward, pid))
            total_rewards += reward
        log_entry += (
            f"\n\n{E_TROPHY} <b>СОБЫТИЕ ЗАВЕРШЕНО!</b>\n"
            f"👥 Участников: {ACTIVE_CHAT_EVENT.get_participants_count()}\n"
            f"{E_CRYSTAL} Роздано наград: {total_rewards}"
        )
    return log_entry


def get_chat_event_status() -> Optional[str]:
    global ACTIVE_CHAT_EVENT
    if not ACTIVE_CHAT_EVENT or not ACTIVE_CHAT_EVENT.is_active():
        return None
    time_left = ACTIVE_CHAT_EVENT.get_time_left()
    minutes = time_left // 60
    seconds = time_left % 60
    hp_percent = (ACTIVE_CHAT_EVENT.hp / ACTIVE_CHAT_EVENT.max_hp) * 100
    return (
        f"{ACTIVE_CHAT_EVENT.name}\n"
        f"❤️ HP: <b>{ACTIVE_CHAT_EVENT.hp}</b>/{ACTIVE_CHAT_EVENT.max_hp} ({hp_percent:.0f}%)\n"
        f"👥 Участников: <b>{ACTIVE_CHAT_EVENT.get_participants_count()}</b>\n"
        f"⏱ Осталось: <b>{minutes}:{seconds:02d}</b>\n\n"
        f"Используйте команду <code>атака</code> для нанесения урона!"
    )


def create_promo_code(
    code: str, reward_crystals: int, reward_wins: int,
    max_uses: int, hours_valid: int, created_by: int
) -> Tuple[bool, str]:
    code = code.strip().upper()
    if not code or len(code) < Config.PROMO_MIN_CODE_LENGTH or len(code) > Config.PROMO_MAX_CODE_LENGTH:
        return False, f"Код должен быть от {Config.PROMO_MIN_CODE_LENGTH} до {Config.PROMO_MAX_CODE_LENGTH} символов."
    if not re.match(r'^[A-Z0-9_-]+$', code):
        return False, "Код может содержать только буквы, цифры, _ и -"
    if reward_crystals < 0 or reward_wins < 0:
        return False, "Награды не могут быть отрицательными."
    if max_uses < 1 or max_uses > Config.PROMO_MAX_USES:
        return False, f"Максимум активаций: от 1 до {Config.PROMO_MAX_USES}."
    if hours_valid < 1 or hours_valid > Config.PROMO_MAX_HOURS:
        return False, f"Срок действия: от 1 до {Config.PROMO_MAX_HOURS} часов."
    existing = db.fetch_one("SELECT code FROM promo_codes WHERE code=?", (code,))
    if existing:
        return False, f"Промокод <code>{code}</code> уже существует."
    now = time.time()
    expires_at = now + (hours_valid * 3600)
    db.execute(
        """INSERT INTO promo_codes
           (code, reward_crystals, reward_wins, max_uses, current_uses, expires_at, created_by, created_at, active)
           VALUES (?, ?, ?, ?, 0, ?, ?, ?, 1)""",
        (code, reward_crystals, reward_wins, max_uses, expires_at, created_by, now)
    )
    return True, (
        f"{E_PROMO} Промокод <code>{code}</code> создан!\n\n"
        f"💎 Кристаллы: {reward_crystals}\n🏆 Победы: {reward_wins}\n"
        f"👥 Макс. активаций: {max_uses}\n⏳ Действует: {hours_valid} ч."
    )


def activate_promo_code(user_id: int, code: str) -> Tuple[bool, str]:
    code = code.strip().upper()
    player = db.fetch_one("SELECT * FROM players WHERE user_id=?", (user_id,))
    if not player:
        return False, "Сначала отправь /start в ЛС бота."
    if player["banned"]:
        return False, "🚫 Тебе недоступна активация промокодов."
    promo = db.fetch_one("SELECT * FROM promo_codes WHERE code=?", (code,))
    if not promo:
        return False, f"❌ Промокод <code>{code}</code> не найден."
    if not promo["active"]:
        return False, f"❌ Промокод <code>{code}</code> деактивирован."
    if promo["expires_at"] < time.time():
        return False, f"❌ Промокод <code>{code}</code> истёк."
    if promo["current_uses"] >= promo["max_uses"]:
        return False, f"❌ Промокод <code>{code}</code> исчерпан."
    already = db.fetch_one("SELECT 1 FROM promo_activations WHERE user_id=? AND code=?", (user_id, code))
    if already:
        return False, f"❌ Ты уже активировал промокод <code>{code}</code>."
    now = time.time()
    db.execute("INSERT INTO promo_activations (user_id, code, activated_at) VALUES (?, ?, ?)", (user_id, code, now))
    db.execute("UPDATE promo_codes SET current_uses=current_uses+1 WHERE code=?", (code,))
    rewards = []
    if promo["reward_crystals"] > 0:
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (promo["reward_crystals"], user_id))
        rewards.append(f"💎 +{promo['reward_crystals']} кристаллов")
    if promo["reward_wins"] > 0:
        db.execute("UPDATE players SET wins=wins+? WHERE user_id=?", (promo["reward_wins"], user_id))
        rewards.append(f"🏆 +{promo['reward_wins']} побед")
    rewards_text = "\n".join(rewards) if rewards else "🎁 Секретный бонус!"
    remaining = promo["max_uses"] - promo["current_uses"] - 1
    return True, (
        f"{E_GIFT} <b>ПРОМОКОД АКТИВИРОВАН!</b>\n\n"
        f"🎟 Код: <code>{code}</code>\n{rewards_text}\n\n"
        f"📊 Осталось активаций: {remaining}/{promo['max_uses']}"
    )


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
    "покормить": ("🍕", "покормил(а)"),
    "напоить": ("🍺", "напоил(а)"),
    "щекотать": ("🤣", "пощекотал(а)"),
    "благословить": ("🙏", "благословил(а)"),
    "проклясть": ("💀", "проклял(а)"),
}

RP_COOLDOWNS: Dict[Tuple[int, int, str], float] = {}


def generate_rp_text(actor_id: int, actor_name: str, target_id: int, target_name: str, action_key: str) -> str:
    emoji, verb = RP_ACTIONS.get(action_key, ("✨", "взаимодействовал(а) с"))
    actor_mention = create_mention(actor_id, actor_name)
    target_mention = create_mention(target_id, target_name)
    return f"{emoji} {actor_mention} {verb} {target_mention}!"


def resolve_command_target(m: Message, command_word: str) -> Tuple[Optional[int], Optional[str]]:
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
                """SELECT user_id FROM players
                   WHERE (LOWER(username)=LOWER(?) OR LOWER(name)=LOWER(?)) AND banned=0 LIMIT 1""",
                (val, val)
            )
            if row:
                return row["user_id"], None
    if m.chat.type == "private":
        return None, f"Укажи цель: ответь на сообщение или напиши <code>{command_word} @user</code> / <code>{command_word} ID</code>"
    return None, f"⚠️ В группе команда работает <b>ответом</b> или через <code>@username</code> / <code>ID</code>."


BTN_ARENA = "⚔️ Арена"
BTN_CASINO = "🎰 Казино"
BTN_GEAR = "🎒 Снаряжение"
BTN_TOP = "🏆 Топ"
MENU_TEXTS = {BTN_ARENA, BTN_CASINO, BTN_GEAR, BTN_TOP}

MENU_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_ARENA), KeyboardButton(text=BTN_CASINO)],
        [KeyboardButton(text=BTN_GEAR), KeyboardButton(text=BTN_TOP)],
    ],
    resize_keyboard=True,
)


def generate_arena_menu_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
    a = ARENAS[determine_arena(p["wins"])]
    text = (
        f"╔══════════════════════════╗\n      ⚔️ <b>АРЕНА ДУЭЛЯНТОВ</b>\n╚══════════════════════════╝\n\n"
        f"{E_TROPHY} Победы: <b>{p['wins']}</b>\n"
        f"{E_SKULL} Поражения: {p['losses']}\n"
        f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>\n"
        f"📍 {a['emoji']} <b>{a['name']}</b>\n\n"
        f"🥉 Бронза — 0–9 побед · <b>{ARENAS['bronze']['prize']} {E_CRYSTAL}</b>\n"
        f"🥈 Серебро — 10–29 побед · <b>{ARENAS['silver']['prize']} {E_CRYSTAL}</b>\n"
        f"🥇 Золото — 30+ побед · <b>{ARENAS['gold']['prize']} {E_CRYSTAL}</b>"
    )
    kb = build_colored_vertical_keyboard([
        ("🎲 Найти соперника", "arena:find", "success"),
        ("👹 Боссы", "arena:bosses", "danger"),
        ("📋 Список соперников", "arena:list", "primary"),
        ("🔎 Вызвать по нику", "arena:find_name", "primary"),
        ("🏆 Топ арен", "top:cur", "warning"),
        ("👤 Мой профиль", "duel:myprofile", "success"),
    ])
    return text, kb


def generate_bosses_menu_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
    lines = ["╔══════════════════════════╗\n      👹 <b>БОССЫ АРЕНЫ</b>\n╚══════════════════════════╝\n"]
    buttons = []
    for bkey, b in BOSSES.items():
        locked = p["wins"] < b["min_wins"]
        lock_text = f"🔒 нужен {b['min_wins']} {E_TROPHY}" if locked else f"награда ×{b['reward_mult']}"
        lines.append(f"{b['name']}\n  ❤️ HP {b['hp']} · ⚔️ {WEAPONS[b['weapon']]['name']}\n  {b['desc']}\n  → {lock_text}\n")
        if locked:
            buttons.append((f"{b['name']} 🔒", f"arena:boss_locked:{bkey}", "primary"))
        else:
            buttons.append((b["name"], f"arena:boss:{bkey}", "danger"))
    buttons.append((f"{E_BACK} Назад", "arena:menu", "success"))
    return "\n".join(lines), build_colored_vertical_keyboard(buttons)


def generate_gear_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
    w = WEAPONS[p["weapon"]]
    f = create_fighter_from_db(p)
    slots = get_player_armor_slots(p)
    lines = [
        f"🎒 <b>{esc(p['name'])}</b>", "",
        f"{E_TROPHY} Победы: <b>{p['wins']}</b>",
        f"{E_SKULL} Поражения: {p['losses']}",
        f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>",
        f"📍 {ARENAS[determine_arena(p['wins'])]['emoji']} {ARENAS[determine_arena(p['wins'])]['name']}", "",
        f"❤️ HP: <b>{f.max_hp}</b>",
        f"⚔️ Атака: <b>{f.base_weapon_dmg}</b>", "",
        "<b>⚔️ Оружие:</b>",
        f"  {w['emoji']} {w['name']} — <i>{w['description']}</i>",
        f"  Базовый урон: <b>{w['base_dmg']}</b>", "",
        "<b>🛡 Броня по слотам:</b>"
    ]
    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"  {ZONE_INFO[slot]['emoji']} {ZONE_INFO[slot]['name']}: {item['emoji']} <b>{item['name']}</b> (защита {item['df']})")
    kb = build_colored_vertical_keyboard([
        ("⚔️ Оружие", "gear:w", "danger"),
        ("🛡 Броня", "gear:armor_menu", "primary"),
        ("👤 Мой профиль", "duel:myprofile", "success"),
    ])
    return "\n".join(lines), kb


def generate_weapon_list(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
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
            style = "warning"
        buttons.append((f"{it['emoji']} {it['name']} · {label}", f"buy_weapon:{key}", style))
    buttons.append((f"{E_BACK} Назад", "gear:menu", "danger"))
    return "\n".join(lines), build_colored_vertical_keyboard(buttons)


def generate_armor_slot_menu(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
    slots = get_player_armor_slots(p)
    lines = ["🛡 <b>Броня — выбери часть тела</b>", f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>", ""]
    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"{ZONE_INFO[slot]['emoji']} <b>{ZONE_INFO[slot]['name']}</b> — {item['emoji']} {item['name']} (защита {item['df']})")
    kb = build_colored_vertical_keyboard([
        ("🧠 Голова", "gear:head", "danger"),
        ("🫀 Торс", "gear:torso", "primary"),
        ("💪 Руки", "gear:arms", "warning"),
        ("🦵 Ноги", "gear:legs", "success"),
        (f"{E_BACK} Назад", "gear:menu", "danger"),
    ])
    return "\n".join(lines), kb


def generate_armor_slot_list(uid: int, slot: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
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
        elif key in owned:
            label = "🎒 надеть"
            style = "primary"
        else:
            label = f"{item['price']}💎"
            style = "warning"
        buttons.append((f"{item['emoji']} {item['name']} · {label}", f"buy_armor:{slot}:{key}", style))
    buttons.append((f"{E_BACK} К слотам", "gear:armor_menu", "danger"))
    return "\n".join(lines), build_colored_vertical_keyboard(buttons)


def generate_top_screen(uid: int, arena_key: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
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
        you = " ← ты" if r["user_id"] == uid else ""
        lines.append(f"{mark} <b>{esc(r['name'])}</b> — {r['wins']} {E_TROPHY} / {r['losses']} {E_SKULL}{you}")
    me = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if me and all(r["user_id"] != uid for r in rows) and a["min_wins"] <= me["wins"] <= a["max_wins"]:
        rank_row = db.fetch_one(
            """SELECT COUNT(*) c FROM players
               WHERE is_bot=0 AND banned=0 AND wins BETWEEN ? AND ? AND wins > ?""",
            (a["min_wins"], a["max_wins"], me["wins"])
        )
        rank = (rank_row["c"] if rank_row else 0) + 1
        lines += ["…", f"{rank}. <b>{esc(me['name'])}</b> — {me['wins']} {E_TROPHY} / {me['losses']} {E_SKULL} ← ты"]
    lines += ["", f"{E_TROPHY} Победа: +1 и деньги. {E_SKULL} Поражение: −1 без награды."]
    kb = build_colored_vertical_keyboard([
        ("🥉 Бронза", "top:bronze", "warning"),
        ("🥈 Серебро", "top:silver", "primary"),
        ("🥇 Золото", "top:gold", "success"),
        (f"{E_BACK} Назад", "arena:menu", "danger"),
    ])
    return "\n".join(lines), kb


def generate_arena_list_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
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
            build_colored_vertical_keyboard([
                ("🎲 Найти", "arena:find", "success"),
                (f"{E_BACK} Назад", "arena:menu", "danger"),
            ])
        )
    buttons = []
    for r in rows:
        buttons.append((f"{r['name'][:16]} · {r['wins']}{E_TROPHY}/{r['losses']}{E_SKULL}", f"duel:pick:{r['user_id']}", "primary"))
    buttons.append((f"{E_BACK} Назад", "arena:menu", "danger"))
    return f"{a['emoji']} <b>{a['name']}</b> — соперники:", build_colored_vertical_keyboard(buttons)


def generate_profile_text(row: sqlite3.Row) -> str:
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
        f"⚡ Авто-приём вызовов: <b>{auto_accept}</b>", "",
        "<b>🛡 Броня:</b>"
    ]
    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"  {ZONE_INFO[slot]['emoji']} {ZONE_INFO[slot]['name']}: {item['emoji']} {item['name']} ({item['df']})")
    return "\n".join(lines)


def generate_profile_kb(uid: int) -> InlineKeyboardMarkup:
    return build_colored_vertical_keyboard([
        ("🎒 Снаряжение", "gear:menu", "primary"),
        (f"{E_SETTINGS} Настройки", "profile:settings", "warning"),
        (f"{E_BACK} Назад", "arena:menu", "danger"),
    ])


def generate_settings_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
    auto_accept = bool(p.get("auto_accept", 0))
    status = "✅ ВКЛЮЧЕНО" if auto_accept else "❌ ОТКЛЮЧЕНО"
    text = (
        f"{E_SETTINGS} <b>НАСТРОЙКИ</b>\n\n"
        f"👤 <b>{esc(p['name'])}</b>\n\n"
        f"⚡ <b>Авто-приём вызовов:</b>\n"
        f"{status}\n\n"
        f"<i>Если включено, то при вызове на дуэль бой начинается сразу, "
        f"без ожидания подтверждения.</i>"
    )
    kb = build_colored_vertical_keyboard([
        (f"{'🔴 Отключить' if auto_accept else '🟢 Включить'} авто-приём", "settings:toggle_auto_accept", "warning" if auto_accept else "success"),
        (f"{E_BACK} Назад к профилю", "profile:back", "danger"),
    ])
    return text, kb


def generate_duel_status_text(duel: Duel, for_uid: int, extra: str = "", timer_left: Optional[int] = None) -> str:
    role = duel.get_state_for(for_uid)
    me = duel.get_fighter(for_uid) or duel.a
    opp = duel.get_opponent(for_uid) or duel.b
    if role == "attacker" and duel.chosen_variant_idx is None:
        prompt = "🎯 <b>Твой ход</b> — выбери вариант атаки"
    elif role == "attacker":
        prompt = "🎯 <b>Твой ход</b> — выбери зону удара"
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
        f"{boss_line}┌─ 🔵 <b>ТЫ</b>\n{format_fighter_card(me)}\n└────────────\n\n"
        f"┌─ 🔴 <b>СОПЕРНИК</b>\n{format_fighter_card(opp)}\n└────────────\n\n"
        f"📜 <b>Последние действия:</b>\n{body}\n\n━━━━━━━━━━━━━━━━━━━━\n{prompt}"
        + (f"\n\n{extra}" if extra else "")
    )


def get_attack_variant_kb(uid: int) -> InlineKeyboardMarkup:
    duel = ACTIVE_DUELS.get(uid)
    if not duel:
        return build_colored_vertical_keyboard([])
    weapon = WEAPONS[duel.get_attacker().weapon]
    buttons = []
    for i, v in enumerate(weapon["variants"]):
        cd = duel.get_attacker().attack_cooldowns.get(i, 0)
        if cd > 0:
            text = f"⏳ {i + 1}. {v.name} (КД: {cd}р)"
            buttons.append((text, f"duel:variant_disabled:{i}", "primary"))
        else:
            effect_text = f" [{v.effect}]" if v.effect else ""
            text = f"{i + 1}. {v.name} · x{v.damage_mult}{effect_text}"
            buttons.append((text, f"duel:variant:{i}", "danger"))
    return build_colored_vertical_keyboard(buttons)


def get_attack_zone_kb() -> InlineKeyboardMarkup:
    return build_colored_vertical_keyboard([
        (f"{E_ZONE_HEAD} Голова ×1.5", "duel:atk:head", "danger"),
        (f"{E_ZONE_TORSO} Торс ×1.0", "duel:atk:torso", "warning"),
        (f"{E_ZONE_ARMS} Руки ×0.8", "duel:atk:arms", "primary"),
        (f"{E_ZONE_LEGS} Ноги ×0.9", "duel:atk:legs", "success"),
    ])


def get_defend_zone_kb() -> InlineKeyboardMarkup:
    return build_colored_vertical_keyboard([
        (f"{E_ZONE_HEAD} Голова", "duel:def:head", "danger"),
        (f"{E_ZONE_TORSO} Торс", "duel:def:torso", "warning"),
        (f"{E_ZONE_ARMS} Руки", "duel:def:arms", "primary"),
        (f"{E_ZONE_LEGS} Ноги", "duel:def:legs", "success"),
    ])


def get_finish_duel_kb() -> InlineKeyboardMarkup:
    return build_colored_vertical_keyboard([
        ("🔁 Ещё раз", "duel:again", "primary"),
        ("🏠 В главное меню", "arena:menu", "success"),
    ])


def get_challenge_accept_kb(challenger_id: int, target_id: int) -> InlineKeyboardMarkup:
    return build_colored_vertical_keyboard([
        (f"{E_ACCEPT} Принять вызов", f"challenge:accept:{challenger_id}:{target_id}", "success"),
        (f"{E_REJECT} Отклонить", f"challenge:reject:{challenger_id}:{target_id}", "danger"),
    ])


def get_challenge_waiting_kb(challenger_id: int, target_id: int) -> InlineKeyboardMarkup:
    return build_colored_vertical_keyboard([
        (f"{E_REFRESH} Обновить статус", f"challenge:refresh:{challenger_id}:{target_id}", "primary"),
        (f"{E_REJECT} Отменить вызов", f"challenge:cancel:{challenger_id}:{target_id}", "danger"),
    ])


def get_slots_mode_kb() -> InlineKeyboardMarkup:
    return build_colored_vertical_keyboard([
        (f"🎰 Джекпот (×10) — выпадет 1", "casino:slots:jackpot", "success"),
        (f"🎰 Промах (×1.5) — НЕ выпадет 1", "casino:slots:miss", "warning"),
        (f"{E_BACK} Назад", "casino:menu", "danger"),
    ])


def get_darts_mode_kb() -> InlineKeyboardMarkup:
    return build_colored_vertical_keyboard([
        (f"🎯 Попадание (×1.9) — зоны 3-6", "casino:darts:hit", "success"),
        (f"❌ Промах (×2) — зоны 1-2", "casino:darts:miss", "danger"),
        (f"{E_RED} Красная зона (×3) — 4", "casino:darts:red", "danger"),
        (f"{E_YELLOW} Белая/жёлтая зона (×4) — 3", "casino:darts:white", "warning"),
        (f"🎯 Яблочко (×10) — 6", "casino:darts:bullseye", "success"),
        (f"{E_BACK} Назад", "casino:menu", "primary"),
    ])


def get_basket_mode_kb() -> InlineKeyboardMarkup:
    return build_colored_vertical_keyboard([
        (f"🏀 Попадание (×1.9) — 5", "casino:basket:hit", "success"),
        (f"❌ Промах (×1.3) — 1-4", "casino:basket:miss", "danger"),
        (f"{E_BACK} Назад", "casino:menu", "primary"),
    ])


def get_bet_kb(game: str, mode: str) -> InlineKeyboardMarkup:
    bets = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
    buttons = []
    for b in bets:
        buttons.append((f"{b} 💎", f"casino:{game}:{mode}:bet:{b}", "primary"))
    buttons.append((f"{E_BACK} Назад", f"casino:{game}", "danger"))
    return build_colored_vertical_keyboard(buttons)


def get_roulette_mode_kb() -> InlineKeyboardMarkup:
    return build_colored_vertical_keyboard([
        ("🎨 На цвет (×2 / ×14)", "casino:roulette:color", "warning"),
        ("⚖️ Чёт / Нечет (×2)", "casino:roulette:even_odd", "primary"),
        ("📈 Половина (×2)", "casino:roulette:half", "success"),
        ("🔢 На число (×36)", "casino:roulette:number", "danger"),
        ("🎯 На дюжину (×3)", "casino:roulette:dozen", "warning"),
        (f"{E_BACK} Назад", "casino:menu", "primary"),
    ])


def get_roulette_color_kb(bet: int) -> InlineKeyboardMarkup:
    return build_colored_vertical_keyboard([
        (f"{E_RED} Красное (×2)", f"casino:roulette:color:red:{bet}", "danger"),
        (f"⚫ Чёрное (×2)", f"casino:roulette:color:black:{bet}", "primary"),
        (f"{E_GREEN} Зеро (×14)", f"casino:roulette:color:green:{bet}", "success"),
        (f"{E_BACK} Назад", "casino:roulette", "warning"),
    ])


def get_roulette_even_odd_kb(bet: int) -> InlineKeyboardMarkup:
    return build_colored_vertical_keyboard([
        ("🔵 Чёт (×2)", f"casino:roulette:even_odd:even:{bet}", "primary"),
        ("🔴 Нечет (×2)", f"casino:roulette:even_odd:odd:{bet}", "danger"),
        (f"{E_BACK} Назад", "casino:roulette", "warning"),
    ])


def get_roulette_half_kb(bet: int) -> InlineKeyboardMarkup:
    return build_colored_vertical_keyboard([
        ("📉 1-18 (×2)", f"casino:roulette:half:low:{bet}", "primary"),
        ("📈 19-36 (×2)", f"casino:roulette:half:high:{bet}", "success"),
        (f"{E_BACK} Назад", "casino:roulette", "warning"),
    ])


def get_roulette_number_kb(bet: int) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i in range(0, 37):
        row.append((f"{i} (×36)", f"casino:roulette:num:{bet}:{i}", "warning"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([(f"{E_BACK} Назад", "casino:roulette", "danger")])
    return build_colored_grid_keyboard(buttons)


def get_roulette_dozen_kb(bet: int) -> InlineKeyboardMarkup:
    return build_colored_vertical_keyboard([
        ("1️⃣ 1-12 (×3)", f"casino:roulette:dozen:1:{bet}", "primary"),
        ("2️⃣ 13-24 (×3)", f"casino:roulette:dozen:2:{bet}", "warning"),
        ("3️⃣ 25-36 (×3)", f"casino:roulette:dozen:3:{bet}", "success"),
        (f"{E_BACK} Назад", "casino:roulette", "danger"),
    ])


def generate_casino_menu(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
    text = (
        f"╔══════════════════════════╗\n      {E_SLOT} <b>КАЗИНО</b>\n╚══════════════════════════╝\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"<b>Выбери игру:</b>"
    )
    kb = build_colored_vertical_keyboard([
        (f"{E_SLOT} Слоты", "casino:slots", "warning"),
        (f"{E_DICE} Кости", "casino:dice", "primary"),
        (f"{E_DARTS} Дротик", "casino:darts", "success"),
        (f"{E_BASKET} Баскетбол", "casino:basket", "danger"),
        ("🎡 Рулетка", "casino:roulette", "warning"),
        (f"{E_COIN} Монетка (×2)", "casino:coin", "primary"),
        ("📊 Больше/Меньше (×1.9)", "casino:highlow", "success"),
        (f"{E_BACK} Назад", "arena:menu", "danger"),
    ])
    return text, kb


router = Router()


class RegistrationState(StatesGroup):
    waiting_for_name = State()


class DuelFindState(StatesGroup):
    waiting_for_target = State()


HELP_TEXT = (
    "╔══════════════════════════╗\n   ⚔️ <b>АРЕНА ДУЭЛЯНТОВ</b>\n╚══════════════════════════╝\n\n"
    "<b>📌 Как использовать команды:</b>\n"
    "• Ответь на сообщение игрока командой\n"
    "• Или: <code>команда @user</code> / <code>команда ID</code>\n\n"
    "<b>⚔️ Дуэли:</b>\n"
    "• <code>перчатка</code> или <code>перч</code> — вызов с подтверждением\n"
    "• <code>дуэль</code> или <code>бой</code> — прямой вызов (без подтверждения)\n"
    "• <code>профиль</code> или <code>фото</code> — статистика\n\n"
    "<b>💎 Экономика:</b>\n"
    "• <code>перевод [сумма]</code> — перевести кристаллы\n"
    "• <code>баланс</code> — проверить баланс\n\n"
    "<b>🎰 Казино:</b>\n"
    "• <code>сл джекпот [сумма]</code> — слоты на джекпот ×10\n"
    "• <code>сл промах [сумма]</code> — слоты на промах ×1.5\n"
    "• <code>дрот попадание [сумма]</code> — ×1.9\n"
    "• <code>дрот промах [сумма]</code> — ×2\n"
    "• <code>дрот красное [сумма]</code> — ×3\n"
    "• <code>дрот белое [сумма]</code> — ×4\n"
    "• <code>дрот яблочко [сумма]</code> — ×10\n"
    "• <code>баскет попадание [сумма]</code> — ×1.9\n"
    "• <code>баскет промах [сумма]</code> — ×1.3\n"
    "• <code>кости число [сумма] [1-6]</code> — ×6\n"
    "• <code>кости чет [сумма] [чет/нечет]</code> — ×2\n"
    "• <code>кости больше [сумма] [больше/меньше]</code> — ×2\n"
    "• <code>рул цвет [сумма] [к/ч/з]</code>\n"
    "• <code>рул чет [сумма] [чет/нечет]</code>\n"
    "• <code>рул половина [сумма] [верх/низ]</code>\n"
    "• <code>рул число [сумма] [0-36]</code> — ×36\n"
    "• <code>рул дюжина [сумма] [1/2/3]</code> — ×3\n"
    "• <code>мон [сумма] [о/р]</code>\n"
    "• <code>больше [сумма]</code> / <code>меньше [сумма]</code>\n\n"
    "<b>👹 Чатовые события:</b>\n"
    "• <code>атака</code> — ударить босса/караван\n"
    "• <code>событие</code> — статус текущего события\n\n"
    "<b>🎭 RP действия:</b>\n"
    "• <code>ударить</code>, <code>обнять</code>, <code>поцеловать</code>\n"
    "• <code>пнуть</code>, <code>погладить</code>, <code>укусить</code>\n"
    "• <code>пожать</code>, <code>толкнуть</code>, <code>кинуть</code>\n"
    "• <code>лечить</code>, <code>игнор</code>, <code>смеяться</code>\n"
    "• <code>танцевать</code>, <code>шлепнуть</code>, <code>обозвать</code>\n"
    "• <code>покормить</code>, <code>напоить</code>, <code>щекотать</code>\n\n"
    "<b>👑 Админ:</b>\n"
    "• <code>бан</code> / <code>разбан</code>\n"
    "• <code>выдать [сумма]</code>\n"
    "• <code>событие босс/караван/набег/дракон</code>\n"
    "• <code>босс [ключ]</code> — активировать босса\n"
    "• <code>следующее событие</code>\n"
    "• <code>промо создать/удалить/список</code>"
)


ADMIN_HELP_TEXT = (
    "╔══════════════════════════╗\n   👑 <b>ПОМОЩЬ АДМИНУ</b>\n╚══════════════════════════╝\n\n"
    "<b>📋 Команды администратора:</b>\n\n"
    "<b>👥 Управление игроками:</b>\n"
    "• <code>бан @user</code> или <code>бан ID</code> — забанить игрока\n"
    "• <code>разбан @user</code> или <code>разбан ID</code> — разбанить\n"
    "• <code>выдать 1000 @user</code> — выдать кристаллы\n\n"
    "<b>👹 Активация боссов и событий:</b>\n"
    "• <code>событие босс</code> — рейдовый босс (2000 HP)\n"
    "• <code>событие караван</code> — золотой караван (1000 HP)\n"
    "• <code>событие набег</code> — набег орков (3000 HP)\n"
    "• <code>событие дракон</code> — нашествие драконов (5000 HP)\n"
    "• <code>босс goblin</code> — гоблин-вождь (160 HP)\n"
    "• <code>босс dragon</code> — древний дракон (260 HP)\n"
    "• <code>босс lord</code> — древний лорд (380 HP)\n"
    "• <code>босс titan</code> — каменный титан (500 HP)\n"
    "• <code>босс demon_king</code> — король демонов (750 HP)\n\n"
    "<b>📅 Расписание событий:</b>\n"
    "• <code>следующее событие</code> — когда будет следующий босс\n"
    "• Авто-события запускаются каждые 4 часа\n\n"
    "<b>🎟 Промокоды:</b>\n"
    "• <code>промо создать [код] [💎] [🏆] [макс] [часы]</code>\n"
    "  Пример: <code>промо создать NEWYEAR 1000 5 100 24</code>\n"
    "• <code>промо удалить [код]</code>\n"
    "• <code>промо список</code>\n\n"
    "<b>📢 Рассылка:</b>\n"
    "• <code>рассылка [текст]</code> — отправить всем игрокам\n\n"
    "<b>💡 Коды боссов для команды <code>босс</code>:</b>\n"
    "• <code>goblin</code> — 👺 Гоблин-Вождь\n"
    "• <code>dragon</code> — 🐉 Древний Дракон\n"
    "• <code>lord</code> — 👹 Древний Лорд\n"
    "• <code>titan</code> — 🗿 Каменный Титан\n"
    "• <code>demon_king</code> — 😈 Король Демонов"
)


CHAT_HINT_TEXT = (
    f"{E_INFO} <b>Подсказка по командам:</b>\n\n"
    f"⚔️ <b>Дуэли:</b>\n"
    f"• <code>перчатка @user</code> — вызвать на бой\n"
    f"• <code>дуэль @user</code> — прямой вызов\n"
    f"• <code>профиль @user</code> — статистика\n\n"
    f"💎 <b>Экономика:</b>\n"
    f"• <code>перевод 100 @user</code> — перевод\n"
    f"• <code>баланс</code> — проверить баланс\n\n"
    f"🎰 <b>Казино:</b>\n"
    f"• <code>сл джекпот 100</code> — слоты\n"
    f"• <code>дрот попадание 100</code> — дартс\n"
    f"• <code>баскет попадание 100</code> — баскет\n"
    f"• <code>мон 100 о</code> — монетка\n"
    f"• <code>рул цвет 100 к</code> — рулетка\n\n"
    f"👹 <b>События:</b>\n"
    f"• <code>атака</code> — ударить босса\n"
    f"• <code>событие</code> — статус\n\n"
    f"🎭 <b>RP:</b>\n"
    f"• <code>ударить @user</code>\n"
    f"• <code>обнять @user</code>\n"
    f"• <code>поцеловать @user</code>\n\n"
    f"Напиши <code>help</code> для полного списка."
)


@router.message(CommandStart())
async def handle_start_command(m: Message, state: FSMContext) -> None:
    await state.clear()
    ensure_masked_bots_exist(Config.BOT_GENERATION_COUNT)
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if p:
        db.execute("UPDATE players SET username=?, last_active=? WHERE user_id=?",
                   (m.from_user.username, time.time(), m.from_user.id))
        if m.chat.type == "private":
            await m.answer(f"С возвращением, <b>{esc(p['name'])}</b>! Арена ждёт 👇", reply_markup=MENU_KB)
            await flush_notifications(m)
        else:
            await m.answer(f"С возвращением, <b>{esc(p['name'])}</b>! Пиши <code>help</code> для списка команд.")
        return
    await state.set_state(RegistrationState.waiting_for_name)
    await m.answer(
        "⚔️ <b>Добро пожаловать на Арену Дуэлянтов!</b>\n\n"
        "PvP + казино + боссы + чатовые ивенты.\n"
        "Уникальная броня на 4 части тела и множество видов оружия.\n\n"
        f"Как зовут твоего бойца? ({MIN_NAME_LENGTH}–{MAX_NAME_LENGTH} символов)",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(RegistrationState.waiting_for_name, F.text)
async def handle_registration_name(m: Message, state: FSMContext) -> None:
    name = " ".join(m.text.split())
    if not MIN_NAME_LENGTH <= len(name) <= MAX_NAME_LENGTH:
        await m.answer(f"Имя должно быть от {MIN_NAME_LENGTH} до {MAX_NAME_LENGTH} символов.")
        return
    if name.startswith("/"):
        await m.answer("Имя не может начинаться с '/'.")
        return
    if db.fetch_one("SELECT 1 FROM players WHERE LOWER(name)=LOWER(?)", (name,)):
        name = f"{name}{random.randint(1, 99)}"
    now = time.time()
    db.execute(
        """INSERT OR IGNORE INTO players
           (user_id, username, name, crystals, wins, losses, weapon,
            armor_head, armor_torso, armor_arms, armor_legs,
            weapons_owned, armors_owned, created, last_active)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (m.from_user.id, m.from_user.username, name, Config.START_CRYSTALS, 0, 0, START_WEAPON,
         "head_none", "torso_none", "arms_none", "legs_none", START_WEAPON,
         ",".join(START_ARMOR_KEYS), now, now)
    )
    ensure_masked_bots_exist(Config.BOT_GENERATION_COUNT)
    await state.clear()
    await m.answer(
        f"Боец <b>{esc(name)}</b> создан! 🎉\n\n"
        f"{E_CRYSTAL} Стартовый баланс: {Config.START_CRYSTALS}\n"
        f"⚔️ Оружие: {WEAPONS[START_WEAPON]['emoji']} {WEAPONS[START_WEAPON]['name']}",
        reply_markup=MENU_KB if m.chat.type == "private" else None
    )


@router.message(F.text.regexp(r"(?i)^(help|помощь|хелп)$"))
async def handle_help_command(m: Message) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        await m.answer("Сначала отправь /start в ЛС бота.")
        return
    kb = MENU_KB if m.chat.type == "private" else None
    await m.answer(HELP_TEXT, reply_markup=kb)


@router.message(F.text.regexp(r"(?i)^(админ помощь|админ инфо|admin help)$"))
async def handle_admin_help_command(m: Message) -> None:
    if not is_admin(m.from_user.id):
        await m.answer("🚫 Эта команда только для администраторов.")
        return
    await m.answer(ADMIN_HELP_TEXT)


async def flush_notifications(m: Message) -> None:
    rows = db.fetch_all(
        "SELECT id, text FROM notifications WHERE user_id=? AND seen=0 ORDER BY id LIMIT ?",
        (m.from_user.id, MAX_NOTIFICATIONS_PER_USER)
    )
    if not rows:
        return
    ids = [r["id"] for r in rows]
    if ids:
        placeholders = ",".join("?" * len(ids))
        db.execute(f"UPDATE notifications SET seen=1 WHERE id IN ({placeholders})", tuple(ids))
    await m.answer("📬 <b>Пока тебя не было:</b>\n\n" + "\n\n".join(r["text"] for r in rows))


def is_admin(uid: int) -> bool:
    return uid == Config.ADMIN_ID


def is_user_banned(uid: int) -> bool:
    p = db.fetch_one("SELECT banned FROM players WHERE user_id=?", (uid,))
    return bool(p and p["banned"])


def notify_player(uid: int, text: str) -> None:
    if uid <= 0:
        return
    db.execute("INSERT INTO notifications (user_id, text, ts) VALUES (?,?,?)", (uid, text, time.time()))


@router.message(F.text.in_(MENU_TEXTS))
async def on_menu_button(m: Message, state: FSMContext) -> None:
    if m.chat.type != "private":
        return
    await state.clear()
    if is_user_banned(m.from_user.id):
        await m.answer("🚫 Доступ закрыт.")
        return
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        await m.answer("Сначала отправь /start.")
        return
    db.execute("UPDATE players SET last_active=? WHERE user_id=?", (time.time(), m.from_user.id))
    await flush_notifications(m)
    if m.text == BTN_ARENA:
        text, kb = generate_arena_menu_screen(m.from_user.id)
        await m.answer(text, reply_markup=kb)
    elif m.text == BTN_CASINO:
        text, kb = generate_casino_menu(m.from_user.id)
        await m.answer(text, reply_markup=kb)
    elif m.text == BTN_GEAR:
        text, kb = generate_gear_screen(m.from_user.id)
        await m.answer(text, reply_markup=kb)
    elif m.text == BTN_TOP:
        p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
        if p:
            text, kb = generate_top_screen(m.from_user.id, determine_arena(p["wins"]))
            await m.answer(text, reply_markup=kb)


@router.message(F.text.regexp(r"(?i)^(перчатка|перч|glove|вызов)(\s|$)"))
async def cmd_challenge_duel(m: Message, bot: Bot) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        await m.answer("Сначала отправь /start в ЛС бота.")
        return
    if m.from_user.id in ACTIVE_DUELS:
        await m.answer("У тебя уже идёт бой.")
        return
    tid, err = resolve_command_target(m, m.text.split()[0])
    if err:
        await m.answer(err)
        return
    if tid == m.from_user.id:
        await m.answer("🤨 Нельзя вызвать себя.")
        return
    if tid < 0:
        await initiate_duel_message(m.from_user.id, tid, m, bot)
        return
    target = db.fetch_one("SELECT * FROM players WHERE user_id=?", (tid,))
    if not target or target["banned"]:
        await m.answer("Игрок не найден или забанен.")
        return
    if tid in ACTIVE_DUELS:
        await m.answer("Этот игрок уже в бою.")
        return
    if target.get("auto_accept", 0):
        await initiate_duel_message(m.from_user.id, tid, m, bot)
        return
    key = (m.from_user.id, tid)
    if key in PENDING_DUELS:
        await m.answer("Ты уже отправил этому игроку вызов.")
        return
    challenger_row = db.fetch_one("SELECT name FROM players WHERE user_id=?", (m.from_user.id,))
    challenger_name = challenger_row["name"]
    target_name = target["name"]
    challenger_msg, target_msg = await send_challenge_messages(
        m.from_user.id, tid, challenger_name, target_name, bot, direct=False
    )
    if not target_msg:
        await m.answer("Не удалось отправить вызов (игрок не начал бота).")
        return
    pending = PendingDuel(
        challenger_id=m.from_user.id,
        target_id=tid,
        challenger_msg_id=challenger_msg.message_id if challenger_msg else 0,
        target_msg_id=target_msg.message_id,
        chat_id=m.from_user.id,
        created_at=time.time(),
        direct=False,
    )
    PENDING_DUELS[key] = pending
    pending.timeout_task = asyncio.create_task(challenge_timeout_task(m.from_user.id, tid, bot))


@router.message(F.text.regexp(r"(?i)^(дуэль|бой|fight)(\s|$)"))
async def cmd_direct_duel(m: Message, bot: Bot) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        await m.answer("Сначала отправь /start в ЛС бота.")
        return
    if m.from_user.id in ACTIVE_DUELS:
        await m.answer("У тебя уже идёт бой.")
        return
    tid, err = resolve_command_target(m, m.text.split()[0])
    if err:
        await m.answer(err)
        return
    if tid == m.from_user.id:
        await m.answer("🤨 Нельзя вызвать себя.")
        return
    if tid < 0:
        await initiate_duel_message(m.from_user.id, tid, m, bot)
        return
    target = db.fetch_one("SELECT * FROM players WHERE user_id=?", (tid,))
    if not target or target["banned"]:
        await m.answer("Игрок не найден или забанен.")
        return
    if tid in ACTIVE_DUELS:
        await m.answer("Этот игрок уже в бою.")
        return
    challenger_row = db.fetch_one("SELECT name FROM players WHERE user_id=?", (m.from_user.id,))
    challenger_name = challenger_row["name"]
    target_name = target["name"]
    challenger_msg, target_msg = await send_challenge_messages(
        m.from_user.id, tid, challenger_name, target_name, bot, direct=True
    )
    if not target_msg:
        await m.answer("Не удалось отправить вызов.")
        return
    key = (m.from_user.id, tid)
    pending = PendingDuel(
        challenger_id=m.from_user.id,
        target_id=tid,
        challenger_msg_id=challenger_msg.message_id if challenger_msg else 0,
        target_msg_id=target_msg.message_id,
        chat_id=m.from_user.id,
        created_at=time.time(),
        direct=True,
    )
    PENDING_DUELS[key] = pending
    pending.timeout_task = asyncio.create_task(challenge_timeout_task(m.from_user.id, tid, bot))


@router.message(F.text.regexp(r"(?i)^(фото|профиль|stat)(\s|$)"))
async def cmd_show_profile(m: Message) -> None:
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


@router.message(F.text.regexp(r"(?i)^перевод(\s|$)"))
async def cmd_transfer(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    tid, err = resolve_command_target(m, "перевод")
    if err:
        await m.answer(err)
        return
    if tid == m.from_user.id:
        await m.answer("🤨 Себе переводить нельзя.")
        return
    target = db.fetch_one("SELECT * FROM players WHERE user_id=?", (tid,))
    if not target or target["banned"]:
        await m.answer("Игрок не найден или забанен.")
        return
    amount = next((int(x) for x in (m.text or "").split() if x.lstrip("-").isdigit()), None)
    if not amount or amount <= 0:
        await m.answer("Укажи сумму: <code>перевод 100 @user</code>")
        return
    if amount < Config.MIN_TRANSFER:
        await m.answer(f"Минимальная сумма перевода: {Config.MIN_TRANSFER} {E_CRYSTAL}")
        return
    if amount > Config.MAX_TRANSFER:
        await m.answer(f"Максимальная сумма перевода: {Config.MAX_TRANSFER} {E_CRYSTAL}")
        return
    if p["crystals"] < amount:
        await m.answer(f"Недостаточно кристаллов: у тебя {p['crystals']} {E_CRYSTAL}")
        return
    tax = int(amount * Config.TRANSFER_TAX)
    net_amount = amount - tax
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (amount, m.from_user.id))
    db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (net_amount, tid))
    await m.answer(
        f"{E_CRYSTAL} Переведено <b>{net_amount}</b> игроку <b>{esc(target['name'])}</b>.\n"
        f"💰 Налог: {tax} ({Config.TRANSFER_TAX * 100:.0f}%)"
    )
    notify_player(tid, f"{E_CRYSTAL} <b>{esc(p['name'])}</b> перевёл тебе <b>{net_amount}</b> кристаллов!")


@router.message(F.text.regexp(r"(?i)^атака(\s|$)"))
async def cmd_attack_event(m: Message) -> None:
    p = db.fetch_one("SELECT name FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    result = attack_chat_event(m.from_user.id, p["name"])
    if not result:
        await m.answer("Сейчас нет активных чатовых событий.")
        return
    await m.answer(result)


@router.message(F.text.regexp(r"(?i)^(событие|статус события)(\s|$)"))
async def cmd_event_status(m: Message) -> None:
    status = get_chat_event_status()
    if not status:
        await m.answer("Сейчас нет активных чатовых событий.")
        return
    await m.answer(f"📋 <b>Текущее событие:</b>\n\n{status}")


@router.message(F.text.regexp(r"(?i)^(баланс|balance|бал)(\s|$)"))
async def cmd_balance(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    await m.answer(
        f"👤 <b>{esc(p['name'])}</b>\n\n"
        f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>\n"
        f"{E_TROPHY} Победы: <b>{p['wins']}</b>\n"
        f"{E_SKULL} Поражения: <b>{p['losses']}</b>"
    )


async def process_rp_action(m: Message, action_key: str) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        await m.answer("Сначала /start в ЛС бота.")
        return
    tid, err = resolve_command_target(m, m.text.split()[0])
    if err:
        await m.answer(err)
        return
    if tid == m.from_user.id:
        await m.answer("🤨 Себе это делать странно.")
        return
    target = db.fetch_one("SELECT * FROM players WHERE user_id=?", (tid,))
    if not target or target["banned"]:
        await m.answer("Игрок не найден или забанен.")
        return
    cooldown_key = (m.from_user.id, tid, action_key)
    now = time.time()
    if now - RP_COOLDOWNS.get(cooldown_key, 0) < Config.RP_COOLDOWN:
        left = int(Config.RP_COOLDOWN - (now - RP_COOLDOWNS[cooldown_key])) + 1
        await m.answer(f"⏱ Подожди ещё {left} сек.")
        return
    RP_COOLDOWNS[cooldown_key] = now
    actor = db.fetch_one("SELECT name FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(
        generate_rp_text(m.from_user.id, actor["name"], tid, target["name"], action_key),
        parse_mode=ParseMode.HTML
    )


RP_MAPPINGS: Dict[str, List[str]] = {
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
    "игнорировать": ["игнор", "игнорировать", "ignore"],
    "смеяться": ["смеяться", "смех", "laugh"],
    "плакать": ["плакать", "плач", "cry"],
    "танцевать": ["танцевать", "танец", "dance"],
    "шлепнуть": ["шлепнуть", "шлеп", "slap"],
    "обозвать": ["обозвать", "обзывать", "insult"],
    "восхититься": ["восхититься", "восхищение", "admire"],
    "испугаться": ["испугаться", "испуг", "fear"],
    "подмигнуть": ["подмигнуть", "подмигивание", "wink"],
    "пожать_плечами": ["пожать_плечами", "плечи", "shrug"],
    "покормить": ["покормить", "кормить", "feed"],
    "напоить": ["напоить", "поить", "drink"],
    "щекотать": ["щекотать", "tickle"],
    "благословить": ["благословить", "bless"],
    "проклясть": ["проклясть", "curse"],
}


def _create_rp_handler(action: str) -> Callable:
    async def handler(m: Message) -> None:
        await process_rp_action(m, action)
    return handler


for action, variants in RP_MAPPINGS.items():
    pattern = r"(?i)^(" + "|".join(re.escape(v) for v in variants) + r")(\s|$)"
    router.message(F.text.regexp(pattern))(_create_rp_handler(action))


@router.message(F.text.regexp(r"(?i)^сл (джекпот|промах)(\s+)(\d+)$"))
async def cmd_chat_slots(m: Message, bot: Bot) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    parts = m.text.split()
    mode_raw = parts[1].lower()
    bet = int(parts[3])
    mode = "jackpot" if mode_raw == "джекпот" else "miss"
    result, err = await play_casino_slots_animated(m.chat.id, bet, m.from_user.id, bot, mode)
    if err:
        await m.answer(err)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^дрот (попадание|промах|красное|белое|жёлтое|желтое|яблочко)(\s+)(\d+)$"))
async def cmd_chat_darts(m: Message, bot: Bot) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    parts = m.text.split()
    mode_raw = parts[1].lower()
    bet = int(parts[3])
    mode_map = {
        "попадание": "hit",
        "промах": "miss",
        "красное": "red",
        "белое": "white",
        "жёлтое": "yellow",
        "желтое": "yellow",
        "яблочко": "bullseye",
    }
    mode = mode_map.get(mode_raw, "hit")
    result, err = await play_casino_darts_animated(m.chat.id, bet, m.from_user.id, bot, mode)
    if err:
        await m.answer(err)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^баскет (попадание|промах)(\s+)(\d+)$"))
async def cmd_chat_basket(m: Message, bot: Bot) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    parts = m.text.split()
    mode_raw = parts[1].lower()
    bet = int(parts[3])
    mode = "hit" if mode_raw == "попадание" else "miss"
    result, err = await play_casino_basketball_animated(m.chat.id, bet, m.from_user.id, bot, mode)
    if err:
        await m.answer(err)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^кости число(\s+)(\d+)(\s+)([1-6])$"))
async def cmd_dice_number(m: Message, bot: Bot) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    parts = m.text.split()
    bet = int(parts[2])
    number = int(parts[4])
    result, err = await play_casino_dice_game(m.chat.id, bet, m.from_user.id, bot, "number", number)
    if err:
        await m.answer(err)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^кости чет(\s+)(\d+)(\s+)(чет|нечет|четное|нечетное|ч|нч)$"))
async def cmd_dice_even_odd(m: Message, bot: Bot) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    parts = m.text.split()
    bet = int(parts[2])
    choice_raw = parts[4].lower()
    choice = "even" if choice_raw in ["чет", "четное", "ч"] else "odd"
    result, err = await play_casino_dice_game(m.chat.id, bet, m.from_user.id, bot, "even_odd", choice)
    if err:
        await m.answer(err)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^кости больше(\s+)(\d+)(\s+)(больше|меньше|б|м)$"))
async def cmd_dice_high_low(m: Message, bot: Bot) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    parts = m.text.split()
    bet = int(parts[2])
    choice_raw = parts[4].lower()
    choice = "high" if choice_raw in ["больше", "б"] else "low"
    result, err = await play_casino_dice_game(m.chat.id, bet, m.from_user.id, bot, "high_low", choice)
    if err:
        await m.answer(err)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


async def play_casino_dice_game(chat_id: int, bet: int, uid: int, bot: Bot, mode: str, value: Any = None) -> Tuple[Optional[str], Optional[str]]:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."
    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))
    sent_message = await bot.send_dice(chat_id=chat_id, emoji="🎲")
    dice_value = sent_message.dice.value
    win = False
    mult = 0
    if mode == "even_odd":
        is_even = (dice_value % 2 == 0)
        if (value == "even" and is_even) or (value == "odd" and not is_even):
            mult = 2
            win = True
    elif mode == "high_low":
        if (value == "high" and dice_value >= 4) or (value == "low" and dice_value <= 3):
            mult = 2
            win = True
    elif mode == "number":
        if dice_value == value:
            mult = 6
            win = True
    if win:
        payout = bet * mult
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
        return (
            f"🎲 <b>{dice_value}</b>\n\n"
            f"{E_TROPHY} <b>Победа ×{mult}!</b>\n"
            f"Вы выиграли: <b>+{payout} {E_CRYSTAL}</b>",
            None
        )
    else:
        return (
            f"🎲 <b>{dice_value}</b>\n\n"
            f"{E_SKULL} <b>Поражение.</b>\n"
            f"Вы проиграли: <b>−{bet} {E_CRYSTAL}</b>",
            None
        )


@router.message(F.text.regexp(r"(?i)^(монетка|coin|мон)(\s+)(\d+)(\s+)(орел|решка|о|р)$"))
async def cmd_chat_coin(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    parts = m.text.split()
    choice = "heads" if parts[3].lower() in ["орел", "о"] else "tails"
    result, err = play_casino_coin(m.from_user.id, int(parts[1]), choice)
    if err:
        await m.answer(err)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^рул цвет(\s+)(\d+)(\s+)(красное|черное|зеленое|к|ч|з)$"))
async def cmd_roulette_color(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    parts = m.text.split()
    bet = int(parts[2])
    color_raw = parts[4].lower()
    color = "red" if color_raw in ["красное", "к"] else ("black" if color_raw in ["черное", "ч"] else "green")
    result, err = play_casino_roulette(m.from_user.id, bet, "color", color)
    if err:
        await m.answer(err)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^рул чет(\s+)(\d+)(\s+)(чет|нечет|четное|нечетное|ч|нч)$"))
async def cmd_roulette_even_odd(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    parts = m.text.split()
    bet = int(parts[2])
    choice_raw = parts[4].lower()
    choice = "even" if choice_raw in ["чет", "четное", "ч"] else "odd"
    result, err = play_casino_roulette(m.from_user.id, bet, "even_odd", choice)
    if err:
        await m.answer(err)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^рул половина(\s+)(\d+)(\s+)(низ|верх|1-18|19-36|н|в)$"))
async def cmd_roulette_half(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    parts = m.text.split()
    bet = int(parts[2])
    choice_raw = parts[4].lower()
    choice = "low" if choice_raw in ["низ", "1-18", "н"] else "high"
    result, err = play_casino_roulette(m.from_user.id, bet, "half", choice)
    if err:
        await m.answer(err)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^рул число(\s+)(\d+)(\s+)(\d{1,2})$"))
async def cmd_roulette_number(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    parts = m.text.split()
    bet = int(parts[2])
    number = int(parts[4])
    if number < 0 or number > 36:
        await m.answer("Число должно быть от 0 до 36.")
        return
    result, err = play_casino_roulette(m.from_user.id, bet, "number", number)
    if err:
        await m.answer(err)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^рул дюжина(\s+)(\d+)(\s+)(1|2|3)$"))
async def cmd_roulette_dozen(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    parts = m.text.split()
    bet = int(parts[2])
    dozen = int(parts[4])
    result, err = play_casino_roulette(m.from_user.id, bet, "dozen", dozen)
    if err:
        await m.answer(err)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^(больше|high)(\s+)(\d+)$"))
async def cmd_chat_highlow_high(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    result, err = play_casino_highlow(m.from_user.id, int(m.text.split()[-1]), "high")
    if err:
        await m.answer(err)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^(меньше|low)(\s+)(\d+)$"))
async def cmd_chat_highlow_low(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    result, err = play_casino_highlow(m.from_user.id, int(m.text.split()[-1]), "low")
    if err:
        await m.answer(err)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^событие босс$"))
async def adm_spawn_boss(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    event = spawn_chat_event("boss", m.from_user.id)
    if not event:
        await m.answer("Событие уже активно!")
        return
    template = CHAT_EVENT_TEMPLATES["boss"]
    await m.answer(template["announce_text"].format(emoji=template["emoji"], hp=event.hp))


@router.message(F.text.regexp(r"(?i)^событие караван$"))
async def adm_spawn_caravan(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    event = spawn_chat_event("caravan", m.from_user.id)
    if not event:
        await m.answer("Событие уже активно!")
        return
    template = CHAT_EVENT_TEMPLATES["caravan"]
    await m.answer(template["announce_text"].format(emoji=template["emoji"], hp=event.hp))


@router.message(F.text.regexp(r"(?i)^событие набег$"))
async def adm_spawn_raid(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    event = spawn_chat_event("raid", m.from_user.id)
    if not event:
        await m.answer("Событие уже активно!")
        return
    template = CHAT_EVENT_TEMPLATES["raid"]
    await m.answer(template["announce_text"].format(emoji=template["emoji"], hp=event.hp))


@router.message(F.text.regexp(r"(?i)^событие дракон$"))
async def adm_spawn_dragon_raid(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    event = spawn_chat_event("dragon_raid", m.from_user.id)
    if not event:
        await m.answer("Событие уже активно!")
        return
    template = CHAT_EVENT_TEMPLATES["dragon_raid"]
    await m.answer(template["announce_text"].format(emoji=template["emoji"], hp=event.hp))


@router.message(F.text.regexp(r"(?i)^босс(\s+)(\w+)$"))
async def adm_spawn_boss_by_key(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    parts = m.text.split()
    bkey = parts[2].lower()
    if bkey not in BOSSES:
        await m.answer(
            f"❌ Босс <code>{bkey}</code> не найден.\n\n"
            f"<b>Доступные коды боссов:</b>\n"
            f"• <code>goblin</code> — 👺 Гоблин-Вождь\n"
            f"• <code>dragon</code> — 🐉 Древний Дракон\n"
            f"• <code>lord</code> — 👹 Древний Лорд\n"
            f"• <code>titan</code> — 🗿 Каменный Титан\n"
            f"• <code>demon_king</code> — 😈 Король Демонов\n\n"
            f"Пример: <code>босс goblin</code>"
        )
        return
    boss = BOSSES[bkey]
    event = spawn_chat_event("boss", m.from_user.id, custom_hp=boss["hp"])
    if not event:
        await m.answer("Событие уже активно!")
        return
    await m.answer(
        f"🚨 <b>ВНИМАНИЕ!</b>\n\n"
        f"{boss['name']} появился в чате!\n"
        f"❤️ HP: {event.hp}\n\n"
        f"Используйте команду <code>атака</code>!"
    )


@router.message(F.text.regexp(r"(?i)^(следующее событие|когда босс)$"))
async def adm_next_event(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    global NEXT_SCHEDULED_EVENT
    if NEXT_SCHEDULED_EVENT and NEXT_SCHEDULED_EVENT > time.time():
        time_left = int(NEXT_SCHEDULED_EVENT - time.time())
        hours = time_left // 3600
        minutes = (time_left % 3600) // 60
        seconds = time_left % 60
        await m.answer(
            f"⏰ <b>Следующее запланированное событие:</b>\n\n"
            f"Через: <b>{hours}ч {minutes}м {seconds}с</b>\n"
            f"Время: <b>{time.strftime('%d.%m.%Y %H:%M:%S', time.localtime(NEXT_SCHEDULED_EVENT))}</b>"
        )
    else:
        await m.answer("📅 Следующее событие будет через 4 часа (автоматически).")


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
    amount = next((int(x) for x in (m.text or "").split() if x.lstrip("-").isdigit()), None)
    if not amount:
        await m.answer("Укажи сумму: <code>выдать 1000 @user</code>")
        return
    db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (amount, tid))
    await m.answer(f"✅ Выдано {amount} {E_CRYSTAL} игроку <code>{tid}</code>.")
    notify_player(tid, f"🎁 Админ выдал тебе {amount} {E_CRYSTAL}")


@router.message(F.text.regexp(r"(?i)^промо создать(\s+)(\S+)(\s+)(\d+)(\s+)(\d+)(\s+)(\d+)(\s+)(\d+)$"))
async def adm_promo_create(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    parts = m.text.split()
    code = parts[2]
    crystals = int(parts[4])
    wins = int(parts[6])
    max_uses = int(parts[8])
    hours = int(parts[10])
    success, message = create_promo_code(code, crystals, wins, max_uses, hours, m.from_user.id)
    await m.answer(message)


@router.message(F.text.regexp(r"(?i)^промо удалить(\s+)(\S+)$"))
async def adm_promo_delete(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    code = m.text.split()[2].strip().upper()
    existing = db.fetch_one("SELECT code FROM promo_codes WHERE code=?", (code,))
    if not existing:
        await m.answer(f"❌ Промокод <code>{code}</code> не найден.")
        return
    db.execute("UPDATE promo_codes SET active=0 WHERE code=?", (code,))
    await m.answer(f"✅ Промокод <code>{code}</code> деактивирован.")


@router.message(F.text.regexp(r"(?i)^промо список$"))
async def adm_promo_list(m: Message) -> None:
    if not is_admin(m.from_user.id):
        return
    promos = db.fetch_all("SELECT * FROM promo_codes ORDER BY created_at DESC LIMIT 20")
    if not promos:
        await m.answer(f"{E_PROMO} Промокодов пока нет.")
        return
    lines = [f"{E_PROMO} <b>ВСЕ ПРОМОКОДЫ ({len(promos)})</b>\n"]
    now = time.time()
    for i, p in enumerate(promos, 1):
        is_expired = p["expires_at"] < now
        is_maxed = p["current_uses"] >= p["max_uses"]
        status = "✅" if (p["active"] and not is_expired and not is_maxed) else ("⏰" if is_expired else ("🚫" if is_maxed else "❌"))
        expires_str = time.strftime("%d.%m %H:%M", time.localtime(p["expires_at"]))
        lines.append(f"{i}. {status} <code>{p['code']}</code>")
        rewards = []
        if p["reward_crystals"] > 0:
            rewards.append(f"💎{p['reward_crystals']}")
        if p["reward_wins"] > 0:
            rewards.append(f"🏆{p['reward_wins']}")
        lines.append(f"   Награда: {' + '.join(rewards) if rewards else '—'}")
        lines.append(f"   Активаций: {p['current_uses']}/{p['max_uses']}")
        lines.append(f"   Истекает: {expires_str}\n")
    await m.answer("\n".join(lines))


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
            await asyncio.sleep(BROADCAST_DELAY)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except Exception:
            pass
    await m.answer(f"✅ Рассылка завершена. Доставлено: {ok_count} игрокам.")


async def send_challenge_messages(
    challenger_id: int,
    target_id: int,
    challenger_name: str,
    target_name: str,
    bot: Bot,
    direct: bool = False
) -> Tuple[Optional[Message], Optional[Message]]:
    challenger_msg = None
    target_msg = None
    if direct:
        target_text = (
            f"{E_GLOVE} <b>ПРЯМОЙ ВЫЗОВ НА ДУЭЛЬ!</b>\n\n"
            f"👤 <b>{esc(challenger_name)}</b> вызывает тебя на бой!\n"
            f"⏳ У тебя <b>{Config.CHALLENGE_TIMEOUT}</b> секунд, чтобы принять или отклонить.\n\n"
            f"Выбери действие:"
        )
        challenger_text = (
            f"{E_GLOVE} <b>ПРЯМОЙ ВЫЗОВ ОТПРАВЛЕН!</b>\n\n"
            f"👤 Твой запрос доставлен игроку <b>{esc(target_name)}</b>.\n"
            f"⏳ Ожидай ответа <b>{Config.CHALLENGE_TIMEOUT}</b> секунд.\n\n"
            f"Ты можешь обновить статус или отменить вызов:"
        )
    else:
        target_text = (
            f"{E_GLOVE} <b>ВЫЗОВ НА ДУЭЛЬ!</b>\n\n"
            f"👤 <b>{esc(challenger_name)}</b> кинул тебе перчатку!\n"
            f"⏳ У тебя <b>{Config.CHALLENGE_TIMEOUT}</b> секунд, чтобы принять или отклонить.\n\n"
            f"Выбери действие:"
        )
        challenger_text = (
            f"{E_GLOVE} <b>ВЫЗОВ ОТПРАВЛЕН!</b>\n\n"
            f"👤 Твой запрос доставлен игроку <b>{esc(target_name)}</b>.\n"
            f"⏳ Ожидай ответа <b>{Config.CHALLENGE_TIMEOUT}</b> секунд.\n\n"
            f"Ты можешь обновить статус или отменить вызов:"
        )
    try:
        target_msg = await bot.send_message(
            target_id,
            target_text,
            reply_markup=get_challenge_accept_kb(challenger_id, target_id),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"Failed to send challenge to target {target_id}: {e}")
        return None, None
    try:
        challenger_msg = await bot.send_message(
            challenger_id,
            challenger_text,
            reply_markup=get_challenge_waiting_kb(challenger_id, target_id),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"Failed to send confirmation to challenger {challenger_id}: {e}")
    return challenger_msg, target_msg


async def challenge_timeout_task(challenger_id: int, target_id: int, bot: Bot) -> None:
    await asyncio.sleep(Config.CHALLENGE_TIMEOUT)
    key = (challenger_id, target_id)
    pending = PENDING_DUELS.get(key)
    if not pending:
        return
    await safe_edit_message_by_id(
        bot, pending.chat_id, pending.target_msg_id,
        f"{E_SKULL} <b>ВЫЗОВ ОТКЛОНЁН</b>\n\n⏱ Время ожидания истекло.\nИгрок не успел принять вызов.",
        None
    )
    await safe_edit_message_by_id(
        bot, pending.chat_id, pending.challenger_msg_id,
        f"{E_SKULL} <b>ВЫЗОВ ОТКЛОНЁН</b>\n\n⏱ Время ожидания истекло.\nИгрок не ответил на твой вызов.",
        None
    )
    PENDING_DUELS.pop(key, None)


@router.callback_query(F.data.regexp(r"^challenge:accept:(-?\d+):(-?\d+)$"))
async def cb_challenge_accept(cb: CallbackQuery, bot: Bot) -> None:
    parts = cb.data.split(":")
    challenger_id = int(parts[2])
    target_id = int(parts[3])
    if cb.from_user.id != target_id:
        await cb.answer("Это не твой вызов!", show_alert=True)
        return
    key = (challenger_id, target_id)
    pending = PENDING_DUELS.get(key)
    if not pending:
        await cb.answer("Вызов уже не действителен.", show_alert=True)
        return
    if pending.timeout_task and not pending.timeout_task.done():
        pending.timeout_task.cancel()
    challenger_row = db.fetch_one("SELECT name FROM players WHERE user_id=?", (challenger_id,))
    target_row = db.fetch_one("SELECT name FROM players WHERE user_id=?", (target_id,))
    challenger_name = challenger_row["name"] if challenger_row else "Неизвестный"
    target_name = target_row["name"] if target_row else "Неизвестный"
    await safe_edit_message_by_id(
        bot, pending.chat_id, pending.target_msg_id,
        f"{E_TROPHY} <b>ВЫЗОВ ПРИНЯТ!</b>\n\n⚔️ <b>{esc(target_name)}</b> принял вызов <b>{esc(challenger_name)}</b>!\nБой начинается...",
        None
    )
    await safe_edit_message_by_id(
        bot, pending.chat_id, pending.challenger_msg_id,
        f"{E_TROPHY} <b>ВЫЗОВ ПРИНЯТ!</b>\n\n⚔️ <b>{esc(target_name)}</b> принял твой вызов!\nБой начинается...",
        None
    )
    PENDING_DUELS.pop(key, None)
    await cb.answer()
    await asyncio.sleep(1.5)
    await initiate_duel_message(challenger_id, target_id, cb.message, bot)


@router.callback_query(F.data.regexp(r"^challenge:reject:(-?\d+):(-?\d+)$"))
async def cb_challenge_reject(cb: CallbackQuery, bot: Bot) -> None:
    parts = cb.data.split(":")
    challenger_id = int(parts[2])
    target_id = int(parts[3])
    if cb.from_user.id != target_id:
        await cb.answer("Это не твой вызов!", show_alert=True)
        return
    key = (challenger_id, target_id)
    pending = PENDING_DUELS.get(key)
    if not pending:
        await cb.answer("Вызов уже не действителен.", show_alert=True)
        return
    if pending.timeout_task and not pending.timeout_task.done():
        pending.timeout_task.cancel()
    challenger_row = db.fetch_one("SELECT name FROM players WHERE user_id=?", (challenger_id,))
    target_row = db.fetch_one("SELECT name FROM players WHERE user_id=?", (target_id,))
    challenger_name = challenger_row["name"] if challenger_row else "Неизвестный"
    target_name = target_row["name"] if target_row else "Неизвестный"
    await safe_edit_message_by_id(
        bot, pending.chat_id, pending.target_msg_id,
        f"{E_SKULL} <b>ВЫЗОВ ОТКЛОНЁН</b>\n\nТы отклонил вызов от <b>{esc(challenger_name)}</b>.",
        None
    )
    await safe_edit_message_by_id(
        bot, pending.chat_id, pending.challenger_msg_id,
        f"{E_SKULL} <b>ВЫЗОВ ОТКЛОНЁН</b>\n\n<b>{esc(target_name)}</b> отклонил твой вызов.",
        None
    )
    PENDING_DUELS.pop(key, None)
    await cb.answer("Вызов отклонён.")


@router.callback_query(F.data.regexp(r"^challenge:cancel:(-?\d+):(-?\d+)$"))
async def cb_challenge_cancel(cb: CallbackQuery, bot: Bot) -> None:
    parts = cb.data.split(":")
    challenger_id = int(parts[2])
    target_id = int(parts[3])
    if cb.from_user.id != challenger_id:
        await cb.answer("Это не твой вызов!", show_alert=True)
        return
    key = (challenger_id, target_id)
    pending = PENDING_DUELS.get(key)
    if not pending:
        await cb.answer("Вызов уже не действителен.", show_alert=True)
        return
    if pending.timeout_task and not pending.timeout_task.done():
        pending.timeout_task.cancel()
    challenger_row = db.fetch_one("SELECT name FROM players WHERE user_id=?", (challenger_id,))
    target_row = db.fetch_one("SELECT name FROM players WHERE user_id=?", (target_id,))
    challenger_name = challenger_row["name"] if challenger_row else "Неизвестный"
    target_name = target_row["name"] if target_row else "Неизвестный"
    await safe_edit_message_by_id(
        bot, pending.chat_id, pending.target_msg_id,
        f"{E_SKULL} <b>ВЫЗОВ ОТМЕНЁН</b>\n\n<b>{esc(challenger_name)}</b> отменил вызов.",
        None
    )
    await safe_edit_message_by_id(
        bot, pending.chat_id, pending.challenger_msg_id,
        f"{E_SKULL} <b>ВЫЗОВ ОТМЕНЁН</b>\n\nТы отменил свой вызов.",
        None
    )
    PENDING_DUELS.pop(key, None)
    await cb.answer("Вызов отменён.")


@router.callback_query(F.data.regexp(r"^challenge:refresh:(-?\d+):(-?\d+)$"))
async def cb_challenge_refresh(cb: CallbackQuery, bot: Bot) -> None:
    parts = cb.data.split(":")
    challenger_id = int(parts[2])
    target_id = int(parts[3])
    if cb.from_user.id != challenger_id:
        await cb.answer("Это не твой вызов!", show_alert=True)
        return
    key = (challenger_id, target_id)
    pending = PENDING_DUELS.get(key)
    if not pending:
        await cb.answer("Вызов уже не действителен.", show_alert=True)
        return
    target_row = db.fetch_one("SELECT name FROM players WHERE user_id=?", (target_id,))
    target_name = target_row["name"] if target_row else "Неизвестный"
    time_left = max(0, int(Config.CHALLENGE_TIMEOUT - (time.time() - pending.created_at)))
    await safe_edit_message_by_id(
        bot, pending.chat_id, pending.challenger_msg_id,
        f"{E_GLOVE} <b>ВЫЗОВ ОЖИДАЕТ ОТВЕТА</b>\n\n"
        f"👤 Игрок <b>{esc(target_name)}</b> получил твой вызов.\n"
        f"⏳ Осталось времени: <b>{time_left}</b> сек.\n\n"
        f"Ты можешь обновить статус или отменить вызов:",
        get_challenge_waiting_kb(challenger_id, target_id)
    )
    await cb.answer(f"Осталось {time_left} сек.")


@router.callback_query(F.data == "profile:settings")
async def cb_profile_settings(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    text, kb = generate_settings_screen(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "settings:toggle_auto_accept")
async def cb_toggle_auto_accept(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT auto_accept FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p:
        await cb.answer("Сначала /start", show_alert=True)
        return
    new_value = 0 if p["auto_accept"] else 1
    db.execute("UPDATE players SET auto_accept=? WHERE user_id=?", (new_value, cb.from_user.id))
    text, kb = generate_settings_screen(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer("✅ Настройки сохранены")


@router.callback_query(F.data == "profile:back")
async def cb_profile_back(cb: CallbackQuery) -> None:
    row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not row:
        await cb.answer("Сначала /start", show_alert=True)
        return
    await safe_edit_message(cb, generate_profile_text(row), generate_profile_kb(cb.from_user.id))
    await cb.answer()


@router.callback_query(F.data == "casino:menu")
async def cb_casino_menu(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    text, kb = generate_casino_menu(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:slots")
async def cb_casino_slots(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_SLOT} <b>СЛОТЫ</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"<b>Выбери тип ставки:</b>"
    )
    await safe_edit_message(cb, text, get_slots_mode_kb())
    await cb.answer()


@router.callback_query(F.data == "casino:slots:jackpot")
async def cb_casino_slots_jackpot(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"🎰 <b>СЛОТЫ — ДЖЕКПОТ (×10)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"<b>Правила:</b>\n"
        f"• Выпадает число от 1 до 64\n"
        f"• <b>1</b> = ДЖЕКПОТ ×10\n"
        f"• Другие значения = проигрыш\n\n"
        f"Выбери ставку:"
    )
    await safe_edit_message(cb, text, get_bet_kb("slots", "jackpot"))
    await cb.answer()


@router.callback_query(F.data == "casino:slots:miss")
async def cb_casino_slots_miss(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"🎰 <b>СЛОТЫ — ПРОМАХ (×1.5)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"<b>Правила:</b>\n"
        f"• Выпадает число от 1 до 64\n"
        f"• <b>НЕ 1</b> = выигрыш ×1.5\n"
        f"• <b>1</b> = проигрыш\n\n"
        f"Выбери ставку:"
    )
    await safe_edit_message(cb, text, get_bet_kb("slots", "miss"))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:slots:(jackpot|miss):bet:(\d+)$"))
async def cb_casino_slots_bet(cb: CallbackQuery, bot: Bot) -> None:
    parts = cb.data.split(":")
    mode = parts[3]
    bet = int(parts[5])
    result, err = await play_casino_slots_animated(cb.message.chat.id, bet, cb.from_user.id, bot, mode)
    if err:
        await cb.answer(err, show_alert=True)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_colored_vertical_keyboard([
        ("🔁 Ещё раз", f"casino:slots:{mode}", "success"),
        (f"{E_BACK} К выбору типа", "casino:slots", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "danger"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:darts")
async def cb_casino_darts(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_DARTS} <b>ДРОТИК</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"<b>Зоны дротика:</b>\n"
        f"• ❌ 1-2: промах мимо мишени\n"
        f"• {E_YELLOW} 3: жёлтая зона (внешнее кольцо)\n"
        f"• {E_RED} 4: красная зона (среднее кольцо)\n"
        f"• {E_GREEN} 5: зелёная зона (внутреннее кольцо)\n"
        f"• 🎯 6: яблочко (центр)\n\n"
        f"<b>Выбери тип ставки:</b>"
    )
    await safe_edit_message(cb, text, get_darts_mode_kb())
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:darts:(hit|miss|red|white|bullseye)$"))
async def cb_casino_darts_mode(cb: CallbackQuery) -> None:
    mode = cb.data.split(":")[3]
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    mode_names = {
        "hit": "ПОПАДАНИЕ (×1.9)",
        "miss": "ПРОМАХ (×2)",
        "red": "КРАСНАЯ ЗОНА (×3)",
        "white": "БЕЛАЯ/ЖЁЛТАЯ ЗОНА (×4)",
        "bullseye": "ЯБЛОЧКО (×10)",
    }
    text = (
        f"{E_DARTS} <b>ДРОТИК — {mode_names[mode]}</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    await safe_edit_message(cb, text, get_bet_kb("darts", mode))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:darts:(hit|miss|red|white|bullseye):bet:(\d+)$"))
async def cb_casino_darts_bet(cb: CallbackQuery, bot: Bot) -> None:
    parts = cb.data.split(":")
    mode = parts[3]
    bet = int(parts[5])
    result, err = await play_casino_darts_animated(cb.message.chat.id, bet, cb.from_user.id, bot, mode)
    if err:
        await cb.answer(err, show_alert=True)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_colored_vertical_keyboard([
        ("🔁 Ещё раз", f"casino:darts:{mode}", "success"),
        (f"{E_BACK} К выбору типа", "casino:darts", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "danger"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:basket")
async def cb_casino_basket(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_BASKET} <b>БАСКЕТБОЛ</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"<b>Значения:</b>\n"
        f"• ❌ 1-4: промах\n"
        f"• 🏀 5: попадание (слэм-данк)\n\n"
        f"<b>Выбери тип ставки:</b>"
    )
    await safe_edit_message(cb, text, get_basket_mode_kb())
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:basket:(hit|miss)$"))
async def cb_casino_basket_mode(cb: CallbackQuery) -> None:
    mode = cb.data.split(":")[3]
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    mode_names = {
        "hit": "ПОПАДАНИЕ (×1.9)",
        "miss": "ПРОМАХ (×1.3)",
    }
    text = (
        f"{E_BASKET} <b>БАСКЕТБОЛ — {mode_names[mode]}</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    await safe_edit_message(cb, text, get_bet_kb("basket", mode))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:basket:(hit|miss):bet:(\d+)$"))
async def cb_casino_basket_bet(cb: CallbackQuery, bot: Bot) -> None:
    parts = cb.data.split(":")
    mode = parts[3]
    bet = int(parts[5])
    result, err = await play_casino_basketball_animated(cb.message.chat.id, bet, cb.from_user.id, bot, mode)
    if err:
        await cb.answer(err, show_alert=True)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_colored_vertical_keyboard([
        ("🔁 Ещё раз", f"casino:basket:{mode}", "success"),
        (f"{E_BACK} К выбору типа", "casino:basket", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "danger"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:dice")
async def cb_casino_dice(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_DICE} <b>КОСТИ</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"<b>Выбери режим игры:</b>"
    )
    kb = build_colored_vertical_keyboard([
        ("🔢 На число (×6)", "casino:dice:number", "danger"),
        ("⚖️ Чёт / Нечет (×2)", "casino:dice:even_odd", "primary"),
        ("📈 Больше / Меньше (×2)", "casino:dice:high_low", "success"),
        (f"{E_BACK} Назад", "casino:menu", "warning"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:dice:number")
async def cb_casino_dice_number(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_DICE} <b>КОСТИ — НА ЧИСЛО (×6)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    buttons = [(f"{b} 💎", f"casino:dice:number:bet:{b}", "primary") for b in [10, 25, 50, 100, 250, 500, 1000]]
    buttons.append((f"{E_BACK} Назад", "casino:dice", "danger"))
    await safe_edit_message(cb, text, build_colored_vertical_keyboard(buttons))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:dice:number:bet:(\d+)$"))
async def cb_casino_dice_number_bet(cb: CallbackQuery) -> None:
    bet = int(cb.data.split(":")[4])
    text = (
        f"{E_DICE} <b>КОСТИ — НА ЧИСЛО</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери число от 1 до 6:"
    )
    buttons = [(f"{i} (×6)", f"casino:dice:num:{bet}:{i}", "warning") for i in range(1, 7)]
    buttons.append((f"{E_BACK} Назад", "casino:dice:number", "danger"))
    await safe_edit_message(cb, text, build_colored_vertical_keyboard(buttons))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:dice:num:(\d+):(\d+)$"))
async def cb_casino_dice_num(cb: CallbackQuery, bot: Bot) -> None:
    parts = cb.data.split(":")
    bet = int(parts[3])
    number = int(parts[4])
    result, err = await play_casino_dice_game(cb.message.chat.id, bet, cb.from_user.id, bot, "number", number)
    if err:
        await cb.answer(err, show_alert=True)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_colored_vertical_keyboard([
        ("🔁 Ещё раз", "casino:dice:number", "success"),
        (f"{E_BACK} К режимам", "casino:dice", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "danger"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:dice:even_odd")
async def cb_casino_dice_even_odd(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_DICE} <b>КОСТИ — ЧЁТ/НЕЧЕТ (×2)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    buttons = [(f"{b} 💎", f"casino:dice:even_odd:bet:{b}", "primary") for b in [10, 25, 50, 100, 250, 500, 1000]]
    buttons.append((f"{E_BACK} Назад", "casino:dice", "danger"))
    await safe_edit_message(cb, text, build_colored_vertical_keyboard(buttons))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:dice:even_odd:bet:(\d+)$"))
async def cb_casino_dice_even_odd_bet(cb: CallbackQuery) -> None:
    bet = int(cb.data.split(":")[4])
    text = (
        f"{E_DICE} <b>КОСТИ — ЧЁТ/НЕЧЕТ</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери:"
    )
    await safe_edit_message(cb, text, get_roulette_even_odd_kb(bet).replace("casino:roulette:even_odd", "casino:dice:even_odd"))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:dice:(even|odd):(\d+)$"))
async def cb_casino_dice_even_odd_play(cb: CallbackQuery, bot: Bot) -> None:
    parts = cb.data.split(":")
    choice = parts[3]
    bet = int(parts[4])
    result, err = await play_casino_dice_game(cb.message.chat.id, bet, cb.from_user.id, bot, "even_odd", choice)
    if err:
        await cb.answer(err, show_alert=True)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_colored_vertical_keyboard([
        ("🔁 Ещё раз", "casino:dice:even_odd", "success"),
        (f"{E_BACK} К режимам", "casino:dice", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "danger"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:dice:high_low")
async def cb_casino_dice_high_low(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_DICE} <b>КОСТИ — БОЛЬШЕ/МЕНЬШЕ (×2)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"• Больше: 4, 5, 6\n"
        f"• Меньше: 1, 2, 3\n\n"
        f"Выбери ставку:"
    )
    buttons = [(f"{b} 💎", f"casino:dice:high_low:bet:{b}", "primary") for b in [10, 25, 50, 100, 250, 500, 1000]]
    buttons.append((f"{E_BACK} Назад", "casino:dice", "danger"))
    await safe_edit_message(cb, text, build_colored_vertical_keyboard(buttons))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:dice:high_low:bet:(\d+)$"))
async def cb_casino_dice_high_low_bet(cb: CallbackQuery) -> None:
    bet = int(cb.data.split(":")[4])
    text = (
        f"{E_DICE} <b>КОСТИ — БОЛЬШЕ/МЕНЬШЕ</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери:"
    )
    kb = build_colored_vertical_keyboard([
        ("📈 Больше (4-6) (×2)", f"casino:dice:high:{bet}", "success"),
        ("📉 Меньше (1-3) (×2)", f"casino:dice:low:{bet}", "danger"),
        (f"{E_BACK} Назад", "casino:dice:high_low", "primary"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:dice:(high|low):(\d+)$"))
async def cb_casino_dice_high_low_play(cb: CallbackQuery, bot: Bot) -> None:
    parts = cb.data.split(":")
    choice = parts[3]
    bet = int(parts[4])
    result, err = await play_casino_dice_game(cb.message.chat.id, bet, cb.from_user.id, bot, "high_low", choice)
    if err:
        await cb.answer(err, show_alert=True)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_colored_vertical_keyboard([
        ("🔁 Ещё раз", "casino:dice:high_low", "success"),
        (f"{E_BACK} К режимам", "casino:dice", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "danger"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:roulette")
async def cb_casino_roulette(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"🎡 <b>РУЛЕТКА</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"<b>Выбери режим игры:</b>"
    )
    await safe_edit_message(cb, text, get_roulette_mode_kb())
    await cb.answer()


@router.callback_query(F.data == "casino:roulette:color")
async def cb_roulette_color(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"🎨 <b>РУЛЕТКА — НА ЦВЕТ</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"• 🔴 Красное / ⚫ Чёрное = ×2\n"
        f"• 🟢 Зеро = ×14\n\n"
        f"Выбери ставку:"
    )
    buttons = [(f"{b} 💎", f"casino:roulette:color:bet:{b}", "primary") for b in [10, 25, 50, 100, 250, 500, 1000]]
    buttons.append((f"{E_BACK} Назад", "casino:roulette", "danger"))
    await safe_edit_message(cb, text, build_colored_vertical_keyboard(buttons))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:color:bet:(\d+)$"))
async def cb_roulette_color_bet(cb: CallbackQuery) -> None:
    bet = int(cb.data.split(":")[4])
    text = (
        f"🎨 <b>РУЛЕТКА — НА ЦВЕТ</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери цвет:"
    )
    await safe_edit_message(cb, text, get_roulette_color_kb(bet))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:color:(red|black|green):(\d+)$"))
async def cb_roulette_color_play(cb: CallbackQuery) -> None:
    parts = cb.data.split(":")
    color = parts[3]
    bet = int(parts[4])
    result, err = play_casino_roulette(cb.from_user.id, bet, "color", color)
    if err:
        await cb.answer(err, show_alert=True)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_colored_vertical_keyboard([
        ("🔁 Ещё раз", "casino:roulette:color", "success"),
        (f"{E_BACK} К режимам", "casino:roulette", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "danger"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:roulette:even_odd")
async def cb_roulette_even_odd(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"⚖️ <b>РУЛЕТКА — ЧЁТ/НЕЧЕТ (×2)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    buttons = [(f"{b} 💎", f"casino:roulette:even_odd:bet:{b}", "primary") for b in [10, 25, 50, 100, 250, 500, 1000]]
    buttons.append((f"{E_BACK} Назад", "casino:roulette", "danger"))
    await safe_edit_message(cb, text, build_colored_vertical_keyboard(buttons))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:even_odd:bet:(\d+)$"))
async def cb_roulette_even_odd_bet(cb: CallbackQuery) -> None:
    bet = int(cb.data.split(":")[4])
    text = (
        f"⚖️ <b>РУЛЕТКА — ЧЁТ/НЕЧЕТ</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери:"
    )
    await safe_edit_message(cb, text, get_roulette_even_odd_kb(bet))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:even_odd:(even|odd):(\d+)$"))
async def cb_roulette_even_odd_play(cb: CallbackQuery) -> None:
    parts = cb.data.split(":")
    choice = parts[3]
    bet = int(parts[4])
    result, err = play_casino_roulette(cb.from_user.id, bet, "even_odd", choice)
    if err:
        await cb.answer(err, show_alert=True)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_colored_vertical_keyboard([
        ("🔁 Ещё раз", "casino:roulette:even_odd", "success"),
        (f"{E_BACK} К режимам", "casino:roulette", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "danger"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:roulette:half")
async def cb_roulette_half(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"📈 <b>РУЛЕТКА — ПОЛОВИНА (×2)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"• 1-18 (низ)\n"
        f"• 19-36 (верх)\n\n"
        f"Выбери ставку:"
    )
    buttons = [(f"{b} 💎", f"casino:roulette:half:bet:{b}", "primary") for b in [10, 25, 50, 100, 250, 500, 1000]]
    buttons.append((f"{E_BACK} Назад", "casino:roulette", "danger"))
    await safe_edit_message(cb, text, build_colored_vertical_keyboard(buttons))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:half:bet:(\d+)$"))
async def cb_roulette_half_bet(cb: CallbackQuery) -> None:
    bet = int(cb.data.split(":")[4])
    text = (
        f"📈 <b>РУЛЕТКА — ПОЛОВИНА</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери:"
    )
    await safe_edit_message(cb, text, get_roulette_half_kb(bet))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:half:(low|high):(\d+)$"))
async def cb_roulette_half_play(cb: CallbackQuery) -> None:
    parts = cb.data.split(":")
    choice = parts[3]
    bet = int(parts[4])
    result, err = play_casino_roulette(cb.from_user.id, bet, "half", choice)
    if err:
        await cb.answer(err, show_alert=True)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_colored_vertical_keyboard([
        ("🔁 Ещё раз", "casino:roulette:half", "success"),
        (f"{E_BACK} К режимам", "casino:roulette", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "danger"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:roulette:number")
async def cb_roulette_number(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"🔢 <b>РУЛЕТКА — НА ЧИСЛО (×36)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    buttons = [(f"{b} 💎", f"casino:roulette:number:bet:{b}", "primary") for b in [10, 25, 50, 100, 250, 500, 1000]]
    buttons.append((f"{E_BACK} Назад", "casino:roulette", "danger"))
    await safe_edit_message(cb, text, build_colored_vertical_keyboard(buttons))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:number:bet:(\d+)$"))
async def cb_roulette_number_bet(cb: CallbackQuery) -> None:
    bet = int(cb.data.split(":")[4])
    text = (
        f"🔢 <b>РУЛЕТКА — НА ЧИСЛО</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери число от 0 до 36:"
    )
    await safe_edit_message(cb, text, get_roulette_number_kb(bet))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:num:(\d+):(\d+)$"))
async def cb_roulette_number_play(cb: CallbackQuery) -> None:
    parts = cb.data.split(":")
    bet = int(parts[3])
    number = int(parts[4])
    result, err = play_casino_roulette(cb.from_user.id, bet, "number", number)
    if err:
        await cb.answer(err, show_alert=True)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_colored_vertical_keyboard([
        ("🔁 Ещё раз", "casino:roulette:number", "success"),
        (f"{E_BACK} К режимам", "casino:roulette", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "danger"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:roulette:dozen")
async def cb_roulette_dozen(cb: CallbackQuery) -> None:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"🎯 <b>РУЛЕТКА — НА ДЮЖИНУ (×3)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    buttons = [(f"{b} 💎", f"casino:roulette:dozen:bet:{b}", "primary") for b in [10, 25, 50, 100, 250, 500, 1000]]
    buttons.append((f"{E_BACK} Назад", "casino:roulette", "danger"))
    await safe_edit_message(cb, text, build_colored_vertical_keyboard(buttons))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:dozen:bet:(\d+)$"))
async def cb_roulette_dozen_bet(cb: CallbackQuery) -> None:
    bet = int(cb.data.split(":")[4])
    text = (
        f"🎯 <b>РУЛЕТКА — НА ДЮЖИНУ</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери дюжину:"
    )
    await safe_edit_message(cb, text, get_roulette_dozen_kb(bet))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:dozen:(\d+):(\d+)$"))
async def cb_roulette_dozen_play(cb: CallbackQuery) -> None:
    parts = cb.data.split(":")
    dozen = int(parts[3])
    bet = int(parts[4])
    result, err = play_casino_roulette(cb.from_user.id, bet, "dozen", dozen)
    if err:
        await cb.answer(err, show_alert=True)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_colored_vertical_keyboard([
        ("🔁 Ещё раз", "casino:roulette:dozen", "success"),
        (f"{E_BACK} К режимам", "casino:roulette", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "danger"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:coin")
async def cb_casino_coin(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_COIN} <b>МОНЕТКА (×2)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    buttons = [(f"{b} 💎", f"casino:coin:bet:{b}", "primary") for b in [10, 25, 50, 100, 250, 500, 1000]]
    buttons.append((f"{E_BACK} Назад", "casino:menu", "danger"))
    await safe_edit_message(cb, text, build_colored_vertical_keyboard(buttons))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:coin:bet:(\d+)$"))
async def cb_casino_coin_bet(cb: CallbackQuery) -> None:
    bet = int(cb.data.split(":")[3])
    text = (
        f"{E_COIN} <b>МОНЕТКА</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери:"
    )
    kb = build_colored_vertical_keyboard([
        ("🔵 Орёл (×2)", f"casino:coin:heads:{bet}", "primary"),
        ("🔴 Решка (×2)", f"casino:coin:tails:{bet}", "danger"),
        (f"{E_BACK} Назад", "casino:coin", "warning"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:coin:(heads|tails):(\d+)$"))
async def cb_casino_coin_play(cb: CallbackQuery) -> None:
    parts = cb.data.split(":")
    choice = parts[3]
    bet = int(parts[4])
    result, err = play_casino_coin(cb.from_user.id, bet, choice)
    if err:
        await cb.answer(err, show_alert=True)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_colored_vertical_keyboard([
        ("🔁 Ещё раз", "casino:coin", "success"),
        (f"{E_BACK} В казино", "casino:menu", "danger"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:highlow")
async def cb_casino_highlow(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"📊 <b>БОЛЬШЕ/МЕНЬШЕ (×1.9)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"• Число от 1 до 100\n"
        f"• Больше: 51-100\n"
        f"• Меньше: 1-49\n"
        f"• 50 = возврат ставки\n\n"
        f"Выбери ставку:"
    )
    buttons = [(f"{b} 💎", f"casino:highlow:bet:{b}", "primary") for b in [10, 25, 50, 100, 250, 500, 1000]]
    buttons.append((f"{E_BACK} Назад", "casino:menu", "danger"))
    await safe_edit_message(cb, text, build_colored_vertical_keyboard(buttons))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:highlow:bet:(\d+)$"))
async def cb_casino_highlow_bet(cb: CallbackQuery) -> None:
    bet = int(cb.data.split(":")[3])
    text = (
        f"📊 <b>БОЛЬШЕ/МЕНЬШЕ</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери:"
    )
    kb = build_colored_vertical_keyboard([
        ("📈 Больше (51-100) (×1.9)", f"casino:highlow:high:{bet}", "success"),
        ("📉 Меньше (1-49) (×1.9)", f"casino:highlow:low:{bet}", "danger"),
        (f"{E_BACK} Назад", "casino:highlow", "primary"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:highlow:(high|low):(\d+)$"))
async def cb_casino_highlow_play(cb: CallbackQuery) -> None:
    parts = cb.data.split(":")
    choice = parts[3]
    bet = int(parts[4])
    result, err = play_casino_highlow(cb.from_user.id, bet, choice)
    if err:
        await cb.answer(err, show_alert=True)
        return
    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_colored_vertical_keyboard([
        ("🔁 Ещё раз", "casino:highlow", "success"),
        (f"{E_BACK} В казино", "casino:menu", "danger"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


def initiate_duel(
    a_id: int, b_id: int, is_boss: bool = False,
    boss_key: Optional[str] = None, reward_mult: int = 1
) -> Optional[Duel]:
    a_row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (a_id,))
    if not a_row:
        return None
    fa = create_fighter_from_db(a_row)
    if is_boss and boss_key and boss_key in BOSSES:
        boss_data = BOSSES[boss_key]
        fb = Fighter(
            name=boss_data["name"], max_hp=boss_data["hp"], hp=boss_data["hp"],
            weapon=boss_data["weapon"], armor_slots=boss_data["armor_keys"],
        )
    else:
        b_row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (b_id,))
        if not b_row:
            return None
        fb = create_fighter_from_db(b_row)
    duel = Duel(
        a_id=a_id, b_id=b_id, a=fa, b=fb,
        attacker_is_a=random.random() < 0.5,
        is_boss=is_boss, boss_key=boss_key, reward_mult=reward_mult,
    )
    first_attacker = fa.name if duel.attacker_is_a else fb.name
    prefix = f"{E_BOSS} <b>БОСС</b> " if is_boss else ""
    duel.add_log(f"{prefix}Бой начался! Первым атакует <b>{first_attacker}</b>.")
    ACTIVE_DUELS[a_id] = duel
    if b_id > 0:
        ACTIVE_DUELS[b_id] = duel
    return duel


async def initiate_duel_message(
    aid: int, bid: int, m: Message, bot: Bot,
    is_boss: bool = False, boss_key: Optional[str] = None, reward_mult: int = 1
) -> None:
    if bid == aid:
        await m.answer("🤨 Нельзя драться с самим собой.")
        return
    if aid in ACTIVE_DUELS:
        await m.answer("У тебя уже идёт активный бой.")
        return
    duel = initiate_duel(aid, bid, is_boss, boss_key, reward_mult)
    if not duel:
        await m.answer("Не удалось начать бой.")
        return
    role = duel.get_state_for(aid)
    if role == "attacker":
        await m.answer(
            generate_duel_status_text(duel, aid, timer_left=Config.TURN_TIMEOUT),
            reply_markup=get_attack_variant_kb(aid)
        )
        start_duel_timer(duel, aid, "attacker", bot)
    else:
        atk_id = duel.get_attacker_id()
        if atk_id < 0:
            variant_idx = bot_decide_attack_variant(duel.get_attacker())
            duel.chosen_variant_idx = variant_idx
            duel.atk_zone = bot_decide_attack_zone(duel.get_attacker(), duel.get_defender())
            await m.answer(
                generate_duel_status_text(duel, aid, extra="⚔️ Соперник уже выбрал удар.", timer_left=Config.TURN_TIMEOUT),
                reply_markup=get_defend_zone_kb()
            )
            start_duel_timer(duel, aid, "defender", bot)
        else:
            await m.answer(
                generate_duel_status_text(duel, aid, extra="⏳ Соперник выбирает удар…"),
                reply_markup=build_colored_vertical_keyboard([(f"{E_REFRESH} Обновить", "duel:refresh", "primary")])
            )
    if bid > 0 and not is_boss:
        attacker_name = db.fetch_one("SELECT name FROM players WHERE user_id=?", (aid,))["name"]
        notify_player(bid, f"{E_GLOVE} <b>{esc(attacker_name)}</b> кинул тебе перчатку!")


async def process_duel_round(
    duel: Duel, bot: Bot, cb: Optional[CallbackQuery],
    atk_zone: str, def_zone: Optional[str]
) -> None:
    if duel.finished:
        return
    stop_duel_timer(duel)
    attacker = duel.get_attacker()
    defender = duel.get_defender()
    duel.add_log(f"── Раунд {duel.round_no} ──")
    duel.add_log(f"⚔️ {attacker.name} → {ZONE_INFO[atk_zone]['emoji']} {ZONE_INFO[atk_zone]['name']}")
    if def_zone:
        duel.add_log(f"🛡 {defender.name} → {ZONE_INFO[def_zone]['emoji']} {ZONE_INFO[def_zone]['name']}")
    process_dots(attacker, duel.log)
    if not attacker.is_alive():
        await finalize_duel(duel, winner_is_a=(attacker is duel.b), bot=bot)
        return
    execute_attack_phase(attacker, defender, atk_zone, def_zone, duel.chosen_variant_idx, duel.log)
    if not defender.is_alive():
        await finalize_duel(duel, winner_is_a=(defender is duel.a), bot=bot)
        return
    duel.atk_zone = None
    duel.def_zone = None
    duel.chosen_variant_idx = None
    duel.attacker_is_a = not duel.attacker_is_a
    duel.round_no += 1
    attacker.reduce_cooldowns()
    defender.reduce_cooldowns()
    if duel.round_no - duel.bot_last_block_round > 4:
        duel.bot_block_streak = 0
    await start_next_duel_round(duel, bot)


async def start_next_duel_round(duel: Duel, bot: Bot) -> None:
    if duel.finished:
        return
    atk_id = duel.get_attacker_id()
    def_id = duel.get_defender_id()
    if atk_id > 0:
        await bot.send_message(
            atk_id,
            generate_duel_status_text(duel, atk_id, extra="🎯 Твой ход — выбери вариант атаки.", timer_left=Config.TURN_TIMEOUT),
            reply_markup=get_attack_variant_kb(atk_id)
        )
        start_duel_timer(duel, atk_id, "attacker", bot)
    else:
        variant_idx = bot_decide_attack_variant(duel.get_attacker())
        duel.chosen_variant_idx = variant_idx
        duel.atk_zone = bot_decide_attack_zone(duel.get_attacker(), duel.get_defender())
        weapon_data = WEAPONS[duel.get_attacker().weapon]
        variant_name = weapon_data["variants"][variant_idx].name
        duel.add_log(f"⚔️ {duel.get_attacker().name} использует [{variant_name}]")
        if def_id > 0:
            await bot.send_message(
                def_id,
                generate_duel_status_text(duel, def_id, extra=f"{E_SHIELD} Соперник атакует — выбери зону защиты.", timer_left=Config.TURN_TIMEOUT),
                reply_markup=get_defend_zone_kb()
            )
            start_duel_timer(duel, def_id, "defender", bot)


async def finalize_duel(duel: Duel, winner_is_a: bool, bot: Bot, reason: str = "ko") -> None:
    if duel.finished:
        return
    aid, bid = duel.a_id, duel.b_id
    a_row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (aid,))
    if not a_row:
        terminate_duel(duel)
        return
    mult = duel.reward_mult if duel.is_boss else 1
    if winner_is_a:
        db.execute("UPDATE players SET wins=wins+1, total_duels=total_duels+1 WHERE user_id=?", (aid,))
        current_wins = db.fetch_one("SELECT wins FROM players WHERE user_id=?", (aid,))["wins"]
        prize = ARENAS[determine_arena(current_wins)]["prize"] * mult
        db.execute("UPDATE players SET crystals=crystals+?, total_crystals_earned=total_crystals_earned+? WHERE user_id=?",
                   (prize, prize, aid))
        if bid and bid > 0:
            db.execute(
                "UPDATE players SET losses=losses+1, total_duels=total_duels+1, "
                "wins=CASE WHEN wins>0 THEN wins-1 ELSE 0 END WHERE user_id=?",
                (bid,)
            )
            a_name = a_row["name"]
            notify_player(bid, f"{E_SKULL} <b>{esc(a_name)}</b> одолел тебя. −1 {E_TROPHY}.")
        result_line = f"{E_TROPHY} <b>ТЫ ПОБЕДИЛ!</b>  +1 {E_TROPHY}  ·  +{prize} {E_CRYSTAL}"
    else:
        if bid and bid > 0:
            db.execute("UPDATE players SET wins=wins+1, total_duels=total_duels+1 WHERE user_id=?", (bid,))
            current_wins_b = db.fetch_one("SELECT wins FROM players WHERE user_id=?", (bid,))["wins"]
            prize_b = ARENAS[determine_arena(current_wins_b)]["prize"] * mult
            db.execute("UPDATE players SET crystals=crystals+?, total_crystals_earned=total_crystals_earned+? WHERE user_id=?",
                       (prize_b, prize_b, bid))
            a_name = a_row["name"]
            notify_player(bid, f"{E_TROPHY} <b>{esc(a_name)}</b> проиграл тебе! +1 {E_TROPHY}, +{prize_b} {E_CRYSTAL}")
        db.execute(
            "UPDATE players SET losses=losses+1, total_duels=total_duels+1, "
            "wins=CASE WHEN wins>0 THEN wins-1 ELSE 0 END WHERE user_id=?",
            (aid,)
        )
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
        f"{E_CRYSTAL} Кристаллы: <b>{format_number(new_a['crystals'])}</b>\n"
        f"📍 {a_arena['emoji']} {a_arena['name']}"
        f"{reason_line}\n\nВыбери действие:"
    )
    try:
        await bot.send_message(aid, text, reply_markup=get_finish_duel_kb())
    except Exception as e:
        logging.error(f"Failed to send duel result to {aid}: {e}")
    if bid and bid > 0:
        new_b = db.fetch_one("SELECT * FROM players WHERE user_id=?", (bid,))
        if new_b:
            b_arena = ARENAS[determine_arena(new_b["wins"])]
            res_b = f"{E_SKULL} <b>ТЫ ПРОИГРАЛ.</b>  −1 {E_TROPHY}" if winner_is_a else f"{E_TROPHY} <b>ТЫ ПОБЕДИЛ!</b>  +1 {E_TROPHY}"
            text_b = (
                f"╔══════════════════════════╗\n        ⚔️ <b>ИТОГ БОЯ</b>\n╚══════════════════════════╝\n\n"
                f"{res_b}\n\n"
                f"{E_TROPHY} Кубки: <b>{new_b['wins']}</b>\n"
                f"{E_SKULL} Поражения: <b>{new_b['losses']}</b>\n"
                f"{E_CRYSTAL} Кристаллы: <b>{format_number(new_b['crystals'])}</b>\n"
                f"📍 {b_arena['emoji']} {b_arena['name']}"
                f"{reason_line}\n\nВыбери действие:"
            )
            try:
                await bot.send_message(bid, text_b, reply_markup=get_finish_duel_kb())
            except Exception as e:
                logging.error(f"Failed to send duel result to {bid}: {e}")


@router.callback_query(F.data == "arena:menu")
async def cb_arena_menu(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    text, kb = generate_arena_menu_screen(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "arena:bosses")
async def cb_arena_bosses(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    text, kb = generate_bosses_menu_screen(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^arena:boss_locked:\w+$"))
async def cb_arena_boss_locked(cb: CallbackQuery) -> None:
    bkey = cb.data.split(":")[2]
    if bkey in BOSSES:
        await cb.answer(f"Нужно {BOSSES[bkey]['min_wins']} {E_TROPHY} для этого босса.", show_alert=True)
    else:
        await cb.answer("Босс не найден.", show_alert=True)


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
        await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, timer_left=Config.TURN_TIMEOUT), get_attack_variant_kb(cb.from_user.id))
        start_duel_timer(duel, cb.from_user.id, "attacker", bot)
    else:
        variant_idx = bot_decide_attack_variant(duel.get_attacker())
        duel.chosen_variant_idx = variant_idx
        duel.atk_zone = bot_decide_attack_zone(duel.get_attacker(), duel.get_defender())
        await safe_edit_message(
            cb,
            generate_duel_status_text(duel, cb.from_user.id, extra="⚔️ Босс уже выбрал удар.", timer_left=Config.TURN_TIMEOUT),
            get_defend_zone_kb()
        )
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
    await initiate_duel_message(cb.from_user.id, oid, cb.message, bot)
    await cb.answer()


@router.callback_query(F.data == "arena:list")
async def cb_arena_list(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    text, kb = generate_arena_list_screen(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
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
    await initiate_duel_message(cb.from_user.id, tid, cb.message, bot)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^duel:profile:-?\d+$"))
async def cb_duel_profile(cb: CallbackQuery) -> None:
    tid = int(cb.data.split(":")[2])
    row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (tid,))
    if not row:
        await cb.answer("Игрок не найден.", show_alert=True)
        return
    await safe_edit_message(
        cb,
        generate_profile_text(row),
        build_colored_vertical_keyboard([
            (f"{E_BACK} Назад", "arena:list", "danger"),
            (f"⚔️ Вызвать на бой", f"duel:pick:{tid}", "success"),
        ])
    )
    await cb.answer()


@router.callback_query(F.data == "duel:myprofile")
async def cb_my_profile(cb: CallbackQuery) -> None:
    row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not row:
        await cb.answer("Сначала /start", show_alert=True)
        return
    await safe_edit_message(cb, generate_profile_text(row), generate_profile_kb(cb.from_user.id))
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
    await initiate_duel_message(cb.from_user.id, oid, cb.message, bot)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^duel:variant:\d+$"))
async def cb_duel_variant(cb: CallbackQuery, bot: Bot) -> None:
    duel = ACTIVE_DUELS.get(cb.from_user.id)
    if not duel or duel.finished or duel.get_state_for(cb.from_user.id) != "attacker":
        await cb.answer("Неверное состояние боя.", show_alert=True)
        return
    if duel.chosen_variant_idx is not None:
        await cb.answer("Вариант уже выбран.", show_alert=True)
        return
    variant_idx = int(cb.data.split(":")[2])
    if variant_idx in duel.get_attacker().attack_cooldowns:
        await cb.answer("Эта атака на перезарядке!", show_alert=True)
        return
    weapon_data = WEAPONS[duel.get_attacker().weapon]
    if variant_idx >= len(weapon_data["variants"]):
        await cb.answer("Неверный вариант атаки.", show_alert=True)
        return
    duel.chosen_variant_idx = variant_idx
    await safe_edit_message(
        cb,
        generate_duel_status_text(duel, cb.from_user.id, extra="🎯 Теперь выбери зону удара.", timer_left=Config.TURN_TIMEOUT),
        get_attack_zone_kb()
    )
    await cb.answer("Вариант атаки выбран.")


@router.callback_query(F.data.regexp(r"^duel:variant_disabled:\d+$"))
async def cb_duel_variant_disabled(cb: CallbackQuery) -> None:
    await cb.answer("Эта атака на перезарядке!", show_alert=True)


@router.callback_query(F.data.regexp(r"^duel:atk:(head|torso|arms|legs)$"))
async def cb_duel_attack(cb: CallbackQuery, bot: Bot) -> None:
    duel = ACTIVE_DUELS.get(cb.from_user.id)
    if not duel or duel.finished:
        await cb.answer("Бой не найден или завершён.", show_alert=True)
        return
    if duel.get_state_for(cb.from_user.id) != "attacker":
        await cb.answer("Сейчас не твой ход атаковать.", show_alert=True)
        return
    if duel.chosen_variant_idx is None:
        await cb.answer("Сначала выбери вариант атаки.", show_alert=True)
        return
    stop_duel_timer(duel)
    duel.atk_zone = cb.data.split(":")[2]
    def_id = duel.get_defender_id()
    if def_id < 0:
        bot_is_a = (def_id == duel.a_id)
        bot_fighter = duel.a if bot_is_a else duel.b
        if bot_decide_to_defend(duel, bot_is_a):
            duel.def_zone = bot_decide_defend_zone(duel.get_attacker(), bot_fighter)
            duel.bot_last_block_round = duel.round_no
            duel.bot_block_streak += 1
            duel.add_log(f"🛡 {bot_fighter.name} встаёт в защиту")
        else:
            duel.def_zone = None
            duel.bot_block_streak = 0
        await process_duel_round(duel, bot, cb=cb, atk_zone=duel.atk_zone, def_zone=duel.def_zone)
    else:
        await bot.send_message(
            def_id,
            generate_duel_status_text(duel, def_id, extra=f"⚔️ {duel.get_attacker().name} выбрал зону удара!", timer_left=Config.TURN_TIMEOUT),
            reply_markup=get_defend_zone_kb()
        )
        start_duel_timer(duel, def_id, "defender", bot)
        await safe_edit_message(
            cb,
            generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Ждём защиту соперника…"),
            build_colored_vertical_keyboard([(f"{E_REFRESH} Обновить", "duel:refresh", "primary")])
        )
    await cb.answer("Зона удара выбрана.")


@router.callback_query(F.data.regexp(r"^duel:def:(head|torso|arms|legs)$"))
async def cb_duel_defend(cb: CallbackQuery, bot: Bot) -> None:
    duel = ACTIVE_DUELS.get(cb.from_user.id)
    if not duel or duel.finished:
        await cb.answer("Бой не найден или завершён.", show_alert=True)
        return
    if duel.get_state_for(cb.from_user.id) != "defender":
        await cb.answer("Сейчас ты не защищаешься.", show_alert=True)
        return
    if not duel.atk_zone:
        await cb.answer("Атакующий ещё не выбрал зону.", show_alert=True)
        return
    stop_duel_timer(duel)
    duel.def_zone = cb.data.split(":")[2]
    await process_duel_round(duel, bot, cb=cb, atk_zone=duel.atk_zone, def_zone=duel.def_zone)


@router.callback_query(F.data == "duel:refresh")
async def cb_duel_refresh(cb: CallbackQuery) -> None:
    duel = ACTIVE_DUELS.get(cb.from_user.id)
    if not duel or duel.finished:
        await cb.answer("Бой не найден или завершён.", show_alert=True)
        return
    role = duel.get_state_for(cb.from_user.id)
    time_left = max(0, int(round(duel.timer_deadline - time.time()))) if duel.timer_for == cb.from_user.id else None
    if role == "attacker":
        if duel.chosen_variant_idx is None:
            await safe_edit_message(
                cb,
                generate_duel_status_text(duel, cb.from_user.id, extra="🎯 Выбери вариант атаки.", timer_left=time_left),
                get_attack_variant_kb(cb.from_user.id)
            )
        else:
            await safe_edit_message(
                cb,
                generate_duel_status_text(duel, cb.from_user.id, extra="🎯 Теперь выбери зону удара.", timer_left=time_left),
                get_attack_zone_kb()
            )
    else:
        if not duel.atk_zone:
            await safe_edit_message(
                cb,
                generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Соперник ещё выбирает удар…"),
                build_colored_vertical_keyboard([(f"{E_REFRESH} Обновить", "duel:refresh", "primary")])
            )
        else:
            await safe_edit_message(
                cb,
                generate_duel_status_text(duel, cb.from_user.id, extra=f"{E_SHIELD} Выбери зону защиты.", timer_left=time_left),
                get_defend_zone_kb()
            )
    await cb.answer("Обновлено")


@router.callback_query(F.data == "gear:menu")
async def cb_gear_menu(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    text, kb = generate_gear_screen(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "gear:w")
async def cb_gear_weapon(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    text, kb = generate_weapon_list(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
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
    elif p["crystals"] >= item["price"]:
        db.execute(
            "UPDATE players SET crystals=crystals-?, weapons_owned=?, weapon=? WHERE user_id=?",
            (item["price"], ",".join(owned | {key}), key, cb.from_user.id)
        )
        toast = f"Куплено: {item['name']}"
    else:
        await cb.answer(f"Нужно {item['price']}💎", show_alert=True)
        return
    text, kb = generate_weapon_list(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer(toast)


@router.callback_query(F.data == "gear:armor_menu")
async def cb_gear_armor_menu(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    text, kb = generate_armor_slot_menu(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^gear:(head|torso|arms|legs)$"))
async def cb_gear_armor_slot(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    slot = cb.data.split(":")[1]
    text, kb = generate_armor_slot_list(cb.from_user.id, slot)
    await safe_edit_message(cb, text, kb)
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
    elif p["crystals"] >= item["price"]:
        db.execute(
            f"UPDATE players SET crystals=crystals-?, armors_owned=?, {col}=? WHERE user_id=?",
            (item["price"], ",".join(owned | {key}), key, cb.from_user.id)
        )
        toast = f"Куплено: {item['name']}"
    else:
        await cb.answer(f"Нужно {item['price']}💎", show_alert=True)
        return
    text, kb = generate_armor_slot_list(cb.from_user.id, slot)
    await safe_edit_message(cb, text, kb)
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
    text, kb = generate_top_screen(cb.from_user.id, key)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.message(DuelFindState.waiting_for_target, F.text)
async def duel_find_target_handler(m: Message, state: FSMContext, bot: Bot) -> None:
    if m.chat.type != "private":
        await state.clear()
        return
    if m.text in MENU_TEXTS:
        await state.clear()
        return
    await state.clear()
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start.")
        return
    key = m.text.strip().lstrip("@")
    if key.isdigit():
        row = db.fetch_one("SELECT user_id FROM players WHERE user_id=? AND banned=0", (int(key),))
    else:
        row = None
    if not row:
        row = db.fetch_one(
            """SELECT user_id FROM players
               WHERE (LOWER(username)=LOWER(?) OR LOWER(name)=LOWER(?)) AND banned=0 LIMIT 1""",
            (key, key)
        )
    target = row["user_id"] if row else pick_balanced_opponent(m.from_user.id, p["wins"])
    if not target:
        await m.answer("Не удалось подобрать соперника.")
        return
    await initiate_duel_message(m.from_user.id, target, m, bot)


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
    db.execute("UPDATE players SET last_active=? WHERE user_id=?", (time.time(), m.from_user.id))
    
    text = m.text or ""
    text_lower = text.lower().strip()
    
    known_patterns = [
        r"(?i)^(help|помощь|хелп)$",
        r"(?i)^(админ помощь|админ инфо|admin help)$",
        r"(?i)^(перчатка|перч|glove|вызов)(\s|$)",
        r"(?i)^(дуэль|бой|fight)(\s|$)",
        r"(?i)^(фото|профиль|stat)(\s|$)",
        r"(?i)^перевод(\s|$)",
        r"(?i)^атака(\s|$)",
        r"(?i)^(событие|статус события)(\s|$)",
        r"(?i)^(баланс|balance|бал)(\s|$)",
        r"(?i)^сл (джекпот|промах)(\s+)(\d+)$",
        r"(?i)^дрот (попадание|промах|красное|белое|жёлтое|желтое|яблочко)(\s+)(\d+)$",
        r"(?i)^баскет (попадание|промах)(\s+)(\d+)$",
        r"(?i)^кости (число|чет|больше)(\s+)",
        r"(?i)^(монетка|coin|мон)(\s+)(\d+)(\s+)(орел|решка|о|р)$",
        r"(?i)^рул (цвет|чет|половина|число|дюжина)(\s+)",
        r"(?i)^(больше|high)(\s+)(\d+)$",
        r"(?i)^(меньше|low)(\s+)(\d+)$",
        r"(?i)^событие (босс|караван|набег|дракон)$",
        r"(?i)^босс(\s+)(\w+)$",
        r"(?i)^(следующее событие|когда босс)$",
        r"(?i)^бан(\s|$)",
        r"(?i)^разбан(\s|$)",
        r"(?i)^выдать(\s|$)",
        r"(?i)^промо (создать|удалить|список)",
        r"(?i)^рассылка\s+",
    ]
    
    for action_key in RP_MAPPINGS.keys():
        variants = RP_MAPPINGS[action_key]
        for v in variants:
            known_patterns.append(rf"(?i)^{re.escape(v)}(\s|$)")
    
    for pattern in known_patterns:
        if re.match(pattern, text):
            return
    
    if m.chat.type == "private":
        await m.answer(
            f"{E_WARNING} <b>Неизвестная команда.</b>\n\n"
            f"Пиши <code>help</code> для списка команд или пользуйся меню внизу 👇",
            reply_markup=MENU_KB
        )
    else:
        await m.answer(CHAT_HINT_TEXT)


async def scheduled_event_spawner(bot: Bot) -> None:
    global NEXT_SCHEDULED_EVENT
    while True:
        try:
            NEXT_SCHEDULED_EVENT = time.time() + 4 * 3600
            await asyncio.sleep(4 * 3600)
            if ACTIVE_CHAT_EVENT and ACTIVE_CHAT_EVENT.is_active():
                continue
            event_types = list(CHAT_EVENT_TEMPLATES.keys())
            event_type = random.choice(event_types)
            event = spawn_chat_event(event_type, 0)
            if event:
                logging.info(f"Scheduled event spawned: {event.name}")
        except Exception as e:
            logging.error(f"Error in scheduled_event_spawner: {e}")
            await asyncio.sleep(60)


async def main() -> None:
    logging.basicConfig(level=Config.LOG_LEVEL, format=Config.LOG_FORMAT, datefmt=Config.LOG_DATE_FORMAT)
    if not Config.BOT_TOKEN or Config.BOT_TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        logging.critical("❌ ОШИБКА: Задай BOT_TOKEN!")
        raise SystemExit("Missing BOT_TOKEN")
    logging.info("=" * 60)
    logging.info("⚔️ АРЕНА ДУЭЛЯНТОВ — Ultimate Edition v10.0")
    logging.info("=" * 60)
    logging.info("Initializing database...")
    logging.info("Generating masked bots...")
    ensure_masked_bots_exist(Config.BOT_GENERATION_COUNT)
    logging.info("Creating bot instance...")
    bot = Bot(Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logging.info("Setting up dispatcher...")
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать / вернуться"),
        BotCommand(command="help", description="Правила и команды"),
    ])
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("✅ Bot successfully started and polling!")
    logging.info("=" * 60)
    event_task = asyncio.create_task(scheduled_event_spawner(bot))
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logging.info("Received shutdown signal...")
    except Exception as e:
        logging.critical(f"Fatal error: {e}\n{traceback.format_exc()}")
    finally:
        event_task.cancel()
        db.close()
        await bot.session.close()
        logging.info("Bot shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
