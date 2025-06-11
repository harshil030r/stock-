
import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import datetime

st.set_page_config(page_title="Breakout & Fundamental Stock Scanner", layout="wide")
st.title("📈 Ultimate Stock Breakout & Fundamentals Scanner")

st.sidebar.header("Scanner Settings")
universe = st.sidebar.multiselect("Select Stock Universe", ["NIFTY200", "SMALLCAP100", "Manual Input"], default=["Manual Input"])
manual = st.sidebar.text_area("Manual NSE Tickers (comma-separated)", value="TATAMOTORS.NS, INFY.NS")
start_date = st.sidebar.date_input("Start Date", datetime.date(2024,1,1))
fundamental_csv = st.sidebar.file_uploader("Upload Screener.in Export CSV", type="csv")

tickers = []
if "NIFTY200" in universe:
    df_nifty = pd.read_csv("nifty200.csv")
    tickers += [f + ".NS" for f in df_nifty["Symbol"].tolist()]
if "SMALLCAP100" in universe:
    df_small = pd.read_csv("smallcap100.csv")
    tickers += [f + ".NS" for f in df_small["Symbol"].tolist()]
if "Manual Input" in universe:
    tickers += [t.strip() for t in manual.split(",") if t.strip()]

tickers = sorted(set(tickers))

fund_df = None
if fundamental_csv:
    fund_df = pd.read_csv(fundamental_csv)
else:
    st.sidebar.warning("Upload Screener CSV to enable fundamentals filtering.")

min_roce = st.sidebar.slider("Min ROCE (%)", 0, 30, 15)

def meets_fundamentals(sym):
    if fund_df is None or sym not in fund_df["Symbol"].values:
        return False
    row = fund_df[fund_df["Symbol"]==sym].iloc[0]
    return row["ROCE"]>=min_roce and row["DebtToEquity"]<0.5

def analyze_stock(sym):
    df = yf.download(sym, start=start_date)
    if len(df)<60: return None
    df["EMA20"] = df["Close"].ewm(20).mean()
    df["EMA50"] = df["Close"].ewm(50).mean()
    df["EMA200"] = df["Close"].ewm(200).mean()
    df["High20max"] = df["High"].rolling(20).max()
    ema_ok = df["Close"].iloc[-1]>df["EMA20"].iloc[-1]>df["EMA50"].iloc[-1]>df["EMA200"].iloc[-1]
    near_high = df["Close"].iloc[-1] >= 0.95*df["High20max"].iloc[-1]
    pole = (df["Close"].pct_change(5).iloc[-6:-1] > 0.08).any()
    base = df["Close"].iloc[-7:-1].max()/df["Close"].iloc[-7:-1].min() < 1.05
    breakout = ema_ok and near_high and pole and base
    if breakout:
        return {
            "Ticker": sym, "Price": round(df["Close"].iloc[-1],2),
            "EMA20": round(df["EMA20"].iloc[-1],2),
            "EMA50": round(df["EMA50"].iloc[-1],2),
            "EMA200": round(df["EMA200"].iloc[-1],2),
            "Pole?": "✔" if pole else "✘", "Base?": "✔" if base else "✘"
        }
    return None

res = []
progress = st.progress(0)
total = len(tickers)
for i,sym in enumerate(tickers):
    if fund_df is not None and not meets_fundamentals(sym.replace(".NS","")):
        continue
    r = analyze_stock(sym)
    if r: res.append(r)
    progress.progress((i+1)/total)

if res:
    st.success(f"Found {len(res)} candidate stocks!")
    st.dataframe(pd.DataFrame(res))
else:
    st.warning("No stocks passed all filters—try adjusting settings.")
