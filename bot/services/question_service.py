"""Сервис для работы с вопросами пользователей"""
from typing import Optional
from bot.database.models import Database


class QuestionService:
    """Сервис управления вопросами пользователей"""
    
    def __init__(self, db: Database):
        self._db = db
    
    @property
    def db(self):
        """Доступ к базе данных для совместимости"""
        return self._db
    
    async def create_question(
        self,
        user_id: int,
        question_text: Optional[str] = None
    ) -> int:
        """Создание вопроса пользователя"""
        return await self._db.create_user_question(user_id, question_text)
    
    async def get_pending_questions(self, limit: int = 10, offset: int = 0) -> list:
        """Получение списка неотвеченных вопросов"""
        return await self._db.get_pending_questions(limit, offset)
    
    async def get_question(self, question_id: int):
        """Получение вопроса по ID"""
        return await self._db.get_question(question_id)
    
    async def answer_question(
        self,
        question_id: int,
        admin_id: int,
        answer_text: str
    ) -> bool:
        """Ответ на вопрос пользователя"""
        return await self._db.answer_question(question_id, admin_id, answer_text)
    
    async def count_pending_questions(self) -> int:
        """Подсчет количества неотвеченных вопросов"""
        return await self._db.count_pending_questions()

