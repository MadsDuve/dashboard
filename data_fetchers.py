"""
Data fetching functions for each API source.
All functions return data or a safe fallback (None / empty list / empty dict)
so the rest of the application never crashes on network failures.
"""

import requests
import pytz
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import feedparser
import yfinance as yf

from config import CITY_CONFIG, TRANSPORT_CONFIG, STOCKS_CONFIG, GOOGLE_MAPS_KEY

_TZ = pytz.timezone(CITY_CONFIG["timezone"])


# ---------------------------------------------------------------------------
# Weather — Open-Meteo (free, no API key required)
# ---------------------------------------------------------------------------

def fetch_weather() -> dict | None:
    """
    Fetch current conditions, hourly forecast, and 7-day daily forecast
    from Open-Meteo for the configured city coordinates.
    """
    lat = CITY_CONFIG["latitude"]
    lon = CITY_CONFIG["longitude"]
    tz  = CITY_CONFIG["timezone"]

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,apparent_temperature,weather_code,"
        "wind_speed_10m,precipitation,relative_humidity_2m"
        "&hourly=temperature_2m,weather_code,precipitation_probability"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min,"
        "precipitation_probability_max,sunrise,sunset"
        f"&timezone={tz}&forecast_days=7&wind_speed_unit=ms"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Electricity prices — elprisenligenu.dk (free, no API key required)
# ---------------------------------------------------------------------------

