"""
Widget builders: each function returns a Dash html.Div ready for the layout.
Every builder accepts its data as an argument and handles None / empty input
gracefully so the dashboard never crashes when an API is unavailable.
"""

import calendar as _cal
import pytz
from datetime import datetime, timedelta

import plotly.graph_objects as go
from dash import dcc, html

from config import CITY_CONFIG, TRASH_CONFIG

_TZ = pytz.timezone(CITY_CONFIG["timezone"])

# ---------------------------------------------------------------------------
# Helper maps
# ---------------------------------------------------------------------------

_WMO_ICON = {
    0: "☀️",
    1: "🌤️", 2: "⛅", 3: "☁️",
    45: "🌫️", 48: "🌫️",
    51: "🌦️", 53: "🌦️", 55: "🌧️",
    56: "🌧️", 57: "🌧️",
    61: "🌧️", 63: "🌧️", 65: "🌧️",
    66: "🌨️", 67: "🌨️",
    71: "🌨️", 73: "❄️", 75: "❄️", 77: "❄️",
    80: "🌦️", 81: "🌧️", 82: "⛈️",
    85: "🌨️", 86: "❄️",
    95: "⛈️", 96: "⛈️", 99: "⛈️",
}

_WMO_DESC = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    56: "Light freezing drizzle", 57: "Freezing drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Light showers", 81: "Rain showers", 82: "Heavy showers",
    85: "Light snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm w. hail", 99: "Heavy thunderstorm",
}

_DAYS_SHORT = ["Mon.", "Tue.", "Wed.", "Thu.", "Fri.", "Sat.", "Sun."]
_DAYS_LONG  = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
_MONTHS_DK  = [
    "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
    "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER",
]



def _wmo_icon(code: int) -> str:
    return _WMO_ICON.get(code, "🌡️")


def _wmo_desc(code: int) -> str:
    return _WMO_DESC.get(code, "Unknown weather")


def _fmt_dk(value: float, decimals: int = 2) -> str:
    """Format a number with thousands separator and fixed decimals."""
    return f"{value:,.{decimals}f}"


# ---------------------------------------------------------------------------
# Weather widget
# ---------------------------------------------------------------------------

def weather_widget(data: dict | None) -> html.Div:
    """Dark-blue weather widget with current conditions, hourly and daily forecasts."""
    if not data:
        return html.Div(
            html.Div("Weather data unavailable", className="widget-error"),
            className="widget weather-widget",
        )

    now     = datetime.now(_TZ)
    current = data.get("current", {})
    hourly  = data.get("hourly",  {})
    daily   = data.get("daily",   {})

    temp       = round(current.get("temperature_2m", 0))
    feels_like = round(current.get("apparent_temperature", temp))
    wmo        = current.get("weather_code", 0)
    wind       = round(current.get("wind_speed_10m", 0))
    humidity   = round(current.get("relative_humidity_2m", 0))

    max_today  = round(daily["temperature_2m_max"][0]) if daily.get("temperature_2m_max") else "?"
    min_today  = round(daily["temperature_2m_min"][0]) if daily.get("temperature_2m_min") else "?"

    # --- Hourly forecast: next 6 hours ---
    h_times  = hourly.get("time", [])
    h_temps  = hourly.get("temperature_2m", [])
    h_codes  = hourly.get("weather_code", [])
    h_precip = hourly.get("precipitation_probability", [])

    hourly_items = []
    count = 0
    for i, t in enumerate(h_times):
        try:
            dt = _TZ.localize(datetime.strptime(t, "%Y-%m-%dT%H:%M"))
        except ValueError:
            continue
        if dt > now and count < 12:
            hourly_items.append(
                html.Div([
                    html.Div(f"{dt.hour:02d}", className="hour-time"),
                    html.Div(_wmo_icon(h_codes[i] if i < len(h_codes) else 0), className="hour-icon"),
                    html.Div(f"{round(h_temps[i])}°" if i < len(h_temps) else "?", className="hour-temp"),
                    html.Div(
                        f"{h_precip[i]}%" if i < len(h_precip) and h_precip[i] else "",
                        className="hour-precip",
                    ),
                ], className="hourly-item")
            )
            count += 1

    # --- Daily forecast: next 5 days ---
    d_dates  = daily.get("time", [])
    d_codes  = daily.get("weather_code", [])
    d_max    = daily.get("temperature_2m_max", [])
    d_min    = daily.get("temperature_2m_min", [])
    d_precip = daily.get("precipitation_probability_max", [])

    daily_rows = []
    for i in range(1, min(4, len(d_dates))):
        prob        = d_precip[i] if i < len(d_precip) and d_precip[i] else 0
        bar_pct     = int(prob)
        day_date    = datetime.strptime(d_dates[i], "%Y-%m-%d")
        day_label   = _DAYS_SHORT[day_date.weekday()]

        daily_rows.append(
            html.Div([
                html.Span(day_label, className="daily-day"),
                html.Span(_wmo_icon(d_codes[i] if i < len(d_codes) else 0), className="daily-icon"),
                html.Div(
                    html.Div(
                        style={
                            "width": f"{bar_pct}%",
                            "height": "4px",
                            "backgroundColor": "#4dd0c4",
                            "borderRadius": "2px",
                            "minWidth": "6px",
                        }
                    ),
                    className="daily-bar-track",
                ),
                html.Span(f"{round(d_min[i])}°" if i < len(d_min) else "?", className="daily-min"),
                html.Span(f"{round(d_max[i])}°" if i < len(d_max) else "?", className="daily-max"),
            ], className="daily-item")
        )

    return html.Div([
        # Header row: city + icon
        html.Div([
            html.Span(f"{CITY_CONFIG['display_name']} ↗", className="weather-city"),
            html.Span(_wmo_icon(wmo), className="weather-main-icon"),
        ], className="weather-header"),

        # Temperature + description
        html.Div([
            html.Span(f"{temp}°", className="weather-temp"),
            html.Div([
                html.Div(_wmo_desc(wmo), className="weather-desc"),
                html.Div(f"H: {max_today}°  L: {min_today}°", className="weather-hl"),
                html.Div(
                    f"Feels like {feels_like}°  💨 {wind} m/s  💧 {humidity}%",
                    className="weather-extra",
                ),
            ], className="weather-desc-block"),
        ], className="weather-current"),

        # Hourly scroll
        html.Div(hourly_items, className="hourly-forecast"),
        html.Hr(className="weather-divider"),

        # Daily rows
        html.Div(daily_rows, className="daily-forecast"),
    ], className="widget weather-widget")


