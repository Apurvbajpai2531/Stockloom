from nicegui import ui

from api_client import api
from components import render_header


def render_warehouses():
    render_header(active="Warehouses")

    with ui.column().classes("w-full p-6 gap-4"):
        ui.label("Warehouses").classes("text-2xl font-bold")
        ui.button("Add Warehouse", icon="add", on_click=lambda: open_dialog()).classes("self-end")

        columns = [
            {"name": "code", "label": "Code", "field": "code"},
            {"name": "name", "label": "Name", "field": "name"},
            {"name": "location", "label": "Location", "field": "location"},
            {"name": "actions", "label": "Actions", "field": "actions"},
        ]
        table = ui.table(columns=columns, rows=[], row_key="id").classes("w-full")
        table.add_slot(
            "body-cell-actions",
            '''
            <q-td :props="props">
                <q-btn dense flat icon="delete" color="red" @click="() => $parent.$emit('delete-row', props.row)" />
            </q-td>
            ''',
        )

        def refresh():
            try:
                rows = api.get("/warehouses")
            except Exception as e:
                ui.notify(f"Failed to load warehouses: {e}", type="negative")
                rows = []
            table.rows = rows
            table.update()

        def open_dialog():
            with ui.dialog() as dialog, ui.card().classes("w-96"):
                ui.label("New Warehouse").classes("text-lg font-bold")
                name = ui.input("Name")
                code = ui.input("Code")
                location = ui.input("Location")
                error_label = ui.label("").classes("text-red-600 text-sm")

                def save():
                    errors = []
                    if not name.value or not name.value.strip():
                        errors.append("Name is required")
                    if not code.value or not code.value.strip():
                        errors.append("Code is required")
                    if errors:
                        error_label.text = " | ".join(errors)
                        return
                    try:
                        api.post("/warehouses", {
                            "name": name.value.strip(), "code": code.value.strip(), "location": location.value
                        })
                        ui.notify("Saved", type="positive")
                        dialog.close()
                        refresh()
                    except Exception as e:
                        ui.notify(f"Save failed: {e}", type="negative")

                with ui.row().classes("justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=dialog.close)
                    ui.button("Save", on_click=save).props("color=primary")
            dialog.open()

        def handle_delete(e):
            row = e.args

            def confirm_delete():
                try:
                    api.delete(f"/warehouses/{row['id']}")
                    ui.notify("Deleted", type="positive")
                    refresh()
                except Exception as ex:
                    ui.notify(f"Delete failed: {ex}", type="negative")
                confirm_dialog.close()

            with ui.dialog() as confirm_dialog, ui.card():
                ui.label(f"Delete warehouse '{row['name']}'? This also removes its stock records.")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=confirm_dialog.close)
                    ui.button("Delete", on_click=confirm_delete).props("color=red")
            confirm_dialog.open()

        table.on("delete-row", handle_delete)
        refresh()
