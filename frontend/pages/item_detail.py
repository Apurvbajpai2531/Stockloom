import os

from nicegui import ui

from api_client import api
from components import render_header
from auth_guard import require_login

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")


def render_item_detail(item_id: int):
    if not require_login():
        return

    render_header(active="Items")

    with ui.column().classes("w-full p-4 md:p-6 gap-6 page-container"):
        try:
            item = api.get(f"/items/{item_id}")
        except Exception as e:
            ui.label(f"Could not load item: {e}").classes("text-red-600")
            return

        with ui.row().classes("items-center gap-2 justify-between w-full"):
            with ui.row().classes("items-center gap-2"):
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/items")).props("flat dense")
                ui.label(f"{item['sku']} — {item['name']}").classes("text-2xl font-bold page-title")

            with ui.row().classes("gap-2"):
                ui.button(
                    "View QR Code", icon="qr_code_2",
                    on_click=lambda: ui.navigate.to(f"{API_BASE}/items/{item_id}/qrcode.png", new_tab=True)
                ).props("outline")
                ui.button("Quick Adjust", icon="tune", on_click=lambda: open_adjust_dialog()).props("outline")

        def open_adjust_dialog():
            with ui.dialog() as dialog, ui.card().classes("w-80"):
                ui.label("Quick Stock Adjustment").classes("font-bold")
                levels = api.get("/stock-levels", params={"item_id": item_id})
                if levels:
                    wh_options = {l["warehouse_id"]: f"Warehouse {l['warehouse_id']}" for l in levels}
                else:
                    all_warehouses = api.get("/warehouses")
                    wh_options = {w["id"]: f"{w['code']} - {w['name']}" for w in all_warehouses}

                wh_select = ui.select(wh_options, label="Warehouse").classes("w-full")
                new_qty = ui.number("New Quantity", value=0).classes("w-full")

                def save():
                    if not wh_select.value:
                        ui.notify("Select a warehouse", type="warning")
                        return
                    try:
                        api.post("/stock-movements", {
                            "item_id": item_id,
                            "warehouse_id": wh_select.value,
                            "movement_type": "adjustment",
                            "quantity": int(new_qty.value),
                            "reference": "quick-adjust",
                        })
                        ui.notify("Stock adjusted", type="positive")
                        dialog.close()
                        ui.navigate.to(f"/items/{item_id}")
                    except Exception as e:
                        ui.notify(f"Failed: {e}", type="negative")

                with ui.row().classes("justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=dialog.close)
                    ui.button("Save", on_click=save).props("color=primary")
            dialog.open()
        with ui.row().classes("w-full gap-4 chart-row"):
            with ui.card().classes("p-4 flex-1"):
                ui.label("Overview").classes("font-semibold mb-2")
                _info_row("Unit", item["unit"])
                _info_row("Unit Price", f"${float(item['unit_price']):.2f}")
                _info_row("Reorder Threshold", item["reorder_threshold"])
                _info_row("Total Quantity", item["total_quantity"])
                status = "LOW STOCK" if item["total_quantity"] <= item["reorder_threshold"] else "OK"
                ui.badge(status, color="red" if status == "LOW STOCK" else "teal").classes("mt-2")

                try:
                    forecast = api.get(f"/forecasting/stockout-risk/{item_id}")
                    if forecast.get("days_until_stockout") is not None:
                        ui.label(f"Est. stockout in {forecast['days_until_stockout']} days").classes(
                            "text-sm mt-2 font-medium"
                        ).style(
                            f"color: {'#C0463C' if forecast['risk']=='critical' else ('#E8A33D' if forecast['risk']=='warning' else '#2F6F6B')}"
                        )
                except Exception:
                    pass

                if item.get("description"):
                    ui.label("Description").classes("font-semibold mt-4")
                    ui.label(item["description"]).style("color:var(--ink-soft)")

            with ui.card().classes("p-4 flex-1"):
                ui.label("Stock by Warehouse").classes("font-semibold mb-2")
                levels_table = ui.table(
                    columns=[
                        {"name": "warehouse_id", "label": "Warehouse ID", "field": "warehouse_id"},
                        {"name": "quantity", "label": "Quantity", "field": "quantity"},
                    ],
                    rows=[], row_key="id",
                ).classes("w-full")
                try:
                    levels_table.rows = api.get("/stock-levels", params={"item_id": item_id})
                    levels_table.update()
                except Exception:
                    pass

        ui.label("Movement History").classes("text-lg font-semibold mt-2")
        history_table = ui.table(
            columns=[
                {"name": "created_at", "label": "When", "field": "created_at"},
                {"name": "movement_type", "label": "Type", "field": "movement_type"},
                {"name": "warehouse_id", "label": "Warehouse ID", "field": "warehouse_id"},
                {"name": "destination_warehouse_id", "label": "Dest. Warehouse ID", "field": "destination_warehouse_id"},
                {"name": "quantity", "label": "Qty", "field": "quantity"},
                {"name": "reference", "label": "Reference", "field": "reference"},
            ],
            rows=[], row_key="id",
        ).classes("w-full")
        try:
            history_table.rows = api.get("/stock-movements", params={"item_id": item_id, "limit": 100})
            history_table.update()
        except Exception:
            pass


def _info_row(label: str, value):
    with ui.row().classes("justify-between w-full text-sm py-1").style("border-bottom:1px solid var(--line);"):
        ui.label(label).style("color:var(--ink-soft)")
        ui.label(str(value)).classes("font-medium mono")