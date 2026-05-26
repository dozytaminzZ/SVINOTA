from flask import Blueprint, redirect, render_template, request, url_for

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return {'status': 'login not implemented'}

    return render_template('auth.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return redirect(url_for('auth.register_success'))

    return render_template('auth.html')


@auth_bp.route('/register/success', methods=['GET'])
def register_success():
    return render_template('register_success.html')
