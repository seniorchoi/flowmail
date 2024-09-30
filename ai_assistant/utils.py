# ai_assistant/utils.py
import os
import requests
import re
import hmac
import hashlib
from openai import OpenAI
import logging
import time
from .config import Config


client = OpenAI(api_key=Config.OPENAI_API_KEY)
logger = logging.getLogger(__name__)

def send_email(to_email, subject, text_content, html_content=None, from_email=None, cc=None, reply_to=None):
    try:
        if from_email is None:
            from_email = Config.FROM_EMAIL

        data = {
            "from": from_email,
            "to": to_email if isinstance(to_email, list) else [to_email],
            "subject": subject,
            "text": text_content,
            "html": html_content,
        }

        if reply_to:
            data["h:Reply-To"] = reply_to

        if cc:
            data["cc"] = cc if isinstance(cc, list) else [cc]

        response = requests.post(
            f"{Config.MAILGUN_BASE_URL}/messages",
            auth=("api", Config.MAILGUN_API_KEY),
            data=data,
        )

        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending email: {e}")
        if 'response' in locals():
            logger.error(f"Response status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
        return None

def extract_user_identifier(recipient_address):
    """
    Extracts the user's identifier from the recipient address.
    Expected format: assistant.username@yourdomain.com
    """
    domain = Config.MAILGUN_DOMAIN.replace('.', r'\.')
    # Pattern for assistant.username@aiflowmail.com
    pattern_with_username = rf'assistant\.([A-Za-z0-9_.+-]+)@{domain}'
    # Pattern for assistant@aiflowmail.com
    pattern_without_username = rf'assistant@{domain}$'
    
    match_with_username = re.match(pattern_with_username, recipient_address)
    if match_with_username:
        user_identifier = match_with_username.group(1)
        return user_identifier
    elif re.match(pattern_without_username, recipient_address):
        # No username provided
        return None
    else:
        # Invalid email format
        return None

def extract_additional_recipients(email_content):
    # Simple regex to find email addresses in the content
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    found_emails = re.findall(email_pattern, email_content)
    # Filter out any unwanted emails, such as the owner's email
    filtered_emails = [email for email in found_emails if email != Config.FROM_EMAIL]
    return filtered_emails


def verify_mailgun_request(token, timestamp, signature):
    signing_key = Config.MAILGUN_WEBHOOK_SIGNING_KEY
    if not signing_key:
        return False

    # Prepare the data to be hashed
    data = f'{timestamp}{token}'.encode('utf-8')

    # Check if the timestamp is within 5 minutes
    if abs(time.time() - float(timestamp)) > 300:
        logger.error("Timestamp is too old or too far in the future.")
        return False

    hmac_digest = hmac.new(
        key=signing_key.encode('utf-8'),
        msg=f'{timestamp}{token}'.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

    logger.info(f"Computed HMAC digest: {hmac_digest}")
    logger.info(f"Received signature: {signature}")

    is_valid = hmac.compare_digest(hmac_digest, signature)
    logger.info(f"Signature valid: {is_valid}")
    return is_valid


#OPEN AI
def process_email_with_ai(email_subject, email_content, user=None):
    messages = []

    if user:
        # Include user-specific context if necessary
        messages.append({"role": "system", "content": f"Assistant for user {user.username}."})

    # Include the subject in the message
    if email_subject:
        combined_content = f"Subject: {email_subject}\n\n{email_content}"
    else:
        combined_content = email_content

    messages.append({"role": "user", "content": combined_content})

    response = client.chat.completions.create(
        model='gpt-4o-mini',  # or 'gpt-4' if you have access
        messages=messages,
        max_tokens=300,
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()
