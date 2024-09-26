# ai_assistant/utils.py
import os
import requests
import re
import hmac
import hashlib
import openai
import logging
from .config import Config

logger = logging.getLogger(__name__)

def send_email(to_email, subject, text_content, html_content=None):
    try:
        response = requests.post(
            f"{Config.MAILGUN_BASE_URL}/messages",
            auth=("api", Config.MAILGUN_API_KEY),
            data={
                "from": Config.FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "text": text_content,
                "html": html_content,
            },
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
    pattern = rf'assistant\.([A-Za-z0-9_.+-]+)@{domain}'
    match = re.match(pattern, recipient_address)
    if match:
        user_identifier = match.group(1)
        return user_identifier
    else:
        return None

def verify_mailgun_request(token, timestamp, signature):
    api_key = Config.MAILGUN_API_KEY
    if not api_key:
        return False
    hmac_digest = hmac.new(
        key=api_key.encode('utf-8'),
        msg=f'{timestamp}{token}'.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(hmac_digest, signature)

def process_email_with_ai(email_content):
    openai.api_key = Config.OPENAI_API_KEY
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=email_content,
        max_tokens=150,
        temperature=0.7
    )
    return response.choices[0].text.strip()
