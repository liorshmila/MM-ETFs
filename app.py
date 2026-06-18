# ------------- Imports ------------------
import pandas as pd
import streamlit as st
from pathlib import Path
import sqlite3
import base64
from etf_config import load_etfs
import json
import streamlit.components.v1 as components
import os
# ----------------------------------------

# ------------ Page Config ---------------
st.set_page_config(
    page_title="MM ETFs",
    page_icon="assets/MMFavicon.png",
    layout="wide")
# ----------------------------------------

# ------------- Globals ------------------
YOUTUBE_URL = "https://www.youtube.com/@MarketMakersIL"
LOGO_PATH = "assets/MMLogo.jpg"
ACCESS_PASSWORD = st.secrets.get(
    "ACCESS_PASSWORD",
    os.getenv("ACCESS_PASSWORD", "")
)
ALLOWED_USERS_CSV = "allowed_users.csv"
MAIN_PAGE_BACKGROUND = "assets/MMETFsBackground.png"
YOUTUBE_ICON = "assets/YouTubeLogo.png"
MAIL_ICON = "assets/MailLogo.png"
COMPARE_CONFIG = "compare_config.json"
COMPARE_DB = "compare.db"
# ----------------------------------------

# ---------- Simple Access Gate ----------
def load_allowed_users(csv_path):
    try:
        users_df = pd.read_csv(csv_path)
        users_df["email"] = users_df["email"].astype(str).str.lower().str.strip()
        return set(users_df["email"].tolist())
    except FileNotFoundError:
        return set()
allowed_users = load_allowed_users(ALLOWED_USERS_CSV)
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
# ----------------------------------------

