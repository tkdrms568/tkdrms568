from fastapi.testclient import TestClient

from app import SESSIONS, app, reset_database

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


# ---------------------------------------------------------------------------
# Advanced authorization / business-logic case study
# ---------------------------------------------------------------------------


def test_employee_cross_department_object_access():
    session_id = login("alice", "alice123!")
    cookies = {"session_id": session_id}

    vulnerable = client.get("/api/v2/vuln/expenses/203", cookies=cookies)
    assert vulnerable.status_code == 200
    assert vulnerable.json()["expense"]["department"] == "B"

    secure = client.get("/api/v2/secure/expenses/203", cookies=cookies)
    assert secure.status_code == 403


def test_employee_can_skip_workflow_only_in_vulnerable_endpoint():
    session_id = login("alice", "alice123!")
    cookies = {"session_id": session_id}

    vulnerable = client.post(
        "/api/v2/vuln/expenses/201/transition",
        json={"status": "approved"},
        cookies=cookies,
    )
    assert vulnerable.status_code == 200
    assert vulnerable.json()["expense"]["status"] == "approved"

    reset_database()
    SESSIONS.clear()
    session_id = login("alice", "alice123!")
    cookies = {"session_id": session_id}

    secure = client.post("/api/v2/secure/expenses/201/submit", cookies=cookies)
    assert secure.status_code == 200
    assert secure.json()["expense"]["status"] == "submitted"


def test_manager_cross_department_approval_is_blocked_in_secure_flow():
    session_id = login("manager_a", "managerA123!")
    cookies = {"session_id": session_id}

    vulnerable = client.post("/api/v2/vuln/expenses/203/approve", cookies=cookies)
    assert vulnerable.status_code == 200
    assert vulnerable.json()["expense"]["status"] == "approved"

    reset_database()
    SESSIONS.clear()
    session_id = login("manager_a", "managerA123!")
    cookies = {"session_id": session_id}

    secure = client.post("/api/v2/secure/expenses/203/approve", cookies=cookies)
    assert secure.status_code == 403


def test_manager_self_approval_is_blocked_in_secure_flow():
    session_id = login("manager_a", "managerA123!")
    cookies = {"session_id": session_id}

    vulnerable = client.post("/api/v2/vuln/expenses/204/approve", cookies=cookies)
    assert vulnerable.status_code == 200
    assert vulnerable.json()["expense"]["status"] == "approved"

    reset_database()
    SESSIONS.clear()
    session_id = login("manager_a", "managerA123!")
    cookies = {"session_id": session_id}

    secure = client.post("/api/v2/secure/expenses/204/approve", cookies=cookies)
    assert secure.status_code == 403


def test_same_department_manager_can_approve_submitted_expense():
    session_id = login("manager_a", "managerA123!")
    cookies = {"session_id": session_id}

    secure = client.post("/api/v2/secure/expenses/202/approve", cookies=cookies)
    assert secure.status_code == 200
    assert secure.json()["expense"]["status"] == "approved"
