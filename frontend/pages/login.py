from nicegui import ui

from api_client import api, set_token


def render_login():
    with ui.column().classes("w-full h-screen items-center justify-center gap-6").style(
        "background:#1C2230;"
    ):
        with ui.card().classes("p-8 w-96").style("background:#fff; border-radius:14px;"):
            with ui.column().classes("items-center gap-1 mb-4"):
                ui.icon("warehouse").style("color:#E8A33D; font-size:40px;")
                ui.label("STOCKLOOM").classes("font-bold text-xl tracking-wide")

            username = ui.input("Username").classes("w-full")
            password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")
            error_label = ui.label("").classes("text-red-600 text-sm")

            def do_login():
                try:
                    result = api.post("/auth/login", {"username": username.value, "password": password.value})
                    set_token(result["access_token"])
                    ui.navigate.to("/dashboard")
                except Exception:
                    error_label.text = "Invalid username or password"

            ui.button("Login", on_click=do_login).classes("w-full mt-2").style(
                "background:#E8A33D; color:#1C2230; font-weight:600;"
            )
            password.on("keydown.enter", lambda e: do_login())