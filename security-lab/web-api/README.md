# Web / API Security Lab

보안 진단 포트폴리오를 위한 **로컬 전용 의도적 취약 웹/API 테스트 환경**입니다.

현재는 단순 SQL Injection·XSS 재현보다 한 단계 더 나아가, 실제 업무 서비스에서 자주 문제가 되는 **객체 권한, 부서 범위, 상태 전이, 업무 승인 로직**을 분석할 수 있도록 고도화했습니다.

## Advanced Case Study · Expense Approval Workflow

가상의 비용 승인 시스템을 사용합니다.

### 역할

| 계정 | 역할 | 부서 |
|---|---|---|
| admin | Admin | HQ |
| alice | Employee | A |
| bob | Employee | A |
| manager_a | Manager | A |
| manager_b | Manager | B |
| charlie | Employee | B |

### 핵심 Business Rule

- 직원은 자신의 비용 요청만 조회 가능
- Manager는 자신의 부서 요청만 조회·승인 가능
- 요청자는 자신의 요청을 직접 승인할 수 없음
- 비용 요청은 `draft → submitted → approved/rejected` 순서를 따라야 함
- UI가 아니라 서버에서 권한과 상태를 검증해야 함

### 진단 포인트

| 검증 | 취약 구현 | 개선 구현 |
|---|---|---|
| 객체 조회 | 인증만 확인 | 소유자·부서·역할 확인 |
| 목록 범위 | 전체 부서 반환 | 역할/부서에 따른 필터링 |
| 상태 전이 | Client가 status 직접 지정 | 서버가 허용된 전이만 수행 |
| 부서 범위 | Manager 역할만 확인 | Manager + 동일 부서 검증 |
| 자기 승인 | 허용 | Separation of Duties 적용 |
| 승인 상태 | 현재 상태 미검증 | submitted 상태에서만 승인 |

상세 테스트 시나리오는 [CASE_STUDY_AUTHZ.md](./CASE_STUDY_AUTHZ.md)에 정리했습니다.

---

## 기본 Web/API 진단 항목

| 항목 | 취약 Endpoint | 개선 Endpoint |
|---|---|---|
| SQL Injection | `/vuln/search` | `/secure/search` |
| Reflected XSS | `/vuln/xss` | `/secure/xss` |
| IDOR / 접근통제 | `/vuln/profile/{id}` | `/secure/profile/{id}` |
| API BOLA | `/api/vuln/orders/{id}` | `/api/secure/orders/{id}` |
| 중요정보 노출 | `/vuln/debug` | `/secure/status` |
| CSRF | `/vuln/change-email` | `/secure/change-email` |

기본 항목은 포트폴리오의 주인공이 아니라, 요청·응답 분석과 재점검을 위한 보조 환경으로 사용합니다.

---

## 실행 방법

### Python

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

Swagger:

```text
http://127.0.0.1:8001/docs
```

### Docker

```powershell
docker compose up --build
```

종료:

```powershell
docker compose down
```

---

## 자동 검증

```powershell
pytest -q
```

테스트는 취약 구현에서 다음 문제가 재현되고 개선 구현에서는 차단되는지 비교합니다.

- 타 부서 객체 접근
- 업무 단계 건너뛰기
- 타 부서 Manager 승인
- 자기 승인
- 정상적인 동일 부서 승인

---

## 포트폴리오에서 볼 것

이 Lab을 단순히 "취약점이 있다"는 화면으로 사용하지 않습니다.

다음 흐름으로 정리합니다.

**권한 구조 이해 → 공격면 선정 → 정상 요청 확보 → 사용자/객체/상태 변조 → 실제 영향 확인 → 원인 분석 → 서버 측 개선 → 재점검**

[Authorization & Business Logic Portfolio](../../portfolio/02-authz-business-logic-case.md)

---

## 안전 주의사항

이 애플리케이션에는 의도적으로 취약한 코드가 포함되어 있습니다.

- 인터넷에 배포하지 마세요.
- Public Cloud Endpoint로 노출하지 마세요.
- 실제 개인정보·계정·Token을 넣지 마세요.
- 본인 PC의 로컬 환경에서만 사용하세요.
