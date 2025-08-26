# LinkedIn Posting Agent: Requirements and Tasks

## How to Read This Document

This is a living document that outlines the requirements and development tasks for transforming the LinkedIn Posting Agent from an MVP into a production-ready application. It is designed to provide clear, actionable instructions for any developer.

**Structure:**

1.  **Section 1: Requirements (User Stories):** This section describes the *why* behind the work. It is organized into **Epics**, which are high-level project goals. Each Epic contains specific **User Stories**, which describe a feature from a user's perspective. Each story is assigned a **Priority** (High, Medium, Low).

2.  **Section 2: Sequential Task List:** This section describes the *how*. It provides a checklist of concrete development tasks. The tasks are grouped by Epic and should be completed in the order they are listed to ensure a stable development process.

**Development Philosophy:**
Work should be completed in order of priority, starting with the **Epic 1: Core Stability and Reliability**. This epic addresses critical bugs and foundational issues that must be resolved before new features can be added.

---

## Section 1: Requirements (User Stories)

### Epic 1: Core Stability and Reliability

**Goal:** To resolve critical bugs, upgrade core components, and make the agent's existing operations more robust and less prone to failure. This is the highest priority and foundational for all other improvements.

---

**User_Story: 1.1**
As the agent operator, I want the agent to remember which articles it has already processed, so that it does not send the same article for approval multiple times.
*Status: To Do*
*Priority: High*

#### Acceptance Criteria
1.  WHEN the agent fetches an article, THEN it SHALL check a persistent database (SQLite) to see if the article's URL has been processed before.
2.  IF the article has been processed, THEN the agent SHALL ignore it.
3.  WHEN an article is processed, THEN its URL and a timestamp SHALL be saved to the database.

---

**User_Story: 1.2**
As the agent operator, I want the agent's Telegram integration to be stable, so that it does not crash when handling user responses.
*Status: To Do*
*Priority: High*

#### Acceptance Criteria
1.  WHEN a user clicks a button on Telegram, THEN the agent SHALL handle the callback without raising an `asyncio` event loop error.
2.  The agent's code SHALL be refactored to use a single, consistent `asyncio` event loop.
3.  The `nest_asyncio` library SHALL be removed.

---

**User_Story: 1.3**
As the agent operator, I want the agent to use up-to-date and non-deprecated libraries, so that it is secure, efficient, and maintainable.
*Status: To Do*
*Priority: High*

#### Acceptance Criteria
1.  The `google-generativeai` library SHALL be replaced with the recommended `google-genai` package.
2.  All other libraries in `requirements.txt` SHALL be updated to their latest stable versions.
3.  The agent's code SHALL be updated to be compatible with the new library versions.

---

**User_Story: 1.4**
As the agent operator, I want the agent to reliably fetch articles from all configured sources (Hacker News, TechCrunch), not just Reddit.
*Status: To Do*
*Priority: High*

#### Acceptance Criteria
1.  WHEN the agent runs, THEN it SHALL successfully identify and fetch new articles from Hacker News and TechCrunch.
2.  The web scraping selectors for these sources SHALL be updated to match their current HTML structure.

---

**User_Story: 1.5**
As the agent operator, I want the LinkedIn posting process to be highly reliable, so that approved articles are posted successfully without manual intervention.
*Status: To Do*
*Priority: High*

#### Acceptance Criteria
1.  The script SHALL use robust selectors (e.g., ARIA roles, data-test-ids) to interact with LinkedIn's website.
2.  The script SHALL use explicit waits to ensure elements are fully loaded before interacting with them.
3.  IF a post fails, THEN the agent SHALL log the error in detail (including a screenshot) and send a failure notification to the user on Telegram.

---

### Epic 2: Agent Orchestration and Intelligence

**Goal:** To re-architect the agent using modern, AI-native frameworks. This will make the agent more powerful, intelligent, and easier to extend in the future.

---

**User_Story: 2.1**
As a developer, I want the agent to be built on a formal orchestration framework (CrewAI), so that its workflow is more robust, scalable, and easier to maintain.
*Status: To Do*
*Priority: Medium*

#### Acceptance Criteria
1.  The agent's workflow SHALL be re-implemented using CrewAI.
2.  There SHALL be separate "Crews" or "Agents" for fetching, summarizing, and posting.
3.  The linear script in `main.py` SHALL be replaced by a CrewAI orchestration script.

---

**User_Story: 2.2**
As the agent operator, I want the agent to use an advanced, AI-powered web scraping library (Crawl4AI), so that it can reliably extract clean, relevant content from articles.
*Status: To Do*
*Priority: Medium*

#### Acceptance Criteria
1.  The current scraping logic (Requests + BeautifulSoup) SHALL be replaced with Crawl4AI.
2.  The agent SHALL use Crawl4AI to fetch and extract the main content of an article into clean Markdown.
3.  The extracted Markdown SHALL be used as the input for the summarization step.

---

### Epic 3: Feature Enhancements and Automation

**Goal:** To add new features that improve the user experience and make the agent a truly autonomous, "set-it-and-forget-it" tool.

---

**User_Story: 3.1**
As the agent operator, I want the agent to run automatically on a schedule, so that I don't have to manually execute it every day.
*Status: To Do*
*Priority: Low*

