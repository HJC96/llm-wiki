---
title: Inbox 패턴
type: concept
status: growing
tags: [distributed-transaction, kafka, payment, consistency]
sources: ["[[결제 시스템 백엔드 학습 가이드]]"]
moc: ["[[MOC-분산시스템]]", "[[MOC-결제시스템]]"]
created: 2026-08-31
updated: 2026-08-31
---

## 한 줄 정의

> 🟡 **소비한 `event_id`를 고유 제약이 걸린 테이블에 기록해, 같은 메시지를 두 번 받아도 두 번째는 아무 일도 일어나지 않게 만드는 것.**

[[Outbox 패턴]]이 Producer의 **유실**을 다룬다면, Inbox는 Consumer의 **중복 실행**을 다룬다. 둘은 짝이다.

## 왜 필요한가

Outbox Relay는 발행 성공 후 상태 마킹 전에 죽을 수 있고, Kafka 컨슈머는 처리 후 오프셋 커밋 전에 죽을 수 있다. 어느 쪽이든 결과는 같다 — **같은 승인 이벤트가 두 번 도착한다.** 그대로 처리하면 판매자 지갑에 정산금이 두 번 들어간다.

> ⚠️ **충돌** (2026-08-31): [[외래키 제약과 락 경합]]은 정반대로 `idempotency_key`의 UNIQUE를 **빼라**고 한다 — 유니크 인덱스 INSERT가 거는 갭락이 동시 정산의 데드락 원인이 되기 때문. 현재 판단: **조건이 갈린다.** 같은 부모 행에 INSERT와 UPDATE가 함께 몰리는 정산 경로에서는 제약을 빼고 앱에서 막고, 그렇지 않은 일반 컨슈머에서는 고유 제약이 더 안전하다. 🔴 볼트에 그 락 경합 실측치가 없으므로 어느 쪽도 일반 규칙으로 승격하지 않는다.

> 🔴 사전 SELECT로 "이미 처리했나" 확인하는 것만으로는 못 막는다. 두 컨슈머가 동시에 SELECT를 통과한 뒤 둘 다 INSERT한다. **고유 제약과 INSERT 충돌을 최종 판정으로 써야** 경쟁 조건이 닫힌다.

## 어떻게 동작하는가

핵심은 Inbox 기록과 비즈니스 변경이 **같은 DB 트랜잭션**이라는 것이다. 따로 커밋하면 그 사이에서 다시 [[Dual Write 문제]]가 생긴다.

```
[Wallet DB Tx]
  1. INSERT INTO processed_events(event_id) ...   ← UNIQUE 위반이면 여기서 끝. 이미 처리한 것
  2. INSERT INTO wallet_transactions ...
  3. UPDATE wallets SET balance = ... WHERE version = ?
  4. INSERT INTO outbox (완료 이벤트)
커밋
```

> 🟢 중복 메시지를 받았을 때 **잔액 반영은 건너뛰되 완료 이벤트는 다시 발행**하는 설계가 유용하다. 상위 Payment Service가 완료 이벤트를 놓쳤을 때 이게 복구 경로가 된다. 물론 그 완료 이벤트도 멱등해야 한다.

## 코드에 닿는 지점

```sql
CREATE TABLE processed_events (
    event_id   VARCHAR(64) NOT NULL,
    consumer   VARCHAR(64) NOT NULL,
    created_at DATETIME    NOT NULL,
    PRIMARY KEY (consumer, event_id)     -- 컨슈머마다 따로 세야 한다
);
```

`consumer`를 키에 넣는 이유 — Wallet과 Ledger는 같은 `payment-approved` 이벤트를 각자 한 번씩 처리해야 한다. `event_id`만 유일하게 하면 나중에 붙은 컨슈머가 첫 컨슈머의 기록에 막힌다.

## 트레이드오프

| 쓸 때 | 안 쓸 때 |
|---|---|
| 처리가 **자연스럽게 멱등하지 않을 때** — 잔액 증감, 카운터, 이벤트 재발행 | 처리 자체가 멱등할 때 — `SET status = 'DONE'` 같은 덮어쓰기는 몇 번 해도 같다 |
| 중복 판정 근거를 감사 로그로 남겨야 할 때 | 비즈니스 테이블에 이미 자연 고유키가 있을 때 (`order_id` UNIQUE) — 그게 곧 Inbox다 |

대가: 테이블이 무한히 커진다. 보존 기간(예: 30일)을 정하고 파티션 드롭으로 지운다. 단, **보존 기간보다 늦게 도착한 중복은 막지 못한다** — DLQ에서 한 달 뒤 재처리하는 경로가 있다면 그 상호작용을 확인해야 한다.

## 연결

- [[Outbox 패턴]] — 짝. Outbox의 at-least-once가 Inbox를 필수로 만든다
- [[멱등성]] — Inbox는 멱등성을 구현하는 여러 방법 중 "기록으로 판정하는" 방식
- [[정확히 한 번 전달의 불가능성]] — Inbox가 존재해야 하는 근본 이유
- [[낙관적 락]] — Inbox 트랜잭션 안에서 잔액 갱신을 지키는 짝
- [[Kafka Transaction의 범위]] — Kafka만으로는 이 문제를 못 닫는 이유
