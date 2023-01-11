import os
import json
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time

USERNAME = os.environ['USERNAME_BYU']
PASSWORD = os.environ['PASSWORD']

with open('../data/appData.json', 'r') as f:
    appData = json.load(f)

def login(driver = None):
    if not driver:
        options = webdriver.ChromeOptions()
        #options.add_argument('headless')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://cas.byu.edu/cas/login?service=https%3A%2F%2Flearningsuite.byu.edu%2F.ugKL%2Fstudent%2Ftop")
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
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, appData["elements"]["home"]["css"]))
    )
    return driver

def loggedIn(driver):
    try:
        driver.find_element(By.CSS_SELECTOR, appData['elements']['username']['css'])
        return False
    except:
        return True
