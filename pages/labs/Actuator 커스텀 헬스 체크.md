---
title: Actuator 커스텀 헬스 체크
type: lab
status: growing
tags: [observability, spring-boot, performance]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-실험]]", "[[MOC-인프라]]", "[[MOC-Spring]]"]
repo: deep-dive/labs/spring-boot-actuator
created: 2026-08-16
updated: 2026-08-16
---

## 확인하려던 것

Actuator·Micrometer로 **무엇을 어떤 계측기로 재야 하는지**를 12단계로 나눠 직접 호출해 보고 값 변화를 관찰한다. `deep-dive` 모듈 중 문서가 가장 두껍다(49KB).

## 실험 설계

- Spring Boot + Actuator + Micrometer
- **Postman 컬렉션을 위에서 아래로** 실행하며 App API 호출 → `/actuator/metrics/{name}` 값 변화 확인
- 12개 폴더: Basic → Health → Info → Metrics Basic → Counter/Tags → Common Tags → Gauge → Timer.record → Timer.Sample → @Timed → Percentile → HTTP Metrics → Custom Endpoint

> 🔴 이 모듈은 **손으로 호출하고 눈으로 값을 보는** 구성이다. 자동 검증 테스트가 아니라 관찰 실습이다.

## 결과

### 계측기 선택 기준 — 이게 이 모듈의 결론

| 상황 | 선택 |
|---|---|
| 정상/비정상 상태 확인 | **Health** |
| 현재 배포 버전 확인 | **Info** |
| 발생 **횟수 누적** | **Counter** |
| **현재 개수** 관찰 | **Gauge** |
| **소요 시간** 측정 | **Timer** |
| 조건별 분리 | **Tag** |
| 앱/환경/인스턴스 공통 식별 | **Common Tags** |
| tail latency 확인 | **Percentile** |

🟡 축은 하나다 — **누적이냐(Counter), 현재값이냐(Gauge), 시간이냐(Timer).**

### Gauge는 값을 저장하지 않는다

```java
Gauge.builder("app.notification.pending.size", pendingNotifications, List::size)
        .register(meterRegistry);
```

🟢 **`Gauge`는 값을 저장하지 않고 actuator 조회 시점에 `List::size`를 호출한다.** 그래서 "현재 대기 개수"처럼 **지금 물어봐야 의미 있는 값**에 맞는다. 반대로 순간적으로 튀었다 돌아온 값은 조회 시점에 안 보인다.

### Timer는 횟수와 시간을 함께 기록한다

🟢 `Timer`는 `COUNT`(호출 횟수)와 `TOTAL_TIME`·`MAX`를 함께 남긴다. Counter를 따로 둘 필요가 없다는 뜻이기도 하다.

Percentile을 켜면 `p50`/`p95`/`p99`를 `?tag=phi:0.95` 형태로 조회할 수 있다.

| | 뜻 |
|---|---|
| p95 | 95% 요청이 이 시간 이하 |
| p99 | **느린 꼬리 구간** |

### Cardinality — tag의 함정

| 좋은 tag | 나쁜 tag |
|---|---|
| `application` `environment` `region` `hostname` | `userId` `email` `requestId` **전체 URL** |

🔴 **tag 값 종류가 무한히 늘면 cardinality 폭발.** 시계열이 tag 조합마다 하나씩 생기므로, `userId`를 tag로 넣으면 사용자 수만큼 메트릭이 만들어진다.

### 증상별 체크리스트

| 증상 | 먼저 볼 것 |
|---|---|
| actuator endpoint가 목록에 없음 | `management.endpoints.web.exposure.include` |
| `/actuator/info`에 값이 적음 | `management.info.env.enabled`, build/git resource |
| metric 이름이 없음 | 관련 App API를 호출했는지 |
| tag 필터 결과가 이상함 | 필터 없는 metric의 `availableTags` |
| `COUNT`가 기대보다 큼 | **이전 실행에서 누적된 호출** 포함 여부 |
| `MAX`가 갑자기 낮음 | **Micrometer time window 리셋** 가능성 |

🔴 마지막 두 줄이 실무에서 제일 헷갈리는 지점이다. Counter는 **프로세스 생존 기간 동안 계속 누적**되고, `MAX`는 롤링 윈도우라 조용히 리셋된다. 그래프가 이상할 때 앱을 의심하기 전에 이걸 먼저 본다.

## 해석

🟡 **"뭘 재야 하나"보다 "어떤 계측기로 재야 하나"가 실제 난점이다.** 대기 개수를 Counter로 재면 줄어들 때를 표현할 수 없고, 소요 시간을 Gauge로 재면 분포가 사라진다.

💬 [[실패 사실의 기록]]에서 정리한 운영 지표들 — `PENDING` 주문 수, 오래 `RESERVED`인 예약, `CompensationRegistry`의 `PENDING` 행 — 이 전부 **Gauge**로 재야 하는 값이다. "지금 몇 개가 매달려 있나"이지 "지금까지 몇 번 매달렸나"가 아니기 때문. 그 페이지에서 *"0이어야 정상이 아니라 감시되고 있어야 정상"*이라고 쓴 것이 여기서 계측기 선택으로 구체화된다.

🟡 **Common Tags는 나중에 붙이면 늦다.** 여러 인스턴스의 메트릭을 구분하려면 `application`·`environment`·`hostname`이 처음부터 붙어 있어야 하고, 나중에 추가하면 이전 시계열과 이어지지 않는다.

## 한계

🔴 **자동 검증이 없다.** Postman으로 손으로 호출하고 눈으로 값을 확인하는 구성이라, 회귀 테스트로 쓸 수 없다.

🔴 **부하 상황을 재현하지 않았다.** Percentile의 값어치는 부하 아래에서 나오는데, 수동 호출 몇 번으로는 p99가 의미 있는 분포를 갖지 못한다. → [[k6로 Before After 측정하기]]와 붙여야 완성된다.

🔴 **수집·저장 쪽이 없다.** Prometheus scrape, 보존 기간, 대시보드, 알림 룰이 전부 범위 밖이다. **"측정한다"와 "감시한다"는 다르다.**

🔴 **cardinality 폭발을 실제로 일으켜 보지 않았다.** 경고는 서술이고, 어느 규모에서 문제가 되는지 수치가 없다.

🔴 [[Actuator 엔드포인트 보안 경계]]를 다루지 않았다 — endpoint를 노출하는 설정은 나오지만, 외부 노출을 막는 쪽은 없다.

## 연결

- 개념: [[실패 사실의 기록]] — 거기서 정한 운영 지표들이 여기서 계측기로 매핑된다
- 개념: [[Actuator 엔드포인트 보안 경계]] 🔴 — 이 실험이 안 다룬 반대편
- 개념: [[커스텀 헬스 인디케이터]] · [[구조화 로깅]]
- 개념: [[k6로 Before After 측정하기]] — Percentile이 의미를 갖는 조건
- 코드: `~/Desktop/git/deep-dive/labs/spring-boot-actuator/`
- 원본: `raw/code/spring-boot-actuator.md`
