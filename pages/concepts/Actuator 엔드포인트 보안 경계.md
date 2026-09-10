---
title: Actuator 엔드포인트 보안 경계
type: concept
status: growing
tags: [spring-boot, observability, architecture]
sources: ["실무 소재 카탈로그 (raw/private/, 2026-08-31)"]
moc: ["[[MOC-Spring]]", "[[MOC-인프라]]"]
created: 2026-08-31
updated: 2026-08-31
---

## 한 줄 정의

> 🟡 **Actuator는 관측용 조회 엔드포인트만 있는 게 아니라 상태를 바꾸는 엔드포인트를 함께 갖는다.** 그래서 "어디까지 노출할 것인가"가 아니라 **"누가 호출할 수 있는가"** 가 진짜 질문이다.

## 왜 필요한가

`/actuator/caches/{name}`에 `DELETE`를 보내면 캐시가 지워진다. `/actuator/loggers`는 로그 레벨을 바꾸고, `/actuator/shutdown`은 애플리케이션을 내린다. 조회 엔드포인트도 안전하지 않다 — `/actuator/env`와 `/actuator/configprops`는 **설정값(DB URL, 사용자명, 때로는 키)** 을 그대로 보여준다.

> 🔴 운영 도구로 쓰려고 엔드포인트를 열어 두면 **그 순간 외부 누구나 캐시를 날리고 로그 레벨을 바꿀 수 있는 상태**가 된다. "내부에서만 쓸 거니까"는 방어가 아니다.

## 어떻게 동작하는가

방어선은 셋이고, 하나만 쓰면 부족하다.

| 층 | 무엇 | 한계 |
|---|---|---|
| **노출 제어** | `management.endpoints.web.exposure.include`로 필요한 것만 | 노출한 것은 여전히 누구나 부른다 |
| **인증·인가** | Spring Security로 `/actuator/**`에 역할 요구 | 운영 스크립트가 자격증명을 들고 다녀야 한다 |
| **네트워크 경계** | 별도 포트(`management.server.port`)로 분리하거나 **내부 IP에서만** 허용 | IP는 위조 가능. 프록시 뒤에서는 `X-Forwarded-For` 신뢰 문제 |

> 🟢 실무에서 자주 쓰이는 조합은 **"별도 관리 포트 + 내부 IP 제한"** 이다. 관리 포트를 서비스 포트와 나누면 L7/LB가 그 포트를 외부로 라우팅하지 않는 것만으로 1차 방어가 된다.

## 코드에 닿는 지점

```yaml
management:
  server:
    port: 9090                      # 서비스 포트와 분리
  endpoints.web.exposure.include: health,info,metrics,caches
  endpoint.health.show-details: when-authorized
```

```java
// 관리 엔드포인트는 내부 대역에서만
http.authorizeHttpRequests(auth -> auth
    .requestMatchers(EndpointRequest.toAnyEndpoint())
        .access(new WebExpressionAuthorizationManager("hasIpAddress('10.0.0.0/8')")));
```

> 🔴 **L7 로드밸런서를 통해 호출하면 어느 인스턴스가 처리할지 보장되지 않는다.** 인스턴스별 상태를 바꾸는 엔드포인트(캐시 무효화 등)는 각 서버에 접속해 `localhost`로 직접 호출해야 의도한 대상이 바뀐다 → [[로컬 캐시와 인스턴스 정합성]]

## 트레이드오프

| 열 때 | 닫을 때 |
|---|---|
| 운영 중 상태를 바꿀 수단이 필요할 때 (캐시 무효화, 로그 레벨) | 별도 운영 API를 만들 여력이 있을 때 |
| 별도 관리 포트를 둘 수 있을 때 | 포트를 하나만 열 수 있는 환경 |

🔴 대가는 **운영 절차가 사람에게 남는다는 것**이다. "각 서버에 들어가 localhost로 호출한다"는 절차는 문서화되지 않으면 만든 사람만 아는 지식이 된다.

## 연결

- [[로컬 캐시와 인스턴스 정합성]] — 인스턴스별 무효화가 필요해지는 이유
- [[Micrometer 계측기 선택]] · [[실패 사실의 기록]] — 같은 Actuator 위의 관측 축
- [[Spring Cache 추상화]]
- 실험: [[Actuator 커스텀 헬스 체크]]