#### Acceptance Criteria
1.  The agent SHALL include a built-in scheduler that can be configured via the `.env` file.
2.  The agent SHALL run its main processing loop automatically based on the defined schedule.
3.  To appear more human, the agent SHALL add a small, random delay to its posting time.

---

**User_Story: 3.2**
As the agent operator, I want the ability to edit the AI-generated summary before it's posted to LinkedIn, so that I have full control over the final content.
*Status: To Do*
*Priority: Low*

#### Acceptance Criteria
1.  The approval message on Telegram SHALL include an "Edit" button.
2.  WHEN the user clicks "Edit", THEN the bot SHALL prompt the user to send the new summary.
3.  The agent SHALL wait for the user's new summary and then use it for the LinkedIn post.

---

### Epic 4: Comprehensive Documentation

**Goal:** To create and update project documentation to ensure the agent is easy to understand, maintain, and extend for any developer.

---

**User_Story: 4.1**
As a developer, I want comprehensive and up-to-date project documentation, so that I can quickly understand the project's architecture, workflow, and setup process.
*Status: To Do*
*Priority: Low*

#### Acceptance Criteria
1.  A `Product_Architecture.md` file SHALL be created in the project root.
2.  This file SHALL contain a detailed description of the agent's architecture, including the roles of each component (Fetcher, Summarizer, Poster, etc.).
3.  This file SHALL include a Mermaid process flow diagram illustrating the end-to-end workflow of the agent.
4.  The main `README.md` file SHALL be updated to reflect all the new features and architectural changes from all epics.

---

## Section 2: Sequential Task List

### Epic 1: Core Stability and Reliability
**Priority: High**
- [x] **1. Upgrade Dependencies**
  - [x] **Web Search:** Identify the latest stable versions of all libraries in `requirements.txt`.
  - [x] Update `requirements.txt` with the new versions.
  - [x] **Web Search:** Research breaking changes for the new library versions.
  - [x] Refactor the code to be compatible with the new versions, especially replacing `google-generativeai` with `google-genai`.
  - _User_Story: 1.3_
- [x] **2. Implement Persistent Storage**
  - [x] Add `db-sqlite3` to the project for database interaction.
  - [x] Create a `database.py` module to handle database initialization and connection.
  - [x] Implement a function to store a processed article URL and a function to check if a URL exists.
  - [x] Integrate the database check into the main processing loop in `main.py`.
  - _User_Story: 1.1_
- [x] **3. Fix Asynchronous Execution**
  - [x] **Web Search:** Research best practices for `asyncio` with the `python-telegram-bot` library.
  - [x] Re-architect the application to run within a single, top-level `asyncio` event loop, starting in `main.py`.
  - [x] Remove the `nest_asyncio` library and all synchronous wrappers (e.g., `run_until_complete`).
  - _User_Story: 1.2_
- [x] **4. Improve Scraper and Poster Reliability**
  - [x] **Web Search:** Inspect the current HTML structure of Hacker News and TechCrunch to find new, stable selectors.
  - [x] Update the selectors in `article_fetcher.py`.
  - [x] **Web Search:** Research best practices for robust Selenium automation on dynamic websites like LinkedIn.
  - [x] Re-implement the `linkedin_poster.py` script with robust selectors (ARIA roles, data-attributes), explicit waits, and intelligent retry logic.
  - [x] Add enhanced error handling (screenshots, Telegram notifications) to the LinkedIn poster.
  - _User_Story: 1.4, 1.5_

### Epic 2: Agent Orchestration and Intelligence
**Priority: Medium**
- [x] **5. Implement Advanced Web Scraping**
  - [x] **Web Search:** Review the documentation for `Crawl4AI` to understand its API and features.
  - [x] Replace the `get_article_content` function in `article_fetcher.py` with an implementation that uses `Crawl4AI`.
  - _User_Story: 2.2_
- [x] **6. Migrate to CrewAI**
  - [x] **Web Search:** Complete tutorials and review documentation for `CrewAI`.
  - [x] Design the agent's new architecture using CrewAI, defining roles and tasks for a Fetcher, Summarizer, and Poster.
  - [x] Re-implement the application logic, replacing the `main.py` script with a new `crew.py` for orchestration.
  - _User_Story: 2.1_

### Epic 3: Feature Enhancements and Automation
**Priority: Low**
- [x] **7. Add Scheduling and Editing Features**
  - [x] Integrate the `schedule` library into the main script to run the agent automatically based on a `.env` variable.
  - _User_Story: 3.1_
  - [x] Modify the `telegram_bot.py` to add an "Edit" button to the approval message.
  - [x] Implement the conversation flow to receive and use the user's edited summary.
  - _User_Story: 3.2_

### Epic 4: Comprehensive Documentation
**Priority: Low**
- [x] **8. Create Project Documentation**
  - [x] Create the `Product_Architecture.md` file.
  - [x] Write a detailed description of the agent's architecture and components.
  - [x] Design and embed a Mermaid process flow diagram in `Product_Architecture.md`.
  - [x] Update the main `README.md` to reflect all the new features and architectural changes.
  - _User_Story: 4.1_
