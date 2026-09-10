---
title: Spring WebFlux vs MVC
type: source
kind: 대화
status: growing
tags: [spring, reactive, concurrency]
moc: ["[[MOC-출처]]", "[[MOC-Spring]]"]
created: 2026-08-31
updated: 2026-08-31
---

## 무엇

payment-system 강의를 Kotlin → Java로 포팅하면서 나온 `Mono`/`Flux` 관련 질문 8개. "Mono가 뭐냐"에서 시작해 "결제 시스템에서 WebFlux를 많이 쓰냐"로 끝난다.

## 핵심 주장

1. `Mono<T>`는 값을 담은 상자가 아니라 **처리 계획**이다. Lazy라서 `subscribe()` 전까지 아무 일도 안 일어난다.
2. **블로킹/논블로킹과 동기/비동기는 독립된 두 축**이다. WebFlux는 비동기 논블로킹이고, `@Async` + JDBC는 비동기 블로킹이다.
3. WebFlux가 빠른 이유는 **"기다림에는 스레드가 필요 없다"** 는 사실을 활용하기 때문이다. 소켓 감시는 OS의 일이다. 단일 요청은 오히려 미세하게 느리다.
4. WebFlux도 `@Controller`·`@GetMapping`을 쓰므로 **MVC 패턴을 따른다.** 진짜 대립축은 블로킹/서블릿 스택 대 논블로킹/리액티브 스택이다.
5. **결제 시스템의 다수는 여전히 MVC + JPA다.** 강의가 WebFlux를 쓰는 건 교육적 선택이지 현업 표준이어서가 아니다.

## 여기서 나온 페이지

| 페이지 | 무엇을 가져갔나 |
|---|---|
| [[블로킹과 비동기는 다른 축]] | 네 조합 표, 동기 논블로킹이 실제로 쓰이는 세 자리 |
| [[이벤트 루프와 스레드 점유]] | 1000 요청 × 200ms 시나리오, `.block()` 금지 이유 |
| [[Reactor]] | Mono/Flux 연산자, Lazy, `ThreadLocal` 유실, 코루틴과의 비교 |
| [[Spring WebFlux]] | 스택 비교표, 부분 도입 무의미, 가상 스레드 이후의 위치 |
| [[결제 시스템에 WebFlux를 쓸 것인가]] | 다섯 근거와 확신도 |

## 기존 위키와의 관계

- **엔티티 축이 열렸다** — `pages/entities/`가 [[Testcontainers]] 하나뿐이었는데 [[Reactor]]·[[Spring WebFlux]] 둘이 붙었다
- **연결**: [[@Async vs ExecutorService]] — 기존 실험이 "비동기 블로킹"의 실제 동작을 이미 관찰해 뒀다. 이번 개념이 그 실험에 이름을 붙여 줬다
- **연결**: [[Bulkhead]] — `flatMap` concurrency가 리액티브에서의 자원 격리라는 점이 양쪽에서 만난다

## 아직 안 다룬 것

- 🔴 **수치가 없다.** MVC와 WebFlux를 같은 조건으로 돌린 결과가 없어서 [[결제 시스템에 WebFlux를 쓸 것인가]]의 확신도가 "중간"에 머문다
- [[Java 21 가상 스레드]] — 이 문서 전체의 결론을 흔드는 변수인데 페이지가 없다. **Ingest 우선순위 후보**
- [[R2DBC]] — 트랜잭션 전파가 JDBC와 어떻게 다른지
- Reactor `Context`로 MDC·SecurityContext를 잇는 실제 코드
- 배압(backpressure) — `Flux`의 핵심 개념인데 원문이 다루지 않았다

## 원본

`raw/code/deep-dive-spring-webflux-vs-mvc.md`
