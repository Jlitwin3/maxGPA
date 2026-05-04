"""
Author: Jack S
Course: CS 422
Term: Spring 26

In between Flask routes in app.py and the MongoDB implementation in db.py
Functions have simple inputs and return dicts and lists so for easy jsonify()

Required classes for a major: get_required_courses("CS_major")
Grade distribution graphs per class: generate_all_graphs_for_course()
All instructors per class: get_instructors_for_course()
Instructors with highest grades: get_instructors_for_course() sorted by highest percentage of A
Student's years: get_term_codes_in_range()
Throw exception if there is no grade data for a class: check_missing_grade_data()
Ranks professors by grade by percentage of As top to bottom: rank_instructors_by_grade()
Returns frontend data: get_full_major_report()
"""

import matplotlib
import io
import base64
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pymongo import MongoClient
import os
import sys

# Database connecting format from db.py
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB_NAME", "maxGPAdb")
_client = MongoClient(MONGO_URI)
_db = _client[MONGO_DB]
CS_col = _db["cs"]
BA_col = _db["ba"]
MATH_col = _db["math"]


# maps the major name Dacian/Jesse send us → the right collection
MAJOR_COLLECTIONS = { "CS_major": CS_col, "BA_major": BA_col, "MATH_major": MATH_col,}

# Get courses from major using subjects.py 
sys.path.append(os.path.join(os.path.dirname(__file__), 'database'))
from subjects import CS, BA, MATH

MAJOR_SUBJECTS = {"CS_major": CS, "BA_major": BA, "MATH_major": MATH}



def get_required_courses(major: str) -> list[dict]:
    """
    Return list of all required courses as dictonaries, each in the format of:
    {"subject": "CS", "number": "210", "key": "CS-210"}
    Expected input for major should be one of the keys in MAJOR_SUBJECTS
    """
    subj_map = MAJOR_SUBJECTS.get(major)
    if not subj_map:
        raise ValueError(f"No existing major: {major}")

    courses = []
    for subj, numbers in subj_map.items():
        if subj == "NAME":
            continue
        for num in numbers:
            courses.append({
                "subject": subj,
                "number":  num,
                "key":     f"{subj}-{num}",})
    return courses



def term_code_parsing(ay: str) -> list[int]:
    """
    Change AY (ex AY22) to YYYYTT format for db
    Returns integer list of term codes for the full AY
    Term codes for fall winter and spring, looks like: [202201, 202302, 202303]
    In YYYYTT -> TT = 01 (Fall), 02 (Winter), 03 (Spring)
    """
    half = int(ay[2:]) #just second half of AY22
    year_start = 2000 + half
    year_end = year_start + 1

    # fall, winter, and spring term
    return [int(f"{year_start}01"), int(f"{year_end}02"), int(f"{year_end}03")]


def get_term_codes_in_range(start_ay: str, end_ay: str) -> list[int]:
    """
    Returns the term codes for all within the given ay range inclusively, calls above function
    """
    start_year = int(start_ay[2:])
    end_year   = int(end_ay[2:])

    codes = []
    for year_short in range(start_year, end_year + 1):
        codes.extend(term_code_parsing(f"AY{year_short:02d}"))
    return codes


def get_instructors_for_course(major: str, subject: str, number: str, start_ay: str, end_ay: str) -> list[dict]:
    """
    Query the database for every professor entry for one course within the ay range
    Returns a list of dicts with instructor info in the format:
    {"name": "Kyle", "grades": {"A": 55, "B": 20, "C": 11, "DNF": 6}}

    First item of the list is an "All Instructors" entry sum of all professors and all terms in ay range
    """
    collection = MAJOR_COLLECTIONS.get(major)
    if collection is None:
        raise ValueError(f"No existing major: {major}")

    term_codes = get_term_codes_in_range(start_ay, end_ay)

    # find matches
    docs = list(collection.find({
        "major": subject,
        "class": number,
        "term": {"$in": [str(t) for t in term_codes]}}))

    # if no matches found
    if not docs:
        return []

    # totals for  all docs and all professors
    totals: dict[str, dict] = {}   

    all_grades = {"A": 0, "B": 0, "C": 0, "DNF": 0}

    for doc in docs:
        for prof in doc.get("professors", []):
            name = prof["name"]
            grades = prof["grades"]   # {"A": int, "B": int, "C": int, "DNF": int}
            if name not in totals:
                totals[name] = {"A": 0, "B": 0, "C": 0, "DNF": 0}
            for letter in ("A", "B", "C", "DNF"):
                count = grades.get(letter, 0)
                totals[name][letter] += count
                all_grades[letter]   += count

    result = [{"name": "All Instructors", "grades": all_grades}]
    for name, grades in totals.items():
        result.append({"name": name, "grades": grades})

    return result



