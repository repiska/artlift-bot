"""Сервис для отправки уведомлений"""

import logging
from typing import Optional

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.models import Database
from bot.services.message_service import MessageService
from bot.utils.telegram_utils import bot_send_with_retry
from config.settings import settings


logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис отправки уведомлений"""
    
    def __init__(self, bot: Bot, db: Database, message_service: Optional[MessageService] = None):
        self.bot = bot
        self.db = db
        self.message_service = message_service
    
    async def notify_admin_new_application(
        self,
        user_id: int,
        username: Optional[str],
        full_name: Optional[str]
    ) -> bool:
        """Уведомление админа о новой заявке"""
        message = (
            "🔔 <b>Новая заявка!</b>\n\n"
            f"Пользователь: {full_name or 'Не указано'}\n"
            f"Username: @{username or 'не указан'}\n"
            f"ID: <code>{user_id}</code>"
        )
        
        for admin_id in settings.ADMIN_IDS:
            try:
                await bot_send_with_retry(
                    self.bot.send_message,
                    admin_id,
                    message,
                    parse_mode="HTML",
                )
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Не удалось отправить уведомление о новой заявке админу %s", admin_id
                )
        
        return True
    
    async def notify_admin_user_question(
        self,
        user_id: int,
        username: Optional[str],
        full_name: Optional[str],
        question_text: Optional[str] = None
    ) -> bool:
        """Уведомление админа о вопросе пользователя"""
        question_preview = ""
        if question_text:
            if len(question_text) > 100:
                question_preview = question_text[:100] + "..."
            else:
                question_preview = question_text
            question_preview = f"\n\n<b>Вопрос:</b>\n{question_preview}"
        
        message = (
            "❓ <b>Новый вопрос от пользователя</b>\n\n"
            f"Пользователь: {full_name or 'Не указано'}\n"
            f"Username: @{username or 'не указан'}\n"
            f"ID: <code>{user_id}</code>{question_preview}\n\n"
            "Просмотрите вопрос в админ-панели."
        )
        
        for admin_id in settings.ADMIN_IDS:
            try:
                await bot_send_with_retry(
                    self.bot.send_message,
                    admin_id,
                    message,
                    parse_mode="HTML",
                )
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Не удалось отправить уведомление о вопросе админу %s", admin_id
                )
        
        return True
    
    async def notify_user_application_approved(
        self,
        user_id: int,
        full_name: Optional[str],
        keyboard: Optional[InlineKeyboardMarkup] = None
    ) -> bool:
        """Уведомление пользователя об одобрении заявки"""
        name = full_name or "друг/подруга"
        
        # Получаем сообщение из базы данных, если доступен MessageService
        if self.message_service:
            message = await self.message_service.get_message("application_approved", name=name)
        else:
            # Fallback на хардкод, если MessageService не доступен
            message = (
                f"{name}, спасибо за вашу заявку!\n\n"
                "Мы очарованы вашими работами и рады пригласить вас в закрытое комьюнити Art Lift!\n\n"
                "<b>Стоимость:</b>\n"
                "• Первый месяц со скидкой — 2 500 ₽\n"
                "• Последующие месяцы — 5 000 ₽\n\n"
                "Оплата проходит через сервис @tribute:\n"
                f"👉 {settings.PAYMENT_URL}\n\n"
                "После оплаты вы автоматически получите доступ к сообществу.\n\n"
                "Как войдёте в комьюнити — представьтесь, пожалуйста, и подключайтесь к ближайшим мероприятиям!\n\n"
                "Остались вопросы? С радостью ответим!"
            )
        
        try:
            await bot_send_with_retry(
                self.bot.send_message,
                user_id,
                message,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            return True
        except Exception:  # noqa: BLE001
            logger.exception(
                "Не удалось отправить уведомление об одобрении пользователю %s", user_id
            )
            return False
    
    async def notify_user_application_rejected(
        self,
        user_id: int,
        full_name: Optional[str],
        keyboard: Optional[InlineKeyboardMarkup] = None
    ) -> bool:
        """Уведомление пользователя об отказе в заявке"""
        name = full_name or "друг/подруга"
        
        # Получаем сообщение из базы данных, если доступен MessageService
        if self.message_service:
            message = await self.message_service.get_message("application_rejected", name=name)
        else:
            # Fallback на хардкод, если MessageService не доступен
            message = (
                f"Здравствуйте, {name}!\n\n"
                "Благодарим вас за заявку в Art Lift Community и за то, что поделились своими работами.\n\n"
                "К сожалению, сейчас мы не готовы пригласить вас в закрытое комьюнити — мы следим за тем, "
                "чтобы участники в сообществе были приблизительно одного уровня.\n\n"
                "Но мы будем очень рады видеть вас позже! А пока предлагаем другие форматы сотрудничества:\n\n"
                "<b>1. Индивидуальная консультация</b>\n\n"
                "Мы предварительно изучаем ваши материалы и подстраиваем встречу под ваш запрос.\n\n"
                "<b>Консультация включает:</b>\n"
                "• Анализ вашей ситуации и портфолио\n"
                "• Конкретные рекомендации по подаче на опен-коллы\n"
                "• Обсуждение направлений развития\n"
                "• Поддерживающий диалог\n\n"
                "<b>Стоимость:</b> от 8 000 ₽ (60 мин)\n"
                "Зависит от запроса и продолжительности.\n\n\n"
                "<b>2. Менторство</b>\n\n"
                "Гораздо более глубокая индивидуальная работа с экспертом более высокого уровня, чем сопровождение.\n\n"
                "Это работа как с практикой художника, так и с подбором галерей и сменой ориентиров в художественном поле. "
                "И, самое главное, — регулярные живые сессии в Zoom/Google Meet/Telegram.\n\n"
                "<b>Стоимость:</b>\n"
                "Разброс цен очень большой — всё зависит от специфики запроса и самого ментора.\n\n"
                f"Остались вопросы? Пишите {settings.CONTACT_USERNAME} — подберём услугу и вышлем актуальный план по менторам 💬"
            )
        
        try:
            await bot_send_with_retry(
                self.bot.send_message,
                user_id,
                message,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            return True
        except Exception:  # noqa: BLE001
            logger.exception(
                "Не удалось отправить уведомление об отказе пользователю %s", user_id
            )
            return False
    
    async def send_reminder(self, user_id: int, message: str) -> bool:
        """Отправка напоминания пользователю"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Нет, заполнить",
                        url=settings.APPLICATION_FORM_URL
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Да, заполнил(а)",
                        callback_data="application_filled"
                    )
                ],
            ]
        )

        try:
            await bot_send_with_retry(
                self.bot.send_message,
                user_id,
                message,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            return True
        except Exception:  # noqa: BLE001
            logger.exception(
                "Не удалось отправить напоминание пользователю %s", user_id
            )
            return False

