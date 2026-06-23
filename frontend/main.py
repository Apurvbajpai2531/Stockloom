from nicegui import ui

from pages.welcome import render_welcome
from pages.dashboard import render_dashboard
from pages.items import render_items
from pages.warehouses import render_warehouses
from pages.movements import render_movements
from pages.categories import render_categories
from pages.purchase_orders import render_purchase_orders
from pages.reports import render_reports


ui.dark_mode(False)


ui.add_head_html("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">

<style>

:root{
--paper:#F6F4EF;
--ink:#1C2230;
--ink-soft:#5B6275;
--amber:#E8A33D;
--teal:#2F6F6B;
--red:#C0463C;
--line:#E2DED3;
}

body.body--dark{
--paper:#14161C;
--ink:#ECE9E1;
--ink-soft:#9A9C9F;
--line:#2A2D35;
}

body{
background:var(--paper)!important;
color:var(--ink);
font-family:'Inter',sans-serif;
}

.page-title,
h1,
h2,
.text-2xl,
.text-xl{
font-family:'Space Grotesk',sans-serif!important;
}

.q-card{
background:white!important;
border:1px solid var(--line)!important;
border-radius:10px!important;
box-shadow:none!important;
}

body.body--dark .q-card{
background:#1B1E26!important;
}

.q-header{
background:var(--ink)!important;
border-bottom:3px solid var(--amber);
}

.page-container{
max-width:1200px;
margin:auto;
width:100%;
}

.gauge-track{
height:6px;
background:var(--line);
overflow:hidden;
border-radius:3px;
}

.gauge-fill{
height:100%;
}

.gauge-ok{
background:var(--teal);
}

.gauge-low{
background:var(--red);
}

.q-badge{
font-family:'JetBrains Mono', monospace;
font-weight:600;
padding:4px 8px;
border-radius:6px;
}

@media (max-width:768px){

.stats-row,
.chart-row,
.form-row{
flex-direction:column!important;
}

.stats-row > div,
.form-row > div{
width:100%!important;
}

}

</style>
""")


@ui.page("/")
def welcome_page():
    render_welcome()


@ui.page("/dashboard")
def dashboard_page():
    render_dashboard()


@ui.page("/items")
def items():
    render_items()


@ui.page("/warehouses")
def warehouses():
    render_warehouses()


@ui.page("/movements")
def movements():
    render_movements()


@ui.page("/categories")
def categories():
    render_categories()


@ui.page("/purchase-orders")
def purchase_orders_page():
    render_purchase_orders()


@ui.page("/reports")
def reports_page():
    render_reports()


ui.run(
    title="StockLoom",
    host="0.0.0.0",
    port=8081,
)