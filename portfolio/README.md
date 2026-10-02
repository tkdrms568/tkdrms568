# Security Portfolio

약 7년간 수행해 온 기술보안 업무에서 사용한 **분석 방식, 판단 기준, 개선관리 및 프로젝트 리딩 경험**을 정리한 포트폴리오입니다.

단순 취약점 재현이나 도구 사용 화면보다, 실제 보안 업무에서 중요한 **서비스 이해 → 공격면 선정 → 검증 → 영향도 판단 → 개선 → 재점검**의 흐름을 보여주는 것을 목표로 합니다.

고객사 시스템, URL·IP·계정, 내부 문서, 실제 취약점 원본 증적은 공개하지 않습니다.

---

## Professional Portfolio

1. [Security Assessment Methodology](./01-security-assessment-methodology.md)  
   서비스 구조 파악, 공격면 선정, 검증, Finding 판단 및 재점검 방식

2. [Authorization & Business Logic Assessment](./02-authz-business-logic-case.md)  
   사용자·권한 구조, 객체 단위 권한검증, 업무 로직 및 영향도 판단

3. [Mobile Security & Reversing](./03-mobile-reversing-frida.md)  
   역공학, Root Detection 분석, Frida 런타임·메모리 분석

4. [C/S · .NET Application Security Analysis](./04-cs-dotnet-analysis.md)  
   dnSpy와 EchoMirage를 활용한 클라이언트 로직 및 통신 분석

5. [AI Chatbot Security Assessment](./05-ai-prompt-injection.md)  
   Prompt Injection, 내부정보 노출 가능성, 영향도와 개선 방향

6. [Vulnerability Management](./06-vulnerability-management.md)  
   Finding 관리, 조치 협의, 재점검 및 개선 확인

7. [Security Project Leadership](./07-project-leadership.md)  
   PM/PL 관점의 범위·일정·진단 품질·고객 커뮤니케이션 관리

---

## Supporting Lab

실제 고객사 증적 대신 공개 가능한 증적을 만들기 위한 별도 로컬 테스트 환경입니다.

- [Web / API Security Lab](../security-lab/web-api/README.md)

Security Lab 자체가 포트폴리오의 핵심은 아니며, 위 문서의 분석 방식과 판단 근거를 공개 가능한 환경에서 재현하기 위한 보조 수단으로 사용합니다.

---

## 공개 원칙

- 고객사 기밀 및 식별정보 비공개
- 실제 취약점 원본 증적 비공개
- 실제 계정·토큰·개인정보 비공개
- 공개 증적은 별도 테스트 환경에서 재현
- 공격 성공 화면보다 원인·영향·개선 과정을 중심으로 정리
