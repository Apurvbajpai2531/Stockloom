from nicegui import ui

from api_client import get_token


def require_login():
    """Call at the top of every protected page. Redirects to login if not authenticated."""
    if not get_token():
        ui.navigate.to("/")
        return False
    return True
