---
title: Micrometer 계측기 선택
type: concept
status: growing
tags: [observability, spring-boot, performance]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-인프라]]"]
created: 2026-08-16
updated: 2026-08-16
---

## 한 줄 정의

🟡 "무엇을 잴까"보다 **"어떤 계측기로 잴까"**가 실제 난점이다. 축은 셋 — **누적(Counter) · 현재값(Gauge) · 시간(Timer).**

## 왜 필요한가

잘못 고르면 되돌릴 수 없다. 대기 개수를 Counter로 재면 **줄어드는 것을 표현할 수 없고**, 소요 시간을 Gauge로 재면 **분포가 사라진다.** 그리고 메트릭은 과거를 소급 수정할 수 없어서, 고쳐도 이전 시계열과 이어지지 않는다.

## 어떻게 동작하는가

| 상황 | 계측기 |
|---|---|
| 정상/비정상 상태 | Health |
| 현재 배포 버전 | Info |
| 발생 **횟수 누적** | **Counter** |
| **현재 개수** | **Gauge** |
| **소요 시간** | **Timer** |
| 조건별 분리 | Tag |
| 앱·환경·인스턴스 식별 | Common Tags |
| tail latency | Percentile |

🟢 **Gauge는 값을 저장하지 않는다.** 조회 시점에 함수를 호출한다.

```java
Gauge.builder("app.notification.pending.size", pendingNotifications, List::size)
        .register(meterRegistry);
```

그래서 "지금 몇 개인가"에 맞고, 🔴 **순간적으로 튀었다 돌아온 값은 조회 시점에 안 보인다.**

🟢 **Timer는 `COUNT`와 `TOTAL_TIME`·`MAX`를 함께 남긴다.** 시간을 재고 있으면 Counter를 따로 둘 필요가 없다.

## 코드에 닿는 지점

💬 [[실패 사실의 기록]]에서 정한 운영 지표들이 여기서 계측기로 매핑된다.

| 지표 | 계측기 | 왜 |
|---|---|---|
| `PENDING` 주문 수 | **Gauge** | "지금 몇 개 매달려 있나" |
| 오래 `RESERVED`인 예약 수 | **Gauge** | 위와 같음 |
| `ObjectOptimisticLockingFailureException` 발생 | **Counter** | 누적 횟수 |
| 재시도 소진 횟수 | **Counter** | 누적 횟수 |
| 외부 API 응답 시간 | **Timer** + Percentile | 분포가 필요 |

## 트레이드오프

🔴 **Cardinality 폭발.** tag 값 종류가 무한히 늘면 시계열이 조합마다 하나씩 생긴다.

| 좋은 tag | 나쁜 tag |
|---|---|
| `application` `environment` `region` `hostname` | `userId` `email` `requestId` **전체 URL** |

🔴 **Counter는 프로세스 생존 기간 동안 계속 누적된다.** `COUNT`가 기대보다 크면 앱을 의심하기 전에 이전 실행분이 포함됐는지 본다.

🔴 **`MAX`는 롤링 윈도우라 조용히 리셋된다.** 그래프가 갑자기 낮아졌다고 성능이 좋아진 게 아니다.

🔴 **Common Tags는 나중에 붙이면 늦다.** 이전 시계열과 이어지지 않는다. 처음부터 넣는다.

🔴 **Percentile은 부하 아래에서만 의미가 있다.** 호출 몇 번으로는 p99가 분포를 갖지 못한다 → [[k6로 Before After 측정하기]]

## 연결

- [[실패 사실의 기록]] — 여기서 정한 지표가 이 페이지에서 계측기로 확정된다
- [[Actuator 엔드포인트 보안 경계]] 🔴 — 노출 범위는 별개 문제
- [[k6로 Before After 측정하기]] — Percentile이 의미를 갖는 조건
- [[구조화 로깅]] — 로그와 메트릭의 역할 분담
- 실험: [[Actuator 커스텀 헬스 체크]]
