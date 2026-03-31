import os
import streamlit as st
import joblib
from utils.ui import apply_ui

# Configuration
BASE_DIR = "/content/smart_city_app"
METRICS_PATH = f"{BASE_DIR}/model/metrics.pkl"

# Page Config
st.set_page_config(page_title="About Project | Smart City", page_icon="ℹ️", layout="wide")

# Apply custom CSS from your utils folder
apply_ui()

# Header Section
st.markdown('<div class="badge">Project Documentation</div>', unsafe_allow_html=True)
st.title("ℹ️ About the Smart City Traffic Project")
st.markdown('<p class="subtle-text">MSc Project: Traffic Hotspot Prediction & Decision Support System</p>', unsafe_allow_html=True)

# 1. Project Overview & Architecture
col_a, col_b = st.columns([2, 1])

with col_a:
    st.markdown("""
    <div class="info-card">
        <h3>Project Mission</h3>
        <p>This platform is designed to provide urban planners and citizens with real-time 
        insights into traffic congestion patterns. By leveraging Machine Learning (Random Forest) 
        and Spatial Clustering (DBSCAN), the system identifies high-risk 'hotspots' and provides 
        actionable interventions.</p>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown("### Technical Stack")
    st.info("**Frontend:** Streamlit Framework")
    st.success("**Engine:** Scikit-Learn (RF & DBSCAN)")
    st.warning("**Spatial:** Folium & GeoJSON")

# 2. Performance Metrics Section
st.divider()
st.subheader("📊 Model Performance Metrics")

if os.path.exists(METRICS_PATH):
    try:
        metrics = joblib.load(METRICS_PATH)
        
        # Metric Grid
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Accuracy Score", f"{metrics.get('accuracy', 0):.4f}")
        m2.metric("Weighted Precision", f"{metrics.get('precision_weighted', 0):.4f}")
        m3.metric("Weighted Recall", f"{metrics.get('recall_weighted', 0):.4f}")
        m4.metric("F1 Score", f"{metrics.get('f1_weighted', 0):.4f}")
        
        with st.expander("Detailed Classification Report"):
            report = metrics.get("classification_report", "No report available.")
            st.code(report)
            
    except Exception as e:
        st.error(f"Error loading metrics: {e}")
else:
    st.warning("⚠️ Metrics unavailable. Please run 'train_model.py' to generate performance data.")

# 3. Architecture & Future Scope
st.divider()
c1, c2 = st.columns(2)

with c1:
    st.markdown("### Core Modules")
    st.markdown("""
    * **Hotspot Map:** DBSCAN-based spatial clustering for zone-wise density analysis.
    * **Predictive Engine:** Random Forest Classifier for hotspot probability.
    * **Public Advisory:** Rule-based intervention engine for decision support.
    * **Risk Calculator:** Weighted logic combining weather, events, and congestion.
    """)

with c2:
    st.markdown("### Future Roadmap")
    st.markdown("""
    1.  **Real-time Integration:** Connecting to Google Maps/OpenStreetMap APIs.
    2.  **Ensemble Models:** Comparing XGBoost and LSTM for time-series forecasting.
    3.  **Advanced Routing:** Dijkstra-based route optimization avoiding predicted hotspots.
    4.  **Mobile Push:** SMS/Push notifications for high-risk alerts.
    """)

# Footer
st.markdown("---")
st.caption("© 2026 Smart City AI System | MSc Dissertation Project | Mumbai, India")
