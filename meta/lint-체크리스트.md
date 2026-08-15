---
title: lint-체크리스트
type: moc
tags: [meta]
created: 2026-08-15
updated: 2026-08-15
---

# Lint 체크리스트

"린트 돌려줘"라고 하면 이 순서로 점검한다. 전체 절차는 **`lint` 스킬**에 있다.

> **고치기 전에 발견 목록을 먼저 보고한다.** 무엇을 어떻게 고칠지 합의한 뒤에 손댄다.
> 결과는 [[log]]에 `## [YYYY-MM-DD] lint | 발견 N건`으로 남긴다.

## 기계 / 사람

**먼저 스크립트를 돌린다.** 아래 표의 왼쪽은 기계가 다 보므로 눈으로 다시 훑지 않는다.

```bash
python3 ~/.claude/skills/lint/scripts/lint_tool.py run          # 읽기 전용
python3 ~/.claude/skills/ingest/scripts/moc_sync.py check       # MOC 양방향
python3 ~/.claude/skills/tag/scripts/tag_tool.py audit          # 사전 밖 태그
```

| 기계가 보는 것 (3·5절) | 사람이 봐야 하는 것 (1·2·4·6절) |
|---|---|
| 깨진 링크·유사도 매칭 | 페이지 간 **모순** |
| frontmatter 결손·태그 추론 | 새 소스가 덮은 **낡은 주장** |
| stale 판정 (보고만) | 언급만 되고 페이지가 없는 **빈칸** |
| orphan 탐지 + 연결 후보 | 개념 ↔ 실험 ↔ 실무 **삼각형** |
| MOC 양방향 링크 | 트레이드오프·한계 절 누락 |

🔴 **미작성 링크 200여 개는 정상이다.** 빈 링크는 "써야 할 것" 표시다. 문제로 보고하면 진짜 신호가 묻힌다.

🔴 **어떤 항목에서도 삭제하지 않는다.** stale·orphan·빈 껍데기 전부, 지우는 결정은 사람이 한다.

🔴 **`raw/`는 Lint 대상이 아니다.** 원본 상태는 `tag scan` / `ingest_state status`가 본다.

---

## 1. 모순

- [ ] 같은 사실을 다르게 말하는 페이지 쌍이 있는가
- [ ] `> ⚠️ 충돌` 표시가 붙은 채 해결되지 않고 오래 남은 게 있는가
- [ ] 새로 들어온 소스가 기존 주장을 뒤집었는데 기존 페이지가 그대로인가

발견하면 **양쪽 페이지 모두에** 충돌 블록을 남기고 [[index]]의 `⚠️ 충돌` 절에 올린다.

## 2. 낡음

- [ ] `synthesis` 페이지의 "이 답이 바뀔 조건"이 이미 충족된 게 있는가
- [ ] 라이브러리·프레임워크 버전 메모가 현재 쓰는 버전과 다른가
- [ ] `updated`가 6개월 이상 멈춘 `stable` 페이지 중 다시 봐야 할 게 있는가

## 3. 고아 · 미아

```bash
# 링크된 적 없는 페이지 후보 (대략적)
cd pages && for f in **/*.md; do
  n=$(basename "$f" .md)
  c=$(grep -rl "\[\[$n\]\]" .. --include='*.md' | grep -v "$f" | wc -l)
  [ "$c" -eq 0 ] && echo "orphan: $f"
done
```

```bash
python3 ~/.claude/skills/ingest/scripts/moc_sync.py check    # 양방향 링크 점검
```

- [ ] 들어오는 링크가 0개인 페이지
- [ ] frontmatter `moc:`가 비어 있는 개념·엔티티·실험·종합 페이지 → **자동 수정 불가, 판단 필요**
- [ ] 한쪽만 걸린 링크 → `--fix`
- [ ] `## 최근 추가 (분류 대기)` 절에 쌓인 링크 → 알맞은 주제 절로 옮기고 한 줄 설명 붙이기
- [ ] 30줄 넘는 MOC → 하위 MOC로 쪼갤 때
- [ ] [[index]]에 등재되지 않은 페이지

## 4. 빈칸

