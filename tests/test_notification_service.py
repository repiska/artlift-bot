"""Тесты для сервиса уведомлений"""
from unittest.mock import patch

import pytest
from aiogram.types import InlineKeyboardMarkup

from config import settings


@pytest.mark.asyncio
async def test_notify_admin_new_application(notification_service, user_service):
    """Тест уведомления админа о новой заявке"""
    with patch.object(settings, "ADMIN_IDS", [999999, 888888]):
        await user_service.register_user(123456, "test_user", "Test User")

        result = await notification_service.notify_admin_new_application(
            123456,
            "test_user",
            "Test User",
        )

        assert result is True
        assert notification_service.bot.send_message.called


@pytest.mark.asyncio
async def test_notify_admin_user_question(notification_service, user_service):
    """Тест уведомления админа о вопросе пользователя"""
    with patch.object(settings, "ADMIN_IDS", [999999, 888888]):
        await user_service.register_user(123456, "test_user", "Test User")

        result = await notification_service.notify_admin_user_question(
            123456,
            "test_user",
            "Test User",
        )

        assert result is True
        assert notification_service.bot.send_message.called


@pytest.mark.asyncio
async def test_notify_user_application_approved(notification_service, user_service):
    """Тест уведомления пользователя об одобрении"""
    await user_service.register_user(123456, "test_user", "Test User")

    result = await notification_service.notify_user_application_approved(
        123456,
        "Test User",
    )

    assert result is True
    assert notification_service.bot.send_message.called

    call_args = notification_service.bot.send_message.call_args
    assert call_args.args[0] == 123456


@pytest.mark.asyncio
async def test_notify_user_application_rejected(notification_service, user_service):
    """Тест уведомления пользователя об отказе"""
    await user_service.register_user(123456, "test_user", "Test User")

    result = await notification_service.notify_user_application_rejected(
        123456,
        "Test User",
    )

    assert result is True
    assert notification_service.bot.send_message.called


@pytest.mark.asyncio
async def test_send_reminder(notification_service):
    """Тест отправки напоминания"""
    result = await notification_service.send_reminder(
        123456,
        "Test reminder message",
    )

    assert result is True
    assert notification_service.bot.send_message.called

    call_args = notification_service.bot.send_message.call_args
    # positional args: chat_id, text
    assert call_args.args[0] == 123456
    assert call_args.args[1] == "Test reminder message"

    reply_markup = call_args.kwargs.get("reply_markup")
    assert isinstance(reply_markup, InlineKeyboardMarkup)
    buttons = reply_markup.inline_keyboard
    assert buttons[0][0].text == "Нет, заполнить"
    assert buttons[1][0].text == "Да, заполнил(а)"
    assert buttons[1][0].callback_data == "application_filled"
