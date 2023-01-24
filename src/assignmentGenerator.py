import os
import json
import classScraper as classScraper
from simple_term_menu import TerminalMenu
from classScraper import Assignment
from datetime import datetime, timedelta
import hashlib

MAXTITLE = 30
FORCE = os.environ['FORCE'] if 'FORCE' in os.environ else False
DEBUG = os.environ['DEBUG'] if 'DEBUG' in os.environ else False
if DEBUG:
    print("DEBUG MODE ON")
    FORCE = True
    CLASSDATA = "../data/DEBUG_classData.json"
else:
    CLASSDATA = os.environ['CLASSDATA']

with open(CLASSDATA, 'r') as f:
    classData = json.load(f)

def createSchedule(schedule, time):
    dates = []
    rootDates = []
    # TODO: Ends at end of semester
    indices = [i for i in range(len(schedule)) if schedule[i] != '-']
    print(indices)
    now = datetime.now()
    today = datetime.strptime(time, "%I:%M %p")
    today = today.replace(year=now.year, month=now.month, day=now.day)
    print(today)
    for i in indices:
        day = today + timedelta(days=-today.weekday()+i, weeks=0)
        if day >= today:
            rootDates.append(day)
        else:
            rootDates.append(day + timedelta(weeks=1))
    weeksLeft = 14
    for i in range(weeksLeft):
        for date_ in rootDates:
            dates.append(date_ + timedelta(weeks=i))
    print(dates)
    return dates

def createAssignment():
    print("Class name?")
    classes = list(classData["assignments"].keys())
    # TODO: Create a class
    tm = TerminalMenu(classes)
    className = classes[tm.show()]
    print("Repeating?")
    options = ["No", "Yes"]
    tm = TerminalMenu(options)
    selection = tm.show()
    if selection==1:
        # TODO: Default weekly
        title = input("Title: ")
        time = input("Time (%I:%M %p): ")
        schedule = input("Schedule? (MTWTFSS): ")
        i = 1
        for date in createSchedule(schedule, time):
            assignment = Assignment(title+' '+str(i), date, "not submitted", None)
            classData["assignments"][className][hashlib.sha1(bytes(assignment.name, 'utf-8')).hexdigest()] = assignment.__dict__
            print("Assignment created!", assignment.__dict__)
            i+=1
    else:
        assignment = Assignment()
        assignment.name = input("Title: ")
        assignment.dueDate = datetime.strptime(input("Due date (mm/dd/yyyy HH:MM AM/PM): "), "%m/%d/%Y %I:%M %p")
        assignment.score = None
        assignment.submitted = "not submitted"
        classData["assignments"][className][hashlib.sha1(bytes(assignment.name, 'utf-8')).hexdigest()] = assignment.__dict__
        print("Assignment created!", assignment.__dict__)


while True:
    print("Assignment Generator")
    options = ["Create Assignment", "Save", "Exit"]
    tm = TerminalMenu(options)
    selection = tm.show()
    if selection == 0:
        print("Creating an Assignment")
        createAssignment()
        print("Done!")
    elif selection == 1:
        with open(CLASSDATA, 'w') as outfile:
            json.dump(classData, outfile, default=str, indent=4)
    else:
        break