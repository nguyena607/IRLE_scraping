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

FILE_PATH = "burger_king_missing_rnd1.csv"
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

    burger_king_locations = ['6351 Hembree Lane, Windsor, CA, 95492, US',
  '4424 Broadway, Oakland, CA, 94611, US',
  '972 El Camino Real, South San Francisco, CA, 94080, US',
#   '503 East Foothill, Rialto, CA, 92376, US',
#   '2817 South El Camino Real, San Mateo, CA, 94403, US',
#   '5154 Moorpark Ave, San Jose, CA, 95129, US',
#   '20950 Figueroa Street, Carson, CA, 90745, US',
#   '35 Powell Street, San Francisco, CA, 94102, US',
#   '7201 Fair Oaks Boulevard, Carmichael, CA, 95608, US',
#   '1278 El Camino Real, San Bruno, CA, 94066, US',
#   '1320 Industrial Park Avenue, Redlands, CA, 92374, US',
#   '4087 West Clinton Avenue, Fresno, CA, 93722, US',
#   '773 North Mathilda Avenue, Sunnyvale, CA, 94085, US',
#   '815 Highland Avenue, National City, CA, 91950, US',
#   '175 West Calaveras Boulevard, Milpitas, CA, 95035, US',
#   '1255 North Blackstone Street, Tulare, CA, 93274, US',
#   '1949 Columbus Avenue, Bakersfield, CA, 93305, US',
#   '7200 Bancroft Road, Oakland, CA, 94605, US',
#   '2855 North Main Street, Walnut Creek, CA, 94597, US',
#   '1915 Arden Way, Sacramento, CA, 95815, US',
#   '1265 Third Avenue, Chula Vista, CA, 91911, US',
#   '1153 North H Street, Lompoc, CA, 93436, US',
#   '899 East H Street, Chula Vista, CA, 91910, US',
#   '3750 El Camino Real, Santa Clara, CA, 95051, US',
#   '2001 - 41st Avenue, Capitola, CA, 95010, US',
#   '619 West Charter Way, Stockton, CA, 95206, US',
#   '814 N Brookhurst St, Anaheim, CA, 92801, US',
#   '2101 Sylvan Avenue, Modesto, CA, 95355, US',
#   '34943, Newark, CA, 94560, US',
#   '7 Muir Road, Martinez, CA, 94553, US',
#   '3747 Rosecrans Street, San Diego, CA, 92110, US',
#   '1329 South Harbor Boulevard, Fullerton, CA, 92832, US',
#   '5120 Olive Drive, Bakersfield, CA, 93308, US',
#   '205 East Redlands, San Bernardino, CA, 92408, US',
#   '127 West 4th Street, Long Beach, CA, 90802, US',
#   '2050 South Broadway, Santa Maria, CA, 93454, US',
#   '2102 Middlefield Road, Redwood City, CA, 94063, US',
#   '1305 N Bascom Ave, San Jose, CA, 95128, US',
#   '6835 Valley Way, Riverside, CA, 92509, US',
#   '6217 Niles Street, Bakersfield, CA, 93306, US',
#   '2714 El Centro Road, Sacramento, CA, 95833, US',
#   '2001 North, Oxnard, CA, 93036, US',
#   '763 Ikea Ct #120, West Sacramento, CA, 95605, US',
#   '2757 Castro Valley Boulevard, Castro Valley, CA, 94546, US',
#   '3235 West Little League Drive, San Bernardino, CA, 92407, US',
#   '1701 FILLMORE ST, San Francisco, CA, 94115, US',
#   '4571 North Pershing Avenue, Stockton, CA, 95207, US',
#   '936 Blossom Hill Road, San Jose, CA, 95123, US',
#   '7225 Greenhaven Drive, Sacramento, CA, 95831, US',
#   '2532 Channing Avenue, San Jose, CA, 95131, US',
#   '8034 Greenback Lane, Citrus Heights, CA, 95610, US',
#   '1361 West Foothill Boulevard, Rialto, CA, 92376, US',
#   '180 Niblick Rd, Paso Robles, CA, 93446, US',
#   '24530 Lyons Avenue, Newhall, CA, 91321, US',
#   '97 Bonita Road, Chula Vista, CA, 91910, US'
]

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
            search_box.send_keys(Keys.ENTER)

            # Move to address suggestion element
            ActionChains(driver).move_to_element(search_box).move_by_offset(0, -5).perform()

            # Wait for address suggestion to be clickable
            element = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@data-testid='address-suggestion']"))
            )
            element.click()

            # Wait for the first store card to be clickable
            store_card = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "(//div[@data-testid='store-card'])[1]"))
            )
            store_card.click()

            # Wait for order button to be clickable
            order_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='store-modal-order-here']"))
            )
            order_button.click()

            time.sleep(3)


            # Click on specific buttons with a delay between each click
            click_nth_button(driver, [3, 5], location)

        except Exception as e:
            logger.error(f"An error occurred while processing location {location}: {str(e)}")

        finally:
            # Quit the driver after each location
            driver.quit()

if __name__ == "__main__":
    main()
