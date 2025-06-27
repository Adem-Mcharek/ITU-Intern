# ITU WebTV Processing System

A comprehensive Flask web application for processing video content from UN WebTV and other platforms into searchable transcripts with AI-powered features, professional documentation generation, and enterprise-grade user management.

## 🚀 Features

### Core Processing
- 🎥 **Audio Extraction**: Download audio from UN WebTV, YouTube, Vimeo, and other video platforms
- 🤖 **AI Transcription**: Generate transcripts using OpenAI Whisper with GPU acceleration
- 👥 **Speaker Identification**: Identify speakers using Google Gemini AI
- 📁 **Multiple Formats**: Export as MP3, TXT, SRT, and speaker-labeled transcripts

### AI-Powered Analysis
- 📊 **ITU-Focused Summaries**: Generate policy-relevant internal briefs using ITU terminology
- 📝 **Professional Meeting Notes**: Create formatted Word documents following UN/ITU standards
- 🎯 **Smart Content Recognition**: Identify ICT/telecommunications content relevant to ITU mandate

### Enterprise Features
- 👤 **Three-Tier User Management**: Users, Admins, Developers with role-based access
- 🔐 **Secure Authentication**: Email-based registration with admin approval
- 📊 **Queue System**: Production-ready sequential processing for multiple users
- 📱 **Responsive Interface**: Clean Bootstrap 5 interface with role-based navigation

