import random
import string
import uuid

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models import Room, RoomPlayer


lobby_bp = Blueprint('lobby', __name__)
@lobby_bp.route('/', methods=['GET'])
def lobby_index():
    return {'status': 'lobby module in development'}

def get_max_players_from_form(default=6):
    try:
        max_players = int(request.form.get('max_players', default))
    except (TypeError, ValueError):
        return default

    return min(max(max_players, 2), 6)


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


def _is_json_request():
    return request.is_json or request.headers.get('Accept') == 'application/json'


def _unique_invite_code(length=8):
    alphabet = string.ascii_uppercase + string.digits

    while True:
        code = ''.join(random.choice(alphabet) for _ in range(length))

        if Room.query.filter_by(invite_code=code).first() is None:
            return code


def _room_counts(room_id):
    players_count = RoomPlayer.query.filter_by(room_id=room_id).count()
    ready_count = RoomPlayer.query.filter_by(room_id=room_id, is_ready=True).count()

    return players_count, ready_count


def _room_payload(room, players_count=None, ready_count=None):
    if players_count is None or ready_count is None:
        players_count, ready_count = _room_counts(room.id)

    return {
        'id': str(room.id),
        'owner_id': str(room.owner_id),
        'invite_code': room.invite_code,
        'status': room.status,
        'max_players': room.max_players,
        'players_count': players_count,
        'ready_count': ready_count,
        'is_private': room.is_private
    }


@lobby_bp.route('/create', methods=['GET', 'POST'])
def create_game():
    creator_name = current_user.username if current_user.is_authenticated else 'Главный свинтус'
    max_players = 6

    if request.method == 'POST':
        if _is_json_request():
            if not current_user.is_authenticated:
                return _json_error('authentication required', 401)

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

            return {
                'status': 'ok',
                'room': _room_payload(room)
            }, 201

        max_players = get_max_players_from_form()

        return redirect(url_for('lobby.game_table', max_players=max_players))

    return render_template(
        'create_game.html',
        creator_name=creator_name,
        invite_code='SVN-7K3B',
        max_players=max_players,
    )


@lobby_bp.route('/join', methods=['GET', 'POST'])
def join_game():
    lobby_id = ''
    nickname = ''
    error = None

    if request.method == 'POST':
        if _is_json_request():
            if not current_user.is_authenticated:
                return _json_error('authentication required', 401)

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
                    return {
                        'status': 'ok',
                        'room': _room_payload(room)
                    }

                return _json_error('user already in a room', 409)

            current_players = RoomPlayer.query.filter_by(room_id=room.id).all()

            if len(current_players) >= room.max_players:
                return _json_error('room is full', 409)

            used_seats = {player.seat_index for player in current_players}
            seat_index = next(index for index in range(room.max_players) if index not in used_seats)

            member = RoomPlayer(
                room_id=room.id,
                user_id=current_user.id,
                seat_index=seat_index
            )

            db.session.add(member)
            db.session.commit()

            return {
                'status': 'ok',
                'room': _room_payload(room)
            }

        lobby_id = request.form.get('lobby_id', '').strip()
        nickname = request.form.get('nickname', '').strip()

        if not lobby_id:
            error = 'Укажите ID лобби'
        elif not nickname:
            error = 'Укажите ник'
        else:
            return redirect(url_for('lobby.game_table', lobby_id=lobby_id, nickname=nickname))

    return render_template(
        'join_game.html',
        lobby_id=lobby_id,
        nickname=nickname,
        error=error,
    )


@lobby_bp.route('/game', methods=['GET'])
def game_table():
    return render_template('lobby.html')


@lobby_bp.route('/rooms', methods=['GET'])
def get_rooms():
    public_only = request.args.get('public_only', '1').strip().lower()
    query = Room.query

    if public_only in {'1', 'true', 'yes', 'y'}:
        query = query.filter_by(is_private=False)

    rooms = query.all()

    return {
        'status': 'ok',
        'rooms': [_room_payload(room) for room in rooms]
    }


@lobby_bp.route('/leave', methods=['POST'])
def leave_room():
    if not current_user.is_authenticated:
        return _json_error('authentication required', 401)

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


@lobby_bp.route('/ready', methods=['POST'])
def set_ready():
    if not current_user.is_authenticated:
        return _json_error('authentication required', 401)

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

    if 'is_ready' in data:
        membership.is_ready = _parse_bool(data.get('is_ready'), default=False)
    else:
        membership.is_ready = not membership.is_ready

    db.session.commit()

    room = db.session.get(Room, membership.room_id)

    return {
        'status': 'ok',
        'is_ready': membership.is_ready,
        'room': _room_payload(room)
    }