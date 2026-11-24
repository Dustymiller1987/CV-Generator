import json
import os
import unittest
from io import BytesIO
from unittest.mock import patch

from ai_writer import AIConfigurationError, improve_cv, write_cover_letter


class AIWriterTests(unittest.TestCase):
    def test_missing_api_key_is_reported(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with self.assertRaises(AIConfigurationError):
                write_cover_letter({}, "Developer")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("ai_writer.urlopen")
    def test_cover_letter_uses_cv_and_job_details(self, mocked_urlopen):
        mocked_urlopen.return_value = BytesIO(
            b'{"choices":[{"message":{"content":"A tailored letter."}}]}'
        )

        result = write_cover_letter(
            {"name": "Alex", "experience": "Retail assistant"},
            "Support Analyst",
            "Example Co",
            "Help customers resolve issues.",
            "Keep it concise.",
        )

        self.assertEqual(result, "A tailored letter.")
        request = mocked_urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        user_content = json.loads(payload["messages"][1]["content"])
        self.assertEqual(user_content["job_title"], "Support Analyst")
        self.assertEqual(user_content["candidate_cv"]["experience"], "Retail assistant")
        self.assertEqual(payload["model"], "gpt-4o-mini")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("ai_writer.urlopen")
    def test_cv_improvement_requires_all_expected_text_fields(self, mocked_urlopen):
        mocked_urlopen.return_value = BytesIO(
            b'{"choices":[{"message":{"content":"{\\"summary\\":\\"Summary\\",'
            b'\\"experience\\":\\"Experience\\",\\"skills\\":\\"Writing\\"}"}}]}'
        )

        result = improve_cv({"experience": "Original"}, "Writer")

        self.assertEqual(
            result,
            {
                "summary": "Summary",
                "experience": "Experience",
                "skills": "Writing",
            },
        )

if __name__ == "__main__":
    unittest.main()
