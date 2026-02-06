"""
OCR (Optical Character Recognition) Module
Extracts text from images in tender documents
"""

import io
import base64
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

import pytesseract
from PIL import Image
import cv2
import numpy as np
from loguru import logger


class OCRProcessor:
    """
    Handles optical character recognition for extracting text from images.
    Supports preprocessing, language-specific OCR, and confidence scoring.
    """

    def __init__(self, language: str = 'spa', enable_preprocessing: bool = True):
        """
        Initialize OCR processor.
        
        Args:
            language: Tesseract language code (default: 'spa' for Spanish)
            enable_preprocessing: Whether to preprocess images (default: True)
        """
        self.language = language
        self.enable_preprocessing = enable_preprocessing
        logger.info(f"Initialized OCR processor with language: {language}")

    def extract_text_from_image(self, image_source: Any) -> Dict[str, Any]:
        """
        Extract text from an image source.
        
        Args:
            image_source: Can be file path, PIL Image, numpy array, or bytes
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Convert input to PIL Image
            img = self._load_image(image_source)
            
            # Preprocess image if enabled
            if self.enable_preprocessing:
                img = self._preprocess_image(img)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(img, lang=self.language)
            
            # Get detailed data
            data = pytesseract.image_to_data(img, lang=self.language, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['confidence'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            logger.info(f"Extracted text from image with {len(text)} characters, confidence: {avg_confidence:.2f}%")
            
            return {
                'text': text.strip(),
                'confidence': avg_confidence,
                'word_count': len(text.split()),
                'language': self.language,
                'data': data,
                'success': True
            }
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return {
                'text': '',
                'confidence': 0,
                'word_count': 0,
                'language': self.language,
                'data': {},
                'success': False,
                'error': str(e)
            }

    def extract_table_data(self, image_source: Any) -> Dict[str, Any]:
        """
        Extract tabular data from image.
        
        Args:
            image_source: Image source (file path, PIL Image, numpy array, or bytes)
            
        Returns:
            Dictionary with table data and cell information
        """
        try:
            img = self._load_image(image_source)
            
            if self.enable_preprocessing:
                img = self._preprocess_image(img)
            
            # Get detailed data with bounding boxes
            data = pytesseract.image_to_data(img, lang=self.language, output_type=pytesseract.Output.DICT)
            
            # Group words into rows based on y-coordinate
            rows = {}
            for i, (x, y, w, h, conf, text) in enumerate(zip(
                data['left'], data['top'], data['width'], data['height'],
                data['confidence'], data['text']
            )):
                if int(conf) > 0 and text.strip():
                    row_key = round(y / 10) * 10  # Group by approximate y coordinate
                    if row_key not in rows:
                        rows[row_key] = []
                    rows[row_key].append({'x': x, 'text': text, 'conf': int(conf)})
            
            # Sort and format rows
            sorted_rows = []
            for row_key in sorted(rows.keys()):
                row_data = sorted(rows[row_key], key=lambda x: x['x'])
                row_text = [item['text'] for item in row_data]
                sorted_rows.append(row_text)
            
            logger.info(f"Extracted table with {len(sorted_rows)} rows")
            
            return {
                'table': sorted_rows,
                'row_count': len(sorted_rows),
                'success': True
            }
        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            return {
                'table': [],
                'row_count': 0,
                'success': False,
                'error': str(e)
            }

    def _load_image(self, image_source: Any) -> Image.Image:
        """
        Load image from various sources.
        
        Args:
            image_source: File path, PIL Image, numpy array, or bytes
            
        Returns:
            PIL Image object
        """
        if isinstance(image_source, Image.Image):
            return image_source
        elif isinstance(image_source, np.ndarray):
            return Image.fromarray(image_source.astype('uint8'))
        elif isinstance(image_source, bytes):
            return Image.open(io.BytesIO(image_source))
        elif isinstance(image_source, str):
            # Could be file path or base64 string
            if image_source.startswith('/')or image_source.startswith('.'):
                return Image.open(image_source)
            else:
                # Try to decode as base64
                try:
                    img_data = base64.b64decode(image_source)
                    return Image.open(io.BytesIO(img_data))
                except:
                    return Image.open(image_source)
        else:
            raise ValueError(f"Unsupported image source type: {type(image_source)}")

    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy.
        
        Args:
            img: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to numpy array for OpenCV
            img_array = np.array(img)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                img_gray = img_array
            
            # Apply thresholding
            _, img_binary = cv2.threshold(img_gray, 150, 255, cv2.THRESH_BINARY)
            
            # Denoise
            img_denoised = cv2.fastNlMeansDenoising(img_binary, h=10)
            
            # Upscale if image is too small
            if img_denoised.shape[0] < 300:
                scale = 2
                img_denoised = cv2.resize(img_denoised, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            
            # Convert back to PIL Image
            return Image.fromarray(img_denoised)
        except Exception as e:
            logger.warning(f"Error preprocessing image: {e}. Using original image.")
            return img

    def batch_extract_text(self, image_sources: list) -> list:
        """
        Extract text from multiple images.
        
        Args:
            image_sources: List of image sources
            
        Returns:
            List of extraction results
        """
        results = []
        for idx, source in enumerate(image_sources, 1):
            logger.info(f"Processing image {idx}/{len(image_sources)}")
            result = self.extract_text_from_image(source)
            results.append(result)
        return results

    def set_language(self, language: str) -> None:
        """
        Change OCR language.
        
        Args:
            language: Tesseract language code (e.g., 'spa', 'eng', 'fra')
        """
        self.language = language
        logger.info(f"Changed OCR language to: {language}")

    def validate_tesseract(self) -> bool:
        """
        Validate if Tesseract is installed and accessible.
        
        Returns:
            True if Tesseract is available, False otherwise
        """
        try:
            pytesseract.get_tesseract_version()
            logger.info("Tesseract is properly installed and accessible")
            return True
        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract is not installed or not found in PATH")
            return False
