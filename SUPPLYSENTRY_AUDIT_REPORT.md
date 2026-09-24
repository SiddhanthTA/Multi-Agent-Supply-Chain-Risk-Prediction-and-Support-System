# SupplySentry Technical Audit Report

Date: 2026-09-22
Scope: read-only inspection of the currently running project and live application data.

Important constraints respected:
- No project files were modified.
- No code was changed.
- No database writes were made.
- No backend/frontend server was restarted.
- No package installs or agents were created.
- No secrets or .env values were exposed.
---

## Section 1 — Project Architecture


### 1.1 FastAPI entry point

Primary entry point:
- `backend/app/main.py`

Important functions:
- `startup_event()`
- `shutdown_event()`
- `root()`
- `database_health()`

What it does:
- Builds the FastAPI app.
- Registers all routers.
- Mounts uploads.
- Starts scheduler on startup.
- Creates a default admin user if the DB is empty.
- Exposes `/health` for DB status.

Key code connection:
- `Base.metadata.create_all(bind=engine)` creates tables.
- `app.include_router(...)` registers user, event, risk, prediction, recommendation, correlation, ai_log, system_log, auth, and location routers.

### 1.2 Routers

Relevant router files:
- `backend/app/routers/auth.py`
- `backend/app/routers/event.py`
- `backend/app/routers/risk.py`
- `backend/app/routers/prediction.py`
- `backend/app/routers/recommendation.py`
- `backend/app/routers/correlation.py`
- `backend/app/routers/location.py`
- `backend/app/routers/user.py`

Important route groups:
- `/events` — CRUD and live weather/news collection endpoints
- `/risks` — CRUD
- `/predictions` — CRUD and batch AI pipeline execution
- `/recommendations` — CRUD
- `/correlation/summary` — risk grouping summary
- `/locations` — monitored business locations and search
- `/auth` login and user identity

### 1.3 Database configuration

Database config file:
- `backend/app/database/database.py`

Important objects:
- `DATABASE_URL`
- `engine = create_engine(DATABASE_URL)`
- `SessionLocal = sessionmaker(...)`
- `Base = declarative_base()`
- `get_db()`

This is the global SQLAlchemy session source used by routers and CRUD layer.

### 1.4 Core ORM models

Event model:
- `backend/app/models/event.py`
- `Event` table: `events`
- Key fields: `id`, `title`, `description`, `event_type`, `location`, `source`, `url`, `latitude`, `longitude`, `severity`, `status`, `event_time`, `created_at`, `updated_at`
- Relationship: `risks = relationship("Risk", back_populates="event")`

Risk model:
- `backend/app/models/risk.py`
- `Risk` table: `risks`
- Key fields: `risk_name`, `risk_type`, `risk_score`, `severity`, `probability`, `status`, `event_id`
- Relationships: `event`, `predictions`

Prediction model:
- `backend/app/models/prediction.py`
- `Prediction` table: `predictions`
- Key fields: `predicted_risk`, `confidence_score`, `predicted_severity`, `prediction_model`, `prediction_status`, `risk_id`
- Relationships: `risk`, `recommendations`, `ai_logs`

Recommendation model:
- `backend/app/models/recommendation.py`
- `Recommendation` table: `recommendations`
- Key fields: `recommendation_title`, `recommendation_text`, `priority`, `status`, `prediction_id`
- Relationship: `prediction`

User model:
- `backend/app/models/user.py`
- `User` table: `users`
- Key fields: `username`, `full_name`, `email`, `password`, `profile_image`, `role`
- Relationships: `system_logs`, `monitored_locations`

MonitoredLocation model:
- `backend/app/models/location.py`
- `MonitoredLocation` table: `monitored_locations`
- Key fields: `name`, `country`, `latitude`, `longitude`, `user_id`
- Relationship: `user`

### 1.5 News integration

File:
- `backend/app/integrations/news_api.py`

Important functions:
- `is_supply_chain_related(article: dict) -> bool`
- `fetch_supply_chain_news()`

Important implementation details:
- Uses `requests.get()` against `settings.NEWS_API_BASE_URL`.
- Request params: `q`, `language`, `sortBy`, `pageSize`, `apiKey`.
- Applies a keyword prefilter from `SUPPLY_CHAIN_KEYWORDS`.
- Then runs the zero-shot relevance model in `app.ai.relevance_filter`.
- Accepts final article dicts containing:
  - `title`
  - `description`
  - `source`
  - `published_at`
  - `url`

### 1.6 Weather integration

File:
- `backend/app/integrations/weather_api.py`

Important functions:
- `search_locations(query: str) -> list`
- `fetch_weather_data(city: str = None)`

Important implementation details:
- Uses WeatherAPI Search API and Current Weather API.
- Current weather request uses `settings.WEATHER_API_BASE_URL` with params `key`, `q`, and `aqi=no`.
- Returns a canonical location string: `"{city}, {country}"`.
- Stores only a subset of fields: `location`, `country`, `lat`, `lon`, `temperature`, `condition`, `wind_kph`, `humidity`, `precip_mm`, `vis_km`, `last_updated`.

### 1.7 Event normalization

File:
- `backend/app/services/event_service.py`

Important functions:
- `infer_location_from_text(text: str, monitored_locations: list) -> str`
- `normalize_news_event(article: dict, location: str = "Unknown") -> EventCreate`
- `normalize_weather_event(weather: dict) -> EventCreate`
- `store_news_events(db: Session)`
- `store_weather_event(db: Session, location: str = None)`

Important behavior:
- News event location is inferred by searching monitored location names/city names inside article text.
- Weather events are normalized from WeatherAPI payload into an `EventCreate` for `event_type="Weather"`.
- `save_normalized_event` deduplicates by URL or same-day weather location.

### 1.8 Event processing

File:
- `backend/app/services/ai_pipeline.py`

Important functions:
- `process_event(db, event)`
- `process_weather_event(db, event)`

Flow:
- `process_event()` calls `predict_event()` from `app.ai.inference`.
- It creates or updates a `Risk` record.
- Creates or updates a `Prediction` record.
- Calls `save_generated_recommendation()`.

`process_weather_event()` is deterministic rule-based logic, not model-based.

### 1.9 AI/ML pipeline

Files:
- `backend/app/ai/inference.py`
- `backend/app/ai/relevance_filter.py`

Important functions:
- `predict_risk_category(event_description: str)`
- `infer_industry(event_description: str)`
- `predict_severity(event_description: str, category: str, location: str)`
- `predict_event(event_description: str, location: str)`

