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
        Falls back to Mock Mode (Logging) if credentials are removed.
        """
        if not self.username or not self.password or "example" in self.username:
            logger.warning(f"MOCK EMAIL TO {to_email}:")
            logger.warning(f"Subject: Interview Invitation")
            logger.warning(f"Link: {link}")
            logger.warning(f"Time: {time_str}")
            return True

        try:
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = to_email
            msg["Subject"] = "Your AI Interview Invitation"

            body = f"""
            Hi {candidate_name},

            You have been invited to an AI-Proctored Interview.

            Details:
            - Scheduled Time: {time_str}
            - Duration: {duration_minutes} minutes
            - Link: {link}

            Please click the link at the scheduled time to begin.
            Note: The link will not work before the scheduled time.

            Good Luck!
            """
            
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.username, to_email, msg.as_string())
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            logger.warning(f"FALLBACK MOCK LINK: {link}")
            return False
