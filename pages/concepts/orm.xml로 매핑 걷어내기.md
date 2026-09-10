---
title: orm.xml로 매핑 걷어내기
type: concept
status: growing
tags: [jpa, hibernate, ddd, architecture]
sources: ["[[JPA와 도메인 모델 분리 논쟁]]"]
moc: ["[[MOC-Spring]]", "[[MOC-설계]]"]
created: 2026-08-31
updated: 2026-08-31
---

## 한 줄 정의

> 🟡 **JPA는 애노테이션으로 기본 매핑 정보를 만든 뒤 `META-INF/orm.xml`이 있으면 읽어서 없는 정보는 추가하고 있는 정보는 오버라이드한다.** XML이 우위에 있고, 둘은 배타적이지 않다.

## 왜 필요한가

도메인 모델과 JPA 엔티티를 합쳐 쓰기로 하면([[도메인 모델과 JPA 엔티티를 분리해야 하는가]]) 딱 하나 불편함이 남는다 — **도메인 코드에 관심사가 다른 코드가 섞여 보이는 것.** `@Column(length=100, nullable=false)`, `@Enumerated`, `@Embedded`, `uniqueConstraints`… 도메인과 상관없는 정보가 코드 안에 있다는 사실 자체가 거슬린다.

> 🟡 이건 **취향의 문제**다. 기능에 영향을 주지 않는다는 걸 알아도 볼 때마다 불편한 건 사실이다. 그런데 그 취향을 이유로 클래스를 두 벌 만들 필요는 없다. **제거할 수 있기 때문이다.**

## 어떻게 동작하는가

원래 JPA의 모든 설정은 XML로 하게 되어 있었다. Hibernate가 나온 2001년에는 자바에 애노테이션이 아예 없었다. 애노테이션이 도입된 뒤에도 **XML 설정은 여전히 표준으로 지원된다.**

XML의 장점 — 매핑 설계를 로직 코드 작성자와 **독립적으로** 관리할 수 있고, 바꿔도 **재컴파일이 필요 없고**, 스키마가 있어서 문법이 검증되고 IDE 지원이 좋다.

### 무엇을 남기고 무엇을 빼는가

> 🟡 기준은 하나다 — **도메인 관점에서 의미가 있어 "주석"으로서 값어치가 있는 애노테이션만 남긴다.**

| 남긴다 | 이유 |
|---|---|
| `@Entity` | "이건 도메인의 엔티티다"라는 선언 |
| `@NaturalId` | 도메인 입장에서 **비즈니스적으로 의미를 가진 식별자**가 무엇인지 알려 준다 |
| `@OneToOne` `@ManyToOne` 등 관계 | 도메인 모델 관점에서 중요한 정보 |

뺀다 — `@Table` `@Column` `@Embedded` `@Embeddable` `@Enumerated` `length` `nullable` `uniqueConstraints` …

🟢 결과는 **거의 순수한 도메인 정보만 남은 코드**인데 동시에 **완전한 JPA 엔티티**다. 재생성한 스키마는 애노테이션만 썼을 때와 완전히 동일했다.

## 코드에 닿는 지점

```xml
<!-- src/main/resources/META-INF/orm.xml -->
<access>FIELD</access>   <!-- 프로퍼티(getter)가 아니라 필드 방식 -->
<mapped-superclass class="...AbstractEntity"> ... </mapped-superclass>
<entity class="...Member">
  <table name="member">
    <unique-constraint name="uk_member_email_address"> ... </unique-constraint>
  </table>
</entity>
<embeddable class="...Email"> ... </embeddable>
```

🟡 애노테이션과 거의 1:1로 대응된다. 애노테이션의 element가 태그나 태그 사이 텍스트가 될 뿐이다.

> 🟢 **가장 큰 진입 장벽이던 "이걸 다 XML로 써야 한다"가 AI로 사라졌다.** 클래스를 주고 "이 애노테이션으로 `orm.xml`의 entity 부분을 만들어 줘"라고 하면 잘 만들어 준다. 작업 순서는 **새 매핑을 애노테이션으로 먼저 넣어 동작을 검증하고, 검증된 것을 XML로 옮기는 것.**

> 🔴 부작용 — `@Embedded`/`@Embeddable`을 XML로 빼면 IntelliJ나 JPA Buddy가 매핑을 인식하지 못해 경고를 띄운다. 무시 설정하면 된다.

## 트레이드오프

| 쓸 때 | 안 쓸 때 |
|---|---|
| 도메인 코드를 순수하게 유지하고 싶을 때 | 매핑 정보를 코드 옆에서 바로 보고 싶을 때 |
| 매핑을 별도로 관리할 사람·역할이 있을 때 | 🔴 **정보가 두 곳으로 나뉜다.** 클래스만 보고는 컬럼 길이를 알 수 없다 |

## 연결

- [[도메인 모델과 JPA 엔티티를 분리해야 하는가]] — 이 기법이 필요해지는 맥락
- [[도메인 모델 패턴]] — 순수하게 유지하려는 대상
- [[스키마 마이그레이션 도구]] — `ddl-auto` 대신 최종적으로 가야 할 방향
