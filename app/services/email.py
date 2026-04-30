import ssl
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..core.logger import get_logger
from ..core.config import (
    MAIL_USERNAME,
    MAIL_PASSWORD,
    BREVO_SENDER_EMAIL,
    MAIL_FROM_NAME,
    BREVO_API_KEY,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_STARTTLS,
    SMTP_USE_SSL,
)

logger = get_logger(__name__)

class EmailService:
    def __init__(self):
        self.username = MAIL_USERNAME
        self.password = MAIL_PASSWORD
        self.sender_email = BREVO_SENDER_EMAIL
        self.sender_name = MAIL_FROM_NAME
        self.smtp_server = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_starttls = SMTP_STARTTLS
        self.smtp_use_ssl = SMTP_USE_SSL

    def _get_sender_email(self) -> str:
        sender_email = self.sender_email or self.username
        if not sender_email:
            return ""

        if sender_email.endswith("@smtp-brevo.com"):
            logger.error(
                "Invalid email sender configured: %s. Set BREVO_SENDER_EMAIL or MAIL_FROM_EMAIL to a validated sender address.",
                sender_email,
            )
            return ""

        return sender_email

    def _create_smtp_client(self):
        if self.smtp_use_ssl:
            return smtplib.SMTP_SSL(
                self.smtp_server,
                self.smtp_port,
                timeout=15,
                context=ssl.create_default_context(),
            )

        server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15)
        if self.smtp_starttls:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
        return server

    def _send_smtp_email(self, to_email: str, subject: str, body_text: str) -> bool:
        """Helper to send email via SMTP with robust logging."""
        if not self.username or not self.password:
            logger.warning("SMTP credentials missing (MAIL_USERNAME or MAIL_PASSWORD).")
            return False

        sender_email = self._get_sender_email()
        if not sender_email:
            return False

        try:
            logger.info(f"Attempting SMTP connection to {self.smtp_server}:{self.smtp_port}...")
            msg = MIMEMultipart()
            msg['From'] = f"{self.sender_name} <{sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body_text, 'plain'))

            server = self._create_smtp_client()
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
            logger.warning(
                f"SMTP connection/delivery failed ({self.smtp_server}:{self.smtp_port}, starttls={self.smtp_starttls}, ssl={self.smtp_use_ssl}): {e}"
            )
            return False

    def _send_brevo_email(self, to_email: str, subject: str, body_text: str) -> bool:
        """Fallback email delivery using Brevo's HTTP API."""
        if not BREVO_API_KEY:
            logger.warning("Brevo API key missing (BREVO_API_KEY).")
            return False

        sender_email = self._get_sender_email()
        if not sender_email:
            logger.warning("Brevo fallback skipped because no valid sender email is configured.")
            return False

        payload = {
            "sender": {"name": self.sender_name, "email": sender_email},
            "to": [{"email": to_email}],
            "subject": subject,
            "textContent": body_text,
        }

        try:
            logger.info(f"Attempting Brevo HTTP email delivery to {to_email}...")
            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key": BREVO_API_KEY,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=15,
            )
            
            logger.info(f"Brevo HTTP response: status={response.status_code}")
            
            if response.status_code in (200, 201, 202):
                logger.info(f"Brevo Email Sent Successfully to {to_email} (status: {response.status_code})")
                if response.text:
                    logger.debug(f"Brevo response body: {response.text[:200]}")
                return True

            logger.warning(
                f"Brevo delivery failed for {to_email}: HTTP {response.status_code}\nResponse: {response.text[:500]}"
            )
            return False
        except requests.exceptions.Timeout as te:
            logger.warning(f"Brevo delivery timeout for {to_email}: {te}")
            return False
        except Exception as e:
            logger.warning(f"Brevo delivery exception for {to_email}: {type(e).__name__}: {e}")
            return False

    def _send_email_with_fallbacks(self, to_email: str, subject: str, body_text: str) -> tuple[bool, str]:
        if self._send_smtp_email(to_email, subject, body_text):
            return True, "Success (SMTP)"

        if self._send_brevo_email(to_email, subject, body_text):
            return True, "Success (Brevo)"

        return False, "Delivery Failed (SMTP + Brevo)"

    def send_interview_invitation(self, to_email: str, candidate_name: str, link: str, time_str: str, duration_minutes: int):
        """
        Sends an email with the interview link via SMTP.
        """
        logger.info(f"--- EMAIL TASK STARTING: Sending invite to {to_email} ---")
        
        body_text = f"Hi {candidate_name},\n\nYou have been invited to an AI-Proctored Interview.\n\nDetails:\n- Scheduled Time: {time_str}\n- Duration: {duration_minutes} minutes\n- Link: {link}\n\nPlease click the link at the scheduled time to begin.\nNote: The link will not work before the scheduled time.\n\nGood Luck!"

        success, message = self._send_email_with_fallbacks(to_email, "Your AI Interview Invitation", body_text)
        if success:
            return True, message

        logger.error(f"FINAL DELIVERY FAILURE for {to_email}")
        return False, message

    def send_otp_email(self, to_email: str, otp: str):
        """
        Sends an OTP code for candidate login via SMTP.
        """
        logger.info(f"--- EMAIL TASK STARTING: Sending OTP to {to_email} ---")
        
        body_text = f"Your Verification Code for AI Interview Login is:\n\n{otp}\n\nThis code is valid for 10 minutes.\n\nIf you did not request this, please ignore this email."

        success, _message = self._send_email_with_fallbacks(to_email, f"{otp} is your verification code", body_text)
        if success:
            return True

        logger.error(f"FINAL OTP DELIVERY FAILURE for {to_email}")
        return False
