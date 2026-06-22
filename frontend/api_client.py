import os
import requests

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")


class ApiClient:
    @staticmethod
    def _raise_with_detail(resp):
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise RuntimeError(detail)

    @staticmethod
    def get(path: str, params: dict | None = None):
        resp = requests.get(f"{API_BASE}{path}", params=params, timeout=10)
        if not resp.ok:
            ApiClient._raise_with_detail(resp)
        return resp.json()

    @staticmethod
    def post(path: str, json: dict):
        resp = requests.post(f"{API_BASE}{path}", json=json, timeout=10)
        if not resp.ok:
            ApiClient._raise_with_detail(resp)
        return resp.json() if resp.content else None

    @staticmethod
    def put(path: str, json: dict):
        resp = requests.put(f"{API_BASE}{path}", json=json, timeout=10)
        if not resp.ok:
            ApiClient._raise_with_detail(resp)
        return resp.json() if resp.content else None

    @staticmethod
    def delete(path: str):
        resp = requests.delete(f"{API_BASE}{path}", timeout=10)
        if not resp.ok:
            ApiClient._raise_with_detail(resp)


api = ApiClient()
