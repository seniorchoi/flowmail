# ai_assistant/email_handler/routes.py
from flask import request, abort, current_app
from . import email_handler  # Import the existing blueprint
from ..extensions import db
from ..models import User
from ..utils import (
    verify_mailgun_request,
    extract_user_identifier,
    process_email_with_ai,
    send_email
)
import logging

# Configure logger
logger = logging.getLogger(__name__)

@email_handler.route('/receive', methods=['POST'])
def receive_email():
    """
    Endpoint to receive emails forwarded by Mailgun.
    """
    # Verify the request came from Mailgun
    token = request.form.get('token')
    timestamp = request.form.get('timestamp')
    signature = request.form.get('signature')

    if not verify_mailgun_request(token, timestamp, signature):
        logger.error('Invalid Mailgun request signature.')
        abort(403)

    # Parse the incoming email data
    recipient = request.form.get('recipient')  # The To address
    sender = request.form.get('sender')        # The From address
    subject = request.form.get('subject')
    body_plain = request.form.get('body-plain')

    # Extract the username from the recipient address
    user_identifier = extract_user_identifier(recipient)
    if not user_identifier:
        logger.error(f"Invalid recipient address: {recipient}")
        return '', 200  # Respond with 200 to prevent Mailgun retries

    # Find the user in the database
    user = User.query.filter_by(username=user_identifier).first()
    if not user:
        # Optionally send an email informing them to register
        send_email(
            to_email=sender,
            subject='Registration Required',
            text_content='Please register for an account to use this service.'
        )
        return '', 200  # Respond with 200 to prevent Mailgun retries

    # Process the email with OpenAI
    try:
        ai_response = process_email_with_ai(body_plain)
    except Exception as e:
        logger.error(f"Error processing email with AI: {e}")
        ai_response = "There was an error processing your email. Please try again later."

    # Send the AI-generated response back to the sender
    send_email(
        to_email=sender,
        subject='Re: ' + subject,
        text_content=ai_response
    )

    return '', 200  # Respond with 200 OK
