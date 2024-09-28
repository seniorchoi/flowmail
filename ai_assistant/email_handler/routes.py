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
from ..config import Config
import logging
import traceback

# Configure logger
logger = logging.getLogger(__name__)

@email_handler.route('/receive', methods=['POST'])
def receive_email():
    """
    Endpoint to receive emails forwarded by Mailgun.
    """
    # Log incoming data
    logger.info(f"Received webhook data: {request.form}")

    # Verify the request came from Mailgun
    token = request.form.get('token')
    timestamp = request.form.get('timestamp')
    signature = request.form.get('signature')

    logger.info(f"Token: {token}, Timestamp: {timestamp}, Signature: {signature}")

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
    logger.info(f"Extracted user identifier: {user_identifier}")
    
    if user_identifier is None:
        # Email sent to assistant@aiflowmail.com without a username
        instruction_message = (
            "Hello,\n\n"
            "Thank you for reaching out to our AI Assistant service.\n\n"
            "To use the assistant, please send your email to "
            "`assistant.YOUR_USERNAME@aiflowmail.com`, replacing `YOUR_USERNAME` with your registered username.\n\n"
            "If you haven't registered yet, please sign up at https://www.aiflowmail.com/register.\n\n"
            "Best regards,\n"
            "AI FlowMail Team"
        )
        send_email(
            to_email=sender,
            subject='How to Use the AI Assistant',
            text_content=instruction_message
        )
        return '', 200  # Respond with 200 OK

    # Find the user in the database
    user = User.query.filter_by(username=user_identifier).first()
    logger.info(f"User found: {user}")

    if not user:
        # Send an email informing them to register
        registration_message = (
            f"Hello,\n\n"
            f"We couldn't find a user with the username '{user_identifier}'.\n\n"
            f"Please ensure you have registered at https://www.aiflowmail.com/register and are using the correct username in the email address.\n\n"
            f"`assistant.YOUR_USERNAME@aiflowmail.com`, replacing `YOUR_USERNAME` with your registered username.\n\n"
            f"Best regards,\n"
            f"AI FlowMail Team"
        )
        send_email(
            to_email=sender,
            subject='Registration Required',
            text_content=registration_message
        )
        return '', 200

    # Process the email with OpenAI
    try:
        ai_response = process_email_with_ai(subject, body_plain, user)
        logger.info(f"AI response: {ai_response}")
    except Exception as e:
        logger.error(f"Error processing email with AI: {e}")
        logger.error(traceback.format_exc())
        ai_response = "There was an error processing your email. Please try again later."

    # Construct the email content   
    
    user_name = user.name if user.name else user.username
    user_email = user.email
    greeting = f"Hi, this is {user_name}'s AI assistant.\n\n"
    footer = f"\n\nYou can email {user_name} directly at {user_email}.\nGet your Personal AI assistant at www.aiflowmail.com."

    email_content = greeting + ai_response + footer

    # Send the AI-generated response back to the sender
    from_email = f"assistant.{user_identifier}@{Config.MAILGUN_DOMAIN}"
    send_email(
        to_email=sender,
        subject='Re: ' + subject,
        text_content=email_content,
        from_email=from_email
    )

    return '', 200  # Respond with 200 OK
