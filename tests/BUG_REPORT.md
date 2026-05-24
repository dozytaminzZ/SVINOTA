# Bug: user_loader падает на UUID из cookie

**Файл:** [app/__init__.py:20-21](../app/__init__.py#L20-L21)

```python
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)   # user_id — str, User.id — UUID
```

**Ошибка:**
```
sqlalchemy.exc.StatementError: 'str' object has no attribute 'hex'
```

**Проверка:** `python -m pytest tests/ -q` → должно стать `62 passed` (сейчас `17 passed, 36 failed, 9 errors`).
