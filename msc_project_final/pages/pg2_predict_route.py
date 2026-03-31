import os
import streamlit as st
import pandas as pd
import time

from utils.locations import get_all_zones
from utils.predictor import full_prediction_payload, get_feature_importance
from utils.intervention import generate_advisory
from utils.pdf_report import generate_prediction_report
from utils.ui import apply_ui

# Configuration
BASE_DIR = "/content/smart_city_app"

# Page Config & UI
st.set_page_config(page_title="Predict Route | Smart City", page_icon="🚘", layout="wide")
apply_ui()

# Header Section
st.markdown("<div class='badge'>Smart Mobility</div>", unsafe_allow_html=True)
st.title("🚘 Route Prediction and Risk Assessment")
st.markdown("<p class='subtle-text'>Predict congestion risk, hotspot probability, and route-level advisory intelligence.</p>", unsafe_allow_html=True)

# 1. Input Data Loading
zones = get_all_zones()
weather_options = ["Clear", "Cloudy", "Rain", "Storm", "Fog"]
festival_options = ["No", "Yes"]
road_options = ["Highway", "Main Road", "Arterial", "Internal Road", "Mixed"]
time_options = ["Early Morning", "Morning", "Late Morning", "Afternoon", "Evening", "Night", "Late Night"]
day_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# 2. Prediction Form
with st.form("prediction_form"):
    c1, c2 = st.columns(2)
    source = c1.selectbox("Source Zone", zones, index=0)
    destination = c2.selectbox("Destination Zone", zones, index=min(1, len(zones)-1))

    c3, c4, c5 = st.columns(3)
    distance_km = c3.number_input("Distance (km)", min_value=0.1, max_value=500.0, value=12.0, step=0.5)
    congestion_index = c4.slider("Input Congestion Index", min_value=0, max_value=100, value=55)
    actual_travel_time_min = c5.number_input("Observed Travel Time (min)", min_value=1.0, max_value=600.0, value=35.0, step=1.0)

    c6, c7, c8 = st.columns(3)
    weather = c6.selectbox("Current Weather", weather_options)
    festival = c7.selectbox("Festival / Public Event", festival_options)
    road_type = c8.selectbox("Road Category", road_options)

    c9, c10 = st.columns(2)
    time_of_day = c9.selectbox("Departure Time Period", time_options)
    day_of_week = c10.selectbox("Day of Week", day_options)

    submitted = st.form_submit_button("🚀 Run Prediction Engine")

# 3. Processing the Prediction
if submitted:
    try:
        with st.spinner("Analyzing traffic patterns..."):
            # Execute Prediction Payload
            result = full_prediction_payload(
                source=source,
                destination=destination,
                distance_km=distance_km,
                congestion_index=congestion_index,
                weather=weather,
                festival=festival,
                road_type=road_type,
                time_of_day=time_of_day,
                day_of_week=day_of_week,
                actual_travel_time_min=actual_travel_time_min
            )

            # Generate Advisories
            advisories = generate_advisory(
                weather=weather,
                festival=festival,
                congestion_index=congestion_index,
                risk_band_value=result["risk_band"],
                source=source,
                destination=destination
            )

        # --- SECTION: RESULTS DISPLAY ---
        st.subheader("📊 Prediction Analysis")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Hotspot Predict", str(result["prediction"]))
        m2.metric("Probability", f"{result['hotspot_probability']*100:.1f}%")
        m3.metric("Risk Score", f"{result['risk_score']}/100")
        m4.metric("Safety Band", result["risk_band"])
        m5.metric("CO2 Footprint", f"{result['co2_kg']} kg")

        # Visual Feedback based on Risk
        if result["risk_band"] == "Severe":
            st.error(f"🚨 **Critical Alert:** High congestion detected between {source} and {destination}.")
        elif result["risk_band"] == "High":
            st.warning(f"⚠️ **Caution:** Significant delays expected on this route.")
        elif result["risk_band"] == "Moderate":
            st.info(f"ℹ️ **Notice:** Moderate traffic flow expected.")
        else:
            st.success(f"✅ **Clear Path:** Route appears safe for travel.")

        # --- SECTION: ADVISORIES ---
        with st.expander("📝 Intelligence Advisories", expanded=True):
            if advisories:
                for adv in advisories:
                    st.markdown(f"- {adv}")
            else:
                st.write("No critical advisories detected for this specific route.")

        # --- SECTION: MODEL INSIGHT ---
        st.subheader("🔍 AI Model Insights")
        fi = get_feature_importance().head(12)
        if not fi.empty:
            # Using Streamlit's native bar chart for speed
            st.bar_chart(fi.set_index("feature")["importance"])
            st.caption("Feature Importance: These factors most influenced the current prediction.")
        else:
            st.info("Feature importance data is currently loading...")

        # --- SECTION: PDF GENERATION ---
        # We use a unique filename to prevent conflict in multi-user environments
        output_dir = os.path.join(BASE_DIR, "output_reports")
        os.makedirs(output_dir, exist_ok=True)
        
        report_filename = f"report_{int(time.time())}.pdf"
        report_path = os.path.join(output_dir, report_filename)

        report_data = {
            "Journey": f"{source} to {destination}",
            "Distance": f"{distance_km} km",
            "Day/Time": f"{day_of_week}, {time_of_day}",
            "Weather": weather,
            "Result": result["prediction"],
            "Hotspot Prob": f"{result['hotspot_probability']*100:.2f}%",
            "Risk Score": result["risk_score"],
            "Risk Band": result["risk_band"],
            "CO2 Emission": f"{result['co2_kg']} kg"
        }
        
        success_pdf = generate_prediction_report(report_path, report_data)

        if success_pdf:
            with open(report_path, "rb") as f:
                st.download_button(
                    label="📩 Download Official PDF Report",
                    data=f,
                    file_name=f"Traffic_Report_{source}_{destination}.pdf",
                    mime="application/pdf"
                )

    except Exception as e:
        st.error(f"An error occurred during prediction: {e}")
        st.info("Please ensure the model is trained via 'train_model.py' before running predictions.")