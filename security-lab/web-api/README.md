# Web / API Security Lab

보안 진단 포트폴리오를 만들기 위한 **로컬 전용 의도적 취약 웹/API 테스트 환경**입니다.

취약 버전과 개선 버전을 같은 애플리케이션에서 비교할 수 있도록 구성했습니다.

## 포함된 진단 항목

| 항목 | 취약 Endpoint | 개선 Endpoint |
|---|---|---|
| SQL Injection | `/vuln/search` | `/secure/search` |
| Reflected XSS | `/vuln/xss` | `/secure/xss` |
| IDOR / 접근통제 | `/vuln/profile/{id}` | `/secure/profile/{id}` |
| API BOLA | `/api/vuln/orders/{id}` | `/api/secure/orders/{id}` |
| 중요정보 노출 | `/vuln/debug` | `/secure/status` |
| CSRF | `/vuln/change-email` | `/secure/change-email` |

## 테스트 계정

| 계정 | 비밀번호 | 역할 |
|---|---|---|
| admin | `admin123!` | admin |
| alice | `alice123!` | user |
| bob | `bob123!` | user |

모든 데이터는 로컬 실습용 가짜 데이터입니다.

---

## 실행 방법 1 · Python

Windows PowerShell 기준:

```powershell
cd security-lab\web-api

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8001
```

브라우저:

```text
http://127.0.0.1:8001
```

API 문서:

```text
http://127.0.0.1:8001/docs
```

---

## 실행 방법 2 · Docker

```powershell
docker compose up --build
```

브라우저:

```text
http://127.0.0.1:8001
```

`docker-compose.yml`은 호스트의 `127.0.0.1`에만 포트를 바인딩합니다.

종료:

```powershell
docker compose down
```

---

## 첫 번째 포트폴리오 진행 순서

### 1. 환경 확인

브라우저에서 메인 화면을 열고 전체 테스트 환경을 캡처합니다.

추천 파일명:

```text
portfolio/assets/web-api/01-target-overview.png
```

### 2. Burp Suite 연결

브라우저 프록시를 Burp Suite로 설정한 뒤 로그인과 주요 기능을 사용하면서 요청·응답을 확인합니다.

캡처:

```text
02-request-response.png
```

### 3. SQL Injection

정상 검색 요청과 비정상 입력 요청의 응답 차이를 비교합니다.

- 취약: `/vuln/search`
- 개선: `/secure/search`

확인할 것:

- 반환 데이터 개수 차이
- SQL 오류 노출 여부
- 취약 버전과 Parameterized Query 적용 버전 차이

### 4. XSS

- 취약: `/vuln/xss`
- 개선: `/secure/xss`

사용자 입력이 HTML에 출력되는 과정과 Encoding 적용 전후를 비교합니다.

### 5. IDOR / BOLA

Alice로 로그인한 뒤 Bob의 프로필과 주문에 접근을 시도합니다.

- `/vuln/profile/3`
- `/secure/profile/3`
- `/api/vuln/orders/102`
- `/api/secure/orders/102`

취약 버전은 리소스 소유권을 확인하지 않고, 개선 버전은 서버에서 권한을 검증합니다.

### 6. 중요정보 노출

`/vuln/debug`와 `/secure/status`의 응답을 비교해 운영정보와 가짜 내부 키가 외부로 노출되는 차이를 확인합니다.

### 7. CSRF

로그인 상태에서 이메일 변경 기능을 비교합니다.

- 취약 버전: CSRF Token 미검증
- 개선 버전: 세션별 CSRF Token 검증

### 8. 원인 분석

각 취약 기능의 코드에서 원인을 확인합니다.

예:

- SQL 문자열 직접 조합
- HTML Encoding 누락
- Object Ownership 검증 누락
- Debug 정보 응답 노출
- CSRF Token 미검증

### 9. 재점검

같은 입력과 요청을 개선 Endpoint로 전송하여 차단 여부를 확인합니다.

이 과정의 스크린샷을 `portfolio/01-web-api-security.md`에 연결하면 첫 포트폴리오가 완성됩니다.

---

## 자동 테스트

```powershell
pytest -q
```

테스트는 취약 버전에서 문제가 실제로 재현되고, 개선 버전에서는 차단되는지 비교합니다.

---

## 안전 주의사항

이 애플리케이션에는 의도적으로 취약한 코드가 포함되어 있습니다.

- 인터넷에 배포하지 마세요.
- 클라우드에 Public Endpoint로 올리지 마세요.
- 실제 개인정보, 계정, Token을 넣지 마세요.
- 테스트는 본인 PC의 로컬 환경에서만 진행하세요.
