import json
from nicegui import ui

from api_client import api
from components import render_header
from auth_guard import require_login


def render_analytics():
    if not require_login():
        return

    render_header(active="Analytics")

    with ui.column().classes("w-full p-4 md:p-6 gap-6 page-container"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("bar_chart").classes("text-2xl").style("color:#E8A33D;")
            ui.label("Analytics").classes("text-2xl font-bold page-title")

        # ---- Scorecard ----
        ui.label("Inventory Scorecard").classes("font-semibold text-lg mt-2")
        scorecard_row = ui.row().classes("w-full gap-4 flex-wrap stats-row")

        try:
            cards = api.get("/analytics/scorecard")
            with scorecard_row:
                for card in cards:
                    trend = card.get("trend", "")
                    trend_color = "#2F6F6B" if "+" in str(trend) else ("#C0463C" if "-" in str(trend) else "#9A9C9F")
                    trend_icon = "trending_up" if "+" in str(trend) else ("trending_down" if "-" in str(trend) else "trending_flat")

                    with ui.card().classes("p-4 w-48").style(f"border-top: 3px solid {card['color']};"):
                        with ui.row().classes("items-center gap-2 mb-1"):
                            ui.icon(card["icon"]).classes("text-lg").style(f"color:{card['color']};")
                            ui.label(card["label"]).classes("text-xs").style("color:var(--ink-soft)")
                        ui.label(str(card["value"])).classes("text-2xl font-bold mono")
                        if trend and trend != "flat":
                            with ui.row().classes("items-center gap-1 mt-1"):
                                ui.icon(trend_icon).classes("text-sm").style(f"color:{trend_color};")
                                ui.label(str(trend)).classes("text-xs mono").style(f"color:{trend_color};")
                        elif trend == "flat":
                            ui.label("same as last week").classes("text-xs").style("color:#9A9C9F;")
        except Exception as e:
            ui.label(f"Could not load scorecard: {e}").classes("text-red-600")

        # ---- Activity Heatmap ----
        ui.label("Stock Activity — Last 12 Weeks").classes("font-semibold text-lg mt-4")
        ui.label("Each cell = 1 day. Darker = more movement.").classes("text-xs mb-2").style("color:var(--ink-soft)")

        try:
            heatmap_data = api.get("/analytics/activity-heatmap")
            _render_heatmap(heatmap_data)
        except Exception as e:
            ui.label(f"Could not load heatmap: {e}").classes("text-red-600")

        # ---- Movement type breakdown chart ----
        ui.label("Movement Breakdown").classes("font-semibold text-lg mt-4")
        try:
            movements = api.get("/stock-movements", params={"limit": 500})
            type_counts = {}
            for m in movements:
                t = m["movement_type"]
                type_counts[t] = type_counts.get(t, 0) + 1

            if type_counts:
                ui.echart({
                    "tooltip": {"trigger": "item"},
                    "series": [{
                        "type": "pie",
                        "radius": ["40%", "70%"],
                        "data": [{"name": k, "value": v} for k, v in type_counts.items()],
                        "itemStyle": {"borderRadius": 6},
                        "label": {"show": True, "formatter": "{b}: {c}"},
                    }],
                    "color": ["#2F6F6B", "#E8A33D", "#2563eb", "#C0463C"],
                }).classes("w-full h-64")
        except Exception:
            pass


def _render_heatmap(data: list):
    """Renders a GitHub-style contribution heatmap using HTML/SVG."""
    from datetime import datetime, timedelta

    date_counts = {d["date"]: d["count"] for d in data}
    max_count = max(date_counts.values(), default=1) or 1

    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=12)

    days = []
    current = start_date
    while current <= end_date:
        days.append(current)
        current += timedelta(days=1)

    cell_size = 14
    gap = 2
    weeks = 12
    day_labels = ["", "Mon", "", "Wed", "", "Fri", ""]

    svg_width = weeks * (cell_size + gap) + 40
    svg_height = 7 * (cell_size + gap) + 30

    cells = []
    for day in days:
        date_str = day.strftime("%Y-%m-%d")
        count = date_counts.get(date_str, 0)
        intensity = count / max_count if count > 0 else 0
        if intensity == 0:
            color = "#1C2230"
        elif intensity < 0.3:
            color = "#1a3a2a"
        elif intensity < 0.6:
            color = "#2F6F6B"
        else:
            color = "#E8A33D"

        week_num = (day - start_date).days // 7
        day_of_week = day.weekday()
        x = week_num * (cell_size + gap) + 32
        y = day_of_week * (cell_size + gap) + 16

        cells.append(
            f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
            f'rx="2" fill="{color}" opacity="0.9">'
            f'<title>{date_str}: {count} movements</title></rect>'
        )

    day_label_svgs = "".join(
        f'<text x="0" y="{i * (cell_size + gap) + 16 + 10}" font-size="9" fill="#5B6275" '
        f'font-family="JetBrains Mono, monospace">{label}</text>'
        for i, label in enumerate(day_labels)
    )

    svg = f'''
    <div style="overflow-x:auto; width:100%;">
    <svg width="{svg_width}" height="{svg_height}" style="display:block;">
        {day_label_svgs}
        {"".join(cells)}
        <text x="32" y="{svg_height - 2}" font-size="9" fill="#5B6275"
            font-family="JetBrains Mono, monospace">12 weeks ago</text>
        <text x="{svg_width - 60}" y="{svg_height - 2}" font-size="9" fill="#5B6275"
            font-family="JetBrains Mono, monospace">today</text>
    </svg>
    <div style="display:flex; align-items:center; gap:4px; margin-top:6px; font-size:11px; color:#5B6275; font-family:'JetBrains Mono',monospace;">
        Less
        <span style="display:inline-block;width:12px;height:12px;background:#1C2230;border-radius:2px;"></span>
        <span style="display:inline-block;width:12px;height:12px;background:#1a3a2a;border-radius:2px;"></span>
        <span style="display:inline-block;width:12px;height:12px;background:#2F6F6B;border-radius:2px;"></span>
        <span style="display:inline-block;width:12px;height:12px;background:#E8A33D;border-radius:2px;"></span>
        More
    </div>
    </div>
    '''
    ui.html(svg)