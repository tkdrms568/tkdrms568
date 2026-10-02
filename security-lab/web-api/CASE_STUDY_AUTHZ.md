# Authorization & Business Logic Case Study

## 시나리오

가상의 사내 비용 승인 시스템을 대상으로 객체 단위 접근통제와 업무 승인 로직을 검증합니다.

단순 IDOR 한 건을 재현하는 것이 아니라 **사용자 역할, 부서 범위, 객체 소유권, 업무 상태, 승인 책임 분리**를 함께 확인하는 것이 목적입니다.

---

## 권한 모델

| 사용자 | 역할 | 부서 | 정상 권한 |
|---|---|---|---|
| alice | Employee | A | 본인 비용 조회·제출 |
| bob | Employee | A | 본인 비용 조회·제출 |
| manager_a | Manager | A | A부서 제출 건 조회·승인 |
| manager_b | Manager | B | B부서 제출 건 조회·승인 |
| charlie | Employee | B | 본인 비용 조회·제출 |
| admin | Admin | HQ | 전체 조회 |

## 업무 상태

```text
draft
  ↓ submit
submitted
  ↓ approve / reject
approved / rejected
```

검증 핵심은 Client가 전달하는 상태값을 신뢰하지 않고 서버가 **현재 상태 + 사용자 역할 + 부서 + 객체 소유권**을 함께 확인하는지 여부입니다.

---

## Test Scenario 01 · 수평/범위 권한

Alice로 로그인한 뒤 B부서 Charlie의 비용 객체 `203`에 접근합니다.

### 취약 구현

```text
GET /api/v2/vuln/expenses/203
```

인증 여부만 확인하기 때문에 다른 부서 객체가 반환됩니다.

### 개선 구현

```text
GET /api/v2/secure/expenses/203
```

Employee는 자신의 객체만 접근할 수 있으므로 서버에서 403으로 차단합니다.

### 분석 포인트

단순히 ID를 바꿔 데이터가 보인다는 사실보다, **목록·상세·수정 등 여러 Endpoint에서 동일한 Object Authorization 정책이 일관되게 적용되는지**를 확인합니다.

---

## Test Scenario 02 · Workflow 단계 건너뛰기

Alice의 비용 요청 `201`은 `draft` 상태입니다.

취약 구현은 Client가 원하는 상태를 직접 전달할 수 있습니다.

```text
POST /api/v2/vuln/expenses/201/transition

{"status":"approved"}
```

서버가 현재 상태와 역할을 확인하지 않으면 `draft → approved`로 업무 단계를 건너뛸 수 있습니다.

개선 구현은 상태값을 직접 받지 않고 `submit`, `approve`와 같이 서버가 의미를 알고 있는 동작으로 분리하고, 현재 상태를 확인합니다.

---

## Test Scenario 03 · 부서 범위 우회

A부서 `manager_a`가 B부서 Charlie의 요청 `203`을 승인하도록 시도합니다.

### 취약 판단

"Manager인가?"만 확인하면 Role 검증은 존재하지만 **Scope 검증은 누락**된 상태입니다.

### 개선 판단

다음을 함께 확인해야 합니다.

- Manager 역할인가
- 해당 Expense와 같은 부서인가
- 현재 상태가 submitted인가
- 요청자 본인의 Expense가 아닌가

---

## Test Scenario 04 · Separation of Duties

`manager_a`가 자신의 비용 요청 `204`를 직접 승인하도록 시도합니다.

Role만 확인하면 Manager 본인의 요청도 승인할 수 있습니다.

개선 구현에서는 `expense.owner_id != current_user.id` 조건을 통해 요청과 승인을 분리합니다.

이 시나리오는 단순한 URL 접근통제보다 **업무 규칙 자체가 보안 통제라는 점**을 보여주기 위한 항목입니다.

---

## 재점검 관점

조치 후에는 한 Endpoint만 확인하지 않습니다.

- 목록과 상세의 권한 정책이 같은가
- 조회·수정·승인에 동일한 범위가 적용되는가
- 다른 부서 Manager도 동일하게 차단되는가
- 상태 전이 우회가 남아 있지 않은가
- 자기 승인 외 다른 업무 분리 우회가 없는가

---

## 포트폴리오 증적

실제 캡처에서는 다음 6개 정도만 사용합니다.

1. 사용자·부서·역할 구조
2. 정상적인 A부서 승인 요청
3. Alice → Charlie 객체 접근 비교
4. Draft → Approved 직접 변경 시도
5. A부서 Manager → B부서 승인 시도
6. 취약/개선 Endpoint의 결과 비교

화면 수를 늘리는 것보다 **왜 이 요청을 변조했고, 서버가 무엇을 검증해야 하는지**를 설명하는 데 초점을 둡니다.
