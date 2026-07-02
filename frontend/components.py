from nicegui import ui


def render_header(active: str = ""):
    from api_client import get_token, API_BASE
    token = get_token() or ""
    ui.run_javascript(f"window.__stockloom_token = '{token}'; window.__API_BASE__ = '{API_BASE}';")
    _add_command_palette()
    _add_assistant_widget()
    drawer = ui.left_drawer(value=True).classes("p-0").style(
        "background:#1C2230; width:230px; border-right:3px solid #E8A33D;"
    )
    with drawer:
        with ui.column().classes("w-full p-4 gap-1"):
            with ui.row().classes("items-center gap-2 mb-6"):
                ui.icon("warehouse").style("color:#E8A33D").classes("text-3xl")
                ui.label("STOCKLOOM").classes("text-lg font-bold text-white tracking-wide")

            _nav_link("Dashboard", "/dashboard", "dashboard", active)
            _nav_link("Items", "/items", "inventory_2", active)
            _nav_link("Warehouses", "/warehouses", "store", active)
            _nav_link("Stock Movements", "/movements", "sync_alt", active)
            _nav_link("Categories", "/categories", "category", active)
            _nav_link("Purchase Orders", "/purchase-orders", "shopping_cart", active)
            _nav_link("Reports", "/reports", "description", active)
            _nav_link("Audit Log", "/audit-log", "history", active)
            _nav_link("Settings", "/settings", "settings", active)
            _nav_link("Reorder Suggestions", "/reorder-suggestions", "shopping_bag", active)
            _nav_link("Forecasting", "/forecasting", "insights", active)
            _nav_link("Rebalancing", "/rebalancing", "swap_horiz", active)
            _nav_link("Network View", "/network", "hub", active)
            _nav_link("Smart Insights", "/insights", "auto_awesome", active)
            _nav_link("Analytics", "/analytics", "bar_chart", active)
            _nav_link("Command Center", "/command-center", "radar", active)
            _nav_link("War Room", "/warroom", "emergency", active)
            _nav_link("Inventory DNA", "/dna", "biotech", active)
            _nav_link("Supply Chain Timeline", "/timeline", "timeline", active)
            _nav_link("Supplier Intelligence", "/supplier-intelligence", "store", active)
            _nav_link("Alert Rules", "/rules", "rule", active)


            ui.element("div").classes("flex-grow")

            with ui.row().classes("items-center gap-2 mt-6 px-2"):
                dark = ui.dark_mode()
                icon_btn = ui.button(icon="dark_mode", on_click=lambda: toggle_dark()).props("flat round color=white")
                ui.label("Theme").classes("text-white text-sm")

                def toggle_dark():
                    dark.toggle()
                    icon_btn.props(f"icon={'light_mode' if dark.value else 'dark_mode'}")

            from api_client import clear_token

            def logout():
                clear_token()
                ui.navigate.to("/")

            with ui.row().classes("items-center gap-2 px-2 mt-1"):
                ui.button("Logout", icon="logout", on_click=logout).props("flat color=white").classes("text-sm")

    with ui.header().classes("px-4 py-3 items-center justify-between").style(
        "background:#1C2230; border-bottom:3px solid #E8A33D;"
    ):
        

        with ui.row().classes("items-center gap-3"):
            ui.button(icon="menu", on_click=drawer.toggle).props("flat round color=white").classes("md:hidden")
            ui.label("StockLoom Operations").classes("text-white font-semibold")
            ui.label("⌘K / Ctrl+K for quick nav").classes("text-xs hidden md:block").style("color:#9A9C9F;")
            with ui.row().classes("items-center gap-2"):
                search_box = ui.input(placeholder="Search items by SKU or name...").props("dense standout").classes("w-64").style(
                "background: rgba(255,255,255,0.1); border-radius: 8px; --q-field-text-color: white;"
            )

            async def do_search():
                if not search_box.value or not search_box.value.strip():
                    return
                from api_client import api
                try:
                    results = api.get("/items", params={"search": search_box.value.strip(), "limit": 5})
                    if results:
                        ui.navigate.to(f"/items/{results[0]['id']}")
                    else:
                        ui.notify("No matching item found", type="warning")
                except Exception:
                    ui.notify("Search failed", type="negative")

            search_box.on("keydown.enter", lambda e: do_search())
            ui.button(icon="search", on_click=do_search).props("flat round color=white")

            from api_client import api as _api
            bell_btn = ui.button(icon="notifications", on_click=lambda: open_notifications()).props("flat round color=white")

            def open_notifications():
                with ui.dialog() as dialog, ui.card().classes("w-96"):
                    ui.label("Notifications").classes("text-lg font-bold")
                    try:
                        notifs = _api.get("/notifications", params={"unread_only": True})
                    except Exception:
                        notifs = []
                    if not notifs:
                        ui.label("No new notifications").style("color:var(--ink-soft)")
                    for n in notifs:
                        color = "#C0463C" if n["severity"] == "critical" else "#E8A33D"
                        with ui.row().classes("items-start gap-2 w-full py-2").style("border-bottom:1px solid var(--line);"):
                            ui.icon("circle").style(f"color:{color}; font-size:10px; margin-top:4px;")
                            with ui.column().classes("flex-grow"):
                                ui.label(n["title"]).classes("font-semibold text-sm")
                                ui.label(n["message"]).classes("text-xs").style("color:var(--ink-soft)")
                    ui.button("Close", on_click=dialog.close).classes("mt-2")
                dialog.open()


