from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, ChatSession, ChatMessage, Assessment, MeditationSession, VentingPost, VentingResponse, ConsultationRequest
from gemini_service import chat_with_ai, analyze_assessment_results, suggest_assessment
from voice_service import voice_service
from utils import (hash_student_id, calculate_phq9_score, calculate_gad7_score, 
                  calculate_ghq_score, get_assessment_questions, get_assessment_options,
                  format_time_ago, get_meditation_content)
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy import func, and_

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        role = request.form['role']
        student_id = request.form.get('student_id', '')
        accommodation_type = request.form.get('accommodation_type', '')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email, full_name=full_name, role=role)
        user.set_password(password)
        
        if student_id:
            user.set_student_id(student_id)
        
        if accommodation_type:
            user.accommodation_type = accommodation_type
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.update_login_streak()
            flash(f'Welcome back! Your login streak: {user.login_streak} days', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user stats
    recent_assessments = Assessment.query.filter_by(user_id=current_user.id).order_by(Assessment.completed_at.desc()).limit(3).all()
    meditation_streak = MeditationSession.query.filter_by(user_id=current_user.id).filter(
        MeditationSession.date >= datetime.utcnow().date() - timedelta(days=7)
    ).count()
    
    # Get chat sessions with crisis flags
    crisis_sessions = ChatSession.query.filter_by(user_id=current_user.id, crisis_flag=True).count()
    
    return render_template('dashboard.html', 
                         recent_assessments=recent_assessments,
                         meditation_streak=meditation_streak,
                         crisis_sessions=crisis_sessions)

@app.route('/chatbot')
@login_required
def chatbot():
    # Get or create current chat session
    session_id = session.get('chat_session_id')
    chat_session = None
    
    if session_id:
        chat_session = ChatSession.query.get(session_id)
    
    if not chat_session:
        chat_session = ChatSession(user_id=current_user.id)
        db.session.add(chat_session)
        db.session.commit()
        session['chat_session_id'] = chat_session.id
    
    # Get chat history
    messages = ChatMessage.query.filter_by(session_id=chat_session.id).order_by(ChatMessage.timestamp).all()
    
    return render_template('chatbot.html', messages=messages, session_id=chat_session.id)

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    message = request.form['message']
    session_id = request.form['session_id']
    
    chat_session = ChatSession.query.get(session_id)
    if not chat_session or chat_session.user_id != current_user.id:
        return jsonify({'error': 'Invalid session'}), 400
    
    # Save user message
    user_msg = ChatMessage(session_id=session_id, message_type='user', content=message)
    db.session.add(user_msg)
    
    # Get chat history for context
    chat_history = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()
    history_context = [{"role": "user" if msg.message_type == "user" else "assistant", "content": msg.content} for msg in chat_history[-10:]]
    
    # Get AI response
    ai_result = chat_with_ai(message, user_context=current_user.username, chat_history=history_context)
    
    # Save bot message
    bot_msg = ChatMessage(
        session_id=session_id, 
        message_type='bot', 
        content=ai_result['response']
    )
    
    if ai_result['crisis_detected']:
        bot_msg.crisis_keywords = json.dumps(ai_result['crisis_keywords'])
        chat_session.crisis_flag = True
        chat_session.keywords_detected = json.dumps(ai_result['crisis_keywords'])
    
    db.session.add(bot_msg)
    db.session.commit()
    
    # Suggest assessment if appropriate
    assessment_suggestion = suggest_assessment(message, history_context)
    
    response = {
        'bot_message': ai_result['response'],
        'crisis_detected': ai_result['crisis_detected'],
        'assessment_suggestion': assessment_suggestion if assessment_suggestion['suggested_assessment'] != 'none' else None
    }
    
    return jsonify(response)

@app.route('/save_venting_session', methods=['POST'])
@login_required
def save_venting_session():
    try:
        data = request.get_json()
        # Create a simple meditation session record for venting activity
        venting_session = MeditationSession(
            user_id=current_user.id,
            session_type='venting',
            duration=1  # 1 minute default for venting session
        )
        
        db.session.add(venting_session)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error saving venting session: {e}")
        return jsonify({'success': False}), 500

@app.route('/track_mood', methods=['POST'])
@login_required
def track_mood():
    try:
        data = request.get_json()
        mood = data.get('mood')
        context = data.get('context', '')
        
        # Store mood as a meditation session with type 'mood'
        mood_session = MeditationSession(
            user_id=current_user.id,
            session_type=f'mood_{mood}',
            duration=1,
            date=datetime.now().date()
        )
        
        db.session.add(mood_session)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Mood tracked successfully'})
    except Exception as e:
        logging.error(f"Error tracking mood: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
@app.route('/voice_chat', methods=['POST'])
@login_required
def voice_chat():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Generate speech
    audio_path = voice_service.text_to_speech(text)
    
    if audio_path:
        return jsonify({'audio_url': f'/audio/{audio_path}'})
    else:
        return jsonify({'error': 'Failed to generate speech'}), 500

@app.route('/assessments')
@login_required
def assessments():
    user_assessments = Assessment.query.filter_by(user_id=current_user.id).order_by(Assessment.completed_at.desc()).all()
    return render_template('assessments.html', assessments=user_assessments)

@app.route('/assessment/<assessment_type>')
@login_required
def assessment_form(assessment_type):
    if assessment_type not in ['PHQ-9', 'GAD-7', 'GHQ']:
        flash('Invalid assessment type', 'error')
        return redirect(url_for('assessments'))
    
    questions = get_assessment_questions(assessment_type)
    options = get_assessment_options(assessment_type)
    
    return render_template('assessment_form.html', 
                         assessment_type=assessment_type,
                         questions=questions,
                         options=options)

@app.route('/assessment/results/<int:assessment_id>')
@login_required
def view_assessment_results(assessment_id):
    # Get the assessment
    assessment = Assessment.query.get_or_404(assessment_id)
    
    # Verify the assessment belongs to the current user
    if assessment.user_id != current_user.id:
        flash('You do not have permission to view these results', 'error')
        return redirect(url_for('assessments'))
    
    # Generate analysis based on assessment type and score
    analysis = generate_analysis(assessment.assessment_type, assessment.score)
    
    return render_template('assessment_results.html',
                         assessment=assessment,
                         analysis=analysis)

def generate_analysis(assessment_type, score):
    if assessment_type == 'PHQ-9':
        if score <= 4:
            return "Your PHQ-9 score suggests minimal or no depression. This is great news!"
        elif score <= 9:
            return "Your PHQ-9 score suggests mild depression. Consider monitoring your mood and seeking support if symptoms persist."
        elif score <= 14:
            return "Your PHQ-9 score suggests moderate depression. You may benefit from professional support."
        elif score <= 19:
            return "Your PHQ-9 score suggests moderately severe depression. We recommend seeking professional help."
        else:
            return "Your PHQ-9 score suggests severe depression. We strongly recommend seeking professional help as soon as possible."
    elif assessment_type == 'GAD-7':
        if score < 5:
            return "Your GAD-7 score suggests minimal anxiety. This is great news!"
        elif score < 10:
            return "Your GAD-7 score suggests mild anxiety. Consider monitoring your anxiety levels."
        elif score < 15:
            return "Your GAD-7 score suggests moderate anxiety. You may benefit from professional support."
        else:
            return "Your GAD-7 score suggests severe anxiety. We recommend seeking professional help."
    else:  # GHQ
        if score < 4:
            return "Your GHQ score suggests good psychological well-being."
        elif score < 12:
            return "Your GHQ score suggests some psychological distress. Consider monitoring your well-being."
        else:
            return "Your GHQ score suggests significant psychological distress. We recommend seeking professional support."

@app.route('/submit_assessment', methods=['POST'])
@login_required
def submit_assessment():
    assessment_type = request.form['assessment_type']
    responses = {}
    
    # Collect responses
    for i in range(len(get_assessment_questions(assessment_type))):
        responses[f'q{i}'] = int(request.form[f'q{i}'])
    
    # Calculate score
    if assessment_type == "PHQ-9":
        score, severity = calculate_phq9_score(responses)
    elif assessment_type == "GAD-7":
        score, severity = calculate_gad7_score(responses)
    elif assessment_type == "GHQ":
        score, severity = calculate_ghq_score(responses)
    
    # Get AI analysis
    analysis = analyze_assessment_results(assessment_type, responses, score)
    
    # Save assessment
    assessment = Assessment(
        user_id=current_user.id,
        assessment_type=assessment_type,
        responses=json.dumps(responses),
        score=score,
        severity_level=severity,
        recommendations=json.dumps(analysis)
    )
    
    db.session.add(assessment)
    db.session.commit()
    
    return render_template('assessment_results.html',
                         assessment=assessment,
                         analysis=analysis)

@app.route('/meditation')
@login_required
def meditation():
    meditation_content = get_meditation_content()

    # Calculate meditation stats for the current user
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday()) # Monday as start of week

    weekly_sessions_count = MeditationSession.query.filter_by(user_id=current_user.id).filter(
        MeditationSession.date >= start_of_week
    ).count()

    total_minutes_meditated = db.session.query(func.sum(MeditationSession.duration)).filter_by(
        user_id=current_user.id
    ).scalar() or 0 # Use .scalar() to get single result, default to 0 if None

    return render_template('meditation.html',
                           meditation_content=meditation_content,
                           weekly_sessions_count=weekly_sessions_count,
                           total_minutes_meditated=total_minutes_meditated)

@app.route('/meditation_completed', methods=['POST'])
@login_required
def meditation_completed():
    data = request.get_json()
    duration = data.get('duration', 0) # Duration in seconds
    session_type = data.get('session_type', 'meditation')

    if duration <= 0:
        return jsonify({"success": False, "message": "Invalid duration"}), 400

    meditation_session = MeditationSession(
        user_id=current_user.id,
        session_type=session_type,
        duration=duration,
        date=datetime.utcnow().date() # Record the date of completion
    )

    db.session.add(meditation_session)
    db.session.commit()

    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())

    # Weekly count (from start of week)
    weekly_count = MeditationSession.query.filter_by(user_id=current_user.id).filter(
        MeditationSession.date >= start_of_week
    ).count()

    # Today's sessions (for progress)
    today_sessions = MeditationSession.query.filter_by(user_id=current_user.id, date=today).all()
    today_sessions_count = len(today_sessions)

    return jsonify({
        "success": True,
        "message": "Meditation session recorded",
        "session": {
            "type": session_type,
            "duration": duration
        },
        "weekly_sessions": weekly_count,
        "today_sessions_count": today_sessions_count
    })

