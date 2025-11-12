"""Сервис для работы с заявками"""
from typing import Optional
from bot.database.models import Database


class ApplicationService:
    """Сервис управления заявками"""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create_application(self, user_id: int) -> int:
        """Создание новой заявки"""
        return await self.db.create_application(user_id)
    
    async def get_application(self, user_id: int) -> Optional[dict]:
        """Получение заявки пользователя"""
        return await self.db.get_application(user_id)
    
    async def approve_application(self, user_id: int, admin_id: int) -> bool:
        """Одобрение заявки"""
        return await self.db.update_application_status(user_id, "approved", admin_id)
    
    async def reject_application(self, user_id: int, admin_id: int) -> bool:
        """Отказ в заявке"""
        return await self.db.update_application_status(user_id, "rejected", admin_id)
    
    async def get_pending_applications(self, limit: int = 10, offset: int = 0) -> list:
        """Получение списка заявок на рассмотрении"""
        return await self.db.get_pending_applications(limit, offset)
    
    async def count_pending_applications(self) -> int:
        """Подсчет количества заявок на рассмотрении"""
        return await self.db.count_pending_applications()
    
    async def get_statistics(self) -> dict:
        """Получение полной статистики по заявкам"""
        return {
            "total": await self.db.count_total_applications(),
            "pending": await self.db.count_pending_applications(),
            "approved": await self.db.count_approved_applications(),
            "rejected": await self.db.count_rejected_applications(),
        }

