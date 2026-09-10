# LLM Wiki를 Codex와 ChatGPT에서 사용하기

기존 Claude 스킬의 `ingest`, `tag`, `lint`와 `CLAUDE.md`의 질의 규칙을 옮겼다. 페이지 구조·출처·MOC·태그·처리 상태는 함께 사용한다. Claude의 기존 스킬과 설정은 그대로이며, Codex 도구는 저장소 안의 `scripts/llm_wiki/`를 사용한다.

## Codex에서 시작

이 `llm-wiki` 폴더를 프로젝트로 열고 새 작업에서 다음처럼 요청한다.

```text
$llm-wiki-ingest 상태를 확인해줘
$llm-wiki-tag raw/inbox 폴더를 분류해줘
$llm-wiki-ingest raw/inbox/자료.md를 위키에 반영해줘
$llm-wiki-query 낙관적 락과 비관적 락을 내 위키 근거로 비교해줘
$llm-wiki-lint 점검해줘
```

"위키에 넣어줘", "태그 붙여줘", "위키 근거로 답해줘"도 가능하다. 스킬이 선택기에 보이지 않으면 Codex를 다시 열거나 `.agents/skills/llm-wiki-ingest/SKILL.md` 등 해당 파일을 읽어 실행하라고 요청한다. 프로젝트별 `.agents/skills`에서 로드하므로 다른 저장소의 일반 작업에는 영향을 주지 않는다. [공식 스킬 문서](https://learn.chatgpt.com/docs/build-skills)

`AGENTS.md`가 Codex의 시작 안내이며 `CLAUDE.md`는 공유 스키마다. Claude 전용 스크립트 경로와 도구 이름, 이미 받은 승인을 재확인하는 부분은 `AGENTS.md`의 대응 규칙에 따라 해석한다. [공식 AGENTS.md 문서](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

### 원본 보호 훅

`.codex/hooks.json`에 `PreToolUse` 훅을 등록했다. 직접 파일 편집/`apply_patch`의 추가·수정·삭제·이동 대상이 `raw/`면 차단한다. 상대 경로, `..`, 심볼릭 링크로 연결되는 대상도 검사한다. 본문 변경은 `pages/`에서 하고 원본 메타데이터는 전용 도구로 바꾼다.

프로젝트/훅을 신뢰하는 Codex 확인 화면이 표시되면 등록 내용을 확인해 활성화한다. 파일 설치와 스크립트 테스트를 마쳤지만, 현재 앱에서 훅이 로드되고 신뢰됐는지까지 자동으로 확인한 것은 아니다. 셸·Python·다른 앱까지 막는 OS 파일 권한은 아니며 기존 Claude 훅도 셸 쓰기 전체를 차단하지 않는다. [공식 훅 문서](https://learn.chatgpt.com/docs/hooks)

## 일반 ChatGPT 웹·앱에서 시작

ChatGPT 프로젝트는 업로드한 파일과 프로젝트 지침을 공유할 수 있다. 업로드 방식에서는 컴퓨터의 위키 폴더를 자동으로 읽거나 수정하지 않으므로 내보낸 사본을 사용한다. 로컬 폴더와 도구가 연결된 데스크톱 환경은 실제 접근 가능한 범위를 확인해 사용한다. [공식 프로젝트 문서](https://learn.chatgpt.com/docs/projects)

1. ChatGPT에서 `LLM Wiki` 프로젝트를 만든다.
2. `output/chatgpt/2026-09-10/llm-wiki-chatgpt.zip`을 로컬에서 푼다.
3. `PROJECT-INSTRUCTIONS.txt`의 내용을 프로젝트 지침에 붙여 넣는다.
4. `LLM-WIKI-GUIDE.md`, `WIKI-CONTENT-01.md`(분할본이 있으면 전부), `manifest.json`을 프로젝트 파일로 올린다. ZIP 자체를 읽을 수 없는 환경에서도 이 개별 파일을 쓰면 된다.
5. 해당 프로젝트 안에서 아래 예시처럼 대화한다. 원본을 ingest/tag하려면 해당 원본도 별도로 첨부한다.

```text
위키 근거로 낙관적 락 재시도에서 트랜잭션 경계가 중요한 이유를 설명해줘.

/ingest 첨부한 강의 노트를 반영해줘. 기존 페이지 보강과 MOC 연결까지 해줘.

/tag 첨부한 원본의 태그만 분류해줘. 본문은 보존해줘.

/lint 제공된 위키 사본을 점검해줘. 수정 제안과 미제공 파일을 구분해줘.

이 답을 종합 페이지로 저장할 수 있게 변경 파일과 인덱스·로그 추가분을 만들어줘.
```

이 방식의 `/ingest` 등은 프로젝트 지침에서 해석하는 텍스트 약어다. ChatGPT에 네이티브 스킬이나 플러그인을 설치한 것은 아니다. 스킬 UI 유무와 관계없이 파일·지침으로 같은 작업 절차를 사용할 수 있게 준비한 방식이다.

### 포함된 자료와 갱신

기본 사본에는 공개 `pages/`, `MOC/`, 템플릿, 태그 사전, 린트 체크리스트를 담는다. `.gitignore` 제외 규칙도 적용한다. `raw/`, `pages/private/`, 상세 프로필, 일일 노트, 초안, 원래 `index.md`와 `log.md`는 넣지 않는다. 비공개 페이지명이나 비공개 경로를 참조하는 공개 문서도 제외한다. 새 카탈로그는 포함된 파일만으로 만든다. 이는 모든 본문을 자동 익명화하는 기능은 아니므로 업로드할 내용을 확인한다.

포함된 파일 목록과 생성 시각·각 파일의 SHA-256은 `manifest.json`에 있다. 학습 날짜 질문에 필요한 `log.md`가 없다는 사실을 지침에 명시했다. 필요한 개인 자료는 사용자가 선택해서 추가한다.

위키가 바뀌면 Codex에 "ChatGPT용 위키 묶음을 최신으로 다시 만들어줘"라고 요청하거나 저장소 루트에서 실행한다. 매번 새 출력 폴더를 지정한다.

```bash
python3 scripts/llm_wiki/export_chatgpt.py --output output/chatgpt/새-버전
```

이 명령은 로컬 파일만 생성한다. ChatGPT에 올리는 작업은 별도이며, 프로젝트에서 오래된 `WIKI-CONTENT`와 manifest를 제거하고 최신 묶음으로 교체한다. 출력 폴더는 Git에서 제외된다.

### ChatGPT 결과를 로컬 위키에 반영

ChatGPT는 변경 페이지, MOC 변경, 인덱스 추가 항목, 로그 추가분, 원본 메타데이터 제안을 반환한다. 파일 생성 도구가 없으면 경로별 Markdown으로 반환한다. 사본만 고쳤다면 로컬에 저장됐다고 하지 않고, `ingested` 완료 표시도 로컬 검증 뒤로 남긴다.

다운로드한 결과와 그 작업에 사용한 `manifest.json`을 Codex에 지정한다.

```text
이 ChatGPT 변경 묶음을 llm-wiki에 반영해줘.
함께 준 manifest와 현재 파일의 해시를 비교하고 달라진 파일은 병합해줘.
raw 본문은 보존하고 MOC·index·log를 갱신해줘.
검증을 마친 원본만 ingest 완료로 표시해줘.
```

결과 ZIP을 볼트 위에 통째로 덮어 풀지 않는다. 지침에는 별도 임시 위치에서 경로·변경 범위·기준 해시를 확인하고 병합하도록 정해 두었다.

## 동작 확인

Python 3.10 이상으로 실행하며 런타임용 추가 패키지는 필요 없다.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/llm_wiki/ingest_state.py --vault . status
python3 scripts/llm_wiki/tag_tool.py --vault . scan
python3 scripts/llm_wiki/moc_sync.py --vault . check
```

테스트는 임시 볼트에서 CRLF/BOM 본문·기존 중첩 메타데이터 보존, PDF 사이드카, 처리 상태 변경, 완료 원본 태깅 제외, 경로 범위, 원본 보호 훅, MOC, 린트, 공개 내보내기를 확인한다. `status`의 1은 미처리 원본 존재이며 실행 오류가 아니다.

스킬 문서 형식은 `skill-creator`의 공식 `quick_validate.py`로도 검증했다. 실제 위키에서는 상태 조회·태깅 상태 조회·MOC 점검만 수행했다. 테스트를 위해 실제 원본을 태깅하거나 새로 ingest하지 않았다.

## 강의 자료 반영 범위

첨부한 '지식시스템 설계' PDF 두 개는 SHA-256이 같은 중복 파일이었다. 기존 구현의 ingest/tag/lint와 질의 규칙을 기준으로 변환했으며, 강의의 프롬프트 예시는 현재 작업 지시로 실행하지 않았다. 원본 보호 훅은 Codex 입력 형식에 맞췄다. 기존 설정에 없던 회의록·주간 리뷰·알림·Daily Note 자동화는 추가하지 않았다.

강의 예시의 `ingested: - [x]` 대신 기존 위키에서 쓰는 올바른 YAML boolean `ingested: true/false`를 유지했다. 스크립트는 본문 바이트와 변경하지 않은 메타데이터를 보존하도록 보완했고, 같은 날 재실행한 린트 리포트도 이전 수정 기록이 사라지지 않게 보존한다.