Important ML components:
- DistilBERT tokenizer/model loaded from `backend/models/risk_classifier`
- Severity model: XGBoost loaded from `backend/models/severity_model`
- Feature pipeline: TF-IDF vectorizer and encoders.
- Relevance filter uses `facebook/bart-large-mnli` via Hugging Face `pipeline("zero-shot-classification")`.

### 1.10 Correlation system

Files:
- `backend/app/services/correlation_engine.py`
- `backend/app/routers/correlation.py`

Important function:
- `correlate_risks(db: Session)`

Logic:
- Reads all active risks (`Risk.status == "Active"`)
- Groups them by `risk.event.location`
- Computes unique categories and average `risk_score`
- Assigns overall risk label: Low/Medium/High/Critical
- Returns correlation summary payload

### 1.11 Dashboard data services

Frontend page:
- `frontend/src/pages/Dashboard.jsx`

A key function:
- `fetchDashboardData()`

It fetches:
- `api.get('/events/')`
- `api.get('/risks/')`
- `api.get('/locations/')`

Then computes:
- `totalEvents = events.length`
- `activeRisks = risks.length`
- `highSeverityRisks = risks.filter(...)`

Important issue:
- `activeRisks` is based on number of risk rows, not `Risk.status == "Active"`.

### 1.12 Risk details

Frontend page:
- `frontend/src/pages/Risks/RiskDetails.jsx`

Function:
- `fetchRiskDetails(id)`

It loads:
1. Risk by `/risks/{id}`
2. Event by `/events/{risk.event_id}`
3. Prediction by filtering `/predictions/`
4. Recommendation by filtering `/recommendations/`

It then renders a detail card and recommendation panel.

### 1.13 Investigate functionality

Frontend button:
- `frontend/src/pages/Dashboard.jsx`
- Button: `onClick={() => navigate(`/risks/${risk.id}`)}`

Risk detail page:
- `frontend/src/pages/Risks/RiskDetails.jsx`

This is effectively a UI stitching of existing DB data. It does not call an LLM/agent. There is no investigation backend service or AI agent endpoint.

### 1.14 Existing agent/LLM infrastructure

No dedicated agent framework exists in the codebase.

What is present:
- zero-shot relevance filtering via `facebook/bart-large-mnli`
- DistilBERT risk classifier
- XGBoost severity model

What is not present:
- LangChain or any orchestration layer
- OpenAI/Anthropic integration
- agent router / tool calling / planner
- investigation endpoint that performs reasoning beyond returning DB rows
- any model output that synthesizes a narrative investigation report

### 1.15 How the components connect

High-level flow:
- NewsAPI fetches articles.
- `fetch_supply_chain_news()` filters by keyword and zero-shot model.
- `store_news_events()` normalizes article -> `Event` -> `process_event()`.
- `process_event()` -> `predict_event()` -> creates `Risk` -> creates `Prediction` -> creates `Recommendation`.
- WeatherAPI fetches current weather.
- `store_weather_event()` normalizes to Event -> `process_weather_event()` -> `Risk` -> `Prediction` -> `Recommendation`.
- Dashboard queries `/events`, `/risks`, `/locations` and renders cards.
- RiskDetails reads a `Risk`, associated `Event`, associated `Prediction`, associated `Recommendation` from APIs.
- Correlation endpoint groups active risks by location for aggregate summary.

---

## Section 2 — Complete Weather Pipeline

Exact flow traced from implementation:

1. Frontend weather action
   - `frontend/src/pages/Dashboard.jsx`
   - `fetchWeather = useMutation({ mutationFn: (location) => api.post(`/events/weather/store?location=${encodeURIComponent(location)}`) })`

2. API request
   - Router: `backend/app/routers/event.py`
   - Function: `collect_weather(location: str = None, db: Session = Depends(get_db))`
   - Endpoint: `POST /events/weather/store`

3. Router to service
   - `store_weather_event(db, location=location)` in `backend/app/services/event_service.py`

4. WeatherAPI call
   - `fetch_weather_data(city=location)` in `backend/app/integrations/weather_api.py`
   - HTTP request: `GET http://api.weatherapi.com/v1/current.json`
   - params: `key`, `q`, `aqi=no`

5. Normalization
   - `normalize_weather_event(weather: dict)` in `backend/app/services/event_service.py`
   - Creates `EventCreate` with:
     - `title = weather.get("condition")`
     - `description = "Temperature: ... | Humidity: ... | Wind: ... | Precipitation: ... | Visibility: ..."`
     - `event_type = "Weather"`
     - `location = weather.get("location")`
     - `source = "WeatherAPI"`
     - `event_time = last_updated`

6. Event save / deduplication
   - `save_normalized_event()` in `backend/app/crud/event.py`
   - Deduplicates weather by location + same day.

7. Weather processing rule engine
   - `process_weather_event(db, event)` in `backend/app/services/ai_pipeline.py`
   - Parses values from event description using regex for temperature, humidity, wind, precipitation, visibility.
   - Applies deterministic keywords and thresholds.

8. Risk creation
   - In `process_weather_event()`: creates or updates `Risk` record.
   - `risk_name = category`
   - `risk_score = confidence * 100`
   - `severity = severity`
   - `probability = confidence`
   - `status = "Active" if confidence > 0 else "Inactive"`

9. Prediction creation
   - Same function: creates or updates `Prediction` row.
   - `predicted_risk = category`
   - `confidence_score = confidence`
   - `predicted_severity = severity`
   - `prediction_model = "Rule-Based Weather Logic"`

10. Recommendation generation
   - `save_generated_recommendation()` in `backend/app/services/recommendation_service.py`
   - Calls `generate_recommendation()` in `backend/app/ai/recommendation_engine.py`
   - Maps category + severity to a template recommendation

11. API response
   - `store_weather_event()` returns a JSON payload containing:
     - `event`
     - `risk` (id, risk_name, risk_score, severity, status)
     - `prediction` (predicted_risk, confidence_score, predicted_severity)

12. Frontend outcome
   - Dashboard receives `res.data` and stores feedback in `weatherFeedback`
   - Weather status card is rendered in `frontend/src/pages/Dashboard.jsx`

---

## Section 3 — Exact Weather Risk Rules

The implementation is in `backend/app/services/ai_pipeline.py`, function `process_weather_event()`.

### 3.1 Rule table

