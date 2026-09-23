#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
⚔️ АРЕНА ДУЭЛЯНТОВ (DUEL ARENA) — ULTIMATE EDITION v9.0
================================================================================
Полнофункциональный Telegram-бот для PvP дуэлей, казино, RP-действий,
глобальных чатовых ивентов (Боссы, Осады) и системы промокодов.

Особенности архитектуры:
- Монолитная структура с четким разделением на логические модули.
- Строгая типизация (Type Hinting) во всех функциях и методах.
- Исчерпывающие Docstring (Google Style) для каждого компонента.
- Расширенная система оружия: 9 видов × 3 варианта атаки с перезарядкой.
- Расширенная броня: 4 слота × 6 уникальных предметов.
- Глобальные ивенты: Чатовый Босс и Осада Крепости (награды по % урона).
- Авто-запуск ивентов при добавлении бота в новую группу.
- Уведомления в ЛС при вызове на дуэль.
- Гибкая система таргетинга: Reply, @username, User ID.
- Премиум эмодзи из github.com/Zulut30/premium-telegram-emoji.
- Валюта: Ареники (🪙).
- Эмодзи-механика в казино (слоты, кости).
- Разноцветные кнопки для улучшенного UX.

Требования:
    - Python 3.10+
    - aiogram >= 3.0.0
    - sqlite3 (встроен)

