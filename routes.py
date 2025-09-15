from flask import render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, ChatSession, ChatMessage, Assessment, MeditationSession, VentingPost, VentingResponse, ConsultationRequest, AvailabilitySlot, SoundVentingSession
from gemini_service import chat_with_ai, analyze_assessment_results, suggest_assessment
from voice_service import voice_service
from utils import (hash_student_id, calculate_phq9_score, calculate_gad7_score, 
                  calculate_ghq_score, get_assessment_questions, get_assessment_options,
                  format_time_ago, get_meditation_content)
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy import func, and_, case
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image
import io
import os

# Email helper
import smtplib
import ssl
from email.message import EmailMessage

@app.route('/set_language/<language>')
def set_language(language=None):
    """Set the language for the current session"""
    if language and language in app.config['LANGUAGES']:
        session['language'] = language
    return redirect(request.referrer or url_for('dashboard'))

def send_email(subject: str, body: str, to_email: str, sender_type: str = 'user') -> bool:
    """Send email using environment SMTP settings; fallback to logging. Sender type can be 'user', 'mentor', or 'counsellor'."""
    try:
        smtp_host = os.environ.get('SMTP_HOST')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_user = os.environ.get('SMTP_USER')
        smtp_pass = os.environ.get('SMTP_PASS')
        # Set sender email based on type
        if sender_type == 'mentor':
            from_email = os.environ.get('MENTOR_EMAIL', smtp_user)
        elif sender_type == 'counsellor':
            from_email = os.environ.get('COUNSELLOR_EMAIL', smtp_user)
        else:
            from_email = os.environ.get('SMTP_FROM', smtp_user)
        if not (smtp_host and smtp_user and smtp_pass and to_email):
            app.logger.info(f"EMAIL (stub) to {to_email}: {subject} | {body}")
            return False
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        msg.set_content(body)
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        app.logger.warning(f"EMAIL send failed to {to_email}: {e}. Falling back to log. Subject: {subject}")
        app.logger.info(f"EMAIL (stub) to {to_email}: {subject} | {body}")
        return False

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

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
            # Role-based landing
            if user.role == 'counsellor':
                return redirect(url_for('counsellor_dashboard'))
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            if user.role in ['teacher']:
                return redirect(url_for('mentor_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Redirect counsellors to their dedicated dashboard
    if getattr(current_user, 'role', None) == 'counsellor':
        return redirect(url_for('counsellor_dashboard'))
    # Get today's tasks for current user
    from models import RoutineTask
    today = datetime.utcnow().date()
    tasks_today = RoutineTask.query.filter_by(user_id=current_user.id, created_date=today).all()
    total_tasks = len(tasks_today)
    tasks_completed = sum(1 for t in tasks_today if t.status == 'completed')
    tasks_progress = int((tasks_completed / total_tasks) * 100) if total_tasks > 0 else 0
    # Get user stats
    recent_assessments = Assessment.query.filter_by(user_id=current_user.id).order_by(Assessment.completed_at.desc()).limit(3).all()
    meditation_streak = MeditationSession.query.filter_by(user_id=current_user.id).filter(
        MeditationSession.date >= datetime.utcnow().date() - timedelta(days=7)
    ).count()

    # Weekly sessions count (from start of week)
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())
    weekly_sessions_count = MeditationSession.query.filter_by(user_id=current_user.id).filter(
        MeditationSession.date >= start_of_week
    ).count()

    # Total seconds meditated
    total_seconds = db.session.query(func.sum(MeditationSession.duration)).filter_by(
        user_id=current_user.id
    ).scalar() or 0
    total_minutes_meditated = total_seconds // 60

    # Get chat sessions with crisis flags
    crisis_sessions = ChatSession.query.filter_by(user_id=current_user.id, crisis_flag=True).count()

    return render_template('dashboard.html', 
                         recent_assessments=recent_assessments,
                         meditation_streak=meditation_streak,
                         crisis_sessions=crisis_sessions,
                         weekly_sessions_count=weekly_sessions_count,
                         total_minutes_meditated=total_minutes_meditated,
                         tasks_completed=tasks_completed,
                         total_tasks=total_tasks,
                         tasks_progress=tasks_progress,
                         login_streak=current_user.login_streak or 0)

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
        
        # Check if it's a sound venting session with decibel data
        if 'max_decibel' in data:
            # Sound venting session
            duration = data.get('duration', 0)
            max_decibel = data.get('max_decibel', 0)
            avg_decibel = data.get('avg_decibel', 0)
            scream_count = data.get('scream_count', 0)
            session_type = data.get('session_type', 'sound_venting')
            
            session = SoundVentingSession(
                user_id=current_user.id,
                duration=duration,
                max_decibel=max_decibel,
                avg_decibel=avg_decibel,
                scream_count=scream_count,
                session_type=session_type
            )
            
            db.session.add(session)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Sound venting session saved successfully',
                'duration': duration,
                'max_decibel': max_decibel
            })
        else:
            # Regular text venting session
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
        return jsonify({'success': False, 'error': str(e)}), 500

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

