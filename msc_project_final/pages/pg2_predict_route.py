import os
import streamlit as st
import pandas as pd
import time
from datetime import datetime

from utils.locations import get_all_zones
from utils.predictor import full_prediction_payload, get_feature_importance
from utils.intervention import generate_advisory
from utils.pdf_report import generate_prediction_report
from utils.ui import apply_ui

# --- DYNAMIC CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Page Config & UI
st.set_page_config(page_title="Predict Route | Smart City", page_icon="🚘", layout="wide")
apply_ui()

# Header Section
st.markdown("<div class='badge'>Smart Mobility</div>", unsafe_allow_html=True)
st.title("🚘 Route Prediction & Risk Assessment")
st.markdown("<p class='subtle-text'>Predict congestion risk, hotspot probability, and route-level advisory intelligence using Random Forest & DBSCAN.</p>", unsafe_allow_html=True)

# 1. Input Data Loading
zones = get_all_zones()
weather_options = ["Clear", "Cloudy", "Rain", "Heavy Rain", "Storm", "Fog"]
festival_options = ["No", "Yes"]
road_options = ["Highway", "Main Road", "Arterial", "Internal Road", "Mixed"]
time_options = ["Early Morning", "Morning", "Late Morning", "Afternoon", "Evening", "Night", "Late Night"]
day_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# 2. Prediction Form
with st.form("prediction_form"):
    st.subheader("📍 Journey Details")
    c1, c2 = st.columns(2)
    source = c1.selectbox("Source Zone", zones, index=0)
    destination = c2.selectbox("Destination Zone", zones, index=min(1, len(zones)-1))

    st.divider()
    st.subheader("🚗 Real-time Parameters")
    c3, c4, c5 = st.columns(3)
    distance_km = c3.number_input("Distance (km)", min_value=0.1, max_value=200.0, value=12.0, step=0.5)
    congestion_index = c4.slider("Input Congestion Index (%)", min_value=0, max_value=100, value=55)
    actual_travel_time_min = c5.number_input("Observed Travel Time (min)", min_value=1.0, max_value=300.0, value=35.0, step=1.0)

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
    if source == destination:
        st.warning("⚠️ Source and Destination are the same. Please select a valid route.")
    else:
        try:
            with st.spinner("🧠 AI Engine analyzing traffic patterns..."):
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
            st.success("Analysis Complete!")
            
            # KPI Metrics Row
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Hotspot Predict", str(result["prediction"]))
            m2.metric("Probability", f"{result['hotspot_probability']*100:.1f}%")
            m3.metric("Risk Score", f"{result['risk_score']}/100")
            m4.metric("Safety Band", result["risk_band"])
            m5.metric("CO2 Footprint", f"{result['co2_kg']} kg")

            # Visual Feedback Callouts
            risk_band = result["risk_band"]
            if risk_band == "Severe":
                st.error(f"🚨 **CRITICAL:** High traffic density confirmed. Seek alternate transport.")
            elif risk_band == "High":
                st.warning(f"⚠️ **HIGH RISK:** Expect significant delays on the {road_type} network.")
            elif risk_band == "Moderate":
                st.info(f"ℹ️ **MODERATE:** Traffic is moving but slowing in key zones.")
            else:
                st.success(f"✅ **OPTIMAL:** Conditions are favorable for travel.")

            # --- SECTION: ADVISORIES & EXPLAINABILITY ---
            col_adv, col_feat = st.columns([1, 1.2])

            with col_adv:
                st.subheader("📝 Public Advisories")
                for adv in advisories:
                    st.info(adv)

            with col_feat:
                st.subheader("🔍 Model Decision Factors")
                fi = get_feature_importance().head(8)
                if not fi.empty:
                    # Sort to show highest importance at the top
                    st.bar_chart(fi.set_index("feature")["importance"], horizontal=True)
                    st.caption("Factors influencing the current traffic prediction.")

            # --- SECTION: PDF GENERATION ---
            st.divider()
            st.subheader("📋 Official Documentation")
            
            # Using the simplified filename logic from our updated pdf_report.py
            report_filename = f"Traffic_Report_{datetime.now().strftime('%H%M%S')}.pdf"
            
            report_data = {
                "Journey Route": f"{source} to {destination}",
                "Distance (KM)": distance_km,
                "Temporal Data": f"{day_of_week} ({time_of_day})",
                "Weather Condition": weather,
                "ML Prediction": result["prediction"],
                "Hotspot Probability": f"{result['hotspot_probability']*100:.2f}%",
                "Risk Score": result["risk_score"],
                "Safety Category": result["risk_band"],
                "Est. Carbon Impact": f"{result['co2_kg']} kg CO2"
            }
            
            # Call the updated generator (which handles paths internally)
            pdf_path = generate_prediction_report(report_filename, report_data)

            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📩 Download Technical PDF Report",
                        data=f,
                        file_name=f"SmartCity_Analysis_{source}_{destination}.pdf",
                        mime="application/pdf",
                        help="Download a formal technical report for urban planning documentation."
                    )
            
        except Exception as e:
            st.error(f"Prediction Pipeline Error: {e}")
            st.info("Check if model artifacts (Random Forest .pkl) are uploaded to the 'model/' folder.")
