from nicegui import ui

from api_client import api
from components import render_header


def render_items():
    render_header(active="Items")

    with ui.column().classes("w-full p-6 gap-4"):
        ui.label("Items").classes("text-2xl font-bold")

        with ui.row().classes("w-full items-center gap-4"):
            search_input = ui.input("Search by name or SKU").classes("w-64")
            low_stock_switch = ui.switch("Low stock only")
            auto_switch = ui.switch("Auto-refresh (15s)", value=False)
            ui.button("Add Item", icon="add", on_click=lambda: open_item_dialog()).classes("ml-auto")

        columns = [
            {"name": "sku", "label": "SKU", "field": "sku", "sortable": True},
            {"name": "name", "label": "Name", "field": "name", "sortable": True},
            {"name": "unit", "label": "Unit", "field": "unit"},
            {"name": "unit_price", "label": "Unit Price", "field": "unit_price"},
            {"name": "total_quantity", "label": "Total Qty", "field": "total_quantity", "sortable": True},
            {"name": "reorder_threshold", "label": "Reorder At", "field": "reorder_threshold"},
            {"name": "actions", "label": "Actions", "field": "actions"},
        ]
        table = ui.table(columns=columns, rows=[], row_key="id").classes("w-full")
        table.add_slot(
            "body-cell-actions",
            '''
            <q-td :props="props">
                <q-btn dense flat icon="edit" @click="() => $parent.$emit('edit-row', props.row)" />
                <q-btn dense flat icon="delete" color="red" @click="() => $parent.$emit('delete-row', props.row)" />
            </q-td>
            ''',
        )

        def refresh():
            params = {}
            if search_input.value:
                params["search"] = search_input.value
            if low_stock_switch.value:
                params["low_stock_only"] = True
            try:
                rows = api.get("/items", params=params)
            except Exception as e:
                ui.notify(f"Failed to load items: {e}", type="negative")
                rows = []
            table.rows = rows
            table.update()

        def open_item_dialog(item: dict | None = None):
            is_edit = item is not None
            with ui.dialog() as dialog, ui.card().classes("w-96"):
                ui.label("Edit Item" if is_edit else "New Item").classes("text-lg font-bold")
                sku = ui.input("SKU", value=item["sku"] if is_edit else "")
                name = ui.input("Name", value=item["name"] if is_edit else "")
                unit = ui.input("Unit", value=item["unit"] if is_edit else "pcs")
                price = ui.number("Unit Price", value=float(item["unit_price"]) if is_edit else 0, format="%.2f")
                threshold = ui.number(
                    "Reorder Threshold", value=item["reorder_threshold"] if is_edit else 10, format="%.0f"
                )
                description = ui.textarea("Description", value=item.get("description") or "" if is_edit else "")

                sku.props("clearable")
                name.props("clearable")
                error_label = ui.label("").classes("text-red-600 text-sm")

                def validate() -> bool:
                    errors = []
                    if not sku.value or not sku.value.strip():
                        errors.append("SKU is required")
                    if not name.value or not name.value.strip():
                        errors.append("Name is required")
                    if price.value is None or price.value < 0:
                        errors.append("Unit price must be 0 or more")
                    if threshold.value is None or threshold.value < 0:
                        errors.append("Reorder threshold must be 0 or more")
                    error_label.text = " | ".join(errors)
                    return not errors

                def save():
                    if not validate():
                        return
                    payload = {
                        "sku": sku.value.strip(),
                        "name": name.value.strip(),
                        "unit": unit.value,
                        "unit_price": price.value,
                        "reorder_threshold": int(threshold.value),
                        "description": description.value,
                    }
                    try:
                        if is_edit:
                            api.put(f"/items/{item['id']}", payload)
                        else:
                            api.post("/items", payload)
                        ui.notify("Saved", type="positive")
                        dialog.close()
                        refresh()
                    except Exception as e:
                        ui.notify(f"Save failed: {e}", type="negative")

                with ui.row().classes("justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=dialog.close)
                    ui.button("Save", on_click=save).props("color=primary")
            dialog.open()

        def handle_edit(e):
            open_item_dialog(e.args)

        def handle_delete(e):
            row = e.args

            def confirm_delete():
                try:
                    api.delete(f"/items/{row['id']}")
                    ui.notify("Deleted", type="positive")
                    refresh()
                except Exception as ex:
                    ui.notify(f"Delete failed: {ex}", type="negative")
                confirm_dialog.close()

            with ui.dialog() as confirm_dialog, ui.card():
                ui.label(f"Delete item '{row['name']}'?")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=confirm_dialog.close)
                    ui.button("Delete", on_click=confirm_delete).props("color=red")
            confirm_dialog.open()

        table.on("edit-row", handle_edit)
        table.on("delete-row", handle_delete)
        search_input.on("update:model-value", lambda e: refresh())
        refresh()

        def tick():
            if auto_switch.value:
                refresh()

        ui.timer(15.0, tick)
