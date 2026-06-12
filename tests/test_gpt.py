import unittest
from unittest.mock import patch

from gget.gget_gpt import gpt


class TestGpt(unittest.TestCase):
    @patch("openai.ChatCompletion.create")
    def test_gpt(self, mock_create):
        # Mock the response from the API
        mock_response = {
            "choices": [{"message": {"content": "This is a generated response."}}],
            "usage": {"total_tokens": 10},
        }
        mock_create.return_value = mock_response

        # Call the function with a prompt and test API key
        prompt = "Test prompt"
        api_key = "test_api_key"
        output = gpt(prompt, api_key)

        # Check that the mock API was called with the correct arguments
        messages = [
            {"role": "user", "content": prompt},
        ]

        mock_create.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=1,
            top_p=1,
            n=1,
            stream=False,
            stop=None,
            max_tokens=200,
            presence_penalty=0,
            frequency_penalty=0,
        )

        # Check that the output matches the mock response
        expected_output = "This is a generated response.\n"
        self.assertEqual(output, expected_output)
