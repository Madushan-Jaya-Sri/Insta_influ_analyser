from datetime import datetime
from app.models.database import db

class Influencer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    full_name = db.Column(db.String(120))
    profile_url = db.Column(db.String(255), nullable=False)
    followers_count = db.Column(db.Integer)
    following_count = db.Column(db.Integer)
    posts_count = db.Column(db.Integer)
    bio = db.Column(db.Text)
    is_private = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('influencers', lazy=True))
    analyses = db.relationship('Analysis', backref='influencer', lazy=True)

    def soft_delete(self):
        self.is_deleted = True
        db.session.commit()

    @staticmethod
    def get_by_username(username, user_id):
        return Influencer.query.filter_by(
            username=username,
            user_id=user_id,
            is_deleted=False
        ).first()

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)  # e.g., 'engagement', 'growth', 'content'
    results = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('analyses', lazy=True))

    def soft_delete(self):
        self.is_deleted = True
        db.session.commit()

    @staticmethod
    def get_recent_analyses(user_id, limit=10):
        return Analysis.query.filter_by(
            user_id=user_id,
            is_deleted=False
        ).order_by(Analysis.created_at.desc()).limit(limit).all()

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    theme = db.Column(db.String(20), default='light')  # 'light' or 'dark'
    notifications_enabled = db.Column(db.Boolean, default=True)
    email_notifications = db.Column(db.Boolean, default=True)
    analysis_refresh_interval = db.Column(db.Integer, default=24)  # hours
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('settings', uselist=False))

    @staticmethod
    def get_or_create(user_id):
        settings = UserSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            settings = UserSettings(user_id=user_id)
            db.session.add(settings)
            db.session.commit()
        return settings 