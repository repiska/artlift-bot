"""Модели базы данных"""
from datetime import datetime
from typing import Optional
import aiosqlite


class Database:
    """Класс для работы с базой данных SQLite"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    async def init_db(self):
        """Инициализация базы данных - создание таблиц"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица заявок
            await db.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    admin_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                    FOREIGN KEY (admin_id) REFERENCES users(telegram_id)
                )
            """)
            
            # Таблица напоминаний
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    reminder_type TEXT NOT NULL,
                    scheduled_at TIMESTAMP NOT NULL,
                    sent_at TIMESTAMP,
                    cancelled BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                )
            """)
            
            # Таблица действий администраторов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS admin_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    user_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (admin_id) REFERENCES users(telegram_id),
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                )
            """)
            
            # Таблица шаблонов сообщений бота
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_key TEXT UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by INTEGER,
                    FOREIGN KEY (updated_by) REFERENCES users(telegram_id)
                )
            """)
            
            # Таблица истории версий сообщений (бэкапы)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_messages_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_key TEXT NOT NULL,
                    content TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (created_by) REFERENCES users(telegram_id),
                    FOREIGN KEY (message_key) REFERENCES bot_messages(message_key)
                )
            """)
            
            # Таблица вопросов пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question_text TEXT,
                    status TEXT DEFAULT 'pending',
                    admin_id INTEGER,
                    answer_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    answered_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                    FOREIGN KEY (admin_id) REFERENCES users(telegram_id)
                )
            """)
            
            # Инициализация дефолтных шаблонов
            default_templates = [
                ("welcome", 
                 "Привет! 👋\n\nДобро пожаловать в Art Lift Community — профессиональное пространство для художников, кураторов и арт-менеджеров.\n\n<b>Что включает членство:</b>\n• Общение в закрытом Telegram-чате\n• Ответы на вопросы от команды специалистов\n• Встречи с экспертами арт-рынка: кураторами, галеристами, арт-менеджерами и художниками\n• Обзоры международных событий в сфере искусства\n• Портфолио-ревью\n• Еженедельные обсуждения актуальных тем арт-индустрии\n• Random coffee с участниками\n• Поддержка от комьюнити\n\n<b>Стоимость участия:</b>\n• Первый пробный месяц — 2 500 ₽\n• Последующие месяцы — 5 000 ₽\n\nЧтобы присоединиться, заполните короткую анкету и затем подтвердите отправку в боте.",
                 "Приветственное сообщение при /start"),
                ("main_menu",
                 "<b>Главное меню</b>\n\nВыберите нужное действие, используя кнопки ниже.",
                 "Сообщение главного меню"),
                ("application_filled_response",
                 "Отлично! 🎉\n\nВаша заявка получена и скоро будет рассмотрена.\nОбычно ответ приходит в течение 1–2 дней.",
                 "Ответ после подтверждения заполнения анкеты"),
                ("user_question_response",
                 "Спасибо! Мы передали ваш вопрос менеджеру — скоро он выйдет на связь.",
                 "Ответ на вопрос пользователя"),
                ("channel_subscribe_message",
                 "<b>Art Lift Community</b>\n\nНажмите ниже, чтобы заполнить анкету и подать заявку в комьюнити.",
                 "Сообщение для закрепа в канале"),
                ("application_approved",
                 "{name}, спасибо за вашу заявку!\n\nМы очарованы вашими работами и рады пригласить вас в закрытое комьюнити Art Lift!\n\n<b>Стоимость:</b>\n• Первый месяц со скидкой — 2 500 ₽\n• Последующие месяцы — 5 000 ₽\n\nОплата проходит через сервис @tribute:\n👉 {PAYMENT_URL}\n\nПосле оплаты вы автоматически получите доступ к сообществу.\n\nКак войдёте в комьюнити — представьтесь, пожалуйста, и подключайтесь к ближайшим мероприятиям!\n\nОстались вопросы? С радостью ответим!",
                 "Уведомление об одобрении заявки"),
                ("application_rejected",
                 "Здравствуйте, {name}!\n\nБлагодарим вас за заявку в Art Lift Community и за то, что поделились своими работами.\n\nК сожалению, сейчас мы не готовы пригласить вас в закрытое комьюнити — мы следим за тем, чтобы участники в сообществе были приблизительно одного уровня.\n\nНо мы будем очень рады видеть вас позже! А пока предлагаем другие форматы сотрудничества:\n\n<b>1. Индивидуальная консультация</b>\n\nМы предварительно изучаем ваши материалы и подстраиваем встречу под ваш запрос.\n\n<b>Консультация включает:</b>\n• Анализ вашей ситуации и портфолио\n• Конкретные рекомендации по подаче на опен-коллы\n• Обсуждение направлений развития\n• Поддерживающий диалог\n\n<b>Стоимость:</b> от 8 000 ₽ (60 мин)\nЗависит от запроса и продолжительности.\n\n\n<b>2. Менторство</b>\n\nГораздо более глубокая индивидуальная работа с экспертом более высокого уровня, чем сопровождение.\n\nЭто работа как с практикой художника, так и с подбором галерей и сменой ориентиров в художественном поле. И, самое главное, — регулярные живые сессии в Zoom/Google Meet/Telegram.\n\n<b>Стоимость:</b>\nРазброс цен очень большой — всё зависит от специфики запроса и самого ментора.\n\nОстались вопросы? Пишите {CONTACT_USERNAME} — подберём услугу и вышлем актуальный план по менторам 💬",
                 "Уведомление об отклонении заявки"),
                ("faq",
                 "<b>Часто задаваемые вопросы</b>\n\n<b>Что такое Art Lift Community?</b>\nПрофессиональное пространство для художников, кураторов и арт-менеджеров.\n\n<b>Что включает членство?</b>\n• Общение в закрытом Telegram-чате\n• Ответы на вопросы от команды специалистов\n• Встречи с экспертами арт-рынка\n• Обзоры на международные события в сфере искусства\n• Портфолио-ревью\n• Еженедельные обсуждения актуальных тем\n• Random coffee с участниками\n• Поддержка от комьюнити\n\n<b>Стоимость:</b>\n• Первый пробный месяц — 2 500 ₽\n• Последующие месяцы — 5 000 ₽\n\nОстались вопросы? Нажмите «❓ Задать вопрос» в меню, и мы ответим лично.",
                 "FAQ раздел"),
            ]
            
            for key, content, description in default_templates:
                await db.execute("""
                    INSERT OR IGNORE INTO bot_messages (message_key, content, description)
                    VALUES (?, ?, ?)
                """, (key, content, description))
            
            await db.commit()
    
    async def create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        role: str = "user"
    ) -> bool:
        """Создание нового пользователя или обновление существующего"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO users (telegram_id, username, full_name, role, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (telegram_id, username, full_name, role, datetime.now()))
            await db.commit()
            return True
    
    async def get_user(self, telegram_id: int) -> Optional[dict]:
        """Получение пользователя по telegram_id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
    
    async def create_application(self, user_id: int) -> int:
        """Создание новой заявки"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO applications (user_id, status, created_at)
                VALUES (?, 'pending', ?)
            """, (user_id, datetime.now()))
            await db.commit()
            return cursor.lastrowid
    
    async def get_application(self, user_id: int) -> Optional[dict]:
        """Получение заявки пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM applications WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
    
    async def update_application_status(
        self,
        user_id: int,
        status: str,
        admin_id: int
    ) -> bool:
        """Обновление статуса заявки"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE applications
                SET status = ?, admin_id = ?, reviewed_at = ?
                WHERE user_id = ? AND status = 'pending'
            """, (status, admin_id, datetime.now(), user_id))
            await db.commit()
            return True
    
    async def get_pending_applications(self, limit: int = 10, offset: int = 0) -> list:
        """Получение списка заявок со статусом pending"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT a.*, u.username, u.full_name
                FROM applications a
                JOIN users u ON a.user_id = u.telegram_id
                WHERE a.status = 'pending'
                ORDER BY a.created_at ASC
                LIMIT ? OFFSET ?
            """, (limit, offset)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def count_pending_applications(self) -> int:
        """Подсчет количества pending заявок"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM applications WHERE status = 'pending'"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    async def count_approved_applications(self) -> int:
        """Подсчет количества одобренных заявок"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM applications WHERE status = 'approved'"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    async def count_rejected_applications(self) -> int:
        """Подсчет количества отклоненных заявок"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM applications WHERE status = 'rejected'"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    async def count_total_applications(self) -> int:
        """Подсчет общего количества заявок"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM applications"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    async def create_reminder(
        self,
        user_id: int,
        reminder_type: str,
        scheduled_at: datetime
    ) -> int:
        """Создание напоминания"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO reminders (user_id, reminder_type, scheduled_at)
                VALUES (?, ?, ?)
            """, (user_id, reminder_type, scheduled_at))
            await db.commit()
            return cursor.lastrowid
    
    async def get_pending_reminders(self) -> list:
        """Получение напоминаний, которые нужно отправить"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM reminders
                WHERE scheduled_at <= ? AND sent_at IS NULL AND cancelled = 0
                ORDER BY scheduled_at ASC
            """, (datetime.now(),)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def mark_reminder_sent(self, reminder_id: int) -> bool:
        """Отметка напоминания как отправленного"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE reminders SET sent_at = ? WHERE id = ?
            """, (datetime.now(), reminder_id))
            await db.commit()
            return True
    
    async def cancel_user_reminders(self, user_id: int) -> bool:
        """Отмена всех напоминаний пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE reminders
                SET cancelled = 1
                WHERE user_id = ? AND sent_at IS NULL
            """, (user_id,))
            await db.commit()
            return True
    
    async def log_admin_action(
        self,
        admin_id: int,
        action_type: str,
        user_id: Optional[int] = None
    ) -> bool:
        """Логирование действия администратора"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO admin_actions (admin_id, action_type, user_id)
                VALUES (?, ?, ?)
            """, (admin_id, action_type, user_id))
            await db.commit()
            return True
    
    async def get_message(self, message_key: str) -> Optional[dict]:
        """Получение шаблона сообщения"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM bot_messages WHERE message_key = ?",
                (message_key,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
    
    async def update_message(
        self,
        message_key: str,
        content: str,
        admin_id: int
    ) -> bool:
        """Обновление шаблона сообщения с сохранением предыдущей версии в историю"""
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем текущую версию для сохранения в историю
            current = await self.get_message(message_key)
            
            if current:
                # Сохраняем предыдущую версию в историю
                await db.execute("""
                    INSERT INTO bot_messages_history (message_key, content, description, created_at, created_by)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    message_key,
                    current["content"],
                    current.get("description"),
                    current.get("updated_at", datetime.now()),
                    current.get("updated_by")
                ))
            
            # Обновляем сообщение
            await db.execute("""
                INSERT INTO bot_messages (message_key, content, updated_at, updated_by)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(message_key) DO UPDATE SET
                    content = excluded.content,
                    updated_at = excluded.updated_at,
                    updated_by = excluded.updated_by
            """, (message_key, content, datetime.now(), admin_id))
            await db.commit()
            return True
    
    async def get_all_messages(self) -> list:
        """Получение всех шаблонов сообщений"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT message_key, description, updated_at FROM bot_messages ORDER BY message_key"
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_message_history(self, message_key: str, limit: int = 10) -> list:
        """Получение истории версий сообщения"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT id, message_key, content, description, created_at, created_by
                FROM bot_messages_history
                WHERE message_key = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (message_key, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_history_item(self, history_id: int) -> Optional[dict]:
        """Получение конкретного элемента истории по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM bot_messages_history WHERE id = ?",
                (history_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
    
    async def restore_message_from_history(
        self,
        history_id: int,
        admin_id: int
    ) -> bool:
        """Восстановление сообщения из истории"""
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем версию из истории
            history_item = await self.get_history_item(history_id)
            if not history_item:
                return False
            
            # Сохраняем текущую версию в историю перед восстановлением
            current = await self.get_message(history_item["message_key"])
            if current:
                await db.execute("""
                    INSERT INTO bot_messages_history (message_key, content, description, created_at, created_by)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    history_item["message_key"],
                    current["content"],
                    current.get("description"),
                    current.get("updated_at", datetime.now()),
                    current.get("updated_by")
                ))
            
            # Восстанавливаем версию из истории
            await db.execute("""
                INSERT INTO bot_messages (message_key, content, updated_at, updated_by)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(message_key) DO UPDATE SET
                    content = excluded.content,
                    updated_at = excluded.updated_at,
                    updated_by = excluded.updated_by
            """, (
                history_item["message_key"],
                history_item["content"],
                datetime.now(),
                admin_id
            ))
            await db.commit()
            return True
    
    async def delete_history_item(self, history_id: int) -> bool:
        """Удаление элемента истории"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM bot_messages_history WHERE id = ?",
                (history_id,)
            )
            await db.commit()
            return True
    
    async def create_user_question(
        self,
        user_id: int,
        question_text: Optional[str] = None
    ) -> int:
        """Создание вопроса пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO user_questions (user_id, question_text, status, created_at)
                VALUES (?, ?, 'pending', ?)
            """, (user_id, question_text, datetime.now()))
            await db.commit()
            return cursor.lastrowid
    
    async def get_pending_questions(self, limit: int = 10, offset: int = 0) -> list:
        """Получение списка неотвеченных вопросов"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT q.*, u.username, u.full_name
                FROM user_questions q
                JOIN users u ON q.user_id = u.telegram_id
                WHERE q.status = 'pending'
                ORDER BY q.created_at ASC
                LIMIT ? OFFSET ?
            """, (limit, offset)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_question(self, question_id: int) -> Optional[dict]:
        """Получение вопроса по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT q.*, u.username, u.full_name
                FROM user_questions q
                JOIN users u ON q.user_id = u.telegram_id
                WHERE q.id = ?
            """, (question_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
    
    async def answer_question(
        self,
        question_id: int,
        admin_id: int,
        answer_text: str
    ) -> bool:
        """Ответ на вопрос пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE user_questions
                SET status = 'answered',
                    admin_id = ?,
                    answer_text = ?,
                    answered_at = ?
                WHERE id = ?
            """, (admin_id, answer_text, datetime.now(), question_id))
            await db.commit()
            return True
    
    async def count_pending_questions(self) -> int:
        """Подсчет количества неотвеченных вопросов"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM user_questions WHERE status = 'pending'"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

