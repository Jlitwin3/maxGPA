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
        {"id": "MATH_major", "name": "Mathematics BA"},
    ])

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
