/* ============================================================
   Soul Questions — Chat UI JavaScript
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
    renderMessages(INITIAL_MESSAGES);
    scrollToBottom();
    setupTextarea();
    setupSidebar();
});

// ---- Message rendering ----

function renderMessages(messages) {
    const container = document.getElementById('messagesList');
    container.innerHTML = '';
    messages.forEach(msg => appendMessage(msg));
}

function appendMessage(msg) {
    const container = document.getElementById('messagesList');
    const div = document.createElement('div');
    div.className = `message ${msg.role}-message`;

    const roleLabel = msg.role === 'user' ? 'You' : 'Soul Questions';
    let html = `
        <div class="message-role">${roleLabel}</div>
        <div class="bubble ${msg.role}-bubble">${escapeHtml(msg.content)}</div>
    `;

    // Sources
    if (msg.sources && msg.sources.length > 0) {
        html += '<div class="sources-section"><div class="sources-title">Sources</div>';
        msg.sources.forEach(src => {
            const title = src.title || 'Source';
            const game = src.game ? ` <span class="source-game">(${escapeHtml(src.game)})</span>` : '';
            const link = src.url ? `<a href="${escapeHtml(src.url)}" target="_blank" rel="noopener">${escapeHtml(title)}</a>` : escapeHtml(title);
            const snippet = src.snippet ? `<div class="source-snippet">${escapeHtml(src.snippet.substring(0, 150))}...</div>` : '';
            html += `<div class="source-item">${link}${game}${snippet}</div>`;
        });
        html += '</div>';
    }

    // Recommendations
    if (msg.recommendations && msg.recommendations.length > 0) {
        html += '<div class="recommendations">';
        msg.recommendations.forEach(rec => {
            html += `<button class="rec-chip" onclick="askSuggestion(this)">${escapeHtml(rec)}</button>`;
        });
        html += '</div>';
    }

    div.innerHTML = html;
    container.appendChild(div);
}

// ---- Send message ----

async function sendMessage(event) {
    event.preventDefault();
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message) return;

    // Clear welcome if visible
    const welcome = document.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    // Show user message
    appendMessage({ role: 'user', content: message, sources: [], recommendations: [] });
    input.value = '';
    autoResize(input);
    scrollToBottom();

    // Show typing indicator
    const typing = document.getElementById('typingIndicator');
    typing.style.display = 'block';
    scrollToBottom();

    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;

    try {
        const response = await fetch(`/session/${SESSION_ID}/send/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN,
            },
            body: JSON.stringify({ message }),
        });

        const data = await response.json();
        typing.style.display = 'none';

        if (response.ok) {
            appendMessage({
                role: 'assistant',
                content: data.answer,
                sources: data.sources || [],
                recommendations: data.recommendations || [],
            });
            // Update title
            if (data.session_title) {
                document.getElementById('chatTitle').textContent = data.session_title;
                const titleEl = document.getElementById(`title-${SESSION_ID}`);
                if (titleEl) titleEl.textContent = data.session_title;
            }
        } else {
            appendMessage({
                role: 'assistant',
                content: data.error || 'Something went wrong. Please try again.',
                sources: [],
                recommendations: [],
            });
        }
    } catch (err) {
        typing.style.display = 'none';
        appendMessage({
            role: 'assistant',
            content: 'Network error. Please check your connection and try again.',
            sources: [],
            recommendations: [],
        });
    }

    sendBtn.disabled = false;
    scrollToBottom();
}

// ---- Suggestion chips ----

function askSuggestion(el) {
    const text = el.textContent || el.innerText;
    document.getElementById('messageInput').value = text;
    document.getElementById('chatForm').dispatchEvent(new Event('submit'));
}

// ---- Session management ----

function renameSession(sessionId) {
    const titleEl = document.getElementById(`title-${sessionId}`);
    const currentTitle = titleEl ? titleEl.textContent : '';
    const newTitle = prompt('Rename session:', currentTitle);
    if (!newTitle || newTitle === currentTitle) return;

    fetch(`/session/${sessionId}/rename/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN,
        },
        body: JSON.stringify({ title: newTitle }),
    })
    .then(r => r.json())
    .then(data => {
        if (data.title && titleEl) {
            titleEl.textContent = data.title;
            if (sessionId === SESSION_ID) {
                document.getElementById('chatTitle').textContent = data.title;
            }
        }
    });
}

function deleteSession(sessionId) {
    if (!confirm('Delete this conversation?')) return;

    fetch(`/session/${sessionId}/delete/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN,
        },
    })
    .then(r => r.json())
    .then(data => {
        if (data.deleted) {
            if (sessionId === SESSION_ID) {
                window.location.href = '/';
            } else {
                const item = document.querySelector(`[data-session-id="${sessionId}"]`);
                if (item) item.remove();
            }
        }
    });
}

// ---- Utilities ----

function scrollToBottom() {
    const container = document.getElementById('messagesContainer');
    requestAnimationFrame(() => {
        container.scrollTop = container.scrollHeight;
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function setupTextarea() {
    const textarea = document.getElementById('messageInput');
    textarea.addEventListener('input', () => autoResize(textarea));
    textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            document.getElementById('chatForm').dispatchEvent(new Event('submit'));
        }
    });
}

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 150) + 'px';
}

function setupSidebar() {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    toggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 &&
            sidebar.classList.contains('open') &&
            !sidebar.contains(e.target) &&
            e.target !== toggle) {
            sidebar.classList.remove('open');
        }
    });
}
