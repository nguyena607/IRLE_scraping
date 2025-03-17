import logging
import pandas as pd
import os
import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FILE_PATH = "bk_wave4_test.csv"
CHROMEDRIVER_PATH = "/Users/alyssanguyen/Downloads/chromedriver-mac-arm64-133/chromedriver"

def setup_driver():
    # WebDriver options
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    service = Service(executable_path=CHROMEDRIVER_PATH)
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def clear_existing_data(file_path):
    try:
        os.remove(file_path)
        logger.info(f"Cleared existing data in {file_path}.")
    except FileNotFoundError:
        logger.info(f"No existing data file found at {file_path}. Starting fresh.")

def scrape(driver, location):
    wait = WebDriverWait(driver, 10)
    try:
        location_div = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//div[@class='css-146c3p1 r-1iln25a r-17l9mgj r-13awgt0 r-anxyqk r-ubezar r-oxtfae r-135wba7 r-1kb76zh r-e73std r-1udh08x r-1m04atk r-1hvjb8t r-1udbk01 r-3s2u2q']")
        ))
        scraped_location = location_div.text.strip()

        # Find all elements with the specified class
        product_items = wait.until(EC.visibility_of_all_elements_located(
            (By.XPATH, "//div[contains(@class, 'css-175oi2r r-1awozwy r-shm4j r-tabonr r-1ypo0qm r-1777fci')]")
        ))
    except Exception as e:
        logger.error(f"An error occurred while finding product items: {e}")
        return []

    menu_items = []
    
    for product in product_items:
        try:
            item_name = product.find_element(By.XPATH, ".//h2[contains(@class, 'css-146c3p1')]").text.strip()
            price = product.find_element(By.XPATH, ".//div[contains(@class, 'css-146c3p1') and contains(text(), '$')]").text.strip()
            calories = product.find_element(By.XPATH, ".//div[contains(@class, 'css-146c3p1') and contains(text(), 'Cal')]").text.strip()
            
            item_info = {
                'menu_item': item_name,
                'menu_item_price': price,
                'menu_item_calories': calories,
                'inputted_address' : location
            }
            menu_items.append(item_info)
        except Exception as e:
            logger.error(f"An error occurred while scraping product details: {e}")

    add_menu_items_to_csv(menu_items, scraped_location, FILE_PATH)

def add_menu_items_to_csv(menu_items, location, file_path):
    file_exists = os.path.isfile(file_path)
    with open(file_path, 'a', newline='') as csvfile:
        fieldnames = ['menu_item', 'menu_item_price', 'menu_item_calories', 'input_address', 'restaurant_address']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for item in menu_items:
            menu_item_data = {
                'menu_item': item['menu_item'],
                'menu_item_price': item['menu_item_price'],
                'menu_item_calories': item['menu_item_calories'],
                'input_address' : item['inputted_address'],
                'restaurant_address': location
            }
            writer.writerow(menu_item_data)
    
    logger.info(f"Menu items added to {file_path} for location: {location}")

def click_nth_button(driver, indices, location):
    for index in indices:
        retry_count = 3
        while retry_count > 0:
            try:
                # Find all buttons
                buttons = WebDriverWait(driver, 10).until(
                    EC.visibility_of_all_elements_located((By.XPATH, "//div[@data-testid='picture-img']"))
                )

                if 0 <= index < len(buttons):
                    button = buttons[index]

                    driver.execute_script("arguments[0].scrollIntoView(true);", button)

                    # Click on the div
                    driver.execute_script("arguments[0].click();", button)
                    logger.info("Clicked on the div.")

                    # Perform additional actions after clicking
                    scrape(driver, location)
                    logger.info("Scraped menu.")

                    driver.back()  # Navigate back to previous page or perform other navigation

                    retry_count = 0  # exit loop
                else:
                    logger.warning(f"Index {index} is out of range. Skipping...")
                    break

            except Exception as e:
                logger.error(f"An error occurred: {str(e)}")
                retry_count -= 1
                if retry_count == 0:
                    logger.error(f"Failed to process after retries. Skipping index {index}.")

all_locations = pd.read_csv("/Users/alyssanguyen/Desktop/IRLE_scraping/scripts/ubereats_mega_combined.csv")
LOCATIONS = list(all_locations[all_locations['restaurant_name'] == 'Burger King']['restaurant_location'].unique())
    
def main():
    clear_existing_data(FILE_PATH)
    for location in LOCATIONS:
        driver = setup_driver()
        try:
            driver.get("https://www.bk.com/store-locator/service-mode")
            
            time.sleep(3)


            try:
                # Locate the close button for the cookie banner
                close_button = driver.find_element(By.CLASS_NAME, "onetrust-close-btn-handler")
                
                # Click on the close button to dismiss the banner
                close_button.click()
            except NoSuchElementException:
                print("Cookie consent close button not found.")

            # Wait for search box to be clickable and interactable
            search_box = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Your Address']"))
            )
            search_box.clear()
            search_box.click()
            search_box.send_keys(location)

            time.sleep(2)


            # Wait for address suggestion to be clickable
            element = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@data-testid='address-suggestion']"))
            )
            element.click()

            time.sleep(2)


            # Wait for the first store card to be clickable
            store_card = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "(//div[@data-testid='store-card'])[1]"))
            )
            store_card.click()

            time.sleep(2)

            # Wait for order button to be clickable
            order_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='store-modal-order-here']"))
            )
            order_button.click()

            time.sleep(6)


            # Click on specific buttons with a delay between each click
            click_nth_button(driver, [3, 5], location)

        except Exception as e:
            logger.error(f"An error occurred while processing location {location}: {str(e)}")

        finally:
            # Quit the driver after each location
            driver.quit()

if __name__ == "__main__":
    main()
