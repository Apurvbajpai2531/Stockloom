from nicegui import ui
import os

from components import render_header
from auth_guard import require_login
from api_client import api, get_token

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")


def render_reports():
    if not require_login():
        return

    render_header(active="Reports")

    with ui.column().classes("w-full p-4 md:p-6 gap-6 page-container"):
        ui.label("Reports").classes("text-2xl font-bold page-title")

        with ui.row().classes("gap-4 flex-wrap"):
            with ui.card().classes("p-4 w-64"):
                ui.icon("inventory_2").classes("text-3xl")
                ui.label("Items Report").classes("font-semibold mt-2")
                ui.label("All items with current stock totals").classes("text-sm").style("color:var(--ink-soft)")
                ui.button(
                    "Download CSV", icon="download",
                    on_click=lambda: ui.navigate.to(f"{API_BASE}/reports/items.csv", new_tab=True)
                ).classes("mt-3")

            with ui.card().classes("p-4 w-64"):
                ui.icon("sync_alt").classes("text-3xl")
                ui.label("Movements Report").classes("font-semibold mt-2")
                ui.label("Full stock movement history").classes("text-sm").style("color:var(--ink-soft)")
                ui.button(
                    "Download CSV", icon="download",
                    on_click=lambda: ui.navigate.to(f"{API_BASE}/reports/movements.csv", new_tab=True)
                ).classes("mt-3")

            with ui.card().classes("p-4 w-72"):
                ui.icon("upload_file").classes("text-3xl")
                ui.label("Bulk Import Items").classes("font-semibold mt-2")
                ui.label("CSV columns: sku,name,unit,unit_price,reorder_threshold,description").classes(
                    "text-xs"
                ).style("color:var(--ink-soft)")

                result_label = ui.label("")

                def handle_upload(e):
                    import requests
                    files = {"file": (e.name, e.content.read(), "text/csv")}
                    headers = {"Authorization": f"Bearer {get_token()}"} if get_token() else {}
                    try:
                        resp = requests.post(f"{API_BASE}/reports/import-items", files=files, headers=headers)
                        resp.raise_for_status()
                        data = resp.json()
                        result_label.text = f"Created: {data['created']}, Skipped: {data['skipped_existing']}, Errors: {len(data['errors'])}"
                        ui.notify("Import complete", type="positive")
                    except Exception as ex:
                        ui.notify(f"Import failed: {ex}", type="negative")

                ui.upload(on_upload=handle_upload, auto_upload=True).props("accept=.csv").classes("mt-3 w-full")
                result_label

        ui.label("Inventory Value by Category").classes("text-lg font-semibold mt-4")
        valuation_chart = ui.echart({
            "xAxis": {"type": "category", "data": []},
            "yAxis": {"type": "value"},
            "series": [{"type": "bar", "data": [], "itemStyle": {"color": "#E8A33D"}}],
            "tooltip": {"trigger": "axis"},
        }).classes("w-full h-72")

        try:
            val_data = api.get("/reports/valuation-by-category")
            valuation_chart.options["xAxis"]["data"] = [d["category"] for d in val_data]
            valuation_chart.options["series"][0]["data"] = [round(d["total_value"], 2) for d in val_data]
            valuation_chart.update()
        except Exception:
            pass

        ui.label("ABC Analysis (Top 15 by Value)").classes("text-lg font-semibold mt-4")
        abc_table = ui.table(
            columns=[
                {"name": "sku", "label": "SKU", "field": "sku"},
                {"name": "name", "label": "Name", "field": "name"},
                {"name": "value", "label": "Value", "field": "value"},
                {"name": "cumulative_pct", "label": "Cumulative %", "field": "cumulative_pct"},
                {"name": "class", "label": "Class", "field": "class"},
            ],
            rows=[], row_key="sku",
        ).classes("w-full")
        abc_table.add_slot(
            "body-cell-class",
            '''
            <q-td :props="props">
                <q-badge :color="props.value === 'A' ? 'orange' : (props.value === 'B' ? 'blue' : 'grey')" :label="props.value" />
            </q-td>
            ''',
        )
        try:
            abc_data = api.get("/reports/abc-analysis")
            for d in abc_data:
                d["value"] = round(d["value"], 2)
            abc_table.rows = abc_data[:15]
            abc_table.update()
        except Exception:
            pass