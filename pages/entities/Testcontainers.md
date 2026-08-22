---
title: Testcontainers
type: entity
kind: library
status: growing
tags: [testcontainers, test, docker]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-설계]]", "[[MOC-데이터베이스]]", "[[MOC-인프라]]"]
created: 2026-08-16
updated: 2026-08-16
---

## 한 줄

테스트가 시작될 때 **실제 이미지를 도커로 띄우고** 끝나면 내리는 라이브러리. 인메모리 대체재가 주는 "가짜 안정감"을 없앤다.

## 어디에 쓰나

- `deep-dive`의 거의 모든 모듈 — [[선착순 쿠폰 발급 동시성]](MySQL 8.0.36 + Redis 7.2.5), [[2PC 실험]](MySQL 8 두 개), [[Spring Cache Redis]]
- 실무에서 통합 테스트를 운영 DB와 같은 엔진으로 돌리는 데 씀

🟢 [[2PC 실험]]은 **Testcontainers가 아니면 아예 성립하지 않는다.** `XA PREPARE`로 멈춘 트랜잭션이 커넥션 종료 후에도 살아 있고 `XA RECOVER`로 찾을 수 있어야 하는데 H2는 그걸 지원하지 않는다.

## 핵심 동작

컨테이너를 띄우면 **포트가 랜덤으로 잡힌다.** 그래서 접속 정보를 정적 설정 파일에 쓸 수 없고, 실행 시점에 Spring `Environment`로 밀어넣어야 한다.

```java
@Container
static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.0.36");

@DynamicPropertySource
static void props(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", mysql::getJdbcUrl);   // supplier
}
```

`@Container`는 시작·종료를 JUnit 생명주기에 맡긴다. 🔴 **수동으로 하면 선언·시작·종료·프로퍼티 등록 네 책임이 각각 다른 위치로 흩어진다.**

## 대안과 비교

| | H2 (인메모리) | Testcontainers |
|---|---|---|
| 속도 | 빠름 | **컨테이너 기동 시간** |
| 방언 | 운영과 다름 🔴 | **운영과 동일** |
| XA·전문 검색 등 | 미지원 | 지원 |
| 도커 필요 | ✗ | **✓** |

🟡 **H2는 테스트를 통과시키고 운영에서 터지게 만든다.** SQL 방언 차이로 "통과하는데 틀린" 상태가 되는 것이 가장 나쁘다 → [[H2와 실제 DB의 방언 차이]]

## 알아둘 함정

🔴 **기동 시간이 실질적 비용이다.** 테스트마다 새로 띄우면 스위트가 느려진다. 싱글톤 컨테이너 패턴이나 `reuse` 옵션을 쓴다.

🔴 **CI에 도커가 있어야 한다.** 도커 없는 실행 환경에서는 통째로 실패한다.

🔴 이미지 태그를 `latest`로 두면 어느 날 조용히 버전이 바뀐다. **운영과 같은 태그로 고정한다.**

## 버전 메모

`@DynamicPropertySource`는 Spring Framework 5.2.5+. 최근 Spring Boot는 `@ServiceConnection`으로 일부 컨테이너의 프로퍼티 주입을 자동화한다 — 이 실험 모듈은 명시적 방식을 쓴다.

## 연결

- [[H2와 실제 DB의 방언 차이]] 🔴 — 이걸 쓰는 이유
- [[단위 테스트와 통합 테스트의 경계]]
- [[테스트 가능한 설계란]]
- 실험: [[Testcontainers 테스트 인프라]] · [[2PC 실험]] · [[Spring Cache Redis]]
