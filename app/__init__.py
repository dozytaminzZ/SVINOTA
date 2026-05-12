from flask import Flask
from config.settings import Config
from app.extensions import db, migrate, socketio

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    # Импорт моделей (чтобы Alembic их увидел)
    from app import models

    # Регистрация blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.lobby import lobby_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(lobby_bp, url_prefix='/lobby')

    @app.route('/health')
    def health_check():
        return {'status': 'ok'}

    return app