def _nav_link(label: str, target: str, icon: str, active: str):
    is_active = active == label
    bg = "background: rgba(232,163,61,0.15); border-left: 3px solid #E8A33D;" if is_active else "border-left: 3px solid transparent;"
    with ui.link(target=target).classes("no-underline w-full"):
        with ui.row().classes("items-center gap-3 px-3 py-2 cursor-pointer text-white hover:bg-white/5 rounded-r-lg w-full").style(bg):
            ui.icon(icon).classes("text-lg")
            ui.label(label).classes("text-sm font-medium")


def _add_command_palette():
    ui.add_body_html('''
    <style>
    #cmdk-overlay {
        position: fixed; inset: 0; background: rgba(0,0,0,0.5);
        display: none; align-items: flex-start; justify-content: center;
        padding-top: 12vh; z-index: 9999;
    }
    #cmdk-box {
        background: #1C2230; border: 1px solid #E8A33D; border-radius: 12px;
        width: 480px; max-width: 90vw; box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        font-family: 'Inter', sans-serif;
    }
    #cmdk-input {
        width: 100%; padding: 16px; background: transparent; border: none;
        color: white; font-size: 16px; outline: none; border-bottom: 1px solid #2A2D35;
    }
    #cmdk-list { max-height: 320px; overflow-y: auto; padding: 8px; }
    .cmdk-item {
        padding: 10px 12px; border-radius: 8px; color: #ECE9E1; cursor: pointer;
        display: flex; align-items: center; gap: 10px; font-size: 14px;
    }
    .cmdk-item:hover, .cmdk-item.active { background: rgba(232,163,61,0.15); }
    .cmdk-hint { color: #5B6275; font-size: 11px; padding: 8px 16px; border-top: 1px solid #2A2D35; }
    </style>
    <div id="cmdk-overlay">
        <div id="cmdk-box">
            <input id="cmdk-input" placeholder="Type a command or search... (try: items, dashboard, reports)" />
            <div id="cmdk-list"></div>
            <div class="cmdk-hint">↑↓ to navigate · Enter to select · Esc to close</div>
        </div>
    </div>
    <script>
    (function() {
        const commands = [
            {label: "Go to Dashboard", icon: "📊", url: "/dashboard"},
            {label: "Go to Items", icon: "📦", url: "/items"},
            {label: "Go to Warehouses", icon: "🏬", url: "/warehouses"},
            {label: "Go to Stock Movements", icon: "🔄", url: "/movements"},
            {label: "Go to Categories", icon: "🏷️", url: "/categories"},
            {label: "Go to Purchase Orders", icon: "🛒", url: "/purchase-orders"},
            {label: "Go to Reports", icon: "📄", url: "/reports"},
            {label: "Go to Audit Log", icon: "📜", url: "/audit-log"},
            {label: "Go to Reorder Suggestions", icon: "🛍️", url: "/reorder-suggestions"},
            {label: "Go to Forecasting", icon: "📈", url: "/forecasting"},
            {label: "Go to Rebalancing", icon: "↔️", url: "/rebalancing"},
        ];

        let filtered = commands;
        let activeIndex = 0;

        const overlay = document.getElementById('cmdk-overlay');
        const input = document.getElementById('cmdk-input');
        const list = document.getElementById('cmdk-list');

        function render() {
            list.innerHTML = '';
            filtered.forEach((cmd, i) => {
                const div = document.createElement('div');
                div.className = 'cmdk-item' + (i === activeIndex ? ' active' : '');
                div.innerHTML = `<span>${cmd.icon}</span><span>${cmd.label}</span>`;
                div.onclick = () => { window.location.href = cmd.url; };
                list.appendChild(div);
            });
        }

        function open() {
            overlay.style.display = 'flex';
            input.value = '';
            filtered = commands;
            activeIndex = 0;
            render();
            setTimeout(() => input.focus(), 50);
        }

        function close() {
            overlay.style.display = 'none';
        }

        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                if (overlay.style.display === 'flex') { close(); } else { open(); }
            }
            if (e.key === 'Escape') close();
        });

        input.addEventListener('input', () => {
            const q = input.value.toLowerCase();
            filtered = commands.filter(c => c.label.toLowerCase().includes(q));
            activeIndex = 0;
            render();
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown') { activeIndex = Math.min(activeIndex + 1, filtered.length - 1); render(); e.preventDefault(); }
            if (e.key === 'ArrowUp') { activeIndex = Math.max(activeIndex - 1, 0); render(); e.preventDefault(); }
            if (e.key === 'Enter' && filtered[activeIndex]) { window.location.href = filtered[activeIndex].url; }
        });

        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
    })();
    </script>
                     
    ''')