@app.route('/venting_room')
@login_required
def venting_room():
    return render_template('venting_room.html')

@app.route('/venting_hall')
@login_required
def venting_hall():
    posts = VentingPost.query.order_by(VentingPost.created_at.desc()).all()
    
    return render_template('venting_hall.html', posts=posts, format_time_ago=format_time_ago)

@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    content = request.form['content']
    anonymous = 'anonymous' in request.form
    
    if not content.strip():
        flash('Post content cannot be empty', 'error')
        return redirect(url_for('venting_hall'))
    
    post = VentingPost(
        user_id=current_user.id,
        content=content,
        anonymous=anonymous
    )
    
    db.session.add(post)
    db.session.commit()
    
    flash('Your post has been shared', 'success')
    return redirect(url_for('venting_hall'))

@app.route('/respond_to_post', methods=['POST'])
@login_required
def respond_to_post():
    post_id = int(request.form['post_id'])
    content = request.form['content']
    anonymous = 'anonymous' in request.form
    
    if not content.strip():
        flash('Response cannot be empty', 'error')
        return redirect(url_for('venting_hall'))
    
    response = VentingResponse(
        post_id=post_id,
        user_id=current_user.id,
        content=content,
        anonymous=anonymous
    )
    
    db.session.add(response)
    db.session.commit()
    
    flash('Your response has been added', 'success')
    return redirect(url_for('venting_hall'))

