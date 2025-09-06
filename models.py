from datetime import datetime
from app import db

class Note(db.Model):
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=True)  # Optional anonymous posting
    note_text = db.Column(db.Text, nullable=False)
    mood = db.Column(db.String(20), nullable=True)  # happy, sad, angry, calm, anxious, excited
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(10), default='active', nullable=False)  # active, burnt
    shared = db.Column(db.Boolean, default=False, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'note_text': self.note_text,
            'mood': self.mood,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'shared': self.shared
        }
    
    def __repr__(self):
        return f'<Note {self.id}: {self.note_text[:30]}...>'
