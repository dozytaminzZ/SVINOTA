from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == '__main__':
    # Используем socketio.run вместо стандартного app.run для поддержки WebSockets
    socketio.run(app, debug=True, port=5000)
