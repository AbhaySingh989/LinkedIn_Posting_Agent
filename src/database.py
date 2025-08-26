import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Database:
    """
    Handles database operations for the LinkedIn AI Agent.
    """
    def __init__(self, db_path: str = "linkedin_agent.db"):
        """
        Initializes the Database handler.

        Args:
            db_path (str): The path to the SQLite database file.
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._setup_database()

    def _setup_database(self):
        """
        Connects to the database and creates the necessary tables if they don't exist.
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            # Create table for processed articles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_articles (
                    id INTEGER PRIMARY KEY,
                    url TEXT NOT NULL UNIQUE,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
            logger.info(f"Database setup complete at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database error during setup: {e}")
            self.conn = None # Ensure connection is not used if setup fails

    def article_is_processed(self, url: str) -> bool:
        """
        Checks if an article with the given URL has already been processed.

        Args:
            url (str): The URL of the article to check.

        Returns:
            bool: True if the article has been processed, False otherwise.
        """
        if not self.conn:
            logger.error("Cannot check article; database connection not available.")
            return False # Fail safe: assume not processed if DB is down
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM processed_articles WHERE url = ?", (url,))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Database error when checking article URL {url}: {e}")
            return False

    def add_processed_article(self, url: str) -> bool:
        """
        Adds a new article's URL to the database of processed articles.

        Args:
            url (str): The URL of the article to add.

        Returns:
            bool: True if the article was added successfully, False otherwise.
        """
        if not self.conn:
            logger.error("Cannot add article; database connection not available.")
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO processed_articles (url) VALUES (?)", (url,))
            self.conn.commit()
            logger.info(f"Added processed article to database: {url}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Attempted to add duplicate article URL to database: {url}")
            return False # It already exists, which is not an error in this context
        except sqlite3.Error as e:
            logger.error(f"Database error when adding article URL {url}: {e}")
            return False

    def close(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")
            self.conn = None
