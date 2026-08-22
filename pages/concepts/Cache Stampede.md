---
title: Cache Stampede
type: concept
status: growing
tags: [cache, concurrency, redis]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-Spring]]", "[[MOC-동시성]]"]
created: 2026-08-16
updated: 2026-08-16
---

## 한 줄 정의

🟡 **인기 키 하나가 만료되는 순간 그 키를 기다리던 요청 전부가 동시에 저장소로 내려간다.** 캐시가 있어서 버티던 부하가 한 점에 몰린다.

## 왜 필요한가

캐시 히트율이 높을수록 위험하다. 평소 저장소가 초당 1건만 받다가, TTL이 끝나는 그 1초에 수백 건을 받는다. **캐시가 잘 동작할수록 만료 순간의 낙차가 크다.**

## 어떻게 동작하는가

```
t=0    키 만료
t=0.01 요청 A miss → 저장소 조회 시작 (200ms 걸림)
t=0.02 요청 B miss → 저장소 조회 시작   ← A가 아직 안 끝남
t=0.03 요청 C miss → 저장소 조회 시작
...    같은 쿼리 수백 건
t=0.20 A가 캐시에 put. 나머지도 곧이어 같은 값을 put
```

문제는 **miss 확인과 캐시 채우기 사이의 시간**이다. 그 구간에 들어온 요청은 전부 통과한다.

## 코드에 닿는 지점

**① Single Flight** — 같은 키의 동시 로드를 1회로 합친다.

```java
// 같은 key 로 들어온 두 번째 이후 요청은 첫 로드의 결과를 기다린다
cache.computeIfAbsent(key, k -> loader.load(k));
```

**② 분산 락 + Double-Checked Locking** — 인스턴스가 여러 대면 Single Flight로 부족하다.

```java
if (lock.tryLock(key)) {
    try {
        Book cached = cache.get(key);      // ← 락 얻은 뒤 한 번 더 확인
        if (cached != null) return cached; //    대기 중에 앞 요청이 채웠을 수 있다
        return loadAndCache(key);
    } finally { lock.unlock(); }
}
```

🟢 [[Spring Cache Redis]]의 `RedisHotKeyLockTest`가 락 없는 경우와 있는 경우를 비교한다.

**③ Refresh Ahead** — 만료 전에 미리 갱신한다. 만료 순간 자체를 없앤다.

## 트레이드오프

🔴 **DCL은 저장소 호출을 줄이는 대신 대기를 만든다.** 락을 못 얻은 요청은 기다린다. 저장소 조회가 느리면 그 지연이 그대로 전파된다.

🔴 **락 자체가 비용이다.** [[Redis 분산락]]은 요청마다 왕복을 낸다 — [[선착순 쿠폰 발급 동시성]]에서 1312ms로 측정됐다. 모든 키에 거는 게 아니라 **핫 키에만** 건다.

🔴 Refresh Ahead는 **읽히지 않을 데이터도 계속 갱신**한다. 인기 키가 식으면 낭비가 된다.

| 방어 | 언제 |
|---|---|
| Single Flight | 단일 인스턴스, 또는 인스턴스별 부하만 줄이면 될 때 |
| 분산 락 + DCL | 여러 인스턴스가 같은 저장소를 볼 때 |
| Refresh Ahead | 키가 소수이고 항상 뜨거울 때 |

## 연결

- [[Cache Penetration]] · [[Cache Avalanche]] — 캐시가 무너지는 다른 두 방식
- [[Redis 분산락]] — DCL 방어에 쓰이는 것
- [[Cache Aside]] — miss 구간이 생기는 구조
- 실험: [[Spring Cache Redis]] · [[캐시 패턴 비교]]
