import os
import sys

from flask import Flask, jsonify, request
from pymongo import MongoClient

sys.path.append("..")
from logic import get_available_years, get_full_major_report

app = Flask(__name__)

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


# Return a small service metadata response for the API root.
@app.route("/")
def index():
    return jsonify({"service": "maxGPA API", "database": MONGO_DB_NAME})


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
    app.run(debug=True)
