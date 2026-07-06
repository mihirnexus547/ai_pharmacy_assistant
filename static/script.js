/* ============================================================
   AI Pharmacy Assistant
   script.js
   Upgraded Premium Version
============================================================ */

// DOM Elements
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const clearBtn = document.getElementById("clearBtn");
const clearBtnMobile = document.getElementById("clearBtnMobile");
const micBtnMobile = document.getElementById("micBtnMobile");
const chatContainer = document.getElementById("chatContainer");
const thinkingIndicator = document.getElementById("thinkingIndicator");
const connectionStatus = document.getElementById("connectionStatus");
const voiceStatus = document.getElementById("voiceStatus");
const waveform = document.getElementById("waveform");
const audioPlayer = document.getElementById("audioPlayer");
const textInput = document.getElementById("textInput");
const sendBtn = document.getElementById("sendBtn");
const suggestionsContainer = document.getElementById("suggestionsContainer");
const logoutBtn = document.getElementById("logoutBtn");


// Web Audio & WebSocket Globals
let socket = null;
let audioContext = null;
let processor = null;
let source = null;
let mediaStream = null;

// Audio Visualizer Globals
let visualizerId = null;
let micAnalyser = null;
let assistantAnalyser = null;
let currentAnalyser = null;
let assistantSourceConnected = false;
const waveformSpans = document.querySelectorAll("#waveform span");

// Conversation State
let SESSION_ID = "default";
let lastTranscript = "";

