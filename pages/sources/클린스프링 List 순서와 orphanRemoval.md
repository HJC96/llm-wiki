---
title: 클린스프링 List 순서와 orphanRemoval
type: source
kind: lecture
status: stable
tags: [jpa, hibernate, ddd]
moc: ["[[MOC-출처]]", "[[MOC-Spring]]"]
created: 2026-09-11
updated: 2026-09-11
---

## 무엇

같은 splearn 강의의 Curriculum/Section/Lesson 부분 문답. `removeLesson()`이 순서는 고쳤는데 행은 남긴 현상을 추적해, **순서 관리와 행 삭제가 별개 책임**이라는 결론에 도달한다. `source: 대화 (2026-09-11)`

## 핵심 주장

1. **`ORDER BY` 없는 조회 순서는 보장되지 않는다.** INSERT 순서대로 나오는 건 우연이다.
2. **`id`로 정렬하면 중간 삽입에서 깨진다.** `id`는 "누구인가", `order`는 "몇 번째인가"로 역할이 다르다.
3. **`@OrderColumn`은 남아 있는 것의 순서만 관리한다.** 컬렉션에서 빠진 엔티티를 DB에서 지우는 건 다른 문제다.
4. **`orphanRemoval=true`를 못 켜는 도메인이 있다.** Lesson을 다른 Section으로 **이동**하는 기능이 있으면, 컬렉션에서 빠지는 사건에 "삭제"와 "이동" 두 의미가 겹친다.
5. **그래서 진짜 삭제만 명시적으로 지운다** — `curriculum.removeLesson(...)` 후 `lessonRepository.delete(removed)`.

## 여기서 나온 페이지

| 페이지 | 무엇을 가져갔나 |
|---|---|
| [[컬렉션 순서와 @OrderColumn]] | id와 order의 역할 분리, `@OrderColumn`의 재정렬 UPDATE, orphanRemoval을 못 켜는 이유와 그 대가 |

## 기존 위키와의 관계

- **보강**: [[애그리거트 경계 정하기]] — Curriculum이 Section·Lesson을 통째로 들고 있다는 판단이 이 문제의 전제다
- **연결 추가**: [[영속성 컨텍스트]] — 컬렉션 변경이 언제 SQL로 옮겨가는가

## 아직 안 다룬 것

- > ❓ **확인 필요**: 삭제 후 L1 행의 실제 컬럼값(`section_id`, `lesson_order`)을 원문이 보여주지 않았다. 조회 결과로 역추론한 해석이라 위키에 `❓`로 표시했다
- **`@OrderColumn` vs `order` 필드 + `@OrderBy`** — 어느 쪽이 나은지 실측이 없다. 앞쪽은 중간 변경 시 뒤쪽 전부 UPDATE가 나간다
- **고아 행 탐지** — 명시적 삭제를 빠뜨렸을 때 조용히 쌓이는 걸 어떻게 발견하나

## 원본

`raw/lectures/클린스프링_List순서와_orphanRemoval.md`
