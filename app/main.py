"""
FastAPI application.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from schemas.chat import ChatRequest, ChatResponse
from services.conversation import conversation_service

from app.websocket import router as websocket_router
from app.audio_ws import router as audio_router


app = FastAPI(
    title="AI Pharmacy Voice Assistant",
    version="1.0.0",
    description="AI-powered Pharmacy Assistant using LangGraph and Groq",
)

# Existing websocket (keep it)
app.include_router(websocket_router)

# New audio websocket
app.include_router(audio_router)

# Serve static files
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


@app.get("/")
async def home():
    """
    Open the Voice Assistant web page.
    """
    return FileResponse("static/index.html")


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
from fastapi import Depends
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Medicine, Customer, Order
from services.agent import agent

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

@app.get("/admin")
async def admin_portal():
    """
    Serve the Admin Portal page.
    """
    return FileResponse("static/admin.html")

@app.get("/api/admin/data")
async def get_admin_data(db: Session = Depends(get_db)):
    """
    Return all database tables and memory-based chat sessions.
    """
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
        conn = sqlite3.connect("checkpoints.db")
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