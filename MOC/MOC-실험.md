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
소스 페이지는 [[deep-dive 실험실]].
실험 결과 덤프(로그·벤치마크 출력)는 `raw/code/`에 넣고, 해석은 `pages/labs/`에 쓴다.

## 동시성

| 모듈 | 페이지 | 확인한 것 |
|---|---|---|
| `coupon-issue` | [[선착순 쿠폰 발급 동시성]] ✅ | 9가지 실행 시간 비교. **낙관적 락 3156ms(최악) / Redis Lua 41ms(최선)** |
| `seat-reservation` | [[좌석 예약 동시성]] ✅ | 버스트 부하: 직접 쓰기 88건 실패 vs Kafka 경유 0건 |

## 분산 트랜잭션

기준선 → 문제 재현 → 해법 순서로 읽는다.

| 모듈 | 페이지 | 확인한 것 |
|---|---|---|
| `distributed-transaction-monolith` | [[분산 트랜잭션 기준선 - 모놀리식]] ✅ | 쪼개기 전 기준선. 실패해도 예약은 `CREATED`로 남아 재실행 |
| `distributed-transaction-msa` | [[분산 트랜잭션 기준선 - MSA]] ✅ | **부분 커밋 재현.** 좌석은 커밋됐는데 되돌릴 수단이 없다 |
| `distributed-transaction-2pc` | [[2PC 실험]] ✅ | `XA RECOVER`로 in-doubt 발견, `ERROR 1205` 블로킹 재현 |
| `distributed-transaction-tcc` | [[TCC 실험]] ✅ | **2PC와 같은 SQL, 뒤집힌 결과.** 안전 시나리오 4종 |

## 캐시

| 모듈 | 페이지 | 확인한 것 |
|---|---|---|
| `cache-patterns` | [[캐시 패턴 비교]] ✅ | 읽기 2종·쓰기 3종 + **실패 모드 4종** (Race / Stampede / Penetration / Avalanche) |
| `spring-cache-local` | [[Spring Cache 로컬 캐시]] ✅ | 키 생성 규칙의 함정, 테이블 버전 키 |
| `spring-cache-redis` | [[Spring Cache Redis]] ✅ | 추상화로 안 되는 것들을 `RedisTemplate`으로 |

## Spring · 테스트

| 모듈 | 페이지 | 확인한 것 |
|---|---|---|
| `spring-test-infra` | [[Testcontainers 테스트 인프라]] ✅ | 정적 설정을 **일부러 틀리게** 두고 동적 주입을 증명. ArchUnit 계층 규칙 |
| `spring` | [[@Async vs ExecutorService]] ✅ | 무엇이 드러나고 숨나. self-invocation 재현 |
| `spring-data-jpa` | [[낙관적 락과 Hibernate SQL 관찰]] ✅ | `UPDATE ... WHERE version = 0` → affected rows 0 |
| `spring-boot-actuator` | [[Actuator 커스텀 헬스 체크]] ✅ | Micrometer 12단계. 계측기 선택 기준과 cardinality |
| `java-sandbox` | [[BouncyCastle Provider 등록 비용]] ✅ | 1,526배 차이. **그런데 빠른 쪽이 확장이 안 된다** |

---

🔴 실험 페이지는 **한계** 섹션이 없으면 미완성이다. 로컬에서 앱과 부하 도구를 같이 돌린 결과는 절대 성능이 아니라 **같은 조건에서의 상대 개선치**다.
