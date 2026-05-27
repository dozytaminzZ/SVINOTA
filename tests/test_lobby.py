import pytest
from app.models import Room, RoomPlayer

def test_lobby_index(client):
    res = client.get('/lobby/')
    assert res.status_code == 200

def test_get_rooms(client):
    res = client.get('/lobby/rooms')
    assert res.status_code == 200
    assert 'rooms' in res.json
    assert type(res.json['rooms']) is list

def login_guest(client, username):
    res = client.post('/auth/guest', json={'username': username})
    assert res.status_code == 201
    return res.json['user']['id']

def test_create_room(client):
    login_guest(client, 'creator')
    res = client.post('/lobby/create', json={'max_players': 4, 'is_private': False})
    
    assert res.status_code == 201
    assert res.json['status'] == 'ok'
    room = res.json['room']
    assert room['max_players'] == 4
    assert room['is_private'] is False
    assert room['players_count'] == 1
    assert room['ready_count'] == 0

def test_create_room_already_in_room(client):
    login_guest(client, 'creator2')
    client.post('/lobby/create', json={'max_players': 4})
    
    res2 = client.post('/lobby/create', json={'max_players': 4})
    assert res2.status_code == 409
    assert res2.json['error'] == 'user already in a room'

def test_join_room_by_invite(client):
    # Создатель
    login_guest(client, 'creator3')
    res = client.post('/lobby/create', json={'max_players': 4})
    invite_code = res.json['room']['invite_code']
    
    # Чтобы другой игрок мог зайти, нужно вылогиниться и зайти под другим
    client.post('/auth/logout')
    login_guest(client, 'joiner')
    
    join_res = client.post('/lobby/join', json={'invite_code': invite_code})
    assert join_res.status_code == 200
    assert join_res.json['room']['players_count'] == 2

def test_join_private_room_needs_invite(client):
    login_guest(client, 'creator4')
    res = client.post('/lobby/create', json={'max_players': 4, 'is_private': True})
    room_id = res.json['room']['id']
    
    client.post('/auth/logout')
    login_guest(client, 'joiner2')
    
    # Пытаемся зайти по ID в приватную комнату без invite
    join_res = client.post('/lobby/join', json={'room_id': room_id})
    assert join_res.status_code == 403
    assert join_res.json['error'] == 'invite_code required for private room'

def test_ready_status(client):
    login_guest(client, 'readyuser')
    client.post('/lobby/create', json={'max_players': 4})
    
    res = client.post('/lobby/ready')
    assert res.status_code == 200
    assert res.json['status'] == 'ok'
    
    # В ответе из test_ready не возвращается room, но можно проверить в БД или через /lobby/rooms
    # Тут просто пробили статус код 200
    
def test_leave_room(client):
    login_guest(client, 'leaveuser')
    client.post('/lobby/create', json={'max_players': 4})
    
    res = client.post('/lobby/leave')
    assert res.status_code == 200
    assert res.json['status'] == 'ok'