Автор: AI Assistant
Лицензия: MIT
================================================================================
"""

# ==============================================================================
# ИМПОРТЫ И ЗАВИСИМОСТИ
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
from typing import Optional, Tuple, List, Dict, Any, Callable, Union

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

# ==============================================================================
# 1. КОНФИГУРАЦИЯ И КОНСТАНТЫ
# ==============================================================================

class Config:
    """
    Глобальная конфигурация бота.
    В продакшене настоятельно рекомендуется использовать переменные окружения (.env).
    
    Attributes:
        BOT_TOKEN: Токен бота от @BotFather
        DB_PATH: Путь к файлу базы данных SQLite
        ADMIN_ID: Telegram ID администратора бота
        START_CURRENCY: Начальное количество валюты для новых игроков
        TURN_TIMEOUT: Таймаут на ход в секундах
        RP_COOLDOWN: Кулдаун между RP действиями в секундах
        CURRENCY_NAME: Название внутриигровой валюты
        CURRENCY_EMOJI: Эмодзи валюты
        BOSS_EVENT_INTERVAL: Интервал между авто-спавном боссов в секундах
        SIEGE_EVENT_INTERVAL: Интервал между осадами в секундах
        GROUP_ADD_EVENT_CHANCE: Шанс запуска ивента при добавлении в группу (0.0-1.0)
        LOG_LEVEL: Уровень логирования
        LOG_FORMAT: Формат логирования
    """
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
    DB_PATH: str = os.getenv("DB_PATH", "arena.db")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "5356400377"))
    
    START_CURRENCY: int = 500
    TURN_TIMEOUT: int = 45
    RP_COOLDOWN: int = 5
    
    # Новая валюта по названию бота (Арена -> Ареники)
    CURRENCY_NAME: str = "Ареники"
    CURRENCY_EMOJI: str = "🪙"
    
    # Интервалы глобальных ивентов (в секундах)
    BOSS_EVENT_INTERVAL: int = 3600    # 1 час
    SIEGE_EVENT_INTERVAL: int = 5400   # 1.5 часа
    GROUP_ADD_EVENT_CHANCE: float = 0.4  # 40% шанс ивента при добавлении в группу
    
    # Настройки логирования
    LOG_LEVEL: int = logging.INFO
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"


# ==============================================================================
# 2. ПРЕМИУМ ЭМОДЗИ
# ==============================================================================

# Премиум эмодзи ID (источник: github.com/Zulut30/premium-telegram-emoji)
# Замените эти ID на актуальные, если они устареют.
PREMIUM_EMOJI_IDS: Dict[str, str] = {
    "fire": "5424972470023104089",
    "sword": "5210957702817137308",
    "coin": "5409048419211682843",
    "crystal": "5172484558305625218",
    "trophy": "5415655814079723871",
    "skull": "5460755126761312667",
    "shield": "5210952531676504517",
    "heart": "4996980495100150380",
    "slot": "5935847413859225147",
    "dice": "5418011199914662526",
    "boss": "5890794491119407059",
    "glove": "5992199545151295755",
    "star": "5438496463044752972",
    "magic": "5944914003921739178",
    "gift": "5382357040008021292",
    "promo": "5222444124698853913",
    "warning": "5447644880824181073",
    "check": "5206607081334906820",
    "cross": "5210952531676504517",
    "bell": "5458603043203327669",
    "crown": "5992157823838984339",
    "explosion": "5276032951342088188",
}


def get_premium_emoji(key: str, fallback: str) -> str:
    """
    Генерирует HTML-тег для премиум эмодзи или возвращает fallback.
    
    Args:
        key: Ключ из словаря PREMIUM_EMOJI_IDS.
        fallback: Стандартный эмодзи для отката (если у пользователя нет Premium).
        
    Returns:
        Строка с HTML-тегом <tg-emoji> или строка fallback.
        
    Example:
        >>> get_premium_emoji("fire", "🔥")
        '<tg-emoji emoji-id="5424972470023104089">🔥</tg-emoji>'
    """
    eid = PREMIUM_EMOJI_IDS.get(key)
    if not eid:
        return fallback
    return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'


# Глобальные переменные эмодзи для использования по всему коду
E_FIRE = get_premium_emoji("fire", "🔥")
E_SWORD = get_premium_emoji("sword", "⚔️")
E_COIN = get_premium_emoji("coin", "🪙")
E_CUR = get_premium_emoji("crystal", "💎")
E_TROPHY = get_premium_emoji("trophy", "🏆")
E_SKULL = get_premium_emoji("skull", "💀")
E_SHIELD = get_premium_emoji("shield", "🛡")
E_HEART = get_premium_emoji("heart", "❤️")
E_SLOT = get_premium_emoji("slot", "🎰")
E_DICE = get_premium_emoji("dice", "🎲")
E_BOSS = get_premium_emoji("boss", "👹")
E_GLOVE = get_premium_emoji("glove", "🧤")
E_STAR = get_premium_emoji("star", "⭐")
E_MAGIC = get_premium_emoji("magic", "✨")
E_GIFT = get_premium_emoji("gift", "🎁")
E_PROMO = get_premium_emoji("promo", "🎟")
E_WARN = get_premium_emoji("warning", "⚠️")
E_CHECK = get_premium_emoji("check", "✅")
E_CROSS = get_premium_emoji("cross", "❌")
E_BELL = get_premium_emoji("bell", "🔔")

# ==============================================================================
# 3. ИГРОВЫЕ ДАННЫЕ: ЗОНЫ ТЕЛА
# ==============================================================================

ZONES: List[str] = ["head", "torso", "arms", "legs"]

ZONE_INFO: Dict[str, Dict[str, Any]] = {
    "head": dict(
        name="Голова",
        emoji="🧠",
        mult=1.5,
        desc="Высокий урон, сложно попасть"
    ),
    "torso": dict(
        name="Торс",
        emoji="🫀",
        mult=1.0,
        desc="Стандартная цель"
    ),
    "arms": dict(
        name="Руки",
        emoji="💪",
        mult=0.8,
        desc="Низкий урон, высокая точность"
    ),
    "legs": dict(
        name="Ноги",
        emoji="🦵",
        mult=0.9,
        desc="Средний урон, шанс замедлить"
    ),
}

# ==============================================================================
# 4. ИГРОВЫЕ ДАННЫЕ: ОРУЖИЕ (9 видов × 3 атаки)
# ==============================================================================

WEAPONS: Dict[str, Dict[str, Any]] = {
    "fists": dict(
        emoji="👊",
        name="Кулаки",
        dmg=10,
        price=0,
        chance=25,
        spec="Серия ударов",
        attacks={
            "light": dict(name="Легкий удар", mult=0.8, cooldown=0, desc="Быстрый удар, без КД"),
            "heavy": dict(name="Мощный удар", mult=1.5, cooldown=2, desc="Сильный, но долгий"),
            "special": dict(name="Серия", mult=0.5, hits=3, cooldown=4, desc="3 удара подряд"),
        }
    ),
    "dagger": dict(
        emoji="🗡",
        name="Кинжал",
        dmg=14,
        price=200,
        chance=30,
        spec="Тысяча порезов",
        attacks={
            "light": dict(name="Быстрый порез", mult=0.9, cooldown=0, desc="Мгновенная атака"),
            "heavy": dict(name="Глубокий укол", mult=1.6, cooldown=2, desc="Пробивной удар"),
            "special": dict(name="Веер ножей", mult=0.4, hits=4, cooldown=4, desc="4 броска ножей"),
        }
    ),
    "sword": dict(
        emoji="⚔️",
        name="Меч",
        dmg=20,
        price=500,
        chance=28,
        spec="Казнь",
        attacks={
            "light": dict(name="Рубящий удар", mult=1.0, cooldown=0, desc="Стандартная атака"),
            "heavy": dict(name="Двуручный удар", mult=2.0, cooldown=3, desc="Мощный размах"),
            "special": dict(name="Казнь", mult=2.5, cooldown=5, desc="Смертельное добивание"),
        }
    ),
    "axe": dict(
        emoji="🪓",
        name="Топор",
        dmg=26,
        price=800,
        chance=24,
        spec="Кровопускание",
        attacks={
            "light": dict(name="Боковой удар", mult=0.9, cooldown=0, desc="Быстрый замах"),
            "heavy": dict(name="Вертикальный", mult=1.8, cooldown=3, desc="Удар сверху вниз"),
            "special": dict(name="Рассечение", mult=1.3, cooldown=4, bleed=True, desc="Наносит кровотечение"),
        }
    ),
    "bow": dict(
        emoji="🏹",
        name="Лук",
        dmg=32,
        price=1200,
        chance=22,
        spec="Снайперский выстрел",
        attacks={
            "light": dict(name="Быстрый выстрел", mult=0.7, cooldown=0, desc="1 стрела"),
            "heavy": dict(name="Залп", mult=1.4, cooldown=3, desc="3 стрелы одновременно"),
            "special": dict(name="Снайперский", mult=2.2, cooldown=5, pierce=True, desc="Игнорирует броню"),
        }
    ),
    "staff": dict(
        emoji="🔥",
        name="Посох",
        dmg=38,
        price=1700,
        chance=22,
        spec="Огненный шторм",
        attacks={
            "light": dict(name="Огненный шар", mult=0.8, cooldown=0, desc="Базовая магия"),
            "heavy": dict(name="Стена огня", mult=1.5, cooldown=3, burn=True, desc="Наносит горение"),
            "special": dict(name="Метеорит", mult=2.3, cooldown=6, desc="Огромный магический урон"),
        }
    ),
    "hammer": dict(
        emoji="🔨",
        name="Молот",
        dmg=46,
        price=2500,
        chance=18,
        spec="Землетрясение",
        attacks={
            "light": dict(name="Удар молотом", mult=0.9, cooldown=0, desc="Стандартный удар"),
            "heavy": dict(name="Сокрушение", mult=1.7, cooldown=3, desc="Мощный удар по земле"),
            "special": dict(name="Землетрясение", mult=2.0, cooldown=6, stun=True, desc="Оглушает цель"),
        }
    ),
    "spear": dict(
        emoji="🔱",
        name="Копье",
        dmg=28,
        price=950,
        chance=26,
        spec="Пронзающий выпад",
        attacks={
            "light": dict(name="Укол", mult=1.0, cooldown=0, desc="Стандартный выпад"),
            "heavy": dict(name="Метание", mult=1.6, cooldown=3, desc="Дальний бой"),
            "special": dict(name="Тройной выпад", mult=0.6, hits=3, cooldown=4, desc="3 быстрых укола"),
        }
    ),
    "whip": dict(
        emoji="🪢",
        name="Кнут",
        dmg=18,
        price=600,
        chance=35,
        spec="Хлесткий удар",
        attacks={
            "light": dict(name="Щелчок", mult=0.8, cooldown=0, desc="Быстрый удар"),
            "heavy": dict(name="Опутать", mult=1.3, cooldown=2, stun=True, desc="Шанс оглушить"),
            "special": dict(name="Вихрь кнута", mult=0.5, hits=4, cooldown=4, desc="4 быстрых удара"),
        }
    ),
}

# ==============================================================================
# 5. ИГРОВЫЕ ДАННЫЕ: БРОНЯ (4 слота × 6 предметов)
# ==============================================================================

ARMOR_DATA: Dict[str, List[Dict[str, Any]]] = {
    "head": [
        dict(key="head_none", name="Без шлема", emoji="👕", df=0, hp=0, price=0, chance=0, dmg_bonus=0, desc="Полная уязвимость"),
        dict(key="head_leather", name="Кожаный капюшон", emoji="🧢", df=2, hp=3, price=120, chance=3, dmg_bonus=0, desc="+3% шанс спец-атаки"),
        dict(key="head_iron", name="Железный шлем", emoji="⛑", df=4, hp=8, price=380, chance=0, dmg_bonus=0, desc="Базовая защита головы"),
        dict(key="head_steel", name="Стальной шлем", emoji="🪖", df=7, hp=15, price=850, chance=0, dmg_bonus=10, desc="+10% урон спец-атаки"),
        dict(key="head_dragon", name="Драконий шлем", emoji="🐲", df=11, hp=25, price=1800, chance=8, dmg_bonus=20, desc="+8% шанс, +20% урон"),
        dict(key="head_crown", name="Корона Лорда", emoji="👑", df=14, hp=30, price=3000, chance=12, dmg_bonus=25, desc="Максимальная защита"),
    ],
    "torso": [
        dict(key="torso_none", name="Без брони", emoji="👕", df=0, hp=0, price=0, chance=0, dmg_bonus=0, desc="Полная уязвимость"),
        dict(key="torso_robe", name="Мантия", emoji="🥋", df=3, hp=5, price=150, chance=4, dmg_bonus=0, desc="+4% шанс спец-атаки"),
        dict(key="torso_chain", name="Кольчуга", emoji="🛡", df=6, hp=12, price=480, chance=0, dmg_bonus=0, desc="Надежная защита корпуса"),
        dict(key="torso_plate", name="Латный доспех", emoji="🏋️", df=11, hp=22, price=1000, chance=0, dmg_bonus=15, desc="+15% урон спец-атаки"),
        dict(key="torso_titan", name="Титановый панцирь", emoji="✨", df=17, hp=35, price=2200, chance=10, dmg_bonus=25, desc="+10% шанс, +25% урон"),
        dict(key="torso_aegis", name="Эгида", emoji="🌟", df=22, hp=45, price=3500, chance=15, dmg_bonus=30, desc="Легендарная защита"),
    ],
    "arms": [
        dict(key="arms_none", name="Без наручей", emoji="👕", df=0, hp=0, price=0, chance=0, dmg_bonus=0, desc="Полная уязвимость"),
        dict(key="arms_cloth", name="Тканевые бинты", emoji="🩹", df=2, hp=2, price=100, chance=3, dmg_bonus=0, desc="+3% шанс спец-атаки"),
        dict(key="arms_iron", name="Железные наручи", emoji="🛡", df=4, hp=8, price=350, chance=0, dmg_bonus=0, desc="Базовая защита рук"),
        dict(key="arms_steel", name="Стальные латы", emoji="⚙️", df=7, hp=14, price=800, chance=0, dmg_bonus=10, desc="+10% урон спец-атаки"),
        dict(key="arms_runic", name="Рунические наручи", emoji="🔮", df=11, hp=22, price=1700, chance=8, dmg_bonus=20, desc="+8% шанс, +20% урон"),
        dict(key="arms_berserk", name="Наручи Берсерка", emoji="🩸", df=9, hp=18, price=1500, chance=5, dmg_bonus=35, desc="-2 защиты, +35% урона"),
    ],
    "legs": [
        dict(key="legs_none", name="Без поножей", emoji="👕", df=0, hp=0, price=0, chance=0, dmg_bonus=0, desc="Полная уязвимость"),
        dict(key="legs_cloth", name="Тканевые штаны", emoji="👖", df=2, hp=3, price=110, chance=3, dmg_bonus=0, desc="+3% шанс спец-атаки"),
        dict(key="legs_iron", name="Железные поножи", emoji="🛡", df=5, hp=10, price=400, chance=0, dmg_bonus=0, desc="Базовая защита ног"),
        dict(key="legs_steel", name="Стальные поножи", emoji="⚙️", df=8, hp=16, price=900, chance=0, dmg_bonus=10, desc="+10% урон спец-атаки"),
        dict(key="legs_demon", name="Демонические поножи", emoji="😈", df=12, hp=25, price=1900, chance=8, dmg_bonus=20, desc="+8% шанс, +20% урон"),
        dict(key="legs_wind", name="Поножи Ветра", emoji="💨", df=6, hp=12, price=1100, chance=10, dmg_bonus=5, desc="Высокая мобильность"),
    ],
}

START_ARMOR_KEYS: List[str] = ["head_none", "torso_none", "arms_none", "legs_none"]
BASE_STATS: Dict[str, int] = dict(hp=150)

# ==============================================================================
# 6. ИГРОВЫЕ ДАННЫЕ: АРЕНЫ
# ==============================================================================

ARENAS: Dict[str, Dict[str, Any]] = {
    "bronze": dict(
        name="Бронзовая арена",
        emoji="🥉",
        min_wins=0,
        max_wins=9,
        prize=50,
        color="#cd7f32"
    ),
    "silver": dict(
        name="Серебряная арена",
        emoji="🥈",
        min_wins=10,
        max_wins=29,
        prize=100,
        color="#c0c0c0"
    ),
    "gold": dict(
        name="Золотая арена",
        emoji="🥇",
        min_wins=30,
        max_wins=10**9,
        prize=200,
        color="#ffd700"
    ),
}

ARENA_ORDER: List[str] = ["bronze", "silver", "gold"]

# ==============================================================================
# 7. ИГРОВЫЕ ДАННЫЕ: БОССЫ (огромные HP)
# ==============================================================================

# Данжен-боссы (для личных боев)
DUNGEON_BOSSES: Dict[str, Dict[str, Any]] = {
    "goblin": dict(
        key="goblin",
        name="👺 Гоблин-Вождь",
        desc="Хитрый и злой. Бьёт по слабой броне.",
        hp=500,
        weapon="dagger",
        armor_keys={
            "head": "head_leather",
            "torso": "torso_robe",
            "arms": "arms_none",
            "legs": "legs_none"
        },
        reward_mult=3,
        min_wins=0
    ),
    "dragon": dict(
        key="dragon",
        name="🐉 Древний Дракон",
        desc="Огнедышащий ужас. Оружие — посох.",
        hp=1500,
        weapon="staff",
        armor_keys={
            "head": "head_steel",
            "torso": "torso_plate",
            "arms": "arms_iron",
            "legs": "legs_iron"
        },
        reward_mult=5,
        min_wins=5
    ),
    "lord": dict(
        key="lord",
        name="👹 Древний Лорд",
        desc="Владыка арены. Молот разрушения.",
        hp=3000,
        weapon="hammer",
        armor_keys={
            "head": "head_dragon",
            "torso": "torso_titan",
            "arms": "arms_runic",
            "legs": "legs_demon"
        },
        reward_mult=10,
        min_wins=15
    ),
    "titan": dict(
        key="titan",
        name="🗿 Каменный Титан",
        desc="Неуязвимая глыба. Огромная защита.",
        hp=5000,
        weapon="fists",
        armor_keys={
            "head": "head_crown",
            "torso": "torso_aegis",
            "arms": "arms_berserk",
            "legs": "legs_wind"
        },
        reward_mult=15,
        min_wins=35
    ),
}

# Глобальные чатовые боссы (огромные HP, награды по % урона)
CHAT_BOSSES: List[Dict[str, Any]] = [
    dict(
        key="giant_spider",
        name="🕷️ Гигантский Паук",
        hp=2000,
        max_hp=2000,
        reward_pool=5000,
        weapon="dagger",
        desc="Ядовитое чудовище из глубин подземелий"
    ),
    dict(
        key="demon_lord",
        name="😈 Повелитель Демонов",
        hp=4000,
        max_hp=4000,
        reward_pool=15000,
        weapon="staff",
        desc="Властелин ада явился за душами"
    ),
    dict(
        key="ice_dragon",
        name="🐉 Ледяной Дракон",
        hp=7000,
        max_hp=7000,
        reward_pool=30000,
        weapon="hammer",
        desc="Древнее зло пробудилось от вечного сна"
    ),
    dict(
        key="void_king",
        name="👑 Король Пустоты",
        hp=12000,
        max_hp=12000,
        reward_pool=75000,
        weapon="sword",
        desc="Разрушитель миров, пожиратель реальности"
    ),
]

# Ивент: Осада Крепости
SIEGE_WAVES: Dict[str, Dict[str, Any]] = {
    "wave1": dict(name="🧟 Волна Зомби", enemies=5, hp_each=30, reward=500),
    "wave2": dict(name="👻 Волна Призраков", enemies=7, hp_each=50, reward=1200),
    "wave3": dict(name="🧙 Волна Магов", enemies=6, hp_each=80, reward=2500),
    "wave4": dict(name="👹 Волна Демонов", enemies=8, hp_each=120, reward=5000),
    "wave5": dict(name="🐉 Финальная Волна", enemies=3, hp_each=300, reward=15000),
}

# ==============================================================================
# 8. СИСТЕМА БАЗЫ ДАННЫХ (SQLite Wrapper)
# ==============================================================================

class DatabaseManager:
    """
    Менеджер базы данных для управления состоянием игроков, уведомлений,
    статистики, промокодов и глобальных ивентов.
    Использует sqlite3 с отключенной проверкой потока для совместимости с asyncio.
    
    Attributes:
        db_path: Путь к файлу базы данных
        _connection: Объект соединения sqlite3
    """
    
    def __init__(self, db_path: str):
        """
        Инициализирует менеджер базы данных.
        
        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = db_path
        self._connection = sqlite3.connect(
            db_path,
            check_same_thread=False,
            isolation_level=None
        )
        self._connection.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """
        Инициализирует схему базы данных при первом запуске.
        Создаёт все необходимые таблицы и индексы.
        """
        schema = """
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                name TEXT NOT NULL,
                currency INTEGER NOT NULL DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                weapon TEXT DEFAULT 'fists',
                armor_head TEXT DEFAULT 'head_none',
                armor_torso TEXT DEFAULT 'torso_none',
                armor_arms TEXT DEFAULT 'arms_none',
                armor_legs TEXT DEFAULT 'legs_none',
                weapons_owned TEXT DEFAULT 'fists',
                armors_owned TEXT DEFAULT 'head_none,torso_none,arms_none,legs_none',
                rp_received INTEGER DEFAULT 0,
                rp_given INTEGER DEFAULT 0,
                boss_kills INTEGER DEFAULT 0,
                siege_wins INTEGER DEFAULT 0,
                banned INTEGER DEFAULT 0,
                is_bot INTEGER DEFAULT 0,
                created REAL DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT,
                ts REAL,
                seen INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                reward_currency INTEGER DEFAULT 0,
                reward_wins INTEGER DEFAULT 0,
                max_uses INTEGER DEFAULT 1,
                current_uses INTEGER DEFAULT 0,
                expires_at REAL DEFAULT 0,
                created_by INTEGER,
                created_at REAL DEFAULT 0,
                active INTEGER DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS promo_activations (
                user_id INTEGER,
                code TEXT,
                activated_at REAL,
                PRIMARY KEY (user_id, code)
            );
            
            CREATE TABLE IF NOT EXISTS chat_boss (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                boss_key TEXT,
                current_hp INTEGER,
                max_hp INTEGER,
                started_at REAL,
                active INTEGER DEFAULT 0,
                reward_pool INTEGER,
                chat_id INTEGER
            );
            
            CREATE TABLE IF NOT EXISTS siege_event (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                current_wave INTEGER DEFAULT 0,
                active INTEGER DEFAULT 0,
                started_at REAL,
                chat_id INTEGER
            );
            
            CREATE TABLE IF NOT EXISTS event_damage (
                event_type TEXT,
                event_key TEXT,
                user_id INTEGER,
                damage INTEGER,
                hits INTEGER,
                PRIMARY KEY (event_type, event_key, user_id)
            );
            
            CREATE INDEX IF NOT EXISTS ix_notif ON notifications(user_id, seen);
            CREATE INDEX IF NOT EXISTS ix_players ON players(wins, is_bot, banned);
            CREATE INDEX IF NOT EXISTS ix_promo ON promo_codes(active, expires_at);
            CREATE INDEX IF NOT EXISTS ix_promo_act ON promo_activations(user_id);
        """
        try:
            self._connection.executescript(schema)
            # Инициализация строк глобальных событий, если их нет
            if not self.fetch_one("SELECT 1 FROM chat_boss WHERE id=1"):
                self.execute("INSERT INTO chat_boss (id, active) VALUES (1, 0)")
            if not self.fetch_one("SELECT 1 FROM siege_event WHERE id=1"):
                self.execute("INSERT INTO siege_event (id, active) VALUES (1, 0)")
            logging.info("Database schema initialized successfully.")
        except sqlite3.Error as e:
            logging.critical(f"Failed to initialize database schema: {e}")
            raise

    def fetch_one(self, sql: str, args: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Выполняет SELECT запрос и возвращает одну строку.
        
        Args:
            sql: SQL запрос с плейсхолдерами ?
            args: Кортеж аргументов для подстановки
            
        Returns:
            Объект sqlite3.Row или None при ошибке
        """
        try:
            return self._connection.execute(sql, args).fetchone()
        except sqlite3.Error as e:
            logging.error(f"DB fetch_one error: {e} | SQL: {sql} | Args: {args}")
            return None

    def fetch_all(self, sql: str, args: tuple = ()) -> List[sqlite3.Row]:
        """
        Выполняет SELECT запрос и возвращает все строки.
        
        Args:
            sql: SQL запрос с плейсхолдерами ?
            args: Кортеж аргументов для подстановки
            
        Returns:
            Список объектов sqlite3.Row или пустой список при ошибке
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
            sql: SQL запрос с плейсхолдерами ?
            args: Кортеж аргументов для подстановки
            
        Returns:
            True при успехе, False при ошибке
        """
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
# 9. МОДЕЛИ ДАННЫХ: БОЕЦ
# ==============================================================================

def get_armor_item_by_key(key: str) -> Optional[Dict[str, Any]]:
    """
    Поиск предмета брони по ключу во всем массиве данных.
    
    Args:
        key: Уникальный ключ предмета брони (например, "head_iron")
        
    Returns:
        Словарь с данными предмета или None, если не найден
    """
    for slot, items in ARMOR_DATA.items():
        for it in items:
            if it["key"] == key:
                return {**it, "slot": slot}
    return None


@dataclass
class Fighter:
    """
    Представление бойца в бою.
    Содержит текущие и максимальные характеристики, экипировку, статусы и перезарядки.
    
    Attributes:
        name: Имя бойца
        max_hp: Максимальное здоровье
        hp: Текущее здоровье
        weapon: Ключ оружия из WEAPONS
        armor_slots: Словарь слотов брони {zone: armor_key}
        dots: Список периодических эффектов (кровотечение, горение)
        stun: Флаг оглушения
        attack_cooldowns: Словарь перезарядок атак {type: round_number}
    """
    name: str
    max_hp: int
    hp: int
    weapon: str
    armor_slots: Dict[str, str] = field(default_factory=dict)
    dots: List[Dict[str, Any]] = field(default_factory=list)
    stun: bool = False
    attack_cooldowns: Dict[str, int] = field(default_factory=lambda: {
        "light": 0,
        "heavy": 0,
        "special": 0
    })

    def __post_init__(self) -> None:
        """Валидация и расчет бонусов после инициализации."""
        if self.weapon not in WEAPONS:
            self.weapon = "fists"
        
        self.weapon_dmg = WEAPONS[self.weapon]["dmg"]

        # Валидация слотов брони
        slots = self.armor_slots or {}
        fixed_slots = {}
        for s in ZONES:
            key = slots.get(s) or f"{s}_none"
            if not get_armor_item_by_key(key):
                key = f"{s}_none"
            fixed_slots[s] = key
        self.armor_slots = fixed_slots

        # Расчет защиты и бонусов
        self.armor_def = {}
        total_chance = 0
        total_bonus = 0
        
        for slot in ZONES:
            key = self.armor_slots[slot]
            item = get_armor_item_by_key(key) or get_armor_item_by_key(f"{slot}_none")
            self.armor_def[slot] = item["df"]
            total_chance += item["chance"]
            total_bonus += item["dmg_bonus"]

        self.spec_chance = min(WEAPONS[self.weapon]["chance"] + total_chance, 70)
        self.spec_dmg_bonus = total_bonus / 100.0

    def is_alive(self) -> bool:
        """Проверяет, жив ли боец (HP > 0)."""
        return self.hp > 0

    def get_armor_def(self, zone: str) -> int:
        """
        Возвращает значение защиты для конкретной зоны.
        
        Args:
            zone: Зона тела (head, torso, arms, legs)
            
        Returns:
            Значение защиты
        """
        return self.armor_def.get(zone, 0)

    def get_weapon_dmg_for_zone(self, zone: str) -> int:
        """
        Рассчитывает базовый урон оружия по конкретной зоне с учетом множителя.
        
        Args:
            zone: Зона тела
            
        Returns:
            Базовый урон по зоне
        """
        return max(1, round(self.weapon_dmg * ZONE_INFO[zone]["mult"]))

    def can_use_attack(self, attack_type: str, round_no: int) -> bool:
        """
        Проверяет, готова ли атака к использованию (нет перезарядки).
        
        Args:
            attack_type: Тип атаки (light, heavy, special)
            round_no: Текущий номер раунда
            
        Returns:
            True если атака готова, False если на перезарядке
        """
        return round_no >= self.attack_cooldowns.get(attack_type, 0)

    def use_attack(self, attack_type: str, round_no: int) -> None:
        """
        Устанавливает перезарядку для выбранного типа атаки.
        
        Args:
            attack_type: Тип атаки
            round_no: Текущий номер раунда
        """
        weapon = WEAPONS[self.weapon]
        attack = weapon["attacks"][attack_type]
        self.attack_cooldowns[attack_type] = round_no + attack["cooldown"]


def generate_hp_bar(fighter: Fighter, width: int = 12) -> str:
    """
    Генерирует визуальную полосу здоровья.
    
    Args:
        fighter: Объект бойца
        width: Ширина полосы в символах
        
    Returns:
        Строка с визуальной полосой HP
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
    
    Args:
        fighter: Объект бойца
        
    Returns:
        Отформатированная строка с информацией о бойце
    """
    w = WEAPONS[fighter.weapon]
    ad = fighter.armor_def
    return (
        f"│ <b>{fighter.name}</b>\n"
        f"│ {E_HEART} <b>{fighter.hp}</b>/{fighter.max_hp}  {generate_hp_bar(fighter)}\n"
        f"│ {w['emoji']} {w['name']} · урон {fighter.weapon_dmg}\n"
        f"│ {E_SHIELD} 🧠{ad['head']} 🫀{ad['torso']} 💪{ad['arms']} 🦵{ad['legs']}"
    )


# ==============================================================================
# 10. МОДЕЛИ ДАННЫХ: ДУЭЛЬ
# ==============================================================================

@dataclass
class Duel:
    """
    Состояние активной дуэли.
    Управляет ходами, таймерами, логами и специальными состояниями.
    
    Attributes:
        a_id: ID первого бойца
        b_id: ID второго бойца (-1 для босса)
        a: Объект Fighter первого бойца
        b: Объект Fighter второго бойца
        attacker_is_a: True если первый боец атакует первым
        round_no: Текущий номер раунда
        atk_zone: Выбранная зона атаки
        atk_type: Выбранный тип атаки
        log: Список логов боя
        started: Время начала боя
        is_boss: True если это бой с боссом
        boss_key: Ключ босса если is_boss=True
        reward_mult: Множитель награды
        finished: Флаг завершения боя
        bot_last_block_round: Последний раунд, когда бот блокировал
        bot_block_streak: Серия блоков бота
        timer_task: asyncio задача таймера
        timer_deadline: Дедлайн таймера
        timer_for: ID игрока для которого запущен таймер
        timer_role: Роль игрока (attacker/defender)
    """
    a_id: int
    b_id: int
    a: Fighter
    b: Fighter
    attacker_is_a: bool = True
    round_no: int = 1
    atk_zone: Optional[str] = None
    atk_type: Optional[str] = None
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
        """
        Определяет роль пользователя в текущем раунде.
        
        Args:
            uid: ID пользователя
            
        Returns:
            "attacker", "defender" или "none"
        """
        if uid == self.a_id:
            return "attacker" if self.attacker_is_a else "defender"
        if uid == self.b_id:
            return "defender" if self.attacker_is_a else "attacker"
        return "none"

    def get_attacker(self) -> Fighter:
        """Возвращает объект атакующего бойца."""
        return self.a if self.attacker_is_a else self.b

    def get_defender(self) -> Fighter:
        """Возвращает объект защищающегося бойца."""
        return self.b if self.attacker_is_a else self.a

    def get_attacker_id(self) -> int:
        """Возвращает ID атакующего."""
        return self.a_id if self.attacker_is_a else self.b_id

    def get_defender_id(self) -> int:
        """Возвращает ID защищающегося."""
        return self.b_id if self.attacker_is_a else self.a_id

    def get_fighter(self, uid: int) -> Optional[Fighter]:
        """
        Возвращает объект бойца по ID.
        
        Args:
            uid: ID пользователя
            
        Returns:
            Объект Fighter или None
        """
        return self.a if uid == self.a_id else (self.b if uid == self.b_id else None)

    def get_opponent(self, uid: int) -> Optional[Fighter]:
        """
        Возвращает объект противника по ID.
        
        Args:
            uid: ID пользователя
            
        Returns:
            Объект Fighter противника или None
        """
        return self.b if uid == self.a_id else (self.a if uid == self.b_id else None)


# Глобальное хранилище активных дуэлей
ACTIVE_DUELS: Dict[int, Duel] = {}

# ==============================================================================
# 11. БОЕВАЯ ЛОГИКА: РАСЧЕТ УРОНА
# ==============================================================================

def calculate_damage(
    attacker: Fighter,
    defender: Fighter,
    atk_zone: str,
    def_zone: Optional[str],
    attack_type: str = "light"
) -> Tuple[int, str]:
    """
    Рассчитывает итоговый урон с учетом брони, зон и множителей атаки.
    
    Args:
        attacker: Объект атакующего бойца
        defender: Объект защищающегося бойца
        atk_zone: Зона атаки
        def_zone: Зона защиты (None если не защищается)
        attack_type: Тип атаки (light, heavy, special)
        
    Returns:
        Кортеж (нанесенный урон, строка примечания, например "Блок!")
    """
    if def_zone == atk_zone:
        return 0, f"{E_SHIELD} <b>Блок!</b>"
    
    weapon = WEAPONS[attacker.weapon]
    attack = weapon["attacks"][attack_type]
    
    base_dmg = attacker.get_weapon_dmg_for_zone(atk_zone)
    armor = defender.get_armor_def(atk_zone)
    
    # Игнорирование брони для pierce атак
    if attack.get("pierce"):
        armor = 0
        
    raw_dmg = base_dmg * attack["mult"] - armor
    final_dmg = max(1, round(raw_dmg))
    
    return final_dmg, ""


def process_dots(fighter: Fighter, log: List[str]) -> None:
    """
    Обрабатывает периодический урон (яд, горение, кровотечение).
    
    Args:
        fighter: Объект бойца
        log: Список логов для добавления
    """
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
    """
    Накладывает или обновляет эффект периодического урона.
    
    Args:
        target: Целевой боец
        name: Название эффекта
        dmg: Урон за раунд
        rounds: Количество раундов
    """
    target.dots = [d for d in target.dots if d["name"] != name]
    target.dots.append({"name": name, "dmg": dmg, "left": rounds})


def execute_attack_phase(
    attacker: Fighter,
    defender: Fighter,
    atk_zone: str,
    def_zone: Optional[str],
    attack_type: str,
    log: List[str],
    round_no: int
) -> bool:
    """
    Выполняет полный цикл атаки: проверка оглушения -> перезарядка -> расчет урона -> эффекты.
    
    Args:
        attacker: Объект атакующего бойца
        defender: Объект защищающегося бойца
        atk_zone: Зона атаки
        def_zone: Зона защиты
        attack_type: Тип атаки
        log: Список логов
        round_no: Номер раунда
        
    Returns:
        True, если атака была успешно выполнена, False если пропущена из-за КД
    """
    weapon = WEAPONS[attacker.weapon]
    attack = weapon["attacks"][attack_type]
    attack_name = attack["name"]

    # Проверка оглушения
    if attacker.stun:
        attacker.stun = False
        log.append(f"💫 {attacker.name} оглушён и пропускает ход!")
        return False

    # Проверка перезарядки
    if not attacker.can_use_attack(attack_type, round_no):
        cd_left = attacker.attack_cooldowns[attack_type] - round_no
        log.append(f"⏳ <b>{attack_name}</b> перезаряжается (ещё {cd_left} раунда)")
        return False

    # Устанавливаем перезарядку
    attacker.use_attack(attack_type, round_no)

    # Спец-атака с несколькими ударами
    if "hits" in attack:
        total_dmg = 0
        hits = []
        for _ in range(attack["hits"]):
            d, note = calculate_damage(attacker, defender, atk_zone, def_zone, attack_type)
            if note and "Блок" in note:
                log.append(f"{E_SHIELD} {defender.name} заблокировал {attack_name}")
                return True
            hits.append(d)
            total_dmg += d
        defender.hp = max(0, defender.hp - total_dmg)
        log.append(f"{weapon['emoji']} <b>{attack_name}</b>: {'+'.join(map(str, hits))}=<b>−{total_dmg}</b>")
    else:
        dmg, note = calculate_damage(attacker, defender, atk_zone, def_zone, attack_type)
        if note:
            log.append(f"{E_SHIELD} {defender.name} заблокировал {attack_name}")
            return True
        defender.hp = max(0, defender.hp - dmg)
        log.append(f"{weapon['emoji']} <b>{attack_name}</b>: {attacker.name} → {defender.name} <b>−{dmg}</b>")

    # Дополнительные эффекты атаки
    if attack.get("bleed"):
        bleed = max(1, round(defender.max_hp * 0.04))
        apply_dot_effect(defender, "🩸 Кровотечение", bleed, 3)
        log.append(f"🩸 +кровотечение {bleed} ×3")
        
    if attack.get("burn"):
        burn = max(1, round(dmg * 0.4))
        apply_dot_effect(defender, f"{E_FIRE} Горение", burn, 3)
        log.append(f"{E_FIRE} +горение {burn} ×3")
        
    if attack.get("stun"):
        defender.stun = True
        log.append(f"💫 {defender.name} оглушён!")

    # Шанс особой атаки оружия (только для special)
    if random.random() * 100 < attacker.spec_chance and attack_type == "special":
        bonus_dmg = round(dmg * attacker.spec_dmg_bonus) if 'dmg' in locals() else 0
        if bonus_dmg > 0:
            defender.hp = max(0, defender.hp - bonus_dmg)
            log.append(f"{E_MAGIC} <b>{weapon['spec']}</b>! доп. <b>−{bonus_dmg}</b>")

    return True


# ==============================================================================
# 12. УПРАВЛЕНИЕ ДУЭЛЬЮ И ТАЙМЕРАМИ
# ==============================================================================

def stop_duel_timer(duel: Duel) -> None:
    """
    Безопасно останавливает и очищает задачу таймера дуэли.
    
    Args:
        duel: Объект дуэли
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
    
    Args:
        duel: Объект дуэли
    """
    duel.finished = True
    stop_duel_timer(duel)
    ACTIVE_DUELS.pop(duel.a_id, None)
    if duel.b_id > 0:
        ACTIVE_DUELS.pop(duel.b_id, None)


def start_duel_timer(duel: Duel, uid: int, role: str, bot: Bot) -> None:
    """
    Инициализирует таймер хода для конкретного игрока.
    
    Args:
        duel: Объект дуэли
        uid: ID игрока
        role: Роль (attacker/defender)
        bot: Объект бота
    """
    if uid < 0:  # Боты не имеют таймеров
        return
    stop_duel_timer(duel)
    duel.timer_for = uid
    duel.timer_role = role
    duel.timer_deadline = time.time() + Config.TURN_TIMEOUT
    duel.timer_task = asyncio.create_task(_timer_runner_task(duel, uid, role, bot))


async def _timer_runner_task(duel: Duel, uid: int, role: str, bot: Bot) -> None:
    """
    Асинхронная задача, отслеживающая истечение времени хода.
    
    Args:
        duel: Объект дуэли
        uid: ID игрока
        role: Роль игрока
        bot: Объект бота
    """
    try:
        while True:
            if duel.finished:
                return
            time_left = int(round(duel.timer_deadline - time.time()))
            if time_left <= 0:
                break
            await asyncio.sleep(1)
            
        # Проверки перед применением наказания за время
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
    """
    Обрабатывает автоматическое поражение из-за таймаута.
    
    Args:
        duel: Объект дуэли
        loser_uid: ID проигравшего
        bot: Объект бота
    """
    loser = duel.get_fighter(loser_uid)
    duel.log.append(f"⏱ <b>{loser.name if loser else 'Неизвестный'} не успел за {Config.TURN_TIMEOUT} сек — авто-поражение!</b>")
    
    # Определяем победителя (противоположная сторона)
    winner_is_a = not (loser_uid == duel.a_id)
    await finalize_duel(duel, winner_is_a=winner_is_a, bot=bot, reason="timeout")


# ==============================================================================
# 13. ИИ БОТА И ГЕНЕРАЦИЯ СОПЕРНИКОВ
# ==============================================================================

def get_player_armor_slots(player_row: sqlite3.Row) -> Dict[str, str]:
    """
    Извлекает и валидирует слоты брони из записи БД.
    
    Args:
        player_row: Строка из БД
        
    Returns:
        Словарь слотов брони {zone: armor_key}
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
    Создает объект Fighter на основе данных из БД.
    
    Args:
        player_row: Строка из БД
        
    Returns:
        Объект Fighter
    """
    slots = get_player_armor_slots(player_row)
    total_hp = BASE_STATS["hp"]
    
    for key in slots.values():
        item = get_armor_item_by_key(key)
        if item:
            total_hp += item.get("hp", 0)
            
    return Fighter(
        name=html.escape(player_row["name"]),
        max_hp=total_hp,
        hp=total_hp,
        weapon=player_row["weapon"] if player_row["weapon"] in WEAPONS else "fists",
        armor_slots=slots,
    )


def create_boss_fighter(boss_data: Dict[str, Any]) -> Fighter:
    """
    Создает объект Fighter для босса.
    
    Args:
        boss_data: Словарь с данными босса
        
    Returns:
        Объект Fighter
    """
    return Fighter(
        name=boss_data["name"],
        max_hp=boss_data["hp"],
        hp=boss_data["hp"],
        weapon=boss_data["weapon"],
        armor_slots=boss_data["armor_keys"],
    )


def determine_arena(wins: int) -> str:
    """
    Определяет текущую арену игрока на основе количества побед.
    
    Args:
        wins: Количество побед
        
    Returns:
        Ключ арены (bronze, silver, gold)
    """
    for k in ARENA_ORDER:
        a = ARENAS[k]
        if a["min_wins"] <= wins <= a["max_wins"]:
            return k
    return "gold"


def generate_random_bot_name(existing_names: set) -> str:
    """
    Генерирует уникальное имя для скрытого бота.
    
    Args:
        existing_names: Множество уже существующих имён
        
    Returns:
        Уникальное имя бота
    """
    human_names = [
        "Максим", "Артём", "Данил", "Кирилл", "Егор", "Иван", "Никита", "Рома",
        "Саня", "Дима", "Влад", "Серёга", "Паша", "Толя", "Женя", "Костя",
        "Лёха", "Миша", "Гриша", "Стас", "Олег", "Ден", "Марк", "Тимур",
        "Алина", "Катя", "Настя", "Даша", "Лера", "Соня", "Вика", "Полина",
        "Крис", "Милана", "Аня", "Юля", "Оля", "Маша", "Ксюша", "Ника"
    ]
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
    
    Args:
        target_count: Целевое количество ботов
    """
    existing_names = {r["name"].lower() for r in db.fetch_all("SELECT name FROM players")}
    bots = db.fetch_all("SELECT user_id, wins FROM players WHERE is_bot=1")
    need = max(0, target_count - len(bots))
    
    for _ in range(need):
        name = generate_random_bot_name(existing_names)
        uid = -random.randint(10_000_000, 99_999_999)
        
        # Балансировка: распределение ботов по аренам
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
            INSERT INTO players (user_id, username, name, currency, wins, losses, weapon,
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
    Приоритет: реальные игроки > боты той же арены > генерация нового бота.
    
    Args:
        player_uid: ID игрока
        player_wins: Количество побед игрока
        
    Returns:
        ID подобранного соперника или None
    """
    arena = determine_arena(player_wins)
    limits = ARENAS[arena]
    
    # 1. Ищем реальных игроков
    humans = [r["user_id"] for r in db.fetch_all("""
        SELECT user_id FROM players
        WHERE user_id != ? AND banned=0 AND is_bot=0 AND wins BETWEEN ? AND ?
        ORDER BY RANDOM() LIMIT 6
    """, (player_uid, limits["min_wins"], limits["max_wins"]))]
    
    # 2. Ищем ботов той же арены
    bots = [r["user_id"] for r in db.fetch_all("""
        SELECT user_id FROM players
        WHERE is_bot=1 AND banned=0 AND wins BETWEEN ? AND ?
        ORDER BY RANDOM() LIMIT 6
    """, (limits["min_wins"], limits["max_wins"]))]
    
    if humans and bots:
        return random.choice(bots if random.random() < 0.6 else humans) # 60% шанс на бота для скорости
    if humans:
        return random.choice(humans)
    if bots:
        return random.choice(bots)
    
    # 3. Fallback: генерируем нового бота под текущую арену
    ensure_masked_bots_exist(10)
    rows = db.fetch_all("""
        SELECT user_id FROM players
        WHERE is_bot=1 AND wins BETWEEN ? AND ?
        ORDER BY RANDOM() LIMIT 1
    """, (limits["min_wins"], limits["max_wins"]))
    
    return rows[0]["user_id"] if rows else None


# ==============================================================================
# 14. ИСКУССТВЕННЫЙ ИНТЕЛЛЕКТ БОТА В БОЮ
# ==============================================================================

def bot_decide_attack(attacker: Fighter, defender: Fighter, round_no: int) -> Tuple[str, str]:
    """
    Логика выбора типа атаки и зоны для бота.
    Учитывает перезарядку, добивание и элемент случайности.
    
    Args:
        attacker: Объект атакующего бота
        defender: Объект защищающегося игрока
        round_no: Текущий номер раунда
        
    Returns:
        Кортеж (тип атаки, зона атаки)
    """
    # Выбираем тип атаки из доступных (без КД)
    available_attacks = []
    for atk_type in ["light", "heavy", "special"]:
        if attacker.can_use_attack(atk_type, round_no):
            available_attacks.append(atk_type)
            
    if not available_attacks:
        available_attacks = ["light"] # Fallback

    # Стратегия выбора атаки
    hp_ratio = defender.hp / defender.max_hp
    if hp_ratio < 0.3 and "special" in available_attacks:
        atk_type = "special"  # Добивание
    elif hp_ratio < 0.6 and "heavy" in available_attacks:
        atk_type = random.choice(["heavy", "special"]) if "special" in available_attacks else "heavy"
    else:
        atk_type = random.choice(available_attacks)

    # Выбор зоны
    if random.random() < 0.10:
        zone = random.choice(ZONES) # 10% шанс на ошибку
    elif defender.hp <= defender.max_hp * 0.30:
        zone = max(ZONES, key=lambda z: attacker.get_weapon_dmg_for_zone(z)) # Добивание в самую уязвимую
    else:
        # Иначе ищем зону с наилучшим соотношением урон минус защита
        zone = max(ZONES, key=lambda z: attacker.get_weapon_dmg_for_zone(z) - defender.get_armor_def(z))

    return atk_type, zone


def bot_decide_to_defend(duel: Duel, bot_is_a: bool) -> bool:
    """
    Определяет, будет ли бот пытаться блокировать атаку.
    
    Args:
        duel: Объект дуэли
        bot_is_a: True если бот - первый игрок
        
    Returns:
        True если бот будет защищаться
    """
    if duel.bot_block_streak >= 2:
        return False
    if duel.round_no - duel.bot_last_block_round < 3:
        return False
        
    bot_fighter = duel.a if bot_is_a else duel.b
    hp_ratio = bot_fighter.hp / bot_fighter.max_hp
    
    # Чем меньше здоровья, тем выше шанс встать в блок
    if hp_ratio < 0.30:
        base_chance = 0.65
    elif hp_ratio < 0.60:
        base_chance = 0.40
    else:
        base_chance = 0.25
        
    return random.random() < base_chance


def bot_pick_defend_zone(attacker: Fighter, defender: Fighter) -> str:
    """
    Выбирает зону для защиты, основываясь на наиболее опасной зоне атаки противника.
    
    Args:
        attacker: Объект атакующего
        defender: Объект защищающегося бота
        
    Returns:
        Название зоны для защиты
    """
    def danger_level(z: str) -> int:
        return attacker.get_weapon_dmg_for_zone(z) - defender.get_armor_def(z)
        
    sorted_zones = sorted(ZONES, key=danger_level, reverse=True)
    
    # 25% шанс ошибиться и защитить вторую по опасности зону
    if random.random() < 0.25 and len(sorted_zones) > 1:
        return sorted_zones[1]
    return sorted_zones[0]


# ==============================================================================
# 15. КАЗИНО И ЭКОНОМИКА (С ЭМОДЗИ МЕХАНИКОЙ)
# ==============================================================================

def play_casino_slots(uid: int, bet: int) -> Tuple[Optional[str], Optional[str]]:
    """
    Логика игры в слоты с эмодзи механикой.
    
    Args:
        uid: ID игрока
        bet: Размер ставки
        
    Returns:
        Кортеж (результат, ошибка)
    """
    p = db.fetch_one("SELECT currency FROM players WHERE user_id=?", (uid,))
    if not p or p["currency"] < bet:
        return None, f"Недостаточно {Config.CURRENCY_NAME} на балансе."
        
    # Эмодзи слотов определяют результат
    symbols = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣"]
    weights = [25, 22, 20, 15, 12, 6]
    spin = random.choices(symbols, weights=weights, k=3)
    
    db.execute("UPDATE players SET currency=currency-? WHERE user_id=?", (bet, uid))
    
    if spin[0] == spin[1] == spin[2]:
        mult = {"7️⃣": 10, "💎": 8}.get(spin[0], 5)
        win = bet * mult
        db.execute("UPDATE players SET currency=currency+? WHERE user_id=?", (win, uid))
        return f"🎰 {spin[0]} | {spin[1]} | {spin[2]}\n\n{E_TROPHY} <b>ДЖЕКПОТ ×{mult}!</b>\nВы выиграли: +{win}{Config.CURRENCY_EMOJI}", None
        
    if spin[0] == spin[1] or spin[1] == spin[2] or spin[0] == spin[2]:
        win = int(bet * 2)
        db.execute("UPDATE players SET currency=currency+? WHERE user_id=?", (win, uid))
        return f"🎰 {spin[0]} | {spin[1]} | {spin[2]}\n\n✅ <b>Пара!</b>\nВы выиграли: +{win}{Config.CURRENCY_EMOJI}", None
        
    return f"🎰 {spin[0]} | {spin[1]} | {spin[2]}\n\n{E_SKULL} <b>Мимо.</b>\nВы проиграли: −{bet}{Config.CURRENCY_EMOJI}", None


def play_casino_dice(uid: int, bet: int) -> Tuple[Optional[str], Optional[str]]:
    """
    Логика игры в кости с эмодзи механикой.
    
    Args:
        uid: ID игрока
        bet: Размер ставки
        
    Returns:
        Кортеж (результат, ошибка)
    """
    p = db.fetch_one("SELECT currency FROM players WHERE user_id=?", (uid,))
    if not p or p["currency"] < bet:
        return None, "Недостаточно фишек на балансе."
        
    # Эмодзи костей
    dice_emojis = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    player_roll = random.randint(1, 6)
    dealer_roll = random.randint(1, 6)
    
    db.execute("UPDATE players SET currency=currency-? WHERE user_id=?", (bet, uid))
    
    p_emoji, d_emoji = dice_emojis[player_roll-1], dice_emojis[dealer_roll-1]
    if player_roll > dealer_roll:
        win = bet * 2
        db.execute("UPDATE players SET currency=currency+? WHERE user_id=?", (win, uid))
        return f"🎲 Ты: {p_emoji} ({player_roll}) · Дилер: {d_emoji} ({dealer_roll})\n\n{E_TROPHY} <b>Победа!</b> +{win}{Config.CURRENCY_EMOJI}", None
    elif player_roll == dealer_roll:
        db.execute("UPDATE players SET currency=currency+? WHERE user_id=?", (bet, uid))
        return f"🎲 Ты: {p_emoji} ({player_roll}) · Дилер: {d_emoji} ({dealer_roll})\n\n🤝 <b>Ничья.</b> Ставка возвращена.", None
    else:
        return f"🎲 Ты: {p_emoji} ({player_roll}) · Дилер: {d_emoji} ({dealer_roll})\n\n{E_SKULL} <b>Поражение.</b> −{bet}{Config.CURRENCY_EMOJI}", None


def play_casino_coin(uid: int, bet: int, choice: str = "heads") -> Tuple[Optional[str], Optional[str]]:
    """
    Логика игры в монетку (Орел или Решка).
    
    Args:
        uid: ID игрока
        bet: Размер ставки
        choice: Выбор игрока (heads/tails)
        
    Returns:
        Кортеж (результат, ошибка)
    """
    p = db.fetch_one("SELECT currency FROM players WHERE user_id=?", (uid,))
    if not p or p["currency"] < bet:
        return None, "Недостаточно фишек на балансе."
        
    result = random.choice(["heads", "tails"])
    db.execute("UPDATE players SET currency=currency-? WHERE user_id=?", (bet, uid))
    
    result_text = "Орёл 🪙" if result == "heads" else "Решка 🦅"
    
    if result == choice:
        win = bet * 2
        db.execute("UPDATE players SET currency=currency+? WHERE user_id=?", (win, uid))
        return f"{E_COIN} Выпало: <b>{result_text}</b>\n\n{E_TROPHY} <b>Победа!</b> +{win}{Config.CURRENCY_EMOJI}", None
    else:
        return f"{E_COIN} Выпало: <b>{result_text}</b>\n\n{E_SKULL} <b>Поражение.</b> −{bet}{Config.CURRENCY_EMOJI}", None


def play_casino_roulette(uid: int, bet: int, color: str = "red") -> Tuple[Optional[str], Optional[str]]:
    """
    Логика игры в упрощенную рулетку.
    
    Args:
        uid: ID игрока
        bet: Размер ставки
        color: Выбор цвета (red/black/green)
        
    Returns:
        Кортеж (результат, ошибка)
    """
    p = db.fetch_one("SELECT currency FROM players WHERE user_id=?", (uid,))
    if not p or p["currency"] < bet:
        return None, "Недостаточно фишек на балансе."
        
    reds = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    num = random.randint(0, 36)
    
    if num == 0:
        res_color = "green"
    elif num in reds:
        res_color = "red"
    else:
        res_color = "black"
        
    db.execute("UPDATE players SET currency=currency-? WHERE user_id=?", (bet, uid))
    
    if color == res_color:
        mult = 14 if color == "green" else 2
        win = bet * mult
        db.execute("UPDATE players SET currency=currency+? WHERE user_id=?", (win, uid))
        return f"🎡 Выпало: <b>{num} ({res_color})</b>\n\n{E_TROPHY} <b>Победа ×{mult}!</b> +{win}{Config.CURRENCY_EMOJI}", None
    else:
        return f"🎡 Выпало: <b>{num} ({res_color})</b>\n\n{E_SKULL} <b>Поражение.</b> −{bet}{Config.CURRENCY_EMOJI}", None


def play_casino_highlow(uid: int, bet: int, choice: str = "high") -> Tuple[Optional[str], Optional[str]]:
    """
    Логика игры Больше/Меньше (число от 1 до 100).
    
    Args:
        uid: ID игрока
        bet: Размер ставки
        choice: Выбор игрока (high/low)
        
    Returns:
        Кортеж (результат, ошибка)
    """
    p = db.fetch_one("SELECT currency FROM players WHERE user_id=?", (uid,))
    if not p or p["currency"] < bet:
        return None, "Недостаточно фишек на балансе."
        
    result_num = random.randint(1, 100)
    db.execute("UPDATE players SET currency=currency-? WHERE user_id=?", (bet, uid))
    
    is_high = result_num > 50
    is_low = result_num < 50
    
    win = False
    if choice == "high" and is_high: win = True
    elif choice == "low" and is_low: win = True
    elif result_num == 50: # Ровно 50 - возврат
        db.execute("UPDATE players SET currency=currency+? WHERE user_id=?", (bet, uid))
        return f"📊 Выпало число: <b>{result_num}</b>\n\n🤝 <b>Ровно 50!</b> Ставка возвращена.", None
        
    if win:
        payout = int(bet * 1.9) # Небольшая маржа казино
        db.execute("UPDATE players SET currency=currency+? WHERE user_id=?", (payout, uid))
        return f"📊 Выпало число: <b>{result_num}</b>\n\n{E_TROPHY} <b>Победа!</b> +{payout}{Config.CURRENCY_EMOJI}", None
    else:
        return f"📊 Выпало число: <b>{result_num}</b>\n\n{E_SKULL} <b>Поражение.</b> −{bet}{Config.CURRENCY_EMOJI}", None


# ==============================================================================
# 16. СИСТЕМА ПРОМОКОДОВ
# ==============================================================================

def create_promo_code(
    code: str,
    reward_currency: int,
    reward_wins: int,
    max_uses: int,
    hours_valid: int,
    created_by: int
) -> Tuple[bool, str]:
    """
    Создает новый промокод.
    
    Args:
        code: Уникальный код (будет приведен к верхнему регистру)
        reward_currency: Награда в валюте
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
    
    if reward_currency < 0 or reward_wins < 0:
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
        INSERT INTO promo_codes (code, reward_currency, reward_wins, max_uses, current_uses, expires_at, created_by, created_at, active)
        VALUES (?, ?, ?, ?, 0, ?, ?, ?, 1)
    """, (code, reward_currency, reward_wins, max_uses, expires_at, created_by, now))
    
    return True, (
        f"{E_PROMO} Промокод <code>{code}</code> создан!\n\n"
        f"💎 Валюта: {reward_currency}\n"
        f"🏆 Победы: {reward_wins}\n"
        f"👥 Макс. активаций: {max_uses}\n"
        f"⏳ Действует: {hours_valid} ч."
    )


def deactivate_promo_code(code: str) -> Tuple[bool, str]:
    """
    Деактивирует промокод.
    
    Args:
        code: Код промокода
        
    Returns:
        Кортеж (успех, сообщение)
    """
    code = code.strip().upper()
    existing = db.fetch_one("SELECT * FROM promo_codes WHERE code=?", (code,))
    if not existing:
        return False, "Промокод не найден."
    
    db.execute("UPDATE promo_codes SET active=0 WHERE code=?", (code,))
    return True, f"{E_PROMO} Промокод <code>{code}</code> деактивирован."


def activate_promo_code(user_id: int, code: str) -> Tuple[bool, str]:
    """
    Активирует промокод для игрока.
    
    Args:
        user_id: ID игрока
        code: Код промокода
        
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
        return False, f"❌ Промокод <code>{code}</code> деактивирован администратором."
    
    if promo["expires_at"] < time.time():
        return False, f"❌ Промокод <code>{code}</code> истёк."
    
    if promo["current_uses"] >= promo["max_uses"]:
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
        
        if promo["reward_currency"] > 0:
            db.execute(
                "UPDATE players SET currency=currency+? WHERE user_id=?",
                (promo["reward_currency"], user_id)
            )
        
        if promo["reward_wins"] > 0:
            db.execute(
                "UPDATE players SET wins=wins+? WHERE user_id=?",
                (promo["reward_wins"], user_id)
            )
        
        rewards = []
        if promo["reward_currency"] > 0:
            rewards.append(f"💎 +{promo['reward_currency']} {Config.CURRENCY_NAME}")
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


# ==============================================================================
# 17. ГЛОБАЛЬНЫЕ ИВЕНТЫ: ЧАТОВЫЙ БОСС И ОСАДА
# ==============================================================================

def spawn_global_event(chat_id: int, event_type: str, force_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Создает новый глобальный ивент (босс или осаду).
    
    Args:
        chat_id: ID чата где запущен ивент
        event_type: Тип ивента (boss/siege)
        force_key: Принудительный ключ босса (опционально)
        
    Returns:
        Словарь с данными ивента или None
    """
    if event_type == "boss":
        boss_key = force_key or random.choice([b["key"] for b in CHAT_BOSSES])
        boss_data = next(b for b in CHAT_BOSSES if b["key"] == boss_key)
        
        db.execute("DELETE FROM event_damage WHERE event_type='boss' AND event_key=?", (boss_key,))
        db.execute("""
            UPDATE chat_boss SET boss_key=?, current_hp=?, max_hp=?, started_at=?, active=1,
            reward_pool=?, chat_id=? WHERE id=1
        """, (boss_key, boss_data["hp"], boss_data["max_hp"], time.time(), boss_data["reward_pool"], chat_id))
        return boss_data
    elif event_type == "siege":
        db.execute("DELETE FROM event_damage WHERE event_type LIKE 'siege_%'")
        db.execute(
            "UPDATE siege_event SET current_wave=1, active=1, started_at=?, chat_id=? WHERE id=1",
            (time.time(), chat_id)
        )
        return SIEGE_WAVES["wave1"]
    return None


def get_chat_boss_state() -> Optional[sqlite3.Row]:
    """Получает текущее состояние чатового босса."""
    return db.fetch_one("SELECT * FROM chat_boss WHERE id=1")


def get_siege_state() -> Optional[sqlite3.Row]:
    """Получает текущее состояние осады."""
    return db.fetch_one("SELECT * FROM siege_event WHERE id=1")


def attack_global_event(uid: int, damage: int, event_type: str, event_key: str) -> str:
    """
    Игрок атакует глобальный ивент.
    
    Args:
        uid: ID игрока
        damage: Нанесённый урон
        event_type: Тип ивента
        event_key: Ключ ивента
        
    Returns:
        "killed" если убит, "hit" если просто удар
    """
    db.execute("""
        INSERT INTO event_damage (event_type, event_key, user_id, damage, hits) VALUES (?, ?, ?, ?, 1)
        ON CONFLICT(event_type, event_key, user_id) DO UPDATE SET
        damage=damage+?, hits=hits+1
    """, (event_type, event_key, uid, damage, damage))
    
    if event_type == "boss":
        db.execute("UPDATE chat_boss SET current_hp=MAX(0, current_hp-?) WHERE id=1", (damage,))
        state = get_chat_boss_state()
        if state and state["current_hp"] <= 0:
            return "killed"
    return "hit"


def distribute_global_event_rewards(event_type: str, event_key: str) -> List[Tuple[int, int, int, int]]:
    """
    Распределяет награды после завершения ивента пропорционально урону.
    
    Args:
        event_type: Тип ивента
        event_key: Ключ ивента
        
    Returns:
        Список кортежей (user_id, reward, damage, hits)
    """
    state = get_chat_boss_state() if event_type == "boss" else get_siege_state()
    if not state:
        return []
        
    pool = state["reward_pool"] if event_type == "boss" else 5000
    
    damages = db.fetch_all(
        "SELECT user_id, damage, hits FROM event_damage WHERE event_type=? AND event_key=? ORDER BY damage DESC",
        (event_type, event_key)
    )
    
    if not damages:
        return []
        
    total_dmg = sum(d["damage"] for d in damages)
    rewards = []
    
    for d in damages:
        # Пропорциональное распределение по урону
        share = int((d["damage"] / total_dmg) * pool) if total_dmg > 0 else 0
        # Минимальная награда за участие (если урон > 0)
        if share == 0 and d["damage"] > 0:
            share = 10
        
        if share > 0:
            db.execute(
                "UPDATE players SET currency=currency+?, boss_kills=boss_kills+1 WHERE user_id=?",
                (share, d["user_id"])
            )
            rewards.append((d["user_id"], share, d["damage"], d["hits"]))
            
    if event_type == "boss":
        db.execute("UPDATE chat_boss SET active=0 WHERE id=1")
    return rewards


# ==============================================================================
# 18. RP (ROLEPLAY) СИСТЕМА
# ==============================================================================

RP_ACTIONS: Dict[str, Tuple[str, str, str]] = {
    "ударить": ("👊", "ударил(а)", "получил(а) удар"),
    "обнять": ("🤗", "обнял(а)", "был(а) обнят(а)"),
    "поцеловать": ("😘", "поцеловал(а)", "был(а) поцелован(а)"),
    "пнуть": ("🦵", "пнул(а)", "получил(а) пинок"),
    "погладить": ("🤚", "погладил(а)", "был(а) поглажен(а)"),
    "укусить": ("😬", "укусил(а)", "был(а) укушен(а)"),
    "пожать": ("🤝", "пожал(а) руку", "рука пожата"),
    "толкнуть": ("💥", "толкнул(а)", "был(а) толкнут(а)"),
    "кинуть": ("🥊", "кинул(а) в", "получил(а) бросок"),
    "лечить": ("💊", "подлечил(а)", "был(а) подлечен(а)"),
    "игнорировать": ("💅", "проигнорировал(а)", "был(а) проигнорирован(а)"),
    "смеяться": ("😂", "посмеялся(ась) над", "был(а) высмеян(а)"),
    "плакать": ("😭", "заплакал(а) перед", "увидел(а) слёзы"),
    "танцевать": ("💃", "станцевал(а) для", "увидел(а) танец"),
    "шлепнуть": ("👋", "шлепнул(а)", "получил(а) шлепок"),
    "обозвать": ("🤬", "обозвал(а)", "был(а) обозван(а)"),
    "восхититься": ("😍", "восхитился(ась)", "вызвал(а) восхищение"),
    "испугаться": ("😱", "испугался(ась)", "напугал(а)"),
    "подмигнуть": ("😉", "подмигнул(а)", "получил(а) подмигивание"),
    "пожать_плечами": ("🤷", "пожал(а) плечами", "увидел(а) пожатие плеч"),
    "благословить": ("🙏", "благословил(а)", "был(а) благословлён(а)"),
    "проклясть": ("👿", "проклял(а)", "был(а) проклят(а)"),
    "покормить": ("🍕", "покормил(а)", "был(а) накормлен(а)"),
    "напоить": ("🍺", "напоил(а)", "был(а) напоен(а)"),
    "подарить": ("🎁", "подарил(а) подарок", "получил(а) подарок"),
}

# Хранилище кулдаунов: (actor_id, target_id, action) -> timestamp
RP_COOLDOWNS: Dict[Tuple[int, int, str], float] = {}


def generate_rp_text(actor_name: str, target_name: str, action_key: str) -> str:
    """
    Генерирует отформатированный текст RP-действия с упоминанием и реакцией.
    
    Args:
        actor_name: Имя актёра
        target_name: Имя цели
        action_key: Ключ действия
        
    Returns:
        Отформатированная строка с RP действием
    """
    action_data = RP_ACTIONS.get(action_key, ("✨", "взаимодействовал(а) с", "взаимодействие"))
    # Используем HTML-экранирование для безопасности
    safe_actor = html.escape(actor_name)
    safe_target = html.escape(target_name)
    return f"{action_data[0]} <b>{safe_actor}</b> {action_data[1]} <b>{safe_target}</b>!\n\n💭 <i>{safe_target}: {action_data[2]}</i>"


# ==============================================================================
# 19. УНИВЕРСАЛЬНЫЙ ПАРСЕР ЦЕЛЕЙ
# ==============================================================================

def resolve_command_target(m: Message, command_word: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Универсальная функция для определения цели команды в чате.
    Поддерживает: 1. Reply на сообщение. 2. Упоминание @username. 3. Числовой ID.
    
    Args:
        m: Объект сообщения
        command_word: Слово-команда (для очистки строки)
        
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
                "SELECT user_id FROM players WHERE (LOWER(username)=LOWER(?) OR LOWER(name)=LOWER(?)) AND banned=0 LIMIT 1",
                (val, val)
            )
            if row:
                return row["user_id"], None
                
    # Если ничего не найдено, формируем ошибку в зависимости от типа чата
    if m.chat.type == "private":
        return None, f"Укажи цель: ответь на сообщение или напиши <code>{command_word} @user</code> / <code>{command_word} ID</code>"
    else:
        return None, f"⚠️ В группе команда работает <b>только ответом</b> на сообщение игрока или через <code>@username</code> / <code>ID</code>."


# ==============================================================================
# 20. UI HELPERS
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


def get_attack_keyboard(weapon_key: str, round_no: int, fighter: Fighter) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора типа атаки с учетом перезарядки.
    
    Args:
        weapon_key: Ключ оружия
        round_no: Текущий номер раунда
        fighter: Объект бойца
        
    Returns:
        Объект InlineKeyboardMarkup
    """
    weapon = WEAPONS[weapon_key]
    rows = []
    for atk_type in ["light", "heavy", "special"]:
        atk = weapon["attacks"][atk_type]
        cd = fighter.attack_cooldowns.get(atk_type, 0)
        if cd > round_no:
            label = f"⏳ {atk['name']} ({cd - round_no})"
            data = f"atk_disabled:{atk_type}"
        else:
            # Разноцветные эмодзи для разных типов атак
            color_emoji = "🟥" if atk_type == "heavy" else ("🟪" if atk_type == "special" else "🟦")
            label = f"{color_emoji} {atk['name']}"
            data = f"atk_type:{atk_type}"
        rows.append([(label, data)])
    rows.append([("ℹ️ Инфо об атаках", "atk_info")])
    return build_inline_keyboard(*rows)


def get_zone_keyboard(role: str = "attack") -> InlineKeyboardMarkup:
    """
    Клавиатура выбора зоны атаки или защиты.
    
    Args:
        role: "attack" или "defend"
        
    Returns:
        Объект InlineKeyboardMarkup
    """
    prefix = "duel:atk:" if role == "attack" else "duel:def:"
    return build_inline_keyboard(
        [("🟥 🧠 Голова ×1.5" if role == "attack" else "🟦 🧠 Голова", f"{prefix}head"),
         ("🟧 🫀 Торс ×1.0" if role == "attack" else "🟦 🫀 Торс", f"{prefix}torso")],
        [("🟨 💪 Руки ×0.8" if role == "attack" else "🟦 💪 Руки", f"{prefix}arms"),
         ("🟩 🦵 Ноги ×0.9" if role == "attack" else "🟦 🦵 Ноги", f"{prefix}legs")]
    )


# ==============================================================================
# 21. ХЕНДЛЕРЫ: СТАРТ, МЕНЮ, ПОМОЩЬ
# ==============================================================================

router = Router()

class RegistrationState(StatesGroup):
    """Состояния для процесса регистрации нового игрока."""
    waiting_for_name = State()

class DuelFindState(StatesGroup):
    """Состояния для поиска соперника по нику."""
    waiting_for_target = State()

HELP_TEXT = (
    "╔══════════════════════════╗\n   ⚔️ <b>АРЕНА ДУЭЛЯНТОВ</b>\n╚══════════════════════════╝\n\n"
    "<b>💎 Валюта:</b> Ареники 🪙\n\n"
    "<b>📌 Как использовать команды в чате:</b>\n"
    "• Ответь на сообщение игрока командой\n"
    "• Или напиши: <code>команда @username</code> / <code>команда ID</code>\n\n"
    "<b>⚔️ Дуэли:</b>\n"
    "• <code>перчатка</code> или <code>перч</code> — вызвать на бой\n"
    "• <code>профиль</code> или <code>фото</code> — статистика игрока\n"
    "• <code>перевод [сумма]</code> или <code>пер [сумма]</code> — перевод ареников\n\n"
    "<b>🎰 Казино (в чате):</b>\n"
    "• <code>слоты [сумма]</code> или <code>сл [сумма]</code>\n"
    "• <code>кости [сумма]</code> или <code>кост [сумма]</code>\n"
    "• <code>монетка [сумма] [орел/решка]</code> или <code>мон [сумма] [о/р]</code>\n"
    "• <code>рулетка [сумма] [красное/черное/зеленое]</code> или <code>рул [сумма] [к/ч/з]</code>\n"
    "• <code>больше [сумма]</code> или <code>меньше [сумма]</code>\n\n"
    "<b>🎟 Промокоды:</b>\n"
    "• <code>#код [промокод]</code> или <code>активировать [код]</code> — активировать\n"
    "• <code>промо</code> — список активных промокодов\n\n"
    "<b>👹 Чатовый босс:</b>\n"
    "• <code>босс</code> — атаковать текущего босса\n"
    "• <code>босс инфо</code> — состояние босса\n\n"
    "<b>🏰 Осада крепости:</b>\n"
    "• <code>осада</code> — участвовать в волне\n"
    "• <code>осада инфо</code> — состояние ивента\n\n"
    "<b>🎭 RP действия (25 шт):</b>\n"
    "• <code>ударить</code>, <code>уд</code> | <code>обнять</code>, <code>обн</code>\n"
    "• <code>поцеловать</code>, <code>поц</code> | <code>пнуть</code>, <code>пн</code>\n"
    "• <code>погладить</code>, <code>погл</code> | <code>укусить</code>, <code>ук</code>\n"
    "• <code>пожать</code>, <code>пож</code> | <code>толкнуть</code>, <code>толк</code>\n"
    "• <code>кинуть</code>, <code>кин</code> | <code>лечить</code>, <code>леч</code>\n"
    "• <code>игнор</code>, <code>смеяться</code>, <code>плакать</code>, <code>танцевать</code>\n"
    "• <code>благословить</code>, <code>проклясть</code>, <code>покормить</code>, <code>напоить</code>, <code>подарить</code>\n\n"
    "<b>👑 Админ:</b>\n"
    "• <code>бан</code> / <code>разбан</code>\n"
    "• <code>выдать [сумма]</code>\n"
    "• <code>очки [число]</code> | <code>винрейт [число]</code>\n"
    "• <code>стоп</code> | <code>рассылка [текст]</code> | <code>ботов [число]</code>\n"
    "• <code>промо создать [код] [валюта] [победы] [макс] [часов]</code>\n"
    "• <code>промо удалить [код]</code> | <code>промо список</code>\n"
    "• <code>спавн босса [тип]</code> | <code>начать осаду</code>"
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
            kb = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="🟥 ⚔️ Арена"), KeyboardButton(text="🟪 🎰 Казино")],
                    [KeyboardButton(text="🟦 🎒 Снаряжение"), KeyboardButton(text="🟩 🏆 Топ")],
                    [KeyboardButton(text="🟧 👹 Босс"), KeyboardButton(text="🟨 🏰 Осада")],
                ],
                resize_keyboard=True,
            )
            await m.answer(f"🟢 С возвращением, <b>{esc(p['name'])}</b>! Арена ждёт 👇", reply_markup=kb)
            await flush_notifications(m)
        else:
            await m.answer(f"🟢 С возвращением, <b>{esc(p['name'])}</b>! Пиши <code>help</code> для списка команд.")
        return
        
    await state.set_state(RegistrationState.waiting_for_name)
    await m.answer(
        "⚔️ <b>Добро пожаловать на Арену Дуэлянтов!</b>\n\n"
        "PvP + казино + боссы + промокоды.\n"
        "Уникальная броня на 4 части тела и 9 видов оружия с 3 атаками.\n\n"
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
        INSERT OR IGNORE INTO players (user_id, username, name, currency, wins, losses, weapon,
        armor_head, armor_torso, armor_arms, armor_legs, weapons_owned, armors_owned, created)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        m.from_user.id, m.from_user.username, name, Config.START_CURRENCY, 0, 0, "fists",
        "head_none", "torso_none", "arms_none", "legs_none", "fists", ",".join(START_ARMOR_KEYS), time.time()
    ))
    
    ensure_masked_bots_exist(50)
    await state.clear()
    
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🟥 ⚔️ Арена"), KeyboardButton(text="🟪 🎰 Казино")],
            [KeyboardButton(text="🟦 🎒 Снаряжение"), KeyboardButton(text="🟩 🏆 Топ")],
            [KeyboardButton(text="🟧 👹 Босс"), KeyboardButton(text="🟨 🏰 Осада")],
        ],
        resize_keyboard=True,
    ) if m.chat.type == "private" else None
    
    await m.answer(
        f"🟢 Боец <b>{esc(name)}</b> создан! 🎉\n\n"
        f"{Config.CURRENCY_EMOJI} Стартовый баланс: {Config.START_CURRENCY} ареников\n"
        f"{E_PROMO} Активируй промокоды командой <code>#код [код]</code>",
        reply_markup=kb
    )


