# ITU WebTV Processing System - Technical Documentation

## System Overview

A Flask-based web application that processes video content into searchable transcripts using AI/ML models. The system handles audio extraction, transcription, speaker diarization, and generates professional documentation.

---

## Architecture

### Technology Stack

**Backend Framework**
- Flask 3.0.0 (Python web framework)
- SQLAlchemy 3.1.1 (ORM for database operations)
- Flask-Migrate 4.0.5 (database migrations)
- Flask-Login 0.6.3 (user authentication)

**AI/ML Models**
- OpenAI Whisper (speech-to-text transcription)
- Google Gemini 2.5 Flash Lite (speaker diarization)
- Azure OpenAI GPT-4 (enhanced speaker identification)
- Ollama (optional local LLM inference)

**Media Processing**
- yt-dlp (audio extraction from video platforms)
- PyTorch 2.0+ (GPU acceleration for Whisper)
- FFmpeg (audio format conversion)

**Frontend**
- Bootstrap 5 (responsive UI framework)
- JavaScript (real-time status updates)
- Jinja2 templates (server-side rendering)

---

## Processing Pipeline

### Stage 1: URL Analysis
**Function**: `analyze_url()`

Intelligent detection of video platform and metadata extraction:
- UN WebTV: Direct API access with partner_id authentication
- YouTube: yt-dlp metadata extraction
- Vimeo, Dailymotion: Platform-specific handlers
- Generic: Fallback to yt-dlp for unknown platforms

**UN WebTV Special Handling**:
```python
partner_id = "2503451"  # ITU partner ID for UN WebTV
api_url = f"https://media.un.org/api/v2/assets/{asset_id}"
# Prioritizes English audio streams
```

### Stage 2: Audio Download
**Function**: `download_audio()`

Platform-optimized audio extraction:
- **UN WebTV**: Direct M3U8 playlist download, prioritizes English
- **Other Platforms**: yt-dlp with format selection
- Output: MP3 format for compatibility
- Location: `uploads/meeting_{id}/audio.mp3`

**yt-dlp Configuration**:
```python
ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': output_path,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}
```

### Stage 3: AI Transcription
**Function**: `transcribe_audio()`

OpenAI Whisper model implementation:
- Model: `large-v2` or `large-v3` (highest accuracy)
- Device: CUDA GPU if available, else CPU
- Output: SRT format with timestamps
- Language: Auto-detect or force English

**GPU Acceleration**:
```python
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("large-v2", device=device)
# ~3-5x faster on NVIDIA GPUs
```

**Timestamp Format**:
```
1
00:00:00,000 --> 00:00:05,120
Welcome to this session on digital transformation.

2
00:00:05,120 --> 00:00:10,340
My name is John Smith from the United States.
```

### Stage 4: Speaker Separation
**Function**: `separate_speakers_with_gemini()`

Multi-stage AI-powered speaker identification:

**Phase 1: Context Extraction (Gemini)**
- Analyzes full transcript for speaker introductions
- Extracts names, titles, organizations, countries
- Creates speaker database for reference

**Phase 2: Segment Assignment (Gemini)**
- Processes transcript in batches (~100 segments)
- Assigns speakers to individual segments
- Identifies speaker changes and affiliations

**Phase 3: Enhancement (Azure GPT-4 - Optional)**
- Further refines speaker identification
- Better context understanding across meeting
- Handles ambiguous speaker references

**Phase 4: Consolidation**
- Merges consecutive segments from same speaker
- Standardizes speaker names across transcript
- Validates country/organization assignments

**Batch Processing**:
```python
MAX_TOKENS_PER_BATCH = 10000
ESTIMATED_TOKENS_PER_SEGMENT = 100
MAX_SEGMENTS_PER_BATCH = 100

# Process in chunks to avoid API limits
for batch in segment_batches:
    response = gemini_model.generate_content(batch)
    # Extract and assign speakers
```

### Stage 5: File Generation
**Function**: `generate_output_files()`

Multiple format outputs:
- `transcript.txt`: Plain text transcript
- `transcript.srt`: Subtitles with timestamps
- `transcript.json`: Structured data with speakers
- `transcript_speakers.txt`: Speaker-labeled format

**Speaker-Labeled Format**:
```
[00:00:05 - 00:00:45] John Smith (United States)
Thank you for joining us today. We are here to discuss...

[00:00:45 - 00:01:30] Maria Garcia (Spain)
I appreciate the opportunity to share our perspective...
```

### Stage 6: Database Storage
**Function**: Database models in `app/models.py`

**Meeting Table**:
```python
Meeting {
    id: Integer (primary key)
    title: String(256)
    source_url: String(512)
    status: String(32)  # queued|processing|completed|error
    created_by_user_id: Integer (foreign key)
    audio_path: String(512)
    transcript_path: String(512)
    srt_path: String(512)
    speakers_path: String(512)
    notes_path: String(512)
    itu_summary: Text
    segments: Relationship to Segment model
}
```

