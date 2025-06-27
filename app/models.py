"""
Simple Database Models for WebTV Processing App
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_developer = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def role(self):
        """Get user role as string"""
        if self.is_developer:
            return 'Developer'
        elif self.is_admin:
            return 'Admin'
        else:
            return 'User'
    
    @property
    def has_admin_access(self):
        """Check if user has admin access (admin or developer)"""
        return self.is_admin or self.is_developer
    
    @property
    def has_developer_access(self):
        """Check if user has developer access"""
        return self.is_developer
    
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.is_developer
    
    def can_manage_admins(self):
        """Check if user can manage admin privileges"""
        return self.is_developer
    
    def __repr__(self):
        return f'<User {self.email}>'

class AllowedUser(db.Model):
    """Model for managing allowed user emails"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    added_by_admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_used = db.Column(db.Boolean, default=False, nullable=False)  # Track if email was used to register
    
    # Relationship
    added_by = db.relationship('User', backref='allowed_users_created')
    
    def __repr__(self):
        return f'<AllowedUser {self.email}>'

class ProcessingQueue(db.Model):
    """Queue model for managing sequential processing"""
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    priority = db.Column(db.Integer, default=0, nullable=False)  # Higher number = higher priority
    queued_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(32), default="queued", nullable=False)  # queued|processing|completed|failed
    
    # Relationship
    meeting = db.relationship('Meeting', backref='queue_entry', uselist=False)
    
    @property
    def position_in_queue(self):
        """Get position in queue (1-based)"""
        try:
            if self.status != 'queued':
                return 0
            
            # Count items ahead of this one
            ahead_count = ProcessingQueue.query.filter(
                ProcessingQueue.status == 'queued',
                ProcessingQueue.priority > self.priority,  # Higher priority first
                ProcessingQueue.queued_at < self.queued_at  # Then by time
            ).count()
            
            return ahead_count + 1
        except Exception:
            # Return 1 if unable to calculate (during migration)
            return 1
    
    def __repr__(self):
        return f'<ProcessingQueue meeting_id={self.meeting_id} status={self.status}>'

class Meeting(db.Model):
    """Meeting model for storing WebTV processing jobs"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    source_url = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(32), default="queued")  # queued|processing|completed|error
    error_message = db.Column(db.Text)
    
    # Processing timestamps
    processing_started_at = db.Column(db.DateTime, nullable=True)
    processing_completed_at = db.Column(db.DateTime, nullable=True)
    
    # User tracking
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by = db.relationship('User', backref='meetings_created')
    
    # File paths (relative to uploads directory)
    audio_path = db.Column(db.String(512))
    transcript_path = db.Column(db.String(512))
    srt_path = db.Column(db.String(512))
    speakers_path = db.Column(db.String(512))
    notes_path = db.Column(db.String(512))  # Path to generated meeting notes .docx
    
    # ITU-focused meeting summary
    itu_summary = db.Column(db.Text)
    
    # Relationship
    segments = db.relationship("Segment", backref="meeting", lazy=True, cascade="all, delete-orphan")
    
    @property
    def is_complete(self):
        """Check if processing is complete"""
        return self.status == 'completed'
    
    @property
    def has_files(self):
        """Check if any files are available"""
        return any([self.audio_path, self.transcript_path, self.srt_path, self.speakers_path])
    
    @property
    def status_badge_class(self):
        """Get CSS class for status badge"""
        status_classes = {
            'queued': 'bg-secondary',
            'processing': 'bg-warning',
            'completed': 'bg-success',
            'done': 'bg-success',
            'error': 'bg-danger'
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    @property
    def queue_position(self):
        """Get position in processing queue"""
        try:
            if hasattr(self, 'queue_entry') and self.queue_entry:
                return self.queue_entry.position_in_queue
            return 0
        except Exception:
            # Return 0 if queue system not ready
            return 0
    
    @property
    def estimated_wait_time(self):
        """Estimate wait time based on queue position (rough estimate)"""
        try:
            position = self.queue_position
            if position <= 1:
                return "Starting soon"
            
            # Rough estimate: 10 minutes per meeting ahead
            estimated_minutes = (position - 1) * 10
            if estimated_minutes < 60:
                return f"~{estimated_minutes} minutes"
            else:
                hours = estimated_minutes // 60
                minutes = estimated_minutes % 60
                if minutes == 0:
                    return f"~{hours} hour{'s' if hours > 1 else ''}"
                else:
                    return f"~{hours}h {minutes}m"
        except Exception:
            # Return empty string if queue system not ready
            return ""

class Segment(db.Model):
    """Segment model for storing speaker segments"""
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    speaker = db.Column(db.String(128))
    representing = db.Column(db.String(256))  # Country/Organization
    content = db.Column(db.Text)
    start_time = db.Column(db.Float)  # seconds
    end_time = db.Column(db.Float)    # seconds
    
    def to_dict(self):
        """Convert segment to dictionary"""
        return {
            'id': self.id,
            'speaker': self.speaker,
            'representing': self.representing,
            'content': self.content,
            'start_time': self.start_time,
            'end_time': self.end_time
        } 