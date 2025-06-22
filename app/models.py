"""
Simple Database Models for WebTV Processing App
"""
from datetime import datetime
from app import db

class Meeting(db.Model):
    """Meeting model for storing WebTV processing jobs"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    source_url = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(32), default="queued")  # queued|processing|completed|error
    error_message = db.Column(db.Text)
    
    # File paths (relative to uploads directory)
    audio_path = db.Column(db.String(512))
    transcript_path = db.Column(db.String(512))
    srt_path = db.Column(db.String(512))
    speakers_path = db.Column(db.String(512))
    
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