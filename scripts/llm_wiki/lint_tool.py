#!/usr/bin/env python3
"""볼트 건강검진.

절대 원칙
  1. raw/ 는 읽지도 쓰지도 않는다 — 이 스크립트는 pages/ 와 MOC/ 만 연다
  2. 삭제하지 않는다 — 삭제 기능 자체가 없다
  3. 모든 자동 수정은 리포트의 「수정됨」 절에 근거와 함께 남는다

검진 항목
  links       미해결 링크. 확신도로 갈라 HIGH만 자동 재연결
  frontmatter 필수 필드 누락. 폴더·mtime·본문으로 추론해 채움
  stale       오래 안 만진 페이지. 보고만 — 삭제 여부는 사용자가 결정
  orphan      들어오는 링크 0. 연결 후보를 제안만

사용:
  lint_tool.py run [--vault PATH] [--fix] [--stale-days N] [--seed-days N]
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_VAULT = Path(__file__).resolve().parents[2]

FM_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)
LINK_RE = re.compile(r"\[\[([^\]|#]+)")
VOCAB_ROW = re.compile(r"`([a-z0-9가-힣][a-z0-9가-힣-]*)`\s*\|([^|]*)")

FOLDER_TYPE = {
    "concepts": "concept", "entities": "entity", "labs": "lab",
    "syntheses": "synthesis", "questions": "question", "sources": "source",
}
LINK_FIELD_TYPES = {"concept", "entity", "lab", "synthesis"}
HUBS = {"MOC-홈"}

AUTO_LINK_RATIO = 0.90   # 이 위만 자동 재연결
SUGGEST_RATIO = 0.72     # 이 위는 제안


# ── frontmatter ───────────────────────────────────────────────────────

from metadata import split_fm, render_fm, write_metadata, require_source


def links_in(s: str) -> list[str]:
    return [t.strip() for t in LINK_RE.findall(s or "")]


def parse_list(v: str) -> list[str]:
    v = (v or "").strip().strip("[]")
    return [t.strip().strip("\"'") for t in v.split(",") if t.strip()]


def norm(s: str) -> str:
    return re.sub(r"[\s\-_·:()\[\]/]+", "", s).lower()


# ── 수집 ──────────────────────────────────────────────────────────────

class Page:
    __slots__ = ("path", "name", "rel", "fm", "body", "text", "kind")

    def __init__(self, path: Path, vault: Path):
        self.path = path
        self.name = path.stem
        self.rel = str(path.relative_to(vault))
        self.text = path.read_text(encoding="utf-8", errors="replace")
        self.fm, self.body = split_fm(self.text)
        self.kind = "moc" if path.parent.name == "MOC" else "page"

    @property
    def type(self) -> str:
        return self.fm.get("type", "").strip("\"'")

    def save(self, fm: dict) -> None:
        self.path.write_text(render_fm(fm) + self.body, encoding="utf-8")
        self.fm = fm
        self.text = render_fm(fm) + self.body


ROOT_ALLOWED = {"index.md", "log.md", "README.md", "CLAUDE.md", "AGENTS.md"}


def collect(vault: Path) -> dict[str, Page]:
    """pages/ · MOC/ · 루트 미아만 연다. raw/ 는 절대 건드리지 않는다."""
    pages: dict[str, Page] = {}
    for root in (vault / "pages", vault / "MOC"):
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.md")):
            if "private" in p.relative_to(vault).parts or p.name == "README.md" or p.resolve() != p.absolute():
                continue
            pg = Page(p, vault)
            pages[pg.name] = pg
    # 루트에 흘러든 페이지 — Obsidian에서 미작성 링크를 클릭하면 여기 생긴다
    for p in sorted(vault.glob("*.md")):
        if p.name not in ROOT_ALLOWED and p.resolve() == p.absolute():
            pg = Page(p, vault)
            pg.kind = "stray"
            pages[pg.name] = pg

    # 시스템 문서 — 링크 해석에만 쓰고 검진하지 않는다
    for p in list(vault.glob("*.md")) + list((vault / "meta").glob("*.md")):
        if (p.name in ROOT_ALLOWED or p.parent.name == "meta") and p.name != "프로필.md" and p.resolve() == p.absolute():
            pg = Page(p, vault)
            pg.kind = "system"
            pages.setdefault(pg.name, pg)
    return pages


def load_vocab(vault: Path) -> dict[str, str]:
    f = vault / "meta" / "태그-사전.md"
    if not f.is_file():
        return {}
    out: dict[str, str] = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        m = VOCAB_ROW.search(line)
        if m:
            out.setdefault(m.group(1), m.group(2).strip())
    return out


# ── 1. 링크 ───────────────────────────────────────────────────────────

def check_links(pages, fix, rep):
    names = set(pages)
    by_norm = defaultdict(list)
    for n in names:
        by_norm[norm(n)].append(n)

    unresolved = defaultdict(list)   # target -> [page names]
    for pg in pages.values():
        if pg.kind == "system":
            continue
        for t in links_in(pg.text):
            if t not in names:
                unresolved[t].append(pg.name)

    auto, suggest, todo = [], [], []
    for target, srcs in sorted(unresolved.items()):
        cands = by_norm.get(norm(target))
        if cands:
            auto.append((target, cands[0], srcs, "정규화 일치"))
            continue
        close = difflib.get_close_matches(target, names, n=3, cutoff=SUGGEST_RATIO)
        if close:
            ratio = difflib.SequenceMatcher(None, target, close[0]).ratio()
            if ratio >= AUTO_LINK_RATIO:
                auto.append((target, close[0], srcs, f"유사도 {ratio:.2f}"))
            else:
                suggest.append((target, close, srcs, ratio))
        else:
            todo.append((target, srcs))

    if fix:
        for target, new, srcs, why in auto:
            pat = re.compile(r"\[\[" + re.escape(target) + r"(?=[\]|#])")
            for s in srcs:
                pg = pages[s]
                new_text = pat.sub(f"[[{new}", pg.text)
                if new_text != pg.text:
                    pg.path.write_text(new_text, encoding="utf-8")
                    pg.text = new_text
                    pg.fm, pg.body = split_fm(new_text)
            rep["fixed"].append(
                f"**링크 재연결** `[[{target}]]` → `[[{new}]]` "
                f"({why}) — {', '.join(srcs)}")

    rep["links"] = {"auto": auto, "suggest": suggest, "todo": todo}


# ── 2. frontmatter ────────────────────────────────────────────────────

def tag_terms(tag: str, desc: str) -> set[str]:
    terms = {tag, tag.replace("-", " ")}
    for tok in re.split(r"[,·/()\s]+", desc):
        tok = tok.strip(". ")
        if len(tok) >= 2:
            terms.add(tok)
    return terms


def infer_tags(pg: Page, vocab: dict[str, str], pages) -> list[str]:
    text = pg.text.lower()
    scores: Counter[str] = Counter()
    for tag, desc in vocab.items():
        if tag in ("meta", "미분류"):
            continue
        s = 0
        if tag.lower() in text:
            s += 3
        for term in tag_terms(tag, desc):
            if len(term) >= 2 and term.lower() in text:
                s += 1
        if s:
            scores[tag] = s
    # 이웃 투표 — 이 페이지가 가리키는 페이지들의 태그
    for t in links_in(pg.text):
        nb = pages.get(t)
        if nb:
            for tg in parse_list(nb.fm.get("tags", "")):
                if tg in vocab:
                    scores[tg] += 1
    return [t for t, s in scores.most_common(3) if s >= 3]


def check_frontmatter(pages, vocab, fix, rep):
    issues, today = [], dt.date.today().isoformat()

    for pg in sorted(pages.values(), key=lambda p: p.rel):
        if pg.kind == "system":
            continue
        fm = split_fm(pg.text)[0]
        missing, added = [], []

        scratch = not fm
        if scratch:
            missing.append("frontmatter 전체")
            fm["title"] = pg.name
            fm["status"] = "seed"
            added.append(f"title: {pg.name} · status: seed (신규 생성)")
            if pg.kind == "stray":
                issues.append((pg.rel, ["볼트 루트에 있음 — 알맞은 `pages/` 하위로 옮길 것"], []))
            if not pg.body.strip():
                issues.append((pg.rel, ["본문이 빈 껍데기 — 미작성 링크 클릭으로 생긴 것"], []))

        # type — 폴더로 추론
        if not fm.get("type"):
            inferred = "moc" if pg.kind == "moc" else FOLDER_TYPE.get(pg.path.parent.name)
            missing.append("type")
            if inferred:
                fm["type"] = inferred
                added.append(f"type: {inferred} (폴더 추론)")

        ptype = fm.get("type", "").strip("\"'")

        # created / updated — mtime 으로
        for key in ("created", "updated"):
            if not fm.get(key):
                missing.append(key)
                mt = dt.date.fromtimestamp(pg.path.stat().st_mtime).isoformat()
                fm[key] = mt
                added.append(f"{key}: {mt} (파일 시각)")

        # tags — 본문 + 이웃 투표
        if not parse_list(fm.get("tags", "")):
            missing.append("tags")
            guess = infer_tags(pg, vocab, pages)
            if guess:
                fm["tags"] = "[" + ", ".join(guess) + "]"
                added.append(f"tags: [{', '.join(guess)}] (본문·이웃 추론)")
            else:
                fm.setdefault("tags", "[]")

        # sources / moc — 값은 추론하지 않고 빈 필드만 세운다
        if ptype in LINK_FIELD_TYPES:
            for key in ("sources", "moc"):
                if key not in fm:
                    missing.append(key)
                    fm[key] = "[]"
                    added.append(f"{key}: [] (빈 필드 생성)")

        if missing:
            issues.append((pg.rel, missing, added))
            if fix and added:
                pg.save(fm)
                rep["fixed"].append(
                    f"**frontmatter** `{pg.rel}` — " + " · ".join(added))

    rep["frontmatter"] = issues


# ── 3. stale ──────────────────────────────────────────────────────────

def check_stale(pages, stale_days, seed_days, rep):
    today, out = dt.date.today(), []
    for pg in sorted(pages.values(), key=lambda p: p.rel):
        if pg.kind in ("moc", "system"):
            continue
        raw = pg.fm.get("updated", "").strip("\"'")
        try:
            upd = dt.date.fromisoformat(raw)
        except ValueError:
            continue
        age = (today - upd).days
        status = pg.fm.get("status", "").strip("\"'")
        reason = None
        if status == "seed" and age >= seed_days:
            reason = f"seed 로 {age}일 방치"
        elif status == "stable" and age >= stale_days:
            reason = f"stable 인데 {age}일째 미갱신 — 재검토"
        elif age >= stale_days * 2:
            reason = f"{age}일째 미갱신"
        if reason:
            out.append((pg.rel, reason, len(pg.body.strip())))
    rep["stale"] = out


# ── 4. orphan ─────────────────────────────────────────────────────────

def check_orphan(pages, rep):
    inbound: Counter[str] = Counter()
    for pg in pages.values():
        for t in set(links_in(pg.text)):
            if t != pg.name:
                inbound[t] += 1

    out = []
    for pg in sorted(pages.values(), key=lambda p: p.rel):
        if pg.kind in ("moc", "system") or pg.name in HUBS:
            continue
        if inbound.get(pg.name, 0) > 0:
            continue
        my_tags = set(parse_list(pg.fm.get("tags", "")))
        my_mocs = links_in(pg.fm.get("moc", ""))
        props = []
        for m in my_mocs:
            if m in pages and pg.name not in links_in(pages[m].text):
                props.append(f"[[{m}]] 에 링크 추가 (moc: 선언돼 있는데 MOC 본문에 없음)")
        if my_tags:
            sib = [(o.name, len(my_tags & set(parse_list(o.fm.get("tags", "")))))
                   for o in pages.values()
                   if o.name != pg.name and o.kind != "moc"]
            sib = sorted([s for s in sib if s[1] > 0], key=lambda x: -x[1])[:3]
            for n, c in sib:
                props.append(f"[[{n}]] 와 태그 {c}개 공유 — 상호 링크 검토")
        if not my_mocs:
            props.append("moc: 미선언 — 소속 MOC를 정해야 한다")
        out.append((pg.rel, pg.name, props))
    rep["orphan"] = out


# ── 리포트 ────────────────────────────────────────────────────────────

def write_report(vault: Path, rep, fix) -> Path:
    d = dt.date.today().isoformat()
    out = vault / "meta" / "lint" / f"{d}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    L = rep["links"]
    n_fixed = len(rep["fixed"])
    n_ask = len(L["suggest"]) + len(rep["stale"])
    n_sug = len(rep["orphan"])

    w = [
        "---", f"title: Lint {d}", "type: moc", "tags: [meta]",
        f"created: {d}", f"updated: {d}", "---", "",
        f"# Lint 리포트 — {d}", "",
        f"모드: **{'--fix (자동 수정 적용)' if fix else 'check (읽기 전용)'}**",
        "",
        "| 항목 | 결과 |", "|---|---|",
        f"| 자동 수정 | {n_fixed}건 |",
        f"| 링크 — 자동 재연결 후보 | {len(L['auto'])} |",
        f"| 링크 — 확인 필요 | {len(L['suggest'])} |",
        f"| 링크 — 미작성(정상 TODO) | {len(L['todo'])} |",
        f"| frontmatter 결손 | {len(rep['frontmatter'])} |",
        f"| stale | {len(rep['stale'])} |",
        f"| orphan | {len(rep['orphan'])} |",
        "",
        "> `raw/` 는 이 검진에서 열지 않는다. 삭제는 어떤 항목에서도 하지 않는다.",
        "",
    ]

    w += ["---", "", "## ✅ 수정됨", ""]
    if rep["fixed"]:
        w += ["되돌리려면 `git diff` 로 확인 후 되돌린다.", ""]
        w += [f"{i}. {line}" for i, line in enumerate(rep["fixed"], 1)]
    else:
        w += ["_없음_" + ("" if fix else " — `--fix` 를 주지 않아 적용하지 않았다.")]
    w += [""]

    w += ["---", "", "## ⚠️ 사용자 결정 필요", ""]

    w += ["### 링크 — 매칭 후보가 애매함", ""]
    if L["suggest"]:
        w += ["| 깨진 링크 | 후보 | 유사도 | 나온 곳 |", "|---|---|---|---|"]
        for t, c, s, r in L["suggest"]:
            w.append(f"| `[[{t}]]` | {' · '.join(f'`{x}`' for x in c)} | {r:.2f} | {', '.join(s)} |")
    else:
        w += ["_없음_"]
    w += [""]

    w += ["### 링크 — 매칭 후보 없음", "",
          "유사한 페이지가 전혀 없다. **대부분은 아직 안 쓴 페이지(정상 TODO)**이지만, "
          "참조 횟수가 많은 것은 우선 작성 대상이다.", ""]
    if L["todo"]:
        top = sorted(L["todo"], key=lambda x: -len(x[1]))[:25]
        w += ["| 미작성 페이지 | 참조 | 나온 곳 |", "|---|---|---|"]
        for t, s in top:
            w.append(f"| `[[{t}]]` | {len(s)} | {', '.join(sorted(set(s))[:4])} |")
        if len(L["todo"]) > 25:
            w += ["", f"_… 외 {len(L['todo']) - 25}개_"]
    else:
        w += ["_없음_"]
    w += [""]

    w += ["### Stale — 지울지 살릴지 결정 요청", "",
          "**이 스크립트는 지우지 않는다.** 각 항목에 대해 갱신 / 보관 / 삭제를 정해 달라.", ""]
    if rep["stale"]:
        w += ["| 페이지 | 사유 | 본문 길이 |", "|---|---|---|"]
        for rel, why, size in rep["stale"]:
            w.append(f"| `{rel}` | {why} | {size}자 |")
    else:
        w += ["_없음_"]
    w += [""]

    w += ["---", "", "## 💡 제안 — 자동 적용 안 함", "", "### Orphan — 들어오는 링크 0", "",
          "**삭제하지 않는다.** 아래 연결 후보를 검토해 이어 붙인다.", ""]
    if rep["orphan"]:
        for rel, name, props in rep["orphan"]:
            w += [f"**`{rel}`**", ""]
            w += [f"- {p}" for p in props] or ["- 후보 없음 — 어느 MOC에 속하는지 직접 정해야 한다"]
            w += [""]
    else:
        w += ["_없음_", ""]

    w += ["---", "", "## 다음", "",
          "- [ ] 「수정됨」을 `git diff` 로 검토",
          "- [ ] 「확인 필요」 각 항목 결정",
          "- [ ] `log.md` 에 `## [%s] lint | 발견 N건` 추가" % d, ""]

    if out.exists():
        stamp = dt.datetime.now().strftime("%H%M%S%f")
        out = out.with_name(f"{out.stem}-{stamp}.md")
    out.write_text("\n".join(w), encoding="utf-8")
    return out


# ── main ──────────────────────────────────────────────────────────────

def cmd_run(args) -> int:
    vault = Path(args.vault).expanduser().resolve()
    if not (vault / "CLAUDE.md").is_file():
        sys.exit(f"볼트가 아니다 (CLAUDE.md 없음): {vault}")

    pages = collect(vault)
    vocab = load_vocab(vault)
    rep = {"fixed": []}

    only = set(args.only.split(",")) if args.only else None
    run = lambda n: only is None or n in only

    check_links(pages, args.fix and run("links"), rep) if run("links") else rep.setdefault(
        "links", {"auto": [], "suggest": [], "todo": []})
    if run("frontmatter"):
        check_frontmatter(pages, vocab, args.fix, rep)
    else:
        rep["frontmatter"] = []
    if run("stale"):
        check_stale(pages, args.stale_days, args.seed_days, rep)
    else:
        rep["stale"] = []
    if run("orphan"):
        check_orphan(pages, rep)
    else:
        rep["orphan"] = []

    path = write_report(vault, rep, args.fix)

    L = rep["links"]
    print(f"페이지 {len(pages)}개 검진\n")
    print(f"  수정됨              {len(rep['fixed'])}")
    print(f"  링크 자동 재연결 후보 {len(L['auto'])}")
    print(f"  링크 확인 필요       {len(L['suggest'])}")
    print(f"  링크 미작성(정상)    {len(L['todo'])}")
    print(f"  frontmatter 결손    {len(rep['frontmatter'])}")
    print(f"  stale               {len(rep['stale'])}")
    print(f"  orphan              {len(rep['orphan'])}")
    print(f"\n리포트: {path.relative_to(vault)}")
    if not args.fix and (L["auto"] or rep["frontmatter"]):
        print("→ --fix 로 자동 수정 적용")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="볼트 건강검진 (raw/ 는 열지 않는다)")
    ap.add_argument("--vault", default=str(DEFAULT_VAULT))
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("run")
    s.add_argument("--fix", action="store_true")
    s.add_argument("--stale-days", type=int, default=180)
    s.add_argument("--seed-days", type=int, default=60)
    s.add_argument("--only", help="links,frontmatter,stale,orphan 중 쉼표 구분")
    s.set_defaults(func=cmd_run)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
