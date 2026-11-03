---
type: llm
weight: 1
---

PASS only if the final paragraph of the commit message contains both `Assisted-by: Claude Opus 5.5 (code generation)` and `Assisted-by: GPT-5 (code review)`, each on its own line, and no other line for the same vendor and role. Also FAIL if the message contains a `Co-Authored-By:` trailer with a `noreply@` address or a "Generated with" footer.
