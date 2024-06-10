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
# import LOCATIONS
from FFLOCALRESTAURANTS import RESTAURANTS


# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCATIONS = ['2800 oxford dr, bethel park, pa, 15102, us',
  '15190 crossroads pkwy, gulfport, ms, 39503, us',
  '6840 northlake mall drive, charlotte, nc, 28216, us',
  '1835 n highway 17, mount pleasant, sc, 29464, us',
  '301 rocky run pkwy, wilmington, de, 19803, us',
  '1100 timber dr e, garner, nc, 27529, us',
  '240 mall blvd, monroeville, pa, 15146, us',
  '2871 stonecrest cir, lithonia, ga, 30038, us',
  '1114 woodruff road, greenville, sc, 29607, us',
  '20430 highway 59 n, humble, tx, us, us',
  '3502 e 86th st, indianapolis, in, 46240, us',
  '3202 s highway 17, murrells inlet, sc, 29576, us',
  '1516 s willow st, manchester, nh, 03103, us',
  '2794 parkway, pigeon forge, tn, 37863, us',
  '6915 w 38th st, indianapolis, in, 46214, us',
  '3700 towne crossing blvd, mesquite, tx, 75150, us',
  '12811 s tryon st, charlotte, nc, us, us',
  '703 41, schererville, in, 46375, us',
  '395 s cedar crest blvd, allentown, pa, 18103, us',
  '3670 camp creek parkway, atlanta, ga, 30331, us',
  '449 opry mills dr, nashville, tn, 37214, us',
  '4951 belt line rd, dallas, tx, 75001, us',
  '4239 nw expressway st, oklahoma city, ok, 73116, us',
  '4423 w wendover ave, greensboro, nc, 27407, us',
  '409 w wt harris blvd, charlotte, nc, 28262, us',
  '311 north clark road, cedar hill, tx, 75104, us',
  '115 hendersonvile rd, asheville, nc, 28803, us',
  '4000 city ave, philadelphia, pa, 19131, us',
  '2502 e springs dr, madison, wi, 53704, us']

RESTAURANTS = ["TGI Fridays"] 
FILE_PATH = f"missing_nonca_fullserv_rnd3.jsonl"
# Use your own executable_path (download from https://chromedriver.chromium.org/).
CHROMEDRIVER_PATH = "/Users/alyssanguyen/Downloads/chromedriver-mac-arm64/chromedriver"
#CHROMEDRIVER_PATH = "/Users/sakshikolli/Downloads/chromedriver-mac-x64/chromedriver"


def setup_driver():
    # Webdriver options
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
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

def scrape_restaurant_data(driver, restaurant_name, location, carousel=False):
    item_data = {}
    wait = WebDriverWait(driver, 3)
    
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
        item_data['location'] = full_address
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
                    #get_carousel_items(driver, restaurant, location)
                    in_search_page = True
            else:
                items = scrape_restaurant_data(driver, restaurant, location)
                update_json_file(FILE_PATH, location, restaurant, items)
                driver.back()
                #get_carousel_items(driver, restaurant, location)
            driver.back()
        driver.quit()


if __name__ == "__main__":
    main()


