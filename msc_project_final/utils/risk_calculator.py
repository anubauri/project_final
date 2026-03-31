import streamlit as st

def compute_co2_emission(distance_km, vehicle_factor=0.192):
    """
    Calculates CO2 emissions based on distance.
    Default vehicle_factor is 0.192 kg CO2 per km (avg passenger car).
    """
    try:
        if distance_km is None:
            return 0.0
        val = float(distance_km)
        return round(max(val, 0.0) * vehicle_factor, 3)
    except (ValueError, TypeError):
        return 0.0

def travel_delay_index(predicted_time_min, free_flow_time_min):
    """
    Calculates the ratio of predicted time vs free flow time.
    """
    try:
        p_time = float(predicted_time_min) if predicted_time_min is not None else 0.0
        f_time = float(free_flow_time_min) if free_flow_time_min is not None else 0.0
        
        if f_time <= 0:
            return 1.0
        return round(p_time / f_time, 3)
    except (ValueError, TypeError):
        return 1.0

def compute_risk_score(congestion_index, bad_weather_flag, festival_binary, hotspot_probability):
    """
    Calculates a weighted risk score between 0 and 100.
    """
    try:
        # 1. Congestion Weight (Max 45 points)
        c_idx = float(congestion_index) if congestion_index is not None else 0.0
        congestion_component = min(max(c_idx, 0), 100) * 0.45
        
        # 2. Weather Weight (Fixed 15 points)
        # Handles both integer 1/0 and boolean True/False
        w_flag = int(bad_weather_flag) if bad_weather_flag is not None else 0
        weather_component = 15 if w_flag == 1 else 0
        
        # 3. Festival Weight (Fixed 10 points)
        f_flag = int(festival_binary) if festival_binary is not None else 0
        festival_component = 10 if f_flag == 1 else 0
        
        # 4. Hotspot Probability Weight (Max 30 points)
        h_prob = float(hotspot_probability) if hotspot_probability is not None else 0.0
        hotspot_component = min(max(h_prob, 0), 1) * 30
        
        score = congestion_component + weather_component + festival_component + hotspot_component
        return round(min(max(score, 0), 100), 2)
        
    except (ValueError, TypeError) as e:
        # Log error in streamlit console for debugging without crashing the UI
        # st.sidebar.error(f"Calculation Error: {e}") 
        return 0.0

def risk_band(score):
    """
    Categorizes the numeric score into safety bands.
    """
    try:
        s = float(score)
    except (ValueError, TypeError):
        s = 0.0

    if s >= 75:
        return "Severe"
    if s >= 55:
        return "High"
    if s >= 35:
        return "Moderate"
    return "Low"