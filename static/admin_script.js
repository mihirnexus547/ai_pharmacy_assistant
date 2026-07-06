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

        // Populate dropdowns in addOrderModal
        const orderCustomerSelect = document.getElementById("orderCustomerSelect");
        const orderMedicineSelect = document.getElementById("orderMedicineSelect");
        if (orderCustomerSelect) {
            orderCustomerSelect.innerHTML = `<option value="" disabled selected>Choose a customer...</option>` + 
                adminData.customers.map(c => `<option value="${c.id}">${c.name} (${c.phone})</option>`).join("");
        }
        if (orderMedicineSelect) {
            orderMedicineSelect.innerHTML = `<option value="" disabled selected>Choose a medicine...</option>` + 
                adminData.medicines.map(m => `<option value="${m.id}">${m.name} (Stock: ${m.stock})</option>`).join("");
        }
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
            <td style="text-align: center;">
                <button class="btn btn-outline-danger btn-sm" onclick="confirmDeleteMedicine(${m.id}, '${m.name.replace(/'/g, "\\'")}')" style="border-radius: 50px; font-weight: 600; padding: 4px 12px; font-size: 13px;">
                    <i class="bi bi-trash-fill"></i> Delete
                </button>
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
            <td style="text-align: center;">
                <button class="btn btn-outline-danger btn-sm" onclick="confirmDeleteCustomer(${c.id}, '${c.name.replace(/'/g, "\\'")}')" style="border-radius: 50px; font-weight: 600; padding: 4px 12px; font-size: 13px;">
                    <i class="bi bi-trash-fill"></i> Delete
                </button>
            </td>
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
            <td style="text-align: center;">
                <button class="btn btn-outline-danger btn-sm" onclick="confirmDeleteOrder(${o.id})" style="border-radius: 50px; font-weight: 600; padding: 4px 12px; font-size: 13px;">
                    <i class="bi bi-trash-fill"></i> Delete
                </button>
            </td>
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
    
    // Header with Delete Button
    chatViewerHeader.innerHTML = `
        <div class="d-flex align-items-center justify-content-between w-100" style="width: 100%;">
            <div>
                <i class="bi bi-person-fill text-primary"></i> Chat Log: <strong>${threadId}</strong>
            </div>
            <button class="btn btn-outline-danger btn-sm" onclick="confirmDeleteChat('${threadId}')" style="border-radius: 50px; font-weight: 600; padding: 4px 12px; font-size: 13px;">
                <i class="bi bi-trash-fill"></i> Delete Session
            </button>
        </div>
    `;
    
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

// Logout Handler
const adminLogoutBtn = document.getElementById("adminLogoutBtn");
if (adminLogoutBtn) {
    adminLogoutBtn.onclick = async () => {
        try {
            const res = await fetch("/api/admin/logout", { method: "POST" });
            if (res.ok) {
                window.location.href = "/login";
            }
        } catch (err) {
            console.error("Logout failed:", err);
        }
    };
}

// Delete Customer Handler
async function confirmDeleteCustomer(id, name) {
    if (confirm(`Are you sure you want to delete customer "${name}"? This will also delete all reservations associated with this customer.`)) {
        try {
            const res = await fetch(`/api/admin/customers/${id}`, {
                method: "DELETE"
            });
            const data = await res.json();
            if (res.ok) {
                alert("Customer deleted successfully.");
                loadAdminData(); // Refresh UI tables
            } else {
                alert("Error deleting customer: " + (data.detail || "Unknown error"));
            }
        } catch (err) {
            console.error("Delete customer error:", err);
            alert("Failed to delete customer.");
        }
    }
}

// Add Customer Form Handler
const addCustomerForm = document.getElementById("addCustomerForm");
const addCustomerError = document.getElementById("addCustomerError");

if (addCustomerForm) {
    addCustomerForm.onsubmit = async (e) => {
        e.preventDefault();
        addCustomerError.classList.add("d-none");
        
        const name = document.getElementById("customerName").value;
        const phone = document.getElementById("customerPhone").value;
        
        try {
            const res = await fetch("/api/admin/customers", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ name, phone })
            });
            
            const data = await res.json();
            
            if (res.ok) {
                // Clear and hide modal
                addCustomerForm.reset();
                const modalEl = document.getElementById("addCustomerModal");
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
                
                alert("Customer added successfully!");
                loadAdminData(); // Refresh UI tables
            } else {
                addCustomerError.textContent = data.detail || "An error occurred.";
                addCustomerError.classList.remove("d-none");
            }
        } catch (err) {
            console.error("Add customer error:", err);
            addCustomerError.textContent = "Failed to add customer. Please try again.";
            addCustomerError.classList.remove("d-none");
        }
    };
}

