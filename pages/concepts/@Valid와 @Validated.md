---
title: "@Valid와 @Validated"
type: concept
status: growing
tags: [spring, architecture]
sources: ["[[클린스프링 검증·엔티티 상태·테스트 픽스처]]"]
moc: ["[[MOC-Spring]]"]
created: 2026-09-11
updated: 2026-09-11
---

## 한 줄 정의

`@Valid`는 **"이 객체 안으로 들어가서 검사해라"**, `@Validated`는 **"이 Spring Bean의 메서드 검증을 켜라"**. 하나는 범위 지정이고 하나는 스위치다.

## 왜 필요한가

🔴 **제약을 선언하는 것과 검증이 실행되는 것은 다른 일이다.**

```java
public record Request(@NotNull Long id) {}
```

`@NotNull`은 규칙을 적어 둔 것일 뿐이다. 이것만으로 어디서든 자동으로 검사되지 않는다. 누군가 **실행시켜야** 한다. 이 구분을 놓치면 "제약을 붙였는데 왜 안 걸리지"가 된다.

## 어떻게 동작하는가

세 층이 각자 다른 일을 한다.

```text
@NotNull · @Size        규칙을 선언한다
    ↓
@Valid                  이 파라미터 객체 내부까지 들어가 검사한다 (cascade)
    ↓
@Validated              이 Bean의 메서드 검증 자체를 활성화한다
```

### Controller — `@Valid`만으로 된다

```java
@PostMapping
void create(@Valid @RequestBody Request request) { }
```

🟡 **여기는 AOP가 아니라 아규먼트 리졸버가 직접 검증한다.** 그래서 `@Validated`가 필요 없다. 컨트롤러에서 `@Validated`를 쓰는 건 **그룹 지정이 필요할 때뿐**이다.

참고로 `@Validated`를 파라미터에 붙이면 `@Valid` 역할 + 그룹 지정을 겸한다. 클래스에 붙일 때(AOP 스위치)와 자리에 따라 의미가 다르다.

### 일반 Spring Bean — `@Validated`가 있어야 한다

Application Service는 MVC가 대신 검증해 주는 영역이 아니다. **Method Validation**을 켜야 한다.

```java
@Validated
@Service
class InstructorApplicationService {
    public void apply(@Valid InstructorApplyRequest request) { }
}
```

`@Validated`를 빼면 `@Valid`도 `@NotNull`도 조용히 무시된다.

### 인터페이스에 선언하고 구현체에서 켜는 구성

입력 포트가 계약을 들고, 구현체가 스위치를 든다.

```java
public interface InstructorApplication {
    Instructor apply(@Valid InstructorApplyRequest request);
}
```

```java
@ValidatedApplicationService
class InstructorApplicationService implements InstructorApplication { }
```

`@ValidatedApplicationService`는 프로젝트에서 만든 합성 애노테이션이고, 그 안에 `@Validated` 역할이 포함돼 있다.

🟡 **제약이 인터페이스에 있으면 그게 곧 포트의 계약이다.** [[포트와 어댑터]]에서 포트가 "이런 입력만 받는다"를 스스로 선언하는 셈이다.

## 코드에 닿는 지점

**`@Valid`가 필요 없는 경우** — 파라미터 자체에 제약이 붙으면 들어갈 내부가 없다.

```java
void find(@NotNull Long memberId) { }          // @Valid 불필요
void create(@Valid Request request) { }        // 객체 내부로 cascade해야 하므로 필요
```

## 트레이드오프

- 🔴 **`@Validated`는 프록시로 동작한다.** AOP 기반이므로 같은 빈 안에서 자기 메서드를 부르면 검증이 걸리지 않는다 → [[프록시 자기호출 문제]]와 같은 함정이다
- 🔴 **인터페이스와 구현체 양쪽에 제약을 걸면 터진다.** Bean Validation 스펙상 하위 타입에서 파라미터 제약을 **강화할 수 없고**(사전조건 강화 금지), 양쪽에 걸면 `ConstraintDeclarationException`이 난다. **한쪽에만** 선언한다
- 🔴 **단순 파라미터 검증은 버전에 따라 예외와 상태 코드가 통째로 달라진다.**

  | | Boot 3.2 미만 | Boot 3.2+ (Framework 6.1+) |
  |---|---|---|
  | 동작 방식 | 클래스 `@Validated` + AOP | MVC 내장 메서드 검증 |
  | `@Validated` | 필수 | 없어도 된다 |
  | 예외 | `ConstraintViolationException` | `HandlerMethodValidationException` |
  | 기본 응답 | 🔴 **500** | **400** |

  🔴 **6.1+에서 `@Validated`를 붙이면 AOP가 우선해 예외 타입이 옛날로 되돌아간다.** 내장 검증을 쓰려면 클래스의 `@Validated`를 **제거**해야 한다
- 파라미터에 붙이는 `@Validated`는 **검증 그룹 지정** 용도로도 쓴다
- 🔴 **실패 형태가 계층마다 다르다.** Controller의 `@Valid`는 `MethodArgumentNotValidException`, 클래스 `@Validated` AOP 검증은 `ConstraintViolationException`이고 **기본 응답이 500**이다. `@RestControllerAdvice`에서 따로 잡아 400으로 내려야 한다
- 🔴 **AOP의 한계를 그대로 물려받는다.** self-invocation은 물론 `private`·`final` 메서드에도 검증이 걸리지 않는다 → [[프록시 자기호출 문제]]
- **어디까지 선언할지는 설계 판단이다.** Web과 Application 양쪽에 붙이면 같은 규칙이 두 번 돌 수 있다. 그게 중복인지 계층별 계약인지는 → [[검증 로직은 어디에 두는가]]
- 애노테이션으로 표현되는 건 [[검증 로직은 어디에 두는가]] 표의 **첫 줄(입력 형식)** 뿐이다. 복합 검증은 이 메커니즘으로 풀 수 없다

## 연결

- [[검증 로직은 어디에 두는가]] — 이 메커니즘이 덮는 범위와 덮지 못하는 범위
- [[프록시 자기호출 문제]] — `@Validated`도 같은 AOP 함정을 공유한다
- [[포트와 어댑터]] — 인터페이스에 제약을 다는 것이 포트 계약이 되는 지점
- [[애플리케이션 서비스]] — Method Validation을 켜는 자리