**Segment Table**:
```python
Segment {
    id: Integer (primary key)
    meeting_id: Integer (foreign key)
    speaker: String(128)
    representing: String(256)  # Country/Organization
    content: Text
    start_time: Float (seconds)
    end_time: Float (seconds)
}
```

### Stage 7: Quality Validation
**Function**: Error handling and status updates

Validates:
- Audio file integrity and format
- Transcript completeness
- Speaker identification success rate
- File generation success

Updates meeting status:
- `queued`: Waiting in processing queue
- `processing`: Active processing
- `completed`: Successfully finished
- `error`: Failed with error message stored

### Stage 8: ITU Summary Generation
**Function**: `generate_itu_summary()` in `meeting_summarizer.py`

Gemini-powered policy-relevant summary:
- Identifies ICT/telecommunications content
- Extracts key points relevant to ITU mandate
- Highlights potential ITU actions/opportunities
- Focuses on digital infrastructure, standards, development

**ITU-Specific Topics**:
- Digital connectivity & broadband
- ICT standardization (ITU-T)
- Digital transformation (ITU-D)
- AI governance and regulation
- Cybersecurity frameworks
- 5G/6G, IoT, emerging tech
- Digital inclusion initiatives
- Emergency telecommunications

**Output Format**:
```
**Key ITU-Relevant Points:**
• [Priority point with specific relevance]
• [Second point with sector attribution]

**Potential ITU Actions/Opportunities:**
• [Actionable recommendation for ITU work]
```

### Stage 9: Meeting Notes Generation
**Function**: `generate_meeting_notes()` in `meeting_notes_generator.py`

Professional Word document (.docx) generation:

**Document Structure**:
1. **Header**: ITU branding and meeting title
2. **Meeting Overview**: Date, platform, key themes
3. **Key Discussions**: Main topics with speaker attribution
4. **Positions & Recommendations**: Member state positions
5. **Decisions & Action Items**: Concrete outcomes
6. **Technical Matters**: Standards, implementation details
7. **Capacity Building**: Training and assistance discussed

**Formatting**:
- Professional fonts (Calibri 11pt)
- UN/ITU diplomatic language
- Speaker names highlighted in bold
- Action items in distinct formatting
- Proper margins and spacing

---

## Queue System

### Architecture
**File**: `app/queue_manager.py`

Sequential processing system for multi-user environment:

**ProcessingQueue Model**:
```python
ProcessingQueue {
    id: Integer
    meeting_id: Integer (foreign key)
    priority: Integer (higher = earlier)
    queued_at: DateTime
    started_at: DateTime
    completed_at: DateTime
    status: String  # queued|processing|completed|failed
}
```

**Queue Worker**:
- Background thread processes one meeting at a time
- Polls queue every 5 seconds
- Updates status in real-time
- Handles failures gracefully

**User Experience**:
```python
position = queue_entry.position_in_queue
estimated_wait = (position - 1) * 10  # minutes
# Displays: "Queued (#2) - ~10 minutes"
```

---

## User Management

### Authentication System
**File**: `app/models.py`, `app/routes.py`

**User Model**:
```python
User {
    id: Integer
    email: String(120) [unique, indexed]
    password_hash: String(255)
    is_admin: Boolean (default: False)
    is_developer: Boolean (default: False)
    is_active: Boolean (default: True)
    created_at: DateTime
    last_login: DateTime
}
```

**Role Hierarchy**:
1. **Developer** (`is_developer=True`): Full system access
2. **Admin** (`is_admin=True`): User management, monitoring
3. **User** (default): Basic access to process meetings

**Access Control**:
```python
@login_required
def protected_route():
    if not current_user.has_admin_access:
        abort(403)  # Forbidden
```

**AllowedUser Model**:
- Email whitelist for registration
- Admin-managed approval workflow
- Tracks registration status

---

## API Configuration

### Priority System for AI Services

**1. Azure OpenAI (Primary)**
```python
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://z-openai-openai4tsb-dev-chn.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=GPT-4
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

**2. Google Gemini (Speaker Diarization)**
```python
GEMINI_API_KEY=your-key
MODEL_NAME=gemini-2.5-flash-lite-preview-06-17
```

**3. OpenAI API (Fallback)**
```python
OPENAI_API_KEY=your-key
OPENAI_MODEL_NAME=gpt-4-turbo
```

**4. Ollama (Local Option)**
```python
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=gemma2:latest
```

### Retry Logic
All AI API calls include exponential backoff:
```python
MAX_RETRIES = 3
BASE_DELAY = 1  # seconds
MAX_DELAY = 60  # seconds

for attempt in range(MAX_RETRIES):
    try:
        response = api_call()
        break
    except RateLimitError:
        delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
        time.sleep(delay + random.uniform(0, 1))
```

---

## Database Design

### Schema Overview

**Core Tables**:
- `user`: Authentication and authorization
- `allowed_user`: Registration whitelist
- `meeting`: Processed meeting metadata
- `segment`: Individual speaker segments
- `processing_queue`: Job queue management

**Relationships**:
```
User ─┬─ has many ──> Meeting
      └─ has many ──> AllowedUser (created)

