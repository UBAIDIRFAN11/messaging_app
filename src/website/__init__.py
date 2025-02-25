from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_socketio import join_room, leave_room, send, SocketIO
from flask_migrate import Migrate  # Import Flask-Migrate

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'Ubaid is really cool!'
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

    socketio = SocketIO(app)

    db.init_app(app)

    # Initialize Flask-Migrate
    migrate = Migrate(app, db)  # This binds Flask-Migrate to your app

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    from .models import User, Post, Event

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app, socketio

def create_database(app):
    # Database creation logic should now be handled by migrations
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()  # This line can be removed once you're using migrations
            print('Created Database!')