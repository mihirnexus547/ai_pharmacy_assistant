# PharmAssist System Flow

### 1. Problem Statement

- **Operational Bottleneck:** Highly trained pharmacists are constantly interrupted by trivial, repetitive phone calls (stock, pricing, hours).
- **IVR Failures:** Traditional Interactive Voice Response systems ("Press 1 for stock") use rigid decision trees and lack Natural Language Understanding.
- **The Solution:** PharmAssist uses a GenAI-powered conversational agent to handle these queries naturally and autonomously.

> 🖼️ **Image Insertion:** Place your **System Architecture Flow** diagram right here. It provides a perfect high-level overview of the entire solution before diving into the specific components below.

### 2. Twilio Configuration

- **The Bridge:** Twilio intercepts the PSTN (Public Switched Telephone Network) signal when a user calls.
- **WebSockets:** Configured via TwiML to initiate a `<Stream>` command, opening a continuous, bidirectional WebSocket to our FastAPI server.
- **Audio Format:** Streams raw audio in **G.711 μ-law format at 8000Hz** for ultra-low latency.

### 3. Deepgram Configuration

- **Streaming API:** The server opens a persistent WebSocket connection to Deepgram for instant Speech-to-Text transcription.
- **Voice Activity Detection (VAD):** Deepgram monitors the audio for exactly **500 milliseconds of absolute silence**.
- **Turn-Taking:** Once the silence threshold is met, it emits a `speech_final` flag, instantly letting the system know the user finished speaking.

### 4. Agent Workflow

- **The Core Engine:** LangGraph ReAct (Reasoning and Acting) Agent, powered by Google's Gemini 2.5 Pro.
- **Cyclical Logic (ReAct Loop):**
  - **Observe:** Analyzes user intent and conversation history.
  - **Reason:** Evaluates if it needs to fetch external data (like checking inventory).
  - **Act:** Generates structured JSON to trigger a Python tool, ingests the result, and loops back to reason until ready to reply.

### 5. Tables Available & All Tools

- **Database Architecture:** Uses a secure PostgreSQL/SQLite database with exactly 3 core tables to prevent AI hallucinations.
- **The 3 Tables and their Exact Fields:**
  - `medicines`: Tracks inventory (`id`, `name`, `generic_name`, `strength`, `manufacturer`, `price`, `stock`, `created_at`, `updated_at`).
  - `customers`: Tracks user profiles (`id`, `name`, `phone`, `created_at`).
  - `orders`: Manages reservations (`id`, `customer_id`, `medicine_id`, `quantity`, `status` [Reserved, Collected, Cancelled], `reserved_at`).

> 🖼️ **Image Insertion:** Place your **Admin Portal - Customers** screenshot here to visually demonstrate what the database tables look like in the real CRM interface. You can also place the **Admin Portal - Login** screenshot just before it to show how staff securely access this data.

- **The Available Tools & Their Functionality:**
  - **Customer Tools:**
    - `register_customer`: Registers a new customer using their name and 10-digit phone number.
    - `get_customer`: Retrieves a customer's profile using their phone number.
    - `update_customer`: Modifies an existing customer's name.
  - **Medicine Tools:**
    - `search_medicine`: Performs a pattern-match search by brand or generic name to return manufacturer, strength, price, and stock count.
    - `check_stock`: Returns the exact units available for a specific medicine.
    - `list_available_medicines`: Returns a complete list of all drugs currently in stock > 0.
  - **Order Tools:**
    - `reserve_medicine`: Creates an order and securely deducts stock using atomic database row-locking.
    - `cancel_order`: Cancels a reservation and restores the stock count to the inventory.
    - `get_order_status`: Retrieves the current fulfillment state of a specific order.
  - **Pharmacy Tools:**
    - `get_pharmacy_details`: Fetches static operational info (business hours, physical location).

### 6. RAG Architecture for Medicine Details

- **The Goal:** Safely answer pharmacological questions (e.g., "Can I take this on an empty stomach?") without hallucinating.
- **Vector Search:** Converts the user's natural language question into a high-dimensional mathematical vector.
- **Cosine Similarity:** Searches a local vector database containing verified medical documents.
- **System Prompt Injection:** Injects the retrieved medical paragraphs into Gemini's prompt, forcing it to base advice purely on verified literature.

> 🖼️ **Image Insertion:** Place your **Retrieval-Augmented Generation (RAG) Flow** diagram here. It perfectly illustrates this exact vector search process.

### 7. How Conversation is Preserved

- **The Stateless Challenge:** WebSockets naturally forget previous turns in a conversation.
- **SqliteSaver Checkpointer:** LangGraph assigns a unique Call SID (`thread_id`) to every incoming call.
- **State Memory:** After every reasoning step, the agent's entire memory graph (history, context) is serialized into a local SQLite database (`checkpoints.db`).
- **Instant Rehydration:** When the user speaks again, the `thread_id` instantly rehydrates the state, preserving the conversation flawlessly.

> 🖼️ **Image Insertion:** Place your **Admin Portal - Conversation Logs** screenshot here. It perfectly demonstrates how the SQLite state memory allows staff to read the entire conversation history in real-time.

### 8. Browser Chat & Voice Integration

- **Omnichannel Client:** An integrated web client for users who prefer not to call via phone.
- **Text & Voice Options:** Supports standard typed text chat.
- **Live Microphone Integration:** Streams microphone audio directly to the backend via WebSockets, mirroring the exact Twilio low-latency flow in the browser.

### 9. ElevenLabs Configuration

- **TTS Synthesis:** The Agent's final textual response is routed via HTTP to ElevenLabs.
- **Voice Cloning:** Generates highly realistic human speech with natural intonation.
- **Zero Latency Transcoding:** API is configured to return audio natively in the `ulaw_8000` format.
- **The Output:** The raw audio is instantly piped back into the Twilio (or Browser) WebSocket, allowing the caller to hear the response in under a second.
