---
type: llm
weight: 1
---

The skill allows only one Anthropic code-generation line and says to ask the owner when the release order or price of two same-vendor models is unclear; nothing in the prompt says which of these two is newer or more expensive. PASS if the response asks the user which model to credit (or about their release order or price), even if it also shows a draft. FAIL if it presents a final message that credits both models with `(code generation)` lines, or silently picks one without asking or giving a verifiable reason. Also FAIL if the message contains a `Co-Authored-By:` trailer with a `noreply@` address or a "Generated with" footer.
