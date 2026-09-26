#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
⚔️ АРЕНА ДУЭЛЯНТОВ — Ultimate Edition v16.0 (Production-Ready)
================================================================================

Полнофункциональный Telegram-бот для PvP-дуэлей, казино, чатовых ивентов,
RP-действий и экономики. Написан в production-стиле с полной обработкой
всех edge-cases.

Ключевые особенности:
    • НИКАКИХ заглушек — каждая кнопка имеет полную реализацию
    • Полная обработка edge-cases (удаленные сообщения, устаревшие колбэки)
    • FSM для сложных диалогов
    • Математическая пагинация для длинных списков
    • edit_text/edit_reply_markup для плавного UX
    • call.answer() для сброса спиннера
    • Строгая типизация Python 3.10+
    • Подробные docstrings в Google Style
    • Логирование всех критических операций

Архитектура:
    1. Конфигурация и константы
    2. Эмодзи и UI-элементы
    3. Игровые данные (оружие, броня, арены, боссы)
    4. Утилиты и хелперы
    5. База данных (SQLite wrapper)
    6. Модели данных (Fighter, Duel, ChatEvent)
    7. Боевая логика
    8. ИИ бота и генерация соперников
    9. Казино (7 игр с анимацией)
    10. Чатовые события
    11. Промокоды
    12. RP система
    13. Генераторы UI с пагинацией
    14. Help с 4 интерактивными разделами
    15. Хендлеры команд (чат + ЛС)
    16. Callback handlers (полная реализация)
    17. FSM и fallback
    18. Фоновые задачи и запуск

Требования:
    - Python 3.10+
    - aiogram >= 3.0.0
    - sqlite3 (встроен)

Автор: AI Assistant
Версия: 16.0
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
from typing import (
    Optional,
    Tuple,
    List,
    Dict,
    Any,
    Union,
    Callable,
    Set,
)

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


# ==============================================================================
# 2. КОНФИГУРАЦИЯ
# ==============================================================================

class Config:
    """
    Глобальная конфигурация бота.
    
    Все настройки сгруппированы по категориям для удобства управления.
    В продакшене рекомендуется использовать переменные окружения.
    
    Attributes:
        BOT_TOKEN: Токен бота от @BotFather
        ADMIN_ID: Числовой ID администратора
        DB_PATH: Путь к файлу базы данных SQLite
        START_CRYSTALS: Стартовый баланс кристаллов для новых игроков
        TURN_TIMEOUT: Время на ход в дуэли (в секундах)
        RP_COOLDOWN: Кулдаун между RP-действиями (в секундах)
        TRANSFER_TAX: Налог на перевод кристаллов (в процентах)
        MIN_TRANSFER: Минимальная сумма перевода
        MAX_TRANSFER: Максимальная сумма перевода
        CASINO_MIN_BET: Минимальная ставка в казино
        CASINO_MAX_BET: Максимальная ставка в казино
        CASINO_BETS: Список доступных ставок
        BOT_GENERATION_COUNT: Количество скрытых ботов для матчмейкинга
        BOT_WIN_DISTRIBUTION: Распределение побед ботов по аренам
        EVENT_*: Параметры чатовых событий
        PROMO_*: Параметры промокодов
        TOP_LEADERBOARD_SIZE: Размер топа
        CHALLENGE_TIMEOUT: Таймаут вызова на дуэль
        LOG_*: Настройки логирования
    """
    
    # --- Авторизация ---
    BOT_TOKEN: str = "8996813076:AAHgcyCWj6l2x3H7xWuW4HCLUkmT8lVRizs"
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "5356400377"))
    DB_PATH: str = os.getenv("DB_PATH", "arena_ultimate.db")
    
    # --- Игровые константы ---
    START_CRYSTALS: int = 500
    TURN_TIMEOUT: int = 45
    RP_COOLDOWN: int = 5
    TRANSFER_TAX: float = 0.05
    MIN_TRANSFER: int = 10
    MAX_TRANSFER: int = 100000
    
    # --- Казино ---
    CASINO_MIN_BET: int = 10
    CASINO_MAX_BET: int = 50000
    CASINO_BETS: List[int] = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
    
    # --- Боты ---
    BOT_GENERATION_COUNT: int = 50
    BOT_WIN_DISTRIBUTION: Dict[str, float] = {
        "bronze": 0.5,
        "silver": 0.35,
        "gold": 0.15,
    }
    
    # --- События ---
    EVENT_BOSS_BASE_HP: int = 2000
    EVENT_CARAVAN_BASE_HP: int = 1000
    EVENT_RAID_BASE_HP: int = 3000
    EVENT_MIN_DAMAGE: int = 50
    EVENT_MAX_DAMAGE: int = 200
    EVENT_CRIT_CHANCE: float = 0.15
    EVENT_CRIT_MULT: float = 2.5
    EVENT_DEFAULT_DURATION_HOURS: float = 2.0
    
    # --- Промокоды ---
    PROMO_MIN_CODE_LENGTH: int = 3
    PROMO_MAX_CODE_LENGTH: int = 20
    PROMO_MAX_USES: int = 1000
    PROMO_MAX_HOURS: int = 8760
    
    # --- Топ ---
    TOP_LEADERBOARD_SIZE: int = 20
    
    # --- Вызовы ---
    CHALLENGE_TIMEOUT: int = 60
    
    # --- Логирование ---
    LOG_LEVEL: int = logging.INFO
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


# Дополнительные константы
BASE_HP: int = 150
MIN_NAME_LENGTH: int = 2
MAX_NAME_LENGTH: int = 16
DUEL_LOG_LIMIT: int = 10
DUEL_LOG_DISPLAY_LIMIT: int = 5
TELEGRAM_MAX_TEXT_LENGTH: int = 4096
BROADCAST_DELAY: float = 0.05
BOT_NAME_GENERATION_ATTEMPTS: int = 300
MAX_NOTIFICATIONS_PER_USER: int = 15


# ==============================================================================
# 3. ЭМОДЗИ
# ==============================================================================

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
E_BLACK = "⚫"
E_GREEN = "🟢"
E_BLUE = "🔵"
E_ADMIN = "🛠"
E_STATS = "📊"
E_USERS = "👥"
E_MONEY = "💰"
E_LOCK = "🔒"
E_UNLOCK = "🔓"
E_PROFILE = "👤"


# ==============================================================================
# 4. ИГРОВЫЕ ДАННЫЕ
# ==============================================================================

ZONES: List[str] = ["head", "torso", "arms", "legs"]

ZONE_INFO: Dict[str, Dict[str, Any]] = {
    "head": {
        "name": "Голова",
        "emoji": E_ZONE_HEAD,
        "mult": 1.5,
        "desc": "Высокий урон, сложно попасть",
    },
    "torso": {
        "name": "Торс",
        "emoji": E_ZONE_TORSO,
        "mult": 1.0,
        "desc": "Средний урон, стандартная цель",
    },
    "arms": {
        "name": "Руки",
        "emoji": E_ZONE_ARMS,
        "mult": 0.8,
        "desc": "Низкий урон, высокая точность",
    },
    "legs": {
        "name": "Ноги",
        "emoji": E_ZONE_LEGS,
        "mult": 0.9,
        "desc": "Средний урон, шанс замедлить",
    },
}


@dataclass
class AttackVariant:
    """
    Вариант атаки для оружия.
    
    Каждое оружие имеет 3 уникальных варианта атаки с разными характеристиками:
    - Множитель урона
    - Пробитие брони
    - Кулдаун в раундах
    - Специальный эффект (опционально)
    
    Attributes:
        name: Название приёма (например, "Джеб", "Казнь")
        description: Краткое описание эффекта для игрока
        damage_mult: Множитель базового урона оружия
        armor_penetration: Процент игнорирования брони (от 0.0 до 1.0)
        cooldown_rounds: Количество раундов перезарядки
        effect: Специальный эффект (triple, bleed, burn, pierce, stun, exec)
    """
    name: str
    description: str
    damage_mult: float
    armor_penetration: float
    cooldown_rounds: int
    effect: Optional[str] = None


WEAPONS: Dict[str, Dict[str, Any]] = {
    "fists": {
        "emoji": "👊",
        "name": "Кулаки",
        "base_dmg": 10,
        "price": 0,
        "description": "Базовое оружие новичка. Быстрые, но слабые удары.",
        "tier": "common",
        "variants": [
            AttackVariant("Джеб", "Быстрый удар", 0.8, 0.0, 0, None),
            AttackVariant("Серия ударов", "3 удара по 50% урона", 1.5, 0.0, 2, "triple"),
            AttackVariant("Апперкот", "Оглушает при попадании", 1.2, 0.1, 3, "stun"),
        ],
    },
    "dagger": {
        "emoji": "🗡",
        "name": "Кинжал",
        "base_dmg": 14,
        "price": 200,
        "description": "Быстрое оружие убийцы. Высокий шанс критов.",
        "tier": "uncommon",
        "variants": [
            AttackVariant("Укол", "Точный удар, пробивает 20% брони", 1.0, 0.2, 0, None),
            AttackVariant("Рассечение", "Кровотечение на 3 раунда", 1.1, 0.1, 2, "bleed"),
            AttackVariant("Тысяча порезов", "3 удара, игнор 30% брони", 1.4, 0.3, 3, "triple"),
        ],
    },
    "sword": {
        "emoji": E_SWORD,
        "name": "Меч",
        "base_dmg": 20,
        "price": 500,
        "description": "Классическое оружие воина. Сбалансированный урон.",
        "tier": "rare",
        "variants": [
            AttackVariant("Размах", "Стандартная атака", 1.0, 0.0, 0, None),
            AttackVariant("Пронзающий выпад", "Игнор 50% защиты", 1.2, 0.5, 2, "pierce"),
            AttackVariant("Казнь", "Двойной урон, легко блокируется", 2.0, 0.0, 4, "exec"),
        ],
    },
    "axe": {
        "emoji": "🪓",
        "name": "Топор",
        "base_dmg": 26,
        "price": 800,
        "description": "Тяжёлое оружие варвара. Огромный урон.",
        "tier": "rare",
        "variants": [
            AttackVariant("Рубящий удар", "Тяжелая атака", 1.0, 0.1, 0, None),
            AttackVariant("Кровопускание", "Сильное кровотечение", 1.1, 0.0, 3, "bleed"),
            AttackVariant("Сокрушение", "Огромный урон, долгий КД", 1.8, 0.2, 4, None),
        ],
    },
    "bow": {
        "emoji": "🏹",
        "name": "Лук",
        "base_dmg": 32,
        "price": 1200,
        "description": "Дальнобойное оружие охотника.",
        "tier": "epic",
        "variants": [
            AttackVariant("Прицельный выстрел", "Стандартная атака", 1.0, 0.3, 0, None),
            AttackVariant("Залп", "2 выстрела с шансом крита", 1.6, 0.2, 2, "triple"),
            AttackVariant("Бронебойная стрела", "Полный игнор брони", 1.3, 1.0, 3, "pierce"),
        ],
    },
    "staff": {
        "emoji": E_FIRE,
        "name": "Посох",
        "base_dmg": 38,
        "price": 1700,
        "description": "Магическое оружие чародея.",
        "tier": "epic",
        "variants": [
            AttackVariant("Магический импульс", "Базовая магия", 1.0, 0.4, 0, None),
            AttackVariant("Огненный шар", "Поджигает на 3 раунда", 1.2, 0.2, 2, "burn"),
            AttackVariant("Метеор", "Массовый урон", 2.2, 0.0, 4, "burn"),
        ],
    },
    "hammer": {
        "emoji": "🔨",
        "name": "Молот",
        "base_dmg": 46,
        "price": 2500,
        "description": "Тяжёлое оружие паладина.",
        "tier": "legendary",
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
    "bronze": {
        "name": "Бронзовая арена",
        "emoji": "🥉",
        "min_wins": 0,
        "max_wins": 9,
        "prize": 50,
    },
    "silver": {
        "name": "Серебряная арена",
        "emoji": "🥈",
        "min_wins": 10,
        "max_wins": 29,
        "prize": 100,
    },
    "gold": {
        "name": "Золотая арена",
        "emoji": "🥇",
        "min_wins": 30,
        "max_wins": 10**9,
        "prize": 200,
    },
}
ARENA_ORDER: List[str] = ["bronze", "silver", "gold"]


BOSSES: Dict[str, Dict[str, Any]] = {
    "goblin": {
        "key": "goblin",
        "name": "👺 Гоблин-Вождь",
        "desc": "Хитрый и злой. Бьёт по слабой броне.",
        "hp": 160,
        "weapon": "dagger",
        "armor_keys": {"head": "head_leather", "torso": "torso_robe", "arms": "arms_none", "legs": "legs_none"},
        "reward_mult": 3,
        "min_wins": 0,
    },
    "dragon": {
        "key": "dragon",
        "name": "🐉 Древний Дракон",
        "desc": "Огнедышащий ужас. Оружие — посох.",
        "hp": 260,
        "weapon": "staff",
        "armor_keys": {"head": "head_steel", "torso": "torso_plate", "arms": "arms_iron", "legs": "legs_iron"},
        "reward_mult": 5,
        "min_wins": 5,
    },
    "lord": {
        "key": "lord",
        "name": "👹 Древний Лорд",
        "desc": "Владыка арены. Молот разрушения.",
        "hp": 380,
        "weapon": "hammer",
        "armor_keys": {"head": "head_dragon", "torso": "torso_titan", "arms": "arms_runic", "legs": "legs_demon"},
        "reward_mult": 10,
        "min_wins": 15,
    },
    "titan": {
        "key": "titan",
        "name": "🗿 Каменный Титан",
        "desc": "Неуязвимая глыба. Огромная защита.",
        "hp": 500,
        "weapon": "fists",
        "armor_keys": {"head": "head_crown", "torso": "torso_aegis", "arms": "arms_berserk", "legs": "legs_wind"},
        "reward_mult": 15,
        "min_wins": 35,
    },
    "demon_king": {
        "key": "demon_king",
        "name": "😈 Король Демонов",
        "desc": "Повелитель преисподней. Смесь всех стихий.",
        "hp": 750,
        "weapon": "staff",
        "armor_keys": {"head": "head_crown", "torso": "torso_aegis", "arms": "arms_runic", "legs": "legs_demon"},
        "reward_mult": 25,
        "min_wins": 50,
    },
}


CHAT_EVENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "boss": {
        "name_template": "{emoji} Рейдовый Босс",
        "emoji": E_BOSS,
        "base_hp": 2000,
        "duration_hours": 2.0,
        "reward_per_participant": (50, 150),
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n{emoji} <b>Рейдовый Босс</b> появился!\nHP: {hp}\n\nКоманда <code>атака</code>!",
    },
    "caravan": {
        "name_template": "🐪 Золотой Караван",
        "emoji": "🐪",
        "base_hp": 1000,
        "duration_hours": 1.0,
        "reward_per_participant": (30, 100),
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n🐪 <b>Золотой Караван</b>!\nHP: {hp}\n\nКоманда <code>атака</code>!",
    },
    "raid": {
        "name_template": "⚔️ Набег Орков",
        "emoji": "⚔️",
        "base_hp": 3000,
        "duration_hours": 3.0,
        "reward_per_participant": (80, 200),
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n⚔️ <b>Набег Орков</b>!\nHP: {hp}\n\nКоманда <code>атака</code>!",
    },
    "dragon_raid": {
        "name_template": "🐉 Нашествие Драконов",
        "emoji": "🐉",
        "base_hp": 5000,
        "duration_hours": 4.0,
        "reward_per_participant": (150, 350),
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n🐉 <b>Нашествие Драконов</b>!\nHP: {hp}\n\nКоманда <code>атака</code>!",
    },
}


# ==============================================================================
# 5. УТИЛИТЫ И ХЕЛПЕРЫ
# ==============================================================================

def esc(text: Any) -> str:
    """
    Безопасное экранирование HTML-тегов в пользовательском вводе.
    
    Функция преобразует любой входной объект в строку и экранирует специальные
    HTML-символы (<, >, &, ", ') для предотвращения XSS-атак и ошибок парсинга.
    
    Args:
        text: Любой объект, который нужно преобразовать в строку и экранировать.
            Если передан None, вернётся строка "None".
            
    Returns:
        Безопасная для вставки в HTML строка, где:
        - < заменено на &lt;
        - > заменено на &gt;
        - & заменено на &amp;
        - " заменено на &quot;
        - ' заменено на &#x27;
        
    Example:
        >>> esc("<script>alert('xss')</script>")
        "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        >>> esc(None)
        "None"
        >>> esc(123)
        "123"
    """
    return html.escape(str(text))


def create_mention(user_id: int, name: str) -> str:
    """
    Создаёт HTML-ссылку на профиль пользователя Telegram для упоминания в RP.
    
    Telegram поддерживает deep links вида tg://user?id=<user_id>, которые
    при клике открывают профиль пользователя. Эта функция создаёт такую ссылку
    с безопасным отображаемым именем.
    
    Args:
        user_id: Числовой идентификатор пользователя Telegram.
            Должен быть положительным целым числом.
        name: Отображаемое имя пользователя. Будет экранировано для
            безопасности перед вставкой в HTML.
            
    Returns:
        Строка формата <a href="tg://user?id=...">Name</a>,
        которая при отображении в Telegram превратится в кликабельное
        упоминание пользователя.
        
    Example:
        >>> create_mention(123456789, "Иван")
        '<a href="tg://user?id=123456789">Иван</a>'
    """
    return f'<a href="tg://user?id={user_id}">{esc(name)}</a>'


def build_horizontal_keyboard(
    buttons: List[Tuple[str, str]],
    buttons_per_row: int = 2
) -> InlineKeyboardMarkup:
    """
    Строит горизонтальную Inline-клавиатуру из кортежей (текст, callback_data).
    
    Удобная функция-обёртка для быстрого создания inline-клавиатур с несколькими
    кнопками в строке. Автоматически разбивает кнопки на строки по указанному
    количеству.
    
    Args:
        buttons: Список кортежей вида (текст_кнопки, callback_data).
        buttons_per_row: Количество кнопок в одной строке (по умолчанию 2).
            
    Returns:
        Объект InlineKeyboardMarkup, готовый к отправке.
        
    Example:
        >>> kb = build_horizontal_keyboard(
        ...     [("Да", "yes"), ("Нет", "no"), ("Отмена", "cancel")],
        ...     buttons_per_row=2
        ... )
        # Создаст клавиатуру:
        # [Да] [Нет]
        # [Отмена]
    """
    builder = InlineKeyboardBuilder()
    row = []
    for text, callback_data in buttons:
        row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        if len(row) == buttons_per_row:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
    return builder.as_markup()


def build_vertical_keyboard_with_styles(
    buttons: List[Tuple[str, str, Optional[str]]]
) -> InlineKeyboardMarkup:
    """
    Строит вертикальную Inline-клавиатуру с цветными кнопками.
    
    Каждая кнопка размещается в отдельной строке. Поддерживает стилизацию
    кнопок через параметр style.
    
    Args:
        buttons: Список кортежей вида (текст, callback_data, style).
            style может быть:
            - "primary" (синий) — для основных действий
            - "success" (зелёный) — для подтверждений
            - "danger" (красный) — для отмен/удалений
            - None — стандартный стиль
            
    Returns:
        Объект InlineKeyboardMarkup с вертикальным расположением кнопок.
        
    Example:
        >>> kb = build_vertical_keyboard_with_styles([
        ...     ("Принять", "accept", "success"),
        ...     ("Отклонить", "reject", "danger"),
        ...     ("Инфо", "info", "primary"),
        ... ])
    """
    builder = InlineKeyboardBuilder()
    for text, callback_data, style in buttons:
        if style:
            builder.row(InlineKeyboardButton(text=text, callback_data=callback_data, style=style))
        else:
            builder.row(InlineKeyboardButton(text=text, callback_data=callback_data))
    return builder.as_markup()


def build_vertical_keyboard(buttons: List[Tuple[str, str]]) -> InlineKeyboardMarkup:
    """
    Строит вертикальную клавиатуру без стилей.
    
    Упрощённая версия build_vertical_keyboard_with_styles для случаев,
    когда стилизация не нужна.
    
    Args:
        buttons: Список кортежей вида (текст, callback_data).
            
    Returns:
        Объект InlineKeyboardMarkup.
    """
    return build_vertical_keyboard_with_styles([(t, c, None) for t, c in buttons])


