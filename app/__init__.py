"""
Flask WebTV Processing App - Simple Configuration
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

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
login = LoginManager()

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Simple configuration with optional environment variable overrides
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Disable CSRF for testing (only in development)
    app.config['WTF_CSRF_ENABLED'] = os.environ.get('WTF_CSRF_ENABLED', 'False').lower() == 'true'
    
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
    
    # Azure OpenAI configuration for enhanced speaker identification (GPT-4)
    app.config['AZURE_OPENAI_API_KEY'] = os.environ.get('AZURE_OPENAI_API_KEY')
    app.config['AZURE_OPENAI_ENDPOINT'] = os.environ.get('AZURE_OPENAI_ENDPOINT', 'https://z-openai-openai4tsb-dev-chn.openai.azure.com/')
    app.config['AZURE_OPENAI_API_VERSION'] = os.environ.get('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
    app.config['AZURE_OPENAI_DEPLOYMENT_NAME'] = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'GPT-4')
    
    # GPU configuration for Whisper transcription
    app.config['USE_GPU'] = os.environ.get('USE_GPU', 'true')
    
    # Flask debug mode
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Create directories
    os.makedirs(uploads_path, exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize Flask-Login
    login.init_app(app)
    login.login_view = 'main.login'
    login.login_message = 'Please log in to access this page.'
    login.login_message_category = 'info'
    
    @login.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Start queue worker (unless explicitly skipped during migration)
    if not os.environ.get('SKIP_QUEUE_WORKER'):
        from app.queue_manager import queue_manager
        queue_manager.start_worker(app)
    else:
        print("Skipping queue worker startup (migration mode)")
    
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Set up logging
        file_handler = RotatingFileHandler('logs/itu_intern.log', 
                                         maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('ITU Intern startup')
    
    return app 