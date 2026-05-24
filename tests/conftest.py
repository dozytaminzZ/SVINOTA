import os
import sys

import pytest

# Добавляем корень проекта в PYTHONPATH, чтобы можно было импортировать app
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import create_app
from app.extensions import db as _db


class TestConfig:
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def registered_user(client):
    payload = {
        'username': 'existing_user',
        'password': 'qwerty123',
        'email': 'existing@example.com',
    }
    client.post('/auth/register', json=payload)
    # Сбрасываем сессию, чтобы пользователь не был залогинен
    client.post('/auth/logout')
    return payload
