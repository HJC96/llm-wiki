# wiki

**LLM Wiki** 방식으로 운영하는 개인 기술 위키 (Obsidian Vault).

질문할 때마다 원본을 다시 훑는 RAG가 아니라, **LLM이 위키를 점진적으로 짓고 계속 최신으로 유지하는** 방식. 지식은 한 번 컴파일되고 그 뒤로는 갱신된다.

Obsidian이 IDE, LLM이 프로그래머, 위키가 코드베이스.

## 열기

Obsidian → `Open folder as vault` → 이 폴더 선택.
사람의 입구는 [`MOC/MOC-홈.md`](MOC/MOC-홈.md), LLM의 입구는 [`index.md`](index.md).

Codex와 일반 ChatGPT에서도 사용할 수 있다. 설치 구조, 명령 예시, ChatGPT 업로드 묶음과 결과 반영 방법은 [사용 안내](meta/ChatGPT-Codex-사용법.md)를 참고한다. Codex는 [`AGENTS.md`](AGENTS.md)와 `.agents/skills/`를 읽고, 기존 Claude 설정과 스키마를 공유한다.

## 3레이어

| 레이어 | 위치 | 누가 쓰나 |
|---|---|---|
| 원본 | `raw/` | 사람이 넣는다. **불변** |
| 위키 | `pages/` | **LLM이 전적으로 쓴다** |
| 스키마 | [`CLAUDE.md`](CLAUDE.md) | 둘이 함께 진화시킨다 |

여기에 내비게이션 레이어 `MOC/`가 얹힌다.

## 특수 파일

| 파일 | 성격 |
|---|---|
| [`index.md`](index.md) | 콘텐츠 카탈로그 — 위키에 **뭐가** 있는지 |
| [`log.md`](log.md) | 시간순 append-only — **언제** 뭘 했는지 |
| [`CLAUDE.md`](CLAUDE.md) | 규칙 전부 |

## 세 가지 작업

| 작업 | 어떻게 |
|---|---|
| **Ingest** | `raw/inbox/`에 파일을 넣고 "이거 ingest 해줘" |
| **Query** | 그냥 물어본다. 답이 좋으면 `pages/syntheses/`로 파일링 요청 |
| **Lint** | "린트 돌려줘" → [`meta/lint-체크리스트.md`](meta/lint-체크리스트.md) |

## 구조

```
raw/      Layer 1 — 원본. 불변. 전체 gitignore
pages/    Layer 2 — LLM이 쓰는 위키
MOC/      내비게이션 — 주제별 입구
meta/     템플릿 · 태그 사전 · 린트 체크리스트
```

## 권장 플러그인

- **Dataview** — frontmatter 쿼리
- **Obsidian Web Clipper** (브라우저 확장) — 웹 기사를 마크다운으로
- **Marp** — 위키 내용으로 슬라이드 생성
- 그래프 뷰 — 허브와 고아를 눈으로 확인하는 가장 좋은 방법
