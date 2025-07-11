import asyncio
import logging
import time
from typing import Optional
from contextlib import asynccontextmanager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)


class SeleniumClient:
    """Simple, production-ready Selenium client for getting rendered HTML."""

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30,
        page_load_timeout: int = 30,
        wait_for_element: Optional[str] = None
    ):
        self.headless = headless
        self.timeout = timeout
        self.page_load_timeout = page_load_timeout
        self.wait_for_element = wait_for_element
        self._driver: Optional[webdriver.Chrome] = None

    def _create_driver(self) -> webdriver.Chrome:
        """Create and configure Chrome driver."""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Essential options for production
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--window-size=1920,1080")

        # Realistic user agent
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(self.page_load_timeout)
            driver.implicitly_wait(5)
            return driver
        except Exception as e:
            logger.error(f"Failed to create Chrome driver: {e}")
            raise

    async def get_driver(self) -> webdriver.Chrome:
        """Get or create driver instance."""
        if self._driver is None:
            loop = asyncio.get_event_loop()
            self._driver = await loop.run_in_executor(None, self._create_driver)
        return self._driver

    async def close(self):
        """Close the driver."""
        if self._driver:
            try:
                await asyncio.get_event_loop().run_in_executor(None, self._driver.quit)
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
            finally:
                self._driver = None

    @asynccontextmanager
    async def session(self):
        """Context manager for driver session."""
        try:
            yield await self.get_driver()
        finally:
            await self.close()

    async def get_rendered_html(self, url: str) -> str:
        """
        Get fully rendered HTML after JavaScript execution.

        Args:
            url: URL to load

        Returns:
            Rendered HTML content
        """
        driver = await self.get_driver()
        loop = asyncio.get_event_loop()

        def _get_rendered_page():
            try:
                # Load the page
                driver.get(url)

                # Wait for body to be present
                WebDriverWait(driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # Wait for specific element if provided
                if self.wait_for_element:
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, self.wait_for_element))
                        )
                    except TimeoutException:
                        logger.debug(
                            f"Element {self.wait_for_element} not found, proceeding anyway")

                # Small delay to ensure all JS has executed
                time.sleep(2)

                return driver.page_source

            except TimeoutException as e:
                logger.warning(f"Timeout loading {url}: {e}")
                return driver.page_source
            except WebDriverException as e:
                logger.error(f"WebDriver error loading {url}: {e}")
                raise

        return await loop.run_in_executor(None, _get_rendered_page)
