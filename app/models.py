import uuid
from flask_login import UserMixin
from app.extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=True) # None для гостевых аккаунтов
    password_hash = db.Column(db.String(255), nullable=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)

class Room(db.Model):
    __tablename__ = 'rooms'
    
    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    invite_code = db.Column(db.String(8), unique=True, nullable=False)
    status = db.Column(db.String(20), default='waiting') # waiting, playing, finished
    max_players = db.Column(db.Integer, default=6)
    is_private = db.Column(db.Boolean, default=False, nullable=False)

class RoomPlayer(db.Model):
    __tablename__ = 'room_players'
    
    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('rooms.id'), nullable=False)
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    seat_index = db.Column(db.Integer, nullable=False)
    is_ready = db.Column(db.Boolean, default=False, nullable=False)

class Game(db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('rooms.id'), nullable=False)
    winner_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    current_player_idx = db.Column(db.Integer, default=0)
    direction = db.Column(db.Integer, default=1) # 1 - по часовой, -1 - против
    current_color = db.Column(db.String(10), nullable=True)

class Card(db.Model):
    __tablename__ = 'cards'
    
    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('games.id'), nullable=False)
    owner_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    card_type = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(10), nullable=True)
    location = db.Column(db.String(20), default='deck') # deck, hand, discard

class Move(db.Model):
    __tablename__ = 'moves'
    
    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('games.id'), nullable=False)
    player_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    card_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('cards.id'), nullable=True)
    move_type = db.Column(db.String(20), nullable=False)
