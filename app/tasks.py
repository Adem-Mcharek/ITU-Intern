"""
Simple Background Tasks - Threading-based
"""
import threading
import time
from pathlib import Path
from flask import current_app
from app import db
from app.models import Meeting, Segment
from app.pipeline import run_full_pipeline

def start_processing(meeting):
    """Start processing a meeting in the background using threading"""
    def process_meeting():
        """Background processing function"""
        from app import create_app
        app = create_app()
        
        with app.app_context():
            try:
                # Refresh meeting object in new context
                meeting_obj = Meeting.query.get(meeting.id)
                
                # Update status to processing
                meeting_obj.status = 'processing'
                db.session.commit()
                
                # Create meeting directory
                uploads_dir = Path(app.config['UPLOAD_FOLDER'])
                meeting_dir = uploads_dir / f"meeting_{meeting_obj.id}"
                meeting_dir.mkdir(parents=True, exist_ok=True)
                
                # Run the pipeline
                results = run_full_pipeline(meeting_obj.source_url, meeting_obj.title, str(meeting_dir))
                
                # Update meeting with results
                meeting_obj.audio_path = results.get('audio')
                meeting_obj.transcript_path = results.get('transcript')
                meeting_obj.srt_path = results.get('srt')
                meeting_obj.speakers_path = results.get('speakers')
                meeting_obj.status = 'completed'
                
                # Add segments to database
                for segment_data in results.get('segments', []):
                    segment = Segment(
                        meeting_id=meeting_obj.id,
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
                    summary_success = process_meeting_summary(meeting_obj.id, meeting_dir)
                    if summary_success:
                        print(f"✅ ITU summary generated successfully for meeting {meeting_obj.id}")
                    else:
                        print(f"⚠️  ITU summary generation failed for meeting {meeting_obj.id}")
                except Exception as e:
                    print(f"⚠️  Error generating ITU summary: {e}")
                    # Don't fail the entire processing if summary fails
                
                # Generate professional meeting notes after summary completion
                print("Step 9: Generating professional meeting notes...")
                try:
                    from app.meeting_notes_generator import process_meeting_notes
                    notes_success = process_meeting_notes(meeting_obj.id, meeting_dir, meeting_obj.title)
                    if notes_success:
                        print(f"✅ Meeting notes generated successfully for meeting {meeting_obj.id}")
                    else:
                        print(f"⚠️  Meeting notes generation failed for meeting {meeting_obj.id}")
                except Exception as e:
                    print(f"⚠️  Error generating meeting notes: {e}")
                    # Don't fail the entire processing if notes generation fails
                
                db.session.commit()
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Pipeline error for meeting {meeting.id}: {str(e)}")
                print(f"Full traceback: {error_details}")
                
                # Update status to error
                meeting_obj = Meeting.query.get(meeting.id)
                meeting_obj.status = 'error'
                meeting_obj.error_message = f"{str(e)}\n\nFull traceback:\n{error_details}"
                db.session.commit()
    
    # Start background thread
    thread = threading.Thread(target=process_meeting)
    thread.daemon = True
    thread.start()
    
    return f"thread_{meeting.id}"

def get_processing_status(meeting):
    """Get processing status for a meeting"""
    return {
        'status': meeting.status,
        'error_message': getattr(meeting, 'error_message', None)
    } 