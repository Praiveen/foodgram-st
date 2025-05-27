# Foodgram - Продуктовый помощник

Foodgram - это веб-сервис, где пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в «Избранное», а перед походом в магазин скачивать сводный «Список покупок» в формате .txt.

## Стек технологий

- **Бэкенд**: Python, Django, Django REST framework, djoser, PostgreSQL
- **Фронтенд**: JavaScript, React (или другой ваш стек, укажите его)
- **Веб-сервер**: Nginx
- **Контейнеризация**: Docker, Docker Compose
- **CI/CD**: GitHub Actions

## Предварительные требования

Для локального запуска (режим разработки):
- Python 3.9+ (рекомендуется использовать виртуальное окружение)
- Node.js и npm/yarn (для сборки и запуска фронтенда)
- PostgreSQL (локально установленный или в Docker)

Для запуска в Docker-контейнерах:
- Docker
- Docker Compose

## Локальный запуск для разработки (без Docker)

### 1. Бэкенд (Django)

1.  **Клонируйте репозиторий:**
    ```bash
    git clone <URL репозитория>
    cd foodgram-st
    ```

2.  **Настройте и активируйте виртуальное окружение (рекомендуется):**
    ```bash
    python -m venv venv
    # Для Windows
    .\venv\Scripts\activate
    # Для macOS/Linux
    source venv/bin/activate
    ```

3.  **Установите зависимости бэкенда:**
    ```bash
    pip install -r backend/requirements.txt
    ```

4.  **Настройте переменные окружения для бэкенда:**
    Создайте файл `.env` в директории `backend/` (или в `infra/`, если `docker-compose.yml` его там ожидает для локального использования Django с Docker PostgreSQL). Пример содержимого `.env`:
    ```env
    # backend/.env
    DJANGO_SECRET_KEY='ваш_супер_секретный_ключ'
    DJANGO_DEBUG=True 

    # Настройки для подключения к PostgreSQL (если используете локальный PostgreSQL)
    # Если используете SQLite (при DEBUG=True по умолчанию в текущих настройках), эти переменные не нужны.
    # POSTGRES_DB=foodgram
    # POSTGRES_USER=foodgram_user
    # POSTGRES_PASSWORD=your_strong_password
    # POSTGRES_HOST=localhost # или адрес вашего Docker PostgreSQL, если он запущен отдельно
    # POSTGRES_PORT=5432
    ```

5.  **Примените миграции и добавление ингредиентов:**
    ```bash
    python manage.py makemigrations users recipes
    python manage.py migrate
    python manage.py load_ingredients
    ```

6.  **Создайте суперпользователя (опционально):**
    ```bash
    python backend/manage.py createsuperuser
    ```

7.  **Запустите сервер разработки Django:**
    ```bash
    python backend/manage.py runserver
    ```
    По умолчанию бэкенд будет доступен по адресу `http://127.0.0.1:8000/`.

### 2. Фронтенд (React)

1.  **Перейдите в директорию фронтенда:**
    ```bash
    cd frontend
    ```

2.  **Установите зависимости фронтенда:**
    ```bash
    # если используете npm
    npm install
    # если используете yarn
    yarn install
    ```

3.  **Запустите сервер разработки фронтенда:**
    ```bash
    # если используете npm
    npm start
    # если используете yarn
    yarn start
    ```
    Фронтенд обычно доступен по адресу `http://localhost:3000/` 

## Запуск проекта в Docker-контейнерах

Этот способ использует `docker-compose` для запуска всех сервисов (бэкенд, фронтенд (сборка), база данных PostgreSQL, веб-сервер Nginx).

1.  **Клонируйте репозиторий (если еще не сделали):**
    ```bash
    git clone <URL репозитория>
    cd foodgram-st
    ```

