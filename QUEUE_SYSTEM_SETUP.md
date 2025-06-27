# Queue System Setup Guide

This guide shows you how to upgrade your WebTV processing application to use a queue system for production deployment with multiple users.

## Overview

Your current system processes meetings immediately using background threads. For production with multiple users, you need a queue system to:

1. **Process one meeting at a time** (prevents resource conflicts)
2. **Queue incoming requests** when the system is busy
3. **Automatically process the next item** when current processing completes
4. **Provide queue status** to users (position, estimated wait time)

## Option 1: Database-Based Queue (Recommended for SQLite)

This is the **simpler option** that fits your current SQLite setup.

### 1. Run the Migration

```bash
# Run the migration script to upgrade your database
python upgrade_to_queue_system.py
```

### 2. Restart Your Application

```bash
# Stop your current application (Ctrl+C)
# Then restart
python run.py
```

### 3. Verify It's Working

- Submit a new meeting - it should show queue position
- Check the admin panel for queue status
- Look at the console logs for queue worker messages

### Features:
- ✅ Sequential processing (one at a time)
- ✅ Queue position tracking
- ✅ Estimated wait times
- ✅ Admin queue monitoring
- ✅ Works with existing SQLite database
- ✅ No additional dependencies

## Option 2: Redis + Celery (Production-Grade)

For **high-traffic production** environments, Redis + Celery is more robust.

### Dependencies

```bash
pip install redis celery
```

### Setup Redis

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Windows:**
```bash
# Download and install Redis for Windows
# Or use Docker: docker run -d -p 6379:6379 redis:alpine
```

### Configuration

Add to your `.env` file:
```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Implementation

Create `app/celery_tasks.py`:

```python
from celery import Celery
from app import create_app, db
from app.models import Meeting, Segment
from app.pipeline import run_full_pipeline

# Initialize Celery
celery = Celery('webty_processor')
celery.config_from_object('celeryconfig')

@celery.task(bind=True)
def process_meeting_task(self, meeting_id):
    """Celery task to process a meeting"""
    app = create_app()
    
    with app.app_context():
        try:
            meeting = Meeting.query.get(meeting_id)
            if not meeting:
                return {'status': 'error', 'message': 'Meeting not found'}
            
            # Update status
            meeting.status = 'processing'
            db.session.commit()
            
            # Process meeting (same logic as before)
            # ... (processing code)
            
            return {'status': 'completed', 'meeting_id': meeting_id}
            
        except Exception as e:
            meeting = Meeting.query.get(meeting_id)
            meeting.status = 'error'
            meeting.error_message = str(e)
            db.session.commit()
            return {'status': 'error', 'message': str(e)}
```

### Running Celery

```bash
# Terminal 1: Start the Celery worker
celery -A app.celery_tasks worker --loglevel=info --concurrency=1

# Terminal 2: Start your Flask app
python run.py
```

### Features:
- ✅ Production-grade queue system
- ✅ Distributed processing capability
- ✅ Task retry mechanisms
- ✅ Monitoring with Flower
- ✅ Scales to multiple workers
- ✅ Redis persistence

## Comparison

| Feature | Database Queue | Redis + Celery |
|---------|----------------|----------------|
| Setup Complexity | Simple | Moderate |
| Dependencies | None (uses existing DB) | Redis, Celery |
| Performance | Good for <100 jobs/day | Excellent |
| Scalability | Single server | Multi-server |
| Monitoring | Basic admin panel | Advanced (Flower) |
| Persistence | SQLite/Postgres | Redis |
| Recommended For | Small to medium deployments | High-traffic production |

## Migration Summary

### What Changed:

1. **New Database Model**: `ProcessingQueue` table manages the queue
2. **Sequential Processing**: Only one meeting processes at a time
3. **Queue Position Tracking**: Users see their position and estimated wait time
4. **Enhanced Status Updates**: Real-time queue information in the UI
5. **Admin Monitoring**: Admin/developer panels show queue status

### Files Modified:

- `app/models.py` - Added ProcessingQueue model and queue methods
- `app/queue_manager.py` - New queue management system (replaces tasks.py)
- `app/routes.py` - Updated to use queue system and show queue info
- `app/__init__.py` - Starts queue worker on app startup
- `app/templates/_components/status_badge.html` - Shows queue position
- `app/static/js/live_status.js` - Handles queue status updates

### Backup Files:

- `app/tasks_backup.py` - Original threading implementation (for reference)

## Monitoring Queue Status

### User View:
- Queue position shown in meeting status
- Estimated wait time displayed
- Real-time updates via JavaScript

### Admin View:
- Total queue length
- Currently processing meeting
- Queue status API endpoint: `/api/queue/status`

## Troubleshooting

### Queue Worker Not Starting:
```bash
# Check console logs for errors
python run.py

# Look for: "Queue worker started"
```

### Database Migration Issues:
```bash
# If migration fails, check database manually
python -c "from app import create_app, db; app=create_app(); app.app_context().push(); print('Tables:', db.engine.table_names())"
```

### Queue Not Processing:
```bash
# Check if worker thread is alive
# Look for console messages about processing
# Verify database queue has items
```

## Production Deployment Tips

1. **Use a proper database** (PostgreSQL) instead of SQLite for production
2. **Set up monitoring** to track queue lengths and processing times
3. **Configure proper logging** to track queue operations
4. **Set resource limits** to prevent memory issues during processing
5. **Add health checks** for the queue worker

## Rollback Plan

If you need to rollback to the old system:

1. Stop the application
2. Replace `app/tasks.py` with `app/tasks_backup.py`
3. Update `app/routes.py` to import from `tasks` instead of `queue_manager`
4. Remove queue worker startup from `app/__init__.py`
5. Restart the application

The database changes are additive, so rollback won't break existing data. 