"""Tests for skills/assisted-by-trailers/scripts/check_trailers.py.

Run from the repository root:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "assisted-by-trailers" / "scripts" / "check_trailers.py"

_spec = importlib.util.spec_from_file_location("check_trailers", SCRIPT)
check_trailers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_trailers)


def msg(text: str) -> str:
    return textwrap.dedent(text).lstrip("\n")


class ValidMessages(unittest.TestCase):
    def assertOk(self, text: str, **kwargs) -> None:
        self.assertEqual(check_trailers.check(text, **kwargs), [])

    def test_single_generation_trailer(self):
        self.assertOk(msg("""
            Fix off-by-one in pagination

            The last page was skipped.

            Assisted-by: Claude Opus 5.5 (code generation)
            """), require=True)

    def test_subject_and_trailer_only(self):
        self.assertOk(msg("""
            Fix typo

            Assisted-by: Claude Opus 5.5 (code generation)
            """), require=True)

    def test_vendors_and_roles_each_get_a_line(self):
        self.assertOk(msg("""
            Add retry

            Assisted-by: Claude Opus 5.5 (code generation)
            Assisted-by: GPT-5 (code generation)
            Assisted-by: Claude Opus 5.5 (code review)
            Assisted-by: Gemini 3 Pro (code review)
            """), require=True)

    def test_other_trailers_in_final_paragraph(self):
        self.assertOk(msg("""
            Add retry

            Co-authored-by: Jane Doe <jane@example.com>
            Co-authored-by: octo <123+octo@users.noreply.github.com>
            Signed-off-by: Frank Example <frank@example.com>
            Assisted-by: Claude Opus 5.5 (code generation)
            """), require=True)

    def test_sign_off_appended_by_git_after_assisted_by(self):
        self.assertOk(msg("""
            Add retry

            Assisted-by: Claude Opus 5.5 (code generation)
            Signed-off-by: Frank Example <frank@example.com>
            """), require=True)

    def test_continuation_line_in_trailer_paragraph(self):
        self.assertOk(msg("""
            Add retry

            Fixes: a very long description that git wrapped
              onto a continuation line
            Assisted-by: Claude Opus 5.5 (code generation)
            """), require=True)

    def test_no_trailer_is_fine_without_require(self):
        self.assertOk("Human-only commit\n\nNo AI was involved.\n")

    def test_empty_message_without_require(self):
        self.assertOk("")

    def test_crlf_line_endings(self):
        self.assertOk(
            "Fix\r\n\r\nAssisted-by: Claude Opus 5.5 (code generation)\r\n",
            require=True,
        )

    def test_trailing_whitespace_and_blank_lines(self):
        self.assertOk(
            "Fix\n\nAssisted-by: Claude Opus 5.5 (code generation)   \n\n\n",
            require=True,
        )

    def test_git_comments_and_scissors_are_ignored_for_commits(self):
        self.assertOk(msg("""
            Fix

            Assisted-by: Claude Opus 5.5 (code generation)
            # Please enter the commit message for your changes.
            # ------------------------ >8 ------------------------
            # Do not modify or remove the line above.
            diff --git a/x b/x
            Co-Authored-By: Claude <noreply@anthropic.com>
            """), require=True)

    def test_quoted_generated_with_is_prose(self):
        self.assertOk(msg("""
            Remove footers

            Drop the
            "Generated with" footers and `Generated with` lines.

            Assisted-by: Claude Opus 5.5 (code generation)
            """), require=True)

    def test_pr_body_may_be_only_trailers(self):
        self.assertOk(
            "Assisted-by: Claude Opus 5.5 (code generation)\n",
            kind="pr", require=True,
        )

    def test_pr_body_with_markdown(self):
        self.assertOk(msg("""
            ## Summary

            - adds retry with backoff

            ## Test plan

            - [x] unit tests

            Assisted-by: Claude Opus 5.5 (code generation)
            """), kind="pr", require=True)


class InvalidMessages(unittest.TestCase):
    def assertProblem(self, text: str, fragment: str, **kwargs) -> None:
        problems = check_trailers.check(text, **kwargs)
        self.assertTrue(
            any(fragment in p for p in problems),
            f"expected a problem containing {fragment!r}, got {problems!r}",
        )

    def test_missing_trailer_with_require(self):
        self.assertProblem("Fix\n\nBody.\n", "no Assisted-by trailer", require=True)

    def test_noreply_co_author(self):
        self.assertProblem(msg("""
            Fix

            Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
            """), "remove this AI co-author trailer")

    def test_noreply_co_author_any_case(self):
        self.assertProblem(
            "Fix\n\nco-authored-by: Bot <NOREPLY@example.com>\n",
            "AI co-author",
        )

    def test_generated_with_footer(self):
        self.assertProblem(msg("""
            ## Summary

            Adds retry.

            🤖 Generated with [Claude Code](https://claude.com/claude-code)
            """), "Generated with", kind="pr")

    def test_email_in_model(self):
        self.assertProblem(
            "Fix\n\nAssisted-by: Claude Opus 5.5 <noreply@anthropic.com> (code generation)\n",
            "without an email address",
        )

    def test_unknown_role(self):
        self.assertProblem(
            "Fix\n\nAssisted-by: Claude Opus 5.5 (code writing)\n",
            "expected 'Assisted-by: <model> (code",
        )

    def test_missing_role(self):
        self.assertProblem(
            "Fix\n\nAssisted-by: Claude Opus 5.5\n",
            "expected 'Assisted-by: <model> (code",
        )

    def test_wrong_key_case(self):
        self.assertProblem(
            "Fix\n\nAssisted-By: Claude Opus 5.5 (code generation)\n",
            "expected 'Assisted-by: <model> (code",
        )

    def test_extra_spaces(self):
        self.assertProblem(
            "Fix\n\nAssisted-by:  Claude Opus 5.5 (code generation)\n",
            "expected 'Assisted-by: <model> (code",
        )

    def test_same_vendor_same_role_twice(self):
        self.assertProblem(msg("""
            Fix

            Assisted-by: Claude Sonnet 5 (code generation)
            Assisted-by: Claude Opus 5.5 (code generation)
            """), "second 'code generation' line for vendor Anthropic (first on line 3)")

    def test_exact_duplicate_line(self):
        self.assertProblem(msg("""
            Fix

            Assisted-by: GPT-5 (code review)
            Assisted-by: GPT-5 (code review)
            """), "vendor OpenAI")

    def test_unknown_vendor_grouped_by_first_word(self):
        self.assertProblem(msg("""
            Fix

            Assisted-by: Acme Coder 1 (code generation)
            Assisted-by: Acme Coder 2 (code generation)
            """), "vendor acme")

    def test_trailer_not_in_final_paragraph(self):
        self.assertProblem(msg("""
            Fix

            Assisted-by: Claude Opus 5.5 (code generation)

            More text after the trailer.
            """), "belong in the final paragraph")

    def test_text_mixed_into_trailer_paragraph(self):
        self.assertProblem(msg("""
            Fix

            Some body text.
            Assisted-by: Claude Opus 5.5 (code generation)
            """), "trailers only")

    def test_trailer_in_subject_paragraph(self):
        self.assertProblem(
            "Assisted-by: Claude Opus 5.5 (code generation)\n",
            "subject paragraph",
        )

    def test_markdown_heading_counts_in_pr_bodies(self):
        self.assertProblem(msg("""
            Adds retry.

            # Notes
            Assisted-by: Claude Opus 5.5 (code generation)
            """), "trailers only", kind="pr")

    def test_indented_trailer(self):
        self.assertProblem(
            "Fix\n\n  Assisted-by: Claude Opus 5.5 (code generation)\n",
            "expected 'Assisted-by: <model> (code",
        )

    def test_reports_every_problem(self):
        problems = check_trailers.check(msg("""
            Fix

            Co-Authored-By: Claude <noreply@anthropic.com>
            Assisted-by: Claude Opus 5.5 <x@y> (code generation)
            🤖 Generated with Claude Code
            """))
        self.assertEqual(len(problems), 4, problems)


class VendorLookup(unittest.TestCase):
    def test_known_vendors(self):
        cases = {
            "Claude Opus 5.5": "Anthropic",
            "GPT-5": "OpenAI",
            "o3": "OpenAI",
            "Gemini 3 Pro": "Google",
            "Llama 4": "Meta",
            "Devstral": "Mistral AI",
            "Grok 4": "xAI",
            "Qwen3-Coder": "Alibaba",
            "o4-mini": "OpenAI",
            "Acme Coder 1": "acme",
            "1337 Model": "1337",
        }
        for model, vendor in cases.items():
            with self.subTest(model=model):
                self.assertEqual(check_trailers.vendor_of(model), vendor)


class CommandLine(unittest.TestCase):
    def run_script(self, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=stdin, capture_output=True, text=True, check=False,
        )

    def test_ok_from_stdin_is_silent(self):
        result = self.run_script(
            "--require", stdin="Fix\n\nAssisted-by: Claude Opus 5.5 (code generation)\n"
        )
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_problems_exit_1_and_go_to_stderr(self):
        result = self.run_script("--require", stdin="Fix\n")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("1 problem(s) in standard input", result.stderr)

    def test_file_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "MSG")
            path.write_text("Fix\n\nAssisted-by: GPT-5 (code review)\n", encoding="utf-8")
            self.assertEqual(self.run_script("--require", str(path)).returncode, 0)

    def test_non_utf8_file_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "MSG")
            path.write_bytes(
                "Größe korrigiert\n\nAssisted-by: GPT-5 (code review)\n".encode("latin-1")
            )
            self.assertEqual(self.run_script("--require", str(path)).returncode, 0)
            path.write_bytes("Größe\n\nCo-Authored-By: X <noreply@x>\n".encode("latin-1"))
            self.assertEqual(self.run_script(str(path)).returncode, 1)

    def test_utf8_stdin_regardless_of_locale(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--kind", "pr"],
            input="🤖 Generated with Claude Code\n".encode("utf-8"),
            capture_output=True, check=False,
            env={**os.environ, "LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0"},
        )
        self.assertEqual(result.returncode, 1, result.stderr)

    def test_missing_file_exits_2(self):
        result = self.run_script("/nonexistent/message")
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot read", result.stderr)

    def test_bad_option_exits_2(self):
        self.assertEqual(self.run_script("--kind", "email").returncode, 2)


@unittest.skipUnless(shutil.which("git"), "git is not installed")
@unittest.skipIf(os.name == "nt", "hook test uses a POSIX shebang")
class CommitMsgHook(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(
            GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
            GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.com",
            GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.com",
        )
        self.env = env
        self.git("init", "-q")
        hook = self.repo / ".git" / "hooks" / "commit-msg"
        hook.write_text(
            f"#!/bin/sh\nexec '{sys.executable}' '{SCRIPT}' \"$1\"\n", encoding="utf-8"
        )
        hook.chmod(hook.stat().st_mode | stat.S_IXUSR)

    def tearDown(self):
        self._tmp.cleanup()

    def git(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args], cwd=self.repo, env=self.env,
            capture_output=True, text=True, check=False,
        )

    def commit(self, message: str) -> subprocess.CompletedProcess:
        return self.git("commit", "-q", "--allow-empty", "-m", message)

    def test_valid_commit_passes(self):
        result = self.commit("Fix\n\nAssisted-by: Claude Opus 5.5 (code generation)")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_human_commit_without_trailer_passes(self):
        self.assertEqual(self.commit("Human change").returncode, 0)

    def test_noreply_co_author_is_rejected(self):
        result = self.commit("Fix\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("AI co-author", result.stderr)
        self.assertNotEqual(self.git("rev-parse", "-q", "--verify", "HEAD").returncode, 0)


if __name__ == "__main__":
    unittest.main()
