import time
from pathlib import Path

import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)

from torch.optim import AdamW
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "distilbert-base-uncased"

TRAIN_PATH = Path("datasets/relevance/relevance_train.csv")
VAL_PATH = Path("datasets/relevance/relevance_val.csv")

MODEL_DIR = Path("models/relevance_distilbert")

MAX_LENGTH = 128
BATCH_SIZE = 8
EPOCHS = 3
LEARNING_RATE = 2e-5

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ============================================================
# DATASET CLASS
# ============================================================

class RelevanceDataset(Dataset):

    def __init__(self, dataframe, tokenizer):

        self.texts = dataframe["text"].tolist()
        self.labels = dataframe["label"].astype(int).tolist()
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, index):

        text = self.texts[index]
        label = self.labels[index]

        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=MAX_LENGTH,
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(label, dtype=torch.long),
        }


# ============================================================
# LOAD DATA
# ============================================================

print("\n==================================================")
print("       DISTILBERT RELEVANCE MODEL TRAINING")
print("==================================================")

print(f"\nDevice : {DEVICE}")

train_df = pd.read_csv(TRAIN_PATH)
val_df = pd.read_csv(VAL_PATH)

print(f"Training samples   : {len(train_df)}")
print(f"Validation samples : {len(val_df)}")

print("\nTraining distribution:")
print(train_df["label"].value_counts())

print("\nValidation distribution:")
print(val_df["label"].value_counts())


# ============================================================
# LOAD TOKENIZER
# ============================================================

print("\nLoading DistilBERT tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print("Tokenizer loaded successfully.")


# ============================================================
# CREATE DATASETS
# ============================================================

train_dataset = RelevanceDataset(
    train_df,
    tokenizer
)

val_dataset = RelevanceDataset(
    val_df,
    tokenizer
)


train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading DistilBERT classification model...")

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=2
)

model.to(DEVICE)

print("Model loaded successfully.")


# ============================================================
# OPTIMIZER
# ============================================================

optimizer = AdamW(
    model.parameters(),
    lr=LEARNING_RATE
)


# ============================================================
# TRAINING
# ============================================================

print("\n==================================================")
print("Starting training...")
print("==================================================")

start_time = time.time()

for epoch in range(EPOCHS):

    model.train()

    total_loss = 0

    for batch in train_loader:

        input_ids = batch["input_ids"].to(DEVICE)
        attention_mask = batch["attention_mask"].to(DEVICE)
        labels = batch["labels"].to(DEVICE)

        optimizer.zero_grad()

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )

        loss = outputs.loss

        loss.backward()

        optimizer.step()

        total_loss += loss.item()

    average_loss = total_loss / len(train_loader)

    print(
        f"Epoch {epoch + 1}/{EPOCHS} "
        f"| Training Loss: {average_loss:.4f}"
    )


# ============================================================
# VALIDATION
# ============================================================

print("\n==================================================")
print("Evaluating model...")
print("==================================================")

model.eval()

predictions = []
actual_labels = []

with torch.no_grad():

    for batch in val_loader:

        input_ids = batch["input_ids"].to(DEVICE)
        attention_mask = batch["attention_mask"].to(DEVICE)
        labels = batch["labels"].to(DEVICE)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )

        logits = outputs.logits

        preds = torch.argmax(
            logits,
            dim=1
        )

        predictions.extend(
            preds.cpu().numpy()
        )

        actual_labels.extend(
            labels.cpu().numpy()
        )


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    actual_labels,
    predictions
)

precision, recall, f1, _ = precision_recall_fscore_support(
    actual_labels,
    predictions,
    average="binary",
    zero_division=0
)

print("\n==================================================")
print("MODEL EVALUATION")
print("==================================================")

print(f"Accuracy  : {accuracy:.4f}")
print(f"Precision : {precision:.4f}")
print(f"Recall    : {recall:.4f}")
print(f"F1 Score  : {f1:.4f}")

print("==================================================")


# ============================================================
# SAVE MODEL
# ============================================================

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

print("\nSaving trained model...")

model.save_pretrained(MODEL_DIR)

tokenizer.save_pretrained(MODEL_DIR)

print(f"Model saved to : {MODEL_DIR}")


# ============================================================
# TRAINING SUMMARY
# ============================================================

training_time = time.time() - start_time

print("\n==================================================")
print("TRAINING COMPLETED")
print("==================================================")

print(f"Training time : {training_time:.2f} seconds")
print(f"Accuracy      : {accuracy:.4f}")
print(f"Precision     : {precision:.4f}")
print(f"Recall        : {recall:.4f}")
print(f"F1 Score      : {f1:.4f}")
print(f"Model path    : {MODEL_DIR}")

print("\nSUCCESS: Relevance DistilBERT model trained.")
print("==================================================")