@app.route('/assessment_results/<int:assessment_id>')
@login_required
def assessment_results(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    counsellors = User.query.filter_by(role='counsellor').all()
    # Permission check (example: only owner or counsellor can view)
    if assessment.user_id != current_user.id and current_user.role != 'counsellor':
        flash('You do not have permission to view these results', 'error')
        return redirect(url_for('assessments'))  
    if assessment.recommendations:
        try:
            analysis = json.loads(assessment.recommendations)
        except Exception:
            analysis = generate_analysis(assessment.assessment_type, assessment.score)
    else:
        analysis = generate_analysis(assessment.assessment_type, assessment.score)
    return render_template('assessment_results.html',
                         assessment=assessment,
                         analysis=analysis,
                         counsellors=counsellors)

def generate_analysis(assessment_type, score):
    if assessment_type == 'PHQ-9':
        if score <= 4:
            return {
                "interpretation": "Your PHQ-9 score of {} indicates minimal or no depression symptoms, which is excellent news! This suggests you're currently managing your mental health well and experiencing few or no significant depressive symptoms. This low score reflects good emotional regulation and psychological well-being.".format(score),
                "recommendations": [
                    "Continue maintaining your current healthy lifestyle and mental health practices",
                    "Keep up with regular self-care activities that bring you joy and relaxation",
                    "Maintain strong social connections and support networks",
                    "Practice preventive mental health care through regular check-ins with yourself",
                    "Consider sharing your successful coping strategies with others who might benefit",
                    "Stay aware of any changes in your mood or stress levels for early intervention"
                ],
                "coping_strategies": [
                    "Continue regular physical exercise - aim for at least 30 minutes of activity most days",
                    "Maintain a consistent sleep schedule with 7-9 hours of quality sleep nightly",
                    "Practice daily mindfulness, meditation, or deep breathing exercises",
                    "Engage in hobbies and activities that bring you fulfillment and purpose",
                    "Keep a gratitude journal to reinforce positive thinking patterns",
                    "Stay connected with friends and family through regular communication",
                    "Practice stress management techniques before challenging situations arise",
                    "Maintain a balanced diet rich in nutrients that support brain health"
                ],
                "detailed_breakdown": {
                    "score_range": "0-4 points",
                    "severity_category": "Minimal Depression",
                    "key_insights": [
                        "You demonstrate strong emotional resilience and coping abilities",
                        "Your current mental health practices are serving you well",
                        "You're likely experiencing good quality of life and functioning",
                        "This score suggests protective factors are working effectively"
                    ],
                    "warning_signs": [
                        "Sudden changes in sleep patterns or appetite",
                        "Increased irritability or mood swings",
                        "Loss of interest in previously enjoyable activities",
                        "Persistent feelings of sadness lasting more than two weeks"
                    ]
                },
                "professional_help_recommended": False,
                "urgency_level": "low"
            }
        elif score <= 9:
            return {
                "interpretation": "Your PHQ-9 score of {} indicates mild depression symptoms. While this suggests some challenges with mood, it's encouraging that you're seeking support and taking steps to understand your mental health. Mild depression is very treatable, and with the right strategies and support, you can feel significantly better.".format(score),
                "recommendations": [
                    "Track your mood daily using a journal or mood tracking app to identify patterns",
                    "Consider scheduling a consultation with a licensed mental health counselor or therapist",
                    "Engage in regular physical activity - even 20-30 minutes of walking can make a difference",
                    "Establish a consistent daily routine to provide structure and stability",
                    "Prioritize activities that previously brought you joy, even if they don't feel appealing right now",
                    "Practice good sleep hygiene and aim for consistent sleep/wake times",
                    "Consider joining a support group or online community for peer support",
                    "Limit alcohol consumption and avoid substances that can worsen depression"
                ],
                "coping_strategies": [
                    "Practice progressive muscle relaxation and deep breathing exercises for stress reduction",
                    "Maintain regular social activities, even when you don't feel like socializing",
                    "Focus on nutrient-rich foods including omega-3 fatty acids, complex carbs, and lean proteins",
                    "Try the '5-4-3-2-1' grounding technique when feeling overwhelmed",
                    "Engage in creative activities like art, music, or writing for emotional expression",
                    "Set small, achievable daily goals to build momentum and sense of accomplishment",
                    "Practice mindful movement like yoga or tai chi",
                    "Spend time in nature when possible, as outdoor exposure can boost mood"
                ],
                "detailed_breakdown": {
                    "score_range": "5-9 points",
                    "severity_category": "Mild Depression",
                    "key_insights": [
                        "You may experience low mood, reduced energy, or changes in sleep/appetite",
                        "Symptoms are noticeable but don't severely impair daily functioning",
                        "Early intervention can prevent progression to more severe depression",
                        "Many people with mild depression respond well to lifestyle changes and therapy"
                    ],
                    "warning_signs": [
                        "Symptoms persisting for more than 2 weeks without improvement",
                        "Increasing difficulty with work, school, or relationship responsibilities",
                        "Thoughts of self-harm or worthlessness",
                        "Complete loss of interest in all previously enjoyable activities"
                    ]
                },
                "professional_help_recommended": True,
                "urgency_level": "low"
            }
        elif score <= 14:
            return {
                "interpretation": "Your PHQ-9 score of {} indicates moderate depression symptoms. This level suggests that depression is having a noticeable impact on your daily life and functioning. The good news is that moderate depression is highly treatable with professional support, and many people see significant improvement with the right treatment approach.".format(score),
                "recommendations": [
                    "Schedule an appointment with a licensed mental health professional within the next 1-2 weeks",
                    "Consider cognitive-behavioral therapy (CBT) or other evidence-based therapeutic approaches",
                    "Discuss your symptoms with your primary healthcare provider to rule out medical causes",
                    "Create a structured daily routine with regular sleep, meals, and activities",
                    "Ask trusted friends or family members for additional support during this time",
                    "Consider joining a depression support group or online community",
                    "Keep a mood diary to track symptoms and identify triggers",
                    "Discuss medication options with a psychiatrist if therapy alone isn't sufficient"
                ],
                "coping_strategies": [
                    "Develop and maintain a consistent daily routine, even when motivation is low",
                    "Practice progressive muscle relaxation and guided meditation for 10-20 minutes daily",
                    "Stay connected with your support system - reach out even when you don't feel like it",
                    "Break large tasks into smaller, manageable steps to avoid feeling overwhelmed",
                    "Engage in 'behavioral activation' - do activities that used to bring joy, even if they don't feel appealing",
                    "Practice the 'STOP' technique: Stop, Take a breath, Observe your thoughts, Proceed mindfully",
                    "Use the '3-3-3 rule' when anxious: name 3 things you see, 3 sounds you hear, move 3 parts of your body",
                    "Focus on basic self-care: regular showers, nutritious meals, and adequate sleep",
                    "Limit news consumption and social media if they increase negative feelings",
                    "Try light therapy, especially during winter months or if you spend lots of time indoors"
                ],
                "detailed_breakdown": {
                    "score_range": "10-14 points",
                    "severity_category": "Moderate Depression",
                    "key_insights": [
                        "Depression symptoms are significantly impacting your daily functioning and quality of life",
                        "You may experience persistent low mood, fatigue, difficulty concentrating, or changes in sleep/appetite",
                        "This level typically requires professional intervention for optimal recovery",
                        "With proper treatment, most people with moderate depression see substantial improvement within 6-12 weeks",
                        "Combination therapy (counseling + lifestyle changes) often shows the best outcomes"
                    ],
                    "warning_signs": [
                        "Symptoms worsening rapidly or lasting more than 2 weeks without any improvement",
                        "Increasing thoughts of self-harm, suicide, or feeling that life isn't worth living",
                        "Complete inability to function at work, school, or in relationships",
                        "Significant changes in eating patterns (eating much more or much less than usual)",
                        "Sleeping much more or much less than normal for extended periods",
                        "Increased use of alcohol or drugs to cope with feelings"
                    ]
                },
                "professional_help_recommended": True,
                "urgency_level": "medium"
            }
        elif score <= 19:
            return {
                "interpretation": "Your PHQ-9 score suggests moderately severe depression. We recommend seeking professional help.",
                "recommendations": [
                    "Seek immediate professional help",
                    "Consider medication evaluation",
                    "Regular therapy sessions recommended"
                ],
                "coping_strategies": [
                    "Focus on basic self-care",
                    "Reach out to trusted friends/family",
                    "Practice grounding techniques"
                ],
                "professional_help_recommended": True,
                "urgency_level": "high"
            }
        else:
            return {
                "interpretation": "Your PHQ-9 score suggests severe depression. We strongly recommend seeking professional help as soon as possible.",
                "recommendations": [
                    "Seek immediate professional help",
                    "Contact crisis helpline if needed",
                    "Consider emergency support"
                ],
                "coping_strategies": [
                    "Prioritize safety and basic needs",
                    "Stay with trusted support person",
                    "Use crisis resources when needed"
                ],
                "professional_help_recommended": True,
                "urgency_level": "high"
            }
    elif assessment_type == 'GAD-7':
        if score < 5:
            return {
                "interpretation": "Your GAD-7 score suggests minimal anxiety. This is great news!",
                "recommendations": [
                    "Continue current coping strategies",
                    "Maintain healthy stress management",
                    "Practice preventive self-care"
                ],
                "coping_strategies": [
                    "Regular relaxation exercises",
                    "Maintain work-life balance",
                    "Practice deep breathing"
                ],
                "professional_help_recommended": False,
                "urgency_level": "low"
            }
        elif score < 10:
            return {
                "interpretation": "Your GAD-7 score suggests mild anxiety. Consider monitoring your anxiety levels.",
                "recommendations": [
                    "Track anxiety triggers",
                    "Learn stress management techniques",
                    "Consider counseling if persistent"
                ],
                "coping_strategies": [
                    "Practice mindfulness meditation",
                    "Regular physical exercise",
                    "Limit caffeine intake"
                ],
                "professional_help_recommended": True,
                "urgency_level": "low"
            }
        elif score < 15:
            return {
                "interpretation": "Your GAD-7 score suggests moderate anxiety. You may benefit from professional support.",
                "recommendations": [
                    "Seek professional counseling",
                    "Consider anxiety management therapy",
                    "Discuss with healthcare provider"
                ],
                "coping_strategies": [
                    "Practice progressive muscle relaxation",
                    "Use grounding techniques",
                    "Maintain regular sleep schedule"
                ],
                "professional_help_recommended": True,
                "urgency_level": "medium"
            }
        else:
            return {
                "interpretation": "Your GAD-7 score suggests severe anxiety. We recommend seeking professional help.",
                "recommendations": [
                    "Seek immediate professional help",
                    "Consider medication evaluation",
                    "Regular therapy sessions"
                ],
                "coping_strategies": [
                    "Focus on breathing exercises",
                    "Use crisis coping techniques",
                    "Stay connected with support system"
                ],
                "professional_help_recommended": True,
                "urgency_level": "high"
            }
    else:  # GHQ
        if score < 4:
            return {
                "interpretation": "Your GHQ score suggests good psychological well-being.",
                "recommendations": [
                    "Continue healthy lifestyle",
                    "Maintain current wellness practices",
                    "Regular self-assessment"
                ],
                "coping_strategies": [
                    "Keep balanced lifestyle",
                    "Regular social activities",
                    "Stress prevention techniques"
                ],
                "professional_help_recommended": False,
                "urgency_level": "low"
            }
        elif score < 12:
            return {
                "interpretation": "Your GHQ score suggests some psychological distress. Consider monitoring your well-being.",
                "recommendations": [
                    "Monitor stress levels",
                    "Consider counseling support",
                    "Practice self-care activities"
                ],
                "coping_strategies": [
                    "Regular exercise routine",
                    "Mindfulness practices",
                    "Social support engagement"
                ],
                "professional_help_recommended": True,
                "urgency_level": "medium"
            }
        else:
            return {
                "interpretation": "Your GHQ score suggests significant psychological distress. We recommend seeking professional support.",
                "recommendations": [
                    "Seek professional counseling",
                    "Consider comprehensive assessment",
                    "Regular mental health check-ins"
                ],
                "coping_strategies": [
                    "Focus on stress reduction",
                    "Practice relaxation techniques",
                    "Build strong support network"
                ],
                "professional_help_recommended": True,
                "urgency_level": "high"
            }

@app.route('/submit_assessment', methods=['POST'])
@login_required
def submit_assessment():
    try:
        assessment_type = request.form['assessment_type']
        print(f"Debug: Assessment type: {assessment_type}")
        
        responses = {}
        for i in range(len(get_assessment_questions(assessment_type))):
            responses[f'q{i}'] = int(request.form[f'q{i}'])
        print(f"Debug: Responses: {responses}")
        
        if assessment_type == "PHQ-9":
            score, severity = calculate_phq9_score(responses)
        elif assessment_type == "GAD-7":
            score, severity = calculate_gad7_score(responses)
        elif assessment_type == "GHQ":
            score, severity = calculate_ghq_score(responses)
        
        print(f"Debug: Score: {score}, Severity: {severity}")
        
        # Try to get analysis from Gemini
        try:
            analysis = analyze_assessment_results(assessment_type, responses, score)
            print(f"Debug: Analysis successful: {type(analysis)}")
        except Exception as e:
            print(f"Debug: Analysis failed: {e}")
            # Fallback analysis
            analysis = {
                "interpretation": f"Your {assessment_type} score is {score}, indicating {severity.lower()} symptoms.",
                "recommendations": [
                    "Consider speaking with a mental health professional",
                    "Practice regular self-care activities",
                    "Maintain social connections"
                ],
                "coping_strategies": [
                    "Practice deep breathing exercises",
                    "Maintain regular sleep schedule",
                    "Engage in physical activity"
                ],
                "professional_help_recommended": score > 9,
                "urgency_level": "medium" if score > 14 else "low"
            }
        
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
        print(f"Debug: Assessment saved with ID: {assessment.id}")
        
        counsellors = User.query.filter_by(role='counsellor').all()
        return render_template('assessment_results.html',
                             assessment=assessment,
                             analysis=analysis,
                             counsellors=counsellors)
                             
    except Exception as e:
        print(f"Debug: Error in submit_assessment: {e}")
        flash(f'Error processing assessment: {str(e)}', 'error')
        return redirect(url_for('assessments'))

@app.route('/resources')
@login_required
def resources():
    """Mental Health Resources page with coping strategies and self-help content"""
    return render_template('resources.html')

@app.route('/vr_meditation')
@login_required
def vr_meditation():
    """VR Meditation experience using A-Frame"""
    return render_template('vr_meditation.html')

@app.route('/ar_breathing')
@login_required
def ar_breathing():
    """AR Breathing exercises for anxiety relief"""
    return render_template('ar_breathing.html')

@app.route('/save_breathing_session', methods=['POST'])
@login_required
def save_breathing_session():
    """Save AR breathing session data"""
    try:
        data = request.get_json()
        duration = data.get('duration', 0)
        pattern = data.get('pattern', 'Unknown')
        session_type = data.get('session_type', 'breathing')
        
        # Save as meditation session with special type
        session = MeditationSession(
            user_id=current_user.id,
            duration=duration,
            date=datetime.utcnow().date(),
            session_type=session_type
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{pattern} session saved successfully',
            'duration': duration
        })
        
    except Exception as e:
        print(f"Error saving breathing session: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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

    total_seconds = db.session.query(func.sum(MeditationSession.duration)).filter_by(
        user_id=current_user.id
    ).scalar() or 0

    total_minutes_meditated = total_seconds // 60   # or round(total_seconds / 60, 1)


    return render_template('meditation.html',
                           meditation_content=meditation_content,
                           weekly_sessions_count=weekly_sessions_count,
                           total_minutes_meditated=total_minutes_meditated)

@app.route('/meditation_completed', methods=['POST'])
@login_required
def meditation_completed():
    data = request.get_json()
    duration_seconds = int(data.get('duration', 0)) # Duration in seconds
    session_type = data.get('session_type', 'meditation')
    if duration_seconds <= 0:
        return jsonify({"success": False, "message": "Invalid duration"}), 400
    meditation_session = MeditationSession(
        user_id=current_user.id,
        session_type=session_type,
        duration=duration_seconds, # Store duration in seconds
        date=datetime.utcnow().date() # Record the date of completion
    )
    db.session.add(meditation_session)
    db.session.commit()
    # Notify user about successful meditation (optional encouragement)
    try:
        send_email(
            subject='Meditation completed',
            body=f'Great job! You completed a {duration_seconds//60} minute {session_type} session today. Keep your streak going!',
            to_email=current_user.email
        )
    except Exception:
        pass
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())
    weekly_count = MeditationSession.query.filter_by(user_id=current_user.id).filter(
        MeditationSession.date >= start_of_week
    ).count()
    today_sessions = MeditationSession.query.filter_by(user_id=current_user.id, date=today).all()
    today_sessions_count = len(today_sessions)
    return jsonify({
        "success": True,
        "message": "Meditation session recorded",
        "session": {
            "type": session_type,
            "duration": duration_seconds
        },
        "weekly_sessions": weekly_count,
        "today_sessions_count": today_sessions_count
    })

