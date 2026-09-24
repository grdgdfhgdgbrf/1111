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


class Config:
    BOT_TOKEN = "8996813076:AAGq74gyRRW5fMxvHaIE190_B-tmzXk8aNA"
    ADMIN_ID =  "5356400377"
    DB_PATH: str = os.getenv("DB_PATH", "arena_ultimate.db")
    START_CRYSTALS: int = 500
    TURN_TIMEOUT: int = 45
    RP_COOLDOWN: int = 5
    TRANSFER_TAX: float = 0.05
    MIN_TRANSFER: int = 10
    MAX_TRANSFER: int = 100000
    CASINO_MIN_BET: int = 10
    CASINO_MAX_BET: int = 50000
    CASINO_DAILY_LIMIT: int = 100000
    CASINO_BETS: List[int] = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
    BOT_GENERATION_COUNT: int = 50
    BOT_WIN_DISTRIBUTION: Dict[str, float] = {
        "bronze": 0.5,
        "silver": 0.35,
        "gold": 0.15,
    }
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
    TOP_SHOW_SELF_RANK: bool = True
    LOG_LEVEL: int = logging.INFO
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


BASE_HP: int = 150
MIN_NAME_LENGTH: int = 2
MAX_NAME_LENGTH: int = 16
MAX_OWNED_WEAPONS: int = 10
MAX_OWNED_ARMORS: int = 30
DUEL_LOG_LIMIT: int = 10
DUEL_LOG_DISPLAY_LIMIT: int = 5
TELEGRAM_MAX_TEXT_LENGTH: int = 4096
BROADCAST_DELAY: float = 0.05
BOT_NAME_GENERATION_ATTEMPTS: int = 300
MAX_NOTIFICATIONS_PER_USER: int = 15


PREMIUM_EMOJI_IDS: Dict[str, str] = {
    "fire": "5368324170671202286",
    "sword": "5368324170671202287",
    "shield": "5368324170671202292",
    "heart": "5368324170671202293",
    "skull": "5368324170671202291",
    "trophy": "5368324170671202290",
    "crystal": "5368324170671202310",
    "coin": "5368324170671202288",
    "slot": "5368324170671202294",
    "dice": "5368324170671202295",
    "gift": "5368324170671202300",
    "promo": "5368324170671202301",
    "boss": "5368324170671202296",
    "glove": "5368324170671202297",
    "star": "5368324170671202298",
    "magic": "5368324170671202299",
    "lightning": "5368324170671202311",
    "meteor": "5368324170671202312",
    "zone_head": "5368324170671202320",
    "zone_torso": "5368324170671202321",
    "zone_arms": "5368324170671202322",
    "zone_legs": "5368324170671202323",
    "warning": "5368324170671202330",
    "success": "5368324170671202331",
    "error": "5368324170671202332",
    "info": "5368324170671202333",
    "crown": "5368324170671202334",
    "diamond": "5368324170671202335",
    "gem": "5368324170671202336",
    "scroll": "5368324170671202337",
    "book": "5368324170671202338",
    "potion": "5368324170671202339",
}


def get_premium_emoji(key: str, fallback: str) -> str:
    eid = PREMIUM_EMOJI_IDS.get(key)
    return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>' if eid else fallback


E_FIRE = get_premium_emoji("fire", "🔥")
E_SWORD = get_premium_emoji("sword", "⚔️")
E_SHIELD = get_premium_emoji("shield", "🛡")
E_HEART = get_premium_emoji("heart", "❤️")
E_SKULL = get_premium_emoji("skull", "💀")
E_TROPHY = get_premium_emoji("trophy", "🏆")
E_CRYSTAL = get_premium_emoji("crystal", "💎")
E_COIN = get_premium_emoji("coin", "🪙")
E_SLOT = get_premium_emoji("slot", "🎰")
E_DICE = get_premium_emoji("dice", "🎲")
E_GIFT = get_premium_emoji("gift", "🎁")
E_PROMO = get_premium_emoji("promo", "🎟")
E_BOSS = get_premium_emoji("boss", "👹")
E_GLOVE = get_premium_emoji("glove", "🧤")
E_STAR = get_premium_emoji("star", "⭐")
E_MAGIC = get_premium_emoji("magic", "✨")
E_LIGHTNING = get_premium_emoji("lightning", "⚡")
E_METEOR = get_premium_emoji("meteor", "☄️")
E_ZONE_HEAD = get_premium_emoji("zone_head", "🧠")
E_ZONE_TORSO = get_premium_emoji("zone_torso", "🫀")
E_ZONE_ARMS = get_premium_emoji("zone_arms", "💪")
E_ZONE_LEGS = get_premium_emoji("zone_legs", "🦵")
E_WARNING = get_premium_emoji("warning", "⚠️")
E_SUCCESS = get_premium_emoji("success", "✅")
E_ERROR = get_premium_emoji("error", "❌")
E_INFO = get_premium_emoji("info", "ℹ️")
E_CROWN = get_premium_emoji("crown", "👑")
E_DIAMOND = get_premium_emoji("diamond", "💠")
E_GEM = get_premium_emoji("gem", "💎")
E_SCROLL = get_premium_emoji("scroll", "📜")
E_BOOK = get_premium_emoji("book", "📖")
E_POTION = get_premium_emoji("potion", "🧪")


ZONES: List[str] = ["head", "torso", "arms", "legs"]

