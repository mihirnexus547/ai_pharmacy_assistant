"""
CRUD (Repository) layer for the AI Pharmacy Assistant.

All database interactions should happen through these repositories.
"""

from typing import Optional

from sqlalchemy import select,func
from sqlalchemy.orm import Session

from database.models import Customer, Medicine, Order, OrderStatus



def get_customer_by_phone(db, phone: str):

    return (
        db.query(Customer)
        .filter(Customer.phone == phone)
        .first()
    )


def create_customer(
    db,
    name: str,
    phone: str,
):

    customer = Customer(
        name=name,
        phone=phone,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer

def create_order(
    db,
    customer_id: int,
    medicine_id: int,
    quantity: int,
):
    order = Order(
        customer_id=customer_id,
        medicine_id=medicine_id,
        quantity=quantity,
        status="Reserved",
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order

def get_order(db, order_id: int):

    return (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

def get_customer_orders(db, customer_id: int):

    return (
        db.query(Order)
        .filter(Order.customer_id == customer_id)
        .all()
    )

def cancel_order(db, order_id: int):

    order = get_order(db, order_id)

    if not order:
        return None

    order.status = "Cancelled"

    db.commit()
    db.refresh(order)

    return order

def get_medicine_by_id(db, medicine_id: int):

    return (
        db.query(Medicine)
        .filter(Medicine.id == medicine_id)
        .first()
    )

def get_medicine_by_name(db, medicine_name: str):
    """
    Get a medicine by name (case-insensitive).
    """

    return (
        db.query(Medicine)
        .filter(
            func.lower(Medicine.name) == medicine_name.lower()
        )
        .first()
    )

def get_available_medicines(db):

    return (
        db.query(Medicine)
        .filter(Medicine.stock > 0)
        .order_by(Medicine.name)
        .all()
    )

# ==========================================================
# Medicine Repository
# ==========================================================

class MedicineRepository:
    """Repository for medicine-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Medicine]:
        """Return all medicines."""
        stmt = select(Medicine).order_by(Medicine.name)
        return list(self.db.scalars(stmt).all())

    def get_by_id(self, medicine_id: int) -> Optional[Medicine]:
        """Return a medicine by ID."""
        stmt = select(Medicine).where(Medicine.id == medicine_id)
        return self.db.scalar(stmt)

    def get_by_name(self, name: str) -> Optional[Medicine]:
        """Return an exact medicine match."""
        stmt = (
            select(Medicine)
            .where(Medicine.name.ilike(name))
        )
        return self.db.scalar(stmt)

    def search(self, query: str) -> list[Medicine]:
        """Search medicines by partial name."""
        stmt = (
            select(Medicine)
            .where(Medicine.name.ilike(f"%{query}%"))
            .order_by(Medicine.name)
        )

        return list(self.db.scalars(stmt).all())

    def update_stock(self, medicine: Medicine, quantity: int) -> Medicine:
        """
        Reduce stock after reservation.

        Raises:
            ValueError: If stock is insufficient.
        """
        if medicine.stock < quantity:
            raise ValueError("Insufficient stock.")

        medicine.stock -= quantity

        self.db.commit()
        self.db.refresh(medicine)

        return medicine
    def get_available(self) -> list[Medicine]:
        stmt = (
            select(Medicine)
            .where(Medicine.stock > 0)
            .order_by(Medicine.name)
        )
        return list(self.db.scalars(stmt).all())



# ==========================================================
# Customer Repository
# ==========================================================

class CustomerRepository:
    """Repository for customer-related operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_phone(self, phone: str) -> Optional[Customer]:
        stmt = (
            select(Customer)
            .where(Customer.phone == phone)
        )
        return self.db.scalar(stmt)

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        stmt = (
            select(Customer)
            .where(Customer.id == customer_id)
        )
        return self.db.scalar(stmt)

    def create(self, name: str, phone: str) -> Customer:
        customer = Customer(
            name=name,
            phone=phone,
        )

        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        return customer

    def get_all(self) -> list[Customer]:
        stmt = select(Customer).order_by(Customer.name)
        return list(self.db.scalars(stmt).all())



# ==========================================================
# Order Repository
# ==========================================================

class OrderRepository:
    """Repository for reservation/order operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        customer_id: int,
        medicine_id: int,
        quantity: int,
    ) -> Order:
        order = Order(
            customer_id=customer_id,
            medicine_id=medicine_id,
            quantity=quantity,
            status=OrderStatus.RESERVED,
        )

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        return order

    def get_by_id(self, order_id: int) -> Optional[Order]:
        stmt = (
            select(Order)
            .where(Order.id == order_id)
        )
        return self.db.scalar(stmt)

    def history(self, customer_id: int) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(Order.reserved_at.desc())
        )

        return list(self.db.scalars(stmt).all())

    def cancel(self, order: Order) -> Order:
        order.status = OrderStatus.CANCELLED

        self.db.commit()
        self.db.refresh(order)

        return order

    def collected(self, order: Order) -> Order:
        order.status = OrderStatus.COLLECTED

        self.db.commit()
        self.db.refresh(order)

        return order

    def get_all(self) -> list[Order]:
        stmt = (
            select(Order)
            .order_by(Order.reserved_at.desc())
        )

        return list(self.db.scalars(stmt).all())