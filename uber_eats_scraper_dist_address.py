import json
import logging
import os
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
CHROMEDRIVER_PATH = "/Users/alyssanguyen/Downloads/chromedriver-mac-arm64/chromedriver"

def clear_existing_data(file_path):
    try:
        os.remove(file_path)
        print(f"Cleared existing data in {file_path}.")
    except FileNotFoundError:
        print(f"No existing data file found at {file_path}. Starting fresh.")


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
            logger.info(f"Finished inputting address!")
        else:
            logger.info(f"Passed {query} search page!")

        return True
    except:
        return False
  
#Scrapes the restaurant data 
def scrape_restaurant_data(driver):
    item_data = {}
    wait = WebDriverWait(driver, 10)
    try:
        # Find the script tag that contains the JSON data
        script = wait.until(EC.presence_of_element_located((By.XPATH, "//script[@type='application/ld+json']")))
        json_data = json.loads(script.get_attribute('innerHTML'))
        logger.info("JSON data retrieved successfully.")

        # Initialize variables to store the extracted data
        menu_items = {}
        full_address = None

        # Extract menu items if available
        if 'hasMenu' in json_data:
            logger.info("Found 'hasMenu' in JSON data.")
            menu_sections = json_data['hasMenu'].get('hasMenuSection', [])
            for section in menu_sections:
                for item in section.get('hasMenuItem', []):
                    name = item.get('name')
                    price = item.get('offers', {}).get('price')
                    if name and price:
                        menu_items[name] = price

        # Extract the full address if available
        if "address" in json_data:
            logger.info("Found 'address' in JSON data.")
            address_parts = [json_data['address'].get(part) for part in ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode', 'addressCountry']]
            full_address = ', '.join(filter(None, address_parts))

        #Extracting DISTANCE and RATINGS 
        info_elems = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//span[@data-testid='rich-text']")))

        # Check if there are at least four bar elements
        if len(info_elems) >= 4:
           
           #FIND RATINGS HERE (copy the code below but for the FIRST element)

            distance_elem = info_elems[3]  # This will get the fourth element in the list
            distance = distance_elem.text
            logger.info(f"Found distance: {distance}")

        else:
            logger.info("Not enough rating elements found")
            rating = None   
            distance = None  

        # Update item_data with collected information
        item_data['menu'] = menu_items
        item_data['location'] = full_address
        item_data['rating'] = rating #make sure you assign the rating text as rating 
        item_data['distance'] = distance

    except Exception as e:
        logger.error(f"Error while scraping data: {e}")

    return item_data


def scrape_top_restaurant(driver, location, restaurant):
    wait = WebDriverWait(driver, 10)
    if find_search_box_and_enter_query(driver, restaurant, restaurant_or_location="RESTAURANT"):
        try:
            first_result = wait.until(EC.element_to_be_clickable((By.XPATH, "//h3[contains(text(), '" + restaurant + "')]")))
            first_result.click()
            item_data = scrape_restaurant_data(driver)
            update_json_file(FILE_PATH, location, restaurant, item_data)
        except:
            logger.info(f"{restaurant} not found at {location}.")
            return

def get_carousel_items(driver, restaurant, location):
    if find_search_box_and_enter_query(driver, restaurant, restaurant_or_location="RESTAURANT"):
        wait = WebDriverWait(driver, 10)
        try:
            # Check for the presence of at least one carousel slide to ensure the carousel exists
            carousel_exists = wait.until(EC.presence_of_element_located((By.XPATH, "//li[@data-testid='carousel-slide']")))
            
            if carousel_exists:
                carousel_slides = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-testid='carousel-slide']")))
                print(f"Found {len(carousel_slides)} carousel slides.")

                for index in range(len(carousel_slides)):
                    # Refresh the list of carousel slides to ensure we have the most current elements
                    carousel_slides = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-testid='carousel-slide']")))
                    slide = carousel_slides[index]
                    store_card_link = slide.find_element(By.XPATH, ".//a[@data-testid='store-card']")
                    
                    href = store_card_link.get_attribute('href')
                    print(f"Navigating to {href}")
                    
                    # Navigate directly to the link
                    driver.get(href)
                    
                    item_data = scrape_restaurant_data(driver)
                    update_json_file(FILE_PATH, location, restaurant, item_data)
                    # Navigate back to the carousel page
                    driver.back()

                    # Wait for the carousel to reappear
                    wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-testid='carousel-slide']")))
                print("Finished visiting all carousel items.")
            else:
                print("Carousel not found.")
        except Exception as e:
            print("An unexpected error occurred: ", e)    
        except:
            logger.info(f"{restaurant} not found at {location}.")
    else:
        print("Search box not found or query failed.")


def update_json_file(file_path, location, restaurant, new_data):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}

    if location not in data:
        data[location] = {}

    # Check if the restaurant already exists and create a unique key if so
    base_restaurant_key = restaurant
    counter = 1
    restaurant_key = base_restaurant_key
    while restaurant_key in data[location]:
        counter += 1
        restaurant_key = f"{base_restaurant_key}_{counter}"

    # Now use the unique key for the restaurant
    data[location][restaurant_key] = new_data

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

    logger.info(f"Data for {restaurant_key} in {location} added to {file_path}.")

        
def main():
    # First, scrape top restaurants for all locations
    for location in LOCATIONS:
        for restaurant in RESTAURANTS:
            driver = setup_driver()
            try:
                driver.get("https://www.ubereats.com")
                logger.info(f"Scraping top restaurant data for {restaurant} at {location}")
                if find_search_box_and_enter_query(driver, location, restaurant_or_location="LOCATION"):
                    scrape_top_restaurant(driver, location, restaurant)
            finally:
                driver.quit()  

    # After completing top restaurants, start scraping carousel items for all locations
    for location in LOCATIONS:
        for restaurant in RESTAURANTS:
            driver = setup_driver()
            try:
                driver.get("https://www.ubereats.com")
                logger.info(f"Scraping carousel restaurant data for {restaurant} at {location}")
                if find_search_box_and_enter_query(driver, location, restaurant_or_location="LOCATION"):
                    get_carousel_items(driver, restaurant,location)
                else:
                    logger.error(f"Failed to find search box or enter query for {restaurant} at {location}")
            finally:
                driver.quit() 

if __name__ == "__main__":
    clear_existing_data(FILE_PATH)
    main()

