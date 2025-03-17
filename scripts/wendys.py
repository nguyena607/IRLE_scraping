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
from time import sleep
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd 

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


FILE_PATH = "wendy_wave_4.jsonl"
# Use your own executable_path (download from https://chromedriver.chromium.org/).
CHROMEDRIVER_PATH = "/Users/alyssanguyen/Downloads/chromedriver-mac-arm64-133/chromedriver"
LOCATIONS_FILE = "wendys_locations.json"


def save_locations_to_json(locations, file_path):
    with open(file_path, "w") as file:
        json.dump(locations, file, indent=4)
    print(f"Updated LOCATIONS saved to {file_path}.")


def load_locations_dict_from_json(file_path):
    """Load locations_dict from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def clear_existing_data(file_path):
    try:
        os.remove(file_path)
        print("Cleared existing data in {}.".format(file_path))
    except FileNotFoundError:
       print("No existing data file found at {}. Starting fresh.".format(file_path))



def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    chrome_options.add_experimental_option("prefs", {"profile.default_content_setting_values.geolocation": 2})
    # chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def input_and_search(driver, location):
    try:
        print("Clicking on the 'Find a Wendy's' link...")
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Find a Wendy's"))
        )
        element.click()
        print("Successfully clicked on the 'Find a Wendy's' link.")

        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "find-search-input-text"))
        )
        print("Search box is present.")

        search_box.send_keys(location)
        print("Location entered successfully.")

        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "find-search-input-submit"))
        )
        search_button.click()
        print("Search button clicked successfully.")

        # Wait for the first address elements to be present using a generalized XPath
        address_line1 = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[starts-with(@id,'find-description')]/div/p[1]"))
        ).text
        address_line2 = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[starts-with(@id,'find-description')]/div/p[2]"))
        ).text

        # Combine the two lines into one address
        full_address = f"{address_line1}, {address_line2}"
        full_address = full_address.lower()
        print("Full Address:", full_address)

        # Wait for the button to be clickable and click it
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.order-button"))
        )
        
        # Scroll into view and click the button
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        driver.execute_script("arguments[0].click();", button)
        print("Clicked on the button.")

    except Exception as e:
        print("An error occurred:", str(e))
    
    return full_address

def click_nth_button(driver, indices, location, address):
    try:
        # Find all buttons
        buttons = WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located((By.XPATH, "//button[@type='button' and @data-testid='category-item-button']"))
        )
        
        # Click on the buttons at the specified indices
        for index in indices:
            if 0 <= index < len(buttons):
                button = buttons[index]
                
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                
                driver.execute_script("arguments[0].click();", button)
                print("Clicked on the button.")
                
                scrape(driver, location, address)
                print("scraped menu")

                driver.back()
                buttons = WebDriverWait(driver, 10).until(
                    EC.visibility_of_all_elements_located((By.XPATH, "//button[@type='button' and @data-testid='category-item-button']"))
                )
            else:
                print(f"Index {index} is out of range. Skipping...")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def scrape(driver, location, address): 
    wait = WebDriverWait(driver, 10)
    try:
        # Find all elements with class 'product-item'
        product_items = wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, "product-item")))
    except Exception as e:
        print(f"An error occurred while finding product items: {e}")
        return []   

    menu_items = []

    # Extract information for each product item
    for item in product_items:
        # Extract item name
        item_name = item.find_element(By.CLASS_NAME, 'product-item-title').text.strip()
        
        # Extract sub-title containing price and calories
        sub_title = item.find_element(By.CLASS_NAME, 'sub-title').find_element(By.TAG_NAME, 'pre').text.strip()
        
        # Split sub-title to extract price and calories
        price, calories = map(str.strip, sub_title.split('|'))
        
        # Remove leading currency symbol from price
        price = price.replace('$', '')
        calories = calories.replace(' Cal', '')
        item_info = {
            'name': item_name,
            'price': price,  
            'calories': calories
        }
        menu_items.append(item_info)
    add_menu_items_to_json(menu_items, location, address, FILE_PATH)

def add_menu_items_to_json(menu_items, location, address, file_path):
    if os.path.exists(file_path):
        # Read the existing JSON data
        with open(file_path, 'r') as file:
            data = json.load(file)
    else:
        data = {}
    
    if location not in data:
        data[location] = []

    for item in menu_items:
        menu_item_data = {
            'name': item['name'],
            'price': item['price'],
            'calories': item['calories'],
            'location': address
        }
        data[location].append(menu_item_data)

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
    
    print(f"Menu items added to {file_path} for location: {location}")

 
THRESHOLD_PERCENTAGE = 20

def main():
    all_locations = pd.read_csv("/Users/alyssanguyen/Desktop/IRLE_scraping/scripts/ubereats_mega_combined.csv")
    LOCATIONS = list(all_locations[all_locations['restaurant_name'] == 'Wendy']['restaurant_location'].unique())
    
    total_locations = len(LOCATIONS)
    failed_count = 0

    for location in LOCATIONS[:]:  # Iterate over a copy of the list to allow modification
        driver = setup_driver()
        
        try:
            driver.get("https://www.wendys.com/")
            
            try:
                # Locate the "Accept All" button by its ID and click it
                accept_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                accept_button.click()
                print("Clicked 'Accept All' button successfully!")
                
            except Exception as e:
                print(f"Error clicking 'Accept All': {e}")
            
            address = input_and_search(driver, location)
            if address:
                fixed_address = ", ".join(address.split(", ")[:-1])
                fixed_loc = ", ".join(location.split(", ")[:-3])
                print(f"Extracted Address: {fixed_address}")
                print(f"Fixed Location: {fixed_loc}")

                if fixed_address == fixed_loc: 
                    print(f"Correct location found for {location}, removing from list.")
                    LOCATIONS.remove(location)  # Remove successful location from list
                    click_nth_button(driver, [1, 5], location, address)
                    save_locations_to_json({"Wendy": LOCATIONS}, LOCATIONS_FILE)  # Save updated LOCATIONS
                else:
                    failed_count += 1
            else:
                failed_count += 1
            
            # Check if failure threshold is met
            failure_percentage = (failed_count / total_locations) * 100
            if failure_percentage >= THRESHOLD_PERCENTAGE:
                print(f"Failure threshold reached ({failure_percentage:.2f}%). Stopping execution.")
                break
        
        finally:
            driver.quit()

if __name__ == "__main__":
    clear_existing_data(FILE_PATH)
    main()