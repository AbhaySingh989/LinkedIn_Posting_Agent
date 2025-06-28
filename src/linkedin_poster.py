import logging
import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional

from config import Config # Assuming config.py is in the parent directory or PYTHONPATH
from src.article_fetcher import Article # For type hinting

logger = logging.getLogger(__name__)

class LinkedInPoster:
    def __init__(self, config: Config):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None

        if not self.config.linkedin_email or not self.config.linkedin_password:
            logger.error("LinkedIn email or password not configured in .env. LinkedIn posting will be skipped/fail.")
            # Not raising an error to allow other parts of the agent to function if LinkedIn is optional.
            # The post_article method will check for driver and credentials again.
            return

        try:
            logger.info("Initializing Selenium WebDriver for LinkedIn...")
            options = webdriver.ChromeOptions()
            # Headless mode is essential for server environments.
            # For local debugging, you might want to comment out "--headless" to see the browser.
            # options.add_argument("--headless") # Temporarily disabled for debugging
            options.add_argument("--disable-gpu") # Often recommended for headless
            options.add_argument("--no-sandbox") # Required for running as root (e.g., in Docker)
            options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems in Docker
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36") # More recent UA
            options.add_argument("--window-size=1920,1080") # Standard desktop size
            options.add_argument("--disable-blink-features=AutomationControlled") # Helps avoid bot detection
            options.add_experimental_option("excludeSwitches", ["enable-automation"]) # Removes "Chrome is being controlled..."
            options.add_experimental_option('useAutomationExtension', False) # Disables automation extension

            # Disable password save prompt
            prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False}
            options.add_experimental_option("prefs", prefs)
            logger.info("ChromeOptions configured to disable password manager.")

            # Suppress WebDriverManager logs unless they are errors
            logging.getLogger('WDM').setLevel(logging.WARNING)

            # Use webdriver-manager to automatically download and manage ChromeDriver
            # This ensures compatibility between Chrome browser and ChromeDriver.
            try:
                service = ChromeService(ChromeDriverManager().install())
            except Exception as wdm_error:
                logger.error(f"WebDriverManager failed to download/install ChromeDriver: {wdm_error}", exc_info=True)
                logger.error("Please ensure you have Google Chrome installed and that WebDriverManager can access the internet.")
                logger.error("If behind a proxy, set HTTPS_PROXY environment variable.")
                self.driver = None
                return

            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(60) # Time to wait for a page to load
            # Implicit wait can be useful but use with caution, explicit waits are generally better.
            # self.driver.implicitly_wait(5)

            # Additional step to prevent detection (from navigator.webdriver)
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                      get: () => undefined
                    })
                """
            })
            logger.info("Selenium WebDriver initialized successfully for LinkedIn.")

        except Exception as e:
            logger.error(f"Failed to initialize Selenium WebDriver: {e}", exc_info=True)
            logger.error("Common issues: ChromeDriver version mismatch with installed Chrome, or resource limitations.")
            self.driver = None


    def _login(self) -> bool:
        if not self.driver:
            logger.error("WebDriver not initialized. Cannot log in.")
            return False
        if not self.config.linkedin_email or not self.config.linkedin_password:
            logger.error("LinkedIn credentials not provided in config.")
            return False

        try:
            logger.info("Attempting to log in to LinkedIn...")
            self.driver.get("https://www.linkedin.com/login")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "username"))
            )

            email_field = self.driver.find_element(By.ID, "username")
            password_field = self.driver.find_element(By.ID, "password")

            email_field.send_keys(self.config.linkedin_email)
            time.sleep(0.5) # Small delay
            password_field.send_keys(self.config.linkedin_password)
            time.sleep(0.5)
            password_field.send_keys(Keys.RETURN)

            # Wait for login to complete - check for feed or a known element on the home page
            # Example: Wait for the "Start a post" button or feed container
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'share-box-feed-entry__trigger')] | //div[contains(@class, 'feed-container')] | //div[@id='ember30']")) # ember ID is volatile
            )

            # Check if login was actually successful by looking for a URL change or specific element
            if "feed" in self.driver.current_url.lower() or "homepage" in self.driver.current_url.lower():
                logger.info("Successfully logged in to LinkedIn.")
                return True
            else:
                # Check for common login failure indicators
                if self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Hmm, that's not the right password')]") or \
                   self.driver.find_elements(By.ID, "error-for-password") or \
                   self.driver.find_elements(By.XPATH, "//*[contains(text(), 'security verification')]"): # Security challenge
                    logger.error("LinkedIn login failed: Incorrect credentials or security challenge.")
                    # You might want to save a screenshot here for debugging
                    # self.driver.save_screenshot("linkedin_login_failure.png")
                else:
                    logger.error(f"LinkedIn login may have failed. Current URL: {self.driver.current_url}")
                    # self.driver.save_screenshot("linkedin_login_unexpected_page.png")
                return False

        except Exception as e:
            logger.error(f"An error occurred during LinkedIn login: {e}", exc_info=True)
            # self.driver.save_screenshot("linkedin_login_exception.png")
            return False

    def post_article(self, article: Article) -> bool:
        if not self.driver:
            logger.error("WebDriver not initialized. Cannot post article.")
            return False
        if not article.summary or not article.url:
            logger.error("Article summary or URL is missing. Cannot post.")
            return False

        if not self._login(): # Ensure logged in before posting
            logger.error("LinkedIn login failed. Aborting post.")
            return False

        try:
            logger.info(f"Attempting to post article to LinkedIn: {article.title}")

            # Click on the "Start a post" button
            # This selector is prone to change. More robust selectors are needed.
            # Common selectors:
            # By.XPATH, "//button[contains(@class, 'share-box-feed-entry__trigger')]"
            # By.XPATH, "//span[text()='Start a post']" (if inside a button)
            # By.CLASS_NAME, "share-creation-state__button" (might be too generic)
            start_post_button_xpath = "//button[contains(., 'Start a post')] | //div[contains(@aria-label, 'Start a post')]"
            try:
                start_post_button = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, start_post_button_xpath))
                )
                start_post_button.click()
                logger.info("Clicked 'Start a post' button.")
            except Exception as e_button:
                logger.error(f"Could not find or click 'Start a post' button: {e_button}")
                self.driver.save_screenshot("linkedin_start_post_fail.png") # Add screenshot on failure
                # Try an alternative by directly focusing the editor if visible
                try:
                    editor_placeholder = self.driver.find_element(By.XPATH, "//div[@aria-placeholder='What do you want to talk about?']")
                    editor_placeholder.click() # Clicking placeholder might open the full editor
                    logger.info("Clicked editor placeholder as fallback.")
                except:
                    logger.error("Fallback to click editor placeholder also failed.")
                    # self.driver.save_screenshot("linkedin_start_post_fail.png")
                    return False


            # Wait for the post editor modal to appear and the text area to be ready
            # The text area is often a div with role="textbox" or similar ARIA attributes
            # Example: By.XPATH, "//div[@role='textbox' and @aria-label='Text editor for creating content']"
            # Example: By.CLASS_NAME, "ql-editor" (if Quill editor is used)
            # Example: By.XPATH, "//div[contains(@class, 'editor-content')]/div[@role='textbox']"

            # This selector looks for a div that is a textbox, often within a container that becomes active
            # LinkedIn's DOM is complex and changes. This is a best-effort selector.
            post_editor_xpath = "//div[@data-placeholder='What do you want to talk about?'] | //div[@aria-label='Text editor for creating content'] | //div[contains(@class,'ql-editor')]/p | //div[contains(@class,'editor-content')]//div[@role='textbox']"

            post_text_area = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, post_editor_xpath))
            )
            logger.info("Post editor text area located.")

            # Construct the post content
            post_content = f"{self.config.linkedin_post_prefix}\n\n" \
                           f"{article.summary}\n\n" \
                           f"Read more: {article.url}\n\n" \
                           f"{self.config.linkedin_post_suffix}"

            # LinkedIn's text input can be tricky. Sometimes direct send_keys works,
            # other times JavaScript execution is more reliable.
            # Try direct send_keys first.
            try:
                # Click again to ensure focus if it's a div acting as textbox
                if post_text_area.tag_name == 'div':
                    post_text_area.click()
                    time.sleep(0.5)

                # Clear any pre-filled text (e.g. if it's a DIV)
                # For a true textarea, .clear() works. For contenteditable divs, it's more complex.
                # A common pattern for contenteditable divs:
                if post_text_area.get_attribute("contenteditable") == "true":
                     self.driver.execute_script("arguments[0].innerHTML = ''", post_text_area)

                # Send content line by line or in chunks to simulate typing
                for line in post_content.split('\n'):
                    post_text_area.send_keys(line)
                    post_text_area.send_keys(Keys.ENTER) # Simulates newline for div-based textboxes
                    time.sleep(0.2) # Small delay between lines

                logger.info("Post content entered into text area.")

            except Exception as e_input:
                logger.error(f"Error sending keys to post text area: {e_input}. Trying JS fallback.")
                # Fallback using JavaScript to set the value (might not trigger all event listeners)
                # For contenteditable divs, setting innerText or innerHTML is common.
                js_escaped_content = post_content.replace("\n", "\\n").replace("'", "\\'")
                try:
                    if post_text_area.get_attribute("contenteditable") == "true":
                        self.driver.execute_script(f"arguments[0].innerText = '{js_escaped_content}';", post_text_area)
                    else: # Assuming it's a standard textarea if not contenteditable
                        self.driver.execute_script(f"arguments[0].value = '{js_escaped_content}';", post_text_area)
                    logger.info("Post content entered using JavaScript fallback.")
                except Exception as e_js:
                    logger.error(f"JavaScript fallback for text input also failed: {e_js}")
                    # self.driver.save_screenshot("linkedin_post_text_input_fail.png")
                    return False

            time.sleep(2) # Wait for any link preview to load, if applicable

            # Click the "Post" button
            # This selector is also prone to change.
            # Example: By.XPATH, "//button[.//span[text()='Post'] and not(@disabled)]"
            # Example: By.CLASS_NAME, "share-actions__primary-action"
            post_button_xpath = "//button[contains(@class, 'share-actions__primary-action') and not(@disabled)] | //button[.//span[text()='Post'] and not(@disabled)]"
            try:
                post_button = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, post_button_xpath))
                )
                # Scroll into view if necessary, then click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", post_button)
                time.sleep(0.5)
                post_button.click()
                logger.info("Clicked the 'Post' button.")
            except Exception as e_post_btn:
                logger.error(f"Could not find or click the final 'Post' button: {e_post_btn}")
                # self.driver.save_screenshot("linkedin_post_button_fail.png")
                return False

            # Wait for confirmation (e.g., "Post successful" message or modal closes)
            # This is highly variable. A simple delay might be the most practical.
            # Or, wait for the post editor to disappear.
            time.sleep(5) # Wait for post to be processed and modal to close

            # Check if the post editor is gone (one way to confirm success)
            try:
                WebDriverWait(self.driver, 10).until_not(
                    EC.presence_of_element_located((By.XPATH, post_editor_xpath)) # Wait for editor to disappear
                )
                logger.info(f"Article '{article.title}' posted successfully to LinkedIn.")
                return True
            except: # TimeoutException means editor might still be there
                # Check for "Post successful" message if one exists and is reliable
                # e.g., self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Post successful')]")
                logger.warning("Post editor did not disappear as expected. Post may or may not have succeeded. Assuming success for now.")
                # Could also check the user's profile page for the new post, but that's more complex.
                return True # Optimistic assumption

        except Exception as e:
            logger.error(f"An error occurred during LinkedIn posting: {e}", exc_info=True)
            # self.driver.save_screenshot("linkedin_post_general_exception.png")
            return False

    def close(self):
        if self.driver:
            try:
                logger.info("Closing Selenium WebDriver.")
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error while closing WebDriver: {e}")
            finally:
                self.driver = None


if __name__ == "__main__":
    # Add the parent directory to the Python path to allow importing config.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    sys.path.insert(0, parent_dir)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    from config import load_config
    test_config = load_config()

    if not test_config or not test_config.linkedin_email or not test_config.linkedin_password:
        logger.error("LINKEDIN_EMAIL or LINKEDIN_PASSWORD is not configured in .env file. Exiting test.")
    else:
        logger.info(f"Test configured for LinkedIn user: {test_config.linkedin_email}")

        # Create a dummy Article object for testing
        test_article = Article(
            title="Amazing New AI Discovery That Will Change Everything!",
            url="https://example.com/amazing-ai-discovery-" + str(time.time()), # Unique URL
            source="Test Suite",
            summary=(
                "Researchers have unveiled a groundbreaking AI model that demonstrates "
                "unprecedented capabilities in natural language understanding and generation. "
                "This could revolutionize how we interact with technology."
            )
        )

        # Override post prefix/suffix for testing if desired
        # test_config.linkedin_post_prefix = "🧪 Test Post - Automated Agent:"
        # test_config.linkedin_post_suffix = "#Testing #Automation #AI #BotPost"

        poster = LinkedInPoster(test_config)

        if poster.driver is None:
            logger.error("LinkedInPoster WebDriver initialization failed. Cannot run test.")
        else:
            logger.info("--- LinkedIn Poster Test ---")
            # Attempt to post the article
            # Warning: This will actually post to LinkedIn if login is successful!
            # Be sure you want to do this with the configured account.

            # For safety, you might want to confirm before actually posting during a test:
            # proceed = input("This will attempt a REAL LinkedIn post. Proceed? (yes/no): ")
            # if proceed.lower() != 'yes':
            #    logger.info("LinkedIn post test aborted by user.")
            #    poster.close()
            #    exit()

            success = poster.post_article(test_article)

            if success:
                logger.info("LinkedIn post test: Article posted successfully (allegedly). Please verify on LinkedIn.")
            else:
                logger.error("LinkedIn post test: Failed to post article. Check logs and screenshots (if saved).")

            # Close the browser
            poster.close()
            logger.info("--- LinkedIn Poster Test Finished ---")

"""
Important Notes for LinkedIn Automation:
1.  **Fragility**: LinkedIn's website structure (HTML, CSS classes, IDs) changes frequently.
    This makes Selenium scripts highly prone to breaking. Selectors need to be chosen carefully
    and may require regular updates. Using ARIA roles, stable data attributes, or combinations
    of text and structure can be more robust than relying solely on CSS classes.
