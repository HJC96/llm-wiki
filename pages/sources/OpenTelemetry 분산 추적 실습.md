---
title: OpenTelemetry 분산 추적 실습
type: source
kind: code
status: seed
tags: [observability, distributed, docker]
moc: ["[[MOC-출처]]", "[[MOC-인프라]]"]
created: 2026-09-10
updated: 2026-09-10
---

## 무엇

user → order → payment 세 서비스를 체인으로 호출시키고, 그 흐름을 OpenTelemetry Collector → Tempo → Grafana로 들여다보는 실습 인프라. 애플리케이션 코드가 아니라 **Docker Compose와 에이전트 설정이 본체**다.

## 핵심 주장

1. **관측 경로와 서비스 경로는 별개여야 한다.** 트레이스 전송이 실제 호출과 다른 길로 나가므로 Collector가 죽어도 서비스는 돈다.
2. **Collector를 반드시 거치게 만든다.** Tempo의 수신 포트(4317)를 호스트에 열지 않아, 앱이 저장소로 직접 쏘는 길을 원천 차단했다.
3. **계측에 코드 변경이 필요 없다.** `build.gradle.kts`에 OpenTelemetry 의존성이 없고, `-javaagent`와 `OTEL_*` 환경변수만으로 붙는다.
4. **이번 구성은 트레이스만 다룬다.** `OTEL_METRICS_EXPORTER=none`이고 Collector 설정의 prometheus receiver도 주석 처리돼 있다. 8889 포트는 열려만 있고 쓰이지 않는다.
5. **빌드가 컨테이너 안에서 일어난다.** 로컬에 Gradle·JDK가 없어도 Docker만 있으면 돌아간다.

## 여기서 나온 페이지

| 페이지 | 무엇을 가져갔나 |
|---|---|
| [[분산 추적]] | Span·Trace·Collector 세 용어, 두 갈래 경로 구조, Java Agent 계측과 그 대가 |

## 기존 위키와의 관계

- **빈 링크 해소**: `[[분산 추적]]` — [[결제 시스템 키워드 지도]]가 "완전히 없다. [[Micrometer 계측기 선택]]은 지표지 추적이 아니다"라고 3회 지목하던 구멍
- **보강**: [[Micrometer 계측기 선택]] — 지표와 추적이 어떻게 갈리는지의 반대편이 생겼다
- **경계 확인**: [[Bulkhead]] — 관측 경로를 서비스 경로에서 떼어 놓는 것도 같은 자원 격리 사고다

## 아직 안 다룬 것

- 🔴 **수치가 하나도 없다.** 에이전트 유무의 시작 시간·p95 차이를 재지 않았다. 재면 [[MOC-실험]]의 lab 페이지가 된다
- **샘플링** — 전량 수집만 한다. 트래픽이 커졌을 때의 정책이 없다
- **Trace ↔ Log 연결** — trace id를 애플리케이션 로그에 심어 Grafana에서 오가는 구성
- **수동 Span** — 도메인 단위(결제 승인 한 건)로 끊는 계측
- **Metrics·Logs** — OTel의 세 신호 중 트레이스만 켰다

## 원본

`raw/code/lecture-otel-분산추적-인프라.md` (README 캡처)
저장소 원본: `~/Desktop/git/lecture_otel/` — `infra/` 4개 설정 파일과 서비스 3개. 복사하지 않고 경로로 가리킨다
