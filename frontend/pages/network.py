from nicegui import ui

from api_client import api
from components import render_header
from auth_guard import require_login


def render_network():
    if not require_login():
        return

    render_header(active="Network")

    with ui.column().classes("w-full p-4 md:p-6 gap-4 page-container"):
        ui.label("Live Stock Flow Network").classes("text-2xl font-bold page-title")
        ui.label("Warehouses and transfer activity between them").classes(
            "text-sm"
        ).style("color:var(--ink-soft)")

        try:
            data = api.get("/network/flow-graph")
        except Exception as e:
            ui.label(f"Failed to load network: {e}").classes("text-red-600")
            return

        nodes = data["nodes"]
        edges = data["edges"]

        if not nodes:
            ui.label("No warehouses to display.").style("color:var(--ink-soft)")
            return

        graph_html = _build_network_svg(nodes, edges)
        ui.html(graph_html).classes("w-full")


def _build_network_svg(nodes, edges):
    import math

    n = len(nodes)
    cx, cy, radius = 400, 280, 200
    positions = {}
    for i, node in enumerate(nodes):
        angle = (2 * math.pi * i / n) - math.pi / 2
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        positions[node["id"]] = (x, y)

    max_stock = max((node["total_stock"] for node in nodes), default=1) or 1

    edge_svgs = []
    particle_svgs = []
    for idx, edge in enumerate(edges):
        if edge["from"] not in positions or edge["to"] not in positions:
            continue
        x1, y1 = positions[edge["from"]]
        x2, y2 = positions[edge["to"]]
        width = min(1 + edge["transfer_count"] * 0.8, 8)
        edge_svgs.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#E8A33D" stroke-width="{width}" opacity="0.35" />'
        )
        dur = max(2, 6 - edge["transfer_count"])
        particle_svgs.append(
            f"""
        <circle r="5" fill="#E8A33D">
            <animateMotion dur="{dur}s" repeatCount="indefinite"
                path="M{x1},{y1} L{x2},{y2}" />
        </circle>
        """
        )

    node_svgs = []
    for node in nodes:
        x, y = positions[node["id"]]
        size = 28 + (node["total_stock"] / max_stock) * 32
        node_svgs.append(
            f"""
        <g class="net-node" style="cursor:pointer;">
            <circle cx="{x}" cy="{y}" r="{size}" fill="#1C2230" stroke="#E8A33D" stroke-width="2"
                class="net-circle" />
            <text x="{x}" y="{y-2}" text-anchor="middle" fill="white" font-size="12" font-weight="600"
                font-family="Space Grotesk, sans-serif">{node["code"]}</text>
            <text x="{x}" y="{y+14}" text-anchor="middle" fill="#E8A33D" font-size="10"
                font-family="JetBrains Mono, monospace">{node["total_stock"]} units</text>
            <title>{node["name"]} — {node["total_stock"]} units in stock</title>
        </g>
        """
        )

    svg = f"""
    <div style="width:100%; border-radius:16px; overflow:hidden; position:relative;
        background: radial-gradient(circle at 50% 30%, #232A3D 0%, #14161C 80%);">
        <style>
            .net-circle {{ transition: r 0.3s ease, fill 0.3s ease; }}
            .net-node:hover .net-circle {{ fill: #E8A33D; stroke: white; }}
            .net-grid-line {{ stroke: rgba(232,163,61,0.05); }}
        </style>
        <svg viewBox="0 0 800 560" style="width:100%; height:auto; display:block;">
            <defs>
                <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" class="net-grid-line" stroke-width="1"/>
                </pattern>
            </defs>
            <rect width="800" height="560" fill="url(#grid)" />
            {''.join(edge_svgs)}
            {''.join(particle_svgs)}
            {''.join(node_svgs)}
        </svg>
    </div>
    """
    return svg