def fetch_electricity() -> list | None:
    """
    Fetch today's hourly spot prices (DKK/kWh) for the configured price area.
    Returns a list of 24 dicts with keys: DKK_per_kWh, time_start, time_end.
    """
    area = CITY_CONFIG["electricity_price_area"]
    now  = datetime.now(_TZ)
    url  = (
        f"https://www.elprisenligenu.dk/api/v1/prices/"
        f"{now.year}/{now.month:02d}-{now.day:02d}_{area}.json"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public transport — Rejseplanen trip planner
# ---------------------------------------------------------------------------

def _nearest_stop_id(lat: float, lon: float, key: str) -> str | None:
    """Return the extId of the nearest stop to the given coordinates."""
    try:
        r = requests.get(
            "https://www.rejseplanen.dk/api/location.nearbystops",
            params={
                "originCoordLat": lat,
                "originCoordLong": lon,
                "maxNo": 1,
                "format": "json",
                "accessId": key,
            },
            timeout=10,
        )
        r.raise_for_status()
        stops = r.json().get("stopLocationOrCoordLocation", [])
        if stops:
            return stops[0].get("StopLocation", {}).get("extId")
    except Exception:
        pass
    return None


def fetch_journeys() -> list:
    """
    Fetch upcoming journeys from origin to destination via Rejseplanen trip API.
    Looks up the nearest stop to each address coordinate, then queries the
    trip planner. Returns a list of journey dicts:
      depart, arrive, duration_min, transfers, legs
    where each leg has: line, type, color.
    """
    import re
    now = datetime.now(_TZ)
    cfg = TRANSPORT_CONFIG
    key = cfg["api_key"]

    origin_id = _nearest_stop_id(cfg["origin"]["lat"], cfg["origin"]["lon"], key)
    dest_id   = _nearest_stop_id(cfg["destination"]["lat"], cfg["destination"]["lon"], key)
    if not origin_id or not dest_id:
        return []

    try:
        resp = requests.get(
            "https://www.rejseplanen.dk/api/trip",
            params={
                "originId":  origin_id,
                "destId":    dest_id,
                "date":      now.strftime("%Y-%m-%d"),
                "time":      now.strftime("%H:%M"),
                "numTrips":  cfg["num_trips"],
                "format":    "json",
                "accessId":  key,
            },
            timeout=10,
        )
        resp.raise_for_status()
        trips_raw = resp.json().get("Trip", [])
        if isinstance(trips_raw, dict):
            trips_raw = [trips_raw]
    except Exception:
        return []

    _CAT_MAP = {
        "INTERCITY": "IC", "IC": "IC", "LYN": "LYN", "ICE": "ICE",
        "REGIONALTOG": "REG", "REG": "REG",
        "S-TOG": "S", "S": "S",
        "METRO": "M",
        "BYBUS": "BUS", "BUS": "BUS", "LOKALBUS": "BUS",
        "LETBANE": "LET",
    }
    _LINE_COLORS = {
        "IC": "#c8102e", "ICE": "#c8102e", "LYN": "#c8102e",
        "REG": "#004b93", "S": "#f7a600",
        "BUS": "#007a4d", "M": "#009b77", "LET": "#0072b1",
    }

    def _parse_duration(iso: str) -> int:
        """Convert PT1H05M, PT35M, or PT1H to total minutes."""
        h = re.search(r"(\d+)H", iso)
        m = re.search(r"(\d+)M", iso)
        return (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0)

    journeys = []
    for trip in trips_raw:
        legs_raw = trip.get("LegList", {}).get("Leg", [])
        if isinstance(legs_raw, dict):
            legs_raw = [legs_raw]

        if not legs_raw:
            continue

        depart  = legs_raw[0].get("Origin",      {}).get("time", "")[:5]
        arrive  = legs_raw[-1].get("Destination", {}).get("time", "")[:5]
        dur_min = _parse_duration(trip.get("duration", "PT0M"))

        legs = []
        for leg in legs_raw:
            prod = leg.get("Product", {})
            if isinstance(prod, list):
                prod = prod[0] if prod else {}
            cat  = (prod.get("catOut") or leg.get("type", "BUS")).upper()
            line = prod.get("displayNumber") or leg.get("name", "?")
            # Walking legs ("Gå") get a neutral grey style
            if leg.get("type", "").upper() == "WALK" or "GÅ" in line.upper():
                legs.append({"line": "🚶", "type": "WALK", "color": "#aaa"})
            else:
                ltype = _CAT_MAP.get(cat, "BUS")
                legs.append({
                    "line":  line,
                    "type":  ltype,
                    "color": _LINE_COLORS.get(ltype, "#555"),
                })

        # Count only transit legs (not walks) as transfers
        transit_legs = [l for l in legs if l["type"] != "WALK"]
        journeys.append({
            "depart":       depart,
            "arrive":       arrive,
            "duration_min": dur_min,
            "transfers":    max(0, len(transit_legs) - 1),
            "legs":         legs,
        })

    return journeys[:cfg["num_trips"]]


# ---------------------------------------------------------------------------
# Traffic — Vejdirektoratet (public WFS feed, no key required)
# ---------------------------------------------------------------------------

def fetch_traffic_events() -> list:
    """
    Fetch active traffic events / roadworks from Vejdirektoratet's open feed.
    Returns a list of feature dicts.  Falls back to [] on failure.
    """
    url = (
        "https://api.vejdirektoratet.dk/v2/traffic"
        "?api_key=&lang=da&type=trafikmelding"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json().get("features", [])[:8]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Drive time — OSRM public demo server (free, no API key required)
# ---------------------------------------------------------------------------

def fetch_drive_time() -> int | None:
    """
    Estimate driving time in minutes from origin to destination using the
    Google Maps Routes API with live traffic (TRAFFIC_AWARE routing).
    Returns integer minutes or None on failure.
    Requires the Routes API to be enabled in Google Cloud Console.
    """
    cfg = TRANSPORT_CONFIG
    o   = cfg["origin"]
    d   = cfg["destination"]
    key = GOOGLE_MAPS_KEY
    try:
        resp = requests.post(
            "https://routes.googleapis.com/directions/v2:computeRoutes",
            headers={
                "X-Goog-Api-Key":   key,
                "X-Goog-FieldMask": "routes.duration",
            },
            json={
                "origin":      {"location": {"latLng": {"latitude": o["lat"], "longitude": o["lon"]}}},
                "destination": {"location": {"latLng": {"latitude": d["lat"], "longitude": d["lon"]}}},
                "travelMode":        "DRIVE",
                "routingPreference": "TRAFFIC_AWARE",
            },
            timeout=10,
        )
        resp.raise_for_status()
        routes = resp.json().get("routes", [])
        if not routes:
            return None
        # duration is a string like "3456s"
        duration_str = routes[0].get("duration", "0s")
        secs = int(duration_str.rstrip("s"))
        return round(secs / 60)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Pollen — Google Pollen API
# ---------------------------------------------------------------------------

def fetch_pollen() -> list:
    """
    Fetch today's pollen forecast for GRASS, TREE, and WEED from the
    Google Pollen API.  Returns a list of dicts:
      { name, value (0-5), category, in_season }
    Falls back to [] on failure.
    """
    lat = CITY_CONFIG["latitude"]
    lon = CITY_CONFIG["longitude"]
    try:
        resp = requests.get(
            "https://pollen.googleapis.com/v1/forecast:lookup",
            params={
                "key":                GOOGLE_MAPS_KEY,
                "location.latitude":  lat,
                "location.longitude": lon,
                "days":               1,
            },
            timeout=10,
        )
        resp.raise_for_status()
        types = resp.json().get("dailyInfo", [{}])[0].get("pollenTypeInfo", [])
        result = []
        for t in types:
            info = t.get("indexInfo")
            if not info:
                continue
            result.append({
                "name":      t.get("displayName", t["code"].title()),
                "value":     info.get("value", 0),       # 0–5 scale
                "category":  info.get("category", ""),
                "in_season": t.get("inSeason", False),
            })
        return result
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Air quality — Google Air Quality API
# ---------------------------------------------------------------------------

def fetch_air_quality() -> dict | None:
    """
    Fetch current air quality conditions from Google Air Quality API.
    Returns a dict: { aqi, aqi_display, category, dominant_pollutant }
    or None on failure.
    """
    lat = CITY_CONFIG["latitude"]
    lon = CITY_CONFIG["longitude"]
    try:
        resp = requests.post(
            "https://airquality.googleapis.com/v1/currentConditions:lookup",
            headers={"X-Goog-Api-Key": GOOGLE_MAPS_KEY},
            json={"location": {"latitude": lat, "longitude": lon}},
            timeout=10,
        )
        resp.raise_for_status()
        indexes = resp.json().get("indexes", [])
        if not indexes:
            return None
        idx = indexes[0]
        return {
            "aqi":               idx.get("aqi", 0),
            "aqi_display":       idx.get("aqiDisplay", "?"),
            "category":          idx.get("category", ""),
            "dominant_pollutant": idx.get("dominantPollutant", "").upper(),
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# News — DR.dk public RSS feed (no API key required)
# ---------------------------------------------------------------------------

def fetch_news() -> list:
    """
    Parse DR's all-news RSS feed and return the latest entries.
    Uses requests (which has working SSL) to fetch, then feedparser to parse.
    """
    try:
        resp = requests.get(
            "https://www.dr.dk/nyheder/service/feeds/allenyheder",
            timeout=10,
        )
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        return feed.entries[:3]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Stocks — Yahoo Finance via yfinance (no API key required)
# ---------------------------------------------------------------------------

def _fetch_single_stock(ticker: str) -> tuple:
    t = yf.Ticker(ticker)

    # Intraday: 5-minute bars for today
    intraday = t.history(period="1d", interval="5m")
    # Previous close for % change: use last daily close from yesterday
    daily = t.history(period="5d", interval="1d")

    if intraday.empty or daily.empty or len(daily) < 2:
        return ticker, None

    closes     = intraday["Close"].tolist()
    current    = closes[-1]
    prev_close = daily["Close"].iloc[-2]   # yesterday's close
    change     = ((current - prev_close) / prev_close) * 100
    name       = t.info.get("shortName", ticker)
    return ticker, {"price": current, "change": change, "history": closes, "prev_close": prev_close, "name": name}


def fetch_stocks() -> dict:
    """
    Fetch recent closing prices and compute daily % change for each ticker.
    Runs all tickers in parallel with a 10-second total timeout.
    Returns a dict: { ticker: { price, change, history, name } }
    """
    results = {}
    with ThreadPoolExecutor(max_workers=len(STOCKS_CONFIG["tickers"])) as executor:
        futures = {executor.submit(_fetch_single_stock, t): t for t in STOCKS_CONFIG["tickers"]}
        for future in as_completed(futures, timeout=10):
            try:
                ticker, data = future.result()
                if data:
                    results[ticker] = data
            except Exception:
                continue
    return results
