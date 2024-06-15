import logging
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

FILE_PATH = "burger_king_missing_nonca_rnd1.csv"
CHROMEDRIVER_PATH = "/Users/alyssanguyen/Downloads/chromedriver-mac-arm64/chromedriver"

def setup_driver():
    # WebDriver options
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    service = Service(executable_path=CHROMEDRIVER_PATH)
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

def main():
    clear_existing_data(FILE_PATH)

    burger_king_locations = ['3227 Poplar Ave, Memphis, TN, 38111, US',
  '659 Government St, Mobile, AL, 36602, US',
  '5068 Old National Highway, College Park, GA, 30349, US',
  '2116 Whitesburg Drive, Huntsville, AL, 35801, US',
  '1131 Lexington Road, Georgetown, KY, 40324, US',
  '4200 Saron Road, Lexington, KY, 40515, US',
  '2806 North Broadway, Knoxville, TN, 37917, US',
  '2119 East 23rd Street, Chattanooga, TN, 37404, US',
  '1901 Route 286, Pittsburgh, PA, 15239, US',
  '451 W. New Circle Road, Lexington, KY, 40511, US',
  '6337 Crawfordsville Rd, Speedway, IN, 46224, US',
  '1524 6th Avenue S, Birmingham, AL, 35233, US',
  '308 Jordan Lane, Huntsville, AL, 35805, US',
  '6971 West 38th Street, Indianapolis, IN, 46214, US',
  '2605 Jacksboro Hwy, River Oaks, TX, 76114, US',
  '2700 University Blvd, Birmingham, AL, 35233, US',
  '1330 Poplar Avenue, Memphis, TN, 38104, US',
  '3875 Airport Boulevard, Mobile, AL, 36609, US',
  '2773 Evans Mill Rd, Lithonia, GA, 30058, US',
  '1004 North Memorial Parkway, Huntsville, AL, 35801, US',
  '2230 Salem Road, Conyers, GA, 30013, US',
  '730 Lane Allen Rd, Lexington, KY, 40504, US',
  '3941 Crosstown Expressway, Corpus Christi, TX, 78416, US']

    for idx, location in enumerate(burger_king_locations):
        driver = setup_driver()
        try:
            driver.get("https://www.bk.com/store-locator/service-mode")

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
