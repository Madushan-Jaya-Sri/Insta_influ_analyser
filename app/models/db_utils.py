from app.models.database import db
from app.models.models import Influencer, Analysis, UserSettings
from datetime import datetime, timedelta
import json

def get_user_influencers(user_id, limit=None, offset=0):
    """Get all influencers for a user with pagination"""
    query = Influencer.query.filter_by(
        user_id=user_id,
        is_deleted=False
    ).order_by(Influencer.last_updated.desc())
    
    if limit is not None:
        query = query.limit(limit).offset(offset)
    
    return query.all()

def get_influencer_analyses(influencer_id, analysis_type=None, limit=10):
    """Get recent analyses for an influencer"""
    query = Analysis.query.filter_by(
        influencer_id=influencer_id,
        is_deleted=False
    )
    
    if analysis_type:
        query = query.filter_by(analysis_type=analysis_type)
    
    return query.order_by(Analysis.created_at.desc()).limit(limit).all()

def save_analysis(user_id, influencer_id, analysis_type, results):
    """Save analysis results"""
    try:
        analysis = Analysis(
            user_id=user_id,
            influencer_id=influencer_id,
            analysis_type=analysis_type,
            results=results
        )
        db.session.add(analysis)
        db.session.commit()
        return analysis
    except Exception as e:
        db.session.rollback()
        raise

def update_influencer_data(user_id, username, data):
    """Update or create influencer data"""
    try:
        influencer = Influencer.get_by_username(username, user_id)
        if not influencer:
            influencer = Influencer(
                user_id=user_id,
                username=username,
                profile_url=f"https://instagram.com/{username}"
            )
        
        # Update influencer data
        influencer.full_name = data.get('full_name')
        influencer.followers_count = data.get('followers_count')
        influencer.following_count = data.get('following_count')
        influencer.posts_count = data.get('posts_count')
        influencer.bio = data.get('bio')
        influencer.is_private = data.get('is_private', False)
        influencer.last_updated = datetime.utcnow()
        
        if not influencer.id:
            db.session.add(influencer)
        
        db.session.commit()
        return influencer
    except Exception as e:
        db.session.rollback()
        raise

def cleanup_old_data(days=30):
    """Clean up old analyses and soft-deleted records"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Soft delete old analyses
        Analysis.query.filter(
            Analysis.created_at < cutoff_date,
            Analysis.is_deleted == False
        ).update({'is_deleted': True})
        
        # Permanently delete soft-deleted records older than cutoff
        Analysis.query.filter(
            Analysis.is_deleted == True,
            Analysis.created_at < cutoff_date
        ).delete()
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise

def get_user_settings(user_id):
    """Get user settings, creating default if not exists"""
    return UserSettings.get_or_create(user_id)

def update_user_settings(user_id, **kwargs):
    """Update user settings"""
    try:
        settings = UserSettings.get_or_create(user_id)
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        db.session.commit()
        return settings
    except Exception as e:
        db.session.rollback()
        raise 