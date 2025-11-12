"""Тесты для клавиатур"""
import pytest
from bot.keyboards.user_keyboards import (
    get_start_keyboard,
    get_after_form_keyboard,
    get_main_menu_keyboard
)
from bot.keyboards.admin_keyboards import (
    get_admin_panel_keyboard,
    get_applications_list_keyboard,
    get_application_action_keyboard
)


def test_get_start_keyboard():
    """Тест создания стартовой клавиатуры"""
    keyboard = get_start_keyboard(include_admin_panel=False)
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0


def test_get_start_keyboard_with_admin():
    """Тест создания стартовой клавиатуры с админ-панелью"""
    keyboard = get_start_keyboard(include_admin_panel=True)
    
    assert keyboard is not None
    # Должна быть кнопка админ-панели
    admin_button = any(
        button.callback_data == "admin_panel"
        for row in keyboard.inline_keyboard
        for button in row
    )
    assert admin_button is True


def test_get_after_form_keyboard():
    """Тест создания клавиатуры после формы"""
    keyboard = get_after_form_keyboard()
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0


def test_get_admin_panel_keyboard():
    """Тест создания админ-панели"""
    keyboard = get_admin_panel_keyboard(pending_count=5)
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0


def test_get_applications_list_keyboard():
    """Тест создания списка заявок"""
    applications = [
        {"user_id": 111, "full_name": "User 1", "username": "user1"},
        {"user_id": 222, "full_name": "User 2", "username": "user2"},
    ]
    
    keyboard, returned_apps = get_applications_list_keyboard(applications, offset=0, limit=10)
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0
    assert len(returned_apps) == 2


def test_get_application_action_keyboard():
    """Тест создания клавиатуры действий с заявкой"""
    keyboard = get_application_action_keyboard(user_id=123456)
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0
    
    # Проверяем наличие кнопок одобрения и отклонения
    has_approve = any(
        "admin_approve_123456" in button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
    )
    has_reject = any(
        "admin_reject_123456" in button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
    )
    
    assert has_approve is True
    assert has_reject is True

