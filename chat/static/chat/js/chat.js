/* ============================================================
   Soul Questions — Chat UI JavaScript
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
    renderMessages(INITIAL_MESSAGES);
    scrollToBottom();
    setupTextarea();
    setupSidebar();
    setupSettings();
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

// ---- Settings modal ----

function setupSettings() {
    const btn = document.getElementById('settingsBtn');
    const modal = document.getElementById('settingsModal');
    const closeBtn = document.getElementById('closeSettings');
    const saveBtn = document.getElementById('saveSettingsBtn');
    const clearBtn = document.getElementById('clearSettingsBtn');

    btn.addEventListener('click', () => {
        modal.style.display = 'flex';
        loadSettings();
    });

    closeBtn.addEventListener('click', () => { modal.style.display = 'none'; });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            modal.style.display = 'none';
        }
    });

    saveBtn.addEventListener('click', saveSettings);
    clearBtn.addEventListener('click', clearSettings);
}

async function loadSettings() {
    try {
        const res = await fetch('/settings/', {
            headers: { 'X-CSRFToken': CSRF_TOKEN },
        });
        const data = await res.json();
        document.getElementById('settingsModel').value = data.llm_model || 'gpt-4o-mini';
        document.getElementById('settingsApiKey').value = '';

        const status = document.getElementById('apiKeyStatus');
        if (data.api_key_set) {
            status.textContent = 'Key saved: ' + data.api_key_masked;
            status.style.color = '#22c55e';
        } else {
            status.textContent = 'No API key configured — using server default';
            status.style.color = '';
        }
    } catch (err) {
        console.error('Failed to load settings', err);
    }
}

async function saveSettings() {
    const model = document.getElementById('settingsModel').value;
    const apiKey = document.getElementById('settingsApiKey').value.trim();
    const feedback = document.getElementById('settingsFeedback');

    const body = {
        llm_model: model || 'gpt-4o-mini',
    };

    // Only include api_key if the user typed a new one
    if (apiKey) {
        body.api_key = apiKey;
    } else {
        // Preserve existing key by not sending the field — backend merges
        // But we need to send something; fetch current key state
        const res = await fetch('/settings/');
        const current = await res.json();
        if (current.api_key_set) {
            // Don't overwrite with empty — just send provider+model
        } else {
            body.api_key = '';
        }
    }

    try {
        const res = await fetch('/settings/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN,
            },
            body: JSON.stringify(body),
        });
        const data = await res.json();

        feedback.style.display = 'block';
        if (data.saved) {
            feedback.className = 'settings-feedback success';
            feedback.textContent = 'Settings saved!';
            setTimeout(() => { feedback.style.display = 'none'; }, 2000);
            loadSettings();
        } else {
            feedback.className = 'settings-feedback error';
            feedback.textContent = data.error || 'Failed to save';
        }
    } catch (err) {
        feedback.style.display = 'block';
        feedback.className = 'settings-feedback error';
        feedback.textContent = 'Network error';
    }
}

async function clearSettings() {
    try {
        await fetch('/settings/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN,
            },
            body: JSON.stringify({
                llm_model: 'gpt-4o-mini',
                api_key: '',
            }),
        });
        document.getElementById('settingsModel').value = 'gpt-4o-mini';
        document.getElementById('settingsApiKey').value = '';
        document.getElementById('apiKeyStatus').textContent = 'No API key configured — using server default';
        document.getElementById('apiKeyStatus').style.color = '';

        const feedback = document.getElementById('settingsFeedback');
        feedback.style.display = 'block';
        feedback.className = 'settings-feedback success';
        feedback.textContent = 'Settings cleared';
        setTimeout(() => { feedback.style.display = 'none'; }, 2000);
    } catch (err) {
        console.error('Failed to clear settings', err);
    }
}
