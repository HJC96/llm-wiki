---
title: Optimistic Offline Lock (PoEAA)
type: source
kind: article
status: stable
tags: [concurrency, lock, transaction, design-pattern]
moc: ["[[MOC-동시성]]", "[[MOC-출처]]"]
created: 2026-08-22
updated: 2026-08-22
---

## 무엇

Martin Fowler의 PoEAA 패턴 카탈로그 항목. **업무 트랜잭션이 여러 시스템 트랜잭션에 걸칠 때** 충돌을 감지해 롤백하는 방식. 원문은 세 문단짜리 요약이고 상세는 책 16장(Offline Concurrency Patterns).

저자는 David Rice, 2003-03-05.

## 핵심 주장

1. 🟡 업무 트랜잭션은 흔히 **여러 시스템 트랜잭션에 걸쳐** 실행된다 — *"Often a business transaction executes across a series of system transactions."*
2. 단일 시스템 트랜잭션의 울타리를 벗어나는 순간 **DB 매니저만으로는** 레코드가 정합한 상태로 남는다고 보장할 수 없다.
3. 두 세션이 같은 레코드를 만지기 시작하면 **lost update**가 충분히 가능하고, 한쪽이 편집 중인 데이터를 다른 쪽이 읽으면 **inconsistent read**가 생긴다.
4. 🟡 해법은 **커밋 직전 검증**이다. 검증 성공이 곧 락 획득이다 — *"A successful pre-commit validation is, in a sense, obtaining a lock."*
5. 🟡 **검증과 갱신만 한 시스템 트랜잭션 안에 있으면** 업무 트랜잭션 전체가 정합해 보인다. 조회까지 묶을 필요가 없다.
6. Pessimistic이 충돌 확률을 **높다고** 보고 동시성을 제한하는 반면, Optimistic은 **낮다고** 가정하고 여러 사용자가 같은 데이터를 동시에 다루게 허용한다.

## 여기서 나온 페이지

| 페이지 | 무엇을 가져갔나 |
|---|---|
| [[업무 트랜잭션과 시스템 트랜잭션]] | 주장 1·2 — 두 단위가 어긋난다는 문제 정의 자체 |
| [[Optimistic Offline Lock]] | 주장 4·5·6 — 커밋 전 검증, 검증=락, 낮은 충돌 확률 가정 |
| [[조회와 저장이 다른 요청일 때 무엇으로 막는가]] | 선택지 비교의 한 축 |
| [[JPA @Version과 Optimistic Offline Lock의 차이]] | 주장 5를 면접 답변으로 |

## 기존 위키와의 관계

- **보강**: [[낙관적 락]] — 기존 페이지는 **한 시스템 트랜잭션 안**만 다루고 있었다. 같은 알고리즘이 업무 트랜잭션 단위로 확장되는 층위가 새로 붙었다
- **보강**: [[Lost Update]] — 오프라인 맥락(요청이 나뉜 상황)에서의 발생 경로가 추가됐다
- **⚠️ 충돌**: 없음. 기존 페이지들과 층위가 달라 어긋나는 주장이 없다

## 아직 안 다룬 것

- 책 16장 본문 (구현 코드, 버전 관리 세부, 충돌 감지 실패 사례)
- [[Coarse-Grained Lock]] — 같은 챕터의 짝 패턴. 락 단위를 애그리거트로 묶는 쪽. **원문 미확보**
- inconsistent read 쪽 (주장 3의 후반부) — 이번 컴파일은 lost update 중심으로만 갔다

## 원본

`raw/articles/Optimistic Offline Lock.md` — https://martinfowler.com/eaaCatalog/optimisticOfflineLock.html
