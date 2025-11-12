"""Главный файл запуска бота"""
import asyncio
import logging
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.settings import settings
from bot.database.models import Database
from bot.services.user_service import UserService
from bot.services.application_service import ApplicationService
from bot.services.notification_service import NotificationService
from bot.services.reminder_service import ReminderService
from bot.services.message_service import MessageService
from bot.services.question_service import QuestionService
from bot.middlewares.logging_middleware import LoggingMiddleware
from bot.handlers import user_handlers, admin_handlers, common_handlers


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    # Инициализация базы данных
    db = Database(settings.DATABASE_PATH)
    await db.init_db()
    logger.info("База данных инициализирована")
    
    # Инициализация Redis для FSM
    storage = RedisStorage.from_url(settings.redis_url)
    
    # Инициализация бота и диспетчера
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=storage)
    
    # Инициализация сервисов
    user_service = UserService(db)
    application_service = ApplicationService(db)
    message_service = MessageService(db)
    notification_service = NotificationService(bot, db, message_service)
    question_service = QuestionService(db)
    
    # Инициализация планировщика
    scheduler = AsyncIOScheduler()
    scheduler.start()
    
    reminder_service = ReminderService(scheduler, db, notification_service)
    
    # Регистрация роутеров
    # Важно: common_handlers должен быть первым, чтобы reply-кнопки обрабатывались раньше состояний
    dp.include_router(common_handlers.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)
    
    # Регистрация middleware для логирования
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    # Dependency injection для handlers через FSM context
    class DependencyMiddleware(BaseMiddleware):
        """Middleware для внедрения зависимостей"""
        async def __call__(self, handler, event, data):
            data["user_service"] = user_service
            data["application_service"] = application_service
            data["notification_service"] = notification_service
            data["reminder_service"] = reminder_service
            data["message_service"] = message_service
            data["question_service"] = question_service
            return await handler(event, data)
    
    dp.message.middleware(DependencyMiddleware())
    dp.callback_query.middleware(DependencyMiddleware())
    
    logger.info("Бот запущен")
    
    # Запуск бота
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