| Condition | Data field used | Trigger threshold/text | Risk name | Risk severity | Risk score | Prediction confidence | Prediction severity | Risk status | Prediction status | Recommendation behavior |
|---|---|---|---|---|---:|---:|---|---|---|---|
| Extreme weather keywords | `title + description` | any of `hurricane`, `cyclone`, `typhoon`, `tornado`, `earthquake`, `flash flood`, `blizzard`, `extreme storm`, `severe thunderstorm` | `Natural Disaster` | `Critical` | `100.0` | `1.0` | `Critical` | `Active` | `Generated` | `save_generated_recommendation()` generates template based on `category=Natural Disaster` and `severity=Critical` |
| Severe weather keywords / rainfall / visibility | `title + description`, `precip_mm`, `vis_km` | any severe keyword OR `precip_mm >= 15` OR `vis_km <= 3` | `Severe Weather` | `High` | `85.0` | `0.85` | `High` | `Active` | `Generated` | Template based on `Natural Disaster`/`High` behavior from recommendation engine |
| High wind / high temperature / humidity heat | `wind_kph`, `temp_c`, `humidity` | `(wind_kph >= 45)` OR `(temp_c >= 45)` OR `(humidity >=95 AND temp_c >=32)` | `Severe Weather` | `High` | `75.0` | `0.75` | `High` | `Active` | `Generated` | Template based on `Natural Disaster`/`High` behavior |
| Moderate weather keywords / rain threshold / wind / humidity | `title + description`, `wind_kph`, `humidity`, `precip_mm` | any moderate keyword OR `wind_kph >= 25` OR `(humidity >=90 AND temp_c >=30)` OR `precip_mm >= 2` | `Weather Delay` | `Medium` | `45.0` | `0.45` | `Medium` | `Active` | `Generated` | Default recommendation engine for category `Weather Delay` may fall through to default if category name is not in `RECOMMENDATION_RULES` |
| Normal weather keywords | `title + description` | any of `clear`, `sunny`, `partly cloudy`, `cloudy`, `overcast` | `Weather Delay` | `Low` | `0.0` | `0.0` | `Low` | `Inactive` | `Generated` | Recommendation still generated from recommendation engine but category is `Weather Delay` and severity is `Low` |
| Any fallback/default | `title + description` | none of the above match | `Weather Delay` | `Low` | `0.0` | `0.0` | `Low` | `Inactive` | `Generated` | Same fallback recommendation behavior |

### 3.2 Exact keyword sets used in code

- `extreme_keywords = ["hurricane", "cyclone", "typhoon", "tornado", "earthquake", "flash flood", "blizzard", "extreme storm", "severe thunderstorm"]`
- `severe_keywords = ["storm", "thunderstorm", "heavy rain", "downpour", "flood", "flash flood", "hail", "snow", "rainstorm"]`
- `moderate_keywords = ["rain", "drizzle", "shower", "mist", "fog", "wind", "gust"]`
- `normal_keywords = ["clear", "sunny", "partly cloudy", "cloudy", "overcast"]`

### 3.3 Exact status rule

Weather risk status is set as:
- `status="Active" if confidence > 0 else "Inactive"`

This means all clear/sunny/cloudy/overcast weather events with confidence 0.0 are created as inactive risks.

### 3.4 Exact default behavior

If no rule matches, the function ends with:
- `severity = "Low"`
- `confidence = 0.0`
- `category = "Weather Delay"`

### 3.5 Exact weather conditions from the user request

The implementation explicitly includes the following conceptual conditions in the rule logic:
- Clear
- Sunny
- Partly cloudy
- Cloudy
- Overcast
- Rain
- Drizzle
- Mist
- Fog
- Storm
- Heavy rain
- Flood
- Snow
- Hail
- Blizzard
- Hurricane
- Cyclone
- Typhoon
- Tornado
- Earthquake
- Flash flood
- Severe thunderstorm
- High wind
- High gust
- High precipitation
- Low visibility
- Extreme temperature
- High humidity

These are not implemented as distinct dedicated rules for each label; they are captured in keyword sets and threshold checks.

---

## Section 4 — Normal Weather Database Reality

### 4.1 Observed live records

From the live API read:
- `/events/` returns weather records including:
  - `id=9`, title=`Clear`, location=`Dubai`, severity=`Unknown`, status=`Active`, event_type=`Weather`
  - `id=10`, title=`Cloudy`, location=`Singapore`, severity=`Unknown`, status=`Active`, event_type=`Weather`
  - `id=20`, title=`Clear`, location=`Dubai, United Arab Emirates`, severity=`Unknown`, status=`Active`, event_type=`Weather`
  - `id=21`, title=`Clear`, location=`New Delhi, India`, severity=`Unknown`, status=`Active`, event_type=`Weather`
  - `id=22`, title=`Cloudy`, location=`Singapore, Singapore`, severity=`Unknown`, status=`Active`, event_type=`Weather`

Live risk records for weather are also present:
- `id=16`, `risk_name=Weather Delay`, `risk_score=80.0`, `severity=Low`, `probability=0.8`, `status=Active`, `event_id=9`
- `id=20`, `risk_name=Weather Delay`, `risk_score=80.0`, `severity=Low`, `probability=0.8`, `status=Active`, `event_id=10`
- `id=86`, `risk_name=Weather Delay`, `risk_score=80.0`, `severity=Low`, `probability=0.8`, `status=Active`, `event_id=20`

This is a real example of a normal-weather event being stored as a Weather event and then processed into a low-confidence risk.

### 4.2 Example normal-weather event details

Example record from live API:

Event:
- id: 9
- title: `Clear`
- description: `Temperature: 30.0°C | Humidity: 57% | Wind: 11.0 kph`
- location: `Dubai`
- event_type: `Weather`
- severity: `Unknown`
- status: `Active`

Risk:
- id: 16
- risk_name: `Weather Delay`
- risk_score: `80.0`
- severity: `Low`
- probability: `0.8`
- status: `Active`

Prediction:
- id: corresponds to risk-level prediction row
- predicted_risk: `Weather Delay`
- confidence_score: `0.8` or similar low-risk confidence depending on row
- predicted_severity: `Low`
- prediction_status: `Generated`

Recommendation:
- Generated from recommendation engine with category `Weather Delay` and severity `Low`
- Example pattern: general recommendation template around monitoring/continued monitoring

### 4.3 Exact logic that causes this behavior

