# Flask WebTV Processing App

A simple Flask web application for processing UN WebTV content into searchable transcripts with AI-powered speaker identification.

## Features

- 🎥 **Audio Extraction**: Download audio from UN WebTV streams using yt-dlp
- 🤖 **AI Transcription**: Generate transcripts using OpenAI Whisper
- 👥 **Speaker Identification**: Identify speakers using Google Gemini
- 📁 **Multiple Formats**: Export as MP3, TXT, SRT, and speaker-labeled transcripts
- 🔍 **Search & Browse**: Find meetings by title and content
- 📱 **Simple Interface**: Clean Bootstrap 5 interface

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd webty-processor

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Database

```bash
# Initialize the database
python init_db.py
```

### 3. Run the Application

```bash
# Start the Flask app
python run.py

# The app will be available at http://localhost:5000
```

## Configuration

The app uses simple defaults that work out of the box:

- **Database**: SQLite file in the project directory (`app.db`)
- **Uploads**: Files stored in `uploads/` directory
- **Processing**: Background threading (no Redis/Celery needed)

### Optional Configuration

For advanced users, you can customize settings using environment variables:

```bash
# Copy the example file
cp env.example .env

# Edit .env with your preferences
# All settings are optional!
```

Key optional settings:
- `GEMINI_API_KEY`: For AI speaker identification
- `DATABASE_URL`: Custom database location
- `UPLOAD_FOLDER`: Custom uploads directory
- `SECRET_KEY`: Custom Flask secret key

The app works perfectly without any configuration!

## Usage

1. **Submit URL**: Go to the home page and paste a UN WebTV URL
2. **Add Title**: Provide a descriptive meeting title
3. **Wait for Processing**: The app will process in the background
4. **Download Results**: Access all generated files from the meeting page

## File Structure

```
├── app/
│   ├── __init__.py          # Flask app setup
│   ├── models.py            # Database models
│   ├── routes.py            # Web routes
│   ├── forms.py             # Web forms
│   ├── tasks.py             # Background processing
│   ├── pipeline.py          # AI processing pipeline
│   ├── templates/           # HTML templates
│   └── static/              # CSS/JS files
├── run.py                   # Application entry point
├── init_db.py              # Database setup script
├── requirements.txt         # Python dependencies
└── uploads/                 # Generated files (created automatically)
```

## Dependencies

- **Flask**: Web framework
- **SQLAlchemy**: Database ORM
- **yt-dlp**: Video/audio downloading
- **OpenAI Whisper**: Speech transcription
- **Google Gemini**: Speaker identification (optional)

## Troubleshooting

**Database Issues**:
```bash
# Reset the database
rm app.db
python init_db.py
```

**Missing Dependencies**:
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

**Permission Errors**:
```bash
# Ensure upload directory is writable
mkdir uploads
```

## Notes

- The app works without AI dependencies (limited functionality)
- Processing happens in background threads
- All files are stored locally in the `uploads/` directory
- SQLite database is used for simplicity
- No complex deployment setup required

---

**Simple. Local. No Docker required.** 