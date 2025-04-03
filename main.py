import logging
import asyncio
import logging.config
import sys
from random import randint
from time import sleep

from playwright.async_api import async_playwright

from automation_server_client import AutomationServer, Workqueue


def populate_queue(workqueue: Workqueue):
    # List of major news sites to post sequentially
    news_sites = [
        "https://www.cnn.com", 
        "https://www.bbc.com", 
        "https://www.nytimes.com", 
        "https://www.theguardian.com", 
        "https://www.reuters.com", 
        "https://www.washingtonpost.com", 
        "https://www.aljazeera.com", 
        "https://www.foxnews.com", 
        "https://www.nbcnews.com", 
        "https://www.usatoday.com"
    ]

    # Loop to create and post JSON items sequentially from the list
    for i, site in enumerate(news_sites):
        # Create the data object as a string
        data = {
            "url": site,
            "imagecount": 0,
            "hrefcount": 0
        }
       
        try:
            workqueue.add_item(data=data, reference=site)
        except Exception as e:
            print(f"An error occurred while posting item {i+1}: {e}")


async def process_workqueue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)
    # Start Playwright
    async with async_playwright() as p:
        # Launch Chrome with necessary options
        browser = await p.chromium.launch(headless=True, args=["--disable-search-engine-choice-screen"])
        page = await browser.new_page()

        for item in workqueue:
            with item:
                data = item.get_data_as_dict()

                try:
                    # Open the URL
                    await page.goto(data["url"])

                    # Get the count of img tags
                    images = await page.query_selector_all("img")
                    data["imagecount"] = len(images)

                    # Get the count of a tags with href attributes
                    links = await page.query_selector_all("a")
                    data["hrefcount"] = len([link for link in links if await link.get_attribute("href")])
    
                    # Update the workqueue item
                    item.update(data)

                    logger.info(f"Processed {data['url']} with {data['imagecount']} images and {data['hrefcount']} hrefs")
                except Exception as e:
                    logger.error(f"An error occurred while counting hrefs on: {data['url']} - {e}")
                    data["hrefcount"] = -1
                    item.fail(str(e))

            delay = randint(10, 40)
            logger.info(f"Sleeping {delay} seconds")
            sleep(delay)

        await browser.close()

# Run the async main function
if __name__ == "__main__":
    
    ats = AutomationServer.from_environment()    
    
    workqueue = ats.workqueue()

    # Populate the workqueue if we have --queue arg
    if "--queue" in sys.argv:
        workqueue.clear_workqueue("new")
        populate_queue(workqueue)
        exit(0)
    
    asyncio.run(process_workqueue(workqueue))
    
