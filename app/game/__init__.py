from app.game.engine import GameConfig, GameEngine, GameRuleError

class GameRoom:
    def __init__(self, room_id, player_ids, config=None, seed=None):
        self.room_id = str(room_id)
        self.engine = GameEngine(player_ids, config=config, seed=seed)

    def start_game(self):
        return self.engine.get_public_state()

    def get_state(self, viewer_id=None):
        return self.engine.get_public_state(viewer_id=viewer_id)

    def play_card(self, player_id, card_id, chosen_color=None):
        return self.engine.play_card(player_id, card_id, chosen_color=chosen_color)

    def draw_card(self, player_id):
        return self.engine.draw_card(player_id)

    def pass_turn(self, player_id):
        return self.engine.pass_turn(player_id)

    def call_svintus(self, player_id):
        return self.engine.call_svintus(player_id)

    def cover_deck_press(self, player_id):
        return self.engine.cover_deck_press(player_id)
