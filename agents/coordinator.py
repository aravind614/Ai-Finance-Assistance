import re
from langchain_core.runnables import RunnableBranch, RunnableLambda
from services.llm import get_llm, extract_text_content
from models.schemas import RouteDecision
from agents.news_agent import get_news
from agents.research_agent import research_company_fundamentals, research_company
from agents.parallel_agent import compare_companies
from agents.report_agent import generate_investment_report, format_report_as_markdown
from agents.email_agent import send_email_report
from services.rag_service import query_documents, get_uploaded_documents
from tools.python_tool import run_calculation_code, calculate_cagr, calculate_growth, calculate_roi
from services.db import get_investor_profile, update_investor_profile


def classify_intent(query: str) -> str:
    """
    Classify user query into an execution route.
    """
    uploaded_docs = get_uploaded_documents()
    has_docs = len(uploaded_docs) > 0

    llm = get_llm()
    structured_llm = llm.with_structured_output(RouteDecision)

    prompt = f"""
You are the central coordinator for an AI Investment & Financial Research Assistant.
Uploaded Reports in System: {uploaded_docs if has_docs else "None"}

Analyze the user query and choose the single best execution route:

- 'pdf_rag': Questions about financial metrics (revenue, net income, growth, segments, risks, profit, balance sheet) or uploaded annual/quarterly reports/PDFs. (Select this if reports are uploaded or user asks about report facts).
- 'news': Searching for current news, market news, stock updates (e.g., "Google stock news", "NVIDIA Earnings", "AI industry news").
- 'compare': Comparing 2 or more companies (e.g., "Compare Microsoft and Google").
- 'report': Requesting a full investment report or comprehensive recommendation (e.g., "Research NVIDIA and generate an investment report").
- 'email': Requests to email a report to client (e.g., "Email today's investment report to client@example.com").
- 'calculate': Pure math calculations like CAGR formula execution or standalone math.
- 'memory': Storing or setting investor profile preferences (e.g., "Remember that I prefer low-risk tech investments").
- 'research': General online fundamental research for a company when no uploaded report is available.
- 'general': Conversational Q&A.

Query: "{query}"
"""
    try:
        decision = structured_llm.invoke(prompt)
        if isinstance(decision, RouteDecision):
            return decision.route
        elif isinstance(decision, dict):
            return str(decision.get("route", "pdf_rag" if has_docs else "general"))
        elif hasattr(decision, "route"):
            return str(getattr(decision, "route"))
    except Exception:
        return "pdf_rag" if has_docs else "general"
    return "pdf_rag" if has_docs else "general"


