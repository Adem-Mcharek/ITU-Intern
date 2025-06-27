"""
Queue Manager for Sequential Meeting Processing
Handles one meeting at a time with proper queue management
"""
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import current_app
from app import db
from app.models import Meeting, ProcessingQueue, Segment
from app.pipeline import run_full_pipeline

class QueueManager:
    """Singleton queue manager for processing meetings sequentially"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(QueueManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not getattr(self, '_initialized', False):
            self._initialized = True
            self._worker_thread = None
            self._worker_running = False
            self._stop_event = threading.Event()
            self._app = None
    
    def start_worker(self, app):
        """Start the background worker thread"""
        with self._lock:
            if self._worker_thread is None or not self._worker_thread.is_alive():
                self._app = app
                self._worker_running = True
                self._stop_event.clear()
                self._worker_thread = threading.Thread(target=self._worker_loop)
                self._worker_thread.daemon = True
                self._worker_thread.start()
                print("Queue worker started")
    
    def stop_worker(self):
        """Stop the background worker thread"""
        with self._lock:
            self._worker_running = False
            self._stop_event.set()
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=5)
                print("Queue worker stopped")
    
    def add_to_queue(self, meeting, priority=0):
        """Add a meeting to the processing queue"""
        try:
            with self._app.app_context() if self._app else current_app.app_context():
                # Check if already in queue
                existing_queue_item = ProcessingQueue.query.filter_by(meeting_id=meeting.id).first()
                if existing_queue_item:
                    return existing_queue_item
                
                # Create queue entry
                queue_item = ProcessingQueue(
                    meeting_id=meeting.id,
                    priority=priority,
                    status='queued'
                )
                
                db.session.add(queue_item)
                db.session.commit()
                
                print(f"Added meeting {meeting.id} to queue at position {queue_item.position_in_queue}")
                return queue_item
        except Exception as e:
            error_msg = str(e).lower()
            if 'no such table' in error_msg or 'no such column' in error_msg:
                print(f"Queue system not ready yet - falling back to immediate processing: {str(e)}")
                # Fallback to immediate processing if queue system not ready
                from app.tasks_backup import start_processing as fallback_start_processing
                return fallback_start_processing(meeting)
            else:
                print(f"Error adding to queue: {str(e)}")
                raise
    
    def get_queue_status(self):
        """Get current queue status"""
        try:
            with self._app.app_context() if self._app else current_app.app_context():
                # Current processing
                processing = ProcessingQueue.query.filter_by(status='processing').first()
                
                # Queued items
                queued = ProcessingQueue.query.filter_by(status='queued').order_by(
                    ProcessingQueue.priority.desc(),
                    ProcessingQueue.queued_at.asc()
                ).all()
                
                return {
                    'currently_processing': processing.meeting.title if processing else None,
                    'processing_meeting_id': processing.meeting_id if processing else None,
                    'queue_length': len(queued),
                    'queued_meetings': [
                        {
                            'id': item.meeting.id,
                            'title': item.meeting.title,
                            'position': item.position_in_queue,
                            'queued_at': item.queued_at.isoformat()
                        }
                        for item in queued
                    ]
                }
        except Exception as e:
            # Return empty status if tables don't exist yet (during migration)
            print(f"Queue status query failed (likely during migration): {e}")
            return {
                'currently_processing': None,
                'processing_meeting_id': None,
                'queue_length': 0,
                'queued_meetings': []
            }
    
    def _worker_loop(self):
        """Main worker loop - processes one meeting at a time"""
        print("Worker loop started")
        
        while self._worker_running and not self._stop_event.is_set():
            try:
                with self._app.app_context():
                    # Check for next item in queue
                    next_item = ProcessingQueue.query.filter_by(status='queued').order_by(
                        ProcessingQueue.priority.desc(),  # Higher priority first
                        ProcessingQueue.queued_at.asc()   # Then FIFO
                    ).first()
                    
                    if next_item:
                        self._process_queue_item(next_item)
                    else:
                        # No items in queue, wait before checking again
                        time.sleep(5)
                        
            except Exception as e:
                error_msg = str(e).lower()
                # If tables don't exist, wait longer and continue (migration in progress)
                if 'no such table' in error_msg or 'no such column' in error_msg:
                    print(f"Database not ready yet (migration may be needed): {str(e)}")
                    time.sleep(30)  # Wait longer during migration
                else:
                    print(f"Worker loop error: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(10)  # Wait before retrying
    
    def _process_queue_item(self, queue_item):
        """Process a single queue item"""
        try:
            print(f"Starting processing of meeting {queue_item.meeting_id}")
            
            # Update queue item status
            queue_item.status = 'processing'
            queue_item.started_at = datetime.utcnow()
            
            # Update meeting status
            meeting = queue_item.meeting
            meeting.status = 'processing'
            meeting.processing_started_at = datetime.utcnow()
            
            db.session.commit()
            
            # Create meeting directory
            uploads_dir = Path(self._app.config['UPLOAD_FOLDER'])
            meeting_dir = uploads_dir / f"meeting_{meeting.id}"
            meeting_dir.mkdir(parents=True, exist_ok=True)
            
            # Run the pipeline
            results = run_full_pipeline(meeting.source_url, meeting.title, str(meeting_dir))
            
            # Update meeting with results
            meeting.audio_path = results.get('audio')
            meeting.transcript_path = results.get('transcript')
            meeting.srt_path = results.get('srt')
            meeting.speakers_path = results.get('speakers')
            meeting.status = 'completed'
            meeting.processing_completed_at = datetime.utcnow()
            
            # Add segments to database
            for segment_data in results.get('segments', []):
                segment = Segment(
                    meeting_id=meeting.id,
                    speaker=segment_data.get('speaker'),
                    representing=segment_data.get('representing', ''),
                    content=segment_data.get('content'),
                    start_time=segment_data.get('start_time'),
                    end_time=segment_data.get('end_time')
                )
                db.session.add(segment)
            
            # Generate ITU-focused summary after pipeline completion
            print("Step 8: Generating ITU-focused meeting summary...")
            try:
                from app.meeting_summarizer import process_meeting_summary
                summary_success = process_meeting_summary(meeting.id, meeting_dir)
                if summary_success:
                    print(f"✅ ITU summary generated successfully for meeting {meeting.id}")
                else:
                    print(f"⚠️  ITU summary generation failed for meeting {meeting.id}")
            except Exception as e:
                print(f"⚠️  Error generating ITU summary: {e}")
                # Don't fail the entire processing if summary fails
            
            # Generate professional meeting notes after summary completion
            print("Step 9: Generating professional meeting notes...")
            try:
                from app.meeting_notes_generator import process_meeting_notes
                notes_success = process_meeting_notes(meeting.id, meeting_dir, meeting.title)
                if notes_success:
                    print(f"✅ Meeting notes generated successfully for meeting {meeting.id}")
                else:
                    print(f"⚠️  Meeting notes generation failed for meeting {meeting.id}")
            except Exception as e:
                print(f"⚠️  Error generating meeting notes: {e}")
                # Don't fail the entire processing if notes generation fails
            
            # Mark queue item as completed
            queue_item.status = 'completed'
            queue_item.completed_at = datetime.utcnow()
            
            db.session.commit()
            
            print(f"Successfully completed processing of meeting {meeting.id}")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Pipeline error for meeting {queue_item.meeting_id}: {str(e)}")
            print(f"Full traceback: {error_details}")
            
            # Update meeting status to error
            meeting = queue_item.meeting
            meeting.status = 'error'
            meeting.error_message = f"{str(e)}\n\nFull traceback:\n{error_details}"
            meeting.processing_completed_at = datetime.utcnow()
            
            # Mark queue item as failed
            queue_item.status = 'failed'
            queue_item.completed_at = datetime.utcnow()
            
            db.session.commit()

# Global queue manager instance
queue_manager = QueueManager()

def start_processing(meeting, priority=0):
    """Add meeting to processing queue"""
    return queue_manager.add_to_queue(meeting, priority)

def get_processing_status(meeting):
    """Get processing status for a meeting"""
    try:
        queue_status = queue_manager.get_queue_status()
        
        return {
            'status': meeting.status,
            'error_message': getattr(meeting, 'error_message', None),
            'queue_position': meeting.queue_position,
            'estimated_wait_time': meeting.estimated_wait_time,
            'currently_processing_id': queue_status.get('processing_meeting_id'),
            'queue_length': queue_status.get('queue_length', 0)
        }
    except Exception as e:
        # Fallback status if queue system not ready
        return {
            'status': meeting.status,
            'error_message': getattr(meeting, 'error_message', None),
            'queue_position': 0,
            'estimated_wait_time': '',
            'currently_processing_id': None,
            'queue_length': 0
        }

def get_queue_status():
    """Get overall queue status"""
    return queue_manager.get_queue_status() 