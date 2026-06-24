from nicegui import ui

from api_client import api
from components import render_header
from auth_guard import require_login


def render_reorder_suggestions():
    if not require_login():
        return

    render_header(active="Reorder Suggestions")

    with ui.column().classes("w-full p-4 md:p-6 gap-4 page-container"):
        ui.label("Reorder Suggestions").classes("text-2xl font-bold page-title")
        ui.label("Grouped by supplier — what to order and estimated cost").classes("text-sm").style(
            "color:var(--ink-soft)"
        )

        container = ui.column().classes("w-full gap-4")

        def refresh():
            container.clear()
            try:
                data = api.get("/reports/reorder-suggestions")
            except Exception as e:
                with container:
                    ui.label(f"Failed to load: {e}").classes("text-red-600")
                return

            if not data:
                with container:
                    ui.label("Nothing to reorder right now — all stock levels are healthy.").style(
                        "color:var(--teal); font-weight:600;"
                    )
                return

            with container:
                for group in data:
                    with ui.card().classes("w-full p-4"):
                        with ui.row().classes("items-center justify-between w-full"):
                            ui.label(group["supplier_name"]).classes("font-semibold text-lg")
                            ui.label(f"Est. Cost: ${group['estimated_cost']:,.2f}").classes("mono font-bold").style(
                                "color:var(--amber);"
                            )

                        item_table = ui.table(
                            columns=[
                                {"name": "sku", "label": "SKU", "field": "sku"},
                                {"name": "name", "label": "Name", "field": "name"},
                                {"name": "current_quantity", "label": "Current", "field": "current_quantity"},
                                {"name": "suggested_quantity", "label": "Suggested Order", "field": "suggested_quantity"},
                                {"name": "estimated_cost", "label": "Cost", "field": "estimated_cost"},
                            ],
                            rows=group["items"], row_key="item_id",
                        ).classes("w-full mt-2")

        ui.button("Refresh", icon="refresh", on_click=refresh).classes("self-end")
        refresh()
