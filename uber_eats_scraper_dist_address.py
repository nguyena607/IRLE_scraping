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
import datetime
import re
from selenium.webdriver.common.action_chains import ActionChains
from NON_CA_LOCATION import LOCATIONS
from RESTAURANTS import RESTAURANTS


# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCATIONS = LOCATIONS
RESTAURANTS = RESTAURANTS
FILE_PATH = f"raw_prices_ubereats_non_ca_{datetime.datetime.now().strftime('%m-%d-%Y')}.jsonl"
# Use your own executable_path (download from https://chromedriver.chromium.org/).
CHROMEDRIVER_PATH = "/Users/apple/Downloads/chromedriver-mac-arm64/chromedriver"
#CHROMEDRIVER_PATH = "/Users/sakshikolli/Downloads/chromedriver-mac-x64/chromedriver"


def setup_driver():
    # Webdriver options
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def find_search_box_and_enter_query(driver, query, restaurant_or_location = "RESTAURANT"):
    wait_time = 3
    try:
        # Wait for the search box to become clickable
        if restaurant_or_location == "RESTAURANT":
            search_box_id = "search-suggestions-typeahead-input"
        elif restaurant_or_location == "LOCATION":
            search_box_id = "location-typeahead-home-input"

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
def scrape_restaurant_data(driver, restaurant_name, location, carousel = False):

    item_data = {}
    wait = WebDriverWait(driver, 3)
    if not carousel:
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
           
            ratings_elem = info_elems[0]
            rating = ratings_elem.text
            logger.info(f"Found rating: {rating}")

            no_ratings_elem = info_elems[1]
            no_ratings_txt = no_ratings_elem.text
            no_ratings = re.search('(\d{1,3}\+?)', no_ratings_txt).group(1)
            logger.info(f"Found number of ratings: {no_ratings}")

            distance_elem = info_elems[3]  # This will get the fourth element in the list
            distance = distance_elem.text
            logger.info(f"Found distance: {distance}")

        else:
            logger.info("Not enough rating elements found")
            rating = None   
            distance = None
            no_ratings = None

        # Update item_data with collected information
        item_data['menu'] = menu_items
        item_data['location'] = full_address
        item_data['rating'] = rating #make sure you assign the rating text as rating
        item_data['number of ratings'] = no_ratings
        item_data['distance'] = distance

        try:
            # Attempt to find the close button using its aria-label
            wait_2 = WebDriverWait(driver, 1)
            close_button = wait_2.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close']")))
            close_button.click()
            logger.info("Close button clicked successfully.")
            driver.back()
            driver.back()
        except:
            logger.info(" ")

    except Exception as e:
        logger.error(f"Error while scraping data: {e}")
    
    
    return item_data

def get_carousel_items(driver, restaurant, location):
    if find_search_box_and_enter_query(driver, restaurant, restaurant_or_location="RESTAURANT"):
        wait = WebDriverWait(driver, 2)
        try:
            # Check for the presence of at least one carousel slide to ensure the carousel exists
            carousel_exists = wait.until(EC.presence_of_element_located((By.XPATH, "//li[@data-testid='carousel-slide']")))
            
            if carousel_exists:
                carousel_slides = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-testid='carousel-slide']")))
                logger.info(f"Found {len(carousel_slides)} carousel slides.")
                for index in range(len(carousel_slides)):
                    # Refresh the list of carousel slides to ensure we have the most current elements
                    carousel_slides = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-testid='carousel-slide']")))
                    slide = carousel_slides[index]
                    store_card_link = slide.find_element(By.XPATH, ".//a[@data-testid='store-card']")
                    
                    href = store_card_link.get_attribute('href')
                    logger.info(f"Navigating to {href}")
                    
                    # Navigate directly to the link
                    driver.get(href)
                    
                    item_data = scrape_restaurant_data(driver, restaurant, location, carousel = True)
                    update_json_file(FILE_PATH, location, restaurant, item_data)    
                    driver.back()
                    
                    # Wait for the carousel to reappear
                    wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-testid='carousel-slide']")))
                logger.info("Finished visiting all carousel items.")

        except:
            logger.info("Carousel not found.")
    else:
        logger.info("Search box not found or query failed.")


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
    if new_data and 'location' in new_data:
        if not new_data['location']:
            address = '_'
        else:
            address = '_'.join(new_data['location'].split())
        restaurant_name= '_'.join(restaurant.split())
        restaurant_key = f"{restaurant_name}@{address}"

        # Now use the unique key for the restaurant
        data[location][restaurant_key] = new_data

        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

        logger.info(f"Data for {restaurant_key} in {location} added to {file_path}.")

        
def main():
    # First, scrape top restaurants for all locations
                
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
                    update_json_file(FILE_PATH, location, restaurant, items)
                    driver.back()
                    get_carousel_items(driver, restaurant, location)
                    in_search_page = True
            else:
                #scrape_top_restaurant(driver, location, restaurant)
                items = scrape_restaurant_data(driver, restaurant, location)
                update_json_file(FILE_PATH, location, restaurant, items)
                driver.back()
                get_carousel_items(driver, restaurant, location)
            driver.back()
        driver.quit()


if __name__ == "__main__":
    main()


