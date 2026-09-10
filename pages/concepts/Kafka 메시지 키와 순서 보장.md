---
title: Kafka 메시지 키와 순서 보장
type: concept
status: growing
tags: [kafka, distributed, concurrency]
sources: ["[[분산 트랜잭션 학습노트]]", "[[결제 시스템 백엔드 학습 가이드]]"]
moc: ["[[MOC-분산시스템]]"]
created: 2026-08-15
updated: 2026-08-31
---

## 한 줄 정의

🟡 순서는 **토픽이 아니라 파티션 단위로만** 보장된다. 순서를 지켜야 하는 단위를 메시지 키로 잡아 같은 파티션에 몰아야 한다.

## 왜 필요한가

[[Saga 패턴]]의 Choreography에는 **코디네이터도 [[Redis 분산락]]도 없다.** 같은 주문의 이벤트가 동시에 두 번 처리되면 안 되는데, 그 보장이 어디서도 나오지 않는다.

이 보장은 카프카에서 와야 한다.

## 어떻게 동작하는가

```java
kafkaTemplate.send("order-placed",
                   String.valueOf(event.orderId()),   // ← 메시지 키 = orderId
                   event);
```

🟡 카프카는 **메시지 키가 같으면 같은 파티션으로 라우팅**하고, 한 파티션은 컨슈머 그룹 안에서 **하나의 컨슈머만** 읽는다. 키를 `orderId`로 두면 같은 주문의 이벤트가 **순서대로, 동시에 단 하나씩만** 처리된다.

순서 보장과 동시 처리 차단이 **같은 메커니즘에서 한꺼번에** 나온다는 것이 요점이다.

## 코드에 닿는 지점

역직렬화에서 한 번 걸린다. 발행 측 `JsonSerializer`는 자기 클래스의 FQCN을 타입 헤더에 실어 보내는데, **구독하는 서비스는 패키지 구조가 달라서 그 클래스를 찾지 못한다.**

```java
@KafkaListener(
    topics = "order-placed",
    groupId = "order-placed-consumer",
    properties = "spring.json.value.default.type=com.example.product.consumer.dto.OrderPlacedEvent"
)
public void handle(OrderPlacedEvent event) { ... }
```

`spring.json.use.type.headers`를 끄고 **수신 측이** 변환 대상 타입을 결정하게 만든다. `spring.json.trusted.packages`도 함께 열어 준다.

## 트레이드오프

🔴 **파티션을 늘리면 키 해싱 대상이 바뀌어 기존 키의 파티션 배치가 흐트러진다.** 순서 보장이 필요한 토픽은 파티션 수를 함부로 바꾸지 않는다. → 처리량 확장과 순서 보장이 정면으로 충돌한다.

🔴 키를 잡으면 그 키에 **핫스팟**이 생길 수 있다. 특정 주문/사용자에 이벤트가 몰리면 한 파티션만 밀린다.

🔴 전달은 **at-least-once**다. 컨슈머가 실패하면 카프카가 다시 전달하므로 **컨슈머는 반드시 [[멱등성]]**을 갖춰야 한다. 오프셋 커밋과 처리의 순서 때문 — 처리 후 커밋이면 중복, 커밋 후 처리면 유실.

💬 "키를 넣으면 순서가 보장됩니다"는 맞지만 **왜**(같은 파티션 → 단일 컨슈머 → 순차 처리)가 빠지면 외운 답으로 들린다.

## 연결

- [[Saga 패턴]] — Choreography의 사고 지점 ②
- [[멱등성]] — at-least-once의 유일한 방어선
- [[커밋 후 이벤트 발행]] — 사고 지점 ①
- [[Kafka 전달 보장]] · [[컨슈머 그룹과 리밸런싱]]
- [[정확히 한 번 전달의 불가능성]]
- 면접: [[Kafka에서 순서 보장은 어떻게 하나]]
- [[Kafka 전달 보장]] — acks·오프셋 커밋 시점이 정하는 유실/중복 경계
- [[컨슈머 그룹과 리밸런싱]] — 파티션 할당이 병렬성과 순서 범위를 동시에 정한다
