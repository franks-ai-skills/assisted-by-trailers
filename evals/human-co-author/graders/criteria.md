---
type: llm
weight: 1
---

PASS only if the final paragraph of the commit message contains both `Co-authored-by: Jane Doe <jane@example.com>` (any capitalization of the key) and an `Assisted-by: <Claude model name> (code generation)` line, with the `Assisted-by` line after the human co-author line. FAIL if Jane Doe is dropped or the model gets an email address. Also FAIL if the message contains a `Co-Authored-By:` trailer with a `noreply@` address or a "Generated with" footer.
