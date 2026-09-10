#!/usr/bin/env python3
"""Codex PreToolUse guard for direct patches and file-edit calls, not a shell sandbox."""
import json
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]


def blocked_paths(payload, vault=VAULT):
    data = payload.get("tool_input")
    if not isinstance(data, dict):
        raise ValueError("편집 도구의 입력을 해석할 수 없습니다")
    cwd = Path(payload.get("cwd") or vault).expanduser()
    candidates = []
    if payload.get("tool_name") == "apply_patch":
        patch = data.get("command")
        if not isinstance(patch, str):
            raise ValueError("apply_patch의 command 문자열이 없습니다")
        candidates = re.findall(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$", patch, re.M)
        if not candidates:
            raise ValueError("패치에서 대상 경로를 확인할 수 없습니다")
    else:
        candidates = [data[k] for k in ("file_path", "notebook_path") if isinstance(data.get(k), str)]
        if not candidates:
            raise ValueError("편집 대상 경로가 없습니다")
    raw = (vault / "raw").resolve()
    result = []
    for value in candidates:
        given = Path(value).expanduser()
        path = (given if given.is_absolute() else cwd / given).resolve()
        if path == raw or path.is_relative_to(raw):
            result.append(str(path.relative_to(vault.resolve())))
    return result


def main():
    try:
        payload = json.load(sys.stdin)
        paths = blocked_paths(payload)
        reason = ("raw/ 원본 직접 편집 차단: " + ", ".join(paths) +
                  ". 해석은 pages/에 쓰고, 메타데이터는 scripts/llm_wiki/의 "
                  "ingest_state.py 또는 tag_tool.py로 갱신하세요.") if paths else None
    except (ValueError, TypeError, AttributeError, OSError) as exc:
        reason = f"원본 보호 검증 실패: {exc}"
    if reason:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": reason}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
