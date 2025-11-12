"""Клавиатуры для администраторов"""
from typing import Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_panel_keyboard(pending_count: int = 0, pending_questions: int = 0) -> InlineKeyboardMarkup:
    """Главная панель администратора"""
    buttons = [
        [InlineKeyboardButton(
            text=f"📋 Заявки на рассмотрении ({pending_count})",
            callback_data="admin_applications"
        )],
        [InlineKeyboardButton(
            text=f"❓ Вопросы пользователей ({pending_questions})",
            callback_data="admin_questions"
        )],
        [InlineKeyboardButton(
            text="📊 Статистика",
            callback_data="admin_stats"
        )],
        [InlineKeyboardButton(
            text="✏️ Редактировать сообщения",
            callback_data="admin_messages"
        )],
        [InlineKeyboardButton(
            text="📌 Обновить закреп",
            callback_data="admin_pin_subscribe"
        )],
        [InlineKeyboardButton(
            text="◀️ Вернуться в меню",
            callback_data="main_menu"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_applications_list_keyboard(
    applications: list,
    offset: int = 0,
    limit: int = 10
) -> Tuple[InlineKeyboardMarkup, list]:
    """Клавиатура со списком заявок"""
    buttons = []
    
    for app in applications:
        user_name = app.get("full_name") or app.get("username") or "Неизвестно"
        user_id = app.get("user_id")
        buttons.append([InlineKeyboardButton(
            text=f"👤 {user_name} (ID: {user_id})",
            callback_data=f"admin_view_application_{user_id}"
        )])
    
    # Пагинация
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"admin_applications_page_{offset - limit}"
        ))
    
    if len(applications) == limit:
        nav_buttons.append(InlineKeyboardButton(
            text="Вперед ▶️",
            callback_data=f"admin_applications_page_{offset + limit}"
        ))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(
        text="◀️ Назад в админ-панель",
        callback_data="admin_panel"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons), applications


def get_application_action_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для действий с заявкой"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Одобрить",
                callback_data=f"admin_approve_{user_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"admin_reject_{user_id}"
            )
        ],
        [InlineKeyboardButton(
            text="◀️ Назад к заявкам",
            callback_data="admin_applications"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_messages_list_keyboard(messages: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком сообщений для редактирования"""
    buttons = []
    
    for msg in messages:
        key = msg.get("message_key", "unknown")
        description = msg.get("description", "Без описания")
        buttons.append([InlineKeyboardButton(
            text=f"✏️ {key} - {description}",
            callback_data=f"admin_edit_message_{key}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="◀️ Назад в админ-панель",
        callback_data="admin_panel"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_message_edit_keyboard(message_key: str) -> InlineKeyboardMarkup:
    """Клавиатура для редактирования сообщения"""
    buttons = [
        [InlineKeyboardButton(
            text="✏️ Редактировать текст",
            callback_data=f"admin_message_edit_{message_key}"
        )],
        [InlineKeyboardButton(
            text="👁️ Просмотреть текущий текст",
            callback_data=f"admin_message_view_{message_key}"
        )],
        [InlineKeyboardButton(
            text="📜 История версий",
            callback_data=f"admin_message_history_{message_key}"
        )],
        [InlineKeyboardButton(
            text="◀️ Назад к сообщениям",
            callback_data="admin_messages"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_message_edit_cancel_keyboard(message_key: str) -> InlineKeyboardMarkup:
    """Клавиатура отмены редактирования сообщения"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="❌ Отменить редактирование",
                callback_data=f"admin_message_cancel_{message_key}"
            )],
            [InlineKeyboardButton(
                text="◀️ Назад к действиям",
                callback_data=f"admin_edit_message_{message_key}"
            )]
        ]
    )


def get_message_edit_confirm_keyboard(message_key: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения редактирования"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Сохранить",
                callback_data=f"admin_message_save_{message_key}"
            ),
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=f"admin_edit_message_{message_key}"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_message_history_keyboard(message_key: str, history: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком версий из истории"""
    buttons = []
    
    for item in history[:10]:  # Показываем до 10 версий
        history_id = item.get("id")
        created_at = item.get("created_at", "Неизвестно")
        # Обрезаем дату для краткости
        if isinstance(created_at, str) and len(created_at) > 19:
            created_at = created_at[:19]
        
        # Показываем первые 30 символов содержимого
        content_preview = item.get("content", "")[:30].replace("\n", " ")
        if len(item.get("content", "")) > 30:
            content_preview += "..."
        
        buttons.append([InlineKeyboardButton(
            text=f"📄 {created_at} - {content_preview}",
            callback_data=f"admin_history_view_{history_id}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="◀️ Назад к сообщению",
        callback_data=f"admin_edit_message_{message_key}"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_history_item_keyboard(message_key: str, history_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для элемента истории"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Восстановить эту версию",
                callback_data=f"admin_history_restore_{history_id}"
            )
        ],
        [InlineKeyboardButton(
            text="🗑️ Удалить из истории",
            callback_data=f"admin_history_delete_{history_id}"
        )],
        [InlineKeyboardButton(
            text="◀️ Назад к истории",
            callback_data=f"admin_message_history_{message_key}"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
def get_questions_list_keyboard(
    questions: list,
    offset: int = 0,
    limit: int = 10
) -> InlineKeyboardMarkup:
    """Клавиатура со списком вопросов"""
    buttons = []
    
    for question in questions:
        user_name = question.get("full_name") or question.get("username") or "Неизвестно"
        question_id = question.get("id")
        question_text = question.get("question_text", "")[:30]
        if len(question.get("question_text", "")) > 30:
            question_text += "..."
        
        buttons.append([InlineKeyboardButton(
            text=f"❓ {user_name}: {question_text}",
            callback_data=f"admin_view_question_{question_id}"
        )])
    
    # Пагинация
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"admin_questions_page_{offset - limit}"
        ))
    
    if len(questions) == limit:
        nav_buttons.append(InlineKeyboardButton(
            text="Вперед ▶️",
            callback_data=f"admin_questions_page_{offset + limit}"
        ))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(
        text="◀️ Назад в админ-панель",
        callback_data="admin_panel"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_question_action_keyboard(question_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для действий с вопросом"""
    buttons = [
        [InlineKeyboardButton(
            text="💬 Ответить на вопрос",
            callback_data=f"admin_answer_question_{question_id}"
        )],
        [InlineKeyboardButton(
            text="◀️ Назад к вопросам",
            callback_data="admin_questions"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