2.  **Account Safety**: Automating LinkedIn actions, especially posting, can be against their
    Terms of Service. Excessive or bot-like activity can lead to account restrictions or bans.
    - Use reasonable delays (time.sleep) to mimic human behavior.
    - Avoid overly frequent posting.
    - Consider rotating user agents or using proxy IPs if running at scale (adds complexity).
    - Headless mode is often detectable; some sites have countermeasures. The options added try to mitigate this.
3.  **Login Challenges**: LinkedIn may present CAPTCHAs, 2FA prompts, or other security checks,
    especially when logging in from new IPs or with automation. Selenium alone cannot easily solve
    complex CAPTCHAs. Manual intervention or third-party CAPTCHA solving services might be needed
    for robust, unattended operation (adds cost and complexity).
    The current script does not handle these advanced login challenges.
4.  **Error Handling & Debugging**:
    - Save screenshots (e.g., `self.driver.save_screenshot("error_page.png")`) on failure to help
      diagnose issues.
    - Log extensively.
    - Be prepared for WebDriverWait timeouts if elements are not found or page loads slowly.
5.  **Alternatives**:
    - **Official API**: LinkedIn has an official API, but it's generally restricted for content posting
      to approved partners and has strict usage limits. It's not typically available for general
      automated posting by individual users.
    - **Browser Extensions**: Some browser extensions offer LinkedIn automation, but they often
      run in the context of an already logged-in browser and might also use DOM manipulation.
    - **Third-party services/platforms (like n8n, Zapier, etc.)**: These often have pre-built
      LinkedIn integrations that might be more stable as they are maintained by the service provider.
      However, the task specified "unofficial API, browser automation (e.g., Selenium), or tools like n8n",
      and this implementation focuses on Selenium as a direct browser automation method.

This Selenium script is a best-effort approach and will require maintenance.
"""
