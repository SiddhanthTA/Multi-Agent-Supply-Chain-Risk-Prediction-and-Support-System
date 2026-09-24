import pandas as pd
from pathlib import Path

DATASET_PATH = Path("datasets/relevance/relevance_dataset.csv")

df = pd.read_csv(DATASET_PATH)

print("\n========== DATASET VALIDATION ==========")

print(f"Total samples : {len(df)}")

print("\nClass distribution:")
print(df["label"].value_counts())

print("\nClass percentages:")
print(df["label"].value_counts(normalize=True).mul(100).round(2))

print("\nMissing values:")
print(df.isnull().sum())

print(f"\nDuplicate texts : {df['text'].duplicated().sum()}")

print("\nLabel values:")
print(sorted(df["label"].unique()))

print("\nSample data:")
print(df.head())

print("\n========================================")

if set(df["label"].unique()) != {0, 1}:
    print("ERROR: Dataset must contain both labels 0 and 1.")
elif df["text"].isnull().any() or df["label"].isnull().any():
    print("ERROR: Dataset contains missing values.")
elif df["text"].duplicated().sum() > 0:
    print("WARNING: Duplicate texts found.")
else:
    print("SUCCESS: Dataset is ready for training.")