@app.route('/venting_room')
@login_required
def venting_room():
    return render_template('venting_room.html')

@app.route('/sound_venting')
@login_required
def sound_venting():
    """Sound Venting Room with decibel tracking"""
    # Get user's previous venting sessions count
    venting_sessions = VentingPost.query.filter_by(user_id=current_user.id).count()
    return render_template('sound_venting.html', venting_sessions=venting_sessions)

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

@app.route('/delete_post/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    post = VentingPost.query.get(post_id)
    if not post:
        return jsonify({'success': False, 'error': 'Post not found'}), 404

    # Only allow the author or an admin
    if post.user_id != current_user.id and not getattr(current_user, 'is_admin', False):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    # Delete associated responses too
    VentingResponse.query.filter_by(post_id=post.id).delete()
    db.session.delete(post)
    db.session.commit()

    return jsonify({'success': True}), 200


@app.route('/delete_response/<int:response_id>', methods=['DELETE'])
@login_required
def delete_response(response_id):
    response = VentingResponse.query.get(response_id)
    if not response:
        return jsonify({'success': False, 'error': 'Response not found'}), 404

    if response.user_id != current_user.id and not getattr(current_user, 'is_admin', False):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    db.session.delete(response)
    db.session.commit()
    return jsonify({'success': True}), 200


@app.route('/consultation')
@login_required
def consultation():
    user_requests = ConsultationRequest.query.filter_by(user_id=current_user.id).order_by(ConsultationRequest.created_at.desc()).all()
    counsellors = User.query.filter_by(role='counsellor').all()
    from datetime import datetime, timedelta
    for req in user_requests:
        if req.status == 'booked':
            flash(f'Your consultation with counsellor {req.counsellor.full_name} is booked!', 'success')
            if req.session_datetime:
                now = datetime.utcnow()
                if req.session_datetime > now and req.session_datetime < now + timedelta(days=2):
                    flash(f'Reminder: Your session is scheduled for {req.session_datetime.strftime("%d %b %Y, %I:%M %p")}', 'info')
        elif req.status == 'rejected':
            flash(f'Your consultation request was rejected by counsellor {req.counsellor.full_name}.', 'warning')
    # Available slots (open, future)
    open_slots = AvailabilitySlot.query.filter(
        AvailabilitySlot.is_booked == False,
        AvailabilitySlot.start_time >= datetime.utcnow()
    ).order_by(AvailabilitySlot.start_time.asc()).all()
    # Pass current time to template for comparisons
    return render_template('consultation.html', requests=user_requests, counsellors=counsellors, open_slots=open_slots, now=datetime.utcnow())

@app.route('/api/open_slots')
@login_required
def api_open_slots():
    counsellor_id = request.args.get('counsellor_id', type=int)
    q = AvailabilitySlot.query.filter(
        AvailabilitySlot.is_booked == False,
        AvailabilitySlot.start_time >= datetime.utcnow()
    )
    if counsellor_id:
        q = q.filter(AvailabilitySlot.counsellor_id == counsellor_id)
    slots = q.order_by(AvailabilitySlot.start_time.asc()).all()
    return jsonify([
        {
            'id': s.id,
            'counsellor': {
                'id': s.counsellor.id,
                'full_name': s.counsellor.full_name,
                'username': s.counsellor.username
            },
            'start': s.start_time.isoformat(),
            'end': s.end_time.isoformat()
        } for s in slots
    ])


# Routine Scheduler
@app.route('/routine', methods=['GET', 'POST'])
@login_required
def routine():
    from models import RoutineTask
    if request.method == 'POST':
        # Status update form
        update_id = request.form.get('update_id')
        new_status = request.form.get('new_status')
        if update_id and new_status:
            task = RoutineTask.query.filter_by(id=update_id, user_id=current_user.id).first()
            if task:
                task.status = new_status
                db.session.commit()
                flash(f'Task status updated to {new_status.capitalize()}', 'success')
            else:
                flash('Task not found or permission denied.', 'error')
        else:
            # Add new task form
            title = request.form.get('title', '').strip()
            start_time = request.form.get('start_time', '').strip()
            end_time = request.form.get('end_time', '').strip()
            notes = request.form.get('notes', '').strip()
            if not title or not start_time or not end_time:
                flash('Title, start time, and end time are required.', 'error')
            else:
                try:
                    task = RoutineTask(
                        user_id=current_user.id,
                        title=title,
                        start_time=start_time,
                        end_time=end_time,
                        notes=notes,
                        status='pending',
                        created_date=datetime.utcnow().date()
                    )
                    db.session.add(task)
                    db.session.commit()
                    flash('Routine task added!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash('Error adding routine task.', 'error')
    # Get today's tasks for current user
    today = datetime.utcnow().date()
    tasks = RoutineTask.query.filter_by(user_id=current_user.id, created_date=today).order_by(RoutineTask.start_time.asc()).all()
    return render_template('routine.html', tasks=tasks)

@app.route('/request_consultation', methods=['POST'])
@login_required
def request_consultation():
    urgency = request.form['urgency']
    time_slot = request.form.get('preferred_time', '')
    contact_preference = request.form['contact_preference']
    notes = request.form.get('notes', '')
    counsellor_id_raw = request.form.get('counsellor_id')
    try:
        counsellor_id = int(counsellor_id_raw)
    except (TypeError, ValueError):
        flash('Please select a valid counsellor.', 'error')
        return redirect(url_for('consultation'))
    counsellor = User.query.filter_by(id=counsellor_id, role='counsellor').first()
    if not counsellor:
        flash('Selected counsellor not found.', 'error')
        return redirect(url_for('consultation'))

    consultation = ConsultationRequest(
        user_id=current_user.id,
        urgency_level=urgency,
        time_slot=time_slot,
        contact_preference=contact_preference,
        additional_notes=notes,
        counsellor_id=counsellor_id
    )

    db.session.add(consultation)
    db.session.commit()

    # Notify counsellor
    send_email(
        subject='New consultation request',
        body=f'New consultation request from {current_user.full_name} ({current_user.username}). Urgency: {urgency}.',
        to_email=counsellor.email
    )
    # Notify user (confirmation)
    send_email(
        subject='Consultation request submitted',
        body=f'Your consultation request to {counsellor.full_name} has been submitted. Urgency: {urgency}. We will notify you once the counsellor responds.',
        to_email=current_user.email
    )

    flash(f'Your consultation request has been submitted to {counsellor.full_name}. You will be notified once they respond.', 'success')
    return redirect(url_for('consultation'))

@app.route('/counsellor/availability', methods=['GET', 'POST'])
@login_required
def counsellor_availability():
    if current_user.role != 'counsellor':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        start = request.form.get('start_time')
        end = request.form.get('end_time')
        try:
            from datetime import datetime
            start_dt = datetime.strptime(start, '%Y-%m-%dT%H:%M')
            end_dt = datetime.strptime(end, '%Y-%m-%dT%H:%M')
            if end_dt <= start_dt:
                raise ValueError('End must be after start')
            slot = AvailabilitySlot(counsellor_id=current_user.id, start_time=start_dt, end_time=end_dt)
            db.session.add(slot)
            db.session.commit()
            flash('Availability slot added.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Invalid date/time.', 'error')
        return redirect(url_for('counsellor_availability'))
    slots = AvailabilitySlot.query.filter_by(counsellor_id=current_user.id).order_by(AvailabilitySlot.start_time.asc()).all()
    return render_template('counsellor_availability.html', slots=slots)

@app.route('/book_slot/<int:slot_id>', methods=['POST'])
@login_required
def book_slot(slot_id):
    slot = AvailabilitySlot.query.get_or_404(slot_id)
    if slot.is_booked:
        flash('Slot already booked.', 'warning')
        return redirect(url_for('consultation'))
    counsellor = User.query.get(slot.counsellor_id)
    # Create consultation request tied to this slot
    consultation = ConsultationRequest(
        user_id=current_user.id,
        counsellor_id=slot.counsellor_id,
        urgency_level='low',
        time_slot=f"{slot.start_time.strftime('%d %b %Y %I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}",
        contact_preference='video',
        additional_notes='Booked via availability slot',
        status='pending'
    )
    slot.is_booked = True
    db.session.add(consultation)
    db.session.commit()
    # Notify counsellor
    send_email(
        subject='Slot booked',
        body=f'Slot booked by {current_user.full_name} ({current_user.username}) for {slot.start_time}.',
        to_email=counsellor.email
    )
    # Notify user (confirmation)
    send_email(
        subject='Slot booking submitted',
        body=f'You requested to book {slot.start_time.strftime('%d %b %Y, %I:%M %p')} with {counsellor.full_name}. You will receive a confirmation when the counsellor accepts.',
        to_email=current_user.email
    )
    flash(f'Booked slot with {counsellor.full_name}. Awaiting confirmation.', 'success')
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

@app.route('/inkblot')
@login_required
def inkblot_start():
    return render_template('inkblot/start.html')

@app.route('/inkblot/userinfo', methods=['GET', 'POST'])
@login_required
def inkblot_userinfo():
    if request.method == 'POST':
        session['inkblot_name'] = request.form.get('name', '')
        session['inkblot_career'] = request.form.get('career', '')
        session['inkblot_age'] = request.form.get('age', '')
        session['inkblot_gender'] = request.form.get('gender', '')
        return redirect(url_for('beforestart'))
    return render_template('inkblot/userinfo.html')

@app.route('/inkblot/beforestart')
@login_required
def beforestart():
    return render_template('inkblot/beforestart.html')

@app.route('/inkblot/about')
@login_required
def about():
    return render_template('inkblot/about.html')

@app.route('/inkblot/test', methods=['GET', 'POST'])
@login_required
def inkblot_test():
    if 'inkblot_answers' not in session:
        session['inkblot_answers'] = {}
    answers = session['inkblot_answers']
    if request.method == 'POST':
        blot_num = int(request.form.get('blot_num', 1))
        response = request.form.get('response', '')
        answers[str(blot_num)] = response
        session['inkblot_answers'] = answers
        next_blot = blot_num + 1
        if next_blot > 10:
            return redirect(url_for('inkblot_results'))
        return render_template('inkblot/inkblot.html', blot_num=next_blot)
    else:
        return render_template('inkblot/inkblot.html', blot_num=1)

@app.route('/inkblot/results')
@login_required
def inkblot_results():
    answers = session.get('inkblot_answers', {})
    return render_template('inkblot/results.html', answers=answers)

@app.route('/inkblot/download_pdf')
@login_required
def download_pdf():
    answers = session.get('inkblot_answers', {})
    name = session.get('inkblot_name', '')
    career = session.get('inkblot_career', '')
    age = session.get('inkblot_age', '')
    gender = session.get('inkblot_gender', '')
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    # First page: user info
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(300, 750, "Inkblot Test Results")
    p.setFont("Helvetica", 16)
    y = 700
    if name:
        p.drawCentredString(300, y, f"Name: {name}")
        y -= 40
    if career:
        p.drawCentredString(300, y, f"Career: {career}")
        y -= 40
    if age:
        p.drawCentredString(300, y, f"Age: {age}")
        y -= 40
    if gender:
        p.drawCentredString(300, y, f"Gender: {gender}")
        y -= 40
    p.showPage()
    # Each blot: one page, image centered, answer centered below
    static_img_path = os.path.join(os.path.dirname(__file__), 'static', 'img')
    for i in range(1, 11):
        p.setFont("Helvetica-Bold", 18)
        p.drawCentredString(300, 700, f"Blot {i}")
        img_file = os.path.abspath(os.path.join(static_img_path, f'blot{i}.jpg'))
        if os.path.exists(img_file):
            try:
                img = Image.open(img_file)
                p.drawInlineImage(img, 150, 350, width=300, height=300)
            except Exception as e:
                p.setFont("Helvetica", 12)
                p.drawCentredString(300, 320, f"[Image error: {e}]")
        p.setFont("Helvetica", 16)
        answer = answers.get(str(i), "No response")
        p.drawCentredString(300, 280, f"Your answer: {answer}")
        p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="inkblot_results.pdf", mimetype="application/pdf")

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

@app.route('/counsellor_dashboard')
@login_required
def counsellor_dashboard():
    if current_user.role != 'counsellor':
        flash('Access denied. This page is for counsellors only.', 'error')
        return redirect(url_for('dashboard'))
    # Show all requests (pending, booked, rejected) for this counsellor
    # Order: pending first, then booked, then others by date desc
    status_order = case(
        (ConsultationRequest.status == 'pending', 0),
        (ConsultationRequest.status == 'booked', 1),
        else_=2
    )
    requests = ConsultationRequest.query.filter_by(counsellor_id=current_user.id).order_by(
        status_order, ConsultationRequest.created_at.desc()
    ).all()
    from datetime import datetime
    return render_template('counsellor_dashboard.html', requests=requests, now=datetime.utcnow())

@app.route('/_debug/consults')
@login_required
def debug_consults():
    # Admin sees all; counsellor sees own; others see own user requests
    if current_user.role == 'admin':
        q = ConsultationRequest.query.order_by(ConsultationRequest.created_at.desc()).all()
    elif current_user.role == 'counsellor':
        q = ConsultationRequest.query.filter_by(counsellor_id=current_user.id).order_by(ConsultationRequest.created_at.desc()).all()
    else:
        q = ConsultationRequest.query.filter_by(user_id=current_user.id).order_by(ConsultationRequest.created_at.desc()).all()
    data = []
    for r in q:
        data.append({
            'id': r.id,
            'user_id': r.user_id,
            'user_username': getattr(r.user, 'username', None),
            'counsellor_id': r.counsellor_id,
            'counsellor_username': getattr(r.counsellor, 'username', None) if r.counsellor else None,
            'urgency': r.urgency_level,
            'status': r.status,
            'time_slot': r.time_slot,
            'session_datetime': r.session_datetime.isoformat() if r.session_datetime else None,
            'created_at': r.created_at.isoformat() if r.created_at else None
        })
    return jsonify({'role': current_user.role, 'current_user': current_user.username, 'records': data})

@app.route('/accept_consultation/<int:request_id>', methods=['POST'])
@login_required
def accept_consultation(request_id):
    req = ConsultationRequest.query.get_or_404(request_id)
    if req.counsellor_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('counsellor_dashboard'))
    req.status = 'booked'
    db.session.commit()
    # Notify user
    send_email(
        subject='Consultation accepted',
        body=f'Your consultation was accepted by {current_user.full_name}. You will receive scheduling details soon.',
        to_email=req.user.email
    )
    flash('Consultation accepted and booked. The user will be notified.', 'success')
    return redirect(url_for('counsellor_dashboard'))

