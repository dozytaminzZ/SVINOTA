import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

COLORS = ["red", "yellow", "green", "blue"]
NUMBER_TYPE = "number"
SPECIAL_CARD_VALUES = {
    "skip": 8,
    "reverse": 9,
    "cover_deck": 10,
    "draw2": 11,
}
SPECIAL_TYPES = set(SPECIAL_CARD_VALUES)
BLACK_TYPES = {"wild", "wild_draw4"}

@dataclass
class Card:
    id: str
    color: Optional[str]
    type: str
    value: Optional[int] = None

    def to_dict(self):
        return {
            "id": self.id,
            "color": self.color,
            "type": self.type,
            "value": self.value
        }

@dataclass
class GameConfig:
    cards_per_player: int = 8
    svintus_timeout_sec: int = 3
    cover_deck_timeout_sec: int = 5
    penalty_invalid: int = 0
    penalty_svintus: int = 2
    penalty_cover_deck: int = 2
    allow_pass_without_draw: bool = False

@dataclass
class CoverDeckEvent:
    deadline_at: float
    presses: List[str] = field(default_factory=list)

    def seconds_left(self, now: float) -> int:
        return max(0, int(self.deadline_at - now))

@dataclass
class GameState:
    game_id: str
    players: List[str]
    hands: Dict[str, List[Card]]
    deck: List[Card]
    discard: List[Card]
    current_player_idx: int
    direction: int
    current_color: Optional[str]
    pending_draw: int = 0
    status: str = "playing"
    winner_id: Optional[str] = None
    svintus_deadlines: Dict[str, float] = field(default_factory=dict)
    cover_deck: Optional[CoverDeckEvent] = None
    turn_drawn: bool = False

class GameRuleError(Exception):
    def __init__(self, message: str, code: str = "invalid_action"):
        super().__init__(message)
        self.code = code

