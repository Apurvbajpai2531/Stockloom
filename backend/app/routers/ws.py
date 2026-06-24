from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

active_connections: list[WebSocket] = []


@router.websocket("/ws/stock-updates")
async def stock_updates_ws(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive ping from client
    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def broadcast_stock_update(message: dict):
    """Call this after any stock-changing operation to push live updates to all connected clients."""
    import json
    dead = []
    for conn in active_connections:
        try:
            await conn.send_text(json.dumps(message))
        except Exception:
            dead.append(conn)
    for d in dead:
        active_connections.remove(d)
