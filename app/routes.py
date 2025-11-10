"""
Routes for ITU Intern WebTV Processing App with Authentication
"""
import os
import re
from pathlib import Path
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_, text
from app import db
from app.models import Meeting, Segment, User, AllowedUser
from app.forms import UrlForm, SearchForm, LoginForm, SignupForm, AddUserForm, BulkAddUsersForm, AdminUserForm, DeveloperUserForm, CreateAdminForm
from app.queue_manager import start_processing, get_processing_status, get_queue_status

# Create blueprint
bp = Blueprint('main', __name__)

def admin_required(f):
    """Decorator to require admin access (admin or developer)"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_admin_access:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def developer_required(f):
    """Decorator to require developer access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_developer_access:
            flash('Developer access required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# Authentication routes
@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=form.remember_me.data)
            
            # Redirect to next page or index
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            
            flash(f'Welcome back, {user.email}!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = SignupForm()
    if form.validate_on_submit():
        # Create new user
        user = User(email=form.email.data.lower())
        user.set_password(form.password.data)
        
        # Mark allowed user as used
        allowed_user = AllowedUser.query.filter_by(email=form.email.data.lower()).first()
        if allowed_user:
            allowed_user.is_used = True
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('auth/signup.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

# Main application routes
@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """Home page with URL submission form and file upload"""
    form = UrlForm()
    
    if form.validate_on_submit():
        try:
            # Handle file upload if file input type is selected
            if form.input_type.data == 'file' and form.audio_file.data:
                # Save uploaded file
                uploaded_file = form.audio_file.data
                filename = uploaded_file.filename
                
                # Create meeting record with file indicator
                meeting = Meeting(
                    title=form.title.data,
                    source_url=f"file_upload://{filename}",  # Special URL format for uploaded files
                    status='queued',
                    created_by_user_id=current_user.id
                )
                db.session.add(meeting)
                db.session.commit()
                
                # Create uploads directory for this meeting
                meeting_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads')) / f'meeting_{meeting.id}'
                meeting_dir.mkdir(parents=True, exist_ok=True)
                
                # Save the uploaded file with its original extension
                file_extension = Path(filename).suffix.lower()
                if file_extension in ['.mp3', '.wav', '.m4a', '.ogg']:
                    # Save with original extension first
                    audio_path = meeting_dir / f'audio{file_extension}'
                    uploaded_file.save(str(audio_path))
                    
                    # Update meeting record to indicate we have an audio file
                    # The pipeline will handle conversion to MP3 during processing
                    meeting.audio_path = str(meeting_dir / 'audio.mp3')  # Final expected path
                    db.session.commit()
                else:
                    # Shouldn't happen due to form validation, but just in case
                    raise ValueError(f"Unsupported file format: {file_extension}")
                
            else:
                # Handle URL input (existing functionality)
                meeting = Meeting(
                    title=form.title.data,
                    source_url=form.url.data.strip(),
                    status='queued',
                    created_by_user_id=current_user.id
                )
                db.session.add(meeting)
                db.session.commit()
            
            # Start processing in background
            start_processing(meeting)
            
            flash(f'Processing started for "{meeting.title}".', 'success')
            return redirect(url_for('main.meeting_detail', id=meeting.id))
            
        except Exception as e:
            import traceback
            current_app.logger.error(f"Processing error: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            flash(f'Failed to start processing: {str(e)}', 'error')
    
    # Show recent meetings
    recent_meetings = Meeting.query.order_by(Meeting.created_at.desc()).limit(5).all()
    
    return render_template('index.html', form=form, recent_meetings=recent_meetings)

@bp.route('/meetings')
@login_required
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

@bp.route('/meetings/<int:id>')
@login_required
def meeting_detail(id):
    """Detailed view of a single meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Get segments
    segments = Segment.query.filter_by(meeting_id=id).order_by(
        Segment.start_time.asc().nullslast()
    ).all()
    
    return render_template('meeting_detail.html', meeting=meeting, segments=segments)

@bp.route('/api/status/<int:id>')
@login_required
def api_meeting_status(id):
    """API endpoint to get meeting processing status"""
    meeting = Meeting.query.get_or_404(id)
    processing_status = get_processing_status(meeting)
    
    return jsonify({
        'meeting_id': meeting.id,
        'status': meeting.status,
        'error_message': meeting.error_message,
        'queue_position': processing_status.get('queue_position', 0),
        'estimated_wait_time': processing_status.get('estimated_wait_time', ''),
        'currently_processing_id': processing_status.get('currently_processing_id'),
        'queue_length': processing_status.get('queue_length', 0),
        'files': {
            'audio': bool(meeting.audio_path),
            'transcript': bool(meeting.transcript_path),
            'srt': bool(meeting.srt_path),
            'speakers': bool(meeting.speakers_path)
        },
        'segments_count': len(meeting.segments)
    })

@bp.route('/download/<int:id>/<file_type>')
@login_required
def download_file(id, file_type):
    """Download files"""
    meeting = Meeting.query.get_or_404(id)
    
    # Map file types to paths
    file_paths = {
        'audio': meeting.audio_path,
        'transcript': meeting.transcript_path,
        'srt': meeting.srt_path,
        'speakers': meeting.speakers_path,
        'notes': meeting.notes_path
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
        'speakers': f"{safe_title}_speakers.txt",
        'notes': f"{safe_title}_meeting_notes.docx"
    }
    
    return send_file(full_path, as_attachment=True, download_name=filename_map[file_type])

@bp.route('/meetings/<int:id>/delete', methods=['POST'])
@login_required
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

@bp.route('/about')
@login_required
def about():
    """About page"""
    return render_template('about.html')

# Admin routes
@bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    users_count = User.query.count()
    allowed_users_count = AllowedUser.query.count()
    unused_allowed_count = AllowedUser.query.filter_by(is_used=False).count()
    meetings_count = Meeting.query.count()
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_meetings = Meeting.query.order_by(Meeting.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         users_count=users_count,
                         allowed_users_count=allowed_users_count,
                         unused_allowed_count=unused_allowed_count,
                         meetings_count=meetings_count,
                         recent_users=recent_users,
                         recent_meetings=recent_meetings)

@bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Admin users management"""
    page = request.args.get('page', 1, type=int)
    
    # Get all users
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get allowed users
    allowed_users = AllowedUser.query.order_by(AllowedUser.added_at.desc()).all()
    
    # Forms
    add_user_form = AddUserForm()
    bulk_add_form = BulkAddUsersForm()
    admin_user_form = AdminUserForm()
    
    # Populate admin user form choices (exclude developers for regular admins)
    if current_user.is_developer:
        # Developers can see all users
        admin_user_form.user_id.choices = [(u.id, f"{u.email} ({u.role})") 
                                           for u in User.query.all()]
    else:
        # Regular admins can only see non-developer users
        admin_user_form.user_id.choices = [(u.id, f"{u.email} ({u.role})") 
                                           for u in User.query.filter_by(is_developer=False).all()]
    
    return render_template('admin/users.html', 
                         users=users, 
                         allowed_users=allowed_users,
                         add_user_form=add_user_form,
                         bulk_add_form=bulk_add_form,
                         admin_user_form=admin_user_form)

@bp.route('/admin/users/add', methods=['POST'])
@login_required
@admin_required
def admin_add_user():
    """Add allowed user"""
    form = AddUserForm()
    
    if form.validate_on_submit():
        allowed_user = AllowedUser(
            email=form.email.data.lower(),
            added_by_admin_id=current_user.id
        )
        db.session.add(allowed_user)
        db.session.commit()
        
        flash(f'Email {form.email.data} added to allowed users list.', 'success')
    else:
        for error in form.errors.values():
            flash(error[0], 'error')
    
    return redirect(url_for('main.admin_users'))

@bp.route('/admin/users/bulk-add', methods=['POST'])
@login_required
@admin_required
def admin_bulk_add_users():
    """Bulk add allowed users"""
    form = BulkAddUsersForm()
    
    if form.validate_on_submit():
        emails = form.emails.data.strip().split('\n')
        added_count = 0
        errors = []
        
        for email_line in emails:
            email = email_line.strip().lower()
            if not email:
                continue
                
            # Basic email validation
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                errors.append(f"Invalid email: {email}")
                continue
            
            # Check if already exists
            if AllowedUser.query.filter_by(email=email).first():
                errors.append(f"Email already in list: {email}")
                continue
                
            if User.query.filter_by(email=email).first():
                errors.append(f"User already registered: {email}")
                continue
            
            # Add to allowed users
            allowed_user = AllowedUser(
                email=email,
                added_by_admin_id=current_user.id
            )
            db.session.add(allowed_user)
            added_count += 1
        
        try:
            db.session.commit()
            flash(f'Added {added_count} email(s) to allowed users list.', 'success')
            
            if errors:
                flash(f'Errors: {"; ".join(errors[:5])}{"..." if len(errors) > 5 else ""}', 'warning')
                
        except Exception as e:
            db.session.rollback()
            flash('Failed to add users. Please try again.', 'error')
    else:
        for error in form.errors.values():
            flash(error[0], 'error')
    
    return redirect(url_for('main.admin_users'))

@bp.route('/admin/users/manage', methods=['POST'])
@login_required
@admin_required
def admin_manage_user():
    """Manage existing user"""
    form = AdminUserForm()
    
    # Populate form choices before validation
    if current_user.is_developer:
        # Developers can see all users
        form.user_id.choices = [(u.id, f"{u.email} ({u.role})") 
                               for u in User.query.all()]
    else:
        # Regular admins can only see non-developer users
        form.user_id.choices = [(u.id, f"{u.email} ({u.role})") 
                               for u in User.query.filter_by(is_developer=False).all()]
    
    if form.validate_on_submit():
        user = User.query.get_or_404(form.user_id.data)
        
        # Prevent admin from demoting themselves if they're the only admin
        if (form.action.data == 'toggle_admin' and user.id == current_user.id and 
            User.query.filter_by(is_admin=True).count() == 1):
            flash('Cannot remove admin status from the only admin user.', 'error')
            return redirect(url_for('main.admin_users'))
        
        # Prevent regular admins from managing developer users
        if user.is_developer and not current_user.is_developer:
            flash('Cannot modify developer users. Developer access required.', 'error')
            return redirect(url_for('main.admin_users'))
        
        # Prevent developers from being deleted by regular admins
        if form.action.data == 'delete' and user.is_developer and not current_user.is_developer:
            flash('Cannot delete developer users. Developer access required.', 'error')
            return redirect(url_for('main.admin_users'))
        
        if form.action.data == 'toggle_admin':
            # Don't allow demoting developers to non-admin (developers are always admin)
            if user.is_developer and user.is_admin:
                flash('Cannot remove admin status from developer users.', 'error')
                return redirect(url_for('main.admin_users'))
            
            user.is_admin = not user.is_admin
            action_text = 'granted admin access' if user.is_admin else 'removed admin access'
            flash(f'User {user.email} {action_text}.', 'success')
            
        elif form.action.data == 'toggle_active':
            user.is_active = not user.is_active
            action_text = 'activated' if user.is_active else 'deactivated'
            flash(f'User {user.email} {action_text}.', 'success')
            
        elif form.action.data == 'delete':
            if user.id == current_user.id:
                flash('Cannot delete your own account.', 'error')
                return redirect(url_for('main.admin_users'))
            
            db.session.delete(user)
            flash(f'User {user.email} deleted.', 'success')
        
        db.session.commit()
    else:
        for error in form.errors.values():
            flash(error[0], 'error')
    
    return redirect(url_for('main.admin_users'))

@bp.route('/admin/users/<int:allowed_user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_allowed_user(allowed_user_id):
    """Delete allowed user"""
    allowed_user = AllowedUser.query.get_or_404(allowed_user_id)
    
    try:
        db.session.delete(allowed_user)
        db.session.commit()
        flash(f'Email {allowed_user.email} removed from allowed users list.', 'success')
    except Exception as e:
        flash('Failed to remove email. Please try again.', 'error')
    
    return redirect(url_for('main.admin_users'))

# Developer routes
@bp.route('/dev')
@login_required
@developer_required
def dev_dashboard():
    """Developer dashboard"""
    # Get statistics
    total_users = User.query.count()
    admin_users = User.query.filter_by(is_admin=True).count()
    developer_users = User.query.filter_by(is_developer=True).count()
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = User.query.filter_by(is_active=False).count()
    
    allowed_users_count = AllowedUser.query.count()
    unused_allowed_count = AllowedUser.query.filter_by(is_used=False).count()
    meetings_count = Meeting.query.count()
    
    # Get recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_meetings = Meeting.query.order_by(Meeting.created_at.desc()).limit(5).all()
    
    return render_template('admin/dev_dashboard.html',
                         total_users=total_users,
                         admin_users=admin_users,
                         developer_users=developer_users,
                         active_users=active_users,
                         inactive_users=inactive_users,
                         allowed_users_count=allowed_users_count,
                         unused_allowed_count=unused_allowed_count,
                         meetings_count=meetings_count,
                         recent_users=recent_users,
                         recent_meetings=recent_meetings)

@bp.route('/dev/users')
@login_required
@developer_required
def dev_users():
    """Developer user management"""
    page = request.args.get('page', 1, type=int)
    
    # Get all users
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get allowed users
    allowed_users = AllowedUser.query.order_by(AllowedUser.added_at.desc()).all()
    
    # Forms
    add_user_form = AddUserForm()
    bulk_add_form = BulkAddUsersForm()
    dev_user_form = DeveloperUserForm()
    create_admin_form = CreateAdminForm()
    
    # Populate developer user form choices
    dev_user_form.user_id.choices = [(u.id, f"{u.email} ({u.role})") 
                                     for u in User.query.all()]
    
    return render_template('admin/dev_users.html', 
                         users=users, 
                         allowed_users=allowed_users,
                         add_user_form=add_user_form,
                         bulk_add_form=bulk_add_form,
                         dev_user_form=dev_user_form,
                         create_admin_form=create_admin_form)

@bp.route('/dev/users/manage', methods=['POST'])
@login_required
@developer_required
def dev_manage_user():
    """Developer user privilege management"""
    form = DeveloperUserForm()
    
    # Populate form choices before validation
    form.user_id.choices = [(u.id, f"{u.email} ({u.role})") 
                           for u in User.query.all()]
    
    if form.validate_on_submit():
        user = User.query.get_or_404(form.user_id.data)
        
        # Prevent removing the last developer from the system
        if (form.action.data == 'remove_developer' and 
            User.query.filter_by(is_developer=True).count() == 1):
            flash('Cannot remove developer status from the only developer user.', 'error')
            return redirect(url_for('main.dev_users'))
        
        # Prevent users from deleting themselves
        if form.action.data == 'delete' and user.id == current_user.id:
            flash('Cannot delete your own account.', 'error')
            return redirect(url_for('main.dev_users'))
        
        if form.action.data == 'make_admin':
            user.is_admin = True
            flash(f'User {user.email} granted admin privileges.', 'success')
            
        elif form.action.data == 'remove_admin':
            # Don't allow removing admin from developer users (developers are always admin)
            if user.is_developer:
                flash('Cannot remove admin privileges from developer users. Remove developer status first.', 'error')
                return redirect(url_for('main.dev_users'))
            
            user.is_admin = False
            flash(f'User {user.email} admin privileges removed.', 'success')
            
        elif form.action.data == 'make_developer':
            user.is_developer = True
            user.is_admin = True  # Developers are automatically admins
            flash(f'User {user.email} granted developer privileges.', 'success')
            
        elif form.action.data == 'remove_developer':
            user.is_developer = False
            flash(f'User {user.email} developer privileges removed.', 'success')
            
        elif form.action.data == 'toggle_active':
            user.is_active = not user.is_active
            action_text = 'activated' if user.is_active else 'deactivated'
            flash(f'User {user.email} {action_text}.', 'success')
            
        elif form.action.data == 'delete':
            db.session.delete(user)
            flash(f'User {user.email} deleted.', 'success')
        
        db.session.commit()
    else:
        for error in form.errors.values():
            flash(error[0], 'error')
    
    return redirect(url_for('main.dev_users'))

@bp.route('/dev/users/create-admin', methods=['POST'])
@login_required
@developer_required
def dev_create_admin():
    """Create new admin/developer user"""
    form = CreateAdminForm()
    
    if form.validate_on_submit():
        # Create new user
        user = User(
            email=form.email.data.lower(),
            is_admin=form.is_admin.data,
            is_developer=form.is_developer.data,
            is_active=True
        )
        user.set_password(form.password.data)
        
        # If developer, automatically make admin too
        if user.is_developer:
            user.is_admin = True
        
        db.session.add(user)
        db.session.commit()
        
        role_text = user.role
        flash(f'{role_text} user {user.email} created successfully.', 'success')
    else:
        for error in form.errors.values():
            flash(error[0], 'error')
    
    return redirect(url_for('main.dev_users'))

# API routes
@bp.route('/api/queue/status')
@login_required
@admin_required
def api_queue_status():
    """API endpoint to get overall queue status (admin only)"""
    queue_status = get_queue_status()
    return jsonify(queue_status)

@bp.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

# Error handlers
@bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Template context processors
@bp.app_context_processor
def inject_app_info():
    """Inject application information into templates"""
    from flask_login import current_user
    
    context = {
        'app_version': os.environ.get('APP_VERSION', 'dev'),
        'git_hash': os.environ.get('GIT_HASH', 'unknown')[:8],
        'current_year': datetime.now().year
    }
    
    # Add user role information for templates
    if current_user.is_authenticated:
        context.update({
            'user_role': current_user.role,
            'is_developer_user': current_user.has_developer_access,
            'is_admin_user': current_user.has_admin_access,
            'is_regular_user': not current_user.has_admin_access
        })
    
    return context 