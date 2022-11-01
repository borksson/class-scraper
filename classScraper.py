import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime

USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']
CLASSDATA = os.environ['CLASSDATA']

def scrapeClass(class_, driver):
    # TODO: Add canvas
    class Assignment:
        def __init__(self, name, dueDate, submitted, score):
            self.name = name
            self.dueDate = dueDate
            self.submitted = submitted
            self.score = score
        
    print("Getting assignments for " + class_['name'])
    driver.get(class_["link"])
    if not loggedIn(driver):
        login(driver)
    table = pd.read_html(driver.page_source)[0]
    assignments = []
    # TODO: Make rows dynamic
    for row in table.iterrows():
        if not pd.isna(row[1][2]):
            if '-' in row[1][2]:
                row[1][2] = row[1][2].split('-')[1].strip()
            # TODO: Make year dynamic
            submitted = True
            if (not pd.isna(row[1][3])) and ('Submit' in row[1][3]):
                submitted = False
            assignment = Assignment(row[1][1], datetime.strptime(row[1][2]+" 2022", "%b %d, %I:%M %p %Y"), submitted, row[1][4])
            assignments.append(assignment.__dict__)
    return assignments    

def login(driver):
    print("Logging in...")
    username = driver.find_element(By.CSS_SELECTOR, appData['elements']['username']['css'])
    username.send_keys(USERNAME)
    password = driver.find_element(By.CSS_SELECTOR, appData['elements']['password']['css'])
    password.send_keys(PASSWORD)
    submitButton = driver.find_element(By.CSS_SELECTOR, appData['elements']['submit']['css'])
    submitButton.click()
    # TODO: Make this more efficient
    input("Press enter after duo...")
    print("Logged in!")

def loggedIn(driver):
    try:
        driver.find_element(By.CSS_SELECTOR, appData['elements']['username']['css'])
        return False
    except:
        return True


with open('appData.json', 'r') as f:
    appData = json.load(f)

with open(CLASSDATA, 'r') as f:
    classData = json.load(f)


options = webdriver.ChromeOptions()
#options.add_argument('headless')
driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

print("Scrapping classes...")
classData["assignments"] = {class_["name"]:scrapeClass(class_, driver) for class_ in classData["classLinks"]}
driver.close()

# TODO: Compare to old record for changes

with open(CLASSDATA, 'w') as outfile:
    json.dump(classData, outfile, default=str, indent=4)