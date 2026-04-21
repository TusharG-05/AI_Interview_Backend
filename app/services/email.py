import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..core.logger import get_logger
from ..core.config import MAIL_USERNAME, MAIL_PASSWORD, SMTP_HOST, SMTP_PORT, SMTP_STARTTLS
from ..utils.email_templates import get_invite_template, get_otp_template, get_result_template

logger = get_logger(__name__)

class EmailService:
    def __init__(self):
        self.username = MAIL_USERNAME
        self.password = MAIL_PASSWORD
        self.smtp_server = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_starttls = SMTP_STARTTLS

    def _send_smtp_email(self, to_email: str, subject: str, body_text: str, html_body: str = None) -> bool:
        """Helper to send email via SMTP with robust logging."""
        if not self.username or not self.password:
            logger.warning("SMTP credentials missing (MAIL_USERNAME or MAIL_PASSWORD).")
            return False

        try:
            logger.info(f"Attempting SMTP connection to {self.smtp_server}:{self.smtp_port}...")
            msg = MIMEMultipart('alternative')
            msg['From'] = f"AI Interview Platform <{self.username}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body_text, 'plain'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15)
            if self.smtp_starttls:
                server.starttls()
            try:
                server.login(self.username, self.password)
            except smtplib.SMTPAuthenticationError as auth_err:
                logger.error(f"SMTP Authentication Failed for {self.username}. "
                             f"Error: {auth_err.smtp_code} {auth_err.smtp_error.decode() if isinstance(auth_err.smtp_error, bytes) else auth_err.smtp_error}")
                return False

            server.send_message(msg)
            server.quit()
            logger.info(f"SMTP Email Sent Successfully to {to_email}")
            return True
        except Exception as e:
            logger.warning(
                f"SMTP connection/delivery failed ({self.smtp_server}:{self.smtp_port}, starttls={self.smtp_starttls}): {e}"
            )
            return False

    def send_interview_invitation(self, to_email: str, candidate_name: str, link: str, time_str: str, duration_minutes: int):
        """
        Sends a plain text interview invitation.
        """
        logger.info(f"--- EMAIL TASK STARTING: Sending invite to {to_email} ---")
        
        body_text = f"Hi {candidate_name},\n\nYou have been invited to an AI-Proctored Interview.\n\nDetails:\n- Scheduled Time: {time_str}\n- Duration: {duration_minutes} minutes\n- Link: {link}\n\nPlease click the link at the scheduled time to begin.\n\nGood Luck!"
        html_body = get_invite_template(candidate_name, time_str, duration_minutes, link)

        if self._send_smtp_email(to_email, "Your AI Interview Invitation", body_text, html_body=html_body):
            return True, "Success (SMTP)"

        return False, "Delivery Failed (SMTP)"

    def send_otp_email(self, to_email: str, otp: str):
        """
        Sends a plain text OTP code.
        """
        logger.info(f"--- EMAIL TASK STARTING: Sending OTP to {to_email} ---")
        
        body_text = f"Your Verification Code for AI Interview Login is: {otp}\n\nThis code is valid for 10 minutes."
        html_body = get_otp_template(otp)

        if self._send_smtp_email(to_email, f"{otp} is your verification code", body_text, html_body=html_body):
            return True

        return False

    def send_interview_result_email(self, to_email: str, result_data: dict):
        """
        Sends a plain text interview result report.
        """
        logger.info(f"--- EMAIL TASK STARTING: Sending Result to {to_email} ---")
        
        candidate_name = result_data.get('candidate_name', 'Candidate')
        score = result_data.get('score', 0)
        status = result_data.get('status', 'COMPLETED')
        
        body_text = f"""Hi {candidate_name},

Your AI Interview results are now available. Please find your performance summary below:

---

📊 Candidate Report
Name: {candidate_name}
Status: Completed

---

📈 Overall Performance
Score: {score} / {result_data.get('max_score', 0)}
Result Status: {'❌' if status.upper() == 'FAIL' else '✅'} {status}

---

🧠 Assessment Details
Theory Sections: {result_data.get('theory_count', 0)} questions attempted
Coding Challenges: {result_data.get('coding_count', 0)} challenges attempted

---

🗂️ Session Details
Interviewer: {result_data.get('admin_name', 'N/A')}
Interview Round: {result_data.get('round_name', 'N/A')}
Scheduled Time: {result_data.get('scheduled_time', 'N/A')}
Start Time: {result_data.get('start_time', 'N/A')}
Duration: {result_data.get('duration_mins', 0)} minutes
Proctoring Warnings: {result_data.get('proctoring_warnings', '0 / 3')}

---

If you believe this result is incorrect or need assistance, please contact the support team.

Best regards,
AI Interview Platform Team

---

© 2026 AI Interview Platform. All rights reserved.
If you did not expect this email, please ignore it."""
        html_body = get_result_template(result_data)

        if self._send_smtp_email(to_email, "Your AI Interview Results", body_text, html_body=html_body):
            return True, "Success (SMTP)"

        return False, "Delivery Failed (SMTP)"
