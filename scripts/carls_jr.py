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

FILE_PATH = ""
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
    '871 Marina Village Pkwy, Alameda, CA, 94501, US',
    '10770 MacArthur Blvd, Oakland, CA, 94605, US',
    '1 Hallidie Plaza, San Francisco, CA, 94102, US',
    '20550 Mission Blvd, Hayward, CA, 94541, US',
    '1550 Fitzgerald Drive, Pinole, CA, 94564, US',
    '5670 Thornton Ave, Newark, CA, 94560, US',
    '46637 Mission Blvd, Fremont, CA, 94539, US',
    '27467 Hesperian Blvd, Hayward, CA, 94545, US',
    '1101 Branham Ln, San Jose, CA, 95118, US',
    '4595 Century Blvd., Pittsburg, CA, 94565, US',
    '915 Main St, Oakley, CA, 94561, US',
    '2590 S East Ave, Fresno, CA, 93706, US',
    '5007 E McKinley Ave, Fresno, CA, 93727, US',
    '101 S Union Ave, Bakersfield, CA, 93307, US',
    '229 West 7th Street, Los Angeles, CA, 90014, US',
    '2320 E 4th St, Los Angeles, CA, 90033, US',
    '3215 N. Broadway, Los Angeles, CA, 90031, US',
    '3005 W 6Th St, Los Angeles, CA, 90020, US',
    '2912 S Figueroa St, Los Angeles, CA, 90007, US',
    '1751 S Soto St, Los Angeles, CA, 90023, US',
    '1670 W Pacific Coast Hwy, Long Beach, CA, 90813, US',
    '271 E Willow St, Long Beach, CA, 90806, US',
    '1881 E Del Amo Blvd, Carson, CA, 90746, US',
    '840 Sepulveda Blvd, Harbor City, CA, 90710, US',
    '6601 Atlantic Ave, Long Beach, CA, 90805, US',
    '24715 Pico Canyon Rd, Stevenson Ranch, CA, 91381, US',
    '18950 Soledad Canyon Rd, Canyon Country, CA, 91351, US',
    '18741 Via Princessa, Santa Clarita, CA, 91387, US',
    '3770 Telegraph Ave, Oakland, CA, 94609, US',
    '3897 Sonoma Blvd, Vallejo, CA, 94589, US',
    '2434 Junipero Serra Blvd, Daly City, CA, 94015, US',
    '6460 Redwood Dr, Rohnert Park, CA, 94928, US',
    '1000 Farmers Ln, Santa Rosa, CA, 95405, US',
    '495 Stony Point Rd, Santa Rosa, CA, 95401, US',
    '1142 Fremont Blvd, Seaside, CA, 93955, US',
    '402 S Main St, Orange, CA, 92868, US',
    '1809 E Edinger Ave, Santa Ana, CA, 92705, US',
    '14041 Newport Ave, Tustin, CA, 92780, US',
    '13011 Harbor Blvd, Garden Grove, CA, 92843, US',
    '2820 E. Lincoln Ave, Anaheim, CA, 92806, US',
    '794 N Brookhurst St, Anaheim, CA, 92801, US',
    '2119 S Harbor Blvd, Anaheim, CA, 92802, US',
    '11051 Euclid Ave, Garden Grove, CA, 92840, US',
    '3110 E La Palma, Anaheim, CA, 92806, US',
    '4315 Sierra College Blvd, Rocklin, CA, 95650, US',
    '101 Ferrari Ranch Rd, Lincoln, CA, 95648, US',
    '5225 Canyon Crest Dr Ste 82, Riverside, CA, 92507, US',
    '6061 Van Buren Blvd, Riverside, CA, 92503, US',
    '8919 Limonite Ave, Riverside, CA, 92509, US',
    '2940 Van Buren Boulevard Suite 100, Riverside, CA, 92503, US',
    '27670 Eucalyptus Ave, Moreno Valley, CA, 92555, US',
    '69 W Nuevo Rd, Perris, CA, 92571, US',
    '40375, Murrieta, CA, 92563, US',
    '251 Diamond Dr, Lake Elsinore, CA, 92530, US',
    '30604 Benton Rd, Winchester, CA, 92596, US',
    '2615 Broadway, Sacramento, CA, 95818, US',
    '854 Harbor Blvd, West Sacramento, CA, 95691, US',
    '5501 Freeport Ave, Sacramento, CA, 95822, US',
    '8150 Sheldon Rd, Elk Grove, CA, 95758, US',
    '6201 Mack Road, Sacramento, CA, 95823, US',
    '1505 E Highland Ave, San Bernardino, CA, 92404, US',
    '1180 S Mount Vernon Ave, Colton, CA, 92324, US',
    '293 East 40th Street, San Bernardino, CA, 92404, US',
    '4424 University Parkway, San Bernardino, CA, 92407, US',
    '620 W Foothill Blvd, Rialto, CA, 92376, US',
    '2022 N Riverside Ave, Rialto, CA, 92377, US',
    '15669 Main St, Hesperia, CA, 92345, US',
    '15227 Hook Blvd, Victorville, CA, 92394, US',
    '14292 Highway 395, Adelanto, CA, 92301, US',
    '3008 El Cajon Blvd, San Diego, CA, 92104, US',
    '695 H St, Chula Vista, CA, 91910, US',
    '7162 Broadway, Lemon Grove, CA, 91945, US',
    '1502 Sweetwater Rd, National City, CA, 91950, US',
    '996 Third Ave., Chula Vista, CA, 91911, US',
    '1280 E Plaza Blvd, National City, CA, 91950, US',
    '700 13Th Street, Imperial Beach, CA, 91932, US',
    '2608 El Camino Real, Carlsbad, CA, 92010, US',
    '611 Douglas Dr, Oceanside, CA, 92058, US',
    '4186, Oceanside, CA, 92056, US',
    '775 College Blvd, Oceanside, CA, 92057, US',
    '660 Hacienda Dr, Vista, CA, 92081, US',
    '899 Cherry Ave, San Bruno, CA, 94066, US',
    '1140 Triton Dr, San Mateo, CA, 94404, US',
    '4610, Carpinteria, CA, 93013, US',
    '3015 Johnson Drive, Ventura, CA, 93003, US',
    '1745 S Victoria Ave, Ventura, CA, 93003, US',
    '1095 Oakland Rd, San Jose, CA, 95112, US',
    '172 Bernal Rd, San Jose, CA, 95139, US',
    '1890 McCandless Dr, Milpitas, CA, 95035, US',
    '5000 El Camino Real, Los Altos, CA, 94022, US',
    '1999 Camden Ave, San Jose, CA, 95124, US',
    '2380 N Texas St, Fairfield, CA, 94533, US',
    '2808 McHenry Ave, Modesto, CA, 95350, US',
    '1600 Oakdale Rd, Modesto, CA, 95355, US',
    '118 E Whitmore Ave, Modesto, CA, 95358, US',
    '3350 S Mooney Blvd, Visalia, CA, 93277, US',
    '2301 N, Oxnard, CA, 93036, US',
    '3255 Saviers Rd, Oxnard, CA, 93033, US'
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


