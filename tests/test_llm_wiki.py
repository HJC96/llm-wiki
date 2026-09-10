import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts/llm_wiki"
sys.path.insert(0, str(SCRIPTS))
import export_chatgpt
import lint_tool
import metadata
import moc_sync
import protect_raw


class WikiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wiki-test-")
        self.addCleanup(self.temp.cleanup)
        self.vault = Path(self.temp.name) / "vault with spaces"
        self.vault.mkdir()
        for name in ("raw/inbox", "raw/private", "pages/concepts", "pages/private", "MOC", "meta/templates"):
            (self.vault / name).mkdir(parents=True)
        (self.vault / "CLAUDE.md").write_text("# Schema\n")
        (self.vault / "AGENTS.md").write_text("# Codex\n")
        (self.vault / "meta/태그-사전.md").write_text("| `java` | Java |\n| `jpa` | JPA |\n")

    def cli(self, script, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / script), "--vault", str(self.vault), *args],
                              cwd=self.temp.name, text=True, capture_output=True)

    def source(self, data):
        path = self.vault / "raw/inbox/sample.md"
        path.write_bytes(data)
        return path

    def test_tag_preserves_crlf_body_and_nested_metadata(self):
        data = ('---\r\ntitle: Before\r\ntags:\r\n  - old\r\ncustom:\r\n  owner: retained\r\n'
                'description: |\r\n  first\r\n  second\r\n# KEEP\r\n---\r\n\r\n본문  \r\n끝').encode()
        path = self.source(data)
        result = self.cli("tag_tool.py", "set", "raw/inbox/sample.md", "--tags", "java,jpa", "--title", "제목: #인용")
        self.assertEqual(result.returncode, 0, result.stderr)
        after = path.read_bytes()
        self.assertEqual(after.split(b"---\r\n", 2)[2], data.split(b"---\r\n", 2)[2])
        self.assertIn(b"custom:\r\n  owner: retained\r\n", after)
        self.assertIn(b"description: |\r\n  first\r\n  second\r\n# KEEP", after)
        self.assertEqual(json.loads(metadata.split_fm(after.decode())[0]["title"]), "제목: #인용")

    def test_state_lifecycle_and_completed_tag_skip(self):
        p = self.source(b"original\r\nbody\r\n")
        for args in [("init", "raw/inbox/sample.md"),
                     ("mark", "raw/inbox/sample.md", "--page", 'Title "quoted"', "--pages", "3")]:
            result = self.cli("ingest_state.py", *args)
            self.assertEqual(result.returncode, 0, result.stderr)
        before = p.read_bytes()
        result = self.cli("tag_tool.py", "set", "raw/inbox/sample.md", "--tags", "java")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(p.read_bytes(), before)
        result = self.cli("ingest_state.py", "unmark", "raw/inbox/sample.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        fields, body = metadata.split_fm(p.read_bytes().decode())
        self.assertEqual(fields["ingested"], "false")
        self.assertEqual(fields["pages_touched"], "")
        self.assertEqual(body.encode(), b"original\r\nbody\r\n")

    def test_binary_sidecar_preserves_source(self):
        p = self.vault / "raw/inbox/test.pdf"
        data = b"%PDF\x00\xff\r\n"
        p.write_bytes(data)
        result = self.cli("tag_tool.py", "set", "raw/inbox/test.pdf", "--tags", "java")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(p.read_bytes(), data)
        self.assertTrue(p.with_name("test.pdf.meta.md").is_file())

    def test_reject_outside_and_symlink_escape(self):
        outside = Path(self.temp.name) / "outside.md"
        outside.write_text("untouched")
        (self.vault / "raw/inbox/escape.md").symlink_to(outside)
        for path in (str(outside), "raw/inbox/escape.md"):
            result = self.cli("ingest_state.py", "init", path)
            self.assertNotEqual(result.returncode, 0)
        self.assertEqual(outside.read_text(), "untouched")

    def test_bad_frontmatter_fails_without_writing(self):
        for data in (b"---\na: x\nbody", b"---\na: x\na: y\n---\nbody", b"invalid\xff"):
            p = self.source(data)
            result = self.cli("ingest_state.py", "init", "raw/inbox/sample.md")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(p.read_bytes(), data)

    def test_empty_and_bom_frontmatter(self):
        for data in (b"---\n---\nbody", b"\xef\xbb\xbf---\r\na: x\r\n---\r\n\r\nbody", b"---\na: x\n---"):
            p = self.source(data)
            body = metadata.split_fm(data.decode())[1]
            metadata.write_metadata(p, {"ingested": "false"})
            self.assertEqual(metadata.split_fm(p.read_bytes().decode())[1], body)

    def test_moc_check_then_fix_then_check(self):
        page = self.vault / "pages/concepts/Example.md"
        page.write_text('---\ntype: concept\nmoc: ["[[MOC-Test]]"]\n---\nBody\n')
        moc = self.vault / "MOC/MOC-Test.md"
        moc.write_text("---\ntype: moc\n---\n# Test\n")
        before = moc.read_bytes()
        result = self.cli("moc_sync.py", "check")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(moc.read_bytes(), before)
        self.cli("moc_sync.py", "check", "--fix")
        result = self.cli("moc_sync.py", "check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_lint_report_only_and_fix_preserve_other_metadata(self):
        page = self.vault / "pages/concepts/Example.md"
        page.write_text("---\ncustom:\n  nested: retained\n---\nJava body\n")
        before = page.read_bytes()
        first = self.cli("lint_tool.py", "run", "--only", "frontmatter")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(page.read_bytes(), before)
        second = self.cli("lint_tool.py", "run", "--fix", "--only", "frontmatter")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("custom:\n  nested: retained", page.read_text())
        self.assertEqual(len(list((self.vault / "meta/lint").glob("*.md"))), 2)
        self.assertNotIn("AGENTS", [p.name for p in lint_tool.collect(self.vault).values() if p.kind == "stray"])

    def test_lint_does_not_open_raw_private_or_profile(self):
        self.source(b"\xff")
        (self.vault / "pages/private/hidden.md").write_bytes(b"\xff")
        (self.vault / "meta/프로필.md").write_bytes(b"\xff")
        (self.vault / "pages/concepts/raw-alias.md").symlink_to(self.vault / "raw/inbox/sample.md")
        result = self.cli("lint_tool.py", "run")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = next((self.vault / "meta/lint").glob("*.md")).read_text()
        self.assertNotIn("hidden", report)
        self.assertNotIn("raw-alias", report)

    def test_lint_only_fixes_high_links_and_retains_todos(self):
        (self.vault / "pages/concepts/낙관적 락.md").write_text("---\ntype: concept\n---\nTarget\n")
        referring = self.vault / "pages/concepts/Ref.md"
        referring.write_text("---\ntype: concept\n---\n[[낙관적락#원리|설명]] [[낙관적 락 실험]] [[완전히 별개 개념]]\n")
        result = self.cli("lint_tool.py", "run", "--fix", "--only", "links")
        self.assertEqual(result.returncode, 0, result.stderr)
        content = referring.read_text()
        self.assertIn("[[낙관적 락#원리|설명]]", content)
        self.assertIn("[[낙관적 락 실험]]", content)
        self.assertIn("[[완전히 별개 개념]]", content)
        report = next((self.vault / "meta/lint").glob("*.md")).read_text()
        self.assertIn("링크 재연결", report)

    def test_guard_covers_add_delete_move_and_normalized_paths(self):
        for op in ("Add File: raw/inbox/new.md", "Delete File: raw/inbox/sample.md",
                   "Update File: pages/../raw/inbox/sample.md", "Move to: raw/inbox/moved.md"):
            payload = {"tool_name": "apply_patch", "cwd": str(self.vault),
                       "tool_input": {"command": "*** Begin Patch\n*** " + op + "\n*** End Patch"}}
            self.assertTrue(protect_raw.blocked_paths(payload, self.vault))
        payload["tool_input"]["command"] = "*** Begin Patch\n*** Add File: pages/concepts/OK.md\n+OK\n*** End Patch"
        self.assertEqual(protect_raw.blocked_paths(payload, self.vault), [])
        (self.vault / "alias").symlink_to(self.vault / "raw", target_is_directory=True)
        payload["tool_input"]["command"] = "*** Begin Patch\n*** Add File: alias/file.md\n*** End Patch"
        self.assertTrue(protect_raw.blocked_paths(payload, self.vault))

    def test_guard_json_contract(self):
        payload = {"tool_name": "apply_patch", "cwd": str(ROOT),
                   "tool_input": {"command": "*** Begin Patch\n*** Delete File: raw/example.md\n*** End Patch"}}
        proc = subprocess.run([sys.executable, str(SCRIPTS / "protect_raw.py")], input=json.dumps(payload), text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0)
        result = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(result["permissionDecision"], "deny")

    def test_export_scope_manifest_and_original_preservation(self):
        subprocess.run(["git", "init", "-q", str(self.vault)], check=True, capture_output=True)
        (self.vault / ".gitignore").write_text("raw/**\npages/private/**\n*salary*\n")
        self.source(b"RAW NEVER EXPORT")
        (self.vault / "pages/private/Secret person.md").write_text("PRIVATE NEVER EXPORT")
        (self.vault / "pages/concepts/salary.md").write_text("SALARY NEVER EXPORT")
        (self.vault / "pages/concepts/leaking.md").write_text("[[Secret person]]")
        public = self.vault / "pages/concepts/Public.md"
        public.write_text("PUBLIC CONTENT")
        (self.vault / "pages/concepts/alias.md").symlink_to(self.vault / "raw/inbox/sample.md")
        shutil.copytree(ROOT / ".agents", self.vault / ".agents")
        shutil.copytree(ROOT / "meta/chatgpt", self.vault / "meta/chatgpt")
        before = public.read_bytes()
        output = Path(self.temp.name) / "export"
        manifest = export_chatgpt.build(self.vault, output, max_chars=300)
        texts = "".join(p.read_text() for p in output.glob("*.md"))
        self.assertIn("PUBLIC CONTENT", texts)
        for forbidden in ("RAW NEVER EXPORT", "PRIVATE NEVER EXPORT", "SALARY NEVER EXPORT", "Secret person"):
            self.assertNotIn(forbidden, texts)
        self.assertEqual(public.read_bytes(), before)
        self.assertIn("pages/concepts/Public.md", [x["path"] for x in manifest["files"]])
        self.assertTrue((output / "llm-wiki-chatgpt.zip").is_file())
        with self.assertRaises(ValueError):
            export_chatgpt.build(self.vault, output)
        with self.assertRaises(ValueError):
            export_chatgpt.build(self.vault, self.vault / "raw/export")


if __name__ == "__main__":
    unittest.main()
