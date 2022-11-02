import os
import json
from string import Template
from datetime import datetime, timedelta

CLASSDATA = os.environ['CLASSDATA']

with open(CLASSDATA, 'r') as f:
    classData = json.load(f)

class Todo:
    def __init__(self, title, classTitle, dueDate): # TODO: add priority
        self.title = title
        self.description = classTitle
        self.dueDate = dueDate

todo = []

for name, assignments in classData["assignments"].items():
    for assignment in assignments:
        # TODO: Replace with submit logic
        dueDate = datetime.strptime(assignment['dueDate'], "%Y-%m-%d %H:%M:%S").date()
        if (dueDate + timedelta(days=2)) > datetime.today().date() and dueDate < (datetime.today().date()  + timedelta(days=int(classData['defaultBuffer']))):
            todo.append(Todo(assignment['name'], name, assignment['dueDate']).__dict__)

print(todo)
todo = sorted(todo, key=lambda x: x['dueDate'])

todoStrings = ["- [ ] {title} ({description}) due {dueDate}".format(**todoItem) for todoItem in todo]

d = {
    'date': datetime.now().strftime("%m/%d/%Y"),
    'todoAssignments': "\n".join(todoStrings),
    'futureAssignments': 'whats next'
}

with open('DailyTodo_TEMPLATE.md', 'r') as f:
    src = Template(f.read())
    result = src.substitute(d)

with open(classData['todoLocation']+'/Todo.md', 'w') as f:
    f.write(result)