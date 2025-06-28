import logging
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from typing import Optional, Callable, Dict
from src.article_fetcher import Article # Assuming Article dataclass is in article_fetcher.py or utils.py
from config import Config # To access telegram_chat_id if needed for direct messaging

logger = logging.getLogger(__name__)

# Store callback handlers for approvals. Key: unique_id, Value: function to call with "post" or "ignore"
# This is a simple in-memory store. For persistence or multi-instance, a database/Redis would be better.
APPROVAL_CALLBACKS: Dict[str, Callable[[str], None]] = {}
USER_RESPONSES: Dict[str, Optional[str]] = {} # Stores user's choice: "post", "ignore", or None if timeout

class TelegramNotifier:
    def __init__(self, token: str, default_chat_id: Optional[str] = None):
        if not token:
            raise ValueError("Telegram bot token is required.")
        self.application = Application.builder().token(token).build()
        self.default_chat_id = default_chat_id

        # Add handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CallbackQueryHandler(self._button_callback))
        # A generic message handler for logging or debugging, if needed
        # self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._echo))

        # Store a reference to the running bot instance, to be set by run_polling/run_webhook
        self._bot_instance = None
        self.user_interaction_timeout = 3600  # seconds (1 hour) for user to respond to an approval request

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Sends a welcome message when the /start command is issued."""
        if update.effective_chat:
            await update.effective_chat.send_message(
                "Hello! I am the LinkedIn AI Article Bot. I will send you AI articles for approval before posting to LinkedIn.\n"
                f"Your chat ID is: `{update.effective_chat.id}`. Please set this as `TELEGRAM_CHAT_ID` in the configuration if you haven't already.",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            logger.info(f"Responded to /start command from chat_id: {update.effective_chat.id}")
        else:
            logger.warning("Received /start command but update.effective_chat is None.")


    async def _button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles inline keyboard button presses."""
        query = update.callback_query
        await query.answer() # Acknowledge the button press

        callback_data = query.data
        logger.info(f"Received callback query with data: {callback_data}")

        # Expected callback_data format: "action:unique_id", e.g., "post:article123" or "ignore:article123"
        try:
            action, unique_id = callback_data.split(":", 1)
        except ValueError:
            logger.error(f"Invalid callback data format: {callback_data}")
            if query.message:
                 await query.edit_message_text(text=f"Error processing action. Invalid data: {callback_data}")
            return

        if unique_id in USER_RESPONSES:
            USER_RESPONSES[unique_id] = action
            if query.message:
                if action == "post":
                    await query.edit_message_text(text=f"✅ Article approved for posting!\nOriginal message:\n{query.message.text}")
                elif action == "ignore":
                    await query.edit_message_text(text=f"❌ Article ignored.\nOriginal message:\n{query.message.text}")
                else:
                    await query.edit_message_text(text=f"Action '{action}' recorded.\nOriginal message:\n{query.message.text}")
            logger.info(f"User action '{action}' recorded for article ID '{unique_id}'.")
        else:
            logger.warning(f"Received callback for unknown or timed-out article ID: {unique_id}")
            if query.message:
                await query.edit_message_text(text=f"This action has expired or the article ID is unknown.\nOriginal message:\n{query.message.text}")


    async def send_message_async(self, text: str, chat_id: Optional[str] = None, parse_mode: Optional[str] = ParseMode.HTML) -> None:
        """Asynchronously sends a message to the specified chat_id or default chat_id."""
        target_chat_id = chat_id or self.default_chat_id
        if not target_chat_id:
            logger.error("No chat_id provided and default_chat_id is not set. Cannot send message.")
            return
        try:
            await self.application.bot.send_message(chat_id=target_chat_id, text=text, parse_mode=parse_mode)
            logger.info(f"Message sent to chat_id {target_chat_id}: {text[:50]}...")
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {target_chat_id}: {e}")

    def send_message(self, text: str, chat_id: Optional[str] = None, parse_mode: Optional[str] = ParseMode.HTML) -> None:
        """
        Synchronously sends a message. This is a convenience wrapper for non-async contexts.
        Requires the bot to be running in a separate thread/process.
        """
        import asyncio
        try:
            # Get the currently running event loop or create a new one if none exists
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # If called from within an async context that is already running
            asyncio.create_task(self.send_message_async(text, chat_id, parse_mode))
        else:
            loop.run_until_complete(self.send_message_async(text, chat_id, parse_mode))


    async def send_article_for_approval_async(self, article: Article, chat_id: Optional[str] = None) -> str:
        """
        Asynchronously sends an article to Telegram for user approval and waits for a response.
        Returns "post", "ignore", or "timeout".
        """
        target_chat_id = chat_id or self.default_chat_id
        if not target_chat_id:
            logger.error("No chat_id for approval and default_chat_id is not set.")
            return "error_no_chat_id"

        # Generate a unique ID for this approval request, e.g., based on URL hash or timestamp
        # For simplicity, using article URL (ensure it's unique enough for concurrent articles)
        # A more robust unique_id might be `hashlib.md5(article.url.encode()).hexdigest()[:8]`
        article_id = f"article_{time.time_ns()}" # Unique enough for this run
        USER_RESPONSES[article_id] = None # Initialize response state

        text = (
            f"<b>New AI Article Suggestion:</b>\n\n"
            f"<b>Title:</b> {article.title}\n"
            f"<b>Source:</b> {article.source}\n"
            f"<b>Summary:</b>\n{article.summary}\n\n"
            f"<a href='{article.url}'>Read Full Article</a>\n\n"
            f"Do you want to post this to LinkedIn?"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Post to LinkedIn", callback_data=f"post:{article_id}"),
                InlineKeyboardButton("❌ Ignore", callback_data=f"ignore:{article_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await self.application.bot.send_message(
                chat_id=target_chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            logger.info(f"Article '{article.title}' sent for approval with ID {article_id}.")
        except Exception as e:
            logger.error(f"Failed to send article for approval to {target_chat_id}: {e}")
            if article_id in USER_RESPONSES: del USER_RESPONSES[article_id]
            return f"error_sending_message: {e}"

        # Wait for user response or timeout
        start_time = time.time()
        while time.time() - start_time < self.user_interaction_timeout:
            if USER_RESPONSES.get(article_id) is not None:
                response = USER_RESPONSES.pop(article_id) # Clean up
                logger.info(f"User response for {article_id}: {response}")
                return response
            await asyncio.sleep(1)  # Check every second

        # Timeout
        logger.warning(f"Timeout waiting for approval for article ID {article_id} ('{article.title}').")
        if article_id in USER_RESPONSES: del USER_RESPONSES[article_id] # Clean up

        # Try to inform user about timeout by editing the original message if possible, or sending a new one.
        # Editing might fail if the message context is lost or bot restarted.
        # For simplicity, we'll just return "timeout". A more robust solution might try to find the message ID.
        # await self.application.bot.send_message(chat_id=target_chat_id, text=f"Approval request for '{article.title}' timed out.")
        return "timeout"

    def send_article_for_approval(self, article: Article, chat_id: Optional[str] = None) -> str:
        """
        Synchronous wrapper for send_article_for_approval_async.
        Useful if called from a non-async part of the application.
        Requires the bot event loop to be running (e.g., via `start_polling_threaded`).
        """
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # If called from within an async context that is already running
            # Use create_task to schedule the coroutine on the running loop
            asyncio.create_task(self.send_article_for_approval_async(article, chat_id))
            # We need a way to get the result back from the async task in a sync context.
            # This is tricky. For now, we'll make it block using run_until_complete
            # if the loop is not already running, or rely on the background task
            # to update USER_RESPONSES.
            # Given nest_asyncio, asyncio.run should now work even if a loop is already running.
            return loop.run_until_complete(self.send_article_for_approval_async(article, chat_id))
        else:
            # If the bot's main loop isn't running or we're in a context where we need to run it now.
            # This will block until the async function completes.
            return loop.run_until_complete(self.send_article_for_approval_async(article, chat_id))


    def start_polling(self, block=True):
        """Starts the Telegram bot's polling mechanism."""
        if hasattr(self.application, 'updater') and self.application.updater and self.application.updater.running:
            logger.info("Telegram bot is already polling.")
            return

        logger.info("Starting Telegram bot polling...")
        if block:
            self.application.run_polling()
        else:
            import threading
            import asyncio

            def polling_thread_target():
                """Target for the polling thread to ensure an event loop is set."""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                # run_polling is a blocking call that will create and run its own asyncio loop.
                # By setting the loop for the thread, we ensure it has the context it needs.
                self.application.run_polling()

            self.polling_thread = threading.Thread(target=polling_thread_target, daemon=True)
            self.polling_thread.start()
            logger.info("Telegram bot polling started in a background thread.")
            time.sleep(1)


    async def stop_polling(self):
        """Stops the Telegram bot's polling mechanism if running."""
        if self.application.updater and self.application.updater.running:
            logger.info("Stopping Telegram bot polling...")
            await self.application.updater.stop()
            # If running in a separate thread, join it.
            if hasattr(self, 'polling_thread') and self.polling_thread.is_alive():
                self.polling_thread.join(timeout=5)
                if self.polling_thread.is_alive():
                    logger.warning("Polling thread did not terminate gracefully.")
            logger.info("Telegram bot polling stopped.")
        else:
            logger.info("Telegram bot is not currently polling.")

async def main_test_async(notifier: TelegramNotifier, test_config: Config):
    """Async main function for testing."""
    logger.info("Async test: Sending a test message...")
    await notifier.send_message_async(f"Async Test: Hello from the LinkedIn AI Bot! Your chat ID is {test_config.telegram_chat_id}", chat_id=test_config.telegram_chat_id)

    logger.info("Async test: Sending a test article for approval...")
    test_article = Article(
        title="Test Article: The Future of AI",
        url="https://example.com/ai-future",
        source="Test Source",
        summary="This is a fascinating test summary about the future of AI and its potential impacts."
    )
    response = await notifier.send_article_for_approval_async(test_article, chat_id=test_config.telegram_chat_id)
    logger.info(f"Async test: Approval response: {response}")
    if response == "post":
        await notifier.send_message_async(f"Async Test: You chose to 'post' '{test_article.title}'.", chat_id=test_config.telegram_chat_id)
    elif response == "ignore":
        await notifier.send_message_async(f"Async Test: You chose to 'ignore' '{test_article.title}'.", chat_id=test_config.telegram_chat_id)
    else:
        await notifier.send_message_async(f"Async Test: Action for '{test_article.title}' was '{response}'.", chat_id=test_config.telegram_chat_id)

    # Keep polling running for a bit to receive callbacks if not run in thread
    # await asyncio.sleep(notifier.user_interaction_timeout + 10) # only if not threaded polling

if __name__ == "__main__":
    import asyncio
    # Setup basic logging for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Load configuration (ensure .env file has TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    from config import load_config # Assuming config.py is in parent directory
    test_config = load_config()

    if not test_config or not test_config.telegram_bot_token or not test_config.telegram_chat_id:
        logger.error("Telegram Bot Token or Chat ID is not configured in .env file. Exiting test.")
    else:
        logger.info(f"Test configured for Telegram Bot Token: ...{test_config.telegram_bot_token[-5:]} and Chat ID: {test_config.telegram_chat_id}")

        notifier = TelegramNotifier(token=test_config.telegram_bot_token, default_chat_id=test_config.telegram_chat_id)

        # To test approval flow, the bot needs to be polling for updates (callbacks)
        # Run polling in a separate thread so the main script can continue
        notifier.start_polling(block=False) # Starts polling in a background thread

        try:
            # --- Synchronous Test (simulates usage from main.py) ---
            logger.info("--- Starting Synchronous Test ---")
            notifier.send_message(f"Sync Test (1/2): Hello from the LinkedIn AI Bot! This is a synchronous test message sent to chat ID {test_config.telegram_chat_id}.")

            test_article_sync = Article(
                title="Sync Test Article: AI in Daily Life",
                url="https://example.com/ai-daily",
                source="Sync Test Source",
                summary="A synchronous test summary exploring how AI is becoming integral to our daily routines."
            )
            logger.info(f"Sync Test (2/2): Sending article '{test_article_sync.title}' for approval...")
            # This call will block until a response or timeout
            sync_response = notifier.send_article_for_approval(test_article_sync)
            logger.info(f"Sync Test: Approval response for '{test_article_sync.title}': {sync_response}")

            if sync_response == "post":
                notifier.send_message(f"Sync Test: You chose to 'post' '{test_article_sync.title}'.")
            elif sync_response == "ignore":
                notifier.send_message(f"Sync Test: You chose to 'ignore' '{test_article_sync.title}'.")
            else: # timeout or error
                notifier.send_message(f"Sync Test: Action for '{test_article_sync.title}' was '{sync_response}'.")

            logger.info("--- Synchronous Test Finished ---")
            logger.info("Waiting a few seconds before starting async test...")
            time.sleep(5)

            # --- Asynchronous Test (how you might use it with asyncio directly) ---
            # This part requires an event loop.
            logger.info("--- Starting Asynchronous Test (requires interaction in Telegram) ---")
            # We need to run the async test function in the bot's event loop or a new one.
            # Since polling is already running in its own thread with its own loop,
            # we can schedule tasks on that loop.

            # If notifier.application.updater.loop is accessible and running:
            if notifier.application and hasattr(notifier.application, '_updater') and notifier.application._updater and notifier.application._updater.loop:
                asyncio.run_coroutine_threadsafe(main_test_async(notifier, test_config), notifier.application._updater.loop).result(timeout=notifier.user_interaction_timeout + 30)
            else: # Fallback to running a new loop (might conflict if polling not set up carefully)
                logger.warning("Could not access bot's running loop for async test, running in new loop.")
                asyncio.run(main_test_async(notifier, test_config))

            logger.info("--- Asynchronous Test Finished (or timed out if no interaction) ---")
            logger.info(f"Test concluded. Bot will continue polling in the background for {notifier.user_interaction_timeout // 60} more minutes if you want to test /start or other interactions.")
            logger.info(f"You might need to stop the script manually (Ctrl+C) if it doesn't exit due to the polling thread.")

            # Keep main thread alive for a while so background polling thread can process callbacks
            # This is mainly for testing; in production, the application might run indefinitely or be scheduled.
            time.sleep(notifier.user_interaction_timeout + 10) # Wait for potential interactions

        except Exception as e:
            logger.error(f"An error occurred during the Telegram bot test: {e}", exc_info=True)
        finally:
            logger.info("Stopping Telegram bot polling at the end of the test...")
            notifier.stop_polling()
            logger.info("Test script finished.")
            # If using asyncio.run() for the async test, the loop is closed.
            # If using run_coroutine_threadsafe, the bot's loop is managed by the polling thread.
            # Ensure all tasks are completed or cancelled if necessary for clean exit.
            # Python might hang if daemon threads are still active and not explicitly joined/stopped.
            # The `daemon=True` for polling_thread should allow exit once main thread finishes.

# How to get your Telegram Chat ID:
# 1. Send a message to your bot.
# 2. Go to `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` in your browser.
# 3. Look for `"chat":{"id":YOUR_CHAT_ID, ...}`. Use this `YOUR_CHAT_ID`.
# Alternatively, the /start command in this script will tell you the chat ID.

# python-telegram-bot v20+ uses asyncio heavily.
# `send_article_for_approval` is tricky because it needs to be blocking from the perspective
# of the main script's sequential workflow, but the underlying Telegram operations and
# waiting for callbacks are asynchronous.
# The current implementation uses a shared dictionary `USER_RESPONSES` and polling within
# `send_article_for_approval_async`.
# The `start_polling(block=False)` runs the bot's update polling in a background thread.
# The synchronous `send_article_for_approval` then runs its async counterpart `_async`
# and blocks until it gets a result or times out. This requires careful handling of asyncio event loops.
# The solution with `asyncio.run_coroutine_threadsafe` is generally more robust when mixing sync and async
# if the bot's event loop is running in a known thread.
# The simplified `loop.run_until_complete()` in the sync wrapper works if the bot isn't already fully managing its own complex async loop.
# Given `python-telegram-bot`'s architecture, running its polling in a dedicated thread is standard for sync apps.
