import streamlit as st

CUSTOM_CSS = """
<style>
/* === ChatGPT-like Dark Theme === */

:root {
    --bg-main: #212121;
    --bg-sidebar: #171717;
    --bg-surface: #2f2f2f;
    --bg-user-bubble: #303030;
    --text-primary: #ececec;
    --text-secondary: #8e8ea0;
    --accent: #10a37f;
    --border: #3d3d3d;
    --input-bg: #2f2f2f;
}

/* === GLOBAL === */
.stApp {
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
    font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
                 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

/* === HIDE STREAMLIT CHROME === */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.stDeployButton { display: none !important; }
[data-testid="manage-app-button"] { display: none !important; }

/* === SIDEBAR === */
section[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
}

section[data-testid="stSidebar"] > div {
    background-color: var(--bg-sidebar) !important;
    padding: 0 !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background-color: var(--bg-sidebar) !important;
    padding: 12px !important;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] span:not([class*="st-emotion"]) {
    color: var(--text-primary) !important;
}

section[data-testid="stSidebar"] h1 {
    color: var(--text-primary) !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;
    margin: 0 !important;
    padding: 0 !important;
}

section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: var(--text-secondary) !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    margin: 16px 0 6px !important;
}

section[data-testid="stSidebar"] hr {
    border-color: var(--border) !important;
    margin: 10px 0 !important;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton > button {
    background-color: transparent !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 8px 14px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    transition: background-color 0.15s, border-color 0.15s !important;
    text-align: left !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: rgba(255,255,255,0.07) !important;
    border-color: #555 !important;
}

/* Primary button override */
section[data-testid="stSidebar"] .stButton > button[kind="primary"],
section[data-testid="stSidebar"] [data-testid="baseButton-primary"] {
    background-color: var(--accent) !important;
    border-color: var(--accent) !important;
    color: white !important;
}

section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    background-color: #0d8c6d !important;
    border-color: #0d8c6d !important;
}

/* Sidebar text inputs */
section[data-testid="stSidebar"] .stTextInput > div > div > input {
    background-color: rgba(255,255,255,0.05) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
    padding: 8px 12px !important;
}

section[data-testid="stSidebar"] .stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent) !important;
}

section[data-testid="stSidebar"] .stTextInput label {
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
}

/* Sidebar alerts */
section[data-testid="stSidebar"] [data-testid="stNotification"],
section[data-testid="stSidebar"] [data-baseweb="notification"],
section[data-testid="stSidebar"] .stAlert {
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    padding: 8px 10px !important;
}

section[data-testid="stSidebar"] [data-baseweb="notification"] {
    background-color: rgba(16, 163, 127, 0.12) !important;
    border: 1px solid rgba(16, 163, 127, 0.3) !important;
}

/* Success in sidebar */
section[data-testid="stSidebar"] [data-testid="stAlert"] div {
    color: var(--accent) !important;
    font-size: 0.82rem !important;
}

/* Sidebar code blocks */
section[data-testid="stSidebar"] .stCode pre,
section[data-testid="stSidebar"] code {
    background-color: rgba(255,255,255,0.06) !important;
    color: #b5cea8 !important;
    border-radius: 6px !important;
    font-size: 0.78rem !important;
    padding: 8px 10px !important;
    border: 1px solid var(--border) !important;
}

/* Toggle */
section[data-testid="stSidebar"] [data-testid="stToggle"] label,
section[data-testid="stSidebar"] .stToggle p {
    color: var(--text-primary) !important;
    font-size: 0.88rem !important;
}

/* Toggle track */
section[data-testid="stSidebar"] [role="switch"] {
    background-color: var(--bg-surface) !important;
}

section[data-testid="stSidebar"] [role="switch"][aria-checked="true"] {
    background-color: var(--accent) !important;
}

/* Sidebar caption */
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: var(--text-secondary) !important;
    font-size: 0.78rem !important;
}

/* === MAIN CONTENT AREA === */
[data-testid="stAppViewContainer"] {
    background-color: var(--bg-main) !important;
}

[data-testid="stAppViewContainer"] > section.main {
    background-color: var(--bg-main) !important;
}

.main .block-container {
    max-width: 780px !important;
    padding-left: 24px !important;
    padding-right: 24px !important;
    padding-top: 24px !important;
    padding-bottom: 130px !important;
    margin: 0 auto !important;
}

/* === MAIN TITLE === */
.main [data-testid="stMarkdownContainer"] h1 {
    color: var(--text-primary) !important;
    font-size: 1.3rem !important;
    font-weight: 600 !important;
}

/* === CHAT MESSAGES === */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 6px 0 !important;
    gap: 14px !important;
}

/* User messages — right-aligned bubble (via JS data-role attribute) */
[data-testid="stChatMessage"][data-role="user"] {
    flex-direction: row-reverse !important;
}

[data-testid="stChatMessage"][data-role="user"] [data-testid="stChatMessageContent"] {
    background-color: var(--bg-user-bubble) !important;
    border-radius: 18px 18px 4px 18px !important;
    padding: 12px 16px !important;
    max-width: 78% !important;
    margin-left: auto !important;
}

/* Assistant messages — no bubble, clean text */
[data-testid="stChatMessage"][data-role="assistant"] [data-testid="stChatMessageContent"] {
    background-color: transparent !important;
    padding: 2px 0 2px 4px !important;
    max-width: 90% !important;
}

/* Avatar base */
[data-testid="stChatMessageAvatar"],
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"] {
    width: 34px !important;
    min-width: 34px !important;
    height: 34px !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 0.95rem !important;
    background-color: var(--bg-surface) !important;
    overflow: hidden !important;
    flex-shrink: 0 !important;
}

[data-testid="stChatMessage"][data-role="assistant"] [data-testid="stChatMessageAvatar"],
[data-testid="stChatMessage"][data-role="assistant"] [data-testid="stChatMessageAvatarAssistant"] {
    background-color: var(--accent) !important;
}

[data-testid="stChatMessage"][data-role="user"] [data-testid="stChatMessageAvatar"],
[data-testid="stChatMessage"][data-role="user"] [data-testid="stChatMessageAvatarUser"] {
    background-color: #5436DA !important;
}

/* Message text */
[data-testid="stChatMessageContent"] p {
    color: var(--text-primary) !important;
    line-height: 1.7 !important;
    font-size: 0.95rem !important;
    margin-bottom: 0.5em !important;
}

[data-testid="stChatMessageContent"] p:last-child {
    margin-bottom: 0 !important;
}

[data-testid="stChatMessageContent"] strong {
    color: #ffffff !important;
    font-weight: 600 !important;
}

[data-testid="stChatMessageContent"] code {
    background-color: rgba(0, 0, 0, 0.35) !important;
    color: #ce9178 !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-size: 0.88em !important;
}

[data-testid="stChatMessageContent"] pre {
    background-color: #1e1e2e !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 16px !important;
    overflow-x: auto !important;
}

[data-testid="stChatMessageContent"] pre code {
    background: none !important;
    color: #cdd6f4 !important;
    padding: 0 !important;
}

[data-testid="stChatMessageContent"] ul,
[data-testid="stChatMessageContent"] ol {
    color: var(--text-primary) !important;
    padding-left: 1.4em !important;
    line-height: 1.7 !important;
}

[data-testid="stChatMessageContent"] li {
    margin-bottom: 4px !important;
}

/* === CHAT INPUT === */
[data-testid="stBottom"] {
    background: linear-gradient(to top, var(--bg-main) 80%, transparent) !important;
    padding: 12px 0 16px !important;
}

[data-testid="stBottom"] > div {
    max-width: 780px !important;
    margin: 0 auto !important;
    padding: 0 24px !important;
}

[data-testid="stChatInput"] > div {
    background-color: var(--input-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3) !important;
    transition: border-color 0.2s !important;
}

[data-testid="stChatInput"] > div:focus-within {
    border-color: #555 !important;
    box-shadow: 0 2px 16px rgba(0,0,0,0.4) !important;
}

[data-testid="stChatInput"] textarea {
    background-color: transparent !important;
    color: var(--text-primary) !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
    border: none !important;
    padding: 14px 50px 14px 18px !important;
    resize: none !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-secondary) !important;
}

[data-testid="stChatInput"] button {
    background-color: var(--accent) !important;
    border-radius: 10px !important;
    border: none !important;
    color: white !important;
    opacity: 1 !important;
}

[data-testid="stChatInput"] button:disabled {
    background-color: var(--bg-surface) !important;
    opacity: 0.5 !important;
}

/* === STATUS / INFO MESSAGES === */
[data-testid="stAlert"],
[data-testid="stInfo"],
[data-testid="stWarning"],
[data-testid="stError"],
[data-testid="stSuccess"] {
    background-color: rgba(255,255,255,0.04) !important;
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    font-size: 0.88rem !important;
    padding: 10px 14px !important;
}

[data-testid="stInfo"],
.stAlert[data-baseweb="notification"][kind="info"] {
    border-left: 3px solid var(--accent) !important;
}

/* === EXPANDERS (Sources) === */
[data-testid="stExpander"] {
    background-color: rgba(255,255,255,0.03) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    margin-top: 10px !important;
    overflow: hidden !important;
}

[data-testid="stExpander"] summary {
    color: var(--text-secondary) !important;
    font-size: 0.83rem !important;
    padding: 10px 14px !important;
    cursor: pointer !important;
}

[data-testid="stExpander"] summary:hover {
    color: var(--text-primary) !important;
    background-color: rgba(255,255,255,0.04) !important;
}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background-color: transparent !important;
    padding: 8px 14px 14px !important;
}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] p {
    color: var(--text-secondary) !important;
    font-size: 0.84rem !important;
    line-height: 1.55 !important;
}

/* === CAPTION (search terms, footer) === */
.stCaption,
[data-testid="stCaptionContainer"] {
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
}

/* === DIVIDER === */
hr {
    border-color: var(--border) !important;
    margin: 12px 0 !important;
}

/* === SCROLLBAR === */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #404040; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #505050; }

/* === SOURCE BOXES === */
.source-box {
    background-color: rgba(255,255,255,0.03);
    padding: 10px 14px;
    border-radius: 8px;
    margin: 6px 0;
    font-size: 0.83em;
    color: var(--text-secondary);
    border-left: 3px solid var(--accent);
    line-height: 1.55;
}

/* === SEARCH QUERY TAGS === */
.search-query-tag {
    background-color: rgba(16, 163, 127, 0.1);
    padding: 2px 10px;
    border-radius: 20px;
    margin: 2px 3px;
    display: inline-block;
    font-size: 0.8em;
    color: var(--accent);
    border: 1px solid rgba(16, 163, 127, 0.25);
}

/* === STREAMING CURSOR === */
.streaming-cursor {
    display: inline-block;
    animation: blink 1s infinite;
    color: var(--accent);
    font-weight: 300;
}

@keyframes blink {
    0%, 49% { opacity: 1; }
    50%, 100% { opacity: 0; }
}

/* === WELCOME SCREEN === */
.welcome-container {
    text-align: center;
    padding: 60px 20px 32px;
}

.welcome-icon {
    font-size: 3rem;
    margin-bottom: 16px;
    display: block;
}

.welcome-container h2 {
    color: var(--text-primary) !important;
    font-size: 1.8rem !important;
    font-weight: 600 !important;
    margin-bottom: 10px !important;
}

.welcome-container p {
    color: var(--text-secondary) !important;
    font-size: 0.95rem !important;
    max-width: 420px !important;
    margin: 0 auto !important;
    line-height: 1.6 !important;
}

.welcome-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    margin-top: 28px;
}

.welcome-chip {
    background-color: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 10px 16px;
    font-size: 0.85rem;
    color: var(--text-secondary);
    cursor: default;
    transition: background 0.15s;
    max-width: 200px;
    text-align: left;
    line-height: 1.4;
}

/* === FOOTER === */
.chat-footer {
    display: flex;
    justify-content: center;
    gap: 24px;
    padding: 8px 0 4px;
    font-size: 0.75rem;
    color: var(--text-secondary);
    opacity: 0.7;
}

.chat-footer span {
    font-family: monospace;
}
</style>
"""

