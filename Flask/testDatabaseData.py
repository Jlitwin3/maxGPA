import sys
import unittest
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import PyMongoError


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import app as flask_app


class TestDatabaseData(unittest.TestCase):
    def setUp(self):
        flask_app.app.config["TESTING"] = True
        self.client = flask_app.app.test_client()

    def test_database_has_course_data(self):
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

        course_document = None
        course_major_key = None
        for major_key, collection in flask_app.get_all_major_collections().items():
            course_document = collection.find_one({})
            if course_document is not None:
                course_major_key = major_key
                break

        self.assertIsNotNone(course_document, "No course documents found in MongoDB")
        self.assertIsNotNone(course_major_key)
        self.assertIn("term", course_document)
        self.assertIn("major", course_document)
        self.assertIn("class", course_document)
        self.assertIn("professors", course_document)
        self.assertIsInstance(course_document["professors"], list)

    def test_app_fetches_specific_course_from_database(self):
        source_document = None
        source_major_key = None
        for major_key, collection in flask_app.get_all_major_collections().items():
            source_document = collection.find_one(
                {
                    "major": {"$exists": True},
                    "class": {"$exists": True},
                    "term": {"$exists": True},
                }
            )
            if source_document is not None:
                source_major_key = major_key
                break

        self.assertIsNotNone(source_document, "No queryable course document found in MongoDB")

        subject = source_document["major"]
        class_number = source_document["class"]
        term = source_document["term"]
        documents = flask_app.get_course_documents(
            source_major_key,
            subject=subject,
            class_number=class_number,
            term=term,
        )

        self.assertGreaterEqual(len(documents), 1)
        self.assertEqual(documents[0]["major"], subject)
        self.assertEqual(str(documents[0]["class"]), str(class_number))
        self.assertEqual(documents[0]["term"], term)

        response = self.client.get(
            f"/majors/{source_major_key}/courses/{subject}/{class_number}?term={term}"
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertGreaterEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["major"], subject)
        self.assertEqual(str(response_data[0]["class"]), str(class_number))
        self.assertEqual(response_data[0]["term"], term)


if __name__ == "__main__":
    unittest.main()
