import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

@st.cache_data(ttl=60)  # Cache results for 1 minute to reduce API calls
def fetch_bybit_tickers():
    url = "https://api.bybit.com/v5/market/tickers?category=spot"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get("result", {}).get("list", [])
        return [{
            "symbol": item["symbol"],
            "last_price": float(item["lastPrice"]),
            "percent_change_24h": float(item["price24hPcnt"]) * 100  # Convert to %
        } for item in data]
    return []

@st.cache_data(ttl=600)  # Cache for 10 minutes
def fetch_listing_dates():
    url = "https://api.bybit.com/v5/market/instruments-info?category=spot"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get("result", {}).get("list", [])
        return {item["symbol"]: item.get("launchTime", None) for item in data}
    return {}

def convert_timestamp(timestamp):
    return datetime.utcfromtimestamp(int(timestamp) / 1000).strftime('%Y-%m-%d %H:%M:%S UTC') if timestamp else "N/A"

def main():
    st.title("Bybit 24H Change Filter with Listing Dates")

    # Filter settings
    filter_option = st.radio("Select Filter Range:", ["Custom Range", "100+% Change"])
    if filter_option == "Custom Range":
        min_change = st.slider("Minimum 24H % Change", min_value=-50.0, max_value=100.0, value=-5.0)
        max_change = st.slider("Maximum 24H % Change", min_value=-50.0, max_value=100.0, value=5.0)
    else:
        min_change, max_change = 100.0, float('inf')

    scan_interval = st.slider("Rescan Interval (minutes)", min_value=1, max_value=30, value=10, step=1)

    if st.button("Run Scan"):
        st.write("Fetching data...")
        tickers = fetch_bybit_tickers()
        listing_dates = fetch_listing_dates()

        if tickers:
            df = pd.DataFrame(tickers)
            df["listing_date"] = df["symbol"].map(lambda x: convert_timestamp(listing_dates.get(x, None)))

            # Apply filter
            filtered_df = df[df["percent_change_24h"] >= min_change]
            if max_change != float('inf'):
                filtered_df = filtered_df[filtered_df["percent_change_24h"] <= max_change]

            st.write(f"Showing {len(filtered_df)} results")
            st.dataframe(filtered_df)

        else:
            st.error("Failed to fetch data from Bybit.")

        st.toast(f"Next scan in {scan_interval} minutes")
        time.sleep(scan_interval * 60)
        st.experimental_rerun()  # Rerun the app to refresh data

if __name__ == "__main__":
    main()