@app.route('/reject_consultation/<int:request_id>', methods=['POST'])
@login_required
def reject_consultation(request_id):
    req = ConsultationRequest.query.get_or_404(request_id)
    if req.counsellor_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('counsellor_dashboard'))
    req.status = 'rejected'
    db.session.commit()
    send_email(
        subject='Consultation update',
        body=f'Your consultation request was rejected by {current_user.full_name}. You can request another counsellor from the portal.',
        to_email=req.user.email
    )
    flash('Consultation rejected. The user will be notified.', 'info')
    return redirect(url_for('counsellor_dashboard'))

@app.route('/view_user_assessment/<int:user_id>')
@login_required
def view_user_assessment(user_id):
    if current_user.role != 'counsellor':
        flash('Access denied.', 'error')
        return redirect(url_for('counsellor_dashboard'))
    from models import Assessment, User, MeditationSession, RoutineTask, ConsultationRequest
    user = User.query.get_or_404(user_id)
    # Only allow viewing if this counsellor has a booked consultation with the user
    has_relationship = ConsultationRequest.query.filter_by(
        user_id=user.id,
        counsellor_id=current_user.id,
        status='booked'
    ).first() is not None
    if not has_relationship:
        flash('You can only view analytics for users with booked consultations.', 'error')
        return redirect(url_for('counsellor_dashboard'))
    assessments = Assessment.query.filter_by(user_id=user_id).order_by(Assessment.completed_at.desc()).all()
    if not assessments:
        flash('No assessments found for this user.', 'warning')
        return redirect(url_for('counsellor_dashboard'))
    # Compute user stats for counsellor overview
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())
    weekly_sessions_count = MeditationSession.query.filter_by(user_id=user.id).filter(
        MeditationSession.date >= start_of_week
    ).count()
    total_seconds = db.session.query(func.sum(MeditationSession.duration)).filter_by(
        user_id=user.id
    ).scalar() or 0
    total_minutes_meditated = total_seconds // 60
    todays_tasks = RoutineTask.query.filter_by(user_id=user.id, created_date=today).all()
    # Additional analytics
    recent_30 = datetime.utcnow() - timedelta(days=30)
    recent_assessments = Assessment.query.filter_by(user_id=user.id).filter(Assessment.completed_at >= recent_30).all()
    by_type = {}
    for a in recent_assessments:
        if a.assessment_type not in by_type:
            by_type[a.assessment_type] = {'count': 0, 'moderate': 0, 'severe': 0}
        by_type[a.assessment_type]['count'] += 1
        if a.severity_level in ['Moderate', 'Moderately severe', 'Severe']:
            by_type[a.assessment_type]['severe'] += 1
        elif a.severity_level in ['Mild', 'Fair']:
            by_type[a.assessment_type]['moderate'] += 1
    # Last 3 assessments for quick view
    last_three = assessments[:3]
    # Login streak
    login_streak = current_user.login_streak or 0
    # Meditation time series (last 14 days)
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    sessions_14 = MeditationSession.query.filter_by(user_id=user.id).filter(MeditationSession.date >= days[0]).all()
    minutes_by_day = {d: 0 for d in days}
    for s in sessions_14:
        if s.date in minutes_by_day:
            minutes_by_day[s.date] += (s.duration or 0) // 60
    meditation_series = {
        'labels': [d.strftime('%d %b') for d in days],
        'values': [minutes_by_day[d] for d in days]
    }
    # Assessment severity trend (last 10)
    last_ten = assessments[:10]
    severity_map = {
        'Minimal': 1, 'Good': 1,
        'Mild': 2, 'Fair': 2,
        'Moderate': 3,
        'Moderately severe': 4,
        'Severe': 5
    }
    severity_series = {
        'labels': [a.completed_at.strftime('%d %b') for a in reversed(last_ten)],
        'values': [severity_map.get(a.severity_level, 0) for a in reversed(last_ten)],
        'types': [a.assessment_type for a in reversed(last_ten)]
    }
    return render_template(
        'counsellor_user_assessments.html',
        user=user,
        assessments=assessments,
        weekly_sessions_count=weekly_sessions_count,
        total_minutes_meditated=total_minutes_meditated,
        todays_tasks=todays_tasks,
        recent_by_type=by_type,
        last_three=last_three,
        login_streak=login_streak,
        meditation_series=meditation_series,
        severity_series=severity_series
    )
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied. This page is for admins only.', 'error')
        return redirect(url_for('dashboard'))
    from sqlalchemy.sql import func
    total_users = User.query.count()
    total_counsellors = User.query.filter_by(role='counsellor').count()
    total_bookings = ConsultationRequest.query.count()
    recent_feedback = ConsultationRequest.query.filter(ConsultationRequest.feedback_rating != None).order_by(ConsultationRequest.created_at.desc()).limit(5).all()
    # Top counsellors by bookings and avg rating
    counsellors = User.query.filter_by(role='counsellor').all()
    top_counsellors = []
    for c in counsellors:
        bookings = ConsultationRequest.query.filter_by(counsellor_id=c.id).count()
        ratings = [req.feedback_rating for req in ConsultationRequest.query.filter_by(counsellor_id=c.id).filter(ConsultationRequest.feedback_rating != None).all()]
        avg_rating = sum(ratings)/len(ratings) if ratings else 0
        top_counsellors.append({'full_name': c.full_name, 'username': c.username, 'bookings': bookings, 'avg_rating': avg_rating})
    top_counsellors = sorted(top_counsellors, key=lambda x: (x['bookings'], x['avg_rating']), reverse=True)[:5]
    return render_template('admin_dashboard.html', total_users=total_users, total_counsellors=total_counsellors, total_bookings=total_bookings, recent_feedback=recent_feedback, top_counsellors=top_counsellors)
