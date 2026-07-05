# Context Hygiene Before Plan Review

Use this reference when a plan follows exploratory discussion, prior plans, research
notes, options docs, or generated explanation artifacts.

## Required Pass

1. Identify related artifacts a reviewer could reasonably find or the thread relied on:
   prior plans, research docs, linked docs, checklists, specs, and nearby similarly
   named files.
2. Classify each artifact:
   - `canonical-current`: authoritative context reviewers may rely on
   - `supporting-current`: useful background, not the source of truth
   - `historical/superseded`: stale or exploratory
   - `unknown/conflicting`: cannot be reconciled safely
3. Reconcile artifacts reviewers might treat as current spec:
   - update small stale artifacts when useful
   - mark stale artifacts superseded when they remain for history
   - remove stale links from the plan
   - stop for clarification only when a conflict changes scope, architecture, or
     acceptance criteria and no safe assumption exists
4. Add a compact source-of-truth section to the plan when prior artifacts matter:

```md
## Source of Truth and Context

Current source of truth:
- This plan.

Current supporting docs:
- docs/path/current-doc.md

Historical or superseded docs:
- docs/path/old-plan.md: exploratory; current decisions are reflected in this plan.

Reviewer instruction:
- Treat this plan as authoritative if historical artifacts conflict with it.
```

5. Build the reviewer context list from current sources only.

## Reviewer Prompt Guard

```text
The plan file is the current source of truth. Use only the plan and focused context
file list as specification sources. Historical, exploratory, superseded, or unlisted
documents are not authoritative. Report a mismatch with those documents only when the
current plan links to them, depends on them, or should explicitly update/supersede them.
```