class GameEngine:
    def __init__(self, player_ids: List[str], config: Optional[GameConfig] = None, seed: Optional[int] = None, game_id: Optional[str] = None):
        if len(player_ids) < 2:
            raise GameRuleError("at least 2 players required", "invalid_setup")

        self.config = config or GameConfig()
        self._rng = random.Random(seed)
        players = [str(pid) for pid in player_ids]
        self.state = self._create_initial_state(players, game_id)

    def _create_initial_state(self, players: List[str], game_id: Optional[str]) -> GameState:
        deck = self._build_deck()
        self._rng.shuffle(deck)

        hands = {player_id: [] for player_id in players}
        for _ in range(self.config.cards_per_player):
            for player_id in players:
                hands[player_id].append(deck.pop())

        discard = [self._draw_start_discard(deck)]
        current_color = discard[-1].color

        return GameState(
            game_id=game_id or str(uuid.uuid4()),
            players=players,
            hands=hands,
            deck=deck,
            discard=discard,
            current_player_idx=self._rng.randrange(len(players)),
            direction=1,
            current_color=current_color
        )

    def _build_deck(self) -> List[Card]:
        deck = []
        for color in COLORS:
            deck.append(self._new_card(color=color, type=NUMBER_TYPE, value=0))
            for value in range(1, 8):
                deck.append(self._new_card(color=color, type=NUMBER_TYPE, value=value))
                deck.append(self._new_card(color=color, type=NUMBER_TYPE, value=value))
            for special, value in SPECIAL_CARD_VALUES.items():
                deck.append(self._new_card(color=color, type=special, value=value))
                deck.append(self._new_card(color=color, type=special, value=value))

        for _ in range(4):
            deck.append(self._new_card(color=None, type="wild", value=0))

        return deck

    def _new_card(self, color: Optional[str], type: str, value: Optional[int] = None) -> Card:
        return Card(id=str(uuid.uuid4()), color=color, type=type, value=value)

    def _draw_start_discard(self, deck: List[Card]) -> Card:
        while True:
            card = deck.pop()
            if card.color is not None:
                return card
            deck.insert(0, card)
            self._rng.shuffle(deck)

    def _reshuffle_if_needed(self):
        if self.state.deck:
            return
        if len(self.state.discard) <= 1:
            raise GameRuleError("deck is empty", "deck_empty")
        top = self.state.discard[-1]
        recycle = self.state.discard[:-1]
        self._rng.shuffle(recycle)
        self.state.deck = recycle
        self.state.discard = [top]

    def _draw_cards(self, count: int) -> List[Card]:
        cards = []
        for _ in range(count):
            self._reshuffle_if_needed()
            cards.append(self.state.deck.pop())
        return cards

    def _top_discard(self) -> Card:
        return self.state.discard[-1]

    def _current_player_id(self) -> str:
        return self.state.players[self.state.current_player_idx]

    def _advance_turn(self, skip_next: bool = False):
        step = 1 + (1 if skip_next else 0)
        self.state.current_player_idx = (self.state.current_player_idx + step * self.state.direction) % len(self.state.players)
        self.state.turn_drawn = False

    def _is_playable(self, card: Card) -> bool:
        top = self._top_discard()
        current_color = self.state.current_color or top.color
        if card.type in BLACK_TYPES:
            return True
        if card.color == current_color:
            return True
        if card.value is not None and top.value is not None and card.value == top.value:
            return True
        if card.type != NUMBER_TYPE and card.type == top.type:
            return True
        return False

    def _player_has_playable(self, player_id: str) -> bool:
        return any(self._is_playable(card) for card in self.state.hands[player_id])

    def _check_timeouts(self):
        now = time.time()
        overdue = [pid for pid, deadline in self.state.svintus_deadlines.items() if now >= deadline]
        for pid in overdue:
            self._draw_to_player(pid, self.config.penalty_svintus)
            del self.state.svintus_deadlines[pid]

        if self.state.cover_deck and now >= self.state.cover_deck.deadline_at:
            self._resolve_cover_deck_timeout(now)

    def _draw_to_player(self, player_id: str, count: int) -> List[Card]:
        cards = self._draw_cards(count)
        self.state.hands[player_id].extend(cards)
        return cards

    def _start_svintus_timer_if_needed(self, player_id: str):
        if len(self.state.hands[player_id]) == 1:
            self.state.svintus_deadlines[player_id] = time.time() + self.config.svintus_timeout_sec
        else:
            self.state.svintus_deadlines.pop(player_id, None)

    def _apply_invalid_penalty(self, player_id: str):
        if self.config.penalty_invalid <= 0:
            return
        self._draw_to_player(player_id, self.config.penalty_invalid)

    def _resolve_cover_deck_timeout(self, now: float):
        event = self.state.cover_deck
        if event is None:
            return

        missing = [pid for pid in self.state.players if pid not in event.presses]
        if missing:
            for pid in missing:
                self._draw_to_player(pid, self.config.penalty_cover_deck)
        elif event.presses:
            self._draw_to_player(event.presses[-1], self.config.penalty_cover_deck)

        self.state.cover_deck = None

    def get_public_state(self, viewer_id: Optional[str] = None) -> Dict:
        self._check_timeouts()
        now = time.time()

        players = []
        for pid in self.state.players:
            players.append({
                "id": pid,
                "hand_count": len(self.state.hands[pid]),
                "is_current": pid == self._current_player_id()
            })

        svintus = []
        for pid, deadline in self.state.svintus_deadlines.items():
            svintus.append({
                "player_id": pid,
                "seconds_left": max(0, int(deadline - now))
            })

        cover_deck = None
        if self.state.cover_deck:
            cover_deck = {
                "active": True,
                "seconds_left": self.state.cover_deck.seconds_left(now),
                "pressed_by": list(self.state.cover_deck.presses)
            }
        else:
            cover_deck = {"active": False}

        payload = {
            "game_id": self.state.game_id,
            "status": self.state.status,
            "players": players,
            "current_player_id": self._current_player_id(),
            "direction": self.state.direction,
            "current_color": self.state.current_color,
            "top_discard": self._top_discard().to_dict(),
            "deck_count": len(self.state.deck),
            "discard_count": len(self.state.discard),
            "pending_draw": self.state.pending_draw,
            "svintus": svintus,
            "cover_deck": cover_deck
        }

        if viewer_id is not None:
            viewer_id = str(viewer_id)
            payload["viewer_hand"] = [card.to_dict() for card in self.state.hands.get(viewer_id, [])]

        return payload

    def play_card(self, player_id: str, card_id: str, chosen_color: Optional[str] = None) -> Dict:
        self._check_timeouts()
        player_id = str(player_id)

        if self.state.status != "playing":
            raise GameRuleError("game is not active", "game_not_active")
        if self.state.cover_deck:
            raise GameRuleError("cover deck event active", "cover_deck_active")
        if player_id != self._current_player_id():
            self._apply_invalid_penalty(player_id)
            raise GameRuleError("Не ваша очередь", "not_your_turn")
        if self.state.pending_draw > 0:
            raise GameRuleError("draw penalty required", "draw_required")

        hand = self.state.hands[player_id]
        card = next((c for c in hand if c.id == card_id), None)
        if card is None:
            self._apply_invalid_penalty(player_id)
            raise GameRuleError("card not in hand", "card_missing")
        if not self._is_playable(card):
            self._apply_invalid_penalty(player_id)
            raise GameRuleError("Этой картой нельзя походить", "card_not_playable")

        if card.type in BLACK_TYPES:
            if chosen_color not in COLORS:
                raise GameRuleError("chosen_color required", "missing_color")

        hand.remove(card)
        self.state.discard.append(card)
        skip_next = False

        if card.type in BLACK_TYPES:
            self.state.current_color = chosen_color
        else:
            self.state.current_color = card.color

        if card.type == "skip":
            skip_next = True
        elif card.type == "reverse":
            self.state.direction *= -1
            if len(self.state.players) == 2:
                skip_next = True
        elif card.type == "draw2":
            self.state.pending_draw = 3
        elif card.type == "wild_draw4":
            self.state.pending_draw = 4
        elif card.type == "cover_deck":
            self.state.cover_deck = CoverDeckEvent(
                deadline_at=time.time() + self.config.cover_deck_timeout_sec,
                presses=[]
            )

        if len(hand) == 0:
            self.state.status = "finished"
            self.state.winner_id = player_id
            return {"status": "ok", "winner_id": player_id}

        self._start_svintus_timer_if_needed(player_id)
        self._advance_turn(skip_next=skip_next)

        return {"status": "ok"}

    def draw_card(self, player_id: str) -> Dict:
        self._check_timeouts()
        player_id = str(player_id)

        if self.state.status != "playing":
            raise GameRuleError("game is not active", "game_not_active")
        if self.state.cover_deck:
            raise GameRuleError("cover deck event active", "cover_deck_active")
        if player_id != self._current_player_id():
            self._apply_invalid_penalty(player_id)
            raise GameRuleError("Не ваша очередь", "not_your_turn")

        if self.state.pending_draw > 0:
            count = self.state.pending_draw
            cards = self._draw_to_player(player_id, count)
            self.state.pending_draw = 0
            self._advance_turn()
            return {
                "status": "ok",
                "penalty": True,
                "drawn": [card.to_dict() for card in cards]
            }

        cards = self._draw_to_player(player_id, 1)
        self.state.turn_drawn = True
        drawn = cards[0]

        return {
            "status": "ok",
            "penalty": False,
            "drawn": drawn.to_dict(),
            "playable": self._is_playable(drawn)
        }

    def pass_turn(self, player_id: str) -> Dict:
        self._check_timeouts()
        player_id = str(player_id)

        if self.state.status != "playing":
            raise GameRuleError("game is not active", "game_not_active")
        if self.state.cover_deck:
            raise GameRuleError("cover deck event active", "cover_deck_active")
        if player_id != self._current_player_id():
            self._apply_invalid_penalty(player_id)
            raise GameRuleError("Не ваша очередь", "not_your_turn")
        if self.state.pending_draw > 0:
            raise GameRuleError("draw penalty required", "draw_required")

        if not self.state.turn_drawn:
            if not self.config.allow_pass_without_draw and self._player_has_playable(player_id):
                raise GameRuleError("playable card available", "playable_card_available")

        self._advance_turn()
        return {"status": "ok"}

    def call_svintus(self, player_id: str) -> Dict:
        self._check_timeouts()
        player_id = str(player_id)

        deadline = self.state.svintus_deadlines.get(player_id)
        if deadline is None:
            raise GameRuleError("svintus not required", "svintus_not_required")

        self.state.svintus_deadlines.pop(player_id, None)
        return {"status": "ok"}

    def cover_deck_press(self, player_id: str) -> Dict:
        self._check_timeouts()
        player_id = str(player_id)

        event = self.state.cover_deck
        if event is None:
            raise GameRuleError("cover deck not active", "cover_deck_not_active")
        if player_id in event.presses:
            raise GameRuleError("already pressed", "already_pressed")

        event.presses.append(player_id)
        if len(event.presses) == len(self.state.players):
            self._draw_to_player(event.presses[-1], self.config.penalty_cover_deck)
            self.state.cover_deck = None

        return {"status": "ok"}
