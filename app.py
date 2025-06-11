import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Stock Breakout Scanner", layout="wide")

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
st.title("📈 Fundamentals + Breakout Stock Scanner")
st.sidebar.header("Scanner Settings")

input_method = st.sidebar.selectbox("Select Stock Universe", ["Manual Input", "Upload CSV"])

if input_method == "Manual Input":
    tickers_input = st.sidebar.text_area("Manual NSE Tickers (comma-separated)",
                                         value="TATAMOTORS.NS, INFY.NS")
    tickers = [x.strip() for x in tickers_input.split(",") if x.strip()]
else:
    uploaded_file = st.sidebar.file_uploader("Upload Screener.in Export CSV", type="csv")
    tickers = []
    if uploaded_file:
        try:
            df_csv = pd.read_csv(uploaded_file)
            tickers = df_csv.iloc[:, 0].astype(str).tolist()
        except Exception as e:
            st.error(f"CSV Upload Error: {e}")

start_date = st.sidebar.text_input("Start Date", value="2024/01/01")

if st.sidebar.button("Scan Stocks"):
    st.info("🔍 Scanning stocks...")
    results = []
    for sym in tickers:
        result = analyze_stock(sym)
        if result:
            results.append(result)

    if results:
        st.success(f"✅ {len(results)} breakout stock(s) found!")
        st.write(results)
    else:
        st.warning("No breakout stocks found. Try other tickers or adjust date.")

st.markdown("---")
st.caption("Built with 💹 Streamlit | For educational use only")
