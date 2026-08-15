#!/usr/bin/env python3
"""raw/ 원본 보호 — PreToolUse 훅.

Edit·Write·NotebookEdit 가 볼트의 raw/ 아래 파일을 건드리면 거부한다.
CLAUDE.md 「레이어 규칙 1」: raw/ 의 본문은 절대 수정하지 않는다.
유일한 예외인 frontmatter 는 ingest_state.py / tag_tool.py 로만 건드린다.
두 스크립트는 Bash 로 돌기 때문에 이 훅에 걸리지 않는다.

빠져나가야 할 때(원본을 진짜로 손봐야 할 때)는 WIKI_ALLOW_RAW_EDIT=1 로 세션을 띄운다.
"""

import json
import os
import sys

# .claude/hooks/protect_raw.py → hooks → .claude → 볼트 루트
VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_ROOT = os.path.realpath(os.path.join(VAULT, "raw"))

REASON = (
    "⛔ raw/ 는 읽기 전용이다 (CLAUDE.md 「레이어 규칙 1」). 원본은 진실의 기준이라 "
    "오타가 있어도 고치지 않는다.\n"
    "차단된 경로: raw/{rel}\n\n"
    "하려던 게 무엇이냐에 따라:\n"
    "- 원문 오류를 남기고 싶다 → pages/sources/ 의 해당 소스 페이지에 "
    "`> ⚠️ 원문 오류:` 로 적는다\n"
    "- frontmatter(ingested·tags·title)를 바꾸고 싶다 → 손으로 고치지 말고 스크립트를 쓴다\n"
    "    python3 ~/.claude/skills/ingest/scripts/ingest_state.py mark <파일> --page \"소스페이지\" --pages N\n"
    "    python3 ~/.claude/skills/tag/scripts/tag_tool.py set <파일> --tags a,b\n"
    "- 내용을 위키로 옮기고 싶다 → Ingest. pages/ 에 쓰고 raw/ 는 그대로 둔다"
)


def deny(rel):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": REASON.format(rel=rel),
                }
            },
            ensure_ascii=False,
        )
    )


def main():
    if os.environ.get("WIKI_ALLOW_RAW_EDIT") == "1":
        return 0

    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # 입력을 못 읽으면 막지 않는다. 훅 오류로 작업을 세우지 않는다

    tool_input = payload.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(target, str) or not target:
        return 0

    cwd = payload.get("cwd") or os.getcwd()
    path = os.path.join(cwd, os.path.expanduser(target))
    try:
        real = os.path.realpath(path)
    except OSError:
        real = os.path.abspath(path)

    if real == RAW_ROOT or real.startswith(RAW_ROOT + os.sep):
        deny(os.path.relpath(real, RAW_ROOT))

    return 0


if __name__ == "__main__":
    sys.exit(main())