async def safe_edit_message(
    cb: CallbackQuery,
    text: str,
    markup: Optional[InlineKeyboardMarkup] = None
) -> bool:
    """
    Безопасно редактирует сообщение, обрабатывая типичные ошибки Telegram API.
    
    Функция пытается отредактировать существующее сообщение. Если это не
    удаётся (например, из-за ошибки "message is not modified"), пытается
    отправить новое сообщение вместо редактирования.
    
    Обрабатывает следующие edge-cases:
    - "message is not modified" — когда новый текст совпадает со старым
    - Сообщение было удалено пользователем
    - Превышен лимит длины текста (4096 символов)
    - Прочие ошибки Telegram API
    
    Args:
        cb: Объект CallbackQuery, содержащий исходное сообщение.
        text: Новый текст сообщения. Будет обрезан до 4090 символов
            (лимит Telegram - 4096, оставляем запас).
        markup: Новая клавиатура (опционально). Если None, клавиатура
            будет удалена.
            
    Returns:
        True, если редактирование или отправка нового сообщения прошли успешно.
        False в случае критической ошибки.
        
    Note:
        Функция логирует все ошибки для последующей диагностики.
    """
    try:
        await cb.message.edit_text(
            text[:4090],
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
        return True
    except TelegramBadRequest as e:
        error_str = str(e).lower()
        if "message is not modified" in error_str:
            # Текст не изменился — это не ошибка
            return True
        if "message can't be edited" in error_str or "message to edit not found" in error_str:
            # Сообщение было удалено — отправляем новое
            try:
                await cb.message.answer(
                    text[:4090],
                    reply_markup=markup,
                    parse_mode=ParseMode.HTML
                )
                return True
            except Exception as fallback_err:
                logging.error(f"Critical fallback error in safe_edit_message: {fallback_err}")
                return False
        try:
            await cb.message.answer(
                text[:4090],
                reply_markup=markup,
                parse_mode=ParseMode.HTML
            )
            return True
        except Exception as fallback_err:
            logging.error(f"Fallback error: {fallback_err}")
            return False
    except Exception as e:
        logging.error(f"Unexpected error in safe_edit_message: {e}")
        return False


async def safe_edit_message_by_id(
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str,
    markup: Optional[InlineKeyboardMarkup] = None
) -> bool:
    """
    Безопасно редактирует сообщение по его ID.
    
    Используется для редактирования сообщений вызовов на дуэль,
    где нужно обновить текст и клавиатуру у обоих участников.
    
    Args:
        bot: Объект бота.
        chat_id: ID чата, в котором находится сообщение.
        message_id: ID сообщения для редактирования.
        text: Новый текст сообщения.
        markup: Новая клавиатура (опционально).
            
    Returns:
        True при успешном редактировании, False при ошибке.
    """
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
        if "message to edit not found" in error_str:
            logging.warning(f"Message {message_id} not found in chat {chat_id}")
            return False
        return False
    except Exception as e:
        logging.error(f"Edit by id error: {e}")
        return False


def format_number(num: int) -> str:
    """
    Форматирует число с разделителями тысяч для удобочитаемости.
    
    Args:
        num: Целое число для форматирования.
            
    Returns:
        Строка с числом, где тысячи разделены пробелами.
        
    Example:
        >>> format_number(1234567)
        "1 234 567"
        >>> format_number(500)
        "500"
    """
    return f"{num:,}".replace(",", " ")


# ==============================================================================
# 6. БАЗА ДАННЫХ
# ==============================================================================

class DatabaseManager:
    """
    Менеджер базы данных для управления состоянием игроков, уведомлений,
    статистики, промокодов и глобальных чатовых событий.
    
    Этот класс предоставляет ORM-подобный интерфейс для работы с SQLite,
    оборачивая низкоуровневые операции в удобные методы с обработкой ошибок.
    Использует sqlite3 с отключенной проверкой потока (check_same_thread=False)
    для совместимости с асинхронным циклом asyncio. Включение isolation_level=None
    обеспечивает режим autocommit для простых операций.
    
    Attributes:
        db_path: Путь к файлу базы данных SQLite.
        _connection: Активное соединение с базой данных.
        
    Methods:
        fetch_one: Выполняет SELECT и возвращает одну строку.
        fetch_all: Выполняет SELECT и возвращает все строки.
        execute: Выполняет INSERT/UPDATE/DELETE.
        close: Закрывает соединение с БД.
    """
    
    def __init__(self, db_path: str):
        """
        Инициализирует менеджер базы данных.
        
        При создании экземпляра автоматически:
        1. Подключается к указанному файлу БД (создаёт, если не существует)
        2. Настраивает row_factory для удобного доступа к полям по имени
        3. Инициализирует схему БД (создаёт таблицы, если их нет)
        
        Args:
            db_path: Путь к файлу базы данных SQLite. Может быть абсолютным
                или относительным. Если файл не существует, он будет создан.
        """
        self.db_path = db_path
        self._connection = sqlite3.connect(
            db_path,
            check_same_thread=False,  # Для работы с asyncio
            isolation_level=None,     # Autocommit режим
        )
        self._connection.row_factory = sqlite3.Row  # Доступ по имени поля
        self._init_schema()

    def _init_schema(self) -> None:
        """
        Инициализирует схему базы данных при первом запуске бота.
        
        Создаёт все необходимые таблицы и индексы, если они ещё не существуют.
        Использование CREATE TABLE IF NOT EXISTS гарантирует идемпотентность -
        повторные запуски не вызовут ошибок.
        
        Таблицы:
            - players: основные данные игроков
            - notifications: система уведомлений
            - promo_codes: определение промокодов
            - promo_activations: история активаций промокодов
            - chat_events: активные чатовые события
            - player_stats: расширенная статистика игроков
            
        Индексы:
            - ix_notif_user: быстрый поиск уведомлений пользователя
            - ix_players_wins: быстрая сортировка по победам
            - ix_events_active: поиск активных событий
        """
        schema = """
            -- Таблица игроков (основная)
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
            
            -- Таблица уведомлений
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                ts REAL NOT NULL,
                seen INTEGER NOT NULL DEFAULT 0
            );
            
            -- Таблица промокодов
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
            
            -- Таблица активаций промокодов
            CREATE TABLE IF NOT EXISTS promo_activations (
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                activated_at REAL NOT NULL,
                PRIMARY KEY (user_id, code)
            );
            
            -- Таблица чатовых событий
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
            
            -- Таблица расширенной статистики
            CREATE TABLE IF NOT EXISTS player_stats (
                user_id INTEGER PRIMARY KEY,
                boss_kills INTEGER NOT NULL DEFAULT 0,
                casino_wins INTEGER NOT NULL DEFAULT 0,
                casino_losses INTEGER NOT NULL DEFAULT 0,
                event_participations INTEGER NOT NULL DEFAULT 0,
                rp_actions_used INTEGER NOT NULL DEFAULT 0,
                crystals_spent INTEGER NOT NULL DEFAULT 0,
                items_bought INTEGER NOT NULL DEFAULT 0
            );
            
            -- Индексы для оптимизации запросов
            CREATE INDEX IF NOT EXISTS ix_notif_user ON notifications(user_id, seen);
            CREATE INDEX IF NOT EXISTS ix_players_wins ON players(wins, is_bot, banned);
            CREATE INDEX IF NOT EXISTS ix_events_active ON chat_events(active, ends_at);
        """
        try:
            self._connection.executescript(schema)
            logging.info("Database schema initialized successfully.")
        except sqlite3.Error as e:
            logging.critical(f"Failed to initialize database schema: {e}")
            raise

    def fetch_one(self, sql: str, args: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Выполняет SELECT запрос и возвращает одну строку результата.
        
        Args:
            sql: SQL-запрос с плейсхолдерами (?). Использование плейсхолдеров
                обязательно для защиты от SQL-инъекций.
            args: Кортеж аргументов для подстановки в запрос. Количество
                аргументов должно совпадать с количеством плейсхолдеров.
                
        Returns:
            Объект sqlite3.Row с доступом к полям по имени (row['field_name']),
            или None, если ничего не найдено или произошла ошибка.
            
        Example:
            >>> db.fetch_one("SELECT * FROM players WHERE user_id=?", (123,))
            <sqlite3.Row object>
        """
        try:
            return self._connection.execute(sql, args).fetchone()
        except sqlite3.Error as e:
            logging.error(f"DB fetch_one error: {e} | SQL: {sql} | Args: {args}")
            return None

    def fetch_all(self, sql: str, args: tuple = ()) -> List[sqlite3.Row]:
        """
        Выполняет SELECT запрос и возвращает все строки результата.
        
        Args:
            sql: SQL-запрос с плейсхолдерами (?).
            args: Кортеж аргументов для подстановки в запрос.
                
        Returns:
            Список объектов sqlite3.Row. Пустой список при ошибке или
            отсутствии результатов.
            
        Example:
            >>> db.fetch_all("SELECT * FROM players WHERE wins > ?", (10,))
            [<sqlite3.Row object>, ...]
        """
        try:
            return self._connection.execute(sql, args).fetchall()
        except sqlite3.Error as e:
            logging.error(f"DB fetch_all error: {e} | SQL: {sql} | Args: {args}")
            return []

    def execute(self, sql: str, args: tuple = ()) -> bool:
        """
        Выполняет модифицирующий запрос (INSERT, UPDATE, DELETE).
        
        Args:
            sql: SQL-запрос с плейсхолдерами (?).
            args: Кортеж аргументов для подстановки в запрос.
                
        Returns:
            True при успешном выполнении, False при ошибке.
            Ошибки логируются, но не вызывают исключений.
            
        Example:
            >>> db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (100, 123))
            True
        """
        try:
            self._connection.execute(sql, args)
            return True
        except sqlite3.Error as e:
            logging.error(f"DB execute error: {e} | SQL: {sql} | Args: {args}")
            return False

    def close(self) -> None:
        """
        Безопасно закрывает соединение с базой данных.
        
        Вызывается при остановке бота для корректного освобождения ресурсов.
        После вызова дальнейшая работа с БД невозможна.
        """
        if self._connection:
            self._connection.close()
            logging.info("Database connection closed.")


db = DatabaseManager(Config.DB_PATH)


# ==============================================================================
# 7. МОДЕЛИ ДАННЫХ
# ==============================================================================

@dataclass
class Fighter:
    """
    Представление бойца в бою с поддержкой кулдаунов вариантов атаки.
    
    Этот класс инкапсулирует все характеристики бойца: здоровье, оружие,
    броню, активные эффекты (DoT), статусы (оглушение) и кулдауны атак.
    Автоматически рассчитывает бонусы от экипировки при создании.
    
    Attributes:
        name: Отображаемое имя бойца (должно быть экранировано).
        max_hp: Максимальное здоровье (базовое + бонусы от брони).
        hp: Текущее здоровье. Уменьшается при получении урона.
        weapon: Ключ оружия из словаря WEAPONS.
        armor_slots: Словарь слотов брони {zone: armor_key}.
        dots: Список активных эффектов периодического урона (DoT).
            Каждый элемент: {"name": str, "dmg": int, "left": int}
        stun: Флаг оглушения. Если True, боец пропускает следующий ход.
        attack_cooldowns: Словарь кулдаунов вариантов атаки
            {variant_index: rounds_left}.
    """
    name: str
    max_hp: int
    hp: int
    weapon: str
    armor_slots: Dict[str, str] = field(default_factory=dict)
    dots: List[Dict[str, Any]] = field(default_factory=list)
    stun: bool = False
    attack_cooldowns: Dict[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Валидация и расчет бонусов после инициализации объекта.
        
        Автоматически:
        1. Проверяет корректность оружия (fallback на 'fists')
        2. Фиксирует слоты брони (недостающие заполняются "none")
        3. Рассчитывает защиту по зонам
        4. Суммирует бонусы от брони (шанс спец-атаки, урон)
        """
        # Валидация оружия
        if self.weapon not in WEAPONS:
            logging.warning(f"Unknown weapon '{self.weapon}', fallback to 'fists'")
            self.weapon = "fists"

        # Базовый урон оружия
        self.base_weapon_dmg = WEAPONS[self.weapon]["base_dmg"]

        # Фиксация слотов брони
        slots = self.armor_slots or {}
        fixed_slots = {}
        for s in ZONES:
            key = slots.get(s) or f"{s}_none"
            # Проверка существования предмета брони
            if not get_armor_item_by_key(key):
                key = f"{s}_none"
            fixed_slots[s] = key
        self.armor_slots = fixed_slots

        # Расчет защиты и бонусов
        self.armor_def = {}
        total_chance = 0
        total_bonus = 0

        for slot in ZONES:
            item = get_armor_item_by_key(self.armor_slots[slot]) or get_armor_item_by_key(f"{slot}_none")
            self.armor_def[slot] = item["df"]
            total_chance += item["chance"]
            total_bonus += item["dmg_bonus"]

        # Ограничение шанса спец-атаки до 70%
        self.spec_chance = min(total_chance, 70)
        self.spec_dmg_bonus = total_bonus / 100.0

    def is_alive(self) -> bool:
        """
        Проверяет, жив ли боец (HP > 0).
        
        Returns:
            True если здоровье больше 0, False если боец мёртв.
        """
        return self.hp > 0

    def get_armor_def(self, zone: str) -> int:
        """
        Возвращает значение защиты для конкретной зоны тела.
        
        Args:
            zone: Название зоны (head, torso, arms, legs).
                
        Returns:
            Целое число - значение защиты. 0 если зона не найдена.
        """
        return self.armor_def.get(zone, 0)

    def get_weapon_dmg_for_zone(self, zone: str, variant_mult: float = 1.0) -> int:
        """
        Рассчитывает базовый урон оружия по конкретной зоне с учётом множителя
        зоны и варианта атаки.
        
        Args:
            zone: Название зоны (head, torso, arms, legs).
            variant_mult: Множитель от варианта атаки (по умолчанию 1.0).
                
        Returns:
            Целое число - рассчитанный урон. Минимум 1.
        """
        zone_mult = ZONE_INFO.get(zone, {}).get("mult", 1.0)
        base = self.base_weapon_dmg * zone_mult * variant_mult
        return max(1, round(base))

    def reduce_cooldowns(self) -> None:
        """
        Уменьшает счетчики кулдаунов всех атак на 1 раунд.
        
        Вызывается в конце каждого раунда. Атаки с КД <= 0 удаляются
        из словаря и становятся доступными.
        """
        for idx in list(self.attack_cooldowns.keys()):
            self.attack_cooldowns[idx] -= 1
            if self.attack_cooldowns[idx] <= 0:
                del self.attack_cooldowns[idx]

    def get_available_variants(self) -> List[int]:
        """
        Возвращает список индексов доступных (не на кулдауне) вариантов атаки.
        
        Returns:
            Список индексов вариантов (0, 1, 2), которые можно использовать.
        """
        all_variants = list(range(len(WEAPONS[self.weapon]["variants"])))
        return [i for i in all_variants if i not in self.attack_cooldowns]


def get_armor_item_by_key(key: str) -> Optional[Dict[str, Any]]:
    """
    Поиск предмета брони по ключу во всём массиве данных.
    
    Args:
        key: Ключ предмета брони (например, "head_dragon").
            
    Returns:
        Словарь с данными предмета + поле "slot", или None если не найден.
    """
    for slot, items in ARMOR_DATA.items():
        for it in items:
            if it["key"] == key:
                return {**it, "slot": slot}
    return None


def generate_hp_bar(fighter: Fighter, width: int = 12) -> str:
    """
    Генерирует визуальную полосу здоровья (HP Bar) из эмодзи.
    
    Args:
        fighter: Боец, для которого генерируется полоса.
        width: Ширина полосы в символах (по умолчанию 12).
            
    Returns:
        Строка из эмодзи 🟩🟨🟥⬛, визуализирующая текущее HP.
        - 🟩 зеленая - HP > 60%
        - 🟨 желтая - HP > 30%
        - 🟥 красная - HP <= 30%
        - ⬛ черная - пустая часть
    """
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
    """
    Форматирует информацию о бойце для отображения в чате.
    
    Создаёт красивое текстовое представление бойца с:
    - Именем
    - HP bar
    - Оружием и уроном
    - Защитой по зонам
    - Активными кулдаунами (если есть)
    
    Args:
        fighter: Боец для форматирования.
            
    Returns:
        Многострочная строка с информацией о бойце.
    """
    w = WEAPONS[fighter.weapon]
    ad = fighter.armor_def

    # Формируем строку кулдаунов, если они есть
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
    """
    Состояние активной дуэли с поддержкой выбора варианта атаки.
    
    Этот класс управляет всем состоянием боя: ходами, таймерами, логами,
    специальными состояниями и выбором вариантов атаки.
    
    Attributes:
        a_id: ID первого бойца (игрок или босс).
        b_id: ID второго бойца (игрок, бот или -1 для босса).
        a: Объект Fighter первого бойца.
        b: Объект Fighter второго бойца.
        attacker_is_a: True если сейчас атакует a, False если b.
        round_no: Номер текущего раунда.
        atk_zone: Выбранная зона атаки (None если ещё не выбрана).
        def_zone: Выбранная зона защиты (None если ещё не выбрана).
        chosen_variant_idx: Индекс выбранного варианта атаки.
        log: Список строк лога боя.
        started: Время начала боя (timestamp).
        is_boss: True если это бой с боссом.
        boss_key: Ключ босса из BOSSES (если is_boss=True).
        reward_mult: Множитель награды.
        finished: Флаг завершения боя.
        bot_last_block_round: Раунд последнего блока ботом.
        bot_block_streak: Серия блоков бота подряд.
        timer_task: asyncio.Task таймера хода.
        timer_deadline: Дедлайн таймера (timestamp).
        timer_for: ID игрока, для которого запущен таймер.
        timer_role: Роль игрока с таймером (attacker/defender).
    """
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
        """Определяет роль пользователя в текущем раунде."""
        if uid == self.a_id:
            return "attacker" if self.attacker_is_a else "defender"
        if uid == self.b_id:
            return "defender" if self.attacker_is_a else "attacker"
        return "none"

    def get_attacker(self) -> Fighter:
        """Возвращает текущего атакующего бойца."""
        return self.a if self.attacker_is_a else self.b

    def get_defender(self) -> Fighter:
        """Возвращает текущего защищающегося бойца."""
        return self.b if self.attacker_is_a else self.a

    def get_attacker_id(self) -> int:
        """Возвращает ID текущего атакующего."""
        return self.a_id if self.attacker_is_a else self.b_id

    def get_defender_id(self) -> int:
        """Возвращает ID текущего защищающегося."""
        return self.b_id if self.attacker_is_a else self.a_id

    def get_fighter(self, uid: int) -> Optional[Fighter]:
        """Возвращает бойца по ID или None."""
        if uid == self.a_id:
            return self.a
        if uid == self.b_id:
            return self.b
        return None

    def get_opponent(self, uid: int) -> Optional[Fighter]:
        """Возвращает противника для указанного ID."""
        if uid == self.a_id:
            return self.b
        if uid == self.b_id:
            return self.a
        return None

    def add_log(self, message: str) -> None:
        """Добавляет сообщение в лог боя с ограничением размера."""
        self.log.append(message)
        if len(self.log) > DUEL_LOG_LIMIT:
            self.log = self.log[-DUEL_LOG_LIMIT:]


ACTIVE_DUELS: Dict[int, Duel] = {}


@dataclass
class PendingDuel:
    """
    Ожидающий подтверждения вызов на дуэль.
    
    Хранит информацию о вызове до момента принятия или отклонения.
    
    Attributes:
        challenger_id: ID вызывающего игрока.
        target_id: ID вызываемого игрока.
        challenger_msg_id: ID сообщения у вызывающего.
        target_msg_id: ID сообщения у вызываемого.
        chat_id: ID чата (для редактирования сообщений).
        created_at: Время создания вызова (timestamp).
        timeout_task: asyncio.Task для автоматического отклонения.
    """
    challenger_id: int
    target_id: int
    challenger_msg_id: int
    target_msg_id: int
    chat_id: int
    created_at: float
    timeout_task: Optional[asyncio.Task] = None


PENDING_DUELS: Dict[Tuple[int, int], PendingDuel] = {}


@dataclass
class ChatEvent:
    """
    Модель глобального чатового события (Рейдовый Босс, Караван, Набег).
    
    Чатовые события - это глобальные PvE ивенты, в которых могут участвовать
    все пользователи чата, атакуя общую цель командой "атака".
    
    Attributes:
        event_id: Уникальный идентификатор события.
        event_type: Тип события (boss, caravan, raid, dragon_raid).
        name: Отображаемое имя события.
        hp: Текущее HP события.
        max_hp: Максимальное HP события.
        started_by: ID пользователя, запустившего событие.
        started_at: Время начала (timestamp).
        ends_at: Время окончания (timestamp).
        active: Флаг активности события.
        participants: Множество ID участников.
        damage_log: Лог нанесённого урона.
        total_damage_dealt: Суммарный нанесённый урон.
    """
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
        """Проверяет, активно ли событие."""
        return self.active and self.hp > 0 and time.time() < self.ends_at

    def take_damage(self, attacker_id: int, attacker_name: str, damage: int, is_crit: bool = False) -> str:
        """
        Наносит урон событию и обновляет статистику.
        
        Args:
            attacker_id: ID атакующего.
            attacker_name: Имя атакующего.
            damage: Нанесённый урон.
            is_crit: Был ли это критический удар.
                
        Returns:
            Строка лога для отображения в чате.
        """
        self.hp = max(0, self.hp - damage)
        self.participants.add(attacker_id)
        self.total_damage_dealt += damage

        crit_text = " 💥 <b>КРИТ!</b>" if is_crit else ""
        log_entry = f"⚔️ {attacker_name} наносит <b>{damage}</b> урона!{crit_text} (Осталось HP: {self.hp}/{self.max_hp})"
        self.damage_log.append(log_entry)
        return log_entry

    def get_participants_count(self) -> int:
        """Возвращает количество участников события."""
        return len(self.participants)

    def get_time_left(self) -> int:
        """Возвращает оставшееся время в секундах."""
        return max(0, int(self.ends_at - time.time()))


ACTIVE_CHAT_EVENT: Optional[ChatEvent] = None
NEXT_SCHEDULED_EVENT: Optional[float] = None


# ==============================================================================
# 8. БОЕВАЯ ЛОГИКА
# ==============================================================================

def calculate_damage(
    attacker: Fighter,
    defender: Fighter,
    atk_zone: str,
    def_zone: Optional[str],
    variant: AttackVariant
) -> Tuple[int, str]:
    """
    Рассчитывает итоговый урон с учётом брони, зон и параметров варианта атаки.
    
    Формула:
        weapon_dmg = base_dmg * zone_mult * variant_mult
        effective_armor = defender_armor * (1 - variant_armor_pen)
        final_dmg = max(1, weapon_dmg - effective_armor)
    
    Args:
        attacker: Атакующий боец.
        defender: Защищающийся боец.
        atk_zone: Зона, по которой наносится удар.
        def_zone: Зона, которую защищает противник (None если не защищается).
        variant: Выбранный вариант атаки.
            
    Returns:
        Кортеж (нанесенный урон, строка примечания).
        Примечание может быть "Блок!" если зоны совпали.
    """
    # Проверка на блок
    if def_zone == atk_zone:
        return 0, f"{E_SHIELD} <b>Блок!</b>"

    # Расчет урона оружия с учётом зоны и варианта
    weapon_dmg = attacker.get_weapon_dmg_for_zone(atk_zone, variant.damage_mult)

    # Применяем пробитие брони
    base_armor = defender.get_armor_def(atk_zone)
    effective_armor = max(0, round(base_armor * (1.0 - variant.armor_penetration)))

    # Финальный урон (минимум 1)
    final_dmg = max(1, round(weapon_dmg - effective_armor))

    return final_dmg, ""


def process_dots(fighter: Fighter, log: List[str]) -> None:
    """
    Обрабатывает периодический урон (DoT) в начале хода.
    
    Проходит по всем активным эффектам (кровотечение, горение и т.д.),
    наносит урон и уменьшает счётчик оставшихся раундов.
    Если эффект закончился, удаляет его из списка.
    
    Args:
        fighter: Боец, получающий периодический урон.
        log: Список строк лога боя для добавления сообщений.
    """
    for dot in list(fighter.dots):
        # Наносим урон
        fighter.hp = max(0, fighter.hp - dot["dmg"])
        log.append(f"{dot['name']}: {fighter.name} −{dot['dmg']} HP")

        # Уменьшаем счётчик
        dot["left"] -= 1

        # Удаляем закончившиеся эффекты
        if dot["left"] <= 0:
            fighter.dots.remove(dot)

        # Проверка на смерть от DoT
        if fighter.hp <= 0:
            log.append(f"☠️ {fighter.name} гибнет от эффектов")
            return


def apply_dot_effect(target: Fighter, name: str, dmg: int, rounds: int) -> None:
    """
    Накладывает или обновляет эффект периодического урона (DoT).
    
    Если эффект с таким именем уже существует, он обновляется.
    Иначе создаётся новый.
    
    Args:
        target: Боец, на которого накладывается эффект.
        name: Название эффекта (например, "🩸 Кровотечение").
        dmg: Урон за раунд.
        rounds: Количество раундов действия.
    """
    # Удаляем существующий эффект с таким же именем
    target.dots = [d for d in target.dots if d["name"] != name]
    # Добавляем новый
    target.dots.append({"name": name, "dmg": dmg, "left": rounds})


def resolve_special_attack(
    attacker: Fighter,
    defender: Fighter,
    atk_zone: str,
    def_zone: Optional[str],
    variant: AttackVariant,
    log: List[str]
) -> bool:
    """
    Применяет специальный эффект выбранного варианта атаки.
    
    Обрабатывает следующие эффекты:
    - triple: тройная атака
    - exec: казнь (двойной урон)
    - bleed: кровотечение
    - pierce: пробитие
    - burn: горение
    - stun: оглушение
    
    Args:
        attacker: Атакующий боец.
        defender: Защищающийся боец.
        atk_zone: Зона атаки.
        def_zone: Зона защиты.
        variant: Выбранный вариант атаки.
        log: Список лога боя.
            
    Returns:
        True если спецэффект был применён, False иначе.
    """
    # Блок отменяет спецэффект
    if def_zone == atk_zone:
        log.append(f"{E_SHIELD} {defender.name} заблокировал <b>{variant.name}</b>")
        return True

    effect = variant.effect

    if effect == "triple":
        # Тройная атака: 3 удара, каждый 1/3 от общего урона
        hits = [
            max(1, round(calculate_damage(attacker, defender, atk_zone, def_zone, variant)[0] / 3))
            for _ in range(3)
        ]
        total_dmg = sum(hits)
        defender.hp = max(0, defender.hp - total_dmg)
        log.append(f"⚡ <b>{variant.name}</b>: {' + '.join(map(str, hits))} = <b>−{total_dmg}</b>")
        return True

    elif effect == "exec":
        # Казнь: обычный урон от варианта (с множителем 2.0)
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        log.append(
            f"{E_SWORD} <b>{variant.name}</b>: {attacker.name} → {defender.name} "
            f"[{ZONE_INFO[atk_zone]['emoji']}] <b>−{dmg}</b>"
        )
        return True

    elif effect == "bleed":
        # Кровотечение: урон + DoT 4% от макс HP
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        bleed_dmg = max(1, round(defender.max_hp * 0.04))
        apply_dot_effect(defender, "🩸 Кровотечение", bleed_dmg, 3)
        log.append(f"🪓 <b>{variant.name}</b>: −{dmg}, кровь по <b>{bleed_dmg}</b> ×3")
        return True

    elif effect == "pierce":
        # Пробитие: урон с учётом пробития из варианта
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        log.append(f"🏹 <b>{variant.name}</b>: пробивает броню на <b>−{dmg}</b>")
        return True

    elif effect == "burn":
        # Горение: урон + DoT 40% от урона
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        burn_dmg = max(1, round(dmg * 0.4))
        apply_dot_effect(defender, f"{E_FIRE} Горение", burn_dmg, 3)
        log.append(f"{E_FIRE} <b>{variant.name}</b>: −{dmg}, огонь по <b>{burn_dmg}</b> ×3")
        return True

    elif effect == "stun":
        # Оглушение: урон + пропуск хода
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
    """
    Выполняет полный цикл атаки с учётом выбранного варианта.
    
    Этапы:
    1. Проверка оглушения атакующего
    2. Установка кулдауна варианта
    3. Попытка спецэффекта (если есть и прошёл шанс)
    4. Обычная атака
    
    Args:
        attacker: Атакующий боец.
        defender: Защищающийся боец.
        atk_zone: Зона атаки.
        def_zone: Зона защиты.
        variant_idx: Индекс выбранного варианта атаки.
        log: Список лога боя.
    """
    # Проверка оглушения
    if attacker.stun:
        attacker.stun = False
        log.append(f"💫 {attacker.name} оглушён и пропускает ход!")
        return

    # Получаем вариант атаки
    weapon_data = WEAPONS[attacker.weapon]
    variant = weapon_data["variants"][variant_idx]

    # Устанавливаем кулдаун
    if variant.cooldown_rounds > 0:
        attacker.attack_cooldowns[variant_idx] = variant.cooldown_rounds

    # Попытка спецэффекта
    if variant.effect and random.random() * 100 < attacker.spec_chance:
        if resolve_special_attack(attacker, defender, atk_zone, def_zone, variant, log):
            return

    # Обычная атака
    dmg, note = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
    if note:
        log.append(f"{ZONE_INFO[atk_zone]['emoji']} {attacker.name} бьёт в «{ZONE_INFO[atk_zone]['name']}» — {note}")
    else:
        defender.hp = max(0, defender.hp - dmg)
        log.append(
            f"👊 {attacker.name} [{variant.name}] → {defender.name} "
            f"[{ZONE_INFO[atk_zone]['emoji']}] <b>−{dmg}</b>"
        )


# ==============================================================================
# 9. УПРАВЛЕНИЕ ДУЭЛЬЮ И ТАЙМЕРАМИ
# ==============================================================================

def stop_duel_timer(duel: Duel) -> None:
    """
    Безопасно останавливает и очищает задачу таймера дуэли.
    
    Отменяет запущенную asyncio.Task и обнуляет все поля таймера.
    
    Args:
        duel: Объект дуэли, таймер которой нужно остановить.
    """
    if duel.timer_task and not duel.timer_task.done():
        duel.timer_task.cancel()
    duel.timer_task = None
    duel.timer_deadline = 0.0
    duel.timer_for = None
    duel.timer_role = None


def terminate_duel(duel: Duel) -> None:
    """
    Завершает дуэль и удаляет её из глобального хранилища.
    
    Устанавливает флаг finished, останавливает таймер и удаляет
    дуэль из ACTIVE_DUELS для обоих участников.
    
    Args:
        duel: Объект дуэли для завершения.
    """
    duel.finished = True
    stop_duel_timer(duel)
    ACTIVE_DUELS.pop(duel.a_id, None)
    if duel.b_id > 0:
        ACTIVE_DUELS.pop(duel.b_id, None)


def start_duel_timer(duel: Duel, uid: int, role: str, bot: Bot) -> None:
    """
    Инициализирует таймер хода для конкретного игрока.
    
    Создаёт новую asyncio.Task, которая будет отслеживать время хода.
    Если предыдущий таймер был запущен, он останавливается.
    
    Args:
        duel: Объект дуэли.
        uid: ID игрока, для которого запускается таймер.
        role: Роль игрока (attacker или defender).
        bot: Объект бота для отправки сообщений при таймауте.
    """
    # Для ботов (uid < 0) таймер не нужен
    if uid < 0:
        return

    stop_duel_timer(duel)
    duel.timer_for = uid
    duel.timer_role = role
    duel.timer_deadline = time.time() + Config.TURN_TIMEOUT
    duel.timer_task = asyncio.create_task(_timer_runner_task(duel, uid, role, bot))


async def _timer_runner_task(duel: Duel, uid: int, role: str, bot: Bot) -> None:
    """
    Асинхронная задача, отслеживающая истечение времени хода.
    
    Каждую секунду проверяет:
    - Не завершена ли дуэль
    - Не истекло ли время
    - Не изменилась ли роль игрока
    
    При истечении времени вызывает handle_timeout_defeat.
    
    Args:
        duel: Объект дуэли.
        uid: ID игрока с таймером.
        role: Ожидаемая роль игрока.
        bot: Объект бота.
    """
    try:
        while True:
            # Проверка завершения дуэли
            if duel.finished:
                return

            # Проверка истечения времени
            time_left = int(round(duel.timer_deadline - time.time()))
            if time_left <= 0:
                break

            await asyncio.sleep(1)

        # Дополнительные проверки перед наказанием
        if duel.finished:
            return
        if duel.timer_for != uid:
            return
        if duel.get_state_for(uid) != role:
            return
        if uid not in ACTIVE_DUELS:
            return

        # Наказание за таймаут
        await handle_timeout_defeat(duel, uid, bot)

    except asyncio.CancelledError:
        # Нормальное завершение при отмене задачи
        pass
    except Exception as e:
        logging.error(f"Critical error in duel timer for user {uid}: {e}\n{traceback.format_exc()}")


async def handle_timeout_defeat(duel: Duel, loser_uid: int, bot: Bot) -> None:
    """
    Обрабатывает автоматическое поражение из-за таймаута.
    
    Добавляет сообщение в лог и завершает дуэль с указанием причины.
    
    Args:
        duel: Объект дуэли.
        loser_uid: ID проигравшего (не успел за время).
        bot: Объект бота для отправки сообщений.
    """
    loser = duel.get_fighter(loser_uid)
    loser_name = loser.name if loser else "Неизвестный"
    duel.log.append(
        f"⏱ <b>{loser_name} не успел за {Config.TURN_TIMEOUT} сек — авто-поражение!</b>"
    )

    # Победитель - противоположная сторона
    winner_is_a = not (loser_uid == duel.a_id)
    await finalize_duel(duel, winner_is_a=winner_is_a, bot=bot, reason="timeout")


# ==============================================================================
# 10. ИИ БОТА И ГЕНЕРАЦИЯ СОПЕРНИКОВ
# ==============================================================================

def get_player_armor_slots(player_row: sqlite3.Row) -> Dict[str, str]:
    """
    Извлекает и валидирует слоты брони из записи БД.
    
    Args:
        player_row: Строка из таблицы players.
            
    Returns:
        Словарь {zone: armor_key} для всех 4 зон.
    """
    if not player_row:
        return {s: f"{s}_none" for s in ZONES}

    return {
        "head": player_row["armor_head"] or "head_none",
        "torso": player_row["armor_torso"] or "torso_none",
        "arms": player_row["armor_arms"] or "arms_none",
        "legs": player_row["armor_legs"] or "legs_none",
    }


def create_fighter_from_db(player_row: sqlite3.Row) -> Fighter:
    """
    Создаёт объект Fighter на основе данных из БД.
    
    Рассчитывает полное HP с учётом бонусов от брони.
    
    Args:
        player_row: Строка из таблицы players.
            
    Returns:
        Готовый объект Fighter.
    """
    slots = get_player_armor_slots(player_row)

    # Базовое HP + бонусы от брони
    total_hp = BASE_STATS["hp"]
    for key in slots.values():
        item = get_armor_item_by_key(key)
        if item:
            total_hp += item.get("hp", 0)

    # Валидация оружия
    weapon = player_row["weapon"] if player_row["weapon"] in WEAPONS else "fists"

    return Fighter(
        name=esc(player_row["name"]),
        max_hp=total_hp,
        hp=total_hp,
        weapon=weapon,
        armor_slots=slots,
    )


def determine_arena(wins: int) -> str:
    """
    Определяет текущую арену игрока на основе количества побед.
    
    Args:
        wins: Количество побед игрока.
            
    Returns:
        Ключ арены (bronze, silver, gold).
    """
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

HUMAN_TITLES: List[str] = [
    "", "", "", "xd", "pro", "god", "real", "top", "_", "007", "tvoy", "cz",
    "boss", "king", "elite", "master", "legend", "hero", "dark", "light",
]


def ensure_masked_bots_exist(target_count: int = 50) -> None:
    """
    Гарантирует наличие минимального количества скрытых ботов для матчмейкинга.
    
    Генерирует ботов с именами, похожими на человеческие, и распределяет
    их по аренам для быстрого подбора соперников.
    
    Args:
        target_count: Целевое количество ботов в БД.
    """
    existing_names = {r["name"].lower() for r in db.fetch_all("SELECT name FROM players")}
    bots = db.fetch_all("SELECT user_id, wins FROM players WHERE is_bot=1")
    need = max(0, target_count - len(bots))

    for _ in range(need):
        # Генерация уникального имени
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

        # Генерация UID (отрицательный для ботов)
        uid = -random.randint(10_000_000, 99_999_999)

        # Распределение побед по аренам
        arena_rand = random.random()
        if arena_rand < Config.BOT_WIN_DISTRIBUTION["bronze"]:
            wins = random.randint(0, 9)
        elif arena_rand < Config.BOT_WIN_DISTRIBUTION["bronze"] + Config.BOT_WIN_DISTRIBUTION["silver"]:
            wins = random.randint(10, 29)
        else:
            wins = random.randint(30, 60)

        losses = random.randint(max(0, wins // 2), wins * 2 + 3)
        arena_key = determine_arena(wins)

        # Выбор оружия по арене
        if arena_key == "bronze":
            weapon = random.choice(["fists", "dagger", "sword"])
            tier_max = 2
        elif arena_key == "silver":
            weapon = random.choice(["sword", "axe", "bow", "dagger"])
            tier_max = 3
        else:
            weapon = random.choice(["bow", "staff", "hammer", "axe", "sword"])
            tier_max = 4

        # Генерация слотов брони
        slots = {}
        for s in ZONES:
            items = ARMOR_DATA[s]
            idx = min(random.randint(0, tier_max), len(items) - 1)
            slots[s] = items[idx]["key"]

        owned_armors = set(list(slots.values()) + START_ARMOR_KEYS)

        db.execute(
            """INSERT INTO players (
                user_id, username, name, crystals, wins, losses, weapon,
                armor_head, armor_torso, armor_arms, armor_legs,
                weapons_owned, armors_owned, is_bot, created, last_active
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                uid, None, name, random.randint(0, 400),
                wins, losses, weapon,
                slots["head"], slots["torso"], slots["arms"], slots["legs"],
                weapon, ",".join(owned_armors), 1,
                time.time(), time.time()
            )
        )


def pick_balanced_opponent(player_uid: int, player_wins: int) -> Optional[int]:
    """
    Подбирает соперника строго того же уровня (арены), что и игрок.
    
    Приоритет:
    1. Реальные игроки той же арены
    2. Скрытые боты той же арены
    3. Генерация нового бота
    
    Args:
        player_uid: ID игрока, для которого ищем соперника.
        player_wins: Количество побед игрока.
            
    Returns:
        ID соперника или None если не удалось найти.
    """
    arena = determine_arena(player_wins)
    limits = ARENAS[arena]

    # Поиск реальных игроков
    humans = [
        r["user_id"] for r in db.fetch_all(
            """SELECT user_id FROM players
               WHERE user_id != ? AND banned=0 AND is_bot=0
               AND wins BETWEEN ? AND ?
               ORDER BY RANDOM() LIMIT 6""",
            (player_uid, limits["min_wins"], limits["max_wins"])
        )
    ]

    # Поиск ботов
    bots = [
        r["user_id"] for r in db.fetch_all(
            """SELECT user_id FROM players
               WHERE is_bot=1 AND banned=0
               AND wins BETWEEN ? AND ?
               ORDER BY RANDOM() LIMIT 6""",
            (limits["min_wins"], limits["max_wins"])
        )
    ]

    # Приоритетный выбор
    if humans and bots:
        return random.choice(bots if random.random() < 0.6 else humans)
    if humans:
        return random.choice(humans)
    if bots:
        return random.choice(bots)

    # Fallback: генерируем нового бота
    ensure_masked_bots_exist(10)
    rows = db.fetch_all(
        """SELECT user_id FROM players
           WHERE is_bot=1 AND wins BETWEEN ? AND ?
           ORDER BY RANDOM() LIMIT 1""",
        (limits["min_wins"], limits["max_wins"])
    )

    return rows[0]["user_id"] if rows else None


def bot_decide_attack_zone(attacker: Fighter, defender: Fighter) -> str:
    """
    ИИ выбора зоны атаки для бота.
    
    Логика:
    - 10% шанс случайного выбора (имитация ошибки)
    - При HP < 30% - добивание (зона с макс уроном)
    - Иначе - зона с лучшим соотношением урон-броня
    
    Args:
        attacker: Бот-атакующий.
        defender: Цель атаки.
            
    Returns:
        Название зоны для атаки.
    """
    # Случайный выбор (ошибка ИИ)
    if random.random() < 0.10:
        return random.choice(ZONES)

    # Добивание слабого противника
    if defender.hp <= defender.max_hp * 0.30:
        return max(ZONES, key=lambda z: attacker.get_weapon_dmg_for_zone(z))

    # Оптимальный выбор
    def score_zone(z: str) -> tuple:
        dmg = attacker.get_weapon_dmg_for_zone(z) - defender.get_armor_def(z)
        return (dmg, ZONE_INFO[z]["mult"])

    return max(ZONES, key=score_zone)


def bot_decide_attack_variant(attacker: Fighter) -> int:
    """
    ИИ выбора варианта атаки для бота.
    
    Предпочитает варианты с большим уроном, но учитывает кулдауны.
    
    Args:
        attacker: Бот-атакующий.
            
    Returns:
        Индекс варианта атаки (0, 1 или 2).
    """
    weapon_data = WEAPONS[attacker.weapon]
    variants = weapon_data["variants"]
    available = attacker.get_available_variants()

    if not available:
        return 0

    # Выбираем вариант с максимальным уроном среди доступных
    best_idx = max(available, key=lambda i: variants[i].damage_mult)
    return best_idx


def bot_decide_to_defend(duel: Duel, bot_is_a: bool) -> bool:
    """
    Определяет, будет ли бот пытаться блокировать атаку.
    
    Вероятность блока зависит от:
    - Текущего HP (чем меньше, тем выше шанс блока)
    - Серии блоков подряд
    - Раундов с последнего блока
    
    Args:
        duel: Объект дуэли.
        bot_is_a: True если бот - это fighter.a.
            
    Returns:
        True если бот решает защищаться.
    """
    # Ограничение на серию блоков
    if duel.bot_block_streak >= 2:
        return False

    # Кулдаун после блока
    if duel.round_no - duel.bot_last_block_round < 3:
        return False

    # Расчёт вероятности на основе HP
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
    """
    Выбирает зону для защиты, основываясь на наиболее опасной зоне атаки.
    
    25% шанс ошибиться и защитить вторую по опасности зону.
    
    Args:
        attacker: Атакующий (для расчёта урона).
        defender: Защищающийся бот.
            
    Returns:
        Название зоны для защиты.
    """
    def danger_level(z: str) -> int:
        return attacker.get_weapon_dmg_for_zone(z) - defender.get_armor_def(z)

    sorted_zones = sorted(ZONES, key=danger_level, reverse=True)

    # Шанс ошибки
    if random.random() < 0.25 and len(sorted_zones) > 1:
        return sorted_zones[1]

    return sorted_zones[0]


# ==============================================================================
# 11. КАЗИНО
# ==============================================================================

async def play_casino_slots_animated(chat_id: int, bet: int, uid: int, bot: Bot) -> Tuple[Optional[str], Optional[str]]:
    """
    Логика игры в слоты с анимацией.
    
    Выплаты:
    - 1 (джекпот): x10
    - Другие значения: проигрыш
    
    Args:
        chat_id: ID чата для отправки анимации.
        bet: Размер ставки.
        uid: ID игрока.
        bot: Объект бота.
            
    Returns:
        Кортеж (результат, ошибка). Если ошибка - результат None.
    """
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."

    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    if bet > Config.CASINO_MAX_BET:
        return None, f"Максимальная ставка: {Config.CASINO_MAX_BET} {E_CRYSTAL}"

    # Ставка
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))

    # Анимация
    sent_message = await bot.send_dice(chat_id=chat_id, emoji="🎰")
    dice_value = sent_message.dice.value

    if dice_value == 1:
        mult = 10
        win = bet * mult
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (win, uid))
        db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
        return (
            f"{E_SLOT} Выпало: <b>{dice_value}</b>\n\n"
            f"{E_TROPHY} <b>ДЖЕКПОТ ×{mult}!</b>\n"
            f"💎 Вы выиграли: +{win} кристаллов",
            None
        )
    else:
        db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
        return (
            f"{E_SLOT} Выпало: <b>{dice_value}</b>\n\n"
            f"{E_SKULL} <b>Нет комбинации.</b>\n"
            f"💎 Вы проиграли: −{bet} кристаллов",
            None
        )


async def play_casino_dice_game(chat_id: int, bet: int, uid: int, bot: Bot, mode: str, value: Any = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Логика игры в кости с разными режимами.
    
    Режимы:
    - number: на конкретное число (×6)
    - even_odd: чёт/нечет (×2)
    - high_low: больше/меньше (×2)
    
    Args:
        chat_id: ID чата для отправки анимации.
        bet: Размер ставки.
        uid: ID игрока.
        bot: Объект бота.
        mode: Режим игры.
        value: Значение для режима.
            
    Returns:
        Кортеж (результат, ошибка).
    """
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."

    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"

    # Ставка
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))

    # Анимация
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
        db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
        return (
            f"{E_DICE} Выпало: <b>{dice_value}</b>\n\n"
            f"{E_TROPHY} <b>Победа ×{mult}!</b>\n"
            f"💎 Вы выиграли: +{payout} кристаллов",
            None
        )
    else:
        db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
        return (
            f"{E_DICE} Выпало: <b>{dice_value}</b>\n\n"
            f"{E_SKULL} <b>Поражение.</b>\n"
            f"💎 Вы проиграли: −{bet} кристаллов",
            None
        )


async def play_casino_darts_animated(chat_id: int, bet: int, uid: int, bot: Bot, bet_on_miss: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Логика игры в дротик с анимацией.
    
    Выпадает 1-6:
    - 4, 5, 6 = попадание
    - 1, 2, 3 = промах
    
    Args:
        chat_id: ID чата для отправки анимации.
        bet: Размер ставки.
        uid: ID игрока.
        bot: Объект бота.
        bet_on_miss: Ставка на промах (True) или попадание (False).
            
    Returns:
        Кортеж (результат, ошибка).
    """
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."

    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"

    # Ставка
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))

    # Анимация
    sent_message = await bot.send_dice(chat_id=chat_id, emoji="🎯")
    dice_value = sent_message.dice.value
    is_hit = dice_value >= 4

    if bet_on_miss:
        # Ставка на промах
        if not is_hit:
            payout = int(bet * 1.9)
            db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
            db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
            return (
                f"{E_DARTS} Выпало: <b>{dice_value}</b>\n\n"
                f"{E_TROPHY} <b>Промах! Ты выиграл!</b>\n"
                f"💎 +{payout} кристаллов",
                None
            )
        else:
            db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
            return (
                f"{E_DARTS} Выпало: <b>{dice_value}</b>\n\n"
                f"{E_SKULL} <b>Попадание. Ты проиграл.</b>\n"
                f"💎 −{bet} кристаллов",
                None
            )
    else:
        # Ставка на попадание
        if is_hit:
            payout = int(bet * 1.9)
            db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
            db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
            return (
                f"{E_DARTS} Выпало: <b>{dice_value}</b>\n\n"
                f"{E_TROPHY} <b>Попадание!</b>\n"
                f"💎 +{payout} кристаллов",
                None
            )
        else:
            db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
            return (
                f"{E_DARTS} Выпало: <b>{dice_value}</b>\n\n"
                f"{E_SKULL} <b>Промах.</b>\n"
                f"💎 −{bet} кристаллов",
                None
            )


async def play_casino_basketball_animated(chat_id: int, bet: int, uid: int, bot: Bot, bet_on_miss: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Логика игры в баскетбол с анимацией.
    
    Выпадает 1-5:
    - 5 = слэм-данк (попадание)
    - 1-4 = промах
    
    Args:
        chat_id: ID чата для отправки анимации.
        bet: Размер ставки.
        uid: ID игрока.
        bot: Объект бота.
        bet_on_miss: Ставка на промах (True) или попадание (False).
            
    Returns:
        Кортеж (результат, ошибка).
    """
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."

    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"

    # Ставка
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))

    # Анимация
    sent_message = await bot.send_dice(chat_id=chat_id, emoji="🏀")
    dice_value = sent_message.dice.value
    is_hit = dice_value == 5

    if bet_on_miss:
        # Ставка на промах
        if not is_hit:
            payout = int(bet * 1.9)
            db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
            db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
            return (
                f"{E_BASKET} Выпало: <b>{dice_value}</b>\n\n"
                f"{E_TROPHY} <b>Промах! Ты выиграл!</b>\n"
                f"💎 +{payout} кристаллов",
                None
            )
        else:
            db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
            return (
                f"{E_BASKET} Выпало: <b>{dice_value}</b>\n\n"
                f"{E_SKULL} <b>Слэм-данк. Ты проиграл.</b>\n"
                f"💎 −{bet} кристаллов",
                None
            )
    else:
        # Ставка на попадание
        if is_hit:
            payout = int(bet * 1.9)
            db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
            db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
            return (
                f"{E_BASKET} Выпало: <b>{dice_value}</b>\n\n"
                f"{E_TROPHY} <b>СЛЭМ-ДАНК!</b>\n"
                f"💎 +{payout} кристаллов",
                None
            )
        else:
            db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
            return (
                f"{E_BASKET} Выпало: <b>{dice_value}</b>\n\n"
                f"{E_SKULL} <b>Промах.</b>\n"
                f"💎 −{bet} кристаллов",
                None
            )


def play_casino_roulette(uid: int, bet: int, bet_type: str, bet_value: Any = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Логика игры в рулетку с разными типами ставок.
    
    Типы ставок:
    - color: на цвет (красное/чёрное/зелёное)
    - even_odd: на чётность
    - half: на половину (1-18 или 19-36)
    - number: на конкретное число (×36)
    - dozen: на дюжину (×3)
    
    Args:
        uid: ID игрока.
        bet: Размер ставки.
        bet_type: Тип ставки.
        bet_value: Значение для типа ставки.
            
    Returns:
        Кортеж (результат, ошибка).
    """
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."

    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"

    # Красные числа в рулетке
    reds = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

    # Крутим рулетку
    num = random.randint(0, 36)

    # Определяем цвет
    if num == 0:
        res_color = "green"
        color_emoji = E_GREEN
    elif num in reds:
        res_color = "red"
        color_emoji = E_RED
    else:
        res_color = "black"
        color_emoji = E_BLACK

    # Ставка
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
        db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
        return (
            f"🎡 Выпало: {color_emoji} <b>{num}</b>\n\n"
            f"{E_TROPHY} <b>Победа ×{mult}!</b>\n"
            f"💎 Вы выиграли: +{payout} кристаллов",
            None
        )
    else:
        db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
        return (
            f"🎡 Выпало: {color_emoji} <b>{num}</b>\n\n"
            f"{E_SKULL} <b>Поражение.</b>\n"
            f"💎 Вы проиграли: −{bet} кристаллов",
            None
        )


def play_casino_coin(uid: int, bet: int, choice: str = "heads") -> Tuple[Optional[str], Optional[str]]:
    """
    Логика игры в монетку (Орёл или Решка).
    
    Выплаты:
    - Угадал: x2
    - Не угадал: проигрыш
    
    Args:
        uid: ID игрока.
        bet: Размер ставки.
        choice: Выбор игрока ("heads" или "tails").
            
    Returns:
        Кортеж (результат, ошибка).
    """
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."

    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"

    # Бросаем монетку
    result = random.choice(["heads", "tails"])

    # Ставка
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))

    result_text = "Орёл" if result == "heads" else "Решка"
    result_emoji = "🔵" if result == "heads" else "🔴"

    if result == choice:
        # Победа
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (bet * 2, uid))
        db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
        return (
            f"{E_COIN} Выпало: {result_emoji} <b>{result_text}</b>\n\n"
            f"{E_TROPHY} <b>Победа!</b>\n"
            f"💎 Вы выиграли: +{bet * 2} кристаллов",
            None
        )
    else:
        # Поражение
        db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
        return (
            f"{E_COIN} Выпало: {result_emoji} <b>{result_text}</b>\n\n"
            f"{E_SKULL} <b>Поражение.</b>\n"
            f"💎 Вы проиграли: −{bet} кристаллов",
            None
        )


def play_casino_highlow(uid: int, bet: int, choice: str = "high") -> Tuple[Optional[str], Optional[str]]:
    """
    Логика игры Больше/Меньше (число от 1 до 100).
    
    Выплаты:
    - Угадал (high: >50, low: <50): x1.9
    - Ровно 50: возврат ставки
    - Не угадал: проигрыш
    
    Args:
        uid: ID игрока.
        bet: Размер ставки.
        choice: Выбор ("high" или "low").
            
    Returns:
        Кортеж (результат, ошибка).
    """
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."

    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"

    # Генерируем число
    result_num = random.randint(1, 100)

    # Ставка
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))

    if result_num == 50:
        # Возврат
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (bet, uid))
        return (
            f"📊 Выпало число: <b>{result_num}</b>\n\n"
            f"🤝 <b>Ровно 50!</b> Ставка возвращена.",
            None
        )

    win = (choice == "high" and result_num > 50) or (choice == "low" and result_num < 50)

    if win:
        payout = int(bet * 1.9)
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
        db.execute("UPDATE player_stats SET casino_wins=casino_wins+1 WHERE user_id=?", (uid,))
        return (
            f"📊 Выпало число: <b>{result_num}</b>\n\n"
            f"{E_TROPHY} <b>Победа!</b>\n"
            f"💎 Вы выиграли: +{payout} кристаллов",
            None
        )
    else:
        db.execute("UPDATE player_stats SET casino_losses=casino_losses+1 WHERE user_id=?", (uid,))
        return (
            f"📊 Выпало число: <b>{result_num}</b>\n\n"
            f"{E_SKULL} <b>Поражение.</b>\n"
            f"💎 Вы проиграли: −{bet} кристаллов",
            None
        )


# ==============================================================================
# 12. ЧАТОВЫЕ СОБЫТИЯ
# ==============================================================================

def spawn_chat_event(
    event_type: str,
    started_by: int,
    custom_hp: Optional[int] = None,
    custom_duration: Optional[float] = None
) -> Optional[ChatEvent]:
    """
    Создаёт новое чатовое событие (босс, караван, набег).
    
    Args:
        event_type: Тип события (ключ из CHAT_EVENT_TEMPLATES).
        started_by: ID пользователя, запустившего событие.
        custom_hp: Пользовательское HP (None = использовать базовое).
        custom_duration: Пользовательская длительность в часах.
            
    Returns:
        Объект ChatEvent или None если событие уже активно.
    """
    global ACTIVE_CHAT_EVENT

    # Проверка на активное событие
    if ACTIVE_CHAT_EVENT and ACTIVE_CHAT_EVENT.is_active():
        return None

    # Получаем шаблон
    template = CHAT_EVENT_TEMPLATES.get(event_type)
    if not template:
        logging.error(f"Unknown event type: {event_type}")
        return None

    # Параметры события
    hp = custom_hp or template["base_hp"]
    duration = custom_duration or template["duration_hours"]
    name = template["name_template"].format(emoji=template["emoji"])

    now = time.time()
    ends_at = now + (duration * 3600)

    # Создаём событие
    event = ChatEvent(
        event_id=int(now),
        event_type=event_type,
        name=name,
        hp=hp,
        max_hp=hp,
        started_by=started_by,
        started_at=now,
        ends_at=ends_at,
    )

    ACTIVE_CHAT_EVENT = event

    # Сохраняем в БД
    db.execute(
        """INSERT INTO chat_events
           (event_type, name, hp, max_hp, started_by, started_at, ends_at, active)
           VALUES (?,?,?,?,?,?,?,1)""",
        (event_type, name, hp, hp, started_by, now, ends_at)
    )

    logging.info(f"Spawned chat event: {name} (HP: {hp}, duration: {duration}h)")
    return event


def attack_chat_event(attacker_id: int, attacker_name: str) -> Optional[str]:
    """
    Обрабатывает атаку чатового события игроком.
    
    Рассчитывает урон с учётом:
    - Базового диапазона урона
    - Шанса критического удара
    - Множителя крита
    
    Args:
        attacker_id: ID атакующего.
        attacker_name: Имя атакующего.
            
    Returns:
        Строка лога атаки или None если нет активного события.
    """
    global ACTIVE_CHAT_EVENT

    # Проверка активного события
    if not ACTIVE_CHAT_EVENT or not ACTIVE_CHAT_EVENT.is_active():
        return None

    # Расчёт урона
    base_dmg = random.randint(Config.EVENT_MIN_DAMAGE, Config.EVENT_MAX_DAMAGE)

    # Проверка крита
    is_crit = random.random() < Config.EVENT_CRIT_CHANCE
    if is_crit:
        base_dmg = int(base_dmg * Config.EVENT_CRIT_MULT)

    # Наносим урон
    log_entry = ACTIVE_CHAT_EVENT.take_damage(attacker_id, attacker_name, base_dmg, is_crit)
    db.execute("UPDATE player_stats SET event_participations=event_participations+1 WHERE user_id=?", (attacker_id,))

    # Проверка завершения события
    if ACTIVE_CHAT_EVENT.hp <= 0:
        ACTIVE_CHAT_EVENT.active = False
        db.execute("UPDATE chat_events SET active=0 WHERE event_id=?", (ACTIVE_CHAT_EVENT.event_id,))

        # Начисление наград участникам
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
            f"💎 Роздано наград: {total_rewards}"
        )

        logging.info(f"Chat event completed: {ACTIVE_CHAT_EVENT.name}")

    return log_entry


def get_chat_event_status() -> Optional[str]:
    """
    Возвращает статус активного чатового события.
    
    Returns:
        Строка со статусом события или None если нет активного.
    """
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
        f"Используйте <code>атака</code> для нанесения урона!"
    )


# ==============================================================================
# 13. ПРОМОКОДЫ
# ==============================================================================

def create_promo_code(
    code: str,
    reward_crystals: int,
    reward_wins: int,
    max_uses: int,
    hours_valid: int,
    created_by: int
) -> Tuple[bool, str]:
    """
    Создаёт новый промокод.
    
    Args:
        code: Уникальный код (будет приведён к верхнему регистру)
        reward_crystals: Награда в кристаллах
        reward_wins: Награда в победах
        max_uses: Максимальное количество активаций
        hours_valid: Срок действия в часах
        created_by: ID админа, создавшего код
        
    Returns:
        Кортеж (успех, сообщение)
    """
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
        f"💎 Кристаллы: {reward_crystals}\n"
        f"🏆 Победы: {reward_wins}\n"
        f"👥 Макс. активаций: {max_uses}\n"
        f"⏳ Действует: {hours_valid} ч."
    )


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

    promo = db.fetch_one("SELECT * FROM promo_codes WHERE code=?", (code,))
    if not promo:
        return False, f"❌ Промокод <code>{code}</code> не найден."

    if not promo["active"]:
        return False, f"❌ Промокод <code>{code}</code> деактивирован."

    if promo["expires_at"] < time.time():
        return False, f"❌ Промокод <code>{code}</code> истёк."

    if promo["current_uses"] >= promo["max_uses"]:
        return False, f"❌ Промокод <code>{code}</code> исчерпан."

    already = db.fetch_one(
        "SELECT 1 FROM promo_activations WHERE user_id=? AND code=?",
        (user_id, code)
    )
    if already:
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

        rewards = []
        if promo["reward_crystals"] > 0:
            db.execute(
                "UPDATE players SET crystals=crystals+? WHERE user_id=?",
                (promo["reward_crystals"], user_id)
            )
            rewards.append(f"💎 +{promo['reward_crystals']} кристаллов")

        if promo["reward_wins"] > 0:
            db.execute(
                "UPDATE players SET wins=wins+? WHERE user_id=?",
                (promo["reward_wins"], user_id)
            )
            rewards.append(f"🏆 +{promo['reward_wins']} побед")

        rewards_text = "\n".join(rewards) if rewards else "🎁 Секретный бонус!"
        remaining = promo["max_uses"] - promo["current_uses"] - 1

        return True, (
            f"{E_GIFT} <b>ПРОМОКОД АКТИВИРОВАН!</b>\n\n"
            f"🎟 Код: <code>{code}</code>\n"
            f"{rewards_text}\n\n"
            f"📊 Осталось активаций: {remaining}/{promo['max_uses']}"
        )

    except sqlite3.Error as e:
        logging.error(f"Error activating promo code: {e}")
        return False, "❌ Произошла ошибка при активации. Попробуй позже."


# ==============================================================================
# 14. RP СИСТЕМА
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
    "покормить": ("🍕", "покормил(а)"),
    "напоить": ("🍺", "напоил(а)"),
    "щекотать": ("🤣", "пощекотал(а)"),
    "благословить": ("🙏", "благословил(а)"),
    "проклясть": ("💀", "проклял(а)"),
}

RP_COOLDOWNS: Dict[Tuple[int, int, str], float] = {}


def generate_rp_text(actor_id: int, actor_name: str, target_id: int, target_name: str, action_key: str) -> str:
    """
    Генерирует отформатированный текст RP-действия с упоминаниями.
    
    Args:
        actor_id: ID действующего лица.
        actor_name: Имя действующего лица.
        target_id: ID цели действия.
        target_name: Имя цели.
        action_key: Ключ действия из RP_ACTIONS.
            
    Returns:
        Строка с HTML-упоминаниями и эмодзи.
    """
    emoji, verb = RP_ACTIONS.get(action_key, ("✨", "взаимодействовал(а) с"))
    actor_mention = create_mention(actor_id, actor_name)
    target_mention = create_mention(target_id, target_name)
    return f"{emoji} {actor_mention} {verb} {target_mention}!"


# ==============================================================================
# 15. ПАРСЕР ЦЕЛЕЙ
# ==============================================================================

def resolve_command_target(m: Message, command_word: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Универсальная функция для определения цели команды в чате.
    
    Поддерживает:
    1. Reply (ответ на сообщение)
    2. @username упоминание
    3. Числовой ID
    
    Args:
        m: Объект сообщения.
        command_word: Слово-команда (для очистки строки).
            
    Returns:
        Кортеж (user_id цели, сообщение об ошибке). Если цель найдена, ошибка = None.
    """
    # Приоритет 1: Ответ на сообщение (Reply)
    if m.reply_to_message and m.reply_to_message.from_user and not m.reply_to_message.from_user.is_bot:
        return m.reply_to_message.from_user.id, None

    # Приоритет 2: Парсинг текста на наличие @username или ID
    text = m.text or ""
    if text.lower().startswith(command_word.lower()):
        rest_of_text = text[len(command_word):].strip()
    else:
        rest_of_text = text

    # Регулярное выражение для поиска @username или числа
    match = re.search(r'@(\w+)|(-?\d+)', rest_of_text)
    if match:
        val = match.group(1) or match.group(2)

        # Проверка на числовой ID
        if val.lstrip('-').isdigit():
            row = db.fetch_one("SELECT user_id FROM players WHERE user_id=? AND banned=0", (int(val),))
            if row:
                return row["user_id"], None
        else:
            # Проверка на username или имя
            row = db.fetch_one(
                """SELECT user_id FROM players
                   WHERE (LOWER(username)=LOWER(?) OR LOWER(name)=LOWER(?))
                   AND banned=0 LIMIT 1""",
                (val, val)
            )
            if row:
                return row["user_id"], None

    # Если ничего не найдено, формируем ошибку в зависимости от типа чата
    if m.chat.type == "private":
        return None, (
            f"Укажи цель: ответь на сообщение или напиши "
            f"<code>{command_word} @user</code> / <code>{command_word} ID</code>"
        )
    else:
        return None, (
            f"⚠️ В группе команда работает <b>только ответом</b> на сообщение "
            f"игрока или через <code>@username</code> / <code>ID</code>."
        )


# ==============================================================================
# 16. МЕНЮ И КЛАВИАТУРЫ
# ==============================================================================

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


# ==============================================================================
# 17. ГЕНЕРАТОРЫ UI
# ==============================================================================

def generate_arena_menu_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Генерирует главное меню арены.
    
    ВАЖНО: Кнопка "Мой профиль" убрана — теперь используется отдельная команда /profile.
    
    Args:
        uid: ID пользователя.
            
    Returns:
        Кортеж (текст, клавиатура).
    """
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None

    a = ARENAS[determine_arena(p["wins"])]

    text = (
        f"╔══════════════════════════╗\n"
        f"      ⚔️ <b>АРЕНА ДУЭЛЯНТОВ</b>\n"
        f"╚══════════════════════════╝\n\n"
        f"{E_TROPHY} Победы: <b>{p['wins']}</b>\n"
        f"{E_SKULL} Поражения: {p['losses']}\n"
        f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>\n"
        f"📍 {a['emoji']} <b>{a['name']}</b>\n\n"
        f"🥉 Бронза — 0–9 побед · <b>{ARENAS['bronze']['prize']} {E_CRYSTAL}</b>\n"
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
    """
    Генерирует экран выбора босса.
    
    Args:
        uid: ID пользователя.
            
    Returns:
        Кортеж (текст, клавиатура).
    """
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

    buttons.append((f"{E_BACK} Назад", "arena:menu", "success"))

    return "\n".join(lines), build_vertical_keyboard_with_styles(buttons)


def generate_gear_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Генерирует экран управления снаряжением.
    
    ВАЖНО: Кнопка "Мой профиль" убрана — теперь используется отдельная команда /profile.
    
    Args:
        uid: ID пользователя.
            
    Returns:
        Кортеж (текст, клавиатура).
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

    kb = build_vertical_keyboard_with_styles([
        ("⚔️ Оружие", "gear:w", "primary"),
        ("🛡 Броня", "gear:armor_menu", "primary"),
    ])

    return "\n".join(lines), kb


def generate_weapon_list(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Генерирует список оружия с вариантами атаки.
    
    Args:
        uid: ID пользователя.
            
    Returns:
        Кортеж (текст, клавиатура).
    """
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
            style = "danger"

        buttons.append((f"{it['emoji']} {it['name']} · {label}", f"buy_weapon:{key}", style))

    buttons.append((f"{E_BACK} Назад", "gear:menu", "success"))

    return "\n".join(lines), build_vertical_keyboard_with_styles(buttons)


def generate_armor_slot_menu(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Генерирует меню выбора слота брони.
    
    Args:
        uid: ID пользователя.
            
    Returns:
        Кортеж (текст, клавиатура).
    """
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None

    slots = get_player_armor_slots(p)

    lines = ["🛡 <b>Броня — выбери часть тела</b>", f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>", ""]

    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"{ZONE_INFO[slot]['emoji']} <b>{ZONE_INFO[slot]['name']}</b> — {item['emoji']} {item['name']} (защита {item['df']})")

    kb = build_vertical_keyboard_with_styles([
        ("🧠 Голова", "gear:head", "primary"),
        ("🫀 Торс", "gear:torso", "primary"),
        ("💪 Руки", "gear:arms", "primary"),
        ("🦵 Ноги", "gear:legs", "primary"),
        (f"{E_BACK} Назад", "gear:menu", "success"),
    ])

    return "\n".join(lines), kb


def generate_armor_slot_list(uid: int, slot: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Генерирует список брони для конкретного слота.
    
    Args:
        uid: ID пользователя.
        slot: Название слота (head, torso, arms, legs).
            
    Returns:
        Кортеж (текст, клавиатура).
    """
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
            style = "danger"

        buttons.append((f"{item['emoji']} {item['name']} · {label}", f"buy_armor:{slot}:{key}", style))

    buttons.append((f"{E_BACK} К слотам", "gear:armor_menu", "success"))

    return "\n".join(lines), build_vertical_keyboard_with_styles(buttons)


def generate_top_screen(uid: int, arena_key: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Генерирует экран топа игроков.
    
    Args:
        uid: ID пользователя.
        arena_key: Ключ арены (bronze, silver, gold).
            
    Returns:
        Кортеж (текст, клавиатура).
    """
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

    kb = build_vertical_keyboard_with_styles([
        ("🥉 Бронза", "top:bronze", "danger"),
        ("🥈 Серебро", "top:silver", "primary"),
        ("🥇 Золото", "top:gold", "success"),
        (f"{E_BACK} Назад", "arena:menu", "success"),
    ])

    return "\n".join(lines), kb


def generate_arena_list_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Генерирует список соперников для выбора.
    
    Args:
        uid: ID пользователя.
            
    Returns:
        Кортеж (текст, клавиатура).
    """
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
            build_vertical_keyboard_with_styles([
                ("🎲 Найти", "arena:find", "success"),
                (f"{E_BACK} Назад", "arena:menu", "primary"),
            ])
        )

    buttons = []
    for r in rows:
        buttons.append((f"{r['name'][:16]} · {r['wins']}{E_TROPHY}/{r['losses']}{E_SKULL}", f"duel:pick:{r['user_id']}", "primary"))

    buttons.append((f"{E_BACK} Назад", "arena:menu", "success"))

    return f"{a['emoji']} <b>{a['name']}</b> — соперники:", build_vertical_keyboard_with_styles(buttons)


def generate_profile_text(row: sqlite3.Row) -> str:
    """
    Генерирует текстовое описание профиля игрока.
    
    Args:
        row: Строка из таблицы players.
            
    Returns:
        Многострочная строка с информацией о профиле.
    """
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
    """
    Генерирует клавиатуру для профиля.
    
    Содержит кнопки: Снаряжение, Настройки, Назад.
    
    Args:
        uid: ID пользователя.
            
    Returns:
        InlineKeyboardMarkup с кнопками профиля.
    """
    return build_vertical_keyboard_with_styles([
        ("🎒 Снаряжение", "gear:menu", "primary"),
        (f"{E_SETTINGS} Настройки", "profile:settings", "primary"),
        (f"{E_BACK} Назад", "arena:menu", "success"),
    ])


def generate_settings_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Генерирует экран настроек профиля.
    
    Args:
        uid: ID пользователя.
            
    Returns:
        Кортеж (текст, клавиатура).
    """
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

    kb = build_vertical_keyboard_with_styles([
        (f"{'🔴 Отключить' if auto_accept else '🟢 Включить'} авто-приём", "settings:toggle_auto_accept", "danger" if auto_accept else "success"),
        (f"{E_BACK} Назад к профилю", "profile:back", "primary"),
    ])

    return text, kb


def generate_duel_status_text(duel: Duel, for_uid: int, extra: str = "", timer_left: Optional[int] = None) -> str:
    """
    Генерирует статус боя для конкретного участника.
    
    Args:
        duel: Объект дуэли.
        for_uid: ID пользователя, для которого генерируется статус.
        extra: Дополнительный текст (подсказка).
        timer_left: Оставшееся время на ход.
            
    Returns:
        Отформатированная строка статуса.
    """
    role = duel.get_state_for(for_uid)
    me = duel.get_fighter(for_uid) or duel.a
    opp = duel.get_opponent(for_uid) or duel.b

    # Определяем подсказку
    if role == "attacker" and duel.chosen_variant_idx is None:
        prompt = "🎯 <b>Твой ход</b> — выбери вариант атаки"
    elif role == "attacker":
        prompt = "🎯 <b>Твой ход</b> — выбери зону удара"
    elif role == "defender":
        prompt = f"{E_SHIELD} <b>{duel.get_attacker().name}</b> атакует — выбери, что защищать"
    else:
        prompt = "⏳ Бой идёт…"

    # Добавляем таймер
    if timer_left is not None and role in ("attacker", "defender"):
        prompt += f"\n⏱ Осталось: <b>{timer_left} сек</b>"

    # Лог последних действий
    body = "\n".join(f"  {ln}" for ln in duel.log[-DUEL_LOG_DISPLAY_LIMIT:]) if duel.log else "  <i>Бой начинается…</i>"

    # Заголовок босса
    boss_line = f"{E_BOSS} <b>БОЙ С БОССОМ</b>  ·  награда ×{duel.reward_mult}\n\n" if duel.is_boss else ""

    return (
        f"╔══════════════════════════╗\n"
        f"      ⚔️ <b>РАУНД {duel.round_no}</b>\n"
        f"╚══════════════════════════╝\n\n"
        f"{boss_line}"
        f"┌─ 🔵 <b>ТЫ</b>\n"
        f"{format_fighter_card(me)}\n"
        f"└────────────\n\n"
        f"┌─ 🔴 <b>СОПЕРНИК</b>\n"
        f"{format_fighter_card(opp)}\n"
        f"└────────────\n\n"
        f"📜 <b>Последние действия:</b>\n"
        f"{body}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{prompt}"
        + (f"\n\n{extra}" if extra else "")
    )


def get_attack_variant_kb(uid: int) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру выбора варианта атаки.
    
    Показывает доступные варианты с их параметрами и кулдаунами.
    
    Args:
        uid: ID игрока.
            
    Returns:
        InlineKeyboardMarkup с кнопками вариантов.
    """
    duel = ACTIVE_DUELS.get(uid)
    if not duel:
        return build_vertical_keyboard([])

    weapon = WEAPONS[duel.get_attacker().weapon]
    buttons = []

    for i, v in enumerate(weapon["variants"]):
        cd = duel.get_attacker().attack_cooldowns.get(i, 0)

        if cd > 0:
            # На перезарядке
            text = f"⏳ {i + 1}. {v.name} (КД: {cd}р)"
            buttons.append((text, f"duel:variant_disabled:{i}", "primary"))
        else:
            # Доступна
            effect_text = f" [{v.effect}]" if v.effect else ""
            text = f"{i + 1}. {v.name} · x{v.damage_mult}{effect_text}"
            buttons.append((text, f"duel:variant:{i}", "success"))

    return build_vertical_keyboard_with_styles(buttons) if buttons else build_vertical_keyboard([])


def get_attack_zone_kb() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора зоны атаки."""
    return build_vertical_keyboard_with_styles([
        (f"{E_ZONE_HEAD} Голова ×1.5", "duel:atk:head", "danger"),
        (f"{E_ZONE_TORSO} Торс ×1.0", "duel:atk:torso", "danger"),
        (f"{E_ZONE_ARMS} Руки ×0.8", "duel:atk:arms", "danger"),
        (f"{E_ZONE_LEGS} Ноги ×0.9", "duel:atk:legs", "danger"),
    ])


def get_defend_zone_kb() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора зоны защиты."""
    return build_vertical_keyboard_with_styles([
        (f"{E_ZONE_HEAD} Голова", "duel:def:head", "success"),
        (f"{E_ZONE_TORSO} Торс", "duel:def:torso", "success"),
        (f"{E_ZONE_ARMS} Руки", "duel:def:arms", "success"),
        (f"{E_ZONE_LEGS} Ноги", "duel:def:legs", "success"),
    ])


def get_finish_duel_kb() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру окончания боя."""
    return build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "duel:again", "primary"),
        ("🏠 В главное меню", "arena:menu", "success"),
    ])


def get_challenge_accept_kb(challenger_id: int, target_id: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру принятия/отклонения вызова."""
    return build_vertical_keyboard_with_styles([
        (f"{E_ACCEPT} Принять вызов", f"challenge:accept:{challenger_id}:{target_id}", "success"),
        (f"{E_REJECT} Отклонить", f"challenge:reject:{challenger_id}:{target_id}", "danger"),
    ])


def get_challenge_waiting_kb(challenger_id: int, target_id: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру ожидания ответа на вызов."""
    return build_vertical_keyboard_with_styles([
        (f"{E_REFRESH} Обновить статус", f"challenge:refresh:{challenger_id}:{target_id}", "primary"),
        (f"{E_REJECT} Отменить вызов", f"challenge:cancel:{challenger_id}:{target_id}", "danger"),
    ])


def get_bet_kb(game: str) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора ставки."""
    buttons = [(f"{b} 💎", f"casino:{game}:bet:{b}", "primary") for b in Config.CASINO_BETS]
    buttons.append((f"{E_BACK} Назад", "casino:menu", "success"))
    return build_vertical_keyboard_with_styles(buttons)


def get_darts_mode_kb() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру режимов дротика."""
    return build_vertical_keyboard_with_styles([
        ("🎯 На попадание (×1.9)", "casino:darts:hit", "success"),
        ("💨 На промах (×1.9)", "casino:darts:miss", "danger"),
        (f"{E_BACK} Назад", "casino:menu", "success"),
    ])


def get_basket_mode_kb() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру режимов баскетбола."""
    return build_vertical_keyboard_with_styles([
        ("🏀 На попадание (×1.9)", "casino:basket:hit", "success"),
        ("💨 На промах (×1.9)", "casino:basket:miss", "danger"),
        (f"{E_BACK} Назад", "casino:menu", "success"),
    ])


def get_dice_mode_kb() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру режимов костей."""
    return build_vertical_keyboard_with_styles([
        ("🔢 На число (×6)", "casino:dice:number", "primary"),
        ("⚖️ Чёт / Нечет (×2)", "casino:dice:even_odd", "primary"),
        ("📈 Больше / Меньше (×2)", "casino:dice:high_low", "primary"),
        (f"{E_BACK} Назад", "casino:menu", "success"),
    ])


def get_dice_number_kb(bet: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора числа для костей."""
    buttons = [(f"{i} (×6)", f"casino:dice:num:{bet}:{i}", "primary") for i in range(1, 7)]
    buttons.append((f"{E_BACK} Назад", "casino:dice", "success"))
    return build_vertical_keyboard_with_styles(buttons)


def get_dice_even_odd_kb(bet: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру чёт/нечет для костей."""
    return build_vertical_keyboard_with_styles([
        ("🔵 Чёт (×2)", f"casino:dice:even:{bet}", "primary"),
        ("🔴 Нечет (×2)", f"casino:dice:odd:{bet}", "danger"),
        (f"{E_BACK} Назад", "casino:dice", "success"),
    ])


def get_dice_high_low_kb(bet: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру больше/меньше для костей."""
    return build_vertical_keyboard_with_styles([
        ("📈 Больше (4-6) (×2)", f"casino:dice:high:{bet}", "success"),
        ("📉 Меньше (1-3) (×2)", f"casino:dice:low:{bet}", "danger"),
        (f"{E_BACK} Назад", "casino:dice", "success"),
    ])


def get_roulette_mode_kb() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру режимов рулетки."""
    return build_vertical_keyboard_with_styles([
        ("🎨 На цвет (×2 / ×14)", "casino:roulette:color", "primary"),
        ("⚖️ Чёт / Нечет (×2)", "casino:roulette:even_odd", "primary"),
        ("📈 Половина (×2)", "casino:roulette:half", "primary"),
        ("🔢 На число (×36)", "casino:roulette:number", "danger"),
        ("🎯 На дюжину (×3)", "casino:roulette:dozen", "primary"),
        (f"{E_BACK} Назад", "casino:menu", "success"),
    ])


def get_roulette_color_kb(bet: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора цвета рулетки."""
    return build_vertical_keyboard_with_styles([
        ("🔴 Красное (×2)", f"casino:roulette:color:red:{bet}", "danger"),
        ("⚫ Чёрное (×2)", f"casino:roulette:color:black:{bet}", "primary"),
        ("🟢 Зеро (×14)", f"casino:roulette:color:green:{bet}", "success"),
        (f"{E_BACK} Назад", "casino:roulette", "success"),
    ])


def get_roulette_even_odd_kb(bet: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру чёт/нечет рулетки."""
    return build_vertical_keyboard_with_styles([
        ("🔵 Чёт (×2)", f"casino:roulette:even_odd:even:{bet}", "primary"),
        ("🔴 Нечет (×2)", f"casino:roulette:even_odd:odd:{bet}", "danger"),
        (f"{E_BACK} Назад", "casino:roulette", "success"),
    ])


def get_roulette_half_kb(bet: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру половины рулетки."""
    return build_vertical_keyboard_with_styles([
        ("📉 1-18 (×2)", f"casino:roulette:half:low:{bet}", "primary"),
        ("📈 19-36 (×2)", f"casino:roulette:half:high:{bet}", "success"),
        (f"{E_BACK} Назад", "casino:roulette", "success"),
    ])


def get_roulette_number_kb(bet: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора числа рулетки."""
    buttons = []
    for i in range(0, 37):
        buttons.append((f"{i} (×36)", f"casino:roulette:num:{bet}:{i}", "danger"))
    buttons.append((f"{E_BACK} Назад", "casino:roulette", "success"))
    return build_horizontal_keyboard([(t, c) for t, c, _ in buttons], 3)


def get_roulette_dozen_kb(bet: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора дюжины рулетки."""
    return build_vertical_keyboard_with_styles([
        ("1️⃣ 1-12 (×3)", f"casino:roulette:dozen:1:{bet}", "primary"),
        ("2️⃣ 13-24 (×3)", f"casino:roulette:dozen:2:{bet}", "primary"),
        ("3️⃣ 25-36 (×3)", f"casino:roulette:dozen:3:{bet}", "primary"),
        (f"{E_BACK} Назад", "casino:roulette", "success"),
    ])


def generate_casino_menu(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Генерирует меню казино.
    
    Args:
        uid: ID пользователя.
            
    Returns:
        Кортеж (текст, клавиатура).
    """
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None

    text = (
        f"╔══════════════════════════╗\n"
        f"      {E_SLOT} <b>КАЗИНО</b>\n"
        f"╚══════════════════════════╝\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"<b>Выбери игру:</b>"
    )

    kb = build_vertical_keyboard_with_styles([
        (f"{E_SLOT} Слоты (только комбинация ×10)", "casino:slots", "primary"),
        (f"{E_DICE} Кости (число/чёт/больше)", "casino:dice", "primary"),
        (f"{E_DARTS} Дротик (×1.9)", "casino:darts", "primary"),
        (f"{E_BASKET} Баскетбол (×1.9)", "casino:basket", "primary"),
        ("🎡 Рулетка (цвет/чёт/число)", "casino:roulette", "primary"),
        (f"{E_COIN} Монетка (×2)", "casino:coin", "primary"),
        ("📊 Больше/Меньше (×1.9)", "casino:highlow", "primary"),
        (f"{E_BACK} Назад", "arena:menu", "success"),
    ])

    return text, kb


# ==============================================================================
# 18. HELP С 4 РАЗДЕЛАМИ
# ==============================================================================

HELP_SECTIONS: Dict[str, Dict[str, Any]] = {
    "duels": {
        "title": f"{E_SWORD} <b>⚔️ ДУЭЛИ</b>",
        "text": (
            "• <code>перчатка</code> или <code>перч</code> — вызов с подтверждением\n"
            "• <code>профиль</code> или <code>/profile</code> — статистика\n"
            "• <code>перевод [сумма]</code> — перевести кристаллы\n"
            "• <code>баланс</code> — проверить баланс\n\n"
            "<i>Команды работают ответом на сообщение или через @username / ID</i>"
        ),
    },
    "casino": {
        "title": f"{E_SLOT} <b>🎰 КАЗИНО</b>",
        "text": (
            "• <code>сл [сумма]</code> — слоты ×10\n"
            "• <code>кости число [сумма] [1-6]</code> — ×6\n"
            "• <code>кости чет [сумма] [чет/нечет]</code> — ×2\n"
            "• <code>кости больше [сумма] [больше/меньше]</code> — ×2\n"
            "• <code>дротик [сумма]</code> — ×1.9\n"
            "• <code>дротик промах [сумма]</code> — ×1.9\n"
            "• <code>баскет [сумма]</code> — ×1.9\n"
            "• <code>баскет промах [сумма]</code> — ×1.9\n"
            "• <code>рул цвет [сумма] [к/ч/з]</code>\n"
            "• <code>рул чет [сумма] [чет/нечет]</code>\n"
            "• <code>рул половина [сумма] [верх/низ]</code>\n"
            "• <code>рул число [сумма] [0-36]</code> — ×36\n"
            "• <code>рул дюжина [сумма] [1/2/3]</code> — ×3\n"
            "• <code>мон [сумма] [о/р]</code>\n"
            "• <code>больше [сумма]</code> / <code>меньше [сумма]</code>"
        ),
    },
    "rp": {
        "title": f"{E_MAGIC} <b>🎭 RP ДЕЙСТВИЯ</b>",
        "text": (
            "• <code>ударить</code>, <code>обнять</code>, <code>поцеловать</code>\n"
            "• <code>пнуть</code>, <code>погладить</code>, <code>укусить</code>\n"
            "• <code>пожать</code>, <code>толкнуть</code>, <code>кинуть</code>\n"
            "• <code>лечить</code>, <code>игнор</code>, <code>смеяться</code>\n"
            "• <code>танцевать</code>, <code>шлепнуть</code>, <code>обозвать</code>\n"
            "• <code>покормить</code>, <code>напоить</code>, <code>щекотать</code>\n"
            "• <code>благословить</code>, <code>проклясть</code>, <code>подмигнуть</code>\n\n"
            "<b>👹 События:</b>\n"
            "• <code>атака</code> — ударить босса/караван\n"
            "• <code>событие</code> — статус текущего события\n\n"
            "<b>🎟 Промокоды:</b>\n"
            "• <code>#код [промокод]</code> — активировать\n"
            "• <code>активировать [код]</code> — альтернатива"
        ),
    },
    "admin": {
        "title": f"{E_CROWN} <b>👑 АДМИН</b>",
        "text": (
            "• <code>бан</code> / <code>разбан</code>\n"
            "• <code>выдать [сумма]</code>\n"
            "• <code>событие босс/караван/набег/дракон</code>\n"
            "• <code>босс [ключ]</code> — активировать босса\n"
            "• <code>следующее событие</code>\n"
            "• <code>промо создать/удалить/список</code>\n"
            "• <code>рассылка текст</code>\n"
            "• <code>статистика</code> — статистика бота\n"
            "• <code>список игроков</code> — список всех игроков\n"
            "• <code>очистить ботов</code> — удалить всех ботов\n"
            "• <code>добавить ботов [число]</code> — добавить ботов"
        ),
    },
}


HELP_CHAT_SHORT = (
    f"{E_INFO} <b>КРАТКАЯ СПРАВКА</b>\n\n"
    f"<b>⚔️ Дуэли:</b>\n"
    f"• <code>перчатка</code> — вызвать на бой\n"
    f"• <code>профиль</code> / <code>/profile</code> — статистика\n"
    f"• <code>баланс</code> — проверить баланс\n\n"
    f"<b>💎 Экономика:</b>\n"
    f"• <code>перевод [сумма]</code> — перевести кристаллы\n\n"
    f"<b>🎰 Казино:</b>\n"
    f"• <code>сл 100</code> — слоты\n"
    f"• <code>кости число 100 3</code> — кости\n"
    f"• <code>дротик 100</code> — дротик\n"
    f"• <code>баскет 100</code> — баскетбол\n"
    f"• <code>рул цвет 100 к</code> — рулетка\n"
    f"• <code>мон 100 о</code> — монетка\n\n"
    f"<b>🎭 RP:</b>\n"
    f"• <code>ударить</code>, <code>обнять</code>, <code>поцеловать</code> и др.\n\n"
    f"<b>👹 События:</b>\n"
    f"• <code>атака</code> — ударить босса/караван\n"
    f"• <code>событие</code> — статус события\n\n"
    f"{E_INFO} <i>Полная справка в ЛС с ботом: напиши <code>help</code></i>"
)


def get_help_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру с 4 разделами help."""
    return build_horizontal_keyboard([
        (f"{E_SWORD} Дуэли", "help:section:duels"),
        (f"{E_SLOT} Казино", "help:section:casino"),
        (f"{E_MAGIC} RP", "help:section:rp"),
        (f"{E_CROWN} Админ", "help:section:admin"),
    ], 2)


# ==============================================================================
# 19. РОУТЕР И FSM
# ==============================================================================

router = Router()


class RegistrationState(StatesGroup):
    """Состояния FSM для регистрации нового игрока."""
    waiting_for_name = State()


class DuelFindState(StatesGroup):
    """Состояния FSM для поиска соперника по нику."""
    waiting_for_target = State()


# ==============================================================================
# 20. ХЕНДЛЕРЫ СТАРТА И МЕНЮ
# ==============================================================================

@router.message(CommandStart())
async def handle_start_command(m: Message, state: FSMContext) -> None:
    """
    Обрабатывает команду /start.
    
    Для существующих игроков: приветствие и меню.
    Для новых: запуск регистрации.
    """
    await state.clear()
    ensure_masked_bots_exist(Config.BOT_GENERATION_COUNT)

    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))

    if p:
        # Обновляем username и last_active
        db.execute(
            "UPDATE players SET username=?, last_active=? WHERE user_id=?",
            (m.from_user.username, time.time(), m.from_user.id)
        )

        if m.chat.type == "private":
            await m.answer(
                f"С возвращением, <b>{esc(p['name'])}</b>! Арена ждёт 👇",
                reply_markup=MENU_KB
            )
            await flush_notifications(m)
        else:
            await m.answer(
                f"С возвращением, <b>{esc(p['name'])}</b>! "
                f"Пиши <code>help</code> для списка команд."
            )
        return

    # Новый игрок - запускаем регистрацию
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
    """
    Обрабатывает ввод имени при регистрации.
    
    Валидирует имя и создаёт нового игрока.
    """
    name = " ".join(m.text.split())

    # Валидация длины
    if not MIN_NAME_LENGTH <= len(name) <= MAX_NAME_LENGTH:
        await m.answer(
            f"Имя должно быть от {MIN_NAME_LENGTH} до {MAX_NAME_LENGTH} символов. "
            f"Попробуй ещё раз:"
        )
        return

    # Проверка на слэш в начале
    if name.startswith("/"):
        await m.answer("Имя не может начинаться с '/'. Попробуй ещё раз:")
        return

    # Проверка уникальности
    if db.fetch_one("SELECT 1 FROM players WHERE LOWER(name)=LOWER(?)", (name,)):
        name = f"{name}{random.randint(1, 99)}"

    # Создание игрока
    now = time.time()
    db.execute(
        """INSERT OR IGNORE INTO players
           (user_id, username, name, crystals, wins, losses, weapon,
            armor_head, armor_torso, armor_arms, armor_legs,
            weapons_owned, armors_owned, created, last_active)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            m.from_user.id,
            m.from_user.username,
            name,
            Config.START_CRYSTALS,
            0, 0,
            START_WEAPON,
            "head_none", "torso_none", "arms_none", "legs_none",
            START_WEAPON,
            ",".join(START_ARMOR_KEYS),
            now, now,
        )
    )

    # Инициализация статистики
    db.execute(
        """INSERT OR IGNORE INTO player_stats (user_id) VALUES (?)""",
        (m.from_user.id,)
    )

    ensure_masked_bots_exist(Config.BOT_GENERATION_COUNT)
    await state.clear()

    await m.answer(
        f"Боец <b>{esc(name)}</b> создан! 🎉\n\n"
        f"{E_CRYSTAL} Стартовый баланс: {Config.START_CRYSTALS}\n"
        f"⚔️ Оружие: {WEAPONS[START_WEAPON]['emoji']} {WEAPONS[START_WEAPON]['name']}",
        reply_markup=MENU_KB if m.chat.type == "private" else None
    )


@router.message(Command("profile"))
async def cmd_profile_slash(m: Message) -> None:
    """
    Обрабатывает команду /profile.
    
    Показывает профиль текущего пользователя с inline-кнопками.
    Работает только в ЛС.
    """
    if m.chat.type != "private":
        await m.answer("Команда <code>/profile</code> работает только в ЛС с ботом.")
        return

    row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not row:
        await m.answer("Сначала отправь /start в ЛС бота.")
        return

    text = generate_profile_text(row)
    kb = generate_profile_kb(m.from_user.id)
    await m.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.message(F.text.regexp(r"(?i)^(help|помощь|хелп)$"))
async def handle_help_command(m: Message) -> None:
    """Обрабатывает команду помощи."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        await m.answer("Сначала отправь /start в ЛС бота.")
        return

    if m.chat.type == "private":
        text = (
            f"╔══════════════════════════╗\n"
            f"   ⚔️ <b>АРЕНА ДУЭЛЯНТОВ</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"<b>📋 РАЗДЕЛЫ ПО КНОПКАМ МЕНЮ:</b>\n\n"
            f"{E_SWORD} <b>⚔️ АРЕНА</b> — PvP дуэли и боссы\n"
            f"• Найти соперника — случайный бой\n"
            f"• Боссы — соло-бои с боссами\n"
            f"• Список соперников — выбор из игроков\n"
            f"• Вызвать по нику — поиск по @username\n"
            f"• Топ арен — рейтинг игроков\n\n"
            f"{E_SLOT} <b>🎰 КАЗИНО</b> — Азартные игры\n"
            f"• Слоты — только джекпот ×10\n"
            f"• Кости — на число/чёт/больше\n"
            f"• Дротик — на попадание или промах\n"
            f"• Баскетбол — на попадание или промах\n"
            f"• Рулетка — цвет/чёт/половина/число/дюжина\n"
            f"• Монетка — орёл или решка\n"
            f"• Больше/Меньше — угадай число\n\n"
            f"{E_GIFT} <b>🎒 СНАРЯЖЕНИЕ</b> — Экипировка\n"
            f"• Оружие — 7 видов × 3 варианта атаки\n"
            f"• Броня — 4 слота × 6 предметов\n\n"
            f"{E_TROPHY} <b>🏆 ТОП</b> — Рейтинги\n"
            f"• Бронза — 0-9 побед\n"
            f"• Серебро — 10-29 побед\n"
            f"• Золото — 30+ побед\n\n"
            f"{E_PROFILE} <b>👤 ПРОФИЛЬ</b>\n"
            f"• Команда <code>/profile</code> или <code>профиль</code> — твой профиль\n\n"
            f"<b>📌 ВЫБЕРИ РАЗДЕЛ КОМАНД:</b>"
        )
        await m.answer(text, reply_markup=get_help_keyboard())
        if is_admin(m.from_user.id):
            await m.answer(
                f"{E_CROWN} <b>КОМАНДЫ АДМИНИСТРАТОРА</b>\n\n"
                f"• <code>бан @user</code> или <code>бан ID</code>\n"
                f"• <code>разбан @user</code>\n"
                f"• <code>выдать 1000 @user</code>\n"
                f"• <code>событие босс/караван/набег/дракон</code>\n"
                f"• <code>босс goblin/dragon/lord/titan/demon_king</code>\n"
                f"• <code>следующее событие</code>\n"
                f"• <code>промо создать/удалить/список</code>\n"
                f"• <code>рассылка текст</code>\n"
                f"• <code>статистика</code>\n"
                f"• <code>список игроков</code>\n"
                f"• <code>очистить ботов</code>\n"
                f"• <code>добавить ботов [число]</code>"
            )
    else:
        await m.answer(HELP_CHAT_SHORT)


# ==============================================================================
# 21. CALLBACK HANDLERS HELP
# ==============================================================================

@router.callback_query(F.data.regexp(r"^help:section:(\w+)$"))
async def cb_help_section(cb: CallbackQuery) -> None:
    """Показывает раздел help по кнопке."""
    section_key = cb.data.split(":")[2]
    section = HELP_SECTIONS.get(section_key)

    if not section:
        await cb.answer("Раздел не найден", show_alert=True)
        return

    text = f"{section['title']}\n\n{section['text']}"

    # Кнопка назад и другие разделы
    back_buttons = [
        (f"{E_BACK} Назад к разделам", "help:main", "primary"),
    ]

    # Добавляем кнопки других разделов
    other_sections = [(k, v) for k, v in HELP_SECTIONS.items() if k != section_key]
    for key, sec in other_sections:
        title = sec["title"].split(">")[1].split("<")[0] if ">" in sec["title"] else key
        back_buttons.append((title, f"help:section:{key}", "primary"))

    kb = build_vertical_keyboard_with_styles(back_buttons)

    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "help:main")
async def cb_help_main(cb: CallbackQuery) -> None:
    """Возврат к главным разделам help."""
    text = (
        f"╔══════════════════════════╗\n"
        f"   ⚔️ <b>АРЕНА ДУЭЛЯНТОВ</b>\n"
        f"╚══════════════════════════╝\n\n"
        f"<b>📋 ВЫБЕРИ РАЗДЕЛ КОМАНД:</b>\n\n"
        f"Нажми на кнопку ниже, чтобы увидеть подробные команды раздела."
    )
    await safe_edit_message(cb, text, get_help_keyboard())
    await cb.answer()


# ==============================================================================
# 22. ОБРАБОТЧИКИ МЕНЮ
# ==============================================================================

async def flush_notifications(m: Message) -> None:
    """
    Выводит непрочитанные уведомления игрока и помечает их как прочитанные.
    
    Args:
        m: Объект сообщения для ответа.
    """
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

    await m.answer(
        "📬 <b>Пока тебя не было:</b>\n\n" + "\n\n".join(r["text"] for r in rows)
    )


def is_admin(uid: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    return uid == Config.ADMIN_ID


def is_user_banned(uid: int) -> bool:
    """Проверяет, забанен ли пользователь."""
    p = db.fetch_one("SELECT banned FROM players WHERE user_id=?", (uid,))
    return bool(p and p["banned"])


def notify_player(uid: int, text: str) -> None:
    """
    Добавляет уведомление для игрока в БД.
    
    Args:
        uid: ID получателя уведомления.
        text: Текст уведомления.
    """
    if uid <= 0:
        return
    db.execute(
        "INSERT INTO notifications (user_id, text, ts) VALUES (?,?,?)",
        (uid, text, time.time())
    )


@router.message(F.text.in_(MENU_TEXTS))
async def on_menu_button(m: Message, state: FSMContext) -> None:
    """Обрабатывает кнопки Reply-меню."""
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


# ==============================================================================
# 23. ХЕНДЛЕРЫ ЧАТОВЫХ КОМАНД
# ==============================================================================

@router.message(F.text.regexp(r"(?i)^(перчатка|перч|glove|вызов)(\s|$)"))
async def cmd_challenge_duel(m: Message, bot: Bot) -> None:
    """Обработка вызова на дуэль с подтверждением."""
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
        # Вызов бота - сразу начинаем бой
        await initiate_duel_message(m.from_user.id, tid, m, bot)
        return

    target = db.fetch_one("SELECT * FROM players WHERE user_id=?", (tid,))
    if not target or target["banned"]:
        await m.answer("Игрок не найден или забанен.")
        return

    if tid in ACTIVE_DUELS:
        await m.answer("Этот игрок уже в бою.")
        return

    # Проверка авто-приёма
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
    )
    PENDING_DUELS[key] = pending
    pending.timeout_task = asyncio.create_task(challenge_timeout_task(m.from_user.id, tid, bot))


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


@router.message(F.text.regexp(r"(?i)^перевод(\s|$)"))
async def cmd_transfer(m: Message) -> None:
    """Обработка перевода кристаллов."""
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

    # Извлекаем сумму
    amount = next((int(x) for x in (m.text or "").split() if x.lstrip("-").isdigit()), None)

    if not amount or amount <= 0:
        await m.answer("Укажи сумму: <code>перевод 100 @user</code>")
        return

    # Валидация суммы
    if amount < Config.MIN_TRANSFER:
        await m.answer(f"Минимальная сумма перевода: {Config.MIN_TRANSFER} {E_CRYSTAL}")
        return

    if amount > Config.MAX_TRANSFER:
        await m.answer(f"Максимальная сумма перевода: {Config.MAX_TRANSFER} {E_CRYSTAL}")
        return

    # Проверка баланса
    if p["crystals"] < amount:
        await m.answer(f"Недостаточно кристаллов: у тебя {p['crystals']} {E_CRYSTAL}")
        return

    # Расчёт налога
    tax = int(amount * Config.TRANSFER_TAX)
    net_amount = amount - tax

    # Выполняем перевод
    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (amount, m.from_user.id))
    db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (net_amount, tid))

    await m.answer(
        f"{E_CRYSTAL} Переведено <b>{net_amount}</b> игроку <b>{esc(target['name'])}</b>.\n"
        f"💰 Налог: {tax} ({Config.TRANSFER_TAX * 100:.0f}%)"
    )

    notify_player(
        tid,
        f"{E_CRYSTAL} <b>{esc(p['name'])}</b> перевёл тебе <b>{net_amount}</b> кристаллов!"
    )


@router.message(F.text.regexp(r"(?i)^атака(\s|$)"))
async def cmd_attack_event(m: Message) -> None:
    """Обработка атаки чатового события."""
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
    """Показывает статус текущего чатового события."""
    status = get_chat_event_status()

    if not status:
        await m.answer("Сейчас нет активных чатовых событий.")
        return

    await m.answer(f"📋 <b>Текущее событие:</b>\n\n{status}")


@router.message(F.text.regexp(r"(?i)^(баланс|balance|бал)(\s|$)"))
async def cmd_balance(m: Message) -> None:
    """Показывает баланс игрока."""
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


# ==============================================================================
# 24. RP КОМАНДЫ
# ==============================================================================

async def process_rp_action(m: Message, action_key: str) -> None:
    """
    Обрабатывает RP-действие с проверкой кулдаунов.
    
    Args:
        m: Объект сообщения.
        action_key: Ключ действия из RP_ACTIONS.
    """
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

    # Проверка кулдауна
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

    db.execute("UPDATE player_stats SET rp_actions_used=rp_actions_used+1 WHERE user_id=?", (m.from_user.id,))


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
    """Фабрика хендлеров для RP-действий (исправляет проблему замыкания)."""
    async def handler(m: Message) -> None:
        await process_rp_action(m, action)
    return handler


for action, variants in RP_MAPPINGS.items():
    pattern = r"(?i)^(" + "|".join(re.escape(v) for v in variants) + r")(\s|$)"
    router.message(F.text.regexp(pattern))(_create_rp_handler(action))


# ==============================================================================
# 25. КАЗИНО В ЧАТЕ
# ==============================================================================

@router.message(F.text.regexp(r"(?i)^(слоты|slot|сл)(\s+)(\d+)$"))
async def cmd_chat_slots(m: Message, bot: Bot) -> None:
    """Обработка команды слотов."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return

    bet = int(m.text.split()[-1])
    result, err = await play_casino_slots_animated(m.chat.id, bet, m.from_user.id, bot)
    if err:
        await m.answer(err)
        return

    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^кости число(\s+)(\d+)(\s+)([1-6])$"))
async def cmd_dice_number(m: Message, bot: Bot) -> None:
    """Обработка команды костей на число."""
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
    """Обработка команды костей чёт/нечет."""
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
    """Обработка команды костей больше/меньше."""
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


@router.message(F.text.regexp(r"(?i)^(дротик|darts|дрот)(\s+)(промах\s+)?(\d+)$"))
async def cmd_chat_darts(m: Message, bot: Bot) -> None:
    """Обработка команды дротика."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return

    bet_on_miss = "промах" in m.text.lower()
    bet = int(m.text.split()[-1])
    result, err = await play_casino_darts_animated(m.chat.id, bet, m.from_user.id, bot, bet_on_miss)
    if err:
        await m.answer(err)
        return

    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^(баскет|basketball|баск)(\s+)(промах\s+)?(\d+)$"))
async def cmd_chat_basketball(m: Message, bot: Bot) -> None:
    """Обработка команды баскетбола."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return

    bet_on_miss = "промах" in m.text.lower()
    bet = int(m.text.split()[-1])
    result, err = await play_casino_basketball_animated(m.chat.id, bet, m.from_user.id, bot, bet_on_miss)
    if err:
        await m.answer(err)
        return

    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^(монетка|coin|мон)(\s+)(\d+)(\s+)(орел|решка|о|р)$"))
async def cmd_chat_coin(m: Message) -> None:
    """Обработка команды монетки."""
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
    """Обработка команды рулетки на цвет."""
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
    """Обработка команды рулетки чёт/нечет."""
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
    """Обработка команды рулетки на половину."""
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
    """Обработка команды рулетки на число."""
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
    """Обработка команды рулетки на дюжину."""
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
    """Обработка команды больше."""
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
    """Обработка команды меньше."""
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


# ==============================================================================
# 26. АДМИН КОМАНДЫ
# ==============================================================================

@router.message(F.text.regexp(r"(?i)^событие босс$"))
async def adm_spawn_boss(m: Message) -> None:
    """Админ: создание рейдового босса."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
        return

    event = spawn_chat_event("boss", m.from_user.id)
    if not event:
        await m.answer("Событие уже активно!")
        return

    template = CHAT_EVENT_TEMPLATES["boss"]
    await m.answer(template["announce_text"].format(emoji=template["emoji"], hp=event.hp))


@router.message(F.text.regexp(r"(?i)^событие караван$"))
async def adm_spawn_caravan(m: Message) -> None:
    """Админ: создание каравана."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
        return

    event = spawn_chat_event("caravan", m.from_user.id)
    if not event:
        await m.answer("Событие уже активно!")
        return

    template = CHAT_EVENT_TEMPLATES["caravan"]
    await m.answer(template["announce_text"].format(emoji=template["emoji"], hp=event.hp))


@router.message(F.text.regexp(r"(?i)^событие набег$"))
async def adm_spawn_raid(m: Message) -> None:
    """Админ: создание набега."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
        return

    event = spawn_chat_event("raid", m.from_user.id)
    if not event:
        await m.answer("Событие уже активно!")
        return

    template = CHAT_EVENT_TEMPLATES["raid"]
    await m.answer(template["announce_text"].format(emoji=template["emoji"], hp=event.hp))


@router.message(F.text.regexp(r"(?i)^событие дракон$"))
async def adm_spawn_dragon_raid(m: Message) -> None:
    """Админ: создание нашествия драконов."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
        return

    event = spawn_chat_event("dragon_raid", m.from_user.id)
    if not event:
        await m.answer("Событие уже активно!")
        return

    template = CHAT_EVENT_TEMPLATES["dragon_raid"]
    await m.answer(template["announce_text"].format(emoji=template["emoji"], hp=event.hp))


@router.message(F.text.regexp(r"(?i)^босс(\s+)(\w+)$"))
async def adm_spawn_boss_by_key(m: Message) -> None:
    """Админ: создание конкретного босса."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
        return

    parts = m.text.split()
    bkey = parts[2].lower()
    if bkey not in BOSSES:
        await m.answer(f"❌ Босс <code>{bkey}</code> не найден.\n\nДоступные: {', '.join(BOSSES.keys())}")
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
    """Админ: информация о следующем событии."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
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
    """Админ: бан игрока."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
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
    """Админ: разбан игрока."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
        return

    tid, err = resolve_command_target(m, "разбан")
    if err or not tid:
        await m.answer(err or "Не найдено.")
        return

    db.execute("UPDATE players SET banned=0 WHERE user_id=?", (tid,))
    await m.answer(f"✅ Игрок <code>{tid}</code> разбанен.")


@router.message(F.text.regexp(r"(?i)^выдать(\s|$)"))
async def adm_cmd_give(m: Message) -> None:
    """Админ: выдача кристаллов."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
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
    """Админ: создание промокода."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
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
    """Админ: удаление промокода."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
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
    """Админ: список промокодов."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
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
    """Админ: рассылка сообщения всем игрокам."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
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


@router.message(F.text.regexp(r"(?i)^статистика$"))
async def adm_cmd_stats(m: Message) -> None:
    """Админ: статистика бота."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
        return

    total_players = db.fetch_one("SELECT COUNT(*) c FROM players WHERE is_bot=0")["c"]
    total_bots = db.fetch_one("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    banned_players = db.fetch_one("SELECT COUNT(*) c FROM players WHERE banned=1")["c"]
    active_duels = len(ACTIVE_DUELS)
    active_event = "Да" if ACTIVE_CHAT_EVENT and ACTIVE_CHAT_EVENT.is_active() else "Нет"

    text = (
        f"{E_STATS} <b>СТАТИСТИКА БОТА</b>\n\n"
        f"👥 Всего игроков: <b>{total_players}</b>\n"
        f"🤖 Всего ботов: <b>{total_bots}</b>\n"
        f"🚫 Забанено: <b>{banned_players}</b>\n"
        f"⚔️ Активных дуэлей: <b>{active_duels}</b>\n"
        f"👹 Активное событие: <b>{active_event}</b>"
    )
    await m.answer(text)


@router.message(F.text.regexp(r"(?i)^список игроков$"))
async def adm_cmd_list_players(m: Message) -> None:
    """Админ: список игроков."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
        return

    players = db.fetch_all("SELECT user_id, name, wins, crystals FROM players WHERE is_bot=0 ORDER BY wins DESC LIMIT 20")
    if not players:
        await m.answer("Игроков не найдено.")
        return

    lines = [f"{E_USERS} <b>СПИСОК ИГРОКОВ (Топ 20)</b>\n"]
    for i, p in enumerate(players, 1):
        lines.append(f"{i}. <b>{esc(p['name'])}</b> — {p['wins']}🏆 / {p['crystals']}💎")

    await m.answer("\n".join(lines))


@router.message(F.text.regexp(r"(?i)^очистить ботов$"))
async def adm_cmd_clear_bots(m: Message) -> None:
    """Админ: очистка ботов."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
        return

    db.execute("DELETE FROM players WHERE is_bot=1")
    await m.answer("✅ Все боты удалены.")


@router.message(F.text.regexp(r"(?i)^добавить ботов(\s+)(\d+)$"))
async def adm_cmd_add_bots(m: Message) -> None:
    """Админ: добавление ботов."""
    if not is_admin(m.from_user.id):
        await m.answer(f"{E_WARNING} У тебя нет прав администратора.")
        return

    parts = m.text.split()
    count = int(parts[2])
    if count < 1 or count > 100:
        await m.answer("Количество ботов должно быть от 1 до 100.")
        return

    before = db.fetch_one("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    ensure_masked_bots_exist(before + count)
    after = db.fetch_one("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]

    await m.answer(f"✅ Добавлено {after - before} ботов.")


# ==============================================================================
# 27. СИСТЕМА ВЫЗОВОВ
# ==============================================================================

async def send_challenge_messages(
    challenger_id: int,
    target_id: int,
    challenger_name: str,
    target_name: str,
    bot: Bot,
    direct: bool = False
) -> Tuple[Optional[Message], Optional[Message]]:
    """
    Отправляет сообщения вызова обоим участникам.
    
    Args:
        challenger_id: ID вызывающего.
        target_id: ID вызываемого.
        challenger_name: Имя вызывающего.
        target_name: Имя вызываемого.
        bot: Объект бота.
        direct: Прямой вызов (без подтверждения).
            
    Returns:
        Кортеж (сообщение вызывающего, сообщение вызываемого).
    """
    challenger_msg = None
    target_msg = None

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
    """
    Задача таймаута вызова.
    
    Автоматически отклоняет вызов, если не получен ответ в течение
    Config.CHALLENGE_TIMEOUT секунд.
    """
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


# ==============================================================================
# 28. CALLBACK HANDLERS
# ==============================================================================

@router.callback_query(F.data.regexp(r"^challenge:accept:(-?\d+):(-?\d+)$"))
async def cb_challenge_accept(cb: CallbackQuery, bot: Bot) -> None:
    """Принятие вызова на дуэль."""
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
    """Отклонение вызова на дуэль."""
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
    """Отмена вызова на дуэль."""
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
    """Обновление статуса вызова."""
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
    """Настройки профиля."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return

    text, kb = generate_settings_screen(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "settings:toggle_auto_accept")
async def cb_toggle_auto_accept(cb: CallbackQuery) -> None:
    """Переключение авто-приёма вызовов."""
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
    """Возврат к профилю."""
    row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not row:
        await cb.answer("Сначала /start", show_alert=True)
        return

    await safe_edit_message(cb, generate_profile_text(row), generate_profile_kb(cb.from_user.id))
    await cb.answer()


@router.callback_query(F.data == "casino:menu")
async def cb_casino_menu(cb: CallbackQuery) -> None:
    """Меню казино."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return

    text, kb = generate_casino_menu(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:slots")
async def cb_casino_slots(cb: CallbackQuery) -> None:
    """Слоты."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return

    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_SLOT} <b>СЛОТЫ</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"<b>Правила:</b>\n"
        f"• Выпадает 1 символ (🎰 анимация)\n"
        f"• <b>1</b> = ДЖЕКПОТ ×10\n"
        f"• Другие значения = проигрыш\n\n"
        f"<b>Выбери ставку:</b>"
    )
    await safe_edit_message(cb, text, get_bet_kb("slots"))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:slots:bet:(\d+)$"))
async def cb_casino_slots_bet(cb: CallbackQuery, bot: Bot) -> None:
    """Ставка в слотах."""
    bet = int(cb.data.split(":")[3])
    result, err = await play_casino_slots_animated(cb.message.chat.id, bet, cb.from_user.id, bot)
    if err:
        await cb.answer(err, show_alert=True)
        return

    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:slots", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:dice")
async def cb_casino_dice(cb: CallbackQuery) -> None:
    """Кости."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return

    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_DICE} <b>КОСТИ</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"<b>Выбери режим игры:</b>"
    )
    await safe_edit_message(cb, text, get_dice_mode_kb())
    await cb.answer()


@router.callback_query(F.data == "casino:dice:number")
async def cb_casino_dice_number(cb: CallbackQuery) -> None:
    """Кости на число."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_DICE} <b>КОСТИ — НА ЧИСЛО (×6)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    kb = build_vertical_keyboard_with_styles([
        (f"{b} 💎", f"casino:dice:number:bet:{b}", "primary") for b in Config.CASINO_BETS
    ] + [[(f"{E_BACK} Назад", "casino:dice", "success")]])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:dice:number:bet:(\d+)$"))
