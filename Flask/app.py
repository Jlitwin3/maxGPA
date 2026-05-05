<<<<<<< Updated upstream
import csv
import io
import json
import os
import sys

from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(BASE_DIR, "Database")
INTERFACE_DIR = os.path.join(BASE_DIR, "interface")
sys.path.append(BASE_DIR)
sys.path.append(DATABASE_DIR)

from logic import get_available_years, get_full_major_report
from subjects import BA, CS, MATH

app = Flask(__name__, template_folder=os.path.join(DATABASE_DIR, "templates"))


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

MONGO_HOST = os.getenv("DB_PORT_27017_TCP_ADDR", "localhost")
MONGO_URI = os.getenv("MONGO_URI", f"mongodb://{MONGO_HOST}:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "maxGPAdb")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

MAJOR_CONFIG = {
    "cs": {
        "id": "CS_major",
        "name": "Computer Science BA",
        "label": "CS",
        "collection": os.getenv("MONGO_COLLECTION_CS", "cs"),
    },
    "business_admin": {
        "id": "BA_major",
        "name": "Business Administration BA",
        "label": "Business Admin",
        "collection": os.getenv(
            "MONGO_COLLECTION_BA",
            os.getenv("MONGO_COLLECTION_BUSINESS_ADMIN", "ba"),
        ),
    },
    "math": {
        "id": "MATH_major",
        "name": "Mathematics BA",
        "label": "Math",
        "collection": os.getenv("MONGO_COLLECTION_MATH", "math"),
    },
}

MAJOR_ALIASES = {
    "cs": "cs",
    "cs_major": "cs",
    "computer-science": "cs",
    "computer science": "cs",
    "business": "business_admin",
    "business-admin": "business_admin",
    "business_admin": "business_admin",
    "ba": "business_admin",
    "ba_major": "business_admin",
    "math": "math",
    "math_major": "math",
    "mathematics": "math",
}

GRADE_POINTS = {
    "A": 4.0,
    "B": 3.0,
    "C": 2.0,
    "DNF": 0.0,
}

GRADE_GROUPS = {
    "A": ["AP", "A", "AM"],
    "B": ["BP", "B", "BM"],
    "C": ["CP", "C", "CM"],
    "DNF": ["DP", "D", "DM", "F"],
}

SUBJ_GROUPS = [CS, BA, MATH]
BATCH_SIZE = 1000


# Return a standardized JSON error response with the supplied HTTP status code.
def json_error(message, status_code=400):
    return jsonify({"error": message}), status_code


# Convert incoming major names or aliases into the internal major configuration key.
def normalize_major_key(major_key):
    if not major_key:
        return None
    return MAJOR_ALIASES.get(str(major_key).strip().lower())


def logic_major_id(major_key):
    normalized = normalize_major_key(major_key)
    if not normalized:
        return None
    return MAJOR_CONFIG[normalized]["id"]


# Convert a term query value into the same type used by stored MongoDB documents.
def normalize_term(term_value):
    if term_value is None:
        return None
    value = str(term_value).strip()
    if not value:
        return None
    return int(value) if value.isdigit() else value


# Build possible class-number values to match either string or integer storage.
def build_class_values(class_number):
    values = [class_number]
    if str(class_number).isdigit():
        values.append(int(class_number))
    return list(dict.fromkeys(values))


# Convert a MongoDB document into a JSON-safe dictionary.
def serialize_document(document):
    if document is None:
        return None
    serialized = dict(document)
    if "_id" in serialized:
        serialized["_id"] = str(serialized["_id"])
    return serialized


# Convert multiple MongoDB documents into JSON-safe dictionaries.
def serialize_many(documents):
    return [serialize_document(document) for document in documents]


# Return the MongoDB collection configured for a major key or alias.
def get_major_collection(major_key):
    normalized = normalize_major_key(major_key)
    if not normalized:
        return None
    return db[MAJOR_CONFIG[normalized]["collection"]]


# Return all configured major collections keyed by their internal major names.
def get_all_major_collections():
    return {
        major_key: db[config["collection"]]
        for major_key, config in MAJOR_CONFIG.items()
    }


def get_collection_by_logic_major(major_id):
    for config in MAJOR_CONFIG.values():
        if config["id"] == major_id:
            return db[config["collection"]]
    return None


def get_upload_collections():
    return {
        "CS_major": get_collection_by_logic_major("CS_major"),
        "BA_major": get_collection_by_logic_major("BA_major"),
        "MATH_major": get_collection_by_logic_major("MATH_major"),
    }


# Build a MongoDB query for optional subject, class number, and term filters.
def build_course_query(subject=None, class_number=None, term=None):
    query = {}
    if subject:
        query["major"] = str(subject).strip().upper()
    if class_number is not None:
        query["class"] = {"$in": build_class_values(class_number)}
    if term is not None:
        query["term"] = normalize_term(term)
    return query


# Fetch course documents for a major using optional course and term filters.
def get_course_documents(major_key, subject=None, class_number=None, term=None):
    collection = get_major_collection(major_key)
    if collection is None:
        return None
    query = build_course_query(subject=subject, class_number=class_number, term=term)
    return list(collection.find(query))


# Aggregate A, B, C, and DNF grade counts across course documents.
def aggregate_grade_counts(course_documents, professor_name=None):
    totals = {"A": 0, "B": 0, "C": 0, "DNF": 0}

    for document in course_documents:
        for professor in document.get("professors", []):
            if (
                professor_name
                and professor.get("name", "").strip().lower() != professor_name
            ):
                continue
            for grade_key in totals:
                totals[grade_key] += int(professor.get("grades", {}).get(grade_key, 0))

    return totals


# Compute the weighted average GPA from condensed grade counts.
def compute_average_gpa_from_counts(grade_counts):
    total_students = sum(grade_counts.values())
    if total_students == 0:
        return None

    total_points = sum(
        GRADE_POINTS[grade_key] * grade_counts.get(grade_key, 0)
        for grade_key in GRADE_POINTS
    )
    return round(total_points / total_students, 2)


# Flatten nested professor records into course-professor entries.
def flatten_professor_entries(course_documents):
    entries = []
    for document in course_documents:
        for professor in document.get("professors", []):
            entries.append(
                {
                    "term": document.get("term"),
                    "subject": document.get("major"),
                    "class": document.get("class"),
                    "crn": professor.get("crn"),
                    "name": professor.get("name"),
                    "grades": professor.get("grades", {}),
                }
            )
    return entries


# Combine professor entries across documents into one summary per professor.
def aggregate_professors(course_documents):
    aggregated = {}
    for entry in flatten_professor_entries(course_documents):
        name = entry.get("name")
        if not name:
            continue
        key = name.strip()
        professor_bucket = aggregated.setdefault(
            key,
            {
                "name": entry.get("name"),
                "terms": set(),
                "crns": set(),
                "grades": {"A": 0, "B": 0, "C": 0, "DNF": 0},
            },
        )
        professor_bucket["terms"].add(entry.get("term"))
        professor_bucket["crns"].add(entry.get("crn"))
        for grade_key in professor_bucket["grades"]:
            professor_bucket["grades"][grade_key] += int(
                entry.get("grades", {}).get(grade_key, 0)
            )

    results = []
    for professor in aggregated.values():
        results.append(
            {
                "name": professor["name"],
                "terms": sorted(
                    term for term in professor["terms"] if term is not None
                ),
                "crns": sorted(crn for crn in professor["crns"] if crn is not None),
                "grades": professor["grades"],
                "average_gpa": compute_average_gpa_from_counts(professor["grades"]),
            }
        )
    results.sort(key=lambda item: item["name"] or "")
    return results


# Rank professors by average GPA, then by number of graded students.
def rank_professors(course_documents):
    professors = aggregate_professors(course_documents)
    professors.sort(
        key=lambda item: (
            -(item["average_gpa"] if item["average_gpa"] is not None else -1),
            -sum(item["grades"].values()),
            item["name"] or "",
        )
    )
    return professors


def get_uploaded_csv_file():
    if "file" not in request.files:
        return None, json_error("No file uploaded", 400)

    uploaded_file = request.files["file"]
    if not uploaded_file.filename.endswith(".csv"):
        return None, json_error("File must be a .csv", 400)

    return uploaded_file.stream.read().decode("utf-8"), None


def parse_grade(value):
    if value is None:
        return None

    value = value.strip()
    if value == "*" or value == "":
        return None

    try:
        return int(value)
    except ValueError:
        return None


def condense_grades(row):
    result = {}
    for letter, fields in GRADE_GROUPS.items():
        values = []
        for field in fields:
            value = parse_grade(row.get(field))
            if value is None:
                return None
            values.append(value)
        result[letter] = sum(values)
    return result


def preview_grade_upload(file_content):
    reader = csv.DictReader(io.StringIO(file_content))
    for row in reader:
        grade_dist = condense_grades(row)
        if grade_dist is None:
            continue

        instructor_entry = {
            "crn": row["CRN"].strip(),
            "name": row["INSTRUCTOR"].strip(),
            "grades": grade_dist,
        }
        return jsonify(
            {
                "term": row["TERM"].strip(),
                "major": row["SUBJ"].strip(),
                "class": row["NUMB"].strip(),
                "professors": [instructor_entry],
            }
        )

    return json_error("No rows with usable grade data found", 400)


def preview_degree_plan_upload(file_content):
    reader = csv.DictReader(io.StringIO(file_content))
    for row in reader:
        return jsonify(
            {
                "term": row["TERM"].strip(),
                "year": row["YEAR"].strip(),
                "major": row["SUBJ"].strip(),
                "class": row["NUMB"].strip(),
                "title": row["TITLE"].strip(),
            }
        )

    return json_error("No degree plan rows found", 400)


def flush_upload_batch(batch, major_id):
    docs = list(batch.values())
    if not docs:
        return 0

    collection = get_upload_collections()[major_id]
    try:
        result = collection.insert_many(docs, ordered=False)
        return len(result.inserted_ids)
    except BulkWriteError as error:
        return error.details.get("nInserted", 0)


def generate_grade_upload(file_content):
    reader = csv.DictReader(io.StringIO(file_content))
    batches = {
        "CS_major": {},
        "BA_major": {},
        "MATH_major": {},
    }
    rows_read = 0
    total_inserted = 0

    for row in reader:
        rows_read += 1
        db_insert = []
        term = row["TERM"].strip()
        subj = row["SUBJ"].strip()
        numb = row["NUMB"].strip()
        crn = row["CRN"].strip()
        instructor = row["INSTRUCTOR"].strip()

        for subject_group in SUBJ_GROUPS:
            if subj in subject_group and numb in subject_group[subj]:
                db_insert.append(subject_group["NAME"])

        if not db_insert:
            continue

        grade_dist = condense_grades(row)
        if grade_dist is None:
            continue

        instructor_entry = {
            "crn": crn,
            "name": instructor,
            "grades": grade_dist,
        }
        key = (term, subj, numb)

        for major_id in db_insert:
            if key not in batches[major_id]:
                batches[major_id][key] = {
                    "term": term,
                    "major": subj,
                    "class": numb,
                    "professors": [instructor_entry],
                }
            else:
                batches[major_id][key]["professors"].append(instructor_entry)

            if rows_read % BATCH_SIZE == 0:
                inserted = flush_upload_batch(batches[major_id], major_id)
                total_inserted += inserted
                batches[major_id] = {}
                yield f"data: {json.dumps({'rows': rows_read, 'inserted': total_inserted})}\n\n"

    for major_id, batch in batches.items():
        if not batch:
            continue
        total_inserted += flush_upload_batch(batch, major_id)

    yield f"data: {json.dumps({'rows': rows_read, 'inserted': total_inserted, 'done': True})}\n\n"


def upload_degree_plan(file_content):
    reader = csv.DictReader(io.StringIO(file_content))
    documents = []
    for row in reader:
        documents.append(
            {
                "term": row["TERM"].strip(),
                "year": row["YEAR"].strip(),
                "major": row["SUBJ"].strip(),
                "class": row["NUMB"].strip(),
                "title": row["TITLE"].strip(),
            }
        )

    if not documents:
        return jsonify({"inserted": 0})

    result = db["plan"].insert_many(documents)
    return jsonify({"inserted": len(result.inserted_ids)})


# Return a small service metadata response for the API root.
@app.route("/")
def index():
    return send_from_directory(INTERFACE_DIR, "index.html")


@app.route("/app.js")
def interface_javascript():
    return send_from_directory(INTERFACE_DIR, "app.js")


@app.route("/style.css")
def interface_stylesheet():
    return send_from_directory(INTERFACE_DIR, "style.css")


@app.route("/admin")
def admin_index():
    return render_template("adminindex.html")


@app.route("/upload-prev", methods=["POST"])
def grade_upload_preview():
    file_content, error = get_uploaded_csv_file()
    if error:
        return error
    return preview_grade_upload(file_content)


@app.route("/degree-prev", methods=["POST"])
def degree_upload_preview():
    file_content, error = get_uploaded_csv_file()
    if error:
        return error
    return preview_degree_plan_upload(file_content)


@app.route("/upload-endpoint", methods=["POST"])
def upload_grade_csv():
    file_content, error = get_uploaded_csv_file()
    if error:
        return error
    return Response(generate_grade_upload(file_content), mimetype="text/event-stream")


@app.route("/upload-dg-endpoint", methods=["POST"])
def upload_degree_csv():
    file_content, error = get_uploaded_csv_file()
    if error:
        return error
    return upload_degree_plan(file_content)


# Return API health and active database information.
@app.route("/health")
def health():
    return jsonify({"status": "ok", "database": MONGO_DB_NAME})


# Return frontend report data using the shared logic module.
@app.route("/report", methods=["POST"])
def full_report():
    payload = request.get_json(force=True)
    major = payload.get("major")
    start_ay = payload.get("start_ay")
    end_ay = payload.get("end_ay")
    if not major or not start_ay or not end_ay:
        return json_error("Provide major, start_ay, and end_ay", 400)

    major_id = logic_major_id(major)
    if major_id is None:
        return json_error("Major collection not found", 404)
    return jsonify(get_full_major_report(major_id, start_ay, end_ay))


# Return available academic years for a major using the shared logic module.
@app.route("/years/<major_key>", methods=["GET"])
def available_years(major_key):
    major_id = logic_major_id(major_key)
    if major_id is None:
        return json_error("Major collection not found", 404)
    return jsonify(get_available_years(major_id))


# List the configured majors and their backing MongoDB collections.
@app.route("/majors")
def list_majors():
    return jsonify(
        [
            {
                "key": key,
                "id": config["id"],
                "name": config["name"],
                "label": config["label"],
                "collection": config["collection"],
            }
            for key, config in MAJOR_CONFIG.items()
        ]
    )


# List, filter, or bulk-create course documents for one major collection.
@app.route("/majors/<major_key>/courses", methods=["GET", "POST"])
def major_courses(major_key):
    collection = get_major_collection(major_key)
    if collection is None:
        return json_error("Major collection not found", 404)

    if request.method == "POST":
        payload = request.get_json(force=True)
        documents = payload if isinstance(payload, list) else payload.get("documents")
        if not isinstance(documents, list) or not documents:
            return json_error("Provide a non-empty list of course documents", 400)
        result = collection.insert_many(documents)
        return jsonify({"inserted_ids": [str(item) for item in result.inserted_ids]}), 201

    subject = request.args.get("subject")
    class_number = request.args.get("class")
    term = request.args.get("term")
    documents = get_course_documents(
        major_key,
        subject=subject,
        class_number=class_number,
        term=term,
    )
    documents.sort(
        key=lambda item: (
            item.get("term", 0),
            str(item.get("major", "")),
            str(item.get("class", "")),
        )
    )
    return jsonify(serialize_many(documents))


# Return all stored term records for a specific course in a major collection.
@app.route("/majors/<major_key>/courses/<subject>/<class_number>")
def major_course_detail(major_key, subject, class_number):
    documents = get_course_documents(
        major_key,
        subject=subject,
        class_number=class_number,
        term=request.args.get("term"),
    )
    if documents is None:
        return json_error("Major collection not found", 404)
    if not documents:
        return json_error("Course not found", 404)
    documents.sort(key=lambda item: item.get("term", 0))
    return jsonify(serialize_many(documents))


# Return the terms where a specific course appears in a major collection.
@app.route("/majors/<major_key>/courses/<subject>/<class_number>/terms")
def major_course_terms(major_key, subject, class_number):
    documents = get_course_documents(
        major_key,
        subject=subject,
        class_number=class_number,
    )
    if documents is None:
        return json_error("Major collection not found", 404)
    if not documents:
        return json_error("Course not found", 404)

    terms = sorted(
        {document.get("term") for document in documents if document.get("term") is not None}
    )
    return jsonify(
        {"major": major_key, "subject": subject.upper(), "class": class_number, "terms": terms}
    )


# Return professor grade summaries for a specific course.
@app.route("/majors/<major_key>/courses/<subject>/<class_number>/professors")
def major_course_professors(major_key, subject, class_number):
    documents = get_course_documents(
        major_key,
        subject=subject,
        class_number=class_number,
        term=request.args.get("term"),
    )
    if documents is None:
        return json_error("Major collection not found", 404)
    if not documents:
        return json_error("Course not found", 404)
    return jsonify(aggregate_professors(documents))


# Return aggregate grade distribution and average GPA for a specific course.
@app.route("/majors/<major_key>/courses/<subject>/<class_number>/grade-distribution")
def major_course_grade_distribution(major_key, subject, class_number):
    documents = get_course_documents(
        major_key,
        subject=subject,
        class_number=class_number,
        term=request.args.get("term"),
    )
    if documents is None:
        return json_error("Major collection not found", 404)
    if not documents:
        return json_error("Course not found", 404)

    grade_counts = aggregate_grade_counts(documents)
    return jsonify(
        {
            "major": major_key,
            "subject": subject.upper(),
            "class": class_number,
            "term": normalize_term(request.args.get("term")),
            "grade_distribution": grade_counts,
            "average_gpa": compute_average_gpa_from_counts(grade_counts),
        }
    )


# Return professors for a specific course ranked by average GPA.
@app.route("/majors/<major_key>/courses/<subject>/<class_number>/best-professors")
def major_course_best_professors(major_key, subject, class_number):
    documents = get_course_documents(
        major_key,
        subject=subject,
        class_number=class_number,
        term=request.args.get("term"),
    )
    if documents is None:
        return json_error("Major collection not found", 404)
    if not documents:
        return json_error("Course not found", 404)
    return jsonify(rank_professors(documents))


# Return all courses taught by a professor across one or all major collections.
@app.route("/professors/<path:professor_name>/courses")
def professor_courses(professor_name):
    professor_key = professor_name.strip().lower()
    major_filter = request.args.get("major")

    if major_filter:
        normalized = normalize_major_key(major_filter)
        if not normalized:
            return json_error("Major collection not found", 404)
        collections = {normalized: get_major_collection(normalized)}
    else:
        collections = get_all_major_collections()

    matches = []
    for major_key, collection in collections.items():
        documents = list(collection.find({}))
        for entry in flatten_professor_entries(documents):
            if entry.get("name", "").strip().lower() == professor_key:
                matches.append(
                    {
                        "collection_major": major_key,
                        "term": entry.get("term"),
                        "subject": entry.get("subject"),
                        "class": entry.get("class"),
                        "crn": entry.get("crn"),
                        "grades": entry.get("grades", {}),
                    }
                )

    matches.sort(
        key=lambda item: (
            item["collection_major"],
            item["term"],
            str(item["subject"]),
            str(item["class"]),
        )
    )
    return jsonify(matches)


# Return aggregate grade counts and average GPA for one professor.
@app.route("/professors/<path:professor_name>/grade-summary")
def professor_grade_summary(professor_name):
    professor_key = professor_name.strip().lower()
    major_filter = request.args.get("major")

    if major_filter:
        normalized = normalize_major_key(major_filter)
        if not normalized:
            return json_error("Major collection not found", 404)
        collections = {normalized: get_major_collection(normalized)}
    else:
        collections = get_all_major_collections()

    grade_counts = {"A": 0, "B": 0, "C": 0, "DNF": 0}
    course_count = 0

    for collection in collections.values():
        documents = list(collection.find({}))
        matched = False
        for entry in flatten_professor_entries(documents):
            if entry.get("name", "").strip().lower() != professor_key:
                continue
            matched = True
            for grade_key in grade_counts:
                grade_counts[grade_key] += int(entry.get("grades", {}).get(grade_key, 0))
        if matched:
            course_count += 1

    return jsonify(
        {
            "professor": professor_name,
            "grade_distribution": grade_counts,
            "average_gpa": compute_average_gpa_from_counts(grade_counts),
            "matched_major_collections": course_count,
        }
    )


# Import course documents directly into a major collection.
@app.route("/import/<major_key>", methods=["POST"])
def import_documents(major_key):
    collection = get_major_collection(major_key)
    if collection is None:
        return json_error("Major collection not found", 404)

    payload = request.get_json(force=True)
    documents = payload if isinstance(payload, list) else payload.get("documents")
    if not isinstance(documents, list) or not documents:
        return json_error("Provide a non-empty list of course documents", 400)

    result = collection.insert_many(documents)
    return jsonify({"inserted_ids": [str(item) for item in result.inserted_ids]}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
=======
import os

from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient

import sys
sys.path.append('..')
from logic import get_full_major_report, get_available_years

app = Flask(__name__)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "maxGPA_database")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Collection outline
instructors = db["instructors"]
classes = db["classes"]
grades = db["grades"]
majors = db["majors"]



def serialize_document(document):
    """Convert MongoDB ObjectId values into strings for JSON responses."""
    document["_id"] = str(document["_id"])
    return document


#logic.py routes
@app.route("/report", methods=["POST"])
def full_report():
    data = request.get_json()
    major = data["major"]   
    start_ay = data["start_ay"]  
    end_ay = data["end_ay"]    
    report = get_full_major_report(major, start_ay, end_ay)
    return jsonify(report)

@app.route("/majors", methods=["GET"])
def get_majors():
    return jsonify([
        {"id": "CS_major", "name": "Computer Science BA"},
        {"id": "BA_major", "name": "Business Administration BA"},
        {"id": "MATH_major", "name": "Mathematics BA"}])

@app.route("/years/<major_key>", methods=["GET"])
def available_years(major_key):
    years = get_available_years(major_key)
    return jsonify(years)


# Example schema outline:
# instructors:
#   {
#     "name": "Dr. Smith",
#     "email": "smith@school.edu",
#     "department": "Computer Science",
#     "class_ids": ["CS101", "CS201"]
#   }
#
# classes:
#   {
#     "class_id": "CS101",
#     "title": "Intro to Programming",
#     "instructor_id": "<mongo instructor _id>",
#     "major_ids": ["CS", "SE"]
#   }
#
# grades:
#   {
#     "student_id": "<student id>",
#     "class_id": "CS101",
#     "instructor_id": "<mongo instructor _id>",
#     "grade": "A"
#   }
#
# majors:
#   {
#     "major_code": "CS",
#     "name": "Computer Science",
#     "required_classes": ["CS101", "CS201"]
#   }


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "database": MONGO_DB_NAME})


