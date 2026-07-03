"""
RAG tools for querying medicine knowledge base.
"""

import os
import re
import json
import numpy as np
from google import genai
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from database.database import SessionLocal
from database.models import Medicine
from app.config import settings

# Absolute path to knowledge base directory
KB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base")

# Global embeddings cache
_embeddings_cache = None

def load_embeddings_cache():
    global _embeddings_cache
    if _embeddings_cache is not None:
        return _embeddings_cache
    
    cache_path = os.path.join(KB_DIR, "embeddings_cache.json")
    if not os.path.exists(cache_path):
        return []
    
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            _embeddings_cache = json.load(f)
        return _embeddings_cache
    except Exception as e:
        print(f"Error loading embeddings cache: {e}")
        return []

def get_first_few_sentences(text: str, n: int = 2) -> str:
    """Helper to extract the first few sentences of a text block."""
    if not text:
        return ""
    # Split by period followed by whitespace
    sentences = re.split(r'\.\s+', text.strip())
    snippet = ". ".join(sentences[:n])
    if len(sentences) > n and not snippet.endswith('.'):
        snippet += "."
    return snippet

class GetDrugKnowledgeInput(BaseModel):
    medicine_name: str = Field(
        description="The name of the medicine (brand name or generic name, e.g. Paracetamol, Dolo 650, Ibuprofen)."
    )

class SearchDrugByIndicationInput(BaseModel):
    symptom_or_use: str = Field(
        description="The symptom, medical condition, or indication to search for (e.g. fever, headache, high blood pressure, allergy)."
    )

@tool(args_schema=GetDrugKnowledgeInput)
def get_drug_knowledge(medicine_name: str) -> str:
    """
    Retrieve detailed medical knowledge (uses, dosage, side effects, precautions) for a specific drug name or generic name.
    """
    if not os.path.exists(KB_DIR):
        return "Knowledge base directory not found."

    # Step 1: Normalize input name
    norm_input = re.sub(r"[^a-zA-Z0-9_]", "", medicine_name.lower().replace(" ", "_"))

    # Step 2: Try direct file match
    direct_file = os.path.join(KB_DIR, f"{norm_input}.txt")
    if os.path.exists(direct_file):
        try:
            with open(direct_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return content if content else f"I found the factsheet for {medicine_name}, but it is currently empty."
        except Exception as e:
            return f"Error reading factsheet: {e}"

    # Step 3: Try to match substrings in existing factsheet filenames
    try:
        files = os.listdir(KB_DIR)
    except Exception as e:
        return f"Error reading knowledge base directory: {e}"

    # Find files where norm_input is in the filename, or vice versa
    matches = []
    for f in files:
        if f.endswith(".txt") and f != "embeddings_cache.json":
            base = f[:-4]
            if norm_input in base or base in norm_input:
                matches.append(f)

    if len(matches) == 1:
        match_path = os.path.join(KB_DIR, matches[0])
        try:
            with open(match_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return content if content else f"I found the factsheet for {medicine_name}, but it is currently empty."
        except Exception as e:
            return f"Error reading matched factsheet: {e}"

    # Step 4: Lookup in Database to map to generic name
    db = SessionLocal()
    try:
        med = db.query(Medicine).filter(Medicine.name.ilike(f"%{medicine_name}%")).first()
        if not med:
            med = db.query(Medicine).filter(Medicine.generic_name.ilike(f"%{medicine_name}%")).first()

        if med:
            db_name_norm = re.sub(r"[^a-zA-Z0-9_]", "", med.name.lower().replace(" ", "_"))
            db_file = os.path.join(KB_DIR, f"{db_name_norm}.txt")
            if os.path.exists(db_file):
                with open(db_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    return content if content else f"I found the factsheet for {med.name}, but it is currently empty."

            db_generic_norm = re.sub(r"[^a-zA-Z0-9_]", "", med.generic_name.lower().replace(" ", "_"))
            db_gen_file = os.path.join(KB_DIR, f"{db_generic_norm}.txt")
            if os.path.exists(db_gen_file):
                with open(db_gen_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    return content if content else f"I found the factsheet for {med.generic_name}, but it is currently empty."
    except Exception as e:
        pass
    finally:
        db.close()

    if len(matches) > 1:
        suggestion_list = ", ".join([f[:-4].replace("_", " ").title() for f in matches])
        return f"Did you mean one of these: {suggestion_list}?"

    return f"Medicine factsheet for {medicine_name} not found in the knowledge base."

@tool(args_schema=SearchDrugByIndicationInput)
def search_drug_by_indication(symptom_or_use: str) -> str:
    """
    Search for medicines in the knowledge base that treat a specific symptom, condition, or indication.
    """
    if not os.path.exists(KB_DIR):
        return "Knowledge base directory not found."

    # Try Semantic Search first
    cache = load_embeddings_cache()
    if cache:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.embed_content(
                model="gemini-embedding-2",
                contents=symptom_or_use,
            )
            query_embedding = np.array(response.embeddings[0].values)
            
            # Compute cosine similarities
            results = []
            for chunk in cache:
                chunk_emb = np.array(chunk["embedding"])
                similarity = np.dot(query_embedding, chunk_emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(chunk_emb))
                results.append((similarity, chunk))
            
            # Sort by similarity descending
            results.sort(key=lambda x: x[0], reverse=True)
            
            # Deduplicate by medicine, filter below threshold
            seen_meds = set()
            semantic_matches = []
            for sim, chunk in results:
                # 0.35 similarity threshold for gemini-embedding-2
                if sim < 0.35:
                    continue
                med_name = chunk["medicine"]
                if med_name not in seen_meds:
                    seen_meds.add(med_name)
                    # Extract a short excerpt of the relevant matching text
                    excerpt = get_first_few_sentences(chunk["content"], n=2)
                    semantic_matches.append(f"{med_name} (used for: {excerpt})")
                    if len(semantic_matches) >= 5:
                        break
            
            if semantic_matches:
                return "The following medicines match your search: " + ", ".join(semantic_matches)
        except Exception as e:
            # Print error but fall back silently to keyword search
            print(f"Semantic search failed, falling back to keyword search: {e}")

    # Fallback: Keyword-based scan of factsheet content
    term = symptom_or_use.lower()
    matching_drugs = []

    try:
        files = os.listdir(KB_DIR)
        for filename in files:
            if not filename.endswith(".txt") or filename == "embeddings_cache.json":
                continue

            filepath = os.path.join(KB_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if term in content.lower():
                drug_name = filename[:-4].replace("_", " ").title()
                lines = [line.strip() for line in content.split("\n") if line.strip()]
                overview = ""
                for idx, line in enumerate(lines):
                    if "OVERVIEW" in line.upper() and idx + 1 < len(lines):
                        overview = lines[idx + 1]
                        break
                if not overview and lines:
                    overview = lines[0]
                matching_drugs.append(f"{drug_name} (used for: {get_first_few_sentences(overview, 2)})")
    except Exception as e:
        return f"Error searching knowledge base: {e}"

    if not matching_drugs:
        return f"No medicines found in the knowledge base that match the condition or symptom: {symptom_or_use}."

    return "The following medicines match your search: " + ", ".join(matching_drugs)

RAG_TOOLS = [
    get_drug_knowledge,
    search_drug_by_indication,
]
