---
title: Spring Cache 추상화
type: concept
status: growing
tags: [cache, spring, spring-boot]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-Spring]]"]
created: 2026-08-16
updated: 2026-08-16
---

## 한 줄 정의

🟡 `@Cacheable` 한 줄이 [[Cache Aside]] 흐름을 프록시로 대신 짜 준다. **캐시를 쓰는 것까지만 해 주고, 캐시가 무너지는 방식은 방어해 주지 않는다.**

## 왜 필요한가

miss 확인 → 저장소 조회 → 캐시 적재는 메서드마다 같은 모양으로 반복된다. 그 반복을 애너테이션으로 걷어낸다. 구현체(로컬 맵 / Redis / Caffeine)를 바꿔도 코드가 그대로인 것도 이점이다.

## 어떻게 동작하는가

| 애너테이션 | 하는 일 | 대응 |
|---|---|---|
| `@Cacheable` | 있으면 반환, 없으면 실행 후 저장 | [[Cache Aside]] 읽기 |
| `@CachePut` | **항상 실행**하고 결과를 저장 | Write Through |
| `@CacheEvict` | 키를 제거 | Write Around |

`@Cacheable`과 `@CachePut`의 차이가 자주 헷갈린다 — 🔴 **`@CachePut`은 캐시에 값이 있어도 메서드를 실행한다.** 쓰기 경로에 붙이는 것이라서 그렇다.

## 코드에 닿는 지점

```java
@Cacheable(cacheNames = "bookById")          // 키는 SimpleKeyGenerator 가 만든다
public Book findBookById(long id) { ... }
```

키 생성 규칙과 그 함정은 [[캐시 키 설계]]에.

## 트레이드오프

🔴 **프록시 기반이라 자기호출에서 안 먹는다.** 같은 클래스 안에서 자기 메서드를 부르면 프록시를 안 거쳐 캐싱이 통째로 무시된다 — `@Transactional`·`@Retryable`과 같은 함정이다. → [[프록시 자기호출 문제]]

🔴 **추상화로 안 되는 것이 꽤 많다.** [[Spring Cache Redis]]에서 확인된 경계:

| | `@Cacheable` | `RedisTemplate` |
|---|---|---|
| 단순 조회 캐싱 | ✅ | 장황 |
| Null 센티널 + 별도 TTL ([[Cache Penetration]]) | ❌ | ✅ |
| 키마다 다른 TTL ([[Cache Avalanche]]) | ❌ | ✅ |
| 분산 락 + DCL ([[Cache Stampede]]) | ❌ | ✅ |
| Redis 자료구조 (List·Set·ZSet) | ❌ | ✅ |

🟡 **정리하면 — 정상 경로는 추상화로, 방어는 직접 짠다.** 캐시가 무너지는 세 방식을 막으려면 결국 `RedisTemplate`으로 내려가야 한다.

💬 [[분산 트랜잭션 학습노트]]의 결론이 여기서도 그대로다 — **Spring은 메커니즘을 주고 정책은 주지 않는다.**

## 연결

- [[Cache Aside]] — `@Cacheable`이 만드는 흐름
- [[캐시 쓰기 전략]] — `@CachePut` / `@CacheEvict`
- [[캐시 키 설계]] — 키 생성 규칙과 함정
- [[프록시 자기호출 문제]] 🔴
- [[로컬 캐시와 인스턴스 정합성]]
- 실험: [[Spring Cache 로컬 캐시]] · [[Spring Cache Redis]]
