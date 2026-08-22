---
title: ArchUnit으로 아키텍처 강제하기
type: concept
status: growing
tags: [architecture, test, code-quality]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-설계]]"]
created: 2026-08-16
updated: 2026-08-16
---

## 한 줄 정의

🟡 **패키지 의존 방향과 코딩 컨벤션을 테스트로 고정한다.** 코드리뷰로 지키던 합의를 CI가 지키게 만든다.

## 왜 필요한가

"Repository를 Controller에서 직접 부르지 말자"는 팀 합의는 **시간이 지나면 반드시 샌다.** 급한 수정, 새로 온 사람, 리뷰어의 피로 — 어느 하나로도 뚫린다. 그리고 한 번 뚫린 뒤에는 "이미 이렇게 돼 있으니까"가 근거가 된다.

🟡 규칙을 테스트로 만들면 **어긋나는 순간 빌드가 깨진다.** 사람의 기억이 아니라 파이프라인이 지킨다.

## 어떻게 동작하는가

**`.class` 파일**을 읽는다 — 소스가 아니라 컴파일 결과라서 리플렉션·애너테이션까지 본다.

| 항목 | 내용 |
|---|---|
| 대상 | `.class` 파일 |
| 임포트 | `ClassFileImporter` |
| 규칙 | `ArchRule` (직접 정의 또는 `GeneralCodingRules`) |
| 검증 | `rule.check(classes)` |
| 위반 시 | `check()` 시점에 `AssertionError` |

## 코드에 닿는 지점

```java
ArchRule rule = layeredArchitecture()
        .consideringAllDependencies()
        .layer("Controller").definedBy(BASE + ".controller..")
        .layer("Service").definedBy(BASE + ".service..")
        .layer("Repository").definedBy(BASE + ".repository..")
        // 각 계층에 누가 접근할 수 있는지 선언
```

사전 정의 규칙도 있다 — 필드 주입 금지, `java.util.logging` 사용 금지, `System.out` 금지 등이 `GeneralCodingRules`에.

## 트레이드오프

🔴 **규칙이 현실과 어긋나면 테스트가 만성적으로 깨진다.** 그러면 팀은 규칙을 고치는 대신 테스트를 `@Disabled`한다. 도입 시점에 **지금 코드가 통과하는 규칙**부터 시작해야 한다.

🔴 **레거시에 한꺼번에 적용할 수 없다.** 기존 위반이 수백 건이면 프리징(현재 위반을 기준선으로 저장) 없이는 못 켠다.

🔴 **패키지 구조에 의존한다.** 리팩터링으로 패키지를 옮기면 규칙 문자열도 같이 고쳐야 한다.

🔴 `.class` 기준이라 **컴파일이 먼저** 필요하다. 빌드 파이프라인 위치를 정해야 한다.

💬 [[테스트 가능한 설계란]]과 같은 계열의 도구다. 테스트가 설계 압력을 만드는 것처럼, ArchUnit은 **구조 압력**을 만든다.

## 연결

- [[레이어 의존 방향]] · [[3-Tier와 헥사고날]] — 고정하려는 대상
- [[테스트 가능한 설계란]] — 같은 계열의 압력
- [[CI-CD 품질 게이트]] — 여기 붙어야 실효가 생긴다
- [[의존성 역전과 어댑터]]
- 실험: [[Testcontainers 테스트 인프라]] — 계층 규칙·필드 주입 금지 검증
