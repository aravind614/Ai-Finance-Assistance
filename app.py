import streamlit as st
import io

from agents.coordinator import execute_coordinator
from services.llm import extract_text_content
from services.rag_service import (
    extract_pdf_text_from_bytes,
    ingest_document,
    get_uploaded_documents,
    clear_knowledge_base
)

from services.db import (
    save_chat_message,
    get_chat_history,
    clear_chat_history,
    get_investor_profile,
    update_investor_profile,
    get_all_sessions
)

st.set_page_config(
    page_title="AlphaVest AI - Financial Research Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .stChatMessage {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "session_id" not in st.session_state:
    st.session_state.session_id = "default_session"

if "messages" not in st.session_state:
    st.session_state.messages = get_chat_history(st.session_state.session_id)

# ================= SIDEBAR =================
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/combo-chart.png", width=60)
    st.title("AlphaVest Capital")
    st.markdown("**AI Investment & Financial Research**")
    st.divider()

    # 1. Investor Profile (Long-Term Memory)
    with st.expander("👤 Investor Profile (Long-Term Memory)", expanded=False):
        profile = get_investor_profile()
        new_name = st.text_input("Client Name", value=profile.name)
        new_interests = st.text_input("Investment Interests", value=profile.investment_interests)
        new_risk = st.selectbox("Risk Profile", ["Low", "Moderate", "High"], index=["Low", "Moderate", "High"].index(profile.risk_profile) if profile.risk_profile in ["Low", "Moderate", "High"] else 1)

        if st.button("Save Profile"):
            profile.name = new_name
            profile.investment_interests = new_interests
            profile.risk_profile = new_risk
            update_investor_profile(profile)
            st.success("Profile saved!")

    st.divider()

    # 2. PDF Report File Uploaders
    st.subheader("📁 Report Uploads")
    annual_reports = st.file_uploader(
        "Upload Annual Reports (.pdf)",
        type=["pdf"],
        accept_multiple_files=True,
        key="annual"
    )
    quarterly_reports = st.file_uploader(
        "Upload Quarterly Reports (.pdf)",
        type=["pdf"],
        accept_multiple_files=True,
        key="quarterly"
    )

    if st.button("Build Knowledge Base", type="primary"):
        all_files = (annual_reports or []) + (quarterly_reports or [])
        if all_files:
            with st.spinner("Processing & Indexing Reports in ChromaDB RAG..."):
                for uploaded_file in all_files:
                    try:
                        uploaded_file.seek(0)
                        file_bytes = uploaded_file.read()
                        text, page_count, char_count = extract_pdf_text_from_bytes(file_bytes, uploaded_file.name)

                        if char_count == 0:
                            st.error(f"⚠️ Could not extract text from '{uploaded_file.name}'. Ensure it contains selectable text.")
                        else:
                            stats = ingest_document(text, uploaded_file.name)
                            st.success(f"✅ Indexed '{uploaded_file.name}' ({page_count} pages, {char_count} chars, {stats['num_chunks']} chunks)")
                    except Exception as e:
                        st.error(f"Failed to process {uploaded_file.name}: {e}")
        else:
            st.warning("Please select at least one PDF report file.")

    # View Uploaded Reports
    st.divider()
    st.subheader("📄 View Uploaded Reports")
    uploaded_docs = get_uploaded_documents()
    if uploaded_docs:
        for doc in uploaded_docs:
            st.caption(f"• {doc}")
    else:
        st.caption("No reports in knowledge base.")

    if st.button("Clear Knowledge Base"):
        clear_knowledge_base()
        st.rerun()

    st.divider()

    # Session & Chat History Management
    st.subheader("💬 Conversations")
    sessions = get_all_sessions()
    if sessions:
        selected_session = st.selectbox("Previous Conversations", sessions, index=0 if st.session_state.session_id in sessions else 0)
        if selected_session != st.session_state.session_id:
            st.session_state.session_id = selected_session
            st.session_state.messages = get_chat_history(selected_session)
            st.rerun()

    if st.button("Clear Chat"):
        clear_chat_history(st.session_state.session_id)
        st.session_state.messages = []
        st.rerun()

# ================= MAIN SCREEN =================
st.markdown('<div class="main-title">📈 AI Financial Research Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Automated fundamental research, RAG report analysis, multi-company comparisons, and structured report generation.</div>', unsafe_allow_html=True)

# Quick Action Prompt Chips
st.markdown("**Quick Action Prompts:**")
col_q1, col_q2, col_q3, col_q4 = st.columns(4)
prompt_to_submit = None

with col_q1:
    if st.button("🔍 Research Microsoft"):
        prompt_to_submit = "What was Microsoft's revenue and net income?"
with col_q2:
    if st.button("⚖️ Compare MSFT & GOOG"):
        prompt_to_submit = "Compare Microsoft and Google."
with col_q3:
    if st.button("📊 Summarize PDF Reports"):
        prompt_to_submit = "Summarize the key risk factors in the uploaded annual report."
with col_q4:
    if st.button("📋 Generate Investment Report"):
        prompt_to_submit = "Generate today's investment report for Microsoft."

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input Handler
user_input = st.chat_input("Ask a question (e.g. 'What was Microsoft's revenue?', 'What are Microsoft's major business segments?')...")
final_input = prompt_to_submit or user_input

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    save_chat_message(st.session_state.session_id, "user", final_input)
    with st.chat_message("user"):
        st.markdown(final_input)

    with st.chat_message("assistant"):
        with st.spinner("AI Agents executing workflow..."):
            response_data = execute_coordinator(final_input, st.session_state.session_id)
            route_used = response_data.get("route", "Agent")
            output_text = extract_text_content(response_data.get("output", ""))

            st.caption(f"⚡ **Routed via:** `{route_used}`")
            st.markdown(output_text)

            # Expandable Sections
            if "pdf_chunks" in response_data and response_data["pdf_chunks"]:
                with st.expander("📚 Retrieved PDF Chunks (RAG Context)"):
                    for idx, chunk in enumerate(response_data["pdf_chunks"], 1):
                        st.markdown(f"**Chunk {idx} (Source: {chunk['metadata'].get('source')})**")
                        st.write(chunk["page_content"])

            if "code" in response_data:
                with st.expander("🧮 Financial Calculations & Python Code"):
                    st.code(response_data["code"], language="python")

            if "news" in route_used.lower() or "news" in final_input.lower():
                with st.expander("📰 Latest News Summary"):
                    st.markdown(output_text)

            if "report" in route_used.lower() or "investment" in final_input.lower():
                with st.expander("🎯 Final Recommendation & Summary"):
                    st.markdown(output_text)

            # Download Options
            st.markdown("---")
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    label="📥 Download Report (.txt)",
                    data=output_text,
                    file_name="Investment_Report.txt",
                    mime="text/plain",
                    key=f"txt_{len(st.session_state.messages)}"
                )
            with col_dl2:
                st.download_button(
                    label="📥 Download Report (.pdf)",
                    data=output_text.encode('utf-8'),
                    file_name="Investment_Report.pdf",
                    mime="application/pdf",
                    key=f"pdf_{len(st.session_state.messages)}"
                )

            # Email Options
            if "report" in route_used.lower() or "investment" in final_input.lower() or "# Investment Research Report" in output_text:
                with st.expander("📧 Email This Report", expanded=True):
                    email_col1, email_col2 = st.columns(2)
                    with email_col1:
                        recipient_email = st.text_input(
                            "Email",
                            value="aravindpooja2306@gmail.com",
                            key=f"email_input_{len(st.session_state.messages)}"
                        )
                    with email_col2:
                        email_topic = st.text_input(
                            "Topic",
                            value="Microsoft Financial Report",
                            key=f"email_topic_{len(st.session_state.messages)}"
                        )

                    send_btn = st.button("Send Mail", key=f"send_btn_{len(st.session_state.messages)}")

                    if send_btn:
                        # Prevent rerun duplicate sends
                        action_key = f"sent_{len(st.session_state.messages)}_{recipient_email}_{email_topic}"
                        if st.session_state.get("last_sent_action_key") == action_key:
                            st.info("Email has already been successfully sent.")
                        else:
                            with st.spinner("Sending report..."):
                                from agents.email_agent import send_email_report
                                res_msg = send_email_report(
                                    recipient_email=recipient_email,
                                    subject=email_topic,
                                    report_content=output_text,
                                    pdf_bytes=output_text.encode('utf-8')
                                )
                                if "successfully" in res_msg.lower() or "✅" in res_msg:
                                    st.success("✅ Email sent successfully")
                                    st.session_state["last_sent_action_key"] = action_key
                                else:
                                    st.error(res_msg)

            st.session_state.messages.append({"role": "assistant", "content": output_text})
            save_chat_message(st.session_state.session_id, "assistant", output_text)
