import pytest
from app.extensions import db
from app.models import Room, RoomPlayer, User

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

def test_guest_leave_room_logs_out_and_removes_empty_room(client):
    client.get('/lobby/create')
    room = Room.query.first()
    user = User.query.first()

    assert room is not None
    assert user is not None
    assert user.is_guest is True

    res = client.post('/lobby/leave', data={
        'room_id': str(room.id),
        'next': 'index'
    })

    assert res.status_code == 302
    assert Room.query.count() == 0
    assert RoomPlayer.query.count() == 0
    assert User.query.filter_by(id=user.id).first() is None

    profile_res = client.get('/auth/profile')
    assert profile_res.status_code == 401

def test_owner_leave_waiting_room_deletes_room_and_players(app):
    owner_client = app.test_client()

    owner_client.get('/lobby/create')
    room = Room.query.first()
    joiner = User(username='joiner-guest', is_guest=True)
    db.session.add(joiner)
    db.session.flush()
    db.session.add(RoomPlayer(
        room_id=room.id,
        user_id=joiner.id,
        seat_index=1
    ))
    db.session.commit()

    assert RoomPlayer.query.filter_by(room_id=room.id).count() == 2

    leave_res = owner_client.post('/lobby/leave', data={
        'room_id': str(room.id),
        'next': 'index'
    })

    assert leave_res.status_code == 302
    assert db.session.get(Room, room.id) is None
    assert RoomPlayer.query.filter_by(room_id=room.id).count() == 0
    assert User.query.count() == 0

def test_non_owner_cannot_start_waiting_room(client):
    client.get('/lobby/create')
    room = Room.query.first()
    invite_code = room.invite_code

    client.post('/auth/logout')
    client.post('/auth/guest', json={'username': 'joiner'})
    client.post('/lobby/join', json={'invite_code': invite_code})

    res = client.post('/lobby/create')

    assert res.status_code == 403
    assert 'Начать игру может только создатель комнаты.' in res.get_data(as_text=True)
    assert db.session.get(Room, room.id).status == 'waiting'
