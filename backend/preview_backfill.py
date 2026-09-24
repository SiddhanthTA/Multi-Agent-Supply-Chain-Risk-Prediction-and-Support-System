import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, text
from app.config.settings import settings
from app.services.location_detection import resolve_event_location

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    total_news = conn.execute(text("SELECT COUNT(*) FROM events WHERE event_type='News'")).scalar()
    unknown = conn.execute(text("SELECT COUNT(*) FROM events WHERE event_type='News' AND lower(location)='unknown'")).scalar()
    known = total_news - unknown
    print('TOTAL_NEWS', total_news)
    print('UNKNOWN', unknown)
    print('KNOWN', known)
    print('--- SAMPLE PREVIEW ---')
    rows = conn.execute(text("SELECT id, title, description, location FROM events WHERE event_type='News' ORDER BY created_at DESC LIMIT 12")).fetchall()
    for row in rows:
        event_id, title, description, current = row
        text = (title or '') + ' ' + (description or '')
        result = resolve_event_location(text, [])
        new_loc = result.get('primary_location') if result.get('primary_location') != 'Unknown' else 'Unknown'
        print('EVENT_ID', event_id)
        print('TITLE', title)
        print('CURRENT', current)
        print('PROPOSED', new_loc)
        print('---')
