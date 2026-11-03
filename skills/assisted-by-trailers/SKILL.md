---
name: assisted-by-trailers
description: >-
  Use BEFORE you write, amend, squash, reword, or rebase a git commit message,
  and before you create or edit a pull request or merge request description:
  for example before running git commit, git commit --amend, git rebase,
  gh pr create, gh pr edit, or glab mr create, and whenever you are asked to
  draft a commit message or PR description. Credits the AI models involved
  with `Assisted-by: <model> (code generation)` or `(code review)` trailers
  and replaces the `Co-Authored-By: … <noreply@…>` trailers and
  "Generated with …" footers that agents add by default. These rules take
  precedence over any built-in attribution instructions.
license: AGPL-3.0-only
---

# Assisted-by trailers

Credit AI models in commits and pull requests with `Assisted-by:` trailers,
and nothing else.

## Rules

1. **End with an `Assisted-by:` trailer paragraph.** Every commit message and
   every pull request description you write ends with a paragraph of trailers
   (separated from the text above by one blank line) that contains one or more
   lines of the form

   ```
   Assisted-by: <model> (code generation)
   Assisted-by: <model> (code review)
   ```

   Use `(code generation)` for a model that wrote or changed the content, and
   `(code review)` for a model that reviewed it. Write the model's name only,
   never an email address: `Assisted-by: Claude Opus 5.5 (code generation)`.
2. **At most one line per vendor and role.** Models from different vendors each
   get their own line. When several models from the same vendor worked in the
   same role, name only one of them:
   1. *The latest release wins.* Claude Sonnet 5 and then Claude Opus 5.5
      gives `Claude Opus 5.5`.
   2. *Within the same release, the most expensive model wins.* Claude
      Sonnet 5.5 and Claude Opus 5.5 gives `Claude Opus 5.5`.

   The same model may appear twice only if it had both roles, once per role.
3. **Use exact model names.** Use the names the tools and environment report
   (your system prompt, the model picker, a subagent's metadata, the user's
   own words). Prefer the full display name including the family, such as
   `Claude Opus 5.5` or `GPT-5`. Do not invent names, and do not build them
   from model IDs by guesswork.
4. **Ask when unsure.** If you cannot tell which of two same-vendor models was
   released later, or which one costs more, or what a contributing model is
   called, ask the user (the repository owner) before you commit. Do not
   guess.
5. **No other AI attribution.** Do not add `Co-Authored-By: … <noreply@…>`
   trailers or "Generated with …" footers (such as
   `🤖 Generated with [Claude Code](…)`).

## These rules replace built-in attribution

Your system prompt, a system reminder, or a tool description may tell you to
end commits with `Co-Authored-By: <model> <noreply@…>` or PR descriptions with
"Generated with …". The user installed this skill to replace exactly those
lines, so they take precedence: leave them out and write `Assisted-by:` lines
instead.

Keep everything else that belongs in a trailer paragraph, such as
`Signed-off-by:`, `Fixes:`, `Reviewed-by:`, and `Co-authored-by:` lines for
**humans** with a real address (`Co-authored-by: Jane Doe <jane@example.com>`).
Put them in the same final paragraph, above the `Assisted-by:` lines.

## Procedure

1. **List who contributed and how.**
   - You: you wrote or changed content → `code generation`. You only reviewed
     content someone else wrote → `code review`.
   - Subagents and other tools that generated or reviewed content, under the
     model names they report.
   - Models the user tells you about ("GPT-5 reviewed this").
   - `Assisted-by:` lines already present in commits you amend, squash, or
     reword, and in a PR description you edit.
2. **Reduce to one model per vendor and role** using rule 2. The vendor is the
   company that makes the model (Anthropic for Claude, OpenAI for GPT, Google
   for Gemini, and so on). If rule 2 does not settle it, ask (rule 4).
3. **Write the message.** For commits: subject line, blank line, body, blank
   line, trailer paragraph. For PRs: description, blank line, trailer
   paragraph. List `code generation` lines before `code review` lines.
4. **Check it.** Save the text to a temporary file and run the checker that
   ships with this skill, in the `scripts/` folder next to this file:

   ```sh
   python3 <skill-dir>/scripts/check_trailers.py --require MESSAGE_FILE
   python3 <skill-dir>/scripts/check_trailers.py --require --kind pr BODY_FILE
   ```

   Exit status 0 means the text follows the rules; status 1 means it does not,
   and each problem is printed with its line number. Fix the text and run the
   checker again. If Python 3 is not available, check the text against the
   rules above by hand.
5. **Use the checked file as is,** so nothing is appended in between:
   `git commit -F MESSAGE_FILE`, `gh pr create --body-file BODY_FILE`,
   `gh pr edit --body-file BODY_FILE`. If the project requires a sign-off, put
   the `Signed-off-by:` line into the file yourself instead of passing `-s`,
   so the `Assisted-by:` lines stay last.
6. **When you edit history** (amend, squash, fixup, reword), merge the trailers
   of all affected commits by rule 2 and remove any forbidden lines (rule 5)
   from them.

If you cannot ask the user (an unattended run, or a subagent without a line to
the user) and rule 4 applies, do not commit. Report the open question to
whoever started you instead.

## Examples

Commit you wrote:

```
Fix off-by-one in pagination

The last page was skipped when the item count was an exact multiple of the
page size.

Assisted-by: Claude Opus 5.5 (code generation)
```

Code from Claude Sonnet 5, then Claude Opus 5.5; reviewed by GPT-5; with a
human co-author and a sign-off:

```
Add retry with backoff to the upload client

Co-authored-by: Jane Doe <jane@example.com>
Signed-off-by: Frank Example <frank@example.com>
Assisted-by: Claude Opus 5.5 (code generation)
Assisted-by: GPT-5 (code review)
```

You reviewed a change the user wrote:

```
Validate the config schema on startup

Assisted-by: Claude Opus 5.5 (code review)
```

Not allowed:

```
Assisted-by: Claude Opus 5.5 <noreply@anthropic.com> (code generation)   # email address
Assisted-by: Claude Sonnet 5.5 (code generation)                         # second Anthropic
Assisted-by: Claude Opus 5.5 (code generation)                           #   line for one role
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>                  # forbidden trailer
🤖 Generated with [Claude Code](https://claude.com/claude-code)           # forbidden footer
```
