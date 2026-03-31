import pandas as pd
import streamlit as st
import os

# --- DYNAMIC CONFIGURATION ---
# This looks at where forecasting.py is, then goes up one level to the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "dataset", "final_preprocessed_dataset.csv")

@st.cache_data(ttl=600) # Cache for 10 minutes
def forecast_congestion_by_day():
    """
    Processes historical traffic data to generate a rolling forecast and trend analysis.
    Works seamlessly on Windows (local) and Linux (Streamlit Cloud).
    """
    # 1. Check if dataset exists before proceeding
    if not os.path.exists(DATA_PATH):
        # We don't print to console here as it won't show on Streamlit UI
        return pd.DataFrame()

    try:
        # 2. Efficient Data Loading
        df = pd.read_csv(DATA_PATH)
        # Clean column names (removes hidden spaces from CSV headers)
        df.columns = [c.strip() for c in df.columns]

        # 3. Validation: Check for required columns
        required_cols = ["date", "congestion_index"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"Dataset missing required columns: {required_cols}")
            return pd.DataFrame()

        # 4. Datetime Conversion
        # Streamlit Cloud handles datetime objects best for charting
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        # 5. Data Cleaning & Aggregation
        # Ensure congestion_index is numeric to avoid math errors
        df["congestion_index"] = pd.to_numeric(df["congestion_index"], errors="coerce").fillna(0)
        
        # Aggregate by date to get daily average congestion levels
        daily = df.groupby("date", as_index=False)["congestion_index"].mean()
        daily = daily.sort_values("date")

        # 6. Safety Check
        if daily.empty:
            return pd.DataFrame()

        # 7. Trend Generation (Moving Average)
        # 7-day window is standard for identifying weekly traffic patterns
        daily["forecast_like"] = daily["congestion_index"].rolling(window=7, min_periods=1).mean()
        
        # Calculate daily change (Trend Delta) to show if congestion is increasing
        daily["trend_delta"] = daily["forecast_like"].diff().fillna(0)

        # 8. Final Output
        # Returning the last 30 days provides a clean 'One Month' dashboard view
        return daily.tail(30).reset_index(drop=True)

    except Exception as e:
        # This will show a small warning in the Streamlit app sidebar/bottom if something breaks
        st.warning(f"Forecasting Engine encountered an error: {e}")
        return pd.DataFrame()
