import pytest
import uuid
from app.game.registry import _REGISTRY
from app.game.service import create_game_for_room
from app.extensions import db
from app.models import RoomPlayer, User

def login_guest(client, username):
    res = client.post('/auth/guest', json={'username': username})
    return res.json['user']

@pytest.fixture
def test_room(client):
    # Очищаем реестр игр до начала теста
    _REGISTRY.clear()
    
    # Регаем двух игроков
    p1_user = login_guest(client, 'player1')
    p1 = p1_user['id']
    res1 = client.post('/lobby/create', json={'max_players': 2})
    room_id = res1.json['room']['id']
    invite_code = res1.json['room']['invite_code']
    
    # Второй игрок заходит
    client.post('/auth/logout')
    p2_user = login_guest(client, 'player2')
    p2 = p2_user['id']
    client.post('/lobby/join', json={'invite_code': invite_code})
    
    return {
        'room_id': room_id,
        'p1': p1,
        'p1_username': p1_user['username'],
        'p2': p2,
        'p2_username': p2_user['username']
    }

def test_game_index(client):
    res = client.get('/game/')
    assert res.status_code == 200

def test_create_game(client, test_room):
    room_id = test_room['room_id']
    # Текущий пользователь - p2, не создатель комнаты.
    res = client.post('/game/create', json={'room_id': room_id})
    assert res.status_code == 403
    assert res.json['code'] == 'not_room_owner'

def test_create_game_owner_only(client, test_room):
    room_id = test_room['room_id']
    client.post('/auth/logout')
    client.post('/auth/guest', json={'username': 'owner-check'})

    # Новый пользователь не состоит в комнате и не может стартовать игру.
    res = client.post('/game/create', json={'room_id': room_id})
    assert res.status_code == 403

def test_create_game_by_owner(app):
    owner_client = app.test_client()

    owner = login_guest(owner_client, 'owner')
    create_res = owner_client.post('/lobby/create', json={'max_players': 2})
    room_id = create_res.json['room']['id']
    joiner = User(username='joiner', is_guest=True)
    db.session.add(joiner)
    db.session.flush()
    db.session.add(RoomPlayer(
        room_id=uuid.UUID(room_id),
        user_id=joiner.id,
        seat_index=1
    ))
    db.session.commit()

    res = owner_client.post('/game/create', json={'room_id': room_id})
    assert res.status_code == 201
    assert 'state' in res.json
    assert res.json['state']['status'] == 'playing'
    
    # room_id должен стать playing в бд (опосредованно)
    db_room = owner_client.get('/lobby/rooms').json['rooms']
    target = [r for r in db_room if r['id'] == room_id][0]
    assert target['status'] == 'playing'

def test_get_state(client, test_room):
    room_id = test_room['room_id']
    create_game_for_room(room_id, starter_id=test_room['p1'])
    
    res = client.get(f'/game/state?room_id={room_id}')
    assert res.status_code == 200
    state = res.json['state']
    assert 'game_id' in state
    assert 'viewer_hand' in state

def test_game_draw_card(client, test_room):
    room_id = test_room['room_id']
    create_game_for_room(room_id, starter_id=test_room['p1'])
    
    # p2 делает запрос, чтобы получить state
    res = client.get(f'/game/state?room_id={room_id}')
    state = res.json['state']
    current_player_id = state['current_player_id']
    
    # Только тот игрок, чей ход, может тянуть:
    if test_room['p2'] != current_player_id:
        # P2 пытается вытянуть в ход P1
        draw_res = client.post('/game/draw', json={'room_id': room_id})
        assert draw_res.status_code == 400
        assert draw_res.json['code'] == 'not_your_turn'
    else:
        # P2 сейчас ходит
        draw_res = client.post('/game/draw', json={'room_id': room_id})
        assert draw_res.status_code == 200
        assert draw_res.json['result']['status'] == 'ok'
