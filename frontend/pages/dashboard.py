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
            ui.label("Dashboard").classes("text-2xl font-bold page-title")

            with ui.row().classes("items-center gap-2"):
                auto_switch = ui.switch("Auto-refresh (10s)", value=True)
                ui.button("Refresh now", icon="refresh", on_click=lambda: refresh()).props("outline")

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

        def refresh():
            stats_row.clear()
            alerts_box.clear()

            try:
                data = api.get("/dashboard/summary") or {}
            except Exception as e:
                with stats_row:
                    ui.label(f"Could not load dashboard: {e}").classes("text-red-600")
                return

            cards = [
                ("Total Items", data.get("total_items", 0), "inventory_2", "text-blue-600"),
                ("Warehouses", data.get("total_warehouses", 0), "warehouse", "text-blue-600"),
                ("Total Units", data.get("total_units", 0), "stacks", "text-blue-600"),
                ("Inventory Value", f"${data.get('total_inventory_value', 0):,.2f}", "payments", "text-green-600"),
                (
                    "Low Stock Items",
                    data.get("low_stock_count", 0),
                    "warning",
                    "text-red-600" if data.get("low_stock_count", 0) else "text-green-600",
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
                                ui.label(f"{alert_data.get('count', 0)} item(s) low on stock").classes("font-semibold")
                            for a in alert_data.get("alerts", [])[:5]:
                                with ui.row().classes("items-center gap-3 mt-1 text-sm"):
                                    ui.badge(
                                        a.get("severity", "").upper(),
                                        color="red" if a.get("severity") == "critical" else "orange",
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

        refresh()

        def tick():
            if auto_switch.value:
                refresh()

        ui.timer(10.0, tick)