# 🚀 Quick Deployment Reference

## Essential Files for Deployment

When transferring to a new laptop, ensure you have these files:

### Core Application Files
```
app/                    # Main application directory
├── __init__.py        # Flask app factory
├── routes.py          # Web routes
├── models.py          # Database models
├── pipeline.py        # Processing pipeline
├── forms.py           # Web forms
├── queue_manager.py   # Queue system
├── static/            # CSS, JS, images
└── templates/         # HTML templates

migrations/            # Database migration files
run.py                # Application entry point
requirements.txt      # Python dependencies
config.py            # App configuration
```

### Setup & Deployment Files
```
DEPLOY.md            # Full deployment guide
env.example          # Environment template
init_db.py          # Database initialization
create_admin.py     # Admin user creation
create_developer.py # Developer user creation
setup.bat           # Windows setup script
setup.sh            # Linux/macOS setup script
start.bat           # Windows start script
start.sh            # Linux/macOS start script
```

### Documentation
```
README.md           # Main documentation
LICENSE             # MIT License
```

## Quick Setup Commands

### Windows
```cmd
setup.bat
start.bat
```

### Linux/macOS
```bash
chmod +x setup.sh start.sh
./setup.sh
./start.sh
```

## What NOT to Copy

These files/folders are created automatically:
- `venv/` - Virtual environment (recreated)
- `*.db` - Database files (recreated)
- `uploads/` - Upload directory (recreated)
- `logs/` - Log files (recreated)
- `__pycache__/` - Python cache (recreated)
- `.env` - Created from env.example

## Minimum Deployment Steps

1. Copy project files to new laptop
2. Install Python 3.8+
3. Run setup script: `setup.bat` or `./setup.sh`
4. Start application: `start.bat` or `./start.sh`
5. Open browser: `http://localhost:8000`

**That's it! The system is ready to use.** 🎉 