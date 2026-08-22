---
title: index
type: moc
tags: [meta]
created: 2026-08-15
updated: 2026-08-22
---

# Index

위키에 **뭐가 있는지**의 카탈로그. Query를 시작할 때 LLM이 제일 먼저 읽는 파일.

시간순 기록은 [[log]], 주제별 탐색은 [[MOC-홈]], 규칙은 [[CLAUDE]].

> Ingest / Query 파일링이 끝날 때마다 이 파일을 갱신한다. 페이지마다 **링크 + 한 줄 요약** 한 행.

---

## 현황

| 레이어 | 개수 |
|---|---|
| 소스 (`pages/sources/`) | 4 |
| 개념 (`pages/concepts/`) | 35 |
| 엔티티 (`pages/entities/`) | **1** |
| 실험 (`pages/labs/`) | **14** |
| 종합 (`pages/syntheses/`) | 2 |
| 면접 (`pages/questions/`) | 5 |
| 실무 (`pages/private/`) 🔒 | **2** |
| MOC | 11 |

---

## 소스

원본 하나당 하나. 원문 요약이 아니라 "무엇을 뽑아 어디로 보냈나"의 기록.

| 페이지 | 종류 | 한 줄 | 갱신 |
|---|---|---|---|
| [[deep-dive 실험실]] | code | 직접 돌려본 실험 저장소. 모듈 14개 중 3개 처리 | 2026-08-16 |
| [[분산 트랜잭션 학습노트]] | lecture | 주문 시스템을 모놀리식 → MSA로 쪼갠 뒤 2PC·TCC·Saga로 트랜잭션을 다시 붙이는 과정 | 2026-08-15 |
| [[Optimistic Offline Lock (PoEAA)]] | article | 업무 트랜잭션이 여러 시스템 트랜잭션에 걸칠 때. 커밋 전 검증이 곧 락 획득 | 2026-08-22 |
| [[Pessimistic Offline Lock (PoEAA)]] | article | 먼저 시도할 건 낙관이되, 실패 비용이 크면 뒤집힌다 | 2026-08-22 |

---

## 개념

