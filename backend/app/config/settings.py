from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # -----------------------------------------
    # Database
    # -----------------------------------------
    DATABASE_URL: str

    # -----------------------------------------
    # JWT
    # -----------------------------------------
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # -----------------------------------------
    # News API
    # -----------------------------------------
    NEWS_API_KEY: str = ""
    NEWS_API_BASE_URL: str = "https://newsapi.org/v2/everything"

    NEWS_SEARCH_QUERY: str = (
        "supply chain OR logistics OR shipping OR freight "
        "OR port strike OR customs OR semiconductor"
    )

    NEWS_LANGUAGE: str = "en"
    NEWS_PAGE_SIZE: int = 20
    NEWS_TARGETED_QUERIES_ENABLED: bool = True
    NEWS_TARGETED_QUERY_INTERVAL_MINUTES: int = 360
    NEWS_TARGETED_PAGE_SIZE: int = 10
    NEWS_TARGETED_LOCATION_ROTATION: str = "India,United States,Singapore"
    NEWS_TARGETED_QUERY_INDIA: str = (
        'India AND (shipping OR logistics OR "supply chain" OR port OR freight '
        'OR energy OR fuel OR refinery OR imports OR exports) AND '
        '(disruption OR delay OR shortage OR strike OR restriction OR closure '
        'OR congestion OR blockade)'
    )
    NEWS_TARGETED_QUERY_UNITED_STATES: str = (
        '("United States" OR USA OR US) AND '
        '(shipping OR logistics OR "supply chain" OR port OR freight OR energy '
        'OR fuel OR refinery OR imports OR exports) AND '
        '(disruption OR delay OR shortage OR strike OR restriction OR closure '
        'OR congestion OR blockade)'
    )
    NEWS_TARGETED_QUERY_SINGAPORE: str = (
        'Singapore AND (shipping OR logistics OR "supply chain" OR port OR freight '
        'OR container OR maritime OR energy OR fuel OR imports OR exports) AND '
        '(disruption OR delay OR shortage OR strike OR restriction OR closure '
        'OR congestion OR blockade)'
    )

    # -----------------------------------------
    # Currents API
    # -----------------------------------------
    CURRENTS_API_KEY: str = ""
    CURRENTS_API_BASE_URL: str = "https://api.currentsapi.services/v1/search"
    CURRENTS_LANGUAGE: str = "en"
    CURRENTS_PAGE_SIZE: int = 10

    # -----------------------------------------
    # Weather API
    # -----------------------------------------
    WEATHER_API_KEY: str = ""
    WEATHER_API_BASE_URL: str = "http://api.weatherapi.com/v1/current.json"

    DEFAULT_WEATHER_CITY: str = "Singapore"

    # -----------------------------------------
    # Event Defaults
    # -----------------------------------------
    DEFAULT_EVENT_LOCATION: str = "Unknown"
    DEFAULT_EVENT_SEVERITY: str = "Unknown"
    DEFAULT_EVENT_STATUS: str = "Active"
    PRIMARY_INTELLIGENCE_COUNTRIES: str = "India,United States"

    # -----------------------------------------
    # Risk Investigation Agent
    # -----------------------------------------
    INVESTIGATION_PROVIDER: str = "local"
    INVESTIGATION_MODEL_PATH: str = "Qwen/Qwen2.5-0.5B-Instruct"
    INVESTIGATION_MODEL_NAME: str = "Qwen2.5-0.5B-Instruct"
    INVESTIGATION_CONTEXT_TOKENS: int = 4096
    INVESTIGATION_MAX_NEW_TOKENS: int = 500
    INVESTIGATION_TIMEOUT_SECONDS: int = 300
    INVESTIGATION_ALLOWED_ROLES: str = "admin,analyst"
    INVESTIGATION_LOCAL_FILES_ONLY: bool = True

    # -----------------------------------------
    # Scheduler
    # -----------------------------------------
    NEWS_COLLECTION_INTERVAL_MINUTES: int | None = None
    SCHEDULER_INTERVAL_SECONDS: int | None = None

    @property
    def news_collection_interval_minutes(self) -> int:
        if self.NEWS_COLLECTION_INTERVAL_MINUTES is not None:
            return self.NEWS_COLLECTION_INTERVAL_MINUTES
        if self.SCHEDULER_INTERVAL_SECONDS is not None:
            return self.SCHEDULER_INTERVAL_SECONDS
        return 30

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()