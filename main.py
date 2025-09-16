from app import app
import routes  
from routes import send_email

@app.route('/test_email')
def test_email():
    success = send_email(
        subject='Test Email from MindCare',
        body='This is a test email to verify SMTP setup.',
        to_email='raosarang2006@gmail.com'  # Change to your email for testing
    )
    if success:
        return 'Test email sent successfully! Check your inbox.'
    else:
        return 'Failed to send test email. Check your SMTP settings and logs.'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2323, debug=True)