| 페이지 | 한 줄 | MOC | 상태 |
|---|---|---|---|
| [[분산 트랜잭션이 필요한 순간]] | `@Transactional`이 여는 건 커넥션 하나의 트랜잭션. 쪼개면 사라진다 | [[MOC-분산시스템]] | growing |
| [[2PC]] | 되돌릴 수 없는 지점을 전원 확인 뒤로 미룬다. 대가는 가용성 | [[MOC-분산시스템]] | growing |
| [[TCC]] | 2PC의 Prepare/Commit을 비즈니스 API로 다시 만든 것 | [[MOC-분산시스템]] | growing |
| [[Saga 패턴]] | 즉시 실행하고 보상으로 되돌린다. Orchestration / Choreography | [[MOC-분산시스템]] | growing |
| [[최종적 일관성]] | "언제나 맞다"가 아니라 "지금은 틀릴 수 있지만 수렴한다" | [[MOC-분산시스템]] | growing |
| [[멱등성]] | 두 번째 실행이 아무 일 없이 첫 번째와 같은 응답을 돌려주는 것 | [[MOC-분산시스템]] · [[MOC-동시성]] | growing |
| [[낙관적 락]] | 충돌을 막는 게 아니라 감지하는 장치. 재시도는 트랜잭션 밖에서 | [[MOC-동시성]] 외 2 | growing |
| [[Lost Update]] | 읽고-계산하고-쓰는 사이에 먼저 쓴 갱신이 덮이는 것 | [[MOC-동시성]] · [[MOC-데이터베이스]] | growing |
| [[Redis 분산락]] | SETNX + TTL + finally + 소유권 확인. 락이 트랜잭션보다 바깥 | [[MOC-동시성]] · [[MOC-분산시스템]] | growing |
| [[재시도와 백오프]] | 실패를 줄이는 게 아니라 반복하는 장치. 멱등성 위에서만 안전 | [[MOC-분산시스템]] · [[MOC-Spring]] | growing |
| [[커밋 후 이벤트 발행]] | 되돌릴 수 있는 쪽(DB)을 먼저 확정하고 발행을 나중에 | [[MOC-Spring]] · [[MOC-분산시스템]] | growing |
| [[Kafka 메시지 키와 순서 보장]] | 순서는 파티션 단위. 키가 순서와 단일 처리를 동시에 준다 | [[MOC-분산시스템]] | growing |
| [[실패 사실의 기록]] | 자동 복구를 못 해도 유실은 막는다. 셋은 감시되고 있어야 정상 | [[MOC-분산시스템]] · [[MOC-인프라]] | growing |
| [[비관적 락]] | 감지가 아니라 차단. 경합이 잦을 때 (429ms) | [[MOC-동시성]] 외 2 | growing |
| [[원자적 UPDATE로 푸는 동시성]] | 읽지 않고 쓴다. 틈 자체를 없앤다 (369ms) | [[MOC-동시성]] · [[MOC-데이터베이스]] | growing |
| [[Cache Aside]] | 서비스가 miss를 직접 처리. 가장 단순해서 기본값 | [[MOC-Spring]] | growing |
| [[Read Through]] | miss 처리를 캐시 계층으로 올린 것 | [[MOC-Spring]] | growing |
| [[캐시 쓰기 전략]] | Write Through / Around / Behind — 한 질문의 세 답 | [[MOC-Spring]] | growing |
| [[Cache Stampede]] | 인기 키 만료 순간 요청이 한꺼번에 저장소로 | [[MOC-Spring]] · [[MOC-동시성]] | growing |
| [[Cache Penetration]] | 없는 키는 캐시에 안 남아 매번 관통 | [[MOC-Spring]] | growing |
| [[Cache Avalanche]] | 많은 키가 같은 시각에 만료 | [[MOC-Spring]] | growing |
| [[캐시 정합성 Race Condition]] | 옛 값이 뒤늦게 캐시에 들어와 눌러앉음 | [[MOC-Spring]] · [[MOC-동시성]] | growing |
| [[Spring Cache 추상화]] | 정상 경로는 애너테이션, 방어는 RedisTemplate | [[MOC-Spring]] | growing |
| [[캐시 키 설계]] | 좁으면 공유 사고, 넓으면 히트율 저하 | [[MOC-Spring]] | growing |
| [[로컬 캐시와 인스턴스 정합성]] | WAS 2대면 evict가 전파 안 됨. 테이블 버전 키 | [[MOC-Spring]] | growing |
| [[ArchUnit으로 아키텍처 강제하기]] | 코드리뷰로 지키던 합의를 CI가 지키게 | [[MOC-설계]] | growing |
| [[Micrometer 계측기 선택]] | 누적(Counter)·현재값(Gauge)·시간(Timer) 세 축 | [[MOC-인프라]] | growing |
| [[부분 커밋]] | 자기 트랜잭션은 성공했는데 되돌릴 통로가 없는 상태 | [[MOC-분산시스템]] | growing |
| [[프록시 자기호출 문제]] | 네 애너테이션이 조용히 무시되는 한 가지 원인 | [[MOC-Spring]] | growing |
| [[암달의 법칙]] | 병목은 느린 쪽이 아니라 직렬 구간 비중이 큰 쪽에서 | [[MOC-Java]] · [[MOC-동시성]] | growing |
| [[조건부 상태 전이 선점]] | 조건부 UPDATE에 성공한 쪽만 처리하게 해 중복을 막는 방법 | [[MOC-동시성]] | growing |
| [[업무 트랜잭션과 시스템 트랜잭션]] | 사람이 느끼는 단위와 DB가 보장하는 단위는 다르다. `@Transactional`이 못 넘는 경계 | [[MOC-동시성]] 외 2 | growing |
| [[Optimistic Offline Lock]] | 커밋 직전 검증. 검증 성공이 곧 락 획득 — 충돌은 **끝에서** 드러난다 | [[MOC-동시성]] 외 2 | growing |
| [[Pessimistic Offline Lock]] | 시작 전에 점유해 충돌을 아예 없앤다. 대가는 동시성과 고아 락 | [[MOC-동시성]] · [[MOC-설계]] | growing |
| [[네임드 락]] | 트랜잭션이 아니라 **세션**에 종속되는 DB 락. 커넥션 풀과 부딪힌다 | [[MOC-동시성]] · [[MOC-데이터베이스]] | growing |

