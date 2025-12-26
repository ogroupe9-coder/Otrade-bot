// API Configuration
const API_BASE_URL = 'https://otrade-bot.onrender.com';

// State Management
let sessionId = null;
let messageHistory = [];

// DOM Elements
const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const newChatBtn = document.getElementById('newChatBtn');
const sessionIdDisplay = document.getElementById('sessionId');
const typingIndicator = document.getElementById('typingIndicator');
const statusText = document.getElementById('status-text');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeSession();
    setupEventListeners();
    adjustTextareaHeight();
});

// Generate or retrieve session ID
function initializeSession() {
    const savedSession = localStorage.getItem('otrade_session_id');
    const savedMessages = localStorage.getItem('otrade_messages');

    if (savedSession) {
        sessionId = savedSession;
        if (savedMessages) {
            messageHistory = JSON.parse(savedMessages);
            restoreMessages();
        }
    } else {
        sessionId = generateSessionId();
        localStorage.setItem('otrade_session_id', sessionId);
    }

    sessionIdDisplay.textContent = sessionId.substring(0, 12) + '...';
}

// Generate unique session ID
function generateSessionId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 9);
    return `session_${timestamp}_${random}`;
}

// Setup event listeners
function setupEventListeners() {
    // Send button
    sendBtn.addEventListener('click', sendMessage);

    // Enter key to send (Shift+Enter for new line)
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    messageInput.addEventListener('input', adjustTextareaHeight);

    // Enable/disable send button
    messageInput.addEventListener('input', () => {
        sendBtn.disabled = messageInput.value.trim() === '';
    });

    // New chat button
    newChatBtn.addEventListener('click', startNewChat);
}

// Adjust textarea height dynamically
function adjustTextareaHeight() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
}

// Send message to bot
async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message) return;

    // Clear input and reset height
    messageInput.value = '';
    adjustTextareaHeight();
    sendBtn.disabled = true;

    // Hide welcome message if present
    hideWelcomeMessage();

    // Display user message
    addMessage('user', message);

    // Show typing indicator
    showTyping();

    try {
        // Call API
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                message: message,
                phone_number: '+0000000000' // Placeholder for testing
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Hide typing indicator
        hideTyping();

        // Display bot response
        addMessage('bot', data.response);

        // Update status if needed
        updateStatus('online');

    } catch (error) {
        console.error('Error sending message:', error);
        hideTyping();

        // Show error message
        addMessage('bot', `Sorry, I'm having trouble connecting to the server. Please try again in a moment. (Error: ${error.message})`);

        // Update status
        updateStatus('error');
    }
}

// Add message to chat
function addMessage(type, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = type === 'bot' ? '🤖' : '👤';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;

    const time = document.createElement('div');
    time.className = 'message-time';
    time.textContent = getCurrentTime();

    contentDiv.appendChild(bubble);
    contentDiv.appendChild(time);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);

    messagesContainer.appendChild(messageDiv);

    // Save to history
    messageHistory.push({ type, text, time: time.textContent });
    localStorage.setItem('otrade_messages', JSON.stringify(messageHistory));

    // Scroll to bottom
    scrollToBottom();
}

// Get current time formatted
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Show typing indicator
function showTyping() {
    typingIndicator.classList.add('active');
    scrollToBottom();
}

// Hide typing indicator
function hideTyping() {
    typingIndicator.classList.remove('active');
}

// Hide welcome message
function hideWelcomeMessage() {
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => welcomeMsg.remove(), 300);
    }
}

// Restore messages from history
function restoreMessages() {
    hideWelcomeMessage();

    messageHistory.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msg.type}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = msg.type === 'bot' ? '🤖' : '👤';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = msg.text;

        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = msg.time;

        contentDiv.appendChild(bubble);
        contentDiv.appendChild(time);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);

        messagesContainer.appendChild(messageDiv);
    });

    scrollToBottom();
}

// Start new chat
function startNewChat() {
    if (confirm('Start a new conversation? Your current chat will be saved.')) {
        // Clear messages
        messageHistory = [];
        localStorage.removeItem('otrade_messages');

        // Generate new session
        sessionId = generateSessionId();
        localStorage.setItem('otrade_session_id', sessionId);
        sessionIdDisplay.textContent = sessionId.substring(0, 12) + '...';

        // Clear UI
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">
                    <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                        <circle cx="32" cy="32" r="32" fill="url(#welcomeGradient)" opacity="0.1"/>
                        <path d="M32 16C24.28 16 18 22.28 18 30V34C18 36.21 19.79 38 22 38H26V42H38V42H42C44.21 38 46 36.21 46 34V30C46 22.28 39.72 16 32 16ZM26 32C24.9 32 24 31.1 24 30C24 28.9 24.9 28 26 28C27.1 28 28 28.9 28 30C28 31.1 27.1 32 26 32ZM38 32C36.9 32 36 31.1 36 30C36 28.9 36.9 28 38 28C39.1 28 40 28.9 40 30C40 31.1 39.1 32 38 32ZM28 46H36V48H28V46Z" fill="url(#welcomeGradient)"/>
                        <defs>
                            <linearGradient id="welcomeGradient" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
                                <stop stop-color="#667eea"/>
                                <stop offset="1" stop-color="#764ba2"/>
                            </linearGradient>
                        </defs>
                    </svg>
                </div>
                <h2>Welcome to OTRADE Bot! 👋</h2>
                <p>Your AI-powered wholesale trading assistant</p>
                <div class="feature-pills">
                    <span class="pill">📦 Product Sourcing</span>
                    <span class="pill">💰 Quote Generation</span>
                    <span class="pill">📄 Invoice Creation</span>
                </div>
                <div class="suggestions">
                    <p class="suggestions-title">Try asking:</p>
                    <button class="suggestion-btn" onclick="sendSuggestion('I want to order rice')">I want to order rice</button>
                    <button class="suggestion-btn" onclick="sendSuggestion('Show me available products')">Show me available products</button>
                    <button class="suggestion-btn" onclick="sendSuggestion('I need help with ordering')">I need help with ordering</button>
                </div>
            </div>
        `;
    }
}

// Send suggestion
function sendSuggestion(text) {
    messageInput.value = text;
    sendBtn.disabled = false;
    sendMessage();
}

// Update status indicator
function updateStatus(status) {
    const statusDot = document.querySelector('.status-dot');

    if (status === 'online') {
        statusText.textContent = 'Online';
        statusDot.style.background = '#10b981';
    } else if (status === 'error') {
        statusText.textContent = 'Connection Error';
        statusDot.style.background = '#ef4444';
    } else if (status === 'typing') {
        statusText.textContent = 'Typing...';
        statusDot.style.background = '#f59e0b';
    }
}

// Scroll to bottom of messages
function scrollToBottom() {
    setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 100);
}

// Add fadeOut animation to CSS dynamically if needed
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(-20px); }
    }
`;
document.head.appendChild(style);
