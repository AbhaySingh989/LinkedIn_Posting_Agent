from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from src.llm_handler import LlmHandler
from config import load_config

# Load configuration to get API key
config = load_config()
if not config or not config.gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in configuration.")

# Initialize the LLM handler
llm_handler = LlmHandler(config.gemini_api_key)

class SummarizationTool(BaseTool):
    name: str = "Article Summarization Tool"
    description: str = "Summarizes the provided text content into a concise and engaging LinkedIn post. Input should be the full text content of the article."

    def _run(self, article_content: str) -> str:
        """Uses the LlmHandler to summarize the article content."""
        # This is a synchronous wrapper. The actual llm_handler method is async.
        # CrewAI v0.28.8 has some issues with async tools, so we run it like this.
        # In a more advanced setup, we might use asyncio.run() here,
        # but for now, we need to adjust LlmHandler to have a sync method.
        return llm_handler.summarize_content_sync(article_content)

def create_summary_crew():
    """Creates and configures the summarization crew."""

    summarization_tool = SummarizationTool()

    # Define the Summarizer Agent
    summarizer_agent = Agent(
        role='Expert LinkedIn Content Creator',
        goal='Create a concise and engaging summary of a tech article to be used as a LinkedIn post. The post should include a hook, key takeaways, and a concluding thought or question.',
        backstory=(
            "You are a professional content strategist with years of experience in creating viral tech content for LinkedIn. "
            "You know how to grab the audience's attention and distill complex information into bite-sized, shareable insights."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[summarization_tool]
    )

    # Define the Summarization Task
    # The `inputs` for this task will be provided by the orchestrator during kickoff.
    # We expect 'article_title' and 'article_content' in the input dictionary.
    summarize_task = Task(
        description=(
            "Summarize the given article content into a LinkedIn post. "
            "The article title is: '{article_title}'.\n"
            "Here is the content:\n{article_content}"
        ),
        expected_output=(
            "A well-formatted, engaging LinkedIn post summary of the article. "
            "The summary should be ready to be copy-pasted. "
            "It must include a captivating hook, 2-3 key bullet points, and a concluding sentence to spark conversation. "
            "Do not include the original URL in the output."
        ),
        agent=summarizer_agent
    )

    # Define the Crew
    summary_crew = Crew(
        agents=[summarizer_agent],
        tasks=[summarize_task],
        process=Process.sequential,
        verbose=2
    )

    return summary_crew

if __name__ == '__main__':
    # This is for testing the crew directly
    print("Testing the summary crew...")
    crew = create_summary_crew()
    test_input = {
        'article_title': 'The Rise of AI in Software Development',
        'article_content': (
            "Artificial intelligence (AI) is revolutionizing the software development lifecycle. "
            "From code generation to automated testing, AI tools are empowering developers to build better software faster. "
            "Companies are increasingly adopting AI-powered solutions to streamline their workflows and reduce time-to-market. "
            "One of the most popular applications is in code completion, where tools like GitHub Copilot suggest entire lines or blocks of code. "
            "Another area is in testing, where AI can automatically generate test cases and identify bugs that human testers might miss. "
            "While the benefits are clear, there are also challenges, including the need for large datasets to train AI models and concerns about the security of AI-generated code. "
            "Despite these hurdles, the trend is undeniable: AI is becoming an indispensable part of the modern developer's toolkit."
        )
    }
    result = crew.kickoff(inputs=test_input)
    print("\n--- Crew Kickoff Result ---")
    print(result)
