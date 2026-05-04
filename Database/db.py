"""
Created by: Dennis Hulett

this file sets up the mongoDB database that is used to store
and retrieve information to display on our main user page.
it connects to adminindex.html, which is there so the user
can upload the csv file, and then parses the uploaded csv file
and stores the relevant information for our 3 selected majors 
into the database. to see relevant major data, explore the subjects.py
file and the readme inside the database file.
"""

import os
import csv
import io
import json
from flask import Flask, request, render_template, jsonify, Response
from pymongo import MongoClient
from subjects import CS, BA, MATH
import ast, re

app = Flask(__name__)

#database setup
MONGO_HOST = os.getenv("DB_PORT_27017_TCP_ADDR", "localhost")
MONGO_URI = os.getenv("MONGO_URI", f"mongodb://{MONGO_HOST}:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "maxGPAdb")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

#collections
CS_major = db["cs"]
BA_major = db["ba"]
MATH_major = db["math"]
degreeplans = db["plan"]

#keys for collections
COLLECTIONS = {
    "CS_major": CS_major,
    "BA_major": BA_major,
    "MATH_major": MATH_major,
}

#to condense grade +- into just 4 groups for graph dist
GRADE_GROUPS = {
    "A": ["AP", "A", "AM"],
    "B": ["BP", "B", "BM"],
    "C": ["CP", "C", "CM"],
    "DNF": ["DP", "D", "DM", "F"],
}

#ONLY parsing through required classes for each major
#because all other classes are irrelevant
SUBJ_GROUPS = [
    CS,
    BA,
    MATH
]

BATCH_SIZE = 1000 #accumulates batch size # of lines before pushing to db to save time

@app.route("/", methods=["GET"])
def index():
    return render_template("adminindex.html")

@app.route('/upload-endpoint', methods=['POST'])
def submit():
    """
    function (that contains a smaller function) to submit csv
    file data into the database
    """
    app.logger.debug("Submit grade data to Mongo")

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be a .csv"}), 400
    file_content = file.stream.read().decode('utf-8')

    return Response(generate(file_content), mimetype='text/event-stream')

@app.route('/upload-dg-endpoint', methods=['POST'])
def dgsubmit():
    """
    function (that contains a smaller function) to submit csv
    file data into the database
    """
    app.logger.debug("Submit degree plan to Mongo")

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be a .csv"}), 400
    file_content = file.stream.read().decode('utf-8')

    return dgupload(file_content)

@app.route('/upload-prev', methods=['POST'])
def plan_preview():
    """
    function that contains a call to preview; this is to display the uploaded
    csv file's first line as a preview to the website user. it returns a jsonified
    dict of term/subject/number/crn/instructor/grade distribution data back to the html page
    to be displayed.
    """
    file = request.files['file']

    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be a .csv"}), 400
    file_content = file.stream.read().decode('utf-8')

    return preview(file_content)

@app.route('/degree-prev', methods=['POST'])
def dgplan_preview():
    """
    function that contains a call to dgpreview; this is to display the uploaded
    csv file's first line as a preview to the website user.
    """
    file = request.files['file']

    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be a .csv"}), 400
    file_content = file.stream.read().decode('utf-8')

    return dgpreview(file_content)


"""   PREVIEW FUNCTIONS    """

def preview(file_content):
    '''
    strips the first non-garbage data row in the csv file, puts it in the same
    format as would be added to the database, and then returns it in a json format
    back to plan_preview, which will then be sent back to the html page to be dsplayed
    in a readable format for the viewer.
    '''
    reader = csv.DictReader(io.StringIO(file_content))
    for row in reader: #row is a line in the csv
        # below: stripping each part of the csv line contents
        # ideally self explanatory
        term       = row["TERM"].strip() #course term (eg: 202203)
        subj       = row["SUBJ"].strip() #class subject (eg: MATH)
        numb       = row["NUMB"].strip() #class number (eg: 252)
        crn        = row["CRN"].strip() #crn for course (eg: 33734)
        instructor = row["INSTRUCTOR"].strip() #professors name (eg: "Manco Berrio, Diego Fernando ")

        grade_dist = condense_grades(row) #returns dict of condensed grade distributions
        if grade_dist == None:
            continue #skips line: no grade distribution to read from

        instructor_entry = {"crn": crn, "name": instructor, "grades": grade_dist} #these are unique to each instructor, used for document
        result = {
                    "term": term, 
                    "major": subj,
                    "class": numb,
                    "professor": [instructor_entry]
                }
        
        return jsonify(result)

def dgpreview(file_content):
    '''
    strips the first row in the csv file, puts it in the same format as would be added 
    to the database, and then returns it in a json format back to dgplan_preview, which 
    will then be sent back to the html page to be dsplayed in a readable format for the viewer.
    '''
    reader = csv.DictReader(io.StringIO(file_content))
    for row in reader:
        term       = row["TERM"].strip() #course term (eg: 1)
        subj       = row["SUBJ"].strip() #class subject (eg: MATH)
        numb       = row["NUMB"].strip() #class number (eg: 252)
        year        = row["YEAR"].strip() #year (eg: 1)
        title = row["TITLE"].strip() #class title (eg: Integral Calculus)
        result = {
                    "term": term, 
                    "year": year,
                    "major": subj,
                    "class": numb,
                    "title": title
                }
        return jsonify(result)

"""   DATABASE FUNCTIONS   """

def dgupload(file_content):
    '''
    parses through each line in a degree plan csv and sends it's info organized
    into a MongoDB document into the database. Since the number of lines in the
    degree plans are relatively small I opted to just send one line at a time to the database, especially
    since no lines are being skipped.
    '''
    reader = csv.DictReader(io.StringIO(file_content))
    inserted = 0
    for row in reader:
        term       = row["TERM"].strip() #course term (eg: 1)
        subj       = row["SUBJ"].strip() #class subject (eg: MATH)
        numb       = row["NUMB"].strip() #class number (eg: 252)
        year        = row["YEAR"].strip() #year (eg: 1)
        title = row["TITLE"].strip() #class title (eg: Integral Calculus)
        result = { #document format to be inserted into the database
                    "term": term, 
                    "year": year,
                    "major": subj,
                    "class": numb,
                    "title": title
                }
        degreeplans.insert_one(result)
        inserted += 1
    return jsonify({"inserted": inserted})

def parse_grade(value):
    """converts a grade value to int; if the line has no
    grade dist ('*' instead of a numeric value) then it 
    returns none to skip that line.
    ex: if parse_grade is sent "4", it will return 4
    """
    if value is None:
        return None
    value = value.strip()
    if value == '*' or value == '':
        return None
    try:
        return int(value)
    except ValueError:
        return None
    
def condense_grades(row):
    """
    sum each group of +/plain/- columns into a single letter grade.
    returns none if parse grade returns none, since that means
    there are no grades in that line in the csv file
    and the line should be skipped

    a line in the csv that reads "[rest of info...] 0,4,6,3,3,2,1,0,2,0,0,0,1,0,0,0,3,22"
    will be sent to this function and return {A:10, B:8, C:3, DNF:1}
    """
    result = {} #dict to store grade/number pairs
    for letter, fields in GRADE_GROUPS.items():
        values = [] #stores number of each grade
        for f in fields: #fields: [AP, A, AM] for example. f would just be AP
            value = parse_grade(row.get(f))
            if value == None:
                return None #no grade dist, return none to skip line
            values.append(value)
        result[letter] = sum(v for v in values) #sums the values returned into one letter, so AP, A, AM all get condensed to A: [value]
    return result

def flush(batch, key):
    """adds batch of documents to collection using key
    and returns # of documents inserted to update lines read"""
    docs = list(batch.values()) #creates list of each document
    if not docs:
        return 0
    try:
        # ordered=False lets mongo skip duplicate-key errors and keep going
        result = COLLECTIONS[key].insert_many(docs, ordered=False) #COLLECTIONS[key] will identify the correct collection to insert the batch into
        return len(result.inserted_ids) #returns int to update lines read
    except Exception as e:
        app.logger.error(f"Batch insert error: {e}")
        return 0
    
def generate(file_content):
    '''
    parses each line in the csv into a document and then inserts them into
    the applicable collection in the database in batches. returns nothing
    '''
    reader = csv.DictReader(io.StringIO(file_content)) #to parse file content
    rows_read = 0 # number of rows read; used for displaying to adminindex
    total_inserted = 0 # number of rows inserted; used for displaying to adminindex

    #three dicts for each collection and a dict to store keys for each dict
    csbatch = {} #batch for cs major
    babatch = {} #batch for ba major
    mathbatch = {} #batch for math major
    BATCH = {
        "CS_major" : csbatch,
        "BA_major" : babatch,
        "MATH_major" : mathbatch
    } #same key used in subjects.py and COLLECTIONS global var to match with the correct batch dict

    app.logger.debug(f"PARSING CSV FILE...")

    for row in reader: #row is a line in the csv
        skip = True #determines whether to skip current row in reader
        db_insert = [] #becomes empty for each row, used to determine which/how many majors a class falls under
        rows_read += 1 #adds 1 for each row read, doesn't matter if row is parsed bc it still goes through the row
        # below: stripping each part of the csv line contents
        # ideally self explanatory
        term       = row["TERM"].strip() #course term (eg: 202203)
        subj       = row["SUBJ"].strip() #class subject (eg: MATH)
        numb       = row["NUMB"].strip() #class number (eg: 252)
        crn        = row["CRN"].strip() #crn for course (eg: 33734)
        instructor = row["INSTRUCTOR"].strip() #professors name (eg: "Manco Berrio, Diego Fernando ")

        for item in SUBJ_GROUPS: #item in SUBJ_GROUPS points to the dicts in subjects.py
            if subj in item: #eg: if subj is "CS" and it's looking in the BA dict, then it'll skip. if looking in CS then it won't skip
                    if numb in item[subj]: #eg: if numb is 252 and it's looking in CS[MATH], then it'll continue
                        skip = False #updates skip to NOT skip the current row
                        db_insert.append(item["NAME"]) #appends the db list with the key to access the right collection
            #"NAME" found in subjects.py is the major it falls under (eg "CS_major") which is
            # then used as a key to know which collection batch to put the document in; a class
            #can hypothetically fall under multiple majors so it would get added to both collections
        if skip:
            continue #skips line: class is not part of majors

        grade_dist = condense_grades(row) #returns dict of condensed grade distributions
        if grade_dist == None:
            continue #skips line: no grade distribution to read from

        instructor_entry = {"crn": crn, "name": instructor, "grades": grade_dist} #these are unique to each instructor, used for document
        key = (term, subj, numb) #each needed to best match same-term classes taught by differnt profs

        for item in db_insert: #inserts into each applicable major collection
            if key not in BATCH[item]: #compares keys to documents already in a batch to be submitted to the collection
                #BATCH[item] points to the three dicts related to each major (eg: csbatch)
                BATCH[item][key] = {
                    "term": term, 
                    "major": subj,
                    "class": numb,
                    "professors": [instructor_entry]
                }
            else:
                BATCH[item][key]["professors"].append(instructor_entry)
        
        for item in db_insert: #once again goes through each applicable collection to insert
            if rows_read % BATCH_SIZE == 0: 
                n = flush(BATCH[item], item) #sends data to db in bulk
                total_inserted += n
                BATCH[item] = {}
                app.logger.debug(f"FLUSHED {item}")
                yield f"data: {json.dumps({'rows': rows_read, 'inserted': total_inserted})}\n\n"

    # flush any remaining rows for every major, not only the last row's majors
    for item, batch in BATCH.items():
        if not batch:
            continue
        n = flush(batch, item)
        total_inserted += n
    app.logger.debug("DONE")
    yield f"data: {json.dumps({'rows': rows_read, 'inserted': total_inserted, 'done': True})}\n\n"


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