2.  **Настройте переменные окружения для Docker Compose:**
    Создайте файл `.env` в директории `infra/` (так как `docker-compose.yml` находится там).
    Пример содержимого `infra/.env`:
    ```env
    # infra/.env
    DJANGO_SECRET_KEY='ваш_другой_супер_секретный_ключ_для_продакшена'
    DJANGO_DEBUG=False # Для продакшен-сборки DEBUG должен быть False

    # Для ALLOWED_HOSTS, когда DEBUG=False. Укажите ваш домен(ы) или IP.
    # Например: DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,localhost,127.0.0.1
    # Для локального тестирования с Docker можно использовать localhost и IP Docker-машины.
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.99.100 # Замените 192.168.99.100 при необходимости

    # Настройки базы данных PostgreSQL (будут использованы сервисом db из docker-compose)
    POSTGRES_DB=foodgram
    POSTGRES_USER=foodgram_user
    POSTGRES_PASSWORD=your_strong_password_for_docker_pg
    # POSTGRES_HOST и POSTGRES_PORT обычно не нужны здесь, т.к. Django-контейнер будет обращаться к db по имени сервиса 'db'
    ```

3.  **Сборка и запуск контейнеров:**
    Перейдите в директорию `infra/` и выполните:
    ```bash
    cd infra
    docker-compose up --build -d
    ```
    *   `--build` пересобирает образы, если были изменения в Dockerfile или коде.
    *   `-d` запускает контейнеры в фоновом режиме.


4.  **Доступ к приложению:**
    *   **Фронтенд**: `http://localhost/` или `http://192.168.99.100/` (или IP вашей Docker-машины).
    *   **API документация (Swagger/ReDoc)**: `http://localhost/api/docs/`.
    *   **Админка Django**: `http://localhost/admin/` или `http://localhost/api/admin/`.

5.  **Остановка контейнеров:**
    Находясь в директории `infra/`:
    ```bash
    docker-compose down
    ```
    Для удаления вольюмов (если нужно полностью очистить данные БД):
    ```bash
    docker-compose down -v
    ```

## CI/CD (GitHub Actions)

В проекте настроен CI/CD пайплайн с использованием GitHub Actions (`.github/workflows/docker-image.yml`):
- **Триггеры**: Запускается при push в ветку `main` и может быть запущен вручную.
- **Задачи**:
  1.  **Тестирование бэкенда**: Установка зависимостей Python и запуск Django тестов (`python backend/manage.py test`).
  2.  **Сборка и публикация Docker-образа бэкенда**: Если тесты успешны, собирается образ бэкенда (`backend/Dockerfile`) и публикуется на Docker Hub (`ВАШ_ЛОГИН_DOCKERHUB/foodgram-backend`).
  3.  **Сборка и публикация Docker-образа фронтенда**: Если тесты успешны, собирается образ фронтенда (`frontend/Dockerfile`) и публикуется на Docker Hub (`ВАШ_ЛОГИН_DOCKERHUB/foodgram-frontend`).

Убедитесь, что в настройках вашего репозитория GitHub (`Settings` -> `Secrets and variables` -> `Actions`) добавлены следующие секреты для публикации на Docker Hub:
- `DOCKERHUB_USERNAME`: Ваш логин на Docker Hub.
- `DOCKERHUB_TOKEN`: Ваш Personal Access Token от Docker Hub с правами на запись.

## Тестовые данные

Для загрузки тестовых данных (пользователи, рецепты) используйте команду:
```bash
python manage.py load_initial_data
```

### Тестовые учетные записи

1. Администратор:
   - Email: admin@example.com
   - Пароль: adminpassword123

2. Обычные пользователи:
   - Email: user1@example.com
   - Пароль: user1password
   - Имя: Alice Smith

   - Email: user2@example.com
   - Пароль: user2password
   - Имя: Bob Johnson

### Тестовые рецепты

После загрузки будут доступны следующие рецепты:
- Яичница глазунья (время приготовления: 5 минут)
- Куриный суп с лапшой (время приготовления: 45 минут)
- Греческий салат (время приготовления: 15 минут)

Рецепты создаются с случайным набором ингредиентов из базы данных.

## Автор

Карагачев Иван