ZONE_INFO: Dict[str, Dict[str, Any]] = {
    "head": {
        "name": "Голова",
        "emoji": E_ZONE_HEAD,
        "mult": 1.5,
        "desc": "Высокий урон, но сложно попасть. Критические попадания!",
        "block_chance_bonus": 0.1,
    },
    "torso": {
        "name": "Торс",
        "emoji": E_ZONE_TORSO,
        "mult": 1.0,
        "desc": "Средний урон, стандартная цель. Базовый вариант.",
        "block_chance_bonus": 0.0,
    },
    "arms": {
        "name": "Руки",
        "emoji": E_ZONE_ARMS,
        "mult": 0.8,
        "desc": "Низкий урон, но высокая точность попадания.",
        "block_chance_bonus": -0.1,
    },
    "legs": {
        "name": "Ноги",
        "emoji": E_ZONE_LEGS,
        "mult": 0.9,
        "desc": "Средний урон, шанс замедлить противника.",
        "block_chance_bonus": -0.05,
    },
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
        "emoji": "👊",
        "name": "Кулаки",
        "base_dmg": 10,
        "price": 0,
        "description": "Базовое оружие новичка. Быстрые, но слабые удары.",
        "tier": "common",
        "variants": [
            AttackVariant(
                name="Джеб",
                description="Быстрый удар, низкий шанс промаха. Идеально для разведки",
                damage_mult=0.8,
                armor_penetration=0.0,
                cooldown_rounds=0,
                effect=None,
            ),
            AttackVariant(
                name="Серия ударов",
                description="3 быстрых удара по 50% урона каждый. Пробивает слабую броню",
                damage_mult=1.5,
                armor_penetration=0.0,
                cooldown_rounds=2,
                effect="triple",
            ),
            AttackVariant(
                name="Апперкот",
                description="Мощный восходящий удар. Оглушает при попадании в голову",
                damage_mult=1.2,
                armor_penetration=0.1,
                cooldown_rounds=3,
                effect="stun",
            ),
        ],
    },
    "dagger": {
        "emoji": "🗡",
        "name": "Кинжал",
        "base_dmg": 14,
        "price": 200,
        "description": "Быстрое оружие убийцы. Высокий шанс критических ударов.",
        "tier": "uncommon",
        "variants": [
            AttackVariant(
                name="Укол",
                description="Точный удар в уязвимое место. Пробивает до 20% брони",
                damage_mult=1.0,
                armor_penetration=0.2,
                cooldown_rounds=0,
                effect=None,
            ),
            AttackVariant(
                name="Рассечение",
                description="Глубокий порез, вызывающий кровотечение на 3 раунда",
                damage_mult=1.1,
                armor_penetration=0.1,
                cooldown_rounds=2,
                effect="bleed",
            ),
            AttackVariant(
                name="Тысяча порезов",
                description="3 быстрых удара, игнорирующих 30% брони противника",
                damage_mult=1.4,
                armor_penetration=0.3,
                cooldown_rounds=3,
                effect="triple",
            ),
        ],
    },
    "sword": {
        "emoji": E_SWORD,
        "name": "Меч",
        "base_dmg": 20,
        "price": 500,
        "description": "Классическое оружие воина. Сбалансированный урон и защита.",
        "tier": "rare",
        "variants": [
            AttackVariant(
                name="Размах",
                description="Стандартная атака по площади. Надёжный и проверенный прием",
                damage_mult=1.0,
                armor_penetration=0.0,
                cooldown_rounds=0,
                effect=None,
            ),
            AttackVariant(
                name="Пронзающий выпад",
                description="Мощный выпад, игнорирующий 50% защиты цели",
                damage_mult=1.2,
                armor_penetration=0.5,
                cooldown_rounds=2,
                effect="pierce",
            ),
            AttackVariant(
                name="Казнь",
                description="Двойной урон, но легко блокируется. Для добивания",
                damage_mult=2.0,
                armor_penetration=0.0,
                cooldown_rounds=4,
                effect="exec",
            ),
        ],
    },
    "axe": {
        "emoji": "🪓",
        "name": "Топор",
        "base_dmg": 26,
        "price": 800,
        "description": "Тяжёлое оружие варвара. Огромный урон, но медленные атаки.",
        "tier": "rare",
        "variants": [
            AttackVariant(
                name="Рубящий удар",
                description="Тяжелая, но надежная атака. Пробивает 10% брони",
                damage_mult=1.0,
                armor_penetration=0.1,
                cooldown_rounds=0,
                effect=None,
            ),
            AttackVariant(
                name="Кровопускание",
                description="Глубокая рана, вызывающая сильное кровотечение на 3 раунда",
                damage_mult=1.1,
                armor_penetration=0.0,
                cooldown_rounds=3,
                effect="bleed",
            ),
            AttackVariant(
                name="Сокрушение",
                description="Огромный урон, но очень долгая перезарядка (4 раунда)",
                damage_mult=1.8,
                armor_penetration=0.2,
                cooldown_rounds=4,
                effect=None,
            ),
        ],
    },
    "bow": {
        "emoji": "🏹",
        "name": "Лук",
        "base_dmg": 32,
        "price": 1200,
        "description": "Дальнобойное оружие охотника. Высокий урон на дистанции.",
        "tier": "epic",
        "variants": [
            AttackVariant(
                name="Прицельный выстрел",
                description="Стандартная атака из лука. Пробивает 30% брони",
                damage_mult=1.0,
                armor_penetration=0.3,
                cooldown_rounds=0,
                effect=None,
            ),
            AttackVariant(
                name="Залп",
                description="2 быстрых выстрела с шансом критического урона",
                damage_mult=1.6,
                armor_penetration=0.2,
                cooldown_rounds=2,
                effect="triple",
            ),
            AttackVariant(
                name="Бронебойная стрела",
                description="Полное игнорирование брони противника (100%)",
                damage_mult=1.3,
                armor_penetration=1.0,
                cooldown_rounds=3,
                effect="pierce",
            ),
        ],
    },
    "staff": {
        "emoji": E_FIRE,
        "name": "Посох",
        "base_dmg": 38,
        "price": 1700,
        "description": "Магическое оружие чародея. Стихийные атаки и эффекты.",
        "tier": "epic",
        "variants": [
            AttackVariant(
                name="Магический импульс",
                description="Базовая магическая атака. Игнорирует 40% брони",
                damage_mult=1.0,
                armor_penetration=0.4,
                cooldown_rounds=0,
                effect=None,
            ),
            AttackVariant(
                name="Огненный шар",
                description="Поджигает цель на 3 раунда, нанося периодический урон",
                damage_mult=1.2,
                armor_penetration=0.2,
                cooldown_rounds=2,
                effect="burn",
            ),
            AttackVariant(
                name="Метеор",
                description="Массовый урон с неба. Высокий урон, но долгий КД",
                damage_mult=2.2,
                armor_penetration=0.0,
                cooldown_rounds=4,
                effect="burn",
            ),
        ],
    },
    "hammer": {
        "emoji": "🔨",
        "name": "Молот",
        "base_dmg": 46,
        "price": 2500,
        "description": "Тяжёлое оружие паладина. Сокрушительные удары и оглушение.",
        "tier": "legendary",
        "variants": [
            AttackVariant(
                name="Удар молотом",
                description="Тяжелая физическая атака. Пробивает 30% брони",
                damage_mult=1.0,
                armor_penetration=0.3,
                cooldown_rounds=0,
                effect=None,
            ),
            AttackVariant(
                name="Землетрясение",
                description="Оглушает цель и наносит урон. Пробивает 40% брони",
                damage_mult=1.3,
                armor_penetration=0.4,
                cooldown_rounds=3,
                effect="stun",
            ),
            AttackVariant(
                name="Разрушение",
                description="Сокрушительный удар, ломающий защиту противника (60%)",
                damage_mult=2.0,
                armor_penetration=0.6,
                cooldown_rounds=5,
                effect=None,
            ),
        ],
    },
}


