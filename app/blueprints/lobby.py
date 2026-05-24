from flask import Blueprint

lobby_bp = Blueprint('lobby', __name__)

@lobby_bp.route('/', methods=['GET'])
def lobby_index():
    return {'status': 'lobby module in development'}

@lobby_bp.route('/rooms', methods=['GET'])
def get_rooms():
    return {'status': 'rooms endpoint in development'}
