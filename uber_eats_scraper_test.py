import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
import traceback
import time
import re
from urllib.request import urlopen
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


FILE_PATH = "prices_test.jsonl"
# Use your own executable_path (download from https://chromedriver.chromium.org/).
CHROMEDRIVER_PATH = "/Users/sakshikolli/Downloads/chromedriver-mac-x64/chromedriver"
LOCATIONS = ["2020 Bancroft Way, Berkeley"]
RESTAURANTS = ["McDonald", "Jack in the Box", "KFC",  "Wendy", "Burger King", "Taco Bell"]

def setup_driver():
    # Webdriver options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument(
    #     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    #     "(KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
    # )
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")

    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def find_search_box_and_enter_query(driver, query, restaurant_or_location = "RESTAURANT"):
    try:
        # Wait for the search box to become clickable
        if restaurant_or_location == "RESTAURANT":
            search_box = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "search-suggestions-typeahead-input"))
            )
        elif restaurant_or_location == "LOCATION":
            search_box = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "location-typeahead-home-input"))
                #print("found search box")
            )
        search_box.click()
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        if restaurant_or_location == "LOCATION":
            # Sometimes using the ActionChains can help perform more complex sequences of actions that may be required
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Search here']"))
            )
            ActionChains(driver).move_to_element(search_button).click(search_button).perform()
            logger.info(f"Fisnished inputting address!")
        else:
            logger.info(f"Passed {query} search page!")

        return True
    except:
        return False

def scrape_restaurant_data(driver, restaurant_name):
    item_data = {}
    wait = WebDriverWait(driver, 10)
    if find_search_box_and_enter_query(driver, restaurant_name, restaurant_or_location = "RESTAURANT"):
        # Click on the first restaurant result
        first_result = wait.until(EC.element_to_be_clickable((By.XPATH, "//h3[contains(text(), '" + restaurant_name + "')]")))
        first_result.click()

        print(driver.current_url)
        return getMenu(driver.current_url)

def getMenu(url):
    page = urlopen(url)
    html = page.read().decode("utf-8")
    format = r"{\"@type\":\"MenuItem\",\"name\":\"(.+?)\",\"description\":\".*?\",\"offers\":{\"@type\":\"Offer\",\"price\":\"(\d+\.\d+)\",\"priceCurrency\":\"USD\"}}"
    menu = re.findall(format, html)
    return dict(menu)


def main():
    driver = setup_driver()
    all_data = {}

    for restaurant in RESTAURANTS:
        logger.info(f"Scraping {restaurant}")
        driver.get("https://www.ubereats.com")
        if find_search_box_and_enter_query(driver, LOCATIONS[0], restaurant_or_location = "LOCATION"):
            all_data[restaurant] = scrape_restaurant_data(driver, restaurant)

    with open(FILE_PATH, 'w') as f:
        for restaurant, items in all_data.items():
            entry = json.dumps({restaurant: items})
            f.write(f"{entry}\n")

    driver.quit()

if __name__ == "__main__":
    main()
