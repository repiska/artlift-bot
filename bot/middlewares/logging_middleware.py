"""Middleware для логирования"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import logging

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования действий пользователей"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Логируем сообщения и callback'и
        if isinstance(event, Message):
            user = event.from_user
            logger.info(
                f"Message from user {user.id} (@{user.username}): {event.text}"
            )
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            logger.info(
                f"Callback from user {user.id} (@{user.username}): {event.data}"
            )
        
        return await handler(event, data)

