from services.llm import get_llm
from tools.web_search import web_search

def get_news(query: str) -> str:
    """
    Search for latest financial news and return a summary.
    """
    results = web_search(f"{query} latest news financial market", max_results=6)
    if not results:
        return "No recent news found for this query."
        
    context = ""
    for idx, r in enumerate(results, 1):
        context += f"Source {idx}: {r.get('title')}\nURL: {r.get('url')}\nSnippet: {r.get('snippet')}\n\n"
        
    prompt = f"""
You are a Financial News Analyst agent.
Analyze the following latest news search results for query: "{query}"

NEWS DATA:
{context}

Tasks:
1. Summarize the key news events, stock movements, announcements, or trends.
2. Group the information logically.
3. List the URLs of the sources used so the user can read more.
4. Keep the summary objective and professional.
"""
    llm = get_llm()
    response = llm.invoke(prompt)
    return response.content
