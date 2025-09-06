from flask import request, jsonify, render_template
from app import app, db
from models import Note
import logging

@app.route('/')
def index():
    """Render the main venting wall page"""
    return render_template('index.html')

@app.route('/notes', methods=['GET'])
def get_notes():
    """Fetch all active notes"""
    try:
        notes = Note.query.filter_by(status='active').order_by(Note.timestamp.desc()).all()
        return jsonify([note.to_dict() for note in notes])
    except Exception as e:
        logging.error(f"Error fetching notes: {str(e)}")
        return jsonify({'error': 'Failed to fetch notes'}), 500

@app.route('/notes', methods=['POST'])
def create_note():
    """Add a new note"""
    try:
        data = request.get_json()
        
        if not data or not data.get('note_text'):
            return jsonify({'error': 'Note text is required'}), 400
        
        note_text = data.get('note_text').strip()
        if len(note_text) > 500:
            return jsonify({'error': 'Note text must be 500 characters or less'}), 400
        
        mood = data.get('mood', '').lower()
        valid_moods = ['happy', 'sad', 'angry', 'calm', 'anxious', 'excited']
        if mood and mood not in valid_moods:
            mood = None
        
        note = Note(
            user_id=data.get('user_id'),
            note_text=note_text,
            mood=mood
        )
        
        db.session.add(note)
        db.session.commit()
        
        logging.info(f"Created note {note.id} with mood: {mood}")
        return jsonify(note.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating note: {str(e)}")
        return jsonify({'error': 'Failed to create note'}), 500

@app.route('/notes/<int:note_id>', methods=['DELETE'])
def burn_note(note_id):
    """Burn (delete) a note"""
    try:
        note = Note.query.get_or_404(note_id)
        
        if note.status == 'burnt':
            return jsonify({'error': 'Note already burnt'}), 400
        
        # Mark as burnt instead of deleting for data integrity
        note.status = 'burnt'
        db.session.commit()
        
        logging.info(f"Burnt note {note_id}")
        return jsonify({'message': 'Note burnt successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error burning note {note_id}: {str(e)}")
        return jsonify({'error': 'Failed to burn note'}), 500

@app.route('/notes/<int:note_id>/share', methods=['POST'])
def share_note(note_id):
    """Share note with therapist/journal"""
    try:
        note = Note.query.get_or_404(note_id)
        
        if note.status == 'burnt':
            return jsonify({'error': 'Cannot share burnt note'}), 400
        
        note.shared = True
        db.session.commit()
        
        logging.info(f"Shared note {note_id}")
        return jsonify({'message': 'Note shared successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error sharing note {note_id}: {str(e)}")
        return jsonify({'error': 'Failed to share note'}), 500

@app.route('/notes/shared', methods=['GET'])
def get_shared_notes():
    """Fetch all shared notes for therapists"""
    try:
        notes = Note.query.filter_by(shared=True).order_by(Note.timestamp.desc()).all()
        return jsonify([note.to_dict() for note in notes])
    except Exception as e:
        logging.error(f"Error fetching shared notes: {str(e)}")
        return jsonify({'error': 'Failed to fetch shared notes'}), 500
