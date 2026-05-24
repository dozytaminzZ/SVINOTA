import uuid
from flask import Flask, render_template
from config.settings import Config
from app.extensions import db, migrate, socketio, login_manager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")
    login_manager.init_app(app)

    # Импорт моделей (чтобы Alembic их увидел)
    from app import models
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, TypeError, AttributeError):
            return None
        return db.session.get(User, user_uuid)

    # Регистрация blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.lobby import lobby_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(lobby_bp, url_prefix='/lobby')

    @app.route('/')
    def index():
        return {
            'status': 'ok',
            'modules': {
                'auth': '/auth/',
                'lobby': '/lobby/',
                'docs': '/docs',
                'openapi': '/openapi.yaml',
                'health': '/health'
            }
        }

    @app.route('/docs')
    def docs():
        return render_template('docs.html')

    @app.route('/openapi.yaml')
    def openapi_spec():
        return app.send_static_file('openapi.yaml')

    @app.route('/health')
    def health_check():
        return {'status': 'ok'}

    return app
