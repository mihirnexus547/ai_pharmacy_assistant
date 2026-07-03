import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import create_react_agent
from app.prompts import SYSTEM_PROMPT
from providers.llm import get_llm

from tools.customer_tools import CUSTOMER_TOOLS
from tools.medicine_tools import MEDICINE_TOOLS
from tools.order_tools import ORDER_TOOLS
from tools.pharmacy_tools import PHARMACY_TOOLS
from tools.rag_tools import RAG_TOOLS

llm = get_llm()

conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
memory = SqliteSaver(conn)

TOOLS = (
    CUSTOMER_TOOLS
    + MEDICINE_TOOLS
    + ORDER_TOOLS
    + PHARMACY_TOOLS
    + RAG_TOOLS
)


agent = create_react_agent(
    model=llm,
    tools=TOOLS,
    checkpointer=memory,
    prompt = SYSTEM_PROMPT
)