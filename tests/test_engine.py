import pytest
import uuid
import time
from app.game.engine import GameEngine, GameConfig, GameState, GameRuleError

@pytest.fixture
def players():
    return [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())]

@pytest.fixture
def config():
    return GameConfig(
        cards_per_player=5, # Уменьшаем для тестов
        svintus_timeout_sec=3,
        cover_deck_timeout_sec=5,
        penalty_invalid=2,
        penalty_svintus=2,
        penalty_cover_deck=2,
        allow_pass_without_draw=False
    )

@pytest.fixture
def engine(players, config):
    # Фиксированный seed для воспроизводимости (опционально, но помогает)
    return GameEngine(player_ids=players, config=config, seed=42)

def test_engine_initialization(engine, players, config):
    assert len(engine.state.players) == 3
    for p in players:
        assert len(engine.state.hands[p]) == config.cards_per_player
    assert len(engine.state.discard) == 1
    assert engine.state.current_color is not None
    assert engine.state.status == "playing"
    assert engine.state.direction == 1
    assert engine.state.pending_draw == 0

def test_game_rule_error_few_players():
    with pytest.raises(GameRuleError) as exc:
        GameEngine(player_ids=[str(uuid.uuid4())])
    assert exc.value.code == "invalid_setup"

def test_draw_card(engine):
    current_player = engine._current_player_id()
    initial_hand_size = len(engine.state.hands[current_player])
    
    res = engine.draw_card(current_player)
    assert res["status"] == "ok"
    assert res["penalty"] is False
    assert len(engine.state.hands[current_player]) == initial_hand_size + 1
    assert engine.state.turn_drawn is True

def test_draw_card_not_your_turn(engine):
    current_player = engine._current_player_id()
    not_current = [p for p in engine.state.players if p != current_player][0]
    
    # Пытаемся взять карту не в свой ход
    initial_hand_size = len(engine.state.hands[not_current])
    with pytest.raises(GameRuleError) as exc:
        engine.draw_card(not_current)
        
    assert exc.value.code == "not_your_turn"
    # Должен быть выписан штраф за ошибку
    assert len(engine.state.hands[not_current]) == initial_hand_size + engine.config.penalty_invalid

def test_default_invalid_move_does_not_draw_penalty(players):
    engine = GameEngine(player_ids=players, seed=42)
    current_player = engine._current_player_id()
    not_current = [p for p in engine.state.players if p != current_player][0]
    initial_hand_size = len(engine.state.hands[not_current])

    with pytest.raises(GameRuleError) as exc:
        engine.draw_card(not_current)

    assert exc.value.code == "not_your_turn"
    assert len(engine.state.hands[not_current]) == initial_hand_size

def test_play_valid_card(engine):
    current_player = engine._current_player_id()
    # Искусственно кладем ему в руку карту, подходящую по цвету
    current_color = engine.state.current_color
    top_card = engine.state.discard[-1]
    
    valid_card = None
    for c in engine.state.hands[current_player]:
        if engine._is_playable(c):
            valid_card = c
            break
            
    # Если на руках нет подходящей, дадим искусственно
    if not valid_card:
        valid_card = engine._new_card(color=current_color, type="number", value=1)
        engine.state.hands[current_player].append(valid_card)
        
    res = engine.play_card(current_player, valid_card.id)
    assert res["status"] == "ok"
    assert engine.state.discard[-1] == valid_card
    assert valid_card not in engine.state.hands[current_player]
    
def test_play_invalid_card(engine):
    current_player = engine._current_player_id()
    # Делаем карту гарантированно неподходящей
    current_color = engine.state.current_color
    wrong_color = "red" if current_color != "red" else "blue"
    
    invalid_card = engine._new_card(color=wrong_color, type="number", value=99)
    engine.state.hands[current_player].append(invalid_card)
    
    with pytest.raises(GameRuleError) as exc:
        engine.play_card(current_player, invalid_card.id)

    assert exc.value.code == "card_not_playable"

def test_win_condition(engine):
    current_player = engine._current_player_id()
    
    # Оставляем только 1 карту
    valid_card = engine._new_card(color=engine.state.current_color, type="number", value=1)
    engine.state.hands[current_player] = [valid_card]
    
    res = engine.play_card(current_player, valid_card.id)
    assert res["status"] == "ok"
    assert res["winner_id"] == current_player
    assert engine.state.status == "finished"

def test_draw2_penalty(engine):
    current_player = engine._current_player_id()
    draw2_card = engine._new_card(color=engine.state.current_color, type="draw2")
    engine.state.hands[current_player].append(draw2_card)
    
    # Игрок кидает draw2
    engine.play_card(current_player, draw2_card.id)
    
    assert engine.state.pending_draw == 2
    next_player = engine._current_player_id()
    assert next_player != current_player
    
    # Следующий игрок пытается сходить, хотя должен взять 2 карты
    valid_card = engine._new_card(color=engine.state.current_color, type="number", value=2)
    engine.state.hands[next_player].append(valid_card)
    
    with pytest.raises(GameRuleError) as exc:
        engine.play_card(next_player, valid_card.id)
    assert exc.value.code == "draw_required"
    
    # Следующий игрок берет штраф (он тянет карты)
    initial_hand = len(engine.state.hands[next_player])
    res = engine.draw_card(next_player)
    assert res["penalty"] is True
    assert len(engine.state.hands[next_player]) == initial_hand + 2
    assert engine.state.pending_draw == 0
