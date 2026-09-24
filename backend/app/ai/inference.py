from pathlib import Path
import joblib

from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
)


# --------------------------------------------------
# File Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

RISK_MODEL_DIR = (
    BASE_DIR /
    "models" /
    "risk_classifier"
)

SEVERITY_MODEL_DIR = (
    BASE_DIR /
    "models" /
    "severity_model"
)


# --------------------------------------------------
# Load DistilBERT
# --------------------------------------------------

print("Loading Risk Classification Model...")

risk_tokenizer = DistilBertTokenizerFast.from_pretrained(
    RISK_MODEL_DIR
)

risk_model = DistilBertForSequenceClassification.from_pretrained(
    RISK_MODEL_DIR
)

risk_label_encoder = joblib.load(
    RISK_MODEL_DIR / "label_encoder.pkl"
)

print("Risk Classification Model Loaded")


# --------------------------------------------------
# Load Severity Model
# --------------------------------------------------

print("Loading Severity Prediction Model...")

severity_model = joblib.load(
    SEVERITY_MODEL_DIR / "xgboost_severity.pkl"
)

tfidf_vectorizer = joblib.load(
    SEVERITY_MODEL_DIR / "tfidf_vectorizer.pkl"
)

category_encoder = joblib.load(
    SEVERITY_MODEL_DIR / "category_encoder.pkl"
)

location_encoder = joblib.load(
    SEVERITY_MODEL_DIR / "location_encoder.pkl"
)

industry_encoder = joblib.load(
    SEVERITY_MODEL_DIR / "industry_encoder.pkl"
)

severity_encoder = joblib.load(
    SEVERITY_MODEL_DIR / "severity_encoder.pkl"
)

print("Severity Prediction Model Loaded")


print("\nAll AI Models Loaded Successfully")

import torch


# --------------------------------------------------
# Predict Risk Category
# --------------------------------------------------

def predict_risk_category(event_description: str):
    """
    Predict the risk category using the trained DistilBERT model.
    """

    inputs = risk_tokenizer(
        event_description,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=128,
    )

    risk_model.eval()

    with torch.no_grad():
        outputs = risk_model(**inputs)

    predicted_class = torch.argmax(
        outputs.logits,
        dim=1
    ).item()

    predicted_category = risk_label_encoder.inverse_transform(
        [predicted_class]
    )[0]

    confidence = torch.softmax(
        outputs.logits,
        dim=1
    )[0][predicted_class].item()

    return {
        "category": predicted_category,
        "confidence": round(confidence, 4),
    }

# --------------------------------------------------
# Infer Industry
# --------------------------------------------------

def infer_industry(event_description: str):
    """
    Infer the affected industry from the event description.
    """

    text = event_description.lower()

    if any(word in text for word in [
        "semiconductor",
        "chip",
        "electronics"
    ]):
        return "Semiconductors"

    elif any(word in text for word in [
        "pharma",
        "medicine",
        "drug",
        "hospital"
    ]):
        return "Pharmaceuticals"

    elif any(word in text for word in [
        "food",
        "grain",
        "agriculture"
    ]):
        return "Food"

    elif any(word in text for word in [
        "oil",
        "gas",
        "fuel",
        "energy"
    ]):
        return "Energy"

    elif any(word in text for word in [
        "textile",
        "cotton",
        "garment"
    ]):
        return "Textiles"

    return "Logistics"

from scipy.sparse import hstack
import pandas as pd


# --------------------------------------------------
# Predict Severity
# --------------------------------------------------

def predict_severity(
    event_description: str,
    category: str,
    location: str,
):

    industry = infer_industry(event_description)

    text_features = tfidf_vectorizer.transform(
        [event_description]
    )

    # Encode category
    category_value = category_encoder.transform(
        [category]
    )[0]

    # Encode location safely
    if location not in location_encoder.classes_:
        location = location_encoder.classes_[0]

    location_value = location_encoder.transform(
        [location]
    )[0]

    # Encode industry safely
    if industry not in industry_encoder.classes_:
        industry = industry_encoder.classes_[0]

    industry_value = industry_encoder.transform(
        [industry]
    )[0]

    structured = pd.DataFrame({
        "category": [category_value],
        "location": [location_value],
        "industry": [industry_value],
    })

    X = hstack([
        text_features,
        structured.values
    ])

    prediction = severity_model.predict(X)

    severity = severity_encoder.inverse_transform(
        prediction
    )[0]

    return severity

# --------------------------------------------------
# Complete AI Prediction Pipeline
# --------------------------------------------------

def predict_event(
    event_description: str,
    location: str,
):
    """
    Complete AI prediction pipeline.

    Input:
        - Event Description
        - Location

    Output:
        - Category
        - Severity
        - Confidence
    """

    risk_result = predict_risk_category(event_description)

    severity = predict_severity(
        event_description,
        risk_result["category"],
        location,
    )

    return {
        "category": risk_result["category"],
        "severity": severity,
        "confidence": risk_result["confidence"],
    }
# --------------------------------------------------
# Test
# --------------------------------------------------

if __name__ == "__main__":

    sample_event = (
        "Heavy rainfall caused severe flooding near Shanghai Port."
    )

    location = "Shanghai, CN"

    result = predict_event(
        sample_event,
        location,
    )

    print("\nPrediction Result\n")

    print(result)