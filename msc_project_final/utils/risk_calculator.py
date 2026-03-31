import streamlit as st

def compute_co2_emission(distance_km, vehicle_factor=0.192):
    """
    Calculates CO2 emissions based on travel distance.
    Default factor: 0.192 kg CO2/km (Standard passenger car).
    """
    try:
        # Handle cases where distance might be None or a string from a CSV
        if distance_km is None:
            return 0.0
        val = float(distance_km)
        # Ensure we don't return negative emissions
        return round(max(val, 0.0) * vehicle_factor, 3)
    except (ValueError, TypeError):
        return 0.0

def travel_delay_index(predicted_time_min, free_flow_time_min):
    """
    Calculates the Ratio of Delay (Travel Time Index).
    1.0 = Smooth traffic, >1.5 = Significant congestion.
    """
    try:
        p_time = float(predicted_time_min) if predicted_time_min is not None else 0.0
        f_time = float(free_flow_time_min) if free_flow_time_min is not None else 0.0
        
        # Avoid division by zero
        if f_time <= 0:
            return 1.0
        return round(p_time / f_time, 3)
    except (ValueError, TypeError):
        return 1.0

def compute_risk_score(congestion_index, bad_weather_flag, festival_binary, hotspot_probability):
    """
    Calculates a multi-factor weighted risk score (0-100).
    Weights: 
    - Congestion: 45%
    - Weather: 15%
    - Festival/Event: 10%
    - ML Hotspot Prediction: 30%
    """
    try:
        # 1. Congestion Weight (Max 45 points)
        # Assuming congestion_index is 0-100
        c_idx = float(congestion_index) if congestion_index is not None else 0.0
        congestion_component = (min(max(c_idx, 0), 100) / 100) * 45
        
        # 2. Weather Weight (Max 15 points)
        # Handles boolean (True/False) or numeric (1/0)
        w_flag = 1 if bad_weather_flag in [1, True, "1", "True", "yes"] else 0
        weather_component = 15 if w_flag == 1 else 0
        
        # 3. Festival Weight (Max 10 points)
        f_flag = 1 if festival_binary in [1, True, "1", "True", "yes"] else 0
        festival_component = 10 if f_flag == 1 else 0
        
        # 4. Hotspot Probability Weight (Max 30 points)
        # ML model probability is usually 0.0 to 1.0
        h_prob = float(hotspot_probability) if hotspot_probability is not None else 0.0
        hotspot_component = min(max(h_prob, 0), 1) * 30
        
        total_score = congestion_component + weather_component + festival_component + hotspot_component
        
        # Final safety clip between 0 and 100
        return round(min(max(total_score, 0), 100), 2)
        
    except (ValueError, TypeError):
        # Fallback to a safe zero if data is corrupted
        return 0.0

def risk_band(score):
    """
    Categorizes numeric risk into actionable semantic bands.
    Used for UI color coding (Success/Warning/Error).
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

def get_risk_color(band):
    """
    Helper function for Streamlit UI to return Hex colors 
    based on the risk band.
    """
    colors = {
        "Low": "#28a745",      # Green
        "Moderate": "#fd7e14", # Orange
        "High": "#dc3545",     # Red
        "Severe": "#721c24"    # Dark Maroon
    }
    return colors.get(band, "#0F6CBD")
