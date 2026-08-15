---
title: MOC-인프라
type: moc
tags: [meta, docker, k8s, aws, ci-cd]
created: 2026-08-15
updated: 2026-08-15
---

# MOC — 인프라

← [[MOC-홈]]

## 컨테이너

- [[Docker 이미지 레이어]] — 캐시가 깨지는 지점
- [[멀티스테이지 빌드]] · [[JVM 컨테이너 메모리 인식]] 🔴
- [[Docker Compose로 로컬 의존성 띄우기]] → [[Testcontainers]]와 어떻게 다른가

## Kubernetes

- [[K8s 파드와 서비스]] · [[디플로이먼트 롤링 업데이트]]
- [[readiness와 liveness 프로브]] 🔴 — 잘못 잡으면 재시작 루프
- [[ConfigMap과 Secret]]

## AWS

- [[AWS 가용영역과 리전]] · [[ELB와 헬스체크]]
- [[비용을 설계 근거로 쓰기]] — OpenSearch 미도입 판단 사례

## CI/CD

- [[CI-CD 품질 게이트]] — 테스트 실패 시 배포 차단
- [[배포 승인 게이트를 나누는 이유]] — 개발은 자동, 운영은 수동
- [[정적 분석과 취약점 점검을 파이프라인에 넣기]] — SonarQube, Black Duck
- [[파이프라인 실패 알림]] — Teams 웹훅

## 관측

- [[Actuator 엔드포인트 보안 경계]] 🔴
- [[구조화 로깅]] · [[감사 로그를 AOP로 분리하기]]
- [[실패 사실의 기록]] ✅ — 잔여 상태를 운영 지표로. **0이어야 정상이 아니라 감시되고 있어야 정상**

## 부하 테스트

- [[k6로 Before After 측정하기]] — VU, ramp-up, p50/p95
- [[로컬 부하 테스트의 한계]] 🔴 — 절대 성능이 아니라 상대 개선치로만 읽는다

## 이어지는 곳

- 실무 판단 → `pages/private/` · 실험 → [[MOC-실험]]
