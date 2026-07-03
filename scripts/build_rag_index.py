import os
import sys
import json
import time
from google import genai
from app.config import settings

# Ensure workspace is in Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def parse_factsheet(content):
    lines = content.split('\n')
    current_section = 'OVERVIEW'
    sections = {
        'OVERVIEW': [],
        'INDICATIONS & USES': [],
        'DOSAGE & ADMINISTRATION': [],
        'SIDE EFFECTS': [],
        'WARNINGS & PRECAUTIONS': []
    }
    for line in lines:
        line_stripped = line.strip()
        upper_line = line_stripped.upper()
        if not line_stripped:
            continue
        if 'OVERVIEW' in upper_line and len(upper_line) < 30:
            current_section = 'OVERVIEW'
        elif ('INDICATION' in upper_line or 'USES' in upper_line) and len(upper_line) < 30:
            current_section = 'INDICATIONS & USES'
        elif ('DOSAGE' in upper_line or 'ADMINISTRATION' in upper_line) and len(upper_line) < 30:
            current_section = 'DOSAGE & ADMINISTRATION'
        elif 'SIDE EFFECT' in upper_line and len(upper_line) < 30:
            current_section = 'SIDE EFFECTS'
        elif ('WARNING' in upper_line or 'PRECAUTION' in upper_line) and len(upper_line) < 30:
            current_section = 'WARNINGS & PRECAUTIONS'
        else:
            sections[current_section].append(line_stripped)
    return {k: '\n'.join(v).strip() for k, v in sections.items()}

def embed_with_retry(client, text, model="gemini-embedding-2", max_retries=6, initial_backoff=3):
    backoff = initial_backoff
    for attempt in range(max_retries):
        try:
            response = client.models.embed_content(
                model=model,
                contents=text,
            )
            return response.embeddings[0].values
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "resource_exhausted" in err_str.lower():
                print(f"    [429] Rate limit hit (attempt {attempt + 1}/{max_retries}). Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2
            else:
                raise e
    raise Exception("Failed to generate embedding after max retries due to rate limits.")

def main():
    kb_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base")
    cache_path = os.path.join(kb_dir, "embeddings_cache.json")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    chunks = []
    
    files = [f for f in os.listdir(kb_dir) if f.endswith(".txt") and f != "embeddings_cache.json"]
    print(f"Found {len(files)} factsheet files to index.")

    for filename in files:
        filepath = os.path.join(kb_dir, filename)
        medicine_name = filename[:-4].replace("_", " ").title()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            print(f"Skipping empty factsheet: {filename}")
            continue

        print(f"Processing factsheet for {medicine_name}...")
        parsed_sections = parse_factsheet(content)

        for section_name, section_content in parsed_sections.items():
            if not section_content:
                continue

            print(f"  Embedding section: {section_name} ({len(section_content)} chars)...")
            try:
                embedding_vector = embed_with_retry(client, section_content)
                chunks.append({
                    "medicine": medicine_name,
                    "section": section_name,
                    "content": section_content,
                    "embedding": embedding_vector
                })
                time.sleep(0.1)  # Brief sleep
            except Exception as e:
                print(f"  CRITICAL ERROR embedding {medicine_name} - {section_name}: {e}")

    print(f"Successfully generated embeddings for {len(chunks)} chunks.")
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
    print(f"Saved cached embeddings to {cache_path}")

if __name__ == "__main__":
    main()
