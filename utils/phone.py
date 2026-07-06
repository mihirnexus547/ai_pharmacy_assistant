"""
Phone number validation and normalization utility.
"""

def validate_and_normalize_phone(phone_str: str) -> str:
    """
    Validates and normalizes phone numbers to a 10-digit format.
    Supports Indian region formatting (stripping +91 / 91 / 0 prefixes, ensuring starts with 6-9, exactly 10 digits).
    Raises ValueError with descriptive error messages on failure.
    """
    if not phone_str:
        raise ValueError("Phone number cannot be empty.")
        
    # Extract only digits
    digits = "".join(c for c in phone_str if c.isdigit())
    
    # Handle Indian country code prefix (+91 or 91)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
        
    if len(digits) != 10:
        raise ValueError(
            f"Phone number '{phone_str}' must contain exactly 10 digits (excluding country code)."
        )
        
    # Indian mobile numbers start with 6, 7, 8, or 9.
    if digits[0] not in "6789":
        raise ValueError(
            f"Phone number '{phone_str}' is invalid. For Indian regions, the number must start with 6, 7, 8, or 9."
        )
        
    return digits