Meeting ─┬─ has many ──> Segment
         └─ has one ──> ProcessingQueue
```

**Indexes**:
- `user.email` (unique, indexed)
- `allowed_user.email` (unique, indexed)
- `segment.meeting_id` (foreign key, indexed)
- `processing_queue.status` (for queue queries)

---

## Performance Optimizations

### GPU Acceleration
- **Whisper Transcription**: 3-5x faster on CUDA GPUs
- **Memory Management**: Clears cache after processing
- **Device Selection**: Automatic fallback to CPU

### Batch Processing
- **Gemini API**: 100 segments per batch
- **GPT-4**: 200 segments per batch (rate limit aware)
- **Overlap**: 5 segments between batches for context

### File Storage
- **Compression**: Efficient text formats
- **Cleanup**: Optional auto-delete old files
- **Streaming**: Large file handling for downloads

### Database
- **Connection Pooling**: SQLAlchemy managed
- **Lazy Loading**: Segments loaded on demand
- **Cascade Deletes**: Automatic cleanup of related records

---

## Error Handling

### Graceful Degradation

**Missing Dependencies**:
```python
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    # Falls back to basic speaker labels
```

**API Failures**:
- Retry with exponential backoff
- Fallback to alternative AI service
- Continue with partial results if possible

**Processing Failures**:
- Store error message in database
- Update meeting status to 'error'
- Allow reprocessing from any stage

### Logging
```python
from app.progress import get_logger
logger = get_logger()

logger.info("Processing started", step="transcription")
logger.error("API rate limit exceeded", retries_left=2)
```

---

## Deployment Configuration

### Environment Variables
```bash
# Flask Configuration
SECRET_KEY=your-secret-key
FLASK_DEBUG=False
DATABASE_URL=sqlite:///app.db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=524288000  # 500MB

# AI Services
GEMINI_API_KEY=your-gemini-key
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=GPT-4

# System Settings
USE_GPU=true
VERBOSE=false  # Clean progress logging
```

### Database Initialization
```bash
# Create database and tables
python init_db.py

# Run migrations
flask db upgrade

# Create admin user
python create_admin.py admin@itu.int
```

### Running the Application
```bash
# Development
python run.py

# Production (with Gunicorn)
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

---

## Security Measures

### Authentication
- Password hashing with werkzeug (PBKDF2)
- Session-based authentication (Flask-Login)
- CSRF protection on forms (Flask-WTF)

### Authorization
- Role-based access control (RBAC)
- Route protection with decorators
- Email whitelist for registration

### Data Protection
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (Jinja2 auto-escaping)
- File upload validation
- Secure file paths (no directory traversal)

---

## Monitoring & Maintenance

### System Health
- Queue length monitoring
- Processing time tracking
- API availability checks
- Storage usage monitoring

### Logs
- Application logs: `logs/itu_intern.log`
- Rotating file handler (10MB per file, 10 backups)
- Error tracking and debugging

### Database Maintenance
```bash
# Backup database
cp app.db backups/app_$(date +%Y%m%d).db

# Clear old processing queue
python -c "from app import *; clear_completed_queue(days=7)"
```

---

## Testing

### Unit Tests
- Model validation
- API endpoint testing
- Authentication flow
- File generation

### Integration Tests
- End-to-end processing pipeline
- Queue system functionality
- Multi-user scenarios

### Manual Testing Checklist
- [ ] Video download from UN WebTV
- [ ] Transcription accuracy on sample audio
- [ ] Speaker identification quality
- [ ] Meeting notes formatting
- [ ] Queue system with multiple users
- [ ] Admin panel functionality

---

## Known Limitations

### Current Constraints
- **Processing Speed**: ~15 minutes for 2-hour meeting (GPU)
- **Concurrent Processing**: One meeting at a time (queue system)
- **Speaker Accuracy**: 85-95% depending on audio quality
- **Language Support**: English only (expandable)

### API Rate Limits
- **Gemini**: 15 requests/minute (free tier)
- **Azure OpenAI**: 15K tokens/minute (organization limit)
- **Whisper**: Local processing (no API limit)

### Storage Requirements
- ~50MB per 2-hour meeting (all formats)
- Database grows with segment storage
- Consider periodic cleanup for old meetings

---

## Future Technical Enhancements

### Short Term
1. **Caching**: Redis for improved performance
2. **Async Processing**: Celery for true parallel processing
3. **Real-time Updates**: WebSocket for live status

### Medium Term
1. **Multi-language**: Whisper multilingual + translation
2. **Advanced Search**: Elasticsearch integration
3. **API Endpoints**: RESTful API for external integration

### Long Term
1. **Microservices**: Separate transcription, diarization services
2. **Cloud Deployment**: AWS/Azure scalable infrastructure
3. **ML Pipeline**: Custom fine-tuned models for ITU content

---

## Conclusion

The ITU WebTV Processing System is a production-ready application built with:
- **Robust architecture** for reliability
- **Modern AI/ML models** for accuracy
- **Scalable design** for growth
- **Security best practices** for enterprise use

All source code, documentation, and deployment scripts are available in the project repository.

