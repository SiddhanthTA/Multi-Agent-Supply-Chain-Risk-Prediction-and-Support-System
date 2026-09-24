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

MODEL_PATH = "models/relevance_distilbert"

NEWS_API_URL = "https://newsapi.org/v2/everything"

MAX_ARTICLES = 15

# Store URLs of articles that have already been tested.
TESTED_ARTICLES_FILE = Path(
    "datasets/relevance/tested_articles.json"
)

# Different queries help us obtain different types of news.
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
    """
    Load previously tested article URLs.
    """

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

    except (json.JSONDecodeError, OSError):

        print(
            "WARNING: Could not read test history. "
            "Starting with an empty history."
        )

        return set()


# ============================================================
# SAVE TEST HISTORY
# ============================================================

def save_tested_articles(tested_articles):
    """
    Save tested article URLs.
    """

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
# FETCH ARTICLES
# ============================================================

def fetch_new_articles(tested_articles):
    """
    Fetch articles using multiple queries and return only
    articles that have not been tested previously.
    """

    all_new_articles = []

    # Shuffle queries so every execution does not begin
    # with exactly the same search.
    queries = SEARCH_QUERIES.copy()
    random.shuffle(queries)

    print("\nSearching NewsAPI using multiple queries...")

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

                try:
                    error_data = response.json()
                    error_code = error_data.get("code", "unknown")
                    error_message = error_data.get("message", "unknown error")
                except ValueError:
                    error_code = "unknown"
                    error_message = response.text

                print(
                    f"WARNING: Query failed: {query}"
                )
                print(
                    f"Status Code : {response.status_code}"
                )
                print(
                    f"Error Code  : {error_code}"
                )
                print(
                    f"Message     : {error_message}"
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

                # Skip articles already tested.
                if url in tested_articles:
                    continue

                # Avoid duplicates inside the current run.
                if any(
                    existing.get("url") == url
                    for existing in all_new_articles
                ):
                    continue

                all_new_articles.append(article)

        except requests.exceptions.RequestException as error:

            print(
                f"WARNING: NewsAPI request failed: {error}"
            )

    # Shuffle the collected articles so the same query does not
    # always dominate the test set.
    random.shuffle(all_new_articles)

    return all_new_articles[:MAX_ARTICLES]


# ============================================================
# LOAD MODEL
# ============================================================

print("\n" + "=" * 60)
print("REAL-WORLD RELEVANCE MODEL TEST")
print("=" * 60)

print("\nLoading relevance model...")

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

print("Model loaded successfully.")
print(f"Device : {device}")


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

print("\nFetching NEW NewsAPI articles...")

articles = fetch_new_articles(
    tested_articles
)

print(
    f"New articles available : "
    f"{len(articles)}"
)

if not articles:

    print("\nNo new articles were found.")

    print(
        "Try again later when NewsAPI has newer articles."
    )

    raise SystemExit(0)


# ============================================================
# MODEL PREDICTION
# ============================================================

print("\n" + "=" * 60)
print("MODEL PREDICTIONS")
print("=" * 60)


relevant_count = 0
not_relevant_count = 0


for index, article in enumerate(
    articles,
    start=1,
):

    title = article.get(
        "title"
    ) or ""

    description = article.get(
        "description"
    ) or ""

    url = article.get(
        "url"
    ) or ""

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

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    if predicted_label == 1:

        result = "RELEVANT"
        relevant_count += 1

    else:

        result = "NOT RELEVANT"
        not_relevant_count += 1

    print("\n" + "-" * 60)

    print(
        f"Article #{index}"
    )

    print(
        f"Title      : {title}"
    )

    print(
        f"Prediction : {result}"
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

    tested_articles.add(url)


# ============================================================
# SAVE TEST HISTORY
# ============================================================

save_tested_articles(
    tested_articles
)


# ============================================================
# SUMMARY
# ============================================================

total = (
    relevant_count
    + not_relevant_count
)

print("\n" + "=" * 60)
print("REAL-WORLD TEST SUMMARY")
print("=" * 60)

print(
    f"New articles tested : {total}"
)

print(
    f"Relevant            : "
    f"{relevant_count}"
)

print(
    f"Not Relevant        : "
    f"{not_relevant_count}"
)

if total > 0:

    print(
        f"Relevant Rate       : "
        f"{(relevant_count / total) * 100:.2f}%"
    )

print(
    f"Total test history  : "
    f"{len(tested_articles)} articles"
)

print("=" * 60)
print("TEST COMPLETED")
print("=" * 60)