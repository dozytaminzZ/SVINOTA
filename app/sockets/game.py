from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room

from app.game.engine import GameRuleError
from app.game.service import (
    GameServiceError,
    create_game_for_room,
    finalize_room_if_finished,
    get_game_or_error,
    get_membership,
    parse_room_id
)


def register_game_socket_handlers(socketio):
    def emit_error(message, code="error"):
        emit("game:error", {"error": message, "code": code}, to=request.sid)

    def require_auth():
        if not current_user.is_authenticated:
            emit_error("authentication required", "auth_required")
            return False
        return True

    @socketio.on("game:join")
    def handle_join(data):
        if not require_auth():
            return
        try:
            room_id = parse_room_id((data or {}).get("room_id"))
            get_membership(room_id, current_user.id)
            join_room(str(room_id))
            emit("game:joined", {"room_id": str(room_id)}, to=request.sid)
        except (GameServiceError, GameRuleError) as exc:
            emit_error(str(exc), getattr(exc, "code", "error"))

    @socketio.on("game:leave")
    def handle_leave(data):
        if not require_auth():
            return
        try:
            room_id = parse_room_id((data or {}).get("room_id"))
            leave_room(str(room_id))
            emit("game:left", {"room_id": str(room_id)}, to=request.sid)
        except (GameServiceError, GameRuleError) as exc:
            emit_error(str(exc), getattr(exc, "code", "error"))

    @socketio.on("game:state")
    def handle_state(data):
        if not require_auth():
            return
        try:
            room_id = parse_room_id((data or {}).get("room_id"))
            get_membership(room_id, current_user.id)
            game = get_game_or_error(room_id)
            emit("game:state", game.get_state(viewer_id=current_user.id), to=request.sid)
        except (GameServiceError, GameRuleError) as exc:
            emit_error(str(exc), getattr(exc, "code", "error"))

    @socketio.on("game:create")
    def handle_create(data):
        if not require_auth():
            return
        try:
            room_id = parse_room_id((data or {}).get("room_id"))
            get_membership(room_id, current_user.id)
            game = create_game_for_room(room_id)
            public_state = game.get_state()
            private_state = game.get_state(viewer_id=current_user.id)
            emit("game:state", public_state, to=str(room_id))
            emit("game:state", private_state, to=request.sid)
        except (GameServiceError, GameRuleError) as exc:
            emit_error(str(exc), getattr(exc, "code", "error"))

    @socketio.on("game:play")
    def handle_play(data):
        if not require_auth():
            return
        try:
            payload = data or {}
            room_id = parse_room_id(payload.get("room_id"))
            get_membership(room_id, current_user.id)
            game = get_game_or_error(room_id)

            card_id = (payload.get("card_id") or "").strip()
            chosen_color = (payload.get("chosen_color") or "").strip().lower() or None
            if not card_id:
                emit_error("card_id required", "missing_card")
                return

            result = game.play_card(current_user.id, card_id, chosen_color=chosen_color)
            finalize_room_if_finished(room_id, game)

            public_state = game.get_state()
            private_state = game.get_state(viewer_id=current_user.id)
            emit("game:action", {"result": result}, to=request.sid)
            emit("game:state", public_state, to=str(room_id))
            emit("game:state", private_state, to=request.sid)
        except (GameServiceError, GameRuleError) as exc:
            emit_error(str(exc), getattr(exc, "code", "error"))

    @socketio.on("game:draw")
    def handle_draw(data):
        if not require_auth():
            return
        try:
            room_id = parse_room_id((data or {}).get("room_id"))
            get_membership(room_id, current_user.id)
            game = get_game_or_error(room_id)

            result = game.draw_card(current_user.id)
            finalize_room_if_finished(room_id, game)

            public_state = game.get_state()
            private_state = game.get_state(viewer_id=current_user.id)
            emit("game:action", {"result": result}, to=request.sid)
            emit("game:state", public_state, to=str(room_id))
            emit("game:state", private_state, to=request.sid)
        except (GameServiceError, GameRuleError) as exc:
            emit_error(str(exc), getattr(exc, "code", "error"))

    @socketio.on("game:pass")
    def handle_pass(data):
        if not require_auth():
            return
        try:
            room_id = parse_room_id((data or {}).get("room_id"))
            get_membership(room_id, current_user.id)
            game = get_game_or_error(room_id)

            result = game.pass_turn(current_user.id)
            finalize_room_if_finished(room_id, game)

            public_state = game.get_state()
            private_state = game.get_state(viewer_id=current_user.id)
            emit("game:action", {"result": result}, to=request.sid)
            emit("game:state", public_state, to=str(room_id))
            emit("game:state", private_state, to=request.sid)
        except (GameServiceError, GameRuleError) as exc:
            emit_error(str(exc), getattr(exc, "code", "error"))

    @socketio.on("game:svintus")
    def handle_svintus(data):
        if not require_auth():
            return
        try:
            room_id = parse_room_id((data or {}).get("room_id"))
            get_membership(room_id, current_user.id)
            game = get_game_or_error(room_id)

            result = game.call_svintus(current_user.id)

            public_state = game.get_state()
            private_state = game.get_state(viewer_id=current_user.id)
            emit("game:action", {"result": result}, to=request.sid)
            emit("game:state", public_state, to=str(room_id))
            emit("game:state", private_state, to=request.sid)
        except (GameServiceError, GameRuleError) as exc:
            emit_error(str(exc), getattr(exc, "code", "error"))

    @socketio.on("game:cover_press")
    def handle_cover_press(data):
        if not require_auth():
            return
        try:
            room_id = parse_room_id((data or {}).get("room_id"))
            get_membership(room_id, current_user.id)
            game = get_game_or_error(room_id)

            result = game.cover_deck_press(current_user.id)

            public_state = game.get_state()
            private_state = game.get_state(viewer_id=current_user.id)
            emit("game:action", {"result": result}, to=request.sid)
            emit("game:state", public_state, to=str(room_id))
            emit("game:state", private_state, to=request.sid)
        except (GameServiceError, GameRuleError) as exc:
            emit_error(str(exc), getattr(exc, "code", "error"))
