"""Конфигурация pytest"""
import pytest
import asyncio
import aiosqlite
import tempfile
import os
from pathlib import Path
from bot.database.models import Database
from bot.services.user_service import UserService
from bot.services.application_service import ApplicationService
from bot.services.notification_service import NotificationService
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для асинхронных тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def temp_db():
    """Временная база данных для тестов"""
    # Создаем временный файл
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db = Database(path)
    await db.init_db()
    
    yield db
    
    # Очистка
    os.unlink(path)


@pytest.fixture
async def user_service(temp_db):
    """Сервис для работы с пользователями"""
    yield UserService(temp_db)


@pytest.fixture
async def application_service(temp_db):
    """Сервис для работы с заявками"""
    yield ApplicationService(temp_db)


@pytest.fixture
def mock_bot():
    """Мок бота для тестов"""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
async def notification_service(mock_bot, temp_db):
    """Сервис уведомлений с мок-ботом"""
    yield NotificationService(mock_bot, temp_db)

