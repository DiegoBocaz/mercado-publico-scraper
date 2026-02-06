"""CAPTCHA Solver module for Mercado Público.

This module provides functionality to solve CAPTCHA challenges on
Mercado Público website using OCR and web automation.
"""

import io
import logging
from typing import Optional, Tuple
from urllib.parse import urljoin

import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ocr import OCRProcessor

logger = logging.getLogger(__name__)


class CaptchaSolver:
    """Solves CAPTCHA challenges on Mercado Público."""

    def __init__(self, driver: webdriver.Chrome, ocr_processor: Optional[OCRProcessor] = None):
        """Initialize CAPTCHA solver.

        Args:
            driver: Selenium WebDriver instance
            ocr_processor: OCR processor instance for text extraction
        """
        self.driver = driver
        self.ocr_processor = ocr_processor or OCRProcessor()
        self.base_url = "http://www.mercadopublico.cl"

    def solve(self, captcha_input_id: str = "DWNL$ctl10") -> bool:
        """Solve CAPTCHA on the current page.

        Args:
            captcha_input_id: CSS selector or element ID for CAPTCHA input field

        Returns:
            True if CAPTCHA was solved successfully, False otherwise
        """
        try:
            # Extract CAPTCHA text from image
            captcha_text = self._extract_captcha_text()
            if not captcha_text:
                logger.warning("Failed to extract CAPTCHA text")
                return False

            # Enter CAPTCHA text into input field
            self._input_captcha_text(captcha_text, captcha_input_id)

            logger.info(f"CAPTCHA solved: {captcha_text}")
            return True

        except Exception as e:
            logger.error(f"Error solving CAPTCHA: {e}")
            return False

    def _extract_captcha_text(self) -> Optional[str]:
        """Extract text from CAPTCHA image.

        Returns:
            Extracted text or None if extraction failed
        """
        try:
            # Find CAPTCHA image element
            captcha_img = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//img[contains(@src, 'Captcha')]")
                )
            )

            # Get image source URL
            img_src = captcha_img.get_attribute("src")
            if not img_src:
                logger.error("CAPTCHA image source not found")
                return None

            # Download image
            img_data = self._download_image(img_src)
            if not img_data:
                return None

            # Extract text using OCR
            captcha_text = self.ocr_processor.extract_text(img_data)
            return captcha_text.strip() if captcha_text else None

        except Exception as e:
            logger.error(f"Error extracting CAPTCHA text: {e}")
            return None

    def _download_image(self, url: str) -> Optional[Image.Image]:
        """Download and return PIL Image object.

        Args:
            url: Image URL (absolute or relative)

        Returns:
            PIL Image object or None if download failed
        """
        try:
            # Ensure absolute URL
            if not url.startswith("http"):
                url = urljoin(self.base_url, url)

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            return Image.open(io.BytesIO(response.content))

        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return None

    def _input_captcha_text(
        self, text: str, input_id: str = "DWNL$ctl10"
    ) -> bool:
        """Input CAPTCHA text into form field.

        Args:
            text: Text to input
            input_id: Input field ID or CSS selector

        Returns:
            True if text was entered successfully
        """
        try:
            # Try to find input by ID first
            try:
                input_field = self.driver.find_element(By.ID, input_id)
            except Exception:
                # Try by CSS selector
                input_field = self.driver.find_element(
                    By.CSS_SELECTOR, f"#{input_id}"
                )

            # Clear existing text and enter CAPTCHA
            input_field.clear()
            input_field.send_keys(text)

            logger.debug(f"Entered CAPTCHA text into field {input_id}")
            return True

        except Exception as e:
            logger.error(f"Error inputting CAPTCHA text: {e}")
            return False

    def get_captcha_image(self) -> Optional[Image.Image]:
        """Retrieve current CAPTCHA image without solving.

        Returns:
            PIL Image object or None
        """
        try:
            captcha_img = self.driver.find_element(
                By.XPATH, "//img[contains(@src, 'Captcha')]"
            )
            img_src = captcha_img.get_attribute("src")
            return self._download_image(img_src) if img_src else None
        except Exception as e:
            logger.error(f"Error getting CAPTCHA image: {e}")
            return None
