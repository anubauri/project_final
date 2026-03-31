import streamlit as st
import pandas as pd
import os
from datetime import datetime

from utils.intervention import generate_advisory
from utils.risk_calculator import compute_risk_score, risk_band, compute_co2_emission
from utils.ui import apply_ui
from utils.pdf_report import generate_prediction_report

# 1. Page Configuration
st.set_page_config(page_title="Public Advisory | Smart City", page_icon="📢", layout="wide")
apply_ui()

# Header Section
st.markdown("<div class='badge'>Citizen Advisory</div>", unsafe_allow_html=True)
st.title("📢 Public Advisory & Intervention Simulator")
st.markdown("<p class='subtle-text'>Simulate travel conditions, monitor urban risk, and evaluate the impact of traffic management interventions.</p>", unsafe_allow_html=True)

# 2. Input Section
st.divider()
col_title1, col_title2 = st.columns([2, 1])
with col_title1:
    st.subheader("📍 Journey Context")
    c_in1, c_in2 = st.columns(2)
    source = c_in1.text_input("Source Zone", "Andheri").strip() or "Unknown Origin"
    destination = c_in2.text_input("Destination Zone", "Bandra").strip() or "Unknown Destination"

st.subheader("☁️ Environmental Baseline")
c1, c2, c3 = st.columns(3)
congestion_index = c1.slider("Current Congestion Index (%)", 0, 100, 60)
weather = c2.selectbox("Weather Condition", ["Clear", "Cloudy", "Rain", "Heavy Rain", "Storm", "Fog"])
festival = c3.selectbox("Festival / Public Event", ["No", "Yes"])

c_in3, c_in4 = st.columns(2)
distance_km = c_in3.number_input("Route Distance (km)", min_value=0.1, max_value=200.0, value=10.0, step=0.5)
hotspot_probability = c_in4.slider("AI Hotspot Probability", 0.0, 1.0, 0.65, step=0.01)

# 3. Calculation Logic (Baseline)
bad_weather_flag = 1 if str(weather).lower() in ["rain", "storm", "fog", "heavy rain"] else 0
festival_binary = 1 if str(festival).lower() == "yes" else 0

score = compute_risk_score(congestion_index, bad_weather_flag, festival_binary, hotspot_probability)
band = risk_band(score)
co2 = compute_co2_emission(distance_km)

# --- SECTION 1: CURRENT SCENARIO ---
st.markdown("---")
st.markdown("## 📊 Baseline Analysis")
m1, m2, m3 = st.columns(3)
m1.metric("Current Risk Score", f"{score}/100")
m2.metric("Safety Category", band)
m3.metric("CO2 Footprint", f"{co2} kg")

# --- SECTION 2: ADVISORY ---
with st.expander("📢 View Active Public Advisories", expanded=True):
    advisories = generate_advisory(weather, festival, congestion_index, band, source, destination)
    if advisories:
        for adv in advisories:
            if band == "Severe": st.error(adv)
            elif band == "High": st.warning(adv)
            else: st.info(adv)
    else:
        st.write("No critical advisories for the current parameters.")

# --- SECTION 3: INTERVENTION SIMULATOR ---
st.markdown("---")
st.markdown("## 🛠️ Management Intervention Simulator")
st.info("Adjust parameters below to simulate how traffic management (e.g., signals, diversions) reduces urban risk.")

col_sim1, col_sim2 = st.columns(2)
new_congestion = col_sim1.slider("Simulated Congestion (After Intervention)", 0, 100, max(0, congestion_index - 20))
new_weather = col_sim2.selectbox("Simulated Weather Change", ["Clear", "Cloudy", "Rain", "Storm", "Fog"], index=0)

col_sim3, col_sim4 = st.columns(2)
new_festival = col_sim3.selectbox("Simulated Event Status", ["No", "Yes"], index=0)
new_hotspot_probability = col_sim4.slider("Simulated Reduction in Hotspot Likelihood", 0.0, 1.0, max(0.0, hotspot_probability - 0.25))

# Recalculate for Intervention Scenario
new_bad_weather_flag = 1 if str(new_weather).lower() in ["rain", "storm", "fog", "heavy rain"] else 0
new_festival_binary = 1 if str(new_festival).lower() == "yes" else 0

new_score = compute_risk_score(new_congestion, new_bad_weather_flag, new_festival_binary, new_hotspot_probability)
new_band = risk_band(new_score)
score_diff = round(new_score - score, 2)

# --- SECTION 4: PROJECTED OUTCOME ---
st.markdown("### 📈 Simulation Results")
a1, a2, a3 = st.columns(3)
a1.metric("Baseline Risk", score)
# 'inverse' delta color means a decrease (negative) is shown as green (good)
a2.metric("Projected Risk", new_score, delta=score_diff, delta_color="inverse")
a3.metric("Projected Band", new_band)

if new_score < score:
    st.success(f"✅ Positive Impact: Proposed interventions reduce city-wide risk by {abs(score_diff)} points.")
    if abs(score_diff) >= 20:
        st.balloons()
elif new_score > score:
    st.error("⚠️ Risk Escalation: Simulated conditions indicate worsening safety levels.")

# --- SECTION 5: REPORT EXPORT ---
st.divider()
if st.button("📄 Finalize Simulation & Generate Report"):
    with st.spinner("Compiling results..."):
        report_filename = f"Simulation_Report_{datetime.now().strftime('%H%M%S')}.pdf"
        
        report_data = {
            "Route Evaluated": f"{source} to {destination}",
            "Original Risk Score": f"{score} ({band})",
            "Simulated Risk Score": f"{new_score} ({new_band})",
            "Net Risk Reduction": f"{abs(score_diff)} points",
            "Weather Improvement": f"Changed to {new_weather}",
            "Congestion Change": f"{congestion_index}% down to {new_congestion}%",
            "Status": "Intervention Successful" if new_score < score else "Review Required",
            "Generated At": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        # Uses our updated utility that handles directory creation
        pdf_path = generate_prediction_report(report_filename, report_data)
        
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📩 Download Intervention Analysis PDF",
                    data=f,
                    file_name=report_filename,
                    mime="application/pdf"
                )
