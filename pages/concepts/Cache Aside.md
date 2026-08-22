---
title: Cache Aside
type: concept
status: growing
tags: [cache, redis]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-Spring]]"]
created: 2026-08-16
updated: 2026-08-16
---

## 한 줄 정의

🟡 **서비스 코드가 miss를 직접 처리한다.** `cache.get` → miss면 `store.findById` → `cache.put`.

## 왜 필요한가

가장 단순하고, 그래서 기본값이다. 캐시가 죽어도 저장소 조회 경로가 그대로 살아 있어 **캐시를 선택적 최적화로 둘 수 있다.**

## 어떻게 동작하는가

```java
public Product find(Long id) {
    Product cached = cache.get(id);
    if (cached != null) return cached;          // hit
    Product p = store.findById(id).orElseThrow();
    cache.put(id, p);                            // 서비스가 직접 채운다
    return p;
}
```

쓰기는 보통 [[캐시 쓰기 전략]]의 **Write Around**과 짝을 이룬다 — 저장 후 `evict`하고 다음 읽기에서 재적재.

## 코드에 닿는 지점

Spring에서 `@Cacheable`이 만들어 주는 흐름이 정확히 Cache Aside다 → [[Spring Cache 추상화]]

```java
@Cacheable(cacheNames = "bookById")
public Book findBookById(long id) { ... }
```

🟢 [[Spring Cache Redis]]에서는 `RedisTemplate`으로 직접 구현한 버전도 나란히 놓고 비교한다.

## 트레이드오프

| 쓸 때 | 안 쓸 때 |
|---|---|
| 단순한 CRUD, 캐시 정책을 앱에서 직접 제어 | 여러 서비스가 같은 읽기 로직을 반복 → [[Read Through]] |
| 캐시 장애 시에도 동작해야 함 | miss 처리 코드가 서비스마다 흩어지는 게 싫음 |

🔴 **읽기와 쓰기가 교차하면 오래된 값이 뒤늦게 들어간다** → [[캐시 정합성 Race Condition]]. Cache Aside의 고유 약점이다.

🔴 **miss 처리 코드가 서비스마다 복제된다.** 그 반복이 부담되면 Read Through로 올린다.

## 연결

- [[Read Through]] — miss 처리를 캐시 계층으로 올린 것
- [[캐시 쓰기 전략]] — 보통 Write Around과 짝
- [[캐시 정합성 Race Condition]] 🔴 — 이 패턴의 고유 약점
- [[Spring Cache 추상화]] — `@Cacheable`이 만드는 흐름
- 실험: [[캐시 패턴 비교]] · [[Spring Cache Redis]]
