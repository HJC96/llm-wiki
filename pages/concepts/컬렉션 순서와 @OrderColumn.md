---
title: 컬렉션 순서와 @OrderColumn
type: concept
status: growing
tags: [jpa, hibernate, ddd]
sources: ["[[클린스프링 List 순서와 orphanRemoval]]"]
moc: ["[[MOC-Spring]]"]
created: 2026-09-11
updated: 2026-09-11
---

## 한 줄 정의

Java `List`의 **위치**를 DB 컬럼으로 옮겨 적는 장치. 그리고 그 순서 관리가 **행 삭제와는 별개의 책임**이라는 것.

## 왜 필요한가

`List`는 각 요소가 몇 번째인지가 타입의 일부다. DB의 row에는 그 개념이 없다.

🔴 **`ORDER BY` 없는 조회 결과의 순서는 보장되지 않는다.** INSERT한 순서대로 나오는 건 우연이지 계약이 아니다.

**그럼 `ORDER BY id`로 하면 되지 않나?** 중간 삽입이 없을 때만 된다.

```text
Java List      S1, S3, S2     ← S1과 S2 사이에 S3을 끼워 넣었다
DB id          1,  2,  3      ← S3은 나중에 만들어졌으니 id=3
ORDER BY id →  S1, S2, S3     ← 원하는 순서와 다르다
```

🟡 **`id`는 "이 데이터가 누구인가"고 `order`는 "이 데이터가 몇 번째인가"다.** 생성 순서와 표시 순서가 같다는 보장이 없는 한 둘을 겸할 수 없다.

## 어떻게 동작하는가

`@OrderColumn`을 붙이면 JPA가 List의 인덱스를 전용 컬럼에 유지한다.

```text
id | title | section_order
1  | S1    | 0
3  | S3    | 1
2  | S2    | 2
```

컬렉션에서 요소를 빼면 **남은 것들의 순서를 다시 매겨 UPDATE**한다.

```java
lessons.remove(L1);
```

```text
before   L1(order=0)  L2(order=1)
after    L2(order=0)              ← UPDATE 나감
```

여기까지는 정상이다. **문제는 L1이다.**

## 트레이드오프 — 순서와 삭제는 다른 책임

`orphanRemoval`을 켜지 않으면 `DELETE FROM lesson WHERE id = 1`이 나가지 않는다. L2의 순서는 고쳐졌는데 L1 행은 DB에 남는다.

> 🟡 **`@OrderColumn`은 "남아 있는 데이터의 순서"만 관리한다. 빠진 엔티티를 지우는 건 전혀 다른 문제다.**

남은 L1은 연관만 끊긴 상태로 떠 있다. Section을 다시 조회하면 안 나오지만 행은 살아 있다.

```text
id | title | section_id | lesson_order
1  | L1    | NULL       | NULL          ← 연관만 끊김. 행은 남음
2  | L2    | 10         | 0
```

> ❓ 확인 필요: 원문이 실제 컬럼값까지 보여주지 않았다. 조회 결과로 역추론한 해석이다. 만약 `section_id`가 10으로 남아 있었다면 다시 조회될 것이므로 NULL이 됐다고 보는 게 자연스럽다.

### 그럼 `orphanRemoval=true`를 켜면?

DELETE까지 따라온다. 그런데 **이 도메인에서는 못 켠다.**

Lesson을 다른 Section으로 **이동**하는 기능이 있기 때문이다.

```text
1. S1의 List에서 L1 제거    ← orphanRemoval이 여기서 "삭제 대상"으로 판단
2. S2의 List에 L1 추가      ← 도달하기 전에 이미 지워질 수 있다
```

🔴 **컬렉션에서 빠지는 사건 하나에 "삭제"와 "이동" 두 의미가 겹쳐 있다.** `orphanRemoval`은 그 둘을 구별하지 못하고 전부 삭제로 읽는다.

그래서 강의는 켜지 않고, 진짜 삭제일 때만 명시적으로 지운다.

```java
Lesson removed = curriculum.removeLesson(...);
lessonRepository.delete(removed);
```

| | 켠다 | 끄고 명시 삭제 |
|---|---|---|
| 삭제 누락 | 안 난다 | 🔴 부르는 쪽이 빠뜨리면 고아 행이 남는다 |
| 이동 지원 | 🔴 불가 | 가능 |
| 의도 | 코드에 안 드러난다 | `delete()`가 눈에 보인다 |

## 코드에 닿는 지점

- `@OrderColumn`은 중간 삽입·삭제 때 **뒤쪽 전부를 UPDATE**한다. 요소가 많고 앞쪽 변경이 잦으면 비용이 커진다. 순서가 도메인 속성이면 차라리 `order` 필드를 엔티티가 직접 들고 `@OrderBy`로 정렬하는 쪽이 예측 가능하다
- 🔴 `@OrderColumn`은 컬럼에 `null`이나 구멍이 생기면 조용히 깨진다. 컬렉션을 JPA 밖에서 직접 손대지 않는다
- 컬렉션 변경이 DB로 옮겨가는 시점 자체는 [[영속성 컨텍스트]]가 정한다

## 연결

- [[양방향 연관관계 동기화]] — 도메인 코드가 순서를 먼저 올바르게 만들어야 옮길 게 생긴다
- [[영속성 컨텍스트]] — 컬렉션 변경을 언제 SQL로 옮기는가
- [[애그리거트 경계 정하기]] — Curriculum이 Section·Lesson을 통째로 들고 있다는 판단이 먼저다
- [[외래키 제약과 락 경합]] — 연관을 끊을 때 DB 쪽에서 생기는 다른 비용
- [[실패 사실의 기록]] — 명시적 삭제를 빠뜨려 남은 고아 행은 조용히 쌓인다
