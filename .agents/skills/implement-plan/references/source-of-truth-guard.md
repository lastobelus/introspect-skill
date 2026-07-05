# Source-of-Truth Guard During Implementation

Use this reference when implementing a reviewed plan that may have exploratory docs,
prior plans, research notes, or generated explanation artifacts nearby.

## Required Guard

1. Treat the active plan as authoritative for scope, decisions, invariants, validation,
   and manual review expectations.
2. Read docs and checklists explicitly named by the plan or required by repo guidance.
3. Do not treat older research notes, prior plans, or unlisted artifacts as
   requirements unless the active plan promotes them to current context.
4. If a linked artifact conflicts with the active plan, update it or mark it
   superseded before review.
5. Exclude merely discoverable historical artifacts from reviewer context.

## Reviewer Prompt Guard

Use this text when stale artifacts may be discoverable:

```text
The reviewed plan is authoritative. Use only the plan, touched files, validation
summary, and focused context file list as specification sources. Documents outside the
context file list are not requirements. Report a mismatch with an unlisted historical
document only if the current plan links to or depends on that document.
```

## Conflict Handling

- Code differs from the plan: fix the code or update the plan if implementation
  uncovered a better scoped decision.
- A linked doc differs from the plan: update or supersede the doc.
- An unlinked historical doc differs from the plan: do not expand scope; ignore it
  unless it reveals an actual gap in the plan.
- A reviewer asks for stale compatibility: defend against it in the plan or notes
  instead of adding a compatibility layer.