# ---------------------------------------------------------------------------
# Public transport widget
# ---------------------------------------------------------------------------

def transport_widget(journeys: list, drive_time: int | None = None) -> html.Div:
    """Shows next 3 journeys from home to destination, plus a car time estimate."""
    if not journeys:
        body = html.Div(
            "No journeys available – check API key or connection.",
            className="widget-error",
        )
    else:
        cards = []
        for j in journeys:
            leg_badges = [
                html.Span(
                    leg["line"],
                    className="dep-line",
                    style={"backgroundColor": leg["color"]},
                )
                for leg in j["legs"]
            ]
            transfers = j["transfers"]
            transfer_txt = (
                "Direct" if transfers == 0
                else f"{transfers} transfer{'s' if transfers > 1 else ''}"
            )
            cards.append(
                html.Div([
                    # Left: depart → arrive
                    html.Div([
                        html.Span(j["depart"], className="journey-depart"),
                        html.Span(" → ", className="journey-arrow"),
                        html.Span(j["arrive"], className="journey-arrive"),
                    ], className="journey-times"),
                    # Middle: line badges
                    html.Div(leg_badges, className="journey-legs"),
                    # Right: duration + transfers
                    html.Div([
                        html.Div(f"{j['duration_min']} min", className="journey-duration"),
                        html.Div(transfer_txt, className="journey-transfers"),
                    ], className="journey-meta"),
                ], className="journey-card")
            )
        body = html.Div(cards, className="journey-list")

    # Car travel time row
    if drive_time is not None:
        car_row = html.Div([
            html.Span("🚗", style={"fontSize": "0.9rem", "marginRight": "6px"}),
            html.Span(f"By car: approx. {drive_time} min, including traffic", className="drive-time-text"),
        ], className="drive-time-row")
    else:
        car_row = html.Div()

    return html.Div([
        html.Div([
            html.Span("🚌", className="widget-icon"),
            html.Span("Home → Work"),
            html.Span(
                datetime.now(_TZ).strftime("%H:%M"),
                className="widget-timestamp",
            ),
        ], className="widget-title"),
        body,
        car_row,
    ], className="widget transport-widget")


# ---------------------------------------------------------------------------
# Electricity prices widget
# ---------------------------------------------------------------------------

