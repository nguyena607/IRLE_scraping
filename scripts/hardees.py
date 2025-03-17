import csv
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import pandas as pd


# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FILE_PATH = "raw_prices_hardees_nonca_10102024_test.csv"
CHROMEDRIVER_PATH = "/Users/alyssanguyen/Downloads/chromedriver-mac-arm64 2/chromedriver"


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
    # chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

def navigate_to_charbroiled_burgers(driver):
    # Try a maximum number of swiper button clicks (in case "Charbroiled Burgers" is far in the carousel)
    max_swipes = 3
    for _ in range(max_swipes):
        try:
            # Attempt to find the "Charbroiled Burgers" button
            search_box4 = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, './/button[contains(text(),"Charbroiled Burgers")]'))
            )
            search_box4.click()
            print("Successfully clicked on 'Charbroiled Burgers' button")
            return True
        except Exception as e:
            print(f"'Charbroiled Burgers' button not found. Exception: {e}")

            # If the button wasn't found, click the swiper "next" button
            try:
                swiper_next = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, './/div[contains(@class,"swiper-button-next")]'))
                )
                swiper_next.click()
                time.sleep(2)  # Allow time for the swiper to move
                print("Clicked on swiper next button, trying again...")
            except Exception as e:
                print(f"Failed to click on the swiper next button. Exception: {e}")
                return False
    
    # If we exit the loop, it means we couldn't find the button after swiping
    print("Could not find 'Charbroiled Burgers' button after maximum swipes.")
    return False



# Clear existing data file if necessary
#clear_existing_data(FILE_PATH)

carls_jr = '/Users/alyssanguyen/Desktop/IRLE_scraping/csv_files/processed_prices_hardees_non_ca_03292024.csv'
carls_jr_ = pd.read_csv(carls_jr)
locations = carls_jr_['restaurant_location'].unique()
print(len(locations))
# curr_carls = pd.read_csv("raw_prices_carlsjr_ca_09252024.csv")
# curr_locs = curr_carls['restaurant_address'].unique()

# print("num og locs:", len(locations))
# print("num curr locs:", len(curr_locs))

for idx, location in enumerate(locations):
    print("curr location:", location)
    driver = setup_driver()
    driver.get('https://order.hardees.com')
    
    # Accept cookie banner
    accept_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
    )
    accept_button.click()
    print("Accepted button")

    time.sleep(3)

    # Search for location
    search_box = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/ion-app/ion-router-outlet/app-custom-location-finder/ion-content/div/main/div/div[1]/header/form/div/app-custom-location-search/div/div[2]/input"))
    )
    search_box.clear()
    search_box.click()
    search_box.send_keys(location)

    time.sleep(3)

    # Select location from the dropdown
    li_element = driver.find_element(By.XPATH, '//li[contains(@class, "ng-star-inserted")]//button')
    li_element.click()
    time.sleep(3)
    
    try:
        # Wait and scroll to the 'Order Now' button
        print("Waiting for the button to be present...")
        button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//button[contains(@class, "btn--primary ng-star-inserted")]'))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        driver.execute_script("arguments[0].click();", button)
        time.sleep(3)

    except Exception as e:
        print(f"An error occurred: {e}")

    if navigate_to_charbroiled_burgers(driver): 
        print("adding data:")
        # Extract menu items, prices, and calories using regex
        regex_pattern = 'class="product-card__name">(.*?)<\/div>.*?class="product-card__cost-calories">\$([\d\.]+).*?<\/span><!---->\s([\d,]*)'
        string_burgers = driver.page_source
        result_burgers = re.findall(regex_pattern, string_burgers)

        # Create DataFrame from the results
        data = pd.DataFrame(result_burgers, columns=['menu_item', 'menu_item_price', 'menu_item_calories'])
        data['restaurant_address'] = location
        
        # Append to CSV, without reloading the entire file
        if idx == 0:
            # Write header during the first iteration
            data.to_csv(FILE_PATH, mode='w', index=False)
        else:
            # Append without header for subsequent iterations
            data.to_csv(FILE_PATH, mode='a', header=False, index=False)

        # Close the driver for the current location
        driver.quit()
    else: 
         driver.quit()
