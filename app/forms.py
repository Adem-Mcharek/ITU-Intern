"""
Forms for WebTV Processing App
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, URLField, SubmitField, SelectField, PasswordField, BooleanField, RadioField
from wtforms.validators import DataRequired, URL, Length, Optional, Email, EqualTo, ValidationError
from app.models import User, AllowedUser

class UrlForm(FlaskForm):
    """Form for submitting video URLs or audio files for processing"""
    input_type = RadioField(
        'Input Type',
        choices=[
            ('url', 'Video URL'),
            ('file', 'Audio File Upload')
        ],
        default='url',
        validators=[DataRequired()]
    )
    url = URLField(
        'Video URL', 
        validators=[Optional(), URL()],
        description='Paste URL from UN WebTV, YouTube, Vimeo, or other supported video platforms',
        render_kw={'autocomplete': 'off', 'spellcheck': 'false'}
    )
    audio_file = FileField(
        'Audio File',
        validators=[
            Optional(),
            FileAllowed(['mp3', 'wav', 'm4a', 'ogg'], 'Audio files only! (MP3, WAV, M4A, OGG)')
        ],
        description='Upload an audio file (MP3, WAV, M4A, OGG)'
    )
    title = StringField(
        'Meeting Title', 
        validators=[DataRequired(), Length(min=3, max=256)],
        description='Enter a descriptive title for this meeting'
    )
    submit = SubmitField('Process Content')
    
    def validate(self, extra_validators=None):
        """Custom validation to ensure either URL or file is provided"""
        if not super().validate(extra_validators):
            return False
            
        if self.input_type.data == 'url':
            if not self.url.data:
                self.url.errors.append('Video URL is required when URL input type is selected.')
                return False
        elif self.input_type.data == 'file':
            if not self.audio_file.data:
                self.audio_file.errors.append('Audio file is required when file upload input type is selected.')
                return False
                
        return True

class SearchForm(FlaskForm):
    """Form for searching meetings"""
    query = StringField(
        'Search', 
        validators=[Optional(), Length(max=100)],
        description='Search by title, speaker, or content'
    )
    status = SelectField(
        'Status',
        choices=[
            ('', 'All Statuses'),
            ('queued', 'Queued'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('error', 'Error')
        ],
        validators=[Optional()]
    )
    submit = SubmitField('Search')

class ProcessingForm(FlaskForm):
    """Form for WebTV processing"""
    title = StringField('Meeting Title', validators=[DataRequired(), Length(min=5, max=200)])
    source_url = StringField('WebTV URL', validators=[DataRequired(), URL()])
    submit = SubmitField('Start Processing')

class LoginForm(FlaskForm):
    """Login form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class SignupForm(FlaskForm):
    """Signup form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        """Custom validation for email"""
        # Check if user already exists
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('Email already registered.')
        
        # Check if email is in allowed list
        allowed = AllowedUser.query.filter_by(email=email.data.lower()).first()
        if not allowed:
            raise ValidationError('Email not authorized for registration. Contact administrator.')

class AddUserForm(FlaskForm):
    """Form for admin to add allowed users"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Add User')
    
    def validate_email(self, email):
        """Custom validation for email"""
        # Check if email already in allowed list
        allowed = AllowedUser.query.filter_by(email=email.data.lower()).first()
        if allowed:
            raise ValidationError('Email already in allowed users list.')
        
        # Check if user already registered
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('User with this email already registered.')

class BulkAddUsersForm(FlaskForm):
    """Form for admin to add multiple users at once"""
    emails = TextAreaField('Email Addresses (one per line)', validators=[DataRequired()])
    submit = SubmitField('Add All Users')

class AdminUserForm(FlaskForm):
    """Form for managing existing users"""
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    action = SelectField('Action', choices=[
        ('toggle_admin', 'Toggle Admin Status'),
        ('toggle_active', 'Toggle Active Status'),
        ('delete', 'Delete User')
    ], validators=[DataRequired()])
    submit = SubmitField('Execute Action')

class DeveloperUserForm(FlaskForm):
    """Form for developers to manage user privileges"""
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    action = SelectField('Action', choices=[
        ('make_admin', 'Make Admin'),
        ('remove_admin', 'Remove Admin'),
        ('make_developer', 'Make Developer'),
        ('remove_developer', 'Remove Developer'),
        ('toggle_active', 'Toggle Active Status'),
        ('delete', 'Delete User')
    ], validators=[DataRequired()])
    submit = SubmitField('Execute Action')

class CreateAdminForm(FlaskForm):
    """Form for developers to create new admin users"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match')
    ])
    is_admin = BooleanField('Admin Privileges', default=True)
    is_developer = BooleanField('Developer Privileges', default=False)
    submit = SubmitField('Create User')
    
    def validate_email(self, email):
        """Custom validation for email"""
        # Check if user already exists
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('User with this email already exists.') 