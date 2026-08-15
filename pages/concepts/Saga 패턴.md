---
title: Saga 패턴
type: concept
status: growing
tags: [distributed-transaction, transaction, kafka]
sources: ["[[분산 트랜잭션 학습노트]]"]
moc: ["[[MOC-분산시스템]]"]
created: 2026-08-15
updated: 2026-08-15
---

## 한 줄 정의

🟡 예약 없이 **즉시 실행하고, 실패하면 반대 방향 갱신(보상 트랜잭션)으로 되돌린다.** 목표는 [[최종적 일관성]].

## 왜 필요한가

[[TCC]]는 예약-확정 2단계라 API가 세 벌(try/confirm/cancel) 필요하고, 예약 수량 컬럼 같은 부가 상태도 들고 있어야 한다. Saga는 그 단계를 없앤다 — 그냥 차감하고, 실패하면 다시 늘린다.

| | TCC | Saga |
|---|---|---|
| 재고 차감 | 예약 → 확정 (2단계) | **즉시 차감** (1단계) |
| 실패 시 | 예약 취소 (아직 안 줄었음) | 보상 (**줄인 것을 다시 늘림**) |
| 중간 상태 | 예약됨 — 남에게 안 보임 | 차감됨 — **남에게 이미 보임** |

🔴 대가가 여기 있다. **"최종적으로 맞으니 괜찮다"가 아니라 불일치 구간이 외부에 노출된다는 것**이 대가다. TCC의 "예약됨"은 남이 사지 못하게 막을 뿐 재고 숫자를 바꾸지 않지만, Saga에서 차감된 재고는 다른 사용자에게 그대로 보인다. **보상 전까지 그 재고는 아무도 살 수 없었던 재고다.**

## 어떻게 동작하는가

### Orchestration — 코디네이터가 흐름을 쥔다

```java
public void placeOrder(PlaceOrderCommand command) {
    orderService.request(command.orderId());
    try {
        ProductBuyResponse bought = productApiClient.buy(...);
        pointApiClient.use(...);
        orderService.complete(command.orderId());
    } catch (Exception e) {
        ProductCancelResponse canceled = productApiClient.cancel(...);
        if (canceled.totalPrice() > 0) {          // ← 재고가 실제로 빠졌을 때만
            pointApiClient.cancel(...);
        }
        orderService.fail(command.orderId());
    }
}
```

🟡 **보상 API는 "취소할 것이 없는 상태"를 정상으로 취급해야 한다.** 처음엔 이력이 없으면 예외를 던지게 짰는데, 그러면 재고 차감 단계에서 실패했을 때 보상 호출이 곧바로 예외로 튄다. 0원(또는 즉시 리턴)을 내려보내도록 고친다 — [[멱등성]]을 보상 쪽에 적용한 것.

🔴 이 `try-catch` 구조는 함정과 맞닿는다. 코디네이터 메서드에 `@Transactional`을 붙여 두면 **안쪽에서 예외를 삼켰으니 롤백 신호가 프록시에 도달하지 않는다.** 분산 트랜잭션의 보상은 로컬 롤백과 층위가 다르다 — **코디네이터는 트랜잭션 경계 밖에 있어야 한다.**

### Choreography — 이벤트가 흐름을 만든다

코디네이터가 없다. 각 서비스가 이벤트를 발행·구독하며 흐름이 저절로 이어진다.

| 발행 | 토픽 | 구독 | 하는 일 |
|---|---|---|---|
| Order | `order-placed` | Product | 재고 차감 |
| Product | `quantity-decreased` | Point | 포인트 차감 |
| Point | `point-used` | Order | 주문 완료 |
| Point | `point-use-fail` | Product | 재고 되돌리고 실패 이벤트 발행 |
| Product | `quantity-decreased-fail` | Order | 주문 실패 처리 |

🟡 Choreography는 **결합도를 낮추는 대신 흐름의 가시성을 내준다.** Product는 Order를 모르고 토픽만 안다. 그 대가로 전체 흐름을 알려면 컨슈머 다섯 개를 찾아다니며 머릿속에서 이어 붙여야 한다.

🟢 보상 경로가 정상 경로와 **같은 메커니즘 위에** 있어서 별도 재시도 장치가 필요 없다. 컨슈머가 실패하면 카프카가 다시 전달한다.

🔴 다시 전달한다는 건 **같은 이벤트가 두 번 처리될 수 있다**는 뜻이다(at-least-once). 여기엔 코디네이터도 Redis 락도 없다. **이력 테이블 기반 멱등성이 선택이 아니라 유일한 방어선이다.**

## 코드에 닿는 지점

Saga에는 예약 테이블이 없으니 대신 **처리 이력 테이블**을 둔다.

🟡 이력 테이블은 **멱등성의 판정 근거이자 보상의 복원 근거**다. "이미 처리했는가"를 판정하고, 보상할 때 "무엇을 얼마나 되돌려야 하는가"를 알려 준다.

🟢 취소 시 이력을 지우지 않고 **행을 추가**하는 게 중요하다. 구매 행과 취소 행이 둘 다 남으므로 "처리됐다가 되돌려졌다"는 사실이 보존되고, 같은 취소 요청이 또 와도 취소 행의 존재만 보면 판정이 끝난다.

🔴 [[낙관적 락]]은 Saga에서도 필요하다. 이력 테이블이 있어도 `quantity`를 읽고-쓰는 구간은 그대로라 [[Lost Update]]가 그대로 일어난다.

## 트레이드오프

🔴 "실무에서 많이 쓴다"를 선택 기준으로 오해하면 안 된다. Saga Orchestration이 많이 쓰이는 이유는 우월해서가 아니라 **대부분의 서비스가 최종적 일관성을 감당할 수 있기 때문**이다. 결제처럼 감당할 수 없는 영역에서는 여전히 TCC를 쓴다.

| | Orchestration | Choreography |
|---|---|---|
| 흐름 파악 | 쉬움 (한 곳만 보면 됨) | **어려움** |
| 결합도 | 높음 | **낮음** |
| 인프라 | HTTP + DB | 메시지 브로커 |
| 클라이언트 응답 | 동기 | **비동기 + 폴링** |

기본은 Orchestration. 처리 시간이 길어 동기 응답이 곤란하거나 참여자가 계속 늘어나면 Choreography.

## 연결

- [[TCC]] — 예약으로 중간 상태를 숨기는 쪽
- [[2PC]] — DB에게 맡기는 쪽
- [[최종적 일관성]] — Saga가 목표하는 일관성 모델
- [[멱등성]] — 보상 트랜잭션도 멱등해야 한다
- [[커밋 후 이벤트 발행]] — Choreography 사고 지점 ①
- [[Kafka 메시지 키와 순서 보장]] — 사고 지점 ②
- [[실패 사실의 기록]] — 보상마저 실패했을 때
- [[분산 트랜잭션 네 가지 비교]]
- 면접: [[Saga 오케스트레이션과 코레오그래피 중 무엇을]]
