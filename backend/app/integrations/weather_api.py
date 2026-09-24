import requests

from app.config.settings import settings
from app.utils.logger import logger


def search_locations(query: str) -> list:
    """
    Use WeatherAPI Search/Autocomplete to resolve a city query into
    structured location results (name, region, country, lat, lon).
    Returns a list of matching location dicts, or [] on error.
    """
    if not query or len(query.strip()) < 2:
        return []

    try:
        response = requests.get(
            "http://api.weatherapi.com/v1/search.json",
            params={"key": settings.WEATHER_API_KEY, "q": query.strip()},
            timeout=8,
        )
        response.raise_for_status()
        results = response.json()
        return [
            {
                "name": r["name"],
                "region": r.get("region", ""),
                "country": r["country"],
                "lat": r["lat"],
                "lon": r["lon"],
                # Canonical label stored in DB: "Name, Country"
                "display": f"{r['name']}, {r['country']}",
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"WeatherAPI search failed: {e}")
        return []


def fetch_weather_data(city: str = None):
    """
    Fetch current weather for the configured logistics hub or specified city.
    """

    target_city = city if city else settings.DEFAULT_WEATHER_CITY

    params = {
        "key": settings.WEATHER_API_KEY,
        "q": target_city,
        "aqi": "no",
    }

    try:
        logger.info(
            f"Requesting weather data for {target_city}..."
        )

        response = requests.get(
            settings.WEATHER_API_BASE_URL,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        # Build canonical location string: "City, Country" from the API response.
        # This ensures consistent representation regardless of what the user typed.
        canonical_location = f"{data['location']['name']}, {data['location']['country']}"

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

        logger.info("Weather data fetched successfully.")

        return weather

    except requests.exceptions.RequestException as e:
        logger.error(f"Weather API request failed: {str(e)}")

        return {
            "status": "error",
            "message": str(e),
        }