async def cb_casino_dice_number_bet(cb: CallbackQuery) -> None:
    """Выбор числа для костей."""
    bet = int(cb.data.split(":")[4])
    text = (
        f"{E_DICE} <b>КОСТИ — НА ЧИСЛО</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери число от 1 до 6:"
    )
    await safe_edit_message(cb, text, get_dice_number_kb(bet))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:dice:num:(\d+):(\d+)$"))
async def cb_casino_dice_num(cb: CallbackQuery, bot: Bot) -> None:
    """Игра в кости на число."""
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
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:dice:number", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:dice:even_odd")
async def cb_casino_dice_even_odd(cb: CallbackQuery) -> None:
    """Кости чёт/нечет."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_DICE} <b>КОСТИ — ЧЁТ/НЕЧЕТ (×2)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    kb = build_vertical_keyboard_with_styles([
        (f"{b} 💎", f"casino:dice:even_odd:bet:{b}", "primary") for b in Config.CASINO_BETS
    ] + [[(f"{E_BACK} Назад", "casino:dice", "success")]])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:dice:even_odd:bet:(\d+)$"))
async def cb_casino_dice_even_odd_bet(cb: CallbackQuery) -> None:
    """Выбор чёт/нечет для костей."""
    bet = int(cb.data.split(":")[4])
    text = (
        f"{E_DICE} <b>КОСТИ — ЧЁТ/НЕЧЕТ</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери:"
    )
    await safe_edit_message(cb, text, get_dice_even_odd_kb(bet))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:dice:(even|odd):(\d+)$"))
async def cb_casino_dice_even_odd_play(cb: CallbackQuery, bot: Bot) -> None:
    """Игра в кости чёт/нечет."""
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
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:dice:even_odd", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:dice:high_low")
async def cb_casino_dice_high_low(cb: CallbackQuery) -> None:
    """Кости больше/меньше."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_DICE} <b>КОСТИ — БОЛЬШЕ/МЕНЬШЕ (×2)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"• Больше: 4, 5, 6\n"
        f"• Меньше: 1, 2, 3\n\n"
        f"Выбери ставку:"
    )
    kb = build_vertical_keyboard_with_styles([
        (f"{b} 💎", f"casino:dice:high_low:bet:{b}", "primary") for b in Config.CASINO_BETS
    ] + [[(f"{E_BACK} Назад", "casino:dice", "success")]])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:dice:high_low:bet:(\d+)$"))
