---
name: llm-wiki-ingest
description: 원본을 기존 LLM Wiki에 반영한다. 위키에 넣기, inbox 처리, ingest 상태·전체·재처리에 사용한다. 원본 분류만 하는 요청은 tag다.
---

# LLM Wiki Ingest

## 공통 준비

이 스킬은 LLM Wiki 저장소 전용이다. 작업 디렉터리에서 위로 올라가 `CLAUDE.md`, `index.md`, `pages/`가 함께 있는 볼트 루트를 확인한다. `AGENTS.md`의 Codex 대응 규칙과 `CLAUDE.md`를 읽고 해당 작업에 필요한 템플릿·태그 사전을 사용한다. 명령은 볼트 루트에서 실행한다. 다른 볼트라면 `--vault <볼트>`를 하위 명령 앞에 둔다.

일반 ChatGPT에서 이 문서를 참고하는 경우 `LLM-WIKI-GUIDE.md`의 업로드 모드 지침을 함께 따른다. 실제 파일·실행 도구가 없으면 명령을 실행했다고 보고하지 않는다.

## 모드

- `$llm-wiki-ingest <경로>` 또는 `/ingest <경로>`: 지정한 원본 처리.
- 인자가 없으면 `raw/inbox/` 미처리 목록과 처리 순서를 제시한다. `전체`면 미처리 원본을 순서대로 처리한다.
- `상태`: 상태 조회만. `재처리 <경로>`: 해당 원본만 체크 해제 후 다시 처리.
- URL·붙여넣은 글은 원본을 `raw/inbox/`에 신규 보관한 뒤 처리한다. 기존 원본을 덮어쓰지 않는다.

## 수행

1. `ingest_state.py status`로 완료 여부를 확인한다. 필요한 경우 `init`으로 `false`를 추가한다. 이미 처리된 원본은 명시적 재처리 요청이 없으면 건너뛴다.
2. 원본 전체를 읽는다. PDF는 텍스트 추출과 필요한 페이지 렌더링으로 확인한다. 참조된 그림도 살핀다. 내용을 읽지 못한 부분은 표시하고 완료 처리하지 않는다.
3. 핵심 주장 3~5개와 기존 페이지 연결 후보를 먼저 제시한다. 사용자가 이미 대상·목적을 정했으면 진행하고, 남길 내용에 중요한 선택이 필요할 때만 확인한다. 배치는 전체 계획을 한 번에 정한다.
4. `raw/inbox/` 파일은 내용 성격에 맞는 `articles`, `books`, `lectures`, `papers`, `code`, `journal`, `private`로 파일링한다. 원본과 사이드카를 함께 옮기고 바이트를 보존한다. 목적지 충돌 시 덮어쓰지 않는다. 외부 경로의 원본은 복사해서 보관하고 외부 파일은 유지한다.
5. `meta/templates/source.md`로 `pages/sources/`를 쓴다. 핵심 주장과 '여기서 나온 페이지' 표를 채운다. 소스 요약만 만들고 끝내지 않는다.
6. 기존 개념을 먼저 검색해 보강하고 필요한 개념·엔티티·실험 페이지만 만든다. 개념은 트레이드오프, 실험은 측정 조건·수치·한계가 있어야 한다. 근거가 없으면 확인 필요로 표시한다. 10~15개 수정은 기존 작업의 예시이며 할당량이 아니다.
7. 출처를 연결하고 모순은 양쪽 페이지와 `index.md`에 남긴다. 각 공개 페이지의 `moc:`와 MOC 본문을 양방향으로 연결한다. 적절한 주제 절에 링크와 한 줄 설명을 넣는다. 비공개 자료는 공개 MOC에 노출하지 않는다.
8. `index.md`의 페이지 목록·개수·미해결을 갱신하고 `log.md` 끝에 `## [YYYY-MM-DD] ingest | 제목` 항목을 추가한다.
9. MOC를 점검하고 해당 작업의 연결을 바로잡는다. 자동 `--fix`는 전체 볼트의 연결을 바꿀 수 있으므로 범위를 먼저 확인한다. 분류 대기 링크는 주제 절로 배치하고 다시 `check`한다. 검증이 실패하면 완료 체크를 켜지 않고 남은 문제를 보고한다.
10. 위키 반영과 검증을 마친 후에만 `mark`한다. 새 페이지·보강·모순·실험 연결 부족과 다음 자료 후보를 보고한다.

## 명령

```bash
python3 scripts/llm_wiki/ingest_state.py --vault . status
python3 scripts/llm_wiki/ingest_state.py --vault . init raw/inbox/example.md
python3 scripts/llm_wiki/ingest_state.py --vault . unmark raw/articles/example.md
python3 scripts/llm_wiki/moc_sync.py --vault . check
python3 scripts/llm_wiki/ingest_state.py --vault . mark raw/articles/example.md --page "소스 페이지 제목" --pages 5
```

`status`의 종료 코드 1은 미처리 파일 존재를 뜻한다. `mark`는 위키 품질을 스스로 판단하지 않는 상태 도구이므로 앞 단계 검증을 생략할 수 없다. 텍스트 원본은 frontmatter만, 바이너리는 `.meta.md`만 바뀐다. `log.md` 과거 항목, 원본 본문, 무관한 파일은 수정하지 않는다.
