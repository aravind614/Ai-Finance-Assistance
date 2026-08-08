from ddgs import DDGS


def web_search(
    query: str,
    max_results: int = 5,
    domain: str | None = None,
) -> list[dict]:
    """
    Search the web and return structured search results.
    """

    search_query = query

    if domain:
        search_query = f"site:{domain} {query}"

    results = DDGS().text(
        search_query,
        max_results=max_results,
    )

    return [
        {
            "title": result.get("title", ""),
            "url": result.get("href", ""),
            "snippet": result.get("body", ""),
        }
        for result in results
    ]
