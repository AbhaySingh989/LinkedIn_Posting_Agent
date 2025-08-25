
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

class TelegramBot:
    """
    Manages Telegram bot communication.
    """
    def __init__(self, token, chat_id):
        """
        Initializes the TelegramBot.

        Args:
            token (str): The Telegram bot token.
            chat_id (str): The Telegram chat ID.
        """
        self.application = Application.builder().token(token).build()
        self.chat_id = chat_id
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.button))
        logging.info("TelegramBot initialized.")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /start command.
        """
        await update.message.reply_text(f"Your chat ID is: {update.effective_chat.id}")

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles button presses.
        """
        query = update.callback_query
        await query.answer()
        # Here you would typically handle the callback data
        # For now, we'll just log it
        logging.info(f"Received callback data: {query.data}")

    async def send_article_for_approval(self, title, source, summary, url):
        """
        Sends an article to the user for approval.

        Args:
            title (str): The title of the article.
            source (str): The source of the article.
            summary (str): The summary of the article.
            url (str): The URL of the article.
        """
        keyboard = [
            [InlineKeyboardButton("✅ Post to LinkedIn", callback_data=f"post_{url}")],
            [InlineKeyboardButton("❌ Ignore", callback_data=f"ignore_{url}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = f"*Title:* {title}\n*Source:* {source}\n\n*Summary:*
{summary}"
        await self.application.bot.send_message(chat_id=self.chat_id, text=message, reply_markup=reply_markup, parse_mode='Markdown')

    def run(self):
        """
        Starts the bot.
        """
        self.application.run_polling()

