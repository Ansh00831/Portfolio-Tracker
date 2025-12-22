import sqlite3
import pandas as pd
import os

DB_PATH = "data/portfolio.db"

def init_database():
    """Initialize SQLite database with portfolio table."""
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Ticker TEXT NOT NULL,
            Quantity INTEGER NOT NULL,
            Buy_Price REAL NOT NULL,
            Buy_Date TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


def load_portfolio():
    """Load portfolio from database."""
    init_database()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT Ticker, Quantity, Buy_Price, Buy_Date FROM holdings", conn)
        conn.close()
        
        # Convert Buy_Date to datetime
        if not df.empty:
            df["Buy_Date"] = pd.to_datetime(df["Buy_Date"]).dt.date
        
        return df
    except Exception as e:
        return pd.DataFrame(columns=["Ticker", "Quantity", "Buy_Price", "Buy_Date"])


def save_portfolio(portfolio_df):
    """Save portfolio to database."""
    init_database()
    
    conn = sqlite3.connect(DB_PATH)
    
    # Clear existing data
    conn.execute("DELETE FROM holdings")
    
    # Insert new data
    portfolio_df.to_sql("holdings", conn, if_exists="append", index=False)
    
    conn.commit()
    conn.close()


def delete_holdings(portfolio_df, indices):
    """Delete holdings at specified indices."""
    return portfolio_df.drop(indices).reset_index(drop=True)

