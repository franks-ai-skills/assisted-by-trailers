---
type: llm
weight: 1
---

PASS only if the final paragraph of the commit message credits exactly one Anthropic model for code generation, and that line is exactly `Assisted-by: Claude Opus 5.5 (code generation)` (same release, so the more expensive model wins). FAIL if Claude Sonnet 5.5 also gets an `Assisted-by` line. Also FAIL if the message contains a `Co-Authored-By:` trailer with a `noreply@` address or a "Generated with" footer.
