import stripe
from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request, jsonify, abort
from flask_login import login_required, current_user
from ..utils import send_email
from ..config import Config
from .forms import PreferencesForm
from ..extensions import db
from functools import wraps

main_bp = Blueprint('main', __name__, template_folder='templates')

# Set the Stripe API key
stripe.api_key = Config.STRIPE_SECRET_KEY

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

@main_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    form = PreferencesForm()
    if form.validate_on_submit():
        current_user.role = form.role.data
        current_user.assistant_personality = form.assistant_personality.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your preferences have been updated.', 'success')
        return redirect(url_for('main.dashboard'))
    elif request.method == 'GET':
        form.role.data = current_user.role
        form.assistant_personality.data = current_user.assistant_personality
        form.about_me.data = current_user.about_me
    return render_template('main/preferences.html', form=form)



@main_bp.route('/checkout')
@login_required
def checkout():
    return render_template('main/checkout.html', 
                           stripe_publishable_key=Config.STRIPE_PUBLISHABLE_KEY)

@main_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[
                {
                    'price': 'price_1Q2qsFKjJ23rv2vUvTefj4Sx',  # Replace with your price ID
                    'quantity': 1,
                },
                {
                    'price': 'price_1Q2qrZKjJ23rv2vUc6hO0tpY',  # Replace with your price ID
                    'quantity': 1,
                },
                {
                    'price': 'price_1Q2qrFKjJ23rv2vUbICjHRbK',  # Replace with your price ID
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=url_for('main.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('main.cancel', _external=True),
        )
        return jsonify({'sessionId': checkout_session['id']})
    except Exception as e:
        return jsonify(error=str(e)), 403

@main_bp.route('/success')
@login_required
def success():
    session_id = request.args.get('session_id')
    if session_id:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        if checkout_session.payment_status == 'paid':
            # Update user's subscription status if not already updated by webhook
            if not current_user.is_premium:
                current_user.is_premium = True
                current_user.subscription_status = 'active'
                db.session.commit()
    flash('Your payment was successful!', 'success')
    return render_template('main/success.html')

@main_bp.route('/cancel')
@login_required
def cancel():
    flash('Your payment was canceled.', 'warning')
    return render_template('main/cancel.html')


def premium_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_premium:
            flash('You need a premium subscription to access this feature.', 'warning')
            return redirect(url_for('main.checkout'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/premium-feature')
@login_required
@premium_required
def premium_feature():
    # Premium feature implementation
    return render_template('main/premium_feature.html')