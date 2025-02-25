from website import create_app

app, socketio = create_app()

from website.views import init_socketio
init_socketio(socketio)

if __name__ == '__main__':
    socketio.run(app, debug=True)
