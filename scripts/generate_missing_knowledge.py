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

    kb_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base")
    os.makedirs(kb_dir, exist_ok=True)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=settings.GEMINI_API_KEY,
        temperature=0.2,
    )

    prompt_template = """Generate a highly detailed and comprehensive pharmacy factsheet for the drug {name} (generic: {generic}). 

You MUST write the content in detailed, natural paragraphs under the specified headers. Write at least 4-5 complete sentences per section to ensure a robust knowledge base.

The factsheet must contain exactly these 5 sections:

1. OVERVIEW:
Detailed description of the drug, its classification/class, biological mechanism of action (how it works in the body), and its primary characteristics.

2. INDICATIONS & USES:
All major medical conditions and symptoms it is prescribed for, official FDA-approved uses, and common off-label uses.

3. DOSAGE & ADMINISTRATION:
Standard adult and pediatric dosages, common routes of administration, how to take it (with/without food, etc.), and what to do in case of a missed dose.

4. SIDE EFFECTS:
List of potential mild, moderate, and severe side effects, symptoms of an allergic reaction, and symptoms of an overdose.

5. WARNINGS & PRECAUTIONS:
Key contraindications, pregnancy/breastfeeding safety guidelines, drug-to-drug interactions, risks associated with alcohol consumption, and when to seek immediate emergency medical attention.

Return ONLY the headers and the natural paragraphs. Do NOT use any Markdown formatting, bolding, bullet points, lists, or asterisks."""

    for name, generic in medicines:
        filename = re.sub(r"[^a-zA-Z0-9_]", "", name.lower().replace(" ", "_")) + ".txt"
        filepath = os.path.join(kb_dir, filename)

        # Check if file exists and has substantial content
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            print(f"Factsheet for {name} already exists and has content. Skipping.")
            continue

        print(f"Generating factsheet for {name} ({generic})...")
        try:
            prompt = prompt_template.format(name=name, generic=generic)
            response = llm.invoke(prompt)
            content = response.content.strip()

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Successfully generated and saved factsheet to {filepath}")
        except Exception as e:
            print(f"Failed to generate factsheet for {name}: {e}")

if __name__ == "__main__":
    main()