def rank_instructors_by_grade(instructors: list[dict]) -> list[dict]:
    """
    Sort instructors with most As with the highest prof sorted first
    return inst dicts
    """
    #Can define within the func, not needed elsewhere
    def a_percentage(instructor):
        grades = instructor["grades"]
        total = sum(grades.values()) or 1
        return grades.get("A", 0) / total

    #skip the all inst
    individuals = [i for i in instructors if i["name"] != "All Instructors"]
    ranked = sorted(individuals, key=a_percentage, reverse=True)

    # always keep All Instructors at the front
    all_instr = [i for i in instructors if i["name"] == "All Instructors"]
    return all_instr + ranked #concatenate



def check_missing_grade_data(major: str, start_ay: str, end_ay: str) -> list[str]:
    """
    If a required course has ONLY asterisk (null) data, return a message for this
    Returns  warning strings list for each missing course.
    exmple is ["CS 315 is required but has no grade data available"]
    """
    warnings = []
    for course in get_required_courses(major):
        instructors = get_instructors_for_course(major, course["subject"], course["number"], start_ay, end_ay)
        if not instructors:
            warnings.append(f"{course['subject']} {course['number']} is required but has no grade data available")
    return warnings



GRADE_COLORS = {"A":   "#053C05", "B":   "#06043A", "C":   "#9109EC", "DNF": "#CC4444"}

