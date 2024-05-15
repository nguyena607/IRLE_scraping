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

FILE_PATH = "raw_prices_burgerking_ca_05152024.csv"
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

burger_king_locations = [
    '1541 East 12th Street, Oakland, CA, 94606, US',
    '580 Hegenberger Road, Oakland, CA, 94621, US',
    '5701 Christie Avenue, Emeryville, CA, 94608, US',
    '4200 East 14th Street, Oakland, CA, 94601, US',
    '849 University Avenue, Berkeley, CA, 94710, US',
    '3996 Washington Boulevard, Fremont, CA, 94538, US',
    '1801 Decoto Road, Union City, CA, 94587, US',
    '46700 Mission Boulevard, Fremont, CA, 94539, US',
    '31361 Alavarado Niles Road, Union City, CA, 94587, US',
    '29671 Mission Blvd., Hayward, CA, 94544, US',
    '950 West A Street, Hayward, CA, 94541, US',
    '2757, Castro Valley, CA, 94546, US',
    '15050 E. 14th Street, San Leandro, CA, 94578, US',
    '26251 Hesperian Boulevard, Hayward, CA, 94545, US',
    '3399 Port Chicago Hwy, Concord, CA, 94520, US',
    '4320 Clayton Road, Concord, CA, 94521, US',
    '5400 Ygnacio Valley Road, Concord, CA, 94521, US',
    "4610 East King's Canyon Rd., Fresno, CA, 93702, US",
    '2410 North Cedar, Fresno, CA, 93703, US',
    '575 North Clovis Avenue, Fresno, CA, 93727, US',
    '3405 Union Ave, Bakersfield, CA, 93305, US',
    '2508 White Lane, Bakersfield, CA, 93304, US',
    '8200 Stockdale Hwy, Bakersfield, CA, 93309, US',
    '700 East Cesar E Chavez Avenue, Los Angeles, CA, 90012, US',
    '1501 West 6th Street, Los Angeles, CA, 90017, US',
    '1830 West 8th Street, Los Angeles, CA, 90057, US',
    '1540 North Eastern Avenue, Los Angeles, CA, 90063, US',
    '1845 S. Vermont Ave., Los Angeles, CA, 90006, US',
    '2600, Long Beach, CA, 90806, US',
    '2955 North Bellflower Boulevard, Long Beach, CA, 90815, US',
    '865 West Sepulveda Boulevard, Torrance, CA, 90502, US',
    '5540 Cherry Avenue, Long Beach, CA, 90805, US',
    '2008 Glenoaks Boulevard, San Fernando, CA, 91340, US',
    '20838 Devonshire St., Chatsworth, CA, 91311, US',
    '19662 Nordhoff Street, Northridge, CA, 91324, US',
    '12781 Van Nuys Boulevard, Pacoima, CA, 91331, US',
    '9025 Balboa, Northridge, CA, 91325, US',
    '969 East Francisco Blvd., San Rafael, CA, 94901, US',
    '220 Alameda Del Prado, Novato, CA, 94949, US',
    '1300 Mcdonald Avenue, Richmond, CA, 94801, US',
    '12999 San Pablo Avenue, Richmond, CA, 94805, US',
    '1571 Fitzgerald Drive, Pinole, CA, 94564, US',
    '5304 Old Redwood Highway, Petaluma, CA, 94954, US',
    '909 South Main Street, Salinas, CA, 93901, US',
    '41 S. Sanborn Road, Salinas, CA, 93905, US',
    '701 North Main Street, Santa Ana, CA, 92701, US',
    '2100 East 17th Street, Santa Ana, CA, 92701, US',
    '200 North Harbor Boulevard, Santa Ana, CA, 92703, US',
    '2850 South Bristol Street, Santa Ana, CA, 92704, US',
    '601 East Dyer Road, Santa Ana, CA, 92705, US',
    '14601 Red Hill Avenue, Tustin, CA, 92780, US',
    '1201 South, Anaheim, CA, 92805, US',
    '2210 E Lincoln Ave, Anaheim, CA, 92806, US',
    '510 South Euclid Street, Anaheim, CA, 92802, US',
    '2403 East Chapman Avenue, Fullerton, CA, 92831, US',
    '2751 W. Orangethorpe Blvd, Fullerton, CA, 92833, US',
    '5121 Foothills Boulevard, Roseville, CA, 95747, US',
    '1300 East, Roseville, CA, 95661, US',
    '5869 Antelope Rd, Sacramento, CA, 95621, US',
    '7760 Sunrise Blvd, Citrus Heights, CA, 95610, US',
    '4960 Auburn Blvd., Sacramento, CA, 95841, US',
    '115, Lincoln, CA, 95648, US',
    '5790 VAN BUREN BOULEVARD, Riverside, CA, 92503, US',
    '3630 Tyler Street, Riverside, CA, 92505, US',
    '10055 Cedar Avenue, Bloomington, CA, 92316, US',
    '24800 Sunnymead Blvd, Moreno Valley, CA, 92553, US',
    '1688 North, Perris, CA, 92571, US',
    '2167 University Avenue, Riverside, CA, 92507, US',
    '23125 Hemlock Avenue, Moreno Valley, CA, 92557, US',
    '2020 West Florida Avenue, Hemet, CA, 92545, US',
    '5610 Freeport Boulevard, Sacramento, CA, 95822, US',
    '9181 East Stockton Boulevard, Elk Grove, CA, 95624, US',
    '7218 Stockton Boulevard, Sacramento, CA, 95823, US',
    '487 West Highland, San Bernardino, CA, 92405, US',
    '12077 Palmdale Road, Victorville, CA, 92392, US',
    '9760 Sheep Creek Road, Phelan, CA, 92371, US',
    '1210 11th Ave, San Diego, CA, 92101, US',
    '1220 South 28th Street, San Diego, CA, 92113, US',
    '3676 Market Street, San Diego, CA, 92102, US',
    '599 Broadway, Chula Vista, CA, 91910, US',
    '244 West Mission Avenue, Escondido, CA, 92025, US',
    '1677 S. Centre City Parkway, Escondido, CA, 92025, US',
    '819 Van Ness Avenue, San Francisco, CA, 94109, US',
    '3900 Geary Boulevard, San Francisco, CA, 94118, US',
    '1690 Valencia Street, San Francisco, CA, 94110, US',
    '245 Bayshore Blvd., San Francisco, CA, 94124, US',
    '111, Colma, CA, 94014, US',
    '898 John Daly Boulevard, Daly City, CA, 94015, US',
    '702 North Wilson Way, Stockton, CA, 95205, US',
    '1358 Madonna Road, San Luis Obispo, CA, 93405, US',
    '1773 W Grand Ave, Grover Beach, CA, 93433, US',
    '8304 El Camino Real, Atascadero, CA, 93422, US',
    '1030 Mclaughlin Ave., San Jose, CA, 95122, US',
    '2390 Almaden Road, San Jose, CA, 95125, US',
    '1181 Old Oakland Road, San Jose, CA, 95112, US',
    '2170 Monterey Road, San Jose, CA, 95112, US',
    '329 North Capital Avenue, San Jose, CA, 95133, US',
    '385 South Kiely, San Jose, CA, 95129, US',
    '2015 Mission Street, Santa Cruz, CA, 95060, US',
    '1302 Soquel Avenue, Santa Cruz, CA, 95062, US',
    '3606 Sonoma Boulevard, Vallejo, CA, 94590, US',
    '844 Willow Avenue, Hercules, CA, 94547, US',
    '190 Pittman Road, Suisun City, CA, 94534, US',
    '1260 Anderson Drive, Suisun City, CA, 94585, US',
    '2005 Huntington Drive, Fairfield, CA, 94533, US',
    '56 Mission Circle, Santa Rosa, CA, 95409, US',
    '741 Stony Point Road, SANTA ROSA, CA, 95407-6864, US',
    '2542 Guerneville Road, Santa Rosa, CA, 95401, US',
    '5020 Redwood Drive, Rohnert Park, CA, 94928, US',
    '6125 Commerce Boulevard, Rohnert Park, CA, 94928, US',
    '1042 North Carpenter Road, Modesto, CA, 95351, US',
    '2320 McHenry Ave, Modesto, CA, 95350, US',
    '1009 N Ben Maddox Way, Visalia, CA, 93292, US',
    '500 South De Maree, Visalia, CA, 93277, US',
    '6603 Betty Dr, Visalia, CA, 93291, US',
    '2500 S. Ventura Road, Oxnard, CA, 93033, US',
    '5950 Telegraph Road, Ventura, CA, 93003, US',
    '181 South Arniell Road, Camarillo, CA, 93010, US',
    '21 West Main Street, Ventura, CA, 93001, US'
]

