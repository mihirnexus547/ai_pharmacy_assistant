import os
import sys
import re

# Ensure workspace is in Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal
from database.models import Medicine
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

def get_distinct_medicines():
    db = SessionLocal()
    try:
        # Get distinct medicines by name
        query = db.query(Medicine.name, Medicine.generic_name).all()
        seen = set()
        distinct = []
        for m in query:
            if m.name not in seen:
                seen.add(m.name)
                distinct.append((m.name, m.generic_name))
        return distinct
    finally:
        db.close()

def main():
    medicines = get_distinct_medicines()
    print(f"Found {len(medicines)} distinct medicines in database.")

    # Create knowledge_base folder
    kb_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base")
    os.makedirs(kb_dir, exist_ok=True)

    for name, generic in medicines:
        # Normalize filename
        filename = re.sub(r"[^a-zA-Z0-9_]", "", name.lower().replace(" ", "_")) + ".txt"
        filepath = os.path.join(kb_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("")
        print(f"Created empty factsheet for {name} at {filepath}")


if __name__ == "__main__":
    main()
