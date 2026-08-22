---
title: MOC-Spring
type: moc
tags: [meta, spring]
created: 2026-08-15
updated: 2026-08-22
---

# MOC — Spring

← [[MOC-홈]]

## 컨테이너

- [[DI 컨테이너와 빈 스코프]] · [[빈 생명주기]]
- [[AOP 프록시 동작]] — JDK 동적 프록시 vs CGLIB
- [[프록시 자기호출 문제]] ✅ 🔴 — `@Transactional`·`@Cacheable`·`@Async`·`@Retryable`이 조용히 무시되는 한 가지 원인

## 트랜잭션

- [[@Transactional 전파 속성]] · [[readOnly의 실제 효과]]
- [[트랜잭션 경계와 외부 호출]] 🔴 — 외부 API를 트랜잭션 안에서 부르면 생기는 일
- [[@TransactionalEventListener]] — AFTER_COMMIT으로 후속 처리 분리
- [[커밋 후 이벤트 발행]] ✅ — DB에 없는 사실을 남에게 알리지 않기. 유실 창은 남는다
- [[재시도와 백오프]] ✅ — `@Retryable`도 같은 프록시 기반
- [[ApplicationEventPublisher]] — 도메인 이벤트를 스프링 이벤트로
- [[업무 트랜잭션과 시스템 트랜잭션]] ✅ 🔴 — `@Transactional`이 못 넘는 경계. 요청이 나뉘면 묶을 방법이 없다

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

**Spring에서**

- [[Spring Cache 추상화]] ✅ — 정상 경로는 애너테이션, 방어는 `RedisTemplate`
- [[캐시 키 설계]] ✅ — 키가 좁으면 공유 사고, 넓으면 히트율 저하
- [[로컬 캐시와 인스턴스 정합성]] ✅ 🔴 — WAS 2대 이상일 때. 테이블 버전 키
- [[@Cacheable 동작과 프록시]] · [[캐시 TTL과 명시적 무효화]]

## 배치

- [[Spring Batch Chunk 모델]] · [[Job과 Step 파라미터]]
- [[배치 재시작과 멱등성]]

## 데이터

- [[영속성 컨텍스트]] · [[JPA N+1]] · [[더티 체킹]]
- [[JPA 락 모드]] → [[낙관적 락]] · [[비관적 락]] · 요청이 나뉘면 [[Optimistic Offline Lock]]
- [[Hibernate가 만드는 SQL 관찰하기]]

## 관측

- [[Actuator 엔드포인트 보안 경계]] 🔴 — 외부 노출 차단, 내부망 한정
- [[커스텀 헬스 인디케이터]]

## 실험

→ [[MOC-실험]] — [[캐시 패턴 비교]] · [[Spring Cache 로컬 캐시]] · [[Spring Cache Redis]] · [[@Async vs ExecutorService]] · [[낙관적 락과 Hibernate SQL 관찰]] · [[Actuator 커스텀 헬스 체크]]

## 이어지는 곳

- 설계 판단 → [[MOC-설계]] · 동시성 → [[MOC-동시성]]
