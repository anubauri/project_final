import streamlit as st

def generate_advisory(weather, festival, congestion_index, risk_band_value, source, destination):
    """
    Generates a list of public advisories based on current traffic and environmental factors.
    Includes robust data cleaning to prevent Streamlit UI crashes.
    """
    advisories = []
    
    # 1. Standardize Inputs (Safety against None/NaN/Empty)
    # Using .strip() and .lower() ensures " Rain " and "rain" are treated the same
    weather_val = str(weather or "").lower().strip()
    festival_val = str(festival or "").lower().strip()
    risk_band_str = str(risk_band_value or "Low").strip()
    source_str = str(source or "Origin").strip()
    dest_str = str(destination or "Destination").strip()

    # 2. Risk-Based Advisory
    if risk_band_str in ["Severe", "High", "Critical"]:
        advisories.append(f"⚠️ **High Risk Alert:** Heavy congestion detected from **{source_str}** to **{dest_str}**. Avoid peak travel if possible.")
    
    # 3. Weather-Based Advisory
    # Expanded keywords for better coverage of Mumbai weather patterns
    bad_weather_keywords = ["rain", "storm", "heavy", "fog", "monsoon", "thunder", "flood"]
    if any(word in weather_val for word in bad_weather_keywords):
        advisories.append("🌧️ **Weather Advisory:** Potential for waterlogging or reduced visibility. Drive with caution and check for road closures.")
    
    # 4. Festival/Event Advisory
    festival_keywords = ["yes", "true", "1", "festival", "high", "major", "event", "holiday"]
    if any(word in festival_val for word in festival_keywords):
        advisories.append("🎉 **Event Alert:** Local festivities or public events may cause unpredictable delays. Use public transit if available.")
    
    # 5. Congestion-Based Advisory (Numeric Safety)
    try:
        if congestion_index is not None:
            # Force conversion to float to handle strings passed from CSVs
            c_idx = float(congestion_index)
            if c_idx >= 75:
                advisories.append("🚨 **Gridlock Warning:** Congestion is critical (above 75%). Real-time diversions are likely in effect.")
            elif c_idx >= 45:
                advisories.append("🚙 **Moderate Traffic:** Congestion levels are rising. Expect an additional 10-20 minutes of travel time.")
    except (ValueError, TypeError):
        # Silently log to streamlit console for the dev if the number is bad
        pass

    # 6. Default Fallback
    if not advisories:
        advisories.append("✅ **Clear Route:** Traffic conditions appear stable. Have a safe journey!")
        
    return advisories

def administrative_actions(risk_band_value):
    """
    Returns a list of protocols for city authorities based on the predicted risk level.
    """
    # Clean the status string
    status = str(risk_band_value or "Low").strip()

    # Protocol Dictionary
    mapping = {
        "Low": [
            "Maintain standard automated signal timing (Plan A).",
            "Routine health-checks for IoT traffic sensors."
        ],
        "Moderate": [
            "Enable 'Yellow-Box' enforcement at major junctions.",
            "Increase CCTV monitoring frequency for the affected corridor.",
            "Update Public VMS (Variable Message Signs) with 'Steady Traffic' status."
        ],
        "High": [
            "Deploy 'Green-Wave' signal optimization on arterial roads.",
            "Station rapid-response tow trucks at bottleneck points.",
            "Dispatch traffic personnel for manual override at key intersections.",
            "Broadcast alternate route suggestions via integrated mobile apps."
        ],
        "Severe": [
            "ACTIVATE: Emergency Traffic Mitigation Protocol.",
            "Implement temporary one-way diversions to prioritize outflow.",
            "Restrict heavy commercial vehicle entry into high-risk zones.",
            "Coordinated response with Emergency Services for priority lane access."
        ]
    }
    
    # Returns the mapping, or a generic protocol if the risk_band is an unexpected string
    return mapping.get(status, ["Protocol: Continue baseline monitoring and data collection."])
