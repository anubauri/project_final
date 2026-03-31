# Updated Mumbai Zone Coordinates
# Essential for Folium Map markers and DBSCAN clustering
MUMBAI_ZONE_COORDS = {
    "Colaba": (18.9067, 72.8147),
    "Nariman Point": (18.9256, 72.8232),
    "Churchgate": (18.9350, 72.8269),
    "Marine Lines": (18.9447, 72.8244),
    "Charni Road": (18.9522, 72.8196),
    "Grant Road": (18.9647, 72.8131),
    "Mumbai Central": (18.9690, 72.8193),
    "Mahalaxmi": (18.9830, 72.8130),
    "Lower Parel": (18.9977, 72.8303),
    "Worli": (19.0110, 72.8150),
    "Dadar": (19.0180, 72.8430),
    "Prabhadevi": (19.0166, 72.8295),
    "Bandra": (19.0544, 72.8406),
    "Khar": (19.0694, 72.8361),
    "Santacruz": (19.0817, 72.8410),
    "Vile Parle": (19.1000, 72.8400),
    "Andheri": (19.1197, 72.8468),
    "Jogeshwari": (19.1364, 72.8480),
    "Goregaon": (19.1647, 72.8493),
    "Malad": (19.1867, 72.8484),
    "Kandivali": (19.2043, 72.8526),
    "Borivali": (19.2307, 72.8567),
    "Dahisar": (19.2503, 72.8594),
    "Kurla": (19.0728, 72.8826),
    "Sion": (19.0434, 72.8619),
    "Matunga": (19.0274, 72.8553),
    "Chembur": (19.0522, 72.9005),
    "Ghatkopar": (19.0850, 72.9080),
    "Vikhroli": (19.1115, 72.9287),
    "Bhandup": (19.1458, 72.9397),
    "Mulund": (19.1726, 72.9561),
    "Powai": (19.1176, 72.9060),
    "Airoli": (19.1590, 72.9986),
    "Thane": (19.2183, 72.9781),
    "Panvel": (18.9894, 73.1175),
    "Navi Mumbai": (19.0330, 73.0297)
}

# Mumbai Geo-Center for initializing Folium Maps
DEFAULT_CITY_CENTER = (19.0760, 72.8777)

# Mapping common user inputs to official dictionary keys
ZONE_ALIASES = {
    "bkc": "Bandra",
    "bandra kurla complex": "Bandra",
    "fort": "Churchgate",
    "cst": "Churchgate",
    "csmt": "Churchgate",
    "bombay central": "Mumbai Central",
    "new panvel": "Panvel",
    "vashi": "Navi Mumbai",
    "cbd belapur": "Navi Mumbai",
    "juhu": "Vile Parle"
}

def normalize_zone_name(zone_name):
    """
    Cleans zone names and maps aliases for consistent lookups.
    Essential for matching CSV data with the coordinate dictionary.
    """
    if zone_name is None or str(zone_name).lower() in ['nan', 'none', '']:
        return "Unknown"
    
    # Standardize input
    z_clean = str(zone_name).strip()
    z_lower = z_clean.lower()
    
    # 1. Check alias dictionary first
    if z_lower in ZONE_ALIASES:
        return ZONE_ALIASES[z_lower]
    
    # 2. Check for case-insensitive match in primary dictionary
    for official_key in MUMBAI_ZONE_COORDS.keys():
        if official_key.lower() == z_lower:
            return official_key
            
    # 3. Return the cleaned original if no match (will fallback to center in get_zone_coords)
    return z_clean

def get_zone_coords(zone_name):
    """
    Retrieves (latitude, longitude) for a zone.
    Guaranteed to return a tuple to prevent 'NoneType' map crashes.
    """
    z = normalize_zone_name(zone_name)
    coords = MUMBAI_ZONE_COORDS.get(z)
    
    # If key doesn't exist, return city center so the map still renders
    if coords is None:
        return DEFAULT_CITY_CENTER
        
    return coords

def get_all_zones():
    """
    Returns a sorted list of official zone names.
    Used for st.selectbox dropdowns in the Streamlit UI.
    """
    return sorted(list(MUMBAI_ZONE_COORDS.keys()))
