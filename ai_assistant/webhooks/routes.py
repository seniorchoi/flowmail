import stripe
from flask import request, current_app, jsonify
from ..extensions import db
from ..models import User
from ..config import Config
from . import webhooks_bp

# Set the Stripe API key
stripe.api_key = Config.STRIPE_SECRET_KEY

@webhooks_bp.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = Config.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        return jsonify(success=False), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify(success=False), 400

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)
    # ... handle other relevant events ...

    return jsonify(success=True), 200

def handle_checkout_session(session):
    customer_email = session.get('customer_email')
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')

    user = User.query.filter_by(email=customer_email).first()
    if user:
        user.stripe_customer_id = customer_id
        user.is_premium = True
        user.subscription_status = 'active'
        db.session.commit()

def handle_subscription_updated(subscription):
    customer_id = subscription.get('customer')
    status = subscription.get('status')

    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if user:
        user.subscription_status = status
        user.is_premium = status == 'active'
        db.session.commit()

def handle_subscription_deleted(subscription):
    customer_id = subscription.get('customer')

    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if user:
        user.subscription_status = 'canceled'
        user.is_premium = False
        db.session.commit()