# ----------------- CSS ------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #0a0d0a 0%, #0f140f 100%);
        color: #e8f5e9;
    }
    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }
    div[data-testid="stTextInput"] input {
        background-color: rgba(10,13,10,0.96) !important;
        color: #eaffea !important;
        border: 1px solid rgba(123,255,92,0.35) !important;
        border-radius: 12px !important;
    }
    div[data-testid="stTextInput"] label {
        color: #eaffea !important;
        font-weight: 800 !important;
    }
    h1, h2, h3, h4 {
        color: #eaffea !important;
        letter-spacing: 0.2px;
    }
    .brand-wrap {
        display: flex;
        align-items: center;
        gap: 18px;
        padding: 18px 22px;
        border: 1px solid rgba(123, 255, 92, 0.18);
        border-radius: 20px;
        background:
            radial-gradient(circle at top left, rgba(123,255,92,0.12), transparent 32%),
            linear-gradient(180deg, rgba(18,24,18,0.95), rgba(10,13,10,0.95));
        box-shadow: 0 0 24px rgba(123,255,92,0.08);
        margin-bottom: 18px;
    }
    .brand-title {
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1;
        color: #dfffe0;
        margin: 0;
    }
    .brand-subtitle {
        font-size: 1rem;
        color: #9ccc8c;
        margin-top: 6px;
    }
    .brand-link a {
        display: inline-block;
        margin-top: 12px;
        padding: 10px 16px;
        background: linear-gradient(90deg, #5faa3d, #86ff5c);
        color: #081008 !important;
        text-decoration: none;
        font-weight: 700;
        border-radius: 12px;
        box-shadow: 0 0 16px rgba(123,255,92,0.18);
    }
    .metric-card {
        border: 1px solid rgba(123,255,92,0.15);
        background:
            linear-gradient(180deg, rgba(16,22,16,0.96), rgba(10,13,10,0.96));
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 0 18px rgba(123,255,92,0.06);
    }
    .metric-label {
        color: #9ccc8c;
        font-size: 0.9rem;
        margin-bottom: 6px;
    }
    .metric-value {
        color: #f3fff3;
        font-size: 2rem;
        font-weight: 800;
    }
    .section-card {
        border: 1px solid rgba(123,255,92,0.12);
        background:
            linear-gradient(180deg, rgba(16,22,16,0.96), rgba(10,13,10,0.96));
        border-radius: 18px;
        padding: 16px 16px 10px 16px;
        margin-top: 14px;
        box-shadow: 0 0 18px rgba(123,255,92,0.05);
    }
    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(123,255,92,0.12);
    }
    [data-testid="stMetric"] {
        background: transparent;
    }
    .btn-icon-img {
        width: 90px;
        height: 90px;
        object-fit: contain;
        flex-shrink: 0;
    }
    .home-action-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 20px;
        height: 90px !important;
        min-height: 90px !important;
        padding: 18px 30px;
        border-radius: 18px;
        text-decoration: none !important;
        font-size: 1.35rem;
        font-weight: 900;
        letter-spacing: 0.2px;
        border: 1px solid rgba(123,255,92,0.35);
        box-shadow: 0 0 22px rgba(123,255,92,0.20);
        transition: all 0.18s ease-in-out;
    }
    .home-action-btn span {
        white-space: nowrap;
    }
    .home-action-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 32px rgba(123,255,92,0.35);
    }
    .youtube-btn {
        background: linear-gradient(
            90deg,
            #6dff48,
            #4fb132
        );
        color: #071107 !important;
    }
    .feedback-btn {
        background: linear-gradient(
            90deg,
            rgba(16,35,16,0.95),
            rgba(67,125,45,0.95)
        );
        color: #eaffea !important;
    }
    .btn-icon {
        font-size: 1.7rem;
        line-height: 1;
    }
    .etf-card {
        border: 1px solid rgba(123,255,92,0.16);
        background: linear-gradient(180deg, rgba(16,22,16,0.96), rgba(10,13,10,0.96));
        border-radius: 18px;
        padding: 18px;
        min-height: 300px;
        box-shadow: 0 0 18px rgba(123,255,92,0.06);
        margin-top: 12px;
    }
    div.stButton > button {
        width: auto;
        background: linear-gradient(90deg, #5faa3d, #86ff5c) !important;
        color: #071107 !important;
        border: 1px solid rgba(123,255,92,0.55) !important;
        border-radius: 14px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 900 !important;
        font-size: 1rem !important;
        box-shadow: 0 0 18px rgba(123,255,92,0.25) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 0 28px rgba(123,255,92,0.40) !important;
    }
    div.element-container:has(.open-etf-button-marker) + div.stButton,
    div.element-container:has(.open-etf-button-marker) + div.element-container div.stButton {
        width: 100% !important;
    }
    div.element-container:has(.open-etf-button-marker) + div.stButton > button,
    div.element-container:has(.open-etf-button-marker) + div.element-container div.stButton > button {
        width: 100% !important;
        min-height: 74px !important;
        background: #ffffff !important;
        color: #071107 !important;
        border-radius: 16px !important;
        border: 1px solid rgba(123,255,92,0.65) !important;
        font-size: 1.25rem !important;
        font-weight: 900 !important;
        box-shadow: 0 0 22px rgba(123,255,92,0.28) !important;
    }
    div.element-container:has(.open-etf-button-marker) + div.stButton > button p,
    div.element-container:has(.open-etf-button-marker) + div.element-container div.stButton > button p {
        font-size: 1.25rem !important;
        font-weight: 900 !important;
        color: #071107 !important;
    }
    div[data-testid="stCheckbox"] label p,
    div[data-testid="stDateInput"] label p {
        color: #eaffea !important;
        font-weight: 800 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# ----------------------------------------

# ------------ Authentication ------------
if not st.session_state["authenticated"]:
    st.title("MM ETFs Access")
    st.write("Enter your approved email and access password.")

    email = st.text_input("Email").lower().strip()
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if email in allowed_users and password == ACCESS_PASSWORD:
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email
            st.rerun()
        elif email not in allowed_users:
            st.error("Access denied: email is not approved.")
        else:
            st.error("Access denied: wrong password.")
    st.stop()
# ----------------------------------------

# ------------ ETF Home Page -------------
def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        return None

def load_compare_assets():
    try:
        with open(COMPARE_CONFIG, "r", encoding="utf-8") as file:
            assets = json.load(file)

        return [
            {
                "ticker": asset["ticker"].upper().strip(),
                "name": asset.get("name", asset["ticker"]).strip(),
            }
            for asset in assets
            if asset.get("ticker")
        ]
    except FileNotFoundError:
        return []

def load_compare_colors():
    try:
        with open(COMPARE_CONFIG, "r", encoding="utf-8") as file:
            assets = json.load(file)

        return {
            asset["ticker"].upper().strip():
            asset.get("color", "#FFFFFF")
            for asset in assets
            if asset.get("ticker")
        }

    except FileNotFoundError:
        return {}

def load_compare_series(selected_tickers, start_date, end_date):
    if not selected_tickers:
        return {}
    if not Path(COMPARE_DB).exists():
        return {}
    conn = sqlite3.connect(COMPARE_DB)
    query = f"""
    SELECT date, ticker, close_price
    FROM compare_price_history
    WHERE ticker IN ({",".join(["?"] * len(selected_tickers))})
      AND date >= ?
      AND date <= ?
    ORDER BY date
    """
    params = selected_tickers + [
        pd.to_datetime(start_date).strftime("%Y-%m-%d"),
        pd.to_datetime(end_date).strftime("%Y-%m-%d"),
    ]
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    if df.empty:
        return {}
    df["date"] = pd.to_datetime(df["date"])
    pivot = df.pivot(index="date", columns="ticker", values="close_price")
    pivot = pivot.sort_index().dropna(how="any")

    if pivot.empty:
        return {}
    comparison_series = {}
    for ticker in selected_tickers:
        if ticker not in pivot.columns:
            continue
        normalized = pivot[ticker] / pivot[ticker].iloc[0] * 100
        comparison_series[ticker] = [
            {
                "time": date.strftime("%Y-%m-%d"),
                "value": float(value),
            }
            for date, value in normalized.items()
        ]
    return comparison_series

def calculate_etf_summary(etf):
    portfolio_path = etf["portfolio_path"]
    db_path = etf["db_path"]
    if not Path(portfolio_path).exists() or not Path(db_path).exists():
        return None
    try:
        local_portfolio_df = pd.read_csv(portfolio_path)
        local_portfolio_df["Ticker"] = local_portfolio_df["Ticker"].astype(str).str.upper().str.strip()
        local_portfolio_df["Weight"] = pd.to_numeric(local_portfolio_df["Weight"], errors="coerce")
        local_portfolio_df = local_portfolio_df.dropna(subset=["Ticker", "Weight"]).copy()
        raw_sum = local_portfolio_df["Weight"].sum()
        if raw_sum == 0:
            return None
        local_portfolio_df["Normalized Weight"] = local_portfolio_df["Weight"] / raw_sum
        local_tickers = local_portfolio_df["Ticker"].tolist()
        conn = sqlite3.connect(db_path)
        query = f"""
        SELECT date, ticker, close_price
        FROM price_history
        WHERE ticker IN ({','.join(['?'] * len(local_tickers))})
        ORDER BY date
        """
        price_df = pd.read_sql_query(query, conn, params=local_tickers)
        try:
            local_rebalance_log_df = pd.read_sql_query(
                """
                SELECT date, ticker, action, quantity, price, value, month
                FROM rebalance_log
                ORDER BY date, action DESC, ticker
                """,
                conn,
            )
        except Exception:
            local_rebalance_log_df = pd.DataFrame()
        conn.close()
        if price_df.empty:
            return None
        local_close_prices = price_df.pivot(index="date", columns="ticker", values="close_price")
        local_close_prices.index = pd.to_datetime(local_close_prices.index)
        local_close_prices = local_close_prices.sort_index()
        missing = [ticker for ticker in local_tickers if ticker not in local_close_prices.columns]
        if missing:
            return None
        local_close_prices = local_close_prices[local_tickers].dropna()
        if local_close_prices.empty:
            return None
        if not local_rebalance_log_df.empty:
            local_rebalance_log_df["date"] = pd.to_datetime(local_rebalance_log_df["date"])
        first_prices_local = local_close_prices.iloc[0]
        local_quantities = {}
        initial_capital = etf.get("initial_capital", 100000)
        for _, row in local_portfolio_df.iterrows():
            ticker = row["Ticker"]
            weight = row["Normalized Weight"]
            local_quantities[ticker] = (initial_capital * weight) / first_prices_local[ticker]
        history_rows = []
        for current_date in local_close_prices.index:
            prices = local_close_prices.loc[current_date]
            total_value = sum(
                local_quantities[ticker] * prices[ticker]
                for ticker in local_tickers
            )
            history_rows.append(
                {
                    "Date": current_date,
                    "Total Value": total_value,
                }
            )
            if not local_rebalance_log_df.empty:
                trades_today = local_rebalance_log_df[local_rebalance_log_df["date"] == current_date]
                for _, trade in trades_today.iterrows():
                    ticker = trade["ticker"]
                    quantity = trade["quantity"]
                    if trade["action"] == "SELL":
                        local_quantities[ticker] -= quantity
                    elif trade["action"] == "BUY":
                        local_quantities[ticker] += quantity
        local_portfolio_values = pd.DataFrame(history_rows).set_index("Date")
        local_portfolio_values["ETF Index"] = (
            local_portfolio_values["Total Value"] / local_portfolio_values["Total Value"].iloc[0] * 100
        )
        latest_value_local = local_portfolio_values["Total Value"].iloc[-1]
        return_pct_local = local_portfolio_values["ETF Index"].iloc[-1] - 100
        running_max_local = local_portfolio_values["ETF Index"].cummax()
        drawdown_local = (local_portfolio_values["ETF Index"] / running_max_local - 1) * 100
        max_drawdown_local = drawdown_local.min()
        return {
            "latest_value": latest_value_local,
            "return_pct": return_pct_local,
            "max_drawdown": max_drawdown_local,
            "last_date": local_portfolio_values.index[-1].date(),
        }
    except Exception:
        return None

def render_tv_style_etf_chart(portfolio_values, rebalance_log_df, chart_title, comparison_series=None):
    if comparison_series is None:
        comparison_series = {}
    st.markdown(
    """
    <style>
    div[data-testid="stRadio"] * {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
    )
    selected_range = st.radio(
        "Range",
        ["1W", "1M", "3M", "6M", "YTD", "1Y", "ALL"],
        index=4,
        horizontal=True,
        key=f"range_{chart_title}",
    )
    chart_source = portfolio_values.reset_index().copy()
    chart_source["Date"] = pd.to_datetime(chart_source["Date"])
    chart_source = chart_source.sort_values("Date")
    latest_date = chart_source["Date"].max()
    if selected_range == "1W":
        start_date = latest_date - pd.DateOffset(weeks=1)
    elif selected_range == "1M":
        start_date = latest_date - pd.DateOffset(months=1)
    elif selected_range == "3M":
        start_date = latest_date - pd.DateOffset(months=3)
    elif selected_range == "6M":
        start_date = latest_date - pd.DateOffset(months=6)
    elif selected_range == "YTD":
        start_date = pd.Timestamp(year=latest_date.year, month=1, day=1)
    elif selected_range == "1Y":
        start_date = latest_date - pd.DateOffset(years=1)
    else:
        start_date = chart_source["Date"].min()
    chart_source = chart_source[chart_source["Date"] >= start_date].copy()
    if len(comparison_series) > 0:
        first_etf_value = chart_source["ETF Index"].iloc[0]
        chart_data = [
            {
                "time": row["Date"].strftime("%Y-%m-%d"),
                "value": float(
                    (row["ETF Index"] / first_etf_value - 1) * 100
                ),
            }
            for _, row in chart_source.iterrows()
        ]
    else:
        chart_data = [
            {
                "time": row["Date"].strftime("%Y-%m-%d"),
                "value": float(row["ETF Index"]),
            }
            for _, row in chart_source.iterrows()
        ]
    filtered_comparison_series = {}
    for ticker, series in comparison_series.items():
        series_df = pd.DataFrame(series)
        if series_df.empty:
            continue
        series_df["time"] = pd.to_datetime(series_df["time"])
        series_df = series_df[
            (series_df["time"] >= start_date) &
            (series_df["time"] <= latest_date)
        ].copy()
        if series_df.empty:
            continue
        first_value = series_df["value"].iloc[0]
        series_df["value"] = (
            series_df["value"] / first_value - 1
        ) * 100
        filtered_comparison_series[ticker] = [
            {
                "time": row["time"].strftime("%Y-%m-%d"),
                "value": float(row["value"]),
            }
            for _, row in series_df.iterrows()
        ]
    rebalance_events = {}
    if not rebalance_log_df.empty:
        local_rebalance_df = rebalance_log_df.copy()
        local_rebalance_df["date"] = pd.to_datetime(local_rebalance_df["date"])
        for date, date_df in local_rebalance_df.groupby(local_rebalance_df["date"].dt.strftime("%Y-%m-%d")):
            marker_date = pd.to_datetime(date)
            if marker_date < start_date:
                continue
            sells = date_df[date_df["action"] == "SELL"]
            buys = date_df[date_df["action"] == "BUY"]
            rebalance_events[date] = {
                "month": str(date_df["month"].iloc[0]),
                "date": date,
                "sold_total": float(sells["value"].sum()),
                "bought_total": float(buys["value"].sum()),
                "sells": [
                    {
                        "ticker": row["ticker"],
                        "quantity": float(row["quantity"]),
                        "price": float(row["price"]),
                        "value": float(row["value"]),
                    }
                    for _, row in sells.iterrows()
                ],
                "buys": [
                    {
                        "ticker": row["ticker"],
                        "quantity": float(row["quantity"]),
                        "price": float(row["price"]),
                        "value": float(row["value"]),
                    }
                    for _, row in buys.iterrows()
                ],
            }
    markers = [
        {
            "time": date,
            "position": "aboveBar",
            "color": "#FFD700",
            "shape": "circle",
            "text": "RB",
        }
        for date in rebalance_events.keys()
    ]
    chart_data_json = json.dumps(chart_data)
    markers_json = json.dumps(markers)
    events_json = json.dumps(rebalance_events)
    comparison_series_json = json.dumps(filtered_comparison_series)
    comparison_colors_json = json.dumps(load_compare_colors())
    main_series_title = APP_NAME
    html = f"""
    <div id="chart-container" style="
    position:relative;
    width:100%;
    height:650px;
    background:#0a0d0a;
    border:1px solid rgba(123,255,92,0.22);
    border-radius:18px;
    overflow:hidden;
    box-shadow:0 0 24px rgba(123,255,92,0.10);
    ">
        <style>
        #tv-attr-logo {{
            display: none !important;
        }}
        </style>
        <div id="chart" style="width:100%; height:100%;"></div>
        <div id="tooltip" style="
            display:none;
            position:absolute;
            z-index:20;
            background:rgba(10,13,10,0.96);
            color:#eaffea;
            border:1px solid rgba(123,255,92,0.55);
            border-radius:12px;
            padding:12px 14px;
            font-family:Arial, sans-serif;
            font-size:12px;
            box-shadow:0 0 24px rgba(123,255,92,0.25);
            max-width:380px;
            pointer-events:none;
            white-space:normal;
        "></div>
        <div id="measure-box" style="
            display:none;
            position:absolute;
            z-index:30;
            background:rgba(10,13,10,0.96);
            color:#eaffea;
            border:1px solid rgba(123,255,92,0.55);
            border-radius:14px;
            padding:14px 16px;
            font-family:Arial, sans-serif;
            font-size:12px;
            box-shadow:0 0 26px rgba(123,255,92,0.28);
            min-width:260px;
            pointer-events:none;
        "></div>
    </div>
    <script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
    <script>
    const chartData = {chart_data_json};
    const markers = {markers_json};
    const rebalanceEvents = {events_json};
    const comparisonSeries = {comparison_series_json};
    const comparisonColors = {comparison_colors_json};
    const hasComparisons = Object.keys(comparisonSeries).length > 0;
    const container = document.getElementById("chart");
    const tooltip = document.getElementById("tooltip");
    const measureBox = document.getElementById("measure-box");
    let isMeasuring = false;
    let measureStart = null;
    let measureLine = null;
    let activeMeasureData = chartData;
    let activeMeasureTitle = "{APP_NAME}";
    let activeMeasureColor = "#B26CFF";
    const chart = LightweightCharts.createChart(container, {{
        width: container.clientWidth,
        height: 650,
        layout: {{
            background: {{ color: "#0a0d0a" }},
            textColor: "#E8F5E9",
        }},
        grid: {{
            vertLines: {{ color: "rgba(255,255,255,0.06)" }},
            horzLines: {{ color: "rgba(255,255,255,0.06)" }},
        }},
        rightPriceScale: {{
            borderColor: "rgba(123,255,92,0.25)",
        }},
        timeScale: {{
            borderColor: "rgba(123,255,92,0.25)",
            timeVisible: true,
            secondsVisible: false,
        }},
        crosshair: {{
            mode: LightweightCharts.CrosshairMode.Normal,
        }},
    }});
    const lineSeries = chart.addLineSeries({{
        color: "#B26CFF",
        lineWidth: 3,
        priceLineVisible: true,
        lastValueVisible: true,
        title: "{main_series_title}",
        priceFormat: {{
            type: "custom",
            formatter: price => hasComparisons ? price.toFixed(2) + "%" : price.toFixed(2),
        }},
    }});
    lineSeries.setData(chartData);
    lineSeries.setMarkers(markers);
    const seriesRegistry = new Map();
    seriesRegistry.set(lineSeries, {{
        title: "{APP_NAME}",
        data: chartData,
        color: "#B26CFF",
    }});
    function getActiveSeriesByMouse(param) {{
        if (!param || !param.point || !param.time || !param.seriesData) return null;
        let best = null;
        let bestDistance = Number.MAX_SAFE_INTEGER;
        for (const [series, valueData] of param.seriesData.entries()) {{
            if (!seriesRegistry.has(series)) continue;
            const value = valueData.value;
            const y = series.priceToCoordinate(value);
            if (y === null) continue;
            const distance = Math.abs(param.point.y - y);
            if (distance < bestDistance) {{
                bestDistance = distance;
                best = seriesRegistry.get(series);
            }}
        }}
        if (bestDistance > 18) return null;
        return best;
    }}
    Object.entries(comparisonSeries).forEach(([ticker, seriesData], index) => {{
        const compareLine = chart.addLineSeries({{
            color: comparisonColors[ticker] || "#FFFFFF",
            lineWidth: 2,
            priceLineVisible: false,
            lastValueVisible: true,
            title: ticker,
            priceFormat: {{type: "custom", formatter: price => price.toFixed(2) + "%", }},
        }});
        compareLine.setData(seriesData);
        seriesRegistry.set(compareLine, {{
            title: ticker,
            data: seriesData,
            color: comparisonColors[ticker] || "#FFFFFF",
        }});
    }});
    chart.timeScale().fitContent();
    measureLine = chart.addLineSeries({{
        color: "#7BFF5C",
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
    }});
    function money(value) {{
        return "$" + Number(value).toLocaleString(undefined, {{
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }});
    }}
    function qty(value) {{
        return Number(value).toLocaleString(undefined, {{
            minimumFractionDigits: 4,
            maximumFractionDigits: 4
        }});
    }}
    function buildTradeRows(title, rows, color) {{
        if (!rows || rows.length === 0) return "";
        let html = `<div style="margin-top:8px; color:${{color}}; font-weight:800;">${{title}}</div>`;
        rows.forEach(row => {{
            html += `
                <div style="display:grid; grid-template-columns:52px 1fr; gap:8px; margin-top:4px;">
                    <div style="font-weight:800;">${{row.ticker}}</div>
                    <div>
                        ${{qty(row.quantity)}} @ ${{money(row.price)}} = <b>${{money(row.value)}}</b>
                    </div>
                </div>
            `;
        }});
        return html;
    }}
    chart.subscribeCrosshairMove(param => {{
        if (!param || !param.time || !param.point) {{
            tooltip.style.display = "none";
            return;
        }}
        const activeSeries = getActiveSeriesByMouse(param);
        if (activeSeries) {{
            activeMeasureData = activeSeries.data;
            activeMeasureTitle = activeSeries.title;
            activeMeasureColor = activeSeries.color;
        }}
        if (!activeSeries || activeSeries.title !== "{APP_NAME}") {{
            tooltip.style.display = "none";
            return;
        }}
        const event = rebalanceEvents[param.time];
        if (!event) {{
            tooltip.style.display = "none";
            return;
        }}
        tooltip.innerHTML = `
            <div style="font-size:14px; font-weight:900; color:#FFD700;">Rebalance Event</div>
            <div style="margin-top:4px;"><b>Date:</b> ${{event.date}} | <b>Month:</b> ${{event.month}}</div>
            <div style="margin-top:6px; color:#9ccc8c;">Sold: ${{money(event.sold_total)}} | Bought: ${{money(event.bought_total)}}</div>
            ${{buildTradeRows("Sold", event.sells, "#FF6B6B")}}
            ${{buildTradeRows("Bought", event.buys, "#7BFF5C")}}
        `;
        let left = param.point.x + 20;
        let top = param.point.y + 20;
        if (left + 380 > container.clientWidth) left = param.point.x - 400;
        if (top + 280 > 650) top = param.point.y - 300;
        tooltip.style.left = left + "px";
        tooltip.style.top = top + "px";
        tooltip.style.display = "block";
    }});
    function getNearestDataPoint(time, sourceData) {{
        if (!time || !sourceData) return null;
        let closest = null;
        let bestDiff = Number.MAX_SAFE_INTEGER;
        sourceData.forEach(point => {{
            const diff = Math.abs(new Date(point.time) - new Date(time));
            if (diff < bestDiff) {{
                bestDiff = diff;
                closest = point;
            }}
        }});
        return closest;
    }}
    function clearMeasurement() {{
        measureLine.setData([]);
        measureBox.style.display = "none";
    }}
    function disableChartDrag() {{
        chart.applyOptions({{
            handleScroll: {{
                mouseWheel: false,
                pressedMouseMove: false,
                horzTouchDrag: false,
                vertTouchDrag: false,
            }},
            handleScale: {{
                axisPressedMouseMove: false,
                mouseWheel: false,
                pinch: false,
            }},
        }});
    }}
    function enableChartDrag() {{
        chart.applyOptions({{
            handleScroll: {{
                mouseWheel: true,
                pressedMouseMove: true,
                horzTouchDrag: true,
                vertTouchDrag: true,
            }},
            handleScale: {{
                axisPressedMouseMove: true,
                mouseWheel: true,
                pinch: true,
            }},
        }});
    }}
    document.addEventListener("keydown", event => {{
        if (event.key === "Escape") {{
            clearMeasurement();
            isMeasuring = false;
            measureStart = null;
            enableChartDrag();
        }}
    }});
    document.addEventListener("mouseup", event => {{
        if (!isMeasuring) return;
        event.preventDefault();
        event.stopPropagation();
        isMeasuring = false;
        measureStart = null;
        enableChartDrag();
    }});
    document.addEventListener("blur", () => {{
        if (!isMeasuring) return;
        isMeasuring = false;
        measureStart = null;
        enableChartDrag();
    }});
    container.addEventListener("mousedown", event => {{
        if (!event.shiftKey) return;
        event.preventDefault();
        event.stopPropagation();
        const rect = container.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const time = chart.timeScale().coordinateToTime(x);
        measureStart = getNearestDataPoint(time, activeMeasureData);
        if (!measureStart) return;
        isMeasuring = true;
        disableChartDrag();
        clearMeasurement();
    }});
    container.addEventListener("mousemove", event => {{
        if (!isMeasuring || !measureStart) return;
        event.preventDefault();
        event.stopPropagation();
        const rect = container.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const time = chart.timeScale().coordinateToTime(x);
        const measureEnd = getNearestDataPoint(time, activeMeasureData);
        if (!measureEnd) return;
        const linePoints = [
            {{
                time: measureStart.time,
                value: measureStart.value
            }},
            {{
                time: measureEnd.time,
                value: measureEnd.value
            }}
        ].sort((a, b) => new Date(a.time) - new Date(b.time));
        let pct;
        let simulatedEnd;
        if (hasComparisons) {{
            pct = measureEnd.value - measureStart.value;
            simulatedEnd = 100000 * (1 + pct / 100);
        }} else {{
            pct = ((measureEnd.value - measureStart.value) / measureStart.value) * 100;
            simulatedEnd = 100000 * (measureEnd.value / measureStart.value);
        }}
        const days = Math.round((new Date(measureEnd.time) - new Date(measureStart.time)) / 86400000);
        const boxColor = pct >= 0 ? "#7BFF5C" : "#FF4D4D";
        const pctSign = pct >= 0 ? "+" : "";
        measureLine.applyOptions({{color: boxColor,}});
        measureLine.setData(linePoints);
        measureBox.innerHTML = `
            <div style="font-size:14px;font-weight:900;color:${{boxColor}};">
                ${{activeMeasureTitle}} Range
            </div>
            <div style="font-size:26px;font-weight:900;color:${{boxColor}};">
                ${{pctSign}}${{pct.toFixed(2)}}%
            </div>
            <div style="margin-top:4px;">
                ${{measureStart.time}} → ${{measureEnd.time}}
            </div>
            <div style="margin-top:4px;">
                ${{measureStart.value.toFixed(2)}} → ${{measureEnd.value.toFixed(2)}}
            </div>
            <div style="margin-top:4px;">
                ${{Math.abs(days)}} Days
            </div>
            <div style="margin-top:4px; color:#9ccc8c;">
                $100,000 → ${{money(simulatedEnd)}}
            </div>
        `;
        let left = x + 20;
        let top = y + 20;
        if (left + 300 > container.clientWidth) {{
            left = x - 320;
        }}
        if (top + 210 > 650) {{
            top = y - 230;
        }}
        measureBox.style.left = left + "px";
        measureBox.style.top = top + "px";
        measureBox.style.borderColor = boxColor;
        measureBox.style.display = "block";
    }});
    window.addEventListener("resize", () => {{
        chart.applyOptions({{ width: container.clientWidth }});
    }});
    </script>
    """
    components.html(html, height=680)

def render_etf_home_page():
    etfs = load_etfs()
    background_base64 = image_to_base64(MAIN_PAGE_BACKGROUND)
    youtube_icon_base64 = image_to_base64(YOUTUBE_ICON)
    mail_icon_base64 = image_to_base64(MAIL_ICON)
    if background_base64:
        st.markdown(
            f"""
            <div style="
                background-image: linear-gradient(rgba(0,0,0,0.15), rgba(0,0,0,0.35)), url('data:image/png;base64,{background_base64}');
                background-size: contain;
                background-repeat: no-repeat;
                background-color: #050805;
                background-position: top center;
                min-height: 600px;
                border-radius: 24px;
                border: 1px solid rgba(123,255,92,0.25);
                box-shadow: 0 0 40px rgba(123,255,92,0.15);
                margin-bottom: 24px;
            ">
            </div>
            """,
            unsafe_allow_html=True,
        )
    col_youtube, col_feedback = st.columns(2)
    with col_youtube:
        st.markdown(
        f"""
        <a href="{YOUTUBE_URL}" target="_blank" class="home-action-btn youtube-btn">
            <img src="data:image/png;base64,{youtube_icon_base64}" class="btn-icon-img">
            <span>YouTube Channel</span>
        </a>
        """,
        unsafe_allow_html=True,
    )
    with col_feedback:
        st.markdown(
        f"""
        <a href="mailto:lior.shmila@gmail.com?subject=Feedback%20on%20MM%20ETFs%20page"
           class="home-action-btn feedback-btn">
            <img src="data:image/png;base64,{mail_icon_base64}" class="btn-icon-img">
            <span>Send Feedback</span>
        </a>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("## Our ETFs")
    if not etfs:
        st.error("No ETFs found.")
        st.stop()
    cols = st.columns(2, gap="large")
    for index, etf in enumerate(etfs):
        is_coming_soon = etf.get("status") == "coming_soon"
        summary = calculate_etf_summary(etf)
        col = cols[index % 2]
        with col:
            return_color = "#7BFF5C"
            drawdown_color = "#FF4D4D"
            if is_coming_soon:
                portfolio_value_text = "—"
                return_text = "—"
                drawdown_text = "—"
                updated_text = "Launching Soon"
            elif summary:
                portfolio_value_text = f"${summary['latest_value']:,.2f}"
                return_text = f"{summary['return_pct']:+.2f}%"
                drawdown_text = f"{summary['max_drawdown']:.2f}%"
                updated_text = f"Updated: {summary['last_date']}"
            else:
                portfolio_value_text = "Coming"
                return_text = "Soon"
                drawdown_text = "—"
                updated_text = "Portfolio data not initialized yet"
            st.markdown(
                f"""
                <div class="etf-card">
                    <div style="font-size:2.0rem; font-weight:900; color:#eaffea;">
                        {etf['name']}
                    </div>
                    <div style="font-size:1.05rem; color:#7BFF5C; font-weight:800;">
                        {etf['full_name']}
                    </div>
                    <div style="font-size:0.95rem; color:#b8d8b8; margin-top:10px; min-height:48px;">
                        {etf['description']}
                    </div>
                    <hr style="border-color:rgba(123,255,92,0.18);">
                    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px;">
                        <div>
                            <div style="color:#9ccc8c; font-size:0.85rem;">Portfolio</div>
                            <div style="font-size:1.2rem; font-weight:900;">{portfolio_value_text}</div>
                        </div>
                        <div>
                            <div style="color:#9ccc8c; font-size:0.85rem;">YTD Return</div>
                            <div style="font-size:1.2rem; font-weight:900; color:{return_color};">{return_text}</div>
                        </div>
                        <div>
                            <div style="color:#9ccc8c; font-size:0.85rem;">Max DD</div>
                            <div style="font-size:1.2rem; font-weight:900; color:{drawdown_color};">{drawdown_text}</div>
                        </div>
                    </div>
                    <div style="color:#9ccc8c; font-size:0.82rem; margin-top:10px;">
                        {updated_text}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div class="open-etf-button-marker"></div>', unsafe_allow_html=True)
            button_text = (
                "⏳ Coming Soon..."
                if is_coming_soon
                else f"🚀 Open {etf['name']}"
            )
            if st.button(
                button_text,
                key=f"open_{etf['id']}",
                use_container_width=True,
            ):
                if not is_coming_soon:
                    st.session_state["selected_etf"] = etf["id"]
                    st.rerun()

if "selected_etf" not in st.session_state:
    st.session_state["selected_etf"] = None
if st.session_state["selected_etf"] is None:
    render_etf_home_page()
    st.stop()
available_etfs = load_etfs()
selected_etf = next(
    (etf for etf in available_etfs if etf["id"] == st.session_state["selected_etf"]),
    None,
)
if selected_etf is None:
    st.error("Selected ETF was not found.")
    st.stop()
if st.button("← Back to ETF Home"):
    st.session_state["selected_etf"] = None
    st.rerun()
APP_NAME = selected_etf["name"]
APP_SUBTITLE = selected_etf["full_name"]
PORTFOLIO_CSV = selected_etf["portfolio_path"]
DB_NAME = selected_etf["db_path"]
TOTAL_CAPITAL = selected_etf.get("initial_capital", 100000)
DRIFT_THRESHOLD = selected_etf.get("drift_threshold", 0.02)

# ---------- Load Portfolio ----------
portfolio_df = pd.read_csv(PORTFOLIO_CSV)
portfolio_df["Ticker"] = portfolio_df["Ticker"].astype(str).str.upper().str.strip()
portfolio_df["Weight"] = pd.to_numeric(portfolio_df["Weight"], errors="coerce")
portfolio_df = portfolio_df.dropna(subset=["Ticker", "Weight"]).copy()
raw_weight_sum = portfolio_df["Weight"].sum()
if raw_weight_sum == 0:
    st.error("Portfolio weights sum to zero. Please check portfolio.csv.")
    st.stop()
portfolio_df["Normalized Weight"] = portfolio_df["Weight"] / raw_weight_sum
tickers = portfolio_df["Ticker"].tolist()
if not tickers:
    st.error("No tickers found in portfolio.csv.")
    st.stop()
# ---------- Load Prices from SQLite ----------
conn = sqlite3.connect(DB_NAME)
query = f"""
SELECT date, ticker, close_price
FROM price_history
WHERE ticker IN ({','.join(['?'] * len(tickers))})
ORDER BY date
"""
df = pd.read_sql_query(query, conn, params=tickers)
conn.close()
if df.empty:
    st.error("No price data found in price_history table.")
    st.stop()
close_prices = df.pivot(index="date", columns="ticker", values="close_price")
close_prices.index = pd.to_datetime(close_prices.index)
close_prices = close_prices.sort_index()
missing_tickers = [ticker for ticker in tickers if ticker not in close_prices.columns]
if missing_tickers:
    st.error("Missing price data for: " + ", ".join(missing_tickers))
    st.stop()
close_prices = close_prices[tickers]
close_prices = close_prices.dropna()
if close_prices.empty:
    st.error("Price data exists, but there are no complete rows for all tickers.")
    st.stop()
# ---------- Calculations ----------
# ---------- Portfolio Simulation with Rebalance Log ----------
first_prices = close_prices.iloc[0]
last_prices = close_prices.iloc[-1]
# Initial quantities based on target weights at the first available price date
quantities = {}
for _, row in portfolio_df.iterrows():
    ticker = row["Ticker"]
    weight = row["Normalized Weight"]
    investment = TOTAL_CAPITAL * weight
    quantities[ticker] = investment / first_prices[ticker]
# Load rebalance log from DB
conn = sqlite3.connect(DB_NAME)
rebalance_log_df = pd.read_sql_query(
    """
    SELECT date, ticker, action, quantity, price, value, month
    FROM rebalance_log
    ORDER BY date, action DESC, ticker
    """,
    conn,
)
conn.close()
if not rebalance_log_df.empty:
    rebalance_log_df["date"] = pd.to_datetime(rebalance_log_df["date"])
# Simulate portfolio value day by day, applying rebalance trades after close
portfolio_history_rows = []
for current_date in close_prices.index:
    prices = close_prices.loc[current_date]
    total_value = sum(
        quantities[ticker] * prices[ticker]
        for ticker in tickers
    )
    portfolio_history_rows.append(
        {
            "Date": current_date,
            "Total Value": total_value,
        }
    )
    if not rebalance_log_df.empty:
        trades_today = rebalance_log_df[rebalance_log_df["date"] == current_date]
        for _, trade in trades_today.iterrows():
            ticker = trade["ticker"]
            action = trade["action"]
            quantity = trade["quantity"]

            if action == "SELL":
                quantities[ticker] -= quantity
            elif action == "BUY":
                quantities[ticker] += quantity
portfolio_values = pd.DataFrame(portfolio_history_rows).set_index("Date")
portfolio_values["ETF Index"] = (
    portfolio_values["Total Value"] / portfolio_values["Total Value"].iloc[0] * 100
)
latest_value = portfolio_values["Total Value"].iloc[-1]
latest_index = portfolio_values["ETF Index"].iloc[-1]
return_pct = latest_index - 100
running_max = portfolio_values["ETF Index"].cummax()
drawdown = (portfolio_values["ETF Index"] / running_max - 1) * 100
max_drawdown = drawdown.min()

# ---------- Holdings Table ----------
holdings_rows = []
for _, row in portfolio_df.iterrows():
    ticker = row["Ticker"]
    target_weight = row["Normalized Weight"]
    current_value = quantities[ticker] * last_prices[ticker]
    holdings_rows.append(
        {
            "Ticker": ticker,
            "Original Weight %": row["Weight"],
            "Target Weight": target_weight,
            "Quantity": quantities[ticker],
            "Latest Price": last_prices[ticker],
            "Current Value": current_value,
        }
    )
holdings_df = pd.DataFrame(holdings_rows)
holdings_df["Actual Weight"] = holdings_df["Current Value"] / holdings_df["Current Value"].sum()
holdings_df["Drift"] = holdings_df["Actual Weight"] - holdings_df["Target Weight"]

# ---------- Rebalance Detection ----------
holdings_df["Needs Rebalance"] = holdings_df["Drift"].abs() > DRIFT_THRESHOLD
display_df = holdings_df.copy()
display_df["Original Weight %"] = display_df["Original Weight %"].map(lambda x: f"{x:.2f}%")
display_df["Target Weight"] = display_df["Target Weight"].map(lambda x: f"{x*100:.2f}%")
display_df["Actual Weight"] = holdings_df["Actual Weight"].map(lambda x: f"{x*100:.2f}%")
display_df["Drift"] = holdings_df["Drift"].map(lambda x: f"{x*100:+.2f}%")
display_df["Rebalance"] = holdings_df["Needs Rebalance"].map(lambda x: "YES" if x else "")
display_df["Quantity"] = display_df["Quantity"].map(lambda x: f"{x:,.4f}")
display_df["Latest Price"] = display_df["Latest Price"].map(lambda x: f"${x:,.2f}")
display_df["Current Value"] = display_df["Current Value"].map(lambda x: f"${x:,.2f}")
display_df = display_df[
    [
        "Ticker",
        "Target Weight",
        "Actual Weight",
        "Drift",
        "Rebalance",
        "Quantity",
        "Latest Price",
        "Current Value",
    ]
]

# ---------- Header ----------
left, right = st.columns([1, 4])
with left:
    if Path(LOGO_PATH).exists():
        st.image(LOGO_PATH, width="stretch")
with right:
    st.markdown(
        f"""
        <div class="brand-wrap">
            <div>
                <div class="brand-title">{APP_NAME}</div>
                <div class="brand-subtitle">{APP_SUBTITLE}</div>
                <div class="brand-link">
                    <a href="{YOUTUBE_URL}" target="_blank">YouTube Channel</a>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Metrics ----------
c1, c2, c3, c4 = st.columns(4)
roi_color = "#7BFF5C" if return_pct > 0 else "#FF4D4D" if return_pct < 0 else "#FFFFFF"
dd_color = "#FF4D4D" if max_drawdown < 0 else "#7BFF5C" if max_drawdown > 0 else "#FFFFFF"
with c1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Portfolio Value</div>
            <div class="metric-value">${latest_value:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">ETF Index</div>
            <div class="metric-value">{latest_index:.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">ROI from Jan-1st-2026</div>
            <div class="metric-value" style="color:{roi_color};">
                {return_pct:+.2f}%
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Max Drawdown</div>
            <div class="metric-value" style="color:{dd_color};">
                {max_drawdown:.2f}%
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Entry Date Return ----------
min_entry_date = portfolio_values.index.min().date()
max_entry_date = portfolio_values.index.max().date()
creation_date = pd.to_datetime(
    selected_etf.get("creation_date", min_entry_date)
).date()
default_entry_date = max(min_entry_date, min(creation_date, max_entry_date))
entry_col1, entry_col2 = st.columns([1, 3])
with entry_col1:
    selected_entry_date = st.date_input(
        "Entry date",
        value=default_entry_date,
        min_value=min_entry_date,
        max_value=max_entry_date,
    )
selected_entry_ts = pd.to_datetime(selected_entry_date)
available_dates = portfolio_values.index[portfolio_values.index >= selected_entry_ts]
if len(available_dates) == 0:
    effective_entry_date = portfolio_values.index[-1]
else:
    effective_entry_date = available_dates[0]
entry_value = portfolio_values.loc[effective_entry_date, "Total Value"]
entry_return_pct = (latest_value / entry_value - 1) * 100
return_color = "#7BFF5C" if entry_return_pct >= 0 else "#FF4D4D"
with entry_col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Return from selected entry date</div>
            <div class="metric-value" style="color:{return_color};">
                {entry_return_pct:+.2f}%
            </div>
            <div style="color:#9ccc8c; font-size:0.85rem;">
                Effective entry date: {effective_entry_date.date()}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
if abs(raw_weight_sum - 100) > 0.01:
    st.markdown(
        f"""
        <div style="
            color:#FF4D4D;
            font-weight:800;
            font-size:1rem;
            margin-top:10px;
            margin-bottom:10px;
        ">
            ⚠️ Warning: portfolio.csv weights sum to {raw_weight_sum:.2f}%.
            Weights are being normalized to 100%.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Chart ----------
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader(f"{APP_NAME} ETF Index")

# ---------- Compare --------
compare_assets = load_compare_assets()
selected_compare_tickers = []

for asset in compare_assets:
    ticker = asset["ticker"]
    if st.session_state.get(f"compare_{APP_NAME}_{ticker}", False):
        selected_compare_tickers.append(ticker)

comparison_series = load_compare_series(
    selected_compare_tickers,
    portfolio_values.index.min(),
    portfolio_values.index.max(),
)

render_tv_style_etf_chart(
    portfolio_values=portfolio_values,
    rebalance_log_df=rebalance_log_df,
    chart_title=f"{APP_NAME}_ETF_Index",
    comparison_series=comparison_series,
)

st.markdown("### Compare with")
compare_cols = st.columns([1, 1, 1, 6])
for index, asset in enumerate(compare_assets[:3]):
    ticker = asset["ticker"]
    name = asset["name"]
    with compare_cols[index]:
        st.checkbox(
            ticker,
            key=f"compare_{APP_NAME}_{ticker}",
            help=name,
        )

st.markdown("</div>", unsafe_allow_html=True)

# ---------- Table ----------
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Current Holdings")
st.dataframe(display_df, width="stretch", hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

# ---------- Rebalance History ----------
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Rebalance History")
st.markdown("</div>", unsafe_allow_html=True)
conn = sqlite3.connect(DB_NAME)
rebalance_history_df = pd.read_sql_query(
    """
    SELECT date, month, ticker, action, quantity, price, value, drift_before
    FROM rebalance_log
    ORDER BY date DESC, action DESC, ticker
    """,
    conn,
)
conn.close()
if rebalance_history_df.empty:
    st.info("No rebalance events found.")
else:
    rebalance_history_df["date"] = pd.to_datetime(rebalance_history_df["date"])
    months = sorted(rebalance_history_df["month"].unique(), reverse=True)
    for month in months:
        month_df = rebalance_history_df[rebalance_history_df["month"] == month].copy()
        event_date = month_df["date"].max().date()
        total_sold = month_df.loc[month_df["action"] == "SELL", "value"].sum()
        total_bought = month_df.loc[month_df["action"] == "BUY", "value"].sum()
        with st.expander(
            f"{month} | Date: {event_date} | Sold ${total_sold:,.2f} | Bought ${total_bought:,.2f}",
            expanded=False,
        ):
            display_log = month_df[
                ["date", "action", "ticker", "quantity", "price", "value", "drift_before"]
            ].copy()
            display_log["date"] = display_log["date"].dt.date
            display_log["quantity"] = display_log["quantity"].map(lambda x: f"{x:,.4f}")
            display_log["price"] = display_log["price"].map(lambda x: f"${x:,.2f}")
            display_log["value"] = display_log["value"].map(lambda x: f"${x:,.2f}")
            display_log["drift_before"] = display_log["drift_before"].map(lambda x: f"{x*100:+.2f}%")
            display_log = display_log.rename(
                columns={
                    "date": "Date",
                    "action": "Action",
                    "ticker": "Ticker",
                    "quantity": "Quantity",
                    "price": "Price",
                    "value": "Total",
                    "drift_before": "Drift Before",
                }
            )
            st.dataframe(display_log, width="stretch", hide_index=True)