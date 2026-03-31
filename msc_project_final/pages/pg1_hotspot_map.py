import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np

from utils.predictor import load_dataset, run_dbscan_on_zones
from utils.locations import DEFAULT_CITY_CENTER
from utils.ui import apply_ui

# 1. Page Configuration
st.set_page_config(page_title="Hotspot Map | Smart City", page_icon="🗺️", layout="wide")
apply_ui()

# Header Section
st.markdown('<div class="badge">Spatial Intelligence</div>', unsafe_allow_html=True)
st.title("🗺️ Hotspot Map & DBSCAN Clusters")
st.markdown('<p class="subtle-text">Visualize zone-level traffic severity and density-based spatial clusters across Mumbai.</p>', unsafe_allow_html=True)

@st.cache_data(ttl=600)
def get_clustered_data(eps, min_samples):
    """Fetches and clusters data. Cached to prevent re-running on every UI interaction."""
    try:
        df = load_dataset()
        if df is None or df.empty:
            return pd.DataFrame()
        
        # Perform DBSCAN clustering via predictor utility
        clustered = run_dbscan_on_zones(df, eps=eps, min_samples=min_samples)
        return clustered
    except Exception as e:
        st.error(f"Error processing spatial data: {e}")
        return pd.DataFrame()

# 2. Sidebar Controls
with st.sidebar:
    st.header("📍 Clustering Parameters")
    st.info("Adjust DBSCAN settings to change how traffic hotspots are grouped geographically.")
    
    # Epsilon: The maximum distance between two samples for one to be considered as in the neighborhood of the other.
    eps = st.slider("Epsilon (Distance Threshold)", min_value=0.05, max_value=3.0, value=1.15, step=0.05)
    
    # Min Samples: The number of samples in a neighborhood for a point to be considered as a core point.
    min_samples = st.slider("Min Samples per Cluster", min_value=1, max_value=10, value=2, step=1)
    
    st.divider()
    st.markdown("### 🎨 Map Legend")
    st.write("🔴 **Cluster 0+**: High-Density Zones")
    st.write("⚪ **Noise (-1)**: Isolated Traffic Zones")

# 3. Data Processing
clustered = get_clustered_data(eps, min_samples)

if clustered.empty:
    st.warning("⚠️ No spatial data available. Ensure 'dataset/final_preprocessed_dataset.csv' is present and contains valid 'source' and 'congestion_index' columns.")
    st.stop()

# 4. KPI Metrics
# Calculating metrics safely
unique_clusters = clustered["cluster"].unique()
active_clusters = int(len([c for c in unique_clusters if c != -1]))
noise_points = int((clustered["cluster"] == -1).sum())

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Zones", len(clustered))
with m2:
    st.metric("Active Clusters", active_clusters)
with m3:
    st.metric("Isolated Zones", noise_points)
with m4:
    avg_cong = clustered['congestion_index'].mean()
    st.metric("Avg Congestion", f"{avg_cong:.1f}%")

# 5. Map Generation
# Using 'cartodbpositron' for a clean, professional aesthetic
fmap = folium.Map(
    location=DEFAULT_CITY_CENTER, 
    zoom_start=11, 
    tiles="cartodbpositron",
    control_scale=True
)

def get_cluster_color(cluster_id):
    """Returns a hex color based on the cluster ID."""
    colors = {
        -1: "#95a5a6", # Gray for noise/outliers
        0: "#e74c3c",  # Red
        1: "#3498db",  # Blue
        2: "#2ecc71",  # Green
        3: "#f1c40f",  # Yellow
        4: "#9b59b6",  # Purple
        5: "#e67e22"   # Orange
    }
    # Return indexed color or a random dark color for high-index clusters
    return colors.get(int(cluster_id), "#2c3e50")

# Adding markers to the map
for _, row in clustered.iterrows():
    # Final safety check for NaN coordinates to prevent map breakdown
    if pd.isna(row["lat"]) or pd.isna(row["lon"]):
        continue
    
    # Calculate circle size based on congestion level
    cong_val = float(row.get("congestion_index", 0))
    radius_val = max(5, min(18, int(cong_val / 6) + 4))
    
    # Create an HTML popup for the marker
    popup_html = f"""
    <div style="font-family: 'Inter', sans-serif; font-size: 12px; width: 160px;">
        <strong style="color:#0f6cbd; font-size:14px;">{row['zone']}</strong><br><hr style="margin:5px 0;">
        <b>Cluster:</b> {int(row['cluster'])}<br>
        <b>Congestion:</b> {cong_val:.1f}%<br>
        <b>Hotspot Score:</b> {row.get('hotspot_numeric', 0):.2f}
    </div>
    """
    
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=radius_val,
        popup=folium.Popup(popup_html, max_width=200),
        color=get_cluster_color(row["cluster"]),
        fill=True,
        fill_opacity=0.7,
        weight=2
    ).add_to(fmap)

# 6. Display Dashboard
st.markdown("### 📍 Interactive Mumbai Spatial Analysis")
# Use st_folium with a unique key to prevent re-rendering loops
st_folium(fmap, width="100%", height=600, key="mumbai_map", returned_objects=[])

# 7. Data Table Section
with st.expander("📊 View Detailed Clustering Results"):
    st.write("This table shows the raw data used to generate the clusters above.")
    # Clean up dataframe for display
    display_df = clustered.drop(columns=['lat', 'lon'], errors='ignore').copy()
    display_df = display_df.rename(columns={
        "zone": "Area Name",
        "congestion_index": "Avg Congestion (%)",
        "hotspot_numeric": "Hotspot Probability",
        "cluster": "Cluster ID"
    })
    st.dataframe(
        display_df.sort_values("Cluster ID"), 
        use_container_width=True,
        hide_index=True
    )
