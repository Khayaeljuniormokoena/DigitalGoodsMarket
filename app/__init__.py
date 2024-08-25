from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'

# Function to check if the uploaded file is allowed
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'epub', 'zip', 'mp3', 'wav', 'jpg', 'jpeg', 'png', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Configuration for uploading profile pictures
    app.config['UPLOAD_FOLDER'] = 'static/profile_pics/'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    # Register blueprints after initializing extensions
    from app import routes
    app.register_blueprint(routes.bp)

    return app