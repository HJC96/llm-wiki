---
name: llm-wiki-lint
description: LLM Wiki의 링크, frontmatter, 오래된 페이지, 고아 페이지를 점검하고 요청된 수정을 리포트에 기록한다. 위키 린트·건강검진에 사용하며 일반 코드 린터 요청에는 사용하지 않는다.
---

# LLM Wiki Lint

## 공통 준비

이 스킬은 LLM Wiki 저장소 전용이다. 작업 디렉터리에서 위로 올라가 `CLAUDE.md`, `index.md`, `pages/`가 함께 있는 볼트 루트를 확인한다. `AGENTS.md`의 Codex 대응 규칙과 `CLAUDE.md`를 읽고 해당 작업에 필요한 템플릿·태그 사전을 사용한다. 명령은 볼트 루트에서 실행한다. 다른 볼트라면 `--vault <볼트>`를 하위 명령 앞에 둔다.

일반 ChatGPT에서 이 문서를 참고하는 경우 `LLM-WIKI-GUIDE.md`의 업로드 모드 지침을 함께 따른다. 실제 파일·실행 도구가 없으면 명령을 실행했다고 보고하지 않는다.

## 모드와 범위

- `$llm-wiki-lint` 또는 `/lint`: 검진·리포트와 수정 후보를 제시한다.
- `점검`: 페이지와 MOC 수정 없이 검사한다. 리포트는 파일로 남는다.
- `수정` 또는 명시적인 자동 수정 요청: 점검 후 허용된 범위의 HIGH 링크·누락 필드를 수정한다. 같은 승인을 다시 묻지 않는다.
- `링크`, `태그`, `stale`, `orphan`: 각각 `--only links`, `frontmatter`, `stale`, `orphan`. '태그'는 frontmatter 검사의 일부이며 raw 태깅은 하지 않는다.

`raw/`, `pages/private/`, `meta/프로필.md`는 읽지 않는다. 이 작업에서는 공통 준비의 개인 프로필 로딩도 생략한다. 삭제 기능은 없다.

## 수행

1. 아래 `run`으로 점검하고 생성된 리포트를 읽는다. 같은 날 재실행한 리포트는 시각 접미사로 보존된다.
2. 미작성 링크를 오류와 구분한다. 정규화 일치·유사도 0.90 이상은 HIGH 자동 수정 후보, 0.72~0.90은 MEDIUM 검토 후보, 후보 없는 링크는 정상 TODO로 볼 수 있다. 개념과 실험처럼 비슷한 제목이어도 다른 페이지인지 실제 내용을 확인한다.
3. frontmatter는 누락 필드만 보완한다. `type`은 폴더, 제목은 파일명, 날짜는 파일시각, 태그는 사전과 본문·이웃 태그로 추론한다. `sources`와 `moc`는 빈 필드만 만들고 출처·소속 값을 만들어내지 않는다.
4. 오래된 seed(60일), stable(180일), 그 외 장기 미갱신(360일)은 재검토 목록으로 보고한다. 고아는 연결 후보를 제안한다. 둘 다 지우지 않는다.
5. `meta/lint-체크리스트.md`로 모순·새 소스로 낡아진 주장·트레이드오프 없는 개념·수치나 한계 없는 실험·개념↔실험↔실무 연결도 살핀다.
6. 수정 요청이 있으면 `--fix`를 사용한다. 항목을 한정한 요청에는 동일한 `--only`를 유지한다. MEDIUM은 의미가 확인된 대상만 직접 수정한다. 모든 수정 근거를 리포트의 '수정됨'에 남긴다.
7. MOC `check`를 함께 실행한다. 점검 모드에서는 `--fix`를 붙이지 않는다. 수정 모드에서도 전체 MOC 수정이 허용된 범위인지 확인한다. 자동 추가된 '최근 추가 (분류 대기)'는 적절한 절에 배치하고 실제 diff를 확인한다.
8. `log.md` 끝에 `## [YYYY-MM-DD] lint | 발견 N건`과 리포트 경로·수정·남은 항목을 추가한다. 결과가 있는 만큼 다음 질문·자료·작성할 페이지를 제안한다.

```bash
python3 scripts/llm_wiki/lint_tool.py --vault . run
python3 scripts/llm_wiki/lint_tool.py --vault . run --only links,orphan
python3 scripts/llm_wiki/lint_tool.py --vault . run --fix --only frontmatter
python3 scripts/llm_wiki/moc_sync.py --vault . check
```

기계 점검 결과만으로 모든 주장과 출처가 정확하다고 단정하지 않는다. 실제 현재 리포트의 숫자를 쓰며 과거에 미작성 링크가 약 200개였다는 값을 재사용하지 않는다.
