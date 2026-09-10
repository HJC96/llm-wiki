---
title: index
type: moc
tags: [meta]
created: 2026-08-15
updated: 2026-08-31
---

# Index

위키에 **뭐가 있는지**의 카탈로그. Query를 시작할 때 LLM이 제일 먼저 읽는 파일.

시간순 기록은 [[log]], 주제별 탐색은 [[MOC-홈]], 규칙은 [[CLAUDE]].

> Ingest / Query 파일링이 끝날 때마다 이 파일을 갱신한다. 페이지마다 **링크 + 한 줄 요약** 한 행.

---

## 현황

| 레이어 | 개수 |
|---|---|
| 소스 (`pages/sources/`) | 14 |
| 개념 (`pages/concepts/`) | 69 |
| 엔티티 (`pages/entities/`) | 3 |
| 실험 (`pages/labs/`) | **14** |
| 종합 (`pages/syntheses/`) | 6 |
| 면접 (`pages/questions/`) | 8 |
| 실무 (`pages/private/`) 🔒 | 7 |
| MOC | 12 |

---

## 소스

원본 하나당 하나. 원문 요약이 아니라 "무엇을 뽑아 어디로 보냈나"의 기록.

| 페이지 | 종류 | 한 줄 | 갱신 |
|---|---|---|---|
| [[deep-dive 실험실]] | code | 직접 돌려본 실험 저장소. 모듈 14개 중 3개 처리 | 2026-08-16 |
| [[OpenTelemetry 분산 추적 실습]] | code | Collector → Tempo → Grafana. 코드 변경 없이 `-javaagent`로 계측 | 2026-09-10 |
| [[시스템 설계 분산 캐싱]] | lecture | 시스템 설계 수업 6장. 축출 정책과 노드 분배 | 2026-09-10 |
| [[블로그 글쓰기 스타일 분석]] | note | 블로그 6편에서 뽑은 문체·전개 기준 | 2026-09-10 |
| [[분산 트랜잭션 학습노트]] | lecture | 주문 시스템을 모놀리식 → MSA로 쪼갠 뒤 2PC·TCC·Saga로 트랜잭션을 다시 붙이는 과정 | 2026-08-15 |
| [[Optimistic Offline Lock (PoEAA)]] | article | 업무 트랜잭션이 여러 시스템 트랜잭션에 걸칠 때. 커밋 전 검증이 곧 락 획득 | 2026-08-22 |
| [[Pessimistic Offline Lock (PoEAA)]] | article | 먼저 시도할 건 낙관이되, 실패 비용이 크면 뒤집힌다 | 2026-08-22 |
| **[[결제 시스템 백엔드 학습 가이드]]** | lecture | 강의 PDF 15개 통합. 승인은 성공이 아니라 수렴이 목표다 | 2026-08-31 |
| [[트랜잭셔널 아웃박스 패턴 Q&A]] | 대화 | outbox INSERT를 트랜잭션 밖으로 빼면 패턴의 이득이 사라진다 | 2026-08-31 |
| [[낙관적 락 재시도와 트랜잭션 경계]] | 대화 | 충돌한 트랜잭션은 rollback-only. 재시도는 그 밖에서 | 2026-08-31 |
| [[wallet-service FK와 UNIQUE 생략]] | 대화 | FK가 조용히 거는 S 락과 승격 데드락 | 2026-08-31 |
| [[Spring WebFlux vs MVC]] | 대화 | Mono는 값이 아니라 처리 계획. 결제에서 WebFlux는 소수파 | 2026-08-31 |
| **[[도메인 모델이 이끄는 개발과 헥사고날 아키텍처]]** | lecture | 헥사고날이 실제로 요구하는 건 셋뿐이고 1순위 목표는 테스트 | 2026-08-31 |
| **[[JPA와 도메인 모델 분리 논쟁]]** | lecture | 분리의 대가는 조용히 사라지는 데이터. JPA 스펙이 도메인 모델을 위한 기술이라 말한다 | 2026-08-31 |

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
| [[캐시 축출 정책]] | TTL이 신선도면 축출은 공간. LRU·LFU와 O(1) 구조 | [[MOC-Spring]] | growing |
| [[일관된 해싱]] | 노드 수를 분모에 넣으면 확장이 곧 전면 미스 | [[MOC-분산시스템]] | seed |
| [[ArchUnit으로 아키텍처 강제하기]] | 코드리뷰로 지키던 합의를 CI가 지키게 | [[MOC-설계]] | growing |
| [[Micrometer 계측기 선택]] | 누적(Counter)·현재값(Gauge)·시간(Timer) 세 축 | [[MOC-인프라]] | growing |
| [[분산 추적]] | 지표가 "얼마나"면 추적은 "이 한 건이 어디를 지났나" | [[MOC-인프라]] · [[MOC-분산시스템]] | growing |
| [[부분 커밋]] | 자기 트랜잭션은 성공했는데 되돌릴 통로가 없는 상태 | [[MOC-분산시스템]] | growing |
| [[프록시 자기호출 문제]] | 네 애너테이션이 조용히 무시되는 한 가지 원인 | [[MOC-Spring]] | growing |
| [[암달의 법칙]] | 병목은 느린 쪽이 아니라 직렬 구간 비중이 큰 쪽에서 | [[MOC-Java]] · [[MOC-동시성]] | growing |
| [[조건부 상태 전이 선점]] | 조건부 UPDATE에 성공한 쪽만 처리하게 해 중복을 막는 방법 | [[MOC-동시성]] | growing |
| [[업무 트랜잭션과 시스템 트랜잭션]] | 사람이 느끼는 단위와 DB가 보장하는 단위는 다르다. `@Transactional`이 못 넘는 경계 | [[MOC-동시성]] 외 2 | growing |
| [[Optimistic Offline Lock]] | 커밋 직전 검증. 검증 성공이 곧 락 획득 — 충돌은 **끝에서** 드러난다 | [[MOC-동시성]] 외 2 | growing |
| [[Pessimistic Offline Lock]] | 시작 전에 점유해 충돌을 아예 없앤다. 대가는 동시성과 고아 락 | [[MOC-동시성]] · [[MOC-설계]] | growing |
| [[네임드 락]] | 트랜잭션이 아니라 **세션**에 종속되는 DB 락. 커넥션 풀과 부딪힌다 | [[MOC-동시성]] · [[MOC-데이터베이스]] | growing |
| **[[Outbox 패턴]]** | 두 시스템 쓰기를 한 DB 두 테이블 쓰기로 바꾼다 | [[MOC-분산시스템]] 외 1 | growing |
| [[Dual Write 문제]] | 순서를 바꿔도 사고는 이동만 한다. Outbox가 푸는 문제의 이름 | [[MOC-분산시스템]] 외 2 | growing |
| [[Inbox 패턴]] | 소비한 event_id를 고유 제약으로 기록해 중복을 무해하게 | [[MOC-분산시스템]] 외 1 | growing |
| [[정확히 한 번 전달의 불가능성]] | exactly-once는 전달의 성질이 아니라 전달+처리의 결과 | [[MOC-분산시스템]] | growing |
| [[Kafka 전달 보장]] | acks · min ISR · 오프셋 커밋 시점이 유실/중복 경계를 정한다 | [[MOC-분산시스템]] | growing |
| [[컨슈머 그룹과 리밸런싱]] | 한 파티션 = 한 컨슈머. 병렬성 상한과 순서 범위 | [[MOC-분산시스템]] | growing |
| [[컨슈머 재시도와 DLQ]] | 한 건이 파티션 전체를 막지 못하게 격리 | [[MOC-분산시스템]] | growing |
| [[Kafka Transaction의 범위]] | EOS는 Kafka 안에서만 원자적. 외부 DB는 안 들어온다 | [[MOC-분산시스템]] | growing |
| [[결과 불명 상태]] | 타임아웃은 실패가 아니다. UNKNOWN은 최종 상태가 아니라 대기열 | [[MOC-결제시스템]] | growing |
| [[복식부기 원장]] | 잔액은 합계일 뿐. 취소는 삭제가 아니라 반대 거래 | [[MOC-결제시스템]] | growing |
| [[복구 워커]] | 요청이 끊긴 뒤의 실패를 줍는다. stale 조건 + Lease | [[MOC-결제시스템]] | growing |
| [[원장 대사]] | 코드가 감지 못 하는 불일치를 바깥 기록과 맞춰 찾는다 | [[MOC-결제시스템]] | growing |
| [[Bulkhead]] | 스레드만이 아니라 커넥션 풀·동시성·유입량까지 가른다 | [[MOC-인프라]] · [[MOC-결제시스템]] | growing |
| [[낙관적 락 재시도 경계]] | 충돌한 트랜잭션은 rollback-only. 재시도는 그 밖에서 | [[MOC-동시성]] 외 2 | growing |
| [[외래키 제약과 락 경합]] | 명시적 락이 아니라 제약이 거는 S 락과 승격 데드락 | [[MOC-데이터베이스]] 외 2 | growing |
| [[갭 락과 넥스트키 락]] | 없는 행의 자리를 잠근다. 다른 키를 넣는 INSERT끼리도 부딪힘 | [[MOC-데이터베이스]] | growing |
| [[블로킹과 비동기는 다른 축]] | 두 축은 독립. `@Async` + JDBC는 비동기지만 논블로킹이 아니다 | [[MOC-동시성]] · [[MOC-Java]] | growing |
| [[이벤트 루프와 스레드 점유]] | 기다림에는 스레드가 필요 없다. 단일 요청은 오히려 느리다 | [[MOC-동시성]] | growing |
| [[도메인 모델]] | 개념·관계·규칙의 지도. 실체는 문서가 아니라 팀의 멘탈 모델 | [[MOC-설계]] | growing |
| [[DDD]] | 마지막 D는 Design. 현업 전문가가 빠지면 DDD가 아니다 | [[MOC-설계]] | growing |
| [[보편 언어]] | 대화·문서 **그리고 코드**가 같은 어휘를 쓴다 | [[MOC-설계]] | growing |
| [[도메인 모델 패턴]] | 단순 / 풍성한 / 애니믹. 애니믹은 패턴이 아니다 | [[MOC-설계]] | growing |
| [[애플리케이션 서비스]] | 도메인 모델에 없는 작업 단위 API를 채우는 얇은 층 | [[MOC-설계]] · [[MOC-Spring]] | growing |
| [[계층형 아키텍처]] | 제약은 둘뿐. 단방향 사용 + 제한된 인터페이스 | [[MOC-설계]] | growing |
| **[[헥사고날 아키텍처]]** | 실제 요구는 셋뿐. 육각형에 의미는 없고 오해가 다섯 개 | [[MOC-설계]] | growing |
| [[포트와 어댑터]] | Provided(롤리팝) / Required(소켓). Required도 애플리케이션이 소유 | [[MOC-설계]] | growing |
| [[애그리거트 경계 정하기]] | 함께 저장되고 함께 지켜질 것끼리. 루트만 public | [[MOC-설계]] | growing |
| [[orm.xml로 매핑 걷어내기]] | XML이 애노테이션을 오버라이드. 도메인 의미가 있는 것만 남긴다 | [[MOC-Spring]] · [[MOC-설계]] | growing |
| **[[테스트 가능한 설계란]]** | 테스트를 쓰기 어렵다는 감각은 취향이 아니라 설계 신호 | [[MOC-설계]] · [[MOC-면접]] | growing |
| [[단위 테스트와 통합 테스트의 경계]] | 무엇을 띄우느냐가 아니라 무엇이 깨졌을 때 실패해야 하느냐 | [[MOC-설계]] | growing |
| [[Actuator 엔드포인트 보안 경계]] | 조회만 있는 게 아니다. 노출 제어 + 인증 + 네트워크 경계 | [[MOC-Spring]] · [[MOC-인프라]] | growing |

