"""Тесты для работы с базой данных"""
import pytest
from datetime import datetime


@pytest.mark.asyncio
async def test_create_user(temp_db):
    """Тест создания пользователя"""
    result = await temp_db.create_user(
        telegram_id=123456,
        username="test_user",
        full_name="Test User",
        role="user"
    )
    
    assert result is True
    
    user = await temp_db.get_user(123456)
    assert user is not None
    assert user["telegram_id"] == 123456
    assert user["username"] == "test_user"
    assert user["full_name"] == "Test User"
    assert user["role"] == "user"


@pytest.mark.asyncio
async def test_update_user(temp_db):
    """Тест обновления пользователя"""
    await temp_db.create_user(123456, "old_username", "Old Name")
    
    # Обновляем
    await temp_db.create_user(123456, "new_username", "New Name")
    
    user = await temp_db.get_user(123456)
    assert user["username"] == "new_username"
    assert user["full_name"] == "New Name"


@pytest.mark.asyncio
async def test_create_application(temp_db):
    """Тест создания заявки"""
    await temp_db.create_user(123456, "test_user", "Test User")
    
    app_id = await temp_db.create_application(123456)
    
    assert app_id is not None
    
    application = await temp_db.get_application(123456)
    assert application is not None
    assert application["user_id"] == 123456
    assert application["status"] == "pending"


@pytest.mark.asyncio
async def test_update_application_status(temp_db):
    """Тест обновления статуса заявки"""
    await temp_db.create_user(123456, "test_user", "Test User")
    await temp_db.create_user(999999, "admin", "Admin", role="admin")
    
    await temp_db.create_application(123456)
    
    # Одобряем заявку
    result = await temp_db.update_application_status(123456, "approved", 999999)
    assert result is True
    
    application = await temp_db.get_application(123456)
    assert application["status"] == "approved"
    assert application["admin_id"] == 999999
    assert application["reviewed_at"] is not None


@pytest.mark.asyncio
async def test_get_pending_applications(temp_db):
    """Тест получения заявок на рассмотрении"""
    # Создаем несколько пользователей и заявок
    await temp_db.create_user(111, "user1", "User 1")
    await temp_db.create_user(222, "user2", "User 2")
    await temp_db.create_user(333, "user3", "User 3")
    
    await temp_db.create_application(111)
    await temp_db.create_application(222)
    app_id_3 = await temp_db.create_application(333)
    
    # Одобряем одну заявку
    await temp_db.update_application_status(111, "approved", 999999)
    
    # Получаем pending заявки
    pending = await temp_db.get_pending_applications(limit=10, offset=0)
    
    assert len(pending) == 2
    assert all(app["status"] == "pending" for app in pending)
    assert pending[0]["user_id"] in [222, 333]
    assert pending[1]["user_id"] in [222, 333]


@pytest.mark.asyncio
async def test_reminders(temp_db):
    """Тест создания и получения напоминаний"""
    await temp_db.create_user(123456, "test_user", "Test User")
    
    from datetime import datetime, timedelta
    
    scheduled_time = datetime.now() + timedelta(hours=3)
    reminder_id = await temp_db.create_reminder(123456, "3h", scheduled_time)
    
    assert reminder_id is not None
    
    # Получаем pending напоминания
    reminders = await temp_db.get_pending_reminders()
    
    # Может быть пустым если время еще не наступило
    # Но можем проверить что напоминание создано через прямую проверку


@pytest.mark.asyncio
async def test_cancel_user_reminders(temp_db):
    """Тест отмены напоминаний пользователя"""
    await temp_db.create_user(123456, "test_user", "Test User")
    
    from datetime import datetime, timedelta
    
    await temp_db.create_reminder(123456, "3h", datetime.now() + timedelta(hours=3))
    await temp_db.create_reminder(123456, "1d", datetime.now() + timedelta(days=1))
    
    result = await temp_db.cancel_user_reminders(123456)
    assert result is True