// Dynamic WebSocket URL
function getWebSocketUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws/audio?session_id=${encodeURIComponent(SESSION_ID)}`;
}


/* ============================================================
    TIME HELPERS
============================================================ */
function currentTime() {
    return new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
    });
}

/* ============================================================
    AUTO SCROLL
============================================================ */
function scrollBottom() {
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: "smooth"
    });
}

/* ============================================================
    UI STATUS & BADGES
============================================================ */
function setStatus(text) {
    voiceStatus.innerHTML = text;
}

function setConnection(text, colorClass) {
    connectionStatus.className = `status-badge ${colorClass}`;
    let dotColor = "var(--muted)";
    if (colorClass === "connected" || colorClass === "listening") dotColor = "var(--success)";
    else if (colorClass === "speaking") dotColor = "var(--primary)";
    else if (colorClass === "thinking-state") dotColor = "#f59e0b"; // amber/warning
    else if (colorClass === "disconnected") dotColor = "var(--danger)";
    
    connectionStatus.innerHTML = `
        <span class="dot" style="background-color: ${dotColor}"></span>
        ${text}
    `;
}

/* ============================================================
    THINKING INDICATOR
============================================================ */
function showThinking() {
    thinkingIndicator.classList.add("show");
    scrollBottom();
}

function hideThinking() {
    thinkingIndicator.classList.remove("show");
}

/* ============================================================
    CHAT BUBBLES
============================================================ */
function addAssistantMessage(text) {
    // Process markdown-like line breaks
    const formattedText = text.replace(/\n/g, '<br>');
    
    const wrapper = document.createElement("div");
    wrapper.className = "assistant-row";
    wrapper.innerHTML = `
        <div class="avatar assistant-avatar">
            <i class="bi bi-robot"></i>
        </div>
        <div>
            <div class="message assistant-message">
                <h6>PharmAssist</h6>
                <p>${formattedText}</p>
            </div>
            <div class="time">
                ${currentTime()}
            </div>
        </div>
    `;
    chatContainer.appendChild(wrapper);
    scrollBottom();
}

function addUserMessage(text) {
    const wrapper = document.createElement("div");
    wrapper.className = "user-row";
    wrapper.innerHTML = `
        <div>
            <div class="message user-message">
                <h6>You</h6>
                <p>${text}</p>
            </div>
            <div class="time" style="text-align:right">
                ${currentTime()}
            </div>
        </div>
        <div class="avatar user-avatar">
            <i class="bi bi-person-fill"></i>
        </div>
    `;
    chatContainer.appendChild(wrapper);
    scrollBottom();
}

/* ============================================================
    WELCOME MESSAGE
============================================================ */
function welcomeMessage() {
    addAssistantMessage(
        `Hello 👋 <strong>${SESSION_ID}</strong><br><br>` +
        "I am your AI Pharmacy Assistant. You can ask me about medicine availability, details, orders, and business hours.<br><br>" +
        "<em>Try speaking with me or type a message below!</em>"
    );
}

/* ============================================================
    CLEAR CHAT
============================================================ */
const clearAction = () => {
    chatContainer.innerHTML = "";
    welcomeMessage();
};

clearBtn.onclick = clearAction;
if (clearBtnMobile) {
    clearBtnMobile.onclick = clearAction;
}

/* ============================================================
    AUDIO VISUALIZATION (REAL-TIME)
============================================================ */
function startVisualizer() {
    if (visualizerId) cancelAnimationFrame(visualizerId);

    const bufferLength = currentAnalyser ? currentAnalyser.frequencyBinCount : 0;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {
        if (!currentAnalyser) {
            resetWaveformHeights();
            return;
        }
        visualizerId = requestAnimationFrame(draw);
        currentAnalyser.getByteFrequencyData(dataArray);

        for (let i = 0; i < waveformSpans.length; i++) {
            const dataIndex = Math.floor((i / waveformSpans.length) * bufferLength);
            const value = dataArray[dataIndex] || 0;
            const percent = value / 255;
            const height = Math.max(6, percent * 38);
            waveformSpans[i].style.height = `${height}px`;
        }
    }
    draw();
}

function stopVisualizer() {
    if (visualizerId) {
        cancelAnimationFrame(visualizerId);
        visualizerId = null;
    }
    resetWaveformHeights();
}

function resetWaveformHeights() {
    waveformSpans.forEach(span => {
        span.style.height = "6px";
    });
}

function setupAssistantAnalyser() {
    if (assistantSourceConnected || !audioContext) return;
    try {
        const sourceNode = audioContext.createMediaElementSource(audioPlayer);
        assistantAnalyser = audioContext.createAnalyser();
        assistantAnalyser.fftSize = 32;
        sourceNode.connect(assistantAnalyser);
        assistantAnalyser.connect(audioContext.destination);
        assistantSourceConnected = true;
    } catch (e) {
        console.error("Error setting up assistant analyser:", e);
    }
}

/* ============================================================
    AUDIO PLAYER EVENT HANDLERS
============================================================ */
audioPlayer.onplay = () => {
    setStatus("🔊 Speaking");
    setConnection("Speaking", "speaking");
    waveform.style.opacity = "1";
    
    // Switch visualizer to assistant audio
    if (assistantAnalyser) {
        currentAnalyser = assistantAnalyser;
        startVisualizer();
    }
};

audioPlayer.onended = () => {
    setStatus("🎤 Listening");
    setConnection("Listening", "listening");
    waveform.style.opacity = "0.7";
    
    // Revert visualizer to microphone audio
    if (micAnalyser) {
        currentAnalyser = micAnalyser;
        startVisualizer();
    } else {
        stopVisualizer();
    }
};

/* ============================================================
    BARGE-IN / INTERRUPT SPEECH
============================================================ */
function interruptAssistantSpeech() {
    if (!audioPlayer.paused) {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        
        // Revert UI to listening state
        setStatus("🎤 Listening");
        setConnection("Listening", "listening");
        waveform.style.opacity = "0.7";
        
        if (micAnalyser) {
            currentAnalyser = micAnalyser;
            startVisualizer();
        } else {
            stopVisualizer();
        }
        console.log("Barge-in: Assistant speech interrupted.");
    }
}


/* ============================================================
    WEBSOCKET (VOICE CHAT)
============================================================ */
async function startVoiceChat() {
    setStatus("Connecting...");
    setConnection("Connecting...", "thinking-state");

    const wsUrl = getWebSocketUrl();
    socket = new WebSocket(wsUrl);
    socket.binaryType = "arraybuffer";

    socket.onopen = async () => {
        try {
            mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: true
            });

            audioContext = new AudioContext({
                sampleRate: 16000
            });

            await audioContext.audioWorklet.addModule("/static/processor.js");

            // Setup Assistant Analyser for TTS response visualization
            setupAssistantAnalyser();

            source = audioContext.createMediaStreamSource(mediaStream);
            
            // Setup Mic Analyser for user voice visualization
            micAnalyser = audioContext.createAnalyser();
            micAnalyser.fftSize = 32;
            source.connect(micAnalyser);

            processor = new AudioWorkletNode(audioContext, "pcm-processor");

            processor.port.onmessage = (event) => {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(event.data);
                }
            };

            source.connect(processor);
            processor.connect(audioContext.destination);

            // State changes
            startBtn.disabled = true;
            stopBtn.disabled = false;
            if (micBtnMobile) {
                micBtnMobile.innerHTML = '<i class="bi bi-stop-fill"></i>';
                micBtnMobile.classList.add("listening-active");
                micBtnMobile.title = "Stop Listening";
            }
            
            setStatus("🎤 Listening");
            setConnection("Connected", "connected");
            waveform.style.opacity = "0.7";

            // Run visualizer pointing to microphone input
            currentAnalyser = micAnalyser;
            startVisualizer();

        } catch (err) {
            console.error("Microphone or AudioContext Error:", err);
            setStatus("Mic Access Denied");
            setConnection("Error", "disconnected");
            stopVoiceChat();
        }
    };

    socket.onmessage = async (event) => {
        // String messages = Transcription and Assistant response texts
        if (typeof event.data === "string") {
            const message = JSON.parse(event.data);

            if (message.type === "transcript") {
                if (message.text && message.text.trim()) {
                    interruptAssistantSpeech();
                }
                lastTranscript = message.text;
                setStatus(`🎙️ You: "${message.text}..."`);
            }


            if (message.type === "assistant") {
                // Post user text and assistant text to bubbles
                if (lastTranscript) {
                    addUserMessage(lastTranscript);
                    lastTranscript = "";
                }
                addAssistantMessage(message.text);
            }
            return;
        }

        // Binary messages = Audio response (MP3 bytes)
        console.log("Received audio chunk:", event.data.byteLength, "bytes");
        const blob = new Blob([event.data], { type: "audio/mpeg" });
        const url = URL.createObjectURL(blob);
        audioPlayer.src = url;
        try {
            await audioPlayer.play();
        } catch (err) {
            console.error("Audio playback error:", err);
        }
    };

    socket.onerror = (err) => {
        console.error("WebSocket Voice Error:", err);
        setStatus("Connection Error");
        setConnection("Error", "disconnected");
    };

    socket.onclose = () => {
        setStatus("Stopped");
        setConnection("Disconnected", "disconnected");
        cleanupVoiceElements();
    };
}

async function stopVoiceChat() {
    if (socket) {
        socket.close();
    }
    cleanupVoiceElements();
}

async function cleanupVoiceElements() {
    stopVisualizer();

    if (processor) {
        processor.disconnect();
        processor = null;
    }
    if (source) {
        source.disconnect();
        source = null;
    }
    if (audioContext) {
        if (audioContext.state !== "closed") {
            await audioContext.close();
        }
        audioContext = null;
    }
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }

    micAnalyser = null;
    currentAnalyser = null;

    startBtn.disabled = false;
    stopBtn.disabled = true;
    if (micBtnMobile) {
        micBtnMobile.innerHTML = '<i class="bi bi-mic-fill"></i>';
        micBtnMobile.classList.remove("listening-active");
        micBtnMobile.title = "Start Listening";
    }
    waveform.style.opacity = "0.3";
}

startBtn.onclick = startVoiceChat;
stopBtn.onclick = stopVoiceChat;

if (micBtnMobile) {
    micBtnMobile.onclick = () => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            stopVoiceChat();
        } else {
            startVoiceChat();
        }
    };
}

/* ============================================================
    TEXT CHAT (HTTP POST)
============================================================ */
async function sendTextMessage(messageText) {
    if (!messageText.trim()) return;

    // Stop any playing assistant voice
    interruptAssistantSpeech();

    // Render User bubble
    addUserMessage(messageText);

    textInput.value = "";

    // Show Thinking indicator
    showThinking();

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                session_id: SESSION_ID,
                message: messageText
            })
        });

        if (!response.ok) {
            throw new Error(`Server returned code ${response.status}`);
        }

        const data = await response.json();
        
        // Hide Thinking indicator and render Assistant bubble
        hideThinking();
        addAssistantMessage(data.response);

    } catch (err) {
        console.error("Text chat error:", err);
        hideThinking();
        addAssistantMessage("Sorry, I encountered an error processing your request. Please try again.");
    }
}

// Trigger text chat on button click or Enter key
sendBtn.onclick = () => {
    sendTextMessage(textInput.value);
};

textInput.onkeydown = (event) => {
    if (event.key === "Enter") {
        sendTextMessage(textInput.value);
    }
};

/* ============================================================
    SUGGESTION CHIPS
============================================================ */
document.querySelectorAll(".suggestion-chip").forEach(chip => {
    chip.onclick = () => {
        const msg = chip.getAttribute("data-msg");
        sendTextMessage(msg);
    };
});

/* ============================================================
    SESSION ID MODAL & BADGE LOGIC
============================================================ */
const sessionModal = document.getElementById("sessionModal");
const sessionInput = document.getElementById("sessionInput");
const sessionSubmitBtn = document.getElementById("sessionSubmitBtn");
const sessionBadge = document.getElementById("sessionBadge");
const sessionNameText = document.getElementById("sessionNameText");

function initSession() {
    const savedSession = sessionStorage.getItem("session_id");
    if (savedSession) {
        SESSION_ID = savedSession;
        sessionNameText.innerText = SESSION_ID;
        welcomeMessage();
    } else {
        showSessionModal();
    }
}

function showSessionModal() {
    sessionInput.value = SESSION_ID === "default" ? "" : SESSION_ID;
    sessionModal.classList.add("show");
    setTimeout(() => sessionInput.focus(), 300);
}

function hideSessionModal() {
    sessionModal.classList.remove("show");
}

function submitSession() {
    const val = sessionInput.value.trim();
    if (!val) return;
    
    SESSION_ID = val;
    sessionStorage.setItem("session_id", SESSION_ID);
    sessionNameText.innerText = SESSION_ID;
    hideSessionModal();
    
    // Clear chat and show welcome message for new session
    chatContainer.innerHTML = "";
    welcomeMessage();
}

sessionSubmitBtn.onclick = () => {
    submitSession();
};

sessionInput.onkeydown = (e) => {
    if (e.key === "Enter") {
        submitSession();
    }
};

sessionBadge.onclick = () => {
    showSessionModal();
};

logoutBtn.onclick = () => {
    sessionStorage.removeItem("session_id");
    SESSION_ID = "default";
    sessionNameText.innerText = "Default";
    chatContainer.innerHTML = "";
    showSessionModal();
};

// Initialize the session on page load
initSession();