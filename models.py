from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Plan(db.Model):
    __tablename__ = 'plans'
    
    plan_id = db.Column(db.String(50), primary_key=True)
    plan_name = db.Column(db.String(100), nullable=True)
    plan_date = db.Column(db.DateTime, nullable=True)

class PlanSong(db.Model):
    __tablename__ = 'plan_songs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_id = db.Column(db.String(50), db.ForeignKey('plans.plan_id'), nullable=False)
    song_id = db.Column(db.String(50), nullable=False)
    song_title = db.Column(db.String(200))
    song_key = db.Column(db.String(20))
    position = db.Column(db.Integer, nullable=False)
