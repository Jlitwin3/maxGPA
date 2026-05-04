import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import app as flask_app


def sample_course_documents():
    return [
        {
            "_id": ObjectId(),
            "term": 202203,
            "major": "MATH",
            "class": 252,
            "professors": [
                {
                    "crn": 33730,
                    "name": "Hu, Yang",
                    "grades": {"A": 10, "B": 8, "C": 3, "DNF": 1},
                },
                {
                    "crn": 33737,
                    "name": "Granath, Elliot M",
                    "grades": {"A": 33, "B": 1, "C": 0, "DNF": 0},
                },
            ],
        },
        {
            "_id": ObjectId(),
            "term": 202303,
            "major": "MATH",
            "class": 252,
            "professors": [
                {
                    "crn": 44001,
                    "name": "Hu, Yang",
                    "grades": {"A": 8, "B": 6, "C": 4, "DNF": 2},
                }
            ],
        },
    ]


class TestMaxGPAAPI(unittest.TestCase):
    def setUp(self):
        flask_app.app.config["TESTING"] = True
        self.client = flask_app.app.test_client()

    def test_database_connection(self):
        test_client = None
        try:
            test_client = MongoClient(
                flask_app.MONGO_URI,
                serverSelectionTimeoutMS=2000,
            )
            ping_result = test_client.admin.command("ping")
        except PyMongoError as error:
            self.fail(f"Could not connect to MongoDB at {flask_app.MONGO_URI}: {error}")
        finally:
            if test_client is not None:
                test_client.close()

        self.assertEqual(ping_result.get("ok"), 1.0)
        self.assertEqual(flask_app.db.name, flask_app.MONGO_DB_NAME)

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"status": "ok", "database": flask_app.MONGO_DB_NAME},
        )

    def test_list_majors(self):
        response = self.client.get("/majors")

        self.assertEqual(response.status_code, 200)
        major_keys = [item["key"] for item in response.get_json()]
        self.assertIn("cs", major_keys)
        self.assertIn("business_admin", major_keys)
        self.assertIn("math", major_keys)

    @patch.object(flask_app, "get_major_collection")
    def test_get_major_courses(self, mock_get_major_collection):
        mock_collection = MagicMock()
        mock_collection.find.return_value = sample_course_documents()
        mock_get_major_collection.return_value = mock_collection

        response = self.client.get("/majors/cs/courses?subject=MATH&class=252")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 2)
        mock_collection.find.assert_called_once()

    @patch.object(flask_app, "get_major_collection")
    def test_post_major_courses_bulk_insert(self, mock_get_major_collection):
        mock_collection = MagicMock()
        mock_collection.insert_many.return_value.inserted_ids = ["doc-1", "doc-2"]
        mock_get_major_collection.return_value = mock_collection

        payload = [
            {"term": 202203, "major": "MATH", "class": 252, "professors": []},
            {"term": 202303, "major": "MATH", "class": 252, "professors": []},
        ]
        response = self.client.post("/majors/cs/courses", json=payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["inserted_ids"], ["doc-1", "doc-2"])

    @patch.object(flask_app, "get_major_collection")
    def test_get_course_detail(self, mock_get_major_collection):
        mock_collection = MagicMock()
        mock_collection.find.return_value = sample_course_documents()
        mock_get_major_collection.return_value = mock_collection

        response = self.client.get("/majors/cs/courses/MATH/252")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["major"], "MATH")
        self.assertEqual(response.get_json()[0]["class"], 252)

    @patch.object(flask_app, "get_major_collection")
    def test_get_course_terms(self, mock_get_major_collection):
        mock_collection = MagicMock()
        mock_collection.find.return_value = sample_course_documents()
        mock_get_major_collection.return_value = mock_collection

        response = self.client.get("/majors/cs/courses/MATH/252/terms")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["terms"], [202203, 202303])

    @patch.object(flask_app, "get_major_collection")
    def test_get_course_professors(self, mock_get_major_collection):
        mock_collection = MagicMock()
        mock_collection.find.return_value = sample_course_documents()
        mock_get_major_collection.return_value = mock_collection

        response = self.client.get("/majors/cs/courses/MATH/252/professors")

        self.assertEqual(response.status_code, 200)
        professor_names = [item["name"] for item in response.get_json()]
        self.assertEqual(professor_names, ["Granath, Elliot M", "Hu, Yang"])
        self.assertEqual(response.get_json()[1]["grades"]["A"], 18)

    @patch.object(flask_app, "get_major_collection")
    def test_get_course_grade_distribution(self, mock_get_major_collection):
        mock_collection = MagicMock()
        mock_collection.find.return_value = sample_course_documents()
        mock_get_major_collection.return_value = mock_collection

        response = self.client.get("/majors/cs/courses/MATH/252/grade-distribution")

        self.assertEqual(response.status_code, 200)
        distribution = response.get_json()["grade_distribution"]
        self.assertEqual(distribution["A"], 51)
        self.assertEqual(distribution["B"], 15)
        self.assertEqual(response.get_json()["average_gpa"], 3.46)

    @patch.object(flask_app, "get_major_collection")
    def test_get_best_professors(self, mock_get_major_collection):
        mock_collection = MagicMock()
        mock_collection.find.return_value = sample_course_documents()
        mock_get_major_collection.return_value = mock_collection

        response = self.client.get("/majors/cs/courses/MATH/252/best-professors")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["name"], "Granath, Elliot M")
        self.assertGreater(
            response.get_json()[0]["average_gpa"],
            response.get_json()[1]["average_gpa"],
        )

    @patch.object(flask_app, "get_all_major_collections")
    def test_professor_courses(self, mock_get_all_major_collections):
        cs_collection = MagicMock()
        cs_collection.find.return_value = sample_course_documents()
        math_collection = MagicMock()
        math_collection.find.return_value = []
        mock_get_all_major_collections.return_value = {
            "cs": cs_collection,
            "math": math_collection,
        }

        response = self.client.get("/professors/Hu,%20Yang/courses")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 2)
        self.assertEqual(response.get_json()[0]["subject"], "MATH")

    @patch.object(flask_app, "get_all_major_collections")
    def test_professor_grade_summary(self, mock_get_all_major_collections):
        cs_collection = MagicMock()
        cs_collection.find.return_value = sample_course_documents()
        mock_get_all_major_collections.return_value = {"cs": cs_collection}

        response = self.client.get("/professors/Hu,%20Yang/grade-summary")

        self.assertEqual(response.status_code, 200)
        summary = response.get_json()
        self.assertEqual(summary["grade_distribution"]["A"], 18)
        self.assertEqual(summary["grade_distribution"]["DNF"], 3)
        self.assertEqual(summary["average_gpa"], 3.05)

    @patch.object(flask_app, "get_major_collection")
    def test_import_documents(self, mock_get_major_collection):
        mock_collection = MagicMock()
        mock_collection.insert_many.return_value.inserted_ids = ["doc-1"]
        mock_get_major_collection.return_value = mock_collection

        response = self.client.post(
            "/import/cs",
            json=[{"term": 202203, "major": "MATH", "class": 252, "professors": []}],
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["inserted_ids"], ["doc-1"])

    @patch.object(flask_app, "get_major_collection")
    def test_missing_major_collection_returns_404(self, mock_get_major_collection):
        mock_get_major_collection.return_value = None

        response = self.client.get("/majors/unknown/courses")

        self.assertEqual(response.status_code, 404)
        self.assertIn("Major collection not found", response.get_json()["error"])

    @patch.object(flask_app, "get_major_collection")
    def test_course_not_found_returns_404(self, mock_get_major_collection):
        mock_collection = MagicMock()
        mock_collection.find.return_value = []
        mock_get_major_collection.return_value = mock_collection

        response = self.client.get("/majors/cs/courses/MATH/999")

        self.assertEqual(response.status_code, 404)
        self.assertIn("Course not found", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
