from nicegui import ui

from api_client import api
from components import render_header


def render_movements():
    render_header(active="Stock Movements")

    with ui.column().classes("w-full p-6 gap-6"):
        ui.label("Stock Movements").classes("text-2xl font-bold")

        items = api.get("/items")
        warehouses = api.get("/warehouses")
        item_options = {i["id"]: f"{i['sku']} - {i['name']}" for i in items}
        wh_options = {w["id"]: f"{w['code']} - {w['name']}" for w in warehouses}

        with ui.card().classes("w-full p-4"):
            ui.label("Record a Movement").classes("text-lg font-semibold")
            with ui.row().classes("gap-4 items-end flex-wrap"):
                item_select = ui.select(item_options, label="Item").classes("w-64")
                movement_type = ui.select(
                    {"inbound": "Inbound", "outbound": "Outbound", "transfer": "Transfer", "adjustment": "Adjustment"},
                    label="Type", value="inbound",
                ).classes("w-40")
                warehouse_select = ui.select(wh_options, label="Warehouse").classes("w-64")
                dest_select = ui.select(wh_options, label="Destination (transfer only)").classes("w-64")
                quantity_input = ui.number("Quantity", value=1, format="%.0f").classes("w-32")
                reference_input = ui.input("Reference").classes("w-48")

            dest_select.bind_visibility_from(movement_type, "value", value="transfer")

            error_label = ui.label("").classes("text-red-600 text-sm")

            def submit():
                errors = []
                if not item_select.value:
                    errors.append("Item is required")
                if not warehouse_select.value:
                    errors.append("Warehouse is required")
                if not quantity_input.value or quantity_input.value <= 0:
                    errors.append("Quantity must be greater than 0")
                if movement_type.value == "transfer" and not dest_select.value:
                    errors.append("Destination warehouse required for transfer")
                if movement_type.value == "transfer" and dest_select.value == warehouse_select.value:
                    errors.append("Source and destination must differ")
                if errors:
                    error_label.text = " | ".join(errors)
                    return
                error_label.text = ""

                payload = {
                    "item_id": item_select.value,
                    "warehouse_id": warehouse_select.value,
                    "movement_type": movement_type.value,
                    "quantity": int(quantity_input.value),
                    "reference": reference_input.value or None,
                }
                if movement_type.value == "transfer":
                    payload["destination_warehouse_id"] = dest_select.value
                try:
                    api.post("/stock-movements", payload)
                    ui.notify("Movement recorded", type="positive")
                    quantity_input.value = 1
                    reference_input.value = ""
                    refresh_history()
                except Exception as e:
                    ui.notify(f"Failed: {e}", type="negative")

            ui.button("Submit", icon="send", on_click=submit).classes("mt-2")

        with ui.row().classes("items-center justify-between w-full"):
            ui.label("Recent Movements").classes("text-lg font-semibold mt-4")
            auto_switch = ui.switch("Auto-refresh (10s)", value=True)
        columns = [
            {"name": "created_at", "label": "When", "field": "created_at"},
            {"name": "item_id", "label": "Item ID", "field": "item_id"},
            {"name": "movement_type", "label": "Type", "field": "movement_type"},
            {"name": "warehouse_id", "label": "Warehouse ID", "field": "warehouse_id"},
            {"name": "destination_warehouse_id", "label": "Dest. Warehouse ID", "field": "destination_warehouse_id"},
            {"name": "quantity", "label": "Qty", "field": "quantity"},
            {"name": "reference", "label": "Reference", "field": "reference"},
        ]
        history_table = ui.table(columns=columns, rows=[], row_key="id").classes("w-full")

        def refresh_history():
            try:
                history_table.rows = api.get("/stock-movements", params={"limit": 50})
                history_table.update()
            except Exception as e:
                ui.notify(f"Failed to load history: {e}", type="negative")

        refresh_history()

        def tick():
            if auto_switch.value:
                refresh_history()

        ui.timer(10.0, tick)
