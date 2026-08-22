---
title: 원자적 UPDATE로 푸는 동시성
type: concept
status: growing
tags: [concurrency, sql, mysql, redis]
sources: ["[[deep-dive 실험실]]", "[[분산 트랜잭션 학습노트]]"]
moc: ["[[MOC-동시성]]", "[[MOC-데이터베이스]]"]
created: 2026-08-16
updated: 2026-08-16
---

## 한 줄 정의

🟡 **읽지 않고 쓴다.** 값을 가져와 계산하는 대신 조건과 연산을 한 문장에 담아, 애초에 끼어들 틈을 만들지 않는다.

## 왜 필요한가

[[Lost Update]]는 **읽고-계산하고-쓰는 세 걸음 사이의 틈**에서 생긴다. 락은 그 틈에 아무도 못 들어오게 막는 방식이고, 이건 **틈 자체를 없애는** 방식이다.

🟢 그래서 가장 싸다. 실험에서 원자적 UPDATE는 **369ms**로 비관적 락(429ms)·분산락(1312ms)·낙관적 락(3156ms)보다 빨랐고, Redis Lua 원자 차감은 **41ms**로 락 없음(163ms)보다도 빨랐다.

## 어떻게 동작하는가

```sql
UPDATE coupon
   SET quantity = quantity - 1
 WHERE id = 1 AND quantity > 0;
```

`quantity - 1`을 DB가 계산하므로 애플리케이션이 현재 값을 알 필요가 없다. `WHERE`에 재고 조건을 넣으면 **검사와 차감이 한 문장**이 된다.

성공 여부는 **영향받은 행 수**로 판정한다.

```java
int updated = repository.decrease(couponId);
if (updated == 0) throw new SoldOutException();   // 재고 없음 또는 이미 소진
```

Redis에서는 Lua 스크립트가 같은 역할을 한다 — 스크립트 전체가 원자적으로 실행된다.

## 코드에 닿는 지점

```java
@Modifying
@Query("update Coupon c set c.quantity = c.quantity - 1 " +
       "where c.id = :id and c.quantity > 0")
int decrease(@Param("id") Long id);
```

🔴 `@Modifying` 쿼리는 **영속성 컨텍스트를 우회한다.** 같은 트랜잭션에서 이미 로드한 엔티티는 옛 값을 들고 있으므로 `clearAutomatically = true`를 고려한다.

## 트레이드오프

| 쓸 때 | 안 쓸 때 |
|---|---|
| 갱신이 **현재 값에 대한 단순 연산** (증감·플래그) | 읽은 값으로 **복잡한 분기**를 해야 함 |
| 검사 조건을 `WHERE`에 담을 수 있음 | 여러 테이블에 걸친 규칙 |
| 최대 처리량이 필요함 | 도메인 로직이 엔티티 안에 있어야 함 |

🔴 **도메인 로직이 SQL로 새어 나간다.** `Product.buy()` 같은 엔티티 메서드에 있던 검증이 `WHERE` 절로 이사한다. 규칙이 늘면 SQL이 비대해지고 테스트하기 어려워진다 — [[테스트 가능한 설계란]]과 정면으로 충돌하는 지점이다.

🔴 **읽은 값을 응답에 실을 수 없다.** "몇 개 남았는지"를 돌려주려면 결국 다시 조회해야 한다.

🔴 **여러 자원에 걸치면 안 통한다.** 재고와 포인트를 동시에 다뤄야 하면 이 방법 하나로는 부족하고, [[TCC]]나 [[Saga 패턴]]으로 올라가야 한다.

💬 같은 아이디어를 **상태 전이**에 적용한 것이 [[조건부 상태 전이 선점]]이다 — `SET status='PROCESSING' WHERE status='PENDING'`. 값이 아니라 소유권을 원자적으로 가져온다.

## 연결

- [[Lost Update]] — 이 방법이 푸는 문제
- [[비관적 락]] · [[낙관적 락]] — 틈을 막는 쪽 vs 틈을 없애는 쪽
- [[조건부 상태 전이 선점]] — 같은 아이디어의 상태 전이 버전
- [[테스트 가능한 설계란]] 🔴 — 도메인 로직이 SQL로 새는 문제
- 실험: [[선착순 쿠폰 발급 동시성]] — 369ms / Redis Lua 41ms
- 면접: [[원자적 UPDATE로 풀 수 있는데 락이 필요한가]]
