from nicegui import ui


def render_header(active: str = ""):
    with ui.header().classes("items-center justify-between bg-slate-800 dark:bg-slate-900 px-4"):
        with ui.row().classes("items-center gap-4 nav-links flex-wrap"):
            ui.label("StockLoom").classes("text-xl font-bold text-white")
            with ui.row().classes("gap-3 nav-links flex-wrap"):
                _nav_link("Dashboard", "/", active)
                _nav_link("Items", "/items", active)
                _nav_link("Warehouses", "/warehouses", active)
                _nav_link("Stock Movements", "/movements", active)
                _nav_link("Categories", "/categories", active)

        with ui.row().classes("items-center gap-2"):
            dark = ui.dark_mode()
            icon_btn = ui.button(icon="dark_mode", on_click=lambda: toggle_dark()).props("flat round color=white")

            def toggle_dark():
                dark.toggle()
                icon_btn.props(f"icon={'light_mode' if dark.value else 'dark_mode'}")


def _nav_link(label: str, target: str, active: str):
    classes = "text-white no-underline cursor-pointer hover:opacity-80"
    if active == label:
        classes += " font-bold underline"
    ui.link(label, target).classes(classes)