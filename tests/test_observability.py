"""Homework 2 authentication tests. Offline: no Langfuse, Docker, or model key."""

from __future__ import annotations

import base64
import json

from fastapi.testclient import TestClient

from server import app as server_app

client = TestClient(server_app.app)  # no `with`, so the lifespan (tracing setup) never runs


def _session(user_id: int, role: str) -> dict:
    response = client.post("/sessions", json={"user_id": user_id, "role": role})
    assert response.status_code == 200
    return response.json()


def test_create_session_rejects_role_mismatch(world: dict) -> None:
    server_app._SESSIONS.clear()
    response = client.post("/sessions", json={"user_id": 1, "role": "support"})
    assert response.status_code == 403
    assert server_app._SESSIONS == {}


def test_token_cannot_authorize_another_session(world: dict) -> None:
    a = _session(1, "shopper")
    b = _session(2, "shopper")
    response = client.post(
        f"/sessions/{b['session_id']}/messages",
        headers={"Authorization": f"Bearer {a['token']}"},
        json={"message": "Show my recent orders."},
    )
    assert response.status_code == 403


def test_tampered_token_is_rejected(world: dict) -> None:
    a = _session(1, "shopper")
    body, sig = a["token"].rsplit(".", 1)
    payload = json.loads(base64.urlsafe_b64decode(body))
    payload["role"] = "support"
    forged = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True).encode()).decode()
    response = client.post(
        f"/sessions/{a['session_id']}/messages",
        headers={"Authorization": f"Bearer {forged}.{sig}"},
        json={"message": "Show all orders."},
    )
    assert response.status_code == 401
