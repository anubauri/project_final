import joblib
import numpy as np
import pandas as pd
import streamlit as st
import os

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from utils.locations import get_zone_coords, normalize_zone_name
from utils.risk_calculator import compute_co2_emission, compute_risk_score, risk_band

# --- DYNAMIC PATH CONFIGURATION ---
# Looks one level up from 'utils/' to the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "model", "final_random_forest_model.pkl")
METRICS_PATH = os.path.join(BASE_DIR, "model", "metrics.pkl")
DATA_PATH = os.path.join(BASE_DIR, "dataset", "final_preprocessed_dataset.csv")
ANOMALY_PATH = os.path.join(BASE_DIR, "model", "anomaly_model.pkl")

@st.cache_resource
def load_artifacts():
    """Loads and caches the ML model and metrics to prevent memory lag."""
    if not os.path.exists(MODEL_PATH):
        st.error(f"Model file missing at: {MODEL_PATH}")
        return None, None
    try:
        artifact = joblib.load(MODEL_PATH)
        # Metrics is optional for the predictor but used in 'About' page
        metrics = joblib.load(METRICS_PATH) if os.path.exists(METRICS_PATH) else {}
        return artifact, metrics
    except Exception as e:
        st.error(f"Error loading model artifacts: {e}")
        return None, None

def parse_time_of_day(value):
    """Safely converts time strings to numeric hour proxies."""
    if pd.isna(value):
        return 12.0
    val = str(value).strip().lower()
    mapping = {
        "early morning": 5, "morning": 8, "late morning": 11,
        "afternoon": 14, "evening": 18, "night": 21, "late night": 23
    }
    if val in mapping:
        return float(mapping[val])
    try:
        if ":" in val:
            return float(val.split(":")[0])
        return float(val)
    except:
        return 12.0

def add_engineered_features(df):
    """Generates features that the Random Forest model expects."""
    df = df.copy()
    
    # 1. Date Handling
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["month"] = df["date"].dt.month.fillna(0)
        df["day"] = df["date"].dt.day.fillna(0)
        df["is_weekend"] = df["date"].dt.dayofweek.isin([5, 6]).astype(int)
    else:
        df["month"], df["day"], df["is_weekend"] = 0, 0, 0

    # 2. Time Proxy
    df["hour_proxy"] = df["time_of_day"].apply(parse_time_of_day) if "time_of_day" in df.columns else 12.0

    # 3. Route Logic
    if "source" in df.columns and "destination" in df.columns:
        df["same_zone_trip"] = (df["source"].astype(str).str.strip().str.lower() == 
                                df["destination"].astype(str).str.strip().str.lower()).astype(int)
    else:
        df["same_zone_trip"] = 0

    # 4. Traffic Metrics
    if "distance_km" in df.columns and "actual_travel_time_min" in df.columns:
        dist = pd.to_numeric(df["distance_km"], errors="coerce").fillna(0)
        tt = pd.to_numeric(df["actual_travel_time_min"], errors="coerce").fillna(0)
        df["avg_speed_kmph"] = np.where(tt > 0, dist / (tt / 60.0), 0)
        df["delay_per_km"] = np.where(dist > 0, tt / dist, 0)
    else:
        df["avg_speed_kmph"], df["delay_per_km"] = 0, 0

    # 5. Binary Flags
    if "festival" in df.columns:
        df["festival_binary"] = df["festival"].astype(str).str.lower().isin(["yes", "true", "1", "high"]).astype(int)
    
    if "weather" in df.columns:
        df["bad_weather_flag"] = df["weather"].astype(str).str.lower().isin(["rain", "storm", "fog", "heavy rain"]).astype(int)

    return df

def predict_hotspot(input_df):
    """Feeds input to the pipeline and returns prediction + probability."""
    artifact, _ = load_artifacts()
    if not artifact: 
        return "Unknown", 0.5
    
    pipeline = artifact["pipeline"]
    label_encoder = artifact["label_encoder"]
    feature_columns = artifact["feature_columns"]

    X = input_df.copy()
    
    # FEATURE ALIGNMENT: Ensure all training columns exist in input to prevent Scikit-Learn errors
    for col in feature_columns:
        if col not in X.columns:
            X[col] = 0
            
    X = X[feature_columns] # Strict column ordering

    pred_encoded = pipeline.predict(X)[0]
    pred_label = label_encoder.inverse_transform([pred_encoded])[0]

    try:
        probas = pipeline.predict_proba(X)[0]
        class_index = list(label_encoder.classes_).index(pred_label)
        hotspot_probability = float(probas[class_index])
    except:
        hotspot_probability = 0.5

    return pred_label, hotspot_probability