driver = setup_driver()
for idx, location in enumerate(burger_king_locations):
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
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div/div/div/div[2]/div[1]/div/div/div/div[3]/div/div[2]/div[1]/div/div/div/div/div[1]/div/div/div[2]/div/button"))
    )
    search_box4.click()
    time.sleep(3)

    search_box5 = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div/div/div/div[2]/div[1]/div/div/div/div/div/div/div[2]/div/div[3]/a/div[2]/h2')))
    search_box5.click()
    time.sleep(3)


    regex_pattern = r'css-146c3p1 r-17l9mgj r-95zftm r-1i10wst r-oxtfae r-rjixqe r-p1pxzi r-11wrixw r-61z16t r-1mnahxq r-q4m81j">(.*?)<.*?\$(.*?)<.*?>([\d,\s]+)\sCal'

    string_burgers = driver.page_source
    result_burgers = re.findall(regex_pattern, string_burgers)

    search_box6 = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div/div/div/div[2]/div[1]/div/div/div[1]/div[1]/div/div[5]/h3")))
    search_box6.click()
    time.sleep(3)

    string_sides = driver.page_source
    result_sides = re.findall(regex_pattern, string_sides)

    combined = result_burgers + result_sides
    data = pd.DataFrame(combined, columns = ['menu_item', 'menu_item_price', 'menu_item_calories'])
    data['restaurant_address'] = location
    if idx == 0:
       data.to_csv(FILE_PATH, index=False)
    else:
        data1 = pd.read_csv(FILE_PATH)
        df = pd.concat([data1, data])
        df.to_csv(FILE_PATH, index = False)











