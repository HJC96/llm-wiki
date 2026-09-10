---
title: 컨슈머 재시도와 DLQ
type: concept
status: growing
tags: [kafka, retry, distributed-transaction, observability]
sources: ["[[결제 시스템 백엔드 학습 가이드]]"]
moc: ["[[MOC-분산시스템]]"]
created: 2026-08-31
updated: 2026-08-31
---

## 한 줄 정의

> 🟡 **회복 가능한 실패는 지연 재시도로 흘려보내고, 계속 실패하는 메시지는 정상 흐름에서 격리한다.** 목적은 재처리가 아니라 **한 건이 파티션 전체를 막지 못하게** 하는 것이다.

## 왜 필요한가

Kafka 파티션은 순서 큐다. 앞의 메시지 하나가 계속 실패하면 뒤의 정상 메시지가 **전부 대기한다.** 이것이 **Poison Pill** — 역직렬화 실패나 항상 예외가 나는 메시지가 파티션을 통째로 세우는 현상이다.

컨슈머 안에서 즉시 재시도하는 것도 답이 아니다. 그 시간만큼 `poll()`이 늦어져 `max.poll.interval.ms`를 넘기고 [[컨슈머 그룹과 리밸런싱]]을 유발한다.

## 어떻게 동작하는가

```
payment-approved
    │ 처리 실패 (일시)
    ▼
payment-approved.retry-1   (5s 지연 후 재처리)
    │ 또 실패
    ▼
payment-approved.retry-2   (30s)
    │ 한도 초과
    ▼
payment-approved.DLQ       ← 정상 흐름에서 격리. 여기서 사람이 본다
    │ 원인 해결 후
    ▼
Parking Lot / 원본 토픽으로 Replay
```

> 🔴 **DLQ는 삭제 장소가 아니다.** 원본 topic·partition·offset, key, event id, exception, stack trace, retry count, 최초·최종 실패 시각을 함께 보존해야 나중에 재처리할 수 있다. 그냥 메시지 본문만 넣으면 그건 쓰레기통이다.

🟢 DLQ 파티션 수는 원본과 맞춰 두는 게 낫다. 파티션 정보를 유지해야 재처리 시 같은 키의 순서를 되살릴 수 있다.

## 코드에 닿는 지점

```yaml
spring.cloud.stream.bindings.paymentApproved-in-0.consumer:
  max-attempts: 3            # maxAtttempts 아님
  back-off-initial-interval: 1000
  back-off-multiplier: 2.0   # backOffMultipler 아님
spring.cloud.stream.kafka.bindings.paymentApproved-in-0.consumer:
  enable-dlq: true
  dlq-name: payment-approved.dlq
```

> 🔴 Binder의 **Transactional 모드에서는 일반 DLQ 설정과 다른 오류 처리 경로**가 적용될 수 있다. `AfterRollbackProcessor` 쪽이 관여하므로 사용 중인 Spring Cloud Stream 버전 문서를 확인해야 한다.

## 트레이드오프

| 지연 토픽을 둘 때 | 컨슈머 안에서 재시도할 때 |
|---|---|
| 재시도 간격이 초 이상일 때 | 밀리초 단위 즉시 재시도로 충분할 때 |
| 뒤의 메시지를 막으면 안 될 때 | 순서가 절대적이라 건너뛰면 안 될 때 |

대가 — 토픽이 늘어나고, **같은 키의 순서가 깨진다.** retry 토픽으로 빠진 메시지는 원본에서 뒤따라오던 같은 키의 메시지보다 늦게 처리된다. 순서가 정합성에 필요한 도메인이면 이 방식 자체를 다시 봐야 한다.

## 연결

- [[재시도와 백오프]] — 무엇을 재시도 후보로 볼 것인가
- [[컨슈머 그룹과 리밸런싱]] — 컨슈머 안 재시도가 리밸런싱을 부르는 경로
- [[실패 사실의 기록]] — DLQ는 "자동 복구를 못 해도 유실은 막는다"의 구현
- [[Bulkhead]] — 실패 격리의 같은 사고방식
- [[Outbox 패턴]] — 발행 쪽의 `DEAD` 상태가 DLQ와 같은 역할
