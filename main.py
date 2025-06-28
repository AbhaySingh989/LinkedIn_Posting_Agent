import time
import logging
from config import load_config
from src.article_fetcher import ArticleFetcher
from src.llm_handler import LLMHandler
from src.telegram_bot import TelegramNotifier
from src.linkedin_poster import LinkedInPoster
from src.utils import setup_logging # Assuming Article dataclass is available via one of these or utils

logger = logging.getLogger(__name__)

def main():
    """
    Main function to run the LinkedIn AI Agent.
    Orchestrates the fetching, processing, and posting of AI articles.
    """
    # setup_logging() is called by load_config() if LOG_LEVEL is set, or can be called here.
    # For consistency, let's ensure it's called once.
    # config.py currently doesn't call setup_logging. utils.py does.
    # Let main.py handle calling setup_logging using the log_level from config.

    temp_config_for_log = load_config()
    if not temp_config_for_log:
        # Basic logging if config fails early
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger.error("Initial configuration loading failed. Cannot setup advanced logging. Exiting.")
        return

    setup_logging(log_level=temp_config_for_log.log_level) # Setup logging using config's log_level
    logger.info("Autonomous LinkedIn AI Agent started.")

    # Reload config in case setup_logging changed anything or to ensure it's fresh
    config = load_config()
    if not config: # Should not happen if temp_config_for_log succeeded, but as a safeguard.
        logger.error("Configuration could not be loaded after logging setup. Exiting.")
        return

    # Initialize components
    fetcher = ArticleFetcher(config)
    # Pass model_name from config to LLMHandler
    llm = LLMHandler(config.gemini_api_key, model_name=config.llm_model_name)
    notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
    # Pass full config to LinkedInPoster as it uses multiple settings from it
    linkedin_poster = LinkedInPoster(config)

    try:
        logger.info("Starting Telegram bot polling in background...")
        notifier.start_polling(block=False) # Start polling in a non-blocking way

        logger.info("Fetching trending AI articles...")
        articles = fetcher.fetch_all_articles()

        if not articles:
            logger.info("No new articles found in this run.")
            # return # Keep running to allow Telegram bot to respond to commands if any, or for scheduling.
            # For a single run, returning here is fine. If scheduled, it would just mean this hour had no articles.
        else:
            logger.info(f"Found {len(articles)} new articles. Processing...")
            for article in articles:
                logger.info(f"Processing article: '{article.title}' ({article.url}) from {article.source}")

                try:
                    logger.debug(f"Generating summary for: {article.title}")
                    summary = llm.summarize_article(article.url) # summarize_article handles content fetching
                    if not summary:
                        logger.warning(f"Could not generate summary for '{article.title}'. Skipping.")
                        continue
                    article.summary = summary
                    logger.info(f"Summary generated for '{article.title}'.")
                except Exception as e:
                    logger.error(f"Error summarizing article '{article.title}': {e}", exc_info=True)
                    continue # Skip to next article

                logger.info(f"Sending article to Telegram for approval: {article.title}")
                # This call is blocking and waits for user response or timeout
                approval_response = notifier.send_article_for_approval(article)

                if approval_response == "post":
                    logger.info(f"Article '{article.title}' approved for posting by user.")
                    try:
                        post_success = linkedin_poster.post_article(article)
                        if post_success:
                            logger.info(f"Successfully posted '{article.title}' to LinkedIn.")
                            # Optionally, send a confirmation back to Telegram user
                            # notifier.send_message(f"Successfully posted to LinkedIn: {article.title}")
                        else:
                            logger.error(f"Failed to post '{article.title}' to LinkedIn (as reported by poster).")
                            notifier.send_message(f"⚠️ Failed to post article to LinkedIn: {article.title}\nReview logs for details.")
                    except Exception as e:
                        logger.error(f"An exception occurred while trying to post '{article.title}' to LinkedIn: {e}", exc_info=True)
                        notifier.send_message(f"🚨 Error during LinkedIn posting for: {article.title}\nError: {e}")
                elif approval_response == "ignore":
                    logger.info(f"Article '{article.title}' was ignored by user via Telegram.")
                elif approval_response == "timeout":
                    logger.info(f"Approval request for '{article.title}' timed out.")
                else: # Other errors from send_article_for_approval like "error_no_chat_id"
                    logger.error(f"Could not get approval for '{article.title}'. Response: {approval_response}")

        logger.info("Main processing loop completed for this run.")

    except Exception as e:
        logger.critical(f"An unexpected critical error occurred in the main agent loop: {e}", exc_info=True)
        try:
            notifier.send_message(f"🆘 The LinkedIn AI Agent encountered a critical error and may have stopped functioning: {e}")
        except Exception as notify_err:
            logger.error(f"Failed to send critical error notification via Telegram: {notify_err}")
    finally:
        logger.info("Initiating cleanup...")
        if 'linkedin_poster' in locals() and linkedin_poster is not None:
            linkedin_poster.close() # Close Selenium WebDriver
        if 'notifier' in locals() and notifier is not None:
            notifier.stop_polling() # Stop Telegram bot polling
        logger.info("Autonomous LinkedIn AI Agent run finished. Exiting.")

if __name__ == "__main__":
    main()

    # Example for scheduling (runs main() every hour):
    # Note: If using scheduling, ensure main() is robust enough to be called multiple times.
    # Selenium WebDriver and Telegram bot polling should be managed carefully in a scheduled setup
    # (e.g., ensure they are properly started and stopped for each run, or managed globally if the script runs continuously).
    # The current setup with start/stop polling and WebDriver close in main() is suitable for discrete runs.

    # import schedule
    # import time

    # def job():
    #     logger.info("Scheduler running job 'main'.")
    #     main()
    #     logger.info("Scheduler finished job 'main'. Next run scheduled.")

    # schedule.every().hour.do(job)
    # # schedule.every().day.at("10:30").do(job)
    # # schedule.every(5).to(10).minutes.do(job)

    # logger.info("Scheduler started. Waiting for the first job to run...")
    # try:
    #     while True:
    #         schedule.run_pending()
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     logger.info("Scheduler stopped by user (KeyboardInterrupt).")
    # except Exception as e:
    #     logger.critical(f"Scheduler failed: {e}", exc_info=True)
    # finally:
    #     logger.info("Exiting scheduled application.")
