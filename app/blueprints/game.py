from flask import Blueprint, request
from flask_login import current_user, login_required

from app.game.engine import GameRuleError
from app.game.service import (
    GameServiceError,
    create_game_for_room,
    finalize_room_if_finished,
    get_game_or_error,
    get_membership,
    get_room,
    parse_room_id
)


game_bp = Blueprint("game", __name__)


@game_bp.route("/", methods=["GET"])
def game_index():
    return {"status": "game module in development"}


def _json_error(message, code="error", status_code=400):
    return {"error": message, "code": code}, status_code


def _get_request_data():
    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict()
    return data or {}


def _get_room_id_from_data(data):
    return parse_room_id((data.get("room_id") or "").strip())


def _state_payload(game, viewer_id):
    return game.get_state(viewer_id=viewer_id)


@game_bp.route("/state", methods=["GET"])
@login_required
def get_state():
    room_id_raw = request.args.get("room_id")
    try:
        room_id = parse_room_id(room_id_raw)
        get_membership(room_id, current_user.id)
        game = get_game_or_error(room_id)
        return {"status": "ok", "state": _state_payload(game, current_user.id)}
    except (GameServiceError, GameRuleError) as exc:
        status_code = getattr(exc, "status_code", 400)
        return _json_error(str(exc), getattr(exc, "code", "error"), status_code)


@game_bp.route("/create", methods=["POST"])
@login_required
def create_game():
    data = _get_request_data()
    try:
        room_id = _get_room_id_from_data(data)
        get_membership(room_id, current_user.id)
        game = create_game_for_room(room_id, starter_id=current_user.id)
        return {"status": "ok", "state": _state_payload(game, current_user.id)}, 201
    except (GameServiceError, GameRuleError) as exc:
        status_code = getattr(exc, "status_code", 400)
        return _json_error(str(exc), getattr(exc, "code", "error"), status_code)


@game_bp.route("/play", methods=["POST"])
@login_required
def play_card():
    data = _get_request_data()
    try:
        room_id = _get_room_id_from_data(data)
        get_membership(room_id, current_user.id)
        game = get_game_or_error(room_id)

        card_id = (data.get("card_id") or "").strip()
        chosen_color = (data.get("chosen_color") or "").strip().lower() or None
        if not card_id:
            return _json_error("card_id required", "missing_card")

        result = game.play_card(current_user.id, card_id, chosen_color=chosen_color)
        finalize_room_if_finished(room_id, game)

        return {"status": "ok", "result": result, "state": _state_payload(game, current_user.id)}
    except (GameServiceError, GameRuleError) as exc:
        status_code = getattr(exc, "status_code", 400)
        return _json_error(str(exc), getattr(exc, "code", "error"), status_code)


@game_bp.route("/draw", methods=["POST"])
@login_required
def draw_card():
    data = _get_request_data()
    try:
        room_id = _get_room_id_from_data(data)
        get_membership(room_id, current_user.id)
        game = get_game_or_error(room_id)

        result = game.draw_card(current_user.id)
        finalize_room_if_finished(room_id, game)

        return {"status": "ok", "result": result, "state": _state_payload(game, current_user.id)}
    except (GameServiceError, GameRuleError) as exc:
        status_code = getattr(exc, "status_code", 400)
        return _json_error(str(exc), getattr(exc, "code", "error"), status_code)


@game_bp.route("/pass", methods=["POST"])
@login_required
def pass_turn():
    data = _get_request_data()
    try:
        room_id = _get_room_id_from_data(data)
        get_membership(room_id, current_user.id)
        game = get_game_or_error(room_id)

        result = game.pass_turn(current_user.id)
        finalize_room_if_finished(room_id, game)

        return {"status": "ok", "result": result, "state": _state_payload(game, current_user.id)}
    except (GameServiceError, GameRuleError) as exc:
        status_code = getattr(exc, "status_code", 400)
        return _json_error(str(exc), getattr(exc, "code", "error"), status_code)


@game_bp.route("/svintus", methods=["POST"])
@login_required
def call_svintus():
    data = _get_request_data()
    try:
        room_id = _get_room_id_from_data(data)
        get_membership(room_id, current_user.id)
        game = get_game_or_error(room_id)

        result = game.call_svintus(current_user.id)
        return {"status": "ok", "result": result, "state": _state_payload(game, current_user.id)}
    except (GameServiceError, GameRuleError) as exc:
        status_code = getattr(exc, "status_code", 400)
        return _json_error(str(exc), getattr(exc, "code", "error"), status_code)


@game_bp.route("/cover-press", methods=["POST"])
@login_required
def cover_deck_press():
    data = _get_request_data()
    try:
        room_id = _get_room_id_from_data(data)
        get_membership(room_id, current_user.id)
        game = get_game_or_error(room_id)

        result = game.cover_deck_press(current_user.id)
        return {"status": "ok", "result": result, "state": _state_payload(game, current_user.id)}
    except (GameServiceError, GameRuleError) as exc:
        status_code = getattr(exc, "status_code", 400)
        return _json_error(str(exc), getattr(exc, "code", "error"), status_code)
