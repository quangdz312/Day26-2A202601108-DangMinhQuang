from typing import Any
import httpx
import logging
import os
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
port = int(os.getenv("PORT", 8085))
mcp = FastMCP("weather", host="0.0.0.0", port=port)

# Constants
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"
USER_AGENT = "weather-app/1.0"

logger = logging.getLogger(__name__)

async def make_weather_request(endpoint: str, params: dict[str, str]) -> dict[str, Any] | None:
    """Make a request to the WeatherAPI with proper error handling."""
    api_key = os.getenv("WEATHERAPI_KEY")
    # Check if API key is set
    if not api_key:
        logger.error("WeatherAPI key not set. Set WEATHERAPI_KEY before starting the server.")
        return None
        
    headers = {
        "User-Agent": USER_AGENT,
    }
    # Do not mutate the caller's dictionary.
    request_params = {**params, "key": api_key}
    
    url = f"{WEATHERAPI_BASE}/{endpoint}"
    
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        try:
            response = await client.get(url, params=request_params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning("WeatherAPI returned HTTP %s", e.response.status_code)
            return None
        except httpx.RequestError as e:
            logger.warning("WeatherAPI request failed: %s", e)
            return None
        except ValueError as e:
            logger.warning("WeatherAPI returned invalid JSON: %s", e)
            return None

@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Get current weather conditions for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney")
    """
    city = city.strip()
    if not city:
        return "City must not be empty."

    params = {
        "q": city,
        "aqi": "no"
    }
    
    data = await make_weather_request("current.json", params)

    if not data:
        if not os.getenv("WEATHERAPI_KEY"):
            return "WeatherAPI key is not configured. Set WEATHERAPI_KEY and restart the server."
        return f"Unable to fetch current weather data for {city}. Please check the city name and API key configuration."

    current = data["current"]
    location = data["location"]
    
    return f"""
Current Weather for {location['name']}, {location['region']}, {location['country']}:

Temperature: {current['temp_c']}°C ({current['temp_f']}°F)
Feels like: {current['feelslike_c']}°C ({current['feelslike_f']}°F)
Condition: {current['condition']['text']}
Humidity: {current['humidity']}%
Wind: {current['wind_kph']} km/h ({current['wind_mph']} mph) {current['wind_dir']}
Pressure: {current['pressure_mb']} mb
UV Index: {current['uv']}
Visibility: {current['vis_km']} km

Last updated: {current['last_updated']}
"""

@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney", "Melbourne")
        days: Number of days to forecast (1-3 for free tier, max 10 for paid)
    """
    city = city.strip()
    if not city:
        return "City must not be empty."
    if not 1 <= days <= 3:
        return "Days must be between 1 and 3."
    
    params = {
        "q": city,
        "days": str(days),
        "aqi": "no",
        "alerts": "no"
    }
    
    data = await make_weather_request("forecast.json", params)

    if not data:
        if not os.getenv("WEATHERAPI_KEY"):
            return "WeatherAPI key is not configured. Set WEATHERAPI_KEY and restart the server."
        return f"Unable to fetch forecast data for {city}. Please check the city name and API key configuration."

    location = data["location"]
    forecast_days = data["forecast"]["forecastday"]
    
    forecasts = []
    forecasts.append(f"Weather Forecast for {location['name']}, {location['region']}, {location['country']}:")
    
    for day in forecast_days:
        day_data = day["day"]
        date = day["date"]
        
        forecast = f"""
{date}:
High: {day_data['maxtemp_c']}°C ({day_data['maxtemp_f']}°F)
Low: {day_data['mintemp_c']}°C ({day_data['mintemp_f']}°F)
Condition: {day_data['condition']['text']}
Chance of Rain: {day_data['daily_chance_of_rain']}%
Max Wind: {day_data['maxwind_kph']} km/h
UV Index: {day_data['uv']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def health_check() -> str:
    """Health check endpoint for deployment verification."""
    return "✅ Weather MCP Server is running! Ready to provide weather data for Australian cities and worldwide."

if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    logger.info("Starting weather MCP server on http://0.0.0.0:%s/mcp", port)
    mcp.run(transport="streamable-http")
