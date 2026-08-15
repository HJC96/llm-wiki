# raw/ — Layer 1: 원본

**본문은 불변(immutable).** LLM은 본문을 읽기만 하고 절대 수정하지 않는다. 진실의 기준.

원문에 오류가 있어도 여기서 고치지 않는다. 대응하는 `pages/sources/` 페이지에 `> ⚠️ 원문 오류:`로 적는다.

## 유일한 예외 — frontmatter

원본은 **자기가 분류됐는지·처리됐는지를 스스로 들고 있는다.** 별도 대장을 두면 파일과 대장이 어긋나기 때문이다.

```yaml
---
title: Kafka 컨슈머 재시도와 DLQ 설계     # 파일명이 "Pasted 3.md" 여도 여기로 식별
kind: article
tags: [kafka, distributed]               # 2~4개
source_url: https://...
added: 2026-08-15
ingested: false                          # ← 체크박스. Obsidian Properties에 체크박스로 보인다
ingested_at:                             # ingest 완료 시 채워짐
source_page:                             # ingest 완료 시 채워짐
pages_touched:                           # ingest 완료 시 채워짐
---
```

**`ingested`는 Ingest가 완전히 끝난 뒤에만 켠다.** 중간에 켜면 실패한 작업이 완료로 남아 영영 다시 안 보게 된다.
`true`가 되면 **재Ingest 대상에서도, 태깅 대상에서도 제외**된다.

바이너리(`.pdf` `.pptx` 등)는 frontmatter를 넣을 수 없으므로 옆에 사이드카가 생긴다 — `강의자료.pdf` → `강의자료.pdf.meta.md`. 원본 바이트는 그대로다.

frontmatter는 **손으로 편집하지 않는다.** 아래 스크립트만 쓴다. 둘 다 쓰기 전후 본문 해시를 대조하고, 이동·삭제 기능이 없다.

```bash
python3 ~/.claude/skills/tag/scripts/tag_tool.py scan          # 태깅 대상
python3 ~/.claude/skills/ingest/scripts/ingest_state.py status # ingest 대상
```

## 🔒 이 디렉터리는 통째로 gitignore 대상이다

저작권 있는 책·강의 자료, 클리핑한 기사, 개인 기록이 여기 모인다.
저장소는 public remote(`HJC96/wiki`)에 연결돼 있으므로 **구조만 커밋되고 내용은 로컬에만 남는다.**

커밋되는 것은 이 `README.md`와 각 폴더의 `.gitkeep`뿐이다.

## 폴더

| 폴더 | 무엇 |
|---|---|
| `inbox/` | 아직 처리 안 한 소스. **여기 오래 두지 않는다** |
| `articles/` | 웹 클리핑 (Obsidian Web Clipper) |
| `books/` | 책 발췌·사진·PDF |
| `lectures/` | 강의 자료 |
| `papers/` | 논문 |
| `code/` | 실험 결과 덤프, 로그, 벤치마크 원시 출력 |
| `journal/` | 개인 기록 |
| `assets/` | 이미지. Obsidian 첨부 경로를 여기로 설정 |
| `private/` | 이력·경력·면접 관련 원본 |

## 넣는 법

1. 파일을 `inbox/`에 놓는다
2. **"이거 ingest 해줘"** (`/ingest`)
3. LLM이 읽고 → 요점을 확인받고 → 성격에 맞는 폴더로 옮기고 → `pages/`를 갱신하고 → 체크박스를 켠다

클리핑이 수십 개씩 쌓여서 뭐부터 할지 모르겠으면, 먼저 **`/tag`**로 분류만 한다. 태그만 붙고 파일은 제자리에 그대로 있으며 위키에는 아무것도 안 생긴다. 그다음 태그 분포를 보고 Ingest 순서를 정한다.

## Obsidian 설정 권장

- **Settings → Files and links → Attachment folder path**: `raw/assets/`
- **Settings → Hotkeys → "Download attachments for current file"**: 단축키 지정 (예: `Ctrl+Shift+D`)

웹 기사를 클리핑한 뒤 단축키를 누르면 이미지가 로컬로 내려온다. URL이 깨져도 LLM이 이미지를 직접 볼 수 있다.

> LLM은 인라인 이미지가 섞인 마크다운을 한 번에 읽지 못한다. 텍스트를 먼저 읽고, 필요한 이미지를 따로 여는 방식으로 처리한다.
