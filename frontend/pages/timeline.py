import datetime
from nicegui import ui
from api_client import api
from auth_guard import require_login


def render_timeline():
    if not require_login():
        return

    ui.add_head_html('''
    <style>
    body { background: #0a0a0f !important; }
    .tl-container {
        position: fixed; inset: 0; background: #0a0a0f;
        font-family: "JetBrains Mono", monospace;
        display: flex; flex-direction: column; padding: 16px; gap: 12px;
        overflow: hidden; color: white;
    }
    .tl-header {
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #ffffff10; padding-bottom: 8px;
    }
    .tl-title { font-size: 16px; font-weight: 700; letter-spacing: 0.1em; color: #E8A33D; }
    .tl-exit {
        position: fixed; top: 12px; right: 16px; background: transparent;
        border: 1px solid #C0463C; color: #C0463C; padding: 4px 12px;
        border-radius: 4px; cursor: pointer; font-family: "JetBrains Mono", monospace;
        font-size: 11px; z-index: 9999;
    }
    .tl-exit:hover { background: #C0463C20; }
    .tl-track { flex: 1; overflow-y: auto; overflow-x: hidden; }
    .tl-row {
        display: flex; align-items: center; gap: 8px;
        padding: 4px 0; border-bottom: 1px solid #ffffff05;
        position: relative;
    }
    .tl-label {
        width: 140px; font-size: 9px; color: #ffffff50;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-shrink: 0;
    }
    .tl-bar-track {
        flex: 1; height: 18px; background: #ffffff05;
        border-radius: 3px; position: relative; overflow: hidden;
    }
    .tl-bar {
        height: 100%; border-radius: 3px; position: absolute;
        display: flex; align-items: center; padding: 0 6px;
        font-size: 8px; font-weight: 600; white-space: nowrap;
        overflow: hidden; transition: width 0.5s ease;
    }
    .tl-today-line {
        position: absolute; top: 0; bottom: 0; width: 1px;
        background: #E8A33D; z-index: 10; opacity: 0.6;
    }
    .tl-date-header {
        display: flex; gap: 0; margin-left: 148px;
        border-bottom: 1px solid #ffffff10; padding-bottom: 4px; margin-bottom: 4px;
    }
    .tl-date-tick {
        flex: 1; font-size: 8px; color: #ffffff20;
        text-align: center; border-left: 1px solid #ffffff08;
    }
    </style>
    ''')

    container = ui.html("")

    def build():
        try:
            movements = api.get("/stock-movements", params={"limit": 200})
            pos = api.get("/purchase-orders")
            forecast = api.get("/forecasting/stockout-risk")
            api.get("/items", params={"limit": 50})
        except Exception as e:
            container.content = f'<div style="color:red;padding:20px;">Error: {e}</div>'
            return

        now = datetime.datetime.now()
        window_start = now - datetime.timedelta(days=14)
        window_end = now + datetime.timedelta(days=14)

        def day_pct(dt_str, fmt="%Y-%m-%dT%H:%M:%S"):
            try:
                if not dt_str:
                    return None
                dt_str_clean = dt_str[:19]
                dt = datetime.datetime.strptime(dt_str_clean, fmt)
                delta = (dt - window_start).total_seconds()
                total = (window_end - window_start).total_seconds()
                return max(0, min(100, delta / total * 100))
            except Exception:
                return None

        # Date header
        date_ticks = ""
        for i in range(0, 29, 4):
            d = window_start + datetime.timedelta(days=i)
            date_ticks += f'<div class="tl-date-tick">{d.strftime("%d %b")}</div>'

        today_pct = (now - window_start).total_seconds() / (window_end - window_start).total_seconds() * 100

        rows_html = ""

        # Section 1: Recent Movements
        rows_html += '''
        <div style="font-size:9px;color:#E8A33D;letter-spacing:0.1em;padding:8px 0 4px 0;
            border-bottom:1px solid #E8A33D20;">STOCK MOVEMENTS (last 14 days)</div>
        '''
        type_colors = {
            "inbound": "#2F6F6B",
            "outbound": "#E8A33D",
            "transfer": "#2563eb",
            "adjustment": "#9A9C9F",
        }
        for m in movements[:20]:
            pct = day_pct(m.get("created_at", ""))
            if pct is None or pct > 100:
                continue
            mtype = m.get("movement_type", "?")
            color = type_colors.get(mtype, "#fff")
            width = max(3, min(8, m.get("quantity", 1) / 50))
            item_id = m.get("item_id", "?")
            label = f"#{item_id} {mtype[:3].upper()}"
            rows_html += f'''
            <div class="tl-row">
                <div class="tl-label">{label} +{m.get("quantity")} u</div>
                <div class="tl-bar-track">
                    <div class="tl-today-line" style="left:{today_pct:.1f}%;"></div>
                    <div class="tl-bar" style="left:{pct:.1f}%;width:{width}%;
                        background:{color}30;border-left:2px solid {color};">
                    </div>
                </div>
            </div>'''

        # Section 2: Purchase Orders
        rows_html += '''
        <div style="font-size:9px;color:#2563eb;letter-spacing:0.1em;padding:8px 0 4px 0;
            border-bottom:1px solid #2563eb20;margin-top:8px;">PURCHASE ORDERS</div>
        '''
        po_colors = {
            "draft": "#9A9C9F",
            "ordered": "#2563eb",
            "received": "#2F6F6B",
            "cancelled": "#C0463C",
        }
        for po in pos[:15]:
            pct = day_pct(po.get("created_at", ""))
            if pct is None:
                pct = 50
            status = po.get("status", "draft")
            color = po_colors.get(status, "#fff")
            label = po.get("po_number", "PO")
            rows_html += f'''
            <div class="tl-row">
                <div class="tl-label">{label}</div>
                <div class="tl-bar-track">
                    <div class="tl-today-line" style="left:{today_pct:.1f}%;"></div>
                    <div class="tl-bar" style="left:{pct:.1f}%;width:12%;
                        background:{color}20;border-left:2px solid {color};">
                        <span style="color:{color};">{status.upper()}</span>
                    </div>
                </div>
            </div>'''

        # Section 3: Stockout Predictions
        rows_html += '''
        <div style="font-size:9px;color:#C0463C;letter-spacing:0.1em;padding:8px 0 4px 0;
            border-bottom:1px solid #C0463C20;margin-top:8px;">PREDICTED STOCKOUTS (next 14 days)</div>
        '''
        at_risk = [f for f in forecast if f.get("risk") in ("critical", "warning") and f.get("days_until_stockout")]
        for f in sorted(at_risk, key=lambda x: x["days_until_stockout"])[:15]:
            days = f["days_until_stockout"]
            stockout_dt = now + datetime.timedelta(days=days)
            pct = (stockout_dt - window_start).total_seconds() / (window_end - window_start).total_seconds() * 100
            if pct < 0 or pct > 100:
                continue
            color = "#C0463C" if f["risk"] == "critical" else "#E8A33D"
            rows_html += f'''
            <div class="tl-row">
                <div class="tl-label" style="color:{color};">{f["sku"]}</div>
                <div class="tl-bar-track">
                    <div class="tl-today-line" style="left:{today_pct:.1f}%;"></div>
                    <div class="tl-bar" style="left:{pct:.1f}%;width:2%;
                        background:{color}; border-radius:50%; width:14px; height:14px;">
                    </div>
                    <div style="position:absolute;left:{pct:.1f}%;top:0;
                        font-size:8px;color:{color};padding-left:18px;line-height:18px;white-space:nowrap;">
                        {f["sku"]} out in {days:.0f}d
                    </div>
                </div>
            </div>'''

        if not at_risk:
            rows_html += '<div style="font-size:10px;color:#2F6F6B;padding:6px 0;">No predicted stockouts in the next 14 days</div>'

        now_str = datetime.datetime.now().strftime("%H:%M:%S")

        html = f'''
        <div class="tl-container">
            <button class="tl-exit" onclick="window.location.href='/dashboard'">EXIT TIMELINE</button>
            <div class="tl-header">
                <div class="tl-title">SUPPLY CHAIN TIMELINE</div>
                <div style="font-size:9px;color:#ffffff30;letter-spacing:0.08em;">
                    14d PAST — TODAY — 14d FUTURE &nbsp;|&nbsp; {now_str}
                </div>
            </div>
            <div class="tl-date-header">{date_ticks}</div>
            <div class="tl-track">{rows_html}</div>
        </div>
        '''
        container.content = html

    build()
    ui.timer(12.0, build)