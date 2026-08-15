---
title: MOC-Spring
type: moc
tags: [meta, spring]
created: 2026-08-15
updated: 2026-08-15
---

# MOC — Spring

← [[MOC-홈]]

## 컨테이너

- [[DI 컨테이너와 빈 스코프]] · [[빈 생명주기]]
- [[AOP 프록시 동작]] — JDK 동적 프록시 vs CGLIB
- [[프록시 자기호출 문제]] 🔴 — `@Transactional`·`@Cacheable`이 안 먹는 대표 원인

## 트랜잭션

- [[@Transactional 전파 속성]] · [[readOnly의 실제 효과]]
- [[트랜잭션 경계와 외부 호출]] 🔴 — 외부 API를 트랜잭션 안에서 부르면 생기는 일
- [[@TransactionalEventListener]] — AFTER_COMMIT으로 후속 처리 분리
- [[커밋 후 이벤트 발행]] ✅ — DB에 없는 사실을 남에게 알리지 않기. 유실 창은 남는다
- [[재시도와 백오프]] ✅ — `@Retryable`도 같은 프록시 기반
- [[ApplicationEventPublisher]] — 도메인 이벤트를 스프링 이벤트로

## 캐시

- [[Spring Cache 추상화]] · [[@Cacheable 동작과 프록시]]
- [[로컬 캐시와 인스턴스 정합성]] 🔴 — WAS 2대 이상일 때
- [[캐시 TTL과 명시적 무효화]]

## 배치

- [[Spring Batch Chunk 모델]] · [[Job과 Step 파라미터]]
- [[배치 재시작과 멱등성]]

## 데이터

- [[영속성 컨텍스트]] · [[JPA N+1]] · [[더티 체킹]]
- [[JPA 락 모드]] → [[낙관적 락]] · [[비관적 락]]
- [[Hibernate가 만드는 SQL 관찰하기]]

## 관측

- [[Actuator 엔드포인트 보안 경계]] 🔴 — 외부 노출 차단, 내부망 한정
- [[커스텀 헬스 인디케이터]]

## 실험

→ [[MOC-실험]] — [[Spring Cache 로컬 캐시]] · [[Spring Cache Redis]] · [[@Async vs ExecutorService]] · [[낙관적 락과 Hibernate SQL 관찰]] · [[Actuator 커스텀 헬스 체크]]

## 이어지는 곳

- 설계 판단 → [[MOC-설계]] · 동시성 → [[MOC-동시성]]