async def cb_casino_dice_high_low_bet(cb: CallbackQuery) -> None:
    """Выбор больше/меньше для костей."""
    bet = int(cb.data.split(":")[4])
    text = (
        f"{E_DICE} <b>КОСТИ — БОЛЬШЕ/МЕНЬШЕ</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери:"
    )
    await safe_edit_message(cb, text, get_dice_high_low_kb(bet))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:dice:(high|low):(\d+)$"))
async def cb_casino_dice_high_low_play(cb: CallbackQuery, bot: Bot) -> None:
    """Игра в кости больше/меньше."""
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
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:dice:high_low", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:darts")
async def cb_casino_darts(cb: CallbackQuery) -> None:
    """Дротик."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return

    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_DARTS} <b>ДРОТИК</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"<b>Правила:</b>\n"
        f"• Выпадает 1-6\n"
        f"• 4, 5, 6 = попадание\n"
        f"• 1, 2, 3 = промах\n\n"
        f"<b>Выбери режим:</b>"
    )
    await safe_edit_message(cb, text, get_darts_mode_kb())
    await cb.answer()


@router.callback_query(F.data == "casino:darts:hit")
async def cb_casino_darts_hit(cb: CallbackQuery) -> None:
    """Дротик на попадание."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_DARTS} <b>ДРОТИК — НА ПОПАДАНИЕ (×1.9)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    await safe_edit_message(cb, text, get_bet_kb("darts:hit"))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:darts:hit:bet:(\d+)$"))
