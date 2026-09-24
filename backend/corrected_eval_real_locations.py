import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, text
from app.config.settings import settings
from app.services.location_detection import resolve_event_location

EXPECTED = {
    1: ['Toronto', 'Pickering Nuclear Generating Station'],
    2: ['Iran'],
    3: [],
    4: ['United States', 'Iran'],
    5: ['Kochi', 'Tamil Nadu', 'Kerala'],
    6: ['United States'],
    7: [],
    8: ['United States'],
    9: ['Pine Bluff Arsenal', 'Arkansas', 'United States'],
    10: [],
    11: ['Europe'],
    12: [],
    13: [],
    14: [],
    15: ['Europe'],
    16: ['Saudi Arabia'],
    17: ['Russia'],
    18: [],
    19: ['India', 'Southeast Asia'],
    20: [],
}

CANDIDATE_MAP = {
    'toronto': 'Toronto',
    'pickering nuclear generating station': 'Pickering Nuclear Generating Station',
    'iran': 'Iran',
    'united states': 'United States',
    'usa': 'United States',
    'us': 'United States',
    'u s': 'United States',
    'kochi': 'Kochi',
    'tamil nadu': 'Tamil Nadu',
    'kerala': 'Kerala',
    'pine bluff arsenal': 'Pine Bluff Arsenal',
    'arkansas': 'Arkansas',
    'europe': 'Europe',
    'european': 'Europe',
    'saudi arabia': 'Saudi Arabia',
    'russia': 'Russia',
    'india': 'India',
    'southeast asia': 'Southeast Asia',
}

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    rows = conn.execute(text("SELECT title, description FROM events WHERE event_type='News' ORDER BY created_at DESC LIMIT 20")).fetchall()

    explicit_geo_articles = 0
    correct = 0
    missed = 0
    false_geo = 0
    locationless = 0
    primary_good = 0

    for idx, (title, description) in enumerate(rows, 1):
        expected = EXPECTED[idx]
        text = (title or '') + ' ' + (description or '')
        result = resolve_event_location(text, [])
        primary = result.get('primary_location') or 'Unknown'
        detected = result.get('normalized_locations', [])

        if expected:
            explicit_geo_articles += 1
            expected_norm = set(expected)
            detected_norm = {str(v) for v in detected}
            # Normalize detector output to canonical labels for comparison.
            mapped_detected = set()
            for v in detected_norm:
                lowered = v.lower()
                mapped_detected.add(CANDIDATE_MAP.get(lowered, v))

            overlap = expected_norm & mapped_detected
            if overlap:
                correct += 1
            else:
                missed += 1

            primary_match = bool(any(item in expected_norm for item in [primary, *[v for v in mapped_detected]]))
            if primary_match:
                primary_good += 1
        else:
            locationless += 1
            if primary != 'Unknown':
                false_geo += 1

        print(f'#{idx}: {title[:120]}')
        print(f'  expected={expected}')
        print(f'  detected={detected}')
        print(f'  primary={primary}')
        print(f'  status={"CORRECT" if expected and overlap else "MISS" if expected else "LOCATIONLESS_OK" if primary == "Unknown" else "FALSE_POSITIVE"}')
        print('---')

    print('SUMMARY')
    print('explicit_geo_articles=', explicit_geo_articles)
    print('correct=', correct)
    print('missed=', missed)
    print('locationless_articles=', locationless)
    print('false_geo=', false_geo)
    print('primary_accuracy=', primary_good / explicit_geo_articles if explicit_geo_articles else 0)
