#!/usr/bin/env python3
"""raw/ 원본의 ingest 상태를 읽고 쓴다.

핵심 불변식: **본문은 단 1바이트도 바뀌지 않는다.**
frontmatter 블록만 추가·교체하고, 쓰기 전후로 본문 해시를 대조해 검증한다.

텍스트 원본(.md/.txt)  → 파일 자신의 frontmatter
바이너리 원본(.pdf 등) → 옆에 <파일명>.meta.md 사이드카

사용:
  ingest_state.py status [--vault PATH] [--all]
  ingest_state.py init   <파일...>
  ingest_state.py mark   <파일> --page "페이지명" [--pages N] [--date YYYY-MM-DD]
  ingest_state.py unmark <파일>
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

DEFAULT_VAULT = Path(__file__).resolve().parents[2]
TEXT_EXT = {".md", ".markdown", ".txt", ".text"}
SKIP_NAMES = {"README.md", ".gitkeep", ".DS_Store"}

FM_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)
FIELD_ORDER = ["ingested", "ingested_at", "source_page", "pages_touched", "note"]


# ── frontmatter 입출력 ────────────────────────────────────────────────


from metadata import split_fm, render_fm, write_metadata, require_source


def raw_fm_block(text: str) -> str:
    m = FM_RE.match(text)
    return m.group(0) if m else ""


# ── 상태 파일 위치 ────────────────────────────────────────────────────


def is_text(p: Path) -> bool:
    return p.suffix.lower() in TEXT_EXT


def state_path(p: Path) -> Path:
    """상태를 실제로 기록하는 파일. 바이너리면 사이드카."""
    return p if is_text(p) else p.with_name(p.name + ".meta.md")


def read_state(p: Path) -> dict:
    sp = state_path(p)
    if not sp.exists():
        return {}
    fields, _ = split_fm(sp.read_text(encoding="utf-8"))
    return fields


def write_state(p: Path, fields: dict) -> None:
    write_metadata(state_path(p), fields,
                   f"\n> 바이너리 원본 `{p.name}` 의 ingest 상태 파일.\n")


# ── 스캔 ──────────────────────────────────────────────────────────────


def iter_sources(vault: Path):
    """raw/ 아래 원본 파일. 사이드카·README·gitkeep 은 원본이 아니다."""
    root = vault / "raw"
    if not root.is_dir():
        sys.exit(f"raw/ 가 없다: {root}")
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if p.name in SKIP_NAMES or p.name.startswith("."):
            continue
        if p.name.endswith(".meta.md"):
            continue
        if p.resolve().is_relative_to(root.resolve()):
            yield p


def truthy(v) -> bool:
    return str(v).split(" #", 1)[0].strip().strip("\"'").lower() in {"true", "yes", "y", "1"}


def cmd_status(args) -> int:
    vault = Path(args.vault).expanduser().resolve()
    done, todo = [], []
    for p in iter_sources(vault):
        rel = p.relative_to(vault)
        st = read_state(p)
        (done if truthy(st.get("ingested", "false")) else todo).append((rel, st))

    total = len(done) + len(todo)
    print(f"raw/ 원본 {total}개 — ingest 완료 {len(done)} / 미처리 {len(todo)}\n")

    if todo:
        print("■ 미처리")
        for rel, st in todo:
            mark = " " if st else "?"  # ? = frontmatter 자체가 없음
            print(f"  [{mark}] {rel}")
        print()
    if done and (args.all or not todo):
        print("■ 완료")
        for rel, st in done:
            page = st.get("source_page", "").strip("\"'")
            when = st.get("ingested_at", "")
            print(f"  [x] {rel}  → {page}  ({when})")
        print()
    if not total:
        print("raw/ 가 비어 있다. inbox/ 에 원본을 넣고 시작한다.")
    return 1 if todo else 0


def cmd_init(args) -> int:
    for f in args.files:
        p = require_source(args.vault, f)
        if not p.exists():
            print(f"없음: {p}")
            continue
        st = read_state(p)
        if "ingested" in st:
            print(f"이미 있음: {p.name} (ingested: {st['ingested']})")
            continue
        write_state(p, {"ingested": "false"})
        print(f"초기화: {state_path(p).name}  ingested: false")
    return 0


def cmd_mark(args) -> int:
    p = require_source(args.vault, args.file)
    if not p.exists():
        sys.exit(f"없음: {p}")
    fields = {
        "ingested": "true",
        "ingested_at": args.date or dt.date.today().isoformat(),
    }
    if args.page:
        fields["source_page"] = json.dumps(f"[[{args.page}]]", ensure_ascii=False)
    if args.pages is not None:
        fields["pages_touched"] = str(args.pages)
    write_state(p, fields)
    print(f"체크: {state_path(p).name}  ingested: true  ({fields['ingested_at']})")
    return 0


def cmd_unmark(args) -> int:
    p = require_source(args.vault, args.file)
    if not p.exists():
        sys.exit(f"없음: {p}")
    write_state(p, {"ingested": "false", "ingested_at": "", "source_page": "", "pages_touched": ""})
    print(f"해제: {state_path(p).name}  ingested: false")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="raw/ ingest 상태 관리")
    ap.add_argument("--vault", default=str(DEFAULT_VAULT))
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status", help="미처리/완료 목록")
    s.add_argument("--all", action="store_true", help="완료 목록도 항상 출력")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("init", help="ingested: false 로 초기화")
    s.add_argument("files", nargs="+")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("mark", help="ingest 완료 체크")
    s.add_argument("file")
    s.add_argument("--page", help="만들어진 소스 페이지 이름 ([[ ]] 없이)")
    s.add_argument("--pages", type=int, help="이번에 건드린 페이지 수")
    s.add_argument("--date", help="YYYY-MM-DD (기본: 오늘)")
    s.set_defaults(func=cmd_mark)

    s = sub.add_parser("unmark", help="체크 해제 (재처리용)")
    s.add_argument("file")
    s.set_defaults(func=cmd_unmark)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
