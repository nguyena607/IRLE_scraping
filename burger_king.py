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

FILE_PATH = "raw_prices_burgerking_non_ca_03302024.csv"
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
    '659 Government St, Mobile, AL, 36602, US',
    '1524 6th Avenue S, Birmingham, AL, 35233, US',
    '2700 University Blvd, Birmingham, AL, 35233, US',
    '801 3rd Avenue West, Birmingham, AL, 35204, US',
    '2116 Whitesburg Drive, Huntsville, AL, 35801, US',
    '1004 North Memorial Parkway, Huntsville, AL, 35801, US',
    '308 Jordan Lane, Huntsville, AL, 35805, US',
    '3949 Government Boulevard, Mobile, AL, 36693, US',
    '2915 Saint Stephens Rd, Mobile, AL, 36612, US',
    '3875 Airport Boulevard, Mobile, AL, 36609, US',
    '7050, Theodore, AL, 36582, US',
    '3004 Airport Boulevard, Mobile, AL, 36606, US',
    '601 MARTIN LUTHER KING BLVD, Savannah, GA, 31401, US',
    '14 W De Renne Ave, Savannah, GA, 31405, US',
    '4241 AUGUSTA RD, Garden City, GA, 31408, US',
    '11711 Abercorn St., Savannah, GA, 31419, US',
    '415 East Highway 80, Pooler, GA, 31322, US',
    '199 SW Northside Dr, Atlanta, GA, 30313, US',
    '2230 Salem Road, Conyers, GA, 30013, US',
    '2807 Panola Road, Lithonia, GA, 30035, US',
    '2773 Evans Mill Rd, Lithonia, GA, 30058, US',
    '5068 Old National Highway, College Park, GA, 30349, US',
    '8378 W Overland Rd., Boise, ID, 83709, US',
    '6971 West 38th Street, Indianapolis, IN, 46214, US',
    '6904 Kennedy Ave., Hammond, IN, 46323, US',
    '621 West Chicago Avenue, East Chicago, IN, 46312, US',
    '7938 Calumet Avenue, Munster, IN, 46321, US',
    '1817 Indianapolis Boulevard, Whiting, IN, 46394, US',
    '6337 Crawfordsville Rd, Speedway, IN, 46224, US',
    '6003 Gateway Drive, Plainfield, IN, 46168, US',
    '410 East Morris Street, Indianapolis, IN, 46225, US',
    '2122 E. 10th Street, Indianapolis, IN, 46201, US',
    '2502 East Raymond Street, Indianapolis, IN, 46203, US',
    '205 University Avenue, Des Moines, IA, 50314, US',
    '1405 East Court Avenue, Des Moines, IA, 50316, US',
    '2222 M. L. King Jr. Parkway, Des Moines, IA, 50310, US',
    '4600 Fleur Dr, Des Moines, IA, 50321, US',
    '1107 73rd Street, Windsor Heights, IA, 50324, US',
    '5401 E. University Ave, Pleasant Hill, IA, 50327, US',
    '4004 Rainbow Boulevard, Kansas City, KS, 66103, US',
    '1104 North Broadway, Wichita, KS, 67214, US',
    '1909 East Pawnee, Wichita, KS, 67211, US',
    '3500 South Meridian Avenue, Wichita, KS, 67217, US',
    '451 W. New Circle Road, Lexington, KY, 40511, US',
    '730 Lane Allen Rd, Lexington, KY, 40504, US',
    '2548 Richmond Road, Lexington, KY, 40517, US',
    '3348 Clays Mill Road, Lexington, KY, 40503, US',
    '4200 Saron Road, Lexington, KY, 40515, US',
    '1131 Lexington Road, Georgetown, KY, 40324, US',
    '1434 East Tenth Street, Jeffersonville, IN, 47130, US',
    '3100 Highland Road, Baton Rouge, LA, 70802, US',
    '7638 Perkins Road, Baton Rouge, LA, 70810, US',
    '2100 Clearview Parkway, Metairie, LA, 70001, US',
    '2429 West Pinhook Road, Lafayette, LA, 70508, US',
    '2256 Ambassador Caffrey Pkway, Lafayette, LA, 70506, US',
    '3801 Moss Street, Lafayette, LA, 70507, US',
    '5301 Johnston St, Lafayette, LA, 70503, US',
    '2713 South Claiborne St, New Orleans, LA, 70125, US',
    '185 Gause Blvd., Slidell, LA, 70458, US',
    '120 Brownswitch Road, Slidell, LA, 70458, US',
    '141 North Shore Boulevard, Slidell, LA, 70460, US',
    '2509 25th Avenue, Gulfport, MS, 39501, US',
    '623 Second Street, Manchester, NH, 03102, US',
    '28 Portsmouth Ave, Stratham, NH, 03885, US',
    '85 Tunnel Road, Asheville, NC, 28805, US',
    '344 Eastern Blvd, Fayetteville, NC, 28301, US',
    '2820 Bragg Boulevard, Fayetteville, NC, 28303, US',
    '1200 West Club Boulevard, Durham, NC, 27701, US',
    '1601 Hwy 55, Durham, NC, 27707, US',
    '2100 Peters Creek Pkwy, Winston Salem, NC, 27127, US',
    '696 Hanes Mall Blvd, Winston Salem, NC, 27103, US',
    '310 East Trade Street, Charlotte, NC, 28202, US',
    '16800 Caldwell Creek Drive, Huntersville, NC, 28078, US',
    '819 South 3rd Street, Wilmington, NC, 28401, US',
    '2241 Avent Ferry Road, Raleigh, NC, 27606, US',
    '1828 Rock Quarry Road, Raleigh, NC, 27610, US',
    '245 Bayshore Blvd., San Francisco, CA, 94124, US',
    '3900 Geary Boulevard, San Francisco, CA, 94118, US',
    '1563 N Peoria Avenue, Tulsa, OK, 74106, US',
    '3242 East 11th Street, Tulsa, OK, 74104, US',
    '1533 N. Peoria, Tulsa, OK, 74106, US',
    '7939 East 41 Street, South, Tulsa, OK, 74145, US',
    '121 Walmart Drive, North Versailles, PA, 15137, US',
    '3220 Library Rd., Castle Shannon, PA, 15234, US',
    '2900 Brownsville Road, Pittsburgh, PA, 15227, US',
    '1197 Berkshire Blvd, Reading, PA, 19610, US',
    '3419 North 5th Street Highway, Reading, PA, 19605, US',
    '1502, West Chester, PA, 19382, US',
    '4701 Edgmont Ave, Brookhaven, PA, 19015, US',
    '501 Macdade Blvd, Holmes, PA, 19036, US',
    '1408 Lititz Pike, Lancaster, PA, 17601, US',
    '1738 W Tilghman Street, Allentown, PA, 18104, US',
    '1958 South 4th Street, Allentown, PA, 18103, US',
    '568 West Dekalb Pike, King Of Prussia, PA, 19406, US',
    '409 West Ridge Pike, Conshohocken, PA, 19428, US',
    '1521 Columbus Boulevard, Philadelphia, PA, 19147, US',
    '1901 Route 286, Pittsburgh, PA, 15239, US',
    '4490 Broadway Boulevard, Monroeville, PA, 15146, US',
    '490 Loucks Road, York, PA, 17404, US',
    '4709 Dorchester Road, N Charleston, SC, 29405, US',
    '6000 Rivers Ave, North Charleston, SC, 29406, US',
    "501 South King's Highway, Myrtle Beach, SC, 29577, US",
    '2216 Bush River Road, Columbia, SC, 29210, US',
    '3403 North Main Street, Columbia, SC, 29203, US',
    '1212 West Main Street, Lexington, SC, 29072, US',
    '226 Longs Pond Road, Lexington, SC, 29072, US',
    '2902 Two Notch Road, Columbia, SC, 29204, US',
    '2022 Bluff Road, Columbia, SC, 29201, US',
    '6029 Wade Hampton Boulevard, Taylors, SC, 29687, US',
    '1599 Highway 101 South, Greer, SC, 29651, US',
    '1371 Saluda Street, Rock Hill, SC, 29730, US',
    '2430 North Cherry Road, Rock Hill, SC, 29732, US',
    '1501 Charlotte Avenue, Nashville, TN, 37203, US',
    '2119 East 23rd Street, Chattanooga, TN, 37404, US',
    '3401 Amnicola Highway, Chattanooga, TN, 37406, US',
    '2806 North Broadway, Knoxville, TN, 37917, US',
    '819 Memorial Blvd, Murfreesboro, TN, 37129, US',
    '1661 Middle Tennessee Blvd, Murfreesboro, TN, 37130, US',
    '819 Memorial Blvd, Murfreesboro, TN, 37129, US',
    '1621 Middle Tennessee Boulevard, Murfreesboro, TN, 37130, US',
    '412 Forks Of The River, Sevierville, TN, 37862, US',
    '1231 Dolly Parton Pkwy, Sevierville, TN, 37862, US',
    '1027 Union Ave, Memphis, TN, 38104, US',
    '1330 Poplar Avenue, Memphis, TN, 38104, US',
    '3227 Poplar Ave, Memphis, TN, 38111, US',
    '1911 Mallory Lane, Franklin, TN, 37067, US',
    '7116 Highway 70 South, Nashville, TN, 37221, US',
    '493 Old Hickory Blvd, Brentwood, TN, 37027, US',
    '4520 West Commerce, San Antonio, TX, 78237, US',
    '8131 Pat Booker Rd, Live Oak, TX, 78233, US',
    '11001A Fuqua, Houston, TX, 77089, US',
    '2910 Airport Boulevard, Houston, TX, 77051, US',
    '2902 Richey Street, Houston, TX, 77017, US',
    '11404 East Northwest Highway, Dallas, TX, 75218, US',
    '3112 E Berry St, Fort Worth, TX, 76119, US',
    '2542 NE 30th Street, Ft. Worth, TX, 76106, US',
    '2605 Jacksboro Hwy, River Oaks, TX, 76114, US',
    '425 South, El Paso, TX, 79901, US',
    '4639 Irvington, Houston, TX, 77009, US',
    '3009 Collingsworth St, Houston, TX, 77026, US',
    '7011 Gulf Freeway, Houston, TX, 77087, US',
    '10205 E. Freeway, Houston, TX, 77013, US',
    '1094 Federal Road, Houston, TX, 77015, US',
    '6220 East Freeway, Houston, TX, 77020, US',
    '1620 South Loop West, Houston, TX, 77054, US',
    '9009 Clinton Drive, Houston, TX, 77029, US',
    '4676 Bellfort Avenue, Houston, TX, 77051, US',
    '2414 East Expressway 83, Mission, TX, 78572, US',
    '6135 Eastex Freeway #2, Beaumont, TX, 77706, US',
    '6425 Phelan Boulevard, Beaumont, TX, 77706, US',
    '1804 4th Street, Lubbock, TX, 79415, US',
    '2002 50th Street, Lubbock, TX, 79412, US',
    '309 Ih 37, Corpus Christi, TX, 78401, US',
    '3204 Southeast Loop 820, Forest Hill, TX, 76140, US',
    '2500 E Riverside Dr, Austin, TX, 78741, US',
    '1001 East Ben White Boulevard, Austin, TX, 78704, US',
    '2500 S I H 35, Round Rock, TX, 78681, US',
    '4410 Sunrise Rd, Round Rock, TX, 78665, US',
    '13200 North Ih 35, Austin, TX, 78753, US',
    '100 River Oaks Cove, Georgetown, TX, 78626, US',
    '803 N. Main, Layton, UT, 84041, US',
    '4029, Riverdale, UT, 84405, US',
    '575 East 400 South Street, Salt Lake City, UT, 84102, US',
    '11 West Center Street, Orem, UT, 84057, US',
    '1075 South State Street, Orem, UT, 84097, US',
    '2328 University Ave, Green Bay, WI, 54302, US',
    '6909 Odana Road, Madison, WI, 53719, US',
    '810 North Main Street, Oregon, WI, 53575, US',
    '3219 S 27th St, Milwaukee, WI, 53215, US',
    '2862 N. Martin Luther King Dr., Milwaukee, WI, 53212, US',
    '1841 South 14th Street, Milwaukee, WI, 53204, US',
    '1190 West Sunset Drive, Waukesha, WI, 53189, US'
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
        data.to_csv(FILE_PATH, index=False)
    else:
        data1 = pd.read_csv(FILE_PATH)
        df = pd.concat([data1, data])
        df.to_csv(FILE_PATH, index = False)











