# ai_assistant/email_handler/routes.py
from flask import request, abort, current_app
from . import email_handler  # Import the existing blueprint
from ..extensions import db
from ..models import User
from ..utils import (
    verify_mailgun_request,
    extract_user_identifier,
    process_email_with_ai,
    send_email,
    extract_additional_recipients
)
from ..config import Config
import logging
import traceback

# Configure logger
logger = logging.getLogger(__name__)

@email_handler.route('/receive', methods=['POST'])
def receive_email():
    try:
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

        # Get the sender and recipient
        sender = request.form.get('sender').strip().lower()        # The From address
        recipient = request.form.get('recipient').strip().lower()  # The To address
        subject = request.form.get('subject')
        body_plain = request.form.get('body-plain')

        # Extract the username from the recipient address
        user_identifier = extract_user_identifier(recipient)
        logger.info(f"Extracted user identifier: {user_identifier}")

        # Check if the sender is the AI assistant's own email address
        ai_email_address = f"assistant.{user_identifier}@{Config.MAILGUN_DOMAIN}".lower()
        if sender == ai_email_address:
            logger.info(f"Ignoring email from AI assistant itself: {sender}")
            return '', 200  # Ignore the email

        # Check if the sender is the AI assistant's email
        if sender.lower().startswith('assistant.') and sender.lower().endswith(f"@{Config.MAILGUN_DOMAIN.lower()}"):
            logger.info(f"Ignoring email from AI assistant: {sender}")
            return '', 200  # Ignore the email

        
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
        #user = User.query.filter_by(username=user_identifier).first()
        #logger.info(f"User found: {user}")

        # Find the owner of the AI assistant email (User 1)
        #owner_user = User.query.filter_by(username=user_identifier).first()
        owner_user = db.session.query(User).filter_by(username=user_identifier).first()
        logger.info(f"Owner user found: {owner_user}")

        if not owner_user:
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


        # Parse CC addresses
        cc_header = request.form.get('Cc', '')
        cc_addresses = [email.strip().lower() for email in cc_header.split(',') if email.strip()]
        # Remove the AI assistant's email from CC addresses to prevent loops
        cc_addresses = [email for email in cc_addresses if email != ai_email_address]
        # Collect additional recipients from the email content (Option 1)
        additional_recipients = extract_additional_recipients(body_plain)

        # Combine CC addresses and additional recipients
        all_recipients = set([sender] + additional_recipients)
        cc = [owner_user.email]

        # Determine if the sender is the owner or another user
        if sender.lower() == owner_user.email.lower() and additional_recipients:
            # Case 1 or Case 3: User 1 is sending an email
            recipients = list(all_recipients)
            cc = cc_addresses
        else:
            # Case 2: Another user is sending an email to the AI assistant
            recipients = [sender]
            cc = [owner_user.email]


        # Process the email with OpenAI
        #try:
        ai_response = process_email_with_ai(subject, body_plain, owner_user)
        logger.info(f"AI response: {ai_response}")
    

        # Construct the email content including the original message
        user_name = owner_user.name if owner_user.name else owner_user.username
        user_email = owner_user.email
        greeting = f"Hi, this is {user_name}'s AI assistant."
        
        # Log who to whom email was sent from
        logger.info(f"Received email from: {sender} to: {recipient}")

        # Format the AI's response
        ai_response_formatted = f"\n\n{ai_response}\n\n"

        # Include the original message thread
        original_message = (
            "\n\n--- Original Message ---\n"
            f"From: {sender}\n"
            f"To: {recipient}\n"
            f"Subject: {subject}\n\n"
            f"{body_plain}"
        )

        footer = (
            f"\n\nYou can email {user_name} directly at {user_email}."
            f"\nGet your Personal AI assistant at www.aiflowmail.com."
        )

        email_content = greeting + ai_response_formatted + original_message + footer

        # Send the AI-generated response
        from_email = ai_email_address
        reply_to_email = from_email  # Replies should go back to the AI assistant
        email_subject = subject if subject.startswith("Re:") else f"Re: {subject}"

        send_email(
            to_email=recipients,
            cc=cc,
            subject=email_subject,
            text_content=email_content,
            from_email=from_email,
            reply_to=reply_to_email
        )

        return '', 200  # Respond with 200 OK

    except Exception as e:
        logger.error(f"Error processing email with AI: {e}")
        logger.error(traceback.format_exc())