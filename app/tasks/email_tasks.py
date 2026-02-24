from ..core.celery_app import celery_app
from ..services.email import EmailService
import logging

logger = logging.getLogger(__name__)
email_service = EmailService()

@celery_app.task(name="app.tasks.email_tasks.send_interview_invitation_task", bind=True, max_retries=3)
def send_interview_invitation_task(self, to_email: str, candidate_name: str, link: str, time_str: str, duration_minutes: int):
    """
    Celery task to send interview invitations.
    """
    logger.info(f"Executing Celery task: Sending invite to {to_email}")
    try:
        success, message = email_service.send_interview_invitation(
            to_email=to_email,
            candidate_name=candidate_name,
            link=link,
            time_str=time_str,
            duration_minutes=duration_minutes
        )
        if not success:
            raise Exception(message)
        return {"status": "success", "message": message}
    except Exception as exc:
        logger.error(f"Error sending email to {to_email}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
