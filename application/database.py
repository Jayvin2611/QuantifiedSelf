from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()
class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email_id = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    user_fname=db.Column(db.String, nullable=False)
    user_lname=db.Column(db.String)
    email_verified=db.Column(db.Boolean,nullable=False)

class Otp(db.Model):
    __tablename__ = "otp"
    otp_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.user_id), nullable=False)
    otp_value=db.Column(db.String, nullable=False)
    otp_time=db.Column(db.DateTime, nullable=False)

class Tracker(db.Model):
    __tablename__ = "tracker"
    tracker_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.user_id), nullable=False)
    tracker_name = db.Column(db.String, nullable=False)
    tracker_type = db.Column(db.String, nullable=False)
    tracker_description= db.Column(db.String)
    tracker_settings=db.Column(db.String)
    tracker_lastupdate=db.Column(db.DateTime)
    logs=db.relationship("Log",cascade="all,delete")



class Log(db.Model):
    __tablename__ = "log"
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tracker_id = db.Column(db.Integer, db.ForeignKey(Tracker.tracker_id,ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.user_id), nullable=False)
    log_time=db.Column(db.DateTime ,nullable=False)
    log_value=db.Column(db.String,nullable=False)
    log_note=db.Column(db.String)
