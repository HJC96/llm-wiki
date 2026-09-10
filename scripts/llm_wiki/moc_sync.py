#!/usr/bin/env python3
"""페이지 ↔ MOC 양방향 링크를 점검하고 맞춘다.

규칙: 모든 페이지는 최소 하나의 MOC에 속하며, 연결은 양쪽에 걸린다.
  · 페이지 frontmatter의  moc: ["[[MOC-동시성]]"]
  · MOC 파일 본문의       [[페이지명]]
한쪽만 있으면 그래프가 끊긴다. 이 스크립트가 그걸 잡는다.

pages/private/ 는 제외한다 — MOC 파일은 커밋되므로 비공개 페이지명이 새면 안 된다.

사용:
  moc_sync.py check [--vault PATH] [--fix]
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

DEFAULT_VAULT = Path(__file__).resolve().parents[2]
FM_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)
LINK_RE = re.compile(r"\[\[([^\]|#]+)")
SECTION = "## 최근 추가 (분류 대기)"
SECTION_NOTE = "> 아직 주제 절에 배치되지 않은 페이지. 알맞은 절로 옮기고 여기서 지운다."

# 허브 MOC는 다른 MOC로 가는 입구일 뿐이라 페이지가 소속을 선언하지 않는다.
# 여기서 페이지를 언급해도 양방향 대상이 아니다.
HUBS = {"MOC-홈"}


from metadata import split_fm, render_fm, write_metadata, require_source


def links_in(s: str) -> list[str]:
    return [t.strip() for t in LINK_RE.findall(s or "")]


# ── 수집 ──────────────────────────────────────────────────────────────


def collect(vault: Path):
    pages, mocs = {}, {}

    for p in sorted((vault / "pages").rglob("*.md")):
        if "private" in p.relative_to(vault).parts or p.name == "README.md" or p.resolve() != p.absolute():
            continue
        fm, _ = split_fm(p.read_text(encoding="utf-8", errors="replace"))
        pages[p.stem] = {
            "path": p,
            "type": fm.get("type", "").strip("\"'"),
            "declared": links_in(fm.get("moc", "")),
            "fm": fm,
        }

    for p in sorted((vault / "MOC").glob("*.md")):
        if p.resolve() != p.absolute():
            continue
        mocs[p.stem] = {"path": p, "links": set(links_in(p.read_text(encoding="utf-8")))}

    return pages, mocs


# ── 수정 ──────────────────────────────────────────────────────────────


def add_link_to_moc(moc: dict, page_name: str) -> bool:
    path: Path = moc["path"]
    text = path.read_text(encoding="utf-8")
    if f"[[{page_name}]]" in text:
        return False
    line = f"- [[{page_name}]]"

    if SECTION in text:
        start = text.index(SECTION)
        nxt = text.find("\n## ", start + len(SECTION))
        end = len(text) if nxt == -1 else nxt
        block = text[start:end].rstrip("\n")
        text = text[:start] + block + "\n" + line + "\n" + text[end:]
    else:
        text = (
            text.rstrip("\n")
            + f"\n\n---\n\n{SECTION}\n\n{SECTION_NOTE}\n\n{line}\n"
        )

    path.write_text(text, encoding="utf-8")
    moc["links"].add(page_name)
    return True


def add_moc_to_page(page: dict, moc_name: str) -> bool:
    path: Path = page["path"]
    original = path.read_text(encoding="utf-8")
    fm, body = split_fm(original)
    if not fm:
        return False

    cur = links_in(fm.get("moc", ""))
    if moc_name in cur:
        return False
    cur.append(moc_name)
    fm["moc"] = "[" + ", ".join(f'"[[{m}]]"' for m in cur) + "]"

    before = hashlib.sha256(body.encode()).hexdigest()
    new_text = render_fm(fm) + body
    after = hashlib.sha256(split_fm(new_text)[1].encode()).hexdigest()
    if before != after:
        sys.exit(f"중단: 본문이 바뀔 뻔했다 — {path}")

    path.write_text(new_text, encoding="utf-8")
    page["declared"] = cur
    return True


# ── 점검 ──────────────────────────────────────────────────────────────


def cmd_check(args) -> int:
    vault = Path(args.vault).expanduser().resolve()
    pages, mocs = collect(vault)

    no_moc, one_way_page, one_way_moc, dangling = [], [], [], []

    for name, pg in pages.items():
        if pg["type"] == "moc":
            continue
        if not pg["declared"]:
            no_moc.append(name)
        for m in pg["declared"]:
            if m not in mocs:
                dangling.append((name, m))
            elif name not in mocs[m]["links"]:
                one_way_page.append((name, m))

    for mname, mc in mocs.items():
        if mname in HUBS:
            continue
        for link in mc["links"]:
            if link in pages and mname not in pages[link]["declared"]:
                if pages[link]["type"] != "moc":
                    one_way_moc.append((link, mname))

    empty = sum(1 for mc in mocs.values() for l in mc["links"]
                if l not in pages and l not in mocs)

    print(f"페이지 {len(pages)}개 · MOC {len(mocs)}개 · 미작성 링크 {empty}개\n")

    fixed = 0
    if no_moc:
        print("■ MOC 미선언 (고아 위험) — moc: 필드를 채워야 한다. 자동 수정 불가")
        for n in no_moc:
            print(f"  · {n}")
        print()
    if dangling:
        print("■ 없는 MOC를 가리킴")
        for n, m in dangling:
            print(f"  · {n}  →  [[{m}]] 없음")
        print()
    if one_way_page:
        print("■ 페이지는 선언했는데 MOC에 링크 없음")
        for n, m in one_way_page:
            print(f"  · {n}  →  {m}")
            if args.fix and add_link_to_moc(mocs[m], n):
                fixed += 1
        print()
    if one_way_moc:
        print("■ MOC에는 있는데 페이지가 선언 안 함")
        for n, m in one_way_moc:
            print(f"  · {m}  →  {n}")
            if args.fix and add_moc_to_page(pages[n], m):
                fixed += 1
        print()

    problems = len(no_moc) + len(dangling) + len(one_way_page) + len(one_way_moc)
    if not problems:
        print("양방향 링크 이상 없음")
    elif args.fix:
        print(f"{fixed}건 수정. `{SECTION}` 절에 들어간 링크는 알맞은 주제 절로 옮길 것")
    else:
        print(f"{problems}건 발견. --fix 로 자동 수정 (moc: 미선언은 수동)")
    return 1 if problems else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="페이지 ↔ MOC 양방향 링크 동기화")
    ap.add_argument("--vault", default=str(DEFAULT_VAULT))
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("check")
    s.add_argument("--fix", action="store_true")
    s.set_defaults(func=cmd_check)
    args = ap.parse_args()
    if not getattr(args, "func", None):
        ap.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
