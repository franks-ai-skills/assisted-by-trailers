# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/). Keep the version in
`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` in sync.

## [1.0.0] - 2026-11-03

### Added

- `assisted-by-trailers` skill: `Assisted-by: <model> (code generation|code
  review)` trailer rules, one line per vendor and role with latest-release and
  most-expensive tie-breaks, ask-when-unsure rule, and precedence over built-in
  `Co-Authored-By` and "Generated with" attribution.
- `check_trailers.py`: dependency-free checker for commit messages and PR
  descriptions that also works as a git `commit-msg` hook.
- Unit and git-hook integration tests for the checker.
- Behavioral eval suite.
- Claude Code plugin and single-plugin marketplace manifests.
- Licensed under AGPL-3.0-only.
