# ai_assistant/main/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from ..utils import send_email
from ..config import Config

main_bp = Blueprint('main', __name__, template_folder='templates')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    assistant_email = f'assistant.{current_user.username}@{Config.MAILGUN_DOMAIN}'
    return render_template('main/dashboard.html', assistant_email=assistant_email)

@main_bp.route('/send-test-email', methods=['GET','POST'])
@login_required
def send_test_email():
    response = send_email(
        to_email=current_user.email,
        subject='Test Email from AI Assistant',
        text_content='This is a test email from your AI Assistant application.',
        html_content='<p>This is a test email from your <strong>AI Assistant</strong> application.</p>'
    )
    if response is None:
        current_app.logger.error("send_email returned None")
    else:
        current_app.logger.info(f"Email sent, response status code: {response.status_code}")
    if response and response.status_code in [200, 202]:
        flash('Test email sent!', 'success')
    else:
        flash('Failed to send test email.', 'danger')
    return redirect(url_for('main.dashboard'))