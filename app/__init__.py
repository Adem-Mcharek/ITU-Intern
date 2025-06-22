"""
Flask WebTV Processing App - Simple Configuration
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Try to load environment variables from .env file (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, skip loading .env file
    pass

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Simple configuration with optional environment variable overrides
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration
    default_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{default_db_path}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Upload folder configuration
    default_uploads_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    uploads_path = os.environ.get('UPLOAD_FOLDER', default_uploads_path)
    app.config['UPLOAD_FOLDER'] = uploads_path
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024))  # 500MB
    
    # AI Services configuration
    app.config['GEMINI_API_KEY'] = os.environ.get('GEMINI_API_KEY')
    
    # Flask debug mode
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Create directories
    os.makedirs(uploads_path, exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Import models for migrations
    from app import models
    
    return app 