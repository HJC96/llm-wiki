---
name: llm-wiki-tag
description: LLM Wiki raw 원본에 태그와 제목·종류 frontmatter를 붙인다. raw 태깅, 클리핑 분류, 태그 사전·감사에 사용한다. 위키 페이지 생성이나 파일 이동은 하지 않는다.
---

# LLM Wiki Tag

## 공통 준비

이 스킬은 LLM Wiki 저장소 전용이다. 작업 디렉터리에서 위로 올라가 `CLAUDE.md`, `index.md`, `pages/`가 함께 있는 볼트 루트를 확인한다. `AGENTS.md`의 Codex 대응 규칙과 `CLAUDE.md`를 읽고 해당 작업에 필요한 템플릿·태그 사전을 사용한다. 명령은 볼트 루트에서 실행한다. 다른 볼트라면 `--vault <볼트>`를 하위 명령 앞에 둔다.

일반 ChatGPT에서 이 문서를 참고하는 경우 `LLM-WIKI-GUIDE.md`의 업로드 모드 지침을 함께 따른다. 실제 파일·실행 도구가 없으면 명령을 실행했다고 보고하지 않는다.

## 모드

- `$llm-wiki-tag` 또는 `/tag`: 미태깅 원본 분류.
- `<경로>`: 해당 파일·폴더만 처리. `다시 <경로>`: 미ingest 원본의 태그 재분류.
- `상태`: `scan`. `사전`: `vocab`. `감사`: `audit`. 이 세 모드는 조회만 한다.

## 수행

1. `scan`, `vocab`, `meta/태그-사전.md`로 대상과 어휘 범위를 확인한다. 사용자가 지정한 경로 밖은 태깅하지 않는다.
2. 제목·초반 문단·소제목을 읽고 주제를 판단한다. `ingested: true`는 건너뛴다. `--force`를 일반 태깅이나 `다시`의 기본값으로 사용하지 않는다.
3. 영역 + 구체 주제로 태그 2~4개를 고른다. 곁다리 언급에는 태그를 붙이지 않는다. 판단 불가라면 `미분류`로 남기고 보고한다.
4. 기존 태그를 우선한다. 새 태그는 두 개 이상 파일에서 재사용되고 기존 태그 조합으로 의미가 충분히 표현되지 않을 때 만든다. 새 태그를 허용받은 범위라면 작업 중 사전에 범위 한 줄과 함께 추가하고 이유·대상을 보고한다. 어휘 선택이 모호한 부분만 사용자에게 확인한다.
5. 아래 스크립트로 frontmatter를 갱신한다. 제목·URL에 `:` 같은 문자가 있어도 YAML 문자열로 안전하게 저장된다. 기존 본문 바이트·다른 메타데이터·ingest 상태를 보존한다.
6. `audit`으로 사전 누락을 확인한다. 처리 수·미분류·신규 태그와 ingest 우선순위를 보고한다. 개인 자료는 본문을 요약하지 않고 필요한 파일명과 태그만 보고한다.

```bash
python3 scripts/llm_wiki/tag_tool.py --vault . scan
python3 scripts/llm_wiki/tag_tool.py --vault . vocab
python3 scripts/llm_wiki/tag_tool.py --vault . set raw/inbox/example.md --tags kafka,distributed --title "문서 제목" --kind article
python3 scripts/llm_wiki/tag_tool.py --vault . audit
```

`kind`: `article|book|lecture|paper|code|journal|note`. 웹 원문 URL은 `--url`로 준다. 바이너리는 옆의 `.meta.md`에 기록한다. `scan`의 1은 미태깅 존재, `audit`의 1은 사전 밖 태그 존재다.

원본을 이동·삭제·이름 변경하지 않는다. `pages/`를 만들거나 `ingested`를 켜는 것은 이 작업이 아니다.
