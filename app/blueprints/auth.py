from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()

        if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
            return render_template('auth.html', password_error=True), 401

        login_user(user)
        return redirect(url_for('index'))

    return render_template('auth.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        password_repeat = request.form.get('password_repeat', '')

        if password != password_repeat:
            return render_template('auth.html', password_error=True), 400

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
        )

        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return render_template('auth.html', nickname_error=True), 409

        login_user(user)
        return redirect(url_for('auth.register_success'))

    return render_template('auth.html')


@auth_bp.route('/register/success', methods=['GET'])
def register_success():
    return render_template('register_success.html')


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
