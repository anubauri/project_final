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
    classification_report,
    confusion_matrix
)

warnings.filterwarnings("ignore")

# Path Configurations
BASE_DIR = "/content/smart_city_app"
DATA_PATH = f"{BASE_DIR}/dataset/final_preprocessed_dataset.csv"
MODEL_DIR = f"{BASE_DIR}/model"
MODEL_PATH = f"{MODEL_DIR}/final_random_forest_model.pkl"
METRICS_PATH = f"{MODEL_DIR}/metrics.pkl"
ANOMALY_PATH = f"{MODEL_DIR}/anomaly_model.pkl"

TARGET_COLUMN = "hotspot"

def parse_time_of_day(value):
    """Safely converts time strings or categories to numeric hour proxies."""
    if pd.isna(value):
        return 12.0 # Default to midday if unknown
    val = str(value).strip().lower()
    mapping = {
        "early morning": 5,
        "morning": 8,
        "late morning": 11,
        "afternoon": 14,
        "evening": 18,
        "night": 21,
        "late night": 23
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
    """
    Creates consistent features used by both the training script 
    and the predictor.py module in Streamlit.
    """
    df = df.copy()

    # 1. Date Features
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["month"] = df["date"].dt.month.fillna(0)
        df["day"] = df["date"].dt.day.fillna(0)
        df["is_weekend"] = df["date"].dt.dayofweek.isin([5, 6]).astype(int)
    else:
        df["month"], df["day"], df["is_weekend"] = 0, 0, 0

    # 2. Time Features
    if "time_of_day" in df.columns:
        df["hour_proxy"] = df["time_of_day"].apply(parse_time_of_day)
    else:
        df["hour_proxy"] = 12.0

    # 3. Route Features
    if "source" in df.columns and "destination" in df.columns:
        df["same_zone_trip"] = (df["source"].astype(str) == df["destination"].astype(str)).astype(int)
    else:
        df["same_zone_trip"] = 0

    # 4. Traffic Metrics
    if "distance_km" in df.columns and "actual_travel_time_min" in df.columns:
        dist = pd.to_numeric(df["distance_km"], errors="coerce").fillna(0)
        tt = pd.to_numeric(df["actual_travel_time_min"], errors="coerce").fillna(0)
        # Avoid division by zero
        df["avg_speed_kmph"] = np.where(tt > 0, dist / (tt / 60.0), 0)
        df["delay_per_km"] = np.where(dist > 0, tt / dist, 0)
    else:
        df["avg_speed_kmph"], df["delay_per_km"] = 0, 0

    # 5. Flags
    if "festival" in df.columns:
        df["festival_binary"] = df["festival"].astype(str).str.lower().isin(
            ["yes", "true", "1", "festival", "high", "major"]
        ).astype(int)
    else:
        df["festival_binary"] = 0

    if "weather" in df.columns:
        df["bad_weather_flag"] = df["weather"].astype(str).str.lower().isin(
            ["rain", "storm", "heavy rain", "fog"]
        ).astype(int)
    else:
        df["bad_weather_flag"] = 0

    return df

def main():
    # Ensure directories exist
    os.makedirs(MODEL_DIR, exist_ok=True)

    if not os.path.exists(DATA_PATH):
        print(f"ERROR: Dataset not found at {DATA_PATH}")
        return

    # Load and clean column names
    df = pd.read_csv(DATA_PATH)
    df.columns = [c.strip() for c in df.columns]

    if TARGET_COLUMN not in df.columns:
        print(f"ERROR: Target '{TARGET_COLUMN}' missing from CSV.")
        return

    # Apply Engineering
    df = add_engineered_features(df)

    # Define features to exclude from X
    exclude_cols = [TARGET_COLUMN, "date", "route"] # 'route' is often too high-cardinality
    y_raw = df[TARGET_COLUMN].astype(str).fillna("unknown")
    X = df.drop(columns=[c for c in exclude_cols if c in df.columns], errors="ignore")

    # Encode Target
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_raw)

    # Separate column types
    numeric_cols = X.select_dtypes(include=["int64", "float64", "int32", "float32"]).columns.tolist()
    categorical_cols = [c for c in X.columns if c not in numeric_cols]

    # Preprocessing Pipelines
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(transformers=[
        ("num", numeric_transformer, numeric_cols),
        ("cat", categorical_transformer, categorical_cols)
    ])

    # Model Definition
    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )

    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", rf_model)
    ])

    # Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Fit Pipeline
    print("Fitting model...")
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    # Save Metrics for the 'About' page
    metrics_data = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1_weighted": float(f1_score(y_test, y_pred, average="weighted")),
        "classification_report": classification_report(y_test, y_pred, target_names=label_encoder.classes_.astype(str)),
        "feature_columns": list(X.columns),
        "target_classes": list(label_encoder.classes_)
    }

    # Save Artifact for Predictor
    artifact = {
        "pipeline": pipeline,
        "label_encoder": label_encoder,
        "feature_columns": list(X.columns), # CRITICAL: Streamlit needs this list
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols
    }

    # Anomaly Detection Training
    anomaly_features = ["distance_km", "congestion_index", "actual_travel_time_min", "avg_speed_kmph"]
    # Check which features actually exist
    existing_anom_feats = [f for f in anomaly_features if f in df.columns]
    
    anomaly_df = df[existing_anom_feats].copy()
    anomaly_df = anomaly_df.apply(pd.to_numeric, errors='coerce').fillna(0)
    
    anomaly_model = IsolationForest(contamination=0.05, random_state=42)
    anomaly_model.fit(anomaly_df)

    # Final Exports
    joblib.dump(artifact, MODEL_PATH)
    joblib.dump(metrics_data, METRICS_PATH)
    joblib.dump({"model": anomaly_model, "features": existing_anom_feats}, ANOMALY_PATH)

    print(f"✅ Success! Accuracy: {metrics_data['accuracy']:.4f}")
    print(f"Files saved in {MODEL_DIR}")

if __name__ == "__main__":
    main()