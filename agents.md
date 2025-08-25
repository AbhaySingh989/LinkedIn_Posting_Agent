# Project Overview

This project is an autonomous LinkedIn agent. Currently an MVP, the goal is to transform it into a production-ready application. The agent discovers trending AI articles, summarizes them using Google's Gemini LLM, and seeks user approval via Telegram before posting to LinkedIn.

The development plan is outlined in `tasks.md` and focuses on moving the project from its current MVP state to a robust, reliable, and feature-rich application.

# Development Roadmap

The development roadmap is divided into four main epics, as defined in `tasks.md`:

1.  **Epic 1: Core Stability and Reliability**: This is the highest priority and focuses on fixing critical bugs, upgrading dependencies, and making the existing features more robust.
2.  **Epic 2: Agent Orchestration and Intelligence**: This epic focuses on re-architecting the agent using modern AI-native frameworks like CrewAI and Crawl4AI to make it more intelligent and maintainable.
3.  **Epic 3: Feature Enhancements and Automation**: This epic focuses on adding new features like scheduling, content editing, and other improvements to make the agent more autonomous.
4.  **Epic 4: Comprehensive Documentation**: This epic focuses on creating comprehensive documentation to make the project easy to understand, maintain, and extend.

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

The development process will follow the tasks outlined in `tasks.md` to ensure a stable and organized progression from MVP to production.

*   **Priority**: All development should follow the priorities outlined in `tasks.md`, starting with **Epic 1: Core Stability and Reliability**.
*   **Task-Driven Development**: Each development effort should correspond to a specific task in the `tasks.md` file.
*   **Code Style**: The project follows the PEP 8 style guide.
*   **Logging**: The project uses a custom JSON logger to log messages.
*   **Configuration**: The project uses a `.env` file for configuration.
*   **Modularity**: The project is divided into several modules, each with a specific responsibility.