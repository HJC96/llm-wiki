---
title: Testcontainers 테스트 인프라
type: lab
status: growing
tags: [test, testcontainers, architecture]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-실험]]", "[[MOC-설계]]"]
repo: deep-dive/labs/spring-test-infra
created: 2026-08-16
updated: 2026-08-16
---

## 확인하려던 것

**실행 시점에야 정해지는 값**(컨테이너의 랜덤 포트·JDBC URL)을 Spring 테스트 컨텍스트에 어떻게 밀어넣는가. 그리고 아키텍처 규칙을 테스트로 고정할 수 있는가.

## 실험 설계

🟢 **설계가 영리하다 — 정적 설정을 일부러 틀리게 둔다.**

| 항목 | 값 |
|---|---|
| 정적 `spring.datasource.url` | `localhost:1` (**실패해야 하는 값**) |
| 정적 username | `wrong-user` |
| 동적 값 | Testcontainers MySQL이 만든 실제 주소 |

정적 설정이 틀렸는데도 테스트가 통과한다면, 동적 주입이 **실제로 덮어썼다는 증거**가 된다. 통과/실패 자체가 결론이 되게 만든 구성이다.

```
정적 설정(localhost:1) ─┐
                        ├→ @DynamicPropertySource → DataSource 자동설정 → select database()
Testcontainers(random) ─┘
```

## 결과

### ① 동적 주입이 정적 yml을 이긴다

| 확인 포인트 | 결과 |
|---|---|
| `spring.datasource.url` | `localhost:1`이 **아님** |
| username | `wrong-user`가 아니라 `test` |
| `select database()` | `dynamic_property_source` |

🟡 **테스트 동적 값이 정적 yml보다 우선한다.** `@DynamicPropertySource`는 테스트 클래스의 `static` 메서드에서 `DynamicPropertyRegistry`에 `registry.add("이름", supplier)`로 등록한다. supplier라서 **컨텍스트가 만들어지는 시점에 평가**된다 — 컨테이너가 그때 이미 떠 있어야 하는 이유다.

### ② `@Container`가 생명주기를 가져간다

| 테스트 | 확인 |
|---|---|
| `ContainerAnnotationLifecycleTest` | `@Container` 유무에 따른 자동 시작 차이 |
| `ManualContainerLifecycleTest` | `start()`·`stop()` 위치를 테스트 코드가 직접 가짐 |

🔴 **수동 방식에서 "생명주기가 흩어진다"는 건** 컨테이너 선언·시작·종료·Spring 프로퍼티 등록 **네 가지 책임이 각각 다른 위치로 나뉜다**는 뜻이다. 하나만 빠뜨려도 원인 찾기가 어렵다.

### ③ ArchUnit — 아키텍처를 테스트로 고정

`.class` 파일을 `ClassFileImporter`로 읽어 `ArchRule`로 검증하고, 위반 시 `check()` 시점에 `AssertionError`를 던진다.

```java
ArchRule rule = layeredArchitecture()
        .consideringAllDependencies()
        .layer("Controller").definedBy(BASE + ".controller..")
        .layer("Service").definedBy(BASE + ".service..")
        .layer("Repository").definedBy(BASE + ".repository..")
        // ... 접근 방향 규칙
```

필드 주입 금지 같은 컨벤션도 `GeneralCodingRules`로 검증된다.

## 해석

🟡 **`@DynamicPropertySource`는 "테스트 환경이 실행 시점에 정해진다"는 사실을 Spring에 알리는 유일한 공식 통로다.** 이게 없으면 컨테이너 포트를 고정하거나 프로퍼티 파일을 테스트마다 써야 하고, 둘 다 병렬 실행에서 깨진다.

🟡 **ArchUnit은 코드리뷰로 잡던 것을 CI로 옮긴다.** "Repository를 Controller에서 직접 부르지 말자"는 합의는 시간이 지나면 반드시 샌다. 규칙을 테스트로 고정하면 **어긋나는 순간 빌드가 깨진다** — 사람의 기억이 아니라 파이프라인이 지킨다.

💬 [[H2와 실제 DB의 방언 차이]]와 이어지는 지점이다. H2는 빠르지만 운영 MySQL과 방언이 달라 **테스트는 통과하는데 운영에서 터지는 가짜 안정감**을 준다. Testcontainers는 그 대가로 기동 시간을 낸다.

## 한계

🔴 **컨테이너 기동 비용을 재지 않았다.** Testcontainers의 실질적 단점이 테스트 시간인데, H2 대비 얼마나 느린지 수치가 없다. 재사용(`reuse`)이나 싱글톤 컨테이너 패턴도 다루지 않았다.

🔴 **병렬 실행을 확인하지 않았다.** 동적 프로퍼티의 진짜 값어치가 병렬 실행에서 나오는데, 그 시나리오는 없다.

🔴 **ArchUnit 규칙이 예제 패키지(`archunit.example`)에만 걸려 있다.** 실제 프로젝트 구조에 적용했을 때의 위반 처리나 예외 규칙 관리는 범위 밖이다.

🔴 CI 통합이 없다. "빌드가 깨진다"는 서술이고, 파이프라인에서 실제로 게이트가 되는지는 확인하지 않았다.

## 연결

- 개념: [[Testcontainers]] · [[ArchUnit으로 아키텍처 강제하기]]
- 개념: [[H2와 실제 DB의 방언 차이]] 🔴 — Testcontainers를 쓰는 이유
- 개념: [[테스트 가능한 설계란]] · [[단위 테스트와 통합 테스트의 경계]]
- 코드: `~/Desktop/git/deep-dive/labs/spring-test-infra/`
- 원본: `raw/code/spring-test-infra.md`
