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

FILE_PATH = "raw_prices_carlsjr_non_ca_03302024.csv"
# Use your own executable_path (download from https://chromedriver.chromium.org/).
#CHROMEDRIVER_PATH = "/Users/alyssanguyen/Downloads/chromedriver-mac-arm64/chromedriver"
CHROMEDRIVER_PATH = "/Users/sakshikolli/Downloads/chromedriver-mac-x64/chromedriver"

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

carls_jr_locations = [
    '1700 W State St, Boise, ID, 83702, US',
    '493 N Milwaukee St, Boise, ID, 83704, US',
    '4994 E 41St, Tulsa, OK, 74135, US',
    '1039 W University Ave, Georgetown, TX, 78628, US',
    '925 w Antelope Drive, Layton, UT, 84041, US',
    '2118 W 1700 S SYRACUSE, UT 84075, US',
    '582 N MAIN STREET CLEARFIELD, UT 84015, US',
    '1155 W RIVERDALE RD UNIT A RIVERDALE, UT 84405',
    '5722 S 49TH WEST AVE TULSA, OK 74107'
]

driver = setup_driver()
for idx, location in enumerate(carls_jr_locations):
    driver.get('https://order.carlsjr.com/?utm_medium=cpc&utm_source=google&utm_campaign=carls-jr_n_807-sf-ca_ggl_sem_branded_general_eng&utm_content=carls%20jr&utm_term=carl%27s%20jr&device=c&gad_source=1&gclid=Cj0KCQjwqpSwBhClARIsADlZ_TmNvYfPIiDHUv6GbAPKlm0pXEJEe1deauPhqf90B9d8rr9E9CkG_LUaAjz6EALw_wcB&gclsrc=aw.ds')

    search_box = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/ion-app/ion-router-outlet/app-custom-location-finder/ion-content/div/main/div/div[1]/header/form/div/app-custom-location-search/div/div[2]/input"))
    )
    search_box.clear()
    search_box.click()
    search_box.send_keys(location)

    ActionChains(driver).move_to_element(search_box).move_by_offset(0, -5).perform()

    search_box2 = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/app-root/ion-app/ion-router-outlet/app-custom-location-finder/ion-content/div/main/div/div[1]/header/form/div/app-custom-location-search/div/div[3]/ul/li[1]/button'))
    )
    search_box2.click()
    time.sleep(3)

    search_box3 = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/app-root/ion-app/ion-router-outlet/app-custom-location-finder/ion-content/div/main/div/div[1]/div/div[2]/swiper/div/div[1]/app-custom-location-card[1]/div/div/div[3]/div/button')))
    search_box3.click()
    time.sleep(5)

    search_box4 = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, './/button[contains(text(),"Charbroiled Burgers")]')))
    search_box4.click()
    time.sleep(3)

    regex_pattern = 'class="product-card__name">(.*?)<\/div>.*?class="product-card__cost-calories">\$([\d\.]+).*?<\/span><!---->\s([\d,]*)'

    string_burgers = driver.page_source
    result_burgers = re.findall(regex_pattern, string_burgers)

    data = pd.DataFrame(result_burgers, columns = ['menu_item', 'menu_item_price', 'menu_item_calories'])
    data['restaurant_address'] = location
    if idx == 0:
        data.to_csv(FILE_PATH, index=False)
    else:
        data1 = pd.read_csv(FILE_PATH)
        df = pd.concat([data1, data])
        df.to_csv(FILE_PATH, index = False)


