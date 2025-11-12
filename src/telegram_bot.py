import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from src.models import Article
from src.database import Database
from src.linkedin_poster import LinkedInPoster

logger = logging.getLogger(__name__)

# States for conversation handler
EDITING_SUMMARY = 1

from selenium.common.exceptions import WebDriverException

class TelegramNotifier:
    def __init__(self, config, db: Database):
        if not config.telegram_bot_token or not config.telegram_chat_id:
            raise ValueError("Telegram token and chat ID must be configured.")
        self.application = Application.builder().token(config.telegram_bot_token).build()
        self.chat_id = config.telegram_chat_id
        self.db = db
        try:
            self.linkedin_poster = LinkedInPoster(config)
        except WebDriverException:
            logger.error("Failed to initialize LinkedInPoster due to WebDriver issues. LinkedIn posting will be disabled.")
            self.linkedin_poster = None
        self.shutdown_event = asyncio.Event()

        # Handlers
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.edit_summary_start, pattern='^edit_')],
            states={
                EDITING_SUMMARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_new_summary)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_edit)],
        )

        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("shutdown", self.shutdown_command))
        self.application.add_handler(conv_handler)
        self.application.add_handler(CallbackQueryHandler(self.handle_post, pattern='^post_'))
        self.application.add_handler(CallbackQueryHandler(self.handle_ignore, pattern='^ignore_'))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles the /start command."""
        await update.message.reply_text(f"Bot started. Your chat ID is: {update.effective_chat.id}")

    async def send_article_for_approval(self, article: Article):
        """Sends an article to the user for approval non-blockingly."""
        logger.info(f"Sending article for approval: {article.url}")
        keyboard = [
            [InlineKeyboardButton("✅ Post to LinkedIn", callback_data=f"post_{article.url}")],
            [InlineKeyboardButton("📝 Edit Summary", callback_data=f"edit_{article.url}")],
            [InlineKeyboardButton("❌ Ignore", callback_data=f"ignore_{article.url}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = f"""*Title:* {article.title}

*Summary:*
{article.summary}

[Read More]({article.url})"""
        # Store the article object in context, keyed by URL, for later retrieval
        context_key = f"article_{article.url}"
        self.application.bot_data[context_key] = article

        await self.application.bot.send_message(
            chat_id=self.chat_id,
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Callback handler for the 'Post' button."""
        query = update.callback_query
        await query.answer("Processing...")
        url = query.data.split('_', 1)[1]
        context_key = f"article_{url}"
        article = self.application.bot_data.get(context_key)

        if article:
            if not self.linkedin_poster or not self.linkedin_poster.logged_in:
                logger.warning(f"Attempted to post article {article.url}, but LinkedIn poster is not available or not logged in.")
                await query.edit_message_text(text=f"⚠️ Could not post article: LinkedIn integration is disabled due to an error. The article has been marked as 'ignored'.")
                self.db.add_processed_article(url, 'ignored_poster_unavailable')
                return

            logger.info(f"Posting article: {article.url}")
            try:
                success = self.linkedin_poster.post_article(article)
                if success:
                    self.db.add_processed_article(url, 'posted')
                    await query.edit_message_text(text=f"✅ Successfully posted:\n{article.title}")
                else:
                    # The error is already logged inside post_article
                    await query.edit_message_text(text=f"❌ Failed to post article: {article.title}\nAn error occurred. Check logs for details.")
                    # Still mark as processed to avoid retries
                    self.db.add_processed_article(url, 'failed_to_post')

            except Exception as e:
                logger.error(f"An unexpected error occurred while handling post for {article.url}: {e}", exc_info=True)
                await query.edit_message_text(text=f"❌ An unexpected error occurred while posting: {article.title}\nError: {e}")
                self.db.add_processed_article(url, 'failed_to_post')
            finally:
                del self.application.bot_data[context_key]
        else:
            await query.edit_message_text(text="Error: Article data not found. It might have been processed already.")

    async def handle_ignore(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Callback handler for the 'Ignore' button."""
        query = update.callback_query
        await query.answer()
        url = query.data.split('_', 1)[1]
        context_key = f"article_{url}"
        article = self.application.bot_data.get(context_key)

        if article:
            self.db.add_processed_article(url, 'ignored')
            logger.info(f"Ignoring article: {url}")
            await query.edit_message_text(text=f"❌ Article ignored:\n{article.title}")
            del self.application.bot_data[context_key]
        else:
            await query.edit_message_text(text="Error: Article data not found.")

    async def edit_summary_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Starts the summary editing conversation."""
        query = update.callback_query
        await query.answer()
        url = query.data.split('_', 1)[1]
        context.user_data['editing_url'] = url
        await query.message.reply_text("Please send me the new summary for the article.")
        return EDITING_SUMMARY

    async def receive_new_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receives the new summary and updates the article."""
        new_summary = update.message.text
        url = context.user_data.get('editing_url')
        context_key = f"article_{url}"
        article = self.application.bot_data.get(context_key)

        if article:
            article.summary = new_summary
            self.application.bot_data[context_key] = article # Update the article in bot_data
            await update.message.reply_text("Summary updated. Now, what would you like to do?")
            # Resend the approval message with the updated summary
            await self.send_article_for_approval(article)
        else:
            await update.message.reply_text("Could not find the original article to update.")

        del context.user_data['editing_url']
        return ConversationHandler.END

    async def cancel_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancels the edit conversation."""
        await update.message.reply_text("Edit cancelled.")
        if 'editing_url' in context.user_data:
            del context.user_data['editing_url']
        return ConversationHandler.END

    async def shutdown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles the /shutdown command."""
        await update.message.reply_text("Bot is shutting down...")
        self.shutdown_event.set()

    async def run(self):
        """Runs the bot until shutdown is called."""
        logger.info("Telegram bot is running...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        await self.shutdown_event.wait()
        await self.application.updater.stop()
        await self.application.stop()
        logger.info("Telegram bot has shut down gracefully.")

    async def stop(self):
        """Stops the bot by setting the shutdown event."""
        logger.info("Orchestrator requesting Telegram bot shutdown.")
        self.shutdown_event.set()
