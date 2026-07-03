"""
General pharmacy related LangChain tools.
"""

from langchain_core.tools import tool


@tool
def pharmacy_hours() -> str:
    """
    Return pharmacy opening hours.
    """

    return (
        "Our pharmacy is open:\n"
        "Monday - Saturday: 9:00 AM to 9:00 PM\n"
        "Sunday: 10:00 AM to 4:00 PM"
    )


@tool
def delivery_information() -> str:
    """
    Return home delivery information.
    """

    return (
        "We provide home delivery within 10 km.\n"
        "Delivery usually takes 30-60 minutes."
    )


@tool
def refund_policy() -> str:
    """
    Return refund policy.
    """

    return (
        "Medicines can only be returned if they are unopened, "
        "unused, and returned within 48 hours of purchase."
    )


@tool
def contact_information() -> str:
    """
    Return pharmacy contact information.
    """

    return (
        "Phone: +91-9876543210\n"
        "Email: pharmacy@example.com\n"
        "Address: 123 Main Road, Ahmedabad"
    )


@tool
def transfer_to_pharmacist() -> str:
    """
    Mock transfer to pharmacist.
    """

    return (
        "Certainly. I'm transferring you to a pharmacist now. "
        "Please stay on the line."
    )


PHARMACY_TOOLS = [
    pharmacy_hours,
    delivery_information,
    refund_policy,
    contact_information,
    transfer_to_pharmacist,
]