async def cb_casino_darts_hit_bet(cb: CallbackQuery, bot: Bot) -> None:
    """Игра в дротик на попадание."""
    bet = int(cb.data.split(":")[4])
    result, err = await play_casino_darts_animated(cb.message.chat.id, bet, cb.from_user.id, bot, False)
    if err:
        await cb.answer(err, show_alert=True)
        return

    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:darts:hit", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:darts:miss")
async def cb_casino_darts_miss(cb: CallbackQuery) -> None:
    """Дротик на промах."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_DARTS} <b>ДРОТИК — НА ПРОМАХ (×1.9)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    await safe_edit_message(cb, text, get_bet_kb("darts:miss"))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:darts:miss:bet:(\d+)$"))
async def cb_casino_darts_miss_bet(cb: CallbackQuery, bot: Bot) -> None:
    """Игра в дротик на промах."""
    bet = int(cb.data.split(":")[4])
    result, err = await play_casino_darts_animated(cb.message.chat.id, bet, cb.from_user.id, bot, True)
    if err:
        await cb.answer(err, show_alert=True)
        return

    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:darts:miss", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:basket")
async def cb_casino_basket(cb: CallbackQuery) -> None:
    """Баскетбол."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return

    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_BASKET} <b>БАСКЕТБОЛ</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"<b>Правила:</b>\n"
        f"• Выпадает 1-5\n"
        f"• 5 = слэм-данк (попадание)\n"
        f"• 1-4 = промах\n\n"
        f"<b>Выбери режим:</b>"
    )
    await safe_edit_message(cb, text, get_basket_mode_kb())
    await cb.answer()


