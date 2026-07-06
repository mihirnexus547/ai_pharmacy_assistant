import sqlite3
from fastapi.testclient import TestClient
from app.main import app, get_admin_token
from database.database import SessionLocal
from database.models import Customer, Medicine, Order, OrderStatus

client = TestClient(app)

def test_admin_full_flow():
    # Set admin token cookie
    admin_token = get_admin_token()
    client.cookies.set("admin_token", admin_token)

    db = SessionLocal()
    
    # 1. Clear test data if left over from previous runs
    test_phone = "9876543210"
    existing_cust = db.query(Customer).filter(Customer.phone == test_phone).first()
    if existing_cust:
        db.delete(existing_cust)
        db.commit()
        
    existing_med = db.query(Medicine).filter(Medicine.name == "TestMedBrand").first()
    if existing_med:
        db.delete(existing_med)
        db.commit()
        
    # 2. Add customer
    cust_res = client.post("/api/admin/customers", json={"name": "Test Cust", "phone": test_phone})
    assert cust_res.status_code == 200
    cust_id = cust_res.json()["customer"]["id"]
    
    # 3. Add medicine
    med_res = client.post("/api/admin/medicines", json={
        "name": "TestMedBrand",
        "generic_name": "TestGenericChem",
        "strength": "250 mg",
        "manufacturer": "Test Lab",
        "price": 12.50,
        "stock": 50
    })
    assert med_res.status_code == 200
    med_id = med_res.json()["medicine"]["id"]
    assert med_res.json()["medicine"]["stock"] == 50
    
    # 4. Add reservation (order)
    order_res = client.post("/api/admin/orders", json={
        "customer_id": cust_id,
        "medicine_id": med_id,
        "quantity": 5
    })
    assert order_res.status_code == 200
    order_id = order_res.json()["order"]["id"]
    
    # Verify medicine stock is reduced by 5 (50 - 5 = 45)
    db.expire_all()
    medicine = db.query(Medicine).filter(Medicine.id == med_id).first()
    assert medicine.stock == 45
    
    # 5. Delete reservation (order)
    del_order_res = client.delete(f"/api/admin/orders/{order_id}")
    assert del_order_res.status_code == 200
    
    # Verify stock restored to 50
    db.expire_all()
    medicine = db.query(Medicine).filter(Medicine.id == med_id).first()
    assert medicine.stock == 50
    
    # 6. Delete medicine
    del_med_res = client.delete(f"/api/admin/medicines/{med_id}")
    assert del_med_res.status_code == 200
    
    # 7. Delete customer
    del_cust_res = client.delete(f"/api/admin/customers/{cust_id}")
    assert del_cust_res.status_code == 200
    
    # 8. Test chat delete endpoint
    del_chat_res = client.delete("/api/admin/chats/non_existing_dummy_thread")
    assert del_chat_res.status_code == 200
    
    db.close()
    print("ALL ADMIN MEDICINES/CUSTOMERS/RESERVATIONS/CHATS TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_admin_full_flow()
