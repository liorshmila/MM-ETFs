from pathlib import Path
import sqlite3
import pandas as pd
from etf_config import load_etfs


def load_portfolio(portfolio_path):
    portfolio_df = pd.read_csv(portfolio_path)
    portfolio_df["Ticker"] = portfolio_df["Ticker"].astype(str).str.upper().str.strip()
    portfolio_df["Weight"] = pd.to_numeric(portfolio_df["Weight"], errors="coerce")
    portfolio_df = portfolio_df.dropna(subset=["Ticker", "Weight"]).copy()

    raw_weight_sum = portfolio_df["Weight"].sum()

    if raw_weight_sum == 0:
        raise ValueError("Portfolio weights sum to zero.")

    portfolio_df["Target Weight"] = portfolio_df["Weight"] / raw_weight_sum

    return portfolio_df


def ensure_rebalance_table(conn):
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rebalance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            month TEXT,
            ticker TEXT,
            action TEXT,
            quantity REAL,
            price REAL,
            value REAL,
            drift_before REAL,
            reason TEXT
        )
        """
    )

    conn.commit()


def load_close_prices(conn, tickers):
    query = f"""
    SELECT date, ticker, close_price
    FROM price_history
    WHERE ticker IN ({','.join(['?'] * len(tickers))})
    ORDER BY date
    """

    df = pd.read_sql_query(query, conn, params=tickers)

    if df.empty:
        raise ValueError("No price data found in DB.")

    close_prices = df.pivot(index="date", columns="ticker", values="close_price")
    close_prices.index = pd.to_datetime(close_prices.index)
    close_prices = close_prices.sort_index()

    missing = [ticker for ticker in tickers if ticker not in close_prices.columns]

    if missing:
        raise ValueError("Missing price data for: " + ", ".join(missing))

    close_prices = close_prices[tickers].dropna()

    if close_prices.empty:
        raise ValueError("No complete price rows found for all tickers.")

    return close_prices


def rebuild_etf_rebalance(etf):
    etf_id = etf["id"]
    status = etf.get("status", "active")

    if status == "coming_soon":
        print(f"\nSkipping {etf_id}: coming soon")
        return

    portfolio_path = Path(etf["portfolio_path"])
    db_path = Path(etf["db_path"])

    total_capital = etf.get("initial_capital", 100000)
    drift_threshold = etf.get("drift_threshold", 0.02)

    if not portfolio_path.exists():
        print(f"\nSkipping {etf_id}: missing portfolio file {portfolio_path}")
        return

    if not db_path.exists():
        print(f"\nSkipping {etf_id}: missing DB file {db_path}")
        return

    print(f"\nRebuilding rebalance log for {etf_id}")
    print(f"Portfolio: {portfolio_path}")
    print(f"DB: {db_path}")
    print(f"Drift threshold: {drift_threshold:.2%}")

    portfolio_df = load_portfolio(portfolio_path)

    tickers = portfolio_df["Ticker"].tolist()
    target_weights = dict(zip(portfolio_df["Ticker"], portfolio_df["Target Weight"]))

    conn = sqlite3.connect(db_path)

    try:
        close_prices = load_close_prices(conn, tickers)
        ensure_rebalance_table(conn)

        cursor = conn.cursor()
        cursor.execute("DELETE FROM rebalance_log")
        conn.commit()

        first_date = close_prices.index[0]
        first_prices = close_prices.loc[first_date]

        holdings = {}

        for ticker in tickers:
            initial_value = total_capital * target_weights[ticker]
            holdings[ticker] = initial_value / first_prices[ticker]

        latest_period = close_prices.index[-1].to_period("M")

        month_end_dates = (
            close_prices
            .groupby(close_prices.index.to_period("M"))
            .apply(lambda x: x.index.max())
        )

        completed_month_end_dates = [
            date for period, date in month_end_dates.items()
            if period < latest_period
        ]

        all_trade_rows = []

        for rebalance_date in completed_month_end_dates:
            prices = close_prices.loc[rebalance_date]

            current_values = {
                ticker: holdings[ticker] * prices[ticker]
                for ticker in tickers
            }

            total_value = sum(current_values.values())

            rows = []

            for ticker in tickers:
                actual_weight = current_values[ticker] / total_value
                target_weight = target_weights[ticker]
                drift = actual_weight - target_weight

                rows.append(
                    {
                        "Ticker": ticker,
                        "Target Weight": target_weight,
                        "Actual Weight": actual_weight,
                        "Drift": drift,
                        "Current Value": current_values[ticker],
                        "Price": prices[ticker],
                    }
                )

            holdings_df = pd.DataFrame(rows)

            sell_df = holdings_df[holdings_df["Drift"] > drift_threshold].copy()
            buy_df = holdings_df[holdings_df["Drift"] < 0].copy()

            if sell_df.empty or buy_df.empty:
                continue

            sell_df["Target Value"] = sell_df["Target Weight"] * total_value
            sell_df["Trade Value"] = sell_df["Target Value"] - sell_df["Current Value"]
            total_sell_cash = -sell_df["Trade Value"].sum()

            buy_df["Target Value"] = buy_df["Target Weight"] * total_value
            buy_df["Deficit Value"] = buy_df["Target Value"] - buy_df["Current Value"]
            total_deficit = buy_df["Deficit Value"].sum()

            if total_sell_cash <= 0 or total_deficit <= 0:
                continue

            buy_df["Trade Value"] = buy_df["Deficit Value"] / total_deficit * total_sell_cash

            month_label = rebalance_date.strftime("%Y-%m")

            for _, row in sell_df.iterrows():
                ticker = row["Ticker"]
                trade_value = abs(row["Trade Value"])
                price = row["Price"]
                quantity = trade_value / price

                holdings[ticker] -= quantity

                all_trade_rows.append(
                    {
                        "date": rebalance_date.date(),
                        "month": month_label,
                        "ticker": ticker,
                        "action": "SELL",
                        "quantity": quantity,
                        "price": price,
                        "value": trade_value,
                        "drift_before": row["Drift"],
                        "reason": "Drift above threshold",
                    }
                )

            for _, row in buy_df.iterrows():
                ticker = row["Ticker"]
                trade_value = row["Trade Value"]
                price = row["Price"]
                quantity = trade_value / price

                holdings[ticker] += quantity

                all_trade_rows.append(
                    {
                        "date": rebalance_date.date(),
                        "month": month_label,
                        "ticker": ticker,
                        "action": "BUY",
                        "quantity": quantity,
                        "price": price,
                        "value": trade_value,
                        "drift_before": row["Drift"],
                        "reason": "Funded by overweight positions",
                    }
                )

        for row in all_trade_rows:
            cursor.execute(
                """
                INSERT INTO rebalance_log
                (date, month, ticker, action, quantity, price, value, drift_before, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row["date"]),
                    row["month"],
                    row["ticker"],
                    row["action"],
                    row["quantity"],
                    row["price"],
                    row["value"],
                    row["drift_before"],
                    row["reason"],
                ),
            )

        conn.commit()

        if not all_trade_rows:
            print(f"{etf_id}: no monthly rebalance trades generated.")
        else:
            print(f"{etf_id}: saved {len(all_trade_rows)} rebalance rows.")

    except Exception as error:
        print(f"{etf_id}: ERROR - {error}")

    finally:
        conn.close()


def main():
    etfs = load_etfs()

    if not etfs:
        print("No ETFs found.")
        return

    for etf in etfs:
        rebuild_etf_rebalance(etf)

    print("\nAll rebalance rebuilds completed.")


if __name__ == "__main__":
    main()