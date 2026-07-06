"""
Customer related LangChain tools.
"""

from pydantic import BaseModel, Field
from langchain_core.tools import tool

from database.database import SessionLocal
from database import crud
from utils.phone import validate_and_normalize_phone


class RegisterCustomerInput(BaseModel):
    """Input schema for registering a customer."""

    name: str = Field(..., description="Customer full name")
    phone: str = Field(..., description="10 digit phone number")


class GetCustomerInput(BaseModel):
    """Input schema for fetching a customer."""

    phone: str = Field(..., description="10 digit phone number")


class UpdateCustomerInput(BaseModel):
    """Input schema for updating a customer."""

    phone: str = Field(..., description="Customer phone number")
    name: str = Field(..., description="Updated customer name")


@tool(args_schema=RegisterCustomerInput)
def register_customer(name: str, phone: str) -> str:
    """
    Register a new customer.
    """
    try:
        phone = validate_and_normalize_phone(phone)
    except ValueError as e:
        return f"Error: {e}"

    db = SessionLocal()

    try:

        customer = crud.get_customer_by_phone(db, phone)

        if customer:
            return (
                f"Customer already exists.\n"
                f"Name: {customer.name}\n"
                f"Phone: {customer.phone}"
            )

        customer = crud.create_customer(
            db=db,
            name=name,
            phone=phone,
        )

        return (
            f"Customer registered successfully.\n"
            f"Customer ID: {customer.id}"
        )

    finally:
        db.close()


@tool(args_schema=GetCustomerInput)
def get_customer(phone: str) -> str:
    """
    Retrieve customer information.
    """
    try:
        phone = validate_and_normalize_phone(phone)
    except ValueError as e:
        return f"Error: {e}"

    db = SessionLocal()

    try:

        customer = crud.get_customer_by_phone(db, phone)

        if not customer:
            return "Customer not found."

        return (
            f"Customer ID: {customer.id}\n"
            f"Name: {customer.name}\n"
            f"Phone: {customer.phone}"
        )

    finally:
        db.close()


@tool(args_schema=UpdateCustomerInput)
def update_customer(phone: str, name: str) -> str:
    """
    Update customer details.
    """
    try:
        phone = validate_and_normalize_phone(phone)
    except ValueError as e:
        return f"Error: {e}"

    db = SessionLocal()

    try:

        customer = crud.get_customer_by_phone(db, phone)

        if not customer:
            return "Customer not found."

        customer.name = name

        db.commit()
        db.refresh(customer)

        return "Customer updated successfully."

    finally:
        db.close()


CUSTOMER_TOOLS = [
    register_customer,
    get_customer,
    update_customer,
]