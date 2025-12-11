
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils

class TestUtils(unittest.TestCase):

    def test_generate_pdf_with_unicode(self):
        # Test with Unicode characters (emoji and non-latin)
        text = "This is a test report with emojis: 🚀 and non-latin: 你好."
        pdf_bytes = utils.generate_pdf(text)

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)

        # Verify that we can write to a file (optional, but good for debugging)
        with open("test_output.pdf", "wb") as f:
            f.write(pdf_bytes)

        # Check if file exists and has content
        self.assertTrue(os.path.exists("test_output.pdf"))
        self.assertGreater(os.path.getsize("test_output.pdf"), 0)

        # Clean up
        if os.path.exists("test_output.pdf"):
            os.remove("test_output.pdf")

    def test_generate_pdf_with_markdown(self):
        # Test with Markdown syntax
        text = "# Header\n\n**Bold Text**\n\n*Italic Text*"
        pdf_bytes = utils.generate_pdf(text)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)

    @patch('openai.OpenAI')
    def test_stream_deep_research(self, mock_openai):
        # Mock the OpenAI client and response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock the stream response
        mock_chunk = MagicMock()
        mock_chunk.choices[0].delta.content = "Test chunk"
        mock_stream = [mock_chunk]

        mock_client.chat.completions.create.return_value = mock_stream

        messages = [{"role": "user", "content": "Test prompt"}]

        # Consume the generator
        response = list(utils.stream_deep_research("fake_key", messages))

        self.assertEqual(response, ["Test chunk"])

        # Verify call arguments
        mock_client.chat.completions.create.assert_called_with(
            model="alibaba/tongyi-deepresearch-30b-a3b:free",
            messages=messages,
            stream=True
        )

if __name__ == '__main__':
    unittest.main()
