# 🏆 Sports Quiz — Live

A RAG-grounded sports quiz generator. It pulls historic facts from a local
**ChromaDB** vector store and live news from **DuckDuckGo web search**, then
asks **Gemini** to write multiple-choice questions using *only* that
retrieved context — reducing hallucinated stats. Wrapped in a
scoreboard-themed Streamlit UI.

**Live demo:** https://sports-quiz-agent-anilhr.streamlit.app/
**Source:** https://github.com/aniilhr/sports-quiz-agent

## How it works
User picks Sport + Difficulty
│
▼
ChromaDB (local facts) + DuckDuckGo (live web) ──► combined context
│
▼
Gemini writes 4 MCQs strictly from that context
│
▼
Streamlit shows each question as a card, with click-to-reveal feedback
and a live "broadcast ticker" of the facts actually used

## Project structure
sports-quiz-agent/
├── .env.example        # template for your API key — copy to .env
├── requirements.txt
├── README.md
├── data/
│   └── sports_facts.json
├── chroma_db/           # auto-created on first run (vector store)
├── src/
│   ├── init.py
│   ├── config.py
│   ├── database.py
│   ├── search.py
│   └── generator.py
└── app.py

## Local setup

1. **Python 3.11 is required** (not 3.12+) — `chromadb` and
   `sentence-transformers` depend on packages that don't yet ship prebuilt
   wheels for newer Python versions.

```bash
   py -0                 # check installed versions on Windows
```

   If 3.11 isn't listed, install it from
   https://www.python.org/downloads/release/python-3119/

2. **Create and activate a virtual environment:**

```bash
   # Windows
   py -3.11 -m venv venv
   venv\Scripts\activate

   # macOS / Linux
   python3.11 -m venv venv
   source venv/bin/activate
```

3. **Install dependencies:**

```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
```

4. **Add your Gemini API key:**

```bash
   copy .env.example .env      # Windows
   cp .env.example .env        # macOS / Linux
```

   Open `.env` and paste your real key (get one free at
   https://aistudio.google.com/apikey):
GEMINI_API_KEY=AIza...

5. **Run it:**

```bash
   streamlit run app.py
```

## Deploying to Streamlit Community Cloud

1. Push the repo to GitHub (make sure `.env`, `venv/`, and `chroma_db/` stay
   out of git — they're already in `.gitignore`).
2. Go to **share.streamlit.io** → **New app** → pick the repo, branch
   `main`, main file path `app.py`.
3. Under **Advanced settings**:
   - Python version: **3.11**
   - Secrets:
```toml
     GEMINI_API_KEY = "your-actual-key-here"
```
4. Click **Deploy**.

## Customizing the knowledge base

Add more entries to `data/sports_facts.json` (same
`{"sport": ..., "fact": ...}` shape), then delete the local `chroma_db/`
folder so it re-populates on next run. Add new sports there **and** to the
`SPORT_ICONS` dict at the top of `app.py`.

## Troubleshooting

- **ChromaDB sqlite error:**
```bash
  pip install pysqlite3-binary
```
  `src/database.py` auto-detects and uses it — no code changes needed.

- **`duckduckgo_search` import error:** the package was renamed to `ddgs`
  upstream. `src/search.py` falls back automatically; if pip can't find
  `duckduckgo-search` at all, run `pip install ddgs` instead.

- **`ModuleNotFoundError: No module named '_cffi_backend'`** (seen on some
  Windows installs): the `cryptography`/`cffi` install got corrupted.
```bash
  pip uninstall -y cryptography cffi
  pip install --upgrade --force-reinstall cffi
  pip install --upgrade --force-reinstall cryptography
```

- **"Invalid format: please enter valid TOML"** when pasting Streamlit
  Cloud secrets: make sure the value is in quotes, e.g.
  `GEMINI_API_KEY = "your-key"` — not `GEMINI_API_KEY=your-key`.

- **Quiz shows raw text instead of interactive cards:** the model's output
  didn't match the expected `Question:/A)/B).../Correct Answer:` format.
  Regenerate, or switch to a model/config with stricter structured output.

- **"GEMINI_API_KEY is missing" error:** confirm `.env` exists locally (not
  just `.env.example`), or that the Cloud secret is saved correctly.
