import boto3
import os
import uuid
import logging
from typing import Optional
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
import io

load_dotenv()

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        """Initialize S3 service with AWS credentials and configuration."""
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("AWS_S3_BUCKET_NAME")

        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.bucket_name]):
            logger.warning("AWS credentials or bucket name not configured")
            self.s3_client = None
            return

        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            logger.info(f"S3 service initialized for bucket: {self.bucket_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            self.s3_client = None
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            self.s3_client = None

    def is_available(self) -> bool:
        """Check if S3 service is available and configured."""
        return self.s3_client is not None

    async def upload_page_image(
        self,
        image_data: bytes,
        book_id: int,
        page_number: int,
        file_format: str = "png"
    ) -> Optional[str]:
        """
        Upload a page image to S3.

        Args:
            image_data: The image data as bytes
            book_id: ID of the book
            page_number: Page number
            file_format: Image format (png, jpg, etc.)

        Returns:
            The S3 URL of the uploaded image, or None if failed
        """
        if not self.is_available():
            logger.error("S3 service not available")
            return None

        try:
            # Generate unique filename
            image_id = str(uuid.uuid4())
            key = f"pages/book_{book_id}/page_{page_number}_{image_id}.{file_format}"

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=image_data,
                ContentType=f"image/{file_format}",
                CacheControl="max-age=31536000",  # Cache for 1 year
                Metadata={
                    'book_id': str(book_id),
                    'page_number': str(page_number),
                    'format': file_format
                }
            )

            # Generate public URL
            url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{key}"
            logger.info(f"Successfully uploaded page image: {url}")
            return url

        except ClientError as e:
            logger.error(f"AWS S3 error uploading page image: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error uploading page image to S3: {str(e)}")
            return None

    async def delete_page_image(self, image_url: str) -> bool:
        """
        Delete a page image from S3.

        Args:
            image_url: The S3 URL of the image to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.is_available():
            logger.error("S3 service not available")
            return False

        try:
            # Extract key from URL
            if not image_url.startswith(f"https://{self.bucket_name}.s3."):
                logger.error(f"Invalid S3 URL format: {image_url}")
                return False

            # Extract key from URL
            key = image_url.split(f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/")[1]

            # Delete from S3
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )

            logger.info(f"Successfully deleted page image: {image_url}")
            return True

        except ClientError as e:
            logger.error(f"AWS S3 error deleting page image: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error deleting page image from S3: {str(e)}")
            return False

    async def upload_multiple_page_images(
        self,
        images_data: list,
        book_id: int,
        file_format: str = "png"
    ) -> list:
        """
        Upload multiple page images to S3 in batch.

        Args:
            images_data: List of tuples (page_number, image_bytes)
            book_id: ID of the book
            file_format: Image format

        Returns:
            List of tuples (page_number, url) for successful uploads
        """
        if not self.is_available():
            logger.error("S3 service not available")
            return []

        results = []

        for page_number, image_data in images_data:
            try:
                url = await self.upload_page_image(
                    image_data, book_id, page_number, file_format
                )
                if url:
                    results.append((page_number, url))
                    logger.info(f"Uploaded image for page {page_number}")
                else:
                    logger.error(f"Failed to upload image for page {page_number}")

            except Exception as e:
                logger.error(f"Error uploading image for page {page_number}: {str(e)}")
                continue

        logger.info(f"Successfully uploaded {len(results)} out of {len(images_data)} page images")
        return results

    def get_bucket_info(self) -> dict:
        """
        Get information about the S3 bucket configuration.

        Returns:
            Dictionary with bucket information
        """
        return {
            "available": self.is_available(),
            "bucket_name": self.bucket_name,
            "region": self.aws_region,
            "configured": bool(self.aws_access_key_id and self.aws_secret_access_key and self.bucket_name)
        }

# Global instance
s3_service = S3Service()