import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from utils.predictor import load_dataset, run_dbscan_on_zones
from utils.locations import DEFAULT_CITY_CENTER
from utils.ui import apply_ui

# 1. Page Configuration
st.set_page_config(page_title="Hotspot Map | Smart City", page_icon="🗺️", layout="wide")
apply_ui()

# Header Section
st.markdown('<div class="badge">Spatial Intelligence</div>', unsafe_allow_html=True)
st.title("🗺️ Hotspot Map and DBSCAN Clusters")
st.markdown('<p class="subtle-text">Visualize zone-level traffic severity and density-based spatial clusters across Mumbai.</p>', unsafe_allow_html=True)

@st.cache_data(ttl=600)
def get_clustered_data(eps, min_samples):
    """Fetches and clusters data. Cached to prevent re-running on every UI interaction."""
    try:
        df = load_dataset()
        if df.empty:
            return pd.DataFrame()
        clustered = run_dbscan_on_zones(df, eps=eps, min_samples=min_samples)
        return clustered
    except Exception as e:
        st.error(f"Error processing spatial data: {e}")
        return pd.DataFrame()

# 2. Sidebar Controls
with st.sidebar:
    st.header("📍 Clustering Parameters")
    st.info("Adjust DBSCAN settings to change how traffic hotspots are grouped.")
    eps = st.slider("Epsilon (Distance Threshold)", min_value=0.1, max_value=5.0, value=1.15, step=0.05)
    min_samples = st.slider("Minimum Samples per Cluster", min_value=1, max_value=15, value=2, step=1)
    
    st.divider()
    st.markdown("""
    **Legend:**
    - <span style='color:red'>●</span> Cluster 0 (High Density)
    - <span style='color:blue'>●</span> Cluster 1
    - <span style='color:gray'>●</span> Noise (Isolated Zones)
    """, unsafe_allow_html=True)

# 3. Data Processing
clustered = get_clustered_data(eps, min_samples)

if clustered.empty:
    st.warning("⚠️ No spatial data available. Ensure your dataset contains valid zone names and coordinates.")
    st.stop()

# 4. KPI Metrics
c1, c2, c3, c4 = st.columns(4)
active_clusters = int(clustered["cluster"].nunique() - (1 if -1 in clustered["cluster"].unique() else 0))
noise_points = int((clustered["cluster"] == -1).sum())

c1.metric("Zones Mapped", len(clustered))
c2.metric("Active Clusters", active_clusters)
c3.metric("Noise/Isolated Zones", noise_points)
c4.metric("Avg Congestion", f"{clustered['congestion_index'].mean():.2f}%")

# 5. Map Generation
# Using 'cartodbpositron' for a clean, professional look
fmap = folium.Map(location=DEFAULT_CITY_CENTER, zoom_start=11, tiles="cartodbpositron")

def get_color(cluster_id):
    """Assigns specific colors to clusters."""
    palette = {
        -1: "#808080", # Gray for noise
        0: "#e63946",  # Red
        1: "#457b9d",  # Blue
        2: "#2a9d8f",  # Green
        3: "#9b5de5",  # Purple
        4: "#f15bb5",  # Pink
        5: "#fb5607"   # Orange
    }
    return palette.get(int(cluster_id), "#000000")

# Adding markers with safety check for coordinates
for _, row in clustered.iterrows():
    # Skip if coordinates are invalid
    if pd.isna(row["lat"]) or pd.isna(row["lon"]):
        continue
        
    # Scale radius based on congestion
    val = float(row.get("congestion_index", 0))
    radius = max(6, min(22, int(val / 5) + 5))
    
    popup_content = f"""
    <div style="font-family: sans-serif; min-width: 150px;">
        <h4 style="margin-bottom:5px;">{row['zone']}</h4>
        <b>Cluster ID:</b> {int(row['cluster'])}<br>
        <b>Congestion:</b> {val:.1f}%<br>
        <b>Hotspot Prob:</b> {row.get('hotspot_numeric', 0):.2f}
    </div>
    """
    
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=radius,
        popup=folium.Popup(popup_content, max_width=300),
        color=get_color(row["cluster"]),
        fill=True,
        fill_opacity=0.7,
        weight=1.5
    ).add_to(fmap)

# 6. Display Map & Table
st.markdown("### Interactive Geospatial Dashboard")
st_folium(fmap, width="100%", height=550, returned_objects=[])

with st.expander("📂 View Detailed Spatial Data Table"):
    display_df = clustered.copy()
    # Rounding for clean display
    cols_to_round = ["congestion_index", "actual_travel_time_min", "hotspot_numeric"]
    for col in cols_to_round:
        if col in display_df.columns:
            display_df[col] = display_df[col].astype(float).round(2)
            
    st.dataframe(display_df.sort_values("cluster"), use_container_width=True)