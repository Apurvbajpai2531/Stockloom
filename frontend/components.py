from nicegui import ui


def render_header(active: str = ""):
    drawer = ui.left_drawer(value=True).classes("p-0").style(
        "background:#1C2230; width:230px; border-right:3px solid #E8A33D;"
    )
    with drawer:
        with ui.column().classes("w-full p-4 gap-1"):
            with ui.row().classes("items-center gap-2 mb-6"):
                ui.icon("warehouse").style("color:#E8A33D").classes("text-3xl")
                ui.label("STOCKLOOM").classes("text-lg font-bold text-white tracking-wide")

            _nav_link("Dashboard", "/dashboard", "dashboard", active)
            _nav_link("Items", "/items", "inventory_2", active)
            _nav_link("Warehouses", "/warehouses", "store", active)
            _nav_link("Stock Movements", "/movements", "sync_alt", active)
            _nav_link("Categories", "/categories", "category", active)
            _nav_link("Purchase Orders", "/purchase-orders", "shopping_cart", active)
            _nav_link("Reports", "/reports", "description", active)

            ui.element("div").classes("flex-grow")

            with ui.row().classes("items-center gap-2 mt-6 px-2"):
                dark = ui.dark_mode()
                icon_btn = ui.button(icon="dark_mode", on_click=lambda: toggle_dark()).props("flat round color=white")
                ui.label("Theme").classes("text-white text-sm")

                def toggle_dark():
                    dark.toggle()
                    icon_btn.props(f"icon={'light_mode' if dark.value else 'dark_mode'}")

            from api_client import clear_token

            def logout():
                clear_token()
                ui.navigate.to("/")

            with ui.row().classes("items-center gap-2 px-2 mt-1"):
                ui.button("Logout", icon="logout", on_click=logout).props("flat color=white").classes("text-sm")

    with ui.header().classes("px-4 py-3 items-center").style("background:#1C2230; border-bottom:3px solid #E8A33D;"):
        ui.button(icon="menu", on_click=drawer.toggle).props("flat round color=white").classes("md:hidden")
        ui.label("StockLoom Operations").classes("text-white font-semibold ml-2")


def _nav_link(label: str, target: str, icon: str, active: str):
    is_active = active == label
    bg = "background: rgba(232,163,61,0.15); border-left: 3px solid #E8A33D;" if is_active else "border-left: 3px solid transparent;"
    with ui.link(target=target).classes("no-underline w-full"):
        with ui.row().classes("items-center gap-3 px-3 py-2 cursor-pointer text-white hover:bg-white/5 rounded-r-lg w-full").style(bg):
            ui.icon(icon).classes("text-lg")
            ui.label(label).classes("text-sm font-medium")