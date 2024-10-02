import requests
import re
import hmac
import hashlib
from openai import OpenAI
import logging
import time
from .config import Config
import json

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
"""
def process_email_with_ai(email_subject, email_content, user=None):
    messages = []

    if user:
        # Include user-specific context if necessary
        messages.append({"role": "system", "content": f"Assistant for user {user.username}."})

    combined_content = f"Subject: {email_subject}\n\n{email_content}" if email_subject else email_content
    messages.append({"role": "user", "content": combined_content})
    
    try:
        response = client.chat.completions.create(
            model='gpt-4o-mini',  # Use a model you have access to
            messages=messages,
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "I'm sorry, but I couldn't process your request at this time."
"""

def process_email_with_ai(email_subject, email_content, user=None):
    """
    Process the email content with OpenAI's ChatCompletion API, including user context.
    """
    if not user:
        # Handle the case where user is None
        user_name = "User"
        user_role = ""
        assistant_personality = ""
        about_me = ""
    else:
        user_name = user.name
        user_role = user.role or ""
        assistant_personality = user.assistant_personality or ""
        about_me = user.about_me or ""
    
    # Prepare the assistant personality traits
    #personality_traits = assistant_personality.split(',') if assistant_personality else []
    personality_traits = [trait.strip() for trait in assistant_personality.split(',')] if assistant_personality else []
    personality_description = ', '.join([trait.strip() for trait in personality_traits])

    # Prepare the 'about me' information
    #about_me_info = about_me.split(',') if about_me else []
    about_me_info = [info.strip() for info in about_me.split(',')] if about_me else []
    about_me_description = '. '.join([info.strip() for info in about_me_info])

    # Construct the detailed prompt
    prompt = (
        f"You are {user_name}'s personal AI assistant. "
        f"{f'{user_name} is a {user_role}. ' if user_role else ''}"
        f"Your personality traits are: {personality_description}. "
        f"{f'{user_name} is {about_me_description}.' if about_me_description else ''} "
        f"Your task is to read the following email sent to {user_name} and write a response as {user_name}'s assistant. "
        f"The response should have a {personality_description} tone. "
        #f"\n\nEmail Subject:\n{email_subject}\n\n" if email_subject else ""
        f"Email Content:\n{email_content}\n\n"
        f"Do not include any placeholders."
    )

    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": prompt}
    ]

    """
    # Construct the detailed prompt
    prompt = (
        f"You are the personal AI assistant of {user_name}. "
        f"{f'They are a {user_role}.' if user_role else ''} "
        f"Your task is to read the following email and write a response that aligns with {user_name}'s style and preferences.\n\n"
        "Email Content:\n"
        f"{email_content}\n\n"
        f"{user_name}'s Preferences:\n"
        f"{json.dumps(user_preferences, indent=2)}"
        f"Do not include any placeholders."
    )

    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": prompt}
    ]
    """
    try:
        response = client.chat.completions.create(
            model='gpt-4o-mini',  # Use a model you have access to
            messages=messages,
            max_tokens=300,
            temperature=0.7,
        )
        ai_reply = response.choices[0].message.content.strip()
        return ai_reply
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "I'm sorry, but I couldn't process your request at this time."