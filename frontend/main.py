from nicegui import ui

from pages.dashboard import render_dashboard
from pages.items import render_items
from pages.warehouses import render_warehouses
from pages.movements import render_movements
from pages.categories import render_categories

dark = ui.dark_mode()

ui.add_css('''
* { transition: background-color 0.25s ease, color 0.25s ease, border-color 0.25s ease; }
.q-card { transition: transform 0.2s ease, box-shadow 0.2s ease; }
.q-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.12); }
.q-btn { transition: transform 0.15s ease; }
.q-btn:hover { transform: scale(1.04); }
@media (max-width: 768px) {
    .nav-links { flex-wrap: wrap; gap: 8px !important; }
}
''')

@ui.page("/")
def index_page():
    render_dashboard()


@ui.page("/items")
def items_page():
    render_items()


@ui.page("/warehouses")
def warehouses_page():
    render_warehouses()


@ui.page("/movements")
def movements_page():
    render_movements()


@ui.page("/categories")
def categories_page():
    render_categories()


ui.run(title="StockLoom", host="0.0.0.0", port=8081, reload=False)