ARMOR_DATA: Dict[str, List[Dict[str, Any]]] = {
    "head": [
        {
            "key": "head_none",
            "name": "Без шлема",
            "emoji": "👕",
            "df": 0,
            "hp": 0,
            "price": 0,
            "chance": 0,
            "dmg_bonus": 0,
            "desc": "Полная уязвимость головы. Рискованно!",
            "tier": "none",
        },
        {
            "key": "head_leather",
            "name": "Кожаный капюшон",
            "emoji": "🧢",
            "df": 2,
            "hp": 3,
            "price": 120,
            "chance": 3,
            "dmg_bonus": 0,
            "desc": "+3% шанс спец-атаки. Лёгкая защита.",
            "tier": "common",
        },
        {
            "key": "head_iron",
            "name": "Железный шлем",
            "emoji": "⛑",
            "df": 4,
            "hp": 8,
            "price": 380,
            "chance": 0,
            "dmg_bonus": 0,
            "desc": "Базовая защита головы. Надёжно и недорого.",
            "tier": "common",
        },
        {
            "key": "head_steel",
            "name": "Стальной шлем",
            "emoji": "🪖",
            "df": 7,
            "hp": 15,
            "price": 850,
            "chance": 0,
            "dmg_bonus": 10,
            "desc": "+10% урон спец-атаки. Военный стандарт.",
            "tier": "uncommon",
        },
        {
            "key": "head_dragon",
            "name": "Драконий шлем",
            "emoji": "🐲",
            "df": 11,
            "hp": 25,
            "price": 1800,
            "chance": 8,
            "dmg_bonus": 20,
            "desc": "+8% шанс, +20% урон спец-атаки. Чешуя дракона.",
            "tier": "rare",
        },
        {
            "key": "head_crown",
            "name": "Корона Лорда",
            "emoji": "👑",
            "df": 14,
            "hp": 30,
            "price": 3000,
            "chance": 12,
            "dmg_bonus": 25,
            "desc": "Максимальная защита и престиж. Королевский артефакт.",
            "tier": "legendary",
        },
    ],
    "torso": [
        {
            "key": "torso_none",
            "name": "Без брони",
            "emoji": "👕",
            "df": 0,
            "hp": 0,
            "price": 0,
            "chance": 0,
            "dmg_bonus": 0,
            "desc": "Полная уязвимость торса. Очень опасно!",
            "tier": "none",
        },
        {
            "key": "torso_robe",
            "name": "Мантия",
            "emoji": "🥋",
            "df": 3,
            "hp": 5,
            "price": 150,
            "chance": 4,
            "dmg_bonus": 0,
            "desc": "+4% шанс спец-атаки. Одежда мага.",
            "tier": "common",
        },
        {
            "key": "torso_chain",
            "name": "Кольчуга",
            "emoji": E_SHIELD,
            "df": 6,
            "hp": 12,
            "price": 480,
            "chance": 0,
            "dmg_bonus": 0,
            "desc": "Надежная защита корпуса. Плетёная сталь.",
            "tier": "common",
        },
        {
            "key": "torso_plate",
            "name": "Латный доспех",
            "emoji": "🏋️",
            "df": 11,
            "hp": 22,
            "price": 1000,
            "chance": 0,
            "dmg_bonus": 15,
            "desc": "+15% урон спец-атаки. Рыцарская броня.",
            "tier": "uncommon",
        },
        {
            "key": "torso_titan",
            "name": "Титановый панцирь",
            "emoji": E_STAR,
            "df": 17,
            "hp": 35,
            "price": 2200,
            "chance": 10,
            "dmg_bonus": 25,
            "desc": "+10% шанс, +25% урон спец-атаки. Сплав богов.",
            "tier": "rare",
        },
        {
            "key": "torso_aegis",
            "name": "Эгида",
            "emoji": "🌟",
            "df": 22,
            "hp": 45,
            "price": 3500,
            "chance": 15,
            "dmg_bonus": 30,
            "desc": "Легендарная защита Зевса. Максимум статов.",
            "tier": "legendary",
        },
    ],
    "arms": [
        {
            "key": "arms_none",
            "name": "Без наручей",
            "emoji": "👕",
            "df": 0,
            "hp": 0,
            "price": 0,
            "chance": 0,
            "dmg_bonus": 0,
            "desc": "Полная уязвимость рук. Быстро, но рискованно.",
            "tier": "none",
        },
        {
            "key": "arms_cloth",
            "name": "Тканевые бинты",
            "emoji": "🩹",
            "df": 2,
            "hp": 2,
            "price": 100,
            "chance": 3,
            "dmg_bonus": 0,
            "desc": "+3% шанс спец-атаки. Монашеская обмотка.",
            "tier": "common",
        },
        {
            "key": "arms_iron",
            "name": "Железные наручи",
            "emoji": E_SHIELD,
            "df": 4,
            "hp": 8,
            "price": 350,
            "chance": 0,
            "dmg_bonus": 0,
            "desc": "Базовая защита рук. Стандартное оснащение.",
            "tier": "common",
        },
        {
            "key": "arms_steel",
            "name": "Стальные латы",
            "emoji": "⚙️",
            "df": 7,
            "hp": 14,
            "price": 800,
            "chance": 0,
            "dmg_bonus": 10,
            "desc": "+10% урон спец-атаки. Кованая сталь.",
            "tier": "uncommon",
        },
        {
            "key": "arms_runic",
            "name": "Рунические наручи",
            "emoji": "🔮",
            "df": 11,
            "hp": 22,
            "price": 1700,
            "chance": 8,
            "dmg_bonus": 20,
            "desc": "+8% шанс, +20% урон спец-атаки. Магические руны.",
            "tier": "rare",
        },
        {
            "key": "arms_berserk",
            "name": "Наручи Берсерка",
            "emoji": "🩸",
            "df": 9,
            "hp": 18,
            "price": 1500,
            "chance": 5,
            "dmg_bonus": 35,
            "desc": "-2 защиты, но +35% урона спец-атак. Для ярости.",
            "tier": "rare",
        },
    ],
    "legs": [
        {
            "key": "legs_none",
            "name": "Без поножей",
            "emoji": "👕",
            "df": 0,
            "hp": 0,
            "price": 0,
            "chance": 0,
            "dmg_bonus": 0,
            "desc": "Полная уязвимость ног. Максимальная мобильность.",
            "tier": "none",
        },
        {
            "key": "legs_cloth",
            "name": "Тканевые штаны",
            "emoji": "👖",
            "df": 2,
            "hp": 3,
            "price": 110,
            "chance": 3,
            "dmg_bonus": 0,
            "desc": "+3% шанс спец-атаки. Лёгкая одежда.",
            "tier": "common",
        },
        {
            "key": "legs_iron",
            "name": "Железные поножи",
            "emoji": E_SHIELD,
            "df": 5,
            "hp": 10,
            "price": 400,
            "chance": 0,
            "dmg_bonus": 0,
            "desc": "Базовая защита ног. Баланс веса и защиты.",
            "tier": "common",
        },
        {
            "key": "legs_steel",
            "name": "Стальные поножи",
            "emoji": "⚙️",
            "df": 8,
            "hp": 16,
            "price": 900,
            "chance": 0,
            "dmg_bonus": 10,
            "desc": "+10% урон спец-атаки. Усиленная защита.",
            "tier": "uncommon",
        },
        {
            "key": "legs_demon",
            "name": "Демонические поножи",
            "emoji": "😈",
            "df": 12,
            "hp": 25,
            "price": 1900,
            "chance": 8,
            "dmg_bonus": 20,
            "desc": "+8% шанс, +20% урон спец-атаки. Кожа демона.",
            "tier": "rare",
        },
        {
            "key": "legs_wind",
            "name": "Поножи Ветра",
            "emoji": E_ZONE_LEGS,
            "df": 6,
            "hp": 12,
            "price": 1100,
            "chance": 10,
            "dmg_bonus": 5,
            "desc": "+10% шанс уворота, +5% урона. Скорость ветра.",
            "tier": "rare",
        },
    ],
}


START_ARMOR_KEYS: List[str] = [
    "head_none",
    "torso_none",
    "arms_none",
    "legs_none",
]

START_WEAPON: str = "fists"

BASE_STATS: Dict[str, int] = {"hp": BASE_HP}


ARENAS: Dict[str, Dict[str, Any]] = {
    "bronze": {
        "name": "Бронзовая арена",
        "emoji": "🥉",
        "min_wins": 0,
        "max_wins": 9,
        "prize": 50,
        "color": "#cd7f32",
        "description": "Арена для новичков. Здесь начинают свой путь все бойцы.",
        "min_level": 1,
        "background": "🟫",
    },
    "silver": {
        "name": "Серебряная арена",
        "emoji": "🥈",
        "min_wins": 10,
        "max_wins": 29,
        "prize": 100,
        "color": "#c0c0c0",
        "description": "Арена для опытных воинов. Серьёзные противники и награды.",
        "min_level": 10,
        "background": "⬜",
    },
    "gold": {
        "name": "Золотая арена",
        "emoji": "🥇",
        "min_wins": 30,
        "max_wins": 10**9,
        "prize": 200,
        "color": "#ffd700",
        "description": "Элитная арена для мастеров. Легенды сражаются здесь.",
        "min_level": 30,
        "background": "🟨",
    },
}

ARENA_ORDER: List[str] = ["bronze", "silver", "gold"]


BOSSES: Dict[str, Dict[str, Any]] = {
    "goblin": {
        "key": "goblin",
        "name": "👺 Гоблин-Вождь",
        "desc": "Хитрый и злой. Бьёт по слабой броне, использует кинжал. Быстрый и ловкий.",
        "hp": 160,
        "weapon": "dagger",
        "armor_keys": {
            "head": "head_leather",
            "torso": "torso_robe",
            "arms": "arms_none",
            "legs": "legs_none",
        },
        "reward_mult": 3,
        "min_wins": 0,
        "difficulty": "easy",
        "lore": "Вождь лесных гоблинов, известный своей хитростью и жестокостью.",
    },
    "dragon": {
        "key": "dragon",
        "name": "🐉 Древний Дракон",
        "desc": "Огнедышащий ужас. Оружие — посох, драконья чешуя вместо брони.",
        "hp": 260,
        "weapon": "staff",
        "armor_keys": {
            "head": "head_steel",
            "torso": "torso_plate",
            "arms": "arms_iron",
            "legs": "legs_iron",
        },
        "reward_mult": 5,
        "min_wins": 5,
        "difficulty": "medium",
        "lore": "Древний дракон, пробудившийся от тысячелетнего сна.",
    },
    "lord": {
        "key": "lord",
        "name": "👹 Древний Лорд",
        "desc": "Владыка арены. Молот разрушения и полная драконья экипировка.",
        "hp": 380,
        "weapon": "hammer",
        "armor_keys": {
            "head": "head_dragon",
            "torso": "torso_titan",
            "arms": "arms_runic",
            "legs": "legs_demon",
        },
        "reward_mult": 10,
        "min_wins": 15,
        "difficulty": "hard",
        "lore": "Павший лорд, ставший тёмным владыкой арены.",
    },
    "titan": {
        "key": "titan",
        "name": "🗿 Каменный Титан",
        "desc": "Неуязвимая глыба. Огромная защита, но медленные атаки.",
        "hp": 500,
        "weapon": "fists",
        "armor_keys": {
            "head": "head_crown",
            "torso": "torso_aegis",
            "arms": "arms_berserk",
            "legs": "legs_wind",
        },
        "reward_mult": 15,
        "min_wins": 35,
        "difficulty": "extreme",
        "lore": "Древний титан, пробуждённый магией. Его кожа — камень, его кулаки — горы.",
    },
    "demon_king": {
        "key": "demon_king",
        "name": "😈 Король Демонов",
        "desc": "Повелитель преисподней. Смесь всех стихий и максимальные статы.",
        "hp": 750,
        "weapon": "staff",
        "armor_keys": {
            "head": "head_crown",
            "torso": "torso_aegis",
            "arms": "arms_runic",
            "legs": "legs_demon",
        },
        "reward_mult": 25,
        "min_wins": 50,
        "difficulty": "nightmare",
        "lore": "Сам Король Демонов спустился в арену, чтобы испытать достойных.",
    },
}