### Advanced Capabilities
- 🔗 **Custom Domain Support**: Access via ITUIntern.int with local network setup
- ⚡ **GPU Acceleration**: CUDA support for faster transcription
- 🛡️ **Robust Error Handling**: Comprehensive retry logic and graceful degradation
- 📈 **Real-time Status**: Live processing updates and queue monitoring

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Advanced Setup](#advanced-setup)
- [User Management](#user-management)
- [AI Features](#ai-features)
- [Queue System](#queue-system)
- [Network Access](#network-access)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

### 1. Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd ITU-T

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup
```bash
# Initialize the database
python init_db.py

# Create first admin user
python create_admin.py admin@example.com
```

### 3. Optional: Configure AI Features
```bash
# Copy configuration template
cp env.example .env

# Edit .env with your API keys
GEMINI_API_KEY=your-gemini-api-key-here
```

### 4. Run the Application
```bash
# Start the Flask app
python run.py

# Access at http://localhost:8000 or http://ITUIntern.int:8000
```

## 🔧 Advanced Setup

### AI-Powered Features Configuration
For full AI capabilities, configure these environment variables:

```bash
# Required for ITU summaries and meeting notes
GEMINI_API_KEY=your-gemini-api-key-here

# Optional Flask settings
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=False
DATABASE_URL=sqlite:///app.db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=1073741824  # 1GB
```

### Dependencies for Full Features
```bash
# Core dependencies (required)
pip install Flask SQLAlchemy yt-dlp openai-whisper

# AI features (optional but recommended)
pip install google-generativeai python-docx

# GPU acceleration (optional)
pip install torch>=2.0.0
```

## 👥 User Management

### Role Hierarchy
1. **Developer** (Highest Privilege)
   - Full system access and user privilege management
   - Can create/delete admin and developer users
   - Access to advanced developer dashboard
   - All admin capabilities

2. **Admin** (Medium Privilege)
   - Can manage allowed user emails
   - Can activate/deactivate users
   - Can toggle basic admin status
   - Access to admin dashboard

3. **User** (Basic Privilege)
   - Can process meetings and view content
   - Basic application access only

### Creating Users
```bash
# Create developer user (highest privileges)
python create_developer.py developer@example.com

# Create admin user  
python create_admin.py admin@example.com

# Regular users register via web interface with admin approval
```

### Access Control Matrix
| Feature | User | Admin | Developer |
|---------|------|-------|-----------|
| Process Meetings | ✅ | ✅ | ✅ |
| View All Meetings | ✅ | ✅ | ✅ |
| Admin Dashboard | ❌ | ✅ | ✅ |
| Manage Users | ❌ | ✅ (Basic) | ✅ (Full) |
| Create Admins | ❌ | ❌ | ✅ |
| System Statistics | ❌ | ❌ | ✅ |

## 🤖 AI Features

### ITU-Focused Summaries
Automatically generates concise internal briefs focusing on:
- Digital connectivity & infrastructure
- ICT standardization (ITU-T)
- Digital transformation (ITU-D)
- Artificial intelligence governance
- Cybersecurity frameworks
- Emerging technologies (5G/6G, IoT)
- Digital inclusion initiatives
- Emergency telecommunications
- Sustainable development
- Regulatory frameworks

**Output Format:**
```
**Key ITU-Relevant Points:**
• [Most important point for ITU work]
• [Second priority point with sector relevance]

**Potential ITU Actions/Opportunities:**
• [What ITU could/should do based on this meeting]
```

### Professional Meeting Notes
Creates formatted Word documents (.docx) with:

**Document Structure:**
1. **Meeting Overview** - Purpose, participants, themes
2. **Key Discussions** - Main topics with speaker attribution
3. **Positions & Recommendations** - Member state positions
4. **Decisions & Action Items** - Specific decisions and next steps
5. **Technical Matters** - Standards, implementation (if applicable)
6. **Capacity Building** - Training, assistance (if discussed)

**Professional Features:**
- ITU header and branding
- Diplomatic language throughout
- Speaker identification highlighting
- Action item emphasis
- Professional margins and spacing

## ⚡ Queue System

### Production-Ready Processing
For multiple users, the system includes a queue-based processor:

**Benefits:**
- Sequential processing (one meeting at a time)
- Queue position tracking with estimated wait times
- Real-time status updates via JavaScript
- Admin monitoring with queue health statistics
- Graceful handling of high traffic

**User Experience:**
```
Meeting #1: "Processing..." (currently running)
Meeting #2: "Queued (#1) - Starting soon"
Meeting #3: "Queued (#2) - ~10 minutes"
```

**Monitoring:**
- Admin dashboard shows queue length and current processing
- API endpoint: `/api/queue/status` for queue monitoring
- Real-time updates every 5 seconds

## 🌐 Network Access

### Custom Domain Setup (ITUIntern.int)
Access your application via custom domain on local network:

**Option 1: Use Setup Script (Recommended)**
```bash
# Run as Administrator
.\setup_custom_domain.ps1
```

**Option 2: Manual Setup**
1. Open Command Prompt as Administrator
2. Edit hosts file: `notepad C:\Windows\System32\drivers\etc\hosts`
3. Add line: `127.0.0.1    ITUIntern.int`
4. Save and access via: `http://ITUIntern.int:8000`

## 🏗️ Architecture

### Processing Pipeline (9 Steps)
1. **URL Analysis**: Intelligent detection of video platform with specialized UN WebTV handling
2. **Audio Download**: Platform-optimized extraction with English prioritization for WebTV
3. **GPU Transcription**: Hardware-accelerated Whisper processing
4. **Speaker Separation**: Chunked Gemini processing with fallbacks
5. **File Generation**: Complete set of output formats
6. **Database Storage**: Meeting and segment information
7. **Quality Validation**: Error checking and status updates
8. **ITU Summary Generation**: Policy-focused internal briefs
9. **Meeting Notes Creation**: Professional Word documents

### File Structure
```
ITU-T/
├── app/
│   ├── __init__.py              # Flask app setup with queue worker
│   ├── models.py                # Database models with user roles
│   ├── routes.py                # Web routes with role-based access
│   ├── forms.py                 # Web forms with validation
│   ├── queue_manager.py         # Production queue system
│   ├── pipeline.py              # Enhanced AI processing pipeline
│   ├── meeting_summarizer.py    # ITU-focused summary generator
│   ├── meeting_notes_generator.py # Professional notes generator
│   ├── templates/               # HTML templates with role-based UI
│   └── static/                  # CSS/JS with live status updates
├── migrations/                  # Database migrations
├── run.py                       # Application entry point
├── init_db.py                  # Database setup script
├── create_admin.py             # Admin user creation
├── create_developer.py         # Developer user creation
├── requirements.txt            # Python dependencies
└── uploads/                    # Generated files (auto-created)
```

### Database Schema
**Core Tables:**
- `meeting` - Meeting information with AI-generated content
- `segment` - Transcript segments with timing
- `user` - User accounts with role management
- `allowed_user` - Email whitelist for registration
- `processing_queue` - Sequential processing queue

**Key Fields:**
```sql
-- Meeting table enhancements
itu_summary TEXT              -- ITU-focused policy brief
notes_path VARCHAR(512)       -- Path to .docx meeting notes

-- User table with roles
is_admin BOOLEAN DEFAULT FALSE
is_developer BOOLEAN DEFAULT FALSE
is_active BOOLEAN DEFAULT TRUE
```

## ⚙️ Configuration

### Environment Variables
```bash
# AI Services (optional but recommended)
GEMINI_API_KEY=your-gemini-api-key-here

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=False

# Database
DATABASE_URL=sqlite:///app.db

# File Storage
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=1073741824

# Admin Configuration
ADMIN_EMAIL=admin@example.com
```

### Optional Dependencies Handling
The application gracefully handles missing dependencies:
- Works without AI features if `google-generativeai` unavailable
- Falls back to CPU if CUDA/GPU support missing
- Continues processing if document generation fails

## 🔍 Troubleshooting

### Common Issues

#### Authentication Issues
```bash
# Reset admin user
python create_admin.py existing@admin.com

# Check user roles
python -c "from app import *; app = create_app(); app.app_context().push(); from app.models import User; print([(u.email, u.role) for u in User.query.all()])"
```

#### Processing Issues
```bash
# Check dependencies
python -c "import torch, openai, google.generativeai; print('All AI deps available')"

# Reset database
rm instance/app.db
python init_db.py
```

#### Queue Issues
```bash
# Check queue status
python -c "from app import *; app = create_app(); app.app_context().push(); from app.models import ProcessingQueue; print(f'Queue length: {ProcessingQueue.query.count()}')"

# Clear stuck queue items
python -c "from app import *; app = create_app(); app.app_context().push(); from app.models import ProcessingQueue, db; ProcessingQueue.query.delete(); db.session.commit(); print('Queue cleared')"
```

#### Network Access Issues
```bash
# Verify hosts file entry
findstr "ITUIntern.int" C:\Windows\System32\drivers\etc\hosts

# Test domain resolution
nslookup ITUIntern.int
```

### System Requirements
- **Python**: 3.8+ (tested with 3.9-3.11)
- **Memory**: 4GB RAM minimum, 8GB recommended for GPU acceleration
- **Storage**: 1GB+ free space for processed files
- **Network**: Internet access for AI services and WebTV downloads
- **Optional**: NVIDIA GPU with CUDA for faster transcription

### Performance Optimization
- **GPU Acceleration**: Install CUDA and PyTorch for 3-5x faster transcription
- **SSD Storage**: Use SSD for faster file I/O during processing
- **Memory**: More RAM allows processing longer meetings without issues
- **Database**: Use PostgreSQL instead of SQLite for high-traffic production

## 📊 Production Deployment

### Scaling Recommendations
- **Light Usage** (<50 meetings/day): Current SQLite + queue system
- **Medium Usage** (50-200 meetings/day): PostgreSQL + queue system
- **High Usage** (200+ meetings/day): Redis + Celery + PostgreSQL
- **Enterprise**: Load balancer + multiple app instances + shared storage

### Monitoring
- Queue length and processing times
- AI service availability and response times
- Storage usage and file cleanup
- User activity and error rates

---

## 🎯 Key Benefits

1. **Comprehensive Processing**: Complete WebTV-to-documentation pipeline
2. **Enterprise-Grade**: Role-based access, queue system, professional output
3. **AI-Enhanced**: Intelligent summaries and professional document generation
4. **Production-Ready**: Robust error handling, monitoring, and scalability
5. **ITU-Focused**: Specialized for telecommunications and ICT content
6. **User-Friendly**: Clean interface with real-time status updates

**The ITU WebTV Processing System transforms raw video content into professional documentation while providing enterprise-grade user management and processing capabilities.**

## 🚀 Deployment

For detailed deployment instructions on a new system, see [DEPLOY.md](DEPLOY.md).

**Quick Setup:**
```bash
# Windows
setup.bat

# Linux/macOS  
./setup.sh
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Copyright (c) 2025 Adem Mcharek**

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files, to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, subject to the conditions in the MIT License.