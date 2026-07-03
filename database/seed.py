"""
Seed the PostgreSQL database with sample data.

Run:
    python -m database.seed
"""

from random import choice, randint, sample

from faker import Faker

from database.database import SessionLocal, create_tables
from database.models import Customer, Medicine, Order, OrderStatus

fake = Faker()


# ==========================================================
# Sample Medicine Data
# ==========================================================

MEDICINES = [
    ("Paracetamol", "Acetaminophen", "500 mg"),
    ("Crocin", "Paracetamol", "500 mg"),
    ("Dolo 650", "Paracetamol", "650 mg"),
    ("Ibuprofen", "Ibuprofen", "400 mg"),
    ("Azithromycin", "Azithromycin", "500 mg"),
    ("Amoxicillin", "Amoxicillin", "500 mg"),
    ("Cetirizine", "Cetirizine", "10 mg"),
    ("Levocetirizine", "Levocetirizine", "5 mg"),
    ("Pantoprazole", "Pantoprazole", "40 mg"),
    ("Omeprazole", "Omeprazole", "20 mg"),
    ("Vitamin C", "Ascorbic Acid", "500 mg"),
    ("Vitamin D3", "Cholecalciferol", "60000 IU"),
    ("Metformin", "Metformin", "500 mg"),
    ("Amlodipine", "Amlodipine", "5 mg"),
    ("Telmisartan", "Telmisartan", "40 mg"),
    ("Losartan", "Losartan", "50 mg"),
    ("Atorvastatin", "Atorvastatin", "10 mg"),
    ("Rosuvastatin", "Rosuvastatin", "20 mg"),
    ("Ondansetron", "Ondansetron", "4 mg"),
    ("Domperidone", "Domperidone", "10 mg"),
]

MANUFACTURERS = [
    "Sun Pharma",
    "Cipla",
    "Dr. Reddy's",
    "Lupin",
    "Torrent",
    "Mankind",
    "Abbott",
    "Alkem",
    "Glenmark",
    "Zydus",
]


# ==========================================================
# Seed Medicines
# ==========================================================

def seed_medicines(db):
    """Insert sample medicines."""

    if db.query(Medicine).count() > 0:
        print("Medicines already exist.")
        return

    medicines = []

    for _ in range(100):
        name, generic, strength = choice(MEDICINES)

        medicines.append(
            Medicine(
                name=name,
                generic_name=generic,
                strength=strength,
                manufacturer=choice(MANUFACTURERS),
                price=round(randint(15, 900) + randint(0, 99) / 100, 2),
                stock=randint(0, 150),
            )
        )

    db.add_all(medicines)
    db.commit()

    print("✓ Medicines inserted")


# ==========================================================
# Seed Customers
# ==========================================================

def seed_customers(db):
    """Insert sample customers."""

    if db.query(Customer).count() > 0:
        print("Customers already exist.")
        return

    customers = []

    for _ in range(20):
        customers.append(
            Customer(
                name=fake.name(),
                phone=f"9{randint(100000000, 999999999)}",
            )
        )

    db.add_all(customers)
    db.commit()

    print("✓ Customers inserted")


# ==========================================================
# Seed Orders
# ==========================================================

def seed_orders(db):
    """Insert sample reservations."""

    if db.query(Order).count() > 0:
        print("Orders already exist.")
        return

    customers = db.query(Customer).all()
    medicines = db.query(Medicine).all()

    orders = []

    for _ in range(30):
        customer = choice(customers)
        medicine = choice(medicines)

        orders.append(
            Order(
                customer_id=customer.id,
                medicine_id=medicine.id,
                quantity=randint(1, 5),
                status=choice(list(OrderStatus)),
            )
        )

    db.add_all(orders)
    db.commit()

    print("✓ Orders inserted")


# ==========================================================
# Main
# ==========================================================

def main():
    """Create tables and seed data."""

    create_tables()

    db = SessionLocal()

    try:
        seed_medicines(db)
        seed_customers(db)
        seed_orders(db)

        print("\nDatabase seeded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    main()