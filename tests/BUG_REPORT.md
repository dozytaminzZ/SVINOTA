# Bug report для бэка — user_loader падает на UUID-cookie

**Текущий статус `pytest tests/`:** `17 passed, 36 failed, 9 errors`.
Все падения — один и тот же баг.

## Важно прочитать сначала: при чём тут лобби

Этот баг **не появился из-за лобби**. На коммите `f3b733c` (до лобби) все
26 auth-тестов проходят зелёными — баг там есть, но дремлет.

Чтобы написать тесты лобби с несколькими игроками в одном тесте, в
`tests/conftest.py` пришлось добавить `before_request`-хук, который перед каждым
запросом чистит `g._login_user` (иначе второй `test_client` в том же тесте
видит юзера от первого — flask_login кэширует current_user в `g`). Хук
**не баг и не workaround** — это нормальное устройство тестовой фикстуры под
multi-client сценарии.

Но хук как побочный эффект заставляет flask_login на каждом запросе восстанавливать
юзера из cookie через `user_loader` — и вот тут вскрывается реальный баг бэка.

**Без фикса бэка** auth-тесты падают, как только тестовая инфраструктура
перестаёт случайно держать кэшированного юзера в `g`. То же самое случится в
проде при любом сценарии, где cookie живёт дольше, чем `g` (рестарт воркера,
фоновый job, истекший request-контекст).

## Симптом

```
sqlalchemy.exc.StatementError: (builtins.AttributeError) 'str' object has no attribute 'hex'
[SQL: SELECT users.id ... FROM users WHERE users.id = ?]
[parameters: [{'pk_1': '491e0c6c-a46d-4b11-90e9-84975e2c7425'}]]
```

Падает запрос внутри `flask_login` → `user_loader` → `db.session.get(User, user_id)`.

## Где баг

[app/__init__.py:20-21](../app/__init__.py#L20-L21)

```python
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)   # user_id — str, User.id — UUID
```

`flask_login` всегда передаёт `user_id` как **строку** (сериализованную в cookie).
А `User.id` объявлен как `db.Uuid(as_uuid=True)` ([app/models.py:8](../app/models.py#L8))
— под SQLite SQLAlchemy ждёт `uuid.UUID` и вызывает `.hex` на нём. На строке —
`AttributeError`.

## Почему в проде не видно (пока)

После `login_user(user)` объект юзера лежит в `g._login_user`. Пока запрос/сессия
живы и `g` тёплый, loader из cookie не вызывается. Loader срабатывает только когда
flask_login **восстанавливает юзера из cookie** на новом запросе с пустым `g`.

На дев-машине одного разработчика это случается редко. Но обязательно случится при:

- рестарте процесса / запуске нового воркера (cookie у юзера ещё валидный → loader → 500),
- любом фоновом джобе/cron'е, который воссоздаёт сессию из cookie,
- разлогине после рестарта,
- по сути любом первом запросе нового процесса под уже залогиненным юзером.

## Что нужно сделать

В [app/__init__.py:20-21](../app/__init__.py#L20-L21):

```python
import uuid

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, uuid.UUID(user_id))
    except (ValueError, TypeError):
        return None
```

- `uuid.UUID(...)` — потому что в cookie лежит строка.
- `try/except` — потому что в cookie может оказаться мусор (старая сессия, подделка),
  и тогда нужно вернуть `None`, а не 500.

## Как проверить, что починилось

```bash
python -m pytest tests/ -q
```

Должно быть `62 passed`. До фикса: `17 passed, 36 failed, 9 errors`,
все падения — `'str' object has no attribute 'hex'`.

## Падающие сейчас тесты (все из-за одного бага)

- `tests/auth/` — 13 passed, 4 failed, 9 errors
- `tests/lobby/` — почти всё падает (любой тест, где нужен авторизованный клиент)

После фикса все 62 теста зелёные без правок в тестах.
