import cloudinary
import cloudinary.uploader
from ..core.config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
import logging
import uuid
from typing import BinaryIO, Union

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

    def upload_resume(self, file_content: Union[bytes, BinaryIO], folder: str = "resumes") -> str:
        """
        Uploads resume (PDF) to Cloudinary as a 'raw' resource and returns the secure URL.
        """
        try:
            # 1. Prepare the bytes correctly
            if hasattr(file_content, "read"):
                try:
                    file_content.seek(0)
                except Exception:
                    # Some file-like objects don't support seek; we handle it gracefully
                    pass
                file_bytes = file_content.read()
            else:
                file_bytes = file_content

            # 2. Use .pdf extension so browsers recognize the file type
            if filename and filename.endswith(".pdf"):
                public_id = filename.replace(".pdf", "")
            else:
                unique_id = uuid.uuid4().hex
                public_id = f"resume_{unique_id}"

            # 3. Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file_bytes,
                folder=folder,
                public_id=public_id,
                resource_type="raw",
                overwrite=True
            )
            
            # 4. Extract and return the direct clickable link
            secure_url = upload_result.get("secure_url")
            
            if not secure_url:
                logger.error("Cloudinary upload succeeded but no secure_url was returned.")
                return ""

            return secure_url

        except Exception as e:
            logger.error(f"Cloudinary resume upload failed: {str(e)}")
            # Raise the exception so the API endpoint can catch it and return a 500 error
            raise e