ROLE_LABEL_SCRIPT = """
<script>
(function() {
    function labelChatMessages() {
        var msgs = document.querySelectorAll('[data-testid="stChatMessage"]:not([data-role])');
        msgs.forEach(function(msg) {
            var avatarEl = msg.querySelector('[data-testid="stChatMessageAvatar"], [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"]');
            if (!avatarEl) return;
            var txt = avatarEl.textContent || '';
            var hasUserEmoji  = txt.indexOf('\\u{1F464}') !== -1 || txt.indexOf('👤') !== -1;
            var hasRobotEmoji = txt.indexOf('\\u{1F916}') !== -1 || txt.indexOf('🤖') !== -1;
            // Check data-testid of avatar element itself
            var avatarId = avatarEl.getAttribute('data-testid') || '';
            if (hasUserEmoji || avatarId.toLowerCase().includes('user')) {
                msg.setAttribute('data-role', 'user');
            } else if (hasRobotEmoji || avatarId.toLowerCase().includes('assistant')) {
                msg.setAttribute('data-role', 'assistant');
            } else {
                // Fallback: odd indices are typically user in alternating pattern
                var allMsgs = Array.from(document.querySelectorAll('[data-testid="stChatMessage"]'));
                var idx = allMsgs.indexOf(msg);
                msg.setAttribute('data-role', idx % 2 === 0 ? 'user' : 'assistant');
            }
        });
    }

    labelChatMessages();
    var observer = new MutationObserver(function(mutations) {
        var relevant = mutations.some(function(m) {
            return m.type === 'childList' && m.addedNodes.length > 0;
        });
        if (relevant) labelChatMessages();
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
"""


def inject_styles():
    """Inject the custom CSS and JS role-labeler into the Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(ROLE_LABEL_SCRIPT, unsafe_allow_html=True)
