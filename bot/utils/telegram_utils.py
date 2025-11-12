"""Утилиты для безопасной отправки сообщений в Telegram."""

import asyncio
import logging
from typing import Callable, Iterable, Tuple

from aiohttp import ClientError
from aiogram.exceptions import (
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)


logger = logging.getLogger(__name__)


DEFAULT_RETRY_EXCEPTIONS: Tuple[type, ...] = (
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
    ClientError,
    asyncio.TimeoutError,
)


async def send_with_retry(
    send_callable: Callable,
    *args,
    retries: int = 3,
    base_delay: float = 1.0,
    exceptions: Tuple[type, ...] | Iterable[type] = DEFAULT_RETRY_EXCEPTIONS,
    log_context: str | None = None,
    **kwargs
):
    """Вызывает Telegram-метод с повторными попытками при сетевых ошибках."""

    if isinstance(exceptions, tuple):
        handled_exceptions: Tuple[type, ...] = exceptions
    else:
        handled_exceptions = tuple(exceptions)

    for attempt in range(retries):
        try:
            return await send_callable(*args, **kwargs)
        except handled_exceptions as exc:  # type: ignore[arg-type]
            if attempt == retries - 1:
                logger.exception(
                    "Telegram send failed after retries%s",
                    f" ({log_context})" if log_context else "",
                )
                raise

            delay = base_delay * (2 ** attempt)

            if isinstance(exc, TelegramRetryAfter):
                delay = max(delay, exc.retry_after + 0.1)

            if log_context:
                logger.warning(
                    "Telegram send error%s: %s. Retry in %.1fs (attempt %d/%d)",
                    f" ({log_context})",
                    exc,
                    delay,
                    attempt + 1,
                    retries,
                )
            else:
                logger.warning(
                    "Telegram send error: %s. Retry in %.1fs (attempt %d/%d)",
                    exc,
                    delay,
                    attempt + 1,
                    retries,
                )

            await asyncio.sleep(delay)


async def answer_with_retry(message, *args, **kwargs):
    """Обертка для message.answer с повторными попытками."""
    return await send_with_retry(
        message.answer,
        *args,
        log_context=f"chat_id={message.chat.id}",
        **kwargs,
    )


async def edit_text_with_retry(message, *args, **kwargs):
    """Обертка для message.edit_text с повторными попытками."""
    return await send_with_retry(
        message.edit_text,
        *args,
        log_context=f"chat_id={message.chat.id}",
        **kwargs,
    )


async def bot_send_with_retry(bot_send_callable: Callable, chat_id: int | str, *args, **kwargs):
    """Обертка для методов Bot (например, send_message) с повторными попытками."""
    return await send_with_retry(
        bot_send_callable,
        chat_id,
        *args,
        log_context=f"chat_id={chat_id}",
        **kwargs,
    )


async def bot_call_with_retry(bot_callable: Callable, *args, log_context: str | None = None, **kwargs):
    """Обертка для произвольного вызова метода Telegram Bot с повторными попытками."""
    return await send_with_retry(
        bot_callable,
        *args,
        log_context=log_context,
        **kwargs,
    )

