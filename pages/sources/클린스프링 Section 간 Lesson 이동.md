---
title: 클린스프링 Section 간 Lesson 이동
type: source
kind: lecture
status: stable
tags: [jpa, ddd, test]
moc: ["[[MOC-출처]]", "[[MOC-Spring]]"]
created: 2026-09-11
updated: 2026-09-11
---

## 무엇

같은 splearn 강의에서 Curriculum / Section / Lesson의 이동 로직을 따라가며 `this`가 어느 객체인지, 왜 `while`과 `insertIndex++`가 필요한지를 푼 문답. `source: 대화 (2026-09-11)`

## 핵심 주장

1. **`this`는 메서드를 호출한 객체다.** `target.addLesson(...)`으로 부르면 `addLesson` 안의 `this`는 target이다. 같은 코드라도 호출 경로에 따라 가리키는 대상이 바뀐다.
2. **`addLesson()`이 양쪽을 동시에 바꾼다.** `lesson.moveTo(this)`로 자식의 부모 참조를, `this.lessons.add(...)`로 부모의 컬렉션을 함께 고친다.
3. **이동은 더하기와 빼기가 한 쌍이다.** `removeFirst()`를 빠뜨려 원본 컬렉션이 비워지지 않았고 `while`이 무한 루프에 빠졌다.
4. **`insertIndex++`는 순서 보존 장치다.** 같은 자리에 계속 넣으면 옮긴 Lesson들의 순서가 뒤집힌다.
5. **책임이 셋으로 갈린다.** Curriculum은 Section 간 이동을 결정하고, Section은 Lesson 목록을 관리하며, Lesson은 자신의 Section을 바꾼다.
6. **테스트는 스냅샷 record로 비교한다.** 엔티티 그래프 대신 `SectionContent` / `LessonContent`로 변환해 구조와 순서만 본다.

## 여기서 나온 페이지

| 페이지 | 무엇을 가져갔나 |
|---|---|
| [[양방향 연관관계 동기화]] | 한쪽만 바꿨을 때 깨지는 방식, 동기화 메서드가 불변식인 이유, 무한 루프와 순서 역전 함정, 책임 3분할 |

## 기존 위키와의 관계

- **새 축**: `양방향` · `연관관계 주인` · `mappedBy` · `편의 메서드` 전부 검색 **0건**이었다. JPA의 고전 주제인데 볼트에 없었다
- **보강**: [[컬렉션 순서와 @OrderColumn]] — 도메인 코드가 순서를 먼저 올바르게 만들어야 `@OrderColumn`이 옮길 게 생긴다는 앞단이 붙었다
- **보강**: [[애그리거트 경계 정하기]] — 루트가 내부 변경을 독점한다는 원칙의 구체적 구현
- **연결**: [[테스트 픽스처 상속 구조]] — 양방향 그래프를 스냅샷 record로 바꿔 검증하는 기법

## 아직 안 다룬 것

- **단방향으로 충분한 경우의 판단 기준** — 원문은 양방향을 전제로 시작한다. 언제 양방향을 포기할지는 다루지 않는다
- **`mappedBy`와 연관관계 주인** — 어느 쪽이 외래키를 쥐는가는 원문에 없다. 개념 페이지에 한 줄만 적었다
- **컬렉션을 불변 뷰로 내보내기** — 동기화 메서드가 있어도 세터가 열려 있으면 우회된다는 문제
- 🔴 **수치가 없다.** 전부 설계·구현 판단이다

## 원본

`raw/lectures/클린스프링_Section간_Lesson이동.md`