def full_prediction_payload(source, destination, distance_km, congestion_index, weather, festival, road_type, time_of_day, day_of_week, actual_travel_time_min):
    """Orchestrates the entire logic for pg2_predict_route."""
    row = {
        "source": source, "destination": destination, "distance_km": distance_km,
        "congestion_index": congestion_index, "weather": weather, "festival": festival,
        "road_type": road_type, "time_of_day": time_of_day, "day_of_week": day_of_week,
        "actual_travel_time_min": actual_travel_time_min, "date": pd.Timestamp.today().strftime("%Y-%m-%d")
    }
    
    input_df = add_engineered_features(pd.DataFrame([row]))
    pred_label, hotspot_prob = predict_hotspot(input_df)
    
    # Calculate local risk flags for the risk score module
    bad_weather_flag = 1 if str(weather).lower() in ["rain", "storm", "fog", "heavy rain"] else 0
    festival_binary = 1 if str(festival).lower() in ["yes", "true", "high"] else 0
    
    score = compute_risk_score(congestion_index, bad_weather_flag, festival_binary, hotspot_prob)
    
    return {
        "prediction": pred_label,
        "hotspot_probability": round(hotspot_prob, 4),
        "co2_kg": compute_co2_emission(distance_km),
        "risk_score": score,
        "risk_band": risk_band(score)
    }

@st.cache_data
def load_dataset():
    """Caches CSV loading for the Analytics page."""
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame()
    try:
        df = pd.read_csv(DATA_PATH)
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

def run_dbscan_on_zones(df, eps=1.15, min_samples=2):
    """Performs clustering for geospatial analysis."""
    if df.empty: return pd.DataFrame()
    try:
        # Aggregate by zone
        agg = df.groupby("source").agg({
            "congestion_index": "mean", 
            "hotspot": lambda x: (x.astype(str).str.lower()=="yes").mean()
        }).reset_index()
        agg.columns = ["zone", "congestion_index", "hotspot_numeric"]
        
        # Add coords from locations.py
        agg["lat"] = agg["zone"].apply(lambda z: get_zone_coords(z)[0])
        agg["lon"] = agg["zone"].apply(lambda z: get_zone_coords(z)[1])
        
        X = agg[["lat", "lon", "congestion_index", "hotspot_numeric"]].fillna(0)
        X_scaled = StandardScaler().fit_transform(X)
        
        agg["cluster"] = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(X_scaled)
        return agg
    except Exception as e:
        st.warning(f"Clustering error: {e}")
        return pd.DataFrame()

def detect_anomalies(df):
    """Uses the Isolation Forest model to detect unusual traffic patterns."""
    if not os.path.exists(ANOMALY_PATH) or df.empty:
        return df
    try:
        anomaly_bundle = joblib.load(ANOMALY_PATH)
        model = anomaly_bundle["model"]
        features = anomaly_bundle["features"]

        temp = add_engineered_features(df.copy())
        # Ensure all required features for anomaly detection exist
        for f in features:
            if f not in temp.columns: temp[f] = 0
            
        X_anom = temp[features].fillna(0)
        temp["anomaly_flag"] = np.where(model.predict(X_anom) == -1, "Anomaly", "Normal")
        temp["anomaly_score"] = model.decision_function(X_anom)
        return temp
    except:
        return df

def get_feature_importance():
    """Retrieves Random Forest feature importance for UI visualization."""
    artifact, _ = load_artifacts()
    if not artifact: return pd.DataFrame()
    
    try:
        pipe = artifact["pipeline"]
        # Navigate through the Scikit-Learn Pipeline to find feature names
        names = pipe.named_steps["preprocessor"].get_feature_names_out()
        imps = pipe.named_steps["classifier"].feature_importances_
        
        # Clean up 'num__' and 'cat__' prefixes from names for cleaner charts
        clean_names = [n.split("__")[-1] for n in names]
        
        return pd.DataFrame({"feature": clean_names, "importance": imps}).sort_values("importance", ascending=False)
    except:
        return pd.DataFrame()
