"""
FastAPI application.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from schemas.chat import ChatRequest, ChatResponse
from services.conversation import conversation_service

from app.websocket import router as websocket_router
from app.audio_ws import router as audio_router
from app.twilio_ws import router as twilio_router
from database.database import create_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically create tables on startup
    create_tables()

    # Automatically seed the database if it is empty (zero-configuration setup)
    from database.database import SessionLocal
    from database.seed import seed_medicines, seed_customers, seed_orders
    db = SessionLocal()
    try:
        from database.models import Medicine
        if db.query(Medicine).count() == 0:
            seed_medicines(db)
            seed_customers(db)
            seed_orders(db)
    except Exception as e:
        print(f"Error auto-seeding database on startup: {e}")
    finally:
        db.close()

    yield

app = FastAPI(
    title="AI Pharmacy Voice Assistant",
    version="1.0.0",
    description="AI-powered Pharmacy Assistant using LangGraph and Groq",
    lifespan=lifespan,
)

# Existing websocket (keep it)
app.include_router(websocket_router)

# New audio websocket
app.include_router(audio_router)

# Twilio webhook/websocket
app.include_router(twilio_router)

# Serve static files
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


@app.get("/")
async def home():
    """
    Open the Landing Page describing agent capabilities.
    """
    return FileResponse("static/index.html")


@app.get("/assistant")
async def assistant():
    """
    Open the Voice Assistant web page.
    """
    return FileResponse("static/assistant.html")


@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    return {
        "message": "AI Pharmacy Assistant Running"
    }


@app.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
) -> ChatResponse:

    try:

        response = conversation_service.chat(
            session_id=request.session_id,
            message=request.message,
        )

        # Handle LangChain content format
        if isinstance(response, list):
            response = response[0]["text"]

        return ChatResponse(
            response=response,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# Admin Portal & Data Endpoints
# ============================================================
import os
import secrets
import hashlib
from pydantic import BaseModel
from fastapi import Depends, status, Cookie, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Medicine, Customer, Order
from services.agent import agent

class LoginRequest(BaseModel):
    username: str
    password: str

def get_admin_token() -> str:
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin")
    return hashlib.sha256(f"{username}:{password}".encode()).hexdigest()

def parse_message_content(content):
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(item.get("text", ""))
            elif isinstance(item, str):
                texts.append(item)
        return "".join(texts)
    return str(content)

@app.get("/login")
async def login_page():
    """
    Serve the custom Admin Login page.
    """
    return FileResponse("static/login.html")

@app.post("/api/admin/login")
async def api_admin_login(login_data: LoginRequest, response: Response):
    correct_username = os.getenv("ADMIN_USERNAME", "admin")
    correct_password = os.getenv("ADMIN_PASSWORD", "admin")
    
    is_correct_username = secrets.compare_digest(login_data.username, correct_username)
    is_correct_password = secrets.compare_digest(login_data.password, correct_password)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Set secure HttpOnly cookie
    token = get_admin_token()
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        max_age=1800,  # 30 minutes
        samesite="lax",
        secure=False   # Set to True in production with HTTPS
    )
    return {"status": "success", "message": "Logged in successfully"}

@app.post("/api/admin/logout")
async def api_admin_logout(response: Response):
    response.delete_cookie("admin_token")
    return {"status": "success", "message": "Logged out successfully"}

@app.get("/admin")
async def admin_portal(admin_token: str = Cookie(None)):
    """
    Serve the Admin Portal page (redirect to login if unauthenticated).
    """
    expected_token = get_admin_token()
    if not admin_token or admin_token != expected_token:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("static/admin.html")

@app.get("/api/admin/data")
async def get_admin_data(
    response: Response,
    db: Session = Depends(get_db),
    admin_token: str = Cookie(None)
):
    """
    Return all database tables and memory-based chat sessions (401 if unauthenticated).
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    expected_token = get_admin_token()
    if not admin_token or admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated as admin",
        )
    # 1. Medicines
    medicines = db.query(Medicine).all()
    medicines_list = [
        {
            "id": m.id,
            "name": m.name,
            "generic_name": m.generic_name,
            "strength": m.strength,
            "manufacturer": m.manufacturer,
            "price": m.price,
            "stock": m.stock,
        }
        for m in medicines
    ]

    # 2. Customers
    customers = db.query(Customer).all()
    customers_list = [
        {
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in customers
    ]

    # 3. Orders (Reservations)
    orders = db.query(Order).all()
    orders_list = [
        {
            "id": o.id,
            "customer_name": o.customer.name if o.customer else "Unknown",
            "customer_phone": o.customer.phone if o.customer else "Unknown",
            "medicine_name": o.medicine.name if o.medicine else "Unknown",
            "quantity": o.quantity,
            "status": o.status.value,
            "reserved_at": o.reserved_at.isoformat() if o.reserved_at else None,
        }
        for o in orders
    ]

    # 4. Persistent conversation histories from SQLite checkpointer
    chat_histories = {}
    try:
        import sqlite3
        conn = sqlite3.connect("data/checkpoints.db")
        cursor = conn.cursor()
        # Verify checkpoints table exists first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkpoints'")
        if cursor.fetchone():
            cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
            thread_ids = [row[0] for row in cursor.fetchall()]
        else:
            thread_ids = []
        conn.close()

        for thread_id in thread_ids:
            state = agent.get_state({"configurable": {"thread_id": thread_id}})
            messages = state.values.get("messages", [])
            parsed_msgs = []
            for msg in messages:
                role = "user" if msg.type == "human" else "assistant"
                content = parse_message_content(msg.content)
                if content:
                    parsed_msgs.append({
                        "role": role,
                        "content": content
                    })
            if parsed_msgs:
                chat_histories[thread_id] = parsed_msgs
    except Exception as e:
        print("Failed to load conversation history:", e)


    return {
        "medicines": medicines_list,
        "customers": customers_list,
        "orders": orders_list,
        "chats": chat_histories,
    }


# ============================================================
# Customer/User Management Endpoints
# ============================================================
from utils.phone import validate_and_normalize_phone

class CustomerCreateRequest(BaseModel):
    name: str
    phone: str

@app.post("/api/admin/customers")
async def api_admin_add_customer(
    request: CustomerCreateRequest,
    db: Session = Depends(get_db),
    admin_token: str = Cookie(None)
):
    expected_token = get_admin_token()
    if not admin_token or admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated as admin",
        )
        
    # Validate and normalize phone
    try:
        normalized_phone = validate_and_normalize_phone(request.phone)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
        
    # Check if customer already exists with this phone
    existing = db.query(Customer).filter(Customer.phone == normalized_phone).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with phone number '{normalized_phone}' already exists."
        )
        
    new_customer = Customer(
        name=request.name.strip(),
        phone=normalized_phone
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    return {
        "status": "success",
        "message": "Customer added successfully",
        "customer": {
            "id": new_customer.id,
            "name": new_customer.name,
            "phone": new_customer.phone,
            "created_at": new_customer.created_at.isoformat() if new_customer.created_at else None
        }
    }

@app.delete("/api/admin/customers/{customer_id}")
async def api_admin_delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    admin_token: str = Cookie(None)
):
    expected_token = get_admin_token()
    if not admin_token or admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated as admin",
        )
        
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
        
    db.delete(customer)
    db.commit()
    
    return {
        "status": "success",
        "message": "Customer and their associated orders deleted successfully"
    }

