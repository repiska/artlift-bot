"""Тесты для сервиса пользователей"""
import pytest
from bot.services.user_service import UserService


@pytest.mark.asyncio
async def test_register_user(user_service):
    """Тест регистрации пользователя"""
    result = await user_service.register_user(
        telegram_id=123456,
        username="test_user",
        full_name="Test User"
    )
    
    assert result is True


@pytest.mark.asyncio
async def test_get_user(user_service):
    """Тест получения пользователя"""
    await user_service.register_user(123456, "test_user", "Test User")
    
    user = await user_service.get_user(123456)
    
    assert user is not None
    assert user["telegram_id"] == 123456
    assert user["username"] == "test_user"


@pytest.mark.asyncio
async def test_get_nonexistent_user(user_service):
    """Тест получения несуществующего пользователя"""
    user = await user_service.get_user(999999)
    
    assert user is None


@pytest.mark.asyncio
async def test_is_admin(user_service):
    """Тест проверки администраторских прав"""
    admin_ids = [111111, 222222]
    
    # Пользователь в списке админов
    assert await user_service.is_admin(111111, admin_ids) is True
    
    # Пользователь не в списке админов
    assert await user_service.is_admin(999999, admin_ids) is False
    
    # Пользователь с ролью admin в БД
    await user_service.register_user(333333, "admin_user", "Admin User", role="admin")
    assert await user_service.is_admin(333333, admin_ids) is True