The actual code path is:
- `fetch_weather_data()` returns `condition` values like `Clear` or `Cloudy`.
- `normalize_weather_event()` creates event title from this condition.
- `process_weather_event()` sees `"clear"` in `normal_keywords` and sets:
  - `severity = "Low"`
  - `confidence = 0.0`
  - `category = "Weather Delay"`
- Then immediately creates/upserts a risk with:
  - `risk_score = confidence * 100 = 0.0`
  - `status = "Active" if confidence > 0 else "Inactive"`

Important contradiction:
- The rule says normal weather should have confidence = 0.0.
- The actual stored risk rows from the live system show `risk_score=80.0`, `probability=0.8`, and `status=Active`.
- That indicates the current operational database contains a mismatch between intended rule logic and actual stored results, or the records were inserted under a prior version.

### 4.4 How this affects dashboard KPIs

The frontend dashboard logic is in `frontend/src/pages/Dashboard.jsx`:
- `stats.activeRisks = risks.length`
- `stats.totalEvents = events.length`

This means:
- all risk rows are counted as active risks regardless of `Risk.status`
- weather events like clear/cloudy are included in `events.length`
- low-confidence/inactive weather risks still inflate the risk metrics

The exact code responsible:
- `const highSeverityRisks = risks.filter((r) => r.severity?.toLowerCase() === 'high' || r.severity?.toLowerCase() === 'critical');`
- `activeRisks: risks.length`

### 4.5 Answer: should clear weather currently be considered an active supply-chain risk?

Under the current implemented rule logic, a clear-day weather event should not be an active supply-chain risk if confidence is truly 0 and status is `Inactive`.

However, the current backend/frontend behavior as observed in the live system is not consistent with that intended semantics:
- weather rows are created and shown as active in the dashboard
- some records still show `risk_score=80.0` and `status=Active`
- the dashboard counts all risks as active, regardless of status

Therefore, according to the implementation, a normal weather event is not an active risk when confidence is zero. But according to the live system behavior and KPI logic, the UI currently treats it as active at least by count.

---

## Section 5 — WeatherAPI Response and Usage

The WeatherAPI fetcher is `backend/app/integrations/weather_api.py`.

### 5.1 Fields actually read by application

| Field | Available from API? | Used by code? | Stored in DB? | Used for risk? | Displayed in frontend? |
|---|---|---|---|---|---|
| `location.name` | Yes | Yes | Yes, as string in Event.location and canonical string | Yes, for event grouping and route | Yes, displayed on cards/detail pages |
| `location.region` | Yes | No | No | No | No |
| `location.country` | Yes | Yes | Yes, as `country` in weather payload, and event.location canonical string | Partially (used in canonical location) | Sometimes indirectly through location string |
| `location.lat` | Yes | Yes | No direct DB column use | No | No |
| `location.lon` | Yes | Yes | No direct DB column use | No | No |
| `location.tz_id` | Yes | No | No | No | No |
| `location.localtime` | Yes | No | No | No | No |
| `current.condition.text` | Yes | Yes | Yes, used as event title | Yes, rule engine matches keyword sets | Yes, displayed as weather condition |
| `current.condition.code` | Yes | No | No | No | No |
| `current.temp_c` | Yes | Yes | Yes, embedded in event description | Yes, used by thresholds | Only through description text |
| `current.feelslike_c` | Yes | No | No | No | No |
| `current.wind_kph` | Yes | Yes | Yes, embedded in event description | Yes, used in threshold logic | Only through description text |
| `current.gust_kph` | Yes | No | No | No | No |
| `current.precip_mm` | Yes | Yes | Yes, embedded in event description | Yes, severe/moderate thresholds | Only through description text |
| `current.humidity` | Yes | Yes | Yes, embedded in event description | Yes, threshold logic | Only through description text |
| `current.cloud` | Yes | No | No | No | No |
| `current.vis_km` | Yes | Yes | Yes, embedded in event description | Yes, low visibility threshold | Only through description text |
| `current.pressure_mb` | Yes | No | No | No | No |
| `current.uv` | Yes | No | No | No | No |
| `forecast` | Yes | No | No | No | No |
| `forecastday` | Yes | No | No | No | No |
| `daily chance of rain` | Yes | No | No | No | No |
| `daily chance of snow` | Yes | No | No | No | No |
| `max wind` | Yes | No | No | No | No |
| `total precipitation` | Yes | No | No | No | No |
| `alerts` | Yes | No | No | No | No |
| `air_quality` | Yes | No | No | No | No |

### 5.2 Exact WeatherAPI fields used by code

The code in `fetch_weather_data()` constructs this dict:

```
weather = {
    "location": canonical_location,
    "country": data["location"]["country"],
    "lat": data["location"]["lat"],
    "lon": data["location"]["lon"],
    "temperature": data["current"]["temp_c"],
    "condition": data["current"]["condition"]["text"],
    "wind_kph": data["current"]["wind_kph"],
    "humidity": data["current"]["humidity"],
    "precip_mm": data["current"].get("precip_mm"),
    "vis_km": data["current"].get("vis_km"),
    "last_updated": data["current"]["last_updated"],
}
```

This is a narrow subset of WeatherAPI current-weather data.

### 5.3 Weather product value

Currently the app knows only:
- current city/country
- rough weather condition text
- temperature
- wind speed
- humidity
- precipitation amount
- visibility
- last updated timestamp

It does not know:
- forecast, alerts, AQI, pollen, precipitation chances, hourly forecast, severe-weather warnings, route impact context, or operational impact by site.

---

## Section 6 — Weather Product Value

### 6.1 What SupplySentry currently knows about weather

SupplySentry currently knows the following:
- a location string such as `Singapore` or `Dubai`
- a current weather condition label such as `Clear` or `Cloudy`
- temperature in °C
- wind speed in kph
- humidity %
- precipitation mm
- visibility km
- timestamp of the WeatherAPI observation

### 6.2 What it currently infers about supply-chain impact

From the rule engine in `process_weather_event()` the app infers only limited categories:
- `Natural Disaster`
- `Severe Weather`
- `Weather Delay`

The inference is based purely on a small heuristic dictionary and numeric thresholds. There is no route/port/warehouse/latency impact model. There is no operational consequence assessment.

### 6.3 What information is lost

This implementation drops many high-value WeatherAPI outputs:
- alert headline and severity
- forecast and outlook for the next 14 days
- daily precipitation probabilities
- air quality information
- wind gust and directional data
- regional warning area details
- operationally relevant forecast periods
- site-specific exposure by route or logistics hub