@router.message(F.text.regexp(r"(?i)^(help|помощь|хелп)$"))
async def handle_help_command(m: Message) -> None:
    """Обрабатывает команду помощи."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        await m.answer("Сначала отправь /start в ЛС бота.")
        return
        
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🟥 ⚔️ Арена"), KeyboardButton(text="🟪 🎰 Казино")],
            [KeyboardButton(text="🟦 🎒 Снаряжение"), KeyboardButton(text="🟩 🏆 Топ")],
            [KeyboardButton(text="🟧 👹 Босс"), KeyboardButton(text="🟨 🏰 Осада")],
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


def notify_player(uid: int, text: str) -> None:
    """Добавляет уведомление для игрока в БД."""
    if uid <= 0:
        return
    db.execute("INSERT INTO notifications (user_id, text, ts) VALUES (?,?,?)", (uid, text, time.time()))


# ==============================================================================
# 22. ХЕНДЛЕРЫ: ЧАТОВЫЕ КОМАНДЫ (ДУЭЛИ, ПЕРЕВОД, ПРОФИЛЬ)
# ==============================================================================

def is_admin(uid: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    return uid == Config.ADMIN_ID


def is_user_banned(uid: int) -> bool:
    """Проверяет, забанен ли пользователь."""
    p = db.fetch_one("SELECT banned FROM players WHERE user_id=?", (uid,))
    return bool(p and p["banned"])


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
        
    if tid < 0: # Вызов бота
        await initiate_duel_message(m.from_user.id, tid, m, bot)
    else:
        attacker_row = db.fetch_one("SELECT name FROM players WHERE user_id=?", (m.from_user.id,))
        attacker_name = attacker_row["name"] if attacker_row else "Неизвестный"
        
        # УВЕДОМЛЕНИЕ В ЛС ПРОТИВНИКУ
        try:
            await bot.send_message(
                tid,
                f"🥊 <b>{esc(attacker_name)}</b> бросил вам перчатку!\n\n"
                f"Откройте бота и нажмите <code>⚔️ Арена</code>, чтобы начать бой.",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass # У пользователя могут быть закрыты ЛС
            
        notify_player(tid, f"{E_GLOVE} <b>{esc(attacker_name)}</b> вызывает вас на дуэль!")
        await m.answer(f"🥊 Вызов отправлен <b>{esc(target['name'])}</b>. Ожидайте ответа в ЛС.")


@router.message(F.text.regexp(r"(?i)^(перевод|пер|transfer|send)(\s+)(\d+)(\s|$)"))
async def cmd_transfer(m: Message) -> None:
    """Обработка перевода ареников."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        await m.answer("Сначала отправь /start в ЛС бота.")
        return
        
    parts = m.text.split()
    amount = None
    for p in parts[1:]:
        if p.isdigit():
            amount = int(p)
            break
            
    if not amount or amount <= 0:
        await m.answer("Укажи сумму: <code>перевод 100</code>")
        return
        
    tid, err = resolve_command_target(m, parts[0])
    if err:
        await m.answer(err)
        return
    if tid == m.from_user.id:
        await m.answer("🤨 Себе переводить нельзя.")
        return
        
    sender = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    target = db.fetch_one("SELECT * FROM players WHERE user_id=?", (tid,))
    
    if not target:
        await m.answer("Игрок не найден.")
        return
    if sender["currency"] < amount:
        await m.answer(f"У тебя только {sender['currency']}{Config.CURRENCY_EMOJI}")
        return
        
    db.execute("UPDATE players SET currency=currency-? WHERE user_id=?", (amount, m.from_user.id))
    db.execute("UPDATE players SET currency=currency+? WHERE user_id=?", (amount, tid))
    
    await m.answer(f"🟢 Переведено <b>{amount}</b> {Config.CURRENCY_EMOJI} игроку <b>{esc(target['name'])}</b>.")
    notify_player(tid, f"🟢 <b>{esc(sender['name'])}</b> перевёл тебе <b>{amount}</b> ареников!")


