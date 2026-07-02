from nicegui import ui

from api_client import api
from components import render_header
from auth_guard import require_login


def render_rules():
    if not require_login():
        return

    render_header(active="Alert Rules")

    with ui.column().classes("w-full p-4 md:p-6 gap-6 page-container"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("rule").classes("text-2xl").style("color:#E8A33D;")
            ui.label("Custom Alert Rules").classes("text-2xl font-bold page-title")
        ui.label("Define your own conditions — evaluated against real-time stock").classes(
            "text-sm"
        ).style("color:var(--ink-soft)")

        # ---- Triggered Rules Banner ----
        triggered_box = ui.column().classes("w-full")

        def check_rules():
            triggered_box.clear()
            try:
                result = api.get("/rules/evaluate")
                if result["triggered_count"] > 0:
                    with triggered_box:
                        with ui.card().classes("w-full p-4").style("border-left:4px solid #C0463C;"):
                            with ui.row().classes("items-center gap-2 mb-2"):
                                ui.icon("notification_important").style("color:#C0463C;")
                                ui.label(f"{result['triggered_count']} rule(s) currently triggered").classes("font-semibold")
                            for t in result["triggered"]:
                                with ui.row().classes("items-center gap-3 text-sm py-1").style("border-bottom:1px solid var(--line);"):
                                    ui.badge(t["condition"].upper(), color="red")
                                    ui.label(f"{t['rule_name']}").classes("font-semibold")
                                    ui.label(f"{t['sku']} — current: {t['current_quantity']} (threshold: {t['threshold']})").style("color:var(--ink-soft)")
                                    ui.button(icon="open_in_new", on_click=lambda iid=t["item_id"]: ui.navigate.to(f"/items/{iid}")).props("flat dense")
                else:
                    with triggered_box:
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("check_circle").style("color:#2F6F6B;")
                            ui.label("All rules pass — no conditions triggered right now").style("color:#2F6F6B;")
            except Exception as e:
                with triggered_box:
                    ui.label(f"Error evaluating rules: {e}").classes("text-red-600")

        ui.button("Evaluate Now", icon="play_arrow", on_click=check_rules).props("outline")

        with ui.row().classes("w-full gap-6 chart-row"):
            # ---- Left: Existing Rules ----
            with ui.card().classes("flex-1 p-4"):
                ui.label("Active Rules").classes("font-semibold mb-2")
                rules_container = ui.column().classes("w-full gap-2")

                def refresh_rules():
                    rules_container.clear()
                    try:
                        rule_list = api.get("/rules")
                    except Exception as e:
                        with rules_container:
                            ui.label(f"Error: {e}").classes("text-red-600")
                        return
                    if not rule_list:
                        with rules_container:
                            ui.label("No rules defined yet.").style("color:var(--ink-soft)")
                        return
                    with rules_container:
                        for r in rule_list:
                            cond_color = "#C0463C" if r["condition"] == "below" else ("#2F6F6B" if r["condition"] == "above" else "#2563eb")
                            with ui.card().classes("p-3 w-full"):
                                with ui.row().classes("items-center justify-between"):
                                    with ui.row().classes("items-center gap-2"):
                                        ui.badge(r["condition"].upper(), color="red" if r["condition"] == "below" else "teal")
                                        ui.label(r["name"]).classes("font-semibold text-sm")
                                    with ui.row().classes("items-center gap-2"):
                                        ui.label(f"threshold: {r['threshold']}").classes("mono text-xs").style("color:var(--ink-soft)")
                                        ui.button(icon="delete", on_click=lambda rid=r["id"]: delete_rule(rid)).props("flat dense color=red")

                def delete_rule(rule_id: int):
                    try:
                        api.delete(f"/rules/{rule_id}")
                        ui.notify("Rule deleted", type="positive")
                        refresh_rules()
                    except Exception as e:
                        ui.notify(f"Error: {e}", type="negative")

                refresh_rules()

            # ---- Right: New Rule Form ----
            with ui.card().classes("flex-1 p-4"):
                ui.label("Create New Rule").classes("font-semibold mb-2")

                items_list = api.get("/items", params={"limit": 200})
                warehouses_list = api.get("/warehouses")
                item_options = {None: "All Items"} | {i["id"]: f"{i['sku']} — {i['name']}" for i in items_list}
                wh_options = {None: "All Warehouses"} | {w["id"]: w["name"] for w in warehouses_list}

                rule_name = ui.input("Rule Name").classes("w-full")
                item_sel = ui.select(item_options, value=None, label="Item").classes("w-full")
                wh_sel = ui.select(wh_options, value=None, label="Warehouse").classes("w-full")
                condition_sel = ui.select(
                    {"below": "Quantity BELOW threshold", "above": "Quantity ABOVE threshold", "equals": "Quantity EQUALS threshold"},
                    value="below", label="Condition"
                ).classes("w-full")
                threshold_input = ui.number("Threshold Quantity", value=10).classes("w-full")
                error_label = ui.label("").classes("text-red-600 text-sm")

                def save_rule():
                    if not rule_name.value or not rule_name.value.strip():
                        error_label.text = "Rule name is required"
                        return
                    try:
                        api.post("/rules", {
                            "name": rule_name.value.strip(),
                            "item_id": item_sel.value,
                            "warehouse_id": wh_sel.value,
                            "condition": condition_sel.value,
                            "threshold": int(threshold_input.value),
                        })
                        ui.notify("Rule created", type="positive")
                        rule_name.value = ""
                        refresh_rules()
                        check_rules()
                    except Exception as e:
                        ui.notify(f"Failed: {e}", type="negative")

                ui.button("Create Rule", icon="add", on_click=save_rule).classes("w-full mt-2").style(
                    "background:var(--ink); color:white;"
                )

        check_rules()
        ui.timer(30.0, check_rules)