import uuid

from flask import Flask, render_template, request
from flask_login import login_required

from app.extensions import db, login_manager, migrate, socketio
from config.settings import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.index'
    login_manager.login_message = None
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    from app import models

    @login_manager.user_loader
    def load_user(user_id):
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None

        return db.session.get(models.User, user_uuid)

    from app.blueprints.auth import auth_bp
    from app.blueprints.lobby import lobby_bp
    from app.blueprints.game import game_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(lobby_bp, url_prefix='/lobby')
    app.register_blueprint(game_bp, url_prefix='/game')

    from app.sockets.game import register_game_socket_handlers
    register_game_socket_handlers(socketio)

    @app.route('/health')
    def health_check():
        return {'status': 'ok'}

    @app.route('/')
    def index():
        if app.config.get('TESTING') or request.headers.get('Accept') == 'application/json':
            return {
                'status': 'ok',
                'modules': {
                    'auth': '/auth/',
                    'lobby': '/lobby/',
                    'game': '/game/',
                    'health': '/health'
                }
            }

        return render_template('index.html')

    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html')

    return app