@app.put("/api/admin/customers/{customer_id}")
async def api_admin_update_customer(
    customer_id: int,
    request: CustomerCreateRequest,
    db: Session = Depends(get_db),
    admin_token: str = Cookie(None)
):
    expected_token = get_admin_token()
    if not admin_token or admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated as admin",
        )
        
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
        
    try:
        normalized_phone = validate_and_normalize_phone(request.phone)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
        
    existing = db.query(Customer).filter(Customer.phone == normalized_phone, Customer.id != customer_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with phone number '{normalized_phone}' already exists."
        )

    customer.name = request.name.strip()
    customer.phone = normalized_phone
    db.commit()
    
    return {
        "status": "success",
        "message": "Customer updated successfully"
    }



# ============================================================
# Medicine Management Endpoints
# ============================================================
class MedicineCreateRequest(BaseModel):
    name: str
    generic_name: str
    strength: str
    manufacturer: str
    price: float
    stock: int

@app.post("/api/admin/medicines")
async def api_admin_add_medicine(
    request: MedicineCreateRequest,
    db: Session = Depends(get_db),
    admin_token: str = Cookie(None)
):
    expected_token = get_admin_token()
    if not admin_token or admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated as admin",
        )
        
    new_medicine = Medicine(
        name=request.name.strip(),
        generic_name=request.generic_name.strip(),
        strength=request.strength.strip(),
        manufacturer=request.manufacturer.strip(),
        price=request.price,
        stock=request.stock
    )
    db.add(new_medicine)
    db.commit()
    db.refresh(new_medicine)
    return {
        "status": "success",
        "message": "Medicine added successfully",
        "medicine": {
            "id": new_medicine.id,
            "name": new_medicine.name,
            "generic_name": new_medicine.generic_name,
            "strength": new_medicine.strength,
            "manufacturer": new_medicine.manufacturer,
            "price": new_medicine.price,
            "stock": new_medicine.stock
        }
    }

@app.delete("/api/admin/medicines/{medicine_id}")
async def api_admin_delete_medicine(
    medicine_id: int,
    db: Session = Depends(get_db),
    admin_token: str = Cookie(None)
):
    expected_token = get_admin_token()
    if not admin_token or admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated as admin",
        )
        
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found"
        )
    db.delete(medicine)
    db.commit()
    return {
        "status": "success",
        "message": "Medicine deleted successfully"
    }

