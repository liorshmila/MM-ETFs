import json
import sqlite3
from pathlib import Path

import pandas as pd
import yfinance as yf


CONFIG_FILE = Path("compare_config.json")
DB_FILE = Path("compare.db")
START_DATE = "2026-01-01"


def load_compare_assets():
    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        assets = json.load(file)

    tickers = [
        asset["ticker"].upper().strip()
        for asset in assets
        if asset.get("ticker")
    ]

    return sorted(set(tickers))


def ensure_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS compare_price_history (
            date TEXT NOT NULL,
            ticker TEXT NOT NULL,
            close_price REAL NOT NULL,
            PRIMARY KEY (ticker, date)
        )
        """
    )
    conn.commit()


def download_compare_prices(tickers):
    end_date = (pd.Timestamp.today() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    data = yf.download(
        tickers,
        start=START_DATE,
        end=end_date,
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        progress=False,
        threads=True,
    )

    if data.empty:
        return pd.DataFrame()

    close_df = pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        if "Close" in data.columns.get_level_values(0):
            close_df = data["Close"][tickers].copy()
        elif "Close" in data.columns.get_level_values(1):
            close_df = pd.concat(
                {ticker: data[ticker]["Close"] for ticker in tickers},
                axis=1,
            )
        else:
            raise ValueError("Could not find Close prices in Yahoo data")
    else:
        close_df[tickers[0]] = data["Close"]

    close_df.index = pd.to_datetime(close_df.index)
    close_df = close_df.sort_index()
    close_df = close_df.dropna(how="any")

    return close_df


def rebuild_compare_db(tickers, close_df):
    conn = sqlite3.connect(DB_FILE)

    try:
        ensure_table(conn)

        conn.execute("DELETE FROM compare_price_history")

        rows = []

        for date, row in close_df.iterrows():
            date_text = date.strftime("%Y-%m-%d")

            for ticker in tickers:
                rows.append((ticker, date_text, float(row[ticker])))

        conn.executemany(
            """
            INSERT OR REPLACE INTO compare_price_history
            (ticker, date, close_price)
            VALUES (?, ?, ?)
            """,
            rows,
        )

        conn.commit()

    finally:
        conn.close()

    return len(rows)


def main():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Missing {CONFIG_FILE}")

    tickers = load_compare_assets()

    if not tickers:
        print("No compare tickers found.")
        return

    print("Updating compare assets")
    print("Tickers:", ", ".join(tickers))

    close_df = download_compare_prices(tickers)

    if close_df.empty:
        print("No complete compare price data downloaded.")
        return

    print(f"Complete dates downloaded: {close_df.index.min().date()} → {close_df.index.max().date()}")
    print(f"Complete rows: {len(close_df)} dates × {len(tickers)} tickers")

    rows = rebuild_compare_db(tickers, close_df)

    print(f"compare.db rebuilt with {rows} rows.")
    print("Compare assets update completed.")


if __name__ == "__main__":
    main()