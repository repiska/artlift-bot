"""Тесты для сервиса заявок"""
import pytest
from bot.services.application_service import ApplicationService
from bot.services.user_service import UserService


@pytest.mark.asyncio
async def test_create_application(application_service, user_service):
    """Тест создания заявки"""
    await user_service.register_user(123456, "test_user", "Test User")
    
    app_id = await application_service.create_application(123456)
    
    assert app_id is not None


@pytest.mark.asyncio
async def test_get_application(application_service, user_service):
    """Тест получения заявки"""
    await user_service.register_user(123456, "test_user", "Test User")
    await application_service.create_application(123456)
    
    application = await application_service.get_application(123456)
    
    assert application is not None
    assert application["user_id"] == 123456
    assert application["status"] == "pending"


@pytest.mark.asyncio
async def test_approve_application(application_service, user_service):
    """Тест одобрения заявки"""
    await user_service.register_user(123456, "test_user", "Test User")
    await user_service.register_user(999999, "admin", "Admin", role="admin")
    
    await application_service.create_application(123456)
    
    result = await application_service.approve_application(123456, 999999)
    
    assert result is True
    
    application = await application_service.get_application(123456)
    assert application["status"] == "approved"
    assert application["admin_id"] == 999999


@pytest.mark.asyncio
async def test_reject_application(application_service, user_service):
    """Тест отклонения заявки"""
    await user_service.register_user(123456, "test_user", "Test User")
    await user_service.register_user(999999, "admin", "Admin", role="admin")
    
    await application_service.create_application(123456)
    
    result = await application_service.reject_application(123456, 999999)
    
    assert result is True
    
    application = await application_service.get_application(123456)
    assert application["status"] == "rejected"


@pytest.mark.asyncio
async def test_get_pending_applications(application_service, user_service):
    """Тест получения заявок на рассмотрении"""
    # Создаем несколько пользователей
    for i in range(1, 4):
        await user_service.register_user(i * 100, f"user{i}", f"User {i}")
        await application_service.create_application(i * 100)
    
    # Одобряем одну заявку
    await application_service.approve_application(100, 999999)
    
    # Получаем pending заявки
    pending = await application_service.get_pending_applications(limit=10, offset=0)
    
    assert len(pending) == 2


@pytest.mark.asyncio
async def test_count_pending_applications(application_service, user_service):
    """Тест подсчета заявок на рассмотрении"""
    # Создаем заявки
    for i in range(1, 6):
        await user_service.register_user(i * 100, f"user{i}", f"User {i}")
        await application_service.create_application(i * 100)
    
    count = await application_service.count_pending_applications()
    
    assert count == 5
    
    # Одобряем одну
    await application_service.approve_application(100, 999999)
    
    count = await application_service.count_pending_applications()
    
    assert count == 4

