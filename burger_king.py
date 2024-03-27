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
import re
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from CA_LOCATIONS import LOCATIONS
from RESTAURANTS import RESTAURANTS


# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCATIONS = LOCATIONS
RESTAURANTS = RESTAURANTS
FILE_PATH = "burger_king_prices.jsonl"
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


def web_scraping_bk():
    driver = setup_driver()
    location = "3300 Capitol Ave, Fremont, CA 94538"
    driver.get("https://www.bk.com/store-locator/service-mode")

    search_box = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Your Address']"))
    )
    search_box.clear()
    search_box.click()
    search_box.send_keys(location)

    ActionChains(driver).move_to_element(search_box).move_by_offset(0, -5).perform()

    search_box2 = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div/div/div/div[2]/div[1]/div/div/div/div[1]/div/div[2]/div/div[2]/div/div/div[1]/div/div/div[2]'))
    )
    search_box2.click()
    time.sleep(2)

    search_box3 = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div/div/div/div[2]/div[1]/div/div/div/div[3]/div/div[2]/div[1]/div/div/div/div/div[1]/div/div/div/div[1]"))
    )
    search_box3.click()
    time.sleep(2)

    search_box4 = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div/div/div/div[2]/div[1]/div/div/div/div[3]/div/div[2]/div[1]/div/div/div/div/div[1]/div/div[2]/div/div/div[3]/button"))
    )
    search_box4.click()
    time.sleep(3)

    search_box5 = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div/div/div/div[2]/div[1]/div/div/div/div/div/div/div[2]/div/div[3]')))
    search_box5.click()
    time.sleep(3)

    string = driver.page_source
    regex_pattern = r'css-146c3p1 r-17l9mgj r-95zftm r-1i10wst r-oxtfae r-rjixqe r-p1pxzi r-11wrixw r-61z16t r-1mnahxq r-q4m81j">(.*?)<.*?\$(.*?)<.*?>([\d,\s]+)\sCal'
    result = re.findall(regex_pattern, string)
    out_file = open(FILE_PATH, "a")
    json.dump(result, out_file, indent = 6)
    out_file.close()


web_scraping_bk()
