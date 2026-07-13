"""
Medicine related LangChain tools.
"""

# pyrefly: ignore [missing-import]
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from database.database import SessionLocal
from database import crud


# ----------------------------
# Input Schemas
# ----------------------------

class SearchMedicineInput(BaseModel):
    medicine_name: str = Field(
        description="Name of the medicine."
    )


class CheckStockInput(BaseModel):
    medicine_name: str = Field(
        description="Name of the medicine."
    )


# ----------------------------
# Search Medicine
# ----------------------------

@tool(args_schema=SearchMedicineInput)
def search_medicine(medicine_name: str) -> str:
    """
    Search for a medicine in the database. Returns all matching entries including manufacturer, strength, price, and stock.
    """

    db = SessionLocal()
    import time
    from services.logger import logger
    sql_start = time.perf_counter()

    try:
        from sqlalchemy import func
        from database.models import Medicine

        # Fetch all matching medicines by name or generic name
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
            return "Medicine not found."

        result = []
        for m in medicines:
            result.append(
                f"Brand Name: {m.name}, Generic Name: {m.generic_name}, Strength: {m.strength}, Manufacturer: {m.manufacturer}, Price: ₹{m.price}, Stock: {m.stock}"
            )
        
        return "\n".join(result)

    finally:
        db.close()
        logger.info(f"[Latency] SQL Execution (search_medicine) took: {(time.perf_counter() - sql_start) * 1000:.2f} ms")


# ----------------------------
# Check Stock
# ----------------------------

@tool(args_schema=CheckStockInput)
def check_stock(medicine_name: str) -> str:
    """
    Check medicine stock.
    """

    db = SessionLocal()
    import time
    from services.logger import logger
    sql_start = time.perf_counter()

    try:
        repo = crud.MedicineRepository(db)

        medicine = repo.get_by_name(medicine_name)

        if not medicine:
            return "Medicine not found."

        return (
            f"{medicine.name} has "
            f"{medicine.stock} units available."
        )

    finally:
        db.close()
        logger.info(f"[Latency] SQL Execution (check_stock) took: {(time.perf_counter() - sql_start) * 1000:.2f} ms")


# ----------------------------
# List Medicines
# ----------------------------

@tool
def list_available_medicines() -> dict:
    """
    List all medicines currently in stock.
    """
    
    db = SessionLocal()
    import time
    from services.logger import logger
    sql_start = time.perf_counter()

    try:
        repo = crud.MedicineRepository(db)

        medicines = [
            medicine.name
            for medicine in repo.get_all()
            if medicine.stock > 0
        ]

        return {
            "available_medicines": medicines
        }

    finally:
        db.close()
        logger.info(f"[Latency] SQL Execution (list_available_medicines) took: {(time.perf_counter() - sql_start) * 1000:.2f} ms")

MEDICINE_TOOLS = [
    search_medicine,
    check_stock,
    list_available_medicines,
]