---

## 엔티티

도구·라이브러리·프레임워크·시스템.

| 페이지 | 한 줄 | MOC | 상태 |
|---|---|---|---|
| [[Testcontainers]] | 실제 이미지를 띄워 H2의 가짜 안정감을 없앤다 | [[MOC-설계]] 외 2 | growing |

---

## 실험

`~/Desktop/git/deep-dive/labs/` 모듈과 1:1. 숫자가 있어야 실험 페이지다.

| 페이지 | 확인한 것 | 모듈 | 상태 |
|---|---|---|---|
| [[선착순 쿠폰 발급 동시성]] | 9가지 동시성 제어 실행 시간. 낙관적 락 3156ms / Redis Lua 41ms | `coupon-issue` | growing |
| [[2PC 실험]] | `XA RECOVER`로 in-doubt 발견, `ERROR 1205` 블로킹 재현 | `distributed-transaction-2pc` | growing |
| [[TCC 실험]] | 2PC와 같은 SQL·뒤집힌 결과. 안전 시나리오 4종 | `distributed-transaction-tcc` | growing |
| [[캐시 패턴 비교]] | 읽기 2종·쓰기 3종 + 실패 모드 4종. 인메모리라 시간이 아닌 호출 횟수 | `cache-patterns` | growing |
| [[Spring Cache 로컬 캐시]] | 키 생성 규칙의 함정, 테이블 버전 키로 세대 넘기기 | `spring-cache-local` | growing |
| [[Spring Cache Redis]] | Null Caching 20회 중 MySQL 1회, TTL Jitter, Hot Key DCL | `spring-cache-redis` | growing |
| [[Testcontainers 테스트 인프라]] | 정적 설정을 일부러 틀리게 두고 동적 주입을 증명. ArchUnit | `spring-test-infra` | growing |
| [[Actuator 커스텀 헬스 체크]] | Micrometer 12단계. 계측기 선택 기준과 cardinality | `spring-boot-actuator` | growing |
| [[분산 트랜잭션 기준선 - 모놀리식]] | 쪼개기 전 기준선. 실패해도 예약은 CREATED로 남아 재실행 | `...-monolith` | growing |
| [[분산 트랜잭션 기준선 - MSA]] | 부분 커밋 재현. 좌석은 커밋됐는데 되돌릴 수단이 없다 | `...-msa` | growing |
| [[좌석 예약 동시성]] | 버스트 부하 — 직접 쓰기 88건 실패 / Kafka 경유 0건 | `seat-reservation` | growing |
| [[낙관적 락과 Hibernate SQL 관찰]] | `UPDATE ... WHERE version = 0` → affected rows 0 | `spring-data-jpa` | growing |
| [[@Async vs ExecutorService]] | 무엇이 드러나고 숨나. self-invocation 재현 | `spring` | growing |
| [[BouncyCastle Provider 등록 비용]] | 1,526배 차이. **그런데 빠른 쪽이 확장이 안 된다** | `java-sandbox` | growing |

---

## 종합

질문의 답이 쌓이는 곳. 비교·분석·발견한 연결.

| 페이지 | 질문 | 확신도 | 갱신 |
|---|---|---|---|
| [[분산 트랜잭션 네 가지 비교]] | 2PC·TCC·Saga 중 무엇을 언제 고르는가 | 높음 | 2026-08-15 |
| [[조회와 저장이 다른 요청일 때 무엇으로 막는가]] | 요청이 나뉜 구간의 Lost Update를 무엇으로 막는가 | 높음 | 2026-08-22 |

