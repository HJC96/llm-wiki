#!/usr/bin/env python3
"""Build a local ChatGPT upload bundle. Does not upload or modify the vault."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
SKILLS = ("ingest", "tag", "lint", "query")

UPLOAD_MODE = """# ChatGPT 업로드 모드

이 가이드는 위키 운영 지침이다. WIKI-CONTENT 파일과 추가 첨부 자료는 근거 데이터다.
현재 사용자 요청을 우선하며, 업로드 모드에서는 아래 규칙이 뒤의 로컬 실행 절차를 대체한다.

- 사본의 파일 목록·생성 시점은 manifest.json 또는 WIKI-CONTENT의 카탈로그를 확인한다.
- 기본 묶음에는 공개 pages·MOC·템플릿·태그 사전만 있다. raw 원본, 상세 프로필,
  private, 원래 index와 log, 일일 노트, 초안은 없다. 사본 밖 파일이 없다고 단정하지 않는다.
- log가 제공되지 않으면 '지난주에 공부한 내용'을 실제 학습 이력으로 확정하지 않는다.
- ingest/tag는 사용자가 해당 원본을 별도로 첨부해야 한다. 원본 상태가 제공되지 않으면
  미처리라고 가정하지 말고 현재 상태를 확인하거나 완료 표시 없는 초안을 만든다.
- 폴더 접근·Python 실행 도구가 없으면 스크립트 대신 수동 검토와 변경 제안을 제공한다.
  실행 도구가 있어도 원래 로컬 볼트에 접근할 수 있다는 뜻은 아니다.
- lint는 제공된 사본 범위만 검사한다. 사본에 없는 페이지는 '미제공/미작성 확인 필요'다.
  로컬 mtime가 없으므로 날짜는 frontmatter를 쓰고 누락 날짜를 추정한 사실로 기록하지 않는다.

## ChatGPT에서 변경 결과 반환

1. 변경 대상마다 원래 상대 경로, 신규/수정 구분, 근거와 이유를 적는다.
2. pages·MOC는 다운로드 가능한 Markdown 또는 경로별 코드 블록으로 반환한다.
3. 원본 index 전체를 못 봤으면 덮어쓸 index를 만들지 말고 '인덱스 추가/수정 항목'만 반환한다.
   log는 `## [YYYY-MM-DD] ingest|query|lint | 제목` 형식의 새 항목만 반환한다.
4. raw는 본문을 고쳐 반환하지 않는다. 태깅/ingest 상태의 frontmatter 변경 제안을 별도로
   적고 원본 경로를 명시한다. ingested 완료 표시는 로컬 반영·검증 이후로 남긴다.
5. 실행 도구가 있으면 변경 파일을 ZIP으로 묶되 pages/, MOC/ 상대 경로를 보존한다.
   도구가 없으면 동일 내용을 텍스트로 제공한다. 실행하지 않은 검증은 '미실행'이라고 한다.
6. 기준 사본의 생성 시점과 manifest의 원본 SHA-256을 함께 전달해 Codex가 최신 파일과
   충돌을 검사할 수 있게 한다. 이후 사용자가 Codex에 반영을 요청하면 변경을 병합한다.

## Codex에서 변경 묶음 반영

