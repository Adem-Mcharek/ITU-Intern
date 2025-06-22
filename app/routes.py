"""
Simple Routes for WebTV Processing App
"""
import os
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file, abort, current_app
from sqlalchemy import or_, text
from app import db
from app.models import Meeting, Segment
from app.forms import UrlForm, SearchForm
from app.tasks import start_processing, get_processing_status
from datetime import datetime

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """Home page with URL submission form"""
    form = UrlForm()
    
    if form.validate_on_submit():
        try:
            # Create new meeting record
            meeting = Meeting(
                title=form.title.data,
                source_url=form.url.data,
                status='queued'
            )
            db.session.add(meeting)
            db.session.commit()
            
            # Start processing in background
            start_processing(meeting)
            
            flash(f'Processing started for "{meeting.title}".', 'success')
            return redirect(url_for('main.meeting_detail', id=meeting.id))
            
        except Exception as e:
            flash('Failed to start processing. Please try again.', 'error')
    
    # Show recent meetings
    recent_meetings = Meeting.query.order_by(Meeting.created_at.desc()).limit(5).all()
    
    return render_template('index.html', form=form, recent_meetings=recent_meetings)

@main_bp.route('/meetings')
def meetings():
    """List all meetings"""
    form = SearchForm(request.args)
    
    # Build query
    query = Meeting.query
    
    # Apply search filter
    if form.query.data:
        search_term = f"%{form.query.data}%"
        query = query.filter(
            or_(
                Meeting.title.like(search_term),
                Meeting.source_url.like(search_term)
            )
        )
    
    # Apply status filter
    if form.status.data:
        query = query.filter(Meeting.status == form.status.data)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    meetings = query.order_by(Meeting.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    
    return render_template('meetings.html', meetings=meetings, form=form)

@main_bp.route('/meetings/<int:id>')
def meeting_detail(id):
    """Detailed view of a single meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Get segments
    segments = Segment.query.filter_by(meeting_id=id).order_by(
        Segment.start_time.asc().nullslast()
    ).all()
    
    return render_template('meeting_detail.html', meeting=meeting, segments=segments)

@main_bp.route('/api/status/<int:id>')
def api_meeting_status(id):
    """API endpoint to get meeting processing status"""
    meeting = Meeting.query.get_or_404(id)
    
    return jsonify({
        'meeting_id': meeting.id,
        'status': meeting.status,
        'error_message': meeting.error_message,
        'files': {
            'audio': bool(meeting.audio_path),
            'transcript': bool(meeting.transcript_path),
            'srt': bool(meeting.srt_path),
            'speakers': bool(meeting.speakers_path)
        },
        'segments_count': len(meeting.segments)
    })

@main_bp.route('/download/<int:id>/<file_type>')
def download_file(id, file_type):
    """Download files"""
    meeting = Meeting.query.get_or_404(id)
    
    # Map file types to paths
    file_paths = {
        'audio': meeting.audio_path,
        'transcript': meeting.transcript_path,
        'srt': meeting.srt_path,
        'speakers': meeting.speakers_path
    }
    
    if file_type not in file_paths or not file_paths[file_type]:
        abort(404, description="File not available")
    
    # Build full path
    full_path = Path(current_app.config['UPLOAD_FOLDER']) / file_paths[file_type]
    
    if not full_path.exists():
        abort(404, description="File not found")
    
    # Generate filename
    safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in meeting.title)
    filename_map = {
        'audio': f"{safe_title}_audio.mp3",
        'transcript': f"{safe_title}_transcript.txt",
        'srt': f"{safe_title}_subtitles.srt",
        'speakers': f"{safe_title}_speakers.txt"
    }
    
    return send_file(full_path, as_attachment=True, download_name=filename_map[file_type])

@main_bp.route('/meetings/<int:id>/delete', methods=['POST'])
def delete_meeting(id):
    """Delete a meeting and its files"""
    meeting = Meeting.query.get_or_404(id)
    
    try:
        # Delete files from disk
        upload_dir = Path(current_app.config['UPLOAD_FOLDER'])
        meeting_dir = upload_dir / f"meeting_{id}"
        
        if meeting_dir.exists():
            import shutil
            shutil.rmtree(meeting_dir)
        
        # Delete from database
        db.session.delete(meeting)
        db.session.commit()
        
        flash(f'Meeting "{meeting.title}" has been deleted.', 'success')
        
    except Exception as e:
        flash('Failed to delete meeting. Please try again.', 'error')
    
    return redirect(url_for('main.meetings'))

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

# Error handlers
@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Template context processors
@main_bp.app_context_processor
def inject_app_info():
    """Inject application information into templates"""
    return {
        'app_version': os.environ.get('APP_VERSION', 'dev'),
        'git_hash': os.environ.get('GIT_HASH', 'unknown')[:8],
        'current_year': datetime.now().year
    } 