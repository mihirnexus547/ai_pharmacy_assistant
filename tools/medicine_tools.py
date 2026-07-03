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
    Search for a medicine in the database.
    """

    db = SessionLocal()

    try:
        repo = crud.MedicineRepository(db)

        medicine = repo.get_by_name(medicine_name)

        if not medicine:
            return "Medicine not found."

        return f"""
            Medicine Name : {medicine.name}
            Generic Name  : {medicine.generic_name}
            Strength      : {medicine.strength}
            Manufacturer  : {medicine.manufacturer}
            Price         : ₹{medicine.price}
            Stock         : {medicine.stock}
            """.strip()

    finally:
        db.close()


# ----------------------------
# Check Stock
# ----------------------------

@tool(args_schema=CheckStockInput)
def check_stock(medicine_name: str) -> str:
    """
    Check medicine stock.
    """

    db = SessionLocal()

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


# ----------------------------
# List Medicines
# ----------------------------

@tool
def list_available_medicines() -> dict:
    """
    List all medicines currently in stock.
    """
    
    db = SessionLocal()

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

MEDICINE_TOOLS = [
    search_medicine,
    check_stock,
    list_available_medicines,
]