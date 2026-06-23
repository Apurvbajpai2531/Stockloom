from nicegui import ui

from api_client import api
from components import render_header


def render_purchase_orders():
    render_header(active="Purchase Orders")

    with ui.column().classes("w-full p-4 md:p-6 gap-4 page-container"):
        ui.label("Purchase Orders").classes("text-2xl font-bold page-title")

        items = api.get("/items")
        warehouses = api.get("/warehouses")
        suppliers = api.get("/suppliers")
        item_options = {i["id"]: f"{i['sku']} - {i['name']}" for i in items}
        wh_options = {w["id"]: f"{w['code']} - {w['name']}" for w in warehouses}
        sup_options = {s["id"]: s["name"] for s in suppliers}

        ui.button("New Purchase Order", icon="add", on_click=lambda: open_po_dialog()).classes("self-end")

        columns = [
            {"name": "po_number", "label": "PO #", "field": "po_number"},
            {"name": "status", "label": "Status", "field": "status"},
            {"name": "warehouse_id", "label": "Warehouse ID", "field": "warehouse_id"},
            {"name": "created_at", "label": "Created", "field": "created_at"},
            {"name": "actions", "label": "Actions", "field": "actions"},
        ]
        table = ui.table(columns=columns, rows=[], row_key="id").classes("w-full")
        table.add_slot(
            "body-cell-actions",
            '''
            <q-td :props="props">
                <q-btn v-if="props.row.status === 'draft'" dense flat label="Mark Ordered" @click="() => $parent.$emit('mark-ordered', props.row)" />
                <q-btn v-if="props.row.status !== 'received' && props.row.status !== 'cancelled'" dense flat color="green" label="Receive" @click="() => $parent.$emit('receive', props.row)" />
                <q-btn v-if="props.row.status !== 'received' && props.row.status !== 'cancelled'" dense flat color="red" label="Cancel" @click="() => $parent.$emit('cancel', props.row)" />
            </q-td>
            ''',
        )

        def refresh():
            try:
                table.rows = api.get("/purchase-orders")
                table.update()
            except Exception as e:
                ui.notify(f"Failed to load POs: {e}", type="negative")

        def open_po_dialog():
            with ui.dialog() as dialog, ui.card().classes("w-[480px]"):
                ui.label("New Purchase Order").classes("text-lg font-bold")
                po_number = ui.input("PO Number")
                supplier = ui.select(sup_options, label="Supplier")
                warehouse = ui.select(wh_options, label="Warehouse")
                notes = ui.textarea("Notes")

                ui.label("Line Items").classes("font-semibold mt-2")
                lines_container = ui.column().classes("w-full gap-2")
                lines = []

                def add_line():
                    with lines_container:
                        with ui.row().classes("gap-2 items-end w-full") as row:
                            item_sel = ui.select(item_options, label="Item").classes("flex-1")
                            qty = ui.number("Qty", value=1).classes("w-24")
                            cost = ui.number("Unit Cost", value=0, format="%.2f").classes("w-28")
                    lines.append((item_sel, qty, cost))

                add_line()
                ui.button("+ Add line", on_click=add_line).props("flat dense")
                error_label = ui.label("").classes("text-red-600 text-sm")

                def save():
                    if not po_number.value or not po_number.value.strip():
                        error_label.text = "PO number is required"
                        return
                    if not warehouse.value:
                        error_label.text = "Warehouse is required"
                        return
                    line_payload = []
                    for item_sel, qty, cost in lines:
                        if item_sel.value:
                            line_payload.append({
                                "item_id": item_sel.value,
                                "quantity_ordered": int(qty.value),
                                "unit_cost": cost.value,
                            })
                    if not line_payload:
                        error_label.text = "Add at least one valid line item"
                        return
                    try:
                        api.post("/purchase-orders", {
                            "po_number": po_number.value.strip(),
                            "supplier_id": supplier.value,
                            "warehouse_id": warehouse.value,
                            "notes": notes.value,
                            "lines": line_payload,
                        })
                        ui.notify("Purchase order created", type="positive")
                        dialog.close()
                        refresh()
                    except Exception as e:
                        ui.notify(f"Failed: {e}", type="negative")

                with ui.row().classes("justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=dialog.close)
                    ui.button("Create", on_click=save).props("color=primary")
            dialog.open()

        def handle_action(action: str, row: dict):
            try:
                api.post(f"/purchase-orders/{row['id']}/{action}", {})
                ui.notify(f"PO {action.replace('-', ' ')}", type="positive")
                refresh()
            except Exception as e:
                ui.notify(f"Failed: {e}", type="negative")

        table.on("mark-ordered", lambda e: handle_action("mark-ordered", e.args))
        table.on("receive", lambda e: handle_action("receive", e.args))
        table.on("cancel", lambda e: handle_action("cancel", e.args))

        refresh()