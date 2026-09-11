---
title: Spring Data Repository 계약
type: concept
status: growing
tags: [jpa, spring, architecture]
sources: ["[[클린스프링 전체 문답 118]]"]
moc: ["[[MOC-Spring]]"]
created: 2026-09-11
updated: 2026-09-11
---

## 한 줄 정의

`save()`는 JPA가 아니라 **Spring Data의 저장 계약**이다. 더티 체킹과 겹쳐 보이지만 층이 다르고, Repository 인터페이스를 어디까지 노출할지는 설계 선택이다.

## 왜 필요한가

셋이 자주 뭉뚱그려진다.

| | 정체 |
|---|---|
| **JPA** | ORM 표준. Hibernate 같은 구현체가 실제로 동작한다 |
| **Spring의 JPA 지원** | `EntityManager`·트랜잭션을 Spring과 연결한다 |
| **Spring Data JPA** | Repository 추상화. `save()` · `findById()`를 제공한다 |

🔴 **JPA 자체에는 `save()`가 없다.** `persist()`와 `merge()`가 있을 뿐이다. Spring Data의 `save()`는 신규면 `persist()`, 기존이면 `merge()`를 고른다 → [[영속성 컨텍스트]]

## 어떻게 동작하는가

### `save()` 없이도 저장된다

쓰기 트랜잭션 안에서 조회한 엔티티는 영속 상태다. 값만 바꿔도 더티 체킹으로 UPDATE가 나간다.

```java
Course course = courseRepository.findById(id).orElseThrow();
course.changeTitle("새 제목");
// save() 없이도 UPDATE 된다
```

🔴 **detached 객체는 다르다.** 컨텍스트 밖의 객체는 값을 바꿔도 아무 일이 없다.

### 그런데 강의는 `save()`를 부른다

```java
course.changeTitle("새 제목");
courseRepository.save(course);   // 굳이 호출한다
```

🟡 **더티 체킹은 JPA의 메커니즘이고 `save()`는 Repository의 계약이다.** 층이 다르므로 둘 중 하나를 고르는 문제가 아니다. `조회 → 변경 → save`라는 **명시적 스타일**을 택한 것이다.

- **얻는 것**: Repository만 보면 저장 지점이 드러난다. 영속 상태에 대한 지식 없이도 코드가 읽힌다. 나중에 Repository 구현이 JPA가 아니게 돼도 호출부가 안 바뀐다
- 🔴 **대가**: 실제로는 필요 없는 호출이다. 읽는 사람이 "저게 없으면 저장이 안 되나?"라고 오해할 수 있다

### 마커 `Repository`로 필요한 것만 노출한다

```java
public interface InstructorRepository extends Repository<Instructor, Long> {
    Instructor save(Instructor instructor);
    Optional<Instructor> findById(Long id);
}
```

`JpaRepository`가 아니라 **마커 인터페이스 `Repository`**를 상속한다. 마커에는 메서드가 하나도 없어서, **이 컴포넌트가 실제로 쓰는 것만 골라 선언**할 수 있다. 구현체는 Spring Data가 만든다.

| | `JpaRepository` | 마커 `Repository` |
|---|---|---|
| 노출 | `deleteAll` · `flush` · `findAll` 등 전부 | 선언한 것만 |
| 편의 | 바로 쓴다 | 필요할 때마다 추가 |
| 경계 | 🔴 컴포넌트가 안 쓰는 기능까지 열린다 | 계약이 좁다 |

🟡 **이건 [[포트와 어댑터]]의 Required Interface를 좁게 정의하는 것과 같은 발상이다.** 클라이언트가 필요한 만큼만 계약으로 삼는다. 강사가 마커 쪽을 고른 이유도 **의존하는 기능을 명확하게 표현하기 위해서**다.

## 트레이드오프

- 🔴 **`save()`를 습관으로 만들면 detached 문제를 늦게 발견한다.** 항상 부르니까 영속 여부를 생각하지 않게 되고, 정작 컨텍스트 밖 객체를 다룰 때 조용히 틀린다
- **마커 Repository는 메서드를 하나씩 늘려야 한다.** 팀이 작고 변경이 잦으면 마찰이 된다. 경계를 지키는 값이 그 마찰보다 클 때만 의미가 있다
- `save()` 반환값을 쓰는 습관은 여전히 중요하다. `merge()` 경로에서는 **인자로 준 객체가 아니라 반환된 객체가 managed**다

## 연결

- [[영속성 컨텍스트]] — persist/merge 분기와 더티 체킹이 실제로 일어나는 곳
- [[포트와 어댑터]] — 계약을 좁게 정의한다는 같은 원칙
- [[Slice와 Layer]] — 컴포넌트마다 필요한 저장소 기능이 다르다는 전제
- [[도메인 모델과 JPA 엔티티를 분리해야 하는가]] — Repository가 도메인 타입을 다루는 문제
