---
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
tags: [pr]
---

You made the change below. Write the GitHub pull request description for it. Reply with the description only.

```diff
--- a/pager.py
+++ b/pager.py
@@ def page_count(total, size):
-    return total // size
+    return (total + size - 1) // size
```
