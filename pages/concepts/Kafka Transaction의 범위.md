---
title: Kafka Transaction의 범위
type: concept
status: growing
tags: [kafka, distributed-transaction, transaction, consistency]
sources: ["[[결제 시스템 백엔드 학습 가이드]]"]
moc: ["[[MOC-분산시스템]]"]
created: 2026-08-31
updated: 2026-08-31
---

## 한 줄 정의

> 🟡 **Kafka Transaction이 원자적으로 묶는 것은 "Kafka 입력 오프셋 + Kafka 출력 메시지"뿐이다.** 그 트랜잭션에 외부 DB는 들어오지 않는다.

## 왜 필요한가

"Kafka EOS(exactly-once semantics)를 켰으니 중복 걱정 없다"는 결론이 가장 흔한 오해다. Wallet 서비스가 하는 일은 셋인데,

```
① Kafka 에서 승인 이벤트 읽기        ┐
② MySQL 에 잔액 반영                 │ ← ②는 Kafka 트랜잭션 밖이다
③ Kafka 로 완료 이벤트 발행          ┘
```

Kafka Transaction은 ①과 ③만 묶는다. ②가 커밋된 뒤 ③ 커밋 전에 죽으면 잔액은 반영됐는데 오프셋은 안 올라가고, 재처리 시 **잔액이 두 번 오른다.** 이것은 여전히 [[Dual Write 문제]]다.

## 어떻게 동작하는가

Kafka 쪽 메커니즘 자체는 제대로 동작한다.

- **Transaction Coordinator** — 트랜잭션 상태를 관리하는 브로커 역할
- **`transactional.id`** — Producer 세션을 식별한다. 같은 id로 새 Producer가 뜨면 이전 것은 **fencing**되어 더 이상 쓰지 못한다(Zombie Producer 차단)
- **`sendOffsetsToTransaction`** — 입력 오프셋 커밋을 출력 메시지와 같은 트랜잭션에 넣는다
- **`isolation.level=read_committed`** — 커밋된 트랜잭션의 메시지만 소비한다

이 조합이 주는 것은 **read-process-write가 Kafka 안에서만 원자적**이라는 성질이다.

> 🔴 `transactionIdPrefix`는 **인스턴스마다 고유해야 한다.** 같은 값을 쓰면 두 인스턴스가 서로를 fencing해서 정상 처리도 멈춘다.

> 🔴 `transaction.timeout.ms`와 `max.poll.interval.ms`, 실제 처리 시간의 관계를 안 맞추면 정상 처리가 중단된다. 처리가 트랜잭션 타임아웃을 넘기면 코디네이터가 그 트랜잭션을 abort시킨다.

## 코드에 닿는 지점

DB까지 포함해야 한다면 선택지는 셋이다.

| 방법 | 내용 |
|---|---|
| **Inbox + 비즈니스 변경 + Outbox를 한 DB 트랜잭션에** | 가장 명시적. Kafka 트랜잭션이 없어도 성립한다 |
| **멱등 설계 + 상태 복구** | 중복 실행돼도 결과가 같게 만든다 |
| Chained Transaction | 가능하지만 장애 창과 커밋 순서를 정확히 이해하고 보상 수단을 둬야 한다 |

🟢 첫 번째가 기본값이다. Kafka 트랜잭션을 안 켜도 [[Inbox 패턴]]과 [[Outbox 패턴]]만으로 필요한 보장이 나오고, 설정 복잡도도 낮다.

## 트레이드오프

| 켤 때 | 안 켤 때 |
|---|---|
| Kafka → Kafka 스트림 처리 (Kafka Streams, 집계·조인) | 처리 중간에 외부 DB가 끼는 일반적인 컨슈머 |
| 출력이 여러 토픽·파티션에 걸쳐 원자적이어야 할 때 | Inbox/Outbox로 이미 멱등이 보장될 때 |

대가 — 처리량 저하, `read_committed` 컨슈머의 지연 증가, 그리고 **"exactly-once를 켰다"는 잘못된 안도감**.

## 연결

- [[Dual Write 문제]] — Kafka 트랜잭션이 못 닫는 그 창
- [[Inbox 패턴]] · [[Outbox 패턴]] — DB까지 포함하는 실제 해법
- [[정확히 한 번 전달의 불가능성]] — EOS라는 말의 범위를 정확히 읽는 법
- [[Kafka 전달 보장]] — idempotent producer가 지우는 중복의 범위
