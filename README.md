# 🏆 AI-Powered Sports Quiz Generator (RAG Agent)

A Streamlit web app that generates factually grounded, multiple-choice sports
quizzes using **Retrieval-Augmented Generation (RAG)**: it pulls historic
facts from a local **ChromaDB** vector store and live news from **DuckDuckGo
web search**, then asks an LLM to write quiz questions using *only* that
retrieved context — reducing hallucinations.

## How it works

```
User picks Sport + Difficulty
        │
        ▼
 ChromaDB (local facts) + DuckDuckGo (live web) ──► combined context
        │
        ▼
 LLM writes 4 MCQs strictly from that context
        │
        ▼
 Streamlit displays each question as a card with click-to-reveal feedback
```

## Project structure

```
sports-quiz-agent/
├── .env.example        # Template for your API key — copy to .env
├── requirements.txt
├── README.md
├── data/
│   └── sports_facts.json
├── chroma_db/           # auto-created on first run (vector store)
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── search.py
│   └── generator.py
└── app.py
```

## Setup

1. **Create and activate a virtual environment** (Python 3.9–3.11 recommended):

   ```bash
   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Add your API key:**

   ```bash
   cp .env.example .env
   ```

   Then open `.env` and paste your real OpenAI key:

   ```
   OPENAI_API_KEY=sk-proj-...
   ```

   Get a key at https://platform.openai.com/api-keys — never commit this file
   (it's already in `.gitignore`).

4. **Run the app:**

   ```bash
   streamlit run app.py
   ```

   Your browser should open automatically at `http://localhost:8501`.

## Usage

1. Pick a **Sport** and **Difficulty** in the sidebar.
2. Click **Generate Fresh Quiz**.
3. Answer each question, then click **Reveal Answer** for instant feedback
   and a source-grounded explanation.
4. Expand **🔍 Inspect Ground Truth** to see exactly which facts (local +
   web) the quiz was built from.

## Customizing the knowledge base

Add more entries to `data/sports_facts.json` (same `{"sport": ..., "fact": ...}`
shape) and delete the `chroma_db/` folder so it re-populates on next run.
Add new sports there **and** to the `selectbox` options list in `app.py`.

## Troubleshooting

- **ChromaDB sqlite error** (common on some Linux/Windows setups):
  ```bash
  pip install pysqlite3-binary
  ```
  `src/database.py` will automatically detect and use it — no code changes needed.

- **`duckduckgo_search` import error:** the package was renamed to `ddgs`
  upstream. `src/search.py` already falls back automatically, but if pip
  can't find `duckduckgo-search` at all, run `pip install ddgs` instead.

- **Quiz shows raw text instead of interactive cards:** this means the LLM's
  output didn't match the expected `Question:/A)/B).../Correct Answer:` format.
  Try regenerating, or switch the model in `src/generator.py` to one with
  JSON mode (`response_format={"type": "json_object"}`) for stricter output.

- **"API Key is missing" warning:** double-check `.env` exists (not just
  `.env.example`) and contains `OPENAI_API_KEY=...` with no quotes.
