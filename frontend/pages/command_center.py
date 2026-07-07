from nicegui import ui
from datetime import datetime

from api_client import api
from components import render_header
from auth_guard import require_login


def render_command_center():
    if not require_login():
        return

    render_header(active="Command Center")

    with ui.column().classes("w-full p-4 md:p-6 gap-6 page-container"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("radar").classes("text-2xl").style("color:#E8A33D;")
            ui.label("Command Center").classes("text-2xl font-bold page-title")
        ui.label("Anomaly detection, demand forecast, and warehouse grid — all in one view").classes(
            "text-sm"
        ).style("color:var(--ink-soft)")

        with ui.row().classes("w-full gap-4 chart-row"):
            # ---- Left: Anomaly Detection ----
            with ui.card().classes("flex-1 p-4").style("min-width:300px;"):
                with ui.row().classes("items-center gap-2 mb-3"):
                    ui.icon("crisis_alert").style("color:#C0463C;")
                    ui.label("Anomaly Detection").classes("font-semibold")

                anomaly_container = ui.column().classes("w-full gap-2")
                try:
                    data = api.get("/anomaly/detect")
                    with anomaly_container:
                        if data["count"] == 0:
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("check_circle").style("color:#2F6F6B;")
                                ui.label("No anomalies detected").style("color:var(--ink-soft)")
                        else:
                            ui.label(f"{data['count']} anomalies found").classes("text-xs font-semibold").style(
                                "color:#C0463C;"
                            )
                            for a in data["anomalies"][:6]:
                                with ui.card().classes("p-3 w-full").style(
                                    f"border-left: 3px solid {a['color']};"
                                ):
                                    with ui.row().classes("items-center gap-2"):
                                        ui.icon(a["icon"]).classes("text-sm").style(f"color:{a['color']};")
                                        ui.label(f"{a['sku']} — {a['type']}").classes("text-sm font-semibold")
                                    ui.label(a["description"]).classes("text-xs").style("color:var(--ink-soft)")
                                    ui.button(
                                        "Inspect", icon="open_in_new",
                                        on_click=lambda iid=a["item_id"]: ui.navigate.to(f"/items/{iid}")
                                    ).props("flat dense").classes("text-xs mt-1")
                except Exception as e:
                    with anomaly_container:
                        ui.label(f"Error: {e}").classes("text-red-600 text-xs")

            # ---- Right: Demand Forecast Calendar ----
            with ui.card().classes("flex-1 p-4").style("min-width:300px;"):
                with ui.row().classes("items-center gap-2 mb-3"):
                    ui.icon("event_note").style("color:#2563eb;")
                    ui.label("30-Day Demand Forecast").classes("font-semibold")

                try:
                    cal_data = api.get("/anomaly/demand-forecast-calendar")
                    _render_forecast_calendar(cal_data)
                except Exception as e:
                    ui.label(f"Error: {e}").classes("text-red-600 text-xs")

        # ---- Bottom: Warehouse 3D Grid ----
        with ui.card().classes("w-full p-4"):
            with ui.row().classes("items-center gap-2 mb-3"):
                ui.icon("view_in_ar").style("color:#E8A33D;")
                ui.label("Warehouse Capacity Grid").classes("font-semibold")

            try:
                warehouses = api.get("/warehouses")
                stock_levels = api.get("/stock-levels")

                wh_totals = {}
                for sl in stock_levels:
                    wid = sl["warehouse_id"]
                    wh_totals[wid] = wh_totals.get(wid, 0) + sl["quantity"]

                max_units = max(wh_totals.values(), default=1) or 1

                _render_warehouse_grid(warehouses, wh_totals, max_units)
            except Exception as e:
                ui.label(f"Error: {e}").classes("text-red-600 text-xs")


def _render_forecast_calendar(cal_data: list):
    """Renders a mini calendar with color-coded risk cells."""
    months = {}
    for d in cal_data:
        month = d["date"][:7]
        if month not in months:
            months[month] = []
        months[month].append(d)

    for month, days in months.items():
        dt = datetime.strptime(month, "%Y-%m")
        ui.label(dt.strftime("%B %Y")).classes("text-xs font-semibold mb-1").style("color:var(--ink-soft)")

        with ui.row().classes("flex-wrap gap-1 mb-3"):
            for d in days:
                risk = d["risk_count"]
                if risk == 0:
                    bg = "#1C2230"
                    border = "#2A2D35"
                elif risk <= 2:
                    bg = "#1a3a2a"
                    border = "#2F6F6B"
                elif risk <= 5:
                    bg = "#3a2a1a"
                    border = "#E8A33D"
                else:
                    bg = "#3a1a1a"
                    border = "#C0463C"

                day_num = d["date"].split("-")[2]
                tooltip = f"Day {day_num}: {d['predicted_units']} units predicted, {risk} items at risk"
                if d["items_at_risk"]:
                    tooltip += f" ({', '.join(d['items_at_risk'])})"

                with ui.element("div").style(
                    f"width:28px; height:28px; background:{bg}; border:1px solid {border}; "
                    f"border-radius:4px; display:flex; align-items:center; justify-content:center; cursor:default;"
                ):
                    ui.tooltip(tooltip)
                    ui.label(day_num).classes("text-xs mono").style("color:white;")


def _render_warehouse_grid(warehouses: list, wh_totals: dict, max_units: int):
    """Renders a visual 3D-style shelf grid per warehouse."""

    with ui.row().classes("w-full gap-6 flex-wrap"):
        for wh in warehouses:
            total = wh_totals.get(wh["id"], 0)
            fill_pct = min(total / max_units, 1.0)
            rows = 5
            cols = 8
            total_cells = rows * cols
            filled_cells = round(fill_pct * total_cells)

            color = "#2F6F6B" if fill_pct > 0.6 else ("#E8A33D" if fill_pct > 0.3 else "#C0463C")

            with ui.column().classes("items-center gap-2"):
                ui.label(f"{wh['code']}").classes("font-bold text-sm mono").style(f"color:{color};")
                ui.label(wh["name"]).classes("text-xs").style("color:var(--ink-soft)")

                html = f'<div style="display:grid; grid-template-columns:repeat({cols}, 16px); gap:3px;">'
                for i in range(total_cells):
                    cell_color = color if i < filled_cells else "#1C2230"
                    border = color if i < filled_cells else "#2A2D35"
                    html += (
                        f'<div style="width:16px;height:16px;background:{cell_color};'
                        f'border:1px solid {border};border-radius:2px;opacity:0.85;'
                        f'box-shadow: {f"0 1px 3px {color}40" if i < filled_cells else "none"};">'
                        f'</div>'
                    )
                html += '</div>'
                html += f'<div style="font-size:10px;color:#9A9C9F;font-family:JetBrains Mono,monospace;margin-top:4px;">{total:,} units • {fill_pct*100:.0f}% capacity</div>'
                ui.html(html)

    with ui.row().classes("items-center gap-3 mt-4"):
        ui.label("Capacity:").classes("text-xs").style("color:var(--ink-soft)")
        for label, color in [("Low (<30%)", "#C0463C"), ("Medium (30-60%)", "#E8A33D"), ("High (>60%)", "#2F6F6B")]:
            with ui.row().classes("items-center gap-1"):
                ui.element("div").style(
                    f"width:12px;height:12px;background:{color};border-radius:2px;"
                )
                ui.label(label).classes("text-xs").style("color:var(--ink-soft)")