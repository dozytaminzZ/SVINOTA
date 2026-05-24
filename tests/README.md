# Тесты модуля авторизации
## Установка зависимостей

```powershell
pip install -r requirements.txt
pip install -r tests/requirements-test.txt
```

Для генерации HTML-отчёта понадобится Allure CLI (https://allurereport.org/docs/install/):

```powershell
scoop install allure
# или
choco install allure
```

## Запуск тестов

Из корня проекта:

```powershell
pytest tests --alluredir=allure-results
```

## Просмотр Allure-отчёта

```powershell
allure serve allure-results
```

## Структура

- `conftest.py` — фикстуры `app`, `client`, `db`, `registered_user`. Использует SQLite in-memory, чтобы не трогать боевую БД.
- `test_auth_register.py` — регистрация: успех, валидация, дубликаты, повторная регистрация.
- `test_auth_login.py` — вход по username/email, неверные учётные данные, повторный вход.
- `test_auth_guest.py` — гостевой вход, уникальность имён, защита от повторного входа.
- `test_auth_session.py` — logout, /auth/profile, /auth/.
