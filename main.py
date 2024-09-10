import logging

from automationserver import AutomationServer, AutomationServerConfig, AutomationServerLoggingHandler
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException

from queuefiller import populate_queue

if __name__ == "__main__":
    AutomationServerConfig.from_enviroment(
        fallback_url="http://localhost:8000/api", fallback_token=""
    )

    logging.basicConfig(level=logging.INFO,handlers=[AutomationServerLoggingHandler(),logging.StreamHandler()])
    logger = logging.getLogger(__name__)

    ats = AutomationServer.from_environment()

    # We are running locally, so we will use a fixed workqueue_id
    if ats is None:
        ats = AutomationServer.debug(workqueue_id=1)

    logger.info(f"Using {ats}")
    workqueue = ats.workqueue()

    # Populate the workqueue
    populate_queue(workqueue)

    # Do more initailization here
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-search-engine-choice-screen")
    driver = webdriver.Chrome(options=options)


    for item in workqueue:
        with item:
            data = item.get_data_as_dict()

            # Open the URL
            driver.get(data["url"])

            # Get the count of img tags
            images = driver.find_elements(By.TAG_NAME, "img")
            data["imagecount"] = len(images)

            # Get the count of a tags with href attributes
            links = driver.find_elements(By.TAG_NAME, "a")
            try:
                data["hrefcount"] = len(
                    [link for link in links if link.get_attribute("href")]
                )
            except StaleElementReferenceException:
                logger.error(f"An error occurred while counting hrefs on: {data['url']}")
                data["hrefcount"] = -1

            # Update the workqueue item
            item.update(data)

    driver.close()
    driver.quit()
