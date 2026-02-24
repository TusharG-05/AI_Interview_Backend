import os
import requests
from ..core.logger import get_logger
from ..core.config import MAIL_USERNAME

logger = get_logger(__name__)

class EmailService:
    def __init__(self):
        # We still pull MAIL_USERNAME to act as the 'From' or fallback
        self.username = MAIL_USERNAME
        
    def send_interview_invitation(self, to_email: str, candidate_name: str, link: str, time_str: str, duration_minutes: int):
        """
        Sends an email with the interview link using SendGrid v3 HTTP API.
        """
        logger.info(f"--- EMAIL TASK STARTING: Sending invite to {to_email} via SendGrid ---")
        
        # Load API key directly from environment
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        
        if not sendgrid_api_key:
            logger.warning(f"MOCK MODE: No SENDGRID_API_KEY found. Link: {link}")
            return True, "Mock Mode: Sent successfully (simulated - No API Key)"

        # SendGrid API Endpoint
        url = "https://api.sendgrid.com/v3/mail/send"

        body_text = f"""Hi {candidate_name},

You have been invited to an AI-Proctored Interview.

Details:
- Scheduled Time: {time_str}
- Duration: {duration_minutes} minutes
- Link: {link}

Please click the link at the scheduled time to begin.
Note: The link will not work before the scheduled time.

Good Luck!"""

        # SendGrid Headers
        headers = {
            "Authorization": f"Bearer {sendgrid_api_key}",
            "Content-Type": "application/json"
        }

        # SendGrid Payload
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
            ]
        }

        try:
            logger.info(f"Attempting SendGrid API call to {to_email}...")
            response = requests.post(url, json=payload, headers=headers)
            
            # SendGrid returns 202 Accepted on success
            if response.status_code in [202, 201, 200]:
                logger.info(f"SendGrid Request Successful!")
                return True, "Success (SendGrid HTTP API)"
            else:
                err_content = response.text
                logger.error(f"SendGrid API Error ({response.status_code}): {err_content}")
                
                # Check for common verification issues
                if "sender" in err_content.lower() or "forbidden" in err_content.lower():
                    logger.warning("--- PRODUCTION NOTICE: SENDGRID SENDER NOT VERIFIED ---")
                    logger.warning(f"You must verify '{from_email}' in SendGrid > Settings > Sender Authentication.")
                    logger.warning(f"BYPASS LINK FOR TESTING: {link}")
                    return False, f"SendGrid Restriction: Sender not verified. Use this link: {link}"
                
                return False, f"SendGrid API Failed ({response.status_code}): {err_content}"

        except Exception as e:
            err_msg = str(e)
            logger.error(f"SendGrid Connection Failed: {err_msg}")
            logger.warning(f"FALLBACK MOCK LINK FOR {to_email}: {link}")
            return False, f"SendGrid Error: {err_msg}"
