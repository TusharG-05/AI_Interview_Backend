"""
S3 Service for PDF uploads - Alternative to Cloudinary for documents.
Requires: pip install boto3
"""
import boto3
from botocore.exceptions import ClientError
import logging
from ..core.config import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_S3_BUCKET, AWS_REGION

logger = logging.getLogger(__name__)


class S3Service:
    """Handles PDF and document uploads to AWS S3."""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION or 'us-east-1'
        )
        self.bucket = AWS_S3_BUCKET
    
    def upload_pdf(self, file_content: bytes, key: str) -> str:
        """
        Upload PDF to S3 and return public URL.
        
        Args:
            file_content: PDF bytes
            key: S3 key/path (e.g., "resumes/user_123.pdf")
        
        Returns:
            Public URL of uploaded file
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_content,
                ContentType='application/pdf',
                ACL='public-read'
            )
            url = f"https://{self.bucket}.s3.{AWS_REGION}.amazonaws.com/{key}"
            logger.info(f"PDF uploaded to S3: {url}")
            return url
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise e
    
    def delete_file(self, key: str) -> bool:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            return False
