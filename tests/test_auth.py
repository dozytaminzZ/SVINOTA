import pytest
from app.models import User
from app.extensions import db

def test_index_route(client):
    res = client.get('/')
    assert res.status_code == 200
    assert res.json['status'] == 'ok'

def test_auth_index(client):
    res = client.get('/auth/')
    assert res.status_code == 200

def test_register(client):
    res = client.post('/auth/register', json={
        'username': 'testuser',
        'password': 'password123',
        'email': 'test@test.com'
    })
    assert res.status_code == 201
    assert res.json['status'] == 'ok'
    assert 'user' in res.json
    assert res.json['user']['username'] == 'testuser'

def test_register_duplicate(client):
    client.post('/auth/register', json={
        'username': 'testuser',
        'password': 'password123'
    })
    # Пытаемся зарегистрировать еще раз
    res = client.post('/auth/register', json={
        'username': 'testuser',
        'password': 'password123'
    })
    assert res.status_code == 400

def test_register_rejects_blank_username(client):
    res = client.post('/auth/register', json={
        'username': '   ',
        'password': 'password123'
    })

    assert res.status_code == 400
    assert 'error' in res.json

def test_login(client):
    client.post('/auth/register', json={
        'username': 'testuser',
        'password': 'password123'
    })
    client.post('/auth/logout') # Выходим, чтобы потом войти

    res = client.post('/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    assert res.status_code == 200
    assert res.json['user']['username'] == 'testuser'

def test_invalid_login(client):
    res = client.post('/auth/login', json={
        'username': 'notexists',
        'password': 'wrongpassword'
    })
    assert res.status_code == 401

def test_guest_login(client):
    res = client.post('/auth/guest', json={'username': 'myguest'})
    assert res.status_code == 201
    assert 'myguest' in res.json['user']['username']

def test_profile_protected(client):
    # Не авторизован
    res = client.get('/auth/profile')
    assert res.status_code == 401

def test_profile_authorized(client):
    client.post('/auth/guest')
    res = client.get('/auth/profile')
    assert res.status_code == 200
    assert 'user' in res.json

def test_page_profile_guest_redirects_to_auth(client):
    client.post('/auth/guest')
    res = client.get('/profile')
    assert res.status_code == 302
    assert '/auth/' in res.location

def test_page_profile_registered_user_opens(client):
    client.post('/auth/register', json={
        'username': 'profileuser',
        'password': 'password123'
    })

    res = client.get('/profile')
    assert res.status_code == 200
