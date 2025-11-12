"""Сервис для управления напоминаниями"""
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.database.models import Database
from bot.services.notification_service import NotificationService
from config.settings import settings


class ReminderService:
    """Сервис управления напоминаниями"""
    
    def __init__(
        self,
        scheduler: AsyncIOScheduler,
        db: Database,
        notification_service: NotificationService
    ):
        self.scheduler = scheduler
        self.db = db
        self.notification_service = notification_service
    
    def schedule_reminders(self, user_id: int):
        """Планирование напоминаний для пользователя"""
        # Отменяем старые напоминания если есть
        # (через cancel_user_reminders при подтверждении)
        
        now = datetime.now()

        reminder_time = now + timedelta(days=1)
        reminder_message = (
            "⏰ Привет! Прошли сутки с момента, как вы собирались заполнить анкету "
            "в Art Lift Community.\n\n"
            "Удалось ли уже отправить её? Если нет — самое время сделать это."
        )

        self._schedule_single_reminder(
            user_id,
            "1d",
            reminder_time,
            reminder_message
        )
    
    def _schedule_single_reminder(
        self,
        user_id: int,
        reminder_type: str,
        scheduled_at: datetime,
        message: str
    ) -> str:
        """Планирование одного напоминания"""
        job_id = f"reminder_{user_id}_{reminder_type}_{scheduled_at.timestamp()}"
        
        # Сохраняем в БД
        # await self.db.create_reminder(user_id, reminder_type, scheduled_at)
        
        # Планируем задачу
        self.scheduler.add_job(
            self._send_reminder,
            'date',
            run_date=scheduled_at,
            args=[user_id, message, job_id],
            id=job_id
        )
        
        return job_id
    
    async def _send_reminder(self, user_id: int, message: str, job_id: str):
        """Отправка напоминания"""
        # Проверяем, не заполнил ли пользователь анкету
        application = await self.db.get_application(user_id)
        if application and application.get("status") != "pending":
            # Пользователь уже заполнил, отменяем остальные
            return
        
        await self.notification_service.send_reminder(user_id, message)
        
        # Помечаем как отправленное
        # await self.db.mark_reminder_sent(reminder_id)
    
    async def cancel_user_reminders(self, user_id: int):
        """Отмена всех напоминаний пользователя"""
        # Удаляем задачи из scheduler
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            if job.id.startswith(f"reminder_{user_id}_"):
                self.scheduler.remove_job(job.id)
        
        # Отменяем в БД
        await self.db.cancel_user_reminders(user_id)
    
    async def process_pending_reminders(self):
        """Обработка напоминаний из БД (альтернативный подход)"""
        reminders = await self.db.get_pending_reminders()
        for reminder in reminders:
            user_id = reminder["user_id"]
            reminder_id = reminder["id"]
            
            # Проверяем статус заявки
            application = await self.db.get_application(user_id)
            if application and application.get("status") != "pending":
                # Пользователь уже заполнил
                await self.db.mark_reminder_sent(reminder_id)
                continue
            
            # Отправляем напоминание
            await self.notification_service.send_reminder(
                user_id,
                "⏰ Комьюнити ждёт! Вы уже заполнили анкету?"
            )
            await self.db.mark_reminder_sent(reminder_id)

