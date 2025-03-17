import json
import logging
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CHROMEDRIVER_PATH = "/Users/alyssanguyen/Downloads/chromedriver-mac-arm64-133/chromedriver"
FILE_PATH = "simplified_scrape_results_1.json"

# Function to set up the WebDriver
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--disable-gpu")
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
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='find-food-button']"))
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


def scrape_restaurant_address(driver, restaurant_name, location):
    try:
        # Search for the location first
        if not find_search_box_and_enter_query(driver, location, restaurant_or_location="LOCATION"):
            logger.error(f"Failed to set location: {location}")
            return None
        
        # Search for the restaurant
        if not find_search_box_and_enter_query(driver, restaurant_name, restaurant_or_location="RESTAURANT"):
            logger.error(f"Failed to find restaurant: {restaurant_name}")
            return None
        
        # Click on the first restaurant result
        first_result = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-testid='store-card']"))
        )
        driver.get(first_result.get_attribute("href"))

        # Add close button code here if there is a close button 
        
        # Wait for all rich-text elements to load
        rich_text_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//span[@data-testid='rich-text']"))
        )
        
        # Iterate through all rich-text elements and filter for the address
        for element in rich_text_elements:
            text = element.text.strip()
            if "," in text and any(state in text for state in ["CA", "US"]):  # Heuristic to identify an address
                logger.info(f"Scraped address: {text}")
                return text
        
        logger.warning("No address found in rich-text elements.")
        return None
    
    except Exception as e:
        logger.error(f"Error scraping address for {restaurant_name} at {location}: {e}")
        return None

def update_json_file(file_path, location, restaurant_name, address):
    try:
        # Load existing data from JSON file if it exists; otherwise start with an empty list
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                logger.info("Loaded existing JSON data.")
        except FileNotFoundError:
            data = []
        
        # Append new data to the list
        entry = {
            "location": location,
            "restaurant": restaurant_name,
            "address": address,
        }
        
        data.append(entry)

        # Write updated data back to the JSON file
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
        
        logger.info(f"Saved data for {restaurant_name} at {location}")
    except Exception as e:
        logger.error(f"Error saving data to JSON: {e}")

# Main function
def main():

    # Load and process restaurant and location data
    wave_3 = pd.read_csv("/Users/alyssanguyen/Desktop/IRLE_scraping/scripts/attrition_1.csv")
    grouped = wave_3.groupby('restaurant_name')['restaurant_location'].apply(list).reset_index()
    restaurants_and_locations = grouped.set_index('restaurant_name')['restaurant_location'].to_dict()
    
    restaurants_and_locations['The Habit Burger & Grill'] = restaurants_and_locations.pop('The Habit')

    print(restaurants_and_locations)

    for restaurant_name, locations in restaurants_and_locations.items():
        for location in locations:
            logger.info(f"Scraping {restaurant_name} at {location}")
            
            driver = setup_driver()
            try:
                driver.get("https://www.ubereats.com")
                
                # Scrape the address and save results
                click_close_button(driver)
                address_data = scrape_restaurant_address(driver, restaurant_name, location)
                if address_data:
                    update_json_file(FILE_PATH, location, restaurant_name, address_data)
            
            finally:
                driver.quit()

if __name__ == "__main__":
    main()