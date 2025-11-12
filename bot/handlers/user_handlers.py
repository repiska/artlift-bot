"""Handlers для пользователей"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.keyboards.user_keyboards import (
    get_start_keyboard,
    get_after_form_keyboard,
    get_main_menu_keyboard,
    get_back_to_menu_keyboard
)
from bot.services.user_service import UserService
from bot.services.application_service import ApplicationService
from bot.services.notification_service import NotificationService
from bot.services.reminder_service import ReminderService
from bot.services.message_service import MessageService
from bot.services.question_service import QuestionService
from bot.utils.states import ApplicationStates, QuestionStates
from bot.middlewares.auth_middleware import is_admin
from bot.utils.telegram_utils import answer_with_retry, edit_text_with_retry

router = Router()


@router.message(Command("start"))
async def cmd_start(
    message: Message,
    user_service: UserService,
    reminder_service: ReminderService,
    message_service: MessageService,
    application_service: ApplicationService = None,
    question_service: QuestionService = None
):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    # Регистрируем пользователя
    await user_service.register_user(user_id, username, full_name)
    
    # Получаем приветственное сообщение из базы
    welcome_text = await message_service.get_message("welcome")
    
    keyboard = get_start_keyboard(include_admin_panel=is_admin(user_id))
    
    await answer_with_retry(
        message,
        welcome_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Планируем напоминания
    reminder_service.schedule_reminders(user_id)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Обработчик команды /cancel"""
    current_state = await state.get_state()
    
    if current_state == ApplicationStates.waiting_for_confirmation:
        await state.clear()
        await answer_with_retry(message, "✅ Действие отменено")
    elif current_state == QuestionStates.waiting_for_question:
        await state.clear()
        await answer_with_retry(message, "✅ Ввод вопроса отменен")


@router.callback_query(F.data == "fill_form")
async def handle_fill_form(callback: CallbackQuery):
    """Инструкция после выбора заполнения анкеты"""
    user_id = callback.from_user.id

    text = (
        "Спасибо! 🙏\n\n"
        "Откройте анкету по кнопке ниже и заполните её. Как только закончите, нажмите кнопку «Я заполнил(а) анкету», и мы рассмотрим вашу заявку очень скоро."
    )

    keyboard = get_after_form_keyboard(include_admin_panel=is_admin(user_id))

    await answer_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "application_filled")
async def handle_application_filled(
    callback: CallbackQuery,
    application_service: ApplicationService,
    notification_service: NotificationService,
    reminder_service: ReminderService,
    user_service: UserService,
    message_service: MessageService
):
    """Обработчик подтверждения заполнения анкеты"""
    user_id = callback.from_user.id
    
    # Отменяем напоминания
    await reminder_service.cancel_user_reminders(user_id)
    
    # Создаем заявку
    await application_service.create_application(user_id)
    
    # Получаем данные пользователя
    user = await user_service.get_user(user_id)
    
    # Уведомляем админа
    await notification_service.notify_admin_new_application(
        user_id,
        user.get("username") if user else callback.from_user.username,
        user.get("full_name") if user else callback.from_user.full_name
    )
    
    # Получаем ответ из базы данных
    response_text = await message_service.get_message("application_filled_response")
    
    keyboard = get_main_menu_keyboard(include_admin_panel=is_admin(user_id))
    
    await edit_text_with_retry(
        callback.message,
        response_text,
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "user_question")
async def handle_user_question(
    callback: CallbackQuery,
    state: FSMContext,
    notification_service: NotificationService,
    user_service: UserService,
    message_service: MessageService,
    question_service: QuestionService
):
    """Обработчик вопроса пользователя"""
    user_id = callback.from_user.id
    
    # Сохраняем состояние для ввода вопроса
    await state.set_state(QuestionStates.waiting_for_question)
    
    text = (
        "Напишите свой вопрос в этом чате, и наш менеджер вскоре даст подробный ответ.\n\n"
        "Мы стараемся отвечать максимально быстро 👌\n\n"
        "Если хотите отменить ввод — отправьте /cancel."
    )

    keyboard = get_back_to_menu_keyboard(include_admin_panel=is_admin(user_id))

    await edit_text_with_retry(
        callback.message,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(QuestionStates.waiting_for_question)
async def save_user_question(
    message: Message,
    state: FSMContext,
    notification_service: NotificationService,
    user_service: UserService,
    message_service: MessageService,
    question_service: QuestionService
):
    """Сохранение вопроса пользователя"""
    # Пропускаем команды (они обрабатываются отдельным handler)
    if message.text and message.text.startswith("/"):
        return
    
    user_id = message.from_user.id
    question_text = message.text
    
    if not question_text:
        await answer_with_retry(message, "Вопрос не может быть пустым")
        return
    
    # Создаем вопрос в БД
    question_id = await question_service.create_question(user_id, question_text)
    
    # Получаем данные пользователя
    user = await user_service.get_user(user_id)
    
    # Уведомляем админа
    await notification_service.notify_admin_user_question(
        user_id,
        user.get("username") if user else message.from_user.username,
        user.get("full_name") if user else message.from_user.full_name,
        question_text
    )
    
    # Получаем ответ из базы данных
    response_text = await message_service.get_message("user_question_response")
    
    keyboard = get_main_menu_keyboard(include_admin_panel=is_admin(user_id))
    
    await answer_with_retry(
        message,
        response_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await state.clear()

