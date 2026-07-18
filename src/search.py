# The duckduckgo-search package was renamed to "ddgs" in newer releases.
# This import tries the classic name first and falls back automatically,
# so the app keeps working regardless of which version got installed.
try:
    from duckduckgo_search import DDGS
except ImportError:
    from ddgs import DDGS


def get_live_news_context(sport_name):
    """
    Searches the live web for recent sport news, matches, or events.
    Returns a unified text summary of search snippets.
    """
    search_query = f"{sport_name} latest tournament results championship winners news 2026"
    retrieved_texts = []

    print(f"Executing web search for: '{search_query}'...")
    try:
        # Initializing DuckDuckGo search context
        with DDGS() as ddgs:
            # We fetch the top 5 text search results
            results = ddgs.text(search_query, max_results=5)

            for index, r in enumerate(results, start=1):
                title = r.get("title", "No Title")
                snippet = r.get("body", "No Snippet Content Available")
                retrieved_texts.append(f"Web Source {index}: {title}\nSnippet: {snippet}")

    except Exception as e:
        print(f"Web Search fell back or failed: {e}")
        return "No recent search engine updates available due to system connectivity."

    if not retrieved_texts:
        return "No recent search engine updates were found for this query."

    return "\n\n".join(retrieved_texts)