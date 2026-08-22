---
title: Cache Penetration
type: concept
status: growing
tags: [cache, redis]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-Spring]]"]
created: 2026-08-16
updated: 2026-08-16
---

## 한 줄 정의

🟡 **존재하지 않는 키는 캐시에 남지 않으므로 매번 저장소까지 관통한다.** 캐시가 아무것도 막아 주지 못한다.

## 왜 필요한가

[[Cache Aside]]는 "값이 있으면 캐시에 넣는다". 없으면? 넣을 게 없으니 안 넣는다. 그래서 **없는 키를 반복 조회하면 캐시는 100% miss**고 저장소가 전부 받는다.

🔴 이건 오타나 버그로도 생기지만, **공격 표면**이기도 하다. 없는 ID를 무작위로 던지면 캐시를 우회해 저장소를 직접 때릴 수 있다.

## 어떻게 동작하는가

**① Negative Caching** — 없다는 사실도 캐시한다.

```
GET book:999 → miss → MySQL SELECT → 결과 없음
SET book:999 "__NULL__" EX 30        ← 센티널을 저장
```

🟢 [[Spring Cache Redis]]에서 없는 ID를 **20번** 조회했을 때 **MySQL 조회는 처음 한 번뿐**이었다.

**② Bloom Filter** — 확실히 없는 키는 저장소 조회 전에 차단한다.

## 코드에 닿는 지점

Spring Cache 추상화로는 안 된다 — `@Cacheable`은 `null`을 캐시할지 여부만 정할 수 있고 **센티널 값과 별도 TTL을 지정할 수 없다.** `RedisTemplate`을 직접 쓴다. → [[Spring Cache 추상화]]

## 트레이드오프

🔴 **센티널 TTL을 길게 잡으면 안 된다.** 나중에 실제로 생성된 데이터가 그 TTL 동안 계속 "없음"으로 보인다. 30초처럼 짧게 잡거나, 생성 시점에 명시적으로 무효화한다.

🔴 **없는 키가 무한하면 negative caching이 메모리를 먹는다.** 무작위 ID 공격에는 Bloom Filter가 맞다.

🔴 **Bloom Filter는 위양성이 있다.** "있다"는 답은 틀릴 수 있으므로 저장소 조회로 확인해야 한다. "없다"는 답만 확실하다. 그리고 **원소 삭제가 안 된다.**

| 방어 | 언제 |
|---|---|
| Negative Caching | 없는 키의 종류가 제한적 (오타·삭제된 리소스) |
| Bloom Filter | 없는 키가 사실상 무한 (무작위 ID) |

## 연결

- [[Cache Stampede]] · [[Cache Avalanche]] — 캐시가 무너지는 다른 두 방식
- [[Cache Aside]] — 없는 값을 안 넣는 구조가 원인
- [[Spring Cache 추상화]] 🔴 — 추상화로 안 되는 대표 사례
- 실험: [[Spring Cache Redis]] — 20회 조회 중 MySQL 1회
