import os
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Read API key from .env
API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5"


class WeatherServiceError(Exception):
    pass


def _check_api_key():
    if not API_KEY:
        raise WeatherServiceError(
            "OPENWEATHER_API_KEY is missing from the .env file."
        )


def get_weather(city: str) -> dict:
    _check_api_key()

    url = f"{BASE_URL}/weather"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10,
        )

        if not response.ok:
            logger.error(
                "OpenWeather error: status=%s response=%s",
                response.status_code,
                response.text,
            )

        response.raise_for_status()

        data = response.json()

        return {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "rainfall": data.get("rain", {}).get("1h", 0),
        }

    except requests.exceptions.RequestException as e:
        logger.error(
            "Weather API request failed for city=%s: %s",
            city,
            e,
        )

        raise WeatherServiceError(
            f"Could not fetch weather for '{city}'."
        ) from e

    except (KeyError, ValueError) as e:
        logger.error(
            "Invalid weather response for city=%s: %s",
            city,
            e,
        )

        raise WeatherServiceError(
            f"Unexpected weather response for '{city}'."
        ) from e


def get_forecast(city: str, days: int = 7) -> list:
    _check_api_key()

    url = f"{BASE_URL}/forecast"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10,
        )

        if not response.ok:
            logger.error(
                "OpenWeather forecast error: status=%s response=%s",
                response.status_code,
                response.text,
            )

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as e:
        logger.error(
            "Forecast API request failed for city=%s: %s",
            city,
            e,
        )

        raise WeatherServiceError(
            f"Could not fetch forecast for '{city}'."
        ) from e

    forecast = []

    for item in data.get("list", []):
        dt_txt = item.get("dt_txt", "")

        if "12:00:00" not in dt_txt:
            continue

        date_str = dt_txt.split(" ")[0]

        day_name = datetime.strptime(
            date_str,
            "%Y-%m-%d"
        ).strftime("%A")

        forecast.append({
            "day": day_name,
            "temp": item["main"]["temp"],
            "humidity": item["main"]["humidity"],
            "rainfall": item.get("rain", {}).get("3h", 0),
        })

        if len(forecast) >= days:
            break

    return forecast
