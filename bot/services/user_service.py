"""Сервис для работы с пользователями"""
from typing import Optional
from bot.database.models import Database


class UserService:
    """Сервис управления пользователями"""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def register_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        role: str = "user"
    ) -> bool:
        """Регистрация нового пользователя"""
        return await self.db.create_user(telegram_id, username, full_name, role)
    
    async def get_user(self, telegram_id: int) -> Optional[dict]:
        """Получение пользователя"""
        return await self.db.get_user(telegram_id)
    
    async def is_admin(self, telegram_id: int, admin_ids: list) -> bool:
        """Проверка, является ли пользователь администратором"""
        if telegram_id in admin_ids:
            return True
        
        user = await self.get_user(telegram_id)
        if user and user.get("role") == "admin":
            return True
        
        return False

