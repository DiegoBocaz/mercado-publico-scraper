"""Document downloader for Mercado Público.

Automates the process of downloading documents from Mercado Público
licitaciones, handling CAPTCHA challenges automatically.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from captcha_solver import CaptchaSolver
from ocr import OCRProcessor

logger = logging.getLogger(__name__)


class MercadoPublicoDownloader:
    """Downloads documents from Mercado Público tenders."""

    def __init__(self, output_dir: str = "./downloads"):
        """Initialize downloader.

        Args:
            output_dir: Directory to save downloaded files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.driver = self._setup_driver()
        self.ocr = OCRProcessor()
        self.captcha_solver = CaptchaSolver(self.driver, self.ocr)
        self.base_url = "https://www.mercadopublico.cl"

    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Selenium Chrome driver."""
        options = Options()
        # Uncomment to run in headless mode
        # options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0")
        return webdriver.Chrome(options=options)

    def download_documents(self, tender_url: str) -> List[str]:
        """Download all documents from a tender.

        Args:
            tender_url: URL of the Mercado Público tender

        Returns:
            List of downloaded file paths
        """
        downloaded_files = []
        try:
            self.driver.get(tender_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, 'BID')]"))
            )

            # Find and click on attachments section
            attachment_elements = self._find_attachment_links()
            logger.info(f"Found {len(attachment_elements)} attachment links")

            for i, link in enumerate(attachment_elements):
                try:
                    logger.info(f"Downloading attachment {i + 1}/{len(attachment_elements)}")
                    file_path = self._download_attachment(link)
                    if file_path:
                        downloaded_files.append(file_path)
                except Exception as e:
                    logger.error(f"Error downloading attachment: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in download_documents: {e}")
        finally:
            self.close()

        return downloaded_files

    def _find_attachment_links(self) -> List[str]:
        """Find all attachment download links on the page."""
        links = []
        try:
            elements = self.driver.find_elements(
                By.XPATH, "//a[contains(@href, 'ViewBidAttachment')]"
            )
            for elem in elements:
                href = elem.get_attribute("href")
                if href:
                    links.append(href)
        except Exception as e:
            logger.error(f"Error finding attachment links: {e}")
        return links

    def _download_attachment(self, attachment_url: str) -> Optional[str]:
        """Download a single attachment.

        Args:
            attachment_url: URL of the attachment

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Navigate to attachment page
            self.driver.get(attachment_url)
            time.sleep(2)

            # Solve CAPTCHA if present
            if self._has_captcha():
                logger.info("CAPTCHA detected, attempting to solve...")
                if not self.captcha_solver.solve():
                    logger.warning("Failed to solve CAPTCHA")
                    return None
                time.sleep(2)

            # Find and click download button
            download_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(@href, 'DWNL')] | //button[contains(text(), 'Descargar')]")
                )
            )
            download_button.click()

            # Wait for download to complete
            time.sleep(5)
            return self._get_latest_download()

        except Exception as e:
            logger.error(f"Error downloading attachment: {e}")
            return None

    def _has_captcha(self) -> bool:
        """Check if CAPTCHA is present on the page."""
        try:
            self.driver.find_element(By.XPATH, "//img[contains(@src, 'Captcha')]")
            return True
        except Exception:
            return False

    def _get_latest_download(self) -> Optional[str]:
        """Get the most recently downloaded file."""
        try:
            latest_file = max(
                self.output_dir.glob("*"),
                key=lambda p: p.stat().st_mtime,
                default=None,
            )
            return str(latest_file) if latest_file else None
        except Exception as e:
            logger.error(f"Error getting latest download: {e}")
            return None

    def close(self):
        """Close the browser."""
        try:
            self.driver.quit()
        except Exception as e:
            logger.error(f"Error closing driver: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    downloader = MercadoPublicoDownloader()
    print("Downloader initialized successfully")
