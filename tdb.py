import os
import json
from string import Template
from datetime import datetime, timedelta
import re
import classScraper
# Local
MAXTITLE = 30
CLASSDATA = os.environ['CLASSDATA']

with open(CLASSDATA, 'r+') as f:
    classData = json.load(f)

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

    d = {
        'date': datetime.now().strftime("%m/%d/%Y"),
        'todoAssignments': "\n".join(todoStrings),
        'futureAssignments': "\n".join(futureStrings)
    }

    with open('DailyTodo_TEMPLATE.md', 'r') as f:
        src = Template(f.read())
        result = src.substitute(d)

    with open(classData['todoLocation']+'/Todo.md', 'w') as f:
        f.write(result)

def updateClassData():
    try:
        with open(classData['todoLocation']+'/Todo.md', 'r') as f:
            todo = f.read()
    except FileNotFoundError:
        print("Todo.md not found")
        return
    
    for line in todo.splitlines():
        if line.startswith("- [x]"):
            id = re.search('<!--.*-->', line).group(0)[4:-3]
            className = re.search('\(.*\)', line).group(0)[1:-1]
            classData["assignments"][className][id]["submitted"] = "submitted"
    
    with open(CLASSDATA, 'w') as outfile:
        json.dump(classData, outfile, default=str, indent=4)



print("Scanning for changes to Todo.md and update the classData")
updateClassData()
print("Calling classScraper.py")
classScraper.main(classData)
print("Creating the new Todo.md")
createTodoList()


