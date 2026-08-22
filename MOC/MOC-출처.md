---
title: MOC-출처
type: moc
tags: [meta]
created: 2026-08-15
updated: 2026-08-22
---

# MOC — 출처

← [[MOC-홈]]

책·강의의 **진입점**. 원문은 `raw/`에 두고(gitignore) 여기서는 "무엇을 뽑아 어디로 보냈나"만 잇는다.
각 소스 페이지는 `pages/sources/`에 있다.

## 책

| 소스 페이지 | 원본 위치 | 진행 |
|---|---|---|
| [[DDIA]] | `~/Documents/DDIA/` → `raw/books/` | 1장, 5장 복제 |
| [[오브젝트]] | `~/Desktop/git/Obejct/` | |
| [[DDD Start 2]] | `~/Desktop/git/ddd-start2/` | |
| **[[Optimistic Offline Lock (PoEAA)]]** ✅ | `raw/articles/` — martinfowler.com 카탈로그 | 16장 중 패턴 2개 |
| **[[Pessimistic Offline Lock (PoEAA)]]** ✅ | `raw/articles/` — martinfowler.com 카탈로그 | Coarse-Grained Lock 미확보 |

## 강의

| 소스 페이지 | 원본 위치 |
|---|---|
| [[시스템 설계 수업]] | `~/Documents/스터디/요즘개발자시스템설계/` |
| **[[분산 트랜잭션 학습노트]]** ✅ | `raw/lectures/분산_학습노트.md` — 개념 10 + 종합 1 + 면접 3 배출 |
| [[분산 트랜잭션 강의]] | `~/Documents/주문시스템으로 알아보는 분산트랜잭션/` |
| [[분산 환경 강의]] | `~/Documents/카카오 면접관이 알려주는 .../` |
| [[CS 면접 Java]] | `~/Documents/채널톡 ... Java 편/` |
| [[CS 면접 DB]] | `~/Documents/채널톡 ... 데이터베이스 편/` |
| [[동시성 강의]] | `~/Documents/동시성강의/` |
| [[Spring Boot DDD 실전]] | `~/Documents/Spring Boot DDD 실전 .../` |

## 이미 정리된 학습 노트

자기 문장으로 정리 완료. **Ingest 1순위 후보** — 여기서 개념 페이지를 뽑아낸다.

- `~/Documents/분산_학습노트.md` (89KB)
- `~/Documents/분산_섹션별_정리.md`
- `~/Desktop/DDIA_1장_학습노트.md`
- `~/Documents/DDIA/DDIA_5장_복제_학습노트.md`

## 실험실

| 소스 페이지 | 원본 위치 |
|---|---|
| **[[deep-dive 실험실]]** ✅ | `raw/code/` — 모듈 14개 중 3개 처리. lab 3 + 개념 2 배출 |

## OSS 기여

| PR | 페이지 |
|---|---|
| Spring Framework #35656 | [[Spring Framework 기여]] |
| Spring Batch #5043 | [[Spring Batch 기여]] |
| MongoDB Java Driver #1827 | [[MongoDB Driver 기여]] |

## 자격증을 커리큘럼으로

시험 범위를 정형화된 학습 로드맵으로 쓰는 방식 → [[자격증을 학습 로드맵으로 쓰기]]

AWS SAA (2026.03) · Confluent Kafka Fundamentals (2026.04) · MongoDB Associate Developer (2025.10)

---

## Ingest 하는 법

1. 원본을 `raw/inbox/`에 넣는다 (웹 기사는 Obsidian Web Clipper, 이미지는 첨부 경로를 `raw/assets/`로)
2. **"이거 ingest 해줘"**
3. LLM이 요점을 먼저 말하면 무엇을 강조할지 알려준다
4. 소스 페이지 + 개념 페이지들 + MOC + [[index]] + [[log]]가 한 번에 갱신된다
