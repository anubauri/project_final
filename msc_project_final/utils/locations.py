# Updated Mumbai Zone Coordinates
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

DEFAULT_CITY_CENTER = (19.0760, 72.8777)

# Mapping aliases to the official keys in MUMBAI_ZONE_COORDS
ZONE_ALIASES = {
    "bkc": "Bandra",
    "bandra kurla complex": "Bandra",
    "fort": "Churchgate",
    "cst": "Churchgate",
    "csmt": "Churchgate",
    "bombay central": "Mumbai Central",
    "new panvel": "Panvel",
    "vashi": "Navi Mumbai",
    "cbd belapur": "Navi Mumbai"
}

def normalize_zone_name(zone_name):
    """
    Cleans zone names and maps aliases for consistent lookups.
    """
    if zone_name is None or str(zone_name).lower() == 'nan':
        return "Unknown"
    
    # Standardize to title case for lookup (e.g., "bandra " -> "Bandra")
    z = str(zone_name).strip()
    z_lower = z.lower()
    
    # Check alias dictionary first (using lowercase key)
    if z_lower in ZONE_ALIASES:
        return ZONE_ALIASES[z_lower]
    
    # Return original string formatted correctly if it matches a key
    for key in MUMBAI_ZONE_COORDS.keys():
        if key.lower() == z_lower:
            return key
            
    return z # Return as-is if no match found (get_zone_coords will handle it)

def get_zone_coords(zone_name):
    """
    Retrieves (latitude, longitude) for a zone.
    Returns DEFAULT_CITY_CENTER if the zone is not found to prevent UI crashes.
    """
    z = normalize_zone_name(zone_name)
    coords = MUMBAI_ZONE_COORDS.get(z)
    
    if coords is None:
        # Final fallback: case-insensitive search in primary dictionary
        z_lower = str(z).lower()
        for key, val in MUMBAI_ZONE_COORDS.items():
            if key.lower() == z_lower:
                return val
        return DEFAULT_CITY_CENTER
        
    return coords

def get_all_zones():
    """Returns a sorted list of official zone names for Streamlit dropdowns."""
    return sorted(MUMBAI_ZONE_COORDS.keys())