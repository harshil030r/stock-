import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Stock Breakout + Fundamental Scanner", layout="wide")

# ------------------- Data Fetching -------------------
def fetch_price_data(symbol, start="2024-01-01"):
    try:
        df = yf.download(symbol, start=start)
        df = df["Close"].to_frame()
        df.rename(columns={"Close": "Close"}, inplace=True)
        return df
    except:
        return None

# ------------------- Technical Analysis -------------------
def analyze_stock(symbol):
    df = fetch_price_data(symbol)

    if df is None or len(df) < 200:
        return None

    # Calculate EMAs
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["EMA200"] = df["Close"].ewm(span=200).mean()

    required_cols = ["EMA20", "EMA50", "EMA200", "Close"]
    if not all(col in df.columns for col in required_cols):
        return None

    try:
        ema_ok = (
            df["Close"].iloc[-1] > df["EMA20"].iloc[-1] > df["EMA50"].iloc[-1] > df["EMA200"].iloc[-1]
        )
    except Exception as e:
        print(f"Error processing {symbol}: {e}")
        return None

    if ema_ok:
        return symbol

    return None

# ------------------- UI -------------------
st.title("📈 Fundamental + Breakout Stock Scanner")
st.sidebar.header("Scanner Settings")

input_method = st.sidebar.selectbox("Select Stock Universe", ["Manual Input", "Upload Screener CSV"])

tickers = []
dataframe_fundamentals = pd.DataFrame()

if input_method == "Manual Input":
    tickers_input = st.sidebar.text_area("Manual NSE Tickers (comma-separated)",
                                         value="TATAMOTORS.NS, INFY.NS")
    tickers = [x.strip() for x in tickers_input.split(",") if x.strip()]
else:
    uploaded_file = st.sidebar.file_uploader("Upload Screener.in Export CSV", type="csv")
    if uploaded_file:
        try:
            dataframe_fundamentals = pd.read_csv(uploaded_file)
            if 'Name' in dataframe_fundamentals.columns:
                tickers = dataframe_fundamentals['Name'].astype(str).apply(lambda x: x + ".NS").tolist()
        except Exception as e:
            st.error(f"CSV Upload Error: {e}")

start_date = st.sidebar.text_input("Start Date", value="2024/01/01")

if st.sidebar.button("Scan Stocks"):
    st.info("🔍 Scanning stocks...")
    results = []

    for i, sym in enumerate(tickers):
        if not sym.endswith(".NS"):
            sym += ".NS"

        # Fundamental filter check
        if not dataframe_fundamentals.empty:
            row = dataframe_fundamentals.iloc[i]
            try:
                roce = float(str(row.get("ROCE", 0)).replace("%", ""))
                eps = float(str(row.get("EPS last year", 0)))
                debt = float(str(row.get("Debt to equity", 0)))
                profit_growth = float(str(row.get("Profit growth", 0)).replace("%", ""))

                if roce < 15 or eps < 10 or debt > 1 or profit_growth < 10:
                    continue
            except:
                continue

        result = analyze_stock(sym)
        if result:
            results.append(result)

    if results:
        st.success(f"✅ {len(results)} fundamentally strong breakout stock(s) found!")
        st.write(results)
    else:
        st.warning("No matching stocks found. Try different filters or dates.")

st.markdown("---")
st.caption("Built with 💹 Streamlit | Educational use only")

