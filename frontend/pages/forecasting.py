from nicegui import ui

from api_client import api
from components import render_header
from auth_guard import require_login

RISK_COLORS = {"critical": "red", "warning": "orange", "healthy": "teal", "no_movement": "grey"}
RISK_LABELS = {
    "critical": "CRITICAL — Reorder Now",
    "warning": "WARNING — Order Soon",
    "healthy": "HEALTHY",
    "no_movement": "No Recent Movement",
}


def render_forecasting():
    if not require_login():
        return

    render_header(active="Forecasting")

    with ui.column().classes("w-full p-4 md:p-6 gap-4 page-container"):
        ui.label("Stockout Forecasting").classes("text-2xl font-bold page-title")
        ui.label("Based on outbound velocity over the last 30 days").classes("text-sm").style(
            "color:var(--ink-soft)"
        )

        summary_row = ui.row().classes("w-full gap-4 stats-row")
        table_container = ui.column().classes("w-full mt-4")

        def refresh():
            summary_row.clear()
            table_container.clear()
            try:
                data = api.get("/forecasting/stockout-risk")
            except Exception as e:
                with table_container:
                    ui.label(f"Failed to load forecast: {e}").classes("text-red-600")
                return

            critical = sum(1 for d in data if d["risk"] == "critical")
            warning = sum(1 for d in data if d["risk"] == "warning")
            healthy = sum(1 for d in data if d["risk"] == "healthy")

            with summary_row:
                _stat_card("Critical", critical, "error", "red")
                _stat_card("Warning", warning, "warning", "orange")
                _stat_card("Healthy", healthy, "check_circle", "teal")

            with table_container:
                columns = [
                    {"name": "sku", "label": "SKU", "field": "sku"},
                    {"name": "name", "label": "Name", "field": "name"},
                    {"name": "current_quantity", "label": "Current Qty", "field": "current_quantity"},
                    {"name": "daily_velocity", "label": "Daily Usage", "field": "daily_velocity"},
                    {"name": "days_until_stockout", "label": "Days Until Stockout", "field": "days_until_stockout"},
                    {"name": "risk", "label": "Risk", "field": "risk"},
                ]
                t = ui.table(columns=columns, rows=data, row_key="item_id").classes("w-full")
                t.add_slot(
                    "body-cell-risk",
                    '''
                    <q-td :props="props">
                        <q-badge :color="
                            props.value === 'critical' ? 'red' :
                            props.value === 'warning' ? 'orange' :
                            props.value === 'healthy' ? 'teal' : 'grey'
                        " :label="props.value.toUpperCase()" />
                    </q-td>
                    ''',
                )
                t.on("row-click", lambda e: ui.navigate.to(f"/items/{e.args[1]['item_id']}"))

        ui.button("Refresh", icon="refresh", on_click=refresh).classes("self-end")
        refresh()


def _stat_card(title: str, value: int, icon: str, color: str):
    with ui.card().classes("w-48 p-4"):
        with ui.row().classes("items-center gap-2"):
            ui.icon(icon).classes(f"text-2xl text-{color}-600")
            ui.label(title).style("color:var(--ink-soft)")
        ui.label(str(value)).classes("text-2xl font-bold mono mt-1")
