"""
Business logic for pharmacy operations.
"""

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from database.crud import (
    CustomerRepository,
    MedicineRepository,
    OrderRepository,
)


class PharmacyService:
    """
    Handles pharmacy business logic.
    """

    def __init__(self, db: Session):
        self.db = db
        self.medicine_repo = MedicineRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.order_repo = OrderRepository(db)

    def search_medicine(self, name: str):
        return self.medicine_repo.get_by_name(name)

    def check_stock(self, name: str):
        medicine = self.medicine_repo.get_by_name(name)

        if medicine is None:
            return None

        return medicine.stock

    def reserve(
        self,
        phone: str,
        medicine_name: str,
        quantity: int,
    ):
        customer = self.customer_repo.get_by_phone(phone)

        if customer is None:
            return "Customer not found."

        medicine = self.medicine_repo.get_by_name(
            medicine_name
        )

        if medicine is None:
            return "Medicine not found."

        if medicine.stock < quantity:
            return (
                f"Only {medicine.stock} units available."
            )

        self.medicine_repo.update_stock(
            medicine,
            quantity,
        )

        order = self.order_repo.create(
            customer.id,
            medicine.id,
            quantity,
        )

        return order