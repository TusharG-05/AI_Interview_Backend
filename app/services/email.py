import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..core.logger import get_logger
from ..core.config import MAIL_USERNAME, MAIL_PASSWORD

logger = get_logger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.username = MAIL_USERNAME
        self.password = MAIL_PASSWORD

    def send_interview_invitation(self, to_email: str, candidate_name: str, link: str, time_str: str, duration_minutes: int):
        """
        Sends an email with the interview link. 
        Tries Port 465 (SSL) first, then 587 (TLS) as fallback.
        """
        logger.info(f"--- EMAIL TASK STARTING: Sending invite to {to_email} ---")
        # Refresh credentials from environment in case they were added after startup
        from ..core.config import MAIL_USERNAME, MAIL_PASSWORD
        user = MAIL_USERNAME or os.getenv("MAIL_USERNAME")
        password = MAIL_PASSWORD or os.getenv("MAIL_PASSWORD")

        if not user or not password or "example" in user:
            logger.warning(f"MOCK MODE: No valid credentials for {to_email}. Link: {link}")
            return True

        msg = MIMEMultipart()
        msg["From"] = user
        msg["To"] = to_email
        msg["Subject"] = "Your AI Interview Invitation"
        body = f"""Hi {candidate_name},

You have been invited to an AI-Proctored Interview.

Details:
- Scheduled Time: {time_str}
- Duration: {duration_minutes} minutes
- Link: {link}

Please click the link at the scheduled time to begin.
Note: The link will not work before the scheduled time.

Good Luck!"""
        msg.attach(MIMEText(body, "plain"))

        # Try Port 465 (SSL) first - more reliable in many cloud environments
        try:
            logger.info(f"Attempting email to {to_email} via Port 465 (SSL)...")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
                server.login(user, password)
                server.sendmail(user, to_email, msg.as_string())
            logger.info(f"Email sent successfully via 465 to {to_email}")
            return True
        except Exception as e465:
            logger.warning(f"Port 465 failed: {e465}. Trying Port 587 (TLS)...")
            
            # Fallback to Port 587 (TLS)
            try:
                with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
                    server.starttls()
                    server.login(user, password)
                    server.sendmail(user, to_email, msg.as_string())
                logger.info(f"Email sent successfully via 587 to {to_email}")
                return True
            except Exception as e587:
                logger.error(f"All SMTP methods failed. 465: {e465}, 587: {e587}")
                logger.warning(f"FALLBACK MOCK LINK FOR {to_email}: {link}")
                return False
