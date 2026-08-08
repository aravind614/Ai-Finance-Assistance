# 📈 AI Investment & Financial Research Assistant
*AlphaVest Capital Capstone Project*

An end-to-end multi-agent AI research assistant built with **LangChain**, **Groq**, **ChromaDB**, and **Streamlit** to automate financial research, earnings report summaries, RAG document analysis, multi-company comparisons, investor preference memory, and email dispatch.

---

## 🏗️ System Architecture

```
Investor → Streamlit UI (app.py)
            ↓
    Financial Research Coordinator (agents/coordinator.py)
            ↓
  ┌─────────┼──────────────┬──────────────┬──────────────┐
  │         │              │              │              │
News Agent  PDF RAG Agent  Research Agent  Parallel Agent Email Agent
  │         │              │              │              │
  └─────────┴──────────────┼──────────────┴──────────────┘
                           ↓
                Financial Memory Layer
                     (SQLite + ChromaDB)
```

---

## ✨ Features & Module Mapping

| Module | Feature | Implementation |
|---|---|---|
| **Module 1** | AI Financial Assistant | Conversational interface in Streamlit (`app.py`) |
| **Module 2** | Financial News Agent | Real-time financial news search via DuckDuckGo (`agents/news_agent.py`) |
| **Module 3** | Company Research Agent | Fundamentals, Business Overview, Products, Competitors, and Announcements via Wikipedia & Web Search (`agents/research_agent.py`) |
| **Module 4** | Annual Report Analysis (RAG) | Upload PDF Annual/Quarterly Reports into ChromaDB Vector Store (`services/rag_service.py`) |
| **Module 5** | Multi-Company Comparison | Parallel research execution using `RunnableParallel` (`agents/parallel_agent.py`) |
| **Module 6** | Investment Report Generator | Structured Pydantic output (`InvestmentReport` schema) (`agents/report_agent.py`) |
| **Module 7** | Sequential Workflow | Pipeline: Research → PDF Context → Merge → Analyze → Report (`agents/coordinator.py`) |
| **Module 8** | Conditional Routing | Dynamic route classification (`RouteDecision`) (`agents/coordinator.py`) |
| **Module 9** | Memory Layer | Short-term history & long-term investor profiles stored in SQLite (`services/db.py`) |
| **Module 10** | Python Financial Calculation Tool | Growth, CAGR, ROI, and comparison table generator (`tools/python_tool.py`) |
| **Module 11** | Email Integration | Email dispatch via SMTP (`agents/email_agent.py`) |
| **Module 12** | Streamlit Dashboard | Full-featured UI with PDF uploads, knowledge base controls, quick prompts, and report text downloads (`app.py`) |

---

## 🚀 Quick Start & Installation

### 1. Install Dependencies
```bash
uv pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY="your_groq_api_key"
OPENROUTER_API_KEY="your_openrouter_key" # Optional
SENDER_EMAIL="your_email@gmail.com"       # Optional for Email Agent
SENDER_PASSWORD="your_app_password"      # Optional for Email Agent
```

### 3. Run the Streamlit Application
```bash
uv run streamlit run app.py
```

---

## 📁 Repository Structure

```
├── README.md
├── requirements.txt
├── app.py                      # Main Streamlit Dashboard Application
├── models/
│   └── schemas.py              # Pydantic schemas (InvestmentReport, InvestorProfile, etc.)
├── services/
│   ├── db.py                   # SQLite chat memory & investor profile service
│   ├── rag_service.py          # ChromaDB vector store ingestion & retriever
│   ├── llm.py                  # Groq LLM setup
│   └── financial_calculations.py
├── tools/
│   ├── python_tool.py          # Financial calculation executor (CAGR, ROI, tables)
│   ├── web_search.py           # DuckDuckGo search tool
│   └── web_fetch.py           # Web page & PDF scraper
└── agents/
    ├── coordinator.py          # Central Coordinator router
    ├── news_agent.py           # Financial News Agent
    ├── research_agent.py       # Fundamental Research Agent
    ├── parallel_agent.py       # Multi-Company RunnableParallel Agent
    ├── report_agent.py         # Investment Report Generator
    └── email_agent.py          # Gmail / SMTP Dispatch Agent
```
