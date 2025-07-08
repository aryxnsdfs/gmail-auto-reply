import os
import base64
import time
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from email.mime.text import MIMEText
import json
import logging

import google.generativeai as genai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ✅ Logging setup
logging.basicConfig(
    filename='email_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ✅ Configure Gemini API
genai.configure(api_key="")
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

LABELS = {
    'bank': 'Bank',
    'orders': 'Orders',
    'important': 'Important'
}

# ----------------------- Gmail Auth ------------------------ #
def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds_json = json.loads(os.environ['GOOGLE_CREDS'])
            flow = InstalledAppFlow.from_client_config(creds_json, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

# ---------------------- Email Helpers ---------------------- #
def extract_links(text):
    return re.findall(r'https?://[^\s]+', text)

def fetch_link_preview(link):
    try:
        response = requests.get(link, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else "No Title"
        p_tags = soup.find_all('p')
        preview = " ".join([p.get_text() for p in p_tags[:3]])
        return f"Title: {title}\nPreview: {preview[:300]}"
    except:
        return f"Could not read content from the link: {link}"

# ------------------ Gemini & Email Logic ------------------- #
def classify_email(subject, body, sender):
    subject_lower = subject.lower()
    body_lower = body.lower()
    sender_lower = sender.lower()

    if any(bank in sender_lower for bank in ['hdfc', 'sbi', 'axis', 'icici', 'bank']):
        return 'bank'
    if 'order' in subject_lower and 'amazon' in sender_lower:
        return 'orders'
    if 'flipkart' in sender_lower and 'order' in subject_lower:
        return 'orders'
    if any(x in sender_lower for x in ['noreply', 'mailer', 'notification']) or 'unsubscribe' in body_lower:
        if is_useful_by_gemini(subject, body):
            return 'keep'
        else:
            return 'bin'
    if any(x in body_lower for x in ['congratulations', 'claim prize', 'lottery', 'lucky winner']):
        return 'bin'
    if is_personal_by_gemini(subject, body):
        return 'important'
    return 'bin'

def is_useful_by_gemini(subject, body):
    prompt = f"""
    Is this email important to a human? Don't say maybe. Subject: {subject}\nBody: {body[:1000]}\nReply only Yes or No.
    """
    try:
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        return 'yes' in response.text.lower()
    except Exception as e:
        logging.warning(f"Gemini failed during is_useful: {e}")
        return False

def is_personal_by_gemini(subject, body):
    prompt = f"""
    Is this email a personal or work-related message that needs a reply? Be honest. Subject: {subject}\nBody: {body[:1000]}\nReply only Yes or No.
    """
    try:
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        return 'yes' in response.text.lower()
    except Exception as e:
        logging.warning(f"Gemini failed during is_personal: {e}")
        return False

def generate_reply(email_body, subject, links_preview):
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""
You are an AI assistant replying to a professional email on behalf of Aryan Gupta.

Date: {today}
Subject: {subject}
Message: {email_body}
Link Analysis: {links_preview or 'No links'}

Guidelines:
- Do NOT use the sender's name or any placeholder like [Sender Name].
- End the reply with: "Regards,\nAryan Gupta"
- Keep the tone polite and professional.
- Avoid using any placeholder like [Your Name].
Return only the body of the reply.
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logging.warning(f"Gemini failed during generate_reply: {e}")
        return "Thank you for your message.\n\nRegards,\nAryan Gupta"


# -------------------- Main Auto Handler -------------------- #
def auto_reply(service):
    try:
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
        messages = results.get('messages', [])
    except Exception as e:
        logging.error(f"Failed to fetch messages: {e}")
        return

    if not messages:
        print("✅ No unread messages.")
        return

    for msg in messages:
        try:
            message = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            payload = message['payload']
            headers = payload['headers']
            parts = payload.get('parts', [])

            body_data = payload['body'].get('data')
            if not body_data and parts:
                for part in parts:
                    if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                        body_data = part['body']['data']
                        break

            email_body = base64.urlsafe_b64decode(body_data).decode('utf-8') if body_data else '[No content]'
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "")
            thread_id = message['threadId']

            classification = classify_email(subject, email_body, sender)
            print(f"📬 From: {sender} | Subject: {subject} => Action: {classification}")

            if classification == 'important':
                links = extract_links(email_body)
                links_preview = "\n\n".join([fetch_link_preview(link) for link in links]) if links else None
                reply_text = generate_reply(email_body, subject, links_preview)

                reply_msg = MIMEText(reply_text)
                reply_msg['to'] = sender
                reply_msg['subject'] = "Re: " + subject
                raw = base64.urlsafe_b64encode(reply_msg.as_bytes()).decode()
                body = {'raw': raw, 'threadId': thread_id}

                try:
                    service.users().messages().send(userId='me', body=body).execute()
                    print(f"✅ Smart reply sent to: {sender}")
                except Exception as e:
                    print("❌ Send failed:", e)

                label_id = get_or_create_label(service, LABELS['important'])
                service.users().messages().modify(userId='me', id=msg['id'], body={'addLabelIds': [label_id]}).execute()

            elif classification in LABELS:
                label_id = get_or_create_label(service, LABELS[classification])
                service.users().messages().modify(userId='me', id=msg['id'], body={'addLabelIds': [label_id]}).execute()

            elif classification == 'bin':
                service.users().messages().trash(userId='me', id=msg['id']).execute()

            service.users().messages().modify(userId='me', id=msg['id'], body={'removeLabelIds': ['UNREAD']}).execute()

        except Exception as e:
            logging.error(f"Failed to process message {msg['id']}: {e}")

# ---------------------- Labels Handler ---------------------- #
def get_or_create_label(service, label_name):
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    for label in labels:
        if label['name'].lower() == label_name.lower():
            return label['id']
    new_label = {'name': label_name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
    created_label = service.users().labels().create(userId='me', body=new_label).execute()
    return created_label['id']

# ------------------------- Runner --------------------------- #
if __name__ == '__main__':
    gmail = authenticate_gmail()
    while True:
        auto_reply(gmail)
        print("⏳ Waiting 60s for next check...")
        time.sleep(60)
