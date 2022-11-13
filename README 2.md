## Launch
Start the python environment

`source env/bin/activate`

Add your optimal schedule to the scheduleData.json file under optimalSchedule using the format:

```JSON
"monday": {
    "start": "1:00pm",
    "numSeats": 2,
    "floor": 1
}
```

Create a `.env` file and add your username and password information.
Use the `env_template.txt` file as an example.

Run the automated scheduler

`python roomScheduler.py`