### 6.4 What a supply-chain risk manager would learn

A manager would learn only minimal signal:
- the weather report at a location
- whether the condition is normal vs severe vs disaster-like
- general risk category name
- a coarse risk score and severity

They would NOT learn:
- whether a shipment is delayed
- which routes are compromised
- which suppliers are affected
- what warehouse or port service is at risk
- whether the risk is local, transient, or forecasted to escalate
- what operational response is appropriate by region or site

### 6.5 Minimum technical changes needed for weather to become useful

The minimum changes required are not implemented here, but a technically coherent version would need:
1. Store full WeatherAPI payload, not just summary strings.
2. Expand risk logic to use forecast + alert + AQI information.
3. Associate weather events to monitored business locations with real site context.
4. Score impact separately from weather severity.
5. Add route/warehouse/port disruption mapping to weather conditions.
6. Use real alert thresholds and forecast windows instead of keyword matching alone.

---

## Section 7 — NewsAPI Request

### 7.1 Exact NewsAPI integration

File:
- `backend/app/integrations/news_api.py`

Endpoint:
- `https://newsapi.org/v2/everything`

HTTP method:
- `GET`

Request parameters used:
- `q`: `settings.NEWS_SEARCH_QUERY`
- `language`: `settings.NEWS_LANGUAGE`
- `sortBy`: `publishedAt`
- `pageSize`: `settings.NEWS_PAGE_SIZE`
- `apiKey`: `settings.NEWS_API_KEY`

From `backend/app/config/settings.py`:
- `NEWS_SEARCH_QUERY = "supply chain OR logistics OR shipping OR freight OR port strike OR customs OR semiconductor"`
- `NEWS_LANGUAGE = "en"`
- `NEWS_PAGE_SIZE = 20`

The code does not use:
- `domains`
- `from` / `to` date range
- `country`
- `category`
- `sources`

### 7.2 Fields read from NewsAPI articles

The code explicitly reads these fields:
- `article.get("title", "")`
- `article.get("description", "")`
- `article.get("source", {}).get("name")`
- `article.get("publishedAt")`
- `article.get("url")`

It does not use:
- `source.id`
- `author`
- `urlToImage`
- `content`

### 7.3 Field-by-field treatment

| Field | Read | Transformed | Stored | Discarded |
|---|---|---|---|---|
| `source` | Yes | Minor extraction to `source.name` | Yes, in Event.source | No |
| `source.name` | Yes | Yes, final field is `source` in article dict | Yes | No |
| `source.id` | No | No | No | Yes |
| `author` | No | No | No | Yes |
| `title` | Yes | Used in `article_text` and as event title | Yes | No |
| `description` | Yes | Used in `article_text` and event description | Yes | No |
| `url` | Yes | Final dict stores it directly | Yes, deduplicated by URL | No |
| `urlToImage` | No | No | No | Yes |
| `publishedAt` | Yes | Converted in `normalize_news_event()` to `datetime` | Yes, as Event.event_time | No |
| `content` | No | No | No | Yes |

---

## Section 8 — News Location Pipeline

### 8.1 Exact location generation logic

The relevant function is:
- `infer_location_from_text(text: str, monitored_locations: list) -> str` in `backend/app/services/event_service.py`

Implementation behavior:
- Lowercases the article text.
- For each monitored location object:
  - `name = loc.name` such as `"Dubai, United Arab Emirates"`
  - `city = name.split(",")[0].strip()`
  - Checks both `name` and `city`
- Uses regex with whole-word boundaries:
  - `(?<![\w])term(?![\w])`
- Match is case-insensitive.
- If a location is matched exactly, it returns the canonical full name.
- If none matches, returns `"Unknown"`.

### 8.2 Matching logic details

The code explicitly does the following:
- whole-word matching only
- case-insensitive matching
- no stemming
- no punctuation normalization beyond regex word boundaries
- no NER
- no geocoding
- no LLM extraction
- no alias dictionary beyond the actual string in `MonitoredLocation.name`

### 8.3 Fallback behavior

Fallback behavior is simple:
- return `"Unknown"`

If no monitored location name or city portion appears as a whole-word match in the article text, location is not recognized.

### 8.4 Behavior by case

1. Article contains "Dubai"
   - If `MonitoredLocation.name` contains `Dubai` or the city text starts with `Dubai`, and `Dubai` appears as a whole word in the article, the function returns the canonical monitored name such as `"Dubai, United Arab Emirates"`.

2. Article contains "Singapore"
   - Same logic applies: it matches `Singapore` against monitored locations and returns the monitored location string if present.

3. Article contains "Port of Rotterdam"
   - If there is a monitored location named `Port of Rotterdam` or a city with that name, it can match. Otherwise it remains `Unknown`.
   - Because the logic does not do NER or contextual expansion, a short place name inside a longer phrase may not match properly unless the exact string is present.

4. Article contains "UAE"
   - The function does not check aliases like `UAE`; it only matches the exact strings from `MonitoredLocation.name` and city names. So `UAE` usually fails unless the monitored location string literally contains `UAE`.

5. Article contains "India"
   - It can match only if `India` is in a monitored location name or if the city name is exactly `India` (unlikely in this data). Otherwise it will return `Unknown`.

6. Article contains no geographic reference
   - Returns `Unknown`.

7. Article contains a location not present in Monitored Locations
   - Returns `Unknown`.

### 8.5 Country, region, city, source-country handling

This implementation does not perform:
- country matching beyond the stored `MonitoredLocation.name` string
- region matching beyond the city before a comma
- source-country fallback handling
- geocoding
- alias expansion
- entity linking

If the article mentions a country but not a monitored location, the result is `Unknown`.

---

## Section 9 — Real News Database Examples

The live API `/events/` was queried. The following are examples observed in the running DB.