- [ ] 여러 페이지에서 언급되는데 **자기 페이지가 없는** 개념
- [ ] MOC의 빈 링크(`[[아직 없는 것]]`) 중 3회 이상 참조된 것 → 우선 작성 대상
- [ ] 웹 검색이나 새 소스로 메울 수 있는 지식 공백

### raw/ 처리 상태

```bash
python3 ~/.claude/skills/tag/scripts/tag_tool.py scan       # 미태깅 / 태깅됨·미ingest
python3 ~/.claude/skills/ingest/scripts/ingest_state.py status
python3 ~/.claude/skills/tag/scripts/tag_tool.py audit      # 사전 밖 태그
```

- [ ] `ingested: false`인 채 오래 방치된 원본 → Ingest 우선순위 제안
- [ ] `tags`가 없는 원본 → `/tag` 대상
- [ ] `tags: [미분류]`인 원본 → 다시 판단하거나 버릴 것
- [ ] `ingested: true`인데 `pages/sources/`에 대응 페이지가 없음 → 체크박스가 잘못 켜졌다
- [ ] `pages_touched: 1`인 원본 → Ingest가 부실했다. 재처리 후보
- [ ] 사전에 없는 태그가 붙은 원본 → 사전 등재 또는 기존 태그로 교체

```bash
# 빈 링크 빈도 상위
grep -rho "\[\[[^]]*\]\]" pages MOC index.md | sort | uniq -c | sort -rn | head -30
```

## 5. 형식

```bash
# 빈 껍데기 페이지 — Obsidian에서 미작성 링크를 클릭하면 생긴다
find . -name '*.md' -not -path './.git/*' -size -1c
find . -maxdepth 1 -name '*.md' ! -name 'index.md' ! -name 'log.md' ! -name 'README.md' ! -name 'CLAUDE.md'
```

- [ ] **0바이트 또는 frontmatter 없는 페이지** → 채우거나 지운다. 미작성 링크를 클릭해서 생긴 껍데기다
- [ ] **볼트 루트에 생긴 페이지** → 루트에는 `index` `log` `README` `CLAUDE`만 있어야 한다
- [ ] frontmatter 필수 필드 누락 (`type` `tags` `created` `updated`, 그리고 `sources` `moc`)
- [ ] [[태그-사전]]에 없는 태그
- [ ] 개념 페이지에 **트레이드오프** 절이 없음 → 미완성
- [ ] 실험 페이지에 **한계** 절이 없거나 숫자가 없음 → 미완성
- [ ] 형광펜 밀도 초과 (한 페이지에 색당 3개 넘음) → 쪼갤 신호
- [ ] "그리고"로 이어붙인 제목 → 원자성 위반

```bash
grep -rL "^tags:" pages --include='*.md'        # tags 없는 페이지
grep -rL "## 트레이드오프" pages/concepts        # 미완성 개념
grep -rL "## 한계" pages/labs                    # 미완성 실험
```

## 6. 삼각형

각 개념이 **개념 ↔ 실험 ↔ 실무** 중 둘 이상에 닿는지.

- [ ] 실험도 실무도 안 걸린 개념 목록 → 실험 후보 / 다음 학습 주제
- [ ] 실험은 있는데 개념 페이지가 없는 것 → 개념 추출 필요

## 7. 프라이버시 🔒

**푸시 전에는 반드시 이것만이라도 돌린다.**

```bash
git status --short
git ls-files | grep -iE "이력|경력기술|자소서|연봉|resume|private"     # 비어야 정상
grep -rinE "ghp_|sk-[A-Za-z0-9]{20}|BEGIN [A-Z ]*PRIVATE KEY" . --include='*.md'
```

- [ ] `raw/` 아래 파일이 스테이징에 올라온 게 없는가
- [ ] `pages/private/` 파일이 올라온 게 없는가
- [ ] 공개 페이지에 사내 시스템명·고객사명·내부 URL·동료 실명이 없는가
- [ ] 토큰·키 패턴이 없는가

## 8. 제안

린트 끝에 항상 붙인다.

- 다음에 파고들면 좋을 **질문** 3개
- 넣으면 좋을 **소스** 3개
- 지금 쓰면 가장 값어치 있을 **페이지** 3개
