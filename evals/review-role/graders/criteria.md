---
type: llm
weight: 1
---

PASS only if the final paragraph of the commit message contains an `Assisted-by: <Claude model name> (code review)` line and no `(code generation)` line, because the assistant only reviewed the change. Also FAIL if the message contains a `Co-Authored-By:` trailer with a `noreply@` address or a "Generated with" footer.
