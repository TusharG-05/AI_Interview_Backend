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

    def _send_smtp_email(self, to_email: str, subject: str, body_text: str) -> bool:
        """Helper to send email via SMTP with robust logging."""
        if not self.username or not self.password:
            logger.warning("SMTP credentials missing (MAIL_USERNAME or MAIL_PASSWORD).")
            return False

        try:
            logger.info(f"Attempting SMTP connection to {self.smtp_server}:{self.smtp_port}...")
            msg = MIMEMultipart()
            msg['From'] = f"AI Interview Platform <{self.username}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body_text, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15)
            server.starttls()
            try:
                server.login(self.username, self.password)
            except smtplib.SMTPAuthenticationError as auth_err:
                logger.error(f"SMTP Authentication Failed for {self.username}. "
                             f"Error: {auth_err.smtp_code} {auth_err.smtp_error.decode() if isinstance(auth_err.smtp_error, bytes) else auth_err.smtp_error}")
                if "gmail.com" in self.smtp_server:
                    logger.error("TIP: If using Gmail, ensure you are using an 'App Password' if 2FA is enabled. "
                                 "Regular passwords will NOT work.")
                return False

            server.send_message(msg)
            server.quit()
            logger.info(f"SMTP Email Sent Successfully to {to_email}")
            return True
        except Exception as e:
            logger.warning(f"SMTP connection/delivery failed: {e}")
            return False

    def send_interview_invitation(self, to_email: str, candidate_name: str, link: str, time_str: str, duration_minutes: int):
        """
        Sends an email with the interview link. 
        Priority: 
        1. Gmail SMTP (Primary)
        2. SendGrid API (Fallback)
        """
        logger.info(f"--- EMAIL TASK STARTING: Sending invite to {to_email} ---")
        
        body_text = f"Hi {candidate_name},\n\nYou have been invited to an AI-Proctored Interview.\n\nDetails:\n- Scheduled Time: {time_str}\n- Duration: {duration_minutes} minutes\n- Link: {link}\n\nPlease click the link at the scheduled time to begin.\nNote: The link will not work before the scheduled time.\n\nGood Luck!"

        # 1. Try Gmail SMTP First
        if self._send_smtp_email(to_email, "Your AI Interview Invitation", body_text):
            return True, "Success (Gmail SMTP)"
        
        logger.info("SMTP failed, attempting SendGrid fallback...")

        # 2. Fallback to SendGrid API
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        if sendgrid_api_key:
            try:
                logger.info("Attempting SendGrid API connection...")
                url = "https://api.sendgrid.com/v3/mail/send"
                headers = {
                    "Authorization": f"Bearer {sendgrid_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "personalizations": [{"to": [{"email": to_email, "name": candidate_name}], "subject": "Your AI Interview Invitation"}],
                    "from": {"email": os.getenv("MAIL_USERNAME", "tushar@chicmicstudios.in"), "name": "AI Interview Platform"},
                    "content": [{"type": "text/plain", "value": body_text}]
                }
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                if response.status_code in [202, 201, 200]:
                    logger.info("SendGrid Request Successful!")
                    return True, "Success (SendGrid HTTP API)"
                else:
                    logger.warning(f"SendGrid API Error ({response.status_code}): {response.text}")
            except Exception as sg_e:
                logger.error(f"SendGrid Connection Failed: {sg_e}")
        
        logger.error(f"FINAL DELIVERY FAILURE for {to_email}")
        return False, "Delivery Failed (Both SMTP and SendGrid)"

    def send_otp_email(self, to_email: str, otp: str):
        """
        Sends an OTP code for candidate login.
        Priority:
        1. Gmail SMTP (Primary)
        2. SendGrid API (Fallback)
        """
        logger.info(f"--- EMAIL TASK STARTING: Sending OTP to {to_email} ---")
        
        body_text = f"Your Verification Code for AI Interview Login is:\n\n{otp}\n\nThis code is valid for 10 minutes.\n\nIf you did not request this, please ignore this email."

        # 1. Try Gmail SMTP First
        if self._send_smtp_email(to_email, f"{otp} is your verification code", body_text):
            return True

        logger.info("SMTP failed, attempting SendGrid fallback...")

        # 2. Fallback to SendGrid API
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        if sendgrid_api_key:
            try:
                url = "https://api.sendgrid.com/v3/mail/send"
                headers = {
                    "Authorization": f"Bearer {sendgrid_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "personalizations": [{"to": [{"email": to_email}], "subject": f"{otp} is your verification code"}],
                    "from": {"email": os.getenv("MAIL_USERNAME", "tushar@chicmicstudios.in"), "name": "AI Interview Platform"},
                    "content": [{"type": "text/plain", "value": body_text}]
                }
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                if response.status_code in [202, 201, 200]:
                    logger.info("SendGrid OTP Sent Successfully!")
                    return True
            except Exception as sg_e:
                logger.error(f"SendGrid OTP Failed: {sg_e}")

        logger.error(f"FINAL OTP DELIVERY FAILURE for {to_email}")
        return False