CHAT_EVENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "boss": {
        "name_template": "{emoji} Рейдовый Босс",
        "emoji": E_BOSS,
        "base_hp": 2000,
        "duration_hours": 2.0,
        "reward_per_participant": (50, 150),
        "description": "Могущественное существо появилось в чате! Объединитесь, чтобы победить его.",
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n{emoji} <b>Рейдовый Босс</b> появился в чате!\nHP: {hp}\n\nИспользуйте команду <code>атака</code>, чтобы нанести урон и получить награды!",
    },
    "caravan": {
        "name_template": "🐪 Золотой Караван",
        "emoji": "🐪",
        "base_hp": 1000,
        "duration_hours": 1.0,
        "reward_per_participant": (30, 100),
        "description": "Богатый караван проезжает через чат! Ограбьте его, пока он не ушёл.",
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n🐪 <b>Золотой Караван</b> проезжает через чат!\nHP: {hp}\n\nИспользуйте команду <code>атака</code>, чтобы ограбить его!",
    },
    "raid": {
        "name_template": "⚔️ Набег Орков",
        "emoji": "⚔️",
        "base_hp": 3000,
        "duration_hours": 3.0,
        "reward_per_participant": (80, 200),
        "description": "Орда орков атакует чат! Отразите набег совместными усилиями.",
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n⚔️ <b>Набег Орков</b> начался!\nHP: {hp}\n\nИспользуйте команду <code>атака</code>, чтобы защитить чат!",
    },
    "dragon_raid": {
        "name_template": "🐉 Нашествие Драконов",
        "emoji": "🐉",
        "base_hp": 5000,
        "duration_hours": 4.0,
        "reward_per_participant": (150, 350),
        "description": "Стая драконов атакует! Это самое сложное испытание.",
        "announce_text": "🚨 <b>ВНИМАНИЕ!</b>\n\n🐉 <b>Нашествие Драконов</b> началось!\nHP: {hp}\n\nИспользуйте команду <code>атака</code>, чтобы победить драконов!",
    },
}


def esc(text: Any) -> str:
    return html.escape(str(text))


