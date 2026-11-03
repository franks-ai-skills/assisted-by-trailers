# assisted-by-trailers

An [Agent Skill](https://agentskills.io) that makes an AI agent credit the
models it used with **`Assisted-by:` trailers** in git commits and pull
requests, instead of `Co-Authored-By: … <noreply@…>` trailers and
"Generated with …" footers.

## The problem

Coding agents add their own attribution to commits and PRs. Claude Code, for
example, ends commit messages with

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

and pull request descriptions with

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

If your project wants a different format, you end up correcting the agent
again and again: in every session, every repository, every amended commit.

## What the skill does

Whenever the agent writes or edits a commit message or a PR description, it
ends the text with a trailer paragraph like this one:

```
Assisted-by: Claude Opus 5.5 (code generation)
Assisted-by: GPT-5 (code review)
```

The rules:

1. One line per model with the role it had: `(code generation)` or
   `(code review)`. The model's name only, no email address.
2. **At most one line per vendor and role.** Models from different vendors
   each get their own line. Among several models from one vendor in one role,
   only one is named: the **latest release** wins (Claude Sonnet 5, then
   Claude Opus 5.5 → `Claude Opus 5.5`); within the same release, the **most
   expensive** wins (Claude Sonnet 5.5 and Claude Opus 5.5 →
   `Claude Opus 5.5`).
3. Exact model names as the tools report them, never invented. If release
   order or price is unclear, the agent asks you.
4. No `Co-Authored-By: … <noreply@…>` trailers and no "Generated with …"
   footers. Human co-authors (`Co-authored-by: Jane Doe <jane@example.com>`),
   `Signed-off-by:` and other trailers are kept, in the same final paragraph
   above the `Assisted-by:` lines.

The skill also ships [`check_trailers.py`](skills/assisted-by-trailers/scripts/check_trailers.py),
a small checker (Python 3.9+, no dependencies) that the agent runs on its
message before committing, and that you can install as a git `commit-msg`
hook.

The full behavior is in
[`skills/assisted-by-trailers/SKILL.md`](skills/assisted-by-trailers/SKILL.md).

## Installation

### Claude Code: as a plugin (recommended)

This repository is both a plugin and a single-plugin marketplace:

```sh
claude plugin marketplace add franks-ai-skills/assisted-by-trailers
claude plugin install assisted-by-trailers@assisted-by-trailers
```

Or inside a Claude Code session:

```
/plugin marketplace add franks-ai-skills/assisted-by-trailers
/plugin install assisted-by-trailers@assisted-by-trailers
```

To try a local checkout without installing it:

```sh
claude --plugin-dir /path/to/assisted-by-trailers
```

### Claude Code: as a plain skill

Copy the skill folder into your personal or project skills directory:

```sh
# for all your projects
cp -R skills/assisted-by-trailers ~/.claude/skills/

# for one project only (commit it to share it with your team)
cp -R skills/assisted-by-trailers /path/to/project/.claude/skills/
```

### Other agents

`SKILL.md` follows the open [Agent Skills](https://agentskills.io) format.
Agents that support it can load the `skills/assisted-by-trailers/` folder
from their skills directory; see your agent's documentation for where that
is. For agents without skill support, paste the body of `SKILL.md`
(everything after the front matter) into the agent's rules file, for example
`AGENTS.md`, and adjust the checker path in step 4 of the procedure.

## Turn off the built-in attribution (Claude Code)

By default, Claude Code tells the agent to end commits with its
`Co-Authored-By: <model> <noreply@anthropic.com>` trailer and PR descriptions
with its "🤖 Generated with [Claude Code](…)" line. In cloud and Remote
Control sessions it also adds a `Claude-Session:` trailer and a session link.
The skill works with these defaults: since Claude Code v2.1.269, Claude Code
tells the agent that the user's own instructions about these lines take
precedence. The skill's evals pass that way.

Turning the built-in attribution off is still recommended:

- the agent no longer gets two conflicting instructions, and
- commits the agent makes without loading the skill no longer get a
  `Co-Authored-By` trailer.

Add this to `~/.claude/settings.json` (or a project's `.claude/settings.json`)
next to your existing settings, then **start a new session**:

```json
{
  "attribution": {
    "commit": "",
    "pr": "",
    "sessionUrl": false
  }
}
```

| Key | Effect |
|-----|--------|
| `commit: ""` | no commit trailer |
| `pr: ""` | no PR description line |
| `sessionUrl: false` | no `Claude-Session:` trailer or PR link in cloud and Remote Control sessions |

Details worth knowing:

- **Start a new session after the change.** In a local session that starts
  with attribution off, Claude Code sends the agent no attribution
  instructions at all. If you turn it off *during* a session, Claude Code
  2.1.317 tells the agent to stop adding attribution lines altogether, "even
  if a CLAUDE.md or memory rule asks for attribution lines". That conflicts
  with the skill for the rest of that session. Remote Control sessions can
  get the same message at the start.
- **The shorthand `"attribution": false`** has the same effect, but it needs
  Claude Code v2.1.281 or later. Earlier versions reject it and skip the
  *whole* settings file that contains it. Use the object form in files that
  other or older installations may read.
- **`includeCoAuthoredBy` is deprecated.** `attribution` replaced it in
  v2.0.62. Claude Code still reads `"includeCoAuthoredBy": false`: it removes
  the commit trailer and the PR line, but not the session link. It is ignored
  as soon as `attribution.commit` or `attribution.pr` is set. You only need it
  for versions older than 2.0.62.
- **Don't put an `Assisted-by:` line into `attribution.commit`.** That line
  would be static, so it can't follow model changes, roles, or several
  vendors. And Claude Code tells the agent not to add attribution lines that
  the setting leaves out, which works against the skill's per-vendor lines.
- **Managed settings win.** If your organization sets `attribution` in
  managed settings, Claude Code tells the agent that those lines apply even
  if your instructions say otherwise. The skill can't override that; ask your
  administrator.

Sources: the [`attribution`](https://code.claude.com/docs/en/settings-reference#attribution)
and [`includeCoAuthoredBy`](https://code.claude.com/docs/en/settings-reference#includecoauthoredby)
entries of the Claude Code settings reference, and the Claude Code
[changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
(2.0.62, 2.1.183, 2.1.269, 2.1.281). The mid-session behavior is not
documented; it was read from the Claude Code 2.1.317 source and may change.

Other agents may add attribution of their own; check their documentation.

## Usage

The skill loads **automatically** when the agent is about to commit or write
a PR description. You can also call it explicitly:

| Installed as | Command |
|--------------|---------|
| Plugin | `/assisted-by-trailers:assisted-by-trailers` |
| Plain skill | `/assisted-by-trailers` |

**Making it reliable.** Automatic loading depends on the model matching the
task to the skill's description. To have the rules applied every time, add a
line like this to your `CLAUDE.md` (or `AGENTS.md`). Claude Code explicitly
tells the agent that such a rule outranks its own attribution lines:

```markdown
Before every git commit or pull request, follow the assisted-by-trailers
skill for attribution trailers.
```

## Enforcing the rules with a git hook

The checker reads the message file that git passes to a `commit-msg` hook, so
it can reject commits that break the rules, whoever writes them. Without
`--require` it accepts commits that have no `Assisted-by:` line at all, so
your own commits without AI help still go through.

```sh
# in the repository that should enforce the rules
cp /path/to/assisted-by-trailers/skills/assisted-by-trailers/scripts/check_trailers.py \
   .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
```

- If the repository already has a `commit-msg` hook, don't overwrite it; call
  the checker from it instead: `python3 /path/to/check_trailers.py "$1" || exit 1`.
- On Windows, where `python3` may not be on the `PATH`, use a two-line hook
  instead of the copy: `#!/bin/sh` and then
  `exec python /path/to/check_trailers.py "$1"`.
- Hooks are local to your clone. To share the hook with a team, commit it to
  the repository and point git to it with `git config core.hooksPath <dir>`,
  or use a hook manager. Note that a `core.hooksPath` set globally disables
  every repository's `.git/hooks/` folder.
- When the hook rejects a commit, git keeps the message in
  `.git/COMMIT_EDITMSG`; fix it and commit with
  `git commit -e -F .git/COMMIT_EDITMSG`.

You can also check any text by hand:

```sh
git log -1 --format=%B | python3 check_trailers.py --require
python3 check_trailers.py --require --kind pr pr-body.md
```

Exit status 0 means the text follows the rules, 1 means it doesn't (every
problem is printed to standard error with its line number), 2 means a usage
or read error.

## Testing

```sh
# unit tests for the checker, including a real git commit-msg hook run
python3 -m unittest discover -s tests -v

# check manifests and skill front matter
claude plugin validate .

# run the behavioral evals (with and without the skill, for comparison)
claude plugin eval . --no-publish
```

The cases in [`evals/`](evals/):

| Case | Expected behavior |
|------|-------------------|
| `commit-message` | ends a commit message with `Assisted-by: <model> (code generation)` (automatic triggering) |
| `review-role` | uses `(code review)` when the agent only reviewed the change |
| `same-vendor-latest` | Claude Sonnet 5, then Claude Opus 5.5 → only `Claude Opus 5.5` |
| `same-release-price` | Claude Sonnet 5.5 and Claude Opus 5.5 → only `Claude Opus 5.5` |
| `multi-vendor` | one line each for Claude (generation) and GPT-5 (review) |
| `unclear-order-asks` | asks which model to credit when release order and price are unknown |
| `pr-description` | PR description ends with `Assisted-by:` and has no "Generated with" footer |
| `human-co-author` | keeps a human `Co-authored-by:` line and adds `Assisted-by:` below it |

Each eval run starts real agent sessions on your account, so it costs tokens.
Add `--runs 1` for a cheaper smoke test. The cases name Claude models from
the Claude 5 family; when those models are superseded, update the names in
the prompts and graders. Results are written to `evals/results/`, which is
git-ignored.

## Known limitations

- **Instructions, not a guarantee.** The skill only tells the agent what to
  do. Switch off the built-in attribution (see above) so the agent doesn't
  get two conflicting instructions, and install the `commit-msg` hook if you
  need enforcement. The hook does not cover PR descriptions; run the checker
  with `--kind pr` on them, for example in CI.
- **Release order and price are not looked up.** The skill contains no model
  catalog, because it would go stale. The agent decides from what it knows
  and asks you when that isn't enough.
- **The checker's vendor list is a heuristic.** It maps the first word of a
  model name to a vendor (`Claude` → Anthropic, `GPT` → OpenAI, …). A model
  whose first word it doesn't know counts as its own vendor, so two such
  models from the same vendor are not flagged. Add entries to `VENDORS` in
  `check_trailers.py` as needed.
- **"Generated with" at the start of a line is always flagged**, even in
  ordinary prose such as "Generated with protoc 3.21", unless it is quoted.
  Rephrase such lines.
- **Comment handling assumes git's defaults.** For commits, the checker
  ignores lines starting with `#` and everything after git's scissors line.
  With a different `core.commentChar` or `commit.cleanup`, those lines are
  checked like any other.

## Contributing

Issues and pull requests are welcome, especially eval cases where the agent
got the trailers wrong. When you change `SKILL.md`, run the evals before and
after; when you change `check_trailers.py`, add a test for it.

## License

Licensed under the GNU Affero General Public License v3.0 only
([AGPL-3.0-only](LICENSE)).
