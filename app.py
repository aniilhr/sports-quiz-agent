import streamlit as st
from src.generator import compile_quiz_data, parse_quiz_text
from src.database import setup_and_populate_db


# 1. Warm-up and initialize the vector DB with our offline facts on startup
@st.cache_resource
def prepare_knowledge_base():
    setup_and_populate_db()


prepare_knowledge_base()

# 2. Set page configuration
st.set_page_config(page_title="Sports Quiz Agent", page_icon="🏆", layout="centered")

st.title("🏆 AI-Powered Sports Quiz Generator")
st.write(
    "Challenge yourself or generate engaging social media content! "
    "Powered by RAG (ChromaDB local facts + live web search)."
)

# 3. Sidebar inputs
st.sidebar.header("Quiz Settings")
sport_choice = st.sidebar.selectbox("Select Sport", ["Cricket", "Football", "Badminton"])
difficulty = st.sidebar.select_slider("Select Difficulty", options=["Easy", "Medium", "Hard"])

# 4. Initialize session state so the quiz + answers survive reruns
if "quiz_output" not in st.session_state:
    st.session_state.quiz_output = None
    st.session_state.quiz_context = None
    st.session_state.parsed_questions = []
    st.session_state.revealed = {}

# Button to trigger the generation pipeline
if st.sidebar.button("Generate Fresh Quiz", use_container_width=True):
    with st.spinner("Fetching historical facts & scouring the live web..."):
        try:
            quiz_text, context_used = compile_quiz_data(sport_choice, difficulty)
            st.session_state.quiz_output = quiz_text
            st.session_state.quiz_context = context_used
            st.session_state.parsed_questions = parse_quiz_text(quiz_text)
            st.session_state.revealed = {}
            st.success("Quiz created successfully!")
        except Exception as e:
            st.error(f"Failed to generate quiz: {e}")

# 5. Display the generated quiz
if st.session_state.quiz_output:
    st.subheader(f"Current Quiz: {sport_choice} ({difficulty})")

    if st.session_state.parsed_questions:
        # Nicely parsed interactive cards with click-to-reveal feedback
        for i, q in enumerate(st.session_state.parsed_questions):
            with st.container(border=True):
                st.markdown(f"**Q{i + 1}. {q['question']}**")

                choice = st.radio(
                    "Choose an answer:",
                    options=list(q["options"].keys()),
                    format_func=lambda k, opts=q["options"]: f"{k}) {opts[k]}",
                    key=f"choice_{i}",
                    index=None,
                )

                if st.button("Reveal Answer", key=f"reveal_{i}"):
                    st.session_state.revealed[i] = True

                if st.session_state.revealed.get(i):
                    if choice == q["correct"]:
                        st.success(f"✅ Correct! The answer is {q['correct']}) {q['options'][q['correct']]}")
                    else:
                        st.error(f"❌ The correct answer is {q['correct']}) {q['options'][q['correct']]}")
                    st.info(f"**Why:** {q['explanation']}")
    else:
        # Fallback if the LLM output didn't match the expected format
        st.warning("Couldn't parse structured questions — showing raw output instead.")
        st.text_area(
            "Generated Quiz Output (Copy paste to your socials)",
            value=st.session_state.quiz_output,
            height=350
        )

    # Expandable window showcasing the "ground truth context" for audit purposes
    with st.expander("🔍 Inspect Ground Truth (RAG Context Used)"):
        st.code(st.session_state.quiz_context, language="markdown")