---

## 면접

| 페이지 | 주제 | 레벨 | Anki |
|---|---|---|---|
| [[MSA에서 트랜잭션은 어떻게 관리하나]] | 분산 | 심화 | ☐ |
| [[2PC의 문제는 무엇인가]] | 분산 | 심화 | ☐ |
| [[같은 요청이 두 번 들어와도 한 번만 처리되게 하려면]] | 동시성 | 기본 | ☐ |
| [[낙관적 락과 비관적 락 중 언제 무엇을]] | 동시성 | 기본 | ☐ |
| [[JPA @Version과 Optimistic Offline Lock의 차이]] | 동시성 | 심화 | ☐ |

---

## MOC

| MOC | 범위 |
|---|---|
| [[MOC-홈]] | 모든 MOC의 허브 |
| [[MOC-Java]] | 언어·JVM·GC·메모리 모델 |
| [[MOC-Spring]] | 컨테이너·AOP·트랜잭션·캐시·배치 |
| [[MOC-데이터베이스]] | 인덱스·락·격리수준·MongoDB |
| [[MOC-분산시스템]] | 복제·일관성·분산 트랜잭션·Kafka |
| [[MOC-동시성]] | 락 전략·원자적 연산·스레드 |
| [[MOC-인프라]] | Docker·K8s·AWS·CI/CD·관측 |
| [[MOC-설계]] | DDD·객체지향·패턴·테스트 가능한 설계 |
| [[MOC-실험]] | deep-dive 모듈과 1:1 |
| [[MOC-출처]] | 책·강의 진입점 |
| [[MOC-면접]] | 질문 → 답 → 근거 |

---

## 미해결

Lint와 Ingest에서 나온 열린 항목. 처리되면 지운다.

- [x] ~~`분산_학습노트.md` Ingest~~ → [[분산 트랜잭션 학습노트]] (2026-08-15, 페이지 19개 배출)
- [ ] **[[Outbox 패턴]]** — 소스가 이름만 언급하고 범위 밖으로 뺐다. 별도 소스 필요
- [ ] `~/Desktop/DDIA_1장_학습노트.md`, `~/Documents/DDIA/DDIA_5장_복제_학습노트.md`
- [x] ~~`deep-dive` 2PC·TCC·coupon-issue → 실험 페이지~~ (2026-08-16). **삼각형 첫 개통**
- [x] ~~`deep-dive` 캐시 3종~~ (2026-08-16). **캐시 축 개통 — 개념 0 → 10**
- [x] ~~`spring-test-infra` · `spring-boot-actuator`~~ (2026-08-16). **테스트·관측 축 개통, 엔티티 첫 페이지**
- [x] ~~`deep-dive` 14개 모듈 전부~~ (2026-08-16). **실험 축 완주**
- [x] ~~**실무 축** — `pages/private/`가 0~~ (2026-08-22). **삼각형 완성** — 편집 충돌 제어 판단 기록 + 소스 2건. 공개 일반화는 [[Optimistic Offline Lock]]에
- [ ] `deep-dive` 테스트 코드 자체 (지금까지 README만 읽음)
- [ ] 업무 프로젝트 5건 → `pages/private/`에 판단 기록 (1/5 완료)
- [ ] **[[Coarse-Grained Lock]]** — PoEAA 16장 짝 패턴. 원문 미확보라 빈 링크로만 걸어 둠
- [ ] 오프라인 동시성 **수치가 없다** — 볼트의 락 실측은 전부 한 트랜잭션 안 기준. 요청이 나뉜 상황의 충돌 빈도는 미측정
- [ ] [[Optimistic Offline Lock]]의 inconsistent read 쪽 — 이번 컴파일은 lost update 중심으로만 갔다

### ⚠️ 충돌

페이지 간 모순. 해결되면 지운다.

- _(없음)_
