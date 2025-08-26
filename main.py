import asyncio
import logging
import schedule
import time
from src.orchestrator import Orchestrator
from config import load_config

# --- Basic Logging Setup ---
# Set up a logger to print messages to the console.
# This is helpful for seeing the flow of the application.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Suppress noisy loggers from libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
# --- End of Logging Setup ---

logger = logging.getLogger(__name__)

async def job():
    """The main job to be run by the scheduler."""
    logger.info("Starting a new orchestrator run...")
    try:
        config = load_config()
        if not config:
            logger.error("Failed to load configuration. Exiting.")
            return

        orchestrator = Orchestrator(config)
        await orchestrator.run()
        logger.info("Orchestrator run finished.")
    except Exception as e:
        logger.error(f"An error occurred during the orchestrator run: {e}", exc_info=True)

async def main():
    """The main entry point of the application."""
    config = load_config()

    if config and config.schedule:
        logger.info(f"Scheduling job with schedule: '{config.schedule}'")
        # This is a simple example. A more robust scheduler might be needed for complex rules.
        # For now, we support 'daily' and 'hourly'.
        if config.schedule.lower() == 'daily':
            schedule.every().day.at("09:00").do(lambda: asyncio.create_task(job()))
        elif config.schedule.lower() == 'hourly':
            schedule.every().hour.do(lambda: asyncio.create_task(job()))
        else:
            logger.warning(f"Unknown schedule '{config.schedule}'. Defaulting to a single run.")
            await job()
            return

        logger.info("Scheduler started. First job will run at the next scheduled time.")
        # Run the first job immediately, then schedule future runs.
        asyncio.create_task(job())

        while True:
            schedule.run_pending()
            await asyncio.sleep(1)
    else:
        logger.info("No schedule configured. Running job once.")
        await job()

if __name__ == '__main__':
    # Ensure we are in an async context to run the main function.
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Application shutting down.")
