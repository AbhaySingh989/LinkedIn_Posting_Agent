import google.generativeai as genai
import logging
import time
from typing import Optional
from config import Config # Assuming config.py is in the parent directory or PYTHONPATH
from src.article_fetcher import ArticleFetcher # For fetching article content

logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        if not api_key:
            raise ValueError("Gemini API Key is required.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.config = Config() # Load general config for retry logic, prompts
        # The ArticleFetcher is needed to get content if not already provided
        # This creates a dependency. Consider if it should be passed in or if LLMHandler
        # should only work with text. For this project, fetching content here is okay.
        self._article_fetcher = ArticleFetcher(self.config)


    def _get_article_text_content(self, article_url: str) -> Optional[str]:
        """Helper to fetch article content using ArticleFetcher."""
        try:
            content = self._article_fetcher.get_article_content(article_url)
            return content
        except Exception as e:
            logger.error(f"Error fetching article content for summarization from {article_url}: {e}")
            return None

    def summarize_article(self, article_url_or_content: str, is_url: bool = True) -> Optional[str]:
        """
        Generates a summary for the given article URL or direct text content.

        Args:
            article_url_or_content: The URL of the article or its full text content.
            is_url: True if article_url_or_content is a URL, False if it's text content.

        Returns:
            A string containing the summary, or None if summarization fails.
        """
        article_text: Optional[str]
        if is_url:
            logger.info(f"Fetching article content from URL for summarization: {article_url_or_content}")
            article_text = self._get_article_text_content(article_url_or_content)
            if not article_text:
                logger.error(f"Could not retrieve content from URL: {article_url_or_content}")
                return None
        else:
            article_text = article_url_or_content
            logger.info(f"Summarizing provided text content (first 100 chars): {article_text[:100]}...")


        prompt = f"{self.config.summarization_prompt}\n\n---\n\n{article_text}"

        # Truncate prompt if too long (Gemini has token limits)
        # This is a very rough estimate. Proper token counting is better.
        # Max input tokens for gemini-pro is often around 30720 for text.
        # A character is roughly 0.25 tokens on average.
        # Max chars ~ 30720 * 4 = 122880. Let's be safer.
        max_prompt_chars = 100000
        if len(prompt) > max_prompt_chars:
            logger.warning(f"Prompt length ({len(prompt)} chars) exceeds max ({max_prompt_chars}). Truncating.")
            prompt = prompt[:max_prompt_chars]


        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Sending prompt to Gemini (attempt {attempt + 1}/{self.config.max_retries}). Length: {len(prompt)} chars.")
                # Safety settings can be adjusted if needed
                # Example:
                # safety_settings = [
                #     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                #     {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                #     {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                #     {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                # ]
                # response = self.model.generate_content(prompt, safety_settings=safety_settings)

                response = self.model.generate_content(prompt)

                if response.parts:
                    summary = "".join(part.text for part in response.parts if hasattr(part, 'text'))
                    if summary:
                        logger.info(f"Summary generated successfully for {'URL' if is_url else 'content'}.")
                        #logger.debug(f"Generated summary: {summary}")
                        return summary.strip()
                    else:
                        logger.warning("Gemini response contained no text parts.")

                if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                    logger.error(f"Content generation blocked by Gemini. Reason: {response.prompt_feedback.block_reason}")
                    if response.prompt_feedback.block_reason_message:
                         logger.error(f"Block reason message: {response.prompt_feedback.block_reason_message}")
                    return None # Blocked content is a definitive failure for this attempt.

                logger.warning(f"Gemini response did not contain expected parts or was empty. Response: {response}")

            except Exception as e:
                logger.error(f"Error during Gemini API call (attempt {attempt + 1}/{self.config.max_retries}): {e}")
                # Specific error handling for common issues like API key, quota, etc. can be added here.
                # For example, if e is an APIError related to auth, no point retrying.
                if "API_KEY_INVALID" in str(e) or "permission" in str(e).lower():
                    logger.error("Invalid API key or permission issue. Please check your GEMINI_API_KEY.")
                    return None # Don't retry on auth errors

            if attempt < self.config.max_retries - 1:
                logger.info(f"Retrying in {self.config.retry_delay} seconds...")
                time.sleep(self.config.retry_delay)
            else:
                logger.error(f"Failed to generate summary after {self.config.max_retries} retries.")
                return None

        return None # Should be unreachable

if __name__ == "__main__":
    # This is for testing the LLMHandler locally
    # You'll need a .env file with GEMINI_API_KEY

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Load configuration (ensure .env file has GEMINI_API_KEY)
    from config import load_config
    test_config = load_config()

    if not test_config or not test_config.gemini_api_key:
        logger.error("GEMINI_API_KEY is not configured in .env file. Exiting test.")
    else:
        logger.info(f"Test configured for Gemini API Key: ...{test_config.gemini_api_key[-5:]}")
        llm_handler = LLMHandler(api_key=test_config.gemini_api_key, model_name=test_config.llm_model_name)

        # --- Test 1: Summarize from a URL ---
        # Using a well-known, stable article for testing is good.
        # For a real test, ensure the URL is accessible and has clear article text.
        # For this example, we'll use a placeholder URL and if it fails, use direct text.
        # test_article_url = "https://techcrunch.com/2023/10/26/ais-next-frontier-explainability-and-trust/" # Example
        test_article_url = "https://example.com/nonexistent-article-for-testing" # This will fail content fetch

        print(f"\n--- Test 1: Summarizing article from URL: {test_article_url} ---")
        summary_from_url = llm_handler.summarize_article(test_article_url, is_url=True)

        if summary_from_url:
            print(f"Summary from URL:\n{summary_from_url}")
        else:
            print("Could not generate summary from URL (this might be expected if the URL is a dummy or content extraction fails).")

        # --- Test 2: Summarize from direct text content ---
        print("\n--- Test 2: Summarizing direct text content ---")
        sample_text_content = (
            "Artificial Intelligence (AI) is rapidly transforming industries worldwide. From healthcare to finance, "
            "AI algorithms are optimizing processes, enabling new capabilities, and driving innovation. "
            "Machine learning, a subset of AI, allows systems to learn from data and improve over time without explicit programming. "
            "Deep learning, with its neural network architectures, has achieved remarkable success in areas like image recognition and natural language processing. "
            "However, the development and deployment of AI also raise ethical considerations, including bias, transparency, and accountability, which need careful attention."
            "The future of AI promises even more advanced applications, potentially leading to artificial general intelligence (AGI)."
        )
        summary_from_text = llm_handler.summarize_article(sample_text_content, is_url=False)

        if summary_from_text:
            print(f"Summary from text:\n{summary_from_text}")
        else:
            print("Could not generate summary from text.")

        # --- Test 3: Summarize a longer text that might require fetching and truncation awareness ---
        # For this, we'd ideally use a real URL that ArticleFetcher can process.
        # Let's try a known public blog post about AI if ArticleFetcher is robust.
        # If you have a specific URL you want to test with ArticleFetcher, put it here.
        # For now, we'll simulate a longer text.
        print("\n--- Test 3: Summarizing a longer piece of text (simulated) ---")
        long_text = sample_text_content * 5 # Make it longer
        long_text += (
            " As AI systems become more integrated into society, ensuring their reliability and fairness is paramount. "
            "Researchers are exploring techniques for explainable AI (XAI) to make the decision-making processes of complex models more understandable to humans. "
            "This is crucial for building trust and for debugging models when they make errors. "
            "The regulatory landscape for AI is also evolving, with governments worldwide considering frameworks to govern AI development and use. "
            "International collaboration will be key to establishing common standards and best practices. "
            "The economic impact of AI is projected to be substantial, with both job creation in new roles and displacement in others. "
            "Preparing the workforce for these changes through education and retraining programs is a significant challenge."
        )

        summary_from_long_text = llm_handler.summarize_article(long_text, is_url=False)
        if summary_from_long_text:
            print(f"Summary from long text:\n{summary_from_long_text}")
        else:
            print("Could not generate summary from long text.")

        # --- Test 4: Test with a real, accessible URL (if ArticleFetcher is working) ---
        # Find a stable AI news article URL to test this properly
        real_article_url = "https://www.technologyreview.com/2024/01/08/1086010/ai-is-entering-its-jello-salad-era/" # Example
        # Note: Content extraction can be flaky. If this URL doesn't work, try another or skip.
        # Ensure the domain is not blocked by robots.txt for your User-Agent if ArticleFetcher respects it.

        print(f"\n--- Test 4: Summarizing article from a REAL URL: {real_article_url} ---")
        print("(This test depends on successful content extraction by ArticleFetcher)")
        summary_from_real_url = llm_handler.summarize_article(real_article_url, is_url=True)

        if summary_from_real_url:
            print(f"Summary from REAL URL ({real_article_url}):\n{summary_from_real_url}")
        else:
            print(f"Could not generate summary from REAL URL ({real_article_url}). This could be due to content extraction issues or the LLM call itself.")

        print("\nLLM Handler tests finished.")
"""
Note on Gemini API:
- Ensure your `GEMINI_API_KEY` environment variable is correctly set and has access to the specified model (e.g., "gemini-1.5-flash").
- The `google-generativeai` library handles the API calls.
- Content summarization quality depends on the model, the prompt, and the quality/clarity of the source article text.
- The `summarization_prompt` in `config.py` can be tuned for better results.
- Error handling for API rate limits, quota issues, or content safety blocks from Gemini is important for robustness.
  The current code has basic retry logic and checks for `prompt_feedback.block_reason`.
- For very long articles, effective truncation or chunking of the input text might be necessary if it exceeds the model's context window.
  The current `get_article_content` in `ArticleFetcher` has a basic truncation mechanism.
"""
