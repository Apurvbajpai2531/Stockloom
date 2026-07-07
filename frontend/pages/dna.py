import datetime
from nicegui import ui
from api_client import api
from auth_guard import require_login


def render_dna():
    if not require_login():
        return

    ui.add_head_html(
        """
    <style>
    body { background: #000 !important; }
    .dna-container {
        position: fixed; inset: 0; background: #000;
        font-family: "JetBrains Mono", monospace;
        display: flex; flex-direction: column; padding: 16px; gap: 10px;
        overflow: hidden;
    }
    .dna-header {
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #ffffff15; padding-bottom: 8px;
    }
    .dna-title { font-size: 16px; font-weight: 700; letter-spacing: 0.12em; color: #fff; }
    .dna-legend { display: flex; gap: 16px; align-items: center; }
    .dna-legend-item { display: flex; align-items: center; gap: 5px; font-size: 10px; color: #ffffff50; }
    .dna-legend-dot { width: 10px; height: 10px; border-radius: 2px; }
    .dna-grid {
        flex: 1; display: flex; flex-wrap: wrap; gap: 3px;
        content: ""; align-content: flex-start; overflow: hidden;
    }
    .dna-cell {
        width: 28px; height: 28px; border-radius: 4px; cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        font-size: 7px; font-weight: 700; letter-spacing: 0;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        position: relative;
    }
    .dna-cell:hover {
        transform: scale(1.6); z-index: 99;
        box-shadow: 0 0 12px currentColor;
    }
    .dna-tooltip {
        position: absolute; bottom: 120%; left: 50%; transform: translateX(-50%);
        background: #1C2230; border: 1px solid #E8A33D; border-radius: 6px;
        padding: 6px 8px; font-size: 9px; white-space: nowrap; pointer-events: none;
        color: white; display: none; z-index: 999;
    }
    .dna-cell:hover .dna-tooltip { display: block; }
    .dna-exit {
        position: fixed; top: 12px; right: 16px; background: transparent;
        border: 1px solid #C0463C; color: #C0463C; padding: 4px 12px;
        border-radius: 4px; cursor: pointer; font-family: "JetBrains Mono", monospace;
        font-size: 11px; z-index: 9999;
    }
    .dna-exit:hover { background: #C0463C20; }
    @keyframes dna-glow {
        0%,100% { opacity: 0.8; }
        50% { opacity: 1; }
    }
    .dna-cell { animation: dna-glow 3s ease-in-out infinite; }
    </style>
    """
    )

    container = ui.html("")

    def build():
        try:
            items = api.get("/items", params={"limit": 500})
            categories = api.get("/categories")
        except Exception as e:
            container.content = f'<div style="color:red;padding:20px;">Error: {e}</div>'
            return

        cat_colors = [
            "#00ff88",
            "#E8A33D",
            "#2563eb",
            "#C0463C",
            "#a855f7",
            "#06b6d4",
            "#ec4899",
            "#84cc16",
        ]
        cat_map = {}
        for i, cat in enumerate(categories):
            cat_map[cat["id"]] = cat_colors[i % len(cat_colors)]

        max_qty = max((item.get("total_quantity", 0) for item in items), default=1) or 1
        max((float(item.get("unit_price", 0)) for item in items), default=1) or 1

        cells = ""
        for item in items:
            cat_id = item.get("category_id")
            base_color = cat_map.get(cat_id, "#ffffff")
            qty = item.get("total_quantity", 0)
            price = float(item.get("unit_price", 0))
            is_low = qty <= item.get("reorder_threshold", 10)

            brightness = 0.3 + (qty / max_qty) * 0.7
            border_color = "#C0463C" if is_low else base_color
            sku_short = item.get("sku", "?").replace("SKU-", "")

            hex_r = int(int(base_color[1:3], 16) * brightness)
            hex_g = int(int(base_color[3:5], 16) * brightness)
            hex_b = int(int(base_color[5:7], 16) * brightness)
            bg_color = f"rgb({hex_r},{hex_g},{hex_b})"

            tooltip_text = (
                f"{item['sku']} | {item['name'][:20]} | {qty} units | ${price:.0f}"
            )
            alert_indicator = " !" if is_low else ""

            cells += f"""
            <div class="dna-cell" style="background:{bg_color}; border:1px solid {border_color}40;
                color:{base_color}; animation-delay:{hash(item["sku"]) % 30 * 0.1}s;">
                {sku_short}{alert_indicator}
                <div class="dna-tooltip">{tooltip_text}</div>
            </div>"""

        legend_html = ""
        for i, cat in enumerate(categories):
            color = cat_colors[i % len(cat_colors)]
            legend_html += f"""
            <div class="dna-legend-item">
                <div class="dna-legend-dot" style="background:{color};"></div>
                {cat["name"]}
            </div>"""

        now_str = datetime.datetime.now().strftime("%H:%M:%S")

        html = f"""
        <div class="dna-container">
            <button class="dna-exit" onclick="window.location.href='/dashboard'">EXIT DNA VIEW</button>
            <div class="dna-header">
                <div class="dna-title">INVENTORY DNA — {len(items)} items</div>
                <div class="dna-legend">{legend_html}</div>
                <div style="font-size:10px;color:#ffffff30;">{now_str}</div>
            </div>
            <div style="font-size:9px;color:#ffffff25;letter-spacing:0.08em;margin-bottom:2px;">
                BRIGHTNESS = STOCK LEVEL  |  COLOR = CATEGORY  |  RED BORDER = LOW STOCK  |  HOVER = DETAILS
            </div>
            <div class="dna-grid">{cells}</div>
        </div>
        """
        container.content = html

    build()
    ui.timer(15.0, build)