// Delete Medicine Handler
async function confirmDeleteMedicine(id, name) {
    if (confirm(`Are you sure you want to delete medicine "${name}"? This will also delete all reservations associated with this medicine.`)) {
        try {
            const res = await fetch(`/api/admin/medicines/${id}`, {
                method: "DELETE"
            });
            const data = await res.json();
            if (res.ok) {
                alert("Medicine deleted successfully.");
                loadAdminData(); // Refresh UI tables
            } else {
                alert("Error deleting medicine: " + (data.detail || "Unknown error"));
            }
        } catch (err) {
            console.error("Delete medicine error:", err);
            alert("Failed to delete medicine.");
        }
    }
}

// Delete Reservation (Order) Handler
async function confirmDeleteOrder(id) {
    if (confirm(`Are you sure you want to delete reservation ID ${id}? This will restore the reserved stock.`)) {
        try {
            const res = await fetch(`/api/admin/orders/${id}`, {
                method: "DELETE"
            });
            const data = await res.json();
            if (res.ok) {
                alert("Reservation deleted successfully and stock restored.");
                loadAdminData(); // Refresh UI tables
            } else {
                alert("Error deleting reservation: " + (data.detail || "Unknown error"));
            }
        } catch (err) {
            console.error("Delete reservation error:", err);
            alert("Failed to delete reservation.");
        }
    }
}

// Delete Chat Session Handler
async function confirmDeleteChat(threadId) {
    if (confirm(`Are you sure you want to delete the entire conversation history for session "${threadId}"? This action cannot be undone.`)) {
        try {
            const res = await fetch(`/api/admin/chats/${threadId}`, {
                method: "DELETE"
            });
            const data = await res.json();
            if (res.ok) {
                alert("Conversation log deleted successfully.");
                
                // Clear the chat viewer right panel
                chatViewerHeader.innerHTML = `<i class="bi bi-chat-left-text"></i> Select a conversation log`;
                chatViewerMessages.innerHTML = `
                    <div class="chat-empty-state">
                        <i class="bi bi-chat-square-dots"></i>
                        <h5>No Session Selected</h5>
                        <p>Select a thread ID from the list on the left to review the conversation log history.</p>
                    </div>
                `;
                
                loadAdminData(); // Refresh UI tables
            } else {
                alert("Error deleting conversation log: " + (data.detail || "Unknown error"));
            }
        } catch (err) {
            console.error("Delete chat error:", err);
            alert("Failed to delete conversation log.");
        }
    }
}

// Add Medicine Form Handler
const addMedicineForm = document.getElementById("addMedicineForm");
const addMedicineError = document.getElementById("addMedicineError");

if (addMedicineForm) {
    addMedicineForm.onsubmit = async (e) => {
        e.preventDefault();
        addMedicineError.classList.add("d-none");
        
        const name = document.getElementById("medicineName").value;
        const generic_name = document.getElementById("medicineGenericName").value;
        const strength = document.getElementById("medicineStrength").value;
        const manufacturer = document.getElementById("medicineManufacturer").value;
        const price = parseFloat(document.getElementById("medicinePrice").value);
        const stock = parseInt(document.getElementById("medicineStock").value);
        
        try {
            const res = await fetch("/api/admin/medicines", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ name, generic_name, strength, manufacturer, price, stock })
            });
            
            const data = await res.json();
            
            if (res.ok) {
                addMedicineForm.reset();
                const modalEl = document.getElementById("addMedicineModal");
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
                
                alert("Medicine added successfully!");
                loadAdminData();
            } else {
                addMedicineError.textContent = data.detail || "An error occurred.";
                addMedicineError.classList.remove("d-none");
            }
        } catch (err) {
            console.error("Add medicine error:", err);
            addMedicineError.textContent = "Failed to add medicine.";
            addMedicineError.classList.remove("d-none");
        }
    };
}

// Add Order Form Handler
const addOrderForm = document.getElementById("addOrderForm");
const addOrderError = document.getElementById("addOrderError");

if (addOrderForm) {
    addOrderForm.onsubmit = async (e) => {
        e.preventDefault();
        addOrderError.classList.add("d-none");
        
        const customer_id = parseInt(document.getElementById("orderCustomerSelect").value);
        const medicine_id = parseInt(document.getElementById("orderMedicineSelect").value);
        const quantity = parseInt(document.getElementById("orderQuantity").value);
        
        try {
            const res = await fetch("/api/admin/orders", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ customer_id, medicine_id, quantity })
            });
            
            const data = await res.json();
            
            if (res.ok) {
                addOrderForm.reset();
                const modalEl = document.getElementById("addOrderModal");
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
                
                alert("Reservation created successfully!");
                loadAdminData();
            } else {
                addOrderError.textContent = data.detail || "An error occurred.";
                addOrderError.classList.remove("d-none");
            }
        } catch (err) {
            console.error("Add reservation error:", err);
            addOrderError.textContent = "Failed to create reservation.";
            addOrderError.classList.remove("d-none");
        }
    };
}
