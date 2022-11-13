import os
from datetime import date, datetime
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def getOptimalRooms(optimalSchedule, driver):
    print("Navigating to homepage...")
    driver.get('https://groupstudy.lib.byu.edu/')
    dateElement = driver.find_element(By.XPATH, appData['elements']['date']['xpath'])
    dateSelect = Select(dateElement)
    floorSelect = Select(driver.find_element(By.XPATH, appData['elements']['subarea']['xpath']))
    numOptions = len(dateSelect.options)

    reserveRooms = []
    for key in optimalSchedule.keys():
        i = [i for i, x in enumerate(dateSelect.options) if key in x.text.lower()][0]
        dateSelect.select_by_index(i)
        date = dateSelect.options[i].text
        floorIndex = [i for i, x in enumerate(floorSelect.options) if str(optimalSchedule[key]['floor']) in x.text.lower()]
        if len(floorIndex) > 0:
            floorIndex = floorIndex[0]
        else:
            print("Floor not found")
            continue

        floorSelect.select_by_index(floorIndex)
        floor = floorSelect.options[floorIndex].text
        print("Getting rooms for " + date + ", " + floor + "...")
        go = driver.find_element(By.XPATH, appData['elements']['go']['xpath'])
        go.click()
        grid = driver.find_element(By.XPATH, appData['elements']['grid']['xpath'])
        rooms = grid.find_elements(By.CSS_SELECTOR, appData['elements']['rooms']['css'])[0]
        rooms = rooms.find_elements(By.XPATH, "./*")
        optimalTime = optimalSchedule[key]['start']
        times = grid.find_elements(By.XPATH, appData['elements']['times']['xpath'])
        timeRow = [timeRow for timeRow in times if optimalTime in timeRow.get_attribute('innerHTML')]
        if len(timeRow) > 0:
            timeRowItem = timeRow[0]
            timeRow = timeRowItem.find_elements(By.XPATH, "./*")
            # TODO: add preferred room logic
            # TODO: Add logic if preferred room, floor, time is not available
            maxTime = {}
            for j in range(1, len(timeRow)):
                if 'Reserved' not in timeRow[j].get_attribute('innerHTML'):
                    roomData = rooms[j].text.split('\n')
                    roomNumber = roomData[0]
                    numberOfSeats = int(roomData[1].split(' ')[0])
                    if numberOfSeats >= optimalSchedule[key]['numSeats']:
                        timeAvailable = 0.5
                        index = times.index(timeRowItem)+1                        
                        while index < len(times):
                            currRow = times[index].find_elements(By.XPATH, "./*")
                            if 'Reserved' not in currRow[j].get_attribute('innerHTML'):
                                index += 1
                                timeAvailable += 0.5
                            else:
                                break
                        roomDetails = {'roomNumber': roomNumber, 'numberOfSeats': numberOfSeats, 'date': date, 'floor': floor, 'day': key, 'start': optimalTime}
                        if maxTime == {} or timeAvailable > maxTime['timeAvailable']:
                            maxTime['timeAvailable'] = timeAvailable
                            maxTime['room'] = roomNumber
                            maxTime['link'] = timeRow[j].find_element(By.XPATH, "./*").get_attribute('href')
                            maxTime['roomDetails'] = roomDetails
            if maxTime is not {}:
                print("Room " + maxTime['roomDetails']['roomNumber'] + " is available at " + optimalTime + " on " + date + " with " + str(maxTime['roomDetails']['numberOfSeats']) + " seats for " + str(timeAvailable) + " hours.")
                reserveRooms.append(maxTime)
            else:
                print("No rooms available at " + optimalTime + " on " + date + " with " + str(optimalSchedule[key]['numSeats']) + " seats.")
        else: print("No time row for found.")

        if i < (numOptions - 1):
            WebDriverWait(driver, 10).until(EC.staleness_of(dateElement))
            dateElement = driver.find_element(By.XPATH, appData['elements']['date']['xpath'])
            dateSelect = Select(dateElement)        
            floorSelect = Select(driver.find_element(By.XPATH, appData['elements']['subarea']['xpath']))
        
    return reserveRooms

def reserveRooms_(reserveRooms, driver):
    for room in reserveRooms:
        driver.get(room['link'])
        # Check is duration is 2 hours
        duration = Select(driver.find_element(By.CSS_SELECTOR, appData['elements']['duration']['css']))
        numOptions = len(duration.options)
        duration.select_by_index(numOptions - 1)
        description = driver.find_element(By.CSS_SELECTOR, appData['elements']['description']['css'])
        # TODO: Add description
        description.send_keys("Reserved for group study")
        reserveButton = driver.find_element(By.CSS_SELECTOR, appData['elements']['reserve']['css'])
        input("FINISH CAPTCHA, then press Enter to continue...")
        reserveButton.click()
        schedule['currentSchedule'][room['roomDetails']['day']] = room
        print("Reserved room!")

# TODO: Replace with updated login function
def login_mainpage(driver):
    print("Navigating to homepage...")
    driver.get('https://groupstudy.lib.byu.edu/')
    print("Logging in...")
    loginButton = driver.find_element(By.CSS_SELECTOR, appData['elements']['login']['css'])
    loginButton.click()
    username = driver.find_element(By.CSS_SELECTOR, appData['elements']['username']['css'])
    username.send_keys(USERNAME)
    password = driver.find_element(By.CSS_SELECTOR, appData['elements']['password']['css'])
    password.send_keys(PASSWORD)
    submitButton = driver.find_element(By.CSS_SELECTOR, appData['elements']['submit']['css'])
    submitButton.click()
    input("Press enter after duo...")
    print("Logged in!")

def getReservedRooms():
    with open(SCHEDULE, 'r') as f:
        schedule = json.load(f)
    rooms = []
    for reservation in schedule['currentSchedule'].values():
        # TODO: Make year dynamic
        reservationDate = datetime.strptime(reservation['roomDetails']['date']+", 2022", '%A, %B %d, %Y')
        if reservationDate.date() == datetime.now().date():
            rooms.append(reservation['roomDetails'])
    return rooms

USERNAME = os.environ['USERNAME_BYU']
PASSWORD = os.environ['PASSWORD']
SCHEDULE = os.environ['SCHEDULE']
if SCHEDULE == '':
    raise Exception('No schedule provided')

with open('appData.json', 'r') as f:
    appData = json.load(f)

def main():
    with open(SCHEDULE, 'r') as f:
        schedule = json.load(f)

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    schedule['currentSchedule'] = {i:x for (i, x) in schedule['currentSchedule'].items() if datetime.strptime(x['roomDetails']['date']+' 2022', '%A, %B %d %Y').date()  >= date.today()}

    optimalSchedule = {i:x for (i, x) in schedule['optimalSchedule'].items() if i not in schedule['currentSchedule'].keys()}

    if len(optimalSchedule) > 0:
        reserveRooms = getOptimalRooms(optimalSchedule, driver)
        if(len(reserveRooms) > 0):
            print("Reserving rooms...")
            driver.close()
            driver = webdriver.Chrome(ChromeDriverManager().install())
            login_mainpage(driver)
            reserveRooms_(reserveRooms, driver)
            driver.close()
        else:
            print("No rooms available for reservation.")
    else:
        print("All optimal schedule rooms are scheduled.")

    input("Press Enter to save...")
    with open(SCHEDULE, 'w') as outfile:
        json.dump(schedule, outfile, indent=4)