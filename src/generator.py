import re
from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY
from src.database import query_historic_facts
from src.search import get_live_news_context


def compile_quiz_data(sport, difficulty):
    """
    1. Gathers context from ChromaDB (Historical).
    2. Gathers context from DuckDuckGo (Live news).
    3. Blends them inside a grounded prompt.
    4. Connects to Gemini and generates the structured quiz.

    Returns a tuple: (raw_quiz_text, unified_context_used)
    """
    # Create query to run against ChromaDB
    db_query = f"{sport} history cup championships rules records"
    db_matches = query_historic_facts(sport=sport, query_text=db_query, n_results=2)
    db_context = "\n".join(db_matches) if db_matches else "No offline historic data recorded."

    # Search the live web
    web_context = get_live_news_context(sport)

    # Combine historical and web contexts
    unified_context = f"=== HISTORICAL FACTS ===\n{db_context}\n\n=== LIVE INTERNET NEWS ===\n{web_context}"

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to your .env file before generating a quiz."
        )

    # Instantiate the API client
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Constructing a structured system prompt
    system_instruction = (
        "You are an expert sports quiz creator. Your job is to write multiple-choice quizzes "
        "relying strictly on the provided Context. Avoid hallucinations. Do not use facts not "
        "found in the Context below. If facts are scarce, make do with what you have, "
        "but keep details completely accurate to the text context.\n\n"
        f"CONTEXT DETAILS:\n{unified_context}"
    )

    user_prompt = (
        f"Generate exactly 4 unique multiple-choice questions for the sport: {sport}.\n"
        f"Difficulty target: {difficulty}.\n\n"
        "Format each question EXACTLY as follows so my program can parse it "
        "(no extra commentary, no numbering, no markdown bold):\n"
        "Question: [Question text here]\n"
        "A) [Option A]\n"
        "B) [Option B]\n"
        "C) [Option C]\n"
        "D) [Option D]\n"
        "Correct Answer: [Single Letter, e.g., A]\n"
        "Explanation: [Detailed background reasoning quoting from the context details]\n"
        "---"
    )

    # Make API call
    response = client.models.generate_content(
        model="gemini-flash-latest",  # fast + cheap; swap for "gemini-2.5-pro" if you want higher quality
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
        )
    )

    return response.text, unified_context


def parse_quiz_text(raw_text):
    """
    Parses the LLM's structured text output into a list of question dicts:
    [{ "question": str, "options": {"A": str, ...}, "correct": "A", "explanation": str }, ...]

    Falls back to an empty list if the format doesn't match, so the UI can
    show the raw text instead of crashing (see Troubleshooting: Parsing Failures).
    """
    questions = []
    blocks = raw_text.split("---")

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        q_match = re.search(r"Question:\s*(.+)", block)
        a_match = re.search(r"A\)\s*(.+)", block)
        b_match = re.search(r"B\)\s*(.+)", block)
        c_match = re.search(r"C\)\s*(.+)", block)
        d_match = re.search(r"D\)\s*(.+)", block)
        correct_match = re.search(r"Correct Answer:\s*([ABCD])", block, re.IGNORECASE)
        explanation_match = re.search(r"Explanation:\s*(.+)", block, re.DOTALL)

        if not (q_match and a_match and b_match and c_match and d_match and correct_match):
            continue  # skip malformed blocks rather than crashing the whole quiz

        questions.append({
            "question": q_match.group(1).strip(),
            "options": {
                "A": a_match.group(1).strip(),
                "B": b_match.group(1).strip(),
                "C": c_match.group(1).strip(),
                "D": d_match.group(1).strip(),
            },
            "correct": correct_match.group(1).strip().upper(),
            "explanation": explanation_match.group(1).strip() if explanation_match else "No explanation provided.",
        })

    return questions