import random
import string
import uuid

from flask import Blueprint, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Room, RoomPlayer

lobby_bp = Blueprint('lobby', __name__)

@lobby_bp.route('/', methods=['GET'])
def lobby_index():
    return {'status': 'lobby module in development'}

def _json_error(message, status_code=400):
    return {'error': message}, status_code

def _get_request_data():
    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict()
    return data or {}

def _parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'y'}
    return bool(value)

def _unique_invite_code(length=8):
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(alphabet) for _ in range(length))
        if Room.query.filter_by(invite_code=code).first() is None:
            return code

def _room_payload(room, players_count):
    return {
        'id': str(room.id),
        'owner_id': str(room.owner_id),
        'invite_code': room.invite_code,
        'status': room.status,
        'max_players': room.max_players,
        'players_count': players_count,
        'is_private': room.is_private
    }

@lobby_bp.route('/rooms', methods=['GET'])
def get_rooms():
    public_only = request.args.get('public_only', '1').strip().lower()
    query = Room.query
    if public_only in {'1', 'true', 'yes', 'y'}:
        query = query.filter_by(is_private=False)

    rooms = query.all()
    payload = []
    for room in rooms:
        players_count = RoomPlayer.query.filter_by(room_id=room.id).count()
        payload.append(_room_payload(room, players_count))

    return {'status': 'ok', 'rooms': payload}

@lobby_bp.route('/create', methods=['POST'])
@login_required
def create_room():
    data = _get_request_data()
    max_players = data.get('max_players', 6)
    try:
        max_players = int(max_players)
    except (TypeError, ValueError):
        return _json_error('max_players must be an integer')

    if max_players < 2 or max_players > 6:
        return _json_error('max_players must be between 2 and 6')

    is_private = _parse_bool(data.get('is_private'), default=False)

    existing_membership = RoomPlayer.query.filter_by(user_id=current_user.id).first()
    if existing_membership is not None:
        return _json_error('user already in a room', 409)

    room = Room(
        owner_id=current_user.id,
        invite_code=_unique_invite_code(),
        status='waiting',
        max_players=max_players,
        is_private=is_private
    )
    db.session.add(room)
    db.session.flush()

    owner_member = RoomPlayer(
        room_id=room.id,
        user_id=current_user.id,
        seat_index=0
    )
    db.session.add(owner_member)
    db.session.commit()

    return {'status': 'ok', 'room': _room_payload(room, 1)}, 201

@lobby_bp.route('/join', methods=['POST'])
@login_required
def join_room():
    data = _get_request_data()
    room_id_raw = (data.get('room_id') or '').strip()
    invite_code = (data.get('invite_code') or '').strip().upper()

    if not room_id_raw and not invite_code:
        return _json_error('room_id or invite_code is required')

    room = None
    if invite_code:
        room = Room.query.filter_by(invite_code=invite_code).first()
    if room is None and room_id_raw:
        try:
            room_uuid = uuid.UUID(room_id_raw)
        except ValueError:
            return _json_error('invalid room_id')
        room = db.session.get(Room, room_uuid)

    if room is None:
        return _json_error('room not found', 404)
    if room.is_private and not invite_code:
        return _json_error('invite_code required for private room', 403)
    if room.status != 'waiting':
        return _json_error('room is not accepting players', 409)

    existing_membership = RoomPlayer.query.filter_by(user_id=current_user.id).first()
    if existing_membership is not None:
        if existing_membership.room_id == room.id:
            players_count = RoomPlayer.query.filter_by(room_id=room.id).count()
            return {'status': 'ok', 'room': _room_payload(room, players_count)}
        return _json_error('user already in a room', 409)

    current_players = RoomPlayer.query.filter_by(room_id=room.id).all()
    if len(current_players) >= room.max_players:
        return _json_error('room is full', 409)

    used_seats = {player.seat_index for player in current_players}
    seat_index = next(index for index in range(room.max_players) if index not in used_seats)

    member = RoomPlayer(room_id=room.id, user_id=current_user.id, seat_index=seat_index)
    db.session.add(member)
    db.session.commit()

    players_count = len(current_players) + 1
    return {'status': 'ok', 'room': _room_payload(room, players_count)}

@lobby_bp.route('/leave', methods=['POST'])
@login_required
def leave_room():
    data = _get_request_data()
    room_id_raw = (data.get('room_id') or '').strip()

    query = RoomPlayer.query.filter_by(user_id=current_user.id)
    if room_id_raw:
        try:
            room_uuid = uuid.UUID(room_id_raw)
        except ValueError:
            return _json_error('invalid room_id')
        query = query.filter_by(room_id=room_uuid)

    membership = query.first()
    if membership is None:
        return _json_error('user is not in a room', 404)

    room = db.session.get(Room, membership.room_id)
    db.session.delete(membership)
    db.session.flush()

    remaining = RoomPlayer.query.filter_by(room_id=membership.room_id).count()
    if remaining == 0 and room is not None:
        db.session.delete(room)

    db.session.commit()
    return {'status': 'ok'}
