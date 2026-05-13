# Smart Dashboard

A personal home-screen dashboard built with Python Dash, designed to run in a browser and auto-refresh every 5 minutes. Currently configured for Aarhus C, Denmark.

## Widgets

| Widget | Source |
|---|---|
| Weather (current + 7-day forecast) | Open-Meteo (free, no key) |
| Public transport departures | Rejseplanen 2.0 API |
| Drive time | Google Maps Distance Matrix API |
| Electricity spot prices (hourly) | elprisenligenu.dk (free, no key) |
| Pollen & air quality | Google Pollen / Air Quality APIs |
| Stocks | Yahoo Finance via `yfinance` |
| News | RSS feed via `feedparser` |
| Google Calendar (day view) | Google Calendar API |
| To-do list | Local state |
| Trash collection schedule | Hard-coded Aarhus C / Kredsløb schedule |

## Setup

**Requirements:** Python 3.12

```bash
# Install dependencies
pip install -r requirements.txt
```

**API keys** — set the following in [config.py](config.py):

| Variable | Used for |
|---|---|
| `GOOGLE_MAPS_KEY` | Drive time (Google Maps Distance Matrix) |
| `TRANSPORT_CONFIG["api_key"]` | Rejseplanen 2.0 journey planner |

Open-Meteo and elprisenligenu.dk are free and require no key.

## Configuration

All location and preference settings live in [config.py](config.py):

- `CITY_CONFIG` — latitude/longitude, timezone, electricity price area (`DK1`/`DK2`)
- `TRANSPORT_CONFIG` — origin/destination coordinates, number of trips shown
- `STOCKS_CONFIG` — list of ticker symbols
- `TRASH_CONFIG` — weekday and week-parity for waste collection schedule
- `REFRESH_INTERVAL_MINUTES` — how often the page auto-reloads

## Running

```bash
# Option A — shell script (uses the system Python 3.12)
./run.sh

# Option B — directly
python app.py
```

Then open [http://localhost:8050](http://localhost:8050) in a browser.

The page reloads automatically every 5 minutes (via `assets/auto_refresh.js`). Each reload fetches fresh data from all APIs in parallel; any failed request falls back gracefully so the rest of the dashboard stays intact.

## Production deployment

The Flask server is exposed as `app.server`, so the app can be served with gunicorn:

```bash
gunicorn app:server -b 0.0.0.0:8050
```

## Project structure

```
app.py             # Entry point, layout, parallel data fetching
config.py          # All user-configurable settings
data_fetchers.py   # One function per API source, all with safe fallbacks
widgets.py         # Dash component builders for each card
assets/            # Static files (CSS, auto_refresh.js)
run.sh             # Convenience launcher using Python 3.12
requirements.txt   # Python dependencies
```
