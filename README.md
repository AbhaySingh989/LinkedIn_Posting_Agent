# Autonomous LinkedIn AI Agent (Open Source)

This project is a fully automated Python-based LinkedIn agent that discovers trending AI articles, summarizes them using Google's Gemini LLM, and seeks user approval via Telegram before posting to LinkedIn.

## Features

- **Trend Sourcing**: Monitors Hacker News (API), Reddit r/artificialintelligence (API with scrape fallback), TechCrunch AI (scrape), and ArXiv (API) for new AI articles.
- **AI Summarization**: Uses Google Gemini Pro to generate concise summaries of articles.
- **Telegram Approval Workflow**: Sends article title, source, summary, and link to a specified Telegram chat, with "Post to LinkedIn" and "Ignore" inline buttons.
- **Automated LinkedIn Posting**: Posts the article link and its AI-generated summary to LinkedIn using Selenium browser automation if approved.
- **Configurable**: Easily configure API keys, sources, post formatting, and behavior via an `.env` file.
- **Modular Codebase**: Clean, well-documented, and modular Python code.
- **Error Handling & Logging**: Robust error handling, retry mechanisms, and detailed logging.

## Architecture & Flow

The agent operates through a sequence of steps orchestrated by `main.py`:

1.  **Configuration Load**: Loads API keys, credentials, and settings from the `.env` file via `config.py`.
2.  **Initialization**:
    *   `ArticleFetcher`: For sourcing articles.
    *   `LLMHandler`: For interacting with the Gemini API.
    *   `TelegramNotifier`: For Telegram bot interactions (starts polling in a background thread).
    *   `LinkedInPoster`: For Selenium-based LinkedIn automation.
3.  **Article Fetching**: `ArticleFetcher` queries enabled sources (Hacker News, Reddit, TechCrunch AI, ArXiv) for recent AI-related articles.
4.  **Processing Loop (for each unique article)**:
    *   **Summarization**: `LLMHandler` fetches the full content of the article (if not already text) and sends it to the Gemini API to generate a summary.
    *   **Telegram Approval**: `TelegramNotifier` sends a message to the configured Telegram chat ID containing the article title, source, generated summary, and the original article link, along with "Post to LinkedIn" and "Ignore" buttons. The agent waits for the user's response or a timeout.
    *   **LinkedIn Posting**:
        *   If "Post to LinkedIn" is chosen, `LinkedInPoster` logs into LinkedIn (using credentials from `.env`) and creates a new post with the summary and article link.
        *   If "Ignore" is chosen or the request times out, the article is skipped.
5.  **Cleanup**: After processing all articles (or if an error occurs), Selenium WebDriver is closed, and Telegram bot polling is stopped.

```mermaid
graph TD
    A[Start main.py] --> B{Load Config (.env)};
    B --> C[Initialize Components: Fetcher, LLM, Telegram, LinkedIn];
    C --> D[Start Telegram Bot Polling];
    D --> E[Fetcher: Get AI Articles];
    E --> F{Articles Found?};
    F -- No --> G[Log & End Run];
    F -- Yes --> H[For each Article];
    H --> I[LLM: Get Article Content & Summarize];
    I --> J[Telegram: Send for Approval (Title, Summary, Link)];
    J --> K{User Action?};
    K -- Ignore/Timeout --> H;
    K -- Approve --> L[LinkedIn Poster: Login & Post];
    L --> M{Post Successful?};
    M -- Yes --> N[Log Success];
    M -- No --> O[Log Failure & Notify Telegram];
    N --> H;
    O --> H;
    H -- All Articles Processed --> P[Stop Telegram Polling];
    P --> Q[Close LinkedIn WebDriver];
    Q --> G;
```

## Tech Stack

-   **Programming Language**: Python 3.9+
-   **LLM**: Google Gemini Pro (via `google-generativeai` SDK)
-   **Telegram Bot**: `python-telegram-bot`
-   **LinkedIn Automation**: `Selenium` with `webdriver-manager` (Chrome)
-   **Web Scraping/API Interaction**: `requests`, `beautifulsoup4`
-   **Configuration**: `python-dotenv`
-   **Logging**: Python's built-in `logging` module
-   **Optional Scheduling**: `schedule` (example provided)

## Project Structure

