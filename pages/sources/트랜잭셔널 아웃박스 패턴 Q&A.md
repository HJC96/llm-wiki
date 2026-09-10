---
title: 트랜잭셔널 아웃박스 패턴 Q&A
type: source
kind: 대화
status: growing
tags: [distributed-transaction, kafka, transaction, payment]
moc: ["[[MOC-출처]]", "[[MOC-결제시스템]]", "[[MOC-분산시스템]]"]
created: 2026-08-31
updated: 2026-08-31
---

## 무엇

payment-service의 결제 이벤트 발행 코드를 보면서 주고받은 문답 6개. "왜 커밋까지 지연시키나"에서 시작해 "outbox INSERT를 `AFTER_COMMIT`으로 빼면 잘못인가"까지 간다.

## 핵심 주장

1. `AFTER_COMMIT` 발행이 막는 것은 **DB 롤백인데 이벤트는 나간** 사고 하나뿐이다. 커밋 후 발행 전 죽는 경로는 그대로 남는다.
2. Outbox는 "Kafka 대신 남기는 것"이 아니라 **"Kafka로 보내야 할 목록을 DB에 안전하게 적어 둔 대기열"** 이다.
3. 정통 Outbox(테이블 + 스케줄러 폴링)에 `AFTER_COMMIT` 즉시 발행을 얹은 **하이브리드**가 실무 형태다. 스케줄러 단독은 느리지만 확실, `AFTER_COMMIT` 단독은 빠르지만 유실 가능.
4. at-least-once는 "성공으로 마킹될 때까지 재시도"로 구현된다. 무한 재시도는 독약 메시지를 만들므로 `attempts` 상한과 `FAILURE`/`DEAD` 상태가 필요하다.
5. **outbox INSERT를 결제 트랜잭션 밖으로 빼면 패턴의 유일한 이득이 사라진다.** 같은 DB·같은 트랜잭션의 INSERT는 비즈니스 UPDATE와 운명공동체라서 "outbox만 실패해서 결제를 망친다"는 시나리오가 사실상 없다.

## 여기서 나온 페이지

| 페이지 | 무엇을 가져갔나 |
|---|---|
| [[Outbox 패턴]] | 하이브리드 Relay의 역할 분담, `AFTER_COMMIT` INSERT 반례, `SENT` 마킹과 재시도 |
| [[Dual Write 문제]] | 순서를 바꿔도 사고가 이동만 하는 구조 |

## 기존 위키와의 관계

- **보강**: [[커밋 후 이벤트 발행]] — 기존 페이지는 `AFTER_COMMIT`의 유실 창을 표로만 언급했는데, 이 소스가 "왜 그 창이 남는가"와 "outbox INSERT의 위치가 그 창을 결정한다"를 구체화했다
- **⚠️ 대조 항목**: 비공개 실무 기록과 대조할 항목으로 표시했다

## 아직 안 다룬 것

- CDC(Debezium) 방식 — 이름만 언급하고 "인프라가 무겁다"로 끝났다
- 여러 Relay 인스턴스의 동시 집기(Lease / `SKIP LOCKED`) — [[결제 시스템 백엔드 학습 가이드]] 쪽에서 보충했다
- outbox 테이블 보존·아카이빙 정책의 구체적 수치

## 원본

`raw/code/deep-dive-transactional-outbox-pattern.md`
