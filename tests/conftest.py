import os
import sys

import pytest
from flask import g

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

    # Фикстура держит один app_context на весь тест (SQLite :memory: иначе
    # сбрасывается между соединениями). flask_login кэширует current_user в
    # flask.g — без сброса второй test_client видит юзера от предыдущего реквеста.
    @application.before_request
    def _reset_flask_login_cache():
        for attr in ('_login_user', '_current_user'):
            if hasattr(g, attr):
                delattr(g, attr)

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


def _make_logged_in_client(app, username, password='qwerty123', email=None):
    """Создаёт отдельный test_client с зарегистрированным и залогиненным пользователем."""
    client = app.test_client()
    payload = {'username': username, 'password': password}
    if email is not None:
        payload['email'] = email
    response = client.post('/auth/register', json=payload)
    assert response.status_code == 201, response.get_json()
    user_id = response.get_json()['user']['id']
    return client, user_id


@pytest.fixture()
def owner_client(app):
    """Клиент с пользователем-владельцем комнаты."""
    client, user_id = _make_logged_in_client(app, 'room_owner', email='owner@example.com')
    return client, user_id


@pytest.fixture()
def guest_client(app):
    """Второй авторизованный клиент — для сценариев со вторым игроком."""
    client, user_id = _make_logged_in_client(app, 'second_player', email='second@example.com')
    return client, user_id


@pytest.fixture()
def third_client(app):
    """Третий авторизованный клиент."""
    client, user_id = _make_logged_in_client(app, 'third_player', email='third@example.com')
    return client, user_id
