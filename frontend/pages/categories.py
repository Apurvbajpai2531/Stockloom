from nicegui import ui

from api_client import api
from components import render_header

from auth_guard import require_login


def render_categories():
    if not require_login():
        return

    render_header(active="Categories")

    with ui.column().classes("w-full p-6 gap-6"):
        ui.label("Categories & Suppliers").classes("text-2xl font-bold")

        with ui.row().classes("w-full gap-6"):
            # ---------- Categories ----------
            with ui.card().classes("flex-1 p-4"):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label("Categories").classes("text-lg font-semibold")
                    ui.button("Add", icon="add", on_click=lambda: open_category_dialog())

                cat_columns = [
                    {"name": "name", "label": "Name", "field": "name"},
                    {"name": "description", "label": "Description", "field": "description"},
                    {"name": "actions", "label": "Actions", "field": "actions"},
                ]
                cat_table = ui.table(columns=cat_columns, rows=[], row_key="id").classes("w-full")
                cat_table.add_slot(
                    "body-cell-actions",
                    '''
                    <q-td :props="props">
                        <q-btn dense flat icon="delete" color="red" @click="() => $parent.$emit('delete-cat', props.row)" />
                    </q-td>
                    ''',
                )

                def refresh_categories():
                    try:
                        cat_table.rows = api.get("/categories")
                        cat_table.update()
                    except Exception as e:
                        ui.notify(f"Failed to load categories: {e}", type="negative")

                def open_category_dialog():
                    with ui.dialog() as dialog, ui.card().classes("w-96"):
                        ui.label("New Category").classes("text-lg font-bold")
                        name = ui.input("Name")
                        description = ui.textarea("Description")
                        error_label = ui.label("").classes("text-red-600 text-sm")

                        def save():
                            if not name.value or not name.value.strip():
                                error_label.text = "Name is required"
                                return
                            try:
                                api.post("/categories", {"name": name.value.strip(), "description": description.value})
                                ui.notify("Saved", type="positive")
                                dialog.close()
                                refresh_categories()
                            except Exception as e:
                                ui.notify(f"Save failed: {e}", type="negative")

                        with ui.row().classes("justify-end gap-2 mt-4"):
                            ui.button("Cancel", on_click=dialog.close)
                            ui.button("Save", on_click=save).props("color=primary")
                    dialog.open()

                def handle_delete_cat(e):
                    row = e.args
                    try:
                        api.delete(f"/categories/{row['id']}")
                        ui.notify("Deleted", type="positive")
                        refresh_categories()
                    except Exception as ex:
                        ui.notify(f"Delete failed: {ex}", type="negative")

                cat_table.on("delete-cat", handle_delete_cat)
                refresh_categories()

            # ---------- Suppliers ----------
            with ui.card().classes("flex-1 p-4"):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label("Suppliers").classes("text-lg font-semibold")
                    ui.button("Add", icon="add", on_click=lambda: open_supplier_dialog())

                sup_columns = [
                    {"name": "name", "label": "Name", "field": "name"},
                    {"name": "contact_email", "label": "Email", "field": "contact_email"},
                    {"name": "contact_phone", "label": "Phone", "field": "contact_phone"},
                    {"name": "actions", "label": "Actions", "field": "actions"},
                ]
                sup_table = ui.table(columns=sup_columns, rows=[], row_key="id").classes("w-full")
                sup_table.add_slot(
                    "body-cell-actions",
                    '''
                    <q-td :props="props">
                        <q-btn dense flat icon="delete" color="red" @click="() => $parent.$emit('delete-sup', props.row)" />
                    </q-td>
                    ''',
                )

                def refresh_suppliers():
                    try:
                        sup_table.rows = api.get("/suppliers")
                        sup_table.update()
                    except Exception as e:
                        ui.notify(f"Failed to load suppliers: {e}", type="negative")

                def open_supplier_dialog():
                    with ui.dialog() as dialog, ui.card().classes("w-96"):
                        ui.label("New Supplier").classes("text-lg font-bold")
                        name = ui.input("Name")
                        email = ui.input("Email")
                        phone = ui.input("Phone")
                        address = ui.textarea("Address")
                        error_label = ui.label("").classes("text-red-600 text-sm")

                        def save():
                            if not name.value or not name.value.strip():
                                error_label.text = "Name is required"
                                return
                            try:
                                api.post("/suppliers", {
                                    "name": name.value.strip(),
                                    "contact_email": email.value,
                                    "contact_phone": phone.value,
                                    "address": address.value,
                                })
                                ui.notify("Saved", type="positive")
                                dialog.close()
                                refresh_suppliers()
                            except Exception as e:
                                ui.notify(f"Save failed: {e}", type="negative")

                        with ui.row().classes("justify-end gap-2 mt-4"):
                            ui.button("Cancel", on_click=dialog.close)
                            ui.button("Save", on_click=save).props("color=primary")
                    dialog.open()

                def handle_delete_sup(e):
                    row = e.args
                    try:
                        api.delete(f"/suppliers/{row['id']}")
                        ui.notify("Deleted", type="positive")
                        refresh_suppliers()
                    except Exception as ex:
                        ui.notify(f"Delete failed: {ex}", type="negative")

                sup_table.on("delete-sup", handle_delete_sup)
                refresh_suppliers()#
