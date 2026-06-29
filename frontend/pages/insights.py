from nicegui import ui

from api_client import api
from components import render_header
from auth_guard import require_login


def render_insights():
    if not require_login():
        return

    render_header(active="Insights")

    with ui.column().classes("w-full p-4 md:p-6 gap-4 page-container"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("auto_awesome").classes("text-2xl").style("color:#E8A33D;")
            ui.label("Smart Insights").classes("text-2xl font-bold page-title")
        ui.label("Auto-generated, data-driven observations about your inventory").classes("text-sm").style(
            "color:var(--ink-soft)"
        )

        container = ui.column().classes("w-full gap-4 mt-2")

        def refresh():
            container.clear()
            try:
                data = api.get("/insights")
            except Exception as e:
                with container:
                    ui.label(f"Failed to load insights: {e}").classes("text-red-600")
                return

            with container:
                for ins in data:
                    with ui.card().classes("w-full p-5").style(
                        f"border-left: 5px solid {ins['color']}; background: linear-gradient(90deg, {ins['color']}10, transparent);"
                    ):
                        with ui.row().classes("items-start gap-4 w-full"):
                            with ui.element("div").classes("rounded-full flex items-center justify-center").style(
                                f"width:48px; height:48px; background:{ins['color']}20; flex-shrink:0;"
                            ):
                                ui.icon(ins["icon"]).classes("text-2xl").style(f"color:{ins['color']};")

                            with ui.column().classes("flex-grow gap-1"):
                                ui.label(ins["title"]).classes("font-semibold text-base")
                                ui.label(ins["detail"]).classes("text-sm").style("color:var(--ink-soft)")

                            ui.button(
                                ins["action_label"], icon="arrow_forward",
                                on_click=lambda url=ins["action_url"]: ui.navigate.to(url)
                            ).props("outline").style(f"border-color:{ins['color']}; color:{ins['color']};")

        ui.button("Refresh Insights", icon="refresh", on_click=refresh).classes("self-end")
        refresh()