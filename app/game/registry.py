from typing import Dict, Optional

from app.game import GameRoom
from app.game.engine import GameConfig

_REGISTRY: Dict[str, GameRoom] = {}


def get_game(room_id: str) -> Optional[GameRoom]:
    return _REGISTRY.get(str(room_id))


def create_game(room_id: str, player_ids, config: Optional[GameConfig] = None, seed: Optional[int] = None) -> GameRoom:
    key = str(room_id)
    if key in _REGISTRY:
        raise ValueError("game already exists")
    game = GameRoom(room_id=key, player_ids=player_ids, config=config, seed=seed)
    _REGISTRY[key] = game
    return game


def remove_game(room_id: str) -> Optional[GameRoom]:
    return _REGISTRY.pop(str(room_id), None)
