import pytest
from sqlalchemy.exc import IntegrityError
from app.models import User, Room, RoomPlayer, Game, Card, Move
from app.extensions import db

def test_create_user(app):
    with app.app_context():
        user = User(username="db_test_user", email="db@test.com")
        db.session.add(user)
        db.session.commit()
        
        fetched = User.query.filter_by(username="db_test_user").first()
        assert fetched is not None
        assert fetched.email == "db@test.com"
        assert fetched.wins == 0
        assert fetched.losses == 0

def test_unique_username(app):
    with app.app_context():
        u1 = User(username="unique_user")
        db.session.add(u1)
        db.session.commit()
        
        u2 = User(username="unique_user")
        db.session.add(u2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

def test_room_creation_and_relations(app):
    with app.app_context():
        u1 = User(username="room_owner")
        u2 = User(username="room_guest")
        db.session.add_all([u1, u2])
        db.session.commit()
        
        room = Room(owner_id=u1.id, invite_code="TESTCODE", max_players=4)
        db.session.add(room)
        db.session.commit()
        
        rp1 = RoomPlayer(room_id=room.id, user_id=u1.id, seat_index=0)
        rp2 = RoomPlayer(room_id=room.id, user_id=u2.id, seat_index=1, is_ready=True)
        db.session.add_all([rp1, rp2])
        db.session.commit()
        
        fetched_room = Room.query.filter_by(invite_code="TESTCODE").first()
        assert fetched_room is not None
        assert fetched_room.status == "waiting"
        
        players = RoomPlayer.query.filter_by(room_id=fetched_room.id).all()
        assert len(players) == 2
        
        ready_players = RoomPlayer.query.filter_by(room_id=fetched_room.id, is_ready=True).all()
        assert len(ready_players) == 1
        assert ready_players[0].user_id == u2.id

def test_game_models_creation(app):
    with app.app_context():
        u = User(username="game_tester")
        db.session.add(u)
        db.session.commit()
        
        r = Room(owner_id=u.id, invite_code="GAMECODE")
        db.session.add(r)
        db.session.commit()
        
        g = Game(room_id=r.id, current_player_idx=0, direction=1)
        db.session.add(g)
        db.session.commit()
        
        c1 = Card(game_id=g.id, owner_id=u.id, card_type="number", color="red", location="hand")
        c2 = Card(game_id=g.id, card_type="wild", location="deck")
        db.session.add_all([c1, c2])
        db.session.commit()
        
        m = Move(game_id=g.id, player_id=u.id, card_id=c1.id, move_type="play_card")
        db.session.add(m)
        db.session.commit()
        
        fetched_game = db.session.get(Game, g.id)
        assert fetched_game is not None
        assert fetched_game.direction == 1
        
        fetched_cards = Card.query.filter_by(game_id=g.id).all()
        assert len(fetched_cards) == 2
        
        fetched_moves = Move.query.filter_by(game_id=g.id).all()
        assert len(fetched_moves) == 1
        assert fetched_moves[0].move_type == "play_card"