@app.route('/schedule_follow_up/<int:request_id>', methods=['POST'])
@login_required
def schedule_follow_up(request_id):
    req = ConsultationRequest.query.get_or_404(request_id)
    if req.counsellor_id != current_user.id or req.status != 'booked':
        flash('Unauthorized or invalid request.', 'error')
        return redirect(url_for('counsellor_dashboard'))
    follow_up_datetime_str = request.form.get('follow_up_datetime')
    try:
        from datetime import datetime
        req.follow_up_datetime = datetime.strptime(follow_up_datetime_str, '%Y-%m-%dT%H:%M')
        db.session.commit()
        send_email(
            subject='Follow-up scheduled',
            body=f'Your follow-up is scheduled on {req.follow_up_datetime} with {current_user.full_name}.',
            to_email=req.user.email
        )
        flash('Follow-up session scheduled!', 'success')
    except Exception:
        flash('Invalid date/time format.', 'error')
    return redirect(url_for('counsellor_dashboard'))
@app.route('/set_chat_video_link/<int:request_id>', methods=['POST'])
@login_required
def set_chat_video_link(request_id):
    req = ConsultationRequest.query.get_or_404(request_id)
    if req.counsellor_id != current_user.id or req.status != 'booked':
        flash('Unauthorized or invalid request.', 'error')
        return redirect(url_for('counsellor_dashboard'))
    req.chat_video_link = request.form.get('chat_video_link')
    db.session.commit()
    send_email(
        subject='Session link available',
        body=f'Your session link is set: {req.chat_video_link}',
        to_email=req.user.email
    )
    flash('Chat/Video link set!', 'success')
    return redirect(url_for('counsellor_dashboard'))
