from nicegui import ui


def render_welcome():
    with ui.column().classes("w-full h-screen items-center justify-center gap-10 relative").style(
        "background: radial-gradient(circle at 30% 20%, #232A3D 0%, #1C2230 55%, #14161C 100%); overflow:hidden;"
    ):
        # subtle background grid lines for depth
        ui.html('''
        <div style="position:absolute; inset:0; opacity:0.06;
            background-image: linear-gradient(#E8A33D 1px, transparent 1px), linear-gradient(90deg, #E8A33D 1px, transparent 1px);
            background-size: 48px 48px;">
        </div>
        ''')

        with ui.column().classes("items-center gap-4 relative z-10"):
            ui.icon("warehouse").style(
                "color:#E8A33D; font-size:72px; filter: drop-shadow(0 0 24px rgba(232,163,61,0.35));"
            )
            ui.label("STOCKLOOM").classes("font-bold text-5xl tracking-widest text-white").style(
                "font-family:'Space Grotesk',sans-serif;"
            )
            with ui.row().classes("items-center gap-2"):
                ui.element("div").style("width:32px; height:2px; background:#E8A33D;")
                ui.label("INVENTORY & WAREHOUSE CONTROL").classes("text-xs tracking-widest").style(
                    "color:#9A9C9F; font-family:'JetBrains Mono',monospace;"
                )
                ui.element("div").style("width:32px; height:2px; background:#E8A33D;")

        ui.button(
            "Enter Dashboard", icon="arrow_forward", on_click=lambda: ui.navigate.to("/dashboard")
        ).props("unelevated").classes("relative z-10").style(
            "background:#E8A33D; color:#1C2230; font-weight:700; padding:14px 32px; "
            "border-radius:10px; font-size:15px; letter-spacing:0.02em; "
            "box-shadow: 0 8px 24px rgba(232,163,61,0.25);"
        )

        ui.label("v1.0").classes("absolute bottom-6 text-xs relative z-10").style("color:#5B6275;")