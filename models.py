from datetime import datetime, timedelta
from app import db
from datetime import datetime, timedelta

class RoutineTask(db.Model):
    __tablename__ = 'routine_tasks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)  # HH:MM
    end_time = db.Column(db.String(5), nullable=False)    # HH:MM
    notes = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')  # pending, completed, skipped
    created_date = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='routine_tasks')

    def duration_minutes(self):
        try:
            start_h, start_m = map(int, self.start_time.split(':'))
            end_h, end_m = map(int, self.end_time.split(':'))
            return (end_h * 60 + end_m) - (start_h * 60 + start_m)
        except Exception:
            return 0

    def as_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'notes': self.notes,
            'status': self.status,
            'created_date': self.created_date,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import json

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # student, teacher, admin
    full_name = db.Column(db.String(100), nullable=False)
    student_id_hash = db.Column(db.String(64))  # Hashed student ID for privacy
    accommodation_type = db.Column(db.String(20))  # hostel, local
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    login_streak = db.Column(db.Integer, default=0)
    last_streak_date = db.Column(db.Date)
    
    # Relationships
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True, cascade='all, delete-orphan')
    assessments = db.relationship('Assessment', backref='user', lazy=True, cascade='all, delete-orphan')
    meditation_sessions = db.relationship('MeditationSession', backref='user', lazy=True, cascade='all, delete-orphan')
    venting_posts = db.relationship('VentingPost', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def set_student_id(self, student_id):
        # Hash student ID for privacy
        self.student_id_hash = hashlib.sha256(str(student_id).encode()).hexdigest()
    
    def update_login_streak(self):
        today = datetime.utcnow().date()
        if self.last_streak_date:
            if self.last_streak_date == today:
                return  # Already updated today
            elif self.last_streak_date == today - timedelta(days=1):
                self.login_streak += 1
            else:
                self.login_streak = 1
        else:
            self.login_streak = 1
        
        self.last_streak_date = today
        self.last_login = datetime.utcnow()
        db.session.commit()

class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_start = db.Column(db.DateTime, default=datetime.utcnow)
    session_end = db.Column(db.DateTime)
    crisis_flag = db.Column(db.Boolean, default=False)
    keywords_detected = db.Column(db.Text)  # JSON string of detected keywords
    
    # Relationship
    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade='all, delete-orphan')

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    message_type = db.Column(db.String(10), nullable=False)  # user, bot
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    crisis_keywords = db.Column(db.Text)  # JSON string of crisis keywords in this message

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assessment_type = db.Column(db.String(10), nullable=False)  # PHQ-9, GAD-7, GHQ
    responses = db.Column(db.Text, nullable=False)  # JSON string of responses
    score = db.Column(db.Integer, nullable=False)
    severity_level = db.Column(db.String(20), nullable=False)
    recommendations = db.Column(db.Text)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

class MeditationSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_type = db.Column(db.String(20), nullable=False)  # meditation, music
    duration = db.Column(db.Integer)  # in minutes
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    date = db.Column(db.Date, default=datetime.utcnow().date)

class VentingPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    anonymous = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.Column(db.Integer, default=0)
    
    # Relationship
    responses = db.relationship('VentingResponse', backref='post', lazy=True, cascade='all, delete-orphan')

class VentingResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('venting_post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    anonymous = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='venting_responses')

class ConsultationRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    urgency_level = db.Column(db.String(10), nullable=False)  # low, medium, high
    preferred_time = db.Column(db.String(50))
    contact_preference = db.Column(db.String(20))  # phone, email, video
    additional_notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, scheduled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='consultation_requests')

class RoutineTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.String(5), nullable=False) # HH:MM
    end_time = db.Column(db.String(5), nullable=False)   # HH:MM
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending') # pending, completed, skipped
    created_date = db.Column(db.Date, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='routine_tasks')

    def __repr__(self):
        return f"<RoutineTask {self.id}: {self.title} ({self.start_time}-{self.end_time})>"