ui.add_head_html("""
<style>
.q-field__native,
.q-field__input {
    color: white !important;
}

.q-field__label {
    color: rgba(255,255,255,0.7) !important;
}
</style>
""")

def _add_assistant_widget():
    ui.add_body_html('''
    <style>
#assistant-fab {
        position: fixed; bottom: 24px; right: 24px; width: 56px; height: 56px;
        border-radius: 50%; background: #1C2230; border: 1.5px solid #E8A33D;
        display: flex; align-items: center; justify-content: center; cursor: pointer;
        z-index: 9998; box-shadow: 0 4px 14px rgba(0,0,0,0.25);
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }
    #assistant-fab:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(232,163,61,0.3);
    }
    #assistant-fab .material-icons {
        font-size: 26px; color: #E8A33D;
    }
    #assistant-panel {
        position: fixed; bottom: 92px; right: 24px; width: 340px; max-height: 460px;
        background: #1C2230; border: 1px solid #E8A33D; border-radius: 14px;
        display: none; flex-direction: column; z-index: 9998; overflow: hidden;
        box-shadow: 0 12px 40px rgba(0,0,0,0.4);
    }
    #assistant-header {
        padding: 12px 16px; background: #14161C; color: white; font-weight: 600;
        font-family: 'Space Grotesk', sans-serif; display: flex; justify-content: space-between; align-items: center;
    }
    #assistant-messages { flex-grow: 1; overflow-y: auto; padding: 12px; max-height: 320px; }
    .asst-msg { margin-bottom: 10px; font-size: 13px; line-height: 1.4; }
    .asst-msg.user { color: #E8A33D; text-align: right; }
    .asst-msg.bot { color: #ECE9E1; }
    .asst-msg .item-line { color: #9A9C9F; padding-left: 8px; }
    #assistant-input-row { display: flex; padding: 10px; border-top: 1px solid #2A2D35; }
    #assistant-input {
        flex-grow: 1; background: #0F1116; border: 1px solid #2A2D35; border-radius: 8px;
        padding: 8px 10px; color: white; outline: none; font-size: 13px;
    }
    </style>
   <div id="assistant-fab"><span class="material-icons">forum</span></div>
    <div id="assistant-panel">
        <div id="assistant-header">
            <span>StockLoom Assistant</span>
            <span id="assistant-close" style="cursor:pointer;">✕</span>
        </div>
        <div id="assistant-messages">
            <div class="asst-msg bot">Hi! Ask me about stock levels, low stock items, or inventory value.</div>
        </div>
        <div id="assistant-input-row">
            <input id="assistant-input" placeholder="Ask something..." />
        </div>
    </div>
    <script>
    (function() {
        const fab = document.getElementById('assistant-fab');
        const panel = document.getElementById('assistant-panel');
        const closeBtn = document.getElementById('assistant-close');
        const input = document.getElementById('assistant-input');
        const messages = document.getElementById('assistant-messages');

        fab.onclick = () => { panel.style.display = panel.style.display === 'flex' ? 'none' : 'flex'; };
        closeBtn.onclick = () => { panel.style.display = 'none'; };

        function addMsg(text, cls) {
            const div = document.createElement('div');
            div.className = 'asst-msg ' + cls;
            div.textContent = text;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }

        function addList(items) {
            items.forEach(it => {
                const div = document.createElement('div');
                div.className = 'asst-msg bot item-line';
                div.textContent = '• ' + it;
                messages.appendChild(div);
            });
            messages.scrollTop = messages.scrollHeight;
        }

        async function ask() {
            const q = input.value.trim();
            if (!q) return;
            addMsg(q, 'user');
            input.value = '';

            const token = window.__stockloom_token || '';
            try {
                const resp = await fetch((window.__API_BASE__ || 'http://localhost:8000/api') + '/assistant/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
                    body: JSON.stringify({ query: q })
                });
                const data = await resp.json();
                addMsg(data.answer, 'bot');
                if (data.list) addList(data.list);
            } catch (e) {
                addMsg("Sorry, I couldn't reach the server.", 'bot');
            }
        }

        input.addEventListener('keydown', (e) => { if (e.key === 'Enter') ask(); });
    })();
    </script>
    ''')