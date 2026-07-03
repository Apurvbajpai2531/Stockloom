from nicegui import ui

from pages.login import render_login
from pages.welcome import render_welcome
from pages.dashboard import render_dashboard
from pages.items import render_items
from pages.warehouses import render_warehouses
from pages.movements import render_movements
from pages.categories import render_categories
from pages.purchase_orders import render_purchase_orders
from pages.reports import render_reports
from pages.item_detail import render_item_detail
from pages.audit_log import render_audit_log
from pages.settings import render_settings
from pages.reorder_suggestions import render_reorder_suggestions
from pages.forecasting import render_forecasting
from pages.rebalancing import render_rebalancing
from pages.network import render_network
from pages.insights import render_insights
from pages.analytics import render_analytics
from pages.command_center import render_command_center
from pages.warroom import render_warroom
from pages.dna import render_dna
from pages.timeline import render_timeline
from pages.supplier_intelligence import render_supplier_intelligence
from pages.rules import render_rules
from pages.reservations import render_reservations
from pages.cycle_count import render_cycle_count
from pages.cost_analysis import render_cost_analysis



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
                 /* Professional hover polish */
.q-card { cursor: default; }
.q-card.cursor-pointer:hover {
    border-color: var(--amber) !important;
    transform: translateY(-2px);
}

.q-tr:hover { background: rgba(232,163,61,0.06) !important; cursor: pointer; }

.q-btn { position: relative; overflow: hidden; }
.q-btn:active { transform: scale(0.97); }

a, .q-item { transition: background-color 0.15s ease, transform 0.15s ease; }

.q-table tbody tr { transition: background-color 0.15s ease; }

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: var(--line); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--amber); }

.q-field:focus-within .q-field__control { border-color: var(--amber) !important; }
}
</style>
""")


@ui.page("/")
def login_page():
    render_login()


@ui.page("/welcome")
def welcome_page():
    render_welcome()


@ui.page("/dashboard")
def dashboard_page():
    render_dashboard()


@ui.page("/items")
def items():
    render_items()

@ui.page("/items/{item_id}")
def item_detail_page(item_id: int):
    render_item_detail(item_id)


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

@ui.page("/audit-log")
def audit_log_page():
    render_audit_log()


@ui.page("/settings")
def settings_page():
    render_settings()

@ui.page("/reorder-suggestions")
def reorder_suggestions_page():
    render_reorder_suggestions()    


@ui.page("/forecasting")
def forecasting_page():
    render_forecasting()

@ui.page("/rebalancing")
def rebalancing_page():
    render_rebalancing()

@ui.page("/network")
def network_page():
    render_network()


@ui.page("/insights")
def insights_page():
    render_insights()

@ui.page("/analytics")
def analytics_page():
    render_analytics()



@ui.page("/command-center")
def command_center_page():
    render_command_center()


@ui.page("/warroom")
def warroom_page():
    render_warroom()


@ui.page("/dna")
def dna_page():
    render_dna()


@ui.page("/timeline")
def timeline_page():
    render_timeline()


@ui.page("/supplier-intelligence")
def supplier_intelligence_page():
    render_supplier_intelligence()


@ui.page("/rules")
def rules_page():
    render_rules()


@ui.page("/reservations")
def reservations_page():
    render_reservations()


@ui.page("/cycle-count")
def cycle_count_page():
    render_cycle_count()


@ui.page("/cost-analysis")
def cost_analysis_page():
    render_cost_analysis()
    

ui.run(
    title="StockLoom",
    host="0.0.0.0",
    port=8081,
)