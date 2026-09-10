---
title: Kafka 전달 보장
type: concept
status: growing
tags: [kafka, distributed-transaction, consistency]
sources: ["[[결제 시스템 백엔드 학습 가이드]]"]
moc: ["[[MOC-분산시스템]]"]
created: 2026-08-31
updated: 2026-08-31
---

## 한 줄 정의

> 🟡 **유실과 중복의 경계는 세 개의 설정이 정한다 — Producer의 `acks`, Broker의 `min.insync.replicas`, Consumer의 오프셋 커밋 시점.** 셋 중 하나만 잘못 잡혀도 나머지가 무의미해진다.

## 왜 필요한가

"Kafka는 복제하니까 안전하다"는 절반만 맞다. Replication은 **브로커 장애 내성**을 높일 뿐, 프로듀서가 응답을 언제 받는지와 컨슈머가 오프셋을 언제 커밋하는지가 실제 유실 지점을 결정한다.

## 어떻게 동작하는가

### Producer — 언제 "성공"이라고 답할 것인가

| `acks` | 성공 판정 시점 | 유실 |
|---|---|---|
| `0` | 보내기만 하면 | 리더가 죽으면 통째로 유실 |
| `1` | 리더가 로그에 쓰면 | 리더가 팔로워 복제 전에 죽으면 유실 |
| **`all`** | ISR의 `min.insync.replicas`만큼 복제되면 | 사실상 없음. 대신 지연 증가 |

> 🔴 `acks=all`만 켜고 `min.insync.replicas=1`이면 사실상 `acks=1`이다. **둘은 세트다.** RF=3 / `min.insync.replicas=2`가 흔한 조합이고, 이 경우 브로커 1대 장애까지 쓰기를 계속할 수 있다.

관련 설정 셋:
- `enable.idempotence=true` — Producer **재시도로 생기는 브로커 로그 내 중복**을 제거한다
- `delivery.timeout.ms` — 한 레코드가 성공·실패로 확정되기까지의 총 시간 상한
- `max.in.flight.requests.per.connection` — 재시도 중 순서 보장과 처리량의 균형

### Consumer — 오프셋을 언제 커밋할 것인가

```
auto-commit ON:   poll → (백그라운드 커밋) → 비즈니스 처리 → 죽음  ⇒ 유실
manual commit :   poll → 비즈니스 처리 → DB 커밋 → 오프셋 커밋 → 죽음  ⇒ 중복
```

> 🟡 금전 처리에서는 **DB 반영 전에 오프셋이 커밋되는 경로를 막는다.** 중복은 [[Inbox 패턴]]으로 무해하게 만들 수 있지만 유실은 되돌릴 수 없다. auto-commit이 항상 잘못은 아니지만 이 경로에서는 아니다.

`auto.offset.reset`은 저장된 오프셋이 없거나 유효하지 않을 때만 쓰인다. 🟢 최신 Kafka 문서 기준 기본값은 `latest`이며 버전에 따라 달랐던 이력이 있으니 사용 버전의 공식 문서로 확인한다.

## 코드에 닿는 지점

```yaml
spring.kafka:
  producer:
    acks: all
    properties:
      enable.idempotence: true
      delivery.timeout.ms: 120000        # deliver.timeout.ms 아님
  consumer:
    enable-auto-commit: false
    properties:
      isolation.level: read_committed
```

> 🔴 원문 자료의 `deliver.timeout.ms`, `fetch.message.max.bytes`는 현행 설정명이 아니다. 각각 **`delivery.timeout.ms`**, **`max.partition.fetch.bytes` / `fetch.max.bytes`** 다.

## 트레이드오프

| `acks=all` + manual commit | `acks=1` + auto-commit |
|---|---|
| 금전·주문·재고 — 유실이 곧 사고 | 로그 수집, 메트릭, 클릭 스트림 |
| 지연과 처리량을 내주고 내구성을 산다 | 처리량이 우선이고 일부 유실을 감수한다 |

## 연결

- [[정확히 한 번 전달의 불가능성]] — Kafka도 예외가 아닌 이유
- [[Kafka Transaction의 범위]] — idempotent producer가 지우지 못하는 중복
- [[컨슈머 그룹과 리밸런싱]] — 오프셋 커밋 시점이 리밸런싱과 만나는 지점
- [[Inbox 패턴]] — 중복을 받아 내는 쪽
- [[Kafka 메시지 키와 순서 보장]] — 파티션 단위 순서
- 실험: [[좌석 예약 동시성]] — Kafka 버퍼링으로 실패 88건 → 0건
