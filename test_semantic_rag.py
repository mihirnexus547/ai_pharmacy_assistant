import os
import sys

# Ensure workspace is in Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.rag_tools import search_drug_by_indication, get_drug_knowledge

def test_semantic_search(query):
    print(f"\n--- Testing Semantic Search for Query: '{query}' ---")
    try:
        result = search_drug_by_indication.invoke({"symptom_or_use": query})
        print("Result:")
        print(result)
    except Exception as e:
        print(f"Error during semantic search: {e}")

def test_drug_knowledge(med_name):
    print(f"\n--- Testing Drug Knowledge Lookup for: '{med_name}' ---")
    try:
        result = get_drug_knowledge.invoke({"medicine_name": med_name})
        # Print first few lines of the result to keep output clean
        lines = result.split("\n")
        print("First 10 lines of result:")
        print("\n".join(lines[:10]))
        print(f"... ({len(lines)} total lines)")
    except Exception as e:
        print(f"Error during knowledge lookup: {e}")

def main():
    print("Starting Semantic RAG Verification...")
    
    # 1. Test semantic searches
    test_semantic_search("blood pressure")
    test_semantic_search("infection")
    test_semantic_search("allergy")
    test_semantic_search("headache")
    
    # 2. Test direct lookups
    test_drug_knowledge("paracetamol")
    test_drug_knowledge("amlodipine")
    test_drug_knowledge("non_existent_drug")

if __name__ == "__main__":
    main()
