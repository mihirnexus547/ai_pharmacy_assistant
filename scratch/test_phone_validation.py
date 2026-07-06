import unittest
import sys
import os

# Add workspace root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.phone import validate_and_normalize_phone
from tools.customer_tools import get_customer, register_customer
from tools.order_tools import get_customer_orders

class TestPhoneValidation(unittest.TestCase):
    
    def test_valid_indian_numbers(self):
        # 10 digits starting with 9
        self.assertEqual(validate_and_normalize_phone("9876543210"), "9876543210")
        
        # 10 digits starting with 8
        self.assertEqual(validate_and_normalize_phone("8765432109"), "8765432109")
        
        # 10 digits starting with 7
        self.assertEqual(validate_and_normalize_phone("7654321098"), "7654321098")
        
        # 10 digits starting with 6
        self.assertEqual(validate_and_normalize_phone("6543210987"), "6543210987")
        
        # Indian region formatting with +91 prefix
        self.assertEqual(validate_and_normalize_phone("+91-9876543210"), "9876543210")
        self.assertEqual(validate_and_normalize_phone("+91 87654 32109"), "8765432109")
        
        # Indian region formatting with 91 prefix (no plus)
        self.assertEqual(validate_and_normalize_phone("919876543210"), "9876543210")
        
        # Indian region formatting with leading 0
        self.assertEqual(validate_and_normalize_phone("09876543210"), "9876543210")
        
        # Formatting with spaces and dashes
        self.assertEqual(validate_and_normalize_phone(" 9876-543-210 "), "9876543210")

    def test_invalid_phone_formats(self):
        # Too short
        with self.assertRaises(ValueError):
            validate_and_normalize_phone("12345")
            
        # Too long
        with self.assertRaises(ValueError):
            validate_and_normalize_phone("987654321012")
            
        # Invalid starting digit for mobile lines (e.g., starting with 1, 2, 3, 4, 5)
        with self.assertRaises(ValueError):
            validate_and_normalize_phone("5876543210")
            
        with self.assertRaises(ValueError):
            validate_and_normalize_phone("1876543210")
            
        # Empty inputs
        with self.assertRaises(ValueError):
            validate_and_normalize_phone("")

    def test_tool_error_handling(self):
        # Tools should catch ValueError and return a descriptive error message
        res_get = get_customer.invoke({"phone": "5876543210"})
        self.assertTrue(res_get.startswith("Error:"))
        self.assertIn("For Indian regions, the number must start with 6, 7, 8, or 9", res_get)

        res_reg = register_customer.invoke({"name": "Test User", "phone": "12345"})
        self.assertTrue(res_reg.startswith("Error:"))
        self.assertIn("must contain exactly 10 digits", res_reg)

        res_order = get_customer_orders.invoke({"phone": ""})
        self.assertTrue(res_order.startswith("Error:"))

if __name__ == "__main__":
    unittest.main()
