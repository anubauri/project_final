import os
import streamlit as st
from utils.ui import apply_ui

# 1. Setup DYNAMIC Base Directory
# This ensures paths work on Local Windows, Google Colab, or Streamlit Cloud (Linux)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define paths relative to the project root
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "final_preprocessed_dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model", "final_random_forest_model.pkl")
METRICS_PATH = os.path.join(BASE_DIR, "model", "metrics.pkl")

# 2. Page Configuration
st.set_page_config(
    page_title="Smart City Traffic Hotspot Prediction",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS from your utils
try:
    apply_ui()
except Exception:
    st.warning("⚠️ UI styles partially loaded. Check 'utils/ui.py' for errors.")

# 3. Helper Functions
def check_file_status(path):
    """Returns a status string and boolean for file availability."""
    exists = os.path.exists(path)
    return "✅ Available" if exists else "❌ Missing", exists

# Ensure directories exist (Crucial for Streamlit Cloud to avoid 'Folder Not Found' errors)
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

# 5. System Status Dashboard
st.markdown("---")
st.subheader("🛠️ System Environment Health")

status_ds, ds_exists = check_file_status(DATASET_PATH)
status_ml, ml_exists = check_file_status(MODEL_PATH)
status_mt, mt_exists = check_file_status(METRICS_PATH)

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Dataset File", status_ds)
    if not ds_exists: st.error("Upload CSV to /dataset/")
with c2:
    st.metric("ML Model (RF)", status_ml)
    if not ml_exists: st.error("Upload .pkl to /model/")
with c3:
    st.metric("Model Metrics", status_mt)
    if not mt_exists: st.info("Run 'train_model.py' to generate.")

# 6. Module Navigation Guide
st.markdown("---")
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
    st.markdown("## 🚀 Getting Started")
    if ml_exists:
        st.success("✨ **System Ready!** \n\nAll model artifacts are loaded. Use the **Sidebar** to navigate between modules.")
        if st.button("Explore Hotspot Map"):
            st.info("👈 Please select 'Hotspot Map' from the sidebar menu.")
    else:
        st.error("⚠️ **Action Required!**")
        st.write("The system cannot find the trained model. Please ensure your GitHub repository contains the pre-trained `.pkl` files in the `model/` folder.")

# 7. Deployment Metadata
st.markdown("---")
with st.expander("💻 Technical Deployment Details"):
    st.code(f"""
    Platform: Streamlit Production
    Root Directory: {BASE_DIR}
    Python Environment: 3.10+
    Status: {'Operational' if ml_exists else 'Awaiting Model'}
    """, language="yaml")

st.caption("MSc Project - Smart City Infrastructure & Data Science Framework © 2026 | Mumbai, India")
