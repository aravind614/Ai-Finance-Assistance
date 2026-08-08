from urllib.parse import urljoin
import wikipedia

from services.llm import get_llm
from tools.web_search import web_search
from tools.web_fetch import fetch_webpage, fetch_links, fetch_pdf
from services.financial_calculations import calculate_growth
from models.schemas import FinancialResearch


def research_company(company: str, question: str) -> FinancialResearch:
    """
    Research a company's latest financial results using
    official web pages and financial statements.
    """

    # 1. Search for the company's latest financial results
    results = web_search(
        f"{company} latest quarterly financial results",
        max_results=5,
    )

    if not results:
        raise ValueError("No search results found.")

    # 2. Prefer an official company result
    official_result = results[0]

    preferred_keywords = [
        "reports",
        "quarter",
        "results",
        "earnings",
        "financial-results",
    ]

    for result in results:
        title = result.get("title", "").lower()
        url = result.get("url", "").lower()

        score = sum(
            keyword in title or keyword in url
            for keyword in preferred_keywords
        )

        if score >= 2:
            official_result = result
            break

    webpage_url = official_result["url"]

    # 3. Fetch the official financial-results webpage
    webpage_text = fetch_webpage(webpage_url)

    # 4. Find links to financial PDFs
    links = fetch_links(webpage_url)

    pdf_url = None

    for link in links:
        url = link["url"].lower()
        title = link["title"].lower()

        if "pdf" in url and (
            "financial" in title
            or "statement" in title
            or "financial" in url
        ):
            pdf_url = link["url"]
            break

    # 5. Convert relative PDF URL to absolute URL
    if pdf_url and pdf_url.startswith("/"):
        pdf_url = urljoin(webpage_url, pdf_url)

    # 6. Extract PDF text if available
    pdf_text = ""

    if pdf_url:
        try:
            pdf_text = fetch_pdf(pdf_url)
        except Exception:
            pdf_text = ""

    # Limit context to avoid unnecessarily huge prompts
    pdf_context = pdf_text[:30000]

    prompt = f"""
You are a financial research assistant.

Company:
{company}

Research question:
{question}

OFFICIAL WEBPAGE:
{webpage_text[:12000]}

OFFICIAL FINANCIAL STATEMENT:
{pdf_context}

Extract ONLY facts supported by the provided sources.

Return:
- company
- quarter
- revenue
- previous_revenue
- net_income
- previous_net_income
- eps
- previous_eps
- summary
- risks
- sources
"""

    llm = get_llm()
    structured_llm = llm.with_structured_output(FinancialResearch)
    research = structured_llm.invoke(prompt)

    # 7. Calculate growth using Python
    research.revenue_growth = calculate_growth(
        research.revenue,
        research.previous_revenue,
    )

    research.net_income_growth = calculate_growth(
        research.net_income,
        research.previous_net_income,
    )

    # 8. Ensure the official sources are included
    sources = list(research.sources or [])

    if webpage_url not in sources:
        sources.append(webpage_url)

    if pdf_url and pdf_url not in sources:
        sources.append(pdf_url)

    research.sources = sources

    return research


def research_company_fundamentals(company: str) -> str:
    """
    Perform company-level research combining Wikipedia and internet search.
    Covers Business Overview, Products, Competitors, Revenue Sources, and Recent Announcements.
    """
    wiki_summary = ""
    try:
        wiki_summary = wikipedia.summary(company, sentences=5)
    except Exception:
        try:
            search_results = wikipedia.search(company)
            if search_results:
                wiki_summary = wikipedia.summary(search_results[0], sentences=5)
        except Exception:
            wiki_summary = "No Wikipedia overview found."

    search_res = web_search(f"{company} business model competitors revenue sources announcements", max_results=5)
    search_context = ""
    for r in search_res:
        search_context += f"- {r.get('title')}: {r.get('snippet')} ({r.get('url')})\n"

    prompt = f"""
You are a Company Research Agent.
Perform detailed fundamental research on: "{company}"

WIKIPEDIA OVERVIEW:
{wiki_summary}

WEB SEARCH FINDINGS:
{search_context}

Provide a comprehensive, professional research summary covering these specific sections:
1. Business Overview: A description of what the company does.
2. Products: Primary products or services offered.
3. Competitors: Key industry competitors.
4. Revenue Sources: How the company makes money.
5. Recent Announcements: Any major recent corporate news, earnings releases, or events.
"""
    llm = get_llm()
    response = llm.invoke(prompt)
    return response.content
