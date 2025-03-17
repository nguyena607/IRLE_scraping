import json
import logging
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException

# import LOCATIONS
from FFLOCALRESTAURANTS import RESTAURANTS
from LOCALRESTAURANT_LOCATIONS import LOCATIONS

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCATIONS = LOCATIONS
RESTAURANTS = RESTAURANTS
FILE_PATH = f"ubereats_mega_wave4.jsonl"
# Use your own executable_path (download from https://chromedriver.chromium.org/).
CHROMEDRIVER_PATH = "/Users/alyssanguyen/Downloads/chromedriver-mac-arm64-133/chromedriver"
#CHROMEDRIVER_PATH = "/Users/sakshikolli/Downloads/chromedriver-mac-x64/chromedriver"


def setup_driver():
    # Webdriver options
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    # chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    # chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def click_close_button(driver):
    wait = WebDriverWait(driver, 5)
    try:
        # Try to locate and click the first close button
        close_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-baseweb='button' and @aria-label='Close' and @title='Close']"))
        )
        close_button.click()
        logger.info("Clicked the 'Close' button (first type).")
        return True
    except Exception as e:
        logger.info("First 'Close' button not found or not clickable.")
 
    logger.info("No 'Close' buttons were found.")
    return False

def find_search_box_and_enter_query(driver, query, restaurant_or_location="RESTAURANT"):
    wait_time = 3
    try:
        print(f"Attempting to search for {query} in {restaurant_or_location}...")
        
        # Determine search box based on restaurant or location
        if restaurant_or_location == "RESTAURANT":
            search_box_id = "search-suggestions-typeahead-input"
        elif restaurant_or_location == "LOCATION":
            search_box_id = "location-typeahead-home-input"
        print(f"Using search box ID: {search_box_id}")

        # Wait for the search box to become clickable
        search_box = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((By.ID, search_box_id))
        )
        print("Search box found and clickable.")

        search_box.clear()
        search_box.click()
        print("Search box cleared and clicked.")

        # Delete existing text by simulating backspace keypresses
        length_of_existing_text = len(search_box.get_attribute('value'))
        print(f"Length of existing text: {length_of_existing_text}")
        for _ in range(length_of_existing_text):
            search_box.send_keys(Keys.BACKSPACE)
        print("Cleared existing text.")

        search_box.click()  # Click again just in case

        # Enter the query
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        print(f"Entered query: {query}")
        time.sleep(2)

        if restaurant_or_location == "LOCATION":
            print("Waiting for 'Search here' button to be clickable...")
            # Wait for and click the "Search here" button
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Search here']"))
            )
            print("'Search here' button found.")
            ActionChains(driver).move_to_element(search_button).click(search_button).perform()
            print("Clicked 'Search here' button.")
            time.sleep(1)
            logger.info("Finished inputting address!")
        else:
            logger.info(f"Passed {query} search page!")

        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def scrape_restaurant_data(driver, restaurant_name, location, carousel=False):
    item_data = {}
    wait = WebDriverWait(driver, 3)
    correct_address = None

    if not carousel:
        if find_search_box_and_enter_query(driver, restaurant_name, restaurant_or_location="RESTAURANT"):
            try:
                # Click on the first restaurant result
                first_result = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-testid='store-card']")))
                href = first_result.get_attribute('href')
                logger.info(f"Navigating to {href}")
                # Navigate directly to the link
                driver.get(href)
            except:
                logger.info(f"{restaurant_name} not found at {location}.")
                return
            
            try:
                # Check for and click the close button if it exists
                close_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='close-button']")))
                close_button.click()
                logger.info("Closed the pop-up window.")
            except:
                logger.info("No pop-up window to close.")
            
            try:
                # Check for and click the close button with the specified attributes
                close_button_alt = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-baseweb='button' and @aria-label='Close' and @title='Close']")))
                close_button_alt.click()
                logger.info("Closed the pop-up window with the alternate close button.")
            except:
                logger.info("No alternate pop-up window to close or unable to find the alternate close button.")
    
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
            correct_address = full_address.lower()
        
        # Extracting DISTANCE and RATINGS 
        info_elems = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//span[@data-testid='rich-text']")))
        
        # Check if there are at least four bar elements
        if len(info_elems) >= 4:
            ratings_elem = info_elems[0]
            rating = ratings_elem.text
            logger.info(f"Found rating: {rating}")
            
            no_ratings_elem = info_elems[1]
            no_ratings_txt = no_ratings_elem.text
            no_ratings_match = re.search(r'(\d{1,3}\+?)', no_ratings_txt)
            if no_ratings_match:
                no_ratings = no_ratings_match.group(1)
                logger.info(f"Found number of ratings: {no_ratings}")
            else:
                no_ratings = None
                logger.info("No ratings found.")
            
            distance_elem = info_elems[3]  # This will get the fourth element in the list
            distance = distance_elem.text
            logger.info(f"Found distance: {distance}")
        else:
            logger.info("Not enough rating elements found")
            rating = None   
            distance = None
            no_ratings = None
        
        # Scrape item names and prices
        try:
            item_elements = driver.find_elements(By.XPATH, "//span[@data-testid='rich-text']")
            items = []
            prices = []
            
            for elem in item_elements:
                text = elem.text.strip()
                if text.startswith('$'):
                    prices.append(text)
                else:
                    items.append(text)
            
            if len(items) == len(prices):
                for item, price in zip(items, prices):
                    menu_items[item] = price
                    logger.info(f"Found item: {item} with price: {price}")
            else:
                logger.warning("Mismatch between the number of items and prices.")
        
        except Exception as e:
            logger.error(f"Error while scraping menu items and prices: {e}")
        
        # Update item_data with collected information
        item_data['menu'] = menu_items
        item_data['location'] = correct_address
        item_data['rating'] = rating  # make sure you assign the rating text as rating
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
    
    if correct_address is None:
        logger.error("Failed to extract correct address.")

    return [item_data, correct_address]
    
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


