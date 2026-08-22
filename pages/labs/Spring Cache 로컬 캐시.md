---
title: Spring Cache 로컬 캐시
type: lab
status: growing
tags: [cache, spring, jpa]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-실험]]", "[[MOC-Spring]]"]
repo: deep-dive/labs/spring-cache-local
created: 2026-08-16
updated: 2026-08-16
---

## 확인하려던 것

`@Cacheable` 한 줄 뒤에서 **실제로 무엇이 키가 되는지**, 그리고 로컬 캐시가 **여러 WAS 환경에서 어디까지 버티는지.**

## 실험 설계

- Spring Cache 추상화 + JVM 메모리 캐시 (외부 캐시 없음)
- `@Cacheable` · `@CachePut` · `@CacheEvict` 각각의 호출 흐름 관찰
- `books` 테이블 + `idx_books_updated_at` 인덱스

## 결과

### 기본 키는 파라미터 개수로 갈린다

`SimpleKeyGenerator`가 만드는 키:

| 파라미터 | 키 |
|---|---|
| 없음 | `SimpleKey.EMPTY` |
| **하나** | **그 파라미터 자체** (`SimpleKey(1L)`이 아니라 `1L`) |
| 여러 개 | `SimpleKey [1L, "ko"]` |

🔴 **키를 명시하면 함정이 생긴다.**

```java
@Cacheable(cacheNames = "bookSummary", key = "#id")
public String findBookSummary(long id, String language)
```

```text
findBookSummary(1L, "ko") → key = 1L
findBookSummary(1L, "en") → key = 1L   ← 같은 캐시 값을 공유
```

🟢 **의도한 최적화일 수도, 버그일 수도 있다.** 언어별 결과가 달라야 한다면 후자다. 이 모듈은 이 상황을 *일부러* 만들어 보여준다.

### DTO를 키로 쓰면 `equals`/`hashCode`가 전부다

| 클래스 | 결과 |
|---|---|
| `BookSearchCondition` (record) | 같은 값 → **같은 키** (hit) |
| `BookSearchConditionWithoutEquals` | 같은 값이어도 **다른 키** (매번 miss) |

💬 `record`가 아닌 DTO를 캐시 키로 쓰면서 `equals`를 안 만들면, 캐시가 있는데도 hit이 0인 상태가 된다. 로그에는 아무 이상이 없어서 발견이 늦다. → [[equals와 hashCode]]

### 여러 WAS의 정합성 — 테이블 버전 키

🔴 한 서버에서 `@CacheEvict`를 실행해도 **다른 서버의 로컬 캐시는 그대로다.**

Redis를 바로 도입할 수 없을 때의 우회로:

```java
// {max(updatedAt), id} 를 키로 사용
findBookNameByIdWithTableVersion(long id)
```

공통 테이블의 `max(updatedAt)`을 **테이블 버전처럼 키에 포함**한다. 어떤 row가 바뀌든 새 버전 키가 되므로 **기존 캐시를 지우지 않고도 캐시 세대 전체가 넘어간다.**

🟢 실무 조건이 붙는다 — `max(updated_at)` 조회가 가벼워야 하므로 `updated_at` 인덱스가 필요하다. 공통코드 그룹처럼 구분 컬럼이 있으면 `(group_key, updated_at)` 복합 인덱스를 고려한다.

## 해석

🟡 **`@Cacheable`은 캐싱을 해 주지만 캐시 키를 정해 주지는 않는다.** 이 모듈이 보여주는 함정 두 가지(`key = "#id"`로 파라미터를 흘리는 것, `equals` 없는 DTO)가 전부 키에서 나온다.

🟡 **테이블 버전 키는 "지우기"를 "새 키로 옮기기"로 바꾼 것이다.** 무효화 전파가 안 되는 환경에서 무효화 없이 정합성을 얻는다. 대신 옛 세대 캐시가 메모리에 남으므로 TTL·최대 크기가 함께 있어야 한다.

## 한계

🔴 **여러 WAS를 실제로 띄우지 않았다.** 정합성 문제는 서술이고, 테이블 버전 키만 단일 프로세스에서 동작 확인했다.

🔴 **캐시 축출(eviction) 정책을 다루지 않았다.** 메모리 상한, LRU, 옛 세대 키가 쌓이는 문제는 범위 밖이다.

🔴 시간을 재지 않았다. 캐시가 얼마나 빠른지가 아니라 **키가 어떻게 만들어지는지**를 본 실험이다.

🔴 프록시 함정(자기호출)은 이 모듈에서 재현하지 않았다 → [[프록시 자기호출 문제]]

## 연결

- 개념: [[Spring Cache 추상화]] · [[캐시 키 설계]] · [[로컬 캐시와 인스턴스 정합성]]
- 개념: [[equals와 hashCode]] — DTO 키가 이것에 전적으로 의존
- 실험: [[Spring Cache Redis]] — 같은 추상화를 공용 캐시로
- 실험: [[캐시 패턴 비교]] — 패턴 자체의 분류
- 코드: `~/Desktop/git/deep-dive/labs/spring-cache-local/`
- 원본: `raw/code/spring-cache-local.md`
