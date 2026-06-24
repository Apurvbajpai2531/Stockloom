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
            _nav_link("Audit Log", "/audit-log", "history", active)
            _nav_link("Reorder Suggestions", "/reorder-suggestions", "shopping_bag", active)
            _nav_link("Forecasting", "/forecasting", "insights", active)
            _nav_link("Rebalancing", "/rebalancing", "swap_horiz", active)

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

    with ui.header().classes("px-4 py-3 items-center justify-between").style(
        "background:#1C2230; border-bottom:3px solid #E8A33D;"
    ):
        with ui.row().classes("items-center"):
            ui.button(icon="menu", on_click=drawer.toggle).props("flat round color=white").classes("md:hidden")
            ui.label("StockLoom Operations").classes("text-white font-semibold ml-2")

        with ui.row().classes("items-center gap-2"):
            search_box = ui.input(placeholder="Search items by SKU or name...").props("dense dark standout").classes("w-64")

            async def do_search():
                if not search_box.value or not search_box.value.strip():
                    return
                from api_client import api
                try:
                    results = api.get("/items", params={"search": search_box.value.strip(), "limit": 5})
                    if results:
                        ui.navigate.to(f"/items/{results[0]['id']}")
                    else:
                        ui.notify("No matching item found", type="warning")
                except Exception:
                    ui.notify("Search failed", type="negative")

            search_box.on("keydown.enter", lambda e: do_search())
            ui.button(icon="search", on_click=do_search).props("flat round color=white")

            from api_client import api as _api
            bell_btn = ui.button(icon="notifications", on_click=lambda: open_notifications()).props("flat round color=white")

            def open_notifications():
                with ui.dialog() as dialog, ui.card().classes("w-96"):
                    ui.label("Notifications").classes("text-lg font-bold")
                    try:
                        notifs = _api.get("/notifications", params={"unread_only": True})
                    except Exception:
                        notifs = []
                    if not notifs:
                        ui.label("No new notifications").style("color:var(--ink-soft)")
                    for n in notifs:
                        color = "#C0463C" if n["severity"] == "critical" else "#E8A33D"
                        with ui.row().classes("items-start gap-2 w-full py-2").style("border-bottom:1px solid var(--line);"):
                            ui.icon("circle").style(f"color:{color}; font-size:10px; margin-top:4px;")
                            with ui.column().classes("flex-grow"):
                                ui.label(n["title"]).classes("font-semibold text-sm")
                                ui.label(n["message"]).classes("text-xs").style("color:var(--ink-soft)")
                    ui.button("Close", on_click=dialog.close).classes("mt-2")
                dialog.open()


def _nav_link(label: str, target: str, icon: str, active: str):
    is_active = active == label
    bg = "background: rgba(232,163,61,0.15); border-left: 3px solid #E8A33D;" if is_active else "border-left: 3px solid transparent;"
    with ui.link(target=target).classes("no-underline w-full"):
        with ui.row().classes("items-center gap-3 px-3 py-2 cursor-pointer text-white hover:bg-white/5 rounded-r-lg w-full").style(bg):
            ui.icon(icon).classes("text-lg")
            ui.label(label).classes("text-sm font-medium")