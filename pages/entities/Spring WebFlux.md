---
title: Spring WebFlux
type: entity
kind: framework
status: growing
tags: [reactive, spring, performance]
sources: ["[[Spring WebFlux vs MVC]]"]
moc: ["[[MOC-Spring]]"]
version: Spring Boot 3.2 계열
created: 2026-08-31
updated: 2026-08-31
---

## 한 줄

Servlet API 대신 **Reactive Streams 기반의 논블로킹 웹 스택.** `spring-webflux` 모듈이고, 전통 스택은 `spring-webmvc`다.

## 어디에 쓰나

`deep-dive/labs/payment-system` 하나뿐이다. 강의 원본이 Kotlin + WebFlux + R2DBC라서 그대로 포팅 중이고, **실무에서 쓰고 있지 않다.**

## 핵심 동작

| | Spring MVC | WebFlux |
|---|---|---|
| 요청당 스레드 점유 | 요청이 끝날 때까지 | 조립하는 순간만, 이후 반납 |
| I/O 대기 중 스레드 | 묶여서 대기 | 다른 일 하러 감 |
| 한 요청을 처리하는 스레드 | 하나로 고정 | 구간마다 바뀔 수 있음 |
| 동시 처리 상한 | 스레드 수 | 메모리 허용치 |

> 🟡 **WebFlux도 MVC 패턴을 쓴다.** `@Controller`·`@GetMapping`·뷰 렌더링을 그대로 쓴다. 진짜 대립축은 "MVC 패턴이냐"가 아니라 **"블로킹/서블릿 스택이냐 논블로킹/리액티브 스택이냐"** 다. 스프링이 전통 스택 모듈명을 하필 `webmvc`로 지어서 "MVC = 전통 블로킹 스택"의 대명사가 됐을 뿐이다.

## 대안과 비교

| | WebFlux | MVC + JDBC | MVC + 가상 스레드 |
|---|---|---|---|
| 스레드 고갈 | 안 남 | 스레드 수가 상한 | 대부분 해소 |
| 코드 모양 | 체인 조립 | 순차 | **순차 그대로** |
| 트랜잭션 성숙도 | R2DBC 트랜잭션은 상대적으로 미성숙 | `@Transactional` 검증 완료 | 검증 완료 |
| 디버깅 | 스택트레이스 끊김 | 온전 | 온전 |

> 🟡 **결제 신규 프로젝트라면 여전히 MVC + JPA + (필요시) 가상 스레드가 무난한 기본값이다.** 판단 근거는 [[결제 시스템에 WebFlux를 쓸 것인가]]에 있다.

## 알아둘 함정

> 🔴 **부분 도입은 이점이 없다.** 블로킹 JDBC나 벤더 SDK가 체인에 하나만 껴도 이벤트 루프가 막힌다. DB는 R2DBC, HTTP는 `WebClient`로 전 구간을 맞춰야 한다

> 🔴 **`flatMap`의 기본 concurrency(256)를 그대로 두면** PSP Rate Limit과 커넥션 풀을 그냥 초과한다 → [[Bulkhead]]

> 🔴 **운영 리스크가 곧 비용인 도메인에서는 신중해야 한다.** 결제 장애는 돈이고, 흐름 추적이 어려운 스택은 그 자체가 리스크다

## 버전 메모

Java 21 [[Java 21 가상 스레드]] 이후 "동시성 때문에 WebFlux"라는 논리는 약해졌다. WebFlux가 여전히 값을 하는 자리는 **여러 외부 서비스를 팬아웃 호출해 합치는 게이트웨이/오케스트레이션 계층**이다.

## 연결

- [[Reactor]] — 기반 라이브러리
- 개념: [[이벤트 루프와 스레드 점유]] · [[블로킹과 비동기는 다른 축]]
- [[결제 시스템에 WebFlux를 쓸 것인가]] — 이 스택을 고를지에 대한 답
- [[R2DBC]] — 짝이 되는 DB 접근 기술
