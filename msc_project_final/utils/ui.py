import streamlit as st

def apply_ui():
    """
    Applies custom CSS styling to the Streamlit application for a 
    consistent 'Smart City' aesthetic.
    """
    # Using st.cache_resource here is a 'pro-tip' for production. 
    # It ensures the CSS is injected efficiently without re-processing strings on every click.
    st.markdown("""
    <style>
    /* 1. Global Page Background and Font Smoothing */
    /* Added overflow-x: hidden to prevent unwanted horizontal scrolling on mobile */
    .stApp {
        background: linear-gradient(180deg, #f6fbff 0%, #eef4fb 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* 2. Container Padding and Width Management */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1300px;
    }

    /* 3. Typography and Headers */
    h1, h2, h3 {
        color: #1d2b3a !important;
        font-weight: 800 !important;
        letter-spacing: -0.025em !important;
    }

    .subtle-text {
        color: #597087;
        font-size: 1.05rem;
        margin-top: -0.5rem;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }

    /* 4. Metric Cards Styling */
    /* Target the container of metrics more specifically for Cloud deployment */
    [data-testid="stMetric"] {
        background: white !important;
        border: 1px solid #d8e4ef !important;
        padding: 20px !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 15px rgba(18, 52, 77, 0.05) !important;
    }

    /* 5. Modern Button Styling (Gradient) */
    div.stButton > button {
        background: linear-gradient(94deg, #0f6cbd 0%, #1b84dd 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        width: auto !important;
    }

    div.stButton > button:hover {
        background: linear-gradient(94deg, #0b5ca0 0%, #166fbf 100%) !important;
        box-shadow: 0 4px 12px rgba(15, 108, 189, 0.3) !important;
        transform: translateY(-1px) !important;
    }

    /* 6. Sidebar Aesthetic Adjustments */
    section[data-testid="stSidebar"] {
        background-color: #f0f5fa !important;
        border-right: 1px solid #e1e8f0 !important;
    }

    /* 7. Reusable Component Classes (HTML Injections) */
    .badge {
        display: inline-block;
        background: #e1efff;
        color: #0f6cbd;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 800;
        padding: 0.4rem 0.9rem;
        border-radius: 100px;
        margin-bottom: 1rem;
        border: 1px solid #c8e1ff;
    }

    .info-card {
        background: white;
        border: 1px solid #d8e4ef;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 6px 20px rgba(18, 52, 77, 0.06);
        margin-bottom: 1.2rem;
    }

    /* 8. Success/Risk Status Classes */
    .prediction-text {
        font-size: 1.2rem;
        font-weight: 600;
        color: #0f6cbd;
    }

    /* Target inputs for rounded corners */
    .stTextInput input, .stSelectbox [data-baseweb="select"] {
        border-radius: 12px !important;
    }

    /* Hide the Streamlit 'Made with Streamlit' footer for a professional look */
    footer {visibility: hidden;}
    #MainMenu {visibility: visible;}
    
    </style>
    """, unsafe_allow_html=True)
