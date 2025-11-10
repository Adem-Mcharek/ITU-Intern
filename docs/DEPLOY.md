# 🚀 ITU WebTV Processing System - Deployment Guide

This guide walks you through setting up the ITU WebTV Processing System on a new laptop from scratch.

## 📋 Prerequisites Checklist

### System Requirements
- **Operating System**: Windows 10/11 (tested), macOS, or Linux
- **Python**: 3.8 or higher (3.9-3.11 recommended)
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 2GB+ free space
- **Internet**: Required for downloads and AI services

### Optional (for better performance)
- **GPU**: NVIDIA GPU with CUDA support for faster transcription
- **FFmpeg**: For audio format conversion (auto-downloaded by yt-dlp)

## 🛠️ Step-by-Step Deployment

### Step 1: Install Python
1. **Download Python** from [python.org](https://www.python.org/downloads/)
2. **Install** with these options:
   - ✅ Add Python to PATH
   - ✅ Install pip
   - ✅ Install for all users (recommended)
3. **Verify installation**:
   ```bash
   python --version
   pip --version
   ```

### Step 2: Get the Project Code
Choose one of these methods:

#### Option A: Git Clone (Recommended)
```bash
git clone <your-repository-url>
cd ITU-T
```

#### Option B: Download ZIP
1. Download the project ZIP file
2. Extract to your desired location
3. Open terminal/command prompt in the project folder

### Step 3: Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 4: Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# This will install:
# - Flask and web framework components
# - AI processing libraries (Whisper, Gemini)
# - Audio/video processing tools (yt-dlp)
# - Document generation (python-docx)
```

**Note**: The installation may take 5-15 minutes depending on your internet speed.

### Step 5: Configure Environment (Optional)
```bash
# Copy environment template
cp env.example .env

# Edit the .env file with your preferred settings
notepad .env    # Windows
nano .env       # Linux/macOS
```

**Recommended .env configuration**:
```env
# Required for full AI features
GEMINI_API_KEY=your-gemini-api-key-here

# Security (change this!)
SECRET_KEY=your-unique-secret-key-here

# Performance
FLASK_DEBUG=False
```

### Step 6: Initialize Database
```bash
# Create database tables
python init_db.py
```

### Step 7: Create Admin User
```bash
# Create your admin account
python create_admin.py

# Follow the prompts to enter:
# - Your email address
# - Your password
```

### Step 8: Test the Installation
```bash
# Start the application
python run.py
```

You should see:
```
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8000
 * Running on http://[your-ip]:8000
```

### Step 9: Access the Application
1. Open your web browser
2. Go to: `http://localhost:8000`
3. Log in with your admin credentials
4. Upload a test audio file or video URL

## 🔧 Configuration Options

### AI Services Setup

#### Google Gemini API (Recommended)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API key
3. Add to `.env` file:
   ```env
   GEMINI_API_KEY=your-api-key-here
   ```

### Performance Optimization

#### GPU Acceleration (Optional)
For faster transcription on NVIDIA GPUs:
```bash
# Install CUDA version of PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Memory Settings
For large files, increase memory limits in `.env`:
```env
MAX_CONTENT_LENGTH=2147483648  # 2GB
```

## 🌐 Network Access Setup

### Local Network Access
To access from other devices on your network:

1. Find your IP address:
   ```bash
   # Windows
   ipconfig | findstr IPv4
   
   # macOS/Linux
   ifconfig | grep inet
   ```

2. Access from other devices: `http://[your-ip]:8000`

### Custom Domain (Optional)
For easier access, set up a custom domain:

1. **Edit hosts file as Administrator**:
   ```bash
   # Windows
   notepad C:\Windows\System32\drivers\etc\hosts
   
   # macOS/Linux
   sudo nano /etc/hosts
   ```

2. **Add line**:
   ```
   127.0.0.1    ITUIntern.int
   ```

3. **Access via**: `http://ITUIntern.int:8000`

## 🏭 Production Deployment

### Security Hardening
```env
# .env for production
SECRET_KEY=your-very-secure-secret-key-change-this
FLASK_DEBUG=False
WTF_CSRF_ENABLED=True
```

### Process Management
For production, use a process manager:

#### Option A: Windows Service
```bash
# Install pywin32
pip install pywin32

# Use Windows Task Scheduler or NSSM
```

#### Option B: Linux systemd
```bash
# Create systemd service file
sudo nano /etc/systemd/system/itu-webtv.service
```

### Database Upgrade (Production)
For high traffic, consider PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@localhost/ituwebtv
```

## 🔍 Troubleshooting

### Common Issues

#### "Python not found"
- Reinstall Python with "Add to PATH" option
- Restart terminal/command prompt

#### "No module named 'app'"
- Ensure you're in the project directory
- Activate virtual environment: `venv\Scripts\activate`

#### "Database error"
- Run: `python init_db.py`
- Check file permissions in project directory

#### "CUDA not available"
- GPU acceleration is optional
- CPU processing will work fine, just slower

#### "Permission denied" on uploads
- Check uploads directory permissions
- Ensure sufficient disk space

### Memory Issues
For large files:
```bash
# Increase virtual memory
# Windows: System Properties > Advanced > Performance > Settings > Advanced > Virtual Memory
```

### Port Already in Use
Change the port in `run.py`:
```python
app.run(host='0.0.0.0', port=8001, debug=debug, use_reloader=False)
```

## 📊 Performance Monitoring

### Check System Status
```bash
# View logs
tail -f logs/itu_intern.log

# Check database size
ls -lh *.db

# Monitor uploads folder
du -sh uploads/
```

### Health Check
Visit: `http://localhost:8000/api/health`

## 🔄 Updates and Maintenance

### Update Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Database Migrations
```bash
# If database schema changes
python -c "from app import db; db.create_all()"
```

### Cleanup Old Files
```bash
# Clear old uploads (optional)
# Be careful - this deletes processed files!
rm -rf uploads/meeting_*
```

## 🆘 Getting Help

### Log Files
Check these for error details:
- `logs/itu_intern.log` - Application logs
- Terminal output - Real-time errors

### System Information
```bash
# Python version
python --version

# Installed packages
pip list

# System info
python -c "import platform; print(platform.platform())"
```

### Quick Fix Commands
```bash
# Reset database
rm app.db instance/app.db
python init_db.py

# Clear Python cache
find . -name "__pycache__" -type d -delete

# Restart with clean environment
deactivate
venv\Scripts\activate
python run.py
```

## ✅ Deployment Checklist

- [ ] Python 3.8+ installed
- [ ] Project code downloaded/cloned
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database initialized (`python init_db.py`)
- [ ] Admin user created (`python create_admin.py`)
- [ ] Environment configured (`.env` file)
- [ ] Application starts successfully (`python run.py`)
- [ ] Can access web interface at `http://localhost:8000`
- [ ] Can log in with admin credentials
- [ ] Test file upload or URL processing works

## 🎯 Quick Start Summary

For experienced users, the minimal setup:
```bash
# 1. Clone and enter directory
git clone <repo-url> && cd ITU-T

# 2. Set up environment
python -m venv venv && venv\Scripts\activate

# 3. Install and initialize
pip install -r requirements.txt && python init_db.py

# 4. Create admin and start
python create_admin.py && python run.py
```

**Your ITU WebTV Processing System is now ready for deployment! 🚀**

---

*For additional support or advanced configuration, refer to the main [README.md](README.md) file.* 