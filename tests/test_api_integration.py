import importlib
import os
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class ApiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        project_root = Path(__file__).resolve().parents[1]
        src_path = project_root / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        cls.test_db = project_root / "tests" / "integration_test.db"
        if cls.test_db.exists():
            cls.test_db.unlink()

        os.environ["DATABASE_URL"] = f"sqlite:///{cls.test_db}"

        if "app" in sys.modules:
            cls.app_module = importlib.reload(sys.modules["app"])
        else:
            cls.app_module = importlib.import_module("app")

        cls.client = TestClient(cls.app_module.app)

    @classmethod
    def tearDownClass(cls):
        if cls.test_db.exists():
            cls.test_db.unlink()

    def test_signup_rejects_empty_email(self):
        response = self.client.post("/activities/Chess Club/signup", params={"email": "   "})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Email is required")

    def test_unregister_rejects_empty_email(self):
        response = self.client.delete("/activities/Chess Club/unregister", params={"email": ""})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Email is required")


if __name__ == "__main__":
    unittest.main()
