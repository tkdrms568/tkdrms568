from fastapi.testclient import TestClient

from app import app, reset_database, SESSIONS

client = TestClient(app)


def login(username: str, password: str):
    response = client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return response.cookies.get("session_id")


def setup_function():
    reset_database()
    SESSIONS.clear()


def test_sql_injection_lab_difference():
    vulnerable = client.get("/vuln/search", params={"q": "' OR 1=1 --"})
    assert vulnerable.status_code == 200
    assert vulnerable.json()["count"] >= 3

    secure = client.get("/secure/search", params={"q": "' OR 1=1 --"})
    assert secure.status_code == 200
    assert secure.json()["count"] == 0


def test_idor_lab_difference():
    session_id = login("alice", "alice123!")
    cookies = {"session_id": session_id}

    vulnerable = client.get("/vuln/profile/3", cookies=cookies)
    assert vulnerable.status_code == 200
    assert vulnerable.json()["profile"]["username"] == "bob"

    secure = client.get("/secure/profile/3", cookies=cookies)
    assert secure.status_code == 403


def test_order_bola_difference():
    session_id = login("alice", "alice123!")
    cookies = {"session_id": session_id}

    vulnerable = client.get("/api/vuln/orders/102", cookies=cookies)
    assert vulnerable.status_code == 200
    assert vulnerable.json()["order"]["user_id"] == 3

    secure = client.get("/api/secure/orders/102", cookies=cookies)
    assert secure.status_code == 403


def test_debug_data_is_only_on_vulnerable_endpoint():
    vulnerable = client.get("/vuln/debug")
    assert vulnerable.status_code == 200
    assert vulnerable.json()["demo_internal_key"] == "LAB-DEMO-SECRET-2026"

    secure = client.get("/secure/status")
    assert secure.status_code == 200
    assert "demo_internal_key" not in secure.json()
