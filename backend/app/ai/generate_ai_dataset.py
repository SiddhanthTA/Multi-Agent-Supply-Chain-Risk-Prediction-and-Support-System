from pathlib import Path
import random
import pandas as pd
from faker import Faker

fake = Faker()


# --------------------------------------------------
# File Path
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "datasets" / "ai"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "supply_chain_ai_dataset.csv"


# --------------------------------------------------
# Categories
# --------------------------------------------------

CATEGORIES = {
    "Natural Disaster": [
        "Heavy rainfall caused severe flooding near {location}, delaying shipments.",
        "A powerful typhoon disrupted logistics operations in {location}.",
        "Earthquake damaged transportation infrastructure around {location}.",
        "Cyclone interrupted cargo movement across {location}.",
        "Flooding forced temporary closure of warehouses in {location}."
    ],

    "Transportation": [
        "Port congestion delayed container shipments in {location}.",
        "Truck drivers' strike disrupted deliveries in {location}.",
        "Railway maintenance delayed cargo transportation in {location}.",
        "Airport cargo operations were suspended in {location}.",
        "Shipping vessel breakdown caused delivery delays near {location}."
    ],

    "Supplier": [
        "Major supplier bankruptcy affected manufacturing in {location}.",
        "Raw material shortage disrupted production in {location}.",
        "Supplier failed to deliver critical components to factories.",
        "Factory shutdown caused supply shortages in {location}.",
        "Component supplier unexpectedly halted production."
    ],

    "Political": [
        "Trade sanctions disrupted exports from {location}.",
        "Political conflict interrupted cross-border transportation.",
        "Border restrictions delayed international shipments.",
        "Government policy changes affected import operations.",
        "Regional conflict disrupted logistics routes."
    ],

    "Financial": [
        "Fuel prices increased transportation costs significantly.",
        "Inflation raised logistics expenses across {location}.",
        "Currency fluctuations affected import pricing.",
        "Freight costs surged because of market instability.",
        "Economic slowdown reduced supply chain efficiency."
    ]
}


LOCATIONS = [
    "Shanghai, CN",
    "Singapore",
    "Mumbai, IN",
    "Hamburg, DE",
    "Tokyo, JP",
    "Rotterdam, NL",
    "Los Angeles, US",
    "Dubai, UAE",
    "Seoul, KR",
    "Taipei, TW"
]


INDUSTRIES = [
    "Electronics",
    "Automotive",
    "Pharmaceuticals",
    "Food",
    "Logistics",
    "Retail",
    "Manufacturing",
    "Semiconductors",
    "Textiles",
    "Energy"
]


SEVERITIES = ["Low", "Medium", "High"]


# --------------------------------------------------
# Generate Dataset
# --------------------------------------------------

rows = []

for category, templates in CATEGORIES.items():

    for _ in range(500):

        location = random.choice(LOCATIONS)

        template = random.choice(templates)

        description = template.format(location=location)

        severity = random.choices(
            SEVERITIES,
            weights=[25, 40, 35],
            k=1
        )[0]

        industry = random.choice(INDUSTRIES)

        rows.append({
            "event_description": description,
            "category": category,
            "severity": severity,
            "location": location,
            "industry": industry,
            "source": "AI Generated Historical Dataset"
        })


df = pd.DataFrame(rows)

df = df.sample(frac=1).reset_index(drop=True)

df.to_csv(OUTPUT_FILE, index=False)

print(f"\nDataset Created Successfully")

print(f"Total Records : {len(df)}")

print(df.head())