@app.route('/like_post', methods=['POST'])
@login_required
def like_post():
    post_id = int(request.form['post_id'])
    post = VentingPost.query.get(post_id)
    
    if post:
        post.likes += 1
        db.session.commit()
    
    return redirect(url_for('venting_hall'))

@app.route('/consultation')
@login_required
def consultation():
    user_requests = ConsultationRequest.query.filter_by(user_id=current_user.id).order_by(ConsultationRequest.created_at.desc()).all()
    return render_template('consultation.html', requests=user_requests)

@app.route('/request_consultation', methods=['POST'])
@login_required
def request_consultation():
    urgency = request.form['urgency']
    preferred_time = request.form['preferred_time']
    contact_preference = request.form['contact_preference']
    notes = request.form.get('notes', '')
    
    consultation = ConsultationRequest(
        user_id=current_user.id,
        urgency_level=urgency,
        preferred_time=preferred_time,
        contact_preference=contact_preference,
        additional_notes=notes
    )
    
    db.session.add(consultation)
    db.session.commit()
    
    flash('Your consultation request has been submitted. A mental health professional will contact you soon.', 'success')
    return redirect(url_for('consultation'))

@app.route('/mentor_dashboard')
@login_required
def mentor_dashboard():
    if current_user.role not in ['teacher', 'admin']:
        flash('Access denied. This page is for mentors only.', 'error')
        return redirect(url_for('dashboard'))
    
    # Analytics for mentors
    total_students = User.query.filter_by(role='student').count()
    
    # Students by accommodation type
    hostel_students = User.query.filter_by(role='student', accommodation_type='hostel').count()
    local_students = User.query.filter_by(role='student', accommodation_type='local').count()
    
    # Recent assessments statistics
    recent_assessments = db.session.query(
        Assessment.assessment_type,
        Assessment.severity_level,
        func.count(Assessment.id).label('count')
    ).filter(
        Assessment.completed_at >= datetime.utcnow() - timedelta(days=30)
    ).group_by(Assessment.assessment_type, Assessment.severity_level).all()
    
    # Crisis flags in the last 30 days
    crisis_sessions = ChatSession.query.filter(
        and_(ChatSession.crisis_flag == True,
             ChatSession.session_start >= datetime.utcnow() - timedelta(days=30))
    ).count()
    
    # Login streaks
    active_users = User.query.filter(
        and_(User.role == 'student',
             User.last_streak_date >= datetime.utcnow().date() - timedelta(days=7))
    ).count()
    
    # Stress level comparison
    hostel_stress = db.session.query(func.avg(Assessment.score)).filter(
        and_(Assessment.assessment_type == 'PHQ-9',
             Assessment.user_id.in_(
                 db.session.query(User.id).filter_by(accommodation_type='hostel')
             ))
    ).scalar() or 0
    
    local_stress = db.session.query(func.avg(Assessment.score)).filter(
        and_(Assessment.assessment_type == 'PHQ-9',
             Assessment.user_id.in_(
                 db.session.query(User.id).filter_by(accommodation_type='local')
             ))
    ).scalar() or 0
    
    stats = {
        'total_students': total_students,
        'hostel_students': hostel_students,
        'local_students': local_students,
        'recent_assessments': recent_assessments,
        'crisis_sessions': crisis_sessions,
        'active_users': active_users,
        'hostel_avg_stress': round(hostel_stress, 2),
        'local_avg_stress': round(local_stress, 2)
    }
    
    return render_template('mentor_dashboard.html', stats=stats)

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