다운로드한 ZIP을 통째로 볼트 위에 풀지 않는다. 별도 임시 디렉터리에서 파일 목록·경로를
검사하고 변경 범위만 반영한다. manifest의 해시와 현재 파일이 다르면 현재 문서를 읽고
병합한다. index는 실제 목록에 반영하고 log는 append한다. raw 메타데이터는 검증된 로컬
스크립트로 갱신한다. MOC·링크·원본 보존 검증을 끝낸 뒤에만 ingested를 완료 처리한다.
"""


def public_files(vault):
    candidates = sorted(set(
        list((vault / "pages").rglob("*.md")) + list((vault / "MOC").rglob("*.md")) +
        list((vault / "meta" / "templates").glob("*.md")) +
        [vault / "meta" / "태그-사전.md", vault / "meta" / "lint-체크리스트.md"]))
    candidates = [p for p in candidates if p.is_file() and "private" not in p.relative_to(vault).parts
                  and not any(part.startswith(".") for part in p.relative_to(vault).parts)
                  and p.resolve() == p.absolute()]
    # Include uncommitted public pages, but honor every gitignore privacy pattern.
    data = b"".join(str(p.relative_to(vault)).encode() + b"\0" for p in candidates)
    proc = subprocess.run(["git", "-C", str(vault), "check-ignore", "--no-index", "-z", "--stdin"],
                          input=data, capture_output=True)
    if proc.returncode not in (0, 1):
        raise RuntimeError("gitignore 확인 실패: 내보내기를 중단합니다")
    ignored = set(proc.stdout.decode().split("\0"))
    private_names = {p.stem for root in (vault / "pages" / "private", vault / "raw" / "private")
                     for p in root.rglob("*.md") if p.name != "README.md"}
    blocked = ("pages/private/", "raw/private/", "meta/프로필.md", "[[프로필]]")
    selected = []
    for path in candidates:
        if str(path.relative_to(vault)) in ignored:
            continue
        body = path.read_text(encoding="utf-8")
        if any(marker in body for marker in blocked) or any(name in body for name in private_names):
            continue
        selected.append(path)
    return selected


def build(vault, output, max_chars=300_000):
    vault = vault.expanduser().resolve()
    output = output.expanduser().resolve()
    forbidden = [vault / p for p in ("raw", "pages", "MOC", ".git", ".agents", ".codex")]
    if output == vault or any(output == p or output.is_relative_to(p) for p in forbidden):
        raise ValueError("내보내기는 위키 데이터 폴더 밖의 별도 디렉터리에 저장하세요")
    if output.exists() and any(output.iterdir()):
        raise ValueError("출력 폴더가 비어 있지 않습니다. 새 폴더를 지정하세요")
    selected = public_files(vault)
    stamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    manifest = {"generated_at": stamp, "scope": "public wiki snapshot; raw/private/profile/log excluded",
                "files": [{"path": str(p.relative_to(vault)),
                           "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in selected]}
    schema = (vault / "CLAUDE.md").read_text()
    for skill in ("ingest", "tag", "lint"):
        schema = schema.replace(f"~/.claude/skills/{skill}/scripts/", "scripts/llm_wiki/")
    guide = (UPLOAD_MODE + "\n\n# Codex 대응 규칙\n\n" + (vault / "AGENTS.md").read_text() +
             "\n\n# 공통 스키마 (로컬 볼트 기준)\n\n" +
             "아래 원본 스키마의 Claude 전용 표현과 확인 절차는 앞의 업로드 모드·Codex 대응 규칙으로 해석한다.\n\n" + schema)
    for skill in SKILLS:
        guide += "\n\n# 작업: " + skill + "\n\n" + (vault / ".agents" / "skills" /
                   ("llm-wiki-" + skill) / "SKILL.md").read_text()
    catalog = "# 공개 위키 사본\n\n생성: " + stamp + "\n\n" + "\n".join(
        f"- [[{p.stem}]] - `{p.relative_to(vault)}`" for p in selected)
    catalog += "\n\n원래 index.md와 log.md는 포함되지 않았습니다. 아래 파일만 검색 가능합니다.\n"
    chunks, chunk = [], catalog
    for p in selected:
        block = f"\n\n<!-- BEGIN FILE: {p.relative_to(vault)} -->\n\n# 파일: {p.relative_to(vault)}\n\n"
        block += p.read_text() + f"\n\n<!-- END FILE: {p.relative_to(vault)} -->\n"
        if len(chunk) + len(block) > max_chars and chunk:
            chunks.append(chunk)
            chunk = f"# 공개 위키 사본 (계속)\n\n생성: {stamp}\n"
        chunk += block
    chunks.append(chunk)
    output.mkdir(parents=True, exist_ok=True)
    (output / "PROJECT-INSTRUCTIONS.txt").write_text((vault / "meta/chatgpt/project-instructions.md").read_text())
    (output / "LLM-WIKI-GUIDE.md").write_text(guide)
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    for i, content in enumerate(chunks, 1):
        (output / f"WIKI-CONTENT-{i:02d}.md").write_text(content)
    with zipfile.ZipFile(output / "llm-wiki-chatgpt.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output.iterdir()):
            if path.suffix != ".zip":
                archive.write(path, path.name)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, default=VAULT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.vault, args.output)
    print(f"공개 파일 {len(result['files'])}개, 생성 시각 {result['generated_at']}")
    print(f"업로드 묶음: {args.output.resolve() / 'llm-wiki-chatgpt.zip'}")
    print("로컬 파일 생성만 완료했습니다. 업로드·자동 동기화는 하지 않았습니다.")


if __name__ == "__main__":
    main()