```
.
├── README.md
├── requirements.txt
├── main.py             # Main orchestrator script
├── config.py           # Configuration loading and validation
├── .env.example        # Example environment variables file
├── src/
│   ├── __init__.py
│   ├── article_fetcher.py  # Fetches articles from various sources
│   ├── llm_handler.py      # Handles interaction with Gemini LLM
│   ├── telegram_bot.py   # Manages Telegram bot communication
│   ├── linkedin_poster.py  # Handles LinkedIn posting via Selenium
│   └── utils.py            # Utility functions (e.g., logging setup)
└── (screenshots/)          # Optional: For example screenshots
```

## Setup and Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/autonomous-linkedin-ai-agent.git # Replace with your actual repo URL if forked
    cd autonomous-linkedin-ai-agent
    ```

2.  **Create a Virtual Environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    This will also install `webdriver-manager`, which automatically downloads the correct ChromeDriver if you have Google Chrome installed. Ensure Google Chrome browser is installed on your system.

4.  **Set Up Environment Variables**:
    *   Copy `.env.example` to a new file named `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and fill in your actual credentials and API keys:
        *   `GEMINI_API_KEY`: Your Google Gemini API key.
        *   `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token.
        *   `TELEGRAM_CHAT_ID`: Your Telegram Chat ID where notifications will be sent.
        *   `LINKEDIN_EMAIL`: Your LinkedIn login email.
        *   `LINKEDIN_PASSWORD`: Your LinkedIn login password.
        *   `REDDIT_CLIENT_ID` & `REDDIT_CLIENT_SECRET` (Optional, for Reddit API access, highly recommended over scraping for reliability).
        *   Review other settings like `ENABLE_*` flags for sources, `*_MAX_ARTICLES`, etc.

## Configuration Details

### 1. Telegram Bot Setup

*   **Create a Bot**:
    1.  Open Telegram and search for "BotFather".
    2.  Send `/newbot` command to BotFather.
    3.  Follow the instructions to choose a name and username for your bot.
    4.  BotFather will provide you with an **API Token**. Copy this token and paste it into your `.env` file as `TELEGRAM_BOT_TOKEN`.
*   **Get Your Chat ID**:
    1.  After setting up the bot token in `.env` and running the agent for the first time (or by directly interacting with your bot), send the `/start` command to your newly created bot in a private chat.
    2.  The bot (if `main.py` or `telegram_bot.py` is running and configured with the token) should reply with a message including "Your chat ID is: `YOUR_CHAT_ID`".
    3.  Alternatively, you can use other methods like sending a message to your bot and then checking `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` in a browser.
    4.  Paste this Chat ID into `TELEGRAM_CHAT_ID` in your `.env` file.

### 2. Google Gemini API Key

1.  Go to [Google AI Studio (formerly MakerSuite)](https://aistudio.google.com/).
2.  Sign in with your Google account.
3.  Navigate to "Get API key" (or a similar section, e.g., "API keys" in a project) to create or retrieve your API key.
4.  Ensure the Gemini API (e.g., "Generative Language API" or "Vertex AI API" if using Vertex models) is enabled for your project in Google Cloud Console if required.
5.  Copy the API key and paste it into `GEMINI_API_KEY` in your `.env` file.

### 3. Reddit API (Optional but Recommended)

Using the Reddit API is more reliable than scraping for fetching posts from subreddits.
1.  Go to [Reddit Apps](https://www.reddit.com/prefs/apps).
2.  Scroll down and click "are you a developer? create an app...".
3.  Fill in the details:
    *   **Name**: e.g., "LinkedInAIAgent" (or any unique name)
    *   **Type**: Select "script".
    *   **Description**: (Optional)
    *   **About URL**: (Optional)
    *   **Redirect URI**: e.g., `http://localhost:8080` (This won't actually be used for a script app but is often a required field).