@router.message(F.text.regexp(r"(?i)^(профиль|фото|stat|me)(\s|$)"))
async def cmd_show_profile(m: Message) -> None:
    """Показывает профиль игрока (свой или указанного)."""
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


def generate_profile_text(row: sqlite3.Row) -> str:
    """Генерирует текстовое описание профиля игрока."""
    if not row:
        return "Профиль не найден."
        
    w = WEAPONS[row["weapon"]] if row["weapon"] in WEAPONS else WEAPONS["fists"]
    f = create_fighter_from_db(row)
    slots = get_player_armor_slots(row)
    arena = ARENAS[determine_arena(row["wins"])]
    
    lines = [
        f"🟢 <b>{esc(row['name'])}</b>", "",
        f"🟡 {E_TROPHY} {row['wins']}  ·  {E_SKULL} {row['losses']}  ·  {Config.CURRENCY_EMOJI} {row['currency']}",
        f"🔵 📍 {arena['emoji']} {arena['name']}", "",
        f"🔴 ❤️ HP: <b>{f.max_hp}</b>",
        f"⚔️ {w['emoji']} {w['name']} — урон <b>{w['dmg']}</b>", "",
        f"🟣 👊 RP дано: <b>{row['rp_given']}</b> · Получено: <b>{row['rp_received']}</b>",
        f"🟠 👹 Боссов убито: <b>{row['boss_kills']}</b>",
        f"🟤 🏰 Осад пройдено: <b>{row['siege_wins']}</b>", "",
        "<b>🛡 Броня:</b>"
    ]
    
    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"  {ZONE_INFO[slot]['emoji']} {ZONE_INFO[slot]['name']}: {item['emoji']} {item['name']} ({item['df']})")
        
    return "\n".join(lines)


