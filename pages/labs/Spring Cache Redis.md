---
title: Spring Cache Redis
type: lab
status: growing
tags: [cache, redis, spring]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-실험]]", "[[MOC-Spring]]"]
repo: deep-dive/labs/spring-cache-redis
created: 2026-08-16
updated: 2026-08-16
---

## 확인하려던 것

Redis를 공용 캐시로 쓸 때 **`@Cacheable` 추상화로 되는 것과 `RedisTemplate`을 직접 써야 하는 것**의 경계. 그리고 [[캐시 패턴 비교]]에서 인메모리로 봤던 방어들이 **실제 Redis에서 어떻게 구현되는지.**

## 실험 설계

- Testcontainers **Redis + MySQL** (인메모리 아님)
- 두 경로를 나란히 놓는다 — Spring Cache 추상화(`@Cacheable`) vs `RedisTemplate` 직접 호출
- Redis에 **실제로 어떤 형태로 저장되는지**와 어떤 명령이 나가는지 관찰

## 결과

### Null Caching — 없는 것도 캐시한다

없는 ID(`999L`)를 **20번** 조회했을 때:

```
1회차  GET book:999 → miss → MySQL SELECT → 결과 없음
       SET book:999 "__NULL__" EX 30
2~20회 GET book:999 → "__NULL__" → 즉시 Optional.empty()
```

🟢 **MySQL 조회는 처음 한 번뿐이다.** 없는 값을 `"__NULL__"` 센티널로 저장해 [[Cache Penetration]]을 막는다.

🔴 TTL을 짧게(30초) 잡는 게 핵심이다. 길면 나중에 **실제로 생성된 데이터가 계속 "없음"으로 보인다.**

### TTL Jitter — 만료를 흩는다

```java
cacheBooksWithJitter(books, 60초, 10초)
// 키마다: key hash로 jitter 계산 → SET book:id JSON EX 60~70초
```

🟢 같은 배치로 넣은 키들의 TTL을 조회하면 **서로 다른 값**이 나온다. 한꺼번에 만료돼 저장소로 몰리는 [[Cache Avalanche]]를 막는다.

🟢 **jitter를 key hash로 계산한 게 중요하다.** 난수로 하면 같은 키를 다시 캐싱할 때마다 만료 시점이 달라진다.

### Hot Key — 분산 락 + Double-Checked Locking

`RedisHotKeyLockTest`가 락 없는 경우와 있는 경우를 비교한다. 인기 키가 동시에 만료되면 여러 요청이 한꺼번에 저장소로 내려간다([[Cache Stampede]]).

방어는 [[Redis 분산락]] + **DCL** — 락을 얻은 뒤 캐시를 **한 번 더** 확인한다. 대기하던 요청들이 락을 얻었을 땐 이미 앞선 요청이 채워 놨기 때문이다.

### 추상화 vs 직접 호출의 경계

| | `@Cacheable` | `RedisTemplate` |
|---|---|---|
| 단순 조회 캐싱 | ✅ 한 줄 | 불필요하게 장황 |
| Null Caching 센티널 | ❌ | ✅ |
| TTL Jitter (키마다 다른 TTL) | ❌ | ✅ |
| DCL·분산 락 | ❌ | ✅ |
| 자료구조 사용 (List·Set·ZSet) | ❌ | ✅ |

🟡 **추상화는 "캐시를 쓴다"까지만 해 준다.** 캐시가 무너지는 방식을 방어하는 건 전부 직접 짜야 한다.

## 해석

🟡 [[캐시 패턴 비교]]의 인메모리 방어들이 Redis에서는 **다른 모습**이 된다 — `NegativeCachingCache` → `"__NULL__"` 센티널 + 짧은 TTL, `ExpiringCache` + jitter → `SET ... EX 60~70`, `SingleFlightCache` → 분산 락 + DCL. 아이디어는 같고 구현 층이 다르다.

💬 [[분산 트랜잭션 학습노트]]의 결론이 여기서도 반복된다 — **Spring은 메커니즘을 주고 정책은 주지 않는다.** TTL 길이, jitter 폭, 센티널 값, 락 대기 정책은 전부 내가 정한다.

## 한계

🔴 **처리량·지연을 재지 않았다.** hit/miss 동작과 저장 형태를 확인한 실험이지 성능 실험이 아니다. "Redis 캐시가 얼마나 빠른가"는 답할 수 없다.

🔴 **단일 Redis 노드다.** 클러스터에서의 키 분산, 페일오버 중 락 동작, [[Redis 분산락의 함정]](TTL 만료와 GC 정지가 겹칠 때)은 재현되지 않았다.

🔴 **직렬화 비용을 따로 재지 않았다.** JSON 직렬화가 캐시 이득을 얼마나 깎는지는 범위 밖이다.

🔴 Hot Key 방어의 **락 대기 시간**이 만드는 지연은 관찰하지 않았다. DCL은 저장소 호출을 줄이지만 대기를 만든다.

## 연결

- 개념: [[Cache Penetration]] — Null Caching이 막는 것
- 개념: [[Cache Avalanche]] — TTL Jitter가 막는 것
- 개념: [[Cache Stampede]] — 분산 락 + DCL이 막는 것
- 개념: [[Cache Aside]] · [[Spring Cache 추상화]]
- 개념: [[Redis 분산락]] — Hot Key 방어에 쓰인 것
- 실험: [[캐시 패턴 비교]] — 같은 방어를 인메모리로
- 실험: [[Spring Cache 로컬 캐시]] — 같은 추상화를 로컬로
- 코드: `~/Desktop/git/deep-dive/labs/spring-cache-redis/`
- 원본: `raw/code/spring-cache-redis.md`
