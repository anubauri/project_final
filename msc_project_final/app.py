import os
import streamlit as st
from utils.ui import apply_ui

# 1. Setup DYNAMIC Base Directory and Paths
# This finds the directory where app.py is located automatically
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define paths relative to the project root
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "final_preprocessed_dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model", "final_random_forest_model.pkl")
METRICS_PATH = os.path.join(BASE_DIR, "model", "metrics.pkl")

# 2. Page Configuration
st.set_page_config(
    page_title="Smart City Traffic Hotspot Prediction System",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS from your utils
try:
    apply_ui()
except Exception:
    # Fallback if utils/ui.py has issues during initial deployment
    st.warning("UI styles partially loaded.")

# 3. Helper Functions
def check_file_status(path):
    exists = os.path.exists(path)
    return "✅ Available" if exists else "❌ Missing"

# Ensure directories exist (Crucial for Streamlit Cloud file writing)
for folder in ["dataset", "model", "output_reports"]:
    os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)

# 4. Header Section
st.markdown("<div class='badge'>System Portal</div>", unsafe_allow_html=True)
st.title("🚦 Smart City Traffic Hotspot Prediction System")
st.markdown("""
<p class='subtle-text'>
An integrated MSc research framework for predicting traffic hotspot risk, estimating travel delays, 
and evaluating smart-city interventions using Machine Learning and Geospatial Analytics.
</p>
""", unsafe_allow_html=True)

# 5. System Status Cards
st.markdown("### 🛠 System Environment Status")
c1, c2, c3 = st.columns(3)
c1.metric("Dataset File", check_file_status(DATASET_PATH))
c2.metric("ML Model", check_file_status(MODEL_PATH))
c3.metric("Performance Metrics", check_file_status(METRICS_PATH))

st.markdown("---")

# 6. Module Navigation Guide
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("## 🧩 Core Modules")
    st.markdown("""
    * **📍 Hotspot Map**: Interactive geospatial visualization using Folium and DBSCAN clustering.
    * **🚘 Predict Route**: Route-specific risk analysis using Random Forest with PDF report generation.
    * **📊 Admin Analytics**: Deep-dive dashboards for anomaly detection and congestion forecasting.
    * **📢 Public Advisory**: A real-time simulator for testing "What-If" traffic intervention scenarios.
    * **ℹ️ About**: Project architecture, model methodology, and future research scope.
    """)

with col_right:
    st.markdown("## 🚀 Quick Start")
    if not os.path.exists(MODEL_PATH):
        st.error("⚠️ **Model Not Found!**")
        st.markdown(f"""
        The system cannot find the model at: 
        `{MODEL_PATH}`
        
        Please ensure you have uploaded the `.pkl` files to the `model/` folder in your GitHub repository.
        """)
    else:
        st.success("✨ **System Ready!** \nUse the sidebar to navigate through the modules.")

# 7. Operational Information
st.markdown("### 💻 Deployment Info")
st.info(f"**Root Directory:** `{BASE_DIR}`")

st.markdown("---")
st.caption("MSc Project - Smart City Infrastructure & Data Science Framework © 2026")
