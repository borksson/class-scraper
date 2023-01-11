import os
import json
from string import Template
from datetime import datetime, timedelta
import re
import classScraper as classScraper
import roomScheduler
from login import login
# Local

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

TODO_FILE = classData['todoLocation']

class Todo:
    def __init__(self, title, classTitle, dueDate, finishBy, hash): # TODO: add priority
        self.title = title
        self.description = classTitle
        self.dueDate = dueDate
        self.finishBy = finishBy
        self.hash = hash

def createTodoList():
    todo = []
    future = []

    for name, assignments in classData["assignments"].items():
        for key, assignment in assignments.items():
            if assignment["submitted"] is None or assignment["submitted"] == "not submitted":
                dueDate = datetime.strptime(assignment['dueDate'], "%Y-%m-%d %H:%M:%S").date()
                finishBy = dueDate - timedelta(days=classData['defaultBuffer'])
                if finishBy.weekday() == 6:
                    finishBy = finishBy - timedelta(days=1)
                if finishBy <= datetime.now().date():
                    todo.append(Todo(assignment['name'], name, dueDate, finishBy, key).__dict__)
                elif finishBy <= datetime.now().date() + timedelta(days=classData['defaultFuture']):
                    future.append(Todo(assignment['name'], name, dueDate, finishBy, key).__dict__)

    todo = sorted(todo, key=lambda x: x['finishBy'])
    for item in todo:
        if len(item['title'])> MAXTITLE:
            item['title'] = item['title'][:MAXTITLE].strip()+"..."
        item['dueDate'] = item['dueDate'].strftime("%a, %b %d")
        item['finishBy'] = item['finishBy'].strftime("%a, %b %d")

    future = sorted(future, key=lambda x: x['finishBy'])
    for item in future:
        if len(item['title'])>MAXTITLE:
            item['title'] = item['title'][:MAXTITLE].strip()+"..."
        item['dueDate'] = item['dueDate'].strftime("%a, %b %d")
        item['finishBy'] = item['finishBy'].strftime("%a, %b %d")

    todoStrings = ["- [ ] {title} ({description}) finish by **{finishBy}**, due {dueDate} <!--{hash}-->".format(**todoItem) for todoItem in todo]
    futureStrings = ["- [ ] {title} ({description}) finish by **{finishBy}**,  due {dueDate} <!--{hash}-->".format(**todoItem) for todoItem in future]
    reservedRoomsStrings = ["- Room number {roomNumber} with {numberOfSeats} seats, starting at {start}".format(**room) for room in roomScheduler.getReservedRooms()]
    userTodoStrings = ["- [ ] "+todo for todo in classData['userTodo']]
    d = {
        'date': datetime.now().strftime("%m/%d/%Y"),
        'todoAssignments': "\n".join(todoStrings),
        'futureAssignments': "\n".join(futureStrings),
        'reserved': "\n".join(reservedRoomsStrings),
        'userTodo': "\n".join(userTodoStrings)
    }

    with open('../static/DailyTodo_TEMPLATE.md', 'r') as f:
        src = Template(f.read())
        result = src.substitute(d)

    with open(TODO_FILE, 'w') as f:
        f.write(result)

def updateClassData():
    try:
        with open(TODO_FILE, 'r') as f:
            todo = f.read()
        userTodo = True
        for line in todo.splitlines():
            # TODO: group sections with assignments and userTodo
            if line == "## Assignments":
                userTodo = False
                continue
            if line.startswith("- [ ]") and userTodo and line[6:] not in classData['userTodo']:
                classData['userTodo'].append(line[6:])
            if line.startswith("- [x]"):
                if userTodo:
                    print(line)
                    classData['userTodo'].remove(line[6:])
                else:
                    id = re.search('<!--.*-->', line).group(0)[4:-3]
                    #TODO: Remove () from classTitle
                    className = re.search('\(.*\)', line).group(0)[1:-1]
                    classData["assignments"][className][id]["submitted"] = "submitted"
    except FileNotFoundError:
        with open(TODO_FILE, 'w') as f:
            print("Creating new Daily Todo")
    
    with open(CLASSDATA, 'w') as outfile:
        json.dump(classData, outfile, default=str, indent=4)

def updateTimestamp():
    classData["lastUpdated"] = datetime.now()
    with open(CLASSDATA, 'w') as outfile:
        json.dump(classData, outfile, default=str, indent=4)

def shouldUpdate():
    return datetime.now().date() >= (datetime.strptime(classData["lastUpdated"], "%Y-%m-%d %H:%M:%S.%f").date() + timedelta(days=classData["refreshInterval"])) or FORCE

print("Scanning for changes to Daily Todo.md and update the classData")
updateClassData()

if shouldUpdate():
    # TODO: Create logged in driver
    authDriver = login()
    print("Calling classScraper.py")

    with open(CLASSDATA, 'w') as outfile:
        data = classScraper.main(classData, authDriver)
        print(data)
        json.dump(data, outfile, default=str, indent=4)
    print("Calling room_scheduler.py")
    roomScheduler.main(authDriver)
    authDriver.close()
    print("Updating the timestamp")
    updateTimestamp()

print("Creating the new Daily Todo.md")
createTodoList()