# ==============================================================================
# 23. ХЕНДЛЕРЫ: RP ДЕЙСТВИЯ
# ==============================================================================

async def process_rp_action(m: Message, action_key: str) -> None:
    """Обрабатывает RP-действие с проверкой кулдаунов и упоминанием."""
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
    
    # Обновляем статистику RP
    db.execute("UPDATE players SET rp_given=rp_given+1 WHERE user_id=?", (m.from_user.id,))
    db.execute("UPDATE players SET rp_received=rp_received+1 WHERE user_id=?", (tid,))
    
    actor = db.fetch_one("SELECT name FROM players WHERE user_id=?", (m.from_user.id,))
    
    # Генерируем текст с реакцией получателя
    action_data = RP_ACTIONS.get(action_key, ("✨", "взаимодействовал(а) с", "взаимодействие"))
    safe_actor = esc(actor["name"])
    safe_target = esc(target["name"])
    
    text = f"{action_data[0]} <b>{safe_actor}</b> {action_data[1]} <b>{safe_target}</b>!\n\n"
    text += f"💭 <i>{safe_target}: {action_data[2]}</i>"
    
    await m.answer(text)


# Динамическая регистрация хендлеров для всех RP команд с сокращениями
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
    "игнорировать": ["игнор", "игнорировать", "ignore"],
    "смеяться": ["смеяться", "смех", "laugh"],
    "плакать": ["плакать", "плач", "cry"],
    "танцевать": ["танцевать", "танец", "dance"],
    "шлепнуть": ["шлепнуть", "шлеп", "slap"],
    "обозвать": ["обозвать", "обзыв"],
    "восхититься": ["восхититься", "восх"],
    "испугаться": ["испугаться", "испуг", "fear"],
    "подмигнуть": ["подмигнуть", "подмиг", "wink"],
    "пожать_плечами": ["плечи", "shrug"],
    "благословить": ["благословить", "благ", "bless"],
    "проклясть": ["проклясть", "прокл", "curse"],
    "покормить": ["покормить", "корм", "feed"],
    "напоить": ["напоить", "поить", "drink"],
    "подарить": ["подарить", "подарок", "gift"],
}

for action, variants in RP_MAPPINGS.items():
    pattern = r"(?i)^(" + "|".join(re.escape(v) for v in variants) + r")(\s|$)"
    
    def make_rp_handler(act: str) -> Callable:
        async def handler(m: Message) -> None:
            await process_rp_action(m, act)
        return handler
        
    router.message(F.text.regexp(pattern))(make_rp_handler(action))


# ==============================================================================
# 24. ХЕНДЛЕРЫ: КАЗИНО В ЧАТЕ (С СОКРАЩЕНИЯМИ)
# ==============================================================================

@router.message(F.text.regexp(r"(?i)^(слоты|slot|сл|s)(\s+)(\d+)$"))
async def cmd_chat_slots(m: Message) -> None:
    """Обработка команды слоты в чате."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    bet = int(m.text.split()[-1])
    result, err = play_casino_slots(m.from_user.id, bet)
    if err:
        await m.answer(err)
        return
    p2 = db.fetch_one("SELECT currency FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n🟢 Баланс: <b>{p2['currency']}</b> {Config.CURRENCY_EMOJI}")


@router.message(F.text.regexp(r"(?i)^(кости|dice|кост|d)(\s+)(\d+)$"))
async def cmd_chat_dice(m: Message) -> None:
    """Обработка команды кости в чате."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    bet = int(m.text.split()[-1])
    result, err = play_casino_dice(m.from_user.id, bet)
    if err:
        await m.answer(err)
        return
    p2 = db.fetch_one("SELECT currency FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n🟢 Баланс: <b>{p2['currency']}</b> {Config.CURRENCY_EMOJI}")


@router.message(F.text.regexp(r"(?i)^(монетка|coin|мон|c)(\s+)(\d+)(\s+)(орел|решка|о|р)$"))
async def cmd_chat_coin(m: Message) -> None:
    """Обработка команды монетка в чате."""
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
    p2 = db.fetch_one("SELECT currency FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n🟢 Баланс: <b>{p2['currency']}</b> {Config.CURRENCY_EMOJI}")


@router.message(F.text.regexp(r"(?i)^(рулетка|roulette|рул|r)(\s+)(\d+)(\s+)(красное|черное|зеленое|к|ч|з)$"))
async def cmd_chat_roulette(m: Message) -> None:
    """Обработка команды рулетка в чате."""
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
    p2 = db.fetch_one("SELECT currency FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n🟢 Баланс: <b>{p2['currency']}</b> {Config.CURRENCY_EMOJI}")


@router.message(F.text.regexp(r"(?i)^(больше|high|h)(\s+)(\d+)$"))
async def cmd_chat_highlow_high(m: Message) -> None:
    """Обработка команды больше в чате."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    bet = int(m.text.split()[-1])
    result, err = play_casino_highlow(m.from_user.id, bet, "high")
    if err:
        await m.answer(err)
        return
    p2 = db.fetch_one("SELECT currency FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n🟢 Баланс: <b>{p2['currency']}</b> {Config.CURRENCY_EMOJI}")


@router.message(F.text.regexp(r"(?i)^(меньше|low|l)(\s+)(\d+)$"))
async def cmd_chat_highlow_low(m: Message) -> None:
    """Обработка команды меньше в чате."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return
    bet = int(m.text.split()[-1])
    result, err = play_casino_highlow(m.from_user.id, bet, "low")
    if err:
        await m.answer(err)
        return
    p2 = db.fetch_one("SELECT currency FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n🟢 Баланс: <b>{p2['currency']}</b> {Config.CURRENCY_EMOJI}")


# ==============================================================================
# 25. ХЕНДЛЕРЫ: ПРОМОКОДЫ (ИГРОК)
# ==============================================================================

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
    
    promos = db.fetch_all("SELECT * FROM promo_codes WHERE active=1 ORDER BY created_at DESC")
    now = time.time()
    valid_promos = [p for p in promos if p["expires_at"] > now and p["current_uses"] < p["max_uses"]]
    
    if not valid_promos:
        await m.answer(f"{E_PROMO} <b>Активных промокодов сейчас нет.</b>\n\nСледи за новостями — администратор периодически выпускает новые коды!")
        return
    
    lines = [f"{E_PROMO} <b>АКТИВНЫЕ ПРОМОКОДЫ</b>\n", f"Найдено: <b>{len(valid_promos)}</b>\n"]
    
    for i, promo in enumerate(valid_promos[:10], 1):
        remaining = promo["max_uses"] - promo["current_uses"]
        exp_str = time.strftime("%d.%m %H:%M", time.localtime(promo["expires_at"]))
        lines.append(f"{i}. <code>{promo['code']}</code>")
        rewards = []
        if promo["reward_currency"] > 0:
            rewards.append(f"💎{promo['reward_currency']}")
        if promo["reward_wins"] > 0:
            rewards.append(f"🏆{promo['reward_wins']}")
        lines.append(f"   Награда: {' + '.join(rewards) if rewards else '🎁'}")
        lines.append(f"   Осталось: {remaining}/{promo['max_uses']} · до {exp_str}\n")
    
    if len(valid_promos) > 10:
        lines.append(f"… и ещё {len(valid_promos) - 10} промокодов")
        
    lines.append(f"\n{E_MAGIC} Активируй: <code>#код [код]</code>")
    
    await m.answer("\n".join(lines))


# ==============================================================================
# 26. ХЕНДЛЕРЫ: ЧАТОВЫЙ БОСС И ОСАДА (ИВЕНТЫ)
# ==============================================================================

@router.message(F.text.regexp(r"(?i)^босс(\s|$)"))
async def cmd_boss_attack(m: Message, bot: Bot) -> None:
    """Атака чатового босса."""
    player = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not player:
        await m.answer("Сначала /start")
        return
        
    state = get_chat_boss_state()
    if not state or not state["active"]:
        await m.answer(f"{E_WARN} Сейчас нет активного босса!\n\nАдмин может заспавнить командой <code>спавн босса</code>")
        return

    boss = next((b for b in CHAT_BOSSES if b["key"] == state["boss_key"]), None)
    if not boss:
        return

    # Рассчитываем урон на основе оружия игрока
    weapon = WEAPONS.get(player["weapon"], WEAPONS["fists"])
    base_dmg = weapon["dmg"]
    damage = random.randint(int(base_dmg * 0.8), int(base_dmg * 1.5))

    result = attack_global_event(m.from_user.id, damage, "boss", state["boss_key"])
    new_state = get_chat_boss_state()

    if result == "killed":
        rewards = distribute_global_event_rewards("boss", state["boss_key"])
        lines = [
            f"🎉 <b>{boss['name']} ПОВЕРЖЕН!</b>\n",
            f"{E_EXPLO} Последний удар: <b>{esc(player['name'])}</b> на <b>{damage}</b> урона!\n",
            "<b>🏆 Награды (по % урона):</b>"
        ]
        for uid, share, dmg, hits in rewards[:10]:
            p_row = db.fetch_one("SELECT name FROM players WHERE user_id=?", (uid,))
            name = p_row["name"] if p_row else "?"
            lines.append(f"• {esc(name)} — {share}{Config.CURRENCY_EMOJI} ({dmg} урона, {hits} ударов)")
        if len(rewards) > 10:
            lines.append(f"… и ещё {len(rewards) - 10} участников")
        await m.answer("\n".join(lines))
    else:
        # Визуальная полоска HP
        max_hp = new_state["max_hp"]
        curr_hp = new_state["current_hp"]
        ratio = curr_hp / max_hp
        bar_char = "🟩" if ratio > 0.6 else ("🟨" if ratio > 0.3 else "🟥")
        bar_len = int(15 * ratio)
        hp_bar_str = bar_char * bar_len + "⬛" * (15 - bar_len)
        
        await m.answer(
            f"🟥 <b>{esc(player['name'])}</b> нанёс <b>{damage}</b> урона {boss['name']}!\n\n"
            f"❤️ HP: <b>{curr_hp}</b>/{max_hp} {hp_bar_str}"
        )


@router.message(F.text.regexp(r"(?i)^босс инфо$"))
async def cmd_boss_info(m: Message) -> None:
    """Информация о текущем боссе."""
    state = get_chat_boss_state()
    if not state or not state["active"]:
        await m.answer(f"{E_WARN} Нет активного босса")
        return
        
    boss = next((b for b in CHAT_BOSSES if b["key"] == state["boss_key"]), None)
    if not boss:
        return
        
    damages = db.fetch_all(
        "SELECT user_id, damage, hits FROM event_damage WHERE event_type='boss' AND event_key=? ORDER BY damage DESC LIMIT 5",
        (state["boss_key"],)
    )
    
    max_hp = state["max_hp"]
    curr_hp = state["current_hp"]
    ratio = curr_hp / max_hp
    bar_char = "🟩" if ratio > 0.6 else ("🟨" if ratio > 0.3 else "🟥")
    bar_len = int(15 * ratio)
    hp_bar_str = bar_char * bar_len + "⬛" * (15 - bar_len)
    
    lines = [
        f"{E_BOSS} <b>{boss['name']}</b>\n",
        f"{boss['desc']}\n",
        f"❤️ HP: <b>{curr_hp}</b>/{max_hp} {hp_bar_str}\n",
        f"💰 Пул наград: <b>{state['reward_pool']}</b>{Config.CURRENCY_EMOJI}\n",
        f"🏆 Топ урона:"
    ]
    
    for d in damages:
        p_row = db.fetch_one("SELECT name FROM players WHERE user_id=?", (d["user_id"],))
        name = p_row["name"] if p_row else "?"
        lines.append(f"• {esc(name)} — {d['damage']} урона ({d['hits']} ударов)")
        
    lines.append(f"\n💥 Используй <code>босс</code> для атаки!")
    await m.answer("\n".join(lines))


@router.message(F.text.regexp(r"(?i)^осада(\s|$)"))
async def cmd_siege(m: Message) -> None:
    """Участие в осаде крепости."""
    player = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not player:
        await m.answer("Сначала /start")
        return
        
    state = get_siege_state()
    if not state or not state["active"]:
        await m.answer(f"{E_WARN} Осада не активна!\n\nАдмин может начать: <code>начать осаду</code>")
        return
        
    wave_data = SIEGE_WAVES[f"wave{state['current_wave']}"]
    weapon = WEAPONS.get(player["weapon"], WEAPONS["fists"])
    damage = random.randint(int(weapon["dmg"] * 0.8), int(weapon["dmg"] * 1.5))
    
    attack_global_event(m.from_user.id, damage, f"siege_{state['current_wave']}", "current")
    db.execute("UPDATE players SET siege_wins=siege_wins+1, currency=currency+? WHERE user_id=?", (wave_data['reward'], m.from_user.id))
    
    await m.answer(
        f"🟨 <b>Волна {state['current_wave']}: {wave_data['name']}</b>\n\n"
        f"{E_SWORD} <b>{esc(player['name'])}</b> уничтожил врагов на <b>{damage}</b> урона!\n"
        f"🟢 Награда за волну: <b>{wave_data['reward']}</b> {Config.CURRENCY_NAME}"
    )


