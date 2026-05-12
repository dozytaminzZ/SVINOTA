from flask import Blueprint

lobby_bp = Blueprint('lobby', __name__)

@lobby_bp.route('/rooms', methods=['GET'])
def get_rooms():
    return {'status': 'not implemented'}
