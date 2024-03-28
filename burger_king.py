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

FILE_PATH = "burger_king_prices.csv"
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
    '5701 Christie Avenue, Emeryville, CA, 94608, US',
    '15050 E. 14th Street, San Leandro, CA, 94578, US',
    '849 University Avenue, Berkeley, CA, 94710, US',
    '7200 Bancroft Road, Oakland, CA, 94605, US',
    '3996 Washington Boulevard, Fremont, CA, 94538, US',
    '1801 Decoto Road, Union City, CA, 94587, US',
    '34943, Newark, CA, 94560, US',
    '31361 Alavarado Niles Road, Union City, CA, 94587, US',
    '29671 Mission Blvd., Hayward, CA, 94544, US',
    '3399 Port Chicago Hwy, Concord, CA, 94520, US',
    '5400 Ygnacio Valley Road, Concord, CA, 94521, US',
    '7 Muir Road, Martinez, CA, 94553, US',
    '2855 North Main Street, Walnut Creek, CA, 94597, US',
    "4610 East King's Canyon Rd., Fresno, CA, 93702, US",
    '2410 North Cedar, Fresno, CA, 93703, US',
    '575 North Clovis Avenue, Fresno, CA, 93727, US',
    '4087 West Clinton Avenue, Fresno, CA, 93722, US',
    '3405 Union Ave, Bakersfield, CA, 93305, US',
    '1949 Columbus Avenue, Bakersfield, CA, 93305, US',
    '5120 Olive Drive, Bakersfield, CA, 93308, US',
    '2508 White Lane, Bakersfield, CA, 93304, US',
    '8200 Stockdale Hwy, Bakersfield, CA, 93309, US',
    '6217 Niles Street, Bakersfield, CA, 93306, US',
    '700 East Cesar E Chavez Avenue, Los Angeles, CA, 90012, US',
    '1501 West 6th Street, Los Angeles, CA, 90017, US',
    '1830 West 8th Street, Los Angeles, CA, 90057, US',
    '1540 North Eastern Avenue, Los Angeles, CA, 90063, US',
    '1845 S. Vermont Ave., Los Angeles, CA, 90006, US',
    '127 West 4th Street, Long Beach, CA, 90802, US',
    '2600, Long Beach, CA, 90806, US',
    '2955 North Bellflower Boulevard, Long Beach, CA, 90815, US',
    '5540 Cherry Avenue, Long Beach, CA, 90805, US',
    '20950 Figueroa Street, Carson, CA, 90745, US',
    '24530 Lyons Avenue, Newhall, CA, 91321, US',
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
    '1329 South Harbor Boulevard, Fullerton, CA, 92832, US',
    '814 N Brookhurst St, Anaheim, CA, 92801, US',
    '2403 East Chapman Avenue, Fullerton, CA, 92831, US',
    '5121 Foothills Boulevard, Roseville, CA, 95747, US',
    '5869 Antelope Rd, Sacramento, CA, 95621, US',
    '7760 Sunrise Blvd, Citrus Heights, CA, 95610, US',
    '8034 Greenback Lane, Citrus Heights, CA, 95610, US',
    '4960 Auburn Blvd., Sacramento, CA, 95841, US',
    '7201 Fair Oaks Boulevard, Carmichael, CA, 95608, US',
    '2167 University Avenue, Riverside, CA, 92507, US',
    '6835 Valley Way, Riverside, CA, 92509, US',
    '5790 VAN BUREN BOULEVARD, Riverside, CA, 92503, US',
    '3630 Tyler Street, Riverside, CA, 92505, US',
    '205 East Redlands, San Bernardino, CA, 92408, US',
    '23125 Hemlock Avenue, Moreno Valley, CA, 92557, US',
    '24800 Sunnymead Blvd, Moreno Valley, CA, 92553, US',
    '1688 North, Perris, CA, 92571, US',
    '1320 Industrial Park Avenue, Redlands, CA, 92374, US',
    '2714 El Centro Road, Sacramento, CA, 95833, US',
    '763 Ikea Ct #120, West Sacramento, CA, 95605, US',
    '5610 Freeport Boulevard, Sacramento, CA, 95822, US',
    '1915 Arden Way, Sacramento, CA, 95815, US',
    '7225 Greenhaven Drive, Sacramento, CA, 95831, US',
    '5150 Stockton Blvd., Sacramento, CA, 95820, US',
    '9181 East Stockton Boulevard, Elk Grove, CA, 95624, US',
    '7218 Stockton Boulevard, Sacramento, CA, 95823, US',
    '935 North Waterman, San Bernardino, CA, 92410, US',
    '487 West Highland, San Bernardino, CA, 92405, US',
    '503 East Foothill, Rialto, CA, 92376, US',
    '3235 West Little League Drive, San Bernardino, CA, 92407, US',
    '16878 Foothill Boulevard, Fontana, CA, 92335, US',
    '1361 West Foothill Boulevard, Rialto, CA, 92376, US',
    '10055 Cedar Avenue, Bloomington, CA, 92316, US',
    '1210 11th Ave, San Diego, CA, 92101, US',
    '1220 South 28th Street, San Diego, CA, 92113, US',
    '3747 Rosecrans Street, San Diego, CA, 92110, US',
    '3676 Market Street, San Diego, CA, 92102, US',
    '815 Highland Avenue, National City, CA, 91950, US',
    '599 Broadway, Chula Vista, CA, 91910, US',
    '97 Bonita Road, Chula Vista, CA, 91910, US',
    '1265 Third Avenue, Chula Vista, CA, 91911, US',
    '899 East H Street, Chula Vista, CA, 91910, US',
    '819 Van Ness Avenue, San Francisco, CA, 94109, US',
    '1701 FILLMORE ST, San Francisco, CA, 94115, US',
    '35 Powell Street, San Francisco, CA, 94102, US',
    '3900 Geary Boulevard, San Francisco, CA, 94118, US',
    '1690 Valencia Street, San Francisco, CA, 94110, US',
    '245 Bayshore Blvd., San Francisco, CA, 94124, US',
    '702 North Wilson Way, Stockton, CA, 95205, US',
    '619 West Charter Way, Stockton, CA, 95206, US',
    '4571 North Pershing Avenue, Stockton, CA, 95207, US',
    '1358 Madonna Road, San Luis Obispo, CA, 93405, US',
    '1773 W Grand Ave, Grover Beach, CA, 93433, US',
    '8304 El Camino Real, Atascadero, CA, 93422, US',
    '180 Niblick Rd, Paso Robles, CA, 93446, US',
    '2817 South El Camino Real, San Mateo, CA, 94403, US',
    '575 El Camino Real, Redwood City, CA, 94063, US',
    '2102 Middlefield Road, Redwood City, CA, 94063, US',
    '1278 El Camino Real, San Bruno, CA, 94066, US',
    '972 El Camino Real, South San Francisco, CA, 94080, US',
    '111, Colma, CA, 94014, US',
    '898 John Daly Boulevard, Daly City, CA, 94015, US',
    '2050 South Broadway, Santa Maria, CA, 93454, US',
    '1153 North H Street, Lompoc, CA, 93436, US',
    '1030 Mclaughlin Ave., San Jose, CA, 95122, US',
    '1181 Old Oakland Road, San Jose, CA, 95112, US',
    '2170 Monterey Road, San Jose, CA, 95112, US',
    '2390 Almaden Road, San Jose, CA, 95125, US',
    '329 North Capital Avenue, San Jose, CA, 95133, US',
    '1305 N Bascom Ave, San Jose, CA, 95128, US',
    '773 North Mathilda Avenue, Sunnyvale, CA, 94085, US',
    '3750 El Camino Real, Santa Clara, CA, 95051, US',
    '5154 Moorpark Ave, San Jose, CA, 95129, US',
    '385 South Kiely, San Jose, CA, 95129, US',
    '2532 Channing Avenue, San Jose, CA, 95131, US',
    '2015 Mission Street, Santa Cruz, CA, 95060, US',
    '1302 Soquel Avenue, Santa Cruz, CA, 95062, US',
    '2001 - 41st Avenue, Capitola, CA, 95010, US',
    '3606 Sonoma Boulevard, Vallejo, CA, 94590, US',
    '844 Willow Avenue, Hercules, CA, 94547, US',
    '56 Mission Circle, Santa Rosa, CA, 95409, US',
    '5020 Redwood Drive, Rohnert Park, CA, 94928, US',
    '6125 Commerce Boulevard, Rohnert Park, CA, 94928, US',
    '2542 Guerneville Road, Santa Rosa, CA, 95401, US',
    '6351 Hembree Lane, Windsor, CA, 95492, US',
    '1042 North Carpenter Road, Modesto, CA, 95351, US',
    '2320 McHenry Ave, Modesto, CA, 95350, US',
    '2101 Sylvan Avenue, Modesto, CA, 95355, US',
    '500 South De Maree, Visalia, CA, 93277, US',
    '6603 Betty Dr, Visalia, CA, 93291, US',
    '1255 North Blackstone Street, Tulare, CA, 93274, US',
    '2001 North, Oxnard, CA, 93036, US',
    '2500 S. Ventura Road, Oxnard, CA, 93033, US',
    '5950 Telegraph Road, Ventura, CA, 93003, US',
    '181 South Arniell Road, Camarillo, CA, 93010, US'
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
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div/div/div/div[2]/div[1]/div/div/div/div[3]/div/div[2]/div[1]/div/div/div/div/div[1]/div/div[2]/div/div/div[3]/button"))
    )
    search_box4.click()
    time.sleep(3)

    search_box5 = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div/div/div/div[2]/div[1]/div/div/div/div/div/div/div[2]/div/div[3]')))
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
        data.to_csv('burger_king_prices.csv', index=False)
    else:
        data1 = pd.read_csv('burger_king_prices.csv')
        df = pd.concat([data1, data])
        df.to_csv('burger_king_prices.csv', index = False)











