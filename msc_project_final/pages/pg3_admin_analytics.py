import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

from utils.predictor import load_dataset, run_dbscan_on_zones, detect_anomalies
from utils.forecasting import forecast_congestion_by_day
from utils.ui import apply_ui

# 1. Page Configuration
st.set_page_config(page_title="Admin Analytics | Smart City", page_icon="📊", layout="wide")
apply_ui()

# Header
st.markdown('<div class="badge">Administrative Suite</div>', unsafe_allow_html=True)
st.title("📊 Admin Analytics Dashboard")
st.markdown('<p class="subtle-text">Deep-dive into traffic clusters, anomaly detection, and historical trends.</p>', unsafe_allow_html=True)

@st.cache_data(ttl=300) # Cache for 5 minutes
def get_processed_data():
    """Load and process datasets with safety checks."""
    try:
        df = load_dataset()
        if df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
        # Ensure numeric columns are actually numeric to prevent chart crashes
        numeric_cols = ["congestion_index", "actual_travel_time_min", "avg_speed_kmph"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Run spatial clustering and anomaly detection
        clustered = run_dbscan_on_zones(df)
        anomaly_df = detect_anomalies(df)
        
        return df, clustered, anomaly_df
    except Exception as e:
        st.error(f"Data Processing Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Load data
df, clustered, anomaly_df = get_processed_data()

if df.empty:
    st.warning("⚠️ No data available. Please ensure the dataset exists and is formatted correctly.")
    st.stop()

# 2. KPI Calculations (Safe mean calculation)
avg_cong = round(df["congestion_index"].mean(), 2)
avg_tt = round(df["actual_travel_time_min"].mean(), 2)
total_routes = len(df)
hotspot_rate = round(
    100 * df["hotspot"].astype(str).str.lower().isin(["yes", "true", "1", "hotspot", "high"]).mean(), 
    2
) if "hotspot" in df.columns else 0

# 3. Layout: Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Overview Trends", 
    "📍 Spatial Hotspots", 
    "🔮 Traffic Forecast", 
    "🚨 Anomaly Detection"
])

# --- TAB 1: OVERVIEW ---
with tab1:
    st.markdown("### Executive Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Records", f"{total_routes:,}")
    c2.metric("Avg Congestion", f"{avg_cong}%")
    c3.metric("Avg Travel Time", f"{avg_tt} min")
    c4.metric("Hotspot Frequency", f"{hotspot_rate}%")

    col_left, col_right = st.columns(2)

    with col_left:
        if "day_of_week" in df.columns:
            # Sort days logically
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            temp = df.groupby("day_of_week")["congestion_index"].mean().reindex(day_order).reset_index()
            temp = temp.dropna() # Remove days not in dataset
            
            fig = px.bar(temp, x="day_of_week", y="congestion_index", 
                         title="Average Congestion by Day of Week",
                         labels={"congestion_index": "Congestion (%)", "day_of_week": "Day"},
                         color="congestion_index", color_continuous_scale="Blues")
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        if "time_of_day" in df.columns:
            # Sort time periods logically
            time_order = ["Early Morning", "Morning", "Late Morning", "Afternoon", "Evening", "Night", "Late Night"]
            temp_tt = df.groupby("time_of_day")["actual_travel_time_min"].mean().reindex(time_order).reset_index()
            temp_tt = temp_tt.dropna()
            
            fig_tt = px.line(temp_tt, x="time_of_day", y="actual_travel_time_min", 
                             markers=True, title="Travel Time Delay by Time Period",
                             labels={"actual_travel_time_min": "Minutes"})
            st.plotly_chart(fig_tt, use_container_width=True)

# --- TAB 2: HOTSPOTS ---
with tab2:
    st.markdown("### Spatial Intelligence & Cluster Analysis")
    
    col_h1, col_h2 = st.columns([2, 1])
    
    with col_h1:
        if "source" in df.columns:
            temp_zone = df.groupby("source")["congestion_index"].mean().sort_values(ascending=False).head(10).reset_index()
            fig_zone = px.bar(temp_zone, x="congestion_index", y="source", orientation='h',
                              title="Top 10 High-Congestion Zones",
                              color="congestion_index", color_continuous_scale="Reds")
            st.plotly_chart(fig_zone, use_container_width=True)

    with col_h2:
        if not clustered.empty and "cluster" in clustered.columns:
            cluster_counts = clustered["cluster"].value_counts().reset_index()
            cluster_counts.columns = ["Cluster ID", "Zone Count"]
            fig_pie = px.pie(cluster_counts, names="Cluster ID", values="Zone Count", 
                             hole=0.4, title="DBSCAN Zone Density")
            st.plotly_chart(fig_pie, use_container_width=True)

# --- TAB 3: FORECAST ---
with tab3:
    st.markdown("### Predictive Trend Forecasting")
    forecast_df = forecast_congestion_by_day()
    
    if not forecast_df.empty:
        # Prepare data for plotting
        fig_forecast = px.line(
            forecast_df, x="date", y=["congestion_index", "forecast_like"],
            title="30-Day Rolling Congestion Forecast",
            labels={"value": "Index", "variable": "Type", "date": "Timeline"},
            color_discrete_map={"congestion_index": "#adb5bd", "forecast_like": "#007bff"}
        )
        st.plotly_chart(fig_forecast, use_container_width=True)
        
        with st.expander("View Raw Forecast Calculations"):
            st.dataframe(forecast_df.sort_values("date", ascending=False), use_container_width=True)
    else:
        st.info("💡 Insufficient historical date data found to generate a time-series forecast.")

# --- TAB 4: ANOMALIES ---
with tab4:
    st.markdown("### Anomaly Detection (Unusual Traffic Patterns)")
    
    if not anomaly_df.empty:
        anom_counts = anomaly_df["anomaly_flag"].value_counts().reset_index()
        anom_counts.columns = ["Status", "Count"]
        
        fig_anom = px.bar(anom_counts, x="Status", y="Count", color="Status",
                          title="Traffic Pattern Integrity Check",
                          color_discrete_map={"Normal": "#28a745", "Anomaly": "#dc3545"})
        st.plotly_chart(fig_anom, use_container_width=True)

        st.markdown("#### Top 50 Anomalous Records (High Priority)")
        # Show specific details that explain the anomaly
        cols_to_show = ["source", "destination", "congestion_index", "actual_travel_time_min", "anomaly_score"]
        top_anoms = anomaly_df[anomaly_df["anomaly_flag"] == "Anomaly"].sort_values("anomaly_score").head(50)
        
        if not top_anoms.empty:
            st.dataframe(top_anoms[[c for c in cols_to_show if c in top_anoms.columns]], use_container_width=True)
        else:
            st.success("✅ No critical traffic anomalies detected.")
