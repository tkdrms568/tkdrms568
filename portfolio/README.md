# Security Portfolio

실무에서 수행해 온 보안 진단 역량을 공개 가능한 테스트 환경에서 재현해 정리하는 포트폴리오입니다.

고객사 시스템, 실제 URL·IP·계정, 내부 문서, 취약점 원본 증적은 포함하지 않습니다.  
모든 테스트는 직접 구성한 환경 또는 공개된 의도적 취약 환경에서 수행합니다.

## Portfolio

1. [Web / API Security Assessment](./01-web-api-security.md)
2. [Mobile Security & Reversing](./02-mobile-reversing.md)
3. [C/S Security Analysis](./03-cs-security-analysis.md)
4. [AI Chatbot Security](./04-ai-chatbot-security.md)
5. [Vulnerability Management](./05-vulnerability-management.md)

## 작성 원칙

- 실제로 수행한 테스트만 기록
- 공격 성공 화면만 보여주지 않고 원인과 영향까지 설명
- 개발·운영 관점의 개선방안 포함
- 수정 후 재점검 결과까지 가능하면 포함
- 고객사 자료와 실습 자료를 명확히 분리
- 민감정보, 실제 자격증명, 고객사 식별정보는 공개하지 않음

## 증적 관리

스크린샷은 `portfolio/assets/` 아래에 항목별 폴더를 만들어 저장합니다.

예시:

```text
portfolio/
├─ 01-web-api-security.md
├─ 02-mobile-reversing.md
├─ 03-cs-security-analysis.md
├─ 04-ai-chatbot-security.md
├─ 05-vulnerability-management.md
└─ assets/
   ├─ web-api/
   ├─ mobile/
   ├─ cs/
   ├─ ai/
   └─ vulnerability-management/
```
