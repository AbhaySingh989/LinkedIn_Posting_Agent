# 🤖 Autonomous LinkedIn AI Agent 🤖

👤 **Author**

*   **Abhay Singh**
*   📧 Email: [abhay.rkvv@gmail.com](mailto:abhay.rkvv@gmail.com)
*   🐙 GitHub: [AbhaySingh989](https://github.com/AbhaySingh989)
*   💼 LinkedIn: [Abhay Singh](https://www.linkedin.com/in/abhay-pratap-singh-905510149/)

***

## 📖 About

This project is a fully automated Python-based LinkedIn agent that discovers trending AI articles, summarizes them using Google's Gemini LLM, and seeks user approval via Telegram before posting to LinkedIn. The agent is built using the CrewAI framework for orchestration and Crawl4AI for advanced web scraping.

## ✨ Features

### 🚀 Core Functionality

*   **📄 Trend Sourcing**: Monitors Hacker News, Reddit, TechCrunch AI, and ArXiv for new AI articles using Crawl4AI.
*   **🤖 AI Summarization**: Uses Google Gemini to generate concise summaries of articles.
*   **✅ Approval Workflow**: Sends article title, source, summary, and link to a specified Telegram chat, with "Post to LinkedIn", "Edit Summary", and "Ignore" inline buttons.
*   **🌐 Automated LinkedIn Posting**: Posts the article link and its AI-generated summary to LinkedIn using Selenium browser automation if approved.
*   **💾 Persistent Storage**: Remembers which articles have already been processed to avoid duplicate posts.
*   **⏰ Scheduling**: Runs automatically on a schedule defined in the `.env` file.

### 🎨 User Experience

*   **💬 Telegram Integration**: Native Telegram bot interface with inline keyboards for easy approval and editing.
*   **🔘 Interactive Buttons**: Easy-to-use buttons for all functions (no typing commands!).
*   **🎯 Progress Tracking**: Real-time progress updates in the console logs.

### 🛠️ Customization

*   **⚙️ Configurable**: Easily configure API keys, sources, post formatting, and behavior via an `.env` file.
*   **✏️ Custom Prompts**: Set personalized summarization instructions in the `.env` file.
*   **🔄 Source Management**: Enable or disable article sources as needed.

### 🔒 Security & Reliability

*   **🔐 Secure Configuration**: API keys and credentials stored safely in environment variables.
*   **❌ Error Handling**: Robust error handling and retry mechanisms.
*   **📝 Comprehensive Logging**: Detailed logs for monitoring and debugging.

***

## 🛠️ Installation

### Prerequisites

Before you begin, ensure you have:
*   🐍 Python 3.9 or higher installed.
*   📱 A Telegram account.
*   🔑 A Google Gemini API Key.
*   🌐 Google Chrome browser installed.

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd <your-repo-name>
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Create Environment File

Copy the contents of `.env.example` (if available) or create a new file named `.env` in the project root.

***

## ⚙️ Setup

### 🤖 Getting Your Telegram Bot Token

1.  Open Telegram and search for **@BotFather**.
2.  Start a chat and send the `/newbot` command.
3.  Follow the instructions to choose a name and username for your bot.
4.  Copy the **API token** provided by BotFather and add it to your `.env` file.

### 🆔 Getting Your Telegram Chat ID

1.  Run the agent for the first time.
2.  Send the `/start` command to your bot.
3.  The bot will reply with your Chat ID. Add this to your `.env` file.

### 🔑 Getting Your Google API Key

1.  Visit [Google AI Studio](https://aistudio.google.com/).
2.  Sign in and create a new API key.
3.  Copy the generated API key and add it to your `.env` file.

### 📝 Configure Environment Variables

Edit your `.env` file:

```env
# Gemini API Key
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID="YOUR_TELEGRAM_CHAT_ID"

# LinkedIn Credentials
LINKEDIN_EMAIL="your_linkedin_email@example.com"
LINKEDIN_PASSWORD="your_linkedin_password"

# Reddit API Credentials (Optional but Recommended)
REDDIT_CLIENT_ID="YOUR_REDDIT_CLIENT_ID"
REDDIT_CLIENT_SECRET="YOUR_REDDIT_CLIENT_SECRET"
REDDIT_USER_AGENT="YourApp/0.1 by YourUsername"

# ... and other configurations as needed
```

⚠️ **Important**: Never share or commit your `.env` file to version control!

***

## 🚀 Usage

### Starting the Agent

```bash
python main.py
```

The agent will run once by default. To run it on a schedule, set the `SCHEDULE` variable in your `.env` file. For example, to run every hour, set `SCHEDULE=hourly`.

### 📱 Using the Bot

1.  **Start the Bot**: The agent will automatically start fetching articles.
2.  **Receive Approval Requests**: The bot will send messages to your configured Telegram chat with article details and approval buttons.
3.  **Approve, Edit, or Ignore**:
    *   Click **✅ Post to LinkedIn** to approve.
    *   Click **📝 Edit Summary** to provide a new summary.
    *   Click **❌ Ignore** to skip the article.

***

## 🎯 Demo

The agent follows this workflow:

*   🚀 **Starting Processing** - Initialization and configuration loading.
*   🤖 **CrewAI Orchestration** - The CrewAI framework orchestrates the agents and tasks.
*   📥 **Fetching Articles** - The `ArticleFetcherAgent` fetches articles using Crawl4AI.
*   🤖 **AI Analysis** - The `SummarizerAgent` generates an intelligent summary with Google Gemini.
*   💬 **Requesting Approval** - The `TelegramBot` sends the summary and article to you on Telegram.
*   ✅ **Posting to LinkedIn** - If approved, the `LinkedInPosterAgent` posts to LinkedIn.
*   📝 **Done** - The agent finishes its run.

***

## 📁 Project Structure

```
.
├── README.md
├── requirements.txt
├── main.py             # Main entry point for the application
├── config.py           # Configuration loading and validation
├── .env.example        # Example environment variables file
├── src/
│   ├── __init__.py
│   ├── crew.py             # CrewAI agents, tasks, and crew definition
│   ├── database.py         # SQLite database handler
│   ├── article_fetcher.py  # Fetches articles from various sources
│   ├── llm_handler.py      # Handles interaction with Gemini LLM
│   ├── telegram_bot.py   # Manages Telegram bot communication
│   ├── linkedin_poster.py  # Handles LinkedIn posting via Selenium
│   └── utils.py            # Utility functions (e.g., logging setup)
└── (screenshots/)          # Optional: For example screenshots
```

***

## 🐛 Troubleshooting

### Common Issues

*   **❌ Bot not responding**:
    *   Check if your `TELEGRAM_BOT_TOKEN` is correct.
    *   Ensure the agent is running (`python main.py`).
*   **❌ AI processing fails**:
    *   Confirm your `GEMINI_API_KEY` is valid.
    *   Check your Google AI Studio quota/billing.
*   **❌ LinkedIn login issues**:
    *   LinkedIn may require a CAPTCHA or 2FA, which this script cannot handle.
    *   LinkedIn's website structure may have changed, breaking the Selenium selectors.
*   **❌ Scraper issues**:
    *   Websites like TechCrunch frequently change their layout, which can break the scrapers.

### 🔍 Debugging

*   Enable detailed logging by setting `LOG_LEVEL=DEBUG` in your `.env` file.
*   For LinkedIn issues, comment out the `--headless` option in `src/linkedin_poster.py` to watch the browser actions.

***

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1.  🍴 Fork the repository.
2.  🌿 Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  💾 Commit your changes (`git commit -m 'Add amazing feature'`).
4.  📤 Push to the branch (`git push origin feature/amazing-feature`).
5.  🔄 Open a Pull Request.

***

## 🙏 Acknowledgments

*   🤖 **Google AI** for the powerful Gemini model.
*   **CrewAI** and **Crawl4AI** for their amazing frameworks.
*   🔗 **The developers of `python-telegram-bot` and `Selenium`**.
*   🌟 **The Open Source Community** for continuous inspiration and support.

***

> Made with ❤️ by **Abhay Singh**

Turn trending articles into engaging LinkedIn posts with the power of AI!

***

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```text
MIT License

Copyright (c) 2025 Abhay Singh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify,merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
