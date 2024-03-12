import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.action_chains import ActionChains
from LOCATIONS import LOCATIONS
from RESTAURANTS import RESTAURANTS


# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCATIONS = LOCATIONS
RESTAURANTS = RESTAURANTS
FILE_PATH = "prices.jsonl"
# Use your own executable_path (download from https://chromedriver.chromium.org/).
CHROMEDRIVER_PATH = "/Users/apple/Downloads/chromedriver-mac-arm64/chromedriver"

def setup_driver():
    # Webdriver options
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")

    
    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def find_search_box_and_enter_query(driver, query, restaurant_or_location = "RESTAURANT"):
    try:
        # Wait for the search box to become clickable
        if restaurant_or_location == "RESTAURANT":
            search_box_id = "search-suggestions-typeahead-input"
            wait_time = 2
        elif restaurant_or_location == "LOCATION":
            search_box_id = "location-typeahead-home-input"
            wait_time = 5

        search_box = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((By.ID, search_box_id))
        )
        
        search_box.clear()
        search_box.click()
        
        length_of_existing_text = len(search_box.get_attribute('value'))  # Get the length of the existing text
        for _ in range(length_of_existing_text):
            search_box.send_keys(Keys.BACKSPACE)
            
        search_box.click()
        
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)
        if restaurant_or_location == "LOCATION":     
            # Sometimes using the ActionChains can help perform more complex sequences of actions that may be required
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Search here']"))
            )
            ActionChains(driver).move_to_element(search_button).click(search_button).perform()
            time.sleep(1)
            logger.info(f"Fisnished inputting address!")
        else:
            logger.info(f"Passed {query} search page!")

        return True
    except:
        return False
  

def scrape_restaurant_data(driver, restaurant_name, location):
    item_data = {}
    wait = WebDriverWait(driver, 2)
    if find_search_box_and_enter_query(driver, restaurant_name, restaurant_or_location = "RESTAURANT"):
        try:
            # Click on the first restaurant result
            first_result = wait.until(EC.element_to_be_clickable((By.XPATH, "//h3[contains(text(), '" + restaurant_name + "')]")))
            first_result.click()
        except:
            logger.info(f"{restaurant_name} not found at {location}.")
            return

    try:
        # Find the script tag that contains the JSON data
        script = wait.until(EC.presence_of_element_located((By.XPATH, "//script[@type='application/ld+json']")))
        json_data = json.loads(script.get_attribute('innerHTML'))
        # Navigate through the JSON structure to extract menu items
        if 'hasMenu' in json_data:
            menu_sections = json_data['hasMenu']['hasMenuSection']
            for section in menu_sections:
                for item in section['hasMenuItem']:
                    name = item['name']
                    price = item['offers']['price']
                    # Add the item name and price to the item_data dictionary
                    item_data[name] = price
        full_address = None
        if "address" in json_data:
            address = json_data['address']
            full_address = f"{address['streetAddress']}, {address['addressLocality']}, {address['addressRegion']} {address['postalCode']}, {address['addressCountry']}"
                                    
        item_data['location'] = full_address 
        
        # Add code to get the calories here!
        
    except Exception as e:
        logger.error(f"Error while scraping data: {e}")
        
    return item_data

def update_json_file(location, restaurant, items):
    try:
        # Load the existing data
        with open(FILE_PATH, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    # Update the location data with the new restaurant information
    if location not in data:
        data[location] = {}
    data[location][restaurant] = items

    # Write the updated data back to the file
    with open(FILE_PATH, 'w') as f:
        json.dump(data, f, indent=4)
        
def main():
    
    for location in LOCATIONS:
        driver = setup_driver()
        in_search_page = False
        driver.get("https://www.ubereats.com")
        for restaurant in RESTAURANTS:
            logger.info(f"Scraping {restaurant} at {location}")
            driver.get("https://www.ubereats.com")
            if not in_search_page:
                # Go to search page
                if find_search_box_and_enter_query(driver, location, restaurant_or_location="LOCATION"):
                    items = scrape_restaurant_data(driver, restaurant, location)
                    update_json_file(location, restaurant, items)
                    in_search_page = True
            else:
                items = scrape_restaurant_data(driver, restaurant, location)
                update_json_file(location, restaurant, items)
        driver.quit()

if __name__ == "__main__":
    main()
