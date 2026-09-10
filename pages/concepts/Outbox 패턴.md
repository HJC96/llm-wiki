---
title: Outbox 패턴
type: concept
status: growing
tags: [distributed-transaction, kafka, transaction, payment]
sources: ["[[결제 시스템 백엔드 학습 가이드]]", "[[트랜잭셔널 아웃박스 패턴 Q&A]]"]
moc: ["[[MOC-분산시스템]]", "[[MOC-결제시스템]]"]
created: 2026-08-31
updated: 2026-08-31
---

## 한 줄 정의

> 🟡 **"두 시스템에 원자적으로 쓰기"라는 불가능한 문제를, "한 DB 안의 두 테이블에 쓰기"로 바꿔 트랜잭션으로 푸는 것.**

발행할 이벤트를 비즈니스 데이터와 **같은 DB, 같은 트랜잭션**에서 outbox 테이블에 INSERT하고, 별도 Relay가 그걸 읽어 브로커로 내보낸다.

## 왜 필요한가

결제 승인 한 건이 해야 하는 일은 둘이다 — DB에 `SUCCESS` 저장, Kafka에 승인 이벤트 발행. 서로 다른 시스템이라 하나의 트랜잭션으로 묶을 수 없다. 이것이 [[Dual Write 문제]]다.

순진하게 짜면 어느 쪽을 먼저 해도 구멍이 난다.

| 순서 | 사고 |
|---|---|
| DB 커밋 → Kafka 발행 실패 | 결제는 성공인데 정산·배송이 영영 모른다 (**유실**) |
| Kafka 발행 → DB 롤백 | 세상에는 "결제 성공"이 퍼졌는데 DB엔 흔적이 없다 (**유령 배송, 잘못된 정산**) |

[[커밋 후 이벤트 발행]]은 두 번째 사고만 막는다. 커밋 직후 발행 직전에 프로세스가 죽으면 첫 번째 사고가 그대로 남는다. Outbox는 그 창(window)을 DB 안으로 끌고 들어와 없앤다.

## 어떻게 동작하는가

```
[Tx]  결제 상태 SUCCESS UPDATE
      + outbox INSERT (status = INIT)         ← 둘 다 커밋되거나 둘 다 사라진다
 ─────────────────────────────────────
      커밋 성공
 ─────────────────────────────────────
[Relay]  outbox 에서 미발행 행 조회 → Kafka 발행 → status = SUCCESS 마킹
```

Relay는 두 방식이 있고, 실무에서는 섞어 쓴다.

| 방식 | 장점 | 대가 |
|---|---|---|
| **Polling Publisher** | 구현이 단순 | 폴링 주기만큼 지연 + 대부분 빈 폴링인 DB 부하 |
| **CDC** (Debezium 등) | 지연·폴링 부하 없음 | 인프라 구성이 무겁다 |
| **하이브리드** — `AFTER_COMMIT` 즉시 발행 + 느긋한 스케줄러 | 정상 경로는 지연 ~0, 스케줄러는 안전망만 | 코드 경로가 둘로 늘어난다 |

> 🟢 하이브리드에서 각각의 역할이 다르다. 스케줄러 단독은 "느리지만 확실", `AFTER_COMMIT` 단독은 "빠르지만 유실 가능". 둘을 합쳐야 "빠르면서 유실도 없다"가 된다.

**Outbox 행이 들고 있어야 하는 것** — 상태(`INIT` / `PROCESSING` / `RETRY_WAIT` / `SUCCESS` / `DEAD`), 재시도 정보(`attempts`, `next_retry_at`, `last_error`), 동시 실행 제어(`locked_by`/`locked_at` 또는 `SKIP LOCKED`), 감사(`event_id`, `aggregate_id`, `correlation_id`), 호환성(`event_type`, `schema_version`, `payload`).

## 코드에 닿는 지점

```java
@Transactional
public void confirmSuccess(PaymentOrder order, PaymentEvent event) {
    paymentRepository.updateStatus(order.id(), SUCCESS);
    outboxRepository.insert(PaymentOutbox.init(event));   // ← 같은 트랜잭션
}

// 커밋된 뒤에만 발행을 시도한다. 실패해도 outbox 행은 남아 스케줄러가 줍는다.
@TransactionalEventListener(phase = AFTER_COMMIT)
public void publish(PaymentApprovedEvent e) { ... }
```

> 🔴 **outbox INSERT를 `AFTER_COMMIT`으로 빼면 패턴의 유일한 이득이 사라진다.** "DB 쓰기도 실패할 수 있으니 분리했다"는 논리는 성립하지 않는다 — 같은 DB·같은 트랜잭션의 INSERT는 비즈니스 UPDATE와 운명공동체다. 커넥션이 죽으면 결제도 커밋 못 하고, 제약 위반이면 어디에 두든 터진다. 반대로 커밋 직후 죽으면 **재시도할 대상 자체가 없어서** 이벤트가 조용히 증발한다.

## 트레이드오프

| 쓸 때 | 안 쓸 때 |
|---|---|
| 이벤트 유실이 곧 돈·정합성 사고인 경우 (결제, 정산, 재고) | 이벤트가 가끔 유실돼도 되는 best-effort 알림 — 그럴 거면 `@Async` fire-and-forget이 더 단순하다 |
| DB와 브로커가 서로 다른 시스템일 때 | outbox 테이블이 비즈니스 DB와 **물리적으로 다른 DB**일 때 — 그건 진짜 dual write라 패턴이 성립하지 않는다 |

대가는 셋이다. ① **Exactly-once가 아니다** — 발행 성공 후 `SUCCESS` 마킹 전에 죽으면 다음 폴링에 또 나간다. 소비자 쪽 [[Inbox 패턴]]이나 고유 제약이 반드시 따라붙는다. ② **테이블이 계속 커진다** — 보존·아카이빙·파티셔닝 정책이 필요하다. ③ **독약 메시지** — 무한 재시도를 두면 같은 행이 폴링을 계속 잡아먹는다. `attempts` 상한과 `DEAD` 상태로 빼야 한다.

## 연결

- [[Dual Write 문제]] — Outbox가 푸는 문제 그 자체
- [[커밋 후 이벤트 발행]] — 사고의 절반만 막는 앞 단계. Outbox는 그 나머지 절반
- [[Inbox 패턴]] — Producer 쪽 유실을 막은 대가로 생긴 Consumer 쪽 중복을 받는다
- [[정확히 한 번 전달의 불가능성]] — Outbox가 at-least-once에 머무는 이유
- [[멱등성]] — 중복 발행이 무해해지려면 소비자가 멱등해야 한다
- [[조건부 상태 전이 선점]] — 여러 Relay가 같은 행을 집지 않게 하는 방법
- [[분산 트랜잭션 네 가지 비교]] — 2PC·TCC·Saga 옆의 다섯 번째 선택지
- 실무 적용 기록 → `pages/private/` — MQ 없이 발송 요청 테이블만으로 같은 목적을 달성한 사례
