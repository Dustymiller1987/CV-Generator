import unittest
from unittest.mock import patch

import app


class AIWritingRouteTests(unittest.TestCase):
    def test_cover_letter_route_requires_a_job_title(self):
        response = app.app.test_client().post(
            "/cover-letter",
            data={"name": "Alex", "experience": "Retail assistant"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Enter the job title", response.data)

    @patch("app.write_cover_letter", return_value="I can help your team.")
    def test_cover_letter_route_generates_a_letter_from_job_form(self, mocked_writer):
        response = app.app.test_client().post(
            "/cover-letter",
            data={
                "name": "Alex",
                "experience": "Retail assistant",
                "job_title": "Support Analyst",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"I can help your team.", response.data)
        self.assertEqual(mocked_writer.call_args.args[1], "Support Analyst")

    @patch(
        "app.improve_cv",
        return_value={
            "summary": "Improved summary",
            "experience": "Improved experience",
            "skills": "Communication",
        },
    )
    def test_cv_improvement_opens_an_editable_review(self, mocked_improve):
        response = app.app.test_client().post(
            "/improve-cv",
            data={"name": "Alex", "experience": "Original"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Improved summary", response.data)
        self.assertIn(b"Use these details in my CV", response.data)
        self.assertEqual(mocked_improve.call_args.args[0]["experience"], "Original")


if __name__ == "__main__":
    unittest.main()
