from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user

lobby_bp = Blueprint('lobby', __name__)


def get_max_players_from_form(default=6):
    try:
        max_players = int(request.form.get('max_players', default))
    except (TypeError, ValueError):
        return default

    return min(max(max_players, 2), 6)


@lobby_bp.route('/create', methods=['GET', 'POST'])
def create_game():
    creator_name = current_user.username if current_user.is_authenticated else 'Главный свинтус'
    max_players = 6

    if request.method == 'POST':
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
    return {'status': 'not implemented'}
