from nicegui import ui

from api_client import api
from components import render_header
from auth_guard import require_login


def render_supplier_intelligence():
    if not require_login():
        return

    render_header(active="Supplier Intelligence")

    with ui.column().classes("w-full p-4 md:p-6 gap-6 page-container"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("store").classes("text-2xl").style("color:#E8A33D;")
            ui.label("Supplier Intelligence").classes("text-2xl font-bold page-title")

        with ui.tabs().classes("w-full") as tabs:
            tab_perf = ui.tab("Performance Scorecard")
            tab_turn = ui.tab("Inventory Turnover & GMROI")
            tab_dead = ui.tab("Dead Stock Report")

        with ui.tab_panels(tabs, value=tab_perf).classes("w-full"):

            # ---- Tab 1: Supplier Performance ----
            with ui.tab_panel(tab_perf):
                try:
                    perf_data = api.get("/supplier-analytics/performance")
                except Exception as e:
                    ui.label(f"Error: {e}").classes("text-red-600")
                    perf_data = []

                if not perf_data:
                    ui.label("No suppliers found.").style("color:var(--ink-soft)")
                else:
                    with ui.row().classes("w-full gap-4 flex-wrap mb-4"):
                        total_val = sum(s["inventory_value"] for s in perf_data)
                        total_items = sum(s["item_count"] for s in perf_data)
                        top = perf_data[0] if perf_data else {}

                        for label, val, icon in [
                            ("Total Suppliers", len(perf_data), "store"),
                            ("Total Items Tracked", total_items, "inventory_2"),
                            ("Total Value Held", f"${total_val:,.0f}", "payments"),
                            ("Top Supplier", top.get("supplier_name", "—"), "star"),
                        ]:
                            with ui.card().classes("p-4 w-48").style(
                                "border-top:3px solid #E8A33D;"
                            ):
                                ui.icon(icon).style("color:#E8A33D;")
                                ui.label(label).classes("text-xs mt-1").style(
                                    "color:var(--ink-soft)"
                                )
                                ui.label(str(val)).classes("text-xl font-bold mono")

                    columns = [
                        {
                            "name": "supplier_name",
                            "label": "Supplier",
                            "field": "supplier_name",
                        },
                        {"name": "item_count", "label": "Items", "field": "item_count"},
                        {
                            "name": "inventory_value",
                            "label": "Value Held",
                            "field": "inventory_value",
                        },
                        {
                            "name": "open_purchase_orders",
                            "label": "Open POs",
                            "field": "open_purchase_orders",
                        },
                        {
                            "name": "received_purchase_orders",
                            "label": "Received POs",
                            "field": "received_purchase_orders",
                        },
                        {
                            "name": "avg_fulfillment_days",
                            "label": "Avg Fulfillment (days)",
                            "field": "avg_fulfillment_days",
                        },
                        {
                            "name": "reliability_score",
                            "label": "Reliability",
                            "field": "reliability_score",
                        },
                    ]
                    for row in perf_data:
                        row["inventory_value"] = f"${row['inventory_value']:,.2f}"
                        row["avg_fulfillment_days"] = (
                            f"{row['avg_fulfillment_days']}d"
                            if row["avg_fulfillment_days"]
                            else "N/A"
                        )
                        row["reliability_score"] = (
                            f"{row['reliability_score']}%"
                            if row["reliability_score"] is not None
                            else "N/A"
                        )

                    ui.table(
                        columns=columns, rows=perf_data, row_key="supplier_id"
                    ).classes("w-full")

            # ---- Tab 2: Turnover & GMROI ----
            with ui.tab_panel(tab_turn):
                try:
                    turn_data = api.get("/supplier-analytics/turnover")
                except Exception as e:
                    ui.label(f"Error: {e}").classes("text-red-600")
                    turn_data = []

                if turn_data:
                    health_colors = {
                        "excellent": "#2F6F6B",
                        "good": "#2563eb",
                        "slow": "#E8A33D",
                        "dead": "#C0463C",
                    }
                    with ui.row().classes("w-full gap-4 flex-wrap mb-4"):
                        for d in turn_data:
                            color = health_colors.get(d["health"], "#9A9C9F")
                            with ui.card().classes("p-4 w-56").style(
                                f"border-top:3px solid {color};"
                            ):
                                ui.label(d["category"]).classes("font-semibold")
                                with ui.row().classes("justify-between mt-2"):
                                    ui.label("Turnover").classes("text-xs").style(
                                        "color:var(--ink-soft)"
                                    )
                                    ui.label(f"{d['turnover_ratio']}x").classes(
                                        "mono font-bold"
                                    )
                                with ui.row().classes("justify-between"):
                                    ui.label("GMROI").classes("text-xs").style(
                                        "color:var(--ink-soft)"
                                    )
                                    ui.label(f"${d['gmroi']}").classes(
                                        "mono font-bold"
                                    ).style(f"color:{color};")
                                with ui.row().classes("justify-between"):
                                    ui.label("COGS").classes("text-xs").style(
                                        "color:var(--ink-soft)"
                                    )
                                    ui.label(f"${d['cogs_annual']:,.0f}").classes(
                                        "mono text-xs"
                                    )
                                ui.badge(
                                    d["health"].upper(),
                                    color=(
                                        "teal"
                                        if d["health"] in ("excellent", "good")
                                        else (
                                            "orange" if d["health"] == "slow" else "red"
                                        )
                                    ),
                                ).classes("mt-2")

                    ui.html(
                        """
                    <div style="margin-top:12px;padding:12px;background:rgba(0,0,0,0.03);border-radius:8px;font-size:12px;color:var(--ink-soft);">
                        <b>Turnover Ratio</b>: How many times inventory is sold per year. Higher = better capital efficiency.<br>
                        <b>GMROI</b>: Gross Margin Return on Investment. $1+ = profitable inventory. Target: $3+.<br>
                        <b>Health</b>: Excellent (6x+), Good (3-6x), Slow (1-3x), Dead (&lt;1x)
                    </div>
                    """
                    )

            # ---- Tab 3: Dead Stock ----
            with ui.tab_panel(tab_dead):
                try:
                    dead_data = api.get("/supplier-analytics/dead-stock")
                except Exception as e:
                    ui.label(f"Error: {e}").classes("text-red-600")
                    dead_data = {"count": 0, "total_tied_capital": 0, "items": []}

                with ui.row().classes("gap-4 mb-4"):
                    with ui.card().classes("p-4 w-48").style(
                        "border-top:3px solid #C0463C;"
                    ):
                        ui.icon("inventory").style("color:#C0463C;")
                        ui.label("Dead Stock Items").classes("text-xs mt-1").style(
                            "color:var(--ink-soft)"
                        )
                        ui.label(str(dead_data["count"])).classes(
                            "text-2xl font-bold mono"
                        )
                    with ui.card().classes("p-4 w-48").style(
                        "border-top:3px solid #E8A33D;"
                    ):
                        ui.icon("payments").style("color:#E8A33D;")
                        ui.label("Capital Tied Up").classes("text-xs mt-1").style(
                            "color:var(--ink-soft)"
                        )
                        ui.label(f"${dead_data['total_tied_capital']:,.0f}").classes(
                            "text-2xl font-bold mono"
                        )

                if dead_data["items"]:
                    columns = [
                        {"name": "sku", "label": "SKU", "field": "sku"},
                        {"name": "name", "label": "Name", "field": "name"},
                        {"name": "quantity", "label": "Qty Idle", "field": "quantity"},
                        {
                            "name": "unit_price",
                            "label": "Unit Price",
                            "field": "unit_price",
                        },
                        {
                            "name": "tied_capital",
                            "label": "Capital Tied",
                            "field": "tied_capital",
                        },
                        {
                            "name": "days_idle",
                            "label": "Days Idle",
                            "field": "days_idle",
                        },
                    ]
                    t = ui.table(
                        columns=columns, rows=dead_data["items"], row_key="item_id"
                    ).classes("w-full")
                    t.on(
                        "row-click",
                        lambda e: ui.navigate.to(f"/items/{e.args[1]['item_id']}"),
                    )
                else:
                    ui.label("No dead stock found — great inventory health!").style(
                        "color:#2F6F6B; font-weight:600;"
                    )
