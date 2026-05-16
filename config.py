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

GOOGLE_MAPS_KEY = "AIzaSyAivSGV6wib5refL90ehe64aD-PhFkTh3g"

TRANSPORT_CONFIG = {
    "api_key": "c9f2faa4-93f7-4d57-a4aa-b5533ca6fbfe",
    "origin": {
        "name": "Tage-Hansens Gade 17, Aarhus C",
        "lat": 56.1537,
        "lon": 10.2038,
    },
    "destination": {
        "name": "Anders Dams Passage, Silkeborg",
        "lat": 56.1689402,
        "lon": 9.5469173,
    },
    "num_trips": 3,
}

STOCKS_CONFIG = {
    "tickers": ["DSV.CO", "JYSK.CO", "NOVO-B.CO", "VWS.CO", "MAERSK-B.CO"],
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
