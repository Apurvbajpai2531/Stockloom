from nicegui import ui

from api_client import api
from components import render_header


def render_dashboard():
    render_header(active="Dashboard")

    with ui.column().classes("w-full p-6 gap-6"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Dashboard").classes("text-2xl font-bold")
            with ui.row().classes("items-center gap-2"):
                auto_switch = ui.switch("Auto-refresh (10s)", value=True)
                ui.button("Refresh now", icon="refresh", on_click=lambda: refresh()).props("outline")

        stats_row = ui.row().classes("w-full gap-4")

        with ui.row().classes("w-full gap-4"):
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
            try:
                data = api.get("/dashboard/summary")
            except Exception as e:
                with stats_row:
                    ui.label(f"Could not load dashboard: {e}").classes("text-red-600")
                return

            cards = [
                ("Total Items", data["total_items"], "inventory_2", "text-blue-600"),
                ("Warehouses", data["total_warehouses"], "warehouse", "text-blue-600"),
                ("Total Units in Stock", data["total_units"], "stacks", "text-blue-600"),
                ("Inventory Value", f"${data['total_inventory_value']:,.2f}", "payments", "text-green-600"),
                ("Low Stock Items", data["low_stock_count"], "warning",
                 "text-red-600" if data["low_stock_count"] else "text-green-600"),
            ]
            with stats_row:
                for title, value, icon, color in cards:
                    with ui.card().classes("w-56 p-4"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon(icon).classes(f"text-2xl {color}")
                            ui.label(title).classes("text-sm text-gray-500")
                        ui.label(str(value)).classes("text-2xl font-bold mt-2")

            try:
                wh_data = api.get("/dashboard/stock-by-warehouse")
                warehouse_chart.options["xAxis"]["data"] = [d["warehouse"] for d in wh_data]
                warehouse_chart.options["series"][0]["data"] = [d["quantity"] for d in wh_data]
                warehouse_chart.update()
            except Exception:
                pass

            try:
                top_data = api.get("/dashboard/top-items")
                items_chart.options["xAxis"]["data"] = [d["name"] for d in top_data]
                items_chart.options["series"][0]["data"] = [d["quantity"] for d in top_data]
                items_chart.update()
            except Exception:
                pass

        refresh()

        def tick():
            if auto_switch.value:
                refresh()

        ui.timer(10.0, tick)
