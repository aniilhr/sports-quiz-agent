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
# 3. Theme — scoreboard / broadcast aesthetic
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

    :root {
        --charcoal: #14181C;
        --charcoal-2: #1B2126;
        --slate: #232B31;
        --chalk: #EDEDE6;
        --chalk-dim: #9BA3A9;
        --amber: #FFB000;
        --amber-dim: rgba(255,176,0,0.16);
        --turf: #2FBE72;
        --foul: #FF5A4E;
        --hairline: rgba(237,237,230,0.10);
    }

    html, body, .stApp {
        background: var(--charcoal) !important;
        font-family: 'IBM Plex Sans', sans-serif;
    }
    .stApp, .stApp p, .stApp li, .stApp label, .stApp span, .stMarkdown {
        color: var(--chalk);
    }
    #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {
        background: var(--charcoal-2);
        border-right: 1px solid var(--hairline);
    }
    [data-testid="stSidebar"] * { color: var(--chalk) !important; }

    .panel-label {
        font-family: 'Oswald', sans-serif;
        font-weight: 600;
        letter-spacing: 0.12em;
        font-size: 0.8rem;
        color: var(--amber) !important;
        border-bottom: 2px solid var(--amber);
        padding-bottom: 6px;
        margin: 0.4rem 0 1.2rem 0;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: var(--slate) !important;
        border: 1px solid var(--hairline) !important;
        border-radius: 6px !important;
    }

    /* ---------- Buttons ---------- */
    .stButton > button {
        background: var(--amber);
        color: var(--charcoal) !important;
        font-family: 'Oswald', sans-serif;
        font-weight: 600;
        letter-spacing: 0.04em;
        border: none;
        border-radius: 6px;
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

    /* ---------- Scoreboard header ---------- */
    .scoreboard-header {
        background: linear-gradient(160deg, var(--charcoal-2), var(--charcoal));
        border: 1px solid var(--hairline);
        border-radius: 10px;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.2rem;
    }
    .sb-eyebrow {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.14em;
        color: var(--chalk-dim) !important;
        margin-bottom: 0.4rem;
    }
    .sb-title {
        font-family: 'Oswald', sans-serif;
        font-weight: 700;
        font-size: 2.3rem;
        letter-spacing: 0.02em;
        margin: 0;
        color: var(--chalk) !important;
        text-transform: uppercase;
    }
    .sb-amber { color: var(--amber) !important; text-shadow: 0 0 18px var(--amber-dim); }
    .sb-sub {
        color: var(--chalk-dim) !important;
        margin-top: 0.5rem;
        font-size: 0.95rem;
    }

    /* ---------- Live ticker (signature element) ---------- */
    .ticker-wrap {
        display: flex;
        align-items: center;
        background: #0F1215;
        border: 1px solid var(--hairline);
        border-radius: 6px;
        overflow: hidden;
        margin: 0.4rem 0 1.4rem 0;
        height: 38px;
    }
    .live-badge {
        flex-shrink: 0;
        font-family: 'Oswald', sans-serif;
        font-weight: 600;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        color: var(--foul) !important;
        padding: 0 0.8rem;
        border-right: 1px solid var(--hairline);
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
        color: var(--amber) !important;
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
        color: var(--chalk) !important;
        border-left: 4px solid var(--amber);
        padding-left: 0.7rem;
        margin: 0.6rem 0 1rem 0;
        text-transform: uppercase;
    }

    /* ---------- Quiz cards ---------- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--slate) !important;
        border: 1px solid var(--hairline) !important;
        border-radius: 10px !important;
        padding: 0.5rem 0.3rem !important;
        margin-bottom: 1rem !important;
    }
    .q-tag {
        display: inline-block;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        color: var(--charcoal);
        background: var(--amber);
        border-radius: 4px;
        padding: 2px 8px;
        margin-bottom: 0.5rem;
        letter-spacing: 0.05em;
    }
    .q-text {
        font-weight: 500;
        font-size: 1.02rem;
        color: var(--chalk) !important;
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }
    .explain-box {
        font-size: 0.9rem;
        color: var(--chalk-dim) !important;
        background: var(--charcoal-2);
        border-left: 3px solid var(--amber);
        border-radius: 4px;
        padding: 0.6rem 0.8rem;
        margin-top: 0.5rem;
    }

    /* radio options styled like roster rows */
    .stRadio [role="radiogroup"] label {
        background: var(--charcoal-2);
        border: 1px solid var(--hairline);
        border-radius: 6px;
        padding: 0.45rem 0.8rem;
        margin-bottom: 0.4rem;
        transition: border-color 0.15s ease;
    }
    .stRadio [role="radiogroup"] label:hover { border-color: var(--amber); }

    /* expander */
    [data-testid="stExpander"] {
        background: var(--charcoal-2);
        border: 1px solid var(--hairline);
        border-radius: 8px;
    }

    /* empty state */
    .empty-state {
        color: var(--chalk-dim) !important;
        text-align: center;
        padding: 3rem 1rem;
        border: 1px dashed var(--hairline);
        border-radius: 10px;
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