
# Project Overview

This project is a Python-based autonomous LinkedIn agent that discovers trending AI articles, summarizes them using Google's Gemini LLM, and seeks user approval via Telegram before posting to LinkedIn.

The agent's workflow is as follows:
1.  **Fetch Articles**: Fetches articles from various sources like Reddit.
2.  **Summarize**: Summarizes the articles using the Gemini LLM.
3.  **Approval**: Sends the summarized article to a Telegram chat for approval.
4.  **Post to LinkedIn**: If approved, the agent posts the article to LinkedIn.

## Key Technologies

*   **Python**: The core language of the project.
*   **Google Gemini**: Used for summarizing articles.
*   **Telegram Bot**: Used for user interaction and approval.
*   **Selenium**: Used for browser automation to post on LinkedIn.

## Architecture

The project is structured into several modules:

*   `main.py`: The main entry point of the application.
*   `config.py`: Handles the configuration of the application.
*   `src/article_fetcher.py`: Fetches articles from various sources.
*   `src/llm_handler.py`: Handles the interaction with the Gemini LLM.
*   `src/telegram_bot.py`: Manages the Telegram bot.
*   `src/linkedin_poster.py`: Handles posting to LinkedIn.
*   `src/utils.py`: Provides utility functions like logging.

# Building and Running

## Prerequisites

*   Python 3.9 or higher
*   A Telegram account and a bot token.
*   A Google Gemini API key.
*   Google Chrome browser.

## Installation

1.  **Clone the repository**
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure the application**:
    *   Create a `.env` file in the root directory.
    *   Add the following environment variables to the `.env` file:
        ```
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
        TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
        TELEGRAM_CHAT_ID="YOUR_TELEGRAM_CHAT_ID"
        LINKEDIN_EMAIL="your_linkedin_email@example.com"
        LINKEDIN_PASSWORD="your_linkedin_password"
        REDDIT_CLIENT_ID="YOUR_REDDIT_CLIENT_ID"
        REDDIT_CLIENT_SECRET="YOUR_REDDIT_CLIENT_SECRET"
        REDDIT_USER_AGENT="YourApp/0.1 by YourUsername"
        ```

## Running the application

```bash
python main.py
```

# Development Conventions

*   **Coding Style**: The project follows the PEP 8 style guide.
*   **Logging**: The project uses a custom JSON logger to log messages.
*   **Configuration**: The project uses a `.env` file for configuration.
*   **Modularity**: The project is divided into several modules, each with a specific responsibility.
