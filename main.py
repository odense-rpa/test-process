import logging

from automationserver import AutomationServer, AutomationServerConfig
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    AutomationServerConfig.from_enviroment(
        fallback_url="http://localhost:8000/api", fallback_token=""
    )

    ats = AutomationServer.from_environment()

    # We are running locally, so we will use a fixed workqueue_id
    if ats is None:
        ats = AutomationServer.debug(workqueue_id=1)

    logger.info(f"Using {ats}")
    workqueue = ats.workqueue()

    # Do more initailization here
    driver = webdriver.Safari()

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
            data["hrefcount"] = len(
                [link for link in links if link.get_attribute("href")]
            )

            # Update the workqueue item
            item.update(data)

    driver.close()
    driver.quit()
