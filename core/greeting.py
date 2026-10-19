"""
Jarvis -- Greeting Pipeline
Location, weather, and Claude-generated greeting.
"""

import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[1] / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
RAIN_CODES = {51, 53, 55, 61, 63, 65, 71, 73, 75, 80, 81, 82, 95, 96, 99}


def weather_code_to_text(code):
    if code == 0:             return "clear skies"
    if code in (1, 2, 3):    return "partly cloudy"
    if code in (45, 48):     return "foggy"
    if code in (51, 53, 55): return "drizzling"
    if code in (61, 63, 65): return "rain"
    if code in (71, 73, 75): return "snow"
    if code in (80, 81, 82): return "showers"
    if code in (95, 96, 99): return "thunderstorms"
    return "overcast"


def get_location():
    override = os.getenv("LOCATION_CITY")
    lat_override = os.getenv("LOCATION_LAT")
    lon_override = os.getenv("LOCATION_LON")
    if override and lat_override and lon_override:
        return {"city": override, "lat": float(lat_override), "lon": float(lon_override)}
    try:
        r = requests.get("http://ip-api.com/json/", timeout=5)
        d = r.json()
        return {"city": d.get("city", "your city"), "lat": d.get("lat"), "lon": d.get("lon")}
    except Exception:
        return {"city": "your city", "lat": None, "lon": None}


def get_weather(lat, lon):
    if lat is None or lon is None:
        return None
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,weathercode"
            f"&hourly=weathercode"
            f"&temperature_unit=celsius"
            f"&forecast_days=1"
            f"&timezone=auto"
        )
        d = requests.get(url, timeout=5).json()
        current = d.get("current", {})
        temp = current.get("temperature_2m")
        condition = weather_code_to_text(current.get("weathercode", 0))

        now_hour = datetime.now().hour
        forecast_alert = None
        for wc in d.get("hourly", {}).get("weathercode", [])[now_hour:now_hour + 12]:
            if wc in RAIN_CODES:
                forecast_alert = "rain is expected later today"
                break

        return {"temp": temp, "condition": condition, "forecast_alert": forecast_alert}
    except Exception:
        return None


def read_strategy(strategy_path):
    try:
        return Path(strategy_path).read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def generate_greeting(location, weather, strategy_path=None):
    now = datetime.now()
    time_str = now.strftime("%I:%M %p").lstrip("0")
    date_str = now.strftime("%B %d")
    hour = now.hour

    if 6 <= hour < 12:
        period = "morning"
    elif 12 <= hour < 18:
        period = "afternoon"
    else:
        period = "evening"

    weather_str = ""
    if weather:
        weather_str = f"{weather['temp']}C with {weather['condition']} in {location['city']}."
        if weather["forecast_alert"]:
            weather_str += f" {weather['forecast_alert'].capitalize()}."

    if not ANTHROPIC_API_KEY:
        fallback = f"Welcome back, sir. It's {time_str} on {date_str}."
        if weather_str:
            fallback += f" Currently {weather_str}"
        return fallback

    strategy = read_strategy(strategy_path) if strategy_path else ""

    if period == "morning":
        briefing = (
            f"It's morning. Give a brief, focused digest of what to prioritise today "
            f"based on this context: {strategy if strategy else 'no tasks set yet'}"
        )
    elif period == "evening":
        briefing = (
            f"It's evening. Keep a relaxed tone -- suggest one thing to work on tonight "
            f"based on: {strategy if strategy else 'no tasks set yet'}"
        )
    else:
        briefing = (
            f"It's the afternoon. Give a mid-day check-in -- recap what's in progress, "
            f"suggest what to tackle in the next few hours, and keep the energy sharp. "
            f"Based on: {strategy if strategy else 'no tasks set yet'}"
        )

    prompt = f"""You are JARVIS from Iron Man -- calm, British, precise, and occasionally dry.
Generate a spoken greeting for your user. It will be read aloud by a text-to-speech engine.

Facts:
- Current time: {time_str} on {date_str}
- Weather: {weather_str if weather_str else "unknown"}
- {briefing}

Instructions:
- Open with: "Welcome back, sir. It's {time_str} on {date_str}."
- Mention the weather naturally if available (don't just read the data -- weave it in)
- Morning: add 1-2 sentences on what to focus on today
- Afternoon: give a proper mid-day briefing -- what's in progress, what to prioritise next, same depth as morning
- Evening: mention one thing worth working on, casually
- Total length: 4-6 sentences
- No markdown, no bullet points -- this is spoken aloud
- Sound like JARVIS, not a weather app or a task manager"""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        print(f"[greeting] Claude API error: {e}", flush=True)
        return f"Welcome back, sir. It's {time_str} on {date_str}. {weather_str}"
