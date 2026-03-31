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
st.markdown('<p class="subtle-text">Deep-dive into traffic clusters, anomaly detection, and historical trends across Mumbai.</p>', unsafe_allow_html=True)

@st.cache_data(ttl=300) # Cache for 5 minutes to maintain performance
def get_processed_data():
    """Load and process datasets with strict type-safety checks."""
    try:
        df = load_dataset()
        if df is None or df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
        # SANITIZATION: Ensure numeric columns are actually numeric to prevent Plotly crashes
        numeric_cols = ["congestion_index", "actual_travel_time_min", "avg_speed_kmph", "distance_km"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        # Run spatial clustering and anomaly detection utilities
        clustered = run_dbscan_on_zones(df)
        anomaly_df = detect_anomalies(df)
        
        return df, clustered, anomaly_df
    except Exception as e:
        st.error(f"Data Processing Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Load data
df, clustered, anomaly_df = get_processed_data()

if df.empty:
    st.warning("⚠️ No data available. Ensure 'dataset/final_preprocessed_dataset.csv' is present and contains traffic records.")
    st.stop()

# 2. KPI Calculations
avg_cong = round(df["congestion_index"].mean(), 1)
avg_tt = round(df["actual_travel_time_min"].mean(), 1)
total_records = len(df)
# Safe calculation for hotspot frequency
hotspot_col = "hotspot" if "hotspot" in df.columns else None
if hotspot_col:
    hotspot_rate = round(100 * df[hotspot_col].astype(str).str.lower().isin(["yes", "true", "1", "hotspot"]).mean(), 1)
else:
    hotspot_rate = 0.0

# 3. Layout: Tabs for cleaner UX
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Overview Trends", 
    "📍 Spatial Hotspots", 
    "🔮 Traffic Forecast", 
    "🚨 Anomaly Detection"
])

# --- TAB 1: OVERVIEW ---
with tab1:
    st.subheader("Executive Traffic Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Records", f"{total_records:,}")
    c2.metric("Avg Congestion", f"{avg_cong}%")
    c3.metric("Avg Travel Time", f"{avg_tt} min")
    c4.metric("Hotspot Frequency", f"{hotspot_rate}%")

    col_left, col_right = st.columns(2)

    with col_left:
        if "day_of_week" in df.columns:
            # Sort days logically rather than alphabetically
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            temp = df.groupby("day_of_week")["congestion_index"].mean().reindex(day_order).reset_index()
            temp = temp.dropna() 
            
            fig = px.bar(temp, x="day_of_week", y="congestion_index", 
                         title="Average Congestion by Day",
                         labels={"congestion_index": "Congestion (%)", "day_of_week": "Day"},
                         template="plotly_white",
                         color="congestion_index", color_continuous_scale="Blues")
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        if "time_of_day" in df.columns:
            # Sort time periods logically
            time_order = ["Early Morning", "Morning", "Late Morning", "Afternoon", "Evening", "Night", "Late Night"]
            temp_tt = df.groupby("time_of_day")["actual_travel_time_min"].mean().reindex(time_order).reset_index()
            temp_tt = temp_tt.dropna()
            
            fig_tt = px.line(temp_tt, x="time_of_day", y="actual_travel_time_min", 
                             markers=True, title="Travel Delay by Time Period",
                             labels={"actual_travel_time_min": "Minutes"},
                             template="plotly_white")
            st.plotly_chart(fig_tt, use_container_width=True)

# --- TAB 2: HOTSPOTS ---
with tab2:
    st.subheader("Spatial Intelligence & Density Analysis")
    col_h1, col_h2 = st.columns([2, 1])
    
    with col_h1:
        if "source" in df.columns:
            # Top 10 worst areas
            temp_zone = df.groupby("source")["congestion_index"].mean().sort_values(ascending=False).head(10).reset_index()
            fig_zone = px.bar(temp_zone, x="congestion_index", y="source", orientation='h',
                              title="Top 10 High-Congestion Zones",
                              color="congestion_index", color_continuous_scale="Reds",
                              template="plotly_white")
            # Invert y-axis so the highest is at the top
            fig_zone.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_zone, use_container_width=True)

    with col_h2:
        if not clustered.empty and "cluster" in clustered.columns:
            cluster_counts = clustered["cluster"].value_counts().reset_index()
            cluster_counts.columns = ["Cluster ID", "Zone Count"]
            # Map -1 to "Noise" for better readability
            cluster_counts["Cluster ID"] = cluster_counts["Cluster ID"].apply(lambda x: "Noise" if x == -1 else f"Cluster {x}")
            
            fig_pie = px.pie(cluster_counts, names="Cluster ID", values="Zone Count", 
                             hole=0.4, title="DBSCAN Density Distribution",
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

# --- TAB 3: FORECAST ---
with tab3:
    st.subheader("30-Day Rolling Congestion Forecast")
    st.info("💡 Forecast is generated using a simple moving average of historical date-stamped data.")
    
    forecast_df = forecast_congestion_by_day()
    
    if not forecast_df.empty:
        fig_forecast = px.line(
            forecast_df, x="date", y=["congestion_index", "forecast_like"],
            title="Congestion Trend vs. Predicted Forecast",
            labels={"value": "Index Score", "variable": "Data Type", "date": "Timeline"},
            color_discrete_map={"congestion_index": "#ced4da", "forecast_like": "#0d6efd"},
            template="plotly_white"
        )
        st.plotly_chart(fig_forecast, use_container_width=True)
    else:
        st.info("Insufficient historical date-stamped data to generate a forecast.")

# --- TAB 4: ANOMALIES ---
with tab4:
    st.subheader("Traffic Pattern Integrity (Isolation Forest)")
    
    if not anomaly_df.empty and "anomaly_flag" in anomaly_df.columns:
        col_a1, col_a2 = st.columns([1, 2])
        
        with col_a1:
            anom_counts = anomaly_df["anomaly_flag"].value_counts().reset_index()
            anom_counts.columns = ["Status", "Count"]
            fig_anom = px.bar(anom_counts, x="Status", y="Count", color="Status",
                              color_discrete_map={"Normal": "#198754", "Anomaly": "#dc3545"},
                              template="plotly_white")
            st.plotly_chart(fig_anom, use_container_width=True)

        with col_a2:
            st.markdown("#### High-Priority Anomalies")
            # Isolate the records the model found "weird"
            top_anoms = anomaly_df[anomaly_df["anomaly_flag"] == "Anomaly"].sort_values("anomaly_score").head(20)
            
            if not top_anoms.empty:
                # Clean table for display
                cols = ["source", "destination", "congestion_index", "actual_travel_time_min"]
                st.dataframe(top_anoms[cols], use_container_width=True, hide_index=True)
            else:
                st.success("✅ No unusual traffic patterns detected in the current dataset.")
