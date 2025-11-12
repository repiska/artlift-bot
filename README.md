# Art Lift Community Telegram Bot

Телеграм-бот помогает принимать заявки в закрытое сообщество Art Lift Community, собирать вопросы пользователей и вести коммуникацию через встроенную админ-панель.

**Основа функциональности**
- приветственное меню со ссылкой на анкету;
- автоматические напоминания о незаполненной анкете;
- обработка вопросов пользователей и ответы менеджеров;
- админ-панель с шаблонами сообщений, статистикой и историей версий;
- отправка служебных уведомлений администраторам.

## Настройка `.env`
1. Скопируйте пример:
   ```bash
   cp .env.example .env
   ```
2. Заполните ключевые переменные:
   - `BOT_TOKEN` — токен Telegram-бота от @BotFather;
   - `ADMIN_IDS` — ID администраторов через запятую;
   - `APPLICATION_FORM_URL` — ссылка на анкету;
   - `CHANNEL_CHAT_ID`, `CHANNEL_USERNAME`, `CHANNEL_SUBSCRIBE_URL` — параметры канала с закрепом, если используется;
   - остальные переменные оставьте по умолчанию или настройте под инфраструктуру.

## Установка на сервер через Docker (Linux)
1. Установите Docker и Docker Compose (если ещё не стоят):
   ```bash
   sudo apt update
   sudo apt install -y ca-certificates curl gnupg git
   sudo install -m 0755 -d /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
   echo \
     "deb [arch=\"$(dpkg --print-architecture)\" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
     $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt update
   sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   sudo systemctl enable --now docker
   ```
2. Создайте рабочую директорию и перейдите в неё:
   ```bash
   sudo mkdir -p /opt/artlif-bot
   sudo chown "$USER":"$USER" /opt/artlif-bot
   cd /opt/artlif-bot
   ```
3. Клонируйте репозиторий:
   ```bash
   git clone <repo-url> .
   ```
4. Настройте `.env` (см. раздел выше).
5. Запустите контейнер:
   ```bash
   docker compose up -d
   ```
6. Проверьте логи и статус:
   ```bash
   docker compose logs -f bot
   docker compose ps
   ```
7. Для остановки или обновления:
   ```bash
   docker compose down                   # остановить
   git pull && docker compose up -d --build  # обновить и перезапустить
   ```

После старта убедитесь, что бот отвечает на `/start`, а админы видят панель управления.#

