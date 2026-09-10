---
title: Reactor
type: entity
kind: library
status: growing
tags: [reactive, spring, concurrency]
sources: ["[[Spring WebFlux vs MVC]]"]
moc: ["[[MOC-Spring]]", "[[MOC-동시성]]"]
version: Spring Boot 3.2 계열
created: 2026-08-31
updated: 2026-08-31
---

## 한 줄

**"미래에 값이 도착할 비동기 스트림"을 타입으로 표현한 라이브러리.** `Mono<T>`는 0~1개, `Flux<T>`는 0~N개. Spring WebFlux의 기반이다.

## 어디에 쓰나

`deep-dive/labs/payment-system` — 원본 강의가 Kotlin + WebFlux라서 Java로 포팅하면 `Mono`/`Flux`가 포트 인터페이스 시그니처에 그대로 드러난다. 헥사고날 경계가 리액티브 타입으로 노출되는 형태를 관찰하기 좋은 코드.

## 핵심 동작

`CompletableFuture<T>`와 비슷한 자리인데 연산자가 훨씬 많다. 핵심은 **값을 꺼내려 하지 말고 그 위에서 조립한다**는 것.

```java
Mono<Confirm> result = paymentMono
        .map(p -> toResponse(p))                                    // 동기 변환 T -> U
        .flatMap(p -> pgClient.confirm(p))                          // 비동기 이어붙이기 T -> Mono<U>
        .flatMap(c -> repository.save(c))
        .onErrorResume(PgException.class, e -> Mono.just(fallback)) // 에러 처리
        .switchIfEmpty(Mono.error(new PaymentNotFoundException()));  // 값 없을 때
```

생성 — `Mono.just(x)` / `Mono.empty()` / `Mono.error(e)`.

성질 두 가지가 전부다.

1. **Lazy** — 만들기만 하면 아무 일도 안 일어난다. 누가 `subscribe()` 해야 실행된다. 컨트롤러가 `Mono`를 리턴하면 WebFlux 프레임워크가 대신 구독한다
2. **체인 전체가 논블로킹이어야 의미가 있다** — 중간에 블로킹이 하나만 껴도 이점이 사라진다

## 대안과 비교

| | Reactor | `CompletableFuture` | Kotlin 코루틴 |
|---|---|---|---|
| 값 개수 | 0~1(`Mono`) / 0~N(`Flux`) | 1 | 1 / `Flow`로 N |
| 연산자 | 매우 많음 (배압·재시도·타임아웃 내장) | 제한적 | suspend 함수로 순차 코드처럼 |
| 코드 모양 | 체인 | 체인 | **동기 코드와 거의 동일** |

원본 강의가 Kotlin인 이유가 여기 있다 — 코루틴이면 `Mono` 체인이 순차 코드로 보인다. Java로 옮기면 그 설탕이 사라져서 비동기 조립이 시그니처에 그대로 드러난다.

## 알아둘 함정

> 🔴 **`.block()`은 프로덕션 경로에서 금지.** 테스트에서만 쓴다. 이벤트 루프 스레드가 이걸 만나면 멈추고, 그 스레드는 몇 개 안 된다 → [[이벤트 루프와 스레드 점유]]

> 🔴 **`ThreadLocal`이 안 따라온다.** 한 요청이 여러 스레드를 오가므로 MDC 로깅·SecurityContext·트랜잭션 컨텍스트가 유실된다. Reactor `Context`를 써야 한다

> 🔴 **스택트레이스가 끊긴다.** 조립 시점과 실행 시점이 달라서 예외가 터진 자리가 코드의 자리와 다르다. `Hooks.onOperatorDebug()`는 비용이 커서 프로덕션에 못 켠다

## 버전 메모

`flatMap(fn)`의 concurrency 기본값은 256이다. 외부 호출에 쓸 때는 사실상 무제한이므로 **명시적으로 지정**한다 → [[Bulkhead]]

## 연결

- 개념: [[블로킹과 비동기는 다른 축]] · [[이벤트 루프와 스레드 점유]]
- [[Spring WebFlux]] — 이 라이브러리를 웹 스택으로 감싼 것
- [[결제 시스템에 WebFlux를 쓸 것인가]]
