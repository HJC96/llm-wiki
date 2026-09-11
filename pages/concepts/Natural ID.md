---
title: Natural ID
type: concept
status: growing
tags: [jpa, hibernate, ddd]
sources: ["[[클린스프링 검증·엔티티 상태·테스트 픽스처]]"]
moc: ["[[MOC-설계]]"]
created: 2026-09-11
updated: 2026-09-11
---

## 한 줄 정의

시스템이 만들어 준 PK 말고, **업무에서 이 엔티티를 가리킬 때 쓰는 값**. Hibernate의 `@NaturalId`로 표시한다(JPA 표준 아님, `org.hibernate.annotations.NaturalId`).

## 왜 필요한가

```java
@Id @GeneratedValue Long id;   // Surrogate Key — 시스템이 만든 번호
@NaturalId String email;       // Natural ID — 현실에서 회원을 가리키는 값
```

🔴 **`@NaturalId`를 붙여도 PK가 되지는 않는다.** PK는 여전히 `@Id`다. 이건 "이 값이 이 엔티티의 도메인상 정체성"이라는 **선언**이다.

## 어떻게 동작하는가

### Enrollment의 경우 — 조합이 정체성이 된다

"어떤 회원이 어떤 강의를 수강한다"가 Enrollment의 의미다. 그러면 정체성도 그 둘이다.

```java
@NaturalId @ManyToOne private Member member;
@NaturalId @ManyToOne private Course course;
```

```text
(Member 1, Course 10)
(Member 1, Course 20)   ← 다른 Enrollment
(Member 2, Course 10)   ← 또 다른 Enrollment
```

🔴 **이건 Composite Primary Key가 아니다.** 진짜 복합 PK라면 `@EmbeddedId`나 `@IdClass`를 쓴다. 현재 구조는 PK = `Enrollment.id`, Natural ID = `(member, course)`다.

### Identity와 State를 가르는 선

```text
member, course              → Identity. 바꾸지 않는다
status, enrolledAt, ...     → State. ENROLLED → STUDYING → COMPLETED로 변한다
```

🟡 **"회원 A의 Spring 수강"을 "회원 A의 Java 수강"으로 바꾸는 건 수정이 아니라 종료 + 새 생성이다.** 정체성을 갈아끼우는 UPDATE는 도메인적으로 말이 안 된다. 이 선을 그어 두면 어떤 필드에 setter를 열지가 저절로 정해진다.

## 트레이드오프

### 🟡 Unique하다고 전부 Natural ID는 아니다

Course에도 `(instructor, title)` UNIQUE가 있는데, 강의는 이걸 Natural ID로 보지 않았다. **`title`이 바뀔 수 있기 때문이다.**

```text
"Spring 7"  →  "Spring Framework 완벽 가이드"
```

Natural ID의 조건은 둘이다.

1. 고유하다
2. **엔티티 생명주기 동안 안정적이다**

| | UNIQUE | 안정적 | Natural ID |
|---|---|---|---|
| Course `(instructor, title)` | ✅ | 🔴 title 변경 가능 | ❌ |
| Enrollment `(member, course)` | ✅ | ✅ 생성 후 안 바꿈 | ✅ |

**2번을 빠뜨리고 UNIQUE만 보고 Natural ID로 선언하는 게 흔한 실수다.**

### `@NaturalId`와 UNIQUE는 역할이 다르다

```text
@NaturalId   → 도메인상 정체성이라는 의미 표시. Hibernate가 이 키로 조회 캐시도 쓴다
UNIQUE       → DB에서 실제 중복 저장을 막는다
```

둘은 같이 쓴다. 의미 선언만으로는 중복이 막히지 않고, 제약만으로는 의도가 드러나지 않는다 → [[검증 로직은 어디에 두는가]]의 마지막 줄

### 🔴 대가

- **Hibernate 전용이다.** JPA 표준으로 옮길 수 없다
- `@NaturalId`를 연관 엔티티에 걸면 조회·캐시 동작이 직관과 달라질 수 있다. 이 볼트에 실측이 없다

## 연결

- [[검증 로직은 어디에 두는가]] — UNIQUE 제약은 검증의 마지막 방어선
- [[멱등성]] — "의도를 식별하는 키"라는 발상이 같다. 그쪽은 요청, 이쪽은 엔티티
- [[애그리거트 경계 정하기]] — 무엇이 정체성인가는 경계를 정하는 일과 이어진다
- [[복식부기 원장]] — Identity는 안 바꾸고 State만 추가한다는 구조가 닮았다
