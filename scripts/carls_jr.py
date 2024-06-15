import csv
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
import re
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains


# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FILE_PATH = "carlsjr_missing_rnd1.csv"
# Use your own executable_path (download from https://chromedriver.chromium.org/).
CHROMEDRIVER_PATH = "/Users/alyssanguyen/Downloads/chromedriver-mac-arm64/chromedriver"
#CHROMEDRIVER_PATH = "/Users/sakshikolli/Downloads/chromedriver-mac-x64/chromedriver"

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
    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def click_next_button(driver):
    try:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.swiper-button-next"))
        )
        driver.execute_script("arguments[0].click();", next_button)
        print("Clicked on the next button with the SVG icon using JavaScript.")
        return True
    except Exception as e:
        print(f"Failed to click on the next button with the SVG icon: {e}")
        return False

def click_charbroiled_burgers(driver, retries=3):
    for attempt in range(retries):
        try:
            # Try to click on the 'Charbroiled Burgers' button
            search_box4 = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, './/button[contains(text(),"Charbroiled Burgers")]'))
            )
            search_box4.click()
            print("Clicked on 'Charbroiled Burgers'.")
            return True
        except Exception as e:
            print(f"Attempt {attempt+1}: Failed to find 'Charbroiled Burgers' button, clicking on the next button instead.")
            # Click the next button with the SVG icon
            if not click_next_button(driver):
                continue
            time.sleep(3)
    print("Failed to click on 'Charbroiled Burgers' after multiple attempts.")
    return False

clear_existing_data(FILE_PATH)

carls_jr_locations = [
    '1001 Veterans Blvd, Redwood City, CA, 94063, US',
    '3131 Crow Canyon Pl, San Ramon, CA, 94583, US',
    '16101 N. Harbor Blvd, Fountain Valley, CA, 92708, US',
    '16565 Sierra Lakes Pkwy, Fontana, CA, 92336, US',
    '939 W. Charter Way, Stockton, CA, 95206, US',
    '3370 La Sierra Ave, Riverside, CA, 92503, US',
    '14454 Valley Blvd, Fontana, CA, 92335, US',
    '1670 Pacific Coast Highway, Long Beach, CA, 90810, US',
    '4595 Century Boulevard, Pittsburg, CA, 94565, US',
    '2280 Arden Way, Sacramento, CA, 95825, US',
    '7432 Pacific Ave, Stockton, CA, 95207, US',
    '222 N. Euclid Ave, Fullerton, CA, 92832, US',
    '2400 White Ln, Bakersfield, CA, 93304, US',
    '1259 W Carson St, Torrance, CA, 90502, US',
    '46637 Mission Boulevard, Fremont, CA, 94539, US',
    '2110 W 7Th St, Los Angeles, CA, 90057, US',
    '1095 Oakland Road, San Jose, CA, 95112, US',
    '1588 N 1st St, Fresno, CA, 93703, US',
    '5670 Thornton Avenue, Newark, CA, 94560',
    '2903 Burgener Blvd, San Diego, CA, 92110, US'
]

for idx, location in enumerate(carls_jr_locations):
    driver = setup_driver()  # Create a new driver instance for each location
    
    try:
        driver.get('https://order.carlsjr.com/?utm_medium=cpc&utm_source=google&utm_campaign=carls-jr_n_807-sf-ca_ggl_sem_branded_general_eng&utm_content=carls%20jr&utm_term=carl%27s%20jr&device=c&gad_source=1&gclid=Cj0KCQjwqpSwBhClARIsADlZ_TmNvYfPIiDHUv6GbAPKlm0pXEJEe1deauPhqf90B9d8rr9E9CkG_LUaAjz6EALw_wcB&gclsrc=aw.ds')
        
        # Click on popup screen
        continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        continue_button.click()
        print("Clicked on 'Continue to Site' button successfully.")
        time.sleep(3)

        # Type in the address
        search_box = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/ion-app/ion-router-outlet/app-custom-location-finder/ion-content/div/main/div/div[1]/header/form/div/app-custom-location-search/div/div[2]/input"))
        )
        search_box.clear()
        search_box.click()
        search_box.send_keys(location)
        print(f"Typed in address: {location}")
        time.sleep(3)
        
        # Click on the first suggested address
        li_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//li[@class='ng-star-inserted']//button"))
        )
        li_element.click()
        print("Clicked on the suggested address successfully.")
        time.sleep(3)
        
        # Click on the 'Start Order' button
        button = driver.find_element(By.XPATH, "//button[@class='btn--primary' and contains(text(), 'Start Order')]")
        ActionChains(driver).move_to_element(button).click().perform()
        print("Clicked on 'Start Order' button successfully using ActionChains.")
        
        time.sleep(4)

        # Extract actual address from <a> tag
        address_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.c-menu__order-details__location"))
        )
    
        # Extract the text content of the address element
        actual_address = address_element.text
        
        print(f"Menu Address: {actual_address}")
    
        # Try to click on the 'Charbroiled Burgers' button or click the next button if it fails
        if not click_charbroiled_burgers(driver):
            print("Skipping this location due to failure in finding the 'Charbroiled Burgers' button.")
            continue
             
        # Extract data and store in CSV
        regex_pattern = 'class="product-card__name">(.*?)<\/div>.*?class="product-card__cost-calories">\$([\d\.]+).*?<\/span><!---->\s([\d,]*)'
        string_burgers = driver.page_source
        result_burgers = re.findall(regex_pattern, string_burgers)
            
        data = pd.DataFrame(result_burgers, columns=['menu_item', 'menu_item_price', 'menu_item_calories'])
        data['restaurant_address'] = location
        data['inputted_address'] = actual_address
            
        if idx == 0:
            data.to_csv(FILE_PATH, index=False)
        else:
            data1 = pd.read_csv(FILE_PATH)
            df = pd.concat([data1, data])
            df.to_csv(FILE_PATH, index=False)
    
    except Exception as e:
        logger.error(f"Error processing location '{location}': {e}")
    
    finally:
        driver.quit()  # Quit the driver instance after processing each location

print("Script execution completed.")