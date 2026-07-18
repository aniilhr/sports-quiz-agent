import re
import streamlit as st

from src.generator import compile_quiz_data, parse_quiz_text
from src.database import setup_and_populate_db

SPORT_ICONS = {"Cricket": "🏏", "Football": "⚽", "Badminton": "🏸"}


# ---------------------------------------------------------------------------
# 1. Warm up the vector DB with offline facts on startup
# ---------------------------------------------------------------------------
@st.cache_resource
def prepare_knowledge_base():
    setup_and_populate_db()


prepare_knowledge_base()

# ---------------------------------------------------------------------------
# 2. Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Sports Quiz — Live", page_icon="🏆", layout="centered")

# ---------------------------------------------------------------------------
# 3. Theme — most of the heavy lifting (dropdowns, alerts, sliders, code
#    blocks) is handled by .streamlit/config.toml, which sets Streamlit's
#    *native* dark theme. That's what actually fixes text disappearing
#    against white backgrounds — those widgets render in layers that plain
#    CSS overrides can't reliably reach. This CSS only adds the custom
#    scoreboard look on top: fonts, the header, transparent glass cards,
#    and the ticker.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

    :root {
        --amber: #FFB000;
        --amber-dim: rgba(255, 176, 0, 0.16);
        --foul: #FF6B5E;
        --glass-bg: rgba(255, 255, 255, 0.035);
        --glass-border: rgba(255, 255, 255, 0.09);
        --glass-bg-strong: rgba(255, 255, 255, 0.05);
    }

    .stApp {
        background: radial-gradient(circle at 15% 0%, #1b2126 0%, #12161a 55%, #0d1013 100%);
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* keep the sidebar-toggle usable on mobile — just make the header blend in */
    header[data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer { visibility: hidden; }

    /* ---------- Sidebar ---------- */
    .panel-label {
        font-family: 'Oswald', sans-serif;
        font-weight: 600;
        letter-spacing: 0.12em;
        font-size: 0.8rem;
        color: var(--amber);
        border-bottom: 2px solid var(--amber);
        padding-bottom: 6px;
        margin: 0.4rem 0 1.2rem 0;
    }

    /* ---------- Buttons ---------- */
    .stButton > button {
        background: var(--amber);
        color: #12161A;
        font-family: 'Oswald', sans-serif;
        font-weight: 600;
        letter-spacing: 0.04em;
        border: none;
        border-radius: 8px;
        padding: 0.55rem 1rem;
        transition: transform 0.08s ease, box-shadow 0.15s ease;
    }
    .stButton > button:hover {
        box-shadow: 0 0 0 3px var(--amber-dim);
        transform: translateY(-1px);
    }
    .stButton > button:focus-visible {
        outline: 3px solid var(--amber);
        outline-offset: 2px;
    }
    .stButton > button p { color: #12161A !important; }

    /* ---------- Scoreboard header (transparent card) ---------- */
    .scoreboard-header {
        background: var(--glass-bg-strong);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 1.7rem 1.9rem;
        margin-bottom: 1.3rem;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
    }
    .sb-eyebrow {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.14em;
        opacity: 0.65;
        margin-bottom: 0.4rem;
    }
    .sb-title {
        font-family: 'Oswald', sans-serif;
        font-weight: 700;
        font-size: 2.3rem;
        letter-spacing: 0.02em;
        margin: 0;
        text-transform: uppercase;
    }
    .sb-amber { color: var(--amber); text-shadow: 0 0 18px var(--amber-dim); }
    .sb-sub { opacity: 0.7; margin-top: 0.5rem; font-size: 0.95rem; }

    /* ---------- Live ticker (signature element, transparent) ---------- */
    .ticker-wrap {
        display: flex;
        align-items: center;
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--glass-border);
        border-radius: 10px;
        overflow: hidden;
        margin: 0.4rem 0 1.4rem 0;
        height: 40px;
    }
    .live-badge {
        flex-shrink: 0;
        font-family: 'Oswald', sans-serif;
        font-weight: 600;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        color: var(--foul);
        padding: 0 0.9rem;
        border-right: 1px solid var(--glass-border);
        display: flex;
        align-items: center;
        gap: 6px;
        height: 100%;
    }
    .live-dot {
        width: 7px; height: 7px; border-radius: 50%;
        background: var(--foul);
        animation: pulse 1.4s ease-in-out infinite;
    }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.25; } }

    .ticker-track { flex: 1; overflow: hidden; white-space: nowrap; }
    .ticker-content {
        display: inline-block;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.8rem;
        color: var(--amber);
        padding-left: 100%;
        animation: ticker-scroll 28s linear infinite;
    }
    @keyframes ticker-scroll {
        0% { transform: translateX(0); }
        100% { transform: translateX(-100%); }
    }
    @media (prefers-reduced-motion: reduce) {
        .ticker-content { animation: none; padding-left: 1rem; }
        .live-dot { animation: none; }
    }

    /* ---------- Round title ---------- */
    .round-title {
        font-family: 'Oswald', sans-serif;
        font-weight: 600;
        font-size: 1.05rem;
        letter-spacing: 0.05em;
        border-left: 4px solid var(--amber);
        padding-left: 0.7rem;
        margin: 0.6rem 0 1rem 0;
        text-transform: uppercase;
    }

    /* ---------- Quiz cards — clean transparent glass ---------- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid var(--glass-border) !important;
        border-radius: 14px !important;
        padding: 0.6rem 0.4rem !important;
        margin-bottom: 1.1rem !important;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.2);
    }
    .q-tag {
        display: inline-block;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        color: #12161A;
        background: var(--amber);
        border-radius: 5px;
        padding: 2px 9px;
        margin-bottom: 0.5rem;
        letter-spacing: 0.05em;
    }
    .q-text {
        font-weight: 500;
        font-size: 1.02rem;
        margin-bottom: 0.5rem;
        line-height: 1.45;
    }
    .explain-box {
        font-size: 0.9rem;
        opacity: 0.85;
        background: var(--glass-bg);
        border-left: 3px solid var(--amber);
        border-radius: 6px;
        padding: 0.65rem 0.85rem;
        margin-top: 0.5rem;
    }

    /* radio options — subtle transparent roster rows */
    .stRadio [role="radiogroup"] label {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 8px;
        padding: 0.5rem 0.85rem;
        margin-bottom: 0.4rem;
        transition: border-color 0.15s ease, background 0.15s ease;
    }
    .stRadio [role="radiogroup"] label:hover {
        border-color: var(--amber);
        background: rgba(255, 176, 0, 0.06);
    }

    /* expander — transparent card too */
    [data-testid="stExpander"] {
        background: var(--glass-bg) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
    }

    /* empty state */
    .empty-state {
        opacity: 0.6;
        text-align: center;
        padding: 3rem 1rem;
        border: 1px dashed var(--glass-border);
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# 4. Scoreboard header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="scoreboard-header">
        <div class="sb-eyebrow">RAG-GROUNDED &middot; POWERED BY GEMINI</div>
        <h1 class="sb-title">Sports Quiz <span class="sb-amber">Live</span></h1>
        <div class="sb-sub">Every question is sourced from verified facts — no invented stats.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# 5. Sidebar — match setup
# ---------------------------------------------------------------------------
st.sidebar.markdown('<div class="panel-label">MATCH SETUP</div>', unsafe_allow_html=True)

sport_choice = st.sidebar.selectbox(
    "Sport",
    list(SPORT_ICONS.keys()),
    format_func=lambda s: f"{SPORT_ICONS[s]}  {s}",
)
difficulty = st.sidebar.select_slider("Difficulty", options=["Easy", "Medium", "Hard"])

# ---------------------------------------------------------------------------
# 6. Session state
# ---------------------------------------------------------------------------
if "quiz_output" not in st.session_state:
    st.session_state.quiz_output = None
    st.session_state.quiz_context = None
    st.session_state.parsed_questions = []
    st.session_state.revealed = {}

generate_clicked = st.sidebar.button("⚡ GENERATE QUIZ", use_container_width=True)

if generate_clicked:
    with st.spinner("Pulling facts from the archive & the live wire..."):
        try:
            quiz_text, context_used = compile_quiz_data(sport_choice, difficulty)
            st.session_state.quiz_output = quiz_text
            st.session_state.quiz_context = context_used
            st.session_state.parsed_questions = parse_quiz_text(quiz_text)
            st.session_state.revealed = {}
        except Exception as e:
            st.error(f"Failed to generate quiz: {e}")


# ---------------------------------------------------------------------------
# 7. Live ticker — signature element, built from the RAG context actually used
# ---------------------------------------------------------------------------
def build_ticker_text(context: str, sport: str) -> str:
    headlines = re.findall(r"Web Source \d+: (.+)", context)
    facts_block = re.findall(r"=== HISTORICAL FACTS ===\n(.*?)\n\n=== LIVE INTERNET NEWS ===", context, re.DOTALL)
    bits = []
    if facts_block:
        bits.extend([line.strip() for line in facts_block[0].split("\n") if line.strip()])
    bits.extend(headlines)
    if not bits:
        bits = [f"Loading grounded facts for {sport}..."]
    return "     •     ".join(bits[:6])


if st.session_state.quiz_context:
    ticker_text = build_ticker_text(st.session_state.quiz_context, sport_choice)
    st.markdown(
        f"""
        <div class="ticker-wrap">
            <span class="live-badge"><span class="live-dot"></span> LIVE</span>
            <div class="ticker-track">
                <div class="ticker-content">{ticker_text}&nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp;{ticker_text}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# 8. Quiz display
# ---------------------------------------------------------------------------
if st.session_state.quiz_output:
    st.markdown(
        f'<div class="round-title">{SPORT_ICONS.get(sport_choice, "🏆")} {sport_choice} — {difficulty} Round</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.parsed_questions:
        for i, q in enumerate(st.session_state.parsed_questions):
            with st.container(border=True):
                st.markdown(f'<div class="q-tag">Q{i + 1}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="q-text">{q["question"]}</div>', unsafe_allow_html=True)

                choice = st.radio(
                    f"Options for question {i + 1}",
                    options=list(q["options"].keys()),
                    format_func=lambda k, opts=q["options"]: f"{k})  {opts[k]}",
                    key=f"choice_{i}",
                    index=None,
                    label_visibility="collapsed",
                )

                if st.button("Reveal Answer", key=f"reveal_{i}"):
                    st.session_state.revealed[i] = True

                if st.session_state.revealed.get(i):
                    if choice == q["correct"]:
                        st.success(f"✅ Correct — {q['correct']}) {q['options'][q['correct']]}")
                    else:
                        st.error(f"❌ Correct answer: {q['correct']}) {q['options'][q['correct']]}")
                    st.markdown(f'<div class="explain-box">📖 {q["explanation"]}</div>', unsafe_allow_html=True)
    else:
        st.warning("Couldn't parse structured questions — showing raw output instead.")
        st.text_area(
            "Raw quiz output",
            value=st.session_state.quiz_output,
            height=350,
            label_visibility="collapsed",
        )

    with st.expander("📼 Full Broadcast Replay — inspect the RAG context used"):
        st.code(st.session_state.quiz_context, language="markdown")
else:
    st.markdown(
        '<div class="empty-state">Pick a sport and difficulty on the left, then hit '
        '<b>⚡ GENERATE QUIZ</b> to kick off the round.</div>',
        unsafe_allow_html=True,
    )