AUTHOR: Dennis Hulett; May 4th, 2026
Created adminindex.html, db.py, subjects.py, and docker-compose.yml/Dockerfile, 
as well as the contents of the Degree_Plans folder and this README.
Contributed to requirements.txt.

The Admin Page/Database

BASIC OVERVIEW:
- general overview/AI usage
- the program files
- the database
- justification of headers/systems

OVERVIEW/AI USAGE:

The Database folder and all of it's contents were created by me, including comments and function headers.
AI was prompted to help me speed up the grade data history uploading process; specifically, it wrote the flush function.
It also helped debug my adminindex js code; I do not code in js super often so a lot of my code was guesswork that
was then assisted by AI to iron out major bugs (eg. I couldn't figure out how to display uploaded filenames to the user in the
degree plan data section without it displaying the wrong thing, nor did I know how yielding data worked to show the user how many lines of the csv had been
parsed in the grade history data sction, so I asked AI to assist me). This readme was created entirely myself, with no AI usage whatsoever,
as was the structure of the databases.
Specific information regarding global variables or function variables have been commented extensively in the various files, so I'm opting
to leave that information out as to not overload the reader with technical jargon.

THE PROGRAM FILES:

== adminindex.html ==

This file is the html page for the admin interface. It allows the user to submit
grade history data as well as degree plan data (Note: There would have been a seperate
js file instead of having the script be contained entirely within the html page,
but I was running into troubles (and out of time) so I just kept it all in one file).
It will not allow the user to submit anything but a .csv file, will show the user a preview
before allowing you to commit to your submission, and will populate the database with the
relevant data to be used for the student interface.



-- functions/interactable buttons --

- section 1: grade history data - 

function switchTab(btn, name);
- this provides functionality to switch between the two tabs I built; one tab to submit
    grade distribution csv files and the other tab to submit the three degree plan csv files.