def save_locations_dict_to_json(locations_dict, file_path):
    """Save locations_dict to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(locations_dict, f)

def load_locations_dict_from_json(file_path):
    """Load locations_dict from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def main():
    percentage_threshold = 20 

    # Load locations_dict from JSON if it exists
    locations_dict_file = load_locations_dict_from_json('locations_dict_mega.json')
    
    if locations_dict_file:
        locations_dict = locations_dict_file
    else:
        all_locations = pd.read_csv("/Users/alyssanguyen/Desktop/IRLE_scraping/scripts/ubereats_mega_combined.csv")
        locations_dict = all_locations.groupby('restaurant_name')['restaurant_location'].apply(list).to_dict()

    initial_lengths = {restaurant: len(locations) for restaurant, locations in locations_dict.items()}

    thresholds = {restaurant: int(length * (percentage_threshold / 100)) for restaurant, length in initial_lengths.items()}

    while True:
        all_thresholds_reached = True

        for restaurant in locations_dict.keys():
            locations_lst = locations_dict[restaurant]
            
            if len(locations_lst) > thresholds[restaurant]:
                all_thresholds_reached = False

                for location in locations_lst[:]:  # Iterate over a copy of the list
                    logger.info(f"Scraping {restaurant} at {location}")
                    driver = setup_driver()
                    driver.get("https://www.ubereats.com")
                    click_close_button(driver)

                    # Go to search page and search by location
                    if find_search_box_and_enter_query(driver, location, restaurant_or_location="LOCATION"):
                        items = scrape_restaurant_data(driver, restaurant, location)
                        update_json_file(FILE_PATH, location, restaurant, items[0])

                        # Extract short locations
                        match = re.match(r"(.*?), \d{5}$", location)
                        location_short = match.group(1) if match else None
                        print(location_short)
                        if items[1] != None: 
                            match_ = re.match(r"(.*?), \d{5}$", items[1])
                            correct_address_short = match_.group(1) if match_ else None   
                            print(correct_address_short)

                        # Check if locations match and add to remove list if they do
                        if location_short == correct_address_short:
                            print("this is a match!")
                            # Remove location from the list and update dictionary
                            locations_lst.remove(location)
                            locations_dict[restaurant] = locations_lst
                            save_locations_dict_to_json(locations_dict, 'locations_dict.json')
                            logger.info("locations_dict updated and saved to JSON.")

                    driver.quit()
                    print(f"Finished scraping {restaurant} at {location}")

        # Check if all restaurants have reached the threshold
        if all_thresholds_reached:
            print("All restaurants have reached the threshold. Stopping scraping.")
            break

if __name__ == "__main__":
    main()