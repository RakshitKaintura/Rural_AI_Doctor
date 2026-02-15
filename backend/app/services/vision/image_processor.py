"""
Image preprocessing and validation for Rural AI Doctor
Optimized for February 2026 Standards
"""

from PIL import Image
import io
import cv2
import numpy as np
from typing import Tuple, Optional


class ImageProcessor:
    
    # Updated 2026 Standard Formats (Added WEBP)
    SUPPORTED_FORMATS = ['JPEG', 'PNG', 'BMP', 'TIFF', 'WEBP']
    
    # Max file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Standard dimensions for Gemini multimodal tokens
    MAX_DIMENSION = 2048
    
    @staticmethod
    def validate_image(image_data: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate image file size, format, and dimensions
        
        Returns:
            (is_valid, error_message)
        """
        # Check file size
        if len(image_data) > ImageProcessor.MAX_FILE_SIZE:
            return False, "Image too large (max 10MB)"
        
        try:
            # Try to open image
            image = Image.open(io.BytesIO(image_data))
            
            # Check format
            if image.format not in ImageProcessor.SUPPORTED_FORMATS:
                return False, f"Unsupported format. Allowed: {', '.join(ImageProcessor.SUPPORTED_FORMATS)}"
            
            # Check dimensions
            width, height = image.size
            if width < 100 or height < 100:
                return False, "Image too small (minimum 100x100)"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
    
    @staticmethod
    def preprocess_image(
        image_data: bytes,
        target_size: Optional[Tuple[int, int]] = None,
        enhance: bool = True
    ) -> bytes:
        """
        Preprocess image for analysis (Resize, Convert, Enhance)
        
        Args:
            image_data: Raw image bytes
            target_size: Optional (width, height) to resize
            enhance: Apply CLAHE enhancement filters
        
        Returns:
            Preprocessed image bytes
        """
        # Load image
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary (strips Alpha channel for Gemini)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if needed
        if target_size:
            image = image.resize(target_size, Image.Resampling.LANCZOS)
        else:
            # Limit max dimension while maintaining aspect ratio
            width, height = image.size
            if max(width, height) > ImageProcessor.MAX_DIMENSION:
                ratio = ImageProcessor.MAX_DIMENSION / max(width, height)
                new_size = (int(width * ratio), int(height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Apply enhancement if requested
        if enhance:
            image = ImageProcessor._enhance_medical_image(image)
        
        # Convert back to bytes
        output = io.BytesIO()
        # Quality 95 and subsampling=0 preserves high-frequency detail for skin/X-ray analysis
        image.save(output, format='JPEG', quality=95, subsampling=0)
        output.seek(0)
        
        return output.read()
    
    @staticmethod
    def _enhance_medical_image(image: Image.Image) -> Image.Image:
        """
        Apply medical image enhancement using CLAHE.
        Optimized for Numpy 2.2 and Gemini 2.5 vision encoders.
        """
        # Convert PIL to OpenCV using the 2026 asarray standard
        img_array = np.asarray(image)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        if len(img_array.shape) == 3:
            # Convert to LAB color space to enhance luminosity only
            lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # ClipLimit 1.5 is the 2026 sweet spot for Gemini 2.5
            # Prevents over-sharpening noise while highlighting clinical opacities
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge channels back
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
        else:
            # Grayscale processing
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
            enhanced = clahe.apply(img_array)
        
        # Convert back to PIL
        return Image.fromarray(enhanced)
    
    @staticmethod
    def get_image_metadata(image_data: bytes) -> dict:
        """Extract detailed image metadata for database logging"""
        image = Image.open(io.BytesIO(image_data))
        
        return {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
            "width": image.size[0],
            "height": image.size[1],
            "file_size_bytes": len(image_data),
            "file_size_mb": round(len(image_data) / (1024 * 1024), 2)
        }


# Singleton instance
image_processor = ImageProcessor()