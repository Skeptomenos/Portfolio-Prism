import sqlite3
import os
from typing import Dict, List, Optional
import pandas as pd

DB_PATH = "data/working/database/portfolio.db"


def init_db():
    """Initialize the SQLite database with tables."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Securities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS securities (
            isin TEXT PRIMARY KEY,
            name TEXT,
            ticker TEXT,
            provider TEXT,
            asset_type TEXT,
            exchange TEXT,
            sector TEXT,
            links TEXT,  -- JSON string
            price REAL,
            last_updated TEXT
        )
    """)

    # Holdings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            isin TEXT,
            holding_ticker TEXT,
            holding_name TEXT,
            weight_percentage REAL,
            last_updated TEXT,
            FOREIGN KEY (isin) REFERENCES securities (isin)
        )
    """)

    # Metadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Insert version
    cursor.execute(
        "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", ("version", "1.0")
    )

    conn.commit()
    conn.close()


def insert_security(
    isin: str,
    name: str,
    ticker: str,
    provider: str,
    asset_type: str = "stock",
    exchange: str = "",
    sector: str = "",
    links: Dict = None,
    price: float = None,
):
    """Insert or update a security in the DB."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    links_json = str(links) if links else "{}"
    last_updated = pd.Timestamp.now().isoformat()

    cursor.execute(
        """
        INSERT OR REPLACE INTO securities 
        (isin, name, ticker, provider, asset_type, exchange, sector, links, price, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            isin,
            name,
            ticker,
            provider,
            asset_type,
            exchange,
            sector,
            links_json,
            price,
            last_updated,
        ),
    )

    conn.commit()
    conn.close()


def get_security(isin: str) -> Optional[Dict]:
    """Retrieve a security from the DB."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM securities WHERE isin = ?", (isin,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "isin": row[0],
            "name": row[1],
            "ticker": row[2],
            "provider": row[3],
            "asset_type": row[4],
            "exchange": row[5],
            "sector": row[6],
            "links": eval(row[7]) if row[7] else {},
            "price": row[8],
            "last_updated": row[9],
        }
    return None


def insert_holdings(isin: str, holdings_df: pd.DataFrame):
    """Insert ETF holdings into the DB."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    last_updated = pd.Timestamp.now().isoformat()

    for _, row in holdings_df.iterrows():
        cursor.execute(
            """
            INSERT OR REPLACE INTO holdings 
            (isin, holding_ticker, holding_name, weight_percentage, last_updated)
            VALUES (?, ?, ?, ?, ?)
        """,
            (isin, row["ticker"], row["name"], row["weight_percentage"], last_updated),
        )

    conn.commit()
    conn.close()


def get_holdings(isin: str) -> pd.DataFrame:
    """Retrieve ETF holdings from the DB."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM holdings WHERE isin = ?", conn, params=(isin,)
    )
    conn.close()
    return df[["holding_ticker", "holding_name", "weight_percentage"]].rename(
        columns={"holding_ticker": "ticker", "holding_name": "name"}
    )


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