---

## 엔티티

도구·라이브러리·프레임워크·시스템.

| 페이지 | 한 줄 | MOC | 상태 |
|---|---|---|---|
| [[Testcontainers]] | 실제 이미지를 띄워 H2의 가짜 안정감을 없앤다 | [[MOC-설계]] 외 2 | growing |
| [[Reactor]] | Mono/Flux. 값을 꺼내지 말고 그 위에서 조립한다. Lazy | [[MOC-Spring]] · [[MOC-동시성]] | growing |
| [[Spring WebFlux]] | Servlet 대신 Reactive Streams. 부분 도입은 이점이 0 | [[MOC-Spring]] | growing |

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
| [[결제 시스템에 WebFlux를 쓸 것인가]] | 결제 백엔드를 새로 만든다면 WebFlux를 고를 이유가 있나 | 중간 | 2026-08-31 |
| [[도메인 모델과 JPA 엔티티를 분리해야 하는가]] | `@Entity`를 어댑터로 빼고 도메인 엔티티와 따로 둬야 하나 | 높음 | 2026-08-31 |
| [[결제 시스템 키워드 지도]] | 결제 키워드 35개가 각각 위키 어디에 붙어 있나 | 높음 | 2026-09-05 |
| [[결제 도메인 개념과 백엔드 키워드의 연결]] | 결제 도메인의 어떤 사실이 어떤 백엔드 키워드를 요구하나 | 중간 | 2026-09-08 |