@app.put("/api/admin/medicines/{medicine_id}")
async def api_admin_update_medicine(
    medicine_id: int,
    request: MedicineCreateRequest,
    db: Session = Depends(get_db),
    admin_token: str = Cookie(None)
):
    expected_token = get_admin_token()
    if not admin_token or admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated as admin",
        )
        
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found"
        )
        
    medicine.name = request.name.strip()
    medicine.generic_name = request.generic_name.strip()
    medicine.strength = request.strength.strip()
    medicine.manufacturer = request.manufacturer.strip()
    medicine.price = request.price
    medicine.stock = request.stock
    
    db.commit()
    return {
        "status": "success",
        "message": "Medicine updated successfully"
    }


# ============================================================
# Reservation (Order) Management Endpoints
# ============================================================
from database.models import OrderStatus

class OrderCreateRequest(BaseModel):
    customer_id: int
    medicine_id: int
    quantity: int

class OrderUpdateRequest(BaseModel):
    status: OrderStatus
    quantity: int

@app.post("/api/admin/orders")
async def api_admin_add_order(
    request: OrderCreateRequest,
    db: Session = Depends(get_db),
    admin_token: str = Cookie(None)
):
    expected_token = get_admin_token()
    if not admin_token or admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated as admin",
        )
        
    # Verify customer and medicine exist
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
        
    medicine = db.query(Medicine).filter(Medicine.id == request.medicine_id).first()
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found"
        )
        
    if request.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than 0"
        )
        
    if medicine.stock < request.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Available: {medicine.stock}"
        )
        
    # Deduct stock
    medicine.stock -= request.quantity
    
    new_order = Order(
        customer_id=request.customer_id,
        medicine_id=request.medicine_id,
        quantity=request.quantity,
        status=OrderStatus.RESERVED
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return {
        "status": "success",
        "message": "Reservation created successfully",
        "order": {
            "id": new_order.id,
            "customer_name": customer.name,
            "medicine_name": medicine.name,
            "quantity": new_order.quantity,
            "status": new_order.status.value,
            "reserved_at": new_order.reserved_at.isoformat() if new_order.reserved_at else None
        }
    }

@app.delete("/api/admin/orders/{order_id}")
async def api_admin_delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    admin_token: str = Cookie(None)
):
    expected_token = get_admin_token()
    if not admin_token or admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated as admin",
        )
        
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
        
    # Restore stock when deleted
    medicine = db.query(Medicine).filter(Medicine.id == order.medicine_id).first()
    if medicine and order.status != OrderStatus.CANCELLED:
        medicine.stock += order.quantity
        
    db.delete(order)
    db.commit()
    return {
        "status": "success",
        "message": "Reservation deleted and stock restored successfully"
    }

@app.put("/api/admin/orders/{order_id}")
async def api_admin_update_order(
    order_id: int,
    request: OrderUpdateRequest,
    db: Session = Depends(get_db),
    admin_token: str = Cookie(None)
):
    expected_token = get_admin_token()
    if not admin_token or admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated as admin",
        )
        
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
        
    medicine = db.query(Medicine).filter(Medicine.id == order.medicine_id).first()
    
    if order.status != OrderStatus.CANCELLED and request.status == OrderStatus.CANCELLED:
        if medicine:
            medicine.stock += order.quantity
    elif order.status == OrderStatus.CANCELLED and request.status != OrderStatus.CANCELLED:
        if medicine:
            if medicine.stock < request.quantity:
                raise HTTPException(status_code=400, detail="Insufficient stock to un-cancel this reservation.")
            medicine.stock -= request.quantity
    elif order.status != OrderStatus.CANCELLED and request.status != OrderStatus.CANCELLED:
        diff = request.quantity - order.quantity
        if diff > 0 and medicine and medicine.stock < diff:
            raise HTTPException(status_code=400, detail="Insufficient stock for increased quantity.")
        if medicine:
            medicine.stock -= diff
            
    order.status = request.status
    order.quantity = request.quantity
    db.commit()
    
    return {
        "status": "success",
        "message": "Reservation updated successfully"
    }


# ============================================================
# Chat Session Management Endpoints
# ============================================================
@app.delete("/api/admin/chats/{thread_id}")
async def api_admin_delete_chat(
    thread_id: str,
    admin_token: str = Cookie(None)
):
    expected_token = get_admin_token()
    if not admin_token or admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated as admin",
        )
        
    try:
        import sqlite3
        conn = sqlite3.connect("data/checkpoints.db")
        cursor = conn.cursor()
        
        # Verify checkpoints table exists first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkpoints'")
        if cursor.fetchone():
            cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            cursor.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
            conn.commit()
            success = cursor.rowcount > 0
        else:
            success = False
            
        conn.close()
        
        # Let's assume deletion is successful even if it deletes 0 rows, 
        # as it means the database state matches the request.
        return {
            "status": "success",
            "message": f"Conversation history for thread '{thread_id}' deleted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chat history: {str(e)}"
        )