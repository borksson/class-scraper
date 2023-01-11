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
from deepdiff import DeepDiff, extract
import hashlib
import re
from login import login, loggedIn


USERNAME = os.environ['USERNAME_BYU']
PASSWORD = os.environ['PASSWORD']
CLASSDATA = os.environ['CLASSDATA']

class Assignment:
    def __init__(self, name, dueDate, submitted, score):
        self.name = name
        self.dueDate = dueDate
        self.submitted = submitted
        self.score = score


with open('appData.json', 'r') as f:
    appData = json.load(f)

# TODO: list has scaling buffer

def scrapeClass(class_, driver):
    print("Getting assignments for " + class_['name'])
    driver.get(class_["link"])
    if not loggedIn(driver):
        driver = login(driver)
    if(class_['type'] == 'learningsuite'):
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, appData["elements"]["table_ls"]["css"]))
        )
    else:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, appData["elements"]["table_c"]["css"]))
        )
    
    table = pd.read_html(table.get_attribute('outerHTML'))[0]
    assignments = {}
    print("Scanning column titles...")
    # Default column values
    nameIndex = 1
    dueDateIndex = 2
    submitIndex = 3
    scoreIndex = 4

    for i in range(len(table.columns)):
        if "unnamed" not in table.columns[i].lower():
            if any(sub in table.columns[i].lower() for sub in appData["columnKeywords"]["name"]):
                nameIndex = i
            elif any(sub in table.columns[i].lower() for sub in appData["columnKeywords"]["dueDate"]):
                dueDateIndex = i
            elif any(sub in table.columns[i].lower() for sub in appData["columnKeywords"]["score"]):
                scoreIndex = i
            elif any(sub in table.columns[i].lower() for sub in appData["columnKeywords"]["submissionStatus"]) and class_['type'] == 'learningsuite':
                submitIndex = i
            elif any(sub in table.columns[i].lower() for sub in appData["columnKeywords"]["submissionStatus_c"]):
                submitIndex = i
            # else:
            #     print("No matching column for", table.columns[i])
    
    for row in table.iterrows():
        if not pd.isna(row[1][dueDateIndex]):
            if '-' in row[1][dueDateIndex]:
                row[1][dueDateIndex] = row[1][dueDateIndex].split('-')[1].strip()
            name = row[1][nameIndex]
            if class_['type'] == 'learningsuite':
                dueDate = datetime.strptime(row[1][dueDateIndex], "%b %d, %I:%M %p")
                dueDate.year = datetime.now().year
                print(dueDate)
            else:
                try:
                    dueDate = datetime.strptime(row[1][dueDateIndex], "%b %d by %I:%M%p")
                    dueDate.year = datetime.now().year
                    print(dueDate)
                except:
                    print("DUE DATE ERROR:")
                    dueDate = datetime.strptime(row[1][dueDateIndex]+, "%b %d by %I%p")
                    dueDate.year = datetime.now().year
                    print(dueDate)
            submit = row[1][submitIndex]
            if class_['type'] == 'learningsuite':
                score = row[1][scoreIndex]
            else:
                score = row[1][scoreIndex]
                score = score.split()
                if '/' in score:
                    score = score[len(score)-3]
                else:
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
                        if '-' == score:
                            submitted = 'not submitted'
                        else:
                            submitted = 'submitted'
                    else:
                        temp = str(score).replace(' ', '').split('/')
                        if len(temp)==2 and temp[0] != '':
                            submitted = 'submitted'
            assignment = Assignment(name, dueDate.strftime("%Y-%m-%d %H:%M:%S"), submitted, score)
            assignments[hashlib.sha1(bytes(name, 'utf-8')).hexdigest()] = assignment.__dict__
    return assignments

def main(classData, authDriver = None):
    if classData is None:
        with open('classData.json', 'r') as f:
            classData = json.load(f)
    if authDriver is None:
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    else:
        driver = authDriver

    print("Scrapping classes...")
    #try:
    # TODO: Add hashing
    newData = {class_["name"]:scrapeClass(class_, driver) for class_ in classData["classLinks"]}
    diff = DeepDiff(classData["assignments"], newData)
    if diff != {}:
        if 'type_changes' in diff:
            print('Type changes detected!')
            for key, change in diff['type_changes'].items():
                if change['old_value'] == 'submitted':
                    params = re.findall("\[\'[\w|\s]*\'\]", key)
                    class_ = params[0][2:-2]
                    id = params[1][2:-2]
                    newData[class_][id]['submitted'] = 'submitted'
        if 'values_changed' in diff:
            for key, change in diff['values_changed'].items():
                if "score" in key:
                    print("Score updated!")
                else:
                    print("Other change:", key, change)
        #diff = {type_:changes for type_, changes in diff.items() if type_ != 'type_changes' or type_ != 'values_changed'}
        if diff != {}:
            print("Changes detected!")
            print(diff)
    classData["assignments"] = newData
    # except Exception as e:
    #     print("HERE:",e)
    
    if authDriver is None:
        driver.quit()

    with open(CLASSDATA, 'w') as outfile:
        json.dump(classData, outfile, default=str, indent=4)