from pathlib import Path
import sqlite3
import pandas as pd
import yfinance as yf
from etf_config import load_etfs


START_DATE = "2026-01-01"


def ensure_price_history_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS price_history (
            date TEXT NOT NULL,
            ticker TEXT NOT NULL,
            close_price REAL NOT NULL,
            PRIMARY KEY (ticker, date)
        )
        """
    )
    conn.commit()


def load_portfolio_tickers(portfolio_path):
    df = pd.read_csv(portfolio_path)
    df["Ticker"] = df["Ticker"].astype(str).str.upper().str.strip()
    df = df.dropna(subset=["Ticker"])
    return sorted(df["Ticker"].unique().tolist())


def download_prices_batch(tickers):
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
                axis=1
            )
        else:
            raise ValueError("Could not find Close prices in Yahoo data")
    else:
        close_df[tickers[0]] = data["Close"]

    close_df.index = pd.to_datetime(close_df.index)
    close_df = close_df.sort_index()
    close_df = close_df.dropna(how="any")

    return close_df


def replace_price_history(conn, tickers, close_df):
    conn.execute(
        f"""
        DELETE FROM price_history
        WHERE ticker NOT IN ({",".join(["?"] * len(tickers))})
        """,
        tickers,
    )

    conn.execute("DELETE FROM price_history")

    rows = []

    for date, row in close_df.iterrows():
        date_text = date.strftime("%Y-%m-%d")

        for ticker in tickers:
            rows.append((ticker, date_text, float(row[ticker])))

    conn.executemany(
        """
        INSERT OR REPLACE INTO price_history (ticker, date, close_price)
        VALUES (?, ?, ?)
        """,
        rows,
    )

    conn.commit()
    return len(rows)


def update_etf(etf):
    etf_id = etf["id"]

    if etf.get("status", "active") == "coming_soon":
        print(f"\nSkipping {etf_id}: coming soon")
        return

    portfolio_path = Path(etf["portfolio_path"])
    db_path = Path(etf["db_path"])

    if not portfolio_path.exists():
        print(f"\nSkipping {etf_id}: missing portfolio file {portfolio_path}")
        return

    tickers = load_portfolio_tickers(portfolio_path)

    if not tickers:
        print(f"\nSkipping {etf_id}: no tickers found")
        return

    print(f"\nUpdating {etf_id}")
    print(f"DB: {db_path}")
    print(f"Tickers: {', '.join(tickers)}")

    close_df = download_prices_batch(tickers)

    if close_df.empty:
        print(f"{etf_id}: no complete price data downloaded")
        return

    print(f"Complete dates downloaded: {close_df.index.min().date()} → {close_df.index.max().date()}")
    print(f"Complete rows: {len(close_df)} dates × {len(tickers)} tickers")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)

    try:
        ensure_price_history_table(conn)
        rows_written = replace_price_history(conn, tickers, close_df)
    finally:
        conn.close()

    print(f"{etf_id} completed. Rebuilt price_history with {rows_written} rows.")


def main():
    etfs = load_etfs()

    if not etfs:
        print("No ETFs found.")
        return

    for etf in etfs:
        update_etf(etf)

    print("\nAll ETF updates completed.")


if __name__ == "__main__":
    main()