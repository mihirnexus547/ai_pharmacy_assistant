from fastapi.testclient import TestClient
from app.main import app, get_admin_token
from database.database import SessionLocal
from database.models import Customer

client = TestClient(app)

def test_admin_customer_flow():
    # 1. Unauthenticated request to add customer
    response = client.post("/api/admin/customers", json={"name": "Test User", "phone": "9876543210"})
    assert response.status_code == 401
    
    # 2. Get valid admin token and set cookie
    admin_token = get_admin_token()
    client.cookies.set("admin_token", admin_token)
    
    # Clean up any existing customer with this phone
    db = SessionLocal()
    existing = db.query(Customer).filter(Customer.phone == "9876543210").first()
    if existing:
        db.delete(existing)
        db.commit()
    db.close()
    
    # 3. Add customer with valid details
    response = client.post("/api/admin/customers", json={"name": "Test User", "phone": "9876543210"})
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    customer_id = res_data["customer"]["id"]
    
    # 4. Add customer with invalid phone number
    response = client.post("/api/admin/customers", json={"name": "Invalid Phone", "phone": "12345"})
    assert response.status_code == 400
    
    # 5. Delete customer
    response = client.delete(f"/api/admin/customers/{customer_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify customer deleted
    db = SessionLocal()
    deleted_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    assert deleted_customer is None
    db.close()
    
    print("ALL ADMIN CUSTOMER ENDPOINT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_admin_customer_flow()
