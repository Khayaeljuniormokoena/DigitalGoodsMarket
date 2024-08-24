from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    # Configuration for uploading profile pictures
    app.config['UPLOAD_FOLDER'] = 'static/profile_pics/'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    # Register blueprints after initializing extensions
    from app import routes
    app.register_blueprint(routes.bp)

    return app