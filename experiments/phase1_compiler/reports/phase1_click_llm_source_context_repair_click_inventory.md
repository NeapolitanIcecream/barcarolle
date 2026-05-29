# Click Source Repair Candidate Inventory

What happened: the click task universe was frozen from the paid-readiness task table and source-hardening metadata without loading paid outcomes.

Click tasks in scope: 30. Expected count met: true.
Title-only/minor-risk rows: 30.
Outcome fields absent: true.

Task-family buckets:
- click:_bashcomplete: 1
- click:_termui_impl: 2
- click:core: 15
- click:shell_completion: 5
- click:termui: 1
- click:testing: 2
- click:types: 4

Why it matters: processing order and scope are fixed before any public-context or LLM branch can see a task list.

Whether click is cleaner now: still title-only/minor-risk at the inventory step; repair decisions have not been applied.
