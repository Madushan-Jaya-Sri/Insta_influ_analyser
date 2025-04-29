from app.models.database import db, User
from app.models.models import Influencer, Analysis, UserSettings

# Create indexes for frequently queried fields
db.Index('idx_user_username', User.username)
db.Index('idx_user_email', User.email)
db.Index('idx_influencer_username', Influencer.username)
db.Index('idx_influencer_user_id', Influencer.user_id)
db.Index('idx_analysis_user_id', Analysis.user_id)
db.Index('idx_analysis_influencer_id', Analysis.influencer_id)
db.Index('idx_analysis_created_at', Analysis.created_at)
db.Index('idx_user_settings_user_id', UserSettings.user_id)

# Create indexes after table creation to improve query performance
influencer_user_idx = db.Index('idx_influencer_user', 'influencer.user_id')
influencer_username_idx = db.Index('idx_influencer_username', 'influencer.username')
influencer_updated_idx = db.Index('idx_influencer_updated', 'influencer.last_updated')

analysis_user_idx = db.Index('idx_analysis_user', 'analysis.user_id')
analysis_influencer_idx = db.Index('idx_analysis_influencer', 'analysis.influencer_id')
analysis_type_idx = db.Index('idx_analysis_type', 'analysis.analysis_type')
analysis_created_idx = db.Index('idx_analysis_created', 'analysis.created_at')

# Compound indexes for common query patterns
user_settings_idx = db.Index('idx_user_settings', 'user_settings.user_id')
user_analysis_idx = db.Index('idx_user_analysis', 'analysis.user_id', 'analysis.is_deleted')
influencer_unique_idx = db.Index('idx_influencer_unique', 'influencer.user_id', 'influencer.username', 'influencer.is_deleted') 