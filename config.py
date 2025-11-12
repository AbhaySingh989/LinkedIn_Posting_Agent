import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class Config:
    """
    Configuration class to hold all settings for the LinkedIn AI Agent.
    Loads values from environment variables.
    """
    def __init__(self):
        load_dotenv()  # Load environment variables from .env file

        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID") # Your Telegram user/chat ID

        # LinkedIn Credentials
        self.linkedin_email = os.getenv("LINKEDIN_EMAIL")
        self.linkedin_password = os.getenv("LINKEDIN_PASSWORD")

        # Article Sources - Enable/disable as needed
        self.enable_hackernews = os.getenv("ENABLE_HACKERNEWS", "true").lower() == "true"
        self.hackernews_max_articles = int(os.getenv("HACKERNEWS_MAX_ARTICLES", "5"))

        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.reddit_user_agent = os.getenv("REDDIT_USER_AGENT", f"LinkedInAIAgent/0.1 by YourUsername (UniqueId:{{os.urandom(4).hex()}})")
        
        # New Reddit configuration
        self.reddit_subreddits = [
            "generativeAI", "MachineLearning", "OpenAI", "singularity", "ChatGPT",
            "LargeLanguageModels", "AIethics", "Futurology", "artificial", "LocalLLaMA"
        ]
        self.reddit_max_articles_per_subreddit = int(os.getenv("REDDIT_MAX_ARTICLES_PER_SUBREDDIT", "2"))

        self.enable_techcrunch_ai = os.getenv("ENABLE_TECHCRUNCH_AI", "true").lower() == "true"
        self.techcrunch_ai_url = os.getenv("TECHCRUNCH_AI_URL", "https://techcrunch.com/category/artificial-intelligence/")
        self.techcrunch_max_articles = int(os.getenv("TECHCRUNCH_MAX_ARTICLES", "5"))

        # Optional: Arxiv (can be complex to parse relevant articles)
        self.enable_arxiv = os.getenv("ENABLE_ARXIV", "false").lower() == "true"
        self.arxiv_search_query = os.getenv("ARXIV_SEARCH_QUERY", "cat:cs.AI OR cat:cs.LG OR cat:stat.ML") # Example: AI, ML, LG
        self.arxiv_max_articles = int(os.getenv("ARXIV_MAX_ARTICLES", "3"))

        # LLM Settings
        self.llm_model_name = os.getenv("LLM_MODEL_NAME", "gemini-2.0-flash") # Or other compatible Gemini model
        self.summarization_prompt = os.getenv(
            "SUMMARIZATION_PROMPT",
            "Please provide a concise and engaging summary of the following article, suitable for a LinkedIn post. "
            "Highlight key insights and implications. The summary should be around 2-3 sentences. Article content: "
        )

        # LinkedIn Posting Settings
        self.linkedin_post_prefix = os.getenv("LINKEDIN_POST_PREFIX", "Check out this insightful AI article:")
        self.linkedin_post_suffix = os.getenv("LINKEDIN_POST_SUFFIX", "#AI #ArtificialIntelligence #TechTrends #LinkedInPost")

        # General Settings
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "10")) # seconds for HTTP requests
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("RETRY_DELAY", "5")) # seconds

        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_file_path = os.getenv("LOG_FILE_PATH") # Optional: For standard text log file
        self.log_json_file_path = os.getenv("LOG_JSON_FILE_PATH") # Optional: For JSON formatted log file

        # Scheduling
        self.schedule = os.getenv("SCHEDULE", "")


    def validate(self) -> bool:
        """
        Validates that essential configuration parameters are set.
        Returns True if configuration is valid, False otherwise.
        """
        required_vars = {
            "GEMINI_API_KEY": self.gemini_api_key,
            "TELEGRAM_BOT_TOKEN": self.telegram_bot_token,
            "TELEGRAM_CHAT_ID": self.telegram_chat_id,
            "LINKEDIN_EMAIL": self.linkedin_email,
            "LINKEDIN_PASSWORD": self.linkedin_password,
        }

        missing_vars = [var for var, val in required_vars.items() if not val]

        if missing_vars:
            logger.error(f"Missing required configuration variables: {', '.join(missing_vars)}")
            logger.error("Please set them in your .env file or environment.")
            return False

        if self.reddit_subreddits and (not self.reddit_client_id or not self.reddit_client_secret):
            logger.warning("Reddit subreddits are configured, but REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET is missing. Reddit will be skipped.")

        logger.info("Configuration loaded and validated successfully.")
        return True

def load_config() -> Config | None:
    """Loads and validates configuration."""
    config = Config()
    if config.validate():
        return config
    return None

# Example .env.example file content:
"""
# Gemini API Key
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID="YOUR_TELEGRAM_CHAT_ID" # Can be your user ID or a group/channel ID

# LinkedIn Credentials
LINKEDIN_EMAIL="your_linkedin_email@example.com"
LINKEDIN_PASSWORD="your_linkedin_password"

# Article Sources (true/false to enable/disable)
ENABLE_HACKERNEWS="true"
HACKERNEWS_MAX_ARTICLES="5"

REDDIT_CLIENT_ID="YOUR_REDDIT_APP_CLIENT_ID"         # Optional: For Reddit API access
REDDIT_CLIENT_SECRET="YOUR_REDDIT_APP_CLIENT_SECRET" # Optional: For Reddit API access
REDDIT_USER_AGENT="LinkedInAIAgent/0.1 by YourUsername" # Optional: Custom user agent for Reddit API
REDDIT_MAX_ARTICLES_PER_SUBREDDIT="2"

ENABLE_TECHCRUNCH_AI="true"
TECHCRUNCH_AI_URL="https://techcrunch.com/category/artificial-intelligence/"
TECHCRUNCH_MAX_ARTICLES="5"

ENABLE_ARXIV="false" # Arxiv can be noisy, enable with caution
ARXIV_SEARCH_QUERY="cat:cs.AI OR cat:cs.LG OR cat:stat.ML"
ARXIV_MAX_ARTICLES="3"

# LLM Settings
LLM_MODEL_NAME="gemini-2.0-flash"
# SUMMARIZATION_PROMPT="Provide a brief summary for this article for LinkedIn: "

# LinkedIn Posting Settings
# LINKEDIN_POST_PREFIX="Trending in AI: "
# LINKEDIN_POST_SUFFIX="#AI #MachineLearning #Innovation"

# General Settings
REQUEST_TIMEOUT="10" # seconds
MAX_RETRIES="3"
RETRY_DELAY="5" # seconds
LOG_LEVEL="INFO" # DEBUG, INFO, WARNING, ERROR, CRITICAL
"""

if __name__ == "__main__":
    # This is for testing the config loading locally
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    if config:
        logger.info("Configuration loaded successfully.")
        # You can print specific config values to test
        # print(f"Gemini Key: {config.gemini_api_key}")
        # print(f"Telegram Token: {config.telegram_bot_token}")
        # print(f"LinkedIn Email: {config.linkedin_email}")
    else:
        logger.error("Failed to load configuration.")

"""
Note on .env.example:
You should create a file named `.env` in the root of your project and copy the contents
of the .env.example (pasted within the triple quotes at the end of config.py) into it.
Then, fill in your actual API keys and credentials in the `.env` file.
The `.env` file should be added to your `.gitignore` to prevent committing sensitive data.
"""
