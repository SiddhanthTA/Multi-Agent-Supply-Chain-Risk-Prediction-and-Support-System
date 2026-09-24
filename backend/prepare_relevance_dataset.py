import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

# --------------------------------------------------
# PATHS
# --------------------------------------------------

INPUT_PATH = Path("datasets/relevance/relevance_dataset.csv")
HARD_EXAMPLES_PATH = Path("datasets/relevance/relevance_hard_examples.csv")

OUTPUT_DIR = Path("datasets/relevance")

CLEAN_PATH = OUTPUT_DIR / "relevance_clean.csv"
TRAIN_PATH = OUTPUT_DIR / "relevance_train.csv"
VAL_PATH = OUTPUT_DIR / "relevance_val.csv"

# --------------------------------------------------
# LOAD DATASETS
# --------------------------------------------------

print("\n========== PREPARING RELEVANCE DATASET ==========")

print("\nLoading original dataset...")
df_original = pd.read_csv(INPUT_PATH)

print(f"Original samples : {len(df_original)}")

print("\nLoading hard-example dataset...")
df_hard = pd.read_csv(HARD_EXAMPLES_PATH)

print(f"Hard examples    : {len(df_hard)}")

# --------------------------------------------------
# COMBINE DATASETS
# --------------------------------------------------

df = pd.concat(
    [df_original, df_hard],
    ignore_index=True
)

print(f"\nCombined samples : {len(df)}")

# --------------------------------------------------
# REMOVE MISSING VALUES
# --------------------------------------------------

before = len(df)

df = df.dropna(
    subset=["text", "label"]
)

missing_removed = before - len(df)

print(f"Missing samples removed : {missing_removed}")

# --------------------------------------------------
# NORMALIZE DATA
# --------------------------------------------------

df["text"] = (
    df["text"]
    .astype(str)
    .str.strip()
)

df["label"] = (
    pd.to_numeric(df["label"], errors="coerce")
)

df = df.dropna(
    subset=["label"]
)

df["label"] = df["label"].astype(int)

# --------------------------------------------------
# VALIDATE LABELS
# --------------------------------------------------

valid_labels = {0, 1}

invalid_labels = set(df["label"].unique()) - valid_labels

if invalid_labels:
    raise ValueError(
        f"Invalid labels found: {invalid_labels}. "
        f"Only 0 and 1 are allowed."
    )

# --------------------------------------------------
# REMOVE EMPTY TEXT
# --------------------------------------------------

before = len(df)

df = df[df["text"].str.len() > 0]

empty_removed = before - len(df)

print(f"Empty texts removed : {empty_removed}")

# --------------------------------------------------
# REMOVE DUPLICATES
# --------------------------------------------------

before = len(df)

df = df.drop_duplicates(
    subset=["text"],
    keep="first"
)

duplicates_removed = before - len(df)

print(f"Duplicates removed : {duplicates_removed}")
print(f"Samples after cleaning : {len(df)}")

# --------------------------------------------------
# CLASS DISTRIBUTION
# --------------------------------------------------

print("\nClass distribution before balancing:")
print(
    df["label"]
    .value_counts()
    .sort_index()
)

# --------------------------------------------------
# CHECK BOTH CLASSES EXIST
# --------------------------------------------------

class_counts = df["label"].value_counts()

if len(class_counts) != 2:
    raise ValueError(
        "Dataset must contain both label 0 and label 1."
    )

# --------------------------------------------------
# BALANCE DATASET
# --------------------------------------------------

minimum_count = class_counts.min()

balanced_parts = []

for label in sorted(df["label"].unique()):

    class_data = df[
        df["label"] == label
    ]

    class_data = class_data.sample(
        n=minimum_count,
        random_state=42
    )

    balanced_parts.append(
        class_data
    )

df = pd.concat(
    balanced_parts,
    ignore_index=True
)

# --------------------------------------------------
# SHUFFLE
# --------------------------------------------------

df = df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

# --------------------------------------------------
# BALANCED DISTRIBUTION
# --------------------------------------------------

print("\nClass distribution after balancing:")
print(
    df["label"]
    .value_counts()
    .sort_index()
)

print(f"\nFinal samples : {len(df)}")

# --------------------------------------------------
# SAVE CLEAN DATASET
# --------------------------------------------------

df.to_csv(
    CLEAN_PATH,
    index=False
)

# --------------------------------------------------
# TRAIN / VALIDATION SPLIT
# --------------------------------------------------

train_df, val_df = train_test_split(
    df,
    test_size=0.20,
    random_state=42,
    stratify=df["label"]
)

# --------------------------------------------------
# SHUFFLE TRAIN / VALIDATION
# --------------------------------------------------

train_df = train_df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

val_df = val_df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

# --------------------------------------------------
# SAVE TRAIN DATASET
# --------------------------------------------------

train_df.to_csv(
    TRAIN_PATH,
    index=False
)

# --------------------------------------------------
# SAVE VALIDATION DATASET
# --------------------------------------------------

val_df.to_csv(
    VAL_PATH,
    index=False
)

# --------------------------------------------------
# FINAL SUMMARY
# --------------------------------------------------

print("\n========== DATASET SPLIT ==========")

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

print("\nFiles created:")
print(
    f"Clean dataset : {CLEAN_PATH}"
)

print(
    f"Train dataset : {TRAIN_PATH}"
)

print(
    f"Validation dataset : {VAL_PATH}"
)

print(
    "\nSUCCESS: Dataset is ready for DistilBERT training."
)

print("==============================================\n")