import requests
import praw
import asyncpraw
from bs4 import BeautifulSoup
import logging
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from config import Config # Assuming config.py is in the parent directory or PYTHONPATH
import asyncio
import nest_asyncio

logger = logging.getLogger(__name__)

@dataclass
class Article:
    title: str
    url: str
    source: str
    summary: Optional[str] = None
    # content: Optional[str] = None # Full content, if fetched and needed

class ArticleFetcher:
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[requests.Response]:
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=self.config.request_timeout)
                response.raise_for_status()  # Raise HTTPError for bad responses (4XX or 5XX)
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request to {url} failed (attempt {attempt + 1}/{self.config.max_retries}): {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
                else:
                    logger.error(f"Failed to fetch {url} after {self.config.max_retries} retries.")
                    return None
        return None # Should be unreachable if loop completes

    async def fetch_hackernews_articles(self) -> List[Article]:
        if not self.config.enable_hackernews:
            return []

        logger.info("Fetching articles from Hacker News...")
        hn_api_url = "https://hn.algolia.com/api/v1/search_by_date"
        params = {
            "query": "AI OR artificial intelligence OR machine learning OR LLM", # Broad query for AI topics
            "tags": "story",
            "hitsPerPage": self.config.hackernews_max_articles + 20 # Fetch more to filter for quality if needed
        }

        response = self._make_request(hn_api_url, params=params)
        if not response:
            return []

        articles: List[Article] = []
        try:
            data = response.json()
            for hit in data.get("hits", []):
                title = hit.get("title")
                url = hit.get("url")
                # Hacker News often has 'story_text' or 'comment_text' which are not external articles
                # Also, filter out job postings or Ask HN/Show HN if not desired
                if title and url and "http" in url and not hit.get("story_text") and not hit.get("comment_text"):
                    # Basic keyword filtering for relevance
                    title_lower = title.lower()
                    if any(keyword in title_lower for keyword in ["ai", "artificial intelligence", "machine learning", "llm", "deep learning", "neural network"]):
                        articles.append(Article(title=title, url=url, source="Hacker News"))
                        if len(articles) >= self.config.hackernews_max_articles:
                            break
            logger.info(f"Fetched {len(articles)} articles from Hacker News.")
        except Exception as e:
            logger.error(f"Error parsing Hacker News response: {e}")
        return articles[:self.config.hackernews_max_articles]

    def fetch_reddit_articles_sync(self) -> List[Article]:
        nest_asyncio.apply()
        return asyncio.run(self.fetch_reddit_ai_articles())

    async def fetch_reddit_ai_articles(self) -> List[Article]:
        nest_asyncio.apply()
        return asyncio.run(self.fetch_reddit_ai_articles())

    async def fetch_reddit_ai_articles(self) -> List[Article]:
        if not self.config.enable_reddit_ai:
            return []
        if not self.config.reddit_client_id or not self.config.reddit_client_secret:
            logger.warning("Reddit API credentials not configured. Skipping Reddit.")
            return []

        logger.info("Fetching articles from Reddit r/artificialintelligence using Async PRAW...")

        try:
            reddit = asyncpraw.Reddit(
                client_id=self.config.reddit_client_id,
                client_secret=self.config.reddit_client_secret,
                user_agent=self.config.reddit_user_agent,
            )

            subreddit = await reddit.subreddit("MachineLearning")
            articles: List[Article] = []

            async for submission in subreddit.new(limit=self.config.reddit_ai_max_articles + 50): # Fetch more to filter
                # Filter out self-posts, stickied posts, and non-external links
                if not submission.is_self and not submission.stickied and "reddit.com" not in submission.url:
                    # Further filter by keywords in title or selftext (if it's a text post)
                    title_lower = submission.title.lower()
                    if any(keyword in title_lower for keyword in ["ai", "artificial intelligence", "machine learning", "llm", "deep learning", "neural network"]):
                        # Filter out common irrelevant post types
                        if not any(substring in title_lower for substring in ["ama", "ask me anything", "discussion", "weekly thread", "showoff", "meme"]):
                            articles.append(Article(title=submission.title, url=submission.url, source="Reddit r/artificialintelligence"))
                            if len(articles) >= self.config.reddit_ai_max_articles:
                                break
            logger.info(f"Fetched {len(articles)} articles from Reddit API.")
            await reddit.close()
            return articles[:self.config.reddit_ai_max_articles]

        except Exception as e:
            logger.error(f"Error fetching from Reddit using Async PRAW: {e}")
            return []

    def _scrape_reddit_ai_articles(self) -> List[Article]:
        logger.info("Attempting to scrape articles from Reddit r/artificialintelligence (fallback)...")
        url = "https://old.reddit.com/r/artificialintelligence/top/?t=day" # old.reddit is often easier to scrape

        response = self._make_request(url)
        if not response:
            return []

        articles: List[Article] = []
        try:
            soup = BeautifulSoup(response.content, "html.parser")
            # Find entry elements. This selector might need adjustment if Reddit changes layout.
            entries = soup.find_all("div", class_="entry", limit=self.config.reddit_ai_max_articles + 5)
            for entry in entries:
                title_tag = entry.find("p", class_="title")
                if title_tag:
                    link_tag = title_tag.find("a", class_="title")
                    if link_tag:
                        title = link_tag.text
                        url = link_tag["href"]
                        # If it's a relative URL, prepend reddit domain (though for external links it should be absolute)
                        if url.startswith("/r/"):
                            # This is a link to another reddit post, not an external article usually.
                            # We want external articles primarily.
                            # Check if it's a crosspost that has a clear external link data attribute
                            if 'data-event-action' in link_tag.attrs and link_tag.attrs.get('data-event-action') == 'title':
                                url = link_tag.attrs.get('href') # this should be the intended external link
                            else:
                                continue # Skip internal links or ones we can't resolve to external

                        if not url.startswith("http"): # if somehow it's still relative
                             logger.warning(f"Skipping relative or unclear URL from Reddit scrape: {url}")
                             continue

                        # Filter out self-posts or links to reddit itself
                        if "reddit.com" in url:
                            continue
                        if not any(substring in title.lower() for substring in ["ama", "ask me anything", "discussion", "weekly thread"]):
                            articles.append(Article(title=title, url=url, source="Reddit r/artificialintelligence (Scraped)"))
                        if len(articles) >= self.config.reddit_ai_max_articles:
                            break
            logger.info(f"Scraped {len(articles)} articles from Reddit.")
        except Exception as e:
            logger.error(f"Error scraping Reddit: {e}")
        return articles[:self.config.reddit_ai_max_articles]


    async def fetch_techcrunch_ai_articles(self) -> List[Article]:
        if not self.config.enable_techcrunch_ai:
            return []

        logger.info(f"Fetching articles from TechCrunch AI ({self.config.techcrunch_ai_url})...")
        response = self._make_request(self.config.techcrunch_ai_url)
        if not response:
            return []

        articles: List[Article] = []
        try:
            soup = BeautifulSoup(response.content, "html.parser")
            # TechCrunch structure: articles are often in <article> tags or specific divs
            # This selector is highly dependent on TechCrunch's current HTML structure.
            # It's crucial to inspect TechCrunch's AI section HTML structure if this breaks.
            # Common patterns involve looking for article titles within header tags (h2, h3) inside article containers.
            # The class 'post-block' and similar are often used for article entries.

            # Primary strategy: Look for common article container classes and then find title links within them.
            # Selectors are ordered by assumed likelihood or specificity.
            potential_article_selectors = [
                "a.post-card__title-link", # Common for newer TechCrunch layouts
                "h2.post-block__title a", # Older TechCrunch layout
                "div.river-block h2 a", # Another common pattern on news sites
                "li.river-item h2 a", # If articles are in a list
                "article header h2 a", # General article structure
                "div[class*='content-list'] div[class*='item'] a[href*='/20']" # Generic list item with a link that looks like an article
            ]

            found_urls = set()

            for selector in potential_article_selectors:
                if len(articles) >= self.config.techcrunch_max_articles:
                    break

                elements = soup.select(selector)
                for link_tag in elements:
                    title = link_tag.text.strip()
                    url = link_tag.get('href')

                    if not url: continue
                    if not url.startswith("http"): # Ensure absolute URL
                        if url.startswith("/"): 
                            url = f"https://techcrunch.com{url}"
                        else:
                            logger.warning(f"Skipping potentially malformed TechCrunch URL: {url}")
                            continue

                    if title and url and url not in found_urls:
                        # Basic check to ensure it's likely an article and not a category link etc.
                        # TechCrunch URLs often contain year/month/day.
                        if "/20" in url and len(title) > 15: # Heuristic: year in URL, title has some length
                            articles.append(Article(title=title, url=url, source="TechCrunch AI"))
                            found_urls.add(url)
                            if len(articles) >= self.config.techcrunch_max_articles:
                                break

            if not articles: # A fallback if the above doesn't work well
                logger.warning("Primary TechCrunch scraping selectors found no articles, trying broader fallback.")
                # Fallback: Look for any link within an <article> tag that seems plausible.
                # This is very broad and might pick up non-article links.
                article_tags = soup.find_all('article')
                for article_tag in article_tags:
                    link_tag = article_tag.find("a", href=True)
                    if link_tag and link_tag['href'].startswith("http"):
                        title = link_tag.text.strip()
                        url = link_tag['href']
                        if title and url and url not in found_urls and "/20" in url and len(title) > 15:
                            articles.append(Article(title=title, url=url, source="TechCrunch AI (Fallback)"))
                            found_urls.add(url)
                            if len(articles) >= self.config.techcrunch_max_articles:
                                break

            logger.info(f"Fetched {len(articles)} articles from TechCrunch AI.")
        except Exception as e:
            logger.error(f"Error scraping TechCrunch AI: {e}")
        return articles[:self.config.techcrunch_max_articles]

    async def fetch_arxiv_articles(self) -> List[Article]:
        if not self.config.enable_arxiv:
            return []

        logger.info("Fetching articles from ArXiv...")
        # ArXiv API base URL for search queries
        arxiv_api_url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": self.config.arxiv_search_query,
            "sortBy": "submittedDate", # Get the latest articles
            "sortOrder": "descending",
            "max_results": self.config.arxiv_max_articles + 5 # Fetch a bit more to allow filtering
        }

        response = self._make_request(arxiv_api_url, params=params)
        if not response:
            return []

        articles: List[Article] = []
        try:
            # ArXiv API returns XML
            soup = BeautifulSoup(response.content, "xml") # Use 'xml' parser
            entries = soup.find_all("entry")

            for entry in entries:
                title_tag = entry.find("title")
                # ArXiv links can be to PDF or abstract, prefer abstract page (HTML link)
                link_tag = entry.find("link", rel="alternate", type="text/html")
                if not link_tag: # Fallback to PDF if no HTML link found
                    link_tag = entry.find("link", title="pdf")

                if title_tag and link_tag and link_tag.get('href'):
                    title = title_tag.text.strip().replace('\n', ' ').replace('  ', ' ')
                    url = link_tag['href']
                    # Add a check to ensure the article is somewhat recent if sortBy doesn't guarantee it for all queries
                    # For example, check updated_date or published_date from entry if needed.
                    # published_date_tag = entry.find("published")
                    # if published_date_tag and "2023" not in published_date_tag.text and "2024" not in published_date_tag.text: # Example filter
                    #    logger.debug(f"Skipping older ArXiv article: {title} published {published_date_tag.text}")
                    #    continue
                    articles.append(Article(title=title, url=url, source="ArXiv"))
                    if len(articles) >= self.config.arxiv_max_articles:
                        break
            logger.info(f"Fetched {len(articles)} articles from ArXiv.")
        except Exception as e:
            logger.error(f"Error parsing ArXiv API response: {e}")
        return articles[:self.config.arxiv_max_articles]


    async def fetch_all_articles(self) -> List[Article]:
        all_articles: List[Article] = []

        # Deduplication based on URL
        seen_urls = set()

        def add_articles_if_new(new_articles: List[Article]):
            for article in new_articles:
                if article.url not in seen_urls:
                    all_articles.append(article)
                    seen_urls.add(article.url)
                else:
                    logger.debug(f"Duplicate article skipped: {article.title} ({article.url})")

        if self.config.enable_hackernews:
            add_articles_if_new(await self.fetch_hackernews_articles())
        if self.config.enable_reddit_ai:
            add_articles_if_new(self.fetch_reddit_articles_sync())
        if self.config.enable_techcrunch_ai:
            add_articles_if_new(await self.fetch_techcrunch_ai_articles())
        if self.config.enable_arxiv:
            add_articles_if_new(await self.fetch_arxiv_articles())

        logger.info(f"Total unique articles fetched: {len(all_articles)}")
        return all_articles

    def get_article_content(self, url: str) -> Optional[str]:
        """
        Fetches the main textual content of an article from its URL.
        This is a basic implementation and might need a more sophisticated
        library like 'newspaper3k' for better results across various sites.
        Uses heuristics to find the main content body.
        """
        logger.info(f"Fetching content for article: {url}")
        response = self._make_request(url)
        if not response:
            return None

        # Check content type. If not HTML, return None.
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            logger.warning(f"Skipping non-HTML content for {url}. Content-Type: {content_type}")
            return None

        try:
            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script, style, nav, header, footer, aside elements as they usually don't contain main content
            for unwanted_tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "button", "iframe"]):
                unwanted_tag.decompose()

            # Try to find common article body tags/classes
            # This is highly heuristic and will not work for all sites.
            # Order matters: more specific selectors first.
            possible_body_selectors = [
                "article[class*='body']", "div[class*='article-body']", "div[class*='story-content']", # Specific classes
                "article", "main", "div[role='main']", # Semantic tags
                "div[class*='post-content']", "div[class*='entry-content']", "div[class*='content']", # Common class names
                "section[class*='article']"
            ]

            text_parts = []
            content_found = False
            selected_content_container = None

            for selector in possible_body_selectors:
                body_container = soup.select_one(selector)
                if body_container:
                    # Check if this container has significant text, not just links or tiny bits
                    container_text_check = body_container.get_text(separator=" ", strip=True)
                    if len(container_text_check) > 200: # Arbitrary threshold for significant text
                        selected_content_container = body_container
                        content_found = True
                        logger.debug(f"Selected content container for {url} using selector: '{selector}'")
                        break

            if selected_content_container:
                # Extract text primarily from <p> tags within the selected container
                paragraphs = selected_content_container.find_all('p')
                if paragraphs:
                    for p in paragraphs:
                        text = p.get_text(separator=" ", strip=True)
                        # Filter out short paragraphs that might be captions, ads, or social media links
                        if text and len(text.split()) > 7 and not any(kw in text.lower() for kw in ["follow us", "subscribe", "related:", "also read", "©", "rights reserved"]):
                             text_parts.append(text)
                else: # If no <p> tags, try to get all text from the container, but be wary of noise
                    logger.debug(f"No <p> tags in selected container for {url}, using broader text extraction.")
                    all_text_in_container = selected_content_container.get_text(separator="\n", strip=True)
                    # Split by lines and filter
                    for line in all_text_in_container.splitlines():
                        stripped_line = line.strip()
                        if stripped_line and len(stripped_line.split()) > 7 and not any(kw in stripped_line.lower() for kw in ["follow us", "subscribe", "related:", "also read", "©", "rights reserved"]):
                            text_parts.append(stripped_line)

            if not content_found or not text_parts:
                logger.warning(f"Could not find specific article body for {url} with selectors. Falling back to generic text extraction from body.")
                body = soup.find("body")
                if body:
                    # Get text from all <p> tags in the body as a last resort
                    all_paragraphs = body.find_all("p")
                    if all_paragraphs:
                        for p in all_paragraphs:
                            text = p.get_text(separator=" ", strip=True)
                            if text and len(text.split()) > 10 and not any(kw in text.lower() for kw in ["follow us", "subscribe", "related:", "also read", "©", "rights reserved"]):
                                text_parts.append(text)
                    else: # If still no p tags, just grab all text from body, this will be noisy
                         logger.debug(f"No <p> tags found in body for {url} during fallback. Grabbing all body text.")
                         body_text = body.get_text(separator="\n", strip=True)
                         for line in body_text.splitlines():
                            stripped_line = line.strip()
                            if stripped_line and len(stripped_line.split()) > 10 and not any(kw in stripped_line.lower() for kw in ["follow us", "subscribe", "related:", "also read", "©", "rights reserved"]):
                                text_parts.append(stripped_line)


            if not text_parts:
                logger.warning(f"No significant text content found for {url} after trying all methods.")
                return None

            full_text = "\n\n".join(text_parts) # Join paragraphs with double newlines for readability
            # Basic cleaning: reduce multiple newlines/spaces that might have been introduced
            full_text = "\n".join([line.strip() for line in full_text.splitlines() if line.strip()])
            full_text = full_text.replace('  ', ' ') # Replace double spaces with single

            # Limit content length to avoid oversized LLM prompts (e.g. first 1500 words)
            # This should be based on tokens for LLMs, but word count is a simpler proxy.
            max_words_for_summary = 1500
            words = full_text.split()
            if len(words) > max_words_for_summary:
                full_text = " ".join(words[:max_words_for_summary]) + "..."
                logger.info(f"Truncated article content for {url} to approximately {max_words_for_summary} words for LLM processing.")

            return full_text
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}", exc_info=True)
            return None


