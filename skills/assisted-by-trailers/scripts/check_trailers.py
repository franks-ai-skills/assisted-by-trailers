#!/usr/bin/env python3
"""Check a commit message or pull request description against the
Assisted-by trailer rules of the assisted-by-trailers skill.

Usage:
    check_trailers.py [--require] [--kind commit|pr] [FILE]

FILE is the text to check; omit it or pass "-" to read standard input.
Because git passes the message file as the only argument, the script also
works unchanged as a commit-msg hook.

Checks:
  * no "Co-Authored-By: ... <noreply@...>" trailers
    (human co-authors with real addresses are fine)
  * no "Generated with ..." footers
  * every "Assisted-by:" line has the exact form
    "Assisted-by: <model> (code generation)" or "... (code review)",
    without an email address
  * all "Assisted-by:" lines are in the final paragraph, and that paragraph
    holds trailers only (and, for commits, is not the subject paragraph)
  * at most one "Assisted-by:" line per vendor and role
  * with --require: at least one "Assisted-by:" line exists

The vendor of a model is looked up from the first word of its name (see
VENDORS and vendor_of); unknown first words count as their own vendor.

For --kind commit (the default), lines starting with "#" are ignored and
everything from git's scissors line on is cut off, as git does with the
default commit.cleanup and core.commentChar settings. For --kind pr, every
line counts, so Markdown headings are not mistaken for comments.

Exit status: 0 if the text follows the rules, 1 if it does not (each problem
is printed to standard error), 2 on usage or read errors.
"""

from __future__ import annotations

import argparse
import re
import sys

ROLES = ("code generation", "code review")

# First word of a model name (lowercase) -> vendor.
VENDORS = {
    "claude": "Anthropic",
    "anthropic": "Anthropic",
    "gpt": "OpenAI",
    "chatgpt": "OpenAI",
    "codex": "OpenAI",
    "o1": "OpenAI",
    "o3": "OpenAI",
    "o4": "OpenAI",
    "openai": "OpenAI",
    "gemini": "Google",
    "gemma": "Google",
    "google": "Google",
    "llama": "Meta",
    "meta": "Meta",
    "mistral": "Mistral AI",
    "codestral": "Mistral AI",
    "devstral": "Mistral AI",
    "magistral": "Mistral AI",
    "ministral": "Mistral AI",
    "mixtral": "Mistral AI",
    "grok": "xAI",
    "xai": "xAI",
    "deepseek": "DeepSeek",
    "qwen": "Alibaba",
}

SCISSORS = "# ------------------------ >8 ------------------------"

ASSISTED_KEY = re.compile(r"assisted-by\s*:", re.IGNORECASE)
ASSISTED_LINE = re.compile(
    r"Assisted-by: (?P<model>\S(?:.*\S)?) \((?P<role>"
    + "|".join(map(re.escape, ROLES))
    + r")\)"
)
EMAIL_LIKE = re.compile(r"[<>@]")
NOREPLY_COAUTHOR = re.compile(r"\s*co-authored-by\s*:.*<noreply@", re.IGNORECASE)
# Optional emoji or bullet, but not a quote: quoted mentions are prose.
GENERATED_WITH = re.compile(r"""[^\w"'`“‘„]*generated with\b""", re.IGNORECASE)
# A git trailer line ("Token: value") or a continuation line (leading space).
TRAILER_LINE = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*:\s|\s+\S")

Line = tuple[int, str]  # (1-based line number, text without line ending)


def vendor_of(model: str) -> str:
    """Vendor for a model name, from its first word ("Qwen3-Coder" -> "qwen3",
    then its leading letters "qwen" if the whole word is unknown)."""
    first_word = re.split(r"[^0-9a-z]+", model.lower(), maxsplit=1)[0]
    letters = re.match(r"[a-z]*", first_word).group()
    return VENDORS.get(first_word) or VENDORS.get(letters) or first_word or model