@app.route("/instructors", methods=["GET", "POST"])
def instructor_collection():
    if request.method == "POST":
        payload = request.get_json(force=True)
        result = instructors.insert_one(
            {
                "name": payload.get("name"),
                "email": payload.get("email"),
                "department": payload.get("department"),
                "class_ids": payload.get("class_ids", []),
            }
        )
        return jsonify({"inserted_id": str(result.inserted_id)}), 201

    instructor_list = [serialize_document(doc) for doc in instructors.find()]
    return jsonify(instructor_list)


@app.route("/classes", methods=["GET", "POST"])
def class_collection():
    if request.method == "POST":
        payload = request.get_json(force=True)
        result = classes.insert_one(
            {
                "class_id": payload.get("class_id"),
                "title": payload.get("title"),
                "instructor_id": payload.get("instructor_id"),
                "major_ids": payload.get("major_ids", []),
            }
        )
        return jsonify({"inserted_id": str(result.inserted_id)}), 201

    class_list = [serialize_document(doc) for doc in classes.find()]
    return jsonify(class_list)


@app.route("/grades", methods=["GET", "POST"])
def grade_collection():
    if request.method == "POST":
        payload = request.get_json(force=True)
        result = grades.insert_one(
            {
                "student_id": payload.get("student_id"),
                "class_id": payload.get("class_id"),
                "instructor_id": payload.get("instructor_id"),
                "grade": payload.get("grade"),
            }
        )
        return jsonify({"inserted_id": str(result.inserted_id)}), 201

    grade_list = [serialize_document(doc) for doc in grades.find()]
    return jsonify(grade_list)


@app.route("/majors", methods=["GET", "POST"])
def major_collection():
    if request.method == "POST":
        payload = request.get_json(force=True)
        result = majors.insert_one(
            {
                "major_code": payload.get("major_code"),
                "name": payload.get("name"),
                "required_classes": payload.get("required_classes", []),
            }
        )
        return jsonify({"inserted_id": str(result.inserted_id)}), 201

    major_list = [serialize_document(doc) for doc in majors.find()]
    return jsonify(major_list)


@app.route("/instructors/<instructor_id>/grades", methods=["GET"])
def instructor_grades(instructor_id):
    """Return all grade records for the classes taught by one instructor."""
    grade_list = [
        serialize_document(doc)
        for doc in grades.find({"instructor_id": instructor_id})
    ]
    return jsonify(grade_list)


if __name__ == "__main__":
    app.run(debug=True)
>>>>>>> Stashed changes
