---
title: "@Async vs ExecutorService"
type: lab
status: growing
tags: [spring, concurrency, java]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-실험]]", "[[MOC-Spring]]"]
repo: deep-dive/labs/spring
created: 2026-08-16
updated: 2026-08-16
---

## 확인하려던 것

같은 백그라운드 작업을 `@Async`와 `ExecutorService`로 각각 짰을 때 **무엇이 드러나고 무엇이 숨는가.** 그리고 프록시 함정이 실제로 재현되는가.

## 실험 설계

주문 완료 후 확인 메일 후처리를 두 방식으로 구현하고, **실행 스레드**를 관찰한다. 순차 → 병렬 전환의 소요 시간도 비교한다.

## 결과

### 무엇이 드러나고 무엇이 숨나

| | `@Async` | `ExecutorService` |
|---|---|---|
| 실행 방식 | Spring 프록시가 `TaskExecutor`에 위임 | 코드에서 직접 제출 |
| 호출부 | **일반 메서드 호출처럼 보임** | `CompletableFuture.supplyAsync(..., executor)`가 드러남 |
| 장점 | 서비스 코드가 단순 | **실행 흐름과 풀 선택이 명확** |
| 주의점 | **같은 Bean 내부 호출에는 적용 안 됨** | 풀 종료와 제출 흐름을 직접 관리 |

🟡 트레이드오프가 정확히 대칭이다 — **`@Async`는 비동기를 숨겨서 코드를 단순하게 만들고, 그 숨김 때문에 어느 풀에서 도는지도 안 보인다.**

### self-invocation이 재현된다

같은 Bean 안에서 `@Async` 메서드를 직접 호출하면:

```
Test → 프록시 → callAsyncMethodFromSameBean()
              → this.sendOrderConfirmationEmailWithAsync()   ← 프록시 미경유
```

🔴 **실행 스레드가 "테스트 스레드"로 찍히고, 이미 완료된 `CompletableFuture`가 반환된다.** 비동기가 통째로 무시됐는데 **예외도 경고도 없다.** 반환 타입이 `CompletableFuture`라서 호출부는 정상으로 보인다.

### 언제 무엇을 쓰나

| 상황 | 선택 |
|---|---|
| 서비스 메서드 하나를 간단히 백그라운드로 | `@Async` |
| 메일·알림·후처리처럼 비즈니스 흐름에서 분리 가능 | `@Async` |
| 여러 작업의 제출·완료·조합을 직접 제어 | `ExecutorService` |
| Spring 프록시를 안 거치는 순수 Java 코드 | `ExecutorService` |
| **같은 클래스 내부에서 비동기 메서드를 호출해야 함** | `ExecutorService` 또는 **Bean 분리 후 `@Async`** |

## 해석

🟡 **마지막 줄이 실무 판단이다.** self-invocation 문제를 만나면 `ExecutorService`로 내려가거나 **Bean을 쪼갠다.** 후자가 대개 낫다 — 비동기로 돌려야 할 작업이라면 애초에 별도 협력 객체일 가능성이 높기 때문. 프록시 제약이 설계 압력으로 작용하는 사례다.

🔴 **이 함정은 `@Transactional`·`@Retryable`과 완전히 같다.** 전부 프록시 기반이고, 전부 조용히 실패한다 → [[프록시 자기호출 문제]]

💬 `@Async`가 조용히 동기로 도는 게 특히 나쁜 이유는 **테스트가 오히려 잘 통과하기 때문**이다. 동기 실행이면 결과가 즉시 있어서 타이밍 이슈가 없다. 운영에서 응답 시간이 안 줄어드는 걸로만 드러난다.

## 한계

🔴 **시간 수치가 없다.** 순차 → 병렬 전환 예제가 있지만 실측 비교표가 없어 "얼마나 줄었나"는 답할 수 없다.

🔴 **스레드 풀 설정을 다루지 않았다.** 코어/최대 크기, 큐 용량, 포화 정책(`RejectedExecutionHandler`)이 범위 밖이다. 기본 풀을 그대로 쓰면 운영에서 문제가 되는 지점인데 확인되지 않았다.

🔴 **예외 전파를 다루지 않았다.** `@Async`에서 던진 예외가 어디로 가는지(`AsyncUncaughtExceptionHandler`)는 없다.

🔴 트랜잭션 경계와 비동기의 상호작용이 없다 — 비동기 스레드에는 영속성 컨텍스트가 전파되지 않는다.

## 연결

- 개념: [[프록시 자기호출 문제]] 🔴 — 이 실험이 재현한 함정
- 개념: [[CompletableFuture]] · [[ExecutorService]] · [[스레드 풀 크기 결정]]
- 개념: [[재시도와 백오프]] — `@Retryable`도 같은 프록시 기반
- 개념: [[커밋 후 이벤트 발행]] — 후처리를 분리하는 다른 방식
- 코드: `~/Desktop/git/deep-dive/labs/spring/`
- 원본: `raw/code/spring.md`
