"""
Order related LangChain tools.
"""

from pydantic import BaseModel, Field
# pyrefly: ignore [missing-import]
from langchain_core.tools import tool

from database.database import SessionLocal
from database import crud
from utils.phone import validate_and_normalize_phone


# ----------------------------
# Input Schemas
# ----------------------------

from typing import Optional

class ReserveMedicineInput(BaseModel):
    phone: str = Field(description="Customer phone number")
    medicine_name: str = Field(description="Medicine name")
    quantity: int = Field(description="Quantity to reserve")
    manufacturer: Optional[str] = Field(
        default=None,
        description="Optional manufacturer name. Specify if the patient has chosen a manufacturer."
    )


class CancelOrderInput(BaseModel):
    order_id: int = Field(description="Order ID")


class CustomerOrdersInput(BaseModel):
    phone: str = Field(description="Customer phone number")


# ----------------------------
# Reserve Medicine
# ----------------------------

@tool(args_schema=ReserveMedicineInput)
def reserve_medicine(
    phone: str,
    medicine_name: str,
    quantity: int,
    manufacturer: Optional[str] = None,
) -> str:
    """
    Reserve medicine for a customer.
    If multiple manufacturers are available and manufacturer parameter is not provided, the tool will return a list of available manufacturers for the patient to choose from.
    """
    try:
        phone = validate_and_normalize_phone(phone)
    except ValueError as e:
        return f"Error: {e}"

    db = SessionLocal()

    try:
        from sqlalchemy import func
        from database.models import Medicine

        customer = crud.get_customer_by_phone(db, phone)

        if not customer:
            return "Customer not found."

        # Fetch all matching medicines by name (brand or generic)
        medicines = db.query(Medicine).filter(
            (func.lower(Medicine.name) == medicine_name.lower()) |
            (func.lower(Medicine.generic_name) == medicine_name.lower())
        ).all()

        if not medicines:
            # Try partial matching if exact name fails
            medicines = db.query(Medicine).filter(
                (Medicine.name.ilike(f"%{medicine_name}%")) |
                (Medicine.generic_name.ilike(f"%{medicine_name}%"))
            ).all()

        if not medicines:
            return f"Medicine '{medicine_name}' not found."

        # Filter by manufacturer if provided
        if manufacturer:
            matching = [m for m in medicines if manufacturer.lower() in m.manufacturer.lower()]
            if not matching:
                avail_manufacturers = ", ".join([f"{m.manufacturer} (Stock: {m.stock}, Price: ₹{m.price})" for m in medicines])
                return f"Medicine '{medicine_name}' is not available from manufacturer '{manufacturer}'. Available manufacturers are: {avail_manufacturers}. Please ask the patient to choose one."
            medicine = matching[0]
        else:
            # No manufacturer provided. If there are multiple entries with different manufacturers:
            if len(medicines) > 1:
                manufacturers_list = []
                for m in medicines:
                    manufacturers_list.append(f"{m.manufacturer} (Strength: {m.strength}, Stock: {m.stock}, Price: ₹{m.price})")
                options_str = ", ".join(manufacturers_list)
                return f"Multiple manufacturers are available for '{medicine_name}': {options_str}. Please ask the patient to choose one of these manufacturers."
            
            medicine = medicines[0]

        if medicine.stock < quantity:
            return f"Only {medicine.stock} units are available for {medicine.name} by {medicine.manufacturer}."

        medicine.stock -= quantity

        order = crud.create_order(
            db=db,
            customer_id=customer.id,
            medicine_id=medicine.id,
            quantity=quantity,
        )

        db.commit()

        return (
            f"Reservation successful.\n"
            f"Order ID: {order.id}\n"
            f"Medicine: {medicine.name} ({medicine.strength}) by {medicine.manufacturer}\n"
            f"Quantity: {quantity}"
        )

    finally:
        db.close()


# ----------------------------
# Cancel Reservation
# ----------------------------

@tool(args_schema=CancelOrderInput)
def cancel_reservation(order_id: int) -> str:
    """
    Cancel an order.
    """

    db = SessionLocal()

    try:

        order = crud.cancel_order(
            db,
            order_id,
        )

        if not order:
            return "Order not found."

        return "Reservation cancelled successfully."

    finally:

        db.close()


# ----------------------------
# Customer Orders
# ----------------------------

@tool(args_schema=CustomerOrdersInput)
def get_customer_orders(phone: str) -> str:
    """
    Return all customer reservations.
    """
    try:
        phone = validate_and_normalize_phone(phone)
    except ValueError as e:
        return f"Error: {e}"

    db = SessionLocal()

    try:

        customer = crud.get_customer_by_phone(
            db,
            phone,
        )

        if not customer:
            return "Customer not found."

        orders = crud.get_customer_orders(
            db,
            customer.id,
        )

        if not orders:
            return "No reservations found."

        response = []

        for order in orders:

            medicine = crud.get_medicine_by_id(
                db,
                order.medicine_id,
            )

            response.append(
                f"""
Order ID : {order.id}
Medicine : {medicine.name}
Quantity : {order.quantity}
Status   : {order.status}
""".strip()
            )

        return "\n\n".join(response)

    finally:

        db.close()


ORDER_TOOLS = [
    reserve_medicine,
    cancel_reservation,
    get_customer_orders,
]