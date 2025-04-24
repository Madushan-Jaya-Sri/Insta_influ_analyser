from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, SelectField, PasswordField, BooleanField
from wtforms.validators import DataRequired, URL, ValidationError, NumberRange, Optional, Length, Email, EqualTo, Regexp

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

class LoginForm(FlaskForm):
    """Form for user login"""
    username = StringField('Username or Email', validators=[
        DataRequired(message='Please enter your username or email')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter your password')
    ])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """Form for user registration"""
    username = StringField('Username', validators=[
        DataRequired(message='Please enter a username'),
        Length(min=3, max=30, message='Username must be between 3 and 30 characters'),
        Regexp('^[A-Za-z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Please enter your email'),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter a password'),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register') 