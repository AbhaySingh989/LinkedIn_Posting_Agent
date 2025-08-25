# Project: Autonomous LinkedIn AI Agent

## Project Overview

This project is a Python-based autonomous agent that discovers trending AI articles, summarizes them using Google's Gemini LLM, and posts them to LinkedIn after receiving user approval via a Telegram bot.

The core technologies used are:
- **Python**: The main programming language.
- **Google Gemini**: For summarizing articles.
- **Telegram Bot API**: For user interaction and approval.
- **Selenium**: For browser automation to post on LinkedIn.
- **Requests & BeautifulSoup**: For fetching and parsing articles from various web sources.
- **PRAW (Python Reddit API Wrapper)**: For fetching articles from Reddit.

The project is structured into a `src` directory containing modules for each major functionality:
- `article_fetcher.py`: Fetches articles from Hacker News, Reddit, TechCrunch, and ArXiv.
- `llm_handler.py`: Interacts with the Gemini API to summarize articles.
- `telegram_bot.py`: Manages the Telegram bot for sending approval requests and receiving user responses.
- `linkedin_poster.py`: Handles logging into and posting on LinkedIn using Selenium.
- `config.py`: Manages configuration from environment variables.
- `main.py`: The main entry point that orchestrates the entire workflow.

## Building and Running

### Prerequisites

- Python 3.9+
- Google Chrome browser
- A Telegram account and a bot token
- A Google Gemini API key

### Setup

1.  **Clone the repository.**
2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Create a `.env` file** in the project root. You can copy the example from `config.py` and fill in your credentials for:
    - `GEMINI_API_KEY`
    - `TELEGRAM_BOT_TOKEN`
    - `TELEGRAM_CHAT_ID`
    - `LINKEDIN_EMAIL`
    - `LINKEDIN_PASSWORD`
    - (Optional) Reddit API credentials.

### Running the Agent

To run the agent, execute the `main.py` script:

```bash
python main.py
```

The agent will then:
1.  Fetch articles from the configured sources.
2.  For each article, generate a summary.
3.  Send the article title, source, summary, and link to the configured Telegram chat for approval.
4.  If approved, it will post the article to LinkedIn.

## Development Conventions

- **Configuration**: All configuration is managed through environment variables loaded from a `.env` file via the `python-dotenv` library. The `config.py` module centralizes access to these settings.
- **Logging**: The project uses Python's built-in `logging` module. Logging is configured in `src/utils.py` and can be customized via the `LOG_LEVEL` environment variable. JSON logging is also supported.
- **Dependencies**: Project dependencies are listed in `requirements.txt`.
- **Code Style**: The code follows standard Python conventions (PEP 8).
- **Error Handling**: The application includes error handling and retry mechanisms for network requests and API calls.
- **Modularity**: The code is organized into modules with specific responsibilities, promoting separation of concerns.
- **Asynchronous Operations**: The project uses `asyncio` for some operations, particularly for fetching articles from multiple sources concurrently and for the Telegram bot. `nest_asyncio` is used to allow `asyncio` to work within environments that may already have a running event loop.
