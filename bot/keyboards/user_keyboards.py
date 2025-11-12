"""Клавиатуры для пользователей"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import settings


def get_start_keyboard(include_admin_panel: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для команды /start"""
    buttons = [
        [InlineKeyboardButton(
            text="📝 Заполнить анкету",
            callback_data="fill_form"
        )],
        [InlineKeyboardButton(
            text="❓ Задать вопрос",
            callback_data="user_question"
        )]
    ]

    if include_admin_panel:
        buttons.append([InlineKeyboardButton(
            text="⚙️ Админ-панель",
            callback_data="admin_panel"
        )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_form_keyboard(include_admin_panel: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура после отправки ссылки на анкету"""
    buttons = [
        [InlineKeyboardButton(
            text="📝 Открыть анкету",
            url=settings.APPLICATION_FORM_URL
        )],
        [InlineKeyboardButton(
            text="✅ Я заполнил(а) анкету",
            callback_data="application_filled"
        )],
        [InlineKeyboardButton(
            text="❓ Задать вопрос",
            callback_data="user_question"
        )],
        [InlineKeyboardButton(
            text="◀️ Вернуться в меню",
            callback_data="main_menu"
        )]
    ]

    if include_admin_panel:
        buttons.append([InlineKeyboardButton(
            text="⚙️ Админ-панель",
            callback_data="admin_panel"
        )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_menu_keyboard(include_admin_panel: bool = False) -> InlineKeyboardMarkup:
    """Главное меню"""
    buttons = [
        [InlineKeyboardButton(
            text="📝 Заполнить анкету",
            callback_data="fill_form"
        )],
        [InlineKeyboardButton(
            text="❓ Задать вопрос",
            callback_data="user_question"
        )],
        [InlineKeyboardButton(
            text="📄 FAQ",
            callback_data="faq"
        )]
    ]

    if include_admin_panel:
        buttons.append([InlineKeyboardButton(
            text="⚙️ Админ-панель",
            callback_data="admin_panel"
        )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_menu_keyboard(include_admin_panel: bool = False) -> InlineKeyboardMarkup:
    """Кнопка возврата в меню"""
    buttons = [
        [InlineKeyboardButton(
            text="◀️ Вернуться в меню",
            callback_data="main_menu"
        )]
    ]
    
    if include_admin_panel:
        buttons.append([InlineKeyboardButton(
            text="⚙️ Админ-панель",
            callback_data="admin_panel"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)