@router.callback_query(F.data == "casino:basket:hit")
async def cb_casino_basket_hit(cb: CallbackQuery) -> None:
    """Баскетбол на попадание."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_BASKET} <b>БАСКЕТБОЛ — НА ПОПАДАНИЕ (×1.9)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    await safe_edit_message(cb, text, get_bet_kb("basket:hit"))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:basket:hit:bet:(\d+)$"))
async def cb_casino_basket_hit_bet(cb: CallbackQuery, bot: Bot) -> None:
    """Игра в баскетбол на попадание."""
    bet = int(cb.data.split(":")[4])
    result, err = await play_casino_basketball_animated(cb.message.chat.id, bet, cb.from_user.id, bot, False)
    if err:
        await cb.answer(err, show_alert=True)
        return

    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:basket:hit", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:basket:miss")
async def cb_casino_basket_miss(cb: CallbackQuery) -> None:
    """Баскетбол на промах."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_BASKET} <b>БАСКЕТБОЛ — НА ПРОМАХ (×1.9)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    await safe_edit_message(cb, text, get_bet_kb("basket:miss"))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:basket:miss:bet:(\d+)$"))
async def cb_casino_basket_miss_bet(cb: CallbackQuery, bot: Bot) -> None:
    """Игра в баскетбол на промах."""
    bet = int(cb.data.split(":")[4])
    result, err = await play_casino_basketball_animated(cb.message.chat.id, bet, cb.from_user.id, bot, True)
    if err:
        await cb.answer(err, show_alert=True)
        return

    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{result}\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>\n\n"
        f"Выбери действие:"
    )
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:basket:miss", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:roulette")
async def cb_casino_roulette(cb: CallbackQuery) -> None:
    """Рулетка."""
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
    """Рулетка на цвет."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"🎨 <b>РУЛЕТКА — НА ЦВЕТ</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"• 🔴 Красное / ⚫ Чёрное = ×2\n"
        f"• 🟢 Зеро = ×14\n\n"
        f"Выбери ставку:"
    )
    kb = build_vertical_keyboard_with_styles([
        (f"{b} 💎", f"casino:roulette:color:bet:{b}", "primary") for b in Config.CASINO_BETS
    ] + [[(f"{E_BACK} Назад", "casino:roulette", "success")]])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:color:bet:(\d+)$"))
async def cb_roulette_color_bet(cb: CallbackQuery) -> None:
    """Выбор цвета рулетки."""
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
    """Игра в рулетку на цвет."""
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
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:roulette:color", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:roulette:even_odd")
async def cb_roulette_even_odd(cb: CallbackQuery) -> None:
    """Рулетка чёт/нечет."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"⚖️ <b>РУЛЕТКА — ЧЁТ/НЕЧЕТ (×2)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    kb = build_vertical_keyboard_with_styles([
        (f"{b} 💎", f"casino:roulette:even_odd:bet:{b}", "primary") for b in Config.CASINO_BETS
    ] + [[(f"{E_BACK} Назад", "casino:roulette", "success")]])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:even_odd:bet:(\d+)$"))
