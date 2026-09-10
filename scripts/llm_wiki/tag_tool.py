#!/usr/bin/env python3
"""raw/ 원본에 태그 frontmatter를 붙인다.

핵심 불변식:
  1. 본문은 단 1바이트도 바뀌지 않는다 (쓰기 전후 해시 대조)
  2. 파일을 옮기거나 지우지 않는다 (이 스크립트에 이동·삭제 기능이 없다)
  3. ingested: true 인 파일은 태깅 대상에서 제외한다

사용:
  tag_tool.py scan  [--vault PATH] [--all]        태깅 대상 목록
  tag_tool.py vocab [--vault PATH]                사전 태그 + 실제 사용 빈도
  tag_tool.py set   <파일> --tags a,b,c [--title T] [--kind K] [--url U]
  tag_tool.py audit [--vault PATH]                사전에 없는 태그 찾기
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_VAULT = Path(__file__).resolve().parents[2]
TEXT_EXT = {".md", ".markdown", ".txt", ".text"}
SKIP_NAMES = {"README.md", ".gitkeep", ".DS_Store"}

FM_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)
FIELD_ORDER = [
    "title", "kind", "tags", "source_url", "added",
    "ingested", "ingested_at", "source_page", "pages_touched",
]
VOCAB_RE = re.compile(r"`([a-z0-9가-힣][a-z0-9가-힣-]*)`")


# ── frontmatter (ingest 스킬과 같은 규약) ─────────────────────────────


from metadata import split_fm, render_fm, write_metadata, require_source


def is_text(p: Path) -> bool:
    return p.suffix.lower() in TEXT_EXT


def state_path(p: Path) -> Path:
    return p if is_text(p) else p.with_name(p.name + ".meta.md")


def read_fields(p: Path) -> dict:
    sp = state_path(p)
    if not sp.exists():
        return {}
    return split_fm(sp.read_text(encoding="utf-8"))[0]


def write_fields(p: Path, updates: dict) -> Path:
    sp = state_path(p)
    write_metadata(sp, updates, f"\n> 바이너리 원본 `{p.name}` 의 메타 파일.\n")
    return sp


# ── 스캔 ──────────────────────────────────────────────────────────────


def truthy(v) -> bool:
    return str(v).split(" #", 1)[0].strip().strip("\"'").lower() in {"true", "yes", "y", "1"}


def parse_tags(v: str) -> list[str]:
    v = (v or "").strip()
    if not v:
        return []
    v = v.strip("[]")
    return [t.strip().strip("\"'") for t in v.split(",") if t.strip()]


def iter_sources(vault: Path):
    root = vault / "raw"
    if not root.is_dir():
        sys.exit(f"raw/ 가 없다: {root}")
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name in SKIP_NAMES or p.name.startswith("."):
            continue
        if p.name.endswith(".meta.md"):
            continue
        if p.resolve().is_relative_to(root.resolve()):
            yield p


def load_vocab(vault: Path) -> list[str]:
    """meta/태그-사전.md 의 표에서 승인된 태그를 뽑는다."""
    f = vault / "meta" / "태그-사전.md"
    if not f.is_file():
        return []
    seen, out = set(), []
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        for t in VOCAB_RE.findall(line):
            if t not in seen:
                seen.add(t)
                out.append(t)
    return out


def cmd_scan(args) -> int:
    vault = Path(args.vault).expanduser().resolve()
    todo, tagged, done = [], [], []
    for p in iter_sources(vault):
        rel = p.relative_to(vault)
        f = read_fields(p)
        if truthy(f.get("ingested", "false")):
            done.append((rel, parse_tags(f.get("tags", ""))))
        elif parse_tags(f.get("tags", "")):
            tagged.append((rel, parse_tags(f.get("tags", ""))))
        else:
            todo.append(rel)

    print(f"raw/ 원본 {len(todo)+len(tagged)+len(done)}개 — "
          f"미태깅 {len(todo)} / 태깅됨·미ingest {len(tagged)} / ingest 완료 {len(done)}\n")
    if todo:
        print("■ 태깅 대상 (태그 없음, ingest 안 됨)")
        for rel in todo:
            print(f"  · {rel}")
        print()
    if tagged:
        print("■ 태깅됨 — ingest 대기")
        for rel, tg in tagged:
            print(f"  · {rel}  [{', '.join(tg)}]")
        print()
    if done and args.all:
        print("■ ingest 완료 — 태깅 대상 아님")
        for rel, tg in done:
            print(f"  · {rel}  [{', '.join(tg)}]")
        print()
    return 1 if todo else 0


def cmd_vocab(args) -> int:
    vault = Path(args.vault).expanduser().resolve()
    vocab = load_vocab(vault)
    used: Counter[str] = Counter()
    for p in iter_sources(vault):
        used.update(parse_tags(read_fields(p).get("tags", "")))

    print(f"사전 등재 태그 {len(vocab)}개\n")
    for t in vocab:
        n = used.get(t, 0)
        print(f"  {'●' if n else '○'} {t:<26} raw 사용 {n}")
    unknown = [t for t in used if t not in vocab]
    if unknown:
        print("\n■ 사전에 없는 태그 (사전에 추가하거나 기존 태그로 바꿀 것)")
        for t in sorted(unknown, key=lambda x: -used[x]):
            print(f"  ! {t:<26} {used[t]}회")
    return 0


def cmd_set(args) -> int:
    p = require_source(args.vault, args.file)
    if not p.exists():
        sys.exit(f"없음: {p}")

    cur = read_fields(p)
    if truthy(cur.get("ingested", "false")) and not args.force:
        sys.exit(f"거부: 이미 ingest 된 파일이다 — {p.name} (강제하려면 --force)")

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    if not tags:
        sys.exit("태그가 비었다")

    updates = {"tags": json.dumps(tags, ensure_ascii=False)}
    if args.title:
        updates["title"] = json.dumps(args.title, ensure_ascii=False)
    if args.kind:
        updates["kind"] = args.kind
    if args.url:
        updates["source_url"] = json.dumps(args.url, ensure_ascii=False)
    updates.setdefault("added", cur.get("added") or dt.date.today().isoformat())
    updates.setdefault("ingested", cur.get("ingested") or "false")

    sp = write_fields(p, updates)
    vocab = load_vocab(Path(args.vault).expanduser().resolve())
    new = [t for t in tags if t not in vocab]
    print(f"태깅: {sp.name}  [{', '.join(tags)}]")
    if new:
        print(f"  ⚠ 사전에 없는 태그: {', '.join(new)} → meta/태그-사전.md 에 추가할 것")
    return 0


def cmd_audit(args) -> int:
    vault = Path(args.vault).expanduser().resolve()
    vocab = set(load_vocab(vault))
    bad = 0
    for p in iter_sources(vault):
        tags = parse_tags(read_fields(p).get("tags", ""))
        off = [t for t in tags if t not in vocab]
        if off:
            bad += 1
            print(f"  ! {p.relative_to(vault)}  →  {', '.join(off)}")
    print("사전 밖 태그 없음" if not bad else f"\n{bad}개 파일에 사전 밖 태그")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="raw/ 태그 관리")
    ap.add_argument("--vault", default=str(DEFAULT_VAULT))
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan"); s.add_argument("--all", action="store_true"); s.set_defaults(func=cmd_scan)
    s = sub.add_parser("vocab"); s.set_defaults(func=cmd_vocab)
    s = sub.add_parser("audit"); s.set_defaults(func=cmd_audit)

    s = sub.add_parser("set")
    s.add_argument("file")
    s.add_argument("--tags", required=True, help="쉼표 구분")
    s.add_argument("--title")
    s.add_argument("--kind", help="article|book|lecture|paper|code|journal|note")
    s.add_argument("--url")
    s.add_argument("--force", action="store_true", help="ingest 된 파일도 강제 태깅")
    s.set_defaults(func=cmd_set)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
