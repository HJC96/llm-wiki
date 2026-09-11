---
title: MOC-Spring
type: moc
tags: [meta, spring]
created: 2026-08-15
updated: 2026-08-31
---

# MOC — Spring

← [[MOC-홈]]

## 컨테이너

- [[DI 컨테이너와 빈 스코프]] · [[빈 생명주기]]
- [[AOP 프록시 동작]] — JDK 동적 프록시 vs CGLIB
- [[프록시 자기호출 문제]] ✅ 🔴 — `@Transactional`·`@Cacheable`·`@Async`·`@Retryable`이 조용히 무시되는 한 가지 원인
- [[@Valid와 @Validated]] ✅ — 제약 **선언**과 검증 **실행**은 다른 일. `@Validated`도 같은 프록시 함정을 공유한다

## 트랜잭션

- [[@Transactional 전파 속성]] · [[readOnly의 실제 효과]]
- [[트랜잭션 경계와 외부 호출]] 🔴 — 외부 API를 트랜잭션 안에서 부르면 생기는 일
- [[@TransactionalEventListener]] — AFTER_COMMIT으로 후속 처리 분리
- [[커밋 후 이벤트 발행]] ✅ — DB에 없는 사실을 남에게 알리지 않기. 유실 창은 남는다
- [[재시도와 백오프]] ✅ — `@Retryable`도 같은 프록시 기반
- [[ApplicationEventPublisher]] — 도메인 이벤트를 스프링 이벤트로
- [[업무 트랜잭션과 시스템 트랜잭션]] ✅ 🔴 — `@Transactional`이 못 넘는 경계. 요청이 나뉘면 묶을 방법이 없다
- [[낙관적 락 재시도 경계]] ✅ 🔴 — 충돌한 트랜잭션은 rollback-only. 재시도는 `TransactionTemplate`으로 트랜잭션 밖에서
- [[Dual Write 문제]] ✅ — 트랜잭션 안에서 Kafka로 쏘면 롤백돼도 되돌아오지 않는다

## 캐시

**패턴** — 축은 둘뿐이다. 읽기 miss를 누가 처리하나 / 쓰기를 언제 반영하나

- [[Cache Aside]] ✅ — 서비스가 miss 처리. 기본값
- [[Read Through]] ✅ — 캐시 계층이 miss 처리
- [[캐시 쓰기 전략]] ✅ — Write Through / Around / Behind

**무너지는 방식** — 캐시가 잘 돌수록 만료 순간의 낙차가 크다

- [[Cache Stampede]] ✅ — 인기 키 하나가 만료될 때. 분산 락 + DCL
- [[Cache Penetration]] ✅ — 없는 키가 관통할 때. Null Caching
- [[Cache Avalanche]] ✅ — 많은 키가 동시 만료될 때. TTL Jitter
- [[캐시 정합성 Race Condition]] ✅ — 옛 값이 뒤늦게 들어와 눌러앉을 때

**용량** — TTL이 신선도 문제라면 이건 공간 문제

- [[캐시 축출 정책]] ✅ — 자리가 없을 때 누굴 버리나. LRU·LFU와 O(1) 구조

**Spring에서**

- [[Spring Cache 추상화]] ✅ — 정상 경로는 애너테이션, 방어는 `RedisTemplate`
- [[캐시 키 설계]] ✅ — 키가 좁으면 공유 사고, 넓으면 히트율 저하
- [[로컬 캐시와 인스턴스 정합성]] ✅ 🔴 — WAS 2대 이상일 때. 테이블 버전 키
- [[@Cacheable 동작과 프록시]] · [[캐시 TTL과 명시적 무효화]]

## 웹 스택 — 서블릿이냐 리액티브냐

- [[Spring WebFlux]] ✅ — Servlet 대신 Reactive Streams. 진짜 대립축은 "MVC 패턴이냐"가 아니라 블로킹이냐다
- [[Reactor]] ✅ — `Mono`/`Flux`. 값을 꺼내지 말고 그 위에서 조립한다. Lazy
- **[[결제 시스템에 WebFlux를 쓸 것인가]]** ⭐ — 결론은 "아니다". 판단 근거 다섯

## 배치

- [[Spring Batch Chunk 모델]] · [[Job과 Step 파라미터]]
- [[배치 재시작과 멱등성]]

## 데이터

- [[영속성 컨텍스트]] ✅ — 상태 4단계와 `save()`의 persist/merge 분기. 🔴 `merge()`는 원본이 아니라 **새 인스턴스**를 돌려준다
- [[JPA N+1]] · [[더티 체킹]]
- [[양방향 연관관계 동기화]] ✅ 🔴 — 한쪽만 바꾸면 객체 그래프와 DB가 다른 말을 한다. 이동은 더하기+빼기 한 쌍
- [[컬렉션 순서와 @OrderColumn]] ✅ 🔴 — 순서 관리와 행 삭제는 **다른 책임**이다
- [[Spring Data Repository 계약]] ✅ — `save()`는 JPA가 아니라 Spring Data의 계약. 마커 `Repository`로 좁게 노출
- [[JPA 락 모드]] → [[낙관적 락]] · [[비관적 락]] · 요청이 나뉘면 [[Optimistic Offline Lock]]
- **[[도메인 모델과 JPA 엔티티를 분리해야 하는가]]** ⭐ — JPA 스펙이 스스로 "도메인 오브젝트 매핑 기술"이라고 말한다
- [[orm.xml로 매핑 걷어내기]] ✅ — XML이 애노테이션을 오버라이드한다. `@Entity`·`@NaturalId`·관계만 남긴다
- [[애플리케이션 서비스]] ✅ — `@Service`가 실제로 무엇을 하는 층인가
- [[Hibernate가 만드는 SQL 관찰하기]]
- 소스: [[클린스프링 검증·엔티티 상태·테스트 픽스처]] · [[클린스프링 List 순서와 orphanRemoval]] · [[클린스프링 Section 간 Lesson 이동]]
- 소스: [[시스템 설계 분산 캐싱]] — 캐시 절의 출처

## 관측

- [[Actuator 엔드포인트 보안 경계]] ✅ 🔴 — 조회만 있는 게 아니다. `DELETE /actuator/caches/{name}`를 열면 따라오는 문제
- [[커스텀 헬스 인디케이터]]

## 실험

→ [[MOC-실험]] — [[캐시 패턴 비교]] · [[Spring Cache 로컬 캐시]] · [[Spring Cache Redis]] · [[@Async vs ExecutorService]] · [[낙관적 락과 Hibernate SQL 관찰]] · [[Actuator 커스텀 헬스 체크]]

## 이어지는 곳

- 설계 판단 → [[MOC-설계]] · 동시성 → [[MOC-동시성]] · 결제 흐름에서의 조합 → [[MOC-결제시스템]]
- 소스 → [[MOC-출처]] — [[Spring WebFlux vs MVC]]

