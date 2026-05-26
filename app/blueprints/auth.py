from flask import Blueprint, render_template, request

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return {'status': 'login not implemented'}

    return render_template('auth.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return {'status': 'register not implemented'}

    return render_template('auth.html')