---

## 면접

| 페이지 | 주제 | 레벨 | Anki |
|---|---|---|---|
| [[MSA에서 트랜잭션은 어떻게 관리하나]] | 분산 | 심화 | ☐ |
| [[2PC의 문제는 무엇인가]] | 분산 | 심화 | ☐ |
| [[같은 요청이 두 번 들어와도 한 번만 처리되게 하려면]] | 동시성 | 기본 | ☐ |
| [[낙관적 락과 비관적 락 중 언제 무엇을]] | 동시성 | 기본 | ☐ |
| [[JPA @Version과 Optimistic Offline Lock의 차이]] | 동시성 | 심화 | ☐ |
| [[정확히 한 번 전달이 가능한가]] | 분산 | 심화 | ☐ |
| [[중복 처리를 어떻게 막았나]] | 동시성 | 기본 | ☐ |
| [[애그리거트 경계를 어떻게 정했나]] | 설계 | 심화 | ☐ |

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
| [[MOC-결제시스템]] | 승인 상태 머신·Outbox/Inbox·정산·복구·대사 |
| [[MOC-실험]] | deep-dive 모듈과 1:1 |
| [[MOC-출처]] | 책·강의 진입점 |
| [[MOC-면접]] | 질문 → 답 → 근거 |

---

## 미해결