def electricity_widget(prices: list | None) -> html.Div:
    """Hourly electricity price bar chart."""
    title_row = html.Div([
        html.Span("⚡", className="widget-icon"),
        html.Span("Electricity Prices (DK1)"),
    ], className="widget-title")

    if not prices:
        return html.Div([
            title_row,
            html.Div("Price data unavailable.", className="widget-error"),
        ], className="widget electricity-widget")

    now          = datetime.now(_TZ)
    current_hour = now.hour

    hours, values, colors = [], [], []
    for entry in prices:
        try:
            h     = int(entry["time_start"].split("T")[1][:2])
            price = round(entry["DKK_per_kWh"], 2)
            hours.append(h)
            values.append(price)
            if h == current_hour:
                colors.append("#e74c3c")
            elif price > 2.5:
                colors.append("#e7923c")
            elif price > 1.5:
                colors.append("#f3e012")
            else:
                colors.append("#38f10f")
        except (KeyError, IndexError, ValueError):
            continue

    if not hours:
        return html.Div([title_row, html.Div("No price data.", className="widget-error")],
                        className="widget electricity-widget")

    current_price = next(
        (values[i] for i, h in enumerate(hours) if h == current_hour), None
    )
    price_label = f" — {_fmt_dk(current_price)} kr/kWh now" if current_price is not None else ""

    fig = go.Figure(go.Bar(
        x=[f"{h:02d}" for h in hours],
        y=values,
        marker_color=colors,
        hovertemplate="%{x}:00<br>%{y:.2f} kr/kWh<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(l=28, r=8, t=8, b=28),
        paper_bgcolor="white",
        plot_bgcolor="white",
        height=170,
        xaxis=dict(
            tickfont=dict(size=9, color="#aaa"),
            gridcolor="rgba(0,0,0,0)",
            tickmode="array",
            tickvals=[f"{h:02d}" for h in hours[::2]],
            ticktext=[f"{h:02d}" for h in hours[::2]],
        ),
        yaxis=dict(
            tickfont=dict(size=9, color="#aaa"),
            gridcolor="rgba(0,0,0,0.06)",
            tickformat=".2f",
        ),
        showlegend=False,
    )

    return html.Div([
        html.Div([
            html.Span("⚡", className="widget-icon"),
            html.Span("Electricity Prices (DK1)"),
            html.Span(price_label, className="widget-sub"),
        ], className="widget-title"),
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
    ], className="widget electricity-widget")


# ---------------------------------------------------------------------------
# News widget
# ---------------------------------------------------------------------------

def news_widget(entries: list) -> html.Div:
    """Shows latest Danish news items from DR."""
    if not entries:
        items = [html.Div("Nyheder ikke tilgængelige.", className="widget-error")]
    else:
        items = []
        for e in entries:
            title   = getattr(e, "title", "") or ""
            tags    = getattr(e, "tags", []) or []
            cat     = tags[0]["term"] if tags else "Nyheder"
            is_live = "live" in title.lower()

            items.append(
                html.Div([
                    html.Span(
                        ("● " if is_live else "") + cat,
                        className="news-cat",
                        style={"backgroundColor": "#e74c3c" if is_live else "#444"},
                    ),
                    html.Div(
                        title[:90] + ("…" if len(title) > 90 else ""),
                        className="news-title",
                    ),
                ], className="news-item")
            )

    return html.Div([
        html.Div([
            html.Span("📰", className="widget-icon"),
            html.Span("News"),
        ], className="widget-title"),
        html.Div(items, className="news-list"),
    ], className="widget news-widget")


# ---------------------------------------------------------------------------
# Stocks widget
# ---------------------------------------------------------------------------

def stocks_widget(data: dict) -> html.Div:
    """Three stocks with intraday sparklines on a dark background."""
    if not data:
        body = html.Div("Stock data unavailable.", className="widget-error")
    else:
        rows = []
        for ticker, d in data.items():
            price   = d["price"]
            change  = d["change"]
            name    = d.get("name", ticker)
            history = d.get("history", [])
            up      = change >= 0
            clr     = "#e74c3c" if not up else "#2ecc71"
            arrow   = "▼" if not up else "▲"

            # Sparkline — y-axis centred on previous close so up/down is symmetric
            if len(history) >= 2:
                baseline = d.get("prev_close", history[0])
                lo = min(history)
                hi = max(history)
                half = max(abs(hi - baseline), abs(lo - baseline)) * 1.2 or baseline * 0.002
                spark_fig = go.Figure()
                # Filled area between line and opening-price baseline
                spark_fig.add_trace(go.Scatter(
                    y=history, mode="lines",
                    line=dict(color=clr, width=1.5),
                    fill="tonexty",
                    fillcolor=f"rgba({231 if not up else 46},{76 if not up else 204},{60 if not up else 113},0.25)",
                    showlegend=False,
                ))
                # Invisible baseline trace for fill reference
                spark_fig.add_trace(go.Scatter(
                    y=[baseline] * len(history), mode="lines",
                    line=dict(color="rgba(0,0,0,0.2)", width=1, dash="dot"),
                    showlegend=False,
                ))
                spark_fig.update_layout(
                    margin=dict(l=0, r=0, t=2, b=2),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=44, width=110,
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False, range=[baseline - half, baseline + half]),
                    showlegend=False,
                )
                spark = dcc.Graph(
                    figure=spark_fig,
                    config={"displayModeBar": False},
                    style={"width": "110px", "height": "44px", "flexShrink": "0"},
                )
            else:
                spark = html.Div()

            rows.append(
                html.Div([
                    html.Div([
                        html.Div([
                            html.Span(arrow, className="stock-arrow", style={"color": clr}),
                            html.Span(ticker, className="stock-ticker"),
                        ], className="stock-ticker-row"),
                        html.Div(name[:24], className="stock-name"),
                    ], className="stock-labels"),
                    spark,
                    html.Div([
                        html.Div(f"{price:,.2f}", className="stock-price"),
                        html.Div(
                            f"{arrow} {abs(change):.2f} %",
                            className="stock-change",
                            style={"color": clr},
                        ),
                    ], className="stock-values"),
                ], className="stock-row")
            )
        body = html.Div(rows, className="stocks-list")

    return html.Div([
        html.Div([
            html.Span("📈", className="widget-icon"),
            html.Span("Stocks"),
        ], className="widget-title"),
        body,
    ], className="widget stocks-widget")


