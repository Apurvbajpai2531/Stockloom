from nicegui import ui

from api_client import api
from components import render_header
from auth_guard import require_login


def render_settings():
    if not require_login():
        return

    render_header(active="Settings")

    with ui.column().classes("w-full p-4 md:p-6 gap-6 page-container"):
        ui.label("Settings").classes("text-2xl font-bold page-title")

        with ui.row().classes("w-full gap-4 chart-row"):
            with ui.card().classes("p-4 flex-1"):
                ui.label("Keyboard Shortcuts").classes("font-semibold mb-2")
                shortcuts = [
                    ("Ctrl + K", "Open command palette"),
                    ("↑ / ↓", "Navigate command list"),
                    ("Enter", "Select command"),
                    ("Esc", "Close command palette"),
                ]
                for key, desc in shortcuts:
                    with ui.row().classes("justify-between w-full py-1").style("border-bottom:1px solid var(--line);"):
                        ui.label(desc).style("color:var(--ink-soft)")
                        ui.label(key).classes("mono font-semibold")

            with ui.card().classes("p-4 flex-1"):
                ui.label("User Management").classes("font-semibold mb-2")
                ui.label("Admins can add or remove team members").classes("text-xs mb-2").style(
                    "color:var(--ink-soft)"
                )

                user_container = ui.column().classes("w-full gap-1")

                def refresh_users():
                    user_container.clear()
                    try:
                        users = api.get("/users")
                    except Exception as e:
                        with user_container:
                            ui.label(f"Cannot load users (admin only): {e}").classes("text-xs text-red-600")
                        return
                    with user_container:
                        for u in users:
                            with ui.row().classes("items-center justify-between w-full py-1").style(
                                "border-bottom:1px solid var(--line);"
                            ):
                                with ui.row().classes("items-center gap-2"):
                                    ui.icon("person").classes("text-sm")
                                    ui.label(u["username"]).classes("text-sm")
                                    ui.badge(u["role"], color="orange" if u["role"] == "admin" else "grey")
                                if u["username"] != "admin":
                                    ui.button(
                                        icon="delete", on_click=lambda uid=u["id"]: delete_user(uid)
                                    ).props("dense flat color=red")

                def delete_user(user_id: int):
                    try:
                        api.delete(f"/users/{user_id}")
                        ui.notify("User removed", type="positive")
                        refresh_users()
                    except Exception as e:
                        ui.notify(f"Failed: {e}", type="negative")

                ui.button("+ Add User", icon="person_add", on_click=lambda: open_add_user_dialog()).classes("mt-2")

                def open_add_user_dialog():
                    with ui.dialog() as dialog, ui.card().classes("w-80"):
                        ui.label("Add Team Member").classes("font-bold")
                        username = ui.input("Username").classes("w-full")
                        password = ui.input("Password", password=True).classes("w-full")
                        role = ui.select({"staff": "Staff", "admin": "Admin"}, value="staff", label="Role").classes("w-full")
                        error_label = ui.label("").classes("text-red-600 text-xs")

                        def save():
                            if not username.value or not password.value:
                                error_label.text = "Username and password required"
                                return
                            try:
                                api.post("/users", {
                                    "username": username.value.strip(),
                                    "password": password.value,
                                    "role": role.value,
                                })
                                ui.notify("User created", type="positive")
                                dialog.close()
                                refresh_users()
                            except Exception as e:
                                ui.notify(f"Failed: {e}", type="negative")

                        with ui.row().classes("justify-end gap-2 mt-4"):
                            ui.button("Cancel", on_click=dialog.close)
                            ui.button("Create", on_click=save).props("color=primary")
                    dialog.open()

                refresh_users()