4.  Click "create app".
5.  You will see your app listed. The **Client ID** is shown below the app name (it's a string of characters). The **Client Secret** (labeled "secret") is also provided.
6.  Copy these into `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` in your `.env` file. Set `REDDIT_USER_AGENT` to something descriptive, e.g., "LinkedInAIAgent/0.1 by YourRedditUsername".

### 4. LinkedIn Credentials & Automation Notes

*   Provide your LinkedIn email and password in the `.env` file for `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD`.
*   **Important Considerations**:
    *   **Terms of Service**: Automating LinkedIn actions, especially with tools like Selenium, can be against their Terms of Service. This can lead to account restrictions or permanent bans if not used carefully and responsibly. **Use this feature at your own risk.**
    *   **Fragility**: LinkedIn's website structure (HTML, CSS classes, element IDs) changes frequently without notice. This makes Selenium scripts highly prone to breaking. The selectors used in `linkedin_poster.py` may require regular updates.
    *   **Detection**: While the script attempts to use headless Chrome and other measures (like modifying `navigator.webdriver`) to appear less like a bot, sophisticated detection mechanisms can still identify automated activity.
    *   **Login Challenges**: Frequent automated logins or activity from new/suspicious IP addresses might trigger CAPTCHAs, two-factor authentication (2FA) prompts, or other security verifications. This script is **not** designed to handle these advanced login challenges. If you encounter them, manual intervention will be needed, or the login will fail.
    *   **Best Practices**: If you use this, consider running it infrequently, with natural delays (some are already in the script), and from a stable IP address if possible.

## Running the Agent

1.  Ensure your virtual environment is activated and all dependencies (including Google Chrome browser) are installed.
2.  Ensure your `.env` file is correctly configured with all necessary API keys, credentials, and desired settings.
3.  Run the main script from the project root directory:
    ```bash
    python main.py
    ```
    The agent will start, log its actions to the console, fetch articles, and if any are found, it will begin the summarization and Telegram approval process. Check your Telegram for messages from the bot.

### Scheduling (Optional)

The `main.py` script includes a commented-out example using the `schedule` library to run the agent periodically (e.g., every hour). To enable this:
1.  Uncomment the `schedule` related lines at the end of `main.py`.
2.  The script will then run continuously, executing the `main()` function at the configured interval. Ensure the logic within `main()` is suitable for repeated execution (the current design is).

## Debugging Tips

*   **Check Logs**: The agent logs extensively to the console. The log level can be set in `.env` (e.g., `LOG_LEVEL="DEBUG"` for more detail). Optionally, configure `LOG_FILE_PATH` in `.env` to log to a file for persistent records.
*   **`.env` Configuration**: Double-check all API keys, tokens, chat IDs, and credentials in your `.env` file. Ensure the file is correctly named `.env` (not `.env.example`) and is in the project root.
*   **Python Version**: Ensure you are using Python 3.9 or newer, as specified in the tech stack.
*   **Dependencies**: Verify that all packages listed in `requirements.txt` are installed in your active virtual environment (`pip list`).
*   **Selenium/WebDriver Issues (`linkedin_poster.py`)**:
    *   **LinkedIn HTML Changes**: If posting fails, the most common reason is LinkedIn has updated its website HTML, breaking the Selenium selectors. You'll need to inspect LinkedIn's page structure and update the XPaths/selectors in `linkedin_poster.py`.
    *   **Chrome & ChromeDriver**: Ensure Google Chrome browser is installed and up-to-date. `webdriver-manager` should handle ChromeDriver downloads, but if issues persist (e.g., "SessionNotCreatedException"), there might be a version mismatch or WebDriverManager might be blocked from downloading. Check `WDM` logs (set to WARNING by default).
    *   **Debugging Visually**: For debugging Selenium interactions, temporarily comment out the `--headless` option in `linkedin_poster.py` to watch the browser perform the actions.
    *   **Screenshots**: The `linkedin_poster.py` has commented-out lines like `self.driver.save_screenshot(...)`. Uncomment these at points of failure to capture what the browser sees.
*   **Content Fetching (`article_fetcher.py`)**:
    *   **Scraper Breakage**: Website structures (TechCrunch, Reddit scrape fallback) change, which can break scrapers. The selectors in `article_fetcher.py` may need updating.
    *   **`get_article_content` Quality**: The generic content extraction in `get_article_content` uses heuristics. For some websites, it might not extract text cleanly or might miss content. More advanced libraries like `newspaper3k` or `trafilatura` could be integrated for better results but add dependencies.
*   **API Quotas/Errors (Gemini, Reddit)**:
    *   All APIs have rate limits. If you run the agent too frequently or process a very large number of articles, you might hit these limits. Check the respective API documentation for details. The script includes basic retry logic.
    *   Ensure your Gemini API key is active, correctly entered, and has the necessary permissions/APIs enabled in its Google Cloud project.
    *   Similarly, check Reddit API credentials if you're using the API method.

## Example Workflow Outputs

1.  **Console Output (Agent Running - Snippet)**:
    ```
    [timestamp] - __main__ - INFO - Autonomous LinkedIn AI Agent started.
    [timestamp] - config - INFO - Configuration loaded and validated successfully.
    [timestamp] - __main__ - INFO - Starting Telegram bot polling in background...
    [timestamp] - telegram_bot - INFO - Starting Telegram bot polling...
    [timestamp] - telegram_bot - INFO - Telegram bot polling started in a background thread.
    [timestamp] - __main__ - INFO - Fetching trending AI articles...
    [timestamp] - src.article_fetcher - INFO - Fetching articles from Hacker News...
    [timestamp] - src.article_fetcher - INFO - Fetched X articles from Hacker News.
    ...
    [timestamp] - src.article_fetcher - INFO - Total unique articles fetched: Z
    [timestamp] - __main__ - INFO - Processing article: 'Some Amazing AI Article Title' (http://example.com/article) from TechCrunch AI
    [timestamp] - src.llm_handler - INFO - Fetching article content from URL for summarization: http://example.com/article
    [timestamp] - src.article_fetcher - INFO - Fetching content for article: http://example.com/article
    [timestamp] - src.llm_handler - INFO - Summary generated successfully for URL.
    [timestamp] - __main__ - INFO - Summary generated for 'Some Amazing AI Article Title'.
    [timestamp] - __main__ - INFO - Sending article to Telegram for approval: Some Amazing AI Article Title
    [timestamp] - src.telegram_bot - INFO - Article 'Some Amazing AI Article Title' sent for approval with ID article_xxxxxxxx.
    ```

2.  **Telegram Notification (Received by User)**:
    You will receive a message from your bot in the chat specified by `TELEGRAM_CHAT_ID`:

    ```html
    <b>New AI Article Suggestion:</b>

    <b>Title:</b> Some Amazing AI Article Title
    <b>Source:</b> TechCrunch AI
    <b>Summary:</b>
    This is an AI-generated summary of the article, highlighting its key points and implications for LinkedIn, crafted by Gemini.

    <a href='http://example.com/article'>Read Full Article</a>

    Do you want to post this to LinkedIn?
    ```
    (Followed by inline buttons: [✅ Post to LinkedIn] [❌ Ignore])

3.  **After User Action in Telegram (Console Logs)**:
    *   If "✅ Post to LinkedIn" is clicked:
        ```
        [timestamp] - src.telegram_bot - INFO - User action 'post' recorded for article ID 'article_xxxxxxxx'.
        [timestamp] - __main__ - INFO - Article 'Some Amazing AI Article Title' approved for posting by user.
        [timestamp] - src.linkedin_poster - INFO - Attempting to log in to LinkedIn...
        [timestamp] - src.linkedin_poster - INFO - Successfully logged in to LinkedIn.
        [timestamp] - src.linkedin_poster - INFO - Attempting to post article to LinkedIn: Some Amazing AI Article Title
        ...
        [timestamp] - src.linkedin_poster - INFO - Article 'Some Amazing AI Article Title' posted successfully to LinkedIn.
        [timestamp] - __main__ - INFO - Successfully posted 'Some Amazing AI Article Title' to LinkedIn.
        ```
    *   If "❌ Ignore" is clicked:
        ```
        [timestamp] - src.telegram_bot - INFO - User action 'ignore' recorded for article ID 'article_xxxxxxxx'.
        [timestamp] - __main__ - INFO - Article 'Some Amazing AI Article Title' was ignored by user via Telegram.
        ```
    *   If the request times out (default 1 hour):
        ```
        [timestamp] - src.telegram_bot - WARNING - Timeout waiting for approval for article ID article_xxxxxxxx ('Some Amazing AI Article Title').
        [timestamp] - __main__ - INFO - Approval request for 'Some Amazing AI Article Title' timed out.
        ```

4.  **LinkedIn Post (Example, if approved and successful)**:
    A new post will appear on your LinkedIn profile, formatted similarly to this (prefix and suffix are configurable in `.env`):

    > Check out this insightful AI article:
    >
    > This is an AI-generated summary of the article, highlighting its key points and implications for LinkedIn, crafted by Gemini.
    >
    > Read more: http://example.com/article
    >
    > \#AI \#ArtificialIntelligence \#TechTrends \#Innovation \#LLM

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change. Ensure any contributions maintain code quality, include documentation where necessary, and consider the project's constraints (open source tools, specified technology stack). Adherence to the general coding style and structure is appreciated.

## License

This project is intended for open-source demonstration and personal use. It is provided "as is" without warranty of any kind. While no specific license file (e.g., `LICENSE.md`) has been generated as part of this automated process, it's generally understood that such projects shared publicly would fall under a permissive license like MIT if the original prompter intended to distribute it. Please add a `LICENSE` file (e.g., MIT License) if you plan to distribute this code more formally.
