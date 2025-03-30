import streamlit as st
import pandas as pd
import numpy as np
import requests
import time

# Function to get Bybit crypto pairs
def get_bybit_pairs():
    url = "https://api.bybit.com/v5/market/instruments-info?category=spot"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"API Error: {response.status_code}")
            return []
        try:
            data = response.json()
            if "result" in data and "list" in data["result"]:
                return [s["symbol"] for s in data["result"]["list"]]
            else:
                st.error("Unexpected API response format.")
                return []
        except requests.exceptions.JSONDecodeError:
            st.error("Failed to parse JSON response from Bybit API.")
            st.text(response.text)  # Show raw response for debugging
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
        return []

# Function to detect reversal and continuation patterns, including flags
def detect_pattern(df):
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    
    pattern = "No Clear Pattern"
    tp1, tp2, tp3, sl = None, None, None, None
    
    # Reversal patterns
    if close.iloc[-1] > close.iloc[-2] and close.iloc[-2] < close.iloc[-3]:
        pattern = "Bullish Reversal"
        tp1, tp2, tp3 = close.iloc[-1] * 1.02, close.iloc[-1] * 1.04, close.iloc[-1] * 1.06
        sl = close.iloc[-1] * 0.98
    elif close.iloc[-1] < close.iloc[-2] and close.iloc[-2] > close.iloc[-3]:
        pattern = "Bearish Reversal"
        tp1, tp2, tp3 = close.iloc[-1] * 0.98, close.iloc[-1] * 0.96, close.iloc[-1] * 0.94
        sl = close.iloc[-1] * 1.02
    
    # Continuation patterns
    elif high.max() == high.iloc[-1] and low.min() == low.iloc[0]:
        pattern = "Triangle Pattern"
    elif close.iloc[-1] > np.mean(close[-5:]):
        pattern = "Continuation Uptrend"
    elif close.iloc[-1] < np.mean(close[-5:]):
        pattern = "Continuation Downtrend"
    
    # Flag patterns (checking for sharp move followed by consolidation)
    elif (close.iloc[-1] > close.iloc[-5] * 1.02) and (np.std(close[-5:]) < np.std(close[-10:-5])):
        pattern = "Bullish Flag"
        tp1, tp2, tp3 = close.iloc[-1] * 1.02, close.iloc[-1] * 1.04, close.iloc[-1] * 1.06
        sl = close.iloc[-1] * 0.98
    elif (close.iloc[-1] < close.iloc[-5] * 0.98) and (np.std(close[-5:]) < np.std(close[-10:-5])):
        pattern = "Bearish Flag"
        tp1, tp2, tp3 = close.iloc[-1] * 0.98, close.iloc[-1] * 0.96, close.iloc[-1] * 0.94
        sl = close.iloc[-1] * 1.02
    
    return pattern, df.iloc[-1]["timestamp"], tp1, tp2, tp3, sl

# Function to fetch and analyze market data
def scan_patterns(symbol, interval):
    try:
        url = f"https://api.bybit.com/v5/market/kline?category=spot&symbol={symbol}&interval={interval}"
        response = requests.get(url)
        if response.status_code != 200:
            return f"API Error: {response.status_code}"
        try:
            data = response.json()
            if "result" in data and "list" in data["result"]:
                columns = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
                raw_data = data["result"]["list"]
                filtered_data = [row[:len(columns)] for row in raw_data]  # Ensure correct column count
                df = pd.DataFrame(filtered_data, columns=columns)
                return detect_pattern(df)
            return "No Data"
        except requests.exceptions.JSONDecodeError:
            return "JSON Parse Error"
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"

# Streamlit UI
st.title("Crypto Pattern Scanner (Bybit v5)")
st.write("Scanning Bybit crypto pairs for emerging patterns...")

# Select timeframe
timeframes = {
    "1m": "1",
    "3m": "3",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "4h": "240",
    "1d": "1440",
}
selected_timeframe = st.selectbox("Select Timeframe", list(timeframes.keys()))

# Get Bybit pairs
pairs = get_bybit_pairs()
if not pairs:
    st.stop()  # Stop execution if no pairs are available

selected_pairs = st.multiselect("Select Crypto Pairs", pairs, default=pairs[:5])

if st.button("Scan Patterns"):
    if not selected_pairs:
        st.warning("Please select at least one trading pair.")
    else:
        results = []
        with st.spinner("Scanning..."):
            for pair in selected_pairs:
                pattern, timestamp, tp1, tp2, tp3, sl = scan_patterns(pair, timeframes[selected_timeframe])
                results.append({
                    "Pair": pair,
                    "Pattern": pattern,
                    "Timestamp": timestamp,
                    "TP1": tp1,
                    "TP2": tp2,
                    "TP3": tp3,
                    "Stop Loss": sl
                })
                time.sleep(1)  # Avoid API rate limits

        df = pd.DataFrame(results)
        st.dataframe(df)
