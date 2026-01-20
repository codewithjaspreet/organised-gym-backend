"""
Cloudinary utility module for image upload and management.
Follows SOLID principles with separation of concerns.
"""
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from typing import Optional, Dict, Any, BinaryIO
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import ValidationError


class CloudinaryConfig:
    """Single Responsibility: Manages Cloudinary configuration"""
    
    @staticmethod
    def initialize() -> None:
        """Initialize Cloudinary configuration from environment variables"""
        # Prefer explicit vars if present (you added all 4 in .env)
        if (
            settings.cloudinary_cloud_name
            and settings.cloudinary_cloud_api_key
            and settings.cloudinary_cloud_api_secret
        ):
            cloudinary.config(
                cloud_name=settings.cloudinary_cloud_name,
                api_key=settings.cloudinary_cloud_api_key,
                api_secret=settings.cloudinary_cloud_api_secret,
                secure=True,
            )
            return

        # Fallback to CLOUDINARY_URL parsing
        if not settings.cloudinary_url:
            raise ValueError(
                "Cloudinary env not set. Provide CLOUDINARY_CLOUD_NAME, "
                "CLOUDINARY_CLOUD_API_KEY, CLOUDINARY_CLOUD_API_SECRET (preferred) "
                "or CLOUDINARY_URL."
            )

        try:
            cloudinary.config(
                cloud_name=CloudinaryConfig._extract_cloud_name(settings.cloudinary_url),
                api_key=CloudinaryConfig._extract_api_key(settings.cloudinary_url),
                api_secret=CloudinaryConfig._extract_api_secret(settings.cloudinary_url),
                secure=True,
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Cloudinary configuration: {str(e)}")
    
    @staticmethod
    def _extract_cloud_name(cloudinary_url: str) -> str:
        """Extract cloud name from Cloudinary URL"""
        # Format: cloudinary://api_key:api_secret@cloud_name
        try:
            parts = cloudinary_url.split("@")
            if len(parts) != 2:
                raise ValueError("Invalid CLOUDINARY_URL format: missing @ separator")
            return parts[1].strip()
        except Exception as e:
            raise ValueError(f"Failed to extract cloud name: {str(e)}")
    
    @staticmethod
    def _extract_api_key(cloudinary_url: str) -> str:
        """Extract API key from Cloudinary URL"""
        # Format: cloudinary://api_key:api_secret@cloud_name
        try:
            if not cloudinary_url.startswith("cloudinary://"):
                raise ValueError("Invalid CLOUDINARY_URL format: must start with cloudinary://")
            
            # Remove protocol prefix
            without_protocol = cloudinary_url.replace("cloudinary://", "")
            
            # Split by @ to get credentials part
            credentials_part = without_protocol.split("@")[0]
            
            # Split by : to get api_key and api_secret
            key_secret = credentials_part.split(":")
            if len(key_secret) < 2:
                raise ValueError("Invalid CLOUDINARY_URL format: missing api_key or api_secret")
            
            return key_secret[0].strip()
        except Exception as e:
            raise ValueError(f"Failed to extract API key: {str(e)}")
    
    @staticmethod
    def _extract_api_secret(cloudinary_url: str) -> str:
        """Extract API secret from Cloudinary URL"""
        # Format: cloudinary://api_key:api_secret@cloud_name
        try:
            if not cloudinary_url.startswith("cloudinary://"):
                raise ValueError("Invalid CLOUDINARY_URL format: must start with cloudinary://")
            
            # Remove protocol prefix
            without_protocol = cloudinary_url.replace("cloudinary://", "")
            
            # Split by @ to get credentials part
            credentials_part = without_protocol.split("@")[0]
            
            # Split by : to get api_key and api_secret
            key_secret = credentials_part.split(":")
            if len(key_secret) < 2:
                raise ValueError("Invalid CLOUDINARY_URL format: missing api_secret")
            
            # Join all parts after the first colon in case secret contains colons
            secret = ":".join(key_secret[1:])
            return secret.strip()
        except Exception as e:
            raise ValueError(f"Failed to extract API secret: {str(e)}")


class ImageUploader:
    """Single Responsibility: Handles image upload operations"""
    
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_file(file: UploadFile) -> None:
        """Validate uploaded file before processing"""
        if not file.filename:
            raise ValidationError(detail="File name is required")
        
        # Check file extension
        file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if file_extension not in ImageUploader.ALLOWED_EXTENSIONS:
            raise ValidationError(
                detail=f"File type not allowed. Allowed types: {', '.join(ImageUploader.ALLOWED_EXTENSIONS)}"
            )
        
        # Check content type
        if file.content_type and not file.content_type.startswith("image/"):
            raise ValidationError(detail="File must be an image")
    
    @staticmethod
    async def upload_file(
        file: UploadFile,
        folder: Optional[str] = None,
        public_id: Optional[str] = None,
        transformation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Cloudinary
        
        Args:
            file: FastAPI UploadFile object
            folder: Optional folder path in Cloudinary
            public_id: Optional public ID for the uploaded file
            transformation: Optional transformation parameters
        
        Returns:
            Dictionary containing upload result with secure_url
        """
        ImageUploader.validate_file(file)
        
        # Read file content
        file_content = await file.read()
        
        # Check file size
        if len(file_content) > ImageUploader.MAX_FILE_SIZE:
            raise ValidationError(detail=f"File size exceeds maximum allowed size of {ImageUploader.MAX_FILE_SIZE / (1024 * 1024)}MB")
        
        # Prepare upload options
        upload_options: Dict[str, Any] = {
            "resource_type": "image",
        }
        
        if folder:
            upload_options["folder"] = folder
        
        if public_id:
            upload_options["public_id"] = public_id
        
        if transformation:
            upload_options.update(transformation)
        
        try:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file_content,
                **upload_options
            )
            
            return {
                "secure_url": upload_result.get("secure_url"),
                "public_id": upload_result.get("public_id"),
                "format": upload_result.get("format"),
                "width": upload_result.get("width"),
                "height": upload_result.get("height"),
                "bytes": upload_result.get("bytes"),
            }
        except Exception as e:
            raise ValidationError(detail=f"Failed to upload image to Cloudinary: {str(e)}")


class ImageOptimizer:
    """Single Responsibility: Handles image optimization and transformation"""
    
    @staticmethod
    def get_optimized_url(
        public_id: str,
        fetch_format: str = "auto",
        quality: str = "auto",
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: Optional[str] = None,
        gravity: Optional[str] = None
    ) -> str:
        """
        Generate optimized URL for an uploaded image
        
        Args:
            public_id: Public ID of the uploaded image
            fetch_format: Format optimization (auto, webp, etc.)
            quality: Quality optimization (auto, etc.)
            width: Optional width for transformation
            height: Optional height for transformation
            crop: Optional crop mode
            gravity: Optional gravity for cropping
        
        Returns:
            Optimized image URL
        """
        transformation_options: Dict[str, Any] = {
            "fetch_format": fetch_format,
            "quality": quality
        }
        
        if width:
            transformation_options["width"] = width
        if height:
            transformation_options["height"] = height
        if crop:
            transformation_options["crop"] = crop
        if gravity:
            transformation_options["gravity"] = gravity
        
        optimized_url, _ = cloudinary_url(
            public_id,
            **transformation_options
        )
        
        return optimized_url


class CloudinaryService:
    """Facade pattern: Provides a simple interface for Cloudinary operations"""
    
    def __init__(self):
        """Initialize Cloudinary configuration"""
        CloudinaryConfig.initialize()
    
    async def upload_image(
        self,
        file: UploadFile,
        folder: Optional[str] = "payments",
        public_id: Optional[str] = None,
        optimize: bool = True
    ) -> str:
        """
        Upload an image and return the secure URL
        
        Args:
            file: FastAPI UploadFile object
            folder: Folder path in Cloudinary (default: "payments")
            public_id: Optional public ID for the uploaded file
            optimize: Whether to apply auto-format and auto-quality optimization
        
        Returns:
            Secure URL of the uploaded image
        """
        transformation = {}
        if optimize:
            transformation = {
                "fetch_format": "auto",
                "quality": "auto"
            }
        
        upload_result = await ImageUploader.upload_file(
            file=file,
            folder=folder,
            public_id=public_id,
            transformation=transformation
        )
        
        return upload_result["secure_url"]
    
    def get_optimized_url(
        self,
        public_id: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: Optional[str] = None
    ) -> str:
        """
        Get optimized URL for an existing image
        
        Args:
            public_id: Public ID of the image
            width: Optional width for transformation
            height: Optional height for transformation
            crop: Optional crop mode
        
        Returns:
            Optimized image URL
        """
        return ImageOptimizer.get_optimized_url(
            public_id=public_id,
            width=width,
            height=height,
            crop=crop
        )


# Singleton instance
_cloudinary_service: Optional[CloudinaryService] = None


def get_cloudinary_service() -> CloudinaryService:
    """Get or create CloudinaryService instance (Singleton pattern)"""
    global _cloudinary_service
    if _cloudinary_service is None:
        _cloudinary_service = CloudinaryService()
    return _cloudinary_service
