from database.database import SessionLocal
from database.models import Customer, Medicine, Order
from tools.order_tools import reserve_medicine

def test_reserve_medicine_manufacturer():
    db = SessionLocal()
    
    # 1. Ensure we have a customer
    test_phone = "9876543210"
    cust = db.query(Customer).filter(Customer.phone == test_phone).first()
    if not cust:
        cust = Customer(name="Test Cust", phone=test_phone)
        db.add(cust)
        db.commit()
        db.refresh(cust)
        
    # 2. Add two entries for a specific medicine name with different manufacturers
    test_med_name = "ManufacturerTestMed"
    db.query(Order).filter(Order.customer_id == cust.id).delete()
    db.query(Medicine).filter(Medicine.name == test_med_name).delete()
    db.commit()
    
    med1 = Medicine(
        name=test_med_name,
        generic_name="GenChemTest",
        strength="500 mg",
        manufacturer="Sun Pharma",
        price=10.0,
        stock=100
    )
    med2 = Medicine(
        name=test_med_name,
        generic_name="GenChemTest",
        strength="500 mg",
        manufacturer="Cipla",
        price=12.0,
        stock=150
    )
    db.add_all([med1, med2])
    db.commit()
    
    # 3. Call reserve_medicine without manufacturer parameter
    res = reserve_medicine.invoke({"phone": test_phone, "medicine_name": test_med_name, "quantity": 2})
    print("Result without manufacturer:\n", res)
    assert "Multiple manufacturers are available" in res
    assert "Sun Pharma" in res
    assert "Cipla" in res
    
    # 4. Call reserve_medicine with manufacturer = "Cipla"
    res_success = reserve_medicine.invoke({"phone": test_phone, "medicine_name": test_med_name, "quantity": 2, "manufacturer": "Cipla"})
    print("Result with manufacturer:\n", res_success)
    assert "Reservation successful" in res_success
    assert "Cipla" in res_success
    
    # Clean up
    db.query(Order).filter(Order.customer_id == cust.id).delete()
    db.query(Medicine).filter(Medicine.name == test_med_name).delete()
    db.commit()
    db.close()
    
    print("ALL MANUFACTURER RESERVATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_reserve_medicine_manufacturer()
