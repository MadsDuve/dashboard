"""
Dashboard Configuration
Modify these settings to adapt the dashboard to a different city.
"""

CITY_CONFIG = {
    "name": "Aarhus",
    "display_name": "Aarhus C",
    "latitude": 56.1629,
    "longitude": 10.2039,
    "timezone": "Europe/Copenhagen",
    "electricity_price_area": "DK1",  # DK1 = Western DK, DK2 = Eastern DK
}

TRANSPORT_CONFIG = {
    # Rejseplanen stop ID for Aarhus H (main train station).
    # Use https://xmlopen.rejseplanen.dk/bin/rest.exe/location?input=Aarhus+H&format=json to find other stop IDs.
    "stop_id": "008600053",
    "stop_name": "Aarhus H",
    "api_key": "c9f2faa4-93f7-4d57-a4aa-b5533ca6fbfe",
    "max_departures": 8,
}

STOCKS_CONFIG = {
    "tickers": ["ENR.DE", "JYSK.CO", "NOVO-B.CO"],
    "history_period": "5d",
}

TRASH_CONFIG = {
    # Aarhus C hard-coded schedule (Kredsløb does not expose a public API).
    # weekday: 0=Monday … 6=Sunday
    "general_waste_weekday": 3,   # Thursday
    "recycling_weekday": 1,        # Tuesday (bi-weekly)
    "recycling_week_parity": 1,    # 1 = odd ISO weeks, 0 = even ISO weeks
}

# Auto-refresh interval shown to the user (JS handles the actual reload)
REFRESH_INTERVAL_MINUTES = 5

# Visual
WEATHER_BG_COLOR = "#1e3d5e"
CARD_BG_COLOR = "#ffffff"
PAGE_BG_COLOR = "#c8a882"
