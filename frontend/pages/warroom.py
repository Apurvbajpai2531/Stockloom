import datetime

from nicegui import ui
from api_client import api
from auth_guard import require_login


def render_warroom():
    if not require_login():
        return

    ui.add_head_html(
        """
    <style>
    body { background: #000 !important; overflow: hidden; }
    .wr-container {
        position: fixed; inset: 0; background: #000;
        font-family: "JetBrains Mono", monospace;
        display: flex; flex-direction: column; padding: 16px; gap: 12px;
        color: #00ff88;
    }
    .wr-header {
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #00ff8830; padding-bottom: 8px;
    }
    .wr-title { font-size: 18px; font-weight: 700; letter-spacing: 0.1em; color: #E8A33D; }
    .wr-time { font-size: 13px; color: #00ff88; }
    .wr-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; flex: 1; }
    .wr-panel {
        border: 1px solid #00ff8820; background: #050a05;
        border-radius: 8px; padding: 12px; overflow: hidden; position: relative;
    }
    .wr-panel-title {
        font-size: 10px; letter-spacing: 0.15em; color: #00ff8880;
        margin-bottom: 8px; text-transform: uppercase;
    }
    .wr-stat { font-size: 36px; font-weight: 700; color: #00ff88; }
    .wr-stat.amber { color: #E8A33D; }
    .wr-stat.red { color: #C0463C; }
    .wr-sub { font-size: 10px; color: #00ff8840; margin-top: 2px; }
    .wr-bar-track { width: 100%; height: 6px; background: #00ff8815; border-radius: 3px; margin: 4px 0; }
    .wr-bar-fill { height: 100%; border-radius: 3px; transition: width 0.8s ease; }
    .wr-feed { font-size: 11px; max-height: 200px; overflow: hidden; }
    .wr-feed-line { padding: 3px 0; border-bottom: 1px solid #00ff8810; animation: wr-fadein 0.4s ease; }
    @keyframes wr-fadein { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; } }
    .wr-gauge-ring { transition: stroke-dashoffset 1s ease; }
    .wr-pulse { animation: wr-pulse 2s infinite; }
    @keyframes wr-pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
    .wr-scanline {
        position: absolute; inset: 0; pointer-events: none;
        background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,136,0.015) 2px, rgba(0,255,136,0.015) 4px);
    }
    .wr-corner { position: absolute; width: 12px; height: 12px; }
    .wr-corner.tl { top:4px; left:4px; border-top:1px solid #E8A33D; border-left:1px solid #E8A33D; }
    .wr-corner.tr { top:4px; right:4px; border-top:1px solid #E8A33D; border-right:1px solid #E8A33D; }
    .wr-corner.bl { bottom:4px; left:4px; border-bottom:1px solid #E8A33D; border-left:1px solid #E8A33D; }
    .wr-corner.br { bottom:4px; right:4px; border-bottom:1px solid #E8A33D; border-right:1px solid #E8A33D; }
    .wr-exit {
        position: fixed; top: 12px; right: 16px; background: transparent;
        border: 1px solid #C0463C; color: #C0463C; padding: 4px 12px;
        border-radius: 4px; cursor: pointer; font-family: "JetBrains Mono", monospace;
        font-size: 11px; letter-spacing: 0.1em; z-index: 9999;
    }
    .wr-exit:hover { background: #C0463C20; }
    </style>
    """
    )

    ui.add_body_html(
        """
    <script>
    setInterval(() => {
        const el = document.getElementById("wr-clock");
        if (el) el.textContent = new Date().toLocaleTimeString("en-GB");
    }, 1000);
    </script>
    """
    )

    container = ui.html("")

    def build():
        try:
            summary = api.get("/dashboard/summary")
            pulse = api.get("/network/pulse")
            warehouses = api.get("/warehouses")
            stock_levels = api.get("/stock-levels")
            movements = api.get("/stock-movements", params={"limit": 8})
            alerts = api.get("/alerts/low-stock")
        except Exception as e:
            container.content = (
                f'<div style="color:red;padding:20px;">Connection error: {e}</div>'
            )
            return

        wh_totals = {}
        for sl in stock_levels:
            wid = sl["warehouse_id"]
            wh_totals[wid] = wh_totals.get(wid, 0) + sl["quantity"]

        max_wh = max(wh_totals.values(), default=1) or 1
        score = pulse["health_score"]
        score_color = (
            "#00ff88" if score >= 80 else ("#E8A33D" if score >= 50 else "#C0463C")
        )

        wh_bars = ""
        for wh in warehouses[:5]:
            qty = wh_totals.get(wh["id"], 0)
            pct = min(qty / max_wh * 100, 100)
            bar_color = (
                "#00ff88" if pct > 60 else ("#E8A33D" if pct > 30 else "#C0463C")
            )
            wh_bars += f"""
            <div style="margin-bottom:6px;">
                <div style="display:flex;justify-content:space-between;font-size:10px;color:#00ff8880;margin-bottom:2px;">
                    <span>{wh["code"]}</span><span>{qty:,}</span>
                </div>
                <div class="wr-bar-track">
                    <div class="wr-bar-fill" style="width:{pct}%;background:{bar_color};"></div>
                </div>
            </div>"""

        feed_lines = ""
        type_colors = {
            "inbound": "#00ff88",
            "outbound": "#E8A33D",
            "transfer": "#2563eb",
            "adjustment": "#9A9C9F",
        }
        for m in movements:
            mtype = m.get("movement_type", "?")
            color = type_colors.get(mtype, "#fff")
            ts = (m.get("created_at") or "")[:16].replace("T", " ")
            feed_lines += f"""
            <div class="wr-feed-line">
                <span style="color:{color};">[{mtype.upper()[:3]}]</span>
                <span style="color:#00ff8880;"> item#{m.get("item_id")} </span>
                <span style="color:#00ff88;">+{m.get("quantity")} units</span>
                <span style="color:#00ff8830;"> {ts}</span>
            </div>"""

        alert_lines = ""
        for a in (alerts.get("alerts") or [])[:5]:
            sev_color = "#C0463C" if a.get("severity") == "critical" else "#E8A33D"
            alert_lines += f"""
            <div style="font-size:10px;padding:3px 0;border-bottom:1px solid #ff000010;color:{sev_color};">
                {a.get("sku")} - {a.get("current_quantity")} left
            </div>"""

        if not alert_lines:
            alert_lines = '<div style="color:#00ff8840;font-size:11px;">All clear</div>'

        circ = 2 * 3.14159 * 40
        offset = circ * (1 - score / 100)
        now_str = datetime.datetime.now().strftime("%H:%M:%S")

        html = f"""
        <div class="wr-container">
            <button class="wr-exit" onclick="window.location.href='/dashboard'">EXIT WAR ROOM</button>

            <div class="wr-header">
                <div class="wr-title">STOCKLOOM WAR ROOM</div>
                <div style="display:flex;gap:24px;align-items:center;">
                    <span style="font-size:10px;color:#00ff8850;letter-spacing:0.1em;">LIVE OPERATIONS MONITOR</span>
                    <span class="wr-time" id="wr-clock">{now_str}</span>
                </div>
            </div>

            <div class="wr-grid">
                <div class="wr-panel">
                    <div class="wr-scanline"></div>
                    <div class="wr-corner tl"></div><div class="wr-corner tr"></div>
                    <div class="wr-corner bl"></div><div class="wr-corner br"></div>
                    <div class="wr-panel-title">System Health Score</div>
                    <div style="display:flex;align-items:center;gap:16px;">
                        <svg width="100" height="100" viewBox="0 0 100 100">
                            <circle cx="50" cy="50" r="40" fill="none" stroke="#00ff8810" stroke-width="8"/>
                            <circle cx="50" cy="50" r="40" fill="none" stroke="{score_color}" stroke-width="8"
                                stroke-dasharray="{circ:.2f}" stroke-dashoffset="{offset:.2f}"
                                stroke-linecap="round" transform="rotate(-90 50 50)"
                                class="wr-gauge-ring"/>
                            <text x="50" y="46" text-anchor="middle" font-size="22" font-weight="700"
                                fill="{score_color}" font-family="JetBrains Mono">{score}</text>
                            <text x="50" y="60" text-anchor="middle" font-size="8"
                                fill="#00ff8040" font-family="JetBrains Mono">HEALTH</text>
                        </svg>
                        <div>
                            <div style="font-size:11px;color:#00ff8880;margin-bottom:4px;">ITEMS: <span style="color:#00ff88">{summary["total_items"]}</span></div>
                            <div style="font-size:11px;color:#00ff8880;margin-bottom:4px;">UNITS: <span style="color:#00ff88">{summary["total_units"]:,}</span></div>
                            <div style="font-size:11px;color:#00ff8880;margin-bottom:4px;">VALUE: <span style="color:#E8A33D">${summary["total_inventory_value"]:,.0f}</span></div>
                            <div style="font-size:11px;color:#00ff8880;">LOW STOCK: <span style="color:#C0463C" class="wr-pulse">{summary["low_stock_count"]}</span></div>
                        </div>
                    </div>
                </div>

                <div class="wr-panel">
                    <div class="wr-scanline"></div>
                    <div class="wr-corner tl"></div><div class="wr-corner tr"></div>
                    <div class="wr-corner bl"></div><div class="wr-corner br"></div>
                    <div class="wr-panel-title">Warehouse Capacity</div>
                    {wh_bars}
                </div>

                <div class="wr-panel">
                    <div class="wr-scanline"></div>
                    <div class="wr-corner tl"></div><div class="wr-corner tr"></div>
                    <div class="wr-corner bl"></div><div class="wr-corner br"></div>
                    <div class="wr-panel-title" style="color:#C0463C80;">Active Alerts</div>
                    {alert_lines}
                </div>

                <div class="wr-panel" style="grid-column:span 2;">
                    <div class="wr-scanline"></div>
                    <div class="wr-corner tl"></div><div class="wr-corner tr"></div>
                    <div class="wr-corner bl"></div><div class="wr-corner br"></div>
                    <div class="wr-panel-title">Live Movement Feed</div>
                    <div class="wr-feed">{feed_lines}</div>
                </div>

                <div class="wr-panel">
                    <div class="wr-scanline"></div>
                    <div class="wr-corner tl"></div><div class="wr-corner tr"></div>
                    <div class="wr-corner bl"></div><div class="wr-corner br"></div>
                    <div class="wr-panel-title">Warehouses Online</div>
                    <div class="wr-stat">{len(warehouses)}</div>
                    <div class="wr-sub">nodes active</div>
                    <div style="height:12px;"></div>
                    <div class="wr-panel-title">Transfers Logged</div>
                    <div class="wr-stat amber">{pulse.get("recent_transfers", 0)}</div>
                    <div class="wr-sub">all time</div>
                </div>
            </div>
        </div>
        """
        container.content = html

    build()
    ui.timer(8.0, build)
