def generate_advisory(weather, festival, congestion_index, risk_band_value, source, destination):
    """
    Generates a list of public advisories based on current traffic and environmental factors.
    """
    advisories = []
    
    # 1. Standardize Inputs (Safety against None/NaN)
    weather_val = str(weather or "").lower().strip()
    festival_val = str(festival or "").lower().strip()
    risk_band_str = str(risk_band_value or "Low")
    source_str = str(source or "Origin")
    dest_str = str(destination or "Destination")

    # 2. Risk-Based Advisory
    if risk_band_str in ["Severe", "High"]:
        advisories.append(f"⚠️ High Risk Alert: Avoid peak travel from {source_str} to {dest_str} unless necessary.")
    
    # 3. Weather-Based Advisory
    bad_weather_keywords = ["rain", "storm", "heavy rain", "fog", "thunderstorm"]
    if any(word in weather_val for word in bad_weather_keywords):
        advisories.append("🌧️ Weather Advisory: Poor visibility/traction detected. Drive slowly and allow extra buffer time.")
    
    # 4. Festival/Event Advisory
    festival_keywords = ["yes", "true", "1", "festival", "high", "major", "event"]
    if any(word in festival_val for word in festival_keywords):
        advisories.append("🎉 Event Alert: Festival movement may increase local congestion. Consider alternate routes.")
    
    # 5. Congestion-Based Advisory (Numeric Safety)
    try:
        if congestion_index is not None:
            c_idx = float(congestion_index)
            if c_idx >= 70:
                advisories.append("🚗 Gridlock Warning: Congestion is critically elevated. Public transit is highly recommended.")
            elif c_idx >= 40:
                advisories.append("🚙 Moderate Traffic: Congestion expected. Monitor live conditions before departure.")
    except (ValueError, TypeError):
        # Fail silently if congestion_index isn't a valid number
        pass

    # 6. Default Fallback
    if not advisories:
        advisories.append("✅ Clear Route: Traffic conditions appear manageable. Proceed with normal caution.")
        
    return advisories

def administrative_actions(risk_band_value):
    """
    Returns a list of protocols for city authorities based on the risk level.
    """
    # Ensure we are checking a string and handle None
    status = str(risk_band_value or "Low").strip()

    mapping = {
        "Low": [
            "Maintain regular automated signal timing plan.",
            "Continue routine sensor monitoring."
        ],
        "Moderate": [
            "Increase CCTV surveillance at critical junctions.",
            "Issue soft public advisory notifications via mobile apps."
        ],
        "High": [
            "Deploy manual traffic personnel at vulnerable corridors.",
            "Adjust signal timing dynamically (Green-wave optimization).",
            "Broadcast alternate-route guidance on digital signboards."
        ],
        "Severe": [
            "Trigger Emergency Traffic Response Mode.",
            "Prioritize congestion dispersal corridors for emergency vehicles.",
            "Send high-priority SMS alerts and restrict heavy vehicle inflow."
        ]
    }
    
    # Use .get with a default list to prevent KeyError
    return mapping.get(status, ["Protocol: Continue standard monitoring."])