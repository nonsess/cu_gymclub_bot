# 🏋️ GYM Club Bot
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![ONNX](https://img.shields.io/badge/ONNX-005CED?style=for-the-badge&logo=onnx&logoColor=white)](https://onnx.ai/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3FA9F5?style=for-the-badge&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)

**Умный сервис знакомств для тренажерного зала.**  
Бот помогает спортсменам находить партнеров для тренировок, основываясь на общих целях, опыте и симпатиях. Система использует векторный поиск для подбора наиболее релевантных анкет.

---

## 🚀 Быстрый старт

Для запуска проекта локально вам понадобится **Docker** и **Docker Compose**.

### 1. Подготовка модели эмбеддингов
Перед первым запуском необходимо скачать веса нейросети для векторного поиска. Выполните скрипт в папке бэкенда:

```bash
cd backend
./export-model.sh
```

Примечание: Скрипт скачает модель paraphrase-multilingual-MiniLM-L12-v2 и сохранит её в оптимизированном формате ONNX в папку кэша. Это нужно сделать один раз.

### 2. Настройка переменных окружения
Создайте файл .env в корне проекта на основе примера:

```bash
cp .env.example .env
```

Отредактируйте .env, указав свои данные

### 3. Запуск проекта

Запустите все сервисы (БД, Redis, Бэкенд, Бот) одной командой:

```bash
docker compose up --build
```

---

## Архитектура проекта
Проект состоит из следующих основных компонентов:

Backend (FastAPI)	
REST API для управления профилями, лайками, матчами и рассылками.

Bot (Aiogram)
Telegram-бот для взаимодействия с пользователями.

Database (PostgreSQL + pgvector)
Хранение данных пользователей и векторных эмбеддингов для поиска через косинусную схожесть.

Cache (Redis)
Кэширование профилей, хранение сессий и очередей уведомлений.

Особенности реализации

Векторный поиск: Подбор анкет осуществляется с помощью расширения pgvector и ONNX-модели, что обеспечивает высокую скорость и релевантность.
Асинхронность: Полностью асинхронный стек (FastAPI + Aiogram + AsyncPG) для высокой нагрузки.
Безопасность: Валидация данных, защита от спам-атак, разграничение прав доступа.
Тестирование: Покрытие тестами (pytest) репозиториев, сервисов и API эндпоинтов.

---

## 🧪 Запуск тестов
Проект покрыт тестами. Для запуска внутри контейнера:

```bash
docker compose exec backend pytest
```

---

## 📂 Структура проекта

```text
.
├── backend/                 # Исходный код бэкенда
│   ├── src/
│   │   ├── api/             # Роутеры FastAPI
│   │   ├── services/        # Бизнес-логика
│   │   ├── repositories/    # Работа с БД
│   │   ├── models/          # SQLAlchemy модели
│   │   └── schemas/         # Pydantic схемы
│   ├── export-model.sh      # Скрипт загрузки модели
│   └── Dockerfile
├── bot/                     # Исходный код Telegram-бота
│   ├── handlers/            # Обработчики сообщений
│   ├── keyboards/           # Клавиатуры
│   └── Dockerfile
├── docker-compose.yml       # Оркестрация сервисов
├── .env.example             # Шаблон переменных окружения
└── README.md
```
