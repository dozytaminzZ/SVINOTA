import uuid

from flask import Blueprint, request
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET'])
def auth_index():
    return {'status': 'auth module in development'}

def _json_error(message, status_code=400):
    return {'error': message}, status_code

def _user_payload(user):
    return {
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'wins': user.wins,
        'losses': user.losses
    }

def _unique_guest_username(base):
    suffix = uuid.uuid4().hex[:6]
    candidate = f"{base}-{suffix}"
    while User.query.filter_by(username=candidate).first() is not None:
        suffix = uuid.uuid4().hex[:6]
        candidate = f"{base}-{suffix}"
    return candidate

@auth_bp.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return _json_error('already authenticated', 400)

    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    email = (data.get('email') or '').strip() or None

    if not username or not password:
        return _json_error('username and password are required')
    if len(username) > 50:
        return _json_error('username too long')
    if len(password) < 6:
        return _json_error('password too short')

    if User.query.filter_by(username=username).first() is not None:
        return _json_error('username already exists')
    if email and User.query.filter_by(email=email).first() is not None:
        return _json_error('email already exists')

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()
    login_user(user)

    return {'status': 'ok', 'user': _user_payload(user)}, 201

@auth_bp.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return _json_error('already authenticated', 400)

    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''

    if not password or (not username and not email):
        return _json_error('username or email and password are required')

    user = None
    if email:
        user = User.query.filter_by(email=email).first()
    if user is None and username:
        user = User.query.filter_by(username=username).first()

    if user is None or not user.password_hash:
        return _json_error('invalid credentials', 401)
    if not check_password_hash(user.password_hash, password):
        return _json_error('invalid credentials', 401)

    login_user(user)
    return {'status': 'ok', 'user': _user_payload(user)}

@auth_bp.route('/guest', methods=['POST'])
def guest_login():
    if current_user.is_authenticated:
        return _json_error('already authenticated', 400)

    data = request.get_json(silent=True) or {}
    base_username = (data.get('username') or '').strip() or 'guest'
    base_username = base_username[:45]
    username = _unique_guest_username(base_username)

    user = User(username=username)
    db.session.add(user)
    db.session.commit()
    login_user(user)

    return {'status': 'ok', 'user': _user_payload(user)}, 201

@auth_bp.route('/logout', methods=['POST'])
def logout():
    if current_user.is_authenticated:
        logout_user()
    return {'status': 'ok'}

@auth_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    return {'status': 'ok', 'user': _user_payload(current_user)}
