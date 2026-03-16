import cloudinary
import cloudinary.uploader
from ..core.config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
import logging

logger = logging.getLogger(__name__)

# Configure cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

class CloudinaryService:
    def upload_image(self, file_content: bytes, folder: str = "interview_selfies") -> str:
        """
        Uploads image content to Cloudinary and returns the secure URL.
        """
        try:
            upload_result = cloudinary.uploader.upload(
                file_content,
                folder=folder
            )
            return upload_result.get("secure_url")
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            raise e
    
    def upload_pdf(self, file_content: bytes, folder: str = "resumes", filename: str = None) -> str:
        """
        Uploads PDF as raw file to Cloudinary and returns the secure URL.
        Note: Cloudinary free tier has limitations on raw files.
        """
        try:
            upload_result = cloudinary.uploader.upload(
                file_content,
                folder=folder,
                resource_type="raw",  # Required for PDFs
                public_id=filename.replace(".pdf", "") if filename else None
            )
            return upload_result.get("secure_url")
        except Exception as e:
            logger.error(f"Cloudinary PDF upload failed: {e}")
            raise e
