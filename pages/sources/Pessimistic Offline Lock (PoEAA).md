---
title: Pessimistic Offline Lock (PoEAA)
type: source
kind: article
status: stable
tags: [concurrency, lock, transaction, design-pattern]
moc: ["[[MOC-동시성]]", "[[MOC-출처]]"]
created: 2026-08-22
updated: 2026-08-22
---

## 무엇

PoEAA 패턴 카탈로그의 짝 항목. **한 번에 하나의 업무 트랜잭션만** 데이터에 접근하게 해서 충돌을 아예 없앤다. 같은 저자, 같은 날짜(2003-03-05), 같은 16장.

## 핵심 주장

1. 업무 트랜잭션 전체를 **시스템 트랜잭션 하나로 여는 것**이 가장 단순해 보이지만, 🔴 트랜잭션 시스템이 **장기 트랜잭션에 맞게 만들어져 있지 않아** 잘 동작하지 않는다 — *"transaction systems aren't geared to work with long transactions."*
2. 그래서 여러 시스템 트랜잭션을 쓸 수밖에 없고, 그 순간부터 **동시 접근 관리는 각자의 몫**이 된다.
3. 🟡 **먼저 시도할 것은 Optimistic이다** — *"The first approach to try is Optimistic Offline Lock."*
4. 🔴 그런데 Optimistic은 충돌이 **업무 트랜잭션 끝에서만** 드러난다. 피해자는 작업을 전부 마친 뒤 마지막 순간에 실패를 통보받고 시간을 통째로 잃는다.
5. 🔴 긴 업무 트랜잭션에서 이게 잦으면 *"the system will soon become very unpopular."*
6. Pessimistic은 **쓰기 시작 전에 락을 획득**하게 강제해서 충돌을 회피한다. 그래서 시작한 업무 트랜잭션은 대개 동시성 제어에 튕기지 않고 끝난다.

## 여기서 나온 페이지

| 페이지 | 무엇을 가져갔나 |
|---|---|
| [[Pessimistic Offline Lock]] | 주장 3·4·5·6 — 선택 순서와 뒤집히는 조건 |
| [[업무 트랜잭션과 시스템 트랜잭션]] | 주장 1 — 트랜잭션을 길게 여는 선택지가 왜 탈락하는지 |
| [[네임드 락]] | 주장 6의 DB 구현 형태 |
| [[조회와 저장이 다른 요청일 때 무엇으로 막는가]] | 주장 3·4 — "낙관이 기본값, 실패 비용이 크면 뒤집힌다" |

## 기존 위키와의 관계

- **보강**: [[비관적 락]] — 이름이 닮았지만 **트랜잭션 종속 vs 업무 트랜잭션 종속**으로 층위가 다르다는 구분이 추가됐다
- **보강**: [[Redis 분산락]] — TTL이 결국 고아 락 방어라는 관점이 붙었다
- **⚠️ 충돌**: 없음

## 아직 안 다룬 것

- 책 16장의 락 테이블 스키마·구현 세부, 락 획득 실패 시 대기 전략
- 고아 락 해제 수단 3종(만료·강제 해제·세션 감지) 중 실무에서 무엇이 무난한지 — 원문은 존재만 시사한다
- Optimistic과 Pessimistic을 **섞어 쓰는** 구성 (읽기는 낙관, 특정 화면만 비관)

## 원본

`raw/articles/Pessimistic Offline Lock.md` — https://martinfowler.com/eaaCatalog/pessimisticOfflineLock.html
