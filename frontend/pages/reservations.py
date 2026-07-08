from nicegui import ui

from api_client import api
from components import render_header
from auth_guard import require_login


def render_reservations():
    if not require_login():
        return

    render_header(active="Reservations")

    with ui.column().classes("w-full p-4 md:p-6 gap-6 page-container"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("bookmark").classes("text-2xl").style("color:#E8A33D;")
            ui.label("Stock Reservations").classes("text-2xl font-bold page-title")
        ui.label("Reserve stock for upcoming orders before they are fulfilled").classes(
            "text-sm"
        ).style("color:var(--ink-soft)")

        with ui.row().classes("w-full gap-6 chart-row"):
            # ---- Create Reservation ----
            with ui.card().classes("flex-1 p-4"):
                ui.label("New Reservation").classes("font-semibold mb-3")

                items_list = api.get("/items", params={"limit": 200})
                warehouses_list = api.get("/warehouses")
                item_options = {
                    i["id"]: f"{i['sku']} — {i['name']}" for i in items_list
                }
                wh_options = {w["id"]: w["name"] for w in warehouses_list}

                item_sel = ui.select(item_options, label="Item").classes("w-full")
                wh_sel = ui.select(wh_options, label="Warehouse").classes("w-full")
                qty_input = ui.number("Quantity to Reserve", value=1).classes("w-full")
                ref_input = ui.input("Reference (Order #, Customer, etc.)").classes(
                    "w-full"
                )
                reason_input = ui.textarea("Reason (optional)").classes("w-full")

                avail_label = ui.label("").classes("text-sm mono")

                def check_avail():
                    if item_sel.value and wh_sel.value:
                        try:
                            avail = api.get(
                                f"/reservations/availability/{item_sel.value}/{wh_sel.value}"
                            )
                            avail_label.text = (
                                f"Total: {avail['total_quantity']} | "
                                f"Reserved: {avail['reserved_quantity']} | "
                                f"Available: {avail['available_quantity']}"
                            )
                            avail_label.style(
                                "color:#2F6F6B;"
                                if avail["available_quantity"] > 0
                                else "color:#C0463C;"
                            )
                        except Exception:
                            pass

                item_sel.on("update:model-value", lambda e: check_avail())
                wh_sel.on("update:model-value", lambda e: check_avail())

                error_label = ui.label("").classes("text-red-600 text-sm")

                def create():
                    if not item_sel.value or not wh_sel.value or not ref_input.value:
                        error_label.text = "Item, warehouse and reference are required"
                        return
                    try:
                        result = api.post(
                            "/reservations",
                            {
                                "item_id": item_sel.value,
                                "warehouse_id": wh_sel.value,
                                "quantity": int(qty_input.value),
                                "reference": ref_input.value.strip(),
                                "reason": reason_input.value or None,
                            },
                        )
                        ui.notify(
                            f"Reserved — available after: {result['available_after']}",
                            type="positive",
                        )
                        error_label.text = ""
                        ref_input.value = ""
                        reason_input.value = ""
                        refresh_list()
                        check_avail()
                    except Exception as e:
                        ui.notify(f"Failed: {e}", type="negative")

                ui.button(
                    "Reserve Stock", icon="bookmark_add", on_click=create
                ).classes("w-full mt-2").style("background:var(--ink); color:white;")

            # ---- Active Reservations ----
            with ui.card().classes("flex-1 p-4"):
                ui.label("Active Reservations").classes("font-semibold mb-3")
                res_container = ui.column().classes("w-full gap-2")

                def refresh_list():
                    res_container.clear()
                    try:
                        rows = api.get("/reservations", params={"status": "active"})
                    except Exception as e:
                        with res_container:
                            ui.label(f"Error: {e}").classes("text-red-600")
                        return
                    if not rows:
                        with res_container:
                            ui.label("No active reservations").style(
                                "color:var(--ink-soft)"
                            )
                        return
                    with res_container:
                        for r in rows:
                            with ui.card().classes("p-3 w-full"):
                                with ui.row().classes("justify-between items-center"):
                                    with ui.column():
                                        ui.label(
                                            f"{r['sku']} — {r['item_name']}"
                                        ).classes("font-semibold text-sm")
                                        ui.label(
                                            f"Ref: {r['reference']} | {r['quantity']} units @ {r['warehouse_name']}"
                                        ).classes("text-xs").style(
                                            "color:var(--ink-soft)"
                                        )
                                    with ui.row().classes("gap-1"):
                                        ui.button(
                                            "Fulfil",
                                            icon="check",
                                            on_click=lambda rid=r["id"]: fulfil(rid),
                                        ).props("flat dense color=teal")
                                        ui.button(
                                            "Cancel",
                                            icon="close",
                                            on_click=lambda rid=r["id"]: cancel(rid),
                                        ).props("flat dense color=red")

                def fulfil(res_id: int):
                    try:
                        api.post(f"/reservations/{res_id}/fulfil", {})
                        ui.notify(
                            "Reservation fulfilled — stock deducted", type="positive"
                        )
                        refresh_list()
                    except Exception as e:
                        ui.notify(f"Failed: {e}", type="negative")

                def cancel(res_id: int):
                    try:
                        api.post(f"/reservations/{res_id}/cancel", {})
                        ui.notify("Reservation cancelled", type="positive")
                        refresh_list()
                    except Exception as e:
                        ui.notify(f"Failed: {e}", type="negative")

                refresh_list()
