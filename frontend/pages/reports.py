from nicegui import ui
import os

from components import render_header

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")


def render_reports():
    render_header(active="Reports")

    with ui.column().classes("w-full p-4 md:p-6 gap-6 page-container"):
        ui.label("Reports").classes("text-2xl font-bold page-title")

        with ui.row().classes("gap-4 flex-wrap"):
            with ui.card().classes("p-4 w-64"):
                ui.icon("inventory_2").classes("text-3xl")
                ui.label("Items Report").classes("font-semibold mt-2")
                ui.label("All items with current stock totals").classes("text-sm").style("color:var(--ink-soft)")
                ui.button(
                    "Download CSV", icon="download",
                    on_click=lambda: ui.navigate.to(f"{API_BASE}/reports/items.csv", new_tab=True)
                ).classes("mt-3")

            with ui.card().classes("p-4 w-64"):
                ui.icon("sync_alt").classes("text-3xl")
                ui.label("Movements Report").classes("font-semibold mt-2")
                ui.label("Full stock movement history").classes("text-sm").style("color:var(--ink-soft)")
                ui.button(
                    "Download CSV", icon="download",
                    on_click=lambda: ui.navigate.to(f"{API_BASE}/reports/movements.csv", new_tab=True)
                ).classes("mt-3")