# ---------------------------------------------------------------------------
# Calendar — day view
# ---------------------------------------------------------------------------

# Hard-coded schedule events: (label, start_h, start_m, end_h, end_m, bg_rgba, border_color)
_CALENDAR_EVENTS = [
    ("Work",             8,  0, 16,  0, "rgba(26,115,232,0.12)", "#1a73e8"),
    ("Rasmus Football", 17,  0, 18,  0, "rgba(231,76,60,0.12)",  "#e74c3c"),
    ("Gym",             20,  0, 21, 30, "rgba(39,174,96,0.12)",  "#27ae60"),
]

_CAL_SLOT_H   = 15   # px per hour in the timeline
_CAL_TL_START = 8    # first hour shown
_CAL_TL_END   = 22   # last hour shown (exclusive)


def calendar_widget() -> html.Div:
    """
    Shows today's date and a day-view timeline from 08:00–22:00 with
    hard-coded schedule events rendered as coloured blocks.
    Replace _CALENDAR_EVENTS with a CalDAV / iCal source for live data.
    """
    now        = datetime.now(_TZ)
    today_name = _DAYS_LONG[now.weekday()]

    total_h = _CAL_TL_END - _CAL_TL_START          # number of visible hours
    total_px = total_h * _CAL_SLOT_H                # total pixel height

    # ---- Hour-line grid ----
    slots = []
    for h in range(_CAL_TL_START, _CAL_TL_END):
        slots.append(
            html.Div([
                html.Span(f"{h:02d}", className="cal-time"),
                html.Div(className="cal-line"),
            ], className="cal-slot")
        )

    # ---- Event blocks ----
    event_blocks = []
    for label, sh, sm, eh, em, bg, border in _CALENDAR_EVENTS:
        top    = (sh - _CAL_TL_START + sm / 60) * _CAL_SLOT_H
        height = max(14, ((eh - sh) * 60 + (em - sm)) / 60 * _CAL_SLOT_H)
        event_blocks.append(
            html.Div(
                label,
                style={
                    "position":        "absolute",
                    "top":             f"{top}px",
                    "left":            "30px",
                    "right":           "0",
                    "height":          f"{height}px",
                    "backgroundColor": bg,
                    "borderLeft":      f"3px solid {border}",
                    "borderRadius":    "4px",
                    "padding":         "1px 5px",
                    "fontSize":        "0.7rem",
                    "fontWeight":      "600",
                    "color":           border,
                    "overflow":        "hidden",
                    "zIndex":          "5",
                    "boxSizing":       "border-box",
                    "lineHeight":      "1.3",
                }
            )
        )

    # ---- Current-time red line ----
    elapsed = max(0, min(total_h, now.hour + now.minute / 60 - _CAL_TL_START))
    top_now = elapsed * _CAL_SLOT_H
    time_indicator = html.Div(style={
        "position":        "absolute",
        "top":             f"{top_now}px",
        "left":            "0",
        "right":           "0",
        "height":          "2px",
        "backgroundColor": "#e74c3c",
        "zIndex":          "10",
    })

    return html.Div([
        html.Div([
            html.Div(today_name, className="cal-day-name"),
            html.Div(str(now.day), className="cal-day-number"),
        ], className="cal-header"),

        html.Div(
            [html.Div(slots, className="cal-timeline")] + event_blocks + [time_indicator],
            style={"position": "relative", "height": f"{total_px}px", "overflow": "hidden"},
        ),
    ], className="widget calendar-widget")


