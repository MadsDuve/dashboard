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

from config import CITY_CONFIG, TRANSPORT_CONFIG, STOCKS_CONFIG

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
# Public transport — Rejseplanen HAFAS API
# ---------------------------------------------------------------------------

def fetch_departures() -> list:
    """
    Fetch upcoming departures from the configured stop via Rejseplanen API 2.0.
    Returns a list of departure dicts. Each entry has:
      name, type, stop, direction, time (HH:MM:SS), date (YYYY-MM-DD),
      rtTime (real-time, optional), ProductAtStop (with catOut, displayNumber).
    """
    now     = datetime.now(_TZ)
    stop_id = TRANSPORT_CONFIG["stop_id"]
    api_key = TRANSPORT_CONFIG["api_key"]
    max_dep = TRANSPORT_CONFIG["max_departures"]

    url = (
        "https://www.rejseplanen.dk/api/departureBoard"
        f"?id={stop_id}"
        f"&date={now.strftime('%Y-%m-%d')}"
        f"&time={now.strftime('%H:%M')}"
        f"&maxJourneys={max_dep}"
        "&format=json"
        f"&accessId={api_key}"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # API 2.0: departures are directly under key "Departure"
        departures = data.get("Departure", [])
        if isinstance(departures, dict):
            departures = [departures]
        return departures[:max_dep]
    except Exception:
        return []


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
    t    = yf.Ticker(ticker)
    hist = t.history(period=STOCKS_CONFIG["history_period"])
    if len(hist) < 2:
        return ticker, None
    closes  = hist["Close"].tolist()
    current = closes[-1]
    prev    = closes[-2]
    change  = ((current - prev) / prev) * 100
    name    = t.info.get("shortName", ticker)
    return ticker, {"price": current, "change": change, "history": closes, "name": name}


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
