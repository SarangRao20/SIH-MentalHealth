import os
import logging
from flask import Flask, request, session
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel, gettext, ngettext, lazy_gettext, get_locale
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase
## Removed inkblot import; will define inkblot routes in routes.py
from database import db

# Configure logging with reduced noise from comtypes
logging.basicConfig(level=logging.INFO)

# Suppress verbose debugging from comtypes (Windows Speech API)
logging.getLogger('comtypes').setLevel(logging.WARNING)
logging.getLogger('comtypes.client').setLevel(logging.WARNING)
logging.getLogger('comtypes._post_coinit').setLevel(logging.WARNING)
logging.getLogger('comtypes._comobject').setLevel(logging.WARNING)

class Base(DeclarativeBase):
    pass

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Babel Configuration
app.config['LANGUAGES'] = {
    'en': 'English',
    'hi': 'हिंदी'
}
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///mental_health.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

db.init_app(app)

# Initialize Babel
babel = Babel()

def get_locale():
    # 1. If user explicitly set a language
    if request.args.get('language'):
        session['language'] = request.args.get('language')
    
    # 2. Use session language if set
    if 'language' in session and session['language'] in app.config['LANGUAGES'].keys():
        return session['language']
    
    # 3. Fall back to browser's preferred language
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or app.config['BABEL_DEFAULT_LOCALE']

babel.init_app(app, locale_selector=get_locale)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    import models  # noqa: F401
    db.create_all()  # Ensure all tables are created, including routine_tasks
    logging.info("Database tables created")

def nl2br(value):
    if value is None:
        return ''
    if not isinstance(value, str):
        value = str(value)
    return Markup(value.replace('\n', '<br>'))

app.jinja_env.filters['nl2br'] = nl2br

# Add get_locale to template context
app.jinja_env.globals['get_locale'] = get_locale

## Import routes to register them
import routes

## Removed inkblot_bp blueprint registration; now using direct route in routes.py

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