def execute_coordinator(query: str, session_id: str = "default") -> dict:
    """
    Main entry point for routing and executing user requests.
    Returns a dictionary with result text, route name, and optional extra metadata.
    """
    profile = get_investor_profile()
    profile_summary = f"Client Name: {profile.name}, Risk Profile: {profile.risk_profile}, Interests: {profile.investment_interests}"

    uploaded_docs = get_uploaded_documents()
    route = classify_intent(query)

    # Smart Override: If uploaded documents exist and query is asking about financial metrics or reports,
    # attempt RAG query first before defaulting to web research
    if len(uploaded_docs) > 0 and route in ["research", "general", "pdf_rag"]:
        rag_chunks = query_documents(query, k=5)
        if rag_chunks:
            context = "\n\n".join([f"Source ({c['metadata'].get('source')}): {c['page_content']}" for c in rag_chunks])
            prompt = f"""
You are an expert Financial Analyst. Answer the user's question accurately based ON THE FOLLOWING UPLOADED FINANCIAL REPORT EXCERPTS.

EXCERPTS FROM UPLOADED REPORT:
{context}

USER QUESTION: {query}

INSTRUCTIONS:
1. Provide a direct, precise, and complete answer using the metrics and facts in the excerpts.
2. If revenue, net income, growth, or segment figures are present, state them clearly.
3. State the name of the source document referenced.
"""
            llm = get_llm()
            result = extract_text_content(llm.invoke(prompt).content)
            return {"route": "PDF RAG Agent (Uploaded Report)", "output": result, "pdf_chunks": rag_chunks}

    # Route-based Execution
    if route == "pdf_rag":
        chunks = query_documents(query, k=5)
        if not chunks:
            result = f"No matching information found in the uploaded financial reports ({', '.join(uploaded_docs) if uploaded_docs else 'None uploaded'}). Please upload annual/quarterly reports in the sidebar."
            return {"route": "PDF RAG Agent", "output": result, "pdf_chunks": []}
        else:
            context = "\n\n".join([f"Source ({c['metadata'].get('source')}): {c['page_content']}" for c in chunks])
            prompt = f"Answer the user's question using ONLY the following uploaded report excerpts:\n\n{context}\n\nQuestion: {query}"
            llm = get_llm()
            result = extract_text_content(llm.invoke(prompt).content)
            return {"route": "PDF RAG Agent", "output": result, "pdf_chunks": chunks}

    elif route == "news":
        result = get_news(query)
        return {"route": "Financial News Agent", "output": result}

    elif route == "compare":
        prompt = f"Extract all company names mentioned in this query as a comma-separated list. Query: '{query}'"
        llm = get_llm()
        raw_companies = extract_text_content(llm.invoke(prompt).content).strip()
        companies = [c.strip() for c in raw_companies.split(",") if c.strip()]
        if not companies:
            companies = ["Google", "Microsoft"]
        result = compare_companies(companies)
        return {"route": "Multi-Company Parallel Research Agent", "output": result}

    elif route == "memory":
        prompt = f"Extract investor profile updates from query: '{query}'."
        llm = get_llm()
        if "low-risk" in query.lower() or "low risk" in query.lower():
            profile.risk_profile = "Low"
            profile.investment_interests = "Low-risk tech investments"
        elif "high-risk" in query.lower() or "high risk" in query.lower():
            profile.risk_profile = "High"
        update_investor_profile(profile)
        return {"route": "Long-Term Memory Layer", "output": f"Updated investor preferences in persistent storage:\n- Risk Profile: {profile.risk_profile}\n- Interests: {profile.investment_interests}"}

    elif route == "email":
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', query)
        recipient = email_match.group(0) if email_match else "aravindpooja2306@gmail.com"

        # Generate or retrieve real financial research report for email body
        report_text = ""
        if len(uploaded_docs) > 0:
            chunks = query_documents("financial results revenue net income growth segment risks", k=6)
            if chunks:
                ctx = "\n\n".join([f"Source ({c['metadata'].get('source')}): {c['page_content']}" for c in chunks])
                llm = get_llm()
                prompt = f"""
You are a Senior Investment Research Analyst.
Generate a comprehensive, formal AI Investment Research Report based on these uploaded financial report excerpts:

{ctx}

FORMAT: Include Executive Summary, Financial Performance (Revenue, Profit, EPS, Margins), Major Segments, Growth Drivers, Risks, and Investment Recommendation.
"""
                report_text = extract_text_content(llm.invoke(prompt).content)

        if not report_text:
            # Fallback to research generator if no uploaded RAG docs exist
            comp_match = re.search(r'\b(Microsoft|Google|Apple|Tesla|NVIDIA|Amazon|Meta)\b', query, re.I)
            target_company = comp_match.group(0) if comp_match else "Microsoft"
            res_text = research_company_fundamentals(target_company)
            news_text = get_news(f"{target_company} stock earnings")
            rep_obj = generate_investment_report(target_company, res_text, news_text, "", profile_summary)
            report_text = format_report_as_markdown(rep_obj)

        report_text = extract_text_content(report_text)

        result_msg = send_email_report(
            recipient_email=recipient,
            subject="AI Investment Research Report",
            report_content=report_text,
            pdf_bytes=report_text.encode('utf-8')
        )
        return {"route": "Email Dispatch Agent", "output": result_msg, "report_content": report_text}

    elif route == "calculate":
        prompt = f"""
Write python code to perform the financial calculation requested in: "{query}"
Available functions:
- calculate_growth(current, previous)
- calculate_cagr(start_value, end_value, periods)
- calculate_roi(gain, cost)
- generate_comparison_table(data_dict)

Format output strictly as clean Python code block starting with ```python and ending with ```.
Print the final result using print().
"""
        llm = get_llm()
        code_resp = extract_text_content(llm.invoke(prompt).content)
        code_match = re.search(r'```python(.*?)```', code_resp, re.DOTALL)
        code = code_match.group(1).strip() if code_match else code_resp
        calc_out = run_calculation_code(code)
        return {"route": "Python Financial Calculation Tool", "output": f"**Calculation Results:**\n```\n{calc_out}\n```", "code": code}

    elif route == "report":
        prompt = f"Extract the target company name from query: '{query}'"
        llm = get_llm()
        company = extract_text_content(llm.invoke(prompt).content).strip() or "NVIDIA"

        res_text = research_company_fundamentals(company)
        news_text = get_news(f"{company} news")
        pdf_chunks = query_documents(f"{company} financial results risk revenue", k=3)
        pdf_ctx = "\n".join([c["page_content"] for c in pdf_chunks])

        rep_obj = generate_investment_report(company, res_text, news_text, pdf_ctx, profile_summary)
        markdown_rep = format_report_as_markdown(rep_obj)
        return {"route": "Sequential Investment Report Pipeline", "output": markdown_rep, "report_obj": rep_obj}

    else:
        prompt_company = f"Extract any single company name from query: '{query}'. If none, respond NONE."
        llm = get_llm()
        comp = extract_text_content(llm.invoke(prompt_company).content).strip()
        if comp and comp != "NONE":
            res = research_company_fundamentals(comp)
            return {"route": "Company Research Agent", "output": res}
        else:
            ans = extract_text_content(llm.invoke(f"You are an AI Financial Research Assistant. Answer professionally:\n\n{query}").content)
            return {"route": "Conversational AI Assistant", "output": ans}

