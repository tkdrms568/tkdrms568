from __future__ import annotations

import html
import secrets
import sqlite3
from pathlib import Path

from fastapi import Cookie, FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "security_lab.db"

app = FastAPI(
    title="Security Lab - Web/API",
    description="Intentionally vulnerable local lab for security assessment practice.",
    version="0.2.0",
)

SESSIONS: dict[str, dict] = {}


class StatusChange(BaseModel):
    status: str


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def reset_database() -> None:
    conn = db()
    conn.executescript(
        """
        DROP TABLE IF EXISTS expenses;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS users;

        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT NOT NULL,
            email TEXT NOT NULL
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product TEXT NOT NULL,
            price INTEGER NOT NULL,
            note TEXT NOT NULL
        );

        CREATE TABLE expenses (
            id INTEGER PRIMARY KEY,
            owner_id INTEGER NOT NULL,
            department TEXT NOT NULL,
            title TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL
        );
        """
    )
    conn.executemany(
        "INSERT INTO users(id, username, password, role, department, email) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, "admin", "admin123!", "admin", "HQ", "admin@lab.local"),
            (2, "alice", "alice123!", "employee", "A", "alice@lab.local"),
            (3, "bob", "bob123!", "employee", "A", "bob@lab.local"),
            (4, "manager_a", "managerA123!", "manager", "A", "manager-a@lab.local"),
            (5, "manager_b", "managerB123!", "manager", "B", "manager-b@lab.local"),
            (6, "charlie", "charlie123!", "employee", "B", "charlie@lab.local"),
        ],
    )
    conn.executemany(
        "INSERT INTO orders(id, user_id, product, price, note) VALUES (?, ?, ?, ?, ?)",
        [
            (101, 2, "Security Book", 32000, "alice-private-note"),
            (102, 3, "USB Adapter", 19000, "bob-private-note"),
        ],
    )
    conn.executemany(
        "INSERT INTO expenses(id, owner_id, department, title, amount, status) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (201, 2, "A", "Cloud test license", 120000, "draft"),
            (202, 3, "A", "Security appliance rental", 890000, "submitted"),
            (203, 6, "B", "Training budget", 350000, "submitted"),
            (204, 4, "A", "Team tool renewal", 500000, "submitted"),
        ],
    )
    conn.commit()
    conn.close()


@app.on_event("startup")
def startup() -> None:
    reset_database()


def current_user(session_id: str | None) -> dict:
    if not session_id or session_id not in SESSIONS:
        raise HTTPException(status_code=401, detail="Login required")
    return SESSIONS[session_id]


