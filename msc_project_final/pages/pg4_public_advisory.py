import streamlit as st
import pandas as pd

from utils.intervention import generate_advisory
from utils.risk_calculator import compute_risk_score, risk_band, compute_co2_emission
from utils.ui import apply_ui

# 1. Page Configuration
st.set_page_config(page_title="Public Advisory | Smart City", page_icon="📢", layout="wide")
apply_ui()

# Header Section with Styling
st.markdown("<div class='badge'>Citizen Advisory</div>", unsafe_allow_html=True)
st.title("📢 Public Advisory and Intervention Simulator")
st.markdown("<p class='subtle-text'>Simulate travel conditions, monitor risk, and evaluate intervention impact.</p>", unsafe_allow_html=True)

# 2. Input Section
st.markdown("---")
st.subheader("📍 Journey Details")
c_in1, c_in2 = st.columns(2)
# Added strip() and default fallback to prevent empty string errors in reports
source = c_in1.text_input("Source Zone", "Andheri").strip() or "Unknown Origin"
destination = c_in2.text_input("Destination Zone", "Bandra").strip() or "Unknown Destination"

st.subheader("☁️ Environmental Factors")
c1, c2, c3 = st.columns(3)
congestion_index = c1.slider("Current Congestion Index", 0, 100, 60)
weather = c2.selectbox("Weather Condition", ["Clear", "Cloudy", "Rain", "Storm", "Fog"])
festival = c3.selectbox("Festival / Public Event", ["No", "Yes"])

c_in3, c_in4 = st.columns(2)
distance_km = c_in3.number_input("Distance (km)", min_value=0.1, max_value=500.0, value=10.0, step=0.5)
hotspot_probability = c_in4.slider("Model Prediction: Hotspot Probability", 0.0, 1.0, 0.65, step=0.01)

# 3. Calculation Logic (Safety Casting)
bad_weather_flag = 1 if str(weather).lower() in ["rain", "storm", "fog"] else 0
festival_binary = 1 if str(festival).lower() == "yes" else 0

# Compute risk metrics using the updated risk_calculator.py
score = compute_risk_score(congestion_index, bad_weather_flag, festival_binary, hotspot_probability)
band = risk_band(score)
co2 = compute_co2_emission(distance_km)

# --- SECTION 1: CURRENT SCENARIO ---
st.markdown("## 📊 Current Scenario Analysis")
c4, c5, c6 = st.columns(3)
c4.metric("Risk Score", f"{score}/100")
c5.metric("Safety Band", band)
c6.metric("Estimated CO2 Impact", f"{co2} kg")

# --- SECTION 2: PUBLIC ADVISORY ---
st.markdown("## 📢 Public Advisory")
# Using the updated intervention.py logic
advisories = generate_advisory(weather, festival, congestion_index, band, source, destination)

if advisories:
    for adv in advisories:
        if band == "Severe":
            st.error(adv)
        elif band == "High":
            st.warning(adv)
        elif band == "Moderate":
            st.info(adv)
        else:
            st.success(adv)
else:
    st.info("No active advisories for the current parameters.")

# --- SECTION 3: INTERVENTION SIMULATOR ---
st.divider()
st.markdown("## 🛠️ Intervention Simulator")
st.markdown("<p class='subtle-text'>Adjust parameters to simulate how traffic management or weather improvements impact safety.</p>", unsafe_allow_html=True)

col_sim1, col_sim2 = st.columns(2)
# We use current sliders as the baseline for the simulator
new_congestion = col_sim1.slider("Simulated Congestion (After Traffic Management)", 0, 100, max(0, congestion_index - 15))
new_weather = col_sim2.selectbox("Simulated Weather Improvement", ["Clear", "Cloudy", "Rain", "Storm", "Fog"], index=0)

col_sim3, col_sim4 = st.columns(2)
new_festival = col_sim3.selectbox("Simulated Event Condition", ["No", "Yes"], index=0)
new_hotspot_probability = col_sim4.slider("Simulated Reduction in Hotspot Likelihood", 0.0, 1.0, max(0.0, hotspot_probability - 0.20))

# Recalculate for Intervention Scenario
new_bad_weather_flag = 1 if str(new_weather).lower() in ["rain", "storm", "fog"] else 0
new_festival_binary = 1 if str(new_festival).lower() == "yes" else 0

new_score = compute_risk_score(new_congestion, new_bad_weather_flag, new_festival_binary, new_hotspot_probability)
new_band = risk_band(new_score)

# --- SECTION 4: IMPROVED OUTCOME ---
st.markdown("### 📈 Projected Outcome")
a1, a2, a3 = st.columns(3)
a1.metric("Original Risk", score)

# Delta logic for visual feedback
score_diff = round(new_score - score, 2)
a2.metric("Projected Risk", new_score, delta=score_diff, delta_color="inverse")
a3.metric("Projected Band", new_band)

if new_score < score:
    st.success(f"✅ Success: Proposed interventions reduce risk by {abs(score_diff)} points.")
    if score_diff <= -15: # If improvement is significant
        st.balloons()
elif new_score > score:
    st.error("⚠️ Warning: Simulated conditions lead to increased risk levels.")

# --- SECTION 5: EXPORT ---
st.divider()
if st.button("📄 Generate Simulation Report"):
    from utils.pdf_report import generate_prediction_report
    import time
    
    report_data = {
        "Source": source,
        "Destination": destination,
        "Original Score": score,
        "Original Band": band,
        "Simulated Score": new_score,
        "Simulated Band": new_band,
        "Improvement": abs(score_diff) if score_diff < 0 else 0,
        "Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    }
    
    report_name = f"intervention_report_{int(time.time())}.pdf"
    report_path = f"/tmp/{report_name}" # Using /tmp for streamlit cloud/colab compatibility
    
    final_path = generate_prediction_report(report_path, report_data)
    
    if final_path:
        with open(final_path, "rb") as f:
            st.download_button("📩 Download PDF Summary", f, file_name=report_name)