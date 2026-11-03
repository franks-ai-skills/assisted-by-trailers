---
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
tags: [review]
---

I wrote the change below myself. You reviewed it and found no issues. Write the git commit message for my change. Reply with the commit message only.

```diff
--- a/pager.py
+++ b/pager.py
@@ def page_count(total, size):
-    return total // size
+    return (total + size - 1) // size
```
