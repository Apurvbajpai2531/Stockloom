from nicegui import ui
from api_client import api
from components import render_header
from auth_guard import require_login


def render_items():
    if not require_login():
        return

    render_header(active="Items")

    with ui.column().classes("w-full p-4 md:p-6 gap-4 page-container"):

        ui.label("Items").classes("text-2xl font-bold")

        view_mode = {"mode": "table"}
        page_state = {"offset": 0, "limit": 25, "last_rows": []}

        with ui.row().classes("w-full items-center gap-4 form-row flex-wrap"):
            search_input = ui.input("Search by name or SKU").classes("w-64 md:w-64")
            view_toggle = ui.button(icon="grid_view", on_click=lambda: switch_view()).props("flat dense")

        with ui.row().classes("items-center gap-3 mt-2"):
            prev_btn = ui.button(icon="chevron_left", on_click=lambda: change_page(-1)).props("flat dense")
            page_label = ui.label("Page 1")
            next_btn = ui.button(icon="chevron_right", on_click=lambda: change_page(1)).props("flat dense")
            low_stock_switch = ui.switch("Low stock only")
            auto_switch = ui.switch("Auto-refresh (15s)", value=False)

            ui.button(
                "Add Item",
                icon="add",
                on_click=lambda: open_item_dialog()
            ).classes("ml-auto")

        columns = [
            {"name": "sku", "label": "SKU", "field": "sku", "sortable": True},
            {"name": "name", "label": "Name", "field": "name", "sortable": True},
            {"name": "unit", "label": "Unit", "field": "unit"},
            {"name": "unit_price", "label": "Unit Price", "field": "unit_price"},
            {"name": "total_quantity", "label": "Total Qty", "field": "total_quantity", "sortable": True},
            {"name": "reorder_threshold", "label": "Reorder At", "field": "reorder_threshold"},
            {"name": "status", "label": "Status", "field": "status"},
            {"name": "actions", "label": "Actions", "field": "actions"},
        ]

        table = ui.table(columns=columns, rows=[], row_key="id").classes("w-full")
        grid_container = ui.row().classes("w-full gap-4 flex-wrap").style("display:none;")

        table.add_slot(
            "body-cell-actions",
            '''
            <q-td :props="props">
                <q-btn dense flat icon="edit"
                       @click="() => $parent.$emit('edit-row', props.row)" />
                <q-btn dense flat icon="delete"
                       color="red"
                       @click="() => $parent.$emit('delete-row', props.row)" />
            </q-td>
            '''
        )

        table.add_slot(
            "body-cell-status",
            '''
            <q-td :props="props">
                <q-badge
                    :color="props.value === 'LOW' ? 'red' : 'teal'"
                    :label="props.value"
                />
            </q-td>
            '''
        )

        table.on("row-click", lambda e: ui.navigate.to(f"/items/{e.args[1]['id']}"))

        # ---------------- VIEW SWITCH ----------------
        def switch_view():
            if view_mode["mode"] == "table":
                view_mode["mode"] = "grid"
                table.style("display:none;")
                grid_container.style("display:flex;")
                view_toggle.props("icon=table_rows")
            else:
                view_mode["mode"] = "table"
                table.style("display:table;")
                grid_container.style("display:none;")
                view_toggle.props("icon=grid_view")
            render_grid()

        def render_grid():
            grid_container.clear()
            rows = page_state.get("last_rows", [])
            with grid_container:
                for r in rows:
                    status = "LOW" if r["total_quantity"] <= r["reorder_threshold"] else "OK"
                    with ui.card().classes("w-64 p-4 cursor-pointer").on(
                        "click", lambda e, item_id=r["id"]: ui.navigate.to(f"/items/{item_id}")
                    ):
                        with ui.row().classes("items-center justify-between"):
                            ui.label(r["sku"]).classes("font-mono text-sm").style("color:var(--ink-soft)")
                            ui.badge(status, color="red" if status == "LOW" else "teal")
                        ui.label(r["name"]).classes("font-semibold mt-1")
                        ui.label(f"Qty: {r['total_quantity']}").classes("mono text-sm mt-2")
                        ui.label(f"${float(r['unit_price']):.2f} / {r['unit']}").classes("text-sm").style(
                            "color:var(--ink-soft)"
                        )

        # ---------------- REFRESH ----------------
        def refresh():
            params = {
                "limit": page_state["limit"],
                "offset": page_state["offset"]
            }

            if search_input.value:
                params["search"] = search_input.value

            if low_stock_switch.value:
                params["low_stock_only"] = True

            try:
                res = api.get("/items", params=params)
                rows = res.get("data", res) if isinstance(res, dict) else res

                table.rows = rows
                table.update()
                page_state["last_rows"] = rows
                render_grid()

            except Exception as e:
                ui.notify(f"Failed to load items: {e}", type="negative")

        # ---------------- PAGINATION ----------------
        def change_page(direction: int):
            new_offset = page_state["offset"] + direction * page_state["limit"]
            if new_offset < 0:
                return
            page_state["offset"] = new_offset
            page_label.text = f"Page {new_offset // page_state['limit'] + 1}"
            refresh()

        # ---------------- DIALOG ----------------
        def open_item_dialog(item: dict | None = None):
            is_edit = item is not None

            with ui.dialog() as dialog, ui.card().classes("w-96"):

                ui.label("Edit Item" if is_edit else "New Item").classes("text-lg font-bold")

                sku = ui.input("SKU", value=item["sku"] if is_edit else "")
                name = ui.input("Name", value=item["name"] if is_edit else "")
                unit = ui.input("Unit", value=item["unit"] if is_edit else "pcs")

                price = ui.number("Unit Price", value=float(item["unit_price"]) if is_edit else 0)
                threshold = ui.number("Reorder Threshold", value=item["reorder_threshold"] if is_edit else 10)

                description = ui.textarea(
                    "Description",
                    value=(item.get("description", "") if is_edit else "")
                )

                error_label = ui.label("").classes("text-red-600 text-sm")

                def validate():
                    errors = []
                    if not sku.value.strip():
                        errors.append("SKU required")
                    if not name.value.strip():
                        errors.append("Name required")
                    if price.value < 0:
                        errors.append("Price must be >= 0")
                    if threshold.value < 0:
                        errors.append("Threshold must be >= 0")

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
                    ui.button("Save", on_click=save)

            dialog.open()

        # ---------------- EVENTS ----------------
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

                with ui.row().classes("justify-end"):
                    ui.button("Cancel", on_click=confirm_dialog.close)
                    ui.button("Delete", on_click=confirm_delete).props("color=red")

            confirm_dialog.open()

        table.on("edit-row", handle_edit)
        table.on("delete-row", handle_delete)

        search_input.on("update:model-value", lambda e: refresh())
        low_stock_switch.on("update:model-value", lambda e: refresh())

        refresh()

        ui.timer(15.0, lambda: refresh() if auto_switch.value else None)