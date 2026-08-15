---
title: MOC-실험
type: moc
tags: [meta, performance]
created: 2026-08-15
updated: 2026-08-15
---

# MOC — 실험

← [[MOC-홈]]

`~/Desktop/git/deep-dive/labs/`의 모듈과 1:1. **숫자가 없으면 실험 페이지가 아니다.**
실험 결과 덤프(로그·벤치마크 출력)는 `raw/code/`에 넣고, 해석은 `pages/labs/`에 쓴다.

## 동시성

| 모듈 | 페이지 | 확인한 것 |
|---|---|---|
| `coupon-issue` | [[선착순 쿠폰 발급 동시성]] | 락 없음 / synchronized / 원자적 UPDATE / 비관·낙관·네임드 락 / Redis 분산락 / Lua 원자 차감 / Redisson |
| `seat-reservation` | [[좌석 예약 동시성]] | Redis 선점 + Kafka 비동기 확정 |

## 분산 트랜잭션

기준선 → 문제 재현 → 해법 순서로 읽는다.

| 모듈 | 페이지 | 확인한 것 |
|---|---|---|
| `distributed-transaction-monolith` | [[분산 트랜잭션 기준선 - 모놀리식]] | 하나의 로컬 트랜잭션 기준선 |
| `distributed-transaction-msa` | [[분산 트랜잭션 기준선 - MSA]] | 서비스별 로컬 트랜잭션의 부분 커밋 재현 |
| `distributed-transaction-2pc` | [[2PC 실험]] | MySQL XA로 prepare·commit 직접 실행. 블로킹과 in-doubt 재현 |
| `distributed-transaction-tcc` | [[TCC 실험]] | Try 후 즉시 커밋, Confirm·Cancel. 멱등성·빈 취소·매달림 처리 |

## 캐시

| 모듈 | 페이지 | 확인한 것 |
|---|---|---|
| `cache-patterns` | [[캐시 패턴 비교]] | Cache Aside / Read Through / Write Through / Write Around / Write Behind |
| `spring-cache-local` | [[Spring Cache 로컬 캐시]] | JVM 메모리 캐시 동작 |
| `spring-cache-redis` | [[Spring Cache Redis]] | Cache Aside / Null Caching / TTL Jitter / Hot Key 방어 |

## Spring · 테스트

| 모듈 | 페이지 | 확인한 것 |
|---|---|---|
| `spring-test-infra` | [[Testcontainers 테스트 인프라]] | `@DynamicPropertySource`, ArchUnit 검증 |
| `spring` | [[@Async vs ExecutorService]] | 스레드 모델 비교 |
| `spring-data-jpa` | [[낙관적 락과 Hibernate SQL 관찰]] | 버전 컬럼, 발생 SQL |
| `spring-boot-actuator` | [[Actuator 커스텀 헬스 체크]] | 기본 엔드포인트, 헬스 인디케이터 |
| `java-sandbox` | [[BouncyCastle Provider 등록 비용]] | JMH로 AES 암호화 시 Provider 등록 비용 측정 |

---

🔴 실험 페이지는 **한계** 섹션이 없으면 미완성이다. 로컬에서 앱과 부하 도구를 같이 돌린 결과는 절대 성능이 아니라 **같은 조건에서의 상대 개선치**다.
