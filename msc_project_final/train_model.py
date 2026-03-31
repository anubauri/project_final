import os
import warnings
import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)

warnings.filterwarnings("ignore")

# --- PATH CONFIGURATIONS (DYNAMIC) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(BASE_DIR, "dataset", "final_preprocessed_dataset.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "final_random_forest_model.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.pkl")
ANOMALY_PATH = os.path.join(MODEL_DIR, "anomaly_model.pkl")

TARGET_COLUMN = "hotspot"

def parse_time_of_day(value):
    """Converts categorical time periods to numeric hour proxies for ML compatibility."""
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
        # Handle cases where value might already be a string representation of an hour
        if ":" in val:
            return float(val.split(":")[0])
        return float(val)
    except:
        return 12.0

def add_engineered_features(df):
    """Feature Engineering: Creates consistent inputs for both Training and Inference."""
    df = df.copy()

    # 1. Date-based Features
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["month"] = df["date"].dt.month.fillna(1)
        df["day_of_month"] = df["date"].dt.day.fillna(1)
        df["is_weekend"] = df["date"].dt.dayofweek.isin([5, 6]).astype(int)
    else:
        df["month"], df["day_of_month"], df["is_weekend"] = 1, 1, 0

    # 2. Temporal Proxy
    if "time_of_day" in df.columns:
        df["hour_proxy"] = df["time_of_day"].apply(parse_time_of_day)
    else:
        df["hour_proxy"] = 12.0

    # 3. Spatial Logic
    if "source" in df.columns and "destination" in df.columns:
        df["intra_zone_trip"] = (df["source"].astype(str).str.lower() == 
                                 df["destination"].astype(str).str.lower()).astype(int)
    else:
        df["intra_zone_trip"] = 0

    # 4. Derived Traffic Performance Metrics
    # We use numeric coercion to avoid string-math errors
    dist = pd.to_numeric(df.get("distance_km", 0), errors="coerce").fillna(1)
    tt = pd.to_numeric(df.get("actual_travel_time_min", 0), errors="coerce").fillna(1)
    
    df["avg_speed_kmph"] = (dist / (tt / 60.0)).replace([np.inf, -np.inf], 0).fillna(0)
    df["delay_intensity"] = (tt / dist).replace([np.inf, -np.inf], 0).fillna(0)

    return df

def main():
    # Setup directory structure
    os.makedirs(MODEL_DIR, exist_ok=True)

    if not os.path.exists(DATA_PATH):
        print(f"❌ CRITICAL ERROR: Dataset not found at {DATA_PATH}")
        return

    # 1. Load and Sanitize
    print("📂 Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    df.columns = [c.strip() for c in df.columns]

    if TARGET_COLUMN not in df.columns:
        print(f"❌ ERROR: Target '{TARGET_COLUMN}' column missing from CSV.")
        return

    # 2. Engineering
    print("🛠 Engineering features...")
    df = add_engineered_features(df)

    # 3. Preparation
    # Drop non-predictive metadata columns
    metadata_cols = ["date", "route", "hotspot_numeric", "cluster"]
    y_raw = df[TARGET_COLUMN].astype(str).str.capitalize().fillna("Normal")
    X = df.drop(columns=[c for c in metadata_cols if c in df.columns] + [TARGET_COLUMN], errors="ignore")

    # Encode Target Labels
    le = LabelEncoder()
    y = le.fit_transform(y_raw)

    # Identify Column Types
    numeric_features = X.select_dtypes(include=['int64', 'float64', 'int32']).columns.tolist()
    categorical_features = X.select_dtypes(include=['object']).columns.tolist()

    # 4. Pipeline Construction
    num_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    cat_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(transformers=[
        ("num", num_transformer, numeric_features),
        ("cat", cat_transformer, categorical_features)
    ])

    # Classifier (Random Forest)
    # Balanced class weights help if 'hotspot' occurrences are rare in your data
    rf = RandomForestClassifier(
        n_estimators=250, 
        max_depth=12, 
        random_state=42, 
        class_weight="balanced", 
        n_jobs=-1
    )

    clf_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", rf)
    ])

    # 5. Split and Train
    print("🧠 Training Random Forest model...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf_pipeline.fit(X_train, y_train)
    y_pred = clf_pipeline.predict(X_test)

    # 6. Evaluate
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")
    report = classification_report(y_test, y_pred, target_names=le.classes_)

    print(f"📊 Training Results - Accuracy: {acc:.4f} | F1: {f1:.4f}")

    # 7. Unsupervised Anomaly Detection
    print("🚨 Fitting Anomaly Detection (Isolation Forest)...")
    anomaly_cols = ["congestion_index", "distance_km", "actual_travel_time_min", "avg_speed_kmph"]
    # Only use columns that exist in the dataframe
    actual_anom_cols = [c for c in anomaly_cols if c in df.columns]
    
    anom_data = df[actual_anom_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    anom_model = IsolationForest(contamination=0.04, random_state=42)
    anom_model.fit(anom_data)

    # 8. Artifact Serialization
    # We save EVERYTHING needed to reconstruct the prediction in one pkl
    model_artifact = {
        "pipeline": clf_pipeline,
        "label_encoder": le,
        "features": list(X.columns),
        "numeric_cols": numeric_features,
        "categorical_cols": categorical_features
    }

    metrics_artifact = {
        "accuracy": float(acc),
        "f1_weighted": float(f1),
        "precision_weighted": float(precision_score(y_test, y_pred, average="weighted")),
        "recall_weighted": float(recall_score(y_test, y_pred, average="weighted")),
        "classification_report": report,
        "target_classes": le.classes_.tolist()
    }

    joblib.dump(model_artifact, MODEL_PATH)
    joblib.dump(metrics_artifact, METRICS_PATH)
    joblib.dump({"model": anom_model, "features": actual_anom_cols}, ANOMALY_PATH)

    print(f"✅ Success! Artifacts saved to: {MODEL_DIR}")

if __name__ == "__main__":
    main()
