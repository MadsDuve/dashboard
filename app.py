"""
Smart Dashboard — main entry point.

Run with:
    python app.py

Then open http://localhost:8050 in a browser.
The page auto-refreshes every 5 minutes (see assets/auto_refresh.js).
A full page reload fetches fresh data from all APIs.
"""

import pytz
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import dash
import dash_bootstrap_components as dbc
from dash import html

from config import CITY_CONFIG, REFRESH_INTERVAL_MINUTES
from data_fetchers import (
    fetch_weather,
    fetch_electricity,
    fetch_departures,
    fetch_news,
    fetch_stocks,
)
from widgets import (
    weather_widget,
    transport_widget,
    electricity_widget,
    news_widget,
    stocks_widget,
    mini_calendar_widget,
    pollen_widget,
    todo_widget,
    trash_widget,
)

_TZ = pytz.timezone(CITY_CONFIG["timezone"])

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title=f"Dashboard — {CITY_CONFIG['display_name']}",
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

# Expose the Flask server for production deployment (e.g. gunicorn app:server)
server = app.server


def serve_layout():
    """
    Called on every browser request to generate a fully fresh layout.
    All API data is fetched synchronously here; failed calls return
    safe fallbacks so no individual failure breaks the whole page.
    """
    now = datetime.now(_TZ)

    fetchers = {
        "weather":  fetch_weather,
        "price":    fetch_electricity,
        "departs":  fetch_departures,
        "news":     fetch_news,
        "stocks":   fetch_stocks,
    }
    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fn): key for key, fn in fetchers.items()}
        for future in as_completed(futures, timeout=12):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception:
                results[key] = None

    weather_data = results.get("weather")
    price_data   = results.get("price")
    departures   = results.get("departs") or []
    news_entries = results.get("news") or []
    stocks_data  = results.get("stocks") or {}

    return dbc.Container(
        [
            # ----------------------------------------------------------------
            # Row 1 — Weather | Transport | Mini calendar
            # ----------------------------------------------------------------
            dbc.Row(
                [
                    dbc.Col(
                        weather_widget(weather_data),
                        xs=12, md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        transport_widget(departures),
                        xs=12, md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        mini_calendar_widget(),
                        xs=12, md=4,
                        className="mb-3",
                    ),
                ],
                className="g-3",
            ),

            # ----------------------------------------------------------------
            # Row 2 — To-do | Pollen/Air | Trash
            # ----------------------------------------------------------------
            dbc.Row(
                [
                    dbc.Col(
                        todo_widget(),
                        xs=12, sm=6, md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        pollen_widget(),
                        xs=12, sm=6, md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        trash_widget(),
                        xs=12, sm=6, md=4,
                        className="mb-3",
                    ),
                ],
                className="g-3",
            ),

            # ----------------------------------------------------------------
            # Row 3 — Stocks | Electricity prices | News
            # ----------------------------------------------------------------
            dbc.Row(
                [
                    dbc.Col(
                        stocks_widget(stocks_data),
                        xs=12, md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        electricity_widget(price_data),
                        xs=12, md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        news_widget(news_entries),
                        xs=12, md=4,
                        className="mb-3",
                    ),
                ],
                className="g-3",
            ),

            # ----------------------------------------------------------------
            # Footer
            # ----------------------------------------------------------------
            html.Div(
                [
                    html.Span(
                        f"Last updated: {now.strftime('%H:%M:%S')}",
                        className="footer-ts",
                    ),
                    html.Span(
                        f"  •  Auto-refreshes every {REFRESH_INTERVAL_MINUTES} min",
                        className="footer-hint",
                    ),
                ],
                className="dashboard-footer",
            ),
        ],
        fluid=True,
        className="dashboard-container",
        id="dashboard-root",
    )


# Assign a callable layout so Dash calls serve_layout() on each page load
app.layout = serve_layout


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
