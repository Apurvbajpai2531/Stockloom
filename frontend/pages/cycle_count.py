from nicegui import ui

from api_client import api
from components import render_header
from auth_guard import require_login


def render_cycle_count():
    if not require_login():
        return

    render_header(active="Cycle Count")

    with ui.column().classes("w-full p-4 md:p-6 gap-6 page-container"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("fact_check").classes("text-2xl").style("color:#E8A33D;")
            ui.label("Inventory Cycle Count").classes("text-2xl font-bold page-title")
        ui.label("Physical verification of stock — compare actual vs system quantities").classes("text-sm").style("color:var(--ink-soft)")

        active_count = {"id": None}
        count_container = ui.column().classes("w-full")
        history_container = ui.column().classes("w-full")

        def load_history():
            history_container.clear()
            try:
                counts = api.get("/cycle-counts")
            except Exception:
                return
            with history_container:
                ui.label("Past Cycle Counts").classes("font-semibold mt-4")
                if not counts:
                    ui.label("No cycle counts yet.").style("color:var(--ink-soft)")
                    return
                cols = [
                    {"name": "id", "label": "ID", "field": "id"},
                    {"name": "warehouse_name", "label": "Warehouse", "field": "warehouse_name"},
                    {"name": "status", "label": "Status", "field": "status"},
                    {"name": "line_count", "label": "Items", "field": "line_count"},
                    {"name": "verified_count", "label": "Counted", "field": "verified_count"},
                    {"name": "variance_count", "label": "Variances", "field": "variance_count"},
                    {"name": "created_by", "label": "Created By", "field": "created_by"},
                    {"name": "created_at", "label": "Date", "field": "created_at"},
                ]
                for c in counts:
                    c["created_at"] = (c["created_at"] or "")[:10]
                t = ui.table(columns=cols, rows=counts, row_key="id").classes("w-full")
                t.on("row-click", lambda e: open_count(e.args[1]["id"]))

        def open_count(cc_id: int):
            count_container.clear()
            try:
                cc = api.get(f"/cycle-counts/{cc_id}")
            except Exception as e:
                ui.notify(f"Error: {e}", type="negative")
                return
            active_count["id"] = cc_id

            with count_container:
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label(f"Cycle Count #{cc_id} — {cc['warehouse_name']}").classes("font-semibold")
                    if cc["status"] == "open":
                        with ui.row().classes("gap-2"):
                            ui.button("Complete (no adjustments)", on_click=lambda: complete(cc_id, False)).props("outline")
                            ui.button("Complete + Apply Adjustments", icon="tune", on_click=lambda: complete(cc_id, True)).props("color=primary")

                for line in cc["lines"]:
                    is_variance = line["variance"] is not None and line["variance"] != 0
                    card_style = "border-left:3px solid #C0463C;" if is_variance else ""
                    with ui.card().classes("p-3 w-full").style(card_style):
                        with ui.row().classes("items-center justify-between"):
                            with ui.column():
                                ui.label(f"{line['sku']} — {line['name']}").classes("text-sm font-semibold")
                                ui.label(f"System: {line['system_quantity']}").classes("text-xs").style("color:var(--ink-soft)")
                            with ui.row().classes("items-center gap-2"):
                                if line["is_verified"]:
                                    variance_color = "#C0463C" if is_variance else "#2F6F6B"
                                    ui.badge(f"Variance: {line['variance']:+d}", color="red" if is_variance else "teal")
                                else:
                                    counted = ui.number("Counted Qty", value=line["system_quantity"]).classes("w-28")
                                    ui.button("Submit", on_click=lambda lid=line["id"], c=counted: submit_count(cc_id, lid, c)).props("flat dense")

        def submit_count(cc_id: int, line_id: int, counted_input):
            try:
                result = api.post(f"/cycle-counts/{cc_id}/submit-count", {
                    "line_id": line_id,
                    "counted_quantity": int(counted_input.value),
                })
                var = result["variance"]
                ui.notify(f"Counted. Variance: {var:+d}", type="positive" if var == 0 else "warning")
                open_count(cc_id)
            except Exception as e:
                ui.notify(f"Error: {e}", type="negative")

        def complete(cc_id: int, apply: bool):
            try:
                api.post(f"/cycle-counts/{cc_id}/complete", {}, params={"apply_adjustments": str(apply).lower()})
                msg = "Cycle count completed with adjustments applied!" if apply else "Cycle count completed."
                ui.notify(msg, type="positive")
                count_container.clear()
                load_history()
            except Exception as e:
                ui.notify(f"Error: {e}", type="negative")

        # Start new count
        with ui.card().classes("w-full p-4"):
            ui.label("Start New Cycle Count").classes("font-semibold mb-2")
            warehouses = api.get("/warehouses")
            wh_options = {w["id"]: f"{w['code']} — {w['name']}" for w in warehouses}
            wh_sel = ui.select(wh_options, label="Select Warehouse").classes("w-64")

            def start():
                if not wh_sel.value:
                    ui.notify("Select a warehouse", type="warning")
                    return
                try:
                    result = api.post(f"/cycle-counts?warehouse_id={wh_sel.value}", {})
                    ui.notify(f"Cycle count started — {result['line_count']} items to count", type="positive")
                    open_count(result["id"])
                    load_history()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")

            ui.button("Start Count", icon="play_arrow", on_click=start).props("color=primary")

        count_container
        load_history()