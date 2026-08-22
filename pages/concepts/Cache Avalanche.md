---
title: Cache Avalanche
type: concept
status: growing
tags: [cache, redis, performance]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-Spring]]"]
created: 2026-08-16
updated: 2026-08-16
---

## 한 줄 정의

🟡 **많은 키가 같은 시각에 만료되면** 저장소로 요청이 폭주한다. [[Cache Stampede]]가 키 하나의 문제라면 이건 **키 전체**의 문제다.

## 왜 필요한가

캐시를 배치로 채우면 TTL도 같이 시작한다. 애플리케이션 기동 시 워밍업, 배치 갱신, 대량 무효화 후 재적재 — 전부 **같은 시각에 만료되는 키 무리**를 만든다.

🔴 캐시 서버가 통째로 죽는 경우도 같은 결과를 낳는다. TTL 분산은 그건 못 막는다.

## 어떻게 동작하는가

**TTL Jitter** — 만료 시점을 흩는다.

```java
cacheBooksWithJitter(books, 60초, 10초);
// 키마다: key hash로 jitter 계산 → SET book:id JSON EX 60~70초
```

🟢 [[Spring Cache Redis]]에서 같은 배치로 넣은 키들의 TTL을 조회하면 **서로 다른 값**이 나온다.

🟢 **jitter를 key hash로 계산한 게 중요하다.** 난수로 하면 같은 키를 다시 캐싱할 때마다 만료 시점이 달라져, 그 키의 갱신 주기를 예측할 수 없다.

## 코드에 닿는 지점

Spring Cache 추상화는 캐시 이름 단위로 TTL을 정한다 — **키마다 다른 TTL을 줄 수 없다.** `RedisTemplate`으로 직접 `SET ... EX`를 호출한다. → [[Spring Cache 추상화]]

## 트레이드오프

🔴 **jitter 폭이 좁으면 효과가 없고, 넓으면 캐시 수명이 들쭉날쭉해진다.** 기준 TTL의 10~20% 안팎이 흔한 출발점이지만, 폭은 저장소가 감당 가능한 초당 재적재량에서 역산하는 게 맞다.

🔴 **TTL 분산은 만료만 흩는다.** 캐시 서버 장애로 전부 사라지는 경우는 못 막는다. 그건 서킷 브레이커나 저장소 쪽 스로틀로 대응한다.

🔴 만료 시점이 달라지면 **같은 배치로 넣은 데이터 사이에 세대 차이**가 생긴다. 함께 갱신돼야 하는 데이터라면 문제가 된다.

## 연결

- [[Cache Stampede]] — 키 하나가 만료될 때
- [[Cache Penetration]] — 없는 키가 관통할 때
- [[Spring Cache 추상화]] 🔴 — 키별 TTL을 못 준다
- 실험: [[Spring Cache Redis]] — TTL 60~70초 분산 확인