@app.route('/submit_feedback/<int:request_id>', methods=['POST'])
@login_required
def submit_feedback(request_id):
    req = ConsultationRequest.query.get_or_404(request_id)
    if req.user_id != current_user.id or req.status != 'booked':
        flash('Unauthorized or invalid request.', 'error')
        return redirect(url_for('consultation'))
    req.feedback_rating = int(request.form.get('feedback_rating'))
    req.feedback_text = request.form.get('feedback_text')
    db.session.commit()
    flash('Thank you for your feedback!', 'success')
    return redirect(url_for('consultation'))
@app.route('/add_session_notes/<int:request_id>', methods=['POST'])
@login_required
def add_session_notes(request_id):
    req = ConsultationRequest.query.get_or_404(request_id)
    if req.counsellor_id != current_user.id or req.status != 'booked':
        flash('Unauthorized or invalid request.', 'error')
        return redirect(url_for('counsellor_dashboard'))
    req.session_notes = request.form.get('session_notes')
    db.session.commit()
    flash('Session notes saved!', 'success')
    return redirect(url_for('counsellor_dashboard'))
@app.route('/schedule_session/<int:request_id>', methods=['POST'])
@login_required
def schedule_session(request_id):
    req = ConsultationRequest.query.get_or_404(request_id)
    if req.counsellor_id != current_user.id or req.status != 'booked':
        flash('Unauthorized or invalid request.', 'error')
        return redirect(url_for('counsellor_dashboard'))
    session_datetime_str = request.form.get('session_datetime')
    try:
        from datetime import datetime
        req.session_datetime = datetime.strptime(session_datetime_str, '%Y-%m-%dT%H:%M')
        db.session.commit()
        send_email(
            subject='Session scheduled',
            body=f'Your session is scheduled for {req.session_datetime} with {current_user.full_name}.',
            to_email=req.user.email
        )
        flash('Session scheduled successfully!', 'success')
    except Exception:
        flash('Invalid date/time format.', 'error')
    return redirect(url_for('counsellor_dashboard'))