@router.message(F.text.regexp(r"(?i)^осада инфо$"))
async def cmd_siege_info(m: Message) -> None:
    """Информация о текущей осаде."""
    state = get_siege_state()
    if not state or not state["active"]:
        await m.answer(f"{E_WARN} Осада не активна")
        return
        
    wave_data = SIEGE_WAVES[f"wave{state['current_wave']}"]
    lines = [
        f"🟨 <b>ОСАДА КРЕПОСТИ</b>\n",
        f"🌊 Текущая волна: <b>{state['current_wave']}</b>/5\n",
        f"{wave_data['name']}\n",
        f"👹 Врагов: {wave_data['enemies']} · HP каждого: {wave_data['hp_each']}\n",
        f"💰 Награда: <b>{wave_data['reward']}</b>{Config.CURRENCY_EMOJI}\n",
        f"\n💥 Используй <code>осада</code> для атаки!"
    ]
    await m.answer("\n".join(lines))


# ==============================================================================
# 27. ХЕНДЛЕРЫ: АДМИН КОМАНДЫ
# ==============================================================================

@router.message(F.text.regexp(r"(?i)^бан(\s|$)"))
async def adm_cmd_ban(m: Message) -> None:
    """Бан игрока."""
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_command_target(m, "бан")
    if err or not tid:
        await m.answer(err or "Не найдено.")
        return
    db.execute("UPDATE players SET banned=1 WHERE user_id=?", (tid,))
    ACTIVE_DUELS.pop(tid, None)
    await m.answer(f"🔴 Игрок <code>{tid}</code> забанен.")


@router.message(F.text.regexp(r"(?i)^разбан(\s|$)"))
async def adm_cmd_unban(m: Message) -> None:
    """Разбан игрока."""
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_command_target(m, "разбан")
    if err or not tid:
        await m.answer(err or "Не найдено.")
        return
    db.execute("UPDATE players SET banned=0 WHERE user_id=?", (tid,))
    await m.answer(f"🟢 Игрок <code>{tid}</code> разбанен.")


@router.message(F.text.regexp(r"(?i)^выдать(\s|$)"))
async def adm_cmd_give(m: Message) -> None:
    """Выдать валюту игроку."""
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
        
    db.execute("UPDATE players SET currency=currency+? WHERE user_id=?", (amount, tid))
    await m.answer(f"🟢 Выдано {amount}{Config.CURRENCY_EMOJI} игроку <code>{tid}</code>.")
    notify_player(tid, f"🎁 Админ выдал тебе {amount}{Config.CURRENCY_EMOJI}")


@router.message(F.text.regexp(r"(?i)^очки(\s|$)"))
async def adm_cmd_points(m: Message) -> None:
    """Начислить победы игроку."""
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
    await m.answer(f"🟢 Игроку <code>{tid}</code> начислено {amount} {E_TROPHY}.")
    notify_player(tid, f"🎁 Админ начислил тебе {amount} {E_TROPHY}")


@router.message(F.text.regexp(r"(?i)^винрейт(\s|$)"))
async def adm_cmd_setwins(m: Message) -> None:
    """Установить количество побед игроку."""
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
    await m.answer(f"🟢 Игроку <code>{tid}</code> установлено {amount} {E_TROPHY}.")
    notify_player(tid, f"🎁 Админ установил тебе {amount} {E_TROPHY}")


@router.message(F.text.regexp(r"(?i)^стоп(\s|$)"))
async def adm_cmd_stop_duel(m: Message) -> None:
    """Принудительно завершить бой игрока."""
    if not is_admin(m.from_user.id):
        return
    tid, err = resolve_command_target(m, "стоп")
    if err or not tid:
        await m.answer(err or "Не найдено.")
        return
        
    if tid in ACTIVE_DUELS:
        terminate_duel(ACTIVE_DUELS[tid])
        await m.answer(f"🟢 Бой игрока <code>{tid}</code> принудительно завершен.")
    else:
        await m.answer("У игрока нет активного боя.")


@router.message(F.text.regexp(r"(?i)^рассылка\s+"))
async def adm_cmd_broadcast(m: Message, bot: Bot) -> None:
    """Рассылка сообщения всем игрокам."""
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
            await asyncio.sleep(0.05) # Anti-flood задержка
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except Exception:
            pass
            
    await m.answer(f"🟢 Рассылка завершена. Доставлено: {ok_count} игрокам.")


@router.message(F.text.regexp(r"(?i)^ботов(\s|$)"))
async def adm_cmd_addbots(m: Message) -> None:
    """Добавить скрытых ботов."""
    if not is_admin(m.from_user.id):
        return
    n = next((int(p) for p in (m.text or "").split() if p.isdigit()), 10)
    before = db.fetch_one("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    ensure_masked_bots_exist(before + n)
    after = db.fetch_one("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    await m.answer(f"🟢 Добавлено: {after - before} ботов.")


@router.message(F.text.regexp(r"(?i)^промо создать\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$"))
async def adm_cmd_promo_create(m: Message) -> None:
    """Создание промокода."""
    if not is_admin(m.from_user.id):
        return
    match = re.search(r"(?i)^промо создать\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$", m.text or "")
    if not match:
        await m.answer("Использование: <code>промо создать [код] [валюта] [победы] [макс] [часов]</code>")
        return
    
    code = match.group(1)
    reward_currency = int(match.group(2))
    reward_wins = int(match.group(3))
    max_uses = int(match.group(4))
    hours = int(match.group(5))
    
    success, message = create_promo_code(code, reward_currency, reward_wins, max_uses, hours, m.from_user.id)
    await m.answer(message)


@router.message(F.text.regexp(r"(?i)^промо удалить\s+(\S+)$"))
async def adm_cmd_promo_delete(m: Message) -> None:
    """Удаление (деактивация) промокода."""
    if not is_admin(m.from_user.id):
        return
    match = re.search(r"(?i)^промо удалить\s+(\S+)$", m.text or "")
    if not match:
        return
    
    code = match.group(1)
    success, message = deactivate_promo_code(code)
    await m.answer(message)


@router.message(F.text.regexp(r"(?i)^промо список$"))
async def adm_cmd_promo_list_admin(m: Message) -> None:
    """Список всех промокодов для админа."""
    if not is_admin(m.from_user.id):
        return
    
    promos = db.fetch_all("SELECT * FROM promo_codes ORDER BY created_at DESC")
    if not promos:
        await m.answer(f"{E_PROMO} <b>Промокодов пока нет.</b>\n\nСоздай первый: <code>промо создать [код] [валюта] [победы] [макс] [часов]</code>")
        return
    
    lines = [f"{E_PROMO} <b>ВСЕ ПРОМОКОДЫ ({len(promos)})</b>\n"]
    
    for i, promo in enumerate(promos[:20], 1):
        status = "✅" if promo["active"] and promo["expires_at"] > time.time() and promo["current_uses"] < promo["max_uses"] else "❌"
        expires_str = time.strftime("%d.%m %H:%M", time.localtime(promo["expires_at"]))
        lines.append(f"{i}. {status} <code>{promo['code']}</code>")
        rewards = []
        if promo["reward_currency"] > 0:
            rewards.append(f"💎{promo['reward_currency']}")
        if promo["reward_wins"] > 0:
            rewards.append(f"🏆{promo['reward_wins']}")
        lines.append(f"   Награда: {' + '.join(rewards) if rewards else '—'}")
        lines.append(f"   Активаций: {promo['current_uses']}/{promo['max_uses']}")
        lines.append(f"   Истекает: {expires_str}\n")
    
    if len(promos) > 20:
        lines.append(f"… и ещё {len(promos) - 20} промокодов")
    
    await m.answer("\n".join(lines))


@router.message(F.text.regexp(r"(?i)^спавн босса(\s+(\w+))?$"))
async def adm_cmd_spawn_boss(m: Message, bot: Bot) -> None:
    """Спавн чатового босса."""
    if not is_admin(m.from_user.id):
        return
    match = re.search(r"(?i)^спавн босса\s+(\w+)$", m.text or "")
    force_key = match.group(1) if match else None
    
    if force_key and force_key not in [b["key"] for b in CHAT_BOSSES]:
        await m.answer(f"Доступные боссы: {', '.join(b['key'] for b in CHAT_BOSSES)}")
        return
        
    boss = spawn_global_event(m.chat.id, "boss", force_key)
    
    msg = (
        f"{E_BOSS} <b>ПОЯВИЛСЯ БОСС!</b>\n\n"
        f"{boss['name']}\n{boss['desc']}\n\n"
        f"❤️ HP: <b>{boss['hp']}</b>\n"
        f"💰 Пул наград: <b>{boss['reward_pool']}</b>{Config.CURRENCY_EMOJI}\n\n"
        f"💥 Игроки, используйте <code>босс</code> для атаки!"
    )
    await m.answer(msg)


@router.message(F.text.regexp(r"(?i)^начать осаду$"))
async def adm_cmd_start_siege(m: Message) -> None:
    """Запуск осады крепости."""
    if not is_admin(m.from_user.id):
        return
    wave = spawn_global_event(m.chat.id, "siege")
    msg = (
        f"🟨 <b>ОСАДА КРЕПОСТИ НАЧАЛАСЬ!</b>\n\n"
        f"🌊 Волна 1: {wave['name']}\n"
        f"👹 Врагов: {wave['enemies']} · HP: {wave['hp_each']}\n"
        f"💰 Награда: <b>{wave['reward']}</b>{Config.CURRENCY_EMOJI}\n\n"
        f"💥 Игроки, используйте <code>осада</code> для атаки!"
    )
    await m.answer(msg)


@router.message(F.text.regexp(r"(?i)^следующая волна$"))
async def adm_cmd_next_wave(m: Message) -> None:
    """Продвижение волны осады."""
    if not is_admin(m.from_user.id):
        return
    state = get_siege_state()
    if not state or not state["active"]:
        await m.answer("Осада не активна")
        return
        
    if state["current_wave"] >= 5:
        db.execute("UPDATE siege_event SET active=0 WHERE id=1")
        await m.answer(f"🎉 <b>ОСАДА ЗАВЕРШЕНА!</b>\nВсе выжившие получают бонусы!")
        return
        
    db.execute("UPDATE siege_event SET current_wave=current_wave+1 WHERE id=1")
    wave = SIEGE_WAVES[f"wave{state['current_wave']+1}"]
    await m.answer(
        f"🟨 <b>Волна {state['current_wave']+1}</b>\n{wave['name']}\n"
        f"👹 {wave['enemies']} врагов · HP {wave['hp_each']}\n"
        f"💰 Награда: {wave['reward']}{Config.CURRENCY_EMOJI}"
    )


@router.message(Command("admin"))
async def cmd_admin_panel(m: Message) -> None:
    """Панель админ-команд."""
    if not is_admin(m.from_user.id):
        return
    await m.answer(
        "🛠 <b>Админ-команды</b>\n\n"
        "<b>Игроки:</b>\n"
        "• <code>бан</code> / <code>разбан</code>\n"
        "• <code>выдать [сумма]</code>\n"
        "• <code>очки [число]</code>\n"
        "• <code>винрейт [число]</code>\n"
        "• <code>стоп</code>\n"
        "• <code>рассылка [текст]</code>\n"
        "• <code>ботов [число]</code>\n\n"
        "<b>🎟 Промокоды:</b>\n"
        "• <code>промо создать [код] [валюта] [победы] [макс] [часов]</code>\n"
        "• <code>промо удалить [код]</code>\n"
        "• <code>промо список</code>\n\n"
        "<b>🌍 Ивенты:</b>\n"
        "• <code>спавн босса [тип]</code>\n"
        "• <code>начать осаду</code>\n"
        "• <code>следующая волна</code>"
    )


@router.message(Command("stats"))
async def cmd_bot_stats(m: Message) -> None:
    """Статистика бота."""
    if not is_admin(m.from_user.id):
        return
    total = db.fetch_one("SELECT COUNT(*) c FROM players WHERE is_bot=0")["c"]
    bots = db.fetch_one("SELECT COUNT(*) c FROM players WHERE is_bot=1")["c"]
    banned = db.fetch_one("SELECT COUNT(*) c FROM players WHERE banned=1")["c"]
    promos = db.fetch_one("SELECT COUNT(*) c FROM promo_codes WHERE active=1")["c"]
    
    boss_state = get_chat_boss_state()
    boss_info = f"Активен: {boss_state['boss_key']}" if boss_state and boss_state["active"] else "Нет"
    
    siege_state = get_siege_state()
    siege_info = f"Волна {siege_state['current_wave']}" if siege_state and siege_state["active"] else "Нет"
    
    await m.answer(
        f"📊 <b>Статистика бота:</b>\n"
        f"👥 Игроков: {total}\n"
        f"🤖 Скрытых ботов: {bots}\n"
        f"🚫 В бане: {banned}\n"
        f"🎟 Активных промокодов: {promos}\n"
        f"⚔️ Активных боёв: {len({id(d) for d in ACTIVE_DUELS.values()})}\n"
        f"🟥 Чатовый босс: {boss_info}\n"
        f"🟨 Осада: {siege_info}"
    )


# ==============================================================================
# 28. ЛОГИКА ДУЭЛИ: ЗАПУСК, РАУНДЫ, ЗАВЕРШЕНИЕ
# ==============================================================================

def initiate_duel(a_id: int, b_id: int, is_boss: bool = False, boss_key: Optional[str] = None, reward_mult: int = 1) -> Optional[Duel]:
    """Создает и инициализирует объект дуэли."""
    a_row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (a_id,))
    if not a_row:
        return None
        
    fa = create_fighter_from_db(a_row)
    
    if is_boss and boss_key in DUNGEON_BOSSES:
        fb = create_boss_fighter(DUNGEON_BOSSES[boss_key])
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
        fighter = duel.get_attacker()
        await m.answer(
            generate_duel_status_text(duel, aid, timer_left=Config.TURN_TIMEOUT),
            reply_markup=get_attack_keyboard(fighter.weapon, duel.round_no, fighter)
        )
        start_duel_timer(duel, aid, "attacker", bot)
    else:
        atk_id = duel.get_attacker_id()
        if atk_id < 0:
            atk_type, atk_zone = bot_decide_attack(duel.get_attacker(), duel.get_defender(), duel.round_no)
            duel.atk_type = atk_type
            duel.atk_zone = atk_zone
            weapon = WEAPONS[duel.get_attacker().weapon]
            atk_name = weapon["attacks"][atk_type]["name"]
            await m.answer(
                generate_duel_status_text(duel, aid, extra=f"⚔️ Соперник выбрал: <b>{atk_name}</b>", timer_left=Config.TURN_TIMEOUT),
                reply_markup=get_zone_keyboard("defend")
            )
            start_duel_timer(duel, aid, "defender", bot)
        else:
            await m.answer(
                generate_duel_status_text(duel, aid, extra="⏳ Соперник выбирает атаку…"),
                reply_markup=build_inline_keyboard([("🔄 Обновить", "duel:refresh")])
            )
            
    if bid > 0 and not is_boss:
        attacker_name = db.fetch_one("SELECT name FROM players WHERE user_id=?", (aid,))["name"]
        notify_player(bid, f"{E_GLOVE} <b>{esc(attacker_name)}</b> кинул тебе перчатку! Открой «⚔️ Арена» в ЛС бота.")


async def process_duel_round(duel: Duel, bot: Bot, cb: Optional[CallbackQuery], atk_type: str, atk_zone: str, def_zone: Optional[str]) -> None:
    """Обрабатывает один раунд боя."""
    if duel.finished:
        return
    stop_duel_timer(duel)
    
    attacker = duel.get_attacker()
    defender = duel.get_defender()

    duel.log.append(f"── Раунд {duel.round_no} ──")
    weapon = WEAPONS[attacker.weapon]
    atk_name = weapon["attacks"][atk_type]["name"]
    duel.log.append(f"⚔️ {attacker.name}: <b>{atk_name}</b> → {ZONE_INFO[atk_zone]['name']}")
    
    if def_zone:
        duel.log.append(f"🛡 {defender.name} защитил {ZONE_INFO[def_zone]['name']}")

    process_dots(attacker, duel.log)
    if not attacker.is_alive():
        return await finalize_duel(duel, winner_is_a=(attacker is duel.b), bot=bot)

    success = execute_attack_phase(attacker, defender, atk_zone, def_zone, atk_type, duel.log, duel.round_no)
    
    # Если атака не удалась из-за КД, fallback на light
    if not success:
        execute_attack_phase(attacker, defender, atk_zone, def_zone, "light", duel.log, duel.round_no)
        
    if not defender.is_alive():
        return await finalize_duel(duel, winner_is_a=(defender is duel.a), bot=bot)

    # Смена ролей для следующего раунда
    duel.atk_zone = None
    duel.atk_type = None
    duel.attacker_is_a = not duel.attacker_is_a
    duel.round_no += 1
    
    if duel.round_no - duel.bot_last_block_round > 4:
        duel.bot_block_streak = 0
        
    await start_next_duel_round(duel, bot)


async def start_next_duel_round(duel: Duel, bot: Bot) -> None:
    """Инициализирует следующий раунд, отправляя сообщения участникам."""
    if duel.finished:
        return
        
    atk_id = duel.get_attacker_id()
    def_id = duel.get_defender_id()

    if atk_id > 0:
        fighter = duel.get_attacker()
        await bot.send_message(
            atk_id,
            generate_duel_status_text(duel, atk_id, extra="🎯 Твой ход — выбери тип атаки", timer_left=Config.TURN_TIMEOUT),
            reply_markup=get_attack_keyboard(fighter.weapon, duel.round_no, fighter)
        )
        start_duel_timer(duel, atk_id, "attacker", bot)
    else:
        atk_type, atk_zone = bot_decide_attack(duel.get_attacker(), duel.get_defender(), duel.round_no)
        duel.atk_type = atk_type
        duel.atk_zone = atk_zone
        weapon = WEAPONS[duel.get_attacker().weapon]
        atk_name = weapon["attacks"][atk_type]["name"]
        duel.log.append(f"⚔️ {duel.get_attacker().name} выбирает: <b>{atk_name}</b>")
        
        if def_id > 0:
            await bot.send_message(
                def_id,
                generate_duel_status_text(duel, def_id, extra=f"{E_SHIELD} Соперник атакует: <b>{atk_name}</b>", timer_left=Config.TURN_TIMEOUT),
                reply_markup=get_zone_keyboard("defend")
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
        db.execute("UPDATE players SET currency=currency+? WHERE user_id=?", (prize, aid))
        
        if bid and bid > 0:
            db.execute("UPDATE players SET losses=losses+1, wins=CASE WHEN wins>0 THEN wins-1 ELSE 0 END WHERE user_id=?", (bid,))
            a_name = a_row["name"]
            notify_player(bid, f"{E_SKULL} <b>{esc(a_name)}</b> одолел тебя. −1 {E_TROPHY}, без награды.")
            
        result_line = f"{E_TROPHY} <b>ТЫ ПОБЕДИЛ!</b>  +1 {E_TROPHY}  ·  +{prize}{Config.CURRENCY_EMOJI}"
    else:
        if bid and bid > 0:
            db.execute("UPDATE players SET wins=wins+1 WHERE user_id=?", (bid,))
            current_wins_b = db.fetch_one("SELECT wins FROM players WHERE user_id=?", (bid,))["wins"]
            prize_b = ARENAS[determine_arena(current_wins_b)]["prize"] * mult
            db.execute("UPDATE players SET currency=currency+? WHERE user_id=?", (prize_b, bid))
            
            a_name = a_row["name"]
            notify_player(bid, f"{E_TROPHY} <b>{esc(a_name)}</b> проиграл тебе! +1 {E_TROPHY}, +{prize_b}{Config.CURRENCY_EMOJI}")
            
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
        f"{Config.CURRENCY_EMOJI} Ареники: <b>{new_a['currency']}</b>\n"
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
                f"{Config.CURRENCY_EMOJI} Ареники: <b>{new_b['currency']}</b>\n"
                f"📍 {b_arena['emoji']} {b_arena['name']}"
                f"{reason_line}\n\nВыбери действие:"
            )
            try:
                await bot.send_message(bid, text_b, reply_markup=get_finish_duel_kb())
            except Exception:
                pass


def generate_duel_status_text(duel: Duel, for_uid: int, extra: str = "", timer_left: Optional[int] = None) -> str:
    """Генерирует статус боя для конкретного участника."""
    role = duel.get_state_for(for_uid)
    atk_name = duel.get_attacker().name
    me = duel.get_fighter(for_uid) or duel.a
    opp = duel.get_opponent(for_uid) or duel.b

    if role == "attacker":
        prompt = "🎯 <b>Твой ход</b> — выбери тип атаки"
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


def get_finish_duel_kb() -> InlineKeyboardMarkup:
    """Клавиатура окончания боя."""
    return build_inline_keyboard(
        [("🟪 🔁 Ещё раз", "duel:again")],
        [("🟦 🏠 В главное меню", "arena:menu")]
    )


# ==============================================================================
# 29. CALLBACK HANDLERS (INLINE КНОПКИ)
# ==============================================================================

@router.callback_query(F.data == "arena:menu")
async def cb_arena_menu(cb: CallbackQuery, state: FSMContext) -> None:
    """Главное меню арены."""
    await state.clear()
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    await safe_edit_message(cb, *generate_arena_menu_screen(cb.from_user.id))
    await cb.answer()


@router.callback_query(F.data == "arena:bosses")
async def cb_arena_bosses(cb: CallbackQuery) -> None:
    """Меню боссов."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    await safe_edit_message(cb, *generate_bosses_menu_screen(cb.from_user.id))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^arena:boss:\w+$"))
async def cb_arena_boss_fight(cb: CallbackQuery, bot: Bot) -> None:
    """Бой с боссом."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p or cb.from_user.id in ACTIVE_DUELS:
        await cb.answer("Сначала /start или бой уже идёт", show_alert=True)
        return
        
    bkey = cb.data.split(":")[2]
    if bkey not in DUNGEON_BOSSES or p["wins"] < DUNGEON_BOSSES[bkey]["min_wins"]:
        await cb.answer(f"Нужно {DUNGEON_BOSSES[bkey]['min_wins']} {E_TROPHY} для этого босса.", show_alert=True)
        return
        
    duel = initiate_duel(cb.from_user.id, -1, is_boss=True, boss_key=bkey, reward_mult=DUNGEON_BOSSES[bkey]["reward_mult"])
    if not duel:
        await cb.answer("Ошибка запуска боя.", show_alert=True)
        return
        
    role = duel.get_state_for(cb.from_user.id)
    if role == "attacker":
        fighter = duel.get_attacker()
        await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, timer_left=Config.TURN_TIMEOUT), get_attack_keyboard(fighter.weapon, duel.round_no, fighter))
        start_duel_timer(duel, cb.from_user.id, "attacker", bot)
    else:
        atk_type, atk_zone = bot_decide_attack(duel.get_attacker(), duel.get_defender(), duel.round_no)
        duel.atk_type = atk_type
        duel.atk_zone = atk_zone
        weapon = WEAPONS[duel.get_attacker().weapon]
        atk_name = weapon["attacks"][atk_type]["name"]
        await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra=f"⚔️ Босс выбрал: <b>{atk_name}</b>", timer_left=Config.TURN_TIMEOUT), get_zone_keyboard("defend"))
        start_duel_timer(duel, cb.from_user.id, "defender", bot)
        
    await cb.answer(f"Бой с {DUNGEON_BOSSES[bkey]['name']} начался!")


