import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime
from deepdiff import DeepDiff


USERNAME = os.environ['USERNAME_BYU']
PASSWORD = os.environ['PASSWORD']
CLASSDATA = os.environ['CLASSDATA']

class Assignment:
    def __init__(self, name, dueDate, submitted, score):
        self.name = name
        self.dueDate = dueDate
        self.submitted = submitted
        self.score = score

# TODO: list has scaling buffer

def scrapeClass(class_, driver):
    print("Getting assignments for " + class_['name'])
    driver.get(class_["link"])
    if not loggedIn(driver):
        login(driver)
    if(class_['type'] == 'learningsuite'):
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, appData["elements"]["table_ls"]["css"]))
        )
    else:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, appData["elements"]["table_c"]["css"]))
        )
    
    table = pd.read_html(table.get_attribute('outerHTML'))[0]
    assignments = []
    print("Scanning column titles...")
    # Default column values
    nameIndex = 1
    dueDateIndex = 2
    submitIndex = 3
    scoreIndex = 4

    for i in range(len(table.columns)):
        if "unnamed" not in table.columns[i].lower():
            if any(sub in table.columns[i].lower() for sub in appData["columnKeywords"]["name"]):
                print("Name:", table.columns[i], i)
                nameIndex = i
            elif any(sub in table.columns[i].lower() for sub in appData["columnKeywords"]["dueDate"]):
                print("DueDate:", table.columns[i], i)
                dueDateIndex = i
            elif any(sub in table.columns[i].lower() for sub in appData["columnKeywords"]["score"]):
                print("Score:", table.columns[i], i)
                scoreIndex = i
            elif any(sub in table.columns[i].lower() for sub in appData["columnKeywords"]["submissionStatus"]) and class_['type'] == 'learningsuite':
                print("Submit:", table.columns[i], i)
                submitIndex = i
            elif any(sub in table.columns[i].lower() for sub in appData["columnKeywords"]["submissionStatus_c"]):
                print("Submit:", table.columns[i], i)
                submitIndex = i
            # else:
            #     print("No matching column for", table.columns[i])
    
    for row in table.iterrows():
        if not pd.isna(row[1][dueDateIndex]):
            if '-' in row[1][dueDateIndex]:
                row[1][dueDateIndex] = row[1][dueDateIndex].split('-')[1].strip()
            name = row[1][nameIndex]
            if class_['type'] == 'learningsuite':
                dueDate = datetime.strptime(row[1][dueDateIndex]+" 2022", "%b %d, %I:%M %p %Y")
            else:
                try:
                    dueDate = datetime.strptime(row[1][dueDateIndex]+" 2022", "%b %d by %I:%M%p %Y")
                except:
                    dueDate = datetime.strptime(row[1][dueDateIndex]+" 2022", "%b %d by %I%p %Y")
            submit = row[1][submitIndex]
            if class_['type'] == 'learningsuite':
                score = row[1][scoreIndex]
            else:
                score = row[1][scoreIndex].split()
                score = score[len(score)-1]
                if score == 'grade':
                    score = None
            # TODO: Make year dynamic
            submitted = None
            if not pd.isna(submit):
                # TODO: Add grade
                if 'submission' in submit.lower():
                    submitted = 'submitted'
                elif 'submit' in submit.lower():
                    submitted = 'not submitted'
            if submitted is None:
                if score is not None:
                    if class_['type'] == 'canvas':
                        submitted = 'submitted'
                    else:
                        temp = score.replace(' ', '').split('/')
                        if len(temp)==2 and temp[0] != '':
                            submitted = 'submitted'
            assignment = Assignment(name, dueDate.strftime("%Y-%m-%d %H:%M:%S"), submitted, score)
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
    print("Submit DUO")
    trust = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, appData["elements"]["trust"]["css"]))
    )
    trust.click()
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
options.add_argument('headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

print("Scrapping classes...")
try:
    # TODO: Add hashing
    newData = {class_["name"]:scrapeClass(class_, driver) for class_ in classData["classLinks"]}
    diff = DeepDiff(classData["assignments"], newData)

except Exception as e:
    print(e)
    driver.close()

# TODO: Compare to old record for changes

with open(CLASSDATA, 'w') as outfile:
    json.dump(classData, outfile, default=str, indent=4)