| Event ID | Title | Description (short) | Source | URL | Current location | Severity | Status | Event time |
|---|---|---|---|---|---|---|---|---|
| 1 | Trump’s 4-Week War With Iran Approaches Month 7 | latest expansion of the war into Yemen is compounding the damage to oil supplies | Reason | https://reason.com/... | Unknown | Unknown | Active | 2026-09-18T23:44:21+05:30 |
| 2 | European Union officials may hold emergency meeting on energy crisis ... | Rising energy costs could exacerbate inflation | Crypto Briefing | ... | Unknown | Unknown | Active | 2026-09-18T23:41:03+05:30 |
| 3 | Kodak Ektar 100 Brings Fine Grain and Vivid Color Saturation | film review, not supply-chain event | PetaPixel | ... | Unknown | Unknown | Active | 2026-09-18T23:39:25+05:30 |
| 4 | Shipping’s New Normal: Slower Trade, Higher Costs, Bigger Pr... | shipping trade context | ... | ... | Unknown | Unknown | Active | ... |
| 5 | JPMorgan admits it cannot forecast oil prices as US-Iran conflict ... | finance/economic issue | ... | ... | Unknown | Unknown | Active | ... |
| 6 | Saudi Arabia cuts off October oil supplies to Europe | oil supply disruption | ... | ... | Unknown | Unknown | Active | ... |
| 7 | US Treasury Secretary to discuss AI, rare earths with Chinese ... | trade/rare earth | ... | ... | Unknown | Unknown | Active | ... |
| 8 | Generation Mining Agrees to a Term Sheet with the Ontario Government | mining/industry | ... | ... | Unknown | Unknown | Active | ... |
| 11 | Full transcript of "Face the Nation" ... | broader political news | ... | ... | Unknown | Unknown | Active | ... |
| 12 | anthriq-services added to PyPI | repository package post | ... | ... | Unknown | Unknown | Active | ... |

### 9.1 Categorization of examples

- `Event 1` — likely `B` or `E` depending on whether the article mentions Yemen or Iran; location is not mapped to monitored site due no monitored location match.
- `Event 2` — likely `C` or `E` because it references the EU, not a monitored site.
- `Event 3` — `C` clearly not supply-chain disruption.
- `Event 4` — `C` or `B`, because shipping terms are present but no monitored site is matched.
- `Event 5` — `C` because it is financial commentary.
- `Event 6` — `E` if treated as source-country-based risk; no actual business location is grounded.
- `Event 7` — `C` or `E` around China; no site-level extraction.
- `Event 8` — `C` or `D` due industry event but no site/location.
- `Event 11` — `C` because it is a transcript / general news item.
- `Event 12` — `C` because it is package repository metadata, no real geographic event.

### 9.2 Important conclusion

The current system does not reliably distinguish between:
- genuine site-specific operational incidents
- generic economic or political updates
- weakly correlated context without real location grounding

This is a major product issue for a risks platform.

---

## Section 10 — Location Intelligence Design

### 10.1 Root cause of “Not specified” / Unknown location

The root cause is structural and explicit in the code:
- `infer_location_from_text()` only checks for exact matches of `MonitoredLocation.name` or the city name before a comma
- it does not use NER, geocoding, aliases, source-country logic, or a geographic knowledge graph
- article text often contains countries, ports, regions, or major cities without being present in `MonitoredLocation.name`
- when no monitored location matches, fallback is `"Unknown"`

This is why the app often reports `Unknown` even when a news story clearly references a meaningful geography.

### 10.2 Comparison of approaches

| Approach | Benefits | Limitations | Cost | Complexity | Suitability |
|---|---|---|---|---|---|
| Monitored-location matching | simple, deterministic, cheap | fails outside preloaded names; weak for city/region aliases | low | low | good baseline |
| Alias dictionary | catches common synonyms like `UAE` -> `United Arab Emirates` | manual maintenance; partial coverage | low | low-medium | useful when combined with monitoring |
| Country/city lookup | helps map to geographies | still not enough for route or port context | low-medium | medium | helpful but not sufficient |
| NLP NER | finds entities in text | not reliable for event-location extraction without tuning and context | medium | medium | promising for a later phase |
| Geocoding | can map city/port/location strings to coordinates | requires clean extraction first; not enough for ambiguous text | medium | medium | good when extraction already works |
| LLM extraction | best semantic interpretation in ambiguous cases | cost, latency, prompt drift, not free | medium/high | medium/high | useful as optional enhancer |
| Hybrid approach | best balance of cost and reliability | more engineering | medium | medium-high | recommended |

### 10.3 Minimal architecture recommendation

The minimal architecture that is reliable enough while remaining free is:
1. Keep monitored-location matching as the first pass.
2. Add a curated alias dictionary for common geography aliases.
3. Add a small country/city normalization layer.
4. Use regex or simple NER only for the most important location entities.
5. Keep geocoding as a fallback when a location string is specific enough.
6. Avoid LLM extraction until the feature is needed and has a clear evaluation path.

This is the best free-first path for a platform of this size.

---

## Section 11 — Complete News Risk Pipeline

### 11.1 Trace

NewsAPI -> filtering -> relevance -> normalization -> event -> risk classification -> severity -> prediction -> recommendation

| Step | Component | Type |
|---|---|---|
| News fetch | `fetch_supply_chain_news()` in `backend/app/integrations/news_api.py` | API client |
| Keyword filtering | `is_supply_chain_related()` | deterministic keyword rule |
| AI relevance check | `relevance_filter.evaluate()` in `backend/app/ai/relevance_filter.py` | zero-shot model |
| Normalization | `normalize_news_event()` in `backend/app/services/event_service.py` | deterministic rule |
| Event save | `save_normalized_event()` in `backend/app/crud/event.py` | database lookup / dedupe |
| AI risk classification | `predict_event()` -> `predict_risk_category()` -> `predict_severity()` in `backend/app/ai/inference.py` | ML classifier + XGBoost |
| Risk creation | `process_event()` in `backend/app/services/ai_pipeline.py` | database write |
| Severity assignment | in `process_event()` from AI output | ML output |
| Prediction save | `Prediction(...)` in `process_event()` | database write |
| Recommendation | `save_generated_recommendation()` using `generate_recommendation()` in `backend/app/ai/recommendation_engine.py` | template |

### 11.2 Summary of each component

- `SUPPLY_CHAIN_KEYWORDS` filter: deterministic keyword rule
- `AIRelevanceFilter`: zero-shot model
- `normalize_news_event`: deterministic rule
- `save_normalized_event`: database dedupe
- `predict_risk_category`: DistilBERT classifier
- `predict_severity`: XGBoost severity model
- `Risk` creation: database write
- `Prediction` creation: database write
- `generate_recommendation`: template / rule-based recommendation mapping

---

## Section 12 — Risk Score Semantics

### 12.1 Where `Risk.risk_score` is calculated

Risk score is calculated in two places:
1. In `process_event()`:
   - `risk.risk_score = ai_result["confidence"] * 100`
2. In `process_weather_event()`:
   - `risk.risk_score = confidence * 100`

`risk_score` is stored as a float percent value.