@router.callback_query(F.data == "arena:find")
async def cb_arena_find(cb: CallbackQuery, bot: Bot) -> None:
    """Поиск соперника."""
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
        fighter = duel.get_attacker()
        await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, timer_left=Config.TURN_TIMEOUT), get_attack_keyboard(fighter.weapon, duel.round_no, fighter))
        start_duel_timer(duel, cb.from_user.id, "attacker", bot)
    else:
        atk_id = duel.get_attacker_id()
        if atk_id < 0:
            atk_type, atk_zone = bot_decide_attack(duel.get_attacker(), duel.get_defender(), duel.round_no)
            duel.atk_type = atk_type
            duel.atk_zone = atk_zone
            weapon = WEAPONS[duel.get_attacker().weapon]
            atk_name = weapon["attacks"][atk_type]["name"]
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra=f"⚔️ Соперник выбрал: <b>{atk_name}</b>", timer_left=Config.TURN_TIMEOUT), get_zone_keyboard("defend"))
            start_duel_timer(duel, cb.from_user.id, "defender", bot)
        else:
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Соперник выбирает атаку…"), build_inline_keyboard([("🔄 Обновить", "duel:refresh")]))
    await cb.answer()


@router.callback_query(F.data == "arena:list")
async def cb_arena_list(cb: CallbackQuery) -> None:
    """Список соперников."""
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
        await safe_edit_message(cb, "Сейчас на твоей арене никого нет — жми «Найти соперника».", build_inline_keyboard([("🟪 🎲 Найти", "arena:find")], [("🟦 ⬅️ Назад", "arena:menu")]))
        return
        
    kb_rows = [[(f"🟦 {r['name'][:16]} · {r['wins']}{E_TROPHY}/{r['losses']}{E_SKULL}", f"duel:pick:{r['user_id']}"), ("🟩 👁", f"duel:profile:{r['user_id']}")] for r in rows]
    kb_rows.append([("🟦 ⬅️ Назад", "arena:menu")])
    
    await safe_edit_message(cb, f"{a['emoji']} <b>{a['name']}</b> — соперники:", build_inline_keyboard(*kb_rows))
    await cb.answer()


@router.callback_query(F.data == "arena:find_name")
async def cb_arena_find_name(cb: CallbackQuery, state: FSMContext) -> None:
    """Поиск по нику."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    await state.set_state(DuelFindState.waiting_for_target)
    await cb.message.answer("🔎 Отправь @username, ID или имя бойца.")
    await cb.answer()


@router.callback_query(F.data.regexp(r"^duel:pick:-?\d+$"))
async def cb_duel_pick(cb: CallbackQuery, bot: Bot) -> None:
    """Выбор соперника из списка."""
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
        fighter = duel.get_attacker()
        await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, timer_left=Config.TURN_TIMEOUT), get_attack_keyboard(fighter.weapon, duel.round_no, fighter))
        start_duel_timer(duel, cb.from_user.id, "attacker", bot)
    else:
        atk_id = duel.get_attacker_id()
        if atk_id < 0:
            atk_type, atk_zone = bot_decide_attack(duel.get_attacker(), duel.get_defender(), duel.round_no)
            duel.atk_type = atk_type
            duel.atk_zone = atk_zone
            weapon = WEAPONS[duel.get_attacker().weapon]
            atk_name = weapon["attacks"][atk_type]["name"]
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra=f"⚔️ Соперник выбрал: <b>{atk_name}</b>", timer_left=Config.TURN_TIMEOUT), get_zone_keyboard("defend"))
            start_duel_timer(duel, cb.from_user.id, "defender", bot)
        else:
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Соперник выбирает атаку…"), build_inline_keyboard([("🔄 Обновить", "duel:refresh")]))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^duel:profile:-?\d+$"))
async def cb_duel_profile(cb: CallbackQuery) -> None:
    """Просмотр профиля соперника."""
    tid = int(cb.data.split(":")[2])
    row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (tid,))
    if not row:
        await cb.answer("Игрок не найден.", show_alert=True)
        return
    await safe_edit_message(cb, generate_profile_text(row), build_inline_keyboard([("🟦 ⬅️ Назад", "arena:list")], [("🟥 ⚔️ Вызвать на бой", f"duel:pick:{tid}")]))
    await cb.answer()


@router.callback_query(F.data == "duel:myprofile")
async def cb_my_profile(cb: CallbackQuery) -> None:
    """Мой профиль."""
    row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not row:
        await cb.answer("Сначала /start", show_alert=True)
        return
    await safe_edit_message(cb, generate_profile_text(row), build_inline_keyboard([("🟦 ⬅️ Назад", "arena:menu")], [("🟪 🎒 Снаряжение", "gear:menu")]))
    await cb.answer()


@router.callback_query(F.data == "duel:again")
async def cb_duel_again(cb: CallbackQuery, bot: Bot) -> None:
    """Ещё раз."""
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
        fighter = duel.get_attacker()
        await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, timer_left=Config.TURN_TIMEOUT), get_attack_keyboard(fighter.weapon, duel.round_no, fighter))
        start_duel_timer(duel, cb.from_user.id, "attacker", bot)
    else:
        atk_id = duel.get_attacker_id()
        if atk_id < 0:
            atk_type, atk_zone = bot_decide_attack(duel.get_attacker(), duel.get_defender(), duel.round_no)
            duel.atk_type = atk_type
            duel.atk_zone = atk_zone
            weapon = WEAPONS[duel.get_attacker().weapon]
            atk_name = weapon["attacks"][atk_type]["name"]
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra=f"⚔️ Соперник выбрал: <b>{atk_name}</b>", timer_left=Config.TURN_TIMEOUT), get_zone_keyboard("defend"))
            start_duel_timer(duel, cb.from_user.id, "defender", bot)
        else:
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Соперник выбирает атаку…"), build_inline_keyboard([("🔄 Обновить", "duel:refresh")]))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^atk_type:(light|heavy|special)$"))
async def cb_atk_type(cb: CallbackQuery) -> None:
    """Выбор типа атаки."""
    duel = ACTIVE_DUELS.get(cb.from_user.id)
    if not duel or duel.finished or duel.get_state_for(cb.from_user.id) != "attacker":
        await cb.answer("Не твой ход", show_alert=True)
        return
        
    atk_type = cb.data.split(":")[1]
    fighter = duel.get_attacker()
    
    if not fighter.can_use_attack(atk_type, duel.round_no):
        await cb.answer("⏳ Эта атака ещё перезаряжается!", show_alert=True)
        return
        
    duel.atk_type = atk_type
    weapon = WEAPONS[fighter.weapon]
    atk_name = weapon["attacks"][atk_type]["name"]
    
    await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra=f"⚔️ <b>{atk_name}</b> — выбери зону удара", timer_left=Config.TURN_TIMEOUT), get_zone_keyboard("attack"))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^atk_disabled:\w+$"))
async def cb_atk_disabled(cb: CallbackQuery) -> None:
    """Атака на перезарядке."""
    await cb.answer("⏳ Перезарядка! Выбери другую атаку.", show_alert=True)


@router.callback_query(F.data == "atk_info")
async def cb_atk_info(cb: CallbackQuery) -> None:
    """Инфо об атаках."""
    duel = ACTIVE_DUELS.get(cb.from_user.id)
    if not duel:
        await cb.answer("Бой не найден", show_alert=True)
        return
        
    fighter = duel.get_attacker()
    weapon = WEAPONS[fighter.weapon]
    
    lines = [f"🟪 {weapon['emoji']} <b>{weapon['name']}</b>\n"]
    for atk_type in ["light", "heavy", "special"]:
        atk = weapon["attacks"][atk_type]
        cd = fighter.attack_cooldowns.get(atk_type, 0)
        cd_txt = f"⏳ {cd - duel.round_no} раундов" if cd > duel.round_no else "✅ готово"
        lines.append(f"<b>{atk['name']}</b>\n{atk['desc']}\n{cd_txt}\n")
        
    lines.append("Выбери атаку:")
    await safe_edit_message(cb, "\n".join(lines), get_attack_keyboard(fighter.weapon, duel.round_no, fighter))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^duel:atk:(head|torso|arms|legs)$"))
async def cb_duel_attack(cb: CallbackQuery, bot: Bot) -> None:
    """Выбор зоны атаки."""
    duel = ACTIVE_DUELS.get(cb.from_user.id)
    if not duel or duel.finished or duel.get_state_for(cb.from_user.id) != "attacker":
        await cb.answer("Бой не найден, завершён или не твой ход.", show_alert=True)
        return
        
    if not duel.atk_type:
        await cb.answer("Сначала выбери тип атаки!", show_alert=True)
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
            def_zone = bot_pick_defend_zone(attacker, bot_f)
            duel.bot_last_block_round = duel.round_no
            duel.bot_block_streak += 1
            duel.log.append(f"🛡 {bot_f.name} встаёт в защиту")
        else:
            def_zone = None
            duel.bot_block_streak = 0
            
        await process_duel_round(duel, bot, cb=cb, atk_type=duel.atk_type, atk_zone=atk_zone, def_zone=def_zone)
    else:
        weapon = WEAPONS[duel.get_attacker().weapon]
        atk_name = weapon["attacks"][duel.atk_type]["name"]
        await bot.send_message(
            def_id,
            generate_duel_status_text(duel, def_id, extra=f"⚔️ {duel.get_attacker().name} атакует: <b>{atk_name}</b>", timer_left=Config.TURN_TIMEOUT),
            reply_markup=get_zone_keyboard("defend")
        )
        start_duel_timer(duel, def_id, "defender", bot)
        await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Ждём защиту соперника…"), build_inline_keyboard([("🔄 Обновить", "duel:refresh")]))
    await cb.answer("Удар выбран.")


@router.callback_query(F.data.regexp(r"^duel:def:(head|torso|arms|legs)$"))
async def cb_duel_defend(cb: CallbackQuery, bot: Bot) -> None:
    """Выбор зоны защиты."""
    duel = ACTIVE_DUELS.get(cb.from_user.id)
    if not duel or duel.finished or duel.get_state_for(cb.from_user.id) != "defender":
        await cb.answer("Бой не найден, завершён или не твой ход.", show_alert=True)
        return
        
    if not duel.atk_zone or not duel.atk_type:
        await cb.answer("Атакующий ещё не выбрал цель.", show_alert=True)
        return
        
    stop_duel_timer(duel)
    def_zone = cb.data.split(":")[2]
    await process_duel_round(duel, bot, cb=cb, atk_type=duel.atk_type, atk_zone=duel.atk_zone, def_zone=def_zone)


@router.callback_query(F.data == "duel:refresh")
async def cb_duel_refresh(cb: CallbackQuery) -> None:
    """Обновление статуса боя."""
    duel = ACTIVE_DUELS.get(cb.from_user.id)
    if not duel or duel.finished:
        await cb.answer("Бой не найден или завершён.", show_alert=True)
        return
        
    role = duel.get_state_for(cb.from_user.id)
    if role == "attacker":
        if not duel.atk_type:
            fighter = duel.get_attacker()
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="🎯 Выбери тип атаки.", timer_left=max(0, int(round(duel.timer_deadline - time.time())))), get_attack_keyboard(fighter.weapon, duel.round_no, fighter))
        else:
            weapon = WEAPONS[duel.get_attacker().weapon]
            atk_name = weapon["attacks"][duel.atk_type]["name"]
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra=f"⚔️ <b>{atk_name}</b> — выбери зону.", timer_left=max(0, int(round(duel.timer_deadline - time.time())))), get_zone_keyboard("attack"))
    else:
        if not duel.atk_zone:
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra="⏳ Соперник ещё выбирает атаку…"), build_inline_keyboard([("🔄 Обновить", "duel:refresh")]))
        else:
            weapon = WEAPONS[duel.get_attacker().weapon]
            atk_name = weapon["attacks"][duel.atk_type]["name"]
            await safe_edit_message(cb, generate_duel_status_text(duel, cb.from_user.id, extra=f"{E_SHIELD} Соперник атакует: <b>{atk_name}</b>. Выбери зону.", timer_left=max(0, int(round(duel.timer_deadline - time.time())))), get_zone_keyboard("defend"))
    await cb.answer("Обновлено")


# ==============================================================================
# 30. МЕНЮ КНОПКИ (ЛС) И GEAR
# ==============================================================================

def generate_arena_menu_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует главное меню арены."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
        
    key = determine_arena(p["wins"])
    a = ARENAS[key]
    
    text = (
        f"╔══════════════════════════╗\n      ⚔️ <b>АРЕНА ДУЭЛЯНТОВ</b>\n╚══════════════════════════╝\n\n"
        f"🟡 {E_TROPHY} Победы: <b>{p['wins']}</b>  ·  {E_SKULL} Поражения: {p['losses']}\n"
        f"🟢 {Config.CURRENCY_EMOJI} Ареники: <b>{p['currency']}</b>\n🔵 📍 {a['emoji']} <b>{a['name']}</b>\n\n"
        f"🟥 Бронза — 0–9 побед  ·  <b>{ARENAS['bronze']['prize']}{Config.CURRENCY_EMOJI}</b>\n"
        f"🟧 Серебро — 10–29 побед  ·  <b>{ARENAS['silver']['prize']}{Config.CURRENCY_EMOJI}</b>\n"
        f"🟨 Золото — 30+ побед  ·  <b>{ARENAS['gold']['prize']}{Config.CURRENCY_EMOJI}</b>\n\n"
        "<b>📜 Правила боя:</b>\n"
        f"• Атакующий выбирает атаку и зону — <b>{Config.TURN_TIMEOUT} сек</b>\n"
        f"• Защищающийся — зону защиты — <b>{Config.TURN_TIMEOUT} сек</b>\n"
        "• Совпало → блок. Иначе урон = оружие − броня зоны\n"
        "• Бой идёт <b>до 0 HP</b> у одного из бойцов\n"
        "• <i>Поражение: только −1 🏆, без награды</i>"
    )
    
    kb = build_inline_keyboard(
        [("🟪 🎲 Найти соперника", "arena:find"), ("🟥 👹 Боссы", "arena:bosses")],
        [("🟦 📋 Список соперников", "arena:list"), ("🟩 🏆 Топ арен", "top:cur")],
        [("🟫 👤 Мой профиль", "duel:myprofile")]
    )
    return text, kb


def generate_bosses_menu_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует экран выбора босса."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
        
    lines = ["╔══════════════════════════╗\n      🟥 <b>БОССЫ АРЕНЫ</b>\n╚══════════════════════════╝\n"]
    rows = []
    
    for bkey, b in DUNGEON_BOSSES.items():
        locked = p["wins"] < b["min_wins"]
        lock_text = f"🔒 нужен {b['min_wins']} {E_TROPHY}" if locked else f"награда ×{b['reward_mult']}"
        lines.append(f"{b['name']}\n  ❤️ HP {b['hp']} · ⚔️ {WEAPONS[b['weapon']]['name']}\n  {b['desc']}\n  → {lock_text}\n")
        rows.append([(b["name"] if not locked else f"{b['name']} 🔒", f"arena:boss:{bkey}")])
        
    rows.append([("🟦 ⬅️ Назад", "arena:menu")])
    return "\n".join(lines), build_inline_keyboard(*rows)


@router.message(F.text == "🟥 ⚔️ Арена")
async def menu_arena(m: Message, state: FSMContext) -> None:
    """Кнопка меню Арена."""
    await state.clear()
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала отправь /start")
        return
    arena = ARENAS[determine_arena(p["wins"])]
    text = (
        f"╔══════════════════════════╗\n      ⚔️ <b>АРЕНА</b>\n╚══════════════════════════╝\n\n"
        f"🟡 {E_TROPHY} Победы: <b>{p['wins']}</b>  ·  {E_SKULL} Поражения: {p['losses']}\n"
        f"🟢 {Config.CURRENCY_EMOJI} Ареники: <b>{p['currency']}</b>\n🔵 📍 {arena['emoji']} <b>{arena['name']}</b>"
    )
    kb = build_inline_keyboard(
        [("🟪 🎲 Найти соперника", "arena:find"), ("🟥 👹 Боссы", "arena:bosses")],
        [("🟦 📋 Список", "arena:list"), ("🟩 🏆 Топ", "top:cur")],
        [("🟫 👤 Профиль", "duel:myprofile")]
    )
    await m.answer(text, reply_markup=kb)


@router.message(F.text == "🟪 🎰 Казино")
async def menu_casino(m: Message) -> None:
    """Кнопка меню Казино."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала отправь /start")
        return
    text = (
        f"╔══════════════════════════╗\n   🟪 {E_SLOT} <b>КАЗИНО</b>\n╚══════════════════════════╝\n\n"
        f"🟢 Баланс: <b>{p['currency']}</b> {Config.CURRENCY_EMOJI}\n\n"
        f"<b>Команды в чате:</b>\n"
        f"🟥 <code>сл [сумма]</code> — слоты\n"
        f"🟧 <code>кост [сумма]</code> — кости\n"
        f"🟨 <code>мон [сумма] [о/р]</code> — монетка\n"
        f"🟩 <code>рул [сумма] [к/ч/з]</code> — рулетка\n"
        f"🟦 <code>больше [сумма]</code> / <code>меньше [сумма]</code>"
    )
    await m.answer(text)


