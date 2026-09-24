import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

# ============================================================
# PATHS
# ============================================================

INPUT_PATH = Path("datasets/impact/impact_dataset.csv")
OUTPUT_DIR = Path("datasets/impact")

CLEAN_PATH = OUTPUT_DIR / "impact_clean.csv"
TRAIN_PATH = OUTPUT_DIR / "impact_train.csv"
VAL_PATH = OUTPUT_DIR / "impact_val.csv"


# ============================================================
# LOAD DATASET
# ============================================================

print("\n" + "=" * 60)
print("PREPARING SUPPLY-CHAIN IMPACT DATASET")
print("=" * 60)

print("\nLoading dataset...")

df = pd.read_csv(INPUT_PATH)

print(f"Original samples : {len(df)}")


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

required_columns = ["text", "label"]

for column in required_columns:

    if column not in df.columns:
        raise ValueError(
            f"Required column missing: {column}"
        )


# ============================================================
# REMOVE MISSING VALUES
# ============================================================

before = len(df)

df = df.dropna(
    subset=["text", "label"]
)

missing_removed = before - len(df)

print(
    f"Missing samples removed : "
    f"{missing_removed}"
)


# ============================================================
# REMOVE EMPTY TEXT
# ============================================================

df["text"] = (
    df["text"]
    .astype(str)
    .str.strip()
)

before = len(df)

df = df[df["text"] != ""]

empty_removed = before - len(df)

print(
    f"Empty texts removed : "
    f"{empty_removed}"
)


# ============================================================
# NORMALIZE LABELS
# ============================================================

df["label"] = df["label"].astype(int)


# ============================================================
# VALIDATE LABEL VALUES
# ============================================================

valid_labels = {0, 1, 2}

invalid_labels = set(
    df["label"].unique()
) - valid_labels

if invalid_labels:

    raise ValueError(
        f"Invalid label values found: "
        f"{invalid_labels}"
    )


# ============================================================
# REMOVE DUPLICATES
# ============================================================

before = len(df)

df = df.drop_duplicates(
    subset=["text"],
    keep="first"
)

duplicates_removed = before - len(df)

print(
    f"Duplicates removed : "
    f"{duplicates_removed}"
)


# ============================================================
# SHUFFLE DATASET
# ============================================================

df = df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)


# ============================================================
# CLASS DISTRIBUTION
# ============================================================

print("\nClass distribution:")

print(
    df["label"]
    .value_counts()
    .sort_index()
)


# ============================================================
# CLASS PERCENTAGES
# ============================================================

print("\nClass percentages:")

print(
    (
        df["label"]
        .value_counts(normalize=True)
        .sort_index()
        * 100
    ).round(2)
)


# ============================================================
# SAVE CLEAN DATASET
# ============================================================

df.to_csv(
    CLEAN_PATH,
    index=False
)


# ============================================================
# TRAIN / VALIDATION SPLIT
# ============================================================

train_df, val_df = train_test_split(
    df,
    test_size=0.20,
    random_state=42,
    stratify=df["label"]
)


# ============================================================
# SAVE TRAINING DATASET
# ============================================================

train_df.to_csv(
    TRAIN_PATH,
    index=False
)


# ============================================================
# SAVE VALIDATION DATASET
# ============================================================

val_df.to_csv(
    VAL_PATH,
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("DATASET SPLIT")
print("=" * 60)

print(
    f"Training samples   : "
    f"{len(train_df)}"
)

print(
    f"Validation samples : "
    f"{len(val_df)}"
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
# FILE INFORMATION
# ============================================================

print("\nFiles created:")

print(
    f"Clean dataset : "
    f"{CLEAN_PATH}"
)

print(
    f"Train dataset : "
    f"{TRAIN_PATH}"
)

print(
    f"Validation dataset : "
    f"{VAL_PATH}"
)


print(
    "\nSUCCESS: "
    "Impact dataset is ready for training."
)

print("=" * 60)