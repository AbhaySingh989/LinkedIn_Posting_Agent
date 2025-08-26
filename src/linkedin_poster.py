import logging
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromiumService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

logger = logging.getLogger(__name__)

class LinkedInPoster:
    """
    Handles posting articles to LinkedIn using Selenium.
    """
    def __init__(self, config):
        """
        Initializes the LinkedInPoster, setting up configuration and the WebDriver.
        """
        self.config = config
        self.driver = self._init_driver()
        if self.driver:
            self.logged_in = self._login()
        else:
            self.logged_in = False

    def _init_driver(self):
        """
        Initializes the Selenium WebDriver using webdriver-manager for Chromium.
        """
        logger.info("Initializing Selenium WebDriver for LinkedIn...")
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920x1080")

            prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False}
            options.add_experimental_option("prefs", prefs)
            logger.info("ChromeOptions configured.")

            # Use webdriver-manager to handle the chromium driver
            service = ChromiumService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())

            logger.info("WebDriver service and options configured for Chromium.")
            driver = webdriver.Chrome(service=service, options=options)
            logger.info("WebDriver initialized successfully.")
            return driver
        except WebDriverException as e:
            logger.error(f"WebDriver failed to initialize, likely due to environment issues: {e.msg}")
            logger.warning("LinkedIn posting will be disabled.")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during WebDriver initialization: {e}", exc_info=True)
            logger.warning("LinkedIn posting will be disabled.")
            return None

    def _login(self):
        """
        Logs into LinkedIn.
        """
        if not self.driver:
            return False

        try:
            logger.info("Navigating to LinkedIn login page.")
            self.driver.get("https://www.linkedin.com/login")

            logger.info("Entering credentials.")
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(self.config.linkedin_email)
            self.driver.find_element(By.ID, "password").send_keys(self.config.linkedin_password)
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()

            # Wait for the home page to load by checking for the search bar
            wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@class, 'search-global-typeahead__input')]")))
            logger.info("LinkedIn login successful.")
            return True
        except TimeoutException:
            logger.error("Login failed: Timeout while waiting for page elements.")
            self.save_screenshot("login_timeout_error")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during login: {e}", exc_info=True)
            self.save_screenshot("login_unexpected_error")
            return False

    def post_article(self, article):
        """
        Posts an article to LinkedIn.
        """
        if not self.logged_in:
            logger.error("Cannot post article, not logged in.")
            return False

        try:
            logger.info(f"Attempting to post article: {article.title}")
            # Click the "Start a post" button
            start_post_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'share-box-feed-entry__trigger')]"))
            )
            start_post_button.click()
            logger.info("Clicked 'Start a post' button.")

            # Write the post content
            post_editor = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'editor-container')]//div[@role='textbox']"))
            )

            post_text = f"{article.summary}\n\nRead more: {article.url}"
            post_editor.send_keys(post_text)
            logger.info("Entered post content into the editor.")

            # Click the "Post" button
            post_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'share-actions__primary-action')]"))
            )
            # Check if button is enabled
            if not post_button.is_enabled():
                logger.error("Post button is not enabled.")
                self.save_screenshot("post_button_disabled")
                return False

            post_button.click()
            logger.info("Clicked the final 'Post' button.")

            # Wait for the post to be successful, e.g., by looking for a confirmation message
            # This part is tricky as LinkedIn's UI can change. A simple sleep is a brittle but simple solution for now.
            time.sleep(5)

            logger.info(f"Successfully posted article: {article.title}")
            return True

        except TimeoutException as e:
            logger.error(f"Timeout while trying to post article: {e}")
            self.save_screenshot("post_timeout_error")
            return False
        except NoSuchElementException as e:
            logger.error(f"Could not find an element while posting: {e}")
            self.save_screenshot("post_element_not_found_error")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while posting: {e}", exc_info=True)
            self.save_screenshot("post_unexpected_error")
            return False

    def save_screenshot(self, error_name):
        """Saves a screenshot of the current browser state for debugging."""
        screenshots_dir = "screenshots"
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(screenshots_dir, f"{error_name}_{timestamp}.png")
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")

    def close(self):
        """
        Closes the WebDriver.
        """
        if self.driver:
            logger.info("Closing WebDriver.")
            self.driver.quit()
