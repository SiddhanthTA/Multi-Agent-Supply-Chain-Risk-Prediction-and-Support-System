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
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)


# ============================================================
# CONFIGURATION
# ============================================================

TRAIN_PATH = Path(
    "datasets/impact/impact_train.csv"
)

VAL_PATH = Path(
    "datasets/impact/impact_val.csv"
)

MODEL_NAME = "distilbert-base-uncased"

OUTPUT_DIR = Path(
    "models/impact_distilbert"
)

NUM_LABELS = 3

MAX_LENGTH = 256

BATCH_SIZE = 8

EPOCHS = 3

LEARNING_RATE = 2e-5

RANDOM_SEED = 42


# ============================================================
# REPRODUCIBILITY
# ============================================================

torch.manual_seed(RANDOM_SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(RANDOM_SEED)


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

print("\n" + "=" * 60)
print("IMPACT DISTILBERT TRAINING")
print("=" * 60)

print(f"\nDevice : {device}")


# ============================================================
# LOAD DATASET
# ============================================================

train_df = pd.read_csv(
    TRAIN_PATH
)

val_df = pd.read_csv(
    VAL_PATH
)

print(
    f"Training samples   : {len(train_df)}"
)

print(
    f"Validation samples : {len(val_df)}"
)

print("\nTraining distribution:")
print(
    train_df["label"]
    .value_counts()
    .sort_index()
)

print("\nValidation distribution:")
print(
    val_df["label"]
    .value_counts()
    .sort_index()
)


# ============================================================
# DATASET CLASS
# ============================================================

class ImpactDataset(Dataset):

    def __init__(
        self,
        dataframe,
        tokenizer,
        max_length=256,
    ):

        self.texts = (
            dataframe["text"]
            .astype(str)
            .tolist()
        )

        self.labels = (
            dataframe["label"]
            .astype(int)
            .tolist()
        )

        self.tokenizer = tokenizer

        self.max_length = max_length

    def __len__(self):

        return len(self.texts)

    def __getitem__(self, index):

        text = self.texts[index]

        label = self.labels[index]

        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )

        item = {
            key: value.squeeze(0)
            for key, value in encoding.items()
        }

        item["labels"] = torch.tensor(
            label,
            dtype=torch.long,
        )

        return item


# ============================================================
# LOAD TOKENIZER
# ============================================================

print(
    "\nLoading DistilBERT tokenizer..."
)

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

print(
    "Tokenizer loaded successfully."
)


# ============================================================
# CREATE DATASETS
# ============================================================

train_dataset = ImpactDataset(
    train_df,
    tokenizer,
    MAX_LENGTH,
)

val_dataset = ImpactDataset(
    val_df,
    tokenizer,
    MAX_LENGTH,
)


# ============================================================
# CREATE DATALOADERS
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
)


# ============================================================
# LOAD MODEL
# ============================================================

print(
    "\nLoading DistilBERT classification model..."
)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=NUM_LABELS,
)

model.to(device)

print(
    "Model loaded successfully."
)


# ============================================================
# OPTIMIZER
# ============================================================

optimizer = AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
)


# ============================================================
# TRAINING
# ============================================================

print(
    "\nStarting training..."
)

start_time = time.time()

model.train()

for epoch in range(EPOCHS):

    total_loss = 0.0

    for batch in train_loader:

        batch = {
            key: value.to(device)
            for key, value in batch.items()
        }

        optimizer.zero_grad()

        outputs = model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            labels=batch["labels"],
        )

        loss = outputs.loss

        total_loss += loss.item()

        loss.backward()

        optimizer.step()

    average_loss = (
        total_loss / len(train_loader)
    )

    print(
        f"Epoch {epoch + 1}/{EPOCHS} | "
        f"Training Loss: {average_loss:.4f}"
    )


# ============================================================
# VALIDATION
# ============================================================

print(
    "\nEvaluating model..."
)

model.eval()

true_labels = []

predicted_labels = []

with torch.no_grad():

    for batch in val_loader:

        labels = batch["labels"].to(device)

        inputs = {
            "input_ids":
                batch["input_ids"].to(device),

            "attention_mask":
                batch["attention_mask"].to(device),
        }

        outputs = model(
            **inputs
        )

        predictions = torch.argmax(
            outputs.logits,
            dim=1,
        )

        true_labels.extend(
            labels.cpu().numpy()
        )

        predicted_labels.extend(
            predictions.cpu().numpy()
        )


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    true_labels,
    predicted_labels,
)

precision = precision_score(
    true_labels,
    predicted_labels,
    average="weighted",
    zero_division=0,
)

recall = recall_score(
    true_labels,
    predicted_labels,
    average="weighted",
    zero_division=0,
)

f1 = f1_score(
    true_labels,
    predicted_labels,
    average="weighted",
    zero_division=0,
)


# ============================================================
# SAVE MODEL
# ============================================================

print(
    "\nSaving trained model..."
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

model.save_pretrained(
    OUTPUT_DIR
)

tokenizer.save_pretrained(
    OUTPUT_DIR
)


# ============================================================
# FINAL RESULTS
# ============================================================

training_time = (
    time.time() - start_time
)

print(
    f"\nTraining time : "
    f"{training_time:.2f} seconds"
)

print(
    f"Accuracy      : "
    f"{accuracy:.4f}"
)

print(
    f"Precision     : "
    f"{precision:.4f}"
)

print(
    f"Recall        : "
    f"{recall:.4f}"
)

print(
    f"F1 Score      : "
    f"{f1:.4f}"
)

print(
    f"Model path    : "
    f"{OUTPUT_DIR}"
)

print(
    "\n# SUCCESS: "
    "Impact DistilBERT model trained."
)

print("=" * 60)