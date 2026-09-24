from pathlib import Path
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments,
)

from app.ai.dataset import SupplyChainDataset
from app.ai.utils import compute_metrics


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
    "risk_classifier"
)

MODEL_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# Load Dataset
# --------------------------------------------------

df = pd.read_csv(DATASET_PATH)

print(f"Dataset Loaded : {len(df)} records")


# --------------------------------------------------
# Features & Labels
# --------------------------------------------------

X = df["event_description"]

y = df["category"]


# --------------------------------------------------
# Label Encoding
# --------------------------------------------------

label_encoder = LabelEncoder()

y = label_encoder.fit_transform(y)

joblib.dump(
    label_encoder,
    MODEL_DIR / "label_encoder.pkl"
)

print("\nCategory Mapping\n")

for label, idx in zip(
    label_encoder.classes_,
    label_encoder.transform(label_encoder.classes_)
):
    print(f"{idx} -> {label}")


# --------------------------------------------------
# Train / Test Split
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(f"\nTraining Samples : {len(X_train)}")
print(f"Testing Samples  : {len(X_test)}")


# --------------------------------------------------
# Tokenizer
# --------------------------------------------------

print("\nLoading DistilBERT Tokenizer...")

tokenizer = DistilBertTokenizerFast.from_pretrained(
    "distilbert-base-uncased"
)

train_encodings = tokenizer(
    X_train.tolist(),
    truncation=True,
    padding=True,
    max_length=128,
)

test_encodings = tokenizer(
    X_test.tolist(),
    truncation=True,
    padding=True,
    max_length=128,
)

print("Tokenization Completed")


# --------------------------------------------------
# PyTorch Dataset
# --------------------------------------------------

train_dataset = SupplyChainDataset(
    train_encodings,
    y_train
)

test_dataset = SupplyChainDataset(
    test_encodings,
    y_test
)


# --------------------------------------------------
# Load DistilBERT
# --------------------------------------------------

print("\nLoading DistilBERT Model...")

model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=len(label_encoder.classes_)
)

print("Model Loaded Successfully")


# --------------------------------------------------
# Training Arguments
# --------------------------------------------------

training_args = TrainingArguments(
    output_dir=str(MODEL_DIR),
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
    load_best_model_at_end=True,
    report_to="none",
)


# --------------------------------------------------
# Trainer
# --------------------------------------------------

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
)


# --------------------------------------------------
# Train
# --------------------------------------------------

print("\nTraining Started...\n")

trainer.train()

print("\nTraining Completed Successfully")


# --------------------------------------------------
# Evaluation
# --------------------------------------------------

results = trainer.evaluate()

print("\nEvaluation Results\n")

for key, value in results.items():
    print(f"{key} : {value}")


# --------------------------------------------------
# Save Model
# --------------------------------------------------

model.save_pretrained(MODEL_DIR)

tokenizer.save_pretrained(MODEL_DIR)

print("\nModel Saved Successfully")

print(f"\nLocation : {MODEL_DIR}")