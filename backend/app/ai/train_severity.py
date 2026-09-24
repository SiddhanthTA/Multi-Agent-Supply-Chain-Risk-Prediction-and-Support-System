from pathlib import Path
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack

from xgboost import XGBClassifier
from sklearn.metrics import classification_report, accuracy_score


# --------------------------------------------------
# File Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    BASE_DIR /
    "datasets" /
    "ai" /
    "supply_chain_ai_dataset.csv"
)

MODEL_DIR = (
    BASE_DIR /
    "models" /
    "severity_model"
)

MODEL_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# Load Dataset
# --------------------------------------------------

df = pd.read_csv(DATASET_PATH)

print(f"Dataset Loaded : {len(df)} records")


# --------------------------------------------------
# Feature Selection
# --------------------------------------------------

text = df["event_description"]

category = df["category"]

location = df["location"]

industry = df["industry"]

target = df["severity"]


# --------------------------------------------------
# Encode Category
# --------------------------------------------------

category_encoder = LabelEncoder()

category = category_encoder.fit_transform(category)

joblib.dump(
    category_encoder,
    MODEL_DIR / "category_encoder.pkl"
)


# --------------------------------------------------
# Encode Location
# --------------------------------------------------

location_encoder = LabelEncoder()

location = location_encoder.fit_transform(location)

joblib.dump(
    location_encoder,
    MODEL_DIR / "location_encoder.pkl"
)


# --------------------------------------------------
# Encode Industry
# --------------------------------------------------

industry_encoder = LabelEncoder()

industry = industry_encoder.fit_transform(industry)

joblib.dump(
    industry_encoder,
    MODEL_DIR / "industry_encoder.pkl"
)


# --------------------------------------------------
# Encode Severity
# --------------------------------------------------

severity_encoder = LabelEncoder()

target = severity_encoder.fit_transform(target)

joblib.dump(
    severity_encoder,
    MODEL_DIR / "severity_encoder.pkl"
)


# --------------------------------------------------
# TF-IDF
# --------------------------------------------------

vectorizer = TfidfVectorizer(
    max_features=500
)

text_features = vectorizer.fit_transform(text)

joblib.dump(
    vectorizer,
    MODEL_DIR / "tfidf_vectorizer.pkl"
)


# --------------------------------------------------
# Combine Features
# --------------------------------------------------

structured_features = pd.DataFrame({
    "category": category,
    "location": location,
    "industry": industry
})

X = hstack([
    text_features,
    structured_features.values
])

y = target


# --------------------------------------------------
# Train Test Split
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(f"Training Samples : {X_train.shape[0]}")
print(f"Testing Samples  : {X_test.shape[0]}")


# --------------------------------------------------
# XGBoost Model
# --------------------------------------------------

model = XGBClassifier(
    objective="multi:softprob",
    num_class=3,
    n_estimators=200,
    learning_rate=0.1,
    max_depth=6,
    random_state=42,
    eval_metric="mlogloss"
)


# --------------------------------------------------
# Train
# --------------------------------------------------

print("\nTraining Severity Model...\n")

model.fit(
    X_train,
    y_train
)


# --------------------------------------------------
# Prediction
# --------------------------------------------------

predictions = model.predict(
    X_test
)


# --------------------------------------------------
# Evaluation
# --------------------------------------------------

print("\nAccuracy :")

print(
    accuracy_score(
        y_test,
        predictions
    )
)

print("\nClassification Report\n")

print(
    classification_report(
        y_test,
        predictions,
        target_names=severity_encoder.classes_
    )
)


# --------------------------------------------------
# Save Model
# --------------------------------------------------

joblib.dump(
    model,
    MODEL_DIR / "xgboost_severity.pkl"
)

print("\nSeverity Model Saved Successfully")