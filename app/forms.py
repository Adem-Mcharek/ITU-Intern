"""
Forms for WebTV Processing App
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, URLField, SubmitField, SelectField
from wtforms.validators import DataRequired, URL, Length, Optional

class UrlForm(FlaskForm):
    """Form for submitting UN WebTV URLs for processing"""
    url = URLField(
        'UN WebTV URL', 
        validators=[DataRequired(), URL()],
        description='Paste the full URL from UN WebTV (e.g., https://webtv.un.org/watch/...)'
    )
    title = StringField(
        'Meeting Title', 
        validators=[DataRequired(), Length(min=3, max=256)],
        description='Enter a descriptive title for this meeting'
    )
    submit = SubmitField('Process Video')

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