def relevant_lines(text: str, kind: str) -> list[Line]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    result: list[Line] = []
    for number, line in enumerate(lines, start=1):
        if kind == "commit":
            if line.rstrip() == SCISSORS:
                break
            if line.startswith("#"):
                continue
        result.append((number, line.rstrip()))
    return result


def paragraphs(lines: list[Line]) -> list[list[Line]]:
    result: list[list[Line]] = []
    current: list[Line] = []
    for number, line in lines:
        if line.strip():
            current.append((number, line))
        elif current:
            result.append(current)
            current = []
    if current:
        result.append(current)
    return result


def check(text: str, kind: str = "commit", require: bool = False) -> list[str]:
    """Return a list of problems; an empty list means the text is fine."""
    lines = relevant_lines(text, kind)
    problems: list[str] = []

    for number, line in lines:
        if NOREPLY_COAUTHOR.match(line):
            problems.append(
                f"line {number}: remove this AI co-author trailer and use "
                f"an Assisted-by line instead: {line.strip()}"
            )
        if GENERATED_WITH.match(line):
            problems.append(
                f"line {number}: remove this 'Generated with' footer: "
                f"{line.strip()}"
            )

    assisted = [(n, line) for n, line in lines if ASSISTED_KEY.match(line.lstrip())]
    if not assisted:
        if require:
            problems.append(
                "no Assisted-by trailer: end the text with a paragraph like "
                "'Assisted-by: <model> (code generation)'"
            )
        return problems

    paras = paragraphs(lines)
    final = paras[-1]
    final_numbers = {n for n, _ in final}

    if kind == "commit" and len(paras) == 1:
        problems.append(
            f"line {final[0][0]}: trailers cannot be part of the subject "
            "paragraph; add a subject line and a blank line before them"
        )

    seen: dict[tuple[str, str], int] = {}
    for number, line in assisted:
        if number not in final_numbers:
            problems.append(
                f"line {number}: Assisted-by trailers belong in the final "
                "paragraph"
            )
        match = ASSISTED_LINE.fullmatch(line)
        if not match:
            problems.append(
                f"line {number}: expected 'Assisted-by: <model> (code "
                f"generation)' or '... (code review)', got: {line.strip()}"
            )
            continue
        model, role = match["model"], match["role"]
        if EMAIL_LIKE.search(model):
            problems.append(
                f"line {number}: use the model name without an email "
                f"address: {line.strip()}"
            )
            continue
        key = (vendor_of(model), role)
        if key in seen:
            problems.append(
                f"line {number}: second '{role}' line for vendor {key[0]} "
                f"(first on line {seen[key]}); keep only the latest model, "
                "or the most expensive one of the same release"
            )
        else:
            seen[key] = number

    for number, line in final:
        if not TRAILER_LINE.match(line):
            problems.append(
                f"line {number}: the final trailer paragraph may contain "
                f"trailers only; separate this text with a blank line: "
                f"{line.strip()}"
            )

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check a commit message or PR description against the "
        "Assisted-by trailer rules."
    )
    parser.add_argument(
        "file", nargs="?", default="-",
        help="file to check (default: standard input)",
    )
    parser.add_argument(
        "--kind", choices=("commit", "pr"), default="commit",
        help="commit message (default) or pull request description",
    )
    parser.add_argument(
        "--require", action="store_true",
        help="fail if there is no Assisted-by trailer",
    )
    args = parser.parse_args(argv)

    try:
        if args.file == "-":
            data = sys.stdin.buffer.read()
        else:
            with open(args.file, "rb") as handle:
                data = handle.read()
    except OSError as error:
        print(f"check_trailers: cannot read {args.file}: {error}", file=sys.stderr)
        return 2
    # Git allows messages in other encodings (i18n.commitEncoding). Every
    # pattern checked here is ASCII, so undecodable bytes can be replaced.
    text = data.decode("utf-8", errors="replace")

    problems = check(text, kind=args.kind, require=args.require)
    if not problems:
        return 0
    name = "standard input" if args.file == "-" else args.file
    print(f"check_trailers: {len(problems)} problem(s) in {name}:", file=sys.stderr)
    for problem in problems:
        print(f"  {problem}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
