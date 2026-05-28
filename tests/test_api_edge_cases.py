import pytest
from app.game.service import create_game_for_room
from app.models import Room

def test_auth_missing_fields(client):
    res = client.post('/auth/register', json={'username': 'missing_pass'})
    assert res.status_code == 400
    assert 'error' in res.json

    res = client.post('/auth/login', json={'username': 'missing_pass'})
    assert res.status_code == 400
    assert 'error' in res.json

def login_guest(client, username):
    res = client.post('/auth/guest', json={'username': username})
    return res.json['user']['id']

def test_join_room_invalid_uuid(client):
    login_guest(client, 'hacker')
    res = client.post('/lobby/join', json={'room_id': 'not-a-uuid'})
    assert res.status_code == 400
    assert res.json['error'] == 'invalid room_id'

def test_join_non_existent_room(client):
    login_guest(client, 'hacker2')
    import uuid
    res = client.post('/lobby/join', json={'room_id': str(uuid.uuid4())})
    assert res.status_code == 404
    assert res.json['error'] == 'room not found'

def test_create_game_for_non_existent_room(client):
    login_guest(client, 'hacker3')
    import uuid
    res = client.post('/game/create', json={'room_id': str(uuid.uuid4())})
    # Должна быть ошибка 403, так как пользователя там нет, или 404, если комнаты нет.
    # В blueprint `get_membership` отрабатывает раньше и вернет 403 user is not in this room
    assert res.status_code == 403
    assert res.json['code'] == 'not_in_room'

def test_play_card_missing_data(client):
    # Создать комнату, игру...
    p1 = login_guest(client, 'p1')
    r1 = client.post('/lobby/create', json={'max_players': 2})
    room_id = r1.json['room']['id']
    
    client.post('/auth/logout')
    p2 = login_guest(client, 'p2')
    client.post('/lobby/join', json={'invite_code': r1.json['room']['invite_code']})
    
    create_game_for_room(room_id, starter_id=p1)
    
    # Пытаемся сделать play без card_id
    res = client.post('/game/play', json={'room_id': room_id}) # card_id missing
    assert res.status_code == 400
    assert res.json['code'] == 'missing_card'
