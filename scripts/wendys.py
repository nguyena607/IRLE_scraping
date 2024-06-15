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
from WENDYS_NONCA_LOCATIONS import LOCATIONS

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


FILE_PATH = "wendy_nonca_pt2.jsonl"
LOCATIONS = LOCATIONS
# Use your own executable_path (download from https://chromedriver.chromium.org/).
CHROMEDRIVER_PATH = "/Users/alyssanguyen/Downloads/chromedriver-mac-arm64/chromedriver"

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
        
        button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.order-button"))
    )
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        
        driver.execute_script("arguments[0].click();", button)
        print("Clicked on the button.")

    except Exception as e:
        print("An error occurred:", str(e))

def click_nth_button(driver, indices, location):
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
                
                scrape(driver, location)
                print("scraped menu")

                driver.back()
                buttons = WebDriverWait(driver, 10).until(
                    EC.visibility_of_all_elements_located((By.XPATH, "//button[@type='button' and @data-testid='category-item-button']"))
                )
            else:
                print(f"Index {index} is out of range. Skipping...")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def scrape(driver, location): 
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
    add_menu_items_to_json(menu_items, location, FILE_PATH)

def add_menu_items_to_json(menu_items, location, file_path):
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
            'location': location
        }
        data[location].append(menu_item_data)

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
    
    print(f"Menu items added to {file_path} for location: {location}")

def main():
    for location in LOCATIONS: 
        driver = setup_driver()
        try:
            driver.get("https://www.wendys.com/")
            input_and_search(driver, location)
            click_nth_button(driver, [1,4], location)
        finally:
                    driver.quit() 

if __name__ == "__main__":
    clear_existing_data(FILE_PATH)
    main()