# ---------------------------------------------------------------------------
# Mini month calendar
# ---------------------------------------------------------------------------

def mini_calendar_widget() -> html.Div:
    """Renders a compact grid of the current month."""
    now        = datetime.now(_TZ)
    month_str  = _MONTHS_DK[now.month - 1]
    weeks      = _cal.monthcalendar(now.year, now.month)

    day_headers = html.Div(
        [html.Span(d, className="mc-dh") for d in ["M", "T", "W", "T", "F", "S", "S"]],
        className="mc-row",
    )

    week_rows = []
    for week in weeks:
        cells = []
        for d in week:
            if d == 0:
                cells.append(html.Span("", className="mc-day mc-empty"))
            elif d == now.day:
                cells.append(html.Span(str(d), className="mc-day mc-today"))
            else:
                cells.append(html.Span(str(d), className="mc-day"))
        week_rows.append(html.Div(cells, className="mc-row"))

    return html.Div([
        html.Div(month_str, className="mc-month"),
        day_headers,
        html.Div(week_rows),
    ], className="widget mini-cal-widget")


# ---------------------------------------------------------------------------
# Pollen / Air quality widget (placeholder — requires Google Maps API key)
# ---------------------------------------------------------------------------

_POLLEN_COLORS = {
    "Very Low":  "#27ae60",
    "Low":       "#2ecc71",
    "Moderate":  "#f39c12",
    "High":      "#e67e22",
    "Very High": "#e74c3c",
}


def pollen_widget(pollen: list, air_quality: dict | None) -> html.Div:
    """Pollen forecast and air quality from Google APIs."""
    title_row = html.Div([
        html.Span("🌿", className="widget-icon"),
        html.Span("Pollen & Air Quality"),
    ], className="widget-title")

    if not pollen and air_quality is None:
        return html.Div([
            title_row,
            html.Div("Data unavailable.", className="widget-error"),
        ], className="widget pollen-widget")

    # Pollen rows (value 0–5 → bar %)
    rows = []
    for p in pollen:
        clr = _POLLEN_COLORS.get(p["category"], "#aaa")
        pct = int(p["value"] / 5 * 100)
        rows.append(
            html.Div([
                html.Span(p["name"], className="pollen-label"),
                html.Div(
                    html.Div(style={
                        "width": f"{pct}%", "height": "100%",
                        "backgroundColor": clr, "borderRadius": "3px",
                    }),
                    className="pollen-bar",
                ),
                html.Span(p["category"], className="pollen-level", style={"color": clr}),
            ], className="pollen-row")
        )

    # AQI row
    if air_quality:
        aqi  = air_quality["aqi"]
        cat  = air_quality["category"].replace(" air quality", "")
        poll = air_quality["dominant_pollutant"]
        dot_pct = min(100, aqi / 500 * 100)
        aqi_row = html.Div([
            html.Hr(style={"margin": "8px 0 6px", "borderColor": "#eee"}),
            html.Div([
                html.Span("Air Quality Index", style={"fontSize": "0.78rem", "color": "#666"}),
                html.Span(f" · {poll}", style={"fontSize": "0.72rem", "color": "#bbb"}),
                html.Span(f"  {cat}", style={"fontSize": "0.78rem", "fontWeight": "600", "color": "#555", "float": "right"}),
            ], style={"marginBottom": "5px"}),
            # Gradient bar with dot indicator
            html.Div([
                html.Div(style={
                    "position": "absolute",
                    "left":     f"calc({dot_pct}% - 7px)",
                    "top":      "-3px",
                    "width":    "14px",
                    "height":   "14px",
                    "borderRadius": "50%",
                    "backgroundColor": "#fff",
                    "boxShadow": "0 1px 4px rgba(0,0,0,0.35)",
                    "zIndex": "2",
                }),
            ], style={
                "position":   "relative",
                "height":     "8px",
                "borderRadius": "4px",
                "background": "linear-gradient(to right, #4e8ef7, #00cfff, #00e676, #ffee58, #ffa726, #ef5350, #b71c1c, #7b1fa2)",
            }),
            html.Div(str(aqi), style={
                "marginTop": "6px",
                "fontSize":  "0.75rem",
                "color":     "#888",
                "marginLeft": f"calc({dot_pct}% - 6px)",
            }),
        ])
    else:
        aqi_row = html.Div()

    return html.Div([
        title_row,
        html.Div(rows),
        aqi_row,
    ], className="widget pollen-widget")


