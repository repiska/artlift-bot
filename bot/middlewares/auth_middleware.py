"""Middleware для проверки прав доступа"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from config.settings import settings


class AuthMiddleware(BaseMiddleware):
    """Middleware для проверки администраторских прав"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        return await handler(event, data)


def is_admin(telegram_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return telegram_id in settings.ADMIN_IDS

