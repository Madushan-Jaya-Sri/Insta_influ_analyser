import datetime
from run import db # Import db from run.py
from sqlalchemy.dialects.sqlite import JSON # Or postgresql.JSON if using PostgreSQL

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Foreign key to User model
    profile_username = db.Column(db.String(150), nullable=False)
    # Profile details
    profile_name = db.Column(db.String(255), nullable=True)
    profile_url = db.Column(db.String(255), nullable=True)
    profile_follower_count = db.Column(db.Integer, nullable=True)
    profile_post_count = db.Column(db.Integer, nullable=True)
    # Store analysis results - JSON is flexible, Text could also work
    analysis_results = db.Column(JSON) # Adjust type if using a different DB or structure
    # Analysis metadata
    analysis_complete = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text, nullable=True)
    max_posts = db.Column(db.Integer, nullable=True)
    time_filter = db.Column(db.String(20), nullable=True)
    # Relationship to images
    images = db.relationship('AnalysisImage', backref='history', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<History record {self.id} for {self.profile_username}>'
    
    @property
    def short_summary(self):
        """Return a short summary of the analysis"""
        return {
            'id': self.id,
            'username': self.profile_username,
            'followers': self.profile_follower_count,
            'posts_analyzed': self.max_posts,
            'timestamp': self.timestamp
        }

class AnalysisImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    history_id = db.Column(db.Integer, db.ForeignKey('history.id'), nullable=False)
    image_type = db.Column(db.String(20), nullable=False)  # 'profile', 'post', etc.
    image_url = db.Column(db.String(512), nullable=True)  # External URL if applicable
    image_path = db.Column(db.String(512), nullable=False)  # Local storage path
    image_data = db.Column(db.LargeBinary, nullable=True)  # Optional: store image directly in DB
    image_metadata = db.Column(JSON, nullable=True)  # Additional metadata
    
    def __repr__(self):
        return f'<AnalysisImage {self.id} of type {self.image_type} for history {self.history_id}>' 