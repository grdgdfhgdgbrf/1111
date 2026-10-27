import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from app.config import BOT_TOKEN
from app.database import init_settings
from app.middlewares.throttling import ThrottlingMiddleware
from app.middlewares.subscriptions import RequiredSubscriptionMiddleware
from app.handlers import start, piarflow, menu, tasks, withdraw, promo, admin_panel, admin_actions, broadcast, casino, admin_casino, admin_extra, engagement

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
BOT_COMMANDS = [
    BotCommand(command="start", description="🚀 Запустить бота"),
    BotCommand(command="help", description="📖 Помощь и список команд"),
    BotCommand(command="menu", description="🏠 Главное меню"),
    BotCommand(command="earn", description="💰 Заработать звёзды"),
    BotCommand(command="games", description="🎰 Игры казино (ставки в монетах)"),
    BotCommand(command="topup", description="💳 Пополнить Stars"),
    BotCommand(command="exchange", description="💱 Курс и баланс"),
    BotCommand(command="transfer", description="💸 Перевести монеты по ID или ответом"),
    BotCommand(command="profile", description="👤 Мой профиль"),
    BotCommand(command="withdraw", description="⭐ Вывести звёзды"),
    BotCommand(command="promo", description="🎁 Активировать промокод"),
    BotCommand(command="top", description="🏆 Топ богачей"),
    BotCommand(command="bonus", description="🎁 Ежедневный бонус"),
    BotCommand(command="duel", description="⚔️ Дуэль с игроком"),
]

async def main() -> None:
    init_settings()
    engagement.refund_stale_duels()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.message.middleware(RequiredSubscriptionMiddleware())
    dp.callback_query.middleware(RequiredSubscriptionMiddleware())
    dp.include_router(casino.router)
    dp.include_router(engagement.router)
    dp.include_router(admin_casino.router)
    dp.include_router(admin_extra.router)
    dp.include_router(admin_panel.router)
    dp.include_router(admin_actions.router)
    dp.include_router(broadcast.router)
    dp.include_router(piarflow.router)
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(tasks.router)
    dp.include_router(withdraw.router)
    dp.include_router(promo.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(BOT_COMMANDS)
    while True:
        try:
            logger.info("Бот запущен, начинаю polling...")
            await dp.start_polling(bot)
        except Exception as exc:
            logger.error("Ошибка поллинга: %s", exc, exc_info=True)
            await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")