def generate_grade_distribution(course_id: str, instructor_name: str, grade_data: dict) -> str:
    """
    Bar graph for instructor grade distributions, this function handles one prof ata time
    grade_data: {"A": int, "B": int, "C": int, "DNF": int}
    Returns a base64-encoded PNG string.
    Send it in the API response
    Renders it in the frontend as and image 
    """
    labels = ["A", "B", "C", "DNF"]
    counts = [grade_data.get(g, 0) for g in labels]
    total = sum(counts) or 1   #if sum zero then choose one no division with zero
    pcts = [round(c / total * 100) for c in counts]
    colors = [GRADE_COLORS[g] for g in labels]

    fig, ax = plt.subplots(figsize=(4, 3))
    bars = ax.bar(labels, pcts, color=colors, width=0.5)

    # Each bar labeled with percentage of that grade, shown at the top
    for bar, pct in zip(bars, pcts):
        if pct > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{pct}%",
                ha="center", va="bottom", fontsize=9,
            )

    ax.set_title(f"{course_id}\n{instructor_name}", fontsize=10, pad=6)
    ax.set_ylabel("% of students", fontsize=9)
    ax.set_ylim(0, 105)
    ax.tick_params(labelsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generate_all_graphs_for_course(major: str, subject: str, number: str, start_ay: str, end_ay: str) -> list[dict]:
    """
    Generate all the graphs for each instructors of a course including the "All Instructors" graph
    This function uses the above function and stores the pngs in dictionaries returned as a list
    format like:
    {"instructor": "All Instructors", "graph": "<base64 png>"}
    jsonify() in flask the frontend go over it to render each <img> in the list
    """
    course_id   = f"{subject} {number}"
    instructors = get_instructors_for_course(major, subject, number, start_ay, end_ay)

    graphs = []
    for entry in instructors:
        b64 = generate_grade_distribution(course_id, entry["name"], entry["grades"])
        graphs.append({"instructor": entry["name"], "graph": b64})
    return graphs



# Call this function before getting full major report, available year data needed in the dropdown menu
# before all the course data is needed for the major
def get_available_years(major: str) -> list[str]:
    """
    Return possible AY labels in the DB for a major sorted in order based on year
    format like:
    ["AY17", "AY18", ..., "AY24"]
    Frontend uses this for Start Year and End Year dropdowns so only real years can be there
    """
    collection = MAJOR_COLLECTIONS.get(major)
    if collection is None:
        raise ValueError(f"No existing major: {major}")

    term_codes = collection.distinct("term")

    ay_set = set()
    for term_str in term_codes:
        term = int(term_str)
        yyyy = term // 100
        tt   = term % 100
        if tt == 1:
            ay_year = yyyy
        else:
            ay_year = yyyy - 1
        short = ay_year - 2000
        ay_set.add(f"AY{short:02d}")

    return sorted(ay_set)


def get_full_major_report(major: str, start_ay: str, end_ay: str) -> dict:
    """
    Returns necessary frontend data in one function return:
    required courses list in order, ranked instructors + grade distribution graphs for each course,
    warnings for any courses with no data
    Can call this from one Flask route and send the whole thing to the frontend
    """
    courses = get_required_courses(major)
    warnings = check_missing_grade_data(major, start_ay, end_ay)
    report = []

    for course in courses:
        subj = course["subject"]
        number = course["number"]
        cid = f"{subj} {number}"

        # get ranked instructors from db
        instructors = get_instructors_for_course(major, subj, number, start_ay, end_ay)
        ranked = rank_instructors_by_grade(instructors)

        # graph generation for each prof.
        graphs = []
        for entry in ranked:
            b64 = generate_grade_distribution(cid, entry["name"], entry["grades"])
            graphs.append({
                "instructor": entry["name"],
                "grades": entry["grades"],
                "graph": b64})

        report.append({
            "subject": subj,
            "number": number,
            "course_id": cid,
            "instructors": graphs})

    return {
        "major":    major,
        "start_ay": start_ay,
        "end_ay":   end_ay,
        "courses":  report,
        "warnings": warnings}

 

if __name__ == "__main__":
    import base64 as _b64

    # ── fake data that mirrors what Dennis's DB would return ──────────────────
    fake_instructors_raw = [
        {"name": "Smith", "grades": {"A": 42, "B": 31, "C": 16, "DNF": 5}},
        {"name": "Patel", "grades": {"A": 20, "B": 37, "C": 18, "DNF": 8}},
        {"name": "Wang",  "grades": {"A": 55, "B": 25, "C": 12, "DNF": 4}},
        {"name": "Jones", "grades": {"A": 10, "B": 15, "C": 30, "DNF": 20}},
    ]

    all_grades = {"A": 0, "B": 0, "C": 0, "DNF": 0}
    for inst in fake_instructors_raw:
        for letter in ("A", "B", "C", "DNF"):
            all_grades[letter] += inst["grades"][letter]

    fake_instructors = [{"name": "All Instructors", "grades": all_grades}] + fake_instructors_raw

    fake_courses = [
        {"subject": "CS",   "number": "210", "key": "CS-210"},
        {"subject": "CS",   "number": "211", "key": "CS-211"},
        {"subject": "CS",   "number": "313", "key": "CS-313"},
        {"subject": "MATH", "number": "251", "key": "MATH-251"},
        {"subject": "MATH", "number": "252", "key": "MATH-252"},
    ]

    # ─────────────────────────────────────────────────────────────────────────
    print("=" * 60)
    print("TEST 1: get_required_courses")
    print("=" * 60)
    courses = get_required_courses("CS_major")
    print(f"  Found {len(courses)} required courses for CS_major")
    for c in courses[:4]:
        print(f"  {c['subject']} {c['number']}  (key: {c['key']})")
    print("  ...")
    assert len(courses) > 0, "Should have at least one course"
    print("  PASS\n")

    # ─────────────────────────────────────────────────────────────────────────
    print("=" * 60)
    print("TEST 2: rank_instructors_by_grade")
    print("=" * 60)
    ranked = rank_instructors_by_grade(fake_instructors)
    print("  Instructors ranked by A%:")
    for i, inst in enumerate(ranked):
        grades = inst["grades"]
        total  = sum(grades.values()) or 1
        a_pct  = round(grades["A"] / total * 100)
        print(f"  {i+1}. {inst['name']:20s}  A: {a_pct}%")
    assert ranked[0]["name"] == "All Instructors", "All Instructors should always be first"
    assert ranked[1]["name"] == "Wang",            "Wang has highest A% and should be #1 individual"
    assert ranked[-1]["name"] == "Jones",          "Jones has lowest A% and should be last"
    print("  PASS\n")

    # ─────────────────────────────────────────────────────────────────────────
    print("=" * 60)
    print("TEST 3: generate_grade_distribution (saves test_graph.png)")
    print("=" * 60)
    b64 = generate_grade_distribution(
        "CS 210", "Wang", {"A": 55, "B": 25, "C": 12, "DNF": 4}
    )
    assert len(b64) > 100, "base64 string should not be empty"
    with open("test_graph.png", "wb") as f:
        f.write(_b64.b64decode(b64))
    print("  Graph saved to test_graph.png — open it and check it looks right")
    print("  PASS\n")

    # ─────────────────────────────────────────────────────────────────────────
    print("=" * 60)
    print("TEST 4: generate_all_graphs_for_course (fake data, no DB)")
    print("=" * 60)
    graphs = []
    for entry in fake_instructors:
        b64 = generate_grade_distribution("CS 210", entry["name"], entry["grades"])
        graphs.append({"instructor": entry["name"], "graph": b64})

    print(f"  Generated {len(graphs)} graphs")
    for g in graphs:
        print(f"  {g['instructor']:20s}  base64 length: {len(g['graph'])}")
    assert len(graphs) == len(fake_instructors), "Should have one graph per instructor"
    assert graphs[0]["instructor"] == "All Instructors", "All Instructors should be first"
    print("  PASS\n")

    # ─────────────────────────────────────────────────────────────────────────
    print("=" * 60)
    print("TEST 5: get_full_major_report (fake data, no DB)")
    print("=" * 60)
    fake_report = {
        "major":    "CS_major",
        "start_ay": "AY22",
        "end_ay":   "AY24",
        "warnings": [],
        "courses":  []
    }

    for course in fake_courses:
        ranked = rank_instructors_by_grade(fake_instructors)
        course_graphs = []
        for entry in ranked:
            b64 = generate_grade_distribution(
                course["key"], entry["name"], entry["grades"]
            )
            course_graphs.append({
                "instructor": entry["name"],
                "grades":     entry["grades"],
                "graph":      b64,
            })
        fake_report["courses"].append({
            "subject":     course["subject"],
            "number":      course["number"],
            "course_id":   f"{course['subject']} {course['number']}",
            "instructors": course_graphs,
        })

    print(f"  Major:    {fake_report['major']}")
    print(f"  Years:    {fake_report['start_ay']} - {fake_report['end_ay']}")
    print(f"  Courses:  {len(fake_report['courses'])}")
    print()
    for c in fake_report["courses"]:
        print(f"  {c['course_id']}")
        for inst in c["instructors"]:
            grades = inst["grades"]
            total  = sum(grades.values()) or 1
            a_pct  = round(grades["A"] / total * 100)
            print(f"    {inst['instructor']:20s}  A:{a_pct}%")

    assert len(fake_report["courses"]) == len(fake_courses)
    assert fake_report["courses"][0]["instructors"][0]["instructor"] == "All Instructors"
    print("\n  PASS\n")

    # ─────────────────────────────────────────────────────────────────────────
    print("=" * 60)
    print("TEST 6: All Instructors is sum of all students not avg of avgs")
    print("=" * 60)
    expected = {"A": 0, "B": 0, "C": 0, "DNF": 0}
    for inst in fake_instructors_raw:
        for letter in ("A", "B", "C", "DNF"):
            expected[letter] += inst["grades"][letter]

    actual = next(i for i in fake_instructors if i["name"] == "All Instructors")["grades"]

    print(f"  Expected (correct sum):       {expected}")
    print(f"  Actual:                       {actual}")

    avg_of_avgs = {
        "A":   round(sum(i["grades"]["A"]   for i in fake_instructors_raw) / len(fake_instructors_raw)),
        "B":   round(sum(i["grades"]["B"]   for i in fake_instructors_raw) / len(fake_instructors_raw)),
        "C":   round(sum(i["grades"]["C"]   for i in fake_instructors_raw) / len(fake_instructors_raw)),
        "DNF": round(sum(i["grades"]["DNF"] for i in fake_instructors_raw) / len(fake_instructors_raw)),
    }
    print(f"  Wrong way (avg of avgs):      {avg_of_avgs}")

    assert actual == expected,      "All Instructors should be sum of all students"
    assert actual != avg_of_avgs,   "All Instructors should NOT be avg of averages"

    b64 = generate_grade_distribution("CS 210", "All Instructors", actual)
    with open("test_all_instructors_graph.png", "wb") as f:
        f.write(_b64.b64decode(b64))
    print("  Saved test_all_instructors_graph.png — open to verify")
    print("  PASS\n")

    # ─────────────────────────────────────────────────────────────────────────
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)