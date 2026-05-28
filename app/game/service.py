import uuid
from typing import List, Optional

from app.extensions import db
from app.game.engine import GameRuleError
from app.game.registry import create_game, get_game
from app.models import Room, RoomPlayer


class GameServiceError(Exception):
    def __init__(self, message: str, code: str = "service_error", status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def parse_room_id(room_id_raw: Optional[str]) -> uuid.UUID:
    if not room_id_raw:
        raise GameServiceError("room_id required", "missing_room_id")
    try:
        return uuid.UUID(str(room_id_raw))
    except ValueError:
        raise GameServiceError("invalid room_id", "invalid_room_id")


def get_room(room_id: uuid.UUID) -> Room:
    room = db.session.get(Room, room_id)
    if room is None:
        raise GameServiceError("room not found", "room_not_found", 404)
    return room


def get_membership(room_id: uuid.UUID, user_id) -> RoomPlayer:
    membership = RoomPlayer.query.filter_by(room_id=room_id, user_id=user_id).first()
    if membership is None:
        raise GameServiceError("user is not in this room", "not_in_room", 403)
    return membership


def get_player_ids(room_id: uuid.UUID) -> List[str]:
    players = RoomPlayer.query.filter_by(room_id=room_id).order_by(RoomPlayer.seat_index).all()
    if len(players) < 2:
        raise GameServiceError("not enough players to start", "not_enough_players", 409)
    return [str(player.user_id) for player in players]


def get_game_or_error(room_id: uuid.UUID):
    game = get_game(str(room_id))
    if game is None:
        raise GameServiceError("game not found", "game_not_found", 404)
    return game


def create_game_for_room(room_id: uuid.UUID, starter_id=None):
    room_id = parse_room_id(room_id)
    room = get_room(room_id)

    if starter_id is not None:
        try:
            starter_id = uuid.UUID(str(starter_id))
        except ValueError:
            raise GameServiceError("invalid starter_id", "invalid_starter_id")

    if starter_id is not None and room.owner_id != starter_id:
        raise GameServiceError("only room owner can start the game", "not_room_owner", 403)

    if get_game(str(room_id)) is not None:
        raise GameServiceError("game already exists", "game_exists", 409)

    player_ids = get_player_ids(room_id)
    game = create_game(str(room_id), player_ids)

    room.status = "playing"
    db.session.commit()

    return game


def finalize_room_if_finished(room_id: uuid.UUID, game):
    if game.engine.state.status != "finished":
        return
    room = db.session.get(Room, room_id)
    if room is None:
        return
    room.status = "finished"
    db.session.commit()
