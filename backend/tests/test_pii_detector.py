import unittest
import pandas as pd
import sys
import os

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.processor.pii_detector import (
    deidentify_text,
    deidentify_dataframe,
    verify_pii_safe,
    detect_column_pii_type,
)


class TestPIIDetectionAndDeidentification(unittest.TestCase):

    # --------------------------------------------------------------------------
    # Mandatory Required Tests from Prompt Specification
    # --------------------------------------------------------------------------

    def test_01_email_detection(self):
        """Test 1 — Email: Contact me at rahul@gmail.com -> Contact me at <EMAIL>"""
        input_text = "Contact me at rahul@gmail.com"
        expected = "Contact me at <EMAIL>"
        output, hits = deidentify_text(input_text)
        self.assertEqual(output, expected)
        self.assertIn("EMAIL", hits)
        self.assertEqual(hits["EMAIL"], 1)

    def test_02_phone_detection(self):
        """Test 2 — Phone: My mobile number is 9876543210 -> My mobile number is <PHONE_NUMBER>"""
        input_text = "My mobile number is 9876543210"
        expected = "My mobile number is <PHONE_NUMBER>"
        output, hits = deidentify_text(input_text)
        self.assertEqual(output, expected)
        self.assertIn("PHONE_NUMBER", hits)
        self.assertEqual(hits["PHONE_NUMBER"], 1)

    def test_03_pan_detection(self):
        """Test 3 — PAN: My PAN is ABCDE1234F -> My PAN is <PAN>"""
        input_text = "My PAN is ABCDE1234F"
        expected = "My PAN is <PAN>"
        output, hits = deidentify_text(input_text)
        self.assertEqual(output, expected)
        self.assertIn("PAN", hits)
        self.assertEqual(hits["PAN"], 1)

    def test_04_aadhaar_detection(self):
        """Test 4 — Aadhaar: My Aadhaar is 1234 5678 9012 -> My Aadhaar is <AADHAAR>"""
        input_text = "My Aadhaar is 1234 5678 9012"
        expected = "My Aadhaar is <AADHAAR>"
        output, hits = deidentify_text(input_text)
        self.assertEqual(output, expected)
        self.assertIn("AADHAAR", hits)
        self.assertEqual(hits["AADHAAR"], 1)

    def test_05_bank_account_detection(self):
        """Test 5 — Bank Account: My account number is 123456789012 -> My account number is <BANK_ACCOUNT>"""
        input_text = "My account number is 123456789012"
        expected = "My account number is <BANK_ACCOUNT>"
        output, hits = deidentify_text(input_text)
        self.assertEqual(output, expected)
        self.assertIn("BANK_ACCOUNT", hits)
        self.assertEqual(hits["BANK_ACCOUNT"], 1)

    def test_06_credit_card_detection(self):
        """Test 6 — Credit Card: My card is 4111 1111 1111 1111 -> My card is <CARD_NUMBER>"""
        input_text = "My card is 4111 1111 1111 1111"
        expected = "My card is <CARD_NUMBER>"
        output, hits = deidentify_text(input_text)
        self.assertEqual(output, expected)
        self.assertIn("CARD_NUMBER", hits)
        self.assertEqual(hits["CARD_NUMBER"], 1)

    # --------------------------------------------------------------------------
    # Additional Banking & Customer Sensitive Data Tests
    # --------------------------------------------------------------------------

    def test_07_cvv_detection(self):
        input_text = "My card CVV is 987"
        expected = "My card CVV is <CVV>"
        output, hits = deidentify_text(input_text)
        self.assertEqual(output, expected)
        self.assertIn("CVV", hits)

    def test_08_upi_id_detection(self):
        input_text = "Please transfer money to rahul.sharma@okhdfcbank"
        expected = "Please transfer money to <UPI_ID>"
        output, hits = deidentify_text(input_text)
        self.assertEqual(output, expected)
        self.assertIn("UPI_ID", hits)

    def test_09_passwords_and_credentials(self):
        input_text = "My password is Secret@9988 and api_key: sk-1234567890abcdef123456"
        expected = "My password is <CREDENTIALS_REDACTED> and api_key: <CREDENTIALS_REDACTED>"
        output, hits = deidentify_text(input_text)
        self.assertEqual(output, expected)
        self.assertIn("CREDENTIALS_REDACTED", hits)
        self.assertGreaterEqual(hits["CREDENTIALS_REDACTED"], 2)

    def test_10_complex_customer_query(self):
        input_text = "My name is Rahul Sharma and my account number is 123456789012. You can email me at rahul@gmail.com or call 9876543210."
        expected = "My name is <PERSON> and my account number is <BANK_ACCOUNT>. You can email me at <EMAIL> or call <PHONE_NUMBER>."
        output, hits = deidentify_text(input_text)
        self.assertEqual(output, expected)
        self.assertIn("PERSON", hits)
        self.assertIn("BANK_ACCOUNT", hits)
        self.assertIn("EMAIL", hits)
        self.assertIn("PHONE_NUMBER", hits)

    def test_11_dataframe_column_and_content_deidentification(self):
        df = pd.DataFrame([
            {
                "customer_name": "Rahul Sharma",
                "email_id": "rahul@gmail.com",
                "phone": "9876543210",
                "pan_number": "ABCDE1234F",
                "account_number": "123456789012",
                "customer_query": "My Aadhaar is 1234 5678 9012 and card is 4111 1111 1111 1111"
            }
        ])

        cleaned_df, summary = deidentify_dataframe(df)

        self.assertEqual(cleaned_df.at[0, "customer_name"], "<PERSON>")
        self.assertEqual(cleaned_df.at[0, "email_id"], "<EMAIL>")
        self.assertEqual(cleaned_df.at[0, "phone"], "<PHONE_NUMBER>")
        self.assertEqual(cleaned_df.at[0, "pan_number"], "<PAN>")
        self.assertEqual(cleaned_df.at[0, "account_number"], "<BANK_ACCOUNT>")
        self.assertEqual(cleaned_df.at[0, "customer_query"], "My Aadhaar is <AADHAAR> and card is <CARD_NUMBER>")

        self.assertTrue(summary["is_safe_for_training"])
        self.assertEqual(summary["pii_scan_status"], "PASSED")
        self.assertGreater(summary["pii_instances_detected"], 0)

        # Verification gate check
        is_safe, violations = verify_pii_safe(cleaned_df)
        self.assertTrue(is_safe)
        self.assertEqual(len(violations), 0)


if __name__ == "__main__":
    unittest.main()
