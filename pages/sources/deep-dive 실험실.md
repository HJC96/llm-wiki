---
title: deep-dive 실험실
type: source
kind: code
status: growing
tags: [concurrency, distributed-transaction, test]
moc: ["[[MOC-실험]]", "[[MOC-출처]]"]
created: 2026-08-16
updated: 2026-08-16
---

## 무엇

공부하다 직접 돌려보고 싶은 것을 모듈로 만들어 실험하는 저장소. **주제 하나당 `labs/` 아래 모듈 하나**, 모듈마다 README + JUnit 테스트.

`~/Desktop/git/deep-dive` — 총 14개 모듈. **14개 전부 처리 완료** (2026-08-16 4차).

## 핵심 주장

1. 🟡 경합이 심할수록 [[낙관적 락]]이 최악이다 — 200 요청이 한 로우를 다투면 **19배** 느려진다.
2. 🟢 원자적 연산(Redis Lua 41ms)이 락 방식(429~1312ms)보다 한 자릿수 빠르다. **락을 안 쓰는 게 가장 싸다.**
3. 🟡 [[2PC]]에서 결정을 못 들은 참여자는 **혼자서 커밋도 롤백도 판단할 수 없다.** 커밋하자니 남이 NO였을 수 있고, 롤백하자니 이미 YES를 약속했다.
4. 🟢 `XA RECOVER`는 커넥션과 무관하게 서버에 남은 미결 트랜잭션을 찾아준다 — in-doubt를 **발견 가능하게** 만드는 유일한 수단.
5. 🟡 **같은 자리에 같은 SQL을 놓으면 2PC는 `ERROR 1205`, TCC는 통과.** TCC가 블로킹을 없앤 증거이자, 격리를 포기한 증거이기도 하다.
6. 🟡 TCC에서 **빈 취소는 무시가 아니라 기록이어야 한다.** 그냥 넘기면 뒤늦게 도착한 Try가 잡은 자원을 아무도 회수하지 않는다(매달림).
7. 🟢 JTA를 쓰면 **편해지는 건 코드지 성질이 아니다.** 블로킹은 그대로 남는다.

## 여기서 나온 페이지

| 모듈 | 페이지 | 무엇을 가져갔나 |
|---|---|---|
| `coupon-issue` | [[선착순 쿠폰 발급 동시성]] | 9가지 방식 실행 시간 비교표 |
| `distributed-transaction-2pc` | [[2PC 실험]] | in-doubt 재현, `XA RECOVER`, `ERROR 1205` |
| `distributed-transaction-tcc` | [[TCC 실험]] | 2PC와 같은 SQL 대조, 안전 시나리오 4종 |
| — | [[비관적 락]] | 신규 개념 (실험이 수치를 줌) |
| — | [[원자적 UPDATE로 푸는 동시성]] | 신규 개념 (실험이 수치를 줌) |
| `cache-patterns` | [[캐시 패턴 비교]] | 읽기·쓰기 전략 5종, 실패 모드 4종 |
| `spring-cache-local` | [[Spring Cache 로컬 캐시]] | 키 생성 규칙, 테이블 버전 키 |
| `spring-cache-redis` | [[Spring Cache Redis]] | Null Caching, TTL Jitter, Hot Key DCL |
| `spring-test-infra` | [[Testcontainers 테스트 인프라]] | 동적 프로퍼티 주입, ArchUnit 계층 규칙 |
| `spring-boot-actuator` | [[Actuator 커스텀 헬스 체크]] | Micrometer 계측기 선택 기준, cardinality |
| `distributed-transaction-monolith` | [[분산 트랜잭션 기준선 - 모놀리식]] | 쪼개기 전 기준선 |
| `distributed-transaction-msa` | [[분산 트랜잭션 기준선 - MSA]] | 부분 커밋 재현 |
| `seat-reservation` | [[좌석 예약 동시성]] | 버스트 부하 88건 실패 vs 0건 |
| `spring-data-jpa` | [[낙관적 락과 Hibernate SQL 관찰]] | `@Version` 발생 SQL |
| `spring` | [[@Async vs ExecutorService]] | self-invocation 재현 |
| `java-sandbox` | [[BouncyCastle Provider 등록 비용]] | JMH + 프로파일러. 암달의 법칙 |

## 기존 위키와의 관계

**보강 — 이번 Ingest의 본체다.** 개념만 있던 페이지에 처음으로 숫자와 재현 결과가 붙었다.

- [[2PC]] — "블로킹이 대가"가 `ERROR 1205`와 `XA RECOVER` 출력으로 확인됨
- [[TCC]] — "락 대신 예약 상태"가 **같은 SQL 대조 표**로 확인됨
- [[낙관적 락]] — "충돌이 드물 때만"이라는 전제에 19× 수치가 붙음
- [[Redis 분산락]] — 1312ms. 왕복 비용이 있다는 사실이 수치화됨
- [[Lost Update]] — 락 없음 케이스가 재현(최종 재고 198 아닌 199)
- [[멱등성]] — TCC 안전 시나리오 4종이 전부 이 개념

**⚠️ 충돌** — 없음.

## 아직 안 다룬 것

- **남은 모듈 없음.** 14개 전부 처리
- **테스트 코드 자체** — 전 회차에서 README만 읽었다. `src/test` 코드는 안 봤다
- **테스트 코드 자체** — 이번엔 README만 가져왔다. 실제 `src/test` 코드는 안 읽었다
- 2PC 코디네이터 결정 로그 / TCC 코디네이터 사망 시나리오 — 실험이 명시적으로 범위 밖으로 둠

## 원본

`raw/code/` — `coupon-issue.md` · `distributed-transaction-2pc.md` · `distributed-transaction-tcc.md` · `cache-patterns.md` · `spring-cache-local.md` · `spring-cache-redis.md`
코드 원본: `~/Desktop/git/deep-dive/labs/`
