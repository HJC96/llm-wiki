---
title: Slice와 Layer
type: concept
status: growing
tags: [architecture, ddd, code-quality]
sources: ["[[클린스프링 전체 문답 118]]"]
moc: ["[[MOC-설계]]"]
created: 2026-09-11
updated: 2026-09-11
---

## 한 줄 정의

**Layer는 기술적 역할로 가르는 수평 분리**, **Slice는 같은 Layer 안에서 업무 책임으로 가르는 세로 분리**. 둘은 직교한다.

## 왜 필요한가

Layer만으로는 "회원 코드가 강사 코드를 마음대로 부르는 것"을 막을 수 없다. 같은 `application` 층 안이면 규칙상 문제가 없기 때문이다.

```text
Layer (수평)     web  /  application  /  domain  /  adapter
Slice (수직)     member │ instructor │ course │ curriculum │ shared
```

🟡 **헥사고날은 Layer 쪽 이야기다.** 업무 코어와 외부 기술의 경계를 정할 뿐, 코어 **내부**를 어떻게 나눌지는 말하지 않는다. 그 안을 업무 단위로 가르는 게 Slice다.

🔴 **그래서 헥사곤 안에 작은 헥사곤을 만들지 않는다.** 내부는 업무 컴포넌트(Slice)로 나누고, 웹·DB 어댑터는 코어 **밖**에 둔다. 각각을 독립적으로 설계할 정도라면 그건 중첩이 아니라 **서로 연결된 여러 헥사곤**이다 → [[헥사고날 아키텍처]]

## 어떻게 동작하는가

🟢 **팀 개발가이드에 정의가 문장으로 있다.**

> `domain` 패키지 아래 첫 번째 패키지는 각각 하나의 애그리거트이다. 위에서 구분한 패키지를 **슬라이스(slice)** 라고 부른다. 하나의 도메인과 애플리케이션 서비스 슬라이스를 묶어 **애플리케이션 컴포넌트** 라고 한다.

즉 Slice는 패키지 규칙이고, **애플리케이션 컴포넌트**는 도메인 슬라이스 + 애플리케이션 서비스 슬라이스의 짝이다 → [[개발 가이드 문서]]

이 도메인에서는 `domain` 바로 아래 패키지 하나가 Slice다.

```text
domain.member       Slice
domain.instructor   Slice
domain.course       Slice
domain.shared       Slice
```

🟡 **`shared`는 Aggregate가 아닌데도 Slice로 취급한다.** 의존성 관점에서 독립 단위이기 때문이다. 규칙은 하나다 — **다른 Slice가 shared를 의존하고, shared는 아무도 의존하지 않는다.**

### 순환은 기계가 잡는다

```java
SlicesRuleDefinition.slices()
    .matching("..domain.(*)..")
    .should().beFreeOfCycles();
```

🔴 **한 방향 의존은 위반이 아니다.** `Instructor → Member`는 허용된다. 반대까지 생겨 `Instructor ↔ Member`가 되어야 순환이다. 이걸 혼동하면 멀쩡한 의존을 없애려고 헛수고한다 → [[모듈 간 순환 의존]]

### 조회는 되고 변경은 안 된다

다른 Aggregate를 직접 참조하는 것 자체는 금지되지 않는다. 갈리는 건 **무엇을 호출하느냐**다.

| | 허용 |
|---|---|
| getter · `isXXX` · record accessor | ✅ 상태 조회 |
| 상태 변경 메서드 | 🔴 금지 — 담당 컴포넌트의 제공 인터페이스로 요청한다 |

이유는 **변경 책임이 흩어지면 Aggregate 경계가 무의미해지기** 때문이다 → [[애그리거트 간 참조]]

ArchUnit에 이런 규칙은 기본 제공되지 않는다. `ArchCondition`을 직접 만든다. 각 클래스의 호출 대상을 훑어 **같은 Slice면 통과, 다른 Slice일 때만 메서드 종류를 검사**한다.

## 코드에 닿는 지점

🟢 **테스트가 통과하는 것만 보면 부족하다.** 의도적으로 규칙을 어기는 의존을 하나 넣어 **실제로 실패하는지** 확인해야 그 테스트를 믿을 수 있다. 규칙이 아무것도 안 잡고 있는데 초록불만 켜져 있는 경우가 실제로 생긴다.

## 트레이드오프

- 🔴 **Slice 경계는 패키지 구조에 묶인다.** 패키지를 옮기면 규칙이 조용히 안 맞게 된다. 매칭 패턴을 리팩터링과 함께 봐야 한다
- **커스텀 `ArchCondition`은 유지보수 대상이다.** getter만 허용하는 규칙은 record accessor·Lombok 생성 메서드·`toString` 같은 예외를 계속 만난다
- 🔴 **기계가 잡을 수 있는 건 일부다.** "이 Slice가 저 Slice를 알아야 하는가"는 여전히 사람 판단이다. 문서에 원칙을 남기고, 판별 가능한 것만 테스트로 내린다
- Slice를 잘게 쪼갤수록 순환이 잡히기 쉬워지지만 인터페이스 개수도 함께 는다

## 연결

- [[모듈 간 순환 의존]] — Slice 간 순환을 DIP로 끊는 방법
- [[애그리거트 간 참조]] — 조회는 되고 변경은 안 되는 이유
- [[ArchUnit으로 아키텍처 강제하기]] — 규칙을 테스트로 내리는 도구
- [[헥사고날 아키텍처]] — Layer 쪽 경계. 이 페이지는 그 안쪽
- [[계층형 아키텍처]] — Layer 개념의 원형
