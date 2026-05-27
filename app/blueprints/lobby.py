from flask import Blueprint, render_template

lobby_bp = Blueprint('lobby', __name__)


@lobby_bp.route('/game', methods=['GET'])
def game_table():
    return render_template('lobby.html')


@lobby_bp.route('/rooms', methods=['GET'])
def get_rooms():
    return {'status': 'not implemented'}
