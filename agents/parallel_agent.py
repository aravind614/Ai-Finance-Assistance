from langchain_core.runnables import RunnableParallel, RunnableLambda
from agents.research_agent import research_company_fundamentals
from agents.news_agent import get_news
from services.llm import get_llm


def compare_companies(companies: list[str]) -> str:
    """
    Research multiple companies in parallel using RunnableParallel,
    then generate a structured comparison.
    """
    if not companies:
        return "No companies provided for comparison."

    # Build a parallel runnable for each company
    parallel_tasks = {
        company: RunnableLambda(lambda _c=company: research_company_fundamentals(_c))
        for company in companies
    }

    parallel_runnable = RunnableParallel(**parallel_tasks)
    results = parallel_runnable.invoke({})

    # Build combined context for LLM
    combined = ""
    for company, research in results.items():
        combined += f"\n\n=== {company} ===\n{research}"

    # Also fetch latest news for each company
    news_summaries = ""
    for company in companies:
        try:
            news = get_news(f"{company} stock earnings")
            news_summaries += f"\n\n--- {company} Latest News ---\n{news}"
        except Exception:
            news_summaries += f"\n\n--- {company} Latest News ---\nUnavailable"

    prompt = f"""
You are a Senior Financial Analyst.

You have been asked to compare the following companies: {', '.join(companies)}.

COMPANY RESEARCH:
{combined}

LATEST NEWS:
{news_summaries}

Generate a comprehensive comparison report including:
1. A Comparison Table with columns: Company | Industry | Business Model | Key Strengths | Key Weaknesses | Growth Outlook
2. A detailed narrative comparison covering financial performance, market position, and competitive dynamics.
3. A final Investment Ranking from most to least attractive, with brief justification for each.

Make the output clear, professional, and structured in Markdown format.
"""

    llm = get_llm()
    response = llm.invoke(prompt)
    return response.content