### 12.2 Where `Prediction.confidence_score` is calculated

This is from the model pipeline:
- `predict_risk_category()` in `backend/app/ai/inference.py`
- The confidence is:
  - `torch.softmax(outputs.logits, dim=1)[0][predicted_class].item()`
- For weather, the code sets `confidence` directly from the rule engine.

### 12.3 Are they the same concept?

They are related but not the same:
- `risk_score` is a display/operational score, usually expressed as a percentage from 0 to 100
- `confidence_score` is the model confidence from the prediction pipeline, typically 0.0 to 1.0

### 12.4 What does 80 mean?

- `risk_score = 80` usually means `80%` in the UI.
- `confidence_score = 0.8` means `80% confidence` in the model’s output.

### 12.5 Can the UI safely say “80% risk”?

Not necessarily.
- In a model context, `confidence_score` is not the same as `probability of event impact`.
- In weather processing, `confidence` is a rule-engine confidence, not a true probability distribution.
- In risk records, `risk_score` is often treated as a dashboard score, not necessarily a calibrated operational probability.

### 12.6 Actual database examples

Examples from live data:
- `Risk id 16`: `risk_score=80.0`, `probability=0.8`, `severity=Low`
- This is an example of a low severity but high `risk_score` relative to the rule logic.
- This demonstrates a mismatch between severity and score as they are used in the UI.

### 12.7 Severity vs score

Severity and score are independent in the implementation:
- `severity` is assigned from a rule or model, and may be `Low` even when `risk_score` is high
- `score` is computed from confidence, which is not always aligned to severity semantics

This is a product-level semantic problem.

---

## Section 13 — Recommendations

### 13.1 How recommendations are generated

File:
- `backend/app/services/recommendation_service.py`
- `save_generated_recommendation(db, prediction_id, category, severity)`

This calls:
- `generate_recommendation(category, severity)` in `backend/app/ai/recommendation_engine.py`

The engine uses a static dictionary:
- `RECOMMENDATION_RULES`
- categories: `Transportation`, `Supplier`, `Natural Disaster`, `Financial`, `Political`
- severity levels: `High`, `Medium`, `Low`

### 13.2 Are they rule-based, template-based, ML-generated, or LLM-generated?

They are rule-based template recommendations.

Not generated by ML and not LLM-generated.

### 13.3 Real examples from the database

Examples observed in the code are generic templates such as:
- `Switch Transport Route`
- `Activate Backup Supplier`
- `Increase Inventory and Reroute Shipments`
- `Review Procurement Budget`
- `Shift Procurement Region`

These are generic responses to categories, not specific to a real article, exact weather measurement, or exact location.

### 13.4 Do recommendations depend on the actual event?

They depend only on:
- `category`
- `severity`

They do not meaningfully depend on:
- exact event content
- actual weather measurements
- exact location
- specific article context
- site-specific routing or supplier information

This makes them generic rather than operationally actionable.

---

## Section 14 — Correlation System

### 14.1 Endpoints

- `GET /correlation/summary` via `backend/app/routers/correlation.py`

### 14.2 Service

- `backend/app/services/correlation_engine.py`
- `correlate_risks(db)`

### 14.3 Algorithm

- Query active risks (`Risk.status == "Active"`)
- Group by `risk.event.location`
- Compute categories per location
- Compute average score and classify overall risk level

### 14.4 Output

Example output structure:
- `location`
- `active_events`
- `categories`
- `overall_score`
- `overall_risk`

### 14.5 Current usage

- Not obviously used in the Dashboard
- Not used in the RiskDetails page
- It is a useful aggregate analytic layer but not yet connected to the main product flow

### 14.6 Relevance to an eventual investigation agent

It is potentially useful for summarizing aggregated hotspots, but it does not provide precise root-cause reasoning and is not currently a strong basis for an investigation agent.

---

## Section 15 — Investigate Functionality

### 15.1 Trace

Frontend:
- `frontend/src/pages/Dashboard.jsx`
- Button click: `navigate(`/risks/${risk.id}`)`

Risk details route:
- `frontend/src/pages/Risks/RiskDetails.jsx`

`fetchRiskDetails(id)` calls:
1. `/risks/{id}`
2. `/events/{risk.event_id}`
3. `/predictions/` then filter by `risk_id`
4. `/recommendations/` then filter by `prediction_id`

Then the page renders the gathered data.

### 15.2 Does it call an LLM / AI model / agent?

No.

### 15.3 What does it do?

It simply displays existing database records assembled into a detail page.

It does not:
- call a reasoning engine
- generate new text from the event
- run a planner
- perform any actual investigation
- correlate beyond the selected risk record and its direct dependents

### 15.4 Conclusion

The current “Investigate” feature is a display-only drilldown, not an investigation engine.

---

## Section 16 — Frontend Product Audit

### 16.1 Dashboard

File:
- `frontend/src/pages/Dashboard.jsx`

Main UI components:
- KPI cards: Active Events, Active Risks, Critical Alerts
- monitored business locations search/add/delete area
- weather check button per location
- recent risk list cards with Investgate button

Useful:
- simple monitoring page
- location search UI
- weather-triggered event ingestion

Misleading / problematic:
- `Active Risks` uses `risks.length`
- weather events can be listed as if they are active risks despite zero-confidence / inactive rules
- a `Clear` weather event still appears as a risk row in the dashboard
- risk score is shown as percent without explaining semantics

### 16.2 Events page

Not directly inspected as a dedicated page in the UI summary, but the `events` API is central to the dashboard.

### 16.3 Risks page

The detail page is `RiskDetails.jsx`.

Useful:
- event + risk + recommendation retrieval is present

Misleading:
- the copy states “Why it matters” but the recommendation is generic and not evidence-driven
- explanation is derived from generic template, not actual analysis

### 16.4 Predictions

Predictions are in the data model and API but appear mostly as raw records, not as a strong narrative or decision support component.

### 16.5 Monitored Locations

The location flow is present but still simplistic:
- user adds monitored location by name
- WeatherAPI search resolves to canonical results
- risk event matching depends on exact textual match with the monitored-site string or city name

This is a good starting skeleton but not a real location intelligence layer.

### 16.6 Not specified / Unknown strings

The app surfaces `Unknown` in many event/location records because the current text-matching logic fails.

This makes the UI feel incomplete and undermines trust.

---

## Section 17 — Live API Check

Observed using the already-running backend:

