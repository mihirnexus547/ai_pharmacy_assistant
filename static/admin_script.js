// Admin Portal State
let adminData = {
    medicines: [],
    customers: [],
    orders: [],
    chats: {}
};

// DOM elements
const medicinesTableBody = document.getElementById("medicinesTableBody");
const customersTableBody = document.getElementById("customersTableBody");
const ordersTableBody = document.getElementById("ordersTableBody");
const sessionList = document.getElementById("sessionList");
const chatViewerHeader = document.getElementById("chatViewerHeader");
const chatViewerMessages = document.getElementById("chatViewerMessages");

// Search Inputs
const medicinesSearch = document.getElementById("medicinesSearch");
const customersSearch = document.getElementById("customersSearch");
const ordersSearch = document.getElementById("ordersSearch");

// Initialize Data Load
async function loadAdminData() {
    try {
        const res = await fetch("/api/admin/data");
        adminData = await res.json();
        
        renderMedicines(adminData.medicines);
        renderCustomers(adminData.customers);
        renderOrders(adminData.orders);
        renderSessions(adminData.chats);
    } catch (err) {
        console.error("Failed to load admin data:", err);
    }
}

// ------------------------------------------------------------
// MEDICINES RENDER & FILTER
// ------------------------------------------------------------
function renderMedicines(list) {
    medicinesTableBody.innerHTML = list.map(m => `
        <tr>
            <td><strong>${m.id}</strong></td>
            <td><span class="text-primary fw-bold">${m.name}</span></td>
            <td>${m.generic_name}</td>
            <td><span class="badge bg-light text-dark">${m.strength}</span></td>
            <td>${m.manufacturer}</td>
            <td>₹${m.price.toFixed(2)}</td>
            <td>
                <span class="fw-bold ${m.stock > 0 ? 'text-success' : 'text-danger'}">
                    ${m.stock}
                </span>
            </td>
        </tr>
    `).join("");
}

medicinesSearch.oninput = () => {
    const val = medicinesSearch.value.toLowerCase();
    const filtered = adminData.medicines.filter(m => 
        m.name.toLowerCase().includes(val) || 
        m.generic_name.toLowerCase().includes(val) || 
        m.manufacturer.toLowerCase().includes(val)
    );
    renderMedicines(filtered);
};

// ------------------------------------------------------------
// CUSTOMERS RENDER & FILTER
// ------------------------------------------------------------
function renderCustomers(list) {
    customersTableBody.innerHTML = list.map(c => `
        <tr>
            <td><strong>${c.id}</strong></td>
            <td><span class="fw-bold">${c.name}</span></td>
            <td><i class="bi bi-telephone text-muted me-1"></i> ${c.phone}</td>
            <td><span class="text-muted" style="font-size: 13px;">${formatDateTime(c.created_at)}</span></td>
        </tr>
    `).join("");
}

customersSearch.oninput = () => {
    const val = customersSearch.value.toLowerCase();
    const filtered = adminData.customers.filter(c => 
        c.name.toLowerCase().includes(val) || 
        c.phone.toLowerCase().includes(val)
    );
    renderCustomers(filtered);
};

// ------------------------------------------------------------
// RESERVATIONS RENDER & FILTER
// ------------------------------------------------------------
function renderOrders(list) {
    ordersTableBody.innerHTML = list.map(o => `
        <tr>
            <td><strong>${o.id}</strong></td>
            <td><span class="fw-bold">${o.customer_name}</span></td>
            <td><i class="bi bi-telephone text-muted me-1"></i> ${o.customer_phone}</td>
            <td><span class="text-primary fw-bold">${o.medicine_name}</span></td>
            <td><span class="badge bg-secondary">${o.quantity}</span></td>
            <td><span class="badge-status ${o.status}">${o.status}</span></td>
            <td><span class="text-muted" style="font-size: 13px;">${formatDateTime(o.reserved_at)}</span></td>
        </tr>
    `).join("");
}

ordersSearch.oninput = () => {
    const val = ordersSearch.value.toLowerCase();
    const filtered = adminData.orders.filter(o => 
        o.customer_name.toLowerCase().includes(val) || 
        o.customer_phone.toLowerCase().includes(val) || 
        o.medicine_name.toLowerCase().includes(val) || 
        o.status.toLowerCase().includes(val)
    );
    renderOrders(filtered);
};

// ------------------------------------------------------------
// CONVERSATION SESSIONS RENDER
// ------------------------------------------------------------
function renderSessions(chats) {
    const threadIds = Object.keys(chats);
    if (threadIds.length === 0) {
        sessionList.innerHTML = `<div class="text-muted text-center p-3">No sessions found</div>`;
        return;
    }
    
    sessionList.innerHTML = threadIds.map(tid => `
        <div class="session-item" data-id="${tid}" onclick="selectSession('${tid}')">
            <i class="bi bi-person-fill text-muted"></i>
            <span class="text-truncate">${tid}</span>
        </div>
    `).join("");
}

function selectSession(threadId) {
    // Set active item class
    document.querySelectorAll(".session-item").forEach(item => {
        item.classList.toggle("active", item.getAttribute("data-id") === threadId);
    });
    
    // Header
    chatViewerHeader.innerHTML = `<i class="bi bi-person-fill text-primary"></i> Chat Log: <strong>${threadId}</strong>`;
    
    // Messages
    const msgs = adminData.chats[threadId] || [];
    if (msgs.length === 0) {
        chatViewerMessages.innerHTML = `
            <div class="chat-empty-state">
                <i class="bi bi-chat-dots"></i>
                <p>No messages in this session.</p>
            </div>
        `;
        return;
    }
    
    // Render Dialogue Bubbles
    chatViewerMessages.innerHTML = msgs.map(m => {
        const isUser = m.role === "user";
        
        return `
            <div class="${isUser ? 'user-row' : 'assistant-row'}" style="display: flex; justify-content: ${isUser ? 'flex-end' : 'flex-start'}; margin-bottom: 10px;">
                <div class="message ${isUser ? 'user-message' : 'assistant-message'}" style="max-width: 80%; background: ${isUser ? '#2563eb' : 'white'}; color: ${isUser ? 'white' : '#1e293b'}; padding: 12px 18px; border-radius: 16px; box-shadow: 0 4px 10px rgba(0,0,0,0.03); border: ${isUser ? 'none' : '1px solid rgba(0,0,0,0.05)'}">
                    <h6 style="margin-bottom: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: ${isUser ? 'rgba(255,255,255,0.7)' : '#64748b'};">${isUser ? 'User' : 'Assistant'}</h6>
                    <p style="margin: 0; font-size: 14px; font-weight: 500; line-height: 1.5; white-space: pre-wrap;">${m.content}</p>
                </div>
            </div>
        `;
    }).join("");
    
    // Scroll chat window to bottom
    chatViewerMessages.scrollTop = chatViewerMessages.scrollHeight;
}

// ------------------------------------------------------------
// DATE HELPER
// ------------------------------------------------------------
function formatDateTime(isoString) {
    if (!isoString) return "";
    const date = new Date(isoString);
    return date.toLocaleString();
}

// Load data on page entry
loadAdminData();
