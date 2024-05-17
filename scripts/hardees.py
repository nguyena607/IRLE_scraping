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

FILE_PATH = "raw_prices_hardees_non_ca_05162024.csv"
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

hardees_locations = [
    '6671 Roswell Rd NE, Sandy Springs, GA, 30328, US',
    '161 Marietta Hwy, Canton, GA, 30114, US',
    '1097 Highway 92, Acworth, GA, 30102, US',
    '4850 Floyd Road SW, Mableton, GA, 30126, US',
    '125 W Maple St, Cumming, GA, 30040, US',
    '2930 Highway 138 SW, Conyers, GA, 30094, US',
    '5259 Highway 78, Stone Mountain, GA, 30087, US',
    '3062 Anvil Block Road, Ellenwood, GA, 30294, US',
    '2516 Bouldercrest Drive, Atlanta, GA, 30316, US',
    '940 Thornton Rd., Lithia Springs, GA, 30122, US',
    '1520, Buford, GA, 30518, US',
    '5373 E Bannister Rd., Kansas City, MO, 64137, US',
    '8021 State Ave, Kansas City, KS, 66112, US',
    '6323 Independence Ave, Kansas City, MO, 64125, US',
    '4011 S Noland Rd, Independence, MO, 64055, US',
    '2109 Savannah Hwy., Charleston, SC, 29414, US',
    '5201 Ashley Phosphate Rd., North Charleston, SC, 29418, US',
    '201 N, Goose Creek, SC, 29445, US',
    '10005 Dorchester Rd., Summerville, SC, 29485, US',
    '228 Oxmoor Blvd, Homewood, AL, 35209-4737, US',
    'Roebuck Parkway East &amp; Red Lane Rd, Birmingham, AL, 35215, US',
    '917 Allison-Bonnett Memorial Dr, Hueytown, AL, 35023, US',
    '1 Gateway Blvd S, Savannah, GA, 31419-7551, US',
    '8601 Allisonville Rd, Indianapolis, IN, 46250-1552, US',
    '8009 Pendleton Pike, Indianapolis, IN, 46226-4012, US',
    '9020 East 21st Street, Indianapolis, IN, 46229, US',
    '710 W 10th St, Indianapolis, IN, 46202, US',
    '4945 S Emerson Ave, Indianapolis, IN, 46203-5938, US',
    '8755 University Avenue, Des Moines, IA, 50325, US',
    '915 Army Post Rd, Des Moines, IA, 50315, US',
    '1510 Sw Tradition Dr, Ankeny, IA, 50023, US',
    '2990 Richmond Rd, Lexington, KY, 40509, US',
    '2909 Fern Valley Road, Louisville, KY, 40219, US',
    '11201 Oscar Rd., Louisville, KY, 40241, US',
    '1807 Four Seasons Blvd, Hendersonville, NC, 28792, US',
    '4260 Legion Road, Hope Mills, NC, 28348, US',
    '2497 Hope Mills Road, Fayetteville, NC, 28304, US',
    '3803 Morganton Road, Fayetteville, NC, 28314, US',
    '3912 North Duke Street, Durham, NC, 27704, US',
    '6116 Farrington Road, Chapel Hill, NC, 27517, US',
    '10 E Clemmonsville Rd, Winston Salem, NC, 27127, US',
    '3351 Sides Branch Rd, Winston Salem, NC, 27127, US',
    '704 W Academy St, Randleman, NC, 27317, US',
    '4201 East W.T.Harris Blvd, Charlotte, NC, 28215, US',
    '14101 Statesville Rd, Huntersville, NC, 28078, US',
    '875 Gold Hill Rd, Fort Mill, SC, 29708, US',
    '140 Dale Earnhardt Boulevard, Kannapolis, NC, 28081, US',
    '547 Church Street North, Concord, NC, 28025, US',
    '101 Village Road Ne, Leland, NC, 28451, US',
    '1970 S. 17Th Street, Wilmington, NC, 28401, US',
    '1420 Floral Parkway, Wilmington, NC, 28403, US',
    '5601, Castle Hayne, NC, 28429, US',
    '100 Vandora Springs Rd., Garner, NC, 27529, US',
    '5601 Creedmoor Rd, Raleigh, NC, 27612, US',
    '5639 Hillsborough St., Raleigh, NC, 27606, US',
    '2020 W Market St, York, PA, 17404, US',
    '820 E Main St, Dallastown, PA, 17313, US',
    '646 Main St, Mc Sherrystown, PA, 17344, US',
    '451 Mills Ave, Greenville, SC, 29605, US',
    '2306 W Parker Rd, Greenville, SC, 29617, US',
    '1213 Woodruff Rd, Greenville, SC, 29607, US',
    '3203 Wade Hampton Blvd, Taylors, SC, 29687, US',
    '6501 State Park Road, Travelers Rest, SC, 29690, US',
    '6000 N Kings Hwy, Myrtle Beach, SC, 29577, US',
    '10 Hwy 17 N, Surfside Beach, SC, 29575, US',
    '1506 Church St, Conway, SC, 29526, US',
    '2499 Augusta Rd, West Columbia, SC, 29169, US',
    '496 Piney Grove Rd, Columbia, SC, 29212, US',
    '1910 S Lake Dr, Lexington, SC, 29073-8282, US',
    '3852 Rosewood Dr, Columbia, SC, 29205, US',
    '120 Veterans Rd, Columbia, SC, 29209, US',
    '1397 E Main St, Duncan, SC, 29334, US',
    '2165 Mana Court, Rock Hill, SC, 29730, US',
    '206 S Main St, Clover, SC, 29710, US',
    '5775 Old Hickory Blvd, Hermitage, TN, 37076, US',
    '400 S Cartwright, Goodlettsville, TN, 37072, US',
    '1436 Robinson Rd, Old Hickory, TN, 37138, US',
    '7102 Highway 70 S, Bellevue, TN, 37221, US',
    '4099 Nolensville Pike, Nashville, TN, 37211, US',
    '2919 Tazewell Pike, Knoxville, TN, 37918, US',
    '6760 Clinton Hwy, Knoxville, TN, 37912, US',
    '150 N Cedar Bluff Road, Knoxville, TN, 37923, US',
    '1685 Middle Tennessee Blvd, Murfreesboro, TN, 37130, US',
    '1851 Memorial Blvd, Murfreesboro, TN, 37129, US',
    '2382 Old Fort Pkwy, Murfreesboro, TN, 37128, US',
    '2983 S Church St, Murfreesboro, TN, 37127, US',
    '255 S Lowry St, Smyrna, TN, 37167, US',
    '3046 Parkway, Pigeon Forge, TN, 37863, US',
    '2005 Whitten Road, Memphis, TN, 38133, US',
    '749 Goodman Rd West, Horn Lake, MS, 38637, US',
    '7015 Hacks Cross Road, Olive Branch, MS, 38654, US',
    '7003 City Circle Way, Fairview, TN, 37062, US',
    '508 Waldron Rd, La Vergne, TN, 37086, US',
    '1000 Acorn Dr, Nashville, TN, 37210, US',
    '2450 E Layton Ave, Saint Francis, WI, 53235-6045, US'
]

for idx, location in enumerate(hardees_locations):
    driver = setup_driver()
    driver.get('https://order.hardees.com/')

    search_box = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/ion-app/ion-router-outlet/app-custom-location-finder/ion-content/div/main/div/div[1]/header/form/div/app-custom-location-search/div/div[2]/input")))
    search_box.clear()
    search_box.click()
    search_box.send_keys(location)

    ActionChains(driver).move_to_element(search_box).move_by_offset(0, -5).perform()

    search_box2 = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/ion-app/ion-router-outlet/app-custom-location-finder/ion-content/div/main/div/div[1]/header/form/div/app-custom-location-search/div/div[3]/ul/li[1]/button")))
    search_box2.click()
    time.sleep(3)

    search_box3 = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/ion-app/ion-router-outlet/app-custom-location-finder/ion-content/div/main/div/div[1]/div/div[2]/swiper/div/div[1]/app-custom-location-card/div/div/div[3]/div/button")))
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