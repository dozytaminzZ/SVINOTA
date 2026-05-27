import pytest
import uuid
from app.extensions import socketio, db
from app.models import User, RoomPlayer
from app.game.registry import _REGISTRY

def login_guest(client, username):
    res = client.post('/auth/guest', json={'username': username})
    return res.json['user']

@pytest.fixture
def socket_room(app, client):
    _REGISTRY.clear()
    
    p1 = login_guest(client, 'sock_owner')
    res = client.post('/lobby/create', json={'max_players': 2})
    room_id = res.json['room']['id']
    
    # Добавляем второго игрока напрямую через БД для старта игры
    with app.app_context():
        p2 = User(username='sock_guest')
        db.session.add(p2)
        db.session.commit()
        
        rp2 = RoomPlayer(room_id=uuid.UUID(room_id), user_id=p2.id, seat_index=1)
        db.session.add(rp2)
        db.session.commit()
        
    return room_id

def test_unauthenticated_join(app):
    client = app.test_client()
    sio_client = socketio.test_client(app, flask_test_client=client)
    
    sio_client.emit('game:join', {'room_id': str(uuid.uuid4())})
    received = sio_client.get_received()
    assert len(received) > 0
    assert received[0]['args'][0]['code'] == 'auth_required'

def test_game_join_leave(app, client, socket_room):
    sio_client = socketio.test_client(app, flask_test_client=client)
    
    sio_client.emit('game:join', {'room_id': socket_room})
    r_join = sio_client.get_received()
    assert r_join[0]['name'] == 'game:joined'
    
    sio_client.emit('game:leave', {'room_id': socket_room})
    r_leave = sio_client.get_received()
    assert r_leave[0]['name'] == 'game:left'

def test_game_create_and_state(app, client, socket_room):
    sio_client = socketio.test_client(app, flask_test_client=client)
    
    # Создаем игру
    sio_client.emit('game:create', {'room_id': socket_room})
    events = sio_client.get_received()
    
    # Должен сгенерироваться private_state конкретно этому клиенту.
    # Так как test_client в Flask-SocketIO не всегда ловит широковещательные ответы(room), 
    # иногда мы получаем только 1 ивент. Главное - он должен быть game:state
    state_events = [e for e in events if e['name'] == 'game:state']
    assert len(state_events) >= 1
    assert state_events[0]['args'][0]['status'] == 'playing'

def test_game_play_missing_card(app, client, socket_room):
    sio_client = socketio.test_client(app, flask_test_client=client)
    sio_client.emit('game:create', {'room_id': socket_room})
    sio_client.get_received() # Чистим очередь
    
    sio_client.emit('game:play', {'room_id': socket_room, 'card_id': ''})
    events = sio_client.get_received()
    
    err = [e for e in events if e['name'] == 'game:error'][0]
    assert err['args'][0]['code'] == 'missing_card'
    
def test_game_draw_card(app, client, socket_room):
    sio_client = socketio.test_client(app, flask_test_client=client)
    sio_client.emit('game:create', {'room_id': socket_room})
    sio_client.get_received() # Чистим очередь
    
    sio_client.emit('game:draw', {'room_id': socket_room})
    events = sio_client.get_received()
    
    names = [e['name'] for e in events]
    # Поскольку текущий игрок в начале определяется случайно, 
    # запрос может оказаться в свой ход или не в свой
    if 'game:error' in names:
        err = [e for e in events if e['name'] == 'game:error'][0]
        assert err['args'][0]['code'] == 'not_your_turn'
    else:
        assert 'game:action' in names