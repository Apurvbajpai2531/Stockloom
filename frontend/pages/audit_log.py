from nicegui import ui

from api_client import api
from components import render_header
from auth_guard import require_login


def render_audit_log():
    if not require_login():
        return

    render_header(active="Audit Log")

    with ui.column().classes("w-full p-4 md:p-6 gap-4 page-container"):
        ui.label("Audit Log").classes("text-2xl font-bold page-title")
        ui.label("Recent create/delete actions across the system").classes("text-sm").style(
            "color:var(--ink-soft)"
        )

        columns = [
            {"name": "created_at", "label": "When", "field": "created_at"},
            {"name": "action", "label": "Action", "field": "action"},
            {"name": "entity_type", "label": "Entity", "field": "entity_type"},
            {"name": "entity_id", "label": "Entity ID", "field": "entity_id"},
            {"name": "username", "label": "User", "field": "username"},
            {"name": "details", "label": "Details", "field": "details"},
        ]
        table = ui.table(columns=columns, rows=[], row_key="id").classes("w-full")

        def refresh():
            try:
                table.rows = api.get("/audit-logs", params={"limit": 100})
                table.update()
            except Exception as e:
                ui.notify(f"Failed to load audit logs: {e}", type="negative")

        ui.button("Refresh", icon="refresh", on_click=refresh).classes("self-end")
        refresh()
