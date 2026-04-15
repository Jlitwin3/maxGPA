# Module imports
from flask import Flask, request, render_template, redirect, url_for
from pymongo import MongoClient

# App declaration
app = Flask(__name__)
client = MongoClient("localhost", 27017)

# Database declaration
db = client.maxGPA_database

# Collection declaration
teachers = db["teachers"]
classes = db["classes"]
grades = db["grades"]

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
