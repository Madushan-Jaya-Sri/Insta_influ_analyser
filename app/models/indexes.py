from app.models.database import db
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