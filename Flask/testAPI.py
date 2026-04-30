import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import app as flask_app


class TestMaxGPAAPI(unittest.TestCase):
    def setUp(self):
        flask_app.app.config["TESTING"] = True
        self.client = flask_app.app.test_client()

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"status": "ok", "database": flask_app.MONGO_DB_NAME},
        )

    @patch.object(flask_app.instructors, "insert_one")
    def test_create_instructor(self, mock_insert_one):
        mock_insert_one.return_value.inserted_id = "instructor-001"

        payload = {
            "name": "Dr. Ada Lovelace",
            "email": "adalovelace@maxgpa.edu",
            "department": "Computer Science",
            "class_ids": ["CS101", "CS201"],
        }
        response = self.client.post("/instructors", json=payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json(), {"inserted_id": "instructor-001"})
        mock_insert_one.assert_called_once_with(payload)

    @patch.object(flask_app.instructors, "find")
    def test_get_instructors(self, mock_find):
        mock_find.return_value = [
            {
                "_id": "instructor-001",
                "name": "Dr. Ada Lovelace",
                "email": "adalovelace@maxgpa.edu",
                "department": "Computer Science",
                "class_ids": ["CS101", "CS201"],
            }
        ]

        response = self.client.get("/instructors")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["name"], "Dr. Ada Lovelace")

    @patch.object(flask_app.classes, "insert_one")
    def test_create_class(self, mock_insert_one):
        mock_insert_one.return_value.inserted_id = "class-001"

        payload = {
            "class_id": "CS101",
            "title": "Intro to Programming",
            "instructor_id": "instructor-001",
            "major_ids": ["CS", "SE"],
        }
        response = self.client.post("/classes", json=payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json(), {"inserted_id": "class-001"})
        mock_insert_one.assert_called_once_with(payload)

    @patch.object(flask_app.classes, "find")
    def test_get_classes(self, mock_find):
        mock_find.return_value = [
            {
                "_id": "class-001",
                "class_id": "CS101",
                "title": "Intro to Programming",
                "instructor_id": "instructor-001",
                "major_ids": ["CS", "SE"],
            }
        ]

        response = self.client.get("/classes")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["class_id"], "CS101")

    @patch.object(flask_app.grades, "insert_one")
    def test_create_grade(self, mock_insert_one):
        mock_insert_one.return_value.inserted_id = "grade-001"

        payload = {
            "student_id": "student-001",
            "class_id": "CS101",
            "instructor_id": "instructor-001",
            "grade": "A",
        }
        response = self.client.post("/grades", json=payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json(), {"inserted_id": "grade-001"})
        mock_insert_one.assert_called_once_with(payload)

    @patch.object(flask_app.grades, "find")
    def test_get_grades(self, mock_find):
        mock_find.return_value = [
            {
                "_id": "grade-001",
                "student_id": "student-001",
                "class_id": "CS101",
                "instructor_id": "instructor-001",
                "grade": "A",
            }
        ]

        response = self.client.get("/grades")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["grade"], "A")

    @patch.object(flask_app.majors, "insert_one")
    def test_create_major(self, mock_insert_one):
        mock_insert_one.return_value.inserted_id = "major-001"

        payload = {
            "major_code": "CS",
            "name": "Computer Science",
            "required_classes": ["CS101", "CS201"],
        }
        response = self.client.post("/majors", json=payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json(), {"inserted_id": "major-001"})
        mock_insert_one.assert_called_once_with(payload)

    @patch.object(flask_app.majors, "find")
    def test_get_majors(self, mock_find):
        mock_find.return_value = [
            {
                "_id": "major-001",
                "major_code": "CS",
                "name": "Computer Science",
                "required_classes": ["CS101", "CS201"],
            }
        ]

        response = self.client.get("/majors")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["major_code"], "CS")

    @patch.object(flask_app.grades, "find")
    def test_get_instructor_grades(self, mock_find):
        mock_find.return_value = [
            {
                "_id": "grade-001",
                "student_id": "student-001",
                "class_id": "CS101",
                "instructor_id": "instructor-001",
                "grade": "A",
            }
        ]

        response = self.client.get("/instructors/instructor-001/grades")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["instructor_id"], "instructor-001")
        mock_find.assert_called_once_with({"instructor_id": "instructor-001"})


if __name__ == "__main__":
    unittest.main()
