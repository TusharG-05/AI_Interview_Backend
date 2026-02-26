import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..core.logger import get_logger
from ..core.config import MAIL_USERNAME, MAIL_PASSWORD

logger = get_logger(__name__)

class EmailService:
    def __init__(self):
        self.username = MAIL_USERNAME
        self.password = MAIL_PASSWORD
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
    def send_interview_invitation(self, to_email: str, candidate_name: str, link: str, time_str: str, duration_minutes: int):
        """
        Sends an email with the interview link using SendGrid v3 HTTP API.
        Falls back to Gmail SMTP if SendGrid fails or is not configured.
        """
        logger.info(f"--- EMAIL TASK STARTING: Sending invite to {to_email} ---")
        
        body_text = f"Hi {candidate_name},\n\nYou have been invited to an AI-Proctored Interview.\n\nDetails:\n- Scheduled Time: {time_str}\n- Duration: {duration_minutes} minutes\n- Link: {link}\n\nPlease click the link at the scheduled time to begin.\nNote: The link will not work before the scheduled time.\n\nGood Luck!"

        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        
        # 1. Try SendGrid First
        if sendgrid_api_key:
            try:
                logger.info(f"Attempting SendGrid API connection...")
                url = "https://api.sendgrid.com/v3/mail/send"
                headers = {
                    "Authorization": f"Bearer {sendgrid_api_key}",
                    "Content-Type": "application/json"
                }
                # from_email MUST be verified as a 'Single Sender' in SendGrid
                from_email = os.getenv("MAIL_USERNAME", "tushar@chicmicstudios.in") 
                payload = {
                    "personalizations": [
                        {
                            "to": [{"email": to_email, "name": candidate_name}],
                            "subject": "Your AI Interview Invitation"
                        }
                    ],
                    "from": {"email": from_email, "name": "AI Interview Platform"},
                    "content": [
                        {
                            "type": "text/plain",
                            "value": body_text
                        }
                    ],
                    "tracking_settings": {
                        "click_tracking": {
                            "enable": False,
                            "enable_text": False
                        }
                    }
                }
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code in [202, 201, 200]:
                    logger.info(f"SendGrid Request Successful!")
                    return True, "Success (SendGrid HTTP API)"
                else:
                    err_content = response.text
                    logger.warning(f"SendGrid API Error ({response.status_code}): {err_content}. Falling back to SMTP...")
            except Exception as sg_e:
                logger.warning(f"SendGrid Connection Failed: {sg_e}. Falling back to SMTP...")
        else:
            logger.info("No SENDGRID_API_KEY found, defaulting to SMTP...")

        # 2. Fallback to Gmail SMTP
        if not self.username or not self.password:
            logger.warning(f"MOCK MODE: No MAIL_USERNAME or MAIL_PASSWORD found. Link: {link}")
            return True, "Mock Mode: Sent successfully (simulated - Missing SMTP Credentials)"

        msg = MIMEMultipart()
        msg['From'] = f"AI Interview Platform <{self.username}>"
        msg['To'] = to_email
        msg['Subject'] = "Your AI Interview Invitation"
        
        msg.attach(MIMEText(body_text, 'plain'))

        try:
            logger.info(f"Attempting SMTP connection to {self.smtp_server}:{self.smtp_port}...")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"SMTP Email Sent Successfully!")
            return True, "Success (Gmail SMTP)"

        except Exception as e:
            err_msg = str(e)
            logger.error(f"SMTP Connection Failed: {err_msg}")
            logger.warning(f"FALLBACK MOCK LINK FOR {to_email}: {link}")
            return False, f"Delivery Failed (SendGrid & SMTP). Final Error: {err_msg}"

