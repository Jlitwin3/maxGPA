MaxGPA

AUTHOR: Jack Sedillos
COURSE: CS422
TERM: Spring 2026


Created logic.py, .gitignore, requirements.txt, and routing for logic.py functions in the Flask 
implementation of app.py

logic.py file sits in between Flask routes in app.py and the MongoDB implementation in db.py
Functions have simple inputs and return dicts and lists so for easy routing in Flask file app.py 


The Flask routes in app.py:

Routes show the logic.py functions as REST endpoints
GET, /majors, Gives list of supported majors in MaxGPA (CS, BA, and MATH)
GET, /years/<major_key>, Returns all of the legal academic years for a given major
POST, /report, Core route — accepts `major`, `start_ay`, `end_ay` and returns the full major report |

The `/report` route is the primary endpoint the frontend relies on. It calls `get_full_major_report()` 
from `logic.py` and returns the entire dataset — ranked professors, grade distribution graphs, and 
missing-data warnings — in a single JSON response.


logic.py functions:

get_required_courses(major)
Return list of all required courses as dictonaries, each in the format of:
{"subject": "CS", "number": "210", "key": "CS-210"}
Expected input for major should be one of the keys in MAJOR_SUBJECTS

term_code_parsing(ay)
Change AY (ex AY22) to YYYYTT format for db
Returns integer list of term codes for the full AY
Term codes for fall winter and spring, looks like: [202201, 202302, 202303]
In YYYYTT -> TT = 01 (Fall), 02 (Winter), 03 (Spring)

get_term_codes_in_range(start_ay, end_ay)
Returns the term codes for all within the given ay range inclusively, calls above function

get_instructors_for_course(major, subject, number, start_ay, end_ay)
Query the database for every professor entry for one course within the ay range
Returns a list of dicts with instructor info in the format:
{"name": "Kyle", "grades": {"A": 55, "B": 20, "C": 11, "DNF": 6}}
First item of the list is an "All Instructors" entry sum of all professors and all terms in ay range

rank_instructors_by_grade(instructors)
Sort instructors with most As with the highest prof sorted first
return inst dicts

check_missing_grade_data(major, start_ay, end_ay)
If a required course has ONLY asterisk (null) data, return a message for this
Returns  warning strings list for each missing course.
exmple is ["CS 315 is required but has no grade data available"]

generate_grade_distribution(course_id, instructor_name, grade_data)
Bar graph for instructor grade distributions, this function handles one prof ata time
grade_data: {"A": int, "B": int, "C": int, "DNF": int}
Returns a base64-encoded PNG string.
Send it in the API response
Renders it in the frontend as and image 

generate_all_graphs_for_course(major, subject, number, start_ay, end_ay)
Generate all the graphs for each instructors of a course including the "All Instructors" graph
This function uses the above function and stores the pngs in dictionaries returned as a list
format like:
{"instructor": "All Instructors", "graph": "<base64 png>"}
jsonify() in flask the frontend go over it to render each <img> in the list
    
get_available_years(major)
Return possible AY labels in the DB for a major sorted in order based on year
format like:
["AY17", "AY18", ..., "AY24"]
Frontend uses this for Start Year and End Year dropdowns so only real years can be there

get_full_major_report(major, start_ay, end_ay)
Returns necessary frontend data in one function return:
required courses list in order, ranked instructors + grade distribution graphs for each course,
warnings for any courses with no data
Can call this from one Flask route and send the whole thing to the frontend


Libraries used outside of python standard library:

matplotlib and matplotlib.pyplot
Used to generate the grade bar graphs, used in 2 functions. Matplotlib is the best Python library that can 
create quality, customizable graphs and saving them as PNGs, there's is no built-in Python alternative for
matplot

matplotlib.use("Agg")
This line is necessary becasue default Matplotlib tries to open a window to diplay the plots, but this way
setting the backend to Agg renders the graph in memory instead

io
Used to create a buffer that plt.savefig() writes the PNG into.

base64
Used to encode the raw PNG bytes from the io buffer into a base64 string. JSON doesn't carry binary data, 
so base64 encoding embeds image data in a JSON API response. The frontend gets the string and sets 
it as and src of an <img> tag 

pymongo the MongoClient
The Python implement for MongoDB. Used in logic.py to connect to the database, query collections by
term code and course, and retrieve instructor grade documents. logic.py establishes its own connection 
with the same environment variables as db.py so it can make independent querys  

os
Used to read MONGO_URI and MONGO_DB_NAME from environment variables. 

sys
Used to append  database/ subdirectory to Python's module search path so subjects.py
can be imported from a different location in the directory structure


Requirements.txt downloads needed for my section:
flask
pymongo
matplotlib
Do pip install -r requirements.txt


AI Usage for my section:
- Questioned AI about various logic throughout the project when I was stuck
- What kind of calls I could make and how to use libraries that were new to me, namley:
    - some sections of matplotlib,use("Agg") 
    - io, os, pyMongo during database implementation (database fairly new to me)
    - base64 when encoding png to json
- For testing my logic.py file I had AI write some test cases to make sure everything was
  working properly
- help with routing logic files in flask file app.py