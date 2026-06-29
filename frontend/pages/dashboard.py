from nicegui import ui

from api_client import api
from components import render_header
from auth_guard import require_login


def render_dashboard():
    if not require_login():
        return

    render_header(active="Dashboard")

    with ui.column().classes("w-full p-4 md:p-6 gap-6 page-container"):

        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Dashboard").classes("text-2xl font-bold")

        with ui.row().classes("items-center gap-2"):
                auto_switch = ui.switch("Auto-refresh (10s)", value=True)
                ui.button("Refresh now", icon="refresh", on_click=lambda: refresh()).props("outline")
                import os
                API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")
                ui.button(
                    "Export Report", icon="picture_as_pdf",
                    on_click=lambda: ui.navigate.to(f"{API_BASE}/dashboard/export-pdf", new_tab=True)
                ).props("outline")

        pulse_container = ui.column().classes("w-full items-center mb-4")
        stats_row = ui.row().classes("w-full gap-4 stats-row")
        alerts_box = ui.column().classes("w-full")

        with ui.row().classes("w-full gap-4 chart-row"):
            with ui.card().classes("flex-1 p-4"):
                ui.label("Stock by Warehouse").classes("text-lg font-semibold mb-2")
                warehouse_chart = ui.echart({
                    "xAxis": {"type": "category", "data": []},
                    "yAxis": {"type": "value"},
                    "series": [{"type": "bar", "data": [], "itemStyle": {"color": "#2563eb"}}],
                    "tooltip": {"trigger": "axis"},
                }).classes("w-full h-64")

            with ui.card().classes("flex-1 p-4"):
                ui.label("Top Items by Quantity").classes("text-lg font-semibold mb-2")
                items_chart = ui.echart({
                    "xAxis": {"type": "category", "data": []},
                    "yAxis": {"type": "value"},
                    "series": [{"type": "bar", "data": [], "itemStyle": {"color": "#16a34a"}}],
                    "tooltip": {"trigger": "axis"},
                }).classes("w-full h-64")

        activity_card = ui.card().classes("w-full p-4")

        def render_pulse():
            pulse_container.clear()
            try:
                p = api.get("/network/pulse")
            except Exception:
                return

            score = p["health_score"]
            color = "#2F6F6B" if score >= 80 else ("#E8A33D" if score >= 50 else "#C0463C")
            circumference = 2 * 3.1416 * 85
            offset = circumference * (1 - score / 100)

            html = f'''
            <div style="width:100%; display:flex; justify-content:center; padding:20px 0;">
                <div style="position:relative; width:220px; height:220px;">
                    <svg width="220" height="220" viewBox="0 0 220 220">
                        <defs>
                            <radialGradient id="pulseglow" cx="50%" cy="50%" r="50%">
                                <stop offset="0%" stop-color="{color}" stop-opacity="0.35"/>
                                <stop offset="100%" stop-color="{color}" stop-opacity="0"/>
                            </radialGradient>
                        </defs>
                        <circle cx="110" cy="110" r="100" fill="url(#pulseglow)">
                            <animate attributeName="r" values="90;105;90" dur="2.5s" repeatCount="indefinite"/>
                        </circle>
                        <circle cx="110" cy="110" r="85" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="10"/>
                        <circle cx="110" cy="110" r="85" fill="none" stroke="{color}" stroke-width="10"
                            stroke-linecap="round"
                            stroke-dasharray="{circumference}"
                            stroke-dashoffset="{offset}"
                            transform="rotate(-90 110 110)">
                            <animate attributeName="stroke-dashoffset"
                                values="{circumference};{offset}"
                                dur="1.2s" fill="freeze"/>
                        </circle>
                        <text x="110" y="100" text-anchor="middle" font-size="36" font-weight="700"
                            font-family="Space Grotesk, sans-serif" fill="{color}">{score}</text>
                        <text x="110" y="125" text-anchor="middle" font-size="11"
                            font-family="JetBrains Mono, monospace" fill="#9A9C9F">HEALTH SCORE</text>
                    </svg>
                </div>
            </div>
            '''
            with pulse_container:
                ui.html(html)
                with ui.row().classes("gap-6 justify-center mt-1"):
                    ui.label(f"Warehouses: {p['total_warehouses']}").classes("text-sm mono")
                    ui.label(f"Units: {p['total_units']}").classes("text-sm mono")
                    low_style = "color:#C0463C;" if p["low_stock_count"] > 0 else ""
                    ui.label(f"Low Stock: {p['low_stock_count']}").classes("text-sm mono").style(low_style)
                    ui.label(f"Transfers: {p['recent_transfers']}").classes("text-sm mono")

        def refresh():
            stats_row.clear()
            alerts_box.clear()
            render_pulse()

            try:
                data = api.get("/dashboard/summary")
            except Exception as e:
                with stats_row:
                    ui.label(f"Could not load dashboard: {e}").classes("text-red-600")
                return

            data = data or {}

            cards = [
                ("Total Items", data.get("total_items", 0), "inventory_2", "text-blue-600"),
                ("Warehouses", data.get("total_warehouses", 0), "warehouse", "text-blue-600"),
                ("Total Units", data.get("total_units", 0), "stacks", "text-blue-600"),
                ("Inventory Value", f"${data.get('total_inventory_value', 0):,.2f}", "payments", "text-green-600"),
                (
                    "Low Stock Items",
                    data.get("low_stock_count", 0),
                    "warning",
                    "text-red-600" if data.get("low_stock_count", 0) else "text-green-600"
                ),
            ]

            with stats_row:
                for title, value, icon, color in cards:
                    with ui.card().classes("w-56 p-4"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon(icon).classes(f"text-2xl {color}")
                            ui.label(title).style("color:var(--ink-soft)")
                        ui.label(str(value)).classes("text-2xl font-bold mono mt-1")

            try:
                alert_data = api.get("/alerts/low-stock") or {}
                if alert_data.get("count", 0) > 0:
                    with alerts_box:
                        with ui.card().classes("w-full p-4").style("border-left:4px solid #C0463C;"):
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("warning").style("color:#C0463C;")
                                ui.label(
                                    f"{alert_data.get('count', 0)} item(s) low on stock"
                                ).classes("font-semibold")
                            for a in alert_data.get("alerts", [])[:5]:
                                with ui.row().classes("items-center gap-3 mt-1 text-sm"):
                                    ui.badge(
                                        a.get("severity", "").upper(),
                                        color="red" if a.get("severity") == "critical" else "orange"
                                    )
                                    ui.label(
                                        f"{a.get('sku')} — {a.get('name')}: "
                                        f"{a.get('current_quantity')} left (reorder at {a.get('reorder_threshold')})"
                                    )
            except Exception:
                pass

            try:
                wh_data = api.get("/dashboard/stock-by-warehouse") or []
                warehouse_chart.options["xAxis"]["data"] = [d.get("warehouse") for d in wh_data]
                warehouse_chart.options["series"][0]["data"] = [d.get("quantity") for d in wh_data]
                warehouse_chart.update()
            except Exception:
                pass

            try:
                top_data = api.get("/dashboard/top-items") or []
                items_chart.options["xAxis"]["data"] = [d.get("name") for d in top_data]
                items_chart.options["series"][0]["data"] = [d.get("quantity") for d in top_data]
                items_chart.update()
            except Exception:
                pass

            activity_card.clear()
            try:
                activity = api.get("/audit-logs/recent-summary", params={"limit": 8})
                with activity_card:
                    ui.label("Recent Activity").classes("font-semibold mb-2")
                    if not activity:
                        ui.label("No recent activity").style("color:var(--ink-soft)")
                    for a in activity:
                        with ui.row().classes("items-center gap-2 py-1 text-sm"):
                            ui.icon(a["icon"]).classes("text-base").style("color:var(--amber)")
                            ui.label(a["text"]).style("color:var(--ink-soft)")
            except Exception:
                pass

        refresh()

        def tick():
            if auto_switch.value:
                refresh()

        ui.timer(10.0, tick)