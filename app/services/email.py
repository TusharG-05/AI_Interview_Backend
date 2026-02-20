import os
import resend
from ..core.logger import get_logger
from ..core.config import MAIL_USERNAME

logger = get_logger(__name__)

class EmailService:
    def __init__(self):
        # We still pull MAIL_USERNAME to act as the 'From' or fallback
        self.username = MAIL_USERNAME
        
    def send_interview_invitation(self, to_email: str, candidate_name: str, link: str, time_str: str, duration_minutes: int):
        """
        Sends an email with the interview link using Resend HTTP API.
        """
        logger.info(f"--- EMAIL TASK STARTING: Sending invite to {to_email} via Resend ---")
        
        # Load API key directly from environment for maximum safety
        resend_api_key = os.getenv("RESEND_API_KEY")
        
        if not resend_api_key:
            logger.warning(f"MOCK MODE: No RESEND_API_KEY found. Link: {link}")
            return True, "Mock Mode: Sent successfully (simulated - No API Key)"
            
        resend.api_key = resend_api_key

        body = f"""Hi {candidate_name},

You have been invited to an AI-Proctored Interview.

Details:
- Scheduled Time: {time_str}
- Duration: {duration_minutes} minutes
- Link: {link}

Please click the link at the scheduled time to begin.
Note: The link will not work before the scheduled time.

Good Luck!"""

        # Resend free tier requires the sender to be onboarding@resend.dev 
        # unless a custom domain is verified.
        from_email = "onboarding@resend.dev"

        params = {
            "from": f"AI Interview Platform <{from_email}>",
            "to": [to_email],
            "subject": "Your AI Interview Invitation",
            "text": body,
        }

        try:
            logger.info(f"Attempting Resend API call to {to_email}...")
            email_response = resend.Emails.send(params)
            logger.info(f"Resend Request Successful! ID: {email_response.get('id', 'unknown')}")
            return True, "Success (Resend HTTP API)"
        except Exception as e:
            err_msg = f"Resend API Failed: {str(e)}"
            logger.error(err_msg)
            logger.warning(f"FALLBACK MOCK LINK FOR {to_email}: {link}")
            return False, err_msg
