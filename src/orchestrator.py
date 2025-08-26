import logging
from src.article_fetcher import ArticleFetcher
from src.database import Database
from src.telegram_bot import TelegramNotifier
from src.crew import create_summary_crew
from src.models import Article

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, config):
        self.config = config
        self.article_fetcher = ArticleFetcher(config)
        self.db = Database()
        self.notifier = TelegramNotifier(config, self.db)

    async def run(self):
        logger.info("Orchestrator starting...")
        # The Telegram bot will be started at the end to handle all user input
        # This prevents the script from hanging while waiting for the bot to poll.

        # Fetch articles
        logger.info("Fetching all articles...")
        articles = await self.article_fetcher.fetch_all_articles()
        logger.info(f"Fetched {len(articles)} articles.")

        new_articles = []
        for article in articles:
            if not self.db.article_is_processed(article.url):
                new_articles.append(article)
        logger.info(f"Found {len(new_articles)} new articles to process.")

        if not new_articles:
            logger.info("No new articles to process. Shutting down Telegram bot.")
            await self.notifier.stop()
            return

        # Process each new article
        for article in new_articles:
            logger.info(f"Processing article: {article.title}")

            # 1. Get content using Crawl4AI
            logger.info(f"Fetching content for {article.url}...")
            content = await self.article_fetcher.fetch_article_content(article.url)

            if not content:
                logger.warning(f"Could not fetch content for {article.url}. Skipping.")
                self.db.add_processed_article(article.url, status='skipped_no_content')
                continue

            # 2. Use CrewAI to generate a summary
            logger.info("Invoking CrewAI to generate summary...")
            summary_crew = create_summary_crew()
            crew_input = {
                'article_title': article.title,
                'article_content': content
            }
            summary = summary_crew.kickoff(inputs=crew_input)
            logger.info(f"Generated summary: {summary}")

            # 3. Send for approval
            article_with_summary = Article(
                title=article.title,
                url=article.url,
                summary=summary
            )
            logger.info(f"Sending article to Telegram for approval: {article.title}")
            await self.notifier.send_article_for_approval(article_with_summary)

        logger.info("All new articles have been sent for approval.")
        logger.info("Orchestrator finished. The Telegram bot will continue running to handle user responses.")
        # Note: We don't stop the notifier here, as it needs to listen for user replies.
        # A more robust solution would have a separate process for the bot.
        # For this project, we'll let it run until the main script is stopped.
        # To gracefully shutdown, we'll add a command to the bot.
        await self.notifier.updater.start_polling()
