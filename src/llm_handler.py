
import google.generativeai as genai
import logging

class LlmHandler:
    """
    Handles interaction with the Google Gemini LLM.
    """
    def __init__(self, api_key):
        """
        Initializes the LlmHandler.

        Args:
            api_key (str): The Google Gemini API key.
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        logging.info("LlmHandler initialized.")

    def summarize(self, text, prompt):
        """
        Summarizes the given text using the Gemini LLM.

        Args:
            text (str): The text to summarize.
            prompt (str): The prompt to use for summarization.

        Returns:
            str: The summarized text.
        """
        try:
            response = self.model.generate_content(f"{prompt}\n\n{text}")
            return response.text
        except Exception as e:
            logging.error(f"Error summarizing text: {e}")
            return None

