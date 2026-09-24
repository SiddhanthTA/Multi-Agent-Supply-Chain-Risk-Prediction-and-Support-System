import json
import random
from pathlib import Path

import requests
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)

from app.config.settings import settings


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "models/impact_distilbert"

NEWS_API_URL = "https://newsapi.org/v2/everything"

MAX_ARTICLES = 15

TESTED_ARTICLES_FILE = Path(
    "datasets/impact/tested_impact_articles.json"
)

# ============================================================
# IMPACT LABELS
# ============================================================

IMPACT_LABELS = {
    0: "NO IMPACT",
    1: "POTENTIAL IMPACT",
    2: "DIRECT IMPACT",
}


# ============================================================
# NEWS QUERIES
# ============================================================

SEARCH_QUERIES = [
    '"supply chain" disruption',
    '"shipping" delay OR disruption',
    '"port" closure OR strike OR congestion',
    '"factory" shutdown OR fire OR disruption',
    '"shortage" manufacturing OR supplier',
    '"logistics" disruption OR delay',
    '"semiconductor" shortage OR supply',
    '"freight" disruption OR delay',
    '"cargo" disruption OR delay',
    '"export restrictions" supply',
    '"import restrictions" supply',
    '"supplier" failure OR bankruptcy',
    '"transportation" disruption',
    '"energy supply" disruption',
    '"raw material" shortage',
]


# ============================================================
# LOAD TEST HISTORY
# ============================================================

def load_tested_articles():

    if not TESTED_ARTICLES_FILE.exists():
        return set()

    try:

        with open(
            TESTED_ARTICLES_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return set(data)

    except (
        json.JSONDecodeError,
        OSError,
    ):

        print(
            "WARNING: Could not read test history."
        )

        return set()


# ============================================================
# SAVE TEST HISTORY
# ============================================================

def save_tested_articles(
    tested_articles,
):

    TESTED_ARTICLES_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        TESTED_ARTICLES_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            sorted(tested_articles),
            file,
            indent=2,
        )


# ============================================================
# FETCH NEW ARTICLES
# ============================================================

def fetch_new_articles(
    tested_articles,
):

    all_new_articles = []

    queries = SEARCH_QUERIES.copy()

    random.shuffle(queries)

    print(
        "\nSearching NewsAPI using multiple queries..."
    )

    for query in queries:

        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 50,
            "apiKey": settings.NEWS_API_KEY,
        }

        try:

            response = requests.get(
                NEWS_API_URL,
                params=params,
                timeout=15,
            )

            if response.status_code != 200:

                print(
                    f"WARNING: Query failed: {query}"
                )

                continue

            data = response.json()

            articles = data.get(
                "articles",
                [],
            )

            for article in articles:

                url = article.get("url")

                if not url:
                    continue

                if url in tested_articles:
                    continue

                if any(
                    existing.get("url") == url
                    for existing in all_new_articles
                ):
                    continue

                all_new_articles.append(
                    article
                )

        except requests.exceptions.RequestException as error:

            print(
                f"WARNING: NewsAPI request failed: "
                f"{error}"
            )

    random.shuffle(
        all_new_articles
    )

    return all_new_articles[
        :MAX_ARTICLES
    ]


# ============================================================
# LOAD MODEL
# ============================================================

print("\n" + "=" * 60)

print(
    "REAL-WORLD IMPACT MODEL TEST"
)

print("=" * 60)

print(
    "\nLoading Impact model..."
)

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH
)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_PATH
)

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

model.to(device)

model.eval()

print(
    "Impact model loaded successfully."
)

print(
    f"Device : {device}"
)


# ============================================================
# LOAD TEST HISTORY
# ============================================================

tested_articles = load_tested_articles()

print(
    f"Previously tested articles : "
    f"{len(tested_articles)}"
)


# ============================================================
# FETCH NEW ARTICLES
# ============================================================

print(
    "\nFetching NEW NewsAPI articles..."
)

articles = fetch_new_articles(
    tested_articles
)

print(
    f"New articles available : "
    f"{len(articles)}"
)

if not articles:

    print(
        "\nNo new articles were found."
    )

    print(
        "Try again later when NewsAPI "
        "has newer articles."
    )

    raise SystemExit(0)


# ============================================================
# COUNTERS
# ============================================================

impact_counts = {
    0: 0,
    1: 0,
    2: 0,
}


# ============================================================
# MODEL PREDICTION
# ============================================================

for index, article in enumerate(
    articles,
    start=1,
):

    title = (
        article.get("title")
        or ""
    )

    description = (
        article.get("description")
        or ""
    )

    url = (
        article.get("url")
        or ""
    )

    text = (
        f"{title}. "
        f"{description}"
    ).strip()

    if not text:
        continue

    # --------------------------------------------------------
    # TOKENIZATION
    # --------------------------------------------------------

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=256,
    )

    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }

    # --------------------------------------------------------
    # PREDICTION
    # --------------------------------------------------------

    with torch.no_grad():

        outputs = model(
            **inputs
        )

    probabilities = torch.softmax(
        outputs.logits,
        dim=1,
    )[0]

    predicted_label = torch.argmax(
        probabilities
    ).item()

    confidence = probabilities[
        predicted_label
    ].item()

    impact = IMPACT_LABELS[
        predicted_label
    ]

    impact_counts[
        predicted_label
    ] += 1

    # --------------------------------------------------------
    # DISPLAY RESULT
    # --------------------------------------------------------

    print(
        "\n" + "-" * 60
    )

    print(
        f"Article #{index}"
    )

    print(
        f"Title      : {title}"
    )

    print(
        f"Impact     : {impact}"
    )

    print(
        f"Label      : {predicted_label}"
    )

    print(
        f"Confidence : {confidence:.4f}"
    )

    print(
        f"URL        : {url}"
    )

    # --------------------------------------------------------
    # SAVE AS TESTED
    # --------------------------------------------------------

    tested_articles.add(
        url
    )


# ============================================================
# SAVE TEST HISTORY
# ============================================================

save_tested_articles(
    tested_articles
)


# ============================================================
# SUMMARY
# ============================================================

total = sum(
    impact_counts.values()
)

print(
    "\n" + "=" * 60
)

print(
    "REAL-WORLD IMPACT TEST SUMMARY"
)

print(
    "=" * 60
)

print(
    f"New articles tested : {total}"
)

print(
    f"No Impact           : "
    f"{impact_counts[0]}"
)

print(
    f"Potential Impact    : "
    f"{impact_counts[1]}"
)

print(
    f"Direct Impact       : "
    f"{impact_counts[2]}"
)

if total > 0:

    print(
        f"\nNo Impact Rate      : "
        f"{(impact_counts[0] / total) * 100:.2f}%"
    )

    print(
        f"Potential Rate      : "
        f"{(impact_counts[1] / total) * 100:.2f}%"
    )

    print(
        f"Direct Impact Rate  : "
        f"{(impact_counts[2] / total) * 100:.2f}%"
    )

print(
    f"\nTotal test history  : "
    f"{len(tested_articles)} articles"
)

print(
    "=" * 60
)

print(
    "TEST COMPLETED"
)

print(
    "=" * 60
)