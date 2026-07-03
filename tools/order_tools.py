"""
Order related LangChain tools.
"""

from pydantic import BaseModel, Field
from langchain_core.tools import tool

from database.database import SessionLocal
from database import crud


# ----------------------------
# Input Schemas
# ----------------------------

class ReserveMedicineInput(BaseModel):
    phone: str = Field(description="Customer phone number")
    medicine_name: str = Field(description="Medicine name")
    quantity: int = Field(description="Quantity to reserve")


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
) -> str:
    """
    Reserve medicine for a customer.
    """

    db = SessionLocal()

    try:

        customer = crud.get_customer_by_phone(db, phone)

        if not customer:
            return "Customer not found."

        medicine = crud.get_medicine_by_name(
            db,
            medicine_name,
        )

        if not medicine:
            return "Medicine not found."

        if medicine.stock < quantity:
            return (
                f"Only {medicine.stock} units are available."
            )

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
            f"Medicine: {medicine.name}\n"
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