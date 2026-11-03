---
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
tags: [generation, auto-trigger]
---

You just made the change below to fix the page count. Write the git commit message for it. Reply with the commit message only.

```diff
--- a/pager.py
+++ b/pager.py
@@ def page_count(total, size):
-    return total // size
+    return (total + size - 1) // size
```
