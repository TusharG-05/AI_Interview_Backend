import cloudinary
import cloudinary.uploader
from ..core.config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
import logging

logger = logging.getLogger(__name__)

# Configure cloudinary
# The cloudinary library automatically picks up CLOUDINARY_URL from the environment.
# cloudinary.config() is not required if CLOUDINARY_URL is set.

class CloudinaryService:
    def upload_image(self, file_content: bytes, folder: str = "interview_selfies") -> str:
        """
        Uploads image content to Cloudinary and returns the secure URL.
        """
        try:
            upload_result = cloudinary.uploader.upload(
                file_content,
                folder=folder,
                resource_type="image"
            )
            return upload_result.get("secure_url")
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            raise e

    def upload_resume(self, file_content: bytes, folder: str = "resumes") -> str:
        """
        Uploads resume (PDF) to Cloudinary and returns the secure URL.
        """
        try:
            import uuid
            # Using a public_id with .pdf extension often helps Cloudinary "auto" detection
            public_id = f"resume_{uuid.uuid4().hex}.pdf"
            upload_result = cloudinary.uploader.upload(
                file_content,
                folder=folder,
                public_id=public_id,
                resource_type="auto",
                overwrite=True
            )
            return upload_result.get("secure_url")
        except Exception as e:
            logger.error(f"Cloudinary resume upload failed: {e}")
            raise e
