import sys
import unittest
from pathlib import Path

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from app import _normalize_email_or_400, signup_for_activity, unregister_from_activity


class EmailValidationTests(unittest.TestCase):
    def test_normalize_email_trims_and_lowercases(self):
        self.assertEqual(
            _normalize_email_or_400("  Student@Example.COM  "),
            "student@example.com",
        )

    def test_signup_rejects_empty_email(self):
        with self.assertRaises(HTTPException) as context:
            signup_for_activity("Chess Club", "   ", db=None)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Email is required")

    def test_unregister_rejects_empty_email(self):
        with self.assertRaises(HTTPException) as context:
            unregister_from_activity("Chess Club", "", db=None)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Email is required")


if __name__ == "__main__":
    unittest.main()
