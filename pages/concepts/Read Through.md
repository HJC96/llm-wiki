---
title: Read Through
type: concept
status: growing
tags: [cache]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-Spring]]"]
created: 2026-08-16
updated: 2026-08-16
---

## 한 줄 정의

🟡 **캐시 접근 계층이 miss를 처리한다.** 서비스는 캐시만 부르고 저장소의 존재를 모른다.

## 왜 필요한가

[[Cache Aside]]는 miss 처리 코드가 **서비스마다 복제된다.** 여러 서비스가 같은 읽기 로직을 쓰면 그 반복이 쌓인다. Read Through는 그걸 한 계층으로 올린다.

## 어떻게 동작하는가

```java
// 서비스는 이것만 안다
Product p = readThroughCache.get(id);

// 캐시 계층 안쪽
public Product get(Long id) {
    return cache.computeIfAbsent(id, k -> loader.load(k));   // loader가 저장소를 안다
}
```

🟡 [[Cache Aside]]와의 차이는 **누가 저장소를 호출하느냐** 하나다.

## 코드에 닿는 지점

🔴 **외부 Redis 자체가 DB loader를 아는 구조가 아니다.** 실무에서 Read Through는 두 형태로 나타난다.

- **loading cache** — Caffeine `LoadingCache`, Ehcache `CacheLoader`
- **앱 공통 캐시 래퍼** — Redis 앞에 둔 자체 계층

## 트레이드오프

| 쓸 때 | 안 쓸 때 |
|---|---|
| 여러 서비스가 같은 읽기 로직 재사용 | 캐시 정책을 호출부마다 다르게 하고 싶음 |
| miss 처리 반복을 없애고 싶음 | 캐시 계층이 저장소를 알게 되는 결합이 싫음 |

🔴 **캐시 계층이 저장소를 알게 된다.** 의존 방향이 하나 늘고, 캐시 계층 테스트에 loader 스텁이 필요해진다.

🔴 로컬 loading cache는 인스턴스마다 따로 로드한다 → [[로컬 캐시와 인스턴스 정합성]]

## 연결

- [[Cache Aside]] — miss 처리를 서비스가 하는 쪽
- [[캐시 쓰기 전략]]
- 실험: [[캐시 패턴 비교]]
