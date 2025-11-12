"""Общие handlers"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.keyboards.user_keyboards import (
    get_main_menu_keyboard,
    get_back_to_menu_keyboard
)
from bot.services.message_service import MessageService
from bot.utils.telegram_utils import answer_with_retry, edit_text_with_retry
from bot.middlewares.auth_middleware import is_admin

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await answer_with_retry(
        message,
        "Используйте /start для начала работы с ботом."
    )


@router.callback_query(F.data == "faq")
async def show_faq(callback: CallbackQuery, message_service: MessageService):
    """Показ FAQ"""
    faq_text = await message_service.get_message("faq")
    
    keyboard = get_back_to_menu_keyboard(include_admin_panel=is_admin(callback.from_user.id))
    
    await edit_text_with_retry(
        callback.message,
        faq_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def main_menu(
    callback: CallbackQuery,
    state: FSMContext,
    message_service: MessageService
):
    """Возврат в главное меню"""
    await state.clear()

    keyboard = get_main_menu_keyboard(include_admin_panel=is_admin(callback.from_user.id))
    menu_text = await message_service.get_message("main_menu")

    await edit_text_with_retry(
        callback.message,
        menu_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

