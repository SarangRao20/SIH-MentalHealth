# MindCare Mental Health Platform

## Overview

MindCare is a comprehensive mental health support platform built with Flask that provides students with AI-powered chat support, standardized mental health assessments, meditation resources, and professional consultation services. The platform serves multiple user types (students, teachers, administrators) and includes features for anonymous venting, progress tracking, and crisis intervention protocols.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask**: Core web framework with SQLAlchemy ORM for database operations
- **Flask-Login**: Session management and user authentication
- **Werkzeug**: Password hashing and security utilities
- **Database**: SQLite (default) with PostgreSQL compatibility via environment variables

### Database Design
- **User Model**: Handles authentication, role-based access (student/teacher/admin), and privacy-focused features like hashed student IDs
- **Chat System**: Session-based conversations with message history and AI context preservation
- **Assessment System**: PHQ-9 (depression), GAD-7 (anxiety), and GHQ (general health) screening tools with scoring algorithms
- **Additional Models**: Meditation sessions, venting posts with anonymous responses, and consultation requests

### Frontend Architecture
- **Bootstrap 5**: Responsive UI framework with custom CSS variables for mental health-friendly color schemes
- **Progressive Enhancement**: JavaScript modules for chat interface, assessment handling, and voice integration
- **Template System**: Jinja2 templates with consistent base layout and component reusability

### AI Integration
- **OpenAI GPT-5**: Primary conversational AI for mental health support with specialized system prompts
- **Crisis Detection**: Keyword-based monitoring for suicide ideation and self-harm indicators
- **Assessment Analysis**: AI-powered interpretation of screening results with actionable recommendations

### Voice and Accessibility
- **Text-to-Speech**: pyttsx3 integration for guided meditation and accessibility support
- **Speech Recognition**: Web Speech API for hands-free interaction during crisis situations
- **Responsive Design**: Mobile-first approach with accessibility considerations

### Security and Privacy
- **Data Protection**: Student ID hashing, secure password storage with Werkzeug
- **Session Management**: Flask-Login with configurable session timeouts
- **Crisis Protocols**: Automatic escalation procedures and emergency contact integration

### User Experience Features
- **Gamification**: Login streaks and progress tracking to encourage consistent engagement
- **Anonymous Support**: Venting hall with privacy-preserving user interactions
- **Multi-role Dashboard**: Differentiated interfaces for students, mentors, and administrators
- **Real-time Features**: Live chat with typing indicators and message queuing

## External Dependencies

### AI and NLP Services
- **OpenAI API**: GPT-5 for conversational support and assessment analysis
- **Crisis Detection**: Custom keyword monitoring system with professional escalation protocols

### Voice and Audio
- **pyttsx3**: Cross-platform text-to-speech synthesis for meditation guidance
- **Web Speech API**: Browser-based speech recognition for accessibility features

### Frontend Libraries
- **Bootstrap 5.3.0**: UI framework via CDN
- **Font Awesome 6.0**: Icon library for consistent visual elements
- **Chart.js**: Data visualization for assessment results and progress tracking

### Database and Storage
- **SQLAlchemy**: ORM with support for SQLite (development) and PostgreSQL (production)
- **Database Migrations**: Built-in table creation with model-based schema management

### Deployment and Infrastructure
- **Werkzeug ProxyFix**: Production deployment support with reverse proxy compatibility
- **Environment Configuration**: Flexible configuration for database URLs, API keys, and session secrets