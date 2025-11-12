"""Конфигурация бота"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Настройки приложения"""
    
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    
    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "/app/data/bot.db")
    
    # Admins
    ADMIN_IDS: List[int] = [
        int(admin_id.strip())
        for admin_id in os.getenv("ADMIN_IDS", "").split(",")
        if admin_id.strip().isdigit()
    ]
    
    # Application form URL
    APPLICATION_FORM_URL: str = os.getenv(
        "APPLICATION_FORM_URL",
        "https://clck.ru/3Q4RJU"
    )
    
    # Payment URL
    PAYMENT_URL: str = os.getenv(
        "PAYMENT_URL",
        "https://t.me/tribute/app?startapp=sApp"
    )
    
    # Contact username
    CONTACT_USERNAME: str = os.getenv("CONTACT_USERNAME", "@artlift_agency")

    # Channel settings
    _channel_chat_id_raw = os.getenv("CHANNEL_CHAT_ID", "").strip()
    CHANNEL_CHAT_ID: int | None = (
        int(_channel_chat_id_raw)
        if _channel_chat_id_raw and _channel_chat_id_raw.lstrip("-").isdigit()
        else None
    )
    CHANNEL_USERNAME: str = os.getenv("CHANNEL_USERNAME", "").strip()
    CHANNEL_SUBSCRIBE_URL: str = os.getenv("CHANNEL_SUBSCRIBE_URL", "").strip()
    
    @property
    def redis_url(self) -> str:
        """URL для подключения к Redis"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def channel_target(self) -> str | int | None:
        """Идентификатор канала для отправки сообщений (ID или username)."""
        if self.CHANNEL_CHAT_ID is not None:
            return self.CHANNEL_CHAT_ID
        if self.CHANNEL_USERNAME:
            username = self.CHANNEL_USERNAME
            return username if username.startswith("@") else f"@{username}"
        return None

    @property
    def channel_subscribe_url(self) -> str:
        """URL для кнопки подписки на канал."""
        if self.CHANNEL_SUBSCRIBE_URL:
            return self.CHANNEL_SUBSCRIBE_URL
        if self.CHANNEL_USERNAME:
            return f"https://t.me/{self.CHANNEL_USERNAME.lstrip('@')}"
        return ""


settings = Settings()

