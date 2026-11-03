---
type: llm
weight: 1
---

PASS only if the response is a commit message (subject line, blank line, optional body) whose final paragraph contains exactly one line of the form `Assisted-by: <Claude model name> (code generation)`, for example `Assisted-by: Claude Opus 5.5 (code generation)`, with the model name and no email address. Also FAIL if the message contains a `Co-Authored-By:` trailer with a `noreply@` address or a "Generated with" footer.