async def cb_roulette_even_odd_bet(cb: CallbackQuery) -> None:
    """Выбор чёт/нечет рулетки."""
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
    """Игра в рулетку чёт/нечет."""
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
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:roulette:even_odd", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:roulette:half")
async def cb_roulette_half(cb: CallbackQuery) -> None:
    """Рулетка половина."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"📈 <b>РУЛЕТКА — ПОЛОВИНА (×2)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"• 1-18 (низ)\n"
        f"• 19-36 (верх)\n\n"
        f"Выбери ставку:"
    )
    kb = build_vertical_keyboard_with_styles([
        (f"{b} 💎", f"casino:roulette:half:bet:{b}", "primary") for b in Config.CASINO_BETS
    ] + [[(f"{E_BACK} Назад", "casino:roulette", "success")]])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:half:bet:(\d+)$"))
async def cb_roulette_half_bet(cb: CallbackQuery) -> None:
    """Выбор половины рулетки."""
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
    """Игра в рулетку половина."""
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
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:roulette:half", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:roulette:number")
async def cb_roulette_number(cb: CallbackQuery) -> None:
    """Рулетка на число."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"🔢 <b>РУЛЕТКА — НА ЧИСЛО (×36)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    kb = build_vertical_keyboard_with_styles([
        (f"{b} 💎", f"casino:roulette:number:bet:{b}", "danger") for b in Config.CASINO_BETS
    ] + [[(f"{E_BACK} Назад", "casino:roulette", "success")]])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:number:bet:(\d+)$"))
async def cb_roulette_number_bet(cb: CallbackQuery) -> None:
    """Выбор числа рулетки."""
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
    """Игра в рулетку на число."""
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
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:roulette:number", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:roulette:dozen")
async def cb_roulette_dozen(cb: CallbackQuery) -> None:
    """Рулетка на дюжину."""
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"🎯 <b>РУЛЕТКА — НА ДЮЖИНУ (×3)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    kb = build_vertical_keyboard_with_styles([
        (f"{b} 💎", f"casino:roulette:dozen:bet:{b}", "primary") for b in Config.CASINO_BETS
    ] + [[(f"{E_BACK} Назад", "casino:roulette", "success")]])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:roulette:dozen:bet:(\d+)$"))