@app.route('/cancel_booking/<int:request_id>', methods=['POST'])
@login_required
def cancel_booking(request_id):
    req = ConsultationRequest.query.get_or_404(request_id)
    if req.counsellor_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('counsellor_dashboard'))
    prev_status = req.status
    req.status = 'cancelled'
    db.session.commit()
    if prev_status == 'booked' or prev_status == 'pending':
        send_email(
            subject='Consultation cancelled',
            body=f'Your consultation with {current_user.full_name} has been cancelled. Please book a new slot or request another counsellor.',
            to_email=req.user.email
        )
    flash('Booking cancelled.', 'info')
    return redirect(url_for('counsellor_dashboard'))

@app.route('/download_session_notes/<int:request_id>')
@login_required
def download_session_notes(request_id):
    req = ConsultationRequest.query.get_or_404(request_id)
    if req.counsellor_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('counsellor_dashboard'))
    # Build a simple PDF for session notes
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 760, "Session Notes")
    p.setFont("Helvetica", 12)
    y = 740
    def writeln(text):
        nonlocal y
        if y < 60:
            p.showPage()
            p.setFont("Helvetica", 12)
            y = 780
        p.drawString(50, y, text)
        y -= 18
    writeln(f"Counsellor: {current_user.full_name} ({current_user.username})")
    writeln(f"Student: {req.user.full_name} ({req.user.username})")
    if req.session_datetime:
        writeln(f"Session: {req.session_datetime.strftime('%d %b %Y, %I:%M %p')}")
    writeln(f"Status: {req.status}")
    writeln("")
    p.setFont("Helvetica-Bold", 12)
    writeln("Notes:")
    p.setFont("Helvetica", 12)
    notes = req.session_notes or "(No notes)"
    # Wrap notes
    import textwrap
    for line in notes.splitlines() or [notes]:
        for wrapped in textwrap.wrap(line, width=90):
            writeln(wrapped)
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"session_notes_{request_id}.pdf", mimetype="application/pdf")
@app.route('/send_result_to_counsellor/<int:assessment_id>', methods=['POST'])
@login_required
def send_result_to_counsellor(assessment_id):
    counsellor_id_raw = request.form.get('counsellor_id')
    try:
        counsellor_id = int(counsellor_id_raw)
    except (TypeError, ValueError):
        flash('Please select a valid counsellor.', 'error')
        return redirect(url_for('assessment_results', assessment_id=assessment_id))
    counsellor = User.query.filter_by(id=counsellor_id, role='counsellor').first()
    if not counsellor:
        flash('Selected counsellor not found.', 'error')
        return redirect(url_for('assessment_results', assessment_id=assessment_id))
    assessment = Assessment.query.get_or_404(assessment_id)
    # Create a new consultation request for the selected counsellor, referencing the assessment
    from models import ConsultationRequest
    new_request = ConsultationRequest(
        user_id=current_user.id,
        counsellor_id=counsellor_id,
        urgency_level='medium',
        time_slot='Assessment follow-up',
        contact_preference='email',
        additional_notes=f'Assessment ({assessment.assessment_type}) sent to counsellor. Score: {assessment.score}, Severity: {assessment.severity_level}',
        status='pending'
    )
    db.session.add(new_request)
    db.session.commit()
    # Notify counsellor and user
    try:
        counsellor = User.query.get(int(counsellor_id))
    except Exception:
        counsellor = None
    if counsellor:
        send_email(
            subject='Assessment shared with you',
            body=f'{current_user.full_name} sent {assessment.assessment_type} results (score {assessment.score}, {assessment.severity_level}).',
            to_email=counsellor.email
        )
    send_email(
        subject='Assessment shared',
        body=f'Your {assessment.assessment_type} results were shared with the counsellor.',
        to_email=current_user.email
    )
    # Prepare analysis for template
    try:
        analysis = json.loads(assessment.recommendations) if assessment.recommendations else generate_analysis(assessment.assessment_type, assessment.score)
    except Exception:
        analysis = generate_analysis(assessment.assessment_type, assessment.score)
    flash('Your assessment result has been sent to the selected counsellor and a follow-up request has been created.', 'success')
    return render_template('assessment_results.html', assessment=assessment, analysis=analysis, counsellors=User.query.filter_by(role='counsellor').all(), sent_to_counsellor=True)