import uuid

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User


auth_bp = Blueprint('auth', __name__)


def _json_error(message, status_code=400):
    return {'error': message}, status_code


def _get_request_data():
    data = request.get_json(silent=True)

    if data is None:
        data = request.form.to_dict()

    return data or {}


def _is_json_request():
    return request.is_json or request.headers.get('Accept') == 'application/json'


def _is_real_user_authenticated():
    return (
        current_user.is_authenticated
        and not getattr(current_user, 'is_guest', False)
    )


def _user_payload(user):
    return {
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'is_guest': user.is_guest,
        'wins': user.wins,
        'losses': user.losses
    }


def _unique_guest_username(base):
    base = (base or 'guest').strip()[:45] or 'guest'
    suffix = uuid.uuid4().hex[:6]
    candidate = f"{base}-{suffix}"

    while User.query.filter_by(username=candidate).first() is not None:
        suffix = uuid.uuid4().hex[:6]
        candidate = f"{base}-{suffix}"

    return candidate


def _upgrade_guest_to_real_user(username, password, email=None):
    current_user.username = username
    current_user.email = email
    current_user.password_hash = generate_password_hash(password)
    current_user.is_guest = False

    db.session.commit()
    login_user(current_user)

    return current_user


def _create_real_user(username, password, email=None):
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        is_guest=False
    )

    db.session.add(user)
    db.session.commit()
    login_user(user)

    return user


@auth_bp.route('/', methods=['GET', 'POST'])
def index():
    if _is_real_user_authenticated():
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if (
            not user
            or user.is_guest
            or not user.password_hash
            or not check_password_hash(user.password_hash, password)
        ):
            return render_template('auth.html', password_error=True), 401

        login_user(user)
        return redirect(url_for('index'))

    return render_template('auth.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if _is_real_user_authenticated():
        if _is_json_request():
            return _json_error('already authenticated', 400)

        return redirect(url_for('index'))

    if request.method == 'POST':
        if _is_json_request():
            data = _get_request_data()

            username = (data.get('username') or '').strip()
            password = data.get('password') or ''
            email = (data.get('email') or '').strip() or None

            if not username or not password:
                return _json_error('username and password are required')

            if len(username) > 50:
                return _json_error('username too long')

            if len(password) < 6:
                return _json_error('password too short')

            existing_user = User.query.filter_by(username=username).first()

            if existing_user is not None:
                if not (
                    current_user.is_authenticated
                    and current_user.is_guest
                    and existing_user.id == current_user.id
                ):
                    return _json_error('username already exists')

            if email:
                existing_email_user = User.query.filter_by(email=email).first()

                if existing_email_user is not None:
                    if not (
                        current_user.is_authenticated
                        and current_user.is_guest
                        and existing_email_user.id == current_user.id
                    ):
                        return _json_error('email already exists')

            try:
                if current_user.is_authenticated and current_user.is_guest:
                    user = _upgrade_guest_to_real_user(
                        username=username,
                        password=password,
                        email=email
                    )
                else:
                    user = _create_real_user(
                        username=username,
                        password=password,
                        email=email
                    )
            except IntegrityError:
                db.session.rollback()
                return _json_error('username or email already exists')

            return {'status': 'ok', 'user': _user_payload(user)}, 201

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        password_repeat = request.form.get('password_repeat', '')

        if password != password_repeat:
            return render_template('auth.html', password_error=True), 400

        if not username or not password:
            return render_template('auth.html', password_error=True), 400

        existing_user = User.query.filter_by(username=username).first()

        if existing_user is not None:
            if not (
                current_user.is_authenticated
                and current_user.is_guest
                and existing_user.id == current_user.id
            ):
                return render_template('auth.html', nickname_error=True), 409

        try:
            if current_user.is_authenticated and current_user.is_guest:
                user = _upgrade_guest_to_real_user(
                    username=username,
                    password=password,
                    email=None
                )
            else:
                user = _create_real_user(
                    username=username,
                    password=password,
                    email=None
                )
        except IntegrityError:
            db.session.rollback()
            return render_template('auth.html', nickname_error=True), 409

        login_user(user)
        return redirect(url_for('auth.register_success'))

    return render_template('auth.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    if _is_real_user_authenticated():
        return _json_error('already authenticated', 400)

    data = _get_request_data()

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

    if user is None or user.is_guest or not user.password_hash:
        return _json_error('invalid credentials', 401)

    if not check_password_hash(user.password_hash, password):
        return _json_error('invalid credentials', 401)

    login_user(user)

    return {'status': 'ok', 'user': _user_payload(user)}


@auth_bp.route('/guest', methods=['POST'])
def guest_login():
    if current_user.is_authenticated:
        if current_user.is_guest:
            return {'status': 'ok', 'user': _user_payload(current_user)}

        return _json_error('already authenticated', 400)

    data = _get_request_data()

    base_username = (data.get('username') or '').strip() or 'guest'
    username = _unique_guest_username(base_username)

    user = User(
        username=username,
        is_guest=True
    )

    db.session.add(user)
    db.session.commit()
    login_user(user)

    return {'status': 'ok', 'user': _user_payload(user)}, 201


@auth_bp.route('/register/success', methods=['GET'])
def register_success():
    return render_template('register_success.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()

    if _is_json_request():
        return {'status': 'ok'}

    return redirect(url_for('index'))


@auth_bp.route('/profile', methods=['GET'])
def profile():
    if not current_user.is_authenticated:
        return _json_error('authentication required', 401)

    return {'status': 'ok', 'user': _user_payload(current_user)}