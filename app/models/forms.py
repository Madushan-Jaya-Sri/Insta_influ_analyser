from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, URL, ValidationError, NumberRange, Optional

class UploadForm(FlaskForm):
    """Form for uploading Instagram data files"""
    profile_file = FileField('Profile JSON File', validators=[
        FileRequired(message='Profile file is required'),
        FileAllowed(['json'], 'Only JSON files are allowed')
    ])
    posts_file = FileField('Posts JSON File', validators=[
        FileRequired(message='Posts file is required'),
        FileAllowed(['json'], 'Only JSON files are allowed')
    ])
    submit = SubmitField('Upload Files')

class URLForm(FlaskForm):
    instagram_urls = TextAreaField('Instagram Profile URLs', validators=[DataRequired()])
    max_posts = IntegerField('Maximum Posts', validators=[NumberRange(min=1, max=100)], default=20)
    time_filter = SelectField('Time Filter', 
                              choices=[
                                  ('all', 'All Time'),
                                  ('1m', 'Last Month'),
                                  ('3m', 'Last 3 Months'),
                                  ('6m', 'Last 6 Months'),
                                  ('1y', 'Last Year')
                              ], default='all')
    submit = SubmitField('Analyze')
    
    def validate_instagram_urls(self, field):
        urls = field.data.strip().split('\n')
        if not urls:
            raise ValidationError('At least one Instagram URL is required.')
        
        for url in urls:
            url = url.strip()
            if not url:
                continue
                
            if not url.startswith(('https://www.instagram.com/', 'https://instagram.com/')):
                raise ValidationError(f'Invalid Instagram URL: {url}')

class CountryForm(FlaskForm):
    """Form for setting country for each influencer"""
    submit = SubmitField('Submit Countries')
    
    # Dynamic fields will be added in the route based on the uploaded data 