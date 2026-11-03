---
type: llm
weight: 1
---

PASS only if the final paragraph of the commit message credits exactly one Anthropic model for code generation, and that line is exactly `Assisted-by: Claude Opus 5.5 (code generation)` (the latest release wins over Claude Sonnet 5). FAIL if Claude Sonnet 5 also gets an `Assisted-by` line. Also FAIL if the message contains a `Co-Authored-By:` trailer with a `noreply@` address or a "Generated with" footer.
