from __future__ import annotations

import html
import secrets
import sqlite3
from pathlib import Path

from fastapi import Cookie, FastAPI, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "security_lab.db"

app = FastAPI(
    title="Security Lab - Web/API",
    description="Intentionally vulnerable local lab for security assessment practice.",
    version="0.1.0",
)

SESSIONS: dict[str, dict] = {}


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def reset_database() -> None:
    conn = db()
    conn.executescript(
        """
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS orders;

        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT NOT NULL
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product TEXT NOT NULL,
            price INTEGER NOT NULL,
            note TEXT NOT NULL
        );
        """
    )
    conn.executemany(
        "INSERT INTO users(id, username, password, role, email) VALUES (?, ?, ?, ?, ?)",
        [
            (1, "admin", "admin123!", "admin", "admin@lab.local"),
            (2, "alice", "alice123!", "user", "alice@lab.local"),
            (3, "bob", "bob123!", "user", "bob@lab.local"),
        ],
    )
    conn.executemany(
        "INSERT INTO orders(id, user_id, product, price, note) VALUES (?, ?, ?, ?, ?)",
        [
            (101, 2, "Security Book", 32000, "alice-private-note"),
            (102, 3, "USB Adapter", 19000, "bob-private-note"),
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
<h2>테스트 계정</h2>
<ul>
<li>admin / admin123!</li>
<li>alice / alice123!</li>
<li>bob / bob123!</li>
</ul>
<a href="/login">로그인</a>
</div>

<div class="card">
<h2>SQL Injection</h2>
<ul>
<li><a href="/vuln/search?q=alice">취약 버전</a></li>
<li><a href="/secure/search?q=alice">개선 버전</a></li>
</ul>
</div>

<div class="card">
<h2>Reflected XSS</h2>
<ul>
<li><a href="/vuln/xss?q=hello">취약 버전</a></li>
<li><a href="/secure/xss?q=hello">개선 버전</a></li>
</ul>
</div>

<div class="card">
<h2>접근통제 / IDOR</h2>
<p>로그인 후 Alice와 Bob 계정으로 사용자/주문 리소스 접근 차이를 비교합니다.</p>
<ul>
<li><code>/vuln/profile/2</code>, <code>/vuln/profile/3</code></li>
<li><code>/secure/profile/2</code>, <code>/secure/profile/3</code></li>
<li><code>/api/vuln/orders/101</code>, <code>/api/vuln/orders/102</code></li>
<li><code>/api/secure/orders/101</code>, <code>/api/secure/orders/102</code></li>
</ul>
</div>

<div class="card">
<h2>중요정보 노출</h2>
<ul>
<li><a href="/vuln/debug">취약 Debug Endpoint</a></li>
<li><a href="/secure/status">개선된 상태 Endpoint</a></li>
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
        "SELECT id, username, role, email FROM users WHERE username = ? AND password = ?",
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
    sql = f"SELECT id, username, role, email FROM users WHERE username LIKE '%{q}%'"
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
        "SELECT id, username, role, email FROM users WHERE username LIKE ?",
        (f"%{q}%",),
    ).fetchall()
    conn.close()
    return {"mode": "secure", "count": len(rows), "results": [dict(r) for r in rows]}


@app.get("/vuln/xss", response_class=HTMLResponse)
def vulnerable_xss(q: str = "") -> HTMLResponse:
    # INTENTIONALLY VULNERABLE: unescaped user-controlled value.
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
        "SELECT id, username, role, email FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    # INTENTIONALLY VULNERABLE: any logged-in user can read any profile.
    return {"mode": "vulnerable", "profile": dict(row)}


@app.get("/secure/profile/{user_id}")
def secure_profile(user_id: int, session_id: str | None = Cookie(default=None)):
    user = current_user(session_id)
    if user["role"] != "admin" and user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn = db()
    row = conn.execute(
        "SELECT id, username, role, email FROM users WHERE id = ?", (user_id,)
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
    # INTENTIONALLY VULNERABLE: no ownership check.
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
    # INTENTIONALLY VULNERABLE: debug details and a fake secret are exposed.
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
    # INTENTIONALLY VULNERABLE: no CSRF token validation.
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