### Health
- `GET /health`
- response: `{ "database": "Connected Successfully ✅" }`

### Events
- `GET /events/`
- response includes real event rows, including Weather entries such as `Clear`, `Cloudy`, and News entries such as geopolitical and shipping articles.

### Risks
- `GET /risks/`
- response includes risk rows with fields such as `id`, `risk_name`, `risk_score`, `severity`, `probability`, `status`, `event_id`.

### Predictions
- `GET /predictions/`
- present and returns rows with `predicted_risk`, `confidence_score`, `predicted_severity`.

### Recommendations
- `GET /recommendations/`
- present and returns rows with `recommendation_title`, `recommendation_text`, `priority`, `status`.

### Locations
- `/locations/` is protected by authentication, as defined in `backend/app/routers/location.py` through `Depends(get_current_user)`.
- This was not used for a live unauthenticated read in the final verification pass, but the route definition clearly enforces auth.

---

## Section 18 — Database Relationships

### 18.1 Relationship map

- `User` -> `MonitoredLocation` (one-to-many)
- `Event` -> `Risk` (one-to-many)
- `Risk` -> `Prediction` (one-to-many)
- `Prediction` -> `Recommendation` (one-to-many)

### 18.2 Important details

- One `Event` can have multiple `Risk` records.
- One `Risk` can have multiple `Prediction` records.
- One `Prediction` can have multiple `Recommendation` records.

The current design does not prohibit multiple risk rows per event or multiple predictions per risk.

### 18.3 Event location relation

`Location` is not a formal foreign key from `Event` to `MonitoredLocation`. The code only stores a string as `Event.location`.

This matters because the app does not truly model event-to-location joins; it only uses text values.

---

## Section 19 — External API Validation

### 19.1 NewsAPI

Official documentation confirms:
- `GET /v2/everything` returns a `status`, `totalResults`, and an `articles` array.
- Article objects contain fields like `source`, `author`, `title`, `description`, `url`, `urlToImage`, `publishedAt`, and `content`.
- There is no reliable article-location field in the standard object.

What it does not provide:
- no location field for article provenance
- no guaranteed event geolocation
- no site-level or route-level disruption field

### 19.2 WeatherAPI

Official docs confirm the platform provides:
- real-time current weather
- 14-day forecast
- alerts
- air quality
- marine weather
- astronomy
- sports, timezone, and location search

Useful fields currently ignored by the app:
- alerts
- forecast
- forecastday data
- hourly precipitation chances
- severe weather alert fields
- air-quality data
- historical and multi-day risk trends

---

## Section 20 — Final Engineering Assessment

### A. WHAT IS FIXED

- Basic FastAPI app structure and routing are functional.
- Event, Risk, Prediction, Recommendation, and User models are implemented.
- A scheduler exists and runs for automated news collection.
- A live backend and DB connection are working.
- The app can ingest live NewsAPI and WeatherAPI data.
- There is an ML risk classifier and a zero-shot relevance filter in place.
- There is a UI for monitored locations and risk drilldown.

### B. WHAT IS STILL BROKEN

- Location extraction is weak and often returns `Unknown`.
- Weather risk classification is not coherent with the live database behavior.
- Dashboard KPI logic miscounts “active risks”.
- “Investigate” is not an actual investigation engine.
- Recommendation logic is generic template output, not evidence-grounded.
- Weather pipeline underuses WeatherAPI’s strongest features.
- News pipeline is not robust enough to identify true site-level disruption.

### C. ROOT CAUSES

- Exact-text monitored-location matching is too brittle.
- Weather rule logic creates low-confidence event rows that are then counted as active risk rows.
- The system stores summary strings instead of rich structured metadata.
- The UI and backend are not aligned on what “active risk” means.
- There is no true incident-investigation layer.

### D. WEATHER CURRENT STATE

Weather intelligence exists as a basic rule engine, but it is not yet trustworthy operationally. It uses minimal temperature/wind/humidity/precipitation/visibility thresholds and does not leverage forecast or alert data.

### E. NEWS LOCATION CURRENT STATE

News event location extraction is currently a brittle text-matching operation against monitored locations. It is not true location intelligence.

### F. RISK SCORE CURRENT STATE

Risk score is not consistently semantically aligned with severity or confidence. The exact relationship is not robust enough for production use and is misleading in the UI.

### G. INVESTIGATE CURRENT STATE

The Investigate button is a display-only interrogation of the database. It is not an AI investigation engine.

### H. FRONTEND CURRENT STATE

The frontend is functional and visually coherent, but it presents generic and sometimes misleading risk data. It counts all risks as active, shows low-confidence weather as potentially active, and lacks robust explanation.

### I. P0 — MUST FIX BEFORE AGENT 1

1. Fix weather risk semantics and dashboard counting.
   - Reason: otherwise Agent 1 will inherit a broken risk basis.

2. Make location extraction reliable enough to avoid `Unknown` for real geography.
   - Reason: no agent can reason about supply risk without trusted location grounding.

3. Separate “severity”, “confidence”, and “risk score” semantics.
   - Reason: the current data is ambiguous and misleading.

4. Replace the “Investigate” UI-only flow with a real backend retrieval contract.
   - Reason: the later agent needs a clear API contract, not just raw DB display.

### J. P1 — IMPORTANT AFTER AGENT 1

1. Store richer weather and article metadata.
2. Add source-grounded explanation and causal reasoning.
3. Use real route/site impact mapping.
4. Add alert and forecast-based disruption scoring.

### K. P2 — FUTURE

1. Multi-location correlation and event clustering.
2. Historical comparison and trend analysis.
3. Agent 2 response planning.
4. Human-in-the-loop validation and confidence calibration.

### L. PROPOSED IMPLEMENTATION ORDER

1. Fix risk semantics and data model alignment.
2. Improve location extraction and monitored-location matching.
3. Harden weather and news event enrichment.
4. Introduce robust investigation API contract.
5. Only then add Agent 1 for risk investigation.
6. Then add Agent 2 for response planning.

This order keeps the architecture coherent without making the project unnecessarily complex.

---

## Final Assessment

The project has a functioning skeleton for a supply-chain intelligence platform, but it is not yet a technically coherent, trustworthy operational risk system. It does not yet have a production-grade weather intelligence layer or a reliable location-aware news pipeline. The minimum necessary improvements before introducing an investigation agent are not implementation-heavy, but they are essential: fix semantics, fix data grounding, and fix the risk/alert model so the future agent is acting on truthful, actionable inputs.
