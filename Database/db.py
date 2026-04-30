import os
import csv
import io
import json
from flask import Flask, request, render_template, jsonify, Response
from pymongo import MongoClient
from subjects import CS, BA, MATH

app = Flask(__name__)

#database setup
client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'], 27017)
db = client.maxGPAdb

#collections
CS_major = db["cs"]
BA_major = db["ba"]
MATH_major = db["math"]

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

"""   DATABASE FUNCTIONS   """

def parse_grade(value):
    """converts a grade value to int; if the line has no
    grade dist ('*') then it returns none to skip that line"""
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
    """
    result = {}
    for letter, fields in GRADE_GROUPS.items():
        for f in fields:
            values = []
            value = parse_grade(row[f])
            if value == None:
                return None #no grade dist, return none to skip line
            values.append(value)
        result[letter] = sum(v for v in values)
    return result

def flush(batch, key):
    """adds batch of documents to collection using key
    and returns length to update lines read"""
    docs = list(batch.values())
    if not docs:
        return 0
    try:
        # ordered=False lets mongo skip duplicate-key errors and keep going
        result = COLLECTIONS[key].insert_many(docs, ordered=False)
        return len(result.inserted_ids)
    except Exception as e:
        app.logger.error(f"Batch insert error: {e}")
        return 0

@app.route('/upload-endpoint', methods=['POST'])
def submit():
    app.logger.debug("Submit to Mongo")

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be a .csv"}), 400
    file_content = file.stream.read().decode('utf-8')
    
    def generate():
        '''
        parses each line in the csv into a document and then inserts them into
        the applicable collection in the database in batches
        '''
        reader = csv.DictReader(io.StringIO(file_content))
        rows_read = 0
        total_inserted = 0

        #three dicts for each collection and a dict to store keys for each dict
        csbatch = {}
        babatch = {}
        mathbatch = {}
        BATCH = {
            "CS_major" : csbatch,
            "BA_major" : babatch,
            "MATH_major" : mathbatch
        }

        app.logger.debug(f"PARSING CSV FILE...")

        for row in reader:
            skip = True
            db_insert = []
            rows_read += 1
            term       = row["TERM"].strip()
            term_desc  = row["TERM_DESC"].strip()
            subj       = row["SUBJ"].strip()
            numb       = row["NUMB"].strip()
            crn        = row["CRN"].strip()
            instructor = row["INSTRUCTOR"].strip()    

            for item in SUBJ_GROUPS:
                if subj in item:
                        if numb in item[subj]:
                            skip = False
                            db_insert.append(item["NAME"]) 
                #"NAME" found in subjects.py is the major it falls under (eg "CS_major"); a class
                #can hypothetically fall under multiple majors so it would get added to both collections
            if skip:
                continue #skips line: class is not part of majors

            grade_dist = condense_grades(row)
            if grade_dist == None:
                continue #skips line: no grade distribution to read from

            instructor_entry = {"crn": crn, "name": instructor, "grades": grade_dist}
            key = (term, subj, numb)

            for item in db_insert:
                if key not in BATCH[item]: 
                    #BATCH[item] points to the three dicts related to each major (eg: csbatch)
                    BATCH[item][key] = {
                        "term": term, 
                        "major": subj,
                        "class": numb,
                        "professors": [instructor_entry]
                    }
                else:
                    BATCH[item][key]["professors"].append(instructor_entry)
            
            for item in db_insert:
                if rows_read % BATCH_SIZE == 0:
                    n = flush(BATCH[item], item) #sends data to db in bulk
                    total_inserted += n
                    BATCH[item] = {}
                    app.logger.debug(f"FLUSHED {item}")
                    yield f"data: {json.dumps({'rows': rows_read, 'inserted': total_inserted})}\n\n"

        # flush any remaining rows
        for item in db_insert:
            n = flush(BATCH[item], item)
            total_inserted += n
        app.logger.debug("DONE")
        yield f"data: {json.dumps({'rows': rows_read, 'inserted': total_inserted, 'done': True})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)