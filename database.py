import psycopg2
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DB_URL)

def create_database():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS asx_stocks (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(20),
            date DATE,
            open NUMERIC,
            high NUMERIC,
            low NUMERIC,
            close NUMERIC,
            volume BIGINT
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("Table created successfully")

def load_asx_data():
    # Top 10 ASX stocks
    tickers = [
        "BHP.AX", "CBA.AX", "CSL.AX", "NAB.AX", "WBC.AX",
        "ANZ.AX", "WES.AX", "MQG.AX", "RIO.AX", "TLS.AX"
    ]
    
    conn = get_connection()
    cur = conn.cursor()
    
    for ticker in tickers:
        print(f"Downloading {ticker}...")
        df = yf.download(ticker, period="1y", auto_adjust=True)
        df.reset_index(inplace=True)
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO asx_stocks (ticker, date, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                ticker,
                pd.Timestamp(row["Date"]).date(),
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                int(row["Volume"])
            ))
    
    conn.commit()
    cur.close()
    conn.close()
    print("ASX data loaded successfully")

if __name__ == "__main__":
    create_database()
    load_asx_data()