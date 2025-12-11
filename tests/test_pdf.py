import unittest
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils

class TestPDFGeneration(unittest.TestCase):
    def test_pdf_creation(self):
        text = "This is a test report."
        pdf_bytes = utils.generate_pdf(text)
        self.assertTrue(len(pdf_bytes) > 0)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    def test_unicode_handling(self):
        # Test with some unicode characters that usually break basic latin-1
        text = "Test with unicode: \u2019 \u2014 \u00A9"
        # The function should handle it without crashing (even if it replaces them)
        try:
            pdf_bytes = utils.generate_pdf(text)
            self.assertTrue(len(pdf_bytes) > 0)
        except Exception as e:
            self.fail(f"PDF generation failed with unicode input: {e}")

if __name__ == '__main__':
    unittest.main()