def create_mention(user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{esc(name)}</a>'


def create_button(text: str, callback_data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback_data)


def build_inline_keyboard(*rows: List[Tuple[str, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [create_button(item[0], item[1]) for item in row]
            for row in rows
        ]
    )


async def safe_edit_message(
    cb: CallbackQuery,
    text: str,
    markup: Optional[InlineKeyboardMarkup] = None
) -> bool:
    try:
        await cb.message.edit_text(
            text[:4090],
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
        return True
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            return True
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
    except Exception as e:
        logging.error(f"Unexpected error in safe_edit_message: {e}")
        return False


def format_number(num: int) -> str:
    return f"{num:,}".replace(",", " ")


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection = sqlite3.connect(
            db_path,
            check_same_thread=False,
            isolation_level=None,
        )
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
                total_damage_dealt INTEGER NOT NULL DEFAULT 0,
                total_damage_taken INTEGER NOT NULL DEFAULT 0,
                total_crystals_earned INTEGER NOT NULL DEFAULT 0,
                total_crystals_spent INTEGER NOT NULL DEFAULT 0
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
            CREATE TABLE IF NOT EXISTS player_stats (
                user_id INTEGER PRIMARY KEY,
                best_weapon TEXT,
                most_used_weapon TEXT,
                favorite_zone TEXT,
                total_blocks INTEGER NOT NULL DEFAULT 0,
                total_specials INTEGER NOT NULL DEFAULT 0,
                longest_win_streak INTEGER NOT NULL DEFAULT 0,
                current_win_streak INTEGER NOT NULL DEFAULT 0,
                boss_kills INTEGER NOT NULL DEFAULT 0,
                event_participations INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS daily_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                quest_type TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                target INTEGER NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                reward_crystals INTEGER NOT NULL DEFAULT 0,
                date TEXT NOT NULL,
                UNIQUE(user_id, quest_type, date)
            );
            CREATE INDEX IF NOT EXISTS ix_notif_user ON notifications(user_id, seen);
            CREATE INDEX IF NOT EXISTS ix_players_wins ON players(wins, is_bot, banned);
            CREATE INDEX IF NOT EXISTS ix_players_crystals ON players(crystals DESC);
            CREATE INDEX IF NOT EXISTS ix_events_active ON chat_events(active, ends_at);
            CREATE INDEX IF NOT EXISTS ix_stats_user ON player_stats(user_id);
            CREATE INDEX IF NOT EXISTS ix_quests_user_date ON daily_quests(user_id, date);
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
        try:
            return self._connection.execute(sql, args).fetchone()
        except sqlite3.Error as e:
            logging.error(f"DB fetch_one error: {e} | SQL: {sql} | Args: {args}")
            return None

    def fetch_all(self, sql: str, args: tuple = ()) -> List[sqlite3.Row]:
        try:
            return self._connection.execute(sql, args).fetchall()
        except sqlite3.Error as e:
            logging.error(f"DB fetch_all error: {e} | SQL: {sql} | Args: {args}")
            return []

    def execute(self, sql: str, args: tuple = ()) -> bool:
        try:
            self._connection.execute(sql, args)
            return True
        except sqlite3.Error as e:
            logging.error(f"DB execute error: {e} | SQL: {sql} | Args: {args}")
            return False

    def close(self) -> None:
        if self._connection:
            self._connection.close()
            logging.info("Database connection closed.")


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
            logging.warning(f"Unknown weapon '{self.weapon}', fallback to 'fists'")
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
        hits = [
            max(1, round(calculate_damage(attacker, defender, atk_zone, def_zone, variant)[0] / 3))
            for _ in range(3)
        ]
        total_dmg = sum(hits)
        defender.hp = max(0, defender.hp - total_dmg)
        log.append(f"⚡ <b>{variant.name}</b>: {' + '.join(map(str, hits))} = <b>−{total_dmg}</b>")
        return True

    elif effect == "exec":
        dmg, _ = calculate_damage(attacker, defender, atk_zone, def_zone, variant)
        defender.hp = max(0, defender.hp - dmg)
        log.append(
            f"{E_SWORD} <b>{variant.name}</b>: {attacker.name} → {defender.name} "
            f"[{ZONE_INFO[atk_zone]['emoji']}] <b>−{dmg}</b>"
        )
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
        log.append(f"{ZONE_INFO[atk_zone]['emoji']} {attacker.name} бьёт в «{ZONE_INFO[atk_zone]['name']}» — {note}")
    else:
        defender.hp = max(0, defender.hp - dmg)
        log.append(
            f"👊 {attacker.name} [{variant.name}] → {defender.name} "
            f"[{ZONE_INFO[atk_zone]['emoji']}] <b>−{dmg}</b>"
        )


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

        if duel.finished:
            return
        if duel.timer_for != uid:
            return
        if duel.get_state_for(uid) != role:
            return
        if uid not in ACTIVE_DUELS:
            return

        await handle_timeout_defeat(duel, uid, bot)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Critical error in duel timer for user {uid}: {e}\n{traceback.format_exc()}")


async def handle_timeout_defeat(duel: Duel, loser_uid: int, bot: Bot) -> None:
    loser = duel.get_fighter(loser_uid)
    loser_name = loser.name if loser else "Неизвестный"
    duel.log.append(
        f"⏱ <b>{loser_name} не успел за {Config.TURN_TIMEOUT} сек — авто-поражение!</b>"
    )

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

    return Fighter(
        name=esc(player_row["name"]),
        max_hp=total_hp,
        hp=total_hp,
        weapon=weapon,
        armor_slots=slots,
    )


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

HUMAN_TITLES: List[str] = [
    "", "", "", "xd", "pro", "god", "real", "top", "_", "007", "tvoy", "cz",
    "boss", "king", "elite", "master", "legend", "hero", "dark", "light",
]


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

            if candidate.lower() not in existing_names and MIN_NAME_LENGTH <= len(candidate) <= MAX_NAME_LENGTH:
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
    arena = determine_arena(player_wins)
    limits = ARENAS[arena]

    humans = [
        r["user_id"] for r in db.fetch_all(
            """SELECT user_id FROM players
               WHERE user_id != ? AND banned=0 AND is_bot=0
               AND wins BETWEEN ? AND ?
               ORDER BY RANDOM() LIMIT 6""",
            (player_uid, limits["min_wins"], limits["max_wins"])
        )
    ]

    bots = [
        r["user_id"] for r in db.fetch_all(
            """SELECT user_id FROM players
               WHERE is_bot=1 AND banned=0
               AND wins BETWEEN ? AND ?
               ORDER BY RANDOM() LIMIT 6""",
            (limits["min_wins"], limits["max_wins"])
        )
    ]

    if humans and bots:
        return random.choice(bots if random.random() < 0.6 else humans)
    if humans:
        return random.choice(humans)
    if bots:
        return random.choice(bots)

    ensure_masked_bots_exist(10)
    rows = db.fetch_all(
        """SELECT user_id FROM players
           WHERE is_bot=1 AND wins BETWEEN ? AND ?
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
    weapon_data = WEAPONS[attacker.weapon]
    variants = weapon_data["variants"]
    available = attacker.get_available_variants()

    if not available:
        return 0

    best_idx = max(available, key=lambda i: variants[i].damage_mult)
    return best_idx


def bot_decide_to_defend(duel: Duel, bot_is_a: bool) -> bool:
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
    def danger_level(z: str) -> int:
        return attacker.get_weapon_dmg_for_zone(z) - defender.get_armor_def(z)

    sorted_zones = sorted(ZONES, key=danger_level, reverse=True)

    if random.random() < 0.25 and len(sorted_zones) > 1:
        return sorted_zones[1]

    return sorted_zones[0]


def play_casino_slots(uid: int, bet: int) -> Tuple[Optional[str], Optional[str]]:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."

    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"
    if bet > Config.CASINO_MAX_BET:
        return None, f"Максимальная ставка: {Config.CASINO_MAX_BET} {E_CRYSTAL}"

    symbols = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣"]
    weights = [25, 22, 20, 15, 12, 6]

    spin = random.choices(symbols, weights=weights, k=3)

    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))

    if spin[0] == spin[1] == spin[2]:
        mult = {"7️⃣": 10, "💎": 8}.get(spin[0], 5)
        win = bet * mult
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (win, uid))
        return (
            f"{' | '.join(spin)}\n\n{E_TROPHY} <b>ДЖЕКПОТ ×{mult}!</b>\nВы выиграли: +{win} {E_CRYSTAL}",
            None
        )

    if spin[0] == spin[1] or spin[1] == spin[2] or spin[0] == spin[2]:
        win = int(bet * 2)
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (win, uid))
        return (
            f"{' | '.join(spin)}\n\n✅ <b>Пара!</b>\nВы выиграли: +{win} {E_CRYSTAL}",
            None
        )

    return (
        f"{' | '.join(spin)}\n\n{E_SKULL} <b>Мимо.</b>\nВы проиграли: −{bet} {E_CRYSTAL}",
        None
    )


def play_casino_dice(uid: int, bet: int) -> Tuple[Optional[str], Optional[str]]:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."

    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"

    player_roll = random.randint(1, 6)
    dealer_roll = random.randint(1, 6)

    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))

    if player_roll > dealer_roll:
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (bet * 2, uid))
        return (
            f"{E_DICE} Ты: {player_roll} · Дилер: {dealer_roll}\n\n"
            f"{E_TROPHY} <b>Победа!</b> +{bet * 2} {E_CRYSTAL}",
            None
        )
    elif player_roll == dealer_roll:
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (bet, uid))
        return (
            f"{E_DICE} Ты: {player_roll} · Дилер: {dealer_roll}\n\n"
            f"🤝 <b>Ничья.</b> Ставка возвращена.",
            None
        )
    else:
        return (
            f"{E_DICE} Ты: {player_roll} · Дилер: {dealer_roll}\n\n"
            f"{E_SKULL} <b>Поражение.</b> −{bet} {E_CRYSTAL}",
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

    if result == choice:
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (bet * 2, uid))
        return (
            f"{E_COIN} Выпало: <b>{result_text}</b>\n\n"
            f"{E_TROPHY} <b>Победа!</b> +{bet * 2} {E_CRYSTAL}",
            None
        )
    else:
        return (
            f"{E_COIN} Выпало: <b>{result_text}</b>\n\n"
            f"{E_SKULL} <b>Поражение.</b> −{bet} {E_CRYSTAL}",
            None
        )


def play_casino_roulette(uid: int, bet: int, color: str = "red") -> Tuple[Optional[str], Optional[str]]:
    p = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (uid,))
    if not p or p["crystals"] < bet:
        return None, "Недостаточно кристаллов."

    if bet < Config.CASINO_MIN_BET:
        return None, f"Минимальная ставка: {Config.CASINO_MIN_BET} {E_CRYSTAL}"

    reds = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

    num = random.randint(0, 36)

    if num == 0:
        res_color = "green"
    elif num in reds:
        res_color = "red"
    else:
        res_color = "black"

    db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (bet, uid))

    if color == res_color:
        mult = 14 if color == "green" else 2
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (bet * mult, uid))
        return (
            f"🎡 Выпало: <b>{num} ({res_color})</b>\n\n"
            f"{E_TROPHY} <b>Победа ×{mult}!</b> +{bet * mult} {E_CRYSTAL}",
            None
        )
    else:
        return (
            f"🎡 Выпало: <b>{num} ({res_color})</b>\n\n"
            f"{E_SKULL} <b>Поражение.</b> −{bet} {E_CRYSTAL}",
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
            f"📊 Выпало число: <b>{result_num}</b>\n\n"
            f"🤝 <b>Ровно 50!</b> Ставка возвращена.",
            None
        )

    win = (choice == "high" and result_num > 50) or (choice == "low" and result_num < 50)

    if win:
        payout = int(bet * 1.9)
        db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (payout, uid))
        return (
            f"📊 Выпало число: <b>{result_num}</b>\n\n"
            f"{E_TROPHY} <b>Победа!</b> +{payout} {E_CRYSTAL}",
            None
        )
    else:
        return (
            f"📊 Выпало число: <b>{result_num}</b>\n\n"
            f"{E_SKULL} <b>Поражение.</b> −{bet} {E_CRYSTAL}",
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
        logging.error(f"Unknown event type: {event_type}")
        return None

    hp = custom_hp or template["base_hp"]
    duration = custom_duration or template["duration_hours"]
    name = template["name_template"].format(emoji=template["emoji"])

    now = time.time()
    ends_at = now + (duration * 3600)

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

    db.execute(
        """INSERT INTO chat_events
           (event_type, name, hp, max_hp, started_by, started_at, ends_at, active)
           VALUES (?,?,?,?,?,?,?,1)""",
        (event_type, name, hp, hp, started_by, now, ends_at)
    )

    logging.info(f"Spawned chat event: {name} (HP: {hp}, duration: {duration}h)")
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

        logging.info(f"Chat event completed: {ACTIVE_CHAT_EVENT.name}")

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
        f"Используйте <code>атака</code> для нанесения урона!"
    )


def create_promo_code(
    code: str,
    reward_crystals: int,
    reward_wins: int,
    max_uses: int,
    hours_valid: int,
    created_by: int
) -> Tuple[bool, str]:
    code = code.strip().upper()

    if not code:
        return False, "Код не может быть пустым."
    if len(code) < Config.PROMO_MIN_CODE_LENGTH:
        return False, f"Минимальная длина кода: {Config.PROMO_MIN_CODE_LENGTH} символов."
    if len(code) > Config.PROMO_MAX_CODE_LENGTH:
        return False, f"Максимальная длина кода: {Config.PROMO_MAX_CODE_LENGTH} символов."
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


def generate_rp_text(
    actor_id: int,
    actor_name: str,
    target_id: int,
    target_name: str,
    action_key: str
) -> str:
    emoji, verb = RP_ACTIONS.get(action_key, ("✨", "взаимодействовал(а) с"))
    actor_mention = create_mention(actor_id, actor_name)
    target_mention = create_mention(target_id, target_name)
    return f"{emoji} {actor_mention} {verb} {target_mention}!"


def resolve_command_target(
    m: Message,
    command_word: str
) -> Tuple[Optional[int], Optional[str]]:
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
            row = db.fetch_one(
                "SELECT user_id FROM players WHERE user_id=? AND banned=0",
                (int(val),)
            )
            if row:
                return row["user_id"], None
        else:
            row = db.fetch_one(
                """SELECT user_id FROM players
                   WHERE (LOWER(username)=LOWER(?) OR LOWER(name)=LOWER(?))
                   AND banned=0 LIMIT 1""",
                (val, val)
            )
            if row:
                return row["user_id"], None

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
        f"╔══════════════════════════╗\n"
        f"      ⚔️ <b>АРЕНА ДУЭЛЯНТОВ</b>\n"
        f"╚══════════════════════════╝\n\n"
        f"{E_TROPHY} Победы: <b>{p['wins']}</b>  ·  {E_SKULL} Поражения: {p['losses']}\n"
        f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>\n"
        f"📍 {a['emoji']} <b>{a['name']}</b>\n\n"
        f"🥉 Бронза — 0–9 побед  ·  <b>{ARENAS['bronze']['prize']} {E_CRYSTAL}</b>\n"
        f"🥈 Серебро — 10–29 побед  ·  <b>{ARENAS['silver']['prize']} {E_CRYSTAL}</b>\n"
        f"🥇 Золото — 30+ побед  ·  <b>{ARENAS['gold']['prize']} {E_CRYSTAL}</b>"
    )
    kb = build_inline_keyboard(
        [("🎲 Найти соперника", "arena:find"), ("👹 Боссы", "arena:bosses")],
        [("📋 Список соперников", "arena:list"), ("🔎 Вызвать по нику", "arena:find_name")],
        [("🏆 Топ арен", "top:cur"), ("👤 Мой профиль", "duel:myprofile")]
    )
    return text, kb


def generate_bosses_menu_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
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


def generate_gear_screen(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None

    w = WEAPONS[p["weapon"]]
    f = create_fighter_from_db(p)
    slots = get_player_armor_slots(p)

    lines = [
        f"🎒 <b>{esc(p['name'])}</b>", "",
        f"{E_TROPHY} Победы: <b>{p['wins']}</b>  ·  {E_SKULL} Поражения: {p['losses']}",
        f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>",
        f"📍 {ARENAS[determine_arena(p['wins'])]['emoji']} {ARENAS[determine_arena(p['wins'])]['name']}", "",
        f"❤️ HP: <b>{f.max_hp}</b>   ⚔️ Атака: <b>{f.base_weapon_dmg}</b>", "",
        "<b>⚔️ Оружие:</b>",
        f"  {w['emoji']} {w['name']} — <i>{w['description']}</i>",
        f"  Базовый урон: <b>{w['base_dmg']}</b>", "",
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


def generate_weapon_list(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None

    equipped = p["weapon"]
    owned = set((p["weapons_owned"] or "").split(","))

    lines = ["⚔️ <b>Оружие</b>", f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>", ""]
    rows = []

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
        elif key in owned:
            label = "🎒 надеть"
        else:
            label = f"{it['price']}💎"
        rows.append([(f"{it['emoji']} {it['name']} · {label}", f"buy_weapon:{key}")])

    rows.append([("⬅️ Назад", "gear:menu")])
    return "\n".join(lines), build_inline_keyboard(*rows)


def generate_armor_slot_menu(uid: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p:
        return "Профиль не найден.", None

    slots = get_player_armor_slots(p)
    lines = ["🛡 <b>Броня — выбери часть тела</b>", f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>", ""]

    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"{ZONE_INFO[slot]['emoji']} <b>{ZONE_INFO[slot]['name']}</b> — {item['emoji']} {item['name']} (защита {item['df']})")

    kb = build_inline_keyboard(
        [("🧠 Голова", "gear:head"), ("🫀 Торс", "gear:torso")],
        [("💪 Руки", "gear:arms"), ("🦵 Ноги", "gear:legs")],
        [("⬅️ Назад", "gear:menu")]
    )
    return "\n".join(lines), kb


def generate_armor_slot_list(uid: int, slot: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (uid,))
    if not p or slot not in ZONES:
        return "Ошибка.", None

    slots = get_player_armor_slots(p)
    equipped = slots.get(slot, f"{slot}_none")
    owned = set((p["armors_owned"] or "").split(","))

    lines = [f"🛡 <b>Броня на {ZONE_INFO[slot]['name'].lower()}</b>", f"{E_CRYSTAL} Кристаллы: <b>{format_number(p['crystals'])}</b>", ""]
    rows = []

    for item in ARMOR_DATA[slot]:
        key = item["key"]
        lines.append(f"{item['emoji']} <b>{item['name']}</b> — защита <b>{item['df']}</b>, HP +{item['hp']}")
        lines.append(f"    {item['desc']}")

        if key == equipped:
            label = "✅ надето"
        elif key in owned:
            label = "🎒 надеть"
        else:
            label = f"{item['price']}💎"
        rows.append([(f"{item['emoji']} {item['name']} · {label}", f"buy_armor:{slot}:{key}")])

    rows.append([("⬅️ К слотам", "gear:armor_menu")])
    return "\n".join(lines), build_inline_keyboard(*rows)


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

    kb = build_inline_keyboard(
        [("🥉 Бронза", "top:bronze"), ("🥈 Серебро", "top:silver"), ("🥇 Золото", "top:gold")],
        [("⬅️ Назад", "arena:menu")]
    )
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
            build_inline_keyboard([("🎲 Найти", "arena:find")], [("⬅️ Назад", "arena:menu")])
        )

    kb_rows = []
    for r in rows:
        kb_rows.append([
            (f"{r['name'][:16]} · {r['wins']}{E_TROPHY}/{r['losses']}{E_SKULL}", f"duel:pick:{r['user_id']}"),
            ("👁", f"duel:profile:{r['user_id']}"),
        ])
    kb_rows.append([("⬅️ Назад", "arena:menu")])

    return f"{a['emoji']} <b>{a['name']}</b> — соперники:", build_inline_keyboard(*kb_rows)


def generate_profile_text(row: sqlite3.Row) -> str:
    if not row:
        return "Профиль не найден."

    w = WEAPONS[row["weapon"]] if row["weapon"] in WEAPONS else WEAPONS["fists"]
    f = create_fighter_from_db(row)
    slots = get_player_armor_slots(row)
    arena = ARENAS[determine_arena(row["wins"])]

    lines = [
        f"👤 <b>{esc(row['name'])}</b>", "",
        f"{E_TROPHY} Победы: {row['wins']}  ·  {E_SKULL} Поражения: {row['losses']}",
        f"{E_CRYSTAL} Кристаллы: {format_number(row['crystals'])}",
        f"📍 {arena['emoji']} {arena['name']}", "",
        f"❤️ HP: <b>{f.max_hp}</b>",
        f"{w['emoji']} {w['name']} — баз. урон <b>{w['base_dmg']}</b>", "",
        "<b>🛡 Броня:</b>"
    ]

    for slot in ZONES:
        item = get_armor_item_by_key(slots[slot]) or get_armor_item_by_key(f"{slot}_none")
        lines.append(f"  {ZONE_INFO[slot]['emoji']} {ZONE_INFO[slot]['name']}: {item['emoji']} {item['name']} ({item['df']})")

    return "\n".join(lines)


def generate_duel_status_text(
    duel: Duel,
    for_uid: int,
    extra: str = "",
    timer_left: Optional[int] = None
) -> str:
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
    duel = ACTIVE_DUELS.get(uid)
    if not duel:
        return build_inline_keyboard()

    weapon = WEAPONS[duel.get_attacker().weapon]
    rows = []

    for i, v in enumerate(weapon["variants"]):
        cd = duel.get_attacker().attack_cooldowns.get(i, 0)

        if cd > 0:
            text = f"⏳ {i + 1}. {v.name} (КД: {cd}р)"
            rows.append([(text, f"duel:variant_disabled:{i}")])
        else:
            effect_text = f" [{v.effect}]" if v.effect else ""
            text = f"{i + 1}. {v.name} · x{v.damage_mult}{effect_text}"
            rows.append([(text, f"duel:variant:{i}")])

    return build_inline_keyboard(*rows) if rows else build_inline_keyboard()


def get_attack_zone_kb() -> InlineKeyboardMarkup:
    return build_inline_keyboard(
        [
            (f"{E_ZONE_HEAD} Голова ×1.5", "duel:atk:head"),
            (f"{E_ZONE_TORSO} Торс ×1.0", "duel:atk:torso"),
        ],
        [
            (f"{E_ZONE_ARMS} Руки ×0.8", "duel:atk:arms"),
            (f"{E_ZONE_LEGS} Ноги ×0.9", "duel:atk:legs"),
        ],
    )


def get_defend_zone_kb() -> InlineKeyboardMarkup:
    return build_inline_keyboard(
        [
            (f"{E_ZONE_HEAD} Голова", "duel:def:head"),
            (f"{E_ZONE_TORSO} Торс", "duel:def:torso"),
        ],
        [
            (f"{E_ZONE_ARMS} Руки", "duel:def:arms"),
            (f"{E_ZONE_LEGS} Ноги", "duel:def:legs"),
        ],
    )


def get_finish_duel_kb() -> InlineKeyboardMarkup:
    return build_inline_keyboard(
        [("🔁 Ещё раз", "duel:again")],
        [("🏠 В главное меню", "arena:menu")],
    )


router = Router()


class RegistrationState(StatesGroup):
    waiting_for_name = State()


class DuelFindState(StatesGroup):
    waiting_for_target = State()


HELP_TEXT = (
    "╔══════════════════════════╗\n"
    "   ⚔️ <b>АРЕНА ДУЭЛЯНТОВ</b>\n"
    "╚══════════════════════════╝\n\n"
    "<b>📌 Как использовать команды в чате:</b>\n"
    "• Ответь на сообщение игрока командой\n"
    "• Или: <code>команда @user</code> / <code>команда ID</code>\n\n"
    "<b>⚔️ Дуэли:</b>\n"
    "• <code>перчатка</code> или <code>перч</code> — вызвать на бой\n"
    "• <code>профиль</code> или <code>фото</code> — статистика\n\n"
    "<b>💎 Экономика:</b>\n"
    "• <code>перевод [сумма]</code> — перевести кристаллы\n"
    "• <code>баланс</code> — проверить баланс\n\n"
    "<b>🎰 Казино (сокращения):</b>\n"
    "• <code>сл [сумма]</code> — слоты\n"
    "• <code>кост [сумма]</code> — кости\n"
    "• <code>мон [сумма] [о/р]</code> — монетка\n"
    "• <code>рул [сумма] [к/ч/з]</code> — рулетка\n"
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
    "• <code>событие босс</code> / <code>событие караван</code>\n"
    "• <code>событие набег</code> / <code>событие дракон</code>"
)


@router.message(CommandStart())
async def handle_start_command(m: Message, state: FSMContext) -> None:
    await state.clear()
    ensure_masked_bots_exist(Config.BOT_GENERATION_COUNT)

    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))

    if p:
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
        await m.answer(
            f"Имя должно быть от {MIN_NAME_LENGTH} до {MAX_NAME_LENGTH} символов. "
            f"Попробуй ещё раз:"
        )
        return

    if name.startswith("/"):
        await m.answer("Имя не может начинаться с '/'. Попробуй ещё раз:")
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


@router.message(F.text.regexp(r"(?i)^(help|помощь|хелп)$"))
async def handle_help_command(m: Message) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        await m.answer("Сначала отправь /start в ЛС бота.")
        return

    kb = MENU_KB if m.chat.type == "private" else None
    await m.answer(HELP_TEXT, reply_markup=kb)


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

    await m.answer(
        "📬 <b>Пока тебя не было:</b>\n\n" + "\n\n".join(r["text"] for r in rows)
    )


def is_admin(uid: int) -> bool:
    return uid == Config.ADMIN_ID


def is_user_banned(uid: int) -> bool:
    p = db.fetch_one("SELECT banned FROM players WHERE user_id=?", (uid,))
    return bool(p and p["banned"])


def notify_player(uid: int, text: str) -> None:
    if uid <= 0:
        return
    db.execute(
        "INSERT INTO notifications (user_id, text, ts) VALUES (?,?,?)",
        (uid, text, time.time())
    )


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

    db.execute(
        "UPDATE players SET last_active=? WHERE user_id=?",
        (time.time(), m.from_user.id)
    )

    await flush_notifications(m)

    if m.text == BTN_ARENA:
        text, kb = generate_arena_menu_screen(m.from_user.id)
        await m.answer(text, reply_markup=kb)
    elif m.text == BTN_CASINO:
        text = (
            "╔══════════════════════════╗\n"
            f"   {E_SLOT} <b>КАЗИНО</b>\n"
            "╚══════════════════════════╝\n\n"
            f"{E_CRYSTAL} Баланс: <b>{format_number(db.fetch_one('SELECT crystals FROM players WHERE user_id=?', (m.from_user.id,))['crystals'])}</b>\n\n"
            "Выбери игру в чате:\n"
            "• <code>сл 100</code> — слоты\n"
            "• <code>кост 100</code> — кости\n"
            "• <code>мон 100 о</code> — монетка (о/р)\n"
            "• <code>рул 100 к</code> — рулетка (к/ч/з)\n"
            "• <code>больше 100</code> / <code>меньше 100</code>"
        )
        await m.answer(text)
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

    tid, err = resolve_command_target(m, m.text.split()[0])
    if err:
        await m.answer(err)
        return

    if tid == m.from_user.id:
        await m.answer("🤨 Нельзя вызвать себя.")
        return

    target = db.fetch_one("SELECT * FROM players WHERE user_id=?", (tid,))
    if not target or target["banned"]:
        await m.answer("Игрок не найден или забанен.")
        return

    if tid < 0:
        await initiate_duel_message(m.from_user.id, tid, m, bot)
    else:
        attacker = db.fetch_one("SELECT name FROM players WHERE user_id=?", (m.from_user.id,))
        notify_player(
            tid,
            f"{E_GLOVE} <b>{esc(attacker['name'])}</b> кинул тебе перчатку! "
            f"Открой бота для принятия вызова."
        )
        await m.answer(f"{E_GLOVE} Ты кинул перчатку <b>{esc(target['name'])}</b>.")


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

    notify_player(
        tid,
        f"{E_CRYSTAL} <b>{esc(p['name'])}</b> перевёл тебе <b>{net_amount}</b> кристаллов!"
    )


@router.message(F.text.regexp(r"(?i)^атака(\s|$)"))
async def cmd_attack_event(m: Message) -> None:
    p = db.fetch_one("SELECT name FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return

    result = attack_chat_event(m.from_user.id, p["name"])

    if not result:
        await m.answer("Сейчас нет активных чатовых событий (Босс/Караван/Набег).")
        return

    await m.answer(result)


@router.message(F.text.regexp(r"(?i)^событие(\s|$)"))
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


@router.message(F.text.regexp(r"(?i)^(слоты|slot|сл)(\s+)(\d+)$"))
async def cmd_chat_slots(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return

    result, err = play_casino_slots(m.from_user.id, int(m.text.split()[-1]))
    if err:
        await m.answer(err)
        return

    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


@router.message(F.text.regexp(r"(?i)^(кости|dice|кост)(\s+)(\d+)$"))
async def cmd_chat_dice(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return

    result, err = play_casino_dice(m.from_user.id, int(m.text.split()[-1]))
    if err:
        await m.answer(err)
        return

    balance = db.fetch_one("SELECT crystals FROM players WHERE user_id=?", (m.from_user.id,))
    await m.answer(f"{result}\n\n{E_CRYSTAL} Баланс: <b>{format_number(balance['crystals'])}</b>")


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


@router.message(F.text.regexp(r"(?i)^(рулетка|roulette|рул)(\s+)(\d+)(\s+)(красное|черное|зеленое|к|ч|з)$"))
async def cmd_chat_roulette(m: Message) -> None:
    p = db.fetch_one("SELECT * FROM players WHERE user_id=?", (m.from_user.id,))
    if not p:
        await m.answer("Сначала /start в ЛС бота.")
        return

    parts = m.text.split()
    color_raw = parts[3].lower()
    color = "red" if color_raw in ["красное", "к"] else ("black" if color_raw in ["черное", "ч"] else "green")

    result, err = play_casino_roulette(m.from_user.id, int(parts[1]), color)
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


def initiate_duel(
    a_id: int,
    b_id: int,
    is_boss: bool = False,
    boss_key: Optional[str] = None,
    reward_mult: int = 1
) -> Optional[Duel]:
    a_row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (a_id,))
    if not a_row:
        return None

    fa = create_fighter_from_db(a_row)

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

    first_attacker = fa.name if duel.attacker_is_a else fb.name
    prefix = f"{E_BOSS} <b>БОСС</b> " if is_boss else ""
    duel.add_log(f"{prefix}Бой начался! Первым атакует <b>{first_attacker}</b>.")

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
    if bid == aid:
        await m.answer("🤨 Нельзя драться с самим собой.")
        return

    if aid in ACTIVE_DUELS:
        await m.answer("У тебя уже идёт активный бой.")
        return

    duel = initiate_duel(aid, bid, is_boss, boss_key, reward_mult)
    if not duel:
        await m.answer("Не удалось начать бой (соперник недоступен).")
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
                generate_duel_status_text(
                    duel, aid,
                    extra="⚔️ Соперник уже выбрал удар.",
                    timer_left=Config.TURN_TIMEOUT
                ),
                reply_markup=get_defend_zone_kb()
            )
            start_duel_timer(duel, aid, "defender", bot)
        else:
            await m.answer(
                generate_duel_status_text(duel, aid, extra="⏳ Соперник выбирает удар…"),
                reply_markup=build_inline_keyboard([("🔄 Обновить", "duel:refresh")])
            )

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
            generate_duel_status_text(
                duel, atk_id,
                extra="🎯 Твой ход — выбери вариант атаки.",
                timer_left=Config.TURN_TIMEOUT
            ),
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
        db.execute(
            "UPDATE players SET crystals=crystals+?, total_crystals_earned=total_crystals_earned+? WHERE user_id=?",
            (prize, prize, aid)
        )

        if bid and bid > 0:
            db.execute(
                "UPDATE players SET losses=losses+1, total_duels=total_duels+1, "
                "wins=CASE WHEN wins>0 THEN wins-1 ELSE 0 END WHERE user_id=?",
                (bid,)
            )
            a_name = a_row["name"]
            notify_player(bid, f"{E_SKULL} <b>{esc(a_name)}</b> одолел тебя. −1 {E_TROPHY}, без награды.")

        result_line = f"{E_TROPHY} <b>ТЫ ПОБЕДИЛ!</b>  +1 {E_TROPHY}  ·  +{prize} {E_CRYSTAL}"
    else:
        if bid and bid > 0:
            db.execute("UPDATE players SET wins=wins+1, total_duels=total_duels+1 WHERE user_id=?", (bid,))

            current_wins_b = db.fetch_one("SELECT wins FROM players WHERE user_id=?", (bid,))["wins"]
            prize_b = ARENAS[determine_arena(current_wins_b)]["prize"] * mult
            db.execute(
                "UPDATE players SET crystals=crystals+?, total_crystals_earned=total_crystals_earned+? WHERE user_id=?",
                (prize_b, prize_b, bid)
            )

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
    await safe_edit_message(cb, *generate_arena_list_screen(cb.from_user.id))
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
        build_inline_keyboard(
            [("⬅️ Назад", "arena:list")],
            [("⚔️ Вызвать на бой", f"duel:pick:{tid}")]
        )
    )
    await cb.answer()


@router.callback_query(F.data == "duel:myprofile")
async def cb_my_profile(cb: CallbackQuery) -> None:
    row = db.fetch_one("SELECT * FROM players WHERE user_id=?", (cb.from_user.id,))
    if not row:
        await cb.answer("Сначала /start", show_alert=True)
        return
    await safe_edit_message(
        cb,
        generate_profile_text(row),
        build_inline_keyboard(
            [("⬅️ Назад", "arena:menu")],
            [("🎒 Снаряжение", "gear:menu")]
        )
    )
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
            build_inline_keyboard([("🔄 Обновить", "duel:refresh")])
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
                build_inline_keyboard([("🔄 Обновить", "duel:refresh")])
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
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    await safe_edit_message(cb, *generate_gear_screen(cb.from_user.id))
    await cb.answer()


@router.callback_query(F.data == "gear:w")
async def cb_gear_weapon(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    await safe_edit_message(cb, *generate_weapon_list(cb.from_user.id))
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
            "UPDATE players SET crystals=chips-?, weapons_owned=?, weapon=? WHERE user_id=?",
            (item["price"], ",".join(owned | {key}), key, cb.from_user.id)
        )
        toast = f"Куплено: {item['name']}"
    else:
        await cb.answer(f"Нужно {item['price']}💎", show_alert=True)
        return

    await safe_edit_message(cb, *generate_weapon_list(cb.from_user.id))
    await cb.answer(toast)


@router.callback_query(F.data == "gear:armor_menu")
async def cb_gear_armor_menu(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    await safe_edit_message(cb, *generate_armor_slot_menu(cb.from_user.id))
    await cb.answer()


@router.callback_query(F.data.regexp(r"^gear:(head|torso|arms|legs)$"))
async def cb_gear_armor_slot(cb: CallbackQuery) -> None:
    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (cb.from_user.id,)):
        await cb.answer("Сначала /start", show_alert=True)
        return
    slot = cb.data.split(":")[1]
    await safe_edit_message(cb, *generate_armor_slot_list(cb.from_user.id, slot))
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
            f"UPDATE players SET crystals=chips-?, armors_owned=?, {col}=? WHERE user_id=?",
            (item["price"], ",".join(owned | {key}), key, cb.from_user.id)
        )
        toast = f"Куплено: {item['name']}"
    else:
        await cb.answer(f"Нужно {item['price']}💎", show_alert=True)
        return

    await safe_edit_message(cb, *generate_armor_slot_list(cb.from_user.id, slot))
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

    await safe_edit_message(cb, *generate_top_screen(cb.from_user.id, key))
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
    if not m.from_user:
        return

    if not db.fetch_one("SELECT 1 FROM players WHERE user_id=?", (m.from_user.id,)):
        if m.chat.type == "private":
            await m.answer("Отправь /start, чтобы создать бойца ⚔️")
        return

    if is_user_banned(m.from_user.id):
        await m.answer("🚫 Доступ закрыт.")
        return

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


async def scheduled_event_spawner(bot: Bot) -> None:
    while True:
        try:
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
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format=Config.LOG_FORMAT,
        datefmt=Config.LOG_DATE_FORMAT,
    )

    
    logging.info("=" * 60)
    logging.info("⚔️ АРЕНА ДУЭЛЯНТОВ — Ultimate Edition v7.1")
    logging.info("=" * 60)

    logging.info("Initializing database...")
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
        logging.critical(f"Fatal error in polling: {e}\n{traceback.format_exc()}")
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
