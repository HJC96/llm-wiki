---
title: MOC-Java
type: moc
tags: [meta, java]
created: 2026-08-15
updated: 2026-08-31
---

# MOC — Java

← [[MOC-홈]]

## JVM

- [[JVM 메모리 구조]] — 힙·스택·메타스페이스
- [[클래스 로딩]] — 로딩·링킹·초기화, 로더 위임
- [[GC 동작 방식]] — 마크 앤 스윕, 세대 가설
- [[G1 GC]] · [[GC 튜닝 판단 기준]] 🔴 — 대개 튜닝보다 할당을 줄이는 게 먼저
- [[JIT 컴파일과 워밍업]] — 벤치마크가 왜 JMH를 쓰는지
- [[암달의 법칙]] ✅ — 병목은 느린 쪽이 아니라 **직렬 구간 비중이 큰 쪽**에서 터진다

## 언어

- [[equals와 hashCode]] — 계약을 어기면 컬렉션에서 무슨 일이
- [[null 안전성 애노테이션]] ✅ 🔴 — `@Nonnull`과 `@NotNull`은 이름만 닮았다. 하나는 도구용 계약, 하나만 런타임 검사
- [[불변 객체]] — 왜 동시성에서 공짜인지
- [[제네릭 소거]] · [[와일드카드 PECS]]
- [[record와 값 객체]]
- [[Optional을 쓸 곳과 안 쓸 곳]]

## 컬렉션

- [[HashMap 내부 구조]] — 버킷, 트리화
- [[ConcurrentHashMap]] — 어떻게 락 경합을 줄이나
- [[ArrayList와 LinkedList]] 🔴 — 실무에서 LinkedList를 쓸 일이 거의 없는 이유

## 동시성 기본기

세부는 [[MOC-동시성]].

- [[Java 메모리 모델]] · [[volatile과 가시성]] · [[synchronized의 동작]]
- [[블로킹과 비동기는 다른 축]] ✅ — 네 조합. 동기 논블로킹이 실제로 쓰이는 자리는 셋뿐
- [[ExecutorService]] · [[CompletableFuture]]

## 버전

- [[Java 8에서 17로]] — 레거시 전환 때 실제로 걸린 것들
- [[Java 21 가상 스레드]]

## 실험

→ [[MOC-실험]]

- [[BouncyCastle Provider 등록 비용]] ✅ — JMH + 프로파일러로 확장성의 직관을 뒤집은 실측

## 소스

→ [[MOC-출처]] — [[CS 면접 Java]]

## 이어지는 곳

- 프레임워크 → [[MOC-Spring]] · 면접 → [[MOC-면접]]