Lint와 Ingest에서 나온 열린 항목. 처리되면 지운다.

- [x] ~~`분산_학습노트.md` Ingest~~ → [[분산 트랜잭션 학습노트]] (2026-08-15, 페이지 19개 배출)
- [x] ~~**[[Outbox 패턴]]** — 별도 소스 필요~~ (2026-08-31). **참조 9회로 볼트 최대 구멍이었다.** [[결제 시스템 백엔드 학습 가이드]] + [[트랜잭셔널 아웃박스 패턴 Q&A]]로 해소
- [ ] `~/Desktop/DDIA_1장_학습노트.md`, `~/Documents/DDIA/DDIA_5장_복제_학습노트.md`
- [x] ~~`deep-dive` 2PC·TCC·coupon-issue → 실험 페이지~~ (2026-08-16). **삼각형 첫 개통**
- [x] ~~`deep-dive` 캐시 3종~~ (2026-08-16). **캐시 축 개통 — 개념 0 → 10**
- [x] ~~`spring-test-infra` · `spring-boot-actuator`~~ (2026-08-16). **테스트·관측 축 개통, 엔티티 첫 페이지**
- [x] ~~`deep-dive` 14개 모듈 전부~~ (2026-08-16). **실험 축 완주**
- [x] ~~**실무 축** — `pages/private/`가 0~~ (2026-08-22). **삼각형 완성** — 편집 충돌 제어 판단 기록 + 소스 2건. 공개 일반화는 [[Optimistic Offline Lock]]에
- [ ] **[[Java 21 가상 스레드]]** — [[결제 시스템에 WebFlux를 쓸 것인가]]의 결론을 흔드는 변수인데 페이지가 없다. Ingest 우선순위
- [ ] `deep-dive` 테스트 코드 자체 (지금까지 README만 읽음)
- [ ] 업무 프로젝트 5건 → `pages/private/`에 판단 기록 (**3/5 완료**, 2026-08-31에 3건 추가). 남은 것 2건
- [ ] 🔴 **실패·회복 사례가 비어 있다** — 비공개 소재 보강 1순위
- [ ] **[[Coarse-Grained Lock]]** — PoEAA 16장 짝 패턴. 원문 미확보라 빈 링크로만 걸어 둠. 🟢 이번에 짝인 [[애그리거트 경계 정하기]]는 생겼다
- [ ] 🔴 **신규 개념 31개 중 23개가 개념 축에만 있다** (2026-08-31 lint) — 실험에도 실무에도 안 닿는다. 이번 ingest가 개념을 크게 늘렸지만 삼각형은 그만큼 안 만들어졌다
- [ ] 🔴 **결제 축도 수치가 0이다** — 신규 개념 16개가 전부 설계 원칙이고 실험에 안 닿는다. `deep-dive/labs/payment-system` 모듈이 있으므로 lab 페이지 후보: FK 유무별 데드락 발생률 · 낙관적 락 충돌률과 재시도 분포 · 커밋 후 발행 전 kill 시 Outbox 복구
- [ ] 오프라인 동시성 **수치가 없다** — 볼트의 락 실측은 전부 한 트랜잭션 안 기준. 요청이 나뉜 상황의 충돌 빈도는 미측정
- [ ] [[Optimistic Offline Lock]]의 inconsistent read 쪽 — 이번 컴파일은 lost update 중심으로만 갔다

### ⚠️ 충돌

페이지 간 모순. 해결되면 지운다.

- **[[Inbox 패턴]] ↔ [[외래키 제약과 락 경합]]** (2026-08-31) — 전자는 고유 제약을 중복 판정의 **최종 수단**으로 쓰라 하고, 후자는 유니크 인덱스 INSERT의 갭락 때문에 **빼라** 한다. 현재 판단: **조건이 갈린다**(같은 부모 행에 INSERT+UPDATE가 몰리는 정산 경로 vs 일반 컨슈머). 🔴 볼트에 락 경합 실측치가 없어 어느 쪽도 일반 규칙으로 승격하지 않았다. **해소 조건: `deep-dive`에서 FK/UNIQUE 유무별 데드락 발생률·처리량 측정**
- **`AFTER_COMMIT` outbox INSERT** (2026-08-31) — [[트랜잭셔널 아웃박스 패턴 Q&A]]의 논리와 `pages/private/`의 실무 파이프라인 구조가 어긋난다. **판단 완료**: 구조를 바꾸는 게 아니라 그 알림을 best-effort로 재정의하고 "Outbox 패턴 적용"이라는 명명을 철회했다. 비공개 페이지에 기록
