from nicegui import ui

from api_client import api
from auth_guard import require_login
from components import render_header


def render_cost_analysis():
    if not require_login():
        return

    render_header(active="Cost Analysis")

    with ui.column().classes("w-full p-4 md:p-6 gap-6 page-container"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("calculate").classes("text-2xl").style("color:#E8A33D;")
            ui.label("Cost Analysis & EOQ").classes("text-2xl font-bold page-title")
        ui.label(
            "Economic Order Quantity, Holding Cost Analysis — real finance metrics"
        ).classes("text-sm").style("color:var(--ink-soft)")

        # ---- Holding Cost Summary ----
        try:
            hc = api.get("/cost-analysis/holding-cost")
            with ui.row().classes("w-full gap-4 flex-wrap mb-4"):
                for label, val, color in [
                    (
                        "Annual Holding Cost",
                        f"${hc['total_annual_holding_cost']:,.0f}",
                        "#C0463C",
                    ),
                    (
                        "Monthly Holding Cost",
                        f"${hc['monthly_holding_cost']:,.0f}",
                        "#E8A33D",
                    ),
                    ("Holding Rate Used", hc["holding_rate_used"], "#2563eb"),
                ]:
                    with ui.card().classes("p-4 w-48").style(
                        f"border-top:3px solid {color};"
                    ):
                        ui.label(label).classes("text-xs").style(
                            "color:var(--ink-soft)"
                        )
                        ui.label(val).classes("text-xl font-bold mono").style(
                            f"color:{color};"
                        )

            # Holding cost by category chart
            if hc["by_category"]:
                ui.echart(
                    {
                        "tooltip": {"trigger": "axis"},
                        "xAxis": {
                            "type": "category",
                            "data": [d["category"] for d in hc["by_category"]],
                        },
                        "yAxis": {"type": "value", "name": "Annual Holding Cost ($)"},
                        "series": [
                            {
                                "type": "bar",
                                "data": [
                                    d["annual_holding_cost"] for d in hc["by_category"]
                                ],
                                "itemStyle": {"color": "#E8A33D"},
                            }
                        ],
                    }
                ).classes("w-full h-48")
        except Exception as e:
            ui.label(f"Error loading holding costs: {e}").classes("text-red-600")

        # ---- EOQ Table ----
        ui.label("Economic Order Quantity (EOQ) per Item").classes(
            "font-semibold text-lg mt-2"
        )
        ui.html(
            """
        <div style="font-size:11px;color:var(--ink-soft);margin-bottom:8px;">
            EOQ = √(2 × Annual Demand × Ordering Cost / Holding Cost per unit) — determines optimal order size to minimize total inventory cost.
        </div>
        """
        )

        try:
            eoq_data = api.get("/cost-analysis/eoq")
            if not eoq_data:
                ui.label(
                    "No outbound movement data yet — record some outbound stock movements to see EOQ analysis."
                ).style("color:var(--ink-soft)")
            else:
                cols = [
                    {"name": "sku", "label": "SKU", "field": "sku"},
                    {"name": "name", "label": "Name", "field": "name"},
                    {
                        "name": "annual_demand",
                        "label": "Annual Demand",
                        "field": "annual_demand",
                    },
                    {"name": "eoq", "label": "EOQ (units)", "field": "eoq"},
                    {
                        "name": "orders_per_year",
                        "label": "Orders/Year",
                        "field": "orders_per_year",
                    },
                    {
                        "name": "total_annual_cost",
                        "label": "Total Annual Cost",
                        "field": "total_annual_cost",
                    },
                    {
                        "name": "current_threshold",
                        "label": "Current Threshold",
                        "field": "current_threshold",
                    },
                    {
                        "name": "suggested_threshold",
                        "label": "Suggested Threshold",
                        "field": "suggested_threshold",
                    },
                ]
                for row in eoq_data:
                    row["total_annual_cost"] = f"${row['total_annual_cost']:,.2f}"

                t = ui.table(
                    columns=cols, rows=eoq_data[:50], row_key="item_id"
                ).classes("w-full")
                t.on(
                    "row-click",
                    lambda e: ui.navigate.to(f"/items/{e.args[1]['item_id']}"),
                )
        except Exception as e:
            ui.label(f"Error: {e}").classes("text-red-600")
