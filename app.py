import streamlit as st
from claude_query import ask_claude
import pandas as pd

st.set_page_config(
    page_title="ASX Stock Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 ASX Stock Dashboard")
st.markdown("Ask any question about ASX stock performance in plain English.")

st.divider()

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
    This dashboard uses:
    - **PostgreSQL** to store ASX stock data
    - **Claude AI** to convert your question to SQL
    - **MCP** to connect Claude to the database
    - **Streamlit** for this interface
    """)
    st.markdown("**Stocks tracked:**")
    st.markdown("BHP, CBA, CSL, NAB, WBC, ANZ, WES, MQG, RIO, TLS")

# Example questions
st.subheader("Try asking:")
examples = [
    "Which stock had the highest closing price last month?",
    "What is the average closing price of BHP.AX over the past 3 months?",
    "Which stock had the biggest single-day price drop this year?",
    "Compare the closing prices of CBA.AX and NAB.AX over the last 30 days",
    "Which stock has the highest average trading volume?",
]

cols = st.columns(2)
for i, example in enumerate(examples):
    if cols[i % 2].button(example, use_container_width=True):
        st.session_state.question = example

# Input
question = st.text_input(
    "Your question:",
    value=st.session_state.get("question", ""),
    placeholder="e.g. Which ASX stock had the highest closing price last month?"
)

if st.button("Ask Claude", type="primary") and question:
    with st.spinner("Claude is thinking..."):
        result = ask_claude(question)

    st.divider()

    # Insight
    st.subheader("Claude's Insight")
    st.info(result["insight"])

    # SQL
    with st.expander("View generated SQL"):
        st.code(result["sql"], language="sql")

    # Data table
    if result["rows"]:
        st.subheader("Raw Data")
        df = pd.DataFrame(result["rows"], columns=result["columns"])
        st.dataframe(df, use_container_width=True)

        # Chart if close column exists
        if "close" in df.columns and "date" in df.columns:
            st.subheader("Price Chart")
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")
            if "ticker" in df.columns and df["ticker"].nunique() > 1:
                chart_data = df.pivot(index="date", columns="ticker", values="close")
            else:
                chart_data = df.set_index("date")[["close"]]
            st.line_chart(chart_data)
    else:
        st.warning("No data returned for this query.")