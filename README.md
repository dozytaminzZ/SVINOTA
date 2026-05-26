# SVINOTA

Учебный онлайн-проект по карточной игре "Свинтус".

## Кратко о проекте

SVINOTA — веб-игра с лобби, авторизацией и игровой логикой на сервере.
Сервер выступает источником истины и валидирует все действия игроков.

## Стек

- Python 3.11+
- Flask, Flask-Login, Flask-SocketIO
- PostgreSQL
- SQLAlchemy + Alembic (Flask-Migrate)

## Быстрый старт (Windows, PowerShell)

1) Создай и активируй виртуальное окружение:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Установи зависимости:

```powershell
pip install -r requirements.txt
```

3) Создай базу данных PostgreSQL и настрой переменные окружения в `.env`:

```env
SECRET_KEY=dev_secret_key
DATABASE_URL=postgresql://postgres:postgres@localhost/svinota
```

4) Настрой миграции и создай таблицы:

```powershell
set FLASK_APP=run.py
flask db init
flask db migrate -m "init"
flask db upgrade
```

5) Запусти сервер:

```powershell
python run.py
```

Сервер стартует на http://127.0.0.1:5000

## Документация API и dev-формы

- Swagger UI: `/docs`
- OpenAPI YAML: `/openapi.yaml`
- Dev-форма авторизации: `/auth/dev`
- Dev-форма лобби: `/lobby/dev`

## Основные HTTP-эндпоинты

### Auth
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/guest`
- `POST /auth/logout`
- `GET /auth/profile`

### Lobby
- `GET /lobby/rooms`
- `POST /lobby/create`
- `POST /lobby/join`
- `POST /lobby/leave`
- `POST /lobby/ready`

### Game
- `GET /game/state`
- `POST /game/create`
- `POST /game/play`
- `POST /game/draw`
- `POST /game/pass`
- `POST /game/svintus`
- `POST /game/cover-press`

## Socket.IO события (MVP)

Вход в комнату и синхронизация:
- `game:join` — { room_id }
- `game:leave` — { room_id }
- `game:state` — { room_id }

Игровые действия:
- `game:create` — { room_id }
- `game:play` — { room_id, card_id, chosen_color }
- `game:draw` — { room_id }
- `game:pass` — { room_id }
- `game:svintus` — { room_id }
- `game:cover_press` — { room_id }

Сервер отвечает:
- `game:state` — актуальное состояние
- `game:action` — результат действия
- `game:error` — ошибка

## Правила (MVP)

- Колода 112 карт: 4 цвета, цифры 0-9, спецкарты (пропуск, реверс, +2),
	черные карты (смена цвета, +4, "накрой колодку").
- Первый ход — случайный игрок, направление по часовой стрелке.
- Накопление штрафов (stacking) не используется.
- "Свинтус": 3 секунды после 1 карты, штраф +2.
- "Накрой колодку": 5 секунд на нажатие, штраф +2 тем, кто не нажал;
	если нажали все — +2 получает последний.

## Ограничения (на сейчас)

- Состояние игры хранится в памяти сервера (после рестарта всё сбрасывается).
- Нет масштабирования на несколько инстансов.

## Структура проекта

- `app/blueprints` — HTTP-ручки (auth, lobby, game)
- `app/game` — логика игры (движок, реестр, сервис)
- `app/sockets` — Socket.IO обработчики
- `app/templates` — dev-формы и Swagger UI
- `app/static` — OpenAPI спецификация

## Разработка

Для новых фич используйте отдельные ветки (feature-branches) и Pull Request в основную ветку команды.