# ---------------------------------------------------------------------------
# To-do widget (hard-coded demo items — connect to Reminders / Tasks API)
# ---------------------------------------------------------------------------

def todo_widget() -> html.Div:
    """Displays a short to-do list. Items are hard-coded for the demo."""
    todos = [
        "Buy groceries",
        "Call Alice about weekend plans",
        "Book dentist appointment",
        "Pay electricity bill",
    ]

    items = [
        html.Div([
            html.Span("○", className="todo-circle"),
            html.Span(t, className="todo-text"),
        ], className="todo-item")
        for t in todos
    ]

    return html.Div([
        html.Div([
            html.Div("≡", className="todo-icon"),
            html.Div(items, className="todo-list"),
        ], className="todo-body"),
        html.Div([
            html.Span(str(len(todos)), className="todo-count-num"),
            html.Div("To Do", className="todo-count-label"),
        ], className="todo-count"),
    ], className="widget todo-widget")


# ---------------------------------------------------------------------------
# Trash collection widget (hard-coded Aarhus C schedule)
# ---------------------------------------------------------------------------

def trash_widget() -> html.Div:
    """
    Shows next collection dates.
    Schedule is hard-coded for Aarhus C inner city (Kredsløb).
    Replace with data from https://www.kredslob.dk when a public API is available.
    """
    now  = datetime.now(_TZ)
    wday = now.weekday()   # 0=Mon … 6=Sun
    iso_week = now.isocalendar()[1]

    gw_wday = TRASH_CONFIG["general_waste_weekday"]
    rc_wday = TRASH_CONFIG["recycling_weekday"]
    rc_parity = TRASH_CONFIG["recycling_week_parity"]

    # Days until next general waste pickup
    days_gw = (gw_wday - wday) % 7
    if days_gw == 0:
        days_gw = 7
    next_gw = now + timedelta(days=days_gw)

    # Days until next recycling pickup (bi-weekly)
    days_rc = (rc_wday - wday) % 7
    if days_rc == 0:
        days_rc = 14
    candidate = now + timedelta(days=days_rc)
    # Adjust if this candidate week has wrong parity
    if candidate.isocalendar()[1] % 2 != rc_parity:
        days_rc += 7
        candidate = now + timedelta(days=days_rc)
    next_rc = candidate

    def day_label(dt: datetime) -> str:
        delta = (dt.date() - now.date()).days
        if delta == 1:
            return "tomorrow"
        if delta <= 6:
            return f"on {_DAYS_SHORT[dt.weekday()].rstrip('.')}"
        return dt.strftime("%d/%m")

    return html.Div([
        html.Div([
            html.Span("🗑️", className="widget-icon"),
            html.Span("Trash Collection"),
        ], className="widget-title"),
        html.Div([
            _trash_row("🟤", "General Waste", next_gw, day_label(next_gw)),
            _trash_row("♻️", "Recycling",     next_rc, day_label(next_rc)),
        ], className="trash-list"),
    ], className="widget trash-widget")


def _trash_row(icon: str, label: str, dt: datetime, when_label: str) -> html.Div:
    return html.Div([
        html.Span(icon, style={"fontSize": "1.3rem", "marginRight": "10px"}),
        html.Div([
            html.Div(label, className="trash-label"),
            html.Div(
                f"{when_label.capitalize()} ({dt.strftime('%d/%m')})",
                className="trash-when",
            ),
        ]),
    ], className="trash-row")