@router.message(F.text == "🟦 🎒 Снаряжение")
async def menu_gear(m: Message) -> None:
    """Кнопка меню Снаряжение."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала отправь /start")
        return
    weapon = WEAPONS.get(p["weapon"], WEAPONS["fists"])
    slots = get_player_armor_slots(p)
    lines = [
        f"🟪 <b>{esc(p['name'])}</b>", "",
        f"🟢 {Config.CURRENCY_EMOJI} Ареники: <b>{p['currency']}</b>", "",
        f"<b>🟥 ⚔️ Оружие:</b>", f"{weapon['emoji']} {weapon['name']} — урон {weapon['dmg']}", "",
        "<b>🟦 🛡 Броня:</b>"
    ]
    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"  {ZONE_INFO[slot]['emoji']} {item['name']} (защита {item['df']})")
    kb = build_inline_keyboard([("🟥 ⚔️ Оружие", "gear:w"), ("🟦 🛡 Броня", "gear:armor_menu")])
    await m.answer("\n".join(lines), reply_markup=kb)


@router.message(F.text == "🟩 🏆 Топ")
async def menu_top(m: Message) -> None:
    """Кнопка меню Топ."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала отправь /start")
        return
    arena = ARENAS[determine_arena(p["wins"])]
    rows = db.fetch_all("""
        SELECT user_id, name, wins, losses FROM players
        WHERE is_bot=0 AND banned=0 AND wins BETWEEN ? AND ?
        ORDER BY wins DESC, losses ASC LIMIT 10
    """, (arena["min_wins"], arena["max_wins"]))
    
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"🟩 <b>{arena['name']} — топ</b>\n"]
    
    if not rows:
        lines.append("<i>Пока никого нет на этой арене.</i>")
        
    for i, r in enumerate(rows):
        mark = medals[i] if i < 3 else f"{i+1}."
        you = " ← ты" if r["user_id"] == m.from_user.id else ""
        lines.append(f"{mark} <b>{esc(r['name'])}</b> {r['wins']}{E_TROPHY}/{r['losses']}{E_SKULL}{you}")
        
    kb = build_inline_keyboard([("🟥 Бронза", "top:bronze"), ("🟧 Серебро", "top:silver"), ("🟨 Золото", "top:gold")])
    await m.answer("\n".join(lines), reply_markup=kb)


@router.message(F.text == "🟧 👹 Босс")
async def menu_boss(m: Message) -> None:
    """Кнопка меню Босс."""
    state = get_chat_boss_state()
    if not state or not state["active"]:
        await m.answer(f"{E_WARN} Нет активного босса\n\nВ чате используй <code>босс</code> для атаки или <code>босс инфо</code>")
        return
        
    boss = next((b for b in CHAT_BOSSES if b["key"] == state["boss_key"]), None)
    if not boss:
        return
        
    damages = db.fetch_all("SELECT user_id, damage FROM event_damage WHERE event_type='boss' AND event_key=? ORDER BY damage DESC LIMIT 3", (state["boss_key"],))
    ratio = state["current_hp"] / state["max_hp"]
    bar = "🟩" * int(15 * ratio) + "⬛" * (15 - int(15 * ratio))
    lines = [
        f"🟥 <b>{boss['name']}</b>\n",
        f"❤️ {state['current_hp']}/{state['max_hp']} {bar}\n",
        f"💰 Пул: <b>{state['reward_pool']}</b>{Config.CURRENCY_EMOJI}\n",
        f"\n💥 Используй <code>босс</code> в чате!"
    ]
    
    if damages:
        lines.append("\n<b>Топ урона:</b>")
        for d in damages:
            p_row = db.fetch_one("SELECT name FROM players WHERE user_id=?", (d["user_id"],))
            lines.append(f"• {esc(p_row['name'] if p_row else '?')} — {d['damage']}")
            
    await m.answer("\n".join(lines))


@router.message(F.text == "🟨 🏰 Осада")
async def menu_siege(m: Message) -> None:
    """Кнопка меню Осада."""
    state = get_siege_state()
    if not state or not state["active"]:
        await m.answer(f"{E_WARN} Осада не активна\n\nВ чате используй <code>осада</code> для атаки")
        return
        
    wave = SIEGE_WAVES[f"wave{state['current_wave']}"]
    await m.answer(
        f"🟨 <b>ОСАДА КРЕПОСТИ</b>\n\n"
        f"🌊 Волна {state['current_wave']}/5: {wave['name']}\n"
        f"👹 {wave['enemies']} врагов\n"
        f"💰 Награда: {wave['reward']}{Config.CURRENCY_EMOJI}\n\n"
        f"💥 Используй <code>осада</code> в чате"
    )


@router.callback_query(F.data == "gear:menu")
async def cb_gear_menu(cb: CallbackQuery) -> None:
    """Меню снаряжения."""
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    await safe_edit_message(cb, *generate_gear_screen(cb.from_user.id))
    await cb.answer()


def generate_gear_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Генерирует экран управления снаряжением."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None
        
    w = WEAPONS[p["weapon"]]
    f = create_fighter_from_db(p)
    slots = get_player_armor_slots(p)
    
    lines = [
        f"🟪 <b>{esc(p['name'])}</b>", "",
        f"🟡 {E_TROPHY} Победы: <b>{p['wins']}</b>  ·  {E_SKULL} Поражения: {p['losses']}",
        f"🟢 {Config.CURRENCY_EMOJI} Ареники: <b>{p['currency']}</b>",
        f"🔵 📍 {ARENAS[determine_arena(p['wins'])]['emoji']} {ARENAS[determine_arena(p['wins'])]['name']}", "",
        f"🔴 ❤️ HP: <b>{f.max_hp}</b>   ⚔️ Атака: <b>{f.weapon_dmg}</b>", "",
        "<b>🟥 ⚔️ Оружие:</b>",
        f"  {w['emoji']} {w['name']} — <i>{w['spec']}</i> (урон <b>{w['dmg']}</b>, шанс {w['chance']}%)", "",
        "<b>🟦 🛡 Броня по слотам:</b>"
    ]
    
    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"  {ZONE_INFO[slot]['emoji']} {ZONE_INFO[slot]['name']}: {item['emoji']} <b>{item['name']}</b> (защита {item['df']})")
        
    kb = build_inline_keyboard(
        [("🟥 ⚔️ Оружие", "gear:w"), ("🟦 🛡 Броня", "gear:armor_menu")],
        [("🟫 👤 Мой профиль", "duel:myprofile")]
    )
    return "\n".join(lines), kb


@router.callback_query(F.data == "gear:w")
async def cb_gear_weapon(cb: CallbackQuery) -> None:
    """Список оружия."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p:
        await cb.answer("Сначала /start", show_alert=True)
        return
        
    owned = set((p["weapons_owned"] or "").split(","))
    lines = [f"🟥 <b>Оружие</b> · {Config.CURRENCY_EMOJI} {p['currency']}\n"]
    rows = []
    
    for key, w in WEAPONS.items():
        lines.append(f"🟪 {w['emoji']} <b>{w['name']}</b> — {w['dmg']}\n   {w['spec']}")
        if key == p["weapon"]:
            label = "✅"
        elif key in owned:
            label = "🎒"
        else:
            label = f"{w['price']}{Config.CURRENCY_EMOJI}"
        rows.append([(f"🟦 {w['emoji']} {w['name']} · {label}", f"buy:w:{key}")])
        
    rows.append([("🟩 ⬅️ Назад", "gear:menu")])
    await safe_edit_message(cb, "\n".join(lines), build_inline_keyboard(*rows))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^buy:w:(\w+)$"))
async def cb_buy_weapon(cb: CallbackQuery) -> None:
    """Покупка/надевание оружия."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p:
        await cb.answer("Сначала /start", show_alert=True)
        return
        
    key = cb.data.split(":")[2]
    w = WEAPONS.get(key)
    if not w:
        return
        
    owned = set((p["weapons_owned"] or "").split(","))
    if key in owned:
        db.execute("UPDATE players SET weapon=? WHERE user_id=?", (key, cb.from_user.id))
        toast = f"✅ {w['name']} надето"
    elif p["currency"] >= w["price"]:
        db.execute("UPDATE players SET currency=currency-?, weapons_owned=?, weapon=? WHERE user_id=?",
                   (w["price"], ",".join(owned | {key}), key, cb.from_user.id))
        toast = f"🟢 {w['name']} куплено"
    else:
        await cb.answer(f"Нужно {w['price']}{Config.CURRENCY_EMOJI}", show_alert=True)
        return
        
    await cb_gear_weapon(cb)
    await cb.answer(toast)


@router.callback_query(F.data == "gear:armor_menu")
async def cb_armor_menu(cb: CallbackQuery) -> None:
    """Меню слотов брони."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p:
        await cb.answer("Сначала /start", show_alert=True)
        return
        
    slots = get_player_armor_slots(p)
    lines = [f"🟦 <b>Броня</b> · {Config.CURRENCY_EMOJI} {p['currency']}\n"]
    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"🟪 {ZONE_INFO[slot]['emoji']} <b>{item['name']}</b> (защита {item['df']})")
        
    await safe_edit_message(cb, "\n".join(lines), build_inline_keyboard(
        [("🟥 🧠 Голова", "gear:head"), ("🟧 🫀 Торс", "gear:torso")],
        [("🟨 💪 Руки", "gear:arms"), ("🟩 🦵 Ноги", "gear:legs")],
        [("🟦 ⬅️ Назад", "gear:menu")]))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^gear:(head|torso|arms|legs)$"))
async def cb_armor_slot(cb: CallbackQuery) -> None:
    """Список брони для слота."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p:
        await cb.answer("Сначала /start", show_alert=True)
        return
        
    slot = cb.data.split(":")[1]
    slots = get_player_armor_slots(p)
    equipped = slots.get(slot, f"{slot}_none")
    owned = set((p["armors_owned"] or "").split(","))
    
    lines = [f"🟦 <b>{ZONE_INFO[slot]['name']}</b> · {Config.CURRENCY_EMOJI} {p['currency']}\n"]
    rows = []
    
    for item in ARMOR_DATA[slot]:
        key = item["key"]
        lines.append(f"🟪 {item['emoji']} <b>{item['name']}</b> защ {item['df']} HP +{item['hp']}\n   {item['desc']}")
        if key == equipped:
            label = "✅"
        elif key in owned:
            label = "🎒"
        else:
            label = f"{item['price']}{Config.CURRENCY_EMOJI}"
        rows.append([(f"🟩 {item['emoji']} {label}", f"buy:a:{slot}:{key}")])
        
    rows.append([("🟦 ⬅️ К слотам", "gear:armor_menu")])
    await safe_edit_message(cb, "\n".join(lines), build_inline_keyboard(*rows))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^buy:a:(head|torso|arms|legs):(\w+)$"))
async def cb_buy_armor(cb: CallbackQuery) -> None:
    """Покупка/надевание брони."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p:
        await cb.answer("Сначала /start", show_alert=True)
        return
        
    _, slot, key = cb.data.split(":")
    item = get_armor_item_by_key(key)
    if not item:
        return
        
    owned = set((p["armors_owned"] or "").split(","))
    col = f"armor_{slot}"
    
    if key in owned:
        db.execute(f"UPDATE players SET {col}=? WHERE user_id=?", (key, cb.from_user.id))
        toast = f"✅ {item['name']} надето"
    elif p["currency"] >= item["price"]:
        db.execute(f"UPDATE players SET currency=currency-?, armors_owned=?, {col}=? WHERE user_id=?",
                   (item["price"], ",".join(owned | {key}), key, cb.from_user.id))
        toast = f"🟢 {item['name']} куплено"
    else:
        await cb.answer(f"Нужно {item['price']}{Config.CURRENCY_EMOJI}", show_alert=True)
        return
        
    await cb_armor_slot(cb)
    await cb.answer(toast)


@router.callback_query(F.data.regexp(r"^top:(cur|bronze|silver|gold)$"))
async def cb_top(cb: CallbackQuery) -> None:
    """Топ арен."""
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not p:
        await cb.answer("Сначала /start", show_alert=True)
        return
        
    key = cb.data.split(":")[1]
    if key == "cur":
        key = determine_arena(p["wins"])
        
    arena = ARENAS[key]
    rows = db.fetch_all("""
        SELECT user_id, name, wins, losses FROM players
        WHERE is_bot=0 AND banned=0 AND wins BETWEEN ? AND ?
        ORDER BY wins DESC LIMIT 15
    """, (arena["min_wins"], arena["max_wins"]))
    
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"🟩 <b>{arena['name']}</b>\n"]
    
    if not rows:
        lines.append("<i>Никого нет</i>")
        
    for i, r in enumerate(rows):
        mark = medals[i] if i < 3 else f"{i+1}."
        you = " ← ты" if r["user_id"] == cb.from_user.id else ""
        lines.append(f"{mark} <b>{esc(r['name'])}</b> {r['wins']}{E_TROPHY}/{r['losses']}{E_SKULL}{you}")
        
    await safe_edit_message(cb, "\n".join(lines), build_inline_keyboard(
        [("🟥 Бронза", "top:bronze"), ("🟧 Серебро", "top:silver"), ("🟨 Золото", "top:gold")],
        [("🟦 ⬅️ Назад", "arena:menu")]))
    await cb.answer()


# ==============================================================================
# 31. FALLBACK И ЗАПУСК
# ==============================================================================

@router.message(DuelFindState.waiting_for_target, F.text)
async def duel_find_target_handler(m: Message, state: FSMContext, bot: Bot) -> None:
    """Обработчик поиска цели по нику."""
    if m.chat.type != "private":
        await state.clear()
        return
        
    await state.clear()
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start.")
        return
        
    key = m.text.strip().lstrip("@")
    row = None
    
    if key.isdigit():
        row = db.fetch_one("SELECT user_id FROM players WHERE user_id=? AND banned=0", (int(key),))
        
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


@router.my_chat_member(F.new_chat_member.status == ChatMemberStatus.MEMBER, F.old_chat_member.status == ChatMemberStatus.LEFT)
async def on_bot_added(event: ChatMemberUpdated, bot: Bot) -> None:
    """
    Авто-запуск ивента при добавлении бота в группу.
    С шансом 40% запускает босса или осаду.
    """
    if random.random() < Config.GROUP_ADD_EVENT_CHANCE:
        event_type = random.choice(["boss", "siege"])
        chat_id = event.chat.id
        
        if event_type == "boss":
            boss = spawn_global_event(chat_id, "boss")
            if boss:
                try:
                    await bot.send_message(
                        chat_id,
                        f"🟥 <b>ВНИМАНИЕ!</b>\n\n"
                        f"{boss['name']} явился в эту группу!\n"
                        f"❤️ HP: <b>{boss['hp']}</b>\n"
                        f"💰 Пул: <b>{boss['reward_pool']}</b>{Config.CURRENCY_EMOJI}\n\n"
                        f"💥 Пиши <code>босс</code> для атаки!",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
        else:
            wave = spawn_global_event(chat_id, "siege")
            if wave:
                try:
                    await bot.send_message(
                        chat_id,
                        f"🟨 <b>ОСАДА НАЧАЛАСЬ!</b>\n\n"
                        f"🌊 Волна 1: {wave['name']}\n"
                        f"👹 {wave['enemies']} врагов\n"
                        f"💰 Награда: <b>{wave['reward']}</b>{Config.CURRENCY_EMOJI}\n\n"
                        f"💥 Пиши <code>осада</code> для атаки!",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass


@router.message()
async def fallback_handler(m: Message) -> None:
    """Обработчик fallback для всех остальных сообщений."""
    if not m.from_user:
        return
        
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        if m.chat.type == "private":
            await m.answer("Отправь /start, чтобы создать бойца ⚔️")
        return
        
    if is_user_banned(m.from_user.id):
        await m.answer("🔴 Доступ закрыт.")
        return
        
    if m.chat.type == "private":
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🟥 ⚔️ Арена"), KeyboardButton(text="🟪 🎰 Казино")],
                [KeyboardButton(text="🟦 🎒 Снаряжение"), KeyboardButton(text="🟩 🏆 Топ")],
                [KeyboardButton(text="🟧 👹 Босс"), KeyboardButton(text="🟨 🏰 Осада")],
            ],
            resize_keyboard=True,
        )
        p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
        await m.answer(f"🟢 {p['currency']} {Config.CURRENCY_EMOJI} · 🟡 {p['wins']} {E_TROPHY}\n\n<code>help</code> для команд", reply_markup=kb)
    else:
        await m.answer(f"💡 В чате: <code>help</code> для списка команд\n"
                       f"Ответь на сообщение + команда или <code>команда @user</code>")


async def boss_scheduler(bot: Bot) -> None:
    """Фоновая задача для спавна боссов по расписанию."""
    while True:
        try:
            await asyncio.sleep(Config.BOSS_EVENT_INTERVAL)
            state = get_chat_boss_state()
            if not state or not state["active"]:
                last_spawn = state["started_at"] if state else 0
                if time.time() - last_spawn > Config.BOSS_EVENT_INTERVAL:
                    # Авто-спавн можно добавить здесь если нужно
                    logging.info("Boss scheduler: interval passed, no auto-spawn configured")
        except Exception as e:
            logging.error(f"Boss scheduler error: {e}")
            await asyncio.sleep(60)


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
        BotCommand(command="admin", description="Админ-панель (только для админа)"),
        BotCommand(command="stats", description="Статистика бота (только для админа)"),
    ])
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запуск планировщика глобальных ивентов
    asyncio.create_task(boss_scheduler(bot))
    
    logging.info("✅ Bot successfully started and polling!")
    
    try:
        await dp.start_polling(bot)
    finally:
        db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
