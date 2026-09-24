from pathlib import Path
import pandas as pd


# --------------------------------------------------
# File Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DATASET = (
    BASE_DIR /
    "datasets" /
    "historical" /
    "global_supply_chain_disruption_v1.csv"
)

OUTPUT_DIR = (
    BASE_DIR /
    "datasets" /
    "processed"
)

OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_DATASET = OUTPUT_DIR / "training_dataset.csv"


# --------------------------------------------------
# Load Dataset
# --------------------------------------------------

df = pd.read_csv(RAW_DATASET)

print(f"Loaded {len(df)} records")


# --------------------------------------------------
# Remove Duplicate Records
# --------------------------------------------------

df = df.drop_duplicates()

print(f"After removing duplicates: {len(df)} records")


# --------------------------------------------------
# Remove Missing Values
# --------------------------------------------------

required_columns = [
    "Transportation_Mode",
    "Origin_City",
    "Product_Category",
    "Delay_Days",
    "Weather_Severity_Index",
    "Geopolitical_Risk_Index"
]

df = df.dropna(subset=required_columns)

print(f"After removing missing values: {len(df)} records")


# --------------------------------------------------
# Create Training Dataset
# --------------------------------------------------

training_df = pd.DataFrame()


# --------------------------------------------------
# Generate Event Description
# --------------------------------------------------

def generate_event_description(row):
    disruption = row["Disruption_Event"]

    if pd.isna(disruption) or str(disruption).strip() == "":
        disruption = "No Major Disruption"

    return (
        f"{row['Transportation_Mode']} shipment from "
        f"{row['Origin_City']} transporting "
        f"{row['Product_Category']} experienced "
        f"{disruption} with a delay of "
        f"{int(row['Delay_Days'])} days."
    )


training_df["event_description"] = df.apply(
    generate_event_description,
    axis=1
)


# --------------------------------------------------
# Generate Risk Category
# --------------------------------------------------

def generate_category(row):

    disruption = str(row["Disruption_Event"]).lower()

    geo_risk = row["Geopolitical_Risk_Index"]
    weather = row["Weather_Severity_Index"]
    inflation = row["Inflation_Rate_Pct"]
    delay = row["Delay_Days"]

    # Natural Disaster
    if (
        weather >= 8
        or "weather" in disruption
        or "storm" in disruption
        or "typhoon" in disruption
        or "flood" in disruption
        or "hurricane" in disruption
    ):
        return "Natural Disaster"

    # Political
    elif (
        geo_risk >= 7
        or "geopolitical" in disruption
        or "conflict" in disruption
        or "war" in disruption
        or "sanction" in disruption
    ):
        return "Political"

    # Supplier
    elif (
        "supplier" in disruption
        or "bankruptcy" in disruption
        or "factory" in disruption
        or "production" in disruption
    ):
        return "Supplier"

    # Financial
    elif (
        inflation >= 6
        or "inflation" in disruption
        or "fuel" in disruption
        or "financial" in disruption
        or "price" in disruption
    ):
        return "Financial"

    # Transportation
    elif (
        delay >= 4
        or "port" in disruption
        or "congestion" in disruption
        or "shipping" in disruption
        or "transport" in disruption
        or "delay" in disruption
    ):
        return "Transportation"

    return "Transportation"


training_df["category"] = df.apply(
    generate_category,
    axis=1
)


training_df["location"] = df["Origin_City"]

training_df["industry"] = df["Product_Category"]

training_df["source"] = "Historical Dataset"


# --------------------------------------------------
# Generate Severity Label
# --------------------------------------------------

def calculate_severity(row):

    if (
        row["Delay_Days"] >= 10
        or row["Weather_Severity_Index"] >= 8
        or row["Geopolitical_Risk_Index"] >= 8
    ):
        return "High"

    elif (
        row["Delay_Days"] >= 4
        or row["Weather_Severity_Index"] >= 5
        or row["Geopolitical_Risk_Index"] >= 5
    ):
        return "Medium"

    return "Low"


training_df["severity"] = df.apply(
    calculate_severity,
    axis=1
)


# --------------------------------------------------
# Reorder Columns
# --------------------------------------------------

training_df = training_df[
    [
        "event_description",
        "category",
        "severity",
        "location",
        "industry",
        "source",
    ]
]


# --------------------------------------------------
# Save Dataset
# --------------------------------------------------

training_df.to_csv(
    OUTPUT_DATASET,
    index=False,
)

print("\nTraining Dataset Created Successfully\n")

print(training_df.head())