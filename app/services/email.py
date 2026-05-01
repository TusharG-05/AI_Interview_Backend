import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..core.logger import get_logger
from ..core.config import MAIL_USERNAME, MAIL_PASSWORD, SMTP_HOST, SMTP_PORT, SMTP_STARTTLS, SMTP_USE_SSL

logger = get_logger(__name__)

class EmailService:
    def __init__(self):
        self.username = MAIL_USERNAME
        self.password = MAIL_PASSWORD
        self.smtp_server = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_starttls = SMTP_STARTTLS
        self.smtp_use_ssl = SMTP_USE_SSL

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

        try:
            logger.info(f"Attempting SMTP connection to {self.smtp_server}:{self.smtp_port}...")
            msg = MIMEMultipart()
            msg['From'] = f"AI Interview Platform <{self.username}>"
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

    def send_interview_invitation(self, to_email: str, candidate_name: str, link: str, time_str: str, duration_minutes: int):
        """
        Sends an email with the interview link via SMTP.
        """
        logger.info(f"--- EMAIL TASK STARTING: Sending invite to {to_email} ---")
        
        body_text = f"Hi {candidate_name},\n\nYou have been invited to an AI-Proctored Interview.\n\nDetails:\n- Scheduled Time: {time_str}\n- Duration: {duration_minutes} minutes\n- Link: {link}\n\nPlease click the link at the scheduled time to begin.\nNote: The link will not work before the scheduled time.\n\nGood Luck!"

        if self._send_smtp_email(to_email, "Your AI Interview Invitation", body_text):
            return True, "Success (SMTP)"

        logger.error(f"FINAL DELIVERY FAILURE for {to_email}")
        return False, "Delivery Failed (SMTP)"

    def send_interview_result_email(self, to_email: str, report_data: dict) -> bool:
        """
        Send interview result summary to candidate via SMTP.
        Expects `report_data` to contain keys like: candidate_name, date_str, id,
        score, max_score, status, theory_count, coding_count, admin_name,
        round_name, scheduled_time, start_time, duration_mins, proctoring_warnings
        """
        logger.info(f"--- EMAIL TASK STARTING: Sending result email to {to_email} ---")

        candidate = report_data.get("candidate_name", "Candidate")
        subject = f"Your Interview Results - {report_data.get('round_name','') or ''}".strip()

        body_lines = [
            f"Hi {candidate},",
            "",
            "Here are your interview results:",
            f"Date: {report_data.get('date_str','')}",
            f"Session ID: {report_data.get('id','')}",
            f"Score: {report_data.get('score',0)} / {report_data.get('max_score',0)}",
            f"Result: {report_data.get('status','')}",
            f"Theory Questions: {report_data.get('theory_count',0)}",
            f"Coding Questions: {report_data.get('coding_count',0)}",
            f"Round: {report_data.get('round_name','')}",
            f"Scheduled Time: {report_data.get('scheduled_time','')}",
            f"Start Time: {report_data.get('start_time','N/A')}",
            f"Duration (mins): {report_data.get('duration_mins','')}",
            f"Proctoring Warnings: {report_data.get('proctoring_warnings','0')}",
            "",
            f"Admin: {report_data.get('admin_name','Platform Admin')}",
            "",
            "Thank you for participating. If you have any questions, contact the admin.",
        ]

        body_text = "\n".join(body_lines)

        sent = self._send_smtp_email(to_email, subject, body_text)
        if not sent:
            logger.error(f"Result email delivery failed for {to_email}")
            return False

        logger.info(f"Result email sent to {to_email}")
        return True

    def send_otp_email(self, to_email: str, otp: str):
        """
        Sends an OTP code for candidate login via SMTP.
        """
        logger.info(f"--- EMAIL TASK STARTING: Sending OTP to {to_email} ---")
        
        body_text = f"Your Verification Code for AI Interview Login is:\n\n{otp}\n\nThis code is valid for 10 minutes.\n\nIf you did not request this, please ignore this email."

        if self._send_smtp_email(to_email, f"{otp} is your verification code", body_text):
            return True

        logger.error(f"FINAL OTP DELIVERY FAILURE for {to_email}")
        return False