async def cb_roulette_dozen_bet(cb: CallbackQuery) -> None:
    """Выбор дюжины рулетки."""
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
    """Игра в рулетку на дюжину."""
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
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:roulette:dozen", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:coin")
async def cb_casino_coin(cb: CallbackQuery) -> None:
    """Монетка."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return

    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (cb.from_user.id,))
    text = (
        f"{E_COIN} <b>МОНЕТКА (×2)</b>\n\n"
        f"{E_CRYSTAL} Баланс: <b>{format_number(p['crystals'])}</b>\n\n"
        f"Выбери ставку:"
    )
    kb = build_vertical_keyboard_with_styles([
        (f"{b} 💎", f"casino:coin:bet:{b}", "primary") for b in Config.CASINO_BETS
    ] + [[(f"{E_BACK} Назад", "casino:menu", "success")]])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:coin:bet:(\d+)$"))
async def cb_casino_coin_bet(cb: CallbackQuery) -> None:
    """Выбор ставки монетки."""
    bet = int(cb.data.split(":")[3])
    text = (
        f"{E_COIN} <b>МОНЕТКА</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери:"
    )
    kb = build_vertical_keyboard_with_styles([
        ("🔵 Орёл (×2)", f"casino:coin:heads:{bet}", "primary"),
        ("🔴 Решка (×2)", f"casino:coin:tails:{bet}", "danger"),
        (f"{E_BACK} Назад", "casino:coin", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:coin:(heads|tails):(\d+)$"))
async def cb_casino_coin_play(cb: CallbackQuery) -> None:
    """Игра в монетку."""
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
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:coin", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "casino:highlow")
async def cb_casino_highlow(cb: CallbackQuery) -> None:
    """Больше/Меньше."""
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
    kb = build_vertical_keyboard_with_styles([
        (f"{b} 💎", f"casino:highlow:bet:{b}", "primary") for b in Config.CASINO_BETS
    ] + [[(f"{E_BACK} Назад", "casino:menu", "success")]])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:highlow:bet:(\d+)$"))
async def cb_casino_highlow_bet(cb: CallbackQuery) -> None:
    """Выбор ставки больше/меньше."""
    bet = int(cb.data.split(":")[3])
    text = (
        f"📊 <b>БОЛЬШЕ/МЕНЬШЕ</b>\n\n"
        f"Ставка: <b>{bet} 💎</b>\n\n"
        f"Выбери:"
    )
    kb = build_vertical_keyboard_with_styles([
        ("📈 Больше (51-100) (×1.9)", f"casino:highlow:high:{bet}", "success"),
        ("📉 Меньше (1-49) (×1.9)", f"casino:highlow:low:{bet}", "danger"),
        (f"{E_BACK} Назад", "casino:highlow", "primary"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^casino:highlow:(high|low):(\d+)$"))
async def cb_casino_highlow_play(cb: CallbackQuery) -> None:
    """Игра в больше/меньше."""
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
    kb = build_vertical_keyboard_with_styles([
        ("🔁 Ещё раз", "casino:highlow", "primary"),
        (f"{E_BACK} В казино", "casino:menu", "success"),
    ])
    await safe_edit_message(cb, text, kb)
    await cb.answer()


# ==============================================================================
# 29. ЛОГИКА ДУЭЛЕЙ
# ==============================================================================

def initiate_duel(
    a_id: int,
    b_id: int,
    is_boss: bool = False,
    boss_key: Optional[str] = None,
    reward_mult: int = 1
) -> Optional[Duel]:
    """
    Создаёт и инициализирует объект дуэли.
    
    Args:
        a_id: ID первого бойца.
        b_id: ID второго бойца (-1 для босса).
        is_boss: True если это бой с боссом.
        boss_key: Ключ босса из BOSSES.
        reward_mult: Множитель награды.
            
    Returns:
        Объект Duel или None при ошибке.
    """
    a_row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (a_id,))
    if not a_row:
        return None

    fa = create_fighter_from_db(a_row)

    # Создание второго бойца
    if is_boss and boss_key and boss_key in BOSSES:
        boss_data = BOSSES[boss_key]
        fb = Fighter(
            name=boss_data["name"],
            max_hp=boss_data["hp"],
            hp=boss_data["hp"],
            weapon=boss_data["weapon"],
            armor_slots=boss_data["armor_keys"],
        )
    else:
        b_row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (b_id,))
        if not b_row:
            return None
        fb = create_fighter_from_db(b_row)

    # Создание дуэли
    duel = Duel(
        a_id=a_id,
        b_id=b_id,
        a=fa,
        b=fb,
        attacker_is_a=random.random() < 0.5,
        is_boss=is_boss,
        boss_key=boss_key,
        reward_mult=reward_mult,
    )

    # Начальное сообщение в лог
    first_attacker = fa.name if duel.attacker_is_a else fb.name
    prefix = f"{E_BOSS} <b>БОСС</b> " if is_boss else ""
    duel.add_log(f"{prefix}Бой начался! Первым атакует <b>{first_attacker}</b>.")

    # Регистрация в глобальном хранилище
    ACTIVE_DUELS[a_id] = duel
    if b_id > 0:
        ACTIVE_DUELS[b_id] = duel

    return duel


async def initiate_duel_message(
    aid: int,
    bid: int,
    m: Message,
    bot: Bot,
    is_boss: bool = False,
    boss_key: Optional[str] = None,
    reward_mult: int = 1
) -> None:
    """
    Отправляет начальные сообщения о дуэли и запускает таймеры.
    
    Args:
        aid: ID инициатора.
        bid: ID противника.
        m: Исходное сообщение.
        bot: Объект бота.
        is_boss: Бой с боссом.
        boss_key: Ключ босса.
        reward_mult: Множитель награды.
    """
    # Проверки
    if bid == aid:
        await m.answer("🤨 Нельзя драться с самим собой.")
        return

    if aid in ACTIVE_DUELS:
        await m.answer("У тебя уже идёт активный бой.")
        return

    # Создание дуэли
    duel = initiate_duel(aid, bid, is_boss, boss_key, reward_mult)
    if not duel:
        await m.answer("Не удалось начать бой (соперник недоступен).")
        return

    # Определение роли
    role = duel.get_state_for(aid)

    if role == "attacker":
        # Атакующий - выбор варианта атаки
        await m.answer(
            generate_duel_status_text(duel, aid, timer_left=Config.TURN_TIMEOUT),
            reply_markup=get_attack_variant_kb(aid)
        )
        start_duel_timer(duel, aid, "attacker", bot)
    else:
        # Защищающийся
        atk_id = duel.get_attacker_id()

        if atk_id < 0:
            # Бот атакует первым
            variant_idx = bot_decide_attack_variant(duel.get_attacker())
            duel.chosen_variant_idx = variant_idx
            duel.atk_zone = bot_decide_attack_zone(duel.get_attacker(), duel.get_defender())

            await m.answer(
                generate_duel_status_text(
                    duel, aid,
                    extra="⚔️ Соперник уже выбрал удар.",
                    timer_left=Config.TURN_TIMEOUT
                ),
                reply_markup=get_defend_zone_kb()
            )
            start_duel_timer(duel, aid, "defender", bot)
        else:
            # Ожидание хода противника
            await m.answer(
                generate_duel_status_text(duel, aid, extra="⏳ Соперник выбирает удар…"),
                reply_markup=build_vertical_keyboard_with_styles([("🔄 Обновить", "duel:refresh", "primary")])
            )

    # Уведомление противника
    if bid > 0 and not is_boss:
        attacker_name = db.fetch_one("SELECT name FROM players WHERE user_id=?", (aid,))["name"]
        notify_player(
            bid,
            f"{E_GLOVE} <b>{esc(attacker_name)}</b> кинул тебе перчатку! "
            f"Открой «⚔️ Арена» в ЛС бота."
        )


async def process_duel_round(
    duel: Duel,
    bot: Bot,
    cb: Optional[CallbackQuery],
    atk_zone: str,
    def_zone: Optional[str]
) -> None:
    """
    Обрабатывает один раунд боя.
    
    Args:
        duel: Объект дуэли.
        bot: Объект бота.
        cb: CallbackQuery (если из inline-кнопки).
        atk_zone: Зона атаки.
        def_zone: Зона защиты.
    """
    if duel.finished:
        return

    stop_duel_timer(duel)

    attacker = duel.get_attacker()
    defender = duel.get_defender()

    # Лог раунда
    duel.add_log(f"── Раунд {duel.round_no} ──")
    duel.add_log(f"⚔️ {attacker.name} → {ZONE_INFO[atk_zone]['emoji']} {ZONE_INFO[atk_zone]['name']}")

    if def_zone:
        duel.add_log(f"🛡 {defender.name} → {ZONE_INFO[def_zone]['emoji']} {ZONE_INFO[def_zone]['name']}")

    # Обработка DoT в начале хода
    process_dots(attacker, duel.log)
    if not attacker.is_alive():
        await finalize_duel(duel, winner_is_a=(attacker is duel.b), bot=bot)
        return

    # Выполнение атаки
    execute_attack_phase(attacker, defender, atk_zone, def_zone, duel.chosen_variant_idx, duel.log)

    # Проверка смерти защищающегося
    if not defender.is_alive():
        await finalize_duel(duel, winner_is_a=(defender is duel.a), bot=bot)
        return

    # Подготовка следующего раунда
    duel.atk_zone = None
    duel.def_zone = None
    duel.chosen_variant_idx = None
    duel.attacker_is_a = not duel.attacker_is_a
    duel.round_no += 1

    # Уменьшение кулдаунов
    attacker.reduce_cooldowns()
    defender.reduce_cooldowns()

    # Сброс серии блоков
    if duel.round_no - duel.bot_last_block_round > 4:
        duel.bot_block_streak = 0

    await start_next_duel_round(duel, bot)


async def start_next_duel_round(duel: Duel, bot: Bot) -> None:
    """
    Инициализирует следующий раунд.
    
    Args:
        duel: Объект дуэли.
        bot: Объект бота.
    """
    if duel.finished:
        return

    atk_id = duel.get_attacker_id()
    def_id = duel.get_defender_id()

    if atk_id > 0:
        # Игрок атакует
        await bot.send_message(
            atk_id,
            generate_duel_status_text(
                duel, atk_id,
                extra="🎯 Твой ход — выбери вариант атаки.",
                timer_left=Config.TURN_TIMEOUT
            ),
            reply_markup=get_attack_variant_kb(atk_id)
        )
        start_duel_timer(duel, atk_id, "attacker", bot)
    else:
        # Бот атакует
        variant_idx = bot_decide_attack_variant(duel.get_attacker())
        duel.chosen_variant_idx = variant_idx
        duel.atk_zone = bot_decide_attack_zone(duel.get_attacker(), duel.get_defender())

        weapon_data = WEAPONS[duel.get_attacker().weapon]
        variant_name = weapon_data["variants"][variant_idx].name
        duel.add_log(f"⚔️ {duel.get_attacker().name} использует [{variant_name}]")

        if def_id > 0:
            await bot.send_message(
                def_id,
                generate_duel_status_text(
                    duel, def_id,
                    extra=f"{E_SHIELD} Соперник атакует — выбери зону защиты.",
                    timer_left=Config.TURN_TIMEOUT
                ),
                reply_markup=get_defend_zone_kb()
            )
            start_duel_timer(duel, def_id, "defender", bot)


async def finalize_duel(
    duel: Duel,
    winner_is_a: bool,
    bot: Bot,
    reason: str = "ko"
) -> None:
    """
    Завершает дуэль, начисляет награды и отправляет итоги.
    
    Args:
        duel: Объект дуэли.
        winner_is_a: True если победил a_id.
        bot: Объект бота.
        reason: Причина завершения (ko/timeout).
    """
    if duel.finished:
        return

    aid, bid = duel.a_id, duel.b_id

    a_row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (aid,))
    if not a_row:
        terminate_duel(duel)
        return

    mult = duel.reward_mult if duel.is_boss else 1

    if winner_is_a:
        # Победил A
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

        if duel.is_boss:
            db.execute("UPDATE player_stats SET boss_kills=boss_kills+1 WHERE user_id=?", (aid,))
    else:
        # Победил B
        if bid and bid > 0:
            db.execute("UPDATE players SET wins=wins+1, total_duels=total_duels+1 WHERE user_id=?", (bid,))

            current_wins_b = db.fetch_one("SELECT wins FROM players WHERE user_id=?", (bid,))["wins"]
            prize_b = ARENAS[determine_arena(current_wins_b)]["prize"] * mult
            db.execute("UPDATE players SET crystals=crystals+?, total_crystals_earned=total_crystals_earned+? WHERE user_id=?",
                       (prize_b, prize_b, bid))

            a_name = a_row["name"]
            notify_player(bid, f"{E_TROPHY} <b>{esc(a_name)}</b> проиграл тебе! +1 {E_TROPHY}, +{prize_b} {E_CRYSTAL}")

            if duel.is_boss:
                db.execute("UPDATE player_stats SET boss_kills=boss_kills+1 WHERE user_id=?", (bid,))

        db.execute(
            "UPDATE players SET losses=losses+1, total_duels=total_duels+1, "
            "wins=CASE WHEN wins>0 THEN wins-1 ELSE 0 END WHERE user_id=?",
            (aid,)
        )
        result_line = f"{E_SKULL} <b>ТЫ ПРОИГРАЛ.</b>  −1 {E_TROPHY}  ·  без награды"

    terminate_duel(duel)

    # Формирование итогового сообщения
    reason_line = f"\n⏱ Соперник не успел за {Config.TURN_TIMEOUT} сек." if reason == "timeout" else ""

    new_a = db.fetch_one("SELECT * FROM players WHERE user_id=?", (aid,))
    a_arena = ARENAS[determine_arena(new_a["wins"])]

    text = (
        f"╔══════════════════════════╗\n"
        f"        ⚔️ <b>ИТОГ БОЯ</b>\n"
        f"╚══════════════════════════╝\n\n"
        f"{result_line}\n\n"
        f"{E_TROPHY} Кубки: <b>{new_a['wins']}</b>\n"
        f"{E_SKULL} Поражения: <b>{new_a['losses']}</b>\n"
        f"{E_CRYSTAL} Кристаллы: <b>{format_number(new_a['crystals'])}</b>\n"
        f"📍 {a_arena['emoji']} {a_arena['name']}"
        f"{reason_line}\n\n"
        f"Выбери действие:"
    )

    try:
        await bot.send_message(aid, text, reply_markup=get_finish_duel_kb())
    except Exception as e:
        logging.error(f"Failed to send duel result to {aid}: {e}")

    # Сообщение для B
    if bid and bid > 0:
        new_b = db.fetch_one("SELECT * FROM players WHERE user_id=?", (bid,))
        if new_b:
            b_arena = ARENAS[determine_arena(new_b["wins"])]
            res_b = (
                f"{E_SKULL} <b>ТЫ ПРОИГРАЛ.</b>  −1 {E_TROPHY}"
                if winner_is_a
                else f"{E_TROPHY} <b>ТЫ ПОБЕДИЛ!</b>  +1 {E_TROPHY}"
            )
            text_b = (
                f"╔══════════════════════════╗\n"
                f"        ⚔️ <b>ИТОГ БОЯ</b>\n"
                f"╚══════════════════════════╝\n\n"
                f"{res_b}\n\n"
                f"{E_TROPHY} Кубки: <b>{new_b['wins']}</b>\n"
                f"{E_SKULL} Поражения: <b>{new_b['losses']}</b>\n"
                f"{E_CRYSTAL} Кристаллы: <b>{format_number(new_b['crystals'])}</b>\n"
                f"📍 {b_arena['emoji']} {b_arena['name']}"
                f"{reason_line}\n\n"
                f"Выбери действие:"
            )
            try:
                await bot.send_message(bid, text_b, reply_markup=get_finish_duel_kb())
            except Exception as e:
                logging.error(f"Failed to send duel result to {bid}: {e}")


# ==============================================================================
# 30. CALLBACK HANDLERS АРЕНЫ И ДУЭЛЕЙ
# ==============================================================================

@router.callback_query(F.data == "arena:menu")
async def cb_arena_menu(cb: CallbackQuery, state: FSMContext) -> None:
    """Callback: главное меню арены."""
    await state.clear()
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    text, kb = generate_arena_menu_screen(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "arena:bosses")
async def cb_arena_bosses(cb: CallbackQuery) -> None:
    """Callback: меню боссов."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    text, kb = generate_bosses_menu_screen(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^arena:boss:\w+$"))
async def cb_arena_boss_fight(cb: CallbackQuery, bot: Bot) -> None:
    """Callback: бой с боссом."""
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
    """Callback: поиск соперника."""
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
    """Callback: список соперников."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    text, kb = generate_arena_list_screen(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "arena:find_name")
async def cb_arena_find_name(cb: CallbackQuery, state: FSMContext) -> None:
    """Callback: поиск по нику."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    await state.set_state(DuelFindState.waiting_for_target)
    await cb.message.answer("🔎 Отправь @username, ID или имя бойца.")
    await cb.answer()


@router.callback_query(F.data.regexp(r"^duel:pick:-?\d+$"))
async def cb_duel_pick(cb: CallbackQuery, bot: Bot) -> None:
    """Callback: выбор соперника из списка."""
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
    """Callback: просмотр профиля соперника."""
    tid = int(cb.data.split(":")[2])
    row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (tid,))
    if not row:
        await cb.answer("Игрок не найден.", show_alert=True)
        return

    await safe_edit_message(
        cb,
        generate_profile_text(row),
        build_vertical_keyboard_with_styles([
            (f"{E_BACK} Назад", "arena:list", "primary"),
            (f"⚔️ Вызвать на бой", f"duel:pick:{tid}", "danger"),
        ])
    )
    await cb.answer()


@router.callback_query(F.data == "duel:myprofile")
async def cb_my_profile(cb: CallbackQuery) -> None:
    """Callback: мой профиль."""
    row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not row:
        await cb.answer("Сначала /start", show_alert=True)
        return

    await safe_edit_message(cb, generate_profile_text(row), generate_profile_kb(cb.from_user.id))
    await cb.answer()


@router.callback_query(F.data == "duel:again")
async def cb_duel_again(cb: CallbackQuery, bot: Bot) -> None:
    """Callback: ещё раз (новый бой)."""
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
    """Callback: выбор варианта атаки."""
    duel = ACTIVE_DUELS.get(cb.from_user.id)
    if not duel or duel.finished or duel.get_state_for(cb.from_user.id) != "attacker":
        await cb.answer("Неверное состояние боя.", show_alert=True)
        return

    if duel.chosen_variant_idx is not None:
        await cb.answer("Вариант уже выбран.", show_alert=True)
        return

    variant_idx = int(cb.data.split(":")[2])

    # Проверка кулдауна
    if variant_idx in duel.get_attacker().attack_cooldowns:
        await cb.answer("Эта атака на перезарядке!", show_alert=True)
        return

    # Валидация индекса
    weapon_data = WEAPONS[duel.get_attacker().weapon]
    if variant_idx >= len(weapon_data["variants"]):
        await cb.answer("Неверный вариант атаки.", show_alert=True)
        return

    duel.chosen_variant_idx = variant_idx

    await safe_edit_message(
        cb,
        generate_duel_status_text(
            duel, cb.from_user.id,
            extra="🎯 Теперь выбери зону удара.",
            timer_left=Config.TURN_TIMEOUT
        ),
        get_attack_zone_kb()
    )
    await cb.answer("Вариант атаки выбран.")


@router.callback_query(F.data.regexp(r"^duel:variant_disabled:\d+$"))
async def cb_duel_variant_disabled(cb: CallbackQuery) -> None:
    """Callback: попытка выбрать недоступный вариант."""
    await cb.answer("Эта атака на перезарядке!", show_alert=True)


@router.callback_query(F.data.regexp(r"^duel:atk:(head|torso|arms|legs)$"))
async def cb_duel_attack(cb: CallbackQuery, bot: Bot) -> None:
    """Callback: выбор зоны атаки."""
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
        # Бот защищается
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
        # Игрок защищается
        await bot.send_message(
            def_id,
            generate_duel_status_text(
                duel, def_id,
                extra=f"⚔️ {duel.get_attacker().name} выбрал зону удара!",
                timer_left=Config.TURN_TIMEOUT
            ),
            reply_markup=get_defend_zone_kb()
        )
        start_duel_timer(duel, def_id, "defender", bot)

        await safe_edit_message(
            cb,
            generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Ждём защиту соперника…"),
            build_vertical_keyboard_with_styles([("🔄 Обновить", "duel:refresh", "primary")])
        )

    await cb.answer("Зона удара выбрана.")


@router.callback_query(F.data.regexp(r"^duel:def:(head|torso|arms|legs)$"))
async def cb_duel_defend(cb: CallbackQuery, bot: Bot) -> None:
    """Callback: выбор зоны защиты."""
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
    """Callback: обновление статуса боя."""
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
                generate_duel_status_text(
                    duel, cb.from_user.id,
                    extra="🎯 Выбери вариант атаки.",
                    timer_left=time_left
                ),
                get_attack_variant_kb(cb.from_user.id)
            )
        else:
            await safe_edit_message(
                cb,
                generate_duel_status_text(
                    duel, cb.from_user.id,
                    extra="🎯 Теперь выбери зону удара.",
                    timer_left=time_left
                ),
                get_attack_zone_kb()
            )
    else:
        if not duel.atk_zone:
            await safe_edit_message(
                cb,
                generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Соперник ещё выбирает удар…"),
                build_vertical_keyboard_with_styles([("🔄 Обновить", "duel:refresh", "primary")])
            )
        else:
            await safe_edit_message(
                cb,
                generate_duel_status_text(
                    duel, cb.from_user.id,
                    extra=f"{E_SHIELD} Выбери зону защиты.",
                    timer_left=time_left
                ),
                get_defend_zone_kb()
            )

    await cb.answer("Обновлено")


@router.callback_query(F.data == "gear:menu")
async def cb_gear_menu(cb: CallbackQuery) -> None:
    """Callback: меню снаряжения."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    text, kb = generate_gear_screen(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data == "gear:w")
async def cb_gear_weapon(cb: CallbackQuery) -> None:
    """Callback: список оружия."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    text, kb = generate_weapon_list(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^buy_weapon:(\w+)$"))
async def cb_buy_weapon(cb: CallbackQuery) -> None:
    """Callback: покупка/надевание оружия."""
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
        db.execute("UPDATE player_stats SET items_bought=items_bought+1, crystals_spent=crystals_spent+? WHERE user_id=?",
                   (item["price"], cb.from_user.id))
    else:
        await cb.answer(f"Нужно {item['price']}💎", show_alert=True)
        return

    text, kb = generate_weapon_list(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer(toast)


@router.callback_query(F.data == "gear:armor_menu")
async def cb_gear_armor_menu(cb: CallbackQuery) -> None:
    """Callback: меню слотов брони."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    text, kb = generate_armor_slot_menu(cb.from_user.id)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^gear:(head|torso|arms|legs)$"))
async def cb_gear_armor_slot(cb: CallbackQuery) -> None:
    """Callback: список брони для слота."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    slot = cb.data.split(":")[1]
    text, kb = generate_armor_slot_list(cb.from_user.id, slot)
    await safe_edit_message(cb, text, kb)
    await cb.answer()


@router.callback_query(F.data.regexp(r"^buy_armor:(head|torso|arms|legs):(\w+)$"))
async def cb_buy_armor(cb: CallbackQuery) -> None:
    """Callback: покупка/надевание брони."""
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
        db.execute("UPDATE player_stats SET items_bought=items_bought+1, crystals_spent=crystals_spent+? WHERE user_id=?",
                   (item["price"], cb.from_user.id))
    else:
        await cb.answer(f"Нужно {item['price']}💎", show_alert=True)
        return

    text, kb = generate_armor_slot_list(cb.from_user.id, slot)
    await safe_edit_message(cb, text, kb)
    await cb.answer(toast)


@router.callback_query(F.data.regexp(r"^top:(cur|bronze|silver|gold)$"))
async def cb_top_leaderboard(cb: CallbackQuery) -> None:
    """Callback: топ арен."""
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


# ==============================================================================
# 31. FSM И FALLBACK
# ==============================================================================

@router.message(DuelFindState.waiting_for_target, F.text)
async def duel_find_target_handler(m: Message, state: FSMContext, bot: Bot) -> None:
    """Обработчик FSM для поиска соперника по нику."""
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

    # Поиск по ID
    if key.isdigit():
        row = db.fetch_one("SELECT user_id FROM players WHERE user_id=? AND banned=0", (int(key),))
    else:
        row = None

    # Поиск по имени/username
    if not row:
        row = db.fetch_one(
            """SELECT user_id FROM players
               WHERE (LOWER(username)=LOWER(?) OR LOWER(name)=LOWER(?))
               AND banned=0 LIMIT 1""",
            (key, key)
        )

    target = row["user_id"] if row else pick_balanced_opponent(m.from_user.id, p["wins"])

    if not target:
        await m.answer("Не удалось подобрать соперника.")
        return

    await initiate_duel_message(m.from_user.id, target, m, bot)


@router.message()
async def fallback_handler(m: Message) -> None:
    """Fallback-обработчик для нераспознанных сообщений."""
    if not m.from_user:
        return

    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        if m.chat.type == "private":
            await m.answer("Отправь /start, чтобы создать бойца ⚔️")
        return

    if is_user_banned(m.from_user.id):
        await m.answer("🚫 Доступ закрыт.")
        return

    # Обновляем last_active
    db.execute(
        "UPDATE players SET last_active=? WHERE user_id=?",
        (time.time(), m.from_user.id)
    )

    if m.chat.type == "private":
        await m.answer(
            "Пиши <code>help</code> или пользуйся меню внизу 👇",
            reply_markup=MENU_KB
        )
    else:
        await m.answer(
            "В группе команды работают <b>ответом</b> на сообщение игрока "
            "или через <code>@username</code> / <code>ID</code>. "
            "Пиши <code>help</code> для списка."
        )


# ==============================================================================
# 32. ФОНОВЫЕ ЗАДАЧИ И ЗАПУСК
# ==============================================================================

async def scheduled_event_spawner(bot: Bot) -> None:
    """
    Фоновая задача для периодического запуска чатовых событий.
    
    Запускает случайное событие каждые 4 часа (если нет активного).
    """
    global NEXT_SCHEDULED_EVENT

    while True:
        try:
            NEXT_SCHEDULED_EVENT = time.time() + 4 * 3600
            await asyncio.sleep(4 * 3600)

            # Проверяем, нет ли активного события
            if ACTIVE_CHAT_EVENT and ACTIVE_CHAT_EVENT.is_active():
                continue

            # Выбираем случайный тип события
            event_types = list(CHAT_EVENT_TEMPLATES.keys())
            event_type = random.choice(event_types)

            # Запускаем событие (от имени "системы" = 0)
            event = spawn_chat_event(event_type, 0)

            if event:
                logging.info(f"Scheduled event spawned: {event.name}")

        except Exception as e:
            logging.error(f"Error in scheduled_event_spawner: {e}")
            await asyncio.sleep(60)  # Ждём минуту перед повтором


async def main() -> None:
    """
    Основная точка входа в приложение.
    
    Инициализирует базу данных, создаёт бота и запускает polling.
    """
    # Настройка логирования
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format=Config.LOG_FORMAT,
        datefmt=Config.LOG_DATE_FORMAT,
    )

    # Проверка токена
    if not Config.BOT_TOKEN or Config.BOT_TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        logging.critical("❌ ОШИБКА: Задай BOT_TOKEN в переменных окружения или в коде!")
        raise SystemExit("Missing BOT_TOKEN")

    logging.info("=" * 60)
    logging.info("⚔️ АРЕНА ДУЭЛЯНТОВ — Ultimate Edition v16.0")
    logging.info("=" * 60)

    logging.info("Initializing database...")
    # БД инициализируется при создании экземпляра DatabaseManager

    logging.info("Generating masked bots...")
    ensure_masked_bots_exist(Config.BOT_GENERATION_COUNT)

    logging.info("Creating bot instance...")
    bot = Bot(
        Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    logging.info("Setting up dispatcher...")
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # Установка команд меню
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать / вернуться"),
        BotCommand(command="help", description="Правила и команды"),
        BotCommand(command="profile", description="Мой профиль"),
    ])

    # Удаление webhook
    await bot.delete_webhook(drop_pending_updates=True)

    logging.info("✅ Bot successfully started and polling!")
    logging.info("=" * 60)

    # Запускаем фоновую задачу для событий
    event_task = asyncio.create_task(scheduled_event_spawner(bot))

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logging.info("Received shutdown signal...")
    except Exception as e:
        logging.critical(f"Fatal error in polling: {e}\n{traceback.format_exc()}")
    finally:
        event_task.cancel()
        db.close()
        await bot.session.close()
        logging.info("Bot shutdown complete.")


# Точка входа
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
