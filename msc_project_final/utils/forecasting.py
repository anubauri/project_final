import pandas as pd
import streamlit as st
import os

# Configuration
BASE_DIR = "/content/smart_city_app"
DATA_PATH = f"{BASE_DIR}/dataset/final_preprocessed_dataset.csv"

@st.cache_data(ttl=600) # Cache data for 10 minutes to improve performance
def forecast_congestion_by_day():
    """
    Processes historical traffic data to generate a rolling forecast and trend analysis.
    """
    # 1. File existence check to prevent FileNotFoundError
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame()

    try:
        # 2. Efficient Data Loading
        df = pd.read_csv(DATA_PATH)
        df.columns = [c.strip() for c in df.columns]

        # 3. Validation: Ensure required columns exist
        required_cols = ["date", "congestion_index"]
        if not all(col in df.columns for col in required_cols):
            return pd.DataFrame()

        # 4. Datetime Conversion with Error Handling
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        # 5. Aggregation
        # Convert congestion_index to numeric first to prevent mean() errors on strings
        df["congestion_index"] = pd.to_numeric(df["congestion_index"], errors="coerce")
        
        daily = df.groupby("date", as_index=False)["congestion_index"].mean()
        daily = daily.sort_values("date")

        # 6. Safety Check: Ensure we have enough data to forecast
        if daily.empty:
            return pd.DataFrame()

        # 7. Trend Generation (Moving Average)
        # Using a 3-day window to simulate a short-term forecast
        daily["forecast_like"] = daily["congestion_index"].rolling(window=3, min_periods=1).mean()
        
        # Calculate daily change (Trend Delta)
        daily["trend_delta"] = daily["forecast_like"].diff().fillna(0)

        # 8. Return last 30 data points for visualization
        return daily.tail(30).reset_index(drop=True)

    except Exception as e:
        # Log the error to the Streamlit console for the developer
        print(f"Forecasting Error: {e}")
        return pd.DataFrame()