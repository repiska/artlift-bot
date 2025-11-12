"""Handlers для администраторов"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from bot.keyboards.admin_keyboards import (
    get_admin_panel_keyboard,
    get_applications_list_keyboard,
    get_application_action_keyboard,
    get_messages_list_keyboard,
    get_message_edit_keyboard,
    get_message_edit_cancel_keyboard,
    get_message_edit_confirm_keyboard,
    get_message_history_keyboard,
    get_history_item_keyboard,
    get_questions_list_keyboard,
    get_question_action_keyboard
)
from bot.keyboards.user_keyboards import get_main_menu_keyboard
from bot.services.application_service import ApplicationService
from bot.services.notification_service import NotificationService
from bot.services.user_service import UserService
from bot.services.message_service import MessageService
from bot.services.question_service import QuestionService
from bot.utils.states import MessageEditStates, QuestionStates
from bot.middlewares.auth_middleware import is_admin
from bot.utils.telegram_utils import (
    answer_with_retry,
    edit_text_with_retry,
    bot_send_with_retry,
    bot_call_with_retry,
)
from config.settings import settings
from aiogram.fsm.context import FSMContext

router = Router()


async def check_admin_access(event: CallbackQuery | Message) -> bool:
    """Проверка прав администратора"""
    user_id = event.from_user.id
    if not is_admin(user_id):
        if isinstance(event, CallbackQuery):
            await event.answer("У вас нет прав администратора", show_alert=True)
        elif isinstance(event, Message):
            await answer_with_retry(event, "У вас нет прав администратора")
        return False
    return True


@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(
    callback: CallbackQuery,
    application_service: ApplicationService,
    question_service: QuestionService
):
    """Показ админ-панели"""
    if not await check_admin_access(callback):
        return
    
    pending_count = await application_service.count_pending_applications()
    pending_questions = await question_service.count_pending_questions()
    
    keyboard = get_admin_panel_keyboard(pending_count, pending_questions)
    
    admin_text = (
        "<b>⚙️ Админ-панель</b>\n\n"
        f"📋 Заявок на рассмотрении: <b>{pending_count}</b>\n"
        f"❓ Вопросов пользователей: <b>{pending_questions}</b>\n\n"
        "Выберите действие с помощью кнопок ниже."
    )
    
    await edit_text_with_retry(
        callback.message,
        admin_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await callback.answer()


@router.callback_query(F.data == "admin_pin_subscribe")
async def pin_channel_subscribe_message(
    callback: CallbackQuery,
    message_service: MessageService
):
    """Отправка и закрепление сообщения с кнопкой подписки в канале."""
    if not await check_admin_access(callback):
        return

    channel_target = settings.channel_target
    subscribe_url = settings.channel_subscribe_url

    if not channel_target:
        await callback.answer(
            "Не задан канал. Укажите CHANNEL_CHAT_ID или CHANNEL_USERNAME в настройках.",
            show_alert=True
        )
        return

    if not subscribe_url:
        await callback.answer(
            "Не задана ссылка для подписки. Укажите CHANNEL_SUBSCRIBE_URL или CHANNEL_USERNAME.",
            show_alert=True
        )
        return

    text = await message_service.get_message("channel_subscribe_message")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Заполнить анкету", url=subscribe_url)]
        ]
    )

    bot = callback.message.bot

    try:
        sent_message = await bot_send_with_retry(
            bot.send_message,
            channel_target,
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

        await bot_call_with_retry(
            bot.pin_chat_message,
            channel_target,
            sent_message.message_id,
            disable_notification=True,
            log_context=f"chat_id={channel_target}"
        )
    except Exception as exc:  # noqa: BLE001
        await callback.answer(
            f"Не удалось обновить закреп: {exc}",
            show_alert=True
        )
        return

    await callback.answer("Сообщение закреплено", show_alert=True)


@router.callback_query(F.data == "admin_applications")
async def show_applications_list(
    callback: CallbackQuery,
    application_service: ApplicationService,
    question_service: QuestionService
):
    """Показ списка заявок"""
    if not await check_admin_access(callback):
        return
    
    offset = 0
    limit = 10
    
    applications = await application_service.get_pending_applications(limit, offset)
    pending_questions = await question_service.count_pending_questions()
    
    if not applications:
        await edit_text_with_retry(
            callback.message,
            "Нет заявок на рассмотрении",
            reply_markup=get_admin_panel_keyboard(0, pending_questions)
        )
        await callback.answer()
        return
    
    keyboard, _ = get_applications_list_keyboard(applications, offset, limit)
    
    text = f"<b>📋 Заявки на рассмотрении ({len(applications)})</b>\n\nВыберите заявку:"
    
    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_applications_page_"))
async def show_applications_page(
    callback: CallbackQuery,
    application_service: ApplicationService
):
    """Пагинация списка заявок"""
    if not await check_admin_access(callback):
        return
    
    offset = int(callback.data.split("_")[-1])
    limit = 10
    
    applications = await application_service.get_pending_applications(limit, offset)
    
    if not applications:
        await callback.answer("Больше заявок нет")
        return
    
    keyboard, _ = get_applications_list_keyboard(applications, offset, limit)
    
    text = f"<b>📋 Заявки на рассмотрении</b>\n\nВыберите заявку:"
    
    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_view_application_"))
async def view_application(
    callback: CallbackQuery,
    application_service: ApplicationService,
    user_service: UserService
):
    """Просмотр конкретной заявки"""
    if not await check_admin_access(callback):
        return
    
    user_id = int(callback.data.split("_")[-1])
    
    application = await application_service.get_application(user_id)
    user = await user_service.get_user(user_id)
    
    if not application or not user:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    
    text = (
        "<b>📋 Заявка пользователя</b>\n\n"
        f"<b>Имя:</b> {user.get('full_name', 'Не указано')}\n"
        f"<b>Username:</b> @{user.get('username', 'не указан')}\n"
        f"<b>ID:</b> <code>{user_id}</code>\n"
        f"<b>Статус:</b> {application.get('status', 'unknown')}\n"
        f"<b>Дата создания:</b> {application.get('created_at', 'Не указано')}"
    )
    
    keyboard = get_application_action_keyboard(user_id)
    
    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_approve_"))
async def approve_application(
    callback: CallbackQuery,
    application_service: ApplicationService,
    notification_service: NotificationService,
    user_service: UserService
):
    """Одобрение заявки"""
    if not await check_admin_access(callback):
        return
    
    user_id = int(callback.data.split("_")[-1])
    admin_id = callback.from_user.id
    
    # Одобряем заявку
    await application_service.approve_application(user_id, admin_id)
    
    # Получаем данные пользователя
    user = await user_service.get_user(user_id)
    
    # Уведомляем пользователя
    await notification_service.notify_user_application_approved(
        user_id,
        user.get("full_name") if user else None
    )
    
    # Логируем действие (опционально)
    # db = Database(settings.DATABASE_PATH)
    # await db.log_admin_action(admin_id, "approve", user_id)
    
    await edit_text_with_retry(
        callback.message,
        f"✅ Заявка пользователя {user_id} одобрена. Уведомление отправлено."
    )
    await callback.answer("Заявка одобрена", show_alert=True)


@router.callback_query(F.data.startswith("admin_reject_"))
async def reject_application(
    callback: CallbackQuery,
    application_service: ApplicationService,
    notification_service: NotificationService,
    user_service: UserService
):
    """Отклонение заявки"""
    if not await check_admin_access(callback):
        return
    
    user_id = int(callback.data.split("_")[-1])
    admin_id = callback.from_user.id
    
    # Отклоняем заявку
    await application_service.reject_application(user_id, admin_id)
    
    # Получаем данные пользователя
    user = await user_service.get_user(user_id)
    
    # Уведомляем пользователя
    await notification_service.notify_user_application_rejected(
        user_id,
        user.get("full_name") if user else None
    )
    
    # Логируем действие (опционально)
    # db = Database(settings.DATABASE_PATH)
    # await db.log_admin_action(admin_id, "reject", user_id)
    
    await edit_text_with_retry(
        callback.message,
        f"❌ Заявка пользователя {user_id} отклонена. Уведомление отправлено."
    )
    await callback.answer("Заявка отклонена", show_alert=True)


@router.callback_query(F.data == "admin_stats")
async def show_stats(
    callback: CallbackQuery,
    application_service: ApplicationService,
    question_service: QuestionService
):
    """Показ статистики"""
    if not await check_admin_access(callback):
        return
    
    stats = await application_service.get_statistics()
    
    total_count = stats["total"]
    pending_count = stats["pending"]
    approved_count = stats["approved"]
    rejected_count = stats["rejected"]
    
    # Вычисляем процент одобрения (если есть обработанные заявки)
    processed = approved_count + rejected_count
    approval_rate = 0
    if processed > 0:
        approval_rate = round((approved_count / processed) * 100, 1)
    
    text = (
        "<b>📊 Статистика заявок</b>\n\n"
        f"📋 <b>Всего заявок:</b> {total_count}\n\n"
        f"⏳ <b>На рассмотрении:</b> {pending_count}\n"
        f"✅ <b>Одобрено:</b> {approved_count}\n"
        f"❌ <b>Отклонено:</b> {rejected_count}\n\n"
    )
    
    if processed > 0:
        text += (
            f"📈 <b>Процент одобрения:</b> {approval_rate}%\n"
            f"   (из {processed} обработанных заявок)"
        )
    
    pending_questions = await question_service.count_pending_questions()
    keyboard = get_admin_panel_keyboard(pending_count, pending_questions)
    
    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_messages")
async def show_messages_list(
    callback: CallbackQuery,
    message_service: MessageService,
    question_service: QuestionService
):
    """Показ списка сообщений для редактирования"""
    if not await check_admin_access(callback):
        return
    
    messages = await message_service.get_all_messages()
    pending_questions = await question_service.count_pending_questions()
    
    if not messages:
        await edit_text_with_retry(
        callback.message,
            "Нет доступных сообщений для редактирования",
            reply_markup=get_admin_panel_keyboard(0, pending_questions)
        )
        await callback.answer()
        return
    
    keyboard = get_messages_list_keyboard(messages)
    
    text = "<b>✏️ Редактирование сообщений</b>\n\nВыберите сообщение для редактирования:"
    
    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_message_"))
async def show_message_edit_menu(
    callback: CallbackQuery,
    message_service: MessageService
):
    """Показ меню редактирования сообщения"""
    if not await check_admin_access(callback):
        return
    
    message_key = callback.data.replace("admin_edit_message_", "")
    
    message_data = await message_service.db.get_message(message_key)
    
    if not message_data:
        await callback.answer("Сообщение не найдено", show_alert=True)
        return
    
    text = (
        f"<b>✏️ Редактирование: {message_key}</b>\n\n"
        f"<b>Описание:</b> {message_data.get('description', 'Без описания')}\n"
        f"<b>Обновлено:</b> {message_data.get('updated_at', 'Никогда')}\n\n"
        "Выберите действие:"
    )
    
    keyboard = get_message_edit_keyboard(message_key)
    
    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_message_view_"))
async def view_message_content(
    callback: CallbackQuery,
    message_service: MessageService
):
    """Просмотр текущего содержимого сообщения"""
    if not await check_admin_access(callback):
        return
    
    message_key = callback.data.replace("admin_message_view_", "")
    
    message_data = await message_service.db.get_message(message_key)
    
    if not message_data:
        await callback.answer("Сообщение не найдено", show_alert=True)
        return
    
    content = message_data.get("content", "")
    
    # Ограничиваем длину для показа
    if len(content) > 3000:
        content = content[:3000] + "\n\n... (текст обрезан, показываются первые 3000 символов)"
    
    text = (
        f"<b>👁️ Текущее содержимое: {message_key}</b>\n\n"
        f"<code>{content}</code>"
    )
    
    keyboard = get_message_edit_keyboard(message_key)
    
    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_message_edit_"))
async def start_message_edit(
    callback: CallbackQuery,
    state: FSMContext
):
    """Начало редактирования сообщения"""
    if not await check_admin_access(callback):
        return
    
    message_key = callback.data.replace("admin_message_edit_", "")
    
    # Сохраняем ключ сообщения в состоянии
    await state.update_data(message_key=message_key)
    await state.set_state(MessageEditStates.waiting_for_new_content)
    
    text = (
        f"<b>✏️ Редактирование: {message_key}</b>\n\n"
        "Отправьте новый текст сообщения.\n\n"
        "Используйте переменные:\n"
        "• <code>{name}</code> - имя пользователя\n"
        "• <code>{APPLICATION_FORM_URL}</code> - ссылка на анкету\n"
        "• <code>{PAYMENT_URL}</code> - ссылка на оплату\n"
        "• <code>{CONTACT_USERNAME}</code> - контакт для связи\n\n"
        "Дополнительное форматирование:\n"
        "• <code>[quote]...[/quote]</code> — цитата\n"
        "• <code>[quote collapse]...[/quote]</code> — свёрнутая цитата\n"
        "• <code>[b]...[/b]</code>, <code>[i]...[/i]</code>, <code>[u]...[/u]</code>, <code>[s]...[/s]</code>\n"
        "• <code>[code]...[/code]</code>, <code>[pre]...[/pre]</code>, <code>[spoiler]...[/spoiler]</code>\n"
        "• <code>[текст](https://example.com)</code> — ссылка\n\n"
    )
    
    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=get_message_edit_cancel_keyboard(message_key),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_message_cancel_"))
async def cancel_message_edit(
    callback: CallbackQuery,
    state: FSMContext,
    message_service: MessageService
):
    """Отмена редактирования сообщения"""
    if not await check_admin_access(callback):
        return

    message_key = callback.data.replace("admin_message_cancel_", "")
    await state.clear()

    message_data = await message_service.db.get_message(message_key)

    if not message_data:
        await callback.answer("Сообщение не найдено", show_alert=True)
        return

    text = (
        f"<b>✏️ Редактирование: {message_key}</b>\n\n"
        f"<b>Описание:</b> {message_data.get('description', 'Без описания')}\n"
        f"<b>Обновлено:</b> {message_data.get('updated_at', 'Никогда')}\n\n"
        "Выберите действие:"
    )
    keyboard = get_message_edit_keyboard(message_key)

    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer("Редактирование отменено")


@router.message(MessageEditStates.waiting_for_new_content)
async def save_message_content(
    message: Message,
    state: FSMContext,
    message_service: MessageService
):
    """Сохранение нового содержимого сообщения"""
    if not await check_admin_access(message):
        await state.clear()
        return
    
    data = await state.get_data()
    message_key = data.get("message_key")
    
    if not message_key:
        await answer_with_retry(message, "Ошибка: не найден ключ сообщения")
        await state.clear()
        return
    
    new_content = message.text
    
    if not new_content:
        await answer_with_retry(message, "Текст не может быть пустым")
        return
    
    # Сохраняем новый текст в состоянии для подтверждения
    await state.update_data(new_content=new_content)
    
    # Показываем превью и кнопки подтверждения
    preview = new_content[:500] + ("..." if len(new_content) > 500 else "")
    
    text = (
        f"<b>📝 Превью нового текста для {message_key}:</b>\n\n"
        f"<code>{preview}</code>\n\n"
        "Сохранить изменения?"
    )
    
    keyboard = get_message_edit_confirm_keyboard(message_key)
    
    await answer_with_retry(
        message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_message_save_"))
async def confirm_message_save(
    callback: CallbackQuery,
    state: FSMContext,
    message_service: MessageService
):
    """Подтверждение и сохранение изменений"""
    if not await check_admin_access(callback):
        await state.clear()
        return
    
    message_key = callback.data.replace("admin_message_save_", "")
    admin_id = callback.from_user.id
    
    data = await state.get_data()
    new_content = data.get("new_content")
    
    if not new_content:
        await callback.answer("Ошибка: не найден новый текст", show_alert=True)
        await state.clear()
        return
    
    # Сохраняем изменения
    await message_service.update_message(message_key, new_content, admin_id)
    
    # Логируем действие
    await message_service.db.log_admin_action(
        admin_id=admin_id,
        action_type=f"edit_message_{message_key}",
        user_id=None
    )
    
    await edit_text_with_retry(
        callback.message,
        f"✅ Сообщение <b>{message_key}</b> успешно обновлено!",
        parse_mode="HTML"
    )
    await callback.answer("Изменения сохранены", show_alert=True)
    
    await state.clear()


@router.message(Command("cancel"))
async def cancel_message_edit(
    message: Message,
    state: FSMContext
):
    """Отмена редактирования сообщения или ответа на вопрос"""
    if not await check_admin_access(message):
        return
    
    current_state = await state.get_state()
    
    if current_state == MessageEditStates.waiting_for_new_content:
        await state.clear()
        await answer_with_retry(message, "✅ Редактирование отменено")
    elif current_state == QuestionStates.waiting_for_answer:
        await state.clear()
        await answer_with_retry(message, "✅ Ответ на вопрос отменен")


@router.callback_query(F.data.startswith("admin_message_history_"))
async def show_message_history(
    callback: CallbackQuery,
    message_service: MessageService
):
    """Показ истории версий сообщения"""
    if not await check_admin_access(callback):
        return
    
    message_key = callback.data.replace("admin_message_history_", "")
    
    history = await message_service.get_message_history(message_key, limit=10)
    
    if not history:
        await edit_text_with_retry(
        callback.message,
            f"<b>📜 История версий: {message_key}</b>\n\n"
            "История версий пуста. Это первая версия сообщения.",
            reply_markup=get_message_edit_keyboard(message_key),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    text = (
        f"<b>📜 История версий: {message_key}</b>\n\n"
        f"Найдено версий: <b>{len(history)}</b>\n\n"
        "Выберите версию для просмотра или восстановления:"
    )
    
    keyboard = get_message_history_keyboard(message_key, history)
    
    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_history_view_"))
async def view_history_item(
    callback: CallbackQuery,
    message_service: MessageService
):
    """Просмотр конкретной версии из истории"""
    if not await check_admin_access(callback):
        return
    
    history_id = int(callback.data.replace("admin_history_view_", ""))
    
    history_item = await message_service.get_history_item(history_id)
    
    if not history_item:
        await callback.answer("Версия не найдена", show_alert=True)
        return
    
    content = history_item.get("content", "")
    created_at = history_item.get("created_at", "Неизвестно")
    message_key = history_item.get("message_key", "unknown")
    
    # Ограничиваем длину для показа
    if len(content) > 3000:
        content_preview = content[:3000] + "\n\n... (текст обрезан)"
    else:
        content_preview = content
    
    text = (
        f"<b>📄 Версия из истории: {message_key}</b>\n\n"
        f"<b>Создано:</b> {created_at}\n\n"
        f"<b>Содержимое:</b>\n<code>{content_preview}</code>"
    )
    
    keyboard = get_history_item_keyboard(message_key, history_id)
    
    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_history_restore_"))
async def restore_from_history(
    callback: CallbackQuery,
    message_service: MessageService
):
    """Восстановление сообщения из истории"""
    if not await check_admin_access(callback):
        return
    
    history_id = int(callback.data.replace("admin_history_restore_", ""))
    admin_id = callback.from_user.id
    
    history_item = await message_service.get_history_item(history_id)
    
    if not history_item:
        await callback.answer("Версия не найдена", show_alert=True)
        return
    
    message_key = history_item.get("message_key")
    
    # Восстанавливаем версию
    success = await message_service.restore_message_from_history(history_id, admin_id)
    
    if success:
        # Логируем действие
        await message_service.db.log_admin_action(
            admin_id=admin_id,
            action_type=f"restore_message_{message_key}_from_history_{history_id}",
            user_id=None
        )
        
        await edit_text_with_retry(
        callback.message,
            f"✅ Сообщение <b>{message_key}</b> восстановлено из истории!",
            parse_mode="HTML"
        )
        await callback.answer("Версия восстановлена", show_alert=True)
    else:
        await callback.answer("Ошибка при восстановлении", show_alert=True)


@router.callback_query(F.data.startswith("admin_history_delete_"))
async def delete_history_item(
    callback: CallbackQuery,
    message_service: MessageService
):
    """Удаление элемента из истории"""
    if not await check_admin_access(callback):
        return
    
    history_id = int(callback.data.replace("admin_history_delete_", ""))
    
    history_item = await message_service.get_history_item(history_id)
    
    if not history_item:
        await callback.answer("Версия не найдена", show_alert=True)
        return
    
    message_key = history_item.get("message_key")
    
    # Удаляем из истории
    success = await message_service.delete_history_item(history_id)
    
    if success:
        # Возвращаемся к истории
        history = await message_service.get_message_history(message_key, limit=10)
        
        if not history:
            await edit_text_with_retry(
        callback.message,
                f"<b>📜 История версий: {message_key}</b>\n\n"
                "История версий пуста.",
                reply_markup=get_message_edit_keyboard(message_key),
                parse_mode="HTML"
            )
        else:
            text = (
                f"<b>📜 История версий: {message_key}</b>\n\n"
                f"Найдено версий: <b>{len(history)}</b>\n\n"
                "Выберите версию для просмотра или восстановления:"
            )
            keyboard = get_message_history_keyboard(message_key, history)
            await edit_text_with_retry(
        callback.message,
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        
        await callback.answer("Элемент удален из истории", show_alert=True)
    else:
        await callback.answer("Ошибка при удалении", show_alert=True)


@router.callback_query(F.data == "admin_questions")
async def show_questions_list(
    callback: CallbackQuery,
    question_service: QuestionService
):
    """Показ списка вопросов пользователей"""
    if not await check_admin_access(callback):
        return
    
    offset = 0
    limit = 10
    
    questions = await question_service.get_pending_questions(limit, offset)
    
    if not questions:
        pending_questions = await question_service.count_pending_questions()
        await edit_text_with_retry(
        callback.message,
            "✅ Нет неотвеченных вопросов",
            reply_markup=get_admin_panel_keyboard(0, pending_questions)
        )
        await callback.answer()
        return
    
    keyboard = get_questions_list_keyboard(questions, offset, limit)
    
    text = f"<b>❓ Вопросы пользователей ({len(questions)})</b>\n\nВыберите вопрос для ответа:"
    
    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_questions_page_"))
async def show_questions_page(
    callback: CallbackQuery,
    question_service: QuestionService
):
    """Пагинация списка вопросов"""
    if not await check_admin_access(callback):
        return
    
    offset = int(callback.data.split("_")[-1])
    limit = 10
    
    questions = await question_service.get_pending_questions(limit, offset)
    
    if not questions:
        await callback.answer("Больше вопросов нет")
        return
    
    keyboard = get_questions_list_keyboard(questions, offset, limit)
    
    text = f"<b>❓ Вопросы пользователей</b>\n\nВыберите вопрос для ответа:"
    
    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_view_question_"))
async def view_question(
    callback: CallbackQuery,
    question_service: QuestionService
):
    """Просмотр конкретного вопроса"""
    if not await check_admin_access(callback):
        return
    
    question_id = int(callback.data.split("_")[-1])
    
    question = await question_service.get_question(question_id)
    
    if not question:
        await callback.answer("Вопрос не найден", show_alert=True)
        return
    
    user_name = question.get("full_name") or question.get("username") or "Неизвестно"
    question_text = question.get("question_text", "Вопрос не указан")
    created_at = question.get("created_at", "Неизвестно")
    
    text = (
        "<b>❓ Вопрос от пользователя</b>\n\n"
        f"<b>Пользователь:</b> {user_name}\n"
        f"<b>ID:</b> <code>{question.get('user_id')}</code>\n"
        f"<b>Дата:</b> {created_at}\n\n"
        f"<b>Вопрос:</b>\n{question_text}"
    )
    
    keyboard = get_question_action_keyboard(question_id)
    
    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_answer_question_"))
async def start_answering_question(
    callback: CallbackQuery,
    state: FSMContext,
    question_service: QuestionService
):
    """Начало ответа на вопрос"""
    if not await check_admin_access(callback):
        return
    
    question_id = int(callback.data.split("_")[-1])
    
    question = await question_service.get_question(question_id)
    
    if not question:
        await callback.answer("Вопрос не найден", show_alert=True)
        return
    
    # Сохраняем ID вопроса в состоянии
    await state.update_data(question_id=question_id)
    await state.set_state(QuestionStates.waiting_for_answer)
    
    user_name = question.get("full_name") or question.get("username") or "Неизвестно"
    question_text = question.get("question_text", "")
    
    text = (
        f"<b>💬 Ответ на вопрос от {user_name}</b>\n\n"
        f"<b>Вопрос:</b>\n{question_text}\n\n"
        "Отправьте ваш ответ пользователю.\n"
        "Или отправьте /cancel для отмены."
    )
    
    await edit_text_with_retry(
        callback.message,
        text,
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(QuestionStates.waiting_for_answer)
async def save_answer_to_question(
    message: Message,
    state: FSMContext,
    question_service: QuestionService,
    notification_service: NotificationService
):
    """Сохранение ответа на вопрос"""
    if not await check_admin_access(message):
        await state.clear()
        return
    
    data = await state.get_data()
    question_id = data.get("question_id")
    
    if not question_id:
        await answer_with_retry(message, "Ошибка: не найден ID вопроса")
        await state.clear()
        return
    
    answer_text = message.text
    
    if not answer_text:
        await answer_with_retry(message, "Ответ не может быть пустым")
        return
    
    admin_id = message.from_user.id
    
    # Получаем вопрос для отправки ответа пользователю
    question = await question_service.get_question(question_id)
    
    if not question:
        await answer_with_retry(message, "Вопрос не найден")
        await state.clear()
        return
    
    user_id = question.get("user_id")
    
    # Сохраняем ответ
    await question_service.answer_question(question_id, admin_id, answer_text)
    
    # Отправляем ответ пользователю
    try:
        await bot_send_with_retry(
            notification_service.bot.send_message,
            user_id,
            f"💬 <b>Ответ на ваш вопрос:</b>\n\n{answer_text}",
            parse_mode="HTML"
        )
        await answer_with_retry(
            message,
            f"✅ Ответ отправлен пользователю (ID: {user_id})",
            parse_mode="HTML"
        )
    except Exception as exc:  # noqa: BLE001
        await answer_with_retry(
            message,
            f"⚠️ Ответ сохранен, но не удалось отправить пользователю: {exc}"
        )
    
    # Логируем действие
    await question_service.db.log_admin_action(
        admin_id=admin_id,
        action_type=f"answer_question_{question_id}",
        user_id=user_id
    )
    
    await state.clear()