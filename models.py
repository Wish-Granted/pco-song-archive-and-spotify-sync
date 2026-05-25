from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Plan(db.Model):
    __tablename__ = 'plans'
    
    plan_pco_id = db.Column(db.String(50), primary_key=True)
    plan_name = db.Column(db.String(100), nullable=True)
    plan_date = db.Column(db.DateTime, nullable=True)
    plan_series_name = db.Column(db.String(100), nullable=True)
    plan_backup_name = db.Column(db.String(100), nullable=True)
    plan_spotify_id = db.Column(db.String(50), nullable=True)

	#links songs to this plan for 'plan.songs' in the HTML
    songs = db.relationship('PlanSong', backref='plan', lazy=True, cascade="all, delete-orphan")

class PlanSong(db.Model):
    __tablename__ = 'plan_songs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_pco_id = db.Column(db.String(50), db.ForeignKey('plans.plan_pco_id'), nullable=False)
    song_pco_id = db.Column(db.String(50), nullable=False)
    song_title = db.Column(db.String(200))
    song_key = db.Column(db.String(20))
    position = db.Column(db.Integer, nullable=False)
    song_spotify_id = db.Column(db.String(50), nullable=True)
