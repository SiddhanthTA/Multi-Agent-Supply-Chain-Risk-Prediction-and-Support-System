import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, text
from app.config.settings import settings
from app.services.location_detection import resolve_event_location

GEO_TOKENS = [
    'toronto', 'kochi', 'india', 'us', 'united states', 'iran', 'rotterdam', 'dubai',
    'singapore', 'california', 'europe', 'asia', 'pine bluff', 'arkansas', 'new york',
    'london', 'mumbai', 'chennai', 'canada', 'germany', 'united arab emirates', 'uae',
    'middle east', 'saudi arabia', 'uk', 'berlin', 'frankfurt', 'delhi', 'bengaluru',
    'hyderabad', 'kolkata', 'pune', 'sydney', 'paris', 'jebel ali', 'pickering', 'hubei'
]

GENERIC = {
    'record', 'stocks', 'why', 'oil', 'market', 'markets', 'global', 'shipping', 'operations',
    'local', 'company', 'companies', 'news', 'business', 'energy', 'transport', 'logistics',
    'supply', 'chain', 'demand', 'trade', 'investments', 'the', 'prnewswire', 'globe',
    'newswire', 'tsx', 'new', 'old', 'monday', 'tuesday', 'wednesday', 'thursday',
    'friday', 'saturday', 'sunday', 'sept', 'oct', 'nov', 'dec', 'jan', 'feb', 'mar',
    'apr', 'jun', 'jul', 'aug', 'ai', 'gri', 'ltl', 'fla', 'va', 'edu', 'idiq', 'pba',
    'hdusa', 'ev', 'lfp', 'ai', 'usaj', 'gmp', 'tampa', 'arlington', 'cranbury', 'group',
    'products', 'manufacturing', 'platform', 'services', 'systems', 'capital', 'fund', 'funds',
    'board', 'pipeline', 'project', 'projects', 'technology', 'innovation', 'alliance'
}

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    rows = conn.execute(text("SELECT title, description, location FROM events WHERE event_type='News' ORDER BY created_at DESC LIMIT 20")).fetchall()

    clear_geo_count = 0
    correct = 0
    false_location_count = 0

    for idx, row in enumerate(rows, 1):
        title = row[0] or ''
        description = row[1] or ''
        text = (title + ' ' + description).strip()
        lowered = text.lower()
        result = resolve_event_location(text, [])
        primary = result.get('primary_location') or 'Unknown'

        has_clear_geo = any(token in lowered for token in GEO_TOKENS)
        if has_clear_geo:
            clear_geo_count += 1
            primary_text = primary.lower()
            if any(token in primary_text for token in GEO_TOKENS):
                correct += 1
                status = 'PASS'
            else:
                status = 'FAIL'
            print(f"{idx}. {title[:120]}")
            print(f"   CURRENT={row[2]}")
            print(f"   RESULT={result}")
            print(f"   STATUS={status}")
            print('---')
        else:
            if primary != 'Unknown' and primary.lower() not in GENERIC:
                false_location_count += 1
            print(f"{idx}. {title[:120]}")
            print(f"   CURRENT={row[2]}")
            print(f"   RESULT={result}")
            print('   STATUS=No clear geographic signal')
            print('---')

    precision = (correct / clear_geo_count) if clear_geo_count else 0.0
    total = len(rows)
    print('SUMMARY')
    print('rows=', total)
    print('clear_geo_count=', clear_geo_count)
    print('correct=', correct)
    print('precision=', precision)
    print('false_location_count=', false_location_count)