def page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 980px; margin: 40px auto; line-height: 1.6; }}
code, pre {{ background: #f5f5f5; padding: 3px 6px; border-radius: 4px; }}
.card {{ border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 14px 0; }}
.warn {{ background: #fff4e5; border-left: 4px solid #f0a000; padding: 12px; }}
.ok {{ background: #eef9f0; border-left: 4px solid #2d8a45; padding: 12px; }}
a {{ color: #165dcc; }}
input {{ padding: 7px; margin: 4px; }}
button {{ padding: 7px 12px; }}
</style>
</head>
<body>
<h1>{html.escape(title)}</h1>
{body}
</body>
</html>"""
    )


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return page(
        "Security Lab - Web / API",
        """
<div class="warn">
<strong>로컬 테스트 전용:</strong> 의도적으로 취약한 기능이 포함되어 있습니다.
인터넷에 직접 노출하지 마세요.
</div>

<div class="card">
<h2>Advanced Case Study · 비용 승인 Workflow</h2>
<p>단순 취약점 재현이 아니라 사용자·부서·역할·객체 소유권·상태 전이를 함께 검증하도록 구성했습니다.</p>
<ul>
<li>수평 권한: 다른 사용자의 비용 객체 접근</li>
<li>범위 권한: 다른 부서 Manager의 승인</li>
<li>업무 로직: Draft → Approved 단계 건너뛰기</li>
<li>Separation of Duties: 자신의 요청을 스스로 승인</li>
</ul>
<p><a href="/docs">Swagger API</a> · 저장소의 CASE_STUDY_AUTHZ.md에서 테스트 매트릭스 확인</p>
</div>

<div class="card">
<h2>테스트 계정</h2>
<ul>
<li>admin / admin123! · HQ</li>
<li>alice / alice123! · Employee / A</li>
<li>bob / bob123! · Employee / A</li>
<li>manager_a / managerA123! · Manager / A</li>
<li>manager_b / managerB123! · Manager / B</li>
<li>charlie / charlie123! · Employee / B</li>
</ul>
<a href="/login">로그인</a>
</div>

<div class="card">
<h2>기본 Web/API 진단 항목</h2>
<ul>
<li>SQL Injection: <code>/vuln/search</code> / <code>/secure/search</code></li>
<li>Reflected XSS: <code>/vuln/xss</code> / <code>/secure/xss</code></li>
<li>IDOR: <code>/vuln/profile/{id}</code> / <code>/secure/profile/{id}</code></li>
<li>API BOLA: <code>/api/vuln/orders/{id}</code> / <code>/api/secure/orders/{id}</code></li>
<li>중요정보 노출: <code>/vuln/debug</code> / <code>/secure/status</code></li>
<li>CSRF: <code>/vuln/change-email</code> / <code>/secure/change-email</code></li>
</ul>
</div>
""",
    )


@app.get("/login", response_class=HTMLResponse)
def login_form() -> HTMLResponse:
    return page(
        "Login",
        """
<form method="post" action="/login">
<label>Username <input name="username"></label><br>
<label>Password <input name="password" type="password"></label><br>
<button type="submit">Login</button>
</form>
<p><a href="/">Home</a></p>
""",
    )


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    conn = db()
    row = conn.execute(
        "SELECT id, username, role, department, email FROM users WHERE username = ? AND password = ?",
        (username, password),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_id = secrets.token_urlsafe(24)
    csrf_token = secrets.token_urlsafe(24)
    SESSIONS[session_id] = {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"],
        "department": row["department"],
        "email": row["email"],
        "csrf": csrf_token,
    }
    response = RedirectResponse(url="/me", status_code=303)
    response.set_cookie("session_id", session_id, httponly=True, samesite="lax")
    return response


@app.get("/logout")
def logout(session_id: str | None = Cookie(default=None)):
    if session_id:
        SESSIONS.pop(session_id, None)
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_id")
    return response


@app.get("/me", response_class=HTMLResponse)
def me(session_id: str | None = Cookie(default=None)) -> HTMLResponse:
    user = current_user(session_id)
    return page(
        "My Session",
        f"""
<div class="card">
<p><strong>User:</strong> {html.escape(user["username"])}</p>
<p><strong>Role:</strong> {html.escape(user["role"])}</p>
<p><strong>Department:</strong> {html.escape(user["department"])}</p>
<p><strong>User ID:</strong> {user["id"]}</p>
</div>
<p><a href="/secure/profile/{user['id']}">내 프로필</a></p>
<p><a href="/logout">Logout</a></p>
""",
    )


@app.get("/vuln/search")
def vulnerable_search(q: str = ""):
    conn = db()
    # INTENTIONALLY VULNERABLE: SQL query string interpolation.
    sql = f"SELECT id, username, role, department, email FROM users WHERE username LIKE '%{q}%'"
    try:
        rows = conn.execute(sql).fetchall()
        result = [dict(row) for row in rows]
        return {"mode": "vulnerable", "query": sql, "count": len(result), "results": result}
    except sqlite3.Error as exc:
        return JSONResponse(
            status_code=500,
            content={"mode": "vulnerable", "query": sql, "database_error": str(exc)},
        )
    finally:
        conn.close()


@app.get("/secure/search")
def secure_search(q: str = ""):
    conn = db()
    rows = conn.execute(
        "SELECT id, username, role, department, email FROM users WHERE username LIKE ?",
        (f"%{q}%",),
    ).fetchall()
    conn.close()
    return {"mode": "secure", "count": len(rows), "results": [dict(r) for r in rows]}


@app.get("/vuln/xss", response_class=HTMLResponse)
def vulnerable_xss(q: str = "") -> HTMLResponse:
    return HTMLResponse(
        f"""<h1>Vulnerable Reflected XSS</h1>
<p>검색어: {q}</p>
<p><a href="/">Home</a></p>"""
    )


@app.get("/secure/xss", response_class=HTMLResponse)
def secure_xss(q: str = "") -> HTMLResponse:
    return HTMLResponse(
        f"""<h1>Secure Reflected Output</h1>
<p>검색어: {html.escape(q)}</p>
<p><a href="/">Home</a></p>"""
    )


@app.get("/vuln/profile/{user_id}")
def vulnerable_profile(user_id: int, session_id: str | None = Cookie(default=None)):
    current_user(session_id)
    conn = db()
    row = conn.execute(
        "SELECT id, username, role, department, email FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {"mode": "vulnerable", "profile": dict(row)}


@app.get("/secure/profile/{user_id}")
def secure_profile(user_id: int, session_id: str | None = Cookie(default=None)):
    user = current_user(session_id)
    if user["role"] != "admin" and user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn = db()
    row = conn.execute(
        "SELECT id, username, role, department, email FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {"mode": "secure", "profile": dict(row)}


@app.get("/api/vuln/orders/{order_id}")
def vulnerable_order(order_id: int, session_id: str | None = Cookie(default=None)):
    current_user(session_id)
    conn = db()
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"mode": "vulnerable", "order": dict(row)}


@app.get("/api/secure/orders/{order_id}")
def secure_order(order_id: int, session_id: str | None = Cookie(default=None)):
    user = current_user(session_id)
    conn = db()
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    if user["role"] != "admin" and row["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"mode": "secure", "order": dict(row)}


@app.get("/vuln/debug")
def vulnerable_debug():
    return {
        "debug": True,
        "database": str(DB_PATH),
        "environment": "local-security-lab",
        "demo_internal_key": "LAB-DEMO-SECRET-2026",
        "note": "Fake data for portfolio practice only.",
    }


@app.get("/secure/status")
def secure_status():
    return {"status": "ok"}


@app.post("/vuln/change-email")
def vulnerable_change_email(
    email: str = Form(...),
    session_id: str | None = Cookie(default=None),
):
    user = current_user(session_id)
    conn = db()
    conn.execute("UPDATE users SET email = ? WHERE id = ?", (email, user["id"]))
    conn.commit()
    conn.close()
    SESSIONS[session_id]["email"] = email
    return {"mode": "vulnerable", "updated": True, "email": email}


@app.post("/secure/change-email")
def secure_change_email(
    email: str = Form(...),
    csrf_token: str = Form(...),
    session_id: str | None = Cookie(default=None),
):
    user = current_user(session_id)
    if not secrets.compare_digest(csrf_token, user["csrf"]):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    conn = db()
    conn.execute("UPDATE users SET email = ? WHERE id = ?", (email, user["id"]))
    conn.commit()
    conn.close()
    SESSIONS[session_id]["email"] = email
    return {"mode": "secure", "updated": True, "email": email}


@app.get("/secure/change-email-form", response_class=HTMLResponse)
def secure_change_email_form(session_id: str | None = Cookie(default=None)):
    user = current_user(session_id)
    return page(
        "Secure Email Change",
        f"""
<form method="post" action="/secure/change-email">
<input type="hidden" name="csrf_token" value="{html.escape(user['csrf'])}">
<label>New email <input name="email" value="{html.escape(user['email'])}"></label>
<button type="submit">Change</button>
</form>
""",
    )


# ---------------------------------------------------------------------------
# Advanced Case Study: Expense Approval Workflow
# ---------------------------------------------------------------------------


def get_expense(expense_id: int) -> sqlite3.Row:
    conn = db()
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Expense not found")
    return row


def update_expense_status(expense_id: int, status: str) -> dict:
    conn = db()
    conn.execute("UPDATE expenses SET status = ? WHERE id = ?", (status, expense_id))
    conn.commit()
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()
    return dict(row)


@app.get("/api/v2/vuln/expenses")
def vulnerable_expense_list(session_id: str | None = Cookie(default=None)):
    current_user(session_id)
    conn = db()
    rows = conn.execute("SELECT * FROM expenses ORDER BY id").fetchall()
    conn.close()
    # INTENTIONALLY VULNERABLE: all authenticated users see all departments.
    return {"mode": "vulnerable", "results": [dict(row) for row in rows]}


@app.get("/api/v2/secure/expenses")
def secure_expense_list(session_id: str | None = Cookie(default=None)):
    user = current_user(session_id)
    conn = db()
    if user["role"] == "admin":
        rows = conn.execute("SELECT * FROM expenses ORDER BY id").fetchall()
    elif user["role"] == "manager":
        rows = conn.execute(
            "SELECT * FROM expenses WHERE department = ? ORDER BY id",
            (user["department"],),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE owner_id = ? ORDER BY id",
            (user["id"],),
        ).fetchall()
    conn.close()
    return {"mode": "secure", "results": [dict(row) for row in rows]}


@app.get("/api/v2/vuln/expenses/{expense_id}")
def vulnerable_expense_detail(
    expense_id: int,
    session_id: str | None = Cookie(default=None),
):
    current_user(session_id)
    # INTENTIONALLY VULNERABLE: authentication only; no object/department authorization.
    return {"mode": "vulnerable", "expense": dict(get_expense(expense_id))}


@app.get("/api/v2/secure/expenses/{expense_id}")
def secure_expense_detail(
    expense_id: int,
    session_id: str | None = Cookie(default=None),
):
    user = current_user(session_id)
    expense = get_expense(expense_id)

    allowed = (
        user["role"] == "admin"
        or expense["owner_id"] == user["id"]
        or (user["role"] == "manager" and expense["department"] == user["department"])
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    return {"mode": "secure", "expense": dict(expense)}


@app.post("/api/v2/vuln/expenses/{expense_id}/transition")
def vulnerable_expense_transition(
    expense_id: int,
    change: StatusChange,
    session_id: str | None = Cookie(default=None),
):
    current_user(session_id)
    get_expense(expense_id)

    if change.status not in {"draft", "submitted", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Unsupported status")

    # INTENTIONALLY VULNERABLE:
    # - trusts a client-supplied status
    # - does not enforce state transitions
    # - does not enforce role, department or separation of duties
    updated = update_expense_status(expense_id, change.status)
    return {"mode": "vulnerable", "expense": updated}


@app.post("/api/v2/secure/expenses/{expense_id}/submit")
def secure_expense_submit(
    expense_id: int,
    session_id: str | None = Cookie(default=None),
):
    user = current_user(session_id)
    expense = get_expense(expense_id)

    if expense["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the owner can submit")
    if expense["status"] != "draft":
        raise HTTPException(status_code=409, detail="Only draft expenses can be submitted")

    updated = update_expense_status(expense_id, "submitted")
    return {"mode": "secure", "expense": updated}


@app.post("/api/v2/vuln/expenses/{expense_id}/approve")
def vulnerable_expense_approve(
    expense_id: int,
    session_id: str | None = Cookie(default=None),
):
    user = current_user(session_id)
    expense = get_expense(expense_id)

    if user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Manager role required")

    # INTENTIONALLY VULNERABLE:
    # - manager role is checked, but department scope is ignored
    # - a manager can approve their own request
    # - current workflow state is not checked
    updated = update_expense_status(expense_id, "approved")
    return {"mode": "vulnerable", "expense": updated}


@app.post("/api/v2/secure/expenses/{expense_id}/approve")
def secure_expense_approve(
    expense_id: int,
    session_id: str | None = Cookie(default=None),
):
    user = current_user(session_id)
    expense = get_expense(expense_id)

    if user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Manager role required")
    if expense["department"] != user["department"]:
        raise HTTPException(status_code=403, detail="Department scope violation")
    if expense["owner_id"] == user["id"]:
        raise HTTPException(status_code=403, detail="Self approval is not allowed")
    if expense["status"] != "submitted":
        raise HTTPException(status_code=409, detail="Only submitted expenses can be approved")

    updated = update_expense_status(expense_id, "approved")
    return {"mode": "secure", "expense": updated}
