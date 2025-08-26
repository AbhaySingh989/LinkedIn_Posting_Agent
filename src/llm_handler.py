import logging
import asyncio
import os
import litellm

logger = logging.getLogger(__name__)

class LlmHandler:
    """
    Handles interaction with LLMs via the litellm library.
    """
    def __init__(self, api_key: str):
        """
        Initializes the LlmHandler.

        Args:
            api_key (str): The Google Gemini API key.
        """
        if not api_key:
            raise ValueError("Google Gemini API key is required.")

        # litellm expects the API key to be in an environment variable.
        os.environ["GEMINI_API_KEY"] = api_key

        self.model = 'gemini/gemini-pro'
        logger.info(f"LlmHandler initialized to use {self.model} via litellm.")

    async def summarize_content_async(self, content: str, prompt: str = None) -> str:
        """
        Summarizes the given text content using the specified model asynchronously.

        Args:
            content (str): The text content to summarize.
            prompt (str): An optional custom prompt.

        Returns:
            str: The summarized text, or an empty string if an error occurs.
        """
        if not prompt:
            prompt = (
                "Please summarize the following article content for a LinkedIn post. "
                "The summary should be concise, engaging, and professional. "
                "Include a captivating hook, 2-3 key takeaways as bullet points, and a concluding sentence to spark conversation. "
                "Do not include the original URL or any hashtags in your output."
            )

        messages = [
            {"role": "user", "content": f"{prompt}\n\n---\n\n{content}"}
        ]

        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=messages
            )
            # Check if choices list is not empty and has a message
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content or ""
            else:
                logger.warning("Received an empty response from litellm.")
                return ""
        except Exception as e:
            logger.error(f"Error summarizing content with litellm: {e}", exc_info=True)
            return ""

    def summarize_content_sync(self, content: str, prompt: str = None) -> str:
        """
        Synchronous wrapper for summarize_content_async.

        Args:
            content (str): The text content to summarize.
            prompt (str): An optional custom prompt.

        Returns:
            str: The summarized text.
        """
        logger.debug("Running synchronous summarization via litellm...")
        try:
            return asyncio.run(self.summarize_content_async(content, prompt))
        except Exception as e:
            logger.error(f"Error running sync summarization via litellm: {e}", exc_info=True)
            return ""

if __name__ == '__main__':
    # This is for testing the LlmHandler directly
    from dotenv import load_dotenv
    load_dotenv()

    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("GEMINI_API_KEY not found in .env file. Please add it for testing.")
    else:
        handler = LlmHandler(gemini_key)

        test_content = (
            "Artificial intelligence (AI) is revolutionizing the software development lifecycle. "
            "From code generation to automated testing, AI tools are empowering developers to build better software faster. "
            "Companies are increasingly adopting AI-powered solutions to streamline their workflows and reduce time-to-market. "
            "One of the most popular applications is in code completion, where tools like GitHub Copilot suggest entire lines or blocks of code. "
            "Another area is in testing, where AI can automatically generate test cases and identify bugs that human testers might miss. "
            "Despite these hurdles, the trend is undeniable: AI is becoming an indispensable part of the modern developer's toolkit."
        )

        print("--- Testing Synchronous Summarization (via litellm) ---")
        summary_sync = handler.summarize_content_sync(test_content)
        print(summary_sync)

        async def run_async_test():
            print("\n--- Testing Asynchronous Summarization (via litellm) ---")
            summary_async = await handler.summarize_content_async(test_content)
            print(summary_async)

        asyncio.run(run_async_test())