document.getElementById('submit-prev').addEventListener('click', () 
- this function sends the uploaded file to db.py, where it parses through the file 
    until it finds the first line of non-garbage data and sends it back to be shown to the user
    in a preview. If the filetype is wrong or there is no file it will alert the user and not submit. 
    When there is a successful preview, yes/no buttons appear to confirm submission.

document.getElementById('submit-btn').addEventListener('click', function (e) 
- this function is what happens when the user clicks yes after the preview appears. It sends the file
    back to db.py, where it parses through the entire file and uploads it into the database. More information regarding
    that in the db.py section. db.py will return the number of lines read as well as the number of lines inserted, which
    will be displayed to the user as it parses through the csv. Once the file is finished uploading it hides the preview
    and alerts the user of the function's completion.

document.getElementById('cancel').addEventListener('click', ()
- this function is what happens when the user click no after the preview appears. It cancels the
    file submission and allows the user to submit something else.

- section 2: degree plan data -

document.getElementById('degree-prev').addEventListener('click', ()
- this function is about the same as the 'submit-prev' function above. It sends the uploaded file to db.py,
    where the first line of data is formatted and sent back to adminindex to be previewed by the user. Non-csv files
    and no file to submit will alert the user of a failed upload, and a successful upload will display a preview and yes/no
    buttons for the user to click.

document.getElementById('dgsubmit-btn').addEventListener('click', function (e) 
- this function is about the same as the 'submit-btn' function above. It's what happens when the user confirms the validity
    of the preview shown by 'degree-prev'. It sends the file over to db.py, where it's parsed and uploaded to the database. Once complete,
    it updates the list of uploaded degree plans with the filename, hides the preview, and allows you to upload another csv file.

document.getElementById('dgcancel').addEventListener('click', ()
- this function is the same as 'cancel' above. When the user clicks no on the provided preview, it cancels the
    submission, hides the preview, and allows the user to submit something else.



== db.py ==

This file is the .py file for the admin interface. It uses flask to communicate with adminindex.html
as well as the docker_compose.yml/dockerfiles and the database. Within it contain api calls as well as 
functions used to parse csv files for the MongoDB database collections. There are four collections:
CS_major = db["cs"], BA_major = db["ba"], MATH_major = db["math"], and degreeplans = db["plan"]. 

For information regarding how the database is set up visit the database section of this txt file.

PLEASE NOTE!!!! The way that this is written has it so ONLY the applicable classes for each major are inserted into the database, rather than
every class that has a grade distribution at all. The database does not read from the degree plan csv's when uploading to the database; those are
for frontend to organize the database data to the user.
Had I looked at the online pdf sooner instead of basing my work on the paper handout I would have fixed this but given the time constaint
I just had to work around the code I had already written. It still functions as normal but do not be alarmed when the admin page tells you it only 
uploaded ~2.5k lines out of the >140k lines that are in the csv.

-- functions --

- section one: @app.route calls -

@app.route("/", methods=["GET"])
def index():
- this calls adminindex to be rendered for the user.

@app.route('/upload-endpoint', methods=['POST'])
def submit():
- calls generate() to parse through the grade history csv file provided by the user and submit all applicable data into the MongoDB database
    as documents. Returns a text stream response back to the html page to display the number of rows read/total rows.

@app.route('/upload-dg-endpoint', methods=['POST'])
def dgsubmit():
- calls dgupload() to parse through the degree plan csv file provided by the user and submit all data into the MongoDB database as
    documents. Returns nothing.

@app.route('/upload-prev', methods=['POST'])
def plan_preview():
- calls preview() to look for first applicable line of data to show and sends it back to the html to be viewed
    by the user to confirm their upload.

@app.route('/degree-prev', methods=['POST'])
def dgplan_preview():
def plan_preview():
- calls dgpreview() to look for first applicable line of data to show and sends it back to the html to be viewed
    by the user to confirm their upload.

- section two: preview functions -

def preview(file_content):
- taken from the .py file: strips the first non-garbage data row in the csv file, puts it in the same
    format as would be added to the database, and then returns it in a json format
    back to plan_preview, which will then be sent back to the html page to be dsplayed
    in a readable format for the viewer.

def dgpreview(file_content):
- taken from the .py file:  strips the first row in the csv file, puts it in the same format as would be added 
    to the database, and then returns it in a json format back to dgplan_preview, which 
    will then be sent back to the html page to be dsplayed in a readable format for the viewer.

- section three: database functions -

def dgupload(file_content):
- taken from the .py file: parses through each line in a degree plan csv and sends it's info organized
    into a MongoDB document into the database. Since the number of lines in the
    degree plans are relatively small I opted to just send one line at a time to the database, especially
    since no lines are being skipped.

def parse_grade(value):
- converts a grade value provided by condense_grades(row) to an int; if the line has no
    grade dist ('*' instead of a numeric value) then it returns none to skip that line. returns
    an int or None to condense_grades. 

def condense_grades(row):
- sum each group of +/plain/- columns into a single letter grade. Sends individual grade values to parse_grade,
    and returns none if parse_grade returns none, since that means there are no grades in that line 
    in the csv file and the line should be skipped. Called by generate and returns a dict of string:int pairs or None

def flush(batch, key):
- adds a batch (list) of documents less than or equal to the size of global variable BATCH_SIZE
    in db.py to the applicable database, found using variable key. returns number of inserted documents
    to be sent to frontend to let the user know how many lines are being parsed and added to the database.
    Is called by generate().

def generate(file_content):
- parses each line in the csv into a document and then inserts them into
    the applicable collection in the database in batches. Returns nothing, but yields data to 
    the html to be displayed to the user. Is called by submit().


== subjects.py ==

This is a py file I had written before I realized we needed to have degree plan csv's that allowed me to
sort through the csv file to add only the necessary classes for each major to the right collections in the database.
It contains no functions and is only used as a header file for db.py. For more information regarding that file please look
at the file itself; it contains a header with an explanation and sources.


== Busiess_Administration_BA.csv/Computer_Science_BA.csv/Math_BA.csv ==

These are the three degree plan csv files per the project requirements; they meet the exact
specifications from the project outline document and are uploaded to the admin page seperately from 
the grade distribution data.


THE DATABASE:

We decided to use MongoDB as our database.

Each document that is inserted into the _major collections in the db.py looks like this:
document {
        "term": term, 
        "major": subj,
        "class": numb,
        "professors": [instructor_entry]
    }

where each instructor entry looks like this: 
instructor_entry = {"crn": crn, "name": instructor, "grades": {grade_dist}}

For a practical example: in the pub_rec_master_f2015-u2025.csv file provided by the instructors, 
a particular series of lines that would be added to both the CS major as well as the MATH major is as follows:

202203,Spring 2023,MATH,252,33730,"Hu, Yang ",0,4,6,3,3,2,1,0,2,0,0,0,1,0,0,0,3,22
202203,Spring 2023,MATH,252,33731,"Dunn, Francis Charles",0,2,2,1,4,2,0,4,2,0,3,1,2,0,0,0,0,23
202203,Spring 2023,MATH,252,33732,"Brooke, Corey Tucker",1,2,2,1,3,4,2,5,1,1,2,1,4,0,1,0,1,30
202203,Spring 2023,MATH,252,33733,"Fritze, Halley Ann",0,3,0,0,4,3,3,9,3,1,3,0,2,0,4,0,0,35
202203,Spring 2023,MATH,252,33734,"Manco Berrio, Diego Fernando ",3,6,3,1,4,2,2,0,0,0,0,0,1,1,0,0,2,23
202203,Spring 2023,MATH,252,33736,"Haight, Sean Patrick Robert",3,3,1,4,5,1,1,4,3,2,2,1,1,0,2,0,1,33
202203,Spring 2023,MATH,252,33737,"Granath, Elliot M",27,6,0,1,0,0,0,0,0,0,0,0,0,0,0,0,1,34

with the key provided at the top of the csv that looks like this:
TERM,TERM_DESC,SUBJ,NUMB,CRN,INSTRUCTOR,AP,A,AM,BP,B,BM,CP,C,CM,DP,D,DM,F,P,N,OTHER,W,TOT_NON_W

In db.py, using a key that matches TERM, SUBJ, and NUMB (in this case, (202203, MATH, 252)), all of the professors for this class 
will be concatenated into a single document that looks like this*:
    {
        "term": 202203, 
        "major": MATH,
        "class": 252,
        "professors": [
            {"crn": 33730, "name": "Hu, Yang ", "grades": {A:10, B:8, C:3, DNF:1}}
            {"crn": 33731, "name": "Dunn, Francis Charles", "grades": {A:4, B:6, C:6, DNF: 6}}
            {"crn": 33732, "name": "Brooke, Corey Tucker", "grades": {A:3, B:8, C:8, DNF: 9}}
            {"crn": 33733, "name": "Fritze, Halley Ann", "grades": {A:3, B:7, C:15, DNF: 10}}
            {"crn": 33734, "name": "Manco Berrio, Diego Fernando ", "grades": {A:12, B:7, C:2, DNF:1}}
            {"crn": 33736, "name": "Haight, Sean Patrick Robert", "grades": {A:7, B:10, C:8, DNF:8}}
            {"crn": 33737, "name": "Granath, Elliot M", "grades": {A:33, B:1, C:0, DNF:0}}
        ]
    }

*I combined all of the letter grades in my head while writing this so the actual numbers might accidentally be off. 
Either way ideally the structure still gets across.

The degreeplans collection's documents are formatted like this:
document = {
            "term": term, 
            "year": year,
            "major": subj,
            "class": numb,
            "title": title
        }

where a practical example (taken from the Busiess_Administration_BA.csv file found in the Degree_Plans folder)
would be:

YEAR,TERM,SUBJ,NUMB,TITLE
1,1,BA,101Z,Introduction to Business

document = {
            "term": 1, 
            "year": 1,
            "major": BA,
            "class": 101Z,
            "title": Introduction to Business
        }

This is not how MongoDB is typically used whatsoever and I am aware of this; these concerns will be addressed in the 
justification section.


JUSTIFICATION OF HEADERS/SYSTEMS:

the adminindex.html file used no special libraries.

the db.py file uses these libraries 
import os
import csv
import io
import json
from flask import Flask, request, render_template, jsonify, Response
from pymongo import MongoClient
from subjects import CS, BA, MATH

wherein all were necessary for flask/json usage to communicate between frontend and backend, 
and the subjects was my own file I wrote in an attempt to modularize my code to be more easily updated later;
This ended up being really cumbersome once I realized you were meant to also have 
read-in degree plans but I just worked around it. 

Dockerfile/docker-compose were necessary to be able to link the database, py files, and the html 
files together.

MongoDB justification: 

Mongo is the only database I and others in my group have worked with. I am very familiar with how 
the documents work, how to set it up in dockerfiles, how to integrate it with flask/json data, and how to insert documents into the
database. Had us more time we absolutely would have used an actually structured database like SQLite, but given
the time constraint I elected to just... structure the unstructured database.