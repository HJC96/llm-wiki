---
title: null 안전성 애노테이션
type: concept
status: growing
tags: [java, spring, code-quality]
sources: ["[[클린스프링 전체 문답 118]]"]
moc: ["[[MOC-Java]]"]
created: 2026-09-11
updated: 2026-09-11
---

## 한 줄 정의

이름이 비슷한 애노테이션 두 계열이 **완전히 다른 일**을 한다. 하나는 도구에게 알리는 **계약**이고, 하나는 런타임에 실제로 막는 **검증**이다.

## 왜 필요한가

🔴 **`@Nonnull`을 붙였는데 null이 그대로 통과했다.**

```java
void apply(@Nonnull Long memberId)   // jakarta.annotation.Nonnull
```

Validation 프록시를 지나 서비스와 Repository까지 null이 들어갔다. `@NotNull`로 바꾸자 그제서야 메서드 진입 전에 `ConstraintViolationException`이 났다.

이유는 단순하다. **`@Nonnull`은 Bean Validation constraint가 아니다.**

| | 정체 | 언제 작동 |
|---|---|---|
| `jakarta.annotation.Nonnull` | 코드 계약. IDE·정적 분석용 | 컴파일·분석 시점. 런타임엔 아무 일 없음 |
| `jakarta.validation.constraints.NotNull` | Bean Validation constraint | 런타임에 실제 검사 |

🟡 **이름이 닮았다는 것 말고는 공통점이 없다.** import 문을 봐야 구분된다.

## 어떻게 동작하는가

### 패키지 단위로 기본값을 바꾸는 쪽

메서드마다 `@NonNull`을 붙이는 건 금방 지친다. 그래서 패키지 전체의 기본 정책을 선언한다.

```java
// package-info.java
@NonNullApi
package tobyspring.splearn.application;
```

`@NonNullApi`는 **클래스가 아니라 패키지에 적용**하는 애노테이션이라 `package-info.java`에 쓴다. 그 패키지의 **메서드 파라미터와 반환값**이 기본 Non-Null이 된다.

예외는 그 자리에만 표시한다.

```java
@Nullable Member findByEmail(Email email);
```

🔴 **필드는 대상이 아니다.** `@NonNullApi`는 파라미터와 반환값만 덮는다. 필드는 `@NonNullFields`가 따로 담당한다.

🔴 **이것도 런타임 검사가 아니다.** `Objects.requireNonNull()`을 대신하지 않는다. IDE와 정적 분석 도구에게 "여기 null 들어오면 경고해라"라고 알릴 뿐이다.

### 정리하면 층이 셋이다

```text
@NonNullApi / @Nullable   패키지 기본 계약      도구가 읽는다
@NotNull                  런타임 제약           Bean Validation이 검사한다
@Valid / @Validated       검사를 실행시키는 장치  → [[@Valid와 @Validated]]
```

## 코드에 닿는 지점

🔴 **Spring Framework 7에서 `@NonNullApi`가 deprecated 됐다.** 대신 JSpecify의 `@NullMarked`를 쓰라고 안내한다.

```java
@NullMarked
package tobyspring.splearn.application;
```

> ❓ 확인 필요: 이 프로젝트는 이전 Spring null-safety 방식을 쓰고 있어 `@NonNullApi`가 보인다. 마이그레이션 시점과 호환 범위는 이 소스에 없다.

## 트레이드오프

- 🔴 **계약 애노테이션은 방어가 아니다.** 도구가 경고를 켜 주지 않으면 아무 효과가 없다. "붙였으니 안전하다"가 가장 위험한 오해다
- **런타임 검사로 다 덮으려 하면 비싸다.** 모든 파라미터에 `@NotNull`을 걸면 프록시가 매 호출마다 돈다. 외부에서 들어오는 경계(포트·컨트롤러)에 집중하는 게 맞다
- 🔴 **표준이 흔들리는 영역이다.** `javax` → `jakarta` → Spring 자체 → JSpecify로 계속 옮겨 왔다. 지금 고른 게 몇 년 뒤 deprecated일 수 있다
- 패키지 기본값을 바꾸면 **기존 코드에 경고가 대량으로 뜬다.** 새 패키지부터 적용하는 쪽이 현실적이다

## 연결

- [[@Valid와 @Validated]] — 런타임 검증을 실제로 돌리는 장치
- [[검증 로직은 어디에 두는가]] — 이 애노테이션들이 덮는 건 표의 첫 줄뿐이다
- [[포트와 어댑터]] — 계약을 선언할 자리가 포트인 이유
