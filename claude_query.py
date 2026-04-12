import anthropic
import psycopg2
import os
import json
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
DB_URL = os.getenv("DATABASE_URL")

def run_query(sql: str):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(sql)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return columns, rows

def ask_claude(question: str):
    # Step 1: Ask Claude to generate SQL
    sql_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system="""You are a PostgreSQL expert. Convert the user's question into a SQL query.
        The database has one table called asx_stocks with these columns:
        - ticker (VARCHAR): ASX stock code e.g. BHP.AX, CBA.AX
        - date (DATE): trading date
        - open (NUMERIC): opening price
        - high (NUMERIC): highest price
        - low (NUMERIC): lowest price
        - close (NUMERIC): closing price
        - volume (BIGINT): number of shares traded
        
        Return ONLY the SQL query, nothing else. No explanation, no markdown, just raw SQL.""",
        messages=[{"role": "user", "content": question}]
    )
    
    sql = sql_response.content[0].text.strip()
    
    try:
        # Step 2: Run the SQL against PostgreSQL
        columns, rows = run_query(sql)
        
        # Step 3: Ask Claude to interpret the results
        result_data = {"columns": columns, "rows": [list(r) for r in rows]}
        
        insight_response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system="""You are a financial analyst specialising in ASX stocks. 
            The user asked a question and you ran a SQL query to get data. 
            Now provide a clear, concise insight based on the results.
            Be specific, mention actual numbers, and keep it to 3-5 sentences.""",
            messages=[
                {"role": "user", "content": f"""
                Original question: {question}
                SQL query used: {sql}
                Results: {json.dumps(result_data, default=str)}
                
                Please provide a clear insight based on these results.
                """}
            ]
        )
        
        insight = insight_response.content[0].text.strip()
        
        return {
            "sql": sql,
            "columns": columns,
            "rows": rows,
            "insight": insight
        }
    
    except Exception as e:
        return {
            "sql": sql,
            "columns": [],
            "rows": [],
            "insight": f"Error running query: {str(e)}"
        }

if __name__ == "__main__":
    result = ask_claude("Which ASX stock had the highest closing price last month?")
    print("SQL:", result["sql"])
    print("Insight:", result["insight"])