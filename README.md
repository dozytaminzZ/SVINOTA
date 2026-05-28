# SVINOTA

Онлайн-игра по мотивам настольной игры "Свинтус".

## Стек

- Python 3.11+
- Flask + Flask-SocketIO
- PostgreSQL
- SQLAlchemy + Alembic (Flask-Migrate)

## Локальный запуск (Windows, PowerShell)

1) Виртуальное окружение:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Зависимости:

```powershell
pip install -r requirements.txt
```

3) Настрой `.env`:

```env
SECRET_KEY=dev_secret_key
DATABASE_URL=postgresql://postgres:postgres@localhost/svinota
```

4) Миграции:

```powershell
set FLASK_APP=run.py
flask db init
flask db migrate -m "init"
flask db upgrade
```

5) Старт:

```powershell
python run.py
```

## Деплой на Railway (коротко)

1) Создай проект в Railway и подключи репозиторий.
2) Добавь PostgreSQL (Plugin) — Railway создаст `DATABASE_URL`.
3) Задай переменные окружения:
	- `SECRET_KEY` — любое случайное значение.
4) Start Command:

```
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT run:app
```

5) В Railway Shell выполнить миграции:

```
flask db upgrade
```
