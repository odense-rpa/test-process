import logging
import asyncio

from automationserver import AutomationServer, AutomationServerConfig, AutomationServerLoggingHandler
from queuefiller import populate_queue
from playwright.async_api import async_playwright

async def main():
    # Set up configuration
    AutomationServerConfig.from_enviroment(
        fallback_url="http://localhost:8000/api", fallback_token=""
    )
    
    logging.basicConfig(level=logging.INFO, handlers=[AutomationServerLoggingHandler(), logging.StreamHandler()])
    logger = logging.getLogger(__name__)

    ats = AutomationServer.from_environment()

    # Running locally, use a fixed workqueue_id
    if ats is None:
        ats = AutomationServer.debug(workqueue_id=1)

    logger.info(f"Using {ats}")
    workqueue = ats.workqueue()

    # Populate the workqueue
    populate_queue(workqueue)

    # Start Playwright
    async with async_playwright() as p:
        # Launch Chrome with necessary options
        browser = await p.chromium.launch(headless=True, args=["--disable-search-engine-choice-screen"])
        page = await browser.new_page()

        for item in workqueue:
            with item:
                data = item.get_data_as_dict()

                # Open the URL
                await page.goto(data["url"])

                # Get the count of img tags
                images = await page.query_selector_all("img")
                data["imagecount"] = len(images)

                # Get the count of a tags with href attributes
                try:
                    links = await page.query_selector_all("a")
                    data["hrefcount"] = len([link for link in links if await link.get_attribute("href")])
                except Exception as e:
                    logger.error(f"An error occurred while counting hrefs on: {data['url']} - {e}")
                    data["hrefcount"] = -1

                # Update the workqueue item
                item.update(data)

        await browser.close()

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
