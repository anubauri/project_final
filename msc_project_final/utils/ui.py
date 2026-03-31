import streamlit as st

def apply_ui():
    """
    Applies custom CSS styling to the Streamlit application for a 
    consistent 'Smart City' aesthetic.
    """
    st.markdown("""
    <style>
    /* 1. Global Page Background and Font Smoothing */
    .main {
        background: linear-gradient(180deg, #f6fbff 0%, #eef4fb 100%);
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* 2. Container Padding and Width Management */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1300px;
    }

    /* 3. Typography and Headers */
    h1, h2, h3 {
        color: #1d2b3a;
        font-weight: 800;
        letter-spacing: -0.025em;
    }

    .subtle-text {
        color: #597087;
        font-size: 1.05rem;
        margin-top: -0.5rem;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }

    /* 4. Metric Cards Styling */
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #d8e4ef;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(18, 52, 77, 0.05);
    }

    /* 5. Modern Button Styling (Gradient) */
    div.stButton > button {
        background: linear-gradient(94deg, #0f6cbd 0%, #1b84dd 100%);
        color: white;
        border: none;
        border-radius: 14px;
        padding: 0.7rem 1.5rem;
        font-weight: 700;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        width: auto;
    }

    div.stButton > button:hover {
        background: linear-gradient(94deg, #0b5ca0 0%, #166fbf 100%);
        box-shadow: 0 4px 12px rgba(15, 108, 189, 0.3);
        transform: translateY(-1px);
        color: white;
    }

    /* 6. Sidebar Aesthetic Adjustments */
    section[data-testid="stSidebar"] {
        background-color: #f0f5fa;
        border-right: 1px solid #e1e8f0;
    }

    [data-testid="stSidebarNav"] {
        padding-top: 1rem;
    }

    /* 7. Reusable Component Classes */
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

    .info-card, .chart-card {
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

    /* Target inputs and select boxes for rounded corners */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 12px;
    }
    
    </style>
    """, unsafe_allow_html=True)