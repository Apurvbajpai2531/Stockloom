from nicegui import ui

from api_client import api
from components import render_header
from auth_guard import require_login


def render_rebalancing():
    if not require_login():
        return

    render_header(active="Rebalancing")

    with ui.column().classes("w-full p-4 md:p-6 gap-4 page-container"):
        ui.label("Warehouse Rebalancing").classes("text-2xl font-bold page-title")
        ui.label("Suggested transfers between warehouses to balance stock").classes("text-sm").style(
            "color:var(--ink-soft)"
        )

        container = ui.column().classes("w-full gap-3")

        def refresh():
            container.clear()
            try:
                data = api.get("/forecasting/rebalance-suggestions")
            except Exception as e:
                with container:
                    ui.label(f"Failed: {e}").classes("text-red-600")
                return

            if not data:
                with container:
                    ui.label("No rebalancing needed — stock is evenly distributed.").style(
                        "color:var(--teal); font-weight:600;"
                    )
                return

            with container:
                for s in data:
                    with ui.card().classes("p-4 w-full"):
                        with ui.row().classes("items-center justify-between"):
                            ui.label(f"{s['sku']} — {s['name']}").classes("font-semibold")
                            ui.badge(f"Transfer {s['suggested_transfer_qty']} units", color="orange")
                        with ui.row().classes("items-center gap-2 mt-2 text-sm"):
                            ui.label(f"{s['from_warehouse_name']} ({s['from_quantity']} units)")
                            ui.icon("arrow_forward")
                            ui.label(f"{s['to_warehouse_name']} ({s['to_quantity']} units)")

                        def execute(s=s):
                            try:
                                api.post("/stock-movements", {
                                    "item_id": s["item_id"],
                                    "warehouse_id": s["from_warehouse_id"],
                                    "destination_warehouse_id": s["to_warehouse_id"],
                                    "movement_type": "transfer",
                                    "quantity": s["suggested_transfer_qty"],
                                    "reference": "auto-rebalance",
                                })
                                ui.notify("Transfer executed", type="positive")
                                refresh()
                            except Exception as e:
                                ui.notify(f"Failed: {e}", type="negative")

                        ui.button("Execute Transfer", icon="check", on_click=execute).classes("mt-2").props("color=primary")

        ui.button("Refresh", icon="refresh", on_click=refresh).classes("self-end")
        refresh()