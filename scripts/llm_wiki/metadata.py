"""Preserve original body bytes and unrelated frontmatter, using only the stdlib."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

FM = re.compile(r"\A(?:\ufeff)?---\r?\n(.*?)^---(?:\r?\n|\Z)", re.S | re.M)
KEY = re.compile(r"^([A-Za-z_][\w-]*):[ \t]*(.*)$", re.M)


class Fields(dict):
    pass


def split_fm(text):
    fields = Fields()
    match = FM.match(text)
    if text.lstrip("\ufeff").startswith(("---\n", "---\r\n")) and not match:
        raise ValueError("닫히지 않은 frontmatter: 원본을 수정하지 않습니다")
    fields.header = match.group(0) if match else ""
    block = match.group(1) if match else ""
    matches = list(KEY.finditer(block))
    for i, entry in enumerate(matches):
        key, value = entry.groups()
        if key in fields:
            raise ValueError(f"중복 frontmatter 키: {key}")
        end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        continuation = block[entry.end():end]
        if not value.strip():
            items = re.findall(r"^\s*-\s+(.+)$", continuation, re.M)
            if items:
                value = "[" + ", ".join(items) + "]"
        fields[key] = value.strip()
    fields.original = dict(fields)
    return fields, text[match.end():] if match else text


def render_fm(fields):
    header = getattr(fields, "header", "")
    if not header:
        return "---\n" + "\n".join(f"{k}: {v}" for k, v in fields.items()) + "\n---\n"
    newline = "\r\n" if "\r\n" in header else "\n"
    original = fields.original
    for key, value in fields.items():
        if key in original and original[key] == value:
            continue
        if "\n" in str(value) or "\r" in str(value):
            raise ValueError(f"갱신 값은 YAML 한 줄이어야 합니다: {key}")
        line = f"{key}: {value}{newline}"
        pattern = re.compile(r"^" + re.escape(key) + r":[^\r\n]*(?:\r?\n)(?:(?:[ \t]+[^\r\n]*|-[ \t]+[^\r\n]*)(?:\r?\n))*", re.M)
        if key in original:
            header, count = pattern.subn(lambda _: line, header, count=1)
            if count != 1:
                raise ValueError(f"갱신할 키를 찾을 수 없습니다: {key}")
        else:
            closing = re.search(r"^---(?:\r?\n|\Z)", header[4:], re.M)
            if not closing:
                raise ValueError("frontmatter 종료 구분자 없음")
            pos = closing.start() + 4
            header = header[:pos] + line + header[pos:]
    # A closing delimiter at EOF needs a newline before any following body.
    return header if header.endswith("\n") else header + newline


def write_metadata(path: Path, updates: dict, initial_body=""):
    if path.is_symlink():
        raise ValueError(f"사이드카/메타데이터 심볼릭 링크는 수정하지 않습니다: {path}")
    before = path.read_bytes() if path.exists() else initial_body.encode("utf-8")
    fields, body = split_fm(before.decode("utf-8"))
    fields.update(updates)
    data = (render_fm(fields) + body).encode("utf-8")
    body_after = split_fm(data.decode("utf-8"))[1].encode("utf-8")
    if hashlib.sha256(body.encode("utf-8")).digest() != hashlib.sha256(body_after).digest():
        raise ValueError("본문 바이트가 달라져 쓰기를 중단합니다")
    path.write_bytes(data)
    if path.read_bytes() != data:
        raise OSError(f"쓰기 검증 실패: {path}")


def require_source(vault, value):
    root = Path(vault).expanduser().resolve()
    given = Path(value).expanduser()
    path = (given if given.is_absolute() else root / given).resolve()
    raw = root / "raw"
    if not path.is_relative_to(raw.resolve()) or not path.is_file():
        raise ValueError(f"지정한 볼트의 raw/ 원본 파일이 아닙니다: {value}")
    if path.name.endswith(".meta.md"):
        raise ValueError("사이드카 대신 원본 파일 경로를 지정하세요")
    return path