if __name__ == "__main__":
    # This is for testing the ArticleFetcher locally
    # You'll need a .env file with necessary configurations

    # Setup basic logging for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create a dummy config for testing. In a real scenario, load_config() from config.py would be used.
    class TestConfig(Config):
        def __init__(self):
            super().__init__() # Load from .env
            # Override specific settings for testing if needed, or ensure .env is set up
            self.enable_hackernews = True
            self.hackernews_max_articles = 2
            self.enable_reddit_ai = True # Requires REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env
            self.reddit_ai_max_articles = 1 # Reduced for faster testing
            self.enable_techcrunch_ai = True
            self.techcrunch_ai_url="https://techcrunch.com/category/artificial-intelligence/" # ensure this is correct
            self.techcrunch_max_articles = 1 # Reduced for faster testing
            self.enable_arxiv = True # ArXiv is generally public
            self.arxiv_max_articles = 1 # Reduced for faster testing
            self.request_timeout = 20 # Increased timeout for potentially slow sites
            self.max_retries = 1 # Reduce retries for faster testing
            self.retry_delay = 2
            if not self.validate(): # Validate after overrides
                 logger.error("TestConfig is not valid. Check .env or overrides.")
                 # raise Exception("TestConfig is not valid. Check .env or overrides.")


    try:
        test_config = TestConfig()
        if not test_config.validate(): # Check validation again here before proceeding
            logger.error("TestConfig failed validation. Aborting ArticleFetcher test.")
            exit()

        fetcher = ArticleFetcher(test_config)

        print("\n--- Testing Hacker News ---")
        hn_articles = fetcher.fetch_hackernews_articles()
        for article in hn_articles:
            print(f"  Title: {article.title}, URL: {article.url}, Source: {article.source}")

        print("\n--- Testing Reddit r/artificialintelligence ---")
        # Ensure your .env has REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET for API access
        # If not, it will attempt to scrape (which is less reliable)
        reddit_articles = fetcher.fetch_reddit_ai_articles()
        for article in reddit_articles:
            print(f"  Title: {article.title}, URL: {article.url}, Source: {article.source}")

        print("\n--- Testing TechCrunch AI ---")
        tc_articles = fetcher.fetch_techcrunch_ai_articles()
        for article in tc_articles:
            print(f"  Title: {article.title}, URL: {article.url}, Source: {article.source}")

        print("\n--- Testing ArXiv ---")
        arxiv_articles = fetcher.fetch_arxiv_articles()
        for article in arxiv_articles:
            print(f"  Title: {article.title}, URL: {article.url}, Source: {article.source}")

        print("\n--- Testing Fetch All (Combined & Deduplicated) ---")
        all_articles = fetcher.fetch_all_articles()
        for i, article in enumerate(all_articles):
            print(f"  {i+1}. Title: {article.title}\n     URL: {article.url}\n     Source: {article.source}")
            if i < 2 : # Test content fetching for first 2 articles (or fewer if less than 2 fetched)
                print(f"     Fetching content for: {article.url}")
                content = fetcher.get_article_content(article.url)
                if content:
                    print(f"     Content snippet (first 300 chars): {content[:300]}...")
                    print(f"     Content total length: {len(content)} chars")
                else:
                    print("     Could not fetch content.")
            print("-" * 20)

        if not all_articles:
            print("\nNo articles fetched in 'Fetch All'. Ensure sources are enabled and working.")


    except Exception as e:
        logger.error(f"Error during ArticleFetcher test: {e}", exc_info=True)

"""
Note on Reddit API vs Scraping:
- Using the Reddit API (with client ID and secret) is more reliable and respectful of Reddit's platform.
- Scraping (the fallback `_scrape_reddit_ai_articles`) can break if Reddit changes its HTML structure.
- To use the API:
    1. Go to https://www.reddit.com/prefs/apps
    2. Create a new app (select "script" type).
    3. Set a redirect URI (e.g., http://localhost:8080 - it won't actually be used for this script type).
    4. Note the client ID (under your app name) and client secret.
    5. Add these to your .env file as REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.

Note on Web Scraping (TechCrunch, Reddit scrape fallback, article content):
- Web scraping is inherently fragile. Website HTML structures change without notice, which will break scraper logic.
- Selectors (CSS selectors, XPaths) need to be chosen carefully and may require regular updates.
- For `get_article_content`, the quality of extracted text can vary wildly. Libraries like `newspaper3k` or `trafilatura`
  are more advanced for this task but add extra dependencies. The current implementation is a heuristic-based approach.
- Always respect `robots.txt` (though this script currently doesn't automatically check it).
- Be mindful of request frequency to avoid overloading servers or getting IP banned.
"""