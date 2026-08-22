---
title: 낙관적 락과 Hibernate SQL 관찰
type: lab
status: growing
tags: [jpa, lock, hibernate]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-실험]]", "[[MOC-Spring]]"]
repo: deep-dive/labs/spring-data-jpa
created: 2026-08-16
updated: 2026-08-16
---

## 확인하려던 것

`@Version` 한 줄이 **실제로 어떤 SQL을 만들고**, 충돌이 어느 시점에 어떤 예외로 드러나는가.

## 실험 설계

- Spring Data JPA + `Product` 엔티티에 `@Version`
- 세 케이스: 버전 자동 증가 / 충돌 없는 저장(대조군) / **옛 스냅샷 저장 → 충돌**
- 쿼리 카운트를 Micrometer 메트릭으로 발행

## 결과

### 버전은 커밋마다 오른다

```text
INSERT(version = 0) → 수정 커밋마다 UPDATE ... SET version = version + 1
```

```java
Long id = productService.create("키보드", 10);   // version 0
productService.decreaseStock(id);                // version 1
productService.decreaseStock(id);                // version 2
```

단언: `isEqualTo(0L)` → `isEqualTo(1L)` → `isEqualTo(2L)`

### 옛 스냅샷은 거부된다

```text
A가 SELECT(version 0)
  → B가 먼저 수정 커밋(version 0 → 1)
  → A가 옛 스냅샷으로 saveAndFlush
  → UPDATE ... WHERE version = 0 → affected rows = 0
  → ObjectOptimisticLockingFailureException
```

🟢 **최종 상태가 결론이다** — `stock = 9`, `version = 1`. A까지 반영됐다면 `stock = 8`이었을 것이다. 🟡 **먼저 커밋한 쪽(B)이 이기고 나중 쪽(A)이 실패한다** → [[Lost Update]] 방지.

🟢 JPA가 하는 판정은 단순하다 — `affected rows = 0`을 **"그 사이 누군가 먼저 수정함"**으로 해석한다. 버전 비교는 애플리케이션이 아니라 `WHERE` 절이 한다.

### 쿼리 카운트를 지표로

HTTP 요청 하나가 SQL을 몇 번 날리는지 세서 Micrometer 메트릭으로 발행한다. 🟢 **N+1 같은 "요청당 쿼리 폭발"을 코드 리뷰가 아니라 지표로 감지**하는 게 목적이다.

## 해석

🟡 **`@Version`은 잠그지 않는다. `WHERE version = ?`를 붙일 뿐이다.** [[낙관적 락]]이 "감지하는 장치"라는 말의 실체가 이 SQL 한 줄이다.

🔴 **예외가 `saveAndFlush` 시점에 터진다는 게 핵심이다.** flush/commit 시점이라 그 트랜잭션은 이미 되돌릴 수 없다. 그래서 재시도는 **트랜잭션을 완전히 닫고 새로 열어야** 성립한다 — [[낙관적 락]]에서 Facade에 재시도를 둔 이유가 여기 있다.

💬 쿼리 카운트 메트릭은 [[Micrometer 계측기 선택]]의 좋은 예다. "요청당 쿼리 수"는 누적이 아니라 **분포**를 봐야 하는 값이라 Timer 계열이 맞고, 평균만 보면 N+1이 묻힌다.

## 한계

🔴 **동시 요청이 아니다.** A/B를 순차로 실행해 스냅샷 불일치를 인위적으로 만든다. 진짜 경합에서의 실패율이나 재시도 소진은 [[선착순 쿠폰 발급 동시성]]이 본다(낙관적 락 3156ms).

🔴 **재시도 로직이 없다.** 예외가 뜨는 것까지만 확인하고, 어떻게 복구할지는 범위 밖이다.

🔴 [[비관적 락]]과의 대조가 없다. 언제 무엇을 쓸지는 이 실험만으로 못 정한다.

🔴 쿼리 카운트 메트릭의 임계·알림이 없다. 재고 있지만 감시는 없다.

## 연결

- 개념: [[낙관적 락]] — 이 실험이 SQL 수준에서 뒷받침
- 개념: [[Lost Update]] — 이 락이 막는 것
- 개념: [[Micrometer 계측기 선택]] — 쿼리 카운트 지표
- 개념: [[JPA N+1]] · [[영속성 컨텍스트]]
- 실험: [[선착순 쿠폰 발급 동시성]] — 실제 경합에서의 비용
- 코드: `~/Desktop/git/deep-dive/labs/spring-data-jpa/`
- 원본: `raw/code/spring-data-jpa.md`
