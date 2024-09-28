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

def process_email_with_ai(email_content):
    response = client.chat.completions.create(model='gpt-4o-mini',  # or 'gpt-4' if you have access
    messages=[
        {"role": "user", "content": email_content}
    ],
    max_tokens=150,
    temperature=0.7)
    return response.choices[0].message.content.strip()