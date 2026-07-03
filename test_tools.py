# test_tools.py

from tools.medicine_tools import search_medicine

print(
    search_medicine.invoke(
        {
            "medicine_name": "Crocin"
        }
    )
)